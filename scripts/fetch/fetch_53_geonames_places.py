"""GeoNames populated places for India (IN.zip), for SoilSense's village search (E2.3).

    python scripts/fetch/fetch_53_geonames_places.py

A second open gazetteer beside OpenStreetMap (fetch_52_osm_places.py): each covers only
part of Assam's villages, so the village card searches both, de-duplicated. The build
(scripts/build/erosion_places.py) clips to the state outline rather than trusting
GeoNames' admin codes.

Licence: CC-BY 4.0 — attribution "GeoNames (geonames.org)".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from common import BOUNDARIES, UA, record

URL = "https://download.geonames.org/export/dump/IN.zip"
OUT = BOUNDARIES / "geonames"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "IN.zip"
    r = requests.get(URL, headers=UA, timeout=600)
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"  wrote {dest} ({len(r.content) / 1e6:.1f} MB)")
    record(OUT, source="GeoNames country dump, India", url=URL, files=[dest],
           license_="CC-BY 4.0 — GeoNames (geonames.org)",
           notes="Populated places (feature class P) are used for SoilSense's village search, "
                 "clipped to the state outline.")


if __name__ == "__main__":
    main()
