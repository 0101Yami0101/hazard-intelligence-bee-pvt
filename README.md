# SlopeSense — Hazard Intelligence Platform · Arunachal Pradesh and Assam

Landslide and flood forecasting for Arunachal Pradesh, and soil-erosion risk for
Assam, built on one shared hazard-agnostic core. Four modules ship behind a
single Streamlit app. (Until 2026-10-11 the
landslide module itself was called SlopeSense; it is now SlideSense, and
SlopeSense is the platform.)

| Module | What it is | State |
|---|---|---|
| **SlideSense** | Landslide forecast | live |
| **FloodSense** | Flood forecast | live — static layer unvalidated by design, see [FLOOD_MODULE.md](docs/design/FLOOD_MODULE.md) |
| **SoilSense** | Soil-erosion risk, priority list and weekly outlook for Assam | building — first version in the app, see [SOILSENSE.md](docs/design/SOILSENSE.md) |
| **Data Backbone** | Source catalogue + pipeline view | live |

## What's actually built

Measured, not claimed — the fuller accounting is in
[PLATFORM_ARCHITECTURE.md](docs/design/PLATFORM_ARCHITECTURE.md).

- **29 external sources**, 14 groups, 10,853 files, 308 GB (300 GB of it radar
  scenes from flood dates; 8 GB the rest), every fetch
  recording source, licence, URL, fetch date and checksum
- **One canonical grid**: EPSG:32646, 100 m, 8,202,343 in-state cells
- **34 features per cell** — terrain, soil, geology, land cover, hydrology,
  distances
- **LightGBM susceptibility** at spatial-CV AUC 0.859, plus a percentile
  trigger over 9,555 days of rainfall history

- **Flood forecast loop closed** (since 2026-09-21/22): a daily 08:30 run on
  live rain, river gauges and (flat ground) soil wetness; every forecast logged
  to `records/flood_forecast/` and graded automatically against the gauges

- **The backbone moved to a second state** (since 2026-10-17): every fetch and
  build takes `REGION=assam`, and SoilSense runs the soil-loss recipe on Assam's
  own 100 m grid, ranking 703 small catchments and 35 districts for
  conservation work. Start at [SOILSENSE.md](docs/design/SOILSENSE.md)

Planned but not built: own sensors, partner intake, a public API, and the same
forecast archive and outcome log for landslides.

## Layout

```
webapp/     the deployed app — shell, shared core, one folder per module
scripts/    fetch → build → model → viz, run by hand one stage at a time
models/     trained susceptibility folds + trigger
docs/       design notes, data research, feasibility writeups
reports/    validation output and figures
data/       gitignored — 4+ GB, regenerable via scripts/fetch/
```

## Running it

The app is self-contained: it reads a 15.7 MB bundle in `webapp/assets/` and
calls a free weather service. No database, no API key.

```bash
pip install -r requirements.txt
streamlit run webapp/app.py
```

The geospatial and ML stack (rasterio, geopandas, lightgbm, pysheds) is only
needed to rebuild the bundle, not to serve it — that's what lets the app run on
a free 1 GB host. See [webapp/DEPLOY.md](webapp/DEPLOY.md).

## Codebase map

An interactive map of the whole system — parts, journeys, every file, the data
and the roadmap, in plain words: [docs/codebase-map/](docs/codebase-map/README.md),
live at https://claude.ai/artifact/Ej7MuYSgwAVFoNotfhyFEa. Open
`docs/codebase-map/index.html` locally, or rebuild it after a change:

```bash
node scripts/codebase-map/scan.mjs           # writes data.js, lists anything undescribed
node scripts/codebase-map/scan.mjs --check   # fails if the map is out of date
```

## Notes

Credentials, investor material and raw data are excluded by `.gitignore` and
never belong in this repo.
