"""WHEN rollout pass 2, training half — the same A/B/C/D variant structure as
train_flood_when.py, applied to NWDP's small-river discharge stations.

    python scripts/model/train_flood_when_nwdp.py

Outputs:
    data/interim/flood_when/oof_scores_nwdp.csv   -- out-of-fold blend scores
    reports/flood_when_variant_comparison_nwdp.json

Two deliberate differences from the CWC version, both forced by the data:

  * **No catchment-area feature.** NWDP publishes no catchment area for any
    of the 14, so variant B here is "pooled across all NWDP stations"
    without the size term — an all-NaN column breaks
    HistGradientBoostingClassifier's binning outright, and carries no signal
    anyway. B is still genuinely pooled, just size-blind.
  * **Variant C transfers unchanged.** C is the Passighat-trained model, and
    it consumes ONLY rainfall features (r3, r7, trigger_lag1) — nothing
    level- or discharge-specific — so a model trained on a big river's
    levels applies to a small river's discharge without modification. That
    is the same naive-transfer diagnostic as the CWC pass, now tested across
    an even larger size gap (256,572 km2 down to a ~3 m3/s stream).
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

from backtest_flood_when import derive_flood_days
from backtest_flood_when_nwdp import daily_max_discharge, load_all
from common import INTERIM, ROOT
from gauge_records import trim
from nwdp_stations import STATIONS
from train_flood_when import (FEATURES_NO_SIZE, auc_of, cv_out_of_fold_predict,
                               features_at, fit)

MODELS = ROOT / "models" / "flood_when"
REPORTS = ROOT / "reports"
OUT = INTERIM / "flood_when"
BIG_RIVER_MODEL = MODELS / "C_bigriver_naive_DIAGNOSTIC_ONLY_005-UBDDIB.pkl"


def station_table(code: str, meta: dict, raw: pd.DataFrame) -> pd.DataFrame:
    daily = trim(code, daily_max_discharge(raw, code))   # scale breaks, gauge_records.py
    if len(daily) < 30:
        raise RuntimeError(f"only {len(daily)} usable days")
    flood_days, _ = derive_flood_days(daily)

    feats = features_at(meta["lat"], meta["lon"])
    table = feats.reindex(daily.index)
    table["flood"] = daily.index.isin(flood_days).astype(int)
    table["station_code"] = code
    table["year"] = table.index.year
    table = table.dropna(subset=["r3", "r7"])
    print(f"  {meta['name']}: {len(table):,} usable days, {table['flood'].sum()} flood days")
    return table


def main() -> None:
    print("WHEN pass 2, training — NWDP small rivers (variants A/B/C, blended to D)\n")
    raw = load_all()

    tables, skipped = {}, {}
    for code, meta in STATIONS.items():
        try:
            tables[code] = station_table(code, meta, raw)
        except RuntimeError as exc:
            print(f"  [skip] {meta['name']} ({code}): {exc}")
            skipped[code] = str(exc)

    with open(BIG_RIVER_MODEL, "rb") as fh:
        clf_c = pickle.load(fh)

    results = {code: {"name": STATIONS[code]["name"]} for code in tables}
    preds = {code: {} for code in tables}

    for code, t in tables.items():
        preds[code]["rule"] = t[["r3", "r7"]].mean(axis=1).to_numpy()
        auc, _ = auc_of(t["flood"].to_numpy(), preds[code]["rule"])
        results[code]["baseline_rule"] = auc

    print("\nVariant A - per-station")
    for code, t in tables.items():
        oof = cv_out_of_fold_predict(t, FEATURES_NO_SIZE)
        preds[code]["A"] = oof
        auc, n = auc_of(t["flood"].to_numpy(), oof) if oof is not None else (None, 0)
        results[code]["A_per_station"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc} ({n} flood days)")

    print("\nVariant B - pooled across all NWDP stations (size-blind, see docstring)")
    for code, t in tables.items():
        extra = pd.concat([x for c, x in tables.items() if c != code], axis=0)
        oof = cv_out_of_fold_predict(t, FEATURES_NO_SIZE, extra_train=extra)
        preds[code]["B"] = oof
        auc, n = auc_of(t["flood"].to_numpy(), oof) if oof is not None else (None, 0)
        results[code]["B_pooled"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc} ({n} flood days)")
    MODELS.mkdir(parents=True, exist_ok=True)
    with open(MODELS / "B_pooled_nwdp_all.pkl", "wb") as fh:
        pickle.dump(fit(pd.concat(tables.values(), axis=0), FEATURES_NO_SIZE), fh)

    print("\nVariant C - Passighat-trained, applied unchanged (diagnostic)")
    for code, t in tables.items():
        p = clf_c.predict_proba(t[FEATURES_NO_SIZE])[:, 1]
        preds[code]["C"] = p
        auc, n = auc_of(t["flood"].to_numpy(), p)
        results[code]["C_bigriver_naive_diagnostic"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc} ({n} flood days)")

    print("\nVariant D - shipped blend (rule + B + C)")
    rows = []
    for code, t in tables.items():
        parts = [p for p in (preds[code]["rule"], preds[code]["B"], preds[code]["C"]) if p is not None]
        blend = np.nanmean(np.vstack(parts), axis=0)
        auc, n = auc_of(t["flood"].to_numpy(), blend)
        results[code]["D_blend_shipped"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc} ({n} flood days)")
        rows.append(pd.DataFrame({
            "station_code": code, "station_name": STATIONS[code]["name"],
            "date": t.index, "year": t["year"].to_numpy(),
            "flood": t["flood"].to_numpy(),
            "score_rule": preds[code]["rule"], "score_blend": blend,
            "label_source": "self-derived (top 2% of own history)",
        }))

    pd.concat(rows, ignore_index=True).to_csv(OUT / "oof_scores_nwdp.csv", index=False)
    print(f"\nwrote out-of-fold scores -> {OUT / 'oof_scores_nwdp.csv'}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "flood_when_variant_comparison_nwdp.json").write_text(json.dumps({
        "n_stations": len(tables), "skipped_stations": skipped, "results": results,
    }, indent=2))
    print(f"wrote {REPORTS / 'flood_when_variant_comparison_nwdp.json'}")


if __name__ == "__main__":
    main()
