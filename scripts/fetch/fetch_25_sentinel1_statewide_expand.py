"""WHERE rollout, step 3 — process the REST of the already-identified
exact-match satellite dates at the 9 statewide CWC stations, instead of
stopping at one date per station (sentinel1_flood_evidence_statewide.py).

reports/flood_where_s1_feasibility_statewide.json already lists every exact
same-day match between a real flood day and a real Sentinel-1 pass, per
station — only one per station was ever downloaded+processed. This script
fetches and checks every remaining one: 37 more real events, no new data
source, same debugged calibration/warp pipeline throughout.

    python scripts/fetch/fetch_25_sentinel1_statewide_expand.py

Output:
    reports/flood_where_s1_statewide_expanded.json   -- every result, written
                                                         incrementally so a
                                                         partial run is not lost
    data/interim/flood_when/s1_<code>_<date>_water_check.png
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np

import fetch_14_sentinel as f14
from common import INTERIM, ROOT
from flood_stations import STATIONS
from sentinel1_flood_evidence import WATER_DB_THRESHOLD, read_calibrated_window, scene_meta
from sentinel1_flood_evidence_statewide import BASELINE_BY_ORBIT as KNOWN_BASELINES

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
FEASIBILITY = REPORTS / "flood_where_s1_feasibility_statewide.json"
REPORT_OUT = REPORTS / "flood_where_s1_statewide_expanded.json"
BUF_DEG = 0.15
GRD_FILTER = "contains(Name,'IW_GRDH')"

# dates already fetched+checked by sentinel1_flood_evidence_statewide.py and
# sentinel1_flood_evidence_loose_ends.py — skip these, everything else in
# each station's exact_match_dates list is new.
ALREADY_DONE = {
    "001-UBDDIB": {"2016-07-26"},
    "003-UBDDIB": {"2023-08-29", "2020-06-28"},
    "005-UBDDIB": {"2021-08-29"},
    "007NEID3": {"2022-09-05"},
    "008-ubddib": {"2026-04-22"},
    "020-UBDDIB": {"2019-07-22"},
    "027-UBDDIB": set(),
    "058-UBDDIB": {"2024-11-17"},
    "059-UBDDIB": {"2024-07-01"},
    "070-UBDDIB": set(),
    "078-UBDDIB": {"2026-07-29"},
}

_baseline_cache: dict[tuple, np.ndarray] = {}
_baseline_scene_by_orbit: dict[int, str] = dict(KNOWN_BASELINES)


def wkt_for(lat: float, lon: float) -> str:
    w, s, e, n = lon - BUF_DEG, lat - BUF_DEG, lon + BUF_DEG, lat + BUF_DEG
    return f"POLYGON(({w} {s},{e} {s},{e} {n},{w} {n},{w} {s}))"


def find_scene_for_date(lat: float, lon: float, date: str) -> dict | None:
    """Every scene exists in both a plain and a '_COG' (cloud-optimized,
    smaller) variant in the catalogue — every scene downloaded so far this
    session is the COG one, so prefer it here too for consistency and to
    save bandwidth (COG is ~25% smaller)."""
    f14.AOI_WKT = wkt_for(lat, lon)
    d0 = dt.date.fromisoformat(date)
    prods = f14.search("SENTINEL-1", d0, d0 + dt.timedelta(days=1), GRD_FILTER, limit=10)
    prods = [p for p in prods if p["ContentDate"]["Start"][:10] == date]
    if not prods:
        return None
    cog = [p for p in prods if p["Name"].endswith("_COG.SAFE")]
    return cog[0] if cog else prods[0]


def ensure_baseline(orbit: int, lat: float, lon: float, tok: str) -> np.ndarray | None:
    key = (orbit, round(lat, 3), round(lon, 3))
    if key in _baseline_cache:
        return _baseline_cache[key]
    if orbit not in _baseline_scene_by_orbit:
        # no known dry-season baseline for this orbit yet — find one: a
        # March 2025 (dry season) scene on the same relative orbit.
        f14.AOI_WKT = wkt_for(lat, lon)
        prods = f14.search("SENTINEL-1", dt.date(2025, 3, 1), dt.date(2025, 4, 1),
                            GRD_FILTER, limit=20)
        match = next((p for p in prods if str(f14.attr(p, "relativeOrbitNumber")) == str(orbit)), None)
        if match is None:
            print(f"    [no baseline] no dry-season scene found for orbit {orbit}")
            return None
        dest = f14.download_one(match, f14.token())
        if dest is None:
            return None
        _baseline_scene_by_orbit[orbit] = dest.name.removesuffix(".zip")
        print(f"    new baseline for orbit {orbit}: {_baseline_scene_by_orbit[orbit]}")
    meta = scene_meta(_baseline_scene_by_orbit[orbit])
    arr = read_calibrated_window(meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    _baseline_cache[key] = arr
    return arr


def process_one(code: str, date: str, tok: str) -> dict | None:
    meta = STATIONS[code]
    lat, lon = meta["lat"], meta["lon"]

    prod = find_scene_for_date(lat, lon, date)
    if prod is None:
        print(f"  [skip] {meta['name']} {date}: no scene found on re-search (unexpected)")
        return None
    # CDSE access tokens live ~10 minutes — a single token handed to a
    # multi-hour batch went stale partway through the first real run here
    # (every download after the first ~8 minutes failed with HTTP 401).
    # Re-authenticate before every download instead of reusing one token.
    tok = f14.token()
    dest = f14.download_one(prod, tok)
    if dest is None:
        print(f"  [FAIL] {meta['name']} {date}: download failed")
        return None
    stem = dest.name.removesuffix(".zip")
    orbit = int(f14.attr(prod, "relativeOrbitNumber"))

    base_db = ensure_baseline(orbit, lat, lon, tok)
    if base_db is None:
        print(f"  [skip] {meta['name']} {date}: no baseline available for orbit {orbit}")
        return None

    flood_meta = scene_meta(stem)
    flood_db = read_calibrated_window(flood_meta, lat=lat, lon=lon, buf_deg=BUF_DEG)

    if flood_db.shape != base_db.shape:
        print(f"  [skip] {meta['name']} {date}: shape mismatch {flood_db.shape} vs {base_db.shape}")
        return None

    valid = (flood_db > -59.0) & (base_db > -59.0)
    flood_water = (flood_db < WATER_DB_THRESHOLD) & valid
    base_water = (base_db < WATER_DB_THRESHOLD) & valid
    new_water = flood_water & ~base_water

    result = {
        "station_code": code, "station_name": meta["name"],
        "flood_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {meta['name']} ({date}, orbit {orbit}): new-water "
          f"{result['pct_new_water_flood_only']}%  (flood {result['pct_water_flood_day']}% "
          f"/ baseline {result['pct_water_baseline_day']}%)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(base_db, cmap="gray", vmin=-25, vmax=0)
        axes[0].set_title(f"{meta['name']} baseline (orbit {orbit})")
        axes[1].imshow(flood_db, cmap="gray", vmin=-25, vmax=0)
        axes[1].set_title(f"flood day {date}")
        axes[2].imshow(new_water, cmap="Blues")
        axes[2].set_title("new water (flood-only)")
        for a in axes:
            a.axis("off")
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / f"s1_{code}_{date}_water_check.png", dpi=100, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass

    return result


def main() -> None:
    print("WHERE rollout, step 3 — processing the remaining exact-match dates\n")
    feas = json.loads(FEASIBILITY.read_text())

    todo: list[tuple[str, str]] = []
    for code, v in feas.items():
        remaining = sorted(set(v["exact_match_dates"]) - ALREADY_DONE.get(code, set()))
        for d in remaining:
            todo.append((code, d))
    print(f"{len(todo)} (station, date) pairs already identified as real exact matches, "
          f"not yet fetched+checked\n")

    results = []
    if REPORT_OUT.exists():
        prior = json.loads(REPORT_OUT.read_text())
        results = prior.get("results", [])
        done_pairs = {(r["station_code"], r["flood_date"]) for r in results}
        todo = [t for t in todo if t not in done_pairs]
        print(f"resuming: {len(results)} already done in a prior run, {len(todo)} left\n")

    tok = f14.token()
    for i, (code, date) in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {STATIONS[code]['name']} ({code}) {date}")
        try:
            r = process_one(code, date, tok)
            if r:
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {STATIONS[code]['name']} {date}: {type(exc).__name__}: {str(exc)[:150]}")
        # write incrementally — a long download batch should not lose progress
        REPORTS.mkdir(parents=True, exist_ok=True)
        REPORT_OUT.write_text(json.dumps({
            "note": "Every remaining exact-match satellite date at the 9 statewide "
                    "CWC stations that already had one date checked — grows the "
                    "WHERE evidence base without any new data source.",
            "n_targeted_total": len(results) + len(todo) - i,
            "results": results,
        }, indent=2))

    print(f"\ndone: {len(results)} events processed, wrote {REPORT_OUT}")
    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"new-water %: min {min(vals):.1f} median {sorted(vals)[len(vals)//2]:.1f} "
              f"max {max(vals):.1f} mean {sum(vals)/len(vals):.1f}")
        print(f"positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
