"""OpenStreetMap reference outlines for splitting the "tree" land-cover class.

    $env:REGION = "assam"; python scripts/fetch/fetch_45_osm_landuse_reference.py

The soil-erosion module's cover value for WorldCover "tree" is a class average
over closed forest, tea gardens and jhum fallow (EROSION_PLAN.md, D8 / register
V-02). Splitting that class needs places of KNOWN kind, independent of the
satellite inputs, to set and then test the dividing rules:

    tea      tea gardens   (crop=tea, trees=tea_plants, or a "tea" plantation)
    forest   reserve forests and protected areas (boundary=protected_area,
             leisure=nature_reserve, landuse=forest named "... Reserve Forest")

Both are mapped by volunteers: incomplete, unevenly placed, but not derived from
any of the rasters they will be used to judge. Fetched from the Overpass API
by the region's bounding box (the Assam area-by-name query returned nothing);
the build clips to the state.

Licence: ODbL 1.0 — attribution "© OpenStreetMap contributors".
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from common import AOI_BBOX, AOI_NAME, LANDCOVER, UA, record

OUT = LANDCOVER / "osm_reference"
SERVERS = ["https://overpass.private.coffee/api/interpreter",
           "https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]
QUERIES = {
    "tea": """(way["crop"="tea"];relation["crop"="tea"];
               way["trees"="tea_plants"];relation["trees"="tea_plants"];
               way["landuse"~"orchard|farmland|plantation"]["name"~"[Tt]ea"];
               relation["landuse"~"orchard|farmland|plantation"]["name"~"[Tt]ea"];);""",
    "forest": """(way["boundary"="protected_area"];relation["boundary"="protected_area"];
                  way["leisure"="nature_reserve"];relation["leisure"="nature_reserve"];
                  way["landuse"="forest"]["name"~"[Rr]eserve[d]? [Ff]orest|R\\\\.?F\\\\.?$"];
                  relation["landuse"="forest"]["name"~"[Rr]eserve[d]? [Ff]orest|R\\\\.?F\\\\.?$"];);""",
}


def overpass(body: str) -> dict:
    w, s, e, n = AOI_BBOX
    q = f"[out:json][timeout:600][bbox:{s},{w},{n},{e}];{body}out geom;"
    last = None
    for url in SERVERS:
        for _ in range(2):
            try:
                r = requests.post(url, data={"data": q}, timeout=900, headers=UA)
                if r.ok:
                    d = r.json()
                    if d.get("elements"):
                        return d
                last = f"{url}: http {r.status_code}, {len(r.content)} B"
            except Exception as exc:  # noqa: BLE001
                last = f"{url}: {type(exc).__name__}"
            time.sleep(10)
    raise SystemExit(f"Overpass gave nothing: {last}")


def main() -> None:
    print(f"OSM land-use reference — {AOI_NAME}")
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for kind, body in QUERIES.items():
        d = overpass(body)
        dest = OUT / f"osm_{kind}_overpass_{AOI_NAME}.json"
        dest.write_text(json.dumps(d), encoding="utf-8")
        print(f"  [ok]   {dest.name}: {len(d['elements'])} elements")
        written.append(dest)
    record(OUT, source="OpenStreetMap via Overpass (tea gardens, reserve/protected forests)",
           url=SERVERS[0], files=written, license_="ODbL 1.0 — © OpenStreetMap contributors",
           notes="Reference outlines for the tree-class split (EROSION_PLAN.md E1.1). "
                 "Volunteer-mapped: incomplete and unevenly placed.")


if __name__ == "__main__":
    main()
