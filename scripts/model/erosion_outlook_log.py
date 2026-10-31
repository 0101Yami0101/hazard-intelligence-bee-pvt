"""Write down SoilSense's weekly erosive-rain outlook every day (E2.1).

    $env:REGION = "assam"; python scripts/model/erosion_outlook_log.py          # fetch live rain, log today's issue
    $env:REGION = "assam"; python scripts/model/erosion_outlook_log.py check    # rebuild every logged issue from its file

Writes  records/erosion_outlook/<region>/issues/<issued_on>.npz   the 7 days' rain at every point
        records/erosion_outlook/<region>/state.csv                 the state's figures, one row per day
        records/erosion_outlook/<region>/districts.csv             the district table, per day

Same reason as the landslide log (landslide_forecast_log.py): an outlook that was
never written down before the week cannot be graded after it. An issue keeps the
forecast rain at every point and the checksum of the fixed inputs it was used with
(assets/erosion/<region>/outlook_base.npz), so every number the page showed that
day can be worked out again — `check` proves it. The numbers come from the app's
own function (products.erosion.outlook.compute), never a second copy of the maths.

What it is not, yet: a grade. The rain part can be graded against satellite rain
(E2.2) once the region's IMERG archive is fetched; the soil part cannot be graded
with open data.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "webapp"), str(ROOT / "scripts")]

import numpy as np
import pandas as pd

from common import AOI_NAME

BASE = ROOT / "webapp" / "assets" / "erosion" / AOI_NAME / "outlook_base.npz"
REC = ROOT / "records" / "erosion_outlook" / AOI_NAME


def base():
    z = np.load(BASE)
    meta = json.loads((BASE.parent / "outlook_meta.json").read_text())
    return {k: z[k] for k in z.files}, meta, hashlib.sha256(BASE.read_bytes()).hexdigest()[:16]


def rows_for(issued: str, W: dict, meta: dict) -> tuple[dict, list[dict]]:
    state = {"issued_on": issued, "week_from": W["days"][0], "week_to": W["days"][-1],
             "state_x_normal": round(W["state_x"], 3), "state_share_of_year_pct": round(100 * W["state_share"], 3),
             "state_soil_at_risk_tpha": round(W["state_week"], 4),
             "points_over_2x_normal": int(np.nansum(W["x_normal"] >= 2)),
             "rain_mm_median_point": round(float(np.median(W["rain_mm"])), 1)}
    dist = [{"issued_on": issued, "district": n, "soil_at_risk_tpha": round(float(W["dis_week"][k]), 4),
             "x_normal": None if not np.isfinite(W["dis_x"][k]) else round(float(W["dis_x"][k]), 3)}
            for k, n in enumerate(meta["districts"])]
    return state, dist


def log() -> None:
    from core.rainfall import fetch_rain
    from products.erosion.outlook import compute
    z, meta, sha = base()
    fc = fetch_rain(list(map(float, z["lat"])), list(map(float, z["lon"])))
    if fc is None:
        raise SystemExit("live rain could not be fetched; nothing logged")
    days, rain = fc
    W = compute(z, days, rain)
    issued = date.today().isoformat()
    (REC / "issues").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(REC / "issues" / f"{issued}.npz", days=np.array(days).astype(str),
                        rain=rain.astype(np.float32), base_sha=np.array(sha),
                        logged_utc=np.array(datetime.now(timezone.utc).isoformat(timespec="seconds")))
    state, dist = rows_for(issued, W, meta)
    for name, rows in (("state.csv", [state]), ("districts.csv", dist)):
        f = REC / name
        old = pd.read_csv(f) if f.exists() else pd.DataFrame()
        if len(old):
            old = old[old.issued_on != issued]
        pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(f, index=False)
    print(f"  logged {issued}: week {state['week_from']} to {state['week_to']}, "
          f"{state['state_x_normal']}x normal, {state['state_share_of_year_pct']}% of a year's erosive rain")


def check() -> None:
    from products.erosion.outlook import compute
    z, meta, sha = base()
    st = pd.read_csv(REC / "state.csv")
    bad = 0
    for f in sorted((REC / "issues").glob("*.npz")):
        k = np.load(f)
        if str(k["base_sha"]) != sha:
            print(f"  {f.stem}: logged with other fixed inputs ({k['base_sha']}); skipped")
            continue
        W = compute(z, k["days"], k["rain"])
        state, _ = rows_for(f.stem, W, meta)
        row = st[st.issued_on == f.stem].iloc[0]
        same = all(abs(float(row[c]) - float(state[c])) < 1e-3 for c in
                   ("state_x_normal", "state_share_of_year_pct", "state_soil_at_risk_tpha"))
        bad += not same
        print(f"  {f.stem}: {'rebuilt exactly' if same else 'DIFFERS'}")
    print("PASS" if not bad else f"FAIL {bad}")


if __name__ == "__main__":
    check() if "check" in sys.argv else log()
