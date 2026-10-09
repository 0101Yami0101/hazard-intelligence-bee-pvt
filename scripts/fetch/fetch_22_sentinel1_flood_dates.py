"""Phase 3 of the flood-WHEN pilot — does Sentinel-1 actually cover our real
flood dates near Jang valley? The feasibility check behind the WHERE handoff.

    python scripts/fetch/fetch_22_sentinel1_flood_dates.py

Reads the flood-day list Phases 1-2 produced
(data/interim/flood_when/tawang_flood_days.csv) and checks, for each date,
how close the nearest real Sentinel-1 acquisition over Jang valley actually
is — rather than assuming daily coverage, which Sentinel-1 (a ~12-day single-
satellite repeat cycle, several relative orbits) does not give.

Outputs:
    data/interim/flood_when/s1_jang_acquisition_days.json   -- every S1 pass date over Jang
    reports/flood_where_s1_feasibility.json                 -- match summary + candidate scenes

Queried year-by-year rather than one 7-year span in a single request — a
single wide query against this AOI hung for minutes with no error and no
partial output; the OData catalogue's own comments already warn it is
"flaky on wide queries." Chunking by year keeps each request small and fast
(~15-45s/year) and makes a stall or failure isolable to one year instead of
losing the whole run.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))

import pandas as pd

import fetch_14_sentinel as f14
from common import INTERIM, ROOT

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
FLOOD_DAYS = OUT / "tawang_flood_days.csv"

JANG_LAT, JANG_LON = 27.5834, 91.9802   # same proxy location as the WHEN pilot
BUF_DEG = 0.2                            # ~20 km box around Jang valley
YEARS = range(2019, 2027)
GRD_FILTER = "contains(Name,'IW_GRDH')"


def jang_wkt() -> str:
    w, s = JANG_LON - BUF_DEG, JANG_LAT - BUF_DEG
    e, n = JANG_LON + BUF_DEG, JANG_LAT + BUF_DEG
    return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


def acquisition_days(cache: Path) -> list[dt.date]:
    if cache.exists():
        return [dt.date.fromisoformat(d) for d in json.loads(cache.read_text())]

    f14.AOI_WKT = jang_wkt()
    all_dates: set[str] = set()
    for year in YEARS:
        y0 = dt.date(year, 1, 1)
        y1 = dt.date(year, 12, 31) if year < 2026 else dt.date.today()
        scenes = f14.search("SENTINEL-1", y0, y1, GRD_FILTER, limit=400)
        ds = {s["ContentDate"]["Start"][:10] for s in scenes}
        all_dates |= ds
        print(f"  {year}: {len(scenes)} scenes, {len(ds)} distinct days")

    dates = sorted(all_dates)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(dates, indent=2))
    return [dt.date.fromisoformat(d) for d in dates]


def main() -> None:
    print("Phase 3 — Sentinel-1 feasibility over Jang valley, flood dates from Phase 1-2\n")
    flood = pd.read_csv(FLOOD_DAYS)
    fdates = sorted(set(pd.to_datetime(flood["date"]).dt.date))
    print(f"{len(fdates)} unique flood dates to check\n")

    print("Querying Sentinel-1 GRD acquisitions over Jang, 2019-2026 (year by year)...")
    scene_days = acquisition_days(OUT / "s1_jang_acquisition_days.json")
    print(f"  {len(scene_days)} distinct acquisition days total\n")

    def nearest_gap(fd: dt.date) -> int:
        return min(abs((fd - sd).days) for sd in scene_days)

    gaps = [(str(fd), nearest_gap(fd)) for fd in fdates]
    coverage = {k: sum(1 for _, g in gaps if g <= k) for k in (0, 1, 2, 3, 6)}

    print("Flood dates with a Sentinel-1 pass within N days:")
    for k, n in coverage.items():
        print(f"  within {k:>2} day(s): {n}/{len(fdates)} ({100*n/len(fdates):.0f}%)")

    exact = [d for d, g in gaps if g == 0]
    print(f"\n{len(exact)} exact same-day matches — real, usable WHERE-evidence candidates:")
    for d in exact:
        print(f"  {d}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    report = REPORTS / "flood_where_s1_feasibility.json"
    report.write_text(json.dumps({
        "aoi": "Jang valley, Tawang — 0.2 deg buffer around 27.5834N 91.9802E",
        "n_flood_dates": len(fdates),
        "n_s1_acquisition_days": len(scene_days),
        "coverage_within_n_days": coverage,
        "exact_match_dates": exact,
        "gaps": dict(gaps),
    }, indent=2))
    print(f"\nwrote {report}")


if __name__ == "__main__":
    main()
