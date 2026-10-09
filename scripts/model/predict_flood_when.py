"""The operational end of the flood WHEN system — issue a real calibrated
probability for a given date, per station.

    python scripts/model/predict_flood_when.py                # latest date in the archive
    python scripts/model/predict_flood_when.py 2025-08-31     # a specific date

Output:
    reports/flood_when_forecast_<date>.json

This is the piece that makes the whole chain a system rather than an
analysis: it loads the shipped panel (rule + pooled tree + naive-transfer
tree), blends them exactly as validated, and passes the blend through the
calibrator from calibrate_flood_when.py so the number that comes out is an
actual probability, not a rank.

════════════════════════════════════════════════════════════════════════════
WHAT THE NUMBER MEANS — the two kinds, kept apart
════════════════════════════════════════════════════════════════════════════
For a station with a published CWC danger level it reads:
    "P(this river crosses its official danger level today)"
For a station without one:
    "P(today lands in this river's own wettest 2% of days)"
Both are real and both are calibrated; they are not the same claim, so each
row carries its own `means` field and they are never averaged together.

════════════════════════════════════════════════════════════════════════════
⚠️ THIS IS A HINDCAST PATH, NOT A LIVE FEED
════════════════════════════════════════════════════════════════════════════
Rainfall features come from the archived IMERG stack, which lags real time
by roughly a day and stops at the last archived date. Everything downstream
of the features — blend, calibration, thresholds — is exactly what a live
system would run; only the input tap differs. Wiring the live Open-Meteo
path in (already used by the landslide side, see
docs/design/RAINFALL_FEATURES.md) is the remaining step to make this
genuinely real-time, and it changes nothing about the numbers below.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd

from common import ROOT
from flood_stations import STATIONS as CWC_STATIONS
from nwdp_stations import STATIONS as NWDP_STATIONS
from train_flood_when import FEATURES_NO_SIZE, FEATURES_WITH_SIZE, features_at

MODELS = ROOT / "models" / "flood_when"
REPORTS = ROOT / "reports"

# Alert bands, chosen from the measured reliability table in
# reports/flood_when_calibration.json — each one is a probability level the
# calibration actually verified against observed frequency, not a round
# number picked for looks.
BANDS = [(0.25, "SEVERE"), (0.10, "HIGH"), (0.05, "MODERATE"),
         (0.02, "ELEVATED"), (0.0, "NORMAL")]


def band_for(p: float) -> str:
    return next(name for thr, name in BANDS if p >= thr)


def load_panel():
    with open(MODELS / "B_pooled_size_aware_all.pkl", "rb") as fh:
        b_cwc = pickle.load(fh)
    with open(MODELS / "B_pooled_nwdp_all.pkl", "rb") as fh:
        b_nwdp = pickle.load(fh)
    with open(MODELS / "C_bigriver_naive_DIAGNOSTIC_ONLY_005-UBDDIB.pkl", "rb") as fh:
        c = pickle.load(fh)
    with open(MODELS / "calibrator_isotonic.pkl", "rb") as fh:
        cal = pickle.load(fh)
    return b_cwc, b_nwdp, c, cal


def score_station(code: str, meta: dict, network: str, date: pd.Timestamp,
                   b_model, c_model, calibrator) -> dict | None:
    feats = features_at(meta["lat"], meta["lon"])
    if date not in feats.index:
        return None
    row = feats.loc[[date]].copy()
    if row[["r3", "r7"]].isna().any(axis=None):
        return None

    row["catchment_log"] = (np.log10(meta["catchment_km2"])
                             if meta.get("catchment_km2") else np.nan)

    rule = float(row[["r3", "r7"]].mean(axis=1).iloc[0])
    cols_b = FEATURES_WITH_SIZE if network == "CWC" else FEATURES_NO_SIZE
    b = float(b_model.predict_proba(row[cols_b])[:, 1][0])
    c = float(c_model.predict_proba(row[FEATURES_NO_SIZE])[:, 1][0])
    blend = float(np.mean([rule, b, c]))
    prob = float(calibrator.predict([blend])[0])

    official = bool(meta.get("danger_level") is not None)
    return {
        "station_code": code,
        "station_name": meta["name"],
        "network": network,
        "probability_pct": round(100 * prob, 2),
        "alert_band": band_for(prob),
        "means": ("P(crosses official CWC danger level today)" if official
                  else "P(today is in this river's own wettest 2% of days)"),
        "label_basis": "official CWC danger level" if official else "self-derived top-2%",
        "raw_blend_score": round(blend, 4),
        "panel": {"rule": round(rule, 4), "pooled_tree": round(b, 4),
                   "transfer_tree": round(c, 4)},
    }


def main() -> None:
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    b_cwc, b_nwdp, c, cal = load_panel()

    probe = features_at(CWC_STATIONS["005-UBDDIB"]["lat"], CWC_STATIONS["005-UBDDIB"]["lon"])
    usable = probe.dropna(subset=["r3", "r7"]).index
    date = pd.Timestamp(date_arg) if date_arg else usable.max()
    print(f"Flood WHEN forecast for {date.date()}"
          f"{'' if date_arg else '  (latest date in the rainfall archive)'}\n")

    rows = []
    for stations, network, bmodel in [(CWC_STATIONS, "CWC", b_cwc),
                                       (NWDP_STATIONS, "NWDP", b_nwdp)]:
        for code, meta in stations.items():
            try:
                r = score_station(code, meta, network, date, bmodel, c, cal)
            except RuntimeError:
                continue          # station outside the rainfall grid
            if r:
                rows.append(r)

    rows.sort(key=lambda r: -r["probability_pct"])
    print(f"  {'station':<22}{'net':<6}{'prob':>8}  {'band':<10}basis")
    for r in rows:
        print(f"  {r['station_name'][:21]:<22}{r['network']:<6}"
              f"{r['probability_pct']:>7.2f}%  {r['alert_band']:<10}{r['label_basis']}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"flood_when_forecast_{date.date()}.json"
    out.write_text(json.dumps({
        "date": str(date.date()),
        "n_stations": len(rows),
        "input_source": "archived IMERG rainfall stack (hindcast path - see module docstring)",
        "bands": {name: f">= {100*thr:.0f}%" for thr, name in BANDS},
        "forecasts": rows,
    }, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
