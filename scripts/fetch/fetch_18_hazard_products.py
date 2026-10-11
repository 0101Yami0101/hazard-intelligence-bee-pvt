"""Official hazard products — GSI landslide susceptibility, Bhuvan flood extent.

Two rasters that the project needs for different reasons than the inventories.

GSI Susceptibility is the government's own 50 m national landslide
susceptibility map (3 classes). It is not training data — it is the benchmark.
Any susceptibility surface this project produces has to be defensible against
it, and where the two disagree is exactly what a government client will ask
about. Served from an ArcGIS ImageServer that requires a token, so requests go
through the portal's own proxy, the same route its web map uses.

Bhuvan agg_ar is satellite-observed flood inundation aggregated over 2003-2020.
The flood side of this project currently has GloFAS forecasts but no record of
where water has actually gone; this is that record. It is served only as
rendered map tiles, so what comes back is a mask (flooded / not) rather than
per-year depths or frequencies.

Both are clipped to AOI_BBOX and written as GeoTIFF in EPSG:4326.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import io
import math

import numpy as np
import rasterio
import requests
from PIL import Image
from rasterio.transform import from_bounds

from common import AOI_BBOX, AOI_NAME, CONTEXT, LABELS, UA, record

GSI_PROXY = "https://bhusanket.gsi.gov.in/DotNet/proxy.ashx"
GSI_SUSE = ("https://bhusanket.gsi.gov.in/gisserver/rest/services/GSI/"
            "Susceptibility/ImageServer/exportImage")
GSI_NATIVE_M = 50
# The service's own grid: EPSG:32644 (UTM 44N — one zone for all India), with
# this origin. Tiles are snapped to it so no cell is resampled.
GSI_CRS = "EPSG:32644"
GSI_X0, GSI_Y1 = -361125.7603, 3859539.6613
GSI_TILE = 2000           # px; 2,000 and 4,000 px tiles agree cell for cell

BHUVAN_MC = "https://bhuvan-ras2.nrsc.gov.in/mapcache"
FLOOD_LAYER = "agg_ar"
FLOOD_PX = 4000           # ~150 m across the AOI; the source is a rendered cache


def _deg_to_px(west: float, south: float, east: float, north: float,
               metres: int) -> tuple[int, int]:
    """Pixel dimensions that put roughly `metres` on the ground per pixel."""
    mid = math.radians((south + north) / 2)
    w_km = (east - west) * 111.32 * math.cos(mid)
    h_km = (north - south) * 110.9
    return int(w_km * 1000 / metres), int(h_km * 1000 / metres)


def fetch_susceptibility() -> Path | None:
    """The susceptibility raster, cell for cell as GSI serves it.

    ⚠️ Fetched on the service's OWN grid (EPSG:32644, 50 m, snapped to its
    origin) in tiles, with nearest-neighbour. The first version asked for the
    whole state in one image, in EPSG:4326, and took the server's default
    (bilinear) resampling. What came back had the right classes in the right
    proportions and the right outline — and matched a fresh native export on
    only 41% of cells, about what chance gives for three classes. It scored
    as noise against terrain and against landslides, which is how it was
    caught (2026-10-10, docs/design/GSI_MAP_COMPARISON.md §3). On the native
    grid a 500, a 2,000 and a 4,000 px request agree cell for cell.
    """
    from pyproj import Transformer
    from rasterio.transform import from_origin

    w, s, e, n = AOI_BBOX
    tr = Transformer.from_crs("EPSG:4326", GSI_CRS, always_xy=True)
    xs, ys = tr.transform([w, w, e, e, (w + e) / 2, (w + e) / 2],
                          [s, n, s, n, s, n])
    c0 = int((min(xs) - GSI_X0) // GSI_NATIVE_M)
    c1 = int((max(xs) - GSI_X0) // GSI_NATIVE_M) + 1
    r0 = int((GSI_Y1 - max(ys)) // GSI_NATIVE_M)
    r1 = int((GSI_Y1 - min(ys)) // GSI_NATIVE_M) + 1
    H, W = r1 - r0, c1 - c0
    arr = np.zeros((H, W), dtype="uint8")
    tiles = [(r, c) for r in range(0, H, GSI_TILE) for c in range(0, W, GSI_TILE)]
    print(f"  GSI susceptibility: {W}x{H} px at {GSI_NATIVE_M} m on its own grid "
          f"-> {len(tiles)} tile(s)")
    for i, (r, c) in enumerate(tiles):
        h, wd = min(GSI_TILE, H - r), min(GSI_TILE, W - c)
        xmin = GSI_X0 + (c0 + c) * GSI_NATIVE_M
        ymax = GSI_Y1 - (r0 + r) * GSI_NATIVE_M
        target = (f"{GSI_SUSE}?bbox={xmin},{ymax - h * GSI_NATIVE_M},"
                  f"{xmin + wd * GSI_NATIVE_M},{ymax}&bboxSR=32644&imageSR=32644"
                  f"&size={wd},{h}&format=tiff"
                  f"&interpolation=RSP_NearestNeighbor&f=image")
        for attempt in range(3):
            try:
                resp = requests.get(f"{GSI_PROXY}?{target}", timeout=600, headers=UA)
                resp.raise_for_status()
                if "image" not in resp.headers.get("Content-Type", ""):
                    raise RuntimeError(resp.text[:160])
                with rasterio.open(io.BytesIO(resp.content)) as src:
                    t = src.read(1)
                if t.shape != (h, wd):
                    raise RuntimeError(f"asked {wd}x{h}, got {t.shape[1]}x{t.shape[0]}")
                break
            except Exception as ex:  # noqa: BLE001
                if attempt == 2:
                    print(f"    ! tile {i + 1}: {type(ex).__name__}: {ex}")
                    return None
        arr[r:r + h, c:c + wd] = np.clip(t, 0, 3).astype("uint8")
        print(f"    tile {i + 1}/{len(tiles)} ok", flush=True)

    dest = CONTEXT / f"gsi_landslide-susceptibility_50m_{AOI_NAME}.tif"
    with rasterio.open(
        dest, "w", driver="GTiff", height=H, width=W,
        count=1, dtype="uint8", crs=GSI_CRS,
        transform=from_origin(GSI_X0 + c0 * GSI_NATIVE_M, GSI_Y1 - r0 * GSI_NATIVE_M,
                              GSI_NATIVE_M, GSI_NATIVE_M),
        nodata=0, compress="deflate", tiled=True,
    ) as dst:
        dst.write(arr, 1)
        dst.update_tags(
            classes="1=Low, 2=Moderate, 3=High susceptibility; 0=no data",
            source="Geological Survey of India, National Landslide Susceptibility Mapping",
            grid="GSI's own: EPSG:32644, 50 m, nearest-neighbour, cell for cell",
        )

    vals, counts = np.unique(arr, return_counts=True)
    dist = {int(v): int(c) for v, c in zip(vals, counts)}
    print(f"    -> {dest.name} ({dest.stat().st_size / 1e6:.1f} MB) classes={dist}")
    return dest


def fetch_flood() -> Path | None:
    """Pull the aggregated flood layer and reduce the rendering back to a mask."""
    w, s, e, n = AOI_BBOX
    px_w = FLOOD_PX
    px_h = int(px_w * (n - s) / (e - w) / math.cos(math.radians((s + n) / 2)))
    print(f"  Bhuvan flood (2003-2020 aggregate): {px_w}x{px_h} px")

    r = requests.get(BHUVAN_MC, params={
        "service": "WMS", "version": "1.1.1", "request": "GetMap",
        "layers": FLOOD_LAYER, "srs": "EPSG:4326",
        "bbox": f"{w},{s},{e},{n}", "width": str(px_w), "height": str(px_h),
        "format": "image/png", "transparent": "true",
    }, timeout=600, headers=UA)
    r.raise_for_status()
    if "image" not in r.headers.get("Content-Type", ""):
        print(f"    ! server returned {r.text[:160]}")
        return None

    rgba = np.array(Image.open(io.BytesIO(r.content)).convert("RGBA"))
    # The cache serves a styled image, not values: anything drawn is flooded.
    mask = (rgba[..., 3] > 0).astype("uint8")

    dest = LABELS / f"bhuvan_flood-aggregate-2003-2020_mask_{AOI_NAME}.tif"
    with rasterio.open(
        dest, "w", driver="GTiff", height=mask.shape[0], width=mask.shape[1],
        count=1, dtype="uint8", crs="EPSG:4326",
        transform=from_bounds(w, s, e, n, mask.shape[1], mask.shape[0]),
        nodata=0, compress="deflate",
    ) as dst:
        dst.write(mask, 1)
        dst.update_tags(
            classes="1=flooded at least once 2003-2020, 0=not observed flooded",
            source="NRSC Bhuvan aggregated flood layer (agg_ar)",
        )

    pct = 100 * mask.mean()
    print(f"    -> {dest.name} ({dest.stat().st_size / 1e6:.1f} MB), "
          f"{int(mask.sum())} flooded px ({pct:.2f}% of AOI)")
    return dest


def main() -> None:
    print("Official hazard products — GSI susceptibility, Bhuvan flood extent\n")

    try:
        suse = fetch_susceptibility()
    except Exception as e:  # noqa: BLE001
        print(f"    ! susceptibility failed: {type(e).__name__}: {e}")
        suse = None

    try:
        flood = fetch_flood()
    except Exception as e:  # noqa: BLE001
        print(f"    ! flood failed: {type(e).__name__}: {e}")
        flood = None

    if suse:
        record(CONTEXT,
               source="GSI National Landslide Susceptibility Map (50 m)",
               url=GSI_SUSE, files=[suse],
               license_="UNSTATED — GSI product accessed via the portal's public "
                        "proxy. Confirm redistribution rights before shipping.",
               notes="3-class susceptibility (1 Low / 2 Moderate / 3 High). "
                     "Benchmark to evaluate our own susceptibility output "
                     "against, not a training input.")
    if flood:
        record(LABELS,
               source="NRSC Bhuvan aggregated flood inundation 2003-2020 (agg_ar)",
               url=BHUVAN_MC, files=[flood],
               license_="UNSTATED — Bhuvan terms apply. Confirm before "
                        "redistribution.",
               notes="Binary observed-flood mask derived from a rendered tile "
                     "service; no per-year or depth information is available "
                     "through this endpoint.")


if __name__ == "__main__":
    main()
