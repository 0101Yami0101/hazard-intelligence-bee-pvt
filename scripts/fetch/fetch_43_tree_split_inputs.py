"""Inputs for splitting WorldCover "tree" into forest / tea-bush / cleared, per 100 m cell.

    $env:REGION = "assam"; python scripts/fetch/fetch_43_tree_split_inputs.py

The method and its pass bars were written down first (EROSION_PLAN.md, "Phase 1,
E1.1 part 1"). Five bands on the region's own 100 m grid (scripts/build/grid.py),
computed by Earth Engine from native-resolution data:

    low_frac     share of Meta 1 m canopy-height pixels under 3 m       (x250, uint8)
    h_mean       mean Meta canopy height, m                             (x4,   uint8, cap 63.75)
    fresh_frac   share of Hansen 30 m pixels lost in 2024-2025          (x250, uint8)
    recent_frac  share of Hansen 30 m pixels lost in 2021-2023          (x250, uint8)
    h_eth        mean ETH 10 m (2020) canopy height, m, cross-check     (x4,   uint8)

255 = no data. Two traps met on the way and handled here: Hansen's lossyear is
MASKED where there was no loss (unmask(0) first, or a mean counts only
clearings), and categorical codes must not be averaged at coarse pyramid levels
(fractions are taken at native resolution with reduceResolution).

How it is fetched: our Earth Engine project can compute but has no asset storage
("projects/earthengine-507510/assets does not exist", 2026-10-20), so a batch
export is not possible. Instead the image is requested directly with
computePixels in 8 km tiles (the most one request may average from 1 m
pixels), 8 at a time, each saved as it lands so an interruption resumes. About
1,500 tiles, ~36 s each. If asset storage is ever enabled, a single export
would be faster.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import ee
import numpy as np
import rasterio

import grid as G
from common import AOI_NAME, INTERIM, LANDCOVER, record

PROJECT = "earthengine-507510"
OUT = LANDCOVER / "ee_tree_split"
BANDS = ["low_frac", "h_mean", "fresh_frac", "recent_frac", "h_eth"]
META = "projects/meta-forest-monitoring-okw37/assets/CanopyHeight"
HANSEN = "UMD/hansen/global_forest_change_2025_v1_13"
ETH = "users/nlang/ETH_GlobalCanopyHeight_2020_10m_v1"
# 80 x 80 cells (8 km): Earth Engine's interactive limit is about 8,000 x 8,000
# input pixels per request, and the 1 m canopy heights hit it above ~85 cells.
TILE = 80
WORKERS = 8
TILES = OUT / f"tiles_{AOI_NAME}"
G_MASK = INTERIM / "state_mask.tif"


def build_image() -> ee.Image:
    grid_proj = ee.Projection(G.CRS, [G.CELL, 0, G.ORIGIN_X, 0, -G.CELL, G.TOP_Y])
    meta_ic = ee.ImageCollection(META)
    meta = meta_ic.mosaic().setDefaultProjection(meta_ic.first().projection()).select(0)
    low = meta.lt(3).updateMask(meta.mask())
    gfc = ee.Image(HANSEN)
    ly = gfc.select("lossyear").unmask(0).updateMask(gfc.select("datamask").gt(0))
    fresh = ly.gte(24).And(ly.lte(25))
    recent = ly.gte(21).And(ly.lte(23))
    eth = ee.Image(ETH).select(0)

    def agg(img, max_px):
        return (img.toFloat().reduceResolution(ee.Reducer.mean(), maxPixels=max_px)
                .reproject(grid_proj))

    def code(img, scale, cap):
        return img.multiply(scale).min(cap).round().unmask(255).toUint8()

    return ee.Image.cat([
        code(agg(low, 10_000), 250, 250).rename("low_frac"),
        code(agg(meta, 10_000), 4, 254).rename("h_mean"),
        code(agg(fresh, 64), 250, 250).rename("fresh_frac"),
        code(agg(recent, 64), 250, 250).rename("recent_frac"),
        code(agg(eth, 256), 4, 254).rename("h_eth"),
    ])


def tiles_needed(size: int) -> list[tuple[int, int]]:
    """Tiles that hold at least one in-state cell (the box corners are skipped)."""
    with rasterio.open(G_MASK) as s:
        inside = s.read(1).astype(bool)
    out = []
    for r0 in range(0, G.NROWS, size):
        for c0 in range(0, G.NCOLS, size):
            if inside[r0:r0 + size, c0:c0 + size].any():
                out.append((r0, c0))
    return out


def fetch_tile(img: ee.Image, r0: int, c0: int, size: int) -> Path:
    f = TILES / f"r{r0:05d}_c{c0:05d}.npz"
    if f.exists():
        return f
    h, w = min(size, G.NROWS - r0), min(size, G.NCOLS - c0)
    for attempt in range(8):
        try:
            arr = ee.data.computePixels({
                "expression": img, "fileFormat": "NUMPY_NDARRAY",
                "grid": {"dimensions": {"width": w, "height": h},
                         "affineTransform": {"scaleX": G.CELL, "shearX": 0,
                                             "translateX": G.ORIGIN_X + c0 * G.CELL,
                                             "shearY": 0, "scaleY": -G.CELL,
                                             "translateY": G.TOP_Y - r0 * G.CELL},
                         "crsCode": G.CRS}})
            np.savez_compressed(f, **{b: np.asarray(arr[b], np.uint8) for b in BANDS})
            return f
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            if "too large" in msg:
                raise
            time.sleep(min(120, 10 * 2 ** attempt))
    raise RuntimeError(f"tile {r0},{c0} failed 8 times")


def read_back() -> np.ndarray:
    """Every needed tile by computePixels, 8 at a time, each saved as it lands
    so a dropped connection resumes instead of restarting."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    TILES.mkdir(parents=True, exist_ok=True)
    img = build_image()
    todo = tiles_needed(TILE)
    left = [rc for rc in todo if not (TILES / f"r{rc[0]:05d}_c{rc[1]:05d}.npz").exists()]
    print(f"  {len(todo)} tiles of {TILE}x{TILE} cells; {len(left)} to fetch", flush=True)
    t0, done, failed = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(fetch_tile, img, r0, c0, TILE): (r0, c0) for r0, c0 in left}
        for fut in as_completed(futs):
            try:
                fut.result()
                done += 1
            except Exception as exc:  # noqa: BLE001
                failed.append((futs[fut], str(exc)[:120]))
            if done % 25 == 0 or done == len(left):
                el = time.time() - t0
                print(f"    {done}/{len(left)} tiles, {el / 60:.0f} min, "
                      f"about {el / max(done, 1) * (len(left) - done) / 60:.0f} min left", flush=True)
    if failed:
        raise SystemExit(f"  {len(failed)} tiles failed (re-run to resume): {failed[:3]}")
    out = np.full((len(BANDS), G.NROWS, G.NCOLS), 255, dtype=np.uint8)
    for r0, c0 in todo:
        z = np.load(TILES / f"r{r0:05d}_c{c0:05d}.npz")
        h, w = z[BANDS[0]].shape
        for i, b in enumerate(BANDS):
            out[i, r0:r0 + h, c0:c0 + w] = z[b]
    return out


def main() -> None:
    print(f"Tree-split inputs — {AOI_NAME}")
    ee.Initialize(project=PROJECT)
    arr = read_back()
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"tree_split_inputs_{AOI_NAME}.tif"
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=len(BANDS), dtype="uint8",
                crs=G.CRS, transform=G.TRANSFORM, nodata=255, compress="deflate", tiled=True)
    with rasterio.open(dest, "w", **prof) as d:
        d.write(arr)
        d.descriptions = tuple(BANDS)
    print(f"  wrote {dest}")
    record(OUT, source="Tree-split inputs (Meta 1 m canopy height, Hansen GFC v1.13, ETH 10 m)",
           url="Earth Engine computePixels (Meta CanopyHeight, UMD/hansen/global_forest_change_2025_v1_13, "
            "users/nlang/ETH_GlobalCanopyHeight_2020_10m_v1)", files=[dest],
           license_="Meta CHM: CC-BY 4.0; Hansen GFC: CC-BY 4.0; ETH canopy height: CC-BY 4.0",
           notes="Bands low_frac, fresh_frac, recent_frac x250; h_mean, h_eth x4 (m); 255 = no data. "
                 "Built on the region grid in Earth Engine (fetch_43_tree_split_inputs.py).")


if __name__ == "__main__":
    main()
