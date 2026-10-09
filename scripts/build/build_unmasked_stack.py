"""The 100 m feature stack WITHOUT the Arunachal clip, for the flood WHERE model.

    python scripts/build/build_unmasked_stack.py

════════════════════════════════════════════════════════════════════════════
WHY THIS EXISTS
════════════════════════════════════════════════════════════════════════════
Every layer in `data/interim/terrain/` and `data/interim/features/` is
computed over the full 5,900 x 3,200 grid and then clipped to the state
polygon at write time. For landslides that is right — the product is an
Arunachal map and the labels are Arunachal polygons.

For flood WHERE it silently throws away most of the evidence. Measured over
the 3,546 extracted pixel masks:

    events with any flooded cell, full grid window     2,508
    events with any flooded cell, inside the AP clip     361
    flooded 100 m cells, full grid window          1,400,760
    flooded 100 m cells, inside the AP clip           60,673   (4.3%)

The reason is geography, not a bug: Arunachal's floods are concentrated on
the Brahmaputra and its tributaries where they leave the hills, and the
state boundary runs along that floodplain. Clipping to the polygon cuts the
training set at exactly the landform the model most needs to learn.

So this script rebuilds the same layers unclipped. It is not a new method —
`terrain.py` and `hydrology.py` already compute everything unmasked and only
apply `state_mask.tif` on the final write, and the derivation functions are
imported from them here rather than copied, so the two cannot drift.

════════════════════════════════════════════════════════════════════════════
WHAT IS AND ISN'T AVAILABLE OUTSIDE THE STATE
════════════════════════════════════════════════════════════════════════════
    terrain, hydrology   ✅ Copernicus DEM covers the whole window
    soil (SoilGrids)     ✅ already global — the existing rasters are 99.6%
                            covered and are reused in place, not rebuilt
    land cover (ESA)     ✅ tiles on disk cover the window; rebuilt here
    geology (APSSDI)     ❌ Arunachal-only, by definition. DROPPED from the
                            flood feature set — for inundation extent the
                            physics that matters is HAND, channel size and
                            slope, not bedrock class

Output: data/interim/terrain_unmasked/*.tif, same grid, same dtype, no clip.
Each step is skipped if its output already exists, so the script is resumable.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import rasterio
from affine import Affine
from rasterio.enums import Resampling
from rasterio.warp import reproject, transform_bounds
from scipy import ndimage

import grid as G
import terrain as T
from common import INTERIM, TERRAIN as RAW_TERRAIN, RAW

warnings.filterwarnings("ignore")

SRC = INTERIM / "terrain"
OUT = INTERIM / "terrain_unmasked"
LC_TILES = RAW / "04_landcover" / "esa_worldcover_10m_2021"

# A cell is "drainage" once this much upslope area drains through it.
# Identical to build_flood_layers.py so HAND means the same thing everywhere.
CHANNEL_CELLS = 10_000          # x 100 m x 100 m = 100 km2

# ...and the same thing again for SMALL streams. 100 km2 is a sensible
# threshold on the Brahmaputra and a useless one in a Tawang side valley,
# where the stream that floods the village drains 15 km2. Measured only
# against big channels, a hamlet 30 m above its own creek reports a HAND of
# several hundred metres — the height of the ridge between it and the nearest
# big river — and the model reads it as unfloodable ground. Two scales, so
# both the trunk river and the local creek are represented.
CHANNEL_CELLS_SMALL = 1_000     # x 100 m x 100 m = 10 km2

PROFILE = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1,
               dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
               nodata=np.nan, compress="deflate", tiled=True,
               blockxsize=256, blockysize=256)


def tick(t0: float, msg: str) -> None:
    print(f"  [{time.time()-t0:6.0f}s] {msg}", flush=True)


def write(name: str, arr: np.ndarray, dtype: str = "float32") -> None:
    p = dict(PROFILE)
    p["dtype"] = dtype
    if dtype != "float32":
        p["nodata"] = 0
    with rasterio.open(OUT / f"{name}.tif", "w", **p) as d:
        d.write(arr.astype(dtype), 1)


def have(*names: str) -> bool:
    return all((OUT / f"{n}.tif").exists() for n in names)


# ── step 1: terrain derivatives, unclipped ───────────────────────────────
def step_terrain(t0: float) -> None:
    if have(*T.LAYERS):
        tick(t0, "terrain derivatives already present, skipping")
        return
    tiles = sorted(RAW_TERRAIN.rglob("*.tif"))
    tick(t0, f"terrain derivatives from {len(tiles)} Copernicus tiles "
             f"({T.FINE} m -> {G.CELL} m)")

    srcs = [rasterio.open(t) for t in tiles]
    nodata = srcs[0].nodata
    out = {k: np.full(G.SHAPE, np.nan, dtype=np.float32) for k in T.LAYERS}
    n_chunks = ((G.NROWS + T.CHUNK - 1) // T.CHUNK) * ((G.NCOLS + T.CHUNK - 1) // T.CHUNK)
    done = 0

    for r0 in range(0, G.NROWS, T.CHUNK):
        for c0 in range(0, G.NCOLS, T.CHUNK):
            r1, c1 = min(r0 + T.CHUNK, G.NROWS), min(c0 + T.CHUNK, G.NCOLS)
            done += 1
            fh = (r1 - r0) * T.F + 2 * T.HALO
            fw = (c1 - c0) * T.F + 2 * T.HALO
            west = G.ORIGIN_X + c0 * G.CELL - T.HALO * T.FINE
            north = G.TOP_Y - r0 * G.CELL + T.HALO * T.FINE
            ftr = Affine(T.FINE, 0, west, 0, -T.FINE, north)
            east, south = west + fw * T.FINE, north - fh * T.FINE

            fine = np.full((fh, fw), np.nan, dtype=np.float32)
            for s in srcs:
                b = s.bounds
                sw, ss, se, sn = transform_bounds(G.CRS, s.crs, west, south, east, north)
                if b.right < sw or b.left > se or b.top < ss or b.bottom > sn:
                    continue
                patch = np.full((fh, fw), np.nan, dtype=np.float32)
                reproject(source=rasterio.band(s, 1), destination=patch,
                          dst_transform=ftr, dst_crs=G.CRS, dst_nodata=np.nan,
                          src_nodata=nodata, resampling=Resampling.bilinear)
                np.copyto(fine, patch, where=~np.isnan(patch))
            if np.all(np.isnan(fine)):
                continue

            slope, aspect, prof, plan = T.derivatives(fine, T.FINE)
            sl = slice(T.HALO, fh - T.HALO), slice(T.HALO, fw - T.HALO)
            fine_c, slope_c = fine[sl], slope[sl]
            aspect_c, prof_c, plan_c = aspect[sl], prof[sl], plan[sl]
            dst = (slice(r0, r1), slice(c0, c1))
            out["dem_elev_m"][dst] = T.block_reduce(fine_c, "mean")
            out["terrain_slope_deg"][dst] = T.block_reduce(slope_c, "mean")
            out["terrain_slope_max_deg"][dst] = T.block_reduce(slope_c, "max")
            out["terrain_relief_m"][dst] = (T.block_reduce(fine_c, "max")
                                            - T.block_reduce(fine_c, "min"))
            out["terrain_northness"][dst] = T.block_reduce(np.cos(aspect_c), "mean")
            out["terrain_eastness"][dst] = T.block_reduce(np.sin(aspect_c), "mean")
            out["terrain_curv_prof"][dst] = T.block_reduce(prof_c, "mean")
            out["terrain_curv_plan"][dst] = T.block_reduce(plan_c, "mean")

            if done % 20 == 0 or done == n_chunks:
                el = time.time() - t0
                tick(t0, f"    chunk {done}/{n_chunks}  ETA {el/done*(n_chunks-done):.0f}s")

    for s in srcs:
        s.close()
    for k in T.LAYERS:
        write(k, out[k])
        v = out[k][np.isfinite(out[k])]
        tick(t0, f"  {k:24} med {np.median(v):9.2f}  cover {100*len(v)/out[k].size:5.1f}%")


# ── step 2: flow routing, unclipped ──────────────────────────────────────
def step_hydrology(t0: float) -> None:
    if have("hydro_flowacc_cells", "hydro_twi"):
        tick(t0, "flow accumulation already present, skipping")
        return
    # pysheds still calls np.in1d, which NumPy 2.0 removed — same shim as
    # hydrology.py uses.
    if not hasattr(np, "in1d"):
        np.in1d = np.isin
    from pysheds.grid import Grid

    dem_path = SRC / "_dem_unmasked_m.tif"
    tick(t0, "flow routing (pysheds, D8) on the unmasked DEM")
    pgrid = Grid.from_raster(str(dem_path))
    dem = pgrid.read_raster(str(dem_path))
    dem = pgrid.fill_pits(dem)
    dem = pgrid.fill_depressions(dem)
    dem = pgrid.resolve_flats(dem)
    tick(t0, "  conditioned")
    fdir = pgrid.flowdir(dem, dirmap=(64, 128, 1, 2, 4, 8, 16, 32))
    acc = np.asarray(pgrid.accumulation(fdir, dirmap=(64, 128, 1, 2, 4, 8, 16, 32)),
                     dtype=np.float32)
    tick(t0, f"  max upslope {acc.max():,.0f} cells ({acc.max()*G.CELL**2/1e6:,.0f} km2)")

    with rasterio.open(OUT / "terrain_slope_deg.tif") as s:
        slope_deg = s.read(1)
    sca = (acc + 1.0) * G.CELL
    tan_b = np.tan(np.radians(np.maximum(slope_deg, 0.1)))
    with np.errstate(invalid="ignore", divide="ignore"):
        twi = np.log(sca / tan_b).astype(np.float32)
    twi[~np.isfinite(twi)] = np.nan

    write("hydro_flowacc_cells", acc)
    write("hydro_twi", twi)
    tick(t0, "  wrote flowacc + twi")


# ── step 3: HAND and channel geometry, from the unclipped routing ────────
def step_hand(t0: float) -> None:
    names = ("hydro_hand_m", "hydro_chan_km2", "dist_chan_m",
             "hydro_hand_small_m", "hydro_chan_small_km2", "dist_chan_small_m")
    if have(*names):
        tick(t0, "HAND already present, skipping")
        return
    with rasterio.open(SRC / "_dem_unmasked_m.tif") as s:
        z = s.read(1).astype(np.float32)
    with rasterio.open(OUT / "hydro_flowacc_cells.tif") as s:
        acc = s.read(1)

    for suffix, thresh in (("", CHANNEL_CELLS), ("_small", CHANNEL_CELLS_SMALL)):
        chan = np.isfinite(acc) & (acc >= thresh)
        tick(t0, f"HAND{suffix or ' (trunk)'}: {int(chan.sum()):,} channel cells "
                 f"(>= {thresh/100:.0f} km2)")
        dist, idx = ndimage.distance_transform_edt(~chan, sampling=(100.0, 100.0),
                                                   return_indices=True)
        hand = (z - z[idx[0], idx[1]]).astype(np.float32)
        np.maximum(hand, 0.0, out=hand)      # below its own channel = DEM artefact
        chan_km2 = (acc[idx[0], idx[1]].astype(np.float32) / 100.0)

        write(f"hydro_hand{suffix}_m", hand)
        write(f"hydro_chan{suffix}_km2", chan_km2)
        write(f"dist_chan{suffix}_m", dist.astype(np.float32))
        tick(t0, f"  median HAND{suffix} {np.median(hand):.0f} m")


# ── step 3b: valley confinement ──────────────────────────────────────────
# A flat 100 m patch on a narrow mountain valley floor and a flat patch on
# the open Brahmaputra plain look identical to every per-cell feature, yet a
# flood spreads far less on the first: the valley walls confine it. Measured:
# given a flood, WHERE over-predicted flooded ground ~1.8x inside Arunachal
# vs ~1.2x outside (§0p). Two neighbourhood measures describe confinement:
# the relief and the mean slope within ~1 km. They are shapes of the ground
# around the patch, not a label for "which part of the map" — the trap that
# got absolute elevation removed.
CONFINE_CELLS = 21                     # 21 x 100 m = 2.1 km window


def step_confinement(t0: float) -> None:
    if have("terrain_relief_2km_m", "terrain_slope_2km_deg"):
        tick(t0, "valley confinement already present, skipping")
        return
    with rasterio.open(SRC / "_dem_unmasked_m.tif") as s:
        z = s.read(1).astype(np.float32)
    with rasterio.open(OUT / "terrain_slope_deg.tif") as s:
        sl = s.read(1).astype(np.float32)
    relief = (ndimage.maximum_filter(z, size=CONFINE_CELLS, mode="nearest")
              - ndimage.minimum_filter(z, size=CONFINE_CELLS, mode="nearest"))
    smean = ndimage.uniform_filter(np.nan_to_num(sl), size=CONFINE_CELLS, mode="nearest")
    write("terrain_relief_2km_m", relief.astype(np.float32))
    write("terrain_slope_2km_deg", smean.astype(np.float32))
    tick(t0, f"valley confinement: median 2 km relief {np.median(relief):.0f} m, "
             f"median 2 km slope {np.median(smean):.1f} deg")


# ── step 4: land cover, unclipped ────────────────────────────────────────
def step_landcover(t0: float) -> None:
    if have("lc_class_cat"):
        tick(t0, "land cover already present, skipping")
        return
    tiles = sorted(LC_TILES.glob("*.tif"))
    tick(t0, f"land cover from {len(tiles)} ESA WorldCover tiles (mode, 10 m -> 100 m)")
    out = np.zeros(G.SHAPE, dtype=np.uint8)
    for t in tiles:
        with rasterio.open(t) as s:
            patch = np.zeros(G.SHAPE, dtype=np.uint8)
            reproject(source=rasterio.band(s, 1), destination=patch,
                      dst_transform=G.TRANSFORM, dst_crs=G.CRS,
                      src_nodata=0, dst_nodata=0, resampling=Resampling.mode)
        np.copyto(out, patch, where=patch > 0)
        tick(t0, f"  {t.name[-16:]}  running cover {100*(out>0).mean():5.1f}%")
    write("lc_class_cat", out, dtype="uint8")


def main() -> None:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    print("Unmasked 100 m feature stack (flood WHERE)")
    step_terrain(t0)
    step_hydrology(t0)
    step_hand(t0)
    step_confinement(t0)
    step_landcover(t0)
    print(f"\n  done in {time.time()-t0:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
