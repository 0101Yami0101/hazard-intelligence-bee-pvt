"""Where each gauge's usable record starts — one list, shared by every
script that turns gauge readings into labels or inputs.

Some gauges change scale partway through their record (a re-levelled datum,
or a changed rating/sensor). Found 2026-09-21 by comparing each year's
5th-95th percentile range. A threshold or "ordinary level" taken across the
break is wrong on both sides, so only the record from the break on is used.

The backtest scripts that produced the flood-day lists the WHERE work was
built from (backtest_flood_when*.py) predate this and are deliberately left
alone: those lists fixed which satellite scenes were checked, and changing
them now would not change the checks already made.
"""
from __future__ import annotations

import pandas as pd

RECORD_STARTS = {
    # Ziro 2023-24 (100-5,900 m3/s) looks like another river altogether: its raw
    # NWDP coordinates sit on the Alaknanda, Uttarakhand (FLOOD_WHEN_PILOT_PLAN §13e)
    "Ziro": "2025-03-01",        # 2023-24 dry season 100-2,700 m3/s; 2025 on 0-194
    "009-UBDDIB": "2019-06-01",  # Namsai: level steps up ~5 m during 2019
    "058-UBDDIB": "2022-01-01",  # Doimukh: 2019-21 sits ~22 m lower, then back
    "059-UBDDIB": "2021-01-01",  # Pagoda: 2019-20 sits ~15 m lower
    # Changlang (2nd station): 2024 is on another scale. For the same rain
    # (Apr-Aug mean 7-day rain 0.6 / 0.5 / 0.6) its median flow was 24 m3/s in
    # 2024 against 109 and 104 in 2025 and 2026, and against the first
    # Changlang station it read 0.15x in 2024, 1.3x in 2025. No readings from
    # Oct 2024 to Jan 2025; the record is used from where it resumes. Its own
    # top-2% line moves 594 -> 691 m3/s (10 -> 8 days at it). Checked
    # 2026-10-10 (FLOOD_WHEN_PILOT_PLAN.md §19); takes effect at the next
    # re-teach of the gauge models — the daily run reads the trained
    # stations.json, not this.
    "Changlang_1": "2025-02-01",
    # NOT a break, left whole: Rho Basti (001NEID3). Its levels have eased
    # about 2-3 cm a year since 2016 for the same rain, with no step to date,
    # so 71 of the 91 days at its top-2% line are 2016-17 and one is since
    # 2021. A line from recent years alone would relabel ordinary days as
    # floods with nothing to confirm them. Wants CWC's real danger level
    # (§19).
}


# Gauges whose level is not forecast: no dotted level line is issued, drawn or
# graded for them. code -> the reason, as the screen says it.
#
# Pare HEP (078-UBDDIB) sits at a hydro-power dam. Measured on its whole
# record (62 days from 2026-06-18), against the 17 other CWC level gauges:
#   - a typical day-to-day move of 0.36 m (theirs: 0.01-0.22 m);
#   - its day-to-day move on one day in ten (1.04 m) is bigger than the whole
#     gap between its usual level and its line (0.84 m): 1.24 of it, where no
#     other gauge is above 0.27;
#   - on 57% of days the day's high stands more than 0.5 m above BOTH the
#     first and the last reading — a release in the middle of the day; at the
#     others, 0-8% of days.
# The level model learned how rivers rise and fall on rain; this one rises
# when the gates open. In the five days it was graded the line's range held
# on one (typical miss 0.73 m, against 0.04 m for the rest). What would
# forecast it is the dam's release schedule (on the ask list).
# FLOOD_WHEN_PILOT_PLAN.md §20, 2026-10-11.
NO_LEVEL_LINE = {
    "078-UBDDIB": ("Dam gauge: its level follows the power station's releases, not the rain, "
                   "so no level line is drawn for it."),
}


def trim(code: str, daily: pd.Series) -> pd.Series:
    """The daily series from the gauge's usable start on."""
    start = RECORD_STARTS.get(code)
    return daily[daily.index >= start] if start else daily
