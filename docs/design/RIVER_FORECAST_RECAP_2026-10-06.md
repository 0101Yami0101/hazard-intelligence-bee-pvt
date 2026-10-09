# River gauge forecast — recap and next steps

**As of 6 October 2026.** One place for everything worked through between
28 September and 6 October on the river-gauge side of FloodSense, so nothing
is lost before the next piece of work starts. Plain summary here; the full
numbers are in the sections linked at each step.

> **Update, later on 6 October — the first level-model test is in** (§13
> below; full numbers in FLOOD_WHEN_PILOT_PLAN.md §14).
>
> **Second update, 6 October — it is live** (§14 below). The new chance
> model and the level line went live on the user's go-ahead. §2 and §4
> describe the state *before* that.

---

## 1. In one minute

- **A wrong reading made the forecast say 52%.** On 28 September CWC's feed
  held one false level at Murga Bridge. We changed how readings are cleaned.
  **That fix is live.**
- **We then tried to retrain the river-gauge models on the cleaned history.**
  Three careful attempts. **None went live.**
- **Along the way we found an older fault in the live models:** a river that
  is already above its flood line can be shown about 0% for the days ahead.
- **A better set of models is built and waiting** in a side folder. It is
  more accurate than the live set everywhere and makes the fault rarer. It
  does not remove it.
- **We checked how Google Flood Hub does it.** For the first two days it
  reads a week of the river's own levels and the gauges upstream — exactly
  what our model is not fed.
- **Agreed next:** build our own river level forecast (the "level line").
  Then set up Google's open model beside it as a second opinion. Our own
  model makes the call.

---

## 2. What is live today

| Piece | State on 6 October |
|---|---|
| Cleaning of gauge readings (three passes) | **Live.** Used by the daily run, the training and the backtests |
| River-gauge models | **Unchanged — those of 22 September** |
| Day model, near-here chance, the three screens | Not touched by this work |
| Improved river-gauge models | Built, **not live**: `models/flood_when_gauge_next/` |

- After every step the live forecast was re-run on a recorded day and
  compared number by number: **0 changes** each time
  (`scripts/model/check_live_unchanged.py check`).
- The 6 October forecast ran at 09:21 on the live models.
- There is no forecast for 3 October (this PC was off).

---

## 3. What happened, in order

### 3.1 The wrong reading (28–29 September)
- CWC's feed held one reading of 2,231.30 m at Murga Bridge against a
  steady 2,134.30 m. It was probably Rho Basti's value under the wrong
  station. CWC corrected it within days.
- The river forecast read 52% from it. The track record briefly showed 7
  false crossings; they corrected themselves when the gauges were re-read.
  The 29 September issue stays logged as three false alarms.
- **Why it got through:** CWC levels are heights above sea level, not
  depths. The old test ("3 times its neighbours") means nothing on such
  numbers.

### 3.2 The cleaning, now in three passes
`scripts/model/backtest_flood_when.py`, `clean_readings`:
1. The old proportion test (zeros, slipped decimals).
2. **Impossible excursions:** a level that leaves a steady stretch and comes
   straight back. One reading more than 5 m away, or a flat run more than
   20 m away, back within 72 hours. Never a jump that has not come back, a
   gradual fall, or a shift that stays.
3. **Keying slips:** a slipped or swapped digit on a steady river
   (210.5 for 201.5), including where readings come only 3 a day.
- Both later passes trust a steady level only if it is an ordinary one for
  that gauge.
- **Tested:** 22 made-up series with a known answer, all pass. On the full
  history of 1,180,994 readings: 194 removed, **18 false high-water days**.
  The real landslide-dam surge at Tuting (October 2018) keeps all 144 of
  its readings. → FLOOD_WHEN_PILOT_PLAN.md §13f, §13g.
- **Re-run after any change to the cleaning:**
  `python scripts/model/check_gauge_cleaning.py`

### 3.3 Were the removed readings really false? Yes.
- Checked with four tests that do not use the filter's own rules (still
  neighbours, outside everything the gauge has recorded, explained by one
  slip, another gauge read that value that hour).
- **All 18 high-water days taken away are certain** (two or more tests).
  Doimukh 2, Jollang 6, Miao 1, Pagoda 4, Pangin 2, Tamen 2, Yinkiang 1.
- Pangin was confirmed against Pasighat, 50 km downstream on the same
  river. → §13g, `reports/gauge_excursions_check.json`.

### 3.4 What the false readings had already done
- **Doimukh and Tamen have never really reached their official danger
  level.** The only days on record at the line were false.
- **Four floods in our verified flood list rest on false readings:** Pangin
  2019-08-09, Jollang 2020-05-04 and 2022-09-05, Doimukh 2024-11-17.
  **Not fixed** — see §8.

### 3.5 The retrain, and three attempts to repair what it exposed

Each attempt had its pass/fail rules written down before it was run, and
was run once.

| | What was tried | Result | Why |
|---|---|---|---|
| Retrain | Same models, cleaned history | **Failed** 1 of 12 comparisons (2 days ahead, ranking 0.938 → 0.927) | 13 real flood days went to exactly 0%. The fault of §4, already in the live models |
| Fix 1, "floor" | A high river never gets less than a low river with the same score | **Failed** 1 day ahead (skill 0.406 → 0.344) | It borrowed a curve from where it had no days behind it, and pushed "68%" days to 100% |
| Fix 2, "S-curve" | A smooth curve for the small "river already high" groups | **Better, not cured.** Passed every accuracy check at all nine leads | Cut the wrongly-near-zero cases by 50–90% but did not remove them |
| Fix 3, "habit" | Tell the model how often each river stays high, from its other years | **Failed** every check somewhere | Staying high is not a steady habit of a river (below) |

→ FLOOD_WHEN_PILOT_PLAN.md §13h, §13i, §13j;
`reports/gauge_retrain_check*.json`, `reports/gauge_cure_check.json`.

**A correction that matters.** After Fix 2 the cause was described as "a
habit of each river" (Deomali stays high 7% of the time, Daporizo 82%).
Those figures were all years lumped together. Year against year they hold
only weakly:
- Daporizo's "82%" is a single spell in 2019.
- Rho Basti's "63%" is 2016 and 2017; in its six other years, 3 days of 20.
- A gauge's share in one year is only a little closer to its own other
  years (16 points off) than to the average of all gauges (19–21 points).

So staying high mostly belongs to a particular **long high-water spell**,
not to the river.

---

## 4. The open fault, stated exactly

- **What:** a river already above its flood line can be shown a chance near
  zero of still being above it in the days ahead, though many such days are.
- **Where it bites:** 1 to 4 days ahead. From 5 days on the forecast is
  roughly honest at the low end.
- **Why:** the model sees only the latest reading and one day's change. It
  cannot tell a long spell from a short spike. With no rain coming, it
  scores every high river low.
- **Not affected:** warnings for a river that has not yet risen.

Of the days a high river was given **under 5%**, how many flooded:

| Days ahead | Live models | Improved models (not live) |
|---|---|---|
| 2 | 61 days, 25 flooded (41%) | 41 days, 17 flooded (41%) |
| 3 | 118, 21 (18%) | 55, 9 (16%) |
| 4 | 193, 21 (11%) | 148, 23 (16%) |
| 5 | 205, 15 (7%) | 214, 16 (7%) |
| 6–9 | 6–8% | 4–10% |

The improved models make such days **rarer**, not **milder**.

---

## 5. How Google Flood Hub does it

Full write-up with sources: FLOOD_HUB_AND_MOCKUP_COMPARISON.md §3.

**Google runs two different models.**

| | Worldwide river model | Level model for gauged rivers in India |
|---|---|---|
| Forecasts | flow, as a daily line, 7 days | level in metres, **8–48 hours** |
| Reads | a year of past weather, 7 days of forecast weather, a description of the catchment | the past 7 days of the gauge's own level, 10 days of 2–5 upstream gauges, rain |
| Reads the river's real latest reading? | **No** (Google says so) | Yes |
| Learned from | about 16,000 gauges worldwide | CWC's hourly readings |
| Google's own limits | weaker where data is thin; shown as "lower-confidence" in Arunachal's hills | best on big slow rivers; not flash floods or small-to-medium rivers |

- **So Google answers "a high river — what next" for two days only,** from
  a week of the river's own levels. Beyond that it uses weather alone.
- Even Google shows Pasighat's readings with no forecast.
- **On 3 June 2026 Google open-sourced the worldwide model's framework**
  (`github.com/google-research/flood-forecasting`, free licence, with
  ready-trained models and tools to add your own rivers). It predicts flow,
  not level. **We have not downloaded or run it.**
- Google's forecast service (the API) is free but mainly for non-commercial
  use. It is not a feed for our product.

**What we take from it:** the missing ingredients are a week of hourly
levels and the gauges upstream. We already hold both. The one real gap is
the number of rivers to learn from (16,000 against our 32).

---

## 6. Decisions made

| When | Decision | Whose |
|---|---|---|
| 19 Aug | Build our own flood forecast on Arunachal's own rivers; do not pass through Google's or GloFAS's numbers | User |
| 5 Oct | The river level forecast line is **IMPORTANT**, the next big feature | User |
| 6 Oct | "Check they are actual false readings and retrain after that." | User |
| 6 Oct | "Solve it if it's wrong" — the high-river fault | User |
| 6 Oct | "Add the improvements but no need to push live for now. Just build the real cure." | User |
| 6 Oct | "Just need the tech to be our own and not somebody else's entirely." Google's open model may run **side by side** with ours if it helps | User |
| 6 Oct | **Go-ahead:** start our own level model; set up Google's model alongside as the second step | User |

---

## 7. The plan

### Step 1 — our own river level forecast (the level line)
- **What it is:** a forecast of where each gauged river's level will be over
  the coming days, drawn as a dotted line on the gauge graph. It sits
  beside the chance of crossing the line; it does not replace it.
- **Why now:** it is the user-marked next feature, and it is the proper
  cure for the fault of §4, because it reads how the river has been moving.
- **Starting points agreed:**
  - Feed it a week of the gauge's hourly levels, not one day's high.
  - Add the gauges upstream where a chain exists (for example Tuting →
    Yingkiong → Pangin → Pasighat on the Siang).
  - Rain as now.
  - Aim at 1–2 days ahead first, where Google's own level model stops.
    Further ahead only if the tests carry it.
- **Rules to write down before building:**
  - The rule already written: the line is shown only if, on years it never
    saw, the crossing chance its range implies agrees with the checked
    crossing chance. Two forecasts on one graph must never contradict.
  - The high-river test: of the days a high river is given under 5%, fewer
    than 1 in 10 may flood.
  - It must not be less accurate than the live models.
  - Any pattern used as an input must be shown to hold from one year to
    the next first.
- **Not decided yet:** how many days ahead to show; whether it is drawn as
  one line or a range; whether small flashy streams get a line at all (a
  hill stream rises and falls in hours — a limit of the river, not of
  effort).
- → FLOOD_SCREEN_PLAN.md Phase 10; FLOOD_MODULE.md, top callout.

### Step 2 — Google's open model beside ours
- **Its role:** a second opinion and a yardstick. Never the core, never a
  replacement, and credited honestly as built on Google's open model.
- **How it helps:**
  1. Proof for clients: ours against Google's, on Arunachal's own rivers.
  2. When the two disagree, that day is marked less certain.
  3. Later, an extra input to our model — only if a test shows it helps.
- **How it gets checked:** at the 14 small NWDP rivers by amount (we hold
  measured flow there); at the big CWC rivers by timing (does its flow rise
  and fall when the measured level does; do its rare highs line up).
- **Before relying on it:** read the exact terms on the trained model
  files; set up the daily weather feeds it needs.

---

## 8. Waiting for an answer

1. **The four false floods in the verified flood list** (§3.4). Removing
   them means retraining the main day model too. Asked three times, not yet
   answered.
2. **A display rule for a high river:** show "river is high now, next days
   uncertain" in place of a tiny percentage. A screen change, not a model
   fix. Offered, not yet answered.
3. **When to make the improved river-gauge models live.** Said on 6 Oct:
   not for now.

---

## 9. Loose ends

- The live river-gauge models still learned from a history holding the 18
  false high-water days.
- When the improved models go live, **Doimukh and Tamen move** from the
  official danger level to their own wettest 2% of days (123.50 → 120.45 m;
  283.00 → 277.29 m), by the existing rule that an official level counts
  only where the record reaches it.
- Two gauge-found floods were not at today's line even before the cleaning:
  Seppa 2026-07-15, Tamen 2022-07-07. Not looked into.
- At Tuting, Pangin and Pasighat two sources of readings disagree on some
  days. Which is right is not known.
- ~~Rho Basti sat at its line for a week in June 2016 with almost no rain.
  Snow-melt or a reading problem — not checked.~~ **Checked 6 Oct: a real
  river** (melt water, a smooth daily cycle). See §13.
- The retrain also moves chances on days when a river is *below* its line,
  by up to 28 points in extreme made-up cases. On the tests these days were
  as accurate or better at 8 of 9 leads, but it should be looked at on
  screen before going live.

---

## 10. Where everything is

| What | Where |
|---|---|
| Full record, with every number | `docs/design/FLOOD_WHEN_PILOT_PLAN.md` §13f–§13j |
| Google comparison, with sources | `docs/design/FLOOD_HUB_AND_MOCKUP_COMPARISON.md` §3 |
| Cleaning of readings | `scripts/model/backtest_flood_when.py` |
| Test of the cleaning | `scripts/model/check_gauge_cleaning.py` |
| Evidence the removed readings are false | `scripts/model/check_gauge_excursions.py` → `reports/gauge_excursions_check.json` |
| Training of the river-gauge models | `scripts/model/train_flood_when_gauge.py` |
| The retrain and fix tests | `scripts/model/check_gauge_retrain.py`, `scripts/model/check_gauge_cure.py` → `reports/gauge_retrain_check*.json`, `reports/gauge_cure_check.json` |
| Live river-gauge models | `models/flood_when_gauge/` |
| Improved models, not live | `models/flood_when_gauge_next/` |
| Backups from before this work | `models/flood_when_gauge_pre_cleaning/`, `reports/_pre_gauge_cleaning_backup/`, `data/interim/flood_forecast/golden_live_pre_gauge_retrain/` |
| "Did the live numbers change?" check | `scripts/model/check_live_unchanged.py check` |

**⚠️ Running `train_flood_when_gauge.py` with no `--out` replaces the live
models.** To build a set beside them:
`python scripts/model/train_flood_when_gauge.py --out models/flood_when_gauge_next`

**To make the improved models live, when asked:**
1. Put the contents of `models/flood_when_gauge_next/` in place of
   `models/flood_when_gauge/` (its report goes to
   `reports/flood_when_gauge.json`).
2. Rebuild `scripts/build/build_gauge_levels.py` and
   `scripts/build/build_gauge_reach.py`.
3. Run `check_live_unchanged.py check`: only river-gauge numbers may
   change.
4. Record the new baseline, run the screen checks
   (`scripts/run/check_app_screens.py`), refresh the web snapshot without
   writing to the track record.

---

## 11. How we worked — worth keeping

- **Rules before results.** Every test had its pass/fail rules written in
  the design doc before it was run, and was run once. When a rule failed,
  nothing shipped, even where the result was "better".
- **One fix per test.** No trying fix after fix on the same history until
  one passes.
- **Three things were stated wrongly in chat and corrected:**
  1. That the 29 September forecast had not run. It had. Check the day's
     log in `logs/flood_forecast_daily/` before saying so.
  2. That Murga Bridge's "7 missed crossings" were a model weakness. They
     were one bad reading counted 7 times. Look at the raw readings first.
  3. That staying high is a habit of each river. It did not hold year to
     year. Check a pattern across years before calling it a cause.

---

## 12. Other open items from the same days (not about river gauges)

- **Nothing is committed or pushed.** The public site still shows the old
  screens.
- The daily forecast runs on this PC; a day is lost when it is off
  (3 October). Moving it to a scheduler elsewhere was offered, not taken up.
- Offered earlier, not taken up: grading forecast days 4–7; news-feed
  intake; the Changlang_1 record-break check.
- The soil-erosion module application (NESFIC-D-07) is due **25 October
  2026** — EROSION_PLAN.md.
- Done in the same days and recorded elsewhere: the three FloodSense pages
  made over as dashboards (FLOOD_SCREEN_PLAN.md); floods back to 2003
  counted and learned from (OLDER_FLOODS_TEST.md).

---

## 13. Update, later on 6 October — the first level-model test

Built and tested the same day, rules written first, run once
(FLOOD_WHEN_PILOT_PLAN.md §14).

**What was built.** Six new inputs read from each gauge's last week — how
the level has moved over 3 and 7 days, how many of the last 7 days were
above the line, where the river ended the day, whether it rose or fell
through the day. They work from three readings a day as well as hourly
(half of CWC's days are three a day). Two models read them:
- **the level model** — a low / middle / high forecast of the river's level;
- **a new chance model ("W")** — today's chance of crossing the line, with
  the six inputs added.

**The level model passed every test, 1 and 2 days ahead.**
- Its middle line misses by 0.13 m one day ahead and 0.22 m two days ahead
  at CWC gauges — about a fifth better than "the river stays where it is".
  When the river is already high it is 35–42% better.
- Its low–high range holds 80% of what happened, as it should.
- Where its whole range sits above the line, 80–93% of those days cross.
- **It may be drawn to 2 days ahead.** Further out, the line and the chance
  disagree too often; that needs its own test.

**The new chance model is the most accurate yet, but failed one test of
four.**
- More accurate than the live models and the improved set at every lead.
  One day ahead its skill is 0.548 against 0.406 live.
- The fault (§4) is much smaller: flood days wrongly given under 5%, two
  days ahead, fell from 25 to 5.
- But the rule was "fewer than 1 in 10", and it is at 24%, 11% and 10.4%
  at 2, 3 and 4 days. **By the rule it is not adopted.**
- **Most of the days it still gets wrong are one fortnight at one gauge:**
  Rho Basti, June 2016, when a melt-fed river sat 0–21 cm above its line
  with almost no rain. Whether such a day counts as a flood hangs on
  centimetres. The level model showed those days honestly, as "just under
  the line, could touch it".

**One thing follows from this:** the level line cannot go on screen beside
the *live* chance model — they would contradict each other on some days.
It needs the new chance model beside it.

**Now built, not live, not on screen:** `models/flood_when_gauge_next/`
holds the level models (`level1.pkl`–`level7.pkl`) beside the improved
chance models. Code: `scripts/model/gauge_week.py`; test:
`scripts/model/check_gauge_week.py` → `reports/gauge_week_check.json`.

**Added to "Waiting for an answer" (§8):**

4. **Adopt the new chance model (W) although it failed the fault test
   narrowly?** The level line needs it beside it. Recommended: yes.
5. **Then put the level line on screen** (to 2 days ahead) together with
   it — which means making both live.

**Still to build after that:** reading each day's first and last reading in
the daily run; the dotted line on the gauge graph; upstream gauges (the
next test); the line beyond 2 days; Google's open model alongside (Step 2).

**New loose ends:** Rho Basti's levels have drifted lower since 2016–17, so
its "own wettest 2%" line may be out of date. For rivers that sit on their
line for weeks, the flood label itself is fragile.


---

## 14. Second update, 6 October — adopted and live

**The user's decision:** asked whether to adopt the new chance model
despite its narrow fail, and to put the level line on screen — *"Yes, do
next steps for the updates."*

**What is live now.**

| Piece | State |
|---|---|
| River-gauge chance models | **New.** They read the river's last week as well as its latest reading. Retrained on the cleaned history |
| The level line | **On the gauge graph**, dotted, with a shaded likely range, for 2 days after the last full day of readings. Plus an "Expected high" tile |
| Doimukh and Tamen | Now forecast against their own wettest 2% of days (120.45 m, 277.29 m) |
| Day model, near-here, the map | **Unchanged** — checked number by number |
| Track record | Today's logged forecast (09:21) is the old models'. **The new models' first logged forecast is 7 October, 08:30** |

**How it was checked.**
- The daily run computes the new inputs exactly as the models were trained
  on them (1,136 replayed forecasts, identical).
- After the switch, the only numbers that changed are the river rows and
  the method page's gauge figures.
- A new baseline of the live run was recorded and replays with 0 changes.
- All 21 screen checks pass; the graph was looked at.

**Honest limits of what is live.**
- The chance model was adopted **knowing it failed one test of four** (the
  high-river test, §13). The method page says where it is weakest: a river
  sitting right at its line.
- The level line is drawn **2 days only**.
- **The 14 NWDP gauges have no level line yet.** Their readings arrive 2–3
  days late, so today is already past the 2 days.
- The level forecasts are logged from 7 October, but **nothing grades them
  yet**.

**To go back:** FLOOD_WHEN_PILOT_PLAN.md §14e lists the three copies to
restore.

**Next, in order.**
1. Grade the level line every day against the gauge, like the chance.
2. A level line for the NWDP gauges.
3. Upstream gauges as inputs (its own test); the line beyond 2 days.
4. Google's open model alongside (§7, Step 2).

**Still waiting for an answer (§8):** the four false floods in the verified
flood list; the display note for a river that is high now.

**Nothing is committed or pushed.** The public site still shows the old
screens and the old forecast.
