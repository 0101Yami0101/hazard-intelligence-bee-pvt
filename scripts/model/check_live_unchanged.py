"""Prove a code change left the live flood forecast's numbers alone.

    python scripts/model/check_live_unchanged.py record   # once, BEFORE changing code
    python scripts/model/check_live_unchanged.py check    # after every change

`record` runs the daily forecast exactly as the 08:30 job does, minus the
track-record write, and keeps everything it fetched (the Open-Meteo rain,
every gauge's readings, the Earth Engine soil wetness, the gauge graphs'
30-day history) and everything it produced (the day model's final chances —
soil blend included, via `predict_day` — the area outlook, every river row,
the report, today's raster, the web snapshot). A recording made before a
fetch existed replays it for real (soil) or from the old gauge fetch (graph
history), and lists it as a new fetch. `check` re-runs the CURRENT code on those same inputs, with the
clock frozen to the recorded day, and compares every output field by field:

    old fields    must match exactly (floats to 1e-9)
    new fields    are listed as additions, never a failure
    INTENDED      fields whose change was deliberate, each with its reason

So "no logic changed" is a measured fact, not a promise
(docs/design/FLOOD_SCREEN_PLAN.md, Phase 0).

Nothing permanent is touched: the track record is never written (log=False),
the web snapshot is redirected, the scorecard is frozen to the recorded copy,
and today's report and raster are put back as they were.

Writes  data/interim/flood_forecast/golden_live/  (inputs.pkl, outputs.pkl, ...)
"""
from __future__ import annotations

import copy
import json
import pickle
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT_ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_ / "scripts"), str(ROOT_ / "scripts" / "build"),
                str(ROOT_ / "scripts" / "model"), str(ROOT_ / "webapp")]

import numpy as np
import pandas as pd
import rasterio

import core.rainfall as rainfall
import flood_forecast_live as ffl
import flood_gauge_live as fgl
import forecast_log
from common import INTERIM, PROCESSED, ROOT

GOLD = INTERIM / "flood_forecast" / "golden_live"

# Deliberate changes, with the reason. Reported, never a failure.
INTENDED = {
    "rain_source": ("label fix: the live rain has used 219 points since 2026-09-22, "
                    "the label still said 97 (FLOOD_SCREEN_PLAN.md §5)"),
}
IGNORED = {"generated_at"}          # wall-clock time of the run


def _frozen(day: date):
    class Frozen(date):
        @classmethod
        def today(cls):
            return cls(day.year, day.month, day.day)
    return Frozen


def _run(mode: str, inputs: dict | None) -> tuple[dict, dict]:
    """Run ffl.run(log=False) with every fetch recorded or replayed, and
    return (inputs, outputs)."""
    rec = ({"rain": None, "gauges": {}, "last_seen": {}, "soil": {}, "history": {}}
           if mode == "record" else inputs)
    out = {"predict": [], "new_fetches": []}
    real = (ffl.fetch_rain, fgl.fetch_daily, fgl.last_seen, ffl.export_web,
            ffl.predict_day, ffl.WEB_SNAPSHOT, forecast_log.SCORECARD,
            fgl.date, rainfall.date, ffl.fetch_soil, fgl.fetch_history)

    if mode == "record":
        def fetch_rain(lats, lons, *a, **k):
            got = real[0](lats, lons, *a, **k)
            rec["rain"] = copy.deepcopy(got)
            return got

        def fetch_daily(code, network, since, *a, **k):
            got = real[1](code, network, since, *a, **k)
            rec["gauges"][(code, network, str(since))] = copy.deepcopy(got)
            return got

        def last_seen(code, network):
            got = real[2](code, network)
            rec["last_seen"][(code, network)] = got
            return got

        def fetch_soil(d0, d1):
            got = real[9](d0, d1)
            rec["soil"][(d0, d1)] = copy.deepcopy(got)
            return got

        def fetch_history(code, network, since, *a, **k):
            got = real[10](code, network, since, *a, **k)
            rec["history"][(code, network, str(since))] = copy.deepcopy(got)
            return got
    else:
        def fetch_rain(lats, lons, *a, **k):
            return copy.deepcopy(rec["rain"])

        def fetch_daily(code, network, since, *a, **k):
            key = (code, network, str(since))
            if key not in rec["gauges"]:
                # A fetch the recorded run never made — e.g. the graph's
                # display-only history. It gets no data, and is listed. If the
                # FORECAST's own fetch had changed, its rows would change and
                # show up as "changed" below, so nothing slips through.
                out["new_fetches"].append(key)
                return pd.Series(dtype=float, index=pd.DatetimeIndex([])), None
            return copy.deepcopy(rec["gauges"][key])

        def last_seen(code, network):
            return rec["last_seen"].get((code, network))

        def fetch_soil(d0, d1):
            # recorded before soil existed (2026-09-28): fetch it for real —
            # ERA5-Land for past days does not change — and list it
            if (d0, d1) in rec.get("soil", {}):
                return copy.deepcopy(rec["soil"][(d0, d1)])
            out["new_fetches"].append(("soil", d0, d1))
            return real[9](d0, d1)

        def fetch_history(code, network, since, *a, **k):
            key = (code, network, str(since))
            if key in rec.get("history", {}):
                return copy.deepcopy(rec["history"][key])
            # recorded before the graph's part-days (2026-09-28): the same
            # complete days came through fetch_daily then; no part-days
            out["new_fetches"].append(("history",) + key)
            got = rec["gauges"].get(key)
            return (copy.deepcopy(got[0]) if got else
                    pd.Series(dtype=float, index=pd.DatetimeIndex([]))), []
        frozen = _frozen(rec["today"])
        fgl.date = frozen
        rainfall.date = frozen

    def export_web(today, outlook, times, E, rivers, card, *a, **k):
        out["export_args"] = copy.deepcopy({"today": today, "outlook": outlook,
                                            "times": np.asarray(times), "rivers": rivers,
                                            "card": card})
        return real[3](today, outlook, times, E, rivers, card, *a, **k)

    def predict(model, F, E, soil):
        # the production chance per rain cell per day, soil blend included
        p = real[4](model, F, E, soil)
        out["predict"].append(np.array(p, copy=True))
        return p

    GOLD.mkdir(parents=True, exist_ok=True)
    snap = GOLD / f"_snapshot_{mode}.json"
    card = GOLD / "scorecard.json"
    if mode == "record" and forecast_log.SCORECARD.exists():
        shutil.copy2(forecast_log.SCORECARD, card)

    # files a run overwrites for "today": back them up, put them back after
    today = str(rec["today"]) if mode == "check" else str(date.today())
    touched = [ROOT / "reports" / f"flood_forecast_live_{today}.json",
               PROCESSED / f"flood_forecast_live_{today}.tif"]
    saved = {}
    for p in touched:
        if p.exists():
            saved[p] = GOLD / f"_backup_{p.name}"
            shutil.copy2(p, saved[p])

    ffl.fetch_rain, fgl.fetch_daily, fgl.last_seen = fetch_rain, fetch_daily, last_seen
    ffl.fetch_soil = fetch_soil
    fgl.fetch_history = fetch_history
    ffl.export_web = export_web
    ffl.predict_day = predict
    ffl.WEB_SNAPSHOT = snap
    forecast_log.SCORECARD = card
    try:
        ffl.run(log=False)
        day = out["export_args"]["today"]
        out["report"] = json.loads((ROOT / "reports" / f"flood_forecast_live_{day}.json").read_text())
        with rasterio.open(PROCESSED / f"flood_forecast_live_{day}.tif") as s:
            out["raster"] = s.read(1)
        out["snapshot"] = json.loads(snap.read_text())
    finally:
        (ffl.fetch_rain, fgl.fetch_daily, fgl.last_seen, ffl.export_web,
         ffl.predict_day, ffl.WEB_SNAPSHOT, forecast_log.SCORECARD,
         fgl.date, rainfall.date, ffl.fetch_soil, fgl.fetch_history) = real
        for p in touched:
            if p in saved:
                shutil.copy2(saved[p], p)
                saved[p].unlink()
            elif p.exists():
                p.unlink()
    if mode == "record":
        rec["today"] = date.fromisoformat(out["export_args"]["today"])
    return rec, out


# ── comparison ───────────────────────────────────────────────────────────
def _diff(old, new, path: str, found: dict) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        for k in old:
            p = f"{path}.{k}" if path else str(k)
            if k in IGNORED:
                continue
            if k not in new:
                found["removed"].append(p)
            elif k in INTENDED:
                if old[k] != new[k]:
                    found["intended"].append(f"{p}: {old[k]!r} -> {new[k]!r}  ({INTENDED[k]})")
            else:
                _diff(old[k], new[k], p, found)
        for k in new:
            if k not in old and k not in IGNORED:
                found["added"].append(f"{path}.{k}" if path else str(k))
        return
    if isinstance(old, (list, tuple)) and isinstance(new, (list, tuple)):
        if len(old) != len(new):
            found["changed"].append(f"{path}: length {len(old)} -> {len(new)}")
            return
        for i, (a, b) in enumerate(zip(old, new)):
            _diff(a, b, f"{path}[{i}]", found)
        return
    if isinstance(old, np.ndarray) or isinstance(new, np.ndarray):
        a, b = np.asarray(old), np.asarray(new)
        if a.shape != b.shape:
            found["changed"].append(f"{path}: shape {a.shape} -> {b.shape}")
        elif a.dtype.kind in "fc" or b.dtype.kind in "fc":
            same = np.isclose(a, b, rtol=0, atol=1e-9, equal_nan=True)
            if not same.all():
                both = np.isfinite(a) & np.isfinite(b) & (np.abs(a) > 1e-12)
                r = (b[both] / a[both]) if both.any() else np.array([np.nan])
                found["changed"].append(
                    f"{path}: {int((~same).sum())} of {a.size} values differ "
                    f"(new/old median x{np.nanmedian(r):.2f}, range x{np.nanmin(r):.2f}"
                    f"..x{np.nanmax(r):.2f}; old total {np.nansum(a):.4g}, new {np.nansum(b):.4g})")
        elif not np.array_equal(a, b):
            found["changed"].append(f"{path}: values differ")
        return
    if isinstance(old, float) and isinstance(new, (int, float)) and not isinstance(new, bool):
        if not (old == new or (np.isnan(old) and np.isnan(new)) or abs(old - new) <= 1e-9):
            found["changed"].append(f"{path}: {old!r} -> {new!r}")
        return
    if old != new:
        found["changed"].append(f"{path}: {old!r} -> {new!r}")


def record() -> None:
    print("Recording the golden live run (fetches live rain and every gauge)...\n")
    rec, out = _run("record", None)
    with open(GOLD / "inputs.pkl", "wb") as fh:
        pickle.dump(rec, fh)
    with open(GOLD / "outputs.pkl", "wb") as fh:
        pickle.dump(out, fh)
    print(f"\nRecorded for {rec['today']}: {len(rec['gauges'])} gauge fetches, "
          f"{len(out['predict'])} day-model calls, rain {rec['rain'][1].shape}")
    print(f"  wrote {GOLD}")


def check() -> bool:
    if not (GOLD / "inputs.pkl").exists():
        raise SystemExit("No golden run recorded yet — run `record` first, before changing code.")
    with open(GOLD / "inputs.pkl", "rb") as fh:
        rec = pickle.load(fh)
    with open(GOLD / "outputs.pkl", "rb") as fh:
        old = pickle.load(fh)
    print(f"Re-running the current code on the inputs recorded for {rec['today']}...\n")
    _, new = _run("check", rec)
    found = {"changed": [], "removed": [], "added": [], "intended": []}
    for key in ("predict", "export_args", "report", "raster", "snapshot"):
        _diff(old[key], new[key], key, found)
    print("\n" + "=" * 72)
    print(f"Unchanged-logic check against the run recorded for {rec['today']}")
    for kind in ("changed", "removed", "intended", "added"):
        items = found[kind]
        print(f"  {kind:<9} {len(items)}")
        for x in items[:40]:
            print(f"      {x}")
        if len(items) > 40:
            print(f"      ... and {len(items) - 40} more")
    ok = not found["changed"] and not found["removed"]
    if new.get("new_fetches"):
        print(f"  info      {len(new['new_fetches'])} fetches the recorded run never made "
              "(given no data; e.g. the graph's display-only history)")
    print("  RESULT: " + ("PASS — every old number is identical" if ok
                          else "FAIL — an existing output changed"))
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "record":
        record()
    else:
        sys.exit(0 if check() else 1)
