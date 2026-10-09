"""HAND at the native 100 m grid, as a reusable feature layer.

    python scripts/build/build_hand_100m.py

`build_flood_layers.py` already computes HAND, but only ever persists the
~550 m web-display version (`webapp/assets/flood/hand.npz`). The flood WHERE
model trains on the 100 m feature lattice, where height above the nearest
drainage is the single most informative flood predictor there is — so it
needs the full-resolution array on disk, aligned cell-for-cell with
`data/interim/terrain/*.tif`.

Same method, same constants as `build_flood_layers.py` (imported, not
copied, so the two can never drift apart).

Output:
    data/interim/terrain/hydro_hand_m.tif        metres above nearest channel
    data/interim/terrain/hydro_chan_km2.tif      drainage area of that channel
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rasterio
from scipy import ndimage

from common import INTERIM

TERRAIN = INTERIM / "terrain"
CHANNEL_CELLS = 10_000          # x 100 m x 100 m = 100 km2, same as build_flood_layers


def main() -> None:
    print("HAND at 100 m")

    # Routing runs on the UNMASKED DEM so a valley that leaves Arunachal and
    # comes back is not cut in two - identical to build_flood_layers.py.
    with rasterio.open(TERRAIN / "_dem_unmasked_m.tif") as s:
        z = s.read(1).astype(np.float32)
        profile = s.profile
    with rasterio.open(TERRAIN / "hydro_flowacc_cells.tif") as s:
        acc = s.read(1)

    chan = acc >= CHANNEL_CELLS
    print(f"  {int(chan.sum()):,} channel cells (>= {CHANNEL_CELLS/100:.0f} km2 upstream)")

    dist, idx = ndimage.distance_transform_edt(
        ~chan, sampling=(100.0, 100.0), return_indices=True)
    hand = (z - z[idx[0], idx[1]]).astype(np.float32)
    np.maximum(hand, 0.0, out=hand)          # below its own channel = DEM artefact
    chan_km2 = (acc[idx[0], idx[1]].astype(np.float32) / 100.0)

    with rasterio.open(TERRAIN / "dem_elev_m.tif") as s:
        instate = np.isfinite(s.read(1))
    print(f"  median HAND in state {np.median(hand[instate]):.0f} m")

    profile.update(dtype="float32", count=1, compress="deflate", nodata=np.nan)
    for name, arr in (("hydro_hand_m", hand), ("hydro_chan_km2", chan_km2)):
        with rasterio.open(TERRAIN / f"{name}.tif", "w", **profile) as d:
            d.write(arr, 1)
        print(f"  wrote {TERRAIN / f'{name}.tif'}")


if __name__ == "__main__":
    main()
