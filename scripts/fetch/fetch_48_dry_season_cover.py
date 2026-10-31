"""Bare ground every dry season (1 Feb - 30 Apr), 2019-2026, per 100 m cell.

    $env:REGION = "assam"; python scripts/fetch/fetch_48_dry_season_cover.py [--probe]

The rules and pass bars were written down first (EROSION_PLAN.md, "Phase 1,
E1.1-E1.3 part 1"). Per year Y, from Sentinel-2 L2A with Cloud Score+ at 10 m:

    valid_Y   share of the cell's 10 m pixels with >= 3 clear looks and median NDVI >= 0
    bare_Y    share of those usable pixels whose median NDVI is < 0.30
    ndvi_Y    mean median NDVI of the usable pixels

and, for TESTING only (never an input to the detector), Hansen GFC v1.13 at 30 m:

    tc2000    mean tree cover in 2000, %
    loss_any  share of the cell lost at any time 2001-2025
    loss_YYYY share of the cell lost in that year, 2018-2025

Shares are stored x250 and NDVI x250 (0-1), as uint8; 255 = no data.

Fetched the way fetch_43_tree_split_inputs.py is (our Earth Engine project has
no asset storage, so no batch export): computePixels in square tiles, several at
a time, each saved as it lands so an interruption resumes. Tiles holding the
most steep ground go first, so a partial run already covers the hills.
--probe times one hill tile and stops.
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
from common import AOI_BBOX, AOI_NAME, INTERIM, LANDCOVER, record

PROJECT = "earthengine-507510"
OUT = LANDCOVER / "ee_dry_season"
YEARS = list(range(2019, 2027))
WINDOW = ("02-01", "05-01")             # 1 Feb up to (not including) 1 May
CLEAR_MIN = 0.60                         # Cloud Score+ cs_cdf
LOOKS_MIN = 3
BARE_NDVI = 0.30
LOSS_YEARS = list(range(2018, 2026))
BANDS = ([f"{k}_{y}" for y in YEARS for k in ("valid", "bare", "ndvi")]
         + ["tc2000", "loss_any"] + [f"loss_{y}" for y in LOSS_YEARS])
S2 = "COPERNICUS/S2_SR_HARMONIZED"
CSP = "GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED"
HANSEN = "UMD/hansen/global_forest_change_2025_v1_13"
TILE = 100                               # cells (10 km): ~36 s a tile (probe, 2026-10-25)
WORKERS = 8
TILES = OUT / f"tiles_{AOI_NAME}"
G_MASK = INTERIM / "state_mask.tif"
SLOPE = INTERIM / "terrain" / "terrain_slope_deg.tif"
STEEP_DEG = 10.0


def build_image() -> ee.Image:
    grid_proj = ee.Projection(G.CRS, [G.CELL, 0, G.ORIGIN_X, 0, -G.CELL, G.TOP_Y])
    # 10 m on the same UTM lattice as the grid (every grid origin is a whole
    # multiple of 10 km), so each 100 m cell holds exactly 100 pixels.
    p10 = ee.Projection(G.CRS).atScale(10)
    w, s, e, n = AOI_BBOX
    box = ee.Geometry.Rectangle([w, s, e, n])

    def agg(img, max_px):
        return (img.toFloat().reduceResolution(ee.Reducer.mean(), maxPixels=max_px)
                .reproject(grid_proj))

    def code(img, scale=250, cap=250):
        return img.multiply(scale).min(cap).round().unmask(255).toUint8()

    def ndvi(img):
        return (img.normalizedDifference(["B8", "B4"])
                .updateMask(img.select("cs_cdf").gte(CLEAR_MIN)).rename("ndvi"))

    parts = []
    for y in YEARS:
        col = (ee.ImageCollection(S2).filterBounds(box)
               .filterDate(f"{y}-{WINDOW[0]}", f"{y}-{WINDOW[1]}")
               .linkCollection(ee.ImageCollection(CSP), ["cs_cdf"])
               .map(ndvi))
        med = col.median().setDefaultProjection(p10)
        looks = col.count().setDefaultProjection(p10).unmask(0)
        usable = looks.gte(LOOKS_MIN).And(med.unmask(-1).gte(0))
        bare = med.lt(BARE_NDVI).updateMask(usable)
        parts += [code(agg(usable, 256)).rename(f"valid_{y}"),
                  code(agg(bare, 256)).rename(f"bare_{y}"),
                  code(agg(med.max(0).updateMask(usable), 256)).rename(f"ndvi_{y}")]

    gfc = ee.Image(HANSEN)
    land = gfc.select("datamask").gt(0)
    ly = gfc.select("lossyear").unmask(0).updateMask(land)
    parts += [code(agg(gfc.select("treecover2000").updateMask(land), 64), 1, 100).rename("tc2000"),
              code(agg(ly.gt(0), 64)).rename("loss_any")]
    parts += [code(agg(ly.eq(y - 2000), 64)).rename(f"loss_{y}") for y in LOSS_YEARS]
    return ee.Image.cat(parts)


def tiles_needed(size: int) -> list[tuple[int, int]]:
    """Tiles with at least one in-state cell, the steepest first."""
    with rasterio.open(G_MASK) as s:
        inside = s.read(1).astype(bool)
    with rasterio.open(SLOPE) as s:
        steep = (s.read(1) >= STEEP_DEG) & inside
    out = []
    for r0 in range(0, G.NROWS, size):
        for c0 in range(0, G.NCOLS, size):
            if inside[r0:r0 + size, c0:c0 + size].any():
                out.append((int(steep[r0:r0 + size, c0:c0 + size].sum()), r0, c0))
    return [(r0, c0) for _, r0, c0 in sorted(out, reverse=True)]


def tile_file(r0: int, c0: int) -> Path:
    return TILES / f"r{r0:05d}_c{c0:05d}.npz"


def pixels(img: ee.Image, r0: int, c0: int, h: int, w: int) -> dict:
    arr = ee.data.computePixels({
        "expression": img, "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": w, "height": h},
                 "affineTransform": {"scaleX": G.CELL, "shearX": 0,
                                     "translateX": G.ORIGIN_X + c0 * G.CELL,
                                     "shearY": 0, "scaleY": -G.CELL,
                                     "translateY": G.TOP_Y - r0 * G.CELL},
                 "crsCode": G.CRS}})
    return {b: np.asarray(arr[b], np.uint8) for b in BANDS}


HEAVY = ("timed out", "memory", "too large", "deadline")


def grab(img: ee.Image, r0: int, c0: int, h: int, w: int, depth: int = 0) -> dict:
    """A block of cells; if Earth Engine times out or runs short of memory on it,
    it is fetched as four quarters and stitched (same cells, same values), down to
    blocks of about 12 cells."""
    heavy = False
    for attempt in range(6):
        try:
            return pixels(img, r0, c0, h, w)
        except Exception as exc:  # noqa: BLE001
            msg = str(exc)
            print(f"      block r{r0} c{c0} {h}x{w} try {attempt + 1}: {msg[:120]}", flush=True)
            if any(k in msg.lower() for k in HEAVY):
                heavy = True
                break
            time.sleep(min(120, 10 * 2 ** attempt))
    if not heavy or min(h, w) <= 12 or depth >= 4:
        raise RuntimeError(f"block {r0},{c0} {h}x{w} failed")
    hh, hw = -(-h // 2), -(-w // 2)
    parts = {b: np.full((h, w), 255, np.uint8) for b in BANDS}
    for dr in (0, hh):
        for dc in (0, hw):
            if dr >= h or dc >= w:
                continue
            q = grab(img, r0 + dr, c0 + dc, min(hh, h - dr), min(hw, w - dc), depth + 1)
            for b in BANDS:
                parts[b][dr:dr + q[b].shape[0], dc:dc + q[b].shape[1]] = q[b]
    return parts


def fetch_tile(img: ee.Image, r0: int, c0: int, size: int) -> Path:
    f = tile_file(r0, c0)
    if f.exists():
        return f
    h, w = min(size, G.NROWS - r0), min(size, G.NCOLS - c0)
    np.savez_compressed(f, **grab(img, r0, c0, h, w))
    return f


def probe() -> None:
    """Time one hill tile. Prints timing and the share of no-data only, so the
    probe cannot steer any threshold (they were fixed beforehand)."""
    TILES.mkdir(parents=True, exist_ok=True)
    img = build_image()
    r0, c0 = tiles_needed(TILE)[0]
    t0 = time.time()
    f = fetch_tile(img, r0, c0, TILE)
    z = np.load(f)
    print(f"  probe tile r{r0} c{c0} ({TILE}x{TILE} cells): {time.time() - t0:.0f} s; "
          f"no-data share per band: " + ", ".join(f"{b} {np.mean(z[b] == 255):.2f}" for b in BANDS[:3]))
    print(f"  {len(tiles_needed(TILE))} tiles in all")


def read_back() -> np.ndarray:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    TILES.mkdir(parents=True, exist_ok=True)
    img = build_image()
    todo = tiles_needed(TILE)
    left = [rc for rc in todo if not tile_file(*rc).exists()]
    print(f"  {len(todo)} tiles of {TILE}x{TILE} cells; {len(left)} to fetch", flush=True)
    t0, done, failed = time.time(), 0, []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(fetch_tile, img, r0, c0, TILE): (r0, c0) for r0, c0 in left}
        for fut in as_completed(futs):
            try:
                fut.result()
                done += 1
            except Exception as exc:  # noqa: BLE001
                failed.append((futs[fut], str(exc)[:160]))
            if done % 20 == 0 or done == len(left):
                el = time.time() - t0
                print(f"    {done}/{len(left)} tiles, {el / 60:.0f} min, "
                      f"about {el / max(done, 1) * (len(left) - done) / 60:.0f} min left", flush=True)
    if failed:
        raise SystemExit(f"  {len(failed)} tiles failed (re-run to resume): {failed[:3]}")
    out = np.full((len(BANDS), G.NROWS, G.NCOLS), 255, dtype=np.uint8)
    for r0, c0 in todo:
        z = np.load(tile_file(r0, c0))
        h, w = z[BANDS[0]].shape
        for i, b in enumerate(BANDS):
            out[i, r0:r0 + h, c0:c0 + w] = z[b]
    return out


def main() -> None:
    print(f"Dry-season cover {YEARS[0]}-{YEARS[-1]} — {AOI_NAME}", flush=True)
    ee.Initialize(project=PROJECT)
    if "--probe" in sys.argv:
        probe()
        return
    arr = read_back()
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"dry_season_cover_{AOI_NAME}.tif"
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=len(BANDS), dtype="uint8",
                crs=G.CRS, transform=G.TRANSFORM, nodata=255, compress="deflate", tiled=True)
    with rasterio.open(dest, "w", **prof) as d:
        d.write(arr)
        d.descriptions = tuple(BANDS)
    print(f"  wrote {dest}")
    record(OUT, source="Dry-season cover (Sentinel-2 L2A + Cloud Score+) and Hansen GFC v1.13 test bands",
           url=f"Earth Engine computePixels ({S2}, {CSP}, {HANSEN})", files=[dest],
           license_="Copernicus Sentinel data: free and open (Copernicus licence); "
                    "Cloud Score+: CC-BY 4.0; Hansen GFC: CC-BY 4.0",
           notes=f"Per year {YEARS[0]}-{YEARS[-1]}, 1 Feb-30 Apr: valid/bare/ndvi x250; bare = median NDVI "
                 f"< {BARE_NDVI} among pixels with >= {LOOKS_MIN} clear looks (cs_cdf >= {CLEAR_MIN}). "
                 "Hansen tc2000 (%), loss_any and loss_YYYY x250, for testing only. 255 = no data. "
                 "Built on the region grid in Earth Engine (fetch_48_dry_season_cover.py).")


if __name__ == "__main__":
    main()
