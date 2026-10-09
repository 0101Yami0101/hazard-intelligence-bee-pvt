"""Does reading the river's own week cure the "river above its line told ~0%"
fault — and can it carry a forecast of the level itself? The rules are fixed
in docs/design/FLOOD_WHEN_PILOT_PLAN.md §14; this script only carries them
out.

    python scripts/model/check_gauge_week.py

Chance model (same rows, truth and 27 gauges as check_gauge_retrain.py):
    A   the models live: stepped curve, five inputs, the history as it was
    C   S-curve, five inputs, cleaned history — the improvement of §13i
    W   C + the six "week" inputs (gauge_week.week_inputs)

    W1  W against A   } AUC and Brier skill no more than 0.005 lower at leads
    W2  W against C   } 1-3 and 0.010 at 4-9; all days and onset days
    W3  the fault     of the river-above days W gives under 5%, fewer than 1
                      in 10 flood (leads with under 20 such days together)
    W4  the cause     among river-above days W ranks better than C at each of
                      leads 1-4, and no more than 0.010 worse at 5-9

Level model (every gauge and row of the cleaned history, leads 1 and 2):
    L1  the middle line's average miss is smaller than "no change", on all
        days and on river-above days
    L2  the low-high range holds 75-85% of outcomes on all days and 70-90%
        on river-above days
    L3  whole range above the line: at least 3 in 4 cross and W averages at
        least 50%; whole range below: under 1 in 10 cross and W averages
        under 10%
    Leads 3-7 are reported: the line may be drawn up to the last lead,
    counting from 1, at which L1 and L2 both hold.

Writes  reports/gauge_week_check.json
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

import check_gauge_retrain as R
import gauge_week as W
import train_flood_when_gauge as T
from common import ROOT

REPORT = ROOT / "reports" / "gauge_week_check.json"
KEY = R.KEY
FEATS_W = T.OLD_FEATS + T.WEEK_FEATS
LOW, LOW_MAY_FLOOD, LOW_MIN_DAYS = 0.05, 0.10, 20
LEVEL_LEADS, LEVEL_GATED = range(1, 8), (1, 2)


def chance_part(L, sb, sa, sw, same, ok, small) -> dict:
    pA, pC, pW = R.chances(sb, "isotonic")[0], R.chances(sa, "sigmoid")[0], R.chances(sw, "sigmoid")[0]
    if L == 1 and T.ABOVE == "sigmoid":        # this script's scoring IS the training script's
        assert np.array_equal(pW, T.oof(sw, FEATS_W, by="state"))
    j = sa.assign(C=pC, W=pW).merge(sb.assign(A=pA)[KEY + ["A"]], on=KEY)
    j = j[j["station_code"].isin(same)].reset_index(drop=True)
    y = j["flood"].to_numpy()                          # the CLEANED truth
    above = T.river_state(j) == 1
    P = {v: j[v].to_numpy() for v in "ACW"}
    res = {"gauge_days": int(len(j)), "flood_days": int(y.sum()), "river_above_days": int(above.sum()),
           "river_above_flood_days": int((above & (y == 1)).sum())}
    print(f"\n  lead {L}: {len(j):,} gauge-days, {int(y.sum()):,} flood days; river above on {int(above.sum())}, "
          f"{int((above & (y == 1)).sum())} of them floods  (tolerance {R.tol(L)})")
    for name, m in (("all days", np.ones(len(j), bool)), ("onset only", ~above)):
        s = {v: {"auc": R.auc(y[m], P[v][m]), "brier_skill": R.skill(y[m], P[v][m])} for v in "ACW"}
        res[name] = {v: {k: round(x, 4) for k, x in d.items()} for v, d in s.items()}
        line = []
        for gate, old in (("W1", "A"), ("W2", "C")):
            da, ds = s["W"]["auc"] - s[old]["auc"], s["W"]["brier_skill"] - s[old]["brier_skill"]
            passed = da >= -R.tol(L) and ds >= -R.tol(L)
            ok[gate] &= passed
            res[name][gate] = {"auc_change": round(da, 4), "brier_skill_change": round(ds, 4), "pass": bool(passed)}
            line.append(f"{gate} W-{old} {da:+.4f} / {ds:+.4f} {'ok' if passed else 'FAIL'}")
        print(f"    {name:<11} AUC " + " ".join(f"{v} {s[v]['auc']:.4f}" for v in "ACW") + "   skill "
              + " ".join(f"{v} {s[v]['brier_skill']:.4f}" for v in "ACW") + "   " + "   ".join(line))
    within = {v: R.auc(y[above], P[v][above]) for v in "ACW"}
    d4 = within["W"] - within["C"]
    w4 = d4 > 0 if L <= 4 else d4 >= -0.010
    ok["W4"] &= w4
    res["W4"] = {"auc_within_river_above": {v: round(x, 4) for v, x in within.items()}, "pass": bool(w4)}
    low = {v: (int((above & (P[v] < LOW)).sum()), int((above & (P[v] < LOW) & (y == 1)).sum())) for v in "ACW"}
    n, k = low["W"]
    if n >= LOW_MIN_DAYS:
        w3 = k / n < LOW_MAY_FLOOD
        ok["W3"] &= w3
        verdict = "ok" if w3 else "FAIL"
    else:
        w3, verdict = None, "judged with the other small leads"
    for v in "ACW":
        if low[v][0] < LOW_MIN_DAYS:
            small[v][0] += low[v][0]
            small[v][1] += low[v][1]
    under1 = {v: int((above & (y == 1) & (P[v] < 0.01)).sum()) for v in "ACW"}
    res["W3"] = {"river_above_days_under_5pct": {v: {"days": low[v][0], "flooded": low[v][1]} for v in "ACW"},
                 "pass": w3}
    res["reported"] = {"river_above_flood_days_under_1pct": under1,
                       "lowest_chance_given_pct": {v: round(100 * float(P[v][above].min()), 2) for v in "ACW"}}
    print(f"    W4  ranking among river-above days  " + " ".join(f"{v} {within[v]:.4f}" for v in "ACW")
          + f"   {'ok' if w4 else 'FAIL'}")
    print("    W3  river-above days given under 5%: " + "   ".join(
        f"{v} {low[v][0]} days, {low[v][1]} flooded" + (f" ({100*low[v][1]/low[v][0]:.0f}%)" if low[v][0] else "")
        for v in "ACW") + f"   {verdict}      floods under 1%: " + " / ".join(f"{v} {under1[v]}" for v in "ACW"))
    return res, pW


def level_part(L, sw, pW, registry, ok) -> dict:
    """Every gauge, every row of the cleaned history."""
    y = W.change(sw)
    q = W.level_oof(sw, FEATS_W)
    lo, mid, hi = q[:, 0], q[:, 1], q[:, 2]
    now = sw["g_frac"].to_numpy()
    above = T.river_state(sw) == 1
    crossed = sw["flood"].to_numpy() == 1
    span = sw["station_code"].map(lambda c: registry[c]["threshold"] - registry[c]["base"]).to_numpy()
    cwc = (sw["network"] == "CWC").to_numpy()
    res = {"gauge_days": int(len(sw)), "river_above_days": int(above.sum())}
    out_ok = {}
    for name, m in (("all days", np.ones(len(sw), bool)), ("river above", above)):
        miss, still = float(np.mean(np.abs(mid[m] - y[m]))), float(np.mean(np.abs(y[m])))
        cover = float(np.mean((lo[m] <= y[m]) & (y[m] <= hi[m])))
        lo_c, hi_c = (0.75, 0.85) if name == "all days" else (0.70, 0.90)
        l1, l2 = miss < still, lo_c <= cover <= hi_c
        out_ok[name] = (l1, l2)
        mm = m & cwc
        res[name] = {"days": int(m.sum()), "avg_miss_middle_line": round(miss, 4), "avg_miss_no_change": round(still, 4),
                     "miss_vs_no_change_pct": round(100 * (miss / still - 1), 1), "range_holds_pct": round(100 * cover, 1),
                     "avg_range_width": round(float(np.mean(hi[m] - lo[m])), 4),
                     "cwc_avg_miss_metres": round(float(np.mean(np.abs(mid[mm] - y[mm]) * span[mm])), 3),
                     "cwc_avg_miss_no_change_metres": round(float(np.mean(np.abs(y[mm]) * span[mm])), 3),
                     "L1": bool(l1), "L2": bool(l2)}
    up, down = now + lo >= 1, now + hi < 1
    l3 = {"range_wholly_above": {"days": int(up.sum()), "crossed_pct": round(100 * float(crossed[up].mean()), 1) if up.any() else None,
                                 "W_avg_pct": round(100 * float(pW[up].mean()), 1) if up.any() else None},
          "range_wholly_below": {"days": int(down.sum()), "crossed_pct": round(100 * float(crossed[down].mean()), 2),
                                 "W_avg_pct": round(100 * float(pW[down].mean()), 2)}}
    l3_ok = bool(up.any() and crossed[up].mean() >= 0.75 and pW[up].mean() >= 0.50
                 and crossed[down].mean() < 0.10 and pW[down].mean() < 0.10)
    res["L3"] = {**l3, "pass": l3_ok}
    l1 = out_ok["all days"][0] and out_ok["river above"][0]
    l2 = out_ok["all days"][1] and out_ok["river above"][1]
    res["L1"], res["L2"] = bool(l1), bool(l2)
    if L in LEVEL_GATED:
        ok["L1"] &= l1
        ok["L2"] &= l2
        ok["L3"] &= l3_ok
    a, r = res["all days"], res["river above"]
    print(f"\n  level, lead {L}{'' if L in LEVEL_GATED else ' (reported)'}: "
          f"all days — miss {a['avg_miss_middle_line']} vs no-change {a['avg_miss_no_change']} ({a['miss_vs_no_change_pct']:+}%), "
          f"range holds {a['range_holds_pct']}%;  river above ({r['days']}) — miss {r['avg_miss_middle_line']} vs "
          f"{r['avg_miss_no_change']} ({r['miss_vs_no_change_pct']:+}%), range holds {r['range_holds_pct']}%"
          f"   L1 {'ok' if l1 else 'FAIL'}  L2 {'ok' if l2 else 'FAIL'}")
    print(f"      CWC gauges, in metres: all days miss {a['cwc_avg_miss_metres']} m vs no-change "
          f"{a['cwc_avg_miss_no_change_metres']} m; river above {r['cwc_avg_miss_metres']} m vs {r['cwc_avg_miss_no_change_metres']} m")
    print(f"      L3  range wholly above the line: {l3['range_wholly_above']['days']} days, "
          f"{l3['range_wholly_above']['crossed_pct']}% crossed, W said {l3['range_wholly_above']['W_avg_pct']}%;  wholly below: "
          f"{l3['range_wholly_below']['days']:,} days, {l3['range_wholly_below']['crossed_pct']}% crossed, "
          f"W said {l3['range_wholly_below']['W_avg_pct']}%   {'ok' if l3_ok else 'FAIL'}")
    return res


def main() -> dict:
    t0 = time.time()
    print("GAUGE WEEK CHECK — A live, C improvement, W = C + the river's own week; and the level model\n")
    tb, rb = R.tables(False)
    with contextlib.redirect_stdout(io.StringIO()):
        ta, ra = W.build_tables(W.station_days())
    print(f"  tables built ({time.time()-t0:.0f}s)")
    moved = [c for c in ra if c in rb and (abs(rb[c]["threshold"] - ra[c]["threshold"]) > 1e-9
                                           or rb[c]["official"] != ra[c]["official"])]
    same = [c for c in ra if c in rb and c not in moved]
    out = {"protocol": "docs/design/FLOOD_WHEN_PILOT_PLAN.md §14",
           "versions": {"A": "stepped curve, five inputs, history as it was (the models of 2026-09-22)",
                        "C": "S-curve, five inputs, cleaned history (§13i)",
                        "W": "S-curve, five inputs + the six week inputs, cleaned history"},
           "week_inputs": T.WEEK_FEATS, "gauges": len(ra), "line_unchanged": len(same), "chance": {}, "level": {}}
    ok = {k: True for k in ("W1", "W2", "W3", "W4", "L1", "L2", "L3")}
    small = {v: [0, 0] for v in "ACW"}
    for L in T.LEADS:
        sb, sa, sw = R.scored(tb[L], T.OLD_FEATS), R.scored(ta[L], T.OLD_FEATS), R.scored(ta[L], FEATS_W)
        assert sa[KEY].equals(sw[KEY])
        out["chance"][str(L)], pW = chance_part(L, sb, sa, sw, same, ok, small)
        if L in LEVEL_LEADS:
            out["level"][str(L)] = level_part(L, sw, pW, ra, ok)
        print(f"      ({time.time()-t0:.0f}s)")
    n, k = small["W"]
    if n:
        w3 = k / n < LOW_MAY_FLOOD
        ok["W3"] &= w3
        print(f"\n  W3, the small leads together: " + "   ".join(
            f"{v} {small[v][0]} days, {small[v][1]} flooded" for v in "ACW") + f"   {'ok' if w3 else 'FAIL'}")
    out["W3_small_leads_together"] = {v: {"days": small[v][0], "flooded": small[v][1]} for v in "ACW"}
    far = 0
    for L in LEVEL_LEADS:                       # how far ahead the line may be drawn
        if out["level"][str(L)]["L1"] and out["level"][str(L)]["L2"]:
            far = L
        else:
            break
    out["level_line_may_be_drawn_to_lead"] = far
    out["gates"] = {k: bool(v) for k, v in ok.items()}
    out["chance_pass"] = all(ok[k] for k in ("W1", "W2", "W3", "W4"))
    out["level_pass"] = all(ok[k] for k in ("L1", "L2", "L3"))
    REPORT.write_text(json.dumps(out, indent=2))
    print("\n  " + "   ".join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in ok.items()))
    print(f"  chance model: {'PASS' if out['chance_pass'] else 'FAILED'}    level model: "
          f"{'PASS' if out['level_pass'] else 'FAILED'}    L1 and L2 both hold from lead 1 up to lead {far}")
    print(f"  wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    r = main()
    sys.exit(0 if r["chance_pass"] and r["level_pass"] else 1)
