"""Is the CWC flood site's `MPS` datatype rain in mm? Checked against NWDP daily rain.

    python scripts/inspect/ffs_rain_check.py

The test was written down before this script first ran
(docs/design/RAIN_GAUGES.md, "Part C0"):
  - the FFS stations that carry MPS, each matched to the NWDP manual-daily
    station within 5 km (names printed for a hand check);
  - a day's MPS total: the lone 08:30 reading, or the sum of the 8 three-hourly
    readings from 11:30 the day before to 08:30 (the 24 h ending 08:30); days
    with only some of the 8 slots are counted but not matched;
  - MPS day d against NWDP day d-1, d, d+1; the best lag overall is applied to
    every station;
  - compared days: NWDP rain > 0; agree = within max(1 mm, 10 %);
  - bar: >= 80 % agree on >= 50 days at a station; >= 6 of 9 stations.

Writes reports/ffs_rain_check.csv and reports/ffs_rain_check.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import GAUGES, ROOT
from flood_stations import STATIONS
from gauge_vs_rain_sources import gauges

MAX_KM = 5.0
BAR_SHARE, BAR_DAYS, BAR_STATIONS = 0.80, 50, 6
SLOTS = 8


def km(la1, lo1, la2, lo2):
    c = np.cos(np.radians((la1 + la2) / 2))
    return 111.2 * np.hypot(la2 - la1, (lo2 - lo1) * c)


def daily_mps(df: pd.DataFrame) -> pd.DataFrame:
    """Rain day = 24 h ending 08:30. Returns day, mm, n (readings in the day)."""
    t = df.datetime
    # a reading at 08:30 closes its own day; anything after 08:30 belongs to the next day
    after = (t.dt.hour * 60 + t.dt.minute) > 8 * 60 + 30
    day = t.dt.normalize() + pd.to_timedelta(after.astype(int), unit="D")
    g = df.assign(day=day).groupby("day")
    out = pd.DataFrame({"mm": g.value.sum(), "n": g.size(),
                        "only_0830": g.datetime.agg(lambda s: len(s) == 1 and s.iloc[0].strftime("%H:%M") == "08:30")})
    return out


def agree(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a - b).abs() <= np.maximum(1.0, 0.10 * b)


def main() -> None:
    G = gauges()
    nw = G[G.state == "Arunachal Pradesh"]
    nw_where = nw.groupby("Station")[["lat", "lon"]].first()
    now = pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)

    pairs = []
    for code, meta in STATIONS.items():
        f = GAUGES / "cwc" / f"{code}_mps.csv"
        if not f.exists():
            continue
        d = nw_where.assign(km=km(meta["lat"], meta["lon"], nw_where.lat, nw_where.lon)).sort_values("km")
        if not len(d) or d.km.iloc[0] > MAX_KM:
            print(f"  {meta['name']}: no NWDP station within {MAX_KM} km (nearest {d.index[0]} {d.km.iloc[0]:.1f} km)")
            continue
        mps = pd.read_csv(f, parse_dates=["datetime"])
        pairs.append((code, meta["name"], d.index[0], float(d.km.iloc[0]), mps))

    # one lag for all: pick the lag with the highest pooled agreement
    def table(mps, st, lag):
        m = daily_mps(mps)
        full = m[m.only_0830 | (m.n == SLOTS)]
        g = nw[nw.Station == st].set_index("t").p
        g = g[g > 0]
        g.index = g.index + pd.Timedelta(days=lag)      # NWDP day d-lag -> MPS day d
        j = pd.DataFrame({"nwdp": g}).join(full.mm.rename("mps"), how="inner")
        return m, j

    pooled = {}
    for lag in (-1, 0, 1):
        ok = n = 0
        for code, name, st, dkm, mps in pairs:
            _, j = table(mps, st, lag)
            ok += int(agree(j.mps, j.nwdp).sum()); n += len(j)
        pooled[lag] = round(ok / max(n, 1), 3)
    lag = max(pooled, key=pooled.get)

    rows = []
    for code, name, st, dkm, mps in pairs:
        m, j = table(mps, st, lag)
        g = nw[nw.Station == st].set_index("t").p
        both_span = m.index[(m.index >= g.index.min() + pd.Timedelta(days=lag)) & (m.index <= g.index.max() + pd.Timedelta(days=lag))]
        wet_mps = m.loc[both_span]
        wet_mps = wet_mps[(wet_mps.mm > 0) & (wet_mps.only_0830 | (wet_mps.n == SLOTS))]
        listed = set(g[g > 0].index + pd.Timedelta(days=lag))
        last = mps.datetime.max()
        share = float(agree(j.mps, j.nwdp).mean()) if len(j) else np.nan
        rows.append({
            "code": code, "ffs_name": name, "nwdp_station": st, "km": round(dkm, 2),
            "mps_first": str(mps.datetime.min().date()), "mps_last": str(last),
            "delay_h": round((now - last).total_seconds() / 3600, 1),
            "days_partial": int(((m.n > 1) & (m.n < SLOTS)).sum()),
            "compared_days": int(len(j)), "agree_share": round(share, 3),
            "spearman": round(float(spearmanr(j.mps, j.nwdp).correlation), 3) if len(j) > 2 else np.nan,
            "total_ratio_mps_over_nwdp": round(float(j.mps.sum() / j.nwdp.sum()), 3) if len(j) else np.nan,
            "mps_wet_not_in_nwdp": round(float(np.mean([d not in listed for d in wet_mps.index])), 3) if len(wet_mps) else np.nan,
            "passes": bool(len(j) >= BAR_DAYS and share >= BAR_SHARE),
        })
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "reports" / "ffs_rain_check.csv", index=False)
    res = {"lag_days_nwdp_to_mps": lag, "pooled_agree_by_lag": pooled,
           "stations": int(len(df)), "stations_passing": int(df.passes.sum()),
           "verdict": ("MPS is rain in mm" if df.passes.sum() >= BAR_STATIONS else "not confirmed as rain"),
           "run_at_ist": str(now)}
    (ROOT / "reports" / "ffs_rain_check.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
