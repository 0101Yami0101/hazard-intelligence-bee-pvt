"""AD-27: why the AI says so — per-catchment and per-district reasons, and agreement with the formula.

    $env:REGION = "assam"; python scripts/model/erosion_ai_explain.py

Reads the full AI model (train_erosion_ai.py --full) and its score map. For each ranked
catchment and each district:

    ai_score     mean AI score over the unit's scored squares (a relative index, not a chance)
    ai_rank      rank of that mean among the units
    agreement    "both high" (top 50 by both), "AI higher", "formula higher", or "both lower",
                 for catchments; districts use the top 8
    ai_reason    the input group that pushes the AI's score up most in this unit, from SHAP
                 values (LightGBM's own TreeSHAP, pred_contrib), averaged over a sample of up
                 to 300 scored squares per unit, in log-odds
    ai_against   the group that pulls it down most

Groups: rain strength (R maps), terrain (height, slopes, curvature, aspect, LS), water and
drainage (upstream area, height above channel, wetness, channel size), soil (SoilGrids, K),
cover (land cover, C, canopy height).

Writes reports/erosion_ai_units_<region>.csv and _districts.csv.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio

from common import AOI_NAME, HYDROLOGY, ROOT, outline

warnings.filterwarnings("ignore")

PER_UNIT, SEED, TOP_C, TOP_D = 300, 42, 50, 8
GROUP_NAMES = {"rain": "rain strength", "terrain": "steep or rugged terrain", "water": "water and drainage",
               "soil": "soil", "cover": "land cover"}


def group_of(f: str) -> str:
    if f.startswith("R_"):
        return "rain"
    if f.startswith(("hydro_",)):
        return "water"
    if f.startswith("soil_") or f == "K":
        return "soil"
    if f.startswith(("canopy_", "lc_")) or f == "C":
        return "cover"
    return "terrain"


def main() -> None:
    import train_erosion_ai as T
    from erosion_priority import ids_of
    print(f"AI reasons — {AOI_NAME}")
    model = lgb.Booster(model_file=str(T.MODELS / "full_A.txt"))
    names = model.feature_name()
    ok = T.rd(T.E / "erosion_assessed.tif").astype(bool)
    score = T.rd(T.E / "erosion_ai_score.tif")
    A = T.rd(T.E / "erosion_A_tpha.tif")
    L, setA, _ = T.layers()
    lc_cats = sorted(np.unique(L["lc_class_cat"]).tolist())
    groups = sorted(set(group_of(f) for f in names))
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    rng = np.random.default_rng(SEED)
    for kind, gdf, key, top in (("catchments", bas, "HYBAS_ID", TOP_C), ("districts", dist, "NAME_2", TOP_D)):
        ids = ids_of(gdf)
        n = len(gdf)
        m = ok & (ids > 0) & np.isfinite(score)
        cnt = np.bincount(ids[m], minlength=n + 1)[1:]
        mean_ai = np.bincount(ids[m], weights=score[m].astype(np.float64), minlength=n + 1)[1:] / np.maximum(cnt, 1)
        mean_A = np.bincount(ids[m], weights=A[m].astype(np.float64), minlength=n + 1)[1:] / np.maximum(cnt, 1)
        # a sample of squares per unit, explained in one batch
        flat_ids = ids.ravel()
        cells = np.flatnonzero(m.ravel())
        unit_of = flat_ids[cells]
        order = rng.permutation(len(cells))
        cells, unit_of = cells[order], unit_of[order]
        keep = pd.Series(unit_of).groupby(unit_of).cumcount().to_numpy() < PER_UNIT
        cells, unit_of = cells[keep], unit_of[keep]
        X = T.frame(L, names, cells)
        X["lc_class_cat"] = X["lc_class_cat"].cat.set_categories(lc_cats)
        contrib = model.predict(X, pred_contrib=True)[:, :-1]          # last column is the bias
        gsum = np.zeros((len(cells), len(groups)))
        for j, f in enumerate(names):
            gsum[:, groups.index(group_of(f))] += contrib[:, j]
        g_unit = np.zeros((n + 1, len(groups)))
        c_unit = np.bincount(unit_of, minlength=n + 1).astype(float)
        for g in range(len(groups)):
            g_unit[:, g] = np.bincount(unit_of, weights=gsum[:, g], minlength=n + 1)
        g_unit = g_unit[1:] / np.maximum(c_unit[1:, None], 1)
        t = pd.DataFrame({key: gdf[key].values, "ai_score": np.round(mean_ai, 4), "meanA": np.round(mean_A, 1),
                          "squares": cnt})
        t = t[t.squares > 0].copy()
        t["ai_rank"] = t.ai_score.rank(ascending=False, method="min").astype(int)
        t["formula_rank"] = t.meanA.rank(ascending=False, method="min").astype(int)
        hi_ai, hi_f = t.ai_rank <= top, t.formula_rank <= top
        t["agreement"] = np.select([hi_ai & hi_f, hi_ai & ~hi_f, ~hi_ai & hi_f],
                                   ["both high", "AI higher", "formula higher"], "both lower")
        gu = g_unit[t.index]
        t["ai_reason"] = [GROUP_NAMES[groups[int(np.argmax(r))]] if r.max() > 0 else "" for r in gu]
        t["ai_against"] = [GROUP_NAMES[groups[int(np.argmin(r))]] if r.min() < 0 else "" for r in gu]
        for g in range(len(groups)):
            t[f"shap_{groups[g]}"] = np.round(gu[:, g], 3)
        suf = "" if kind == "catchments" else "_districts"
        t.drop(columns=["meanA"]).to_csv(ROOT / "reports" / f"erosion_ai_units_{AOI_NAME}{suf}.csv", index=False)
        print(f"  {kind}: {len(t)} units; agreement {t.agreement.value_counts().to_dict()}; "
              f"top AI reasons {t[t.ai_rank <= top].ai_reason.value_counts().to_dict()}")
        if kind == "districts":
            print(t.sort_values("ai_rank").head(10)[[key, "ai_rank", "formula_rank", "agreement", "ai_reason", "ai_against"]]
                  .to_string(index=False))


if __name__ == "__main__":
    main()
