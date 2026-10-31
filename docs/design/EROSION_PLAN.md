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
| **0 — Application proof** | 17 Oct → 7 Nov 2026 (closes 10 Nov) | A working, honest first erosion map of Assam, built by the same backbone with a region switch, in the app, and the application submitted | **9 / 11 done** (E0.1–E0.9); E0.10 application drafted and Proof of Work PDF built, not submitted; E0.11 partly done |
| 1 — Cover + validation | Nov → mid-Dec 2026, **started early** | Bare ground per season since 2019; first independent validation | **3 / 9 done** (E1.2, E1.5, E1.6), 2 in progress (E1.1 dry season done; E1.3 flags held back) |
| 2 — Prototype | mid-Dec 2026 → Demo Day, Feb 2027, **started early** | Weekly outlook, priority list with reasons, field kit, pilot protocol | **1 / 6 done** (E2.3), **2 in progress** (E2.1 outlook built, grading blocked; E2.4 exports done, form return not) |
| 3 — MVP | Feb → May 2027 | Department data in, field results in, calibrated; optional sensor pilot | 0 / 5 |

**What to add next, AI and otherwise, in priority order:** [ROADMAP_EROSION.md](ROADMAP_EROSION.md)
(2026-10-26), items AD-01 to AD-36. It also corrects "the soil part cannot be graded with
open data": CWC's daily river-mud readings for Assam run to 13 Oct 2026 and can grade the
outlook for any catchment that drains to a sediment station (AD-02).

**Where SoilSense stands on 2026-10-28, in one list** (details in the Build log, numbers in
the Results log):

| | State |
|---|---|
| Erosion map, all Assam, 100 m, six classes | ☑ Built; sanity checks S1–S8 run (S2, S7 failed, both handled) |
| Priority list, 703 catchments + 35 districts, cause + second reason + typical measures | ☑ Built (V-18 resolved); each rank's firmness measured over 1,000 runs (3 robust, 15 in half); re-rankable by the officer's own weights |
| Field kit: CSV, GeoJSON, KML, GeoPackage, 100 GPS points with form columns | ☑ Built (export side); the return form is not |
| Dry-season bare ground, every year 2019–2026 | ☑ Built and in the app ("Change over time") |
| "New bare ground on a steep slope" flags | ✕ **Held back** after two attempts: F1, F2 pass; H1 and E3 fail (attempt 2: 62.5% of flags confirmed, 75.8% of readable; bar 70% strict) |
| Weekly erosive-rain outlook ("This week") | ◐ Built and logged locally; **replayed over 44 monsoon weeks: good at when (G2 0.633, G3 0.765 pass), weak at where within a week (G1 0.181 fails)**; not in the 08:30 cloud run |
| Check against ISRO's land-degradation map | ☑ Run: X1–X3 **failed**; the national map points the wrong way; gap sits on tree land |
| Measured cover in the main map | ✕ Tested, **not adopted** (no gain on the held-out half) |
| Tree-class split (V-02) | ✕ Attempt 1 not adopted; still the top open question |
| Application answers, Proof of Work PDF | ◐ Drafted and built; team, pitch deck and URLs to settle; not submitted |
| Village card: search a place (or 'lat, lon'), one card, printable | ☑ Built (2,589 places; Assamese wording not done) |
| "What if we treat it?": soil saved per measure, per hectare, per unit | ☑ Built (AD-24; values provisional, V-32) |
| AI erosion map learned from ISRO's eroded-land map (AD-01) | ☑ Trained and tested: AUC 0.82 vs formula 0.66 on held-out blocks; catchment ρ 0.66 vs 0.36. **Blind picture check (AD-05, 2026-10-28): ties the formula (0.63 vs 0.62); its top band no richer in visible erosion.** Shown as a second opinion that follows ISRO's map, not a better map |
| Blind picture check of the formula (AD-05) | ☑ 300 pictures: severe classes show visible erosion 3.1× as often as mild ones (bar 2×, met but not firm: 8 eroded squares) |
| Gully-prone ground from terrain (AD-30) | ✕ Built, **not adopted**: no better than other open sloping land (0.83×) |
| Soil reaching streams (AD-25) | ☑ Built and **in the app** (2026-10-28): map view, list column and weight, district line; 7.8 of 116 Mt/yr; an estimate, untested |
| What the lost soil is worth (AD-29) | ☑ Built and **in the app** (2026-10-29): farmland loses about 35 kg N/ha/yr (1.7 urea bags, ₹61 crore/yr statewide at the farmer's price); tree land given only as a range |
| River-mud forecast, WHEN (AD-02, AD-06 ×2, river colour) | ✕ **Parked** after four tests failed; needs small-stream sensors, plots or CWC flow |
| On the public app | ☐ Not deployed (the user's call, held back on 2026-10-26) |

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
| ~~V-18~~ | ~~Reason line among hill units~~ | **RESOLVED 2026-10-25:** a second reason against units of similar steepness (five slope groups), with a multiple, plus typical measures. See the Build log, "V-18 part 2" | — | — | — | `erosion_priority.py` `table()` |
| V-19 | Arunachal erosion results not shown in the app | Computed (the debug run) but left out of the bundle; the state picker says so | 74% of forested Arunachal reads severe or worse with tree C 0.03 (D8): misleading without the tree-class split | V-02 upgraded (Sentinel-2 tree split), or the user asks to show it | `REGION=arunachal python scripts/run/export_erosion_bundle.py` (needs `erosion_priority.py` and `check_erosion_bars.py` for Arunachal first) | `webapp/products/erosion/view.py` `_region()` |
| V-20 | Home page subtitle | Still "Arunachal Pradesh" under SLOPESENSE, with an Assam module beside it | The home page mirrors the presenter's script and the deck; changing one alone puts them out of step | The user decides how the platform names its states | Change `app.py` landing title, `core/landing.py`, the script and the deck together | `webapp/app.py` |
| V-21 | Earth Engine has no asset storage | Results fetched by `computePixels` in 8 km tiles (1,417 tiles, about 2½ h for Assam) | Works, and resumes | A state-wide refresh is needed often (seasonal cover, E1.2+), or another state | Turn on asset storage for project `earthengine-507510` in the Google Cloud console (user's action); then one batch export per run | `fetch_43_tree_split_inputs.py` |
| V-22 | V3 measured-sediment test | **Not possible on the Assam-only map** (2 qualifying stations). 12–13 CWC stations with 20–48 years drain catchments ≥ 95% inside India, from the hills around Assam | — | The user decides to extend the map | A North-East region on the backbone (about 91.7–96.9° E, 22.9–27.7° N) covering those catchments; then rank catchments by measured concentration against modelled loss. No CWC discharge for Assam, so concentration, not loads | `reports/sediment_station_catchments.csv` |
| V-23 | Seasons watched | **Dry season only** (1 Feb – 30 Apr), 2019 → 2026 (2026-10-25) | It is when *jhum* ground is bare, just before the erosive monsoon rain, and the least cloudy season | The department asks for other seasons; or post-harvest bare cropland matters for the pilot | Add a post-monsoon (Oct–Dec) composite with the same rules | `fetch_48_dry_season_cover.py` |
| V-24 | Bare-pixel and flag thresholds | NDVI < 0.30 bare; flag at ≥ 0.25 bare after ≤ 0.10; slope ≥ 10° (2026-10-25, written before measuring). **2026-10-26: F1, F2 passed; H1 47.6% and E3 57.5% failed, so flags are held back** | The bare-ground layer itself is a measurement and ships | A second attempt passes its own new blind sample | Add a drop in the square's mean NDVI against its earlier seasons (diagnosis in part 2); a burn index (NBR) beside NDVI | `cover_change.py` |
| V-25 | Treatment hints | A fixed table, cause → typical measures (2026-10-25) | Standard practice in Indian soil conservation, and it is labelled as a hint | The department names its own works per situation, or an adviser reviews it | The department's own table; per land use (tea, *jhum*, cropland) | `erosion_priority.py` `HINTS` |
| V-26 | NRSC land degradation as a reference **and, from 2026-10-26, as training labels for the AI map (AD-01)** | 2015–16 1:50k map read from Bhuvan's map service, one class at a time (2026-10-25). Outputs are ours; NRSC's polygons are never shared | The only independent, state-wide, expert-drawn erosion map for Assam | NRSC shares the vector data, or a newer cycle appears | Use the vectors directly; add the 2005–06 cycle as a change reference | `fetch_49_nrsc_land_degradation.py`, `train_erosion_ai.py` |
| V-27 | Weekly outlook method | 0.2° Open-Meteo points (248), 7-day forecast; EI = a·P^b (InRESatE daily model) on both forecast and 2010–2025 history; this week's **share of a normal year** and **× normal for these days**; loss = share × the map's yearly A (2026-10-25) | Same-source comparison cancels Open-Meteo's wet bias exactly for a constant scale factor; same spacing and feed as the live products | The rain part is graded (E2.2) and disagrees; or a denser live refresh becomes affordable | Grade against IMERG (needs V-15); 0.1° points from a background refresh job | `erosion_outlook_base.py`, `products/erosion/outlook.py` |
| V-28 | Where the outlook is logged | Locally, by hand (`erosion_outlook_log.py`), into `records/erosion_outlook/assam/` | The first issue proves the chain and rebuilds exactly | The user agrees to redeploy the 08:30 cloud run | Add it as a step after the flood forecast in `scripts/cloud/modal_daily.py`, then redeploy | `scripts/model/erosion_outlook_log.py` |
| V-29 | Earth Engine access | Project `earthengine-507510` is in **"Restricted Mode"** (a concurrency cap seen 2026-10-25; on 2026-10-26 Earth Engine said why: **the project exceeded its noncommercial compute quota**) | Fetches still finish, with retries | Before any commercial use, or if fetches start failing | Check the project's registration and terms with Google; or build composites from Copernicus directly | `fetch_43`, `fetch_48` |
| V-30 | App bundle size | SoilSense adds 9.4 MB (the 8 dry-season maps are 4.9 MB) to the app's ~5 MB | Within free hosting limits | Hosting gets slow or tight | Ship fewer seasons, or coarser bare-ground maps | `export_erosion_bundle.py` `change_bundle` |
| V-31 | Places for the village card | 2,589 named places from OpenStreetMap + GeoNames + district HQs (2026-10-26) | Open, quick, and a typed position covers any spot | The department or ASSAC can share census village points; or the Assam State Geoportal opens | Census 2011 village points or boundaries; then rank by village and revenue circle | `erosion_places.py` |
| V-32 | Treatment values (AD-24) | Replant C 0.05 (≥ 15°), terrace P 0.15 (≥ 8°), contour P 0.5–0.9 by slope (W&S Table 13, 1.7–14°) (2026-10-26) | Standard, cited ranges; shown as estimates | The department names its own values per measure; or field plots in the pilot | The department's table; add unit costs for "per rupee" | `erosion_treatment.py` |
| V-33 | Blind picture check (AD-05) | One labeller (Claude), Esri 1 m mosaic of unknown dates, 300 squares of which 20 show erosion (2026-10-28) | Blind, pre-registered, and the only independent look at the ground before field visits | A second labeller is available; dated imagery (Earth Engine after 1 Nov, or Copernicus); or the pilot's field visits | Two labellers with an agreement figure; oversample open sloping land so more squares show erosion; replace with field results (E2.4) | `erosion_eyecheck.py` |
| V-34 | Soil value (AD-29) | SoilGrids topsoil N and organic carbon (0–30 cm), enrichment ratio 1, urea at ₹266.5 per 45 kg bag (the farmer's price, incl. taxes, as of 2026-10-29), P = 1 (untreated) | Open, statewide, cited; the farmland figure does not depend on V-02 | The department's soil survey (V-10); measured enrichment ratios for the North East; a price change; the treated-area records (V-05) | The department's soil N and C; enrichment 1.2–3 as a range; P from treated areas; add P and K once a source exists | `erosion_soil_value.py` |
| V-17 | Priority ranking robustness (**part 2, 2026-10-26: 1,000 runs across the unsettled inputs; 3 robust, 15 in half; shown as 'top 20 in X% of runs'**) | Rank under 2 R maps × 2 tree C. **S7 failed (2026-10-17):** 7 of the top 20 are shared between rain maps (ρ 0.82 over all units), 0 in all four runs. **E0.8 (2026-10-18):** the cleared hill catchments #1, #8, #13, #16 hold under tree C 0.003; the 7 rain-robust ones are forested hills. So: mark "top under both rain maps" / "depends on the rain source" and show each unit's rank under each run | Neither lever can be settled with open data now | More R anchors (V-01) or the tree-class split (V-02) | Re-run S7; the marks shrink as the levers are pinned down | E0.8; `check_erosion_bars.py` S7 |

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

### 2026-10-25 · Phase 1, E1.1–E1.3 part 1: bare ground every dry season and "new bare ground on a steep slope", written before measuring

**Why now.** The department's statement asks for "periodic monitoring" with "temporal
comparison". Until today all of it was "planned". This entry fixes, before any Sentinel-2
number exists, how SoilSense measures bare ground each dry season since 2019, how it flags
new bare ground on steep slopes, and how the flags are tested for false alarms **before**
any is shown (E1.2's rule).

**Why the dry season, and only the dry season (for now).** In Assam's hills, *jhum* plots
are slashed in December–February and burned in March–April. The ground then stays bare
until the crop grows after the monsoon starts. The heavy, erosive rain of May–September
falls on whatever the dry season left bare. So the dry-season picture is the one that
matters most for erosion, and it is also the least cloudy part of the year. A post-monsoon
picture is a later addition (register V-23).

**What Earth Engine computes, per year Y = 2019 … 2026, per 100 m cell** (script
`scripts/fetch/fetch_48_dry_season_cover.py`):

| Piece | Rule |
|---|---|
| Images | Sentinel-2 L2A (`COPERNICUS/S2_SR_HARMONIZED`), **1 Feb – 30 Apr of Y** |
| Cloud | Google Cloud Score+ (`GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`), keep a 10 m pixel when `cs_cdf` ≥ 0.60 (Google's suggested value) |
| Per 10 m pixel | Number of clear looks; the **median NDVI** of the clear looks |
| A usable pixel | ≥ 3 clear looks and median NDVI ≥ 0 (below 0 is open water) |
| **Bare pixel** | Usable, with median NDVI < **0.30**: bare soil, burnt ground, slashed and dried vegetation |
| `valid_Y` | Share of the cell's 10 m pixels that are usable |
| `bare_Y` | Share of the usable pixels that are bare |

Plus, from Hansen Global Forest Change v1.13 at 30 m, only for testing (never as an input to
the detector): mean tree cover in 2000, share of the cell lost in each year 2018–2025, and
share lost at any time 2001–2025.

**A cell-year is "evaluable"** when `valid_Y` ≥ 0.50. Otherwise it is shown as "too cloudy
that season" and never counted as bare or as unchanged.

**The flag, "new bare ground on a steep slope", in year Y (2020 … 2026).** All must hold:

1. the cell is scored by the erosion recipe (`erosion_assessed`);
2. its mean slope is **≥ 10°** (`terrain_slope_deg`, the unguarded slope; at 10° the canopy
   slope trap of V-06, under 3°, cannot reach it);
3. year Y is evaluable and `bare_Y` ≥ **0.25** (a quarter hectare or more of the square);
4. of the two years before (Y−1, Y−2), at least one is evaluable, and **every evaluable one**
   has `bare` ≤ **0.10** (the square was green before).

So 2019 can never be flagged (no year before it), and 2020 is judged against 2019 alone.

**Pass bars (written now, before any Sentinel-2 or Hansen cell is measured):**

| # | Check | On which cells | Pass bar |
|---|---|---|---|
| **F1** | False flags on stable forest | WorldCover tree, scored, slope ≥ 10°, Hansen tree cover 2000 ≥ 75%, and **no** Hansen loss in the cell in 2001–2025. Every evaluable cell-year 2020–2026 | Flagged ≤ **1.0%** of cell-years |
| **F2** | False flags from tea pruning | Cells inside an OSM tea outline whose 8 neighbours are also inside one (739 outlines, `fetch_45`), scored. The flag rule **without** the slope condition, so flat tea counts too | Flagged ≤ **3.0%** of cell-years |
| **H1** | Does it catch real clearing? | Scored, slope ≥ 10°, Hansen loss in year L (2020–2025) on ≥ 50% of the cell, and none in L−1 or L−2 | Flagged in L or L+1 for ≥ **50%** of the cells that are evaluable in L or L+1 |
| **E3** | Blind eye check on **dated** imagery | 40 random flags and 40 random unflagged evaluable cell-years on slopes ≥ 10° (the same years), shuffled, neutral ids. Each is shown as a pair of Sentinel-2 true-colour pictures (dry season Y−1 and Y, 1.5 km window, the square outlined) and labelled *new bare or burnt patch: yes / no / can't tell* before the key is opened | Flags: ≥ **70%** "yes"; unflagged: ≤ **10%** "yes". "Can't tell" counts against the flags (strict); the share among readable pictures is reported beside it |

**Clarification, added the same day while the inputs downloaded, before any number or picture
existed:** for the *unflagged* pictures, E3's share is "yes" among the readable pictures. A
"can't tell" there is evidence neither way, and the strict reading belongs to the flags,
which are the claims. Both shares are reported for both sets.

E3 uses the same satellite as the detector, so it checks the rule against what an eye sees,
not against an independent sensor. F1, F2 and H1 use Hansen and OSM, which the detector never
sees. Hansen misses some clearing and calls some forest loss that is not bare ground, so F1
and H1 are measured against an imperfect reference, said plainly.

**What ships, by rule:**

- **The bare-ground layer** (`bare_Y` and `valid_Y` per dry season) is a measurement, not a
  claim. It is shown in the app whatever the bars say, labelled "measured from satellite",
  with its cloudy gaps.
- **The flags** are shown only if **F1, F2 and E3 pass**. If H1 fails while those pass, the
  flags ship and the screen states the measured catch rate instead of implying they catch
  most clearing.
- **A failure means investigate, not tweak.** A second attempt needs a new dated entry and,
  for E3, new pictures.

**The cover refreshed each dry season (a monitoring run; it does not replace the main map).**
On WorldCover tree, shrub and grass cells, a square that is bare in the dry season is treated
as cleared that year, with the cleared-*jhum* value used for T1 (0.34, IWED):

  C_Y = C_class + `bare_Y` × max(0, 0.34 − C_class)

Cropland (0.34) and bare land (0.45) keep their class value; cells that are not evaluable
keep C_class. Then A_Y = R × K × LS × C_Y × P, with everything else exactly as the main run.
Per catchment and district this gives each year's loss, the change since the year before and
since 2019, and the hectares newly bare on steep slopes. Reported, no bar: it reads the change
in cover, not a measured change in soil loss, and the screen says so.

### 2026-10-25 · V-18 part 1: a second reason, against similar slopes, and a treatment hint — written before computing

**The problem (Step 7 part 2, finding 3):** against the state average, every top-20
catchment's main cause is "steep or long slopes". That is true, but it does not say what
sets one hill catchment apart from the next, and that is what decides the treatment.

**The rule, fixed before it is computed:**

| Piece | Rule |
|---|---|
| Peer group | The units (catchments, and separately districts) are cut into **five equal groups by their slope term** (`dlog_LS`, the unit's mean log LS minus the state's). A unit's peers are the units in its group |
| Second reason | For rain, soil and cover (R, K, C), the unit's `dlog` minus the mean `dlog` of its peers. The largest positive one is the second reason, **if it is above 0.10** in log units (about +10%). Otherwise "nothing stands out against similar slopes" |
| Shown as | "Against catchments of similar steepness: *bare or thin cover*, 2.1× their average", where the multiple is exp(difference) |
| Treatment hint | From the main cause and the second reason, from a fixed table: slopes → contour bunds or trenches, terraces, check dams; cover → revegetation, agroforestry, longer *jhum* fallows; rain → ground cover before the monsoon, check dams, gully plugs; soil → mulch, cover crops, grass strips. Labelled "typical measures, to confirm with the department" |
| What it does not change | The ranking, the score and the robustness marks. This is a reading aid |

Register V-18 is resolved by this entry once it runs; the hint table becomes a new
provisional choice (V-25).

**Clarification, the same day, after the first run and before anything was shown:** the cover
hint read "longer *jhum* fallows" on plains catchments, where *jhum* is not practised. On
units in slope groups 1–3 the cover hint is now "cover crops, crop residue left on the field,
grass strips". The ranking and both reasons are unchanged.

### 2026-10-25 · Phase 1, E1.5 (V2) part 1: agreement with ISRO's land-degradation map — the test, written before measuring

**The reference.** NRSC's **Land Degradation 1:50,000, 2015–16** for Assam (Bhuvan layer
`ld:AS_LD50K_1516`). NRSC drew it by eye from satellite imagery. It marks water erosion in
seven classes: sheet erosion slight / moderate / severe, rills, gullies, shallow and deep
ravines; plus "normal" land and other kinds of degradation. It never saw our recipe, and we
never use it to tune the recipe. It is used **for comparison only and never redistributed**.
Fetched by `scripts/fetch/fetch_49_nrsc_land_degradation.py` onto our grid. Only the class
areas were printed before this entry was written; no agreement was computed.

**What it is not.** It is not ground truth. Each polygon carries one dominant process, so
eroding land that NRSC labelled acidic or something else counts as "other", not as erosion.
It is one survey (2015–16), at 1:50,000, from 23.5 m imagery.

**The test, fixed now:**

| # | Check | Cells or units | Pass bar |
|---|---|---|---|
| **X1** | Does our estimated loss separate NRSC's eroded land from its normal land? | Scored cells NRSC maps as **eroded** (sheet erosion moderate or severe, rills, gullies, ravines: codes 2–7) against those it maps **normal** (code 8). Slight sheet erosion (1) and other degradation (9) left out. AUC of our A (main run) | **≥ 0.70** |
| **X2** | Do our catchments rank like NRSC's water-erosion share? | The 703 ranked catchments. Spearman ρ between our mean A and the share of the catchment's scored, NRSC-mapped cells in **any** water-erosion class (1–7) | **≥ 0.40** |
| **X3** | The same for districts | The 35 districts | **≥ 0.50** |

**Reported beside them, no bar:** the same three numbers for (a) the IIT Delhi national map
(IWED), (b) our IRED run, (c) our tree C 0.003 run, and (d) **slope alone** (mean slope). The
last says whether the recipe adds anything to steepness. If slope alone agrees with NRSC
better than the recipe, that is reported as found.

**If a bar fails:** investigate and report. The recipe is not changed to fit NRSC's map.

### 2026-10-25 · Phase 1, E1.5 (V2) part 2: results — all three bars FAIL; the national map points the wrong way; the miss is on tree land

`scripts/inspect/compare_nrsc_ld.py` → `reports/nrsc_ld_comparison_assam.json`. Run exactly as
written in part 1.

**The reference on our scored land:** sheet erosion slight 744 km², moderate 2,689, severe
602, rills 11, gullies 1; normal 49,288; other degradation 948. NRSC marks only about 7% of
scored Assam as water-eroded. 5.40 M of 5.45 M scored cells were compared.

| | Ours (main) | Ours, IRED | Ours, tree C 0.003 | **Slope alone** | **IWED (national map)** | Bar |
|---|---|---|---|---|---|---|
| X1 AUC, eroded vs normal cells | **0.661** | 0.643 | 0.581 | 0.651 | **0.419** | ≥ 0.70 ✕ |
| X2 ρ, 703 catchments | **0.36** | 0.32 | 0.02 | 0.44 | **−0.30** | ≥ 0.40 ✕ |
| X3 ρ, 35 districts | **0.13** | 0.22 | −0.17 | 0.36 | **−0.36** | ≥ 0.50 ✕ |

**What it says, read honestly:**

1. **All three bars fail.** Our map agrees with NRSC's in the right direction, but not as
   strongly as we required.
2. **The national 250 m map (IWED) disagrees with NRSC in every test**: worse than chance at
   cell level, negative at catchment and district level. That follows from its flat slope
   factor (Step 6 part 4): it rates the plains highest, and NRSC's erosion is in the hills.
3. **Slope alone agrees with NRSC about as well as the whole recipe, or better.** So, measured
   against NRSC, rain strength and cover add nothing yet. Rain is the least certain factor
   (V-01, S7), and cover is one value for all tree land (V-02).
4. **Where the miss is (diagnosis, found after the result, not a test):**
   - **79% of NRSC's eroded land is WorldCover "tree".** On steep tree land (≥ 15°), our median
     loss is **54.5** t/ha/yr where NRSC marks erosion and **60.5** where it marks normal. Our map
     cannot separate them, because every tree cell gets C = 0.03. This is V-02 again, now
     measured against an independent map.
   - **District disagreements fall into two groups.** Forested hills we rank high and NRSC
     calls mostly normal: Cachar (ours 4th, NRSC 20th), Kamrup Metro (1st vs 12th), Hailakandi
     (5th vs 10th). And the north-bank foothills NRSC marks as eroding where our gentle slopes
     and tree cover score low: Biswanath (32nd vs 2nd), Sonitpur (34th vs 4th), Chirang
     (25th vs 6th), Golaghat (32nd vs 8th).
   - The tree C 0.003 run does worse (X2 0.02), so lowering cover on all tree land is not
     the answer either. The answer has to tell *which* tree land is bare or degraded.

**What follows (not done yet; needs its own written test first):** the dry-season bare share
(E1.1–E1.3, downloading) measures exactly that. Once it exists, the question becomes "does
each year's measured cover separate NRSC's eroded tree land from its normal tree land, and does
a recipe using it agree better with NRSC on land it was not checked on?" That must be
pre-registered on the frozen spatial folds (decide on half the blocks, judge on the other
half), so NRSC is never both the tuning target and the judge.

**For the application:** report the failure and the comparison together. Against ISRO's own
map, ours points the right way where the national map points the wrong way, and the remaining
gap sits exactly where we already said the map is weakest (cover on tree land), with the fix
in the plan.

### 2026-10-25 · Phase 1, E1.5 part 3: measured cover in the main map? — the test, written before the dry-season data exists

Written while `fetch_48_dry_season_cover.py` was still downloading; no bare-ground value had
been read. It follows from part 2: NRSC's erosion sits mostly on tree land, and one cover value
for all tree land cannot separate it.

**Candidates.** b̄ = a cell's mean dry-season bare share over its evaluable seasons, 2019–2026.
On WorldCover tree, shrub and grass cells with at least one evaluable season (others keep their
class value; cropland and bare land unchanged):

| | Cover value | Idea |
|---|---|---|
| **M1** | C_class + b̄ × max(0, 0.34 − C_class) | The monitoring formula, averaged over the years |
| **M2** | C_low + b̄ × (0.34 − C_low), C_low = 0.003 on tree, C_class on shrub and grass | The bare part is measured, so the rest of the tree land is treated as closed canopy |

**Two halves, so NRSC is never both target and judge.** The frozen spatial folds (hash
`a6bc908e791c9063`): **calibration = folds 0 and 1** (46.5% of cells), **test = folds 2, 3
and 4** (53.5%).

1. **On the calibration half:** X1 (AUC, NRSC eroded vs normal) for the main run, M1 and M2.
   The better candidate goes forward only if it beats the main run by **≥ 0.02** there.
2. **On the test half, judged once.** It is adopted as the main run only if **all** hold:
   - X1 beats the main run by **≥ 0.02** on the test half;
   - X2 (ρ over catchments with most of their cells in the test half) is **not lower** than the
     main run's there;
   - S1 still passes state-wide (hills ≥ 3× the plains).
3. **Reported, no bar:** X1–X3 state-wide for every candidate; inside tree land, the AUC of b̄
   alone; the same candidates with b̄ from 2019–2021 only (nearest to NRSC's 2015–16).

**If adopted:** the main run's C becomes the measured cover; the 0.03 class average becomes a
comparison run; S1–S8, the priority list, the field kit and the app are re-run; V-02 and V-16
are updated. **If not:** reported, nothing changes, and V-02 stays open.

### 2026-10-25 · Phase 2 brought forward, E2.1 part 1: the weekly erosive-rain outlook — method, written before building

**What it answers.** "Where will this week's rain wash the most soil?" A ranked list of
catchments and a map, refreshed from the live 7-day rain forecast. It makes SoilSense a
forecast, like SlideSense and FloodSense, and it reuses their live rain feed (Open-Meteo,
`core/rainfall.py`).

**The trap it must avoid** (`core/rainfall.py`, measured on Arunachal): Open-Meteo's rain runs
**1.68× wetter** than IMERG, the satellite rain InRESatE's daily erosivity model was fitted on,
and correlates with it at only 0.32 a day. Feeding forecast millimetres straight into
EI = a·P^b would overstate erosivity, more so for heavy days (b > 1). **Rule, as for the other
products: compare the forecast with the same source's own history at the same place.**

| Piece | Rule |
|---|---|
| Points | A 0.2° lattice (about 22 km) wherever a 0.2° box around the point holds in-state Assam cells. The same spacing as the live Arunachal products, so the live refresh stays small |
| History | Open-Meteo archive, daily rain, 2010 → yesterday, at those points (`fetch_50_erosion_rain_history.py`). The archive and the forecast API are one source chain (measured: ratio 1.00) |
| Daily erosivity | EI_day = a·P^b, with a and b from InRESatE's daily model at the point's 0.1° cell, applied to Open-Meteo rain on **both** sides (history and forecast) |
| **Share of the year** | s = Σ EI_day over the next 7 days ÷ the point's mean yearly Σ EI_day in the history. A dimensionless number: the source's wetness cancels to first order |
| **× normal for the season** | s ÷ the point's mean 7-day share for the same days of the year (±7 days, all history years) |
| **This week's loss** | Each scored cell takes its nearest point's s. A_week = s × A (the main run's yearly loss). Per catchment and district: the mean over scored cells |
| Kind of number | **Outlook**: approximate, built on a forecast. The rain part can be graded later against satellite rain (E2.2); the soil-loss part cannot be graded with open data |
| Logged | Each issued outlook is written down with its date before the week happens (`records/erosion_outlook/`), so it can be graded later |

**What it does not claim.** It does not measure soil moved this week. It ranks where this week's
forecast rain, set against each place's normal, meets the most erodible ground.

### 2026-10-26 · Phase 1, E1.1–E1.3 part 2: bare ground 2019–2026 is in; F1 and F2 pass, H1 fails narrowly

**Inputs.** `fetch_48_dry_season_cover.py`: 934 tiles over about 3½ hours of fetching, across
two sessions. Three things slowed it, none affecting the values:

- Earth Engine put the project in **"Restricted Mode"** (a concurrency cap), so some requests
  were refused and retried;
- about 40 tiles ran out of Earth Engine memory and were fetched in quarters, one of them (far
  west, r2100 c400) in sixteenths;
- the internet dropped for about an hour.

Every piece covers the same cells and gives the same values.
`dry_season_cover_assam.tif` (34 bands, 142 MB). `cover_change.py` run exactly as written in
part 1 (`logs/assam_cover_change.log`, `reports/cover_change_assam.json`).

**Clouds are not a problem in the dry season:** 99.6–100% of scored land, and 99.9–100% of
steep scored land, is evaluable in every year 2019–2026.

| # | Check | Result | Bar |
|---|---|---|---|
| F1 | False flags on stable forest (500,420 cells, 3.50 M cell-years) | **0.05%** (1,779 cell-years) | ≤ 1.0% ✔ |
| F2 | False flags in tea-garden interiors, no slope condition (75,526 cells) | **1.79%** (on steep tea alone: 0.29%) | ≤ 3.0% ✔ |
| H1 | Hansen clearing caught in L or L+1 (33,109 cell-events, 2020–2025) | **47.6%** (by year 41–54%) | ≥ 50% ✕ |
| E3 | Blind check on dated pictures | pending | flags ≥ 70%, unflagged ≤ 10% |

**What the years show (steep scored land, share bare in the dry season):** 2019 1.25%, 2020
1.51, 2021 1.86, 2022 1.03, 2023 1.43, 2024 1.61, **2025 1.94** (the highest), 2026 1.39.
Flags (new bare ground on slopes ≥ 10°): 6,000–16,000 hectares a year. Mean loss with each
year's cover: 23.4–24.9 t/ha/yr, against 21.6 for the class lookup.

**By the rule written in part 1:** H1 failing does not hold the flags back, but if E3 passes
the screen must state the measured catch rate ("catches about half of the clearing that
global forest-loss maps record") instead of implying it catches most. The flags are shown
only if E3 passes.

**E3, scored 2026-10-26** (80 pictures labelled blind, `eyecheck_change/labels.csv`, key opened
after): **FAIL.**

| | n | yes | no | can't tell | Share "yes" | Bar |
|---|---|---|---|---|---|---|
| Flagged | 40 | 23 | 10 | 7 | **57.5%** (69.7% of readable) | ≥ 70% ✕ |
| Unflagged | 40 | 1 | 37 | 2 | **2.6%** of readable | ≤ 10% ✔ |

**So the flags are not shown.** The bare-ground layer is (it is a measurement, not a claim). A
flagged square is about 20× as likely as an unflagged one to show fresh clearing, but not
reliably enough for the bar.

**Why (diagnosis after the key was opened, not a test):** the confirmed flags were dense green
squares that turned bare (mean NDVI of the earlier seasons 0.5–0.8, then a drop of 0.2–0.5).
Most misses were squares that were already sparse or brown in the dry season (earlier NDVI
0.4–0.5) and tipped just under 0.30 in a dry year (2025 is the barest year). The rule asks
"is it bare now?", not "did it lose its cover?".

**A second attempt** would add a drop in the square's mean NDVI against its earlier seasons, and
must be written down first and judged on a **new** blind sample that excludes all 80 of these
pictures. Not started.

### 2026-10-26 · Phase 1, E1.5 part 3, results: measured cover NOT adopted, and the diagnosis was wrong

`scripts/inspect/measured_cover_test.py` → `reports/measured_cover_assam.json`, run as written.

| | X1 calibration half | X1 test half | X2 test half | X3 all | S1 |
|---|---|---|---|---|---|
| Main (class lookup) | **0.700** | **0.629** | **0.357** | 0.130 | 8.3× |
| M1 (bare share added to class value) | 0.697 | 0.626 | 0.345 | 0.146 | 6.1× |
| M2 (non-bare tree land as closed canopy) | 0.619 | 0.558 | 0.092 | −0.048 | 1.2× |

**Nothing goes forward:** neither candidate beats the main run on the calibration half, so the
test half was only reported. The 2019–2021-only variants behave the same.

**The finding:** inside tree land, NRSC's eroded cells are *not* barer in the dry season. Their
mean bare share separates them from NRSC's normal tree land at **AUC 0.451**, slightly the
wrong way. So the part 2 guess, that NRSC's tree-land erosion is ground our cover value misses
because it is bare, is **not supported**. Whatever NRSC marked there in 2015–16 (degraded
forest, regrowing *jhum* fallow, erosion under canopy) is not visible as bare ground in
2019–2026 dry seasons. The cover question on tree land (V-02) stays open, and the main map
is unchanged.

### 2026-10-25 · V-18 part 2: the second reason and treatment hints — results (and the field kit)

`erosion_priority.py` re-run (log `logs/assam_erosion_priority_v18.log`). **Ranks, scores, causes
and marks are unchanged** for all 703 catchments; only three columns were added
(`vs_similar`, `vs_similar_x`, `hint`, plus `slope_group`).

- **Top 20:** against catchments of similar steepness, 17 stand out for **heavy rain**, up to
  2.5× their group's average (the south Kamrup hills along Meghalaya), 1 for **bare or thin
  cover** (West Karbi Anglong, 1.5×), and 2 for nothing.
- **All 703:** heavy rain 270, bare or thin cover 173, nothing stands out 260.
- This fits S7: the rain map is exactly what lifts the catchments marked "depends on the rain
  source".
- One clarification before showing: the cover hint said "longer *jhum* fallows" on plains, so
  gentle units (slope groups 1–3) now get "cover crops, crop residue left on the field, grass
  strips".

**Field kit, first version** (`export_erosion_bundle.py`):

- **Points:** in each top-20 catchment, the 5 scored squares with the highest estimated loss,
  each at least 500 m from those already picked; 100 points in all.
- **Files:** a CSV with empty columns for what the team finds (visit date, observer, rills,
  gullies, bare-soil %, fresh clearing, existing works, photo ids, notes); a GPX for GPS units
  and a KML for phones, both made in the app; and one GeoPackage holding catchments, districts
  and points (EPSG:4326). KML and GPX were checked to parse.
- **On screen:** single-square tonnes are the least certain number, so the field table shows
  the class; the CSV keeps the estimate.
- **Not built:** reading filled-in forms back (E2.4's round trip).

### 2026-10-26 · Phase 2 brought forward, E2.1 part 2: the weekly outlook is built and the first issue logged

**Rain history:**

- `fetch_50_erosion_rain_history.py`: 248 points (0.2°), Open-Meteo archive 2010-01-01 →
  2026-10-25, 50 calls.
- The archive's hourly limit stopped it twice, and an hour-long internet drop hit; each batch
  is cached, so it resumed.

**Fixed inputs** (`erosion_outlook_base.py` → `webapp/assets/erosion/assam/outlook_base.npz`,
0.5 MB):

- Daily model parameters, medians: a 0.055, b 1.94. With b near 2, a constant wet bias cancels
  exactly in the share.
- Mean yearly EI on Open-Meteo rain, median 4,315.
- A typical June–August week carries **4.2%** of a year's erosive rain; an average week 1.9%.
- Every scored cell is mapped to its nearest point, giving a 703-catchment and a 35-district
  matrix.

**Before the real data**, a dry run on made-up rain checked the plumbing: shapes, all 703
catchments filled, the map pixels.

**First issue** (`erosion_outlook_log.py`, 2026-10-26, week 26 Oct – 1 Nov):

- **0.11× normal** for these days; **0.10%** of a year's erosive rain; 0.021 t/ha on average
  over scored land.
- Most at risk: the Barak valley (Hailakandi, Sribhumi, Cachar).
- A dry post-monsoon week, as expected.
- `check`: the issue rebuilds exactly from its own file.

**App:**

- A "This week" page:
  - the map colours scored land by × normal at its rain point;
  - the 10 catchments with the most soil at risk are outlined;
  - the day-by-day bars, the top 8 catchments and a district table.
- New badges: Outlook and Input.
- A paragraph on the method page.
- Live rain comes through the shared, hourly-cached `core.rainfall.load_forecast` (7 calls of
  40 points).

**Checks:** all 12 SoilSense screen cases pass (`check_app_screens.py`, now with "This week"
and "Change over time"); `check_live_unchanged.py check`: PASS.

**Open:**

- It is not in the 08:30 cloud run (V-28).
- The rain part is not graded yet (E2.2 needs Assam IMERG, V-15).
- The soil part cannot be graded with open data.

### 2026-10-26 · Phase 1, E1.3 attempt 2: change flags with a greenness drop — written before measuring

**Why a second attempt.** Attempt 1 (part 2) failed E3: half its misses were squares that were
already sparse in the dry season and tipped under NDVI 0.30 in a dry year. Its rule asked "is it
bare now?"; the question is "did it lose its cover?". The new condition below was suggested by
looking at attempt 1's 80 pictures after their key was opened, so **those pictures can never
judge it**: attempt 2 is judged on a new sample.

**The rule (attempt 2) = attempt 1's four conditions, plus one:**

5. the square's mean NDVI in Y (`ndvi_Y`) is at least **0.20 below** the highest `ndvi` of
   its evaluable seasons among Y−1 and Y−2.

Nothing else changes: the same 10° slope, 0.25 bare share, ≤ 0.10 before, the same evaluable
rule.

**Tests: the same four bars as attempt 1.**

| # | Bar |
|---|---|
| F1 | ≤ 1.0% of stable-forest cell-years |
| F2 | ≤ 3.0% of tea-interior cell-years |
| H1 | ≥ 50% of Hansen clearing caught (expected to fall, since the rule is stricter: reported either way) |
| E3 | flags ≥ 70% "yes" (strict); unflagged ≤ 10% "yes" (readable) |

E3 uses a **new** blind sample: 40 attempt-2 flags and 40 unflagged evaluable steep cell-years,
**seed 43**, excluding every cell in attempt 1's 80 pictures, labelled before the new key is
opened.

**Ship rule, unchanged:** the flags are shown only if F1, F2 and E3 pass; if H1 fails, the
screen states the measured catch rate. If attempt 2 fails E3 too, the flags stay held back
and no third rule is tried before the application.

Outputs carry the suffix `_v2` (`cover_flags_v2.tif`, `reports/cover_change_assam_v2.json`,
`eyecheck_change_v2/`); attempt 1's files are kept as they are.

### 2026-10-26 · Phase 1, E1.3 attempt 2: results — closer, still FAILS E3; flags stay held back

`cover_change.py --v2` (log `logs/assam_cover_change_v2.log`, `reports/cover_change_assam_v2.json`),
run exactly as written in "E1.3 attempt 2". New blind sample (seed 43, attempt 1's 80 cells
excluded), labelled before the key was opened (`eyecheck_change_v2/labels.csv`).

| # | Attempt 1 | **Attempt 2** | Bar |
|---|---|---|---|
| F1 stable forest | 0.05% | **0.03%** | ≤ 1.0% ✔ |
| F2 tea interiors | 1.79% | **0.90%** | ≤ 3.0% ✔ |
| H1 Hansen clearing caught | 47.6% | **44.4%** | ≥ 50% ✕ |
| E3 flags "yes" (strict / readable) | 57.5% / 69.7% | **62.5% / 75.8%** (25 yes, 8 no, 7 can't tell) | ≥ 70% strict ✕ |
| E3 unflagged "yes" (readable) | 2.6% | **2.8%** | ≤ 10% ✔ |

Flags per year roughly halved: 4,062–10,069 ha (attempt 1: 6,032–16,238).

**By the rule written beforehand, the flags stay held back, and no third rule is tried before
the application.** The greenness-drop condition did what the diagnosis said: fewer false
alarms, and more of the flags confirmed. It falls short only because of the "can't tell"
pictures (haze, already-patchy ground), which the strict reading counts against it.

**What would settle it after the application:** sharper dated imagery for the pictures
(Sentinel-2 at 10 m is near the limit for a 100 m square); or the department's field visits to
a sample of flags; or a stricter "can't tell" protocol written down before a third sample.
The app now shows attempt 2's tests, with a note on attempt 1.

### 2026-10-26 · E2.2 part 1: replaying the weekly outlook over three monsoons — the test, written before fetching

**Question.** Had the "This week" page existed in 2023–2025, would it have pointed at the right
weeks and the right places? The rain part can be graded against what fell. The soil part
cannot; this tests the rain part only.

**The forecasts, as issued.** Open-Meteo's previous-runs service keeps what the forecast said
1–7 days ahead for past dates (hourly `precipitation_previous_dayK`, checked back to July 2023).

- **Issue days:** every Monday from **1 May to 30 September, 2023, 2024 and 2025**: about 66
  non-overlapping weeks.
- **The week's forecast:** day D+k is read at lead k, `precipitation` for k = 0 and
  `precipitation_previous_day{k}` for k = 1…6. Hourly values are summed into UTC days, the
  app's day boundary.
- **Points:** every other point of the outlook's 0.2° lattice in a checkerboard, so 124 of
  the 248 (about 31 km apart). This keeps the fetch inside Open-Meteo's free limits.

**What the replay computes:** exactly what the app does (`products/erosion/outlook.compute`):
the share of a normal year's erosive rain, and × normal for those days.

**The truth: GPM IMERG daily rain** (NASA, satellite; `fetch_11b`, Assam, 2001–2025). It is
independent of the forecast.

- At each point: the mean of the IMERG cells within ±0.1°.
- Observed EI = a·P^b with the same a and b.
- Observed share = the week's EI ÷ the point's mean yearly EI on IMERG (2001–2025).
- Observed × normal uses IMERG's own seasonal normal, built the same way as the app's.

**The baseline to beat:** climatology. "Forecast" each week as its normal share, so × normal = 1
everywhere. An outlook that cannot beat the normal is not worth showing.

**Pass bars (written now):**

| # | Check | Pass bar |
|---|---|---|
| **G1 places** | For each issue week, Spearman ρ across the 124 points between forecast share and observed share; the **median over weeks** | **≥ 0.30** and higher than climatology's median ρ |
| **G2 weeks** | Across the issue weeks, Spearman ρ between the state's forecast share and its observed share | **≥ 0.60** and higher than climatology's ρ |
| **G3 heavy weeks** | Over point-weeks, AUC of forecast × normal for "observed ≥ 2× normal" (average ranks, so ties count half) | **≥ 0.70** (climatology gives 0.50 by construction) |

**Reported, no bar:**

- the median ratio of forecast share to observed share (does the share method cancel the
  wetness bias?);
- the same three numbers for each year;
- catchment-level ρ (forecast vs observed weekly loss) for each week.

**What follows.** The results go into the app's method page and the application answer, pass or
fail. If G1–G3 pass, the "This week" page says so in one line. If they fail, it says that
too, and the outlook stays labelled "not graded" in spirit.

**Two clarifications, added the same day before any IMERG or forecast value was read:**

1. **IMERG history 2013–2025, not 2001–2025.** NASA's server delivered about 9 days a minute,
   so 25 years would take some 17 hours. "Observed share" and "observed × normal" use IMERG's
   mean year and seasonal normal over 2013–2025 (13 years). The grade is computed **once**,
   after those 13 years are in, and not on any partial download.
2. **125 points, not 124.** The checkerboard of the 248-point lattice gives 125.
3. **2024 and 2025 only.** The archive holds forecasts 1–6 days ahead from May 2024 onward;
   for 2023 only the same-day value exists (checked by counting missing values, before any
   grading). So the replay covers the 2024 and 2025 monsoons, about 44 weeks.
4. **IMERG from Earth Engine (added 2026-10-26, before any IMERG value was read).** From about
   13:05 that day, NASA's OPeNDAP data server (`gpm1.gesdisc.eosdis.nasa.gov`) refused
   connections from our address. The website and the login still answered, so it was most
   likely a block after the day's burst of requests. The truth is therefore **GPM IMERG V07
   Final** (half-hourly, Earth Engine `NASA/GPM_L3/IMERG_V07`), summed to UTC days: the same
   0.1° cells, the mean over a 0.2° box round each point, 2013–2025. "Final" is the
   gauge-adjusted run, a stronger truth than the Late run `fetch_11b` reads. The marks and
   everything else are unchanged.

### 2026-10-26 · V-17 part 2: how firm is each rank? Many runs across the unsettled inputs — ranges written before running

**Why.** Today the list marks a top-20 catchment "firm" if it is also top 20 under the other
rain map. That is a yes/no about one input. The department needs a measured answer: across
everything we are unsure of, how often is this catchment in the top 20?

**The runs:** 1,000 draws, seed 42, each recomputing every scored cell's A and every unit's
mean. Per draw:

| Input | How it varies | Why this range |
|---|---|---|
| Rain strength R | R = R_InRESatE^(1−w) × R_IRED^w, **w uniform 0–1** (a blend in log space) | The two national maps; neither is settled (V-01, S7) |
| C on tree land | **log-uniform 0.003 – 0.1**, one value per draw | Closed forest (Wischmeier & Smith) to a tree class rich in tea and *jhum* (V-02; the attempt-1 split averaged 0.10) |
| C on shrub, grass, cropland | each × **log-uniform ½ – 1½**, independently | IWED's class values, ±50% |
| Steepness S | **McCool or Nearing**, 50/50 | Both are defensible on steep ground (V-09) |
| K, P | not varied | A uniform scale cannot change ranks; K's pattern matches ISED (ρ 0.94); P is 1 everywhere |

**Reported per catchment and district (no bar):**

- the share of runs in the top 20, and in the top 50;
- the median rank, with the 5th–95th percentile range.

**The display rule, fixed now.** The priority list shows **"Top 20 in X% of runs"** beside
each catchment. A catchment is called **"robust"** if X ≥ 80%. The old two-map mark stays in
the data. Rank and score still come from the main run. The runs only measure how firm the
rank is.

### 2026-10-26 · V-17 part 2: results — 3 robust catchments, 15 in half the runs; districts steadier

`scripts/model/erosion_rank_stability.py` (log `logs/assam_rank_stability.log`), run as written:
1,000 draws, seed 42, 238 s. `reports/erosion_rank_stability_assam.csv` (catchments),
`…_districts.csv`, `.json`. The columns are joined onto the priority tables and the bundle.

To support it, `erosion_factors.py` now also writes `erosion_LS_nearing.tif` (the second S
form). The main outputs were fingerprinted before and after: identical.

| | Result |
|---|---|
| Catchments top 20 in ≥ 80% of runs ("robust") | **3**: Dima Hasao #12 (89%), Kamrup Rural #1 (87%), Dima Hasao #10 (84%) |
| Catchments top 20 in ≥ 50% of runs | **15** |
| Main run's top 20, median share of runs in the top 20 | **66%** |
| The old two-map mark against the runs (median top-20 share) | "top under both rain maps" **76.5%**; "depends on the rain source" **32.8%** |
| Districts in the top 5, share of runs | West Karbi Anglong 78%, Dima Hasao 77%, Cachar 76%, Kamrup Metro 60%, Bongaigaon 49%, Kamrup Rural 43% |

**Reading it:**

- The ranking is moderately firm. Only three catchments survive every plausible input
  combination in four runs out of five. The Cachar and Dima Hasao forested hills sit around
  75%: they drop when the tree cover value is low.
- Some plains-edge units (Dhubri, Tamulpur) reach the top 20 in about a third of runs: when
  tree C is low, bare cropland rises.
- The district picture is steadier: West Karbi Anglong, Dima Hasao and Cachar are top 5 in
  about three runs out of four.
- The list now shows "top 20 in X% of runs" in place of the yes/no mark. That gives the
  department a measured "survey these first" set: 3 robust, 15 more likely than not.

### 2026-10-26 · V-01: a gauge-corrected rain factor — not tested, because the gauges cannot be the truth

Considered as the next test (leave-one-gauge-out correction of the R map) and **dropped
before any fitting**. The 40 gauge R values from V-01 part 2 cannot serve as a reference:

- Sonapur, about 20 km from Guwahati, gives R **3,069** from its daily records, where the
  half-hourly measurement at Guwahati is **7,924**.
- The CWC files list rainy days only, so incomplete years look dry.
- InRESatE's daily model (a·P^b) was fitted to satellite daily rain, not to gauge rain, whose
  heavy days are distributed differently.

A correction fitted to these values would pull the map toward a known-wrong level. **What
would make it testable:** half-hourly or hourly rain-intensity records (IMD or ASDMA
self-recording gauges, an ASK in the application), or the CWC telemetry stations (hourly since
2019) once 10+ years exist. V-01 is unchanged.

### 2026-10-26 · E2.3 (part): the village card is built

**What it is.** A "Village card" page: type a place name, or a position as "lat, lon" (the
nearest listed place is shown, with its distance), and get one card.

| On the card | From |
|---|---|
| Soil loss around the place, its class, high-risk and steep shares | The main run, over a 2.1 km square round the place ("about 1 km around") |
| Its catchment's rank and "top 20 in X% of runs" | The priority list and V-17 part 2 |
| Why soil is lost there, and typical measures | The catchment's cause and second reason (V-18), hints (V-25) |
| Bare ground round the place, each dry season 2019–2026 | E1.1 |
| This week's erosive rain, × normal | The weekly outlook (E2.1), at the nearest rain point |
| A map zoomed to the place, with the erosion classes | The main run |
| A printable card (HTML → print to PDF) | All of the above |

**Places: 2,589 named places inside Assam**, de-duplicated (the same name within 2 km is one
place):

- 1,389 from OpenStreetMap (`fetch_52_osm_places.py`), 23 of them with an Assamese name as
  mapped;
- 1,165 from GeoNames (`fetch_53_geonames_places.py`, CC-BY);
- the 35 Survey of India district headquarters.

Built by `scripts/build/erosion_places.py` → `webapp/assets/erosion/assam/places.csv.gz`
(0.11 MB).

**Checks:** 15 of 15 SoilSense screen cases pass, three of them on the card (empty, by name,
by position). Screenshot looked at (Haflong).

**Not done:**

- **Coverage:** the open lists hold about 2,600 of Assam's roughly 26,000 census villages
  (V-31).
- **The Assamese card:** its wording must be written and checked by a native speaker; no
  machine-written Assamese is shown.
- **Ranking by revenue circle:** not built.

### 2026-10-26 · E2.3 (rest): ranking by the officer's own weights — built; E2.3 done

**What it is.** On the priority list, "⚖️ Rank by what matters to you": five sliders (0–5). Each
criterion becomes a percentile across the 703 catchments; the list is re-ranked by their
weighted mean. Ties, which come from figures rounded in the app's files, are broken by the main
rank.

| Criterion | From | Default |
|---|---|---|
| Average loss | The main run's mean A | 1 |
| Share of high-risk land | Share of scored land ≥ 10 t/ha/yr | 0 |
| Total soil lost | t/yr over the catchment (big catchments count more) | 0 |
| Getting barer lately | Steep land bare in the dry season, 2024–26 against 2019–21, in points; known for 281 catchments with ≥ 5 km² of steep land (the rest count as middling) | 0 |
| Villages in it | Named places listed in the catchment (an incomplete list: a rough pointer to people) | 0 |

**Checked:** with the defaults, the order equals the main ranking exactly (0 of 703 differ; a
first version without the tie-break differed in 364 places). Two new screen cases (custom
weights; all weights 0, which falls back to the default) pass with the rest.

**Example** (average loss 2, getting barer 3): Dhemaji's foothill gorge (main #5) goes to the top,
then catchments in the Kamrup Metro and Tinsukia hills whose steep land has got 2.5–4.5 points
barer since 2019–21.

### 2026-10-26 · E2.2 part 2: the outlook replay — good at *when*, weak at *where within a week*

`scripts/inspect/outlook_replay.py` → `reports/outlook_replay_assam.json`, run once, exactly as
part 1 and its clarifications fix it: 44 Monday issues (May–Sep 2024 and 2025) at 125 points,
against IMERG V07 Final from Earth Engine (`fetch_54_imerg_points_ee.py`, 4,748 days, none
missing).

| # | Check | Result | Climatology | Bar |
|---|---|---|---|---|
| G1 | Which places, within a week: median ρ across points | **0.181** | 0.115 | ≥ 0.30 and above climatology ✕ |
| G2 | Which weeks, state-wide: ρ across weeks | **0.633** | 0.389 | ≥ 0.60 and above climatology ✔ |
| G3 | Heavy weeks at a point (observed ≥ 2× normal): AUC | **0.765** (899 of 5500 point-weeks heavy) | 0.50 | ≥ 0.70 ✔ |

**By year:** 2024 G1 0.267, G2 0.765,
G3 0.789; 2025 G1 0.074, G2
0.508, G3 0.729.

**Forecast share ÷ observed share:** median **0.701**. The forecast
reads a little low against IMERG Final, but it is the same order: the same-source method kept
Open-Meteo's 1.7× wet bias out.

**Reading it:**

- The outlook says **when** an erosive week is coming: across weeks ρ 0.63, and at a point it
  separates weeks that turn out ≥ 2× normal at AUC 0.77.
- It is weak at **which places** within a week (ρ 0.18; better than climatology, below the
  bar). That is expected from forecast rain sampled every 22–31 km for patchy storm rain.
- So the page should lead with the week ("this week is 2× normal across the hills") and read
  its catchment list as regional, not as a precise spot forecast. The page now says so,
  with these numbers.

**Found on the way:**

- NASA's OPeNDAP server stopped accepting our connections at about 13:05 (clarification 4);
  Earth Engine served the same data.
- Earth Engine's warning names the reason for "Restricted Mode": **the project has exceeded
  its noncommercial compute quota** (V-29).

### 2026-10-26 · AD-01 part 1: an AI erosion map learned from ISRO's eroded-land map — the test, written before training

From [ROADMAP_EROSION.md](ROADMAP_EROSION.md), AD-01 (with AD-27, the explanations). It is
built while Earth Engine waits for its quota reset; every input is already on disk.

**The labels' role changes (register V-26).** NRSC's Land Degradation map 1:50k (2015–16)
becomes **training examples**, not only a check. Outputs are ours; NRSC's polygons are never
shared. Checks X1–X3 can no longer judge a model trained on NRSC, so the independent judge
becomes the blind picture check (AD-05).

**Cells:**

- Scored by the recipe (`erosion_assessed`), inside the state.
- **Eroded (1)** = NRSC codes 2–7 (sheet erosion moderate or severe, rills, gullies,
  ravines). **Normal (0)** = code 8.
- Left out: 0 (not mapped), 1 (slight), 9 (other degradation). These are X1's definitions.

**Inputs, two sets:**

| Set | Inputs |
|---|---|
| **A, the lead** (nothing newer than about 2021) | Terrain: height, slope, steepest slope, relief, plan and profile curvature, eastness, northness, upstream area (log), height above channel, wetness index, channel size (log). Soil: the 18 SoilGrids layers. Land cover (WorldCover class, categorical). Rain strength: InRESatE and IRED. The recipe's own K, LS and C. Canopy: Meta mean height and share under 3 m, ETH height |
| **B** | A + Hansen loss shares (2021–23, 2024–25) + mean and maximum dry-season bare share 2019–2026 + mean dry-season NDVI. These are later than NRSC's 2015–16, so B is reported, never led with |

**Model:** LightGBM with SlideSense's settings (`train_susceptibility.py` PARAMS).

- **Training rows:** in each training fold, every eroded cell plus three normal cells per
  eroded cell, drawn at random (seed 42).
- **Folds:** the frozen Assam 50 km folds (hash `a6bc908e791c9063`).
- **Scores:** every eligible cell is scored by the model that did not see its fold
  (out-of-fold, OOF).
- **The app's map** uses a full model trained on all folds; no score is ever quoted from it.

**Pass bars (set A, OOF):**

| # | Check | Bar |
|---|---|---|
| **AI-1** | AUC, eroded vs normal, on all eligible cells | **≥ 0.70**, and **≥ 0.03 above** both the formula's A and slope alone, computed on the same cells |
| **AI-2** | Spearman ρ over catchments (≥ 100 mapped cells): mean OOF score against NRSC's water-erosion share (codes 1–7) | **≥ 0.40** |

**Reported, no bar:**

- set B on the same tests;
- AUC per fold;
- the formula and slope alone, recomputed on these cells;
- the top inputs by SHAP.

**What ships:**

- If AI-1 and AI-2 pass: the app shows an **"AI rank"** beside the formula's rank, with
  agreement marked and the AI's top reasons from SHAP per catchment and village (AD-27).
- If not: reported, nothing shown.
- **Either way** the blind picture check (AD-05) judges both the formula and the AI on the
  same pictures before any claim that the AI is better.

### 2026-10-26 · AD-24: "What if we treat it?" — built

`scripts/build/erosion_treatment.py` → `webapp/assets/erosion/assam/treatment.json` (34 kB),
`reports/erosion_treatment_assam.csv`. The app has a new page with that name.

**How:** the recipe run forwards with the works in place. One hectare takes one measure,
in this order: replant, then terrace, then contour.

| Measure | Where | Value | Source |
|---|---|---|---|
| Replant (trees, bamboo, agroforestry) | Open land (shrub, grass, cropland, bare) ≥ 15° | C → 0.05 | Between W&S closed forest and IWED's shrub 0.11; provisional |
| Bench terraces | Open land ≥ 8° (not already replanted) | P 0.15 | Mid of the 0.1–0.2 reported for bench terracing in Indian hill studies; provisional |
| Contour bunds or trenches | Open land 1.7–14° | P 0.5–0.9 by slope | Wischmeier & Smith (1978), Table 13 (contouring); above 25% slope, P 1 |

**State-wide, if all eligible land were treated:**

| Measure | Eligible | Saved | Per hectare |
|---|---|---|---|
| Replant | 14,778 ha | 3.19 Mt/yr | **216 t/ha** |
| Terraces | 27,872 ha | 3.15 Mt/yr | **113 t/ha** |
| Contour | 488,443 ha | 5.63 Mt/yr | **11.5 t/ha** |

**Reading it:** a small area of open, steep land carries most of what works can save. Per
hectare, replanting or terracing it saves 10–20× what bunds on gentle farmland save. The
catchment ranking by "t saved per ha treated" is a new way to target conservation money.

**Checks:** three screen cases pass (district, catchment, all measures off).

**Not done:**

- costs per hectare ("per rupee") wait for the department's unit costs;
- tree land (*jhum* fallow) is not treatable here until the tree class is split (V-02, AD-08).

### 2026-10-27 · AD-01 part 2: results — the AI passes both bars; a caution on what it may have learned

`scripts/model/train_erosion_ai.py` (log `logs/assam_erosion_ai.log`, `reports/erosion_ai_assam.json`,
OOF in `data/processed/assam/erosion_ai_oof.parquet`), run as written: 5,259,253 eligible cells,
330,463 eroded. The PC slept between folds 2 and 3; the run resumed and finished unchanged.

| | AI, set A (lead) | AI, set B | Formula (A) | Slope alone | Bar |
|---|---|---|---|---|---|
| AI-1: OOF AUC, eroded vs normal, same 5,259,253 cells | **0.8202** | 0.823 | 0.6603 | 0.6503 | ≥ 0.70 and +0.03 over both ✔ |
| AI-2: catchment Spearman vs NRSC share (703 catchments) | **0.6586** | 0.659 | 0.3584 | — | ≥ 0.40 ✔ |
| AUC per fold, set A | 0.7361, 0.9024, 0.7217, 0.9212, 0.8266 | | | | reported |

**Top inputs (gain, set A):** soil_cfvo_60-100cm 23.1%, R_ired 13.4%, R_inresate 13.2%, dem_elev_m 8.5%, hydro_chan_log 7.3%, canopy_h_eth 4.4%, soil_cfvo_15-30cm 3.6%, soil_cfvo_0-5cm 1.9%.

**Reading it:**

1. **Both bars pass with room to spare**, so by the rule the app shows an AI rank beside the
   formula's, with agreement and the AI's reasons (AD-27).
2. **Set B adds almost nothing** (+0.003): the later satellite layers carry little that set A
   lacks. So the time trap (NRSC 2015–16 against 2019+ layers) does not drive the result.
3. **The caution.** The strongest inputs are smooth, state-scale fields: SoilGrids' deep coarse
   fragments, the two rain-strength maps, elevation and channel size. A model can use such
   fields to learn *where NRSC's mappers tended to mark erosion* (by survey sheet or team),
   not only *why* land erodes.
   - The 50 km blocks limit this but cannot rule it out.
   - Fold AUC ranges 0.72–0.92.
4. **That is why AD-05 matters.** The blind picture check judges both maps on the same squares
   before any claim that the AI finds eroding land better than the formula. Until then the app
   says "learned from ISRO's map", never "more accurate".

### 2026-10-27 · AD-01 part 3 and AD-27: the AI map is in the app, with its reasons

**Full model and map.**

- `full_A.txt` was trained on all folds (set A, 1:3 sample) and scored all 5,453,010 scored
  squares → `erosion_ai_score.tif`.
- The prediction step was re-run from the saved model after the session ended mid-run.

**Reasons (AD-27)**, from `scripts/model/erosion_ai_explain.py` →
`reports/erosion_ai_units_assam.csv` (+ `_districts`):

- **Method:** LightGBM's own TreeSHAP values on up to 300 squares per unit, summed by input
  group (rain strength, terrain, water and drainage, soil, land cover).
- **Per unit:** the group that pushes the AI up most, and the one that pulls it down most.
- **Agreement:** "both high" (top 50 catchments or top 8 districts by both), "AI higher",
  "formula higher" or "both lower".

| | Both high | AI higher | Formula higher |
|---|---|---|---|
| Catchments (top 50) | 14 | 36 | 36 |
| Districts (top 8) | 5 | 3 | 3 |

**What the AI sees differently:**

- **Same top districts as the formula:** West Karbi Anglong, Dima Hasao, Karbi Anglong,
  Hailakandi and Kamrup Rural lead in both.
- **AI only:** the north-bank foothills come in through land cover. Biswanath is 3rd (formula
  32nd), Sonitpur 5th (formula 34th), Chirang 8th (formula 25th). These are exactly the
  districts where NRSC marks sheet erosion and the formula misses it (E1.5 part 2).
- **Its top catchments' main reason** is mostly "soil" (44 of 50): the deep-stoniness signal
  flagged in part 2.

**In the app:**

- The erosion map has an **"AI map"** option: five bands by share of scored land, with its
  own legend, top-20 outlines and tooltip (AI rank, agreement, reasons). Its top list shows
  each catchment's formula rank beside it.
- The priority list has AI rank, agreement and the AI's main reason.
- The village card has a line with its catchment's AI rank and reason.
- The method page has a paragraph with the scores and both cautions.

**Checks:** all SoilSense screen cases pass, a new one included (AI map + Biswanath).
Screenshot looked at.

### 2026-10-27 · AD-02 part 1: does the outlook's erosive rain show up as river mud? — the test, written before fetching rain

From [ROADMAP_EROSION.md](ROADMAP_EROSION.md) AD-02. It checks whether the outlook's number, a
week's erosive rain against the usual for the time of year, shows up as muddier rivers.

**Stations.** CWC daily suspended-sediment concentration (g/L), `fetch_46`.

- Kept: catchments ≥ 95% inside India (`sediment_station_catchments.gpkg`) with ≥ 8 years of
  readings in **2010–2026**.
- **11 stations:** Dudhnai, Rukni at Dholai, Digaru at Sonapur, Sonai at Tulargram, Dikhow at
  Sivasagar, Katakhal at Matijuri, Buridehing at Chenimari, Dhansiri at Golaghat, Kopili at
  Jagibhakatgaon, Barak at Annapurna Ghat and at Badarpur Ghat. Margherita's records end in
  2008.
- The two Barak stations are nested; both are kept and reported, and noted as not independent.

**Rain.** Open-Meteo archive daily rain, the source the outlook itself uses (its forecasts
are compared with this history).

- **Period:** 2010-01-01 → 2026-10-20.
- **Points:** the outlook's 0.2° lattice points inside each catchment, or the nearest one to
  its centre if none falls inside. Points already fetched for Assam are reused.
- **EI_day = a·P^b** at each point (InRESatE's daily model, nearest valid cell); the catchment
  value is the mean over its points.

**Weeks.** Monday to Sunday.

- Erosive rain = the week's summed EI.
- Plain rain = the week's summed P.
- River mud = the mean of the week's readings, counted if it has ≥ 2.

**Departures from the usual.** Each weekly value becomes its percentile among all years' values
for the same week of the year ± 1 week, at that station. Rank-based, so a few huge
monsoon weeks cannot dominate.

**Pass bars:**

| # | Check | Bar |
|---|---|---|
| **M1** | Spearman ρ between the erosive-rain departure and the river-mud departure, same week, per station | ρ > 0 at **≥ 2/3 of stations**, and median ρ **≥ 0.30** |
| **M2** | The same for plain rain (the baseline) | Erosive rain's median ρ **≥** plain rain's |

**Reported, no bar:**

- mud one week later;
- monsoon weeks only (June–September);
- each station's ρ;
- for the two catchments mostly inside the map (Kopili 81%; Gaurang excluded at 72% inside
  India), the soil-at-risk version (erosive-rain share × the map's loss).

**Limits, stated now:**

- **Concentration, not tonnes:** CWC publishes no river flow for Assam.
- **Mud has other sources:** banks and channels add mud too.
- **Scale:** stations sit on medium rivers, so this checks timing per catchment, not per field.

**It sets AD-06's baseline:** the AI river-mud model must beat M1's numbers.

### 2026-10-27 · AD-05 and AD-30 part 1: the blind picture check (independent judge) and gully-prone ground — written before any picture

**Gully-prone ground (AD-30), fixed before sampling**
(`scripts/build/erosion_gully_prone.py`, built, no picture seen). A square is flagged when all
hold:

- open land (shrub, grass, cropland, bare), scored;
- slope ≥ 5°;
- upstream area 0.03–5 km² (a hillslope hollow, not a river);
- stream-power index (upstream area per metre × tan slope) in the top 10% of such squares.

That flags **3,090 ha** out of 30,900 ha of candidates.

**The pictures.** Esri World Imagery (about 1 m), the app's own satellite base map, via the
export service already used for the top-20 eye check.

- One 500 m × 500 m window per square, the 100 m square outlined, a neutral id.
- The key (what each square scored) is written to a separate file, opened only after every
  picture is labelled.
- Esri's imagery is a mosaic of unknown dates. Erosion signs like gullies, bare slopes and
  scars persist for years, so this is a fair but not a dated check.

**Sample (seed 7), 300 squares:**

| Stratum | n | For |
|---|---|---|
| F | 40 scored squares per formula class (slight … very severe) = 240 | The formula; the AI on the same pictures |
| G | 30 gully-prone squares + 30 open, ≥ 5°, not-flagged squares | AD-30 against a control |

**Label, one per picture:**

- **"gully"**: a gully or deep channel cut at the square;
- **"erosion"**: other visible erosion, such as bare soil on a slope, rills, slips or scars,
  freshly cleared slopes or sediment fans;
- **"none"**: covered or stable ground;
- **"can't tell"**.

"Yes" means gully or erosion.

**Pass bars:**

| # | Check | Bar |
|---|---|---|
| **P-F** | The formula: share "yes" in classes severe + very severe against slight + moderate (stratum F) | **≥ 2×** |
| **P-AI** | The AI on stratum F: share "yes" in its top 10% band (score ≥ the 90th percentile of scored land) against its lower half | **≥ 2×** |
| **P-G** | Gully-prone (AD-30): share "yes" among flagged against control squares (stratum G) | **≥ 2×** |
| **P-cmp** | Formula vs AI: AUC of each score for "yes" on stratum F's readable pictures | **Reported.** "AI better" is claimed only if the AI's AUC is **≥ 0.05 higher** |

Shares are over readable pictures ("can't tell" left out). The strict share, which counts
"can't tell" as not "yes", is reported beside it.

### 2026-10-27 · AD-25 and AD-02: results — soil reaching rivers; the river-mud check fails its strength bar

**AD-25, soil reaching rivers** (`scripts/build/erosion_connectivity.py`, 103 s;
`erosion_ic.tif`, `erosion_sdr.tif`, `erosion_delivered_tpha.tif`,
`reports/erosion_connectivity_assam.csv` and `…_districts.csv`):

- **Sediment delivery ratio on scored land:** p10 0.023, median 0.040, p90 0.077 (InVEST
  defaults: IC0 0.5, k 2, SDR_max 0.8).
- **State:** loss 118.0 Mt/yr, of which **7.8 Mt/yr (7%)** is estimated to reach the
  streams.
- **Districts by delivered t/ha:** Dima Hasao 3.76, West Karbi Anglong 3.27, Cachar 3.03,
  Kamrup Metro 2.99, Kamrup Rural 2.98. The delivered share is fairly even (5.6–7.7%), so at
  district level the order barely changes from the loss order.
- **Its use is square by square:** which eroding patches are wired to a stream, which is
  where check dams and gully plugs pay.
- Model estimates; untested. Measured mud cannot check tonnes without river flow (none for
  Assam).

**AD-02, outlook vs river mud** (`scripts/inspect/river_mud_check.py` →
`reports/river_mud_check_assam.json`; station-weeks in
`data/processed/assam/river_mud_weeks.parquet` for AD-06), run as written:

- **Data:** 11 stations; rain from `fetch_55` (Open-Meteo archive, 140 lattice points, 6,137
  days, none missing).

| # | Check | Result | Bar |
|---|---|---|---|
| M1 | Erosive-rain anomaly vs mud anomaly, same week: share of stations with ρ > 0 | **82%** | ≥ 67% ✔ |
| M1 | … median ρ | **0.072** | ≥ 0.30 ✕ |
| M2 | Erosive rain's median ρ vs plain rain's (0.067) | 0.072 ≥ 0.067 | ✔ |

- **Reported:** mud one week later, median ρ **0.112**; monsoon weeks
  only, 0.048.
- **Per station:** Annapurna Ghat 0.097, Badarpur Ghat 0.072, Chenimari (Khowang) -0.013, DUDHNAI 0.225, Dholai 0.005, Golaghat 0.085, Jagibhakatgaon 0.009, Matijuri 0.057, SONAPUR 0.124, Sivasagar -0.009, TULARGRAM 0.107.

**Reading it:**

- **The direction is right**, at 9 of 11 stations, but the weekly link is weak. Unusual
  erosive rain explains little of a river's unusual muddiness at this scale.
- **Expected reasons:**
  - mud is one manual sample a day;
  - concentration dilutes at high flow;
  - banks and channels add mud;
  - the rain is ERA5-based at about 25 km;
  - catchments run to 25,000 km².
- **The outlook must not be presented as a river-mud forecast.** Its tested skill stays the
  rain timing (E2.2).
- **AD-06 now has its baseline:** an AI river-mud model must beat median ρ 0.072
  (same week) and 0.112 (next week).

### 2026-10-27 · AD-06 part 1: an AI river-mud model — the test, written before training

**Question.** Can a model learn a week's river-mud anomaly from rain and ground better than the
outlook's single erosive-rain number (AD-02: median ρ 0.072 same week, 0.112 next week)?

**Rows.** AD-02's station-weeks (`river_mud_weeks.parquet`): 11 stations, 2010–2026, weeks
with a mud anomaly (≥ 2 readings).

**Target.** The same-week mud anomaly (the seasonal percentile from AD-02), so the result is
directly comparable.

**Inputs:**

- this week's erosive-rain anomaly and its raw log value;
- the erosive rain of the 1, 2 and 3 weeks before (log);
- rain over the previous 30 and 60 days (log): how wet the ground already is;
- the week's wettest day (log);
- week of the year (sine, cosine);
- fixed catchment traits: log area, and the mean of the erosion map's slope factor, loss, cover
  factor and delivered share over the catchment's mapped part.

**Model.** LightGBM regression, deliberately small: 300 trees, 15 leaves, at least 50 rows per
leaf, learning rate 0.03, seed 42.

**Held out two ways:**

- **By year:** each year predicted by a model trained on the other years.
- **By station:** each station predicted by a model that never saw it. The two Barak stations
  are held out together, as they are nested.

**Pass bar:** the median over stations of Spearman ρ (predicted vs observed anomaly) **≥ 0.20
under both holdouts**. That is about double AD-02's best (0.11).

**Reported:** each station's ρ, and the inputs' importance.

**What ships if it passes:** a weekly "expected river mud against normal" line per gauged
catchment, fed from the outlook's forecast rain, labelled as an AI outlook and graded weekly
against CWC's 2026 file. **If it fails:** reported; nothing is shown.

### 2026-10-27 · AD-06 part 2: results — the AI river-mud model FAILS; nothing ships

`scripts/model/train_river_mud_ai.py` → `reports/river_mud_ai_assam.json`, run as written:
8,780 station-weeks, 11 stations, 2010–2026.

| Holdout | Median ρ over stations | Bar |
|---|---|---|
| By year (leave-one-year-out) | **-0.036** | ≥ 0.20 ✕ |
| By station (leave-one-out, Barak pair together) | **0.101** | ≥ 0.20 ✕ |
| AD-02's single erosive-rain anomaly, same rows | 0.071 | (baseline) |

**Top inputs:** rain over the previous 60 and 30 days, then erosive rain the week before.
Ground wetness and lag matter more than the week's own rain, as expected for river mud.

**Reading it:** across unseen years the model does no better than chance, and across unseen
stations only a little better than the single number. With weekly mud anomalies from one manual
sample a day, ERA5-scale rain and no river flow, there is no transferable weekly signal to
learn. **Not adopted; nothing is shown.**

**What could change it:**

- river flow or turbidity sensors (AD-19, minute-level);
- daily, not weekly, targets on the stations with daily sampling;
- satellite rain at 0.1° (IMERG via Earth Engine after the quota reset).

### 2026-10-28 · AD-05 and AD-30 part 2: results — the formula meets its bar (weakly); the AI and gully-prone ground do not

`scripts/inspect/erosion_eyecheck.py --score` → `reports/erosion_eyecheck_assam.json`, run as
written in part 1. Labels in `data/interim/assam/erosion/eyecheck_ad05/labels.csv`.

**How the labelling was done.**

- All 300 pictures were labelled before `_key.csv` was opened. They were viewed at full
  resolution (400 px over 500 m) in sheets of 12.
- One labeller (Claude), so there is no second opinion and no agreement figure (V-33).
- A working rule was fixed on the first sheet, before any score was known. **"Erosion"** means
  bare or scarred ground inside the square:
  - included: exposed soil on sloping ground, cut faces (hill cutting, hill quarries,
    hill-road cuts) and freshly cleared hill patches (*jhum*);
  - left out: tilled or fallow fields, paddies (valley terraces included), sand bars, water,
    and flat built or quarried yards.
- A final pass over 12 borderline pictures, still blind, changed one label (061, to match
  145 and 008).

**Labels:** none 274, erosion 19, gully 1, can't tell 6 (cloud or cloud shadow). Only **20 of
300** squares show visible erosion, so every result below rests on small counts.

| # | Check | Result | Bar |
|---|---|---|---|
| **P-F** | Formula: "yes" in severe + very severe vs slight + moderate | **7.7% (6/78) vs 2.5% (2/80), 3.08×** | ≥ 2× ✔ |
| **P-AI** | AI: "yes" in its top 10% band vs its lower half | 3.3% (1/30) vs 3.2% (3/93), **1.03×** | ≥ 2× ✕ |
| **P-G** | Gully-prone vs open, ≥ 5°, not-flagged control | 16.7% (5/30) vs 20.0% (6/30), **0.83×** | ≥ 2× ✕ |
| **P-cmp** | AUC for "yes", stratum F, 234 readable | formula **0.616**, AI **0.628** | "AI better" needs +0.05 ✕ |

**Reported beside the bars (not pre-registered, so read only as context):**

- **P-F is not firm.** A one-sided Fisher test gives p = 0.13, and the 90% bootstrap range of
  the ratio starts at about 1.0. The bar is met, but with 8 "yes" squares it could be chance.
- **Per formula class**, share "yes" for slight → very severe: 2.5 / 2.5 / 2.6 / 0 / 10.5 /
  5.0%.
- **Open land on slopes of 5° or more** (the 60 G-stratum squares) shows visible erosion
  **18%** of the time, against **4%** in the formula sample. All 11 "yes" squares there sit in
  formula classes severe or very severe (0 of 17 below). The formula's cover and slope carry
  most of what the eye can see.
- P-G gully counts: 1 "gully" label in 300. At about 1 m per pixel, gullies narrower than a few
  metres, or under grass, are hard to see. P-G judges "visible erosion of any kind".

**Reading it:**

1. **The formula** passes its pre-registered picture check, weakly. Together with the NRSC
   result (X1 0.66), it is a fair, not a strong, map of where erosion shows.
2. **The AI map does not see the ground better.** On ISRO's labels it scored 0.82 against
   0.66. On pictures it ties the formula, 0.63 against 0.62, and its top band is no richer in
   visible erosion than its lower half. This is what AD-01's caution predicted: it learned
   where ISRO's 2015–16 mappers drew eroded land, through broad regional inputs (deep-soil
   stoniness, rain strength), more than what the ground shows. **It stays in the app as a
   second opinion "that agrees with ISRO's map", never as "the better map".** The map page,
   the help line and the method page now say so, with the numbers read from the report.
3. **Gully-prone ground (AD-30) is not adopted.** The terrain flag is no better than any open
   sloping square. It is not exported and not shown. The useful signal is open land on slopes,
   which the formula already carries.
4. **What would make the check stronger:**
   - more "yes" squares, by sampling open sloping land more heavily;
   - a second labeller, so agreement can be measured;
   - dated imagery, after the Earth Engine reset or from Copernicus;
   - the pilot's field visits, which are the real judge (E2.4).

### 2026-10-28 · RC part 1: our own river-mud record from satellite river colour — the test, written before fetching

**Why.** The WHEN model (AD-06) failed for want of examples: one hand sample a day at a few
stations, and no river flow. Muddy water is browner and brighter in red light. If Sentinel-2's
red reflectance over a river tracks CWC's measured mud, we can build our own mud record. It
would cover every 5 days since 2017, and any river wide enough, not just the stations. This is
the "build the examples ourselves" route (the same idea as the verified flood record).
Copernicus Data Space (openEO), no Earth Engine.

**Sites.** Every Assam CWC sediment station with **≥ 1,000 readings since 2017** (about 22).
Pixels within **300 m** of the station's point.

**Satellite values per clear date** (Sentinel-2 L2A, 10 m, 2017-01-01 → 2026-10-20):

- **Water pixel:** NDWI = (B3 − B8)/(B3 + B8) > 0, and the scene class is not cloud, cloud
  shadow, cirrus, saturated, snow or no data (SCL 0, 1, 3, 8, 9, 10, 11).
  - NDWI is used, not SCL's own water class (6), because very muddy water can be mislabelled
    by SCL, which would drop the muddiest days. The SCL-water variant is reported beside it.
- **Value:** the median red reflectance (B4) of the water pixels, and the count of water
  pixels.
- **A date counts** if it has ≥ 20 water pixels (0.2 ha).

**Match.** A satellite date paired with the same day's CWC reading (sample about 08:00,
overpass about 10:30 local).

**Checks and bars:**

| # | Check | Bar |
|---|---|---|
| **RC1** | Per station with ≥ 20 matched days: Spearman ρ (red reflectance, measured mud) | **median ρ ≥ 0.50** and **ρ > 0 at ≥ 80%** of those stations |
| **RC2** | Within-season: the same, using each value's seasonal percentile (same month ± 1, per station), so the shared dry/wet swing is removed | **median ρ ≥ 0.30** |
| **RC3** | Monsoon cover: clear dates (Jun–Sep) per station-year | **Reported.** The record can feed a WHEN model only if the median is **≥ 3** |

**Reported:** matched days per station; ρ for SCL-water and for B4/B3; monsoon-only ρ.

**What follows:**

- **If RC1 and RC2 pass:** "river colour" is adopted as our own mud record. Next comes a WHEN
  model trained on it, with a new pre-registration. The test is still against CWC's measured
  mud.
- **If RC1 passes and RC2 fails:** colour only tracks the season. It is not adopted for WHEN.
- **If RC1 fails:** reported; not adopted.

**Clarification, added during the fetch and before any match with river mud.** From
2022-01-25 (processing baseline 04.00), Sentinel-2 L2A values carry a +1000 offset.

- **Detection:** the median over stations of the Feb–Apr water-red value in 2022 minus 2021.
  This uses satellite values only.
- **Correction:** if the jump exceeds 500, 1000 is subtracted from dates from 2022-01-25 on.
- **Reporting:** the jump and whether it was removed go in the report.

Scripts: `scripts/fetch/fetch_56_river_colour.py` (fetch),
`scripts/inspect/river_colour_check.py` (score).

**Fetch status (2026-10-28, about 02:45 IST).** All 20 year-jobs are queued on Copernicus
openEO (10 NDWI, 10 SCL-water). They run 2 at a time, about an hour each, on Copernicus's
servers, so the PC can be off.

- The 2017 job carries the first run's title (`river_colour_ndwi_2017`). The others are
  `rc_<variant>_<year>`.
- To collect: `$env:REGION = "assam"; python scripts/fetch/fetch_56_river_colour.py`. It
  downloads the finished jobs and waits for any still running.
- Then score: `python scripts/inspect/river_colour_check.py`.

### 2026-10-28 · RC part 2: results — river colour tracks river mud only weakly; not adopted

`scripts/inspect/river_colour_check.py` → `reports/river_colour_check_assam.json`, run as
written.

- **Data:** 25 stations; 9,420 clear station-dates (NDWI water, ≥ 20 water pixels),
  2017 → Oct 2026.
- **Offset check:** the 2021→2022 jump is −53 DN, well under 500. The CDSE archive is already
  harmonised, so nothing was removed.
- **SCL-water variant:** 7 of its 10 years were collected (2024 errored and was resubmitted;
  2025–26 were still running).

| # | Check | Result | Bar |
|---|---|---|---|
| **RC1** | Same-day ρ (red, measured mud), median over 25 stations | **0.328**, positive at 96% | ≥ 0.50 and ≥ 80% ✕ (strength fails) |
| **RC2** | The same on seasonal percentiles | **0.143** | ≥ 0.30 ✕ |
| **RC3** | Clear Jun–Sep dates per station-year, median | **6** | ≥ 3 ✔ |

**Reported beside the bars:**

- **Red/green ratio:** median ρ 0.36.
- **Monsoon months only:** median ρ **0.03**.
- **SCL-water variant (partial):** RC1 0.326, RC2 0.161, monsoon dates 2.
- **Per station, RC1:**
  - the wide Barak and Brahmaputra sites are the best: Pandu 0.56, Matijuri 0.54,
    Fulertal 0.53, Badarpur Ghat 0.52, Annapurna Ghat 0.52, Pancharatna 0.51;
  - the narrow or tributary sites are the weakest: Kalain −0.01, Khudrakhowa 0.03,
    Sonapur 0.06.

**Reading it:**

- **Direction:** colour moves the right way almost everywhere.
- **Strength:** it is too weak to stand in for measured mud.
- **Season:** most of the link is the shared dry/wet swing (RC2 0.14), and inside the monsoon
  it vanishes (0.03).
- **Cover:** clouds are not the main problem. Six clear monsoon dates a year get through.
- **Likely causes:**
  - **Red saturates.** At the very high mud levels of the monsoon Brahmaputra, red stops
    rising. Near-infrared keeps rising, which is why published methods switch bands
    (Dogliotti et al. 2015).
  - **Narrow rivers.** On narrow rivers the 300 m circle mixes in banks and sandbars.
  - **Timing and place.** One hand sample at about 08:00 at one point, against a 10:30 image
    over a 300 m circle.
- **Not adopted** for WHEN, as pre-registered.

**A second attempt (needs its own pre-registration):**

- near-infrared or a published switching method (Nechad / Dogliotti) instead of plain red;
- wide-river stations only;
- a smaller footprint drawn on the channel itself.

The river-height and rain inputs for the WHEN retry do not depend on this.

### 2026-10-28 · Inputs for a second WHEN attempt: river heights and sharper rain (fetch only, no test yet)

AD-06 failed partly because a muddy river and a diluted one look alike without flow, and
partly on coarse rain. Two inputs are now being gathered. A second attempt will be
pre-registered before any of them is used.

**1. River heights at the mud stations (CWC FFS, the open API FloodSense already uses).**

- **Matched:** 15 of the 25 mud stations, by station name and position (0–0.1 km):

  | Station | CWC code |
  |---|---|
  | Annapurna Ghat | 01-11-01-007 |
  | Badarpur Ghat | 01-11-01-006 |
  | Chenimari | 013-UBDDIB |
  | Chouldhowaghat | 021-UBDDIB |
  | Dholai | 016-MBDGHY |
  | Fulertal | 01-11-01-008 |
  | Golaghat | 026-UBDDIB |
  | Kalain | 027- MDSIL |
  | Lala | 018-MDSIL |
  | Matijuri | 01-11-01-002, plus the older 015-MBDGHY |
  | Nanglamoraghat | 016-UBDDIB |
  | Pandu | 025-MBDGHY |
  | Patharkandi | 019-MDSIL |
  | Sivasagar | 018-ubddib |
  | Tulargram | 007-MDSIL |

- **History:** 35,000–207,000 readings each, from 1971–2019 to today.
- **Not matched (10):** Bhomoraguri, Dudhnai, Jagibhakatgaon, Kulsi, Katigorah, Khudrakhowa,
  Kokrajhar, Pancharatna, Sonapur and Udharbond are not in CWC's forecast-station list, and a
  bulk station query timed out.
  - IIT Bombay's GUARDIAN site (indiariverflow.com) has hourly heights for them from 2020,
    scraped from the same CWC portal. It has **no flow for any Assam station** ("no rating
    curve").
- **Stored apart from FloodSense:** `data/raw/11_gauges/cwc_assam/`. `fetch_21_cwc_gauges.py`
  now writes non-Arunachal regions to `cwc_<region>/`, and skips Arunachal's pilot registry for
  them.
  - Two FloodSense scripts scan `cwc/*_hhs.csv`: `check_gauge_cleaning.py` would have failed on
    them, and `build_backbone_bundle.py` would have miscounted.
  - `check_live_unchanged.py check`: PASS before and after.
- **Station list:** `data/interim/assam/cwc_assam_stations.json`.

**2. Daily IMERG over all Assam, 0.1°, 2013–2026 (NASA GES DISC).**

- The 4-worker run failed: 0 of 5,043 days, ConnectTimeout, the same block as on 26 Oct.
- One worker works, at about 3 s a day, so about 4–5 h. It resumes: finished days are skipped.
- Already on hand: IMERG at 125 points (2013–2025, Earth Engine), and the full grid over the
  Arunachal box (2000–2026).

### 2026-10-28 · AD-06 attempt 2 part 1: daily river mud from rain AND the river's own height — the test, written before training

**What changes from attempt 1** (weekly, rain only: by year −0.04, by station 0.10):

- **The river's height.** It is the stand-in for flow that attempt 1 lacked: a muddy river
  and a diluted one differ in height. Height is also rising or falling, and rising rivers
  carry more mud.
- **Daily, not weekly.** Storm days are not averaged away.
- **Satellite rain** (IMERG V07, 125 points) instead of 25 km reanalysis rain.

**Stations.** The same rule as attempt 1: ≥ 95% of the catchment in India and under
60,000 km². Kept are those with a CWC height record (`cwc_assam/`), **12 stations**:

- Annapurna Ghat, Badarpur Ghat, Chenimari, Dholai, Golaghat, Kalain, Lala, Matijuri,
  Nanglamoraghat, Patharkandi, Sivasagar, Tulargram.
- Matijuri: the newer code (01-11-01-002), filled from the older one (015-MBDGHY) where
  missing.

**Rows.** Station-days 2013–2025 with a mud reading (the mean of the day's readings) and all
inputs present.

**Target.** The day's mud as a seasonal percentile: per station, among that station's days
in the same month ± 1. This takes out the plain dry/wet swing.

**Inputs.** All known by the morning sample (about 08:00 IST), so the model could run as an
outlook:

- **Rain, catchment mean of the IMERG points inside it** (the nearest point if none):
  - the day before;
  - the last 3, 7 and 30 days;
  - the wettest day of the last 7;
  - erosive rain (InRESatE a·P^b) over the last 3 and 7 days.
  - IMERG days are UTC, ending 05:30 IST.
- **River height, from the daily median of CWC readings:**
  - the day before, as an anomaly: (level − the station's median for that month) ÷ that
    month's interquartile range;
  - the change over the last 1 and 3 days, in the same units;
  - the highest anomaly of the last 7 days.
- **Season:** day of year (sine, cosine).
- **Catchment traits:** log area, and the mean slope factor, loss, cover factor and delivered
  share (as in attempt 1).

**Model.** LightGBM regression with attempt 1's settings: 300 trees, 15 leaves, at least 50
rows per leaf, learning rate 0.03, seed 42.

**Held out:**

- **By year:** leave one year out.
- **By station:** leave one out, with nested sites held out together:
  - {Annapurna Ghat, Badarpur Ghat, Tulargram} on the Barak;
  - {Matijuri, Lala}, which share a mapped catchment.

**Baselines on the same rows** (median over stations of Spearman ρ with the target):

- **B1:** yesterday's height anomaly alone. One number, no AI.
- **B2:** the last 3 days' erosive rain alone.

**Pass bar.** Under **both** holdouts, the median over stations of Spearman ρ (predicted vs
observed):

- must be **≥ 0.30**,
- and must be **≥ B1 + 0.05**, so the AI must add something beyond the river's height alone.

**Reported, not judged:**

- a "nowcast" variant that also sees the same day's height;
- per-station ρ;
- input importance;
- monsoon-only ρ.

**What follows:**

- **If it passes:** a daily "river mud against normal" outlook for these gauged rivers, fed
  by forecast rain and FloodSense-style level forecasts. It is labelled AI and graded daily
  against CWC's readings.
- **If it fails:** reported. WHEN waits for sensors (AD-19) and river flow.

Script: `scripts/model/train_river_mud_ai_v2.py` → `reports/river_mud_ai_v2_assam.json`.

### 2026-10-28 · AD-06 attempt 2 part 2: results — FAILS; the river's height alone beats the AI

Run as written: 34,792 station-days, 12 stations, 2013–2025.

| | Median ρ over stations | Bar |
|---|---|---|
| **AI, held out by year** | **0.138** | ≥ 0.30 and ≥ B1 + 0.05 ✕ |
| **AI, held out by station** | **0.204** | ✕ |
| B1: yesterday's river-height anomaly alone | **0.242** | (baseline) |
| B2: last 3 days' erosive rain alone | 0.059 | (baseline) |
| Nowcast (also sees today's height), by year / by station | 0.150 / 0.209 | reported |
| AI, monsoon only, by year | 0.130 | reported |

- **Per station** (AI, by year):
  - positive: Chenimari 0.37, Golaghat 0.33, Nanglamoraghat 0.28, Annapurna Ghat 0.28;
  - negative: Kalain −0.26, Lala −0.27, Dholai −0.10.
  - Kalain's height runs *against* its mud (B1 −0.33), which suggests a gauge or datum
    problem there.
- **Top inputs:** yesterday's height anomaly 25%, the highest height of the last week 15%,
  30-day rain 13%.

**Reading it:**

1. **The AI does not pass,** and it is worse than the single number it was meant to beat.
   Across unseen years it learns patterns that do not carry over.
2. **The useful finding is the baseline.**
   - A river's height above its normal for the month says more about its unusual muddiness
     (ρ 0.24) than any catchment rain measure we have (erosive rain 0.06, attempt 1 0.07).
   - At these stations, river mud follows the river's own state more than the hillsides'
     rain. That fits catchments of 170–25,000 km², where banks, channels and upstream storage
     sit between the slope and the sampler.
   - Even height alone is weak (0.24).
3. **WHEN on open data is closed for now.** Four tries have failed:
   - AD-02, rain vs mud: strength fails;
   - AD-06, weekly AI: fails;
   - RC, river colour: fails;
   - AD-06 attempt 2: fails.
   - The common cause is the target: one hand sample a day on large rivers, with no flow.
   - **It is not re-tried until** one of these exists:
     - turbidity and rain sensors on small hill streams (AD-19);
     - soil-loss plots (AD-31);
     - CWC river flow for Assam (an ask).
4. **What the outlook keeps saying:** "a heavy erosive-rain week", which is tested on
   *when* (E2.2: weeks ρ 0.63, heavy weeks AUC 0.77). It never says "river mud".

### 2026-10-28 · AD-25 in the app: "Soil reaching streams"

Built from AD-25's outputs: no new model, no new numbers.

- **Bundle** (`export_erosion_bundle.py`):
  - **Map layer:** `classes.npz["deliv"]`, five bands of t/ha/yr reaching a stream: < 0.5,
    0.5–1, 1–2, 2–5, ≥ 5. They hold 56 / 12 / 12 / 13 / 7% of scored land.
  - **State summary:** `meta["delivered"]`: 116.4 Mt/yr lost, 7.8 Mt (6.7%) reaching a
    stream; delivery ratio p10/p50/p90 0.023 / 0.040 / 0.077.
  - **Unit figures:** `delivered_tpha`, `delivered_share_pct` and `rank_delivered` on every
    catchment (703) and district (35).
- **App** (`webapp/products/erosion/view.py`):
  - **Map:** a fifth view, "Soil reaching streams", with a blue legend, the state-total
    caption, a tooltip and a top-10 list with each unit's loss rank beside it.
  - **District card:** a line on it.
  - **Priority list:** a "Reaching streams t/ha/yr" column and a sixth weight slider. Its
    default is 0, so the default order is unchanged.
  - **"How to read this":** a paragraph.
  - Everywhere it is labelled "an estimate, not yet checked against measurements".
- **Checks:** 23/23 SoilSense screen cases pass, including two new ones (the map view and the
  list weighted by it).
- **What it shows:** at catchment level the order barely changes from loss. The shares are
  6–9%; Dima Hasao is #1 for districts and #2 for loss. The value is inside a unit: which
  eroding squares are wired to a channel.

### 2026-10-29 · AD-29: what the lost soil is worth — built and in the app

A calculation on the main map, not a model and not a test
(`scripts/build/erosion_soil_value.py`).

**Data.** SoilGrids **total nitrogen** was added to `fetch_03_soil.py` (Assam only, three
depths). `features.py` will now also build `soil_nitrogen_*` for Assam when it is next run.
The AI map's inputs are an explicit list, so they do not change.

**Per scored square:**

- nitrogen lost = A × topsoil N (g/kg);
- carbon lost = A × topsoil organic carbon;
- topsoil lost (mm) = A ÷ (bulk density × 10);
- as urea = N ÷ 0.46 ÷ 45 kg bags × ₹266.5 a bag (V-34);
- topsoil means the 0–5 and 15–30 cm mean, as K uses;
- enrichment ratio 1, so these are floors.

**Results** (`reports/erosion_soil_value_assam.{json,csv}`, `…_districts.csv`):

- **Typical topsoil:** median 2.6 g/kg N and 20.6 g/kg organic carbon.
- **Farmland** (cropland, 13.5 lakh ha):
  - 47,600 t N a year: mean **35 kg/ha** (median 21), about **1.7 urea bags/ha**;
  - **₹61 crore a year** at the farmer's price;
  - median topsoil loss 0.78 mm a year;
  - the same under either tree cover value.
- **Tree land:** 33,000–331,000 t N a year, a **10× range** set by tree C 0.003 vs 0.03
  (V-02). It is never given as one figure.
- **State:** 112,000–410,000 t N a year.
- **Districts by N per hectare:**

  | District | N kg/ha | Urea bags/ha |
  |---|---|---|
  | Dima Hasao | 205 | 9.9 |
  | Cachar | 189 | 9.1 |
  | Kamrup Rural | 139 | 6.7 |
  | Kamrup Metro | 129 | 6.2 |
  | West Karbi Anglong | 128 | 6.2 |

  These are hill districts, so mostly tree land, and they carry the V-02 caveat.

**In the app:**

- **District card:** a line on nitrogen, urea bags, rupees and mm of topsoil.
- **Priority list:** a "Nitrogen lost kg/ha/yr" column.
- **Village card:** a "Nitrogen washed off" tile (the place's local loss × its catchment's
  topsoil N), for example Diphu 13 kg/ha, Tezpur 14, Haflong 251 (steep, tree-covered).
- **"How to read this":** a paragraph that leads with the farmland figure and gives three
  cautions:
  - untreated land;
  - no enrichment counted;
  - tree land as a range.
- **Checks:** 23/23 screen cases pass.

**Why farmland leads.** On farmland the urea comparison is fair, and the figure does not hang
on the open forest question. It still assumes untreated fields (P = 1), so bunded paddies and
terraces lose less.

### 2026-10-29 · AD-28 part 1: heavy-erosive-week warnings — the rule and its bars, written before measuring

**What.** A short warning, per district, when the coming week's erosive rain is forecast to be
heavy. It uses the outlook's own figure: the week's erosive rain against normal for these
days.

**Why districts.** E2.2 found the outlook good at *when* and weak at *where within a week*
(G1 0.18), so warnings stay at district scale or wider.

**Rule, fixed now:**

- **Warn** a district when its forecast × normal ≥ **2.0**. This is the same cut that
  defined "heavy" in E2.2's G3.
- **And** the week's forecast erosive rain is ≥ **2% of a normal year**. That floor
  matches the average week (1.9%), so a dry-season week that is "3× normal" but tiny never
  warns.

**Judged on E2.2's replay** (44 Mondays, May–Sep 2024–25, 125 points, against IMERG). An
observed heavy point-week is one with observed × normal ≥ 2.0 and an observed share ≥ 2%.

| # | Measure | Bar |
|---|---|---|
| **W1** | Hit rate: the share of observed heavy point-weeks that the rule warned | **≥ 0.50** |
| **W2** | False alarms: the share of warned point-weeks that were not heavy | **≤ 0.50** |
| **W3** | Better than chance: hit rate minus false-alarm rate (Peirce skill) | **> 0.20** |

The judging is per point, because district aggregation is not in the replay. Districts are
averages of points, so they should do no worse.

**What follows:**

- **If W1–W3 pass:** the "This week" page shows the warning text for each warned district,
  with the replay's hit and false-alarm rates beside it.
- **If they fail:** no warning text, only the existing "× normal" map.
- In both cases, the channel to divisions (SMS / WhatsApp) is the department's choice.

### 2026-10-29 · AD-28 part 2: results — the warning rule FAILS; no warning text

`scripts/inspect/outlook_warning_check.py` → `reports/outlook_warning_check_assam.json`.

- **Input:** E2.2's replay point-weeks, now saved by `outlook_replay.py` to
  `replay_point_weeks.npz`. The replay report was rebuilt and is byte-identical.
- **Scale:** 5,500 point-weeks; 899 heavy; 626 warned.

| # | Result | Bar |
|---|---|---|
| W1 hit rate | **0.333** (299 of 899) | ≥ 0.50 ✕ |
| W2 false alarms | **0.522** (327 of 626) | ≤ 0.50 ✕ |
| W3 Peirce skill | **0.262** | > 0.20 ✔ |

**Reading it:**

- **Better than chance, not good enough to send.** Two in three heavy weeks would have been
  missed.
- **The forecast runs dry.** Its share of a year is 0.70× the observed (E2.2), so a 2×
  cut warns too rarely. Yet half of what it does flag is still not heavy.
- **Nothing ships:** the "This week" page keeps its "× normal" map and the replay grades
  only.

**A second attempt** needs its own pre-registration:

- a lower cut, fitted on 2024 and judged on 2025 only (no fitting and judging on the same
  weeks);
- or wait for the IMERG grid to finish, for a longer replay.

### How to run anything for Assam

```powershell
$env:REGION = "assam"          # PowerShell; unset it (Remove-Item Env:REGION) to go back
.venv\Scripts\python scripts\fetch\fetch_01_boundaries.py
.venv\Scripts\python scripts\build\make_folds.py
```

In Git Bash: `REGION=assam .venv/Scripts/python <script>`. With no REGION set, every
script runs for Arunachal exactly as before.

**The whole SoilSense chain, in order** (all with `REGION=assam`; the long fetches resume
where they stopped):

| Step | Script | What it makes | Time |
|---|---|---|---|
| 1 | `scripts/build/erosion_factors.py` | R, K, LS, C, the yearly loss map, classes | minutes |
| 2 | `scripts/inspect/check_erosion_bars.py` | Sanity checks S1–S8 | minutes |
| 3 | `scripts/model/erosion_priority.py`, then `scripts/model/erosion_rank_stability.py`; the AI map: `scripts/model/train_erosion_ai.py --full` then `scripts/model/erosion_ai_explain.py` | The ranked catchments and districts, causes, hints; then how firm each rank is (1,000 runs, joined onto the tables) | minutes |
| 4 | `scripts/fetch/fetch_48_dry_season_cover.py` | Dry-season bare ground 2019–2026 + Hansen test bands (Earth Engine) | 2–4 h |
| 5 | `scripts/build/cover_change.py` | Flags, tests F1/F2/H1, yearly loss; `--eyecheck` then `--score labels.csv` for E3 | 10 min |
| 6 | `scripts/fetch/fetch_49_nrsc_land_degradation.py` → `scripts/inspect/compare_nrsc_ld.py` | ISRO's land-degradation map; checks X1–X3 | 15 min |
| 7 | `scripts/inspect/measured_cover_test.py` | The held-out measured-cover test (E1.5 part 3) | 10 min |
| 8 | `scripts/fetch/fetch_50_erosion_rain_history.py` → `scripts/build/erosion_outlook_base.py` | The weekly outlook's fixed inputs | 15–60 min (rate limits) |
| 9 | `scripts/run/export_erosion_bundle.py`; `scripts/fetch/fetch_52_osm_places.py` + `fetch_53_geonames_places.py` → `scripts/build/erosion_places.py` | The app's files in `webapp/assets/erosion/assam/`; the village list | 5 min |
| 10 | `scripts/model/erosion_outlook_log.py` (`check` to verify) | Today's outlook, written down | 1 min |
| 11 | `scripts/run/check_app_screens.py`; `scripts/model/check_live_unchanged.py check` | Every screen opens; the live flood forecast unchanged | 10 min |
| 12 | `scripts/run/capture_soilsense_shots.py` → `scripts/run/build_proof_of_work.py` | Screenshots and the NESFIC Proof of Work PDF in `docs/nesfic/` | 5 min |

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
| **E0.2** | **Assam grid + boundary.** Freeze the spec (design §4.1: EPSG:32646, 100 m, origin 160,000 / 2,660,000, 6,400 × 4,400). State mask. Official boundary and current districts from the Assam State Geoportal (GADM as a stand-in until then) | `DATA_CONTRACT.md` §8 "Assam region"; state mask | In-state cell count recorded; area within 1% of 78,438 km²; spec written into DATA_CONTRACT | 0.5 d | ☑ |
| **E0.3** | **Fetch Assam raw.** DEM (~20 new tiles), SoilGrids (Assam box), WorldCover (1–2 tiles west of 90°E), HydroSHEDS clip (local), IMERG daily 2000-06 → now (~2 h) | Raw files + `_SOURCES.json` entries | Every raw folder has an Assam entry in `_SOURCES.json`; IMERG day count matches Arunachal's date range; no DEM holes inside the state | 1 d (mostly waiting) | ☑ |
| **E0.4** | **Build Assam backbone.** Terrain, hydrology (flow accumulation, channels, height above drainage), soil and land-cover features, rain stack | `data/interim/assam/…` | `check_terrain` / `check_hydro` / `check_rainfall` pictures reviewed for Assam; most plains cells < 2°; drainage follows the Brahmaputra and Barak | 1–2 d | ☑ |
| **E0.5** | **Freeze Assam validation folds** (50 km blocks, seed 42), hashed | `spatial_folds.meta.json` for Assam | Hash written **before any model exists**. Cheap now, impossible to do honestly later | 0.5 d | ☑ |
| **E0.6** | **The recipe** — `erosion_factors.py`. Build and debug on **Arunachal first** (can start day 1), then run on Assam. Confirm the R equation's units and coefficients, the K formula, the LS slope-length cap, and provisional classes (D4) | Soil-loss estimate + class rasters, **each factor saved separately**, both regions; unit suffixes per DATA_CONTRACT §5 | Both regions produce all five factor layers and the estimate; formulas and constants written into design §5.2 with sources | 2–3 d | ☑ |
| **E0.7** | **Pre-registered sanity checks** (bars below, written before running) | Results log entries | Every bar evaluated and logged; failures fixed or explained **before anything is shown to anyone** | 1 d | ☑ |
| **E0.8** | **First priority ranking** — `erosion_priority.py` on HydroBASINS level 12 and on districts; top 20 with main driver | Ranked tables | Top 20 checked by eye against satellite imagery: are they visibly steep and/or bare? Any that aren't, explained | 1 d | ☑ |
| **E0.9** | **App screen** — `webapp/products/erosion/` (status "building"), minimal region picker, map + ranking + "how to read this" note; bundle export | Running module | Runs locally; `check_app_screens.py` passes; screenshots taken for the application | 2 d | ☑ |
| **E0.10** | **Application pack** — screenshots, one-page method, requirements table (design §1), evaluation-criteria table (below), tier story, pilot proposal (D3), grant tier (D5) | Submitted application | Submitted before 25 Oct | 2 d | ◐ drafted, PDF built, not submitted |
| **E0.11** | **Access checks** (parallel, never blocking): NRSC land degradation (Bhuvan), SLUSI priority watersheds / Watershed Atlas, CWC / India-WRIS sediment, GloREDa, global soil-erosion map, NESDR land cover for Assam, Assam State Geoportal. Use the "portals look closed but aren't" method (test the machine endpoints, not the UI) | Status column in design §12 filled in | Each source marked *open / gated / closed* with the working access route | ~1 d, spread out | ◐ NRSC land degradation (Bhuvan) and CWC sediment found open; the rest not checked |

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
| **E1.1** | Sentinel-2 seasonal composites via Earth Engine, 2019 → now (pre-monsoon, post-monsoon, winter) → C per season; cloud share recorded per composite | Every season has a C layer or an explicit "too cloudy" gap; fallback C used only in the gaps | ◐ dry season 2019–2026 done; other seasons not (V-23) |
| **E1.2** | **Specificity test first:** run the change detector on known no-change areas (core forest, long-stable farmland) | False-flag rate measured and below a bar written before running. Only then does E1.3 ship any flag | ☑ F1, F2 pass |
| **E1.3** | Change maps: same season year on year; year vs year; "new bare ground on a steep slope" flags | Change layers in the app; flags spot-checked against imagery | ◐ change maps in the app; flags held back (H1, E3 failed) |
| **E1.4** | R upgrade: half-hourly IMERG for a sample of monsoons → event erosivity. Compare with the annual relation and GloREDa, then choose | Choice and comparison logged; design §5.2 updated | ☐ |
| **E1.5** | V2 cross-map agreement (whichever sources E0.11 opened) | Rank agreement per district / watershed logged against pre-written bars | ☑ done; X1–X3 failed |
| **E1.6** | V3 measured-sediment ranking test (if data opened) | Catchment rank agreement logged, or "no data" logged | ☑ logged: not possible on the Assam-only map (V-22) |
| **E1.7** | V4 blind imagery sample, ~300 points stratified by class | Labels made blind; metric vs bar logged | ☐ |
| **E1.8** | Planning units: Watershed Atlas micro-watersheds if obtained, else stay on HydroBASINS level 12 | Ranking runs on the chosen unit | ☐ |
| **E1.9** | Conclave demo build | Demo runs offline-safe with Assam data | ☐ |

---

## Phase 2 — Prototype (mid-Dec 2026 → Demo Day, Feb 2027)

**Goal:** the module does what the department asked: ranked, explained, periodically
updated, field-ready, with the pilot's field comparison designed and agreed.

| ID | Task | Done when | Status |
|---|---|---|---|
| **E2.1** | Weekly outlook: next-7-day erosivity from the live rain × current K·LS·C·P. Runs inside the existing 08:30 daily job; logged like FloodSense | A week of logged outlooks on disk; `check_live_unchanged.py` still passes for floods | ◐ built and logged locally; not yet in the 08:30 cloud run |
| **E2.2** | Grade the rain part daily (forecast erosive rain vs observed IMERG) | Running scorecard; method page says plainly that the soil-loss part is not gradable at FREE tier | ◐ replay graded (G2, G3 pass; G1 fails); daily grading not running |
| **E2.3** | Place card, priority list with reason line and treatment hint, change view, adjustable weights | All screens in the app; kinds-of-number badges on every figure | ☑ reason line, treatment hint, change view, village card, adjustable weights |
| **E2.4** | Field kit: GeoPackage / KML / CSV export; field-check form → records, quarantined before joining authoritative data | Round trip tested: export → fill in → import → appears flagged as unverified | ◐ exports and field points done; form round trip not |
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
| 2026-10-25 | V-18 | Second reason against similar slopes (5 slope groups), treatment hints | Ranks unchanged (703 units, 0 differences). Top 20: heavy rain 17, bare or thin cover 1, nothing stands out 2. All 703: heavy rain 270, nothing 260, cover 173 | Reading aid, no bar |
| 2026-10-25 | E2.4 (part) | Field kit, first version | 100 points (top 20 catchments × 5, ≥ 500 m apart); CSV with form columns, GPX, KML; GeoPackage with catchments, districts and points (1.46 MB); KML and GPX parse; 7/7 SoilSense screens pass | Done (export side) |
| 2026-10-25 | E1.5 (V2) | Against NRSC Land Degradation 1:50k 2015-16 | X1 AUC 0.661 (IWED 0.419, slope alone 0.651); X2 ρ 0.36 (IWED −0.30, slope 0.44); X3 ρ 0.13 (IWED −0.36, slope 0.36). 79% of NRSC-eroded land is tree; on steep tree land median A 54.5 eroded vs 60.5 normal | X1–X3 all FAIL (bars 0.70 / 0.40 / 0.50) |
| 2026-10-26 | E1.1–E1.3 | Dry-season bare ground 2019–2026; change flags | Evaluable 99.6–100% of scored land every year; steep land bare 1.03–1.94% (2025 highest); F1 0.05% ✔, F2 1.79% ✔, H1 47.6% ✕, E3 flags 57.5% (69.7% readable) ✕, unflagged 2.6% ✔ | Flags NOT shown; bare-ground layer shown |
| 2026-10-26 | E1.5 part 3 | Measured cover vs NRSC, calibrate folds 0–1, judge folds 2–4 | X1 cal: main 0.700, M1 0.697, M2 0.619 → nothing goes forward. Test half: main 0.629, M1 0.626, M2 0.558. Inside tree land, mean bare share alone vs NRSC eroded: AUC 0.451 | NOT adopted |
| 2026-10-26 | E2.1 | Weekly outlook, first live issue (week 26 Oct – 1 Nov) | 248 points; typical Jun–Aug week 4.2% of a year (average 1.9%); this week 0.11× normal, 0.10% of a year, 0.021 t/ha; issue rebuilds exactly | Built; not graded |
| 2026-10-26 | E1.3 attempt 2 | Flags with an NDVI drop ≥ 0.20, new blind sample (seed 43) | F1 0.03% ✔, F2 0.90% ✔, H1 44.4% ✕, E3 flags 62.5% (75.8% readable) ✕, unflagged 2.8% ✔; flags 4,062–10,069 ha/yr | Flags stay held back |
| 2026-10-26 | V-17 part 2 | Rank stability, 1,000 runs (R blend, tree C 0.003–0.1, class C ±50%, McCool/Nearing) | Robust (≥ 80% top 20): 3; ≥ 50%: 15; main top-20 median 66%; two-map mark firm 76.5% vs rain-dependent 32.8% | Reported, no bar |
| 2026-10-26 | E2.3 | Village card | 2,589 places (OSM 1,389, GeoNames 1,165, SoI HQ 35; 23 Assamese names); figures over a 2.1 km square; 15/15 screen cases incl. 3 card cases | Built |
| 2026-10-26 | E2.2 | Outlook replay inputs | Open-Meteo archived forecasts: 125 points, May–early Oct 2023–25; leads 1–6 missing for 2023 (archive starts May 2024). IMERG 2023–25 requests all failed (0 of 200), fetch stopped | Grading blocked |
| 2026-10-26 | E2.3 | Adjustable ranking weights | Default weights reproduce the main ranking exactly (0/703 differ after the tie-break; 364 before); 'getting barer' known for 281 catchments | Built |
| 2026-10-26 | E2.2 | IMERG access for the replay's truth | 2001 downloads worked until about 13:05; after that every request (2013–2025) returned no data ("no version resolved"), so it is access, not versions. Only 56 Assam days on disk (2001) | Grading blocked: check the NASA Earthdata login / GES DISC status, then re-run `fetch_11b` 2023 2025 and 2013 2022 |
| 2026-10-26 | E2.2 | Outlook replay, 44 weeks (2024–25), 125 points, IMERG V07 Final | G1 0.181 (clim 0.115) ✕; G2 0.633 (clim 0.389) ✔; G3 AUC 0.765 ✔; forecast/observed share 0.701 | 2 of 3 pass |
| 2026-10-27 | AD-01 | AI erosion map (LightGBM on NRSC eroded vs normal), OOF on 50 km folds | AUC set A 0.8202 (B 0.823; formula 0.6603; slope 0.6503); catchment ρ 0.6586 (formula 0.3584); folds 0.72–0.92 | AI-1 ✔, AI-2 ✔: ships beside the formula; AD-05 judges |
| 2026-10-27 | AD-25 | Sediment connectivity / delivery (Borselli IC, InVEST SDR) | SDR median 0.040; state 7.8 of 118 Mt/yr (7%) delivered; top districts Dima Hasao 3.76, W. Karbi Anglong 3.27, Cachar 3.03 t/ha | Built, untested |
| 2026-10-27 | AD-02 | Outlook erosive-rain anomaly vs CWC river-mud anomaly, 11 stations, 2010–26 | ρ > 0 at 82%; median ρ 0.072 (next week 0.112); plain rain 0.067 | M1 ✕ (strength), M2 ✔ |
| 2026-10-27 | AD-06 | AI river-mud model (LightGBM, weekly mud anomaly) | by year -0.036, by station 0.101; baseline 0.071 | ✕ not adopted |
| 2026-10-28 | AD-05 / AD-30 | Blind picture check, 300 Esri squares (seed 7), one labeller, key opened after all labels | Labels: none 274, erosion 19, gully 1, can't tell 6. P-F 7.7% vs 2.5% = 3.08× (Fisher p 0.13); P-AI 3.3% vs 3.2% = 1.03×; P-G 16.7% vs 20.0% = 0.83×; AUC formula 0.616, AI 0.628 | P-F ✔ (weak); P-AI ✕; P-G ✕; AI not better. AI kept as a second opinion; gully-prone not adopted |
| 2026-10-28 | RC | Sentinel-2 river colour (red, NDWI water, 300 m) vs CWC same-day mud, 25 stations, 2017–2026, 9,420 clear dates | RC1 median ρ 0.328 (96% positive); RC2 seasonal 0.143; RC3 6 clear monsoon dates/yr; monsoon-only ρ 0.03; wide rivers best (Pandu 0.56) | RC1 ✕, RC2 ✕, RC3 ✔: not adopted |
| 2026-10-29 | AD-28 | Heavy-week warning rule (forecast ×normal ≥ 2 and share ≥ 2%) on E2.2's replay, 5,500 point-weeks | hit rate 0.333, false alarms 0.522, Peirce 0.262 | W1 ✕, W2 ✕, W3 ✔: no warning text |
| 2026-10-28 | AD-06 v2 | Daily AI river-mud model (IMERG rain + CWC river height), 12 stations, 34,792 station-days, 2013–2025 | by year 0.138, by station 0.204; height alone 0.242; erosive rain alone 0.059; nowcast 0.150 / 0.209 | ✕ not adopted; WHEN parked until sensors or flow |
