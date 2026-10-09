"""The flood WHEN score for every rainfall cell on every day, not just at gauges.

    python scripts/model/when_grid.py          # build / refresh the cache

Writes  data/interim/flood_forecast/when_raw.npy     (days x 1,953 cells)
        data/interim/flood_forecast/when_dates.npy
        data/interim/flood_forecast/when_cells.json  (cell centre lat/lon)

WHEN was built and verified at 29 river gauges, but nothing in it is specific
to a gauge. Its inputs are the 3- and 7-day rainfall at a point, each turned
into a percentile of that same point's own monsoon history — so "how unusual
is this rain, for here". That is defined for any rainfall cell, which is what
lets WHEN be joined to WHERE across the whole state instead of only beside
the 29 gauges.

Only the no-size panel members are used: the plain rain rule, the pooled
NWDP tree and the transfer tree. The CWC pooled tree also wants the gauge's
catchment area, which an arbitrary rainfall cell does not have. Their blend is
a RANKING of days; `flood_forecast.py` maps it onto the probability of a
satellite-confirmed flood, so WHEN's own gauge calibrator is not used here.

The rainfall lookup is computed straight from the IMERG lattice rather than
from `imerg_index.tif`, because that raster is clipped to the state and most
of the flood evidence lies just across the line.
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from common import INTERIM, ROOT

RAIN = INTERIM / "rainfall"
OUT = INTERIM / "flood_forecast"
MODELS = ROOT / "models" / "flood_when"
# The lattice starts with the verified flood record (2003) since 2026-09-29;
# it started in 2015, with the first radar-screened news list. The rows from
# 2015 on are unchanged: every score is against each cell's own full-archive
# climatology (docs/design/OLDER_FLOODS_TEST.md). Every consumer aligned to
# when_dates is rebuilt with it: build_upstream_rain.py, build_gauge_reach.py.
START = "2003-01-01"


def lattice() -> dict:
    m = json.loads((RAIN / "_stack_meta.json").read_text())
    nlat, nlon = m["shape"][1], m["shape"][2]
    return {"nlat": nlat, "nlon": nlon, "lat_max": m["lat_max"],
            "lon_min": m["lon_min"], "deg": m["cell_deg"]}


def cell_of(lat, lon, lat_=None) -> np.ndarray:
    """(lat, lon) -> flat IMERG cell index, -1 outside the lattice. Same
    north-up row-major layout the stack was saved in."""
    L = lat_ or lattice()
    r = np.rint((L["lat_max"] - np.asarray(lat)) / L["deg"]).astype(int)
    c = np.rint((np.asarray(lon) - L["lon_min"]) / L["deg"]).astype(int)
    ok = (r >= 0) & (r < L["nlat"]) & (c >= 0) & (c < L["nlon"])
    return np.where(ok, r * L["nlon"] + c, -1)


def cell_centres() -> tuple[np.ndarray, np.ndarray]:
    L = lattice()
    k = np.arange(L["nlat"] * L["nlon"])
    return L["lat_max"] - (k // L["nlon"]) * L["deg"], L["lon_min"] + (k % L["nlon"]) * L["deg"]


def percentile_features() -> tuple[pd.DatetimeIndex, dict[str, np.ndarray]]:
    """r3 / r7 as each cell's own monsoon percentile — identical to
    `train_flood_when.features_at`, vectorised over all cells at once."""
    dates = pd.to_datetime(np.load(RAIN / "dates.npy").astype("datetime64[D]"))
    mons = (dates.month >= 5) & (dates.month <= 10)
    out = {}
    for n in ("r3", "r7"):
        a = np.load(RAIN / "features" / f"{n}.npy").astype(np.float32)
        pct = np.full(a.shape, np.nan, dtype=np.float32)
        for k in range(a.shape[1]):
            col = a[:, k]
            clim = np.sort(col[mons & np.isfinite(col)])
            if len(clim) == 0:
                continue
            fin = np.isfinite(col)
            # searchsorted 'left' == share of history strictly below v,
            # exactly the (clim < v).mean() the WHEN models were trained on
            pct[fin, k] = np.searchsorted(clim, col[fin], side="left") / len(clim)
        out[n] = pct
    return dates, out


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print("WHEN score on the full rainfall lattice")
    dates, f = percentile_features()
    lag = np.vstack([np.full((1, f["r3"].shape[1]), np.nan, np.float32),
                     ((f["r3"] + f["r7"]) / 2)[:-1]])
    keep = dates >= pd.Timestamp(START)
    r3, r7, lag = f["r3"][keep], f["r7"][keep], lag[keep]
    dates = dates[keep]
    n_days, n_cells = r3.shape
    print(f"  {n_days:,} days x {n_cells:,} cells, {dates.min().date()} -> {dates.max().date()}")

    with open(MODELS / "B_pooled_nwdp_all.pkl", "rb") as fh:
        b = pickle.load(fh)
    with open(MODELS / "C_bigriver_naive_DIAGNOSTIC_ONLY_005-UBDDIB.pkl", "rb") as fh:
        c = pickle.load(fh)

    X = pd.DataFrame({"r3": r3.ravel(), "r7": r7.ravel(), "trigger_lag1": lag.ravel()})
    ok = X[["r3", "r7"]].notna().all(axis=1).to_numpy()
    raw = np.full(len(X), np.nan, dtype=np.float32)
    rule = X[["r3", "r7"]].mean(axis=1).to_numpy()
    pb = b.predict_proba(X[ok])[:, 1]
    pc = c.predict_proba(X[ok])[:, 1]
    raw[ok] = ((rule[ok] + pb + pc) / 3).astype(np.float32)
    raw = raw.reshape(n_days, n_cells)
    print(f"  scored {ok.sum():,} cell-days, median {np.nanmedian(raw):.3f}")

    np.save(OUT / "when_raw.npy", raw)
    np.save(OUT / "when_dates.npy", dates.to_numpy().astype("datetime64[D]"))
    lat, lon = cell_centres()
    (OUT / "when_cells.json").write_text(json.dumps(
        {"lat": lat.round(3).tolist(), "lon": lon.round(3).tolist(), **lattice()}))
    print(f"  wrote {OUT / 'when_raw.npy'}")


def load() -> tuple[pd.DatetimeIndex, np.ndarray]:
    return (pd.to_datetime(np.load(OUT / "when_dates.npy")),
            np.load(OUT / "when_raw.npy", mmap_mode="r"))


if __name__ == "__main__":
    build()
