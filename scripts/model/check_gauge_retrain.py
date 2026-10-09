"""Before the gauge models are retrained on the cleaned history: does what
would ship forecast at least as well as what is live? The rules are fixed in
docs/design/FLOOD_WHEN_PILOT_PLAN.md §13g-§13i; this script only carries them
out.

    python scripts/model/check_gauge_retrain.py            # the S-curve, §13i
    python scripts/model/check_gauge_retrain.py floor      # the floor, §13h (failed)

The fix under test is how a river-above day's score becomes a chance
(train_flood_when_gauge.ABOVE):

    A   the models as they were: stepped curve, history as it was (pass 1 only)
    B   the fix, the history as it was
    C   the fix, the history with all three passes — what would ship
    X   stepped curve, cleaned history: the retrain that failed G1, for reference

All are scored the way train_flood_when_gauge.py scores (year-grouped, out of
fold, calibrated out of fold), and graded against the CLEANED history as
truth, on the gauge-days both tables hold, at gauges whose line the cleaning
does not move.

    H1  the retrain alone     C against B
    H2  the fix alone         B against A; river-below days keep their chance
    H3  ships against live    C against A
        each: AUC and Brier skill no more than 0.005 lower at leads 1-3 and
        0.010 at leads 4-9, on all days and on onset days (unrounded)
    H4  the fault itself      S-curve: C gives no river-above flood day a chance
                              under 1%.
                              floor: in C no river-above day is given less than
                              the river-below curve gives its score; and C gives
                              under 1% to no more river-above flood days than A

Writes  reports/gauge_retrain_check.json               (the S-curve)
        reports/gauge_retrain_check_floor_failed.json  (the floor)
(the first run, G1 alone, is kept in reports/gauge_retrain_check_G1_failed.json)
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

import backtest_flood_when as B
import train_flood_when_gauge as T
from check_gauge_cleaning import NONE
from common import ROOT

REPORTS = {"sigmoid": ROOT / "reports" / "gauge_retrain_check.json",
           "floor": ROOT / "reports" / "gauge_retrain_check_floor_failed.json"}
GATES = (("H1", "C", "B", "the retrain alone"), ("H2", "B", "A", "the fix alone"),
         ("H3", "C", "A", "ships against live"))
KEY = ["station_code", "date"]


def tol(lead: int) -> float:
    return 0.005 if lead <= 3 else 0.010


def tables(clean: bool):
    keep = B.impossible_excursions, B.keying_slips
    if not clean:
        B.impossible_excursions = B.keying_slips = NONE
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            return T.build_tables(T.station_daily())
    finally:
        B.impossible_excursions, B.keying_slips = keep


def scored(df, feats: list[str] | None = None):
    """The lead's table with each row's raw out-of-fold score and year-fold."""
    feats = feats or T.OLD_FEATS
    df = df[df["g_frac"].notna()].reset_index(drop=True)
    folds = list(GroupKFold(n_splits=T.N_FOLDS).split(df, groups=df["date"].dt.year))
    fold = np.zeros(len(df), int)
    for k, (_, te) in enumerate(folds):
        fold[te] = k
    return df.assign(raw=T._raw_oof(df, feats, folds), grp=T.cal_group(df), fold=fold)


def chances(df, above: str):
    """Out-of-fold chance exactly as T.oof gives it, with the river-above
    curve fitted the given way; and what the plain river-below curve of the
    same label kind gives each row's score."""
    y, raw = df["flood"].to_numpy(), df["raw"].to_numpy()
    g, f = df["grp"].to_numpy(), df["fold"].to_numpy()
    p, below = np.full(len(df), np.nan), np.full(len(df), np.nan)
    keep = T.ABOVE
    try:
        for k in range(T.N_FOLDS):
            tr, te = f != k, f == k
            T.ABOVE = above
            p[te] = T.apply_cal(T.calibrate(raw[tr], y[tr], g[tr], "state"), raw[te], g[te])
            T.ABOVE = "isotonic"
            below[te] = T.apply_cal(T.calibrate(raw[tr], y[tr], g[tr], "state"), raw[te],
                                    g[te] - g[te] % 2)
    finally:
        T.ABOVE = keep
    return p, below


def auc(y, p) -> float:
    return float(roc_auc_score(y, p))


def skill(y, p) -> float:
    base = y.mean()
    return float(1 - np.mean((p - y) ** 2) / (base * (1 - base)))


def main(fix: str = "sigmoid") -> dict:
    t0 = time.time()
    fix_name = {"sigmoid": "S-curve", "floor": "floor"}[fix]
    print(f"GAUGE RETRAIN CHECK — A as it was, B + {fix_name}, C + {fix_name} + cleaned history (ships)\n")
    tb, rb = tables(False)
    ta, ra = tables(True)
    print(f"  tables built ({time.time()-t0:.0f}s)")
    moved = {c: (rb[c]["threshold"], ra[c]["threshold"], rb[c]["official"], ra[c]["official"])
             for c in ra if c in rb and (abs(rb[c]["threshold"] - ra[c]["threshold"]) > 1e-9
                                         or rb[c]["official"] != ra[c]["official"])}
    same = [c for c in ra if c in rb and c not in moved]
    print(f"  gauges: {len(ra)}; line unchanged at {len(same)}, moved at {len(moved)}")
    for c, (a, b, oa, ob) in moved.items():
        print(f"    {ra[c]['name']:<22} line {a:9.2f} -> {b:9.2f}   "
              f"{'official danger level' if oa else 'own wettest 2%'} -> "
              f"{'official danger level' if ob else 'own wettest 2%'}")

    out = {"protocol": "docs/design/FLOOD_WHEN_PILOT_PLAN.md " + {"sigmoid": "§13i", "floor": "§13h"}[fix],
           "fix": fix,
           "versions": {"A": "stepped curve, history as it was (the models of 2026-09-22)",
                        "B": f"{fix_name}, history as it was",
                        "C": f"{fix_name}, cleaned history (what would ship)",
                        "X": "stepped curve, cleaned history (failed G1)"},
           "tolerance": {"leads 1-3": tol(1), "leads 4-9": tol(9)},
           "gauges": len(ra), "line_unchanged": len(same),
           "line_moved": {ra[c]["name"]: {"before": a, "after": b, "official_before": bool(oa),
                                          "official_after": bool(ob)}
                          for c, (a, b, oa, ob) in moved.items()},
           "leads": {}}
    ok = {g[0]: True for g in GATES} | {"H2 river-below unchanged": True, "H4": True}
    for L in T.LEADS:
        sb, sa = scored(tb[L]), scored(ta[L])
        (pA, below_b), (pB, _) = chances(sb, "isotonic"), chances(sb, fix)
        (pX, below_a), (pC, _) = chances(sa, "isotonic"), chances(sa, fix)
        if L == 1 and T.ABOVE in ("isotonic", fix):     # this script's scoring IS the training script's
            assert np.array_equal(pX if T.ABOVE == "isotonic" else pC, T.oof(sa, T.OLD_FEATS, by="state"))
        # the fix leaves every river-below day's chance as it was
        touched = int((pA != pB)[sb["grp"] % 2 == 0].sum() + (pX != pC)[sa["grp"] % 2 == 0].sum())
        ok["H2 river-below unchanged"] &= touched == 0

        j = sa.assign(C=pC, X=pX, below=below_a).merge(
            sb.assign(A=pA, B=pB, below=below_b)[KEY + ["A", "B", "below", "grp", "flood"]],
            on=KEY, suffixes=("", "_before"))
        j = j[j["station_code"].isin(same)].reset_index(drop=True)
        y = j["flood"].to_numpy()                      # the CLEANED truth
        above = T.river_state(j) == 1
        res = {"gauge_days": int(len(j)), "flood_days": int(y.sum()),
               "river_below_days_touched_by_fix": touched}
        print(f"\n  lead {L}: {len(j):,} gauge-days both have, {int(y.sum()):,} flood days  "
              f"(tolerance {tol(L)})  ({time.time()-t0:.0f}s)")
        for name, m in (("all days", np.ones(len(j), bool)), ("onset only", ~above)):
            s = {v: {"auc": auc(y[m], j[v].to_numpy()[m]), "brier_skill": skill(y[m], j[v].to_numpy()[m])}
                 for v in "ABCX"}
            res[name] = {v: {k: round(x, 4) for k, x in d.items()} for v, d in s.items()}
            print(f"    {name:<11} AUC   " + "  ".join(f"{v} {s[v]['auc']:.4f}" for v in "ABCX")
                  + "     skill   " + "  ".join(f"{v} {s[v]['brier_skill']:.4f}" for v in "ABCX"))
            line = []
            for gate, new, old, _ in GATES:
                da = s[new]["auc"] - s[old]["auc"]
                ds = s[new]["brier_skill"] - s[old]["brier_skill"]
                passed = da >= -tol(L) and ds >= -tol(L)
                ok[gate] &= passed
                res[name][gate] = {"auc_change": round(da, 4), "brier_skill_change": round(ds, 4),
                                   "pass": bool(passed)}
                line.append(f"{gate} {new}-{old} {da:+.4f} / {ds:+.4f} {'ok' if passed else 'FAIL'}")
            print("                " + "    ".join(line))

        # H4, the fault itself
        f_above = above & (y == 1)
        own_above = j["grp_before"].to_numpy() % 2 == 1          # A's own river state
        under_a = own_above & (j["A"].to_numpy() < j["below_before"].to_numpy() - 1e-12)
        under_c = above & (j["C"].to_numpy() < j["below"].to_numpy() - 1e-12)
        u1_a, u1_c = int((f_above & (j["A"] < 0.01)).sum()), int((f_above & (j["C"] < 0.01)).sum())
        h4 = u1_c == 0 if fix == "sigmoid" else int(under_c.sum()) == 0 and u1_c <= u1_a
        ok["H4"] &= h4
        # the lowest-scored fifth of river-above days: chance said against what happened
        low = above & (j["raw"].to_numpy() <= np.quantile(j["raw"].to_numpy()[above], 0.2))
        said = {v: round(100 * float(j[v].to_numpy()[low].mean()), 1) for v in "AC"}
        happened = round(100 * float(y[low].mean()), 1)
        lowest = {v: round(100 * float(j[v].to_numpy()[above].min()), 2) for v in "AC"}
        res["H4"] = {"river_above_days": int(above.sum()), "river_above_flood_days": int(f_above.sum()),
                     "under_the_river_below_curve": {"A": int(under_a.sum()),
                                                     "A_of_which_floods": int((under_a & (y == 1)).sum()),
                                                     "C": int(under_c.sum())},
                     "river_above_flood_days_under_1pct": {"A": u1_a, "C": u1_c},
                     "lowest_scored_fifth": {"days": int(low.sum()), "said_pct": said,
                                             "happened_pct": happened},
                     "lowest_chance_given_pct": lowest, "pass": bool(h4)}
        print(f"    H4  river above: {int(above.sum())} days, {int(f_above.sum())} floods.  Given less than the "
              f"river-below curve: A {int(under_a.sum())} ({int((under_a & (y == 1)).sum())} floods) -> "
              f"C {int(under_c.sum())}.  Floods given under 1%: A {u1_a} -> C {u1_c}   "
              f"{'ok' if h4 else 'FAIL'}" + ("" if touched == 0 else f"   RIVER-BELOW DAYS TOUCHED: {touched}"))
        print(f"        lowest-scored fifth of river-above days ({int(low.sum())}): said A {said['A']}% / "
              f"C {said['C']}%, happened {happened}%.  Lowest chance any river-above day gets: "
              f"A {lowest['A']}% / C {lowest['C']}%")

        wa, wc = ({w["at_pct"]: w for w in T.grade(y, j[v].to_numpy())["warnings"]}[25] for v in "AC")
        res["warn_at_25pct"] = {"A": wa, "C": wc}
        print(f"    warn at 25%: caught {wa['floods_caught_pct']} -> {wc['floods_caught_pct']}%, "
              f"right {wa['warnings_right_pct']} -> {wc['warnings_right_pct']}%")
        # the gauges whose line moved: C only — a different event than before
        mv = sa.assign(C=pC)
        mv = mv[mv["station_code"].isin(moved)]
        if len(mv):
            g = T.grade(mv["flood"].to_numpy(), mv["C"].to_numpy())
            res["line_moved_C_only"] = g
            print(f"    line moved  C only: {len(mv):,} gauge-days, {g['n_flood_days']} flood days, "
                  f"AUC {g['auc']}, skill {g['brier_skill']}")
        out["leads"][str(L)] = res
    out["gates"] = {k: bool(v) for k, v in ok.items()}
    out["pass"] = all(ok.values())
    REPORT = REPORTS[fix]
    REPORT.write_text(json.dumps(out, indent=2))
    print("\n  " + "   ".join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in ok.items()))
    print(f"  {'ALL PASS' if out['pass'] else 'FAILED'}   wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else "sigmoid")["pass"] else 1)
