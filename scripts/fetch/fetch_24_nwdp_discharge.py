"""14 smaller NWDP rivers — the WHEN/WHERE rollout's planned second pass,
after the 17 CWC stations (see docs/design/FLOOD_WHEN_PILOT_PLAN.md §8).

`nwdp.nwic.gov.in` (NWIC, sister body to CWC) is a standard CKAN open-data
site — documented, no key, no login. Bulk CSV dump confirmed working.
License: `other-open`, explicitly for "hydrological analysis, flood
forecasting, and water resource management." See
docs/data_research/DATA_VERIFICATION.md Section C, Finding 12 — this
script executes the archival step that finding already flagged as next.

Two Arunachal resources on the same dataset (`river-discharge-telemetry-
hourly-central-water-commission-cwc`):
    9c755c40-389e-4f5d-92c6-b936d28e51b3  historical, 2023 -> Sept 2025
    9a7feb81-191e-45df-b808-cd9523a97356  current telemetry, Jan 2026 on

⚠️ At least 2 of the 14 stations have visibly wrong government-supplied
coordinates (Changlang's sits in Kashmir, Ziro's in Uttarakhand) — this
script reports each station's raw coordinate and flags any that fall
outside a generous Arunachal bounding box, so they can be corrected by hand
(geocoded from station name + district) before use, rather than trusted
blindly.

Output:
    data/raw/11_gauges/nwdp/<resource_id>.csv    -- raw dump, unmodified
    data/interim/flood_when/nwdp_stations.json   -- per-station summary:
        name, district, reported lat/lon, row count, date range, flag
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import requests

from common import GAUGES, INTERIM, UA

OUT = GAUGES / "nwdp"
INTERIM_OUT = INTERIM / "flood_when"

RESOURCES = {
    "historical": "9c755c40-389e-4f5d-92c6-b936d28e51b3",
    "current": "9a7feb81-191e-45df-b808-cd9523a97356",
}
DUMP_URL = "https://nwdp.nwic.gov.in/datastore/dump/{resource_id}"

# Generous Arunachal bounding box (same spirit as scripts/common.py's AOI_BBOX,
# widened slightly since these are raw government coordinates being checked).
AP_BOUNDS = (91.0, 26.3, 97.6, 29.7)   # (west, south, east, north)


def fetch_resource(name: str, resource_id: str) -> pd.DataFrame:
    dest = OUT / f"{resource_id}.csv"
    if dest.exists() and dest.stat().st_size > 1e6:
        print(f"  [skip] {name} ({resource_id}) already on disk")
        return pd.read_csv(dest)
    print(f"  downloading {name} ({resource_id})...")
    r = requests.get(DUMP_URL.format(resource_id=resource_id), headers=UA, timeout=300)
    r.raise_for_status()
    OUT.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(r.content)
    df = pd.read_csv(dest)
    print(f"  [ok]   {len(df):,} rows -> {dest}")
    return df


def main() -> None:
    print("NWDP small-river discharge archive — 14 Arunachal stations\n")
    dfs = [fetch_resource(name, rid) for name, rid in RESOURCES.items()]
    df = pd.concat(dfs, ignore_index=True)
    print(f"\n{len(df):,} total rows across both resources")

    df["lat"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["lon"] = pd.to_numeric(df["Longitude"], errors="coerce")
    df["ts"] = pd.to_datetime(df["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    disch_col = "Telemetry Hourly River Water Discharge (m3/sec)"
    df["discharge"] = pd.to_numeric(df[disch_col], errors="coerce")

    stations = {}
    for name, g in df.groupby("Station"):
        lat, lon = g["lat"].iloc[0], g["lon"].iloc[0]
        w, s, e, n = AP_BOUNDS
        flagged = not (w <= lon <= e and s <= lat <= n)
        stations[name] = {
            "name": name,
            "district": g["District"].iloc[0],
            "lat_reported": round(float(lat), 6) if pd.notna(lat) else None,
            "lon_reported": round(float(lon), 6) if pd.notna(lon) else None,
            "coord_flagged_bad": flagged,
            "n_rows": int(len(g)),
            "date_range": [str(g["ts"].min()), str(g["ts"].max())] if g["ts"].notna().any() else None,
            "discharge_range_m3s": [round(float(g["discharge"].min()), 2),
                                     round(float(g["discharge"].max()), 2)],
        }
        flag = "  [FLAGGED: coord looks wrong, geocode by name/district before using]" if flagged else ""
        line = (f"  {name:<20} {str(g['District'].iloc[0]):<15} {len(g):>7,} rows  "
                f"lat={lat:.3f} lon={lon:.3f}{flag}")
        print(line.encode("ascii", "replace").decode("ascii"))

    INTERIM_OUT.mkdir(parents=True, exist_ok=True)
    out = INTERIM_OUT / "nwdp_stations.json"
    out.write_text(json.dumps(stations, indent=2))
    print(f"\nwrote {out}  ({len(stations)} stations)")
    print(f"flagged (bad coordinate): {sum(1 for s in stations.values() if s['coord_flagged_bad'])}")


if __name__ == "__main__":
    main()
