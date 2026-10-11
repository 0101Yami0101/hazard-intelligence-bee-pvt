"""The VERIFIED flood record: every flood event some independent route confirms.

    python scripts/build/build_verified_floods.py

Writes  data/interim/flood_events/verified_events.parquet
        reports/flood_verified_record.json

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
The record every flood model trained on was the list of news reports that
passed fetch_32's quick radar screen — which, tested on flood-free dates,
passes almost everything (PARKED §0w). So that list is "reported floods". At
the same time, the events that WERE independently verified — gauge crossings
we found and checked ourselves, reports a gauge confirmed, reports Google's
Global Flood Database confirmed — were not in the training list at all, or
only by coincidence (PARKED §0x).

An event is VERIFIED here if at least one of these confirms it:

    radar      the validated radar water test (radar_water_test.py; 97.8% of
               flood-free dates correctly said "no") supports the report
    gfd        Google's Global Flood Database has flooding there and then
    gauge-xc   a river gauge near the report crossed its line in the window
    gauge      a flood we found FROM a gauge crossing its line, checked with
               our own full-quality radar processing and showing new water.
               Not counted when the crossing rests on a reading the cleaning
               removes (false_gauge_days, FLOOD_WHEN_PILOT_PLAN.md §15): the
               radar step counts any new-water pixel, so this route is only
               as good as the gauge reading

Each event keeps the list of routes that confirm it. The braided-channel-
shift suspects (§0n) stay excluded, as in every model. Events from different
routes on the same day within 2 km are one event.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from common import INTERIM, PROCESSED, ROOT

R = ROOT / "reports"
OUT = INTERIM / "flood_events" / "verified_events.parquet"
REPORT = R / "flood_verified_record.json"
JANG = (27.5834, 91.9802)          # Jang town centre (FLOOD_WHEN_PILOT_PLAN.md)
DROPPED: list[str] = []            # gauge floods left out as resting on false readings
GAUGE_FIRST = ["flood_where_s1_statewide.json", "flood_where_s1_statewide_expanded.json",
               "flood_where_s1_nwdp.json", "flood_where_s1_loose_ends.json"]


def _day(text: str, note: str = "") -> str:
    """A gauge event's flood day. Some are annotated, e.g. "2024-10-05 (nearest
    scene to 2024-10-04 flood day, 1 day off)" — the flood day is the date.

    ⚠️ Two records keep that annotation in a separate `note` and only the
    SCENE's date in `flood_date` (flood_where_s1_loose_ends.json: Seppa,
    Tamen). Read without the note they were filed two days off their river:
    Seppa's real crossing (2026-07-13, 340.88 m against a danger level of
    340.00) sat under 2026-07-15, and Tamen's "flood" of 2022-07-09 — one
    keying slip, 284.19 for 274.19 — sat under 2022-07-07, where the
    false-reading test below could not see it (found 2026-10-10)."""
    import re
    m = (re.search(r"to (\d{4}-\d{2}-\d{2}) flood day", text)
         or re.search(r"to (\d{4}-\d{2}-\d{2}) flood day", note or ""))
    return m.group(1) if m else text[:10]


def _j(name: str):
    return json.loads((R / name).read_text(encoding="utf-8"))


def false_gauge_days(stations: dict) -> set[tuple[str, str]]:
    """(station, day) pairs where a level gauge was at its line only through
    readings the cleaning removes: the cleaning lowers that day's high, and
    the cleaned high is below the line. Four of the 48 gauge-found floods at
    level gauges on 2026-10-09 — Pangin 2019-08-09, Jollang 2020-05-04 and
    2022-09-05, Doimukh 2024-11-17 (FLOOD_WHEN_PILOT_PLAN.md §13g, §15). A
    day below today's line on true readings is NOT one of these."""
    import contextlib
    import io
    sys.path.insert(0, str(ROOT / "scripts" / "model"))
    from backtest_flood_when import clean_readings
    out = set()
    for code, st in stations.items():
        f = ROOT / "data" / "raw" / "11_gauges" / "cwc" / f"{code}_hhs.csv"
        if not f.exists():                      # NWDP flow gauges: no such cleaning
            continue
        d = (pd.read_csv(f, parse_dates=["datetime"])[["datetime", "level"]].dropna()
             .sort_values("datetime").reset_index(drop=True))
        with contextlib.redirect_stdout(io.StringIO()):
            c = clean_readings(d.copy())
        raw = d.groupby(d["datetime"].dt.normalize())["level"].max()
        cln = c.groupby(c["datetime"].dt.normalize())["level"].max().reindex(raw.index)
        bad = (raw - cln.fillna(-np.inf) > 1e-6) & ~(cln >= st["threshold"])
        out |= {(code, str(t.date())) for t in raw.index[bad]}
    return out


def build() -> pd.DataFrame:
    rows = []
    # candidates the radar screens looked at: uuid -> date, lat, lon
    cand = {}
    for n in ["flood_where_groundsource_s1_ee_screen.json",
              "flood_where_groundsource_pre2019_s1_ee_screen.json",
              "flood_where_groundsource_widewindow_recheck.json"]:
        for r in _j(n)["results"]:
            cand.setdefault(r["uuid"], (r["date_str"], r["lat"], r["lon"]))

    # 1. the validated radar test
    thr = _j("flood_radar_test_validation.json")["threshold_share_pct_from_half_A"] / 100
    for line in (INTERIM / "flood_where" / "radar_recheck.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("new_share") is not None and r["new_share"] > thr:
            rows.append({"uuid": r["key"], "date": r["date"], "lat": r["lat"], "lon": r["lon"],
                         "route": "radar"})
    # 2. Google's Global Flood Database
    for r in _j("flood_where_groundsource_gfd_check.json")["results"]:
        if r.get("gfd_match"):
            rows.append({"uuid": r["uuid"], "date": r["date_str"], "lat": r["lat"],
                         "lon": r["lon"], "route": "gfd"})
    # 3. reports a nearby gauge crossing confirmed
    for n in ["flood_where_groundsource_gauge_crosscheck.json",
              "flood_where_groundsource_2019plus_gauge_crosscheck.json"]:
        for r in _j(n)["results"]:
            if r.get("gauge_confirmed"):
                rows.append({"uuid": r["uuid"], "date": r["date_str"], "lat": r["lat"],
                             "lon": r["lon"], "route": "gauge-xc"})
    # 4. floods found from gauges, checked with our own radar processing
    st = json.loads((ROOT / "models" / "flood_when_gauge" / "stations.json").read_text())
    false_days = false_gauge_days(st)
    for n in GAUGE_FIRST:
        for r in _j(n)["results"]:
            if (r.get("pct_new_water_flood_only") or 0) > 0 and r["station_code"] in st:
                s = st[r["station_code"]]
                day = _day(r["flood_date"], r.get("note", ""))
                if (r["station_code"], day) in false_days:
                    DROPPED.append(f"gauge:{r['station_code']}:{day}")
                    continue
                rows.append({"uuid": f"gauge:{r['station_code']}:{day}",
                             "date": day, "lat": s["lat"], "lon": s["lon"],
                             "route": "gauge"})
    for r in _j("flood_where_s1_jang_multi_date.json")["results"]:
        if (r.get("pct_new_water_flood_only") or 0) > 0:
            day = _day(r["flood_date"])
            rows.append({"uuid": f"gauge:jang:{day}", "date": day,
                         "lat": JANG[0], "lon": JANG[1], "route": "gauge"})

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    sus = set(_j("flood_paddy_check.json")["channel_shift_suspects"]["uuids"])
    df = df[~df["uuid"].isin(sus)]
    ev = (df.groupby("uuid").agg(date=("date", "first"), lat=("lat", "first"),
                                 lon=("lon", "first"),
                                 routes=("route", lambda s: ",".join(sorted(set(s)))))
          .reset_index())
    # one event per place-day across routes (a gauge event and a report of it)
    ev["cell"] = (np.round(ev["lat"] / 0.018).astype(int).astype(str) + "_"
                  + np.round(ev["lon"] / 0.02).astype(int).astype(str))
    ev = ev.sort_values("uuid").drop_duplicates(["date", "cell"]).drop(columns="cell")
    masks = {p.stem for p in (INTERIM / "flood_where_pixels").glob("*.npz")}
    ev["has_mask"] = ev["uuid"].isin(masks)
    ev["reported_record"] = ev["uuid"].isin(set(_train_uuids()))
    return ev.reset_index(drop=True)


def _train_uuids() -> list[str]:
    sys.path.insert(0, str(ROOT / "scripts" / "model"))
    from flood_forecast import load_events
    return list(load_events()["uuid"])


def main() -> None:
    ev = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ev.to_parquet(OUT, index=False)
    by_route = {}
    for rs in ev["routes"]:
        for r in rs.split(","):
            by_route[r] = by_route.get(r, 0) + 1
    train = set(_train_uuids())
    sus = set(_j("flood_paddy_check.json")["channel_shift_suspects"]["uuids"])
    out = {"what": "flood events confirmed by at least one independent route (PARKED §0x)",
           "events": int(len(ev)), "by_route": by_route,
           "with_pixel_masks": int(ev["has_mask"].sum()),
           "of_the_reported_training_record": {
               "records": len(train - sus),
               "verified": int(ev["reported_record"].sum()),
               "share": round(float(ev["reported_record"].sum()) / max(len(train - sus), 1), 3)},
           "verified_but_not_in_the_old_training_record": int((~ev["reported_record"]).sum()),
           "gauge_floods_left_out_as_false_readings": sorted(set(DROPPED)),
           "by_year": ev.groupby(ev["date"].dt.year).size().to_dict()}
    REPORT.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
