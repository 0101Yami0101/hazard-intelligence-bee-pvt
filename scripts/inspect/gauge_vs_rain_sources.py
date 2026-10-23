"""Ground rain gauges vs the platform's two rain sources (IMERG, Open-Meteo).

    python scripts/inspect/gauge_vs_rain_sources.py

The test was written down before this script first ran
(docs/design/RAIN_GAUGES.md, "Part A"):
  - CWC manual-daily gauges inside the IMERG archive's box;
  - counted months: April-October with >= 5 recorded rain days; inside them an
    unlisted day is dry, outside them nothing is compared;
  - IMERG = the 0.1 deg cell holding the gauge; Open-Meteo = the nearest of the
    219 forecast points within 0.15 deg;
  - metrics per station: total ratio, daily Spearman, heavy-day detection
    (gauge >= 50 mm -> source >= 20 mm), and "unusual" agreement: Spearman of
    3- and 7-day totals, and the share of the gauge's top-10% days that are in
    the source's top 10%;
  - each source on its own overlap, and head-to-head on 2010-01-01 .. 2026-07-29.

Writes reports/gauge_vs_rain_sources.csv and reports/gauge_vs_rain_sources.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))

import numpy as np
import pandas as pd
import rasterio
from scipy.stats import spearmanr

from common import INTERIM, ROOT, TERRAIN, WEATHER
from fetch_47_cwc_rainfall import RESOURCES

MONTHS, MIN_DAYS = range(4, 11), 5
HEAVY_G, HEAVY_S = 50.0, 20.0
H2H = (pd.Timestamp("2010-01-01"), pd.Timestamp("2026-07-29"))
OM_MAX_DEG = 0.15


def gauges() -> pd.DataFrame:
    frames = []
    for rid, label in RESOURCES.items():
        if "manual daily" not in label:
            continue
        d = pd.read_csv(WEATHER / "cwc_rain" / f"{rid}.csv", dtype=str)
        col = [c for c in d.columns if "Rainfall" in c][0]
        d["t"] = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce").dt.normalize()
        d["p"] = pd.to_numeric(d[col], errors="coerce")
        d["lat"], d["lon"] = pd.to_numeric(d.Latitude, errors="coerce"), pd.to_numeric(d.Longitude, errors="coerce")
        d["state"] = label.split(",")[0]
        frames.append(d[["state", "Station", "t", "p", "lat", "lon"]])
    d = pd.concat(frames).dropna(subset=["t", "p"])
    return d[d.p >= 0].drop_duplicates(["Station", "t"])


def height(lat: float, lon: float) -> float:
    f = TERRAIN / "copernicus_dem_30m" / f"Copernicus_DSM_COG_10_N{int(np.floor(lat)):02d}_00_E{int(np.floor(lon)):03d}_00_DEM.tif"
    if not f.exists():
        return np.nan
    with rasterio.open(f) as s:
        return float(next(s.sample([(lon, lat)]))[0])


def metrics(g: pd.Series, s: pd.Series) -> dict:
    """g, s: daily series on the same calendar; NaN = not compared."""
    ok = g.notna() & s.notna()
    if ok.sum() < 200:
        return {}
    gd, sd = g[ok], s[ok]
    out = {"days": int(ok.sum()), "ratio": round(float(sd.sum() / gd.sum()), 2) if gd.sum() > 0 else np.nan,
           "rho_daily": round(float(spearmanr(gd, sd).correlation), 3)}
    heavy = gd >= HEAVY_G
    out["heavy_days"] = int(heavy.sum())
    out["heavy_detect"] = round(float((sd[heavy] >= HEAVY_S).mean()), 3) if heavy.sum() >= 5 else np.nan
    gm, sm = g.where(ok), s.where(ok)
    for w in (3, 7):
        a = gm.rolling(w, min_periods=w).sum()
        b = sm.rolling(w, min_periods=w).sum()
        k = a.notna() & b.notna()
        if k.sum() < 100:
            continue
        out[f"rho_{w}d"] = round(float(spearmanr(a[k], b[k]).correlation), 3)
        top_g = a[k] >= a[k].quantile(0.9)
        top_s = b[k] >= b[k].quantile(0.9)
        out[f"top10_hit_{w}d"] = round(float((top_g & top_s).sum() / max(top_g.sum(), 1)), 3)
    return out


def main() -> None:
    G = gauges()
    P = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    pdates = pd.to_datetime(np.load(INTERIM / "rainfall" / "dates.npy"))
    meta = json.loads((INTERIM / "rainfall" / "_stack_meta.json").read_text())
    lat_max, lon_min = meta["lat_max"], meta["lon_min"]
    nlat, nlon = P.shape[1], P.shape[2]
    O = np.load(INTERIM / "rainfall_om" / "precip_mm.npy", mmap_mode="r")
    odates = pd.to_datetime(np.load(INTERIM / "rainfall_om" / "dates.npy"))
    pts = json.loads((INTERIM / "rainfall_om" / "points.json").read_text())
    olat, olon = np.asarray(pts["lat"]), np.asarray(pts["lon"])

    rows = []
    for st, g in G.groupby("Station"):
        la, lo = float(g.lat.iloc[0]), float(g.lon.iloc[0])
        i, j = int(round((lat_max - la) / 0.1)), int(round((lo - lon_min) / 0.1))
        if not (0 <= i < nlat and 0 <= j < nlon):
            continue
        g = g.assign(y=g.t.dt.year, m=g.t.dt.month)
        cnt = g[g.m.isin(MONTHS)].groupby(["y", "m"]).size()
        counted = cnt[cnt >= MIN_DAYS].index
        if len(counted) == 0:
            continue
        cal = pd.date_range(g.t.min(), g.t.max(), freq="D")
        ym = pd.MultiIndex.from_arrays([cal.year, cal.month])
        gs = pd.Series(np.where(ym.isin(counted), 0.0, np.nan), index=cal)
        on = g.set_index("t").p
        on = on[on.index.isin(gs.index[gs.notna()])]
        gs.loc[on.index] = on.values
        imerg = pd.Series(np.asarray(P[:, i, j], dtype=float), index=pdates).reindex(cal)
        dist = np.hypot(olat - la, olon - lo)
        k = int(np.argmin(dist))
        om = (pd.Series(np.asarray(O[:, k], dtype=float), index=odates).reindex(cal)
              if dist[k] <= OM_MAX_DEG else pd.Series(np.nan, index=cal))
        h2h = (cal >= H2H[0]) & (cal <= H2H[1])
        row = {"station": st, "state": g.state.iloc[0], "lat": la, "lon": lo, "height_m": round(height(la, lo)),
               "counted_months": int(len(counted)), "first": str(g.t.min().date()), "last": str(g.t.max().date()),
               "om_point_dist_deg": round(float(dist[k]), 3)}
        for name, s, mask in (("imerg", imerg, None), ("om", om, None),
                              ("h2h_imerg", imerg, h2h), ("h2h_om", om, h2h)):
            gg = gs if mask is None else gs.where(mask)
            if name.startswith("h2h"):        # head-to-head: only days BOTH sources have
                both = imerg.notna() & om.notna()
                gg = gg.where(both)
            for kk, v in metrics(gg, s).items():
                row[f"{name}_{kk}"] = v
        rows.append(row)
    df = pd.DataFrame(rows).sort_values("counted_months", ascending=False)
    df.to_csv(ROOT / "reports" / "gauge_vs_rain_sources.csv", index=False)

    def med(col, d=df):
        return round(float(d[col].median()), 3) if col in d and d[col].notna().any() else None

    h = df.dropna(subset=["h2h_imerg_rho_3d", "h2h_om_rho_3d"])
    summ = {"stations": int(len(df)), "stations_head_to_head": int(len(h)),
            "imerg_own_overlap": {m: med(f"imerg_{m}") for m in ("ratio", "rho_daily", "heavy_detect", "rho_3d", "rho_7d", "top10_hit_3d", "top10_hit_7d")},
            "om_own_overlap": {m: med(f"om_{m}") for m in ("ratio", "rho_daily", "heavy_detect", "rho_3d", "rho_7d", "top10_hit_3d", "top10_hit_7d")},
            "head_to_head": {src: {m: med(f"h2h_{src}_{m}", h) for m in ("ratio", "rho_daily", "heavy_detect", "rho_3d", "rho_7d", "top10_hit_3d", "top10_hit_7d")}
                             for src in ("imerg", "om")},
            "head_to_head_wins_rho_3d": {"imerg": int((h.h2h_imerg_rho_3d > h.h2h_om_rho_3d).sum()),
                                         "om": int((h.h2h_om_rho_3d > h.h2h_imerg_rho_3d).sum())},
            "imerg_ratio_vs_height_rho": (round(float(spearmanr(df.height_m, df.imerg_ratio, nan_policy="omit").correlation), 2)
                                          if "imerg_ratio" in df else None)}
    gap = summ["head_to_head"]["imerg"]["rho_3d"] - summ["head_to_head"]["om"]["rho_3d"]
    summ["reading"] = ("Open-Meteo >= 0.10 below IMERG on 3-day 'unusual' agreement: finding for SlideSense"
                       if gap >= 0.10 else "within 0.10: no change indicated")
    summ["gap_rho_3d_imerg_minus_om"] = round(float(gap), 3)
    jang = df[df.station.str.contains("JANG", case=False)]
    summ["jang"] = jang.drop(columns=[c for c in jang.columns if c.startswith("h2h")]).to_dict("records")
    (ROOT / "reports" / "gauge_vs_rain_sources.json").write_text(json.dumps(summ, indent=2, default=str))
    print(json.dumps({k: v for k, v in summ.items() if k != "jang"}, indent=1))
    show = ["station", "state", "height_m", "counted_months", "imerg_ratio", "imerg_rho_3d", "om_ratio", "om_rho_3d",
            "h2h_imerg_rho_3d", "h2h_om_rho_3d", "imerg_heavy_detect", "om_heavy_detect"]
    print(df[[c for c in show if c in df]].to_string(index=False))


if __name__ == "__main__":
    main()
