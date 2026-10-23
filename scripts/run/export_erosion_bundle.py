"""Export the soil-erosion results to the app's bundle (webapp/assets/erosion/<region>/).

    $env:REGION = "assam"; python scripts/run/export_erosion_bundle.py

The app runs on numpy, pandas and folium alone (webapp/DEPLOY.md), so everything
it needs is written here as small plain files:

    classes.npz        class rasters (0 not scored, 1 slight .. 6 very severe) for
                       the three runs shown — main, other rain map (IRED), lower
                       forest cover value — reprojected to web-map coordinates
                       (EPSG:3857, ~300 m), plus their lat/lon bounds
    catchments.geojson all ranked catchments, simplified, with rank, score, cause
                       and robustness mark (from erosion_priority.py)
    districts.geojson  district outlines with the district table's columns
    outline.geojson    the state outline
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


def classify(a: np.ndarray, ok: np.ndarray) -> np.ndarray:
    c = np.digitize(a, EDGES).astype(np.uint8) + 1
    c[~ok | ~np.isfinite(a)] = 0
    return c


def to_web(cls: np.ndarray):
    tr, w, h = calculate_default_transform(G.CRS, "EPSG:3857", G.NCOLS, G.NROWS,
                                           *G.BOUNDS, resolution=WEB_RES)
    dst = np.zeros((h, w), dtype=np.uint8)
    reproject(source=cls, destination=dst, src_transform=G.TRANSFORM, src_crs=G.CRS,
              src_nodata=0, dst_transform=tr, dst_crs="EPSG:3857", dst_nodata=0,
              resampling=Resampling.mode)
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


def main() -> None:
    print(f"Export erosion bundle — {AOI_NAME}")
    OUT.mkdir(parents=True, exist_ok=True)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    runs = {"main": "erosion_A_tpha.tif", "ired": "erosion_A_ired_tpha.tif",
            "treeC_alt": "erosion_A_treeC_alt_tpha.tif"}
    fac0 = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    split_on = bool(fac0.get("tree_split", {}).get("adopted"))
    if split_on:                       # Phase 1 E1.1: what the split changed
        runs["treeC_avg"] = "erosion_A_treeC_avg_tpha.tif"
    arrays, bounds = {}, None
    for k, f in runs.items():
        arrays[k], bounds = to_web(classify(rd(E / f), ok))
    np.savez_compressed(OUT / "classes.npz", bounds=np.array(bounds), **arrays)

    cat = gpd.read_file(PROCESSED / "erosion_priority.gpkg", layer="catchments")
    keep = ["HYBAS_ID", "district", "rank_main", "rank_ired", "rank_treeC_alt", "rank_ired_treeC_alt",
            "meanA_main", "meanA_ired", "meanA_treeC_alt", "high_or_worse_pct", "scored_km2",
            "total_t_per_yr", "not_scored_pct", "main_driver", "also", "mark"]
    keep += [c for c in ("rank_treeC_avg", "meanA_treeC_avg") if c in cat.columns]
    cat = cat[keep + ["geometry"]].copy()
    for c in ("meanA_main", "meanA_ired", "meanA_treeC_alt", "meanA_treeC_avg", "high_or_worse_pct",
              "scored_km2", "not_scored_pct"):
        if c in cat.columns:
            cat[c] = cat[c].round(1)
    cat["total_t_per_yr"] = cat["total_t_per_yr"].round(-2)
    write_geojson(slim(cat), OUT / "catchments.geojson")

    dist = gpd.read_file(outline("district"))
    dt = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}_districts.csv")
    dist = dist[["NAME_2", "geometry"]].rename(columns={"NAME_2": "district"}).merge(dt, on="district")
    dist = dist[["district", "rank_main", "rank_ired", "rank_treeC_alt"]
                + [c for c in ("rank_treeC_avg",) if c in dist.columns]
                + ["meanA_main", "high_or_worse_pct", "scored_km2", "total_t_per_yr",
                   "not_scored_pct", "main_driver", "also", "geometry"]]
    for c in ("meanA_main", "high_or_worse_pct", "scored_km2", "not_scored_pct"):
        dist[c] = dist[c].round(1)
    write_geojson(slim(dist), OUT / "districts.geojson")
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
                      if split_on else {})},
        "settings": fac["settings"],
        "checks": {k: ({kk: vv for kk, vv in v.items()
                        if kk not in ("robust_units", "main_top20", "by_district")}
                       if isinstance(v, dict) else v) for k, v in san.items()},
        "n_catchments": int(len(cat)),
        "n_top_both": int((cat.mark == "top under both rain maps").sum()),
        "tree_split": _split_summary() if split_on else {"adopted": False},
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    size = sum(p.stat().st_size for p in OUT.iterdir()) / 1e6
    print(f"  wrote {OUT.relative_to(ROOT)}: {', '.join(p.name for p in sorted(OUT.iterdir()))}  "
          f"({size:.2f} MB); class raster {arrays['main'].shape}")


if __name__ == "__main__":
    main()
