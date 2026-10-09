"""Cross-check Groundsource candidates that satellite (GFD or the
Sentinel-1-in-EE screen) could NOT confirm against every real gauge we
have — CWC (18 Arunachal stations) + NWDP (14 small-stream stations,
2 with clearly wrong/mislabeled coordinates excluded — see below).

User's instruction, 2026-09-06: "apply gauge check to all data that we
are unable to confirm with just satellite from 2000 to today. Use any
and all gauge data we have/can get." This is the reusable version of the
one-off analysis first run in chat against the pre-2019 GFD-check batch
(23 confirmed) — same logic, parameterized so it can run again against
the 2019+ Sentinel-1-in-EE screen's leftovers once that finishes.

Real, checked issue in the NWDP data: two station labels ("Changlang",
"Ziro") carry coordinates that land nowhere near Arunachal at all (J&K
and Uttarakhand respectively) — almost certainly a mislabeling in the
source data, not real. Excluded rather than trusted. The correctly-named
"Changlang_1" (real Arunachal coordinates) is kept.

Most NWDP stations' records only start in 2023-2025 — they genuinely
cannot help confirm anything older, which is exactly why NWDP added zero
extra confirmations to the pre-2019 batch (all NWDP-proximate candidates
there had no gauge data in their date window) but should help the 2019+
batch, whose dates fall inside NWDP's real coverage window.

    python scripts/model/gauge_crosscheck_groundsource.py <input_report.json> <unconfirmed_key> <output_report.json>

Where <unconfirmed_key> is the boolean field marking a candidate as
already satellite-confirmed (e.g. "real_new_flood" for the GFD check,
"screen_positive" for the S1-EE screen) — candidates where that field is
NOT true get checked against gauges.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from flood_stations import STATIONS as CWC_STATIONS  # noqa: E402

NEAR_KM = 20
WINDOW_DAYS = 3
BAD_NWDP_STATIONS = {"Changlang", "Ziro"}  # real coords land outside Arunachal entirely


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def build_registry() -> list[tuple[str, str, float, float]]:
    registry = [("CWC", code, s["lat"], s["lon"]) for code, s in CWC_STATIONS.items()]
    nwdp = pd.read_parquet(ROOT / "data/interim/flood_when/nwdp_combined.parquet")
    stations = nwdp.groupby("Station").agg(lat=("Latitude", "first"), lon=("Longitude", "first")).reset_index()
    stations = stations[~stations["Station"].isin(BAD_NWDP_STATIONS)]
    for _, s in stations.iterrows():
        registry.append(("NWDP", s["Station"], s["lat"], s["lon"]))
    return registry


def load_series(source: str, code: str, nwdp_df: pd.DataFrame) -> pd.DataFrame:
    if source == "CWC":
        df = pd.read_csv(ROOT / f"data/raw/11_gauges/cwc/{code}_hhs.csv")
        df["datetime"] = pd.to_datetime(df["datetime"])
        return df
    df = nwdp_df[nwdp_df["Station"] == code][["Data Acquisition Time", "discharge"]].copy()
    df.columns = ["datetime", "level"]
    return df


def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    in_path, key, out_path = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])

    d = json.loads(in_path.read_text())
    all_results = d.get("results", [])
    unconfirmed = [r for r in all_results if not r.get(key)]
    print(f"{len(unconfirmed)}/{len(all_results)} candidates not yet satellite-confirmed "
          f"(field '{key}')")

    registry = build_registry()
    print(f"{len(registry)} real gauge stations (CWC + NWDP, bad-coordinate ones excluded)")

    near = []
    for r in unconfirmed:
        best = None
        for src, code, lat, lon in registry:
            km = haversine_km(r["lat"], r["lon"], lat, lon)
            if best is None or km < best[2]:
                best = (src, code, km)
        if best[2] <= NEAR_KM:
            near.append({**r, "gauge_source": best[0], "nearest_station": best[1], "dist_km": round(best[2], 2)})
    print(f"{len(near)} within {NEAR_KM}km of a real gauge")

    nwdp_df = pd.read_parquet(ROOT / "data/interim/flood_when/nwdp_combined.parquet")
    nwdp_df["Data Acquisition Time"] = pd.to_datetime(nwdp_df["Data Acquisition Time"])
    cache: dict[tuple, pd.DataFrame] = {}

    confirmed, no_data = [], 0
    for c in near:
        key_ = (c["gauge_source"], c["nearest_station"])
        if key_ not in cache:
            cache[key_] = load_series(*key_, nwdp_df)
        df = cache[key_]
        d0 = pd.to_datetime(c["date_str"])
        window = df[(df["datetime"] >= d0 - pd.Timedelta(days=WINDOW_DAYS)) &
                    (df["datetime"] <= d0 + pd.Timedelta(days=WINDOW_DAYS))]
        if window.empty:
            no_data += 1
            continue
        danger = CWC_STATIONS.get(c["nearest_station"], {}).get("danger_level") if c["gauge_source"] == "CWC" else None
        if danger is not None:
            hit = (window["level"] > danger).any()
            thresh_desc = f"published CWC danger level {danger}"
        else:
            thresh = df["level"].quantile(0.95)
            hit = (window["level"] > thresh).any()
            thresh_desc = f"95th percentile proxy {round(float(thresh), 2)}"
        if hit:
            confirmed.append({**c, "gauge_confirmed": True, "threshold_used": thresh_desc,
                               "peak_in_window": round(float(window["level"].max()), 3)})

    print(f"no gauge data in that window at all: {no_data}")
    print(f"ADDITIONAL real events confirmed via gauge: {len(confirmed)}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "note": f"Gauge cross-check of candidates unconfirmed by satellite (field "
                f"'{key}' not true), against real CWC+NWDP gauge data.",
        "n_unconfirmed_by_satellite": len(unconfirmed), "n_near_a_gauge": len(near),
        "n_no_gauge_data_in_window": no_data, "n_confirmed": len(confirmed),
        "results": confirmed,
    }, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
