# FloodSense vs Google Flood Hub, and vs the dashboard mock-up

Two comparisons worked through in chat (2026-09-26 → 09-28), written down so
nobody has to re-derive them. Figures updated to the system as of 2026-09-28.

---

## 1. Google Flood Hub — why it shows only some points, and how we differ

### What Flood Hub does

- **It forecasts at points on rivers, never at a spot of land.**
  - In the **default view** only higher-confidence points are shown. Almost
    all are real CWC gauges on the Assam plains and big rivers; Arunachal has
    a handful (Pasighat, a greyed Yingkiong).
  - Turning on **"Extended coverage: lower-confidence gauges"** adds
    hundreds of model-only points along nearly every river in Arunachal's
    hills. Google gates them behind a warning: "intended for expert and
    research use only … use these forecasts with caution".
- **It shows by default only what it could check.** Google's own definition
  of higher-confidence: "Predictions that meet Google's high standards for
  accuracy, using reliable data and validated models". Lower-confidence:
  "Same hydrologic model … but potentially less data or lower accuracy".
- **Its flooded-area maps appear only around alerting gauges, and only on
  flat plains** ("Inundation map: available when alerting"). Turning "the
  river is 1 m higher" into "these fields go under" needs detailed ground
  height, which Google has only there.

### The three kinds of gauge panel (checked on the live site, 2026-09-28)

| Panel title | Where (examples) | What the chart shows |
|---|---|---|
| **"[River] forecast"**, Higher-confidence, source CWC | Neamatighat (Brahmaputra), Chouldhowaghat and Badatighat (Subansiri), Sivasagar (Dikhow) | measured river **level in metres** up to "Now", then a dotted **predicted level** (to 30 Sep at Neamatighat, about 2 days; ~16 h at Badatighat) against the official CWC warning / danger / extreme lines. "Google alert" button; inundation map "available when alerting" or "sometimes" |
| **"[River] trend"**, Higher-confidence, source CWC | **Pasighat** (Siang; basin 255,911 km²), Ranganadi NT-Road Crossing | **only the measured past week**, against the official lines. Nothing after today — **no prediction is issued** for this gauge at present. Google does not say why |
| **"River forecast"**, **Lower-confidence**, source HYBAS, no station name | hundreds of points across Arunachal (e.g. near Aalo, basin 240 km²; near Liromoba, 135 km²) | river **flow in m³/s** — both the past line and the dotted future (5–7 days) are the model's own estimates, since nobody measures these rivers. Lines are Google's own "how rare" levels (outside official gauges: warning ≈ once in 2 years, danger ≈ 5, extreme ≈ 20). Inundation map "not supported" |

So on Flood Hub, **"trend" is not a model-only point**: it is a real gauge
showing its readings with no forecast. And a model-only point **does** say
"forecast", only marked lower-confidence and hidden by default.

The ⓘ beside a chart title reads: "The historical and forecasted river levels
for the selected gauge. The risk level is determined by comparing the forecast
with the predefined thresholds (based on past flood events)."

Pasighat's official lines on Flood Hub (warning 153, danger 154, extreme 158 m)
match the CWC danger level our gauge model uses (153.96 m).

**Worked example — Subansiri at Badatighat** (a CWC gauge in Assam, just
below where the river leaves Arunachal; basin ≈ 34,000 km²):
- The solid line is the measured level, ~80.5 m and falling.
- The dotted forecast runs only ~16 hours ahead.
- Warning is 82 m, Danger 83 m, Extreme 86 m (official CWC levels).
- "Higher-confidence gauge" means a real, measuring gauge.

### Can a model learn from gauges and forecast a whole river?

Partly. Flow is continuous along a big river, so the flow between gauges can
be estimated (Google's virtual gauges). **The catch:**
1. River height does not say which fields flood without detailed terrain.
2. Small hill streams and local downpours never reach a big-river gauge.
3. Nobody measures those spots, so a forecast there cannot be proven.

### How FloodSense covers every spot

We do not forecast the water level at each spot. Every place gets:
- **Flood chance near here:** the chance of a recorded flood within ~10 km,
  each day and over 7 days. It is the same kind of number everywhere, and
  labelled **approximate** with its measured error. It failed its
  pre-registered calibration test; ranking is right ~89 times in 100
  ([FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md)). It replaced "× usual" on
  2026-09-27, which read like the rain handed back.
- **If a flood comes, chance this spot goes under:** from the shape of the
  land, learned from satellite-mapped floods, capped at "20%+".
- **The river gauge on this place's own river,** when there is one: a real,
  checked forecast.

Inputs are live rain (at the spot and upstream), the land's shape, and — on
flat ground since 2026-09-28 — soil wetness ([SOIL_WETNESS_TEST.md](SOIL_WETNESS_TEST.md)).
The model learns from **verified** floods — confirmed by radar, the Global
Flood Database or a gauge (PARKED_HIMALAYAN_FLOOD_WHERE.md §0x) — from 2003
on since 2026-09-29 ([OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md)). Live
timing inside Arunachal on floods it never saw: 0.879 (0.851 before the
older floods were added).

### Side by side

| | Google Flood Hub | FloodSense |
|---|---|---|
| At a gauge, what is forecast | the river's level or flow (dotted line) | the chance the river crosses its danger / warning line |
| How far ahead | ~16 h at Badatighat; days at some gauges | 1–9 days |
| Danger lines | official CWC levels | the same where they exist; else the river's own wettest 2% of days |
| Graph | measured level + forecast level | measured daily highs (30 days) + CWC lines + our daily chance bars; **no level line** (Phase 10, not built) |
| Away from real gauges | default view: blank. Extended view: model-only flow forecasts at hundreds of river points, "use with caution" | every spot: near-here chance (approximate) + chance the spot goes under |
| Arunachal's small rivers | only as lower-confidence model points (e.g. near Aalo: a modelled flow forecast) | 14 NWDP small-river gauges read the real river (e.g. Aalo), plus 18 CWC; forecasts checked daily |
| Checked against reality | yes, at gauges | yes: gauge forecasts graded daily; near-here graded for ranking as new flood records come in |
| Trained on | thousands of gauges worldwide | Arunachal's own gauges, rain and verified floods |

**In short:** at a real gauge, Google gives a more exact answer (a level) for
a shorter time — or, at some gauges such as Pasighat, only the readings. We
give a chance, further ahead. Away from real gauges, Google's hill coverage is
model-only and hidden by default. Ours is shown to everyone as an outlook,
labelled approximate. At Arunachal's small rivers, our NWDP gauges read the
river itself, where Google has only its model.

---

## 2. The FloodSense dashboard mock-up (Jang Township)

The mock-up was an image of a "BEE Intelligence FloodSense" dashboard for Jang Township, shared 2026-09-28: map, 7-day
outlook, river levels, upstream rain, catchments table, alert card, "what
changed", recommended attention, soil wetness, report export. Question: how
far are we from a real system like it?

**Answer:** about two-thirds exists in some form. Most of the rest is
presentation. A few parts need data we do not have. Much of the mock-up is
dressing; our numbers are real, tested and smaller.

**Update, 2026-09-28 (later the same day):** the forecast screen was made
over as a dashboard in the mock-up's shape (FLOOD_SCREEN_PLAN.md, "the
forecast screen made over"). It covers the whole state and any searched place
rather than a fixed "Jang and nearby villages" area.

| Mock-up panel | Status (2026-09-28, after the makeover) |
|---|---|
| Map with risk colours and village markers | ✅ low ground coloured by the outlook; named neighbouring places with their %; rivers by size, each gauge's stretch glowing in its chance colour; the area draining to the place as an outline |
| 7-day outlook, % per day | ✅ tiles for the week and each day (approximate, badge says so); they also pick the map's period |
| River levels | ✅ Rivers tab (30-day sparkline against the line + chance) and the full Flood-Hub-style graph; board of every gauge × every day |
| Upstream rainfall chart, past vs forecast | ✅ Rain tab: rain over everything draining to the place, 10 days past + forecast |
| "Catchments to watch" table | ✅ as "rivers to watch" (Rivers tab) and the highest-outlook areas; a per-catchment table is left for the Catchments page |
| "Elevated flood risk" alert card | ✅ the headline card: level word, %, 7 day bars — per day and week, not "next 18–24 h" |
| "What changed since yesterday" | ✅ from the previous issue (statewide, the place, areas changing level, rivers rising/easing, above the line, gauges offline) |
| Recommended attention | ✅ "Needs attention", from our numbers only; bridges and evacuation advice still need district data and procedures |
| Soil wetness | ✅ Soil tab: percentile for the time of year, and whether it is used here (flat ground only) |
| "Updated 5 min ago" | ❌ once a day (08:30); hourly is possible later |
| Generate report, watchlist, officer login | ❌ not built; login needs proper hosting |
| 3D terrain | 🟡 SlideSense has 3D; FloodSense does not |

**What we have that the mock-up does not show:**
- Every figure tested on past years, with its accuracy stated.
- Gauge forecasts graded daily against the real river.
- An evidence line: how many floods are on record near each place.
- A track record: each forecast written down before the day and graded after.
- Flood reporting: a report form, plus automatic records from gauge crossings.
- The landslide forecast in the same app.

**Jang specifically — do not copy the mock-up's confidence.** The mock-up
shows "16% High" for Jang villages. Our honest numbers there are much
smaller, often under 0.1% a day. Jang is also where our evidence is weakest:
- no gauge on its river;
- very few floods on record nearby;
- high ground, where the location model is least tested.

A Jang dashboard must say "low confidence" until local gauges and field
checks exist.

**Build order** (1–3 and the first half of 4 done 2026-09-28):
1. ✅ Village markers with their own %, and river lines coloured by chance.
2. ✅ The alert card and "what changed since yesterday".
3. ✅ Upstream-rain chart; 🟡 a per-catchment table (for the Catchments page).
4. ✅ Needs attention from our own data; ❌ report export.
5. Later: hourly updates, and login once hosting allows.

The makeover shows Jang's area as it is. Checked for Tawang, 2026-09-28: "Very
low" (under 0.1% for the week), no gauge on its river, 2 flood days on record
nearby. The badge and the ⓘ carry the "approximate" warning.

---

## 3. How Flood Hub makes its forecasts — and what of it we can do (checked 2026-10-06)

Asked after our own "river already above its line" fault stayed open
(FLOOD_WHEN_PILOT_PLAN.md §13h–§13j): how does Google handle a high river,
and why can't we? Read from Google's own papers, help pages and code.

### Google runs two different models

**A. The global river model** — most points on Flood Hub, including the
hundreds of lower-confidence points in Arunachal's hills.
- It forecasts the river's **flow, day by day, as a line** with a range —
  not a yes/no chance.
- It reads **one year of past weather** over the area draining to the point
  (rain, temperature, snowfall, radiation, pressure), **7 days of forecast
  weather** (ECMWF, GraphCast; rain also from IMERG and NOAA CPC), and a
  **description of the catchment** (climate, soils, terrain, land cover,
  from HydroATLAS).
- It learned from about **16,000 river gauges worldwide, 1980–2023**
  (version 2, preprint 29 April 2026: 15,923 basins; version 1 had 5,680).
- **It does not read the river's own latest reading.** Google's help page:
  "we are currently unable to assimilate near-real time streamflow data";
  the models page: "the models do not use real-time data provided by
  governmental entities" unless stated.
- A river staying high comes out of the year of weather: the model carries
  how wet the catchment is and how much snow is waiting.
- Reviewers' notes on version 2: judged on everyday flow, not on flood
  peaks or line crossings; peaks under-stated at longer leads.

**B. The level model for gauged rivers in India and Bangladesh** — the
published design behind a dotted level line in metres at a CWC gauge
(Nevo et al., 2022; operational since 2018 with CWC's hourly readings).
*Not confirmed:* whether today's CWC panels on Flood Hub still run exactly
this, or show CWC's own forecast.
- It reads the **past 168 hours of the gauge's own level**, **240 hours of
  2–5 upstream gauges**, and satellite rain.
- It forecasts the **level 8–48 hours ahead**, no further. The limit is
  each gauge's "maximal lead time".
- Typical error: 0.1 m at 24 h, 0.2 m at 48 h. In 2021: 376 target gauges,
  the level model on 167 of them, trained on 2014–2020.
- Google's own limits: "work best in slow-responding, large rivers";
  "flash floods and small-to-medium-sized basins" are not handled.

### So how does Google answer "a high river — what next"?

- **For the first two days:** from a week of the river's own hourly levels
  and the gauges upstream of it (model B).
- **Beyond two days:** only from weather (model A), which never sees the
  river's real level.
- In Arunachal it does not claim much: Pasighat shows readings with no
  forecast, and the hill points are hidden as lower-confidence (§1).

### Ingredient by ingredient — do we have it?

| What Google uses | Us today | What it would take |
|---|---|---|
| A week of the gauge's own hourly levels | We hold them (CWC hourly, 1.18 M readings). The model is fed only yesterday's high and one day's change | Build: this is the level line (FLOOD_SCREEN_PLAN Phase 10) |
| Upstream gauges | Some chains exist (Siang: Tuting → Yingkiong → Pangin → Pasighat); most small rivers have one gauge | Build where a chain exists |
| A year of past weather; snow and temperature | Rain history held; snow and temperature not fed | Build |
| A description of each catchment | Catchments drawn (webapp); not fed to the gauge model | Build |
| ~16,000 rivers to learn from | 32 gauges. **This is the real gap** | Start from Google's own trained model (below), or pool Himalayan gauges |
| Measured flow (m³/s) to learn from | Only at the 14 NWDP small rivers; CWC publishes level only | Work in levels at CWC gauges; a flow ask to CWC would lift it |

Limits that are physics, not effort: a small hill stream rises and falls in
hours, so no gauge-based forecast reaches days ahead there — Google says the
same of its own.

### Google open-sourced the global model's framework (3 June 2026)

- `github.com/google-research/flood-forecasting` ("OpenHydroNet"),
  Apache 2.0. Training, evaluation and inference code for the current
  production architecture, a `pretrained-models/` folder
  (`google-floodhub-settings-110-epochs`), a tutorial on fine-tuning for
  specific basins, and tools to outline a catchment and build its
  description for a gauge of your own.
- It is built on the open Caravan river dataset and an open weather archive
  (`gs://caravan-multimet`).
- Caveats: "not an officially supported Google product"; it predicts **flow
  only**, not level; the README is about training and evaluation, not daily
  running; a live run needs the daily weather feeds. **We have not
  downloaded or run it.**
- The Flood Forecasting API is separate: free, by waitlist, "primarily
  limited to non-commercial use". Not a feed for a product — in line with
  the standing decision to build our own.

### What this means for the level line

- Feed it what Google's level model reads: a week of hourly levels at the
  gauge, the gauges upstream, and rain. Aim it at 1–2 days first, where
  Google's own stops.
- Its pass/fail tests should include our open fault: of river-above days
  given under 5%, fewer than 1 in 10 flood (§13j, K3).
- Separately, the open pre-trained model can be tried at the 14 NWDP
  rivers, where we hold measured flow to check it against — as it comes,
  and after tuning on our rivers.

Sources: Google Research, "Our models" (sites.research.google/gr/floodforecasting/our-models);
Flood Hub Help, "How does the Hydrology Model Work?"
(support.google.com/flood-hub/answer/15637389); Nearing et al., Nature 627
(2024); "Extending Medium-Range Global Flood Forecasts: The Google Global
Flood Forecasting Model Version 2", EGUsphere preprint 2026-2283; Nevo et
al., HESS 26, 4013 (2022); Google Research blog, "The next chapter in flood
resilience: Open sourcing Google's hydrology framework" (3 June 2026);
developers.google.com/flood-forecasting.
