"""Sanity checks S1-S8 for the erosion recipe (EROSION_PLAN.md, E0.7).

    $env:REGION = "assam"; python scripts/inspect/check_erosion_bars.py

How each check is measured was written down in EROSION_PLAN.md ("Step 6, part 1")
before this script first ran; the pass bars date from 2026-09-29 / R7. A failed bar
means *investigate before showing*, never *adjust until it passes*.

S6 (the live flood forecast) is its own script: scripts/model/check_live_unchanged.py.
S3's ISED comparison and S8 need the national reference maps
(scripts/fetch/fetch_44_erosion_reference.py); without them those parts report
"pending".

Writes reports/erosion_sanity_<region>.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from scipy import ndimage
from scipy.stats import spearmanr

import grid as G
from common import AOI_NAME, BOUNDARIES, HYDROLOGY, INTERIM, ROOT, SOIL_GEOLOGY, WEATHER, outline

warnings.filterwarnings("ignore")

E, TER, FEA = INTERIM / "erosion", INTERIM / "terrain", INTERIM / "features"
HILL_DISTRICTS = {"Karbi Anglong", "West Karbi Anglong", "Dima Hasao"}   # SoI names; same land as GADM's two
NOT_ASSESSED_LC = [50, 70, 80, 90, 95, 100]
TREE = 10
CHANNEL_CELLS = 10_000
RIVER_LAND_M, FLAT_M = 2.0, 10.0
UNIT_MIN_CELLS, TOP_N = 500, 20
GUWAHATI, GAUGE_R = (26.10, 91.59), 7924.29


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def raster_of(polys: gpd.GeoDataFrame) -> np.ndarray:
    g = polys.to_crs(G.CRS)
    return rasterize(((geom, i + 1) for i, geom in enumerate(g.geometry) if geom is not None),
                     out_shape=G.SHAPE, transform=G.TRANSFORM, fill=0, dtype="int32")


def onto_grid(path: Path) -> np.ndarray:
    """Any single-band raster -> the canonical grid (bilinear), NaN outside."""
    dst = np.full(G.SHAPE, np.nan, dtype=np.float32)
    with rasterio.open(path) as s:
        src = s.read(1).astype(np.float32)
        if s.nodata is not None:
            src[src == s.nodata] = np.nan
        reproject(source=src, destination=dst, src_transform=s.transform, src_crs=s.crs,
                  src_nodata=np.nan, dst_transform=G.TRANSFORM, dst_crs=G.CRS,
                  dst_nodata=np.nan, resampling=Resampling.bilinear)
    return dst


def find_tif(folder: Path, *must: str) -> Path | None:
    for p in sorted(folder.rglob("*.tif")):
        if all(m.lower() in p.name.lower() for m in must):
            return p
    return None


def unit_scores(ids, a, ok):
    """Mean of `a` over scored cells per unit id, for units with enough cells."""
    sel = ok & (ids > 0) & np.isfinite(a)
    n = np.bincount(ids[sel], minlength=ids.max() + 1)
    s = np.bincount(ids[sel], weights=a[sel], minlength=ids.max() + 1)
    keep = np.nonzero(n >= UNIT_MIN_CELLS)[0]
    return {int(k): float(s[k] / n[k]) for k in keep}


def top(scores: dict, n=TOP_N) -> list[int]:
    return [k for k, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:n]]


def _split_overlap(uid, ok, main_scores) -> dict:
    """Once the tree split is adopted (Phase 1 E1.1): how many of the top 20
    are also top 20 with one value for all tree land — what the split changed.
    Informational, no bar. Empty before adoption."""
    fac = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    if not fac.get("tree_split", {}).get("adopted"):
        return {}
    avg = unit_scores(uid, rd(E / "erosion_A_treeC_avg_tpha.tif"), ok)
    shared = len(set(top(main_scores)) & set(top(avg)))
    ids = sorted(main_scores)
    rho = spearmanr([main_scores[i] for i in ids], [avg[i] for i in ids]).correlation
    return {"top20_shared_split_vs_tree_class_average": shared,
            "spearman_split_vs_tree_class_average": round(float(rho), 2)}


def main() -> None:
    out: dict = {"region": AOI_NAME, "bars": {}}
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A, A_ired = rd(E / "erosion_A_tpha.tif"), rd(E / "erosion_A_ired_tpha.tif")
    A_lo = rd(E / "erosion_A_treeC_alt_tpha.tif")
    K, C, R, LS = (rd(E / f"erosion_{n}.tif") for n in ("K", "C", "R", "LS"))
    cls = rd(E / "erosion_class.tif")
    lc = rd(FEA / "lc_class_cat.tif")
    hand = rd(TER / "hydro_hand_m.tif")
    acc = rd(TER / "hydro_flowacc_cells.tif")
    slope = rd(TER / "terrain_slope_deg.tif")
    # IRED rain with tree C 0.003: C enters A linearly, so scale tree cells
    A_ired_lo = np.where(lc == TREE, A_ired * (A_lo / np.where(A > 0, A, np.nan)), A_ired)

    dist = gpd.read_file(outline("district"))
    did = raster_of(dist)
    names = list(dist.NAME_2)

    # ---- S1 -----------------------------------------------------------------
    if AOI_NAME == "assam":
        hill_ids = [i + 1 for i, n in enumerate(names) if n in HILL_DISTRICTS]
        hill = np.isin(did, hill_ids) & ok
        plain = (did > 0) & ~np.isin(did, hill_ids) & ok
        s1 = {}
        for k, a in (("main", A), ("ired", A_ired), ("tree_C_0.003", A_lo)):
            h, p = float(np.nanmedian(a[hill])), float(np.nanmedian(a[plain]))
            s1[k] = {"hills_median": round(h, 2), "plains_median": round(p, 2), "ratio": round(h / p, 2)}
        out["bars"]["S1"] = {**s1, "pass": s1["main"]["ratio"] >= 3}

    # ---- S2 -----------------------------------------------------------------
    is_tree = lc == TREE
    other = (lc > 0) & ~is_tree
    fp = np.ones((3, 3), bool)
    edge = ndimage.maximum_filter(is_tree.astype(np.uint8), footprint=fp).astype(bool) & \
           ndimage.maximum_filter(other.astype(np.uint8), footprint=fp).astype(bool)
    flat = ok & (hand < FLAT_M)
    thr = np.nanpercentile(LS[flat], 95)
    topc = flat & (LS >= thr)
    # unguarded LS, rebuilt the same way erosion_factors.py does
    import erosion_factors as EF
    th = np.radians(slope.astype(np.float32))
    LS_raw = np.maximum(EF.l_factor(acc.astype(np.float32), th) * EF.s_mccool(th), 0)
    thr_raw = np.nanpercentile(LS_raw[flat], 95)
    top_raw = flat & (LS_raw >= thr_raw)
    s2 = {"top5_LS_threshold": round(float(thr), 3),
          "edge_share_of_top5_pct": round(100 * float(edge[topc].mean()), 1),
          "edge_share_of_top5_unguarded_pct": round(100 * float(edge[top_raw].mean()), 1),
          "edge_share_of_all_flat_pct": round(100 * float(edge[flat].mean()), 1),
          "tree_share_of_top5_pct": round(100 * float(is_tree[topc].mean()), 1),
          "tree_share_of_top5_unguarded_pct": round(100 * float(is_tree[top_raw].mean()), 1)}
    # Two bars (EROSION_PLAN.md Step 6 part 2): the original <= 25%, set before the
    # base rate was known, and the fair one — top 5% no more edge-heavy than flat
    # land in general. 65% of flat cells are edge cells in Assam, so the first
    # cannot be met even by a map with no artefact; both are reported.
    s2["pass_original_25pct"] = s2["edge_share_of_top5_pct"] <= 25
    s2["pass"] = s2["edge_share_of_top5_pct"] <= s2["edge_share_of_all_flat_pct"]
    out["bars"]["S2"] = s2

    # ---- S3 -----------------------------------------------------------------
    kv, cv = K[inside & np.isfinite(K)], C[ok]
    x, y = Transformer.from_crs(4326, G.CRS, always_xy=True).transform(GUWAHATI[1], GUWAHATI[0])
    r_, c_ = G.xy_to_rowcol(x, y)
    rg = float(R[r_, c_]) if (0 <= r_ < G.NROWS and 0 <= c_ < G.NCOLS and np.isfinite(R[r_, c_])) else None
    s3 = {"K_min": round(float(kv.min()), 4), "K_max": round(float(kv.max()), 4),
          "C_min": float(cv.min()), "C_max": float(cv.max()),
          "R_guwahati_grid": None if rg is None else round(rg),
          "R_guwahati_error_pct": None if rg is None else round(100 * (rg / GAUGE_R - 1), 1)}
    s3["pass"] = (0 <= s3["K_min"] and s3["K_max"] <= 0.08 and 0 <= s3["C_min"] and s3["C_max"] <= 1
                  and (rg is None or abs(rg / GAUGE_R - 1) <= 0.25))
    ised = find_tif(SOIL_GEOLOGY / "ised", "k-factor_india")
    if ised:
        Ki = onto_grid(ised)
        ours, theirs = [], []
        for i in range(1, len(names) + 1):
            m = (did == i) & np.isfinite(K) & np.isfinite(Ki)
            if m.sum() > 100:
                ours.append(float(np.median(K[m]))); theirs.append(float(np.median(Ki[m])))
        s3["ISED"] = {"file": ised.name, "districts": len(ours),
                      "spearman": round(float(spearmanr(ours, theirs).correlation), 2),
                      "median_ratio_ours_over_ised": round(float(np.median(np.array(ours) / np.array(theirs))), 2)}
    else:
        s3["ISED"] = "pending: run fetch_44_erosion_reference.py"
    out["bars"]["S3"] = s3

    # ---- S4 -----------------------------------------------------------------
    summ = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    runs = summ["class_shares_pct_of_assessed"]
    mx = {k: max(v.values()) for k, v in runs.items()}
    main_key = next(k for k in runs if k.startswith("main"))
    out["bars"]["S4"] = {"largest_class_share_pct": mx, "pass": mx[main_key] <= 80}

    # ---- S5 -----------------------------------------------------------------
    na = inside & (np.isin(lc, NOT_ASSESSED_LC) | (acc >= CHANNEL_CELLS) | (hand < RIVER_LAND_M))
    bad = int((na & (cls > 0)).sum())
    out["bars"]["S5"] = {"not_assessed_cells": int(na.sum()), "of_which_given_a_class": bad, "pass": bad == 0}

    # ---- S7 -----------------------------------------------------------------
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    uid = raster_of(bas)
    runs4 = {"inresate_C03": A, "ired_C03": A_ired, "inresate_C003": A_lo, "ired_C003": A_ired_lo}
    sc = {k: unit_scores(uid, a, ok) for k, a in runs4.items()}
    tops = {k: top(v) for k, v in sc.items()}
    shared_r = len(set(tops["inresate_C03"]) & set(tops["ired_C03"]))
    all4 = set.intersection(*(set(v) for v in tops.values()))
    ids_all = sorted(sc["inresate_C03"])
    rho = {k: round(float(spearmanr([sc["inresate_C03"][i] for i in ids_all],
                                    [sc[k][i] for i in ids_all]).correlation), 2)
           for k in runs4 if k != "inresate_C03"}

    def describe(i):
        row = bas.iloc[i - 1]
        m = (uid == i) & ok
        d = np.bincount(did[m], minlength=len(names) + 1)[1:]
        return {"hybas_id": int(row.HYBAS_ID), "district": names[int(np.argmax(d))],
                "scored_km2": round(float(m.sum()) / 100, 1),
                "mean_A_main": round(sc["inresate_C03"][i], 1)}

    out["bars"]["S7"] = {
        "units_counted": len(ids_all),
        "top20_shared_inresate_vs_ired": shared_r,
        "top20_shared_C03_vs_C003": len(set(tops["inresate_C03"]) & set(tops["inresate_C003"])),
        **_split_overlap(uid, ok, sc["inresate_C03"]),
        "top20_in_all_four_runs": len(all4),
        "spearman_all_units_vs_main": rho,
        "robust_units": [describe(i) for i in tops["inresate_C03"] if i in all4],
        "main_top20": [describe(i) for i in tops["inresate_C03"]],
        "pass": shared_r >= 10}

    # ---- S8 -----------------------------------------------------------------
    iwed = find_tif(WEATHER / "erosivity" / "iwed", "psl_india")
    if iwed:
        Wi = onto_grid(iwed)
        ours, ours_ired, theirs, dn = [], [], [], []
        for i in range(1, len(names) + 1):
            m = (did == i) & ok & np.isfinite(Wi)
            if m.sum() > 100:
                ours.append(float(np.nanmean(A[m]))); ours_ired.append(float(np.nanmean(A_ired[m])))
                theirs.append(float(np.nanmean(Wi[m]))); dn.append(names[i - 1])
        s8 = {"file": iwed.name, "districts": len(dn),
              "spearman_main_vs_iwed": round(float(spearmanr(ours, theirs).correlation), 2),
              "spearman_ired_run_vs_iwed": round(float(spearmanr(ours_ired, theirs).correlation), 2),
              "by_district": {n: {"ours": round(a, 1), "ours_ired": round(b, 1), "iwed": round(c, 1)}
                              for n, a, b, c in zip(dn, ours, ours_ired, theirs)}}
        s8["expectation_met"] = s8["spearman_ired_run_vs_iwed"] > s8["spearman_main_vs_iwed"]
        # Why they differ (EROSION_PLAN.md Step 6 part 4): factor by factor, and
        # IWED's LS against true slope — it barely responds to slope.
        tif = iwed.parent
        ours_f = {"R": R, "K": K, "LS": LS, "C": C}
        per = {}
        for k, n in (("R", "R_fac_India"), ("K", "K_fac_India"), ("LS", "LS_fac_India"), ("C", "C_fac_India")):
            W = onto_grid(tif / f"{n}.tif")
            a_, b_ = [], []
            for i in range(1, len(names) + 1):
                m = (did == i) & ok & np.isfinite(W) & np.isfinite(ours_f[k])
                if m.sum() > 100:
                    a_.append(float(ours_f[k][m].mean())); b_.append(float(W[m].mean()))
            mm = ok & np.isfinite(W) & np.isfinite(ours_f[k])
            per[k] = {"spearman_districts": round(float(spearmanr(a_, b_).correlation), 2),
                      "median_ours": round(float(np.median(ours_f[k][mm])), 4),
                      "median_iwed": round(float(np.median(W[mm])), 4)}
            if k == "LS":
                LSw = W
        s8["per_factor"] = per
        bands = {}
        for lo, hi in ((0, 0.5), (0.5, 1), (1, 2), (2, 5), (5, 15), (15, 30), (30, 90)):
            m = ok & (slope >= lo) & (slope < hi) & np.isfinite(LSw)
            if m.sum() > 1000:
                bands[f"{lo}-{hi} deg"] = {"share_pct": round(100 * float(m.sum()) / int(ok.sum()), 1),
                                           "LS_ours": round(float(np.median(LS[m])), 2),
                                           "LS_iwed": round(float(np.median(LSw[m])), 2)}
        s8["LS_by_true_slope_median"] = bands
    else:
        s8 = "pending: run fetch_44_erosion_reference.py"
    out["bars"]["S8"] = s8

    dest = ROOT / "reports" / f"erosion_sanity_{AOI_NAME}.json"
    dest.write_text(json.dumps(out, indent=2))
    for k, v in out["bars"].items():
        if isinstance(v, dict):
            flag = {True: "PASS", False: "FAIL"}.get(v.get("pass"), "logged")
            brief = {kk: vv for kk, vv in v.items() if kk not in ("robust_units", "main_top20", "by_district", "pass")}
            print(f"  {k} {flag:6} {json.dumps(brief)}")
        else:
            print(f"  {k} {v}")
    print(f"  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
