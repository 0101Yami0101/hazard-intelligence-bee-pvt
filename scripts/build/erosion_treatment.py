"""AD-24: "What if we treat it?" — tonnes saved by soil-conservation measures, per unit.

    $env:REGION = "assam"; python scripts/build/erosion_treatment.py

The recipe run forwards: A = R K LS C P. A measure changes P (protection) or C (cover)
on the land where it applies, and the soil saved is the old A minus the new A, summed
over that land (a 100 m cell is 1 ha, so t/ha/yr sums to t/yr).

Measures and their values (each provisional; register V-32 in EROSION_PLAN.md):

    contour   contour bunds / trenches. Cropland, grass, shrub, bare, slope 1.7-14 deg.
              P by slope from Wischmeier & Smith (1978) Table 13 (contouring):
              3-8 % slope 0.5 | 9-12 % 0.6 | 13-16 % 0.7 | 17-20 % 0.8 | 21-25 % 0.9; above 25 %
              (14 deg) contouring alone is not effective (P 1)
    terrace   bench terraces. Cropland, grass, shrub, bare, slope >= 8 deg. P 0.15, mid of the
              0.1-0.2 range reported for bench terracing in Indian hill studies (to confirm)
    replant   revegetation / agroforestry. Cropland, grass, shrub, bare, slope >= 15 deg.
              C -> 0.05 (an established tree-shrub cover; between W&S closed forest and IWED's
              0.11 shrub)

Per catchment and district, for each measure: eligible hectares, tonnes a year saved if the
whole eligible land is treated, and tonnes saved per hectare treated. Measures are not
summed when combined on the same land: the app applies them in the order replant >
terrace > contour, each only on land the earlier ones did not take.

Output: webapp/assets/erosion/<region>/treatment.json, reports/erosion_treatment_<region>.csv
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from common import AOI_NAME, HYDROLOGY, INTERIM, ROOT, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
OPEN = (20, 30, 40, 60)                      # shrub, grass, cropland, bare/sparse (WorldCover)
# Wischmeier & Smith (1978), Table 13, contouring: (upper slope %, P)
CONTOUR_TABLE = [(2.0, 0.6), (8.0, 0.5), (12.0, 0.6), (16.0, 0.7), (20.0, 0.8), (25.0, 0.9)]
CONTOUR_RANGE_DEG = (1.7, 14.0)
TERRACE_P, TERRACE_MIN_DEG = 0.15, 8.0
REPLANT_C, REPLANT_MIN_DEG = 0.05, 15.0
ORDER = ("replant", "terrace", "contour")


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def p_contour(slope_deg: np.ndarray) -> np.ndarray:
    pct = 100 * np.tan(np.radians(slope_deg))
    p = np.ones_like(pct, dtype=np.float32)
    lo = 0.0
    for hi, val in CONTOUR_TABLE:
        p[(pct > lo) & (pct <= hi)] = val
        lo = hi
    return p


def main() -> None:
    from erosion_priority import ids_of
    print(f"What-if treatment — {AOI_NAME}")
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A = np.nan_to_num(rd(E / "erosion_A_tpha.tif"))
    C = rd(E / "erosion_C.tif")
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif")
    open_land = ok & np.isin(lc, OPEN)

    taken = np.zeros_like(ok)
    measures = {}
    # replant first: the steepest open land
    el = open_land & (slope >= REPLANT_MIN_DEG)
    with np.errstate(invalid="ignore", divide="ignore"):
        new = np.where(C > 0, A * np.minimum(REPLANT_C, C) / C, A)
    measures["replant"] = (el, A - new)
    taken |= el
    el = open_land & (slope >= TERRACE_MIN_DEG) & ~taken
    measures["terrace"] = (el, A * (1 - TERRACE_P))
    taken |= el
    el = open_land & (slope >= CONTOUR_RANGE_DEG[0]) & (slope < CONTOUR_RANGE_DEG[1]) & ~taken
    measures["contour"] = (el, A * (1 - p_contour(slope)))

    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    out, rows = {"measures": {"replant": {"C": REPLANT_C, "min_slope_deg": REPLANT_MIN_DEG},
                              "terrace": {"P": TERRACE_P, "min_slope_deg": TERRACE_MIN_DEG},
                              "contour": {"P_table_pct": CONTOUR_TABLE, "slope_deg": CONTOUR_RANGE_DEG}},
                 "order": ORDER}, []
    for kind, gdf, key in (("catchments", bas, "HYBAS_ID"), ("districts", dist, "NAME_2")):
        ids = ids_of(gdf)
        n = len(gdf)
        total = np.bincount(ids[ok], weights=A[ok].astype(np.float64), minlength=n + 1)[1:]
        unit = {"id": [str(v) if key == "NAME_2" else int(v) for v in gdf[key]], "total_t": np.round(total).tolist()}
        for name, (el, saved) in measures.items():
            m = el & (ids > 0)
            ha = np.bincount(ids[m], minlength=n + 1)[1:]
            t = np.bincount(ids[m], weights=np.nan_to_num(saved[m]).astype(np.float64), minlength=n + 1)[1:]
            unit[f"{name}_ha"] = ha.astype(int).tolist()
            unit[f"{name}_t"] = np.round(t).tolist()
            if kind == "catchments":
                for i in range(n):
                    rows.append({"HYBAS_ID": int(gdf[key].iloc[i]), "measure": name, "eligible_ha": int(ha[i]),
                                 "saved_t_per_yr": round(float(t[i])),
                                 "saved_t_per_ha": round(float(t[i] / ha[i]), 1) if ha[i] else None,
                                 "share_of_total_pct": round(100 * float(t[i] / total[i]), 1) if total[i] else None})
        out[kind] = unit
    dest = ROOT / "webapp" / "assets" / "erosion" / AOI_NAME / "treatment.json"
    dest.write_text(json.dumps(out, separators=(",", ":")))
    t = pd.DataFrame(rows)
    t.to_csv(ROOT / "reports" / f"erosion_treatment_{AOI_NAME}.csv", index=False)
    s = t.groupby("measure").agg(ha=("eligible_ha", "sum"), saved=("saved_t_per_yr", "sum"))
    print(s.assign(t_per_ha=lambda d: (d.saved / d.ha).round(1)).to_string())
    for m in ORDER:
        top = t[t.measure == m].dropna(subset=["saved_t_per_ha"]).query("eligible_ha >= 200").nlargest(5, "saved_t_per_ha")
        print(f"  best for {m}:", top[["HYBAS_ID", "eligible_ha", "saved_t_per_ha", "share_of_total_pct"]].to_dict("records")[:3])
    print(f"  wrote {dest.relative_to(ROOT)} ({dest.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
