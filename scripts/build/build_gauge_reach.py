"""Which rain cells each river gauge's water flows through, and the gauge
reading those cells see each day.

    python scripts/build/build_gauge_reach.py

Writes  data/interim/flood_forecast/gauge_reach.npz
            reach_km   (gauges x cells) distance downstream of the gauge, km;
                       NaN where the gauged river does not pass
            codes      gauge codes, in models/flood_when_gauge/stations.json order
        data/interim/flood_forecast/gauge_frac.npz   (aligned to when_dates)
            G          (days x cells) yesterday's reading of the gauge(s)
                       upstream, as a share of the way from ordinary to
                       threshold; the highest if several; NaN if none
            gauge_frac (days x gauges) the same, per gauge

A gauge reading is a measurement of the river itself, the strongest single
signal found for its own flooding (FLOOD_WHEN_PILOT_PLAN.md §13). The map's
day model reads rain only. This hands every rain cell the gauged river flows
into the reading from upstream, one day old, so the replay can test whether
it helps the map too.

The river is followed downhill on the 100 m flow-accumulation raster: from
the gauge (snapped to the biggest channel within 1.5 km), always step to the
neighbour carrying the most water. No flow-direction raster was kept, but on
a trunk river the downstream neighbour is the one with the highest
accumulation, and the walk stops at the grid edge or a pit. Gauge scales
(ordinary level, threshold, record breaks) are the ones the gauge models use.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform

import when_grid
from common import INTERIM, ROOT
from flood_forecast import imerg_index_full

OUT = INTERIM / "flood_forecast"
STATIONS = ROOT / "models" / "flood_when_gauge" / "stations.json"
SNAP_PX = 15                                     # 1.5 km
NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def walk(acc: np.ndarray, r: int, c: int) -> list[tuple[int, int, float]]:
    """(row, col, km from start) along the steepest-accumulation path."""
    H, W = acc.shape
    path, km = [(r, c, 0.0)], 0.0
    for _ in range(200_000):
        best, br, bc, step = acc[r, c], -1, -1, 0.0
        for dr, dc in NB:
            r2, c2 = r + dr, c + dc
            if 0 <= r2 < H and 0 <= c2 < W and acc[r2, c2] > best:
                best, br, bc, step = acc[r2, c2], r2, c2, (0.1414 if dr and dc else 0.1)
        if br < 0:
            break
        r, c, km = br, bc, km + step
        path.append((r, c, km))
    return path


def reach() -> tuple[np.ndarray, list[str], dict]:
    st = json.loads(STATIONS.read_text())
    with rasterio.open(INTERIM / "terrain_unmasked" / "hydro_flowacc_cells.tif") as s:
        acc = np.nan_to_num(s.read(1), nan=-1.0)
        tf = s.transform
    kidx = imerg_index_full()
    n = len(when_grid.cell_centres()[0])
    codes = list(st)
    R = np.full((len(codes), n), np.nan, dtype=np.float32)
    info = {}
    for i, code in enumerate(codes):
        m = st[code]
        xs, ys = transform("EPSG:4326", "EPSG:32646", [m["lon"]], [m["lat"]])
        c0, r0 = ~tf * (xs[0], ys[0])
        r0, c0 = int(r0), int(c0)
        win = acc[max(r0 - SNAP_PX, 0):r0 + SNAP_PX + 1, max(c0 - SNAP_PX, 0):c0 + SNAP_PX + 1]
        if win.size == 0 or win.max() <= 0:
            info[code] = {"name": m["name"], "snapped": False}
            continue
        dr, dc = np.unravel_index(np.argmax(win), win.shape)
        r, c = max(r0 - SNAP_PX, 0) + dr, max(c0 - SNAP_PX, 0) + dc
        path = walk(acc, r, c)
        for pr, pc, km in path:
            k = kidx[pr, pc]
            if k >= 0 and not (R[i, k] <= km):
                R[i, k] = km
        info[code] = {"name": m["name"], "snapped": True,
                      "snapped_catchment_km2_in_window": round(float(acc[r, c]) / 100, 1),
                      "path_km": round(path[-1][2], 1),
                      "cells_reached": int(np.isfinite(R[i]).sum())}
        print(f"  {m['name'][:18]:<19} catchment in window {acc[r, c]/100:>9,.0f} km2   "
              f"river followed {path[-1][2]:>6.0f} km   {int(np.isfinite(R[i]).sum()):>3} rain cells")
    return R, codes, info


def gauge_history(codes: list[str], dates: pd.DatetimeIndex) -> np.ndarray:
    """(days x gauges) the gauge's daily-max as a share of ordinary -> threshold,
    taken from the day BEFORE each date (the reading a morning forecast has)."""
    from train_flood_when_gauge import station_daily
    st = json.loads(STATIONS.read_text())
    daily = {s["code"]: s["daily"] for s in station_daily()}
    out = np.full((len(dates), len(codes)), np.nan, dtype=np.float32)
    for j, code in enumerate(codes):
        if code not in daily:
            continue
        m = st[code]
        frac = (daily[code] - m["base"]) / (m["threshold"] - m["base"])
        out[:, j] = frac.reindex(dates - pd.Timedelta(days=1)).to_numpy(np.float32)
    return out


def main() -> None:
    print("Gauge reach: following each gauged river downstream")
    R, codes, info = reach()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "gauge_reach.npz", reach_km=R, codes=np.array(codes))
    (OUT / "gauge_reach.json").write_text(json.dumps(info, indent=2))

    dates, _ = when_grid.load()
    dates = pd.DatetimeIndex(dates)
    print("\n  gauge history (one-day-old readings)...", flush=True)
    GF = gauge_history(codes, dates)
    reached = np.isfinite(R)                              # gauges x cells
    G = np.full((len(dates), R.shape[1]), np.nan, dtype=np.float32)
    for k in np.flatnonzero(reached.any(axis=0)):
        with np.errstate(all="ignore"):
            G[:, k] = np.nanmax(GF[:, reached[:, k]], axis=1)
    np.savez_compressed(OUT / "gauge_frac.npz", G=G, gauge_frac=GF)
    print(f"\n  {int(reached.any(axis=0).sum())} rain cells have a gauge upstream; "
          f"cell-days with a reading: {100*np.isfinite(G).mean():.1f}%")
    print(f"  wrote {OUT / 'gauge_reach.npz'} and {OUT / 'gauge_frac.npz'}")


if __name__ == "__main__":
    main()
