"""AD-01: an AI erosion map learned from ISRO's eroded-land map (NRSC LD 1:50k, 2015-16).

    $env:REGION = "assam"; python scripts/model/train_erosion_ai.py          # folds, OOF, tests
    $env:REGION = "assam"; python scripts/model/train_erosion_ai.py --full   # + the app's full model and map

The test and its bars were written down before this script first ran
(docs/design/EROSION_PLAN.md, "AD-01 part 1"):

    cells     scored by the recipe; eroded = NRSC 2-7, normal = NRSC 8 (0, 1, 9 left out)
    inputs    set A (lead, nothing newer than ~2021) and set B (A + Hansen loss, dry-season bare)
    model     LightGBM, SlideSense's settings; per training fold every eroded cell + 3 normal
              per eroded (seed 42); frozen 50 km folds; out-of-fold (OOF) scores
    AI-1      OOF AUC >= 0.70 and >= 0.03 above the formula's A and slope alone, same cells
    AI-2      catchments (>= 100 mapped cells): Spearman of mean OOF score vs NRSC water-erosion
              share (codes 1-7) >= 0.40

Like SlideSense, the score is a relative index learned from a 1:3 sample: it ranks places;
it is not a chance of erosion.

Outputs: models/erosion_ai/<region>/fold{k}_{A,B}.txt, full_A.txt
         reports/erosion_ai_<region>.json, data/processed/<region>/erosion_ai_oof.parquet
         data/interim/<region>/erosion/erosion_ai_score.tif (with --full)
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inspect"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from scipy.stats import spearmanr

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, LANDCOVER, PROCESSED, ROOT

warnings.filterwarnings("ignore")

E, TER, FEA = INTERIM / "erosion", INTERIM / "terrain", INTERIM / "features"
MODELS = ROOT / "models" / "erosion_ai" / AOI_NAME
REPORT = ROOT / "reports" / f"erosion_ai_{AOI_NAME}.json"
OOF = PROCESSED / "erosion_ai_oof.parquet"
ERODED, NORMAL, ANY_WATER = (2, 3, 4, 5, 6, 7), 8, (1, 2, 3, 4, 5, 6, 7)
NEG_PER_POS, SEED = 3, 42
BARS = {"AI-1": 0.70, "margin": 0.03, "AI-2": 0.40}
# SlideSense's settings (train_susceptibility.py), unchanged
PARAMS = dict(objective="binary", n_estimators=600, learning_rate=0.05, num_leaves=63,
              min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
              reg_lambda=1.0, verbose=-1, n_jobs=-1, random_state=42)


def rd(p, band=1):
    with rasterio.open(p) as s:
        return s.read(band)


def layers() -> tuple[dict, list[str], list[str]]:
    """name -> full-grid array, and the names in sets A and B."""
    L = {}
    for n in ("dem_elev_m", "terrain_slope_deg", "terrain_slope_max_deg", "terrain_relief_m",
              "terrain_curv_plan", "terrain_curv_prof", "terrain_eastness", "terrain_northness",
              "hydro_hand_m", "hydro_twi"):
        L[n] = rd(TER / f"{n}.tif").astype(np.float32)
    L["hydro_flowacc_log"] = np.log1p(rd(TER / "hydro_flowacc_cells.tif").astype(np.float32))
    L["hydro_chan_log"] = np.log1p(np.nan_to_num(rd(TER / "hydro_chan_km2.tif").astype(np.float32)))
    for p, u in (("bdod", "cgcm3"), ("cfvo", "cm3dm3"), ("clay", "gkg"), ("sand", "gkg"),
                 ("silt", "gkg"), ("soc", "dgkg")):
        for d in ("0-5cm", "15-30cm", "60-100cm"):
            L[f"soil_{p}_{d}"] = rd(FEA / f"soil_{p}_{d}_{u}.tif").astype(np.float32)
    L["lc_class_cat"] = rd(FEA / "lc_class_cat.tif").astype(np.int16)
    L["R_inresate"] = rd(E / "erosion_R.tif").astype(np.float32)
    K, LS, C = (rd(E / f"erosion_{f}.tif").astype(np.float32) for f in ("K", "LS", "C"))
    with np.errstate(invalid="ignore", divide="ignore"):
        L["R_ired"] = rd(E / "erosion_A_ired_tpha.tif").astype(np.float32) / (K * LS * C)
    L["K"], L["LS"], L["C"] = K, LS, C
    ts = LANDCOVER / "ee_tree_split" / f"tree_split_inputs_{AOI_NAME}.tif"
    with rasterio.open(ts) as s:
        names = list(s.descriptions)
        for b, scale in (("low_frac", 250), ("h_mean", 4), ("h_eth", 4), ("fresh_frac", 250), ("recent_frac", 250)):
            a = s.read(names.index(b) + 1).astype(np.float32)
            a[a == 255] = np.nan
            L[f"canopy_{b}" if b in ("low_frac", "h_mean", "h_eth") else f"hansen_{b}"] = a / scale
    with rasterio.open(LANDCOVER / "ee_dry_season" / f"dry_season_cover_{AOI_NAME}.tif") as s:
        names = list(s.descriptions)
        years = sorted(int(n.split("_")[1]) for n in names if n.startswith("bare_"))
        bare, ndvi = [], []
        for y in years:
            v = s.read(names.index(f"valid_{y}") + 1)
            for lst, key in ((bare, "bare"), (ndvi, "ndvi")):
                a = s.read(names.index(f"{key}_{y}") + 1).astype(np.float32) / 250
                a[(v == 255) | (v / 250 < 0.5)] = np.nan
                lst.append(a)
        L["dry_bare_mean"] = np.nanmean(bare, axis=0)
        L["dry_bare_max"] = np.nanmax(bare, axis=0)
        L["dry_ndvi_mean"] = np.nanmean(ndvi, axis=0)
    A = [k for k in L if not k.startswith(("hansen_", "dry_"))]
    B = A + [k for k in L if k.startswith(("hansen_", "dry_"))]
    return L, A, B


def auc(score, pos) -> float:
    from scipy.stats import rankdata
    m = np.isfinite(score)
    s, p = score[m], pos[m]
    r = rankdata(s)
    n1, n0 = int(p.sum()), int((~p).sum())
    return float((r[p].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def frame(L, names, idx) -> pd.DataFrame:
    df = pd.DataFrame({n: L[n].ravel()[idx] for n in names})
    df["lc_class_cat"] = df["lc_class_cat"].astype("category")
    return df


def main(full: bool) -> None:
    t0 = time.time()
    print(f"AD-01 AI erosion map — {AOI_NAME}", flush=True)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    ref = rd(LANDCOVER / "nrsc_ld50k" / f"nrsc_ld50k_1516_{AOI_NAME}.tif")
    elig = ok & (np.isin(ref, ERODED) | (ref == NORMAL))
    idx = np.flatnonzero(elig)
    y = np.isin(ref.ravel()[idx], ERODED)
    rows, cols = np.unravel_index(idx, G.SHAPE)
    folds = pd.read_parquet(INTERIM / "spatial_folds.parquet").set_index("block_id").fold
    fold = folds.reindex(G.fold_block(rows, cols)).fillna(-1).astype(int).to_numpy()
    print(f"  eligible cells {len(idx):,} (eroded {int(y.sum()):,}); per fold "
          f"{np.bincount(fold[fold >= 0]).tolist()}", flush=True)

    L, setA, setB = layers()
    lc_cats = sorted(np.unique(L["lc_class_cat"]).tolist())
    rng = np.random.default_rng(SEED)
    oof = {s: np.full(len(idx), np.nan, np.float32) for s in ("A", "B")}
    per_fold = {"A": [], "B": []}
    MODELS.mkdir(parents=True, exist_ok=True)
    for k in range(5):
        tr = fold != k
        pos = np.flatnonzero(tr & y)
        neg = np.flatnonzero(tr & ~y)
        neg = rng.choice(neg, size=min(len(neg), NEG_PER_POS * len(pos)), replace=False)
        sample = np.concatenate([pos, neg])
        te = np.flatnonzero(fold == k)
        for sname, names in (("A", setA), ("B", setB)):
            X = frame(L, names, idx[sample])
            X["lc_class_cat"] = X["lc_class_cat"].cat.set_categories(lc_cats)
            m = lgb.LGBMClassifier(**PARAMS).fit(X, y[sample])
            m.booster_.save_model(str(MODELS / f"fold{k}_{sname}.txt"))
            Xt = frame(L, names, idx[te])
            Xt["lc_class_cat"] = Xt["lc_class_cat"].cat.set_categories(lc_cats)
            oof[sname][te] = m.predict_proba(Xt)[:, 1]
            per_fold[sname].append(round(auc(oof[sname][te], y[te]), 4))
        print(f"    fold {k}: A {per_fold['A'][-1]}  B {per_fold['B'][-1]}  ({time.time() - t0:.0f}s)", flush=True)

    # ---- AI-1 ---------------------------------------------------------------
    have = np.isfinite(oof["A"]) & np.isfinite(oof["B"])
    A_formula = rd(E / "erosion_A_tpha.tif").ravel()[idx]
    slope = L["terrain_slope_deg"].ravel()[idx]
    same = have & np.isfinite(A_formula) & np.isfinite(slope)
    res = {k: round(auc(v[same], y[same]), 4) for k, v in
           (("ai_A", oof["A"]), ("ai_B", oof["B"]), ("formula", A_formula), ("slope_alone", slope))}
    ai1 = (res["ai_A"] >= BARS["AI-1"] and res["ai_A"] >= res["formula"] + BARS["margin"]
           and res["ai_A"] >= res["slope_alone"] + BARS["margin"])

    # ---- AI-2 ---------------------------------------------------------------
    from erosion_priority import ids_of
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    bid = ids_of(bas)
    mapped = ok & (ref > 0)
    nb = len(bas)
    n_map = np.bincount(bid[mapped], minlength=nb + 1)[1:]
    share = np.bincount(bid[mapped & np.isin(ref, ANY_WATER)], minlength=nb + 1)[1:] / np.maximum(n_map, 1)
    cid = bid.ravel()[idx]
    unit = {}
    for sname in ("A", "B"):
        m = np.isfinite(oof[sname]) & (cid > 0)
        s_ = np.bincount(cid[m], weights=oof[sname][m], minlength=nb + 1)[1:]
        c_ = np.bincount(cid[m], minlength=nb + 1)[1:]
        mean = np.where(c_ > 0, s_ / np.maximum(c_, 1), np.nan)
        keep = (n_map >= 100) & np.isfinite(mean)
        unit[sname] = round(float(spearmanr(mean[keep], share[keep]).correlation), 4)
    A_cat = pri.set_index("HYBAS_ID").meanA_main.reindex(bas.HYBAS_ID).to_numpy()
    keep = (n_map >= 100) & np.isfinite(A_cat)
    unit["formula"] = round(float(spearmanr(A_cat[keep], share[keep]).correlation), 4)
    ai2 = unit["A"] >= BARS["AI-2"]

    # ---- importance (gain), from the fold models ------------------------------
    imp = {}
    for sname in ("A", "B"):
        g = {}
        for k in range(5):
            b = lgb.Booster(model_file=str(MODELS / f"fold{k}_{sname}.txt"))
            for f, v in zip(b.feature_name(), b.feature_importance("gain")):
                g[f] = g.get(f, 0) + v
        tot = sum(g.values())
        imp[sname] = {f: round(100 * v / tot, 1) for f, v in sorted(g.items(), key=lambda x: -x[1])[:12]}

    pd.DataFrame({"cell": idx.astype(np.int64), "fold": fold, "eroded": y,
                  "oof_A": oof["A"], "oof_B": oof["B"]}).to_parquet(OOF)
    rep = {"region": AOI_NAME, "eligible_cells": int(len(idx)), "eroded_cells": int(y.sum()),
           "features": {"A": setA, "B": setB}, "params": PARAMS, "neg_per_pos": NEG_PER_POS,
           "AI-1_auc_same_cells": res, "AI-1_cells": int(same.sum()), "auc_per_fold": per_fold,
           "AI-2_catchment_spearman": unit, "AI-2_units": int(keep.sum()),
           "importance_gain_pct": imp, "bars": BARS,
           "AI-1_pass": bool(ai1), "AI-2_pass": bool(ai2), "ships": bool(ai1 and ai2),
           "seconds": round(time.time() - t0)}
    REPORT.write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: rep[k] for k in ("AI-1_auc_same_cells", "auc_per_fold", "AI-2_catchment_spearman",
                                          "AI-1_pass", "AI-2_pass", "ships")}, indent=1))
    print("  top inputs A:", list(imp["A"].items())[:8])
    print("  top inputs B:", list(imp["B"].items())[:8])

    if full:
        full_model(L, setA, idx, y, ok, lc_cats, rng)


def full_model(L, names, idx, y, ok, lc_cats, rng) -> None:
    """The app's model: every eroded cell + 3 normal per eroded from ALL folds; scores every
    scored cell. Never quoted as a skill number (that is the OOF's job)."""
    pos = np.flatnonzero(y)
    neg = rng.choice(np.flatnonzero(~y), size=min(int((~y).sum()), NEG_PER_POS * len(pos)), replace=False)
    sample = np.concatenate([pos, neg])
    X = frame(L, names, idx[sample])
    X["lc_class_cat"] = X["lc_class_cat"].cat.set_categories(lc_cats)
    m = lgb.LGBMClassifier(**PARAMS).fit(X, y[sample])
    m.booster_.save_model(str(MODELS / "full_A.txt"))
    out = np.full(G.SHAPE[0] * G.SHAPE[1], np.nan, np.float32)
    cells = np.flatnonzero(ok)
    for i in range(0, len(cells), 1_000_000):
        c = cells[i:i + 1_000_000]
        Xc = frame(L, names, c)
        Xc["lc_class_cat"] = Xc["lc_class_cat"].cat.set_categories(lc_cats)
        out[c] = m.predict_proba(Xc)[:, 1]
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="float32", crs=G.CRS,
                transform=G.TRANSFORM, nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(E / "erosion_ai_score.tif", "w", **prof) as d:
        d.write(out.reshape(G.SHAPE), 1)
    print(f"  full model + map written ({E / 'erosion_ai_score.tif'})")


if __name__ == "__main__":
    main("--full" in sys.argv)
