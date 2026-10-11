# Presenting the Data Backbone — the script

**As of 10 October 2026 · 13 slides · about 9 minutes with the screens in the slides, about 12 with a live demo.**

**Visual version:** [PRESENTATION_SCRIPT.html](PRESENTATION_SCRIPT.html) — the same script with a picture of each slide beside its words. **The slides:** [PRESENTATION.html](PRESENTATION.html). The fuller background is in [BRIEFING.md](BRIEFING.md).

The words under **Say** are written to be spoken. Use your own words where they sit better; keep the order and the numbers.

---

## 1. Before you start

1. Open **docs/PRESENTATION.html** by double-clicking it. Press **F** for full screen. It needs no internet: the fonts and pictures are inside the file.
2. Move with the **arrow keys**, the space bar, a clicker, or a click on the slide. To jump, **type the slide number and press Enter**.
3. If the projector washes out the dark slides, press **T** for the light version. It remembers your choice.
4. For the live demo, start the app from the project folder before the meeting: `.venv\Scripts\python -m streamlit run webapp/app.py`. Keep it open in a second browser tab.
5. Open **FloodSense** once. The dot beside "Issued" should be green. If the forecast is a day old, press **Run now** then and wait one to three minutes. Never press it during the demo.
6. The app's maps and live rain need internet. If the room has none, take the route without the app: slides 8 to 10 carry the screens.
7. To hand the deck over afterwards, open it and press **Ctrl+P**, then "Save as PDF". You get 13 pages, one per slide.

**Two speakers?** A split that works:

- **Speaker one, the idea:** Slides 1 to 7, then 11 to 13.
- **Speaker two, the products:** Slide 8, the live demo (or slides 9 and 10), and the questions about how the forecasts work.

## 2. The talk at a glance

| Slide | What it does | Time | Clock |
|---|---|---|---|
| 1 | Title | 0:20 | 0:20 |
| 2 | The problem | 1:05 | 1:25 |
| 3 | The idea | 0:40 | 2:05 |
| 4 | How it works | 1:00 | 3:05 |
| 5 | Six rules | 0:50 | 3:55 |
| 6 | A product is a question | 0:40 | 4:35 |
| 7 | Same layers, reused | 0:45 | 5:20 |
| 8 | Running today | 0:20 | 5:40 |
| 9 | SlopeSense | 0:40 | 6:20 |
| 10 | FloodSense | 0:45 | 7:05 |
| 11 | What else | 0:45 | 7:50 |
| 12 | Stronger with time | 0:50 | 8:40 |
| 13 | Close | 0:45 | 9:25 |

With the live demo, slides 9 and 10 are replaced by about four minutes in the app, so the whole talk is about 12 minutes.

## 3. Slide by slide

### Slide 1 · Title · 0:20

**Say**

> Thank you for having us. We are BEE Solutions.
>
> What we want to show you today is not one app. It is what sits underneath the apps: one shared data backbone for mountain hazards. Ten minutes, and you will see it running.

**Do:** Have this slide up while people settle. Press F for full screen before you start.

### Slide 2 · The problem · 1:05

**Say**

> Start with the problem. The facts you need to see a landslide or a flood coming already exist. Ground height, soil, rain, rock types, rivers, river gauges.
>
> But look at the shapes they come in. One arrives every 30 metres. One every 11 kilometres. One is outlines, one is lines, one is single points. They sit with a dozen agencies, each in its own format.
>
> So every team hits the same four walls. The data is in pieces. Every project starts from zero: months of lining things up, one map published, and the work is thrown away. That map goes stale, because the ground stays put but rain and rivers change every day. And nobody keeps score. Forecasts are not written down and checked afterwards.
>
> That is why we keep seeing static maps, one-off studies, and pilots that never scale.

**Do:** Point at the tilted cards on the left first, then go down the four walls on the right.

### Slide 3 · The idea · 0:40

**Say**

> Our idea is simple. Do the hard part once. Collect every useful source. Check it. Line it up on one shared map. Keep it current.
>
> Picture the state cut into 8.2 million squares, each the size of a football field. Every source becomes one more layer on those same squares. So for any square of ground, you can read straight down and get every fact about it.
>
> And then anything can be built on top.

**Do:** Trace the dotted line down through the four layers as you say "read straight down".

### Slide 4 · How it works · 1:00

**Say**

> This is how it works, left to right. Collect: we fetch each source, and the weather every day. Keep: the original file is stored untouched, with a record of where it came from. Line up: it is fitted to the shared map. Shelve: there are two shelves, one for ready-to-use data and one for the forecasts. Serve: products read from those shelves.
>
> The line underneath matters most. Every forecast is written down before the day and checked after it. What really happened comes back in as new data.
>
> Today that is 29 sources, 8.2 million squares, and 26 years of daily rain for every place in the state.

**Do:** Walk the five boxes with your hand. Pause on the dashed bar: it is the part most systems do not have.

**If asked:** "Is all of this automatic?" The flood side runs by itself every morning. The rest is still run by hand; making the whole pipeline run itself is one of our next steps.

### Slide 5 · Six rules · 0:50

**Say**

> Six rules are built in, and they are why you can trust what comes out.
>
> One map for everything, so two products can never disagree about where a place is. We keep the original, so any number can be traced back to its source. We check a source before trusting it; official data can be wrong, and we have caught it.
>
> Nothing in the backbone names a hazard; a product brings its own question. There are two shelves, because someone planning a road wants base layers and an officer wants a forecast. And we close the loop: every forecast is graded.

**Do:** Do not read all six cards out. Say the first three slowly, the last three quickly.

**Careful:** There is a strong example for rule 3: the only official flood map of the state put most of its "flooded" ground on steep slopes, and one wrong river reading once looked like a 52% flood. Use it only if the room is right. Never aim it at an agency that is in the room.

### Slide 6 · A product is a question · 0:40

**Say**

> So what is a product? A product is a question asked of the backbone.
>
> Every hazard has the same shape. Where can it happen: that is the ground, and it barely changes. Times, when is something setting it off: that is rain and rivers, and they change every day.
>
> For landslides: weak ground, times rain that is unusual for that place. For floods: ground that water can reach, times rain upstream and the level of the river. The backbone already holds both halves. The product only brings the question.

**Do:** Point at WHERE, then WHEN, then read the SlopeSense and FloodSense rows across.

### Slide 7 · Same layers, reused · 0:45

**Say**

> And here is the saving. Down the left are the backbone's layers. A filled dot means a product uses that layer today.
>
> Our landslide forecast came first and used nearly all of them. When we built the flood forecast, it reused those layers and added just two files of its own. One rain fetch now serves both.
>
> The last column is what comes next: soil erosion. Hollow dots are planned, and you can see most of what it needs is already there. That is what we mean by doing the hard part once.

**Do:** Run a finger down the SlopeSense column, then the FloodSense column, then land on the big "2 files".

**If asked:** "What are the two files?" The flood product's own maths for its two questions. The shared map, the state boundary, the place search, the maps on screen, the rain fetch and the rain history were all already there.

### Slide 8 · Running today · 0:20

**Say**

> This is not a plan on paper. It is running today.
>
> WITH THE APP: Let me show you. (Switch to the app and follow the live demo steps below. Come back to slide 11.)
>
> WITHOUT THE APP: These next screens are from the app, taken on 10 October. First the backbone itself: every source it draws from, on record, and every layer on one map. Then the two products.

**Do:** Decide before the meeting which of the two routes you are taking. Do not decide on this slide.

### Slide 9 · SlopeSense · 0:40

**Say**

> First product on the backbone: SlopeSense, the landslide forecast.
>
> It asks the backbone one question. Where is the ground weak, and is the rain unusual for that place? Pick any town or road and it gives a seven-day outlook, on a map in five classes from very low to very high. High simply means look here first.
>
> Now look at the box at the bottom. Ground shape, soil, rock types, land cover, rain. Everything it reads was already in the backbone.

**Do:** Point at the level card on the left of the picture (the level today, with a bar for each of seven days), then the coloured map, then the "Reads from the backbone" box.

**If asked:** "How accurate is it?" Keep it short: "Today is about the backbone. We would rather take you through the testing properly in its own session than quote one number."

### Slide 10 · FloodSense · 0:45

**Say**

> Second product: FloodSense, the flood forecast. Same backbone. Only the question is new.
>
> Can water reach this ground, and are the rain and the river rising? It gives a seven-day flood outlook for any place, and it follows the river gauges on its own rivers. It runs by itself every morning.
>
> It also keeps its own record. The small panel shows every forecast written down, then checked against the real river. That is the loop from the pipeline slide, working.
>
> And again the box at the bottom: nearly everything it reads was already there.

**Do:** Point at the big picture for "runs every morning", the small panel for "keeps its own record", then the box.

**Careful:** It is October. The numbers on the flood screen are low because the rivers are quiet. Say so before anyone wonders.

### Slide 11 · What else · 0:45

**Say**

> What else can stand on it? Three directions.
>
> More hazards: anything with a where and a when. Soil erosion is next, then glacial-lake floods, forest fire, riverbank erosion. More places: the satellite inputs are global, so the same steps run anywhere. Each new state adds its own local records and its own checking, and Assam is the first test. And more users of the data itself: road planners, power and telecom, insurers, researchers, the state's own systems.
>
> To be clear about the dashed ones: that last group is planned, through an open feed. It is not there yet.

**Do:** Touch each column once, then the bar underneath: "one backbone under all three".

### Slide 12 · Stronger with time · 0:50

**Say**

> It also gets stronger with time, in two ways.
>
> First, the loop. Each forecast, once graded, becomes a dated, located example that did not exist before. Code can be copied. Seasons of checked local history cannot.
>
> Second, the data can climb. Today it runs on free, open data and gives you an area, days ahead. The next step costs letters, not money: records that offices already hold make it finer and faster. The top step is our own sensors and surveys on chosen spots: one slope or one river reach, hours ahead.
>
> And each step sharpens every product at once, because they all read the same backbone.

**Do:** Go round the ring once with your hand. Then climb the three steps from the bottom up.

**If asked:** "What records would you ask for?" Rain-gauge readings, road-closure logs, river cross-sections and dam release schedules. All of it already sits in offices.

### Slide 13 · Close · 0:45

**Say**

> So here is the picture to keep. An app is a vehicle. The backbone is the road. We are building the road, and running the first two vehicles on it to show it carries weight.
>
> Next for us: a new hazard in a new state, the loop for landslides, and then an open feed.
>
> And where you come in. If you have a hazard you worry about, a place you are responsible for, or data sitting in a cabinet, that is where we would like to start. Thank you. We are happy to take questions.

**Do:** Leave this slide up through the questions.

## 4. The live demo (from slide 8)

| Step | Click | Time | Say |
|---|---|---|---|
| 1 | **Landing page** | 20 s | "Two products on top. One backbone underneath. And an empty slot for the next one." |
| 2 | **Data Backbone → Pipeline** | 50 s | "This is the idea in one picture, inside the app. Sources in, one shared map, two shelves, products out, and what happened comes back. This page was last rebuilt in August, so it still marks the daily run and the forecast log as planned. For floods both are live now." |
| 3 | **Data catalogue** | 30 s | "Every source, with where it came from and when we fetched it. River gauges, the flood record and both forecast logs are on the list." |
| 4 | **Layer explorer** | 25 s | "One layer of the shared map: ground height for the whole state. Every product reads these same layers." |
| 5 | **SlopeSense → Forecast, search a town** | 45 s | "A product is a question asked of the backbone. This one asks: weak ground, times unusual rain. Seven days, for any place. "High" means look here first." |
| 6 | **FloodSense → Live forecast, search Pasighat, scroll to the track record** | 60 s | "Second product, same backbone. It runs by itself every morning. And here is the loop: every forecast written down, then graded against the gauge." |

**Watch out for**

- Never press **Run now** in front of people.
- SlopeSense now looks like FloodSense: tiles on top, then place, map and day buttons. A level is a rank ("look here first"), never a chance.
- Either forecast page has a one-page report button: a printable page with both forecasts for the place on screen. Good to hand over at the end.
- After the demo, go back to the deck, type **11** and press **Enter**. That skips the two screenshot slides you have just shown live.

## 5. If something goes wrong

| If | Then |
|---|---|
| The app will not start, or is slow | Stay in the deck. Slides 8 to 10 are the same screens. Say "these were taken on 10 October" and carry on. |
| No internet in the room | The deck still works. The app's maps will be blank, so take the route without the app. |
| The flood forecast is a day old | Say so: "this is yesterday's issue". Do not press Run now. |
| The slides look washed out | Press T for the light version. |
| You are running long | Cut slide 5 to one sentence ("six rules keep it honest, the main one is that every forecast is graded") and skip the ladder half of slide 12. |
| You are asked something you do not know | "I do not want to guess at that. Let me come back to you with the exact answer." |

## 6. Questions you will likely get

**What exactly is the Data Backbone?** A standing system that collects every useful source, keeps the originals, lines everything up on one map of the state, keeps it fresh, hands it to products, and records what they said and what really happened.

**The data is public. What is yours?** The assembly, the upkeep and the checked history. Twenty-nine sources made to fit one map, kept current, with every forecast graded. Anyone can download the same files. Few will do the rest.

**Is it a product, or plumbing?** Today it is the engine under our two products. Later it is a product in its own right, through an open feed others build on.

**How good are the forecasts?** Keep it short. Today is about the backbone, and the two forecasts are the first things built on it. Offer a separate session on how they are tested instead of quoting a number. If you are pressed, the tested figures are in BRIEFING.html.

**Has it caught a real event?** Not yet. It was tested hard on past years. The next monsoon is the proof.

**How do you add a new hazard or a new state?** A hazard brings its own two questions and its own record of what happened; everything else is already there. A state needs its own local records and its own checking. Assam is the first test.

**What stops a big player doing this?** They could build the pipeline. The hard parts are local: getting these sources to fit, knowing which official layer cannot be used, and seasons of forecasts checked against these rivers and slopes.

**Who uses it today?** Our own two products. Nobody outside yet: the open feed is planned.

**Can we have the data?** The forecasts are what the app shows. Sharing the base layers depends on each source's terms of use, and that is what the planned open feed is for.

**What do you need from us?** One of three things: a hazard you care about, a place you are responsible for, or records you already hold that could make the forecasts finer.

**What does it cost?** We have not set a price in any of our documents. Agree your answer with the team before the meeting. The shape we do have is the ladder: a free statewide layer first, then finer paid tiers.

## 7. Words to avoid

| Do not say | Because |
|---|---|
| "We are a landslide app." | Lead with the backbone. The products are the proof. |
| "Others already build on it" or "the feed is open." | Both are planned. |
| "It works for any state." | It is designed to. Assam is the first test. |
| "The loop is closed." | It is, for floods. Landslides are next. |
| "We own unique data." | Most inputs are public. Ours is the assembly and the checked record. |
| "It is X% accurate", "it is safe", or "we caught a real event." | Describe what each product does. Leave accuracy for its own session. |
| A landslide class as a percentage. | "High" is a rank: look here first. |
| Sensors, SMS alerts or the open feed as if they are live. | All planned. |
