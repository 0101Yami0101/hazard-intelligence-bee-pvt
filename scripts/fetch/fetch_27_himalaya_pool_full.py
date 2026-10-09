"""Himalaya-pooled WHERE player — full rollout, continuing past the 9-event
proof batch (fetch_26_himalaya_pool_test.py).

Scope, per docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md §0/§5b (2026-09-03
priority decision): the Google Earth Engine Global Flood Database already
covers 155 real Himalaya-arc events for 2000-2018 (see
data/interim/flood_when/gfd_himalaya_arc_results.json). Sentinel-1 didn't
exist before 2015 and GFD already covers up to 2018, so the only events
Sentinel-1 needs to fill in are the Himalaya-arc DFO events from 2019
onward. Queried directly from the DFO archive (not re-guessed):

    Himalaya arc bbox (72-97.5E, 26-36N), BeginDate >= 2019-01-01: 42 events
    of those, only 31 have their representative_point() actually inside
    the bbox (the other 11 are huge multi-country polygons — e.g. an
    Afghanistan/Pakistan or Bangladesh-delta flood that merely grazes the
    bbox edge — not a real Himalaya-terrain event, skipped rather than
    forced through as a bogus check point).

Unlike fetch_26's 9 hand-picked, pre-verified dates, these 31 were never
individually researched — each is checked by searching for any Sentinel-1
pass across its own DFO-reported flood window (BeginDate-1 .. EndDate+3),
not one fixed date. Expect a genuine fraction of these to fail (no
Sentinel-1 coverage in the window, or the window's true peak missed) —
consistent with the "roughly half-to-two-thirds convert" estimate already
written into the plan doc.

    python scripts/fetch/fetch_27_himalaya_pool_full.py

Output:
    reports/flood_where_himalaya_pool_full.json   -- written incrementally
    data/interim/flood_when/s1_himfull_<report#>_<date>_water_check.png
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

import fetch_14_sentinel as f14
from common import INTERIM, ROOT
from sentinel1_flood_evidence import WATER_DB_THRESHOLD, read_calibrated_window, scene_meta
import fetch_25_sentinel1_statewide_expand as expand

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
REPORT_OUT = REPORTS / "flood_where_himalaya_pool_full.json"
DFO_GPKG = ROOT / "data/raw/15_dfo_flood_records/Global_Flood_Records.gpkg"
BUF_DEG = 0.15
GRD_FILTER = "contains(Name,'IW_GRDH')"
HIMALAYA_BBOX = box(72, 26, 97.5, 36)


def build_candidates() -> list[dict]:
    gdf = gpd.read_file(DFO_GPKG)
    gdf["BeginDate"] = pd.to_datetime(gdf["BeginDate"], errors="coerce")
    gdf["EndDate"] = pd.to_datetime(gdf["EndDate"], errors="coerce")
    arc = gdf[gdf.geometry.intersects(HIMALAYA_BBOX)].copy()
    post2019 = arc[arc["BeginDate"] >= "2019-01-01"].copy()
    post2019["rep_point"] = post2019.geometry.apply(lambda g: g.representative_point())
    post2019["rep_in_bbox"] = post2019["rep_point"].apply(lambda p: HIMALAYA_BBOX.contains(p))
    keep = post2019[post2019["rep_in_bbox"]].copy()

    out = []
    for _, r in keep.iterrows():
        p = r["rep_point"]
        out.append({
            "report_number": int(r["ReportNumber"]),
            "country": r["Country"],
            "lat": round(p.y, 4),
            "lon": round(p.x, 4),
            "begin_date": r["BeginDate"].date().isoformat(),
            "end_date": r["EndDate"].date().isoformat(),
            "severity": str(r["Severity"]),
        })
    return out


def find_scene_in_window(lat: float, lon: float, begin: str, end: str) -> tuple[dict, str] | None:
    """Search the whole reported flood window (padded a little on both
    ends) instead of one fixed date — these candidates were never
    hand-verified in advance, unlike fetch_26's 9."""
    expand.f14.AOI_WKT = expand.wkt_for(lat, lon)
    d0 = dt.date.fromisoformat(begin) - dt.timedelta(days=1)
    d1 = dt.date.fromisoformat(end) + dt.timedelta(days=3)
    prods = f14.search("SENTINEL-1", d0, d1, GRD_FILTER, limit=50)
    if not prods:
        return None
    # prefer the scene closest to the window's end (flood extent is more
    # likely near/after the reported peak than right at the first day).
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
    """Returns (result, permanent_no_coverage). permanent_no_coverage is True
    only when no Sentinel-1 scene exists in the window at all — a genuine,
    non-retryable physical fact. Every other failure (download timeout,
    baseline miss, shape mismatch) is transient/positional and should be
    retried on the next run, not permanently skipped — the same distinction
    fetch_25 gets for free by only ever skipping successes, not failures."""
    lat, lon = cand["lat"], cand["lon"]
    found = find_scene_in_window(lat, lon, cand["begin_date"], cand["end_date"])
    if found is None:
        print(f"  [no-coverage] #{cand['report_number']} {cand['country']}: "
              f"no Sentinel-1 pass in window {cand['begin_date']}..{cand['end_date']}")
        return None, True
    prod, date = found

    tok = f14.token()
    dest = f14.download_one(prod, tok)
    if dest is None:
        print(f"  [FAIL] #{cand['report_number']} {date}: download failed (transient, will retry)")
        return None, False
    stem = dest.name.removesuffix(".zip")
    orbit = int(f14.attr(prod, "relativeOrbitNumber"))

    base_db = expand.ensure_baseline(orbit, lat, lon, f14.token())
    if base_db is None:
        print(f"  [skip] #{cand['report_number']} {date}: no baseline for orbit {orbit} (will retry)")
        return None, False

    flood_meta = scene_meta(stem)
    flood_db = read_calibrated_window(flood_meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    if flood_db.shape != base_db.shape:
        print(f"  [skip] #{cand['report_number']} {date}: shape mismatch (will retry)")
        return None, False

    valid = (flood_db > -59.0) & (base_db > -59.0)
    flood_water = (flood_db < WATER_DB_THRESHOLD) & valid
    base_water = (base_db < WATER_DB_THRESHOLD) & valid
    new_water = flood_water & ~base_water

    result = {
        "report_number": cand["report_number"], "country": cand["country"],
        "lat": lat, "lon": lon, "dfo_window": f"{cand['begin_date']}/{cand['end_date']}",
        "scene_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  #{cand['report_number']} {cand['country']} ({date}, orbit {orbit}): "
          f"new-water {result['pct_new_water_flood_only']}%  "
          f"(flood {result['pct_water_flood_day']}% / baseline {result['pct_water_baseline_day']}%)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(base_db, cmap="gray", vmin=-25, vmax=0)
        axes[0].set_title(f"#{cand['report_number']} baseline (orbit {orbit})")
        axes[1].imshow(flood_db, cmap="gray", vmin=-25, vmax=0)
        axes[1].set_title(f"flood day {date}")
        axes[2].imshow(new_water, cmap="Blues")
        axes[2].set_title("new water (flood-only)")
        for a in axes:
            a.axis("off")
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / f"s1_himfull_{cand['report_number']}_{date}_water_check.png",
                    dpi=100, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass

    return result, False


def main() -> None:
    candidates = build_candidates()
    print(f"Himalaya-pooled WHERE player — full rollout, {len(candidates)} candidates "
          f"(2019+, Himalaya arc, GFD can't reach these)\n")

    results, no_coverage = [], []
    if REPORT_OUT.exists():
        prior = json.loads(REPORT_OUT.read_text())
        results = prior.get("results", [])
        no_coverage = prior.get("no_coverage", [])
        # only permanently skip successes and confirmed no-coverage — a
        # transient failure (timeout, temp baseline miss) stays in todo so
        # rerunning this script retries it, same as fetch_25's pattern.
        done = {r["report_number"] for r in results} | set(no_coverage)
        todo = [c for c in candidates if c["report_number"] not in done]
        print(f"resuming: {len(results)} done, {len(no_coverage)} confirmed no-coverage, {len(todo)} left\n")
    else:
        todo = candidates

    for i, cand in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] #{cand['report_number']} {cand['country']} "
              f"{cand['begin_date']}..{cand['end_date']}")
        try:
            r, permanent = process_one(cand)
            if r:
                results.append(r)
            elif permanent:
                no_coverage.append(cand["report_number"])
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] #{cand['report_number']}: {type(exc).__name__}: {str(exc)[:150]} (will retry)")

        REPORTS.mkdir(parents=True, exist_ok=True)
        REPORT_OUT.write_text(json.dumps({
            "note": "Full Himalaya-arc Sentinel-1 rollout for 2019+ DFO events "
                    "(the years GFD's MODIS archive can't reach). Each candidate's "
                    "check point is DFO's own representative_point(), not a "
                    "hand-picked town — some genuinely land on a dry/unaffected "
                    "spot inside a crude news-polygon and correctly score ~0%, "
                    "that's an expected outcome of the method, not a bug.",
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
