"""Priority list for soil-conservation work: rank catchments and districts.

    $env:REGION = "assam"; python scripts/model/erosion_priority.py [--images]

Every rule here was written down in docs/design/EROSION_PLAN.md ("Step 7, part 1")
before this script first ran:
    units    HydroBASINS level-12 catchments with >= 500 scored cells; districts
    score    mean soil loss (A, t/ha/yr) over the unit's scored cells, main run
    driver   which of rain / soil / slope / cover lifts the unit most above the
             state average (log A = log R + log K + log LS + log C)
    marks    "top under both rain maps" or "depends on the rain source", plus
             the unit's rank under all four runs (2 rain maps x 2 tree C values)
--images also fetches a satellite picture of each top-20 catchment for the eye
check (Esri World Imagery, the app's own satellite base map).

A 100 m cell is 1 ha, so a unit's total soil loss in t/yr is the sum of A.

Outputs
    reports/erosion_priority_<region>.csv            catchments, ranked
    reports/erosion_priority_<region>_districts.csv  districts, ranked
    data/processed/<region>/erosion_priority.gpkg    catchment polygons + columns
    data/interim/<region>/erosion/eyecheck/          top-20 images + contact sheets
"""
from __future__ import annotations

import io
import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

import grid as G
from common import AOI_NAME, BOUNDARIES, HYDROLOGY, INTERIM, PROCESSED, ROOT, UA, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
UNIT_MIN_CELLS, TOP_N = 500, 20
HIGH_TPHA = 10.0                      # "high" class or worse
TREE = 10
DRIVER_NAMES = {"R": "heavy rain", "K": "erodible soil", "LS": "steep or long slopes",
                "C": "bare or thin cover"}
RUNNER_UP_WITHIN = 0.5                # log units
# The second reason, against units of similar steepness (EROSION_PLAN.md,
# "V-18 part 1"): five equal groups by the slope term, then the factor that
# stands most above the group's mean, if by more than PEER_MIN log units.
PEER_GROUPS, PEER_MIN = 5, 0.10
# Typical measures per cause (V-25): a reading aid, to confirm with the department.
HINTS = {"LS": ("contour bunds or trenches", "terraces", "check dams"),
         "C": ("revegetation", "agroforestry", "longer jhum fallows"),
         "R": ("ground cover before the monsoon", "check dams", "gully plugs"),
         "K": ("mulch", "cover crops", "grass strips"),
         # cover on gentle ground (slope groups 1-3): farmland, not jhum
         "C_gentle": ("cover crops", "crop residue left on the field", "grass strips")}
CODE_OF = {v: k for k, v in DRIVER_NAMES.items()}
ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def ids_of(gdf: gpd.GeoDataFrame) -> np.ndarray:
    g = gdf.to_crs(G.CRS)
    return rasterize(((geom, i + 1) for i, geom in enumerate(g.geometry) if geom is not None),
                     out_shape=G.SHAPE, transform=G.TRANSFORM, fill=0, dtype="int32")


def per_unit(ids, n_units, sel, values):
    """Sum of `values` over `sel` cells per unit id (index 0 = no unit)."""
    return np.bincount(ids[sel], weights=values[sel], minlength=n_units + 1)


def table(gdf, ids, layers, inside, ok, min_cells):
    n_units = len(gdf)
    n_ok = np.bincount(ids[ok], minlength=n_units + 1).astype(float)
    n_in = np.bincount(ids[inside], minlength=n_units + 1).astype(float)
    df = pd.DataFrame(index=np.arange(1, n_units + 1))
    df["scored_km2"] = n_ok[1:] / 100
    df["not_scored_pct"] = np.where(n_in[1:] > 0, 100 * (1 - n_ok[1:] / np.maximum(n_in[1:], 1)), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        for run, a in layers["A"].items():
            df[f"meanA_{run}"] = per_unit(ids, n_units, ok, a)[1:] / n_ok[1:]
        A = layers["A"]["main"]
        df["total_t_per_yr"] = per_unit(ids, n_units, ok, A)[1:]
        df["high_or_worse_pct"] = 100 * per_unit(ids, n_units, ok, (A >= HIGH_TPHA).astype(np.float32))[1:] / n_ok[1:]
        # driver: unit mean of log-factor minus state mean of log-factor
        diffs = {}
        for f in ("R", "K", "LS", "C"):
            lg = np.log(np.maximum(layers[f], 1e-3)).astype(np.float64)
            state = float(lg[ok].mean())
            diffs[f] = per_unit(ids, n_units, ok, lg)[1:] / n_ok[1:] - state
            df[f"dlog_{f}"] = diffs[f]
    df = df[df.scored_km2 * 100 >= min_cells].copy()

    def driver(row):
        d = sorted(((row[f"dlog_{f}"], f) for f in ("R", "K", "LS", "C")), reverse=True)
        if d[0][0] <= 0:
            return "none above the state average", ""
        first = DRIVER_NAMES[d[0][1]]
        second = DRIVER_NAMES[d[1][1]] if d[1][0] > 0 and d[0][0] - d[1][0] <= RUNNER_UP_WITHIN else ""
        return first, second
    dr = df.apply(driver, axis=1, result_type="expand")
    df["main_driver"], df["also"] = dr[0], dr[1]
    # second reason, against units of similar steepness
    df["slope_group"] = pd.qcut(df["dlog_LS"].rank(method="first"), PEER_GROUPS,
                                labels=False).astype(int) + 1
    peer = {f: df.groupby("slope_group")[f"dlog_{f}"].transform("mean") for f in ("R", "K", "C")}
    best = pd.concat({f: df[f"dlog_{f}"] - peer[f] for f in ("R", "K", "C")}, axis=1)
    top_f, top_v = best.idxmax(axis=1), best.max(axis=1)
    stands = top_v > PEER_MIN
    df["vs_similar"] = np.where(stands, top_f.map(DRIVER_NAMES), "")
    df["vs_similar_x"] = np.where(stands, np.exp(top_v), np.nan)

    def hint(row):
        codes = [CODE_OF[row.main_driver]] if row.main_driver in CODE_OF else []
        if row.vs_similar and CODE_OF[row.vs_similar] not in codes:
            codes.append(CODE_OF[row.vs_similar])
        codes = ["C_gentle" if c == "C" and row.slope_group <= 3 else c for c in codes]
        return ", ".join(dict.fromkeys(m for c in codes for m in HINTS[c]))
    df["hint"] = df.apply(hint, axis=1)
    for run in layers["A"]:
        df[f"rank_{run}"] = df[f"meanA_{run}"].rank(ascending=False, method="min").astype(int)
    both = (df["rank_main"] <= TOP_N) & (df["rank_ired"] <= TOP_N)
    df["mark"] = np.where(both, "top under both rain maps", "depends on the rain source")
    df.loc[df["rank_main"] > TOP_N, "mark"] = ""        # marks are about the top of the list
    return df.sort_values("rank_main")


def reason(row) -> str:
    s = f"main driver: {row.main_driver}"
    if row.also:
        s += f", then {row.also}"
    if row.vs_similar:
        s += f"; against similar slopes: {row.vs_similar}, {row.vs_similar_x:.1f}x their average"
    return s


def fetch_image(bounds_ll, path: Path, px=900):
    import requests
    w, s, e, n = bounds_ll
    pad = 0.08 * max(e - w, n - s)
    w, s, e, n = w - pad, s - pad, e + pad, n + pad
    asp = (n - s) / (e - w)
    size = f"{px},{max(200, int(px * asp))}"
    r = requests.get(ESRI, params=dict(bbox=f"{w},{s},{e},{n}", bboxSR=4326, imageSR=4326,
                                       size=size, format="jpg", f="image"), headers=UA, timeout=120)
    r.raise_for_status()
    path.write_bytes(r.content)
    return (w, s, e, n)


def images(top: gpd.GeoDataFrame, out: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    g = top.to_crs(4326)
    tiles = []
    for _, row in g.iterrows():
        f = out / f"rank{int(row.rank_main):02d}_{int(row.HYBAS_ID)}.jpg"
        ext = fetch_image(row.geometry.bounds, f)
        tiles.append((row, f, ext))
    for sheet, chunk in enumerate((tiles[:10], tiles[10:20])):
        fig, axes = plt.subplots(2, 5, figsize=(25, 11))
        for ax, (row, f, (w, s, e, n)) in zip(axes.ravel(), chunk):
            ax.imshow(Image.open(f), extent=(w, e, s, n))
            gpd.GeoSeries([row.geometry]).boundary.plot(ax=ax, color="yellow", linewidth=1.2)
            ax.set_xlim(w, e); ax.set_ylim(s, n); ax.set_xticks([]); ax.set_yticks([])
            ax.set_title(f"#{int(row.rank_main)} {row.district} — {row.meanA_main:.0f} t/ha/yr\n"
                         f"{row.main_driver}{', ' + row.also if row.also else ''}", fontsize=10)
        for ax in axes.ravel()[len(chunk):]:
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(out / f"_sheet_{sheet + 1}.png", dpi=70, bbox_inches="tight")
        plt.close(fig)
    print(f"  images: {out}")


def main(want_images: bool) -> None:
    print(f"Erosion priority list — {AOI_NAME}")
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    lc = rd(INTERIM / "features" / "lc_class_cat.tif")
    A, A_ired, A_lo = (rd(E / f"erosion_{n}_tpha.tif") for n in ("A", "A_ired", "A_treeC_alt"))
    with np.errstate(invalid="ignore", divide="ignore"):
        A_ired_lo = np.where(lc == TREE, A_ired * (A_lo / np.where(A > 0, A, np.nan)), A_ired)
    runs = {"main": A, "ired": A_ired, "treeC_alt": A_lo, "ired_treeC_alt": A_ired_lo}
    # Once the tree split is adopted (Phase 1 E1.1), the main run uses it, and
    # the D8 class average (0.03 for all tree land) becomes a comparison run:
    # what the split changed. Decided by the recipe's own report, never by a
    # file merely being present, so a stale raster cannot slip in.
    fac = json.loads((ROOT / "reports" / f"erosion_factors_{AOI_NAME}.json").read_text())
    if fac.get("tree_split", {}).get("adopted") or fac.get("measured_cover", {}).get("adopted"):
        runs["treeC_avg"] = rd(E / "erosion_A_treeC_avg_tpha.tif")
    layers = {"A": runs,
              **{f: rd(E / f"erosion_{f}.tif") for f in ("R", "K", "LS", "C")}}

    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    dist = gpd.read_file(outline("district"))
    bid, did = ids_of(bas), ids_of(dist)

    cat = table(bas, bid, layers, inside, ok, UNIT_MIN_CELLS)
    # each catchment's main district (most scored cells)
    dn = list(dist.NAME_2)
    cat["district"] = [dn[int(np.argmax(np.bincount(did[(bid == i) & ok], minlength=len(dn) + 1)[1:]))]
                       for i in cat.index]
    cat.insert(0, "HYBAS_ID", bas.HYBAS_ID.values[cat.index - 1].astype("int64"))
    cat["reason"] = cat.apply(reason, axis=1)
    dis = table(dist, did, layers, inside, ok, 1)
    dis.insert(0, "district", [dn[i - 1] for i in dis.index])
    dis["reason"] = dis.apply(reason, axis=1)

    rep = ROOT / "reports"
    cols = lambda d: [c for c in d.columns if not c.startswith("dlog_")] + [c for c in d.columns if c.startswith("dlog_")]
    cat[cols(cat)].round(3).to_csv(rep / f"erosion_priority_{AOI_NAME}.csv", index=False)
    dis[cols(dis)].round(3).to_csv(rep / f"erosion_priority_{AOI_NAME}_districts.csv", index=False)

    gpkg = bas.iloc[cat.index - 1].copy()
    for c in cols(cat):
        gpkg[c] = cat[c].values
    PROCESSED.mkdir(parents=True, exist_ok=True)
    gpkg.to_crs(G.CRS).to_file(PROCESSED / "erosion_priority.gpkg", driver="GPKG", layer="catchments")

    top = cat.head(TOP_N)
    print(f"  {len(cat)} catchments ranked; {int((top.mark == 'top under both rain maps').sum())} of the top {TOP_N} "
          f"are top under both rain maps")
    print(f"  {'#':>3} {'district':16} {'km2':>6} {'A':>6} {'high%':>6} {'ired#':>6} {'C.003#':>7}  driver / mark")
    for _, r in top.iterrows():
        print(f"  {r.rank_main:>3} {r.district:16} {r.scored_km2:6.1f} {r.meanA_main:6.1f} {r.high_or_worse_pct:6.1f} "
              f"{r.rank_ired:>6} {r.rank_treeC_alt:>7}  {r.main_driver}{', ' + r.also if r.also else ''} | {r.mark}"
              f" | vs similar: {r.vs_similar or '-'}{f' {r.vs_similar_x:.1f}x' if r.vs_similar else ''}")
    vs = cat.vs_similar.replace("", "nothing stands out")
    print(f"\n  second reason, all {len(cat)} catchments: {vs.value_counts().to_dict()}; "
          f"top {TOP_N}: {vs.head(TOP_N).value_counts().to_dict()}")
    print("\n  districts:")
    for _, r in dis.iterrows():
        print(f"  {r.rank_main:>3} {r.district:20} A {r.meanA_main:6.1f}  high {r.high_or_worse_pct:5.1f}%  "
              f"total {r.total_t_per_yr / 1e6:6.2f} Mt/yr  ired#{r.rank_ired:<3} C.003#{r.rank_treeC_alt:<3} {r.reason}")
    if want_images:
        images(gpkg.head(TOP_N).assign(district=top.district.values), INTERIM / "erosion" / "eyecheck")


if __name__ == "__main__":
    main("--images" in sys.argv)
