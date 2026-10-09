"""Does the day model forecast flood timing better when its tree also learns
from the verified floods before 2015? The pre-registered test in
docs/design/OLDER_FLOODS_TEST.md §2 — candidates, metrics and gates are fixed
there; this script only carries them out.

    python scripts/model/test_older_floods.py

Writes  reports/older_floods_test.json

    baseline    tree 2015-2020  (the test copy every earlier test used)
    +2010-14    tree 2010-2020
    +2003-14    tree 2003-2020
    all three   calibration 2021-22, test 2023-01-01 .. TRUTH_END

The rain inputs for the added years are made by the same code as production
(when_grid.build, build_upstream_rain.upstream_percentiles), only not cut at
2015; the script checks they equal production's, value for value, from 2015.
Nothing here writes a production file.
"""
from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import rasterio

import near_here as NH
import when_grid
from common import INTERIM, ROOT
from flood_forecast import (MODELS, SLOPE_CLASS_NAMES, TRUTH_END, fit_day_model,
                            imerg_index_full, label_matrix, soil_input, training_events)
from test_soil_wetness import boot_gain, placements

REPORT = ROOT / "reports" / "older_floods_test.json"
FIRST = pd.Timestamp("2003-01-01")
TREE_FROM = {"baseline": 2015, "+2010-14": 2010, "+2003-14": 2003}
CANDIDATES = ("+2010-14", "+2003-14")
TREE_TO, CAL = 2020, (2021, 2022)
NORMAL_YEARS = (2015, 2022)              # each model's "own normal", same for all
TEST_FROM = pd.Timestamp("2023-01-01")
CI = (0.0125, 0.9875)                    # 97.5%: 95% split over two candidates
GATES = {"G1_region_gain_min": 0.010, "G3_arunachal_gain_min": -0.005,
         "G4_near_here_drop_max": 0.005, "tie_within": 0.002}


# ── inputs: production's, extended back to 2003 by the same code ──────────
def extended_when(t0: float) -> tuple[pd.DatetimeIndex, np.ndarray, dict]:
    """The local WHEN score from FIRST, scored as when_grid.build() scores it
    (production's own file from 2015 on, freshly scored before)."""
    dates, f = when_grid.percentile_features()
    lag = np.vstack([np.full((1, f["r3"].shape[1]), np.nan, np.float32),
                     ((f["r3"] + f["r7"]) / 2)[:-1]])
    wd, Wp = when_grid.load()
    Wp = np.asarray(Wp)
    with open(when_grid.MODELS / "B_pooled_nwdp_all.pkl", "rb") as fh:
        b = pickle.load(fh)
    with open(when_grid.MODELS / "C_bigriver_naive_DIAGNOSTIC_ONLY_005-UBDDIB.pkl", "rb") as fh:
        c = pickle.load(fh)

    def score(rows: np.ndarray) -> np.ndarray:
        r3, r7, lg = f["r3"][rows], f["r7"][rows], lag[rows]
        X = pd.DataFrame({"r3": r3.ravel(), "r7": r7.ravel(), "trigger_lag1": lg.ravel()})
        ok = X[["r3", "r7"]].notna().all(axis=1).to_numpy()
        raw = np.full(len(X), np.nan, dtype=np.float32)
        rule = X[["r3", "r7"]].mean(axis=1).to_numpy()
        raw[ok] = ((rule[ok] + b.predict_proba(X[ok])[:, 1] + c.predict_proba(X[ok])[:, 1])
                   / 3).astype(np.float32)
        return raw.reshape(r3.shape)

    new = np.asarray((dates >= FIRST) & (dates < wd[0]))
    Wn = score(new)
    # the same code must reproduce production exactly: check 2015's first 90 days
    chk = np.flatnonzero(np.asarray(dates >= wd[0]))[:90]
    Wc = score(chk)
    same_nan = bool(np.array_equal(np.isnan(Wc), np.isnan(Wp[:90])))
    dmax = float(np.nanmax(np.abs(Wc - Wp[:90])))
    assert np.array_equal(dates[chk], wd[:90]), "rain dates and when_dates do not line up"
    print(f"  WHEN score {dates[new][0].date()}..{dates[new][-1].date()} scored; "
          f"reproduces production on 90 days: max diff {dmax:.2e}, NaNs same {same_nan}  "
          f"({time.time()-t0:.0f}s)", flush=True)
    ext = dates[new].append(wd)
    return ext, np.vstack([Wn, Wp]), {"when_max_diff": dmax, "when_nan_pattern_same": same_nan}


def extended_upstream(dates_needed: pd.DatetimeIndex) -> tuple[dict, dict]:
    """build_upstream_rain.upstream_percentiles(), kept from FIRST instead of
    from when_dates — the lines are the same, only the final cut differs."""
    import build_upstream_rain as U
    w = U.weights()
    L = when_grid.lattice()
    rain = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    rain = np.asarray(rain).reshape(rain.shape[0], L["nlat"] * L["nlon"]).astype(np.float32)
    rain = np.nan_to_num(rain, nan=0.0)
    Wn = w["W"] / np.maximum(w["W"].sum(1, keepdims=True), 1.0)
    up = rain @ Wn.T
    dates = pd.to_datetime(np.load(INTERIM / "rainfall" / "dates.npy").astype("datetime64[D]"))
    mons = np.asarray((dates.month >= 5) & (dates.month <= 10))
    out = {}
    for name, win in (("up_r3", 3), ("up_r7", 7)):
        tot = pd.DataFrame(up).rolling(win, min_periods=win).sum().to_numpy(np.float32)
        pct = np.full(tot.shape, np.nan, dtype=np.float32)
        for k in range(tot.shape[1]):
            if w["W"][k].sum() == 0:
                continue
            col = tot[:, k]
            clim = np.sort(col[mons & np.isfinite(col)])
            fin = np.isfinite(col)
            pct[fin, k] = np.searchsorted(clim, col[fin], side="left") / len(clim)
        out[name] = pct
    keep = np.asarray(dates.isin(dates_needed))
    assert np.array_equal(dates[keep], dates_needed), "upstream dates do not line up"
    out = {k: v[keep] for k, v in out.items()}
    prod = np.load(INTERIM / "flood_forecast" / "upstream_rain_pct.npz")
    n = prod["up_r3"].shape[0]
    chk = {}
    for k in out:
        a, p = out[k][-n:], prod[k]
        chk[f"{k}_max_diff"] = float(np.nanmax(np.abs(a - p)))
        chk[f"{k}_nan_pattern_same"] = bool(np.array_equal(np.isnan(a), np.isnan(p)))
    return out, chk


def cells_in_state(n_cells: int) -> np.ndarray:
    """The soil test's definition: most of the rain cell lies in Arunachal."""
    kidx = imerg_index_full()
    with rasterio.open(INTERIM / "state_mask.tif") as m:
        instate = m.read(1).astype(bool)
    frac = (np.bincount(kidx[instate & (kidx >= 0)], minlength=n_cells)
            / np.maximum(np.bincount(kidx[kidx >= 0], minlength=n_cells), 1))
    return frac > 0.5


# ── the near-here figure the screen quotes ────────────────────────────────
def near_here_auc(P_om: np.ndarray, od: pd.DatetimeIndex, ev: pd.DataFrame,
                  E: np.ndarray, Yw: np.ndarray) -> dict:
    """near_here.diagnose()'s production-like routine: curves re-fitted each
    year on the latest two complete years, weekly, inside Arunachal, 2023-25."""
    n = P_om.shape[1]
    ap = NH.arunachal_cells(n) & np.isfinite(E)
    cells = np.isfinite(E)
    phase = np.asarray((od - NH.TEST_FROM).days % NH.WEEK)
    mon = np.asarray(od.month) - 1
    base = np.asarray((od.year >= 2010) & (od.year <= 2014))
    ys, ps, cs = [], [], []
    for y in (2023, 2024, 2025):
        cur = NH.fit_curves(P_om, od, ev, ap, cells, f"{y-2}-01-01", f"{y-1}-12-31")
        wk = NH.week_series(NH.day_chance(P_om, cur), cur["iso_week"])
        clim = NH._month_table(wk, od, base)
        rows = np.flatnonzero(np.asarray((od.year == y) & (od + pd.Timedelta(days=NH.WEEK - 1)
                                                            <= TRUTH_END)) & (phase == 0))
        cc = np.flatnonzero(ap)
        ys.append(Yw[np.ix_(rows, cc)].ravel())
        ps.append(wk[np.ix_(rows, cc)].ravel())
        cs.append(clim[np.ix_(mon[rows], cc)].ravel())
    g = NH.grade(np.concatenate(ys), np.concatenate(ps), np.concatenate(cs), None,
                 NH.WEEK_EDGES)
    return {"auc": g["auc"], "n_with_flood": g["n_with_flood"],
            "said_over_happened": g["A1_said_over_happened"]}


def main() -> dict:
    t0 = time.time()
    print("OLDER FLOODS — does the day model gain from verified floods before 2015?")
    print(f"  tree from 2015 / 2010 / 2003 to {TREE_TO}; calibration {CAL[0]}-{CAL[1]}; "
          f"test {TEST_FROM.date()}..{TRUTH_END.date()}\n")
    dates, W, when_chk = extended_when(t0)
    up, up_chk = extended_upstream(dates)
    print(f"  upstream rain extended; reproduces production: "
          f"{ {k: (round(v, 8) if isinstance(v, float) else v) for k, v in up_chk.items()} }  "
          f"({time.time()-t0:.0f}s)", flush=True)
    F = [W, up["up_r3"], up["up_r7"]]
    n = W.shape[1]
    E = np.load(INTERIM / "flood_forecast" / "exposure_replay2022_clean.npy")
    ev = training_events()
    Y = label_matrix(ev, dates, n)
    S = soil_input(dates)
    yrs = lambda a, b: np.asarray((dates.year >= a) & (dates.year <= b))

    models, P, fits = {}, {}, {}
    for name, y0 in TREE_FROM.items():
        m, info = fit_day_model(F, E, Y, yrs(y0, TREE_TO), yrs(*CAL), dates)
        models[name], fits[name] = m, info
        P[name] = m.predict(F, E, S)
        print(f"  {name:<9} tree {y0}-{TREE_TO}: {info['n_tree_pos']:,} flood cell-days of "
              f"{info['n_tree_rows']:,}  ({time.time()-t0:.0f}s)", flush=True)

    # ── timing: chance over the cell's own 2015-22 normal, test cell-days ──
    test = np.asarray((dates >= TEST_FROM) & (dates <= TRUTH_END))
    cells = np.isfinite(E)
    Yt = Y[test][:, cells]
    ratio = {}
    for name, p in P.items():
        normal = np.nanmean(p[yrs(*NORMAL_YEARS)], axis=0)
        ratio[name] = p[test][:, cells] / normal[cells][None, :]
    common = np.logical_and.reduce([np.isfinite(r) for r in ratio.values()])
    inst = np.broadcast_to(cells_in_state(n)[cells][None, :], Yt.shape)
    day_of = np.broadcast_to(np.flatnonzero(test)[:, None], Yt.shape)

    def area(mask):
        y = Yt[mask]
        pos = y == 1
        grp = day_of[mask][pos]
        u = {nm: placements(r[mask][pos], r[mask][~pos]) for nm, r in ratio.items()}
        return {"n_floods": int(pos.sum()), "n_flood_days": int(len(np.unique(grp))),
                "timing_auc": {nm: round(float(v.mean()), 4) for nm, v in u.items()},
                "gain": {c: boot_gain(u[c], u["baseline"], grp, CI) for c in CANDIDATES}}

    out = {"protocol": "docs/design/OLDER_FLOODS_TEST.md §2", "gates": GATES,
           "inputs_reproduce_production": {**when_chk, **up_chk},
           "fits": fits, "areas": {"region": area(common), "arunachal": area(common & inst)}}
    print(f"  timing graded ({time.time()-t0:.0f}s)", flush=True)

    # ── near-here ranking (the screen's figure), each model on live-archive rain ──
    od, Fo = NH.live_archive_features()
    So = soil_input(od)
    evn = NH.clean_events()
    Yw = NH.week_any(NH.truth_near(evn, od, NH.RADIUS_KM))
    out["near_here_week_in_arunachal"] = {
        name: near_here_auc(m.predict(Fo, E, So), od, evn, E, Yw) for name, m in models.items()}
    print(f"  near-here graded ({time.time()-t0:.0f}s)", flush=True)

    # ── verdict, exactly as pre-registered ──
    nh = out["near_here_week_in_arunachal"]
    verdict = {}
    for c in CANDIDATES:
        g = out["areas"]["region"]["gain"][c]
        ga = out["areas"]["arunachal"]["gain"][c]
        v = {"G1": g["gain"] >= GATES["G1_region_gain_min"],
             "G2": g["ci975"][0] > 0,
             "G3": ga["gain"] >= GATES["G3_arunachal_gain_min"],
             "G4": nh[c]["auc"] >= nh["baseline"]["auc"] - GATES["G4_near_here_drop_max"]}
        verdict[c] = {k: bool(x) for k, x in v.items()} | {"pass": bool(all(v.values()))}
    passed = [c for c in CANDIDATES if verdict[c]["pass"]]
    if len(passed) == 2:
        g = {c: out["areas"]["region"]["gain"][c]["gain"] for c in passed}
        ship = ("+2010-14" if abs(g["+2010-14"] - g["+2003-14"]) <= GATES["tie_within"]
                else max(g, key=g.get))
    else:
        ship = passed[0] if passed else None
    out["verdict"] = verdict
    out["ships"] = ship or "neither — training stays at 2015 on"

    # ── diagnostics: reported, never deciding ──
    kin = cells_in_state(n)
    k = ev["k"].to_numpy()
    in_ap = np.array([kk >= 0 and kin[kk] for kk in k])
    per_year = {"region": ev.groupby(ev["date"].dt.year).size().to_dict(),
                "arunachal": ev[in_ap].groupby(ev[in_ap]["date"].dt.year).size().to_dict()}
    mons = np.asarray((dates.month >= 5) & (dates.month <= 10))
    Wm = W[mons][:, cells]
    thr = float(np.nanquantile(Wm, 0.99))
    complete = {}
    for y in range(FIRST.year, TRUTH_END.year + 1):
        r = mons & np.asarray(dates.year == y) & np.asarray(dates <= TRUTH_END)
        w, yy = W[r][:, cells], Y[r][:, cells]
        top = np.isfinite(w) & (w >= thr)
        complete[str(y)] = {"wettest_cell_days": int(top.sum()),
                            "with_a_verified_flood_pct": round(100 * float(yy[top].mean()), 3)
                            if top.any() else None}
    cls = np.load(MODELS / "terrain_class.npy")
    clsb = np.broadcast_to(cls[cells][None, :], Yt.shape)
    terrain = {}
    for j, nm in enumerate(SLOPE_CLASS_NAMES):
        m = common & (clsb == j)
        if (Yt[m] == 1).sum() >= 10:
            terrain[nm] = area(m)
    out["diagnostics"] = {"verified_floods_per_year": {a: {str(y): int(v) for y, v in d.items()}
                                                       for a, d in per_year.items()},
                          "record_completeness_top1pct_wet_monsoon_cell_days":
                              {"threshold_when_score": round(thr, 4), "by_year": complete},
                          "timing_by_terrain_posthoc": terrain}
    REPORT.write_text(json.dumps(out, indent=2))
    _print(out)
    print(f"\n  wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


def _print(o: dict) -> None:
    for a, d in o["areas"].items():
        print(f"\n  {a}: {d['n_floods']} floods on {d['n_flood_days']} days — timing AUC")
        print(f"    baseline {d['timing_auc']['baseline']:.4f}")
        for c in CANDIDATES:
            g = d["gain"][c]
            print(f"    {c:<9} {d['timing_auc'][c]:.4f}  gain {g['gain']:+.4f}  "
                  f"97.5% [{g['ci975'][0]:+.4f}, {g['ci975'][1]:+.4f}]")
    print("\n  near-here weekly ranking inside Arunachal (production-like):")
    for nm, r in o["near_here_week_in_arunachal"].items():
        print(f"    {nm:<9} AUC {r['auc']}  ({r['n_with_flood']} flood place-weeks)")
    print("\n  verdict:", o["verdict"])
    print("  ships:", o["ships"])
    print("\n  diagnostics — wettest 1% monsoon cell-days with a verified flood, by year:")
    print("   ", "  ".join(f"{y}:{v['with_a_verified_flood_pct']}"
                          for y, v in o["diagnostics"]["record_completeness_top1pct_wet_monsoon_cell_days"]["by_year"].items()))


if __name__ == "__main__":
    main()
