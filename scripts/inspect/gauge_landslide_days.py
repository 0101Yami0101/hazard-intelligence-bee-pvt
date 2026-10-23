"""Rain at the nearest ground gauge on dated landslide days, vs IMERG and Open-Meteo.

    python scripts/inspect/gauge_landslide_days.py

The test was written down before this script first ran
(docs/design/RAIN_GAUGES.md, "Part B"): NASA GLC dated landslides in Arunachal;
the nearest CWC gauge within 25 km whose event month is a counted month
(April-October, >= 5 rain days); the trigger's own score = mean of the 3-day
and 7-day rain percentiles against the series' own May-October distribution,
on the event day; for the gauge, IMERG at the gauge's cell and Open-Meteo at
the point nearest the gauge (<= 0.15 deg), on the same events.

Writes reports/gauge_landslide_days.csv and reports/gauge_landslide_days.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd

from common import INTERIM, LABELS, ROOT
from gauge_vs_rain_sources import MIN_DAYS, MONTHS, OM_MAX_DEG, gauges

MAX_KM = 25.0
MONSOON = (5, 10)
HIGH = 0.75


def km(la1, lo1, la2, lo2):
    c = np.cos(np.radians((la1 + la2) / 2))
    return 111.2 * np.hypot(la2 - la1, (lo2 - lo1) * c)


def score_on(series: pd.Series, day: pd.Timestamp) -> float:
    """Mean of 3- and 7-day percentiles on `day`, against May-Oct days of the series."""
    out = []
    for w in (3, 7):
        r = series.rolling(w, min_periods=w).sum()
        ref = r[(r.index.month >= MONSOON[0]) & (r.index.month <= MONSOON[1])].dropna()
        if day not in r.index or pd.isna(r.loc[day]) or len(ref) < 100:
            return np.nan
        out.append(float((ref < r.loc[day]).mean()))
    return float(np.mean(out))


def main() -> None:
    G = gauges()
    ev = gpd.read_file(LABELS / "nasa-glc_landslides_point_arunachal.geojson")
    ev["day"] = pd.to_datetime(ev.ev_date, unit="ms", errors="coerce").dt.normalize()
    ev = ev.dropna(subset=["day"])
    P = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    pdates = pd.to_datetime(np.load(INTERIM / "rainfall" / "dates.npy"))
    meta = json.loads((INTERIM / "rainfall" / "_stack_meta.json").read_text())
    O = np.load(INTERIM / "rainfall_om" / "precip_mm.npy", mmap_mode="r")
    odates = pd.to_datetime(np.load(INTERIM / "rainfall_om" / "dates.npy"))
    pts = json.loads((INTERIM / "rainfall_om" / "points.json").read_text())
    olat, olon = np.asarray(pts["lat"]), np.asarray(pts["lon"])

    # each gauge's daily series on its counted months (unlisted day = 0 there)
    series, where = {}, {}
    for st, g in G.groupby("Station"):
        g = g.assign(y=g.t.dt.year, m=g.t.dt.month)
        cnt = g[g.m.isin(MONTHS)].groupby(["y", "m"]).size()
        counted = set(cnt[cnt >= MIN_DAYS].index)
        if not counted:
            continue
        cal = pd.date_range(g.t.min(), g.t.max(), freq="D")
        keys = list(zip(cal.year, cal.month))
        s = pd.Series([0.0 if k in counted else np.nan for k in keys], index=cal)
        on = g.set_index("t").p
        on = on[on.index.isin(s.index[s.notna()])]
        s.loc[on.index] = on.values
        series[st], where[st] = s, (float(g.lat.iloc[0]), float(g.lon.iloc[0]), counted)

    rows = []
    for _, e in ev.iterrows():
        la, lo, day = float(e.latitude), float(e.longitude), e.day
        cands = sorted(((km(la, lo, w[0], w[1]), st) for st, w in where.items()
                        if (day.year, day.month) in w[2]), key=lambda x: x[0])
        cands = [c for c in cands if c[0] <= MAX_KM]
        if not cands:
            continue
        d_km, st = cands[0]
        gla, glo, _ = where[st]
        row = {"event": e.ev_id, "day": str(day.date()), "gauge": st, "km": round(d_km, 1),
               "score_gauge": score_on(series[st], day)}
        i = int(round((meta["lat_max"] - gla) / 0.1))
        j = int(round((glo - meta["lon_min"]) / 0.1))
        if 0 <= i < P.shape[1] and 0 <= j < P.shape[2]:
            im = pd.Series(np.asarray(P[:, i, j], float), index=pdates)
            row["score_imerg"] = score_on(im, day)
        dist = np.hypot(olat - gla, olon - glo)
        k = int(np.argmin(dist))
        if dist[k] <= OM_MAX_DEG:
            row["score_om"] = score_on(pd.Series(np.asarray(O[:, k], float), index=odates), day)
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "reports" / "gauge_landslide_days.csv", index=False)

    def summ(cols):
        d = df.dropna(subset=cols)
        return {"events": int(len(d)),
                **{c: {"median": round(float(d[c].median()), 3), "share_high": round(float((d[c] >= HIGH).mean()), 3)}
                   for c in cols}}

    res = {"events_with_dates": int(len(ev)), "events_with_a_gauge": int(len(df)),
           "gauge_vs_imerg": summ(["score_gauge", "score_imerg"]),
           "gauge_vs_om": summ(["score_gauge", "score_om"]),
           "all_three": summ(["score_gauge", "score_imerg", "score_om"])}
    (ROOT / "reports" / "gauge_landslide_days.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
