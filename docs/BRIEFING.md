# Briefing — the Data Backbone: the idea, the logic, and what stands on it

**As of 10 October 2026 · the idea in about 7 minutes, all of it in about 14
· plain words.**

**Visual version:** [BRIEFING.html](BRIEFING.html) — the same brief with
diagrams and numbered screenshots of the app. Open it in a browser. This
file is the plain-text twin.

Sections 1–8 are the idea and its logic. 9–12 are where it stands, in
short. 13 is the demo. 14–16 are for the last minute.

---

## 1. The idea in 30 seconds

> We are building the data backbone for mountain-hazard intelligence. The
> facts needed to see a landslide or a flood coming already exist, but they
> are scattered across satellites, government portals, river gauges and
> survey maps, in shapes that do not fit together. Every team that wants to
> use them spends months lining them up, and then that work is thrown away.
> We do it once. Every source is collected, checked, laid on one shared map
> of the state and kept current, with a record of where it came from.
> Anything can then be built on top. Our landslide forecast and our flood
> forecast are the first two products, and the second cost a fraction of
> the first. And because every forecast is written down and checked against
> what really happened, the backbone gets richer every season.

**In one line:** from fragmented mountain data to actionable intelligence.
(The pitch deck's own closing line.)

**The picture to hold:** an app is a vehicle; the backbone is the road. We
are building the road, and running the first two vehicles on it to prove it
carries weight.

## 2. Why a backbone — the problem it solves

Why not just build a landslide app? Because the app is the easy part. Four
things are broken underneath it, and they are the same four for every
hazard.

1. **The data exists, but in pieces.** It sits with NASA and the European
   satellites, GSI, ISRO, the state space centre, the water commission and
   others. Each has its own format and scale: ground height every 30 m,
   soil every 250 m, rain every 11 km, rock types as outlines, rivers as
   lines. Some sit behind portals that look closed and are not.
2. **Every project starts from zero.** A landslide study spends months
   lining this up, publishes one map, and stops. The flood study next door
   does the same work again. Nothing is reused.
3. **A map made once goes stale.** The ground barely changes, but rain and
   rivers change every day. A one-off map looks the same in January and in
   August.
4. **Nobody keeps score.** Forecasts are not written down and checked
   against what happened. So nothing learns, and nobody can prove a
   forecast was any good.

The result is what you see everywhere: static maps, one-off studies, pilots
that never scale.

Our own first forecast taught us this. The model was the small part.
Finding, checking and lining up the data was most of the work — and all of
it was reusable.

## 3. The idea — do the hard part once, and let everything stand on it

```
 SOURCES         RAW STORE        LINE UP          TWO SHELVES            WHO USES IT
 satellites      originals,       one shared map   1 ready-to-use data    SlopeSense
 government   →  never edited, →  of the state, →  2 answers:          →  FloodSense
 river gauges    each with its    every source       the forecasts        next products
 live weather    record           as a column                             open feed, other apps
 (own sensors)
      ▲                                                                        │
      └──────── what was forecast, and what really happened, comes back ◄──────┘
```

It is a standing system, not a one-off study. Six rules make it work:

| Rule | What it means | Why |
|---|---|---|
| **1. One map for everything** | The state is cut into 8.2 million squares, each the size of a football field. Every source, whatever its shape, becomes one more column of facts about those squares | A model needs a table. And two products can never disagree about where a place is |
| **2. Keep the original, and write down where it came from** | Raw files are never edited. Each carries its source, its terms of use, its link, the date it was fetched and a fingerprint | Anyone can audit a number. If a source goes offline we lose freshness, not the system |
| **3. Check a source before trusting it** | Every new source is tested against something independent | Official data can be wrong. The only official flood map of the state put most of its "flooded" ground on steep slopes. One wrong river reading once looked like a 52% flood |
| **4. The backbone does not know which hazard it serves** | Nothing in it says "landslide" or "flood". A product brings its own question | This is what makes the second product cheap, and the third cheaper |
| **5. Two shelves** | One holds ready-to-use data: the map, the facts, the rain history. The other holds answers: forecasts and risk layers | Different people need different shelves. A road planner may want the base layers; an officer wants the forecast |
| **6. Close the loop** | Every forecast is written down before the day and graded after it. What really happened comes back in as new data | More data makes a forecast fresher. Only knowing what happened makes it better |

## 4. How it works — follow one file through

1. **Collect.** A script fetches each source: satellite archives,
   government map servers, river gauges, and a live weather feed every day.
2. **Keep.** The file is stored untouched, with its record.
3. **Line up.** It is fitted to the shared map. A coarse layer is spread
   over the squares it covers. An outline becomes "which rock am I on". A
   line becomes "how far to the nearest river, road or fault".
4. **Describe.** Each square ends up with 34 facts, and each place with 26
   years of daily rain.
5. **Shelve.** That table is shelf one. It is the same for every product.
6. **Ask.** A product asks its two questions of it: where can this happen,
   and is something setting it off now?
7. **Answer.** The result goes on shelf two and onto the screen, place by
   place, for the next seven days.
8. **Check.** The forecast is written down, and later graded against what
   happened.

**One file, three products.** The ground-height file arrives as 28
satellite tiles. The backbone turns it into steepness, the direction each
slope faces, how water drains, and how high each square sits above its
river. SlopeSense reads the steepness and the facing direction. FloodSense
reads the height above the river. The erosion module will read the slope
again.

## 5. How it helps a product

**A product is a question asked of the backbone.** Every hazard has the
same shape: WHERE can it happen (the ground — barely changes) × WHEN is
something setting it off (rain, the river — changes daily).

| A product gets for free | A product adds itself |
|---|---|
| The shared map and its 34 facts per square | Its WHERE question |
| 26 years of rain, and live rain for the next 7 days | Its WHEN question |
| Rivers, catchments, roads, places and search | Its own record of what happened |
| Maps, 3D and the app's frame | Its own screen |
| The honest way of testing, and the forecast log and grader | |

**The same layers, reused** (● uses it today · ○ planned · – not used):

| Backbone layer | SlopeSense | FloodSense | Soil erosion (next) |
|---|:-:|:-:|:-:|
| Ground shape: steepness, facing, curves | ● | ● | ○ |
| Drainage: channels, catchments, height above river | ● | ● | ○ |
| Soil | ● | – | ○ |
| Rock types and fault lines | ● | – | – |
| Land cover | ● | – | ○ |
| Rain history, 26 years | ● | ● | ○ |
| Live rain and 7-day forecast | ● | ● | ○ |
| River gauges | – | ● | – |
| Soil wetness, daily | – | ● | – |
| Roads, places, search | ● | ● | ○ |
| Honest testing, forecast log and grading | part | ● | ○ |

Four proofs that this is real, not a slogan:

- The first flood module reused all of it and added **two files** of its
  own maths.
- **One rain fetch** serves both products.
- In the app, a new module is **a folder and one line** in a list.
- **Each product leaves the backbone richer.** Flood brought in 32 river
  gauges, a verified flood record, the forecast log and a denser rain grid.
  The denser rain now feeds the landslide forecast too, and the log is what
  landslides will use next.

## 6. What else can stand on it

**More hazards.** Anything with the WHERE × WHEN shape fits.

- **Soil erosion, for Assam — next.** The department names five
  ingredients: rain, soil, slope, plant cover, land use. Four are already
  in the backbone.
- Glacial-lake floods, forest fire, earthquake-triggered slides, riverbank
  erosion, city flooding.

**More places.** The satellite inputs are global, so the same steps run
anywhere. A new state needs a switch for the region, its own local records,
and its own checking. Assam is the first test.

**More users of the data itself** — through an open feed, later:

- road and infrastructure planners, who need to know which corridor is
  fragile;
- power and telecom operators with assets on unstable ground;
- insurers and risk modellers;
- researchers and agencies who need the lined-up base layers;
- the state's own systems, so a warning shows up where officers already
  work;
- other startups building their own products.

None of this last group exists yet. It needs the open feed, and each
source's terms must allow sharing.

## 7. Why it gets stronger with time

- **The loop makes its own ground truth.** Each forecast, once graded,
  becomes a dated, located example that did not exist before.
- **New kinds of data land on the same map.** Our own sensors, drone
  surveys, field and citizen reports, old road-closure logs and news
  records: each becomes one more column, or one more dated event.
- **Sensors go where the backbone points.** It ranks the ground, so it
  tells you which slopes and rivers deserve an instrument. Their readings
  then come back in as data.
- **What is ours.** Most inputs are public. What is ours is the assembly,
  the upkeep and the checked local history. Code can be copied; seasons of
  checked local history cannot.

## 8. How the backbone grows — the ladder

| Step | Data | What every product on top gains |
|---|---|---|
| **Free — today** | Open satellite and government data | An area, days ahead |
| **Ask — letters, not money** | What offices hold: rain gauges, road-closure logs, river cross-sections, dam schedules | Finer and faster |
| **Paid — on chosen spots** | What we generate: sensors, drones, detailed terrain surveys | One slope or river reach, hours ahead |

Each step sharpens every product at once, because they all read the same
backbone.

## 9. Where it stands today

| Part of the backbone | State |
|---|---|
| Collecting outside sources | **Built.** 29 sources catalogued, about 308 GB of raw files, river gauges and flood records included |
| Raw store, with a record for every file | **Built** |
| One shared map | **Built.** 8.2 million squares, 34 facts each, 26 years of daily rain |
| Two shelves | **Built** as files. No outside access yet |
| Products on top | **Two live:** SlopeSense and FloodSense |
| The loop: write down, grade | **Built for floods**, daily since late September. **Landslide forecasts are written down daily since 10 October**, not graded yet: nothing feeds dated landslides in |
| Automatic daily run | **Built for floods** (08:30, on one PC). The rest is run by hand |
| Checking sources as a standing gate | By hand today |
| A second state | **Designed** (Assam). Everything is wired to Arunachal today |
| Open feed, other apps | Planned |
| Partner and field intake, own sensors | Planned |

## 10. The two products, as proof

**SlopeSense — landslide forecast (live).** WHERE: how weak is this ground,
learned from about 37,000 mapped landslides inside Arunachal. WHEN: is the
rain unusual for this exact place. It gives a 7-day outlook for any place
and for roads. WHERE picks the right spot about 6 times in 7. It gives a
rank, not a percentage. Its forecasts are written down every day since
10 October; they are not graded yet, because nothing feeds dated
landslides in. Since 10 October it has the same dashboard look as
FloodSense.

**FloodSense — flood forecast (live, the furthest along).** WHERE: how
easily does water reach this spot. WHEN: rain here and upstream, plus the
river's own level at 32 gauges. It runs by itself every morning and grades
itself against the real river. At a gauged river, when it says 20%, about
20% happen. It has not yet been through a live flood: logging began as the
monsoon ended.

## 11. Honest limits

- **Wired to one state.** Moving it to a second is designed, not built.
- **The loop is closed for floods only.** Landslide forecasts are written
  down but not graded. There is no live catch yet.
- **No outside users yet.** No open feed, no partner intake, no sensors.
- **It runs on one PC.** Two days have been missed so far.
- **Sharing data outward** depends on each source's terms of use.

## 12. What is next

1. **Prove it moves.** The Assam soil-erosion module: a new hazard and a
   new state at once. It is our entry for the NESFIC 2026 challenge.
   **Applications close 25 October; the build has not started.**
2. **Grade the landslide forecasts** (they are written down now; grading
   needs dated landslides, such as road-block logs) and run the whole
   pipeline by itself, off the PC.
3. **Stamp every answer with its inputs,** so any past forecast can be
   rebuilt.
4. **Open the feed.** Read-only first, the two shelves separately. Only
   after the pipeline runs itself: a feed of stale data is worse than none.
5. **Let others write in,** through a holding area, then add our own
   sensors.
6. **A pilot at Jang, Tawang,** for ground truth in the mountains.

## 13. The demo — backbone first

**Before the meeting**

1. **Show it from this PC if you can.** It has today's forecast. The old
   public link is the August version. The new screens were pushed for a
   second link on 6 October; once that app is set up it is a fair backup,
   but its flood forecast stays frozen on the day it was pushed.
2. Start it from the project folder:
   `.venv\Scripts\python -m streamlit run webapp/app.py`
3. Open FloodSense once. The dot beside "Issued" should be green. If the
   forecast is a day old, press **Run now** then (1–3 minutes). Never
   during the demo.

**The path**

| Step | Click | Say |
|---|---|---|
| 1 · 20 s | Landing page | "Two products on top. One backbone underneath. An empty slot for the next." |
| 2 · 60 s | **Data Backbone → Pipeline** | "This is the idea in one picture. Sources in, one shared map, two shelves, products out, and what happened comes back. Solid is built, pencil is planned." |
| 3 · 40 s | **Data catalogue** | "Every source, with where it came from and when. And the one that moves daily: 26 years of rain." |
| 4 · 30 s | **Layer explorer** | "One column of the shared map. Every product reads these same layers." |
| 5 · 60 s | **SlopeSense → Forecast**, search a town | "A product is a question asked of the backbone. This one asks: weak ground, times unusual rain." |
| 6 · 90 s | **FloodSense → Live forecast**, search Pasighat, scroll to the track record | "Second product, same backbone. And here is the loop: every forecast written down, then graded." |

**Watch out for**

- The Data Backbone pages were rebuilt on 9 October and now list the river
  gauges, the flood record and both forecast logs.
- Either forecast page has a **one-page report** button. It downloads a
  printable page with both forecasts for the place on screen: useful to
  hand over at the end of a demo.
- **A SlopeSense class is a rank, not a chance.** "High" means "look here
  first". Each level now carries a measured figure: places and days at High have had about 3 times the usual landslides, Very High about 10 times (from 84 dated landslides, so rough).
- It is October: flood screens are quiet. Say it first.

## 14. Questions you will get

**What exactly is the Data Backbone?** A standing system that collects
every useful source, keeps the originals, lines everything up on one map of
the state, keeps it fresh, hands it to products, and records what they said
and what really happened.

**Is it a product, or plumbing?** Today it is the engine under our two
products. Later it is a product in its own right, through an open feed
others build on.

**Why not just build the landslide app?** Because the app is the last small
part. The data underneath is most of the work, and it is the same data
every hazard needs. Built once, it makes each next product cheap.

**The data is public. What is yours?** The assembly, the upkeep and the
checked history. Twenty-nine sources made to fit one map, kept current,
with every forecast graded. Anyone can download the same files. Few will
do the rest.

**Who else would use it?** Road and infrastructure planners, power and
telecom operators, insurers, researchers and agencies, the state's own
systems, other startups. None yet: the open feed is planned.

**How do you add a new hazard, or a new state?** A hazard brings its own
two questions and its own record; everything else is already there. A state
needs a region switch, its own local records and its own checking. Assam is
the first test.

**What stops Google or ISRO doing this?** They could build the pipeline.
The hard parts are local: getting these sources to fit, knowing which
official layer is unusable, and seasons of forecasts checked against these
rivers and slopes.

**Is it live?** The backbone and two products are. The loop runs for
floods. The open feed, partner intake and sensors are planned.

**How good are the products?** Landslide WHERE picks the right spot 6 times
in 7. At a gauged river, 20% means 20%. Never one headline number.

**Has it caught a real event?** Not yet. It was tested hard on past years.
The next monsoon is the proof.

*Not in our docs:* pricing and market size. The shape we do have is the
ladder — a free statewide layer, then paid tiers.

## 15. Numbers, and what not to say

| Number | What it is |
|---|---|
| 29 | sources lined up; about 308 GB of raw files |
| 8.2 million | squares of 100 m on the shared map, 34 facts each |
| 26 years | of daily rain for every place, no gaps |
| 1.9 million | river gauge readings, some back to 1971 |
| 2 | products live on one backbone |
| 2 files | what the first flood module added of its own |
| 4 of 5 | erosion ingredients already in the backbone |
| 4,032 | flood forecasts written down since 21 Sep; 1,938 graded |
| about 5 MB | the app itself, which is why it runs on free hosting |
| 25 Oct | NESFIC application closes |

**Do not say**

- "We are a landslide app" or lead with the forecast. Lead with the
  backbone; the products are the proof.
- "Others already build on it" or "the feed is open". Planned.
- "It works for any state." Designed; Assam is the first test.
- "The loop is closed." It is, for floods.
- "We own unique data." Most inputs are public. Ours is the assembly and
  the checked record.
- "It is X% accurate", "we caught a real event", "safe", or a landslide
  class as a percentage.
- Anything planned as if it is live: sensors, SMS alerts, the open feed.
  Several sit on the pitch-deck slides.

**One naming point:** the pitch deck calls the whole platform "SlopeSense".
In the app, SlopeSense is the landslide module only, and the backbone has
its own name. Decide which you will say.

## 16. Where the detail is

| For | Read |
|---|---|
| The backbone: target, what is built, the plan | [PLATFORM_ARCHITECTURE.md](design/PLATFORM_ARCHITECTURE.md) |
| The shared map and its rules | [DATA_CONTRACT.md](design/DATA_CONTRACT.md) |
| Every source, tested | [DATA_VERIFICATION.md](data_research/DATA_VERIFICATION.md) |
| Moving it to a second state and a third hazard | [EROSION_MODULE.md](design/EROSION_MODULE.md), [EROSION_PLAN.md](design/EROSION_PLAN.md) |
| How the whole system works, in plain words | [DESIGN.md](design/DESIGN.md) |
| The flood product | [FLOOD_MODULE.md](design/FLOOD_MODULE.md), [RIVER_FORECAST_RECAP_2026-10-06.md](design/RIVER_FORECAST_RECAP_2026-10-06.md) |
| The landslide product | [MODEL_SUSCEPTIBILITY.md](design/MODEL_SUSCEPTIBILITY.md), [BACKTEST.md](design/BACKTEST.md) |
| The pilot and the asks | [CEO_PILOT_NEXT_STEPS.md](design/CEO_PILOT_NEXT_STEPS.md), [GOV_DATA_REQUEST_LIST.md](design/GOV_DATA_REQUEST_LIST.md) |
| Competitors | [COMPETITOR_IIOTS.md](design/COMPETITOR_IIOTS.md), [COMPETITOR_ALERTIS.md](design/COMPETITOR_ALERTIS.md) |
