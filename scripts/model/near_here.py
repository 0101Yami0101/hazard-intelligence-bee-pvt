"""Flood chance NEAR HERE: within 10 km, for each day and for the next 7 days.

    python scripts/model/near_here.py check   # the held-out test (Gate A)
    python scripts/model/near_here.py fit     # the production curves
    (flood_forecast_live.py applies them every day through apply())

Writes  reports/flood_near_here_check.json          (check)
        models/flood_forecast/near_here/curves.pkl  (fit)
        models/flood_forecast/near_here/_meta.json  (fit)

════════════════════════════════════════════════════════════════════════════
THE NUMBERS
════════════════════════════════════════════════════════════════════════════
    day    P(at least one flood record within 10 km of this place, that day)
    week   P(at least one ... within 10 km, in the 7 days from today)
    state  P(at least one flood record in an Arunachal rain cell), day / week

"Flood record" is the truth every flood model here uses: a reported flood
that passed a Sentinel-1 screen (tested later, it filters out almost nothing —
PARKED §0w — so in effect a reported flood), braided-channel
suspects removed. "This place" is the centre of its 0.1° rain cell, so
"within 10 km" is within 10 km of that centre. Floods nobody reported, and
flash floods gone before a satellite passed, are not in the truth — so these
are chances of a *recorded* flood, a floor for every flood.

Why this and not "this 100 m spot, today": see docs/design/FLOOD_SCREEN_PLAN.md
§3 — per spot per day the honest number is tiny, cannot be checked spot by
spot, and runs ~4x high in Arunachal; the area chance is the part that adds up.

════════════════════════════════════════════════════════════════════════════
HOW
════════════════════════════════════════════════════════════════════════════
    1. raw day  = 1 - prod_j (1 - w_j p_j): the day model's own-cell chances
                  p (UNCHANGED model), over the cells the 10 km circle
                  touches, each weighted by the share of its area inside the
                  circle (own cell = 1)
    2. day      = isotonic(raw day), fitted to how often a record really fell
                  within 10 km; never below the own-cell chance (every point
                  of a cell is within 7.4 km of its centre, so a flood in the
                  cell is always "near here")
    3. raw week = 1 - prod_d (1 - day_d) over the 7 days
    4. week     = isotonic(raw week), fitted to how often a week really had
                  one; kept within [its likeliest day, min(1, sum of days)]
    Statewide: the same recipe, "any record in an Arunachal cell".

The raw unions assume floods are independent across places and days. They
are not — floods cluster — so the raw values over-state, and the curves,
fitted on real outcomes, correct that. Every number shown is therefore
calibrated against exactly the event its label names.

════════════════════════════════════════════════════════════════════════════
THE TEST (check) — nothing that makes a number has seen the test years
════════════════════════════════════════════════════════════════════════════
    floodable area (E)   WHERE retrained on floods up to 2022 only
    day model            tree 2015-20, calibration 2021-22 (satellite rain)
    rain it is fed       the Open-Meteo ARCHIVE, scored exactly as the live
                         path scores live rain
    near-here curves     fitted 2021-22
    graded               2023-01-01 .. 2025-10-31, inside Arunachal

TRUTH_END: the flood record runs to Oct 2025 (17 records that month, 2 in Jan
2026, none after). Days past it have no truth and are never fitted or graded.
Gate A (pass marks) is pre-registered in FLOOD_SCREEN_PLAN.md, Phase 2.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

ROOT_ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_ / "scripts"), str(ROOT_ / "scripts" / "build"),
                str(ROOT_ / "scripts" / "model"), str(ROOT_ / "webapp")]

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

import when_grid
from common import INTERIM, ROOT
from flood_forecast import (MODELS, TREE_FROM, TRUTH_END, day_features, exposure, fit_day_model,
                            imerg_index_full, label_matrix, load_events, predict_day,
                            soil_input)

RADIUS_KM = 10.0
TRUTH_START = pd.Timestamp("2015-06-01")      # first record 2015-06-03
# The "floods on record" count starts at the verified record's first flood
# (2003-07-06, a news report Google's Global Flood Database confirmed), not
# at TRUTH_START: since 2026-09-28 the record holds 326 floods from before
# 2015 that the count left out (docs/design/OLDER_FLOODS_TEST.md §1).
# TRUTH_START still sets the test windows it always did.
EVIDENCE_START = pd.Timestamp("2003-01-01")
WEEK = 7
KM_PER_DEG = 111.2
SUB = 24                                      # sub-samples per cell side, area weights
CURVES = MODELS / "near_here"
REPORT = ROOT / "reports" / "flood_near_here_check.json"
REPLAY_WHERE = ROOT / "models" / "flood_where_replay2022_clean"
TEST_FROM = pd.Timestamp("2023-01-01")

# Gate A, pre-registered (FLOOD_SCREEN_PLAN.md, Phase 2)
A1_FACTOR = 1.5
A2_FACTOR = 2.0
A2_MIN_POS = 10
DAY_EDGES = [0, 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 1.0001]
WEEK_EDGES = [0, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10, 0.25, 0.50, 1.0001]
STATE_EDGES = [0, 0.02, 0.05, 0.10, 0.25, 0.50, 0.75, 1.0001]


# ── geometry ──────────────────────────────────────────────────────────────
def neighbour_weights(radius_km: float | None = None) -> sparse.csr_matrix:
    """(cells x cells): W[k, j] = share of rain cell j's area lying within
    radius_km of cell k's centre (sub-sampled SUB x SUB per cell)."""
    radius_km = radius_km or RADIUS_KM
    L = when_grid.lattice()
    lat, lon = when_grid.cell_centres()
    nlat, nlon, deg = L["nlat"], L["nlon"], L["deg"]
    off = ((np.arange(SUB) + 0.5) / SUB - 0.5) * deg
    ring = int(np.ceil(radius_km / (deg * KM_PER_DEG * np.cos(np.radians(lat.max()))))) + 1
    rows, cols, vals = [], [], []
    for k in range(len(lat)):
        r, c = divmod(k, nlon)
        cx = np.cos(np.radians(lat[k]))
        for dr in range(-ring, ring + 1):
            for dc in range(-ring, ring + 1):
                r2, c2 = r + dr, c + dc
                if not (0 <= r2 < nlat and 0 <= c2 < nlon):
                    continue
                j = r2 * nlon + c2
                dy = (lat[j] - lat[k] + off[:, None]) * KM_PER_DEG
                dx = (lon[j] - lon[k] + off[None, :]) * KM_PER_DEG * cx
                w = float((np.hypot(dx, dy) <= radius_km).mean())
                if w > 0:
                    rows.append(k)
                    cols.append(j)
                    vals.append(w)
    return sparse.csr_matrix((np.asarray(vals, np.float32), (rows, cols)),
                             shape=(len(lat), len(lat)))


def near_raw(P: np.ndarray, Wt: sparse.csr_matrix) -> np.ndarray:
    """1 - prod_j (1 - w_kj p_j) for every row of P (days x cells). A
    neighbour with no chance (NaN, e.g. no terrain) adds nothing; a place
    whose own cell has no chance stays NaN."""
    coo = Wt.tocoo()
    K, J, w = coo.row, coo.col, coo.data.astype(np.float32)
    A = sparse.csr_matrix((np.ones(len(K), np.float32), (np.arange(len(K)), K)),
                          shape=(len(K), Wt.shape[0]))
    Pz = np.clip(np.nan_to_num(np.asarray(P, np.float32), nan=0.0), 0.0, 1 - 1e-7)
    out = np.empty(Pz.shape, np.float32)
    for a in range(0, Pz.shape[0], 256):
        Lg = np.log1p(-w[None, :] * Pz[a:a + 256][:, J])          # (days, pairs)
        out[a:a + 256] = -np.expm1(np.asarray((A.T @ Lg.T).T))
    out[~np.isfinite(np.asarray(P))] = np.nan
    return out


def state_raw(P: np.ndarray, ap: np.ndarray) -> np.ndarray:
    Pz = np.clip(np.nan_to_num(np.asarray(P, np.float64)[..., ap], nan=0.0), 0.0, 1 - 1e-7)
    return -np.expm1(np.log1p(-Pz).sum(axis=-1))


# ── windows ───────────────────────────────────────────────────────────────
def week_raw(q: np.ndarray) -> np.ndarray:
    """Row t = 1 - prod over days t..t+6; NaN where the window runs off the end."""
    Lg = np.log1p(-np.clip(np.nan_to_num(q, nan=0.0), 0.0, 1 - 1e-7)).astype(np.float64)
    cs = np.concatenate([np.zeros((1,) + q.shape[1:]), np.cumsum(Lg, axis=0)])
    out = np.full(q.shape, np.nan, np.float32)
    out[:q.shape[0] - WEEK + 1] = -np.expm1(cs[WEEK:] - cs[:-WEEK])
    out[~np.isfinite(q)] = np.nan
    return out


def week_bounds(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(likeliest single day, min(1, sum of days)) over each window."""
    from numpy.lib.stride_tricks import sliding_window_view
    lo = np.full(q.shape, np.nan, np.float32)
    hi = np.full(q.shape, np.nan, np.float32)
    v = sliding_window_view(np.nan_to_num(q, nan=0.0), WEEK, axis=0)
    lo[:v.shape[0]] = v.max(axis=-1)
    hi[:v.shape[0]] = np.minimum(1.0, v.sum(axis=-1))
    return lo, hi


def week_any(Y: np.ndarray) -> np.ndarray:
    cs = np.concatenate([np.zeros((1,) + Y.shape[1:], np.int32),
                         np.cumsum(Y, axis=0, dtype=np.int32)])
    out = np.zeros(Y.shape, np.uint8)
    out[:Y.shape[0] - WEEK + 1] = (cs[WEEK:] - cs[:-WEEK]) > 0
    return out


# ── truth ─────────────────────────────────────────────────────────────────
# Which flood record is the truth: "reported" (the list every model trained on
# until 2026-09-28 — news reports; its radar screen filters out almost nothing,
# PARKED §0w) or "verified" (events some independent route confirms —
# build_verified_floods.py, PARKED §0x). Set by --truth.
TRUTH = "verified"          # the production record since 2026-09-28 (flood_forecast.TRAIN_RECORD)


def clean_events() -> pd.DataFrame:
    if TRUTH == "verified":
        ev = pd.read_parquet(INTERIM / "flood_events" / "verified_events.parquet")
        ev["date"] = pd.to_datetime(ev["date"])
        ev["k"] = when_grid.cell_of(ev["lat"].to_numpy(), ev["lon"].to_numpy())
        return ev[["uuid", "date", "lat", "lon", "k"]].reset_index(drop=True)
    sus = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
              ["channel_shift_suspects"]["uuids"])
    ev = load_events()
    return ev[~ev["uuid"].isin(sus)].reset_index(drop=True)


def truth_near(ev: pd.DataFrame, dates: pd.DatetimeIndex, radius_km: float | None = None) -> np.ndarray:
    """(days x cells): 1 where a record fell within radius_km of the centre."""
    radius_km = radius_km or RADIUS_KM
    lat, lon = when_grid.cell_centres()
    Y = np.zeros((len(dates), len(lat)), np.uint8)
    pos = pd.Series(np.arange(len(dates)), index=dates)
    e = ev[ev["date"].isin(dates)]
    for la, lo, d in zip(e["lat"], e["lon"], e["date"]):
        dist = KM_PER_DEG * np.hypot(lat - la, (lon - lo) * np.cos(np.radians(la)))
        Y[pos[d], dist <= radius_km] = 1
    return Y


def arunachal_cells(n_cells: int) -> np.ndarray:
    """Rain cells more than half inside the state — the replay's definition."""
    import rasterio
    kidx = imerg_index_full()
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        inst = m.read(1).astype(bool)
    v = kidx >= 0
    frac = (np.bincount(kidx[v & inst], minlength=n_cells)
            / np.maximum(np.bincount(kidx[v], minlength=n_cells), 1))
    return frac > 0.5


# ── the live-path rain, over the whole archive ────────────────────────────
def live_archive_features() -> tuple[pd.DatetimeIndex, list[np.ndarray]]:
    """The day model's inputs from the Open-Meteo archive, scored exactly as
    the daily run scores live rain (same points, same scales, same code)."""
    import flood_forecast_live as ffl
    om = np.load(ffl.OM / "precip_mm.npy").astype(np.float32)
    od = pd.to_datetime(np.load(ffl.OM / "dates.npy", allow_pickle=True))
    S = dict(np.load(ffl.LIVE / "scales.npz"))
    nn = S.pop("nn")
    return od, ffl.features(om[:, nn], S, ffl._upstream_matrix(), ffl._when_panel())


# ── curves ────────────────────────────────────────────────────────────────
def fit_iso(x: np.ndarray, y: np.ndarray) -> IsotonicRegression:
    x, y = np.asarray(x, np.float64).ravel(), np.asarray(y, np.float64).ravel()
    ok = np.isfinite(x)
    return IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip").fit(x[ok], y[ok])


def _iso(iso: IsotonicRegression, x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, np.float64)
    out = np.full(x.shape, np.nan, np.float32)
    ok = np.isfinite(x)
    out[ok] = iso.predict(x[ok])
    return out


def day_chance(P: np.ndarray, cur: dict) -> np.ndarray:
    """Calibrated daily near-here chance; never below the own-cell chance."""
    q = _iso(cur["iso_day"], near_raw(P, cur["W"]))
    return np.where(np.isfinite(q), np.fmax(q, np.nan_to_num(P, nan=0.0)), np.nan).astype(np.float32)


def fit_curves(P: np.ndarray, dates: pd.DatetimeIndex, ev: pd.DataFrame, ap: np.ndarray,
               cells: np.ndarray, lo: str, hi: str) -> dict:
    """All four curves, fitted on truth days lo..hi (weekly: windows that end
    by hi). `cells` = places with a chance (finite floodable area)."""
    Wt = neighbour_weights(RADIUS_KM)
    days = np.asarray((dates >= pd.Timestamp(lo)) & (dates <= pd.Timestamp(hi)))
    wdays = days & np.asarray(dates + pd.Timedelta(days=WEEK - 1) <= pd.Timestamp(hi))
    Yn = truth_near(ev, dates)
    cur = {"W": Wt, "radius_km": RADIUS_KM, "ap": ap}
    raw = near_raw(P, Wt)
    cur["iso_day"] = fit_iso(raw[days][:, cells], Yn[days][:, cells])
    q = day_chance(P, cur)
    cur["iso_week"] = fit_iso(week_raw(q)[wdays][:, cells], week_any(Yn)[wdays][:, cells])
    ys = label_matrix(ev, dates, P.shape[1])[:, ap].any(axis=1).astype(np.uint8)
    cur["iso_state_day"] = fit_iso(state_raw(P, ap)[days], ys[days])
    sd = state_day_chance(P, cur)
    cur["iso_state_week"] = fit_iso(week_raw(sd[:, None])[:, 0][wdays], week_any(ys[:, None])[:, 0][wdays])
    cur["fit"] = {"from": lo, "to": hi, "n_days": int(days.sum()),
                  "near_here_place_days_with_a_flood": int(Yn[days][:, cells].sum()),
                  "arunachal_days_with_a_flood": int(ys[days].sum())}
    return cur


def state_day_chance(P: np.ndarray, cur: dict) -> np.ndarray:
    """Calibrated statewide daily chance; never below any Arunachal cell's own."""
    ap = cur["ap"]
    s = _iso(cur["iso_state_day"], state_raw(P, ap))
    return np.fmax(s, np.nanmax(np.where(np.isfinite(P[:, ap]), P[:, ap], 0.0), axis=1)).astype(np.float32)


def week_series(q: np.ndarray, iso: IsotonicRegression) -> np.ndarray:
    """Calibrated week chance for every issue day, kept within its bounds."""
    wk = _iso(iso, week_raw(q))
    lo, hi = week_bounds(q)
    return np.where(np.isfinite(wk), np.clip(wk, lo, hi), np.nan).astype(np.float32)


def apply(P7: np.ndarray, cur: dict) -> dict:
    """The daily run: P7 = the day model's chances for today .. +6 (rows)
    across all rain cells. Returns calibrated daily and week chances."""
    q = day_chance(P7, cur)
    wraw = -np.expm1(np.log1p(-np.clip(np.nan_to_num(q, nan=0.0), 0.0, 1 - 1e-7)).sum(axis=0))
    wk = _iso(cur["iso_week"], np.where(np.isfinite(q[0]), wraw, np.nan))
    wk = np.where(np.isfinite(wk), np.clip(wk, np.nanmax(np.nan_to_num(q, nan=0.0), axis=0),
                                             np.minimum(1.0, np.nansum(q, axis=0))), np.nan)
    sd = state_day_chance(P7, cur)
    sraw = -np.expm1(np.log1p(-np.clip(sd, 0.0, 1 - 1e-7)).sum())
    sw = float(np.clip(_iso(cur["iso_state_week"], np.array([sraw]))[0],
                       sd.max(), min(1.0, float(sd.sum()))))
    _assert_consistent(P7, q, wk, sd, sw, cur["ap"])
    return {"day": q, "week": wk.astype(np.float32), "state_day": sd, "state_week": sw,
            "n_days": int(P7.shape[0])}


def _assert_consistent(P, q, wk, sd, sw, ap, tol: float = 1e-6) -> None:
    """The logic every published number must obey (FLOOD_SCREEN_PLAN.md §2.5)."""
    f = np.isfinite(q)
    assert (q[f] >= np.nan_to_num(P, nan=0.0)[f] - tol).all(), "near-here day below own cell"
    ok = np.isfinite(wk)
    qz = np.nan_to_num(q, nan=0.0)
    assert (wk[ok] >= qz.max(axis=0)[ok] - tol).all(), "week below its likeliest day"
    assert (wk[ok] <= np.minimum(1.0, qz.sum(axis=0))[ok] + tol).all(), "week above sum of days"
    assert (sd >= np.nanmax(np.nan_to_num(P[:, ap], nan=0.0), axis=1) - tol).all(), "state below a cell"
    assert sd.max() - tol <= sw <= min(1.0, float(sd.sum())) + tol, "state week out of bounds"


# ── grading ───────────────────────────────────────────────────────────────
def reliability(y: np.ndarray, p: np.ndarray, edges) -> list[dict]:
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() == 0:
            continue
        out.append({"range": f"{100*lo:g}-{100*min(hi, 1):g}%", "n": int(m.sum()),
                    "n_with_flood": int(y[m].sum()),
                    "said_pct": round(100 * float(p[m].mean()), 4),
                    "happened_pct": round(100 * float(y[m].mean()), 4)})
    return out


def grade(y: np.ndarray, p: np.ndarray, clim: np.ndarray, rec: np.ndarray | None,
          edges) -> dict:
    """A1-A3 for one kind of number. y outcomes, p forecasts, clim the
    forecast's own seasonal level, rec the record's place-and-month rate."""
    ok = np.isfinite(p) & np.isfinite(clim)
    y, p, clim = y[ok].astype(np.float64), p[ok].astype(np.float64), clim[ok].astype(np.float64)
    bs = float(np.mean((p - y) ** 2))
    rel = reliability(y, p, edges)
    judged = [b for b in rel if b["n_with_flood"] >= A2_MIN_POS]
    a2_ok = all(1 / A2_FACTOR <= (b["happened_pct"] / b["said_pct"] if b["said_pct"] > 0 else np.inf)
                <= A2_FACTOR for b in judged)
    ratio = float(p.sum() / max(y.sum(), 1e-9))
    out = {"n": int(len(y)), "n_with_flood": int(y.sum()),
           "said_total": round(float(p.sum()), 2), "happened_total": int(y.sum()),
           "A1_said_over_happened": round(ratio, 3),
           "A1_pass": bool(1 / A1_FACTOR <= ratio <= A1_FACTOR),
           "A2_ranges_judged": len(judged), "A2_pass": bool(a2_ok and len(judged) > 0),
           "A3_brier_skill_vs_own_season": round(1 - bs / float(np.mean((clim - y) ** 2)), 4),
           "auc": round(float(roc_auc_score(y, p)), 4) if 0 < y.sum() < len(y) else None,
           "timing_auc_vs_own_season": (round(float(roc_auc_score(y, p / np.maximum(clim, 1e-9))), 4)
                                        if 0 < y.sum() < len(y) else None),
           "reliability": rel}
    out["A3_pass"] = bool(out["A3_brier_skill_vs_own_season"] > 0)
    if rec is not None:
        r = rec[ok].astype(np.float64)
        out["info_brier_skill_vs_record_place_month"] = round(1 - bs / float(np.mean((r - y) ** 2)), 4)
    return out


def _month_table(values: np.ndarray, dates: pd.DatetimeIndex, mask: np.ndarray) -> np.ndarray:
    """(12, cells) mean of values over the masked days, by calendar month."""
    out = np.full((12,) + values.shape[1:], np.nan, np.float32)
    for mth in range(1, 13):
        m = mask & np.asarray(dates.month == mth)
        if m.any():
            out[mth - 1] = np.nanmean(values[m], axis=0)
    return out


# ── check ─────────────────────────────────────────────────────────────────
def check() -> dict:
    t0 = time.time()
    print("Flood chance NEAR HERE — held-out test (Gate A)\n")
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    kidx = imerg_index_full()
    cache = INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy"
    if cache.exists():
        E = np.load(cache)
    else:
        from predict_flood_where import score_grid
        print("  scoring the 2022-only WHERE over the window (once)...", flush=True)
        H, _ = score_grid(REPLAY_WHERE, clip_to_state=False, verbose=False)
        E = exposure(H, kidx, n)
        np.save(cache, E)
    ev = clean_events()
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    print("  day model, test copy (tree 2015-20, calibration 2021-22, satellite rain)...", flush=True)
    m, info = fit_day_model(day_features(Wim, upstream=True), E, label_matrix(ev, wd, n),
                           yrs(wd, 2015, 2020), yrs(wd, 2021, 2022), wd)
    print(f"    {info}  ({time.time()-t0:.0f}s)")
    print("  live-archive rain -> day-model chances, 2010-2026...", flush=True)
    od, F = live_archive_features()
    P = m.predict(F, E, soil_input(od))
    print(f"    {P.shape}  ({time.time()-t0:.0f}s)")

    ap = arunachal_cells(n) & np.isfinite(E)
    cells = np.isfinite(E)
    print("  fitting the near-here curves on 2021-22...", flush=True)
    cur = fit_curves(P, od, ev, ap, cells, "2021-01-01", "2022-12-31")
    print(f"    {cur['fit']}  ({time.time()-t0:.0f}s)")

    q = day_chance(P, cur)
    wk = week_series(q, cur["iso_week"])
    sd = state_day_chance(P, cur)
    sw = week_series(sd[:, None], cur["iso_state_week"])[:, 0]
    Yn = truth_near(ev, od)
    Yw = week_any(Yn)
    ys = label_matrix(ev, od, n)[:, ap].any(axis=1).astype(np.uint8)
    ysw = week_any(ys[:, None])[:, 0]

    # consistency on every day of the archive (A4)
    f = np.isfinite(q)
    lo, hi = week_bounds(q)
    wf = np.isfinite(wk)
    slo, shi = week_bounds(sd[:, None])
    a4 = {
        "near_day_below_own_cell": int((q[f] < np.nan_to_num(P, nan=0.0)[f] - 1e-6).sum()),
        "week_below_likeliest_day": int((wk[wf] < lo[wf] - 1e-6).sum()),
        "week_above_sum_of_days": int((wk[wf] > hi[wf] + 1e-6).sum()),
        "state_day_below_a_cell": int((sd < np.nanmax(np.nan_to_num(P[:, ap], nan=0.0), axis=1) - 1e-6).sum()),
        "state_week_out_of_bounds": int(((sw < slo[:, 0] - 1e-6) | (sw > shi[:, 0] + 1e-6))[np.isfinite(sw)].sum()),
    }
    raw_week = _iso(cur["iso_week"], week_raw(q))
    bind = np.isfinite(raw_week) & np.isfinite(wk) & (np.abs(raw_week - wk) > 1e-7)
    a4_binding = {"week_clipped_share": round(float(bind[wf].mean()), 5),
                  "day_raised_to_own_cell_share": round(float(
                      (np.abs(q - _iso(cur["iso_day"], near_raw(P, cur["W"]))) > 1e-7)[f].mean()), 5)}

    # the forecast's own seasonal level: years the day model never trained on
    base = np.asarray(((od.year >= 2010) & (od.year <= 2014)) | ((od.year >= 2021) & (od.year <= 2022)))
    clim_d = _month_table(q, od, base)
    clim_w = _month_table(wk, od, base)
    clim_sd = _month_table(sd[:, None], od, base)[:, 0]
    clim_sw = _month_table(sw[:, None], od, base)[:, 0]
    recb = np.asarray((od >= TRUTH_START) & (od <= pd.Timestamp("2022-12-31")))
    rec_d = _month_table(Yn.astype(np.float32), od, recb)
    rec_w = _month_table(Yw.astype(np.float32), od, recb)

    test = np.asarray((od >= TEST_FROM) & (od <= TRUTH_END))
    wtest = test & np.asarray(od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END)
    phase = np.asarray((od - TEST_FROM).days % WEEK)
    mon = np.asarray(od.month) - 1

    def cellwise(sel, cmask, val, clim, rec, Y, edges):
        rows = np.flatnonzero(sel)
        cc = np.flatnonzero(cmask)
        p = val[np.ix_(rows, cc)].ravel()
        y = Y[np.ix_(rows, cc)].ravel()
        c = clim[np.ix_(mon[rows], cc)].ravel()
        r = rec[np.ix_(mon[rows], cc)].ravel() if rec is not None else None
        return grade(y, p, c, r, edges)

    res = {"day_in_arunachal": cellwise(test, ap, q, clim_d, rec_d, Yn, DAY_EDGES),
           "week_in_arunachal": cellwise(wtest & (phase == 0), ap, wk, clim_w, rec_w, Yw, WEEK_EDGES),
           "day_region_wide": cellwise(test, cells, q, clim_d, None, Yn, DAY_EDGES),
           "week_region_wide": cellwise(wtest & (phase == 0), cells, wk, clim_w, None, Yw, WEEK_EDGES)}
    st_rows = np.flatnonzero(test)
    res["state_day"] = grade(ys[st_rows], sd[st_rows], clim_sd[mon[st_rows]], None, STATE_EDGES)
    w_rows = np.flatnonzero(wtest & (phase == 0))
    res["state_week"] = grade(ysw[w_rows], sw[w_rows], clim_sw[mon[w_rows]], None, STATE_EDGES)

    # A1 for every week phase, and per test year
    res["week_in_arunachal_A1_all_phases"] = [
        round(float(np.nansum(wk[np.ix_(wtest & (phase == ph), ap)])
                    / max(Yw[np.ix_(wtest & (phase == ph), ap)].sum(), 1)), 3) for ph in range(WEEK)]
    res["day_in_arunachal_A1_by_year"] = {
        str(y): {"said": round(float(np.nansum(q[np.ix_(test & np.asarray(od.year == y), ap)])), 1),
                 "happened": int(Yn[np.ix_(test & np.asarray(od.year == y), ap)].sum())}
        for y in (2023, 2024, 2025)}

    # what people will see: week chances inside Arunachal, test weeks
    v = wk[np.ix_(wtest & (phase == 0), ap)].ravel()
    v = v[np.isfinite(v)]
    mons = np.isin(od.month, [6, 7, 8, 9])
    vm = wk[np.ix_(wtest & (phase == 0) & mons, ap)].ravel()
    vm = vm[np.isfinite(vm)]
    res["what_people_see_week_in_arunachal"] = {
        "all_weeks": {"median_pct": round(100 * float(np.median(v)), 3),
                      "p90_pct": round(100 * float(np.percentile(v, 90)), 3),
                      "p99_pct": round(100 * float(np.percentile(v, 99)), 3),
                      "share_at_or_above": {f"{t}%": round(float((v >= t / 100).mean()), 4)
                                            for t in (2, 5, 10, 25)}},
        "jun_to_sep_weeks": {"median_pct": round(100 * float(np.median(vm)), 3),
                             "p90_pct": round(100 * float(np.percentile(vm, 90)), 3),
                             "p99_pct": round(100 * float(np.percentile(vm, 99)), 3),
                             "share_at_or_above": {f"{t}%": round(float((vm >= t / 100).mean()), 4)
                                                   for t in (2, 5, 10, 25)}}}

    gate = {k: {g: res[k][g] for g in ("A1_pass", "A2_pass", "A3_pass")}
            for k in ("day_in_arunachal", "week_in_arunachal", "state_day", "state_week")}
    a4_ok = all(v_ == 0 for v_ in a4.values())
    passed = a4_ok and all(all(g.values()) for g in gate.values())
    out = {
        "what": ("flood chance within 10 km (day, week) and anywhere in Arunachal (day, week), "
                 "graded 2023-01-01..2025-10-31 on models that never saw those years; "
                 "pass marks pre-registered in docs/design/FLOOD_SCREEN_PLAN.md Phase 2"),
        "truth": (f"the {TRUTH} flood record (build_verified_floods.py, PARKED §0x)"
                  if TRUTH == "verified" else
                  "news-reported flood; its Sentinel-1 screen filters out almost nothing "
                  "(PARKED §0w); channel-shift suspects removed"),
        "truth_end": str(TRUTH_END.date()), "radius_km": RADIUS_KM,
        "design": {"floodable_area": "WHERE retrained on floods to 2022 (clean)",
                   "day_model": "tree 2015-20, calibration 2021-22, satellite rain",
                   "rain_fed": "Open-Meteo archive, scored as the live path scores live rain",
                   "near_here_curves": "fitted 2021-22, region-wide",
                   "weekly_grading": "non-overlapping weeks from 2023-01-01",
                   "seasonal_baseline": "the forecast's own mean by place and calendar month, "
                                        "live-archive 2010-14 and 2021-22"},
        "fit": cur["fit"], "gate": gate, "A4_consistency_violations": a4,
        "A4_how_often_the_rules_bind": a4_binding, "GATE_A_PASS": bool(passed),
        "results": res,
    }
    rep = REPORT if RADIUS_KM == 10.0 else REPORT.with_name(f"{REPORT.stem}_{RADIUS_KM:g}km.json")
    if TRUTH != "reported":
        rep = rep.with_name(f"{rep.stem}_{TRUTH}.json")
    out["truth"] = f"{TRUTH} flood record"
    rep.write_text(json.dumps(out, indent=2))
    _print(out)
    print(f"\n  wrote {rep}  ({time.time()-t0:.0f}s)")
    return out


def _print(out: dict) -> None:
    r = out["results"]
    print("\n" + "=" * 76)
    print(f"Gate A — inside Arunachal, {TEST_FROM.date()} .. {out['truth_end']}, unseen by every model")
    for key, label in (("day_in_arunachal", "near here, each day"),
                       ("week_in_arunachal", "near here, next 7 days"),
                       ("state_day", "anywhere in Arunachal, each day"),
                       ("state_week", "anywhere in Arunachal, 7 days")):
        g = r[key]
        print(f"\n  {label}: {g['n']:,} forecasts, {g['n_with_flood']:,} with a flood")
        print(f"    A1 adds up          said {g['said_total']:,.1f} vs happened {g['happened_total']:,}"
              f"  (x{g['A1_said_over_happened']})  {'PASS' if g['A1_pass'] else 'FAIL'}")
        print(f"    A2 says what happens  {g['A2_ranges_judged']} ranges with >= {A2_MIN_POS} floods"
              f"  {'PASS' if g['A2_pass'] else 'FAIL'}")
        for b in g["reliability"]:
            flag = "" if b["n_with_flood"] >= A2_MIN_POS else "   (too few to judge)"
            print(f"        {b['range']:>12}  said {b['said_pct']:8.3f}%  happened "
                  f"{b['happened_pct']:8.3f}%  n={b['n']:>9,}  floods={b['n_with_flood']:>5,}{flag}")
        print(f"    A3 beats own season   Brier skill {g['A3_brier_skill_vs_own_season']:+.4f}"
              f"  {'PASS' if g['A3_pass'] else 'FAIL'}   (AUC {g['auc']}, timing AUC "
              f"{g['timing_auc_vs_own_season']})")
        if "info_brier_skill_vs_record_place_month" in g:
            print(f"       info: vs the record's own place-and-month rate "
                  f"{g['info_brier_skill_vs_record_place_month']:+.4f}")
    print(f"\n  week A1 across all 7 week phases: {r['week_in_arunachal_A1_all_phases']}")
    print(f"  day A1 by year: {r['day_in_arunachal_A1_by_year']}")
    print(f"  A4 consistency violations: {out['A4_consistency_violations']}")
    print(f"  region-wide context: day A1 x{r['day_region_wide']['A1_said_over_happened']}, "
          f"week A1 x{r['week_region_wide']['A1_said_over_happened']}, "
          f"day AUC {r['day_region_wide']['auc']}")
    w = r["what_people_see_week_in_arunachal"]
    print(f"  what people see (week, Arunachal): {w}")
    print(f"\n  GATE A: {'PASS' if out['GATE_A_PASS'] else 'FAIL'}")


# ── production ────────────────────────────────────────────────────────────
def fit() -> None:
    """Production curves on the production day model, fitted on 2024-01-01 ..
    TRUTH_END — the years its tree never learned from (tree TREE_FROM-2023)."""
    t0 = time.time()
    print("Flood chance NEAR HERE — production curves\n")
    with open(MODELS / "day_model.pkl", "rb") as fh:
        model = pickle.load(fh)
    E = np.load(MODELS / "exposure_km2.npy")
    od, F = live_archive_features()
    P = predict_day(model, F, E, soil_input(od))
    n = P.shape[1]
    ap = arunachal_cells(n) & np.isfinite(E)
    ev = clean_events()
    cur = fit_curves(P, od, ev, ap, np.isfinite(E), "2024-01-01", str(TRUTH_END.date()))
    check_summary = None
    rep = REPORT if TRUTH == "reported" else REPORT.with_name(f"{REPORT.stem}_{TRUTH}.json")
    if rep.exists():
        c = json.loads(rep.read_text())
        check_summary = {"GATE_A_PASS": c["GATE_A_PASS"], "gate": c["gate"], "report": str(rep.name),
                         "truth": f"{TRUTH} flood record"}

    # Confidence: flood days on record within RADIUS_KM, all record years.
    # Levels merged if Gate C′ said High did not measurably beat Medium.
    conf_f = ROOT / "reports" / "flood_near_here_confidence.json"
    conf = json.loads(conf_f.read_text()) if conf_f.exists() else {}
    keep3 = conf.get("keep_high_and_medium_separate")
    by_level = {k: v for k, v in conf.get("production_like_two_levels", {}).items() if k != "design"}
    cur["evidence_days"] = evidence(ev, TRUTH_END)
    lev = level_of(cur["evidence_days"])
    cur["level"] = lev if keep3 else np.where(lev == 2, 1, lev).astype(np.int8)
    cur["level_names"] = list(LEVEL_NAMES) if keep3 else ["Low", "Floods on record"]

    # What the screen must say about accuracy — measured, never typed: the
    # production-like test (curves re-fitted on the latest two years, as this
    # fit is) — every range with >= A2_MIN_POS floods, happened / said.
    measured = None
    diag_f = ROOT / "reports" / "flood_near_here_diagnosis.json"
    if diag_f.exists():
        g = json.loads(diag_f.read_text())["production_like"]["week_in_arunachal"]
        ratios = [b["happened_pct"] / b["said_pct"] for b in g["reliability"]
                  if b["n_with_flood"] >= A2_MIN_POS and b["said_pct"] > 0]
        measured = {"source": "production-like test, 2023-01-01..2025-10-31, weekly, inside "
                              "Arunachal (post-hoc: designed after Gate A failed)",
                    "happened_over_said_low": round(min(ratios), 2),
                    "happened_over_said_high": round(max(ratios), 2),
                    "said_over_happened_total": g["A1_said_over_happened"],
                    "ranking_auc": g["auc"]}
        # The low..high range above uses only ranges with >= A2_MIN_POS floods
        # (the rule as set). Since the tree moved to 2003 (2026-09-29) the high
        # ranges each hold fewer than that and said MORE than happened; a range
        # of ratios that are all above 1 would then read as "it always says too
        # little". So the screen is also told when that is so — measured, never
        # typed (docs/design/OLDER_FLOODS_TEST.md §5c).
        thin = [b for b in g["reliability"] if 0 < b["n_with_flood"] < A2_MIN_POS
                and b["said_pct"] >= 5 and b["said_pct"] > b["happened_pct"]]
        measured["high_ranges_said_more"] = (
            {"from_pct": min(float(b["range"].split("-")[0]) for b in thin),
             "floods": int(sum(b["n_with_flood"] for b in thin)),
             "said_pct": round(sum(b["said_pct"] * b["n"] for b in thin)
                               / sum(b["n"] for b in thin), 2),
             "happened_pct": round(sum(b["happened_pct"] * b["n"] for b in thin)
                                   / sum(b["n"] for b in thin), 2)}
            if thin else None)
    cur["meta"] = {
        "what": "flood chance within 10 km (day, 7 days) and anywhere in Arunachal (day, 7 days)",
        "truth": (f"the {TRUTH} flood record (build_verified_floods.py, PARKED §0x)"
                  if TRUTH == "verified" else
                  "news-reported flood; its Sentinel-1 screen filters out almost nothing "
                  "(PARKED §0w); channel-shift suspects removed"),
        "day_model": ("models/flood_forecast/day_model.pkl (production, unchanged; soil "
                      "wetness on flat cells since 2026-09-28, SOIL_WETNESS_TEST.md)"),
        "rain": "Open-Meteo archive scored as the live path scores live rain",
        "fit": cur["fit"], "radius_km": RADIUS_KM, "truth_end": str(TRUTH_END.date()),
        "held_out_test": check_summary,
        "status": ("APPROXIMATE — Gate A failed (level not stable between years); shown by the "
                   "user's decision of 2026-09-27 with the measured error stated"),
        "measured_error": measured,
        "confidence": {"evidence": f"distinct flood days on record within {RADIUS_KM:g} km, "
                                   f"{EVIDENCE_START.date()}..{TRUTH_END.date()}",
                       "levels": cur["level_names"],
                       "gate_c_prime_keep_three": keep3,
                       # production-like test, for the label text (post-hoc):
                       # how recorded floods compared with the forecast, by level
                       "measured_by_level": by_level},
        "fitted_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    CURVES.mkdir(parents=True, exist_ok=True)
    with open(CURVES / "curves.pkl", "wb") as fh:
        pickle.dump(cur, fh)
    (CURVES / "_meta.json").write_text(json.dumps(cur["meta"], indent=2))

    # sanity on the fit years (in-sample, so ~1 by construction) + a known day
    q = day_chance(P, cur)
    days = np.asarray((od >= pd.Timestamp("2024-01-01")) & (od <= TRUTH_END))
    Yn = truth_near(clean_events(), od)
    print(f"  fit: {cur['fit']}")
    print(f"  in Arunachal on the fit years: said {np.nansum(q[np.ix_(days, ap)]):.1f} "
          f"vs happened {int(Yn[np.ix_(days, ap)].sum())} place-days (in-sample)")
    for d in ("2024-06-30", "2024-01-15"):
        i = int(np.flatnonzero(od == pd.Timestamp(d))[0])
        r = apply(P[i:i + WEEK], cur)
        w = r["week"][ap]
        print(f"  week from {d}: Arunachal-wide {100*r['state_week']:.0f}%;  places: median "
              f"{100*np.nanmedian(w):.2f}%, top {100*np.nanmax(w):.1f}%")
    print(f"  wrote {CURVES}  ({time.time()-t0:.0f}s)")


# ── confidence: how much past-flood evidence is near a place ─────────────
# Gate C′ (FLOOD_SCREEN_PLAN.md, Phase 4, restated before grading): one
# count — distinct days with a flood record within RADIUS_KM since 2015
# (widened to every verified record, from 2003, on 2026-09-29: EVIDENCE_START).
HIGH_MIN_DAYS = 3
LEVEL_NAMES = ("Low", "Medium", "High")


def evidence(ev: pd.DataFrame, until: pd.Timestamp) -> np.ndarray:
    """Per rain cell: distinct days with a flood record within RADIUS_KM of
    its centre, EVIDENCE_START .. until."""
    lat, lon = when_grid.cell_centres()
    e = ev[(ev["date"] >= EVIDENCE_START) & (ev["date"] <= until)]
    days = [set() for _ in range(len(lat))]
    for la, lo, d in zip(e["lat"], e["lon"], e["date"]):
        dist = KM_PER_DEG * np.hypot(lat - la, (lon - lo) * np.cos(np.radians(la)))
        for k in np.flatnonzero(dist <= RADIUS_KM):
            days[k].add(d)
    return np.array([len(s) for s in days], np.int32)


def level_of(n_days: np.ndarray) -> np.ndarray:
    """0 Low (none on record), 1 Medium (1-2 days), 2 High (>= HIGH_MIN_DAYS)."""
    return np.where(n_days >= HIGH_MIN_DAYS, 2, np.where(n_days >= 1, 1, 0)).astype(np.int8)


def confidence() -> dict:
    """Gate C′: do the evidence levels separate how well the forecast did?
    Levels from records up to 2022 only. The test model is the shipped
    design (tree TREE_FROM-2020, calibration 2021-22) — check()'s until
    2026-09-29, when the tree moved to 2003 (OLDER_FLOODS_TEST.md)."""
    t0 = time.time()
    print("Flood chance NEAR HERE — confidence levels (Gate C′)\n")
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    ev = clean_events()
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    m, _ = fit_day_model(day_features(Wim, upstream=True), E, label_matrix(ev, wd, n),
                        yrs(wd, TREE_FROM, 2020), yrs(wd, 2021, 2022), wd)
    od, F = live_archive_features()
    P = m.predict(F, E, soil_input(od))
    ap = arunachal_cells(n) & np.isfinite(E)
    cur = fit_curves(P, od, ev, ap, np.isfinite(E), "2021-01-01", "2022-12-31")
    wk = week_series(day_chance(P, cur), cur["iso_week"])
    Yw = week_any(truth_near(ev, od, RADIUS_KM))
    lev = level_of(evidence(ev, pd.Timestamp("2022-12-31")))
    phase = np.asarray((od - TEST_FROM).days % WEEK)
    rows = np.flatnonzero(np.asarray((od >= TEST_FROM) & (od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END))
                          & (phase == 0))
    print(f"  test models ready ({time.time()-t0:.0f}s)")

    res = {}
    for L in (2, 1, 0):
        cc = np.flatnonzero(ap & (lev == L))
        p = wk[np.ix_(rows, cc)].ravel()
        y = Yw[np.ix_(rows, cc)].ravel().astype(np.float64)
        ok = np.isfinite(p)
        p, y = p[ok].astype(np.float64), y[ok]
        measurable = y.sum() >= A2_MIN_POS and y.sum() < len(y)
        ratio = float(p.sum() / y.sum()) if y.sum() > 0 else None
        res[LEVEL_NAMES[L]] = {
            "places": int(len(cc)), "place_weeks": int(len(y)), "weeks_with_a_flood": int(y.sum()),
            "said": round(float(p.sum()), 2),
            "said_over_happened": round(ratio, 3) if ratio else None,
            "auc": round(float(roc_auc_score(y, p)), 4) if measurable else None,
            "measurable": bool(measurable)}
    hi, me = res["High"], res["Medium"]
    keep_three = bool(hi["measurable"] and me["measurable"] and hi["auc"] > me["auc"]
                      and abs(np.log(hi["said_over_happened"])) < abs(np.log(me["said_over_happened"])))

    # The same split the way production works (post-hoc, for the label text,
    # not a gate): curves re-fitted each year on the latest two years, and a
    # place's evidence counted from records BEFORE the year it is graded on.
    Yw_all = Yw
    acc = {"on_record": [[], []], "none_on_record": [[], []]}
    for y in (2023, 2024, 2025):
        cur_y = fit_curves(P, od, ev, ap, np.isfinite(E), f"{y-2}-01-01", f"{y-1}-12-31")
        wk_y = week_series(day_chance(P, cur_y), cur_y["iso_week"])
        lv = evidence(ev, pd.Timestamp(f"{y-1}-12-31")) > 0
        r_y = np.flatnonzero(np.asarray((od.year == y) & (od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END))
                             & (phase == 0))
        for name, sel in (("on_record", ap & lv), ("none_on_record", ap & ~lv)):
            cc = np.flatnonzero(sel)
            acc[name][0].append(wk_y[np.ix_(r_y, cc)].ravel())
            acc[name][1].append(Yw_all[np.ix_(r_y, cc)].ravel())
    production_like = {}
    for name, (ps, ys) in acc.items():
        p = np.concatenate(ps).astype(np.float64)
        y = np.concatenate(ys).astype(np.float64)
        ok = np.isfinite(p)
        p, y = p[ok], y[ok]
        production_like[name] = {
            "place_weeks": int(len(y)), "weeks_with_a_flood": int(y.sum()),
            "said": round(float(p.sum()), 2),
            "happened_over_said": round(float(y.sum() / max(p.sum(), 1e-9)), 3),
            "auc": round(float(roc_auc_score(y, p)), 4) if 0 < y.sum() < len(y) else None}
    out = {"what": "Gate C′: evidence levels (flood days on record within 10 km, up to 2022) "
                   "vs how the weekly near-here chance did on 2023-01-01.." + str(TRUTH_END.date()),
           "levels": f"High >= {HIGH_MIN_DAYS} days, Medium 1-{HIGH_MIN_DAYS - 1}, Low 0",
           "by_level": res, "keep_high_and_medium_separate": keep_three,
           "production_like_two_levels": {
               "design": "post-hoc, for the label text: curves re-fitted yearly on the latest two "
                         "years; evidence counted from records before each graded year",
               **production_like}}
    (ROOT / "reports" / "flood_near_here_confidence.json").write_text(json.dumps(out, indent=2))
    for name, r in res.items():
        print(f"  {name:<7} {r['places']:>4} places  {r['place_weeks']:>7,} place-weeks  "
              f"{r['weeks_with_a_flood']:>4} with a flood  said {r['said']:>7.1f}  "
              f"(x{r['said_over_happened']})  AUC {r['auc']}")
    print(f"\n  keep High and Medium separate: {keep_three}")
    print("  production-like, two levels (post-hoc, for the label text):")
    for name, r in production_like.items():
        print(f"    {name:<15} {r['place_weeks']:>7,} place-weeks  {r['weeks_with_a_flood']:>4} with a flood"
              f"  said {r['said']:>7.1f}  happened/said x{r['happened_over_said']}  AUC {r['auc']}")
    print(f"  wrote reports/flood_near_here_confidence.json  ({time.time()-t0:.0f}s)")
    return out


def diagnose() -> dict:
    """Why did Gate A fail? Two questions, answered AFTER seeing the failure —
    so these are diagnostics, never a gate pass.

    1. Is the year-to-year drift in the flood record, or in the rain? Per
       year 2016-2025: forecast vs recorded near-here place-days inside
       Arunachal, with the test copy fed (a) the live-archive rain and (b)
       the satellite rain it was built on, each with curves fitted 2021-22.
    2. Would a production-like routine hold up? Re-fit the curves each year
       on the latest two complete years, forecast the next (2023 from
       2021-22, 2024 from 2022-23, 2025 from 2023-24), grade pooled."""
    t0 = time.time()
    print("Flood chance NEAR HERE — diagnosis of the Gate A result (post-hoc)\n")
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    ev = clean_events()
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    F_im = day_features(Wim, upstream=True)
    m, _ = fit_day_model(F_im, E, label_matrix(ev, wd, n), yrs(wd, TREE_FROM, 2020), yrs(wd, 2021, 2022), wd)
    od, F = live_archive_features()
    P_om = m.predict(F, E, soil_input(od))
    P_im = m.predict(F_im, E, soil_input(wd))
    ap = arunachal_cells(n) & np.isfinite(E)
    cells = np.isfinite(E)
    print(f"  models ready ({time.time()-t0:.0f}s)")

    def yearly(P, dates, cur):
        q = day_chance(P, cur)
        Y = truth_near(ev, dates, RADIUS_KM)
        out = {}
        for y in range(2016, 2026):
            rows = np.asarray((dates.year == y) & (dates <= TRUTH_END))
            if rows.any():
                s, h = float(np.nansum(q[np.ix_(rows, ap)])), int(Y[np.ix_(rows, ap)].sum())
                out[str(y)] = {"said": round(s, 1), "happened": h,
                               "happened_over_said": round(h / max(s, 1e-9), 2)}
        return out

    res = {}
    cur_om = fit_curves(P_om, od, ev, ap, cells, "2021-01-01", "2022-12-31")
    cur_im = fit_curves(P_im, wd, ev, ap, cells, "2021-01-01", "2022-12-31")
    res["by_year_live_archive_rain"] = yearly(P_om, od, cur_om)
    res["by_year_satellite_rain"] = yearly(P_im, wd, cur_im)
    recs = ev[ev["k"] >= 0]
    in_ap = ap[recs["k"].to_numpy()]
    res["records_per_year"] = {"arunachal": recs[in_ap].groupby(recs[in_ap]["date"].dt.year).size().to_dict(),
                               "whole_window": recs.groupby(recs["date"].dt.year).size().to_dict()}
    print(f"  per-year comparison done ({time.time()-t0:.0f}s)")

    # production-like: re-fit on the latest two complete years, forecast the next
    Yn = truth_near(ev, od, RADIUS_KM)
    Yw = week_any(Yn)
    phase = np.asarray((od - TEST_FROM).days % WEEK)
    mon = np.asarray(od.month) - 1
    base = np.asarray((od.year >= 2010) & (od.year <= 2014))
    parts = {"day": ([], [], []), "week": ([], [], [])}
    folds = {}
    for y in (2023, 2024, 2025):
        cur = fit_curves(P_om, od, ev, ap, cells, f"{y-2}-01-01", f"{y-1}-12-31")
        q = day_chance(P_om, cur)
        wk = week_series(q, cur["iso_week"])
        clim_d, clim_w = _month_table(q, od, base), _month_table(wk, od, base)
        rows_d = np.flatnonzero(np.asarray((od.year == y) & (od <= TRUTH_END)))
        rows_w = np.flatnonzero(np.asarray((od.year == y) & (od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END))
                                & (phase == 0))
        cc = np.flatnonzero(ap)
        for key, rows, val, clim, Y in (("day", rows_d, q, clim_d, Yn), ("week", rows_w, wk, clim_w, Yw)):
            parts[key][0].append(Y[np.ix_(rows, cc)].ravel())
            parts[key][1].append(val[np.ix_(rows, cc)].ravel())
            parts[key][2].append(clim[np.ix_(mon[rows], cc)].ravel())
        folds[str(y)] = {"curves_from": f"{y-2}-{y-1}",
                         "day_said": round(float(np.nansum(q[np.ix_(rows_d, cc)])), 1),
                         "day_happened": int(Yn[np.ix_(rows_d, cc)].sum())}
    res["production_like"] = {
        "design": "curves re-fitted each year on the latest two complete years; test copy of the "
                  f"day model (tree {TREE_FROM}-20) fed live-archive rain; post-hoc — NOT a gate pass",
        "folds": folds,
        "day_in_arunachal": grade(*(np.concatenate(x) for x in parts["day"]), None, DAY_EDGES),
        "week_in_arunachal": grade(*(np.concatenate(x) for x in parts["week"]), None, WEEK_EDGES)}
    out_path = ROOT / "reports" / "flood_near_here_diagnosis.json"
    out_path.write_text(json.dumps(res, indent=2))

    print("\n  forecast vs recorded near-here place-days inside Arunachal, curves fitted 2021-22")
    print(f"  {'year':<6}{'live-archive rain':>28}{'satellite rain':>28}{'records in AP':>16}")
    for y in range(2016, 2026):
        a = res["by_year_live_archive_rain"].get(str(y))
        b = res["by_year_satellite_rain"].get(str(y))
        r = res["records_per_year"]["arunachal"].get(y, 0)
        fa = f"{a['said']:>7.1f} vs {a['happened']:>4} (x{a['happened_over_said']:.2f})" if a else "-"
        fb = f"{b['said']:>7.1f} vs {b['happened']:>4} (x{b['happened_over_said']:.2f})" if b else "-"
        print(f"  {y:<6}{fa:>28}{fb:>28}{r:>16}")
    pl = res["production_like"]
    print("\n  production-like (post-hoc): re-fit on the latest two years, forecast the next")
    for y, f in pl["folds"].items():
        print(f"    {y} from {f['curves_from']}: said {f['day_said']} vs happened {f['day_happened']}")
    for key in ("day_in_arunachal", "week_in_arunachal"):
        g = pl[key]
        print(f"    {key}: A1 x{g['A1_said_over_happened']} ({'pass' if g['A1_pass'] else 'fail'}), "
              f"A2 {'pass' if g['A2_pass'] else 'fail'} on {g['A2_ranges_judged']} ranges, "
              f"A3 {g['A3_brier_skill_vs_own_season']:+.4f}, AUC {g['auc']}")
        for b in g["reliability"]:
            print(f"        {b['range']:>12}  said {b['said_pct']:8.3f}%  happened {b['happened_pct']:8.3f}%"
                  f"  floods={b['n_with_flood']:>4}")
    print(f"\n  wrote {out_path}  ({time.time()-t0:.0f}s)")
    return res


def confirmed() -> dict:
    """How does the forecast rank floods the validated radar test confirms,
    against all reported floods? Same held-out design as check() (models that
    never saw 2023-25); only the truth differs. Needs the re-check
    (scripts/fetch/radar_water_test.py recheck). Ranking only: the forecast is
    tuned to ALL reports, so its level is not meant for the confirmed subset."""
    t0 = time.time()
    sup = set(json.loads((ROOT / "reports" / "flood_radar_recheck.json").read_text())
              ["supported_uuids"])
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    ev = clean_events()
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    m, _ = fit_day_model(day_features(Wim, upstream=True), E, label_matrix(ev, wd, n),
                        yrs(wd, 2015, 2020), yrs(wd, 2021, 2022), wd)
    od, F = live_archive_features()
    P = m.predict(F, E, soil_input(od))
    ap = arunachal_cells(n) & np.isfinite(E)
    cur = fit_curves(P, od, ev, ap, np.isfinite(E), "2021-01-01", "2022-12-31")
    wk = week_series(day_chance(P, cur), cur["iso_week"])
    phase = np.asarray((od - TEST_FROM).days % WEEK)
    rows = np.flatnonzero(np.asarray((od >= TEST_FROM) & (od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END))
                          & (phase == 0))
    out = {"what": "weekly near-here ranking on 2023-01-01..2025-10-31, held-out models; truth "
                   "= all reported floods vs only radar-confirmed ones"}
    for name, e in (("all reported floods", ev), ("radar-confirmed only", ev[ev["uuid"].isin(sup)])):
        Yw = week_any(truth_near(e, od))
        for area, cells in (("Arunachal", ap), ("whole region", np.isfinite(E))):
            p = wk[np.ix_(rows, np.flatnonzero(cells))].ravel()
            y = Yw[np.ix_(rows, np.flatnonzero(cells))].ravel()
            ok = np.isfinite(p)
            out[f"{name} — {area}"] = {
                "records": int(len(e[e["date"].between(TEST_FROM, TRUTH_END)])),
                "place_weeks_with_a_flood": int(y[ok].sum()),
                "ranking_auc": round(float(roc_auc_score(y[ok], p[ok])), 4) if 0 < y[ok].sum() else None}
    (ROOT / "reports" / "flood_near_here_confirmed.json").write_text(json.dumps(out, indent=2))
    for k, v in out.items():
        print(f"  {k}: {v}")
    print(f"  ({time.time()-t0:.0f}s)")
    return out


def compare() -> dict:
    """Train on which record? The test day model (tree 2015-20, calibration
    2021-22) trained on the REPORTED record vs on the VERIFIED one, both
    graded on 2023-25 against the VERIFIED truth — weekly near-here ranking,
    and timing within each place (its chance vs its own seasonal level)."""
    global TRUTH
    t0 = time.time()
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    od, F = live_archive_features()
    ap = arunachal_cells(n) & np.isfinite(E)
    TRUTH = "verified"
    ev_v = clean_events()
    Yw = week_any(truth_near(ev_v, od))
    phase = np.asarray((od - TEST_FROM).days % WEEK)
    rows = np.flatnonzero(np.asarray((od >= TEST_FROM) & (od + pd.Timedelta(days=WEEK - 1) <= TRUTH_END))
                          & (phase == 0))
    base = np.asarray((od.year >= 2010) & (od.year <= 2014))
    mon = np.asarray(od.month) - 1
    out = {"what": "weekly near-here chance, 2023-01-01..2025-10-31, graded against the "
                   "VERIFIED record; the test day model trained on each record"}
    for trained_on in ("reported", "verified"):
        TRUTH = trained_on
        ev = clean_events()
        m, _ = fit_day_model(day_features(Wim, upstream=True), E, label_matrix(ev, wd, n),
                            yrs(wd, 2015, 2020), yrs(wd, 2021, 2022), wd)
        P = m.predict(F, E, soil_input(od))
        cur = fit_curves(P, od, ev, ap, np.isfinite(E), "2021-01-01", "2022-12-31")
        wk = week_series(day_chance(P, cur), cur["iso_week"])
        clim = _month_table(wk, od, base)
        res = {}
        for area, cells in (("Arunachal", ap), ("whole region", np.isfinite(E))):
            cc = np.flatnonzero(cells)
            p = wk[np.ix_(rows, cc)].ravel()
            c = clim[np.ix_(mon[rows], cc)].ravel()
            y = Yw[np.ix_(rows, cc)].ravel()
            ok = np.isfinite(p) & np.isfinite(c)
            res[area] = {"floods": int(y[ok].sum()),
                         "ranking_auc": round(float(roc_auc_score(y[ok], p[ok])), 4),
                         "timing_auc": round(float(roc_auc_score(y[ok], p[ok] / np.maximum(c[ok], 1e-9))), 4)}
        out[f"trained on the {trained_on} record"] = res
        print(f"  trained on {trained_on}: {res}  ({time.time()-t0:.0f}s)", flush=True)
    TRUTH = "reported"
    (ROOT / "reports" / "flood_near_here_train_on_which.json").write_text(json.dumps(out, indent=2))
    return out


def load_curves() -> dict | None:
    f = CURVES / "curves.pkl"
    if not f.exists():
        return None
    with open(f, "rb") as fh:
        return pickle.load(fh)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if "--truth" in sys.argv:
        TRUTH = sys.argv[sys.argv.index("--truth") + 1]
    if "--radius" in sys.argv:
        # the one pre-registered alternative is 20 km (FLOOD_SCREEN_PLAN.md, Phase 2)
        RADIUS_KM = float(sys.argv[sys.argv.index("--radius") + 1])
    {"fit": fit, "diagnose": diagnose, "confidence": confidence,
     "confirmed": confirmed, "compare": compare}.get(cmd, check)()
