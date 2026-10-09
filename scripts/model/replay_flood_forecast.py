"""Replay the joined flood forecast over 2023-2026 floods it never saw.

    python scripts/model/replay_flood_forecast.py

Needs   models/flood_where_replay2022/   (train_flood_where.py --until
                                          2022-12-31 --tag replay2022)
Writes  reports/flood_forecast_replay.json

════════════════════════════════════════════════════════════════════════════
THE RULE THAT MAKES THIS A REAL TEST
════════════════════════════════════════════════════════════════════════════
Nothing that produces a number here has seen 2023 or later:

    WHERE        retrained on floods up to 2022 only (the shipped model saw
                 every year, so it cannot be used to replay them)
    day model    tree fitted on 2015-2020, calibration curve on 2021-2022
    "normal"     each place's ordinary level, from 2015-2022 only

Then the whole chain is run forward over 2023-01-01 .. 2025-10-31 (TRUTH_END,
where the flood record stops) and scored against the satellite-confirmed
floods of those years. Until 2026-09-27 it ran to 2026-07-29, counting
Feb-Jul 2026 - unrecorded, not dry - as flood-free.

════════════════════════════════════════════════════════════════════════════
THREE QUESTIONS, EACH WITH ITS OWN TRUTH
════════════════════════════════════════════════════════════════════════════
1. RIGHT DAY?    Did the day model's chance rise on the days, in the ~10 km
                 areas, where floods were then confirmed? Truth: every rain
                 cell, every day - a confirmed flood there or not.
2. RIGHT PLACE?  Inside each flood's satellite crop, did the high WHERE
                 numbers sit on the ground that actually went under water?
                 Truth: the flood's own new-water mask.
3. TOGETHER?     Over every 100 m patch and every day, did the joined number
                 add up - does expected flooded ground match observed, and do
                 the patches that flooded outrank the ones that didn't?

The truth definition throughout is "a reported flood a satellite confirmed".
Floods nobody reported are not in it, so absolute chances are a floor. The
"times normal" figures divide that bias out and are the robust read.
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
from pyproj import Transformer
from sklearn.metrics import average_precision_score, roc_auc_score

import grid as G
import when_grid
from build_flood_where_samples import COVER_MIN, POS_FRAC, event_grid
from common import INTERIM, ROOT
from flood_forecast import (TRUTH_END, DayModel, day_features, exposure, imerg_index_full,
                            label_matrix, load_events, years)
from predict_flood_where import score_grid

REPLAY_WHERE = ROOT / "models" / "flood_where_replay2022"
PIX = INTERIM / "flood_where_pixels"
STACK = INTERIM / "terrain_unmasked"
TEST_FROM = pd.Timestamp("2023-01-01")
TIMES = [2, 5, 10, 20]
STEEP_DEG = 10.0


def auc(y, p):
    return float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None


def log_bins(y, p, edges):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum() < 200:
            continue
        out.append({"p_lo": float(lo), "p_hi": float(hi), "n": int(m.sum()),
                    "predicted": float(p[m].mean()), "observed": float(y[m].mean()),
                    "n_pos": int(y[m].sum())})
    return out


def main() -> None:
    t0 = time.time()
    upstream = "--upstream" in sys.argv
    # --gauge: also feed each rain cell yesterday's reading of the gauge(s) on
    # the river flowing into it (build_gauge_reach.py); missing where none
    gauge = "--gauge" in sys.argv
    # Label-audit switches (§0n): drop the braided-channel-shift suspects
    #   --train-clean  from everything the models learn from (WHERE is then
    #                  the flood_where_replay2022_clean model)
    #   --test-clean   from the 2023-26 truth the replay is graded against
    # Running both combinations separates "does cleaning improve the model"
    # from "how much were the suspects dragging the scores down".
    train_clean = "--train-clean" in sys.argv
    test_clean = "--test-clean" in sys.argv
    tag = ("_upstream" if upstream else "") + ("_gauge" if gauge else "") + ("_trainclean" if train_clean else "") \
        + ("_testclean" if test_clean else "")
    suspects = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
                   ["channel_shift_suspects"]["uuids"])
    print(f"Replaying the joined flood forecast over 2023-2026"
          f"{'  [local + upstream rain]' if upstream else '  [local rain only]'}\n")

    dates, W = when_grid.load()
    W = np.asarray(W)
    n_cells = W.shape[1]
    kidx = imerg_index_full()
    print("  scoring WHERE (2022-only model) over the whole window...", flush=True)
    where_dir = REPLAY_WHERE.with_name(REPLAY_WHERE.name + "_clean") if train_clean else REPLAY_WHERE
    H, _ = score_grid(where_dir, clip_to_state=False, verbose=False)
    E = exposure(H, kidx, n_cells)
    ev_all = load_events()
    ev_tr = ev_all[~ev_all["uuid"].isin(suspects)] if train_clean else ev_all
    ev = ev_all[~ev_all["uuid"].isin(suspects)] if test_clean else ev_all
    Y_tr = label_matrix(ev_tr, dates, n_cells)
    Y = label_matrix(ev, dates, n_cells)
    print(f"  labels: train {len(ev_tr):,} floods, test truth {len(ev):,} floods "
          f"(channel-shift suspects removed from: "
          f"{', '.join(n for n, f in (('train', train_clean), ('test', test_clean)) if f) or 'neither'})")

    with rasterio.open(INTERIM / "state_mask.tif") as m:
        instate = m.read(1).astype(bool)
    frac_in = (np.bincount(kidx[instate & (kidx >= 0)], minlength=n_cells)
               / np.maximum(np.bincount(kidx[kidx >= 0], minlength=n_cells), 1))
    cell_in_state = frac_in > 0.5

    F = day_features(W, upstream)
    optional = ()
    if gauge:
        F = F + [np.load(INTERIM / "flood_forecast" / "gauge_frac.npz")["G"]]
        optional = (len(F) - 1,)
    model, fit_info = DayModel.fit(F, E, Y_tr, years(dates, 2015, 2020), years(dates, 2021, 2022),
                                   optional=optional)
    P = model.predict(F, E)
    normal = np.nanmean(P[years(dates, 2015, 2022)], axis=0)
    test = np.asarray((dates >= TEST_FROM) & (dates <= TRUTH_END))
    print(f"  day model fitted: {fit_info}  ({time.time()-t0:.0f}s)")

    # ════ 1. RIGHT DAY? ═════════════════════════════════════════════════
    cells = np.isfinite(E)
    Pt, Yt = P[test][:, cells], Y[test][:, cells]
    ok = np.isfinite(Pt)
    p1, y1 = Pt[ok], Yt[ok]
    base = float(Y_tr[years(dates, 2015, 2022)][:, cells].mean())
    brier = float(np.mean((p1 - y1) ** 2))
    brier_clim = float(np.mean((base - y1) ** 2))
    in_mask = np.broadcast_to(cell_in_state[cells], Pt.shape)[ok]
    ratio = (Pt / normal[cells][None, :])
    ratio_prev = np.vstack([np.full((1, ratio.shape[1]), np.nan), ratio[:-1]])
    ratio_pm1 = np.fmax(ratio, ratio_prev)          # the day, or the day before

    ev_t = np.argwhere(Yt == 1)                     # (day, cell) of each test flood
    r_day = ratio[ev_t[:, 0], ev_t[:, 1]]
    r_pm1 = ratio_pm1[ev_t[:, 0], ev_t[:, 1]]
    warn = []
    for t in TIMES:
        warn.append({
            "warn_when_times_normal_at_least": t,
            "floods_caught_pct": float(100 * np.nanmean(r_day >= t)),
            "floods_caught_pct_day_or_day_before": float(100 * np.nanmean(r_pm1 >= t)),
            "share_of_area_days_under_warning_pct": float(100 * np.nanmean(ratio[np.isfinite(ratio)] >= t)),
        })
    day = {
        "n_area_days": int(ok.sum()), "n_floods": int(y1.sum()),
        "auc": auc(y1, p1), "auc_in_arunachal": auc(y1[in_mask], p1[in_mask]),
        "average_precision": float(average_precision_score(y1, p1)),
        "base_rate": base,
        "brier_skill_vs_climatology": 1 - brier / brier_clim,
        "expected_floods": float(p1.sum()), "observed_floods": int(y1.sum()),
        "expected_floods_in_arunachal": float(p1[in_mask].sum()),
        "observed_floods_in_arunachal": int(y1[in_mask].sum()),
        "reliability": log_bins(y1, p1, np.r_[0, np.logspace(-6, 0, 19)]),
        "warning_levels": warn,
        "median_times_normal_on_flood_days": float(np.nanmedian(r_day)),
    }
    # Timing-only ranking skill. The plain AUC above mostly rewards knowing
    # that floodplain cells flood more than ridge cells — WHERE-type skill.
    # Ranking by "times this place's own normal" removes that, leaving only
    # "was today unusual for here".
    rf = np.isfinite(ratio)
    day["auc_timing_only"] = auc(Yt[rf], ratio[rf])
    # The same, only where a gauged river flows in (build_gauge_reach.py) —
    # scored in every run, gauge input or not, so runs compare like for like.
    gpath = INTERIM / "flood_forecast" / "gauge_frac.npz"
    if gpath.exists():
        gc = np.isfinite(np.load(gpath)["G"]).any(axis=0)[cells]
        sub = {}
        for name, colmask in (("all", gc), ("in_arunachal", gc & cell_in_state[cells])):
            r_, y_ = ratio[:, colmask], Yt[:, colmask]
            f_ = np.isfinite(r_)
            at = np.argwhere(y_ == 1)
            rf_ = r_[at[:, 0], at[:, 1]]
            sub[name] = {"n_cells": int(colmask.sum()), "n_floods": int(y_.sum()),
                         "auc_timing_only": auc(y_[f_], r_[f_]),
                         "warn_2x_floods_caught_pct": float(100 * np.nanmean(rf_ >= 2)),
                         "warn_2x_time_under_warning_pct": float(100 * np.nanmean(r_[f_] >= 2))}
        day["gauged_river_cells"] = sub
        print(f"\n     where a gauged river flows in: timing AUC {sub['all']['auc_timing_only']:.3f} "
              f"({sub['all']['n_floods']} floods), inside Arunachal "
              f"{sub['in_arunachal']['auc_timing_only']:.3f} ({sub['in_arunachal']['n_floods']}); "
              f"warn at 2x catches {sub['all']['warn_2x_floods_caught_pct']:.0f}% on "
              f"{sub['all']['warn_2x_time_under_warning_pct']:.1f}% of area-days")
    test_dates = dates[test]
    col_of = {k: i for i, k in enumerate(np.flatnonzero(cells))}
    named = {}
    for nd in ("2024-05-24", "2024-06-30"):
        di = np.flatnonzero(test_dates == pd.Timestamp(nd))
        e = ev[(ev["date"] == pd.Timestamp(nd)) & (ev["k"] >= 0)]
        cs = [col_of[k] for k in e["k"] if k in col_of]
        if len(di) and cs:
            v = ratio[di[0], cs]
            named[nd] = {"n_floods": len(cs), "median_times_normal": float(np.nanmedian(v)),
                         "share_at_2x_or_more_pct": float(100 * np.nanmean(v >= 2))}
    day["named_days"] = named

    print("\n  1. RIGHT DAY?  (rain cell x day, 2023-2026)")
    print(f"     timing-only skill (each place vs its own normal) AUC {day['auc_timing_only']:.3f}")
    for nd, v in named.items():
        print(f"     {nd}: {v['n_floods']} floods, typically {v['median_times_normal']:.1f}x normal, "
              f"{v['share_at_2x_or_more_pct']:.0f}% at 2x or more")
    print(f"     {day['n_floods']:,} real floods among {day['n_area_days']:,} area-days")
    print(f"     ranking skill (AUC) {day['auc']:.3f}   inside Arunachal {day['auc_in_arunachal']:.3f}")
    print(f"     expected {day['expected_floods']:.0f} floods, observed {day['observed_floods']}"
          f"   (Arunachal: {day['expected_floods_in_arunachal']:.0f} vs {day['observed_floods_in_arunachal']})")
    print(f"     beats 'same chance every day' by {100*day['brier_skill_vs_climatology']:.1f}% (Brier skill)")
    print(f"     on flood days the chance was typically {day['median_times_normal_on_flood_days']:.1f}x normal")
    print(f"     {'warn at':>10}{'floods caught':>16}{'(or day before)':>17}{'time under warning':>21}")
    for w in warn:
        print(f"     {w['warn_when_times_normal_at_least']:>8}x  {w['floods_caught_pct']:>13.1f}%"
              f"{w['floods_caught_pct_day_or_day_before']:>16.1f}%"
              f"{w['share_of_area_days_under_warning_pct']:>19.1f}%")

    # ════ 2. RIGHT PLACE? ═══════════════════════════════════════════════
    with rasterio.open(STACK / "terrain_slope_deg.tif") as s:
        slope = s.read(1)
    to3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_utm = Transformer.from_crs("EPSG:3857", G.CRS, always_xy=True)
    ev_test = ev[(ev["date"] >= TEST_FROM) & (ev["date"] <= TRUTH_END)]
    hv, lab, ins, stp, per_event = [], [], [], [], []
    wet_by_day: dict[pd.Timestamp, set] = {}
    for _, e in ev_test.iterrows():
        p = PIX / f"{e['uuid']}.npz"
        if not p.exists():
            continue
        g = event_grid(p, to3857, to_utm)
        if g is None:
            continue
        r0, c0, frac, cover = g[:4]
        h, w = frac.shape
        sub = (slice(r0, r0 + h), slice(c0, c0 + w))
        hh = H[sub]
        keep = (cover >= COVER_MIN) & np.isfinite(hh)
        wet = keep & (frac >= POS_FRAC)
        dry = keep & (frac <= 0.0)
        if wet.sum() + dry.sum() < 100:
            continue
        use = wet | dry
        hv.append(hh[use]); lab.append(wet[use])
        ins.append(instate[sub][use]); stp.append(slope[sub][use] >= STEEP_DEG)
        per_event.append({"uuid": e["uuid"], "date": str(e["date"].date()),
                          "expected_wet_cells": float(hh[use].sum()),
                          "observed_wet_cells": int(wet.sum())})
        rr, cc = np.nonzero(wet)
        wet_by_day.setdefault(e["date"], set()).update(zip((rr + r0).tolist(), (cc + c0).tolist()))
    hv, lab = np.concatenate(hv), np.concatenate(lab)
    ins, stp = np.concatenate(ins), np.concatenate(stp)
    pe = pd.DataFrame(per_event)
    place = {
        "n_floods_scored": int(len(pe)), "n_cells": int(len(hv)), "n_wet": int(lab.sum()),
        "auc": auc(lab, hv), "auc_in_arunachal": auc(lab[ins], hv[ins]),
        "auc_steep": auc(lab[stp], hv[stp]),
        "expected_wet_cells_total": float(hv.sum()), "observed_wet_cells_total": int(lab.sum()),
        # Given a flood, how much water — on ground a satellite actually looked
        # at, inside Arunachal. The one part of the Arunachal gap that is
        # measurable model error rather than possible under-reporting (§0p).
        "expected_wet_cells_in_arunachal": float(hv[ins].sum()),
        "observed_wet_cells_in_arunachal": int(lab[ins].sum()),
        "expected_wet_cells_steep": float(hv[stp].sum()),
        "observed_wet_cells_steep": int(lab[stp].sum()),
        "reliability": log_bins(lab.astype(float), hv, np.r_[0, 1e-4, 0.01, 0.02, 0.05,
                                                            0.1, 0.15, 0.2, 0.3, 0.5, 1.01]),
        "median_event_expected_over_observed": float(np.median(
            pe["expected_wet_cells"] / pe["observed_wet_cells"].clip(lower=1))),
    }
    print(f"\n  2. RIGHT PLACE?  (inside {place['n_floods_scored']:,} flood crops, 2023-2026)")
    print(f"     ranking skill (AUC) {place['auc']:.3f}   Arunachal {place['auc_in_arunachal']:.3f}"
          f"   steep ground {place['auc_steep']:.3f}")
    print(f"     expected {place['expected_wet_cells_total']:,.0f} flooded patches, "
          f"observed {place['observed_wet_cells_total']:,}")
    print(f"     inside Arunachal: expected {place['expected_wet_cells_in_arunachal']:,.0f}, "
          f"observed {place['observed_wet_cells_in_arunachal']:,}   steep ground: expected "
          f"{place['expected_wet_cells_steep']:,.0f}, observed {place['observed_wet_cells_steep']:,}")

    # ════ 3. TOGETHER? ══════════════════════════════════════════════════
    day_pos = pd.Series(np.arange(len(dates)), index=dates)
    pr, pc, pdd = [], [], []
    for d, s in wet_by_day.items():
        for r, c in s:
            pr.append(r); pc.append(c); pdd.append(day_pos[d])
    pr, pc, pdd = map(np.asarray, (pr, pc, pdd))
    k_pos = kidx[pr, pc]
    good = k_pos >= 0
    comb_pos = P[pdd[good], k_pos[good]] * H[pr[good], pc[good]]
    pos_in = instate[pr[good], pc[good]]

    rng = np.random.default_rng(42)
    valid = np.flatnonzero((np.isfinite(H) & (kidx >= 0)).ravel())
    test_days = np.flatnonzero(test)
    n_neg = 4_000_000
    cell = rng.choice(valid, n_neg)
    nd = rng.choice(test_days, n_neg)
    nr, nc = np.unravel_index(cell, G.SHAPE)
    comb_neg = P[nd, kidx[nr, nc]] * H[nr, nc]
    neg_in = instate[nr, nc]

    # Expected patch-days of flooding over the test period, summed exactly:
    # sum over rain cells of (floodable patches there) x (sum of daily chance).
    Hs = np.where(np.isfinite(H) & (kidx >= 0), H, 0.0)
    A = np.bincount(kidx[kidx >= 0], weights=Hs[kidx >= 0].astype(np.float64), minlength=n_cells)
    A_in = np.bincount(kidx[(kidx >= 0) & instate],
                       weights=Hs[(kidx >= 0) & instate].astype(np.float64), minlength=n_cells)
    Psum = np.nansum(P[test], axis=0)
    y_all = np.r_[np.ones(len(comb_pos)), np.zeros(n_neg)]
    s_all = np.r_[comb_pos, comb_neg]
    ok3 = np.isfinite(s_all)
    thr = {q: float(np.nanquantile(comb_neg, q)) for q in (0.99, 0.999)}
    together = {
        "n_flooded_patch_days": int(len(comb_pos)),
        "auc": auc(y_all[ok3], s_all[ok3]),
        "auc_in_arunachal": auc(np.r_[np.ones(pos_in.sum()), np.zeros(neg_in.sum())],
                                np.r_[comb_pos[pos_in], comb_neg[neg_in]]),
        "expected_flooded_patch_days": float((A * Psum).sum()),
        "observed_flooded_patch_days": int(len(comb_pos)),
        "expected_in_arunachal": float((A_in * Psum).sum()),
        "observed_in_arunachal": int(pos_in.sum()),
        "flooded_patches_in_top_1pct_pct": float(100 * np.nanmean(comb_pos >= thr[0.99])),
        "flooded_patches_in_top_0.1pct_pct": float(100 * np.nanmean(comb_pos >= thr[0.999])),
        "mean_score_flooded_over_ordinary": float(np.nanmean(comb_pos) / np.nanmean(comb_neg)),
    }
    print("\n  3. TOGETHER?  (every 100 m patch x every day, 2023-2026)")
    print(f"     ranking skill (AUC) {together['auc']:.3f}   Arunachal {together['auc_in_arunachal']:.3f}")
    print(f"     {together['flooded_patches_in_top_1pct_pct']:.1f}% of flooded patch-days were in the "
          f"forecast's top 1%;  {together['flooded_patches_in_top_0.1pct_pct']:.1f}% in the top 0.1%")
    print(f"     flooded patches scored {together['mean_score_flooded_over_ordinary']:,.0f}x "
          f"an ordinary patch-day on average")
    print(f"     expected {together['expected_flooded_patch_days']:,.0f} flooded patch-days, "
          f"observed {together['observed_flooded_patch_days']:,}"
          f"   (Arunachal {together['expected_in_arunachal']:,.0f} vs {together['observed_in_arunachal']:,})")

    # ════ 3b. THE JOIN OVER-PROMISES IN THE MOUNTAINS — correct it ═══════
    # WHERE answers "given a flood within ~5 km, does it reach this patch".
    # The join applies that to every patch in a ~10 km rain cell. On the
    # floodplain one river floods broadly, so that nearly holds. A mountain
    # rain cell holds several separate valleys, and a flood down one of them
    # leaves the others dry — so summing WHERE over the whole cell counts
    # floodable ground that the flood never reaches. Measured on the first
    # run: expected 73k flooded patch-days in Arunachal, observed 11k.
    #
    # Fix: one factor per terrain class of rain cell — the share of its
    # floodable ground a typical flood really reaches — fitted on 2021-2022
    # and then checked on 2023-2026. (The 2021-22 masks were inside the replay
    # WHERE model's training years, so the factor is fitted on ground WHERE
    # has seen; the TEST is still on years nothing has seen.)
    valid_k = (kidx >= 0) & np.isfinite(slope)
    slope_sum = np.bincount(kidx[valid_k], weights=slope[valid_k].astype(np.float64),
                            minlength=n_cells)
    slope_n = np.bincount(kidx[valid_k], minlength=n_cells)
    cell_slope = np.where(slope_n > 0, slope_sum / np.maximum(slope_n, 1), np.nan)
    CLASS_EDGES = [5.0, 15.0]
    CLASS_NAMES = ["flat (<5 deg)", "hilly (5-15 deg)", "steep (>=15 deg)"]
    cls_of = np.digitize(np.nan_to_num(cell_slope, nan=0.0), CLASS_EDGES)

    # Two ways of grouping the correction were tried; both are recorded.
    #   terrain         one factor per rain-cell terrain class      <- SHIPPED
    #   terrain+state   also split by patch inside/outside Arunachal
    # The second exists because border rain cells straddle the wide Assam
    # floodplain and the Arunachal foothills, and a floodplain-learnt factor
    # over-promises the foothill side. It was rejected on the 2023-26 test:
    # its Arunachal factors swing by an order of magnitude between fit years
    # and test years (a handful of in-state floods is not enough to pin
    # six numbers), and it barely narrowed the in-state gap.
    def fit_and_test(gid_of_patch, n_groups, names):
        def count(rows, cols):
            k = kidx[rows, cols]
            keep = k >= 0
            g = gid_of_patch(cls_of[k[keep]], instate[rows[keep], cols[keep]])
            return np.bincount(g, minlength=n_groups)

        def wet_rc(evs):
            by_day: dict[pd.Timestamp, set] = {}
            for _, e in evs.iterrows():
                p = PIX / f"{e['uuid']}.npz"
                if not p.exists():
                    continue
                g = event_grid(p, to3857, to_utm)
                if g is None:
                    continue
                r0, c0, frac, cover = g[:4]
                h, w = frac.shape
                wet = ((cover >= COVER_MIN) & (frac >= POS_FRAC)
                       & np.isfinite(H[r0:r0 + h, c0:c0 + w]))
                rr, cc = np.nonzero(wet)
                by_day.setdefault(e["date"], set()).update(
                    zip((rr + r0).tolist(), (cc + c0).tolist()))
            rc = np.asarray([x for s_ in by_day.values() for x in s_], dtype=int).reshape(-1, 2)
            return rc[:, 0], rc[:, 1]

        def expected(day_mask):
            ps = np.nansum(P[day_mask], axis=0)
            out_ = np.zeros(n_groups)
            for side, Aside in ((False, A_out), (True, A_in)):
                g = gid_of_patch(cls_of, np.full(n_cells, side))
                out_ += np.bincount(g, weights=Aside * ps, minlength=n_groups)
            return out_

        cal = (ev_tr["date"].dt.year >= 2021) & (ev_tr["date"].dt.year <= 2022)
        obs_cal = count(*wet_rc(ev_tr[cal]))
        exp_cal = expected(years(dates, 2021, 2022))
        factor = np.where(exp_cal > 0, obs_cal / np.maximum(exp_cal, 1e-9), 1.0)
        obs_t = count(pr, pc)
        exp_t = expected(test)
        # Arunachal totals need the patch side, not the group, so recount.
        in_obs = int(pos_in.sum())
        in_exp = 0.0
        ps = np.nansum(P[test], axis=0)
        g_in = gid_of_patch(cls_of, np.full(n_cells, True))
        in_exp = float((A_in * ps * factor[g_in]).sum())
        return {
            "groups": [{"group": names[i], "factor": float(factor[i]),
                        "fit_expected": float(exp_cal[i]), "fit_observed": int(obs_cal[i]),
                        "test_expected_uncorrected": float(exp_t[i]),
                        "test_expected_corrected": float(exp_t[i] * factor[i]),
                        "test_observed": int(obs_t[i])} for i in range(n_groups)],
            "test_expected_corrected_total": float((exp_t * factor).sum()),
            "test_observed_total": int(obs_t.sum()),
            "test_expected_corrected_in_arunachal": in_exp,
            "test_observed_in_arunachal": in_obs,
        }

    A_out = A - A_in
    variants = {
        "terrain (shipped)": fit_and_test(lambda c, side: c, 3, CLASS_NAMES),
        "terrain+state (rejected)": fit_and_test(
            lambda c, side: c + 3 * np.asarray(side, dtype=int), 6,
            [f"{n} / {sd}" for sd in ("outside", "inside") for n in CLASS_NAMES]),
    }
    print("\n  3b. CORRECTED FOR MOUNTAIN VALLEYS  (factors fitted 2021-22, tested 2023-26)")
    for vname, v in variants.items():
        print(f"     -- {vname}")
        print(f"     {'group':<30}{'factor':>8}{'before':>11}{'after':>10}{'observed':>10}")
        for g in v["groups"]:
            print(f"     {g['group']:<30}{g['factor']:>8.3f}{g['test_expected_uncorrected']:>11,.0f}"
                  f"{g['test_expected_corrected']:>10,.0f}{g['test_observed']:>10,}")
        print(f"     total expected {v['test_expected_corrected_total']:,.0f} vs observed "
              f"{v['test_observed_total']:,};  Arunachal {v['test_expected_corrected_in_arunachal']:,.0f}"
              f" vs {v['test_observed_in_arunachal']:,}")
    corrected = {"method": "scale factor per group = observed/expected flooded "
                           "patch-days on 2021-2022, tested on 2023-2026",
                 "variants": variants, "shipped": "terrain (shipped)"}

    out = ROOT / "reports" / f"flood_forecast_replay{tag}.json"
    out.write_text(json.dumps({
        "what": (f"WHEN x WHERE joined, replayed over 2023-01-01..{TRUTH_END.date()} with "
                 "every component fitted on 2022 and earlier only"),
        "truth": "reported floods confirmed by Sentinel-1 - unreported floods are not counted",
        "day_model_fit": fit_info,
        "right_day": day, "right_place": place, "together": together,
        "together_corrected": corrected,
        "per_event": per_event,
    }, indent=2))
    print(f"\n  wrote {out}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
