"""The forecasts the weekly erosion outlook WOULD have read, May-Sep 2023-2025 (E2.2).

    $env:REGION = "assam"; python scripts/fetch/fetch_51_outlook_replay_forecasts.py

The replay test was written down first (EROSION_PLAN.md, "E2.2 part 1"). Open-Meteo's
previous-runs service keeps, for past hours, what the forecast said K days earlier
(`precipitation_previous_dayK`). Day D+k of a week issued on D is read at lead k:
`precipitation` for k = 0 and `precipitation_previous_day{k}` for k = 1..6, summed from
hours into UTC days (the app's day boundary).

Points: every other point of the outlook's 0.2 deg lattice (a checkerboard, 124 of
248), to stay inside Open-Meteo's free limits. Each request is cached to disk, so a
rate-limit stop costs nothing on a re-run.

Output: data/interim/<region>/outlook_replay/forecast_daily.npz
        dates [n_days], lead_rain [n_days, 7, n_points] mm, lat, lon, point_index
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import requests

from common import INTERIM, record

API = "https://previous-runs-api.open-meteo.com/v1/forecast"
YEARS = (2023, 2024, 2025)
WINDOW = ("05-01", "10-06")          # last issue 29 Sep + 6 days
LEADS = ["precipitation"] + [f"precipitation_previous_day{k}" for k in range(1, 7)]
BATCH, PAUSE = 25, 20.0
OUT = INTERIM / "outlook_replay"
CACHE = OUT / "_batches"


def points() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pts = json.loads((INTERIM / "rainfall_om" / "points.json").read_text())
    lat, lon = np.array(pts["lat"]), np.array(pts["lon"])
    keep = ((np.round(lat / 0.2) + np.round(lon / 0.2)) % 2 == 0)
    return lat[keep], lon[keep], np.nonzero(keep)[0]


def fetch(la, lo, d0, d1, tag) -> pd.DataFrame | None:
    """Hourly lead-K rain for a batch -> daily sums, columns (lead, point)."""
    f = CACHE / f"{tag}.parquet"
    if f.exists():
        return pd.read_parquet(f)
    for attempt in range(12):
        try:
            r = requests.get(API, params={"latitude": ",".join(f"{x:.4f}" for x in la),
                                          "longitude": ",".join(f"{x:.4f}" for x in lo),
                                          "hourly": ",".join(LEADS), "start_date": d0, "end_date": d1,
                                          "timezone": "UTC"}, timeout=300)
            if r.status_code == 429:
                wait = 600 if "Hourly" in r.text or "hourly" in r.text else 90
                print(f"      429 — waiting {wait}s ({r.text[:80]})", flush=True)
                time.sleep(wait)
                continue
            js = r.json()
            if isinstance(js, dict) and js.get("error"):
                print(f"      error: {js.get('reason', '')[:120]}", flush=True)
                time.sleep(60)
                continue
            res = js if isinstance(js, list) else [js]
            cols = {}
            for j, x in enumerate(res):
                h = pd.DataFrame(x["hourly"])
                h["day"] = pd.to_datetime(h["time"]).dt.floor("D")
                daily = h.drop(columns="time").groupby("day").sum(min_count=1)
                for k, v in enumerate(LEADS):
                    cols[(k, j)] = daily[v]
            df = pd.DataFrame(cols)
            df.columns = [f"{k}_{j}" for k, j in df.columns]
            df.to_parquet(f)
            return df
        except Exception as exc:  # noqa: BLE001
            print(f"      try {attempt + 1}: {str(exc)[:120]}", flush=True)
            time.sleep(30 * (attempt + 1))
    return None


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    lat, lon, pidx = points()
    batches = [slice(i, i + BATCH) for i in range(0, len(lat), BATCH)]
    print(f"Outlook replay forecasts — {len(lat)} points, {YEARS}, {len(batches) * len(YEARS)} requests",
          flush=True)
    frames = []
    for y in YEARS:
        parts = []
        for bi, sl in enumerate(batches):
            d = fetch(lat[sl], lon[sl], f"{y}-{WINDOW[0]}", f"{y}-{WINDOW[1]}", f"y{y}_b{bi}")
            if d is None:
                raise SystemExit(f"  {y} batch {bi} FAILED — re-run to resume")
            d.columns = [f"{c.split('_')[0]}_{int(c.split('_')[1]) + sl.start}" for c in d.columns]
            parts.append(d)
            print(f"    {y} batch {bi + 1}/{len(batches)}", flush=True)
            time.sleep(PAUSE)
        frames.append(pd.concat(parts, axis=1))
    full = pd.concat(frames).sort_index()
    arr = np.full((len(full), len(LEADS), len(lat)), np.nan, np.float32)
    for c in full.columns:
        k, j = map(int, c.split("_"))
        arr[:, k, j] = full[c].to_numpy(np.float32)
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "forecast_daily.npz"
    np.savez_compressed(dest, dates=full.index.values.astype("datetime64[D]"), lead_rain=arr,
                        lat=lat.astype(np.float32), lon=lon.astype(np.float32), point_index=pidx)
    record(OUT, source="Open-Meteo previous-runs API (archived forecasts, lead 0-6 days)", url=API,
           files=[dest], license_="Open-Meteo: CC-BY 4.0",
           notes=f"{len(lat)} outlook points (checkerboard of the 0.2 deg lattice), May-early Oct "
                 f"{YEARS}, hourly summed to UTC days (fetch_51_outlook_replay_forecasts.py).")
    print(f"  wrote {dest}: {arr.shape}, missing {np.isnan(arr).mean():.3%}")


if __name__ == "__main__":
    main()
