"""Are the readings the cleaning removes really false? Independent evidence
for each one, gathered BEFORE the gauge models are retrained on the cleaned
history (docs/design/FLOOD_WHEN_PILOT_PLAN.md §13g).

    python scripts/model/check_gauge_excursions.py          # offline, ~2 min
    python scripts/model/check_gauge_excursions.py --cwc    # also ask CWC's server

For every run of readings the second and third cleaning passes remove from
the CWC history, four tests that do NOT use those passes' own rules:

    still        the river did not move: the nearest kept readings before and
                 after agree to within 0.5 m (the value is 5 m to 1,000 m away)
    out of range the value is outside everything else this gauge has ever
                 recorded, or above CWC's own published highest-ever level
    slip         one keying slip undone puts it back BETWEEN its neighbours:
                 a multiple of 10 m added or taken off, two neighbouring
                 digits swapped, or the value halved
    other gauge  another CWC gauge read this very value (within 0.5 m)
                 within the hour — a reading logged under the wrong station

    certain = at least two of them, likely = one, judgement = none.

For the high-water days the cleaning takes away it also gives the 3-day rain
percentile at the gauge that day, and for Pangin what Pasighat — 50 km
downstream on the same river — read at the time.

Writes  reports/gauge_excursions_check.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import requests

import backtest_flood_when as B
import when_grid
from check_gauge_cleaning import GAUGES, STATIONS, cleaned
from common import ROOT, UA

LEVELS = ROOT / "webapp" / "assets" / "flood" / "gauge_levels.json"
CWC_API = "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/"
REPORT = ROOT / "reports" / "gauge_excursions_check.json"
STILL_M = 0.5
SAME_M = 0.5


def cwc_now(code: str, t0: pd.Timestamp, t1: pd.Timestamp) -> dict:
    """What CWC's server holds today for [t0, t1]: {time: level}."""
    f = lambda t: t.strftime("%Y-%m-%dT%H:%M:%S")              # noqa: E731
    spec = {"where": {"expression": {"fieldName": "id.stationCode", "operator": "eq", "value": code}},
            "and": {"expression": {"fieldName": "id.datatypeCode", "operator": "eq", "value": "HHS"},
                    "and": {"expression": {"fieldName": "id.dataTime", "operator": "gte", "value": f(t0)},
                            "and": {"expression": {"fieldName": "id.dataTime", "operator": "lte",
                                                   "value": f(t1)}}}}}
    for attempt in range(3):
        try:
            r = requests.get(CWC_API, params={"specification": json.dumps(spec)}, headers=UA, timeout=90)
            r.raise_for_status()
            return {pd.Timestamp(x["id"]["dataTime"]): float(x["dataValue"]) for x in r.json()
                    if x.get("dataValue") is not None}
        except Exception:                                           # noqa: BLE001
            time.sleep(2 + 3 * attempt)
    return {}


def main(ask_cwc: bool = False) -> dict:
    st = json.loads(STATIONS.read_text())
    lv = json.loads(LEVELS.read_text())
    rdates, pct = when_grid.percentile_features()
    r3 = pd.DataFrame(pct["r3"], index=rdates)

    first, final, raws = {}, {}, {}
    for f in sorted(GAUGES.glob("*_hhs.csv")):
        code = f.stem.replace("_hhs", "")
        raw = pd.read_csv(f, parse_dates=["datetime"]).dropna(subset=["level"])
        raws[code] = raw.sort_values("datetime", kind="stable")
        first[code] = (cleaned(raw, False, False).sort_values("datetime", kind="stable")
                       .reset_index(drop=True))
        final[code] = cleaned(raw, True, True)
    # every gauge's readings by hour, to spot a value logged under the wrong station
    hourly = {c: d.assign(h=d["datetime"].dt.floor("h")).groupby("h")["level"].agg(["min", "max"])
              for c, d in raws.items()}

    out, n_all = [], 0
    for code, a in first.items():
        m = st[code]
        n_all += len(a)
        kept_keys = set(zip(final[code]["datetime"], final[code]["level"]))
        gone = np.array([(tt, vv) not in kept_keys for tt, vv in zip(a["datetime"], a["level"])])
        if not gone.any():
            continue
        t, v = a["datetime"].to_numpy(), a["level"].to_numpy(float)
        rest = v[~gone]
        lo_all, hi_all = float(rest.min()), float(rest.max())
        official_high = (lv.get(code) or {}).get("highest")
        thr = m["threshold"]
        day = a["datetime"].dt.normalize()
        d_old = a.groupby(day)["level"].max()
        d_new = a[~gone].groupby(day[~gone])["level"].max()
        cell = int(when_grid.cell_of(np.array([m["lat"]]), np.array([m["lon"]]))[0])
        idx = np.flatnonzero(gone)
        for g in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1):
            i0, i1 = int(g[0]), int(g[-1])
            # nearest KEPT readings on each side
            b = i0 - 1
            while b >= 0 and gone[b]:
                b -= 1
            e = i1 + 1
            while e < len(v) and gone[e]:
                e += 1
            if b < 0 or e >= len(v):
                continue
            before, after = float(v[b]), float(v[e])
            vals = v[i0:i1 + 1]
            val = float(np.median(vals))
            level = (before + after) / 2
            jump = val - level
            lo_nb, hi_nb = min(before, after) - SAME_M, max(before, after) + SAME_M
            still = abs(before - after) <= STILL_M
            oor = bool((vals > hi_all).all() or (vals < lo_all).all()
                       or (official_high is not None and jump > 0 and (vals > official_high).all()))
            slip = bool(all(any(lo_nb <= c <= hi_nb for c in B._undo_slips(float(x))) for x in vals))
            other = None
            for c2, h2 in hourly.items():
                if c2 == code:
                    continue
                hit = 0
                for tt, x in zip(t[i0:i1 + 1], vals):
                    hh = pd.Timestamp(tt).floor("h")
                    w = h2.loc[hh - pd.Timedelta(hours=1):hh + pd.Timedelta(hours=1)]
                    if len(w) and ((w["min"] - SAME_M <= x) & (x <= w["max"] + SAME_M)).any():
                        hit += 1
                if hit == len(vals):
                    other = st[c2]["name"]
                    break
            days = pd.DatetimeIndex(sorted(set(day.iloc[i0:i1 + 1])))
            flipped = [d for d in days if d_old.get(d, -np.inf) >= thr and not d_new.get(d, -np.inf) >= thr]
            rain = None
            if flipped and cell >= 0:
                rr = [float(r3.loc[d, cell]) for d in flipped if d in r3.index]
                rain = round(float(np.nanmax(rr)), 2) if rr else None
            cwc = None
            if ask_cwc:
                now = cwc_now(code, pd.Timestamp(t[i0]) - pd.Timedelta(hours=2),
                              pd.Timestamp(t[i1]) + pd.Timedelta(hours=2))
                got = [now.get(pd.Timestamp(x)) for x in t[i0:i1 + 1]]
                got = [x for x in got if x is not None]
                cwc = ("no answer" if not now else "reading gone" if not got else
                       "corrected" if all(abs(x - level) <= 0.2 * abs(jump) for x in got) else
                       "still there" if all(abs(x - y) < 0.005 for x, y in zip(got, vals)) else "changed")
            n_tests = int(still) + int(oor) + int(slip) + int(other is not None)
            out.append({
                "gauge": m["name"], "code": code, "from": str(pd.Timestamp(t[i0]))[:16],
                "readings": int(len(g)), "before": before, "value": round(val, 2), "after": after,
                "jump_m": round(jump, 2), "still": bool(still), "out_of_range": oor, "slip": slip,
                "other_gauge": other, "tests_passed": n_tests,
                "verdict": "certain" if n_tests >= 2 else "likely" if n_tests == 1 else "judgement",
                "cwc_highest_ever": official_high,
                "false_high_water_days": [str(d.date()) for d in flipped],
                "rain_r3_pct_that_day": rain, "cwc_today": cwc})

    # Pangin against Pasighat, 50 km downstream: what Pasighat reads when Pangin
    # really is at each level, and what it read on the days in question
    pg, ps = first["003NEID-3"], final["005-UBDDIB"]
    dp = pg.groupby(pg["datetime"].dt.normalize())["level"].median()
    dq = ps.groupby(ps["datetime"].dt.normalize())["level"].median()
    j = pd.concat([dp.rename("pangin"), dq.rename("pasighat")], axis=1).dropna()
    band = lambda lo, hi: j[(j.pangin >= lo) & (j.pangin < hi)].pasighat          # noqa: E731
    downstream = {"pasighat_when_pangin_198_202": [round(float(band(198, 202).quantile(q)), 2) for q in (.05, .5, .95)],
                  "pasighat_when_pangin_208_212": [round(float(band(208, 212).quantile(q)), 2) for q in (.05, .5, .95)],
                  "days": {}}
    for d in ("2019-08-04", "2019-08-09"):
        x = ps[ps["datetime"].dt.normalize() == d]["level"]
        downstream["days"][d] = [round(float(x.min()), 2), round(float(x.max()), 2)]

    hw = [e for e in out if e["false_high_water_days"]]
    rank = {"certain": 2, "likely": 1, "judgement": 0}
    hw_days: dict = {}
    for e in hw:
        for d_ in e["false_high_water_days"]:
            k = (e["gauge"], d_)
            if k not in hw_days or rank[e["verdict"]] < rank[hw_days[k]]:
                hw_days[k] = e["verdict"]
    res = {"what": "independent evidence that each run of removed readings is false",
           "readings_checked": n_all, "runs": len(out),
           "readings_removed": int(sum(e["readings"] for e in out)),
           "by_verdict": {k: sum(1 for e in out if e["verdict"] == k)
                          for k in ("certain", "likely", "judgement")},
           # one day can hold several runs (Pangin, 9 Aug 2019: three): count DAYS, and
           # give each day its weakest run's verdict
           "false_high_water_days": len(hw_days),
           "false_high_water_by_verdict": {k: sum(1 for v_ in hw_days.values() if v_ == k)
                                           for k in ("certain", "likely", "judgement")},
           "pangin_vs_pasighat": downstream, "items": out}
    REPORT.write_text(json.dumps(res, indent=2))

    y = lambda b: "yes" if b else " - "                                            # noqa: E731
    print(f"{len(out)} runs, {res['readings_removed']} readings, of {n_all:,} checked")
    print("verdicts:", res["by_verdict"])
    print(f"\nTHE {res['false_high_water_days']} HIGH-WATER DAYS THE CLEANING TAKES AWAY "
          f"(by verdict: {res['false_high_water_by_verdict']})")
    print(f"  {'gauge':<10}{'day':<12}{'before':>9}{'VALUE':>9}{'after':>9}{'jump':>9}  still range slip  other gauge   rain pct  verdict")
    for e in sorted(hw, key=lambda e: (e["gauge"], e["from"])):
        print(f"  {e['gauge']:<10}{e['false_high_water_days'][0]:<12}{e['before']:>9.2f}{e['value']:>9.2f}"
              f"{e['after']:>9.2f}{e['jump_m']:>+9.2f}   {y(e['still'])}  {y(e['out_of_range'])}  {y(e['slip'])}  "
              f"{(e['other_gauge'] or '-'):<12} {str(e['rain_r3_pct_that_day']):>6}    {e['verdict']}")
    d = downstream
    print("\n  Pangin vs Pasighat (same river, 50 km downstream):")
    print(f"    when Pangin is really at 198-202 m, Pasighat reads {d['pasighat_when_pangin_198_202'][1]} "
          f"(90% of days {d['pasighat_when_pangin_198_202'][0]}..{d['pasighat_when_pangin_198_202'][2]})")
    print(f"    when Pangin is really at 208-212 m, Pasighat reads {d['pasighat_when_pangin_208_212'][1]} "
          f"(90% of days {d['pasighat_when_pangin_208_212'][0]}..{d['pasighat_when_pangin_208_212'][2]})")
    for dd, (a_, b_) in d["days"].items():
        print(f"    {dd}: Pasighat read {a_}..{b_}")
    print("\nEVERYTHING THAT IS NOT 'certain':")
    for e in sorted((e for e in out if e["verdict"] != "certain"), key=lambda e: (e["verdict"], e["gauge"], e["from"])):
        print(f"  {e['verdict']:<10}{e['gauge']:<12}{e['from']:<17}{e['readings']:>3}  {e['before']:>8.2f} -> "
              f"{e['value']:>8.2f} -> {e['after']:>8.2f}  ({e['jump_m']:+.2f})   still {y(e['still'])} range "
              f"{y(e['out_of_range'])} slip {y(e['slip'])} other {e['other_gauge'] or '-'}"
              + ("   HIGH-WATER DAY" if e["false_high_water_days"] else ""))
    if ask_cwc:
        print("\nCWC's server today:", {k: sum(1 for e in out if e["cwc_today"] == k)
                                        for k in sorted({str(e["cwc_today"]) for e in out})})
    print(f"\n  wrote {REPORT.relative_to(ROOT)}")
    return res


if __name__ == "__main__":
    main(ask_cwc="--cwc" in sys.argv)
