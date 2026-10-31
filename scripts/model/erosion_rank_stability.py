"""How firm is each catchment's rank? 1,000 runs across the unsettled inputs (V-17 part 2).

    $env:REGION = "assam"; python scripts/model/erosion_rank_stability.py

The ranges were written down before this ran (docs/design/EROSION_PLAN.md, "V-17 part 2"):

    R      R_InRESatE^(1-w) * R_IRED^w, w ~ U(0, 1)
    C      tree: log-U(0.003, 0.1), one value per draw;
           shrub, grass, cropland: each x log-U(1/1.5, 1.5)
    S      McCool or Nearing, 50/50
    K, P   not varied
    1,000 draws, seed 42

Per catchment and district: share of runs in the top 20 and top 50, median rank and
its 5th-95th percentile range. "Robust" = top 20 in >= 80% of runs.

Writes reports/erosion_rank_stability_<region>.csv (catchments), _districts.csv and .json,
and adds the columns to reports/erosion_priority_<region>*.csv for the bundle.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import rankdata

from common import AOI_NAME, HYDROLOGY, INTERIM, ROOT, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
DRAWS, SEED = 1000, 42
TREE_C = (0.003, 0.1)
CLASS_SCALE = 1.5
TOP, TOP_WIDE, ROBUST = 20, 50, 0.80
TREE, SHRUB, GRASS, CROP = 10, 20, 30, 40


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def main() -> None:
    from erosion_priority import UNIT_MIN_CELLS, ids_of
    t0 = time.time()
    print(f"Rank stability, {DRAWS} runs — {AOI_NAME}")
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    R_inr, R_ired = rd(E / "erosion_R.tif"), None
    # IRED's R on the grid: from the IRED run's A and the shared factors (A = R K LS C)
    K, LS, LSn, C = (rd(E / f"erosion_{f}.tif") for f in ("K", "LS", "LS_nearing", "C"))
    A_ired = rd(E / "erosion_A_ired_tpha.tif")
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    with np.errstate(invalid="ignore", divide="ignore"):
        R_ired = A_ired / (K * LS * C)
    sel = ok & np.isfinite(R_inr) & np.isfinite(R_ired) & (R_ired > 0) & np.isfinite(LSn)
    lr_inr, lr_ired = np.log(R_inr[sel]).astype(np.float32), np.log(R_ired[sel]).astype(np.float32)
    k, ls, lsn, c0, cls = K[sel], LS[sel], LSn[sel], C[sel], lc[sel]

    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    units = {"catchments": (ids_of(bas)[sel], len(bas)), "districts": (ids_of(dist)[sel], len(dist))}
    n_cells = {u: np.bincount(i, minlength=n + 1)[1:] for u, (i, n) in units.items()}
    keep = {"catchments": n_cells["catchments"] >= UNIT_MIN_CELLS, "districts": n_cells["districts"] >= 1}

    rng = np.random.default_rng(SEED)
    ranks = {u: np.zeros((DRAWS, int(keep[u].sum())), np.int16) for u in units}
    draws = []
    for d in range(DRAWS):
        w = rng.uniform(0, 1)
        c_tree = float(np.exp(rng.uniform(np.log(TREE_C[0]), np.log(TREE_C[1]))))
        sc = {c: float(np.exp(rng.uniform(-np.log(CLASS_SCALE), np.log(CLASS_SCALE)))) for c in (SHRUB, GRASS, CROP)}
        nearing = bool(rng.uniform() < 0.5)
        cc = c0.copy()
        cc[cls == TREE] = c_tree
        for c, s in sc.items():
            cc[cls == c] *= s
        a = np.exp((1 - w) * lr_inr + w * lr_ired) * k * (lsn if nearing else ls) * cc
        for u, (ids, n) in units.items():
            mean = (np.bincount(ids, weights=a, minlength=n + 1)[1:] / np.maximum(n_cells[u], 1))[keep[u]]
            ranks[u][d] = rankdata(-mean, method="min").astype(np.int16)
        draws.append({"w": round(w, 3), "c_tree": round(c_tree, 4), "nearing": nearing,
                      **{f"scale_{c}": round(s, 3) for c, s in sc.items()}})
        if (d + 1) % 200 == 0:
            print(f"    {d + 1}/{DRAWS} runs, {time.time() - t0:.0f}s", flush=True)

    out = {}
    for u, gdf in (("catchments", bas), ("districts", dist)):
        r = ranks[u]
        t = pd.DataFrame({"top20_pct": (100 * (r <= TOP).mean(axis=0)).round(1),
                          "top50_pct": (100 * (r <= TOP_WIDE).mean(axis=0)).round(1),
                          "rank_median": np.median(r, axis=0).astype(int),
                          "rank_p05": np.percentile(r, 5, axis=0).astype(int),
                          "rank_p95": np.percentile(r, 95, axis=0).astype(int)})
        if u == "catchments":
            t.insert(0, "HYBAS_ID", bas.HYBAS_ID.values[keep[u]].astype("int64"))
        else:
            t.insert(0, "district", dist.NAME_2.values[keep[u]])
        t["robust"] = t.top20_pct >= 100 * ROBUST
        out[u] = t
    cat, dis = out["catchments"], out["districts"]
    cat.to_csv(ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}.csv", index=False)
    dis.to_csv(ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}_districts.csv", index=False)

    # join onto the priority tables so the bundle export carries the columns
    cols = ["top20_pct", "top50_pct", "rank_median", "rank_p05", "rank_p95", "robust"]
    p1 = pri.drop(columns=[c for c in cols if c in pri]).merge(cat, on="HYBAS_ID", how="left")
    p1.to_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv", index=False)
    pd_ = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}_districts.csv")
    pd_ = pd_.drop(columns=[c for c in cols if c in pd_]).merge(dis, on="district", how="left")
    pd_.to_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}_districts.csv", index=False)

    main_top = p1[p1.rank_main <= TOP]
    rep = {"region": AOI_NAME, "draws": DRAWS, "seed": SEED,
           "ranges": {"R_blend_w": [0, 1], "tree_C": TREE_C, "class_scale": CLASS_SCALE, "S": ["McCool", "Nearing"]},
           "catchments_robust_top20": int(cat.robust.sum()),
           "catchments_top20_in_half_the_runs": int((cat.top20_pct >= 50).sum()),
           "main_top20_robust": int(main_top.robust.sum()),
           "main_top20_median_top20_pct": float(main_top.top20_pct.median()),
           "firm_mark_vs_runs": p1.groupby(p1.mark.fillna("")).top20_pct.median().round(1).to_dict(),
           "districts_robust_top5": dis.sort_values("top20_pct", ascending=False).head(0).to_dict(),
           "seconds": round(time.time() - t0)}
    r_d = ranks["districts"]
    dis["top5_pct"] = (100 * (r_d <= 5).mean(axis=0)).round(1)
    rep["districts_top5_pct"] = dis.sort_values("top5_pct", ascending=False).head(10)[["district", "top5_pct", "rank_median"]].to_dict("records")
    rep.pop("districts_robust_top5")
    (ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: v for k, v in rep.items() if k != "ranges"}, indent=1))
    show = p1.sort_values("top20_pct", ascending=False).head(25)
    print(show[["rank_main", "district", "meanA_main", "mark", "top20_pct", "rank_median", "rank_p05", "rank_p95"]].to_string(index=False))


if __name__ == "__main__":
    main()
