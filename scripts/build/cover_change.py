"""Bare ground each dry season, "new bare ground on a steep slope", and each year's loss.

    $env:REGION = "assam"; python scripts/build/cover_change.py              # flags, F1/F2/H1, yearly loss
    $env:REGION = "assam"; python scripts/build/cover_change.py --eyecheck   # + blind dated pictures (E3)
    $env:REGION = "assam"; python scripts/build/cover_change.py --score labels.csv   # E3 + what ships

Every rule and pass bar was written down before this script first ran
(docs/design/EROSION_PLAN.md, "Phase 1, E1.1-E1.3 part 1"):

    evaluable   valid_Y >= 0.50 (else "too cloudy that season")
    flag in Y   scored, slope >= 10 deg, bare_Y >= 0.25, and every evaluable one of
                Y-1, Y-2 (at least one) had bare <= 0.10
    F1  stable forest (tree, tree cover 2000 >= 75%, no Hansen loss 2001-2025, slope >= 10):
        flagged <= 1.0% of evaluable cell-years
    F2  tea-garden interiors (OSM), the rule without the slope condition: <= 3.0%
    H1  Hansen loss on >= 50% of a steep cell in L, none in L-1, L-2: flagged in L or
        L+1 for >= 50%
    E3  blind eye check on dated Sentinel-2 pictures: flags >= 70% "yes", unflagged <= 10%
    Flags are shown only if F1, F2 and E3 pass.

The yearly loss (a monitoring run, not the main map): on tree, shrub and grass,
C_Y = C_class + bare_Y * max(0, 0.34 - C_class); A_Y = R K LS C_Y P.

Inputs: data/raw/04_landcover/ee_dry_season/dry_season_cover_<region>.tif
        (scripts/fetch/fetch_48_dry_season_cover.py), the recipe's outputs
        (erosion_factors.py), the OSM tea outlines (fetch_45).
Outputs: data/interim/<region>/erosion/cover_flags.tif     (band per year 2020-2026:
                                                            1 flagged, 0 not, 255 not evaluable)
         data/interim/<region>/erosion/erosion_A_dry_<Y>_tpha.tif
         reports/cover_change_<region>.json, _catchments.csv, _districts.csv
         data/interim/<region>/erosion/eyecheck_change/   (pictures, sheets, key)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, LANDCOVER, ROOT, outline

warnings.filterwarnings("ignore")

YEARS = list(range(2019, 2027))
FLAG_YEARS = YEARS[1:]
VALID_MIN, BARE_MIN, BASE_MAX, STEEP_DEG = 0.50, 0.25, 0.10, 10.0
F1_TC, F1_BAR, F2_BAR = 75, 0.010, 0.030
H1_LOSS, H1_BAR = 0.50, 0.50
E3_N, E3_FLAG_BAR, E3_UNFLAG_BAR = 40, 0.70, 0.10
C_CLEARED = 0.34                      # cleared jhum (IWED), as T1 in tree_split.py
REFRESH_LC = (10, 20, 30)             # tree, shrub, grass
# Attempt 2 (EROSION_PLAN.md, "E1.3 attempt 2"): the same rule plus a drop of at
# least DROP_MIN in the square's mean NDVI against its earlier evaluable seasons,
# judged on a NEW blind sample (seed 43) that excludes attempt 1's cells.
ATTEMPT = 2 if "--v2" in sys.argv else 1
SUF = "_v2" if ATTEMPT == 2 else ""
DROP_MIN = 0.20
SEED = 43 if ATTEMPT == 2 else 42
INPUTS = LANDCOVER / "ee_dry_season" / f"dry_season_cover_{AOI_NAME}.tif"
E = INTERIM / "erosion"
EYE = E / f"eyecheck_change{SUF}"
EYE_V1 = E / "eyecheck_change"
REPORT = ROOT / "reports" / f"cover_change_{AOI_NAME}{SUF}.json"


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def load_inputs() -> dict:
    with rasterio.open(INPUTS) as s:
        names = list(s.descriptions)
        arr = s.read()
    band = dict(zip(names, arr))

    def share(b):
        a = band[b].astype(np.float32)
        a[band[b] == 255] = np.nan
        return a / 250.0
    tc = band["tc2000"].astype(np.float32)
    tc[band["tc2000"] == 255] = np.nan
    return {"valid": {y: share(f"valid_{y}") for y in YEARS},
            "bare": {y: share(f"bare_{y}") for y in YEARS},
            "ndvi": {y: share(f"ndvi_{y}") for y in YEARS},
            "tc2000": tc, "loss_any": share("loss_any"),
            "loss": {y: share(f"loss_{y}") for y in range(2018, 2026)}}


def flags(d: dict, steep_gate: np.ndarray) -> tuple[dict, dict]:
    """(flagged, judged) per year. `judged` = the flag could be evaluated:
    Y evaluable and at least one of Y-1, Y-2 evaluable."""
    ev = {y: np.nan_to_num(d["valid"][y], nan=0) >= VALID_MIN for y in YEARS}
    flagged, judged = {}, {}
    for y in FLAG_YEARS:
        base = [b for b in (y - 1, y - 2) if b in ev]
        any_base = np.zeros(G.SHAPE, bool)
        base_green = np.ones(G.SHAPE, bool)
        base_ndvi = np.full(G.SHAPE, -1.0, np.float32)
        for b in base:
            any_base |= ev[b]
            base_green &= ~ev[b] | (np.nan_to_num(d["bare"][b], nan=1) <= BASE_MAX)
            base_ndvi = np.where(ev[b], np.maximum(base_ndvi, np.nan_to_num(d["ndvi"][b], nan=-1)), base_ndvi)
        judged[y] = ev[y] & any_base & steep_gate
        flagged[y] = judged[y] & (np.nan_to_num(d["bare"][y], nan=0) >= BARE_MIN) & base_green
        if ATTEMPT == 2:                    # it lost its cover, not merely dipped under the line
            flagged[y] &= (base_ndvi - np.nan_to_num(d["ndvi"][y], nan=9)) >= DROP_MIN
    return flagged, judged


def rate(flagged: dict, judged: dict, sel: np.ndarray) -> dict:
    n = sum(int((judged[y] & sel).sum()) for y in judged)
    k = sum(int((flagged[y] & sel).sum()) for y in judged)
    per = {str(y): {"cell_years": int((judged[y] & sel).sum()), "flagged": int((flagged[y] & sel).sum())}
           for y in judged}
    return {"cells": int(sel.sum()), "cell_years": n, "flagged": k,
            "rate": round(k / n, 4) if n else None, "per_year": per}


def tea_interior() -> np.ndarray:
    from tree_split import outlines_raster
    ids, _ = outlines_raster("tea")
    return ndimage.minimum_filter((ids > 0).astype(np.uint8), size=3).astype(bool)


def unit_tables(d: dict, flagged: dict, A_y: dict, ok, steep) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per catchment and per district, per year: loss with that year's cover, the
    share of steep scored land that was bare, newly bare steep hectares, cloud."""
    import geopandas as gpd
    from erosion_priority import ids_of
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    out = []
    for kind, gdf, key in (("catchment", bas, "HYBAS_ID"), ("district", dist, "NAME_2")):
        ids = ids_of(gdf)
        n = len(gdf)

        def per(sel, w=None):
            return np.bincount(ids[sel], weights=None if w is None else w[sel], minlength=n + 1)[1:]
        n_ok = per(ok)
        n_steep = per(ok & steep)
        rows = []
        for y in YEARS:
            ev = np.nan_to_num(d["valid"][y], nan=0) >= VALID_MIN
            bare = np.nan_to_num(d["bare"][y], nan=0).astype(np.float64)
            se = ok & steep & ev
            with np.errstate(invalid="ignore", divide="ignore"):
                r = pd.DataFrame({
                    key: gdf[key].values, "year": y,
                    "meanA_dry": per(ok, A_y[y].astype(np.float64)) / n_ok,
                    "evaluable_pct": 100 * per(ok & ev) / n_ok,
                    "steep_bare_pct": 100 * per(se, bare) / per(se),
                    "steep_scored_km2": n_steep / 100,
                    "new_bare_steep_ha": per(flagged[y]) if y in flagged else np.nan})
            rows.append(r)
        t = pd.concat(rows, ignore_index=True)
        t = t[t.groupby(key).meanA_dry.transform("count") > 0]
        out.append(t)
    return out[0], out[1].rename(columns={"NAME_2": "district"})


def main() -> None:
    print(f"Dry-season cover change — {AOI_NAME}")
    d = load_inputs()
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif")
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    steep = slope >= STEEP_DEG

    # ---- the cloud picture, per year --------------------------------------
    yearly = {}
    for y in YEARS:
        v = d["valid"][y]
        ev = np.nan_to_num(v, nan=0) >= VALID_MIN
        b = d["bare"][y]
        yearly[str(y)] = {
            "evaluable_pct_of_scored": round(100 * float((ev & ok).sum()) / ok.sum(), 2),
            "evaluable_pct_of_steep_scored": round(100 * float((ev & ok & steep).sum()) / (ok & steep).sum(), 2),
            "no_data_pct_of_state": round(100 * float((~np.isfinite(v) & inside).sum()) / inside.sum(), 2),
            "bare_pct_of_steep_scored_evaluable": round(100 * float(np.nanmean(b[ev & ok & steep])), 2),
        }

    # ---- flags and the pre-registered tests -------------------------------
    fl, jd = flags(d, ok & steep)
    fl_ns, jd_ns = flags(d, ok)                       # without the slope condition (F2)
    tree = lc == 10
    stable = (tree & ok & steep & (np.nan_to_num(d["tc2000"], nan=0) >= F1_TC)
              & (np.nan_to_num(d["loss_any"], nan=1) == 0))
    F1 = rate(fl, jd, stable)
    F1["bar"], F1["pass"] = F1_BAR, F1["rate"] is not None and F1["rate"] <= F1_BAR
    tea = tea_interior() & ok
    F2 = rate(fl_ns, jd_ns, tea)
    F2["bar"], F2["pass"] = F2_BAR, F2["rate"] is not None and F2["rate"] <= F2_BAR
    F2["steep_only"] = rate(fl, jd, tea & steep)       # reported, no bar

    hits, n_h, per_l = 0, 0, {}
    for L in range(2020, 2026):
        loss = d["loss"]
        sel = (ok & steep & (np.nan_to_num(loss[L], nan=0) >= H1_LOSS)
               & (np.nan_to_num(loss[L - 1], nan=1) == 0) & (np.nan_to_num(loss[L - 2], nan=1) == 0))
        yrs = [y for y in (L, L + 1) if y in fl]
        can = np.zeros(G.SHAPE, bool)
        got = np.zeros(G.SHAPE, bool)
        for y in yrs:
            can |= jd[y]
            got |= fl[y]
        s_ev = sel & can
        per_l[str(L)] = {"cells": int(sel.sum()), "evaluable": int(s_ev.sum()), "caught": int((s_ev & got).sum())}
        n_h += int(s_ev.sum())
        hits += int((s_ev & got).sum())
    H1 = {"cell_events": n_h, "caught": hits, "rate": round(hits / n_h, 4) if n_h else None,
          "per_loss_year": per_l, "bar": H1_BAR}
    H1["pass"] = H1["rate"] is not None and H1["rate"] >= H1_BAR

    print(f"  F1 stable forest: {F1['flagged']}/{F1['cell_years']} = {F1['rate']}  (bar <= {F1_BAR})  "
          f"{'PASS' if F1['pass'] else 'FAIL'}")
    print(f"  F2 tea interiors: {F2['flagged']}/{F2['cell_years']} = {F2['rate']}  (bar <= {F2_BAR})  "
          f"{'PASS' if F2['pass'] else 'FAIL'}")
    print(f"  H1 Hansen clearing caught: {hits}/{n_h} = {H1['rate']}  (bar >= {H1_BAR})  "
          f"{'PASS' if H1['pass'] else 'FAIL'}")

    # ---- write the flags --------------------------------------------------
    stack = np.full((len(FLAG_YEARS), *G.SHAPE), 255, np.uint8)
    for i, y in enumerate(FLAG_YEARS):
        stack[i][jd[y]] = 0
        stack[i][fl[y]] = 1
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=len(FLAG_YEARS), dtype="uint8",
                crs=G.CRS, transform=G.TRANSFORM, nodata=255, compress="deflate", tiled=True)
    with rasterio.open(E / f"cover_flags{SUF}.tif", "w", **prof) as dst:
        dst.write(stack)
        dst.descriptions = tuple(str(y) for y in FLAG_YEARS)
    for y in FLAG_YEARS:
        yearly[str(y)]["flags"] = int(fl[y].sum())

    # ---- each year's loss with that dry season's cover --------------------
    R, K, LS, C = (rd(E / f"erosion_{f}.tif") for f in ("R", "K", "LS", "C"))
    refresh = np.isin(lc, REFRESH_LC)
    A_y = {}
    fprof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="float32",
                 crs=G.CRS, transform=G.TRANSFORM, nodata=np.nan, compress="deflate", tiled=True)
    for y in YEARS:
        ev = np.nan_to_num(d["valid"][y], nan=0) >= VALID_MIN
        b = np.nan_to_num(d["bare"][y], nan=0)
        Cy = np.where(refresh & ev, C + b * np.maximum(0, C_CLEARED - C), C).astype(np.float32)
        a = (R * K * LS * Cy).astype(np.float32)
        a[~ok] = np.nan
        A_y[y] = a
        with rasterio.open(E / f"erosion_A_dry_{y}_tpha.tif", "w", **fprof) as dst:
            dst.write(a, 1)
        yearly[str(y)]["meanA_dry_tpha"] = round(float(np.nanmean(a)), 2)
    A_main = rd(E / "erosion_A_tpha.tif")

    cat, dis = unit_tables(d, fl, A_y, ok, steep)
    cat.round(3).to_csv(ROOT / "reports" / f"cover_change_{AOI_NAME}{SUF}_catchments.csv", index=False)
    dis.round(3).to_csv(ROOT / "reports" / f"cover_change_{AOI_NAME}{SUF}_districts.csv", index=False)

    prev = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    rep = {"region": AOI_NAME,
           "attempt": ATTEMPT, "drop_min": DROP_MIN if ATTEMPT == 2 else None,
           "rules": {"valid_min": VALID_MIN, "bare_min": BARE_MIN, "base_max": BASE_MAX,
                     "steep_deg": STEEP_DEG, "bare_ndvi": 0.30, "window": "1 Feb - 30 Apr",
                     "C_cleared": C_CLEARED, "refresh_lc": REFRESH_LC},
           "F1_stable_forest": F1, "F2_tea": F2, "H1_hansen_clearing": H1,
           "yearly": yearly,
           "meanA_main_tpha": round(float(np.nanmean(A_main)), 2),
           "E3_eyecheck": prev.get("E3_eyecheck"),
           "flags_shown": bool(F1["pass"] and F2["pass"] and (prev.get("E3_eyecheck") or {}).get("pass"))}
    REPORT.write_text(json.dumps(rep, indent=2))
    for y, v in yearly.items():
        print(f"  {y}: evaluable {v['evaluable_pct_of_scored']:5.1f}% of scored "
              f"({v['evaluable_pct_of_steep_scored']:5.1f}% steep); steep bare {v['bare_pct_of_steep_scored_evaluable']:5.2f}%; "
              f"flags {v.get('flags', '-')}; mean A {v['meanA_dry_tpha']}")
    print(f"  wrote {REPORT.relative_to(ROOT)}; flags shown: {rep['flags_shown']}")
    if "--eyecheck" in sys.argv:
        eyecheck(fl, jd)


# ---- E3: blind eye check on dated Sentinel-2 pictures -------------------------

def chip(ee, y: int, x: float, yy: float, half_px: int = 75):
    """Dry-season (1 Feb - 30 Apr) Sentinel-2 true colour, 10 m, centred on (x, yy)."""
    from fetch_48_dry_season_cover import CLEAR_MIN, CSP, S2, WINDOW
    w, s, e, n = x - 1000, yy - 1000, x + 1000, yy + 1000
    box = ee.Geometry.Rectangle([w, s, e, n], G.CRS, False)
    col = (ee.ImageCollection(S2).filterBounds(box).filterDate(f"{y}-{WINDOW[0]}", f"{y}-{WINDOW[1]}")
           .linkCollection(ee.ImageCollection(CSP), ["cs_cdf"])
           .map(lambda i: i.select(["B4", "B3", "B2"]).updateMask(i.select("cs_cdf").gte(CLEAR_MIN))))
    img = col.median().divide(3000).multiply(255).min(255).max(0).unmask(0).toUint8()
    arr = ee.data.computePixels({
        "expression": img, "fileFormat": "NUMPY_NDARRAY",
        "grid": {"dimensions": {"width": 2 * half_px, "height": 2 * half_px},
                 "affineTransform": {"scaleX": 10, "shearX": 0, "translateX": x - half_px * 10,
                                     "shearY": 0, "scaleY": -10, "translateY": yy + half_px * 10},
                 "crsCode": G.CRS}})
    return np.dstack([arr["B4"], arr["B3"], arr["B2"]])


def eyecheck(fl: dict, jd: dict) -> None:
    import ee
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
    ee.Initialize(project="earthengine-507510")
    rng = np.random.default_rng(SEED)
    seen = set()
    if ATTEMPT == 2 and (EYE_V1 / "_key.csv").exists():   # never re-show attempt 1's cells
        k1 = pd.read_csv(EYE_V1 / "_key.csv")
        seen = set(zip(k1.row.astype(int), k1.col.astype(int)))
    picks = []
    for kind, want in (("flag", True), ("unflagged", False)):
        pool = [(y, r, c) for y in FLAG_YEARS
                for r, c in zip(*np.nonzero(jd[y] & (fl[y] == want))) if (int(r), int(c)) not in seen]
        for i in rng.choice(len(pool), size=min(E3_N, len(pool)), replace=False):
            picks.append((kind, *pool[i]))
    order = rng.permutation(len(picks))
    EYE.mkdir(parents=True, exist_ok=True)
    key = []
    for nid, i in enumerate(order, 1):
        kind, y, r, c = picks[i]
        x, yy = G.centre_xy(r, c)
        a, b = chip(ee, int(y) - 1, float(x), float(yy)), chip(ee, int(y), float(x), float(yy))
        fig, axes = plt.subplots(1, 2, figsize=(8, 4.2))
        for ax, im, t in zip(axes, (a, b), ("year before", "this year")):
            ax.imshow(im)
            ax.add_patch(Rectangle((69.5, 69.5), 10, 10, fill=False, ec="yellow", lw=1.4))
            ax.set_title(t, fontsize=10); ax.set_xticks([]); ax.set_yticks([])
        fig.suptitle(f"picture {nid:03d}", fontsize=11)
        fig.tight_layout()
        fig.savefig(EYE / f"pic_{nid:03d}.png", dpi=80)
        plt.close(fig)
        key.append({"id": nid, "kind": kind, "year": int(y), "row": int(r), "col": int(c)})
        print(f"    picture {nid}/{len(picks)}", flush=True)
    pd.DataFrame(key).to_csv(EYE / "_key.csv", index=False)
    pd.DataFrame({"id": [k["id"] for k in key], "label": ""}).to_csv(EYE / "labels_blank.csv", index=False)
    print(f"  {len(key)} pictures in {EYE}; key in _key.csv (do not open before labelling)")


def score(labels_csv: str) -> None:
    lab = pd.read_csv(labels_csv)
    key = pd.read_csv(EYE / "_key.csv")
    m = key.merge(lab, on="id")
    res = {}
    for kind, bar, better in (("flag", E3_FLAG_BAR, "ge"), ("unflagged", E3_UNFLAG_BAR, "le")):
        k = m[m.kind == kind]
        yes = int((k.label == "yes").sum())
        readable = int((k.label != "cant_tell").sum())
        share = yes / len(k) if better == "ge" else yes / max(readable, 1)
        ok = share >= bar if better == "ge" else share <= bar
        res[kind] = {"n": int(len(k)), "yes": yes, "no": int((k.label == "no").sum()),
                     "cant_tell": int((k.label == "cant_tell").sum()), "share_yes": round(share, 3),
                     "share_yes_readable": round(yes / max(readable, 1), 3), "bar": bar, "pass": bool(ok)}
    res["pass"] = bool(res["flag"]["pass"] and res["unflagged"]["pass"])
    rep = json.loads(REPORT.read_text())
    rep["E3_eyecheck"] = res
    rep["flags_shown"] = bool(rep["F1_stable_forest"]["pass"] and rep["F2_tea"]["pass"] and res["pass"])
    REPORT.write_text(json.dumps(rep, indent=2))
    print(json.dumps(res, indent=1))
    print(f"  flags shown: {rep['flags_shown']}")


if __name__ == "__main__":
    if "--score" in sys.argv:
        score(sys.argv[sys.argv.index("--score") + 1])
    else:
        main()
