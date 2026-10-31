# Roadmap — what to add to SoilSense, AI and otherwise, in priority order

**Written 2026-10-26.** A ranked list of everything worth adding to the erosion module
(SoilSense, NESFIC-D-07, Assam), with AI items and non-AI items in one list.

**Companion docs:** [EROSION_MODULE.md](EROSION_MODULE.md) says *why* the module is built
the way it is. [EROSION_PLAN.md](EROSION_PLAN.md) is the working plan: its task IDs (E…),
revisit register (V-…) and results log stay the record. This file says *what to add next,
and in what order*. When an item here starts, it gets a task row and pass marks in the plan.
Every pass mark below is a **proposal**; it is frozen in the plan before anything runs.

---

## 0 · The short version

**The rule is the same in all three modules: use AI where real examples exist to learn
from, and a formula where they don't.** Today SoilSense has no AI because we believed it
had no examples. Two sources found or re-read this week change that:

1. **ISRO's land-degradation map (NRSC, 2015–16)** marks eroded land across Assam, drawn by
   experts from satellite pictures. That is the same kind of example SlideSense learned
   from (landslides marked from satellite pictures). → an **AI WHERE** for erosion.
2. **The river agency's (CWC) daily river-mud readings.** 30 Assam stations from 1979 to
   2025, and 26 stations from January to **13 October 2026**, open. That is measured truth for
   *when* soil washes off. → the weekly outlook **can be checked**, and an **AI WHEN** can
   learn from it.

> **Correction.** EROSION_PLAN.md (the outlook's "kind of number", E2.2) and
> `erosion_outlook_log.py` say the outlook's soil part *cannot be graded with open data*.
> That is wrong for any catchment that drains to a CWC sediment station. The rain part
> can also be graded against ground gauges, not only satellite rain.

### The list at a glance

| # | What | AI? | When |
|---|---|---|---|
| **Priority 1: before submission (target 7 Nov; closes 10 Nov)** ||||
| AD-01 | AI erosion map, learned from ISRO's eroded-land map | **Yes** | P1 |
| AD-02 | Check the weekly outlook against measured river mud, 2000–2026 | No | P1 |
| AD-03 | SoilSense on the public app; outlook in the 08:30 cloud run | No | P1 |
| AD-04 | Grade the outlook's rain against ground rain gauges, daily | No | P1 |
| AD-05 | Blind picture check of the map, ~300 points (the independent judge) | No | P1, if time |
| AD-06 | AI WHEN: learn river mud from rain and ground | **Yes** | P1 stretch, else first in P2 |
| AD-07 | Put the results into the application and the Proof of Work PDF | — | P1, last |
| **Priority 2: before Demo Day (Feb 2027)** ||||
| AD-08 | AI satellite reader: forest / tea / *jhum* / village grove / fresh clearing | **Yes** | P2 |
| AD-09 | AI second look for the "newly cleared slope" alerts | **Yes** | P2 |
| AD-10 | AI-corrected rain strength from ~80 ground gauges | **Yes** | P2 |
| AD-11 | Extend the map to a North-East region (the measured-mud ranking test) | No | P2, user's call |
| AD-12 | Field-check return form (findings flow back in) | No | P2 |
| AD-13 | Adjustable priority weights, plus what lies downstream | No | P2 |
| AD-14 | Weekly advisories for farmers and communities, in local languages | AI for wording only | P2 |
| AD-15 | Post-monsoon season; official micro-watersheds; offline demo | No | P2 |
| **Priority 3: pilot and MVP (Feb–May 2027): needs the department or a budget** ||||
| AD-16 | Pilot field comparison, then an AI correction layer from field findings | **Yes** | P3 |
| AD-17 | Farmers' photo reports, sorted by AI, confirmed by a person | **Yes** | P3 |
| AD-18 | Gully finder on high-resolution imagery (deep learning) | **Yes** | P3 |
| AD-19 | Rain-intensity and stream-muddiness sensors at 2–3 outlets (IoT) | Feeds AD-06 | P3 |
| AD-20 | Department data in: soil survey, treated areas, gauges; "did the works help?" | Optional | P3 |
| **Priority 4: later, or belongs to another problem statement** ||||
| AD-21 | Riverbank erosion watch (Brahmaputra, Barak) | Optional | P4 |
| AD-22 | SlideSense and FloodSense for Assam | Yes (exists) | P4 |
| AD-23 | Smaller ideas: soil carbon lost, bare-earth ground model, river colour from space | Mixed | P4 |
| **Added 2026-10-27 for the application's wider offer (§6b)** ||||
| AD-24 – AD-36 | Pre-monsoon watch list, works planner, "did the works help?", offline field app, voice/SMS advisories, district bulletins, map feeds, soil-loss plots, climate futures, scheme-ready outputs, training and handover, other North-East states, open publication | Mostly no | Programme or beyond |

---

## 1 · Where SoilSense stands against the other two modules

| | WHERE (which places) | WHEN (which days) |
|---|---|---|
| **SlideSense** | AI (tree model, LightGBM), learned from 35,744 mapped landslides (Bhuvan); spatial-fold AUC 0.860 | **Not AI:** an unfitted rain score (3- and 7-day rain, as percentiles of each cell's own history). About 90 dated events exist; fitting on them did worse than not fitting (0.768) |
| **FloodSense** | AI (tree model), learned from satellite flood maps, calibrated | AI, learned from 2,185 verified floods and the river gauges; graded daily |
| **SoilSense today** | Formula (RUSLE) | Formula (forecast rain → erosive rain, InRESatE's daily model) |
| **SoilSense after P1** | Formula **and** AI side by side (AD-01) | Formula, checked against river mud (AD-02); AI if AD-06 passes |

The formula stays even where AI is added. It gives the tonnes and *why* a place is high,
and the department recognises it. The AI gives a second rank, learned from real examples.
Agreement between the two is shown, and so is disagreement. This is the ensemble rule
already decided for the platform ([ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md)): keep
the two side by side and judge them as a pair.

---

## 2 · How the items were ranked

1. **Does it answer the department or the judges?** The judging headings on the NESFIC
   site are Problem Fit, Innovation & Merit, Maturity, Feasibility, Impact, and Team &
   Presentation. The challenge page tags AI & Machine Learning, Environment & Land, GIS
   Mapping, IoT & Sensors, and Satellite & Remote Sensing.
2. **Can it be done on free data now?** Anything needing the department or money waits.
3. **Is it honest?** AI only where real examples exist. Every pass mark is written first and
   judged on data the model never saw.
4. **Effort against the time left.** About 12 days to the 7 Nov target. Effort figures
   below are rough working days.

---

## 3 · Priority 1: before submission

If time runs short, stop after AD-04. The rest move to Priority 2, and the application
lists them as planned.

### AD-01 · AI erosion map, learned from ISRO's eroded-land map — **AI**

- **What.** A tree model (the same kind and the same honest-training pattern as SlideSense,
  `train_susceptibility.py`) learns which 100 m squares ISRO's experts marked as eroded.
- **Examples (labels).** NRSC Land Degradation 1:50k, 2015–16 (`fetch_49`, already on our
  grid). Eroded = codes 2–7 (sheet moderate/severe, rills, gullies, ravines): 3,303 km²,
  about 330,000 squares. Normal = code 8: 49,288 km². Slight sheet erosion (1) and other
  degradation (9) are left out, the same definitions as check X1.
- **Inputs.** Everything already on the Assam grid: slope, curvature, relief; flow
  accumulation, height above drainage, wetness; 18 soil layers; land cover; rain strength
  (InRESatE); canopy height (Meta, ETH); forest-loss shares (Hansen). Also the formula's own
  factors, so the AI can show what it adds on top.
  - **Time trap:** NRSC drew 2015–16. Our dry-season bare-ground layer starts in 2019, and
    Hansen's loss shares are 2021–2025. Run the model with and without the post-2016 layers
    and report both; lead with the version without them.
- **Test (proposed).** Out-of-fold scores on the frozen 50 km Assam folds: every square is
  scored by a model that never saw its block.
  - Pass: X1 AUC ≥ 0.70, beating both the formula (0.661) and slope alone (0.651) by ≥ 0.03
    on the same squares.
  - Catchment rank X2 ρ ≥ 0.40.
  - Independent judge: AD-05, because NRSC can no longer judge a model trained on it.
- **What it gives.** An AI WHERE like the other two modules. It also shows *what the formula
  misses*: 79% of NRSC's eroded land is tree land, where our formula is weakest, and
  measured bareness did not explain it (E1.5 part 3, AUC 0.451).
- **In the app.** "AI rank" beside the formula's rank, with agreement marked.
- **Limits.** It learns NRSC's eyes in one survey year (2015–16, 23.5 m imagery), habits
  included, just as SlideSense learned Bhuvan's mappers.
- **Decision.** NRSC is "comparison only, never redistributed" in EROSION_PLAN (V-26).
  Training on it changes that role; see §7.
- **Effort.** 1–2 days.

### AD-02 · Check the weekly outlook against measured river mud — not AI

- **What.** Rebuild the outlook's erosive-rain number for every week from 2000 to 2026, and
  check it against the river mud CWC measured downstream.
- **Data.**
  - CWC daily suspended sediment (g/L), open on NWDP (`fetch_46`). Assam: 30 stations,
    1979-04-26 → 2025-12-31, 220,442 readings. A 2026 file: 26 stations to 2026-10-13.
    Readings fall evenly across all 12 months, so the dry season is covered too.
  - Station catchments are already traced (`reports/sediment_station_catchments.csv`).
  - Satellite daily rain (IMERG) for Assam is not fetched yet (V-15, about 2 h). Catchments
    reaching into Meghalaya, Nagaland, Manipur and Mizoram need a larger box.
- **Method.** For each station: daily erosive rain over its catchment (EI = a·P^b, the
  outlook's own model), summed by week. Compared with that week's and the next week's mean
  mud, both as departures from the usual for the time of year.
  - Where the catchment lies inside our map (Kopili at Jagibhakatgaon, 81% in Assam; Gaurang
    at Kokrajhar, 72%), the soil-at-risk version is checked too.
- **Test (proposed).**
  - Wetter-than-usual erosive weeks should be muddier than usual.
  - Pass: the two departures have Spearman ρ > 0 at ≥ 2/3 of stations, with median ρ ≥ 0.3.
  - Baseline: the outlook must beat plain weekly rain.
- **What it gives.** The outlook moves from "not graded" to "checked against measured river
  mud at N stations over up to 26 years". The 2026 file is about a week behind, so live
  grading can follow.
- **Limits.**
  - Concentration only: CWC publishes no river flow for Assam, so no tonnes.
  - River mud also comes from banks and channels.
  - Stations sit on medium rivers, so this checks timing per catchment, not per field.
- **Effort.** 1–2 days after the rain fetch.

### AD-03 · SoilSense on the public app; outlook in the cloud run — not AI

- **What.**
  - Publish the erosion module on the public `v2` app, so the application's demo link works.
  - Add `erosion_outlook_log.py` to the 08:30 Modal job, so the outlook is issued and logged
    every day off the PC.
- **Why.** Maturity: judges can open it. A daily log is what any later grade stands on.
- **How.** The `v2` branch routine in DEPLOY.md, and the Modal redeploy. Then run
  `check_live_unchanged.py` and confirm the flood run is untouched.
- **Needs.** The user's go-ahead for both.
- **Effort.** 0.5–1 day.

### AD-04 · Grade the outlook's rain against ground gauges, daily — not AI

- **What.** Reuse the flood module's forecast-rain grading (RAIN_GAUGES.md Part D,
  `scripts/inspect/grade_forecast_rain.py`) for the Assam outlook points, against CWC's
  ground rain gauges, which run to October 2026. IMERG is the second reference once fetched.
- **Why.** "Checked daily" for the rain part, at almost no cost.
- **Effort.** 0.5 day.

### AD-05 · Blind picture check of the map, ~300 points — not AI

- **What.** Plan task E1.7 (V4). About 300 squares, spread across the classes, are shown as
  dated satellite pictures with neutral ids. Each is labelled by eye (visible rills,
  gullies, bare slope, or not) before the key is opened. The `--eyecheck` / `--score`
  workflow exists.
- **Why now.** Once AD-01 trains on NRSC, this is the only independent judge for both the
  formula and the AI.
- **Test (proposed).** The high classes show visible erosion more often than the low
  classes, by a margin frozen first. The formula and the AI are scored on the same pictures.
- **Effort.** 1–2 days, mostly labelling.
- **Done 2026-10-28** (EROSION_PLAN.md, "AD-05 and AD-30 part 2"). 300 pictures, 20 show
  erosion.
  - **Formula:** meets its bar (3.1×, bar 2×), but not firmly.
  - **AI:** no better than the formula on visible ground (AUC 0.63 vs 0.62). It is kept as a
    second opinion that follows ISRO's map.
  - **Gully-prone ground (AD-30):** 0.83× its control, so not adopted.

### AD-06 · AI WHEN: learn river mud from rain and ground — **AI**

- **What.** A tree model learns "this week's rain on this ground → how muddy the river gets".
- **Examples.** CWC daily mud from 2000 (when IMERG starts) to 2026: tens of thousands of
  readings across about 30 stations, plus Meghalaya's and Arunachal's files.
- **Inputs per station-day.**
  - Erosive rain over the catchment for the last 1, 3, 7 and 14 days.
  - Rain over the last 30–60 days (how wet the ground already is).
  - Day of year.
  - Catchment slope, soil and cover.
- **Test (proposed).** Held out two ways: whole years, and whole stations.
  - Must beat AD-02's formula and the season-only guess on both.
  - The pass marks are frozen after AD-02 runs, since AD-02 sets the baseline.
- **What it gives.** An honest AI WHEN on free data, and a weekly "expected river mud vs
  normal" for each gauged catchment. Live grading uses the 2026 file, about a week behind.
- **Effort.** 3–5 days. It is the stretch item: if it doesn't fit before 7 Nov, it is the
  first item of Priority 2.

### AD-07 · Results into the application — last

- Rewrite the AI/ML paragraph (answer 4) to name AD-01 and AD-06, with results as measured,
  pass or fail.
- Add AD-02 and AD-04 to testing and evidence (answer 9).
- Add the two new data sources to the innovation answer (11).
- Update the Proof of Work PDF (`scripts/run/build_proof_of_work.py`).
- Keep every answer at 500 real words or fewer.
- Any item that failed is written as "tested, not adopted".

---

## 4 · Priority 2: before Demo Day (Feb 2027)

| # | What | AI? | Examples / data | Test (proposed, freeze first) | Effort |
|---|---|---|---|---|---|
| **AD-08** | **Satellite reader for tree land:** closed forest / tea / *jhum* fallow / village grove / fresh clearing. Fixes the top open question V-02 (one cover value for all tree land) and feeds the formula's cover factor | **Yes** (tree model on Sentinel-2 seasons, canopy height, forest loss) | OSM tea gardens and reserve forests (`fetch_45`); new hand labels from **dated** imagery for groves and *jhum*. Attempt 1's 100 pictures may now be training data | A **new** blind sample; attempt 1's bars (P2: 0.60 / 0.60 / 0.70) | ~1 week; Earth Engine is capped ("Restricted Mode", no asset storage: about 2½ h per Assam pass) |
| **AD-09** | **AI second look for "newly cleared slope" alerts.** The rule flags pass the false-alarm tests (F1, F2) but only 62.5% are confirmed (bar 70%). A small model learns from the 160 blind-labelled pictures which flags are real | **Yes** | The 80 + 80 pictures from attempts 1 and 2; optionally radar (Sentinel-1) for cloudy years | A **new** blind sample (seed 44); bar unchanged: ≥ 70% of flags confirmed, ≤ 10% of unflagged | 3–4 days. **After submission:** the plan pre-registered no third attempt before the application |
| **AD-10** | **AI-corrected rain strength (R).** Both rain-strength maps flatten Assam's contrast: dry plains read about 2.3× high, the wettest foothills about 0.5× (V-01 part 2). Learn the correction from ground gauges | **Yes** | CWC daily rain, Assam from 1971, up to ~80 stations; ~9 hourly stations since 2019 (`fetch_47`) | Held-out gauges: corrected R beats InRESatE at gauges it never saw; S7 (rank stability) re-run | 3–5 days |
| **AD-11** | **North-East region map** (~91.7–96.9° E, 22.9–27.7° N). Makes the measured-mud *ranking* test possible (V-22: about 9–10 independent long-record stations), and gives AD-06 the soil part on every station's catchment. A second proof the backbone moves | No | Existing chain with a region switch | V3 as already designed | 2–3 days, mostly waiting. **User's call** |
| **AD-12** | **Field-check return form.** Field teams' answers come back in, quarantined as unverified (the `flood_intake.py` pattern). This is the label pipe for AD-16 | No | — | Round trip: export → fill in → import → shows as unverified | 1–2 days |
| **AD-13** | **Adjustable priority weights**, plus **what lies downstream** (farmland, homes, reservoirs below each catchment, from land cover and flow routing) | No | On hand | Weights shown on screen; the default ranking unchanged unless weights are moved | 1–2 days |
| **AD-14** | **Weekly advisories for farmers and communities.** The challenge names them as users; our screens serve officials. A short note per district or village in Assamese, Bengali, Bodo and English: "heavy rain this week on bare slopes here; usual protection: …" | Only for **wording**: templates carry every number; an AI model may draft translations, and a native speaker checks them before use | The outlook and place card | Native-speaker review; the numbers in the note match the app | 2–3 days |
| **AD-15** | **Housekeeping:** post-monsoon season cover (V-23); official micro-watersheds (E1.8) if obtainable; offline demo build (E1.9) | No | — | As in the plan | 1–3 days each |

---

## 5 · Priority 3: pilot and MVP (Feb–May 2027)

These need the department (ASK) or a budget (PAID).

| # | What | AI? | Needs | Notes |
|---|---|---|---|---|
| **AD-16** | **Pilot field comparison (V5), then an AI correction layer** learned from what field teams find (E3.2) | **Yes**, only if enough labelled points | Department field teams; AD-12 | Points handed out without our class shown; pass marks written before visits; spatial folds for the correction |
| **AD-17** | **Farmers' photo reports.** Geotagged photos of rills, gullies, bare slopes. An image model sorts them (kind of erosion, usable or not); a person confirms. Confirmed reports become labels for AD-16 and AD-18 | **Yes** (photo sorting) | A community channel (form or WhatsApp); consent | Quarantined intake; location and face privacy; never shown publicly without consent |
| **AD-18** | **Gully finder** on high-resolution imagery in pilot areas. The formula can't see gullies (X2) | **Yes**, deep learning: shapes in pictures are where it is the right tool | ASSAC imagery (ASK) or drone surveys (PAID); gullies hand-drawn in pilot areas | Held-out pilot area; measured growth from repeat drone surveys |
| **AD-19** | **Sensors** at 2–3 pilot outlets: rain intensity + stream muddiness (turbidity). Answers the IoT tag with measured, minute-level truth | Feeds AD-06 | PAID; grant budget line | Grades the outlook at field scale |
| **AD-20** | **Department data in:** soil survey → K; treated-area records → P; intensity gauges → R. Then **"did the works help?"**: treated vs similar untreated slopes over the years, on bare ground and river mud | Optional (matching similar slopes) | ASK | Before/after logged for each swap (E3.1) |

---

## 6 · Priority 4: later, or another problem statement

Kept short so they don't dilute the D-07 answer. They work as talking points for
"potential for wider application".

- **AD-21 Riverbank erosion watch.** Yearly bank lines of the Brahmaputra and Barak from
  satellite water maps, bank retreat per km, and the villages next in line. Assam's biggest
  erosion loss by area, but a river process owned by another department (X1).
- **AD-22 SlideSense and FloodSense for Assam.** These come almost free from the region
  port (X4). FloodSense matches D-18, and the rules allow only one MVP grant per edition.
  The landslide model would need checking on Assam before any claim: it learned
  Arunachal's mountains.
- **AD-23 Smaller ideas.**
  - Soil carbon lost with the soil (SoilGrids carbon × loss), as ranks only.
  - A bare-earth ground model to remove treetop slopes (V-06). FABDEM is non-commercial,
    and APSAC's LiDAR is an ASK.
  - River muddiness from satellite water colour, calibrated on CWC stations. Monsoon cloud
    is a physics limit, so this is a research item.

---

## 6b · Added 2026-10-27: the wider offer for the application

These were added so the application can show everything SoilSense will provide
([NESFIC_D07_SUBMISSION_PLAN.md](NESFIC_D07_SUBMISSION_PLAN.md) §2 places each one in a
horizon). None is started.

| # | What | AI? | Horizon | Needs |
|---|---|---|---|---|
| AD-24 | **Pre-monsoon watch list:** the barest steep catchments each dry season, ranked by expected monsoon rain, issued to divisions before the rains. Built from the measured bare-ground layer, so it does not wait for the alerts (AD-09) | No | Programme, Phase 3 (first issue Mar–Apr 2027) | — |
| AD-25 | **Works planner:** chosen catchments and treatments → quantities and indicative cost | No | Beyond | The department's schedule of rates |
| AD-26 | **Treated-works register and "did the works help?":** works geo-tagged, then tracked on bare ground and river mud against similar untreated slopes | Optional (matching) | Beyond | Treated-area records (AD-20) |
| AD-27 | **Offline field app** (Android, Assamese), grown out of the field form (AD-12) | No | Beyond | — |
| AD-28 | **Advisories by WhatsApp, SMS and voice**, extending AD-14 to low-literacy users | Wording only | Beyond | Consent (DPDP), messaging costs |
| AD-29 | **District bulletins:** an automatic PDF per district each season (top catchments, change, outlook record) | No | Programme, Phase 2 | — |
| AD-30 | **Map feeds:** WMS / API into ASSAC, the Assam State Geoportal or the department's GIS; private department layers behind a login | No | Programme, Phase 3 | The department's GIS choice |
| AD-31 | **Soil-loss plots:** 2–4 small measured plots at pilot sites. The only direct measure of tonnes; an alternative or companion to the sensors (AD-19) | No | Programme, Phase 3 (one of AD-19 / AD-31) | Budget; a site partner |
| AD-32 | **Climate-future view:** erosion under projected rainfall (downscaled CMIP6), 2030s and 2050s; a scenario, not a forecast | No | Beyond | — |
| AD-33 | **Scheme-ready outputs:** priority catchments shaped for watershed planning under existing schemes (PMKSY watershed component, MGNREGA land and water works) | No | Beyond | The department's planning format |
| AD-34 | **Training and handover:** staff workshops, a user guide in English and Assamese, layers handed over | No | Programme, Phase 3 | — |
| AD-35 | **Other North-East states with *jhum* hills:** Meghalaya, Nagaland, Mizoram, Manipur, Tripura. Arunachal is already computed and held back (V-19) | — | Beyond | The tree split (AD-08) first |
| AD-36 | **Open method and validation:** method note and validation report public; a peer-reviewed paper | — | Beyond | — |

---

## 7 · Decisions for the user

| # | Decision | Recommended | Why |
|---|---|---|---|
| 1 | Use ISRO's land-degradation map as **training examples** (AD-01), not only as a check | Yes | It is the only statewide expert-drawn erosion map. AD-05 takes over as the independent judge. Same footing as SlideSense's Bhuvan labels: outputs are ours, NRSC's polygons are never shared |
| 2 | Publish SoilSense on the public app and add the outlook to the cloud run (AD-03) | Yes, before 7 Nov | The application's demo link; the daily log |
| 3 | Extend the map to a North-East region (AD-11) | After submission | It unlocks the measured-mud ranking test, but isn't needed for the application |
| 4 | Ask for a sensor budget in the grant (AD-19) | Yes, as a small line | It answers the IoT tag and gives measured truth |

---

## 8 · What we will not do, and why

- **Train an AI on the formula's own map.** It would learn to copy the formula and add
  nothing. A soil department would spot that.
- **Deep learning for the statewide map.** The inputs are tables of numbers per square;
  tree models are the right tool, as for SlideSense (DESIGN.md, "why trees"). Deep learning
  is kept for pictures (AD-18).
- **A chatbot over the map.** It adds no evidence.
- **Call the outlook a soil-loss forecast in tonnes** before AD-02 and AD-06 have passed.
  Until then it is "where damaging rain meets weak ground this week".
- **Retry the change-alert rules before submission.** That was pre-registered (EROSION_PLAN,
  E1.3 attempt 2). AD-09 is the next attempt, after submission.

---

## 9 · Review of 2026-10-26 (evening): status, three corrections, and additions

### 9.1 Status against this list

| # | State |
|---|---|
| AD-02 | **Easier than written.** Satellite rain no longer waits for V-15: Earth Engine serves IMERG V07 *Final* (gauge-adjusted) for any box, so catchments reaching into Meghalaya, Nagaland, Manipur and Mizoram are no problem (13 years at 125 points took 6 minutes, `fetch_54`). The outlook's **rain** is already graded against it (E2.2 part 2: *which weeks* ρ 0.63 ✔, *heavy weeks* AUC 0.77 ✔, *which places within a week* ρ 0.18 ✕). The river-mud check is still to do |
| AD-03, AD-07 | **Parked by the user** (no public deploy; no application work for now) |
| AD-12 | Not started (the export side of the field kit exists) |
| AD-13 | **Weights done** (five sliders; the defaults reproduce the main ranking exactly). "What lies downstream" not done: see AD-25 below |
| The rest | Not started |

### 9.2 Three corrections

1. **AD-10: do not learn R from gauge-derived R.** The gauge R values are not a valid truth
   (EROSION_PLAN.md, "V-01: a gauge-corrected rain factor — not tested").
   - Sonapur, about 20 km from Guwahati, gives 3,069 from its daily records, against 7,924
     measured at Guwahati.
   - The CWC files list rainy days only.
   - InRESatE's daily model was fitted to satellite rain.

   **The workable version:** learn a correction of *daily rain* on matched days (gauge
   against IMERG, after a completeness filter), then recompute R from the corrected
   satellite rain. Or anchor on the ~9 hourly telemetry stations (2019 onward). Judged on
   held-out gauges.
2. **NASA's bulk download is not safe to lean on.** NASA's OPeNDAP server blocked our address
   after one day's heavy use (26 Oct). Use Earth Engine for IMERG, and keep any NASA fetch
   small and slow.
3. **Earth Engine is in "restricted mode" because the project used up its noncommercial
   compute quota** (V-29).
   - AD-08 and AD-09 lean on Earth Engine heavily, at about 2½ h per Assam pass.
   - Before they start, settle the quota and the commercial-use terms with Google.

### 9.3 Additions (new items)

| # | What | AI? | Data | Test (proposed, freeze first) | Effort |
|---|---|---|---|---|---|
| **AD-24** | **"What if we treat it?" simulator.** Pick a catchment or district and apply measures: contour bunds or trenches (P about 0.5 on farmed slopes), bench terraces (P about 0.15–0.2 on cleared steep land), revegetation or agroforestry (C toward forest). It shows tonnes saved a year and **tonnes saved per hectare treated**, and ranks catchments by where works save most soil per hectare. Unit costs can be added later to give "per rupee". Answers "better targeting of soil-conservation resources" head-on | No (the formula, run forwards) | On hand; P and C values from Wischmeier & Smith and Indian SWC practice, each one cited | Default (no works) equals today's map; each P/C value has a source; the department reviews the table | 1–2 days |
| **AD-25** | **Does the soil reach the water? Sediment connectivity and what lies downstream.** An index of connectivity (Borselli et al. 2008) on the DEM and land cover marks eroding land that is wired to a stream. Flow routing lists what each catchment drains into: reservoirs, wetlands, farmland, villages. A "soil reaching rivers" rank sits beside the loss rank (this is AD-13's "downstream" part) | No | DEM, flow routing, land cover, OSM water bodies and dams on hand | Later checked against river mud (AD-02, AD-11): catchments with more connected erosion should run muddier | 2 days |
| **AD-26** | **Jhum cycle tracker.** From the 8 dry seasons, find squares that turn bare and count the years since they last did. That gives the **fallow length**, and the share of *jhum* land on short (< 5-year) cycles per catchment and district, with its trend. Shortening *jhum* cycles are the main erosion driver named for the North-East hills | No at first (a rule); AD-08 later | E1.1's bare-ground series on hand | Blind dated pictures, as E3, with a fresh sample: are "cleared again after N years" squares really recleared? Bars frozen first | 1–2 days |
| **AD-27** | **Why the AI says so.** SHAP explanations for AD-01: for each catchment and village card, the top inputs pushing the AI's rank up or down. Plus a map of where the formula and the AI agree and disagree | Yes (explaining AD-01) | AD-01 | Explanations are produced from the out-of-fold models only | +0.5 day on AD-01 |
| **AD-28** | **Warnings for heavy erosive weeks.** The outlook's tested skill is *when* (heavy weeks AUC 0.77). When a district's steep bare land faces ≥ 2× normal erosive rain, write a warning: which districts, why, what to do before the rain. Logged like the issues; sent by email or chat once a channel is chosen | No (AI only for wording, as AD-14) | The outlook | Hits and false alarms counted against IMERG weekly, as the replay | 1 day (+ a sending account from the user) |
| **AD-29** | **What the lost soil is worth.** Nutrients (N, P, K, organic carbon from SoilGrids) carried off with the estimated soil loss, as a fertiliser-equivalent value and carbon lost, per catchment. Ranks and orders of magnitude only. It turns tonnes into a reason a farmer or a finance officer can act on (extends AD-23's carbon idea) | No | SoilGrids on hand; fertiliser prices cited | Shown as an estimate; units checked by hand on one catchment | 0.5–1 day |
| **AD-30** | **Gully-prone ground from the terrain**, a first look before the deep-learning gully finder (AD-18): the slope-area threshold (Montgomery & Dietrich) and stream-power index on the 30 m DEM mark where channels likely start on bare or cleared land | No | DEM on hand | The ~300-point blind picture check (AD-05) includes gully-prone points; bars frozen first | 1 day |

### 9.4 Order of work, now that the application is parked

1. **Wave 1, the AI core:** AD-01 + AD-27 → AD-02 → AD-06, with AD-05 as the independent
   judge.
2. **Wave 2, decision tools on the formula:** AD-24, AD-25, AD-26, AD-12, AD-04.
3. **Wave 3, imagery AI (needs the Earth Engine question settled):** AD-08, AD-09, AD-10
   (corrected), then AD-28, AD-14, AD-29.
4. **Wave 4, the department or a budget:** AD-16 to AD-20; AD-11 (the user's call); AD-21,
   AD-22.
