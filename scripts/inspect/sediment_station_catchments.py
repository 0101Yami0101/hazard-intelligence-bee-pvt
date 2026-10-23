"""Each CWC sediment station's catchment, and how much of it the erosion map covers.

    python scripts/inspect/sediment_station_catchments.py

Why (EROSION_PLAN.md, Phase 1, V3): a station's measured mud can only test our
erosion map if most of the land draining to it is land we have mapped. Assam's
rivers mostly rise in the hills around it, so this is checked first.

Method: snap each station to the nearest HydroRIVERS v10 reach within 3 km that
drains >= 50 km2, collect every reach upstream (NEXT_DOWN), take the union of
their HydroBASINS level-12 basins as the catchment, and measure the share of its
area inside Assam (GADM) and inside India (GADM; the national rain-strength maps
cover India only). Station coordinates are CWC's own; a station with no reach
within 3 km is reported, not guessed.

Writes reports/sediment_station_catchments.csv
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from common import BOUNDARIES, GAUGES, HYDROLOGY, ROOT

warnings.filterwarnings("ignore")

SED = GAUGES / "cwc_sediment"
ASSAM_FILES = ("08cf3a3a-c6e5-4c7a-871d-28861a3f8b88", "b809cd25-a40b-495c-91b3-67137963e542")
BBOX = (88.0, 21.5, 97.8, 30.5)
UTM = 32646


def main() -> None:
    d = pd.concat([pd.read_csv(SED / f"{r}.csv", dtype=str) for r in ASSAM_FILES])
    d["t"] = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    st = d.groupby("Station").agg(river=("Local River", "first"), district=("District", "first"),
                                  lat=("Latitude", "first"), lon=("Longitude", "first"),
                                  readings=("t", "count"), y0=("t", lambda s: s.min().year),
                                  y1=("t", lambda s: s.max().year),
                                  years=("t", lambda s: s.dt.year.nunique())).reset_index()
    st["lat"], st["lon"] = st.lat.astype(float), st.lon.astype(float)

    hs = HYDROLOGY / "hydrosheds"
    riv = gpd.read_file(hs / "HydroRIVERS_v10_as" / "HydroRIVERS_v10_as_shp" / "HydroRIVERS_v10_as.shp", bbox=BBOX)
    bas = gpd.read_file(hs / "hybas_as_lev01-12_v1c" / "hybas_as_lev12_v1c.shp", bbox=BBOX)
    gadm = BOUNDARIES / "gadm41_IND.gpkg"
    assam = gpd.read_file(gadm, layer="ADM_ADM_1").query("NAME_1 == 'Assam'").to_crs(UTM).geometry.union_all()
    india = gpd.read_file(gadm, layer="ADM_ADM_0").to_crs(UTM).geometry.union_all()

    rivu = riv.to_crs(UTM)
    basu = bas.to_crs(UTM).set_index("HYBAS_ID")
    up: dict[int, list[int]] = {}
    for a, b in zip(riv.HYRIV_ID.values, riv.NEXT_DOWN.values):
        up.setdefault(int(b), []).append(int(a))

    rows = []
    for _, s in st.iterrows():
        p = gpd.GeoSeries([Point(s.lon, s.lat)], crs=4326).to_crs(UTM).iloc[0]
        near = rivu[(rivu.distance(p) < 3000) & (rivu.UPLAND_SKM >= 50)].copy()
        base = {k: s[k] for k in ("Station", "river", "district", "y0", "y1", "years", "readings")}
        if near.empty:
            rows.append({**base, "note": "no reach >= 50 km2 within 3 km of CWC's coordinates"})
            continue
        near["dist"] = near.distance(p)
        r0 = near.sort_values("dist").iloc[0]
        stack, seen = [int(r0.HYRIV_ID)], set()
        while stack:
            x = stack.pop()
            if x not in seen:
                seen.add(x)
                stack.extend(up.get(x, []))
        hb = [h for h in set(riv[riv.HYRIV_ID.isin(seen)].HYBAS_L12.astype("int64")) if h in basu.index]
        poly = basu.loc[hb].geometry.union_all()
        area = poly.area / 1e6
        rows.append({**base, "snap_m": round(float(r0.dist)), "reach_upland_km2": round(float(r0.UPLAND_SKM)),
                     "catchment_km2": round(area),
                     "in_assam_pct": round(100 * poly.intersection(assam).area / 1e6 / area, 1),
                     "in_india_pct": round(100 * poly.intersection(india).area / 1e6 / area, 1),
                     "note": "snap > 1 km: check the reach" if r0.dist > 1000 else ""})
    out = pd.DataFrame(rows).sort_values(["in_assam_pct"], ascending=False)
    dest = ROOT / "reports" / "sediment_station_catchments.csv"
    out.to_csv(dest, index=False)
    pd.set_option("display.width", 250)
    print(out.to_string(index=False))
    print(f"\n  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
