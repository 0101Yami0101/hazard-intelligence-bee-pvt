"""AD-02: does the outlook's erosive rain show up as river mud? CWC sediment stations, 2010-2026.

    $env:REGION = "assam"; python scripts/inspect/river_mud_check.py

The test and its bars were written down before any rain was fetched
(docs/design/EROSION_PLAN.md, "AD-02 part 1"):

    weeks     Monday-Sunday; erosive rain = summed EI (a*P^b, InRESatE daily model, catchment
              mean over the outlook's 0.2 deg lattice points); plain rain = summed P;
              river mud = mean of the week's readings (>= 2 readings)
    anomaly   each weekly value's percentile among all years' values for the same week of
              the year +-1 week, per station
    M1        Spearman(erosive-rain anomaly, mud anomaly), same week: > 0 at >= 2/3 of
              stations and median >= 0.30
    M2        erosive rain's median rho >= plain rain's
    reported  mud one week later; monsoon weeks only; per-station rho

Also writes the station-week table AD-06 (the AI river-mud model) trains on.
Outputs: reports/river_mud_check_<region>.json, data/processed/<region>/river_mud_weeks.parquet
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import AOI_NAME, GAUGES, INTERIM, PROCESSED, ROOT

warnings.filterwarnings("ignore")

SED = GAUGES / "cwc_sediment"
ASSAM_FILES = ("08cf3a3a-c6e5-4c7a-871d-28861a3f8b88", "b809cd25-a40b-495c-91b3-67137963e542")
VAL = "Manual Daily Suspended Sediments (g/L)"
BARS = {"share_positive": 2 / 3, "median_rho": 0.30}
MIN_READ = 2


def seasonal_pct(df: pd.DataFrame, col: str) -> pd.Series:
    """Each row's percentile among the station's values for the same week of the year +-1."""
    out = pd.Series(np.nan, index=df.index)
    for st, g in df.groupby("station"):
        woy = g.woy.to_numpy()
        v = g[col].to_numpy()
        for w in np.unique(woy):
            near = np.isin(woy, [((w - 2) % 53) + 1, w, (w % 53) + 1])
            pool = v[near & np.isfinite(v)]
            sel = (woy == w) & np.isfinite(v)
            if len(pool) >= 5 and sel.any():
                out.loc[g.index[sel]] = [(pool < x).mean() + 0.5 * (pool == x).mean() for x in v[sel]]
    return out


def main() -> None:
    from erosion_outlook_base import param_at
    print(f"River-mud check of the outlook — {AOI_NAME}")
    sr = INTERIM / "station_rain"
    pj = json.loads((sr / "points.json").read_text())
    P = np.load(sr / "precip_mm.npy")
    dates = pd.to_datetime(np.load(sr / "dates.npy"))
    a, b = param_at(np.array(pj["lat"]), np.array(pj["lon"]))
    EI = a[None] * np.power(np.maximum(np.nan_to_num(P), 0), b[None])

    mud = pd.concat([pd.read_csv(SED / f"{r}.csv", dtype=str) for r in ASSAM_FILES])
    mud["t"] = pd.to_datetime(mud["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce").dt.normalize()
    mud["v"] = pd.to_numeric(mud[VAL], errors="coerce")
    mud = mud.dropna(subset=["t", "v"])
    mud = mud[(mud.v >= 0) & (mud.t >= dates[0]) & (mud.t <= dates[-1])]

    rows = []
    for st, idx in pj["stations"].items():
        d = pd.DataFrame({"t": dates, "ei": EI[:, idx].mean(axis=1), "p": np.nanmean(P[:, idx], axis=1)})
        d["week"] = d.t - pd.to_timedelta(d.t.dt.weekday, unit="D")
        w = d.groupby("week").agg(ei=("ei", "sum"), p=("p", "sum"), days=("t", "count"))
        w = w[w.days == 7]
        m = mud[mud.Station == st].copy()
        m["week"] = m.t - pd.to_timedelta(m.t.dt.weekday, unit="D")
        mw = m.groupby("week").v.agg(["mean", "count"])
        mw = mw[mw["count"] >= MIN_READ]["mean"].rename("mud")
        j = w.join(mw, how="left")
        j["mud_next"] = j.mud.shift(-1)
        j["station"] = st
        rows.append(j.reset_index())
    W = pd.concat(rows, ignore_index=True)
    W["woy"] = W.week.dt.isocalendar().week.astype(int)
    W["month"] = W.week.dt.month
    for c in ("ei", "p", "mud", "mud_next"):
        W[f"{c}_pct"] = seasonal_pct(W, c)

    def per_station(x, y, sel=None):
        out = {}
        for st, g in W.groupby("station"):
            g = g if sel is None else g[sel(g)]
            m = g[x].notna() & g[y].notna()
            if m.sum() >= 30:
                out[st] = (round(float(spearmanr(g.loc[m, x], g.loc[m, y]).correlation), 3), int(m.sum()))
        return out

    m1 = per_station("ei_pct", "mud_pct")
    m2 = per_station("p_pct", "mud_pct")
    nxt = per_station("ei_pct", "mud_next_pct")
    mons = per_station("ei_pct", "mud_pct", lambda g: g.month.between(6, 9))
    r1 = [v[0] for v in m1.values()]
    r2 = [v[0] for v in m2.values()]
    res = {"region": AOI_NAME, "stations": len(m1), "weeks_scored": {k: v[1] for k, v in m1.items()},
           "M1_rho_by_station": {k: v[0] for k, v in m1.items()},
           "M1_share_positive": round(float(np.mean(np.array(r1) > 0)), 3),
           "M1_median_rho": round(float(np.median(r1)), 3),
           "M2_plain_rain_median_rho": round(float(np.median(r2)), 3),
           "M2_rho_by_station": {k: v[0] for k, v in m2.items()},
           "next_week_median_rho": round(float(np.median([v[0] for v in nxt.values()])), 3),
           "monsoon_only_median_rho": round(float(np.median([v[0] for v in mons.values()])), 3),
           "bars": BARS}
    res["M1_pass"] = bool(res["M1_share_positive"] >= BARS["share_positive"] and res["M1_median_rho"] >= BARS["median_rho"])
    res["M2_pass"] = bool(res["M1_median_rho"] >= res["M2_plain_rain_median_rho"])
    PROCESSED.mkdir(parents=True, exist_ok=True)
    W.to_parquet(PROCESSED / "river_mud_weeks.parquet")
    (ROOT / "reports" / f"river_mud_check_{AOI_NAME}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k not in ("weeks_scored", "M2_rho_by_station")}, indent=1))


if __name__ == "__main__":
    main()
