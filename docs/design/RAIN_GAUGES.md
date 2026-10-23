# Ground rain gauges in SlideSense and FloodSense

> **⭐ The user's standing instruction (2026-10-20):** *"make sure we go back to the other
> modules to add the newly found rain gauge data wherever applicable."* This file is the
> working record for that: plan, tests written before running, results, decisions. Tracked as
> [REMAINING_WORK.md](REMAINING_WORK.md) **#25**. Started 2026-10-20.

## 0 · Where things stand

| Part | What | Status |
|---|---|---|
| A | Gauge rain vs the two rain sources the platform uses (IMERG satellite, Open-Meteo) | ✅ Done 2026-10-20: the two tie at the gauges (0.539 vs 0.538); Open-Meteo, the live one, catches more heavy days. No change |
| B | SlideSense: rain at the gauges on dated landslide days | ✅ Done 2026-10-20: gauges call landslide days unusual *less* often than the sources (64 % vs 81–94 %). No case for gauge input. No change |
| C0 | Is the CWC flood site's `MPS` reading live rain? | ✅ Done 2026-10-20: **yes**, mm, 7 of 9 live stations match NWDP on 87–96 % of days; about 7 h behind. **The platform's first live ground rain feed** |
| C | FloodSense: a river station's own rain in its gauge chance model | ✅ Tested 2026-10-20: **not adopted**, failed the gain gate. One small lead-1 signal is logged as a candidate for a forward test in the 2027 monsoon |
| D | Grading the forecasts' rain against gauges | 🔄 **Running:** the tool is built and grades every kept issue; first fair reading after the 2027 monsoon starts (≥ 50 wet gauge-days per lead) |
| E | Jang pilot: the Jang rain station against both sources | ✅ Reported in A: both sources weakest at Jang (3-day agreement 0.36 / 0.44) |

**In one line (2026-10-20):** ground gauges did not improve either forecast where they were
tested, and neither forecast changes. What they add is **proof**: a live, open ground check of
the rain both forecasts run on (Part D), and a measured limit (single points see only about a
third of the gauge's own unusual spells, §3).

**A rule for this whole piece of work.** The daily forecast moved to the cloud (Modal) on
2026-10-20 and is in a 7-day side-by-side trial against the PC
([PARKED_OFF_PC_DAILY_RUN.md](PARKED_OFF_PC_DAILY_RUN.md) §0). Nothing here changes live
forecast code or models until that trial passes. After any change that does go live, the
cloud must be redeployed.

## 1 · What the platform uses today, and why gauges matter

- **Neither forecast uses ground rain gauges.**
- **IMERG** (satellite, daily, 0.1°, since 2000) is the history the landslide trigger was
  *tested* on (72 dated events, AUC 0.768), and what the flood models were trained on.
- **Open-Meteo** (weather-model rain) is what both forecasts run on *live*, today and the
  next 7 days, scored against Open-Meteo's own history at 219 points (`webapp/core/rainfall.py`).
  That keeps one source end to end.
- Measured earlier: Open-Meteo is 1.68× wetter than IMERG, with a daily correlation of
  only 0.32. The two disagree a lot, and **nothing has said which of them the ground agrees
  with.**
- The gauges: the Central Water Commission's daily rain at its river stations, open on
  NWDP. `scripts/fetch/fetch_47_cwc_rainfall.py`; real spans per station in
  `reports/cwc_rain_inventory.csv`. Arunachal has 18 stations, several with 30–54 years,
  one at Jang. The records list rainy days only (no zeros).

## 2 · Part A — the test, written before running

**Question:** at the gauges, which source tracks the ground's rain better, IMERG or
Open-Meteo? In amount, in heavy days, and above all in **"how unusual is this rain for this
place"**, which is what the landslide trigger and the flood day-model actually use.

| Piece | Rule |
|---|---|
| Gauges | CWC manual daily rain, all files, de-duplicated by station and day; station inside the IMERG archive's box (26.55–29.55° N, 91.35–97.55° E), so north Assam stations count too; coordinates checked against the box |
| Counted months | **April–October only**, and only months in which the gauge recorded **≥ 5 rain days**. Within a counted month an unlisted day is dry (0 mm). Dry-season months are left out: with few rain days, a missing record cannot be told from a dry spell |
| IMERG at a gauge | The 0.1° cell containing it (`data/interim/rainfall/precip_mm.npy`) |
| Open-Meteo at a gauge | The nearest of the 219 forecast points, if within 0.15°; otherwise not compared (`data/interim/rainfall_om/precip_mm.npy`) |
| Periods | Each source against the gauge on their own overlap (IMERG 2000–2026, Open-Meteo 2010–2026), **and** a head-to-head on the common window 2010-01-01 → 2026-07-29 |
| Metrics, per station | (1) total ratio source ÷ gauge over counted months; (2) Spearman ρ of daily rain; (3) heavy days: of gauge days ≥ 50 mm, the share where the source has ≥ 20 mm; (4) **"unusual" agreement**: 3-day and 7-day totals turned into percentiles within each series' own counted months, then Spearman ρ between gauge and source percentiles, and the share of the gauge's top-10% days that are also in the source's top 10% |
| Across stations | Medians, and the count of stations where each source wins on metric 4 |
| Height | Station height from the DEM; Spearman of the IMERG ratio against height (the docs flag drift above 2,500 m) |
| **Reading, fixed now** | No pass bar: this is a measurement. If Open-Meteo's median "unusual" agreement (metric 4, 3-day ρ) is **≥ 0.10 below** IMERG's, that becomes a finding for SlideSense: the live trigger runs on the weaker source at the ground. It is then logged as a test to run after the cloud trial, not changed now. If they are within 0.10, both are equally (in)adequate at the gauges and nothing changes |
| Jang (part E) | Reported on its own: Meteorological Station Jang, 2017→ |

## 3 · Results

*(appended below as they come, newest last)*

### 2026-10-20 · Part A results — gauges vs IMERG vs Open-Meteo

`scripts/inspect/gauge_vs_rain_sources.py` → `reports/gauge_vs_rain_sources.{csv,json}`. Run
exactly as written in §2.

- **43 gauges** inside the IMERG box (Arunachal and north Assam); **21** also within 0.15°
  of an Open-Meteo point (the head-to-head).
- **Head-to-head, medians over the 21:**

  | Metric | IMERG | Open-Meteo (live source) |
  |---|---|---|
  | **"Unusual" 3-day agreement, ρ** | **0.539** | **0.538** |
  | "Unusual" 7-day agreement, ρ | 0.560 | 0.542 |
  | Gauge's top-10% 3-day spells also top 10% | 0.321 | 0.335 |
  | Daily ρ | 0.385 | 0.428 |
  | Heavy days caught (gauge ≥ 50 mm → source ≥ 20 mm) | 0.493 | **0.576** |
  | Total ÷ gauge | 1.27 | 1.63 |

  Station wins on 3-day ρ: Open-Meteo 15, IMERG 6, mostly by small margins.
- **Reading, as fixed beforehand:** the gap on 3-day "unusual" agreement is 0.001, well
  within 0.10. **No change indicated.** The live forecasts already run on the source that is
  at least as good at the gauges, and better at catching heavy days.
- **The limit this measures, worth saying plainly:** at a single point, both sources flag only
  about **a third** of the gauge's own most unusual 3-day spells. Point rain is patchier than
  an 11 km cell or a weather-model point can see. That is the "rain half is broad" limit in
  the brief, now with a number. Ground gauges or radar are what lift it.
- **Height:** no clear drift of IMERG with station height in this sample (ρ −0.12). Only 4
  gauges sit above 1,000 m: Jang 3,524 m, China Bridge and Rho Basti 2,601 m, Kibithu 1,228 m.
- **Jang (part E):** 63 counted months (2017→). Both sources are weakest here: 3-day
  agreement 0.355 for IMERG and 0.444 for Open-Meteo; totals 1.25× and 2.41× the gauge.
- **Gauges that look incomplete:** Daporizo (sources 5.7–8.4× the gauge), Yazali,
  Yingkiong and Seppa (2–4×). Probably missing records, since the files list rainy days
  only. Read their numbers with care.

## 4 · Part B — rain at the gauges on dated landslide days, written before running

**Question:** on the days landslides were recorded, was the rain at the nearest ground gauge
unusual, and more or less so than the two sources said?

| Piece | Rule |
|---|---|
| Events | NASA GLC dated landslides in Arunachal (`nasa-glc_landslides_point_arunachal.geojson`, 99 with dates) |
| Gauge for an event | The nearest gauge within **25 km** whose event month is a counted month (Part A's rule) |
| Score, the trigger's own | Mean of the 3-day and 7-day rain percentiles, each against that series' own **May–October** distribution (the trigger's `MONSOON = (5, 10)`), on the event day |
| Sources | Gauge; IMERG at the gauge's cell; Open-Meteo at the point nearest the gauge (≤ 0.15°); each on the same events |
| Reported | Per source: number of events, median score, share of events with score ≥ 0.75 (the trigger's "high" operating point is 0.75) |
| Reading | No bar; small n. If the gauge says "unusual" (≥ 0.75) clearly more often than the sources on the same events, the sources miss local storms at landslides, which is a case for gauge input near gauged places. If not, the trigger's misses are not a rain-source problem |

### 2026-10-20 · Part B results — rain at the gauges on dated landslide days

`scripts/inspect/gauge_landslide_days.py` → `reports/gauge_landslide_days.{csv,json}`. Run
exactly as written in §4. (§4 said "99 with dates". The file holds **90**, the number already
on record; 99 was a slip in writing the rule, and nothing else changes.)

- **42 of the 90 events** have a gauge within 25 km in a counted month. They fall on 13 gauges
  and **32 distinct days**: 9 events sit at Meteorological Station Chimpu on 2017-07-01 and
  2017-07-09, so the real sample is smaller than 42.

  | Same events | n | Gauge: median score / share ≥ 0.75 | IMERG | Open-Meteo |
  |---|---|---|---|---|
  | Gauge vs IMERG | 42 | 0.804 / **0.64** | 0.928 / **0.81** | — |
  | Gauge vs Open-Meteo | 31 | 0.795 / **0.65** | — | 0.913 / **0.94** |
  | All three | 31 | 0.795 / 0.65 | 0.942 / 0.81 | 0.913 / 0.94 |
  | One per distinct day (mean) | 32 | 0.777 / 0.59 | 0.920 / 0.75 | 0.863 / 0.63 |

  When they disagree: the gauge said "not unusual" while IMERG said "unusual" on 12 events;
  the other way round on 5.
- **Reading, as fixed beforehand:** the gauges did **not** call landslide days unusual more
  often than the two sources. They did it less often. So the trigger's misses are **not** a
  rain-source problem that gauges would fix, and this gives no case for gauge input to
  SlideSense's trigger.
- **Why the gauges read lower, most likely (not tested):** (1) river gauges sit in valleys up
  to 25 km from the slope, and the storm that moves a hillside need not reach the valley
  floor; an 11 km cell or a model point averages over both; (2) incomplete records: an
  unlisted day counts as dry, which pulls a gauge's score down (§3 lists the gauges that look
  incomplete); (3) small sample with one cluster.
- **What it does say, usefully:** both area sources score the landslide days high (IMERG 81%,
  Open-Meteo 94% at or above the "high" point). That fits the trigger's tested AUC of 0.768.
  SlideSense keeps Open-Meteo live and IMERG for history. **No change.**

### 2026-10-20 · Two facts found while planning Parts C and D

1. **NWDP's rain files arrive late.** The newest readings in the 2026 files, fetched today
   (2026-10-20), end 2026-10-04 to 10-11 for most Arunachal stations (Seppa 10-17). Some Assam
   stations stopped in January–June. That is **1–2 weeks behind, in batches**. NWDP is fine for
   history and grading but **cannot feed a live forecast**. Part C as first written (a live
   gauge input) was blocked by this, not by the cloud trial.
2. **The CWC flood-forecasting site carries live rain at 9 of our 18 river stations.**
   `ffs.india-water.gov.in`, the API whose river levels FloodSense already reads live, has a
   datatype `MPS` at Kibithu, Tuting, Pangin, Passighat, Miao, Namsai, Daporizo, Seppa and
   Bhalukpong. Its readings run **to this morning** (2026-10-20 05:30) and back to 1971–2005.
   The 2026-08-20 note that "rainfall datatypes stop around 2021" was about other codes; it
   missed this one. One reading a day at 08:30 until 2017, then mostly 3-hourly since 2018.
   Before 1993, only the half-year from about April to October. Rho Basti, Yinkiang and
   Lemeking have it only to 2023–24. Murga Bridge, Jollang, Doimukh, Pagoda, Tamen and Pare
   HEP have none. `scripts/fetch/fetch_48_ffs_rain.py` → `data/raw/11_gauges/cwc/{code}_mps.csv`.
   **Whether `MPS` is rain in mm is not assumed. Part C0 checks it.**

3. **Part D is possible today for SlideSense.** Each daily issue is kept whole in
   `records/landslide_forecast/issues/<day>.npz`: `rain_mm` (the next 7 days × 219 points) and
   `all_rain_mm` (10 past + 8 ahead). Issues have been kept since 2026-10-10 (9 so far). In the
   cloud they live in the Modal volume. FloodSense's logs (`area_outlook.csv`,
   `gauge_forecasts.csv`) keep the chances but **not the rain** behind them.

## 5 · Part C0 — is `MPS` rain? Written before running

| Piece | Rule |
|---|---|
| Stations | The 9 with `MPS` (fact 2 above), each matched to the NWDP manual-daily station of the same place (names checked by hand, distance ≤ 5 km) |
| A day's `MPS` total | If the day has only an 08:30 reading: that value. If it has more than one reading: the sum of the readings from 11:30 the day before to 08:30 that day, the 24 h ending 08:30, the Indian rain day. Days with some but not all of the 8 three-hourly slots are reported, and left out of the match |
| Alignment | `MPS` day d against NWDP day d−1, d, d+1. The best lag overall is reported and then applied to **every** station, one rule for all |
| Compared days | Days where NWDP lists rain (> 0). NWDP lists rainy days only, so its zeros cannot be checked |
| **Bar, fixed now** | `MPS` counts as **rain in mm** at a station if, on its compared days, **≥ 80 %** agree within **1 mm or 10 %**, whichever is larger, and there are ≥ 50 compared days. It counts as rain for the platform if **≥ 6 of the 9** stations pass |
| Also reported | Per station: compared days, agreement share, Spearman, total ratio; share of days on which `MPS` has rain and NWDP lists nothing (NWDP gaps or `MPS` noise); the newest reading and its delay against the time of the run |
| If it fails | Not rain or not trusted: Part C stays NWDP-only (history and grading, no live input) and the reason is logged |

### 2026-10-20 · Part C0 results — `MPS` is rain, in mm, live the same day

`scripts/inspect/ffs_rain_check.py` → `reports/ffs_rain_check.{csv,json}`. Run exactly as
written in §5.

- **Alignment:** pooled agreement is **0.92 on the same day**, 0.12 and 0.13 a day either side.
  `MPS` and NWDP date the rain day the same way: the 24 h ending 08:30.
- **Per station** (agreement within max(1 mm, 10 %), on NWDP's rain days):

  | Station | Compared days | Agree | Spearman | Total MPS ÷ NWDP | Passes |
  |---|---|---|---|---|---|
  | Passighat | 6,571 | 0.962 | 0.969 | 1.03 | ✅ |
  | Miao | 5,638 | 0.948 | 0.950 | 1.04 | ✅ |
  | Namsai | 4,618 | 0.943 | 0.949 | 1.04 | ✅ |
  | Kibithu | 1,303 | 0.904 | 0.939 | 1.04 | ✅ |
  | Bhalukpong | 2,672 | 0.897 | 0.933 | 1.05 | ✅ |
  | Seppa | 3,161 | 0.888 | 0.913 | 1.11 | ✅ |
  | Tuting | 3,035 | 0.869 | 0.905 | 1.11 | ✅ |
  | Pangin | 473 | 0.715 | 0.723 | 1.29 | ❌ |
  | Daporizo | 217 | 0.364 | 0.382 | 1.70 | ❌ |
  | *Rho Basti (to 2023 only)* | 1,053 | 1.000 | 1.000 | 1.00 | ✅ history only |
  | *Yinkiang (to 2024 only)* | 212 | 0.533 | 0.583 | 1.38 | ❌ |

  Lemeking has no NWDP station within 5 km and was not checked.
- **Verdict, by the bar fixed beforehand:** 7 of the 9 live stations pass (bar: 6). **`MPS` is
  rain in mm.** It is used only at the 7 that passed. At Daporizo, `MPS` has rain on 20 % of
  days that NWDP leaves out, and Part A already flagged NWDP Daporizo as incomplete, so NWDP
  is the likelier fault there. Not tested, so Daporizo and Pangin stay out.
- **Delay:** the newest reading was 05:30 today, read at 12:31, so **about 7 hours**. Three-
  hourly slots are often missing (900–2,900 part-days per station since 2018). At the 08:30
  daily run, the rain day ending that morning has at best 7 of its 8 slots.
- **What this changes:** the platform now has a **live ground rain feed** at 7 Arunachal river
  stations, open, the same day, with 20–55 years of history checked against a second record.
  It goes in the gov data list's "found ourselves" column, beside the river levels.

## 6 · Part C — FloodSense: does a river station's own rain help its chance? Written before running

**Question:** for the river gauges that have their own live rain (the 7 passing stations in
Part C0), do the measured rain of the last day or three, added to the live gauge models, make
the chance of reaching the line better?

| Piece | Rule |
|---|---|
| Base | The live gauge chance models exactly as trained: `gauge_week.build_tables(gauge_week.station_days())`, inputs `train_flood_when_gauge.FEATS` (11), sigmoid calibration by river state, `oof(..., by="state")`, 5 year-grouped folds, leads 1–9, all 27 gauges |
| The station's rain, by day | `MPS` day total where the day is whole (Part C0's rule); else NWDP's listed value; else 0 in an NWDP counted month (April–October, ≥ 5 rain days); else missing. Only at the 7 stations; missing everywhere else (the trees handle missing) |
| New inputs | `gr1`, `gr3`: the station's 1-day and 3-day measured rain, each as its percentile among the station's own May–October days (share strictly below, as the rain inputs `r3`/`r7` are made). "More rain never lowers the chance" applies, as for the other rain inputs |
| Timing, two variants | The lead-L model is issued the morning after the gauge's complete day D−L. **A (generous):** the rain day ending 08:30 on the issue morning, which needs the 08:30 reading to be in (at best 7 of 8 slots at an 08:30 run). **B (safe):** the rain day before that, fully in. A is reported as the most rain could add; adoption is judged on **B** |
| **G1 no harm** | On all gauges, all days and onset days (river below its line at the last reading): AUC and Brier skill no more than 0.005 lower at leads 1–3 and 0.010 at 4–9, as in §14 of the pilot plan |
| **G2 a real gain** | On the 7 stations, onset days, leads 1–3: AUC **or** Brier skill up by **≥ 0.010** at 2 of the 3 leads, and neither down by more than the G1 tolerance at any of them |
| Also reported | The same on the 7 stations at every lead, and the number of onset flood days behind each figure |
| Caveat, fixed now | The models are trained with satellite rain for the target days as if it were known; live it is a forecast. The replay may therefore **understate** what measured rain adds live: a gain is real, a null is not fully final |
| If B passes G1 + G2 | A candidate for the live models **after** the cloud trial (about 2026-10-27), on the user's word, with `flood_gauge_live.py` reading `MPS` each morning, then a cloud redeploy. Not before |
| If it fails | Logged. The live rain still serves Part D (grading) and the gauge page could show it as context, as a separate decision |

## 7 · Part D — grading the forecasts' rain against the ground, written before running

**Question:** how close is the rain the forecasts run on (Open-Meteo, the next 7 days) to the
rain the ground then measured, by how many days ahead?

| Piece | Rule |
|---|---|
| Forecast rain | Every SlideSense issue kept whole: `records/landslide_forecast/issues/<day>.npz`, `rain_mm` (7 days ahead × 219 points) and `all_rain_mm` (10 past days + 8 ahead). FloodSense runs on the same Open-Meteo rain but does not keep it, so it is graded through these |
| Ground rain | `MPS` at the 7 stations that passed Part C0. Each has an Open-Meteo point within 0.15° (0.07–0.13°) |
| Same day on both sides | Open-Meteo days are UTC days: 05:30 IST to 05:30 IST. The `MPS` three-hourly slots ending 08:30, 11:30 … 02:30, 05:30 (next day) cover exactly that span. A gauge day counts only when **all 8 slots** are in |
| By lead | Lead 0 = the issue's own UTC day, up to lead 6. Also leads −1 … −10, Open-Meteo's own estimate of the days already past, which fill the trigger's 3- and 7-day windows |
| Reported per lead | Days graded; total forecast ÷ total gauge; mean absolute error (mm); of gauge days ≥ 10 mm, the share forecast ≥ 5 mm (caught); of forecast days ≥ 10 mm, the share where the gauge had < 2 mm (false alarms); 3-day totals: Spearman |
| Reading | **No bar: this is a log that grows.** October to April is the dry season, so the first fair reading is after the 2027 monsoon starts. It is read when each lead has ≥ 50 gauge days of ≥ 10 mm, and the readout goes here |
| Running it | `python scripts/fetch/fetch_48_ffs_rain.py` then `python scripts/inspect/grade_forecast_rain.py`, any day: it grades every issue kept so far, so it need not run daily. After the cloud trial the issues live in the Modal volume, so it runs on a copy of `records/` pulled down from there |

### 2026-10-20 · Part D, first run — the grading log is running

`scripts/inspect/grade_forecast_rain.py` → `reports/forecast_rain_grade.{csv,json}`. Run as
written in §7.

- 9 issues (2026-10-10 → 10-20), 7 stations, about 900 graded pairs. Post-monsoon, so few wet
  days: at most 12 gauge days of ≥ 10 mm at any lead, against the 50 needed. **Not read yet,
  as fixed.** For the record only: daily Spearman 0.45–0.63 on Open-Meteo's past-day estimates
  (leads −10 to −1), and 0.43–0.45 at leads 0 and 2.
- One thing learned: issues keep 11 past days, not 10. The issue date is the IST date and
  Open-Meteo days are UTC, so an issue made just after midnight IST counts one extra. Lead −11
  is left out, as the rule says −10 to 6.

### 2026-10-20 · Part C results — a station's own rain does not earn a place in the gauge models

`scripts/model/check_gauge_rain.py` → `reports/gauge_rain_check.json` (log
`reports/gauge_rain_check.log`). Run exactly as written in §6, about 2 minutes. Nothing live
was touched. Measured rain was known on 80 % of the 7 stations' rows; about 51,000 onset days
there per lead, with 206 (lead 1) to 470 flood days.

- **Rain stations, onset days** (river below its line at the last reading), base → A / B:

  | Lead | AUC | Brier skill |
  |---|---|---|
  | 1 | 0.961 → 0.960 / 0.958 | **0.130 → 0.166** / 0.138 |
  | 2 | 0.953 → 0.951 / 0.949 | 0.165 → 0.162 / 0.157 |
  | 3 | 0.953 → 0.952 / 0.953 | 0.151 → 0.150 / 0.149 |
  | 4–9 | flat to −0.003 | flat to −0.010 |

- **Gates:** G1 (no harm) passes for A and **fails for B** by a hair (lead 2 Brier skill
  −0.0065 against a tolerance of 0.005). G2 (gain) fails for both: A gains at 1 lead of the 3
  needed (lead 1, skill +0.035); B at none. **Not adoptable. The live models stay as they are.**
- **Reading:** the river level already carries what rain at the station says. Rain has to run
  off the hills before it shows in the river, and the models read both the river and the
  satellite rain for the target days. The one real signal is A at lead 1: the rain of the last
  night, not yet in the river, sharpens tomorrow's chance at these 7 stations. It is small and
  only on the generous timing. **Not adopted on this test:** it failed the bar, and it has
  now been seen. Logged as a candidate, below.
- **Candidate, needs a fresh test (not this data):** a lead-1-only use of the rain day ending
  the issue morning. That needs the run to start after the 08:30 reading lands (about
  10:30 IST), or to use 7 of 8 slots. It would be tested forward on the 2027 monsoon, written
  down before that season starts. Add it to the gauge model rows of `REMAINING_WORK.md`, not
  started.
- **Caveat that stays:** the replay gives the models satellite rain for the target days as if
  it were known. Live it is a forecast, so measured rain might add more live than here. This
  null is not fully final, and the forward test above would also settle it.
