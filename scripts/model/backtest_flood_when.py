"""Phase 1 of the flood-WHEN pilot — backtest the rainfall rule, no training yet.

    python scripts/model/backtest_flood_when.py

Outputs:
    data/interim/flood_when/arunachal_flood_days.csv   -- flood-day labels, all stations
    reports/flood_when_backtest_arunachal.json          -- baseline score, all stations

════════════════════════════════════════════════════════════════════════════
WHY THIS LABEL IS SELF-DERIVED, NOT FROM CWC'S PUBLISHED THRESHOLD
════════════════════════════════════════════════════════════════════════════
Neither pilot gauge (Murga Bridge, Rho Basti) has a published CWC danger/
warning level — confirmed directly, both fields null in fetch_21's static
JSON. **We do not wait for that ask.** "This day counts as high water" is
derived from each station's own recorded history instead: the top 2% of its
own daily-max readings — a standard percentile-based flood-proxy technique
used in hydrology precisely when no official threshold exists. An
annual-maxima Gumbel return-level is fitted alongside as a cross-check,
reported but not used operationally (too few annual maxima — 8-21 years per
station — to trust alone).

If CWC answers the ask later, swap the real threshold in; nothing else here
changes.

════════════════════════════════════════════════════════════════════════════
STATION LOCATIONS — real coordinates, not the original Jang-proxy approximation
════════════════════════════════════════════════════════════════════════════
The main CWC station record returns null lat/lon for every gauge — that's
why the original pilot approximated both Tawang gauges to Jang town centre.
A separate, undocumented `layer-station-geo` endpoint has REAL per-station
coordinates for all of them, found during the 2026-08-30 rollout — see
flood_stations.py, the shared registry both this script and
train_flood_when.py now import from. 18 stations statewide, real locations.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform
from scipy import stats
from sklearn.metrics import roc_auc_score

import grid as G
from common import GAUGES, INTERIM, ROOT
from flood_stations import STATIONS

SRC = INTERIM / "rainfall"
FEAT = SRC / "features"
OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"

# Kept for backward compatibility with anything still importing JANG directly
# (e.g. earlier sentinel1_flood_evidence.py revisions) — no longer used to
# position any station; see flood_stations.py for real per-station locations.
JANG = (27.5834, 91.9802)

FLOOD_PCTILE = 0.98   # self-derived "high water" threshold: top 2% of daily max
MONSOON = (5, 10)
LAG_DAYS = 1          # a flood day counts as "flagged" if trigger was high that day or up to LAG_DAYS before


def clean_readings(df: pd.DataFrame) -> pd.DataFrame:
    """Drop gross sensor/transmission errors before any statistic touches them.

    Found on the Tawang pilot gauges: a handful of raw readings off by
    ~10-1000x (decimal-shift glitches) or literal 0.00 dropouts — e.g. Murga
    Bridge shows one 2026 reading of 2,134,040 against a normal range of
    ~2,134. A single one of these corrupts an annual maximum and the whole
    extreme-value cross-check.

    ⚠️ Found on the statewide rollout, 2026-08-30: a GLOBAL median/MAD (one
    baseline for the whole multi-decade record) is the wrong tool once a
    station's history spans a real datum shift — Miao (008-ubddib) has two
    genuinely real level clusters (~130-215 and ~216-310, no gap-filling
    values between), almost certainly a gauge re-levelling at some point in
    ~30 years of record, not sensor error. The original global check flagged
    **18,732 of 112,413 readings (17%)** as "outliers" — it would have
    silently deleted a real fifth of a station's history. Fixed with a
    ROLLING local median/MAD (90-day window) instead of one whole-series
    baseline: a slow datum shift moves the local baseline along with it (so
    points near their own neighbourhood are never flagged), while a true
    isolated spike still stands out against its own nearby readings exactly
    as before. Re-verified this doesn't regress the original two pilot
    gauges (§ FLOOD_WHEN_PILOT_PLAN.md rollout note).
    """
    s = df["level"]
    med = s.rolling(90, center=True, min_periods=10).median()
    mad = (s - med).abs().rolling(90, center=True, min_periods=10).median()
    mad = mad.replace(0, np.nan)
    mz = 0.6745 * (s - med).abs() / mad
    # A rolling MAD can itself collapse toward 0 in a genuinely calm, stable
    # stretch (a real dry spell with almost no day-to-day change) — caught
    # while re-checking this fix on Rho Basti: the z-score-only version
    # flagged readings like 2229.8-2231.93, entirely inside that station's
    # normal range (annual maxima run 2230-2233), as "errors." A ratio
    # backstop fixes it: only drop where the value is also either a true
    # zero dropout or off by 3x+ from its own local neighbourhood — real
    # gauge noise is never that far off, but a decimal-shift glitch always is.
    ratio = s / med.replace(0, np.nan)
    bad = ((mz > 15) & ((s < 1e-6) | (ratio > 3) | (ratio < 1 / 3))).fillna(False)
    if bad.sum():
        print(f"    [clean] dropped {bad.sum()} gross sensor-error reading(s) "
              f"({100*bad.sum()/len(df):.2f}% of {len(df):,}): "
              f"{sorted(df.loc[bad, 'level'].tolist())[:20]}"
              f"{' ...' if bad.sum() > 20 else ''}")
    df = df.loc[~bad]
    # Second pass, in METRES. The ratio test above cannot see a slip on a
    # level measured as height above sea level: Murga Bridge logged 2,231.30
    # for one hour on 2026-09-28 against a steady 2,134.30 — +97 m, but only
    # 4.5% — and the river forecast read 52% from it (§13f).
    if "datetime" in df.columns and len(df):
        o = df.sort_values("datetime", kind="stable")
        away = impossible_excursions(o["datetime"].to_numpy(), o["level"].to_numpy(float))
        if away.any():
            print(f"    [clean] dropped {int(away.sum())} reading(s) in impossible excursions "
                  f"(away from a steady level and straight back): "
                  f"{sorted(o['level'].to_numpy()[away].tolist())[:20]}"
                  f"{' ...' if away.sum() > 20 else ''}")
            df = df.drop(index=o.index[away])
        # Third pass: keying slips the pass above cannot judge — where readings
        # come 3 a day, or wrong and right readings alternate (§13g).
        o = df.sort_values("datetime", kind="stable")
        slip = keying_slips(o["datetime"].to_numpy(), o["level"].to_numpy(float))
        if slip.any():
            print(f"    [clean] dropped {int(slip.sum())} keying slip(s) (one digit off, or two "
                  f"swapped, on a steady river): "
                  f"{sorted(o['level'].to_numpy()[slip].tolist())[:20]}"
                  f"{' ...' if slip.sum() > 20 else ''}")
            df = df.drop(index=o.index[slip])
    return df


# ── impossible excursions: judged in metres, against the river itself ─────
# A river level leaves a steady stretch by more than a river moves in one
# reading, sits away from it, and then comes BACK to where it was in one
# step. A river cannot do that; a data slip does (a digit off by 100 m, a
# value doubled, a neighbouring station's reading logged under this code).
# The level it left and returned to is taken as the true one.
#
# What is deliberately NOT removed, each checked on made-up series and on
# every CWC gauge's full history before this was switched on (§13f):
#   - a jump that has not come back yet — a real surge must never be hidden,
#     so the newest reading always stands until the next one confirms it;
#   - a rise that recedes gradually (a flood, even +30 m in one hour);
#   - a shift that stays (a re-levelled gauge);
#   - a single reading up to SINGLE_M away (a dam release can pulse 3 m);
#   - anything where the readings are more than STEP_H apart (3 readings a
#     day cannot tell a slip from a short flood).
SPIKE_K = 3             # readings that say where the river was
SPIKE_WINDOW_H = 12.0   # ... all within this many hours
SPIKE_STEP_H = 3.0      # "one step": consecutive readings no further apart
SPIKE_SINGLE_M = 5.0    # one stray reading: more than this from the steady level
SPIKE_BLOCK_M = 20.0    # several readings in a row: more than this, and flat
SPIKE_MAX_H = 72.0      # away for longer than this is a real shift
SPIKE_TIGHT = 0.2       # "steady" / "flat" / "came back": within this share of the jump
BODY_PAD_M = 10.0       # an ordinary level: the middle 98% of the series, give or take this


def _ordinary_levels(v: np.ndarray) -> tuple[float, float]:
    """The range a steady level must fall in to be trusted as "where the
    river was": the middle 98% of the series, give or take BODY_PAD_M. A
    second, wrong series is far outside it unless it fills over 1% of the
    record; a gauge re-levelled part-way through has both its eras inside."""
    lo, hi = np.quantile(v, [0.01, 0.99])
    return float(lo) - BODY_PAD_M, float(hi) + BODY_PAD_M


def impossible_excursions(t: np.ndarray, v: np.ndarray) -> np.ndarray:
    """True for each reading that is part of an impossible excursion. `t`
    (datetime64) must be sorted; `v` is the level in metres. Blank readings
    (the history files have some) are never judged and never used to judge.

    The steady level a reading is judged against must be an ordinary level
    for this gauge (`_ordinary_levels`). Where a second, wrong series
    outnumbers the true one for a stretch, each TRUE reading stands alone
    between steady runs of wrong ones — and without this the true readings
    were the ones removed (found on a made-up series, §13g)."""
    keep = np.flatnonzero(np.isfinite(v))
    out = np.zeros(len(v), bool)
    if len(keep) == 0:
        return out
    body_lo, body_hi = _ordinary_levels(v[keep])
    K = SPIKE_K
    for _ in range(50):                      # a removed block can uncover the next
        tt, vv = t[keep], v[keep]
        n = len(vv)
        if n <= K:
            break
        th = (tt - tt[0]) / np.timedelta64(1, "h")
        bad = np.zeros(n, bool)
        i = K
        while i < n:
            pre = vv[i - K:i]
            if th[i] - th[i - K] > SPIKE_WINDOW_H or th[i] - th[i - 1] > SPIKE_STEP_H:
                i += 1
                continue
            m = float(np.median(pre))
            jump = vv[i] - m
            a = abs(jump)
            if (a <= SPIKE_SINGLE_M or (pre.max() - pre.min()) > SPIKE_TIGHT * a
                    or not body_lo <= m <= body_hi):
                i += 1
                continue
            j = i
            while (j < n and (vv[j] - m) * np.sign(jump) > 0.5 * a
                   and th[j] - th[i] <= SPIKE_MAX_H):
                j += 1
            if j >= n or th[j] - th[i] > SPIKE_MAX_H:        # not back: never removed
                i += 1
                continue
            back = abs(vv[j] - m) <= SPIKE_TIGHT * a and th[j] - th[j - 1] <= SPIKE_STEP_H
            steady_after = bool((np.abs(vv[j:j + K] - m) <= SPIKE_TIGHT * a).all())
            block = vv[i:j]
            flat = (block.max() - block.min()) <= SPIKE_TIGHT * a
            if back and steady_after and (j - i == 1 or (a > SPIKE_BLOCK_M and flat)):
                bad[i:j] = True
                i = j
            else:
                i += 1
        if not bad.any():
            break
        out[keep[bad]] = True
        keep = keep[~bad]
    return out


# ── keying slips: a wrong digit on a steady river ────────────────────────
# The pass above needs readings an hour or so apart and a clean return. Two
# kinds of slip get past it, both found when its removals were checked
# against independent evidence (check_gauge_excursions.py, §13g):
#   - stretches with 3 readings a day (Tamen 370.80 for 270.80, Doimukh
#     188.63 for 118.63, Jollang 194.11 for 164.11) — at Doimukh and Tamen
#     the ONLY days ever "at the danger line" were these;
#   - wrong and right readings alternating (Pangin, 9 Aug 2019: 210.5 for
#     201.5 three times in four hours; Pasighat downstream shows the river
#     was at ~201.5).
# A reading is a keying slip only when ALL of these hold:
#   - the river is steady around it: the readings near it (up to 6 each
#     side, within 36 h) sit within SLIP_STEADY_M of their own middle value;
#   - it is more than SPIKE_SINGLE_M from that middle value;
#   - the river is back on both sides: one of the 2 readings before and one
#     of the 2 after are within SLIP_BACK_M of it — so the newest reading is
#     never judged, and a flood front (the readings after stay high) never is;
#   - undoing a slip explains it: with a multiple of 10 m added or taken
#     off, two neighbouring digits swapped back, or halved, the value lands
#     within SLIP_BACK_M of the middle. Or it is more than SPIKE_BLOCK_M
#     away, further than any of these rivers moves between two readings
#     that agree.
SLIP_SIDE = 6           # readings looked at on each side
SLIP_WINDOW_H = 36.0    # ... within this many hours
SLIP_STEADY_M = 0.5     # "steady": typical distance from the middle value
SLIP_BACK_M = 0.5       # "back" / "explained": this close to the middle value


def _undo_slips(x: float) -> list[float]:
    """The values `x` would be with one keying slip undone."""
    out = [x + s * 10.0 * k for k in range(1, 31) for s in (-1, 1)]
    whole, _, frac = f"{x:.2f}".partition(".")
    for i in range(len(whole) - 1):
        if whole[i] != whole[i + 1]:
            out.append(float(f"{whole[:i]}{whole[i + 1]}{whole[i]}{whole[i + 2:]}.{frac}"))
    out.append(x / 2.0)
    return out


def keying_slips(t: np.ndarray, v: np.ndarray) -> np.ndarray:
    """True for each reading that is a keying slip on a steady river. `t`
    (datetime64) must be sorted; blanks are never judged.

    Repeats until nothing more is found, so a short run of slips (3 readings
    of 134.8 for 143.8 at Namsai) goes whole, not just its middle. And the
    steady level a reading is judged against must itself be an ordinary
    level for this gauge (`_ordinary_levels`): in April 2018 Pangin's feed
    carried a second series 161 m too low that for a few days outnumbered
    the true one, and without this the TRUE readings were the ones removed."""
    out = np.zeros(len(v), bool)
    keep = np.flatnonzero(np.isfinite(v))
    if len(keep) < 5:
        return out
    body_lo, body_hi = _ordinary_levels(v[keep])
    for _ in range(20):
        tt, vv = t[keep], v[keep]
        n = len(vv)
        if n < 5:
            break
        th = (tt - tt[0]) / np.timedelta64(1, "h")
        bad = np.zeros(n, bool)
        # only readings far from their own neighbourhood are worth a closer look
        med13 = (pd.Series(vv).rolling(2 * SLIP_SIDE + 1, center=True, min_periods=5)
                 .median().to_numpy())
        for i in np.flatnonzero(np.abs(vv - med13) > SPIKE_SINGLE_M):
            lo, hi = max(0, i - SLIP_SIDE), min(n, i + 1 + SLIP_SIDE)
            before = vv[lo:i][(th[i] - th[lo:i]) <= SLIP_WINDOW_H]
            after = vv[i + 1:hi][(th[i + 1:hi] - th[i]) <= SLIP_WINDOW_H]
            if len(before) < 2 or len(after) < 2:
                continue
            nb = np.concatenate([before, after])
            m = float(np.median(nb))
            a = abs(vv[i] - m)
            if (a <= SPIKE_SINGLE_M or not body_lo <= m <= body_hi
                    or float(np.median(np.abs(nb - m))) > SLIP_STEADY_M):
                continue
            if not ((np.abs(before[-2:] - m) <= SLIP_BACK_M).any()
                    and (np.abs(after[:2] - m) <= SLIP_BACK_M).any()):
                continue
            explained = any(abs(c - m) <= SLIP_BACK_M for c in _undo_slips(float(vv[i])))
            if explained or a > SPIKE_BLOCK_M:
                bad[i] = True
        if not bad.any():
            break
        out[keep[bad]] = True
        keep = keep[~bad]
    return out


def daily_max(csv_path: Path) -> pd.Series:
    df = pd.read_csv(csv_path, parse_dates=["datetime"])
    df = clean_readings(df)
    df["date"] = df["datetime"].dt.date
    s = df.groupby("date")["level"].max()
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def derive_flood_days(daily: pd.Series) -> tuple[pd.DatetimeIndex, dict]:
    """Self-derived high-water days: top (1-FLOOD_PCTILE) of the record."""
    threshold = daily.quantile(FLOOD_PCTILE)
    flood_days = daily.index[daily >= threshold]

    # Cross-check only: annual-maxima Gumbel return level. Not used as the
    # operational label — too few annual maxima to trust alone (see docstring).
    annual_max = daily.groupby(daily.index.year).max()
    gumbel = {}
    if len(annual_max) >= 5:
        loc, scale = stats.gumbel_r.fit(annual_max.values)
        for t in (2, 5):
            gumbel[f"{t}yr_return_level"] = round(
                float(stats.gumbel_r.ppf(1 - 1 / t, loc, scale)), 2)
    return flood_days, {
        "percentile_threshold": round(float(threshold), 2),
        "n_annual_maxima": int(len(annual_max)),
        "gumbel_cross_check": gumbel,
    }


def trigger_series_at(lat: float, lon: float) -> pd.Series:
    """Daily rainfall-trigger score (mean pctile of r3, r7) at one point."""
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
    mons = (mo >= MONSOON[0]) & (mo <= MONSOON[1])

    scores = []
    for n in feats:
        a = np.load(FEAT / f"{n}.npy", mmap_mode="r")[:, cl].astype(np.float32)
        clim = a[mons]
        clim = clim[~np.isnan(clim)]
        pct = np.array([(clim < v).mean() if np.isfinite(v) else np.nan for v in a],
                        dtype=np.float32)
        scores.append(pct)
    trig = np.nanmean(np.vstack(scores), axis=0)
    return pd.Series(trig, index=dates, name="trigger"), cl


def backtest_station(code: str, meta: dict, trig: pd.Series) -> dict:
    csv_path = GAUGES / "cwc" / f"{code}_hhs.csv"
    daily = daily_max(csv_path)
    # Rollout, 2026-08-30: 13 of 18 stations DO have a published CWC danger
    # level now — use it when available (a real government-defined
    # threshold beats a self-derived proxy), fall back to the percentile
    # method only where none exists. train_flood_when.py's station_table()
    # already did this; backtest_station() hadn't, until now — same fix.
    #
    # Loose-end fix, 2026-08-30: 4 stations (Tuting, Pangin, Lemeking,
    # Namsai) have a real threshold that their ENTIRE recorded history never
    # once reaches — checked, it's real, not a data bug (each station's max
    # ever recorded sits a consistent 1-8 units below its own danger level).
    # A real, calm-river finding, not something to paper over — but it also
    # means "use the real threshold" silently produces zero usable training
    # labels for these 4. Falls back to the same self-derived proxy used for
    # stations with no threshold at all, same as those, clearly labelled so
    # it's never confused with an actual danger-level crossing.
    if meta.get("danger_level") is not None and (daily >= meta["danger_level"]).any():
        flood_days = daily.index[daily >= meta["danger_level"]]
        label_info = {"percentile_threshold": None, "n_annual_maxima": None,
                       "gumbel_cross_check": {},
                       "label_source": "CWC published danger level"}
    else:
        flood_days, label_info = derive_flood_days(daily)
        if meta.get("danger_level") is not None:
            label_info["label_source"] = ("self-derived (top 2% of own history) — "
                                           "real danger level never reached in this "
                                           f"station's full record, max {daily.max():.2f} "
                                           f"vs danger {meta['danger_level']:.2f}")
        else:
            label_info["label_source"] = "self-derived (top 2% of own history)"

    aligned = trig.reindex(daily.index)
    lagged = pd.concat([aligned.shift(d) for d in range(LAG_DAYS + 1)], axis=1).max(axis=1)

    is_flood = daily.index.isin(flood_days)
    valid = lagged.notna().to_numpy() & pd.Series(True, index=daily.index).to_numpy()
    y = is_flood[valid]
    s = lagged.to_numpy()[valid]

    if y.sum() == 0 or y.sum() == len(y):
        auc = None
    else:
        auc = round(float(roc_auc_score(y, s)), 3)

    ops = []
    for q in (0.75, 0.90, 0.95, 0.99):
        thr = np.nanquantile(s, q)
        flagged = s >= thr
        pct_days = round(100 * flagged.mean(), 1)
        pct_caught = round(100 * (flagged & y).sum() / max(y.sum(), 1), 1)
        ops.append({"trigger_pctile": q, "pct_monsoon_days_flagged": pct_days,
                     "pct_flood_days_caught": pct_caught})

    return {
        "station_code": code,
        "station_name": meta["name"],
        "n_daily_readings": int(len(daily)),
        "date_range": [str(daily.index.min().date()), str(daily.index.max().date())],
        "flood_day_label": {**label_info, "n_flood_days": int(len(flood_days))},
        "backtest": {
            "n_days_scored": int(valid.sum()),
            "auc_tie_corrected": auc,
            "operating_points": ops,
        },
        "_flood_days": [str(d.date()) for d in flood_days],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("Phase 1 — backtest the rainfall rule against self-derived flood-day labels\n")

    results = {}
    all_flood_rows = []
    skipped = []
    cell_cache: dict[tuple, tuple] = {}
    for code, meta in STATIONS.items():
        key = (meta["lat"], meta["lon"])
        if key not in cell_cache:
            try:
                cell_cache[key] = trigger_series_at(*key)
            except RuntimeError as exc:
                # A border-adjacent gauge (e.g. Bhalukpong, right on the
                # Assam boundary) can sit outside the IMERG-indexed grid
                # even though it's inside the project's bounding box — the
                # index is built against the state polygon, not the box.
                # Skip that one station rather than losing every other
                # station's result to it.
                print(f"  [skip] {meta['name']} ({code}): {exc}")
                skipped.append(code)
                cell_cache[key] = None
        if cell_cache[key] is None:
            continue
        trig, cl = cell_cache[key]

        print(f"  {meta['name']} ({code}) — IMERG cell {cl}")
        r = backtest_station(code, meta, trig)
        results[code] = r
        for d in r.pop("_flood_days"):
            all_flood_rows.append({"station_code": code, "station_name": meta["name"], "date": d})

        fd = r["flood_day_label"]
        bt = r["backtest"]
        thr = f" (threshold {fd['percentile_threshold']})" if fd['percentile_threshold'] else ""
        print(f"    {fd['label_source']}{thr}: "
              f"{fd['n_flood_days']} flood days out of {r['n_daily_readings']:,}")
        if fd["gumbel_cross_check"]:
            print(f"    Gumbel cross-check: {fd['gumbel_cross_check']}")
        print(f"    AUC (tie-corrected): {bt['auc_tie_corrected']}")
        for op in bt["operating_points"]:
            print(f"      trigger >= p{int(op['trigger_pctile']*100)}: "
                  f"{op['pct_monsoon_days_flagged']}% of days flagged, "
                  f"{op['pct_flood_days_caught']}% of flood days caught")
        print()

    pd.DataFrame(all_flood_rows).to_csv(OUT / "arunachal_flood_days.csv", index=False)
    print(f"  wrote {len(all_flood_rows)} flood-day labels -> "
          f"{OUT / 'arunachal_flood_days.csv'}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS / "flood_when_backtest_arunachal.json"
    report_path.write_text(json.dumps({
        "method": "CWC published danger level where available (13/18 stations); "
                  "self-derived top-2%-of-history label elsewhere — see "
                  "flood_stations.py for which is which per station",
        "station_location": "real per-station coordinates (layer-station-geo "
                             "endpoint) — see flood_stations.py",
        "n_stations": len(STATIONS),
        "skipped_stations": skipped,
        "stations": results,
    }, indent=2))
    print(f"  wrote {report_path}")


if __name__ == "__main__":
    main()
