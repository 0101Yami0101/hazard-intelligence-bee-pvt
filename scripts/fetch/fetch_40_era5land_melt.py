"""ERA5-Land daily snow melt, snow on the ground and air temperature on the
IMERG 0.1° lattice — the melt-water input for the river gauge models
(docs/design/FLOOD_WHEN_PILOT_PLAN.md §17).

    python scripts/fetch/fetch_40_era5land_melt.py            # fetch / resume
    python scripts/fetch/fetch_40_era5land_melt.py --assemble # batches -> arrays

Writes  data/interim/snow_melt/_batches/YYYY-MM.npz      (one per month)
        data/interim/snow_melt/era5land_melt_lattice.npz (days x 1,953 cells)
        data/interim/snow_melt/_SOURCES.json

Why: a river fed by melting snow can sit above its line for weeks with no
rain (Rho Basti, June 2016, §14d). The gauge models read rain and the
river's own week; nothing tells them that melt water is coming.

The same source, grid and method as fetch_39_era5land_soil.py (Earth Engine,
ECMWF/ERA5_LAND/DAILY_AGGR, one computePixels call a month, bilinear onto the
lattice's x.x5 cell centres), so the daily run can read both in one way.

Kept per cell-day:
    melt_mm   snowmelt_sum, mm of water that day
    swe_mm    snow_depth_water_equivalent, mm of water lying as snow
    temp_c    temperature_2m, daily mean, deg C
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "model"), str(ROOT / "scripts" / "fetch")]

import ee
import numpy as np
import pandas as pd

import fetch_39_era5land_soil as F39
from common import INTERIM, record

OUT = INTERIM / "snow_melt"
BATCH = OUT / "_batches"
BANDS = ["snowmelt_sum", "snow_depth_water_equivalent", "temperature_2m"]
NAMES = ["melt_mm", "swe_mm", "temp_c"]
START, DEG, THREADS = F39.START, F39.DEG, F39.THREADS


def _grid() -> dict:
    r0, c0, nr, nc = F39.lattice_window()
    return {"dimensions": {"width": nc, "height": nr},
            "affineTransform": {"scaleX": DEG, "shearX": 0, "translateX": round(F39.W + c0 * DEG, 6),
                                "shearY": 0, "scaleY": -DEG, "translateY": round(F39.N - r0 * DEG, 6)},
            "crsCode": "EPSG:4326"}


def _units(a: np.ndarray, j: int) -> np.ndarray:
    return a * 1000.0 if j < 2 else a - 273.15            # m -> mm ; K -> deg C


def lattice_days(d0: str, d1: str) -> tuple[pd.DatetimeIndex, dict[str, np.ndarray]]:
    """The three fields on the lattice for days d0..d1 inclusive, in one
    call — what the monthly fetch and the daily run both use, so live values
    match the archive exactly. Days ERA5-Land does not have yet are absent."""
    ee.Initialize(project=F39.PROJECT)
    _, _, nr, nc = F39.lattice_window()
    end = (pd.Timestamp(d1) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    col = (ee.ImageCollection(F39.COLL).filterDate(pd.Timestamp(d0).strftime("%Y-%m-%d"), end)
           .select(BANDS).map(lambda i: i.resample("bilinear")))
    if col.size().getInfo() == 0:
        return pd.DatetimeIndex([]), {n: np.empty((0, nr * nc), np.float32) for n in NAMES}
    arr = ee.data.computePixels({"expression": col.toBands(), "fileFormat": "NUMPY_NDARRAY",
                                 "grid": _grid()})
    days = sorted({n.split("_", 1)[0] for n in arr.dtype.names})
    out = {n: np.stack([_units(np.asarray(arr[f"{d}_{b}"], np.float32).ravel(), j) for d in days])
           for j, (n, b) in enumerate(zip(NAMES, BANDS))}
    return pd.to_datetime(days), out


def fetch_month(m0: pd.Timestamp, last: pd.Timestamp) -> Path:
    f = BATCH / f"{m0:%Y-%m}.npz"
    d0 = max(m0, pd.Timestamp(START))
    d1 = min(m0 + pd.offsets.MonthEnd(0), last)
    days, out = lattice_days(str(d0.date()), str(d1.date()))
    np.savez_compressed(f, dates=days.to_numpy().astype("datetime64[D]"), **out)
    return f


def _retry(m, last, tries: int = 4):
    for t in range(tries):
        try:
            return fetch_month(m, last)
        except Exception:                                           # noqa: BLE001
            if t == tries - 1:
                raise
            time.sleep(5 * (t + 1))


def fetch() -> None:
    ee.Initialize(project=F39.PROJECT)
    BATCH.mkdir(parents=True, exist_ok=True)
    last = pd.Timestamp(ee.Date(ee.ImageCollection(F39.COLL).sort("system:time_start", False)
                                .first().get("system:time_start")).format("YYYY-MM-dd").getInfo())
    ms = F39.months(last.strftime("%Y-%m-%d"))
    todo = [m for m in ms if not (BATCH / f"{m:%Y-%m}.npz").exists() or m == ms[-1]]
    print(f"ERA5-Land snow melt, snow and temperature, {START} .. {last.date()}: {len(ms)} months, "
          f"{len(todo)} to fetch", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(THREADS) as pool:
        futs = {pool.submit(_retry, m, last): m for m in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            m = futs[fu]
            try:
                fu.result()
                if i % 20 == 0 or i == len(todo):
                    print(f"  [{i}/{len(todo)}] {m:%Y-%m}  ({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:                                  # noqa: BLE001
                print(f"  [{i}/{len(todo)}] {m:%Y-%m} FAILED {type(e).__name__}: {str(e)[:120]}",
                      flush=True)


def assemble() -> None:
    files = sorted(BATCH.glob("*.npz"))
    D, A = [], {n: [] for n in NAMES}
    for f in files:
        z = np.load(f)
        D.append(z["dates"])
        for n in NAMES:
            A[n].append(z[n])
    dates = np.concatenate(D)
    full = pd.date_range(START, pd.Timestamp(dates.max()))
    assert len(dates) == len(full) and (pd.to_datetime(dates) == full).all(), \
        f"gaps: {len(full) - len(dates)} missing days"
    out = {n: np.concatenate(A[n]).astype(np.float32) for n in NAMES}
    dest = OUT / "era5land_melt_lattice.npz"
    np.savez_compressed(dest, dates=dates, **out)
    meta = {"start": str(dates.min()), "end": str(dates.max()), "n_days": int(len(dates)),
            "lattice_cells": int(out[NAMES[0]].shape[1]), "variables": dict(zip(NAMES, BANDS)),
            "nan_share": {n: float(np.isnan(out[n]).mean()) for n in NAMES}}
    record(OUT, "ECMWF/ERA5_LAND/DAILY_AGGR via Google Earth Engine (snow melt, snow, temperature)",
           "https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR",
           [dest], license_="Copernicus licence (free, attribution)", notes=json.dumps(meta))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    if "--assemble" not in sys.argv:
        fetch()
    assemble()
