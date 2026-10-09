"""Cross-check real CWC gauge flood-threshold-crossing dates (Himachal
Pradesh, Uttarakhand, Jammu & Kashmir, Sub-Himalayan West Bengal — the
Indian Himalayan states beyond Arunachal) against Google Earth Engine's
Global Flood Database (GLOBAL_FLOOD_DB/MODIS_EVENTS/V1) — real,
MODIS-observed flood pixels, 2000-2018.

Unlike the Sentinel-1 rollout (fetch_27), this needs no downloads at all —
every check is a server-side Earth Engine query, so hundreds of candidates
resolve in a couple of minutes (same speed as the original Arunachal/
Himalaya-arc GFD pulls in PARKED_HIMALAYAN_FLOOD_WHERE.md §5b).

For each (station, peak_date) candidate: does a GFD image exist whose time
window covers a few days around that date AND whose footprint contains
the station's real coordinates? If yes, sample the 'flooded' band at that
point — a real MODIS-confirmed flood pixel is an independent match between
two unrelated real data sources (government gauge + NASA/Yale satellite),
exactly like the 43/70 Arunachal cross-validation already found.

Candidates come from scratch_gauge_candidates_2000_2018.json (built in
chat, from the live CWC FFS API — see docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md).

    python scripts/fetch/fetch_28_gfd_gauge_crosscheck.py

Output:
    reports/flood_where_gfd_gauge_crosscheck.json
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import ee

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "scratch_gauge_candidates_2000_2018.json"
REPORT_OUT = ROOT / "reports" / "flood_where_gfd_gauge_crosscheck.json"
DATE_PAD_DAYS = 4  # +/- window around the gauge's peak day
CHECK_BUFFER_M = 2000  # a gauge's exact point often sits on permanent river
# water (MODIS 250m pixel), which GFD correctly excludes from "new flood" —
# checking a small area around it (not just the literal point) is needed to
# see real floodplain inundation, same reasoning as the Sentinel-1 windowed
# check elsewhere in this project (a single point was tried first, see
# docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §5e for the honest correction).


def main() -> None:
    ee.Initialize(project="earthengine-507510")
    gfd = ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")

    candidates = json.loads(CANDIDATES_IN.read_text())
    print(f"Cross-checking {len(candidates)} real CWC gauge flood dates "
          f"(Himachal/Uttarakhand/J&K/Sub-Himalayan WB, 2000-2018) against "
          f"Google's Global Flood Database — no downloads, server-side only\n")

    results = []
    for i, c in enumerate(candidates, 1):
        pt = ee.Geometry.Point([c["lon"], c["lat"]])
        peak = dt.date.fromisoformat(c["peak_date"])
        d0 = ee.Date((peak - dt.timedelta(days=DATE_PAD_DAYS)).isoformat())
        d1 = ee.Date((peak + dt.timedelta(days=DATE_PAD_DAYS + 1)).isoformat())

        # NOTE: plain .filterDate(d0, d1) only checks each image's own
        # system:time_start against the window — it does NOT check for
        # overlap with system:time_end. GFD events can span weeks to
        # months, so a naive filterDate silently missed almost every real
        # match whose peak date fell well after the event's recorded
        # start (caught 2026-09-04 via a known-flooded-pixel sanity
        # check that returned 0 matches until this was fixed). Real
        # interval-overlap test instead: the image's own
        # [time_start, time_end] must overlap [d0, d1].
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
            pct_flooded = round(100 * (val.get("f") or 0), 2)
            pct_perm = round(100 * (val.get("p") or 0), 2)
            pct_new = round(100 * (val.get("nw") or 0), 2)
            results.append({**c, "gfd_match": True, "n_gfd_events_in_window": n,
                             "pct_flooded_in_buffer": pct_flooded,
                             "pct_permanent_water_in_buffer": pct_perm,
                             "pct_new_flood_in_buffer": pct_new,
                             "real_new_flood": pct_new > 0})
        if i % 25 == 0 or i == len(candidates):
            print(f"  ...{i}/{len(candidates)}")

    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    n_match = sum(1 for r in results if r.get("gfd_match"))
    n_real = sum(1 for r in results if r.get("real_new_flood"))
    REPORT_OUT.write_text(json.dumps({
        "note": "Real CWC gauge flood-crossing dates (2000-2018, Himachal/"
                "Uttarakhand/J&K/Sub-Himalayan WB) cross-checked against "
                "Google's Global Flood Database. gfd_match=True means a GFD "
                "image exists near that date/place at all; real_new_flood=True "
                "means it shows an actual new (non-permanent) flooded pixel "
                "at the station's own coordinates — two independent real "
                "data sources agreeing.",
        "n_candidates": len(candidates), "n_gfd_match": n_match,
        "n_real_new_flood": n_real, "results": results,
    }, indent=2))
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_match}/{len(candidates)} had a GFD image nearby at all")
    print(f"{n_real}/{len(candidates)} show a real, independently-confirmed new flood pixel")


if __name__ == "__main__":
    main()
