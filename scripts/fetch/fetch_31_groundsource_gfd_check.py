"""Groundsource candidates (Arunachal, 2000-2018) cross-checked against
Google's Global Flood Database — same proven method as
fetch_28_gfd_gauge_crosscheck.py, just a different candidate source.

No downloads at all — every check is a server-side Earth Engine query.
Uses the same fixed interval-overlap date filter (a plain .filterDate()
only checks an image's own start date, not real overlap — see §5f/§5e in
docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md) and the same 2km buffer
check (a single point often sits on already-"permanent" water, see the
same doc section) that fetch_28 already validated.

Candidates: data/interim/flood_when/groundsource_aru_pre2019.json (built
in chat from data/raw/16_groundsource/groundsource_2026.parquet).

    python scripts/fetch/fetch_31_groundsource_gfd_check.py

Output:
    reports/flood_where_groundsource_gfd_check.json
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "data" / "interim" / "flood_when" / "groundsource_aru_pre2019.json"
REPORT_OUT = ROOT / "reports" / "flood_where_groundsource_gfd_check.json"
DATE_PAD_DAYS = 4
CHECK_BUFFER_M = 2000


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")

    candidates = json.loads(CANDIDATES_IN.read_text())
    print(f"Groundsource pre-2019 Arunachal candidates — {len(candidates)} to check "
          f"against Google's Global Flood Database, no downloads\n")

    results = []
    for i, c in enumerate(candidates, 1):
        pt = ee.Geometry.Point([c["lon"], c["lat"]])
        peak = dt.date.fromisoformat(c["date_str"])
        d0 = ee.Date((peak - dt.timedelta(days=DATE_PAD_DAYS)).isoformat())
        d1 = ee.Date((peak + dt.timedelta(days=DATE_PAD_DAYS + 1)).isoformat())

        matches = (gfd.filterBounds(pt)
                      .filter(ee.Filter.lte("system:time_start", d1.millis()))
                      .filter(ee.Filter.gte("system:time_end", d0.millis())))
        n = matches.size().getInfo()
        if n == 0:
            results.append({**c, "gfd_match": False})
        else:
            img = matches.mosaic()
            region = pt.buffer(CHECK_BUFFER_M)
            fl = img.select("flooded")
            perm = img.select("jrc_perm_water")
            new_water = fl.And(perm.Not())
            val = ee.Image.cat([fl.rename("f"), perm.rename("p"), new_water.rename("nw")]).reduceRegion(
                reducer=ee.Reducer.mean(), geometry=region, scale=250, maxPixels=1e8,
            ).getInfo()
            pct_new = round(100 * (val.get("nw") or 0), 2)
            results.append({**c, "gfd_match": True, "n_gfd_events_in_window": n,
                             "pct_new_flood_in_buffer": pct_new,
                             "real_new_flood": pct_new > 0})
        if i % 50 == 0 or i == len(candidates):
            print(f"  ...{i}/{len(candidates)}")
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            n_match = sum(1 for r in results if r.get("gfd_match"))
            n_real = sum(1 for r in results if r.get("real_new_flood"))
            REPORT_OUT.write_text(json.dumps({
                "note": "Groundsource pre-2019 Arunachal candidates cross-checked "
                        "against Google's Global Flood Database. gfd_match=True "
                        "means a GFD image exists near that date/place at all; "
                        "real_new_flood=True means it shows a real new (non-"
                        "permanent) flooded pixel in a 2km buffer around the "
                        "candidate's representative_point().",
                "n_candidates": len(candidates), "n_checked_so_far": i,
                "n_gfd_match": n_match, "n_real_new_flood": n_real,
                "results": results,
            }, indent=2))

    print(f"\nwrote {REPORT_OUT}")
    n_match = sum(1 for r in results if r.get("gfd_match"))
    n_real = sum(1 for r in results if r.get("real_new_flood"))
    print(f"{n_match}/{len(candidates)} had a GFD image nearby at all")
    print(f"{n_real}/{len(candidates)} show a real, independently-confirmed new flood pixel")


if __name__ == "__main__":
    main()
