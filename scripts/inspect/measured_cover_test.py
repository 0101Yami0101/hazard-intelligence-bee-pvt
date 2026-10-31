"""Measured dry-season cover in the main map? Calibrate on half of Assam, judge on the other.

    $env:REGION = "assam"; python scripts/inspect/measured_cover_test.py

The candidates, halves and decision rule were written down before the dry-season
data existed (docs/design/EROSION_PLAN.md, "Phase 1, E1.5 part 3"):

    b    a cell's mean dry-season bare share over its evaluable seasons 2019-2026
    M1   C_class + b * max(0, 0.34 - C_class)              (tree, shrub, grass)
    M2   C_low + b * (0.34 - C_low), C_low 0.003 on tree    (tree, shrub, grass)
    calibration = folds 0-1; test = folds 2-4 (frozen spatial folds)
    go forward  if the better candidate beats main by >= 0.02 in X1 AUC on calibration
    adopt       if on test: X1 +0.02 or more, X2 not lower, and S1 still passes

Writes reports/measured_cover_<region>.json, and when adopted
data/interim/<region>/erosion/cover_measured_C.tif, which erosion_factors.py then
uses as the main run's C.
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
from scipy.stats import spearmanr

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, LANDCOVER, ROOT, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
YEARS = list(range(2019, 2027))
VALID_MIN = 0.50
C_CLEARED, TREE_LOW = 0.34, 0.003
REFRESH_LC, TREE = (10, 20, 30), 10
CAL_FOLDS, TEST_FOLDS = (0, 1), (2, 3, 4)
GO_MARGIN, ADOPT_MARGIN = 0.02, 0.02
HILLS = ("Karbi Anglong", "West Karbi Anglong", "Dima Hasao")


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def mean_bare(years) -> np.ndarray:
    with rasterio.open(LANDCOVER / "ee_dry_season" / f"dry_season_cover_{AOI_NAME}.tif") as s:
        names = list(s.descriptions)
        tot = np.zeros(G.SHAPE, np.float64)
        n = np.zeros(G.SHAPE, np.int16)
        for y in years:
            v = s.read(names.index(f"valid_{y}") + 1)
            b = s.read(names.index(f"bare_{y}") + 1)
            ev = (v != 255) & (v / 250 >= VALID_MIN) & (b != 255)
            tot[ev] += b[ev] / 250
            n[ev] += 1
    out = np.full(G.SHAPE, np.nan, np.float32)
    out[n > 0] = (tot[n > 0] / n[n > 0]).astype(np.float32)
    return out


def candidates(C, lc, b) -> dict:
    sel = np.isin(lc, REFRESH_LC) & np.isfinite(b)
    bb = np.nan_to_num(b)
    m1 = np.where(sel, C + bb * np.maximum(0, C_CLEARED - C), C).astype(np.float32)
    low = np.where(lc == TREE, TREE_LOW, C)
    m2 = np.where(sel, low + bb * (C_CLEARED - low), C).astype(np.float32)
    return {"M1": m1, "M2": m2}


def main() -> None:
    from compare_nrsc_ld import ANY_WATER, ERODED, NORMAL, REF, auc, per_unit
    from erosion_priority import ids_of
    print(f"Measured cover in the main map? — {AOI_NAME}")
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    ref = rd(REF)
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    R, K, LS, C = (rd(E / f"erosion_{f}.tif") for f in ("R", "K", "LS", "C"))
    A_main = rd(E / "erosion_A_tpha.tif")

    folds = pd.read_parquet(INTERIM / "spatial_folds.parquet").set_index("block_id").fold
    rows, cols = np.indices(G.SHAPE, dtype=np.int32)
    blk = G.fold_block(rows, cols)
    fold = np.full(G.SHAPE, -1, np.int8)
    known = np.isin(blk, folds.index.values)
    fold[known] = folds.reindex(blk[known].ravel()).values.reshape(-1)
    cal, test = np.isin(fold, CAL_FOLDS), np.isin(fold, TEST_FOLDS)

    variants = {}
    for tag, yrs in (("all", YEARS), ("2019-2021", YEARS[:3])):
        b = mean_bare(yrs)
        for k, c in candidates(C, lc, b).items():
            a = (R * K * LS * c).astype(np.float32)
            a[~ok] = np.nan
            variants[(k, tag)] = (a, c, b)
    maps = {"main": A_main, **{f"{k}_{t}": v[0] for (k, t), v in variants.items()}}

    usable = ok & (ref > 0) & np.all([np.isfinite(m) for m in maps.values()], axis=0)
    pair = usable & (np.isin(ref, ERODED) | (ref == NORMAL))

    def x1(m, where):
        s = pair & where
        return round(auc(m[s], np.isin(ref[s], ERODED)), 4)

    # catchments: majority half, by scored cells
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    bid, nb = ids_of(bas), len(bas)
    nm = per_unit(bid, nb, usable)
    share = per_unit(bid, nb, usable & np.isin(ref, ANY_WATER)) / np.maximum(nm, 1)
    in_test = per_unit(bid, nb, usable & test) > nm / 2

    def x2(m, which):
        mean = per_unit(bid, nb, usable, m.astype(np.float64)) / np.maximum(nm, 1)
        k = (nm >= 100) & (which if which is not None else True)
        return round(float(spearmanr(mean[k], share[k]).correlation), 4)

    dist = gpd.read_file(outline("district"))
    did, nd = ids_of(dist), len(dist)
    dn = per_unit(did, nd, usable)
    dshare = per_unit(did, nd, usable & np.isin(ref, ANY_WATER)) / np.maximum(dn, 1)

    def x3(m):
        mean = per_unit(did, nd, usable, m.astype(np.float64)) / np.maximum(dn, 1)
        return round(float(spearmanr(mean, dshare).correlation), 4)

    hill = np.isin(did, [i + 1 for i, n in enumerate(dist.NAME_2) if n in HILLS])

    def s1(m):
        h, p = np.nanmedian(m[ok & hill]), np.nanmedian(m[ok & ~hill])
        return round(float(h / p), 2)

    table = {k: {"X1_cal": x1(m, cal), "X1_test": x1(m, test), "X1_all": x1(m, np.ones(G.SHAPE, bool)),
                 "X2_test": x2(m, in_test), "X2_all": x2(m, None), "X3_all": x3(m), "S1": s1(m)}
             for k, m in maps.items()}
    b_all = variants[("M1", "all")][2]
    tree_pair = pair & (lc == TREE) & np.isfinite(b_all)
    within_tree_auc = round(auc(b_all[tree_pair], np.isin(ref[tree_pair], ERODED)), 4)

    # ---- the decision, exactly as written -----------------------------------
    best = max(("M1_all", "M2_all"), key=lambda k: table[k]["X1_cal"])
    go = table[best]["X1_cal"] - table["main"]["X1_cal"] >= GO_MARGIN
    checks = {"X1_test_gain": round(table[best]["X1_test"] - table["main"]["X1_test"], 4),
              "X2_test_not_lower": table[best]["X2_test"] >= table["main"]["X2_test"],
              "S1_passes": table[best]["S1"] >= 3.0}
    adopted = bool(go and checks["X1_test_gain"] >= ADOPT_MARGIN and checks["X2_test_not_lower"]
                   and checks["S1_passes"])
    rep = {"region": AOI_NAME, "halves": {"calibration_folds": CAL_FOLDS, "test_folds": TEST_FOLDS,
                                          "cal_pairs": int((pair & cal).sum()), "test_pairs": int((pair & test).sum()),
                                          "test_catchments": int(((nm >= 100) & in_test).sum())},
           "table": table, "within_tree_auc_of_bare_share": within_tree_auc,
           "best_on_calibration": best, "goes_forward": bool(go), "test_checks": checks,
           "adopted": adopted, "candidate": best.split("_")[0]}
    if adopted:
        c = variants[(best.split("_")[0], "all")][1]
        prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="float32",
                    crs=G.CRS, transform=G.TRANSFORM, nodata=np.nan, compress="deflate", tiled=True)
        with rasterio.open(E / "cover_measured_C.tif", "w", **prof) as d:
            d.write(c, 1)
    dest = ROOT / "reports" / f"measured_cover_{AOI_NAME}.json"
    dest.write_text(json.dumps(rep, indent=2))
    print(f"  pairs: calibration {rep['halves']['cal_pairs']:,}, test {rep['halves']['test_pairs']:,}; "
          f"test catchments {rep['halves']['test_catchments']}")
    for k, v in table.items():
        print(f"  {k:16} " + "  ".join(f"{kk} {vv}" for kk, vv in v.items()))
    print(f"  inside tree land, bare share alone: AUC {within_tree_auc}")
    print(f"  best on calibration: {best}; goes forward: {go}; test checks: {checks}; ADOPTED: {adopted}")


if __name__ == "__main__":
    main()
