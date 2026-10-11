"""How many times a usual day? Landslides against the rain score, measured.

    python scripts/model/check_landslide_times_usual.py

Writes  reports/landslide_times_usual.json
        webapp/assets/landslide/times_usual.json   (what the screen reads)

The place card used to headline "4 of 5" — a level's position on a scale,
not a measurement. This measures the number that can stand there: on days
when the rain was this unusual, how many times as common were dated
landslides as on a usual day at the same place? The rules for what may be
shown were fixed first: docs/design/LANDSLIDE_TIMES_USUAL.md.

The rain score is the app's own (core.rainfall.trigger_series) on the
Open-Meteo archive at the live run's points — the number the screen calls
"rain vs normal", so what is measured is what is shown.

⚠️ About 84 dated landslides. Every figure here comes with a 90% range, and
bands with fewer than 8 landslides are joined to a neighbour (R1).
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

ROOT_ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT_ / "scripts"), str(ROOT_ / "scripts" / "build"), str(ROOT_ / "webapp")]

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

import core.rainfall as RN
import grid as G
from common import INTERIM, LABELS, PROCESSED, ROOT

warnings.filterwarnings("ignore")
OM = INTERIM / "rainfall_om"
ASSETS = ROOT / "webapp" / "assets"
EDGES = [0.0, 0.50, 0.75, 0.90, 0.95, 1.0001]
MIN_N, N_BOOT = 8, 2000
LEVELS = ["Very Low", "Low", "Moderate", "High", "Very High"]
LEVEL_CUTS = np.array([0.02, 0.06, 0.15, 0.30])          # products.landslide.model.classify


def merge(edges: list[float], ev: np.ndarray, base_share) -> list[float]:
    """Join bands until each holds MIN_N landslides (R1) and the ratios rise (R2)."""
    edges = list(edges)
    while len(edges) > 2:
        n = np.histogram(ev, edges)[0]
        ratio = (n / max(n.sum(), 1)) / np.array([base_share(a, b) for a, b in zip(edges[:-1], edges[1:])])
        thin = [i for i in range(len(n)) if n[i] < MIN_N]
        if thin:
            i = thin[-1]                                   # the top band joins downward, others upward
            edges.pop(i if i == len(n) - 1 else i + 1)
            continue
        bad = [i for i in range(len(ratio) - 1) if ratio[i + 1] < ratio[i]]
        if bad:
            edges.pop(bad[0] + 1)
            continue
        break
    return edges


def table(edges, ev, base_share, rng) -> list[dict]:
    n = np.histogram(ev, edges)[0]
    shares = np.array([base_share(a, b) for a, b in zip(edges[:-1], edges[1:])])
    boot = np.array([np.histogram(rng.choice(ev, len(ev)), edges)[0] for _ in range(N_BOOT)]) / len(ev)
    lo, hi = np.quantile(boot / shares, [0.05, 0.95], axis=0)
    return [{"from": round(float(a), 4), "to": round(float(min(b, 1.0)), 4), "landslides": int(k),
             "share_of_days": round(float(s), 4), "share_of_landslides": round(float(k / len(ev)), 4),
             "times_usual": round(float(k / len(ev) / s), 3),
             "range_90": [round(float(x), 3), round(float(y), 3)]}
            for a, b, k, s, x, y in zip(edges[:-1], edges[1:], n, shares, lo, hi)]


def main() -> dict:
    print("Landslides against the rain score: times a usual day (LANDSLIDE_TIMES_USUAL.md)\n")
    P = np.load(OM / "precip_mm.npy").astype(np.float32)
    dates = pd.to_datetime(np.load(OM / "dates.npy", allow_pickle=True))
    app_pts = json.loads((ASSETS / "base" / "points.json").read_text())
    om_pts = json.loads((OM / "points.json").read_text())
    assert np.allclose(app_pts["lat"], om_pts["lat"]) and np.allclose(app_pts["lon"], om_pts["lon"]), \
        "the archive's points are not the app's points"
    qz = np.load(ASSETS / "base" / "clim_quantiles.npz")
    T = RN.trigger_series(P, {k: qz[k] for k in qz.files})          # the screen's "rain vs normal"
    plat, plon = np.asarray(app_pts["lat"]), np.asarray(app_pts["lon"])

    g = gpd.read_file(LABELS / "nasa-glc_landslides_point_arunachal.geojson")
    g["evdt"] = pd.to_datetime(g.ev_date, unit="ms", errors="coerce")
    g = g.dropna(subset=["evdt"]).to_crs(4326)
    elat, elon = g.geometry.y.to_numpy(), g.geometry.x.to_numpy()
    ej = np.argmin((elat[:, None] - plat[None, :]) ** 2
                   + ((elon[:, None] - plon[None, :]) * np.cos(np.radians(elat[:, None]))) ** 2, axis=1)
    dmap = {d: i for i, d in enumerate(dates)}
    et = np.array([dmap.get(pd.Timestamp(x.date()), -1) for x in g.evdt])
    ok = et >= 0
    ev_all = np.array([T[t, j] for t, j in zip(et[ok], ej[ok])])
    keep = np.isfinite(ev_all)
    ev = ev_all[keep]
    ev_dates = dates[et[ok][keep]]
    print(f"  {int(ok.sum())} dated landslides inside the archive's years, {len(ev)} with a rain score; "
          f"{dates[0].date()} .. {dates[-1].date()}, {P.shape[1]} points")

    fin = T[np.isfinite(T)]
    mons = np.asarray((dates.month >= 5) & (dates.month <= 10))
    fin_m = T[mons][np.isfinite(T[mons])]
    all_year = lambda a, b: float(((fin >= a) & (fin < b)).mean())
    monsoon = lambda a, b: float(((fin_m >= a) & (fin_m < b)).mean())
    rng = np.random.default_rng(0)

    edges = merge(EDGES, ev, all_year)
    rows = table(edges, ev, all_year, rng)
    ev_m = ev[np.asarray((ev_dates.month >= 5) & (ev_dates.month <= 10))]
    rows_m = table(edges, ev_m, monsoon, rng)
    for r, m in zip(rows, rows_m):
        r["monsoon_only_times_usual"] = m["times_usual"]
    print(f"\n  bands as fixed {EDGES[:-1]} -> after R1/R2: {[round(e, 2) for e in edges[:-1]]}")
    print(f"  {'rain score':<14}{'days':>8}{'landslides':>12}{'times usual':>13}{'90% range':>18}{'monsoon only':>14}")
    for r in rows:
        print(f"  {100*r['from']:>3.0f} to {100*r['to']:>3.0f}    {100*r['share_of_days']:>7.1f}%{r['landslides']:>12}"
              f"{r['times_usual']:>13.2f}{str(r['range_90']):>18}{r['monsoon_only_times_usual']:>14.2f}")

    # R4: the same by level (ground x rain), the ground read at the catalogue position
    with rasterio.open(PROCESSED / "susceptibility.tif") as s:
        sus = s.read(1)
    gu = g.to_crs(G.CRS)
    r_, c_ = G.xy_to_rowcol(gu.geometry.x.to_numpy(), gu.geometry.y.to_numpy())
    inb = (r_ >= 0) & (r_ < G.NROWS) & (c_ >= 0) & (c_ < G.NCOLS)
    esus = np.full(len(g), np.nan)
    esus[inb] = sus[r_[inb], c_[inb]]
    esus = esus[ok][keep]
    scored = np.isfinite(esus)
    ev_lvl = np.digitize(esus[scored] * ev[scored], LEVEL_CUTS)
    # the usual: every scored cell (a sample) on every day, with its own nearest point's score
    near = np.load(ASSETS / "landslide" / "nearest_point.npz")["near"]
    sus_d = np.load(ASSETS / "landslide" / "susceptibility.npz")["sus"]
    rr, cc_ = np.nonzero(sus_d != 255)
    pick = rng.choice(len(rr), 4000, replace=False)
    su, nj = sus_d[rr[pick], cc_[pick]] / 254.0, near[rr[pick], cc_[pick]]
    days_i = rng.choice(np.flatnonzero(np.isfinite(T).all(axis=1)), 1500, replace=False)
    hz = su[None, :] * T[np.ix_(days_i, nj)]
    base_lvl = np.bincount(np.digitize(hz.ravel(), LEVEL_CUTS), minlength=5) / hz.size
    n_lvl = np.bincount(ev_lvl, minlength=5)
    lvl_ratio = (n_lvl / max(n_lvl.sum(), 1)) / base_lvl
    bl = np.array([np.bincount(rng.choice(ev_lvl, len(ev_lvl)), minlength=5) for _ in range(N_BOOT)]) / len(ev_lvl)
    llo, lhi = np.quantile(bl / base_lvl, [0.05, 0.95], axis=0)
    lvl_rows = [{"level": LEVELS[i], "landslides": int(n_lvl[i]), "share_of_place_days": round(float(base_lvl[i]), 4),
                 "times_usual": round(float(lvl_ratio[i]), 2),
                 "range_90": [round(float(llo[i]), 2), round(float(lhi[i]), 2)]} for i in range(5)]
    r4 = bool((n_lvl[1:] >= MIN_N).all() and np.all(np.diff(lvl_ratio[1:]) > 0))
    print(f"\n  R4, by level ({int(scored.sum())} landslides on scored ground, of {len(ev)}):")
    for x in lvl_rows:
        print(f"    {x['level']:<10} landslides {x['landslides']:>3}  share of place-days {100*x['share_of_place_days']:>5.1f}%  "
              f"times usual {x['times_usual']:>6.2f}  90% range {x['range_90']}")
    print(f"  R4 (every level from Low up has {MIN_N}+ landslides and the numbers rise): {'PASS' if r4 else 'FAIL'}")

    met = json.loads((ASSETS / "landslide" / "metrics.json").read_text())
    out = {"what": ("how many times as common dated landslides were, by how unusual the rain was "
                    "(the app's rain score), against a usual day at the same place"),
           "method": "docs/design/LANDSLIDE_TIMES_USUAL.md §1 (rules fixed before the run)",
           "landslides": int(len(ev)), "source": "NASA Global Landslide Catalog, dated, inside Arunachal",
           "rain": f"Open-Meteo archive, {P.shape[1]} points, {dates[0].date()}..{dates[-1].date()}",
           "usual_day": "every day of the year at the point",
           "min_landslides_per_band": MIN_N, "bands_fixed": EDGES[:-1],
           "rain_bands": rows,
           "by_level": {"rows": lvl_rows, "landslides_on_scored_ground": int(scored.sum()),
                        "shown_on_screen": r4,
                        "why_not": None if r4 else "R4 failed: too few dated landslides per level, or the "
                                                   "numbers do not rise; the catalogue places a landslide "
                                                   "to about a kilometre"},
           "ground": [{"level": r["name"], "times_average_ground": round(r["lift"], 2),
                       "share_of_land": round(r["area_frac"], 3),
                       "share_of_mapped_landslides": round(r["slide_frac"], 3)}
                      for r in met["susceptibility"]["success_rate"]]}
    (ROOT / "reports" / "landslide_times_usual.json").write_text(json.dumps(out, indent=2))
    ship = {k: out[k] for k in ("what", "landslides", "source", "usual_day", "rain_bands", "ground")}
    ship["combined_shown"] = r4
    ship["levels"] = lvl_rows if r4 else None
    ship["levels_usual"] = "an average scored place on an average day"
    (ASSETS / "landslide" / "times_usual.json").write_text(json.dumps(ship, indent=1))
    print(f"\n  wrote reports/landslide_times_usual.json and the app's times_usual.json")
    return out


if __name__ == "__main__":
    main()
