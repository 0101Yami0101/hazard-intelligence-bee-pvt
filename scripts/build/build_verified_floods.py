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
               our own full-quality radar processing and showing new water

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
GAUGE_FIRST = ["flood_where_s1_statewide.json", "flood_where_s1_statewide_expanded.json",
               "flood_where_s1_nwdp.json", "flood_where_s1_loose_ends.json"]


def _day(text: str) -> str:
    """A gauge event's flood day. Some are annotated, e.g. "2024-10-05 (nearest
    scene to 2024-10-04 flood day, 1 day off)" — the flood day is the date."""
    import re
    m = re.search(r"to (\d{4}-\d{2}-\d{2}) flood day", text)
    return m.group(1) if m else text[:10]


def _j(name: str):
    return json.loads((R / name).read_text(encoding="utf-8"))


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
    for n in GAUGE_FIRST:
        for r in _j(n)["results"]:
            if (r.get("pct_new_water_flood_only") or 0) > 0 and r["station_code"] in st:
                s = st[r["station_code"]]
                day = _day(r["flood_date"])
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
           "by_year": ev.groupby(ev["date"].dt.year).size().to_dict()}
    REPORT.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))
    print(f"  wrote {OUT}")


if __name__ == "__main__":
    main()
