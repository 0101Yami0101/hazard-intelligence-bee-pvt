"""Does Earth Engine's already-preprocessed Sentinel-1 (no download at all)
agree with our own locally-downloaded-and-calibrated pipeline
(sentinel1_flood_evidence.py), closely enough to use EE as the real source
of pixel-level flood data instead of downloading raw scenes?

Local download of one Sentinel-1 scene + our own calibration is 30+ minutes
and ~1 GB; a candidate list of ~2,200 events at that rate is 1,000+ hours.
Earth Engine already stores Sentinel-1 pre-calibrated (and, unlike our
local pipeline, actually terrain-corrected with a real DEM, which matters
in mountains) — if EE's numbers track our local numbers, we can get a
flood mask for every candidate in seconds, not half an hour.

This re-runs the EXACT same 12 Jang-valley dates, same per-orbit baseline
SCENES (not a generic search — matched to the identical baseline acquisition
dates used locally, for a true apples-to-apples test), same buffer, same
-17 dB water threshold, same "new water = flood-day water AND NOT
baseline-day water" logic as sentinel1_flood_evidence.py, but computed
entirely server-side in Earth Engine via reduceRegion — zero local download.

    python scripts/model/sentinel1_ee_validate_jang.py

Output: reports/flood_where_s1_ee_vs_local_jang.json, plus a printed
side-by-side table against reports/flood_where_s1_jang_multi_date.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
LOCAL_REPORT = ROOT / "reports" / "flood_where_s1_jang_multi_date.json"
OUT = ROOT / "reports" / "flood_where_s1_ee_vs_local_jang.json"

JANG_LAT, JANG_LON = 27.5834, 91.9802
BUF_DEG = 0.15
WATER_DB_THRESHOLD = -17.0
S1 = "COPERNICUS/S1_GRD"

# Same flood dates + same orbits as sentinel1_flood_evidence.py's FLOOD_SCENES
# / DATE_ORBIT (2020-07-20 dropped there too — no coverage; kept out here).
FLOOD_DATES = ["2019-07-09", "2019-07-14", "2019-08-02", "2020-05-21",
               "2020-05-23", "2020-06-21", "2020-06-26", "2020-07-21",
               "2020-07-22", "2021-08-27", "2023-08-24", "2025-08-31"]
DATE_ORBIT = {
    "2019-07-09": 150, "2019-08-02": 150, "2020-06-21": 150, "2021-08-27": 150,
    "2019-07-14": 41, "2020-05-21": 41, "2020-06-26": 41,
    "2020-05-23": 77, "2020-07-21": 77, "2020-07-22": 77, "2023-08-24": 77,
    "2025-08-31": 77,
}
# Same baseline ACQUISITION DATES as BASELINE_BY_ORBIT in sentinel1_flood_evidence.py
# (the scene names there encode these dates) — matched here by date, not a
# generic dry-season search, so the baseline scene is the same one.
BASELINE_DATE_BY_ORBIT = {150: "2025-03-03", 41: "2025-02-24", 77: "2025-02-26"}


def region() -> ee.Geometry:
    return ee.Geometry.Rectangle([JANG_LON - BUF_DEG, JANG_LAT - BUF_DEG,
                                   JANG_LON + BUF_DEG, JANG_LAT + BUF_DEG])


def s1_vv_on(date_str: str, orbit: int) -> ee.Image | None:
    d0 = ee.Date(date_str)
    col = (ee.ImageCollection(S1).filterBounds(region())
             .filterDate(d0.advance(-1, "day"), d0.advance(2, "day"))
             .filter(ee.Filter.eq("instrumentMode", "IW"))
             .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
             .filter(ee.Filter.eq("relativeOrbitNumber_start", orbit)))
    n = col.size().getInfo()
    if n == 0:
        return None
    return ee.Image(col.first()).select("VV")


_baseline_cache: dict[int, ee.Image | None] = {}


def baseline_for_orbit(orbit: int) -> ee.Image | None:
    if orbit not in _baseline_cache:
        _baseline_cache[orbit] = s1_vv_on(BASELINE_DATE_BY_ORBIT[orbit], orbit)
    return _baseline_cache[orbit]


def check_one(date: str) -> dict | None:
    orbit = DATE_ORBIT[date]
    flood_img = s1_vv_on(date, orbit)
    if flood_img is None:
        return None
    base_img = baseline_for_orbit(orbit)
    if base_img is None:
        return None

    reg = region()
    fw = flood_img.lt(WATER_DB_THRESHOLD)
    bw = base_img.lt(WATER_DB_THRESHOLD)
    nw = fw.And(bw.Not())
    stats = ee.Image.cat([fw.rename("fw"), bw.rename("bw"), nw.rename("nw")]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=reg, scale=10, maxPixels=1e9, bestEffort=True,
    ).getInfo()
    return {
        "flood_date": date, "orbit": orbit,
        "pct_water_flood_day": round(100 * (stats.get("fw") or 0), 2),
        "pct_water_baseline_day": round(100 * (stats.get("bw") or 0), 2),
        "pct_new_water_flood_only": round(100 * (stats.get("nw") or 0), 2),
    }


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    print("Earth Engine (no download) vs local calibrated pipeline — Jang valley\n")

    local = {r["flood_date"]: r for r in json.loads(LOCAL_REPORT.read_text())["results"]}

    rows = []
    for date in FLOOD_DATES:
        try:
            r = check_one(date)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {date}: {type(exc).__name__}: {str(exc)[:150]}")
            continue
        if r is None:
            print(f"  [skip] {date}: no EE image found for this date/orbit")
            continue
        loc = local.get(date, {})
        r["local_pct_new_water"] = loc.get("pct_new_water_flood_only")
        r["diff"] = (None if r["local_pct_new_water"] is None else
                     round(r["pct_new_water_flood_only"] - r["local_pct_new_water"], 2))
        rows.append(r)
        print(f"  {date} (orbit {r['orbit']}): EE new-water {r['pct_new_water_flood_only']}%  "
              f"vs local {r['local_pct_new_water']}%  (diff {r['diff']})")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "aoi": "Jang valley, Tawang", "water_threshold_db": WATER_DB_THRESHOLD,
        "buffer_deg": BUF_DEG, "n_dates_checked": len(rows), "results": rows,
    }, indent=2))
    print(f"\nwrote {OUT}")
    if rows:
        diffs = [abs(r["diff"]) for r in rows if r["diff"] is not None]
        print(f"\n|EE - local| new-water%%: mean {sum(diffs)/len(diffs):.2f}  "
              f"median {sorted(diffs)[len(diffs)//2]:.2f}  max {max(diffs):.2f}")


if __name__ == "__main__":
    main()
