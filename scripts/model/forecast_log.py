"""The flood forecast's track record: every issued forecast, and what happened.

    python scripts/model/forecast_log.py verify     # check what can be checked
    python scripts/model/forecast_log.py show       # print the scorecard

The daily run (flood_forecast_live.py) appends to the log and then calls
`verify`, so one command a day keeps both going.

Writes  records/flood_forecast/gauge_forecasts.csv   every river forecast issued
        records/flood_forecast/area_outlook.csv      every area outlook issued
        records/flood_forecast/gauge_observed.csv    daily max per gauge, as read back
        records/flood_forecast/gauge_verified.csv    forecasts joined to outcomes
        reports/flood_forecast_scorecard.json

Every number the models were graded on so far came from replaying the past.
This log is the other kind of evidence: forecasts written down BEFORE the day,
graded after. Nothing is rewritten after the fact — a re-run on the same day
replaces that day's issue, never an earlier one.

What can be checked automatically:
    river forecasts   yes — the gauge itself says whether the river reached
                      its threshold that day (read back from the same feeds)
    area outlook      not yet — its truth is a satellite- or news-confirmed
                      flood, which arrives late and patchily. It is logged now
                      so it can be graded when that truth comes in.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from common import ROOT

# Not under data/: that tree is git-ignored and treated as regenerable, and a
# track record is neither — lose it and the history is gone for good. Keep
# it where it can be committed.
LOG = ROOT / "records" / "flood_forecast"
GAUGE_LOG = LOG / "gauge_forecasts.csv"
AREA_LOG = LOG / "area_outlook.csv"
OBSERVED = LOG / "gauge_observed.csv"
VERIFIED = LOG / "gauge_verified.csv"
SCORECARD = ROOT / "reports" / "flood_forecast_scorecard.json"
GIVE_UP_DAYS = 21          # a target day with no reading this long after -> "no reading"
BINS = np.array([0.0, 0.02, 0.05, 0.10, 0.25, 0.50, 1.01])


def _append(path: Path, rows: list[dict], key: list[str]) -> int:
    if not rows:
        return 0
    LOG.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame(rows)
    old = pd.read_csv(path, dtype=str) if path.exists() else pd.DataFrame()
    df = pd.concat([old, new.astype(str)], ignore_index=True)
    df = df.drop_duplicates(subset=key, keep="last")
    df.to_csv(path, index=False)
    return len(new)


def log_gauge(rows: list[dict]) -> int:
    return _append(GAUGE_LOG, rows, ["issued_on", "target_date", "station_code"])


NEAR_DIR = LOG / "near_here"
NEAR_STATE = LOG / "near_here_state.csv"


def log_near_here(issued: str, days: list[str], near: dict) -> int:
    """Every place's flood chance near here (within 10 km) — each day and for
    the week — kept whole, one small file per issue (~15 KB), so it can be
    graded once flood records for those days exist. The record arrives months
    late (a report, then a satellite check), so nothing here is graded yet;
    the point is that it is written down BEFORE the day. Plus one statewide
    row per issue in a CSV anyone can open."""
    NEAR_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NEAR_DIR / f"{issued}.npz", days=np.array(days),
                        day=np.asarray(near["day"], np.float32),
                        week=np.asarray(near["week"], np.float32),
                        state_day=np.asarray(near["state_day"], np.float32),
                        state_week=np.float32(near["state_week"]))
    row = {"issued_on": issued, "first_day": days[0], "last_day": days[-1],
           "arunachal_week_chance": round(float(near["state_week"]), 5)}
    row.update({f"arunachal_day{i}_chance": round(float(v), 5)
                for i, v in enumerate(near["state_day"])})
    return _append(NEAR_STATE, [row], ["issued_on"])


NEW_RECORDS = ROOT / "records" / "flood_events" / "new_records.csv"
AREA_WAIT_DAYS = 7          # let a week's reports come in before grading it


def verify_area(today: date | None = None) -> dict:
    """Grade the logged flood-chance-near-here forecasts against the NEW
    flood records (flood_intake.py: river gauges crossing their lines, and
    people's reports).

    Only the RANKING can be graded: those records come from a few sources, so
    a place-week with no record is not a proven dry one, and "said 3%, 3%
    happened" cannot be checked until the record is complete. What is graded:
    did the places that flooded get higher chances than the rest that week?"""
    today = today or date.today()
    files = sorted(NEAR_DIR.glob("*.npz")) if NEAR_DIR.exists() else []
    out = {"issues_logged": len(files), "issues_graded": 0, "new_flood_records": 0,
           "place_weeks": 0, "place_weeks_with_a_flood": 0,
           "note": ("Ranking only: new flood records come from river gauges crossing their "
                    "lines and from people's reports, so a week with no record is not proven "
                    "dry and the level cannot be graded yet.")}
    if not files or not NEW_RECORDS.exists():
        return out
    conf = pd.read_csv(NEW_RECORDS)
    out["new_flood_records"] = int(len(conf))
    out["by_source"] = conf["source"].value_counts().to_dict() if len(conf) else {}
    if conf.empty:
        return out
    import near_here
    cur = near_here.load_curves()
    if cur is None:
        return out
    conf["date"] = pd.to_datetime(conf["date"])
    ps, ys = [], []
    for f in files:
        z = np.load(f)
        days = pd.to_datetime([str(d) for d in z["days"]])
        if days[-1].date() > today - timedelta(days=AREA_WAIT_DAYS):
            continue
        Y = near_here.truth_near(conf, pd.DatetimeIndex(days)).any(axis=0)
        wk = z["week"]
        m = cur["ap"] & np.isfinite(wk)
        ps.append(wk[m])
        ys.append(Y[m])
        out["issues_graded"] += 1
    if not ps:
        return out
    p, y = np.concatenate(ps).astype(float), np.concatenate(ys).astype(float)
    out["place_weeks"], out["place_weeks_with_a_flood"] = int(len(y)), int(y.sum())
    if 0 < y.sum() < len(y):
        from sklearn.metrics import roc_auc_score
        out["ranking_auc"] = round(float(roc_auc_score(y, p)), 3)
        out["mean_chance_where_it_flooded_pct"] = round(100 * float(p[y == 1].mean()), 3)
        out["mean_chance_elsewhere_pct"] = round(100 * float(p[y == 0].mean()), 3)
    return out


def log_area(issued: str, outlook: list[dict]) -> int:
    rows = []
    for o in outlook:
        a = o["areas_most_ground_at_risk"][0]
        rows.append({"issued_on": issued, "target_date": o["date"],
                     "lead_days": (date.fromisoformat(o["date"]) - date.fromisoformat(issued)).days,
                     "times_an_ordinary_day": o["times_an_ordinary_day"],
                     "expected_flooded_km2": o["expected_flooded_km2"],
                     "top_area_lat": a["lat"], "top_area_lon": a["lon"],
                     "top_area_times_normal": a["times_normal"]})
    return _append(AREA_LOG, rows, ["issued_on", "target_date"])


# ── verification ─────────────────────────────────────────────────────────
def _read_back(pending: pd.DataFrame, today: date) -> pd.DataFrame:
    """Fetch daily maxima for every gauge with a forecast awaiting its outcome."""
    from flood_gauge_live import fetch_daily
    got = []
    for (code, net), g in pending.groupby(["station_code", "network"]):
        since = pd.to_datetime(g["target_date"]).min().date() - timedelta(days=1)
        s, _ = fetch_daily(code, net, since)
        s = s[s.index < pd.Timestamp(today)]          # completed days only
        got += [{"station_code": code, "date": str(d.date()), "daily_max": float(v)}
                for d, v in s.items()]
    return pd.DataFrame(got)


def verify(today: date | None = None) -> dict | None:
    today = today or date.today()
    if not GAUGE_LOG.exists():
        print("  no forecasts logged yet")
        return None
    fc = pd.read_csv(GAUGE_LOG, dtype=str)
    obs = pd.read_csv(OBSERVED, dtype=str) if OBSERVED.exists() else pd.DataFrame(
        columns=["station_code", "date", "daily_max"])
    have = set(zip(obs["station_code"], obs["date"]))
    due = fc[pd.to_datetime(fc["target_date"]).dt.date < today]
    pending = due[[(c, d) not in have for c, d in zip(due["station_code"], due["target_date"])]]
    if len(pending):
        print(f"  reading back {pending['station_code'].nunique()} gauges for "
              f"{len(pending)} forecasts awaiting an outcome...", flush=True)
        new = _read_back(pending, today)
        if len(new):
            obs = pd.concat([obs, new.astype(str)], ignore_index=True)
            obs = obs.drop_duplicates(subset=["station_code", "date"], keep="last")
            LOG.mkdir(parents=True, exist_ok=True)
            obs.sort_values(["station_code", "date"]).to_csv(OBSERVED, index=False)

    v = due.merge(obs.rename(columns={"date": "target_date"}), how="left",
                  on=["station_code", "target_date"])
    v["daily_max"] = pd.to_numeric(v["daily_max"])
    v["happened"] = np.where(v["daily_max"].notna(),
                             (v["daily_max"] >= pd.to_numeric(v["threshold"])).astype(float), np.nan)
    age = (pd.Timestamp(today) - pd.to_datetime(v["target_date"])).dt.days
    v["status"] = np.where(v["happened"].notna(), "checked",
                           np.where(age > GIVE_UP_DAYS, "no reading", "awaiting reading"))
    if len(v):
        v.to_csv(VERIFIED, index=False)
    card = scorecard(v, fc, today)
    try:
        card["near_here"] = verify_area(today)
    except Exception as e:                                          # noqa: BLE001
        # the river track record must never be lost to the newer grader
        card["near_here"] = {"error": f"{type(e).__name__}: {e}"}
    SCORECARD.write_text(json.dumps(card, indent=2))
    print_card(card)
    return card


def _grade(d: pd.DataFrame) -> dict:
    y = d["happened"].to_numpy(float)
    p = pd.to_numeric(d["probability"]).to_numpy(float)
    clim = pd.to_numeric(d["base_rate"]).to_numpy(float)
    bs, bc = float(np.mean((p - y) ** 2)), float(np.mean((clim - y) ** 2))
    warn = p >= 0.25
    return {"n_forecasts": int(len(y)), "n_times_threshold_reached": int(y.sum()),
            "said_on_average_pct": round(100 * float(p.mean()), 2),
            "happened_pct": round(100 * float(y.mean()), 2),
            "brier_skill_vs_long_run_rate": round(1 - bs / bc, 3) if bc > 0 else None,
            "warnings_25pct": {"issued": int(warn.sum()), "right": int((warn & (y == 1)).sum()),
                               "floods_missed": int((~warn & (y == 1)).sum())}}


def scorecard(v: pd.DataFrame, fc: pd.DataFrame, today: date) -> dict:
    chk = v[v["status"] == "checked"]
    card = {"as_of": str(today),
            "logged": {"forecasts": int(len(fc)), "issue_days": int(fc["issued_on"].nunique()),
                       "first_issue": fc["issued_on"].min(), "last_issue": fc["issued_on"].max()},
            "outcomes": v["status"].value_counts().to_dict() if len(v) else {},
            "note": ("Too few checked forecasts to judge yet. Grading means something after "
                     "a monsoon season with several threshold crossings; until then this "
                     "shows the machinery works.") if chk["happened"].sum() < 20 else None}
    if len(chk):
        card["all"] = _grade(chk)
        card["by_lead_days"] = {str(k): _grade(g) for k, g in chk.groupby("lead_days")}
        card["official_danger_level_only"] = (
            _grade(chk[chk["official"] == "True"]) if (chk["official"] == "True").any() else None)
        p = pd.to_numeric(chk["probability"]).to_numpy(float)
        y = chk["happened"].to_numpy(float)
        card["reliability"] = [
            {"said": f"{100*lo:.0f}-{100*min(hi,1):.0f}%", "n": int(m.sum()),
             "happened_pct": round(100 * float(y[m].mean()), 1)}
            for lo, hi in zip(BINS[:-1], BINS[1:]) if (m := (p >= lo) & (p < hi)).any()]
    return card


def print_card(card: dict) -> None:
    lg = card["logged"]
    print(f"\n  Track record as of {card['as_of']}: {lg['forecasts']:,} river forecasts "
          f"logged over {lg['issue_days']} issue day(s) ({lg['first_issue']} .. {lg['last_issue']})")
    print(f"  outcomes: {card['outcomes'] or 'none due yet'}")
    if "all" in card:
        a = card["all"]
        print(f"  checked: {a['n_forecasts']:,} forecasts, threshold reached "
              f"{a['n_times_threshold_reached']} times; said {a['said_on_average_pct']}% on "
              f"average, happened {a['happened_pct']}%")
        w = a["warnings_25pct"]
        print(f"  warnings at 25%+: {w['issued']} issued, {w['right']} right, "
              f"{w['floods_missed']} crossings missed")
    if card.get("note"):
        print(f"  note: {card['note']}")
    print(f"  wrote {SCORECARD}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "show" and SCORECARD.exists():
        print_card(json.loads(SCORECARD.read_text()))
    else:
        verify()
