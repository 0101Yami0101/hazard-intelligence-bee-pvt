"""AD-06: an AI river-mud model — weekly mud anomaly from rain and ground, held out two ways.

    $env:REGION = "assam"; python scripts/model/train_river_mud_ai.py

Written down before training (EROSION_PLAN.md, "AD-06 part 1"):
    rows     AD-02's station-weeks (river_mud_weeks.parquet), weeks with a mud anomaly
    target   the same-week mud anomaly (seasonal percentile, as AD-02)
    inputs   erosive-rain anomaly + log value; erosive rain 1-3 weeks before; rain over the previous
             30 and 60 days; the week's wettest day; week of year (sin, cos); catchment traits
             (log area, mean LS, mean loss, mean C, mean delivered share over the mapped part)
    model    LightGBM regression, 300 trees, 15 leaves, min 50 per leaf, lr 0.03, seed 42
    holdouts by year (leave-one-year-out); by station (leave-one-station-out; the Barak pair together)
    bar      median over stations of Spearman(pred, obs) >= 0.20 under BOTH

Output: reports/river_mud_ai_<region>.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import geopandas as gpd
import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy.stats import spearmanr

import grid as G
from common import AOI_NAME, INTERIM, PROCESSED, ROOT

warnings.filterwarnings("ignore")

PARAMS = dict(objective="regression", n_estimators=300, num_leaves=15, min_child_samples=50,
              learning_rate=0.03, subsample=0.8, subsample_freq=1, colsample_bytree=0.8,
              random_state=42, verbose=-1, n_jobs=-1)
BAR = 0.20
BARAK = {"Annapurna Ghat", "Badarpur Ghat"}


def daily_inputs() -> dict[str, pd.DataFrame]:
    """Per station, daily catchment rain and EI (as AD-02)."""
    from erosion_outlook_base import param_at
    sr = INTERIM / "station_rain"
    pj = json.loads((sr / "points.json").read_text())
    P = np.load(sr / "precip_mm.npy")
    dates = pd.to_datetime(np.load(sr / "dates.npy"))
    a, b = param_at(np.array(pj["lat"]), np.array(pj["lon"]))
    EI = a[None] * np.power(np.maximum(np.nan_to_num(P), 0), b[None])
    return {st: pd.DataFrame({"p": np.nanmean(P[:, idx], axis=1), "ei": EI[:, idx].mean(axis=1)}, index=dates)
            for st, idx in pj["stations"].items()}


def traits() -> pd.DataFrame:
    g = gpd.read_file(ROOT / "data" / "processed" / "sediment_station_catchments.gpkg").to_crs(G.CRS)
    E = INTERIM / "erosion"
    rd = lambda n: rasterio.open(E / f"{n}.tif").read(1)
    LS, A, C, SDR = rd("erosion_LS"), rd("erosion_A_tpha"), rd("erosion_C"), rd("erosion_sdr")
    rows = []
    for _, s in g.iterrows():
        m = rasterize([(s.geometry, 1)], out_shape=G.SHAPE, transform=G.TRANSFORM, fill=0).astype(bool)
        f = lambda a: float(np.nanmean(a[m & np.isfinite(a)])) if (m & np.isfinite(a)).any() else np.nan
        rows.append({"station": s.Station, "log_area": np.log(s.catchment_km2), "LS": f(LS), "A": f(A),
                     "C": f(C), "SDR": f(SDR)})
    return pd.DataFrame(rows)


def features(W: pd.DataFrame) -> pd.DataFrame:
    daily = daily_inputs()
    out = []
    for st, g in W.groupby("station"):
        d = daily[st]
        g = g.copy()
        wk = d.ei.resample("W-SUN").sum()
        wk.index = wk.index - pd.Timedelta(days=6)
        for k in (1, 2, 3):
            g[f"ei_lag{k}"] = np.log1p(g.week.map(wk.shift(k)))
        p30 = d.p.rolling(30).sum().shift(1)
        p60 = d.p.rolling(60).sum().shift(1)
        mx = d.p.resample("W-SUN").max()
        mx.index = mx.index - pd.Timedelta(days=6)
        g["p30"] = np.log1p(g.week.map(p30))
        g["p60"] = np.log1p(g.week.map(p60))
        g["pmax"] = np.log1p(g.week.map(mx))
        out.append(g)
    W = pd.concat(out)
    W["ei_log"] = np.log1p(W.ei)
    ang = 2 * np.pi * W.woy / 53
    W["woy_sin"], W["woy_cos"] = np.sin(ang), np.cos(ang)
    return W.merge(traits(), on="station", how="left")


FEATS = ["ei_pct", "ei_log", "ei_lag1", "ei_lag2", "ei_lag3", "p30", "p60", "pmax", "woy_sin", "woy_cos",
         "log_area", "LS", "A", "C", "SDR"]


def holdout(W: pd.DataFrame, group: pd.Series) -> pd.Series:
    pred = pd.Series(np.nan, index=W.index)
    for gval in group.unique():
        te = group == gval
        m = lgb.LGBMRegressor(**PARAMS).fit(W.loc[~te, FEATS], W.loc[~te, "mud_pct"])
        pred[te] = m.predict(W.loc[te, FEATS])
    return pred


def per_station(W, pred) -> dict:
    return {st: round(float(spearmanr(pred[g.index], g.mud_pct).correlation), 3) for st, g in W.groupby("station")}


def main() -> None:
    print(f"AI river-mud model — {AOI_NAME}")
    W = pd.read_parquet(PROCESSED / "river_mud_weeks.parquet")
    W = W[W.mud_pct.notna()].copy()
    W = features(W).reset_index(drop=True)
    W = W.dropna(subset=["ei_pct", "p60"])
    print(f"  {len(W):,} station-weeks, {W.station.nunique()} stations, {W.week.dt.year.min()}-{W.week.dt.year.max()}")
    by_year = per_station(W, holdout(W, W.week.dt.year))
    st_group = W.station.where(~W.station.isin(BARAK), "Barak pair")
    by_station = per_station(W, holdout(W, st_group))
    base = {st: round(float(spearmanr(g.ei_pct, g.mud_pct).correlation), 3) for st, g in W.groupby("station")}
    full = lgb.LGBMRegressor(**PARAMS).fit(W[FEATS], W.mud_pct)
    imp = dict(sorted(zip(FEATS, full.booster_.feature_importance("gain")), key=lambda x: -x[1]))
    tot = sum(imp.values())
    rep = {"region": AOI_NAME, "rows": int(len(W)), "stations": int(W.station.nunique()),
           "median_rho_by_year": round(float(np.median(list(by_year.values()))), 3),
           "median_rho_by_station": round(float(np.median(list(by_station.values()))), 3),
           "baseline_median_rho_same_rows": round(float(np.median(list(base.values()))), 3),
           "rho_by_year": by_year, "rho_by_station": by_station, "baseline_rho": base,
           "importance_pct": {k: round(100 * v / tot, 1) for k, v in imp.items()}, "bar": BAR}
    rep["pass"] = bool(rep["median_rho_by_year"] >= BAR and rep["median_rho_by_station"] >= BAR)
    (ROOT / "reports" / f"river_mud_ai_{AOI_NAME}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: rep[k] for k in ("rows", "median_rho_by_year", "median_rho_by_station",
                                          "baseline_median_rho_same_rows", "pass")}, indent=1))
    print("  importance:", list(rep["importance_pct"].items())[:8])


if __name__ == "__main__":
    main()
