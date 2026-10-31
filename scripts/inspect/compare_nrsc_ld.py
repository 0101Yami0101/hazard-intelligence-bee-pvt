"""SoilSense against NRSC's Land Degradation 1:50k (2015-16): checks X1-X3 (E1.5 / V2).

    $env:REGION = "assam"; python scripts/inspect/compare_nrsc_ld.py

The test and its bars were written down before this script first ran
(docs/design/EROSION_PLAN.md, "Phase 1, E1.5 (V2) part 1"):

    X1  AUC of our A: NRSC eroded (codes 2-7) vs NRSC normal (8), scored cells   >= 0.70
    X2  Spearman, 703 catchments: our mean A vs NRSC water-erosion share (1-7)   >= 0.40
    X3  the same over the 35 districts                                           >= 0.50

Reported beside them, no bar: IWED (the IIT Delhi national map), our IRED run, our
tree C 0.003 run, and slope alone. AUC uses average ranks, so tied values count
half (a tie-blind AUC once turned chance into 0.88 in this project).

Output: reports/nrsc_ld_comparison_<region>.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import rankdata, spearmanr

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, LANDCOVER, ROOT, WEATHER, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
REF = LANDCOVER / "nrsc_ld50k" / f"nrsc_ld50k_1516_{AOI_NAME}.tif"
BARS = {"X1": 0.70, "X2": 0.40, "X3": 0.50}
ERODED, NORMAL, ANY_WATER = (2, 3, 4, 5, 6, 7), 8, (1, 2, 3, 4, 5, 6, 7)


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def auc(score: np.ndarray, pos: np.ndarray) -> float:
    """Mann-Whitney AUC with average ranks (ties count half)."""
    r = rankdata(score)
    n1, n0 = int(pos.sum()), int((~pos).sum())
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def per_unit(ids, n, sel, w=None):
    return np.bincount(ids[sel], weights=None if w is None else w[sel], minlength=n + 1)[1:]


def main() -> None:
    from check_erosion_bars import find_tif, onto_grid
    from erosion_priority import ids_of
    print(f"SoilSense vs NRSC land degradation 2015-16 — {AOI_NAME}")
    ref = rd(REF)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    maps = {"ours_main": rd(E / "erosion_A_tpha.tif"),
            "ours_ired": rd(E / "erosion_A_ired_tpha.tif"),
            "ours_treeC_0.003": rd(E / "erosion_A_treeC_alt_tpha.tif"),
            "slope_alone": rd(INTERIM / "terrain" / "terrain_slope_deg.tif").astype(np.float32)}
    iwed = find_tif(WEATHER / "erosivity" / "iwed", "psl_india")
    if iwed:
        maps["IWED"] = onto_grid(iwed)
    mapped = ok & (ref > 0)
    common = mapped & np.all([np.isfinite(m) for m in maps.values()], axis=0)

    # ---- X1: cells ----------------------------------------------------------
    x1 = {}
    sel = common & (np.isin(ref, ERODED) | (ref == NORMAL))
    pos = np.isin(ref[sel], ERODED)
    for k, m in maps.items():
        x1[k] = round(auc(m[sel], pos), 3)
    cls_km2 = {int(v): round(int(c) / 100) for v, c in zip(*np.unique(ref[mapped], return_counts=True))}

    # ---- X2 / X3: units -----------------------------------------------------
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    units = {}
    for name, gdf in (("X2_catchments", bas), ("X3_districts", dist)):
        ids, n = ids_of(gdf), len(gdf)
        nm = per_unit(ids, n, common)
        share = per_unit(ids, n, common & np.isin(ref, ANY_WATER)) / np.maximum(nm, 1)
        keep = nm >= (100 if name.startswith("X2") else 1)
        res = {"units": int(keep.sum()),
               "nrsc_water_erosion_share_median_pct": round(100 * float(np.median(share[keep])), 1)}
        for k, m in maps.items():
            mean = per_unit(ids, n, common, m.astype(np.float64)) / np.maximum(nm, 1)
            res[k] = round(float(spearmanr(mean[keep], share[keep]).correlation), 3)
        units[name] = res
        if name.startswith("X3"):
            mean = per_unit(ids, n, common, maps["ours_main"].astype(np.float64)) / np.maximum(nm, 1)
            units["district_table"] = sorted(
                ({"district": d, "ours_meanA": round(float(a), 1), "nrsc_water_erosion_pct": round(100 * float(s), 1)}
                 for d, a, s, kk in zip(dist.NAME_2, mean, share, keep) if kk),
                key=lambda r: -r["ours_meanA"])

    rep = {"region": AOI_NAME, "reference": "NRSC Land Degradation 1:50k 2015-16 (Bhuvan ld:AS_LD50K_1516)",
           "cells_compared": int(common.sum()), "scored_cells": int(ok.sum()),
           "nrsc_classes_km2_on_scored": cls_km2,
           "X1_auc_eroded_vs_normal": {**x1, "n_eroded": int(pos.sum()), "n_normal": int((~pos).sum()),
                                       "bar": BARS["X1"], "pass": x1["ours_main"] >= BARS["X1"]},
           "X2_catchments_spearman": {**units["X2_catchments"], "bar": BARS["X2"],
                                      "pass": units["X2_catchments"]["ours_main"] >= BARS["X2"]},
           "X3_districts_spearman": {**units["X3_districts"], "bar": BARS["X3"],
                                     "pass": units["X3_districts"]["ours_main"] >= BARS["X3"]},
           "district_table": units["district_table"]}
    dest = ROOT / "reports" / f"nrsc_ld_comparison_{AOI_NAME}.json"
    dest.write_text(json.dumps(rep, indent=2))
    print(f"  cells compared {rep['cells_compared']:,} of {rep['scored_cells']:,} scored; NRSC classes (km2): {cls_km2}")
    for x in ("X1_auc_eroded_vs_normal", "X2_catchments_spearman", "X3_districts_spearman"):
        r = rep[x]
        print(f"  {x}: " + "  ".join(f"{k} {r[k]}" for k in maps) + f"   bar {r['bar']}  {'PASS' if r['pass'] else 'FAIL'}")
    print(f"  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
