"""Train the flood WHERE model, then calibrate it into a real probability.

    python scripts/model/train_flood_where.py

Produces:
    models/flood_where/fold{0..4}.txt        leave-one-block-out models
    models/flood_where/full.txt              trained on everything, to ship
    models/flood_where/calibrator_isotonic.pkl
    models/flood_where/_meta.json
    reports/flood_where_training.json
    reports/flood_where_reliability.png

════════════════════════════════════════════════════════════════════════════
WHY THIS ONE CAN BE A PROBABILITY AND SUSCEPTIBILITY CANNOT
════════════════════════════════════════════════════════════════════════════
The landslide susceptibility model is presence-only: we know where slides
were mapped, never where they were confirmed absent, so there is no
denominator and the score can only ever be a ranking (see
train_susceptibility.py).

This one has a real denominator. Every event contributes both the ground the
water reached and the ground it did not, measured the same way by the same
satellite pass. So "of the cells scoring 0.30, what share actually flooded"
is a question the data can answer — which is the definition of calibration.

Two things are needed to get there and BOTH are done here:

    train       learn the ranking from terrain
    calibrate   map that ranking onto observed frequency, on ground the
                model never trained on

Training alone is not enough. A raw model score is a ranking wearing a
decimal point.

════════════════════════════════════════════════════════════════════════════
THE NUMBER WE REPORT IS THE MOUNTAIN NUMBER
════════════════════════════════════════════════════════════════════════════
Most of the training evidence lies on the Brahmaputra floodplain, because
that is where Arunachal's floods are. Predicting flat floodplain inundation
is much easier than predicting it in a steep mountain valley, so a single
pooled score would flatter the model and would not describe the pilot at
Jang at all. Every metric is therefore reported three ways: pooled, inside
Arunachal, and on steep ground. The mountain number is the honest one.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, roc_auc_score

import grid as G
from common import INTERIM, PROCESSED, ROOT

warnings.filterwarnings("ignore")

MODELS = ROOT / "models" / "flood_where"
REPORTS = ROOT / "reports"
SAMPLE = PROCESSED / "flood_where_samples.parquet"
LANDCOVER = "lc_class_cat"      # present in the table, excluded from features

PARAMS = dict(
    objective="binary", n_estimators=700, learning_rate=0.05,
    num_leaves=63, min_child_samples=200, subsample=0.8,
    subsample_freq=1, colsample_bytree=0.8,
    reg_lambda=1.0, verbose=-1, n_jobs=-1, random_state=42,
)

# Steep enough that floodplain intuition stops applying. The Jang pilot
# valley sits well inside this class.
STEEP_DEG = 10.0


def wmean(x, w):
    return float(np.average(x, weights=w))


def metrics(y, p, w) -> dict:
    """AUC/AP under the negative-sampling weights, so they describe the real
    population rather than the sampled one."""
    if len(np.unique(y)) < 2:
        return {"n": int(len(y)), "auc": None, "ap": None, "prevalence": wmean(y, w)}
    return {
        "n": int(len(y)),
        "auc": float(roc_auc_score(y, p, sample_weight=w)),
        "ap": float(average_precision_score(y, p, sample_weight=w)),
        "prevalence": wmean(y, w),
    }


def reliability(y, p, w, n_bins: int = 12) -> list[dict]:
    """Observed flood frequency inside each predicted-probability band.
    This is the table that decides whether the number on the map is real."""
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges = np.unique(edges)
    out = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        upper = (p <= hi) if i == len(edges) - 2 else (p < hi)
        m = (p >= lo) & upper
        if m.sum() < 50:
            continue
        out.append({
            "bin": i, "p_lo": float(lo), "p_hi": float(hi),
            "n": int(m.sum()), "n_weighted": float(w[m].sum()),
            "predicted": wmean(p[m], w[m]),
            "observed": wmean(y[m], w[m]),
        })
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", help="train only on floods dated on/before this "
                    "date (YYYY-MM-DD); used to build the replay model")
    ap.add_argument("--tag", help="write to models/flood_where_<tag>/ and "
                    "reports/flood_where_<tag>_*, leaving the shipped model alone")
    ap.add_argument("--skip-ablation", action="store_true")
    ap.add_argument("--verified-only", action="store_true",
                    help="train only on events some independent route confirms "
                         "(build_verified_floods.py, PARKED §0x)")
    ap.add_argument("--exclude-channel-shift", action="store_true",
                    help="drop the braided-channel-shift suspects found by "
                         "check_paddy_labels.py (reports/flood_paddy_check.json)")
    args = ap.parse_args()

    global MODELS
    sfx = f"_{args.tag}" if args.tag else ""
    if args.tag:
        MODELS = ROOT / "models" / f"flood_where{sfx}"

    t0 = time.time()
    MODELS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    print(f"Flood WHERE — train, then calibrate{'  [' + args.tag + ']' if args.tag else ''}")

    meta_in = json.loads((PROCESSED / "flood_where_samples.meta.json").read_text())
    df = pd.read_parquet(SAMPLE)
    if args.until:
        from build_flood_where_samples import candidate_dates
        ev = pd.read_parquet(PROCESSED / "flood_where_events.parquet")
        dmap = candidate_dates()
        ev["date"] = pd.to_datetime(ev["uuid"].map(dmap))
        keep = set(ev.loc[ev["date"] <= pd.Timestamp(args.until), "event"])
        df = df[df["event"].isin(keep)].reset_index(drop=True)
        print(f"  --until {args.until}: kept {len(keep):,} of {len(ev):,} events")
    if args.exclude_channel_shift:
        sus = set(json.loads((REPORTS / "flood_paddy_check.json").read_text())
                  ["channel_shift_suspects"]["uuids"])
        ev = pd.read_parquet(PROCESSED / "flood_where_events.parquet")
        drop = set(ev.loc[ev["uuid"].isin(sus), "event"])
        before = df["event"].nunique()
        df = df[~df["event"].isin(drop)].reset_index(drop=True)
        print(f"  --exclude-channel-shift: dropped {before - df['event'].nunique():,} "
              f"suspect events, {df['event'].nunique():,} left")
    if args.verified_only:
        ver = set(pd.read_parquet(INTERIM / "flood_events" / "verified_events.parquet")["uuid"])
        ev = pd.read_parquet(PROCESSED / "flood_where_events.parquet")
        keep = set(ev.loc[ev["uuid"].isin(ver), "event"])
        before = df["event"].nunique()
        df = df[df["event"].isin(keep)].reset_index(drop=True)
        print(f"  --verified-only: kept {df['event'].nunique():,} of {before:,} events")
    # Taken from the sample metadata, never inferred from "every column that
    # isn't an id". Land cover is deliberately present in the table and absent
    # from this list, and an inferred feature set would silently put it back.
    feats = (meta_in["features_terrain"] + meta_in["features_soil"]
             + meta_in["features_categorical"])
    CATS = list(meta_in["features_categorical"])
    for c in CATS:
        df[c] = df[c].astype("category")

    # Where is this row, for the three-way reporting split
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        instate = m.read(1).astype(bool)
    in_ap = instate[df["row"].to_numpy(), df["col"].to_numpy()]
    steep = df["terrain_slope_deg"].to_numpy() >= STEEP_DEG

    y = df["label"].to_numpy()
    w = df["weight"].to_numpy()
    print(f"  {len(df):,} rows x {len(feats)} features, {df.event.nunique():,} events")
    print(f"  sampled prevalence {100*y.mean():.2f}%   "
          f"true (weighted) {100*wmean(y, w):.2f}%")
    print(f"  inside Arunachal {100*in_ap.mean():.1f}% of rows   "
          f"steep (>={STEEP_DEG:.0f} deg) {100*steep.mean():.1f}%")

    # ── leave-one-block-out: the honest ranking number ───────────────────
    oof = np.full(len(df), np.nan)
    folds = []
    print(f"\n  {'fold':<6}{'train':>12}{'test':>12}{'AUC':>8}{'AP':>8}{'AUC-AP':>9}{'AUC-steep':>11}")
    for f in sorted(df.fold.unique()):
        te_m = df.fold.to_numpy() == f
        tr, te = df[~te_m], df[te_m]
        m = lgb.LGBMClassifier(**PARAMS)
        m.fit(tr[feats], tr.label, sample_weight=tr.weight, categorical_feature=CATS)
        p = m.predict_proba(te[feats])[:, 1]
        oof[te_m] = p

        all_m = metrics(y[te_m], p, w[te_m])
        ap_m = metrics(y[te_m & in_ap], p[in_ap[te_m]], w[te_m & in_ap])
        st_m = metrics(y[te_m & steep], p[steep[te_m]], w[te_m & steep])
        folds.append({"fold": int(f), "n_train": int(len(tr)), "n_test": int(len(te)),
                      "pooled": all_m, "in_arunachal": ap_m, "steep": st_m})
        print(f"  {int(f):<6}{len(tr):>12,}{len(te):>12,}"
              f"{all_m['auc']:>8.3f}{all_m['ap']:>8.3f}"
              f"{(ap_m['auc'] or float('nan')):>9.3f}{(st_m['auc'] or float('nan')):>11.3f}")
        m.booster_.save_model(str(MODELS / f"fold{int(f)}.txt"))

    pooled = metrics(y, oof, w)
    pooled_ap = metrics(y[in_ap], oof[in_ap], w[in_ap])
    pooled_steep = metrics(y[steep], oof[steep], w[steep])
    print(f"\n  pooled out-of-fold AUC   {pooled['auc']:.3f}   AP {pooled['ap']:.3f}")
    print(f"  inside Arunachal   AUC   {pooled_ap['auc']:.3f}   AP {pooled_ap['ap']:.3f}")
    print(f"  steep ground       AUC   {pooled_steep['auc']:.3f}   AP {pooled_steep['ap']:.3f}"
          f"   (prevalence {100*pooled_steep['prevalence']:.2f}%)")

    # ── calibration ──────────────────────────────────────────────────────
    # CROSS-FITTED, and that detail is the whole point. Fitting isotonic on
    # the out-of-fold vector and then scoring calibration on that same vector
    # drives the error to ~0 by construction and proves nothing — it is the
    # calibration equivalent of quoting a model's training accuracy. So each
    # fold is mapped by a curve fitted only on the OTHER folds, and the error
    # is measured on ground that curve never saw.
    print("\n  calibrating (isotonic, cross-fitted across spatial folds)...", flush=True)
    before = reliability(y, oof, w)
    folds_arr = df.fold.to_numpy()
    cal = np.full(len(df), np.nan)
    for f in sorted(df.fold.unique()):
        m = folds_arr == f
        iso_f = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso_f.fit(oof[~m], y[~m], sample_weight=w[~m])
        cal[m] = iso_f.predict(oof[m])
    after = reliability(y, cal, w)
    after_ap = reliability(y[in_ap], cal[in_ap], w[in_ap])

    def ece(rel):
        tot = sum(r["n_weighted"] for r in rel)
        return sum(r["n_weighted"] * abs(r["predicted"] - r["observed"]) for r in rel) / tot

    print(f"    calibration error  before {100*ece(before):.2f}%  "
          f"after {100*ece(after):.2f}%   (held-out; mean gap promised vs observed)")
    print(f"    inside Arunachal   after {100*ece(after_ap):.2f}%")
    print(f"\n  {'predicted':>11}{'observed':>11}{'cells':>14}")
    for r in after:
        print(f"  {100*r['predicted']:>10.1f}%{100*r['observed']:>10.1f}%{r['n']:>14,}")

    # The SHIPPED curve is fitted on the whole out-of-fold vector — standard,
    # and it is the best estimate available. The number quoted above is the
    # cross-fitted one, which is what it will actually do on new ground.
    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(oof, y, sample_weight=w)
    with open(MODELS / "calibrator_isotonic.pkl", "wb") as fh:
        pickle.dump(iso, fh)

    # ── ablation: the land-cover model we are NOT shipping ───────────────
    # Adding ESA WorldCover scores clearly better on held-out folds, which is
    # exactly why this is recorded rather than quietly dropped. The held-out
    # folds are all in the same floodplain-dominated distribution as training,
    # so they cannot see the failure: at 3,000 m "permanent water" stops
    # meaning river and starts meaning glacial lake. A number that improves on
    # validation and breaks in the field is worse than no number.
    #
    # The evidence for rejecting it is the OUT-OF-DISTRIBUTION check below,
    # not the AUC — so both are written down and the AUC is not treated as
    # the deciding vote.
    if LANDCOVER in df.columns and not args.skip_ablation:
        print("\n  ablation: what land cover would have added (and why it is out)...",
              flush=True)
        ab_feats = feats + [LANDCOVER]
        df[LANDCOVER] = df[LANDCOVER].astype("category")
        ab_oof = np.full(len(df), np.nan)
        for f in sorted(df.fold.unique()):
            te_m = folds_arr == f
            tr = df[~te_m]
            m = lgb.LGBMClassifier(**PARAMS)
            m.fit(tr[ab_feats], tr.label, sample_weight=tr.weight,
                  categorical_feature=[LANDCOVER])
            ab_oof[te_m] = m.predict_proba(df[te_m][ab_feats])[:, 1]

        ablation = {
            "features": ab_feats,
            "pooled": metrics(y, ab_oof, w),
            "in_arunachal": metrics(y[in_ap], ab_oof[in_ap], w[in_ap]),
            "steep": metrics(y[steep], ab_oof[steep], w[steep]),
            "verdict": ("rejected despite the better AUC - its class meanings "
                        "do not survive the move from floodplain to mountain"),
            "evidence": ("the failure is invisible in these fold metrics, "
                         "because every fold is drawn from the same flood-crop "
                         "population as training. It only appears when the "
                         "model is asked about ground it never saw - see "
                         "check_flood_where_sanity.py, which scores the whole "
                         "state and asks how high above its own channel the "
                         "top-scoring ground sits"),
        }
        print(f"    with land cover  AUC pooled {ablation['pooled']['auc']:.3f}"
              f"  Arunachal {ablation['in_arunachal']['auc']:.3f}"
              f"  steep {ablation['steep']['auc']:.3f}")
        print(f"    shipped (no LC)  AUC pooled {pooled['auc']:.3f}"
              f"  Arunachal {pooled_ap['auc']:.3f}  steep {pooled_steep['auc']:.3f}")
        print("    (the land-cover model scores better here and still fails "
              "statewide - see check_flood_where_sanity.py)")
    else:
        ablation = None

    # ── full model, for deployment only ──────────────────────────────────
    print("\n  training full model (deployment)...", flush=True)
    full = lgb.LGBMClassifier(**PARAMS)
    full.fit(df[feats], df.label, sample_weight=df.weight, categorical_feature=CATS)
    full.booster_.save_model(str(MODELS / "full.txt"))

    imp = pd.DataFrame({"feature": feats,
                        "gain": full.booster_.feature_importance("gain")})
    imp["gain_pct"] = 100 * imp.gain / imp.gain.sum()
    imp = imp.sort_values("gain", ascending=False)
    imp.to_csv(REPORTS / f"flood_where{sfx}_importance.csv", index=False)
    print("\n  top features by gain:")
    for _, r in imp.head(8).iterrows():
        print(f"    {r.feature:<28}{r.gain_pct:>6.1f}%")

    # ── write it all down ────────────────────────────────────────────────
    out = {
        "trained_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sample_meta": meta_in,
        "n_rows": int(len(df)), "n_events": int(df.event.nunique()),
        "features": feats, "categorical": CATS, "params": PARAMS,
        "steep_threshold_deg": STEEP_DEG,
        "folds": folds,
        "pooled_oof": {"all": pooled, "in_arunachal": pooled_ap, "steep": pooled_steep},
        "calibration": {
            "method": ("isotonic, cross-fitted across spatial folds - each fold "
                       "mapped by a curve fitted only on the other folds, so the "
                       "reported error is held-out, not in-sample"),
            "ece_before": ece(before), "ece_after": ece(after),
            "ece_after_in_arunachal": ece(after_ap),
            "reliability_before": before, "reliability_after": after,
            "reliability_after_in_arunachal": after_ap,
            "shipped_curve": "fitted on the full out-of-fold vector",
        },
        "ablation_no_landcover": ablation,
        "importance": imp.to_dict("records"),
        "score_meaning": ("calibrated probability that a 100 m cell is under water "
                          "GIVEN a flood reported within about "
                          "5 km (training crops are 10 km, centred on the reports) "
                          "- not an unconditional annual flood chance"),
        "report_from": "fold models (out-of-fold)", "deploy_with": "full.txt + calibrator_isotonic.pkl",
    }
    (REPORTS / f"flood_where{sfx}_training.json").write_text(json.dumps(out, indent=2))
    (MODELS / "_meta.json").write_text(json.dumps(
        {k: v for k, v in out.items() if k != "importance"}, indent=2))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.5, 6))
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
        ax.plot([r["predicted"] for r in before], [r["observed"] for r in before],
                "o-", color="#d1495b", label="raw model score")
        ax.plot([r["predicted"] for r in after], [r["observed"] for r in after],
                "o-", color="#3b7dd8", label="after calibration")
        ax.set_xlabel("probability the model promises")
        ax.set_ylabel("share that actually flooded")
        ax.set_title("Flood WHERE — does the number mean what it says?\n"
                     f"{df.event.nunique():,} real events, out-of-fold", fontsize=10)
        ax.legend()
        fig.tight_layout()
        fig.savefig(REPORTS / f"flood_where{sfx}_reliability.png", dpi=130)
        print(f"  wrote {REPORTS / f'flood_where{sfx}_reliability.png'}")
    except ImportError:
        pass

    print(f"\n  done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
