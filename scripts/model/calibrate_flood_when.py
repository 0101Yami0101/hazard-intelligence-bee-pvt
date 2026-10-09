"""§10 of the plan — turn the checked WHEN *score* into a real *probability*.

    python scripts/model/calibrate_flood_when.py

Outputs:
    models/flood_when/calibrator_isotonic.pkl   -- the operational mapping
    reports/flood_when_calibration.json         -- reliability + skill numbers
    data/interim/flood_when/calibration_curve.png

════════════════════════════════════════════════════════════════════════════
WHAT WAS AND WASN'T ALREADY TRUE
════════════════════════════════════════════════════════════════════════════
Everything up to now measured AUC — whether the score RANKS risky days above
calm ones. It does (0.66-0.96 across 29 stations). AUC says nothing about
whether the number itself means anything: a score that ranks perfectly but
reads 0.9 on days that flood 3% of the time has a perfect AUC and a useless
probability. Calibration is the separate question, and this is the script
that answers it.

Method: isotonic regression (monotonic, non-parametric — it can only rescale
magnitudes, never reorder them, so it cannot damage the AUC already earned),
cross-checked against Platt/logistic scaling.

════════════════════════════════════════════════════════════════════════════
THE THING THAT MAKES THIS HONEST: THE CALIBRATOR IS ITSELF HELD OUT
════════════════════════════════════════════════════════════════════════════
A calibrator scored on the same rows it was fitted on looks perfect by
construction — the single easiest way to fake this result. Every number
reported here comes from year-grouped cross-validation of the CALIBRATOR:
fit on some years, measure on years it never saw, rotate. The input scores
are themselves already out-of-fold (from the model's own year-grouped CV),
so no row is ever scored by a model or a calibrator that saw its year.

════════════════════════════════════════════════════════════════════════════
⚠️ TWO DIFFERENT PROBABILITIES — DO NOT BLUR THEM IN A PITCH
════════════════════════════════════════════════════════════════════════════
Stations split into two groups with genuinely different meanings:

  * **CWC published danger level** — "P(this river crosses the government's
    own official danger level today)". An externally-defined, real-world
    event. This is the number worth quoting to an official.
  * **Self-derived (top 2%)** — "P(today is in this river's own wettest 2%
    of days)". Legitimate and useful, but the base rate is ~2% BY
    CONSTRUCTION, so a calibrated probability here partly reflects the
    label definition, not an independent fact about danger.

Reported separately throughout for that reason.

Skill is measured as Brier Skill Score against climatology (always predict
the base rate). Positive = the forecast beats "it floods X% of days here,
same answer every day"; 0 = no better than that; negative = worse.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold

from common import INTERIM, ROOT

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models" / "flood_when"
N_FOLDS = 5
# Bins are deliberately dense at the LOW end. Flooding is a rare event
# (0.8-2% of days), so an honest calibrated forecast lives almost entirely
# below 0.5 - an evenly-spaced 0-1 binning collapses every real distinction
# into one row and hides whether the forecast is any good.
BINS = np.array([0.0, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.01])
TOP_FRACTIONS = [0.001, 0.01, 0.05, 0.10, 0.25]


def load_scores() -> pd.DataFrame:
    frames = []
    for fname, network in [("oof_scores_cwc.csv", "CWC"), ("oof_scores_nwdp.csv", "NWDP")]:
        p = OUT / fname
        if p.exists():
            d = pd.read_csv(p, parse_dates=["date"])
            d["network"] = network
            frames.append(d)
        else:
            print(f"  [warn] {p} missing - run the matching train script first")
    df = pd.concat(frames, ignore_index=True)
    return df.dropna(subset=["score_blend"])


def ece(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    """Expected calibration error: mean |predicted - observed| per bin,
    weighted by how many days land in each bin."""
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges[-1] += 1e-9
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() == 0:
            continue
        total += (m.sum() / len(p)) * abs(p[m].mean() - y[m].mean())
    return float(total)


def brier_skill(y: np.ndarray, p: np.ndarray) -> float:
    """Brier Skill Score vs climatology (always predict the base rate)."""
    base = np.full_like(p, y.mean(), dtype=float)
    bs, bs_ref = brier_score_loss(y, p), brier_score_loss(y, base)
    return float(1 - bs / bs_ref) if bs_ref > 0 else 0.0


def cv_calibrate(df: pd.DataFrame, method: str = "isotonic") -> np.ndarray:
    """Out-of-fold CALIBRATED probabilities, grouped by year.

    The calibrator never sees the year it is scoring — without this, the
    reliability numbers below would be fitted-on-themselves and meaningless.
    """
    y = df["flood"].to_numpy()
    s = df["score_blend"].to_numpy()
    years = df["year"].to_numpy()
    k = min(N_FOLDS, len(np.unique(years)))
    out = np.full(len(df), np.nan)
    if k < 2:
        return out
    for tr, te in GroupKFold(n_splits=k).split(df, groups=years):
        if y[tr].sum() == 0 or y[tr].sum() == len(tr):
            continue
        if method == "isotonic":
            m = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(s[tr], y[tr])
            out[te] = m.predict(s[te])
        else:
            m = LogisticRegression().fit(s[tr].reshape(-1, 1), y[tr])
            out[te] = m.predict_proba(s[te].reshape(-1, 1))[:, 1]
    return out


def reliability_table(y: np.ndarray, p: np.ndarray) -> list[dict]:
    rows = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() == 0:
            continue
        rows.append({
            "band": f"{lo:.2f}-{min(hi, 1.0):.2f}",
            "n_days": int(m.sum()),
            "predicted_pct": round(100 * float(p[m].mean()), 1),
            "observed_pct": round(100 * float(y[m].mean()), 1),
            "n_floods": int(y[m].sum()),
        })
    return rows


def operational_lift(y: np.ndarray, p: np.ndarray) -> list[dict]:
    """What actually happened on the riskiest N% of days - the framing an
    operator or an official actually acts on, and the one that shows whether
    a calibrated-but-flat forecast has any real sharpness behind it."""
    rows = []
    for frac in TOP_FRACTIONS:
        k = max(1, int(len(p) * frac))
        idx = np.argsort(-p)[:k]
        obs = float(y[idx].mean())
        rows.append({
            "top_pct": round(100 * frac, 1),
            "n_days": int(k),
            "predicted_pct": round(100 * float(p[idx].mean()), 1),
            "observed_pct": round(100 * obs, 1),
            "lift_vs_base_rate": round(obs / y.mean(), 1) if y.mean() > 0 else None,
            "n_floods_caught": int(y[idx].sum()),
            "pct_of_all_floods": round(100 * float(y[idx].sum() / y.sum()), 1) if y.sum() else None,
        })
    return rows


def assess(name: str, df: pd.DataFrame) -> dict:
    y = df["flood"].to_numpy()
    raw = df["score_blend"].to_numpy()
    iso = cv_calibrate(df, "isotonic")
    platt = cv_calibrate(df, "platt")
    ok = ~np.isnan(iso) & ~np.isnan(platt)
    y, raw, iso, platt = y[ok], raw[ok], iso[ok], platt[ok]
    scoreable = 0 < y.sum() < len(y)

    res = {
        "group": name,
        "n_days": int(len(y)),
        "n_flood_days": int(y.sum()),
        "base_rate_pct": round(100 * float(y.mean()), 2),
        "auc_raw": round(float(roc_auc_score(y, raw)), 3) if scoreable else None,
        "auc_calibrated": round(float(roc_auc_score(y, iso)), 3) if scoreable else None,
        "ece_raw_pct": round(100 * ece(y, raw), 2),
        "ece_isotonic_pct": round(100 * ece(y, iso), 2),
        "ece_platt_pct": round(100 * ece(y, platt), 2),
        "brier_raw": round(float(brier_score_loss(y, raw)), 5),
        "brier_isotonic": round(float(brier_score_loss(y, iso)), 5),
        "brier_skill_raw": round(brier_skill(y, raw), 3),
        "brier_skill_isotonic": round(brier_skill(y, iso), 3),
        "reliability_isotonic": reliability_table(y, iso),
        # Calibration alone is not enough: a forecast that always answers
        # "1.3%" is perfectly calibrated and useless. Sharpness is the other
        # half - does it ever commit to a high number, and is it right when
        # it does. Reported as what actually happened on the riskiest days.
        "sharpness_pct": {f"p{q}": round(100 * float(np.percentile(iso, q)), 2)
                           for q in (50, 90, 99, 99.9, 100)},
        "operational_lift": operational_lift(y, iso),
    }
    print(f"\n=== {name} ===")
    print(f"  {res['n_days']:,} days, {res['n_flood_days']} flood days "
          f"(base rate {res['base_rate_pct']}%)")
    print(f"  AUC  raw {res['auc_raw']} -> calibrated {res['auc_calibrated']} "
          "(isotonic is monotonic, so ranking is preserved by construction)")
    print(f"  Calibration error  raw {res['ece_raw_pct']}%  ->  "
          f"isotonic {res['ece_isotonic_pct']}%  (platt {res['ece_platt_pct']}%)")
    print(f"  Brier skill vs climatology  raw {res['brier_skill_raw']}  ->  "
          f"isotonic {res['brier_skill_isotonic']}")
    print(f"  {'band':<14}{'days':>9}{'predicted':>11}{'observed':>10}{'floods':>8}")
    for r in res["reliability_isotonic"]:
        print(f"  {r['band']:<14}{r['n_days']:>9,}{r['predicted_pct']:>10.2f}%"
              f"{r['observed_pct']:>9.2f}%{r['n_floods']:>8}")
    print("  on the riskiest days (the operationally useful view):")
    for r in res["operational_lift"]:
        print(f"    top {r['top_pct']:>5.1f}% ({r['n_days']:>6,} days): "
              f"predicted {r['predicted_pct']:>5.1f}%  observed {r['observed_pct']:>5.1f}%"
              f"  = {r['lift_vs_base_rate']:>4.1f}x base rate"
              f"   catches {r['pct_of_all_floods']:>4.1f}% of all floods")
    return res


def main() -> None:
    print("Calibration - turning the checked WHEN score into a real probability\n")
    df = load_scores()
    print(f"{len(df):,} scored station-days, {int(df['flood'].sum())} flood days, "
          f"{df['station_code'].nunique()} stations")

    real = df[df["label_source"].str.startswith("CWC published")]
    derived = df[~df["label_source"].str.startswith("CWC published")]

    groups = [("ALL stations pooled", df)]
    if len(real):
        groups.append(("Official CWC danger level only (the number to quote)", real))
    if len(derived):
        groups.append(("Self-derived top-2% label only", derived))

    results = [assess(n, g) for n, g in groups]

    MODELS.mkdir(parents=True, exist_ok=True)
    final = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(
        df["score_blend"].to_numpy(), df["flood"].to_numpy())
    with open(MODELS / "calibrator_isotonic.pkl", "wb") as fh:
        pickle.dump(final, fh)
    print(f"\nwrote {MODELS / 'calibrator_isotonic.pkl'}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_when_calibration.json"
    out.write_text(json.dumps({
        "method": "isotonic regression, year-grouped CV of the calibrator itself",
        "caveat_autocorrelation": (
            "Flood days come in multi-day runs, so these rows are not "
            "independent samples. The calibration MAPPING is unaffected, but "
            "confidence in it is narrower than the raw day count suggests - "
            "roughly 310 distinct flood episodes underlie the flood days."),
        "caveat_two_label_types": (
            "'Official CWC danger level' rows carry an externally-defined "
            "event. 'Self-derived top-2%' rows have a ~2% base rate by "
            "construction. Never quote the pooled number as if it were all "
            "the official kind."),
        "groups": results,
    }, indent=2))
    print(f"wrote {out}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, len(groups), figsize=(6 * len(groups), 5))
        axes = np.atleast_1d(axes)
        for ax, (name, g) in zip(axes, groups):
            y_all = g["flood"].to_numpy()
            iso = cv_calibrate(g, "isotonic")
            raw = g["score_blend"].to_numpy()
            ok = ~np.isnan(iso)
            for vals, lab, style in [(raw[ok], "raw score", "o--"), (iso[ok], "calibrated", "s-")]:
                edges = np.quantile(vals, np.linspace(0, 1, 11))
                edges[-1] += 1e-9
                xs, ys = [], []
                for lo, hi in zip(edges[:-1], edges[1:]):
                    m = (vals >= lo) & (vals < hi)
                    if m.sum():
                        xs.append(vals[m].mean())
                        ys.append(y_all[ok][m].mean())
                ax.plot(xs, ys, style, label=lab)
            ax.plot([0, 1], [0, 1], "k:", lw=1, label="perfect")
            # Zoom to where the data actually lives. Flooding is rare, so a
            # full 0-1 reliability plot is ~85% empty space and visually
            # understates how closely the calibrated line tracks the
            # diagonal - the whole point of the figure.
            lim = max(0.05, float(np.nanmax(raw[ok])), float(np.nanmax(iso[ok]))) * 1.1
            ax.set_xlim(0, lim)
            ax.set_ylim(0, lim)
            ax.set_title(name, fontsize=9)
            ax.set_xlabel("predicted probability")
            ax.set_ylabel("observed frequency")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.25)
        fig.tight_layout()
        png = OUT / "calibration_curve.png"
        fig.savefig(png, dpi=110)
        print(f"wrote {png}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
