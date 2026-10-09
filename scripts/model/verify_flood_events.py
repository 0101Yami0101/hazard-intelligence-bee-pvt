"""Event-level verification — what the calibrated system actually said on
every real flood day in the record.

    python scripts/model/verify_flood_events.py

Output:
    reports/flood_when_event_verification.json

AUC and reliability curves are the right statistics, but they are not what
an official asks. The question that gets asked is "on the day the river
actually flooded, what did your system say?" — so this answers exactly that,
for every real flood day on record, and reports the misses as plainly as the
hits.

Two things worth reading carefully before quoting any of it:

  * **Every probability here is out-of-fold**, from the model's and the
    calibrator's own year-grouped CV — no flood day was scored by anything
    that had seen its year. These are honest hindcasts, not fitted-in-sample
    replays.
  * **Flood days come in runs.** 1,138 flood days are roughly 310 distinct
    episodes, so per-day hit rates count long episodes many times. Episode
    level is reported alongside, and is the fairer number.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from calibrate_flood_when import cv_calibrate, load_scores
from common import ROOT

REPORTS = ROOT / "reports"
BANDS = [(0.25, "SEVERE"), (0.10, "HIGH"), (0.05, "MODERATE"),
         (0.02, "ELEVATED"), (0.0, "NORMAL")]
EPISODE_GAP_DAYS = 3   # same rule used to count episodes elsewhere in this project


def band_for(p: float) -> str:
    return next(name for thr, name in BANDS if p >= thr)


def main() -> None:
    print("Event-level verification - what the system said on real flood days\n")
    df = load_scores()
    df["prob"] = cv_calibrate(df, "isotonic")
    df = df.dropna(subset=["prob"])
    df["band"] = [band_for(p) for p in df["prob"]]

    floods = df[df["flood"] == 1].sort_values(["station_code", "date"]).copy()

    # Group consecutive flood days into episodes, per station.
    floods["gap"] = floods.groupby("station_code")["date"].diff().dt.days
    floods["new_episode"] = (floods["gap"].isna()) | (floods["gap"] > EPISODE_GAP_DAYS)
    floods["episode_id"] = floods.groupby("station_code")["new_episode"].cumsum()

    n_days, n_eps = len(floods), floods.groupby(["station_code", "episode_id"]).ngroups
    print(f"{n_days:,} real flood days across {n_eps} distinct episodes, "
          f"{floods['station_code'].nunique()} stations\n")

    # Per-day hit rate by band
    day_counts = floods["band"].value_counts()
    print("What the system issued ON the flood day itself (per day):")
    order = [b for _, b in BANDS]
    for b in order:
        n = int(day_counts.get(b, 0))
        print(f"  {b:<10}{n:>6,}  ({100*n/n_days:>5.1f}%)")
    caught_day = int(sum(day_counts.get(b, 0) for b in ("ELEVATED", "MODERATE", "HIGH", "SEVERE")))
    print(f"  -> ELEVATED or above on {caught_day:,}/{n_days:,} flood days "
          f"({100*caught_day/n_days:.1f}%)")

    # Per-episode: the best band issued anywhere in the episode
    ep = (floods.groupby(["station_code", "station_name", "episode_id"])
                .agg(peak_prob=("prob", "max"), start=("date", "min"),
                     end=("date", "max"), days=("date", "size"))
                .reset_index())
    ep["peak_band"] = [band_for(p) for p in ep["peak_prob"]]
    ep_counts = ep["peak_band"].value_counts()
    print("\nPeak alert reached during each flood EPISODE (the fairer view):")
    for b in order:
        n = int(ep_counts.get(b, 0))
        print(f"  {b:<10}{n:>6,}  ({100*n/len(ep):>5.1f}%)")
    caught_ep = int(sum(ep_counts.get(b, 0) for b in ("ELEVATED", "MODERATE", "HIGH", "SEVERE")))
    print(f"  -> ELEVATED or above in {caught_ep}/{len(ep)} episodes "
          f"({100*caught_ep/len(ep):.1f}%)")

    # The biggest episodes, named - the pitch-ready detail
    biggest = ep.sort_values("days", ascending=False).head(12)
    print("\nThe longest real flood episodes on record, and what was issued:")
    print(f"  {'station':<18}{'dates':<26}{'days':>5}{'peak prob':>11}  band")
    for _, r in biggest.iterrows():
        span = f"{r['start'].date()} to {r['end'].date()}"
        print(f"  {r['station_name'][:17]:<18}{span:<26}{r['days']:>5}"
              f"{100*r['peak_prob']:>10.1f}%  {r['peak_band']}")

    # Honest miss list: episodes where the system never got above NORMAL
    missed = ep[ep["peak_band"] == "NORMAL"].sort_values("days", ascending=False)
    print(f"\nEpisodes the system never raised above NORMAL: {len(missed)}/{len(ep)}")
    for _, r in missed.head(10).iterrows():
        print(f"  {r['station_name'][:17]:<18}{str(r['start'].date()):<12}"
              f"{r['days']:>3}d  peak {100*r['peak_prob']:.2f}%")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_when_event_verification.json"
    out.write_text(json.dumps({
        "note": ("Every probability is out-of-fold from year-grouped CV of both "
                 "the model and the calibrator. Episode counting merges flood "
                 "days less than 3 days apart at the same station."),
        "n_flood_days": int(n_days),
        "n_episodes": int(n_eps),
        "per_day_band_counts": {b: int(day_counts.get(b, 0)) for b in order},
        "pct_flood_days_elevated_or_above": round(100 * caught_day / n_days, 1),
        "per_episode_peak_band_counts": {b: int(ep_counts.get(b, 0)) for b in order},
        "pct_episodes_elevated_or_above": round(100 * caught_ep / len(ep), 1),
        "longest_episodes": [
            {"station": r["station_name"], "start": str(r["start"].date()),
             "end": str(r["end"].date()), "days": int(r["days"]),
             "peak_probability_pct": round(100 * float(r["peak_prob"]), 1),
             "peak_band": r["peak_band"]}
            for _, r in biggest.iterrows()],
        "missed_episodes_never_above_normal": [
            {"station": r["station_name"], "start": str(r["start"].date()),
             "days": int(r["days"]),
             "peak_probability_pct": round(100 * float(r["peak_prob"]), 2)}
            for _, r in missed.iterrows()],
    }, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
