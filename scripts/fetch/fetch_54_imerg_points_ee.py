"""Daily GPM IMERG V07 Final rain at the outlook replay's points, from Earth Engine (E2.2).

    $env:REGION = "assam"; python scripts/fetch/fetch_54_imerg_points_ee.py

The replay's truth (EROSION_PLAN.md, "E2.2 part 1", clarification 4): NASA's OPeNDAP server
stopped accepting our connections on 2026-10-26, so IMERG comes from Earth Engine instead.
Half-hourly `NASA/GPM_L3/IMERG_V07` precipitation (mm/hr) is summed to UTC days
(x 0.5 h), and averaged over a 0.2 deg box round each replay point, 2013-2025.

One request per month (the month's days as bands, reduced over the 125 boxes), each cached
to disk so an interruption resumes.

Output: data/interim/<region>/outlook_replay/imerg_points.npz  dates [n_days], rain [n_days, n_points]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee
import numpy as np
import pandas as pd

from common import INTERIM, record

PROJECT = "earthengine-507510"
COLL = "NASA/GPM_L3/IMERG_V07"
YEARS = range(2013, 2026)
HALF = 0.1
OUT = INTERIM / "outlook_replay"
CACHE = OUT / "_imerg_months"


def month(points: ee.FeatureCollection, y: int, m: int) -> pd.DataFrame:
    f = CACHE / f"{y}{m:02d}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    days = pd.date_range(f"{y}-{m:02d}-01", periods=pd.Period(f"{y}-{m:02d}").days_in_month)
    col = ee.ImageCollection(COLL).select("precipitation")
    imgs = [col.filterDate(str(d.date()), str((d + pd.Timedelta(days=1)).date())).sum().multiply(0.5)
            .rename(f"d{d.day:02d}") for d in days]
    stack = ee.Image.cat(imgs)
    for attempt in range(6):
        try:
            fc = stack.reduceRegions(points, ee.Reducer.mean(), scale=11132).getInfo()
            break
        except Exception as exc:  # noqa: BLE001
            print(f"      {y}-{m:02d} try {attempt + 1}: {str(exc)[:120]}", flush=True)
            time.sleep(20 * (attempt + 1))
    else:
        raise RuntimeError(f"{y}-{m:02d} failed")
    rows = sorted(fc["features"], key=lambda x: x["properties"]["i"])
    arr = np.array([[r["properties"].get(f"d{d.day:02d}", np.nan) for r in rows] for d in days], np.float32)
    df = pd.DataFrame(arr, index=days)
    df.columns = [str(c) for c in df.columns]
    df.to_parquet(f)
    return df


def main() -> None:
    ee.Initialize(project=PROJECT)
    z = np.load(OUT / "forecast_daily.npz")
    lat, lon = z["lat"], z["lon"]
    points = ee.FeatureCollection([
        ee.Feature(ee.Geometry.Rectangle([float(lo) - HALF, float(la) - HALF, float(lo) + HALF, float(la) + HALF]),
                   {"i": i}) for i, (la, lo) in enumerate(zip(lat, lon))])
    CACHE.mkdir(parents=True, exist_ok=True)
    print(f"IMERG V07 Final at {len(lat)} replay points, {YEARS.start}-{YEARS.stop - 1}", flush=True)
    t0, parts = time.time(), []
    for y in YEARS:
        for m in range(1, 13):
            parts.append(month(points, y, m))
        print(f"    {y} done, {(time.time() - t0) / 60:.0f} min", flush=True)
    full = pd.concat(parts).sort_index()
    dest = OUT / "imerg_points.npz"
    np.savez_compressed(dest, dates=full.index.values.astype("datetime64[D]"), rain=full.to_numpy(np.float32),
                        lat=lat, lon=lon)
    record(OUT, source="GPM IMERG V07 Final, half-hourly, via Earth Engine (NASA/GPM_L3/IMERG_V07)",
           url=f"Earth Engine {COLL}", files=[dest], license_="NASA open data",
           notes="Summed to UTC days, mean over a 0.2 deg box round each outlook-replay point, 2013-2025 "
                 "(fetch_54_imerg_points_ee.py).")
    print(f"  wrote {dest}: {full.shape}, missing {np.isnan(full.to_numpy()).mean():.2%}")


if __name__ == "__main__":
    main()
