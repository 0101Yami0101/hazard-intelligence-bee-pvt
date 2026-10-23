"""Official Assam boundaries from the Survey of India, into the raw store.

    python scripts/fetch/fetch_01b_soi_boundaries.py

Source: Survey of India Online Maps Portal (onlinemaps.surveyofindia.gov.in),
"Administrative Boundary Database", product OVSF/1M/9 "State Upto Distt. level
with HQ", 1:1M, shapefile, free (Rs 0). The portal needs a sign-in, so the
files were downloaded by hand by the user on 2026-10-20 into
data/raw/01_boundaries/18/ (18 = Assam's LGD state code). This script does not
fetch; it cleans, converts and records them.

Replaces GADM for Assam (EROSION_PLAN.md register V-12): GADM 4.1 had 27
outdated districts and a non-commercial licence; this has the 35 current ones
with their LGD codes. Arunachal keeps GADM (scripts/common.py BOUNDARY_SOURCE).

Cleaning: district names carry a trailing CR/LF in the source and one typo
("WEST KARBI ANAGLONG"); names are stripped, corrected and title-cased into
NAME_1 / NAME_2 columns, the same names GADM uses, so downstream code that reads
NAME_2 works unchanged. Converted from the source's Lambert conformal conic to
EPSG:4326.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd

from common import BOUNDARIES, record

SRC = BOUNDARIES / "18"
FIX = {"WEST KARBI ANAGLONG": "WEST KARBI ANGLONG"}


def title(s: str) -> str:
    s = FIX.get(s.strip(), s.strip())
    return " ".join(w.capitalize() for w in s.split())


def main() -> None:
    print("Survey of India boundaries — Assam")
    st = gpd.read_file(SRC / "ASSAM_STATE_BDY.shp").to_crs(4326)
    st = gpd.GeoDataFrame({"NAME_1": ["Assam"]}, geometry=[st.geometry.union_all()], crs=4326)
    d = gpd.read_file(SRC / "ASSAM_DISTRICT_BDY.shp").to_crs(4326)
    d = gpd.GeoDataFrame({"NAME_1": "Assam", "NAME_2": d.DISTRICT.map(title),
                          "LGD": d.DIST_LGD.astype(str).str.strip()}, geometry=d.geometry, crs=4326)
    d = d.dissolve(by=["NAME_1", "NAME_2", "LGD"], as_index=False)
    hq = gpd.read_file(SRC / "ASSAM_DISTRICT_HQ.shp").to_crs(4326)
    hq = gpd.GeoDataFrame({"NAME_2": hq.DISTRICT.map(title), "HQ": hq.DIST_HQ.astype(str).str.strip()},
                          geometry=hq.geometry, crs=4326)
    out = {"state": BOUNDARIES / "soi_state-boundary_vector_assam.gpkg",
           "district": BOUNDARIES / "soi_district-boundary_vector_assam.gpkg",
           "hq": BOUNDARIES / "soi_district-hq_point_assam.gpkg"}
    st.to_file(out["state"], driver="GPKG")
    d.to_file(out["district"], driver="GPKG")
    hq.to_file(out["hq"], driver="GPKG")
    area = st.to_crs(32646).area.sum() / 1e6
    print(f"  state {area:,.0f} km2 (official 78,438); {len(d)} districts; {len(hq)} HQs")
    record(BOUNDARIES, source="Survey of India OVSF/1M/9 (state and districts with HQ, 1:1M)",
           url="https://onlinemaps.surveyofindia.gov.in/Digital_Product_Show.aspx",
           files=[*(SRC.glob("*.shp")), *out.values()],
           license_="Survey of India; free download (Rs 0) under the portal's terms",
           notes="Downloaded by hand by the user on 2026-10-20 (portal sign-in). 35 districts with LGD "
                 "codes. Cleaned: names stripped and title-cased, 'ANAGLONG' corrected; LCC -> EPSG:4326.")


if __name__ == "__main__":
    main()
