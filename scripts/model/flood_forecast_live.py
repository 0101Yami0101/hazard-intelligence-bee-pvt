"""The flood forecast on LIVE rain: today and the week ahead.

    python scripts/model/flood_forecast_live.py build   # once: scales + source check
    python scripts/model/flood_forecast_live.py         # every day: the outlook,
                                                        # river chances, log + checks
    python scripts/model/flood_forecast_live.py --no-log   # on-demand refresh, no log

Reads   models/flood_forecast/*            (day model, exposure, valley factors)
        data/processed/flood_where_prob_100m.tif
        data/interim/rainfall_om/*         (Open-Meteo archive, the shared rain points, 2010-)
Writes  models/flood_forecast/live/        (live scales + live "normal")
        reports/flood_forecast_live_check.json      (build)
        reports/flood_forecast_live_<date>.json     (daily run: area + rivers)
        records/flood_forecast/*                    (track record, forecast_log.py)
        data/processed/flood_forecast_live_<date>.tif

════════════════════════════════════════════════════════════════════════════
ONE RAIN SOURCE END TO END
════════════════════════════════════════════════════════════════════════════
Everything was trained on IMERG satellite rain, which lags ~a day and has no
forecast. The live feed is Open-Meteo — the same service and the same rain
points the landslide side already uses (webapp/core/rainfall.py; 219 points,
~22 km apart, since 2026-09-22 — 97 at ~33 km before), so both hazards share
one fetch. Open-Meteo runs 1.68x wetter than IMERG and agrees
with it only loosely day to day (r = 0.32), so its numbers are NEVER compared
against IMERG history. Every input the models see is "how unusual is this
rain, for here", and "for here" is measured against Open-Meteo's own archive
at that point:

    local rain       3/7-day totals at the nearest rain point
    upstream rain    those point values averaged over each area's catchment
                     (same catchment weights as build_upstream_rain.py)
    soil wetness     flat areas only: ERA5-Land top-metre soil water 16 days
                     before the day, fetched from Earth Engine each run — the
                     SAME source the model was trained on, so no rescaling
                     (SOIL_WETNESS_TEST.md). If it cannot be fetched, flat
                     areas use rain only and the issue says so.

Each scored against its own 2010-2026 monsoon distribution. "Times normal" is
likewise divided by the live path's own ordinary level, not IMERG's.

`build` also measures the cost of the live feed rather than assuming it:
three day models fitted identically (tree TREE_FROM-2020, calibration 2021-22 —
the shipped design; tree 2015-20 until 2026-09-29) and graded inside
Arunachal on 2023 - Oct 2025 (where the flood record ends). The
satellite-fitted model fed live-scaled rain ranks
flood days as well as on satellite rain; a model refitted on the live
archive does worse. So the daily run uses the PRODUCTION day model
unchanged, with live rain on the live source's own scale.

Limits: the rain points sit ~22 km apart and all inside Arunachal, so local
rain is coarser than IMERG's 11 km, and catchment rain from Tibet/Bhutan is
filled from the nearest in-state point. Beyond ~3 days the forecast rain
itself is weak in mountains; the later outlook days are indicative.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT_ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_ / "scripts"), str(ROOT_ / "scripts" / "build"),
                str(ROOT_ / "scripts" / "model"), str(ROOT_ / "webapp")]

import numpy as np
import pandas as pd
import rasterio
from sklearn.metrics import roc_auc_score

import flood_gauge_live
import forecast_log
import grid as G
import near_here
import when_grid
from gauge_records import NO_LEVEL_LINE
from common import INTERIM, PROCESSED, ROOT
from core.rainfall import fetch_rain, forecast_days, rolling_totals
from flood_forecast import (CELL_KM2, MODELS, SOIL_LAG, TREE_FROM, TRUTH_END, FlatSoilDayModel,
                            day_features, fit_day_model, imerg_index_full, label_matrix, load_events,
                            predict_day, soil_input, soil_top_metre, training_events)

OM = INTERIM / "rainfall_om"
LIVE = MODELS / "live"
WHEN_MODELS = ROOT / "models" / "flood_when"
QS = np.linspace(0, 1, 101)
SOIL_TIMEOUT_S = 180


def _pct(vals: np.ndarray, breaks: np.ndarray) -> np.ndarray:
    """Share of that cell's monsoon history below each value (1% steps)."""
    out = np.full(vals.shape, np.nan, dtype=np.float32)
    for j in range(vals.shape[1]):
        b = breaks[:, j]
        if not np.isfinite(b).all():
            continue
        v = vals[:, j]
        ok = np.isfinite(v)
        out[ok, j] = np.searchsorted(b, v[ok], side="left") / (len(b) - 1)
    return np.clip(out, 0.0, 1.0)


def _monsoon_breaks(tot: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    m = np.asarray((dates.month >= 5) & (dates.month <= 10))
    return np.nanquantile(tot[m], QS, axis=0).astype(np.float32)


def _points():
    p = json.loads((OM / "points.json").read_text())
    return np.asarray(p["lat"]), np.asarray(p["lon"])


def rain_source() -> str:
    """The label on every issue. Counted, not typed: the point grid changed
    once already (97 -> 219, 2026-09-22) and a typed label went stale."""
    return f"Open-Meteo (live), {len(_points()[0])} points"


def _nearest(plat, plon) -> np.ndarray:
    clat, clon = when_grid.cell_centres()
    c = np.cos(np.radians(27.9))
    d2 = (clat[:, None] - plat[None, :]) ** 2 + ((clon[:, None] - plon[None, :]) * c) ** 2
    return d2.argmin(axis=1)


def _upstream_matrix() -> np.ndarray:
    W = np.load(INTERIM / "flood_forecast" / "upstream_weights.npz")["W"]
    s = W.sum(1, keepdims=True)
    return np.where(s > 0, W / np.maximum(s, 1.0), np.nan).astype(np.float32)


def fetch_soil(d0: str, d1: str) -> tuple[pd.DatetimeIndex, np.ndarray] | None:
    """ERA5-Land top-metre soil water on the lattice, days d0..d1, from Earth
    Engine (fetch_39_era5land_soil.lattice_days) — or None if it cannot be
    had in time. Never stops the forecast."""
    from concurrent.futures import ThreadPoolExecutor
    sys.path.insert(0, str(ROOT_ / "scripts" / "fetch"))
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        from fetch_39_era5land_soil import lattice_days
        sd, L = pool.submit(lattice_days, d0, d1).result(timeout=SOIL_TIMEOUT_S)
    except Exception as e:                                          # noqa: BLE001
        print(f"  [warn] soil wetness unavailable ({type(e).__name__}: {str(e)[:120]})")
        return None
    finally:
        pool.shutdown(wait=False)
    return sd, soil_top_metre(L["swv1"], L["swv2"], L["swv3"])


def live_soil(days) -> tuple[np.ndarray | None, dict]:
    """The soil input for each of the run's days (soil on day t-16), and a
    note of what was used, for the issue and the web page."""
    d = pd.to_datetime([str(x) for x in days])
    want = d - pd.Timedelta(days=SOIL_LAG)
    got = fetch_soil(str(want.min().date()), str(want.max().date()))
    if got is None or len(got[0]) == 0:
        return None, {"used": False, "lag_days": SOIL_LAG,
                      "note": "soil wetness could not be fetched - flat areas use rain only"}
    sd, raw = got
    try:
        S = soil_input(d, sd, raw)
    except Exception as e:                                          # noqa: BLE001
        print(f"  [warn] soil wetness not scored ({type(e).__name__}: {str(e)[:120]})")
        return None, {"used": False, "lag_days": SOIL_LAG,
                      "note": "soil wetness could not be scored - flat areas use rain only"}
    return S, {"used": True, "lag_days": SOIL_LAG, "soil_data_to": str(sd.max().date())}


def _when_panel():
    with open(WHEN_MODELS / "B_pooled_nwdp_all.pkl", "rb") as fh:
        b = pickle.load(fh)
    with open(WHEN_MODELS / "C_bigriver_naive_DIAGNOSTIC_ONLY_005-UBDDIB.pkl", "rb") as fh:
        c = pickle.load(fh)
    return b, c


def rain_pct(rain_cell: np.ndarray, S: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Local r3 / r7 percentiles and yesterday's mean of the two, per cell."""
    tot = rolling_totals(rain_cell)
    r3p, r7p = _pct(tot["r3"], S["r3"]), _pct(tot["r7"], S["r7"])
    rule = (r3p + r7p) / 2
    lag = np.vstack([np.full((1, rule.shape[1]), np.nan, np.float32), rule[:-1]])
    return r3p, r7p, lag


def features(rain_cell: np.ndarray, S: dict, Wn: np.ndarray, panel) -> list[np.ndarray]:
    """Daily rain per rain cell -> the day model's three rain inputs, each
    scored against the live source's own history."""
    r3p, r7p, lag = rain_pct(rain_cell, S)
    rule = (r3p + r7p) / 2
    X = pd.DataFrame({"r3": r3p.ravel(), "r7": r7p.ravel(), "trigger_lag1": lag.ravel()})
    ok = X[["r3", "r7"]].notna().all(axis=1).to_numpy()
    when = np.full(len(X), np.nan, dtype=np.float32)
    b, c = panel
    when[ok] = (rule.ravel()[ok] + b.predict_proba(X[ok])[:, 1]
                + c.predict_proba(X[ok])[:, 1]) / 3
    up = np.nan_to_num(rain_cell) @ np.nan_to_num(Wn).T
    up[:, ~np.isfinite(Wn).all(axis=1)] = np.nan
    utot = rolling_totals(up)
    return [when.reshape(rule.shape), _pct(utot["r3"], S["up_r3"]), _pct(utot["r7"], S["up_r7"])]


# ── build: live scales, live normal, and the source check ────────────────
def build() -> None:
    print("Live flood forecast — building the Open-Meteo scales")
    LIVE.mkdir(parents=True, exist_ok=True)
    om = np.load(OM / "precip_mm.npy").astype(np.float32)
    od = pd.to_datetime(np.load(OM / "dates.npy", allow_pickle=True))
    plat, plon = _points()
    nn = _nearest(plat, plon)
    Wn = _upstream_matrix()
    rain_cell = om[:, nn]
    tot = rolling_totals(rain_cell)
    up = rain_cell @ np.nan_to_num(Wn).T
    utot = rolling_totals(up)
    S = {"r3": _monsoon_breaks(tot["r3"], od), "r7": _monsoon_breaks(tot["r7"], od),
         "up_r3": _monsoon_breaks(utot["r3"], od), "up_r7": _monsoon_breaks(utot["r7"], od)}
    for k in ("up_r3", "up_r7"):
        S[k][:, ~np.isfinite(Wn).all(axis=1)] = np.nan
    np.savez_compressed(LIVE / "scales.npz", nn=nn, **S)
    print(f"  {len(plat)} points -> {len(nn)} rain cells; archive {od.min().date()} .. {od.max().date()}")

    E = np.load(MODELS / "exposure_km2.npy")
    panel = _when_panel()
    F_om = features(rain_cell, S, Wn, panel)
    ev = training_events()          # the same record the production day model uses
    wd, Wim = when_grid.load()
    F_im = day_features(np.asarray(Wim), upstream=True)
    Y_om = label_matrix(ev, od, len(nn))
    Y_im = label_matrix(ev, wd, len(nn))
    yrs_om = lambda a, b: np.asarray((od.year >= a) & (od.year <= b))
    yrs_im = lambda a, b: np.asarray((wd.year >= a) & (wd.year <= b))

    # ---- the source check -------------------------------------------------
    # Three day models, all fitted the same way (tree TREE_FROM-20, calibration
    # 2021-22) and graded on 2023 .. TRUTH_END, which none of them saw:
    #   satellite          IMERG in, IMERG out — what the replay measured
    #   satellite-on-live  the satellite-fitted model fed live-service rain
    #   live               a model fitted on the live service's own archive
    print(f"  fitting day models for the source check ({TREE_FROM}-20 / 2021-22)...", flush=True)
    # each with soil wetness on flat cells, exactly as production (fit_day_model)
    S_im, S_om = soil_input(wd), soil_input(od)
    m_im, _ = fit_day_model(F_im, E, Y_im, yrs_im(TREE_FROM, 2020), yrs_im(2021, 2022), wd)
    m_om, _ = fit_day_model(F_om, E, Y_om, yrs_om(TREE_FROM, 2020), yrs_om(2021, 2022), od)
    P_im = m_im.predict(F_im, E, S_im)
    P_x = m_im.predict(F_om, E, S_om)
    P_om = m_om.predict(F_om, E, S_om)
    normal = {"sat": np.nanmean(P_im[yrs_im(2015, 2022)], axis=0),
              "x": np.nanmean(P_x[yrs_om(2015, 2022)], axis=0),
              "live": np.nanmean(P_om[yrs_om(2015, 2022)], axis=0)}
    days = wd[(wd >= pd.Timestamp("2023-01-01")) & (wd <= TRUTH_END) & wd.isin(od)]
    i_im = pd.Series(np.arange(len(wd)), index=wd)[days].to_numpy()
    i_om = pd.Series(np.arange(len(od)), index=od)[days].to_numpy()
    Y = Y_im[i_im]
    kidx = imerg_index_full()
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        inst = m.read(1).astype(bool)
    v = kidx >= 0
    frac_in = np.bincount(kidx[v & inst], minlength=len(nn)) / np.maximum(np.bincount(kidx[v], minlength=len(nn)), 1)
    cells = (frac_in > 0.5) & np.isfinite(E)

    def score(P, normal):
        r = (P / normal[None, :])[:, cells]
        y = Y[:, cells]
        ok = np.isfinite(r)
        at = np.argwhere(y == 1)
        rf = r[at[:, 0], at[:, 1]]
        out = {"fair_timing_auc": float(roc_auc_score(y[ok], r[ok])),
               "median_times_normal_on_flood_days": float(np.nanmedian(rf)),
               "warning_levels": []}
        for t in (2, 5, 10):
            out["warning_levels"].append({
                "times_normal": t, "floods_caught_pct": float(100 * np.nanmean(rf >= t)),
                "time_under_warning_pct": float(100 * np.nanmean(r[ok] >= t))})
        return out

    res = {"satellite": score(P_im[i_im], normal["sat"]),
           "satellite-fitted, live rain": score(P_x[i_om], normal["x"]),
           "live-fitted, live rain": score(P_om[i_om], normal["live"])}
    names = list(res)
    print(f"\n  Source check — inside Arunachal, {len(days):,} days 2023..{TRUTH_END.date()}, "
          f"{int(Y[:, cells].sum())} floods, all unseen by every model")
    print(f"     {'':<28}" + "".join(f"{n:>28}" for n in names))
    print(f"     {'fair timing score':<28}" + "".join(f"{res[n]['fair_timing_auc']:>28.3f}" for n in names))
    print(f"     {'typical flood day, x normal':<28}"
          + "".join(f"{res[n]['median_times_normal_on_flood_days']:>28.1f}" for n in names))
    for j, t in enumerate((2, 5, 10)):
        print(f"     {'warn at %dx: caught / time' % t:<28}" + "".join(
            f"{res[n]['warning_levels'][j]['floods_caught_pct']:>19.0f}% / "
            f"{res[n]['warning_levels'][j]['time_under_warning_pct']:>4.1f}%" for n in names))
    (ROOT / "reports" / "flood_forecast_live_check.json").write_text(json.dumps({
        "what": (f"three day models fitted the same way (tree {TREE_FROM}-20, calibration 2021-22), "
                 f"graded inside Arunachal on 2023-01-01..{TRUTH_END.date()}: satellite rain "
                 "throughout; the "
                 "satellite-fitted model fed live-service rain; and a model fitted on the "
                 "live service's own archive"),
        "n_days": int(len(days)), "n_floods": int(Y[:, cells].sum()), "results": res,
    }, indent=2))
    print(f"\n  wrote {ROOT / 'reports' / 'flood_forecast_live_check.json'}")

    # ---- what ships ----------------------------------------------------------
    # The satellite-fitted model fed live-scaled rain ranked flood days exactly
    # as well as on satellite rain (0.725 both, §0q); refitting on the live
    # archive made it worse (0.670) — that archive is weather-model rain, a
    # weaker teacher than observed satellite rain. So the daily run uses the
    # PRODUCTION day model unchanged; only its "ordinary day" level is
    # recomputed here, on live-scaled rain, so "times normal" divides like by
    # like.
    with open(MODELS / "day_model.pkl", "rb") as fh:
        prod = pickle.load(fh)
    np.save(LIVE / "normal_daily_prob.npy",
            np.nanmean(predict_day(prod, F_om, E, S_om), axis=0))
    print("  production day model's live 'ordinary day' level saved")


# ── the daily run ─────────────────────────────────────────────────────────
def run(log: bool = True) -> None:
    """The daily forecast. `log=False` (--no-log) is an on-demand refresh,
    e.g. from the web screen's button: it updates the reports and the web
    snapshot but leaves the track record alone, so the logged issue stays
    the scheduled morning one, written down before the day."""
    plat, plon = _points()
    got = fetch_rain(list(plat), list(plon))
    if got is None:
        raise SystemExit("Live rain unavailable (Open-Meteo did not answer) — try again shortly.")
    days, rain = got
    S = dict(np.load(LIVE / "scales.npz"))
    nn = S.pop("nn")
    F = features(rain[:, nn], S, _upstream_matrix(), _when_panel())
    with open(MODELS / "day_model.pkl", "rb") as fh:
        model = pickle.load(fh)
    E = np.load(MODELS / "exposure_km2.npy")
    normal = np.load(LIVE / "normal_daily_prob.npy")
    reach = np.load(MODELS / "valley_factor.npy")[np.load(MODELS / "terrain_class.npy")]
    # soil wetness only for a model that has the soil half (since 2026-09-28)
    soil, soil_info = live_soil(days) if isinstance(model, FlatSoilDayModel) else (None, None)
    P = predict_day(model, F, E, soil)

    with rasterio.open(PROCESSED / "flood_where_prob_100m.tif") as s:
        where = s.read(1)
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        inst = m.read(1).astype(bool)
    kidx = imerg_index_full()
    sel = inst & np.isfinite(where) & (kidx >= 0)
    wk, ww = kidx[sel], where[sel].astype(np.float64)
    normal_km2 = float((ww * (normal * reach)[wk]).sum() * CELL_KM2)
    lat, lon = when_grid.cell_centres()

    idx = forecast_days(days)
    outlook = []
    times_by_day = []
    for n_, i in enumerate(idx):
        p = P[i]
        per_cell = np.bincount(wk, weights=ww * (p * reach)[wk], minlength=len(p)) * CELL_KM2
        km2 = float(np.nansum(per_cell))
        times = p / normal
        times_by_day.append(times)
        top = np.argsort(-np.nan_to_num(per_cell))[:5]
        outlook.append({
            "date": str(days[i]), "is_today": n_ == 0,
            "expected_flooded_km2": round(km2, 3),
            "times_an_ordinary_day": round(km2 / max(normal_km2, 1e-9), 1),
            "areas_most_ground_at_risk": [
                {"lat": round(float(lat[k]), 2), "lon": round(float(lon[k]), 2),
                 "expected_flooded_km2": round(float(per_cell[k]), 4),
                 "times_normal": round(float(times[k]), 1)} for k in top]})
        if n_ == 0:
            comb = np.full(G.SHAPE, np.nan, dtype=np.float32)
            comb[sel] = (ww * (p * reach)[wk]).astype(np.float32)
            out_tif = PROCESSED / f"flood_forecast_live_{days[i]}.tif"
            with rasterio.open(out_tif, "w", driver="GTiff", height=G.NROWS, width=G.NCOLS,
                               count=1, dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
                               nodata=np.nan, compress="deflate") as d:
                d.write(comb, 1)

    today = outlook[0]["date"]
    if soil is not None:
        soil_info["outlook_days_with_soil"] = int(np.isfinite(soil[idx]).any(axis=1).sum())
        soil_info["outlook_days"] = len(idx)
    # rivers with a gauge: a real calibrated chance, fed the live reading
    r3p, r7p, lag = rain_pct(rain[:, nn], S)
    rivers = flood_gauge_live.forecast([str(d) for d in days], idx, r3p, r7p, lag)
    # Flood chance NEAR HERE: within 10 km, each day and for the week, plus
    # anywhere in Arunachal — from the same day-model chances, nothing above
    # changes. APPROXIMATE (FLOOD_SCREEN_PLAN.md Phase 2: its level was not
    # stable between years); computed only once its curves exist.
    # the last 30 days of each gauge's readings, for the web graph only
    try:
        hist, hist_part = flood_gauge_live.history(30)
    except Exception as e:                                          # noqa: BLE001
        print(f"  [warn] gauge history for the graph skipped: {type(e).__name__}: {e}")
        hist, hist_part = {}, {}
    cur = near_here.load_curves()
    near = None
    if cur is not None:
        try:
            near = near_here.apply(P[idx], cur)
        except Exception as e:                                      # noqa: BLE001
            # never let the new layer stop the forecast it sits on
            print(f"  [warn] near-here chances skipped: {type(e).__name__}: {e}")
    report = {
        "issued_for": today, "rain_source": rain_source(),
        "means": ("expected flooded ground in Arunachal from reported-scale floods, and "
                  "how that compares with an ordinary day. Lead with 'times normal'; the "
                  "absolute km2 runs high in Arunachal (see PARKED_HIMALAYAN_FLOOD_WHERE.md §0p)"),
        "outlook": outlook,
        "soil_wetness": soil_info,
        "rivers_means": ("per gauged river: the calibrated chance the river reaches its "
                         "threshold that day (official CWC danger level where one exists, "
                         "else its own top 2% of days), from live rain plus the river's latest "
                         "reading; see reports/flood_when_gauge.json"),
        "rivers": rivers}
    if near is not None:
        report["near_here"] = near_report(near, cur, [str(days[i]) for i in idx], lat, lon)
    js = ROOT / "reports" / f"flood_forecast_live_{today}.json"
    js.write_text(json.dumps(report, indent=2))
    print(f"Flood outlook for Arunachal, issued {today} (live rain)\n")
    print(f"  {'day':<12}{'x ordinary day':>16}{'  most at risk (lat, lon, x normal)'}")
    for o in outlook:
        a = o["areas_most_ground_at_risk"][0]
        print(f"  {o['date']:<12}{o['times_an_ordinary_day']:>15.1f}x"
              f"   {a['lat']:.2f}, {a['lon']:.2f}  {a['times_normal']:.1f}x")
    todays = sorted((r for r in rivers if r["target_date"] == today),
                    key=lambda r: -r["probability"])
    print(f"\n  Rivers today — chance of reaching the threshold ({len(todays)} gauges)")
    for r in todays[:8]:
        now = "  ABOVE NOW" if r["above_threshold_now"] else ""
        print(f"    {r['station_name'][:22]:<23}{100*r['probability']:>6.1f}%  {r['band']:<9}"
              f"{'official' if r['official'] else 'own top-2%':<11}{r['basis']}{now}")
    if near is not None:
        nr = report["near_here"]
        print(f"\n  Flood chance near here (approximate), {nr['days'][0]} .. {nr['days'][-1]}: "
              f"anywhere in Arunachal {100*nr['arunachal_week']:.1f}%")
        for p_ in nr["places_highest_week"][:5]:
            print(f"    {p_['lat']:.2f}, {p_['lon']:.2f}   {100*p_['week']:5.2f}% this week   "
                  f"{p_['floods_on_record']} floods on record nearby")
    print(f"\n  wrote {js}")
    if log:
        n = forecast_log.log_gauge(rivers)
        forecast_log.log_area(today, outlook)
        print(f"  logged {n} river forecasts + {len(outlook)} area outlook days")
        if near is not None:
            forecast_log.log_near_here(today, [str(days[i]) for i in idx], near)
            print("  logged the near-here chances for every place")
        # SlideSense's forecast for the same days, from the same rain: written
        # down here because the app keeps nothing (landslide_forecast_log.py).
        # Never allowed to stop the flood forecast.
        try:
            import landslide_forecast_log
            ls = landslide_forecast_log.log(days, rain)
            print(f"  logged the landslide forecast ({ls['days'][0]} .. {ls['days'][-1]}, "
                  f"{ls['districts']} districts)")
        except Exception as e:                                      # noqa: BLE001
            print(f"  [warn] landslide forecast not logged: {type(e).__name__}: {e}")
        # new flood records: gauge crossings and people's reports, each
        # checked by satellite (flood_intake.py) — before grading, so today's
        # grade sees them. Never allowed to stop the forecast.
        try:
            import flood_intake
            flood_intake.gather()
            flood_intake.check()
        except Exception as e:                                      # noqa: BLE001
            print(f"  [warn] flood intake skipped: {type(e).__name__}: {e}")
        card = forecast_log.verify()
    else:
        print("  on-demand refresh: track record left unchanged")
        card = (json.loads(forecast_log.SCORECARD.read_text())
                if forecast_log.SCORECARD.exists() else None)
    export_web(today, outlook, np.array(times_by_day), E, rivers, card, near, cur, hist,
               soil_info, hist_part,
               soil_now=None if soil is None else soil[idx[0]],
               flat=model.flat if isinstance(model, FlatSoilDayModel) else None)


def near_report(near: dict, cur: dict, days: list[str], lat: np.ndarray, lon: np.ndarray) -> dict:
    """The near-here part of the daily report: statewide chances and the ten
    Arunachal places with the highest chance this week."""
    wk = near["week"]
    top = [int(k) for k in np.argsort(-np.nan_to_num(wk)) if cur["ap"][k]][:10]
    return {
        "means": ("chance of at least one recorded flood within 10 km of a place (the centre "
                  "of its ~10 km rain cell), each day and over the whole outlook; plus "
                  "anywhere in Arunachal"),
        "status": cur["meta"]["status"],
        "measured_error": cur["meta"].get("measured_error"),
        "days": days,
        "arunachal_week": round(float(near["state_week"]), 4),
        "arunachal_daily": [round(float(v), 4) for v in near["state_day"]],
        "places_highest_week": [
            {"lat": round(float(lat[k]), 2), "lon": round(float(lon[k]), 2),
             "week": round(float(wk[k]), 4),
             "daily": [round(float(near["day"][d, k]), 5) for d in range(len(days))],
             "floods_on_record": int(cur["evidence_days"][k])} for k in top],
    }


WEB_SNAPSHOT = ROOT / "webapp" / "assets" / "flood" / "live_forecast.json"


def method_facts() -> dict:
    """The tested figures the web app's "How to read this forecast" page
    quotes — read from the test reports here, so the page never types a
    number. A missing report just leaves its part out."""
    rep, out = ROOT / "reports", {}
    try:
        # what the day model learns from — the method page says it, so a
        # reader never has to guess the years (they moved 2015 -> 2003 on
        # 2026-09-29, docs/design/OLDER_FLOODS_TEST.md)
        dm = json.loads((MODELS / "_meta.json").read_text())
        out["day_model"] = {"tree_years": dm["tree_years"],
                            "calibration_days": dm["calibration_days"].split(" ")[0]}
    except (OSError, KeyError, ValueError):
        pass
    try:
        g = json.loads((rep / "flood_when_gauge.json").read_text())["leads"]["1"]
        off = g["official danger level"]
        w = {x["at_pct"]: x for x in off["rain + gauge"]["warnings"]}[25]
        wr = {x["at_pct"]: x for x in off["rain only"]["warnings"]}[25]
        out["gauge"] = {"lead_days": 1, "warn_at_pct": 25,
                        "caught_pct": w["floods_caught_pct"], "right_pct": w["warnings_right_pct"],
                        "rain_only_caught_pct": wr["floods_caught_pct"],
                        "reliability": g["reliability, rain + gauge"]}
    except (OSError, KeyError, ValueError):
        pass
    try:
        # the level line: what its test measured (FLOOD_WHEN_PILOT_PLAN.md §14)
        k = json.loads((rep / "gauge_week_check.json").read_text())["level"]
        lj = json.loads((ROOT / "models" / "flood_when_gauge" / "level.json").read_text())
        out["level"] = {"draw_to_lead": lj["draw_to_lead"],
                        "leads": {L: {"cwc_miss_m": k[L]["all days"]["cwc_avg_miss_metres"],
                                      "cwc_no_change_m": k[L]["all days"]["cwc_avg_miss_no_change_metres"],
                                      "range_holds_pct": k[L]["all days"]["range_holds_pct"]}
                                  for L in map(str, range(1, lj["draw_to_lead"] + 1))}}
    except (OSError, KeyError, ValueError):
        pass
    try:
        c = json.loads((rep / "flood_forecast_live_check.json").read_text())
        out["timing"] = {"auc": c["results"]["satellite-fitted, live rain"]["fair_timing_auc"],
                         "n_floods": c["n_floods"], "n_days": c["n_days"]}
    except (OSError, KeyError, ValueError):
        pass
    try:
        n = json.loads((rep / "flood_near_here_check.json").read_text())
        out["near_here_gate_passed"] = n["GATE_A_PASS"]
    except (OSError, KeyError, ValueError):
        pass
    try:
        b = json.loads((rep / "flood_where_topend_check.json").read_text())
        out["where_topend_gate_passed"] = b["GATE_B_PASS"]
    except (OSError, KeyError, ValueError):
        pass
    try:
        sw = json.loads((rep / "soil_wetness_test.json").read_text())
        st = sw["stale"]
        out["soil"] = {"passed": st["verdict"]["pass"], "lag_days": st["soil_lag_days"],
                       "test_years": "2015-2018",
                       "flat_gain": st["areas"]["flat"]["gain"]["flat +soil"]["gain"],
                       "arunachal_gain": st["areas"]["arunachal"]["gain"]["flat +soil"]["gain"],
                       "landslides_helped": any(v["pass"] for part in ("slide", "arc")
                                                for v in sw[part]["verdict"].values())}
    except (OSError, KeyError, ValueError):
        pass
    try:
        vr = json.loads((rep / "flood_verified_record.json").read_text())
        out["record"] = {"events": vr["events"], "by_route": vr["by_route"],
                         "reports_verified": vr["of_the_reported_training_record"]["verified"],
                         "reports": vr["of_the_reported_training_record"]["records"]}
    except (OSError, KeyError, ValueError):
        pass
    try:
        v = json.loads((rep / "flood_radar_test_validation.json").read_text())
        r = json.loads((rep / "flood_radar_recheck.json").read_text())
        rec = r["old_screen_positive_records"]
        out["radar"] = {"test_passed": v["PASS"],
                        "flood_free_dates_correct": v["half_B"]["specificity"],
                        "records": int(sum(rec.values())),
                        "confirmed": int(rec.get("radar supports", 0)),
                        "not_shown": int(rec.get("radar does not show it", 0)),
                        "no_pass": int(rec.get("no radar pass within 3 days", 0))}
    except (OSError, KeyError, ValueError):
        pass
    return out


def _sig(a) -> list[float]:
    """Three significant figures: these are small numbers, and fixed decimals
    would round most of the state to zero."""
    return [float(f"{v:.3g}") for v in np.nan_to_num(np.asarray(a, np.float64), nan=0.0)]


def previous_issue(today: str, cells: np.ndarray) -> dict | None:
    """The latest earlier issue's headline numbers, for the web screen's
    "what changed" card: the statewide and river chances from that day's
    report, and every place's week chance from the near-here log when that
    issue was logged. Display only — nothing forecast reads it."""
    earlier = sorted(p for p in (ROOT / "reports").glob("flood_forecast_live_????-??-??.json")
                     if p.stem[-10:] < today)
    if not earlier:
        return None
    day = earlier[-1].stem[-10:]
    try:
        rep = json.loads(earlier[-1].read_text())
    except (OSError, ValueError):
        return None
    riv = {}
    for r in rep.get("rivers", []):
        g = riv.setdefault(r["station_code"], {"p": 0.0,
                                               "above_now": bool(r.get("above_threshold_now")),
                                               "offline": bool(r.get("gauge_offline"))})
        g["p"] = max(g["p"], float(r["probability"]))
    out = {"issued_on": day, "arunachal_week": (rep.get("near_here") or {}).get("arunachal_week"),
           "rivers": riv}
    f = forecast_log.NEAR_DIR / f"{day}.npz"
    if f.exists() and len(cells):
        wk = np.load(f)["week"]
        if wk.shape[0] > int(cells.max()):
            out["week"] = _sig(wk[cells])
    return out


def export_web(today: str, outlook: list[dict], times: np.ndarray, E: np.ndarray,
               rivers: list[dict], card: dict | None, near: dict | None = None,
               cur: dict | None = None, hist: dict | None = None,
               soil: dict | None = None, hist_part: dict | None = None,
               soil_now: np.ndarray | None = None, flat: np.ndarray | None = None) -> None:
    """A small, self-contained snapshot for the FloodSense web screen.

    The web app is deliberately light (no scikit-learn, no rasterio) and runs
    on a free host, so it cannot run these models itself. It reads this file
    instead, and says how old it is. Only rain cells with floodable ground
    are included; the page maps its own display grid onto them with the
    lattice below.

    `soil_now` (today's soil input per rain cell: the soil 16 days ago, as
    that cell's own monsoon percentile) and `flat` (the cells the soil model
    is used on) are for the screen's soil panel only."""
    cells = np.flatnonzero(np.isfinite(E) & np.isfinite(times).any(axis=0))
    tn = np.round(np.nan_to_num(times[:, cells], nan=0.0), 2)
    riv = {}
    for r in rivers:
        g = riv.setdefault(r["station_code"], {
            k: r[k] for k in ("station_code", "station_name", "network", "means", "official",
                              "threshold", "last_complete_day", "last_day_max",
                              "newest_day_max", "newest_reading_day", "gauge_offline",
                              "above_threshold_now")})
        g.setdefault("days", {})[r["target_date"]] = {
            "p": r["probability"], "band": r["band"], "basis": r["basis"]}
        if r.get("level_mid") is not None:      # the level line: [low, middle, high] of that day's high
            g["days"][r["target_date"]]["level"] = [r["level_low"], r["level_mid"], r["level_high"]]
    reg = json.loads((ROOT / "models" / "flood_when_gauge" / "stations.json").read_text())
    for code, g in riv.items():
        g["lat"], g["lon"] = reg[code]["lat"], reg[code]["lon"]
        if code in NO_LEVEL_LINE:                # a dam gauge: the screen says why
            g["no_level_line"] = NO_LEVEL_LINE[code]
        if hist is not None:
            g["history"] = hist.get(code, [])
        if hist_part and hist_part.get(code):
            # NWDP part-days: drawn hollow, never used by a forecast
            g["history_part_days"] = hist_part[code]
    snap = {
        "issued_on": today,
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "rain_source": rain_source(),
        "days": [o["date"] for o in outlook],
        "times_an_ordinary_day": [o["times_an_ordinary_day"] for o in outlook],
        "lattice": when_grid.lattice(),
        "cells": cells.tolist(),
        "times_normal": tn.tolist(),
        "rivers": list(riv.values()),
        "track_record": None if not card else {
            "forecasts_logged": card["logged"]["forecasts"],
            "first_issue": card["logged"]["first_issue"],
            "outcomes": card["outcomes"],
            "checked": card.get("all"),
            "near_here": card.get("near_here"),
            "level_line": card.get("level_line"),
        },
    }
    snap["method"] = method_facts()
    if soil is not None:
        snap["soil_wetness"] = dict(soil)
        if soil_now is not None and flat is not None:
            s_ = np.asarray(soil_now, np.float64)[cells]
            snap["soil_wetness"]["pct_now"] = [None if not np.isfinite(v) else round(float(v), 2)
                                               for v in s_]
            snap["soil_wetness"]["flat"] = np.asarray(flat, bool)[cells].astype(int).tolist()
    snap["previous"] = previous_issue(today, cells)
    if near is not None:
        sig = _sig
        meta = cur["meta"]
        snap["near_here"] = {
            "means": ("chance of at least one recorded flood within 10 km of a place (the "
                      "centre of its ~10 km rain cell): each day, and over the whole outlook"),
            "status": meta["status"],
            "radius_km": cur["radius_km"],
            "daily": [sig(row[cells]) for row in near["day"]],
            "week": sig(near["week"][cells]),
            "arunachal_daily": sig(near["state_day"]),
            "arunachal_week": float(f"{near['state_week']:.3g}"),
            "floods_on_record": cur["evidence_days"][cells].astype(int).tolist(),
            "level": cur["level"][cells].astype(int).tolist(),
            "level_names": cur["level_names"],
            "evidence_period": meta["confidence"]["evidence"],
            "measured_error": meta.get("measured_error"),
            "measured_by_level": meta["confidence"].get("measured_by_level"),
        }
    WEB_SNAPSHOT.write_text(json.dumps(snap, separators=(",", ":")))
    print(f"  web snapshot: {WEB_SNAPSHOT} ({WEB_SNAPSHOT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        build()
    else:
        run(log="--no-log" not in sys.argv)
