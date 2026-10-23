"""Grade the forecasts' rain (Open-Meteo, as each SlideSense issue kept it)
against the CWC flood site's measured rain, by lead.

    python scripts/fetch/fetch_48_ffs_rain.py     # fresh MPS first
    python scripts/inspect/grade_forecast_rain.py

Rules in docs/design/RAIN_GAUGES.md §7 (Part D):
  - issues: records/landslide_forecast/issues/<day>.npz (all_days, all_rain_mm);
  - gauges: the stations that passed Part C0 and are live (reports/ffs_rain_check.csv),
    each at its nearest Open-Meteo point within 0.15 deg;
  - a gauge day is a UTC day, 05:30 IST -> 05:30 IST: the 8 three-hourly MPS
    slots ending 08:30 .. 05:30 next day, all 8 present;
  - leads -10 .. 6 (negative = Open-Meteo's estimate of days already past).

Writes reports/forecast_rain_grade.csv (every graded pair) and .json (per lead)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import GAUGES, ROOT
from flood_stations import STATIONS

ISSUES = ROOT / "records" / "landslide_forecast" / "issues"
POINTS = ROOT / "webapp" / "assets" / "base" / "points.json"
OM_MAX_DEG = 0.15
WET, CAUGHT, FALSE_FC, FALSE_G = 10.0, 5.0, 10.0, 2.0
READ_AT = 50          # gauge days >= 10 mm per lead before the log is read


def utc_days(code: str) -> pd.Series:
    """MPS by UTC day: the 8 slots ending 08:30 IST that day .. 05:30 IST the next."""
    d = pd.read_csv(GAUGES / "cwc" / f"{code}_mps.csv", parse_dates=["datetime"])
    utc = d.datetime - pd.Timedelta(hours=5, minutes=30) - pd.Timedelta(hours=3)   # slot START, in UTC
    g = d.assign(day=utc.dt.normalize()).groupby("day").value
    n, s = g.size(), g.sum()
    return s[n == 8]


def main() -> None:
    c = pd.read_csv(ROOT / "reports" / "ffs_rain_check.csv")
    c = c[c.passes & (pd.to_datetime(c.mps_last) >= pd.Timestamp("2026-10-01"))]
    pts = json.loads(POINTS.read_text())
    la, lo = np.asarray(pts["lat"]), np.asarray(pts["lon"])
    where = {}
    for code in c.code:
        m = STATIONS[code]
        dist = np.hypot(la - m["lat"], lo - m["lon"])
        k = int(np.argmin(dist))
        if dist[k] <= OM_MAX_DEG:
            where[code] = (m["name"], k, utc_days(code))

    rows = []
    for f in sorted(ISSUES.glob("*.npz")):
        z = np.load(f)
        issued = pd.Timestamp(f.stem)
        days = pd.to_datetime([str(x) for x in z["all_days"]])
        rain = z["all_rain_mm"]
        if rain.shape[1] != len(la):
            raise SystemExit(f"{f.name}: {rain.shape[1]} points, the bundle has {len(la)}")
        for code, (name, k, g) in where.items():
            for i, day in enumerate(days):
                lead = (day - issued).days
                if not -10 <= lead <= 6 or day not in g.index:
                    continue
                rows.append({"issued_on": f.stem, "day": str(day.date()), "lead": lead, "station": name,
                             "forecast_mm": round(float(rain[i, k]), 2), "gauge_mm": round(float(g.loc[day]), 2)})
    df = pd.DataFrame(rows, columns=["issued_on", "day", "lead", "station", "forecast_mm", "gauge_mm"])
    df.to_csv(ROOT / "reports" / "forecast_rain_grade.csv", index=False)

    # 3-day totals within one issue and station, on 3 consecutive graded days;
    # filed under the lead of the window's last day
    t3 = []
    for _, e in df.groupby(["issued_on", "station"]):
        e = e.assign(day=pd.to_datetime(e.day)).set_index("day").sort_index().asfreq("D")
        s = e[["forecast_mm", "gauge_mm"]].rolling(3, min_periods=3).sum().dropna()
        t3.append(s.assign(lead=e["lead"].reindex(s.index)))
    t3 = pd.concat(t3) if t3 else pd.DataFrame(columns=["forecast_mm", "gauge_mm", "lead"])

    per = {}
    for lead, d in df.groupby("lead"):
        wet = d.gauge_mm >= WET
        fc = d.forecast_mm >= FALSE_FC
        w3 = t3[t3.lead == lead]
        per[int(lead)] = {
            "spearman_3day": (round(float(spearmanr(w3.forecast_mm, w3.gauge_mm).correlation), 3)
                              if len(w3) > 5 and w3.gauge_mm.nunique() > 1 and w3.forecast_mm.nunique() > 1 else None),
            "days": int(len(d)), "gauge_days_ge_10mm": int(wet.sum()),
            "total_forecast_over_gauge": round(float(d.forecast_mm.sum() / d.gauge_mm.sum()), 2) if d.gauge_mm.sum() > 0 else None,
            "mean_abs_error_mm": round(float((d.forecast_mm - d.gauge_mm).abs().mean()), 2),
            "caught_share": round(float((d.forecast_mm[wet] >= CAUGHT).mean()), 3) if wet.any() else None,
            "false_alarm_share": round(float((d.gauge_mm[fc] < FALSE_G).mean()), 3) if fc.any() else None,
            "spearman_daily": (round(float(spearmanr(d.forecast_mm, d.gauge_mm).correlation), 3)
                               if len(d) > 5 and d.gauge_mm.nunique() > 1 and d.forecast_mm.nunique() > 1 else None),
            "ready_to_read": bool(wet.sum() >= READ_AT),
        }
    res = {"issues": len(list(ISSUES.glob("*.npz"))), "stations": {v[0]: int(v[1]) for v in where.values()},
           "pairs": int(len(df)), "by_lead": per}
    (ROOT / "reports" / "forecast_rain_grade.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
