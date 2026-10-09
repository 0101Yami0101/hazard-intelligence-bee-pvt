"""The river's own week, and a forecast of the level itself.

What a gauge's readings say at the last complete day beyond the daily high
the gauge models already read, and the level model built on it
(docs/design/FLOOD_WHEN_PILOT_PLAN.md §14).

    station_days()   every gauge's cleaned record by day: high, first and last
                     reading, how many readings — same cleaning and trimming
                     as train_flood_when_gauge.station_daily
    week_inputs()    the six inputs, per day, in the gauge's own units
    build_tables()   train_flood_when_gauge.build_tables' tables with the six
                     inputs and the target day's level added
    level_oof()      year-grouped out-of-fold low / middle / high of the
                     change in the daily high, the range set on other years

    python scripts/model/gauge_week.py --out models/flood_when_gauge_next
                     fits the level models (leads 1-7) into that folder,
                     beside whatever chance models are there. Nothing reads
                     them yet: the level line is not on screen.

All six inputs can be read from three readings a day as well as from hourly:
half of CWC's days are three a day (08:00, 13:00, 18:00), §14a.
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
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold

import train_flood_when_gauge as T
from backtest_flood_when import clean_readings
from backtest_flood_when_nwdp import SENTINEL_ABS, load_all
from common import GAUGES
from flood_stations import STATIONS as CWC_STATIONS
from gauge_records import trim
from nwdp_stations import STATIONS as NWDP_STATIONS

WEEK_DAYS, WEEK_MIN = 7, 4          # the week's figures need 4 of the 7 days
QUANTILES = (0.1, 0.5, 0.9)         # low, middle, high
LEVEL_LEADS = tuple(range(1, 8))
# How far ahead the line may be drawn. The test of 2026-10-06 (§14): the middle
# line beats "no change" and the range is honest at every lead to 7, but the
# line and the chance agree only at 1 and 2.
DRAW_TO_LEAD = 2
COVER = 0.8                         # what the low-high range should hold
RANGE_MIN_DAYS = 100                # a thinner group takes the pooled adjustment


# ── the record by day ────────────────────────────────────────────────────
def _by_day(t: pd.Series, v: pd.Series) -> pd.DataFrame:
    g = pd.DataFrame({"t": t.to_numpy(), "v": v.to_numpy()}).sort_values("t", kind="stable")
    k = g.groupby(g["t"].dt.normalize())["v"]
    out = pd.DataFrame({"high": k.max(), "first": k.first(), "last": k.last(), "n": k.count()})
    out.index.name = None
    return out.sort_index()


def station_days() -> list[dict]:
    """station_daily's gauges, each with its record by day. `daily` (the
    day's high) is the series station_daily returns."""
    out = []
    for code, meta in CWC_STATIONS.items():
        print(f"  CWC  {meta['name']}")
        df = clean_readings(pd.read_csv(GAUGES / "cwc" / f"{code}_hhs.csv", parse_dates=["datetime"]))
        out.append({"code": code, "network": "CWC", "meta": meta,
                    "days": _by_day(df["datetime"], df["level"]), "danger": meta["danger_level"]})
    raw = load_all()
    for code, meta in NWDP_STATIONS.items():
        print(f"  NWDP {meta['name']}")
        g = raw.loc[raw["Station"] == code, ["ts", "discharge"]].dropna()
        g = g.loc[~((g["discharge"].abs() >= SENTINEL_ABS) | (g["discharge"] < 0)
                    | (g["ts"] < pd.Timestamp("2020-01-01")))]       # as daily_max_discharge
        d = _by_day(g["ts"], g["discharge"])
        if len(d) >= 30:
            out.append({"code": code, "network": "NWDP", "meta": meta, "days": d, "danger": None})
    for s in out:
        s["daily"] = trim(s["code"], s["days"]["high"])
        s["days"] = s["days"].loc[s["daily"].index]
    return out


# ── the six inputs ───────────────────────────────────────────────────────
def week_inputs(days: pd.DataFrame, sc: dict) -> pd.DataFrame:
    """Indexed by DAY, not yet shifted to a target day: the six inputs as
    that day's readings give them, in the gauge's own units (0 = its
    ordinary level, 1 = its line)."""
    span = sc["threshold"] - sc["base"]
    d = days.asfreq("D")
    f = (d["high"] - sc["base"]) / span
    above = (d["high"] >= sc["threshold"]).astype(float).where(d["high"].notna())
    return pd.DataFrame({
        "rise3": f - f.shift(3),
        "mean7": f.rolling(WEEK_DAYS, min_periods=WEEK_MIN).mean(),
        "max7": f.rolling(WEEK_DAYS, min_periods=WEEK_MIN).max(),
        "above7": above.rolling(WEEK_DAYS, min_periods=WEEK_MIN).sum(),
        "end": (d["last"] - sc["base"]) / span,
        "day_rise": ((d["last"] - d["first"]) / span).where(d["n"] >= 2),
    })[T.WEEK_FEATS]


def build_tables(stations: list[dict]) -> tuple[dict[int, pd.DataFrame], dict]:
    """The gauge tables, row for row, plus the six inputs as they stood
    `lead` days before the target day, and `level`: the target day's high in
    the gauge's own units."""
    tables, registry = T.build_tables(stations)
    by_code = {s["code"]: s for s in stations}
    out = {}
    for L, tb in tables.items():
        parts = []
        for code, g in tb.groupby("station_code", sort=False):
            s, sc = by_code[code], registry[code]
            level = (s["daily"] - sc["base"]) / (sc["threshold"] - sc["base"])
            parts.append(g.join(week_inputs(s["days"], sc).shift(L), on="date")
                          .assign(level=level.reindex(g["date"]).to_numpy()))
        out[L] = pd.concat(parts).sort_index()
        assert out[L].index.equals(tb.index)
    return out, registry


# ── the level model ──────────────────────────────────────────────────────
def level_model(q: float) -> HistGradientBoostingRegressor:
    """The chance model's own tree settings, on a quantile of the change."""
    return HistGradientBoostingRegressor(loss="quantile", quantile=q, max_depth=3, max_iter=150,
                                         learning_rate=0.08, l2_regularization=1.0, random_state=0)


def change(df: pd.DataFrame) -> np.ndarray:
    """What the level model forecasts: the target day's high minus the last
    complete day's, in the gauge's own units."""
    return (df["level"] - df["g_frac"]).to_numpy()


def _raw_level_oof(df, cols, folds) -> np.ndarray:
    X, y = df[cols], change(df)
    out = np.full((len(df), len(QUANTILES)), np.nan)
    for tr, te in folds:
        for i, q in enumerate(QUANTILES):
            out[te, i] = level_model(q).fit(X.iloc[tr], y[tr]).predict(X.iloc[te])
    return np.sort(out, axis=1)


def range_margins(raw: np.ndarray, y: np.ndarray, g: np.ndarray) -> dict:
    """How much to widen (+) or narrow (-) the low-high range so that it holds
    COVER of outcomes: one margin per river state x kind of line, as the
    chance curves; a thin group takes the pooled one."""
    def margin(m):
        miss = np.maximum(raw[m, 0] - y[m], y[m] - raw[m, -1])     # how far outside the range (<0: inside)
        return float(np.quantile(miss, min(1.0, COVER * (1 + 1 / m.sum()))))
    pooled = margin(np.ones(len(y), bool))
    return {k: margin(g == k) if (g == k).sum() >= RANGE_MIN_DAYS else pooled for k in range(4)}


def apply_margins(raw: np.ndarray, g: np.ndarray, margins: dict) -> np.ndarray:
    e = np.array([margins[int(k)] for k in g])
    mid = raw[:, 1]
    return np.column_stack([np.minimum(raw[:, 0] - e, mid), mid, np.maximum(raw[:, -1] + e, mid)])


def level_oof(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """Year-grouped out-of-fold low / middle / high of the CHANGE, the range
    margin set on the other years' out-of-fold forecasts — the discipline of
    train_flood_when_gauge.oof."""
    y, g = change(df), T.cal_group(df)
    folds = list(GroupKFold(n_splits=T.N_FOLDS).split(df, groups=df["date"].dt.year))
    raw = _raw_level_oof(df, cols, folds)
    out = np.full_like(raw, np.nan)
    for tr, te in folds:
        out[te] = apply_margins(raw[te], g[te], range_margins(raw[tr], y[tr], g[tr]))
    return out


def fit_level_final(df: pd.DataFrame, cols: list[str]) -> dict:
    """The level model as it would run: the three models on everything, the
    range margins on the out-of-fold forecasts (as fit_final's calibrators)."""
    y, g = change(df), T.cal_group(df)
    folds = list(GroupKFold(n_splits=T.N_FOLDS).split(df, groups=df["date"].dt.year))
    raw = _raw_level_oof(df, cols, folds)
    return {"models": {q: level_model(q).fit(df[cols], y) for q in QUANTILES},
            "margins": range_margins(raw, y, g), "features": cols}


def fit_levels(tables: dict, registry: dict, out: Path) -> None:
    """The level models, from build_tables' tables, into `out`."""
    feats = T.OLD_FEATS + T.WEEK_FEATS
    out.mkdir(parents=True, exist_ok=True)
    for L in LEVEL_LEADS:
        df = tables[L][tables[L]["g_frac"].notna()].reset_index(drop=True)
        with open(out / f"level{L}.pkl", "wb") as fh:
            pickle.dump({**fit_level_final(df, feats), "lead": L}, fh)
        print(f"  level, lead {L}: {len(df):,} gauge-days")
    (out / "level.json").write_text(json.dumps({
        "what": ("low / middle / high of the CHANGE in the daily high from the last complete day, in the "
                 "gauge's own units (0 = its ordinary level, 1 = its line); level = base + "
                 "(g_frac + change) x (threshold - base), from stations.json"),
        "quantiles": list(QUANTILES), "range_should_hold": COVER, "features": feats,
        "leads": list(LEVEL_LEADS), "draw_to_lead": DRAW_TO_LEAD,
        "test": "docs/design/FLOOD_WHEN_PILOT_PLAN.md §14; reports/gauge_week_check.json",
        "gauges": len(registry)}, indent=2))
    print(f"  wrote the level models to {out}")


def main(out: Path) -> None:
    print(f"River level models -> {out}\n  loading gauges...")
    tables, registry = build_tables(station_days())
    fit_levels(tables, registry, out)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Fit the river level models into a folder.")
    ap.add_argument("--out", type=Path, required=True)
    main(ap.parse_args().out)
