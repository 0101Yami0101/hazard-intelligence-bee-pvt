"""Open-Meteo daily rain over the CWC sediment stations' catchments, 2010-2026 (AD-02).

    $env:REGION = "assam"; python scripts/fetch/fetch_55_station_catchment_rain.py

The test was written first (EROSION_PLAN.md, "AD-02 part 1"). Points: the outlook's 0.2 deg
lattice inside each kept station's catchment (or the lattice point nearest its centre if
none falls inside). Points already in the outlook's Assam history (fetch_50) are reused;
only the rest are fetched, with fetch_20's restartable, rate-limit-aware archive fetch.

Output: data/interim/<region>/station_rain/{precip_mm.npy, dates.npy, points.json}
        points.json maps every station to its point indices
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

from common import INTERIM, PROCESSED, ROOT, record
import fetch_20_openmeteo_climatology as F20

GRID, START, END = 0.2, "2010-01-01", "2026-10-20"
MIN_INDIA, MIN_YEARS, MAX_KM2 = 95.0, 8, 60000
OUT = INTERIM / "station_rain"
CACHE = OUT / "_batches"


def stations() -> gpd.GeoDataFrame:
    g = gpd.read_file(ROOT / "data" / "processed" / "sediment_station_catchments.gpkg")
    g = g[(g.in_india_pct >= MIN_INDIA) & (g.catchment_km2 < MAX_KM2) & (g.y1 >= 2018)]
    return g[g.years >= MIN_YEARS].reset_index(drop=True)


def lattice_points(g: gpd.GeoDataFrame) -> tuple[pd.DataFrame, dict]:
    pts, by_station = {}, {}
    for _, s in g.iterrows():
        w, so, e, n = s.geometry.bounds
        mine = []
        for la in np.arange(np.floor(so / GRID) * GRID, n + GRID, GRID):
            for lo in np.arange(np.floor(w / GRID) * GRID, e + GRID, GRID):
                if s.geometry.contains(Point(lo, la)):
                    mine.append((round(float(la), 4), round(float(lo), 4)))
        if not mine:
            c = s.geometry.centroid
            mine = [(round(round(c.y / GRID) * GRID, 4), round(round(c.x / GRID) * GRID, 4))]
        for p in mine:
            pts.setdefault(p, len(pts))
        by_station[s.Station] = [pts[p] for p in mine]
    df = pd.DataFrame([{"lat": la, "lon": lo} for (la, lo), _ in sorted(pts.items(), key=lambda x: x[1])])
    return df, by_station


def main() -> None:
    g = stations()
    pts, by_station = lattice_points(g)
    print(f"Station catchment rain — {len(g)} stations, {len(pts)} lattice points", flush=True)
    # reuse the outlook's Assam history where the points coincide
    om = INTERIM / "rainfall_om"
    have = json.loads((om / "points.json").read_text())
    hist = np.load(om / "precip_mm.npy")
    hdates = pd.to_datetime(np.load(om / "dates.npy"))
    key = {(round(a, 4), round(b, 4)): i for i, (a, b) in enumerate(zip(have["lat"], have["lon"]))}
    reuse = [key.get((r.lat, r.lon)) for r in pts.itertuples()]
    todo = pts[[k is None for k in reuse]]
    print(f"  reused {sum(k is not None for k in reuse)} points; fetching {len(todo)}", flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    F20.CACHE = CACHE
    years = list(range(2010, 2027))
    chunks = [(f"{years[i]}-01-01", f"{min(years[i] + F20.YEAR_CHUNK - 1, years[-1])}-12-31")
              for i in range(0, len(years), F20.YEAR_CHUNK)]
    chunks[-1] = (chunks[-1][0], END)
    fetched = {}
    batches = [todo.iloc[i:i + F20.BATCH] for i in range(0, len(todo), F20.BATCH)]
    for bi, sub in enumerate(batches):
        parts = []
        for ci, (d0, d1) in enumerate(chunks):
            d = F20.fetch(sub.lat.tolist(), sub.lon.tolist(), d0, d1, f"b{bi:02d}_c{ci}")
            if d is None:
                raise SystemExit(f"  batch {bi} chunk {ci} FAILED — re-run to resume")
            parts.append(d)
            time.sleep(F20.PAUSE)
        b = pd.concat(parts).sort_index()
        for j, idx in enumerate(sub.index):
            fetched[idx] = b.iloc[:, j]
        print(f"    batch {bi + 1}/{len(batches)}", flush=True)
    dates = pd.date_range(START, END)
    arr = np.full((len(dates), len(pts)), np.nan, np.float32)
    for i, k in enumerate(reuse):
        if k is not None:
            s = pd.Series(hist[:, k], index=hdates).reindex(dates)
        else:
            s = fetched[i].reindex(dates)
        arr[:, i] = s.to_numpy(np.float32)
    OUT.mkdir(parents=True, exist_ok=True)
    np.save(OUT / "precip_mm.npy", arr)
    np.save(OUT / "dates.npy", dates.values.astype("datetime64[D]"))
    (OUT / "points.json").write_text(json.dumps({"lat": pts.lat.tolist(), "lon": pts.lon.tolist(),
                                                 "stations": by_station, "grid_deg": GRID,
                                                 "start": START, "end": END}, indent=1))
    record(OUT, source="Open-Meteo archive daily precipitation (CWC sediment station catchments)",
           url=F20.ARCHIVE, files=[OUT / "precip_mm.npy", OUT / "dates.npy", OUT / "points.json"],
           license_="Open-Meteo: CC-BY 4.0",
           notes=f"{len(pts)} lattice points over {len(g)} station catchments, {START} to {END} "
                 "(fetch_55_station_catchment_rain.py).")
    print(f"  wrote {arr.shape}, missing {np.isnan(arr).mean():.2%}")


if __name__ == "__main__":
    main()
