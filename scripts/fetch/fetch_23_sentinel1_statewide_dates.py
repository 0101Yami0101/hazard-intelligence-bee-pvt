"""WHERE rollout, step 1 — Sentinel-1 feasibility at the other 16 CWC
stations, generalizing fetch_22_sentinel1_flood_dates.py (Jang-only) across
every station in flood_stations.py using the real flood-day list Phase 1
already produced (data/interim/flood_when/arunachal_flood_days.csv).

    python scripts/fetch/fetch_23_sentinel1_statewide_dates.py

Skips stations with no confirmed flood day at all (Tuting, Pangin, Lemeking,
Namsai — Phase 1 found zero, see FLOOD_WHEN_PILOT_PLAN.md §8, not
investigated further yet) and Bhalukpong, whose only real flood days
(1987-2014) predate Sentinel-1's operational archive — there is nothing to
search for. Murga Bridge / Rho Basti are already done (Jang valley pilot,
fetch_22).

Output:
    data/interim/flood_when/s1_<code>_acquisition_days.json  -- per station, cached
    reports/flood_where_s1_feasibility_statewide.json         -- one match table
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import pandas as pd

import fetch_14_sentinel as f14
from common import INTERIM, ROOT
from flood_stations import STATIONS

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
FLOOD_DAYS = OUT / "arunachal_flood_days.csv"

BUF_DEG = 0.15
GRD_FILTER = "contains(Name,'IW_GRDH')"
ALREADY_DONE = {"002Neid3", "001NEID3"}   # Jang pilot, fetch_22
NO_RECENT_FLOOD_DAYS = {"029-UBDDIB"}     # Bhalukpong: only pre-2015 events


def wkt_for(lat: float, lon: float) -> str:
    w, s, e, n = lon - BUF_DEG, lat - BUF_DEG, lon + BUF_DEG, lat + BUF_DEG
    return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


def acquisition_days(code: str, lat: float, lon: float) -> list[dt.date]:
    cache = OUT / f"s1_{code}_acquisition_days.json"
    if cache.exists():
        return [dt.date.fromisoformat(d) for d in json.loads(cache.read_text())]

    f14.AOI_WKT = wkt_for(lat, lon)
    all_dates: set[str] = set()
    for year in range(2015, 2027):
        y0 = dt.date(year, 1, 1)
        y1 = dt.date(year, 12, 31) if year < 2026 else dt.date.today()
        scenes = f14.search("SENTINEL-1", y0, y1, GRD_FILTER, limit=400)
        ds = {s["ContentDate"]["Start"][:10] for s in scenes}
        all_dates |= ds

    dates = sorted(all_dates)
    cache.write_text(json.dumps(dates, indent=2))
    return [dt.date.fromisoformat(d) for d in dates]


def main() -> None:
    print("WHERE rollout — Sentinel-1 feasibility, all remaining stations\n")
    flood = pd.read_csv(FLOOD_DAYS, parse_dates=["date"])

    targets = {c: m for c, m in STATIONS.items()
               if c not in ALREADY_DONE and c not in NO_RECENT_FLOOD_DAYS}

    report: dict[str, dict] = {}
    for code, meta in targets.items():
        fdates = sorted(set(flood.loc[flood["station_code"] == code, "date"].dt.date))
        if not fdates:
            print(f"  [skip] {meta['name']} ({code}): no confirmed flood day in Phase 1")
            continue

        print(f"  {meta['name']} ({code}): {len(fdates)} flood dates, "
              f"{fdates[0]}..{fdates[-1]}")
        scene_days = acquisition_days(code, meta["lat"], meta["lon"])

        def nearest_gap(fd):
            return min(abs((fd - sd).days) for sd in scene_days) if scene_days else None

        gaps = [(str(fd), nearest_gap(fd)) for fd in fdates]
        exact = [d for d, g in gaps if g == 0]
        within2 = [d for d, g in gaps if g is not None and g <= 2]
        print(f"    {len(scene_days)} S1 passes since 2015; "
              f"{len(exact)} exact match(es), {len(within2)} within 2 days")

        report[code] = {
            "name": meta["name"], "n_flood_dates": len(fdates),
            "n_s1_acquisition_days": len(scene_days),
            "exact_match_dates": exact, "within_2_days": within2,
        }

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_where_s1_feasibility_statewide.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out}")

    print("\nStations with at least one exact match, ready for Phase-3b-style processing:")
    for code, r in report.items():
        if r["exact_match_dates"]:
            print(f"  {r['name']}: {r['exact_match_dates']}")


if __name__ == "__main__":
    main()
