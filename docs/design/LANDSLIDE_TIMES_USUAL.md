# SlideSense: real numbers in place of "4 of 5" (2026-10-11)

> **Names, 2026-10-11:** the landslide module is **SlideSense**. Until that date it
> was called SlopeSense, which is now the name of the whole platform (SlopeSense,
> Hazard Intelligence Platform). Older notes here were updated to the new name;
> "the earlier SlopeSense" or "SlopeSense v1" still means the first, separate app.

**Why.** The place card's headline read "4 of 5". The user's reaction:
*"What kind of number is this? I want to show real numbers in a way people
easily understand, not something like this which is confusing."* He is
right: it is the level's position on a five-step scale, shown as if it were
a measurement. Levels are normal practice (avalanche bulletins, weather
warnings, GSI's own bulletins), but they are shown as a word and a colour,
not as a score.

**What is real and measured.** Two things, each "times the usual":

1. **This ground against average ground** — how many times the landslides
   of average ground have been mapped on slopes ranked like this one.
   Already measured on ground the model never saw (90,799 landslide cells,
   `metrics.json → success_rate`): Very Low 0.02×, Low 0.3×, Moderate 1.4×,
   High 4.4×, Very High 13.4×.
2. **Today against a usual day at this place** — how many times as common
   landslides have been on days when the rain was as unusual as this. The
   dated landslides are few (NASA's catalogue, about 84 in the state), so
   this one is measured here, with its uncertainty.

Under the model (weak ground × unusual rain) the second number is exactly
"today's risk at this place, against this place's ordinary day": the ground
does not change from day to day.

Code: `scripts/model/check_landslide_times_usual.py` →
`reports/landslide_times_usual.json`, shipped to the app as
`webapp/assets/landslide/times_usual.json`.

## 1. The measurement, fixed before it is run

- **Rain score:** the app's own (`core.rainfall.trigger_series`, the mean
  of the 3- and 7-day rain percentiles against that point's history), on
  the Open-Meteo archive at the live run's 219 points, 2010 on. That is the
  number the screen calls "rain vs normal".
- **Landslides:** every dated landslide in NASA's catalogue inside the
  state, matched to its nearest rain point and its day.
- **Bands of the rain score:** under 50, 50–75, 75–90, 90–95, 95 and up.
- **For each band:** its share of all point-days, its share of the dated
  landslides, and the ratio of the two = "times a usual day". A 90% range
  from drawing the landslides again with replacement (2,000 times).
- **The usual day** is every day of the year at that point, not only the
  monsoon. The monsoon-only figure is reported beside it.

**Rules for what may go on screen**

- **R1.** A band gets its own number only if it holds at least **8**
  landslides. A thinner band is joined to its neighbour (the top band
  downward, the others upward).
- **R2.** The numbers must rise from band to band. Two neighbours out of
  order are joined.
- **R3.** Each number is shown rounded (one figure: "about 3×", "about
  half"), with its 90% range behind the ⓘ. Nothing is shown to a precision
  the 84 landslides do not support.
- **R4, the combined number.** The same measurement by the five LEVELS
  (ground × rain, as the map colours them), with the landslide's ground
  read at its catalogue position. A level-by-level "times usual" is shown
  **only if** every level from Low up holds at least 8 landslides **and**
  the numbers rise with the level. Otherwise the two numbers above are
  shown side by side and never multiplied on screen. (The catalogue places
  a landslide to about a kilometre, which is coarse for a 100 m ground
  map, so this is expected to be the weak one.)

## 2. Result (2026-10-11) — every rule passed, R4 included

84 dated landslides, all with a rain score; Open-Meteo archive, 219 points,
2010-01-01 to 2026-09-21. Run twice, identical.

**By how unusual the rain was** (against a usual day at the same place):

| Rain score | Share of days | Landslides | Times a usual day | 90% range | Monsoon days only |
|---|---|---|---|---|---|
| under 50 | 68% | 13 | **0.2×** | 0.14–0.33 | 0.26 |
| 50–75 | 18% | 19 | **1.3×** | 0.9–1.7 | 0.83 |
| 75–90 | 9% | 20 | **2.7×** | 1.9–3.6 | 1.5 |
| 90–95 | 2.5% | 13 | **6×** | 3.8–8.5 | 3.9 |
| 95 and up | 2.5% | 19 | **9×** | 6.3–12 | 6.0 |

No band had to be joined (R1) and the numbers rise (R2).

**By level** (54 of the 84 fell on ground the model scores; against an
average scored place on an average day):

| Level | Share of place-days | Landslides | Times the usual | 90% range |
|---|---|---|---|---|
| Very Low | 59% | 7 | **0.2×** | 0.09–0.34 |
| Low | 20% | 12 | **1×** | 0.6–1.6 |
| Moderate | 13% | 13 | **2×** | 1.2–2.7 |
| High | 5% | 8 | **3×** | 1.4–4.4 |
| Very High | 2.5% | 14 | **10×** | 6.5–14 |

**R4 passed**: every level from Low up holds 8 or more, and the numbers
rise. High sits exactly on the limit of 8, so its "3×" is the roughest of
the five (it could be anywhere from about 1.4× to 4.4×).

**Ground** (already measured, `metrics.json`): Very Low 0.02×, Low 0.3×,
Moderate 1.4×, High 4.4×, Very High 13.4× the mapped landslides of average
ground.

## 3. What changed on screen

The place card (a town or a point) on SlideSense's Forecast page:

| Was | Is |
|---|---|
| Headline "4 of 5" | **"3× the usual"** — the level's measured figure; the level's word and colour stay |
| "Slope susceptibility 0.60" | **"This ground: 4×"** the landslides of average ground (the 0.60 is behind the ⓘ) |
| "Rain vs normal 27/100" | **"Rain today: 0.2×"** landslides against a usual day here (the 27 of 100 is behind the ⓘ) |
| Day buttons "V.Low / Mod / High" | the level's figure: 0.2× / 2× / 3× (colour and hint still give the level) |
| Colour key: the five names | each name with its figure |
| Key note "A level is a rank, not a chance" | "× = times the usual number of landslides · not a chance" |

- Each ⓘ gives the 90% range and says it rests on 84 dated landslides.
- The one-page report says the same: "3× the usual", ground and rain each
  as a multiple.
- The three numbers are **never multiplied on screen**. Each has its own
  "usual": the level against an average place and day; the ground against
  average ground; the rain against a usual day at that place.
- Whole-state and district views are unchanged: they already showed real
  numbers (shares of land, kilometres of road).
- If `times_usual.json` is missing from the bundle the card shows the
  level's word alone, never a made-up number.

Format (`view.times`): under 1, one decimal ("0.2×"); 1 and up, a whole
number ("3×", "10×"). Nothing finer than the data supports.

Checked: three places on screen (headline, tiles, buttons, key) against the
file; all 34 screen cases open; the three panels still end level at
1,920 px; nothing cut off.

## 4. Step 4 — "High" on a day of below-normal rain: looked at, left alone

The user's screenshot: ground 0.60, rain score 27 of 100, level **High**.
It looks wrong to say High when the rain is below normal. Measured:

- **It is common:** of all place-days the map colours High or Very High,
  22% have a rain score under 50.
- **But the landslides do not say it is wrong.** Of the 17 dated landslides
  that fell at High or Very High, 3 fell on a day with a rain score under
  50. Those place-days are about 1.7% of all place-days, so that is about
  **3 times the usual** — the same as High as a whole. Weak ground stays
  more dangerous on an ordinary day. (Three landslides is very few.)
- **No other way of setting the levels ranked the dated landslides better.**
  Times in 100 that a dated landslide is ranked above an ordinary place-day:
  today's level score 81; the two measured multiples multiplied 78 (and
  that one is flattered, its rain part being fitted on the same
  landslides); rain alone 82; ground alone 69. The catalogue places a
  landslide to about a kilometre, which blunts anything that leans on the
  100 m ground map — so this cannot separate the candidates.

**Decision: the levels are not changed.** There is no evidence that would
justify it, and the card now answers the question it raised: beside "High"
it reads *this ground 4×, rain today 0.2×*, so a reader sees at once that
the level comes from the ground, not from today's rain.

What would settle it: dated landslides located to the slope (road-block
logs with chainage, the Himalayan pooling of item 15).

## 5. What may be said

- "Places and days we mark High have had about 3 times the landslides of an
  average place and day; Very High, about 10 times."
- "With rain in the top 5% for a place, landslides have been about 9 times
  as common as on a usual day there."
- Always with: measured on 84 dated landslides, so these are rough.
- Not: a chance, a percentage, or "10 times more likely to have a landslide
  today" as a promise about one slope.
