"""Sources checked and ready to pull, but not pulled yet.

    python scripts/fetch/ready_sources.py

Each entry is checked live before it is listed: a web address must answer, an
Earth Engine dataset must exist in the catalogue. The result goes to
data/raw/_READY.json, which the backbone bundle shows beside the sources we
hold, marked "ready, not pulled". Nothing is downloaded here.

To pull one later, run its fetcher where there is one (the "fetcher" field),
or write one in the usual way: untouched copy in the raw store, record() it.
An entry whose check fails is left out of the file and printed, so the list
never claims a source that has gone away.

Left out on purpose: ReliefWeb (its API now needs an approved app name; ask
first), ICIMOD's glacial lakes and Copernicus Global Flood Monitoring (free
accounts needed), and anything licensed for non-commercial use only that
we do not already read (the Global Flood Database is NC, and already in use).
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ee
import requests

from common import RAW, UA

PROJECT = "earthengine-507510"
OUT = RAW / "_READY.json"

# (group folder, source, how to check, address, licence, why we'd want it, fetcher)
# how: "ee" = Earth Engine dataset id; "get" = the address must answer 200;
#      "post:<field>=<value>" = a form post must answer 200 with data.
READY = [
    ("06_weather", "IMD gridded daily rainfall 0.25 deg (Pai et al. 2014)",
     "post:rain=2024", "https://www.imdpune.gov.in/cmpg/Griddata/rainfall.php",
     "No licence on the download page; IMD's data policy applies",
     "India's official gauge-based rain grid: a second rain ruler.",
     "scripts/fetch/fetch_59_imd_rain.py"),
    ("06_weather", "CHIRPS v2.0 daily rainfall (UCSB Climate Hazards Center)",
     "ee", "UCSB-CHG/CHIRPS/DAILY", "Free and open; cite Funk et al. 2015",
     "A third independent rain history, 5.5 km, 1981-now. 1981-1986 already on disk.",
     "scripts/fetch/fetch_60_chirps_rain.py"),
    ("06_weather", "GSMaP near-real-time rain (JAXA)",
     "ee", "JAXA/GPM_L3/GSMaP/v8/operational", "Free with attribution (JAXA)",
     "A second live rain feed, hourly, in case Open-Meteo goes down.", ""),
    ("06_weather", "NASA NEX-GDDP-CMIP6 climate projections",
     "ee", "NASA/GDDP-CMIP6", "Free and open (NASA)",
     "Daily rain to 2100 under climate scenarios: how the monsoon may change.", ""),
    ("06_weather", "NOAA Global Summary of the Day (weather stations)",
     "get", "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2024/",
     "Free and open (NOAA)", "Measured daily rain and temperature at airport and city stations.", ""),
    ("02_terrain", "NASADEM (NASA/USGS, from SRTM 2000)",
     "ee", "NASA/NASADEM_HGT/001", "Public domain (NASA/USGS)",
     "Second 30 m elevation model to cross-check ours. 5 of 28 tiles already on disk.",
     "scripts/fetch/fetch_61_dem_crosscheck.py"),
    ("02_terrain", "ALOS World 3D 30 m v4.1 (JAXA)",
     "ee", "JAXA/ALOS/AW3D30/V4_1", "Free with attribution (c) JAXA; JAXA terms apply",
     "Third 30 m elevation model, from optical stereo: catches radar shadow in deep valleys.",
     "scripts/fetch/fetch_61_dem_crosscheck.py"),
    ("03_soil_geology", "SMAP L4 soil moisture, 3-hourly 9 km (NASA)",
     "ee", "NASA/SMAP/SPL4SMGP/008", "Free and open (NASA)",
     "Root-zone soil wetness, modelled: deeper than the surface reading we hold.", ""),
    ("04_landcover", "Dynamic World 10 m land cover, every scene (Google/WRI)",
     "ee", "GOOGLE/DYNAMICWORLD/V1", "CC-BY 4.0",
     "Land cover that updates with every satellite pass: spots ground that has changed since 2021.", ""),
    ("04_landcover", "MODIS yearly land cover 500 m, 2001-now (MCD12Q1)",
     "ee", "MODIS/061/MCD12Q1", "Free and open (NASA)",
     "Twenty years of land cover: where forest became farm or town.", ""),
    ("04_landcover", "MODIS daily snow cover 500 m (MOD10A1)",
     "ee", "MODIS/061/MOD10A1", "Free and open (NASA/NSIDC)",
     "Snow and its melt, for melt-fed river floods.", ""),
    ("04_landcover", "NASA FIRMS active fires (MODIS/VIIRS)",
     "ee", "FIRMS", "Free and open (NASA)",
     "Every fire seen from space since 2000: the core of a forest-fire module.", ""),
    ("04_landcover", "MODIS burned area 500 m, monthly (MCD64A1)",
     "ee", "MODIS/061/MCD64A1", "Free and open (NASA)",
     "Burn scars: what burned, and slopes that lost cover before a monsoon.", ""),
    ("05_hydrology", "Global Flood Database (MODIS flood events 2000-2018)",
     "ee", "GLOBAL_FLOOD_DB/MODIS_EVENTS/V1", "CC-BY-NC 4.0 (Cloud to Street / Tellman et al. 2021)",
     "Already read live by the flood-record builder; no copy stored yet.", ""),
    ("05_hydrology", "Randolph Glacier Inventory 7.0 (NSIDC)",
     "get", "https://nsidc.org/data/nsidc-0770/versions/7", "CC-BY 4.0",
     "Glacier outlines: the start of a glacial-lake flood module.", ""),
    ("07_seismic", "USGS ShakeMap shaking footprints for past quakes",
     "get", "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&producttype=shakemap"
            "&starttime=1990-01-01&minlatitude=24&maxlatitude=30&minlongitude=89&maxlongitude=98",
     "Public domain (USGS)", "How hard the ground shook, cell by cell, for 72 quakes since 1990 "
     "in and around both states: a second landslide trigger.", ""),
    ("08_labels", "NASA Global Landslide Catalog, official copy via HDX",
     "get", "https://data.humdata.org/dataset/1eb911ba-3681-4a96-b025-ae0c33b80a12/resource/"
            "ed703c45-2001-4286-ba16-8248c17fec80/download/global_landslide_catalog_nasa.zip",
     "Public domain (NASA)", "Replaces our unofficial re-host of the same 99 Arunachal events.", ""),
    ("08_labels", "GDELT global news events",
     "get", "http://data.gdeltproject.org/gdeltv2/lastupdate.txt", "Free and open (GDELT)",
     "Every news report, located and dated, every 15 minutes: a hunting ground for dated landslides.", ""),
    ("09_exposure", "Google Open Buildings v3 (South Asia)",
     "ee", "GOOGLE/Research/open-buildings/v3/polygons", "CC-BY 4.0 and ODbL",
     "Every building outline: buildings at risk, not just people.", ""),
    ("09_exposure", "GHSL built-up surface 1975-2030 (JRC)",
     "ee", "JRC/GHSL/P2023A/GHS_BUILT_S", "CC-BY 4.0 (European Commission)",
     "How towns have grown every five years since 1975.", ""),
    ("09_exposure", "Overture Maps (places, buildings, roads)",
     "get", "https://overturemaps-us-west-2.s3.amazonaws.com/?list-type=2&prefix=release/&delimiter=/&max-keys=1",
     "CDLA-Permissive 2.0 / ODbL by theme", "A second open map to cross-check OpenStreetMap's roads and places.", ""),
]


def check(how: str, addr: str) -> tuple[bool, str]:
    try:
        if how == "ee":
            a = ee.data.getAsset(addr)
            return True, a.get("type", "asset").lower()
        if how.startswith("post:"):
            k, v = how[5:].split("=")
            r = requests.post(addr, data={k: v}, headers=UA, timeout=120, stream=True)
            ok = r.status_code == 200 and int(r.headers.get("content-length", "1") or 1) > 0
            r.close()
            return ok, f"HTTP {r.status_code}"
        r = requests.get(addr, headers=UA, timeout=60, stream=True)
        r.close()
        return 200 <= r.status_code < 300, f"HTTP {r.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]


def main() -> None:
    ee.Initialize(project=PROJECT)
    today = date.today().isoformat()
    ok_rows, bad = [], []
    for group, source, how, addr, lic, why, fetcher in READY:
        ok, detail = check(how, addr)
        print(f"  {'ok ' if ok else 'BAD'}  {source[:58]:58}  {detail}")
        row = {"group": group, "source": source,
               "url": f"Earth Engine: {addr}" if how == "ee" else addr,
               "license": lic, "notes": why, "fetcher": fetcher, "checked": today}
        (ok_rows if ok else bad).append(row)
    OUT.write_text(json.dumps(ok_rows, indent=2), encoding="utf-8")
    print(f"\n  {len(ok_rows)} ready, {len(bad)} failed the check -> {OUT}")


if __name__ == "__main__":
    main()
