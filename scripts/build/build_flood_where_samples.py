"""Turn the 3,546 extracted pixel masks into a flood WHERE training table.

    python scripts/build/build_flood_where_samples.py

Reads   data/interim/flood_where_pixels/<uuid>.npz   (fetch_37 output)
        data/interim/terrain_unmasked/*.tif          (build_unmasked_stack.py)
        data/interim/features/soil_*.tif             (already unclipped)
Writes  data/processed/flood_where_samples.parquet
        data/processed/flood_where_samples.meta.json

════════════════════════════════════════════════════════════════════════════
WHAT ONE ROW IS
════════════════════════════════════════════════════════════════════════════
One row = one 100 m cell, in one flood event. `label` is whether real
Sentinel-1 backscatter showed NEW water there on that event's date — new
meaning water on the flood day that was not water in the same-orbit dry
baseline, so permanent river channel is excluded by construction.

The same cell appears in many events, sometimes flooded and sometimes not.
That is deliberate and is the whole point: the model is learning, from
static terrain alone, what share of real flood events reach this cell.
That share IS the probability we want to end up quoting, which is why this
table can be calibrated into one and the old percentile index could not.

════════════════════════════════════════════════════════════════════════════
THREE CHOICES THAT MATTER
════════════════════════════════════════════════════════════════════════════
1.  POSITIVE = at least 25% of the 100 m cell turned to new water. A single
    stray 10 m pixel is speckle, not a flood. Cells in the ambiguous band
    (some new water, but under the threshold) are DROPPED rather than
    called dry — labelling them 0 would teach the model that genuinely wet
    ground is dry.

2.  NEGATIVES COME FROM THE SAME EVENT'S OWN CROP, not from the state at
    large. The question the model must answer is "given a flood here, which
    ground does the water reach" — so the contrast has to be within the
    event. Negatives drawn statewide would mostly be Himalayan ridge line
    and the model would win by learning "not a mountain top", which is
    useless.

3.  NEGATIVES ARE SUBSAMPLED, positives are all kept. The sampling rate is
    recorded in the meta file so the training step can weight each negative
    by 1/rate and recover the true prevalence exactly — without that the
    calibrated probability would come out inflated by the sampling.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.warp import Resampling, reproject

import grid as G
from common import INTERIM, PROCESSED

PIX = INTERIM / "flood_where_pixels"
STACK = INTERIM / "terrain_unmasked"
SOIL = INTERIM / "features"

POS_FRAC = 0.25          # >= this share of the cell is new water -> positive
COVER_MIN = 0.90         # the crop must cover this much of the 100 m cell
NEG_RATE = 0.15          # keep this share of dry cells
SEED = 42

# Only quantities that physically govern where water goes once it leaves the
# channel. Everything here is a shape: how high above the water, how big the
# river, how flat the ground, how confined the valley.
#
# Absolute elevation, aspect and soil were all tried and REMOVED. None of them
# causes inundation; each is really a label for "which part of the map is
# this", and with 97% of the training rows below 500 m the model used them to
# memorise the Brahmaputra lowland. Asked about Arunachal's mountains it then
# extrapolated, and scored flat ground at 1,700 m as flood-prone because
# lowland-flat and highland-flat look identical once you remove the height.
TERRAIN_FEATS = [
    "terrain_slope_deg", "terrain_slope_max_deg", "terrain_relief_m",
    "terrain_curv_plan", "terrain_curv_prof",
    "hydro_flowacc_cells", "hydro_twi",
    # Height above, size of, and distance to the nearest drainage — at two
    # scales. The trunk pair (>=100 km2) describes the Brahmaputra and the
    # Siang; the small pair (>=10 km2) describes the creek that actually
    # floods a Tawang village. Without the small scale a hillside hamlet
    # reads as hundreds of metres above water and can never be flooded.
    "hydro_hand_m", "hydro_chan_km2", "dist_chan_m",
    "hydro_hand_small_m", "hydro_chan_small_km2", "dist_chan_small_m",
    # Valley confinement: relief and mean slope within ~1 km. Tells a narrow
    # mountain valley floor from the open plain (build_unmasked_stack.py).
    "terrain_relief_2km_m", "terrain_slope_2km_deg",
]
SOIL_FEATS: list[str] = []
CAT_FEATS: list[str] = []

# ESA WorldCover is built and stored, but deliberately NOT used as a feature.
# It is the strongest predictor in the table and it fails in exactly the place
# the pilot needs it. Its classes were learnt on the floodplain, where
# "permanent water" is river channel and "bare/sparse" is river sandbar — both
# genuinely flood-prone. At 3,000 m the same two codes mean glacial lake and
# scree, so a model leaning on them scores high-altitude Tawang as floodable.
# Measured: with land cover in, the top-scoring cells statewide had a median
# HAND of 360 m and half of them were class 80 — glacial lakes. Kept as a
# column for diagnosis, out of the feature list.
#
# Elevation is kept on the same terms: it is the variable that exposes the
# training set's lowland bias, so it has to stay readable even though the
# model must not use it.
DIAG_FEATS = ["lc_class_cat", "dem_elev_m"]


SOURCE_REPORTS = [
    "flood_where_groundsource_s1_ee_screen.json",
    "flood_where_groundsource_pre2019_s1_ee_screen.json",
    "flood_where_groundsource_widewindow_recheck.json",
]


def candidate_dates() -> dict[str, str]:
    """uuid -> reported flood date, from the same screen reports fetch_37
    read its candidates from (first report wins, as it did there)."""
    from common import ROOT
    out: dict[str, str] = {}
    for name in SOURCE_REPORTS:
        d = json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))
        for r in d["results"]:
            if r.get("screen_positive") and r["uuid"] not in out:
                out[r["uuid"]] = r["date_str"]
    return out


def load_stack() -> dict[str, np.ndarray]:
    out = {}
    for name in TERRAIN_FEATS + CAT_FEATS + DIAG_FEATS:
        with rasterio.open(STACK / f"{name}.tif") as s:
            out[name] = s.read(1)
    for name in SOIL_FEATS:
        with rasterio.open(SOIL / f"{name}.tif") as s:
            out[name] = s.read(1)
    return out


def event_grid(path: Path, to3857: Transformer, to_utm: Transformer):
    """Reproject one event's new-water mask onto the canonical 100 m grid.
    Returns (r0, c0, nw_frac, cover) or None if it misses the grid."""
    d = np.load(path)
    nw = d["nw"].astype(np.float32)
    lat, lon = float(d["lat"]), float(d["lon"])
    half, scale = int(d["half_m"]), int(d["scale_m"])

    x, y = to3857.transform(lon, lat)
    src_tf = Affine(scale, 0, x - half, 0, -scale, y + half)

    xs, ys = to_utm.transform([x - half, x + half, x - half, x + half],
                              [y - half, y - half, y + half, y + half])
    c0 = int(np.floor((min(xs) - G.ORIGIN_X) / G.CELL))
    c1 = int(np.ceil((max(xs) - G.ORIGIN_X) / G.CELL))
    r0 = int(np.floor((G.TOP_Y - max(ys)) / G.CELL))
    r1 = int(np.ceil((G.TOP_Y - min(ys)) / G.CELL))
    c0, c1 = max(0, c0), min(G.NCOLS, c1)
    r0, r1 = max(0, r0), min(G.NROWS, r1)
    if c1 <= c0 or r1 <= r0:
        return None

    h, w = r1 - r0, c1 - c0
    dst_tf = G.TRANSFORM * Affine.translation(c0, r0)
    frac = np.zeros((h, w), np.float32)
    cover = np.zeros((h, w), np.float32)
    reproject(nw, frac, src_transform=src_tf, src_crs="EPSG:3857",
              dst_transform=dst_tf, dst_crs=G.CRS,
              resampling=Resampling.average, dst_nodata=0)
    reproject(np.ones_like(nw), cover, src_transform=src_tf, src_crs="EPSG:3857",
              dst_transform=dst_tf, dst_crs=G.CRS,
              resampling=Resampling.average, dst_nodata=0)
    return r0, c0, frac, cover, lat, lon


def main() -> None:
    t0 = time.time()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("Flood WHERE — building the training table")

    stack = load_stack()
    finite = np.isfinite(stack["hydro_hand_m"]) & np.isfinite(stack["terrain_slope_deg"])
    print(f"  feature stack loaded, {100*finite.mean():.1f}% of the grid has terrain")

    to3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_utm = Transformer.from_crs("EPSG:3857", G.CRS, always_xy=True)
    rng = np.random.default_rng(SEED)

    files = sorted(PIX.glob("*.npz"))
    print(f"  {len(files):,} extracted events\n")

    parts = []
    n_skip_grid = n_skip_small = 0
    n_dry_total = n_dry_kept = 0
    ev_rows = []

    for i, p in enumerate(files, 1):
        g = event_grid(p, to3857, to_utm)
        if g is None:
            n_skip_grid += 1
            continue
        r0, c0, frac, cover, lat, lon = g
        h, w = frac.shape
        sub = (slice(r0, r0 + h), slice(c0, c0 + w))
        ok = (cover >= COVER_MIN) & finite[sub]
        if ok.sum() < 100:
            n_skip_small += 1
            continue

        f = frac[ok]
        pos = f >= POS_FRAC
        dry = f <= 0.0
        n_dry_total += int(dry.sum())

        keep = pos.copy()
        if dry.any():
            draw = rng.random(dry.sum()) < NEG_RATE
            idx_dry = np.flatnonzero(dry)
            keep[idx_dry[draw]] = True
            n_dry_kept += int(draw.sum())
        if not keep.any():
            continue

        rr, cc = np.nonzero(ok)
        rr, cc = rr[keep] + r0, cc[keep] + c0
        lab = pos[keep].astype(np.uint8)

        rec = {"event": np.full(rr.shape, i - 1, dtype=np.int32),
               "row": rr.astype(np.int32), "col": cc.astype(np.int32),
               "label": lab, "nw_frac": f[keep].astype(np.float32)}
        for name, arr in stack.items():
            rec[name] = arr[rr, cc]
        parts.append(pd.DataFrame(rec))
        ev_rows.append({"event": i - 1, "uuid": p.stem, "lat": lat, "lon": lon,
                        "n_cells_covered": int(ok.sum()),
                        "n_pos": int(pos.sum()), "n_dry": int(dry.sum())})

        if i % 250 == 0 or i == len(files):
            print(f"    {i:>5}/{len(files)}  kept {sum(len(x) for x in parts):>10,} rows"
                  f"   {time.time()-t0:.0f}s", flush=True)

    df = pd.concat(parts, ignore_index=True)
    del parts

    # Spatial block folds — whole 50 km blocks are held out together. Grouping
    # by event would NOT be enough: different events overlap the same ground,
    # and because the features are static a cell seen in training would leak
    # its answer straight into the test fold.
    block = G.fold_block(df["row"].to_numpy(), df["col"].to_numpy())
    ub = np.unique(block)
    fold_of = {b: int(f) for b, f in
               zip(ub, np.random.default_rng(G.FOLD_SEED).integers(0, G.N_FOLDS, len(ub)))}
    df["fold"] = pd.Series(block).map(fold_of).astype(np.int8)
    df["cell_id"] = G.encode(df["row"].to_numpy(), df["col"].to_numpy())

    # Each kept negative stands for 1/NEG_RATE real dry cells. Carrying that
    # weight is what lets the trained score be calibrated back to the true
    # prevalence instead of the sampled one.
    df["weight"] = np.where(df["label"] == 1, 1.0, 1.0 / NEG_RATE).astype(np.float32)

    ev = pd.DataFrame(ev_rows)
    true_prev = df.loc[df.label == 1, "weight"].sum() / df["weight"].sum()

    print(f"\n  rows                 {len(df):,}")
    print(f"  events used          {df.event.nunique():,} of {len(files):,}"
          f"   (skipped {n_skip_grid} off-grid, {n_skip_small} too small)")
    print(f"  positives            {int((df.label==1).sum()):,}")
    print(f"  negatives kept       {int((df.label==0).sum()):,} of {n_dry_total:,} dry "
          f"({100*NEG_RATE:.0f}% sample)")
    print(f"  sampled prevalence   {100*df.label.mean():.2f}%")
    print(f"  TRUE prevalence      {100*true_prev:.2f}%   (weight-corrected)")
    print(f"  fold sizes           {df.fold.value_counts().sort_index().to_dict()}")

    out = PROCESSED / "flood_where_samples.parquet"
    df.to_parquet(out, index=False, compression="zstd")
    ev.to_parquet(PROCESSED / "flood_where_events.parquet", index=False)

    (PROCESSED / "flood_where_samples.meta.json").write_text(json.dumps({
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_rows": int(len(df)), "n_events_used": int(df.event.nunique()),
        "n_events_available": len(files),
        "pos_frac_threshold": POS_FRAC, "cover_min": COVER_MIN,
        "neg_sample_rate": NEG_RATE, "seed": SEED,
        "n_dry_total": n_dry_total, "n_dry_kept": n_dry_kept,
        "sampled_prevalence": float(df.label.mean()),
        "true_prevalence_weighted": float(true_prev),
        "features_terrain": TERRAIN_FEATS, "features_soil": SOIL_FEATS,
        "features_categorical": CAT_FEATS,
        "columns_kept_but_not_features": DIAG_FEATS,
        "geology_dropped": ("APSSDI geology is Arunachal-only; the flood "
                            "training set extends past the state line, so it "
                            "cannot be used without reintroducing the clip"),
        "landcover_dropped": ("ESA WorldCover class meanings do not transfer "
                             "from floodplain to high mountain: 'permanent "
                             "water' is river channel at 200 m and glacial "
                             "lake at 3,000 m, 'bare/sparse' is sandbar then "
                             "scree. With it in the feature set the highest-"
                             "scoring cells statewide were glacial lakes and "
                             "ridges at a median HAND of 360 m"),
        "label_meaning": (">=25% of the 100 m cell showed Sentinel-1 new water "
                          "on the event date, relative to a same-orbit dry baseline"),
    }, indent=2))
    print(f"\n  wrote {out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
