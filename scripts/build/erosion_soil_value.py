"""AD-29: what the lost soil is worth — topsoil depth, organic carbon and nitrogen carried off.

    $env:REGION = "assam"; python scripts/build/erosion_soil_value.py

A calculation on the main map, not a model and not a test. Per scored 100 m square:
    topsoil lost  mm/yr = A (t/ha/yr) / (bulk density (t/m3) x 10)
    carbon lost   kg/ha/yr = A x topsoil organic carbon (g/kg)
    nitrogen lost kg/ha/yr = A x topsoil total nitrogen (g/kg)
    as urea       bags/ha/yr = N / 0.46 / 45 kg; rupees at the farmer's price per bag
Topsoil = mean of SoilGrids 0-5 and 15-30 cm (as the recipe's K factor). Enrichment ratio 1:
eroded soil is usually richer in carbon and nitrogen than the soil it left (ratios of 1.2-3
are reported), so these are floors. Values are provisional (EROSION_PLAN.md V-34).

Outputs: data/interim/<region>/erosion/erosion_{N_kgha,C_kgha,topsoil_mm}.tif
         reports/erosion_soil_value_<region>.csv (catchments), …_districts.csv, .json (state)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from rasterio.warp import Resampling, reproject

import grid as G
from common import AOI_NAME, INTERIM, PROCESSED, ROOT, SOIL_GEOLOGY, outline

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
FEA = INTERIM / "features"
UREA_N = 0.46               # urea is 46% nitrogen
BAG_KG = 45                 # the standard bag since 2018
BAG_RS = 266.5              # farmer's price, neem-coated urea, 45 kg bag incl. taxes (V-34)


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1).astype(np.float64)


def soilgrids(prop: str, depth: str) -> np.ndarray:
    """A raw SoilGrids layer on the grid (bilinear, as features.py), for layers it has not built."""
    dst = np.full(G.SHAPE, np.nan, dtype=np.float32)
    with rasterio.open(SOIL_GEOLOGY / "soilgrids_250m" / f"soilgrids_{prop}-{depth}_250m_{AOI_NAME}.tif") as s:
        reproject(source=rasterio.band(s, 1), destination=dst, dst_transform=G.TRANSFORM, dst_crs=G.CRS,
                  src_nodata=s.nodata, dst_nodata=np.nan, resampling=Resampling.bilinear)
    return dst.astype(np.float64)


def write(name: str, a: np.ndarray) -> None:
    prof = dict(driver="GTiff", height=G.NROWS, width=G.NCOLS, count=1, dtype="float32", crs=G.CRS,
                transform=G.TRANSFORM, nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(E / f"{name}.tif", "w", **prof) as d:
        d.write(a.astype(np.float32), 1)


def summarise(label: str, units: np.ndarray, ids, A, N, C, mm, ok) -> pd.DataFrame:
    rows = []
    for i, uid in enumerate(ids, start=1):
        m = ok & (units == i)
        if not m.any():
            continue
        ha = float(m.sum())                         # 1 ha squares
        rows.append({label: uid, "scored_ha": int(ha),
                     "N_kg_per_ha": round(float(np.nanmean(N[m])), 1),
                     "C_kg_per_ha": round(float(np.nanmean(C[m])), 0),
                     "topsoil_mm_per_yr": round(float(np.nanmean(mm[m])), 2),
                     "N_t_per_yr": round(float(np.nansum(N[m])) / 1000, 1),
                     "C_t_per_yr": round(float(np.nansum(C[m])) / 1000, 0),
                     "N_gkg": round(float(np.nansum(N[m]) / max(np.nansum(A[m]), 1e-9)), 2)})
    d = pd.DataFrame(rows)
    d["urea_bags_per_ha"] = (d.N_kg_per_ha / UREA_N / BAG_KG).round(2)
    d["urea_rs_per_ha"] = (d.urea_bags_per_ha * BAG_RS).round(0)
    d["urea_bags_per_yr"] = (d.N_t_per_yr * 1000 / UREA_N / BAG_KG).round(-1)
    return d


def main() -> None:
    print(f"What the lost soil is worth — {AOI_NAME}")
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A = rd(E / "erosion_A_tpha.tif")
    soc = np.nanmean([rd(FEA / f"soil_soc_{d}_dgkg.tif") for d in ("0-5cm", "15-30cm")], axis=0) / 10    # g/kg
    bd = np.nanmean([rd(FEA / f"soil_bdod_{d}_cgcm3.tif") for d in ("0-5cm", "15-30cm")], axis=0) / 100  # t/m3
    n = np.nanmean([soilgrids("nitrogen", d) for d in ("0-5cm", "15-30cm")], axis=0) / 100                # g/kg
    A = np.where(ok, A, np.nan)
    N, C = A * n, A * soc                                   # t/ha x g/kg = kg/ha
    mm = A / (np.where(bd > 0.5, bd, np.nan) * 10)
    for name, a in (("erosion_N_kgha", N), ("erosion_C_kgha", C), ("erosion_topsoil_mm", mm)):
        write(name, a)

    cat = gpd.read_file(PROCESSED / "erosion_priority.gpkg", layer="catchments").to_crs(G.CRS)
    cu = rasterize([(g, i) for i, g in enumerate(cat.geometry, start=1)], out_shape=G.SHAPE,
                   transform=G.TRANSFORM, fill=0, dtype="int32")
    dc = summarise("HYBAS_ID", cu, cat.HYBAS_ID.tolist(), A, N, C, mm, ok)
    dist = gpd.read_file(outline("district")).to_crs(G.CRS)
    du = rasterize([(g, i) for i, g in enumerate(dist.geometry, start=1)], out_shape=G.SHAPE,
                   transform=G.TRANSFORM, fill=0, dtype="int32")
    dd = summarise("NAME_2", du, dist.NAME_2.tolist(), A, N, C, mm, ok)
    dc.to_csv(ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}.csv", index=False)
    dd.to_csv(ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}_districts.csv", index=False)

    v = ok & np.isfinite(N) & np.isfinite(C) & np.isfinite(mm)
    n_t, c_t = float(np.nansum(N[v])) / 1000, float(np.nansum(C[v])) / 1000
    state = {"region": AOI_NAME, "scored_ha": int(v.sum()),
             "N_t_per_yr": round(n_t, 0), "C_t_per_yr": round(c_t, -2),
             "urea_bags_per_yr": round(n_t * 1000 / UREA_N / BAG_KG, -3),
             "urea_rs_crore_per_yr": round(n_t * 1000 / UREA_N / BAG_KG * BAG_RS / 1e7, 1),
             "N_kg_per_ha_median": round(float(np.nanmedian(N[v])), 2),
             "topsoil_mm_per_yr_median": round(float(np.nanmedian(mm[v])), 2),
             "topsoil_mm_per_yr_mean": round(float(np.nanmean(mm[v])), 2),
             "soil_N_gkg_median": round(float(np.nanmedian(n[v])), 2),
             "soil_C_gkg_median": round(float(np.nanmedian(soc[v])), 1),
             "prices": {"urea_bag_kg": BAG_KG, "urea_bag_rs": BAG_RS, "urea_N": UREA_N},
             "enrichment_ratio": 1}
    # by land cover: on cropland the urea framing is fair; on tree land the tonnes hang on the
    # provisional tree cover value (V-02), so the lower-tree-C run is given beside them
    lc = rd(FEA / "lc_class_cat.tif")
    A_alt = np.where(ok, rd(E / "erosion_A_treeC_alt_tpha.tif"), np.nan)
    by = {}
    for name, codes in (("cropland", (40,)), ("tree", (10,)), ("shrub_grass", (20, 30)), ("other", None)):
        sel = v & (np.isin(lc, codes) if codes else ~np.isin(lc, (10, 20, 30, 40)))
        nt = float(np.nansum(N[sel])) / 1000
        nt_alt = float(np.nansum((A_alt * n)[sel])) / 1000
        by[name] = {"ha": int(sel.sum()), "N_t_per_yr": round(nt, 0), "N_t_per_yr_low_treeC": round(nt_alt, 0),
                    "N_kg_per_ha_mean": round(1000 * nt / max(int(sel.sum()), 1), 1),
                    "N_kg_per_ha_median": round(float(np.nanmedian(N[sel])), 1) if sel.any() else None,
                    "urea_bags_per_ha_mean": round(1000 * nt / max(int(sel.sum()), 1) / UREA_N / BAG_KG, 2),
                    "urea_rs_crore_per_yr": round(nt * 1000 / UREA_N / BAG_KG * BAG_RS / 1e7, 1),
                    "topsoil_mm_per_yr_median": round(float(np.nanmedian(mm[sel])), 2) if sel.any() else None}
    state["by_cover"] = by
    state["N_t_per_yr_low_treeC"] = round(float(np.nansum((A_alt * n)[v])) / 1000, 0)
    (ROOT / "reports" / f"erosion_soil_value_{AOI_NAME}.json").write_text(json.dumps(state, indent=2))
    print(json.dumps(state, indent=1))
    print(dd.sort_values("N_kg_per_ha", ascending=False).head(6)[["NAME_2", "N_kg_per_ha", "urea_bags_per_ha",
                                                                   "urea_rs_per_ha", "topsoil_mm_per_yr"]].to_string(index=False))


if __name__ == "__main__":
    main()
