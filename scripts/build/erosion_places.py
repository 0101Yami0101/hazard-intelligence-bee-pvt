"""Per-place figures for SoilSense's village card (E2.3).

    $env:REGION = "assam"; python scripts/build/erosion_places.py

For every named place inside the state, from three open sources de-duplicated (the same
name within 2 km is one place): OpenStreetMap (fetch_52_osm_places.py, keeps Assamese names
where mapped), GeoNames populated places (fetch_53_geonames_places.py) and the Survey of
India district headquarters. From what the erosion module already computed:

    district, catchment (HydroBASINS 12) and its rank, top-20 share of runs
    around the place (a 2.1 km square, "about 1 km around"):
        loss      mean estimated soil loss over scored land, t/ha/yr (main run)
        high      share of scored land at >= 10 t/ha/yr ("high" or worse)
        steep     share of land with slope >= 10 deg
        scored    share of the land the recipe scores (the rest: rivers, water, towns)
        bare      mean dry-season bare share of scored land, each year 2019-2026
    pt         the nearest weekly-outlook rain point

Output: webapp/assets/erosion/<region>/places.csv.gz
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
from pyproj import Transformer
from scipy import ndimage
from scipy.spatial import cKDTree

import grid as G
from common import AOI_NAME, BOUNDARIES, HYDROLOGY, INTERIM, LANDCOVER, ROOT, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
OUT = ROOT / "webapp" / "assets" / "erosion" / AOI_NAME / "places.csv.gz"
WIN = 21                     # cells: a 2.1 km square round the place
HIGH, STEEP = 10.0, 10.0
DEDUP_M = 2000.0             # the same name within 2 km is one place


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def gazetteer() -> pd.DataFrame:
    """OSM + GeoNames + district HQs, de-duplicated by name within DEDUP_M."""
    import zipfile
    osm = pd.DataFrame(json.loads((BOUNDARIES / "osm_places" / f"osm_places_{AOI_NAME}.json")
                                  .read_text(encoding="utf-8")))
    osm["source"] = "OpenStreetMap"
    cols = ["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass", "fcode", "cc",
            "cc2", "admin1", "admin2", "admin3", "admin4", "pop", "elev", "dem", "tz", "mod"]
    with zipfile.ZipFile(BOUNDARIES / "geonames" / "IN.zip") as z:
        gn = pd.read_csv(z.open("IN.txt"), sep="	", header=None, names=cols, dtype=str,
                         keep_default_na=False, quoting=3)
    gn = gn[gn.fclass == "P"].assign(lat=lambda d: d.lat.astype(float), lon=lambda d: d.lon.astype(float),
                                     place=lambda d: np.where(d.fcode.str.startswith("PPLA"), "town", "village"),
                                     name_as="", source="GeoNames")
    hq = gpd.read_file(BOUNDARIES / f"soi_district-hq_point_{AOI_NAME}.gpkg").to_crs(4326)
    name_col = next(c for c in hq.columns if c.lower() in ("name", "hq", "hq_name", "dist_hq", "name_hq"))
    hq = pd.DataFrame({"name": hq[name_col].astype(str).str.title(), "lat": hq.geometry.y, "lon": hq.geometry.x,
                       "place": "town", "name_as": "", "source": "Survey of India (district HQ)"})
    allp = pd.concat([hq, osm[["name", "name_as", "place", "lat", "lon", "source"]],
                      gn[["name", "name_as", "place", "lat", "lon", "source"]]], ignore_index=True)
    allp = allp[allp.name.str.strip() != ""]
    tr = Transformer.from_crs(4326, G.CRS, always_xy=True)
    allp["x"], allp["y"] = tr.transform(allp.lon.values, allp.lat.values)
    allp["key"] = allp.name.str.lower().str.replace(r"[^a-z]", "", regex=True)
    keep = np.ones(len(allp), bool)
    for _, g in allp.groupby("key"):
        idx = g.index.to_numpy()
        for i, a in enumerate(idx):
            if not keep[a]:
                continue
            for b in idx[i + 1:]:
                if keep[b] and np.hypot(allp.x[a] - allp.x[b], allp.y[a] - allp.y[b]) < DEDUP_M:
                    keep[b] = False
    return allp[keep].drop(columns=["x", "y", "key"]).reset_index(drop=True)


def local_mean(num: np.ndarray, den: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Window sums of num and den (uniform_filter returns means; the ratio is what matters)."""
    a = ndimage.uniform_filter(num.astype(np.float32), size=WIN, mode="constant")
    b = ndimage.uniform_filter(den.astype(np.float32), size=WIN, mode="constant")
    return a, b


def main() -> None:
    from erosion_priority import ids_of
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Village card figures — {AOI_NAME}")
    pl = gazetteer()
    tr = Transformer.from_crs(4326, G.CRS, always_xy=True)
    x, y = tr.transform(pl.lon.values, pl.lat.values)
    r, c = G.xy_to_rowcol(x, y)
    r, c = np.asarray(r), np.asarray(c)
    on = (r >= 0) & (r < G.NROWS) & (c >= 0) & (c < G.NCOLS)
    pl, r, c = pl[on].reset_index(drop=True), r[on], c[on]
    inside = rd(INTERIM / "state_mask.tif").astype(bool)
    keep = inside[r, c]
    pl, r, c = pl[keep].reset_index(drop=True), r[keep], c[keep]
    print(f"  {len(pl):,} places inside the state")

    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A = np.nan_to_num(rd(E / "erosion_A_tpha.tif"))
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif")
    n_ok, n_in = local_mean(ok, inside)
    s_A, _ = local_mean(A * ok, ok)
    s_hi, _ = local_mean((A >= HIGH) & ok, ok)
    s_st, _ = local_mean((slope >= STEEP) & inside, inside)
    with np.errstate(invalid="ignore", divide="ignore"):
        pl["loss"] = np.round((s_A[r, c] / n_ok[r, c]).astype(float), 1)
        pl["high"] = np.round((100 * s_hi[r, c] / n_ok[r, c]).astype(float))
        pl["steep"] = np.round((100 * s_st[r, c] / n_in[r, c]).astype(float))
        pl["scored"] = np.round((100 * n_ok[r, c] / n_in[r, c]).astype(float))

    with rasterio.open(LANDCOVER / "ee_dry_season" / f"dry_season_cover_{AOI_NAME}.tif") as s:
        names = list(s.descriptions)
        years = sorted(int(n.split("_")[1]) for n in names if n.startswith("bare_"))
        bare = []
        for yy in years:
            v = s.read(names.index(f"valid_{yy}") + 1)
            b = s.read(names.index(f"bare_{yy}") + 1).astype(np.float32) / 250
            use = ok & (v != 255) & (v / 250 >= 0.5) & (b <= 1)
            sb, nb = local_mean(np.where(use, b, 0), use)
            with np.errstate(invalid="ignore", divide="ignore"):
                bare.append(np.round((100 * sb[r, c] / nb[r, c]).astype(float), 1))
    pl["bare"] = [";".join("" if not np.isfinite(v) else f"{v:g}" for v in row) for row in np.array(bare).T]

    dist = gpd.read_file(outline("district"))
    did = ids_of(dist)[r, c]
    pl["district"] = [dist.NAME_2.iloc[i - 1] if i > 0 else "" for i in did]
    bas = gpd.read_file(HYDROLOGY / f"hydrosheds_basins-lev12_vector_{AOI_NAME}.gpkg")
    bid = ids_of(bas)[r, c]
    pl["hybas"] = [int(bas.HYBAS_ID.iloc[i - 1]) if i > 0 else 0 for i in bid]
    pri = pd.read_csv(ROOT / "reports" / f"erosion_priority_{AOI_NAME}.csv")
    pri = pri[["HYBAS_ID", "rank_main"] + (["top20_pct"] if "top20_pct" in pri else [])]
    pl = pl.merge(pri.rename(columns={"HYBAS_ID": "hybas", "rank_main": "catchment_rank"}), on="hybas", how="left")

    z = np.load(ROOT / "webapp" / "assets" / "erosion" / AOI_NAME / "outlook_base.npz")
    px, py = tr.transform(z["lon"], z["lat"])
    _, pt = cKDTree(np.c_[px, py]).query(np.c_[G.centre_xy(r, c)[0], G.centre_xy(r, c)[1]])
    pl["pt"] = pt.astype(int)
    pl = pl.drop(columns=[c for c in ("osm_id",) if c in pl]).sort_values(["name", "district"]).reset_index(drop=True)
    pl.to_csv(OUT, index=False, compression="gzip")
    print(f"  wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1e6:.2f} MB); bare years {years}; "
          f"by source {pl.source.value_counts().to_dict()}; Assamese names {int((pl.name_as.fillna('') != '').sum())}")
    print(pl[["name", "district", "loss", "high", "steep", "catchment_rank", "top20_pct", "bare"]]
          .sort_values("loss", ascending=False).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
