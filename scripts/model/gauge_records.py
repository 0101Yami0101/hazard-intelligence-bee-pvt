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
    # SUSPECTED, not applied: Changlang_1's quarterly median flow jumps ~10x from
    # 2024 to 2025 (Q3: 8 -> 87 m3/s). Check before its next retrain (§13e).
}


def trim(code: str, daily: pd.Series) -> pd.Series:
    """The daily series from the gauge's usable start on."""
    start = RECORD_STARTS.get(code)
    return daily[daily.index >= start] if start else daily
