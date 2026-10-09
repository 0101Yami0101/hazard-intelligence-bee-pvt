"""Phase 2 of the flood-WHEN pilot — train and keep separate WHEN model variants.

    python scripts/model/train_flood_when.py

Outputs:
    models/flood_when/<variant>_<station_code>.pkl
    reports/flood_when_variant_comparison_tawang.json

Three variants, trained and scored SEPARATELY (not merged) — see
docs/design/FLOOD_WHEN_PILOT_PLAN.md §5 for the reasoning:

    A  per-station     trained only on that station's own visible years
    B  pooled          all gauged stations pooled, catchment area as a feature
    C  naive-transfer  Passighat (large river) only, applied to Tawang untouched
                        — diagnostic strawman, never shipped, exists only to
                        show whether B's size-awareness actually helps

Passighat (large Siang river, catchment 256,572 km^2) is archived here
specifically to give B and C something to be about — pooling or naive-
transferring across two small, nearby, similar Tawang streams alone would not
test the actual question. This is guardrail #5 in FLOOD_WHEN_PILOT_PLAN.md
("cross-check on one very different station"), pulled forward because
variants B/C need it to mean anything, not a scope change.

Every model is HistGradientBoostingClassifier — handles missing features
(a station with no known catchment area) natively, and is kept deliberately
shallow (few leaves, few trees) per the "keep every variant simple at this
scale" guardrail: at most a few hundred real flood days to learn from.
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
import rasterio
from rasterio.warp import transform
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

import grid as G
from backtest_flood_when import clean_readings, derive_flood_days
from common import GAUGES, INTERIM, ROOT
from flood_stations import STATIONS
from gauge_records import trim

# Rollout, 2026-08-30: grew from the 3-station pilot (2 Tawang gauges +
# Passighat) to all 18 CWC stations found in/near Arunachal — see
# flood_stations.py, the shared registry, and FLOOD_WHEN_PILOT_PLAN.md §8.
# Big-river reference for variant C's naive-transfer diagnostic stays
# Passighat — still the largest catchment in the set (256,572 km^2).

SRC = INTERIM / "rainfall"
FEAT = SRC / "features"
MODELS = ROOT / "models" / "flood_when"
REPORTS = ROOT / "reports"

N_FOLDS = 5            # year-grouped folds — a model is never tested on a year it trained on
MAX_DEPTH = 3
MAX_ITER = 60


def features_at(lat: float, lon: float) -> pd.DataFrame:
    """Per-feature percentile series (r3, r7) at one point, full IMERG span."""
    xs, ys = transform("EPSG:4326", "EPSG:32646", [lon], [lat])
    row, col = G.xy_to_rowcol(xs[0], ys[0])
    with rasterio.open(SRC / "imerg_index.tif") as s:
        idx = s.read(1)
    cl = int(idx[row, col])
    if cl < 0:
        raise RuntimeError(f"({lat},{lon}) falls outside the IMERG-indexed grid")

    cfg = json.loads((ROOT / "models" / "trigger.json").read_text())
    feats = cfg["trigger_definition"]["features"]
    dates = pd.to_datetime(np.load(SRC / "dates.npy").astype("datetime64[D]"))
    mo = dates.month.to_numpy()
    mons = (mo >= 5) & (mo <= 10)

    cols = {}
    for n in feats:
        a = np.load(FEAT / f"{n}.npy", mmap_mode="r")[:, cl].astype(np.float32)
        clim = a[mons]
        clim = clim[~np.isnan(clim)]
        cols[n] = np.array([(clim < v).mean() if np.isfinite(v) else np.nan for v in a],
                            dtype=np.float32)
    df = pd.DataFrame(cols, index=dates)
    df["trigger_lag1"] = df.mean(axis=1).shift(1)
    return df


def station_table(code: str, meta: dict) -> pd.DataFrame:
    """One row per gauge-reading day: features + self-derived-or-real label."""
    csv_path = GAUGES / "cwc" / f"{code}_hhs.csv"
    df = pd.read_csv(csv_path, parse_dates=["datetime"])
    df = clean_readings(df)
    df["date"] = df["datetime"].dt.date
    daily = df.groupby("date")["level"].max()
    daily.index = pd.to_datetime(daily.index)
    daily = trim(code, daily.sort_index())     # scale breaks, gauge_records.py

    # Same fallback as backtest_flood_when.py, 2026-08-30: a real threshold
    # that the whole record never once reaches (found on 4 rollout stations)
    # needs the self-derived proxy too, or it yields zero training labels.
    if meta["danger_level"] is not None and (daily >= meta["danger_level"]).any():
        flood_days = daily.index[daily >= meta["danger_level"]]
        label_source = "CWC published danger level"
    else:
        flood_days, _ = derive_flood_days(daily)
        label_source = "self-derived (top 2% of own history)"

    feats = features_at(meta["lat"], meta["lon"])
    table = feats.reindex(daily.index)
    table["catchment_log"] = (np.log10(meta["catchment_km2"])
                               if meta["catchment_km2"] else np.nan)
    table["flood"] = daily.index.isin(flood_days).astype(int)
    table["station_code"] = code
    table["year"] = table.index.year
    table = table.dropna(subset=["r3", "r7"])
    table.attrs["label_source"] = label_source
    print(f"  {meta['name']}: {len(table):,} usable days, "
          f"{table['flood'].sum()} flood days ({label_source})")
    return table


# Variants A and C each train on a single station, where catchment area is a
# constant (or entirely missing) — HistGradientBoostingClassifier's binning
# step errors on a column with fewer than 2 distinct values, and a constant
# carries no signal for a single station anyway. Only B pools stations with
# genuinely different catchment sizes, so only B gets the size feature.
FEATURES_NO_SIZE = ["r3", "r7", "trigger_lag1"]
FEATURES_WITH_SIZE = ["r3", "r7", "trigger_lag1", "catchment_log"]


def fit(train: pd.DataFrame, cols: list[str]) -> HistGradientBoostingClassifier:
    clf = HistGradientBoostingClassifier(max_depth=MAX_DEPTH, max_iter=MAX_ITER,
                                          random_state=0)
    clf.fit(train[cols], train["flood"])
    clf._feature_cols = cols  # stash for score()/predict-time consistency
    return clf


def cv_out_of_fold_predict(target: pd.DataFrame, cols: list[str],
                            extra_train: pd.DataFrame | None = None) -> np.ndarray | None:
    """Year-grouped out-of-fold predictions for every row of `target`.

    Rotates which years of `target` are held out (GroupKFold on calendar
    year), so — unlike a single most-recent-20% cut — every row eventually
    gets scored by a model that never saw its year, and no single fold can
    end up with zero flood days and silently drop that station from the
    scorecard (which is exactly what a fixed chronological split did here:
    Rho Basti and Passighat's most recent years both happened to be
    flood-quiet, leaving nothing in a single fixed test window).

    `extra_train` (used by variant B) is added to every fold's training set
    in full — it is never the thing being held out. Returns None if there
    are too few distinct years to fold at all.
    """
    years = target["year"].to_numpy()
    n_years = len(np.unique(years))
    k = min(N_FOLDS, n_years)
    if k < 2:
        return None

    oof = np.full(len(target), np.nan)
    gkf = GroupKFold(n_splits=k)
    for train_idx, test_idx in gkf.split(target, groups=years):
        train_rows = target.iloc[train_idx]
        if extra_train is not None:
            train_rows = pd.concat([train_rows, extra_train], axis=0)
        # Rollout, 2026-08-30: several new stations have very few total
        # flood days (2-11) — a fold can land with zero positives in its
        # training split, which HistGradientBoostingClassifier can't fit on
        # (needs 2 classes). Leave that fold's rows as NaN (unscored) rather
        # than crash the whole station; auc_of() already treats NaN as
        # "not scored," so this degrades gracefully to fewer scored days,
        # not a failure.
        if train_rows["flood"].nunique() < 2:
            continue
        clf = fit(train_rows, cols)
        oof[test_idx] = clf.predict_proba(target.iloc[test_idx][cols])[:, 1]
    return oof


def auc_of(y: np.ndarray, s: np.ndarray) -> tuple[float | None, int]:
    valid = ~np.isnan(s)
    y, s = y[valid], s[valid]
    if y.sum() == 0 or y.sum() == len(y):
        return None, int(y.sum())
    return round(float(roc_auc_score(y, s)), 3), int(y.sum())


def baseline_auc(table: pd.DataFrame) -> float | None:
    """The Phase-1 physics rule alone (mean of r3, r7 percentile), full record —
    not trained on anything, so there is no train/test split to apply."""
    if table["flood"].sum() == 0 or table["flood"].sum() == len(table):
        return None
    s = table[["r3", "r7"]].mean(axis=1)
    return round(float(roc_auc_score(table["flood"], s)), 3)


def save_model(clf, variant: str, code: str) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    path = MODELS / f"{variant}_{code}.pkl"
    with open(path, "wb") as fh:
        pickle.dump(clf, fh)


def main() -> None:
    print("Phase 2 — train separate WHEN model variants (A/B/C), kept separate,\n"
          "then blend them into the actual shipped WHEN score (D).\n")
    print(f"Evaluation: {N_FOLDS}-fold year-grouped cross-validation per station — "
          "every flood day gets scored exactly once, by a model that never "
          "trained on its year.\n")

    tables: dict[str, pd.DataFrame] = {}
    skipped: dict[str, str] = {}
    for code, meta in STATIONS.items():
        try:
            tables[code] = station_table(code, meta)
        except RuntimeError as exc:
            # Rollout, 2026-08-30: a border-adjacent gauge (Bhalukpong) sits
            # outside the IMERG-indexed grid even though it's inside the
            # project's bounding box — see backtest_flood_when.py's same
            # fix. Skip that one station, keep the other 17.
            print(f"  [skip] {meta['name']} ({code}): {exc}")
            skipped[code] = str(exc)
    big_river_code = "005-UBDDIB"

    results: dict[str, dict] = {code: {"name": STATIONS[code]["name"]} for code in tables}
    preds: dict[str, dict[str, np.ndarray]] = {code: {} for code in tables}

    # --- Baseline: the existing physics rule, not trained on anything ------
    for code, t in tables.items():
        preds[code]["rule"] = t[["r3", "r7"]].mean(axis=1).to_numpy()
        results[code]["baseline_rule"] = baseline_auc(t)

    # --- Variant A: per-station ---------------------------------------------
    print("\nVariant A — per-station")
    for code, t in tables.items():
        oof = cv_out_of_fold_predict(t, FEATURES_NO_SIZE)
        preds[code]["A"] = oof
        auc, n_pos = auc_of(t["flood"].to_numpy(), oof) if oof is not None else (None, 0)
        results[code]["A_per_station"] = auc
        # A single-class station (0 flood days, e.g. Namsai/Tuting in this
        # rollout) can't fit any model at all, CV or not — skip saving one
        # rather than crash; A_per_station stays None for it in the report.
        if t["flood"].nunique() >= 2:
            save_model(fit(t, FEATURES_NO_SIZE), "A_per_station", code)
        print(f"  {STATIONS[code]['name']}: AUC {auc}  ({n_pos} flood days scored, "
              f"baseline rule {results[code]['baseline_rule']})")

    # --- Variant B: pooled, size-aware ---------------------------------------
    print("\nVariant B — pooled across all gauged stations, catchment-area-aware")
    for code, t in tables.items():
        extra = pd.concat([tt for c, tt in tables.items() if c != code], axis=0)
        oof = cv_out_of_fold_predict(t, FEATURES_WITH_SIZE, extra_train=extra)
        preds[code]["B"] = oof
        auc, n_pos = auc_of(t["flood"].to_numpy(), oof) if oof is not None else (None, 0)
        results[code]["B_pooled_size_aware"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc}  ({n_pos} flood days scored)")
    save_model(fit(pd.concat(tables.values(), axis=0), FEATURES_WITH_SIZE),
               "B_pooled_size_aware", "all")

    # --- Variant C: naive big-river-only (diagnostic, never shipped) -------
    print("\nVariant C — naive, trained on Passighat only, applied elsewhere "
          "(diagnostic only)")
    clf_c = fit(tables[big_river_code], FEATURES_NO_SIZE)
    save_model(clf_c, "C_bigriver_naive_DIAGNOSTIC_ONLY", big_river_code)
    for code, t in tables.items():
        if code == big_river_code:
            p = cv_out_of_fold_predict(t, FEATURES_NO_SIZE)
        else:
            p = clf_c.predict_proba(t[FEATURES_NO_SIZE])[:, 1]
        preds[code]["C"] = p
        auc, n_pos = auc_of(t["flood"].to_numpy(), p) if p is not None else (None, 0)
        results[code]["C_bigriver_naive_diagnostic"] = auc
        print(f"  tested on {STATIONS[code]['name']}: AUC {auc}  ({n_pos} flood days scored)")

    # --- D: the actual shipped WHEN score — a simple blend, ML included ----
    # ENSEMBLE_STRATEGY.md §3/§4: keep the referee simple while proof data is
    # scarce, but DO NOT sideline a trained model just because it didn't win
    # solo — an equal-weight blend is the simplest real meta-learner, and it
    # puts B and C's ML signal into the live score today, not after they
    # "graduate." A is left out of the blend specifically (not the panel) —
    # it isn't weak-but-diverse, it's strictly dominated by B on every
    # station tested, so blending it in would only add noise for zero
    # offsetting signal; it stays on record and gets re-tried as data grows.
    print("\nVariant D — the shipped score: equal-weight blend of rule + B + C")
    for code, t in tables.items():
        parts = [p for p in (preds[code]["rule"], preds[code]["B"], preds[code]["C"]) if p is not None]
        blend = np.nanmean(np.vstack(parts), axis=0) if parts else None
        auc, n_pos = auc_of(t["flood"].to_numpy(), blend) if blend is not None else (None, 0)
        results[code]["D_blend_shipped"] = auc
        print(f"  {STATIONS[code]['name']}: AUC {auc}  ({n_pos} flood days scored)")

    # Persist the out-of-fold blend scores themselves, not just their AUC.
    # Calibration (calibrate_flood_when.py, plan doc §10) needs the raw
    # per-day scores, and they MUST be the out-of-fold ones — calibrating on
    # in-sample predictions would fit the calibrator to scores the model has
    # already seen the answer for, and look perfect for the wrong reason.
    rows = []
    for code, t in tables.items():
        parts = [p for p in (preds[code]["rule"], preds[code]["B"], preds[code]["C"]) if p is not None]
        if not parts:
            continue
        blend = np.nanmean(np.vstack(parts), axis=0)
        rows.append(pd.DataFrame({
            "station_code": code,
            "station_name": STATIONS[code]["name"],
            "date": t.index,
            "year": t["year"].to_numpy(),
            "flood": t["flood"].to_numpy(),
            "score_rule": preds[code]["rule"],
            "score_blend": blend,
            "label_source": t.attrs.get("label_source", "unknown"),
        }))
    if rows:
        oof_path = INTERIM / "flood_when" / "oof_scores_cwc.csv"
        pd.concat(rows, ignore_index=True).to_csv(oof_path, index=False)
        print(f"wrote out-of-fold scores -> {oof_path}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_when_variant_comparison_arunachal.json"
    out.write_text(json.dumps({
        "note": "D is the actual shipped WHEN score: an equal-weight blend of "
                "the rule, B, and C — real ML weight in production today, not "
                "gated behind solo-beats-baseline. A is excluded from the "
                "blend (strictly dominated by B, adds no offsetting signal) "
                "but stays on record, not deleted. Variant C alone is still a "
                "diagnostic label, not a standalone panel candidate — its "
                "role is as an input to D. See FLOOD_WHEN_PILOT_PLAN.md §5/§8. "
                f"A/B/D are scored by {N_FOLDS}-fold year-grouped "
                "cross-validation, not a single holdout.",
        "n_stations": len(tables),
        "skipped_stations": skipped,
        "results": results,
    }, indent=2))
    print(f"\nwrote {out}")

    print("\nScorecard (AUC, higher is better; None = too few flood days to score):")
    print(f"  {'station':<14}{'baseline':>10}{'A (own)':>10}{'B (pooled)':>12}"
          f"{'C (naive)':>11}{'D (shipped)':>13}")
    for code in tables:
        r = results[code]
        def fmt(v): return f"{v:.3f}" if v is not None else "n/a"
        print(f"  {STATIONS[code]['name']:<14}{fmt(r['baseline_rule']):>10}"
              f"{fmt(r['A_per_station']):>10}{fmt(r['B_pooled_size_aware']):>12}"
              f"{fmt(r['C_bigriver_naive_diagnostic']):>11}{fmt(r['D_blend_shipped']):>13}")


if __name__ == "__main__":
    main()
