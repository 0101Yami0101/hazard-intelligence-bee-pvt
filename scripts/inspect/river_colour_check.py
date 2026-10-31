"""RC: does Sentinel-2 river colour track CWC's measured river mud? Assam, 2017-2026.

    $env:REGION = "assam"; python scripts/inspect/river_colour_check.py

The test and its bars were written before fetching (EROSION_PLAN.md, "RC part 1"):
    date      >= 20 water pixels in the station's 300 m circle (NDWI > 0, not cloud etc.)
    match     the same day's CWC reading (mean if more than one)
    RC1       per station with >= 20 matches, Spearman(red B4, mud): median >= 0.50, > 0 at >= 80%
    RC2       the same on seasonal percentiles (same month +-1, per station): median >= 0.30
    RC3       clear Jun-Sep dates per station-year, median (>= 3 needed to feed a WHEN model)
    reported  SCL-water variant, B4/B3, monsoon-only rho, matches per station

Sentinel-2's processing baseline 04.00 (from 2022-01-25) adds 1000 to L2A values. If the
archive still carries it (a jump in the stations' dry-season water values), it is removed.

Outputs: reports/river_colour_check_<region>.json, data/processed/<region>/river_colour.parquet
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import AOI_NAME, GAUGES, INTERIM, PROCESSED, ROOT

warnings.filterwarnings("ignore")

RC = INTERIM / "river_colour"
SED = GAUGES / "cwc_sediment"
ASSAM_FILES = ("08cf3a3a-c6e5-4c7a-871d-28861a3f8b88", "b809cd25-a40b-495c-91b3-67137963e542")
VAL = "Manual Daily Suspended Sediments (g/L)"
MIN_PX, MIN_MATCH = 20, 20
BARS = {"RC1_median": 0.50, "RC1_share_positive": 0.80, "RC2_median": 0.30, "RC3_monsoon_dates": 3}
OFFSET_DAY = pd.Timestamp("2022-01-25")


def colour(variant: str) -> pd.DataFrame:
    names = list(gpd.read_file(RC / "stations.geojson").Station)
    rows = []
    for f in sorted(RC.glob(f"{variant}_*.json")):
        for day, vals in json.loads(f.read_text()).items():
            for st, v in zip(names, vals):
                if v and v[3] and v[3] >= MIN_PX and v[0] is not None and v[2] is not None:
                    rows.append((st, pd.Timestamp(day[:10]), float(v[0]), float(v[2]), int(v[3])))
    d = pd.DataFrame(rows, columns=["station", "t", "b3", "b4", "px"])
    return d.groupby(["station", "t"], as_index=False).agg(b3=("b3", "median"), b4=("b4", "median"), px=("px", "max"))


def offset_jump(d: pd.DataFrame) -> float:
    """Median over stations of (Feb-Apr 2022 minus Feb-Apr 2021) dry-season water red values."""
    j = []
    for _, g in d.groupby("station"):
        a = g[(g.t >= "2021-02-01") & (g.t < "2021-05-01")].b4
        b = g[(g.t >= "2022-02-01") & (g.t < "2022-05-01")].b4
        if len(a) >= 3 and len(b) >= 3:
            j.append(b.median() - a.median())
    return float(np.median(j)) if j else np.nan


def mud() -> pd.DataFrame:
    m = pd.concat([pd.read_csv(SED / f"{r}.csv", dtype=str) for r in ASSAM_FILES])
    m["t"] = pd.to_datetime(m["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce").dt.normalize()
    m["v"] = pd.to_numeric(m[VAL], errors="coerce")
    m = m.dropna(subset=["t", "v"])
    return m[m.v >= 0].groupby(["Station", "t"], as_index=False).v.mean().rename(columns={"Station": "station", "v": "mud"})


def seasonal_pct(df: pd.DataFrame, col: str) -> pd.Series:
    out = pd.Series(np.nan, index=df.index)
    for _, g in df.groupby("station"):
        mo = g.t.dt.month.to_numpy()
        v = g[col].to_numpy()
        for m_ in range(1, 13):
            pool = v[np.isin(mo, [(m_ - 2) % 12 + 1, m_, m_ % 12 + 1])]
            sel = mo == m_
            if len(pool) >= 5 and sel.any():
                out.loc[g.index[sel]] = [(pool < x).mean() + 0.5 * (pool == x).mean() for x in v[sel]]
    return out


def rho(J: pd.DataFrame, x: str, y: str, sel=None) -> dict:
    out = {}
    for st, g in J.groupby("station"):
        g = g if sel is None else g[sel(g)]
        g = g[[x, y]].dropna()
        if len(g) >= MIN_MATCH:
            out[st] = round(float(spearmanr(g[x], g[y]).correlation), 3)
    return out


def score(variant: str, M: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    d = colour(variant)
    jump = offset_jump(d)
    fixed = bool(np.isfinite(jump) and jump > 500)
    if fixed:
        d.loc[d.t >= OFFSET_DAY, ["b3", "b4"]] -= 1000
    d["ratio"] = d.b4 / d.b3.where(d.b3 > 0)
    J = d.merge(M, on=["station", "t"], how="inner").reset_index(drop=True)
    J["b4_pct"], J["mud_pct"] = seasonal_pct(J, "b4"), seasonal_pct(J, "mud")
    r1, r2 = rho(J, "b4", "mud"), rho(J, "b4_pct", "mud_pct")
    mons = d[d.t.dt.month.between(6, 9)]
    per_sy = mons.groupby(["station", mons.t.dt.year]).size()
    # station-years with no clear monsoon date count as 0
    sy = pd.MultiIndex.from_product([d.station.unique(), range(2017, 2026)])
    per_sy = per_sy.reindex(sy, fill_value=0)
    res = {"variant": variant, "clear_dates": int(len(d)), "offset_jump_dn": round(jump, 1), "offset_removed": fixed,
           "matched_days": {k: int(v) for k, v in J.groupby("station").size().items()},
           "RC1_rho": r1, "RC1_median": round(float(np.median(list(r1.values()))), 3) if r1 else None,
           "RC1_share_positive": round(float(np.mean(np.array(list(r1.values())) > 0)), 3) if r1 else None,
           "RC2_rho": r2, "RC2_median": round(float(np.median(list(r2.values()))), 3) if r2 else None,
           "RC3_monsoon_dates_median": float(per_sy.median()),
           "RC3_monsoon_dates_by_year": {int(y): float(per_sy.xs(y, level=1).median()) for y in range(2017, 2026)},
           "ratio_rho_median": round(float(np.median(list(rho(J, "ratio", "mud").values()))), 3) if r1 else None,
           "monsoon_rho_median": (lambda r: round(float(np.median(list(r.values()))), 3) if r else None)(
               rho(J, "b4", "mud", lambda g: g.t.dt.month.between(6, 9))),
           "stations_scored": len(r1)}
    return res, J


def main() -> None:
    print(f"River colour vs river mud — {AOI_NAME}")
    M = mud()
    main_res, J = score("ndwi", M)
    alt, _ = score("scl", M)
    main_res["RC1_pass"] = bool(main_res["RC1_median"] is not None and main_res["RC1_median"] >= BARS["RC1_median"]
                                and main_res["RC1_share_positive"] >= BARS["RC1_share_positive"])
    main_res["RC2_pass"] = bool(main_res["RC2_median"] is not None and main_res["RC2_median"] >= BARS["RC2_median"])
    main_res["RC3_enough_for_WHEN"] = bool(main_res["RC3_monsoon_dates_median"] >= BARS["RC3_monsoon_dates"])
    rep = {"region": AOI_NAME, "bars": BARS, "main": main_res,
           "scl_variant": {k: alt[k] for k in ("clear_dates", "RC1_median", "RC1_share_positive", "RC2_median",
                                               "RC3_monsoon_dates_median", "stations_scored")}}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    J.to_parquet(PROCESSED / "river_colour.parquet")
    (ROOT / "reports" / f"river_colour_check_{AOI_NAME}.json").write_text(json.dumps(rep, indent=2))
    show = {k: v for k, v in main_res.items() if not isinstance(v, dict)}
    print(json.dumps(show, indent=1))
    print("  RC1 per station:", main_res["RC1_rho"])
    print("  RC2 per station:", main_res["RC2_rho"])
    print("  SCL variant:", rep["scl_variant"])


if __name__ == "__main__":
    main()
