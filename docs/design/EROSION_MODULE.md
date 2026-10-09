# SoilSense — soil erosion risk, monitoring and outlook (3rd module, Assam-first)

> **Status: DESIGN — nothing built yet.** Written 2026-09-29.
> **Target:** NESFIC 2026 problem statement **NESFIC-D-07 "Soil Erosion Risk Mapping &
> Monitoring"**, Soil Conservation Department, Government of Assam. Applications close
> **25 Oct 2026**.
> **Working plan (phases, tasks, status):** [EROSION_PLAN.md](EROSION_PLAN.md).
> Companion docs: [PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md),
> [DATA_CONTRACT.md](DATA_CONTRACT.md), [FLOOD_MODULE.md](FLOOD_MODULE.md).
> "SoilSense" is a working name — decision D2 in the plan.

## Contents

0. [The short version](#0--the-short-version)
1. [What the department asked for, and our answer to each line](#1--what-the-department-asked-for)
2. [Why this module, and why Assam](#2--why-this-module-and-why-assam)
3. [What we already have](#3--what-we-already-have)
4. [What changes](#4--what-changes)
5. [The method](#5--the-method)
6. [What a user sees](#6--what-a-user-sees)
7. [Validation — how we will know it works](#7--validation)
8. [Tiers — FREE / ASK / PAID](#8--tiers)
9. [Limits, and which kind each one is](#9--limits-and-which-kind-each-one-is)
10. [Risks and traps we have already paid for once](#10--risks-and-traps)
11. [Scope — what this module is not](#11--scope)
12. [Data sources](#12--data-sources)
13. [Glossary](#13--glossary)

---

## 0 · The short version

The department wants to know **where soil is being washed away, which places to survey
and treat first, and how that changes over time.**

Soil loss from rain has a well-known recipe with five ingredients:

```
  how hard the rain hits  ×  how easily the soil washes  ×  how steep and long the slope is
                          ×  how bare the ground is      ×  whether it is protected (bunds, terraces)
        R                          K                               LS
                                   C                               P
```

The department's own problem statement names the same five: *"Erosion risk is influenced
by rainfall, soil, slope, vegetation cover and land use."* **Four of the five are already
built into our backbone for Arunachal** (rain archive, soil, terrain, land cover). The
fifth (protection) is unknown everywhere until the department shares its treated-area
records, so we start by showing "if untreated".

So the module is three things:

1. **Port the backbone to Assam.** Every fetch and build is wired to Arunachal today. Making
   it run for a second state with a region switch is the proof that the backbone idea is
   real, and it is most of the work.
2. **Compute the recipe on the shared grid**, then refresh the fast-changing parts — bare
   ground every season from satellite, rain every day from the live feed FloodSense already
   pulls.
3. **Turn it into decisions:** a ranked list of micro-watersheds and villages, each with
   the main reason it is high, exportable for field teams, with their checks flowing back
   in.

> **Framing rule (same as SlopeSense and FloodSense).** The headline is a *living*
> outlook — updated each season and each week, logged and graded — not a static risk map.
> For this department the risk map and priority list are themselves asked-for
> deliverables, so they are shown, but as the base layer the outlook updates.

---

## 1 · What the department asked for

Source: `startup.assam.gov.in/nesfic26/problem-statements/nesfic-d-07`, read 2026-09-29.

| The department's words | How SoilSense answers it | Phase |
|---|---|---|
| "Large-area identification and mapping of erosion-prone areas" | Statewide soil-loss estimate and risk classes on the 100 m grid, all of Assam (78,438 km²) | P0 |
| "Prioritisation of intervention locations" | Ranked micro-watersheds and villages, each with its **main driver named** (bare ground / steep-long slope / erodible soil / heavy rain) | P0 first cut, P1 watershed units |
| "Faster preliminary assessment" | Search any village (existing search and gazetteer) → one card: class, driver, trend, this week's rain | P0 map, P2 card |
| "Periodic monitoring … temporal comparison functionality" | Bare-ground layer refreshed every season from Sentinel-2; season-vs-season and year-vs-year change back to 2019; weekly rain outlook | P1–P2 |
| "Better targeting of soil-conservation resources" | Driver → treatment hint (bare → revegetation/agroforestry; steep-long → contour bunds/terraces); "untreated potential" view | P2 |
| "Combining spatial and environmental inputs into erosion-risk layers" | The five factor layers, each viewable on its own | P0 |
| "Classification/prioritisation of areas by risk level" | Standard soil-loss classes (scheme confirmed with the department — decision D4) | P0 |
| "GIS outputs usable for planning and field verification" | GeoPackage / KML / CSV exports, plus a field-check form whose answers come back into the system | P2 |
| Pilot: "Selected Assam areas where soil erosion is a known concern, with comparison against field observations" | Pre-registered field comparison: points handed out **without our class shown**, pass bars written before the visits (§7, V5) | P2–P3 |
| "Satellite data may be accessed through ASSAC; soil/topographic/rainfall and field information may be added subject to availability" | We start on open data and do not wait. Department and ASSAC data slot in as upgrades (§8, ASK) | all |
| Tag "IoT & Sensors" | PAID option: rain-intensity gauges and stream turbidity sensors at pilot watershed outlets give a *measured* signal to grade against | P3 option |

---

## 2 · Why this module, and why Assam

**Same drivers, different target.** SlopeSense already uses slope, soil texture, land cover,
flow accumulation and a 26-year rain archive. Erosion needs the same layers combined
differently — it is a new question asked of the same backbone, not a new project.

**Assam is the hardest honest test of the backbone.** Arunachal is mountains (median slope
29°). Assam is mostly flat floodplain, with hill districts (Karbi Anglong, West Karbi Anglong,
Dima Hasao), foothill belts and hillocks. If the same chain — fetch → grid → terrain →
features → rain → model → app — runs there with only a region switch, then "the next state
is cheap" has been **shown, not claimed**. This module tests two things at once: a new hazard
*and* a new state.

**It makes the platform regional, not state-bound.** Assam's floods start in Arunachal's
rivers. A region-aware backbone is also the precondition for FloodSense on Assam
(NESFIC-D-18, "Digital Twin for Flood Management") and SlopeSense on Assam's hill
districts. Neither is in this plan, but both get cheaper because of it.

---

## 3 · What we already have

**Short answer: most of the code and about half of Assam's raw data. But nothing runs for
Assam yet**, because every fetch and build is wired to Arunachal (§4.1).

| Piece | Where it lives | Arunachal today | For Assam | Reuse |
|---|---|---|---|---|
| Grid rules and data contract | `scripts/build/grid.py`, [DATA_CONTRACT.md](DATA_CONTRACT.md) | 100 m, EPSG:32646, 8,202,343 cells | Same map projection fits Assam (area within 0.05% of official). Needs its own extent | Rules as-is; new region spec |
| Raw store + provenance | `common.record()`, `_SOURCES.json` | Every fetch logged with licence and checksum | Same | As-is |
| Elevation (Copernicus 30 m) | `fetch_02_terrain.py` | 28 tiles | **12 of ~32 Assam tiles already on disk** (N26–N27 × E091–E096); ~20 to fetch | Fetch with new box |
| Slope, curvature, relief (slope computed at 25 m, then aggregated) | `scripts/build/terrain.py` | Built | Rebuild | Code as-is once region-aware |
| Flow routing, wetness index, channels, height above drainage | `hydrology.py`, `build_hand_100m.py` | Built | Rebuild | As-is. The LS factor is a small addition here |
| Soil: sand, silt, clay, organic carbon, bulk density, stones, 3 depths | `fetch_03_soil.py`, `build/features.py` | 18 layers on grid | Re-pull with Assam's box (minutes, open service) | **The K factor needs exactly these** |
| Land cover (ESA WorldCover 10 m, 2021) | `fetch_04_landcover.py` | 6 tiles | The 6 tiles on disk cover Assam except a strip west of 90°E (1–2 tiles) | As-is; fallback cover layer |
| Rain archive (IMERG daily, 2000-06 → now) | `fetch_11b_imerg_archive.py`, `rainfall_stack.py` | 9,555 days | New box pull, ~2 h (request-latency bound, ~34 kB/day) | Code as-is; the R factor is new |
| Live forecast rain (Open-Meteo) | `fetch_20…`, `flood_forecast_live.py` | Pulled daily at 08:30 for FloodSense | Add Assam points | Reuse the feed |
| Soil wetness (ERA5-Land) | `fetch_39_era5land_soil.py` | Built for floods | Optional | Later |
| Earth Engine access | `fetch_32/37/38…` (radar screens) | Working | Same account | Sentinel-2 cover composites are new code on known plumbing |
| River basins (HydroBASINS levels 1–12, HydroRIVERS) | `data/raw/05_hydrology/hydrosheds/` | Clipped to Arunachal | **Asia-wide files already on disk** — clip locally, no download | As-is |
| Boundaries (GADM India) | `data/raw/01_boundaries/gadm41_IND.gpkg` | Arunachal | Assam is in the same file, **but GADM has only 27 Assam districts (outdated)**. Current districts come from the Assam State Geoportal | Plus one official boundary fetch |
| Honest-training pattern (50 km spatial folds, out-of-fold scores, full model to ship) | `train_susceptibility.py` | LightGBM | Used only in Phase 3, if field labels arrive | Pattern |
| Forecast log + grading loop | `forecast_log.py`, `flood_intake.py` | FloodSense | Same pattern for the weekly outlook and field reports | Pattern |
| "Prove nothing changed" harness | `check_live_unchanged.py` | FloodSense | Guards the refactor in §4.1 | As-is |
| Web app shell (registry, search, map, 3D, theme, settings) | `webapp/core/`, `webapp/products/__init__.py` | 3 modules | New folder plus one registry entry, **plus region-awareness** | As-is + region |
| Data Backbone module | `webapp/products/backbone/` | Arunachal catalogue | Shows both regions | Extend |

---

## 4 · What changes

### 4.1 Make the backbone region-aware — this is the proof itself

**Measured coupling (2026-09-29):** 33 scripts import the Arunachal bounding box or name, 29
import the grid, 69 contain the literal "arunachal" (mostly output file names), 15 web-app
files mention it.

**Design:**

- **One region registry**, in one place: name, bounding box, CRS, grid origin and extent,
  boundary source. The `arunachal` entry is **byte-identical** to today's constants, so no
  Arunachal file is rebuilt and the live 08:30 FloodSense job is untouched. This is proven
  with `check_live_unchanged.py`, not assumed.
- Selected by a `--region` flag or `REGION` environment variable; default `arunachal`.
- **Assam grid spec (proposed; frozen in plan task E0.2):**

  | | Arunachal (frozen) | Assam (proposed) |
  |---|---|---|
  | CRS | EPSG:32646 | EPSG:32646 — same. Assam's area in it: 78,474 km² vs official 78,438 (+0.05%). The westernmost 0.3° lies outside UTM zone 46, which is immaterial |
  | Cell | 100 m | 100 m |
  | Origin (x, y bottom) | 350,000 / 2,950,000 | **160,000 / 2,660,000** |
  | Size | 5,900 × 3,200 | **6,400 × 4,400** (28.2 M box cells, ~7.85 M in-state — same size class as Arunachal, so the same memory and run times) |
  | cell_id | row × 100,000 + col | same scheme, region-local |
  | Folds | 50 km blocks, seed 42, hashed | own blocks, seed 42, frozen and hashed **before** any model |

- **Lattice-aligned.** Both origins are whole multiples of 100 m, so Assam's cells line up
  exactly with Arunachal's where the two boxes overlap (northings 2,950–3,100 km). A river
  catchment crossing the border can later be stitched cell for cell.
- **Rejected: one big North-East grid.** It would renumber every Arunachal cell, and under
  DATA_CONTRACT's change policy that voids every number we have reported.
- **Region-scoped folders** for Assam: `data/interim/assam/`, `data/processed/assam/`,
  `webapp/assets/…/assam/`. Whether Arunachal moves into the same layout is decision D1.
- **Port only the chain erosion needs:** boundaries → DEM → terrain → hydrology → soil and
  land-cover features → rain archive → live rain points. Flood and landslide model scripts
  are not ported in this module.
- **Web app:** base assets per region, a region picker in the shell, and "Arunachal" in
  interface text becomes the region's name.

### 4.2 New erosion pieces

| New piece (proposed name) | What it does | Built on |
|---|---|---|
| `scripts/build/erosion_factors.py` | K, LS, long-term R, fallback C, P = 1 → soil-loss estimate and classes, per region | features, terrain, hydrology, rain stack |
| `scripts/fetch/fetch_40_s2_cover.py` | Seasonal Sentinel-2 cover composites (pre-monsoon, post-monsoon, winter), 2019 → now, via Earth Engine → C per season, with each composite's cloud share recorded | Earth Engine plumbing from the radar work |
| `scripts/build/erosivity.py` | R: annual normal (P0); event-based, calibrated on half-hourly IMERG (P1); next-7-day from the live forecast (P2) | IMERG archive, Open-Meteo feed |
| `scripts/model/erosion_priority.py` | Aggregate to micro-watersheds and villages, rank, name the main driver | HydroBASINS level 12 first; Watershed Atlas micro-watersheds if obtainable |
| `scripts/model/erosion_change.py` | Season-vs-season and year-vs-year change; "new bare ground on a steep slope" flags | S2 composites |
| `scripts/model/erosion_outlook.py` | Weekly outlook, logged every day like FloodSense | `forecast_log.py` pattern |
| Field export + intake | GeoPackage / KML / CSV out; field-check answers in, quarantined (PLATFORM_ARCHITECTURE step 5) | `flood_intake.py` pattern |
| `webapp/products/erosion/` | Manifest, view, model, data — one registry entry | Product registry |

---

## 5 · The method

### 5.1 Same shape as the other two modules

```
  WHERE  (static)     how easily this ground loses soil      K × LS  (× P)
  COVER  (seasonal)   how bare it is right now               C       ← satellite, every season
  WHEN   (daily)      how hard the rain will hit             R       ← normal / season so far / next 7 days

  soil-loss estimate  A = R × K × LS × C × P          (RUSLE, in t/ha/yr)
```

**Why the recipe first, not machine learning.** We have no measured soil-loss labels. As
with landslides, the method follows the labels ([DESIGN.md](DESIGN.md), model-choice table). RUSLE needs
no labels, so it works on day one. Every factor is explainable, and the biggest factor tells
the department *which kind of treatment fits*. It is also the recipe Indian soil and land-use
survey work already uses, so officials will recognise it. Machine learning comes in only as a
**correction layer** once field observations exist (Phase 3), trained with the same
spatial-fold discipline as SlopeSense.

### 5.2 The five factors

| Factor | Plain meaning | How we compute it | Resolution | Refresh |
|---|---|---|---|---|
| **R** rain erosivity | How hard the rain hits | **P0:** annual-rainfall relation widely used in Indian RUSLE work, R = 79 + 0.363 × annual rain in mm (Singh et al. 1981 — **confirm units and coefficients in E0.6**), from 26 years of IMERG. **P1:** event-based from half-hourly IMERG. Cross-checked against the global GloREDa erosivity map | ~11 km rain cell, smoothed | Yearly normal; season so far; next 7 days |
| **K** soil erodibility | How easily this soil washes | Williams (1995) EPIC equation from SoilGrids topsoil sand, silt, clay and organic carbon | 250 m → 100 m | Static |
| **LS** slope length × steepness | Steepness × how much water runs down onto this spot | Moore & Burch form, LS = (As/22.13)^0.4 × (sin β / 0.0896)^1.3, from flow accumulation and slope. **Computed on 25 m sub-cells, then aggregated** (same reason as `terrain.py`: coarsening first under-states steepness). Slope length capped (≈300 m, tuned in E0.6); channel cells masked | 25 m → 100 m | Static |
| **C** cover | How bare the ground is | C = exp(−2 × NDVI / (1 − NDVI)) (van der Knijff et al.) from Sentinel-2 seasonal composites; land-cover class lookup as fallback where clouds leave gaps | 10 m → 100 m | Every season |
| **P** support practice | Bunds, terraces, contour farming | **P = 1 everywhere at FREE tier, meaning "if untreated"**; department treated-area records at ASK | — | When records arrive |

**Classes.** A common Indian six-class scheme is slight < 5, moderate 5–10, high 10–20, very
high 20–40, severe 40–80, very severe > 80 t/ha/yr. **Confirm which scheme the department
uses (decision D4)** — using theirs makes our map directly comparable with their own work.

### 5.3 Score only where the recipe applies

Following the DATA_CONTRACT §7 rule (out-of-domain cells are masked, never scored), these
are shown as **"not assessed by this method"**, never as "low":

- water and built-up land;
- channel cells (flow accumulation above the channel threshold);
- floodplain flats (height above nearest drainage below a few metres).

Erosion in the last two is a *river* process — bank cutting, sand-casting — not rain washing
soil off a slope. Calling a riverbank village "low erosion risk" because RUSLE can't see bank
erosion would be the worst possible error for Assam.

### 5.4 The seasonal story — why "periodic updates" matter here

In the hill districts, shifting cultivation (*jhum*) plots are typically cut and burnt in
roughly January–March and sown around April. So **bare, freshly cleared slopes meet the first
heavy storms in April–June** — the highest-loss window of the year. The pre-monsoon months are
also the clearest skies of the rainy half-year, so Sentinel-2 sees the ground well exactly
when it matters.

That gives the most useful watch product: **each spring, a list of newly bared steep plots
before the rains arrive**, ranked by this season's expected rain. That is something a field
team can act on in time.

### 5.5 Priority ranking

- **Unit:** micro-watershed, the unit soil-conservation works are planned in. Start with
  HydroBASINS level 12 (on disk). Switch to the national Watershed Atlas micro-watersheds if
  obtainable (E0.11). Also rank by village / revenue circle for field teams.
- **Score per unit:** share of land in high-and-above classes, mean estimated loss, trend
  (is it getting barer?), and optionally what lies downstream (farmland, settlements,
  reservoirs). **The weights are shown and the department can adjust them.**
- **Every unit gets a reason line**, for example *"main driver: bare ground (cover) — steep
  slopes cleared since last winter"*. That line is what turns a map into a work order.

### 5.6 Change and comparison

- **Cover change** is real and observable: season against the same season last year, and
  year by year back to 2019 (the Sentinel-2 era; Landsat if older is ever needed).
- **Estimated-loss change** is derived: it follows from cover change and rain.
- "New bare ground on a steep slope" is flagged — **but only after the change detector has
  passed a no-change specificity test** (§10, the S1 lesson).

---

## 6 · What a user sees

| Screen | Contents |
|---|---|
| **Map** | Risk classes; each factor as its own layer; change since last season or year; "not assessed" areas shown distinctly |
| **Priority list** | Ranked micro-watersheds and villages, main driver, trend, adjustable weights |
| **Place card** | Search any village → class, main driver, trend, this week's rain outlook, treatment hint |
| **Field** | Export for field teams; the field-check form |
| **How to read this** | Method page in plain words, like FloodSense's |

**Kinds of number, labelled as such** (the FloodSense badge approach):

- *estimate* — tonnes per hectare per year. Indicative, can be off by a factor of several.
- *class* — relative. More trustworthy than the tonnes.
- *rank* — what to act on.

We never present a class or a rank as a probability.

---

## 7 · Validation

**Principle:** no statewide measured soil-loss map exists anywhere. So we check the
**ranking** against several independent, imperfect references, and **write every pass bar
before looking** (the [OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md) discipline).

| # | Test | Against | Needs anyone's permission? |
|---|---|---|---|
| V1 | Sanity | Factor ranges vs literature; share of state per class; **hills ≫ plains** (if not, something is broken); the canopy-edge trap test (§10) | No |
| V2 | Cross-map agreement | NRSC land-degradation "water erosion" classes (Bhuvan); SLUSI priority watersheds (Sediment Yield Index); global soil-erosion map (Borrelli et al.). Rank agreement per district and watershed | No — access to be checked (E0.11) |
| V3 | **Measured sediment** | Suspended sediment at river gauging stations (CWC / India-WRIS), compared with our catchment totals, ranked across catchments. The only truly measured quantity | No — availability to be checked |
| V4 | Blind imagery sample | ~300 points stratified by class, labelled from high-resolution imagery (visible rills, gullies, bare slopes) **without seeing our class** — our own labels, no ask needed | No |
| V5 | Field comparison (pilot) | Department field teams receive points **without our class shown**. Metrics: ranking AUC; share of high-class points with observed erosion vs low-class | Department (pilot) |
| V6 | Weekly outlook | Rain part: forecast erosive rain vs observed IMERG, graded daily. Soil-loss part: gradable only with PAID sensors or field reports — **said plainly on the method page** | No / PAID |

---

## 8 · Tiers

| Tier | What it delivers | What it adds over the tier below |
|---|---|---|
| **FREE** (open data, now) | Statewide 100 m estimate, classes and ranking; seasonal cover refresh; weekly outlook from forecast rain; units = micro-watershed and village | — |
| **ASK** (department / ASSAC data) | Soil survey maps replace SoilGrids → better K. Treated-area records → real P (treated vs untreated). Rain gauges with intensity (IMD / ASDMA) → better R. Field observation records → calibration and an ML correction layer. ASSAC high-resolution imagery → gully mapping in pilot areas. Official micro-watershed boundaries | Confidence in the absolute numbers; treatment-aware ranking |
| **PAID** (sensors, drones) | Rain-intensity gauges + stream turbidity/sediment sensors at 2–3 pilot watershed outlets → measured sediment to grade and calibrate the outlook. Repeat drone surveys → measured gully growth. Field app | Measured truth at pilot sites; a gradable outlook |

As with the other modules, **the ranking should already be usable at FREE** — to be proven by
V2–V5, not assumed. The higher tiers mainly buy confidence in the tonnes, finer units and a
gradable outlook.

---

## 9 · Limits, and which kind each one is

| Limit | Kind | What lifts it |
|---|---|---|
| Satellite rain misses the short, intense bursts that do most of the eroding → R reads low in absolute terms | **Budget** | Intensity gauges (ASK / PAID) |
| SoilGrids is a 250 m global model | **Budget** | Department / NBSS&LUP soil survey (ASK) |
| Clouds hide the ground for much of the monsoon | **Physics** (optical satellites) | Pre- and post-monsoon composites (the pre-monsoon one is what matters most, §5.4); radar as a partial proxy |
| Copernicus DEM is a *surface* model (treetops, roofs) → fake slopes at forest and tea-garden edges on flat land | **Data** | Plains filter (E0.7); a bare-earth DEM (ASK) |
| RUSLE covers sheet and rill erosion only — **not gullies, riverbanks or landslides** | **Method** | Separate detectors (§11 extensions) |
| Absolute tonnes uncertain by a factor of several | **Method** | Calibration against measured sediment (PAID) and field data (ASK) |
| Protection (P) unknown → map shows "if untreated" | **Budget** | Treated-area records (ASK) |

---

## 10 · Risks and traps

Most of these are lessons we have already paid for once on landslides or floods.

| Trap | Where we learned it | Guard |
|---|---|---|
| Canopy edges on flat land look like 20° slopes in a surface DEM → fake LS hotspots along tea gardens and forest edges | The Bhuvan flood mask put 70.5% of its flood on cliffs. Always check *where* a layer puts its extremes | Pre-registered test E0.7: share of high-LS cells on flat land sitting on a tree/non-tree edge. Filter or cap LS on plains |
| A recipe tuned for hills, applied to plains | Flood WHERE scored glacial lakes as floodplain; validation can't see out-of-distribution | Domain mask (§5.3); report hills and plains separately |
| Showing a derived score as a chance | "A percentile max is not a probability" | Kinds-of-number badges (§6) |
| Claiming satellite-detected change without testing false alarms | The S1 "confirmation" passed 97–100% of flood-free dates | Specificity test on known no-change areas before any change flag (E1.2) |
| Outdated district boundaries | GADM has 27 Assam districts | Official boundary from the Assam State Geoportal (E0.2) |
| Scope creep into riverbank erosion before the core works | — | Kept as extension X1, decided in Phase 3 |
| Licences | Open-Meteo's free tier is non-commercial (already flagged in PLATFORM_ARCHITECTURE) | Affects the weekly outlook if sold. SoilGrids / WorldCover are CC-BY; Copernicus DEM needs attribution. **Avoid FABDEM** (non-commercial) |
| Deadline | Applications close 25 Oct 2026 | Phase 0 targets 18 Oct, one week of margin |

---

## 11 · Scope

**In:** rain-driven sheet and rill erosion on land, statewide Assam, plus Arunachal almost
free because its inputs already exist. Risk classes, priority ranking, seasonal monitoring
and change, weekly outlook, field loop.

**Not in the core — extensions, decided in Phase 3:**

| # | Extension | Why it's tempting | Why it waits |
|---|---|---|---|
| X1 | **Riverbank erosion watch** (Brahmaputra, Barak): yearly bank lines from Landsat / Sentinel water masks → retreat per km of bank → villages next in line | Assam's largest erosion loss by area. Ties directly into FloodSense's gauges | A river process and a different department (Water Resources). Must not dilute the D-07 answer |
| X2 | Gully mapping from high-resolution imagery in pilot areas | RUSLE can't see gullies | Needs ASSAC imagery (ASK) |
| X3 | Sand-casting (flood deposits on farmland) | Real loss in Assam's plains | Belongs with FloodSense |
| X4 | SlopeSense and FloodSense for Assam | Fall out of the same region port | Separate problem statements (FloodSense ↔ D-18) |

---

## 12 · Data sources

| Source | Used for | Status | Access / licence |
|---|---|---|---|
| Copernicus DEM GLO-30 | LS, terrain, flow | Arunachal on disk; ~20 Assam tiles to fetch | Open, attribution |
| SoilGrids 2.0 (ISRIC) | K | Arunachal on disk; Assam re-pull | Open WCS, CC-BY 4.0 |
| ESA WorldCover 2021 | C fallback, domain mask | Most of Assam on disk; 1–2 tiles | Open, CC-BY 4.0 |
| Sentinel-2 L2A (via Earth Engine) | C per season, change | New | Open; our Earth Engine account |
| GPM IMERG (daily; half-hourly sample) | R | Arunachal box on disk; Assam box ~2 h | Open, NASA Earthdata login |
| Open-Meteo forecast | Weekly R | Live for Arunachal | Free tier non-commercial ⚠️ |
| HydroBASINS / HydroRIVERS | Units, channels | Asia-wide on disk | Open |
| GADM 4.1 | Quick boundary | On disk (outdated districts) | Non-commercial ⚠️ — replace with official |
| Assam State Geoportal | Official boundaries | To fetch | Listed on NESFIC resources page |
| NESDR land-cover layers (NESAC) | Seasonal land use cross-check | WMS open, not harvested | Registration for download |
| NRSC land degradation (Bhuvan) | V2 | To check (E0.11) | Bhuvan WMS pattern |
| SLUSI priority watersheds / Watershed Atlas | V2, planning units | To check (E0.11) | — |
| CWC / India-WRIS sediment | V3 | To check (E0.11) | — |
| GloREDa erosivity; global soil-erosion map (Borrelli et al.) | R cross-check, V2 | To check (E0.11) | ESDAC registration |
| Department: soil survey, treated areas, field records; ASSAC imagery | ASK tier | Requested only after the FREE version works | Per problem statement |

---

## 13 · Glossary

| Term | Plain meaning |
|---|---|
| **RUSLE** | The standard recipe: soil loss = rain force × soil weakness × slope × bareness × protection |
| **R / K / LS / C / P** | Those five ingredients, in that order |
| **t/ha/yr** | Tonnes of soil lost per hectare per year |
| **Micro-watershed** | A small patch of land that drains to one stream point — the unit conservation work is planned in |
| **Height above nearest drainage** | How far a spot sits above the nearest stream; low means river-flat ground |
| **Surface vs bare-earth DEM** | A surface model includes treetops and roofs; a bare-earth model is the ground itself |
| **Composite** | Many cloudy satellite passes merged into one clear picture per season |
| **Jhum** | Shifting cultivation: clear, burn, farm a few years, move on |
| **Pre-registered test** | Pass/fail bar written down before looking at the result, so we can't fool ourselves |
| **Out-of-fold score** | A score from a model that never saw that part of the map — the honest number |
