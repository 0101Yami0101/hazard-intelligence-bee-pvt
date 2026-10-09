"""Flood WHEN with the river's own latest reading — 1 to 9 days ahead.

    python scripts/model/train_flood_when_gauge.py                    # REPLACES the live models
    python scripts/model/train_flood_when_gauge.py --out models/flood_when_gauge_next
                                                   # a full set beside them; the report goes there too

Writes  models/flood_when_gauge/lead{1..9}.pkl   gauge + rain, calibrated
        models/flood_when_gauge/level{1..7}.pkl  the level line's models (gauge_week.py)
        models/flood_when_gauge/rain_only.pkl     rain alone: the fallback for a
                                                  gauge that has gone offline
        models/flood_when_gauge/stations.json     per-gauge scale + threshold
        reports/flood_when_gauge.json             the fair comparison

The shipped WHEN score reads rain only. At a gauged river we also know where
the water is right now, and a river already two-thirds of the way to danger
needs far less rain to get there than one at its dry-season floor. This
script measures how much that is worth, honestly, before anything uses it.

════════════════════════════════════════════════════════════════════════════
INPUTS
════════════════════════════════════════════════════════════════════════════
For a target day D and a lead of L days (the gauge was last read on D-L):

    r3, r7, trigger_lag1   rain on D, as before — each cell's own percentile
    g_frac                 the river's level on D-L, as a share of the way
                           from its ordinary level (median) to its threshold:
                           0 = ordinary, 1 = at the threshold
    g_rise                 the change in g_frac over the day before D-L
    rise3 ... day_rise     the river's own week up to D-L, six inputs
                           (gauge_week.week_inputs; since 2026-10-06, §14)

Both gauge inputs are in threshold units, so a 5 m trunk river and a 0.5 m
hill stream land on one scale and pool into one model — the same principle
as percentile rain (FLOOD_WHEN_PILOT_PLAN.md §5, guardrail 2). The threshold
is the official CWC danger level where one exists and the record reaches it,
else the river's own top 2% of days — exactly the existing WHEN labels.

════════════════════════════════════════════════════════════════════════════
WHY THE "ONSET" NUMBERS ARE THE ONES THAT COUNT
════════════════════════════════════════════════════════════════════════════
A river above danger yesterday is usually above danger today. Any model fed
yesterday's level scores those days easily, which inflates every headline
number without warning anyone of anything new. So every result is also
reported on ONSET days only: the river was below its threshold at the last
reading. That is the warning people actually need, and it is where rain has
to carry most of the weight.

Validation is year-grouped (no model or calibrator ever scores a year it
fitted on), and the rain-only baseline goes through the identical pipeline
on the identical rows, so the gain is the gauge's alone.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

import when_grid
from backtest_flood_when import FLOOD_PCTILE, daily_max
from backtest_flood_when_nwdp import daily_max_discharge, load_all
from common import GAUGES, ROOT
from flood_stations import STATIONS as CWC_STATIONS
from gauge_records import trim
from nwdp_stations import STATIONS as NWDP_STATIONS

MODELS = ROOT / "models" / "flood_when_gauge"
REPORTS = ROOT / "reports"

# 1-9: the week's outlook plus NWDP's ~2-day publishing lag, so a gauge that
# is reporting always has a model for every outlook day.
LEADS = tuple(range(1, 10))
RAIN_FEATS = ["r3", "r7", "trigger_lag1"]
GAUGE_FEATS = ["g_frac", "g_rise"]
OLD_FEATS = RAIN_FEATS + GAUGE_FEATS     # the five inputs of the models of 2026-09-22
HABIT = "habit"                          # a sixth input, tested and FAILED (habit(), §13j) —
                                         # kept so check_gauge_cure.py can reproduce that test
# The river's own week (gauge_week.py, §14). FREE_FEATS describe the shape of
# the week, so no "more of it never lowers the chance" rule is put on them.
WEEK_FEATS = ["rise3", "mean7", "max7", "above7", "end", "day_rise"]
FREE_FEATS = {"rise3", "mean7", "max7", "above7", "day_rise"}
# What the gauge models read. The week inputs were adopted on the user's word
# on 2026-10-06, knowing they failed one gate of four (§14d-§14e).
FEATS = OLD_FEATS + WEEK_FEATS
N_FOLDS = 5
# How a river-above group's score becomes a chance (calibrate()):
#   "isotonic"  the stepped curve every group had until 2026-10-06
#   "floor"     stepped, never below the river-below curve — FAILED, §13h
#   "sigmoid"   a smooth two-number S-curve — better than the stepped curve at
#               every lead, though not a cure for the fault it was built for (§13i)
# The first two are kept so check_gauge_retrain.py can reproduce those tests.
ABOVE = "sigmoid"
EPS = 1e-6               # scores are held inside (EPS, 1 - EPS) before taking log-odds
BINS = np.array([0.0, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 0.75, 1.01])


# ── per-gauge scale ──────────────────────────────────────────────────────
def station_scale(daily: pd.Series, danger: float | None) -> dict:
    """Threshold + ordinary level, same label rule as the shipped WHEN."""
    official = danger is not None and bool((daily >= danger).any())
    thr = float(danger) if official else float(daily.quantile(FLOOD_PCTILE))
    base = float(daily.median())
    return {"threshold": thr, "base": base, "official": official,
            "base_rate": float((daily >= thr).mean()),
            "means": ("crosses official CWC danger level" if official
                      else "reaches this river's own top 2% of days")}


def gauge_inputs(daily: pd.Series, sc: dict, lead: int) -> pd.DataFrame:
    """Indexed by TARGET day: the gauge state `lead` calendar days earlier."""
    d = daily.asfreq("D")
    frac = (d - sc["base"]) / (sc["threshold"] - sc["base"])
    return pd.DataFrame({"g_frac": frac.shift(lead),
                         "g_rise": (frac - frac.shift(1)).shift(lead),
                         "was_above": (d >= sc["threshold"]).astype(float)
                                      .where(d.notna()).shift(lead)})


def station_daily() -> list[dict]:
    out = []
    for code, meta in CWC_STATIONS.items():
        print(f"  CWC  {meta['name']}")
        out.append({"code": code, "network": "CWC", "meta": meta,
                    "daily": daily_max(GAUGES / "cwc" / f"{code}_hhs.csv"),
                    "danger": meta["danger_level"]})
    raw = load_all()
    for code, meta in NWDP_STATIONS.items():
        print(f"  NWDP {meta['name']}")
        d = daily_max_discharge(raw, code)
        if len(d) >= 30:
            out.append({"code": code, "network": "NWDP", "meta": meta, "daily": d,
                        "danger": None})
    for s in out:                                  # scale breaks, gauge_records.py
        s["daily"] = trim(s["code"], s["daily"])
    return out


def build_tables(stations: list[dict]) -> tuple[dict[int, pd.DataFrame], dict]:
    wdates, pct = when_grid.percentile_features()
    tables = {L: [] for L in LEADS}
    registry = {}
    for s in stations:
        m = s["meta"]
        cell = int(when_grid.cell_of(m["lat"], m["lon"]))
        if cell < 0:
            print(f"  [skip] {m['name']}: outside the rain lattice")
            continue
        sc = station_scale(s["daily"], s["danger"])
        registry[s["code"]] = {"name": m["name"], "network": s["network"],
                               "lat": m["lat"], "lon": m["lon"], "cell": cell,
                               "record_ends": str(s["daily"].index.max().date()), **sc}
        rain = pd.DataFrame({"r3": pct["r3"][:, cell], "r7": pct["r7"][:, cell]}, index=wdates)
        rain["trigger_lag1"] = rain[["r3", "r7"]].mean(axis=1).shift(1)
        daily = s["daily"]
        for L in LEADS:
            t = rain.reindex(daily.index).join(gauge_inputs(daily, sc, L))
            t["flood"] = (daily >= sc["threshold"]).astype(int)
            t["station_code"] = s["code"]
            t["network"] = s["network"]
            t["official"] = sc["official"]
            t = t.dropna(subset=["r3", "r7"])
            tables[L].append(t)
    return {L: pd.concat(v).rename_axis("date").reset_index() for L, v in tables.items()}, registry


# ── fitting ──────────────────────────────────────────────────────────────
def model(cols: list[str]) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(max_depth=3, max_iter=150, learning_rate=0.08,
                                          l2_regularization=1.0,
                                          monotonic_cst=[0 if c in FREE_FEATS else 1 for c in cols],
                                          random_state=0)


def river_state(df: pd.DataFrame) -> np.ndarray:
    """1 = at/above threshold at the last reading, 0 = below or unknown."""
    return (df["was_above"] == 1).to_numpy().astype(int)


def cal_group(df: pd.DataFrame) -> np.ndarray:
    """Calibration group: river state x label kind (0-3)."""
    return river_state(df) + 2 * df["official"].to_numpy(bool).astype(int)


def _iso(raw: np.ndarray, y: np.ndarray) -> IsotonicRegression:
    return IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(raw, y)


def _higher_of(a: IsotonicRegression, b: IsotonicRegression) -> IsotonicRegression:
    """One curve that is the higher of two at every score. Both are straight
    lines between their own steps, so the result is exact once the points
    where they cross are added."""
    x = np.union1d(a.X_thresholds_, b.X_thresholds_)
    d = a.predict(x) - b.predict(x)
    i = np.flatnonzero(d[:-1] * d[1:] < 0)
    x = np.union1d(x, x[i] + (x[i + 1] - x[i]) * d[i] / (d[i] - d[i + 1]))
    out = _iso(x, np.maximum(a.predict(x), b.predict(x)))
    grid = np.union1d(x, np.linspace(0, 1, 20001))
    assert np.abs(out.predict(grid) - np.maximum(a.predict(grid), b.predict(grid))).max() < 1e-9
    return out


def _sigmoid(raw: np.ndarray, y: np.ndarray) -> IsotonicRegression:
    """A smooth S-curve on the model's log-odds, two fitted numbers (Platt
    scaling): the standard calibration for a group too small for a stepped
    curve. It never falls as the score rises — if the fit would, the group's
    flat rate is used. Returned as a plain curve object (the S-curve drawn
    through 4001 points), so whatever reads the calibrators needs no change."""
    z = logit(np.clip(raw, EPS, 1 - EPS))
    lr = LogisticRegression(C=np.inf, max_iter=1000).fit(z.reshape(-1, 1), y)
    a, b = float(lr.coef_[0, 0]), float(lr.intercept_[0])
    if a < 0:
        a, b = 0.0, float(logit(y.mean()))
    zz = np.linspace(logit(EPS), logit(1 - EPS), 4001)
    return _iso(expit(zz), expit(a * zz + b))


def calibrate(raw_tr, y_tr, g_tr, by: str) -> dict:
    """Calibration curves keyed by group (river state + 2 x label kind).

    by="state": one curve per river state x label kind. A single shared curve
      was measured to over-promise on onset days (said ~20%, ~12% happened at
      official gauges, lead 1): the same raw score means less when the river
      has not risen yet, and less again against an official danger level
      (0.29% of onset days there vs 0.79% for a river's own top-2%). Both are
      known at issue time, so splitting costs nothing live.
      The two "river above" groups are a few hundred days each, too few for
      a stepped curve: its lowest step was 0% wherever the few lowest-scored
      days happened not to flood, so a river above its danger level was told
      0% where about 4 in 10 such days flood again (§13h). ABOVE picks their
      curve; the river-below groups (tens of thousands of days) stay stepped.
    by="kind": one curve per label kind, river state ignored — for the rain-
      only fallback, used exactly when the gauge is offline and the state is
      NOT known.
    by="none": one pooled curve (the fair rain-only comparison).
    A group too thin to fit falls back to the pooled curve."""
    pooled = _iso(raw_tr, y_tr)
    cals = {k: pooled for k in range(4)}
    if by == "state":
        for k in range(4):
            m = g_tr == k
            if y_tr[m].sum() >= 20:
                fit = _sigmoid if k % 2 and ABOVE == "sigmoid" else _iso
                cals[k] = fit(raw_tr[m], y_tr[m])
        if ABOVE == "floor":
            for k in (1, 3):
                cals[k] = _higher_of(cals[k], cals[k - 1])
    elif by == "kind":
        for kind in (0, 1):
            m = g_tr // 2 == kind
            if y_tr[m].sum() >= 20:
                cals[2 * kind] = cals[2 * kind + 1] = _iso(raw_tr[m], y_tr[m])
    return cals


def apply_cal(cals: dict, raw: np.ndarray, g: np.ndarray) -> np.ndarray:
    out = np.empty(len(raw))
    for k, c in cals.items():
        m = g == k
        if m.any():
            out[m] = c.predict(raw[m])
    return out


def habit(df: pd.DataFrame, fit: np.ndarray) -> np.ndarray:
    """NOT USED — tested 2026-10-06 and failed every gate (§13j): a gauge's
    share in one year is a poor guide to its other years, so this is less a
    habit of the river than a mark of particular high-water spells.

    This river's habit of staying high: how often this gauge, once above
    its line, was above it again the table's lead later. 0 for a row whose
    river is below its line — there is nothing to stay.

    Counted over the rows in `fit` that are NOT in the row's own year, so no
    row's input ever holds its own outcome, and a year being scored is never
    in the count. One imaginary day at the pooled rate of the gauge's kind of
    line keeps a gauge with few such days away from 0% and 100%, and gives a
    gauge with none the pooled rate (FLOOD_WHEN_PILOT_PLAN.md §13j)."""
    above = river_state(df) == 1
    f = pd.DataFrame({"code": df["station_code"].to_numpy(),
                      "kind": df["official"].to_numpy(bool),
                      "yr": df["date"].dt.year.to_numpy(),
                      "y": df["flood"].to_numpy()})
    a = f[fit & above]

    def counts(keys):
        c = a.groupby(keys)["y"].agg(["sum", "count"])
        j = f[keys].join(c, on=keys)
        return j["sum"].fillna(0).to_numpy(float), j["count"].fillna(0).to_numpy(float)

    (k, n), (ky, ny) = counts(["code"]), counts(["code", "yr"])
    (K, N), (Ky, Ny) = counts(["kind"]), counts(["kind", "yr"])
    pooled = (K - Ky) / np.maximum(N - Ny, 1)
    return np.where(above, (k - ky + pooled) / (n - ny + 1), 0.0)


def habit_now(df: pd.DataFrame, registry: dict) -> dict[str, float]:
    """The same count over every year, per gauge: what the live forecast
    reads for a river that is above its line today."""
    a = df[river_state(df) == 1]
    pooled = {bool(kind): float(v) for kind, v in a.groupby(a["official"].astype(bool))["flood"].mean().items()}
    c = a.groupby("station_code")["flood"].agg(["sum", "count"])
    out = {}
    for code, st in registry.items():
        k, n = (c.loc[code, "sum"], c.loc[code, "count"]) if code in c.index else (0, 0)
        out[code] = float((k + pooled.get(bool(st["official"]), 0.0)) / (n + 1))
    return out


def _design(df: pd.DataFrame, cols: list[str], fit: np.ndarray) -> pd.DataFrame:
    """The model's inputs. `habit` is the one input counted from outcomes, so
    it is rebuilt for every fit from that fit's own rows."""
    if HABIT not in cols:
        return df[cols]
    return df[[c for c in cols if c != HABIT]].assign(**{HABIT: habit(df, fit)})[cols]


def _raw_oof(df, cols, folds):
    y = df["flood"].to_numpy()
    raw = np.full(len(df), np.nan)
    for tr, te in folds:
        fit = np.zeros(len(df), bool)
        fit[tr] = True
        X = _design(df, cols, fit)
        raw[te] = model(cols).fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])[:, 1]
    return raw


def oof(df: pd.DataFrame, cols: list[str], by: str) -> np.ndarray:
    """Year-grouped out-of-fold scores, then a year-grouped calibrator on top."""
    y, st = df["flood"].to_numpy(), cal_group(df)
    folds = list(GroupKFold(n_splits=N_FOLDS).split(df, groups=df["date"].dt.year))
    raw = _raw_oof(df, cols, folds)
    cal = np.full(len(df), np.nan)
    for tr, te in folds:
        cal[te] = apply_cal(calibrate(raw[tr], y[tr], st[tr], by), raw[te], st[te])
    return cal


def fit_final(df: pd.DataFrame, cols: list[str], by: str) -> dict:
    """Shipped model: trees on everything, calibrators on the out-of-fold
    scores so they map honest (unseen-year) scores to frequencies."""
    y, st = df["flood"].to_numpy(), cal_group(df)
    folds = list(GroupKFold(n_splits=N_FOLDS).split(df, groups=df["date"].dt.year))
    raw = _raw_oof(df, cols, folds)
    return {"model": model(cols).fit(_design(df, cols, np.ones(len(df), bool)), y),
            "calibrators": calibrate(raw, y, st, by), "features": cols}


# ── scoring ──────────────────────────────────────────────────────────────
def grade(y: np.ndarray, p: np.ndarray) -> dict:
    ok = np.isfinite(p)
    y, p = y[ok], p[ok]
    base = y.mean()
    brier = float(np.mean((p - y) ** 2))
    k = max(1, int(round(0.01 * len(p))))
    top = np.argsort(-p)[:k]
    out = {"n_days": int(len(y)), "n_flood_days": int(y.sum()),
           "auc": round(float(roc_auc_score(y, p)), 3) if 0 < y.sum() < len(y) else None,
           "brier_skill": round(1 - brier / (base * (1 - base)), 3) if 0 < base < 1 else None,
           "top1pct_said": round(100 * float(p[top].mean()), 1),
           "top1pct_happened": round(100 * float(y[top].mean()), 1),
           "warnings": []}
    for t in (0.25, 0.5):
        w = p >= t
        out["warnings"].append({
            "at_pct": int(100 * t),
            "floods_caught_pct": round(100 * float(w[y == 1].mean()), 1) if y.sum() else None,
            "warnings_right_pct": round(100 * float(y[w].mean()), 1) if w.any() else None,
            "n_warnings": int(w.sum())})
    return out


def reliability(y: np.ndarray, p: np.ndarray) -> list[dict]:
    rows = []
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum():
            rows.append({"said": f"{100*lo:.0f}-{100*min(hi,1):.0f}%", "n": int(m.sum()),
                         "said_avg_pct": round(100 * float(p[m].mean()), 2),
                         "happened_pct": round(100 * float(y[m].mean()), 2)})
    return rows


def main(out: Path | None = None) -> None:
    """`out`: write the models AND the report there, leaving the live ones alone."""
    import gauge_week                      # here, not at the top: gauge_week imports this module
    models, report_path = (out, out / "flood_when_gauge.json") if out else (MODELS, REPORTS / "flood_when_gauge.json")
    print(f"Flood WHEN + latest river reading -> {models}\n  loading gauges...")
    tables, registry = gauge_week.build_tables(gauge_week.station_days())
    models.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"what": ("P(river reaches its threshold on day D), rain on D plus the gauge "
                       "reading L days earlier, vs the same pipeline on rain alone. "
                       "Year-grouped out-of-fold, calibrated out-of-fold."),
              "n_stations": len(registry), "leads": {}}

    for L in LEADS:
        df = tables[L]
        df = df[df["g_frac"].notna()].reset_index(drop=True)   # identical rows for both
        print(f"\n  lead {L} day(s): {len(df):,} gauge-days, {int(df['flood'].sum()):,} flood days")
        p_g = oof(df, FEATS, by="state")
        p_r = oof(df, RAIN_FEATS, by="none")
        y = df["flood"].to_numpy()
        onset = river_state(df) == 0
        off = df["official"].to_numpy(bool)
        subsets = {"all days": np.ones(len(df), bool), "onset only": onset,
                   "official danger level": off, "official, onset only": off & onset}
        res = {}
        for name, m in subsets.items():
            res[name] = {"rain + gauge": grade(y[m], p_g[m]), "rain only": grade(y[m], p_r[m])}
            g, r = res[name]["rain + gauge"], res[name]["rain only"]
            print(f"    {name:<24} AUC {r['auc']} -> {g['auc']}   skill {r['brier_skill']} -> "
                  f"{g['brier_skill']}   top1% said/happened {g['top1pct_said']}/{g['top1pct_happened']}%")
        # the simplest possible rival: "tomorrow looks like the last reading"
        pers = ~onset
        res["persistence (last reading above threshold)"] = {
            "floods_caught_pct": round(100 * float(pers[y == 1].mean()), 1),
            "warnings_right_pct": round(100 * float(y[pers].mean()), 1)}
        res["reliability, rain + gauge"] = reliability(y, p_g)
        res["reliability, rain + gauge, onset only"] = reliability(y[onset], p_g[onset])
        report["leads"][str(L)] = res

        with open(models / f"lead{L}.pkl", "wb") as fh:
            pickle.dump({**fit_final(df, FEATS, by="state"), "lead": L}, fh)

    # The rain-only fallback: every gauge-day (reading or not), calibrated per
    # label kind with the river's state unknown — exactly how it is used.
    fb = tables[1]
    p_fb = oof(fb, RAIN_FEATS, by="kind")
    y_fb, off_fb = fb["flood"].to_numpy(), fb["official"].to_numpy(bool)
    report["rain_only_fallback"] = {}
    for name, m in (("official danger level", off_fb), ("own top 2%", ~off_fb)):
        g = grade(y_fb[m], p_fb[m])
        report["rain_only_fallback"][name] = {**g, "reliability": reliability(y_fb[m], p_fb[m])}
        print(f"\n  rain-only fallback, {name}: AUC {g['auc']}, top1% said/happened "
              f"{g['top1pct_said']}/{g['top1pct_happened']}%")
    with open(models / "rain_only.pkl", "wb") as fh:
        pickle.dump({**fit_final(fb, RAIN_FEATS, by="kind"), "lead": None}, fh)
    (models / "stations.json").write_text(json.dumps(registry, indent=2))
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n  wrote {models} and {report_path}")
    gauge_week.fit_levels(tables, registry, models)     # the level line's models, beside them


if __name__ == "__main__":
    import argparse

    import train_flood_when_gauge as this    # run as the module gauge_week imports, not a second copy
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=None,
                    help="write a full set of models and the report here instead of replacing the live ones")
    this.main(ap.parse_args().out)
