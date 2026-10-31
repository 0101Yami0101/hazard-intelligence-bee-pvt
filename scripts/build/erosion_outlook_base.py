"""The weekly erosion outlook's fixed inputs, for the app (E2.1).

    $env:REGION = "assam"; python scripts/build/erosion_outlook_base.py

Method written down first: docs/design/EROSION_PLAN.md, "E2.1 part 1". Per rain
point (fetch_50_erosion_rain_history.py):

    a, b          InRESatE's daily erosivity model at the point (EI_day = a * P^b)
    ei_year       mean yearly sum of EI_day over complete history years, with
                  Open-Meteo rain on both sides (the source's wetness cancels in
                  the share the app computes)
    season_share  [366, points] the mean share of a year's EI that falls in the
                  7 days starting on each day of the year (smoothed +-7 days)

Per unit (catchment, district), the sparse matrix S[u, p] = sum over the unit's
scored cells nearest to point p of A (main run, t/ha/yr) / the unit's scored
cells, so this week's mean loss = S @ share.

Output: webapp/assets/erosion/<region>/outlook_base.npz and outlook_meta.json
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import scipy.io as sio
from pyproj import Transformer
from scipy.spatial import cKDTree

import grid as G
from common import AOI_NAME, HYDROLOGY, INTERIM, ROOT, WEATHER, outline

warnings.filterwarnings("ignore")

OM = INTERIM / "rainfall_om"
PAR = WEATHER / "erosivity" / "inresate" / "Daily Rainfall Erosivity Model Parameters"
OUT = ROOT / "webapp" / "assets" / "erosion" / AOI_NAME
SMOOTH = 7


def mat(p: Path) -> np.ndarray:
    d = sio.loadmat(p)
    return np.asarray(d[[k for k in d if not k.startswith("__")][0]], float)


def param_at(lat, lon) -> tuple[np.ndarray, np.ndarray]:
    A, B = mat(PAR / "a_ei.mat"), mat(PAR / "b_ei.mat")
    plat, plon = np.ravel(mat(PAR / "lat.mat")), np.ravel(mat(PAR / "lon.mat"))
    if A.shape == (len(plon), len(plat)):
        A, B = A.T, B.T
    a, b = np.empty(len(lat)), np.empty(len(lat))
    for k, (la, lo) in enumerate(zip(lat, lon)):
        # nearest 0.1 deg cell with a valid parameter (edge points can sit just outside India)
        order = np.argsort((plat[:, None] - la) ** 2 + (plon[None, :] - lo) ** 2, axis=None)
        for idx in order[:50]:
            i, j = np.unravel_index(idx, A.shape)
            if np.isfinite(A[i, j]) and np.isfinite(B[i, j]) and A[i, j] > 0:
                a[k], b[k] = A[i, j], B[i, j]
                break
        else:
            a[k] = b[k] = np.nan
    return a, b


def unit_matrix(gdf, ids_fn, near, ok, A, n_pts):
    ids = ids_fn(gdf)
    sel = ok & (ids > 0)
    u = ids[sel] - 1
    p = near[sel]
    n_u = np.bincount(u, minlength=len(gdf)).astype(np.float64)
    key = u.astype(np.int64) * n_pts + p
    sums = np.bincount(key, weights=A[sel].astype(np.float64), minlength=len(gdf) * n_pts)
    nz = np.nonzero(sums)[0]
    uu, pp = nz // n_pts, nz % n_pts
    vals = sums[nz] / np.maximum(n_u[uu], 1)
    return uu.astype(np.int32), pp.astype(np.int16), vals.astype(np.float32)


def main() -> None:
    from erosion_priority import ids_of
    print(f"Erosion outlook base — {AOI_NAME}")
    pts = json.loads((OM / "points.json").read_text())
    lat, lon = np.array(pts["lat"]), np.array(pts["lon"])
    rain = np.load(OM / "precip_mm.npy")
    dates = pd.to_datetime(np.load(OM / "dates.npy"))
    a, b = param_at(lat, lon)
    ei = a[None, :] * np.power(np.maximum(rain, 0), b[None, :])

    years = sorted(set(dates.year))
    full = [y for y in years if ((dates.year == y).sum() >= 365)]
    yr = pd.Series(dates.year)
    ei_year = np.nanmean([ei[(yr == y).values].sum(axis=0) for y in full], axis=0)

    # mean share of the year in the 7 days starting on each day of the year
    doy = np.minimum(dates.dayofyear.values, 365) - 1
    w7 = pd.DataFrame(ei).rolling(7).sum().shift(-6).to_numpy()
    in_full = np.isin(dates.year.values, full)
    season = np.full((365, len(lat)), np.nan)
    for d in range(365):
        m = in_full & (doy == d) & np.isfinite(w7).all(axis=1)
        season[d] = np.nanmean(w7[m], axis=0) / ei_year
    pad = np.vstack([season[-SMOOTH:], season, season[:SMOOTH]])
    season = np.array([pad[d:d + 2 * SMOOTH + 1].mean(axis=0) for d in range(365)])
    season = np.vstack([season, season[-1:]])                   # day 366

    # each scored cell -> its nearest rain point
    E = INTERIM / "erosion"
    with rasterio.open(E / "erosion_assessed.tif") as s:
        ok = s.read(1).astype(bool)
    with rasterio.open(E / "erosion_A_tpha.tif") as s:
        A = s.read(1)
    ok &= np.isfinite(A)
    tr = Transformer.from_crs(4326, G.CRS, always_xy=True)
    px, py = tr.transform(lon, lat)
    r, c = np.nonzero(ok)
    cx, cy = G.centre_xy(r, c)
    _, idx = cKDTree(np.c_[px, py]).query(np.c_[cx, cy], k=1)
    near = np.full(G.SHAPE, -1, np.int32)
    near[r, c] = idx

    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bas = bas[bas.HYBAS_ID.isin(pri.HYBAS_ID)].reset_index(drop=True)
    dist = gpd.read_file(outline("district"))
    cu, cp, cv = unit_matrix(bas, ids_of, near, ok, A, len(lat))
    du, dp, dv = unit_matrix(dist, ids_of, near, ok, A, len(lat))
    # the state as one unit: mean A of the scored cells nearest each point / all scored cells
    st = np.bincount(near[ok], weights=A[ok].astype(np.float64), minlength=len(lat)) / ok.sum()

    # which rain point each pixel of the app's map belongs to (scored land only),
    # on the class rasters' web grid, so the page can colour it without a GIS library
    from rasterio.enums import Resampling
    from rasterio.warp import calculate_default_transform, reproject
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "run"))
    from export_erosion_bundle import WEB_RES
    wtr, ww, wh = calculate_default_transform(G.CRS, "EPSG:3857", G.NCOLS, G.NROWS, *G.BOUNDS,
                                              resolution=WEB_RES)
    pix = np.zeros((wh, ww), np.uint16)
    reproject(source=(near + 1).astype(np.uint16), destination=pix, src_transform=G.TRANSFORM,
              src_crs=G.CRS, src_nodata=0, dst_transform=wtr, dst_crs="EPSG:3857", dst_nodata=0,
              resampling=Resampling.nearest)

    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "outlook_base.npz", pix=pix, lat=lat.astype(np.float32), lon=lon.astype(np.float32),
                        a=a.astype(np.float32), b=b.astype(np.float32), ei_year=ei_year.astype(np.float32),
                        season=season.astype(np.float32),
                        cat_u=cu, cat_p=cp, cat_v=cv, cat_id=bas.HYBAS_ID.values.astype(np.int64),
                        dis_u=du, dis_p=dp, dis_v=dv, dis_n=np.array(len(dist)),
                        state=st.astype(np.float32))
    monsoon = season[151:243].mean()                     # Jun-Aug start days
    meta = {"region": AOI_NAME, "n_points": int(len(lat)), "grid_deg": pts["grid_deg"],
            "history": f"{pts['start']} to {pts['end']}", "full_years": [int(full[0]), int(full[-1])],
            "districts": list(dist.NAME_2), "mean_week_share_pct": round(100 / 52, 2),
            "monsoon_week_share_pct": round(100 * float(monsoon), 2),
            "params_missing": int(np.isnan(a).sum())}
    (OUT / "outlook_meta.json").write_text(json.dumps(meta, indent=1))
    print(f"  {len(lat)} points; a {np.nanmedian(a):.3f}, b {np.nanmedian(b):.3f} (median); "
          f"yearly EI (Open-Meteo) median {np.nanmedian(ei_year):,.0f}; "
          f"a typical Jun-Aug week carries {100 * monsoon:.1f}% of the year (average week {100 / 52:.1f}%)")
    print(f"  catchment matrix {len(cv):,} entries, district {len(dv):,}; wrote {OUT / 'outlook_base.npz'}")


if __name__ == "__main__":
    main()
