"""Does a river station's own measured rain make its gauge chance better? The
rules are fixed in docs/design/RAIN_GAUGES.md §6 (Part C); this script only
carries them out. Nothing live is touched.

    python scripts/model/check_gauge_rain.py

    base  the live gauge chance models: FEATS (11), sigmoid by river state
    A     base + gr1, gr3 from the rain day ending 08:30 on the issue morning
    B     base + gr1, gr3 from the rain day before that (fully in at 08:30)

    gr1 / gr3: the station's 1- and 3-day measured rain as its percentile among
    its own May-October days. Only at the stations that passed Part C0 and are
    live (reports/ffs_rain_check.csv); missing everywhere else.

    G1  no harm: all gauges, all days and onset days, AUC and Brier skill no
        more than 0.005 lower at leads 1-3 and 0.010 at 4-9
    G2  gain: the rain stations, onset days, leads 1-3: AUC or Brier skill up
        >= 0.010 at 2 of 3 leads, neither down by more than the G1 tolerance

Writes  reports/gauge_rain_check.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "inspect"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

import check_gauge_retrain as R
import ffs_rain_check as F
import gauge_week as W
import train_flood_when_gauge as T
from common import GAUGES, ROOT
from gauge_vs_rain_sources import MIN_DAYS, MONTHS, gauges

REPORT = ROOT / "reports" / "gauge_rain_check.json"
RAIN = ["gr1", "gr3"]
GAIN, GAIN_LEADS, GAIN_NEEDED = 0.010, (1, 2, 3), 2


def rain_stations() -> dict[str, str]:
    """FFS code -> NWDP station name, for the stations that passed Part C0 and are live."""
    c = pd.read_csv(ROOT / "reports" / "ffs_rain_check.csv")
    c = c[c.passes & (pd.to_datetime(c.mps_last) >= pd.Timestamp("2026-10-01"))]
    return dict(zip(c.code, c.nwdp_station))


def station_rain(code: str, nwdp_name: str, G: pd.DataFrame) -> pd.Series:
    """By rain day: MPS where the day is whole; else NWDP's listed value; else 0
    in an NWDP counted month; else missing."""
    m = F.daily_mps(pd.read_csv(GAUGES / "cwc" / f"{code}_mps.csv", parse_dates=["datetime"]))
    whole = m.loc[m.only_0830 | (m.n == F.SLOTS), "mm"]
    g = G[G.Station == nwdp_name]
    g = g.assign(y=g.t.dt.year, m=g.t.dt.month)
    cnt = g[g.m.isin(MONTHS)].groupby(["y", "m"]).size()
    counted = set(cnt[cnt >= MIN_DAYS].index)
    cal = pd.date_range(min(whole.index.min(), g.t.min()), max(whole.index.max(), g.t.max()), freq="D")
    s = pd.Series(np.where([(d.year, d.month) in counted for d in cal], 0.0, np.nan), index=cal)
    listed = g.set_index("t").p
    s.loc[listed.index] = listed.to_numpy()
    s.loc[whole.index] = whole.to_numpy()
    return s


def percentile(s: pd.Series, w: int) -> pd.Series:
    r = s.rolling(w, min_periods=w).sum()
    mons = (r.index.month >= 5) & (r.index.month <= 10)
    clim = np.sort(r[mons & r.notna()].to_numpy())
    out = pd.Series(np.nan, index=r.index)
    fin = r.notna().to_numpy()
    out[fin] = np.searchsorted(clim, r[fin].to_numpy(), side="left") / len(clim)
    return out


def with_rain(df: pd.DataFrame, pcts: dict, L: int, shift: int) -> pd.DataFrame:
    parts = []
    for code, (p1, p3) in pcts.items():
        parts.append(pd.DataFrame({"gr1": p1.shift(shift), "gr3": p3.shift(shift)})
                     .rename_axis("date").reset_index().assign(station_code=code))
    add = pd.concat(parts)
    out = df.merge(add, on=["station_code", "date"], how="left", validate="many_to_one")
    assert len(out) == len(df)
    return out


def scores(y, p) -> dict:
    if not (0 < y.sum() < len(y)):
        return {"auc": None, "brier_skill": None}
    return {"auc": round(R.auc(y, p), 4), "brier_skill": round(R.skill(y, p), 4)}


def main() -> None:
    t0 = time.time()
    stations = rain_stations()
    print(f"rain stations: {stations}")
    G = gauges()
    pcts = {}
    for code, name in stations.items():
        s = station_rain(code, name, G)
        pcts[code] = (percentile(s, 1), percentile(s, 3))
        print(f"  {code} {name}: {int(s.notna().sum()):,} rain days known, {s.index.min().date()} -> {s.index.max().date()}")
    tables, _ = W.build_tables(W.station_days())

    report = {"rain_stations": stations, "leads": {}}
    ok = {"G1_A": True, "G1_B": True}
    gains = {"A": 0, "B": 0}
    g2_harm = {"A": False, "B": False}
    for L in T.LEADS:
        df = tables[L]
        df = df[df["g_frac"].notna()].reset_index(drop=True)
        P = {"base": T.oof(df, T.FEATS, by="state")}
        cols = {}
        for v, sh in (("A", L - 1), ("B", L)):
            d = with_rain(df, pcts, L, sh)
            cols[v] = d[RAIN].notna().all(axis=1).to_numpy()
            P[v] = T.oof(d, T.FEATS + RAIN, by="state")
        y = df["flood"].to_numpy()
        onset = T.river_state(df) == 0
        rs = df["station_code"].isin(stations).to_numpy()
        tol = R.tol(L)
        res = {"tolerance": tol}
        for name, m in (("all gauges, all days", np.ones(len(df), bool)), ("all gauges, onset", onset),
                        ("rain stations, all days", rs), ("rain stations, onset", rs & onset)):
            row = {"days": int(m.sum()), "flood_days": int(y[m].sum())}
            for v in ("base", "A", "B"):
                row[v] = scores(y[m], P[v][m])
            res[name] = row
            if name.startswith("all gauges"):
                for v in ("A", "B"):
                    for k in ("auc", "brier_skill"):
                        if row[v][k] is not None and row[v][k] - row["base"][k] < -tol:
                            ok[f"G1_{v}"] = False
            if name == "rain stations, onset" and L in GAIN_LEADS:
                for v in ("A", "B"):
                    da = row[v]["auc"] - row["base"]["auc"]
                    ds = row[v]["brier_skill"] - row["base"]["brier_skill"]
                    gains[v] += int(da >= GAIN or ds >= GAIN)
                    g2_harm[v] |= (da < -tol or ds < -tol)
        res["rain_known_share_on_rain_stations"] = {v: round(float(cols[v][rs].mean()), 3) for v in cols}
        report["leads"][str(L)] = res
        r = res["rain stations, onset"]
        print(f"  lead {L}: rain stations onset {r['days']:,} days / {r['flood_days']} floods  "
              f"AUC {r['base']['auc']} -> A {r['A']['auc']}  B {r['B']['auc']}   "
              f"skill {r['base']['brier_skill']} -> A {r['A']['brier_skill']}  B {r['B']['brier_skill']}")
    for v in ("A", "B"):
        report[f"G1_{v}"] = ok[f"G1_{v}"]
        report[f"G2_{v}"] = bool(gains[v] >= GAIN_NEEDED and not g2_harm[v])
        report[f"G2_{v}_leads_gaining"] = gains[v]
    report["adoptable_after_trial"] = bool(report["G1_B"] and report["G2_B"])
    report["minutes"] = round((time.time() - t0) / 60, 1)
    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "leads"}, indent=1))


if __name__ == "__main__":
    main()
