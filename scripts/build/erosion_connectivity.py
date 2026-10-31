"""AD-25: does the soil reach the water? Sediment connectivity and delivery (InVEST SDR style).

    $env:REGION = "assam"; python scripts/build/erosion_connectivity.py

Eroded soil that never reaches a stream silts no river and no reservoir. This estimates,
for every scored square, the share of its soil loss likely to reach the stream network:

    IC   index of connectivity (Borselli, Cassi & Torri 2008):
             IC = log10(D_up / D_dn)
             D_up = W_up * S_up * sqrt(A)    mean weight and slope over the upslope area A
             D_dn = sum over the downslope path to a stream of d_i / (W_i * S_i)
         W = the recipe's cover factor C (impedance), S = slope (m/m, kept in 0.005-1),
         streams = squares draining >= 1 km2 (and water)
    SDR  sediment delivery ratio (Vigiak et al. 2012, as in InVEST SDR):
             SDR = SDR_max / (1 + exp((IC0 - IC) / k)),  IC0 = 0.5, k = 2, SDR_max = 0.8
    delivered = A (the recipe's loss) x SDR, t/ha/yr

Flow directions are recomputed exactly as scripts/build/hydrology.py does (pysheds, the
same DEM conditioning and direction map). The downslope sums use pointer doubling: each
pass doubles the stretch of path summed, so 26 passes cover any path on the grid.

These are model estimates of the same kind as the soil loss; measured river mud (AD-02,
AD-11) is what can later check them.

Outputs: data/interim/<region>/erosion/erosion_ic.tif, erosion_sdr.tif,
         erosion_delivered_tpha.tif; reports/erosion_connectivity_<region>.csv (+ _districts)
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, ROOT, outline

warnings.filterwarnings("ignore")

E, TER = INTERIM / "erosion", INTERIM / "terrain"
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)               # as hydrology.py: N NE E SE S SW W NW
OFFSETS = {64: (-1, 0), 128: (-1, 1), 1: (0, 1), 2: (1, 1), 4: (1, 0), 8: (1, -1), 16: (0, -1), 32: (-1, -1)}
STREAM_CELLS = 100                                   # >= 1 km2 upstream
W_FILL = 0.1                                         # cover weight where the recipe has none (towns, water)
IC0, K_B, SDR_MAX = 0.5, 2.0, 0.8                    # InVEST SDR defaults


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def write(name, arr):
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="float32", crs=G.CRS,
                transform=G.TRANSFORM, nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(E / f"{name}.tif", "w", **prof) as d:
        d.write(arr.astype(np.float32), 1)


def flow_directions() -> np.ndarray:
    if not hasattr(np, "in1d"):
        np.in1d = np.isin
    from pysheds.grid import Grid
    dem_path = TER / "_dem_unmasked_m.tif"
    pg = Grid.from_raster(str(dem_path))
    dem = pg.read_raster(str(dem_path))
    dem = pg.resolve_flats(pg.fill_depressions(pg.fill_pits(dem)))
    fdir = pg.flowdir(dem, dirmap=DIRMAP)
    return pg, fdir


def main() -> None:
    from erosion_priority import ids_of
    t0 = time.time()
    print(f"Sediment connectivity — {AOI_NAME}", flush=True)
    pg, fdir = flow_directions()
    print(f"  flow directions {time.time() - t0:.0f}s", flush=True)
    C = rd(E / "erosion_C.tif")
    W = np.where(np.isfinite(C), C, W_FILL).astype(np.float64)
    W = np.maximum(W, 0.001)
    S = np.clip(np.tan(np.radians(rd(TER / "terrain_slope_deg.tif").astype(np.float64))), 0.005, 1.0)
    from pysheds.sview import Raster
    as_raster = lambda a: Raster(np.asarray(a, dtype=np.float64), viewfinder=fdir.viewfinder)
    n_up = np.asarray(pg.accumulation(fdir, dirmap=DIRMAP), dtype=np.float64)
    w_up = np.asarray(pg.accumulation(fdir, weights=as_raster(W), dirmap=DIRMAP), dtype=np.float64)
    s_up = np.asarray(pg.accumulation(fdir, weights=as_raster(S), dirmap=DIRMAP), dtype=np.float64)
    n_up = np.maximum(n_up, 1)
    D_up = (w_up / n_up) * (s_up / n_up) * np.sqrt(n_up * G.CELL ** 2)
    print(f"  upslope terms {time.time() - t0:.0f}s", flush=True)

    # downstream pointer per cell; streams and cells leaving the grid point to themselves
    fd = np.asarray(fdir)
    rows, cols = np.indices(fd.shape, dtype=np.int32)
    nxt = np.arange(fd.size, dtype=np.int64).reshape(fd.shape)
    step = np.zeros(fd.shape, np.float64)
    for code, (dr, dc) in OFFSETS.items():
        m = fd == code
        r2, c2 = rows[m] + dr, cols[m] + dc
        inside = (r2 >= 0) & (r2 < fd.shape[0]) & (c2 >= 0) & (c2 < fd.shape[1])
        idx = np.flatnonzero(m.ravel())
        nxt.ravel()[idx[inside]] = r2[inside].astype(np.int64) * fd.shape[1] + c2[inside]
        step.ravel()[idx[inside]] = G.CELL * (np.sqrt(2) if dr and dc else 1.0)
    stream = n_up >= STREAM_CELLS
    nxt = nxt.ravel()
    cost = (step / (W * S)).ravel()
    sflat = stream.ravel()
    cost[sflat] = 0.0
    nxt[sflat] = np.flatnonzero(sflat)
    total = cost.copy()
    for _ in range(26):
        total = total + total[nxt]
        nxt = nxt[nxt]
    D_dn = np.maximum(total.reshape(fd.shape), G.CELL / 1.0)   # at least one cell's own step on streams
    print(f"  downslope terms {time.time() - t0:.0f}s", flush=True)

    with np.errstate(invalid="ignore", divide="ignore"):
        IC = np.log10(D_up / D_dn)
    SDR = SDR_MAX / (1 + np.exp((IC0 - IC) / K_B))
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A = rd(E / "erosion_A_tpha.tif")
    deliv = np.where(ok, A * SDR, np.nan)
    inside_state = rd(INTERIM / "state_mask.tif").astype(bool)
    IC[~inside_state] = np.nan
    SDR[~ok] = np.nan
    write("erosion_ic", IC)
    write("erosion_sdr", SDR)
    write("erosion_delivered_tpha", deliv)

    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    out = {}
    for kind, gdf, key in (("catchments", bas, "HYBAS_ID"), ("districts", dist, "NAME_2")):
        ids = ids_of(gdf)
        n = len(gdf)
        m = ok & (ids > 0) & np.isfinite(deliv)
        cnt = np.bincount(ids[m], minlength=n + 1)[1:]
        loss = np.bincount(ids[m], weights=A[m].astype(np.float64), minlength=n + 1)[1:]
        dl = np.bincount(ids[m], weights=deliv[m].astype(np.float64), minlength=n + 1)[1:]
        t = pd.DataFrame({key: gdf[key].values, "loss_t_per_yr": np.round(loss), "delivered_t_per_yr": np.round(dl),
                          "delivered_tpha": np.round(dl / np.maximum(cnt, 1), 2),
                          "delivered_share_pct": np.round(100 * dl / np.maximum(loss, 1e-9), 1)})
        t["rank_delivered"] = t.delivered_tpha.rank(ascending=False, method="min").astype(int)
        out[kind] = t
    out["catchments"].to_csv(ROOT / "reports" / f"erosion_connectivity_{AOI_NAME}.csv", index=False)
    out["districts"].to_csv(ROOT / "reports" / f"erosion_connectivity_{AOI_NAME}_districts.csv", index=False)
    v = SDR[ok & np.isfinite(SDR)]
    print(f"  SDR on scored land: p10 {np.percentile(v, 10):.3f}  median {np.median(v):.3f}  p90 {np.percentile(v, 90):.3f}")
    tot_l, tot_d = float(np.nansum(np.where(ok, A, 0))), float(np.nansum(deliv))
    print(f"  state: loss {tot_l / 1e6:.1f} Mt/yr, delivered to streams {tot_d / 1e6:.1f} Mt/yr ({100 * tot_d / tot_l:.0f}%)")
    print(out["districts"].sort_values("delivered_tpha", ascending=False).head(8).to_string(index=False))
    print(f"  done {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
