"""JRC Global Surface Water 1984-2021: where water has been, from every Landsat scene.

    python scripts/fetch/fetch_57_surface_water.py

Stored for later; no product reads it yet. It is the natural reference for the
flood WHERE layer (water seen in a cell in some years but not most) and for
riverbank change. Six layers, one 10x10 degree tile (90-100E, 20-30N) that holds
both Arunachal and Assam. Tiles are kept untouched.

    occurrence   % of months water was seen, 1984-2021
    recurrence   how often it comes back year to year
    seasonality  months per year with water
    extent       ever water
    change       occurrence change, 1984-99 vs 2000-21
    transitions  permanent / seasonal / new / lost water

Licence: Copernicus programme; free, open, attribution required
(Pekel et al. 2016, Nature 540, 418-422).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from common import HYDROLOGY, UA, record

BASE = "https://storage.googleapis.com/global-surface-water/downloads2021"
TILE = "90E_30N"
LAYERS = ["occurrence", "recurrence", "seasonality", "extent", "change", "transitions"]
OUT = HYDROLOGY / "jrc_surface_water"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for layer in LAYERS:
        name = f"{layer}_{TILE}v1_4_2021.tif"
        dest = OUT / name
        if not dest.exists():
            with requests.get(f"{BASE}/{layer}/{name}", headers=UA, timeout=900, stream=True) as r:
                r.raise_for_status()
                tmp = dest.with_suffix(".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
                tmp.replace(dest)
        print(f"  {name}  {dest.stat().st_size / 1e6:.0f} MB")
        files.append(dest)
    record(OUT, source="JRC Global Surface Water v1.4 (1984-2021)", url=BASE, files=files,
           license_="Free and open (Copernicus); cite Pekel et al. 2016",
           notes="30 m, from every Landsat scene. One tile, 90-100E 20-30N. Stored for "
                 "the flood WHERE reference and riverbank change; no product reads it yet.")


if __name__ == "__main__":
    main()
