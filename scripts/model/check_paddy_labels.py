"""Are some of our satellite-confirmed "floods" really flooded rice paddies?

    python scripts/model/check_paddy_labels.py

Writes  reports/flood_paddy_check.json
        data/interim/flood_forecast/event_label_audit.parquet   (one row per flood)

════════════════════════════════════════════════════════════════════════════
THE QUESTION
════════════════════════════════════════════════════════════════════════════
A flood label here is "Sentinel-1 saw water that wasn't in a same-orbit DRY-
SEASON baseline". Rice fields in the Brahmaputra valley are deliberately
flooded every year — Ahu (Mar-Apr), Sali (Jun-Aug transplanting), Boro
(irrigated, Dec-Feb). Against a dry-season baseline a flooded paddy looks
exactly like new flood water. The 24 May 2024 "floods" (seen 21 May, before
any real rain) raised the question.

════════════════════════════════════════════════════════════════════════════
THE TEST
════════════════════════════════════════════════════════════════════════════
A real flood needs water from somewhere: unusual rain, locally or upstream.
A paddy doesn't — it's flooded on a calendar. So, per flood:

    crop share      share of its flooded 100 m cells on ESA WorldCover cropland
    rain signal     how unusual the week's rain was before the satellite SAW
                    the water (scene date, not the loose report date): the
                    higher of the local and upstream-catchment 7-day
                    percentiles, each against that place's own monsoon
    channel link    median height above / distance from the nearest channel
                    of the flooded cells — floods spread from channels,
                    paddies sit wherever the fields are

If paddies contaminate the record, cropland-heavy "floods" — above all in the
planting months and the dry season — should show a much weaker rain signal
than floods on other ground in the same months.

The rain percentile is scaled against May-October, so an ordinary monsoon
week scores ~0.5. "Dry" below means the week before the water appeared was
no wetter than an ordinary monsoon week — and in the dry season, far drier.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

import grid as G
import when_grid
from build_flood_where_samples import COVER_MIN, POS_FRAC, SOURCE_REPORTS, event_grid
from common import INTERIM, ROOT

STACK = INTERIM / "terrain_unmasked"
PIX = INTERIM / "flood_where_pixels"
OUT = INTERIM / "flood_forecast"
CROPLAND = 40
DRY = 0.5                       # rain percentile: no wetter than an ordinary monsoon week

SEASONS = {"dry season (Nov-Feb)": [11, 12, 1, 2], "pre-monsoon (Mar-Apr)": [3, 4],
           "early monsoon (May-Jul)": [5, 6, 7], "late monsoon (Aug-Oct)": [8, 9, 10]}


def season_of(m: int) -> str:
    return next(s for s, ms in SEASONS.items() if m in ms)


def load_events() -> pd.DataFrame:
    rows = {}
    for name in SOURCE_REPORTS:
        d = json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))
        for r in d["results"]:
            if r.get("screen_positive") and r["uuid"] not in rows:
                rows[r["uuid"]] = {k: r.get(k) for k in
                                   ("uuid", "date_str", "scene_date", "lat", "lon")}
    ev = pd.DataFrame(rows.values())
    ev["report_date"] = pd.to_datetime(ev["date_str"])
    ev["scene_date"] = pd.to_datetime(ev["scene_date"])
    ev["k"] = when_grid.cell_of(ev["lat"].to_numpy(), ev["lon"].to_numpy())
    return ev


def main() -> None:
    print("Paddy check — are some 'floods' flooded rice fields?\n")
    ev = load_events()

    lay = {}
    for n in ("lc_class_cat", "hydro_hand_m", "hydro_hand_small_m", "dist_chan_small_m"):
        with rasterio.open(STACK / f"{n}.tif") as s:
            lay[n] = s.read(1)
    hand = np.minimum(lay["hydro_hand_m"], lay["hydro_hand_small_m"])

    # Rain signal: local and upstream 7-day percentiles, on the SCENE date.
    dates, f = when_grid.percentile_features()
    local_r7 = pd.DataFrame(f["r7"], index=dates)
    wd = pd.to_datetime(np.load(OUT / "when_dates.npy"))
    up_r7 = pd.DataFrame(np.load(OUT / "upstream_rain_pct.npz")["up_r7"], index=wd)
    rain = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    rain_dates = pd.to_datetime(np.load(INTERIM / "rainfall" / "dates.npy").astype("datetime64[D]"))
    rpos = pd.Series(np.arange(len(rain_dates)), index=rain_dates)
    nlon = when_grid.lattice()["nlon"]

    to3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    to_utm = Transformer.from_crs("EPSG:3857", G.CRS, always_xy=True)
    rows = []
    for _, e in ev.iterrows():
        p = PIX / f"{e['uuid']}.npz"
        if not p.exists() or e["k"] < 0 or pd.isna(e["scene_date"]):
            continue
        g = event_grid(p, to3857, to_utm)
        if g is None:
            continue
        r0, c0, frac, cover = g[:4]
        h, w = frac.shape
        sub = (slice(r0, r0 + h), slice(c0, c0 + w))
        wet = (cover >= COVER_MIN) & (frac >= POS_FRAC) & np.isfinite(hand[sub])
        cov = (cover >= COVER_MIN) & np.isfinite(hand[sub])
        n_wet = int(wet.sum())
        if n_wet < 5:
            continue
        lc_w, lc_c = lay["lc_class_cat"][sub][wet], lay["lc_class_cat"][sub][cov]
        sd, k = e["scene_date"], int(e["k"])
        lr = float(local_r7.at[sd, k]) if sd in local_r7.index else np.nan
        ur = float(up_r7.at[sd, k]) if sd in up_r7.index else np.nan
        mm7 = np.nan
        if sd in rpos.index:
            j = rpos[sd]
            mm7 = float(np.asarray(rain[max(0, j - 6):j + 1, k // nlon, k % nlon]).sum())
        rows.append({
            "uuid": e["uuid"], "report_date": e["report_date"], "scene_date": sd,
            "month": sd.month, "season": season_of(sd.month),
            "lat": e["lat"], "lon": e["lon"], "n_wet": n_wet,
            "crop_share": float((lc_w == CROPLAND).mean()),
            # River-corridor classes: WorldCover's "permanent water" and
            # "bare/sparse" (sandbars) — where a braided channel migrating
            # between two dates would put spurious "new water".
            "channel_share": float(np.isin(lc_w, (60, 80)).mean()),
            "tree_share": float((lc_w == 10).mean()),
            "grass_share": float((lc_w == 30).mean()),
            "crop_share_of_ground": float((lc_c == CROPLAND).mean()),
            "local_r7_pct": lr, "upstream_r7_pct": ur,
            "rain_signal": float(np.nanmax([lr, ur])) if np.isfinite([lr, ur]).any() else np.nan,
            "local_rain_7d_mm": mm7,
            "wet_median_hand_m": float(np.median(hand[sub][wet])),
            "wet_median_dist_chan_m": float(np.median(lay["dist_chan_small_m"][sub][wet])),
        })
    a = pd.DataFrame(rows)
    a = a[np.isfinite(a["rain_signal"])].reset_index(drop=True)
    a["dry"] = a["rain_signal"] < DRY
    a["crop_heavy"] = a["crop_share"] >= 0.5
    a.to_parquet(OUT / "event_label_audit.parquet", index=False)
    print(f"  {len(a):,} floods with a mask, a rain record and >=5 flooded cells\n")

    def summ(df):
        return {"n": int(len(df)),
                "median_rain_signal": float(df["rain_signal"].median()) if len(df) else None,
                "share_dry_pct": float(100 * df["dry"].mean()) if len(df) else None,
                "median_local_rain_7d_mm": float(df["local_rain_7d_mm"].median()) if len(df) else None,
                "median_crop_share": float(df["crop_share"].median()) if len(df) else None,
                "median_wet_hand_m": float(df["wet_median_hand_m"].median()) if len(df) else None,
                "median_wet_dist_chan_m": float(df["wet_median_dist_chan_m"].median()) if len(df) else None}

    # 1. Does cropland-heavy water come with less rain, season by season?
    print("  1. Rain before the water appeared, cropland-heavy vs other floods")
    print(f"     {'season':<26}{'ground':<16}{'floods':>7}{'rain pct':>10}{'dry':>7}{'7d mm':>8}")
    by_season = {}
    for s in SEASONS:
        by_season[s] = {}
        for lab, m in (("cropland-heavy", True), ("other", False)):
            d = a[(a["season"] == s) & (a["crop_heavy"] == m)]
            by_season[s][lab] = summ(d)
            if len(d):
                x = by_season[s][lab]
                print(f"     {s:<26}{lab:<16}{x['n']:>7}{x['median_rain_signal']:>10.2f}"
                      f"{x['share_dry_pct']:>6.0f}%{x['median_local_rain_7d_mm']:>8.0f}")

    # 2. Dose-response: does rain signal fall steadily as crop share rises?
    print("\n  2. By share of the flooded ground that is cropland (all seasons)")
    bins = [0, 0.1, 0.25, 0.5, 0.75, 1.01]
    by_crop = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        d = a[(a["crop_share"] >= lo) & (a["crop_share"] < hi)]
        x = {"crop_share_lo": lo, "crop_share_hi": min(hi, 1.0), **summ(d)}
        by_crop.append(x)
        if len(d):
            print(f"     {int(100*lo):>3}-{int(100*min(hi,1)):>3}% cropland  {x['n']:>5} floods   "
                  f"rain pct {x['median_rain_signal']:.2f}   dry {x['share_dry_pct']:.0f}%   "
                  f"HAND {x['median_wet_hand_m']:.1f} m   to channel {x['median_wet_dist_chan_m']:.0f} m")

    # 3. Do "dry" floods sit away from channels, as fields would?
    print("\n  3. Where the water sits: rain-backed vs dry floods")
    chan = {lab: summ(a[a["dry"] == m]) for lab, m in (("rain-backed", False), ("dry", True))}
    for lab, x in chan.items():
        print(f"     {lab:<12} {x['n']:>5} floods   crop share {x['median_crop_share']:.2f}   "
              f"HAND {x['median_wet_hand_m']:.1f} m   to channel {x['median_wet_dist_chan_m']:.0f} m")

    # 4. The prime suspects: cropland-heavy, dry, in a rice season.
    rice = a["month"].isin([12, 1, 2, 3, 4, 5, 6, 7])
    suspect = a["crop_heavy"] & a["dry"] & rice
    print(f"\n  4. Prime suspects (>=50% cropland, dry week, rice-season month): "
          f"{int(suspect.sum()):,} of {len(a):,} ({100*suspect.mean():.1f}%)")
    print(f"     share of all flooded cells they carry: "
          f"{100*a.loc[suspect,'n_wet'].sum()/a['n_wet'].sum():.1f}%")
    may24 = a[a["report_date"] == pd.Timestamp("2024-05-24")]
    print(f"     the '24 May 2024' floods: {len(may24)} scored, crop share median "
          f"{may24['crop_share'].median():.2f}, rain pct median {may24['rain_signal'].median():.2f}, "
          f"{int((suspect & (a['report_date']==pd.Timestamp('2024-05-24'))).sum())} are suspects")

    # 5. The pattern the paddy test turned up instead: rain-less "floods"
    # lean away from cropland and onto riverbed ground. A braided river like
    # the Brahmaputra moves its channels and sandbars between the baseline
    # image and the flood image, which reads as "new water" with no rain.
    print("\n  5. Riverbed test: share of flooded cells on channel/sandbar land cover")
    corridor = {}
    for lab, m in (("rain-backed", ~a["dry"]), ("dry", a["dry"]),
                   ("dry season Nov-Feb", a["season"] == "dry season (Nov-Feb)")):
        d = a[m]
        corridor[lab] = {"n": int(len(d)),
                         "median_channel_share": float(d["channel_share"].median()),
                         "mean_channel_share": float(d["channel_share"].mean()),
                         "share_mostly_channel_pct": float(100 * (d["channel_share"] >= 0.5).mean())}
        x = corridor[lab]
        print(f"     {lab:<20} {x['n']:>5} floods   channel/sandbar share median "
              f"{x['median_channel_share']:.2f} mean {x['mean_channel_share']:.2f}   "
              f"mostly channel {x['share_mostly_channel_pct']:.0f}%")
    chan_suspect = a["dry"] & (a["channel_share"] >= 0.5)
    print(f"     channel-shift suspects (dry + >=50% channel/sandbar): {int(chan_suspect.sum())} "
          f"floods, {100*a.loc[chan_suspect,'n_wet'].sum()/a['n_wet'].sum():.1f}% of flooded cells")
    may24 = a[a["report_date"] == pd.Timestamp("2024-05-24")]
    print(f"     '24 May 2024' floods: channel/sandbar share median {may24['channel_share'].median():.2f}, "
          f"crop {may24['crop_share'].median():.2f}, grass {may24['grass_share'].median():.2f}, "
          f"tree {may24['tree_share'].median():.2f}")

    # A reference point for "dry": even genuine floods don't always follow an
    # unusual week locally (upstream-in-Tibet rain, snowmelt, dam releases,
    # loose dates). How often are floods on NON-crop ground dry?
    base_dry = float(100 * a.loc[~a["crop_heavy"], "dry"].mean())
    crop_dry = float(100 * a.loc[a["crop_heavy"], "dry"].mean())
    print(f"\n  dry share: floods on other ground {base_dry:.0f}%, "
          f"cropland-heavy floods {crop_dry:.0f}%")

    out = ROOT / "reports" / "flood_paddy_check.json"
    out.write_text(json.dumps({
        "question": "are some satellite-confirmed floods really flooded rice paddies?",
        "n_floods": int(len(a)), "dry_threshold_rain_pct": DRY,
        "by_season": by_season, "by_crop_share": by_crop, "rain_backed_vs_dry": chan,
        "dry_share_pct": {"other_ground": base_dry, "cropland_heavy": crop_dry},
        "riverbed_test": corridor,
        "channel_shift_suspects": {
            "definition": "rain signal < 0.5 and >=50% of flooded cells on WorldCover 60/80",
            "n": int(chan_suspect.sum()),
            "share_of_flooded_cells_pct": float(100 * a.loc[chan_suspect, "n_wet"].sum() / a["n_wet"].sum()),
            "uuids": a.loc[chan_suspect, "uuid"].tolist(),
        },
        "prime_suspects": {
            "definition": ">=50% of flooded cells on cropland, rain signal < 0.5, month Dec-Jul",
            "n": int(suspect.sum()), "share_of_floods_pct": float(100 * suspect.mean()),
            "share_of_flooded_cells_pct": float(100 * a.loc[suspect, "n_wet"].sum() / a["n_wet"].sum()),
            "uuids": a.loc[suspect, "uuid"].tolist(),
        },
    }, indent=2, default=str))
    print(f"\n  wrote {out}")


if __name__ == "__main__":
    main()
