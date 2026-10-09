"""FREE, no-login coverage check against ESA's Envisat ASAR + ERS SAR
archives, for the 682 pre-Oct-2014 Groundsource Arunachal candidates that
have zero other free method available (GFD/gauge already tried and
exhausted — see docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §0c/§0b).

This is a PRECHECK — it only confirms whether a real scene exists near
each candidate's date/location (via ESA's public "SOCat" search
endpoint, reverse-engineered from the search page's own JS this session
— no ESA account needed to search, only to later download). It does NOT
download or compute a flood percentage. That's the deliberate next step
once we know how many candidates are actually worth pursuing.

Collections checked (both are the GLOBAL archives, not the small
regional "thematic" ones like Alps/Iceland/Svalbard):
  - ASA_WSM_1P  — Envisat ASAR Wide Swath, ~150m res, operated to
    2012-04-08 (Envisat lost contact)
  - SAR_IMP_1P  — ERS-1/2 SAR Precision Image, ~30m res, ERS-1 1991-2000,
    ERS-2 1995-2011 (but with a long gyroscope-failure gap post-2001)

Known real gap this can NEVER close, worth remembering: Envisat died
April 2012, Sentinel-1 did not start until Oct 2014 — a ~2.5-year dead
zone with no free full-swath SAR archive at all. That's where ISRO's
RISAT-1 (2012-2017, see fetch_35) is the only free lead.

    python scripts/fetch/fetch_34_esa_asar_ers_precheck.py

Output:
    reports/flood_where_esa_asar_ers_precheck.json
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CANDIDATES_IN = ROOT / "data" / "interim" / "flood_when" / "groundsource_aru_pre2014_unresolved.json"
REPORT_OUT = ROOT / "reports" / "flood_where_esa_asar_ers_precheck.json"

SEARCH_URL = "https://esar-ds.eo.esa.int/socat/{collection}/search"
DATE_PAD_DAYS = 3
BBOX_PAD_DEG = 0.15  # same window size used throughout this project's Sentinel-1 work

# (collection, real operating window) — both GLOBAL archives, confirmed by
# browsing https://esar-ds.eo.esa.int/oads/access/collection this session
# (the place-suffixed ones like ASA_WSM_1P_Alps are separate small regional
# subsets and NOT used here).
COLLECTIONS = [
    ("ASA_WSM_1P", dt.date(2002, 5, 1), dt.date(2012, 4, 8)),
    ("SAR_IMP_1P", dt.date(1991, 7, 1), dt.date(2011, 7, 1)),
]


def search_count(collection: str, d0: dt.date, d1: dt.date, lat: float, lon: float,
                  tries: int = 3) -> int | None:
    """Real match count from ESA's public SOCat search, or None if the
    request itself failed after retries (NOT the same as a confirmed
    zero — same discipline as fetch_14's search(), see its docstring)."""
    data = {
        "service": "SimpleOnlineCatalogue", "version": "1.2", "request": "search",
        "format": "text/html", "pageCount": "1",
        "query.beginAcquisition.start": d0.isoformat(),
        "query.beginAcquisition.stop": d1.isoformat(),
        "query.footprint.minlat": f"{lat - BBOX_PAD_DEG:.4f}",
        "query.footprint.maxlat": f"{lat + BBOX_PAD_DEG:.4f}",
        "query.footprint.minlon": f"{lon - BBOX_PAD_DEG:.4f}",
        "query.footprint.maxlon": f"{lon + BBOX_PAD_DEG:.4f}",
    }
    url = SEARCH_URL.format(collection=collection)
    for attempt in range(tries):
        try:
            r = requests.post(url, data=data, timeout=30)
            r.raise_for_status()
            text = r.text
            # "(N of more than M records found" / "(N records found" — parse the
            # human sentence rather than assuming a stable API field, since this
            # is an HTML-search response, not a documented JSON API.
            import re
            m = re.search(r"\(\s*(\d+)\s+of\s+(?:more than\s+)?(\d+)?\s*records? found", text)
            if m:
                return int(m.group(2) or m.group(1))
            m0 = re.search(r"\(\s*(\d+)\s+records? found", text)
            if m0:
                return int(m0.group(1))
            # confirmed exact phrasing via direct test, 2026-09-07: "No record found."
            if "no record found" in text.lower():
                return 0
            return None  # unrecognized response shape — treat as unknown, not zero
        except Exception:  # noqa: BLE001
            if attempt == tries - 1:
                return None
            time.sleep(2 * (attempt + 1))
    return None


def main() -> None:
    candidates = json.loads(CANDIDATES_IN.read_text(encoding="utf-8"))
    print(f"ESA Envisat ASAR + ERS SAR precheck — {len(candidates)} pre-Oct-2014 "
          f"candidates with zero other free method (see script docstring)\n")

    results = []
    if REPORT_OUT.exists():
        try:
            prior = json.loads(REPORT_OUT.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            prior = json.loads(REPORT_OUT.read_text(encoding="cp1252"))
        results = prior.get("results", [])
        done = {r["uuid"] for r in results}
        candidates = [c for c in candidates if c["uuid"] not in done]
        print(f"resuming: {len(results)} already done, {len(candidates)} left\n")

    for i, c in enumerate(candidates, 1):
        d = dt.date.fromisoformat(c["date_str"])
        d0, d1 = d - dt.timedelta(days=DATE_PAD_DAYS), d + dt.timedelta(days=DATE_PAD_DAYS)
        row = {**c}
        any_found = False
        for collection, op_start, op_end in COLLECTIONS:
            if d1 < op_start or d0 > op_end:
                row[f"{collection}_in_operating_window"] = False
                continue
            row[f"{collection}_in_operating_window"] = True
            n = search_count(collection, d0, d1, c["lat"], c["lon"])
            row[f"{collection}_n_scenes"] = n
            if n:
                any_found = True
            time.sleep(0.3)  # be polite to a free public service
        row["any_scene_found"] = any_found
        results.append(row)
        if i % 25 == 0 or i == len(candidates):
            print(f"  ...{len(results)}/{len(results) + len(candidates) - i}")
            REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
            REPORT_OUT.write_text(encoding="utf-8", data=json.dumps({
                "note": "PRECHECK ONLY — confirms a real scene exists near the "
                        "date/location via ESA's public search (no download, no "
                        "flood computation yet). See script docstring.",
                "n_candidates": len(results), "results": results,
            }, indent=2, ensure_ascii=False))

    n_found = sum(1 for r in results if r.get("any_scene_found"))
    n_in_window = sum(1 for r in results if any(
        r.get(f"{c}_in_operating_window") for c, _, _ in COLLECTIONS))
    print(f"\nwrote {REPORT_OUT}")
    print(f"{n_in_window}/{len(results)} fall inside either archive's real operating window")
    print(f"{n_found}/{len(results)} have a real scene found nearby — worth a real download")


if __name__ == "__main__":
    main()
