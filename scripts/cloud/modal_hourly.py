"""Every CWC gauge reading, every hour, in the cloud (Modal): saved for good,
and the last 3 days published for the app's "last 3 days" gauge graph
(scripts/model/gauge_hourly.py does the work).

Its own Modal app on purpose, beside slopesense-daily (modal_daily.py): a
deploy ships the PC's current code, and redeploying the daily app just to add
this would also ship every other change into the morning forecast. This app
touches nothing of the forecast's. It shares the daily app's storage volume,
under hourly/ only.

    $env:MODAL_PROFILE = "pankajkarjay"
    modal run    scripts/cloud/modal_hourly.py::once     # one fetch now
    modal deploy scripts/cloud/modal_hourly.py           # arm it hourly + the link

Link: https://pankajkarjay--slopesense-gauge-hourly.modal.run (read by
webapp/products/flood/hourly.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import modal

PROJ = Path("/proj")
LOCAL = Path(__file__).resolve().parents[2] if modal.is_local() else PROJ
VOL = Path("/vol")
APP = "slopesense-hourly"
LABEL = "slopesense-gauge-hourly"
STATIONS = "models/flood_when_gauge/stations.json"
# the daily app's versions (modal_daily.PINS): the same spike filter, the same numbers
PINS = ["numpy==2.4.6", "pandas==2.3.3", "scipy==1.18.0", "scikit-learn==1.9.0",
        "joblib==1.5.3", "rasterio==1.5.0", "affine==2.4.0", "pyarrow==24.0.0",
        "requests==2.34.2"]

image = (modal.Image.debian_slim(python_version="3.12")
         .apt_install("tzdata")
         .pip_install(*PINS)
         .env({"TZ": "Asia/Kolkata", "PYTHONUTF8": "1"})
         .add_local_dir(LOCAL / "scripts", "/proj/scripts",
                        ignore=["**/__pycache__", "**/*.pyc"])
         .add_local_file(LOCAL / STATIONS, f"/proj/{STATIONS}"))
web_image = modal.Image.debian_slim(python_version="3.12").pip_install("fastapi[standard]")

app = modal.App(APP)
vol = modal.Volume.from_name("slopesense-daily")      # the daily app's; hourly/ only


# Twenty past each hour (CWC posts an hour's reading a little after it), in
# India: the gauge site answers nowhere else (modal_daily.REGION). A small
# machine for a few seconds.
@app.function(schedule=modal.Cron("20 * * * *", timezone="Asia/Kolkata"), timeout=600,
              image=image, volumes={"/vol": vol}, cpu=0.25, memory=1024, region="ap-south",
              retries=1)
def hourly() -> None:
    sys.path.insert(0, str(PROJ / "scripts" / "model"))
    import gauge_hourly
    gauge_hourly.run(VOL / "hourly")
    vol.commit()


@app.function(image=web_image, volumes={"/vol": vol})
@modal.fastapi_endpoint(method="GET", label=LABEL)
def latest():
    """The last 3 days of CWC readings, read-only. Nothing else is served."""
    from fastapi import Response
    vol.reload()
    f = VOL / "hourly" / "latest.json"
    if not f.exists():
        return Response(status_code=404)
    return Response(f.read_bytes(), media_type="application/json",
                    headers={"Cache-Control": "public, max-age=300"})


@app.local_entrypoint()
def once() -> None:
    hourly.remote()
