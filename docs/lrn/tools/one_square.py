"""Read every backbone layer for one 100 m square: the Phase 2 exercise.

    .venv\\Scripts\\python docs\\lrn\\tools\\one_square.py 27.5494 93.8159
    .venv\\Scripts\\python docs\\lrn\\tools\\one_square.py 28.0660 95.3260 "Pasighat"

Give a latitude and longitude (Google Maps: right-click a spot, click the
numbers to copy them). It prints the square's cell id, its 34 facts plus HAND,
in plain units, and its rain history. Arunachal only, and it needs the local
data/ folder (it reads data/interim/, never writes anything).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "build"))
import grid  # noqa: E402

INTERIM = ROOT / "data" / "interim"

# (file stem, plain name, how to turn the stored number into plain units, source)
LAYERS = [
    ("terrain/dem_elev_m", "height above sea", lambda v: f"{v:,.0f} m", "Copernicus DEM, 30 m"),
    ("terrain/terrain_slope_deg", "steepness (average)", lambda v: f"{v:.1f}°", "from the DEM"),
    ("terrain/terrain_slope_max_deg", "steepness (steepest 25 m bit)", lambda v: f"{v:.1f}°", "from the DEM"),
    ("terrain/terrain_relief_m", "high minus low inside the square", lambda v: f"{v:.0f} m", "from the DEM"),
    ("terrain/terrain_northness", "faces north (+1) or south (-1)", lambda v: f"{v:+.2f}", "from the DEM"),
    ("terrain/terrain_eastness", "faces east (+1) or west (-1)", lambda v: f"{v:+.2f}", "from the DEM"),
    ("terrain/terrain_curv_prof", "bends down-slope (+ convex)", lambda v: f"{v:+.3f}", "from the DEM"),
    ("terrain/terrain_curv_plan", "bends across-slope (+ spreads water)", lambda v: f"{v:+.3f}", "from the DEM"),
    ("terrain/hydro_flowacc_cells", "squares draining through here", lambda v: f"{v:,.0f}", "from the DEM"),
    ("terrain/hydro_twi", "wetness index (high = wet hollow)", lambda v: f"{v:.1f}", "from the DEM"),
    ("terrain/hydro_hand_m", "height above nearest stream (HAND)", lambda v: f"{v:.1f} m", "from the DEM"),
    ("terrain/hydro_chan_km2", "land draining to that stream", lambda v: f"{v:,.1f} km²", "from the DEM"),
    ("terrain/dist_river_m", "distance to a mapped river", lambda v: f"{v:,.0f} m", "HydroSHEDS rivers"),
    ("terrain/dist_road_m", "distance to a road", lambda v: f"{v:,.0f} m", "OpenStreetMap"),
    ("terrain/dist_lineament_m", "distance to a fault line", lambda v: f"{v:,.0f} m", "APSSDI (APSAC)"),
    ("features/lc_class_cat", "land cover", None, "ESA WorldCover 2021"),
    ("features/geol_rockgr_cat", "rock group", None, "APSSDI (APSAC)"),
    ("features/geol_lithunit_cat", "rock type", None, "APSSDI (APSAC)"),
]
SOIL = [("clay", "gkg", "clay", lambda v: f"{v/10:.0f}%"),
        ("sand", "gkg", "sand", lambda v: f"{v/10:.0f}%"),
        ("silt", "gkg", "silt", lambda v: f"{v/10:.0f}%"),
        ("bdod", "cgcm3", "density", lambda v: f"{v/100:.2f} g/cm³"),
        ("cfvo", "cm3dm3", "stones", lambda v: f"{v/10:.0f}%"),
        ("soc", "dgkg", "organic carbon", lambda v: f"{v/10:.0f} g/kg")]
DEPTHS = ["0-5cm", "15-30cm", "60-100cm"]


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    sys.stdout.reconfigure(encoding="utf-8")   # ° and ² on a Windows console
    lat, lon = float(sys.argv[1]), float(sys.argv[2])
    name = sys.argv[3] if len(sys.argv) > 3 else f"{lat}, {lon}"
    x, y = Transformer.from_crs("EPSG:4326", grid.CRS, always_xy=True).transform(lon, lat)
    r, c = grid.xy_to_rowcol(x, y)
    if not (0 <= r < grid.NROWS and 0 <= c < grid.NCOLS):
        raise SystemExit("That point is outside Arunachal's grid box.")

    def read(stem: str) -> float:
        with rasterio.open(INTERIM / f"{stem}.tif") as src:
            return float(src.read(1, window=((r, r + 1), (c, c + 1)))[0, 0])

    with rasterio.open(INTERIM / "state_mask.tif") as m:
        inside = bool(m.read(1, window=((r, r + 1), (c, c + 1)))[0, 0])
    legends = json.loads((INTERIM / "features" / "_legends.json").read_text())

    print(f"\n{name}")
    print(f"  cell_id {grid.encode(r, c)}  =  row {r} x 100,000 + col {c}")
    print(f"  UTM 46N centre x {grid.centre_xy(r, c)[0]:,.0f} m, y {grid.centre_xy(r, c)[1]:,.0f} m")
    print(f"  inside the state: {'yes' if inside else 'NO, values may be blank'}\n")

    for stem, label, fmt, src in LAYERS:
        v = read(stem)
        if np.isnan(v):
            text = "no value"
        elif fmt is None:
            key = Path(stem).name
            text = legends[key].get(str(int(v)), f"code {int(v)}")
        else:
            text = fmt(v)
        print(f"  {label:40s} {text:>24s}   {src}")

    print("\n  soil (SoilGrids 2.0), top / middle / deep:")
    for prop, unit, label, fmt in SOIL:
        vals = [read(f"features/soil_{prop}_{d}_{unit}") for d in DEPTHS]
        shown = ["blank" if (np.isnan(v) or v == 0) else fmt(v) for v in vals]
        print(f"    {label:16s} " + "  /  ".join(f"{s:>10s}" for s in shown))
    print("    (blank: the soil map often has no value under towns, water and ice)")

    rain = np.load(INTERIM / "rainfall" / "precip_mm.npy", mmap_mode="r")
    dates = np.load(INTERIM / "rainfall" / "dates.npy")
    idx = int(read("rainfall/imerg_index"))
    i, j = divmod(idx, rain.shape[2])
    s = np.asarray(rain[:, i, j], dtype=float)
    month = dates.astype("datetime64[M]").astype(int) % 12 + 1
    monsoon = (month >= 6) & (month <= 9)
    r3 = np.convolve(s, np.ones(3), "valid")
    m3 = monsoon[2:]
    print(f"\n  rain (NASA IMERG, 11 km square no. {idx}, {len(s):,} days "
          f"{str(dates[0])[:10]} to {str(dates[-1])[:10]}):")
    print(f"    a year, on average          {s.sum() / (len(s) / 365.25):,.0f} mm")
    print(f"    wettest day on record       {s.max():,.0f} mm on {str(dates[int(s.argmax())])[:10]}")
    print("    3-day monsoon totals: half are under "
          f"{np.percentile(r3[m3], 50):,.0f} mm, 1 in 10 over {np.percentile(r3[m3], 90):,.0f} mm, "
          f"1 in 100 over {np.percentile(r3[m3], 99):,.0f} mm")
    print("    (that 1-in-10 line is roughly where this spot's rain starts to count as unusual)\n")


if __name__ == "__main__":
    main()
