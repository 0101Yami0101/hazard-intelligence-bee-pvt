"""Compare the two rain-erosivity (R) maps over a region, and against the gauge.

Why (docs/design/EROSION_PLAN.md R2, R3): the soil-erosion module needs R, and the
choice moves every class. This puts both open maps side by side, at the one place
with a gauge-derived R (Guwahati, IIT Guwahati 2017: 7,924 MJ mm/ha/h/yr from 15
years of half-hourly IMD rain), at a few towns, and district by district, so the
choice rests on measured numbers.

    python scripts/fetch/fetch_42_erosivity.py              # once, needs the maps
    $env:REGION = "assam"; python scripts/inspect/compare_erosivity.py

Writes reports/erosivity_comparison_<region>.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import rasterio
import scipy.io as sio
from rasterio.features import geometry_mask
from scipy.stats import spearmanr
from shapely import contains_xy

from common import AOI_NAME, BOUNDARIES, ROOT, WEATHER, outline

warnings.filterwarnings("ignore")

ER = WEATHER / "erosivity"
IRED_TIF = ER / "ired" / "Indian Rainfall Erosivity Dataset (IRED)" / "Dataset" / "tif" / "R-Factor_India.tif"
INRESATE = ER / "inresate" / "R-factor"

GAUGE = {"name": "Guwahati IMD (Borjhar)", "lat": 26.10, "lon": 91.59, "R": 7924.29,
         "source": "Das & Sarma 2017, IIT Guwahati, Table 5.2 (15 yr half-hourly IMD)"}
SINGH_AT_GAUGE = 692.971            # the same report, Table 5.10: R = 79 + 0.363 x AAP

TOWNS = {"Kokrajhar": (26.40, 90.27), "Haflong (Dima Hasao)": (25.17, 93.02),
         "Diphu (Karbi Anglong)": (25.84, 93.43), "Silchar": (24.82, 92.80),
         "Dibrugarh": (27.48, 94.91)}


def load_ired():
    with rasterio.open(IRED_TIF) as r:
        a = r.read(1).astype(float)
        if r.nodata is not None:
            a[a == r.nodata] = np.nan
        a[a < 0] = np.nan
        return a, r.transform, r.index


def load_inresate():
    def one(name):
        d = sio.loadmat(INRESATE / f"{name}.mat")
        return np.asarray(d[[k for k in d if not k.startswith("__")][0]], float)
    R, lat, lon = one("R"), np.ravel(one("lat")), np.ravel(one("lon"))
    if R.shape == (len(lon), len(lat)):
        R = R.T
    return R, lat, lon


def main() -> None:
    state = gpd.read_file(outline("state")).to_crs(4326)
    dist = gpd.read_file(outline("district")).to_crs(4326)
    shape_all = state.geometry.union_all()

    ired, tr, idx = load_ired()
    R, lat, lon = load_inresate()
    LON, LAT = np.meshgrid(lon, lat)

    def ired_at(la, lo):
        r, c = idx(lo, la)
        return float(ired[r, c])

    def inr_at(la, lo):
        return float(R[np.argmin(abs(lat - la)), np.argmin(abs(lon - lo))])

    def ired_in(geom, touched):
        # whole state: cell centre inside; a district: any cell it touches, so
        # small districts still get several 0.12-degree cells
        m = geometry_mask([geom], out_shape=ired.shape, transform=tr, invert=True, all_touched=touched)
        v = ired[m]
        return v[np.isfinite(v)]

    def inr_in(geom):
        m = contains_xy(geom, LON, LAT) & np.isfinite(R)
        return R[m]

    pct = [5, 25, 50, 75, 95]
    out = {"region": AOI_NAME, "units": "MJ mm ha-1 h-1 yr-1", "gauge": GAUGE,
           "at_gauge": {}, "towns": {}, "region_percentiles": {}, "districts": {}}

    g = GAUGE
    for k, v in {"Singh 1981": SINGH_AT_GAUGE, "IRED": ired_at(g["lat"], g["lon"]),
                 "InRESatE": inr_at(g["lat"], g["lon"])}.items():
        out["at_gauge"][k] = {"R": round(v), "error_pct": round(100 * (v / g["R"] - 1), 1)}
    for name, (la, lo) in TOWNS.items():
        out["towns"][name] = {"IRED": round(ired_at(la, lo)), "InRESatE": round(inr_at(la, lo))}
    for k, v in {"IRED": ired_in(shape_all, False), "InRESatE": inr_in(shape_all)}.items():
        out["region_percentiles"][k] = {"cells": int(v.size), **{f"p{p}": round(float(np.percentile(v, p))) for p in pct}}

    for _, row in dist.iterrows():
        a, b = ired_in(row.geometry, True), inr_in(row.geometry)
        if a.size and b.size:
            out["districts"][row.NAME_2] = {"IRED": round(float(np.median(a))),
                                            "InRESatE": round(float(np.median(b)))}
    d = out["districts"]
    rho = spearmanr([v["IRED"] for v in d.values()], [v["InRESatE"] for v in d.values()]).correlation
    out["district_spearman"] = round(float(rho), 2)
    out["n_districts"] = len(d)

    dest = ROOT / "reports" / f"erosivity_comparison_{AOI_NAME}.json"
    dest.write_text(json.dumps(out, indent=2))

    print(f"R at the Guwahati gauge ({g['R']:,.0f}):")
    for k, v in out["at_gauge"].items():
        print(f"  {k:<10} {v['R']:>7,}  {v['error_pct']:+.0f}%")
    for k, v in out["region_percentiles"].items():
        print(f"  {k:<10} {AOI_NAME} p5..p95: " + " / ".join(f"{v[f'p{p}']:,}" for p in pct))
    print(f"  district Spearman IRED vs InRESatE: {out['district_spearman']} (n={len(d)})")
    print(f"  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
