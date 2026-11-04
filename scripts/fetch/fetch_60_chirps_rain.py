"""CHIRPS v2.0 daily rain, 0.05 degree, 1981 to now, from Earth Engine.

    python scripts/fetch/fetch_60_chirps_rain.py

A third independent rain history beside Open-Meteo (what the forecast reads)
and IMD's gauge grid (fetch_59_imd_rain.py): satellite infrared blended with
gauges, about 5.5 km. Stored for cross-checks; no product reads it yet.

One box holds both regions (89.5-97.5E, 24.0-29.6N), on CHIRPS's own grid so
nothing is resampled. One file a year, days x rows x columns, float32 mm/day,
NaN = no data. A year is one request (~26 MB); files already on disk are kept.

Licence: free and open (Climate Hazards Center, UC Santa Barbara);
cite Funk et al. 2015, Scientific Data 2, 150066.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee
import numpy as np

from common import WEATHER, record

PROJECT = "earthengine-507510"
COL = "UCSB-CHG/CHIRPS/DAILY"
RES = 0.05
W, S, E, N = 89.5, 24.0, 97.5, 29.6          # both regions, on whole CHIRPS cells
OUT = WEATHER / "chirps_daily"


def year(y: int) -> tuple[np.ndarray, list[str]] | None:
    """One year, fetched 90 days a request (a whole year's band list makes the
    reply header too large for numpy to load)."""
    col = ee.ImageCollection(COL).filterDate(f"{y}-01-01", f"{y + 1}-01-01").select("precipitation")
    n = col.size().getInfo()
    if n == 0:
        return None
    w, h = round((E - W) / RES), round((N - S) / RES)
    lst = col.toList(n)
    mm, days = [], []
    for i in range(0, n, 90):
        img = ee.ImageCollection(lst.slice(i, min(i + 90, n))).toBands()
        arr = ee.data.computePixels({
            "expression": img, "fileFormat": "NUMPY_NDARRAY",
            "grid": {"dimensions": {"width": w, "height": h},
                     "affineTransform": {"scaleX": RES, "shearX": 0, "translateX": W,
                                         "shearY": 0, "scaleY": -RES, "translateY": N},
                     "crsCode": "EPSG:4326"}})
        mm += [arr[k].astype(np.float32) for k in arr.dtype.names]
        days += [k.split("_")[-2] if k.count("_") > 1 else k.split("_")[0] for k in arr.dtype.names]
    return np.stack(mm), days


def main() -> None:
    ee.Initialize(project=PROJECT)
    OUT.mkdir(parents=True, exist_ok=True)
    for y in range(1981, date.today().year + 1):
        dest = OUT / f"chirps_{y}.npz"
        if dest.exists() and y < date.today().year:
            continue
        got = year(y)
        if got is None:
            print(f"  {y}: no days yet")
            continue
        mm, days = got
        mm[mm < 0] = np.nan
        np.savez_compressed(dest, mm=mm, days=np.array(days), west=W, north=N, res=RES)
        print(f"  {y}: {mm.shape[0]} days  {dest.stat().st_size / 1e6:.1f} MB", flush=True)
    record(OUT, source="CHIRPS v2.0 daily rainfall (UCSB Climate Hazards Center)",
           url=f"Earth Engine computePixels ({COL})", files=sorted(OUT.glob("chirps_*.npz")),
           license_="Free and open; cite Funk et al. 2015",
           notes="0.05 deg, 1981-now, one box for both regions on CHIRPS's own grid. "
                 "Third rain ruler for cross-checks; no product reads it yet.")


if __name__ == "__main__":
    main()
