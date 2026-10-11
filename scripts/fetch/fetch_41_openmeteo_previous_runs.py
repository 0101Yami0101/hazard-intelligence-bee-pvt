"""What Open-Meteo's forecast said 1-6 days ahead, kept for every past day.

    python scripts/fetch/fetch_41_openmeteo_previous_runs.py

Writes  data/interim/rainfall_om_prev/prev_mm.npy    (7, days, 219) float32, mm per UTC day
                                                     [0] = the service's own record of what fell,
                                                     [n] = the forecast made n days earlier
        data/interim/rainfall_om_prev/dates.npy
        data/interim/rainfall_om_prev/_months/*.npz  one file per month (resumable)

For grading the flood forecast by how far ahead it looks
(docs/design/LEAD_DAY_TEST.md). The points are the live run's own 219
(data/interim/rainfall_om/points.json), and the default model mix is the one
the live forecast reads, so this is the rain the screen would have been fed.

The archive holds forecasts made 1-6 days ahead from 2024-01-25 (checked
2026-10-11). The seventh comes from another model there and is not fetched.

Free-service limits: 600 weighted calls a minute, 5,000 an hour, 10,000 a
day; a request's weight grows with its days and variables. One month for all
219 points is about 350, so this paces itself at one month every five
minutes and can be stopped and started again.
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

from common import INTERIM, UA

API = "https://previous-runs-api.open-meteo.com/v1/forecast"
OUT = INTERIM / "rainfall_om_prev"
START, END = "2024-01-01", "2025-10-31"
LEADS = 7                      # 0 = what fell, 1..6 = forecast made that many days earlier
VARS = ["precipitation"] + [f"precipitation_previous_day{i}" for i in range(1, LEADS)]
BATCH = 40                     # points per request
PAUSE_S = 300                  # between months


def fetch_month(lat, lon, a: str, b: str) -> np.ndarray:
    """(LEADS, days, points) for one month; NaN where the archive has nothing."""
    days = pd.date_range(a, b, freq="D")
    out = np.full((LEADS, len(days), len(lat)), np.nan, dtype=np.float32)
    for i in range(0, len(lat), BATCH):
        la, lo = lat[i:i + BATCH], lon[i:i + BATCH]
        for attempt in range(6):
            try:
                r = requests.get(API, params={
                    "latitude": ",".join(f"{x:.4f}" for x in la),
                    "longitude": ",".join(f"{x:.4f}" for x in lo),
                    "hourly": ",".join(VARS), "start_date": a, "end_date": b,
                    "timezone": "UTC"}, timeout=180, headers=UA)
                if r.status_code == 429:
                    wait = 120 * (attempt + 1)
                    print(f"      over the limit, waiting {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                js = r.json()
                js = js if isinstance(js, list) else [js]
                if len(js) != len(la):
                    raise RuntimeError(f"asked {len(la)} points, got {len(js)}")
                break
            except Exception as e:                                  # noqa: BLE001
                print(f"      retry {attempt + 1}: {type(e).__name__}: {str(e)[:120]}", flush=True)
                time.sleep(20 * (attempt + 1))
        else:
            raise SystemExit(f"gave up on {a}..{b}, points {i}..{i + len(la)}")
        for j, x in enumerate(js):
            h = x["hourly"]
            t = pd.to_datetime(h["time"])
            for k, v in enumerate(VARS):
                s = pd.Series(pd.to_numeric(pd.Series(h[v]), errors="coerce").to_numpy(), index=t)
                # a day counts only if all 24 hours are there: a part-day sum is not that day's rain
                g = s.groupby(s.index.normalize())
                d = g.sum(min_count=24).reindex(days)
                out[k, :, i + j] = d.to_numpy(np.float32)
        time.sleep(2)
    return out


def main() -> None:
    pts = json.loads((INTERIM / "rainfall_om" / "points.json").read_text())
    lat, lon = np.asarray(pts["lat"], float), np.asarray(pts["lon"], float)
    (OUT / "_months").mkdir(parents=True, exist_ok=True)
    months = pd.period_range(START, END, freq="M")
    print(f"Open-Meteo previous runs: {len(lat)} points, {months[0]} .. {months[-1]}")
    for n, m in enumerate(months):
        f = OUT / "_months" / f"{m}.npz"
        if f.exists():
            print(f"  {m}: already here")
            continue
        a, b = str(m.start_time.date()), min(str(m.end_time.date()), END)
        t0 = time.time()
        arr = fetch_month(lat, lon, a, b)
        np.savez_compressed(f, mm=arr, start=a, end=b)
        have = [int(np.isfinite(arr[k]).all(axis=1).sum()) for k in range(LEADS)]
        print(f"  {m}: {arr.shape[1]} days, complete days by lead {have} ({time.time() - t0:.0f}s)",
              flush=True)
        if n < len(months) - 1:
            time.sleep(PAUSE_S)
    parts = [np.load(OUT / "_months" / f"{m}.npz")["mm"] for m in months]
    mm = np.concatenate(parts, axis=1)
    dates = pd.date_range(START, END, freq="D")
    assert mm.shape == (LEADS, len(dates), len(lat)), mm.shape
    np.save(OUT / "prev_mm.npy", mm)
    np.save(OUT / "dates.npy", np.array([str(d.date()) for d in dates]))
    print(f"  wrote {OUT / 'prev_mm.npy'} {mm.shape}; complete days by lead: "
          f"{[int(np.isfinite(mm[k]).all(axis=1).sum()) for k in range(LEADS)]}")


if __name__ == "__main__":
    main()
