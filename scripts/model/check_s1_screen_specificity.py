"""How often does the Sentinel-1 screen "confirm" a flood when there was none?

    python scripts/model/check_s1_screen_specificity.py

Writes  reports/flood_s1_screen_specificity.json

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
fetch_32's screen (new water within ~17 km vs a dry-season image, positive
above 0.3%) was only ever validated on 4 real floods — it caught all four.
It was never run on dates WITHOUT a flood. It was used to confirm most of
the flood records every model here trains on, and the new-records intake
(flood_intake.py) reuses it. Found 2026-09-27: at 3 places with a confirmed
2024 flood, the same screen on 15 Jan 2024 — dry season — also came back
positive, with more "new water" than on the flood dates.

THE TEST
    40 screen-positive records (2019+, fixed seed), each checked on:
      its own date            (re-check)
      the same place, one year apart, same time of year, no record within
      20 km and 30 days       (season-matched control)
      the same place, mid-January of that year, no record within 20 km and
      30 days                  (dry-season control)
    The per-orbit baseline cache is cleared before every check, so each place
    is compared with a dry image that actually covers it (fetch_32 kept one
    baseline per orbit for the whole batch, whichever place asked first).

Reported: the new-water % distributions, the share of controls the 0.3% rule
calls "positive", and how many real records clear the controls' 95th
percentile — the noise floor a meaningful confirmation has to beat.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from common import ROOT

N = 40
SEED = 42
KM = 111.2


def main() -> None:
    import ee
    import fetch_32_groundsource_s1_ee_screen as s1
    ee.Initialize(project="earthengine-507510")
    rep = json.loads((ROOT / "reports" / "flood_where_groundsource_s1_ee_screen.json")
                     .read_text(encoding="utf-8"))
    pos = pd.DataFrame([r for r in rep["results"] if r.get("screen_positive")])
    pos["date"] = pd.to_datetime(pos["date_str"])
    allrec = pd.DataFrame([r for r in rep["results"]])      # every candidate, positive or not
    allrec["date"] = pd.to_datetime(allrec["date_str"])
    pos = pos[pos["date"] <= "2025-06-30"].sample(N, random_state=SEED).reset_index(drop=True)

    def clear(lat, lon, d: pd.Timestamp) -> bool:
        near = allrec[(abs(allrec["date"] - d) <= pd.Timedelta(days=30))]
        dist = KM * np.hypot(near["lat"] - lat, (near["lon"] - lon) * np.cos(np.radians(lat)))
        return not (dist <= 20).any()

    def screen(lat, lon, day: str) -> dict:
        s1._baseline_cache.clear()
        return s1.process_one({"lat": lat, "lon": lon, "date_str": day})

    rows = []
    with cf.ThreadPoolExecutor(max_workers=1) as pool:
        for i, e in pos.iterrows():
            d = e["date"]
            season = next((c for c in (d + pd.DateOffset(years=1), d - pd.DateOffset(years=1))
                           if c <= pd.Timestamp("2025-10-31") and clear(e["lat"], e["lon"], c)), None)
            dry = pd.Timestamp(date(d.year, 1, 15))
            dry = dry if clear(e["lat"], e["lon"], dry) else None
            for kind, day in (("flood date", d), ("season control", season), ("dry control", dry)):
                if day is None:
                    continue
                try:
                    r = pool.submit(screen, e["lat"], e["lon"], str(day.date())).result(timeout=90)
                except Exception as ex:                             # noqa: BLE001
                    r = {"error": type(ex).__name__}
                rows.append({"record": i, "kind": kind, "date": str(day.date()),
                             "lat": e["lat"], "lon": e["lon"],
                             "pct_new_water": r.get("pct_new_water_screen"),
                             "positive_at_0.3": r.get("screen_positive"),
                             "image": r.get("s1_image_found"), "baseline": r.get("baseline_found"),
                             "original_pct": e.get("pct_new_water_screen")})
            print(f"  {i+1:>2}/{N}  {str(d.date())}  " + "  ".join(
                f"{x['kind']}: {x['pct_new_water']}" for x in rows if x["record"] == i), flush=True)

    df = pd.DataFrame(rows)
    ok = df["pct_new_water"].notna()
    out = {"what": ("fetch_32's Sentinel-1 screen on 40 screen-positive records and on "
                    "flood-free control dates at the same places"),
           "n_records": N, "by_kind": {}}
    for kind, g in df[ok].groupby("kind"):
        v = g["pct_new_water"].astype(float).to_numpy()
        out["by_kind"][kind] = {
            "n": int(len(v)), "median_pct": round(float(np.median(v)), 3),
            "p75_pct": round(float(np.percentile(v, 75)), 3),
            "p95_pct": round(float(np.percentile(v, 95)), 3),
            "positive_at_0.3pct": round(float(np.mean(v > 0.3)), 3)}
    ctrl = df[ok & df["kind"].str.contains("control")]["pct_new_water"].astype(float)
    floor95 = float(np.percentile(ctrl, 95)) if len(ctrl) else None
    flood = df[ok & (df["kind"] == "flood date")]["pct_new_water"].astype(float)
    out["control_noise_floor_p95_pct"] = round(floor95, 3) if floor95 is not None else None
    out["records_above_that_floor"] = (round(float(np.mean(flood > floor95)), 3)
                                       if floor95 is not None and len(flood) else None)
    allpos = pd.DataFrame([r for r in rep["results"] if r.get("screen_positive")])
    out["all_screen_positive_records_above_that_floor"] = (
        round(float(np.mean(allpos["pct_new_water_screen"].astype(float) > floor95)), 3)
        if floor95 is not None else None)
    out["rows"] = df.to_dict("records")
    (ROOT / "reports" / "flood_s1_screen_specificity.json").write_text(json.dumps(out, indent=2,
                                                                                 default=str))
    print("\n" + json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
