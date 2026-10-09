# Floods before 2015: count them on screen, and test training on them

Written 2026-09-29, **before** either step was run. §1–§4 are fixed; results
go in §5 onward and may not change §1–§4.

## 0. Why

The screen says "N flood days on record within 10 km **since 2015**", and the
day model learns only from 2015 on. Both start in 2015 because the first flood
list the models were built on (news reports passed by a radar screen) started
on 2015-06-03: the radar satellite has regular images of the area only from
2015.

On 2026-09-28 the list was rebuilt as the **verified** record
(`build_verified_floods.py`, PARKED_HIMALAYAN_FLOOD_WHERE.md §0x). Google's
Global Flood Database (satellite flood maps, 2000–2018) confirmed 325 of the
751 news reports from before 2015 it could check. So the verified record now
holds **326 floods from 2003–2014** (39 inside Arunachal, all 2010–2014),
beside 1,859 from 2015 on. Neither the screen's count nor the model's training
was widened to use them.

| Verified floods | 2003–09 | 2010–14 | 2015–25 |
|---|---|---|---|
| Whole window (Arunachal + Assam plains) | 54 | 272 | 1,853 |
| Inside Arunachal | 0 | 39 | 275 |

The older years are thin, and unevenly so: 2013 has 1 in the whole window,
2014 has 140. Before 2015 only the Global Flood Database could confirm a
report, and its optical satellite cannot see through monsoon cloud. So most
older floods were **never confirmed** — not absent.

## 1. Fix 1 — count every verified flood on screen

**Change.** The "floods on record" count (`near_here.evidence`) counts from
the verified record's start (2003) instead of 2015-06-01, through the same end
(TRUTH_END). Nothing else in the forecast changes; `TRUTH_START`, which also
sets other test windows, is left alone.

**The check** (re-run with the new count, same code otherwise):
- `near_here.py confidence`: Gate C′ by level, and the production-like
  two-level split the screen's wording quotes (2023–25, evidence counted
  from records **before** each graded year, as before).
- Reported, not gated: how many Arunachal places move from "no floods on
  record" to "floods on record".

**Rules fixed now:**
- The screen's figures ("about ×A as many recorded as forecast where floods
  are on record; ×B where none are") are **replaced** by the re-measured
  ones. They are read from the report file, never typed.
- "Read the outlook as a floor" is shown only if the re-measured
  on-record ratio is ≥ 1.1. The note that places with none on record often
  go unreported is shown only if that ratio is ≥ 1.1 too.
- Gate C′'s own decision (High and Medium merged into one "floods on record"
  level) was made on the 2015 count. If the re-run would reverse it, the
  merge stays and the reversal is reported. Re-deciding a gate on a changed
  count is a new test, not this fix.
- Every forecast number must stay identical: the golden check
  (`check_live_unchanged.py`) may show changes only in `floods_on_record`,
  `level`, `evidence_period`, `measured_by_level` and the daily report's
  `places_highest_week[].floods_on_record`.

## 2. Test 2 — does training on the older years help?

**Question.** Does the day model forecast flood timing better if its tree
also learns from verified floods before 2015?

**Baseline** — the test copy every earlier test used, and what ships in
shape: `fit_day_model` (rain model everywhere, soil model on flat cells),
tree 2015–2020, calibration 2021–2022, test 2023-01-01 .. TRUTH_END
(2025-10-31), verified record, exposure `exposure_replay2022_clean.npy`
(WHERE retrained on floods to 2022).

**Candidates** — identical except the tree's years:
- **+2010–14**: tree 2010–2020.
- **+2003–14**: tree 2003–2020.

The calibration years (2021–22) and the test years (2023–25) are the same
for all three, so the gain can only come from what the tree learned. The rain
inputs for the added years are computed exactly as for 2015 on (same code,
same own-place monsoon percentiles over the full archive from 2000). The
script checks that its extended inputs equal the production inputs, value for
value, on every day from 2015.

**Metrics:**
- **Timing** — the soil test's metric (SOIL_WETNESS_TEST.md §3): each
  model's chance divided by that cell's own 2015–2022 average (so place is
  taken out), ranked across test cell-days; AUC = how often a flood cell-day
  ranks above a no-flood one. Gain = candidate − baseline, with a paired
  bootstrap resampling whole dates (2,000 draws, seed 0). **97.5%**
  intervals: 95% split over two candidates.
- **Near-here ranking** — the figure the screen quotes ("right about 89 in
  100"): each model fed the Open-Meteo archive, near-here curves re-fitted
  each year on the latest two complete years, weekly, inside Arunachal,
  2023–25 (`near_here.diagnose`'s production-like routine).

**Gates** — a candidate passes only if all four hold:
- **G1** Region timing gain ≥ +0.010.
- **G2** The 97.5% interval of that gain is above 0.
- **G3** Inside-Arunachal timing gain ≥ −0.005 (no real loss in the state).
- **G4** Near-here weekly ranking inside Arunachal ≥ baseline − 0.005.

If both pass, the one with the larger G1 gain ships. If the two gains are
within 0.002, the shorter span (+2010–14) ships, since it adds fewer doubtful
years. If neither passes, training stays at 2015 on. Fix 1 still stands: it
only counts records, it trains nothing.

**Diagnostics** (reported, never deciding): verified floods per year; per
year, the share of the wettest monsoon cell-days (top 1% local WHEN score)
with a verified flood — a measure of how complete each year's record is;
the per-candidate breakdown by terrain class.

**What passing would mean, and what it would not.** A pass means the older
years teach the tree something the test years confirm. It does not make the
pre-2015 record complete. Wiring a pass into production (rebuilding the rain
lattice from the chosen year, retraining, re-fitting the near-here curves,
the golden check) is a separate step, done only when asked.

## 3. Order

1. Fix 1: change the count, re-run `near_here.py confidence` and `fit`, run
   the golden check, update the screen text, refresh the snapshot.
2. Test 2: `python scripts/model/test_older_floods.py`, writes
   `reports/older_floods_test.json`; results in §5.

## 4. Files

- `scripts/model/near_here.py` — `EVIDENCE_START`, used by `evidence()`.
- `scripts/model/test_older_floods.py` — test 2.
- Backups before fix 1: `models/flood_forecast/near_here/_pre_older_floods/`,
  `reports/_pre_older_floods_backup/`.

## 5. Results

### 5a. Fix 1 — passed its check (2026-09-29)

The count now runs 2003-01-01 .. 2025-10-31 (`near_here.EVIDENCE_START`).

- **Places:** inside Arunachal, places with floods on record go from 180 to
  189 of 751. 9 places move from "none on record" to "on record", and 55
  gain older flood days.
- **Re-check** (`reports/flood_near_here_confidence.json`; the old copy is in
  `reports/_pre_older_floods_backup/`):

  | | Old count (from 2015) | New count (from 2003) |
  |---|---|---|
  | On record: happened / said | ×1.609 | ×1.602 |
  | None on record: happened / said | ×1.973 | ×1.997 |
  | Ranking, on record / none | 0.854 / 0.868 | 0.859 / 0.868 |
  | Gate C′: keep High and Medium separate | no | no (unchanged) |

  Both ratios stay ≥ 1.1, so the "floor" and "often unreported" readings
  stay. Ranking differs by 0.009 between the groups, so "about the same
  ranking everywhere" stays. The screen and the method page now choose
  each of these readings from the measured numbers instead of typing them,
  and take the start year from the snapshot.
- **Near-here curves** (`models/flood_forecast/near_here/curves.pkl`,
  re-fitted): every calibration curve and the neighbour table are identical.
  Only `evidence_days`, `level` and the label text changed.
- **Golden check:** 207 changes, every one in an allowed field (183
  snapshot `floods_on_record`, 10 `level`, 8 `measured_by_level`, 1
  `evidence_period`, 5 report `places_highest_week[].floods_on_record`).
  **No forecast number changed.** Baseline re-recorded afterwards; the old
  one is in `golden_live_pre_older_floods/`.

### 5b. Test 2 — +2003–14 passes, +2010–14 fails G4 (2026-09-29)

`reports/older_floods_test.json`, run by `scripts/model/test_older_floods.py`.

**Checks first.**
- The extended inputs equal production's on every day from 2015. WHEN score
  max difference 0 on 90 days; upstream r3 and r7 max difference 0 on all
  days; missing values identical.
- The baseline reproduces the screen's near-here figure exactly (0.893).

**Training data added.**

| Tree years | Cell-days | Flood cell-days | Floods per million cell-days |
|---|---|---|---|
| 2015–20 (baseline) | 4.02 M | 903 | 225 |
| 2010–20 | 7.36 M | 1,120 | 152 (2010–14 alone: 65) |
| 2003–20 | 12.05 M | 1,165 | 97 (2003–09 alone: 10) |

**Results** (test 2023-01-01 .. 2025-10-31, verified floods).

| | Baseline | +2010–14 | +2003–14 |
|---|---|---|---|
| Timing, region (332 floods, 126 days) | 0.889 | 0.909 | 0.909 |
| gain [97.5%] | | +0.020 [+0.012, +0.030] | +0.020 [+0.011, +0.029] |
| Timing, Arunachal (44 floods, 33 days) | 0.846 | 0.867 | 0.873 |
| gain [97.5%] | | +0.021 [−0.008, +0.057] | +0.028 [+0.008, +0.053] |
| Near-here weekly ranking, Arunachal | 0.893 | 0.862 | 0.890 |
| G1 / G2 / G3 / G4 | | ✓ ✓ ✓ **✗** | ✓ ✓ ✓ ✓ |

**Verdict, as pre-registered:** **+2003–14 passes; +2010–14 fails G4.**
Training on the verified floods from 2003 ships, **if wired in** (§2: a
separate step, done only when asked).

**Read with care** (post-hoc; explains, does not change the verdict):
- **The near-here figure is jumpy.** The two candidates time floods almost
  identically (region 0.909 each), yet their near-here ranking differs by
  0.028. That figure rests on 127 flood place-weeks. +2003–14 passed G4
  with 0.002 to spare; read that as "no clear loss", not "no change".
- **The timing gain holds across the whole area** and in Arunachal. By
  terrain it comes mostly from steep ground (+0.029 [+0.007, +0.048],
  29 floods), not flat ground (+0.005, interval crosses 0).
- **The old record is very incomplete, and still helped.** On the wettest
  1% of monsoon cell-days, the share with a verified flood was 0% every
  year 2003–08, 0–0.12% in 2009–14, and 0.06–0.56% from 2015. The added
  years show the tree many heavy-rain days with no recorded flood. The
  calibration (2021–22) resets the level, so what the tree gains is
  ranking. Why it ranks better is not shown by this test.
- Before shipping: re-measure the figures the screen quotes (Arunachal
  timing, the near-here error and ranking), and watch the near-here grading
  as new flood records arrive.

### 5c. Wired in (2026-09-29, the user's go-ahead)

**What changed.**
- One constant, `flood_forecast.TREE_FROM = 2003`, used by:
  - the production fit (tree 2003–2023, calibration unchanged 2024-01-01 ..
    2025-10-31);
  - the source check in `flood_forecast_live.build` (tree 2003–20);
  - the near-here test copies whose figures the screen quotes
    (`near_here.confidence`, `near_here.diagnose`: tree 2003–20).
- Older tests keep the years they ran with (`near_here.check` — Gate A —
  `compare`, `confirmed`, the replay, the soil test).
- `NORMAL_FROM = 2015-01-01`: each cell's "ordinary day" level
  (`normal_daily_prob.npy`) stays the mean over the days it always covered,
  so the switch changes the model, not the yardstick.
- `when_grid.START = 2003-01-01`. The lattice and every file aligned to it
  (`upstream_rain_pct.npz`, `gauge_frac.npz`) were rebuilt.

**Checked identical** (bit for bit):
- every lattice row from 2015 on (`when_raw`, `upstream_rain_pct`,
  `gauge_frac`);
- `gauge_reach`, `when_cells.json`, `exposure_km2`, `terrain_class`,
  `soil_breaks`;
- the live rain scales (`live/scales.npz`, same MD5);
- the calibration rows (1,227,440 cell-days, 207 floods).

**Tree:** 14,051,440 cell-days with 1,449 flood cell-days (was 6,021,784
and 1,187). Valley factors moved: flat 0.997 → 1.048, hilly 0.167 → 0.160,
steep 0.025 → 0.020.

**Re-measured figures** (the screen reads each from a file):

| Figure | Before | After |
|---|---|---|
| Live timing inside Arunachal (satellite-fitted, live rain; 44 floods, 2023–25) | 0.851 | **0.879** |
| … on satellite rain | 0.840 | 0.874 |
| … floods caught at 10× normal / time under warning | 0% / 0.1% | 16% / 1.8% |
| Near-here weekly ranking, Arunachal | 0.893 | 0.890 |
| Recorded ÷ forecast, ranges with ≥ 10 floods | 0.81–6.15× (5 ranges) | 1.26–6.3× (2 ranges) |
| Overall forecast ÷ recorded | 0.585 | 0.609 |
| Floods on record: recorded ÷ forecast | ×1.60 | ×1.51 |
| None on record: recorded ÷ forecast | ×2.00 | ×2.04 |
| Ranking, on record / none | 0.859 / 0.868 | 0.853 / 0.866 |
| Gate C′ decision (levels merged) | merged | merged (unchanged) |

**A wording fix this forced.** The error range above uses only ranges with
≥ 10 floods (the rule as set). With the new model, the three top ranges
(5% and up) hold 19 floods between them — each under 10 — and said MORE than
happened (10.5% said, 6.1% happened). So "between 1.3× and 6×" alone would
read as "it always says too little". The rule was not changed. Instead
`near_here.fit` records `high_ranges_said_more` when this holds, and the
three places that state the error (the badge tooltip, "How to read these
numbers", the method page) add one measured sentence: "At its highest
numbers (5% and up), where few floods fell, it said more than happened —
about 11% said, 6% happened." The method page also now says what the model
learns from ("every verified flood of 2003–2023"), read from
`models/flood_forecast/_meta.json` via the snapshot's `method.day_model`.

**Golden check** on the recorded inputs:
- Every difference is a day-model field: chances, the area outlook, near-here,
  times-normal, the raster, and the re-measured figures.
- **Zero** differences in river forecasts, flood-on-record counts, soil, the
  track record or gauge history.
- Added fields: `method.day_model`, `measured_error.high_ranges_said_more`.
- On those inputs, Arunachal 7-day: 6.27% → 5.00%. Places: median ×0.95
  (middle 90% ×0.45–×3.1), rank correlation old vs new 0.90.
- Baseline re-recorded and self-checked (PASS, 0 differences). The previous
  one is in `golden_live_pre_tree2003/`.

**Screens:** 21/21. The method page shows all four new or changed sentences.

**Today's issue.** The scheduled task had already run today's issue at 09:11
(old model, found after the fact — the task starts a missed run when the
machine is available). The run started at 10:52 to issue on the new model
therefore **replaced** today's entries in the log, by the log's same-day
rule (keep the last row per issue, target day and gauge). Both were issued
on 2026-09-29. From 2026-09-30 every issue is the new model's.

**Rollback** (all copies kept):
- `models/flood_forecast_pre_older_floods/` → `models/flood_forecast/`
- `data/interim/flood_forecast/_pre_older_floods/*` → `data/interim/flood_forecast/`
- `reports/_pre_older_floods_backup/wiring/*` → `reports/`
- `when_grid.START`, `TREE_FROM` back to 2015; re-run
  `near_here.py confidence`, `diagnose`, `fit`, and the golden record.
