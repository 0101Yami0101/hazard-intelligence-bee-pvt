# Learning roadmap — from zero to CTO-level on this project

> For one reader: the person who has to run this platform as CTO and tech lead, and answer
> any question from APSAC, GSI, CWC, the Soil Conservation Department or a reviewer.
> Written 2026-10-31. About **4 weeks full-time** (5–6 hours a day) or **7–8 weeks part-time**.
> A 10-day fast track is at the end.

## What "done" looks like

You are there when you can do all five without opening a file:

1. **Tell the story in 3 minutes**: the data backbone, the three modules on top of it, and
   why it moved to a second state.
2. **Trace one square of ground** from raw download to the colour on the app's map, for
   each module.
3. **Defend every headline number**: where it came from, how it was tested, what it does
   *not* mean.
4. **Name the dead ends**: what was tried, why it failed and what would unblock it. Experts
   trust you more when you know what does *not* work.
5. **Ship a change yourself**: rebuild a bundle, run the screen checks, push to `v2`, and
   check the daily cloud run still works.

## How to learn it fast

- **Learn in layers, top-down.** Start with the story, then the data, then each model, then
  how it was proven, then the app and operations. Don't open code until you know what it is
  for.
- **Read the status first, the history second.** The big plans (FLOOD_WHEN_PILOT_PLAN is
  nearly 3,000 lines) are logs. Read the top status section and the "done" headings, and
  skip the step-by-step detail unless a question sends you there.
- **Run things.** Each phase has one hands-on exercise, and one exercise teaches more than
  ten pages of reading.
- **Teach it back.** At the end of each phase, explain it out loud or in writing to an
  imaginary APSAC scientist. Wherever you stall, you have a gap.
- **Use the codebase map** (`docs/codebase-map/index.html`) as your atlas: the journeys,
  the files and who calls what.
- **Use Claude as an examiner.** Say "quiz me on phase 3 like a GSI geologist". Ask for
  hostile questions, not friendly ones.

---

## Phase 0 — The big picture (day 1)

**Read**

| Order | File | Why |
|---|---|---|
| 1 | `docs/BRIEFING.md` | The whole idea, backbone first |
| 2 | `README.md` | Modules, folders, how to run |
| 3 | `docs/design/PLATFORM_ARCHITECTURE.md` | How the shared core and the modules fit together |
| 4 | `docs/PRESENTATION_SCRIPT.md` | How we pitch it, so you speak the same language |
| 5 | `docs/design/DESIGN.md`: skim headings only | The original design and its vocabulary |

**Do:** run the app locally (`streamlit run webapp/app.py`) and click every page of every
module. Write one line per page saying what it tells the user.

**Check yourself**
- What is the data backbone, and why is it the main product rather than any one forecast?
- What are the three modules, and what question does each answer?
- What is the difference between "where" (susceptibility) and "when" (trigger), and why
  does the product talk about forecasts?

---

## Phase 1 — The science you need underneath (days 2–4)

Learn just enough to talk to the scientists. These are standard topics, so read any good
summary or textbook chapter.

| Topic | Enough to explain… | Good starting point |
|---|---|---|
| Landslide susceptibility | Terrain + soil + cover → where slides happen; usual model types | Reichenbach et al. 2018, *A review of statistically-based landslide susceptibility models* |
| Rainfall thresholds | Intensity–duration and antecedent rain as triggers | Guzzetti et al. 2007/2008 on rainfall thresholds |
| Hydrology from a DEM | Flow direction, flow accumulation, catchments, HAND (height above nearest drainage) | Nobre et al. 2011, the HAND paper |
| Flood forecasting | Gauges, danger levels, lead time; how Google Flood Hub works | Nearing et al. 2024 (Nature), plus our memory note on Flood Hub |
| Soil erosion (RUSLE) | A = R·K·LS·C·P, what each factor is, and why the answer is "if untreated" | Renard et al. 1997 (USDA Handbook 703) |
| Remote sensing | Sentinel-1 radar sees water through cloud; Sentinel-2 sees cover; IMERG is satellite rain | ESA and NASA product pages |
| ML evaluation | AUC, calibration, base rate, spatial cross-validation, leakage, out-of-distribution | Any applied-ML text; then our own docs |

**Check yourself**
- Why is a high AUC on a susceptibility map not proof that a forecast works?
- Why is the max of 97 percentile scores not a probability? (See memory "percentile max".)
- Why does radar beat optical satellites for flood mapping in the monsoon?

---

## Phase 2 — The data backbone (days 5–8)

**Read**
- `docs/design/DATA_CONTRACT.md`: the grid, the projection and the layer rules. This is
  the backbone's law.
- `docs/data_research/Base.md` and `Appendix.md`: every source we considered.
- `docs/data_research/DATA_VERIFICATION.md`: what we checked about each source.
- `docs/design/GOV_DATA_REQUEST_LIST.md`: what we still want from government, and why.
- `docs/design/RAINFALL_FEATURES.md` and `RAINFALL_RESOLUTION_LIMITS.md`: rain as an input,
  and its honest limits.

**Code** (open in this order)
- `scripts/common.py`: paths, `REGION`, shared settings.
- `scripts/build/grid.py`: the grid every layer snaps to.
- `scripts/fetch/fetch_01…56`: skim the names, then read 02 (terrain), 04 (land cover),
  11 (IMERG), 21 (CWC gauges) and 42 (erosivity) properly.
- `scripts/build/terrain.py`, `hydrology.py`, `features.py`, `assemble.py`.
- `scripts/build/build_backbone_bundle.py`, then `webapp/products/backbone/`.

**Do:** pick one village. Find its grid square and list every layer value for it: slope,
soil, cover, HAND, rain normal. For each value, write the source and the date.

**Check yourself**
- Which sources are open, which need asking, and which are paid? (Tiers: FREE / ASK / PAID.)
- How did the backbone move to Assam? What did `REGION=assam` have to change, and what
  didn't it?
- Which government portals look closed but are not? (See memory "gov portals".)

---

## Phase 3 — SlideSense, the landslide module (days 9–13)

**Read**
- `MODEL_SUSCEPTIBILITY.md`: the "where" model.
- `LABELS_AND_SAMPLING.md`: the 35,744 landslide labels, and how "no-slide" points were
  chosen.
- `MODEL_TRIGGER_AND_HAZARD.md`: the "when" part, and how the two combine.
- `BACKTEST.md`, `LEAD_DAY_TEST.md`, `LANDSLIDE_TIMES_USUAL.md`, `FORECAST_REPORT.md`.
- `GSI_MAP_COMPARISON.md`: our map against GSI's.
- `TEMPORAL_INVENTORY_ATTEMPTS.md`, `PX0*`, `PX1_MAGNITUDE_FEASIBILITY.md`: the dead ends.
- `PARKED_HIMALAYAN_POOLED_TRIGGER.md`, `ROADMAP_LANDSLIDE.md`, `PILOT_TAWANG.md`.
- `SLIDESENSE_SCREEN.md`.

**Code:** `scripts/build/labels.py`, `sample.py`, `make_folds.py` →
`scripts/model/train_susceptibility.py`, `predict_susceptibility.py` → `trigger.py`,
`hazard.py` → `backtest.py` → `webapp/products/landslide/`.

**Do:** re-run the backtest and read every number it prints.

**Check yourself** (these are the questions a GSI scientist will ask)
- Why trees and not deep learning? (Our shortage is dated events, not labels.)
- Only about 90 day-dated events exist. What does that rule out, and what did we try to get
  more? (Five routes, all closed.)
- Why are Bhuvan's 11,329 season-dated slides real but still not useful as training labels?
- Why doesn't constrained negative sampling help in steep terrain (0.860 vs 0.862)?
- Why is a magnitude (size) forecast closed?

---

## Phase 4 — FloodSense, the flood module (days 14–19)

This is the deepest module. Give it the most time.

**Read**
- `FLOOD_MODULE.md`: the design.
- `FLOOD_WHEN_PILOT_PLAN.md`: read §0–§2 and §10 (calibration) in full. For §13–§20, read
  the opening paragraph of each and its result.
- `PARKED_HIMALAYAN_FLOOD_WHERE.md` §0: how WHERE became a real probability, and the
  out-of-distribution trap (glacial lakes read as floodplain).
- `OLDER_FLOODS_TEST.md`, `SOIL_WETNESS_TEST.md`, `RAIN_GAUGES.md`.
- `RIVER_FORECAST_RECAP_2026-10-06.md`: the level line in one place.
- `FLOOD_SCREEN_PLAN.md`: skim it for why each screen looks the way it does.
- `FLOOD_HUB_AND_MOCKUP_COMPARISON.md`: us against Google.

**Code**
- Labels: `scripts/build/build_verified_floods.py` and the Sentinel-1 evidence scripts in
  `scripts/model/sentinel1_flood_evidence*.py`.
- WHERE: `build_flood_where_samples.py` → `train_flood_where.py` →
  `calibrate_flood_where.py`.
- WHEN: `train_flood_when.py`, `train_flood_when_gauge.py`, `calibrate_flood_when.py`,
  `gauge_week.py`.
- Live: `flood_forecast_live.py`, `flood_gauge_live.py`, `forecast_log.py`, then
  `scripts/cloud/modal_daily.py`.
- App: `webapp/products/flood/` (`ui.py` holds the shared look).

**Do:** run one day's forecast by hand and find today's entry in the self-grading log.

**Check yourself**
- Why build our own model instead of feeding from GloFAS or Flood Hub?
- How was the 2,185-flood verified record built, and why did the old radar screen fail
  (it passed 97–100% of flood-free dates)?
- What is the level line, how far ahead does it go, and which gate did it fail before the
  user adopted it anyway?
- What is the high-river fault, and why are rivers sitting on their danger line the hard
  case?
- Why does soil wetness help on flat ground only?
- What did the gauge spike filter catch? (One wrong reading looked like a 52% flood.)

---

## Phase 5 — SoilSense, the erosion module (days 20–23)

**Read:** `SOILSENSE.md` → `EROSION_MODULE.md` → `EROSION_PLAN.md` (status at a glance and
the revisit register; dip into the build log only when needed) → `ROADMAP_EROSION.md` →
`SOILSENSE_FULL_LIST.md` → `NESFIC_D07_FINAL_ANSWERS.md`.

**Code:** `scripts/build/erosion_factors.py` → `erosion_connectivity.py`,
`erosion_treatment.py`, `cover_change.py` → `scripts/model/erosion_priority.py`,
`erosion_rank_stability.py`, `train_erosion_ai.py` → `scripts/run/export_erosion_bundle.py`
→ `webapp/products/erosion/`.

**Do:** rebuild the Assam bundle (`REGION=assam`, the three commands in `SOILSENSE.md`).
Then compare one catchment's rank under both rain maps.

**Check yourself**
- Which RUSLE factor is unknown, and why is every number "if untreated"?
- Why use InRESatE for rain strength and not the Singh formula (which reads 91% low)?
- What is held back (change flags, river-mud WHEN, tree split, gully flag), and what bar
  did each miss?
- How firm is a catchment's rank, and how do you show that to an officer?

---

## Phase 6 — The app and operations (days 24–26)

**Read:** `WEBAPP_PLAN.md`, `webapp/DEPLOY.md`, `LANDING_PAGE.md`,
`PARKED_OFF_PC_DAILY_RUN.md`.

**Code:** `webapp/app.py` → `webapp/core/` (`shell.py`, `bundle.py`, `mapping.py`,
`rainfall.py`, `landing.py`) → `webapp/products/__init__.py` (how modules register) →
`scripts/run/export_webapp_bundle.py`.

**Know the release path**
- There are two Streamlit apps. The old one follows `slopesense2` `main`; the new one
  follows the `v2` branch on `hazard-intelligence-bee`.
- `v2` holds app files only. `records/` and `flood_intake.py` never go there.
- Before any push: run `scripts/run/check_app_screens.py`, plus
  `scripts/model/check_live_unchanged.py check` after any change to shared code.
- The daily run is on Modal at 08:30 IST under the `pankajkarjay` profile. Redeploy it
  after any model or code change.

**Do:** with me watching, do one full `v2` deploy yourself from start to finish.

**Check yourself:** What breaks if Open-Meteo rate-limits us? What happens if the Modal run
fails one morning? What is on the free tier's memory budget?

---

## Phase 7 — Defending it in the room (days 27–30)

**Read**
- `docs/BEYOND_PRESENTATION.md`: the question bank, including the "keep back" lines.
- `COMPETITOR_IIOTS.md`, `COMPETITOR_ALERTIS.md`.
- `ENSEMBLE_STRATEGY.md`, `REMAINING_WORK.md`, `CEO_PILOT_NEXT_STEPS.md`, `PROJECTED.md`.
- `GOV_DATA_REQUEST_LIST.md`, read again for the agency meeting.

**Do**
1. **Build your numbers card.** Use one page and list every headline number with its source
   file and what it does *not* mean. To start: 35,744 labels; ~90 dated landslide events;
   2,185 verified floods; flood timing 0.706 → 0.845 (verified record) and 0.851 → 0.879
   in Arunachal (from 2003); 17 gauges with a level line; 703 catchments, 35 districts and
   2,589 places in Assam. Find the source of each one yourself, because that is the exercise.
2. **Build your limits card.** For every limit, name the tier that lifts it (FREE, ASK or
   PAID), and keep physics limits apart from budget limits.
3. **Hold two mock grillings** with Claude playing an APSAC remote-sensing scientist, then
   a CWC hydrologist. One hour each, hostile questions only.

---

## The 10-day fast track

If a meeting is coming:

| Day | Do |
|---|---|
| 1 | Phase 0 in full |
| 2 | Phase 1: susceptibility vs trigger, RUSLE, AUC vs calibration only |
| 3 | DATA_CONTRACT + GOV_DATA_REQUEST_LIST + village-trace exercise |
| 4–5 | SlideSense check-yourself questions, answered from the docs |
| 6–7 | FloodSense: FLOOD_MODULE, RIVER_FORECAST_RECAP, calibration §10 |
| 8 | SoilSense: SOILSENSE.md + EROSION_MODULE + final answers |
| 9 | BEYOND_PRESENTATION + numbers card + limits card |
| 10 | Mock grilling, then fill the gaps it found |

## Keeping it current

The project moves weekly. Each Monday, read `git log` for the past week, the status lines at
the top of the three plan files, and any new memory notes. Then update your numbers card.
