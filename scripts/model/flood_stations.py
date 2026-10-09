"""The canonical flood-WHEN gauge registry — one shared source of truth for
every station's real coordinates, catchment area and danger level, used by
both backtest_flood_when.py (Phase 1) and train_flood_when.py (Phase 2).

Rollout, 2026-08-30 (docs/design/FLOOD_WHEN_PILOT_PLAN.md §8): grew from the
3-station Tawang pilot (2 Tawang gauges + Passighat, approximated to a
shared "Jang town" proxy location for the 2 Tawang gauges, since the API
itself returns null lat/lon on the main station record) to all **18** CWC
stations found tagged or physically located in Arunachal Pradesh, spanning
the whole state — Kibithu (97.03°E, near the China border) to Bhalukpong
(92.64°E, near Assam) — with **real per-station coordinates**, not a shared
proxy, sourced from the `layer-station-geo` endpoint (a separate table from
the main station record, undocumented until found this session — the main
endpoint returns null lat/lon for every station, `layer-station-geo` has
real values for all 18). This also fixes the 2 Tawang gauges' own location
to their real coordinates instead of the Jang-proxy approximation.

Catchment area: `layer-station`, per station (its bulk/list query 500s —
call it one station at a time, as done here). 13 of 18 stations have a
published CWC danger level; the other 5 fall back to the self-derived
percentile method (see backtest_flood_when.py's module docstring for why
that's the standing method, not a stopgap).

    python scripts/model/flood_stations.py     # re-fetch and print the
                                                  registry from the live API
"""
from __future__ import annotations

# code -> real name, real lat/lon (layer-station-geo), real catchment area
# km^2 (layer-station, None if not published), real CWC danger level (m,
# None if not published -> self-derived percentile label used instead).
STATIONS = {
    "001-UBDDIB": {"name": "Kibithu", "lat": 28.257222, "lon": 97.025833,
                   "catchment_km2": 12949.0, "danger_level": 1229.25},
    "001NEID3": {"name": "Rho Basti", "lat": 27.622778, "lon": 92.013611,
                 "catchment_km2": 1992.0, "danger_level": None},
    "002-ubddib": {"name": "Tuting", "lat": 28.995, "lon": 94.886944,
                   "catchment_km2": 243264.0, "danger_level": 441.0},
    "002Neid3": {"name": "Murga Bridge", "lat": 27.613889, "lon": 92.026389,
                 "catchment_km2": None, "danger_level": None},
    "003-UBDDIB": {"name": "Yinkiang", "lat": 28.643611, "lon": 95.016944,
                   "catchment_km2": None, "danger_level": None},
    "003NEID-3": {"name": "Pangin", "lat": 28.233611, "lon": 95.002778,
                  "catchment_km2": 254697.0, "danger_level": 220.0},
    "004-UBDDIB": {"name": "Lemeking", "lat": 28.372778, "lon": 93.559722,
                   "catchment_km2": 11318.0, "danger_level": 1109.745},
    "005-UBDDIB": {"name": "Passighat", "lat": 28.077778, "lon": 95.335556,
                   "catchment_km2": 256572.0, "danger_level": 153.96},
    "007NEID3": {"name": "Jollang", "lat": 27.073333, "lon": 93.615,
                 "catchment_km2": None, "danger_level": None},
    "008-ubddib": {"name": "Miao", "lat": 27.493611, "lon": 96.219167,
                   "catchment_km2": 2443.0, "danger_level": 239.9},
    "009-UBDDIB": {"name": "Namsai", "lat": 27.635556, "lon": 95.848056,
                   "catchment_km2": 2664.0, "danger_level": 145.8},
    "020-UBDDIB": {"name": "Daporizo", "lat": 27.993333, "lon": 94.223333,
                   "catchment_km2": 15104.0, "danger_level": 209.55},
    "027-UBDDIB": {"name": "Seppa", "lat": 27.356944, "lon": 93.038611,
                   "catchment_km2": 3629.0, "danger_level": 340.0},
    "029-UBDDIB": {"name": "Bhalukpong", "lat": 27.016389, "lon": 92.642222,
                   "catchment_km2": 8966.0, "danger_level": 140.0},
    "058-UBDDIB": {"name": "Doimukh", "lat": 27.138333, "lon": 93.751944,
                   "catchment_km2": 1210.0, "danger_level": 123.5},
    "059-UBDDIB": {"name": "Pagoda", "lat": 27.773333, "lon": 95.975833,
                   "catchment_km2": 176.0, "danger_level": 147.26},
    "070-UBDDIB": {"name": "Tamen", "lat": 27.76, "lon": 94.008889,
                   "catchment_km2": 7569.0, "danger_level": 283.0},
    "078-UBDDIB": {"name": "Pare HEP", "lat": 27.236944, "lon": 93.815556,
                   "catchment_km2": 824.0, "danger_level": None},
}


def refresh_from_api() -> dict:
    """Re-derive STATIONS from the live CWC FFS API, for re-running when the
    rollout grows further (more states, revisit if a station's metadata
    changes). Not called automatically — STATIONS above is the pinned,
    checked-in version."""
    import json
    import requests

    base = "https://ffs.india-water.gov.in/iam/api"
    spec = {"expression": {"fieldName": "meteorologicalSubDivision",
                            "operator": "eq", "value": "Arunachal Pradesh"}}
    r = requests.get(f"{base}/flood-forecast-static/specification/",
                      params={"specification": json.dumps(spec)}, timeout=60)
    r.raise_for_status()
    codes = sorted({s["stationCode"] for s in r.json()} | {"001NEID3"})
    thresh = {s["stationCode"]: s for s in r.json()}

    out = {}
    for code in codes:
        spec = {"expression": {"fieldName": "stationCode", "operator": "eq", "value": code}}
        geo_r = requests.get(f"{base}/layer-station-geo/specification/",
                              params={"specification": json.dumps(spec)}, timeout=30)
        cat_r = requests.get(f"{base}/layer-station/specification/",
                              params={"specification": json.dumps(spec)}, timeout=30)
        geo = geo_r.json()[0] if geo_r.ok and geo_r.json() else {}
        cat = cat_r.json()[0] if cat_r.ok and cat_r.json() else {}
        out[code] = {
            "name": geo.get("name") or code,
            "lat": geo.get("lat"), "lon": geo.get("lon"),
            "catchment_km2": cat.get("catchmentArea"),
            "danger_level": thresh.get(code, {}).get("dangerLevel"),
        }
    return out


if __name__ == "__main__":
    fresh = refresh_from_api()
    for code, meta in fresh.items():
        pinned = STATIONS.get(code)
        flag = "" if pinned == meta else "  ⚠️ differs from pinned STATIONS"
        print(f"  {code:>12}  {meta}{flag}")
