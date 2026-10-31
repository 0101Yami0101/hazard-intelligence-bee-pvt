"""River colour at the CWC sediment stations from Sentinel-2, 2017-2026 (RC: our own mud record).

    $env:REGION = "assam"; python scripts/fetch/fetch_56_river_colour.py            # all years
    $env:REGION = "assam"; python scripts/fetch/fetch_56_river_colour.py --test     # 1 station, 3 months
    ... fetch_56_river_colour.py --variant ndwi --years 2018 2020   # a share, for parallel runs
    ... fetch_56_river_colour.py --submit     # queue every missing year on Copernicus and exit
                                              # (the PC can be off; re-run plain to collect)

The test was written first (EROSION_PLAN.md, "RC part 1"). Per station: a 300 m circle around
the station point. Per Sentinel-2 L2A date, on pixels that are water (NDWI > 0) and not
cloud, shadow, cirrus, saturated, snow or no data (SCL 0, 1, 3, 8, 9, 10, 11):
median B4 and B3, and the water-pixel count. The SCL-water (class 6) variant is fetched
beside it. Copernicus Data Space openEO (free account, CDSE_USERNAME / CDSE_PASSWORD).

One batch job per year, restartable: finished years are skipped.
Output: data/interim/<region>/river_colour/{stations.geojson, <variant>_<year>.json}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from common import GAUGES, INTERIM, credential, record

SED = GAUGES / "cwc_sediment"
ASSAM_FILES = ("08cf3a3a-c6e5-4c7a-871d-28861a3f8b88", "b809cd25-a40b-495c-91b3-67137963e542")
MIN_READ, SINCE, RADIUS_M = 1000, "2017-01-01", 300
YEARS = range(2017, 2027)
END = "2026-10-21"
BAD_SCL = (0, 1, 3, 8, 9, 10, 11)
OUT = INTERIM / "river_colour"
URL = "https://openeo.dataspace.copernicus.eu"
FIRST_RUN = "2026-10-27T20:10:00Z"


def stations() -> gpd.GeoDataFrame:
    d = pd.concat([pd.read_csv(SED / f"{r}.csv", dtype=str) for r in ASSAM_FILES])
    d["t"] = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    d = d[d.t >= SINCE]
    g = d.groupby("Station").agg(n=("t", "count"), lat=("Latitude", "first"), lon=("Longitude", "first"))
    g = g[g.n >= MIN_READ].reset_index()
    pts = gpd.GeoDataFrame(g, geometry=[Point(float(x), float(y)) for x, y in zip(g.lon, g.lat)], crs=4326)
    circ = pts.to_crs(32646).buffer(RADIUS_M).to_crs(4326)
    return gpd.GeoDataFrame(g[["Station", "n"]], geometry=circ, crs=4326)


def connect():
    import openeo
    c = openeo.connect(URL)
    c.authenticate_oidc_resource_owner_password_credentials(
        username=credential("CDSE_USERNAME"), password=credential("CDSE_PASSWORD"),
        client_id="cdse-public", provider_id="CDSE")
    return c


def _existing(c, title: str, variant: str, year: str):
    """A job already started for this year (several processes share the years), or None.
    The first full run used the title river_colour_<variant>_<year>; the 3-month test before it
    (created 20:08 UTC) shares the title river_colour_ndwi_2024, so only later ones count."""
    for j in c.list_jobs():
        legacy = j.get("title") == f"river_colour_{variant}_{year}" and j.get("created", "") >= FIRST_RUN
        if (j.get("title") == title or legacy) and j.get("status") in ("created", "queued", "running", "finished"):
            return c.job(j["id"])
    return None


def _wait(job) -> None:
    import time
    while (st := job.status()) in ("created", "queued", "running"):    # "created" just after start()
        time.sleep(60)
    if st != "finished":
        raise RuntimeError(f"{job.job_id}: {st}")


def run_job(c, geoms: dict, t0: str, t1: str, variant: str, out: Path, submit_only: bool = False) -> None:
    import openeo.processes as P
    s2 = c.load_collection("SENTINEL2_L2A", temporal_extent=[t0, t1], bands=["B03", "B04", "B08", "SCL"])
    scl = s2.band("SCL")
    bad = scl == BAD_SCL[0]
    for v in BAD_SCL[1:]:
        bad = bad | (scl == v)
    if variant in ("ndwi", "test"):
        b3, b8 = s2.band("B03"), s2.band("B08")
        not_water = ((b3 - b8) / (b3 + b8)) <= 0
    else:
        not_water = scl != 6
    drop = bad | not_water
    v = s2.filter_bands(["B03", "B04"]).mask(drop)
    agg = v.aggregate_spatial(geometries=geoms,
                              reducer=lambda d: P.array_create([P.median(d), P.count(d)]))
    title = f"rc_{variant}_{t0[:4]}"
    job = _existing(c, title, variant, t0[:4]) or agg.create_job(title=title, out_format="JSON")
    if job.status() == "created":
        job.start()
    if submit_only:
        return
    _wait(job)
    res = job.get_results()
    tmp = out.with_suffix(".dl")
    tmp.mkdir(parents=True, exist_ok=True)
    res.download_files(tmp)
    js = [p for p in tmp.iterdir() if p.suffix == ".json" and p.name != "job-results.json"]
    out.write_text(js[0].read_text())
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()


def main(test: bool) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g = stations()
    g.to_file(OUT / "stations.geojson", driver="GeoJSON")
    print(f"River colour — {len(g)} stations with >= {MIN_READ} readings since {SINCE}")
    c = connect()
    if test:
        gt = g.iloc[[list(g.Station).index("Pandu")]] if "Pandu" in set(g.Station) else g.iloc[:1]
        geoms = json.loads(gt.to_json())
        out = OUT / "_test.json"
        run_job(c, geoms, "2024-01-01", "2024-04-01", "test", out)
        print(out.read_text()[:1500])
        return
    geoms = json.loads(g.to_json())
    files = []
    a = sys.argv
    variants = [a[a.index("--variant") + 1]] if "--variant" in a else ["ndwi", "scl"]
    years = range(int(a[a.index("--years") + 1]), int(a[a.index("--years") + 2]) + 1) if "--years" in a else YEARS
    for variant in variants:
        for y in years:
            out = OUT / f"{variant}_{y}.json"
            if out.exists():
                files.append(out)
                continue
            t0, t1 = f"{y}-01-01", (f"{y + 1}-01-01" if y < 2026 else END)
            print(f"  {variant} {y} …", flush=True)
            run_job(c, geoms, t0, t1, variant, out, submit_only="--submit" in a)
            files.append(out)
    if "--submit" in a:
        print("  submitted; Copernicus runs them in its own queue. Re-run without --submit to collect.")
        return
    if all((OUT / f"{v}_{y}.json").exists() for v in ("ndwi", "scl") for y in YEARS):
        record(OUT, "Copernicus Data Space openEO, SENTINEL2_L2A (river colour at CWC sediment stations)", URL, files)
    print("  done")


if __name__ == "__main__":
    main("--test" in sys.argv)
