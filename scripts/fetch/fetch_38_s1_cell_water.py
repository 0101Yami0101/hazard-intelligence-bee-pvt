"""Share of low ground under NEW water, per ~10 km rain cell, per Sentinel-1
pass — the raw material for grading the map's area outlook against the
satellite rather than waiting for news reports.

    python scripts/fetch/fetch_38_s1_cell_water.py 2024-05-01 2024-11-01
    python scripts/fetch/fetch_38_s1_cell_water.py --recent 14      # daily use

Writes  data/interim/flood_forecast/s1_cell_water.parquet   (appends; one row
        per pass x cell: date, orbit, k, new_water, water, n_low)

Runs entirely inside Google Earth Engine (COPERNICUS/S1_GRD), no downloads —
the same free route as fetch_32 (project earthengine-507510, see
PARKED_HIMALAYAN_FLOOD_WHERE.md §5c).

Per pass (one relative orbit on one day, its slices mosaicked):
    water       VV < -17 dB after a 30 m median filter (fetch_32's threshold)
    baseline    the median of the same orbit's March images, that year — dry
                season, same viewing geometry
    new water   water now, dry in the baseline
    low ground  MERIT Hydro height-above-drainage < 10 m, so ridges and radar
                shadow on steep slopes do not count
and per rain cell: the share of its low ground that is new water, and how
much low ground the pass actually saw.

⚠️ This is a MEASUREMENT, not yet a flood label. In the monsoon every river
runs wider than in March, so raw new water is high everywhere; whether a
cell is UNUSUALLY wet has to be judged against its own typical monsoon level
(check_map_grader.py does that, and tests it against known floods first).
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "model")]

import ee
import numpy as np
import pandas as pd

import when_grid
from common import INTERIM, ROOT as _R  # noqa: F401

OUT = INTERIM / "flood_forecast" / "s1_cell_water.parquet"
PROJECT = "earthengine-507510"
S1 = "COPERNICUS/S1_GRD"
WATER_DB = -17.0
HAND_MAX_M = 10
SCALE_M = 50
AOI = [91.45, 26.6, 97.55, 29.55]
PASS_TIMEOUT_S = 300


def cells() -> pd.DataFrame:
    """Rain cells whose centre lies in the app's window and that have
    floodable ground (models/flood_forecast/exposure_km2.npy)."""
    lat, lon = when_grid.cell_centres()
    E = np.load(ROOT / "models" / "flood_forecast" / "exposure_km2.npy")
    w, s, e, n = AOI
    keep = np.isfinite(E) & (E > 0) & (lon >= w) & (lon <= e) & (lat >= s) & (lat <= n)
    k = np.flatnonzero(keep)
    return pd.DataFrame({"k": k, "lat": lat[k], "lon": lon[k]})


def cell_fc(c: pd.DataFrame, deg: float) -> ee.FeatureCollection:
    h = deg / 2
    return ee.FeatureCollection([
        ee.Feature(ee.Geometry.Rectangle([lo - h, la - h, lo + h, la + h]), {"k": int(k)})
        for k, la, lo in zip(c["k"], c["lat"], c["lon"])])


def s1(d0: str, d1: str) -> ee.ImageCollection:
    return (ee.ImageCollection(S1).filterBounds(ee.Geometry.Rectangle(AOI)).filterDate(d0, d1)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")))


def passes(d0: str, d1: str) -> list[tuple[str, int]]:
    col = s1(d0, d1)
    t = col.aggregate_array("system:time_start").getInfo()
    o = col.aggregate_array("relativeOrbitNumber_start").getInfo()
    return sorted({(dt.datetime.fromtimestamp(x / 1000, dt.UTC).date().isoformat(), int(oo))
                   for x, oo in zip(t, o)})


def _vv(img: ee.Image) -> ee.Image:
    return img.select("VV").focalMedian(30, "circle", "meters")


def baseline(orbit: int, year: int) -> ee.Image | None:
    for y in (year, year - 1, year + 1):
        col = s1(f"{y}-03-01", f"{y}-04-01").filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
        if col.size().getInfo() > 0:
            return col.map(_vv).median()
    return None


def one_pass(day: str, orbit: int, fc: ee.FeatureCollection, low: ee.Image,
             base_cache: dict) -> list[dict]:
    d = dt.date.fromisoformat(day)
    col = s1(day, (d + dt.timedelta(days=1)).isoformat()).filter(
        ee.Filter.eq("relativeOrbitNumber_start", orbit))
    key = (orbit, d.year)
    if key not in base_cache:
        base_cache[key] = baseline(orbit, d.year)
    base = base_cache[key]
    if base is None:
        return []
    now = col.map(_vv).mosaic()
    seen = now.mask().And(base.mask()).And(low)
    water = now.lt(WATER_DB)
    new = water.And(base.lt(WATER_DB).Not())
    # masked to low ground the pass actually saw, so the count is that area
    img = ee.Image.cat([new.rename("new_water"), water.rename("water")]).updateMask(seen)
    stats = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean().combine(
        ee.Reducer.count(), sharedInputs=True), scale=SCALE_M, tileScale=4).getInfo()
    rows = []
    for f in stats["features"]:
        p = f["properties"]
        n = p.get("new_water_count") or 0
        if n and p.get("new_water_mean") is not None:
            rows.append({"date": day, "orbit": orbit, "k": p["k"],
                         "new_water": p["new_water_mean"], "water": p["water_mean"],
                         "n_low": n})
    return rows


def run(d0: str, d1: str) -> None:
    ee.Initialize(project=PROJECT)
    c = cells()
    fc = cell_fc(c, when_grid.lattice()["deg"])
    low = ee.Image("MERIT/Hydro/v1_0_1").select("hnd").lt(HAND_MAX_M)
    done = set()
    old = pd.read_parquet(OUT) if OUT.exists() else pd.DataFrame()
    if len(old):
        done = set(zip(old["date"], old["orbit"]))
    todo = [p for p in passes(d0, d1) if p not in done]
    print(f"  {len(c)} rain cells; {len(todo)} new passes {d0} .. {d1}", flush=True)
    base_cache: dict = {}
    rows = []
    pool = ThreadPoolExecutor(max_workers=1)
    for i, (day, orbit) in enumerate(todo):
        t0 = time.time()
        try:
            r = pool.submit(one_pass, day, orbit, fc, low, base_cache).result(timeout=PASS_TIMEOUT_S)
        except FutTimeout:
            print(f"    {day} orbit {orbit}: timed out, skipped", flush=True)
            pool.shutdown(wait=False, cancel_futures=True)
            pool = ThreadPoolExecutor(max_workers=1)
            continue
        except Exception as e:                                      # noqa: BLE001
            print(f"    {day} orbit {orbit}: {type(e).__name__}: {str(e)[:120]}", flush=True)
            continue
        rows += r
        print(f"    [{i+1}/{len(todo)}] {day} orbit {orbit:>3}: {len(r):>4} cells "
              f"({time.time()-t0:.0f}s)", flush=True)
        if rows and (i + 1) % 10 == 0:
            _save(old, rows)
    _save(old, rows)


def _save(old: pd.DataFrame, rows: list[dict]) -> None:
    df = pd.concat([old, pd.DataFrame(rows)], ignore_index=True)
    df = df.drop_duplicates(subset=["date", "orbit", "k"], keep="last")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--recent":
        n = int(a[1]) if len(a) > 1 else 14
        today = dt.date.today()
        run((today - dt.timedelta(days=n)).isoformat(), (today + dt.timedelta(days=1)).isoformat())
    else:
        run(a[0], a[1])
