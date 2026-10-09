"""FREE, no-download screen for Groundsource's 2019+ Arunachal candidates,
using Sentinel-1 imagery hosted directly inside Google Earth Engine
(`COPERNICUS/S1_GRD`) instead of Google's Global Flood Database (which
can't reach these years — see docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md
§5i).

IMPORTANT — this is a SCREEN, not a final number. Validated in chat
2026-09-05 against 4 events already confirmed real via our own downloaded
+ calibrated Sentinel-1 pipeline: this method agrees on *is this a real
flood* every time, but the exact percentage does not match our own
pipeline's number precisely (different processing). Do NOT feed this
script's percentages into training/calibration directly — use it only to
decide which candidates are worth a real download (fetch_27/29-style)
for the precise number. See §5i for the full validation table.

Candidates: data/interim/flood_when/groundsource_aru_2019plus.json (built
in chat from data/raw/16_groundsource/groundsource_2026.parquet).

    python scripts/fetch/fetch_32_groundsource_s1_ee_screen.py

Output:
    reports/flood_where_groundsource_s1_ee_screen.json
"""
from __future__ import annotations

# 2026-09-06: this batch stalled silently for several minutes on a single
# candidate — no exception, no progress, Earth Engine itself confirmed
# healthy at the time (a plain ee.Number(1).getInfo() call answered in
# under a second). None of the ee.* calls below accept a timeout
# parameter directly, so process_one() is wrapped in a hard thread
# timeout in main() below — a single slow candidate can no longer hang
# the whole batch; it's just marked failed/retryable and the batch moves
# on, same "never let one item block everything" discipline as
# fetch_27/29's per-candidate try/except.
PER_CANDIDATE_TIMEOUT_S = 60

import datetime as dt
import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "data" / "interim" / "flood_when" / "groundsource_aru_2019plus.json"
REPORT_OUT = ROOT / "reports" / "flood_where_groundsource_s1_ee_screen.json"
DATE_PAD_DAYS = 3
WATER_DB = -17.0
BUFFER_M = 16650  # ~0.15 deg at these latitudes, matches our own pipeline's window

S1 = "COPERNICUS/S1_GRD"
_baseline_cache: dict[int, ee.Image] = {}

# a handful of known-dry-season windows to search for a per-orbit baseline,
# newest first (closest to "now" tends to have the most reliable archive).
BASELINE_WINDOWS = [("2025-03-01", "2025-04-01"), ("2020-03-01", "2020-04-01"),
                     ("2019-03-01", "2019-04-01"), ("2022-03-01", "2022-04-01")]


def s1_vv(pt: ee.Geometry, d0: str, d1: str) -> ee.ImageCollection:
    return (ee.ImageCollection(S1).filterBounds(pt).filterDate(d0, d1)
             .filter(ee.Filter.eq("instrumentMode", "IW"))
             .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")))


def pick_image_near(col: ee.ImageCollection, target_millis: float) -> ee.Image | None:
    """`.first()` on an unsorted collection is NOT guaranteed to return the
    same image across separate calls — found 2026-09-08 via a user-
    prompted re-check after this script's results were already reported:
    ~47% of a direct sample here have 2+ matching images in their +-3-day
    window, and Earth Engine documents no stable default order for
    `.first()` on an unsorted collection, so the SAME candidate could
    flip between screen_positive True/False on repeated runs with zero
    code change. Fix: deterministically pick the single image whose
    acquisition time is closest to a well-defined target (ties broken by
    system:index) — verified 100% reproducible across repeated calls
    after this fix. See docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §0e."""
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
            "screen_positive": pct_new > 0.3}  # small margin above zero, not a precise cutoff


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    candidates = json.loads(CANDIDATES_IN.read_text())
    print(f"Groundsource 2019+ Arunachal candidates — {len(candidates)} to screen "
          f"via Sentinel-1-in-Earth-Engine (no downloads; this is a FILTER, not a "
          f"final number — see script docstring)\n")

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
            # don't append anything for this uuid — leaving it out of
            # `results` means the next run's resume logic will retry it,
            # instead of permanently mislabeling "couldn't check" as "done"
            print(f"  [TIMEOUT] {c['uuid']}: stuck >{PER_CANDIDATE_TIMEOUT_S}s, "
                  f"skipping (will retry next run)")
            executor.shutdown(wait=False, cancel_futures=True)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        except Exception as exc:  # noqa: BLE001
            # same reasoning — a real error is transient/unknown, not a
            # confirmed result, so don't mark it done either
            print(f"  [FAIL] {c['uuid']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")
        if n_processed % 50 == 0 or n_processed == len(candidates):
            print(f"  ...{len(results)}/{n_total}")
            n_found = sum(1 for r in results if r.get("s1_image_found"))
            n_pos = sum(1 for r in results if r.get("screen_positive"))
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            REPORT_OUT.write_text(json.dumps({
                "note": "SCREEN ONLY, not final data — see script docstring for the "
                        "validated precision caveat. screen_positive=True means "
                        "worth a real local download for the precise number.",
                "n_candidates": n_total, "n_checked_so_far": len(results),
                "n_s1_image_found": n_found, "n_screen_positive": n_pos,
                "results": results,
            }, indent=2))

    n_found = sum(1 for r in results if r.get("s1_image_found"))
    n_pos = sum(1 for r in results if r.get("screen_positive"))
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_found}/{n_total} had a Sentinel-1 image nearby at all")
    print(f"{n_pos}/{n_total} screened positive — worth a real local download")


if __name__ == "__main__":
    main()
