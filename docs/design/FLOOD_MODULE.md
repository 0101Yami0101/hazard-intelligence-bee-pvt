# FloodSense — design, and what the measurements actually said

> **Status: prototype, shipping, static layer UNVALIDATED statewide** — but
> **no longer unvalidated everywhere.** A real, working, checked pilot now
> exists for Tawang/Jang — see the callout immediately below.
> Built 2026-08-17. Pipeline: `scripts/build/build_flood_layers.py`.
> App: `webapp/products/flood/`. Bundle: `webapp/assets/flood/` (0.78 MB).

> ## ⭐ IMPORTANT — the river level forecast line: LIVE to 2 days ahead since 2026-10-06, more to build
>
> Marked by the user on 2026-10-05 so it is not lost among the other open
> items. **This is the next big FloodSense feature.**
>
> - **What:** a dotted line on each gauge graph showing where the river is
>   expected to go, in metres (cubic metres a second at the 14 flow gauges),
>   for the coming days — what Google Flood Hub draws at its "forecast"
>   gauges.
> - **Why it matters:** today we forecast only the *chance* of crossing the
>   line. Flood Hub's level line is the one thing it has at a gauge that we
>   do not ([FLOOD_HUB_AND_MOCKUP_COMPARISON.md](FLOOD_HUB_AND_MOCKUP_COMPARISON.md)).
>   It sits beside the chance; it does not replace it.
> - **What it needs:** its own model and a pre-registered test before it goes
>   on screen. The rule is already written: shown only if, on held-out
>   years, the crossing chance its range implies agrees with the checked
>   crossing chance. Two forecasts on one graph must never contradict each
>   other. → [FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md) Phase 10.
> - **Before it:** the bad-reading filter must judge jumps in metres
>   (the Murga Bridge reading of 2026-09-28, FLOOD_WHEN_PILOT_PLAN.md §13f).
>   A level forecast fed one wrong reading would draw a 97 m spike.
>   **✅ Done — the three-pass filter is live (2026-10-06).**
> - **Go-ahead given by the user, 2026-10-06.** Our own level model first;
>   Google's open model set up beside it second, as a second opinion — our
>   own model makes the call. It is also the proper cure for the open
>   "river already above its line told ~0%" fault. Starting points, the
>   tests to write first, and everything that led here:
>   **[RIVER_FORECAST_RECAP_2026-10-06.md](RIVER_FORECAST_RECAP_2026-10-06.md)**.
> - **Live since 2026-10-06:** a dotted line with a shaded likely range on
>   17 CWC gauge graphs, for 2 days after the last full day of readings.
>   Tested first: it misses by 0.13 m one day on and 0.22 m two days on,
>   and its range holds 80% of what happened (FLOOD_WHEN_PILOT_PLAN.md
>   §14). **Still to build:** grading it daily, the 14 NWDP gauges, beyond
>   2 days, upstream gauges.

> ## 🆕 2026-09-29 — the forecast learns from floods back to 2003
>
> - **The day model now learns from every verified flood from 2003**, not
>   from 2015. The verified record's 326 floods from 2003–2014 are Global
>   Flood Database confirmations of old news reports.
>   - Pre-registered test: timing +0.020 across the window and +0.028 inside
>     Arunachal; the near-here ranking held.
>   - Live timing inside Arunachal, on floods no model saw: **0.851 → 0.879**.
>   - Near-here ranking 0.893 → 0.890.
>   - River forecasts are unchanged (golden check).
> - **"Floods on record" counts from 2003** (was 2015). 189 of 751 Arunachal
>   places now have floods on record (was 180).
> - **The error the screen quotes changed shape.** In the ranges where most
>   floods fell, recorded floods ran 1.3×–6× the forecast. At its highest
>   numbers (5% and up; 19 floods) it said more than happened (about 11% said,
>   6% happened). The screen now says both.
> → [OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md) (§5c: wiring, figures,
> rollback).

> ## 2026-09-28 — soil wetness is live on flat ground; gauges sit on the right rivers
>
> - **Soil wetness now feeds the flood forecast, on flat ground only**
>   (plains and valley floors, mean slope < 5°; 380 of 1,953 rain cells). It
>   uses ERA5-Land's top-metre soil water from 16 days before each forecast
>   day, fetched from Earth Engine by the 08:30 run. If the fetch fails, flat
>   areas fall back to rain only and the issue says so.
>   - Pre-registered test on fresh years: flat-ground timing +0.017, and
>     still +0.0095 with the 16-day-old reading the live run can always get.
>   - It hurts on steep ground (flash floods; the soil is soaked all
>     monsoon), so it is not used there.
>   - It helped neither the landslide trigger nor, as 15/30-day rain, either
>     model. Live timing inside Arunachal: 0.845 → 0.851.
>   - River forecasts and hill/steep cells are unchanged (golden check).
>   → [SOIL_WETNESS_TEST.md](SOIL_WETNESS_TEST.md) (§10 has the wiring and
>   the rollback copies).
> - **Gauges placed on the map's rivers correctly.** The old rule put every
>   gauge 1.5–2 km downstream of its real spot, and 5 on a bigger neighbouring
>   river. Now each goes to the nearest river of its size, which matches
>   CWC's published catchments to ~1–2%. Changlang and Ziro are not matched
>   to places: NWDP's own coordinates for them are wrong.
> - **"Gauge on this river" fixed** for spots with a low flood chance (a
>   gauge in a narrow valley said "no gauge" at its own dot) and on wide
>   rivers (the walk down the Siang skipped cells). The "none" note now says
>   which case applies instead of assuming "a different river".
> - **Gauge graphs** show NWDP's part-days (fewer than half the day's
>   readings) as hollow dots. They are display only; no forecast uses them.
> - How FloodSense compares with Google Flood Hub, and with the dashboard
>   mock-up (what exists, what is missing, what to build next for Jang):
>   [FLOOD_HUB_AND_MOCKUP_COMPARISON.md](FLOOD_HUB_AND_MOCKUP_COMPARISON.md).
> - Gauge details: [FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md) status, and
>   [FLOOD_WHEN_PILOT_PLAN.md §13e](FLOOD_WHEN_PILOT_PLAN.md) (what the
>   gauge data itself showed).

> ## 📋 2026-09-27 — screen rework: safety checks + fixes done; headline % failed its test, ships as approximate
>
> Plan: one calibrated number for every place ("flood chance within about
> 10 km, next 7 days"), a confidence level, the river gauge only when it is
> on the place's own river, and a Flood-Hub-style gauge graph; "× usual"
> leaves the screen; no model changes → [FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md).
>
> - **Done:** unchanged-logic check (`check_live_unchanged.py`) and
>   all-screens check (`check_app_screens.py`); stale 97-point labels; the
>   Flood-prone ground screen now shows the calibrated WHERE layer; the
>   Catchments screen is an input screen again — and its rain was wrong from
>   2026-09-22 to 09-27 (catchments mapped to the old 97 points; fixed).
> - **The "near here" percentage FAILED its pre-registered test.** It ranks
>   well (AUC ~0.85), but the flood record's own rate doubled in 2024–25
>   relative to the rain, so the level is not stable → PARKED §0v.
>   **By the user's decision it now ships as APPROXIMATE**, with its measured
>   error and each place's flood evidence on screen; logged daily.
> - **The day model was retuned on record days only** (the flood record ends
>   Oct 2025; 2026 had been counted as dry). The river forecasts did not
>   change. §0p's "flood count is right" was an artefact of that — corrected.
> - **⚠️→✅ The flood record, fixed (2026-09-28).** The old Sentinel-1 screen
>   passed 97–100% of flood-free dates (§0w). A new, validated radar test
>   (97.8% correct on flood-free dates) re-checked every report; the forecast
>   now trains on the VERIFIED record — 2,185 floods confirmed by radar, the
>   Global Flood Database or a river gauge. Timing inside Arunachal on
>   verified floods: 0.845 (was 0.706 on reports). WHERE stays on the reported
>   record (tested: not better). PARKED §0x.
> - **Also done:** the gauge appears only when it is on the place's own river,
>   with a Flood-Hub-style graph; "if a flood comes" is capped at "20%+" with
>   its checked rate (the terrain correction failed its test); a "How to read
>   this forecast" page; new records from gauge crossings and people's
>   reports, graded for ranking. → FLOOD_SCREEN_PLAN.md, PARKED §0w.

> ## 🆕 2026-09-20/21 — WHERE is calibrated, and WHEN × WHERE are now joined
>
> This **supersedes** the "still WHEN-only / the map stays a relative index /
> the two are deliberately NOT multiplied" statements in the 2026-08-30
> callout below.
>
> - **WHERE is a real calibrated probability per 100 m patch** (held-out
>   calibration error 1.13% in Arunachal), trained on 2,806 satellite-
>   confirmed floods — 215 braided-channel-shift "floods" removed after a
>   label audit (§0n–§0o) — with valley-confinement features added (§0p). Geometry-only features after land cover and elevation
>   were caught scoring glacial lakes as floodplain. Physical sanity checks
>   pass. → [PARKED_HIMALAYAN_FLOOD_WHERE.md §0k](PARKED_HIMALAYAN_FLOOD_WHERE.md)
> - **WHEN runs on every rain cell, not just the 29 gauges, and is joined
>   to WHERE** into one daily forecast (`scripts/model/flood_forecast.py`),
>   replayed on 2023–26 floods nothing was tuned on, now with upstream-
>   catchment rain. Right place holds; timing is modest; the absolute level
>   inside Arunachal runs ~4× high — about half of which can't be told from
>   floods simply going unreported — so lead with "times normal". → §0l–§0p
>   of the same doc.
> - **It runs on live rain** — `scripts/model/flood_forecast_live.py` issues
>   today + a 7-day outlook from Open-Meteo, sharing the landslide side's
>   fetch. Measured: the live feed ranks flood days as well as satellite
>   rain (0.725 both, inside Arunachal, unseen years). Runs daily at 08:30 as
>   a scheduled task (since 2026-09-22), and shown in the web app as
>   FloodSense's first screen, **Live forecast** (`webapp/products/flood/live.py`).
>   The daily run writes a small snapshot, `webapp/assets/flood/live_forecast.json`
>   (~240 KB), and the free-hosted app reads it. The public site shows the last
>   snapshot pushed and says how old it is. → §0q.
> - **At the 32 gauged rivers it now reads the river itself** (2026-09-21).
>   Live CWC/NWDP readings plus rain give a calibrated chance of each river
>   reaching its threshold, 1–3 days ahead. At official-danger gauges, lead
>   1, a 25% warning catches 58% of crossings (rain alone: 11%) and is right
>   56% of the time. On onset days (the river still below danger) AUC goes
>   from 0.87 to 0.93. Every forecast is logged and graded automatically
>   against the gauge; the track record lives in `records/flood_forecast/`
>   (committable, unlike `data/`). → [FLOOD_WHEN_PILOT_PLAN.md §13](FLOOD_WHEN_PILOT_PLAN.md)
> - **Gauge readings on the map were tested and did NOT help** (2026-09-22).
>   The map's timing got slightly worse (0.838 → 0.829), so it is not shipped;
>   the reading stays a per-river number. → PARKED_HIMALAYAN_FLOOD_WHERE.md §0s
> - **One forecast screen, with place search** (2026-09-25). The old
>   rule-based "Rain index" screen (flood-prone ground × upstream rain, never
>   checked against real floods) is removed: two forecasts that could
>   disagree only confused things. "Live forecast" now has place search,
>   click-on-map and a side panel for the chosen spot. The panel shows three
>   separate facts, deliberately NOT multiplied into one "X% today":
>   - the spot's chance of going under water if a flood comes, with the
>     nearest floodable ground when the spot itself is high (Pasighat town
>     0.3%, the Siang bank 1 km away 28%);
>   - its ~10 km area's "× an ordinary day" for each of the 7 days;
>   - the nearest river gauge's chance, labelled as nearest, since it can be
>     on a different river. *(Superseded 2026-09-27: only a gauge on the
>     place's own river is shown — see the callouts above.)*
>
>   Flood-prone ground and Catchments stay as explainer screens.
> - **What can honestly be quoted (decided 2026-09-21; updated 2026-09-28):**
>   - **Per gauged river:** "X% chance it reaches its threshold today". This
>     is the strongest number; calibrated, it says 20% and ~20% happen.
>   - **Per place (NEW, shown since 2026-09-27):** "flood chance within about
>     10 km, next 7 days: X% — approximate". It failed its pre-registered
>     calibration test (the record's own rate moved ~2× between years), so it
>     is always quoted with its measured error (re-measured 2026-09-29 for the
>     model that learns from 2003): in the ranges where most floods fell,
>     recorded floods ran 1.3×–6× the forecast; at its highest numbers (5%
>     and up, few floods) it said more than happened (~11% said, ~6%
>     happened); ranking right ~89 times in 100. Where floods are on record
>     (counted from 2003), ~1.5× more get recorded than forecast; where none
>     are, ~2.0×. The screen reads these from the snapshot, never typed.
>     → [FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md), PARKED §0v,
>     [OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md).
>   - **Soil wetness (since 2026-09-28):** flat ground only (plains, valley
>     floors), from ERA5-Land 16 days before the day. It improves timing
>     there on fresh test years; it is not used on steep ground or for
>     landslides, where it did not help. → [SOIL_WETNESS_TEST.md](SOIL_WETNESS_TEST.md).
>   - ~~Per ~10 km area: "N× normal"~~ — still computed and logged, no
>     longer shown (it read like the rain handed back).
>   - **Per 100 m spot, given a flood:** up to ~44% — but inside Arunachal
>     the top ranges come true about half as often (Phase 3 target).
>   - **Do NOT quote** "this spot has X% chance today": the max ever was
>     0.72%, and it runs ~4× high in Arunachal.
>   - These are budget/data limits, not physics. Local truth (Jang), more
>     gauges, and a steadier flood record lift them.
> - The old rule-based `floodprone.npz` still ships beside the new
>   `floodprob.npz` for comparison.

> ## ⭐⭐⭐ CRITICAL — 2026-08-30: the Tawang pilot proved both WHEN and WHERE for real, on real data
>
> Full record, decisions, bugs found/fixed, and the confirmed next step:
> [FLOOD_WHEN_PILOT_PLAN.md](FLOOD_WHEN_PILOT_PLAN.md). **Read that before
> re-deriving any of this.** Summary:
>
> - **WHEN:** both of the state's open government river networks are now
>   covered — 17 CWC stations (major/medium rivers) plus 12 of NWDP's 14
>   small-river stations, 29 total, each with trained, cross-validated
>   models genuinely blended into the live score. Two independent real
>   data-quality problems found and fixed along the way: CWC stations whose
>   published danger level was never once reached in the whole record (real
>   calm rivers, not a bug), and NWDP's raw feed carrying explicit
>   sentinel/fault-code readings pinned at ±99999.99 (a different problem,
>   fixed differently).
> - **WHERE:** real Sentinel-1 satellite evidence of standing water,
>   checked at **28 distinct river locations statewide — 27 show a real
>   positive signal**, including Jang valley across 12 independent confirmed
>   flood dates. One honest, reproducible miss (Kanubari, checked twice, both
>   zero) reported rather than hidden.
> - **✅ CALIBRATED, 2026-09-01 — it IS a real probability now** (plan doc
>   §10). Measured on years the calibrator never saw: calibration error
>   **10.91% → 0.03%**, Brier skill vs climatology **−2.67 → +0.09** (the
>   raw score really was worse than useless as a percentage — now measured,
>   not assumed). On its top 1% of days it says 20.4% and 19.7% actually
>   flood: **26× the base rate**. It never claims 90%, and with
>   rainfall-only inputs on a 0.76% event it should not.
> - **Verified event by event:** across **379 real flood episodes**, 76.5%
>   reached ELEVATED or above and 38.8% reached HIGH/SEVERE — **23.5% were
>   missed outright, listed by name** in
>   `reports/flood_when_event_verification.json`.
> - **⚠️ Two different probabilities, never blur them:** 13 stations carry a
>   published CWC danger level ("P(crosses the official danger level)" — the
>   number to quote); 16 use a self-derived top-2% label ("P(this river's own
>   wettest 2% of days)" — real, but its base rate follows from its own
>   definition).
> - **Still WHEN-only.** The static WHERE layer is not calibrated, so the two
>   are deliberately NOT multiplied into one headline number: at a gauge,
>   quote the probability; away from one, the map stays a relative index.
> - **Operational scorer:** `scripts/model/predict_flood_when.py` issues the
>   calibrated probability and alert band for all 29 stations for any date.
>   Hindcast input path today (archived IMERG); the live rainfall tap is the
>   remaining wiring, and changes none of the numbers.
>
> Everywhere without a gauge is still the original, unvalidated relative
> index — none of this pilot changes that yet.
>
> **⏸️ 2026-09-02 — WHERE calibration expanded (34→74 events) and a
> Himalaya-pooled WHERE player PAUSED mid-proof, deliberately, on the
> user's own instruction.** Read
> [PARKED_HIMALAYAN_FLOOD_WHERE.md](PARKED_HIMALAYAN_FLOOD_WHERE.md) before
> touching WHERE again — it has what's already proven (9/9 real events
> across Bhutan/Nepal/Sikkim), what's on disk, and the one decision still
> waiting on the user before the full rollout runs.

> ## ⭐⭐⭐ CRITICAL — read before touching flood again: real river gauge data exists, free, BOTH tiers
>
> **2026-08-20.** Two government sources, verified and download-confirmed, between them cover the
> major rivers AND a real sample of small/medium rivers:
>
> - `ffs.india-water.gov.in` (CWC's own live flood site) — open API, no login — **55 years of real
>   measured river level** for Arunachal's major gauged rivers (Passighat/Siang etc.), still
>   updating today, plus official danger/warning thresholds per station.
> - `nwdp.nwic.gov.in` (NWIC's open data portal) — documented, standard API, download verified,
>   openly licensed for flood-forecasting use — **750k+ real discharge readings across 14
>   small/medium rivers** (Ziro, Tenga, Sagalee, Kamlang, Deomali, and 9 others) spanning many
>   districts, not just the trunk rivers.
>
> This was the single biggest gap this whole document is built around ("Validation — the honest
> part," below). **It is very likely no longer true that we have zero local evidence — on either
> tier.** Full detail: `docs/data_research/DATA_VERIFICATION.md`, Section C, Findings 11 and 12.
> Memory: `cwc-ffs-live-river-gauge-data`, `nwdp-small-stream-discharge-data`. **Do not re-derive
> this from scratch — read those first.**

## The shape

Identical to SlopeSense, because the physics splits the same way:

```
landslide hazard = susceptibility     (where, static)  x trigger        (when, daily)
flood hazard     = flood-prone ground (where, static)  x catchment rain (when, daily)
```

That symmetry is why FloodSense reuses the whole spine — grid, boundary,
search, maps, rainfall fetch, climatology — and adds only two files of its own
maths.

## The static half — where water collects

**HAND** (height above nearest drainage), multiplied by the **size of the
drainage** it sits above. Both terms are needed: two metres above the Siang and
two metres above a hillside creek are not the same statement.

| Parameter | Value | Why |
|---|---|---|
| Channel definition | ≥ 100 km² upstream | See "the threshold that mattered" below |
| HAND ceiling | 25 m | Above this, nothing is flood-prone at any river size |
| Size scaling | log, 100 → 10,000 km² | Discharge grows with area far more slowly than area does |
| Min low-lying share | 5% of a display cell | Stops one clipped river corner painting a hillside |

Result: **4.88% of the grid is flood-prone**, spread across 5 classes.

### The threshold that mattered

The channel network was first defined at **≥ 10 km² upstream**. Measured
consequences of that choice:

- 90.7% of the resulting flood-prone ground sat beside a channel **smaller than
  2,000 km²**, with a **median catchment of 47 km²**
- 10.67% of the grid was called floodplain
- Tawang — a ridge town at 3,000 m — came out as class 2, and Ziro as class 3

Raising it to **100 km²** and using one definition of "river" end to end
(network, HAND measured to it, size weighting) fixed all three:

| Place | at 10 km² | at 100 km² | reality |
|---|---|---|---|
| Pasighat (on the Siang) | class 5 | class 5 | on a 18,126 km² river |
| Tezu (on the Lohit) | class 3 | **class 5** | on a 19,338 km² river |
| Tawang (3,000 m ridge) | class 2 | **class 0** | 705 m above drainage |
| Anini (high Dibang) | class 3 | **class 0** | — |

The old threshold also contradicted the module's own headline — that mountain
streams are a *watch*, not a forecast — while painting their banks as
floodplain.

### HAND: flow-path vs nearest-channel

The textbook definition follows the flow path. It was built first and rejected
on measurement:

- The 100 m DEM is not depression-filled. Raw, **34% of in-state cells** end in
  a pit rather than a channel — and this is not confined to ridges: **29% of
  cells within 250 m of a river** were affected.
- Filling with morphological reconstruction (Wang–Liu) raised 4.43% of cells
  but made coverage **worse** (65.7% → 60.9%), because a filled depression is
  flat and a flat cell has no steepest-descent neighbour.
- Scored against observed inundation, flow-path HAND did **no better** than the
  plan-view approximation (0.649 vs 0.666 on the original, uncorrected metric).

So the shipped layer measures to the **nearest channel in plan view**: complete
coverage, simpler, and no worse. In terrain this steep the nearest channel is
nearly always the one you would flow to.

## The daily half — catchment rain

A slope fails from rain landing **on** it. A river rises from rain landing
**anywhere upstream**. So rainfall is pooled over 1,680 HydroBASINS level-12
catchments and carried downstream before it becomes a forecast.

- Routing graph: `NEXT_DOWN`, with topological order taken from `UP_AREA`
  ascending — **verified in the build**, 0 basins ordered after their receiver
- Same rainfall points and same climatology as SlopeSense (97 points at
  ~33 km until 2026-09-22, 219 at ~22 km since), in `assets/base/` because
  rainfall is spine, not hazard
- ⚠️ Each catchment's rain point (`rain_pt` in `catchments.npz`) is a
  *position* in `points.json`. When the points went from 97 to 219 this
  mapping was not rebuilt, so from 2026-09-22 to 2026-09-27 every catchment
  on the Catchments screen read rain from another place (median 119 km away).
  Fixed 2026-09-27: `build_flood_layers.py --rain-points-only` re-maps it,
  the web export now does that whenever it writes the points, and the app
  refuses a mapping whose recorded point count doesn't match.
- One cached fetch serves both modules, so opening the second costs no API call

### The response curve

Passing the catchment percentile straight through produced a forecast that was
really the static map wearing a date:

| | median-day High+ | week's range |
|---|---|---|
| percentile passed through | 34% | 33.5 – 37.0% (3.5 pts) |
| response curve | 10–17% | 10.5 – 17.4% (6.9 pts) |

Rivers rise on rain that is *unusual for their catchment*, and the median day
scores 0.50 by construction. The response is therefore near zero below the 35th
percentile and climbs steeply above it, with a small floor so floodplain still
shows as Very Low on a calm day — "this is floodplain and nothing is coming"
and "this is not floodplain" must not render the same.

## Validation — the honest part

**There is none, and the module says so on its own Method page.**

The only obtainable observed flood record for Arunachal is Bhuvan's aggregated
2003–2020 extent, served as **rendered map tiles**. Measured against the
terrain:

- **70.5%** of the pixels it marks flooded lie on slopes steeper than **15°**
- **31.3%** lie on slopes steeper than **25°**

Water does not pond on a cliff. That is tile smear, not observation, and it
cannot referee anything.

Scores against it, reported on the Method page precisely because they are bad:

| Test | Result | Reading |
|---|---|---|
| Pixel level, tie-corrected AUC | **0.530** | Chance is 0.50 |
| Catchment level, 706 basins, Spearman | **−0.023** | No relationship |

> ⚠️ **A tie-handling bug inflated this to 0.879 before it was caught.** 93% of
> cells score exactly 0, so ties dominate every comparison; breaking them by
> sort order rather than averaging ranks turned chance into an apparently
> strong result. `_auc()` in the builder now uses average ranks and is verified
> against perfect / reversed / all-tied cases.

**What this means:** the layer rests on standard, well-understood physics and
on *no local evidence whatsoever*. It is a well-founded hypothesis about
Arunachal, not a measured fact about it.

**What would validate it:** district inundation reports with dates and
locations; Sentinel-1 water mapping for named events; river gauge stage records.

## Limits stated in the product

- **No depth, ever** — needs 2-D hydraulic modelling on LiDAR
- **Small streams are a watch, not a forecast** — most catchments sit below what
  any global discharge model resolves
- **No dam releases** — several of these rivers are regulated
- **Rainfall sampled at ~22 km** (219 points since 2026-09-22; ~33 km before) —
  a small basin inherits its neighbour's weather
- **GloFAS not in this build** — 2 files on disk where a climatology needs years
  of reanalysis. A download, not a permission, and the next thing to do.

## Next

> **2026-08-28 — full buildable-now vs blocked breakdown, and the panel/ensemble
> plan for both flood sides, is now written up in
> [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §7.** Read that before re-deriving
> either list from scratch.

1. **GloFAS reanalysis archive** → discharge anomaly on the five large rivers,
   turning the "large river" tier from catchment-rain into real river forecast
2. ~~River gauges (the one genuine ask of the state)~~ → **⭐ found free, not asked for.**
   CWC's `ffs.india-water.gov.in` has 55 years of real level data for Arunachal's
   gauged rivers (Passighat/Siang: 93,145 readings, 1971→today, still live), plus
   official danger/warning thresholds per station. See the callout above. This is
   now a **build task** (archive it, derive labels, train on it), not an ask —
   the exact two-step recipe (backtest the current rule, then train/hold-out-test
   a real second model) is in [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §7.
3. ~~Any dated, located flood observation at all~~ → **the CWC gauge history *is*
   this**, for the gauged rivers: crossing a station's warning/danger level on a
   given date is an objective, government-defined flood/no-flood label. NWDP's
   discharge series (item 4) gives the same kind of raw material for 14 small/
   medium rivers, though without a published danger threshold to define "flood"
   from — that would need to be estimated from the series itself (e.g. a high
   percentile of that station's own history).
4. **⭐ NWDP small-river discharge (new, 2026-08-20)** — 750k+ readings, 14
   stations, real small/medium rivers across many districts. See the callout
   above. Still only 14 stations, not the whole network — genuinely new ground
   truth, not full coverage.
4. **NESDR's Waterbody layer, wet-half vs dry-half** — NESAC runs a deep-learning
   land-cover classifier over Arunachal every ~6 months, and the Jul–Dec 2025
   cycle ships a dedicated Waterbody class alongside the drier Jan–Jun 2025 and
   Apr–Dec 2024 combined maps. Comparing them is a candidate for real, dated,
   local flood-season evidence — the first one since the Bhuvan layer above was
   rejected. It is a feature layer NESAC itself never ground-verified, not a
   flood record, so this is a lead to test, not a result to cite. Access route
   and caveats logged in `docs/data_research/DATA_VERIFICATION.md` §G.
