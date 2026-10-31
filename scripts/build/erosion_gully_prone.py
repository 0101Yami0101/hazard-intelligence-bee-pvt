"""AD-30: gully-prone ground from the terrain — a first look before any gully finder on imagery.

    $env:REGION = "assam"; python scripts/build/erosion_gully_prone.py

Gullies start where enough water gathers on steep enough ground: the slope-area threshold
(Montgomery & Dietrich 1992; Patton & Schumm 1975), often written with the stream power
index SPI = A_s x tan(slope), A_s = specific catchment area (m2 per m of contour).

On the 100 m grid a square is flagged gully-prone when ALL hold (fixed before any picture
is looked at; EROSION_PLAN.md "AD-05 / AD-30 part 1"):
    open land (WorldCover shrub, grass, cropland, bare), scored by the recipe
    slope >= 5 deg
    upstream area 0.03-5 km2 (a hillslope hollow, not a river: channels draining
        >= 5 km2 are left out)
    SPI in the top 10% of open land meeting the two rules above

Output: data/interim/<region>/erosion/erosion_gully_prone.tif (1 flagged, 0 not, 255 not open land)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import rasterio

import grid as G
from common import AOI_NAME, INTERIM, ROOT

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
OPEN = (20, 30, 40, 60)
MIN_SLOPE, A_MIN_CELLS, A_MAX_CELLS, TOP = 5.0, 3, 500, 0.10


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def main() -> None:
    print(f"Gully-prone ground — {AOI_NAME}")
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif").astype(np.float64)
    acc = rd(INTERIM / "terrain" / "hydro_flowacc_cells.tif").astype(np.float64)
    open_land = ok & np.isin(lc, OPEN)
    cand = open_land & (slope >= MIN_SLOPE) & (acc >= A_MIN_CELLS) & (acc <= A_MAX_CELLS)
    spi = (acc + 1) * G.CELL * np.tan(np.radians(slope))
    cut = float(np.percentile(spi[cand], 100 * (1 - TOP)))
    flag = cand & (spi >= cut)
    out = np.full(G.SHAPE, 255, np.uint8)
    out[open_land] = 0
    out[flag] = 1
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="uint8", crs=G.CRS,
                transform=G.TRANSFORM, nodata=255, compress="deflate", tiled=True)
    with rasterio.open(E / "erosion_gully_prone.tif", "w", **prof) as d:
        d.write(out, 1)
    rep = {"region": AOI_NAME, "candidates_ha": int(cand.sum()), "flagged_ha": int(flag.sum()),
           "spi_cut_m": round(cut, 1), "open_land_ha": int(open_land.sum())}
    (ROOT / "reports" / f"erosion_gully_prone_{AOI_NAME}.json").write_text(json.dumps(rep, indent=2))
    print(rep)


if __name__ == "__main__":
    main()
