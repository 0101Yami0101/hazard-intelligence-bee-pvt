"""Live river readings -> a calibrated chance per gauged river, today + 6 days.

Called from flood_forecast_live.py's daily run (which supplies the live rain
inputs); `fetch_daily` is also what forecast_log.py uses to check outcomes.

Sources, both open, no key:
    CWC FFS   water level, near-hourly, live to the hour (18 gauges)
    NWDP      discharge, 15-minute, but published ~2 days behind (14 gauges)

For each target day the model is chosen by how old the last COMPLETE day of
readings is: 1-9 days -> the matching gauge + rain model from
train_flood_when_gauge.py (that covers the whole week, NWDP's lag included);
no recent reading -> the same pipeline on rain alone, calibrated for a river
whose state is unknown. Each row says which it used, and a gauge that has
gone offline says since when.

Since 2026-10-06 the gauge models also read the river's own week
(gauge_week.week_inputs), and each row carries a forecast of the level
itself — low / middle / high of the day's high — for as many days after the
last complete day as the level line was shown to hold (level.json's
draw_to_lead; FLOOD_WHEN_PILOT_PLAN.md §14).
"""
from __future__ import annotations

import json
import pickle
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gauge_week
from backtest_flood_when import clean_readings
from backtest_flood_when_nwdp import DISCH_COL, SENTINEL_ABS, daily_max_discharge
from common import ROOT, UA

GMODELS = ROOT / "models" / "flood_when_gauge"
CWC_API = "https://ffs.india-water.gov.in/iam/api/new-entry-data/specification/"
NWDP_API = "https://nwdp.nwic.gov.in/api/3/action/datastore_search"
NWDP_CURRENT = "9a7feb81-191e-45df-b808-cd9523a97356"
NWDP_MIN_READINGS = 48          # of 96 a day (15-minute data)
BANDS = [(0.25, "SEVERE"), (0.10, "HIGH"), (0.05, "MODERATE"), (0.02, "ELEVATED"), (0.0, "NORMAL")]


def band_for(p: float) -> str:
    return next(name for thr, name in BANDS if p >= thr)


# ── fetching ─────────────────────────────────────────────────────────────
def _first_last(t: pd.Series, v: pd.Series) -> dict:
    """{day: (first reading, last reading, how many)} — what the week inputs
    `end` and `day_rise` need beside the day's high. It rides on the daily
    series as `attrs["first_last_n"]`, so everything that takes a daily
    series (the outcome checks, the replay harness) is untouched."""
    g = pd.DataFrame({"t": t.to_numpy(), "v": v.to_numpy()}).dropna().sort_values("t", kind="stable")
    k = g.groupby(g["t"].dt.normalize())["v"]
    return {d: (float(a), float(b), int(n)) for d, a, b, n in
            zip(k.first().index, k.first(), k.last(), k.count())}


def _cwc_daily(code: str, since: date) -> pd.Series:
    """Daily max level from `since` on. The API takes a nested date filter,
    so this is ~150 rows a week rather than the station's whole history."""
    spec = {"where": {"expression": {"fieldName": "id.stationCode", "operator": "eq", "value": code}},
            "and": {"expression": {"fieldName": "id.datatypeCode", "operator": "eq", "value": "HHS"},
                    "and": {"expression": {"fieldName": "id.dataTime", "operator": "gte",
                                           "value": f"{since}T00:00:00"}}}}
    r = requests.get(CWC_API, params={"specification": json.dumps(spec)}, headers=UA, timeout=60)
    r.raise_for_status()
    rows = r.json()
    if not rows:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([]))
    df = pd.DataFrame({"datetime": pd.to_datetime([x["id"]["dataTime"] for x in rows]),
                       "level": [x["dataValue"] for x in rows]}).dropna().sort_values("datetime")
    df = clean_readings(df.reset_index(drop=True))
    s = df.groupby(df["datetime"].dt.normalize())["level"].max().sort_index()
    s.attrs["first_last_n"] = _first_last(df["datetime"], df["level"])
    return s


def _nwdp_daily(station: str, since: date, with_partial: bool = False):
    """Daily max discharge. Newest-first by row id; 15-minute data, so a
    day is ~96 rows, more when the feed double-posts; fetch generously.
    `with_partial` (the web graph only) also returns the part-days this
    drops, and each one's count of distinct readings."""
    n = 200 * ((date.today() - since).days + 3)
    r = requests.get(NWDP_API, params={"resource_id": NWDP_CURRENT, "limit": min(n, 32000),
                                       "sort": "_id desc",
                                       "filters": json.dumps({"Station": station})},
                     headers=UA, timeout=60)
    r.raise_for_status()
    recs = r.json()["result"]["records"]
    if not recs:
        empty = pd.Series(dtype=float, index=pd.DatetimeIndex([]))
        return (empty, empty, empty) if with_partial else empty
    df = pd.DataFrame(recs)
    df["discharge"] = pd.to_numeric(df[DISCH_COL], errors="coerce")
    df["ts"] = pd.to_datetime(df["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    s = daily_max_discharge(df, station)
    # The feed skips days and posts partial ones (12 of 96 readings seen on
    # 2026-09-16 at Tenga). A partial day's max can miss the peak, so it is
    # neither a usable "latest reading" nor proof the river stayed low.
    n = df.groupby(df["ts"].dt.normalize()).size().reindex(s.index).fillna(0)
    full = s[n >= NWDP_MIN_READINGS]
    full = full[full.index >= pd.Timestamp(since)]
    g = df.loc[df["Station"] == station, ["ts", "discharge"]].dropna()        # as daily_max_discharge
    g = g.loc[~((g["discharge"].abs() >= SENTINEL_ABS) | (g["discharge"] < 0)
                | (g["ts"] < pd.Timestamp("2020-01-01")))]
    full.attrs["first_last_n"] = _first_last(g["ts"], g["discharge"])
    if not with_partial:
        return full
    part = s[(n < NWDP_MIN_READINGS) & (s.index >= pd.Timestamp(since))]
    seen = df.groupby(df["ts"].dt.normalize())["ts"].nunique().reindex(part.index).fillna(0)
    return full, part, seen


def fetch_history(code: str, network: str, since: date) -> tuple[pd.Series, list]:
    """For the web graph only: (the complete days' highs — exactly what
    fetch_daily gives the forecast — and [[day, high, readings], ...] for
    NWDP's part-days). Part-days never reach a forecast; the graph shows
    them hollow and labelled, because a part-day's high can miss the peak."""
    try:
        if network == "CWC":
            return _cwc_daily(code, since), []
        full, part, seen = _nwdp_daily(code, since, with_partial=True)
    except Exception as e:                                          # noqa: BLE001
        print(f"    [warn] {code}: gauge feed unavailable ({type(e).__name__})")
        return pd.Series(dtype=float, index=pd.DatetimeIndex([])), []
    return full, [[str(d.date()), round(float(v), 3), int(seen[d])] for d, v in part.items()]


def fetch_daily(code: str, network: str, since: date) -> tuple[pd.Series, pd.Timestamp | None]:
    """(daily max series, day of the newest reading). Empty series on failure,
    so one silent gauge never stops the others."""
    try:
        s = _cwc_daily(code, since) if network == "CWC" else _nwdp_daily(code, since)
    except Exception as e:                                          # noqa: BLE001
        print(f"    [warn] {code}: gauge feed unavailable ({type(e).__name__})")
        return pd.Series(dtype=float, index=pd.DatetimeIndex([])), None
    return s, (s.index.max() if len(s) else None)


# ── forecasting ──────────────────────────────────────────────────────────
def last_seen(code: str, network: str) -> str | None:
    """Date of a silent gauge's newest reading, from the last two years."""
    try:
        if network == "CWC":
            s = _cwc_daily(code, date.today() - timedelta(days=730))
            return str(s.index.max().date()) if len(s) else None
        r = requests.get(NWDP_API, params={"resource_id": NWDP_CURRENT, "limit": 1,
                                           "sort": "_id desc",
                                           "filters": json.dumps({"Station": code})},
                         headers=UA, timeout=60)
        recs = r.json()["result"]["records"]
        if not recs:                        # nothing in the current (2026-) resource
            return None
        t = pd.to_datetime(recs[0]["Data Acquisition Time"], format="%d-%m-%Y %H:%M")
        return str(t.date())
    except Exception:                                               # noqa: BLE001
        return None


def history(days: int = 30, issued: date | None = None) -> tuple[dict, dict]:
    """Each gauge's measured daily maximum over the last `days` days, for the
    web graph: ({code: [[date, value], ...]}, {code: [[date, value,
    readings], ...]} — NWDP's part-days, shown hollow).

    DISPLAY ONLY, and a separate fetch on purpose. forecast() keeps its own
    8-day window: widening that one would silently change which gauges count
    as offline and which reading counts as "now" (FLOOD_SCREEN_PLAN.md,
    Phase 5). The same cleaning applies (fetch_history's complete days are
    fetch_daily's), so the line shows exactly the readings the models see."""
    issued = issued or date.today()
    stations = json.loads((GMODELS / "stations.json").read_text())
    out, part = {}, {}
    for code, st in stations.items():
        # NWDP's own feed skips whole days and posts partial ones (kept off
        # the line, see _nwdp_daily), so its history has real gaps — the
        # graph shows them as gaps rather than joining across them
        s, p = fetch_history(code, st["network"], issued - timedelta(days=days))
        s = s[s.index < pd.Timestamp(issued) + pd.Timedelta(days=1)]
        out[code] = [[str(d.date()), round(float(v), 3)] for d, v in s.items()]
        part[code] = [x for x in p if x[0] <= str(issued)]
    return out, part


def load_models() -> tuple[dict, dict]:
    ms = {}
    for f in sorted(GMODELS.glob("lead*.pkl")):
        with open(f, "rb") as fh:
            m = pickle.load(fh)
        ms[m["lead"]] = m
    with open(GMODELS / "rain_only.pkl", "rb") as fh:
        ms["rain"] = pickle.load(fh)
    return ms, json.loads((GMODELS / "stations.json").read_text())


def load_levels() -> tuple[dict, int]:
    """({lead: level model}, how many days after the last complete day the
    level line may be drawn). Empty when the folder holds no level models."""
    meta = GMODELS / "level.json"
    if not meta.exists():
        return {}, 0
    out = {}
    for f in sorted(GMODELS.glob("level*.pkl")):
        with open(f, "rb") as fh:
            m = pickle.load(fh)
        out[m["lead"]] = m
    return out, int(json.loads(meta.read_text())["draw_to_lead"])


def _prob(m: dict, X: pd.DataFrame, group: int) -> float:
    raw = m["model"].predict_proba(X[m["features"]])[:, 1]
    return float(m["calibrators"][group].predict(raw)[0])


def week_now(daily: pd.Series, complete: pd.Series, last: pd.Timestamp | None, st: dict) -> dict:
    """The six week inputs as they stand on the last complete day — through
    the function the models were trained with. Empty values where the feed
    gives no first/last readings (a daily series from before 2026-10-06)."""
    if last is None:
        return dict.fromkeys(gauge_week.T.WEEK_FEATS, np.nan)
    extra = daily.attrs.get("first_last_n", {})
    days = pd.DataFrame({"high": complete})
    for i, col in enumerate(("first", "last", "n")):
        days[col] = [extra[d][i] if d in extra else np.nan for d in days.index]
    days["n"] = days["n"].fillna(0)
    return gauge_week.week_inputs(days, st).loc[last].to_dict()


def _level(m: dict, X: pd.DataFrame, group: int, g_frac: float, st: dict) -> list[float]:
    """[low, middle, high] of the target day's high, in the gauge's units."""
    raw = np.sort([[float(m["models"][q].predict(X[m["features"]])[0]) for q in sorted(m["models"])]], axis=1)
    lo, mid, hi = gauge_week.apply_margins(raw, np.array([group]), m["margins"])[0]
    span = st["threshold"] - st["base"]
    out = [st["base"] + (g_frac + c) * span for c in (lo, mid, hi)]
    if st["network"] == "NWDP":                 # a flow cannot be negative
        out = [max(0.0, v) for v in out]
    return [round(float(v), 3) for v in out]


def forecast(days: list[str], idx: list[int], r3p: np.ndarray, r7p: np.ndarray,
             lag: np.ndarray, issued: date | None = None) -> list[dict]:
    """One row per gauge per outlook day. r3p/r7p/lag are (days x rain cells),
    already scored against the live rain source's own history."""
    issued = issued or date.today()
    models, stations = load_models()
    levels, draw_to = load_levels()
    since = issued - timedelta(days=8)
    rows = []
    print(f"  reading {len(stations)} river gauges...", flush=True)
    for code, st in stations.items():
        daily, newest = fetch_daily(code, st["network"], since)
        complete = daily[daily.index < pd.Timestamp(issued)]
        last = complete.index.max() if len(complete) else None
        frac = (complete - st["base"]) / (st["threshold"] - st["base"])
        g_frac = float(frac.iloc[-1]) if last is not None else np.nan
        prev = last - pd.Timedelta(days=1) if last is not None else None
        g_rise = (g_frac - float(frac[prev])) if prev is not None and prev in frac.index else np.nan
        above = int(last is not None and complete.iloc[-1] >= st["threshold"])
        group = above + 2 * int(st["official"])
        week = week_now(daily, complete, last, st)
        now_val = float(daily.iloc[-1]) if len(daily) else None
        seen = (str(newest.date()) if newest is not None
                else last_seen(code, st["network"]) or st.get("record_ends"))
        c = st["cell"]
        for i in idx:
            target = pd.Timestamp(days[i])
            lead = (target - last).days if last is not None else None
            X = pd.DataFrame({"r3": [r3p[i, c]], "r7": [r7p[i, c]], "trigger_lag1": [lag[i, c]],
                              "g_frac": [g_frac], "g_rise": [g_rise], **{k: [v] for k, v in week.items()}})
            if not np.isfinite(X[["r3", "r7"]].to_numpy()).all():
                continue
            if lead is not None and lead in models:
                p, basis = _prob(models[lead], X, group), f"rain + river reading ({lead} day old)"
            else:
                p, basis = _prob(models["rain"], X, 2 * int(st["official"])), "rain only"
            lvl = (_level(levels[lead], X, group, g_frac, st)
                   if lead is not None and lead <= draw_to and lead in levels else [None, None, None])
            rows.append({
                "issued_on": str(issued), "target_date": days[i],
                "lead_days": int((target.date() - issued).days),
                "station_code": code, "station_name": st["name"], "network": st["network"],
                "means": st["means"], "official": bool(st["official"]),
                "threshold": st["threshold"], "base_rate": st["base_rate"],
                "probability": round(p, 4), "band": band_for(p), "basis": basis,
                "last_complete_day": str(last.date()) if last is not None else None,
                "last_day_max": round(float(complete.iloc[-1]), 3) if last is not None else None,
                "newest_day_max": now_val, "newest_reading_day": seen,
                "gauge_offline": newest is None,
                "above_threshold_now": bool(now_val is not None and now_val >= st["threshold"]),
                "level_low": lvl[0], "level_mid": lvl[1], "level_high": lvl[2],
            })
    return rows
