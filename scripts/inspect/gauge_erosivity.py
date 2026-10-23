"""Rain strength (R) at the CWC rain gauges, against the InRESatE and IRED maps.

    python scripts/inspect/gauge_erosivity.py

The test was written down before this script first ran (EROSION_PLAN.md,
"V-01 part 1"):
  - daily erosivity EI = a * P^b on every recorded rain day, with a and b from
    InRESatE's published daily model for the gauge's 0.1-degree square (no
    threshold: that variant reproduces the published map on our own IMERG);
  - CWC manual-daily gauges, years 2001-2018 only (the map's years);
  - a station-year counts if every month April-September has >= 5 rain days;
  - a station counts with >= 8 such years; R = mean of their yearly sums;
  - compared with InRESatE R and IRED R at the gauge: map / gauge per station,
    the median ratio and Spearman rho across stations, per state and together.
Decision rule: InRESatE stays unless the gauges agree with IRED better by >= 0.2
in rho AND InRESatE's own rho < 0.4. Station coordinates outside 21.5-30.5 N,
88-98 E are dropped and listed (NWDP has had stations placed in the wrong state).

Writes reports/gauge_erosivity_stations.csv and reports/gauge_erosivity_check.json
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
import scipy.io as sio
from scipy.stats import spearmanr

from common import ROOT, WEATHER
from fetch_47_cwc_rainfall import RESOURCES

ER = WEATHER / "erosivity"
INR = ER / "inresate"
IRED_TIF = ER / "ired" / "Indian Rainfall Erosivity Dataset (IRED)" / "Dataset" / "tif" / "R-Factor_India.tif"
Y0, Y1 = 2001, 2018
MIN_DAYS_PER_MONTH, MONTHS = 5, range(4, 10)
MIN_YEARS = 8
BOX = (88.0, 21.5, 98.0, 30.5)


def mat(p: Path) -> np.ndarray:
    d = sio.loadmat(p)
    return np.asarray(d[[k for k in d if not k.startswith("__")][0]], float)


def grid(folder: Path, name: str):
    a, lat, lon = mat(folder / f"{name}.mat"), np.ravel(mat(folder / "lat.mat")), np.ravel(mat(folder / "lon.mat"))
    if a.shape == (len(lon), len(lat)):
        a = a.T
    return a, lat, lon


def at(a, lat, lon, la, lo):
    i, j = int(np.argmin(abs(lat - la))), int(np.argmin(abs(lon - lo)))
    return float(a[i, j]) if abs(lat[i] - la) <= 0.051 and abs(lon[j] - lo) <= 0.051 else np.nan


def main() -> None:
    frames = []
    for rid, label in RESOURCES.items():
        if "manual daily" not in label:
            continue
        d = pd.read_csv(WEATHER / "cwc_rain" / f"{rid}.csv", dtype=str)
        col = [c for c in d.columns if "Rainfall" in c][0]
        d["t"] = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce").dt.normalize()
        d["p"] = pd.to_numeric(d[col], errors="coerce")
        d["state"] = label.split(",")[0]
        frames.append(d[["state", "Station", "t", "p", "Latitude", "Longitude"]])
    d = pd.concat(frames).dropna(subset=["t", "p"])
    d = d[d.p >= 0].drop_duplicates(["state", "Station", "t"])
    d = d[(d.t.dt.year >= Y0) & (d.t.dt.year <= Y1)]
    d["lat"], d["lon"] = pd.to_numeric(d.Latitude, errors="coerce"), pd.to_numeric(d.Longitude, errors="coerce")

    pdir = INR / "Daily Rainfall Erosivity Model Parameters"
    A, plat, plon = grid(pdir, "a_ei")
    B, _, _ = grid(pdir, "b_ei")
    R, rlat, rlon = grid(INR / "R-factor", "R")
    ired = rasterio.open(IRED_TIF)
    ired_a = ired.read(1).astype(float)

    rows, dropped = [], []
    for (state, st), g in d.groupby(["state", "Station"]):
        la, lo = float(g.lat.iloc[0]), float(g.lon.iloc[0])
        if not (BOX[1] <= la <= BOX[3] and BOX[0] <= lo <= BOX[2]):
            dropped.append({"state": state, "station": st, "lat": la, "lon": lo})
            continue
        a, b = at(A, plat, plon, la, lo), at(B, plat, plon, la, lo)
        g = g.assign(y=g.t.dt.year, m=g.t.dt.month, ei=a * np.power(g.p.values, b))
        months = g.groupby(["y", "m"]).size().unstack(fill_value=0).reindex(columns=list(MONTHS), fill_value=0)
        good = months[(months >= MIN_DAYS_PER_MONTH).all(axis=1)].index
        yearly = g[g.y.isin(good)].groupby("y").agg(ei=("ei", "sum"), rain=("p", "sum"))
        r_ired = np.nan
        try:
            ri, rj = ired.index(lo, la)
            r_ired = float(ired_a[ri, rj]) if ired_a[ri, rj] > 0 else np.nan
        except Exception:  # noqa: BLE001
            pass
        rows.append({"state": state, "station": st, "lat": la, "lon": lo, "a": a, "b": b,
                     "qualifying_years": int(len(good)),
                     "rain_mm_per_year": round(float(yearly.rain.mean()), 0) if len(good) else np.nan,
                     "R_gauge": round(float(yearly.ei.mean()), 0) if len(good) else np.nan,
                     "R_inresate": round(at(R, rlat, rlon, la, lo), 0), "R_ired": round(r_ired, 0)})
    st = pd.DataFrame(rows)
    st["counts"] = st.qualifying_years >= MIN_YEARS
    st["inresate_over_gauge"] = (st.R_inresate / st.R_gauge).round(2)
    st["ired_over_gauge"] = (st.R_ired / st.R_gauge).round(2)
    st.sort_values(["state", "qualifying_years"], ascending=[True, False]).to_csv(
        ROOT / "reports" / "gauge_erosivity_stations.csv", index=False)

    def summary(s: pd.DataFrame) -> dict:
        s = s[s.counts & s.R_gauge.notna() & s.R_inresate.notna() & s.R_ired.notna()]
        if len(s) < 3:
            return {"stations": int(len(s))}
        return {"stations": int(len(s)),
                "median_inresate_over_gauge": round(float(s.inresate_over_gauge.median()), 2),
                "median_ired_over_gauge": round(float(s.ired_over_gauge.median()), 2),
                "rho_inresate": round(float(spearmanr(s.R_gauge, s.R_inresate).correlation), 2),
                "rho_ired": round(float(spearmanr(s.R_gauge, s.R_ired).correlation), 2)}

    res = {"rule": {"years": [Y0, Y1], "min_days_each_month_apr_sep": MIN_DAYS_PER_MONTH,
                    "min_years": MIN_YEARS, "formula": "EI = a * P^b on every rain day (InRESatE daily model)"},
           "stations_seen": int(len(st)), "dropped_bad_coordinates": dropped,
           "Assam": summary(st[st.state == "Assam"]),
           "Arunachal Pradesh": summary(st[st.state == "Arunachal Pradesh"]),
           "both": summary(st)}
    b = res["both"]
    if "rho_inresate" in b:
        res["decision"] = ("switch to IRED" if (b["rho_ired"] - b["rho_inresate"] >= 0.2 and b["rho_inresate"] < 0.4)
                           else "InRESatE stays")
        res["inresate_level_flag"] = not (0.5 <= b["median_inresate_over_gauge"] <= 2.0)
    (ROOT / "reports" / "gauge_erosivity_check.json").write_text(json.dumps(res, indent=2))
    print(json.dumps({k: v for k, v in res.items() if k != "dropped_bad_coordinates"}, indent=1))
    print(f"  dropped for coordinates: {[x['station'] for x in dropped]}")
    show = st[st.counts].sort_values("R_gauge", ascending=False)
    print(show[["state", "station", "qualifying_years", "rain_mm_per_year", "R_gauge", "R_inresate", "R_ired",
                "inresate_over_gauge", "ired_over_gauge"]].to_string(index=False))


if __name__ == "__main__":
    main()
