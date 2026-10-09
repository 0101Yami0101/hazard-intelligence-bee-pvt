"""Can the satellite grade the map's area outlook? Tested on a past monsoon
before anything relies on it.

    python scripts/model/check_map_grader.py [year]        # default 2024

Reads   data/interim/flood_forecast/s1_cell_water.parquet  (fetch_38)
Writes  reports/flood_map_grader_check_<year>.json

The river forecasts grade themselves against the gauges. The map's area
outlook has no such feed: its truth so far was news-reported floods
confirmed by Sentinel-1, which arrive late and patchily. fetch_38 measures,
for every satellite pass and every ~10 km rain cell, the share of low
ground under NEW water. This asks whether that measurement can stand in as
the map's automatic truth.

The grader:  "excess water" = a cell's new-water share on this pass minus
its typical share over that monsoon's passes (median). In the monsoon every
river is wider than in March, so raw new water is high everywhere; only the
excess says "wetter than usual for here".

Two questions, answered separately:
  (a) Do known floods stand out?  Cell-passes with a confirmed flood report
      in that cell within +-2 days (report dates are loose, §0l) against all
      other cell-passes. ⚠️ Partly circular: those reports were confirmed
      with this same satellite. It still measures what matters, the grader's
      noise — how many unreported cells look just as wet.
  (b) Does the forecast agree with the grader?  The replay day model (tree
      2015-20, calibration 2021-22, so the tested year is unseen) scores
      each cell-day as times its own normal; how well does that rank the
      grader's wettest cell-passes above the rest?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

import when_grid
from common import INTERIM, ROOT
from flood_forecast import DayModel, day_features, label_matrix, load_events, years

WATER = INTERIM / "flood_forecast" / "s1_cell_water.parquet"
MIN_LOW_PX = 200          # 50 m pixels -> 0.5 km2 of low ground actually seen
TOP_SHARES = (0.01, 0.02, 0.05)


def grader(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["n_low"] >= MIN_LOW_PX].copy()
    # one row per cell per day (two passes the same day: keep the wetter)
    df = df.sort_values("new_water").drop_duplicates(["date", "k"], keep="last")
    df["excess"] = df["new_water"] - df.groupby("k")["new_water"].transform("median")
    return df


def replay_ratio(dates: pd.DatetimeIndex, W: np.ndarray) -> np.ndarray:
    E = np.load(ROOT / "models" / "flood_forecast" / "exposure_km2.npy")
    sus = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
              ["channel_shift_suspects"]["uuids"])
    ev = load_events()
    Y = label_matrix(ev[~ev["uuid"].isin(sus)], dates, W.shape[1])
    F = day_features(W, upstream=True)
    m, _ = DayModel.fit(F, E, Y, years(dates, 2015, 2020), years(dates, 2021, 2022))
    P = m.predict(F, E)
    return P / np.nanmean(P[years(dates, 2015, 2022)], axis=0)[None, :]


def auc(y, s):
    ok = np.isfinite(s)
    y, s = np.asarray(y)[ok], np.asarray(s)[ok]
    return round(float(roc_auc_score(y, s)), 3) if 0 < y.sum() < len(y) else None


def main() -> None:
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    raw = pd.read_parquet(WATER)
    raw = raw[pd.to_datetime(raw["date"]).dt.year == year]
    g = grader(raw)
    g["date"] = pd.to_datetime(g["date"])
    print(f"Map grader check, {year} monsoon: {g['date'].nunique()} pass days, "
          f"{len(g):,} cell-passes, {g['k'].nunique()} cells")

    # (a) known floods
    sus = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
              ["channel_shift_suspects"]["uuids"])
    ev = load_events()
    ev = ev[~ev["uuid"].isin(sus) & (ev["date"].dt.year == year) & (ev["k"] >= 0)]
    hit = np.zeros(len(g), bool)
    for _, e in ev.iterrows():
        hit |= ((g["k"].to_numpy() == e["k"])
                & (np.abs((g["date"] - e["date"]).dt.days.to_numpy()) <= 2))
    g["reported_flood"] = hit
    a = {"n_reported_cell_passes": int(hit.sum()),
         "auc_excess": auc(hit, g["excess"].to_numpy()),
         "auc_raw_new_water": auc(hit, g["new_water"].to_numpy())}
    for s in TOP_SHARES:
        thr = g["excess"].quantile(1 - s)
        top = g["excess"] >= thr
        a[f"top_{int(100*s)}pct"] = {
            "excess_at_least": round(float(thr), 4),
            "reported_floods_inside_pct": round(100 * float(top[hit].mean()), 1) if hit.any() else None,
            "cell_passes": int(top.sum()),
            "of_which_reported_pct": round(100 * float(hit[top].mean()), 2)}
    print(f"\n  (a) do reported floods stand out?  {a['n_reported_cell_passes']} reported "
          f"cell-passes;  AUC excess {a['auc_excess']}  (raw new water {a['auc_raw_new_water']})")
    for s in TOP_SHARES:
        t = a[f"top_{int(100*s)}pct"]
        print(f"      wettest {int(100*s)}%: holds {t['reported_floods_inside_pct']}% of reported "
              f"floods; {t['of_which_reported_pct']}% of it was reported")

    # (b) forecast vs grader
    dates, W = when_grid.load()
    dates = pd.DatetimeIndex(dates)
    R = replay_ratio(dates, np.asarray(W))
    pos = pd.Series(np.arange(len(dates)), index=dates)
    ok = g["date"].isin(dates)
    gg = g[ok].copy()
    gg["forecast_x_normal"] = R[pos[gg["date"]].to_numpy(), gg["k"].to_numpy()]
    # "day before" counts too: floods and passes are rarely on the same day
    gg["forecast_x_normal_pm1"] = np.fmax(
        gg["forecast_x_normal"],
        R[np.maximum(pos[gg["date"]].to_numpy() - 1, 0), gg["k"].to_numpy()])
    f = gg["forecast_x_normal_pm1"].to_numpy()
    b = {"n_cell_passes": int(len(gg)),
         "spearman_forecast_vs_excess": round(float(spearmanr(f, gg["excess"], nan_policy="omit")[0]), 3)}
    for s in TOP_SHARES:
        top = (gg["excess"] >= gg["excess"].quantile(1 - s)).to_numpy()
        b[f"auc_forecast_for_wettest_{int(100*s)}pct"] = auc(top, f)
    b["auc_forecast_for_reported_floods"] = auc(gg["reported_flood"].to_numpy(), f)
    print(f"\n  (b) does the forecast agree?  {b['n_cell_passes']:,} cell-passes;  "
          f"rank correlation {b['spearman_forecast_vs_excess']}")
    for s in TOP_SHARES:
        print(f"      forecast AUC for the grader's wettest {int(100*s)}%: "
              f"{b[f'auc_forecast_for_wettest_{int(100*s)}pct']}")
    print(f"      forecast AUC for reported floods on pass days: {b['auc_forecast_for_reported_floods']}")

    # named day: 30 Jun 2024
    near = gg[(gg["date"] >= "2024-06-28") & (gg["date"] <= "2024-07-03")]
    c = {}
    if len(near):
        c = {"cell_passes": int(len(near)),
             "median_excess": round(float(near["excess"].median()), 4),
             "median_excess_whole_season": round(float(gg["excess"].median()), 4),
             "share_in_season_top5pct": round(100 * float(
                 (near["excess"] >= gg["excess"].quantile(0.95)).mean()), 1)}
        print(f"\n  28 Jun - 3 Jul 2024: {c['cell_passes']} cell-passes, "
              f"{c['share_in_season_top5pct']}% in the season's wettest 5%")

    out = ROOT / "reports" / f"flood_map_grader_check_{year}.json"
    out.write_text(json.dumps({"year": year, "grader": "new-water share on low ground minus "
                               "the cell's median over the season's passes",
                               "a_known_floods": a, "b_forecast_vs_grader": b,
                               "end_june_2024": c}, indent=2))
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
