"""Does the shipped flood map put water where water can actually go?

    python scripts/model/check_flood_where_sanity.py

Reads  data/processed/flood_where_prob_100m.tif
Writes reports/flood_where_sanity.json

════════════════════════════════════════════════════════════════════════════
WHY A SEPARATE CHECK, WHEN THE MODEL ALREADY HAS FOLD METRICS
════════════════════════════════════════════════════════════════════════════
Because the fold metrics cannot see this class of failure, and this project
has already been bitten by exactly it once.

Training rows are cells inside 10 km crops around real flood reports, so
they are overwhelmingly floodplain. Every validation fold is drawn from that
same population. A model can therefore score 0.95 on held-out folds and
still be nonsense on a Tawang ridge, because no fold ever asked it about a
ridge. That is not a subtle risk: with ESA WorldCover in the feature set,
the highest-scoring cells in Arunachal were glacial lakes at a median 360 m
above their nearest channel, and the fold metrics were the best we had seen.

The `_pre_landcover_drop` numbers in the output are that failure, kept as
the reference this check exists to catch.

So this asks the questions the folds cannot:

    1. How far above its own channel does the top-scoring ground sit?
       Water does not stand hundreds of metres above its own river.
    2. How steep is it? Standing water needs a floor, not a wall.
    3. Is the score monotone in HAND, the way hydrology requires?
    4. Does anything score high on snow, ice or glacial lake?

Nothing here is a model metric. These are physical facts the map must not
contradict, and a fail means the map is wrong however good the AUC looked.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))

import numpy as np
import rasterio

from common import INTERIM, PROCESSED, ROOT

STACK = INTERIM / "terrain_unmasked"
REPORTS = ROOT / "reports"
PROB = PROCESSED / "flood_where_prob_100m.tif"

# Thresholds a real flood map has to satisfy. These are hydrology, not taste.
MAX_MEDIAN_HAND_TOP = 25.0     # m above nearest channel, top 0.1% of cells
MAX_MEDIAN_SLOPE_TOP = 15.0    # degrees, top 0.1% of cells

LC_NAMES = {10: "tree cover", 20: "shrubland", 30: "grassland", 40: "cropland",
            50: "built-up", 60: "bare/sparse", 70: "snow and ice",
            80: "permanent water", 90: "herbaceous wetland", 95: "mangroves",
            100: "moss and lichen"}


def main() -> None:
    # --prob / --out check a candidate layer (e.g. the second-stage "shown"
    # chance, check_where_topend.py) without touching the shipped map's report
    prob_path, out_name = PROB, "flood_where_sanity.json"
    if "--prob" in sys.argv:
        prob_path = Path(sys.argv[sys.argv.index("--prob") + 1])
    if "--out" in sys.argv:
        out_name = sys.argv[sys.argv.index("--out") + 1]
    print(f"Flood WHERE — physical sanity of {prob_path.name}\n")
    with rasterio.open(prob_path) as s:
        P = s.read(1)
    lay = {}
    for n in ("hydro_hand_m", "hydro_hand_small_m", "terrain_slope_deg",
              "dem_elev_m", "hydro_chan_km2", "lc_class_cat"):
        with rasterio.open(STACK / f"{n}.tif") as s:
            lay[n] = s.read(1)

    ok = np.isfinite(P)
    # Height above the nearest drainage of ANY size — a village can be 30 m
    # above its own creek and 400 m above the trunk river; the creek is what
    # floods it, so the smaller of the two is the physically relevant number.
    hand = np.minimum(lay["hydro_hand_m"], lay["hydro_hand_small_m"])
    p, h, sl = P[ok], hand[ok], lay["terrain_slope_deg"][ok]
    elev, lc = lay["dem_elev_m"][ok], lay["lc_class_cat"][ok]

    k = max(1, int(0.001 * len(p)))
    top = np.argsort(p)[-k:]
    med_hand = float(np.median(h[top]))
    med_slope = float(np.median(sl[top]))
    med_elev = float(np.median(elev[top]))

    print(f"  top 0.1% of scored cells ({k:,} cells, score "
          f"{100*p[top].min():.1f}%-{100*p[top].max():.1f}%)")
    print(f"    median height above nearest channel  {med_hand:8.1f} m"
          f"   (limit {MAX_MEDIAN_HAND_TOP:.0f})")
    print(f"    median slope                         {med_slope:8.1f} deg"
          f" (limit {MAX_MEDIAN_SLOPE_TOP:.0f})")
    print(f"    median elevation                     {med_elev:8.0f} m")

    # Monotonicity is checked from 2 m upward, and the 0-2 m band is reported
    # but exempt. That band is mostly the channel bed and its lip, which is
    # already water in the dry baseline — and the label is NEW water, water
    # that was not there before. Permanent channel therefore cannot be a
    # positive by construction, which holds the 0-2 m mean down. The exemption
    # is a property of how the label is defined, not a tolerance for error.
    print("\n  is the score monotone in height above channel?")
    bands, prev, mono = [], None, True
    for lo, hi in [(0, 2), (2, 5), (5, 10), (10, 25), (25, 50), (50, 200), (200, 1e9)]:
        m = (h >= lo) & (h < hi)
        if m.sum() < 100:
            continue
        mp = float(p[m].mean())
        bands.append({"hand_lo": lo, "hand_hi": None if hi > 1e8 else hi,
                      "n": int(m.sum()), "mean_prob": mp})
        exempt = lo == 0
        if prev is not None and not exempt and mp > prev + 1e-6:
            mono = False
        if not exempt:
            prev = mp
        label = f"{lo}-{'inf' if hi > 1e8 else int(hi)}"
        note = "  (channel bed - exempt, see above)" if exempt else ""
        print(f"    HAND {label:>8} m   n={m.sum():>9,}   mean score {100*mp:6.2f}%{note}")
    print(f"    falls monotonically with height, above the channel bed: {mono}")

    print("\n  mean score by land cover (land cover is NOT a model input —"
          " this is a check, not a feature):")
    by_lc = []
    for c in np.unique(lc):
        m = lc == c
        if m.sum() < 100:
            continue
        by_lc.append({"class": int(c), "name": LC_NAMES.get(int(c), "?"),
                      "n": int(m.sum()), "mean_prob": float(p[m].mean())})
    for r in sorted(by_lc, key=lambda r: -r["mean_prob"]):
        print(f"    {r['name']:<18} n={r['n']:>9,}   mean score {100*r['mean_prob']:6.2f}%")

    frozen = [r for r in by_lc if r["class"] in (70, 100)]
    frozen_max = max((r["mean_prob"] for r in frozen), default=0.0)

    checks = {
        "top_cells_near_a_channel": med_hand <= MAX_MEDIAN_HAND_TOP,
        "top_cells_on_flat_ground": med_slope <= MAX_MEDIAN_SLOPE_TOP,
        "score_falls_with_height_above_channel": mono,
        "snow_and_tundra_score_low": frozen_max < 0.01,
    }
    print("\n  " + "-" * 62)
    for name, passed in checks.items():
        print(f"    {'PASS' if passed else 'FAIL'}  {name.replace('_',' ')}")
    verdict = all(checks.values())
    print(f"  {'-'*62}\n  overall: {'PASS' if verdict else 'FAIL'}")

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / out_name
    out.write_text(json.dumps({
        "note": ("Physical checks on the shipped statewide map. These catch "
                 "out-of-distribution failure, which fold metrics structurally "
                 "cannot - every fold comes from the same floodplain-heavy "
                 "population as training."),
        "top_0.1pct": {"n": int(k), "median_hand_m": med_hand,
                       "median_slope_deg": med_slope, "median_elev_m": med_elev},
        "limits": {"max_median_hand_m": MAX_MEDIAN_HAND_TOP,
                   "max_median_slope_deg": MAX_MEDIAN_SLOPE_TOP},
        "by_hand_band": bands, "by_landcover": by_lc,
        "checks": checks, "verdict": "PASS" if verdict else "FAIL",
        "_pre_landcover_drop": {
            "median_hand_m_of_top_cells": 360.0,
            "median_slope_deg_of_top_cells": 31.2,
            "note": ("the model WITH ESA WorldCover as a feature - half its "
                     "top-scoring cells were class 80 at 3,000 m, i.e. glacial "
                     "lakes read as river channel. Its held-out AUC was the "
                     "best of any variant tried (0.947 in Arunachal), which is "
                     "the whole reason this check exists"),
        },
    }, indent=2))
    print(f"\n  wrote {out}")
    sys.exit(0 if verdict else 1)


if __name__ == "__main__":
    main()
