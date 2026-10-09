"""The flood forecast: WHEN and WHERE joined into one number per place per day.

    python scripts/model/flood_forecast.py fit            # fit the day model
    python scripts/model/flood_forecast.py 2024-07-03     # forecast one date

════════════════════════════════════════════════════════════════════════════
THE NUMBER, IN ONE LINE
════════════════════════════════════════════════════════════════════════════
    P(this 100 m patch floods today)
        =  P(a flood happens in this ~10 km area today)      <- the DAY model
        x  P(the water reaches this patch | a flood here)    <- WHERE

WHERE is the calibrated terrain model (train_flood_where.py). The day model
is new, and it exists because WHEN's own probability is the wrong event:
WHEN was calibrated to "this gauge crosses its danger level", while WHERE's
events are satellite-confirmed flood reports. Multiplying probabilities of
two different events gives a number that means nothing. So the WHEN score is
re-mapped here onto the SAME event WHERE was trained on — a reported flood,
confirmed by Sentinel-1, centred in this rainfall cell on this day — so the
two halves multiply cleanly.

The day model sees two things:
    how unusual today's rain is here      the WHEN score (rain rule + trees)
    how much floodable ground is here     sum of WHERE over the rain cell

The second matters because a rain cell that is 30% Brahmaputra floodplain
floods far more often than one that is all ridge, for the same rain. It is
taken from terrain, not from where floods were REPORTED in the past, so that
a thinly-populated valley that nobody writes news about is not told it never
floods.

Since 2026-09-28, FLAT rain cells (mean slope < 5°) also see a third thing:
how wet the top metre of soil already was, 16 days before the day (ERA5-Land).
On plains and valley floors soaked ground floods sooner; on steep ground it
made the forecast worse, so it is not used there. See FlatSoilDayModel and
docs/design/SOIL_WETNESS_TEST.md.

════════════════════════════════════════════════════════════════════════════
WHAT THE NUMBER DOES NOT COUNT
════════════════════════════════════════════════════════════════════════════
Only floods that someone reported AND a satellite then confirmed. Floods that
went unreported, or that happened under cloud between satellite passes, are
not in the record, so the true chance is higher than this number. It is a
floor, not an estimate of every wet day — and the "times normal" figure,
which divides that bias out, is the more robust thing to act on.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from rasterio.warp import Resampling, reproject
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.isotonic import IsotonicRegression

import grid as G
import when_grid
from common import INTERIM, PROCESSED, ROOT

OUT = INTERIM / "flood_forecast"
MODELS = ROOT / "models" / "flood_forecast"
CELL_KM2 = (G.CELL / 1000) ** 2

# The last day the flood record can say "no flood". The record (Groundsource
# reports, confirmed by Sentinel-1) has 17 floods in Oct 2025, then 2 in Jan
# 2026 and none after — it simply stops. A day after this with no record is
# not a flood-free day, it is an unknown one, so nothing is fitted or graded
# on it. Until 2026-09-27 the day model's calibration (2024-2026) and the
# replays (to 2026-07-29) counted Feb-Jul 2026 — a whole monsoon — as dry.
TRUTH_END = pd.Timestamp("2025-10-31")

# The first year the day model's tree learns from. 2015 until 2026-09-29;
# since then 2003, the verified record's first year. Its 326 floods from
# 2003-2014 (Global Flood Database confirmations of news reports) passed a
# pre-registered test: timing +0.020 across the window and +0.028 inside
# Arunachal, near-here ranking held (docs/design/OLDER_FLOODS_TEST.md §2, §5b).
# Production and the test copies whose figures the screen quotes use it; the
# older tests keep their own years, as run.
TREE_FROM = 2003
# Each rain cell's "ordinary day" level (normal_daily_prob.npy) stays the
# mean over the days it always covered, so moving TREE_FROM changes the
# model, not the yardstick.
NORMAL_FROM = pd.Timestamp("2015-01-01")

DAY_PARAMS = dict(max_depth=3, max_iter=200, learning_rate=0.05,
                  monotonic_cst=[1, 1], random_state=42)


# ── the rain lattice on the 100 m grid, unclipped ────────────────────────
def imerg_index_full() -> np.ndarray:
    """100 m cell -> flat rain-cell index, over the whole grid window. The
    shipped imerg_index.tif is clipped to the state; this is the same
    nearest-neighbour mapping without the clip."""
    path = OUT / "imerg_index_full.tif"
    if path.exists():
        with rasterio.open(path) as s:
            return s.read(1)
    L = when_grid.lattice()
    idx = np.arange(L["nlat"] * L["nlon"], dtype=np.int32).reshape(L["nlat"], L["nlon"])
    lon0 = L["lon_min"] - L["deg"] / 2
    lat0 = L["lat_max"] + L["deg"] / 2
    src_tf = Affine(L["deg"], 0, lon0, 0, -L["deg"], lat0)
    dst = np.full(G.SHAPE, -1, dtype=np.int32)
    reproject(source=idx, destination=dst, src_transform=src_tf, src_crs="EPSG:4326",
              dst_transform=G.TRANSFORM, dst_crs=G.CRS, src_nodata=-1, dst_nodata=-1,
              resampling=Resampling.nearest)
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=G.NROWS, width=G.NCOLS,
                       count=1, dtype="int32", crs=G.CRS, transform=G.TRANSFORM,
                       nodata=-1, compress="deflate") as d:
        d.write(dst, 1)
    return dst


def exposure(where: np.ndarray, kidx: np.ndarray, n_cells: int) -> np.ndarray:
    """Per rain cell: expected flooded area in km2 GIVEN a flood there,
    i.e. the sum of WHERE over its 100 m cells. NaN where the rain cell has
    no terrain at all."""
    ok = np.isfinite(where) & (kidx >= 0)
    tot = np.bincount(kidx[ok], weights=where[ok].astype(np.float64), minlength=n_cells)
    has = np.bincount(kidx[ok], minlength=n_cells) > 0
    return np.where(has, tot * CELL_KM2, np.nan)


# ── the flood record, as (day, rain cell) events ─────────────────────────
def load_events() -> pd.DataFrame:
    """Every satellite-confirmed flood report, with its date and rain cell."""
    from build_flood_where_samples import SOURCE_REPORTS
    rows = {}
    for name in SOURCE_REPORTS:
        d = json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))
        for r in d["results"]:
            if r.get("screen_positive") and r["uuid"] not in rows:
                rows[r["uuid"]] = {"uuid": r["uuid"], "date": r["date_str"],
                                   "lat": r["lat"], "lon": r["lon"]}
    ev = pd.DataFrame(rows.values())
    ev["date"] = pd.to_datetime(ev["date"])
    ev["k"] = when_grid.cell_of(ev["lat"].to_numpy(), ev["lon"].to_numpy())
    return ev


# The flood record the day model learns from and is graded on. "verified"
# since 2026-09-28: events some independent route confirms (the validated
# radar test, Google's Global Flood Database, a gauge crossing) —
# build_verified_floods.py, PARKED §0x. Until then it was every news report
# that passed a radar screen which, tested later, filters out almost nothing
# (§0w). Graded on verified floods, training on the verified record picked
# the right weeks better (inside Arunachal 0.747 vs 0.726, region 0.758 vs
# 0.715) at the same ranking (reports/flood_near_here_train_on_which.json).
TRAIN_RECORD = "verified"


def training_events() -> pd.DataFrame:
    """The record TRAIN_RECORD names, as (uuid, date, lat, lon, k) events,
    braided-channel-shift suspects excluded either way."""
    if TRAIN_RECORD == "verified":
        ev = pd.read_parquet(INTERIM / "flood_events" / "verified_events.parquet")
        ev["date"] = pd.to_datetime(ev["date"])
        ev["k"] = when_grid.cell_of(ev["lat"].to_numpy(), ev["lon"].to_numpy())
        return ev[["uuid", "date", "lat", "lon", "k"]].reset_index(drop=True)
    sus = set(json.loads((ROOT / "reports" / "flood_paddy_check.json").read_text())
              ["channel_shift_suspects"]["uuids"])
    ev = load_events()
    return ev[~ev["uuid"].isin(sus)].reset_index(drop=True)


def label_matrix(ev: pd.DataFrame, dates: pd.DatetimeIndex, n_cells: int) -> np.ndarray:
    Y = np.zeros((len(dates), n_cells), dtype=np.uint8)
    pos = pd.Series(np.arange(len(dates)), index=dates)
    e = ev[(ev["k"] >= 0) & ev["date"].isin(dates)]
    Y[pos[e["date"]].to_numpy(), e["k"].to_numpy()] = 1
    return Y


# ── the day model ────────────────────────────────────────────────────────
class DayModel:
    """P(confirmed flood centred in this rain cell today | rain, terrain).
    A monotone tree ranks, then an isotonic curve fitted on LATER years maps
    the rank onto observed frequency — the calibration never sees the years
    the tree learned from."""

    def __init__(self, tree, iso, optional=()):
        self.tree, self.iso = tree, iso
        # indices into F of inputs that may be missing (NaN), e.g. the gauge
        # reading, which only cells with a gauge upstream have; the tree
        # routes a missing value itself
        self.optional = tuple(optional)

    @staticmethod
    def _complete(X: np.ndarray, optional) -> np.ndarray:
        need = [j for j in range(X.shape[1]) if j not in set(optional)]
        return np.isfinite(X[:, need]).all(axis=1)

    @staticmethod
    def design(F, E: np.ndarray) -> np.ndarray:
        """F: one (days, cells) array, or a list of them — the day features
        (local WHEN score, and optionally upstream rain percentiles)."""
        F = [F] if isinstance(F, np.ndarray) else list(F)
        shape = np.shape(F[0])
        cols = [np.asarray(f, dtype=np.float32).ravel() for f in F]
        cols.append(np.broadcast_to(np.log1p(np.asarray(E, dtype=np.float32)), shape).ravel())
        return np.column_stack(cols)

    @classmethod
    def fit(cls, F, E, Y, day_mask_tree, day_mask_cal, optional=()):
        F = [F] if isinstance(F, np.ndarray) else list(F)
        cells = np.isfinite(E)
        def rows(mask):
            f = [x[mask][:, cells] for x in F]
            y = Y[mask][:, cells]
            X = cls.design(f, E[cells][None, :])
            ok = cls._complete(X, optional)
            return X[ok], y.ravel()[ok]
        Xt, yt = rows(day_mask_tree)
        params = dict(DAY_PARAMS, monotonic_cst=[1] * (len(F) + 1))
        tree = HistGradientBoostingClassifier(**params).fit(Xt, yt)
        Xc, yc = rows(day_mask_cal)
        iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso.fit(tree.predict_proba(Xc)[:, 1], yc)
        return cls(tree, iso, optional), {"n_tree_rows": int(len(yt)), "n_tree_pos": int(yt.sum()),
                                "n_cal_rows": int(len(yc)), "n_cal_pos": int(yc.sum())}

    def predict(self, F, E: np.ndarray) -> np.ndarray:
        """F: day features as in design(), each (..., n_cells); E: (n_cells,)."""
        F = [F] if isinstance(F, np.ndarray) else list(F)
        shape = np.shape(F[0])
        X = self.design(F, np.broadcast_to(E, shape))
        out = np.full(len(X), np.nan, dtype=np.float32)
        ok = self._complete(X, getattr(self, "optional", ()))
        if ok.any():
            out[ok] = self.iso.predict(self.tree.predict_proba(X[ok])[:, 1])
        return out.reshape(shape)


def years(dates: pd.DatetimeIndex, lo: int, hi: int) -> np.ndarray:
    return np.asarray((dates.year >= lo) & (dates.year <= hi))


def known(dates: pd.DatetimeIndex) -> np.ndarray:
    """Days the flood record covers (see TRUTH_END)."""
    return np.asarray(dates <= TRUTH_END)


def day_features(W: np.ndarray, upstream: bool) -> list[np.ndarray]:
    """The day model's rain inputs, aligned to when_dates: local WHEN score,
    plus — when `upstream` — the 3- and 7-day upstream-catchment rain
    percentiles from build_upstream_rain.py."""
    if not upstream:
        return [W]
    u = np.load(OUT / "upstream_rain_pct.npz")
    return [W, u["up_r3"], u["up_r7"]]


# ── soil wetness on flat ground ──────────────────────────────────────────
# How wet the top metre of soil already is adds flood-timing skill where
# water collects — flat rain cells (mean slope < 5°: plains, valley floors) —
# and costs skill on steep ground, where a flood is a flash flood from one
# downpour and the soil is soaked all monsoon anyway. So flat cells take the
# chance from a day model that also sees soil wetness; every other cell keeps
# the rain-only chance. Soil is read SOIL_LAG days before the day forecast:
# ERA5-Land runs ~9 days behind, so t-16 exists for every day of a 7-day
# outlook, and the model is trained at that same lag. Pre-registered and
# tested in docs/design/SOIL_WETNESS_TEST.md §6-§8 (15/30-day rain and soil
# on all terrain both failed there; landslides gained nothing).
SOIL_LAG = 16
SOIL_ARCHIVE = INTERIM / "soil_wetness" / "era5land_lattice.npz"
SOIL_DEPTH_CM = (7.0, 21.0, 72.0)          # ERA5-Land layers 0-7, 7-28, 28-100 cm
SOIL_QS = np.linspace(0, 1, 1001)
FLAT_CLASS = 0                              # SLOPE_CLASS_NAMES[0], mean slope < 5°


def soil_top_metre(swv1, swv2, swv3) -> np.ndarray:
    """Depth-weighted volumetric soil water of the top metre."""
    a, b, c = SOIL_DEPTH_CM
    return ((a * np.asarray(swv1) + b * np.asarray(swv2) + c * np.asarray(swv3))
            / (a + b + c)).astype(np.float32)


def soil_archive() -> tuple[pd.DatetimeIndex, np.ndarray]:
    """Top-metre soil water, every day since 2000-06-01, every rain cell
    (scripts/fetch/fetch_39_era5land_soil.py)."""
    z = np.load(SOIL_ARCHIVE)
    return pd.to_datetime(z["dates"]), soil_top_metre(z["swv1"], z["swv2"], z["swv3"])


def soil_breaks(dates: pd.DatetimeIndex, soil: np.ndarray) -> np.ndarray:
    """Each cell's May-October soil-water quantiles, in 0.1% steps."""
    m = np.asarray((dates.month >= 5) & (dates.month <= 10))
    return np.nanquantile(soil[m], SOIL_QS, axis=0).astype(np.float32)


def soil_input(dates, src_dates=None, src: np.ndarray | None = None) -> np.ndarray:
    """The soil input for each day in `dates`: top-metre soil water on day
    t - SOIL_LAG, as that cell's own monsoon percentile. Read from `src`
    (days x cells, e.g. the live fetch), else the archive. NaN where that day
    is missing; flat cells then fall back to rain only."""
    if src is None:
        src_dates, src = soil_archive()
    br = np.load(MODELS / "soil_breaks.npy")
    pct = np.full(src.shape, np.nan, dtype=np.float32)
    for j in range(src.shape[1]):
        b = br[:, j]
        if not np.isfinite(b).all():
            continue
        ok = np.isfinite(src[:, j])
        pct[ok, j] = np.searchsorted(b, src[ok, j], side="left") / (len(b) - 1)
    pos = pd.Series(np.arange(len(src_dates)), index=pd.DatetimeIndex(src_dates))
    at = pos.reindex(pd.DatetimeIndex(dates) - pd.Timedelta(days=SOIL_LAG))
    out = np.full((len(at), src.shape[1]), np.nan, dtype=np.float32)
    ok = at.notna().to_numpy()
    out[ok] = pct[at[ok].astype(int).to_numpy()]
    return out


def flat_cells(n_cells: int) -> np.ndarray:
    f = MODELS / "terrain_class.npy"
    cls = np.load(f) if f.exists() else terrain_class(imerg_index_full(), n_cells)
    return cls == FLAT_CLASS


class FlatSoilDayModel:
    """The production day model: `base` (rain only) for every cell, and on
    flat cells `soil` — the same model with the soil input added — wherever
    that day's soil exists."""

    def __init__(self, base: DayModel, soil: DayModel, flat: np.ndarray):
        self.base, self.soil = base, soil
        self.flat = np.asarray(flat, dtype=bool)

    def predict(self, F, E: np.ndarray, soil: np.ndarray | None) -> np.ndarray:
        """`soil` is required on purpose: None means "no soil today", said
        out loud, never forgotten."""
        P = self.base.predict(F, E)
        if soil is None or not self.flat.any():
            return P
        F = [F] if isinstance(F, np.ndarray) else list(F)
        c = self.flat
        Ps = self.soil.predict([np.asarray(f)[..., c] for f in F] + [np.asarray(soil)[..., c]],
                               np.asarray(E)[c])
        sub = P[..., c]
        ok = np.isfinite(Ps)
        sub[ok] = Ps[ok]
        P[..., c] = sub
        return P


def predict_day(model, F, E: np.ndarray, soil: np.ndarray | None) -> np.ndarray:
    """Chance per rain cell per day from the production day model. `soil` =
    soil_input() for the same days, or None when there is none. A rain-only
    DayModel (before 2026-09-28) ignores it."""
    if isinstance(model, FlatSoilDayModel):
        return model.predict(F, E, soil)
    return model.predict(F, E)


def fit_day_model(F, E, Y, day_mask_tree, day_mask_cal,
                  dates: pd.DatetimeIndex) -> tuple[FlatSoilDayModel, dict]:
    """Both halves fitted the same way. Production and every test copy use
    this, so the tests measure what ships."""
    F = [F] if isinstance(F, np.ndarray) else list(F)
    base, info = DayModel.fit(F, E, Y, day_mask_tree, day_mask_cal)
    soil, sinfo = DayModel.fit(F + [soil_input(dates)], E, Y, day_mask_tree, day_mask_cal)
    return FlatSoilDayModel(base, soil, flat_cells(len(E))), {**info, "soil_model": sinfo}


# ── the mountain-valley correction ───────────────────────────────────────
# WHERE answers "given a flood within ~5 km, does it reach this patch"; the
# join applies it across a whole ~10 km rain cell. A mountain rain cell holds
# several separate valleys and a flood down one leaves the others dry, so the
# raw product over-counts. One factor per terrain class of rain cell - the
# share of its floodable ground a typical flood really reaches - fixes the
# total. Chosen over a finer split by the 2023-26 replay
# (replay_flood_forecast.py, section 3b).
SLOPE_CLASS_EDGES = [5.0, 15.0]
SLOPE_CLASS_NAMES = ["flat (<5 deg)", "hilly (5-15 deg)", "steep (>=15 deg)"]


def terrain_class(kidx: np.ndarray, n_cells: int) -> np.ndarray:
    with rasterio.open(INTERIM / "terrain_unmasked" / "terrain_slope_deg.tif") as s:
        slope = s.read(1)
    ok = (kidx >= 0) & np.isfinite(slope)
    tot = np.bincount(kidx[ok], weights=slope[ok].astype(np.float64), minlength=n_cells)
    n = np.bincount(kidx[ok], minlength=n_cells)
    mean = np.where(n > 0, tot / np.maximum(n, 1), 0.0)
    return np.digitize(mean, SLOPE_CLASS_EDGES)


def wet_patches(evs: pd.DataFrame, where: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(row, col) of every patch confirmed flooded, one per patch per day."""
    from pyproj import Transformer
    from build_flood_where_samples import COVER_MIN, POS_FRAC, event_grid
    to3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_utm = Transformer.from_crs("EPSG:3857", G.CRS, always_xy=True)
    by_day: dict = {}
    for _, e in evs.iterrows():
        f = INTERIM / "flood_where_pixels" / f"{e['uuid']}.npz"
        if not f.exists():
            continue
        g = event_grid(f, to3857, to_utm)
        if g is None:
            continue
        r0, c0, frac, cover = g[:4]
        h, w = frac.shape
        wet = ((cover >= COVER_MIN) & (frac >= POS_FRAC)
               & np.isfinite(where[r0:r0 + h, c0:c0 + w]))
        rr, cc = np.nonzero(wet)
        by_day.setdefault(e["date"], set()).update(zip((rr + r0).tolist(), (cc + c0).tolist()))
    rc = np.asarray([x for s_ in by_day.values() for x in s_], dtype=int).reshape(-1, 2)
    return rc[:, 0], rc[:, 1]


def correction_factors(P, where, kidx, cls, ev, dates, lo, hi, share: float = 1.0) -> np.ndarray:
    """Per terrain class: observed / expected flooded patch-days over the
    years lo..hi — record days only (TRUTH_END), on both sides."""
    n_cells = P.shape[1]
    Hs = np.where(np.isfinite(where) & (kidx >= 0), where, 0.0)
    A = np.bincount(kidx[kidx >= 0], weights=Hs[kidx >= 0].astype(np.float64),
                    minlength=n_cells)
    ps = np.nansum(P[years(dates, lo, hi) & known(dates)], axis=0)
    exp_ = np.bincount(cls, weights=A * ps, minlength=3) * share
    rows, cols = wet_patches(ev[(ev["date"].dt.year >= lo) & (ev["date"].dt.year <= hi)
                                & (ev["date"] <= TRUTH_END)], where)
    k = kidx[rows, cols]
    obs = np.bincount(cls[k[k >= 0]], minlength=3)
    return np.where(exp_ > 0, obs / np.maximum(exp_, 1e-9), 1.0)


# ── production fit + daily forecast ──────────────────────────────────────
def fit_production() -> None:
    from predict_flood_where import score_grid
    print(f"Day model — production fit (tree {TREE_FROM}-2023, calibration 2024-01-01.."
          f"{TRUTH_END.date()}, the end of the flood record)")
    dates, W = when_grid.load()
    W = np.asarray(W)
    kidx = imerg_index_full()
    where, _ = score_grid(clip_to_state=False, verbose=False)
    E = exposure(where, kidx, W.shape[1])
    # The braided-channel-shift suspects (check_paddy_labels.py, §0n) are left
    # out: water that appears because the river moved, with no rain behind
    # it, is not a flood. The replay (§0o) showed the cleaned day model
    # catches the same floods with far fewer alarms.
    ev = training_events()
    Y = label_matrix(ev, dates, W.shape[1])
    # Local + upstream-catchment rain: the 2023-26 replay measured it better
    # on timing (fair timing AUC 0.851 vs 0.841; at the 10x-normal level it
    # catches more floods while warning less). See PARKED doc §0m.
    F = day_features(W, upstream=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    cls = terrain_class(kidx, W.shape[1])
    np.save(MODELS / "terrain_class.npy", cls)
    # Soil wetness on flat cells (SOIL_WETNESS_TEST.md §7-§8): each cell's
    # monsoon soil scale first, so training and the daily run score soil alike.
    sd, soil_raw = soil_archive()
    np.save(MODELS / "soil_breaks.npy", soil_breaks(sd, soil_raw))
    S = soil_input(dates, sd, soil_raw)
    model, info = fit_day_model(F, E, Y, years(dates, TREE_FROM, 2023),
                                years(dates, 2024, 2026) & known(dates), dates)
    with open(MODELS / "day_model.pkl", "wb") as fh:
        pickle.dump(model, fh)
    np.save(MODELS / "exposure_km2.npy", E)
    # Each rain cell's ordinary level, for the "times normal" figure: its mean
    # daily chance from NORMAL_FROM on — the days it has always covered.
    P = predict_day(model, F, E, S)
    np.save(MODELS / "normal_daily_prob.npy",
            np.nanmean(P[np.asarray(dates >= NORMAL_FROM)], axis=0))
    # Observed flooded patches come from the events that HAVE a water map;
    # the day model's chance covers every event in the record. Scale the
    # expected side to the share that have one, or the factor reads low.
    import glob as _glob
    have = {Path(f).stem for f in _glob.glob(str(INTERIM / "flood_where_pixels" / "*.npz"))}
    win = ev[(ev["date"].dt.year >= 2021) & (ev["date"] <= TRUTH_END)]
    share = float(win["uuid"].isin(have).mean()) if len(win) else 1.0
    factor = correction_factors(P, where, kidx, cls, ev, dates, 2021, 2026, share)
    np.save(MODELS / "valley_factor.npy", factor)
    (MODELS / "_meta.json").write_text(json.dumps({
        "event": (f"a flood from the {TRAIN_RECORD} record (build_verified_floods.py: "
                  "confirmed by the validated radar test, Google's Global Flood Database "
                  "or a gauge crossing), centred in the ~10 km rain cell, on its date"),
        "valley_factor_mask_share": round(share, 3),
        "tree_years": f"{TREE_FROM}-2023",
        "tree_years_note": ("2015-2023 until 2026-09-29; from the verified record's first "
                            "year since (docs/design/OLDER_FLOODS_TEST.md)"),
        "normal_days": f"{NORMAL_FROM.date()} on",
        "calibration_days": f"2024-01-01..{TRUTH_END.date()} (the flood record ends there; "
                            "before 2026-09-27 this ran to 2026-07-29 and counted Feb-Jul "
                            "2026 as flood-free)", **info,
        "day_features": ["WHEN local score", "upstream 3-day rain pct",
                         "upstream 7-day rain pct", "log floodable km2"],
        "soil_wetness": {
            "design": (f"flat rain cells (mean slope < 5 deg, {int((cls == FLAT_CLASS).sum())} "
                       "cells) use a second day model that also sees top-metre soil water on "
                       f"day t-{SOIL_LAG}, as the cell's own May-Oct percentile; every other "
                       "cell, and any day without soil data, uses the rain-only model"),
            "source": "ECMWF/ERA5_LAND/DAILY_AGGR via Earth Engine (fetch_39_era5land_soil.py)",
            "lag_days": SOIL_LAG,
            "tested": "docs/design/SOIL_WETNESS_TEST.md §6-§8 (reports/soil_wetness_test.json)"},
        "n_events": int(Y.sum()),
        "excluded": "braided-channel-shift suspects (reports/flood_paddy_check.json)",
        "valley_factor": dict(zip(SLOPE_CLASS_NAMES, map(float, factor))),
        "valley_factor_days": f"2021-01-01..{TRUTH_END.date()}",
        "replay": "reports/flood_forecast_replay.json",
    }, indent=2))
    print(f"  {info}")
    for n_, f_ in zip(SLOPE_CLASS_NAMES, factor):
        print(f"  valley factor {n_:<18} {f_:.3f}")
    print(f"  wrote {MODELS}")


def forecast(date: str) -> None:
    dates, W = when_grid.load()
    d = pd.Timestamp(date)
    if d not in dates:
        raise SystemExit(f"{d.date()} is outside the rainfall archive "
                         f"({dates.min().date()} - {dates.max().date()})")
    i = int(np.where(dates == d)[0][0])
    with open(MODELS / "day_model.pkl", "rb") as fh:
        model = pickle.load(fh)
    E = np.load(MODELS / "exposure_km2.npy")
    normal = np.load(MODELS / "normal_daily_prob.npy")
    F = day_features(np.asarray(W), upstream=True)
    p_day = predict_day(model, [f[i][None, :] for f in F], E, soil_input(dates[i:i + 1]))[0]
    times = p_day / normal
    reach = np.load(MODELS / "valley_factor.npy")[np.load(MODELS / "terrain_class.npy")]

    with rasterio.open(PROCESSED / "flood_where_prob_100m.tif") as s:
        where = s.read(1)
    kidx = imerg_index_full()
    ok = np.isfinite(where) & (kidx >= 0)
    combined = np.full(G.SHAPE, np.nan, dtype=np.float32)
    combined[ok] = where[ok] * (p_day * reach)[kidx[ok]]

    out = PROCESSED / f"flood_forecast_{d.date()}.tif"
    with rasterio.open(out, "w", driver="GTiff", height=G.NROWS, width=G.NCOLS,
                       count=1, dtype="float32", crs=G.CRS, transform=G.TRANSFORM,
                       nodata=np.nan, compress="deflate") as dst:
        dst.write(combined, 1)

    with rasterio.open(INTERIM / "state_mask.tif") as m:
        instate = m.read(1).astype(bool)
    in_cells = np.unique(kidx[instate & (kidx >= 0)])
    lat, lon = when_grid.cell_centres()
    # Rank areas by how much ground is expected under water today, not by
    # "times normal" alone: a ridge-top rain cell with no floodable ground can
    # be 15x its (tiny) normal and still put nothing at risk.
    sel = instate & ok
    today_km2 = np.bincount(kidx[sel], weights=combined[sel].astype(np.float64),
                            minlength=len(p_day)) * CELL_KM2
    top = sorted(in_cells, key=lambda k: -today_km2[k])[:10]
    summary = {
        "date": str(d.date()),
        "means": ("per 100 m patch: chance a reported, satellite-confirmed flood "
                  "puts water on it today. A floor - unreported floods are not "
                  "in the record, and inside Arunachal the replay found the "
                  "absolute level still runs ~3x high; 'times normal' is the "
                  "robust read"),
        "expected_flooded_km2_in_state": float(np.nansum(combined[instate]) * CELL_KM2),
        "normal_expected_flooded_km2_in_state": float(np.nansum(
            (where * (normal * reach)[np.clip(kidx, 0, None)])[sel]) * CELL_KM2),
        "areas_most_ground_at_risk": [
            {"lat": round(float(lat[k]), 2), "lon": round(float(lon[k]), 2),
             "expected_flooded_km2_today": round(float(today_km2[k]), 4),
             "times_normal": round(float(times[k]), 1),
             "floodable_km2": round(float(E[k]), 1)} for k in top],
    }
    js = ROOT / "reports" / f"flood_forecast_{d.date()}.json"
    js.write_text(json.dumps(summary, indent=2))
    ratio = summary["expected_flooded_km2_in_state"] / max(
        summary["normal_expected_flooded_km2_in_state"], 1e-9)
    print(f"Flood forecast {d.date()}: expected flooded ground in Arunachal "
          f"{summary['expected_flooded_km2_in_state']:.2f} km2 "
          f"({ratio:.1f}x an ordinary day)")
    for a in summary["areas_most_ground_at_risk"][:5]:
        print(f"  {a['lat']:.2f},{a['lon']:.2f}  {a['expected_flooded_km2_today']:>7.3f} km2 at risk"
              f"   {a['times_normal']:>5.1f}x normal")
    print(f"  wrote {out}\n  wrote {js}")


if __name__ == "__main__":
    # Run through the module, not __main__, so the pickled DayModel records
    # `flood_forecast.DayModel` and can be loaded from anywhere else.
    import flood_forecast as _ff
    arg = sys.argv[1] if len(sys.argv) > 1 else "fit"
    _ff.fit_production() if arg == "fit" else _ff.forecast(arg)
