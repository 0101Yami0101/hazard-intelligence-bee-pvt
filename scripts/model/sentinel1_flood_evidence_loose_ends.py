"""WHERE loose-ends cleanup, 2026-08-31 — the remaining gaps from the first
statewide rollout pass, now closed:

    - Tuting, Pangin, Lemeking, Namsai: had zero confirmed flood days
      (backtest_flood_when.py never reached their real CWC danger level in
      the full record) until the self-derived-proxy fallback fix; now have
      real flood-day labels and a real satellite date to check.
    - Yinkiang: originally checked on 2023-08-29 and scored an exact 0.0% —
      retried here on a different exact-match date (2020-06-28) to see if
      that was date-specific or a real station limit.
    - Seppa, Tamen: had a confirmed flood day but no EXACT satellite match,
      only a 2-day-away one — checked here on that nearest real date.

Reuses the same calibration/warp pipeline as every other WHERE check.

Output:
    reports/flood_where_s1_loose_ends.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common import INTERIM, ROOT
from flood_stations import STATIONS
from sentinel1_flood_evidence import WATER_DB_THRESHOLD, read_calibrated_window, scene_meta

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
BUF_DEG = 0.15

# code -> (flood date, flood scene stem, orbit, note)
TARGETS = {
    "002-ubddib": ("2016-07-26", "S1A_IW_GRDH_1SSV_20160726T233755_20160726T233809_012326_0132FF_413C_COG.SAFE", 4, "newly-fixed (zero-crossing fallback)"),
    "003NEID-3": ("2019-08-09", "S1A_IW_GRDH_1SDV_20190809T114100_20190809T114125_028492_03387C_10CA_COG.SAFE", 70, "newly-fixed (zero-crossing fallback)"),
    "004-UBDDIB": ("2021-08-29", "S1A_IW_GRDH_1SDV_20210829T233842_20210829T233907_039451_04A930_F4B4_COG.SAFE", 4, "newly-fixed (zero-crossing fallback)"),
    "009-UBDDIB": ("2020-07-12", "S1A_IW_GRDH_1SDV_20200712T233023_20200712T233048_033428_03DF9C_447D_COG.SAFE", 106, "newly-fixed (zero-crossing fallback)"),
    "003-UBDDIB": ("2020-06-28", "S1A_IW_GRDH_1SDV_20200628T114129_20200628T114154_033217_03D925_FECD_COG.SAFE", 70, "Yinkiang retry — first date (2023-08-29) scored exact 0.0%"),
    "027-UBDDIB": ("2026-07-15", "S1D_IW_GRDH_1SDV_20260715T114834_20260715T114853_003684_006956_B4D9_COG.SAFE", 143, "Seppa — nearest scene to 2026-07-13 flood day, 2 days off"),
    "070-UBDDIB": ("2022-07-07", "S1A_IW_GRDH_1SDV_20220707T233845_20220707T233910_044001_054098_AA14_COG.SAFE", 4, "Tamen — nearest scene to 2022-07-09 flood day, 2 days off"),
}
BASELINE_BY_ORBIT = {
    4: "S1A_IW_GRDH_1SDV_20250329T233844_20250329T233909_058526_073DE4_5284_COG.SAFE",
    70: "S1A_IW_GRDH_1SDV_20250322T114115_20250322T114140_058417_073988_F6FE_COG.SAFE",
    106: "S1A_IW_GRDH_1SDV_20250324T233033_20250324T233058_058453_073AF4_3D74_COG.SAFE",
    143: "S1A_IW_GRDH_1SDV_20250327T114927_20250327T114952_058490_073C5E_2411_COG.SAFE",
}

_baseline_cache: dict[tuple, np.ndarray] = {}


def baseline_for(orbit: int, lat: float, lon: float) -> np.ndarray:
    key = (orbit, round(lat, 3), round(lon, 3))
    if key not in _baseline_cache:
        meta = scene_meta(BASELINE_BY_ORBIT[orbit])
        _baseline_cache[key] = read_calibrated_window(meta, lat=lat, lon=lon, buf_deg=BUF_DEG)
    return _baseline_cache[key]


def check_one(code: str) -> dict | None:
    date, scene_stem, orbit, note = TARGETS[code]
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
        "station_code": code, "station_name": meta["name"], "note": note,
        "flood_date": date, "orbit": orbit,
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {meta['name']} ({date}, orbit {orbit}): new-water "
          f"{result['pct_new_water_flood_only']}%  (flood {result['pct_water_flood_day']}% "
          f"/ baseline {result['pct_water_baseline_day']}%)  -- {note}")
    return result


def main() -> None:
    print("WHERE loose-ends cleanup — 7 checks\n")
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
    out = REPORTS / "flood_where_s1_loose_ends.json"
    out.write_text(json.dumps({"n_checked": len(results), "n_targeted": len(TARGETS),
                                "results": results}, indent=2))
    print(f"\nwrote {out}  ({len(results)}/{len(TARGETS)} checked)")
    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"positive signal: {sum(1 for v in vals if v > 0)}/{len(vals)}")


if __name__ == "__main__":
    main()
