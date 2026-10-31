"""Grade the weekly erosion outlook by replaying May-Sep 2023-2025 (E2.2).

    $env:REGION = "assam"; python scripts/inspect/outlook_replay.py

The test and its bars were written down before any forecast was fetched
(docs/design/EROSION_PLAN.md, "E2.2 part 1"):

    issues    every Monday 1 May - 30 Sep, 2023-2025; day D+k read at lead k
    forecast  the app's own numbers (products.erosion.outlook): the week's EI share of a
              normal year, on Open-Meteo rain against Open-Meteo's own history
    truth     GPM IMERG V07 Final daily via Earth Engine (0.2 deg box mean), EI = a*P^b
              with the same a, b, against IMERG's own 2013-2025 history
    baseline  climatology: each week forecast as its normal share
    G1  median over weeks of Spearman across points (forecast vs observed share)
        >= 0.30 and above climatology's
    G2  Spearman across weeks of the state's forecast vs observed share
        >= 0.60 and above climatology's
    G3  AUC of forecast x-normal for observed >= 2x normal (point-weeks)  >= 0.70

Inputs: data/interim/<region>/outlook_replay/forecast_daily.npz (fetch_51),
        data/raw/06_weather/gpm_imerg_daily/*_<region>_*.nc4 (fetch_11b),
        webapp/assets/erosion/<region>/outlook_base.npz (erosion_outlook_base.py)
Output: reports/outlook_replay_<region>.json,
        data/interim/<region>/outlook_replay/replay_point_weeks.npz (the point-weeks, for AD-28)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import xarray as xr
from scipy.stats import spearmanr

from common import AOI_NAME, INTERIM, ROOT, WEATHER
from compare_nrsc_ld import auc

warnings.filterwarnings("ignore")

YEARS = (2024, 2025)          # leads 1-6 are archived from May 2024 (clarification 3)
BARS = {"G1": 0.30, "G2": 0.60, "G3": 0.70}
HEAVY = 2.0
SMOOTH = 7


def imerg_at_points(lat, lon) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """IMERG V07 Final at the points, from Earth Engine (fetch_54; clarification 4)."""
    z = np.load(INTERIM / "outlook_replay" / "imerg_points.npz")
    assert np.allclose(z["lat"], lat) and np.allclose(z["lon"], lon), "point order differs"
    return pd.DatetimeIndex(z["dates"]), z["rain"]


def imerg_at_points_opendap(lat, lon) -> tuple[pd.DatetimeIndex, np.ndarray]:
    """The original route: fetch_11b's OpeNDAP files (blocked on 2026-10-26)."""
    files = sorted((WEATHER / "gpm_imerg_daily").glob(f"gpm-imerg_precip_0p1_{AOI_NAME}_*.nc4"))
    with xr.open_dataset(files[0]) as ds:
        glon, glat = ds.lon.values, ds.lat.values
    masks = [(np.abs(glat - la) <= 0.1001)[:, None] & (np.abs(glon - lo) <= 0.1001)[None, :]
             for la, lo in zip(lat, lon)]
    out = np.full((len(files), len(lat)), np.nan, np.float32)
    dates = []
    for i, f in enumerate(files):
        dates.append(pd.Timestamp(f.stem[-8:]))
        try:
            with xr.open_dataset(f) as ds:
                a = np.squeeze(ds["precipitation"].values)
            if a.shape == (len(glon), len(glat)):
                a = a.T
            for j, m in enumerate(masks):
                out[i, j] = np.nanmean(a[m])
        except Exception:  # noqa: BLE001
            pass
    return pd.DatetimeIndex(dates), out


def season_of(ei: np.ndarray, dates: pd.DatetimeIndex, ei_year: np.ndarray, full) -> np.ndarray:
    """Mean share of a year's EI in the 7 days from each day of the year (as the builder)."""
    doy = np.minimum(dates.dayofyear.values, 365) - 1
    w7 = pd.DataFrame(ei).rolling(7).sum().shift(-6).to_numpy()
    infull = np.isin(dates.year.values, full)
    season = np.full((365, ei.shape[1]), np.nan)
    for d in range(365):
        m = infull & (doy == d) & np.isfinite(w7).all(axis=1)
        season[d] = np.nanmean(w7[m], axis=0) / ei_year
    pad = np.vstack([season[-SMOOTH:], season, season[:SMOOTH]])
    season = np.array([pad[d:d + 2 * SMOOTH + 1].mean(axis=0) for d in range(365)])
    return np.vstack([season, season[-1:]])


def main() -> None:
    print(f"Outlook replay — {AOI_NAME}")
    fc = np.load(INTERIM / "outlook_replay" / "forecast_daily.npz")
    z = np.load(ROOT / "webapp" / "assets" / "erosion" / AOI_NAME / "outlook_base.npz")
    pidx = fc["point_index"]
    a, b = z["a"][pidx], z["b"][pidx]
    ei_year_om, season_om = z["ei_year"][pidx], z["season"][:, pidx]
    w_state = z["state"][pidx]
    lat, lon = fc["lat"], fc["lon"]
    fdates = pd.DatetimeIndex(fc["dates"])
    lead = fc["lead_rain"]                                  # [day, lead, point]

    idates, P = imerg_at_points(lat, lon)
    ei_obs = a[None] * np.power(np.maximum(np.nan_to_num(P), 0), b[None])
    ei_obs[~np.isfinite(P)] = np.nan
    full = [y for y in range(2013, 2026) if (idates.year == y).sum() >= 365]   # 2013-2025 (clarification 1)
    ei_year_im = np.nanmean([np.nansum(ei_obs[idates.year == y], axis=0) for y in full], axis=0)
    season_im = season_of(np.nan_to_num(ei_obs), idates, ei_year_im, full)
    obs = pd.DataFrame(ei_obs, index=idates)

    rows = []
    for y in YEARS:
        for D in pd.date_range(f"{y}-05-01", f"{y}-09-30", freq="W-MON"):
            days = [D + pd.Timedelta(days=k) for k in range(7)]
            if not all(d in fdates for d in days) or not all(d in obs.index for d in days):
                continue
            pf = np.stack([lead[fdates.get_loc(d), k] for k, d in enumerate(days)])     # [7, point]
            s_fc = (a[None] * np.power(np.maximum(pf, 0), b[None])).sum(axis=0) / ei_year_om
            s_fc[np.isnan(pf).any(axis=0)] = np.nan
            s_ob = obs.loc[days].to_numpy().sum(axis=0) / ei_year_im
            doy = D.dayofyear - 1
            n_om, n_im = season_om[doy], season_im[doy]
            if np.isfinite(s_fc).sum() < 20 or np.isfinite(s_ob).sum() < 20:
                continue
            rows.append({"issue": D, "year": y, "s_fc": s_fc, "s_ob": s_ob, "clim": n_om,
                         "x_fc": s_fc / n_om, "x_ob": s_ob / n_im})
    print(f"  {len(rows)} issue weeks, {len(lat)} points")

    def g1(sel, key):
        r = [spearmanr(w[key][m], w["s_ob"][m]).correlation for w in sel
             for m in [np.isfinite(w[key]) & np.isfinite(w["s_ob"])] if m.sum() >= 20]
        return round(float(np.nanmedian(r)), 3), len(r)

    def state(w, key):
        m = np.isfinite(w[key]) & np.isfinite(w["s_ob"])
        return np.average(w[key][m], weights=w_state[m]), np.average(w["s_ob"][m], weights=w_state[m])

    def g2(sel, key):
        f, o = zip(*(state(w, key) for w in sel))
        return round(float(spearmanr(f, o).correlation), 3)

    def g3(sel):
        x = np.concatenate([w["x_fc"] for w in sel]); y_ = np.concatenate([w["x_ob"] for w in sel])
        m = np.isfinite(x) & np.isfinite(y_)
        pos = y_[m] >= HEAVY
        return (round(auc(x[m], pos), 3) if 0 < pos.sum() < m.sum() else None), int(pos.sum()), int(m.sum())

    def block(sel):
        g1f, n = g1(sel, "s_fc")
        g1c, _ = g1(sel, "clim")
        g3v, npos, nall = g3(sel)
        ratio = np.concatenate([w["s_fc"] / w["s_ob"] for w in sel])
        ratio = ratio[np.isfinite(ratio) & (ratio > 0)]
        return {"weeks": len(sel), "G1_median_rho": g1f, "G1_climatology": g1c, "G1_weeks_scored": n,
                "G2_rho": g2(sel, "s_fc"), "G2_climatology": g2(sel, "clim"),
                "G3_auc": g3v, "G3_heavy_point_weeks": npos, "G3_point_weeks": nall,
                "share_ratio_fc_over_obs_median": round(float(np.median(ratio)), 3)}

    allw = block(rows)
    rep = {"region": AOI_NAME, "points": int(len(lat)), "issues": len(rows), "years": YEARS,
           "all": allw, "by_year": {str(y): block([w for w in rows if w["year"] == y]) for y in YEARS},
           "bars": BARS}
    rep["G1_pass"] = bool(allw["G1_median_rho"] >= BARS["G1"] and allw["G1_median_rho"] > allw["G1_climatology"])
    rep["G2_pass"] = bool(allw["G2_rho"] >= BARS["G2"] and allw["G2_rho"] > allw["G2_climatology"])
    rep["G3_pass"] = bool(allw["G3_auc"] is not None and allw["G3_auc"] >= BARS["G3"])
    # point-weeks for later checks (AD-28 warnings): forecast/observed share and x-normal
    np.savez_compressed(INTERIM / "outlook_replay" / "replay_point_weeks.npz",
                        issue=np.array([str(w["issue"])[:10] for w in rows]),
                        s_fc=np.stack([w["s_fc"] for w in rows]), s_ob=np.stack([w["s_ob"] for w in rows]),
                        x_fc=np.stack([w["x_fc"] for w in rows]), x_ob=np.stack([w["x_ob"] for w in rows]))
    dest = ROOT / "reports" / f"outlook_replay_{AOI_NAME}.json"
    dest.write_text(json.dumps(rep, indent=2))
    print(json.dumps({k: rep[k] for k in ("all", "G1_pass", "G2_pass", "G3_pass")}, indent=1))
    for y, v in rep["by_year"].items():
        print(f"  {y}: G1 {v['G1_median_rho']} (clim {v['G1_climatology']}), G2 {v['G2_rho']} "
              f"(clim {v['G2_climatology']}), G3 {v['G3_auc']}")
    print(f"  wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
