"""A Sentinel-1 flood-water test that can say "no" — validated, then run on every record.

    python scripts/fetch/radar_water_test.py validate   # the pre-registered test (PARKED §0x)
    python scripts/fetch/radar_water_test.py recheck    # every screened candidate (resumable)

Writes  reports/flood_radar_test_validation.json
        data/interim/flood_where/radar_recheck.jsonl   (one line per candidate, appended)
        reports/flood_radar_recheck.json               (summary + the supported record list)

════════════════════════════════════════════════════════════════════════════
WHY A NEW TEST
════════════════════════════════════════════════════════════════════════════
fetch_32's screen compared ONE flood-day image with ONE dry-season image and
called a place flooded if more than 0.3% of everything within ~17 km read as
new water. Tested on flood-free dates it said "flood" 97-100% of the time
(check_s1_screen_specificity.py, PARKED §0w): single-image radar speckle,
wet fields, shadows on hillsides and shifting river channels already give
2-3% "new water" on an ordinary day.

THIS TEST, for one place and date
    flood image   the Sentinel-1 VV pass nearest the date, within +-3 days,
                  smoothed (50 m median) to take the speckle out
    reference     the median of up to 15 dry-season (Dec-Mar) passes of the
                  SAME track within two years — "normal", not one image
    where         only low, flat ground that is normally dry: MERIT height
                  above nearest drainage < 15 m, slope < 5 deg, JRC permanent-
                  water occurrence < 50%, within 10 km
    new water     a 30 m pixel that reads as water on the date (< -18 dB),
                  did not in the reference (>= -18 dB), and darkened by > 3 dB
    measured      the share of that ground that became new water

Whether it can tell floods from quiet days is not assumed: `validate` runs
the pre-registered test in PARKED §0x first.
"""
from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

EE_PROJECT = "earthengine-507510"
PAD_DAYS = 3
RADIUS_M = 10_000
WATER_DB = -18.0
DROP_DB = 3.0
HAND_MAX_M = 15
SLOPE_MAX_DEG = 5
PERM_MAX = 50
N_REFS = 15
MIN_REFS = 3
SCALE_M = 30
KM = 111.2
VALIDATION = ROOT / "reports" / "flood_radar_test_validation.json"          # attempt 2
VALIDATION_1 = ROOT / "reports" / "flood_radar_test_validation_attempt1.json"
RECHECK_LINES = ROOT / "data" / "interim" / "flood_where" / "radar_recheck.jsonl"
RECHECK = ROOT / "reports" / "flood_radar_recheck.json"
SCREENS = ["flood_where_groundsource_s1_ee_screen.json",
           "flood_where_groundsource_pre2019_s1_ee_screen.json",
           "flood_where_groundsource_widewindow_recheck.json"]

_static = {}


def _ee():
    import ee
    if not _static:
        ee.Initialize(project=EE_PROJECT)
        hand = ee.Image("MERIT/Hydro/v1_0_1").select("hnd").lt(HAND_MAX_M)
        slope = ee.Terrain.slope(ee.Image("USGS/SRTMGL1_003")).lt(SLOPE_MAX_DEG)
        perm = (ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
                .unmask(0).lt(PERM_MAX))
        _static["low"] = hand.And(slope).And(perm)
    return ee


def test_one(lat: float, lon: float, day: str) -> dict:
    """The test for one place and date. Returns what it found, or why not."""
    ee = _ee()
    pt = ee.Geometry.Point([lon, lat])
    region = pt.buffer(RADIUS_M)
    d = dt.date.fromisoformat(day)
    base = (ee.ImageCollection("COPERNICUS/S1_GRD").filterBounds(pt)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")))
    col = base.filterDate(str(d - dt.timedelta(days=PAD_DAYS)),
                          str(d + dt.timedelta(days=PAD_DAYS + 1)))
    times = col.aggregate_array("system:time_start").getInfo()
    if not times:
        return {"image": False}
    ids = col.aggregate_array("system:index").getInfo()
    target = dt.datetime.combine(d, dt.time()).timestamp() * 1000
    best = min(range(len(times)), key=lambda i: (abs(times[i] - target), ids[i]))
    img = ee.Image(col.filter(ee.Filter.eq("system:index", ids[best])).first())
    orbit = int(img.get("relativeOrbitNumber_start").getInfo())
    refs = (base.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
            .filterDate(str(d - dt.timedelta(days=730)), str(d + dt.timedelta(days=730)))
            .filter(ee.Filter.calendarRange(12, 3, "month"))
            .sort("system:time_start").limit(N_REFS))
    n_refs = int(refs.size().getInfo())
    if n_refs < MIN_REFS:
        return {"image": True, "orbit": orbit, "n_refs": n_refs, "reference": False}
    ref = refs.select("VV").median()
    # attempt 2 (PARKED §0x): an ordinary day of the SAME season too — the
    # dry-season reference alone read a normal wet monsoon day as new water
    doy = int(d.strftime("%j"))
    season = (base.filter(ee.Filter.eq("relativeOrbitNumber_start", orbit))
              .filterDate(f"{d.year - 3}-01-01", f"{d.year + 4}-01-01")
              .filter(ee.Filter.calendarRange(d.year, d.year, "year").Not())
              .filter(ee.Filter.dayOfYear(max(1, doy - 30), min(366, doy + 30)))
              .sort("system:time_start").limit(N_REFS))
    n_season = int(season.size().getInfo())
    if n_season < MIN_REFS:
        return {"image": True, "orbit": orbit, "n_refs": n_refs, "n_season_refs": n_season,
                "reference": False}
    sref = season.select("VV").median()
    fl = img.select("VV").focal_median(50, "circle", "meters")
    low = _static["low"]
    new = (fl.lt(WATER_DB).And(ref.gte(WATER_DB)).And(sref.gte(WATER_DB))
           .And(fl.subtract(sref).lt(-DROP_DB)).And(low))
    area = ee.Image.pixelArea()
    stats = (ee.Image.cat([new.multiply(area).rename("new"),
                           low.And(fl.mask()).multiply(area).rename("low")])
             .reduceRegion(reducer=ee.Reducer.sum(), geometry=region, scale=SCALE_M,
                           maxPixels=1e9, tileScale=4).getInfo())
    low_km2 = (stats.get("low") or 0) / 1e6
    new_km2 = (stats.get("new") or 0) / 1e6
    return {"image": True, "orbit": orbit, "n_refs": n_refs, "n_season_refs": n_season,
            "reference": True,
            "scene_date": dt.datetime.utcfromtimestamp(times[best] / 1000).date().isoformat(),
            "low_km2": round(low_km2, 3), "new_km2": round(new_km2, 4),
            "new_share": round(new_km2 / low_km2, 5) if low_km2 > 0 else None}


def _run(tasks: list[tuple], workers: int = 6, timeout: int = 180, on_done=None) -> list[dict]:
    """tasks: (key, lat, lon, day). Parallel, with a per-task timeout."""
    out = []
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(test_one, la, lo, dy): (k, la, lo, dy) for k, la, lo, dy in tasks}
        for f in cf.as_completed(futs):
            k, la, lo, dy = futs[f]
            try:
                r = f.result(timeout=timeout)
            except Exception as e:                                  # noqa: BLE001
                r = {"error": type(e).__name__}
            row = {"key": k, "lat": la, "lon": lo, "date": dy, **r}
            out.append(row)
            if on_done:
                on_done(row)
    return out


def _records():
    """Every candidate the screens looked at (uuid, date, lat, lon), and the
    positive ones (the flood records)."""
    seen, allc = set(), []
    for name in SCREENS:
        d = json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))
        for r in d["results"]:
            if r["uuid"] in seen:
                continue
            seen.add(r["uuid"])
            allc.append({"uuid": r["uuid"], "date": r["date_str"], "lat": r["lat"],
                         "lon": r["lon"], "screen_positive": bool(r.get("screen_positive"))})
    return allc


# ── validation (PARKED §0x, pre-registered) ───────────────────────────────
def validate(n: int = 80, seed: int = 7) -> dict:
    """Attempt 2 (PARKED §0x): a FRESH sample — seed 7, drawn from the records
    attempt 1 (seed 42) did not use."""
    import pandas as pd
    t0 = time.time()
    allc = pd.DataFrame(_records())
    allc["d"] = pd.to_datetime(allc["date"])
    pool = allc[allc["screen_positive"] & (allc["d"] >= "2016-01-01")
                & (allc["d"] <= "2025-06-30")]
    used = set(pool.sample(80, random_state=42)["uuid"])       # attempt 1's sample
    pos = pool[~pool["uuid"].isin(used)].sample(n, random_state=seed).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    half = np.where(rng.permutation(n) < n // 2, "A", "B")

    def clear(lat, lon, d):
        near = allc[abs(allc["d"] - d) <= pd.Timedelta(days=30)]
        dist = KM * np.hypot(near["lat"] - lat, (near["lon"] - lon) * np.cos(np.radians(lat)))
        return not (dist <= 20).any()

    tasks, meta = [], {}
    for i, e in pos.iterrows():
        d = e["d"]
        dates = [("flood", d)]
        s = next((c for c in (d + pd.DateOffset(years=1), d - pd.DateOffset(years=1))
                  if c <= pd.Timestamp("2025-10-31") and clear(e["lat"], e["lon"], c)), None)
        if s is not None:
            dates.append(("season control", s))
        j = pd.Timestamp(dt.date(d.year, 1, 15))
        if clear(e["lat"], e["lon"], j):
            dates.append(("dry control", j))
        for kind, day in dates:
            key = f"{i}|{kind}"
            meta[key] = {"record": i, "kind": kind, "half": half[i]}
            tasks.append((key, float(e["lat"]), float(e["lon"]), str(day.date())))
    print(f"  {len(tasks)} tests for {n} records ({time.time()-t0:.0f}s)", flush=True)
    done = [0]

    def tick(_row):
        done[0] += 1
        if done[0] % 20 == 0:
            print(f"    {done[0]}/{len(tasks)}  ({time.time()-t0:.0f}s)", flush=True)

    rows = _run(tasks, on_done=tick)
    df = pd.DataFrame([{**r, **meta[r["key"]]} for r in rows])
    ok = df["new_share"].notna()
    ctrl = ok & df["kind"].str.contains("control")
    fl = ok & (df["kind"] == "flood")
    thr = float(np.percentile(df.loc[ctrl & (df["half"] == "A"), "new_share"], 97.5))
    b_ctrl = df.loc[ctrl & (df["half"] == "B"), "new_share"]
    b_fl = df.loc[fl & (df["half"] == "B"), "new_share"]
    spec = float((b_ctrl <= thr).mean())
    ctrl_rate = float((b_ctrl > thr).mean())
    fl_rate = float((b_fl > thr).mean())
    passed = bool(spec >= 0.90 and fl_rate >= 3 * max(ctrl_rate, 1e-9) and fl_rate > 0)
    by_kind = {k: {"n": int(len(g)), "median_share_pct": round(100 * float(g["new_share"].median()), 3),
                   "p95_share_pct": round(100 * float(g["new_share"].quantile(0.95)), 3),
                   "zero_share": round(float((g["new_share"] == 0).mean()), 3)}
               for k, g in df[ok].groupby("kind")}
    out = {"what": "the new radar water test on 80 records and flood-free controls, "
                   "pre-registered in PARKED §0x",
           "n_tests": int(len(df)), "n_measured": int(ok.sum()),
           "not_measured": df.loc[~ok, ["kind"]].assign(
               why=df.loc[~ok].apply(lambda r: "no pass within 3 days" if r.get("image") is False
                                     else ("too few dry references" if r.get("reference") is False
                                           else r.get("error", "no low ground")), axis=1)
           )["why"].value_counts().to_dict(),
           "threshold_share_pct_from_half_A": round(100 * thr, 4),
           "half_B": {"control_dates": int(len(b_ctrl)), "specificity": round(spec, 3),
                      "controls_above": round(ctrl_rate, 3), "flood_dates": int(len(b_fl)),
                      "flood_dates_above": round(fl_rate, 3)},
           "by_kind": by_kind, "PASS": passed,
           "rows": df.to_dict("records")}
    VALIDATION.write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    return out


# ── the re-check of every record ──────────────────────────────────────────
def recheck() -> dict:
    v = json.loads(VALIDATION.read_text())
    if not v["PASS"]:
        raise SystemExit("The new test did not pass its validation — not re-checking with it.")
    thr = v["threshold_share_pct_from_half_A"] / 100
    allc = _records()
    RECHECK_LINES.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if RECHECK_LINES.exists():
        for line in RECHECK_LINES.read_text(encoding="utf-8").splitlines():
            done.add(json.loads(line)["key"])
    tasks = [(c["uuid"], float(c["lat"]), float(c["lon"]), c["date"]) for c in allc
             if c["uuid"] not in done]
    print(f"  {len(allc):,} candidates, {len(done):,} already checked, {len(tasks):,} to go",
          flush=True)
    t0, n = time.time(), [0]
    fh = RECHECK_LINES.open("a", encoding="utf-8")

    def save(row):
        fh.write(json.dumps(row, default=str) + "\n")
        fh.flush()
        n[0] += 1
        if n[0] % 100 == 0:
            rate = n[0] / (time.time() - t0)
            print(f"    {n[0]:,}/{len(tasks):,}  ({rate*60:.0f}/min)", flush=True)

    _run(tasks, workers=8, on_done=save)
    fh.close()
    return summarize(thr)


def summarize(thr: float | None = None) -> dict:
    if thr is None:
        thr = json.loads(VALIDATION.read_text())["threshold_share_pct_from_half_A"] / 100
    rows = [json.loads(x) for x in RECHECK_LINES.read_text(encoding="utf-8").splitlines()]
    cand = {c["uuid"]: c for c in _records()}
    status = {}
    for r in rows:
        if r.get("new_share") is None:
            s = ("no radar pass within 3 days" if r.get("image") is False else
                 "too few dry references" if r.get("reference") is False else
                 "error" if "error" in r else "no low ground")
        else:
            s = "radar supports" if r["new_share"] > thr else "radar does not show it"
        status[r["key"]] = s
    pos = [u for u, c in cand.items() if c["screen_positive"]]
    tally = lambda keys: {s: sum(1 for k in keys if status.get(k) == s)
                          for s in sorted(set(status.values()))}
    out = {"threshold_share_pct": round(100 * thr, 4),
           "checked": len(status),
           "all_candidates": tally(list(cand)),
           "old_screen_positive_records": tally(pos),
           "supported_uuids": sorted(k for k, s in status.items() if s == "radar supports")}
    RECHECK.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "supported_uuids"}, indent=2))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "validate"
    {"validate": validate, "recheck": recheck, "summarize": summarize}[cmd]()
