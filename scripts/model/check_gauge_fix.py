"""Do the gauge upstream, melt water and the level line cure the "river above
its line told ~0%" fault? The design and every rule are fixed in
docs/design/FLOOD_WHEN_PILOT_PLAN.md §17; this script only carries them out.

    python scripts/model/check_gauge_fix.py

    W    the models live (five inputs + the river's week, S-curve) — §14
    +U   W + the gauge upstream          +M   W + melt water
    F    W + whichever of U, M is kept
    X    F + LV: the level line's position in the S-curve of river-above days

    Y  the pattern holds year to year (else the ingredient is dropped first)
    K  an ingredient is kept: no harm, and better Brier skill among
       river-above days at 3 or more of leads 1-4 (level model: middle
       line's miss not larger at leads 1 and 2)
    N  the final model does no harm against W, at every lead
    C  of the river-above days given under 5%, fewer than 1 in 10 flood
    L  L1-L3 of §14c at leads 1 and 2, with the final chance model

Writes  reports/gauge_fix_check.json
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
import pandas as pd
from scipy.stats import spearmanr

import check_gauge_retrain as R
import gauge_extra as X
import gauge_week as W
import train_flood_when_gauge as T
from common import ROOT

REPORT = ROOT / "reports" / "gauge_fix_check.json"
KEY = R.KEY
FEATS_W = T.OLD_FEATS + T.WEEK_FEATS
LOW, LOW_MAY_FLOOD, LOW_MIN_DAYS = 0.05, 0.10, 20
K_LEADS, LEVEL_LEADS, LEVEL_GATED = (1, 2, 3, 4), tuple(range(1, 8)), (1, 2)
Y_MIN_DAYS, Y_U_SHARE, Y_M_SHARE, MELT_MATTERS_MM = 30, 0.9, 2 / 3, 5.0


# ── Y: does the pattern hold from one year to the next ───────────────────
def year_check(t1: pd.DataFrame, registry: dict) -> dict:
    out = {}
    rows = []
    for code in X.UPSTREAM:
        g = t1[(t1["station_code"] == code) & t1["up_frac"].notna() & t1["level"].notna()]
        for yr, d in g.groupby(g["date"].dt.year):
            if len(d) >= Y_MIN_DAYS and d["up_frac"].nunique() > 1 and d["level"].nunique() > 1:
                rows.append((registry[code]["name"], int(yr), float(spearmanr(d["up_frac"], d["level"])[0])))
    u = pd.DataFrame(rows, columns=["gauge", "year", "r"])
    out["U"] = {"pair_years": int(len(u)), "moving_together": int((u["r"] > 0).sum()),
                "share": round(float((u["r"] > 0).mean()), 3) if len(u) else None,
                "median_r": round(float(u["r"].median()), 3) if len(u) else None,
                "by_gauge": {n: f"{int((d['r'] > 0).sum())} of {len(d)}" for n, d in u.groupby("gauge")},
                "pass": bool(len(u) and (u["r"] > 0).mean() >= Y_U_SHARE)}
    rows, matter = [], []
    season = t1[t1["date"].dt.month.between(4, 7) & t1["melt7"].notna() & t1["level"].notna()]
    for code, g in season.groupby("station_code"):
        if g["melt7"].mean() < MELT_MATTERS_MM:
            continue
        matter.append(registry[code]["name"])
        for yr, d in g.groupby(g["date"].dt.year):
            if len(d) >= Y_MIN_DAYS and d["melt7"].nunique() > 1 and d["level"].nunique() > 1:
                rows.append((registry[code]["name"], int(yr), float(spearmanr(d["melt7"], d["level"])[0])))
    m = pd.DataFrame(rows, columns=["gauge", "year", "r"])
    out["M"] = {"gauges_where_melt_matters": matter, "gauge_years": int(len(m)),
                "moving_together": int((m["r"] > 0).sum()),
                "share": round(float((m["r"] > 0).mean()), 3) if len(m) else None,
                "median_r": round(float(m["r"].median()), 3) if len(m) else None,
                "by_gauge": {n: f"{int((d['r'] > 0).sum())} of {len(d)}" for n, d in m.groupby("gauge")},
                "pass": bool(len(m) and (m["r"] > 0).mean() >= Y_M_SHARE)}
    return out


# ── mechanics: no input may read the future ──────────────────────────────
def mechanics(stations, registry, tx) -> None:
    """Change every reading from a date on and nothing dated before the
    target moves; the upstream input at lead L is the upstream reading L
    days before the target; the melt input is the value 16 days before."""
    cut = pd.Timestamp("2019-07-01")
    st2 = []
    for s in stations:
        d = s["days"].copy()
        d.loc[d.index >= cut, ["high", "first", "last"]] += 3.0
        st2.append({**s, "days": d, "daily": d["high"]})
    up, up2 = X.upstream_inputs(stations, registry), X.upstream_inputs(st2, registry)
    for code in up:
        a, b = up[code][up[code].index < cut], up2[code][up2[code].index < cut]
        assert a.equals(b), code
    code = "005-UBDDIB"                                   # Passighat <- Pangin
    g = tx[2][(tx[2]["station_code"] == code) & tx[2]["up_frac"].notna()].iloc[-300]
    raw = up[code].loc[g["date"] - pd.Timedelta(days=2)]
    assert abs(raw["up_frac"] - g["up_frac"]) < 1e-12
    melt = X.melt_inputs(registry)[code]
    assert abs(melt.loc[g["date"] - pd.Timedelta(days=X.MELT_LAG), "melt7"] - g["melt7"]) < 1e-9
    print("  mechanics: no input reads past its own day; lags are as written")


# ── scoring ──────────────────────────────────────────────────────────────
def stats(y, p, above) -> dict:
    onset = ~above
    low = above & (p < LOW)
    return {"auc_all": R.auc(y, p), "skill_all": R.skill(y, p),
            "auc_onset": R.auc(y[onset], p[onset]), "skill_onset": R.skill(y[onset], p[onset]),
            "skill_above": R.skill(y[above], p[above]), "auc_above": R.auc(y[above], p[above]),
            "low_days": int(low.sum()), "low_flooded": int((low & (y == 1)).sum()),
            "above_floods_under_1pct": int((above & (y == 1) & (p < 0.01)).sum())}


def no_harm(a: dict, base: dict, L: int) -> bool:
    return all(a[k] - base[k] >= -R.tol(L) for k in ("auc_all", "skill_all", "auc_onset", "skill_onset"))


def keep(S: dict, v: str, base: str) -> dict:
    harm = [L for L in T.LEADS if not no_harm(S[L][v], S[L][base], L)]
    better = [L for L in K_LEADS if S[L][v]["skill_above"] > S[L][base]["skill_above"]]
    return {"no_harm": not harm, "harm_at_leads": harm, "better_among_river_above_at_leads": better,
            "kept": bool(not harm and len(better) >= 3)}


def fault(S: dict, v: str) -> dict:
    ok, small, per = True, [0, 0], {}
    for L in T.LEADS:
        n, k = S[L][v]["low_days"], S[L][v]["low_flooded"]
        if n >= LOW_MIN_DAYS:
            p = k / n < LOW_MAY_FLOOD
            ok &= p
            per[str(L)] = {"days": n, "flooded": k, "pct": round(100 * k / n, 1), "pass": bool(p)}
        else:
            small[0] += n
            small[1] += k
            per[str(L)] = {"days": n, "flooded": k, "pass": None}
    if small[0]:
        p = small[1] / small[0] < LOW_MAY_FLOOD
        ok &= p
        per["small leads together"] = {"days": small[0], "flooded": small[1], "pass": bool(p)}
    return {"per_lead": per, "pass": bool(ok)}


def level_stats(df, q, registry) -> dict:
    y, mid = W.change(df), q[:, 1]
    above = T.river_state(df) == 1
    span = df["station_code"].map(lambda c: registry[c]["threshold"] - registry[c]["base"]).to_numpy()
    cwc = (df["network"] == "CWC").to_numpy()
    out = {}
    for name, m in (("all", np.ones(len(df), bool)), ("above", above)):
        mm = m & cwc
        out[name] = {"days": int(m.sum()), "miss": float(np.mean(np.abs(mid[m] - y[m]))),
                     "miss_no_change": float(np.mean(np.abs(y[m]))),
                     "holds": float(np.mean((q[m, 0] <= y[m]) & (y[m] <= q[m, 2]))),
                     "cwc_miss_m": float(np.mean(np.abs(mid[mm] - y[mm]) * span[mm]))}
    return out


def main() -> dict:
    t0 = time.time()
    print("GAUGE FIX CHECK — upstream gauges (U), melt water (M), the level line in the chance (LV)\n")
    T.FREE_FEATS = set(T.FREE_FEATS) | X.FREE
    with contextlib.redirect_stdout(io.StringIO()):
        stations = W.station_days()
        ta, registry = W.build_tables(stations)
    tx = X.add_inputs(ta, stations, registry)
    print(f"  tables built: {len(registry)} gauges ({time.time()-t0:.0f}s)")
    mechanics(stations, registry, tx)
    out = {"protocol": "docs/design/FLOOD_WHEN_PILOT_PLAN.md §17", "gauges": len(registry),
           "upstream_pairs": {registry[c]["name"]: [registry[u]["name"] for u in ups if u in registry]
                              for c, ups in X.UPSTREAM.items() if c in registry}}

    # Y ─ before any model
    yc = year_check(tx[1], registry)
    out["Y"] = yc
    for k in "UM":
        print(f"  Y, {k}: {yc[k]['moving_together']} of {yc[k].get('pair_years', yc[k].get('gauge_years'))} "
              f"gauge-years move together ({yc[k]['share']}), median r {yc[k]['median_r']}   "
              f"{'ok' if yc[k]['pass'] else 'FAIL — dropped'}")
    cand = [k for k in "UM" if yc[k]["pass"]]
    feats = {"W": FEATS_W, "U": FEATS_W + X.U_FEATS, "M": FEATS_W + X.M_FEATS}

    # pass 1 ─ W, +U, +M at every lead
    S = {L: {} for L in T.LEADS}
    scored, P = {}, {}
    for L in T.LEADS:
        for v in ["W"] + cand:
            s = R.scored(tx[L], feats[v])
            if v == "W":
                scored[L] = {"W": s}
                y, above = s["flood"].to_numpy(), T.river_state(s) == 1
            else:
                assert s[KEY].equals(scored[L]["W"][KEY])
                scored[L][v] = s
            P[(L, v)] = R.chances(s, "sigmoid")[0]
            S[L][v] = stats(y, P[(L, v)], above)
        print(f"  lead {L}: " + "   ".join(
            f"{v} skill {S[L][v]['skill_all']:.4f} onset {S[L][v]['skill_onset']:.4f} above {S[L][v]['skill_above']:.4f} "
            f"low {S[L][v]['low_days']}/{S[L][v]['low_flooded']}" for v in S[L]) + f"   ({time.time()-t0:.0f}s)")
    K = {v: keep(S, v, "W") for v in cand}
    for v in cand:
        print(f"  K, {v}: no harm {K[v]['no_harm']} (harm at {K[v]['harm_at_leads']}), better among river-above at "
              f"leads {K[v]['better_among_river_above_at_leads']}   {'KEPT' if K[v]['kept'] else 'not kept'}")
    kept = [v for v in cand if K[v]["kept"]]

    # the level model: is each ingredient kept there
    LQ, LS = {}, {}
    for L in LEVEL_GATED:
        for v in ["W"] + cand:
            LQ[(L, v)] = W.level_oof(scored[L]["W"], feats[v])
            LS[(L, v)] = level_stats(scored[L]["W"], LQ[(L, v)], registry)
    KL = {}
    for v in cand:
        notworse = all(LS[(L, v)][n]["miss"] <= LS[(L, "W")][n]["miss"] for L in LEVEL_GATED for n in ("all", "above"))
        KL[v] = {"kept": bool(notworse), "miss": {f"{L}/{n}": [round(LS[(L, 'W')][n]["miss"], 4), round(LS[(L, v)][n]["miss"], 4)]
                                                 for L in LEVEL_GATED for n in ("all", "above")}}
        print(f"  K (level model), {v}: miss W -> {v}  {KL[v]['miss']}   {'KEPT' if notworse else 'not kept'}")
    lkept = [v for v in cand if KL[v]["kept"]]
    f_feats = FEATS_W + [c for v in kept for c in (X.U_FEATS if v == "U" else X.M_FEATS)]
    l_feats = FEATS_W + [c for v in lkept for c in (X.U_FEATS if v == "U" else X.M_FEATS)]
    out["K"] = {"chance": K, "level": KL, "kept_in_chance_model": kept, "kept_in_level_model": lkept}

    # F ─ the kept inputs together; then LV on top
    for L in T.LEADS:
        if len(kept) == 1:
            scored[L]["F"], P[(L, "F")], S[L]["F"] = scored[L][kept[0]], P[(L, kept[0])], S[L][kept[0]]
        elif not kept:
            scored[L]["F"], P[(L, "F")], S[L]["F"] = scored[L]["W"], P[(L, "W")], S[L]["W"]
        else:
            s = R.scored(tx[L], f_feats)
            scored[L]["F"], P[(L, "F")] = s, R.chances(s, "sigmoid")[0]
            S[L]["F"] = stats(s["flood"].to_numpy(), P[(L, "F")], T.river_state(s) == 1)
    level, lv_fit = {}, {}
    for L in T.LEADS:
        s = scored[L]["F"]
        y, above = s["flood"].to_numpy(), T.river_state(s) == 1
        if L in LEVEL_LEADS:
            key = (L, "W") if not lkept else (L, lkept[0]) if len(lkept) == 1 else None
            q = LQ[key] if key in LQ else W.level_oof(s, l_feats)
            level[L] = q
            z = X.level_z(s["g_frac"].to_numpy(), q)
            P[(L, "X")] = X.lv_chances(s, z)
            c = X.calibrate_lv(s["raw"].to_numpy(), z, y, s["grp"].to_numpy())["lv"]
            lv_fit[str(L)] = {str(k): [round(v, 3) for v in p] for k, p in c.items()}
        else:
            P[(L, "X")] = P[(L, "F")]
        S[L]["X"] = stats(y, P[(L, "X")], above)
        print(f"  lead {L}: F skill {S[L]['F']['skill_all']:.4f} above {S[L]['F']['skill_above']:.4f} low "
              f"{S[L]['F']['low_days']}/{S[L]['F']['low_flooded']}   X skill {S[L]['X']['skill_all']:.4f} above "
              f"{S[L]['X']['skill_above']:.4f} low {S[L]['X']['low_days']}/{S[L]['X']['low_flooded']}"
              f"   LV a,c,b {lv_fit.get(str(L))}   ({time.time()-t0:.0f}s)")
    K["LV"] = keep(S, "X", "F")
    print(f"  K, LV: no harm {K['LV']['no_harm']}, better among river-above at leads "
          f"{K['LV']['better_among_river_above_at_leads']}   {'KEPT' if K['LV']['kept'] else 'not kept'}")
    final = "X" if K["LV"]["kept"] else "F"
    out["lv_fitted_numbers_a_c_b_by_group"] = lv_fit

    # the gates on the final model
    N = {str(L): no_harm(S[L][final], S[L]["W"], L) for L in T.LEADS}
    C = {v: fault(S, v) for v in dict.fromkeys(["W", "F", "X", final])}
    lgate = {}
    for L in LEVEL_LEADS:
        s, q = scored[L]["F"], level[L]
        st = level_stats(s, q, registry)
        now, crossed, p = s["g_frac"].to_numpy(), s["flood"].to_numpy() == 1, P[(L, final)]
        up, down = now + q[:, 0] >= 1, now + q[:, 2] < 1
        l1 = st["all"]["miss"] < st["all"]["miss_no_change"] and st["above"]["miss"] < st["above"]["miss_no_change"]
        l2 = 0.75 <= st["all"]["holds"] <= 0.85 and 0.70 <= st["above"]["holds"] <= 0.90
        l3 = bool(up.any() and crossed[up].mean() >= 0.75 and p[up].mean() >= 0.50
                  and crossed[down].mean() < 0.10 and p[down].mean() < 0.10)
        lgate[str(L)] = {"miss_all": round(st["all"]["miss"], 4), "miss_above": round(st["above"]["miss"], 4),
                         "cwc_miss_m_all": round(st["all"]["cwc_miss_m"], 3), "cwc_miss_m_above": round(st["above"]["cwc_miss_m"], 3),
                         "holds_all": round(100 * st["all"]["holds"], 1), "holds_above": round(100 * st["above"]["holds"], 1),
                         "range_wholly_above": {"days": int(up.sum()), "crossed_pct": round(100 * float(crossed[up].mean()), 1) if up.any() else None,
                                                "chance_avg_pct": round(100 * float(p[up].mean()), 1) if up.any() else None},
                         "range_wholly_below": {"days": int(down.sum()), "crossed_pct": round(100 * float(crossed[down].mean()), 2),
                                                "chance_avg_pct": round(100 * float(p[down].mean()), 2)},
                         "L1": bool(l1), "L2": bool(l2), "L3": l3}
    gates = {"N": all(N.values()), "C": C[final]["pass"],
             "L": all(lgate[str(L)][k] for L in LEVEL_GATED for k in ("L1", "L2", "L3"))}
    far = 0
    for L in LEVEL_LEADS:
        if all(lgate[str(L)][k] for k in ("L1", "L2", "L3")):
            far = L
        else:
            break
    out.update({"final": final, "final_inputs_chance": f_feats, "final_inputs_level": l_feats,
                "by_lead": {str(L): {v: {k: (round(x, 4) if isinstance(x, float) else x) for k, x in d.items()}
                                     for v, d in S[L].items()} for L in T.LEADS},
                "N": N, "C": C, "level": lgate, "line_and_chance_agree_to_lead": far, "gates": gates})

    # Rho Basti, June 2016 — the days the live model gets wrong
    rb = {}
    for L in (2, 3, 4):
        s = scored[L]["F"]
        m = ((s["station_code"] == "001NEID3") & (s["date"] >= "2016-06-01") & (s["date"] <= "2016-06-20")).to_numpy()
        rb[str(L)] = [{"day": str(d.date()), "river_above_at_reading": int(a), "flooded": int(f),
                       "W_pct": round(100 * float(w), 1), "final_pct": round(100 * float(x), 1)}
                      for d, a, f, w, x in zip(s["date"][m], T.river_state(s)[m], s["flood"][m],
                                               P[(L, "W")][m], P[(L, final)][m])]
    out["rho_basti_june_2016"] = rb
    REPORT.write_text(json.dumps(out, indent=2, default=str))

    print("\n  the fault — river-above days given under 5%: days / flooded")
    for L in T.LEADS:
        print(f"    lead {L}: " + "   ".join(f"{v} {S[L][v]['low_days']}/{S[L][v]['low_flooded']}" for v in ("W", "F", "X")))
    print(f"\n  final model: {final}   chance inputs kept: {kept or 'none'}   level inputs kept: {lkept or 'none'}   "
          f"LV {'kept' if K['LV']['kept'] else 'not kept'}")
    print("  " + "   ".join(f"{k}: {'PASS' if v else 'FAIL'}" for k, v in gates.items())
          + f"   line and chance agree from lead 1 to {far}")
    print(f"  wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    r = main()
    sys.exit(0 if all(r["gates"].values()) else 1)
