"""Soil-erosion recipe (RUSLE) on the canonical grid: A = R x K x LS x C x P.

    $env:REGION = "assam"; python scripts/build/erosion_factors.py

Every choice here was written down in docs/design/EROSION_PLAN.md ("Step 5, part 1")
BEFORE this script first ran, so the numbers cannot have steered them. Change a
choice only with a new dated entry there.

In plain words, soil washed off a slope each year is the product of:
    R  how hard the rain hits            InRESatE map (IRED alongside)
    K  how easily this soil washes       Williams (1995) from SoilGrids topsoil
    LS how steep and how long the slope  McCool S, capped slope length
    C  how bare the ground is            land-cover lookup (IWED's values)
    P  protection (bunds, terraces)      1 everywhere: "if untreated"

Outputs (data/interim/<region>/erosion/):
    erosion_R.tif  erosion_K.tif  erosion_LS.tif  erosion_C.tif
    erosion_A_tpha.tif        soil loss, t/ha/yr, main run
    erosion_A_ired_tpha.tif   the same with IRED's R
    erosion_A_treeC_alt_tpha.tif  the same with tree C = 0.003 (sensitivity)
    erosion_A_treeC_avg_tpha.tif  once the tree split is adopted: the same with one
                                  value (0.03) for all tree land, i.e. without the split
    erosion_class.tif         0 not assessed, 1 slight .. 6 very severe
    erosion_assessed.tif      1 = scored, 0 = not assessed by this method
Summary: reports/erosion_factors_<region>.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import time
import warnings

import numpy as np
import rasterio
import scipy.io as sio
from affine import Affine
from rasterio.enums import Resampling
from rasterio.warp import reproject
from scipy import ndimage

import grid as G
from common import AOI_NAME, INTERIM, ROOT, WEATHER

warnings.filterwarnings("ignore")

OUT = INTERIM / "erosion"
TER = INTERIM / "terrain"
FEA = INTERIM / "features"
ER = WEATHER / "erosivity"
IRED_TIF = ER / "ired" / "Indian Rainfall Erosivity Dataset (IRED)" / "Dataset" / "tif" / "R-Factor_India.tif"
INRESATE = ER / "inresate" / "R-factor"

# --- the written-down choices (EROSION_PLAN.md, Step 5 part 1) ----------------
# Several are PROVISIONAL. Each has a row in EROSION_PLAN.md's "Revisit register"
# (V-xx below) saying why it is good enough now and what should make us change it.
# Change a value only with a new dated entry there.
LAMBDA_CAP_M = 300.0          # slope length cap                                  V-08
FLAT_BAND_M = 20.0            # "land under 20 m above its channel" for the guard V-06
GUARD_PCTL = 90               # tree slope capped at this pctl of cropland slope  V-06
RIVER_LAND_M = 2.0            # under this height above channel: not assessed     V-07
RIVER_LAND_ALT_M = 5.0        # reported alongside
CHANNEL_CELLS = 10_000        # >= 100 km2 upstream, as build_hand_100m.py

# WorldCover code -> C. Values from IWED Table 2 (Raj, Saharia & Chakma).      V-02, V-04
# Tree 0.03 is a CLASS AVERAGE over closed forest, tea gardens and jhum fallow
# (decision D8): fair for catchment totals, too high for closed-forest cells and
# too low for tea/jhum cells. Upgrade = split the class with Sentinel-2 (E1.1).
C_LOOKUP = {10: 0.03, 20: 0.11, 30: 0.16, 40: 0.34, 60: 0.45}
NOT_ASSESSED_LC = {50, 70, 80, 90, 95, 100}   # built, snow, water, wetland, mangrove, moss
TREE, CROP = 10, 40
TREE_C_ALT = 0.003            # sensitivity: Wischmeier & Smith closed forest (added after the debug run)

CLASS_EDGES = [5, 10, 20, 40, 80]             # t/ha/yr, provisional (D4)   V-11
CLASS_NAMES = ["slight", "moderate", "high", "very high", "severe", "very severe"]

GUWAHATI = (26.10, 91.59)                     # the gauge anchor, for a resampling check


def rd(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        return s.read(1)


def write(name: str, arr: np.ndarray, dtype: str = "float32") -> None:
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype=dtype,
                crs=G.CRS, transform=G.TRANSFORM, compress="deflate", tiled=True,
                blockxsize=256, blockysize=256,
                nodata=np.nan if dtype == "float32" else 0)
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT / f"{name}.tif", "w", **prof) as d:
        d.write(arr.astype(dtype), 1)


def fill_nearest(a: np.ndarray) -> np.ndarray:
    """Fill NaNs from the nearest valid cell, so bilinear resampling at the
    edge of the source's coverage does not turn border cells into NaN."""
    bad = ~np.isfinite(a)
    if not bad.any():
        return a
    idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def to_grid(src: np.ndarray, transform: Affine) -> np.ndarray:
    dst = np.full(G.SHAPE, np.nan, dtype=np.float32)
    reproject(source=src.astype(np.float32), destination=dst,
              src_transform=transform, src_crs="EPSG:4326", src_nodata=np.nan,
              dst_transform=G.TRANSFORM, dst_crs=G.CRS, dst_nodata=np.nan,
              resampling=Resampling.bilinear)
    return dst


def load_r_inresate() -> tuple[np.ndarray, float]:
    def one(n):
        d = sio.loadmat(INRESATE / f"{n}.mat")
        return np.asarray(d[[k for k in d if not k.startswith("__")][0]], float)
    R, lat, lon = one("R"), np.ravel(one("lat")), np.ravel(one("lon"))
    if R.shape == (len(lon), len(lat)):
        R = R.T
    gauge = float(R[np.argmin(abs(lat - GUWAHATI[0])), np.argmin(abs(lon - GUWAHATI[1]))])
    if lat[0] < lat[-1]:                       # make row 0 the north edge
        R, lat = R[::-1], lat[::-1]
    dx, dy = float(lon[1] - lon[0]), float(lat[0] - lat[1])
    tr = Affine(dx, 0, lon[0] - dx / 2, 0, -dy, lat[0] + dy / 2)
    return to_grid(fill_nearest(R), tr), gauge


def load_r_ired() -> np.ndarray:
    with rasterio.open(IRED_TIF) as s:
        a = s.read(1).astype(float)
        if s.nodata is not None:
            a[a == s.nodata] = np.nan
        a[a < 0] = np.nan
        return to_grid(fill_nearest(a), s.transform)


def tree_split():
    """(sub-class raster, C per sub-class) once the tree split is ADOPTED, else None.

    Adoption is recorded by scripts/build/tree_split.py (`--score`) only when
    both pre-registered pass bars are met (EROSION_PLAN.md, Phase 1 E1.1)."""
    rep = ROOT / "reports" / f"tree_split_{AOI_NAME}.json"
    ras = INTERIM / "features" / "tree_subclass.tif"
    if not (rep.exists() and ras.exists()):
        return None
    if json.loads(rep.read_text()).get("adopted") is not True:
        return None
    from tree_split import C_SUB
    return rd(ras), C_SUB


def k_williams(sand, silt, clay, oc):
    """Williams (1995) EPIC erodibility, all inputs in percent. Returns SI units."""
    sn1 = 1 - sand / 100
    f_csand = 0.2 + 0.3 * np.exp(-0.256 * sand * (1 - silt / 100))
    with np.errstate(invalid="ignore", divide="ignore"):
        f_clsi = np.power(silt / (clay + silt), 0.3)
    f_orgc = 1 - 0.25 * oc / (oc + np.exp(3.72 - 2.95 * oc))
    f_hisand = 1 - 0.7 * sn1 / (sn1 + np.exp(-5.51 + 22.9 * sn1))
    return 0.1317 * f_csand * f_clsi * f_orgc * f_hisand


def s_mccool(theta):
    s = np.sin(theta)
    return np.where(np.tan(theta) < 0.09, 10.8 * s + 0.03, 16.8 * s - 0.50)


def s_nearing(theta):
    return -1.5 + 17 / (1 + np.exp(2.3 - 6.1 * np.sin(theta)))


def l_factor(acc, theta):
    lam = np.minimum((acc + 1.0) * G.CELL, LAMBDA_CAP_M)
    s = np.sin(theta)
    beta = (s / 0.0896) / (3 * np.power(s, 0.8) + 0.56)
    m = beta / (1 + beta)
    return np.power(lam / 22.13, m)


def classify(a, ok):
    c = np.digitize(a, CLASS_EDGES).astype(np.uint8) + 1
    c[~ok | ~np.isfinite(a)] = 0
    return c


def shares(cls, ok):
    n = int(ok.sum())
    return {CLASS_NAMES[i]: round(100 * float((cls[ok] == i + 1).sum()) / n, 2) for i in range(6)}


def pct(v, ps=(1, 5, 25, 50, 75, 95, 99)):
    v = v[np.isfinite(v)]
    return {f"p{p}": round(float(np.percentile(v, p)), 4) for p in ps}


def main() -> None:
    t0 = time.time()
    print(f"Erosion recipe (RUSLE) — {AOI_NAME}")
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    n_in = int(inside.sum())

    # ---- R ------------------------------------------------------------------
    R, r_gauge_src = load_r_inresate()
    R_ired = load_r_ired()
    gr, gc = G.xy_to_rowcol(*__import__("pyproj").Transformer.from_crs(
        4326, G.CRS, always_xy=True).transform(GUWAHATI[1], GUWAHATI[0]))
    r_gauge_grid = float(R[gr, gc]) if 0 <= gr < G.NROWS and 0 <= gc < G.NCOLS else None
    print(f"  R  InRESatE p50 {np.nanmedian(R[inside]):,.0f}   IRED p50 {np.nanmedian(R_ired[inside]):,.0f}"
          f"   (Guwahati: source cell {r_gauge_src:,.0f}, on grid "
          f"{'outside box' if r_gauge_grid is None else f'{r_gauge_grid:,.0f}'})")

    # ---- K ------------------------------------------------------------------
    def top(prop, unit, div):
        a = rd(FEA / f"soil_{prop}_0-5cm_{unit}.tif")
        b = rd(FEA / f"soil_{prop}_15-30cm_{unit}.tif")
        return (a + b) / 2 / div
    sand, silt, clay = top("sand", "gkg", 10), top("silt", "gkg", 10), top("clay", "gkg", 10)
    oc = top("soc", "dgkg", 100)
    K = k_williams(sand, silt, clay, oc).astype(np.float32)
    print(f"  K  p50 {np.nanmedian(K[inside]):.4f}  (sand {np.nanmedian(sand[inside]):.0f}% "
          f"silt {np.nanmedian(silt[inside]):.0f}% clay {np.nanmedian(clay[inside]):.0f}% "
          f"OC {np.nanmedian(oc[inside]):.2f}%)")

    # ---- LS, with the treetop guard ------------------------------------------
    slope = rd(TER / "terrain_slope_deg.tif").astype(np.float32)
    acc = rd(TER / "hydro_flowacc_cells.tif").astype(np.float32)
    hand = rd(TER / "hydro_hand_m.tif").astype(np.float32)
    lc = rd(FEA / "lc_class_cat.tif")

    # Guard v2 (2026-10-17, EROSION_PLAN.md Step 6 part 2). The canopy in the
    # surface DEM lifts the slope of tree cells AND of the cells beside them (a
    # crop cell next to a grove sees the canopy step as slope). v1 capped tree
    # cells only and left false hotspots on that crop: next-to-tree cropland read
    # 1.60 deg median vs 0.43 deg away from trees, 30.5% vs 4.5% at >= 40 t/ha/yr.
    # So cap both, against cropland NOT next to trees, the honest flat reference.
    band = inside & (hand < FLAT_BAND_M)
    tree = lc == TREE
    near_tree = ndimage.maximum_filter(tree.astype(np.uint8), size=3).astype(bool)
    crop_ref = float(np.nanpercentile(slope[band & (lc == CROP) & ~near_tree], GUARD_PCTL))
    guard = band & near_tree & (slope > crop_ref)
    slope_g = slope.copy()
    slope_g[guard] = crop_ref
    print(f"  treetop guard v2: p{GUARD_PCTL} slope of cropland not next to trees, under {FLAT_BAND_M:.0f} m = {crop_ref:.2f} deg; "
          f"{100 * guard.sum() / n_in:.1f}% of the state capped")

    th, th_raw = np.radians(slope_g), np.radians(slope)
    L = l_factor(acc, th)
    LS = (L * s_mccool(th)).astype(np.float32)
    LS_raw = (l_factor(acc, th_raw) * s_mccool(th_raw)).astype(np.float32)
    LS_near = (L * s_nearing(th)).astype(np.float32)
    LS = np.maximum(LS, 0)          # McCool's S dips below 0 only at ~0 deg slope
    LS_raw, LS_near = np.maximum(LS_raw, 0), np.maximum(LS_near, 0)

    # ---- C, P ---------------------------------------------------------------
    C = np.full(G.SHAPE, np.nan, dtype=np.float32)
    for code, v in C_LOOKUP.items():
        C[lc == code] = v
    C_avg = C                                 # tree = the D8 class average (0.03)
    split = tree_split()
    if split is not None:
        # Phase 1 E1.1 (EROSION_PLAN.md): the "tree" class split into freshly
        # cleared / regrowing / low canopy / tall canopy, each with its own C.
        # Only once tree_split.py has recorded both pass bars as met
        # ("adopted": true); until then this branch never runs and every output
        # is exactly what it was before the split existed.
        sub, c_sub = split
        C = C.copy()
        for k, v in c_sub.items():
            C[(lc == TREE) & (sub == k)] = v
    P = 1.0                                   # "if untreated" — V-05

    # ---- what is assessed ---------------------------------------------------
    lc_bad = np.isin(lc, list(NOT_ASSESSED_LC))
    channel = acc >= CHANNEL_CELLS
    base_ok = inside & ~lc_bad & ~channel & np.isfinite(C)

    def assessed(river_m):
        return base_ok & (hand >= river_m)

    ok = assessed(RIVER_LAND_M) & np.isfinite(R) & np.isfinite(K) & np.isfinite(LS)
    ok_alt = assessed(RIVER_LAND_ALT_M) & np.isfinite(R) & np.isfinite(K) & np.isfinite(LS)

    # ---- A ------------------------------------------------------------------
    def soil_loss(r, ls):
        a = (r * K * ls * C * P).astype(np.float32)
        a[~ok] = np.nan
        return a

    A = soil_loss(R, LS)
    A_ired = soil_loss(R_ired, LS)
    cls = classify(A, ok)

    main_label = ("main (InRESatE, tree split, guard, McCool, river land < 2 m)" if split is not None
                  else "main (InRESatE, guard, McCool, river land < 2 m)")
    sens = {
        main_label: shares(cls, ok),
        "IRED rain": shares(classify(A_ired, ok), ok),
        "no treetop guard": shares(classify(soil_loss(R, LS_raw), ok), ok),
        "Nearing steepness": shares(classify(soil_loss(R, LS_near), ok), ok),
    }
    # Added 2026-10-17 after the Arunachal debug run (EROSION_PLAN.md, Step 5
    # part 2): IWED's tree C of 0.03 is 10-30x Wischmeier & Smith's closed-forest
    # range (0.001-0.004), and it decides forest-vs-farmland order. Carried as a
    # sensitivity case, not swapped into the main run after seeing numbers.
    C_lo = np.where(lc == TREE, TREE_C_ALT, C).astype(np.float32)
    a_lo = (R * K * LS * C_lo * P).astype(np.float32); a_lo[~ok] = np.nan
    sens[f"tree C {TREE_C_ALT:g}"] = shares(classify(a_lo, ok), ok)
    write("erosion_A_treeC_alt_tpha", a_lo)
    a_alt = (R * K * LS * C * P).astype(np.float32)
    sens["river land < 5 m"] = shares(classify(a_alt, ok_alt), ok_alt)
    if split is not None:
        # What the split changed: the same run with one value for all tree land.
        a_avg = (R * K * LS * C_avg * P).astype(np.float32); a_avg[~ok] = np.nan
        sens[f"tree class average {C_LOOKUP[TREE]:g} (D8)"] = shares(classify(a_avg, ok), ok)
        write("erosion_A_treeC_avg_tpha", a_avg)

    # ---- write --------------------------------------------------------------
    for name, arr in (("erosion_R", R), ("erosion_K", K), ("erosion_LS", LS), ("erosion_C", C)):
        a = arr.copy(); a[~inside] = np.nan
        write(name, a)
    write("erosion_A_tpha", A)
    write("erosion_A_ired_tpha", A_ired)
    write("erosion_class", cls, "uint8")
    write("erosion_assessed", ok.astype(np.uint8), "uint8")

    why_not = {
        "water/built/wetland/snow/moss/mangrove": round(100 * float((inside & lc_bad).sum()) / n_in, 2),
        "channel cells": round(100 * float((inside & channel & ~lc_bad).sum()) / n_in, 2),
        f"river land < {RIVER_LAND_M:g} m": round(100 * float((base_ok & (hand < RIVER_LAND_M)).sum()) / n_in, 2),
    }
    summary = {
        "region": AOI_NAME,
        "settings": {"R": "InRESatE (IRED alongside)", "K": "Williams 1995, mean of 0-5 and 15-30 cm",
                     "L": f"McCool 1989 m, lambda capped {LAMBDA_CAP_M:g} m", "S": "McCool 1987",
                     "treetop_guard": {"version": 2, "applies_to": "tree cells and cells next to a tree cell", "reference": "cropland not next to trees", "band_m": FLAT_BAND_M, "cropland_pctl": GUARD_PCTL,
                                       "cap_deg": round(crop_ref, 3),
                                       "share_of_state_capped_pct": round(100 * float(guard.sum()) / n_in, 2)},
                     "C": C_LOOKUP, "P": 1, "river_land_m": RIVER_LAND_M, "classes_tpha": CLASS_EDGES},
        "in_state_cells": n_in,
        "assessed_pct_of_state": round(100 * float(ok.sum()) / n_in, 2),
        "assessed_pct_if_river_land_5m": round(100 * float(ok_alt.sum()) / n_in, 2),
        "not_assessed_pct_of_state": why_not,
        "R_guwahati": {"source_cell": round(r_gauge_src), "on_grid": None if r_gauge_grid is None else round(r_gauge_grid)},
        "factors_on_assessed_land": {k: pct(v[ok]) for k, v in
                                     (("R", R), ("R_ired", R_ired), ("K", K), ("LS", LS), ("C", C),
                                      ("A_tpha", A), ("A_ired_tpha", A_ired))},
        "A_mean_tpha": {"main": round(float(np.nanmean(A)), 2), "ired": round(float(np.nanmean(A_ired)), 2),
                        f"tree_C_{TREE_C_ALT:g}": round(float(np.nanmean(a_lo)), 2),
                        **({f"tree_class_average_{C_LOOKUP[TREE]:g}": round(float(np.nanmean(a_avg)), 2)}
                           if split is not None else {})},
        "class_shares_pct_of_assessed": sens,
        **({"tree_split": {"adopted": True, "C": {str(k): v for k, v in split[1].items()},
                           "report": f"reports/tree_split_{AOI_NAME}.json"}} if split is not None else {}),
        "seconds": round(time.time() - t0),
    }
    dest = ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json"
    dest.write_text(json.dumps(summary, indent=2))

    print(f"\n  assessed {summary['assessed_pct_of_state']}% of the state "
          f"({summary['assessed_pct_if_river_land_5m']}% if river land were < 5 m); not assessed: {why_not}")
    for k, v in summary["factors_on_assessed_land"].items():
        print(f"  {k:12} p5 {v['p5']:>10}  p50 {v['p50']:>10}  p95 {v['p95']:>10}")
    print(f"  mean A: {summary['A_mean_tpha']}")
    for k, v in sens.items():
        print(f"  {k:48} " + "  ".join(f"{n[:4]} {s:5.1f}" for n, s in v.items()))
    print(f"\n  wrote {OUT} and {dest.relative_to(ROOT)}  ({summary['seconds']}s)")


if __name__ == "__main__":
    main()
