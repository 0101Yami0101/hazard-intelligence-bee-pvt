"""Two more tests on the "river above its line told ~0%" fault. The design
and every rule are fixed in docs/design/FLOOD_WHEN_PILOT_PLAN.md §18; this
script only carries them out. The chance model is the live one (W).

    python scripts/model/check_gauge_fix2.py

    A   a river at its line is called "at its line": a river-above day is
        flagged when the level model's low-high range touches line +- margin
        (10 cm at level gauges, 10% of ordinary-to-line at flow gauges)
        A1  of river-above days NOT flagged and given under 5%, fewer than
            1 in 10 end at or above the line
        A2  at leads 1 and 2, 2 to 8 in 10 of flagged days end at/above it
        A3  at leads 1 and 2, no more than half of river-above days flagged
    B   fresh melt (read on the day of the gauge's own reading) at the level
        gauges above 1,000 m only: Y, K and C as §17b

Writes  reports/gauge_fix2_check.json
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

import check_gauge_fix as F
import check_gauge_retrain as R
import gauge_extra as X
import gauge_week as W
import train_flood_when_gauge as T
from common import ROOT

REPORT = ROOT / "reports" / "gauge_fix2_check.json"
FEATS_W = F.FEATS_W
MARGIN_M, MARGIN_FLOW = 0.10, 0.10
HIGH_M = 1000.0
LEVEL_LEADS, DRAWN = tuple(range(1, 8)), (1, 2)
RHO = "001NEID3"


def margin(df: pd.DataFrame, registry: dict) -> np.ndarray:
    """The band's half-width in the gauge's own units (0 ordinary, 1 its line)."""
    span = df["station_code"].map(lambda c: registry[c]["threshold"] - registry[c]["base"]).to_numpy()
    return np.where((df["network"] == "CWC").to_numpy(), MARGIN_M / span, MARGIN_FLOW)


def test_a(scored: dict, P: dict, registry: dict) -> dict:
    out, small, ok = {"by_lead": {}}, [0, 0], {"A1": True, "A2": True, "A3": True}
    for L in T.LEADS:
        s, p = scored[L], P[L]
        y, above = s["flood"].to_numpy() == 1, T.river_state(s) == 1
        if L in LEVEL_LEADS:
            q = W.level_oof(s, FEATS_W)
            now, m = s["g_frac"].to_numpy(), margin(s, registry)
            flag = above & (now + q[:, 0] <= 1 + m) & (now + q[:, 2] >= 1 - m)
            inside = np.abs(s["level"].to_numpy() - 1) <= m
        else:
            flag = np.zeros(len(s), bool)
            inside = flag
        low = above & ~flag & (p < F.LOW)
        low_all = above & (p < F.LOW)
        n, k = int(low.sum()), int((low & y).sum())
        r = {"river_above_days": int(above.sum()), "flagged": int(flag.sum()),
             "flagged_share_pct": round(100 * float(flag.sum() / max(above.sum(), 1)), 1),
             "flagged_ended_at_or_above_pct": round(100 * float(y[flag].mean()), 1) if flag.any() else None,
             "flagged_ended_inside_band_pct": round(100 * float(inside[flag].mean()), 1) if flag.any() else None,
             "under_5pct_before": {"days": int(low_all.sum()), "flooded": int((low_all & y).sum())},
             "under_5pct_not_flagged": {"days": n, "flooded": k},
             "flood_days_under_5pct_now_flagged": int((low_all & flag & y).sum())}
        if n >= F.LOW_MIN_DAYS:
            r["A1"] = bool(k / n < F.LOW_MAY_FLOOD)
            ok["A1"] &= r["A1"]
        else:
            r["A1"] = None
            small[0] += n
            small[1] += k
        if L in DRAWN:
            r["A2"] = bool(flag.any() and 0.2 <= y[flag].mean() <= 0.8)
            r["A3"] = bool(flag.sum() <= 0.5 * above.sum())
            ok["A2"] &= r["A2"]
            ok["A3"] &= r["A3"]
        out["by_lead"][str(L)] = r
        print(f"  A, lead {L}: river above {r['river_above_days']}, flagged {r['flagged']} ({r['flagged_share_pct']}%), "
              f"of them at/above {r['flagged_ended_at_or_above_pct']}%, inside the band {r['flagged_ended_inside_band_pct']}%;  "
              f"under 5%: before {r['under_5pct_before']['days']}/{r['under_5pct_before']['flooded']} -> not flagged "
              f"{n}/{k}" + (f" ({100*k/n:.1f}%)" if n else "") + f"   A1 {r['A1']}"
              + (f"  A2 {r['A2']}  A3 {r['A3']}" if L in DRAWN else ""))
        if L in (2, 3, 4):
            mm = ((s["station_code"] == RHO) & (s["date"] >= "2016-06-01") & (s["date"] <= "2016-06-20")).to_numpy() & above
            out.setdefault("rho_basti_june_2016", {})[str(L)] = [
                {"day": str(d.date()), "flooded": int(f), "W_pct": round(100 * float(w), 1), "flagged": bool(g)}
                for d, f, w, g in zip(s["date"][mm], y[mm], p[mm], flag[mm])]
    if small[0]:
        p_ = small[1] / small[0] < F.LOW_MAY_FLOOD
        ok["A1"] &= p_
        out["A1_small_leads_together"] = {"days": small[0], "flooded": small[1], "pass": bool(p_)}
        print(f"  A1, the small leads together: {small[0]} days, {small[1]} flooded   {p_}")
    out["gates"] = {k: bool(v) for k, v in ok.items()}
    return out


def test_b(ta: dict, scored: dict, P: dict, registry: dict, t0: float) -> dict:
    high = [c for c, st in registry.items() if st["network"] == "CWC" and st["base"] > HIGH_M]
    out = {"high_gauges": [registry[c]["name"] for c in high], "above_m": HIGH_M}
    print(f"\n  B: level gauges above {HIGH_M:.0f} m: {out['high_gauges']}")
    melt = X.melt_inputs(registry)
    tb = {}
    for L, tbl in ta.items():
        parts = []
        for code, g in tbl.groupby("station_code", sort=False):
            m = melt[code].shift(L) if code in high else pd.DataFrame(columns=X.M_FEATS, dtype=float)
            parts.append(g.join(m, on="date"))
        tb[L] = pd.concat(parts).sort_index()
        assert tb[L].index.equals(tbl.index)
    # mechanics: the value joined is the one L days before the target
    g = tb[3][(tb[3]["station_code"] == RHO) & tb[3]["melt7"].notna()].iloc[-200]
    assert abs(melt[RHO].loc[g["date"] - pd.Timedelta(days=3), "melt7"] - g["melt7"]) < 1e-9

    rows = []
    t1 = tb[1][tb[1]["date"].dt.month.between(4, 7) & tb[1]["melt7"].notna() & tb[1]["level"].notna()]
    for code, d0 in t1.groupby("station_code"):
        for yr, d in d0.groupby(d0["date"].dt.year):
            if len(d) >= F.Y_MIN_DAYS and d["melt7"].nunique() > 1 and d["level"].nunique() > 1:
                rows.append((registry[code]["name"], int(yr), float(spearmanr(d["melt7"], d["level"])[0])))
    y_ = pd.DataFrame(rows, columns=["gauge", "year", "r"])
    Y = {"gauge_years": int(len(y_)), "moving_together": int((y_["r"] > 0).sum()),
         "share": round(float((y_["r"] > 0).mean()), 3) if len(y_) else None,
         "median_r": round(float(y_["r"].median()), 3) if len(y_) else None,
         "by_gauge": {n: f"{int((d['r'] > 0).sum())} of {len(d)}" for n, d in y_.groupby("gauge")},
         "pass": bool(len(y_) and (y_["r"] > 0).mean() >= F.Y_M_SHARE)}
    out["Y"] = Y
    print(f"  B, Y: {Y['moving_together']} of {Y['gauge_years']} gauge-years move together ({Y['share']}), "
          f"median r {Y['median_r']}, {Y['by_gauge']}   {'ok' if Y['pass'] else 'FAIL — dropped'}")
    if not Y["pass"]:
        out["gates"] = {"Y": False, "K": None, "C": None}
        return out

    S = {L: {} for L in T.LEADS}
    hi_rows = {}
    for L in T.LEADS:
        s = R.scored(tb[L], FEATS_W + X.M_FEATS)
        assert s[R.KEY].equals(scored[L][R.KEY])
        p = R.chances(s, "sigmoid")[0]
        y, above = s["flood"].to_numpy(), T.river_state(s) == 1
        S[L]["W"], S[L]["M"] = F.stats(y, P[L], above), F.stats(y, p, above)
        h = s["station_code"].isin(high).to_numpy()
        hi_rows[str(L)] = {v: {"skill_above": round(R.skill(y[h & above], q[h & above]), 4),
                               "low_days": int((h & above & (q < F.LOW)).sum()),
                               "low_flooded": int((h & above & (q < F.LOW) & (y == 1)).sum())}
                           for v, q in (("W", P[L]), ("M", p))}
        if L in (2, 3, 4):
            mm = ((s["station_code"] == RHO) & (s["date"] >= "2016-06-01") & (s["date"] <= "2016-06-20")).to_numpy() & above
            out.setdefault("rho_basti_june_2016", {})[str(L)] = [
                {"day": str(d.date()), "flooded": int(f), "W_pct": round(100 * float(w), 1), "M_pct": round(100 * float(x), 1)}
                for d, f, w, x in zip(s["date"][mm], y[mm], P[L][mm], p[mm])]
        print(f"  B, lead {L}: " + "   ".join(
            f"{v} skill {S[L][v]['skill_all']:.4f} onset {S[L][v]['skill_onset']:.4f} above {S[L][v]['skill_above']:.4f} "
            f"low {S[L][v]['low_days']}/{S[L][v]['low_flooded']}" for v in ("W", "M"))
            + f"   high gauges, river above: {hi_rows[str(L)]}   ({time.time()-t0:.0f}s)")
    K = F.keep(S, "M", "W")
    C = {v: F.fault(S, v) for v in ("W", "M")}
    out.update({"K": K, "C": C, "high_gauges_river_above": hi_rows,
                "by_lead": {str(L): {v: {k: (round(x, 4) if isinstance(x, float) else x) for k, x in d.items()}
                                     for v, d in S[L].items()} for L in T.LEADS},
                "gates": {"Y": True, "K": K["kept"], "C": C["M"]["pass"]}})
    print(f"  B, K: no harm {K['no_harm']} (harm at {K['harm_at_leads']}), better among river-above at leads "
          f"{K['better_among_river_above_at_leads']}   {'KEPT' if K['kept'] else 'not kept'};   C {'PASS' if C['M']['pass'] else 'FAIL'}")
    return out


def main() -> dict:
    t0 = time.time()
    print("GAUGE FIX CHECK 2 — A: 'at its line';  B: fresh melt at the high gauges\n")
    T.FREE_FEATS = set(T.FREE_FEATS) | X.FREE
    with contextlib.redirect_stdout(io.StringIO()):
        ta, registry = W.build_tables(W.station_days())
    scored, P = {}, {}
    for L in T.LEADS:
        scored[L] = R.scored(ta[L], FEATS_W)
        P[L] = R.chances(scored[L], "sigmoid")[0]
    print(f"  live model scored at every lead ({time.time()-t0:.0f}s)\n")
    out = {"protocol": "docs/design/FLOOD_WHEN_PILOT_PLAN.md §18", "gauges": len(registry),
           "A": test_a(scored, P, registry)}
    out["B"] = test_b(ta, scored, P, registry, t0)
    REPORT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n  A: " + "  ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in out["A"]["gates"].items())
          + "     B: " + "  ".join(f"{k} {v}" for k, v in out["B"]["gates"].items()))
    print(f"  wrote {REPORT.relative_to(ROOT)}  ({time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    main()
