"""Real CWC gauge flood-threshold-crossing events (2019+) from the other
Indian Himalayan states — Himachal Pradesh, Uttarakhand, Jammu & Kashmir,
Sub-Himalayan West Bengal — checked via Sentinel-1, the same way the
Arunachal statewide expansion (fetch_25) and Himalaya-arc rollout
(fetch_27) already were.

These are the 2019+ half of the 511 candidates found in chat 2026-09-04
(the CWC FFS is a national system, not Arunachal-only — see
docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §5e). The 2000-2018 half (338
candidates) was already cross-checked for free via Google's Global Flood
Database (fetch_28) — 55 real hits. Google's data stops at 2018, so this
2019+ half needs the Sentinel-1 route instead, same as fetch_27.

Candidates come from scratch_gauge_candidates_2019plus.json (built in
chat from the live CWC FFS API).

    python scripts/fetch/fetch_29_cwc_gauge_himalaya_states.py

Output:
    reports/flood_where_cwc_gauge_himalaya_states.json   -- written
                                                             incrementally
    data/interim/flood_when/s1_cwcstate_<code>_<date>_water_check.png
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
from sentinel1_flood_evidence import WATER_DB_THRESHOLD, read_calibrated_window, scene_meta
import fetch_25_sentinel1_statewide_expand as expand

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
REPORT_OUT = REPORTS / "flood_where_cwc_gauge_himalaya_states.json"
CANDIDATES_IN = ROOT / "scratch_gauge_candidates_2019plus.json"
BUF_DEG = 0.15
GRD_FILTER = "contains(Name,'IW_GRDH')"


def cand_id(c: dict) -> str:
    return f"{c['station_code']}_{c['begin_date']}"


def find_scene_in_window(lat: float, lon: float, begin: str, end: str) -> tuple[dict, str] | None:
    """Search the gauge's own reported crossing window (padded a little),
    same approach as fetch_27 — these weren't hand-verified in advance."""
    expand.f14.AOI_WKT = expand.wkt_for(lat, lon)
    d0 = dt.date.fromisoformat(begin) - dt.timedelta(days=1)
    d1 = dt.date.fromisoformat(end) + dt.timedelta(days=3)
    prods = f14.search("SENTINEL-1", d0, d1, GRD_FILTER, limit=50)
    if not prods:
        return None
    target = dt.date.fromisoformat(end)

    def dist(p):
        pd_ = dt.date.fromisoformat(p["ContentDate"]["Start"][:10])
        return abs((pd_ - target).days)

    prods.sort(key=dist)
    best = prods[0]
    cog_same_day = [p for p in prods if p["ContentDate"]["Start"][:10] == best["ContentDate"]["Start"][:10]
                    and p["Name"].endswith("_COG.SAFE")]
    chosen = cog_same_day[0] if cog_same_day else best
    return chosen, chosen["ContentDate"]["Start"][:10]


def process_one(cand: dict) -> tuple[dict | None, bool]:
    """Returns (result, permanent_no_coverage) — same distinction as
    fetch_27: only a genuine "no scene exists at all" is permanent, every
    other failure stays retryable across reruns."""
    lat, lon = cand["lat"], cand["lon"]
    found = find_scene_in_window(lat, lon, cand["begin_date"], cand["end_date"])
    if found is None:
        print(f"  [no-coverage] {cand['station_code']}: no Sentinel-1 pass in "
              f"window {cand['begin_date']}..{cand['end_date']}")
        return None, True
    prod, date = found

    tok = f14.token()
    dest = f14.download_one(prod, tok)
    if dest is None:
        print(f"  [FAIL] {cand['station_code']} {date}: download failed (transient, will retry)")
        return None, False
    stem = dest.name.removesuffix(".zip")
    orbit = int(f14.attr(prod, "relativeOrbitNumber"))

    base_db = expand.ensure_baseline(orbit, lat, lon, f14.token())
    if base_db is None:
        print(f"  [skip] {cand['station_code']} {date}: no baseline for orbit {orbit} (will retry)")
        return None, False

    flood_meta = scene_meta(stem)
    flood_db = read_calibrated_window(flood_meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    if flood_db.shape != base_db.shape:
        print(f"  [skip] {cand['station_code']} {date}: shape mismatch (will retry)")
        return None, False

    valid = (flood_db > -59.0) & (base_db > -59.0)
    flood_water = (flood_db < WATER_DB_THRESHOLD) & valid
    base_water = (base_db < WATER_DB_THRESHOLD) & valid
    new_water = flood_water & ~base_water

    result = {
        "station_code": cand["station_code"], "lat": lat, "lon": lon,
        "gauge_window": f"{cand['begin_date']}/{cand['end_date']}",
        "scene_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {cand['station_code']} ({date}, orbit {orbit}): "
          f"new-water {result['pct_new_water_flood_only']}%  "
          f"(flood {result['pct_water_flood_day']}% / baseline {result['pct_water_baseline_day']}%)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(base_db, cmap="gray", vmin=-25, vmax=0)
        axes[0].set_title(f"{cand['station_code']} baseline (orbit {orbit})")
        axes[1].imshow(flood_db, cmap="gray", vmin=-25, vmax=0)
        axes[1].set_title(f"flood day {date}")
        axes[2].imshow(new_water, cmap="Blues")
        axes[2].set_title("new water (flood-only)")
        for a in axes:
            a.axis("off")
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / f"s1_cwcstate_{cand['station_code']}_{date}_water_check.png",
                    dpi=100, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass

    return result, False


def main() -> None:
    candidates = json.loads(CANDIDATES_IN.read_text())
    print(f"CWC gauge (other Himalayan states, 2019+) — {len(candidates)} candidates "
          f"via Sentinel-1 (Google's data can't reach these years)\n")

    results, no_coverage = [], []
    if REPORT_OUT.exists():
        prior = json.loads(REPORT_OUT.read_text())
        results = prior.get("results", [])
        no_coverage = prior.get("no_coverage", [])
        done = {f"{r['station_code']}_{r['gauge_window'].split('/')[0]}" for r in results} | set(no_coverage)
        todo = [c for c in candidates if cand_id(c) not in done]
        print(f"resuming: {len(results)} done, {len(no_coverage)} confirmed no-coverage, {len(todo)} left\n")
    else:
        todo = candidates

    for i, cand in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {cand['station_code']} {cand['begin_date']}..{cand['end_date']}")
        try:
            r, permanent = process_one(cand)
            if r:
                results.append(r)
            elif permanent:
                no_coverage.append(cand_id(cand))
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {cand['station_code']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")

        REPORTS.mkdir(parents=True, exist_ok=True)
        REPORT_OUT.write_text(json.dumps({
            "note": "Real CWC gauge flood-threshold-crossing events (2019+) "
                    "from Himachal/Uttarakhand/J&K/Sub-Himalayan West Bengal, "
                    "checked against real Sentinel-1 imagery. Each candidate's "
                    "check point is the gauge's own real coordinates.",
            "n_candidates": len(candidates), "n_checked": len(results),
            "n_no_coverage": len(no_coverage), "results": results,
            "no_coverage": no_coverage,
        }, indent=2))

    print(f"\nwrote {REPORT_OUT}  ({len(results)}/{len(candidates)} real events, "
          f"{len(no_coverage)} no coverage)")
    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"new-water %: min {min(vals):.2f} median {sorted(vals)[len(vals)//2]:.2f} "
              f"max {max(vals):.2f} mean {sum(vals)/len(vals):.2f}")
        print(f"positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
