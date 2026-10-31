"""OpenStreetMap place names (villages, towns) for SoilSense's village search (E2.3).

    $env:REGION = "assam"; python scripts/fetch/fetch_52_osm_places.py

Nodes tagged place = city / town / village / hamlet with a name, inside the region's
bounding box (the build clips them to the state). Keeps the Assamese name (name:as)
where volunteers have mapped one, so the village card can show it as written by
local mappers rather than a machine translation.

Licence: ODbL 1.0 — attribution "© OpenStreetMap contributors".
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import AOI_NAME, BOUNDARIES, record
from fetch_45_osm_landuse_reference import SERVERS, overpass

OUT = BOUNDARIES / "osm_places"
BODY = """(node["place"~"^(city|town|village|hamlet)$"]["name"];);"""


def main() -> None:
    print(f"OSM places — {AOI_NAME}")
    d = overpass(BODY)
    rows = [{"name": e["tags"].get("name"), "name_as": e["tags"].get("name:as", ""),
             "place": e["tags"].get("place"), "lat": round(e["lat"], 5), "lon": round(e["lon"], 5),
             "osm_id": e["id"]} for e in d["elements"] if e.get("type") == "node"]
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / f"osm_places_{AOI_NAME}.json"
    dest.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    kinds = {}
    for r in rows:
        kinds[r["place"]] = kinds.get(r["place"], 0) + 1
    print(f"  {len(rows):,} places {kinds}; with an Assamese name: {sum(bool(r['name_as']) for r in rows):,}")
    record(OUT, source="OpenStreetMap via Overpass (named places: city, town, village, hamlet)",
           url=SERVERS[0], files=[dest], license_="ODbL 1.0 — © OpenStreetMap contributors",
           notes="Village search for SoilSense (EROSION_PLAN.md E2.3). Volunteer-mapped: incomplete; "
                 "name:as kept where mapped.")


if __name__ == "__main__":
    main()
