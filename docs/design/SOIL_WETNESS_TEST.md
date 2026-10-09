# Soil wetness and long rain — do they improve the flood and landslide forecasts?

Started 2026-09-28, at the user's request ("Doesn't flood need soil wetness? … needed
in landslides too?").

**Status:** pre-registered (this section written before any data was fetched or any
result was seen). Results are appended in §6. Nothing ships unless a gate below passes.

---

## 1. The question

Both forecasts look at recent rain only:

| forecast | rain inputs today |
|---|---|
| Flood day model (`flood_forecast.DayModel`) | local WHEN score (3- and 7-day rain percentiles, blended) + upstream-catchment 3- and 7-day rain percentiles + log exposure |
| Landslide trigger (`trigger.py`) | unfitted mean of 3- and 7-day rain percentiles |

Physically, the same storm on already-soaked ground should flood and slide more.
That is **antecedent wetness**. Two ways to give it to the models:

1. **Soil wetness** — how much water is already in the ground.
2. **Long rain** — rain over the last 15 and 30 days (already computed on the
   IMERG lattice: `data/interim/rainfall/features/r15.npy`, `r30.npy`).

Neither has been tried in the flood day model. For landslides, `r15`/`r30`/`api`
were among the 6 features of a logistic model that lost to the unfitted
r3+r7 average (0.755 vs 0.768, `trigger.py` docstring); soil wetness was never tried.

## 2. Inputs (fixed before fetching)

**Soil wetness** — ERA5-Land daily aggregate (Earth Engine
`ECMWF/ERA5_LAND/DAILY_AGGR`), bilinear onto the IMERG 0.1° lattice (cell centres
x.x5), 2000-06-01 onward. Fetch: `scripts/fetch/fetch_39_era5land_soil.py`.

- One number per cell-day: the depth-weighted mean volumetric water of the top
  metre, `(7·L1 + 21·L2 + 72·L3) / 100` (layers 0–7, 7–28, 28–100 cm).
- Taken on **day t−3** — the day before the 3-day rain window that ends on the
  forecast day — so it describes the ground *before* the storm, not the storm's
  own effect.
- Turned into each cell's own May–October percentile over the full record —
  the same convention as the existing r3/r7 inputs (`when_grid.percentile_features`).

Why ERA5-Land: longest record (2000+), exactly our grid spacing, and the same
land-surface model family as the ECMWF forecast soil that Open-Meteo serves live —
so a pass has a plausible route to the live app.

**Long rain** — existing IMERG `r15`, `r30`, each as the cell's own May–October
percentile (same convention).

## 3. Flood test (day model)

Same protocol as `replay_flood_forecast.py` (nothing that produces a number has
seen the test years):

- WHERE exposure from the 2022-only model (`models/flood_where_replay2022`).
- Tree fitted on 2015–2020, calibration curve on 2021–2022.
- Test 2023-01-01 → 2025-10-31 (`TRUTH_END`).
- Train and truth: the **verified record** (`flood_forecast.training_events()`,
  2,185 events), which the production model now uses.
- **Metric: timing-only AUC** — each cell-day's chance divided by that cell's own
  2015–2022 normal, ranked across all test cell-days (exactly the replay's
  `auc_timing_only`), region-wide and inside Arunachal.

| run | day-model inputs |
|---|---|
| baseline | production: WHEN score, upstream r3, upstream r7 (+ exposure) |
| +soil | baseline + soil wetness percentile |
| +long rain | baseline + r15 and r30 percentiles |
| +both | baseline + soil + r15 + r30 |

All new inputs enter with the same "more water → higher chance" constraint as
the existing ones.

**A candidate PASSES only if all three hold:**

- F1: region-wide timing AUC gain over baseline ≥ **+0.010**;
- F2: paired bootstrap (2,000 reps, seed 0) — the **98.3%** interval of the
  gain (95% Bonferroni-split over 3 candidates) lies above 0. The bootstrap
  resamples test flood **days**: all floods on one date move together, because
  one storm floods many cells at once and treating them as independent would
  make the interval too narrow;
- F3: inside Arunachal the gain is ≥ **−0.005** (not worse).

If several pass, the largest region-wide gain wins; within 0.003 of each other,
the one with fewer inputs wins.

## 4. Landslide test

Nothing is fitted — same as the shipped trigger. Each run is an unfitted mean of
percentiles.

| run | trigger |
|---|---|
| baseline | mean(r3, r7) — shipped |
| +soil | mean(r3, r7, soil) |
| +long rain | mean(r3, r7, long) with long = mean(r15, r30) |
| +both | mean(r3, r7, soil, long) |

**4A — Arunachal, production data (IMERG rain).** The 72 dated NASA GLC events
`trigger.load_events` uses.

- L-time: timing-only AUC. Each event is compared only with its own cell on
  the days within ±15 calendar days of its date in every other year 2000–2025
  (days with an incomplete 30-day window excluded). Its placement = share of
  those control days scoring below it (ties count half). L-time = the mean
  placement over events.
- L-prod: the shipped metric (vs 20,000 random monsoon cell-days, seed 0,
  exactly `trigger.py`).

**4B — Himalayan arc, more events (ERA5-Land for rain *and* soil).** The 618
dated, ≤5 km located GLC events in 76–98°E, 26–32°N (`reports/_himalaya_glc.csv`,
2007–2018), all triggers kept as in 4A. Duplicate records of one cell on one day
count once. Rain windows are trailing sums including the day, as in
`rainfall_features.rolling_sum`. L-prod's counterpart is 20,000 random monsoon
days × random event cells (seed 0). Rain percentiles here come from
ERA5-Land's own precipitation, because the IMERG arc archive is only 10% fetched.
This answers "does soil wetness add anything beyond rain" with ~9× the events.
It cannot by itself change the shipped trigger, which runs on different rain.

**A candidate PASSES only if:**

- L1: 4A L-time gain ≥ **+0.02**, with the paired bootstrap (2,000 reps,
  seed 0, events resampled by date) 98.3% interval above 0;
- L2: 4A L-prod not worse by more than **0.01**.

4B is reported the same way. If 4B passes and 4A does not, the conclusion is
"a real effect too small to see on 72 events". That is recorded, not shipped.

## 5. What happens after

- **A long-rain pass** can ship directly. r15/r30 come from the same rain the
  live run already fetches; the live pipeline only needs 30 days of past rain
  per point.
- **A soil pass** does not ship yet. The live app would need a live soil source
  (Open-Meteo / ECMWF). A step-2 check — live-source soil re-run over 2023–25,
  keeping at least half the gain — gets its own written bar before it runs.
- **A fail** is recorded here, with the reason, and nothing changes.

Diagnostics reported but not deciding: each input's timing AUC on its own; the
correlation between soil and r30 percentiles (how much soil just repeats long rain).

## 6. Results (2026-09-28)

Data: `fetch_39_era5land_soil.py` pulled 9,607 days (2000-06-01 → 2026-09-19) with
no gaps and no missing values on the lattice. Numbers: `reports/soil_wetness_test.json`.
Script: `scripts/model/test_soil_wetness.py`.

### 6a. Landslides — FAIL, all candidates, both tests

| | L-time 4A (72 events) | gain [98.3%] | L-prod 4A | L-time 4B (583 events) | gain [98.3%] |
|---|---|---|---|---|---|
| baseline | 0.762 | | **0.768** (reproduces shipped) | 0.690 | |
| +soil | 0.760 | −0.002 [−0.034, +0.033] | 0.762 | 0.684 | −0.006 [−0.020, +0.008] |
| +long rain | 0.764 | +0.002 [−0.017, +0.021] | 0.760 | 0.692 | +0.002 [−0.006, +0.010] |
| +both | 0.764 | +0.002 [−0.028, +0.034] | 0.760 | 0.686 | −0.004 [−0.019, +0.012] |

Each input alone, 4A L-time: r3 0.749, r7 0.741, r15 0.710, r30 0.697, **soil 0.598**.

The 4B arc result is tight: with 583 events, the most soil could be adding is
about +0.008. Nothing moves the landslide trigger.

**Post-hoc (not a gate):** fitted weights, 5-fold CV grouped by date, 4B arc
(`arc_fitted_posthoc` in the report).

| model | soil vs r3,r7 | long rain vs r3,r7 |
|---|---|---|
| logistic | −0.004 [−0.008, −0.001] | −0.013 |
| small tree | −0.010 | −0.013 |

Even when a model chooses its own weights, the extra inputs make unseen events
slightly worse. That closes the "the equal-weight average was too blunt" loophole.

**Why:** in Arunachal the top metre of soil sits at a median 89–95% of its full
range from April to September. 59% of June–September cell-days are in the top
tenth of their range. The ground is soaked all monsoon, so "how wet was it
already" barely varies. The last 3 days of rain is what separates the landslide day.

### 6b. Flood day model — FAIL by the written gate (F3), with a clear pattern

Test 2023-01-01 → 2025-10-31, verified record.

| | region: 332 floods / 126 days | gain [98.3%] | Arunachal: 44 floods / 33 days | gain [98.3%] | verdict |
|---|---|---|---|---|---|
| baseline | 0.897 | | 0.833 | | |
| +soil | 0.918 | **+0.021 [+0.009, +0.033]** | 0.806 | −0.027 [−0.066, +0.012] | F1 ✓ F2 ✓ **F3 ✗** |
| +long rain | 0.917 | **+0.020 [+0.002, +0.037]** | 0.822 | −0.011 [−0.060, +0.035] | F1 ✓ F2 ✓ **F3 ✗** |
| +both | 0.913 | +0.016 [−0.002, +0.032] | 0.802 | −0.031 [−0.095, +0.024] | F1 ✓ F2 ✗ F3 ✗ |

Diagnostics: each input alone (pooled AUC) — soil 0.843, r15 0.908, r30 0.890,
local WHEN 0.881. The soil and r30 percentiles correlate only 0.37 in the
monsoon, so soil is not just repeating long rain.

**Post-hoc breakdown — explains the verdict, cannot change it** (terrain class of
the rain cell = mean slope, `flood_forecast.terrain_class`):

| | floods | baseline | +soil | +long rain |
|---|---|---|---|---|
| outside Arunachal | 288 | 0.906 | +0.026 [+0.016, +0.037] | +0.023 [+0.005, +0.042] |
| flat (<5°) | 298 | 0.895 | **+0.018 [+0.012, +0.026]** | +0.013 [+0.001, +0.029] |
| flat, in Arunachal | 16 | 0.806 | +0.049 [+0.003, +0.103] | +0.036 [−0.008, +0.086] |
| steep (≥15°) | 29 | 0.835 | **−0.063 [−0.115, −0.015]** | +0.003 [−0.045, +0.057] |
| steep, in Arunachal | 28 | 0.834 | −0.052 [−0.103, −0.005] | +0.004 [−0.049, +0.061] |

(The hilly class had fewer than 10 test floods.)

**Reading.** Soil wetness helps flood timing where water collects — plains and
valley floors, where a flood is the ground and rivers filling up over days. It
hurts on steep ground, where a flood is a flash flood from one downpour and the
soil is soaked all monsoon anyway. The day model pools all terrain and applies a
plains-learned soil effect to mountain cells. 28 of Arunachal's 44 test floods
were on steep ground, hence the Arunachal-wide loss.

**Nothing ships from §3 as registered.** The flat-ground pattern is a new
hypothesis formed from the test years, so it gets its own fresh test (§7).

## 7. Follow-up: soil wetness on flat ground only — pre-registered

Written after §6b and before any run of this design.

**Hypothesis:** using the +soil (or +long-rain) day model on flat rain cells
only, and the unchanged baseline everywhere else, improves flood timing.

**Fresh test years.** §6b's discovery used 2023–25, so the confirmation runs
time-reversed:
- tree fitted on 2019–2023, calibration curve on 2024-01-01 → 2025-10-31;
- tested on **2015–2018**, whose results were never looked at in any soil run;
- each cell's normal = the mean chance over the fit years (2019 → 2025-10-31).

Same verified record, same WHERE exposure (the 2022-only model). That model
saw 2015–18 floods; this affects baseline and candidates alike, and timing-only
AUC divides each cell's own level out.

| run | chance on flat cells (<5°) | chance elsewhere |
|---|---|---|
| baseline | baseline model | baseline model |
| flat +soil | +soil model (pooled fit, as in §6b) | baseline model |
| flat +long rain | +long-rain model (pooled fit) | baseline model |

**PASS only if all three hold (per candidate; 97.5% intervals = 95% split over 2):**
- G1: timing-AUC gain on flat cells ≥ **+0.010**, with the date-clustered paired
  bootstrap (2,000 reps, seed 0) 97.5% interval above 0;
- G2: region-wide gain ≥ **0** (point estimate);
- G3: inside Arunachal (all terrain) gain ≥ **−0.005**.

Flat cells inside Arunachal are reported. Only if they hold ≥ 30 test floods
are they gated (G4), at G3's bar: gain ≥ −0.005.

If both pass, the larger flat-ground gain wins; within 0.003 of each other,
long rain wins, because it needs no new live data source. A soil pass still
needs the §5 step-2 live-source check before shipping.

### 7a. Result (2026-09-28) — flat +soil PASSES; flat +long rain FAILS

Tested on 2015–2018, fitted on 2019–2025 (`flat` in the report).

| area | floods / days | baseline | flat +soil [97.5%] | flat +long rain [97.5%] |
|---|---|---|---|---|
| flat cells (G1) | 530 / 180 | 0.841 | **+0.017 [+0.006, +0.027]** | −0.052 [−0.085, −0.025] |
| region (G2) | 632 / 194 | 0.828 | +0.035 [+0.020, +0.046] | −0.071 |
| Arunachal (G3) | 150 / 70 | 0.837 | **+0.021 [+0.007, +0.036]** | −0.039 |
| flat, in Arunachal (G4) | 56 / 32 | 0.857 | +0.010 [−0.017, +0.037] | −0.077 |

- **flat +soil passes G1–G4.** The flat-ground gain is the same size in both
  periods (+0.018 in 2023–25, +0.017 in 2015–18), a stable effect.
- **flat +long rain fails every gate.** It helped in 2023–25 and hurt in
  2015–18, so long rain is not a stable signal here. It is dropped.
- The region and Arunachal gains exceed the flat-only gain because timing AUC
  ranks all cells together, and sharper flat-cell chances also reorder them
  against hill cells. G1, within flat cells only, is the clean timing measure.

## 8. Step 2 — does stale soil still work? — pre-registered

Written after §7a, before this run.

**Why.** The live run cannot have soil for day t−3. ERA5-Land on Earth Engine
ran 9 days behind on 2026-09-28 (last day 2026-09-19), so the forecast for
today + 7 days would need soil up to 13 days newer than exists. The simplest
design that is always available: **soil at a fixed t−16** (latest day + 7-day
lead + 9-day latency). Trained and tested at that lag, so the model learns what
it will really see. No forecast soil is needed.

**Test.** Exactly §7's flat +soil run (fits 2019–2025, test 2015–2018, flat
cells only use the soil model), with the soil input at t−16 instead of t−3.
This re-uses §7's test years on purpose: it asks how much of an already
confirmed effect survives a delay. It is not a search for a new one.

**PASS only if all hold (single candidate, 95% interval):**
- S1: flat-cell gain ≥ **+0.0087** (half of §7a's +0.0173), with the
  date-clustered paired bootstrap 95% interval above 0;
- S2: Arunachal gain ≥ **−0.005**;
- S3: region gain ≥ **0**.

**Pass:** the design (soil at t−16, flat cells only, ERA5-Land on the lattice)
is ready to wire into the live forecast, and that wiring is a separate,
user-approved step. **Fail:** soil stays out until a live soil source with
little delay is found and checked.

### 8a. Result (2026-09-28) — PASS (S1–S3)

Soil on day t−16, flat cells only, fitted 2019–2025, tested 2015–2018 (`stale` in the report).

| area | floods / days | baseline | flat +soil, t−16 [95%] | for comparison: t−3 (§7a) |
|---|---|---|---|---|
| flat cells (S1, bar +0.0086) | 530 / 180 | 0.841 | **+0.0095 [+0.0044, +0.0142]** | +0.0173 |
| region (S3) | 632 / 194 | 0.828 | +0.026 [+0.021, +0.031] | +0.035 |
| Arunachal (S2) | 150 / 70 | 0.837 | **+0.019 [+0.010, +0.030]** | +0.021 |
| flat, in Arunachal | 56 / 32 | 0.857 | +0.014 [−0.001, +0.036] | +0.010 |

About half the flat-ground gain survives a 16-day-old reading. S1 clears its bar
narrowly, and the Arunachal gain is almost unchanged.

## 9. Conclusion

| | verdict | what it means |
|---|---|---|
| Landslides — soil wetness | **no** | the ground is soaked all monsoon; it adds nothing, even with fitted weights on 583 Himalayan events |
| Landslides — 15/30-day rain | **no** | no gain on 72 or 583 events |
| Floods — 15/30-day rain | **no** | helped in 2023–25, hurt in 2015–18 — unstable |
| Floods — soil wetness, all terrain | **no** | helps on plains, hurts on steep ground (flash floods) |
| **Floods — soil wetness, flat ground only** | **yes** | confirmed on fresh years; holds with a 16-day-old reading |

**Wiring steps** (approved by the user and done 2026-09-28 — see §10):
- **Production day model:** refit with the +soil model used on flat cells (soil at t−16).
- **Daily run:** fetch one ERA5-Land image per day onto the lattice. Earth Engine
  `computePixels`, the same call as `fetch_39`. If it fails, fall back to the
  baseline chance on flat cells.
- **Near-here curves:** refit.
- **Checks:** golden check (river forecasts must not move), app screens, method page line.

No production file was changed by the test itself.

## 10. Wired into the live forecast — 2026-09-28

The user approved it, and it was done the same day.

### What changed

- **`flood_forecast.py`**
  - New `FlatSoilDayModel` = the rain-only `DayModel` (unchanged) plus a soil
    `DayModel`, used on the 380 flat cells of 1,953.
  - `fit_day_model()` fits both halves, for production and for every test copy.
  - `predict_day(model, F, E, soil)` takes `soil` as a required argument, so
    no caller can forget it.
  - `soil_input()` gives soil on day t−16 as a percentile against
    `models/flood_forecast/soil_breaks.npy` (0.1% steps, May–Oct, full record).
  - `fit_production()` saves the soil scale first and fits both halves.
- **`flood_forecast_live.py`**
  - `fetch_soil()` reads the lattice from Earth Engine through
    `fetch_39_era5land_soil.lattice_days()` (about 9 s, 180 s timeout). This
    matches the training archive exactly (difference 0.0).
  - `live_soil()` scores it. Soil is used only if the installed model has a
    soil half.
  - Any failure means flat cells use rain only, and the issue says so
    (`soil_wetness` in the report and web snapshot).
  - `build()`'s source check now fits test copies with soil too.
- **`near_here.py`:** the production fit and all five test functions
  (check, confidence, diagnose, confirmed, compare) fit and predict with soil.
- **`check_live_unchanged.py`:** records and replays the soil fetch. It captures
  the final blended chance (`predict_day`), not the inner models.
- **Web:** the method page and the place panel say that flat-ground chances
  use soil wetness. The figures come from `method.soil`, which is read from
  this report.
- **Rollback:**
  - models: `models/flood_forecast_pre_soil/`;
  - reports: `reports/_pre_soil_backup/`;
  - golden baseline: `data/interim/flood_forecast/golden_live_pre_soil/`.

### Checks

| check | result |
|---|---|
| Golden check, new code with the OLD model files | **PASS** — every old number identical; only the soil notes added |
| Retrained rain-only half vs the old model | identical predictions |
| Golden check, retrained | river rows **0 changes**; hill/steep cells' daily chances **identical**; flat cells 3,107 of 6,840 cell-days changed; everything downstream (outlook, near-here, measured error) changed as expected; nothing removed. Re-baselined. |
| Valley factor | flat 1.028 → 0.997; hilly and steep unchanged |
| Live source check, inside Arunachal, 2023–25, 44 floods | satellite-fitted on live rain **0.845 → 0.851**; on satellite rain 0.835 → 0.840 (at 10× normal: 5% → 18% of floods caught) |
| Near-here Gate A (held-out) | still FAIL on level → stays "approximate". Week ranking in Arunachal 0.876 → 0.887; anywhere in Arunachal, week 0.784 → 0.832 |
| Near-here production-like error (on screen) | ranking 0.893 → 0.893; recorded/forecast ×1.62 → ×1.61 (floods on record), ×2.11 → ×1.97 (none on record) |
| App screens (AppTest) | 14 of 14 pass; method page text checked |
| Live refresh 2026-09-28 | soil used on all 7 outlook days (soil data to 2026-09-18) |

The near-here numbers above are graded on 2023–25, the years in which the
flat-ground pattern was first seen (§6b). They are a consistency check, not
independent proof. The independent proof is §7a and §8a, on 2015–18.

### Post-hoc: is the gain about the day or the season?

Same fits as §8, flat cells, 2015–18 (`season_split_posthoc` in the report).
Not a gate.

| ranking | rain only | + soil | gain [95%] |
|---|---|---|---|
| each day vs the place's year-round normal (the gated measure) | 0.841 | 0.851 | +0.010 [+0.004, +0.014] |
| June–Sept only, each day vs the place's normal for that month | 0.618 | 0.632 | **+0.014 [+0.006, +0.022]** |
| all months, each day vs the place's normal for that month | 0.694 | 0.673 | −0.021 [−0.029, −0.014] |

Within the main flood season, soil wetness helps pick the actual flood days.
Across all months at the month level it scores lower. That drop comes from
days outside June–September (31 of 530 flat floods, plus the dry months).
There, chances are tiny, and a 16-day-old soil reading does not match
early-season floods. The screen's "times normal" uses the year-round normal,
the measure that passed.

### Daily operation

The 08:30 Windows task runs as the same user that holds the Earth Engine
login, so the fetch works unattended. ERA5-Land ran 9 days behind on
2026-09-28. If it slips past 9 days, the last outlook days lose soil and those
days' flat cells use rain only. `outlook_days_with_soil` on each issue shows this.
