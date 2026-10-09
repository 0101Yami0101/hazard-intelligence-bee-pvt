"""Score every 100 m cell in Arunachal with the calibrated flood WHERE model.

    python scripts/model/predict_flood_where.py

Reads   models/flood_where/full.txt + calibrator_isotonic.pkl
Writes  data/processed/flood_where_prob_100m.tif    the real output
        webapp/assets/flood/floodprob.npz           display copy

════════════════════════════════════════════════════════════════════════════
WHAT THE NUMBER ON THIS MAP MEANS
════════════════════════════════════════════════════════════════════════════
For each 100 m cell: the share of real flood events reaching this catchment
that put water on this specific ground. 0.73 means roughly 73 of every 100
such events flooded it — checked against held-out events, not asserted.

It is CONDITIONAL on a flood happening nearby. It is not an annual chance of
flooding, and it must not be presented as one. The unconditional answer needs
this map multiplied by the WHEN model's event probability — that product is
the actual forecast, and the two halves are deliberately kept separate so
each can be checked on its own.

This replaces `floodprone.npz`, a rule-based percentile index whose classes
were only ever a ranking. Both are written, so the webapp can show them side
by side until the new one has been reviewed.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

import grid as G
from common import INTERIM, PROCESSED, ROOT

MODELS = ROOT / "models" / "flood_where"
STACK = INTERIM / "terrain_unmasked"
SOIL = INTERIM / "features"
WEB = ROOT / "webapp" / "assets" / "flood"
BASE = ROOT / "webapp" / "assets" / "base"

CHUNK_ROWS = 200

# Water does not stand far above its own channel. This is not a tuning knob:
# measured on our own 1.4 M real flooded cells, 99.68% sit within 10 m of the
# nearest drainage and 99.89% within 25 m. Above the ceiling the probability
# is set to zero rather than left to the model, because up there the model is
# extrapolating - 97% of its training rows are below 500 m elevation, so it
# has almost no evidence about high mountain ground and will happily score a
# flat shelf at 1,700 m like a floodplain.
#
# The ceiling is applied to the SMALLER of the two HANDs: a village can be
# 30 m above its own creek and 400 m above the trunk river, and it is the
# creek that floods it.
HAND_CEILING_M = 25.0


def score_grid(model_dir: Path = MODELS, clip_to_state: bool = True,
               verbose: bool = True) -> tuple[np.ndarray, dict]:
    """Calibrated WHERE probability on the full 100 m grid. NaN = no terrain
    (or outside the state, when clipped); 0 = above the physical ceiling."""
    t0 = time.time()
    booster = lgb.Booster(model_file=str(model_dir / "full.txt"))
    with open(model_dir / "calibrator_isotonic.pkl", "rb") as fh:
        iso = pickle.load(fh)
    meta = json.loads((model_dir / "_meta.json").read_text())
    feats = meta["features"]
    cats = meta["categorical"]
    if verbose:
        print(f"  {len(feats)} features, model has {booster.num_trees()} trees")

    # LightGBM splits a categorical on its internal CODE, not on the raw class
    # number. Training built those codes with `astype("category")`, whose
    # categories are the sorted unique values of the training column — so the
    # exact same set has to be rebuilt here or every land-cover split silently
    # reads the wrong class.
    cat_levels = {
        c: pd.unique(pd.read_parquet(PROCESSED / "flood_where_samples.parquet",
                                     columns=[c])[c].dropna())
        for c in cats
    }
    for c in cats:
        cat_levels[c] = np.sort(cat_levels[c])
        print(f"  {c}: {len(cat_levels[c])} classes {list(cat_levels[c])}")

    srcs = {}
    for name in feats:
        p = STACK / f"{name}.tif"
        if not p.exists():
            p = SOIL / f"{name}.tif"
        srcs[name] = rasterio.open(p)

    if clip_to_state:
        with rasterio.open(INTERIM / "state_mask.tif") as m:
            instate = m.read(1).astype(bool)
    else:
        instate = np.ones(G.SHAPE, dtype=bool)

    hand_src = {n: rasterio.open(STACK / f"{n}.tif")
                for n in ("hydro_hand_m", "hydro_hand_small_m")}

    prob = np.full(G.SHAPE, np.nan, dtype=np.float32)
    n_gated = n_live = 0
    for r0 in range(0, G.NROWS, CHUNK_ROWS):
        r1 = min(r0 + CHUNK_ROWS, G.NROWS)
        win = rasterio.windows.Window(0, r0, G.NCOLS, r1 - r0)
        cols = {n: s.read(1, window=win) for n, s in srcs.items()}
        hand_min = np.minimum(hand_src["hydro_hand_m"].read(1, window=win),
                              hand_src["hydro_hand_small_m"].read(1, window=win))
        valid = instate[r0:r1] & np.isfinite(hand_min) \
            & np.isfinite(cols["terrain_slope_deg"])
        # Everything valid gets a number; ground above the ceiling gets zero
        # rather than a model guess.
        prob[r0:r1][valid] = 0.0
        ok = valid & (hand_min <= HAND_CEILING_M)
        n_gated += int((valid & ~ok).sum())
        n_live += int(ok.sum())
        if not ok.any():
            continue
        X = pd.DataFrame({n: cols[n][ok].astype(np.float32) for n in feats})
        for c in cats:
            X[c] = pd.Categorical(cols[c][ok], categories=cat_levels[c])
        raw = booster.predict(X)
        prob[r0:r1][ok] = iso.predict(raw).astype(np.float32)
        if verbose and (r0 // CHUNK_ROWS) % 4 == 0:
            print(f"    rows {r0:>5}-{r1:<5} {time.time()-t0:>5.0f}s", flush=True)

    for s in list(srcs.values()) + list(hand_src.values()):
        s.close()
    return prob, {"meta": meta, "n_live": n_live, "n_gated": n_gated}


def main() -> None:
    t0 = time.time()
    print("Flood WHERE — scoring the state")
    prob, info = score_grid()
    meta, n_live, n_gated = info["meta"], info["n_live"], info["n_gated"]

    live = np.isfinite(prob)
    v = prob[live]
    print(f"\n  scored {live.sum():,} cells in state")
    print(f"    {n_live:,} within {HAND_CEILING_M:.0f} m of a channel — model scored")
    print(f"    {n_gated:,} above it — set to zero by the physical ceiling "
          f"({100*n_gated/max(1,n_gated+n_live):.1f}% of the state)")
    for q in (50, 90, 99, 99.9):
        print(f"    p{q:<5} {np.percentile(v, q):.4f}")
    print(f"    mean  {v.mean():.4f}   share above 0.5: {100*(v>0.5).mean():.3f}%")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    profile = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1,
                   dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
                   nodata=np.nan, compress="deflate", tiled=True,
                   blockxsize=256, blockysize=256)
    out = PROCESSED / "flood_where_prob_100m.tif"
    with rasterio.open(out, "w", **profile) as d:
        d.write(prob, 1)
    print(f"  wrote {out}")

    write_web_layer(prob, meta)
    print(f"  ({time.time()-t0:.0f}s)")


# Thresholds the web screen reports ground area at (share of a flood's
# water reaching a 100 m cell).
AREA_CUTS = (0.02, 0.05, 0.10, 0.20, 0.30)


def web_meta(prob: np.ndarray, meta: dict, shown_check: dict | None = None) -> dict:
    """floodprob.json: what the layer means, plus every number its screen
    quotes — computed here from the 100 m layer and the model's own records,
    never typed into the app.

    `prob` is the in-state 100 m layer as SHOWN (NaN outside the state).
    `shown_check` is Gate B's report when the terrain second stage is shipped:
    the top-range check then comes from it (the second-stage, cross-fitted
    figures), not from the first-stage training report."""
    v = prob[np.isfinite(prob)]
    if shown_check is None:
        cal = meta.get("calibration", {}).get("reliability_after_in_arunachal", [])
        top = [{"p_lo": round(b["p_lo"], 4), "p_hi": round(b["p_hi"], 4),
                "said": round(b["predicted"], 4), "happened": round(b["observed"], 4)}
               for b in cal[-2:]]
    else:
        after = shown_check["results"]["after_in_arunachal"]
        los = [b["lo"] for b in after] + [1.0]
        top = [{"p_lo": b["lo"], "p_hi": min(los[i + 1], 1.0),
                "said": round(b["said_pct"] / 100, 4),
                "happened": round(b["happened_pct"] / 100, 4)}
               for i, b in enumerate(after) if b["lo"] >= 0.05 and b["flooded_rows"] >= 20]
    return {
        "scale": 10000, "nodata": 65535,
        # WHERE is trained on 10 km crops centred on flood reports (their radar
        # screen filters out little, PARKED §0w), so its condition is "a
        # reported flood within ~5 km" — not "a flood anywhere in the
        # catchment", as this line used to say.
        "meaning": ("calibrated probability a 100 m cell is under water GIVEN a "
                    "flood reported within about 5 km (labels: new water on radar images "
                    "around the report); display cells report the MAX of the 100 m cells "
                    "inside them"
                    + ("; SHOWN chance = second stage by terrain setting (open plain / "
                       "valley), which passed Gate B — the model's own layer is unchanged"
                       if shown_check else "")),
        "second_stage": bool(shown_check),
        "not": "an annual flood chance - multiply by the WHEN forecast for that",
        "model": "models/flood_where/full.txt + calibrator_isotonic.pkl",
        "trained_utc": meta["trained_utc"],
        "oof_auc_in_arunachal": meta["pooled_oof"]["in_arunachal"]["auc"],
        "oof_auc_steep": meta["pooled_oof"]["steep"]["auc"],
        "n_floods_trained_on": meta.get("n_events"),
        "area_km2_in_state": {f"{t:.2f}": round(float((v >= t).sum()) * 0.01, 1)
                              for t in AREA_CUTS},
        # The highest ranges of the cross-fitted check inside Arunachal —
        # first stage: where it over-promised (FLOOD_SCREEN_PLAN.md §5,
        # Phase 3); second stage: what it says now.
        "checked_in_arunachal_top": top,
    }


SHOWN_TIF = PROCESSED / "flood_where_prob_100m_shown.tif"
SECOND_STAGE = MODELS / "second_stage_terrain.pkl"


def write_web_layer(prob: np.ndarray | None = None, meta: dict | None = None) -> None:
    """The display copy on the web grid, plus floodprob.json.

    If the terrain second stage has passed Gate B (check_where_topend.py
    apply), the chance SHOWN is the second-stage one — written beside the
    model's layer as flood_where_prob_100m_shown.tif. The model's own layer
    (flood_where_prob_100m.tif) stays first-stage: it is what the day model's
    floodable area and the joined forecast are built from, so shipping the
    second stage moves no forecast number."""
    if prob is None:
        with rasterio.open(PROCESSED / "flood_where_prob_100m.tif") as s:
            prob = s.read(1)
    if meta is None:
        meta = json.loads((MODELS / "_meta.json").read_text())
    shown, check = prob, None
    if SECOND_STAGE.exists():
        import pickle
        from check_where_topend import REPORT, apply_curves
        with open(SECOND_STAGE, "rb") as fh:
            shown = apply_curves(prob, pickle.load(fh))
        check = json.loads(REPORT.read_text())
        profile = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1,
                       dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
                       nodata=np.nan, compress="deflate", tiled=True,
                       blockxsize=256, blockysize=256)
        with rasterio.open(SHOWN_TIF, "w", **profile) as d:
            d.write(shown, 1)

    # MAX, not mean: a floodplain is often one or two 100 m cells wide, and a
    # display cell is ~550 m across. Averaging would dilute a real narrow
    # flood corridor into nothing. Same choice build_flood_layers.py made.
    g = json.loads((BASE / "grid.json").read_text())
    gh, gw = g["height"], g["width"]
    dst_tf = from_bounds(g["west"], g["south"], g["east"], g["north"], gw, gh)
    web = np.full((gh, gw), np.nan, dtype=np.float32)
    reproject(source=shown, destination=web,
              src_transform=G.TRANSFORM, src_crs=G.CRS,
              dst_transform=dst_tf, dst_crs="EPSG:4326",
              src_nodata=np.nan, dst_nodata=np.nan,
              resampling=Resampling.max)
    WEB.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        WEB / "floodprob.npz",
        prob=np.where(np.isfinite(web), np.clip(web * 10000, 0, 10000), 65535).astype(np.uint16))
    (WEB / "floodprob.json").write_text(json.dumps(web_meta(shown, meta, check), indent=2))
    print(f"  wrote {WEB / 'floodprob.npz'}"
          + ("  (second stage: the shown chance)" if check else ""))


def meta_only() -> None:
    """Rebuild the web copy and floodprob.json from the layer already on
    disk, without re-scoring the state."""
    write_web_layer()


if __name__ == "__main__":
    meta_only() if "--meta-only" in sys.argv else main()
