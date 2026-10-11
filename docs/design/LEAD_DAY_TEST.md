# Grading the forecast by how far ahead it looks (days 1 to 7)

Item 18 of the 2026-10 list; Phase 2b of FLOOD_SCREEN_PLAN.md, which was
left open because nobody had checked whether old rain *forecasts* could be
had.

**The question.** Every test of the flood chance near a place so far fed
the model the rain that actually fell. The live screen feeds it *forecast*
rain, which gets worse the further ahead it looks. Days 4–7 are drawn
dashed and called "less sure" on that reasoning alone. How much worse are
they, measured?

Code: `scripts/fetch/fetch_41_openmeteo_previous_runs.py`,
`scripts/model/check_lead_days.py` → `reports/flood_lead_day_check.json`.
**Nothing live changes in this test.**

## 1. Method, written before the data was fetched (2026-10-11)

**The data.** Open-Meteo keeps, for each hour, what its forecast said one,
two … seven days earlier (its "previous runs" service, the same default
model mix the live forecast reads). Checked on 2026-10-11: forecasts made
one to six days ahead are held from **2024-01-25**. The flood record ends
2025-10-31. So the test window is **2024-01-25 to 2025-10-31**: two
monsoons. Fetched for the same 219 rain points the live run reads, summed to
days in UTC as the live run does.

**Replaying a forecast.** For a target day D seen from L days before
(L = 0 is "today" on the screen, L = 6 is the seventh day):
- rain on days before the day of issue (D − L) is the service's own record
  of what fell, as the live run reads its past days;
- rain on each day from the day of issue to D is what the forecast issued
  on D − L said for that day.

From those the day model's three rain inputs are built exactly as the live
run builds them (3- and 7-day totals at the place and upstream, yesterday's
score), scored against the same scales. Soil wetness is used as it was
known (it is 16 days old in the live run in any case).

**The model under test** is the test copy used by every earlier check
(`near_here.diagnose`, "production-like"): the day model taught on floods
to 2020 and tuned on 2021–22; the near-here curves for 2024 fitted on
2022–23 and for 2025 on 2023–24, on rain that fell. Nothing that makes a
number has seen the year it is graded on. The curves are **not** re-fitted
per lead: the point is to see what the live recipe does with forecast rain.

**Graded,** for each L from 0 to 6, on the day chance near each place
inside Arunachal, against verified floods within 10 km:
1. **Ranking:** how often a place-day with a flood is ranked above one
   without (AUC).
2. **Level:** floods forecast in total, against floods recorded.
3. The same two on the **rain that fell** (the existing test's rain), on
   the same days, as the yardstick.

**How it will be read — fixed now**

- *Days 4–7 are "measurably worse"* if their ranking (mean of L = 3..6) is
  more than **0.02** below days 1–3 (mean of L = 0..2). Otherwise the dashed
  days rank about as well as the near ones.
- *Days 4–7 "over-promise"* if their forecast-to-recorded ratio is more
  than **1.5 times** that of days 1–3; *"under-promise"* if less than
  **two-thirds** of it.
- Whatever comes out is written on the method page's facts and in the
  brief. **The screen changes only on the user's word**: per-lead curves
  (if they over- or under-promise) or dropping the dashes (if they do not
  differ) would each be a new change with its own check.
- **Too few floods to say** if the window holds fewer than 20 place-days
  with a flood inside Arunachal. Then the result is reported as
  inconclusive and nothing is claimed either way.

**Known limits, stated before the run**

- Two monsoons. The year-to-year drift that failed Gate A (the flood
  record itself changing) is in this test too; it affects every lead
  alike, so differences *between* leads are the safer reading.
- The service's "what fell" is its own short-range model, not a rain
  gauge. That is also what the live run reads for past days.
- The seventh-day forecast comes from a different weather model than days
  1–6 in this archive; the screen's seventh day is L = 6, which is inside
  the consistent part.
- Only the place chance is graded here. River-gauge chances are graded
  daily by lead already (the scorecard).

## 2. Result (2026-10-11)

646 days, 2024-01-25 to 2025-10-31; 751 places inside Arunachal; **117
place-days with a flood, on 33 days** (55 in 2024, 62 in 2025). Enough to
say (the rule needed 20).

The first run stopped itself: the replay did not reproduce the live code's
inputs. Cause: rain totals added in 32-bit landed 0.0001 mm off, the
1%-step lookup flipped on tied values, and the model's trees turned that
into differences of up to 0.18. Totals are now added as the live code adds
them; with no forecast in it the replay matches the live function exactly
(largest difference 0.0). No result had been produced before the fix.

| The screen's day | Ranking (times in 100) | Floods forecast | Recorded | Forecast ÷ recorded |
|---|---|---|---|---|
| rain that fell | 89.2 | 76.7 | 117 | 0.66 |
| day 1 (today) | 89.2 | 76.7 | 117 | 0.66 |
| day 2 | 88.8 | 79.1 | 117 | 0.68 |
| day 3 | 89.3 | 78.5 | 117 | 0.67 |
| day 4 | 88.6 | 76.6 | 117 | 0.65 |
| day 5 | 88.6 | 72.8 | 117 | 0.62 |
| day 6 | 84.9 | 69.2 | 117 | 0.59 |
| day 7 | 85.4 | 66.6 | 117 | 0.57 |

**Read by the rules of §1**

- **Days 4–7 are measurably worse at ranking — just.** Days 1–3 average
  89.1, days 4–7 86.9: 2.3 lower, against a line of 2.0. Drawing the days
  again 200 times, 9 in 10 fall between 0.2 and 5.0 lower.
- **They do not over-promise.** If anything they say a little less: the
  forecast-to-recorded ratio falls from 0.67 to 0.61 (0.91 of the near
  days'; the lines were 1.5 and two-thirds). Forecast rain further out is
  smoother, so it reaches the high scores less often.
- So the dashes and "less sure" on days 4–7 are **justified by
  measurement**, where before they rested on reasoning.

**What the table shows beyond the rule** (seen after the run, so an
observation, not a finding to act on by itself): the drop is not gradual.
Days 4 and 5 rank as well as days 1–3 (88.6); the fall is at **days 6 and
7** (about 85).

**Two things to know about the rows**

- "Rain that fell" and "day 1" are the same numbers because they are the
  same rain: the service's record for a past day *is* its archive (checked:
  identical at every point and day). So day 1 here is hindsight, and the
  first row that is a real forecast is day 2 (made one day before). The
  screen's "today" uses rain forecast this morning for the rest of the day,
  which sits between the two. Read the other way — every screen day one
  row later — the comparison is days 2–4 (88.9) against days 5–7 (86.3):
  2.6 lower. The conclusion does not depend on which way it is read.
- The level (0.66 forecast per flood recorded) is the known shortfall of
  the approximate number (the screen says "happened between 0.6× and 7×
  what it said"). It is the same at every lead, which is why differences
  between leads are the safe reading.

## 3. What follows

- **Nothing changes on screen from this test.** The current marking
  (days 4–7 dashed) agrees with the rule as written.
- **An option for the user, not taken:** dash only days 6 and 7, since days
  4 and 5 held up. That would be a post-hoc reading of one two-monsoon
  test; it wants a rule written first and next monsoon's data.
- **No per-lead curves.** The rule for fitting them (over- or
  under-promising beyond the lines) was not met.
- Re-run after the 2026 monsoon: the fetch is resumable and the test is
  one command.
