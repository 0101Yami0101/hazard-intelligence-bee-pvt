"""CWC FFS river-gauge history — real, dated, government-measured river levels.

Phase 0 of the flood-WHEN pilot (docs/design/FLOOD_WHEN_PILOT_PLAN.md). Pulls
each station's full water-level (`HHS`) series plus its published danger/
warning thresholds from `ffs.india-water.gov.in`'s open REST API — no key, no
login. Discovered by capturing the app's real network traffic with a headless
browser; see `docs/data_research/DATA_VERIFICATION.md` Section C, Finding 11.

Station code is a parameter throughout, per the pilot plan's guardrail
("every script is generic from day one") — the STATIONS registry below is the
only thing that grows when more stations are archived later.

Output:
    data/raw/11_gauges/cwc/<station_code>_hhs.csv      -- full level series
    data/raw/11_gauges/cwc/<station_code>_static.json  -- danger/warning etc.

Verified 2026-08-28: both pilot stations return real, live-updating data with
no pagination needed (full history in one response), but NEITHER has a
published danger/warning threshold yet (both fields are null) — confirms
docs/design/PILOT_TAWANG.md and FLOOD_WHEN_PILOT_PLAN.md §1. The pilot plan's
percentile-proxy label is therefore required, not optional, until CWC answers
that ask.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import requests

from common import GAUGES, UA, record

BASE = "https://ffs.india-water.gov.in/iam/api"
OUT = GAUGES / "cwc"

# name -> CWC station code. Add more here (or via --station) as the rollout
# in FLOOD_WHEN_PILOT_PLAN.md §8 proceeds — nothing else in this file changes.
STATIONS = {
    "murga_bridge": "002Neid3",
    "rho_basti": "001NEID3",
}


def _get_spec(path: str, spec: dict) -> list | dict:
    r = requests.get(f"{BASE}/{path}/specification/",
                      params={"specification": json.dumps(spec)},
                      headers=UA, timeout=120)
    r.raise_for_status()
    return r.json()


def fetch_level_series(station_code: str) -> pd.DataFrame:
    """Full history of the HHS (water level, staff gauge) datatype."""
    spec = {
        "where": {"expression": {"fieldName": "id.stationCode",
                                  "operator": "eq", "value": station_code}},
        "and": {"expression": {"fieldName": "id.datatypeCode",
                                "operator": "eq", "value": "HHS"}},
    }
    rows = _get_spec("new-entry-data", spec)
    if not rows:
        return pd.DataFrame(columns=["datetime", "level", "station_code"])
    df = pd.DataFrame({
        "datetime": [r["id"]["dataTime"] for r in rows],
        "level": [r["dataValue"] for r in rows],
        "station_code": station_code,
    })
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.sort_values("datetime").reset_index(drop=True)


def fetch_static(station_code: str) -> dict:
    """Danger/warning levels and station metadata, if published."""
    spec = {"expression": {"fieldName": "stationCode",
                            "operator": "eq", "value": station_code}}
    rows = _get_spec("flood-forecast-static", spec)
    return rows[0] if rows else {}


def fetch_station(name: str, code: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"  {name} ({code})")

    df = fetch_level_series(code)
    csv_path = OUT / f"{code}_hhs.csv"
    df.to_csv(csv_path, index=False)
    if len(df):
        print(f"    [ok]   {len(df):,} readings, "
              f"{df['datetime'].min():%Y-%m-%d} -> {df['datetime'].max():%Y-%m-%d}")
    else:
        print("    [warn] no HHS readings returned")

    static = fetch_static(code)
    json_path = OUT / f"{code}_static.json"
    json_path.write_text(json.dumps(static, indent=2))
    dl, wl = static.get("dangerLevel"), static.get("warningLevel")
    if dl is None and wl is None:
        print("    [warn] no danger/warning threshold published — "
              "pipeline falls back to the percentile proxy (see plan §1)")
    else:
        print(f"    [ok]   warning={wl}  danger={dl}")

    record(OUT, source=f"CWC FFS ({name})",
           url=f"{BASE}/new-entry-data/specification/?stationCode={code}",
           files=[csv_path, json_path],
           license_="open, no login (ffs.india-water.gov.in)",
           notes="HHS water-level series + flood-forecast-static thresholds")


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--station", action="append", default=[],
                    metavar="NAME:CODE",
                    help="fetch one extra station beyond the STATIONS registry")
    args = p.parse_args()

    stations = dict(STATIONS)
    for spec in args.station:
        name, _, code = spec.partition(":")
        stations[name] = code

    print(f"CWC FFS gauge archive — {len(stations)} station(s)")
    for name, code in stations.items():
        fetch_station(name, code)
    print("\ndone.")


if __name__ == "__main__":
    main()
