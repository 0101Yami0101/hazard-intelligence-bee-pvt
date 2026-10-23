"""Split WorldCover "tree" into cleared / regrowing / low canopy / tall canopy (E1.1).

    $env:REGION = "assam"; python scripts/build/tree_split.py            # calibrate, test, map
    $env:REGION = "assam"; python scripts/build/tree_split.py --eyecheck # + blind image sample
    $env:REGION = "assam"; python scripts/build/tree_split.py --score labels.csv   # P2 + adoption

Every rule and pass bar was written down before this script first ran
(docs/design/EROSION_PLAN.md, "Phase 1, E1.1 part 1" and its clarifications):

    T1 freshly cleared   fresh_frac  >= 0.25   C 0.34
    T2 regrowing         recent_frac >= 0.25   C 0.10
    T3 low canopy        low_frac    >= T_low  C 0.18   (tea, bush, young bamboo)
    T4 tall canopy       otherwise             C 0.003  (forest)
    T0 no height data    (not T1/T2)           C 0.03   (the D8 class average)

T_low is chosen on the CALIBRATION half of the OpenStreetMap reference outlines
(tea gardens vs reserve forests; halves drawn per outline, seed 42) and then
judged once on the TEST half: P1 = balanced accuracy >= 0.80.

--eyecheck writes 25 random scored tree cells per sub-class T1-T4 as satellite
pictures with NEUTRAL ids only, plus a separate key file. The pictures are
labelled by eye before the key is opened (P2).

Inputs: data/raw/04_landcover/ee_tree_split/tree_split_inputs_<region>.tif
        (scripts/fetch/fetch_43_tree_split_inputs.py) and the OSM outlines
        (scripts/fetch/fetch_45_osm_landuse_reference.py).
Outputs: data/interim/<region>/features/tree_subclass.tif (0 not tree, 1-4 = T1-T4, 5 = T0)
         reports/tree_split_<region>.json
         data/interim/<region>/erosion/eyecheck_tree/ (pictures, sheets, key)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import rasterio
from rasterio.features import rasterize
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import linemerge, polygonize, unary_union

import grid as G
from common import AOI_NAME, INTERIM, LANDCOVER, ROOT, UA

warnings.filterwarnings("ignore")

TREE = 10
FRESH_MIN, RECENT_MIN = 0.25, 0.25
C_SUB = {1: 0.34, 2: 0.10, 3: 0.18, 4: 0.003, 5: 0.03}
NAMES = {1: "T1 freshly cleared", 2: "T2 regrowing", 3: "T3 low canopy",
         4: "T4 tall canopy", 5: "T0 no height data"}
P1_BAR = 0.80
SEED = 42
INPUTS = LANDCOVER / "ee_tree_split" / f"tree_split_inputs_{AOI_NAME}.tif"
OSM = LANDCOVER / "osm_reference"
OUT_RASTER = INTERIM / "features" / "tree_subclass.tif"
REPORT = ROOT / "reports" / f"tree_split_{AOI_NAME}.json"
EYE = INTERIM / "erosion" / "eyecheck_tree"


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def outline(el) -> Polygon | None:
    """An Overpass `out geom` element -> a polygon in lon/lat, or None."""
    if el["type"] == "way":
        pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
        if len(pts) >= 4 and pts[0] == pts[-1]:
            g = Polygon(pts)
            return g if g.is_valid else g.buffer(0)
        return None
    outer, inner = [], []
    for m in el.get("members", []):
        pts = [(p["lon"], p["lat"]) for p in m.get("geometry", []) or []]
        if len(pts) >= 2:
            (inner if m.get("role") == "inner" else outer).append(LineString(pts))
    if not outer:
        return None
    polys = list(polygonize(linemerge(outer)))
    if not polys:
        return None
    g = unary_union(polys)
    if inner:
        holes = list(polygonize(linemerge(inner)))
        if holes:
            g = g.difference(unary_union(holes))
    return g if not g.is_empty else None


def outlines_raster(kind: str):
    """Rasterise one kind of OSM outline onto the grid, one id per outline."""
    import geopandas as gpd
    d = json.loads((OSM / f"osm_{kind}_overpass_{AOI_NAME}.json").read_text(encoding="utf-8"))
    rows = [(el["type"][0] + str(el["id"]), outline(el)) for el in d["elements"]]
    rows = [(i, g) for i, g in rows if g is not None]
    gdf = gpd.GeoDataFrame({"osm": [i for i, _ in rows]}, geometry=[g for _, g in rows], crs=4326)
    g = gdf.to_crs(G.CRS)
    ids = rasterize(((geom, k + 1) for k, geom in enumerate(g.geometry)),
                    out_shape=G.SHAPE, transform=G.TRANSFORM, fill=0, dtype="int32")
    return ids, list(gdf.osm)


def halves(n: int) -> np.ndarray:
    """Outline index (1..n) -> 0 calibration / 1 test, alternating over a shuffle."""
    order = np.random.default_rng(SEED).permutation(n)
    half = np.zeros(n + 1, dtype=np.int8)
    half[1:][order] = np.arange(n) % 2
    return half


def ba(pred_tea: np.ndarray, is_tea: np.ndarray) -> float:
    tpr = pred_tea[is_tea].mean() if is_tea.any() else np.nan
    tnr = (~pred_tea[~is_tea]).mean() if (~is_tea).any() else np.nan
    return float((tpr + tnr) / 2)


def main(eyecheck: bool) -> None:
    print(f"Tree-class split — {AOI_NAME}")
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    with rasterio.open(INPUTS) as s:
        raw = s.read()
        names = list(s.descriptions)
    band = {n: raw[i] for i, n in enumerate(names)}

    def frac(n, scale):
        a = band[n].astype(np.float32) / scale
        a[band[n] == 255] = np.nan
        return a

    low, fresh, recent = frac("low_frac", 250), frac("fresh_frac", 250), frac("recent_frac", 250)
    h_mean, h_eth = frac("h_mean", 4), frac("h_eth", 4)
    tree = inside & (lc == TREE)
    t1 = tree & (fresh >= FRESH_MIN)
    t2 = tree & ~t1 & (recent >= RECENT_MIN)
    rest = tree & ~t1 & ~t2
    has_h = np.isfinite(low)

    # ---- references and T_low --------------------------------------------
    tea_ids, tea_osm = outlines_raster("tea")
    for_ids, for_osm = outlines_raster("forest")
    tea_half, for_half = halves(len(tea_osm)), halves(len(for_osm))
    ref_tea = tree & (tea_ids > 0) & (for_ids == 0)
    ref_for = tree & (for_ids > 0) & (tea_ids == 0)
    half = np.full(G.SHAPE, -1, dtype=np.int8)
    half[ref_tea] = tea_half[tea_ids[ref_tea]]
    half[ref_for] = for_half[for_ids[ref_for]]
    claimed = {"tea_cells": int(ref_tea.sum()), "forest_cells": int(ref_for.sum()),
               "tea_claimed_by_T1_T2_pct": round(100 * float((ref_tea & ~rest).sum()) / max(int(ref_tea.sum()), 1), 1),
               "forest_claimed_by_T1_T2_pct": round(100 * float((ref_for & ~rest).sum()) / max(int(ref_for.sum()), 1), 1),
               "no_height_data_pct": round(100 * float(((ref_tea | ref_for) & rest & ~has_h).sum())
                                           / max(int((ref_tea | ref_for).sum()), 1), 1)}
    usable = rest & has_h & (ref_tea | ref_for)
    cal, test = usable & (half == 0), usable & (half == 1)
    grid = np.round(np.arange(0.0, 1.0001, 0.01), 2)
    scores = np.array([ba(low[cal] >= t, ref_tea[cal]) for t in grid])
    best = np.flatnonzero(scores >= scores.max() - 1e-12)
    t_low = float(grid[best[len(best) // 2]])            # middle of any tied range
    p1 = ba(low[test] >= t_low, ref_tea[test])

    def confusion(m):
        pt = low[m] >= t_low
        it = ref_tea[m]
        return {"tea_as_tea": int((pt & it).sum()), "tea_as_forest": int((~pt & it).sum()),
                "forest_as_forest": int((~pt & ~it).sum()), "forest_as_tea": int((pt & ~it).sum())}

    # per-outline view on the test half: share of outlines whose majority is right
    def outline_majority(ids, is_tea_kind):
        right = total = 0
        for k in np.unique(ids[test & (ids > 0)]):
            m = test & (ids == k)
            if m.sum() >= 5:
                total += 1
                right += ((low[m] >= t_low).mean() >= 0.5) == is_tea_kind
        return right, total

    tr, tt = outline_majority(np.where(ref_tea, tea_ids, 0), True)
    fr, ft = outline_majority(np.where(ref_for, for_ids, 0), False)

    # ---- the split ----------------------------------------------------------
    sub = np.zeros(G.SHAPE, dtype=np.uint8)
    sub[t1], sub[t2] = 1, 2
    sub[rest & has_h & (low >= t_low)] = 3
    sub[rest & has_h & (low < t_low)] = 4
    sub[rest & ~has_h] = 5
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="uint8",
                crs=G.CRS, transform=G.TRANSFORM, nodata=0, compress="deflate", tiled=True)
    with rasterio.open(OUT_RASTER, "w", **prof) as d:
        d.write(sub, 1)

    ok = rd(INTERIM / "erosion" / "erosion_assessed.tif").astype(bool)
    n_tree, n_tree_ok = int(tree.sum()), int((tree & ok).sum())
    c_map = np.zeros(G.SHAPE, dtype=np.float32)
    for k, c in C_SUB.items():
        c_map[sub == k] = c
    report = {
        "region": AOI_NAME,
        "rules": {"fresh_min": FRESH_MIN, "recent_min": RECENT_MIN, "C": {NAMES[k]: v for k, v in C_SUB.items()}},
        "references": {**claimed, "tea_outlines": len(tea_osm), "forest_outlines": len(for_osm),
                       "calibration_cells": {"tea": int((cal & ref_tea).sum()), "forest": int((cal & ref_for).sum())},
                       "test_cells": {"tea": int((test & ref_tea).sum()), "forest": int((test & ref_for).sum())}},
        "T_low": t_low,
        "calibration_balanced_accuracy": round(float(scores.max()), 3),
        "P1_test_balanced_accuracy": round(p1, 3),
        "P1_pass": bool(p1 >= P1_BAR),
        "test_confusion_cells": confusion(test),
        "test_outlines_majority_right": {"tea": [int(tr), int(tt)], "forest": [int(fr), int(ft)]},
        "share_of_tree_pct": {NAMES[k]: round(100 * float((sub == k).sum()) / n_tree, 2) for k in NAMES},
        "share_of_scored_tree_pct": {NAMES[k]: round(100 * float(((sub == k) & ok).sum()) / n_tree_ok, 2) for k in NAMES},
        "P3_mean_C_all_tree": round(float(c_map[tree].mean()), 4),
        "P3_mean_C_scored_tree": round(float(c_map[tree & ok].mean()), 4),
        "median_height_m": {NAMES[k]: {"meta": round(float(np.nanmedian(h_mean[sub == k])), 1) if (sub == k).any() else None,
                                       "eth": round(float(np.nanmedian(h_eth[sub == k])), 1) if (sub == k).any() else None}
                            for k in NAMES},
        "reference_median_low_frac": {"tea": round(float(np.nanmedian(low[usable & ref_tea])), 3),
                                      "forest": round(float(np.nanmedian(low[usable & ref_for])), 3)},
    }
    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("T_low", "calibration_balanced_accuracy",
                                              "P1_test_balanced_accuracy", "P1_pass",
                                              "test_outlines_majority_right", "share_of_tree_pct",
                                              "P3_mean_C_all_tree", "P3_mean_C_scored_tree",
                                              "median_height_m", "references")}, indent=1))
    if eyecheck:
        make_eyecheck(sub, ok)


def make_eyecheck(sub: np.ndarray, ok: np.ndarray, per: int = 25) -> None:
    """25 random scored cells per T1-T4, as pictures with neutral ids. The key
    (id -> sub-class) goes to a separate file that is NOT printed here."""
    import requests
    from PIL import Image, ImageDraw
    from pyproj import Transformer
    EYE.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    picks = []
    for k in (1, 2, 3, 4):
        r, c = np.nonzero((sub == k) & ok)
        if len(r) == 0:
            continue
        idx = rng.choice(len(r), size=min(per, len(r)), replace=False)
        picks += [(int(r[i]), int(c[i]), k) for i in idx]
    order = rng.permutation(len(picks))
    picks = [picks[i] for i in order]
    to_ll = Transformer.from_crs(G.CRS, 4326, always_xy=True)
    key = {}
    tiles = []
    for n, (r, c, k) in enumerate(picks, start=1):
        x0, y1 = G.ORIGIN_X + c * G.CELL, G.TOP_Y - r * G.CELL       # cell's top-left
        cx, cy = x0 + 50, y1 - 50
        half = 250                                                  # 500 m window
        w, s = to_ll.transform(cx - half, cy - half)
        e, nn = to_ll.transform(cx + half, cy + half)
        f = EYE / f"cell_{n:03d}.jpg"
        if not f.exists():
            resp = requests.get("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export",
                                params=dict(bbox=f"{w},{s},{e},{nn}", bboxSR=4326, imageSR=4326,
                                            size="500,500", format="jpg", f="image"),
                                headers=UA, timeout=120)
            resp.raise_for_status()
            f.write_bytes(resp.content)
        im = Image.open(f).convert("RGB").resize((500, 500))
        dr = ImageDraw.Draw(im)
        dr.rectangle([200, 200, 300, 300], outline=(255, 230, 0), width=2)   # the 100 m cell
        dr.rectangle([0, 0, 70, 22], fill=(0, 0, 0))
        dr.text((5, 4), f"#{n:03d}", fill=(255, 255, 255))
        tiles.append(im)
        key[f"{n:03d}"] = {"subclass": int(k), "row": r, "col": c}
    for sheet in range(0, len(tiles), 25):
        chunk = tiles[sheet:sheet + 25]
        canvas = Image.new("RGB", (5 * 500, 5 * 500), (20, 20, 20))
        for j, im in enumerate(chunk):
            canvas.paste(im, ((j % 5) * 500, (j // 5) * 500))
        canvas.resize((5 * 300, 5 * 300)).save(EYE / f"_sheet_{sheet // 25 + 1}.jpg", quality=88)
    (EYE / "_KEY_do_not_open_before_labelling.json").write_text(json.dumps(key, indent=1))
    print(f"  eye-check: {len(picks)} pictures and {(len(tiles) + 24) // 25} sheets in {EYE} "
          f"(key written separately, not shown)")


P2_BARS = {1: ("cleared", 0.60), 3: ("tea_bush", 0.60), 4: ("closed_canopy", 0.70)}
LABELS = ("cleared", "tea_bush", "closed_canopy", "cant_tell")


def score(labels_csv: Path) -> None:
    """P2: join the by-eye labels with the key and decide adoption.

    The CSV has one row per picture: id,label with label one of LABELS. The
    denominator is EVERY picture of a sub-class: "cant_tell" counts against
    the bar (the strict reading, fixed before labelling); the share among
    readable pictures is reported beside it. Adoption = P1 and P2 both pass."""
    import csv
    key = json.loads((EYE / "_KEY_do_not_open_before_labelling.json").read_text())
    with open(labels_csv, newline="", encoding="utf-8") as fh:
        lab = {r["id"].strip().lstrip("#").zfill(3): r["label"].strip() for r in csv.DictReader(fh)}
    bad = sorted(set(key) - set(lab)) + [k for k, v in lab.items() if v not in LABELS]
    if bad:
        raise SystemExit(f"missing or invalid labels: {bad[:10]}")
    rep = json.loads(REPORT.read_text())
    out = {}
    for k in (1, 2, 3, 4):
        ids = [i for i, v in key.items() if v["subclass"] == k]
        counts = {l: sum(lab[i] == l for i in ids) for l in LABELS}
        readable = len(ids) - counts["cant_tell"]
        row = {"n": len(ids), "labels": counts}
        if k in P2_BARS:
            want, bar = P2_BARS[k]
            share = counts[want] / len(ids) if ids else 0.0
            row.update({"expected": want, "share": round(share, 3), "bar": bar,
                        "share_of_readable": round(counts[want] / readable, 3) if readable else None,
                        "pass": bool(share >= bar)})
        out[NAMES[k]] = row
    p2 = all(v.get("pass", True) for v in out.values())
    rep.update({"P2_eyecheck": out, "P2_pass": p2, "labels_file": str(labels_csv),
                "adopted": bool(rep.get("P1_pass") and p2)})
    REPORT.write_text(json.dumps(rep, indent=2))
    print(json.dumps({"P2": out, "P1_pass": rep.get("P1_pass"), "P2_pass": p2,
                      "adopted": rep["adopted"]}, indent=1))


if __name__ == "__main__":
    if "--score" in sys.argv:
        score(Path(sys.argv[sys.argv.index("--score") + 1]))
    else:
        main("--eyecheck" in sys.argv)
