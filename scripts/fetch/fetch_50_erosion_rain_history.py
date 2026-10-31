"""Open-Meteo daily-rain history at the weekly erosion outlook's points (Assam).

    $env:REGION = "assam"; python scripts/fetch/fetch_50_erosion_rain_history.py

The outlook compares next week's forecast rain with the SAME source's history at
the same place (EROSION_PLAN.md, "E2.1 part 1"; why: core/rainfall.py). Points are
a 0.2 deg lattice wherever a 0.2 deg box round the point holds in-state cells, the
spacing of the live Arunachal products.

Re-uses fetch_20's restartable, rate-limit-aware archive fetch (each batch cached
to disk). fetch_20 itself, and the Arunachal products' points, are untouched.

Output: data/interim/<region>/rainfall_om/{precip_mm.npy, dates.npy, points.json}
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import datetime as dt
import json
import time

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

import grid as G
from common import AOI_BBOX, AOI_NAME, INTERIM, record
import fetch_20_openmeteo_climatology as F20

GRID_DEG = 0.2
START_YEAR = 2010


def query_points() -> pd.DataFrame:
    with rasterio.open(INTERIM / "state_mask.tif") as s:
        inside = s.read(1).astype(bool)
    w, s_, e, n = AOI_BBOX
    lats = np.arange(np.ceil(s_ / GRID_DEG) * GRID_DEG, n, GRID_DEG)
    lons = np.arange(np.ceil(w / GRID_DEG) * GRID_DEG, e, GRID_DEG)
    tr = Transformer.from_crs(4326, G.CRS, always_xy=True)
    pts = []
    half = GRID_DEG / 2
    for la in lats:
        for lo in lons:
            xs, ys = tr.transform([lo - half, lo + half], [la - half, la + half])
            r0, c0 = G.xy_to_rowcol(min(xs), max(ys))
            r1, c1 = G.xy_to_rowcol(max(xs), min(ys))
            r0, c0 = max(int(r0), 0), max(int(c0), 0)
            r1, c1 = min(int(r1), G.NROWS - 1), min(int(c1), G.NCOLS - 1)
            if r1 >= r0 and c1 >= c0 and inside[r0:r1 + 1, c0:c1 + 1].any():
                pts.append({"lat": round(float(la), 4), "lon": round(float(lo), 4)})
    return pd.DataFrame(pts)


def main() -> None:
    out = F20.OUT
    F20.CACHE.mkdir(parents=True, exist_ok=True)
    pts = query_points()
    end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    years = list(range(START_YEAR, int(end[:4]) + 1))
    chunks = [(f"{years[i]}-01-01", f"{min(years[i] + F20.YEAR_CHUNK - 1, years[-1])}-12-31")
              for i in range(0, len(years), F20.YEAR_CHUNK)]
    chunks[-1] = (chunks[-1][0], end)
    batches = [pts.iloc[i:i + F20.BATCH] for i in range(0, len(pts), F20.BATCH)]
    print(f"Erosion-outlook rain history — {AOI_NAME}: {len(pts)} points (~{GRID_DEG} deg), "
          f"{START_YEAR} .. {end}; {len(batches) * len(chunks)} calls", flush=True)
    t0, blocks = time.time(), []
    for bi, sub in enumerate(batches):
        ps = []
        for ci, (d0, d1) in enumerate(chunks):
            d = F20.fetch(sub.lat.tolist(), sub.lon.tolist(), d0, d1, f"b{bi:02d}_c{ci}")
            if d is None:
                print(f"  batch {bi} chunk {ci} FAILED — rerun to resume")
                return
            ps.append(d)
            time.sleep(F20.PAUSE)
        b = pd.concat(ps).sort_index()
        b.columns = [f"{bi}_{k}" for k in range(b.shape[1])]
        blocks.append(b)
        print(f"    batch {bi + 1}/{len(batches)}  {(time.time() - t0) / 60:.0f} min", flush=True)
    full = pd.concat(blocks, axis=1)
    full = full.loc[~full.index.duplicated()].sort_index()
    np.save(out / "precip_mm.npy", full.to_numpy(dtype=np.float32))
    np.save(out / "dates.npy", full.index.values.astype("datetime64[D]"))
    (out / "points.json").write_text(json.dumps({
        "lat": pts.lat.tolist(), "lon": pts.lon.tolist(), "grid_deg": GRID_DEG,
        "n_points": int(len(pts)), "source": "Open-Meteo archive — same chain as the forecast API",
        "start": str(full.index[0].date()), "end": str(full.index[-1].date())}, indent=2))
    record(out, source="Open-Meteo archive daily precipitation (erosion outlook points)",
           url=F20.ARCHIVE, files=[out / "precip_mm.npy", out / "dates.npy", out / "points.json"],
           license_="Open-Meteo: CC-BY 4.0",
           notes=f"{len(pts)} points on a {GRID_DEG} deg lattice over the region, {START_YEAR} to {end} "
                 "(fetch_50_erosion_rain_history.py).")
    print(f"  wrote {full.shape[0]:,} days x {full.shape[1]} points")


if __name__ == "__main__":
    main()
