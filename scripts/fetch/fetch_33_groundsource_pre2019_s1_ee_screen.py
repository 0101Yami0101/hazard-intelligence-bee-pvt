"""Same free, no-download Sentinel-1-in-Earth-Engine screen as
fetch_32_groundsource_s1_ee_screen.py, pointed at the pre-2019 Groundsource
candidates that neither GFD (fetch_31) nor the gauge cross-check
(gauge_crosscheck_groundsource.py) could confirm, restricted to dates
Sentinel-1 can actually reach (>= 2014-10-03).

Context: pre-2019 had 1,946 candidates; 208 already confirmed (185 GFD +
23 gauge); of the remaining 1,738 unconfirmed, 1,056 fall inside
Sentinel-1's operational window (2014-2018) and 682 are genuinely too old
for any Sentinel-1-based method (GFD/gauge were already the best options
for those — no further free avenue right now, see
docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §5n).

Candidates: data/interim/flood_when/groundsource_aru_pre2019_s1window_unconfirmed.json
(built in chat 2026-09-07 from groundsource_aru_pre2019.json minus the GFD-
and gauge-confirmed uuids, minus dates before 2014-10-03).

Per the 2026-09-07 decision (§5n): Earth Engine's numbers are used here as
the practical, fast, no-download method NOW (10/12 known-event dates
agreed within ~1pp in direct validation; 2/12 were off by ~6pp — see §5n
for the full table and root cause). Tag every result `method:
"earth_engine_native"` and do not treat it as equivalent to a locally-
downloaded-and-calibrated number until Phase 2 (re-verify once
compute/storage is upgraded) happens.

    python scripts/fetch/fetch_33_groundsource_pre2019_s1_ee_screen.py

Output:
    reports/flood_where_groundsource_pre2019_s1_ee_screen.json
"""
from __future__ import annotations

PER_CANDIDATE_TIMEOUT_S = 60

import datetime as dt
import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "data" / "interim" / "flood_when" / "groundsource_aru_pre2019_s1window_unconfirmed.json"
REPORT_OUT = ROOT / "reports" / "flood_where_groundsource_pre2019_s1_ee_screen.json"
DATE_PAD_DAYS = 3
WATER_DB = -17.0
BUFFER_M = 16650

S1 = "COPERNICUS/S1_GRD"
_baseline_cache: dict[int, ee.Image] = {}

BASELINE_WINDOWS = [("2025-03-01", "2025-04-01"), ("2020-03-01", "2020-04-01"),
                     ("2019-03-01", "2019-04-01"), ("2022-03-01", "2022-04-01")]


def s1_vv(pt: ee.Geometry, d0: str, d1: str) -> ee.ImageCollection:
    return (ee.ImageCollection(S1).filterBounds(pt).filterDate(d0, d1)
             .filter(ee.Filter.eq("instrumentMode", "IW"))
             .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")))


def pick_image_near(col: ee.ImageCollection, target_millis: float) -> ee.Image | None:
    """`.first()` on an unsorted collection is NOT guaranteed to return the
    same image across separate calls — see fetch_32's identical fix and
    docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §0e for the full story.
    Deterministically pick the image closest to a well-defined target
    (ties broken by system:index) instead."""
    n = col.size().getInfo()
    if n == 0:
        return None
    if n == 1:
        return ee.Image(col.first())
    ids = col.aggregate_array("system:index").getInfo()
    times = col.aggregate_array("system:time_start").getInfo()
    best = min(range(len(times)), key=lambda i: (abs(times[i] - target_millis), ids[i]))
    return ee.Image(col.filter(ee.Filter.eq("system:index", ids[best])).first())


def get_baseline(orbit: int, pt: ee.Geometry) -> ee.Image | None:
    if orbit in _baseline_cache:
        return _baseline_cache[orbit]
    for d0, d1 in BASELINE_WINDOWS:
        col = s1_vv(pt, d0, d1).filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
        if col.size().getInfo() > 0:
            mid = dt.date.fromisoformat(d0) + (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)) / 2
            target_millis = dt.datetime.combine(mid, dt.time()).timestamp() * 1000
            img = pick_image_near(col, target_millis)
            if img is not None:
                img = img.select("VV")
                _baseline_cache[orbit] = img
                return img
    _baseline_cache[orbit] = None
    return None


def process_one(c: dict) -> dict:
    pt = ee.Geometry.Point([c["lon"], c["lat"]])
    d = dt.date.fromisoformat(c["date_str"])
    d0 = (d - dt.timedelta(days=DATE_PAD_DAYS)).isoformat()
    d1 = (d + dt.timedelta(days=DATE_PAD_DAYS + 1)).isoformat()

    col = s1_vv(pt, d0, d1)
    target_millis = dt.datetime.combine(d, dt.time()).timestamp() * 1000
    flood_img = pick_image_near(col, target_millis)
    if flood_img is None:
        return {**c, "s1_image_found": False}

    orbit = int(flood_img.get("relativeOrbitNumber_start").getInfo())
    scene_date = ee.Date(flood_img.get("system:time_start")).format("YYYY-MM-dd").getInfo()

    base_img = get_baseline(orbit, pt)
    if base_img is None:
        return {**c, "s1_image_found": True, "scene_date": scene_date, "orbit": orbit,
                "baseline_found": False}

    region = pt.buffer(BUFFER_M)
    fw = flood_img.select("VV").lt(WATER_DB)
    bw = base_img.lt(WATER_DB)
    nw = fw.And(bw.Not())
    stats = ee.Image.cat([fw.rename("fw"), bw.rename("bw"), nw.rename("nw")]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e9, bestEffort=True,
    ).getInfo()
    pct_new = round(100 * (stats.get("nw") or 0), 2)
    return {**c, "s1_image_found": True, "scene_date": scene_date, "orbit": orbit,
            "baseline_found": True,
            "pct_flood_day_water": round(100 * (stats.get("fw") or 0), 2),
            "pct_baseline_water": round(100 * (stats.get("bw") or 0), 2),
            "pct_new_water_screen": pct_new,
            "screen_positive": pct_new > 0.3,
            "method": "earth_engine_native"}


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    candidates = json.loads(CANDIDATES_IN.read_text())
    print(f"Groundsource pre-2019 (2014-2018), GFD+gauge-unconfirmed candidates — "
          f"{len(candidates)} to screen via Sentinel-1-in-Earth-Engine (no downloads; "
          f"provisional method, see script docstring / doc §5n)\n")

    n_total = len(candidates)
    results = []
    if REPORT_OUT.exists():
        prior = json.loads(REPORT_OUT.read_text())
        results = prior.get("results", [])
        n_total = prior.get("n_candidates", n_total)
        done = {r["uuid"] for r in results}
        candidates = [c for c in candidates if c["uuid"] not in done]
        print(f"resuming: {len(results)} already done, {len(candidates)} left\n")

    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    n_processed = 0
    for c in candidates:
        n_processed += 1
        try:
            fut = executor.submit(process_one, c)
            results.append(fut.result(timeout=PER_CANDIDATE_TIMEOUT_S))
        except concurrent.futures.TimeoutError:
            print(f"  [TIMEOUT] {c['uuid']}: stuck >{PER_CANDIDATE_TIMEOUT_S}s, "
                  f"skipping (will retry next run)")
            executor.shutdown(wait=False, cancel_futures=True)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {c['uuid']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")
        if n_processed % 50 == 0 or n_processed == len(candidates):
            print(f"  ...{len(results)}/{n_total}")
            n_found = sum(1 for r in results if r.get("s1_image_found"))
            n_pos = sum(1 for r in results if r.get("screen_positive"))
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            REPORT_OUT.write_text(json.dumps({
                "note": "Provisional Earth-Engine-native confirmation for pre-2019 "
                        "(2014-2018) Groundsource candidates GFD/gauge could not "
                        "confirm. method='earth_engine_native' throughout — see "
                        "docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §5n for the "
                        "validated ~1-6pp uncertainty vs a locally-calibrated check, "
                        "and the plan to re-verify once local compute/storage allows.",
                "n_candidates": n_total, "n_checked_so_far": len(results),
                "n_s1_image_found": n_found, "n_screen_positive": n_pos,
                "results": results,
            }, indent=2))

    n_found = sum(1 for r in results if r.get("s1_image_found"))
    n_pos = sum(1 for r in results if r.get("screen_positive"))
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_found}/{n_total} had a Sentinel-1 image nearby at all")
    print(f"{n_pos}/{n_total} screened positive (counted, method=earth_engine_native)")


if __name__ == "__main__":
    main()
