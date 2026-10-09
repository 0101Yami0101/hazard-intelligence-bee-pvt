"""Himalaya-pooled WHERE player — small proof batch before committing to the
full 77-296 event list from the DFO Global Flood Records archive.

User's explicit instruction: check 5-10 real events first, confirm the
whole idea actually works end to end, ask before scaling to the rest.

Picked 9 real, well-known Himalayan river towns (Bhutan, Nepal, Sikkim,
plus one already-known-good Arunachal town as a sanity check) whose
location a real DFO flood-event polygon actually contains, then checked
each against real Sentinel-1 passes for that flood window — same
find_scene_for_date/ensure_baseline helpers already built and debugged for
the statewide Arunachal expansion, nothing reinvented.

    python scripts/fetch/fetch_26_himalaya_pool_test.py

Output:
    reports/flood_where_himalaya_pool_test.json
    data/interim/flood_when/s1_himalaya_<slug>_<date>_water_check.png
"""
from __future__ import annotations

import json
import re
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
BUF_DEG = 0.15

# name, lat, lon, flood-scene date, DFO event window (for the record) —
# every date below already confirmed to have a real Sentinel-1 pass.
CANDIDATES = [
    ("Phuentsholing, Bhutan (Wangchu)", 26.8516, 89.3857, "2023-06-16", "2023-06-14/22"),
    ("Thimphu, Bhutan (Wangchu)", 27.4728, 89.6390, "2021-06-14", "2021-05-15/06-21"),
    ("Punakha, Bhutan (Mo/Pho Chhu)", 27.5921, 89.8797, "2021-06-14", "2021-05-15/06-21"),
    ("Kathmandu, Nepal (Bagmati)", 27.7172, 85.3240, "2021-07-02", "2021-07-01/04"),
    ("Pokhara, Nepal (Seti)", 28.2096, 83.9856, "2021-07-02", "2021-07-01/04"),
    ("Biratnagar, Nepal (Koshi)", 26.4525, 87.2718, "2021-06-19", "2021-06-15/21"),
    ("Rangpo, Sikkim (Teesta)", 27.1667, 88.5333, "2023-10-07", "2023-10-04 GLOF, +3d nearest pass"),
    ("Gangtok, Sikkim (Teesta basin)", 27.3389, 88.6065, "2023-10-07", "2023-10-04 GLOF, +3d nearest pass"),
    ("Along/Aalo, Arunachal (sanity check)", 28.1667, 94.8000, "2021-06-30", "2021-06-30/07-04"),
]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:30]


def process_one(name: str, lat: float, lon: float, date: str, tok: str) -> dict | None:
    prod = expand.find_scene_for_date(lat, lon, date)
    if prod is None:
        print(f"  [skip] {name} {date}: no scene on re-search")
        return None
    # same fix as fetch_25: CDSE tokens live ~10 min, too short for a
    # multi-item batch reusing one token — re-authenticate every download.
    tok = f14.token()
    dest = f14.download_one(prod, tok)
    if dest is None:
        print(f"  [FAIL] {name} {date}: download failed")
        return None
    stem = dest.name.removesuffix(".zip")
    orbit = int(f14.attr(prod, "relativeOrbitNumber"))

    base_db = expand.ensure_baseline(orbit, lat, lon, tok)
    if base_db is None:
        print(f"  [skip] {name} {date}: no baseline for orbit {orbit}")
        return None

    flood_meta = scene_meta(stem)
    flood_db = read_calibrated_window(flood_meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    if flood_db.shape != base_db.shape:
        print(f"  [skip] {name} {date}: shape mismatch")
        return None

    valid = (flood_db > -59.0) & (base_db > -59.0)
    flood_water = (flood_db < WATER_DB_THRESHOLD) & valid
    base_water = (base_db < WATER_DB_THRESHOLD) & valid
    new_water = flood_water & ~base_water

    result = {
        "name": name, "lat": lat, "lon": lon, "flood_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {name} ({date}, orbit {orbit}): new-water "
          f"{result['pct_new_water_flood_only']}%  (flood {result['pct_water_flood_day']}% "
          f"/ baseline {result['pct_water_baseline_day']}%)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(base_db, cmap="gray", vmin=-25, vmax=0)
        axes[0].set_title(f"{name} baseline (orbit {orbit})")
        axes[1].imshow(flood_db, cmap="gray", vmin=-25, vmax=0)
        axes[1].set_title(f"flood day {date}")
        axes[2].imshow(new_water, cmap="Blues")
        axes[2].set_title("new water (flood-only)")
        for a in axes:
            a.axis("off")
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / f"s1_himalaya_{slug(name)}_{date}_water_check.png", dpi=100, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass

    return result


def main() -> None:
    print("Himalaya-pooled WHERE player — 9-event proof batch (before the full 77-296)\n")
    tok = f14.token()
    results = []
    out = REPORTS / "flood_where_himalaya_pool_test.json"
    if out.exists():
        prior = json.loads(out.read_text())["results"]
        results = prior
        done_names = {r["name"] for r in results}
        todo = [c for c in CANDIDATES if c[0] not in done_names]
        print(f"resuming: {len(results)} already done, {len(todo)} left\n")
    else:
        todo = CANDIDATES
    for name, lat, lon, date, window in todo:
        try:
            r = process_one(name, lat, lon, date, tok)
            if r:
                r["dfo_event_window"] = window
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {name} {date}: {type(exc).__name__}: {str(exc)[:150]}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_where_himalaya_pool_test.json"
    out.write_text(json.dumps({
        "note": "Proof batch, not the full rollout. 9 real Himalayan-region "
                "flood dates picked from DFO's Global Flood Records archive "
                "(real news-sourced dates, but a specific well-known real "
                "river town chosen by hand as the check point, not the "
                "crude DFO polygon itself). Checked with the same debugged "
                "Sentinel-1 pipeline used for Arunachal throughout this "
                "project.",
        "n_checked": len(results), "n_targeted": len(CANDIDATES),
        "results": results,
    }, indent=2))
    print(f"\nwrote {out}  ({len(results)}/{len(CANDIDATES)} checked)")
    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"new-water %: min {min(vals):.2f} median {sorted(vals)[len(vals)//2]:.2f} "
              f"max {max(vals):.2f} mean {sum(vals)/len(vals):.2f}")
        print(f"positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
