# SoilSense build plan — NESFIC-D-07, Assam

> **The working plan.** Update the status column as tasks close. Record every measured
> result in the [Results log](#results-log) (append-only, never overwrite).
> **Design and reasoning:** [EROSION_MODULE.md](EROSION_MODULE.md). This file says *what,
> when, and how we know it's done*; that one says *why*.
> Written 2026-09-29.

## Status at a glance

| Phase | Window | Goal | Tasks done |
|---|---|---|---|
| **0 — Application proof** | 29 Sep → 18 Oct 2026 | A working, honest first erosion map of Assam, built by the same backbone with a region switch, in the app, and the application submitted | 0 / 11 |
| 1 — Seasonal cover + validation | Nov → mid-Dec 2026 | Bare ground refreshed per season since 2019; first independent validation | 0 / 9 |
| 2 — Prototype | mid-Dec 2026 → Demo Day, Feb 2027 | Weekly outlook, priority list with reasons, field kit, pilot protocol | 0 / 6 |
| 3 — MVP | Feb → May 2027 | Department data in, field results in, calibrated; optional sensor pilot | 0 / 5 |

Status marks: ☐ to do · ◐ in progress · ☑ done · ✕ dropped (with reason in the Results log)

## Key dates (NESFIC 2026)

| Date | What |
|---|---|
| 25 Sep – **25 Oct 2026** | Application window. **Our target is to submit by 18–20 Oct** |
| Nov 2026 | North East Seva First Innovation Conclave, Guwahati |
| Nov 2026 – Feb 2027 | Prototype development phase |
| Feb 2027 | Demo Day |
| Feb – May 2027 | MVP phase |
| Jun 2027 → | MVP demonstration and market access |

Grants: Idea-stage up to ₹10 L · MVP & Prototype up to ₹20 L · Deep Tech up to ₹40 L.
Selection does not guarantee procurement. No prototype is required to apply, but "Maturity"
and "Feasibility" are scored, so a working first map is worth a lot.

---

## Decisions needed

| # | Decision | Options | Recommendation | Needed by |
|---|---|---|---|---|
| **D1** | Where Arunachal's data lives after the region port | (a) leave Arunachal's folders as they are, put Assam in region subfolders · (b) move Arunachal into the same region layout | **(a) now**: zero risk to the live 08:30 flood job during the sprint. Revisit (b) after Demo Day | E0.1 |
| **D2** | Module name | SoilSense · ErosionSense · other | Your call — "SoilSense" is only a working name | E0.9 |
| **D3** | Pilot areas | Hill districts, foothill belt, tea-garden slopes, Barak hillocks | **Dima Hasao + Karbi Anglong** (steep, *jhum*, erosion a known concern) + one foothill belt as contrast. Confirm with the department | E0.10 (proposed), E2.5 (agreed) |
| **D4** | Risk-class scheme | The department's own · the common Indian six-class scheme | **Theirs if they have one**, so our map compares directly with their work | E0.6 (provisional), E2.5 (final) |
| **D5** | Grant tier to apply for | Idea ₹10 L · MVP & Prototype ₹20 L · Deep Tech ₹40 L | **MVP & Prototype**: two live modules plus a working Assam first cut is past idea stage | E0.10 |
| **D6** | Also apply to D-18 (flood digital twin) with FloodSense? | Yes / no | Check whether the proposal rules allow one applicant several statements first. Not part of this plan | E0.10 |
| **D7** | Mention riverbank erosion (X1) in the application? | Omit · one line · full section | **One line, as a future extension.** It's another department's remit and must not blur the D-07 answer | E0.10 |

---

## Phase 0 — Application proof (29 Sep → 18 Oct 2026)

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
| **E0.1** | **Region registry.** `common.py` and `grid.py` take a region (`--region` / `REGION`, default `arunachal`). The Arunachal entry is identical to today's constants | Region registry in one place | `check_live_unchanged.py check` passes. Existing Arunachal scripts run unchanged with no flag. Arunachal constants equal the frozen ones | 1 d | ☐ |
| **E0.2** | **Assam grid + boundary.** Freeze the spec (design §4.1: EPSG:32646, 100 m, origin 160,000 / 2,660,000, 6,400 × 4,400). State mask. Official boundary and current districts from the Assam State Geoportal (GADM as a stand-in until then) | `DATA_CONTRACT.md` §8 "Assam region"; state mask | In-state cell count recorded; area within 1% of 78,438 km²; spec written into DATA_CONTRACT | 0.5 d | ☐ |
| **E0.3** | **Fetch Assam raw.** DEM (~20 new tiles), SoilGrids (Assam box), WorldCover (1–2 tiles west of 90°E), HydroSHEDS clip (local), IMERG daily 2000-06 → now (~2 h) | Raw files + `_SOURCES.json` entries | Every raw folder has an Assam entry in `_SOURCES.json`; IMERG day count matches Arunachal's date range; no DEM holes inside the state | 1 d (mostly waiting) | ☐ |
| **E0.4** | **Build Assam backbone.** Terrain, hydrology (flow accumulation, channels, height above drainage), soil and land-cover features, rain stack | `data/interim/assam/…` | `check_terrain` / `check_hydro` / `check_rainfall` pictures reviewed for Assam; most plains cells < 2°; drainage follows the Brahmaputra and Barak | 1–2 d | ☐ |
| **E0.5** | **Freeze Assam validation folds** (50 km blocks, seed 42), hashed | `spatial_folds.meta.json` for Assam | Hash written **before any model exists**. Cheap now, impossible to do honestly later | 0.5 d | ☐ |
| **E0.6** | **The recipe** — `erosion_factors.py`. Build and debug on **Arunachal first** (can start day 1), then run on Assam. Confirm the R equation's units and coefficients, the K formula, the LS slope-length cap, and provisional classes (D4) | Soil-loss estimate + class rasters, **each factor saved separately**, both regions; unit suffixes per DATA_CONTRACT §5 | Both regions produce all five factor layers and the estimate; formulas and constants written into design §5.2 with sources | 2–3 d | ☐ |
| **E0.7** | **Pre-registered sanity checks** (bars below, written before running) | Results log entries | Every bar evaluated and logged; failures fixed or explained **before anything is shown to anyone** | 1 d | ☐ |
| **E0.8** | **First priority ranking** — `erosion_priority.py` on HydroBASINS level 12 and on districts; top 20 with main driver | Ranked tables | Top 20 checked by eye against satellite imagery: are they visibly steep and/or bare? Any that aren't, explained | 1 d | ☐ |
| **E0.9** | **App screen** — `webapp/products/erosion/` (status "building"), minimal region picker, map + ranking + "how to read this" note; bundle export | Running module | Runs locally; `check_app_screens.py` passes; screenshots taken for the application | 2 d | ☐ |
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
| **E3.5** | Extensions decision: X1 riverbank watch, X2 gullies, X3 sand-casting, X4 SlopeSense/FloodSense for Assam | Decision logged with reasons | ☐ |

---

## Results log

Append-only. One row per measurement. Never edit a past row. Add a new row that supersedes it.

| Date | Task | What was measured | Result | vs bar |
|---|---|---|---|---|
| 2026-09-29 | — | Assam area in EPSG:32646 (GADM polygon) | 78,474 km² vs official 78,438 (+0.05%) | CRS reuse OK |
| 2026-09-29 | — | Assam grid extent, snapped to 10 km | origin 160,000 / 2,660,000; 6,400 × 4,400 cells | — |
| 2026-09-29 | — | Arunachal coupling in code | 33 scripts use the AOI box/name; 29 import the grid; 69 contain "arunachal"; 15 web-app files | Sizes E0.1 |
| 2026-09-29 | — | Assam raw already on disk | 12 of ~32 DEM tiles; 6 WorldCover tiles cover all but the strip west of 90°E; HydroSHEDS Asia-wide; GADM has 27 (outdated) Assam districts | Sizes E0.3 |
