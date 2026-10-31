"""NRSC Land Degradation 1:50,000 (2015-16), water-erosion classes, on the region grid.

    $env:REGION = "assam"; python scripts/fetch/fetch_49_nrsc_land_degradation.py

An independent reference for SoilSense's cross-map check (EROSION_PLAN.md, E1.5 /
V2): NRSC mapped land degradation by visual interpretation of satellite imagery,
not from a soil-loss recipe. FOR COMPARISON ONLY: never redistributed, never an
input to the erosion map.

How it is read (Bhuvan, the "portals look closed but aren't" method):
  - the layer is `ld:AS_LD50K_1516` on bhuvan-vec2.nrsc.gov.in/bhuvan/wms; WFS is
    off, and its features are dissolved state-wide by class, so GetFeatureInfo
    returns whole classes at once;
  - GetMap draws in EPSG:4326 only (a UTM request comes back blank), and every
    water-erosion class is drawn in the same colour (the level-1 rule paints over
    the level-2 ones), so each class is drawn ALONE with a CQL_FILTER and read as
    a mask (alpha);
  - every image carries a "bhuvan" watermark in its centre, so each tile is
    drawn twice, the second shifted by a quarter tile, and a pixel counts only if
    it is painted in both.

Output (data/raw/04_landcover/nrsc_ld50k/):
    nrsc_ld50k_1516_<region>.tif   uint8 on the region grid: 0 not mapped,
        1-7 = water erosion A1-A7 (sheet slight / moderate / severe, rills,
        gullies, shallow ravines, deep ravines), 8 = normal, 9 = other degradation
"""
from __future__ import annotations

import io
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import rasterio
import requests
from affine import Affine
from PIL import Image
from rasterio.enums import Resampling
from rasterio.warp import reproject

import grid as G
from common import AOI_BBOX, AOI_NAME, LANDCOVER, UA, record

URL = "https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms"
LAYER = "ld:AS_LD50K_1516"
OUT = LANDCOVER / "nrsc_ld50k"
RES = 0.0009                       # degrees, about 100 m
TILE_PX = 1000
# class code -> CQL filter; drawn and read one by one
CLASSES = {1: "LD_1516_L2='A1'", 2: "LD_1516_L2='A2'", 3: "LD_1516_L2='A3'",
           4: "LD_1516_L2='A4'", 5: "LD_1516_L2='A5'", 6: "LD_1516_L2='A6'",
           7: "LD_1516_L2='A7'", 8: "LD_1516_L1='N'"}
ANY = None                         # no filter: every mapped polygon (-> 9 where no class above)
NAMES = {0: "not mapped", 1: "sheet erosion, slight", 2: "sheet erosion, moderate",
         3: "sheet erosion, severe", 4: "rills", 5: "gullies", 6: "ravines, shallow",
         7: "ravines, deep", 8: "normal", 9: "other degradation"}
WORKERS = 4


def draw(w: float, s: float, cql: str | None) -> np.ndarray:
    """One TILE_PX square from (w, s), as a painted mask."""
    e, n = w + TILE_PX * RES, s + TILE_PX * RES
    p = dict(service="WMS", version="1.1.1", request="GetMap", layers=LAYER, styles="",
             srs="EPSG:4326", bbox=f"{w},{s},{e},{n}", width=TILE_PX, height=TILE_PX,
             format="image/png", transparent="true", format_options="antialiasing:off")
    if cql:
        p["CQL_FILTER"] = cql
    last = ""
    for attempt in range(8):
        try:
            r = requests.get(URL, params=p, headers=UA, timeout=240)
            if r.headers.get("content-type", "").startswith("image"):
                return np.array(Image.open(io.BytesIO(r.content)).convert("RGBA"))[..., 3] >= 128
            last = r.text[:200]
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:200]
        time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"tile {w},{s} {cql} failed: {last}")


def mask(w: float, s: float, cql: str | None) -> np.ndarray:
    """Painted in both the tile and a copy shifted by a quarter tile (watermark out)."""
    q = TILE_PX // 4
    a = draw(w, s, cql)
    b = draw(w + q * RES, s + q * RES, cql)        # b's pixel (i, j) = a's (i - q, j + q)
    out = a.copy()
    # a's pixel (i, j) = b's (i + q, j - q); the strips b does not cover (south rows,
    # west columns) keep a alone, which is safe: a's watermark is in its centre
    out[:-q, q:] = a[:-q, q:] & b[q:, :-q]
    return out


def main() -> None:
    print(f"NRSC land degradation 1:50k (2015-16) — {AOI_NAME}", flush=True)
    W, S, E, N = AOI_BBOX
    nx = int(np.ceil((E - W) / RES / TILE_PX))
    ny = int(np.ceil((N - S) / RES / TILE_PX))
    full = np.zeros((ny * TILE_PX, nx * TILE_PX), np.uint8)
    top = S + ny * TILE_PX * RES
    jobs = [(ix, iy) for iy in range(ny) for ix in range(nx)]
    t0 = time.time()

    tiles = OUT / f"tiles_{AOI_NAME}"
    tiles.mkdir(parents=True, exist_ok=True)

    def one(job):
        """A tile's labels, saved as it finishes so a re-run resumes."""
        ix, iy = job
        f = tiles / f"x{ix:02d}_y{iy:02d}.npy"
        if f.exists():
            return job, np.load(f)
        w, s = W + ix * TILE_PX * RES, top - (iy + 1) * TILE_PX * RES
        lab = np.zeros((TILE_PX, TILE_PX), np.uint8)
        anym = mask(w, s, ANY)
        if anym.any():
            lab[anym] = 9
            for code in (8, 1, 2, 4, 3, 5, 6, 7):    # more severe last, so it wins at shared edges
                lab[mask(w, s, CLASSES[code])] = code
        np.save(f, lab)
        return job, lab

    def safe(job):
        try:
            return one(job)
        except Exception as exc:  # noqa: BLE001
            return job, exc

    failed = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for k, ((ix, iy), lab) in enumerate(pool.map(safe, jobs), 1):
            if isinstance(lab, Exception):
                failed.append(((ix, iy), str(lab)[:160]))
                continue
            full[iy * TILE_PX:(iy + 1) * TILE_PX, ix * TILE_PX:(ix + 1) * TILE_PX] = lab
            print(f"    {k}/{len(jobs)} tiles, {(time.time() - t0) / 60:.0f} min", flush=True)
    if failed:
        raise SystemExit(f"  {len(failed)} tiles failed (re-run to resume): {failed[:2]}")

    src_tr = Affine(RES, 0, W, 0, -RES, top)
    dst = np.zeros(G.SHAPE, np.uint8)
    reproject(source=full, destination=dst, src_transform=src_tr, src_crs="EPSG:4326",
              src_nodata=0, dst_transform=G.TRANSFORM, dst_crs=G.CRS, dst_nodata=0,
              resampling=Resampling.nearest)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"nrsc_ld50k_1516_{AOI_NAME}.tif"
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="uint8",
                crs=G.CRS, transform=G.TRANSFORM, nodata=0, compress="deflate", tiled=True)
    with rasterio.open(dest, "w", **prof) as d:
        d.write(dst, 1)
    vals, cnt = np.unique(dst, return_counts=True)
    print("  classes on the grid: " + ", ".join(f"{NAMES[int(v)]} {c / 100:,.0f} km2"
                                               for v, c in zip(vals, cnt) if v))
    record(OUT, source="NRSC Land Degradation 1:50,000 (2015-16), Bhuvan WMS ld:AS_LD50K_1516",
           url=URL, files=[dest],
           license_="NRSC / ISRO, Bhuvan: viewing service; used for comparison only, never redistributed",
           notes="Water-erosion classes A1-A7 drawn one by one with CQL_FILTER in EPSG:4326 at 0.0009 deg, "
                 "watermark removed by a shifted second draw, nearest-resampled to the region grid. "
                 "Codes: 1-7 A1-A7, 8 normal, 9 other degradation, 0 not mapped "
                 "(fetch_49_nrsc_land_degradation.py).")


if __name__ == "__main__":
    main()
