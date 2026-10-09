"""ERA5-Land daily soil water and rain on the IMERG 0.1° lattice — the input
for the soil-wetness test (docs/design/SOIL_WETNESS_TEST.md).

    python scripts/fetch/fetch_39_era5land_soil.py            # fetch / resume
    python scripts/fetch/fetch_39_era5land_soil.py --assemble # batches -> arrays

Writes  data/interim/soil_wetness/_batches/YYYY-MM.npz      (one per month)
        data/interim/soil_wetness/era5land_lattice.npz      (days x 1,953 cells)
        data/interim/soil_wetness/era5land_arc_events.npz   (days x event cells)

Runs inside Google Earth Engine (ECMWF/ERA5_LAND/DAILY_AGGR, project
earthengine-507510), no file downloads. Each month is one computePixels call
over the Himalayan-arc box 76-98°E, 26-32°N on a 0.1° grid whose cell centres
sit at x.x5 — the IMERG lattice's own spacing and alignment, so the Arunachal
lattice (91.3-97.6°E, 26.5-29.6°N) is an exact sub-window. ERA5-Land's native
0.1° grid is centred on x.x0, so every value is bilinear from its four
neighbours.

Kept per cell-day: rain (mm) and volumetric soil water of layers 1-3
(0-7, 7-28, 28-100 cm). Only two sets of cells are stored: the Arunachal
lattice, and the arc cells holding a dated, <=5 km located GLC landslide
(reports/_himalaya_glc.csv) — the whole arc box would be ~2 GB.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "model")]

import ee
import numpy as np
import pandas as pd

import when_grid
from common import INTERIM

OUT = INTERIM / "soil_wetness"
BATCH = OUT / "_batches"
PROJECT = "earthengine-507510"
COLL = "ECMWF/ERA5_LAND/DAILY_AGGR"
BANDS = ["total_precipitation_sum", "volumetric_soil_water_layer_1",
         "volumetric_soil_water_layer_2", "volumetric_soil_water_layer_3"]
NAMES = ["rain_mm", "swv1", "swv2", "swv3"]
START = "2000-06-01"                 # the IMERG record's first day
DEG = 0.1
W, E, S, N = 76.0, 98.0, 26.0, 32.0  # arc box edges (PARKED_HIMALAYAN_POOLED_TRIGGER §3)
NX, NY = round((E - W) / DEG), round((N - S) / DEG)
GLC_ACCURACY = ("exact", "1km", "5km")
THREADS = 6


def lattice_window() -> tuple[int, int, int, int]:
    """(row0, col0, nrows, ncols) of the IMERG lattice inside the arc grid."""
    L = when_grid.lattice()
    top, left = L["lat_max"] + L["deg"] / 2, L["lon_min"] - L["deg"] / 2
    r0, c0 = round((N - top) / DEG), round((left - W) / DEG)
    assert abs(N - r0 * DEG - top) < 1e-4 and abs(W + c0 * DEG - left) < 1e-4
    return r0, c0, L["nlat"], L["nlon"]


def arc_events() -> pd.DataFrame:
    d = pd.read_csv(ROOT / "reports" / "_himalaya_glc.csv")
    d["date"] = pd.to_datetime(d["dt"], errors="coerce")
    keep = (d["date"].notna() & d["loc_accu"].isin(GLC_ACCURACY)
            & d["longitude"].between(W, E) & d["latitude"].between(S, N))
    d = d[keep].copy()
    d["row"] = np.floor((N - d["latitude"]) / DEG).astype(int).clip(0, NY - 1)
    d["col"] = np.floor((d["longitude"] - W) / DEG).astype(int).clip(0, NX - 1)
    d["ak"] = d["row"] * NX + d["col"]
    return d.reset_index(drop=True)


def arc_cells() -> np.ndarray:
    return np.unique(arc_events()["ak"].to_numpy())


def months(last: str) -> list[pd.Timestamp]:
    return list(pd.date_range(pd.Timestamp(START).replace(day=1), last, freq="MS"))


def fetch_month(m0: pd.Timestamp, last: pd.Timestamp, ak: np.ndarray) -> Path:
    f = BATCH / f"{m0:%Y-%m}.npz"
    m1 = min(m0 + pd.offsets.MonthBegin(1), last + pd.Timedelta(days=1))
    d0 = max(m0, pd.Timestamp(START))
    col = (ee.ImageCollection(COLL).filterDate(d0.strftime("%Y-%m-%d"), m1.strftime("%Y-%m-%d"))
           .select(BANDS).map(lambda i: i.resample("bilinear")))
    arr = ee.data.computePixels({
        "expression": col.toBands(), "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": NX, "height": NY},
                 "affineTransform": {"scaleX": DEG, "shearX": 0, "translateX": W,
                                     "shearY": 0, "scaleY": -DEG, "translateY": N},
                 "crsCode": "EPSG:4326"}})
    days = sorted({n.split("_", 1)[0] for n in arr.dtype.names})
    cube = np.full((len(days), NY, NX, len(BANDS)), np.nan, dtype=np.float32)
    for i, dstr in enumerate(days):
        for j, b in enumerate(BANDS):
            cube[i, :, :, j] = arr[f"{dstr}_{b}"]
    cube[..., 0] *= 1000.0                      # m -> mm
    r0, c0, nr, nc = lattice_window()
    lat = cube[:, r0:r0 + nr, c0:c0 + nc, :].reshape(len(days), nr * nc, len(BANDS))
    arc = cube.reshape(len(days), NY * NX, len(BANDS))[:, ak, :]
    np.savez_compressed(f, dates=pd.to_datetime(days).to_numpy().astype("datetime64[D]"),
                        lattice=lat, arc=arc, arc_k=ak)
    return f


def lattice_days(d0: str, d1: str) -> tuple[pd.DatetimeIndex, dict[str, np.ndarray]]:
    """Soil water layers 1-3 on the IMERG lattice for days d0..d1 inclusive —
    what the daily flood run needs, in one call. The grid is the lattice
    window of the arc grid above, so values match the archive exactly.
    Days ERA5-Land does not have yet are simply absent."""
    ee.Initialize(project=PROJECT)
    r0, c0, nr, nc = lattice_window()
    end = (pd.Timestamp(d1) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    col = (ee.ImageCollection(COLL).filterDate(pd.Timestamp(d0).strftime("%Y-%m-%d"), end)
           .select(BANDS[1:]).map(lambda i: i.resample("bilinear")))
    if col.size().getInfo() == 0:
        return pd.DatetimeIndex([]), {n: np.empty((0, nr * nc), np.float32) for n in NAMES[1:]}
    arr = ee.data.computePixels({
        "expression": col.toBands(), "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": nc, "height": nr},
                 "affineTransform": {"scaleX": DEG, "shearX": 0,
                                     "translateX": round(W + c0 * DEG, 6),
                                     "shearY": 0, "scaleY": -DEG,
                                     "translateY": round(N - r0 * DEG, 6)},
                 "crsCode": "EPSG:4326"}})
    days = sorted({n.split("_", 1)[0] for n in arr.dtype.names})
    out = {n: np.stack([np.asarray(arr[f"{d}_{b}"], np.float32).ravel() for d in days])
           for n, b in zip(NAMES[1:], BANDS[1:])}
    return pd.to_datetime(days), out


def fetch() -> None:
    ee.Initialize(project=PROJECT)
    BATCH.mkdir(parents=True, exist_ok=True)
    last = pd.Timestamp(ee.Date(ee.ImageCollection(COLL).sort("system:time_start", False)
                                .first().get("system:time_start")).format("YYYY-MM-dd").getInfo())
    ak = arc_cells()
    ms = months(last.strftime("%Y-%m-%d"))
    # the last month is always refetched: it may have grown since last run
    todo = [m for m in ms if not (BATCH / f"{m:%Y-%m}.npz").exists() or m == ms[-1]]
    print(f"ERA5-Land soil water + rain, {START} .. {last.date()}: {len(ms)} months, "
          f"{len(todo)} to fetch; {len(ak)} arc event cells", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(THREADS) as pool:
        futs = {pool.submit(_retry, m, last, ak): m for m in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            m = futs[fu]
            try:
                fu.result()
                print(f"  [{i}/{len(todo)}] {m:%Y-%m}  ({time.time()-t0:.0f}s)", flush=True)
            except Exception as e:                                  # noqa: BLE001
                print(f"  [{i}/{len(todo)}] {m:%Y-%m} FAILED {type(e).__name__}: {str(e)[:120]}",
                      flush=True)


def _retry(m, last, ak, tries: int = 4):
    for t in range(tries):
        try:
            return fetch_month(m, last, ak)
        except Exception:                                           # noqa: BLE001
            if t == tries - 1:
                raise
            time.sleep(5 * (t + 1))


def assemble() -> None:
    files = sorted(BATCH.glob("*.npz"))
    ak = arc_cells()
    D, LAT, ARC = [], [], []
    for f in files:
        z = np.load(f)
        assert np.array_equal(z["arc_k"], ak), f"{f.name}: arc cells changed - refetch"
        D.append(z["dates"]); LAT.append(z["lattice"]); ARC.append(z["arc"])
    dates = np.concatenate(D)
    full = pd.date_range(START, pd.Timestamp(dates.max()))
    assert len(dates) == len(full) and (pd.to_datetime(dates) == full).all(), \
        f"gaps: {len(full) - len(dates)} missing days"
    lat, arc = np.concatenate(LAT), np.concatenate(ARC)
    out = {n: lat[..., j] for j, n in enumerate(NAMES)}
    np.savez(OUT / "era5land_lattice.npz", dates=dates, **out)
    ev = arc_events()
    rows, cols = ak // NX, ak % NX
    np.savez(OUT / "era5land_arc_events.npz", dates=dates, arc_k=ak,
             lat=N - (rows + 0.5) * DEG, lon=W + (cols + 0.5) * DEG,
             **{n: arc[..., j] for j, n in enumerate(NAMES)})
    meta = {"source": COLL, "start": str(dates.min()), "end": str(dates.max()),
            "n_days": int(len(dates)), "lattice_cells": int(lat.shape[1]),
            "arc_event_cells": int(len(ak)), "arc_events": int(len(ev)),
            "variables": dict(zip(NAMES, BANDS)),
            "resampling": "bilinear from ERA5-Land's x.x0 grid onto x.x5 cell centres",
            "nan_share_lattice": {n: float(np.isnan(out[n]).mean()) for n in NAMES}}
    (OUT / "era5land_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    if "--assemble" in sys.argv:
        assemble()
    else:
        fetch()
        assemble()
