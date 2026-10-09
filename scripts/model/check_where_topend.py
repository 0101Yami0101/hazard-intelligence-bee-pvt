"""Does "if a flood comes, chance this spot is under water" say what happens
inside Arunachal — and does a second, terrain-setting step make it? (Gate B)

    python scripts/model/check_where_topend.py          # the test (changes nothing)
    python scripts/model/check_where_topend.py apply    # only after a PASS

Reads   models/flood_where/fold{0..4}.txt, calibrator_isotonic.pkl, _meta.json
        data/processed/flood_where_samples.parquet (the training table)
        data/processed/flood_where_prob_100m.tif   (the shipped layer)
Writes  reports/flood_where_topend_check.json
        data/processed/flood_where_prob_100m_shown.tif  (the candidate layer)
        reports/flood_where_sanity_shown.json            (B4, on that layer)
  apply models/flood_where/second_stage_terrain.pkl
        webapp/assets/flood/floodprob.npz + floodprob.json (the shown layer)

════════════════════════════════════════════════════════════════════════════
THE PROBLEM
════════════════════════════════════════════════════════════════════════════
WHERE is calibrated on the whole training table, which is mostly open
Brahmaputra plain. Checked out-of-fold inside Arunachal, its top ranges come
true about half as often as they say (11.9% -> 5.9%, 23.3% -> 12.6%) — the
same "too much water given a flood in the mountains" found in PARKED §0p.

THE TEST (pre-registered, FLOOD_SCREEN_PLAN.md Phase 3)
    groups   open: relief within ~2 km < 50 m; valley: >= 50 m
    step 2   per group, isotonic from the first-stage calibrated chance to the
             observed share; cross-fitted over the same 5 spatial folds
    B1       inside Arunachal, pooled: ranges >= 5% with >= 20 flooded rows
             within +-30%; lower ranges within x2
    B2       the >= 5% ranges together within +-30% in every fold and every
             year block (2015-18, 2019-21, 2022-25) holding >= 20 flooded rows
    B3       outside Arunachal, calibration error not > 10% worse
    B4       the physical sanity checks pass on the recalibrated map

If it passes, it changes only the number SHOWN and the screen's low-ground
mask. The model's own WHERE — the day model's floodable-area input and the
joined product — stays as it is, so no forecast number moves.
"""
from __future__ import annotations

import json
import pickle
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from sklearn.isotonic import IsotonicRegression

from common import INTERIM, PROCESSED, ROOT

MODELS = ROOT / "models" / "flood_where"
REPORT = ROOT / "reports" / "flood_where_topend_check.json"
SHOWN_TIF = PROCESSED / "flood_where_prob_100m_shown.tif"
CURVES = MODELS / "second_stage_terrain.pkl"
RELIEF = INTERIM / "terrain_unmasked" / "terrain_relief_2km_m.tif"

VALLEY_RELIEF_M = 50.0
EDGES = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 1.01]
TOP = 0.05
MIN_POS = 20
B1_TOP, B1_LOW, B2_TOP, B3_WORSE = 0.30, 2.0, 0.30, 1.10
YEAR_BLOCKS = [(2015, 2018), (2019, 2021), (2022, 2025)]


def _iso() -> IsotonicRegression:
    return IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")


def reliability(y, p, w, pos) -> list[dict]:
    out = []
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        m = (p >= lo) & (p < hi)
        if not m.any():
            continue
        said, happened = float(np.average(p[m], weights=w[m])), float(np.average(y[m], weights=w[m]))
        out.append({"range": f"{100*lo:g}-{100*min(hi, 1):g}%", "lo": lo, "rows": int(m.sum()),
                    "flooded_rows": int(pos[m].sum()), "said_pct": round(100 * said, 3),
                    "happened_pct": round(100 * happened, 3),
                    "happened_over_said": round(happened / said, 3) if said > 0 else None})
    return out


def ece(y, p, w, n_bins: int = 12) -> float:
    """Weighted, over equal-count bins — the training report's definition."""
    order = np.argsort(p)
    err, tot = 0.0, 0.0
    for idx in np.array_split(order, n_bins):
        if len(idx) == 0:
            continue
        ww = w[idx]
        err += abs(np.average(p[idx], weights=ww) - np.average(y[idx], weights=ww)) * ww.sum()
        tot += ww.sum()
    return err / tot


def top_ratio(y, p, w, pos, m) -> dict:
    s = m & (p >= TOP)
    if s.sum() == 0:
        return {"flooded_rows": 0}
    said, happened = np.average(p[s], weights=w[s]), np.average(y[s], weights=w[s])
    return {"flooded_rows": int(pos[s].sum()), "said_pct": round(100 * said, 3),
            "happened_pct": round(100 * happened, 3),
            "happened_over_said": round(happened / said, 3) if said > 0 else None,
            "judged": bool(pos[s].sum() >= MIN_POS)}


def load_table():
    meta_in = json.loads((PROCESSED / "flood_where_samples.meta.json").read_text())
    feats = meta_in["features_terrain"] + meta_in["features_soil"] + meta_in["features_categorical"]
    df = pd.read_parquet(PROCESSED / "flood_where_samples.parquet")
    # the production model was trained without the braided-channel suspects
    sus = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
              ["channel_shift_suspects"]["uuids"])
    ev = pd.read_parquet(PROCESSED / "flood_where_events.parquet")
    df = df[~df["event"].isin(set(ev.loc[ev["uuid"].isin(sus), "event"]))].reset_index(drop=True)
    from build_flood_where_samples import candidate_dates
    dmap = candidate_dates()
    year = pd.to_datetime(ev.set_index("event")["uuid"].map(dmap)).dt.year
    df["year"] = df["event"].map(year).to_numpy()
    return df, feats


def check() -> dict:
    t0 = time.time()
    print("If a flood comes — Arunachal top ranges, terrain second stage (Gate B)\n")
    df, feats = load_table()
    with rasterio.open(INTERIM / "state_mask.tif") as s:
        inst = s.read(1).astype(bool)
    ap = inst[df["row"].to_numpy(), df["col"].to_numpy()]
    y = df["label"].to_numpy().astype(np.float64)
    w = df["weight"].to_numpy().astype(np.float64)
    pos = y == 1
    fold = df["fold"].to_numpy()
    valley = df["terrain_relief_2km_m"].to_numpy() >= VALLEY_RELIEF_M
    print(f"  {len(df):,} rows, {df.event.nunique():,} events; inside Arunachal "
          f"{ap.mean():.1%}; valley rows {valley.mean():.1%} "
          f"(inside Arunachal {valley[ap].mean():.1%})")

    # out-of-fold raw scores from the saved fold models, then the first-stage
    # calibration cross-fitted exactly as training did
    oof = np.full(len(df), np.nan)
    for f in sorted(np.unique(fold)):
        b = lgb.Booster(model_file=str(MODELS / f"fold{int(f)}.txt"))
        m = fold == f
        oof[m] = b.predict(df.loc[m, feats])
    cal = np.full(len(df), np.nan)
    for f in np.unique(fold):
        m = fold == f
        cal[m] = _iso().fit(oof[~m], y[~m], sample_weight=w[~m]).predict(oof[m])
    print(f"  first stage reproduced ({time.time()-t0:.0f}s)")

    # the second stage, cross-fitted over the same folds, per terrain group
    cal2 = np.full(len(df), np.nan)
    for f in np.unique(fold):
        for g in (False, True):
            tr = (fold != f) & (valley == g)
            te = (fold == f) & (valley == g)
            if te.any():
                cal2[te] = _iso().fit(cal[tr], y[tr], sample_weight=w[tr]).predict(cal[te])

    res = {"before_in_arunachal": reliability(y[ap], cal[ap], w[ap], pos[ap]),
           "after_in_arunachal": reliability(y[ap], cal2[ap], w[ap], pos[ap])}
    after = res["after_in_arunachal"]
    b1 = all((b["happened_over_said"] is not None and
              ((1 - B1_TOP) <= b["happened_over_said"] <= (1 + B1_TOP) if b["lo"] >= TOP
               else 1 / B1_LOW <= b["happened_over_said"] <= B1_LOW))
             for b in after if b["flooded_rows"] >= MIN_POS)
    judged_top = [b for b in after if b["lo"] >= TOP and b["flooded_rows"] >= MIN_POS]
    b1 = bool(b1 and judged_top)

    b2_parts = {}
    for f in sorted(np.unique(fold)):
        b2_parts[f"fold {int(f)}"] = top_ratio(y, cal2, w, pos, ap & (fold == f))
    yr = df["year"].to_numpy()
    for lo, hi in YEAR_BLOCKS:
        b2_parts[f"{lo}-{hi}"] = top_ratio(y, cal2, w, pos, ap & (yr >= lo) & (yr <= hi))
    judged = [v for v in b2_parts.values() if v.get("judged")]
    b2 = bool(judged and all((1 - B2_TOP) <= v["happened_over_said"] <= (1 + B2_TOP) for v in judged))

    out_ap = ~ap
    e_before, e_after = ece(y[out_ap], cal[out_ap], w[out_ap]), ece(y[out_ap], cal2[out_ap], w[out_ap])
    b3 = bool(e_after <= B3_WORSE * e_before)
    res["b2_top_ranges_by_fold_and_year"] = b2_parts
    res["ece_outside_arunachal"] = {"before": round(e_before, 5), "after": round(e_after, 5)}
    res["ece_in_arunachal"] = {"before": round(ece(y[ap], cal[ap], w[ap]), 5),
                               "after": round(ece(y[ap], cal2[ap], w[ap]), 5)}

    # production curves: the SHIPPED first-stage calibrator applied to the
    # out-of-fold scores, so the curve sees values made the way the shipped
    # layer's are
    with open(MODELS / "calibrator_isotonic.pkl", "rb") as fh:
        iso_full = pickle.load(fh)
    stage1 = iso_full.predict(oof)
    curves = {"valley_relief_m": VALLEY_RELIEF_M,
              "open": _iso().fit(stage1[~valley], y[~valley], sample_weight=w[~valley]),
              "valley": _iso().fit(stage1[valley], y[valley], sample_weight=w[valley])}

    # B4: build the candidate layer and run the physical checks on it
    with rasterio.open(PROCESSED / "flood_where_prob_100m.tif") as s:
        prob, prof = s.read(1), s.profile
    shown = apply_curves(prob, curves)
    with rasterio.open(SHOWN_TIF, "w", **prof) as d:
        d.write(shown, 1)
    sanity = subprocess.run([sys.executable, str(Path(__file__).parent / "check_flood_where_sanity.py"),
                             "--prob", str(SHOWN_TIF), "--out", "flood_where_sanity_shown.json"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    b4 = sanity.returncode == 0
    print(sanity.stdout[-900:])

    gate = {"B1_pooled_in_arunachal": b1, "B2_stable_by_fold_and_year": b2,
            "B3_outside_not_worse": b3, "B4_physical_checks": b4}
    passed = all(gate.values())
    live = np.isfinite(prob)
    area = {f"{t:.2f}": {"model_km2": round(float((prob[live] >= t).sum()) * 0.01, 1),
                         "shown_km2": round(float((shown[live] >= t).sum()) * 0.01, 1)}
            for t in (0.05, 0.10, 0.20)}
    out = {"what": ("WHERE's shown chance inside Arunachal: first stage vs a second stage by "
                    "terrain setting (open < 50 m relief within ~2 km, valley >= 50 m), "
                    "cross-fitted over the 5 spatial folds; pre-registered in "
                    "FLOOD_SCREEN_PLAN.md Phase 3"),
           "gate": gate, "GATE_B_PASS": bool(passed), "results": res,
           "state_area_at_or_above": area}
    REPORT.write_text(json.dumps(out, indent=2))
    with open(MODELS / "_second_stage_candidate.pkl", "wb") as fh:
        pickle.dump(curves, fh)
    _print(out)
    print(f"\n  wrote {REPORT}  ({time.time()-t0:.0f}s)")
    return out


def apply_curves(prob: np.ndarray, curves: dict) -> np.ndarray:
    """The second stage on the 100 m layer: each cell by its terrain group."""
    with rasterio.open(RELIEF) as s:
        relief = s.read(1)
    out = np.full(prob.shape, np.nan, np.float32)
    ok = np.isfinite(prob)
    val = ok & (relief >= curves["valley_relief_m"])
    opn = ok & ~val
    out[opn] = curves["open"].predict(prob[opn].astype(np.float64))
    out[val] = curves["valley"].predict(prob[val].astype(np.float64))
    out[ok & (prob <= 0)] = 0.0          # the physical ceiling stays a hard zero
    return out


def _print(out: dict) -> None:
    r = out["results"]
    print("\n" + "=" * 72)
    for key in ("before_in_arunachal", "after_in_arunachal"):
        print(f"  {key.replace('_', ' ')}")
        for b in r[key]:
            print(f"    {b['range']:>9}  said {b['said_pct']:7.3f}%  happened {b['happened_pct']:7.3f}%"
                  f"  x{b['happened_over_said']}  flooded rows {b['flooded_rows']:>6,}")
    print("  top ranges (>= 5%) inside Arunachal, by fold and year block:")
    for k, v in r["b2_top_ranges_by_fold_and_year"].items():
        print(f"    {k:<10} {v}")
    print(f"  ECE outside Arunachal {r['ece_outside_arunachal']}   inside {r['ece_in_arunachal']}")
    print(f"  area in the state (km2): {out['state_area_at_or_above']}")
    print(f"  gate: {out['gate']}")
    print(f"\n  GATE B: {'PASS' if out['GATE_B_PASS'] else 'FAIL'}")


def apply() -> None:
    """Ship the second stage to the SHOWN layer only — after a PASS."""
    rep = json.loads(REPORT.read_text())
    if not rep["GATE_B_PASS"]:
        raise SystemExit("Gate B did not pass — nothing applied.")
    with open(MODELS / "_second_stage_candidate.pkl", "rb") as fh:
        curves = pickle.load(fh)
    curves["meta"] = {"what": "second stage for the SHOWN WHERE chance, by terrain setting",
                      "gate_report": REPORT.name,
                      "fitted_on": "the shipped calibrator applied to out-of-fold scores, all rows"}
    with open(CURVES, "wb") as fh:
        pickle.dump(curves, fh)
    import predict_flood_where as pfw
    pfw.write_web_layer(shown_from_curves=True)
    print(f"  applied: {CURVES.name}; the web layer now shows the second-stage chance")


if __name__ == "__main__":
    apply() if (len(sys.argv) > 1 and sys.argv[1] == "apply") else check()
