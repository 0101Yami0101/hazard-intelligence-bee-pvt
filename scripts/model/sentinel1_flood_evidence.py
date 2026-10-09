"""Phase 3b of the flood-WHEN pilot — does Jang valley actually show real
standing water on confirmed flood days, per calibrated Sentinel-1 radar?

Runs the full calibrated water-change check across EVERY exact-date match
found in Phase 3 (reports/flood_where_s1_feasibility.json's exact_match_dates)
— not just one date — to see whether the signal repeats, per the plan's own
honest caveat: "a single date pair... is real, dated, methodologically sound
evidence — not yet a validated flood map."

Compares each flood-day scene against a dry-season baseline on the SAME
relative orbit (so pixel geometry lines up without needing full terrain
correction) — three orbits cover all 13 dates (150, 41, 77), so this needs
only 3 baseline scenes total, reused across every flood date that shares an
orbit; two flood dates (2020-07-21/22) turned out to be the same acquisition.

Both are raw GRD products (uncalibrated digital numbers with GCP-based, not
simple-grid, georeferencing):

    1. Windowed read around Jang valley via a LOCALLY-fit affine.
    2. Parse the scene's own calibration LUT (annotation/calibration/*.xml)
       and bilinearly interpolate it to every pixel in the window.
    3. Convert digital numbers to calibrated sigma-nought backscatter (dB).
    4. Warp via the scene's real GCPs onto a common EPSG:4326 grid — in two
       steps (auto-resolution GCP warp, then a plain reproject onto the
       fixed grid), not one forced-resolution warp. See the comment on
       GRID_RES_DEG below for why the one-step version is a real trap.
    5. Threshold (water is smooth -> very low backscatter) and difference
       flood vs. baseline to isolate NEW water, not permanent river/lake.

Output:
    reports/flood_where_s1_jang_multi_date.json      -- every date's result
    data/interim/flood_when/s1_jang_<date>_water_check.png  -- one visual per date
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_gcps, from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject
from rasterio.windows import Window, from_bounds
from scipy.interpolate import RegularGridInterpolator

from common import INTERIM, ROOT

SAT = ROOT / "data" / "raw" / "11_satellite"
OUT = INTERIM / "flood_when"
REPORTS = ROOT / "reports"

JANG_LAT, JANG_LON = 27.5834, 91.9802
BUF_DEG = 0.15
WATER_DB_THRESHOLD = -17.0   # standard rough cutoff for smooth open water in VV

# Common destination grid every scene is warped onto — fixed explicitly so
# INDEPENDENT warps land on identical pixels. Getting this wrong is a real
# trap, caught here: cropping two separately-fit local-affine windows to
# "the same shape" and diffing them directly looked plausible (real
# percentages) but was wrong — a co-registration artefact, not real change.
# A second, unrelated trap: forcing an explicit transform/width/height
# directly on a GCP-based WarpedVRT silently collapses all real texture
# (reproduced on pure synthetic random data, nothing Sentinel-1-specific —
# GDAL needs to pick the GCP warp's own natural resolution first). Fix used
# here: auto-resolution GCP warp, THEN a plain reproject onto this grid.
GRID_RES_DEG = 0.0001   # ~11 m at this latitude, matches native GRD resolution
GRID_BOUNDS = (JANG_LON - BUF_DEG, JANG_LAT - BUF_DEG,
               JANG_LON + BUF_DEG, JANG_LAT + BUF_DEG)

# date -> (flood scene zip stem, baseline scene zip stem). Baselines reused
# across every flood date on the same relative orbit — only 3 needed for all
# 13 exact-match dates. 2020-07-21 and 2020-07-22 are the same acquisition.
FLOOD_SCENES = {
    "2019-07-09": "S1A_IW_GRDH_1SDV_20190709T235453_20190709T235518_028047_032AE1_1961_COG.SAFE",
    "2019-07-14": "S1A_IW_GRDH_1SDV_20190714T115718_20190714T115743_028113_032CCD_A814_COG.SAFE",
    "2019-08-02": "S1A_IW_GRDH_1SDV_20190802T235454_20190802T235519_028397_03357D_CB3F_COG.SAFE",
    "2020-05-21": "S1A_IW_GRDH_1SDV_20200521T115721_20200521T115746_032663_03C873_7823_COG.SAFE",
    "2020-05-23": "S1A_IW_GRDH_1SDV_20200523T234639_20200523T234704_032699_03C99A_6E24_COG.SAFE",
    "2020-06-21": "S1A_IW_GRDH_1SDV_20200621T235459_20200621T235524_033122_03D646_6704_COG.SAFE",
    "2020-06-26": "S1A_IW_GRDH_1SDV_20200626T115723_20200626T115748_033188_03D839_F8E0_COG.SAFE",
    "2020-07-20": "S1B_IW_GRDH_1SDV_20200721T235429_20200721T235458_022576_02AD94_AB21_COG.SAFE",
    "2020-07-21": "S1A_IW_GRDH_1SDV_20200722T234643_20200722T234708_033574_03E411_8D94_COG.SAFE",
    "2020-07-22": "S1A_IW_GRDH_1SDV_20200722T234643_20200722T234708_033574_03E411_8D94_COG.SAFE",
    "2021-08-27": "S1A_IW_GRDH_1SDV_20210827T235508_20210827T235533_039422_04A82D_6498_COG.SAFE",
    "2023-08-24": "S1A_IW_GRDH_1SDV_20230824T234702_20230824T234727_050024_0604C4_F397_COG.SAFE",
    "2025-08-31": "S1C_IW_GRDH_1SDV_20250831T234542_20250831T234604_003923_007D0B_CB7B_COG.SAFE",
}
DATE_ORBIT = {
    "2019-07-09": 150, "2019-08-02": 150, "2020-06-21": 150, "2020-07-20": 150, "2021-08-27": 150,
    "2019-07-14": 41, "2020-05-21": 41, "2020-06-26": 41,
    "2020-05-23": 77, "2020-07-21": 77, "2020-07-22": 77, "2023-08-24": 77, "2025-08-31": 77,
}
BASELINE_BY_ORBIT = {
    150: "S1A_IW_GRDH_1SDV_20250303T235509_20250303T235534_058147_072EBE_9F60_COG.SAFE",
    41: "S1A_IW_GRDH_1SDV_20250224T115734_20250224T115759_058038_072A4F_B044_COG.SAFE",
    77: "S1A_IW_GRDH_1SDV_20250226T234652_20250226T234717_058074_072BC7_396C_COG.SAFE",
}


def scene_meta(safe_stem: str) -> dict:
    """Locate the VV measurement/calibration file names inside a scene's zip
    — read from the archive's own listing rather than hand-typed per scene,
    since 13 scenes' worth of hand-typed filenames is itself error-prone."""
    zpath = SAT / f"{safe_stem}.zip"
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
    meas = next(n for n in names if "/measurement/" in n and "-vv-" in n)
    cal = next(n for n in names if "/annotation/calibration/calibration-" in n and "-vv-" in n)
    return {
        "zip": zpath, "safe": safe_stem,
        "vv_meas": meas.split("/measurement/")[1],
        "vv_cal": cal.split("/annotation/calibration/")[1],
    }


def parse_calibration_lut(xml_bytes: bytes) -> RegularGridInterpolator:
    """Sentinel-1's calibration XML: a coarse grid of (line, pixel) ->
    sigmaNought, meant to be bilinearly interpolated to every real pixel."""
    text = xml_bytes.decode("utf-8")
    lines = [int(x) for x in re.findall(r"<line>(\d+)</line>", text)]
    pixel_blocks = re.findall(r'<pixel count="\d+">([^<]+)</pixel>', text)
    sigma_blocks = re.findall(r'<sigmaNought count="\d+">([^<]+)</sigmaNought>', text)
    pixels = np.array([float(x) for x in pixel_blocks[0].split()])
    grid = np.array([[float(x) for x in b.split()] for b in sigma_blocks])
    assert grid.shape == (len(lines), len(pixels)), (grid.shape, len(lines), len(pixels))
    return RegularGridInterpolator((np.array(lines), pixels), grid,
                                    bounds_error=False, fill_value=None)


def read_calibrated_window(meta: dict, lat: float = JANG_LAT, lon: float = JANG_LON,
                            buf_deg: float = BUF_DEG,
                            grid_bounds: tuple[float, float, float, float] | None = None) -> np.ndarray:
    """DN window around (lat, lon), calibrated to dB, THEN warped (via the
    scene's real GCPs) onto a shared EPSG:4326 grid — so this scene's pixel
    (i, j) and every other scene's pixel (i, j) are the same ground
    location, not just the same array shape. Defaults to Jang valley for
    backward compatibility with the original Tawang-pilot call sites;
    sentinel1_flood_evidence_statewide.py passes every other station's own
    location explicitly."""
    if grid_bounds is None:
        grid_bounds = (lon - buf_deg, lat - buf_deg, lon + buf_deg, lat + buf_deg)
    vsi = f"/vsizip/{meta['zip']}/{meta['safe']}/measurement/{meta['vv_meas']}"
    with rasterio.open(vsi) as src:
        gcps, gcp_crs = src.gcps
        near = sorted(gcps, key=lambda g: (g.x - lon) ** 2 + (g.y - lat) ** 2)[:60]
        inv = ~from_gcps(near)
        corners = [(lon - buf_deg, lat - buf_deg), (lon + buf_deg, lat - buf_deg),
                   (lon - buf_deg, lat + buf_deg), (lon + buf_deg, lat + buf_deg)]
        px = [inv * c for c in corners]
        cols, rows = [p[0] for p in px], [p[1] for p in px]
        pad = 50
        c0, c1 = max(0, int(min(cols)) - pad), min(src.width, int(max(cols)) + pad)
        r0, r1 = max(0, int(min(rows)) - pad), min(src.height, int(max(rows)) + pad)
        # Found on 2020-07-20's S1B scene: the OData search returned it as
        # "intersecting" the AOI (a bounding-box/footprint test), but the
        # target point sits entirely outside this pass's real coverage —
        # the computed window came out negative after clamping (row 0 to
        # -97). Not a fixable bug, a genuine no-coverage case; raise a clear
        # message instead of rasterio's confusing generic ValueError so a
        # caller can skip it cleanly (as main()'s try/except already does).
        if c1 <= c0 or r1 <= r0:
            raise RuntimeError(
                f"({lat},{lon}) has no real coverage in this scene despite "
                f"matching the AOI search — window came out empty/negative "
                f"(row {r0}:{r1}, col {c0}:{c1})")
        dn = src.read(1, window=Window(c0, r0, c1 - c0, r1 - r0)).astype(np.float64)

        # Margin must be wide enough to keep >=3 distinct azimuth (row)
        # bands — GDAL's auto-selected polynomial order can be 2+ once
        # there are ~7+ points, and with only 2 distinct row values the
        # row^2 term is linearly dependent on row itself, making the fit
        # matrix singular ("Transform is not solvable"). 3000 was enough
        # for every station in the original 13-date sweep; hit the same
        # failure again on Kibithu during the statewide rollout — its
        # window sits right at the image's top edge (row 0), where GCP
        # rows are spaced far enough apart that 3000 still only reaches 2
        # of them. 5000 reaches 3 there and cost nothing on any station
        # that already worked with 3000 (more nearby points, not fewer).
        margin = 5000
        local_gcps = [GroundControlPoint(row=g.row - r0, col=g.col - c0, x=g.x, y=g.y, z=g.z)
                      for g in gcps if r0 - margin <= g.row <= r1 + margin
                      and c0 - margin <= g.col <= c1 + margin]

    with zipfile.ZipFile(meta["zip"]) as z:
        cal_path = f"{meta['safe']}/annotation/calibration/{meta['vv_cal']}"
        lut = parse_calibration_lut(z.read(cal_path))

    rr, cc = np.meshgrid(np.arange(r0, r1), np.arange(c0, c1), indexing="ij")
    sigma_nought = lut(np.stack([rr.ravel(), cc.ravel()], axis=-1)).reshape(dn.shape)
    sigma0_linear = (dn ** 2) / (sigma_nought ** 2)
    with np.errstate(divide="ignore"):
        db = 10 * np.log10(np.clip(sigma0_linear, 1e-6, None)).astype(np.float32)

    with MemoryFile() as mem:
        with mem.open(driver="GTiff", height=db.shape[0], width=db.shape[1],
                      count=1, dtype=db.dtype, gcps=local_gcps, crs=gcp_crs) as ds:
            ds.write(db, 1)
        with mem.open() as ds:
            with WarpedVRT(ds, crs="EPSG:4326", resampling=Resampling.bilinear) as vrt:
                win = from_bounds(*grid_bounds, vrt.transform)
                native = vrt.read(1, window=win)
                native_transform = vrt.window_transform(win)

    dst_width = int(round((grid_bounds[2] - grid_bounds[0]) / GRID_RES_DEG))
    dst_height = int(round((grid_bounds[3] - grid_bounds[1]) / GRID_RES_DEG))
    dst = np.zeros((dst_height, dst_width), dtype=np.float32)
    reproject(native, dst,
              src_transform=native_transform, src_crs="EPSG:4326",
              dst_transform=from_origin(grid_bounds[0], grid_bounds[3], GRID_RES_DEG, GRID_RES_DEG),
              dst_crs="EPSG:4326", resampling=Resampling.bilinear)
    return dst


_baseline_cache: dict[int, np.ndarray] = {}


def baseline_for_orbit(orbit: int) -> np.ndarray:
    if orbit not in _baseline_cache:
        meta = scene_meta(BASELINE_BY_ORBIT[orbit])
        _baseline_cache[orbit] = read_calibrated_window(meta)
    return _baseline_cache[orbit]


def check_one_date(date: str) -> dict | None:
    zip_path = SAT / f"{FLOOD_SCENES[date]}.zip"
    if not zip_path.exists():
        print(f"  [skip] {date}: scene not downloaded yet ({zip_path.name})")
        return None

    orbit = DATE_ORBIT[date]
    flood_meta = scene_meta(FLOOD_SCENES[date])
    flood_db = read_calibrated_window(flood_meta)
    base_db = baseline_for_orbit(orbit)

    assert flood_db.shape == base_db.shape
    valid = (flood_db > -59.0) & (base_db > -59.0)
    flood_water = (flood_db < WATER_DB_THRESHOLD) & valid
    base_water = (base_db < WATER_DB_THRESHOLD) & valid
    new_water = flood_water & ~base_water

    result = {
        "flood_date": date,
        "orbit": orbit,
        "baseline_scene": BASELINE_BY_ORBIT[orbit],
        "pct_nodata_excluded": round(100 * float((~valid).mean()), 2),
        "pct_water_flood_day": round(100 * float(flood_water[valid].mean()), 2),
        "pct_water_baseline_day": round(100 * float(base_water[valid].mean()), 2),
        "pct_new_water_flood_only": round(100 * float(new_water[valid].mean()), 2),
    }
    print(f"  {date} (orbit {orbit}): new-water {result['pct_new_water_flood_only']}%  "
          f"(flood {result['pct_water_flood_day']}% / baseline {result['pct_water_baseline_day']}%)")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        axes[0].imshow(base_db, cmap="gray", vmin=-25, vmax=0)
        axes[0].set_title(f"baseline (orbit {orbit})")
        axes[1].imshow(flood_db, cmap="gray", vmin=-25, vmax=0)
        axes[1].set_title(f"flood day {date}")
        axes[2].imshow(new_water, cmap="Blues")
        axes[2].set_title("new water (flood-only)")
        for a in axes:
            a.axis("off")
        OUT.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT / f"s1_jang_{date}_water_check.png", dpi=100, bbox_inches="tight")
        plt.close(fig)
    except ImportError:
        pass

    return result


def main() -> None:
    print("Phase 3b — calibrated Sentinel-1 water check, Jang valley, all exact-match dates\n")
    results = []
    for date in sorted(FLOOD_SCENES):
        try:
            r = check_one_date(date)
            if r:
                results.append(r)
        except Exception as exc:  # noqa: BLE001
            print(f"  [FAIL] {date}: {type(exc).__name__}: {str(exc)[:150]}")

    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "flood_where_s1_jang_multi_date.json"
    out.write_text(json.dumps({
        "aoi": "Jang valley, Tawang",
        "water_threshold_db": WATER_DB_THRESHOLD,
        "n_dates_checked": len(results),
        "n_dates_total": len(set(FLOOD_SCENES)),
        "results": results,
    }, indent=2))
    print(f"\nwrote {out}  ({len(results)}/{len(set(FLOOD_SCENES))} dates checked)")

    if results:
        vals = [r["pct_new_water_flood_only"] for r in results]
        print(f"\nnew-water %: min {min(vals):.1f}  median {sorted(vals)[len(vals)//2]:.1f}  "
              f"max {max(vals):.1f}  mean {sum(vals)/len(vals):.1f}")


if __name__ == "__main__":
    main()
