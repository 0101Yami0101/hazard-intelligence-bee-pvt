"""Grade the flood chance near a place by how far ahead it looks (days 1-7).

    python scripts/model/check_lead_days.py

Writes  reports/flood_lead_day_check.json

Every earlier test fed the model the rain that fell. The screen feeds it
FORECAST rain. This replays, for each day of 2024-25 and each lead L = 0..6,
the rain the live run would have been handed L days before, and grades the
day chance near each place inside Arunachal. Method and the reading of the
result were fixed before the data was fetched: docs/design/LEAD_DAY_TEST.md.

A forecast issued on I = D - L, for target day D:
    days before I     what fell, as the service records it        (source 0)
    day d in I..D     the forecast for d made d - I days earlier  (source d - I)
The service's "previous_dayN" for a day is the forecast made N days before
it, so the source for day d = D - j is N = L - j when j <= L, else 0.

The model, the curves and the grading are near_here.diagnose's
"production-like" test, unchanged: nothing that makes a number has seen the
year it is graded on. Reads only; nothing live is written.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT_ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_ / "scripts"), str(ROOT_ / "scripts" / "build"),
                str(ROOT_ / "scripts" / "model"), str(ROOT_ / "webapp")]

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import flood_forecast_live as ffl
import near_here as NH
import when_grid
from common import INTERIM, ROOT
from flood_forecast import (TREE_FROM, TRUTH_END, day_features, fit_day_model, label_matrix,
                            soil_input)

PREV = INTERIM / "rainfall_om_prev"
OUT = ROOT / "reports" / "flood_lead_day_check.json"
LEADS = range(7)                     # 0 = today on the screen ... 6 = its seventh day
NEAR, FAR = (0, 1, 2), (3, 4, 5, 6)  # the solid days and the dashed days
WORSE_BY, OVER, UNDER, MIN_FLOODS = 0.02, 1.5, 2 / 3, 20     # LEAD_DAY_TEST.md §1
N_BOOT = 200


def load_prev() -> tuple[pd.DatetimeIndex, np.ndarray]:
    f = PREV / "prev_mm.npy"
    if f.exists():
        return pd.to_datetime(np.load(PREV / "dates.npy", allow_pickle=True)), np.load(f)
    parts = sorted((PREV / "_months").glob("*.npz"))            # a run still in progress
    z = [np.load(p) for p in parts]
    mm = np.concatenate([x["mm"] for x in z], axis=1)
    return pd.date_range(str(z[0]["start"]), str(z[-1]["end"]), freq="D"), mm


def shifted(a: np.ndarray, j: int) -> np.ndarray:
    """Row t holds a[t - j]; the first j rows are unknown."""
    if j == 0:
        return a
    out = np.full_like(a, np.nan)
    out[j:] = a[:-j]
    return out


def lead_features(cell: np.ndarray, up: np.ndarray, L: int, S: dict, panel) -> list[np.ndarray]:
    """The day model's three rain inputs for every target day, as the live run
    would have built them L days earlier. `cell`, `up`: (sources, days, cells)
    rain at the place and upstream. Mirrors flood_forecast_live.features."""
    def win(src, j):                       # the rain of day D - j as known at issue
        return shifted(src[L - j if j <= L else 0], j).astype(np.float64)

    def tot(parts):
        # ⚠️ Added in float64, then stored as float32 — as rolling_totals does.
        # Added in float32, a total lands 0.0001 mm off, the 1%-step
        # percentile lookup flips a step on tied values, and the day model's
        # trees turn that into differences of up to 0.18 (caught by the
        # L = 0 check below on the first run).
        return sum(parts).astype(np.float32)
    v = [win(cell, j) for j in range(8)]
    u = [win(up, j) for j in range(7)]
    r3p, r7p = ffl._pct(tot(v[:3]), S["r3"]), ffl._pct(tot(v[:7]), S["r7"])
    rule = (r3p + r7p) / 2
    lag = (ffl._pct(tot(v[1:4]), S["r3"]) + ffl._pct(tot(v[1:8]), S["r7"])) / 2
    X = pd.DataFrame({"r3": r3p.ravel(), "r7": r7p.ravel(), "trigger_lag1": lag.ravel()})
    ok = X[["r3", "r7"]].notna().all(axis=1).to_numpy()        # as the live function
    when = np.full(len(X), np.nan, dtype=np.float32)
    b, c = panel
    when[ok] = (rule.ravel()[ok] + b.predict_proba(X[ok])[:, 1] + c.predict_proba(X[ok])[:, 1]) / 3
    return [when.reshape(rule.shape), ffl._pct(tot(u[:3]), S["up_r3"]), ffl._pct(tot(u), S["up_r7"])]


def main() -> dict:
    t0 = time.time()
    print("Flood chance near here, graded by lead day (LEAD_DAY_TEST.md)\n")
    pd_, prev = load_prev()
    S = dict(np.load(ffl.LIVE / "scales.npz"))
    nn = S.pop("nn")
    Wn, panel = ffl._upstream_matrix(), ffl._when_panel()
    cell = prev[:, :, nn]                                        # (sources, days, cells)
    whole = np.isfinite(prev).all(axis=2)                        # (sources, days): a day all points have
    up = np.nan_to_num(cell) @ np.nan_to_num(Wn).T
    up[:, :, ~np.isfinite(Wn).all(axis=1)] = np.nan
    for k in range(prev.shape[0]):
        up[k, ~whole[k]] = np.nan
        cell[k, ~whole[k]] = np.nan
    print(f"  rain: {pd_[0].date()} .. {pd_[-1].date()}, complete days by source {whole.sum(axis=1).tolist()}")

    # the machinery, checked against the live function: with no forecast in it
    # (L = 0) it must give exactly what flood_forecast_live.features gives
    ref = ffl.features(cell[0], S, Wn, panel)
    mine = lead_features(cell, up, 0, S, panel)
    same = [float(np.nanmax(np.abs(a - b))) for a, b in zip(ref, mine)]
    both = [bool((np.isfinite(a) == np.isfinite(b)).all()) for a, b in zip(ref, mine)]
    print(f"  L = 0 against the live function: largest difference {max(same):.2e}, same gaps {all(both)}")
    assert max(same) < 1e-5 and all(both), "the replay does not reproduce the live features"

    # the test copy of the model, as near_here.diagnose builds it
    wd, Wim = when_grid.load()
    Wim = np.asarray(Wim)
    n = Wim.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    ev = NH.clean_events()
    yrs = lambda d, a, b: np.asarray((d.year >= a) & (d.year <= b))
    m, _ = fit_day_model(day_features(Wim, upstream=True), E, label_matrix(ev, wd, n),
                         yrs(wd, TREE_FROM, 2020), yrs(wd, 2021, 2022), wd)
    od, F_arch = NH.live_archive_features()
    P_om = m.predict(F_arch, E, soil_input(od))
    ap = NH.arunachal_cells(n) & np.isfinite(E)
    cells = np.isfinite(E)
    cc = np.flatnonzero(ap)
    print(f"  model ready ({time.time() - t0:.0f}s); {len(cc)} places inside Arunachal")

    soil = soil_input(pd_)
    P = {L: m.predict(lead_features(cell, up, L, S, panel), E, soil) for L in LEADS}
    Yn = NH.truth_near(ev, pd_, NH.RADIUS_KM)
    q = {L: np.full(P[L].shape, np.nan, np.float32) for L in LEADS}
    q_arch = np.full(P[0].shape, np.nan, np.float32)
    arch_row = pd.Series(np.arange(len(od)), index=od).reindex(pd_)
    for y in sorted(set(pd_.year)):
        cur = NH.fit_curves(P_om, od, ev, ap, cells, f"{y - 2}-01-01", f"{y - 1}-12-31")
        rows = np.flatnonzero(np.asarray(pd_.year == y))
        for L in LEADS:
            q[L][rows] = NH.day_chance(P[L][rows], cur)
        ar = arch_row.iloc[rows]
        has = ar.notna().to_numpy()
        q_arch[rows[has]] = NH.day_chance(P_om[ar[has].astype(int).to_numpy()], cur)

    # the same days for every lead: all seven have a chance, and the truth exists
    good = np.asarray(pd_ <= TRUTH_END)
    for L in LEADS:
        good &= np.isfinite(q[L][:, cc]).all(axis=1)
    good &= np.isfinite(q_arch[:, cc]).all(axis=1)
    rows = np.flatnonzero(good)
    y = Yn[np.ix_(rows, cc)].astype(np.float64)
    n_fl = int(y.sum())
    print(f"  graded: {len(rows)} days, {pd_[rows[0]].date()} .. {pd_[rows[-1]].date()}; "
          f"{n_fl} place-days with a flood, on {int((y.sum(axis=1) > 0).sum())} days\n")

    def score(Q):
        v = Q[np.ix_(rows, cc)].astype(np.float64)
        return {"ranking_auc": round(float(roc_auc_score(y.ravel(), v.ravel())), 4),
                "said": round(float(v.sum()), 2), "happened": n_fl,
                "said_over_happened": round(float(v.sum()) / max(n_fl, 1), 3)}

    res = {"what": "day chance of a flood within 10 km, inside Arunachal, by how many days ahead "
                   "the rain was forecast (0 = the screen's today, 6 = its seventh day)",
           "method": "docs/design/LEAD_DAY_TEST.md §1 (fixed before the data was fetched)",
           "window": [str(pd_[rows[0]].date()), str(pd_[rows[-1]].date())], "days": int(len(rows)),
           "places": int(len(cc)), "place_days_with_a_flood": n_fl,
           "days_with_a_flood": int((y.sum(axis=1) > 0).sum()),
           "by_year": {str(yr): int(y[np.asarray(pd_[rows].year == yr)].sum())
                       for yr in sorted(set(pd_[rows].year))},
           "replay_reproduces_live_features": {"largest_difference": max(same), "same_gaps": all(both)},
           "rain_that_fell": score(q_arch),
           "by_lead": {str(L): score(q[L]) for L in LEADS}}
    print(f"  {'lead':<22}{'ranking':>9}{'forecast':>10}{'recorded':>10}{'forecast/recorded':>19}")
    a = res["rain_that_fell"]
    print(f"  {'rain that fell':<22}{a['ranking_auc']:>9}{a['said']:>10}{a['happened']:>10}{a['said_over_happened']:>19}")
    for L in LEADS:
        a = res["by_lead"][str(L)]
        print(f"  {'day ' + str(L + 1) + (' (today)' if L == 0 else ''):<22}{a['ranking_auc']:>9}{a['said']:>10}"
              f"{a['happened']:>10}{a['said_over_happened']:>19}")

    auc = lambda Ls: float(np.mean([res["by_lead"][str(L)]["ranking_auc"] for L in Ls]))
    rat = lambda Ls: float(np.mean([res["by_lead"][str(L)]["said_over_happened"] for L in Ls]))
    d_auc, r_rat = auc(FAR) - auc(NEAR), rat(FAR) / max(rat(NEAR), 1e-9)

    # how sure: whole days drawn again with replacement (floods cluster in days)
    rng = np.random.default_rng(0)
    V = {L: q[L][np.ix_(rows, cc)].astype(np.float64) for L in LEADS}
    boot_d, boot_r = [], []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(rows), len(rows))
        yy = y[i].ravel()
        if yy.sum() < 2:
            continue
        au = {L: roc_auc_score(yy, V[L][i].ravel()) for L in LEADS}
        sa = {L: V[L][i].sum() / yy.sum() for L in LEADS}
        boot_d.append(np.mean([au[L] for L in FAR]) - np.mean([au[L] for L in NEAR]))
        boot_r.append(np.mean([sa[L] for L in FAR]) / np.mean([sa[L] for L in NEAR]))
    ci = lambda b: [round(float(x), 3) for x in np.quantile(b, [0.05, 0.95])]

    enough = n_fl >= MIN_FLOODS
    res["reading"] = {
        "days_1_3_ranking": round(auc(NEAR), 4), "days_4_7_ranking": round(auc(FAR), 4),
        "ranking_difference": round(d_auc, 4), "ranking_difference_90pct_range": ci(boot_d),
        "days_1_3_forecast_over_recorded": round(rat(NEAR), 3),
        "days_4_7_forecast_over_recorded": round(rat(FAR), 3),
        "level_ratio_far_over_near": round(r_rat, 3), "level_ratio_90pct_range": ci(boot_r),
        "enough_floods_to_say": bool(enough),
        "days_4_7_measurably_worse": bool(enough and d_auc < -WORSE_BY),
        "days_4_7_over_promise": bool(enough and r_rat > OVER),
        "days_4_7_under_promise": bool(enough and r_rat < UNDER),
        "rules": {"worse_if_ranking_lower_by_more_than": WORSE_BY, "over_promise_if_ratio_above": OVER,
                  "under_promise_if_ratio_below": round(UNDER, 3), "need_at_least_flood_place_days": MIN_FLOODS}}
    r = res["reading"]
    print(f"\n  days 1-3 ranking {r['days_1_3_ranking']}, days 4-7 {r['days_4_7_ranking']}: "
          f"difference {r['ranking_difference']:+} (9 in 10 redraws: {r['ranking_difference_90pct_range']})")
    print(f"  forecast/recorded: days 1-3 {r['days_1_3_forecast_over_recorded']}, days 4-7 "
          f"{r['days_4_7_forecast_over_recorded']}: ratio {r['level_ratio_far_over_near']} "
          f"(9 in 10 redraws: {r['level_ratio_90pct_range']})")
    print(f"  enough floods to say: {r['enough_floods_to_say']} | measurably worse: "
          f"{r['days_4_7_measurably_worse']} | over-promise: {r['days_4_7_over_promise']} | "
          f"under-promise: {r['days_4_7_under_promise']}")
    OUT.write_text(json.dumps(res, indent=2))
    print(f"\n  wrote {OUT}  ({time.time() - t0:.0f}s)")
    return res


if __name__ == "__main__":
    main()
