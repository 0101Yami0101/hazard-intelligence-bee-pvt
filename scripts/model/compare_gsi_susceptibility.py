"""SlideSense's susceptibility against GSI's 50 m national map, on the same cells.

    python scripts/model/compare_gsi_susceptibility.py

Writes  reports/gsi_susceptibility_comparison.json

The method was fixed before this was run (docs/design/GSI_MAP_COMPARISON.md
§1). In short: both maps are marked on the cells the SlideSense model was
tested on — SlideSense by its out-of-fold score (a model that never saw that
cell's region), GSI by its published class read at the cell's centre.

⚠️ GSI's map was built from GSI's own landslide inventory, which is most of
these cells. So GSI is marked on landslides it has seen. The cut that is
fair to both is the landslides only NRSC Bhuvan / APSAC mapped.

⚠️ GSI has three classes, so most pairs of cells tie. roc_auc_score counts a
tie as half — the standard way. Breaking ties any other way is how a
three-class map gets a made-up score (the Bhuvan flood mask once "scored"
0.879 that way).

Reads only; nothing the app uses is written.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1]),
                str(Path(__file__).resolve().parents[1] / "build")]

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from sklearn.metrics import roc_auc_score

import grid as G
from common import CONTEXT, INTERIM, LABELS, PROCESSED, ROOT

warnings.filterwarnings("ignore")
GSI = CONTEXT / "gsi_landslide-susceptibility_50m_arunachal.tif"
OUT = ROOT / "reports" / "gsi_susceptibility_comparison.json"
GSI_NAMES = {1: "Low", 2: "Moderate", 3: "High"}


def gsi_at(x_utm: np.ndarray, y_utm: np.ndarray) -> np.ndarray:
    """GSI's class at each point (0 = no class there)."""
    with rasterio.open(GSI) as src:
        a = src.read(1)
        gx, gy = Transformer.from_crs(G.CRS, src.crs, always_xy=True).transform(x_utm, y_utm)
        r, c = rasterio.transform.rowcol(src.transform, gx, gy)
    r, c = np.asarray(r), np.asarray(c)
    ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
    out = np.zeros(len(r), np.uint8)
    out[ok] = a[r[ok], c[ok]]
    return out


def like_for_like(y: np.ndarray, ours: np.ndarray, gsi: np.ndarray, land: np.ndarray) -> list[dict]:
    """GSI's top class(es) against the same share of land from the top of
    our score. `land`: the cells that stand for the land (non-landslide)."""
    rows = []
    for name, sel in (("High", gsi == 3), ("High + Moderate", gsi >= 2)):
        share = float(sel[land].mean())
        cut = float(np.quantile(ours[land], 1 - share))
        mine = ours >= cut
        rows.append({"gsi_classes": name, "share_of_land": round(share, 4),
                     "gsi_holds_share_of_landslides": round(float(sel[y == 1].mean()), 4),
                     "slidesense_same_land_holds": round(float(mine[y == 1].mean()), 4),
                     "slidesense_land_actually_taken": round(float(mine[land].mean()), 4)})
    return rows


def block(y, ours, gsi, label: str) -> dict:
    land = y == 0
    return {"what": label, "landslide_cells": int((y == 1).sum()), "other_cells": int(land.sum()),
            "ranking_auc": {"slidesense": round(float(roc_auc_score(y, ours)), 4),
                            "gsi_three_classes": round(float(roc_auc_score(y, gsi)), 4)},
            "like_for_like": like_for_like(y, ours, gsi, land),
            "gsi_class_mix": {
                "landslide_cells": {GSI_NAMES[k]: round(float((gsi[y == 1] == k).mean()), 4) for k in (1, 2, 3)},
                "other_cells": {GSI_NAMES[k]: round(float((gsi[land] == k).mean()), 4) for k in (1, 2, 3)}}}


def main() -> None:
    df = pd.read_parquet(PROCESSED / "susceptibility_samples.parquet",
                         columns=["cell_id", "label", "fold", "row", "col", "x_utm", "y_utm"])
    oof = pd.read_parquet(PROCESSED / "susceptibility_oof.parquet")
    assert (df.cell_id.to_numpy() == oof.cell_id.to_numpy()).all(), "sample and scores are not in step"
    df["ours"] = oof.score_oof.to_numpy()
    df["gsi"] = gsi_at(df.x_utm.to_numpy(), df.y_utm.to_numpy())
    with rasterio.open(INTERIM / "labels" / "label_source_cat.tif") as src:
        bits = src.read(1)[df.row.to_numpy(), df.col.to_numpy()]
    df["in_gsi_inventory"] = (bits & 1) > 0
    df["bhuvan_only"] = (bits > 0) & ~df.in_gsi_inventory

    has = df.gsi > 0
    out = {"what": "SlideSense out-of-fold score vs GSI's published 3-class map, same cells",
           "method": "docs/design/GSI_MAP_COMPARISON.md §1 (fixed before the run)",
           "test_cells": int(len(df)),
           "cells_where_gsi_has_a_class": {
               "all": round(float(has.mean()), 4),
               "landslide_cells": round(float(has[df.label == 1].mean()), 4),
               "other_cells": round(float(has[df.label == 0].mean()), 4)},
           "landslide_cells_by_who_mapped_them": {
               "in_gsi_inventory": int((df.in_gsi_inventory & (df.label == 1)).sum()),
               "bhuvan_only": int((df.bhuvan_only & (df.label == 1)).sum())}}
    d = df[has]
    y, ours, gsi = d.label.to_numpy(), d.ours.to_numpy(), d.gsi.to_numpy()
    out["all_cells"] = block(y, ours, gsi, "every test cell where GSI has a class")
    out["by_region"] = []
    for f in sorted(d.fold.unique()):
        m = (d.fold == f).to_numpy()
        out["by_region"].append({"region": int(f), "landslide_cells": int((y[m] == 1).sum()),
                                 "slidesense": round(float(roc_auc_score(y[m], ours[m])), 4),
                                 "gsi": round(float(roc_auc_score(y[m], gsi[m])), 4)})
    # the fair cut: landslides GSI's map-makers did not have, against the same other cells
    m = ((d.label == 0) | d.bhuvan_only).to_numpy()
    out["bhuvan_only_landslides"] = block(y[m], ours[m], gsi[m],
                                          "landslides only Bhuvan/APSAC mapped, against the same other cells")
    m = ((d.label == 0) | d.in_gsi_inventory).to_numpy()
    out["gsi_inventory_landslides"] = block(y[m], ours[m], gsi[m],
                                            "landslides in GSI's own inventory, against the same other cells")

    # where they disagree
    land = y == 0
    half, top10 = np.quantile(ours[land], 0.5), np.quantile(ours[land], 0.9)
    a, b = (gsi == 3) & (ours < half), (gsi == 1) & (ours >= top10)
    base = float(y.mean())
    out["where_they_disagree"] = {
        "share_of_test_cells_that_are_landslides": round(base, 4),
        "gsi_high_but_slidesense_bottom_half": {
            "cells": int(a.sum()), "share_that_are_landslides": round(float(y[a].mean()), 4) if a.any() else None},
        "gsi_low_but_slidesense_top_tenth": {
            "cells": int(b.sum()), "share_that_are_landslides": round(float(y[b].mean()), 4) if b.any() else None}}

    # an outside list: NASA's catalogue, on the shipped map
    with rasterio.open(PROCESSED / "susceptibility.tif") as src:
        full = src.read(1)
    g = gpd.read_file(LABELS / "nasa-glc_landslides_point_arunachal.geojson").to_crs(G.CRS)
    xs, ys = g.geometry.x.to_numpy(), g.geometry.y.to_numpy()
    rr, cc = G.xy_to_rowcol(xs, ys)
    ok = (rr >= 0) & (rr < G.NROWS) & (cc >= 0) & (cc < G.NCOLS)
    xs, ys, rr, cc = xs[ok], ys[ok], rr[ok], cc[ok]
    sc, gk = full[rr, cc], gsi_at(xs, ys)
    both = np.isfinite(sc) & (gk > 0)
    # the land, for this check: every cell SlideSense scores where GSI has a class
    dom = np.isfinite(full)
    r_all, c_all = np.nonzero(dom)
    step = max(len(r_all) // 400_000, 1)                       # a 400,000-cell sample is plenty
    r_s, c_s = r_all[::step], c_all[::step]
    x_s, y_s = rasterio.transform.xy(G.TRANSFORM, r_s, c_s)
    g_s = gsi_at(np.asarray(x_s), np.asarray(y_s))
    s_s = full[r_s, c_s]
    k = g_s > 0
    rows = []
    for name, lo in (("High", 3), ("High + Moderate", 2)):
        share = float((g_s[k] >= lo).mean())
        cut = float(np.quantile(s_s[k], 1 - share))
        rows.append({"gsi_classes": name, "share_of_land": round(share, 4),
                     "points_on_gsi_classes": round(float((gk[both] >= lo).mean()), 4),
                     "points_on_slidesense_same_land": round(float((sc[both] >= cut).mean()), 4)})
    out["nasa_catalogue_points"] = {
        "points_in_the_state": int(ok.sum()), "points_where_both_maps_have_a_value": int(both.sum()),
        "note": "located to about a kilometre; SlideSense's shipped map, not out-of-fold",
        "like_for_like": rows,
        "gsi_has_a_class_on_share_of_scored_land": round(float(k.mean()), 4)}

    OUT.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    print(f"\n  wrote {OUT}")


if __name__ == "__main__":
    main()
