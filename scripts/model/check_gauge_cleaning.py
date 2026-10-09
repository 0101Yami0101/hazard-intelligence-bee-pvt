"""Does the gauge-reading cleaning remove what it should, and ONLY that?

    python scripts/model/check_gauge_cleaning.py            # both parts
    python scripts/model/check_gauge_cleaning.py behaviour  # made-up series, seconds
    python scripts/model/check_gauge_cleaning.py history    # every CWC gauge's record

Run after ANY change to backtest_flood_when.clean_readings (the cleaning the
live run, the training and the backtests all share). The golden check cannot
do this job: it replays daily highs that were already cleaned.

    behaviour   made-up series with a known answer: slips that must go,
                and real river behaviour that must stay — a surge, a flood
                that recedes, a re-levelled gauge, the newest reading, a
                stretch where wrong readings outnumber the true ones
    history     what each pass removes from the full record, how many
                high-water days that changes, which high-water days still
                look odd afterwards, and that the real October 2018
                landslide-dam surge at Tuting is untouched

Exit code 1 if any behaviour check fails or the Tuting surge loses a reading.
docs/design/FLOOD_WHEN_PILOT_PLAN.md §13f-§13g.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import backtest_flood_when as B
from common import ROOT

GAUGES = ROOT / "data" / "raw" / "11_gauges" / "cwc"
STATIONS = ROOT / "models" / "flood_when_gauge" / "stations.json"
NONE = lambda t, v: np.zeros(len(v), bool)                 # noqa: E731  a pass switched off


def cleaned(df: pd.DataFrame, pass2: bool = True, pass3: bool = True) -> pd.DataFrame:
    """clean_readings with the later passes on or off, printing nothing."""
    keep = B.impossible_excursions, B.keying_slips
    B.impossible_excursions = keep[0] if pass2 else NONE
    B.keying_slips = keep[1] if pass3 else NONE
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return B.clean_readings(df.copy())
    finally:
        B.impossible_excursions, B.keying_slips = keep


def removed(t, x) -> np.ndarray:
    df = pd.DataFrame({"datetime": t, "level": x})
    return ~df.index.isin(cleaned(df).index)


# ── made-up series with a known answer ────────────────────────────────────
def behaviour() -> bool:
    print("BEHAVIOUR — made-up series with a known answer\n")
    h60 = np.array(pd.date_range("2026-09-27", periods=60, freq="h"))
    base = 2134.30 + 0.01 * np.sin(np.arange(60))
    d30 = np.array(pd.date_range("2022-11-20", periods=30, freq="8h"))       # 3 readings a day
    b30 = 270.8 + 0.01 * np.sin(np.arange(30))

    def s(**kw):                       # base with changes: s(at=35, to=2231.30)
        x = kw.get("of", base).copy()
        if "at" in kw:
            x[kw["at"]] = kw["to"]
        return x

    add = lambda sl, d, of=base: (lambda x: (x.__setitem__(sl, x[sl] + d), x)[1])(of.copy())  # noqa: E731
    cases = [
        ("Murga Bridge: one reading +97 m, back the next hour", h60, s(at=35, to=2231.30), 1),
        ("the same value as the NEWEST reading — nothing after it yet", h60, s(at=59, to=2231.30), 0),
        ("+143 m for 15 hours, then straight back", h60, add(slice(30, 45), 143.0), 15),
        ("real surge: +30 m in 6 h, receding over a day", h60,
         add(slice(30, 60), np.r_[np.linspace(0, 30, 6), np.linspace(30, 2, 24)]), 0),
        ("dam-break wave: +30 m in ONE hour, receding gradually", h60,
         add(slice(30, 60), np.r_[30.0, np.linspace(28, 1, 29)]), 0),
        ("a gauge re-levelled +25 m, and it stays", h60, add(slice(40, 60), 25.0), 0),
        ("one reading +3 m (a dam release can do this)", h60, add(35, 3.0), 0),
        ("a peaked 6-hour wave that drops back in one step", h60,
         add(slice(30, 36), np.array([25, 40, 55, 40, 25, 22.0])), 0),
        ("a real +10.0 m rise that stays", h60, add(slice(40, 60), 10.0), 0),
        ("+10.0 m, holds 2 hours, then recedes gradually", h60,
         add(slice(40, 60), np.r_[10.0, 10.0, np.linspace(9.5, 1, 18)]), 0),
        ("+10.0 m exactly, flat for 6 hours, then back", h60, add(slice(30, 36), 10.0), 0),
        ("3 readings a day: 370.80 for 270.80", d30, s(of=b30, at=15, to=370.80), 1),
        ("3 readings a day: one reading +6 m (could be a short flood)", d30, add(15, 6.0, b30), 0),
    ]
    p = 201.5 + 0.01 * np.sin(np.arange(60))
    p[[30, 31, 33]] = [210.50, 210.55, 210.53]
    cases.append(("Pangin: digits swapped (210.5 for 201.5), 3 readings alternating", h60, p, 3))
    q = 143.8 + 0.01 * np.sin(np.arange(60))
    q[30:33] = [134.80, 134.81, 134.82]
    cases.append(("Namsai: digits swapped, 3 readings in a row", h60, q, 3))

    ok = True
    for name, t, x, want in cases:
        got = int(removed(t, x).sum())
        ok &= got == want
        print(f"  {'ok  ' if got == want else 'FAIL'} {name:<62} removed {got:>2}  (want {want})")

    # where a second, wrong series is mixed in: count wrong and TRUE removals apart
    n = 8000
    t = np.array(pd.date_range("2018-01-01", periods=n, freq="h"))
    true = 189.5 + 0.3 * np.sin(np.arange(n) / 40)
    t3 = np.array(pd.date_range("2018-01-01", periods=900, freq="8h"))
    true3 = 189.5 + 0.3 * np.sin(np.arange(900) / 9)
    seg = np.arange(4000, 4060)
    mixes = []
    for label, off, idx in (
            ("a second series 161 m LOW on every other reading (starts from a true level)", -161.0,
             np.arange(4000, 4040, 2)),
            ("wrong series 161 m LOW outnumbers the true 3 to 1 for 60 hours", -161.0, seg[seg % 4 != 0]),
            ("wrong series 25 m LOW outnumbers the true 3 to 1 for 60 hours", -25.0, seg[seg % 4 != 0]),
            ("wrong series 25 m HIGH outnumbers the true 3 to 1 for 60 hours", 25.0, seg[seg % 4 != 0])):
        x, wrong = true.copy(), np.zeros(n, bool)
        wrong[idx] = True
        x[wrong] += off
        mixes.append((label, t, x, wrong))
    x, wrong = true3.copy(), np.zeros(900, bool)
    wrong[450:456] = True
    x[wrong] -= 161.0
    mixes.append(("3 readings a day: two whole days 161 m low, true before and after", t3, x, wrong))
    print()
    for label, tt, x, wrong in mixes:
        rm = removed(tt, x)
        lost = int((rm & ~wrong).sum())
        ok &= lost == 0
        print(f"  {'ok  ' if lost == 0 else 'FAIL'} {label:<74} wrong removed {int((rm & wrong).sum()):>2}/"
              f"{int(wrong.sum()):<2}  TRUE removed {lost}  (want 0)")
    floods = [("3 readings a day: a real 4 m flood over five days", t3,
               true3 + np.r_[np.zeros(450), np.linspace(0.5, 4, 6), np.linspace(3.8, 0.2, 9), np.zeros(435)]),
              ("hourly: a real 12 m flood, up in 10 h, down over 2 days", t,
               true + np.r_[np.zeros(4000), np.linspace(0, 12, 10), np.linspace(12, 0.2, 48), np.zeros(n - 4058)])]
    for label, tt, x in floods:
        got = int(removed(tt, x).sum())
        ok &= got == 0
        print(f"  {'ok  ' if got == 0 else 'FAIL'} {label:<74} removed {got}  (want 0)")
    print(f"\n  BEHAVIOUR: {'PASS' if ok else 'FAIL'}")
    return ok


# ── every CWC gauge's full record ─────────────────────────────────────────
def history() -> bool:
    print("\nHISTORY — every CWC gauge's full record\n")
    st = json.loads(STATIONS.read_text())
    tot = {"p2": 0, "p3": 0, "d2": 0, "d3": 0, "n": 0}
    final = {}
    print(f"  {'gauge':<14}{'readings':>10}   pass 2   pass 3    days at/above its line (before -> after)")
    for f in sorted(GAUGES.glob("*_hhs.csv")):
        code = f.stem.replace("_hhs", "")
        raw = pd.read_csv(f, parse_dates=["datetime"]).dropna(subset=["level"])
        a = cleaned(raw, False, False)
        b = cleaned(raw, True, False)
        c = cleaned(raw, True, True)
        final[code] = c
        thr = st[code]["threshold"]
        days = lambda d: int((d.groupby(d["datetime"].dt.normalize())["level"].max() >= thr).sum())  # noqa: E731
        da, db, dc = days(a), days(b), days(c)
        tot["p2"] += len(a) - len(b)
        tot["p3"] += len(b) - len(c)
        tot["d2"] += da - db
        tot["d3"] += db - dc
        tot["n"] += len(a)
        print(f"  {st[code]['name']:<14}{len(a):>10,}{len(a) - len(b):>9}{len(b) - len(c):>9}    "
              f"{da:>4} -> {dc:<4}" + (f"  ({da - dc} false)" if da != dc else ""))
    print(f"\n  {tot['n']:,} readings. Pass 2 removes {tot['p2']} ({tot['d2']} false high-water days); "
          f"pass 3 removes {tot['p3']} ({tot['d3']}).")

    print("\n  high-water days that still look odd (the day's high over 5 m above its own middle reading):")
    odd = 0
    for code, df in final.items():
        thr = st[code]["threshold"]
        g = df.groupby(df["datetime"].dt.normalize())["level"]
        q = pd.DataFrame({"max": g.max(), "med": g.median(), "n": g.size()})
        for d, r in q[(q["max"] >= thr) & (q["max"] - q["med"] > 5)].iterrows():
            odd += 1
            print(f"    {st[code]['name']:<12} {d.date()}  high {r['max']:.2f}  middle {r['med']:.2f}  "
                  f"line {thr:.2f}  ({int(r['n'])} readings)")
    print(f"    {odd} in all")

    raw = pd.read_csv(GAUGES / "002-ubddib_hhs.csv", parse_dates=["datetime"]).dropna(subset=["level"])
    win = lambda d: d[(d["datetime"] >= "2018-10-17") & (d["datetime"] < "2018-10-23")]  # noqa: E731
    a, c = win(raw), win(final["002-ubddib"])
    kept = len(a) == len(c) and float(a["level"].max()) == float(c["level"].max())
    print(f"\n  Tuting, 17-22 Oct 2018 (the landslide-dam surge, a REAL 12-14 m rise): "
          f"{len(c)} of {len(a)} readings kept, highest {c['level'].max():.2f} m — "
          f"{'untouched' if kept else 'READINGS LOST'}")
    print(f"\n  HISTORY: {'PASS' if kept else 'FAIL'}")
    return kept


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    ok = True
    if part in ("all", "behaviour"):
        ok &= behaviour()
    if part in ("all", "history"):
        ok &= history()
    sys.exit(0 if ok else 1)
