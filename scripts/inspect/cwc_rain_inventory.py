"""What the CWC rain-gauge files on NWDP really hold: years and true time resolution.

    python scripts/inspect/cwc_rain_inventory.py

Two things the file names cannot be trusted for (checked 2026-10-20):
  - the PERIOD in a name is a template ("1961-1990"), not the data's span;
  - the RESOLUTION: Arunachal's "manual hourly" file has one reading a day at
    08:00 on scattered days, i.e. daily totals under an hourly label.
So per station this measures the real first/last dates, the number of years and
days with readings, and the median number of readings per day with any reading
(about 24 = truly hourly; about 1 = daily). Erosivity needs truly sub-daily data.

Writes reports/cwc_rain_inventory.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))

import pandas as pd

from common import ROOT, WEATHER
from fetch_47_cwc_rainfall import RESOURCES

SRC = WEATHER / "cwc_rain"


def main() -> None:
    rows = []
    for rid, label in RESOURCES.items():
        f = SRC / f"{rid}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f, dtype=str)
        if d.empty:
            continue
        val = [c for c in d.columns if "Rainfall" in c][0]
        d["t"] = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
        d["v"] = pd.to_numeric(d[val], errors="coerce")
        d = d.dropna(subset=["t"])
        state, kind = label.split(",")[0], ",".join(label.split(",")[1:3]).strip()
        for st, g in d.groupby("Station"):
            per_day = g.groupby(g.t.dt.normalize()).size()
            rows.append({
                "state": state, "file_kind": kind, "file_label": label, "station": st,
                "district": g.District.iloc[0], "lat": g.Latitude.iloc[0], "lon": g.Longitude.iloc[0],
                "first": g.t.min().date(), "last": g.t.max().date(),
                "years_with_data": int(g.t.dt.year.nunique()), "days_with_data": int(len(per_day)),
                "readings": int(len(g)), "median_readings_per_day": float(per_day.median()),
                "true_resolution": "hourly" if per_day.median() >= 12 else
                                   ("sub-daily (partial)" if per_day.median() >= 3 else "daily"),
                "max_reading_mm": float(g.v.max()),
            })
    inv = pd.DataFrame(rows).sort_values(["state", "file_kind", "station"])
    dest = ROOT / "reports" / "cwc_rain_inventory.csv"
    inv.to_csv(dest, index=False)

    print("By state and file kind (stations; real span; true resolution):")
    for (state, kind), g in inv.groupby(["state", "file_kind"]):
        res = g.true_resolution.value_counts().to_dict()
        print(f"  {state:18} {kind:22} {len(g):3} stations  {min(g['first'])} .. {max(g['last'])}  "
              f"median years/station {g.years_with_data.median():.0f}  resolution {res}")
    h = inv[inv.true_resolution == "hourly"]
    print("\nTruly hourly stations, by years with data:")
    for state, g in h.groupby("state"):
        top = g.sort_values("days_with_data", ascending=False)
        print(f"  {state}: {g.station.nunique()} stations; "
              f"{(g.years_with_data >= 10).sum()} with >= 10 years, {(g.years_with_data >= 5).sum()} with >= 5")
        for _, r in top.head(12).iterrows():
            print(f"     {r.station:28} {r.file_kind:22} {r['first']} .. {r['last']}  "
                  f"{r.years_with_data:2} yrs  {r.days_with_data:5} days  {r.median_readings_per_day:4.0f}/day")
    print(f"\n  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
