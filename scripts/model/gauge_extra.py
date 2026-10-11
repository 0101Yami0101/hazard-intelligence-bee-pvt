"""Three more things a gauge forecast can read, built to cure the "river above
its line told ~0%" fault (docs/design/FLOOD_WHEN_PILOT_PLAN.md §17).

    U   the gauge upstream        upstream_inputs()
    M   melt water                melt_inputs()
    LV  the level line sets the   lv_chances() / fit_lv()
        chance when the river
        is already high

    add_inputs()   train_flood_when_gauge / gauge_week tables with U and M
                   added, row for row

Nothing reads this module in the live run until the test of §17 says what
is kept (scripts/model/check_gauge_fix.py) and the user says go.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import pandas as pd
from scipy.special import expit, logit
from sklearn.linear_model import LogisticRegression

import train_flood_when_gauge as T
from common import INTERIM

# ── U: the gauge upstream ────────────────────────────────────────────────
# Each gauge's river, km2 at its placed spot on the 100 m flow raster
# (webapp/assets/flood/gauge_link.json, river_km2), for the gauges in a chain.
RIVER_KM2 = {"002-ubddib": 4331, "003-UBDDIB": 8819, "003NEID-3": 15924, "005-UBDDIB": 18126,
             "004-UBDDIB": 11284, "020-UBDDIB": 15114, "008-ubddib": 2441, "009-UBDDIB": 2634,
             "027-UBDDIB": 3632, "029-UBDDIB": 8966, "078-UBDDIB": 828, "058-UBDDIB": 1212,
             "Sagalee_1": 634, "002Neid3": 842, "001NEID3": 2926, "059-UBDDIB": 127,
             "Tengapani Bridge_1": 203}
# gauge -> the gauges upstream of it on the same flow path, nearest first,
# each at least a quarter of its size (§17a). Traced 2026-10-10 by walking
# down the flow raster from every gauge's placed spot.
UPSTREAM = {
    "003-UBDDIB": ["002-ubddib"],                     # Yinkiang <- Tuting
    "003NEID-3": ["003-UBDDIB", "002-ubddib"],        # Pangin <- Yinkiang, Tuting
    "005-UBDDIB": ["003NEID-3", "003-UBDDIB"],        # Passighat <- Pangin, Yinkiang
    "020-UBDDIB": ["004-UBDDIB"],                     # Daporizo <- Lemeking
    "009-UBDDIB": ["008-ubddib"],                     # Namsai <- Miao
    "029-UBDDIB": ["027-UBDDIB"],                     # Bhalukpong <- Seppa
    "058-UBDDIB": ["078-UBDDIB", "Sagalee_1"],        # Doimukh <- Pare HEP, Sagalee
    "078-UBDDIB": ["Sagalee_1"],                      # Pare HEP <- Sagalee
    "001NEID3": ["002Neid3"],                         # Rho Basti <- Murga Bridge
    "Tengapani Bridge_1": ["059-UBDDIB"],             # Tengapani Bridge <- Pagoda
}
U_FEATS = ["up_frac", "up_rise1", "up_rise3", "up_share"]
M_FEATS = ["melt7", "swe", "temp7"]
FREE = {"up_rise1", "up_rise3", "up_share", "melt7", "swe", "temp7"}   # no direction rule
MELT_LAG = 16                    # days before the target day, as the soil input (SOIL_LAG)
MELT = INTERIM / "snow_melt" / "era5land_melt_lattice.npz"
Z_CLIP = 5.0


def upstream_inputs(stations: list[dict], registry: dict) -> dict[str, pd.DataFrame]:
    """Per gauge with a gauge upstream: the four inputs indexed by DAY (not
    yet shifted to a target day). A day's values all come from ONE upstream
    gauge — the nearest that has a reading that day — so a rise never mixes
    two gauges' levels."""
    daily = {s["code"]: s["daily"] for s in stations}
    out = {}
    for code, ups in UPSTREAM.items():
        if code not in registry:
            continue
        parts = []
        for u in ups:
            if u not in registry or u not in daily:
                continue
            sc = registry[u]
            f = ((daily[u] - sc["base"]) / (sc["threshold"] - sc["base"])).asfreq("D")
            d = pd.DataFrame({"up_frac": f, "up_rise1": f - f.shift(1), "up_rise3": f - f.shift(3),
                              "up_share": RIVER_KM2[u] / RIVER_KM2[code]})
            d.loc[f.isna().to_numpy()] = np.nan          # no reading that day: nothing from this gauge
            parts.append(d)
        if not parts:
            continue
        df = parts[0]
        for p in parts[1:]:
            idx = df.index.union(p.index)
            df, p = df.reindex(idx), p.reindex(idx)
            take = (df["up_frac"].isna() & p["up_frac"].notna()).to_numpy()
            df = df.copy()
            df.loc[take] = p.loc[take]
        out[code] = df[U_FEATS]
    return out


def melt_inputs(registry: dict, archive: Path = MELT) -> dict[str, pd.DataFrame]:
    """Per gauge: melt water over the last 7 days, snow lying and the week's
    mean temperature, averaged over the area draining to the gauge inside
    the map — indexed by the day they describe."""
    z = np.load(archive)
    dates = pd.to_datetime(z["dates"])
    W = np.load(INTERIM / "flood_forecast" / "upstream_weights.npz")["W"]
    out = {}
    for code, st in registry.items():
        w = np.nan_to_num(W[st["cell"]].astype(np.float64))
        if w.sum() <= 0:
            w = np.zeros(W.shape[1])
            w[st["cell"]] = 1.0
        w = w / w.sum()
        melt = pd.Series(z["melt_mm"].astype(np.float64) @ w, index=dates)
        out[code] = pd.DataFrame({
            "melt7": melt.rolling(7, min_periods=7).sum(),
            "swe": pd.Series(z["swe_mm"].astype(np.float64) @ w, index=dates),
            "temp7": pd.Series(z["temp_c"].astype(np.float64) @ w, index=dates)
                       .rolling(7, min_periods=7).mean()})[M_FEATS]
    return out


def add_inputs(tables: dict[int, pd.DataFrame], stations: list[dict], registry: dict,
               melt: dict | None = None) -> dict[int, pd.DataFrame]:
    """The gauge tables, row for row, with U as it stood `lead` days before
    the target day and M as it stood MELT_LAG days before it."""
    up = upstream_inputs(stations, registry)
    melt = melt_inputs(registry) if melt is None else melt
    empty_u = pd.DataFrame(columns=U_FEATS, dtype=float)
    out = {}
    for L, tb in tables.items():
        parts = []
        for code, g in tb.groupby("station_code", sort=False):
            u = up.get(code, empty_u).shift(L) if code in up else empty_u
            parts.append(g.join(u, on="date").join(melt[code].shift(MELT_LAG), on="date"))
        out[L] = pd.concat(parts).sort_index()
        assert out[L].index.equals(tb.index)
    return out


# ── LV: the level line sets the chance when the river is high ────────────
def level_z(now: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Where the line (1.0 in the gauge's own units) sits in the level
    model's range: above 0, the middle of the range is over the line; +1,
    over it by the whole width of the range. `q` is low / middle / high of
    the CHANGE in the day's high."""
    width = np.maximum(q[:, 2] - q[:, 0], 1e-3)
    return np.clip((now + q[:, 1] - 1.0) / width, -Z_CLIP, Z_CLIP)


def fit_lv(raw: np.ndarray, z: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """(a, c, b) of chance = S-curve(a x log-odds of the score + c x z + b).
    Neither a nor c may be negative: an input whose fitted number is
    negative is dropped and the other refitted; if both would be, the
    group's flat rate."""
    s = logit(np.clip(raw, T.EPS, 1 - T.EPS))

    def fit(cols):
        lr = LogisticRegression(C=np.inf, max_iter=2000).fit(np.column_stack(cols), y)
        return [float(v) for v in lr.coef_[0]], float(lr.intercept_[0])
    (a, c), b = fit([s, z])
    if a >= 0 and c >= 0:
        return a, c, b
    if c < 0:
        (a,), b = fit([s])
        if a >= 0:
            return a, 0.0, b
    else:
        (c,), b = fit([z])
        if c >= 0:
            return 0.0, c, b
    return 0.0, 0.0, float(logit(np.clip(y.mean(), T.EPS, 1 - T.EPS)))


def apply_lv(p: tuple, raw: np.ndarray, z: np.ndarray) -> np.ndarray:
    a, c, b = p
    return expit(a * logit(np.clip(raw, T.EPS, 1 - T.EPS)) + c * z + b)


def calibrate_lv(raw, z, y, g) -> dict:
    """T.calibrate(by="state") with the two river-above groups' S-curve given
    its second input. A group too thin for it keeps what calibrate gives."""
    cals = T.calibrate(raw, y, g, "state")
    lv = {}
    for k in (1, 3):
        m = (g == k) & np.isfinite(z)
        if y[m].sum() >= 20:
            lv[k] = fit_lv(raw[m], z[m], y[m])
    return {"curves": cals, "lv": lv}


def apply_cal_lv(c: dict, raw, z, g) -> np.ndarray:
    out = T.apply_cal(c["curves"], raw, g)
    for k, p in c["lv"].items():
        m = (g == k) & np.isfinite(z)
        if m.any():
            out[m] = apply_lv(p, raw[m], z[m])
    return out


def lv_chances(df: pd.DataFrame, z: np.ndarray) -> np.ndarray:
    """Out-of-fold chance with LV: `df` carries each row's raw out-of-fold
    score, group and year-fold (check_gauge_retrain.scored); the curves are
    fitted on the other folds, as T.oof does."""
    y, raw = df["flood"].to_numpy(), df["raw"].to_numpy()
    g, f = df["grp"].to_numpy(), df["fold"].to_numpy()
    p = np.full(len(df), np.nan)
    for k in range(T.N_FOLDS):
        tr, te = f != k, f == k
        p[te] = apply_cal_lv(calibrate_lv(raw[tr], z[tr], y[tr], g[tr]), raw[te], z[te], g[te])
    return p
