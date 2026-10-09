"""WHERE rollout, pass 2 — calibrated Sentinel-1 water check at the 12
scored NWDP small-river stations (see backtest_flood_when_nwdp.py for the
WHEN half of this pass, and FLOOD_WHEN_PILOT_PLAN.md §8 for the plan that
called for this as a separate later pass).

One flood date per station, same as the first statewide CWC rollout.
Reuses the debugged calibration/warp pipeline unchanged.

Output:
    reports/flood_where_s1_nwdp.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common import INTERIM, ROOT
from nwdp_stations import STATIONS
from sentinel1_flood_evidence import WATER_DB_THRESHOLD, read_calibrated_window, scene_meta

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
BUF_DEG = 0.15

# code -> (flood date, flood scene stem, orbit)
TARGETS = {
    "Aalo_1": ("2026-06-04", "S1A_IW_GRDH_1SDV_20260604T233814_20260604T233843_064826_082B1B_009B_COG.SAFE", 4),
    "Basar_1": ("2024-07-01", "S1A_IW_GRDH_1SDV_20240701T114121_20240701T114146_054567_06A442_9750_COG.SAFE", 70),
    "Changlang": ("2024-08-13", "S1A_IW_GRDH_1SDV_20240813T233848_20240813T233913_055201_06BA78_C8BE_COG.SAFE", 4),
    "Changlang_1": ("2026-04-22", "S1C_IW_GRDH_1SDV_20260423T233720_20260423T233751_007350_00EE8E_680F_COG.SAFE", 4),
    "Darak(Kamba)": ("2025-07-27", "S1A_IW_GRDH_1SDV_20250727T233823_20250727T233852_060276_077DB0_7AF0_COG.SAFE", 4),
    "Kamlang_1": ("2024-05-02", "S1A_IW_GRDH_1SDV_20240502T114123_20240502T114148_053692_068599_8843_COG.SAFE", 70),
    "Kanubari_1": ("2026-05-06", "S1A_IW_GRDH_1SDV_20260506T233040_20260506T233105_064403_081C3F_F652_COG.SAFE", 106),
    "Tenga_1": ("2024-06-29", "S1A_IW_GRDH_1SDV_20240629T115741_20240629T115806_054538_06A32B_36FC_COG.SAFE", 41),
    "Tengapani Bridge_1": ("2026-04-22", "S1C_IW_GRDH_1SDV_20260423T233720_20260423T233751_007350_00EE8E_680F_COG.SAFE", 4),
    "Tissa Camp_1": ("2025-07-27", "S1C_IW_GRDH_1SDV_20250728T232925_20250728T232944_003427_006E39_F23B_COG.SAFE", 106),
    "Ziro": ("2023-07-24", "S1A_IW_GRDH_1SDV_20230724T114935_20230724T115000_049565_05F5C1_9C61_COG.SAFE", 143),
    "Sagalee_1": ("2024-10-05 (nearest scene to 2024-10-04 flood day, 1 day off)",
                  "S1A_IW_GRDH_1SDV_20241005T234659_20241005T234724_055974_06D844_4B19_COG.SAFE", 77),
}
BASELINE_BY_ORBIT = {
    4: "S1A_IW_GRDH_1SDV_20250329T233844_20250329T233909_058526_073DE4_5284_COG.SAFE",
    70: "S1A_IW_GRDH_1SDV_20250322T114115_20250322T114140_058417_073988_F6FE_COG.SAFE",
    106: "S1A_IW_GRDH_1SDV_20250324T233033_20250324T233058_058453_073AF4_3D74_COG.SAFE",
    143: "S1A_IW_GRDH_1SDV_20250327T114927_20250327T114952_058490_073C5E_2411_COG.SAFE",
    41: "S1A_IW_GRDH_1SDV_20250224T115734_20250224T115759_058038_072A4F_B044_COG.SAFE",
    77: "S1A_IW_GRDH_1SDV_20250226T234652_20250226T234717_058074_072BC7_396C_COG.SAFE",
}

_baseline_cache: dict[tuple, np.ndarray] = {}


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
        "station_code": code, "station_name": meta["name"], "district": meta["district"],
        "flood_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {meta['name']} ({date}, orbit {orbit}): new-water "
          f"{result['pct_new_water_flood_only']}%  (flood {result['pct_water_flood_day']}% "
          f"/ baseline {result['pct_water_baseline_day']}%)")
    return result


def main() -> None:
    print("WHERE rollout, pass 2 — calibrated Sentinel-1 water check, 12 NWDP stations\n")
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
    out = REPORTS / "flood_where_s1_nwdp.json"
    out.write_text(json.dumps({"n_checked": len(results), "n_targeted": len(TARGETS),
                                "results": results}, indent=2))
    print(f"\nwrote {out}  ({len(results)}/{len(TARGETS)} checked)")
    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"new-water %: min {min(vals):.1f} median {sorted(vals)[len(vals)//2]:.1f} "
              f"max {max(vals):.1f} mean {sum(vals)/len(vals):.1f}")
        print(f"positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
