"""AD-06 attempt 2: daily river-mud anomaly from rain AND the river's own height.

    $env:REGION = "assam"; python scripts/model/train_river_mud_ai_v2.py

Written down before training (EROSION_PLAN.md, "AD-06 attempt 2 part 1"):
    stations  >= 95% in India, < 60,000 km2 (as attempt 1), with a CWC height record: 12
    rows      station-days 2013-2025 with a mud reading and all inputs
    target    the day's mud as a seasonal percentile (station, same month +-1)
    inputs    known by the ~08:00 IST sample: IMERG catchment rain (day before; last 3/7/30 days;
              wettest of last 7; erosive rain last 3/7), river height (yesterday's anomaly vs the
              station's month: (level - median) / IQR; change over 1 and 3 days; max of last 7),
              day of year (sin, cos), attempt 1's catchment traits
    model     attempt 1's LightGBM settings
    holdouts  by year; by station, nested sites together
    baselines B1 yesterday's height anomaly alone; B2 last 3 days' erosive rain alone
    bar       median station rho >= 0.30 AND >= B1 + 0.05, under BOTH holdouts
    reported  nowcast variant (+ same-day height), per-station rho, importance, monsoon-only rho

Output: reports/river_mud_ai_v2_<region>.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from shapely.geometry import Point

from common import AOI_NAME, GAUGES, INTERIM, ROOT
from train_river_mud_ai import PARAMS, traits

warnings.filterwarnings("ignore")

SED = GAUGES / "cwc_sediment"
ASSAM_FILES = ("08cf3a3a-c6e5-4c7a-871d-28861a3f8b88", "b809cd25-a40b-495c-91b3-67137963e542")
VAL = "Manual Daily Suspended Sediments (g/L)"
HEIGHTS = GAUGES / "cwc_assam"
MIN_INDIA, MAX_KM2 = 95.0, 60000
START, END = "2013-01-01", "2025-12-31"
BAR, MARGIN = 0.30, 0.05
GROUPS = {"Annapurna Ghat": "Barak", "Badarpur Ghat": "Barak", "TULARGRAM": "Barak",
          "Matijuri": "Katakhal", "Lala": "Katakhal"}
MATIJURI = ("01-11-01-002", "015-MBDGHY")       # newer code first, older fills gaps
FEATS = ["p1", "p3", "p7", "p30", "pmax7", "ei3", "ei7", "h_anom1", "h_d1", "h_d3", "h_max7",
         "doy_sin", "doy_cos", "log_area", "LS", "A", "C", "SDR"]


def stations() -> gpd.GeoDataFrame:
    g = gpd.read_file(ROOT / "data" / "processed" / "sediment_station_catchments.gpkg").to_crs(4326)
    geo = json.loads((INTERIM / "cwc_assam_stations.json").read_text())
    codes = {}
    for code, (name, _, _) in geo.items():
        if (HEIGHTS / f"{code}_hhs.csv").exists():
            codes.setdefault(name, []).append(code)
    codes["Matijuri"] = [c for c in MATIJURI if c in codes.get("Matijuri", [])]
    g = g[(g.in_india_pct >= MIN_INDIA) & (g.catchment_km2 < MAX_KM2) & g.Station.isin(codes)].copy()
    g["codes"] = g.Station.map(codes)
    return g.reset_index(drop=True)


def daily_height(codes: list[str]) -> pd.Series:
    s = None
    for c in codes:
        d = pd.read_csv(HEIGHTS / f"{c}_hhs.csv", parse_dates=["datetime"]).dropna(subset=["level"])
        x = d.groupby(pd.to_datetime(d["datetime"]).dt.tz_localize(None).dt.normalize())["level"].median()
        s = x if s is None else s.combine_first(x)
    return s


def height_feats(h: pd.Series, days: pd.DatetimeIndex) -> pd.DataFrame:
    h = h.reindex(days)
    mo = h.index.month
    med = h.groupby(mo).transform("median")
    iqr = h.groupby(mo).transform(lambda v: v.quantile(0.75) - v.quantile(0.25)).replace(0, np.nan)
    anom = (h - med) / iqr
    f = pd.DataFrame(index=days)
    f["h_anom1"] = anom.shift(1)
    f["h_d1"] = ((h.shift(1) - h.shift(2)) / iqr)
    f["h_d3"] = ((h.shift(1) - h.shift(4)) / iqr)
    f["h_max7"] = anom.shift(1).rolling(7, min_periods=4).max()
    f["h_anom0"] = anom                    # the nowcast variant only
    return f


def rain_feats(g: gpd.GeoDataFrame) -> dict[str, pd.DataFrame]:
    from erosion_outlook_base import param_at
    z = np.load(INTERIM / "outlook_replay" / "imerg_points.npz")
    days = pd.to_datetime(z["dates"])
    P = np.maximum(np.nan_to_num(z["rain"]), 0)
    a, b = param_at(z["lat"], z["lon"])
    EI = a[None] * np.power(P, b[None])
    pts = gpd.GeoSeries([Point(x, y) for x, y in zip(z["lon"], z["lat"])], crs=4326)
    out = {}
    for _, s in g.iterrows():
        idx = np.flatnonzero(pts.within(s.geometry).to_numpy())
        if not len(idx):
            idx = [int(pts.distance(s.geometry.centroid).idxmin())]
        p = pd.Series(P[:, idx].mean(axis=1), index=days)
        e = pd.Series(EI[:, idx].mean(axis=1), index=days)
        f = pd.DataFrame(index=days)
        f["p1"] = np.log1p(p.shift(1))
        for k in (3, 7, 30):
            f[f"p{k}"] = np.log1p(p.rolling(k).sum().shift(1))
        f["pmax7"] = np.log1p(p.rolling(7).max().shift(1))
        f["ei3"] = np.log1p(e.rolling(3).sum().shift(1))
        f["ei7"] = np.log1p(e.rolling(7).sum().shift(1))
        out[s.Station] = f
    return out


def mud() -> pd.DataFrame:
    m = pd.concat([pd.read_csv(SED / f"{r}.csv", dtype=str) for r in ASSAM_FILES])
    m["t"] = pd.to_datetime(m["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce").dt.normalize()
    m["v"] = pd.to_numeric(m[VAL], errors="coerce")
    m = m.dropna(subset=["t", "v"])
    return m[m.v >= 0].groupby(["Station", "t"]).v.mean()


def seasonal_pct(df: pd.DataFrame, col: str) -> pd.Series:
    out = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby("station"):
        mo, v = g.t.dt.month.to_numpy(), g[col].to_numpy()
        for m_ in range(1, 13):
            pool = np.sort(v[np.isin(mo, [(m_ - 2) % 12 + 1, m_, m_ % 12 + 1])])
            sel = mo == m_
            if len(pool) >= 5 and sel.any():
                lo, hi = np.searchsorted(pool, v[sel], "left"), np.searchsorted(pool, v[sel], "right")
                out.loc[g.index[sel]] = (lo + 0.5 * (hi - lo)) / len(pool)
    return out


def table() -> pd.DataFrame:
    g = stations()
    days = pd.date_range(START, END, freq="D")
    rain, M, T = rain_feats(g), mud(), traits()
    rows = []
    for _, s in g.iterrows():
        f = rain[s.Station].reindex(days).join(height_feats(daily_height(s.codes), days))
        f["mud"] = M.get(s.Station, pd.Series(dtype=float)).reindex(days)
        f["station"], f["t"] = s.Station, days
        rows.append(f[f.mud.notna()])
    W = pd.concat(rows, ignore_index=True)
    W["target"] = seasonal_pct(W, "mud")
    doy = 2 * np.pi * W.t.dt.dayofyear / 366
    W["doy_sin"], W["doy_cos"] = np.sin(doy), np.cos(doy)
    W = W.merge(T, on="station", how="left")
    return W.dropna(subset=FEATS + ["target"]).reset_index(drop=True)


def holdout(W, group, feats) -> pd.Series:
    pred = pd.Series(np.nan, index=W.index)
    for gv in group.unique():
        te = group == gv
        m = lgb.LGBMRegressor(**PARAMS).fit(W.loc[~te, feats], W.loc[~te, "target"])
        pred[te] = m.predict(W.loc[te, feats])
    return pred


def med_rho(W, x, sel=None) -> tuple[float, dict]:
    r = {}
    for st, g in W.groupby("station"):
        g = g if sel is None else g[sel(g)]
        if len(g) >= 30:
            r[st] = round(float(spearmanr(g[x] if isinstance(x, str) else x[g.index], g.target).correlation), 3)
    return round(float(np.median(list(r.values()))), 3), r


def main() -> None:
    print(f"AI river-mud model, attempt 2 (daily, rain + river height) — {AOI_NAME}")
    W = table()
    print(f"  {len(W):,} station-days, {W.station.nunique()} stations, {W.t.dt.year.min()}-{W.t.dt.year.max()}")
    by_year, by_st = W.t.dt.year, W.station.map(lambda s: GROUPS.get(s, s))
    res = {"region": AOI_NAME, "rows": int(len(W)), "stations": sorted(W.station.unique()),
           "rows_per_station": W.groupby("station").size().to_dict(), "bar": BAR, "margin": MARGIN}
    b1, b1s = med_rho(W, "h_anom1")
    b2, _ = med_rho(W, "ei3")
    res["B1_height_alone"], res["B1_by_station"], res["B2_erosive_rain_alone"] = b1, b1s, b2
    for name, feats in (("main", FEATS), ("nowcast", FEATS + ["h_anom0"])):
        py, ps = holdout(W, by_year, feats), holdout(W, by_st, feats)
        (ry, rys), (rs, rss) = med_rho(W, py), med_rho(W, ps)
        res[name] = {"median_rho_by_year": ry, "median_rho_by_station": rs, "rho_by_year": rys, "rho_by_station": rss,
                     "monsoon_median_rho_by_year": med_rho(W, py, lambda g: g.t.dt.month.between(6, 9))[0]}
    m = res["main"]
    m["pass"] = bool(min(m["median_rho_by_year"], m["median_rho_by_station"]) >= max(BAR, b1 + MARGIN))
    full = lgb.LGBMRegressor(**PARAMS).fit(W[FEATS], W.target)
    imp = dict(sorted(zip(FEATS, full.booster_.feature_importance("gain")), key=lambda x: -x[1]))
    res["importance_pct"] = {k: round(100 * v / sum(imp.values()), 1) for k, v in imp.items()}
    (ROOT / "reports" / f"river_mud_ai_v2_{AOI_NAME}.json").write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({"B1": b1, "B2": b2, "main_by_year": m["median_rho_by_year"], "main_by_station": m["median_rho_by_station"],
                      "monsoon_by_year": m["monsoon_median_rho_by_year"], "pass": m["pass"],
                      "nowcast_by_year": res["nowcast"]["median_rho_by_year"],
                      "nowcast_by_station": res["nowcast"]["median_rho_by_station"]}, indent=1))
    print("  per station (by year):", m["rho_by_year"])
    print("  B1 per station:", b1s)
    print("  importance:", list(res["importance_pct"].items())[:8])


if __name__ == "__main__":
    main()
