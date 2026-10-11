"""New flood records: river gauges crossing their lines, and people's reports.

    python scripts/model/flood_intake.py          # gather + radar look (the daily run calls this)
    python scripts/model/flood_intake.py gather   # records only
    python scripts/model/flood_intake.py check    # radar look only (information, not confirmation)
    python scripts/model/flood_intake.py test     # the chain, offline (scratch output)

Reads   records/flood_forecast/gauge_observed.csv  daily highs the track record read back
        records/flood_events/reports.csv            people's reports (the app's form)
        models/flood_when_gauge/stations.json
Writes  records/flood_events/candidates.csv         every candidate and what its check found
        records/flood_events/new_records.csv        the new flood records

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
The flood record every model here learned from (news reports, each passed
through a radar screen that filters out almost nothing — see below) ends in
Oct 2025 and does not update. Without new records,
nothing logged since can be graded, and places with no floods on record stay
unchecked (FLOOD_SCREEN_PLAN.md, Phase 8). Two sources feed this now:

    gauges    a river reaching its line (official danger level, or its own
              wettest-2% mark) — one candidate per crossing episode, dated to
              its highest day, placed at the gauge
    reports   floods people report through the app's form

A third — open news and disaster feeds — is not built: turning a news story
into a place precise enough for a 17 km satellite check needs village-level
place-name reading, which is what Google did to build the record we trained
on. Noted as a gap, not faked.

WHAT COUNTS AS A RECORD — and why the radar check does not decide it
The first version confirmed each candidate with fetch_32's Sentinel-1 screen
(new water within ~17 km above 0.3%), the screen the training records were
"confirmed" with. Tested on flood-free dates at the same places
(check_s1_screen_specificity.py, 2026-09-27) it called 97-100% of them
positive: at 0.3% it filters out almost nothing, and even a same-place test
cannot tell a flood date from a quiet one reliably (PARKED §0w). So:

    gauge crossing   a record as it stands — the river reached a government-
                     defined line (or its own wettest-2% mark), measured
    report           a record of the same kind the models learned from: the
                     training "floods" were, in effect, news reports

Each keeps its source, so a grade can be split by kind.

RADAR CONFIRMATION, since 2026-09-28: each record is also put through the
new, VALIDATED radar test (scripts/fetch/radar_water_test.py — 97.8% of
flood-free dates correctly said "no", PARKED §0x). "radar-confirmed" means it
passed that test; "radar did not show it" does not disprove the record (the
water may have drained before a pass, or been small against 10 km of low
ground). A record stays a record either way.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from common import ROOT

EVENTS = ROOT / "records" / "flood_events"
CANDIDATES = EVENTS / "candidates.csv"
RECORDS = EVENTS / "new_records.csv"
REPORTS = EVENTS / "reports.csv"
OBSERVED = ROOT / "records" / "flood_forecast" / "gauge_observed.csv"
STATIONS = ROOT / "models" / "flood_when_gauge" / "stations.json"
EE_PROJECT = "earthengine-507510"
WAIT_DAYS = 5              # radar archive lag + the +-3-day search window
PER_CHECK_TIMEOUT_S = 90
MAX_TRIES = 3
COLS = ["id", "source", "place", "lat", "lon", "date", "detail", "added_on", "status",
        "tries", "scene_date", "pct_new_water", "checked_on"]


# ── candidates ────────────────────────────────────────────────────────────
def gauge_candidates(observed: pd.DataFrame, stations: dict) -> list[dict]:
    """One candidate per crossing episode per gauge: consecutive days at or
    above the gauge's line, dated to the highest day, placed at the gauge."""
    out = []
    if observed.empty:
        return out
    obs = observed.copy()
    obs["date"] = pd.to_datetime(obs["date"])
    obs["daily_max"] = pd.to_numeric(obs["daily_max"], errors="coerce")
    for code, g in obs.groupby("station_code"):
        st = stations.get(code)
        if st is None:
            continue
        g = g.sort_values("date")
        g = g[g["daily_max"] >= st["threshold"]]
        if g.empty:
            continue
        episode = (g["date"].diff().dt.days != 1).cumsum()
        for _, e in g.groupby(episode):
            peak = e.loc[e["daily_max"].idxmax()]
            d = str(peak["date"].date())
            out.append({"id": f"gauge:{code}:{d}", "source": "gauge", "place": st["name"],
                        "lat": st["lat"], "lon": st["lon"], "date": d,
                        "detail": (f"{st['means']}: {peak['daily_max']:.2f} vs line "
                                   f"{st['threshold']:.2f}; {len(e)} day(s)")})
    return out


def report_candidates(reports: pd.DataFrame) -> list[dict]:
    out = []
    for _, r in reports.iterrows():
        out.append({"id": f"report:{r['reported_on']}:{float(r['lat']):.4f},{float(r['lon']):.4f}"
                          f":{r['date']}",
                    "source": "report", "place": r.get("place", ""), "lat": float(r["lat"]),
                    "lon": float(r["lon"]), "date": str(r["date"]),
                    "detail": str(r.get("note", ""))[:300]})
    return out


WITHDRAWN = "withdrawn: the reading was corrected"


def withdraw_corrected(cur: pd.DataFrame, observed: pd.DataFrame, stations: dict,
                       still: set[str]) -> list[str]:
    """Gauge records whose crossing is gone from the readings as they stand
    now. The track record re-reads every gauge each day, cleaned, so a wrong
    reading the feed has since corrected (or the cleaning now removes) leaves
    its day below the line — as at Murga Bridge, 2026-09-28: 2,231.30 m on
    the day, 2,134.39 m ever since. Such a record is withdrawn: it stays in
    candidates.csv, marked, and leaves the records file. Only where the day
    is still in the readings and reads below the line; a day no longer held
    is left alone. A crossing that comes back is a record again."""
    out = []
    if cur.empty or observed.empty:
        return out
    obs = observed.copy()
    obs["daily_max"] = pd.to_numeric(obs["daily_max"], errors="coerce")
    high = {(c, str(d)[:10]): v for c, d, v in zip(obs["station_code"], obs["date"], obs["daily_max"])}
    for i, c in cur.iterrows():
        if c["source"] != "gauge":
            continue
        code = c["id"].split(":")[1]
        if c["id"] in still:
            if c["status"] == WITHDRAWN:
                cur.loc[i, "status"], cur.loc[i, "tries"] = "pending", "0"
            continue
        v, st = high.get((code, c["date"])), stations.get(code)
        if c["status"] == WITHDRAWN or st is None or v is None or pd.isna(v) or v >= st["threshold"]:
            continue
        cur.loc[i, "status"] = WITHDRAWN
        cur.loc[i, "detail"] = (f"{c['detail']} [withdrawn: the day now reads {v:.2f}, below the "
                                f"line]")[:300]
        out.append(c["id"])
    return out


def write_records(cur: pd.DataFrame, path: Path = RECORDS) -> int:
    """Every gathered candidate is a record (see the module note): gauge
    crossings as measured, reports as reported — each with its radar verdict
    from the validated test ("radar" column). Withdrawn ones are left out."""
    cur = cur[cur["status"] != WITHDRAWN]
    rec = cur.reindex(columns=COLS)[["id", "source", "place", "lat", "lon", "date", "detail",
                                     "status", "scene_date", "pct_new_water"]]
    rec = rec.rename(columns={"status": "radar", "scene_date": "radar_scene_date",
                              "pct_new_water": "radar_new_water_pct"})
    path.parent.mkdir(parents=True, exist_ok=True)
    rec.to_csv(path, index=False)
    return len(rec)


def gather(today: date | None = None, candidates: Path = CANDIDATES,
           records: Path = RECORDS) -> int:
    """Add any new candidates (never touching ones already listed) and
    rewrite the records file."""
    today = today or date.today()
    stations = json.loads(STATIONS.read_text())
    obs = pd.read_csv(OBSERVED, dtype=str) if OBSERVED.exists() else pd.DataFrame()
    rep = pd.read_csv(REPORTS, dtype=str) if REPORTS.exists() else pd.DataFrame()
    new = gauge_candidates(obs, stations) + (report_candidates(rep) if len(rep) else [])
    cur = pd.read_csv(candidates, dtype=str) if candidates.exists() else pd.DataFrame(columns=COLS)
    have = set(cur["id"])
    add = [dict(c, added_on=str(today), status="pending", tries="0") for c in new
           if c["id"] not in have]
    if add:
        cur = pd.concat([cur, pd.DataFrame(add).astype(str)], ignore_index=True)
    before = cur["status"].copy()
    gone = withdraw_corrected(cur, obs, stations, {c["id"] for c in new})
    if add or not cur["status"].equals(before):
        candidates.parent.mkdir(parents=True, exist_ok=True)
        cur.reindex(columns=COLS).to_csv(candidates, index=False)
    n = write_records(cur, records) if len(cur) else 0
    print(f"  flood intake: {len(add)} new record(s) "
          f"({sum(c['source'] == 'gauge' for c in add)} gauge crossings, "
          f"{sum(c['source'] == 'report' for c in add)} reports); {n} on record"
          + (f"; withdrew {len(gone)} whose reading was corrected: {', '.join(gone)}" if gone else ""))
    return len(add)


# ── the radar confirmation (the validated test) ───────────────────────────
def _screen(lat: float, lon: float, day: str) -> dict:
    """The validated radar water test (radar_water_test.py, PARKED §0x)."""
    import radar_water_test as R
    return R.test_one(lat, lon, day)


def _threshold() -> float:
    import radar_water_test as R
    v = json.loads(R.VALIDATION.read_text())
    if not v.get("PASS"):
        raise RuntimeError("the radar test has not passed its validation")
    return v["threshold_share_pct_from_half_A"] / 100


def check(today: date | None = None, candidates: Path = CANDIDATES,
          records: Path = RECORDS) -> dict:
    """Put each record, once old enough for its radar pass to be in the
    archive, through the validated radar test. "radar-confirmed" if it
    passes; "radar did not show it" does not disprove it (module note)."""
    today = today or date.today()
    if not candidates.exists():
        print("  flood intake: nothing on record yet")
        return {"checked": 0}
    cur = pd.read_csv(candidates, dtype=str).reindex(columns=COLS)
    due = cur[(cur["status"].isin(["pending", "error"]))
              & (pd.to_datetime(cur["date"]).dt.date <= today - timedelta(days=WAIT_DAYS))
              & (pd.to_numeric(cur["tries"]).fillna(0) < MAX_TRIES)]
    if due.empty:
        print("  flood intake: no radar check due")
        return {"checked": 0}
    thr = _threshold()
    n = 0
    with cf.ThreadPoolExecutor(max_workers=1) as pool:
        for i, c in due.iterrows():
            cur.loc[i, "tries"] = str(int(float(c["tries"] or 0)) + 1)
            fut = pool.submit(_screen, float(c["lat"]), float(c["lon"]), c["date"])
            try:
                r = fut.result(timeout=PER_CHECK_TIMEOUT_S)
            except Exception as e:                                  # noqa: BLE001
                cur.loc[i, "status"] = "error"
                cur.loc[i, "detail"] = f"{c['detail']} [radar check failed: {type(e).__name__}]"[:300]
                continue
            n += 1
            cur.loc[i, "checked_on"] = str(today)
            if not r.get("image"):
                cur.loc[i, "status"] = "no radar pass within 3 days"
            elif not r.get("reference") or r.get("new_share") is None:
                cur.loc[i, "status"] = "too few radar references"
            else:
                cur.loc[i, "scene_date"] = r["scene_date"]
                cur.loc[i, "pct_new_water"] = str(round(100 * r["new_share"], 3))
                cur.loc[i, "status"] = ("radar-confirmed" if r["new_share"] > thr
                                        else "radar did not show it")
    cur.to_csv(candidates, index=False)
    write_records(cur, records)
    print(f"  flood intake: radar-checked {n} record(s)")
    return {"checked": n}


# ── a test of the chain (no network) ──────────────────────────────────────
def test() -> None:
    """Gauge crossings -> one record per episode, dated to its peak; a report
    -> a record; re-gathering adds nothing twice. Into a scratch folder."""
    import tempfile
    global OBSERVED, REPORTS
    stations = json.loads(STATIONS.read_text())
    code = next(iter(stations))
    th = stations[code]["threshold"]
    tmp = Path(tempfile.mkdtemp())
    OBSERVED, REPORTS = tmp / "observed.csv", tmp / "reports.csv"
    pd.DataFrame({"station_code": [code] * 6,
                  "date": ["2024-07-01", "2024-07-02", "2024-07-03", "2024-07-10",
                           "2024-07-11", "2024-07-20"],
                  "daily_max": [th + 0.1, th + 0.5, th - 1, th + 0.2, th - 0.5, th + 0.3]}
                 ).to_csv(OBSERVED, index=False)
    pd.DataFrame([{"reported_on": "2024-07-05", "place": "test", "lat": 28.07, "lon": 95.33,
                   "date": "2024-07-04", "note": "water over the road"}]).to_csv(REPORTS, index=False)
    cand, rec = tmp / "candidates.csv", tmp / "new_records.csv"
    n1 = gather(date(2024, 7, 30), cand, rec)
    n2 = gather(date(2024, 7, 31), cand, rec)
    r = pd.read_csv(rec, dtype=str)
    got = sorted(r["date"])
    ok = (n1 == 4 and n2 == 0
          and got == ["2024-07-02", "2024-07-04", "2024-07-10", "2024-07-20"]
          and sorted(r["source"]) == ["gauge", "gauge", "gauge", "report"])
    print(f"  records {got} from {sorted(r['source'])}; second gather added {n2}")
    # a reading corrected afterwards: 2 July now reads below the line, and
    # 20 July is no longer held at all (left alone); then the 2 July
    # crossing comes back
    o = pd.read_csv(OBSERVED, dtype=str)
    o.loc[o["date"] == "2024-07-01", "daily_max"] = str(th - 0.4)
    o.loc[o["date"] == "2024-07-02", "daily_max"] = str(th - 0.3)
    o[o["date"] != "2024-07-20"].to_csv(OBSERVED, index=False)
    gather(date(2024, 8, 1), cand, rec)
    r3, c3 = pd.read_csv(rec, dtype=str), pd.read_csv(cand, dtype=str)
    gather(date(2024, 8, 2), cand, rec)
    c4 = pd.read_csv(cand, dtype=str)
    o.loc[o["date"] == "2024-07-02", "daily_max"] = str(th + 0.5)
    o.to_csv(OBSERVED, index=False)
    gather(date(2024, 8, 3), cand, rec)
    r5 = pd.read_csv(rec, dtype=str)
    ok2 = (sorted(r3["date"]) == ["2024-07-04", "2024-07-10", "2024-07-20"]
           and len(c3) == 4 and (c3["status"] == WITHDRAWN).sum() == 1
           and c3.loc[c3["status"] == WITHDRAWN, "date"].item() == "2024-07-02"
           and c4.equals(c3)
           and sorted(r5["date"]) == ["2024-07-02", "2024-07-04", "2024-07-10", "2024-07-20"])
    print(f"  corrected reading: records {sorted(r3['date'])}, withdrawn kept in candidates "
          f"{(c3['status'] == WITHDRAWN).sum()}; crossing back: {sorted(r5['date'])}")
    ok = ok and ok2
    print(f"  test: {'PASS' if ok else 'FAIL'} (scratch: {tmp}; nothing written to records/)")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "test":
        test()
    else:
        if cmd in ("all", "gather"):
            gather()
        if cmd in ("all", "check"):
            check()
