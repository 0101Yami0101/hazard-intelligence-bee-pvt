"""WHEN rollout, pass 2 — backtest the rainfall rule against the 14 NWDP
small-river discharge stations (see FLOOD_WHEN_PILOT_PLAN.md §8's planned
"different pass" for these, after the 17 CWC stations).

    python scripts/model/backtest_flood_when_nwdp.py

Outputs:
    data/interim/flood_when/nwdp_flood_days.csv   -- flood-day labels, all 14 stations
    reports/flood_when_backtest_nwdp.json          -- baseline score, all 14 stations

Reuses backtest_flood_when.py's derive_flood_days() and trigger_series_at()
directly — same self-derived percentile method (no NWDP station publishes a
danger threshold at all, so every one of these 14 uses it, not just a
fallback for a few) and the same rainfall-trigger lookup.

════════════════════════════════════════════════════════════════════════════
WHY DISCHARGE NEEDS ITS OWN CLEANING PASS
════════════════════════════════════════════════════════════════════════════
CWC's level data had decimal-shift glitches (fixed with a rolling-MAD check,
see clean_readings() in backtest_flood_when.py). NWDP's raw discharge data
has a DIFFERENT, worse failure mode: explicit sentinel/fault codes baked
into the telemetry stream, not sensor drift — values pinned at exactly
-99999.99 / 99999.99 / 100000.00 (a "no data"/"fault" placeholder
convention), plus physically impossible negative discharge readings, on
every station checked. Filtered with hard physical/sentinel bounds (drop
|discharge| >= 50,000, drop discharge < 0), not the rolling-MAD approach —
these are not noisy-but-real readings to smooth around, they are dead give-
away fault codes to remove outright.

Also dropped: a handful of rows carrying a garbage 2000-01-10-ish timestamp
on 2 stations (Miao_2, Ziro) — already flagged in
docs/data_research/DATA_VERIFICATION.md as a generic template artefact, not
real historical data; every station's real record starts 2023-2025.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from backtest_flood_when import LAG_DAYS, derive_flood_days, trigger_series_at
from common import GAUGES, INTERIM, ROOT
from nwdp_stations import STATIONS

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
RESOURCES = ["9c755c40-389e-4f5d-92c6-b936d28e51b3", "9a7feb81-191e-45df-b808-cd9523a97356"]
DISCH_COL = "Telemetry Hourly River Water Discharge (m3/sec)"
SENTINEL_ABS = 50_000   # NWDP's fault-code convention pins at +-99999.99/100000.00


def load_all() -> pd.DataFrame:
    dfs = [pd.read_csv(GAUGES / "nwdp" / f"{r}.csv") for r in RESOURCES]
    df = pd.concat(dfs, ignore_index=True)
    df["discharge"] = pd.to_numeric(df[DISCH_COL], errors="coerce")
    df["ts"] = pd.to_datetime(df["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    return df


def daily_max_discharge(df: pd.DataFrame, station: str) -> pd.Series:
    g = df.loc[df["Station"] == station, ["ts", "discharge"]].dropna()
    before = len(g)
    # Sentinel/fault codes (exact convention: values pinned near +-99999.99
    # or 100000.00) and physically impossible negative discharge.
    bad = (g["discharge"].abs() >= SENTINEL_ABS) | (g["discharge"] < 0)
    # Garbage template timestamp (2 stations only) — real record starts 2023+.
    bad |= g["ts"] < pd.Timestamp("2020-01-01")
    g = g.loc[~bad]
    dropped = before - len(g)
    if dropped:
        print(f"    [clean] dropped {dropped} bad reading(s) "
              f"({100*dropped/before:.1f}% of {before:,})")
    g["date"] = g["ts"].dt.date
    s = g.groupby("date")["discharge"].max()
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def backtest_station(code: str, meta: dict, trig: pd.Series, df: pd.DataFrame) -> dict | None:
    daily = daily_max_discharge(df, code)
    if len(daily) < 30:
        print(f"    [skip] {meta['name']}: only {len(daily)} usable days")
        return None

    flood_days, label_info = derive_flood_days(daily)
    label_info["label_source"] = "self-derived (top 2% of own history) — no NWDP station publishes a danger threshold"

    aligned = trig.reindex(daily.index)
    lagged = pd.concat([aligned.shift(d) for d in range(LAG_DAYS + 1)], axis=1).max(axis=1)
    valid = lagged.notna()
    is_flood = daily.index.isin(flood_days)

    y, s = is_flood[valid.values], lagged[valid].values
    auc = None
    if 0 < y.sum() < len(y):
        auc = round(float(roc_auc_score(y, s)), 3)

    print(f"    {label_info['label_source'].split(' — ')[0]} "
          f"(threshold {label_info['percentile_threshold']}): "
          f"{len(flood_days)} flood days out of {len(daily):,}")
    if auc is not None:
        print(f"    AUC: {auc}")

    return {
        "station_code": code, "station_name": meta["name"], "district": meta["district"],
        "n_daily_readings": int(len(daily)), "auc": auc,
        "flood_day_label": {**label_info, "n_flood_days": int(len(flood_days))},
        "_flood_days": [str(d.date()) for d in flood_days],
    }


def main() -> None:
    print("WHEN rollout, pass 2 — backtest against NWDP's 14 small rivers\n")
    df = load_all()

    results, all_flood_rows = [], []
    for code, meta in STATIONS.items():
        print(f"  {meta['name']} ({code}, {meta['district']})")
        try:
            trig, cl = trigger_series_at(meta["lat"], meta["lon"])
        except RuntimeError as exc:
            print(f"    [skip] {exc}")
            continue
        r = backtest_station(code, meta, trig, df)
        if r is None:
            continue
        results.append(r)
        for d in r.pop("_flood_days"):
            all_flood_rows.append({"station_code": code, "station_name": meta["name"], "date": d})
        print()

    pd.DataFrame(all_flood_rows).to_csv(OUT / "nwdp_flood_days.csv", index=False)
    print(f"wrote {len(all_flood_rows)} flood-day labels -> {OUT / 'nwdp_flood_days.csv'}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "flood_when_backtest_nwdp.json").write_text(json.dumps({
        "n_stations": len(STATIONS), "n_stations_scored": len(results),
        "stations": {r["station_code"]: r for r in results},
    }, indent=2))
    print(f"wrote {REPORTS / 'flood_when_backtest_nwdp.json'}")

    aucs = [r["auc"] for r in results if r["auc"] is not None]
    if aucs:
        print(f"\nAUC across {len(aucs)} scored stations: min {min(aucs):.3f} "
              f"median {sorted(aucs)[len(aucs)//2]:.3f} max {max(aucs):.3f}")


if __name__ == "__main__":
    main()
