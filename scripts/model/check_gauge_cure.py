"""Does telling the gauge models each river's habit of staying high cure the
"river above its line told ~0%" fault, without costing anything? The rules
are fixed in docs/design/FLOOD_WHEN_PILOT_PLAN.md §13j; this script only
carries them out.

    python scripts/model/check_gauge_cure.py

    A   the models live: stepped curve, five inputs, the history as it was
    C   S-curve, five inputs, cleaned history — the improvement of §13i
    D   C + the `habit` input (train_flood_when_gauge.habit) — the cure

Scored and graded as check_gauge_retrain.py does: year-grouped, out of fold,
calibrated out of fold, against the CLEANED history as truth, on the
gauge-days both tables hold, at gauges whose line the cleaning does not move.

    K1  the cure against live       D against A  } AUC and Brier skill no more
    K2  the new input on its own    D against C  } than 0.005 lower at leads 1-3
                                                 } and 0.010 at 4-9, on all days
                                                 } and onset days (unrounded)
    K3  the fault itself   of the river-above days D gives under 5%, fewer than
                           1 in 10 flood; leads with under 20 such days are
                           judged together
    K4  the cause itself   among river-above days, D ranks flood days above
                           quiet days better than C does, at every lead

Writes  reports/gauge_cure_check.json
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

import check_gauge_retrain as R
import train_flood_when_gauge as T
from common import ROOT

REPORT = ROOT / "reports" / "gauge_cure_check.json"
GATES = (("K1", "D", "A", "the cure against live"), ("K2", "D", "C", "the new input on its own"))
KEY = R.KEY
LOW, LOW_MAY_FLOOD, LOW_MIN_DAYS = 0.05, 0.10, 20
CURE_FEATS = T.OLD_FEATS + [T.HABIT]


def main() -> dict:
    t0 = time.time()
    print("GAUGE CURE CHECK — A live, C S-curve + cleaned history, D = C + each river's habit\n")
    tb, rb = R.tables(False)
    ta, ra = R.tables(True)
    print(f"  tables built ({time.time()-t0:.0f}s)")
    moved = [c for c in ra if c in rb and (abs(rb[c]["threshold"] - ra[c]["threshold"]) > 1e-9
                                           or rb[c]["official"] != ra[c]["official"])]
    same = [c for c in ra if c in rb and c not in moved]
    print(f"  gauges: {len(ra)}; line unchanged at {len(same)}, moved at {len(moved)}")

    out = {"protocol": "docs/design/FLOOD_WHEN_PILOT_PLAN.md §13j",
           "versions": {"A": "stepped curve, five inputs, history as it was (the models of 2026-09-22)",
                        "C": "S-curve, five inputs, cleaned history (§13i)",
                        "D": "S-curve, five inputs + habit, cleaned history (the cure)"},
           "tolerance": {"leads 1-3": R.tol(1), "leads 4-9": R.tol(9)},
           "K3": {"under": LOW, "may_flood_less_than": LOW_MAY_FLOOD, "min_days_per_lead": LOW_MIN_DAYS},
           "gauges": len(ra), "line_unchanged": len(same), "leads": {}}
    ok = {g[0]: True for g in GATES} | {"K3": True, "K4": True}
    small = {v: [0, 0] for v in "ACD"}                 # K3: leads with too few days, judged together
    for L in T.LEADS:
        sb = R.scored(tb[L], T.OLD_FEATS)
        sa = R.scored(ta[L], T.OLD_FEATS)
        sd = R.scored(ta[L], CURE_FEATS)
        assert sa[KEY].equals(sd[KEY])
        pA, pC, pD = R.chances(sb, "isotonic")[0], R.chances(sa, "sigmoid")[0], R.chances(sd, "sigmoid")[0]
        if L == 1:        # this script's scoring IS the training script's
            keep, T.ABOVE = T.ABOVE, "sigmoid"
            try:
                assert np.array_equal(pD, T.oof(sd, CURE_FEATS, by="state"))
            finally:
                T.ABOVE = keep
        j = sa.assign(C=pC, D=pD, habit=T.habit(sd, np.ones(len(sd), bool))).merge(
            sb.assign(A=pA)[KEY + ["A"]], on=KEY)
        j = j[j["station_code"].isin(same)].reset_index(drop=True)
        y = j["flood"].to_numpy()                      # the CLEANED truth
        above = T.river_state(j) == 1
        P = {v: j[v].to_numpy() for v in "ACD"}
        res = {"gauge_days": int(len(j)), "flood_days": int(y.sum()),
               "river_above_days": int(above.sum()), "river_above_flood_days": int((above & (y == 1)).sum())}
        print(f"\n  lead {L}: {len(j):,} gauge-days, {int(y.sum()):,} flood days; river above on "
              f"{int(above.sum())}, {int((above & (y == 1)).sum())} of them floods  (tolerance {R.tol(L)})  "
              f"({time.time()-t0:.0f}s)")
        for name, m in (("all days", np.ones(len(j), bool)), ("onset only", ~above)):
            s = {v: {"auc": R.auc(y[m], P[v][m]), "brier_skill": R.skill(y[m], P[v][m])} for v in "ACD"}
            res[name] = {v: {k: round(x, 4) for k, x in d.items()} for v, d in s.items()}
            print(f"    {name:<11} AUC   " + "  ".join(f"{v} {s[v]['auc']:.4f}" for v in "ACD")
                  + "     skill   " + "  ".join(f"{v} {s[v]['brier_skill']:.4f}" for v in "ACD"))
            line = []
            for gate, new, old, _ in GATES:
                da = s[new]["auc"] - s[old]["auc"]
                ds = s[new]["brier_skill"] - s[old]["brier_skill"]
                passed = da >= -R.tol(L) and ds >= -R.tol(L)
                ok[gate] &= passed
                res[name][gate] = {"auc_change": round(da, 4), "brier_skill_change": round(ds, 4),
                                   "pass": bool(passed)}
                line.append(f"{gate} {new}-{old} {da:+.4f} / {ds:+.4f} {'ok' if passed else 'FAIL'}")
            print("                " + "    ".join(line))

        # K4, the cause: does the chance tell flood from quiet AMONG river-above days?
        within = {v: R.auc(y[above], P[v][above]) for v in "ACD"}
        k4 = within["D"] > within["C"]
        ok["K4"] &= k4
        res["K4"] = {"auc_within_river_above": {v: round(x, 4) for v, x in within.items()}, "pass": bool(k4)}
        # K3, the fault: river-above days given under 5%
        low = {v: (int((above & (P[v] < LOW)).sum()), int((above & (P[v] < LOW) & (y == 1)).sum())) for v in "ACD"}
        n, k = low["D"]
        if n >= LOW_MIN_DAYS:
            k3 = k / n < LOW_MAY_FLOOD
            ok["K3"] &= k3
            verdict = "ok" if k3 else "FAIL"
        else:
            k3, verdict = None, "judged with the other small leads"
        for v in "ACD":
            if low[v][0] < LOW_MIN_DAYS:
                small[v][0] += low[v][0]
                small[v][1] += low[v][1]
        res["K3"] = {"river_above_days_under_5pct": {v: {"days": low[v][0], "flooded": low[v][1]} for v in "ACD"},
                     "pass": k3}
        under1 = {v: int((above & (y == 1) & (P[v] < 0.01)).sum()) for v in "ACD"}
        lowest = {v: round(100 * float(P[v][above].min()), 2) for v in "ACD"}
        res["reported"] = {"river_above_flood_days_under_1pct": under1, "lowest_chance_given_pct": lowest}
        print(f"    K4  ranking among river-above days   " + "  ".join(f"{v} {within[v]:.4f}" for v in "ACD")
              + f"   {'ok' if k4 else 'FAIL'}")
        print("    K3  river-above days given under 5%: "
              + "   ".join(f"{v} {low[v][0]} days, {low[v][1]} flooded"
                           + (f" ({100*low[v][1]/low[v][0]:.0f}%)" if low[v][0] else "") for v in "ACD")
              + f"   {verdict}")
        print(f"        floods given under 1%: " + " / ".join(f"{v} {under1[v]}" for v in "ACD")
              + "    lowest chance any river-above day gets: " + " / ".join(f"{v} {lowest[v]}%" for v in "ACD"))
        # per gauge: the chance said against the share that stayed above
        g = j[above].assign(y=y[above]).groupby("station_code").agg(
            days=("y", "size"), stayed=("y", "mean"), A=("A", "mean"), C=("C", "mean"), D=("D", "mean"),
            habit=("habit", "mean"))
        g = g[g["days"] >= 15].sort_values("stayed")
        gap = {v: round(100 * float((g[v] - g["stayed"]).abs().mean()), 1) for v in "ACD"}
        res["per_gauge"] = {"gauges_with_15_days": int(len(g)), "mean_gap_said_vs_stayed_pts": gap,
                            "rows": {ra[c]["name"]: {"days": int(r.days), "stayed_pct": round(100 * r.stayed, 1),
                                                     "said_pct": {v: round(100 * r[v], 1) for v in "ACD"},
                                                     "habit_all_years_pct": round(100 * r.habit, 1)}
                                     for c, r in g.iterrows()}}
        print(f"        per gauge ({len(g)} with 15+ river-above days): average gap between the chance said and "
              f"the share that stayed above — " + " / ".join(f"{v} {gap[v]} pts" for v in "ACD"))
        if L in (2, 4, 6):
            print("        stayed / D said:  " + "   ".join(
                f"{ra[c]['name']} {100*r.stayed:.0f}/{100*r.D:.0f}" for c, r in g.iterrows()))
        mv = sd.assign(D=pD)
        mv = mv[mv["station_code"].isin(moved)]
        if len(mv):
            gr = T.grade(mv["flood"].to_numpy(), mv["D"].to_numpy())
            res["line_moved_D_only"] = gr
            print(f"        line moved, D only: {len(mv):,} gauge-days, {gr['n_flood_days']} flood days, "
                  f"AUC {gr['auc']}, skill {gr['brier_skill']}")
        out["leads"][str(L)] = res

    n, k = small["D"]
    if n:
        k3 = k / n < LOW_MAY_FLOOD
        ok["K3"] &= k3
        print(f"\n  K3, the small leads together: " + "   ".join(
            f"{v} {small[v][0]} days, {small[v][1]} flooded" for v in "ACD") + f"   {'ok' if k3 else 'FAIL'}")
    out["K3_small_leads_together"] = {v: {"days": small[v][0], "flooded": small[v][1]} for v in "ACD"}
    out["gates"] = {k: bool(v) for k, v in ok.items()}
    out["pass"] = all(ok.values())
    REPORT.write_text(json.dumps(out, indent=2))
    print("\n  " + "   ".join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in ok.items()))
    print(f"  {'ALL PASS' if out['pass'] else 'FAILED'}   wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    sys.exit(0 if main()["pass"] else 1)
