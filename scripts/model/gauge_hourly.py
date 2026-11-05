"""Every CWC gauge's readings, hour by hour: the last 3 days for the app's
"hourly" graph, and every reading saved, so an hourly level forecast has
history to learn from one day (no such model exists yet; the level line is
a forecast of the DAILY high, trained on daily highs).

Run every hour by the cloud job (scripts/cloud/modal_daily.py, `hourly`):
CWC's site does not answer from outside India, so the hosted app cannot
fetch these itself. On the PC:

    python scripts/model/gauge_hourly.py [out_dir]

CWC gauges only. NWDP's are 15-minute but publish about 2 days late, which
an "hourly, now" graph cannot use.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backtest_flood_when import clean_readings
from common import ROOT
from flood_gauge_live import GMODELS, cwc_readings

HOURS = 72           # shown in the app
CONTEXT_DAYS = 7     # fetched: the spike filter needs neighbours on both sides


def collect(now: datetime | None = None) -> tuple[dict, pd.DataFrame]:
    """(the app's file, every raw reading fetched). One silent gauge never
    stops the others; it is listed under "failed"."""
    now = now or datetime.now()
    stations = json.loads((GMODELS / "stations.json").read_text())
    since = (now - timedelta(days=CONTEXT_DAYS)).date()
    cut = pd.Timestamp(now) - pd.Timedelta(hours=HOURS)
    gauges, failed, raw = {}, [], []
    for code, st in stations.items():
        if st["network"] != "CWC":
            continue
        try:
            df = cwc_readings(code, since)
        except Exception as e:                                      # noqa: BLE001
            failed.append(code)
            print(f"    [warn] {code}: gauge feed unavailable ({type(e).__name__})")
            continue
        if not len(df):
            gauges[code] = []
            continue
        raw.append(df.assign(code=code))
        # the same cleaning the forecast uses (_cwc_daily), so this line and
        # the daily highs beside it never disagree about a spike
        c = clean_readings(df.reset_index(drop=True))
        c = c[c["datetime"] >= cut]
        gauges[code] = [[t.isoformat(timespec="minutes"), round(float(v), 3)]
                        for t, v in zip(c["datetime"], c["level"])]
    out = {"made_at": now.astimezone().isoformat(timespec="seconds"), "hours": HOURS,
           "network": "CWC", "gauges": gauges, "failed": failed}
    allraw = (pd.concat(raw, ignore_index=True)[["code", "datetime", "level"]] if raw
              else pd.DataFrame(columns=["code", "datetime", "level"]))
    return out, allraw


def archive(raw: pd.DataFrame, folder: Path) -> int:
    """Add the readings to one CSV a month (code, datetime, level), as sent:
    uncleaned, so any later cleaning can be redone. Returns rows added."""
    folder.mkdir(parents=True, exist_ok=True)
    added = 0
    if not len(raw):
        return 0
    raw = raw.assign(datetime=pd.to_datetime(raw["datetime"]))
    for month, g in raw.groupby(raw["datetime"].dt.strftime("%Y-%m")):
        f = folder / f"cwc_{month}.csv"
        old = pd.read_csv(f, parse_dates=["datetime"]) if f.exists() else g.iloc[:0]
        new = (pd.concat([old, g], ignore_index=True)
               .drop_duplicates(["code", "datetime"], keep="last")
               .sort_values(["code", "datetime"], kind="stable"))
        added += len(new) - len(old)
        new.to_csv(f, index=False)
    return added


def run(out_dir: Path) -> dict:
    out, raw = collect()
    n = archive(raw, out_dir / "raw")
    (out_dir / "latest.json").write_text(json.dumps(out, separators=(",", ":")))
    print(f"{sum(map(len, out['gauges'].values()))} readings over {HOURS} h from "
          f"{len(out['gauges'])} gauges ({len(out['failed'])} failed); {n} new rows saved")
    return out


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "records" / "gauge_hourly")
