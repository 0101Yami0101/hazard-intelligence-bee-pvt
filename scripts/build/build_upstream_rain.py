"""Rain over each area's UPSTREAM catchment, not just on the spot.

    python scripts/build/build_upstream_rain.py

Writes  data/interim/flood_forecast/upstream_weights.npz
        data/interim/flood_forecast/upstream_rain_pct.npz   (aligned to when_dates)

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
WHEN reads rain at the point. A river floods from the rain that fell on its
whole catchment, often a day or more earlier and tens of kilometres away. On
24 May 2024 — the biggest reported flood day in the record — the flooded
places had 0-10 mm of local rain in the days before, and the forecast came
out quieter than normal. The water came from upstream.

For each ~10 km rain cell, this traces the catchment of the biggest river
channel inside it (its highest flow-accumulation cell), records which rain
cells that catchment covers and by how much, and turns daily rain into
catchment-mean rain. The same 3- and 7-day totals and the same "percentile of
this place's own monsoon" scaling WHEN uses are then applied, so the day
model can weigh local and upstream rain side by side.

════════════════════════════════════════════════════════════════════════════
LIMIT
════════════════════════════════════════════════════════════════════════════
Catchments are traced on the grid window's DEM and averaged over the rain
lattice, both of which stop at the window edge. The Siang's catchment runs
deep into Tibet, so for the largest trunk rivers the "upstream" rain is only
the in-window part. `coverage` records, per rain cell, how much of the traced
catchment has rain data; it is not a measure of how much of the TRUE
catchment was seen, which for the Siang is far less.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np
import pandas as pd
import rasterio

from common import INTERIM

import when_grid
from flood_forecast import imerg_index_full

OUT = INTERIM / "flood_forecast"
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)       # same as hydrology.py

# ESRI D8 codes -> (drow, dcol). pysheds' own catchment tracer is not used:
# it has no bounds checks and dies with a Windows access violation on some
# pour points (seen on border and interior outlets alike). This tracer is
# checked against the flow-accumulation raster instead.
_D8 = {1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1),
       16: (0, -1), 32: (-1, -1), 64: (-1, 0), 128: (-1, 1)}


def downstream_index(fdir: np.ndarray) -> np.ndarray:
    """Flat index of each cell's downstream neighbour; -1 = sink or off-grid."""
    H, W = fdir.shape
    rows, cols = np.indices((H, W))
    down = np.full(H * W, -1, dtype=np.int64)
    for code, (dr, dc) in _D8.items():
        m = fdir == code
        r2, c2 = rows[m] + dr, cols[m] + dc
        ok = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
        src = (rows[m] * W + cols[m])[ok]
        down[src] = r2[ok] * W + c2[ok]
    return down


def _numba_tracer():
    from numba import njit

    @njit(cache=True)
    def trace(indptr, ups, start, stamp, mark, stack, kidx_flat, out_row):
        """Count, per rain cell, the 100 m cells upstream of `start`
        (inclusive). `stamp` avoids clearing a visited array per outlet."""
        top = 0
        stack[top] = start
        top += 1
        stamp[start] = mark
        n = 0
        while top > 0:
            top -= 1
            v = stack[top]
            n += 1
            k = kidx_flat[v]
            if k >= 0:
                out_row[k] += 1.0
            for e in range(indptr[v], indptr[v + 1]):
                u = ups[e]
                if stamp[u] != mark:
                    stamp[u] = mark
                    stack[top] = u
                    top += 1
        return n

    return trace


def weights() -> dict:
    path = OUT / "upstream_weights.npz"
    if path.exists():
        return dict(np.load(path))
    if not hasattr(np, "in1d"):
        np.in1d = np.isin                        # pysheds vs NumPy 2 shim, as hydrology.py
    from pysheds.grid import Grid

    t0 = time.time()
    dem_path = str(INTERIM / "terrain" / "_dem_unmasked_m.tif")
    g = Grid.from_raster(dem_path)
    dem = g.read_raster(dem_path)
    dem = g.resolve_flats(g.fill_depressions(g.fill_pits(dem)))
    fdir = np.asarray(g.flowdir(dem, dirmap=DIRMAP))
    del dem, g
    print(f"  flow directions ready ({time.time()-t0:.0f}s)")

    with rasterio.open(INTERIM / "terrain_unmasked" / "hydro_flowacc_cells.tif") as s:
        acc = s.read(1)
    kidx = imerg_index_full()
    n = len(when_grid.cell_centres()[0])

    # Reverse graph: for every cell, the cells that drain straight into it.
    down = downstream_index(fdir)
    del fdir
    N = down.size
    has = down >= 0
    src = np.flatnonzero(has).astype(np.int32)
    dst = down[has]
    order_e = np.argsort(dst, kind="stable")
    ups = src[order_e]
    indptr = np.zeros(N + 1, dtype=np.int64)
    np.add.at(indptr, dst + 1, 1)
    indptr = np.cumsum(indptr)
    del down, src, dst, order_e, has
    print(f"  reverse drainage graph built ({time.time()-t0:.0f}s)")

    # Outlet of each rain cell = its highest-accumulation 100 m cell.
    a = np.nan_to_num(acc, nan=-1.0)
    flat_k = kidx.ravel()
    flat_a = a.ravel()
    order = np.lexsort((-flat_a, flat_k))                # by cell, then acc desc
    ks = flat_k[order]
    first = np.r_[True, ks[1:] != ks[:-1]]
    outlet = np.full(n, -1, dtype=np.int64)
    sel = first & (ks >= 0)
    outlet[ks[sel]] = order[sel]

    trace = _numba_tracer()
    stamp = np.full(N, -1, dtype=np.int32)
    stack = np.empty(N, dtype=np.int32)
    kflat = kidx.ravel().astype(np.int32)
    W = np.zeros((n, n), dtype=np.float32)               # W[k, j] = cells of rain cell j upstream of k's outlet
    up_km2 = np.zeros(n, dtype=np.float32)
    mismatch = []
    for k in range(n):
        if outlet[k] < 0:
            continue
        cnt = trace(indptr, ups, int(outlet[k]), stamp, k, stack, kflat, W[k])
        up_km2[k] = cnt / 100.0
        # Independent check: the traced count must equal flow accumulation
        # at the outlet (pysheds counts the cell itself, as this does).
        expect = flat_a[outlet[k]]
        if expect > 0 and abs(cnt - expect) > 0.001 * expect:
            mismatch.append((k, cnt, float(expect)))
        if k % 200 == 0:
            print(f"    {k:>5}/{n}  {time.time()-t0:.0f}s", flush=True)
    print(f"  traced vs flow-accumulation mismatches: {len(mismatch)}"
          f"{'  e.g. ' + str(mismatch[:3]) if mismatch else ''}")

    coverage = np.where(up_km2 > 0, W.sum(1) / 100.0 / np.maximum(up_km2, 1e-9), 0.0)
    out = {"W": W, "outlet": outlet, "upstream_km2": up_km2, "coverage": coverage}
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **out)
    print(f"  wrote {path}  ({time.time()-t0:.0f}s)")
    return out


def upstream_percentiles(w: dict) -> dict:
    """Catchment-mean daily rain -> 3/7-day totals -> each cell's own monsoon
    percentile, exactly the scaling WHEN applies to local rain."""
    L = when_grid.lattice()
    rain = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    rain = np.asarray(rain).reshape(rain.shape[0], L["nlat"] * L["nlon"]).astype(np.float32)
    rain = np.nan_to_num(rain, nan=0.0)
    Wn = w["W"] / np.maximum(w["W"].sum(1, keepdims=True), 1.0)
    up = rain @ Wn.T                                     # (days, cells)

    dates = pd.to_datetime(np.load(INTERIM / "rainfall" / "dates.npy").astype("datetime64[D]"))
    mons = np.asarray((dates.month >= 5) & (dates.month <= 10))
    out = {}
    for name, win in (("up_r3", 3), ("up_r7", 7)):
        tot = pd.DataFrame(up).rolling(win, min_periods=win).sum().to_numpy(np.float32)
        pct = np.full(tot.shape, np.nan, dtype=np.float32)
        for k in range(tot.shape[1]):
            if w["W"][k].sum() == 0:
                continue
            col = tot[:, k]
            clim = np.sort(col[mons & np.isfinite(col)])
            fin = np.isfinite(col)
            pct[fin, k] = np.searchsorted(clim, col[fin], side="left") / len(clim)
        out[name] = pct
    when_dates = pd.to_datetime(np.load(OUT / "when_dates.npy"))
    keep = np.asarray(dates.isin(when_dates))
    return {k: v[keep] for k, v in out.items()}


def main() -> None:
    print("Upstream catchment rain")
    w = weights()
    big = w["upstream_km2"] > 1000
    print(f"  {int((w['upstream_km2'] > 0).sum()):,} rain cells traced; "
          f"median upstream {np.median(w['upstream_km2'][w['upstream_km2']>0]):,.0f} km2; "
          f"{int(big.sum())} drain >1,000 km2")
    pct = upstream_percentiles(w)
    np.savez_compressed(OUT / "upstream_rain_pct.npz", **pct)
    print(f"  wrote {OUT / 'upstream_rain_pct.npz'}  {pct['up_r3'].shape}")


if __name__ == "__main__":
    main()
