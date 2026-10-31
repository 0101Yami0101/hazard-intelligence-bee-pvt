"""Export the soil-erosion results to the app's bundle (webapp/assets/erosion/<region>/).

    $env:REGION = "assam"; python scripts/run/export_erosion_bundle.py

The app runs on numpy, pandas and folium alone (webapp/DEPLOY.md), so everything
it needs is written here as small plain files:

    classes.npz        class rasters (0 not scored, 1 slight .. 6 very severe) for
                       the three runs shown — main, other rain map (IRED), lower
                       forest cover value — reprojected to web-map coordinates
                       (EPSG:3857, ~300 m), plus their lat/lon bounds; also the
                       AI map's five bands ("ai") and soil reaching a stream ("deliv")
    catchments.geojson all ranked catchments, simplified, with rank, score, cause
                       and robustness mark (from erosion_priority.py)
    districts.geojson  district outlines with the district table's columns
    outline.geojson    the state outline
    field_points.csv   the field kit's visit list: the worst squares of each
                       top-20 catchment, with empty columns for what is found
    soilsense_<region>.gpkg  catchments, districts and field points in one
                       GeoPackage for the department's GIS (EPSG:4326)
    meta.json          figures for the page: shares, checks, settings, dates

Reads the outputs of erosion_factors.py, erosion_priority.py and
check_erosion_bars.py; run those first.
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import calculate_default_transform, reproject, transform_bounds

import grid as G
from common import AOI_NAME, AOI_STATE, BOUNDARIES, INTERIM, PROCESSED, ROOT, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
OUT = ROOT / "webapp" / "assets" / "erosion" / AOI_NAME
WEB_RES = 300.0              # metres in EPSG:3857 (about 270 m on the ground at 26 N)
SIMPLIFY_M = 150.0
EDGES = [5, 10, 20, 40, 80]
CLASS_NAMES = ["slight", "moderate", "high", "very high", "severe", "very severe"]
# Field kit, first version (EROSION_PLAN.md, "Field kit"): in each top-20
# catchment, the POINTS_PER scored squares with the highest estimated loss,
# each at least POINT_GAP_M from those already picked, so a team sees the
# worst ground spread over the catchment rather than one hillside five times.
FIELD_TOP, POINTS_PER, POINT_GAP_M = 20, 5, 500.0
FIELD_COLUMNS = ["visited_date", "observer", "rills_seen", "gullies_seen", "bare_soil_pct",
                 "fresh_clearing", "existing_works", "photo_ids", "notes"]


def classify(a: np.ndarray, ok: np.ndarray) -> np.ndarray:
    c = np.digitize(a, EDGES).astype(np.uint8) + 1
    c[~ok | ~np.isfinite(a)] = 0
    return c


def to_web(cls: np.ndarray, resampling=Resampling.mode):
    tr, w, h = calculate_default_transform(G.CRS, "EPSG:3857", G.NCOLS, G.NROWS,
                                           *G.BOUNDS, resolution=WEB_RES)
    dst = np.zeros((h, w), dtype=np.uint8)
    reproject(source=cls, destination=dst, src_transform=G.TRANSFORM, src_crs=G.CRS,
              src_nodata=0, dst_transform=tr, dst_crs="EPSG:3857", dst_nodata=0,
              resampling=resampling)
    left, top = tr.c, tr.f
    right, bottom = left + w * tr.a, top + h * tr.e
    w4, s4, e4, n4 = transform_bounds("EPSG:3857", "EPSG:4326", left, bottom, right, top)
    return dst, [[s4, w4], [n4, e4]]


def slim(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    g = gdf.to_crs(G.CRS)
    g["geometry"] = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
    return g.to_crs(4326)


def write_geojson(gdf: gpd.GeoDataFrame, path: Path) -> None:
    gj = json.loads(gdf.to_json(drop_id=True))
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    for f in gj["features"]:
        f["geometry"]["coordinates"] = rnd(f["geometry"]["coordinates"])
    path.write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")


def _split_summary() -> dict:
    """The adopted tree split's headline figures, for the method page."""
    r = json.loads((ROOT / "reports" / f"tree_split_{AOI_NAME}.json").read_text())
    return {"adopted": True, "T_low": r["T_low"], "P1": r["P1_test_balanced_accuracy"],
            "P2": {k: {kk: v.get(kk) for kk in ("n", "share", "bar", "pass")}
                   for k, v in r.get("P2_eyecheck", {}).items()},
            "share_of_tree_pct": r["share_of_tree_pct"],
            "mean_C_tree": r["P3_mean_C_all_tree"],
            "outlines": {"tea": r["references"]["tea_outlines"],
                         "forest": r["references"]["forest_outlines"]}}


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


AI_PCTL = [50, 75, 90, 97]          # the AI map's five bands: by share of scored land


def _ai_layer(ok, arrays) -> dict | None:
    """AD-01: the AI score as five bands by percentile of scored land (a relative index)."""
    f, rep_p = E / "erosion_ai_score.tif", ROOT / "reports" / f"erosion_ai_{AOI_NAME}.json"
    if not (f.exists() and rep_p.exists()):
        return None
    r = json.loads(rep_p.read_text())
    if not r.get("ships"):
        return {"ships": False}
    sc = rd(f)
    v = sc[ok & np.isfinite(sc)]
    edges = np.percentile(v, AI_PCTL)
    cls = np.digitize(sc, edges).astype(np.uint8) + 1
    cls[~ok | ~np.isfinite(sc)] = 0
    arrays["ai"], _ = to_web(cls)
    meta = {"ships": True, "pctl": AI_PCTL, "auc": r["AI-1_auc_same_cells"], "catchment_rho": r["AI-2_catchment_spearman"],
            "folds": r["auc_per_fold"]["A"], "top_inputs": list(r["importance_gain_pct"]["A"].items())[:6]}
    eye = ROOT / "reports" / f"erosion_eyecheck_{AOI_NAME}.json"      # AD-05, the blind picture check
    if eye.exists():
        e = json.loads(eye.read_text())
        meta["eyecheck"] = {"pictures": sum(e["labels"].values()), "yes": e["labels"].get("erosion", 0) + e["labels"].get("gully", 0),
                            "auc_formula": e["P-cmp"]["auc_formula"], "auc_ai": e["P-cmp"]["auc_ai"],
                            "formula_ratio": e["P-F"]["ratio"], "ai_ratio": e["P-AI"]["ratio"],
                            "ai_top": e["P-AI"]["top10"]["share_readable"], "ai_low": e["P-AI"]["lower_half"]["share_readable"]}
    return meta


DELIV_EDGES = [0.5, 1, 2, 5]        # t/ha/yr reaching a stream: the five map bands (AD-25)


def _delivered_layer(ok, arrays) -> dict | None:
    """AD-25: soil estimated to reach a stream (Borselli connectivity, InVEST delivery ratio)."""
    f, sdr_f = E / "erosion_delivered_tpha.tif", E / "erosion_sdr.tif"
    if not f.exists():
        return None
    d, A, sdr = rd(f), rd(E / "erosion_A_tpha.tif"), rd(sdr_f)
    m = ok & np.isfinite(d)
    cls = np.digitize(d, DELIV_EDGES).astype(np.uint8) + 1
    cls[~m] = 0
    arrays["deliv"], _ = to_web(cls)
    loss, dl = float(np.nansum(A[m])), float(np.nansum(d[m]))        # 1 ha squares: t/ha = t
    return {"edges": DELIV_EDGES, "state_loss_mt": round(loss / 1e6, 1), "state_delivered_mt": round(dl / 1e6, 1),
            "share_pct": round(100 * dl / loss, 1),
            "sdr_p10_p50_p90": [round(float(x), 3) for x in np.nanpercentile(sdr[m], [10, 50, 90])],
            "class_share": [round(float((cls[m] == i + 1).mean()), 4) for i in range(5)]}


def _nrsc_summary() -> dict | None:
    """Checks X1-X3 against NRSC's land-degradation map, for the method page."""
    p = ROOT / "reports" / f"nrsc_ld_comparison_{AOI_NAME}.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text())
    pick = lambda k: {"ours": r[k]["ours_main"], "IWED": r[k].get("IWED"), "slope": r[k]["slope_alone"],
                      "bar": r[k]["bar"], "pass": r[k]["pass"]}
    return {"X1": pick("X1_auc_eroded_vs_normal"), "X2": pick("X2_catchments_spearman"),
            "X3": pick("X3_districts_spearman")}


def field_points(cat: gpd.GeoDataFrame, ok: np.ndarray) -> gpd.GeoDataFrame:
    """The visit list: worst squares per top catchment, spread out (FIELD_*)."""
    from rasterio.features import rasterize
    from shapely.geometry import Point
    A = rd(E / "erosion_A_tpha.tif")
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif")
    top = cat[cat.rank_main <= FIELD_TOP].sort_values("rank_main").to_crs(G.CRS)
    ids = rasterize(((g, int(r)) for g, r in zip(top.geometry, top.rank_main)),
                    out_shape=G.SHAPE, transform=G.TRANSFORM, fill=0, dtype="int32")
    rows = []
    for _, u in top.iterrows():
        r, c = np.nonzero((ids == u.rank_main) & ok & np.isfinite(A))
        order = np.argsort(-A[r, c])
        xs, ys = G.centre_xy(r[order], c[order])
        picked = []
        for k in range(len(order)):
            if all((xs[k] - xs[j]) ** 2 + (ys[k] - ys[j]) ** 2 >= POINT_GAP_M ** 2 for j in picked):
                picked.append(k)
                if len(picked) == POINTS_PER:
                    break
        for n, k in enumerate(picked, 1):
            rr, cc = r[order][k], c[order][k]
            a = float(A[rr, cc])
            rows.append({"point_id": f"C{int(u.rank_main):02d}-{n}", "catchment_rank": int(u.rank_main),
                         "catchment_id": int(u.HYBAS_ID), "district": u.district,
                         "est_loss_tpha": round(a), "class": CLASS_NAMES[int(np.digitize(a, EDGES))],
                         "slope_deg": round(float(slope[rr, cc]), 1), "main_cause": u.main_driver,
                         "vs_similar_slopes": u.vs_similar or "", "typical_measures": u.hint,
                         "rank_firmness": u.mark, "geometry": Point(xs[k], ys[k])})
    pts = gpd.GeoDataFrame(rows, crs=G.CRS).to_crs(4326)
    pts.insert(4, "lat", pts.geometry.y.round(5))
    pts.insert(5, "lon", pts.geometry.x.round(5))
    for c in FIELD_COLUMNS:
        pts[c] = ""
    return pts


def to_web_float(a: np.ndarray) -> np.ndarray:
    """A float layer on the grid -> the web grid of to_web(), averaged, NaN kept."""
    tr, w, h = calculate_default_transform(G.CRS, "EPSG:3857", G.NCOLS, G.NROWS,
                                           *G.BOUNDS, resolution=WEB_RES)
    dst = np.full((h, w), np.nan, dtype=np.float32)
    reproject(source=a.astype(np.float32), destination=dst, src_transform=G.TRANSFORM,
              src_crs=G.CRS, src_nodata=np.nan, dst_transform=tr, dst_crs="EPSG:3857",
              dst_nodata=np.nan, resampling=Resampling.average)
    return dst


def wide(gdf: gpd.GeoDataFrame, change: dict | None) -> gpd.GeoDataFrame:
    """The per-year lists as one column per year, for a GIS (GeoPackage has no lists)."""
    if change is None:
        return gdf
    g = gdf.copy()
    for col, years in (("dry_meanA", change["years"]), ("dry_steep_bare", change["years"]),
                       ("dry_eval", change["years"]), ("dry_new_ha", change["years"])):
        if col not in g:
            continue
        for i, y in enumerate(years):
            if col == "dry_new_ha" and not change["flags_shown"]:
                break
            g[f"{col}_{y}"] = [v[i] if isinstance(v, list) else None for v in g[col]]
        g = g.drop(columns=col)
    return g


def change_bundle(ok: np.ndarray, cat: gpd.GeoDataFrame, dist: gpd.GeoDataFrame):
    """The dry-season change layers (cover_change.py), if it has run.

    change.npz: bare share of scored land per dry season, percent (255 = no data or
    too cloudy), and the steep-slope flags per year (1 = a flagged square inside the
    web pixel), on the class rasters' web grid. Per-unit yearly figures go into the
    catchment and district properties as lists, one value per year."""
    # the latest attempt at the change flags wins (EROSION_PLAN.md, "E1.3 attempt 2")
    suf = "_v2" if (ROOT / "reports" / f"cover_change_{AOI_NAME}_v2.json").exists() else ""
    rep_p = ROOT / "reports" / f"cover_change_{AOI_NAME}{suf}.json"
    if not rep_p.exists():
        return None, cat, dist
    rep = json.loads(rep_p.read_text())
    src = rasterio.open(ROOT / "data" / "raw" / "04_landcover" / "ee_dry_season"
                        / f"dry_season_cover_{AOI_NAME}.tif")
    names = list(src.descriptions)
    years = sorted(int(n.split("_")[1]) for n in names if n.startswith("bare_"))
    arrays = {}
    for y in years:
        v = src.read(names.index(f"valid_{y}") + 1)
        b = src.read(names.index(f"bare_{y}") + 1).astype(np.float32) / 250
        b[(v == 255) | (v / 250 < rep["rules"]["valid_min"]) | ~ok] = np.nan
        w = to_web_float(b)
        arrays[f"bare_{y}"] = np.where(np.isfinite(w), np.round(100 * w), 255).astype(np.uint8)
    with rasterio.open(E / f"cover_flags{suf}.tif") as s:
        fyears = [int(t) for t in s.descriptions]
        for i, y in enumerate(fyears):
            if not rep["flags_shown"]:
                break
            f = (s.read(i + 1) == 1).astype(np.uint8)
            arrays[f"flag_{y}"], _ = to_web(f, Resampling.max)   # any flagged square shows
    np.savez_compressed(OUT / "change.npz", **arrays)

    for gdf, key, csv in ((cat, "HYBAS_ID", "catchments"), (dist, "district", "districts")):
        t = pd.read_csv(ROOT / "reports" / f"cover_change_{AOI_NAME}{suf}_{csv}.csv")
        t = t.sort_values("year")
        g = t.groupby(key)
        lists = pd.DataFrame({
            "dry_meanA": g.meanA_dry.apply(lambda s: [None if pd.isna(x) else round(float(x), 1) for x in s]),
            "dry_steep_bare": g.steep_bare_pct.apply(lambda s: [None if pd.isna(x) else round(float(x), 1) for x in s]),
            "dry_eval": g.evaluable_pct.apply(lambda s: [None if pd.isna(x) else round(float(x)) for x in s]),
            "dry_new_ha": g.new_bare_steep_ha.apply(lambda s: [None if pd.isna(x) else int(x) for x in s]),
            "dry_steep_km2": g.steep_scored_km2.first().round(1),
        }).reset_index()
        if not rep["flags_shown"]:         # flags held back by their own tests: ship no counts
            lists = lists.drop(columns="dry_new_ha")
        merged = gdf.merge(lists, on=key, how="left")
        if csv == "catchments":
            cat = merged
        else:
            dist = merged
    keep = ("F1_stable_forest", "F2_tea", "H1_hansen_clearing")
    meta = {"years": years, "flag_years": fyears, "rules": rep["rules"],
            "attempt": rep.get("attempt", 1), "drop_min": rep.get("drop_min"),
            "tests": {k: {kk: rep[k][kk] for kk in ("rate", "bar", "pass", "flagged", "cell_years",
                                                   "cells", "cell_events", "caught") if kk in rep[k]}
                      for k in keep},
            "E3": rep.get("E3_eyecheck"), "flags_shown": rep["flags_shown"],
            "yearly": rep["yearly"], "meanA_main": rep["meanA_main_tpha"]}
    return meta, cat, dist


def main() -> None:
    print(f"Export erosion bundle — {AOI_NAME}")
    OUT.mkdir(parents=True, exist_ok=True)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    runs = {"main": "erosion_A_tpha.tif", "ired": "erosion_A_ired_tpha.tif",
            "treeC_alt": "erosion_A_treeC_alt_tpha.tif"}
    fac0 = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    split_on = bool(fac0.get("tree_split", {}).get("adopted"))
    measured_on = bool(fac0.get("measured_cover", {}).get("adopted"))
    if split_on or measured_on:                       # Phase 1 E1.1: what the split changed
        runs["treeC_avg"] = "erosion_A_treeC_avg_tpha.tif"
    arrays, bounds = {}, None
    for k, f in runs.items():
        arrays[k], bounds = to_web(classify(rd(E / f), ok))
    ai_meta = _ai_layer(ok, arrays)
    deliv_meta = _delivered_layer(ok, arrays)
    np.savez_compressed(OUT / "classes.npz", bounds=np.array(bounds), **arrays)

    cat = gpd.read_file(PROCESSED / "erosion_priority.gpkg", layer="catchments")
    keep = ["HYBAS_ID", "district", "rank_main", "rank_ired", "rank_treeC_alt", "rank_ired_treeC_alt",
            "meanA_main", "meanA_ired", "meanA_treeC_alt", "high_or_worse_pct", "scored_km2",
            "total_t_per_yr", "not_scored_pct", "main_driver", "also", "vs_similar", "vs_similar_x",
            "hint", "mark"]
    keep += [c for c in ("rank_treeC_avg", "meanA_treeC_avg") if c in cat.columns]
    # V-17 part 2: how often each unit is top 20 across 1,000 runs of the unsettled inputs
    stab = ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}.csv"
    if stab.exists() and "top20_pct" not in cat.columns:
        cat = cat.merge(pd.read_csv(stab), on="HYBAS_ID", how="left")
    keep += [c for c in ("top20_pct", "top50_pct", "rank_median", "rank_p05", "rank_p95", "robust")
             if c in cat.columns]
    ai_u = ROOT / "reports" / f"erosion_ai_units_{AOI_NAME}.csv"
    if ai_u.exists() and "ai_rank" not in cat.columns:
        cat = cat.merge(pd.read_csv(ai_u)[["HYBAS_ID", "ai_score", "ai_rank", "agreement", "ai_reason", "ai_against"]],
                        on="HYBAS_ID", how="left")
    keep += [c for c in ("ai_score", "ai_rank", "agreement", "ai_reason", "ai_against") if c in cat.columns]
    DCOLS = ["delivered_tpha", "delivered_share_pct", "rank_delivered"]
    con = ROOT / "reports" / f"erosion_connectivity_{AOI_NAME}.csv"
    if con.exists() and "rank_delivered" not in cat.columns:
        cat = cat.merge(pd.read_csv(con)[["HYBAS_ID"] + DCOLS], on="HYBAS_ID", how="left")
    keep += [c for c in DCOLS if c in cat.columns]
    VCOLS = ["N_kg_per_ha", "N_gkg", "urea_bags_per_ha", "urea_rs_per_ha", "topsoil_mm_per_yr"]   # AD-29
    val = ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}.csv"
    if val.exists() and "N_kg_per_ha" not in cat.columns:
        cat = cat.merge(pd.read_csv(val)[["HYBAS_ID"] + VCOLS], on="HYBAS_ID", how="left")
    keep += [c for c in VCOLS if c in cat.columns]
    cat = cat[keep + ["geometry"]].copy()
    for c in ("meanA_main", "meanA_ired", "meanA_treeC_alt", "meanA_treeC_avg", "high_or_worse_pct",
              "scored_km2", "not_scored_pct"):
        if c in cat.columns:
            cat[c] = cat[c].round(1)
    cat["total_t_per_yr"] = cat["total_t_per_yr"].round(-2)
    cat["vs_similar_x"] = cat["vs_similar_x"].round(1)
    for c in ("also", "vs_similar", "hint", "mark") + tuple(c for c in ("agreement", "ai_reason", "ai_against")
                                                       if c in cat.columns):
        cat[c] = cat[c].fillna("")
    pts = field_points(cat, ok)
    pts.drop(columns="geometry").to_csv(OUT / "field_points.csv", index=False)

    dist = gpd.read_file(outline("district"))
    dt = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}_districts.csv")
    dist = dist[["NAME_2", "geometry"]].rename(columns={"NAME_2": "district"}).merge(dt, on="district")
    ai_d = ROOT / "reports" / f"erosion_ai_units_{AOI_NAME}_districts.csv"
    if ai_d.exists():
        dist = dist.merge(pd.read_csv(ai_d).rename(columns={"NAME_2": "district"})[
            ["district", "ai_rank", "agreement", "ai_reason", "ai_against"]], on="district", how="left")
    con_d = ROOT / "reports" / f"erosion_connectivity_{AOI_NAME}_districts.csv"
    if con_d.exists():
        dist = dist.merge(pd.read_csv(con_d).rename(columns={"NAME_2": "district"})[["district"] + DCOLS],
                          on="district", how="left")
    val_d = ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}_districts.csv"
    if val_d.exists():
        dist = dist.merge(pd.read_csv(val_d).rename(columns={"NAME_2": "district"})[["district"] + VCOLS],
                          on="district", how="left")
    dist = dist[["district", "rank_main", "rank_ired", "rank_treeC_alt"]
                + [c for c in ("rank_treeC_avg",) if c in dist.columns]
                + ["meanA_main", "high_or_worse_pct", "scored_km2", "total_t_per_yr",
                   "not_scored_pct", "main_driver", "also", "vs_similar", "vs_similar_x", "hint"]
                + [c for c in ("top20_pct", "rank_median", "rank_p05", "rank_p95", "ai_rank", "agreement",
                               "ai_reason", "ai_against", *DCOLS, *VCOLS) if c in dist.columns]
                + ["geometry"]]
    for c in ("meanA_main", "high_or_worse_pct", "scored_km2", "not_scored_pct", "vs_similar_x"):
        dist[c] = dist[c].round(1)
    for c in ("also", "vs_similar", "hint") + tuple(c for c in ("agreement", "ai_reason", "ai_against")
                                                     if c in dist.columns):
        dist[c] = dist[c].fillna("")
    change, cat, dist = change_bundle(ok, cat, dist)
    write_geojson(slim(cat), OUT / "catchments.geojson")
    write_geojson(slim(dist), OUT / "districts.geojson")
    gpkg = OUT / f"soilsense_{AOI_NAME}.gpkg"
    gpkg.unlink(missing_ok=True)
    slim(wide(cat, change)).to_file(gpkg, layer="catchments", driver="GPKG")
    slim(wide(dist, change)).to_file(gpkg, layer="districts", driver="GPKG")
    pts.to_file(gpkg, layer="field_points", driver="GPKG")
    state = gpd.read_file(outline("state"))[["geometry"]]
    write_geojson(slim(state), OUT / "outline.geojson")

    fac = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    san = json.loads((ROOT / "reports" / f"erosion_sanity_{AOI_NAME}.json").read_text())["bars"]
    w, s, e, n = state.to_crs(4326).total_bounds
    shares = fac["class_shares_pct_of_assessed"]
    main_key = next(k for k in shares if k.startswith("main"))
    meta = {
        "region": AOI_NAME, "state": AOI_STATE,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bounds": [[float(s), float(w)], [float(n), float(e)]],
        "center": [float((s + n) / 2), float((w + e) / 2)],
        "scored_pct": fac["assessed_pct_of_state"],
        "not_scored_pct": fac["not_assessed_pct_of_state"],
        "mean_A": fac["A_mean_tpha"],
        "median_A": fac["factors_on_assessed_land"]["A_tpha"]["p50"],
        "shares": {"main": shares[main_key], "ired": shares["IRED rain"],
                   "treeC_alt": next(v for k, v in shares.items() if k.startswith("tree C")),
                   **({"treeC_avg": next(v for k, v in shares.items() if k.startswith("tree class average"))}
                      if split_on or measured_on else {})},
        "settings": fac["settings"],
        "checks": {k: ({kk: vv for kk, vv in v.items()
                        if kk not in ("robust_units", "main_top20", "by_district")}
                       if isinstance(v, dict) else v) for k, v in san.items()},
        "n_catchments": int(len(cat)),
        "n_top_both": int((cat.mark == "top under both rain maps").sum()),
        "stability": (json.loads((ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}.json").read_text())
                      if (ROOT / "reports" / f"erosion_rank_stability_{AOI_NAME}.json").exists() else None),
        "field_kit": {"top": FIELD_TOP, "points_per": POINTS_PER, "gap_m": POINT_GAP_M,
                      "n_points": int(len(pts)), "columns": FIELD_COLUMNS},
        "tree_split": _split_summary() if split_on else {"adopted": False},
        "measured_cover": {"adopted": measured_on},
        "change": change,
        "nrsc": _nrsc_summary(),
        "ai": ai_meta,
        "delivered": deliv_meta,
        "soil_value": (json.loads((ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}.json").read_text())
                       if (ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}.json").exists() else None),
        "outlook_grade": (json.loads((ROOT / "reports" / f"outlook_replay_{AOI_NAME}.json").read_text())
                          if (ROOT / "reports" / f"outlook_replay_{AOI_NAME}.json").exists() else None),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    size = sum(p.stat().st_size for p in OUT.iterdir()) / 1e6
    print(f"  wrote {OUT.relative_to(ROOT)}: {', '.join(p.name for p in sorted(OUT.iterdir()))}  "
          f"({size:.2f} MB); class raster {arrays['main'].shape}")


if __name__ == "__main__":
    main()
