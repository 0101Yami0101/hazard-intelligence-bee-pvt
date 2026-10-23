"""Rain readings at the CWC flood-forecasting stations, from ffs.india-water.gov.in.

    python scripts/fetch/fetch_48_ffs_rain.py

Why: the NWDP rain files (fetch_47) arrive 1-2 weeks late, in batches, so they
cannot feed a live forecast. The CWC flood-forecasting site, whose river levels
the gauge forecasts already read live (fetch_21), also carries a datatype
`MPS` at some stations: 3-hourly readings back to 1971, live to the same day.
That it is rain, in mm, is checked against NWDP's daily rain at the same
station by scripts/inspect/ffs_rain_check.py (docs/design/RAIN_GAUGES.md,
Part C0), not assumed.

One CSV per station that has MPS: GAUGES/cwc/{code}_mps.csv. Stations from the
pinned registry in scripts/model/flood_stations.py.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import pandas as pd
import requests

from common import GAUGES, UA, record
from flood_stations import STATIONS

BASE = "https://ffs.india-water.gov.in/iam/api"
OUT = GAUGES / "cwc"
DATATYPE = "MPS"


def fetch_mps(code: str) -> pd.DataFrame:
    spec = {"where": {"expression": {"fieldName": "id.stationCode", "operator": "eq", "value": code}},
            "and": {"expression": {"fieldName": "id.datatypeCode", "operator": "eq", "value": DATATYPE}}}
    r = requests.get(f"{BASE}/new-entry-data/specification/",
                     params={"specification": json.dumps(spec)}, headers=UA, timeout=300)
    r.raise_for_status()
    rows = r.json()
    df = pd.DataFrame({"datetime": [x["id"]["dataTime"] for x in rows],
                       "value": [x["dataValue"] for x in rows]})
    if len(df):
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)
    return df


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for code, meta in STATIONS.items():
        try:
            df = fetch_mps(code)
        except requests.RequestException as e:
            print(f"  {meta['name']:<12} {code:<11} [fail] {e}")
            continue
        if not len(df):
            print(f"  {meta['name']:<12} {code:<11} no {DATATYPE}")
            continue
        p = OUT / f"{code}_mps.csv"
        df.to_csv(p, index=False)
        files.append(p)
        print(f"  {meta['name']:<12} {code:<11} {len(df):>7,} readings  "
              f"{df.datetime.min():%Y-%m-%d} -> {df.datetime.max():%Y-%m-%d %H:%M}")
    if files:
        record(OUT, source="CWC FFS rain readings (MPS)",
               url=f"{BASE}/new-entry-data/specification/ (datatypeCode MPS)",
               files=files, license_="open, no login (ffs.india-water.gov.in)",
               notes="3-hourly; meaning checked against NWDP daily rain in ffs_rain_check.py")


if __name__ == "__main__":
    main()
