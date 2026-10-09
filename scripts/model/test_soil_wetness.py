"""Do soil wetness or long rain improve the flood and landslide forecasts?
The pre-registered test in docs/design/SOIL_WETNESS_TEST.md — gates, inputs
and protocol are fixed there; this script only carries them out.

    python scripts/model/test_soil_wetness.py            # all three parts
    python scripts/model/test_soil_wetness.py flood      # or: slide | arc
    python scripts/model/test_soil_wetness.py flat       # §7 follow-up
    python scripts/model/test_soil_wetness.py stale      # §8 live-delay check

Needs   data/interim/soil_wetness/era5land_lattice.npz, era5land_arc_events.npz
        (scripts/fetch/fetch_39_era5land_soil.py)
Writes  reports/soil_wetness_test.json   (each part updates its own key)

Candidates, the same four in every part:
    baseline     what ships today
    +soil        + soil wetness of the top metre on day t-3, own-cell percentile
    +long rain   + 15- and 30-day rain percentiles
    +both        + soil + long rain

Soil wetness is taken on the day before the 3-day rain window, so it says how
wet the ground was BEFORE the storm — not the storm's own effect on it.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import rasterio
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

import when_grid
from common import INTERIM, ROOT

SOIL = INTERIM / "soil_wetness"
RAIN = INTERIM / "rainfall"
FEAT = RAIN / "features"
REPORT = ROOT / "reports" / "soil_wetness_test.json"
LAG = 3                                  # soil on day t-3
DEPTH_W = (7.0, 21.0, 72.0)              # cm in layers 0-7, 7-28, 28-100
MONSOON = (5, 10)
N_BOOT = 2000
SEED = 0
CI = (0.0085, 0.9915)                    # 98.3%: 95% split over 3 candidates
CANDIDATES = ("+soil", "+long rain", "+both")
CONTROL_WINDOW = 15                      # +/- calendar days, landslide L-time
CONTROL_LAST_YEAR = 2025
GATES = {"flood_gain_min": 0.010, "flood_arunachal_min": -0.005,
         "slide_gain_min": 0.02, "slide_prod_min": -0.01}


# ── shared helpers ───────────────────────────────────────────────────────
def soil_index(z) -> np.ndarray:
    a, b, c = DEPTH_W
    return ((a * z["swv1"] + b * z["swv2"] + c * z["swv3"]) / (a + b + c)).astype(np.float32)


def lag(a: np.ndarray, n: int) -> np.ndarray:
    out = np.full_like(a, np.nan)
    out[n:] = a[:-n]
    return out


def monsoon_pct(a: np.ndarray, dates: pd.DatetimeIndex) -> np.ndarray:
    """Each cell's own May-Oct percentile, share of history strictly below
    (searchsorted 'left') — when_grid.percentile_features' convention."""
    mons = np.asarray((dates.month >= MONSOON[0]) & (dates.month <= MONSOON[1]))
    pct = np.full(a.shape, np.nan, dtype=np.float32)
    for k in range(a.shape[1]):
        col = a[:, k]
        clim = np.sort(col[mons & np.isfinite(col)])
        if len(clim) == 0:
            continue
        fin = np.isfinite(col)
        pct[fin, k] = np.searchsorted(clim, col[fin], side="left") / len(clim)
    return pct


def align(src_dates: pd.DatetimeIndex, a: np.ndarray, dst: pd.DatetimeIndex) -> np.ndarray:
    pos = pd.Series(np.arange(len(src_dates)), index=src_dates).reindex(dst)
    out = np.full((len(dst), a.shape[1]), np.nan, dtype=np.float32)
    ok = pos.notna().to_numpy()
    out[ok] = a[pos[ok].astype(int).to_numpy()]
    return out


def placements(pos: np.ndarray, neg: np.ndarray) -> np.ndarray:
    """Each positive's share of negatives below it, ties half. Their mean is
    the AUC, so resampling positives resamples the AUC."""
    s = np.sort(neg)
    lo = np.searchsorted(s, pos, side="left")
    hi = np.searchsorted(s, pos, side="right")
    return (lo + 0.5 * (hi - lo)) / len(s)


def boot_gain(u_c: np.ndarray, u_b: np.ndarray, groups: np.ndarray, ci=CI) -> dict:
    """Paired bootstrap of mean(u_c - u_b), resampling whole groups (dates)."""
    d = u_c - u_b
    g_ids, g_inv = np.unique(groups, return_inverse=True)
    g_sum = np.bincount(g_inv, weights=d)
    g_n = np.bincount(g_inv)
    rng = np.random.default_rng(SEED)
    idx = rng.integers(0, len(g_ids), size=(N_BOOT, len(g_ids)))
    gains = g_sum[idx].sum(axis=1) / g_n[idx].sum(axis=1)
    lo, hi = np.quantile(gains, ci)
    key = f"ci{round(100 * (ci[1] - ci[0]), 1):g}".replace(".", "")
    return {"gain": float(d.mean()), key: [float(lo), float(hi)],
            "n_groups": int(len(g_ids))}


def save(part: str, res: dict) -> None:
    rep = json.loads(REPORT.read_text()) if REPORT.exists() else {}
    rep["protocol"] = "docs/design/SOIL_WETNESS_TEST.md"
    rep["gates"] = GATES
    rep[part] = res
    REPORT.write_text(json.dumps(rep, indent=2))
    print(f"  wrote {REPORT.relative_to(ROOT)} [{part}]")


# ── 3. flood day model ───────────────────────────────────────────────────
def _flood_inputs(t0: float, soil_lag: int = LAG) -> tuple:
    from flood_forecast import exposure, imerg_index_full, label_matrix, training_events
    from predict_flood_where import score_grid
    from replay_flood_forecast import REPLAY_WHERE
    dates, W = when_grid.load()
    W = np.asarray(W)
    n_cells = W.shape[1]
    kidx = imerg_index_full()
    H, _ = score_grid(REPLAY_WHERE, clip_to_state=False, verbose=False)
    E = exposure(H, kidx, n_cells)
    ev = training_events()
    Y = label_matrix(ev, dates, n_cells)
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        instate = m.read(1).astype(bool)
    frac_in = (np.bincount(kidx[instate & (kidx >= 0)], minlength=n_cells)
               / np.maximum(np.bincount(kidx[kidx >= 0], minlength=n_cells), 1))
    cell_in_state = frac_in > 0.5

    rdates = pd.to_datetime(np.load(RAIN / "dates.npy").astype("datetime64[D]"))
    r15 = align(rdates, monsoon_pct(np.load(FEAT / "r15.npy"), rdates), dates)
    r30 = align(rdates, monsoon_pct(np.load(FEAT / "r30.npy"), rdates), dates)
    z = np.load(SOIL / "era5land_lattice.npz")
    sdates = pd.to_datetime(z["dates"])
    soil = align(sdates, lag(monsoon_pct(soil_index(z), sdates), soil_lag), dates)
    print(f"  inputs ready ({time.time()-t0:.0f}s)", flush=True)
    return dates, W, n_cells, kidx, E, Y, cell_in_state, r15, r30, soil


def flood() -> dict:
    from flood_forecast import TRUTH_END, DayModel, day_features, years
    from replay_flood_forecast import TEST_FROM
    t0 = time.time()
    print("FLOOD - day model, tree 2015-2020, calibration 2021-22, "
          f"test {TEST_FROM.date()}..{TRUTH_END.date()}, verified record")
    dates, W, n_cells, kidx, E, Y, cell_in_state, r15, r30, soil = _flood_inputs(t0)

    base = day_features(W, upstream=True)
    runs = {"baseline": base, "+soil": base + [soil], "+long rain": base + [r15, r30],
            "+both": base + [soil, r15, r30]}
    test = np.asarray((dates >= TEST_FROM) & (dates <= TRUTH_END))
    cells = np.isfinite(E)
    Yt = Y[test][:, cells]
    ratios, fits = {}, {}
    for name, F in runs.items():
        model, info = DayModel.fit(F, E, Y, years(dates, 2015, 2020), years(dates, 2021, 2022))
        P = model.predict(F, E)
        normal = np.nanmean(P[years(dates, 2015, 2022)], axis=0)
        ratios[name] = P[test][:, cells] / normal[cells][None, :]
        fits[name] = info
        print(f"  {name:<11} fitted {info}  ({time.time()-t0:.0f}s)", flush=True)

    common = np.logical_and.reduce([np.isfinite(r) for r in ratios.values()])
    inst = np.broadcast_to(cell_in_state[cells][None, :], Yt.shape)
    day_of = np.broadcast_to(np.flatnonzero(test)[:, None], Yt.shape)
    def area_scores(amask):
        y = Yt[amask]
        pos = y == 1
        grp = day_of[amask][pos]
        u = {n: placements(r[amask][pos], r[amask][~pos]) for n, r in ratios.items()}
        return {"n_floods": int(pos.sum()), "n_flood_days": int(len(np.unique(grp))),
                "timing_auc": {n: float(v.mean()) for n, v in u.items()},
                "gain": {c: boot_gain(u[c], u["baseline"], grp) for c in CANDIDATES}}

    out = {"n_test_cell_days": int(common.sum()), "fits": fits, "areas": {}}
    for area, amask in (("region", common), ("arunachal", common & inst)):
        a = area_scores(amask)
        # sanity: the placement mean IS the AUC
        a["check_auc_baseline"] = float(roc_auc_score(Yt[amask], ratios["baseline"][amask]))
        out["areas"][area] = a
    # Where does a gain come from? Added after the gated result was seen, so
    # it explains the verdict and cannot change it.
    from flood_forecast import SLOPE_CLASS_NAMES, terrain_class
    cls = np.broadcast_to(terrain_class(kidx, n_cells)[cells][None, :], Yt.shape)
    diag_areas = {"outside Arunachal": common & ~inst}
    for j, nm in enumerate(SLOPE_CLASS_NAMES):
        diag_areas[nm] = common & (cls == j)
        diag_areas[f"{nm}, in Arunachal"] = common & (cls == j) & inst
    out["diagnostic_areas_posthoc"] = {k: area_scores(m) for k, m in diag_areas.items()
                                       if (Yt[m] == 1).sum() >= 10}

    verdict = {}
    for c in CANDIDATES:
        g = out["areas"]["region"]["gain"][c]
        ga = out["areas"]["arunachal"]["gain"][c]
        f1 = g["gain"] >= GATES["flood_gain_min"]
        f2 = g["ci983"][0] > 0
        f3 = ga["gain"] >= GATES["flood_arunachal_min"]
        verdict[c] = {"F1": bool(f1), "F2": bool(f2), "F3": bool(f3), "pass": bool(f1 and f2 and f3)}
    out["verdict"] = verdict

    # diagnostics (not deciding)
    mons = np.asarray((dates.month >= 5) & (dates.month <= 10))[test]
    diag = {}
    for n, a in (("soil", soil), ("r15", r15), ("r30", r30), ("local WHEN", W)):
        at = a[test][:, cells]
        ok = common & np.isfinite(at)
        diag[f"{n}_alone_auc"] = float(roc_auc_score(Yt[ok], at[ok]))
    sm, rm = soil[test][:, cells][mons], r30[test][:, cells][mons]
    ok = np.isfinite(sm) & np.isfinite(rm)
    diag["spearman_soil_vs_r30_monsoon"] = float(spearmanr(sm[ok][::50], rm[ok][::50])[0])
    out["diagnostics"] = diag
    _print_flood(out)
    return out


def _print_flood(o: dict) -> None:
    for area, a in o["areas"].items():
        print(f"\n  {area}: {a['n_floods']} floods on {a['n_flood_days']} days")
        print(f"    baseline timing AUC {a['timing_auc']['baseline']:.4f} "
              f"(check {a['check_auc_baseline']:.4f})")
        for c in CANDIDATES:
            g = a["gain"][c]
            print(f"    {c:<11} {a['timing_auc'][c]:.4f}  gain {g['gain']:+.4f}  "
                  f"98.3% [{g['ci983'][0]:+.4f}, {g['ci983'][1]:+.4f}]")
    print("\n  verdict:", {c: v["pass"] for c, v in o["verdict"].items()})
    print("  diagnostics:", {k: round(v, 3) for k, v in o["diagnostics"].items()})
    print("\n  post-hoc breakdown (explains, does not decide):")
    for area, a in o["diagnostic_areas_posthoc"].items():
        g = "  ".join(f"{c} {a['gain'][c]['gain']:+.3f} [{a['gain'][c]['ci983'][0]:+.3f},"
                      f"{a['gain'][c]['ci983'][1]:+.3f}]" for c in CANDIDATES)
        print(f"    {area:<32} {a['n_floods']:>4} floods  base {a['timing_auc']['baseline']:.3f}  {g}")


# ── 7. follow-up: flat ground only ───────────────────────────────────────
FLAT_CANDIDATES = ("flat +soil", "flat +long rain")
FLAT_CI = (0.0125, 0.9875)               # 97.5%: 95% split over 2 candidates
FLAT_MIN_FLOODS_AP = 30


STALE_LAG = 16                           # §8: latest day + 7-day lead + 9-day latency
STALE_CI = (0.025, 0.975)                # one candidate


def _flat_run(soil_lag: int, cands: tuple, ci: tuple, title: str) -> dict:
    """Fit on 2019-2025, test on 2015-2018; flat cells take the candidate
    model's chance, every other cell keeps the baseline's."""
    from flood_forecast import TRUTH_END, DayModel, day_features, terrain_class, years
    t0 = time.time()
    print(f"{title}; tree 2019-2023, calibration 2024..{TRUTH_END.date()}, "
          f"test 2015-2018, verified record, soil on day t-{soil_lag}")
    dates, W, n_cells, kidx, E, Y, cell_in_state, r15, r30, soil = _flood_inputs(t0, soil_lag)
    base = day_features(W, upstream=True)
    rec = np.asarray(dates <= TRUTH_END)
    test = years(dates, 2015, 2018)
    cells = np.isfinite(E)
    flat_c = (terrain_class(kidx, n_cells) == 0)[cells]
    Yt = Y[test][:, cells]
    models = {"baseline": base, "+soil": base + [soil], "+long rain": base + [r15, r30]}
    models = {n: F for n, F in models.items() if n == "baseline" or f"flat {n}" in cands}
    ratio, fits = {}, {}
    for name, F in models.items():
        model, info = DayModel.fit(F, E, Y, years(dates, 2019, 2023), years(dates, 2024, 2025) & rec)
        P = model.predict(F, E)
        normal = np.nanmean(P[years(dates, 2019, 2025) & rec], axis=0)
        ratio[name] = P[test][:, cells] / normal[cells][None, :]
        fits[name] = info
        print(f"  {name:<11} fitted {info}  ({time.time()-t0:.0f}s)", flush=True)
    fl = flat_c[None, :]
    runs = {"baseline": ratio["baseline"],
            **{c: np.where(fl, ratio[c[len("flat "):]], ratio["baseline"]) for c in cands}}

    common = np.logical_and.reduce([np.isfinite(r) for r in runs.values()])
    inst = np.broadcast_to(cell_in_state[cells][None, :], Yt.shape)
    flat_m = np.broadcast_to(fl, Yt.shape)
    day_of = np.broadcast_to(np.flatnonzero(test)[:, None], Yt.shape)
    out = {"soil_lag_days": soil_lag, "n_test_cell_days": int(common.sum()), "fits": fits,
           "areas": {}}
    for area, amask in (("flat", common & flat_m), ("region", common),
                        ("arunachal", common & inst), ("flat, in Arunachal", common & flat_m & inst)):
        y = Yt[amask]
        pos = y == 1
        grp = day_of[amask][pos]
        u = {n: placements(r[amask][pos], r[amask][~pos]) for n, r in runs.items()}
        out["areas"][area] = {
            "n_floods": int(pos.sum()), "n_flood_days": int(len(np.unique(grp))),
            "timing_auc": {n: float(v.mean()) for n, v in u.items()},
            "gain": {c: boot_gain(u[c], u["baseline"], grp, ci) for c in cands}}
    for area, a in out["areas"].items():
        print(f"\n  {area}: {a['n_floods']} floods on {a['n_flood_days']} days, "
              f"baseline {a['timing_auc']['baseline']:.4f}")
        for c in cands:
            g = a["gain"][c]
            lo, hi = [v for k, v in g.items() if k.startswith("ci")][0]
            print(f"    {c:<16} {a['timing_auc'][c]:.4f}  gain {g['gain']:+.4f}  "
                  f"[{lo:+.4f}, {hi:+.4f}]")
    return out


def flat() -> dict:
    """§7: the §6b pattern re-tested on years no soil run had looked at."""
    out = _flat_run(LAG, FLAT_CANDIDATES, FLAT_CI, "FLOOD FOLLOW-UP (§7) - flat cells only")
    A = out["areas"]
    gate_ap_flat = A["flat, in Arunachal"]["n_floods"] >= FLAT_MIN_FLOODS_AP
    verdict = {}
    for c in FLAT_CANDIDATES:
        g1 = (A["flat"]["gain"][c]["gain"] >= GATES["flood_gain_min"]
              and A["flat"]["gain"][c]["ci975"][0] > 0)
        g2 = A["region"]["gain"][c]["gain"] >= 0
        g3 = A["arunachal"]["gain"][c]["gain"] >= GATES["flood_arunachal_min"]
        g4 = (A["flat, in Arunachal"]["gain"][c]["gain"] >= GATES["flood_arunachal_min"]
              if gate_ap_flat else None)
        verdict[c] = {"G1": bool(g1), "G2": bool(g2), "G3": bool(g3), "G4_flat_in_AP": g4,
                      "pass": bool(g1 and g2 and g3 and g4 is not False)}
    out["verdict"] = verdict
    print("\n  verdict:", verdict)
    return out


def stale() -> dict:
    """§8: does the confirmed flat-ground gain survive the live data delay?
    Soil at a fixed t-16, which the live run always has."""
    rep = json.loads(REPORT.read_text())
    ref = rep["flat"]["areas"]["flat"]["gain"]["flat +soil"]["gain"]
    out = _flat_run(STALE_LAG, ("flat +soil",), STALE_CI, "STALE SOIL (§8) - flat cells only")
    A = out["areas"]
    g = {a: A[a]["gain"]["flat +soil"] for a in ("flat", "region", "arunachal")}
    s1 = g["flat"]["gain"] >= ref / 2 and g["flat"]["ci95"][0] > 0
    s2 = g["arunachal"]["gain"] >= GATES["flood_arunachal_min"]
    s3 = g["region"]["gain"] >= 0
    out["reference_flat_gain_s7"] = ref
    out["verdict"] = {"S1": bool(s1), "S2": bool(s2), "S3": bool(s3), "pass": bool(s1 and s2 and s3)}
    print("\n  verdict:", out["verdict"], f"(S1 bar: +{ref/2:.4f})")
    return out


# ── 4. landslides ────────────────────────────────────────────────────────
def _trigger_pct(a: np.ndarray, mons: np.ndarray, t: np.ndarray, c: np.ndarray) -> np.ndarray:
    """trigger.py's own percentile: (monsoon history < value).mean(), history
    including NaN rows, NaN value -> 0. Kept exact so the baseline reproduces
    the shipped 0.768."""
    out = np.empty(len(t), dtype=np.float32)
    clim = {}
    for i, (ti, ci) in enumerate(zip(t, c)):
        if ci not in clim:
            clim[ci] = a[mons, ci]
        out[i] = (clim[ci] < a[ti, ci]).mean()
    return out


def _slide_scores(feat: dict, mons, t, c) -> dict:
    p = {n: _trigger_pct(a, mons, t, c) for n, a in feat.items()}
    long_ = (p["r15"] + p["r30"]) / 2
    return {"baseline": (p["r3"] + p["r7"]) / 2,
            "+soil": (p["r3"] + p["r7"] + p["soil"]) / 3,
            "+long rain": (p["r3"] + p["r7"] + long_) / 3,
            "+both": (p["r3"] + p["r7"] + p["soil"] + long_) / 4,
            **{f"_{n}": v for n, v in p.items()}}


def _controls(dates: pd.DatetimeIndex, ok: np.ndarray, t: int, c: int) -> np.ndarray:
    d = dates[t]
    doy = np.asarray(dates.dayofyear)
    near = np.abs(doy - d.dayofyear) <= CONTROL_WINDOW
    other = np.asarray((dates.year != d.year) & (dates.year <= CONTROL_LAST_YEAR))
    return np.flatnonzero(near & other & ok[:, c])


def _slide_test(feat: dict, dates: pd.DatetimeIndex, ev_t: np.ndarray, ev_c: np.ndarray,
                label: str) -> dict:
    mons = np.asarray((dates.month >= MONSOON[0]) & (dates.month <= MONSOON[1]))
    # a cell-day is usable once its 30-day window and its soil value exist
    ok = np.isfinite(feat["r30"]) & np.isfinite(feat["soil"])
    keep = ok[ev_t, ev_c]
    n_dropped = int((~keep).sum())
    ev_t, ev_c = ev_t[keep], ev_c[keep]
    # L-time: each event against its own cell's same-season days, other years
    ev_s = _slide_scores(feat, mons, ev_t, ev_c)
    U = {n: [] for n in ev_s}
    for i, (ti, ci) in enumerate(zip(ev_t, ev_c)):
        ct = _controls(dates, ok, ti, ci)
        cs = _slide_scores(feat, mons, ct, np.full(len(ct), ci))
        for n in ev_s:
            U[n].append(placements(ev_s[n][i:i + 1], cs[n])[0])
    U = {n: np.asarray(v) for n, v in U.items()}
    grp = np.asarray(dates[ev_t].strftime("%Y-%m-%d"))
    # L-prod: random monsoon days x random event cells, as trigger.py
    rng = np.random.default_rng(SEED)
    nt = rng.choice(np.where(mons)[0], size=20_000)
    nc = rng.choice(np.unique(ev_c), size=20_000)
    ng = _slide_scores(feat, mons, nt, nc)
    y = np.r_[np.ones(len(ev_t)), np.zeros(len(nt))]
    prod = {n: float(roc_auc_score(y, np.r_[ev_s[n], ng[n]])) for n in ev_s}
    runs = ("baseline",) + CANDIDATES
    out = {"n_events": int(len(ev_t)), "n_event_dates": int(len(np.unique(grp))),
           "n_events_dropped_no_data": n_dropped,
           "median_controls_per_event": int(np.median(
               [len(_controls(dates, ok, ti, ci)) for ti, ci in zip(ev_t, ev_c)])),
           "L_time": {n: float(U[n].mean()) for n in runs},
           "L_prod": {n: prod[n] for n in runs},
           "gain_time": {c: boot_gain(U[c], U["baseline"], grp) for c in CANDIDATES},
           "single_input_L_time": {n[1:]: float(U[n].mean()) for n in U if n.startswith("_")}}
    verdict = {}
    for c in CANDIDATES:
        g = out["gain_time"][c]
        l1 = g["gain"] >= GATES["slide_gain_min"] and g["ci983"][0] > 0
        l2 = prod[c] - prod["baseline"] >= GATES["slide_prod_min"]
        verdict[c] = {"L1": bool(l1), "L2": bool(l2), "pass": bool(l1 and l2)}
    out["verdict"] = verdict
    print(f"\n  {label}: {out['n_events']} events on {out['n_event_dates']} dates, "
          f"~{out['median_controls_per_event']} own-cell control days each")
    print(f"    baseline  L-time {out['L_time']['baseline']:.4f}   L-prod {prod['baseline']:.4f}")
    for c in CANDIDATES:
        g = out["gain_time"][c]
        print(f"    {c:<10} L-time {out['L_time'][c]:.4f} gain {g['gain']:+.4f} "
              f"98.3% [{g['ci983'][0]:+.4f}, {g['ci983'][1]:+.4f}]   "
              f"L-prod {prod[c]:.4f} ({prod[c]-prod['baseline']:+.4f})")
    print("    single inputs (L-time):",
          {k: round(v, 3) for k, v in out["single_input_L_time"].items()})
    print("    verdict:", {c: v["pass"] for c, v in verdict.items()})
    return out


def slide() -> dict:
    from trigger import load_events
    print("\nLANDSLIDE 4A - Arunachal, IMERG rain, the shipped trigger's events")
    dates = pd.to_datetime(np.load(RAIN / "dates.npy").astype("datetime64[D]"))
    with rasterio.open(RAIN / "imerg_index.tif") as s:
        idx = s.read(1)
    cell, ti, _ = load_events(idx, dates)
    z = np.load(SOIL / "era5land_lattice.npz")
    soil = align(pd.to_datetime(z["dates"]), lag(soil_index(z), LAG), dates)
    feat = {n: np.load(FEAT / f"{n}.npy", mmap_mode="r") for n in ("r3", "r7", "r15", "r30")}
    feat = {n: np.asarray(a) for n, a in feat.items()}
    feat["soil"] = soil
    return _slide_test(feat, dates, ti, cell, "4A Arunachal")


def arc() -> dict:
    sys.path.insert(0, str(ROOT / "scripts" / "fetch"))
    from fetch_39_era5land_soil import arc_events
    from rainfall_features import rolling_sum
    print("\nLANDSLIDE 4B - Himalayan arc, ERA5-Land rain and soil")
    z = np.load(SOIL / "era5land_arc_events.npz")
    dates = pd.to_datetime(z["dates"])
    rain = z["rain_mm"].astype(np.float32)
    feat = {f"r{w}": rolling_sum(rain, w).astype(np.float32) for w in (3, 7, 15, 30)}
    feat["soil"] = lag(soil_index(z), LAG)
    ev = arc_events()
    col = {k: i for i, k in enumerate(z["arc_k"])}
    ev["c"] = ev["ak"].map(col)
    pos = pd.Series(np.arange(len(dates)), index=dates)
    ev = ev[ev["date"].isin(dates)].copy()
    ev["t"] = pos[ev["date"]].to_numpy()
    ev = ev.drop_duplicates(subset=["c", "t"])
    return _slide_test(feat, dates, ev["t"].to_numpy(), ev["c"].to_numpy(), "4B arc")


if __name__ == "__main__":
    parts = sys.argv[1:] or ["flood", "slide", "arc"]
    for p in parts:
        save(p, {"flood": flood, "flat": flat, "stale": stale, "slide": slide, "arc": arc}[p]())
