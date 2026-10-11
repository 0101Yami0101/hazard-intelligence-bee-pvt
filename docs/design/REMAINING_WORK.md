# What is left to do — as of 2026-10-11

The working list made on 2026-10-09 ("push the application as far as it
will go now"), with everything done since crossed off. One place to look so
nothing is lost. The soil-erosion module for Assam is **not** on this list
by the user's instruction (it has its own plan: EROSION_PLAN.md).

## 1. Open, not started

| # | Item | Size (estimate) | Notes |
|---|---|---|---|
| **15** | **Landslide timing learned from the whole Himalaya** | 3-hour download + about a day | The biggest gain left for the landslide forecast: its "when" half rests on 84 dated landslides in the state; the Himalayan arc has about 800 more. The download was stopped at 10% and resumes. Steps: [PARKED_HIMALAYAN_POOLED_TRIGGER.md](PARKED_HIMALAYAN_POOLED_TRIGGER.md). It would also firm up the roughest number on the place card ("High = 3×", from 8 landslides) and settle whether a weak slope should read High on a below-normal rain day ([LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) §4). |
| **16b** | **The level line beyond 2 days** | 1–2 days | May fail: beyond 2 days the line and the chance disagreed too often when it was last looked at. Rules first. FLOOD_WHEN_PILOT_PLAN.md §14. |
| **21** | **News-feed intake for flood reports** | 2–3 days | So the flood chance *near a place* can be graded as records arrive. Today new records come only from gauge crossings and the report form. |
| **17** | **Google's open river model beside ours** | 3–5 days | As a second opinion, not a feed. A new model to install, feed and compare. |

## 2. Outside the code

| # | Item | Notes |
|---|---|---|
| **23** | **Data request letters** | [GOV_DATA_REQUEST_LIST.md](GOV_DATA_REQUEST_LIST.md). Added by this round of work: **dam release schedules** (Pare HEP's level follows the gates, FLOOD_WHEN_PILOT_PLAN.md §20) and **CWC's danger level for Rho Basti** (§19b). Road-block logs with chainage remain the best ask for landslides. |
| **24** | **Bhoonidhi sign-up and the Inner Line Permit** | |

## 3. Parked on purpose

| # | Item | Where |
|---|---|---|
| **2** | Move the daily forecast off this PC | [PARKED_OFF_PC_DAILY_RUN.md](PARKED_OFF_PC_DAILY_RUN.md) |
| **19** | Finer rain (11 km in place of 22 km), after item 2 | the same file, §4 |

Un-park when days are missed or late again: two days were missed and six
ran late in the first three weeks.

## 4. Decisions waiting on the user

1. **Pare HEP's flood chance.** Its level line is off (a dam gauge). It
   still gets a *chance* of reaching a line that rests on 62 days of
   record. Keep, mark as unsure, or remove? Removing changes the logged
   record. FLOOD_WHEN_PILOT_PLAN.md §20.
2. **Dash only days 6 and 7?** Measured on two monsoons, days 4 and 5 rank
   as well as days 1–3; the drop is at 6 and 7. Left as it is (4–7 dashed)
   until a rule is written and next monsoon's data is in.
   [LEAD_DAY_TEST.md](LEAD_DAY_TEST.md) §3.
3. **"High" on a below-normal rain day.** Looked at, left alone, with the
   reasons. [LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) §4.
4. **Tighter screenshots** in the brief and deck (the new ones have a wider
   empty margin than the old).
5. **Local `main`** still sits on the old public history, so the editor
   lists about 240 files as changed. Pointing it at the private backup
   would clear that; it changes nothing that is deployed.

## 5. Small things noticed, not fixed

- **The first Changlang station** has wrong coordinates and is not linked
  to places (§19a deals only with the second).
- **18 districts.** The district layer is the older 18-district set.
- **The shared look lives in `webapp/products/flood/ui.py`.** Moving it to
  `core/` is a tidy-up.
- **3D view** stays parked (`WIP_3D`).
- **The script page's slide thumbnails** (`PRESENTATION_SCRIPT.html`) were
  not re-made when the deck's pictures were.
- **The flood log does not record the time of issue**, so a late run is not
  visible in it (to fix with item 2).
- **Evidence page figures** ("9,555 days", "8.2 M cells") are typed in, not
  read from files.
- **The landslide log** is written on this PC only; the hosted app does not
  log.

## 6. Done since 2026-10-09 (for the record)

| # | Item | Where it is written up |
|---|---|---|
| 1 | Private backup of the whole project | memory; this file §7 |
| 3, 10 | Withdrawn flood record; small display fixes | FLOOD_SCREEN_PLAN.md |
| 4, 5 | Four false floods removed; day model re-fitted | FLOOD_WHEN_PILOT_PLAN.md §15 |
| 6 | SlopeSense forecasts written down daily | ROADMAP_LANDSLIDE.md |
| 7 | Level line graded daily | FLOOD_WHEN_PILOT_PLAN.md §16 |
| 8 | River above its line shows "unsure" (a stopgap; seven cures tested) | §17–§18 |
| 9 | Full-screen box on all three flood pages | FLOOD_SCREEN_PLAN.md |
| 11 | Phone and tablet check, with fixes | FLOOD_SCREEN_PLAN.md |
| 12 | SlopeSense in the FloodSense look; district figures on real outlines | [SLOPESENSE_SCREEN.md](SLOPESENSE_SCREEN.md) |
| 13 | One-page forecast report | [FORECAST_REPORT.md](FORECAST_REPORT.md) |
| 14 | Brief, deck and script refreshed | FORECAST_REPORT.md, end |
| 16 | Upstream gauges for the high-river fault: tested, no gain | §17 |
| 18 | Forecast graded by lead day | [LEAD_DAY_TEST.md](LEAD_DAY_TEST.md) |
| 20 | Gauge housekeeping, then both models re-taught | §19 |
| 22 | Compared with GSI's 50 m map; GSI's map re-fetched correctly | [GSI_MAP_COMPARISON.md](GSI_MAP_COMPARISON.md) |
| – | Pare HEP: no level line for a dam gauge | §20 |
| – | Real numbers ("3× the usual") in place of "4 of 5" | [LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) |

## 7. What is deployed, and what is backed up

**Public app** — `hazard-intelligence-bee`, branch `v2`, commit `84d56f1`
(2026-10-11). App files only (`webapp`, `requirements.txt`, `runtime.txt`,
`.streamlit`): 18 files changed. It carries SlopeSense's new look and
measured figures, the one-page report, the corrected district figures, the
phone fixes, the "unsure" rule, Pare HEP's note, and the flood forecast
issued 11 October from the re-taught models. Models, logs, training scripts
and internal docs are not on it. The old app (`SlopeSense2`, `main`) was not
touched.

**The hosted flood forecast is frozen at that issue** until someone pushes a
newer snapshot: the daily 08:30 run on this PC does not push (item 2).

**Checked before the push, on the host's package versions** (Streamlit 1.65,
pandas 3.0, in a clean environment): all 34 screens open; phone and tablet
survey 56 of 56 with no fault; desktop 18 of 18; the report downloads 5 of
5; the flood full-screen panel 22 of 22. (Two of those needed a second run:
the test server had not finished starting.)

**Private backup** — `hazard-intelligence-bee-pvt`, `main`, tip `d8caa82`
plus the commit that adds this note: the whole working tree as it stands
(689 files: code, app, docs, models, records, reports), everything
`.gitignore` excludes left out (`data/`, `logs/`, `misc/`, `docs/investor`,
`docs/temp`, `.env`). Its `v2` is the same commit as the public one. It does
not update itself.
