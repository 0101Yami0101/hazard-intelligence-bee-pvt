"""First real empirical check of the static WHERE layer — does the map's
predicted risk class actually track where water showed up on real flood
days?

    python scripts/model/calibrate_flood_where.py

Reuses every satellite check already run this session (Jang's 12 dates,
the 9-station statewide pass, the 12 NWDP stations) — the raw scenes are
still on disk, so this recomputes each real water mask (no new downloads)
and, for the first time, overlays it against `webapp/assets/flood/
floodprone.npz`, the actual shipped static risk map, instead of just
reporting a summary percentage per event.

Output:
    reports/flood_where_calibration.json
    data/interim/flood_when/where_calibration_overlay.png

════════════════════════════════════════════════════════════════════════════
WHAT THIS IS AND ISN'T
════════════════════════════════════════════════════════════════════════════
This is a real, honest first pass — not the finished WHERE calibration
described in the plan doc §10's "remaining limits." ~30 events, mostly one
per station, is a genuinely small sample for a spatial reliability curve
(WHEN's calibration used tens of thousands of station-days; this has a few
thousand pixels across ~30 scenes, and those pixels within one scene are
highly correlated with each other — they are not ~30x(window size)
independent samples). Reported with that caveat throughout, the same
discipline used everywhere else in this project.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from rasterio.transform import from_bounds
from rasterio.windows import from_bounds as window_from_bounds

from common import INTERIM, ROOT
from flood_stations import STATIONS as CWC_STATIONS
from nwdp_stations import STATIONS as NWDP_STATIONS
import sentinel1_flood_evidence as jang
import sentinel1_flood_evidence_statewide as statewide
import sentinel1_flood_evidence_nwdp as nwdp
import sentinel1_flood_evidence_loose_ends as loose_ends

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetch"))
import fetch_25_sentinel1_statewide_expand as expand

OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"
FLOODPRONE = ROOT / "webapp" / "assets" / "flood" / "floodprone.npz"
GRID_JSON = ROOT / "webapp" / "assets" / "base" / "grid.json"
CLASS_NAMES = ["nodata", "Very Low", "Low", "Moderate", "High", "Very High"]


def build_event_list() -> list[dict]:
    """Every (station, date, orbit, lat, lon) already scored by the three
    satellite passes this session — same scenes, same stations, no new
    fetches."""
    events = []
    for date, orbit in jang.DATE_ORBIT.items():
        events.append({"station": "Jang valley (Murga Bridge/Rho Basti)",
                        "date": date, "orbit": orbit,
                        "lat": jang.JANG_LAT, "lon": jang.JANG_LON,
                        "flood_stem": jang.FLOOD_SCENES[date],
                        "baseline_stem": jang.BASELINE_BY_ORBIT[orbit]})
    for code, (date, stem, orbit) in statewide.TARGETS.items():
        meta = CWC_STATIONS[code]
        events.append({"station": meta["name"], "date": date, "orbit": orbit,
                        "lat": meta["lat"], "lon": meta["lon"],
                        "flood_stem": stem,
                        "baseline_stem": statewide.BASELINE_BY_ORBIT[orbit]})
    for code, (date, stem, orbit) in nwdp.TARGETS.items():
        meta = NWDP_STATIONS[code]
        events.append({"station": meta["name"], "date": date, "orbit": orbit,
                        "lat": meta["lat"], "lon": meta["lon"],
                        "flood_stem": stem,
                        "baseline_stem": nwdp.BASELINE_BY_ORBIT[orbit]})
    for code, (date, stem, orbit, _note) in loose_ends.TARGETS.items():
        meta = CWC_STATIONS[code]
        events.append({"station": meta["name"], "date": date, "orbit": orbit,
                        "lat": meta["lat"], "lon": meta["lon"],
                        "flood_stem": stem,
                        "baseline_stem": loose_ends.BASELINE_BY_ORBIT[orbit]})

    # The 35-date expansion (fetch_25_sentinel1_statewide_expand.py) didn't
    # record scene stems in its report — re-resolve them here the same way
    # it originally found them (a metadata search, not a re-download; every
    # scene is already cached locally so this costs one cheap CDSE query
    # per event, no bandwidth).
    expanded_path = REPORTS / "flood_where_s1_statewide_expanded.json"
    if expanded_path.exists():
        expanded = json.loads(expanded_path.read_text())["results"]
        tok = None
        for r in expanded:
            code, date, orbit = r["station_code"], r["flood_date"], r["orbit"]
            meta = CWC_STATIONS[code]
            prod = expand.find_scene_for_date(meta["lat"], meta["lon"], date)
            if prod is None:
                print(f"  [skip] {meta['name']} {date}: could not re-resolve scene stem")
                continue
            stem = prod["Name"].removesuffix(".zip") if prod["Name"].endswith(".zip") else prod["Name"]
            if orbit not in expand._baseline_scene_by_orbit:
                # a dry-season baseline was found for this orbit during the
                # original run but never persisted anywhere except stdout —
                # re-find it the same way (deterministic query, and the
                # scene is already cached locally so this doesn't re-download)
                if tok is None:
                    import fetch_14_sentinel as f14
                    tok = f14.token()
                expand.ensure_baseline(orbit, meta["lat"], meta["lon"], tok)
            base_stem = expand._baseline_scene_by_orbit.get(orbit)
            if base_stem is None:
                print(f"  [skip] {meta['name']} {date}: no baseline found for orbit {orbit}")
                continue
            events.append({"station": meta["name"], "date": date, "orbit": orbit,
                            "lat": meta["lat"], "lon": meta["lon"],
                            "flood_stem": stem, "baseline_stem": base_stem})
    return events


def load_floodprone():
    cls = np.load(FLOODPRONE)["cls"]
    g = json.loads(GRID_JSON.read_text())
    transform = from_bounds(g["west"], g["south"], g["east"], g["north"], g["width"], g["height"])
    return cls, transform, g


def sample_floodprone(cls: np.ndarray, transform, grid_bounds, res_deg: float) -> np.ndarray:
    """The predicted risk class at every pixel of one event's water-mask
    grid — same shape as the event grid, nearest-neighbour sampled from the
    coarser (596x1227, ~5-6 km) static layer onto the finer (~11 m) mask."""
    w, s, e, n = grid_bounds
    width = int(round((e - w) / res_deg))
    height = int(round((n - s) / res_deg))
    lons = w + (np.arange(width) + 0.5) * res_deg
    lats = n - (np.arange(height) + 0.5) * res_deg
    cols = ((lons - transform.c) / transform.a).astype(int)
    rows = ((lats - transform.f) / transform.e).astype(int)
    cols = np.clip(cols, 0, cls.shape[1] - 1)
    rows = np.clip(rows, 0, cls.shape[0] - 1)
    return cls[rows[:, None], cols[None, :]]


def main() -> None:
    print("First empirical check: does the static WHERE map track real flood water?\n")
    cls, transform, g = load_floodprone()
    events = build_event_list()
    print(f"{len(events)} already-scanned satellite events to reuse (no new downloads)\n")

    # class -> [n_water_pixels, n_total_pixels], pooled across every event
    totals = {c: [0, 0] for c in range(6)}
    per_event = []

    for ev in events:
        try:
            fmeta = jang.scene_meta(ev["flood_stem"])
            bmeta = jang.scene_meta(ev["baseline_stem"])
            flood_db = jang.read_calibrated_window(fmeta, lat=ev["lat"], lon=ev["lon"], buf_deg=0.15)
            base_db = jang.read_calibrated_window(bmeta, lat=ev["lat"], lon=ev["lon"], buf_deg=0.15)
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] {ev['station']} {ev['date']}: {type(exc).__name__}: {str(exc)[:100]}")
            continue

        valid = (flood_db > -59.0) & (base_db > -59.0)
        new_water = (flood_db < jang.WATER_DB_THRESHOLD) & ~(base_db < jang.WATER_DB_THRESHOLD) & valid

        gb = (ev["lon"] - 0.15, ev["lat"] - 0.15, ev["lon"] + 0.15, ev["lat"] + 0.15)
        risk = sample_floodprone(cls, transform, gb, jang.GRID_RES_DEG)

        ev_counts = {}
        for c in range(6):
            m = (risk == c) & valid
            n_tot = int(m.sum())
            n_water = int((m & new_water).sum())
            totals[c][0] += n_water
            totals[c][1] += n_tot
            if n_tot:
                ev_counts[c] = {"n": n_tot, "water": n_water}
        per_event.append({"station": ev["station"], "date": ev["date"], "by_class": ev_counts})
        print(f"  {ev['station']:<28}{ev['date']:<14}"
              f"pixels-with-new-water: {int(new_water.sum()):>6,} / {int(valid.sum()):>7,}")

    print(f"\n{len(per_event)}/{len(events)} events processed successfully "
          f"(some are duplicate scenes across nearby stations, expected)\n")

    print(f"{'predicted class':<16}{'pixels':>12}{'showed water':>14}{'observed rate':>16}")
    reliability = []
    for c in range(6):
        n_water, n_tot = totals[c]
        rate = 100 * n_water / n_tot if n_tot else None
        reliability.append({"class": c, "class_name": CLASS_NAMES[c],
                             "n_pixels": n_tot, "n_showed_water": n_water,
                             "observed_water_rate_pct": round(rate, 3) if rate is not None else None})
        rate_s = f"{rate:.3f}%" if rate is not None else "n/a"
        print(f"{CLASS_NAMES[c]:<16}{n_tot:>12,}{n_water:>14,}{rate_s:>16}")

    scored = [r for r in reliability if r["class"] > 0 and r["n_pixels"] > 0]
    monotonic = all(scored[i]["observed_water_rate_pct"] <= scored[i + 1]["observed_water_rate_pct"]
                     for i in range(len(scored) - 1)) if len(scored) > 1 else None

    print(f"\nRises monotonically Very Low -> Very High? {monotonic}")
    print("(that is the one thing a risk RANKING needs to be true before it can be "
          "calibrated into a probability at all - a real reliability CURVE, matched "
          "to real percentages, needs far more than ~30 events)")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_where_calibration.json"
    out.write_text(json.dumps({
        "note": ("First empirical overlay of real satellite flood-water evidence "
                 "against the static WHERE risk map. NOT a finished spatial "
                 "calibration - ~30 events is small for a spatial reliability "
                 "curve, and pixels within one event's scene are correlated with "
                 "each other, not independent samples. This checks whether the "
                 "risk RANKING holds up (does 'High' really see more water than "
                 "'Low'), which is the precondition for calibrating it into a "
                 "real percentage later, once more events accumulate."),
        "n_events_scanned": len(events),
        "n_events_processed": len(per_event),
        "reliability": reliability,
        "ranking_is_monotonic": monotonic,
        "per_event": per_event,
    }, indent=2))
    print(f"\nwrote {out}")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 5))
        xs = [r["class_name"] for r in reliability if r["class"] > 0]
        ys = [r["observed_water_rate_pct"] or 0 for r in reliability if r["class"] > 0]
        ns = [r["n_pixels"] for r in reliability if r["class"] > 0]
        bars = ax.bar(xs, ys, color="#3b7dd8")
        for b, n in zip(bars, ns):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"n={n:,}",
                    ha="center", va="bottom", fontsize=8)
        ax.set_ylabel("% of pixels showing real new water on a flood day")
        ax.set_title("Static WHERE risk class vs. real satellite flood-water evidence\n"
                      f"({len(per_event)} events pooled — a first check, not a finished calibration)",
                      fontsize=10)
        fig.tight_layout()
        png = OUT / "where_calibration_overlay.png"
        fig.savefig(png, dpi=110)
        print(f"wrote {png}")
    except ImportError:
        pass


if __name__ == "__main__":
    main()
