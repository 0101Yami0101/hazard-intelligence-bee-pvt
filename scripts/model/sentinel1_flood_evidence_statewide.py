"""WHERE rollout, step 2 — calibrated Sentinel-1 water check at the other 9
CWC stations with a real exact-date satellite match (see
reports/flood_where_s1_feasibility_statewide.json, produced by
fetch_23_sentinel1_statewide_dates.py).

Reuses the exact calibration/warp pipeline built and debugged for Jang
valley (sentinel1_flood_evidence.py's read_calibrated_window/scene_meta/
parse_calibration_lut — two real bugs were found and fixed there; nothing
new is reinvented here), generalized to each station's own real location
(flood_stations.py) instead of one fixed point.

One flood date per station this pass (not every exact match, unlike the
12-date Jang sweep) — proving the signal exists at each new location, not
yet repeating it across every date at every station. Six of the nine share
relative orbit 4, so only 4 new baseline scenes covered all 9.

Output:
    reports/flood_where_s1_statewide.json
    data/interim/flood_when/s1_<station>_<date>_water_check.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common import INTERIM, ROOT
from flood_stations import STATIONS
from sentinel1_flood_evidence import (WATER_DB_THRESHOLD, read_calibrated_window,
                                       scene_meta)

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
BUF_DEG = 0.15

# station code -> (flood date, flood scene zip stem, relative orbit)
TARGETS = {
    "001-UBDDIB": ("2016-07-26", "S1A_IW_GRDH_1SSV_20160726T113247_20160726T113312_012319_0132BD_B0A9_COG.SAFE", 172),
    "003-UBDDIB": ("2023-08-29", "S1A_IW_GRDH_1SDV_20230829T114937_20230829T115002_050090_06070A_3022_COG.SAFE", 143),
    "005-UBDDIB": ("2021-08-29", "S1A_IW_GRDH_1SDV_20210829T233842_20210829T233907_039451_04A930_F4B4_COG.SAFE", 4),
    "007NEID3": ("2022-09-05", "S1A_IW_GRDH_1SDV_20220905T233849_20220905T233914_044876_055C2B_D3CB_COG.SAFE", 4),
    "008-ubddib": ("2026-04-22", "S1C_IW_GRDH_1SDV_20260423T233720_20260423T233751_007350_00EE8E_680F_COG.SAFE", 4),
    "020-UBDDIB": ("2019-07-22", "S1A_IW_GRDH_1SDV_20190723T233819_20190723T233848_028251_0330F8_6466_COG.SAFE", 4),
    "058-UBDDIB": ("2024-11-17", "S1A_IW_GRDH_1SDV_20241117T233850_20241117T233915_056601_06F126_F78A_COG.SAFE", 4),
    "059-UBDDIB": ("2024-07-01", "S1A_IW_GRDH_1SDV_20240701T114121_20240701T114146_054567_06A442_9750_COG.SAFE", 70),
    "078-UBDDIB": ("2026-07-29", "S1D_IW_GRDH_1SDV_20260729T233756_20260729T233821_003895_0070A3_F0C2_COG.SAFE", 4),
}
BASELINE_BY_ORBIT = {
    4: "S1A_IW_GRDH_1SDV_20250329T233844_20250329T233909_058526_073DE4_5284_COG.SAFE",
    172: "S1A_IW_GRDH_1SDV_20250329T113306_20250329T113331_058519_073D94_41B4_COG.SAFE",
    143: "S1A_IW_GRDH_1SDV_20250327T114927_20250327T114952_058490_073C5E_2411_COG.SAFE",
    70: "S1A_IW_GRDH_1SDV_20250322T114115_20250322T114140_058417_073988_F6FE_COG.SAFE",
}

_baseline_cache: dict[tuple[int, float, float], np.ndarray] = {}


def baseline_for(orbit: int, lat: float, lon: float) -> np.ndarray:
    key = (orbit, round(lat, 3), round(lon, 3))
    if key not in _baseline_cache:
        meta = scene_meta(BASELINE_BY_ORBIT[orbit])
        _baseline_cache[key] = read_calibrated_window(meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    return _baseline_cache[key]


def check_one(code: str) -> dict | None:
    date, scene_stem, orbit = TARGETS[code]
    meta = STATIONS[code]
    lat, lon = meta["lat"], meta["lon"]

    flood_meta = scene_meta(scene_stem)
    flood_db = read_calibrated_window(flood_meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    base_db = baseline_for(orbit, lat, lon)

    assert flood_db.shape == base_db.shape
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
    print("WHERE rollout — calibrated Sentinel-1 water check, 9 new stations\n")
    results = []
    for code in TARGETS:
        try:
            r = check_one(code)
            if r:
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {STATIONS[code]['name']} ({code}): "
                  f"{type(exc).__name__}: {str(exc)[:150]}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_where_s1_statewide.json"
    out.write_text(json.dumps({
        "note": "One flood date per station, proving the signal exists at "
                "each new location — not a repeated multi-date sweep the "
                "way Jang valley got (see flood_where_s1_jang_multi_date.json). "
                "Reuses the same calibration/warp pipeline debugged there.",
        "n_stations_checked": len(results),
        "n_stations_targeted": len(TARGETS),
        "results": results,
    }, indent=2))
    print(f"\nwrote {out}  ({len(results)}/{len(TARGETS)} stations checked)")

    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"\nnew-water %: min {min(vals):.1f}  median {sorted(vals)[len(vals)//2]:.1f}  "
              f"max {max(vals):.1f}  mean {sum(vals)/len(vals):.1f}")
        print(f"stations with a positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
