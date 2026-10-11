"""Write down SlopeSense's forecast every day — the landslide track record.

    python scripts/model/landslide_forecast_log.py          # fetch live rain and log today's issue
    python scripts/model/landslide_forecast_log.py check    # rebuild every logged issue from its own file
    python scripts/model/landslide_forecast_log.py test     # the chain, offline (scratch output)
    python scripts/model/landslide_forecast_log.py rebuild  # rewrite both tables from the issue files

The daily flood run calls log() with the rain it has already fetched, so the
two forecasts are issued from one fetch (flood_forecast_live.run).

Writes  records/landslide_forecast/issues/<issued_on>.npz   the whole issue
        records/landslide_forecast/state.csv                 share of assessed land per class, per day
        records/landslide_forecast/districts.csv             the Forecast page's district table, per day

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
SlopeSense works its forecast out when someone opens the page and keeps
nothing. A forecast that was never written down cannot be checked later, and
that day cannot be had back (PLATFORM_ARCHITECTURE.md, "do this first").
FloodSense has logged since 2026-09-21; this is the same for landslides.

WHAT IS LOGGED — enough to rebuild any number the screens showed that day
    hazard = susceptibility (static, in the bundle) x trigger (daily, per rain point)
So an issue is the 7 days' rain and trigger at every rain point, plus the
checksums of the static files it was multiplied with. From those, the hazard
and its class at any place, road or district can be worked out again exactly
— `check` proves it on every run. The two tables are the same numbers the
Forecast and Statewide pages show, kept readable.

The numbers come from the app's own functions (core.rainfall,
products.landslide.model), never a second copy of the maths.

WHAT THIS IS NOT — yet
A grade. Grading needs dated, located landslides, and nothing feeds those in
today. This writes the forecasts down so that they can be graded when
records arrive (road-block logs, field reports, news).

⚠️ A class is a rank, not a chance. "High" is a share of land to look at
first; nothing here is a probability.

DISTRICT FIGURES — real outlines since 2026-10-10
Until then a district's figures were taken over the BOX around it, as the
page then did; a box holds large parts of the neighbours (Upper Siang: 51,317
cells in its box, 25,928 in its outline), and 14 of 18 districts read
differently. The page now reads core.grid.district_raster and so does this
log. The one issue logged before the change (2026-10-10) was rewritten with
`rebuild`, from its own file; the table as first written is kept in
records/landslide_forecast/_box_figures_until_2026-10-10/.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "webapp")]

import numpy as np
import pandas as pd

import core.rainfall as RN
import products.landslide.model as fc
from core.grid import Grid, district_raster

LOG = ROOT / "records" / "landslide_forecast"
ASSETS = ROOT / "webapp" / "assets"
STATIC = {"susceptibility": ASSETS / "landslide" / "susceptibility.npz",
          "nearest_point": ASSETS / "landslide" / "nearest_point.npz",
          "clim_quantiles": ASSETS / "base" / "clim_quantiles.npz",
          "points": ASSETS / "base" / "points.json"}
CLASSES = ("very_low", "low", "moderate", "high", "very_high")     # classify() 1..5
STATE_COLS = (["issued_on", "issued_at", "target_date", "lead_days"]
              + [f"{c}_pct" for c in CLASSES] + ["high_plus_pct", "mean_trigger", "static"])
DIST_COLS = ["issued_on", "target_date", "lead_days", "district", "high_plus_pct",
             "peak_class", "assessed_cells"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def static_id() -> dict:
    """Checksums of the static half. A logged trigger means nothing against a
    different susceptibility surface, so each issue names the one it used."""
    return {k: _sha(p) for k, p in STATIC.items()}


def load_static():
    sus = np.load(STATIC["susceptibility"])["sus"]
    near = np.load(STATIC["nearest_point"])["near"]
    qz = np.load(STATIC["clim_quantiles"])
    pts = json.loads(STATIC["points"].read_text())
    grid = Grid.from_json(json.loads((ASSETS / "base" / "grid.json").read_text()))
    districts = json.loads((ASSETS / "base" / "districts.geojson").read_text(encoding="utf-8"))
    return sus, near, {k: qz[k] for k in qz.files}, pts, grid, districts


def tables(issued: str, issued_at: str, days: list[str], trig: np.ndarray, sus, near,
           dist_ids, static: str) -> tuple[list[dict], list[dict]]:
    """The state and district rows for one issue, from the app's own maths.
    `dist_ids` = core.grid.district_raster(...): each district's real
    outline, the same raster the page reads (view.district_table)."""
    ids, names = dist_ids
    flat_ids = ids.ravel().astype(np.int64) * 6
    state, dist = [], []
    for lead, (d, t) in enumerate(zip(days, trig)):
        cl = fc.classify(fc.hazard_raster(sus, near, t))
        a = cl[cl > 0]
        share = [100 * float((a == i).mean()) if a.size else 0.0 for i in range(1, 6)]
        state.append({"issued_on": issued, "issued_at": issued_at, "target_date": d,
                      "lead_days": lead,
                      **{f"{c}_pct": round(s, 3) for c, s in zip(CLASSES, share)},
                      "high_plus_pct": round(100 * float((a >= 4).mean()) if a.size else 0.0, 3),
                      "mean_trigger": round(float(np.mean(t)), 4), "static": static})
        n = np.bincount(flat_ids + cl.ravel(), minlength=(len(names) + 1) * 6).reshape(-1, 6)
        for k, name in enumerate(names, start=1):
            c = n[k, 1:]
            tot = int(c.sum())
            if tot:
                dist.append({"issued_on": issued, "target_date": d, "lead_days": lead,
                             "district": name,
                             "high_plus_pct": round(100 * float(c[3] + c[4]) / tot, 1),
                             "peak_class": CLASSES[int(np.nonzero(c)[0].max())],
                             "assessed_cells": tot})
    return state, dist


def _replace(path: Path, rows: list[dict], cols: list[str], issued: str) -> None:
    """A second run on the same day replaces that day's issue (as the flood
    log does); every other day's rows are left exactly as they are."""
    new = pd.DataFrame(rows, columns=cols).astype(str)
    if path.exists():
        old = pd.read_csv(path, dtype=str)
        new = pd.concat([old[old["issued_on"] != issued], new], ignore_index=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(path, index=False)


def log(days, rain: np.ndarray, issued_at: datetime | None = None, out: Path = LOG) -> dict:
    """Log one issue from daily rain per point, as fetch_rain returns it."""
    issued_at = issued_at or datetime.now().astimezone()
    issued = str(issued_at.date())
    sus, near, quant, pts, grid, districts = load_static()
    if rain.shape[1] != len(pts["lat"]):
        raise ValueError(f"rain has {rain.shape[1]} points, the bundle has {len(pts['lat'])}")
    trig_all = RN.trigger_series(rain, quant)
    fut = [i for i, d in enumerate(days) if str(d) >= issued][:7]
    if len(fut) < 7:
        raise ValueError(f"only {len(fut)} forecast days from {issued} in the rain fetched")
    fdays = [str(days[i]) for i in fut]
    trig = trig_all[fut]
    sid = static_id()
    stamp = issued_at.isoformat(timespec="seconds")
    (out / "issues").mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "issues" / f"{issued}.npz", days=np.array(fdays),
                        rain_mm=rain[fut].astype(np.float32), trigger=trig.astype(np.float32),
                        all_days=np.array([str(d) for d in days]), all_rain_mm=rain.astype(np.float32),
                        issued_at=np.array(stamp), static=np.array(json.dumps(sid)))
    state, dist = tables(issued, stamp, fdays, trig, sus, near, district_raster(grid, districts),
                         sid["susceptibility"])
    _replace(out / "state.csv", state, STATE_COLS, issued)
    _replace(out / "districts.csv", dist, DIST_COLS, issued)
    return {"issued_on": issued, "issued_at": stamp, "days": fdays,
            "high_plus_pct": [r["high_plus_pct"] for r in state], "districts": len(dist) // 7}


def check(out: Path = LOG, write: bool = False) -> bool:
    """Every logged issue, rebuilt from its own file: the trigger from the
    logged rain, then both tables from the trigger. They must match what was
    written on the day. Issues logged against a static half that has since
    changed are named and skipped, not failed.

    `write` (the `rebuild` command): put the rebuilt rows in the tables in
    place of what is there — for when the way a table is worked out changes,
    never to paper over a mismatch. The issue files are not touched."""
    files = sorted((out / "issues").glob("*.npz")) if (out / "issues").exists() else []
    if not files:
        print("  landslide log: no issues yet")
        return True
    sus, near, quant, pts, grid, districts = load_static()
    boxes, sid = district_raster(grid, districts), static_id()
    st = pd.read_csv(out / "state.csv", dtype=str)
    di = pd.read_csv(out / "districts.csv", dtype=str)
    ok = True
    for f in files:
        z = np.load(f)
        issued, was = f.stem, json.loads(str(z["static"]))
        if was != sid:
            print(f"  {issued}: static files have changed since ({[k for k in sid if sid[k] != was.get(k)]}) — skipped")
            continue
        days = [str(d) for d in z["days"]]
        all_days = [str(d) for d in z["all_days"]]
        trig = RN.trigger_series(z["all_rain_mm"], quant)[[all_days.index(d) for d in days]]
        same_trig = bool(np.allclose(trig, z["trigger"], atol=1e-6))
        state, dist = tables(issued, str(z["issued_at"]), days, trig, sus, near, boxes,
                             sid["susceptibility"])
        a = pd.DataFrame(state, columns=STATE_COLS).astype(str).reset_index(drop=True)
        b = pd.DataFrame(dist, columns=DIST_COLS).astype(str).reset_index(drop=True)
        same = (same_trig and a.equals(st[st["issued_on"] == issued].reset_index(drop=True))
                and b.equals(di[di["issued_on"] == issued].reset_index(drop=True)))
        if write and same_trig and not same:
            _replace(out / "state.csv", state, STATE_COLS, issued)
            _replace(out / "districts.csv", dist, DIST_COLS, issued)
            print(f"  {issued}: tables rewritten from the issue file")
            continue
        ok = ok and same
        print(f"  {issued}: {'rebuilt exactly' if same else 'DOES NOT MATCH'} "
              f"({len(days)} days, {len(dist) // max(len(days), 1)} districts)")
    print(f"  landslide log: {len(files)} issue(s), {st['issued_on'].nunique()} in the tables — "
          f"{'PASS' if ok else 'FAIL'}")
    return ok


def test() -> None:
    """Made-up rain into a scratch folder: an issue is written, a second run
    the same day replaces it without doubling, another day is added beside
    it, and `check` rebuilds both. Nothing is written to records/."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    n = len(json.loads(STATIC["points"].read_text())["lat"])
    rng = np.random.default_rng(0)
    d0 = pd.Timestamp("2026-07-10")
    days = [str((d0 + pd.Timedelta(days=i)).date()) for i in range(-10, 8)]
    rain = rng.gamma(0.6, 14.0, size=(18, n)).astype(np.float32)
    at = datetime(2026, 7, 10, 8, 30).astimezone()
    r1 = log(days, rain, at, tmp)
    r2 = log(days, rain * 1.5, at.replace(hour=19), tmp)
    days2 = [str((d0 + pd.Timedelta(days=i)).date()) for i in range(-9, 9)]
    log(days2, rng.gamma(0.6, 14.0, size=(18, n)).astype(np.float32),
        datetime(2026, 7, 11, 8, 30).astimezone(), tmp)
    st = pd.read_csv(tmp / "state.csv", dtype=str)
    di = pd.read_csv(tmp / "districts.csv", dtype=str)
    shares = st[[f"{c}_pct" for c in CLASSES]].astype(float).sum(axis=1)
    good = (len(st) == 14 and st["issued_on"].nunique() == 2
            and list(st["target_date"][:7]) == days[10:17] and list(st["lead_days"][:7]) == list("0123456")
            and st["issued_at"].iloc[0].startswith("2026-07-10T19:30")
            and r1["high_plus_pct"] != r2["high_plus_pct"]
            and bool(np.allclose(shares, 100, atol=0.01))
            and len(di) == 14 * r1["districts"] and r1["districts"] >= 15
            and len(list((tmp / "issues").glob("*.npz"))) == 2)
    try:
        log(days[:12], rain[:12], at, tmp)
        short = False
    except ValueError:
        short = True
    ok = good and short and check(tmp)
    print(f"  test: {'PASS' if ok else 'FAIL'} (scratch: {tmp}; nothing written to records/)")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "log"
    if cmd == "test":
        test()
    elif cmd == "check":
        raise SystemExit(0 if check() else 1)
    elif cmd == "rebuild":
        check(write=True)
        raise SystemExit(0 if check() else 1)
    else:
        _, _, _, pts, _, _ = load_static()
        got = RN.fetch_rain(list(pts["lat"]), list(pts["lon"]))
        if got is None:
            raise SystemExit("Live rain unavailable (Open-Meteo did not answer) — try again shortly.")
        r = log(*got)
        print(f"  landslide forecast logged: issued {r['issued_at']}, {r['days'][0]} .. {r['days'][-1]}, "
              f"{r['districts']} districts; High or Very High on "
              f"{r['high_plus_pct'][0]:.1f}% of assessed land today")
