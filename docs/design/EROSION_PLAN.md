# SoilSense build plan — NESFIC-D-07, Assam

> **The working plan.** Update the status column as tasks close. Record every measured
> result in the [Results log](#results-log) (append-only, never overwrite).
> **Design and reasoning:** [EROSION_MODULE.md](EROSION_MODULE.md). This file says *what,
> when, and how we know it's done*; that one says *why*.
> Written 2026-09-29. **Revised 2026-10-17** after a check of every assumption against the
> official challenge pages, the literature and the data itself. See
> [Revision of 2026-10-17](#revision-of-2026-10-17--what-the-check-found) below. Where it
> disagrees with older text in this file, the revision wins.

## Status at a glance

| Phase | Window | Goal | Tasks done |
|---|---|---|---|
| **0 — Application proof** | ~~29 Sep → 18 Oct~~ **17 Oct → 7 Nov 2026** (closes 10 Nov) | A working, honest first erosion map of Assam, built by the same backbone with a region switch, in the app, and the application submitted | 7 / 11 (build tasks E0.1, E0.3, E0.4, E0.6, E0.7, E0.8, E0.9), 2 in progress (E0.2, E0.5: official outline pending); E0.10/E0.11 not started; D8 decided (+ 4 admin tasks, A1–A4). Provisional choices: see the Revisit register |
| 1 — Seasonal cover + validation | Nov → mid-Dec 2026 | Bare ground refreshed per season since 2019; first independent validation | 0 / 9 |
| 2 — Prototype | mid-Dec 2026 → Demo Day, Feb 2027 | Weekly outlook, priority list with reasons, field kit, pilot protocol | 0 / 6 |
| 3 — MVP | Feb → May 2027 | Department data in, field results in, calibrated; optional sensor pilot | 0 / 5 |

Status marks: ☐ to do · ◐ in progress · ☑ done · ✕ dropped (with reason in the Results log)

## Revisit register — provisional choices to come back to

Every choice that is *good enough for now* but not final, in one table, so none is lost.
Each row says what was chosen, why, what would make us change it (the **trigger**), and
where it lives in the code. When a row is resolved, strike it through and add the date
and where the change is logged. Add a row whenever a new provisional choice is made.

| # | What | Current choice | Why it is good enough now | Revisit when (trigger) | Upgrade path | Where |
|---|---|---|---|---|---|---|
| V-01 | Rain factor R | InRESatE (0.1°, 2001–2018); IRED alongside | −5% at the only gauge (Guwahati); IRED −46% | More gauge-derived R values in Assam. **Found 2026-10-20 on NWDP (open): truly hourly CWC rain only from 2019 (about 9 Assam stations, up to about 7 years); daily gauge rain from 1971 (Assam, up to about 80 stations) and 1970 (Arunachal)** (see "Rain-gauge records: what is really there"). Rough hourly anchors, or daily records through InRESatE's own daily-erosivity parameters. **Tested 2026-10-20 (V-01 part 2): InRESatE stays (Assam ρ 0.36 vs IRED 0.20), but both maps flatten the gauges' contrast (log-slope 0.07 / 0.11): dry plains about 2.3× high, wettest foothills about 0.5×. Gauge completeness is uncertain (rainy-days-only records).** Upgrade: a gauge-corrected R surface; or the S7 check fails | Re-anchor on several gauges; extend past 2018 with our own half-hourly IMERG (E1.4) | `erosion_factors.py` `load_r_inresate`; R2/R3 |
| V-02 | **Cover C for "tree"** (D8) | **0.03** as a class average (forest + tea + *jhum* fallow); **0.003** run alongside. **Split attempt 1 (2026-10-20): P1 passed (tea vs forest 0.848), P2 failed (blind check 0.20 / 0.24 / 0.44 against 0.60 / 0.60 / 0.70), so NOT adopted.** Village groves and undated imagery were the main problems (E1.1 part 4) | A mix of about 75% forest (0.003), 15% tea (0.18) and 10% young fallow (0.1) averages about 0.04, so 0.03 is a fair *class* value and matches IWED. Per cell it overstates closed forest and understates tea and *jhum* | E1.1 built; or the V4 blind imagery sample finds visible erosion (rills, fresh *jhum*, bare tea rows) in more than 10% of tree-class points; or the department's land use or field data arrives | **Split the tree class** with Sentinel-2 (closed canopy / open-plantation / recently cleared), each with its Wischmeier & Smith value. Do **not** feed NDVI straight into a C formula (see V-03) | `erosion_factors.py` `C_LOOKUP`, `TREE_C_ALT` |
| V-03 | NDVI → C formulas | Not used | Checked 2026-10-17: Durigon et al. 2014 is C = (1 − NDVI) / 2 (linear), so dense forest (NDVI 0.85) gets about 0.075, which barely separates forest from crops. van der Knijff gives about 0.00001. Both miss Wischmeier & Smith's 0.0001–0.003 at the forest end | A formula calibrated on Indian or North-East plots appears | Use NDVI to *classify*, not as C | R6; E1.1 |
| V-04 | All other C values | IWED Table 2: shrub 0.11, grass 0.16, cropland 0.34, bare 0.45 | Comparable with the national map | The department names its own values; or V4/V5 disagree | Department table; Sentinel-2 seasonal split for paddy versus upland crops | `C_LOOKUP` |
| V-05 | Protection P | 1 everywhere ("if untreated") | No treated-area data exists for us | The department shares its treated-area records (ASK) | P per treated polygon; the "treated vs untreated" view | `erosion_factors.py` `P` |
| V-06 | Treetop guard | **v2 (2026-10-17), residual bias logged in Step 6 part 3 (near-tree cropland median A 13.1 vs 5.2 away from trees):** on land < 20 m above its channel, tree cells **and cells next to a tree cell** capped at the p90 slope of cropland not next to trees. v1 (tree cells only, cropland p90 2.75°) left false hotspots on crop beside groves (S2) | Measured artefact: 0.6° under crops vs 2.8° under trees on the same flats | A bare-earth DEM becomes usable (FABDEM is non-commercial, so an ASK); or V4 shows real slopes being cut | Bare-earth DEM; or a canopy-height correction | `FLAT_BAND_M`, `GUARD_PCTL` |
| V-07 | River land not assessed | Under 2 m above a channel draining ≥ 100 km² (22% of Assam) | Flood deposition and bank cutting dominate there and RUSLE can't model them; 5 m is reported alongside | The department says which river land it wants scored; or riverbank watch X1 starts | Its own riverbank-erosion layer (X1) | `RIVER_LAND_M` |
| V-08 | Slope length | λ = (upslope cells + 1) × 100 m, capped at 300 m | Standard cap; 100 m cells make λ coarse (100/200/300 m) | A 25–30 m LS run becomes affordable, or field checks disagree | Compute L at 25 m with Desmet & Govers | `LAMBDA_CAP_M`, `l_factor` |
| V-09 | Steepness S from the mean slope | McCool on the cell's mean 25 m slope | S is almost linear in sin θ; Nearing moves classes ≤ 2 points | Never urgent | S per 25 m sub-cell inside `terrain.py` | `s_mccool` |
| V-10 | Topsoil for K | Mean of SoilGrids 0–5 and 15–30 cm. **ISED (2026-10-18): district pattern ρ 0.94, but ours is 0.57× theirs** (median 0.0166 vs 0.0285): different formula or depth, not units | 5–15 cm was not fetched; K hardly varies (0.0158–0.0183) and its pattern matches ISED, so ranks are safe; absolute tonnes may run low | Department soil survey (ASK); or a measured-K source for the North East | Fetch 5–15 cm; then the soil survey | `top()` in `erosion_factors.py` |
| V-11 | Classes | Indian six-class scheme, t/ha/yr | Provisional (D4) | The department names its scheme (A2 question 2) | Re-class; one constant | `CLASS_EDGES` |
| ~~V-12~~ | ~~Assam outline~~ | **RESOLVED 2026-10-20:** Survey of India OVSF/1M/9, 35 districts with LGD codes; folds re-frozen with the same hash. See the Build log, "The official Assam outline is in" | — | — | — | DATA_CONTRACT §8 |
| V-13 | Upstream area | Stops at the Assam box edge | Irrelevant for capped L | Flood work on Assam (X4), or any use of big-river flow accumulation | Stitch with Arunachal on the shared lattice | `hydrology.py` |
| V-14 | Data Backbone catalogue | ~~Will count Assam's files in Arunachal's figures~~ **Fixed in code 2026-10-19:** sources tagged by state, files counted once. The live catalogue is not rebuilt yet | — | **The next `build_backbone_bundle.py` run** | When it runs: the brief's and the deck's "29 sources / 308 GB" become about 33 / 342 GB (most of the increase is the comparison-only ISED/IWED). Update BRIEFING.md/.html and PRESENTATION in step | `build_backbone_bundle.py` |
| V-15 | IMERG archive for Assam | Not fetched | Phase 0 R comes from the R maps | The weekly outlook (E2.1) | `fetch_11b` with `REGION=assam` (about 2 h) | E0.3 |
| V-16 | Display of cell classes on tree land | **Shown since 2026-10-19:** a note under the map ("On tree-covered land a square's class is indicative…") | Follows from V-02 | V-02 upgraded | Drop the note | `webapp/products/erosion/view.py` `_map_page` |
| V-18 | Reason line among hill units | Driver = the factor most above the **state** average. All top-20 units read "steep or long slopes" | True and simple for Phase 0 | Screen build (E0.9) or the first department review | Add a second reason against *similar terrain* (hill vs hill units), surfacing cover or rain | `erosion_priority.py` `table()` |
| V-19 | Arunachal erosion results not shown in the app | Computed (the debug run) but left out of the bundle; the state picker says so | 74% of forested Arunachal reads severe or worse with tree C 0.03 (D8): misleading without the tree-class split | V-02 upgraded (Sentinel-2 tree split), or the user asks to show it | `REGION=arunachal python scripts/run/export_erosion_bundle.py` (needs `erosion_priority.py` and `check_erosion_bars.py` for Arunachal first) | `webapp/products/erosion/view.py` `_region()` |
| V-20 | Home page subtitle | Still "Arunachal Pradesh" under SLOPESENSE, with an Assam module beside it | The home page mirrors the presenter's script and the deck; changing one alone puts them out of step | The user decides how the platform names its states | Change `app.py` landing title, `core/landing.py`, the script and the deck together | `webapp/app.py` |
| V-21 | Earth Engine has no asset storage | Results fetched by `computePixels` in 8 km tiles (1,417 tiles, about 2½ h for Assam) | Works, and resumes | A state-wide refresh is needed often (seasonal cover, E1.2+), or another state | Turn on asset storage for project `earthengine-507510` in the Google Cloud console (user's action); then one batch export per run | `fetch_43_tree_split_inputs.py` |
| V-22 | V3 measured-sediment test | **Not possible on the Assam-only map** (2 qualifying stations). 12–13 CWC stations with 20–48 years drain catchments ≥ 95% inside India, from the hills around Assam | — | The user decides to extend the map | A North-East region on the backbone (about 91.7–96.9° E, 22.9–27.7° N) covering those catchments; then rank catchments by measured concentration against modelled loss. No CWC discharge for Assam, so concentration, not loads | `reports/sediment_station_catchments.csv` |
| V-17 | Priority ranking robustness | Rank under 2 R maps × 2 tree C. **S7 failed (2026-10-17):** 7 of the top 20 are shared between rain maps (ρ 0.82 over all units), 0 in all four runs. **E0.8 (2026-10-18):** the cleared hill catchments #1, #8, #13, #16 hold under tree C 0.003; the 7 rain-robust ones are forested hills. So: mark "top under both rain maps" / "depends on the rain source" and show each unit's rank under each run | Neither lever can be settled with open data now | More R anchors (V-01) or the tree-class split (V-02) | Re-run S7; the marks shrink as the levers are pinned down | E0.8; `check_erosion_bars.py` S7 |

## Build log

A plain, dated account of what has been done, newest last. The measured numbers sit in
the [Results log](#results-log); this section says what was done, where it lives, and how
it was checked.

### 2026-10-17 · Check of the plan (no code)

- Every assumption in this plan and in the design was checked against the official
  challenge pages, the literature and the data itself. Twelve findings, R1–R12 in
  [Revision of 2026-10-17](#revision-of-2026-10-17--what-the-check-found). The three that
  change the plan:
  - the deadline is 10 Nov, not 25 Oct;
  - the planned rain formula reads 91% low at Guwahati, so InRESatE replaces it;
  - the two good rain maps disagree on pattern, so the ranking is tested under both.
- The two rain maps (InRESatE, IRED) were downloaded **once, to a scratch folder**, to
  measure them. They are not yet in the raw store. E0.3 fetches them properly, with
  provenance, and the R comparison is then re-run from those copies by a script kept in
  the repo.
- Docs updated: this file (revision, revised Phase 0, decisions D6), EROSION_MODULE.md
  (R/K/LS/C rows, class wording, risks, sources), and BRIEFING.md/.html (deadline).

### 2026-10-17 · Step 1: baseline for the live flood forecast

- **Why:** the region port edits `scripts/common.py` and `scripts/build/grid.py`, which
  the live 08:30 flood run imports. Any change to the flood numbers must be visible.
- **Done:** the old recording (2026-10-11) was backed up to
  `data/interim/flood_forecast/golden_live_2026-10-11/`. Current code was checked against
  it (PASS, 0 changed), then a new recording was made for 2026-10-17 and replayed (PASS).
  Today's 10:41 issue and the track record were not touched.
- **Re-run after any change:** `.venv\Scripts\python scripts\model\check_live_unchanged.py check`

### 2026-10-17 · Step 2: region switch, Assam grid, outline, mask and folds (E0.1, E0.2, E0.5)

- **Region switch** (`scripts/common.py`). A `REGIONS` table (state name, fetch bbox,
  tile ranges) and `REGION` from the environment, default `arunachal`. Non-default regions
  write to `data/interim/<region>/` and `data/processed/<region>/`; raw folders are shared.
  An env var, not a flag, because scripts read these names at import time.
- **Provenance fix** (`record()` in `common.py`). Entries are now one per
  (source, region). Before this, an Assam re-fetch of a shared source (GADM, SoilGrids…)
  would have replaced Arunachal's entry in `_SOURCES.json`. Default-region entries keep
  their old format (no `region` key).
- **Grids** (`scripts/build/grid.py`). One box per region in `_GRIDS`. Assam is frozen at
  160,000 / 2,660,000, 6,500 × 4,500, widened from the proposed 6,400 × 4,400 (reasons in
  [DATA_CONTRACT.md §8](DATA_CONTRACT.md)).
- **Outline** (`scripts/fetch/fetch_01_boundaries.py`). It now takes the state from the
  region. Wrote `gadm_state-boundary_vector_assam.gpkg` and
  `gadm_district-boundary_vector_assam.gpkg` (27 districts, GADM stand-in).
- **Mask and folds** (`scripts/build/make_folds.py`, unchanged, run for Assam). Wrote
  `data/interim/assam/state_mask.tif` and `spatial_folds.*`, hash `a6bc908e791c9063`.
- **Checked:**
  - Arunachal's constants equal their frozen values with REGION unset and set to `arunachal`.
  - The grid round-trip self-test passes for both regions.
  - An unknown region is refused.
  - The provenance test keeps regions apart.
  - `check_live_unchanged.py check` passes with 0 changed.
  - Arunachal's own mask and folds files are untouched (dated 2026-07-31).
- **Open:** the official Assam outline (A3). When it replaces GADM, re-run
  `fetch_01_boundaries.py` (adapted) and `make_folds.py` for Assam and record the new fold
  hash, before any model.

### 2026-10-17 · Step 3: Assam raw data (E0.3)

All fetched with `REGION=assam` into the shared raw folders, each with its own
`_SOURCES.json` entry tagged `"region": "assam"`. Arunachal's entries are intact beside them.
Logs are in `logs/assam_fetch_*.log`.

| Source | Script | What arrived |
|---|---|---|
| Copernicus DEM GLO-30 | `fetch_02_terrain.py` | 40 of 40 tiles (N24–N28 × E89–E96), 22 new, 18 shared with Arunachal; all open and read |
| SoilGrids 2.0 | `fetch_03_soil.py` | 18 of 18 rasters (6 properties × 3 depths), `*_assam.tif` |
| ESA WorldCover 2021 | `fetch_04_landcover.py` | 8 tiles, 2 new (N24E087, N27E087) |
| HydroSHEDS | `fetch_05_hydrology.py` | clipped from the Asia files on disk: 68,215 river reaches, 515 level-8 and 2,534 level-12 basins |
| InRESatE + IRED R maps | **new** `fetch_42_erosivity.py` | both archives with provenance, CC-BY 4.0; national, so fetched without REGION |

- **Not fetched, on purpose:** the IMERG daily rain archive for Assam. The Phase 0 R comes
  from the R maps (R2). IMERG returns in Phase 2 for the weekly outlook.
- **The R comparison is now reproducible:** the new `scripts/inspect/compare_erosivity.py`
  reads the raw-store copies and writes `reports/erosivity_comparison_assam.json`. It gives
  the same numbers as the scratch run (Guwahati: Singh −91%, IRED −46%, InRESatE −5%;
  Spearman 0.26).
- **Two fetch fixes found on the way** (the connection was dropping name lookups on and
  off): `fetch_02_terrain.py` and `fetch_04_landcover.py` asked the server for each tile's
  size even when the tile was on disk. A timed-out answer marked two existing land-cover
  tiles "missing" and left them out of the provenance record, although the build needs them
  (one covers north-east Assam). Both scripts now trust a tile already on disk. The DEM run
  was also cut off once and was re-run; files already down are skipped.
- **Checked:** every needed DEM tile is on disk and readable; the provenance in all six
  folders lists Assam and Arunachal apart; `check_live_unchanged.py check` passes again
  (0 changed).

### 2026-10-17 · Step 4: Assam base layers (E0.4)

Built with the same scripts as Arunachal, `REGION=assam`, into `data/interim/assam/`
(about 10 minutes in all; logs in `logs/assam_build_*.log`):

| Script | Output | Result |
|---|---|---|
| `terrain.py` | 8 layers: height, slope (from 25 m), steepest sub-cell, relief, aspect, curvature | 100% cover; height 8–1,963 m (Assam's highest point is about 1,960 m, in Dima Hasao); median slope 2.5° |
| `hydrology.py` | flow accumulation, wetness index | 100% cover; largest upstream area 21,118 km² (see limit 1) |
| `build_hand_100m.py` | height above nearest channel (≥ 100 km² upstream), channel size | 85,033 channel cells; median height above channel **6 m** |
| `features.py` | 18 soil layers, land cover | 100% cover; topsoil clay 28%, sand 37%, silt 33%, organic carbon 26 g/kg, bulk density 1.24 g/cm³. Land cover: tree 53.5%, cropland 35.0%, water 6.5%, grass 3.2% |

**Pictures checked** (`data/interim/assam/terrain/_check_*.png`): the outline is right
and north is up. The hills sit where they should (the Karbi Anglong plateau, the Barail
range across Dima Hasao, the Barak valley ridges). In a 60 × 40 km close-up round Haflong,
the computed streams lie on HydroSHEDS' mapped rivers.

**Fixes made on the way, all in shared build code:**

- `features.py` picked up every SoilGrids file in the shared raw folder. Run for Assam,
  it would have loaded Arunachal's rasters as extra layers, and the reverse on any
  Arunachal rebuild. It now matches `*_250m_<region>.tif` only, and Arunachal's pattern
  still matches exactly its 18 files. It also skips lithology when a region has none (APSSDI
  is Arunachal-only; erosion does not use rock type).
- `check_terrain.py` / `check_hydro.py`: the state name in the title, and a close-up
  window per region (Arunachal's West Kameng window lies outside Assam).

**Arunachal untouched:** its own terrain, height-above-channel and soil files keep their
July–September dates.

**Findings to act on in E0.6:**

1. **Upstream area stops at the box edge.** Rivers entering from Arunachal, Bhutan and
   Nagaland count only the land inside Assam's box. This does not matter for the slope-length
   term (capped at about 300 m). It does matter if flow accumulation is ever used for big
   rivers. The fix, if needed, is to stitch with Arunachal on the shared lattice.
2. **The floodplain mask needs a written threshold.** Height above the nearest channel is
   under 2 m on 27.9% of the state, under 3 m on 34.5%, under 5 m on 46.7% and under 10 m
   on 63.3%. A careless "a few metres" would drop up to half of Assam as "not assessed".
   Set it in E0.6 with the reason, before any erosion number exists.
3. **Treetops inflate slope on flat land, measured.** On river flats (under 5 m above the
   channel) the median slope is 0.6° under cropland but **2.8° under trees** (90th
   percentile 5.7°), on the same flat ground. That is the surface-DEM trap the design
   predicted (§10), now with a number. It is a noise floor across all tree cover, not only
   at edges. It feeds S into the soil-loss estimate, damped by low C under trees, but tea
   gardens and village groves count as "tree" in WorldCover. Options for E0.6: floor the
   plains slope at the cropland reference; use a bare-earth DEM (FABDEM is non-commercial,
   so it would be an ASK); or both. The E0.4 check "most plains cells < 2°" passes only
   narrowly (58.9% of land under 20 m above the channel), and this is why.
4. **"Tree cover" is 53.5% of Assam**, against about 36% recorded forest (FSI 2021).
   WorldCover counts tea gardens, homestead groves and bamboo as trees. A class lookup for C
   would treat a tea garden like forest. Check against NESDR's land use, or split tea with
   Sentinel-2, in E0.6/E1.1.
5. **The Data Backbone catalogue will double-count** on its next rebuild:
   `build_backbone_bundle.py` counts every file in the raw folders and reads every
   `_SOURCES.json` entry, so Assam's downloads and second entries would appear in
   Arunachal's figures. Make it region-aware before the bundle is next rebuilt. The live
   app is not affected until then.

### 2026-10-17 · Step 5, part 1: the recipe, written down before any erosion number exists (E0.6)

Written before `erosion_factors.py` had run on either region. Anything changed after the
first numbers appear gets a new dated entry with its reason; this one is never edited.

| Ingredient | Main run | Run alongside (sensitivity) | Why |
|---|---|---|---|
| **R** rain | InRESatE annual R, bilinear from 0.1° to 100 m. Source NaNs (outside India) filled from the nearest valid cell **before** resampling, so border cells keep a value | IRED | R2/R3. The fill only touches cells outside India that border cells interpolate from |
| **K** soil | Williams (1995) EPIC: K = 0.1317 × f_csand × f_cl-si × f_orgc × f_hisand (SI, t·ha·h·ha⁻¹·MJ⁻¹·mm⁻¹). Topsoil = mean of SoilGrids 0–5 and 15–30 cm. Sand, silt, clay % = g/kg ÷ 10; organic carbon % = dg/kg ÷ 100 | — | The 5–15 cm layer was not fetched; the two-layer mean stands in for 0–30 cm. ISED comparison in E0.7 |
| **L** slope length | L = (λ / 22.13)^m, λ = (upslope cells + 1) × 100 m, **capped at 300 m**. m = β/(1+β), β = (sin θ / 0.0896) / (3 sin θ^0.8 + 0.56) (McCool 1989) | — | 100 m cells make λ coarse: 100, 200 or 300 m |
| **S** steepness | McCool et al. (1987): 10.8 sin θ + 0.03 where tan θ < 0.09, else 16.8 sin θ − 0.50. θ = the cell's mean slope from 25 m sub-cells (`terrain_slope_deg`) | Nearing (1997): −1.5 + 17 / (1 + e^(2.3 − 6.1 sin θ)) | R5. S is close to linear in sin θ, so S of the mean slope ≈ mean of the sub-cell S. Recorded as an approximation |
| **Treetop guard** (step 4, finding 3) | On land < 20 m above its channel, tree-cover cells take slope = min(own slope, **p90 of cropland slope in the same band**), measured at run time and logged | No guard | Measured: same flat land reads 0.6° under crops, 2.8° under trees. The p90 (not the median) leaves room for real low rises |
| **C** cover | WorldCover lookup, values from IWED's Table 2 (Raj, Saharia & Chakma) for comparability: tree 0.03, shrub 0.11, grass 0.16, cropland 0.34, bare/sparse 0.45 | — | R6. Tea gardens are "tree" in WorldCover (step 4, finding 4), so a tea garden reads like forest. This is a known under-estimate until Sentinel-2 cover (E1.1) |
| **P** protection | 1 everywhere: "if untreated" | — | IWED uses P < 1 on cropland (0.49), so our cropland reads about 2× theirs on the same R. Recorded for S8 |
| **Classes** | t/ha/yr: < 5 slight · 5–10 moderate · 10–20 high · 20–40 very high · 40–80 severe · > 80 very severe | — | Provisional until the department names its own scheme (D4) |
| **Not assessed** | Water (80), built-up (50), herbaceous wetland (90), snow/ice (70), moss (100), mangrove (95); channel cells (≥ 100 km² upstream); and **river land: under 2 m above its channel** | Same with 5 m | Step 4, finding 2. Under 2 m above a channel draining ≥ 100 km², flood deposition and bank cutting dominate, and RUSLE models neither. Above that, gentle land is scored, and RUSLE's own small slope term gives it a low number honestly. 2 m keeps the excluded share at about 28% of Assam; 5 m (47%) is reported alongside so the choice is visible |

**Outputs:** `data/interim/<region>/erosion/`: R, K, LS, C, the not-assessed mask, A and the
class for the main run, plus A for the IRED run. Summary in
`reports/erosion_factors_<region>.json`: settings, factor percentiles, class shares and
every sensitivity case. **Order:** Arunachal first (to debug), then Assam. The sanity bars
S1–S8 are the next step (E0.7) and are judged there, not here.

### 2026-10-17 · Step 5, part 2: the recipe runs on both regions (E0.6)

**New code:** `scripts/build/erosion_factors.py` (the recipe, exactly as written down in
part 1) and `scripts/build/check_erosion.py` (the picture). Arunachal ran first as the
debug run, then Assam. Each takes about 30 s. Logs in `logs/<region>_erosion_factors.log`,
summaries in `reports/erosion_factors_<region>.json`, rasters in
`data/interim/<region>/erosion/`.

**Assam, main run** (InRESatE R, tree C 0.03, P = 1, river land < 2 m not assessed):

- **Scored: 69.6% of the state.** Not assessed: water, built-up, wetland 7.4%; channel
  cells 0.8%; river land under 2 m 22.0%. If river land were "under 5 m", 52.2% would be
  scored.
- **The resampling is right at the gauge:** R on the grid at Guwahati is 7,900 (gauge
  7,924; InRESatE's own cell 7,507).
- **Factors on scored land (median):** R 5,273; K 0.0166; LS 1.30 (p95 34); C 0.03.
- **Soil loss:** median 8.2 t/ha/yr, mean 26.0 (IRED: 11.0 and 30.0).
- **The treetop guard** capped tree-cell slope at 2.75° (cropland p90 under 20 m) on
  17.4% of the state.
- **Picture** (`_check_erosion.png`): the hills are worst (Karbi Anglong, the Barail
  range across Dima Hasao, the Meghalaya and Bhutan edges); the plains are mostly slight to
  moderate; "not assessed" follows the rivers. R peaks below the Arunachal foothills
  (north Lakhimpur, Dhemaji).

**Class shares, % of scored land** (slight / moderate / high / very high / severe /
very severe):

| Run | Assam | Arunachal (debug) |
|---|---|---|
| **Main** | 37.6 / 15.3 / 11.1 / 14.5 / 13.6 / 7.8 | 3.8 / 1.6 / 5.0 / 15.2 / 28.9 / 45.5 |
| IRED rain | 28.5 / 19.2 / 15.1 / 14.2 / 13.3 / 9.8 | 4.2 / 3.7 / 12.1 / 25.4 / 23.2 / 31.3 |
| No treetop guard | 26.5 / 18.8 / 15.9 / 16.7 / 14.3 / 7.9 | 2.3 / 2.3 / 5.3 / 15.4 / 29.1 / 45.6 |
| Nearing steepness | 39.1 / 14.6 / 11.2 / 13.1 / 12.6 / 9.4 | 3.9 / 1.6 / 3.6 / 12.0 / 24.2 / 54.7 |
| **Tree C 0.003** | **67.4 / 13.8 / 7.8 / 4.8 / 3.5 / 2.7** | **32.0 / 31.9 / 25.8 / 3.0 / 0.6 / 6.7** |
| River land < 5 m | 35.0 / 13.9 / 10.8 / 15.9 / 15.5 / 8.9 | 3.1 / 1.5 / 4.9 / 15.3 / 29.2 / 46.0 |

**What the debug run found: the tree cover value is the biggest open lever.** With
IWED's tree C of 0.03, forested Arunachal reads **74% severe or very severe** (mean 101
t/ha/yr). Wischmeier & Smith put closed forest at 0.001–0.004, 10–30× lower; at 0.003 the
mean is 36 t/ha/yr. Neither matches the published district values. Papum Pare: Dabral et
al. 2008 about 51 t/ha/yr, IWED 32; ours 97 (C 0.03) or 11 (C 0.003). So there is no
"right" single value to fit to, and none was fitted. The reasons:

- WorldCover's "tree" mixes closed forest, tea gardens (step 4, finding 4) and regrowing
  *jhum* fallow, whose true C spans 0.001 to about 0.2.
- No single number can be right for that mix.

So **C = 0.003 was added as a sensitivity run, not swapped into the main run** after
seeing numbers (the rule in part 1), and the choice goes to the user as **decision D8**.
It moves Assam's slight share from 38% to 67%. It also changes the *order* of forested
hills versus farmed land, so the priority list (E0.8) is computed under both, like R. The
lasting fix is a measured cover per cell: Sentinel-2 NDVI cover (E1.1), which separates
closed forest, tea and fresh *jhum*. That makes E1.1 worth pulling into Phase 0 if time
allows.

**Other readings:**

- The treetop guard matters: without it, 11 points of Assam's land move up from slight.
  It was set before any number, so it stays.
- Nearing's steepness moves the very-severe share by only about 2 points in Assam. The
  choice of S is not a big lever here.
- K varies little (p5–p95 0.0158–0.0183). Soil is not what separates places in Assam;
  slope, cover and rain are.

### 2026-10-17 · Decision D8: the cover value for "tree"

**Options weighed:**

1. Keep 0.03 (IWED).
2. Switch to 0.003 (Wischmeier & Smith closed forest).
3. An in-between value.
4. Feed Sentinel-2 NDVI straight into a C formula.
5. Split the tree class with Sentinel-2 and give each part its own value.

**Chosen: 1 for now, 5 as the upgrade.** The reasons:

- **A lumped class needs its area-weighted mean C.** Soil loss is linear in C, so for
  WorldCover's "tree" (closed forest about 0.003, tea gardens about 0.18, young *jhum*
  fallow about 0.1) a mix of 75 / 15 / 10% averages about 0.04. So 0.03 is a fair *class*
  value. It was also written down before any number, and it matches the national map.
- **Option 2 is right only for pure forest.** It would hide the tea and *jhum* land the
  department most needs to see.
- **Option 3 is tuning to a number.**
- **Option 4 replaces one uncertain number with another.** Checked against the
  literature: Durigon gives about 0.075 for dense forest and van der Knijff about 0.00001.
  Both miss the reference range (V-03).
- **Option 5 measures the thing that is actually uncertain:** which tree-class cells are
  forest, which are tea, which are cleared.

**Consequences, until V-02 is upgraded:**

- the priority list is ranked by catchment (where a class average is valid) under both tree
  C values and both R maps (V-17);
- cell classes on tree land carry an "indicative" note (V-16);
- the proposal says plainly that the tree class is the main uncertainty and how Phase 1
  removes it.

### 2026-10-17 · Step 6, part 1: how each sanity check is measured, written before running (E0.7)

The pass bars (S1–S8) were set on 2026-09-29 and revised in R7. This entry fixes how
each one is *measured*, written before the check script first ran. Checks are on Assam,
main run, unless a row says otherwise.

| # | Measured as | Pass bar |
|---|---|---|
| **S1** hills vs plains | Hill districts = GADM's "Karbi Anglong" and "Dima Hasao" (West Karbi Anglong sits inside GADM's Karbi Anglong); plains = the other 25. Median A over *scored* cells of each group | Hills ≥ 3× plains. The IRED and tree-C 0.003 runs are reported, not judged |
| **S2** treetop hotspots | Flat = under 10 m above its channel. Among scored flat cells, take the top 5% by LS. An *edge cell* has both tree (10) and some other land cover in its 3 × 3 neighbourhood | ≤ 25% of those top cells are edge cells. Also reported: the same without the treetop guard, and the share of edge cells among *all* scored flat cells, so 25% can be read against the base rate |
| **S3** factor ranges | K over all in-state cells; C over scored cells; R on the grid at Guwahati. ISED: district medians of our K vs ISED's K (Spearman, median ratio) | K in 0–0.08; C in 0–1; R within ±25% of 7,924. ISED is logged, no bar |
| **S4** class spread | Class shares of scored land, every run in `erosion_factors_assam.json` | No class > 80% in the **main** run. The others are reported |
| **S5** not-assessed never "low" | Cells that are water / built / wetland / snow / moss / mangrove, channel cells, or under 2 m above a channel, with a class other than 0 | Zero such cells |
| **S6** live flood forecast unchanged | `check_live_unchanged.py check` | PASS, 0 changed |
| **S7** rain-map robustness | Units = HydroBASINS level-12 basins, rasterised to the grid (cell centre inside); a unit counts if it has ≥ 500 scored cells (5 km²). Score = mean A over its scored cells. Top 20 under InRESatE vs top 20 under IRED | ≥ 10 shared. Also reported, not judged: overlap under tree C 0.003, and the units that are top 20 in **all four** runs (2 R × 2 tree C, register V-17) |
| **S8** national map (IWED) | District mean A (27 GADM districts): ours (main), ours on IRED, and IWED's 250 m raster (cell centre inside the district). Spearman of each against IWED | No bar. Expectation, written now: our IRED run agrees with IWED better than our main run does. If not, something besides rain differs and must be explained |

### 2026-10-17 · Step 6, part 2: first run of the checks, and the guard fix it forced (E0.7)

**First run (`scripts/inspect/check_erosion_bars.py`, Assam, main run, guard v1):**

| # | Result | Bar |
|---|---|---|
| S1 | Hills median 27.4 vs plains 5.3 t/ha/yr = **5.1×** (IRED 3.4×; tree C 0.003 2.3×) | PASS |
| S2 | **91.8%** of the top-5% LS cells on flat land are edge cells. Without the guard: 68.8%. Base rate among all flat scored cells: 65.2%. Tree cells among the top 5%: 0% (88.8% without the guard) | **FAIL** |
| S3 | K 0.0149–0.0572; C 0.03–0.45; R at Guwahati 7,900 (−0.3%). ISED pending | PASS |
| S4 | Largest class share in the main run 37.6% | PASS |
| S5 | 2,363,804 not-assessed cells, 0 with a class | PASS |
| S6 | (run after the fix) | — |
| S7 | Top-20 shared between rain maps: **7**. Between tree C values: 3. Top 20 in all four runs: **0**. Rank correlation over 702 units vs the main run: IRED 0.68, tree C 0.54, both 0.08 | **FAIL** |
| S8 | IWED download running | pending |

**What S2 found: the treetop guard was incomplete.** The guard capped *tree* cells.
But the canopy also lifts the slope of the *non-tree cells beside it* (crop next to a grove
sees the canopy step as a slope). Measured on cropland under 20 m above its channel, where
60% of cells sit next to trees:

| Cropland under 20 m | Median slope | p90 slope | Median A | Share ≥ 40 t/ha/yr |
|---|---|---|---|---|
| Next to a tree cell | 1.60° | 3.87° | 22.3 | **30.5%** |
| Not next to trees | 0.43° | 1.52° | 5.2 | 4.5% |

These are false plains hotspots, and S2 caught them as designed.

**Fix (guard v2), written before re-running:** in the same band (under 20 m above its
channel), cap the slope of **tree cells and every cell with a tree cell in its 3 × 3
neighbourhood**. The reference is the p90 slope of cropland in the band **not next to
trees**, measured at run time (1.52° on this run, against 2.75° for guard v1, whose
reference was itself lifted by the spillover). Real low rises lose a little slope. The
"no guard" run stays as the sensitivity case, and the register row V-06 is updated.

**Correction to the S2 bar itself.** The bar "≤ 25% edge cells among the top 5%" was set
on 2026-09-29 without knowing the base rate. In Assam's mixed groves-and-paddy plains,
65.2% of *all* flat scored cells are edge cells by this definition. So even a map with no
artefact at all would fail the 25% bar. A fair version is added: **the top 5% may be no
more edge-heavy than flat land in general** (edge share in the top 5% ≤ the base rate).
Both are reported from now on; the original result above stays on record.

**S7 is handled after the fix.** The top 20 are mostly hill units (south Kamrup along the
Meghalaya border, Dima Hasao, Cachar, Karbi Anglong), not plains artefacts, so the guard
fix should not change it much. If it still fails, the pre-registered consequence applies:
every unit not top-ranked under both rain maps carries a "depends on the rain source" mark.

### 2026-10-17 · Step 6, part 3: the checks after guard v2 (E0.7)

**Recipe re-run with guard v2** (`logs/assam_erosion_factors.log`). The reference slope
(cropland not next to trees, p90) is **1.22°**, and **36.4% of the state** is capped
(v1: 17.4%). Scored share unchanged at 69.6%. Mean A 21.6 t/ha/yr (was 26.0; IRED 24.4;
tree C 0.003 7.0). Classes, slight → very severe: **44.8 / 10.3 / 13.8 / 14.2 / 11.0 /
6.0%** (v1: 37.6 / 15.3 / 11.1 / 14.5 / 13.6 / 7.8).

| # | Result after guard v2 | Verdict |
|---|---|---|
| S1 | Hills 26.9 vs plains 3.3 t/ha/yr = **8.3×** (IRED 5.3×; tree C 0.003 2.4×) | PASS |
| S2 | Top-5% LS on flats: edge share **69.1%** vs base rate 65.2% (ratio 1.06). Tree cells in the top 5%: 50% (88.8% unguarded). The top-5% LS threshold fell from 1.80 to 0.51 | **FAIL, narrowly, on the fair bar**; FAIL on the original 25% bar |
| S3 | Unchanged: K 0.0149–0.0572, C 0.03–0.45, R at Guwahati −0.3%. ISED pending | PASS |
| S4 | Largest class 44.8% | PASS |
| S5 | 0 of 2,363,804 not-assessed cells given a class | PASS |
| S6 | `check_live_unchanged.py check`: 0 changed | PASS |
| S7 | Top-20 shared between rain maps: **7** (12 within IRED's top 40, 16 within its top 70). Tree C: 4 shared. All four runs: **0**. Rank correlation over 702 units: IRED **0.82** (was 0.68), tree C 0.59, both 0.21 | **FAIL** |
| S8 | IWED download running | pending |

**Reading S2.** The false hotspots are gone: cropland next to trees is now **less** often
≥ 40 t/ha/yr than cropland away from them (1.7% vs 4.5%; it was 30.5% vs 4.5%). The
residual 4-point edge excess is driven by slope *length*: 93.2% of the top-5% flat cells
have the full 300 m slope length, against 46.4% of all flat cells. That is flow
convergence, not canopy. **Not tuned further**: the bar stays failed on record, with this
diagnosis.

**A residual bias the guard leaves, logged (V-06):** capping at the p90 leaves next-to-tree
cells at the *upper* end of honest flat slopes, so near-tree cropland still reads a median
A of 13.1 against 5.2 away from trees (LS median 0.46 vs 0.15). That is a moderate-versus-
slight difference across the plains. It does not reach the severe classes, and the
priority ranking is led by hill units. The fix is a bare-earth DEM (ASK), not a lower cap,
which would flatten real rises.

**S7 — the pre-registered consequence applies.** The rain maps agree on the broad order
(ρ 0.82) but not on the exact top 20. The tree-C lever reorders more (ρ 0.59), and the two
together leave nothing that is top 20 in all four runs. For E0.8 that means:

- the priority list marks each unit **"top under both rain maps"** or **"depends on the rain
  source"** (pre-registered in R7);
- with only 7 units in the first group, the list also gives each unit's rank under each run,
  so a reader sees how far it moves;
- the tree-C lever is shown the same way (register V-02, V-17);
- a tighter "robust" set is not claimed. The honest message is that Phase 0 ranks *areas*
  (the hill districts, the south Kamrup–Meghalaya edge, the Barail range) more firmly than
  single catchments.

### 2026-10-18 · Step 6, part 4: the national-map comparisons, S3 (ISED) and S8 (IWED)

**Downloads** (`scripts/fetch/fetch_44_erosion_reference.py`, log
`logs/fetch_44_erosion_reference.log`):

- ISED, 1.97 GB, into `data/raw/03_soil_geology/ised/`. Zenodo record 6505314 now
  resolves to version 8011445.
- IWED, 2.35 GB, into `data/raw/06_weather/erosivity/iwed/`. Record 7823909 resolves to
  version 10846594. No licence is stated, so compare only.
- **The line failed twice on the way.** First a 30-minute silent stall at 245 MB, then a
  35-minute outage at 1,537 MB. `common.download()` cannot resume, so the script got its
  own resumable downloader: it keeps the `.part` file, asks Zenodo for the rest with an
  HTTP Range header (Zenodo answers 206), gives up on a silent connection after 60 s, and
  retries up to 150 times. Both files finished at 02:08.

**S3, ISED (no bar).** Over 27 districts, the K pattern agrees at **ρ 0.94**, but our K is
**0.57×** theirs (state median 0.0166 vs 0.0285). That is not a unit slip, which would be
7.6×; the cause is a different formula or soil depth. It does not change ranks, since K
varies little and its pattern matches. It does scale our absolute tonnes down against
IWED's. Logged on register V-10.

**S8, IWED (no bar).** District mean A: ours (main) vs IWED **ρ −0.46**; ours on IRED vs
IWED **ρ 0.07**. The expectation written in part 1 ("the IRED run agrees better") is met.
But both are poor, so per the same entry *something besides rain differs*. Found it,
factor by factor (district means on our scored cells):

| Factor | ρ ours vs IWED | State median, ours / IWED |
|---|---|---|
| R | +0.26 | 5,269 / 6,205 |
| K | +0.91 | 0.0166 / 0.0285 |
| **LS** | +0.75 | **0.51 / 3.39** |
| C | +0.90 | 0.030 / 0.132 |
| P | — | 1 / 0.73 |
| **A** | **−0.46** | 7.6 / 44.0 |

**The cause is IWED's slope factor: it barely responds to slope.** By true slope (our 25 m
mean, on our scored cells), median LS:

| Slope | Share of scored land | LS ours | LS IWED |
|---|---|---|---|
| 0–0.5° | 8.3% | 0.11 | **2.67** |
| 0.5–1° | 7.4% | 0.26 | 2.89 |
| 1–2° | 11.8% | 0.47 | 3.00 |
| 2–5° | 29.9% | 0.46 | 3.07 |
| 5–15° | 26.0% | 7.07 | 3.90 |
| 15–30° | 14.8% | 26.6 | 5.16 |
| > 30° | 1.6% | 53.7 | **5.57** |

Cropland under 1°: IWED LS p10/p50/p90 = 0.65 / 2.75 / 4.64. RUSLE's S at 0.25° is about
0.08, so an LS of 2–3 on dead-flat paddy cannot come from the standard equations. The likely
causes are an uncapped flow length on flats and a coarse DEM flattening the hills; their
paper does not let us tell which. The consequences:

- IWED's LS is nearly uniform (3–9) across Assam, so its *ranking* is set mostly by R × C,
  and IRED's R is highest in western Assam. That is how Chirang, Baksa, Kokrajhar,
  Bongaigaon, Dhubri and Barpeta become "India's most erodible districts" (R4). Those are
  largely plains.
- Ours spans 0.1–54 with slope, so the hills lead: Dima Hasao, Kamrup Metropolitan's hills,
  Cachar, Hailakandi, south Kamrup, Karbi Anglong.
- **The disagreement is explained, and it is a point in our favour, not a red flag.** For
  the proposal's prior-art section (USPR §11), say it factually and without dismissing the
  work: "the national 250 m map's slope factor varies only 2.7–5.6 between flat and steep
  ground; ours follows slope, so our priority list starts in the hills."

**E0.7 closed.** Every bar is evaluated and logged, and every failure is explained:

- S2 failed narrowly on the fair bar; the cause is slope length, not canopy (part 3).
- S7 failed; its pre-registered consequence applies (part 3).
- S8 is explained here.

Nothing is shown outside the team before E0.8 adds the robustness marks.

### 2026-10-18 · Step 7, part 1: how the priority list is built, written before computing it (E0.8)

Written before `erosion_priority.py` first ran. Assam, recipe as in Step 6 part 3
(guard v2).

| Piece | Rule | Why |
|---|---|---|
| **Units** | (a) HydroBASINS level-12 catchments, cell centre inside, kept if ≥ 500 scored cells (5 km²), the same set as S7; (b) the 27 GADM districts | Catchments are the stand-in for the micro-watersheds conservation works are planned in (design §5.5) until official ones are obtained (E0.11/E1.8). Districts are what officers think in |
| **Score (rank by)** | Mean A over the unit's scored cells, main run | One number a department can check. The design's adjustable weights (§5.5) come with the screen in Phase 2 |
| **Shown beside it** | Scored km²; share of scored land at ≥ 10 t/ha/yr ("high" or worse); total soil loss (mean A × scored area, t/yr); share of the unit *not* scored | Size and extent change what a treatment programme should do; a small unit with a high mean is a different job from a large one |
| **Main driver** | log A = log R + log K + log LS + log C (P = 1). For each unit, take the mean of each log-factor over its scored cells, minus the same mean over all scored cells in Assam. The driver is the factor with the **largest positive** difference, named *heavy rain* (R), *erodible soil* (K), *steep or long slopes* (LS), *bare or thin cover* (C). The runner-up is named too if it is within 0.5 log units of the first | The reason line turns a map into a work order (design §5.5). Comparing to the state average says what makes *this* place worse than usual |
| **Robustness marks** | The unit's rank under all four runs (InRESatE / IRED × tree C 0.03 / 0.003). **"Top under both rain maps"** = top 20 under InRESatE *and* IRED (tree C 0.03); otherwise **"depends on the rain source"**. The tree-C ranks are shown as columns, not as a mark | Pre-registered consequence of S7 (Step 6 part 3; V-17) |
| **Eye check of the top 20** | For each top-20 catchment, a satellite image (Esri World Imagery, the app's own satellite base map) of the catchment's bounding box, read by eye: **steep relief visible? bare ground, cleared or *jhum* plots, or thin cover visible?** A unit passes if either is visible | The design's E0.8 rule. Any unit that shows neither is explained before the list is shown (a likely artefact) |
| **Outputs** | `reports/erosion_priority_assam.csv` (catchments) and `…_districts.csv`; `data/processed/assam/erosion_priority.gpkg` (catchment polygons with every column, for the department's GIS); top-20 images in `data/interim/assam/erosion/eyecheck/` | GIS outputs are a required capability in the challenge statement |

### 2026-10-18 · Step 7, part 2: the first priority list (E0.8)

**New code:** `scripts/model/erosion_priority.py` (`--images` also fetches the eye-check
pictures). Log `logs/assam_erosion_priority.log`. Outputs:

- `reports/erosion_priority_assam.csv`: 702 catchments, ranked, every column;
- `reports/erosion_priority_assam_districts.csv`: 27 districts;
- `reports/erosion_priority_assam_eyecheck.csv`: the top-20 verdicts;
- `data/processed/assam/erosion_priority.gpkg`, layer `catchments`: polygons with every
  column, ready for a GIS;
- `data/interim/assam/erosion/eyecheck/`: 20 images and 2 contact sheets.

**Top 20 catchments** (mean A, main run): 80–161 t/ha/yr. Kamrup 8 (the south Kamrup
hills along Meghalaya), Cachar 6, Dima Hasao 3, Karbi Anglong 2, Dhemaji 1, Karimganj 1.
All are hill or hill-edge units. **7 are "top under both rain maps"** (ranks 5, 6, 10,
11, 14, 15, 20: the Cachar / Dima Hasao forested hills plus the Dhemaji foothill gorge).
The other 13 "depend on the rain source"; their IRED ranks run 12–200.

**Eye check: 20 of 20 pass** (`erosion_priority_assam_eyecheck.csv`). Steep relief shows
in all 20. Cleared, bare or patchy slopes show in 10 (ranks 1, 4, 7, 8, 9, 11, 13, 16, 17,
19; rank 19 in Karimganj is heavily patched). Units to read with care:

- **#5 Dhemaji** is a forested foothill gorge where a river leaves Arunachal. It is steep
  and genuine, and the riverbed itself is not scored.
- **#14 and #15 Cachar** are half Barail hills, half flat paddy. The hills carry the score.

**Districts** (mean A / high-or-worse share / total soil loss):

1. Kamrup 49.8 / 52% / 10.2 Mt/yr
2. Dima Hasao 48.9 / 87% / 23.0
3. Kamrup Metropolitan 47.9 / 74% / 2.6
4. Cachar 43.0 / 64% / 13.5
5. Hailakandi 42.3 / 65% / 4.8
6. Karbi Anglong 30.1 / 75% / **29.6** (largest total, by size)

Bottom: Udalguri 4.0, Sonitpur 5.1, Darrang 5.5. District rank correlation with the main
run: IRED 0.74 (top 6 shared: 4); tree C 0.003 0.75 (2 shared); both together **0.00**
(0 shared).

**What the list says, read honestly:**

1. **The two levers split the list into two kinds of place.** Catchments **#1, #8, #13,
   #16** stay in the top 20 under tree C 0.003 too (ranks 1, 11, 3, 5), because their loss
   comes from *cleared* hill ground, not from the forest value. They do depend on the rain
   map. The 7 "top under both rain maps" are mostly *forested* hills, which drop under tree
   C 0.003 (ranks 132–168). So when the tree class is split (V-02), the cleared hill
   catchments are the ones most likely to stay on top. That is the strongest Phase 0
   candidate list.
2. **The district picture is firmer than the catchment picture** under one lever at a time
   (ρ about 0.75), but not when both move. The hill districts lead under the main and IRED
   runs. With tree C 0.003, plains districts with much bare cropland rise (Lakhimpur #2,
   Dhubri #4, Barpeta #5).
3. **The reason line does not separate hill units.** Against the *state* average, every
   top-20 catchment's main driver is "steep or long slopes". That is true, but it is not
   what tells one hill catchment from the next. New register row **V-18**: for the screen,
   add a second reason measured against *similar terrain* (hill units against hill units),
   which would surface cover and rain differences.
4. **Totals favour big districts** (Karbi Anglong 29.6 Mt/yr at a mean of 30). The screen
   shows mean, share and total side by side, so a reader can choose (design §5.5's
   adjustable weights, Phase 2).

### 2026-10-19 · Step 8: SoilSense in the app (E0.9), and the catalogue fix (V-14)

**8a — Data Backbone catalogue made region-aware** (`scripts/build/build_backbone_bundle.py`,
`webapp/products/backbone/view.py`):

- A source fetched for both states is now **one row tagged with the states it serves**,
  not "2 series". The files are counted once.
- The catalogue table gains a "States" column, shown only once any source serves more than
  Arunachal.
- A dry run (not written to the app) gives **11,072 files, 342 GB, 33 sources**, against the
  shipped 10,853 / 308 / 29. The increase is Assam's downloads plus the four rain and
  reference maps. Most of the extra ~33 GB is the two unzipped national comparison maps
  (ISED, IWED).
- **The live app's catalogue was not rebuilt.** When it next is, update the brief's and the
  deck's "29 sources / 308 GB". Register V-14 now covers that.
- A bug of mine was caught in the same dry run, before anything was written: a reused
  variable name set every group's file count to 1.

**8b — the module** (`webapp/products/erosion/`: `__init__.py`, `data.py`, `view.py`), one
registry entry (`webapp/products/__init__.py`, status "building"), and
`scripts/run/export_erosion_bundle.py`. The bundle is in `webapp/assets/erosion/assam/`
(2.1 MB; the app is 7.1 MB in all):

- class rasters for three runs, reprojected to web-map coordinates at about 300 m;
- 702 simplified catchments;
- districts, the outline, and `meta.json`.

**Shared-code changes, each small:**

- `Product.available` now also opens "building" modules. Only SoilSense is one, and its
  tile keeps the "🔧 Building" pill.
- `Product.region` was added, so the side menu says "ASSAM · SOIL EROSION". Every other
  module defaults to Arunachal Pradesh.
- `ER_TIERS` (Estimate / Class / Rank) was added to `products/flood/ui.py` beside the flood
  and slope badges.

**Pages:**

- **Erosion map.** Six headline tiles; a three-way run switch (main / other rain map / lower
  forest value) with one line on what each run assumes; the class map over the satellite
  base with the top 20 outlined (hover: rank, district, loss, cause, mark); a district
  picker that zooms and shows the district's figures and its ranks under every run; the
  top-10 list marked *firm* or *rain-dependent*; and the "indicative on tree land" note
  (V-16).
- **Priority list.** All 702 catchments (filter by district) and the 27 districts, each
  with its rank under the other runs. Downloads: catchments CSV, districts CSV, and
  catchments as GeoJSON for a GIS.
- **How to read this.** The recipe in plain words, kinds of number, what is not scored, the
  two unsettled inputs, the checks passed (with numbers), limits, and what lifts them.
- A **state picker** lists the states with a bundle (Assam). It says Arunachal was
  computed as the test run and is not shown yet (V-19).

**Checked:**

- Headless screen suite: **42 of 42 screens** open with no exception. That is the home
  page, the 34 existing screens and 7 new SoilSense cases (each page, a district, each
  alternative run, the list filtered). Log: `logs/check_app_screens_2026-10-19.log`.
- Desktop at 1440 px, looked at: home, map, map with Dima Hasao, list, method page. Two
  faults fixed: the district card's cause line ran past the panel edge, and district
  totals showed decimals. The tile tagline was shortened.
- Phone and tablet (`check_app_mobile.py`, 4 screens × 3 pages): the first run had 5 issues.
  - The key note ran 11 px past the edge on a 360 px phone. Shortened.
  - The list page was flagged "looks empty" on all four screens. That is a checker false
    alarm: tables draw on a canvas, so their text is not counted. The checker now counts a
    table as content.
  - Re-run: **12 of 12 OK**.
- `check_live_unchanged.py check`: PASS, 0 changed.

**Not done, on purpose:**

- **Not deployed.** The public `v2` app is untouched; pushing it is the user's call.
- The home page still reads "Arunachal Pradesh" under the platform name (V-20).
- No Assamese text yet (Phase 2).

### 2026-10-20 · Phase 1, E1.1 part 1: splitting the "tree" class — options, findings, and the method written before measuring

**Options looked at** (all on Earth Engine, which we already use):

| Source | What it gives | Verdict |
|---|---|---|
| JRC Tropical Moist Forest v1_2025 (`projects/JRC/TMF/v1_2025/…`) | Undisturbed / degraded / regrowth / cleared, every year 1990–2025 | **Not usable for Assam.** Measured at 30 m, 72.5% of WorldCover "tree" in Assam is its *other land cover*: it maps only evergreen moist forest, so deciduous forest, bamboo and *jhum* mosaics fall outside it |
| Hansen Global Forest Change v1.13 (to 2025) | Year of tree-cover loss, 30 m | **Use it for "recently cleared".** About 22–25 kha a year cleared in Assam in the 2020s, about 0.5% of tree cover a year, in line with published figures |
| Meta 1 m canopy height (`projects/meta-forest-monitoring-okw37/assets/CanopyHeight`, band `cover_code` = height in m) | Height of whatever is on the ground | **Use it for "forest vs tea / bush".** Tea bushes are about 1 m, bush and young bamboo a few metres, forest 10 m and more |
| ETH 10 m (2020), Potapov 30 m (2019) canopy height | The same, coarser | Cross-check only |
| Sentinel-2 NDVI → C | — | Not used for C (V-03) |

**Two measuring slips of mine, caught before use (not data faults):**

- A 300 m sample garbled categorical codes, because Earth Engine averages them when it
  zooms out.
- Hansen's `lossyear` is *masked* where there was no loss, so a plain mean gave "30%
  cleared in five years". It was the share of clearings that fell in 2021–25.

Both were re-measured at 30 m with the mask filled with 0.

**Reference outlines** (independent of every raster above):
`scripts/fetch/fetch_45_osm_landuse_reference.py` gives **739 OpenStreetMap tea-garden
outlines and 112 reserve forests and protected areas** (ODbL). An honesty note: 4 hand-picked
points were looked at before this entry (tea about 0.4–0.9 m on Meta, forest about 8 m).
That is what suggested canopy height. Nothing below was fitted to them.

**The method, fixed before any reference cell is measured:**

Inputs per 100 m cell on the Assam grid, from Earth Engine at native resolution:

| Input | Meaning |
|---|---|
| `low_frac` | Share of Meta 1 m pixels under 3 m |
| `h_mean` | Mean Meta height |
| `fresh_frac` | Share of 30 m Hansen pixels lost in 2024–2025 |
| `recent_frac` | Share lost in 2021–2023 |
| `h_eth` | ETH 10 m mean height, cross-check |

Sub-classes of WorldCover "tree" cells, in this order (first match wins):

| # | Sub-class | Rule | C | Source of C |
|---|---|---|---|---|
| T1 | Freshly cleared (*jhum* field, felling) | `fresh_frac` ≥ 0.25 | 0.34 | IWED "shifting cultivation" |
| T2 | Recently cleared, regrowing | `recent_frac` ≥ 0.25 | 0.10 | Mid of Wischmeier & Smith brush/regrowth (about 0.04–0.2) |
| T3 | Low canopy (tea, bush, young bamboo) | `low_frac` ≥ **T_low** | 0.18 | IWED "plantation/orchard" |
| T4 | Tall canopy (forest) | otherwise | 0.003 | Wischmeier & Smith closed forest (as the D8 alternative) |

**Setting T_low.** OSM reference cells are WorldCover "tree" cells inside a tea outline
(tea) or a forest outline (forest). They are split 50/50 *by outline* (seed 42), so cells of
one garden never sit on both sides. On the **calibration half**, T_low is the threshold on
`low_frac` that maximises balanced accuracy (tea vs forest). The **test half** is never
looked at before T_low is fixed.

**Pass bars (written now):**

| # | Check | Pass bar |
|---|---|---|
| P1 | Tea vs forest on the **test half**, balanced accuracy of the T3/T4 rule | ≥ 0.80 |
| P2 | Blind eye check on Esri imagery: 25 random tree cells per sub-class (100 in all), shown **without** their sub-class, labelled by eye as *cleared/bare patches*, *tea or bush rows*, *closed canopy* or *can't tell* | T1: ≥ 60% "cleared/bare"; T3: ≥ 60% "tea/bush"; T4: ≥ 70% "closed canopy" (T2 reported, no bar: regrowth is hard to see) |
| P3 | Area-weighted mean C of the split over all "tree" cells | Reported against 0.03 (the D8 class average). No bar: it shows whether 0.03 was in the right range |

**If P1 or P2 fails:** the split is not adopted and the main run stays at 0.03 (D8). The
failure and its reason are logged.

**Three clarifications, added 2026-10-20 while the Earth Engine export ran, before any
reference cell was measured:**

1. **No canopy-height data.** A "tree" cell without Meta height data (`low_frac` = 255) and
   not claimed by T1/T2 keeps the D8 class average, C = 0.03. Its share is reported.
2. **What P1 is computed on.** P1 uses the reference cells that T1/T2 do *not* claim, because
   the T3/T4 rule only ever sees those. The share of tea and forest reference cells that
   T1/T2 claim is reported beside it.
3. **Reference cells.** A cell is a reference cell if it is scored by the recipe's state
   mask, is WorldCover "tree", and its centre lies inside exactly one kind of outline. Cells
   inside both a tea and a forest outline are dropped. The 50/50 split is drawn over
   outlines, not cells: OSM ids are shuffled with seed 42 and alternated per kind.
4. **P2's denominator** (added before any picture was labelled): every picture of a
   sub-class counts, so a "can't tell" counts *against* the bar. That is the strict reading.
   The share among readable pictures is reported beside it.

**If they pass:**

- the split becomes the **main run**;
- 0.03 and 0.003 stay as sensitivity runs;
- S1–S8, the priority list and the app are re-run;
- register rows V-02, V-16 and V-17 are updated.

### 2026-10-20 · Phase 1, E1.1 part 2: fetching the inputs

**New code:**

- `scripts/fetch/fetch_45_osm_landuse_reference.py`: OSM tea and forest outlines (above).
- `scripts/fetch/fetch_43_tree_split_inputs.py`: the five inputs per 100 m cell.
- `scripts/build/tree_split.py`: calibrate, test, map, blind sample. Written before the
  inputs existed.

**Earth Engine could not store a result.** A batch export to an asset failed with
"projects/earthengine-507510/assets does not exist or doesn't allow this operation". Listing
or creating a folder fails the same way, so our project has no asset storage. The inputs
are therefore requested directly with `computePixels`:

- Interactive requests refuse to average more than about 8,000 × 8,000 input pixels
  ("Reprojection output too large"). With 1 m canopy heights that caps a tile at 80 × 80
  cells (8 km).
- **1,417 tiles**, about 36 s each, 8 in parallel, about 2½ hours.
- Each tile is saved as it lands (`data/raw/04_landcover/ee_tree_split/tiles_assam/`), so a
  dropped line resumes.
- Register row **V-21**. Log: `logs/assam_fetch_43_tree_split.log`.

### 2026-10-20 · Phase 1, E1.1 part 3: the hookup, built while the inputs download

Everything needed to adopt the split was built before any split result existed, so that
adopting it is one short run.

**What changes once the split is adopted:**

- **The recipe** (`erosion_factors.py`). A new `tree_split()` returns the sub-class raster
  and C values **only if** `reports/tree_split_<region>.json` says `"adopted": true`. Then:
  - the main run uses the split;
  - the D8 class average (0.03 for all tree land) becomes a comparison run,
    `erosion_A_treeC_avg_tpha.tif`, labelled "tree class average 0.03 (D8)";
  - tree C 0.003 stays.
- **Adoption** (`tree_split.py --score labels.csv`). It joins the by-eye labels with the
  key, applies the P2 bars (strict denominator, clarification 4), and writes
  `"adopted" = P1 and P2`.
- **Downstream.**
  - `erosion_priority.py` adds the comparison run's ranks (`rank_treeC_avg`).
  - `check_erosion_bars.py` S7 adds "top 20 shared, split vs one tree value" (no bar).
  - `export_erosion_bundle.py` ships the comparison run and the split's headline figures.

  All three decide from the recipe's report, never from a file merely being present.
- **The app.** The third run option becomes *Before the tree split*, and the method page's
  cover paragraph describes the split with its measured shares.

**Proof nothing moved before adoption:**

- recipe outputs re-run and fingerprinted: **10 of 10 identical**, and no new file;
- priority list, district list and checks: **3 of 3 identical**;
- SoilSense screens: 7 of 7.

**The adopted path, tested on a throwaway copy of the bundle** marked adopted (then
deleted): 5 of 5 screens open, and the method page and run options read as intended.

### 2026-10-20 · Phase 1, V3 part 1: measured river mud — what exists, and what a fair test needs

**Found:** the Central Water Commission's **daily suspended-sediment measurements** are open
on the National Water Data Portal (CKAN API, no key; licence "Other (Open)"), one CSV per
state. `scripts/fetch/fetch_46_cwc_sediment.py` fetched Assam, Arunachal and Meghalaya with
provenance. Assam alone has **225,546 daily readings at 33 stations**, 14 of them with 30–48
years, as concentration in g/L.

**Not found: river flow (discharge) for Assam.** CWC's daily discharge on the portal covers
only Meghalaya among the North-East states. Flow data for the transboundary Brahmaputra and
Barak basins is withheld in India. Concentration cannot be turned into tonnes per year from
this source, so any test ranks concentration (or concentration over rain), not loads.

**Which stations can test the map** (`scripts/inspect/sediment_station_catchments.py` →
`reports/sediment_station_catchments.csv`). Each station is snapped to HydroRIVERS, its
catchment traced upstream, and the share inside Assam and inside India measured:

- **Only 2 long-record stations drain mostly Assam:** the Kopili at Jagibhakatgaon (36
  years, 81% in Assam) and the Gaurang at Kokrajhar (30 years, 72%; the rest is Bhutan). Two
  stations cannot rank anything. **A fair V3 test is not possible on the Assam-only map.**
- **12–13 long-record stations drain land ≥ 95% inside India**, from the hills around Assam:
  Dhansiri at Golaghat (48 years), Dikhow at Sivasagar (46), Buridehing at Chenimari (41) and
  Margherita (20), Digaru at Sonapur (38), Barak at Badarpur, Annapurna Ghat and Fulertal
  (36–37, nested), Kopili (36), Katakhal at Matijuri (36), Rukni at Dholai (33), Sonai at
  Tulargram (27), Dudhnai (38; its snap is > 1 km, check it). The headwaters are in
  Meghalaya, Nagaland, Manipur, Mizoram and eastern Arunachal. Several are nested
  (the Barak and Buridehing stations), so the independent count is about 9–10.
- The Kulsi station's coordinates fall more than 3 km from any reach draining ≥ 50 km²;
  not guessed.
- Bhutan-fed rivers (Manas, Beki, Sankosh, Puthimari, Gaurang in part) and the Brahmaputra
  main stem cannot be covered: the national rain-strength maps are India-only.

**What a fair test needs:** the erosion map extended over those catchments, as a new region
on the backbone (bounding box about 91.7–96.9° E, 22.9–27.7° N, about 520 × 530 km, the same
size class as Assam). Every step is the existing chain with a region switch: DEM, soil, land
cover, terrain, hydrology, recipe, and the tree-split inputs from Earth Engine (about 2½ h
more). It would also be a second proof that the backbone moves. **Not started: the user's
call** (register V-22).

**Found on the way, for V-01 (rain strength):** ~~the portal also has **CWC hourly rainfall
for Assam, 1961–1990 and 1991–2020**, plus telemetry hourly rainfall from 2021.~~
**Corrected the same day:** those periods are file-name templates, and most "hourly" files
hold daily readings. The real spans are in "Rain-gauge records: what is really there"
below. Rain
erosivity is computed from rain intensity, so this could give measured R at many Assam
stations instead of Guwahati alone, and settle the rain-map question behind S7's failure.
Hourly data under-reads 30-minute intensity, so a published hourly-to-I30 correction would be
needed (register V-01).

### 2026-10-20 · Rain-gauge records: what is really there (correction)

`scripts/fetch/fetch_47_cwc_rainfall.py` fetched all 17 CWC rain files for Assam and
Arunachal from NWDP (about 90 MB, with provenance). `scripts/inspect/cwc_rain_inventory.py`
→ `reports/cwc_rain_inventory.csv` then measured, station by station, the real first and
last dates and the **true resolution** (median readings per day with any reading).
**Neither the period nor the resolution in a file name can be trusted:**

| | Assam | Arunachal |
|---|---|---|
| **Truly hourly** (≥ 12 readings a day) | **9 stations, telemetry only, from 2019**: Nematighat, Goalpara, Melabazar, Golokganj, Tezpur, Dibrugarh, Guwahati (D.C. Court), Dhubri, … About 2–7 years each | **1 station** (Lemeking), 2019–2020 |
| "Manual hourly" files | 13 of 14 stations are really **daily** (1991–2018); 1 partial | The one station is **daily** (2006) |
| Daily gauge records | **From 1971**: 15 stations 1971–1990, 61 in 1991–2020, about 80 in 2021–2025 | **From 1970**: 4 stations 1970–1990, 17 in 1991–2020, 18 in 2021–2025 |

**What this means:**

- **No decades of hourly rain exist on the portal, for either state.** The long records
  are daily.
- **Measured erosivity from gauges:** hourly telemetry gives at most about 7 years at about
  9 Assam stations, short against the ~20 years erosivity needs to settle, and hourly
  under-reads 30-minute intensity. Usable as rough anchors, not as a verdict.
- **A stronger route for V-01:** the decades of daily gauge rain, run through the *daily*
  erosivity model whose parameters InRESatE publishes ("Daily Rainfall Erosivity Model
  Parameters", Zenodo 11064154). That tests whether InRESatE's satellite rain reads the
  ground's rain correctly at about 60–80 places. It uses InRESatE's own daily-to-erosivity
  link, so it checks the rain, not the link.
- **What the platform uses** (unchanged, and a different thing): satellite rain, IMERG
  daily since 2000, for every square of both states. Gauges are points, sparse in the hills.

### 2026-10-20 · V-01 part 1: rain strength at the gauges — the test, written before computing

**Question:** does the rain behind the InRESatE map (satellite) match what fell into ground
gauges, and does its *pattern* across places hold better than IRED's? This is the question
behind S7's failure.

**The link from daily rain to erosivity** (InRESatE publishes it: "Daily Rainfall Erosivity
Model Parameters", per 0.1° square). The paper confirms a power law fitted to daily rain; the
readme does not say whether days below a threshold are dropped. That was **settled
empirically**: run on our own IMERG daily rain for Arunachal, 2001–2018 (the map's years,
same 0.1° squares), the variant with **no threshold** reproduces the published R best.

| Threshold | Our formula / published R, median (IQR) | Log-correlation |
|---|---|---|
| none | **0.98** (0.72–1.80) | 0.887 |
| 10 mm | 0.84 (0.62–1.59) | 0.889 |
| 12.7 mm | 0.80 (0.58–1.53) | 0.888 |

So **daily EI = a × P^b on every rain day**, with a and b from the gauge's square. The scatter
(IQR) is IMERG version and daily-vs-30-minute noise, the same for every variant.

**The gauge records list rainy days only.** Not one reading is 0 (1,968 station-years;
median 118 rain days a year; the monthly shares follow the dry-winter climate). An unlisted
day is taken as dry. A partly observed year cannot be spotted by counting days, so the rule
below looks at months.

**The test** (fixed now, before any gauge R is computed):

| Piece | Rule |
|---|---|
| Gauges | CWC **manual daily** rain, Assam and Arunachal (`fetch_47_cwc_rainfall.py`), de-duplicated by station and day |
| Years | **2001–2018 only**, the years of the InRESatE map, so years cannot explain a difference |
| A qualifying station-year | Every month April–September has **≥ 5 recorded rain days** (the erosive season observed throughout) |
| A qualifying station | **≥ 8 qualifying years** in 2001–2018. Fewer than the ~20 erosivity ideally needs, said plainly |
| R at the gauge | Mean over its qualifying years of Σ a·P^b over the recorded days |
| Compared with | InRESatE R and IRED R at the gauge's location |
| Reported | Per station, map ÷ gauge; across stations, the median ratio and Spearman ρ of each map against the gauges, for Assam, Arunachal and both |
| Expected direction | A gauge is a point and a map cell is 11 km of averaged rain, so point rain has higher peaks. **Map ÷ gauge somewhat below 1 is expected** and is not by itself a fault |
| **Decision rule** | InRESatE stays the main R **unless** the gauges' pattern agrees with IRED better by **≥ 0.2 in ρ** **and** InRESatE's own ρ is **< 0.4**. If InRESatE's median ratio is outside 0.5–2.0, its absolute level is flagged (it moves classes, not ranks) |
| What it does not test | The daily-to-erosivity link itself: the same a, b are used on both sides. It tests the *rain*, and where it is heavy |

### 2026-10-20 · V-01 part 2: rain strength at the gauges — results

`scripts/inspect/gauge_erosivity.py` → `reports/gauge_erosivity_check.json`,
`reports/gauge_erosivity_stations.csv`. Run exactly as written in part 1.

- **Stations:** 72 seen, **40 counted** (≥ 8 complete years in 2001–2018): 32 in Assam, 8 in
  Arunachal. None dropped for coordinates.
- **Pattern, Spearman ρ against the gauges:**

  | | InRESatE | IRED |
  |---|---|---|
  | Assam (32) | **0.36** | 0.20 |
  | Arunachal (8) | −0.14 | **0.71** |
  | Both (40) | **0.24** | 0.16 |

- **Decision rule → InRESatE stays** (IRED is not ≥ 0.2 better, overall or in Assam). For
  Assam, the erosion target, InRESatE's pattern is the better of the two, but **neither
  agrees strongly**. In Arunachal (8 stations) IRED does far better; noted for the
  landslide and flood work, not acted on here.
- **Level:** median map ÷ gauge is **1.72** (InRESatE) and 1.71 (IRED). That is the
  *opposite* of the direction written in part 1 ("somewhat below 1"). It is inside the
  0.5–2.0 band, so not flagged.

**The finding that matters: both maps flatten the real contrast.**

| Gauge's yearly rain | Stations | InRESatE ÷ gauge | IRED ÷ gauge |
|---|---|---|---|
| under 2,000 mm | 20 | 2.29 | 2.55 |
| 2,000–2,600 mm | 13 | 1.69 | 1.19 |
| 2,600–3,200 mm | 4 | 0.90 | 1.23 |
| over 3,200 mm | 3 | 0.47 | 0.52 |

- Map ÷ gauge falls steadily as gauge R rises (ρ −0.73 / −0.74). On log scales the maps follow
  the gauges with a slope of only **0.07 / 0.11**, where 1 would be the same contrast.
- The wettest foothill gauges read about half on both maps: Pasighat R 13,589 by gauge vs
  6,332 InRESatE; the Subansiri at Chouldhowaghat 11,051 vs 6,656; Bhalukpong 10,625 vs 3,890.
  The drier plains read 2–2½ times high.

**Two cautions before reading too much into it:**

1. **The gauge records list rainy days only**, so a missed day looks dry. Some dry-end
   stations are surely incomplete: Anipur at 682 mm a year, map ÷ gauge 10.5, is one. That
   inflates the ratios at the dry end.
2. **40 points, one per gauge;** a 0.1° square holds many microclimates.

So the slope is uncertain, but its sign agrees at both ends and on both maps.

**What it means for the soil-erosion module:**

- If the gauges are right, R contrast is larger than the maps say. The very wet foothills
  along the Arunachal border would be under-scored and the dry plains over-scored. The
  hills-first ranking would be **stronger**, not weaker. The foothill belt (Lakhimpur,
  Dhemaji, the Kamrup–Bhutan edge) is where R error matters most.
- R remains **the least certain factor**. That matches S7: the ranking moves most with the
  rain map.
- **Upgrade path (register V-01):** a gauge-corrected R surface, adjusting the map toward the
  gauges with distance-weighting and height, once gauge completeness can be checked
  (e.g. against IMERG daily at the gauges for the same days, which needs the Assam IMERG
  archive, V-15).

**For the landslide and flood modules** (REMAINING_WORK #25): the same gauges suggest
satellite rain *maps* (and possibly the IMERG they were built from) under-read the wettest
foothill stations. Check IMERG daily against these gauges directly before drawing any
conclusion there.

### 2026-10-20 · Phase 1, E1.1 part 4: results — P1 passed, P2 failed, the split is NOT adopted

**Inputs:** 1,417 tiles fetched (resumed once after the session ended at tile 1,177),
written to `data/raw/04_landcover/ee_tree_split/tree_split_inputs_assam.tif` with provenance.
`tree_split.py` → `reports/tree_split_assam.json`, `data/interim/assam/features/tree_subclass.tif`.

**P1, tea vs forest on the test half: PASS.**

- T_low = **0.41** (share of 1 m canopy under 3 m), set on the calibration half
  (45,691 tea / 95,924 forest cells). Calibration balanced accuracy 0.873.
- **Test half: 0.848** (53,162 tea / 274,967 forest cells; bar 0.80). By outline, 222 of 223
  tea gardens and 20 of 25 forests are right by majority.
- T1/T2 claim 2.3% of tea and 3.0% of forest reference cells. No cell lacked height data.

**The split it gives over all Assam tree land:** freshly cleared 1.3%, regrowing 2.1%, **low
canopy 53.1%**, tall canopy 43.5%. Area-weighted mean C over tree land would be **0.103**,
against D8's 0.03 (P3, reported, no bar). Median Meta height: low canopy 2.2 m, tall canopy
10.2 m (ETH 14.5 / 21.8 m).

**P2, blind eye check: FAIL.** 100 pictures (25 per sub-class) labelled by eye before the key
was opened (`eyecheck_tree/labels.csv`):

| Sub-class | Expected | Share (all) | Bar | Readable only | Labels |
|---|---|---|---|---|---|
| T1 freshly cleared | cleared | **0.20** | 0.60 | 0.25 | cleared 5, tea/bush 6, closed 9, can't tell 5 |
| T2 regrowing | — | — | — | — | cleared 6, tea/bush 4, closed 15 |
| T3 low canopy | tea/bush | **0.24** | 0.60 | 0.60 | cleared 3, tea/bush 6, closed 1, **can't tell 15** |
| T4 tall canopy | closed canopy | **0.44** | 0.70 | 0.65 | tea/bush 6, closed 11, can't tell 8 |

**Per the rule written before measuring: the split is not adopted.** The main run stays at
the D8 class average (0.03). No output, ranking or app page changed: `"adopted": false`, and
the hookup (part 3) keeps everything as it was.

**Why it failed — what the pictures showed:**

1. **T1/T2, recent clearing.** Most "freshly cleared" cells show canopy in the imagery.
   Likely causes:
   - **imagery dates:** Esri's World Imagery is a mosaic of various years, often older than
     the 2024–25 Hansen loss, or after regrowth;
   - **Hansen's 30 m loss pixels** cover only part of a 100 m cell (the rule needs ≥ 25%).

   The pictures cannot judge a recent change without dated imagery.
2. **T3, low canopy.** Most unreadable cells are **village homestead groves** (trees, bamboo
   and areca around houses and fields), a cover the four labels did not foresee. They read as
   "low" on Meta, perhaps from gaps, shadows or the mosaic of houses and gardens. Where a
   T3 cell was readable, 60% were tea or bush.
3. **T4, tall canopy.** 6 of 25 were labelled tea/bush. Those were uniform, smooth, dark-green
   textures that could equally be dense forest at this image resolution. Labeller error is
   possible here.
4. **The labeller.** The labels were made by eye on about 1 m-per-pixel images of a 500 m
   window. Many are genuinely ambiguous, so the 25% "can't tell" is itself a finding:
   **this imagery is not enough to grade 100 m cover classes reliably.**

**What would make a second attempt fair** (not started; new pre-registration and a **new**
blind sample, never these 100 pictures):

- a fifth label, **homestead grove**, and a C value for it;
- dated imagery for T1 (Sentinel-2 before/after composites of the clearing year), not a
  mosaic;
- a canopy-*cover* input beside height (e.g. Sentinel-2 dry-season NDVI), to tell gaps in
  forest from low bush;
- an OSM or NESDR settlement layer to pull village groves out first.

Register **V-02** is updated. V-16 (the "indicative on tree land" note) stays.

### 2026-10-20 · The official Assam outline is in (V-12 resolved)

**Source.** The user downloaded the Survey of India's free "State Upto Distt. level with HQ"
(OVSF/1M/9, 1:1M) into `data/raw/01_boundaries/18/`.
`scripts/fetch/fetch_01b_soi_boundaries.py` cleaned it (names stripped and title-cased, the
source's "ANAGLONG" typo corrected), converted it from the source's Lambert projection to
EPSG:4326 and recorded provenance. It wrote `soi_state-…`, `soi_district-…` and
`soi_district-hq_point_assam.gpkg`.

**How it is wired.**

- `common.outline(kind)` returns each region's outline. Arunachal stays on GADM, untouched;
  Assam uses the Survey of India files.
- Nine scripts that read `gadm_*_{AOI_NAME}` now call it.
- S1's hill districts became Karbi Anglong + **West Karbi Anglong** + Dima Hasao: the same
  land as GADM's two, under today's names.

**What changed:**

- **Outline:** 78,424 km², −0.02% from the official 78,438; GADM was +0.05%. About 281 km²
  was gained and 330 km² lost along the edges.
- **In-state cells:** 7,842,412, against 7,847,338.
- **Districts:** **35 with LGD codes** instead of 27, including Bajali, Biswanath, Charaideo,
  Hojai, Majuli, South Salmara, Tamulpur, West Karbi Anglong and Sribhumi (formerly
  Karimganj).
- **Folds re-frozen, same hash** `a6bc908e791c9063`: no 50 km block changed group, so no
  earlier number is affected.

**The whole Assam chain was re-run** (masks, terrain, hydrology, height above channel,
features, recipe, checks, ranking, bundle; logs `logs/assam_soi_*.log`). The old mask,
folds and reports are kept in `data/interim/assam/_pre_soi_outline/`.

- Checks are unchanged in substance: S1 8.3×, S2 69.0% vs 65.1%, S3 to S5 pass, S7 7/20
  (ρ 0.82), S8 −0.46 over **35** districts.
- **Top 20 catchments: the same 20 units**, slightly reordered, so the E0.8 eye check still
  covers them. Its file keeps the old rank numbers and GADM district names.
- **District ranking with today's districts:** Kamrup Metro 49.6 t/ha/yr, Dima Hasao 49.2,
  Kamrup Rural 49.2, Cachar 42.9, **West Karbi Anglong 42.5** (now apart from Karbi Anglong,
  24.9), Hailakandi 42.4, Sribhumi 25.7.
- App: 7 of 7 SoilSense screens pass. The method page now names the Survey of India outline.
- `check_live_unchanged.py check`: PASS, 0 changed.

### How to run anything for Assam

```powershell
$env:REGION = "assam"          # PowerShell; unset it (Remove-Item Env:REGION) to go back
.venv\Scripts\python scripts\fetch\fetch_01_boundaries.py
.venv\Scripts\python scripts\build\make_folds.py
```

In Git Bash: `REGION=assam .venv/Scripts/python <script>`. With no REGION set, every
script runs for Arunachal exactly as before.

---

## Key dates (NESFIC 2026)

| Date | What |
|---|---|
| ~~25 Sep – 25 Oct 2026~~ | ~~Application window~~. **Wrong: corrected 2026-10-17** |
| **25 Oct 2026** | **Clarification cut-off**: last day to put questions to the department |
| **10 Nov 2026** | **Applications close.** Our target is to submit by **7 Nov** |
| Nov 2026 | North East Seva First Innovation Conclave, Guwahati |
| Nov 2026 – Feb 2027 | Prototype development phase |
| Feb 2027 | Demo Day |
| Feb – May 2027 | MVP phase |
| Jun 2027 → | MVP demonstration and market access |

Grants: Idea-stage up to ₹10 L · MVP & Prototype up to ₹20 L · Deep Tech up to ₹40 L.
Selection does not guarantee procurement. No prototype is required to apply, but "Maturity"
and "Feasibility" are scored, so a working first map is worth a lot.

---

## Revision of 2026-10-17 — what the check found

Every assumption in this plan and in [EROSION_MODULE.md](EROSION_MODULE.md) was checked
against the official challenge pages (read 2026-10-17), the published literature and,
where possible, the data itself. Twelve findings. The first three change the plan.

### R1 · The deadline is 10 November, not 25 October

The challenge's own record gives `applicationCloseDate 2026-11-10` and
`clarificationCutOffDate 2026-10-25`. The same is true of all 50 published challenges. Only
the timeline graphic on the NESFIC home page still shows "25 Sep – 25 Oct", and it looks
out of date. **25 Oct is the last day to put questions to the department.** Confirm by
email to `query.nesfic@assamstartup.org` (task A2) and keep the 7 Nov submit target either
way.

### R2 · The planned rain factor reads about 11 times too low in Assam

The plan used R = 79 + 0.363 × annual rain (Singh et al. 1981). IIT Guwahati computed R
from 15 years of half-hourly IMD rain at Guwahati: **7,924 MJ mm ha⁻¹ h⁻¹ yr⁻¹**. Singh's
relation gives **693** on the same rain, −91% (Das & Sarma 2017, IIT Guwahati report,
Table 5.10). Every annual-rainfall relation in common Indian use was 70–91% low there.

Two open, measured-intensity R maps for India exist, both CC-BY 4.0 on Zenodo, both
downloaded and read on 2026-10-17 (scratch script; numbers in the Results log):

| R source | Built from | Guwahati | Assam median | vs Guwahati gauge |
|---|---|---|---|---|
| Singh et al. 1981 | annual rain | 693 | — | −91% |
| **IRED** (Raj et al. 2022, IIT Delhi) | hourly IMDAA reanalysis, 1979–2018, 0.12° | 4,258 | 6,652 | −46% |
| **InRESatE** (Das, Jain & Gupta 2022, IIT Roorkee) | 30-min IMERG, 2001–2018, 0.1° | **7,507** | 5,613 | **−5%** |

**Decision taken into the plan:** InRESatE is the Phase 0 R. IRED is run alongside as a
sensitivity case. Our own IMERG archive is not needed for the Phase 0 R. That removes the
~2 h Assam IMERG pull from E0.3 (it returns in Phase 2 for the weekly outlook). One gauge is
thin support for this choice. More station values are an ASK (IMD / ASDMA rain-intensity
records).

### R3 · The two good R maps disagree on where the rain is most erosive

Ranked by district median, IRED and InRESatE agree only weakly (Spearman **0.26**, 27 GADM
districts). IRED puts western Assam (Kokrajhar, Dhubri, Bongaigaon, Chirang, Baksa) at
2–2.6 times InRESatE. Two consequences:

- **The ranking is not automatically robust.** The plan assumed that whatever the error in
  the tonnes, the ranking would hold. That is only true if the *pattern* of R is right.
  So every priority list is computed under both R maps, and units that are top-ranked under
  both are marked as such (new sanity check S7).
- **The classes inherit the full R uncertainty.** The six classes are fixed tonnage
  cut-offs (5 / 10 / 20 / 40 / 80 t/ha/yr), so a 2× change in R moves land about one class.
  The design's line "a class is more trustworthy than the tonnes" is withdrawn. **The rank
  is what we lead with.** The class is shown, labelled with the R map it was computed on.

### R4 · A national erosion map that covers Assam already exists

Raj, Saharia & Chakma (IIT Delhi): RUSLE at 250 m for all of India, built on IRED. It ranks
**9 of India's 20 most erodible districts in Assam**: Chirang, Baksa, Kokrajhar, Bongaigaon,
Dhubri, Barpeta, Udalguri, Goalpara, Nalbari, at 105–202 t/ha/yr. Its data, IWED (Zenodo
7823909, 2.3 GB, no licence stated), is open to read. Also in existence: GloSEM (Borrelli et
al.) and the SAC/ISRO Desertification and Land Degradation Atlas (Assam: 716,596 ha degraded
in 2011–13). Consequences:

- The proposal's section 11 (innovation and prior art) must name these and say what we add:
  100 m and not 250 m; bareness refreshed each season from Sentinel-2 and not fixed by a
  land-use class; a rain source checked against a gauge; a ranked work list with the main
  driver named; and a field loop that grades the map. **"A static map exists" is the
  department's own stated problem, so prior art supports the case and does not threaten
  it.**
- IWED is a ready V2 comparison. Its western-Assam hotspots come mostly from IRED's high R
  there, so a disagreement with us is expected wherever we use InRESatE. It is read as
  "which R is right", not as "who is right".
- IWED has no licence, so it is used only to compare. It is never redistributed or shown
  as a layer.

### R5 · The slope factor needs a steep-slope form

The Moore & Burch LS form (exponent 1.3 on sin β) was derived for gentle slopes (under about
14°) and over-predicts on steep ones. Dima Hasao and Karbi Anglong reach well past that.
Use the RUSLE S of McCool et al. (1987), with Nearing (1997) as the steep-slope check. Keep
the flow-accumulation L term with its cap. Record the choice in design §5.2. The comparison
of the two forms is logged and is not a pass/fail check.

### R6 · The cover formula has a tropical alternative, and Phase 0 should use the class lookup

van der Knijff's C = exp(−2·NDVI / (1 − NDVI)) was built for Europe. Durigon et al. (2014)
proposed C = (1 − NDVI) / 2 for tropical conditions, and one Brazilian comparison found
van der Knijff too high. Water and wet paddy (NDVI < 0) push van der Knijff's C above 1.
**Phase 0 uses the WorldCover class lookup** (with literature values, as IWED does). The
Sentinel-2 NDVI cover is Phase 1 and is computed both ways, as a sensitivity case.

### R7 · The pre-registered bars need three changes, made now, before any number exists

These are revisions to bars written on 2026-09-29. They are made before any erosion number
exists, so they are still pre-registered. S3 is changed because GloREDa sits behind
registration with ESDAC (European Soil Data Centre) under non-commercial terms. The gauge
anchor is independent and open. S7 and S8 are new.

| # | Check | Pass bar |
|---|---|---|
| S3 (revised) | Factor ranges | K within 0–0.08 SI; C within 0–1; R: the chosen map within ±25% of the Guwahati gauge value (7,924). InRESatE meets this already (7,507, −5%), so for R this is a recorded check, not a test. K district medians compared with ISED (Raj et al. 2023, CC-BY) and logged |
| S7 (new) | R robustness | Of the top 20 HydroBASINS-12 units under InRESatE, **≥ 10** are also top 20 under IRED. If fewer: the priority list is shown with a "depends on the rain source" mark on every unit that is not top-ranked under both, and the proposal says so |
| S8 (new) | Prior-art comparison | District Spearman against IWED: logged, no pass bar (confounded by R, see R4). Our ranking re-run on IRED should agree with IWED better than our InRESatE ranking does. If it does not, something other than R differs and must be explained |

S1 (hills ≥ 3× plains) stays. RUSLE's slope term is small on flat land, and the floodplain
mask removes river land. IWED's western-Assam result is a rain result, which S8 tests.

### R8 · The users include farmers and communities

The challenge names "farmers, communities in erosion-prone areas and government teams".
The design spoke only to officials. Add a plain village card in **Assamese** to the
prototype (Phase 2). The proposal's user-journey section shows both users.

### R9 · The proposal has a fixed 12-part form, plus a pitch deck

The "Uniform Solution Proposal Requirements" (`/nesfic26/docs/uspr.pdf`, one page) apply to
every challenge: (1) problem and user workflow, (2) solution and features, (3) user journey,
wireframes and prototype, (4) technology and architecture, (5) development method,
(6) timeline and milestones, (7) data needs, "**do not assume unconfirmed access**",
(8) team and manpower, (9) testing, validation and evidence, (10) security, privacy and
compliance, (11) innovation and prior art, (12) resources, risks and pilot validation. The
terms add: upload a pitch deck; disclose third-party data, software and IP; team of up to
five with one Lead Applicant. E0.10 is rebuilt around these twelve parts.

### R10 · Only one MVP grant per applicant per edition

An applicant may apply to several challenges, but can receive **only one MVP grant**, and
idea-stage grants for at most two challenges. If we also apply to D-18 (flood digital twin,
ASSAC) with FloodSense, the two compete for the same single MVP grant. That makes decision
D6 a strategy question, not just an eligibility question.

### R11 · Smaller corrections

- The Assam State Geoportal (`gistcp.assam.gov.in`) needs a registration with a captcha
  before anything can be downloaded. Register now (A3); GADM is the stand-in until then.
- The planned `scripts/fetch/fetch_40_s2_cover.py` clashes with the existing
  `fetch_40_era5land_melt.py`. ~~Use `fetch_42_s2_cover.py`~~: 42 went to the rain maps
  (`fetch_42_erosivity.py`), so use **`fetch_43_s2_cover.py`**. (2026-10-20: 43 became the tree-split inputs, `fetch_43_tree_split_inputs.py`; 44 and 45 the reference maps and OSM outlines. A seasonal Sentinel-2 script, if built, takes the next free number.)
- The department's nodal officer is **Syed Arfad Hussain**, i/c Divisional Officer,
  Engineering Soil Conservation Division (contact details in the challenge record). The
  originating unit is the *Engineering* Soil Conservation Division.
- Copernicus DEM tiles needed: Assam spans about 24.1–28.0° N, 89.7–96.0° E. On disk:
  N26–N29 × E91–E97 (from Arunachal). Still to fetch: the N24 and N25 rows and the E89–E90
  columns, about 16–20 tiles.
- The Bhuvan land-cover WMS (`bhuvan-ras2`) answered; `bhuvan-vec2` timed out today. The
  NESDR Assam page redirects to http. ESDAC answers but needs registration.

### R12 · What does not change

The five-ingredient recipe, the region port, the domain mask, D1 (a), the open-data-first
order and the phases after Phase 0 all stand. The landslide and flood lessons the design
cites (check *where* a layer puts its extremes; test change detection for false alarms
first) were checked again and still apply.

---

## Phase 0, revised — 17 Oct → 7 Nov 2026

**Rule for the whole sprint:** the live 08:30 flood run shares this code. Run
`check_live_unchanged.py record` **before** the first change to `common.py` or `grid.py`.
Run `check` after every change. Make no edits to shared files between 08:00 and 09:00.

**Admin track (A), this week:**

| ID | Task | Done when | By |
|---|---|---|---|
| **A1** | Register the Lead Applicant on the NESFIC portal and read the real form's mandatory fields | Field list copied into this file | 19 Oct |
| **A2** | Send clarification questions to the nodal officer, copied to `query.nesfic@assamstartup.org`: (1) confirm the 10 Nov close; (2) the department's soil-loss class scheme (D4); (3) the unit it plans works in (micro-watershed set, SLUSI codes?); (4) which records it can share, and when: treated areas (→ P), field observations, soil survey; (5) its GIS software and preferred formats; (6) the pilot areas it has in mind (D3); (7) whether riverbank erosion is in scope or another department's | Sent | **22 Oct** (3 days before the cut-off) |
| **A3** | Register on the Assam State Geoportal (official boundaries); optionally ESDAC (GloSEM) | Accounts exist | 20 Oct |
| **A4** | Decide D2, D5, D6 (with R10 in mind) | Logged in the Decisions table | 24 Oct |

**Build track, in order:**

| Window | Tasks | Notes |
|---|---|---|
| 17–19 Oct | `record`; **E0.1** region registry; **E0.2** Assam grid (GADM stand-in); start **E0.3** (DEM ~16–20 tiles, SoilGrids, 1–2 WorldCover tiles; InRESatE and IRED already fetched once; re-fetch them through `common.record()` so they carry provenance) | **E0.6 on Arunachal starts in parallel**: every input is on disk |
| 20–23 Oct | **E0.4** Assam terrain, hydrology, features; **E0.5** freeze folds (hash before any model) | A2 goes out by 22 Oct |
| 24–28 Oct | **E0.6** on Assam (R = InRESatE + IRED case; K Williams; LS with McCool S; C class lookup; P = 1); **E0.7** all sanity bars, including the new S7 and S8 | A failed bar means *investigate before showing* |
| 29 Oct–1 Nov | **E0.8** priority on HydroBASINS-12 and districts, top 20 with driver, checked by eye on imagery; **E0.9** app screen (status "building"), screenshots | Answers from A2 folded in if they arrived |
| 2–6 Nov | **E0.10** proposal in the 12 USPR parts + pitch deck; limits table; data table that marks every source *open / confirmed / not yet confirmed* (USPR §7) | One full read-through by someone who did not write it |
| **7 Nov** | **Submit** | 8–10 Nov is buffer for portal trouble |

**Out of Phase 0, said plainly in the proposal as the roadmap:** the seasonal Sentinel-2
cover, change maps, the weekly outlook, the field kit and the Assamese village card.

---

## Decisions needed

| # | Decision | Options | Recommendation | Needed by |
|---|---|---|---|---|
| **D1** | Where Arunachal's data lives after the region port | (a) leave Arunachal's folders as they are, put Assam in region subfolders · (b) move Arunachal into the same region layout | **(a) now**: zero risk to the live 08:30 flood job during the sprint. Revisit (b) after Demo Day | E0.1 |
| **D2** | Module name | SoilSense · ErosionSense · other | Your call — "SoilSense" is only a working name | E0.9 |
| **D3** | Pilot areas | Hill districts, foothill belt, tea-garden slopes, Barak hillocks | **Dima Hasao + Karbi Anglong** (steep, *jhum*, erosion a known concern) + one foothill belt as contrast. Confirm with the department | E0.10 (proposed), E2.5 (agreed) |
| **D4** | Risk-class scheme | The department's own · the common Indian six-class scheme | **Theirs if they have one**, so our map compares directly with their work | E0.6 (provisional), E2.5 (final) |
| **D5** | Grant tier to apply for | Idea ₹10 L · MVP & Prototype ₹20 L · Deep Tech ₹40 L | **MVP & Prototype**: two live modules plus a working Assam first cut is past idea stage | E0.10 |
| **D6** | Also apply to D-18 (flood digital twin) with FloodSense? | Yes / no | **Checked 2026-10-17:** several applications are allowed, but only **one MVP grant** per applicant per edition (R10). Applying to both raises the chance of selection, but the two can't both win an MVP grant. Your call. Not part of this plan | A4, 24 Oct |
| **D8** | Cover value (C) for WorldCover "tree" (forest + tea gardens + *jhum* fallow) in the main run | 0.03 (IWED) · 0.003 (closed forest) · an in-between value · NDVI→C formula · split the tree class with Sentinel-2 | **DECIDED 2026-10-17: keep 0.03 as a class average; 0.003 alongside; upgrade = split the class (E1.1).** Reasoning in the Build log, "Decision D8". Revisit triggers: register item V-02 | done |
| **D7** | Mention riverbank erosion (X1) in the application? | Omit · one line · full section | **One line, as a future extension.** It's another department's remit and must not blur the D-07 answer | E0.10 |

---

## Phase 0 — Application proof (29 Sep → 18 Oct 2026)

> **Superseded for dates and for E0.3, E0.6, E0.7 and E0.10** by
> [Phase 0, revised](#phase-0-revised--17-oct--7-nov-2026). The task definitions below still
> hold except where the revision changes them (R2–R7, R9).

**Goal:** the first honest erosion map of Assam, produced by the *same* backbone with only a
region switch, on screen in the app, plus the application.

**Two tracks run side by side, so the downloads never block the method work:**

```
 Track A — port the backbone     E0.1 ──► E0.2 ──► E0.3 (downloads, background) ──► E0.4 ──► E0.5 ─┐
                                                                                                  ├─► E0.6 Assam ──► E0.7 ──► E0.8 ──► E0.9 ──► E0.10
 Track B — the recipe            E0.6 on ARUNACHAL (all inputs already on disk) ──────────────────┘
 Anytime, never blocking         E0.11 access checks
```

| ID | Task | Output | Done when | Est. | Status |
|---|---|---|---|---|---|
| **E0.1** | **Region registry.** `common.py` and `grid.py` take a region (`--region` / `REGION`, default `arunachal`). The Arunachal entry is identical to today's constants | Region registry in one place | `check_live_unchanged.py check` passes. Existing Arunachal scripts run unchanged with no flag. Arunachal constants equal the frozen ones | 1 d | ☑ |
| **E0.2** | **Assam grid + boundary.** Freeze the spec (design §4.1: EPSG:32646, 100 m, origin 160,000 / 2,660,000, 6,400 × 4,400). State mask. Official boundary and current districts from the Assam State Geoportal (GADM as a stand-in until then) | `DATA_CONTRACT.md` §8 "Assam region"; state mask | In-state cell count recorded; area within 1% of 78,438 km²; spec written into DATA_CONTRACT | 0.5 d | ◐ |
| **E0.3** | **Fetch Assam raw.** DEM (~20 new tiles), SoilGrids (Assam box), WorldCover (1–2 tiles west of 90°E), HydroSHEDS clip (local), IMERG daily 2000-06 → now (~2 h) | Raw files + `_SOURCES.json` entries | Every raw folder has an Assam entry in `_SOURCES.json`; IMERG day count matches Arunachal's date range; no DEM holes inside the state | 1 d (mostly waiting) | ☑ |
| **E0.4** | **Build Assam backbone.** Terrain, hydrology (flow accumulation, channels, height above drainage), soil and land-cover features, rain stack | `data/interim/assam/…` | `check_terrain` / `check_hydro` / `check_rainfall` pictures reviewed for Assam; most plains cells < 2°; drainage follows the Brahmaputra and Barak | 1–2 d | ☑ |
| **E0.5** | **Freeze Assam validation folds** (50 km blocks, seed 42), hashed | `spatial_folds.meta.json` for Assam | Hash written **before any model exists**. Cheap now, impossible to do honestly later | 0.5 d | ◐ |
| **E0.6** | **The recipe** — `erosion_factors.py`. Build and debug on **Arunachal first** (can start day 1), then run on Assam. Confirm the R equation's units and coefficients, the K formula, the LS slope-length cap, and provisional classes (D4) | Soil-loss estimate + class rasters, **each factor saved separately**, both regions; unit suffixes per DATA_CONTRACT §5 | Both regions produce all five factor layers and the estimate; formulas and constants written into design §5.2 with sources | 2–3 d | ☑ |
| **E0.7** | **Pre-registered sanity checks** (bars below, written before running) | Results log entries | Every bar evaluated and logged; failures fixed or explained **before anything is shown to anyone** | 1 d | ☑ |
| **E0.8** | **First priority ranking** — `erosion_priority.py` on HydroBASINS level 12 and on districts; top 20 with main driver | Ranked tables | Top 20 checked by eye against satellite imagery: are they visibly steep and/or bare? Any that aren't, explained | 1 d | ☑ |
| **E0.9** | **App screen** — `webapp/products/erosion/` (status "building"), minimal region picker, map + ranking + "how to read this" note; bundle export | Running module | Runs locally; `check_app_screens.py` passes; screenshots taken for the application | 2 d | ☑ |
| **E0.10** | **Application pack** — screenshots, one-page method, requirements table (design §1), evaluation-criteria table (below), tier story, pilot proposal (D3), grant tier (D5) | Submitted application | Submitted before 25 Oct | 2 d | ☐ |
| **E0.11** | **Access checks** (parallel, never blocking): NRSC land degradation (Bhuvan), SLUSI priority watersheds / Watershed Atlas, CWC / India-WRIS sediment, GloREDa, global soil-erosion map, NESDR land cover for Assam, Assam State Geoportal. Use the "portals look closed but aren't" method (test the machine endpoints, not the UI) | Status column in design §12 filled in | Each source marked *open / gated / closed* with the working access route | ~1 d, spread out | ☐ |

**Suggested week-by-week:**

- **Week 1 (29 Sep – 5 Oct):** E0.1, E0.2, start E0.3 downloads, E0.6 on Arunachal, E0.11 begins
- **Week 2 (6 – 12 Oct):** E0.4, E0.5, E0.6 on Assam, E0.7, E0.8
- **Week 3 (13 – 18 Oct):** E0.9, E0.10 drafted
- **Buffer (19 – 25 Oct):** fixes, polish, submit

### E0.7 pre-registered sanity bars

Written 2026-09-29, before any erosion number exists. A failed bar means *investigate before
showing*, not *tweak until it passes*.

| # | Check | Pass bar | Why this bar |
|---|---|---|---|
| S1 | Hills vs plains | Median estimated loss in Assam's hill districts **≥ 3×** the plains median (assessed cells only) | Steep, *jhum*-cleared hills must beat flat paddy. If not, a factor is broken |
| S2 | Canopy-edge trap | Among the top 5% LS cells on flat ground (height above drainage < 10 m), **≤ 25%** sit on a tree / non-tree land-cover edge | Above that, the surface-DEM artefact is driving the map → filter or cap LS on plains |
| S3 | Factor ranges | K within 0–0.08 (SI units); C within 0–1; R within ±50% of GloREDa on the same cells if obtained (else within published NE India ranges) | Catches unit errors — the `bdod = 107` class of bug |
| S4 | Class spread | No single class holds > 80% of assessed land | A map that is all one class ranks nothing |
| S5 | Domain mask | Water, built-up, channels and floodplain flats are shown as "not assessed", never "low" | Design §5.3 |
| S6 | Arunachal untouched | `check_live_unchanged.py check` still passes after all Phase 0 code | The region port must not move the live forecast |

### How Phase 0 answers the NESFIC scoring

| Criterion | What we show |
|---|---|
| Problem Fit | Design §1: every line of the department's statement mapped to a feature and a phase |
| Innovation & Merit | A *living* outlook (seasonal cover + weekly rain), not a one-off map; the driver → treatment reason line; pre-registered, blind validation |
| Maturity | Two live modules (landslide, flood), a daily forecast that is logged and graded, and a working Assam first cut |
| Feasibility | The backbone ported to a second state with a region switch — shown, not promised; open data first, department data as upgrades |
| Impact | Field teams sent to the right micro-watersheds first; the pre-monsoon bare-slope list arrives in time to act |
| Team & Presentation | Screenshots, one-page method, honest limits table (design §9) |

---

## Phase 1 — Seasonal cover + validation (Nov → mid-Dec 2026)

**Goal:** the bareness layer refreshes every season back to 2019, the rain factor is upgraded,
and the ranking faces its first independent checks. The Conclave falls in this window.

| ID | Task | Done when | Status |
|---|---|---|---|
| **E1.1** | Sentinel-2 seasonal composites via Earth Engine, 2019 → now (pre-monsoon, post-monsoon, winter) → C per season; cloud share recorded per composite | Every season has a C layer or an explicit "too cloudy" gap; fallback C used only in the gaps | ☐ |
| **E1.2** | **Specificity test first:** run the change detector on known no-change areas (core forest, long-stable farmland) | False-flag rate measured and below a bar written before running. Only then does E1.3 ship any flag | ☐ |
| **E1.3** | Change maps: same season year on year; year vs year; "new bare ground on a steep slope" flags | Change layers in the app; flags spot-checked against imagery | ☐ |
| **E1.4** | R upgrade: half-hourly IMERG for a sample of monsoons → event erosivity. Compare with the annual relation and GloREDa, then choose | Choice and comparison logged; design §5.2 updated | ☐ |
| **E1.5** | V2 cross-map agreement (whichever sources E0.11 opened) | Rank agreement per district / watershed logged against pre-written bars | ☐ |
| **E1.6** | V3 measured-sediment ranking test (if data opened) | Catchment rank agreement logged, or "no data" logged | ☐ |
| **E1.7** | V4 blind imagery sample, ~300 points stratified by class | Labels made blind; metric vs bar logged | ☐ |
| **E1.8** | Planning units: Watershed Atlas micro-watersheds if obtained, else stay on HydroBASINS level 12 | Ranking runs on the chosen unit | ☐ |
| **E1.9** | Conclave demo build | Demo runs offline-safe with Assam data | ☐ |

---

## Phase 2 — Prototype (mid-Dec 2026 → Demo Day, Feb 2027)

**Goal:** the module does what the department asked: ranked, explained, periodically
updated, field-ready, with the pilot's field comparison designed and agreed.

| ID | Task | Done when | Status |
|---|---|---|---|
| **E2.1** | Weekly outlook: next-7-day erosivity from the live rain × current K·LS·C·P. Runs inside the existing 08:30 daily job; logged like FloodSense | A week of logged outlooks on disk; `check_live_unchanged.py` still passes for floods | ☐ |
| **E2.2** | Grade the rain part daily (forecast erosive rain vs observed IMERG) | Running scorecard; method page says plainly that the soil-loss part is not gradable at FREE tier | ☐ |
| **E2.3** | Place card, priority list with reason line and treatment hint, change view, adjustable weights | All screens in the app; kinds-of-number badges on every figure | ☐ |
| **E2.4** | Field kit: GeoPackage / KML / CSV export; field-check form → records, quarantined before joining authoritative data | Round trip tested: export → fill in → import → appears flagged as unverified | ☐ |
| **E2.5** | Pilot agreed with the department (D3, D4); **pre-registered field protocol** (V5): blind points, metrics, pass bars | Protocol written and dated before any visit | ☐ |
| **E2.6** | Demo Day pack | Demo + deck + results so far | ☐ |

---

## Phase 3 — MVP (Feb → May 2027)

| ID | Task | Done when | Status |
|---|---|---|---|
| **E3.1** | Ingest department / ASSAC data as it arrives: soil survey → K, treated areas → P, intensity gauges → R, high-resolution imagery → gully mapping in pilots | Each source swapped in with a before/after comparison logged | ☐ |
| **E3.2** | Field comparison results (V5) → calibration. Add the ML correction layer **only if** there are enough labelled points; spatial folds, out-of-fold reporting | V5 result logged against its pre-written bar; calibration decision logged | ☐ |
| **E3.3** | Optional PAID pilot: rain-intensity gauges + turbidity sensors at 2–3 pilot outlets | Sensor data flowing; outlook graded against measured sediment | ☐ |
| **E3.4** | Outputs for the department's GIS; district-officer reports | Department can open our layers in their own tools | ☐ |
| **E3.5** | Extensions decision: X1 riverbank watch, X2 gullies, X3 sand-casting, X4 SlideSense/FloodSense for Assam | Decision logged with reasons | ☐ |

---

## Results log

Append-only. One row per measurement. Never edit a past row. Add a new row that supersedes it.

| Date | Task | What was measured | Result | vs bar |
|---|---|---|---|---|
| 2026-09-29 | — | Assam area in EPSG:32646 (GADM polygon) | 78,474 km² vs official 78,438 (+0.05%) | CRS reuse OK |
| 2026-09-29 | — | Assam grid extent, snapped to 10 km | origin 160,000 / 2,660,000; 6,400 × 4,400 cells | — |
| 2026-09-29 | — | Arunachal coupling in code | 33 scripts use the AOI box/name; 29 import the grid; 69 contain "arunachal"; 15 web-app files | Sizes E0.1 |
| 2026-09-29 | — | Assam raw already on disk | 12 of ~32 DEM tiles; 6 WorldCover tiles cover all but the strip west of 90°E; HydroSHEDS Asia-wide; GADM has 27 (outdated) Assam districts | Sizes E0.3 |
| 2026-10-17 | — | NESFIC dates, from the challenge records | Close 2026-11-10 and clarification cut-off 2026-10-25, the same on all 50 published challenges; home-page timeline still says "25 Sep – 25 Oct" | R1 |
| 2026-10-17 | — | R at Guwahati: gauge vs formulas vs maps | IMD half-hourly, 15 yr (IIT Guwahati 2017): 7,924. Singh 1981: 693 (−91%). IRED: 4,258 (−46%). InRESatE: 7,507 (−5%) | R2: InRESatE chosen |
| 2026-10-17 | — | R over Assam, GADM polygon, percentiles 5/25/50/75/95 | IRED (0.12°, 496 cells): 2,598 / 4,986 / 6,652 / 8,856 / 17,949. InRESatE (0.1°, 720 cells): 2,791 / 3,657 / 5,613 / 7,248 / 9,364 | — |
| 2026-10-17 | — | R pattern agreement, district medians, 27 GADM districts | Spearman IRED vs InRESatE = 0.26; IRED/InRESatE ratio 0.6 (Hailakandi, Karimganj) to 2.6 (Baksa) | R3: new check S7 |
| 2026-10-17 | pre-E0.1 | Live-forecast baseline before the region port | Old recording (2026-10-11) backed up to `golden_live_2026-10-11/`; current code vs it: PASS (0 changed). New recording for 2026-10-17 (32 gauges, rain 18 × 219), replayed: PASS. Today's 10:41 issue and the track record untouched | S6 baseline set |
| 2026-10-17 | E0.1 | Region switch (`REGION`, default arunachal) in `common.py` + `grid.py`; `record()` keyed by (source, region) | Arunachal constants vs frozen values: 0 mismatches (REGION unset and =arunachal); grid round-trip OK both regions; unknown region refused; provenance test: entries per region kept apart, default format unchanged; `check_live_unchanged.py check`: PASS, 0 changed | S6 holds |
| 2026-10-17 | E0.2 | Assam grid frozen: 160,000 / 2,660,000, **6,500 × 4,500** (widened from 6,400 × 4,400: E/N margins were 1.2 / 2.1 km) | GADM Assam mask: 7,847,338 cells = 78,473 km² vs official 78,438 (+0.04%); margins W 9.6 S 9.2 E 11.2 N 12.1 km. Spec in DATA_CONTRACT §8 | Bar: within 1% ✔. Open: official outline (A3) |
| 2026-10-17 | E0.5 | Assam folds frozen on the GADM mask (seed 42, 50 km) | Hash `a6bc908e791c9063`; 55 blocks, 52 ≥ 5,000 cells; folds 17.3–25.9% of cells. Re-freeze once if the official outline replaces GADM, before any model | Frozen before any model ✔ |
| 2026-10-17 | E0.3 | Assam raw store | DEM 40/40 tiles readable; SoilGrids 18/18; WorldCover 8 tiles; HydroSHEDS clips 68,215 reaches / 515 L8 / 2,534 L12 basins; R maps with provenance. IMERG not fetched (R2) | Done when: every raw folder has an Assam entry ✔; no DEM holes ✔ |
| 2026-10-17 | E0.4 | Assam base layers | Terrain 8, hydrology 2, height-above-channel 2, soil 18, land cover 1; all 100% cover. Height 8–1,963 m; median slope 2.5°; max upstream 21,118 km² (box-limited); median height above channel 6 m | Pictures ✔; drainage on mapped rivers ✔ |
| 2026-10-17 | E0.4 | "Most plains cells < 2°" (land < 20 m above channel = 72.9% of state) | 58.9% under 2° — passes narrowly | Explained by the next row |
| 2026-10-17 | E0.4 | Slope on river flats (< 5 m above channel) by land cover, median / p90 | Cropland 0.6° / 2.5°; **tree 2.8° / 5.7°**; water 0.0° / 2.0°; grass 0.8° / 2.6°; built 1.8° / 3.1° | Canopy inflates slope (finding 3) |
| 2026-10-17 | E0.4 | Share of state below a height above channel of 2 / 3 / 5 / 10 m | 27.9% / 34.5% / 46.7% / 63.3% | Sets up the E0.6 mask decision |
| 2026-10-17 | E0.6 | Assam recipe, main run | Scored 69.6% of state; R at Guwahati on grid 7,900; median R 5,273, K 0.0166, LS 1.30, C 0.03; A median 8.2, mean 26.0 t/ha/yr; classes 37.6 / 15.3 / 11.1 / 14.5 / 13.6 / 7.8 % | Pictures ✔; bars judged in E0.7 |
| 2026-10-17 | E0.6 | Tree C sensitivity (0.03 → 0.003) | Assam slight 37.6 → 67.4%, mean 26.0 → 10.7 t/ha/yr; Arunachal severe+very severe 74.3 → 7.3%, mean 101 → 36 | D8 opened |
| 2026-10-17 | E0.6 | Papum Pare, mean A vs published | Ours 96.7 (C 0.03) / 11.4 (C 0.003); Dabral et al. 2008 about 51; IWED 32 | Neither fits; nothing fitted |
| 2026-10-17 | E0.7 | Sanity bars, guard v1 | S1 5.1× PASS; S2 91.8% edge (base 65.2%) FAIL; S3 PASS; S4 PASS; S5 PASS; S7 7/20 FAIL | Guard v2 written |
| 2026-10-17 | E0.7 | Sanity bars, guard v2 | S1 8.3× PASS; S2 69.1% vs 65.2% base, FAIL narrowly; S3, S4, S5, S6 PASS; S7 7/20 (ρ 0.82) FAIL; 0 in all four runs; S8 pending | Consequences in Step 6 part 3 |
| 2026-10-17 | E0.6 | Main run after guard v2 | Guard reference 1.22°, 36.4% of state capped; mean A 21.6 t/ha/yr; classes 44.8 / 10.3 / 13.8 / 14.2 / 11.0 / 6.0% | Supersedes the guard-v1 main-run row |
| 2026-10-18 | E0.7 | S3 ISED: our K vs ISED by district | ρ 0.94; ours 0.57× theirs (median 0.0166 vs 0.0285) | Logged (V-10) |
| 2026-10-18 | E0.7 | S8 IWED: district mean A | Ours vs IWED ρ −0.46; ours-on-IRED ρ 0.07 (expectation met). Per factor: R 0.26, K 0.91, LS 0.75, C 0.90 | Explained by LS (next row) |
| 2026-10-18 | E0.7 | LS by true slope, ours vs IWED (median) | 0–0.5°: 0.11 vs 2.67; 2–5°: 0.46 vs 3.07; 15–30°: 26.6 vs 5.16; > 30°: 53.7 vs 5.57 | IWED LS barely follows slope |
| 2026-10-18 | E0.8 | Priority list, 702 catchments | Top 20: mean A 80–161 t/ha/yr, all hill or hill-edge units; 7 top under both rain maps; eye check 20/20 pass (steep 20, cleared visible 10) | Done ✔ |
| 2026-10-18 | E0.8 | District rank stability vs main | IRED ρ 0.74 (top 6 shared 4); tree C 0.003 ρ 0.75 (2); both ρ 0.00 (0) | Logged |
| 2026-10-19 | E0.9 | SoilSense module in the app | Screens 42/42 (headless); phone and tablet 12/12 after two fixes; desktop looked at; live forecast unchanged | Done ✔, not deployed |
| 2026-10-19 | V-14 | Catalogue dry run, region-aware | 11,072 files / 342 GB / 33 sources (shipped: 10,853 / 308 / 29) | Code fixed; not rebuilt |
| 2026-10-20 | V-12 | Survey of India outline swapped in | 7,842,412 in-state cells (78,424 km², −0.02%); 35 districts; fold hash unchanged a6bc908e791c9063; S1 8.3×, S7 7/20; top 20 the same units | Resolved |
| 2026-10-17 | — | R comparison re-run from the raw store (`compare_erosivity.py`) | Identical to the scratch run: Guwahati Singh −91% / IRED −46% / InRESatE −5%; district Spearman 0.26 (n = 27) | Reproducible ✔ |
| 2026-10-17 | — | R at points, IRED / InRESatE | Kokrajhar 21,083 / 8,750; Haflong 2,071 / 4,560; Diphu 3,084 / 3,123; Silchar 6,872 / 5,193; Dibrugarh 8,825 / 6,817 | — |
