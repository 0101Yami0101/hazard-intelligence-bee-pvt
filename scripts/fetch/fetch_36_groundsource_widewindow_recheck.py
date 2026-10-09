"""Re-check the 987 Groundsource Arunachal candidates (2014-2018 and
2019+ combined) that came back "no Sentinel-1 image found" from
fetch_32/fetch_33's +-3-day window — NOT because no satellite exists for
their era (they're all inside Sentinel-1's real 2014-present coverage),
but because that window may simply have been too narrow for this
region's real revisit cycle (6-12 days depending on orbit combination).

This is a completely different problem from the 682 pre-Oct-2014
candidates (fetch_34/35) — those have NO satellite option at all pre-
Sentinel-1; these 987 do, they just might need a wider net. No new data
source, no login, same free Earth Engine method already proven in
fetch_32/33, just DATE_PAD_DAYS raised from 3 to 10.

User's question, 2026-09-07: "What about the other that screened
negative... those which couldn't be verified because there is no
satellite image for that timeframe?" — this script is the direct answer:
widen the window on exactly that subset before reaching for a different
satellite. See docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §0c/§0d.

Candidates: built in chat from the "no image found" rows of
reports/flood_where_groundsource_pre2019_s1_ee_screen.json and
reports/flood_where_groundsource_s1_ee_screen.json, minus anything the
gauge cross-check already confirmed.

    python scripts/fetch/fetch_36_groundsource_widewindow_recheck.py

Output:
    reports/flood_where_groundsource_widewindow_recheck.json
"""
from __future__ import annotations

PER_CANDIDATE_TIMEOUT_S = 60
DATE_PAD_DAYS = 10  # was 3 in fetch_32/33 — the only change that matters here

import datetime as dt
import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "data" / "interim" / "flood_when" / "groundsource_aru_widewindow_recheck.json"
REPORT_OUT = ROOT / "reports" / "flood_where_groundsource_widewindow_recheck.json"
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
    same image across separate calls — found 2026-09-08 via a user-
    prompted re-check: the SAME candidate flipped between screen_positive
    True and False on repeated runs with zero code change. Root cause:
    a wide +-10-day window makes 2+ matching images common (~70% of a
    direct sample here), and Earth Engine documents no stable default
    order for `.first()` on an unsorted collection. Fix: deterministically
    pick the single image whose acquisition time is closest to a
    well-defined target (ties broken by system:index), so repeated calls
    are 100% reproducible — verified by direct re-run after this fix."""
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
            mid = (dt.date.fromisoformat(d0) + (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)) / 2)
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
        return {**c, "s1_image_found": False, "date_pad_days": DATE_PAD_DAYS}

    orbit = int(flood_img.get("relativeOrbitNumber_start").getInfo())
    scene_date = ee.Date(flood_img.get("system:time_start")).format("YYYY-MM-dd").getInfo()

    base_img = get_baseline(orbit, pt)
    if base_img is None:
        return {**c, "s1_image_found": True, "scene_date": scene_date, "orbit": orbit,
                "baseline_found": False, "date_pad_days": DATE_PAD_DAYS}

    region = pt.buffer(BUFFER_M)
    fw = flood_img.select("VV").lt(WATER_DB)
    bw = base_img.lt(WATER_DB)
    nw = fw.And(bw.Not())
    stats = ee.Image.cat([fw.rename("fw"), bw.rename("bw"), nw.rename("nw")]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=10, maxPixels=1e9, bestEffort=True,
    ).getInfo()
    pct_new = round(100 * (stats.get("nw") or 0), 2)
    days_from_report = abs((dt.date.fromisoformat(scene_date) - d).days)
    return {**c, "s1_image_found": True, "scene_date": scene_date, "orbit": orbit,
            "baseline_found": True, "date_pad_days": DATE_PAD_DAYS,
            "days_scene_from_reported_date": days_from_report,
            "pct_new_water_screen": pct_new,
            "screen_positive": pct_new > 0.3,
            "method": "earth_engine_native_widewindow"}


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    candidates = json.loads(CANDIDATES_IN.read_text(encoding="utf-8"))
    print(f"Wide-window (+-{DATE_PAD_DAYS}d) Sentinel-1-in-EE re-check — "
          f"{len(candidates)} candidates that had NO image at all in the "
          f"original +-3d window (not a coverage-era problem, just possibly "
          f"too narrow a search — see script docstring)\n")

    n_total = len(candidates)
    results = []
    if REPORT_OUT.exists():
        try:
            prior = json.loads(REPORT_OUT.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            prior = json.loads(REPORT_OUT.read_text(encoding="cp1252"))
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
            print(f"  [TIMEOUT] {c['uuid']}: stuck >{PER_CANDIDATE_TIMEOUT_S}s, skipping (will retry)")
            executor.shutdown(wait=False, cancel_futures=True)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {c['uuid']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")
        if n_processed % 50 == 0 or n_processed == len(candidates):
            print(f"  ...{len(results)}/{n_total}")
            n_found = sum(1 for r in results if r.get("s1_image_found"))
            n_pos = sum(1 for r in results if r.get("screen_positive"))
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            REPORT_OUT.write_text(encoding="utf-8", data=json.dumps({
                "note": f"Re-check of candidates that had NO Sentinel-1 image in the "
                        f"original +-3-day window, now with +-{DATE_PAD_DAYS} days. "
                        f"method='earth_engine_native_widewindow' — same provisional "
                        f"caveat as the original screen (see PARKED_HIMALAYAN_FLOOD_WHERE.md "
                        f"§0c/§0d). A wider window trades date precision for a real chance "
                        f"at finding a pass at all.",
                "n_candidates": n_total, "n_checked_so_far": len(results),
                "n_s1_image_found": n_found, "n_screen_positive": n_pos,
                "results": results,
            }, indent=2, ensure_ascii=False))

    n_found = sum(1 for r in results if r.get("s1_image_found"))
    n_pos = sum(1 for r in results if r.get("screen_positive"))
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_found}/{n_total} now have a Sentinel-1 image with the wider window")
    print(f"{n_pos}/{n_total} screened positive")


if __name__ == "__main__":
    main()
