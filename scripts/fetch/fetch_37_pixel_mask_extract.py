"""Phase 1 of turning the "provisional" Earth-Engine screen results into
actual pixel-level training data (see docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md
§5n and the "provisional means two things" clarification in chat
2026-09-08): pull the REAL per-pixel flood mask for every screen-positive
candidate, not just the one summary percentage fetch_32/33/36 computed.

Still free, still no download of any raw scene, still the same Sentinel-1
data already inside Earth Engine — this only changes what we ASK Earth
Engine for: instead of `reduceRegion` (one averaged number), it uses
`ee.data.computePixels` to pull the actual small raster around each
point. Reuses fetch_32's now-fixed deterministic `pick_image_near` for
the flood/baseline image selection, so every mask here is built from the
exact same scene the screening step already decided on.

Per-event output: a 10m-resolution, 10km x 10km (1000x1000 px) 3-band
uint8 array —
    fw = flood-day water (VV < -17dB)
    bw = baseline (dry-season) water
    nw = new water = fw AND NOT bw   (the actual positive-class mask)
saved compressed (`np.savez_compressed`) to keep the ~3,546-event total
well under what raw arrays would need. `ee.data.computePixels` itself
caps a single request at 50MB — 10km at 10m x3 bands uint8 is ~3MB,
comfortably inside that with room to spare (a full 33km box, matching
the original screening buffer, was tested and does NOT fit: 66.5MB).

Candidates: every `screen_positive: true` row across fetch_32, fetch_33,
and fetch_36's reports (2,178 + 616 + 752 = 3,546, confirmed disjoint by
uuid in chat 2026-09-08 — fetch_36's candidates are a subset of
fetch_32/33's own "no image" rows, never their positives).

    python scripts/fetch/fetch_37_pixel_mask_extract.py

Output:
    data/interim/flood_where_pixels/<uuid>.npz   (one per event)
    reports/flood_where_pixel_mask_extract.json  (progress/summary)
"""
from __future__ import annotations

PER_CANDIDATE_TIMEOUT_S = 60
HALF_M = 5000          # 10km x 10km box
SCALE_M = 10            # native Sentinel-1 GRD resolution
WATER_DB = -17.0

import datetime as dt
import io
import json
import math
import sys
from pathlib import Path

import ee
import numpy as np


def lonlat_to_webmercator(lon: float, lat: float) -> tuple[float, float]:
    """Closed-form EPSG:4326 -> EPSG:3857, done locally instead of a
    `pt.transform(...).getInfo()` round-trip to Earth Engine per
    candidate — that extra network call was a meaningful chunk of the
    ~27s/candidate seen in the first timing test, purely to compute
    something with no server-side dependency at all."""
    R = 6378137.0
    x = math.radians(lon) * R
    y = math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R
    return x, y

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_32_groundsource_s1_ee_screen as scr  # reuse s1_vv / pick_image_near / get_baseline

OUT_DIR = ROOT / "data" / "interim" / "flood_where_pixels"
REPORT_OUT = ROOT / "reports" / "flood_where_pixel_mask_extract.json"

SOURCE_REPORTS = [
    ROOT / "reports" / "flood_where_groundsource_s1_ee_screen.json",
    ROOT / "reports" / "flood_where_groundsource_pre2019_s1_ee_screen.json",
    ROOT / "reports" / "flood_where_groundsource_widewindow_recheck.json",
]

W = H = int(2 * HALF_M / SCALE_M)


def load_candidates() -> list[dict]:
    seen = {}
    for p in SOURCE_REPORTS:
        d = json.loads(p.read_text(encoding="utf-8"))
        for r in d["results"]:
            if r.get("screen_positive") and r["uuid"] not in seen:
                seen[r["uuid"]] = r
    return list(seen.values())


def extract_one(c: dict) -> dict:
    pt = ee.Geometry.Point([c["lon"], c["lat"]])
    d = dt.date.fromisoformat(c["date_str"])
    pad = c.get("date_pad_days", 3)
    d0 = (d - dt.timedelta(days=pad)).isoformat()
    d1 = (d + dt.timedelta(days=pad + 1)).isoformat()

    col = scr.s1_vv(pt, d0, d1)
    target_millis = dt.datetime.combine(d, dt.time()).timestamp() * 1000
    flood_img = scr.pick_image_near(col, target_millis)
    if flood_img is None:
        return {"uuid": c["uuid"], "status": "no_image_on_reextract"}

    orbit = int(flood_img.get("relativeOrbitNumber_start").getInfo())
    base_img = scr.get_baseline(orbit, pt)
    if base_img is None:
        return {"uuid": c["uuid"], "status": "no_baseline_on_reextract"}

    fw = flood_img.select("VV").lt(WATER_DB).rename("fw")
    bw = base_img.lt(WATER_DB).rename("bw")
    nw = fw.And(bw.Not()).rename("nw")
    stack = ee.Image.cat([fw, bw, nw]).toByte()

    pt3857 = lonlat_to_webmercator(c["lon"], c["lat"])
    params = {
        "expression": stack,
        "fileFormat": "NPY",
        "grid": {
            "dimensions": {"width": W, "height": H},
            "affineTransform": {
                "scaleX": SCALE_M, "shearX": 0, "translateX": pt3857[0] - HALF_M,
                "shearY": 0, "scaleY": -SCALE_M, "translateY": pt3857[1] + HALF_M,
            },
            "crsCode": "EPSG:3857",
        },
    }
    raw = ee.data.computePixels(params)
    arr = np.load(io.BytesIO(raw))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT_DIR / f"{c['uuid']}.npz",
        fw=arr["fw"], bw=arr["bw"], nw=arr["nw"],
        lat=c["lat"], lon=c["lon"], half_m=HALF_M, scale_m=SCALE_M,
    )
    pct_new = round(100 * float(arr["nw"].mean()), 2)
    return {"uuid": c["uuid"], "status": "ok", "orbit": orbit,
            "pct_new_water_10km_crop": pct_new,
            "pct_new_water_screen": c.get("pct_new_water_screen")}


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    candidates = load_candidates()
    print(f"Pixel-mask extraction — {len(candidates)} screen-positive candidates "
          f"(fetch_32+33+36 combined, deduplicated)\n")

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
            fut = executor.submit(extract_one, c)
            results.append(fut.result(timeout=PER_CANDIDATE_TIMEOUT_S))
        except concurrent.futures.TimeoutError:
            print(f"  [TIMEOUT] {c['uuid']}: stuck >{PER_CANDIDATE_TIMEOUT_S}s, skipping (will retry)")
            executor.shutdown(wait=False, cancel_futures=True)
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {c['uuid']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")
        if n_processed % 25 == 0 or n_processed == len(candidates):
            n_ok = sum(1 for r in results if r.get("status") == "ok")
            print(f"  ...{len(results)}/{n_total}  (ok so far: {n_ok})")
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            REPORT_OUT.write_text(encoding="utf-8", data=json.dumps({
                "note": f"Real per-pixel flood masks (fw/bw/nw, {W}x{H} @ {SCALE_M}m) "
                        f"saved to data/interim/flood_where_pixels/<uuid>.npz for every "
                        f"screen-positive candidate. method='earth_engine_native' "
                        f"pixel data, same provisional-precision caveat as the screen "
                        f"itself (see PARKED_HIMALAYAN_FLOOD_WHERE.md §0e/§5n).",
                "n_candidates": n_total, "n_checked_so_far": len(results),
                "results": results,
            }, indent=2, ensure_ascii=False))

    n_ok = sum(1 for r in results if r.get("status") == "ok")
    n_fail = len(results) - n_ok
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_ok}/{n_total} masks extracted and saved to {OUT_DIR}")
    print(f"{n_fail}/{n_total} failed on re-extraction (unexpected — flag for review)")


if __name__ == "__main__":
    main()
