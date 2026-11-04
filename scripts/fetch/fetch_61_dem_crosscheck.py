"""Two more 30 m elevation models, to cross-check Copernicus GLO-30: NASADEM and ALOS AW3D30.

    python scripts/fetch/fetch_61_dem_crosscheck.py     ($env:REGION picks the box)

Every slope, curvature and wetness fact comes from one elevation model. Two
independent ones (NASADEM: radar, 2000; AW3D30: optical stereo, 2006-11) show
where GLO-30 might be wrong: voids, cliffs, radar shadow in deep valleys.
Stored for that check; no product reads them yet.

Fetched at their native 1 arc-second, in 1x1 degree tiles (3600 x 3600 int16,
~26 MB a request), as GeoTIFFs in EPSG:4326. Tiles on disk are kept.

Licences: NASADEM public domain (NASA/USGS); AW3D30 free of charge with
attribution "(c) JAXA", JAXA's terms of use apply.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee
import numpy as np
import rasterio
from rasterio.transform import from_origin

from common import AOI_BBOX, AOI_NAME, TERRAIN, record

PROJECT = "earthengine-507510"
PX = 1 / 3600
DEMS = {
    "nasadem": ("NASA/NASADEM_HGT/001", "elevation", False,
                "NASADEM (NASA/USGS, from SRTM 2000)", "Public domain (NASA/USGS)"),
    "aw3d30": ("JAXA/ALOS/AW3D30/V4_1", "DSM", True,
               "ALOS World 3D 30 m v4.1 (JAXA)", "Free with attribution (c) JAXA; JAXA terms apply"),
}


def tile(img: ee.Image, lon: int, lat: int) -> np.ndarray:
    arr = ee.data.computePixels({
        "expression": img, "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": 3600, "height": 3600},
                 "affineTransform": {"scaleX": PX, "shearX": 0, "translateX": lon,
                                     "shearY": 0, "scaleY": -PX, "translateY": lat + 1},
                 "crsCode": "EPSG:4326"}})
    return arr[arr.dtype.names[0]]


def main() -> None:
    ee.Initialize(project=PROJECT)
    w, s, e, n = AOI_BBOX
    cells = [(lo, la) for la in range(math.floor(s), math.ceil(n))
             for lo in range(math.floor(w), math.ceil(e))]
    for key, (asset, band, is_col, source, lic) in DEMS.items():
        out = TERRAIN / key
        out.mkdir(parents=True, exist_ok=True)
        img = (ee.ImageCollection(asset).select(band).mosaic() if is_col
               else ee.Image(asset).select(band)).unmask(-32768).toInt16()
        for lo, la in cells:
            dest = out / f"{key}_N{la:02d}E{lo:03d}.tif"
            if dest.exists():
                continue
            a = tile(img, lo, la)
            with rasterio.open(dest, "w", driver="GTiff", width=3600, height=3600, count=1,
                               dtype="int16", crs="EPSG:4326", nodata=-32768, compress="deflate",
                               transform=from_origin(lo, la + 1, PX, PX)) as d:
                d.write(a, 1)
            print(f"  {dest.name}  {dest.stat().st_size / 1e6:.1f} MB", flush=True)
        record(out, source=source, url=f"Earth Engine computePixels ({asset})",
               files=sorted(out.glob(f"{key}_N*.tif")), license_=lic,
               notes=f"1 arc-second, 1x1 degree tiles over the {AOI_NAME} box. Stored to "
                     "cross-check Copernicus GLO-30; no product reads it yet.")


if __name__ == "__main__":
    main()
