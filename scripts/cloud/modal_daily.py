"""The daily flood + landslide forecast, run in the cloud (Modal) instead of
on one PC (docs/design/PARKED_OFF_PC_DAILY_RUN.md).

Every morning at 08:30 India time this runs scripts/model/flood_forecast_live.py
exactly as the PC's scheduled task did (three tries, ten minutes apart), keeps
the forecast logs in one Modal storage volume, and publishes the web snapshot
at one fixed read-only link that the app fetches (webapp/products/flood/feed.py).

Workspace: pankajkarjay (an invited workspace, not the PC's default Modal
login). Every command names it:

    $env:MODAL_PROFILE = "pankajkarjay"
    modal run    scripts/cloud/modal_daily.py::seed            # once: logs + reports -> volume
    modal run    scripts/cloud/modal_daily.py::seed --what golden   # PC's recorded day -> volume
    modal run    scripts/cloud/modal_daily.py::golden          # same-numbers check, in the cloud
    modal run    scripts/cloud/modal_daily.py::once            # one real run now
    modal deploy scripts/cloud/modal_daily.py                  # arm 08:30 daily + the link
    modal run    scripts/cloud/modal_daily.py::pull            # cloud logs -> logs/cloud_copy/

What goes where
    code, models, the six data files   uploaded from THIS PC at each deploy —
                                       a deploy ships the PC's current copy
    records/, reports/, run logs       the volume: they grow there, one place
    web snapshot                       the volume, served by `latest`

Keys: the Earth Engine robot account's key is the Modal secret
"slopesense-ee" (EE_SERVICE_ACCOUNT_KEY). Never a file in the repo.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import modal

PROJ = Path("/proj")
# This file also runs inside the cloud container, where it sits at /root and
# has no project around it; there the project is /proj.
LOCAL = Path(__file__).resolve().parents[2] if modal.is_local() else PROJ
VOL = Path("/vol")
APP = "slopesense-daily"
FEED_LABEL = "slopesense-flood-latest"        # -> https://pankajkarjay--slopesense-flood-latest.modal.run

ATTEMPTS = 3
WAIT_MIN = 10

# The PC's own versions, so the models give the same numbers (checked with
# scripts/model/check_live_unchanged.py, not assumed).
PINS = ["numpy==2.4.6", "pandas==2.3.3", "scipy==1.18.0", "scikit-learn==1.9.0",
        "joblib==1.5.3", "threadpoolctl==3.6.0", "rasterio==1.5.0", "affine==2.4.0",
        "pyarrow==24.0.0", "requests==2.34.2", "earthengine-api==1.7.42",
        "google-api-python-client==2.200.0", "streamlit==1.60.0"]

# What the run reads besides code and models, found by tracing a real run
# (2026-10-20, file opens + rasterio + parquet).
DATA_FILES = ["data/interim/flood_forecast/imerg_index_full.tif",
              "data/interim/flood_forecast/upstream_weights.npz",
              "data/interim/rainfall/_stack_meta.json",
              "data/interim/rainfall_om/points.json",
              "data/interim/state_mask.tif",
              "data/processed/flood_where_prob_100m.tif"]
MODEL_DIRS = ["models/flood_forecast", "models/flood_when", "models/flood_when_gauge"]
STATE_DIRS = ["records", "reports"]           # live in the volume, linked into /proj
SKIP = ["**/__pycache__", "**/*.pyc"]
# numpy's names for its AVX-512 routines (the Linux build has them, the PC's
# Windows build does not); the old per-feature names are ignored
NO_AVX512 = "X86_V4 AVX512_ICL AVX512_SPR"

image = (modal.Image.debian_slim(python_version="3.12")
         .apt_install("tzdata")
         .pip_install(*PINS)
         .env({"TZ": "Asia/Kolkata",           # dates and "made at" times in India time, as on the PC
               "PYTHONUTF8": "1", "LOKY_MAX_CPU_COUNT": "2",
               # Compute the way the PC does. Modal hands out machines with
               # and without AVX-512; on those with it numpy's maths and
               # sorting routines round and break ties differently, and the
               # same-numbers check failed on exactly those (2 of 5 machines,
               # 2026-10-20). The PC has AVX2 and an OpenBLAS "Haswell" build.
               "NPY_DISABLE_CPU_FEATURES": NO_AVX512,
               "OPENBLAS_CORETYPE": "Haswell"})
         .add_local_dir(LOCAL / "scripts", "/proj/scripts", ignore=SKIP)
         .add_local_dir(LOCAL / "webapp", "/proj/webapp", ignore=SKIP))
for d in MODEL_DIRS:
    image = image.add_local_dir(LOCAL / d, f"/proj/{d}", ignore=SKIP)
for f in DATA_FILES:
    image = image.add_local_file(LOCAL / f, f"/proj/{f}")

web_image = modal.Image.debian_slim(python_version="3.12").pip_install("fastapi[standard]")

app = modal.App(APP)
vol = modal.Volume.from_name(APP, create_if_missing=True)
ee_key = modal.Secret.from_name("slopesense-ee")
# Pinned to India (Mumbai): the CWC gauge site does not answer from the US,
# Tokyo or Jakarta - every request waits out its 60 s timeout - and answers
# in about a second from Mumbai (tested 2026-10-20). Costs 1.75x the base rate.
REGION = "ap-south"
RUN = dict(image=image, volumes={"/vol": vol}, secrets=[ee_key], cpu=2.0, memory=4096,
           region=REGION)


def _say(log: Path, text: str) -> None:
    print(text, flush=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(text + "\n")


def _link_state() -> None:
    for d in STATE_DIRS:
        (VOL / d).mkdir(parents=True, exist_ok=True)
        if not (PROJ / d).exists():
            (PROJ / d).symlink_to(VOL / d)


def _forecast(log: Path) -> int:
    """One run of the daily forecast, its output appended to the day's log."""
    env = dict(os.environ, SOIL_REQUIRED="1")
    p = subprocess.Popen([sys.executable, "scripts/model/flood_forecast_live.py"], cwd=PROJ,
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    with log.open("a", encoding="utf-8") as fh:
        for line in p.stdout:
            print(line, end="", flush=True)
            fh.write(line)
    return p.wait()


def _status(**kw) -> None:
    import json
    (VOL / "status.json").write_text(json.dumps(
        {"checked_at": datetime.now().astimezone().isoformat(timespec="seconds"), **kw}, indent=1))


def _gauges_missing() -> str | None:
    """Why the run must be retried for its river gauges, or None. The run
    itself carries on without them (rain only), which on a host that cannot
    reach the gauge site would be a silent, every-day downgrade. NWDP gauges
    are often all offline even on the PC; CWC's are not."""
    import json
    snap = json.loads((PROJ / "webapp" / "assets" / "flood" / "live_forecast.json").read_text())
    cwc = [r for r in snap.get("rivers", []) if r.get("network") == "CWC"]
    if cwc and all(r.get("gauge_offline") for r in cwc):
        return f"no CWC gauge has a fresh reading ({len(cwc)} offline)"
    return None


def _daily() -> None:
    _link_state()
    logs = VOL / "logs" / "flood_forecast_daily"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{datetime.now():%Y-%m-%d}.log"
    for i in range(1, ATTEMPTS + 1):
        _say(log, f"=== attempt {i} of {ATTEMPTS}, {datetime.now():%Y-%m-%d %H:%M:%S} (Modal) ===")
        code = _forecast(log)
        why = _gauges_missing() if code == 0 else None
        if why and i < ATTEMPTS:
            _say(log, f"=== {why}: retrying ===")
            code = 2
        elif why:
            _say(log, f"=== {why}, on every try: kept as issued (rain only for those rivers) ===")
        if code == 0:
            snap = VOL / "snapshot"
            snap.mkdir(exist_ok=True)
            shutil.copy2(PROJ / "webapp" / "assets" / "flood" / "live_forecast.json",
                         snap / "live_forecast.json")
            _say(log, "=== done ===")
            _status(ok=True, attempts=i, log=log.name, warning=why)
            vol.commit()
            return
        _say(log, f"=== failed (exit {code}) ===")
        vol.commit()                                   # keep the failed attempt's log
        if i < ATTEMPTS:
            time.sleep(60 * WAIT_MIN)
    _status(ok=False, attempts=ATTEMPTS, log=log.name)
    vol.commit()
    raise RuntimeError(f"daily forecast failed {ATTEMPTS} times - see {log.name} in the volume")


# 3 tries of ~3-13 min with 10 min between: up to ~1 h; 90 min leaves room
@app.function(schedule=modal.Cron("30 8 * * *", timezone="Asia/Kolkata"), timeout=5400, **RUN)
def daily() -> None:
    """The 08:30 India-time run."""
    _daily()


@app.function(timeout=5400, **RUN)
def run_now() -> None:
    """The same run, started by hand (`once`)."""
    _daily()


def _cpu() -> str:
    """The vector instructions numpy found on this machine: sorting and sums
    can differ between machines that have AVX-512 and those that do not."""
    from numpy._core._multiarray_umath import __cpu_features__ as cf
    has = "AVX512" if "avx512f" in open("/proc/cpuinfo").read() else "no AVX512"
    used = "numpy uses it" if cf.get("AVX512_SKX") else "numpy does not use it"
    return f"{has} ({used})"


@app.function(timeout=1800, **RUN)
def golden_check(_i: int = 0) -> tuple[str, int]:
    """Replay the day recorded on the PC (check_live_unchanged.py record) on
    this machine and compare every output. Works on private copies: the live
    logs in the volume are never touched."""
    print(f"machine: {_cpu()}", flush=True)
    for d in STATE_DIRS:
        shutil.copytree(VOL / d, PROJ / d)
    gold = PROJ / "data" / "interim" / "flood_forecast" / "golden_live"
    shutil.copytree(VOL / "golden", gold)
    code = subprocess.run([sys.executable, "scripts/model/check_live_unchanged.py", "check"],
                          cwd=PROJ).returncode
    return _cpu(), code


@app.function(image=web_image, volumes={"/vol": vol})
@modal.fastapi_endpoint(method="GET", label=FEED_LABEL)
def latest():
    """The newest web snapshot, read-only. Nothing else in the volume is served."""
    from fastapi import Response
    vol.reload()
    f = VOL / "snapshot" / "live_forecast.json"
    if not f.exists():
        return Response(status_code=404)
    return Response(f.read_bytes(), media_type="application/json",
                    headers={"Cache-Control": "public, max-age=300"})


# ── run from the PC ──────────────────────────────────────────────────────────
@app.local_entrypoint()
def seed(what: str = "state", force: bool = False) -> None:
    """state: this PC's records/ and reports/ -> the volume (once; --force to redo).
    golden: the PC's recorded day for the same-numbers check -> the volume."""
    if what == "golden":
        g = LOCAL / "data" / "interim" / "flood_forecast" / "golden_live"
        with vol.batch_upload(force=True) as b:
            for n in ("inputs.pkl", "outputs.pkl", "scorecard.json"):
                b.put_file(g / n, f"/golden/{n}")
        print("uploaded the recorded day to /golden")
        return
    if not force:
        try:
            if list(vol.listdir("/records")):
                raise SystemExit("the volume already holds records/ - it is the live log now. "
                                 "Use --force only to start it over from this PC's copy.")
        except (FileNotFoundError, modal.exception.NotFoundError):
            pass          # an empty volume: nothing to protect
    with vol.batch_upload(force=True) as b:
        for d in STATE_DIRS:
            b.put_directory(LOCAL / d, f"/{d}")
    print(f"uploaded {', '.join(STATE_DIRS)} from {LOCAL}")


@app.local_entrypoint()
def golden(times: int = 1) -> None:
    """The same-numbers check, on `times` machines at once (they can differ)."""
    for cpu, code in golden_check.map(range(times)):
        print(f"{cpu}: " + ("same numbers as the PC" if code == 0 else f"check FAILED (exit {code})"))


@app.local_entrypoint()
def once() -> None:
    run_now.remote()


@app.local_entrypoint()
def pull() -> None:
    """The cloud's logs, reports and run logs -> logs/cloud_copy/ (git-ignored),
    to compare with the PC's during the side-by-side week."""
    out = LOCAL / "logs" / "cloud_copy"
    for e in vol.iterdir("/", recursive=True):
        if e.type != modal.volume.FileEntryType.FILE or e.path.lstrip("/").startswith("golden/"):
            continue
        dst = out / e.path.lstrip("/")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("wb") as fh:
            vol.read_file_into_fileobj(e.path, fh)
    print(f"cloud copy in {out}")
