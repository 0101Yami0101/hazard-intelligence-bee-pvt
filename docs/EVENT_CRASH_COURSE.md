# Hazard Platform — Field Notes

_Crash course for the Genesis EIR 3.0 roadshow. Generated from the published artifact — edit the HTML, not this file._

> **⚠️ Status note, 6 October 2026.** Written in August for one event. The
> landslide answers still hold. **The flood answers are out of date** — Q5,
> Q14, Q15, Q71–Q72, Q78, Q83–Q84, Q105–Q106, Q117, Q123, Q132, the demo
> steps in §10 and the flood line in §11. Since then FloodSense has learned
> from 2,185 verified floods, reads 32 river gauges, and runs, logs and
> grades itself every morning. This file also opens with the forecasts; the
> agreed framing now opens with the Data Backbone, with the products as
> proof. For the current picture read [BRIEFING.md](BRIEFING.md) first.

One platform, two hazards, one shared engine — and a plan that goes a long way past what's running today. **134 questions, ordered by how likely you are to face them.** Sections 2 and 4 are where the real judging happens; if time is short, read those twice.


---

## 00 · The three answers you must have by heart

_Everything else branches off these. Learn the shape, not the wording._

> _The 20-second version._ "We forecast landslides and floods for Arunachal Pradesh — like a weather forecast, but for disasters. Every morning the system reads satellite rainfall and terrain data and tells you, area by area, what's likely in the next few days. It's live now, and it's built on a shared data engine that any new hazard or any new state can plug into."

> _The 60-second version — add this if they're interested._ "Underneath, every hazard splits the same way: **WHERE** can something fail — that's terrain, soil, rock, drainage, and it barely changes year to year — multiplied by **WHEN** is something pulling the trigger, which is rainfall, and that changes hourly. Neither half warns anybody on its own. Existing landslide maps in India are only the WHERE half — a static map that looks the same in January and August."
> 
> "We built both halves on one shared grid, so landslide and flood are siblings, not separate products. The long game is the data loop: every forecast we issue gets logged, checked against what actually happened, and fed back as training data. That's what turns a model into something that gets measurably better every monsoon."

> _The vision line — for whoever asks "where's this going?"_ "A hazard-intelligence backbone for the whole Himalaya. Right now it's satellite-driven and statewide. Next it grows its own ground truth — sensors on the slopes our own model flags as worst, drone surveys, field reports, and text-mining decades of road-closure records. As that data accumulates, the models go deeper — ensembles, sequence models, graph networks over the river system. Arunachal is the proving ground, not the ceiling."


---

## 01 · What the room will actually be like

_Honest read from how AIC-SMUTBI and APIIP outreach sessions run — not a published agenda._

- **EXPECT** — A briefing on the ₹10 lakh Genesis EIR grant plus the financial-literacy bootcamp, in a room at the APIIP office. Founders at wildly different stages — from "I have an idea" to running revenue.
- **EXPECT** — A go-round where each founder introduces their startup in a sentence or two. Your 20-second version, verbatim. Have it before you walk in.
- **LIKELY** — Informal conversations afterward with AIC-SMUTBI / APIIP mentors. **This is where the real technical questions land** — they're quietly deciding whether to encourage a full application.
- **POSSIBLE** — A technically strong person in the room — a mentor with a deep-tech background, another CTO. Sections 2 and 4 exist for exactly this person.
- **NOTE** — The invite favours IT-based startups at ideation stage or under two years old. Sounding **technically fluent and clearly scoped** helps you more than sounding big.

---

## 02 · The product and the vision

_Twelve questions. If you can only prep one section, prep this one — every conversation starts here._


### Q1 — What does your startup do?

**Say:** Use the 20-second version at the top. Then stop talking and let them ask — the follow-up tells you which of the sections below to go into.


### Q2 — What's the vision — where is this in five years?

**Say:** A hazard-intelligence backbone for the entire Himalayan belt. The engine we've built doesn't care which hazard or which state — it takes terrain and weather and event history for a region and produces daily risk. Landslide and flood are the first two. Forest fire, earthquake-triggered failures, glacial-lake outbursts are all the same shape of problem. And underneath it, a data asset nobody else in this region is accumulating: a growing archive of dated, located, verified hazard events.

> **Follow-up →** "Why is the data archive the important bit?" Because models are commodities — anybody can download the same algorithm. Nobody else has years of verified local events for this terrain, and you can't buy it or shortcut it. It only accumulates by running.


### Q3 — Why is this deep tech and not just a dashboard?  `core`

**Say:** The dashboard is the last five percent. Behind it: terabytes of satellite and government data from over twenty sources, all resampled onto one common grid of eight-point-two million cells covering the state; a machine-learning model trained on nearly forty thousand mapped historical landslides; twenty-six years of daily rainfall history so we can ask "is today unusual _for this exact place_"; and a validation method that deliberately makes our own scores look worse so they're honest. None of that is visible on the screen. That's the company.


### Q4 — What's the "Data Backbone" — is that a third product?

**Say:** It's the shared engine, and yes, eventually a product in its own right. Everything that pulls in a data source, cleans it, and lines it up on one map of the state lives there once. Both hazard modules read from it. The design rule from day one was that nothing in the engine is allowed to know which hazard it's serving — you pass it a hazard as an argument. That's why adding flood didn't mean rebuilding anything.

> **Follow-up →** "Why does that matter commercially?" Because a third hazard, or a second state, costs a fraction of what the first one did. That's the difference between an app and infrastructure.


### Q5 — Is this built, or still an idea?

**Say:** The core is built and running — you can open it right now, search any town in Arunachal, and see today's risk plus the next seven days. Landslide is furthest along, flood is right behind it. What's still being wired on is the loop around it: our own sensor network, the public data feed, and automatic logging of every forecast so we can prove our track record season after season.

> **Follow-up →** "So what would the grant actually fund?" Closing that loop. Concretely: instrumenting a pilot valley with our own sensors, building the data-feed layer, and the deeper models the accumulated data unlocks.


### Q6 — Why Arunachal specifically?

**Say:** Three reasons. It's one of the most landslide- and flood-exposed states in India — the terrain is extreme, median slope across the whole state is about twenty-nine degrees. Second, there's a genuine gap: the national geological survey runs an operational landslide forecast covering several neighbouring northeastern states and zero districts in Arunachal. Third, it's strategically important border terrain where a blocked road is a national issue, not just an inconvenience. And it's under-served — most landslide-tech work in India is happening in the western Himalaya, not the east.


### Q7 — Why landslides and floods together? Aren't those separate problems?

**Say:** Same cause. The same monsoon that saturates a hillside until it fails is the water swelling the river at its foot. So they share almost all of their inputs — terrain, drainage, rainfall history, population exposure. Building them separately would mean building the same pipeline twice. Structurally the two are identical: flood is "flood-prone ground times catchment rainfall" exactly as landslide is "unstable slope times rainfall on it."

> One difference worth knowing: a slope fails from rain landing **on** it; a river rises from rain landing **anywhere upstream**. So for flood we pool rainfall across nearly seventeen hundred catchment basins and route it downstream before it becomes a forecast.


### Q8 — Who actually uses this?

**Say:** Primary user is the state disaster management authority and district officers — they're the ones who issue warnings and move resources. Beyond that: the roads departments and border roads organisation who need to know which corridor is about to close, and eventually anyone through a public feed. The unit we report at is deliberately the administrative circle — because that's a real place with a name, an officer, and a phone number.


### Q9 — What's the single hardest technical problem you're solving?  `core`

**Say:** Dates. We know _where_ almost forty thousand landslides happened in this state — excellent data. We know _when_ for almost none of them. Government inventories record the location and the shape, and leave the date column blank. So the WHERE half of our model has abundant training data and the WHEN half is starved. That single fact drives the entire architecture, and most of our roadmap is different ways of manufacturing dated events we don't inherit.

> **Follow-up →** "So how do you fix that?" Five routes, running in parallel: our own sensors, satellite change-detection, mining decades of road-closure logs with language models, a citizen reporting app, and simply logging every forecast we issue against what actually happened. Section 3 has the detail.


### Q10 — Why hasn't someone already done this?

**Say:** Pieces of it exist. Static hazard maps exist. Global flood models exist. Sensor companies exist. What doesn't exist is any of them joined up for this terrain, running daily, and validated locally. Partly that's because it's genuinely a lot of unglamorous data engineering before you get to the interesting modelling, and partly because the eastern Himalaya is remote enough that most groups work where access is easier.


### Q11 — What makes it defensible? What's the moat?

**Say:** Not the algorithm — algorithms are public. Three things. One, the accumulated data asset: a verified archive of dated local events that only grows by operating. Two, the calibration — twenty-six years of rainfall history _per location_, so we can say "this is unusual for here," which nobody gets by downloading a model. Three, once a disaster authority has built their monsoon workflow around your bulletins, switching is expensive.


### Q12 — What would you do with ten lakh?

**Say:** Keep it concrete and technical: instrument one pilot valley with our own low-cost sensors — that's the step that turns satellite estimates into measured ground truth and unlocks the hours-ahead warning tier. Alongside it, the automated pipeline and forecast-logging layer, so the data asset starts compounding rather than being recomputed by hand.

> **Follow-up →** If asked which valley: Tawang district, starting from Jang. Small enough to fully instrument, has real river gauges already reporting nearby, and carries a second hazard worth showcasing — glacial lakes and snowmelt above the valley, not just monsoon rain.


---

## 03 · The AI and ML stack

_**This is the section that decides whether a technical person takes you seriously.** Forty-one questions. The through-line: we pick the technique the data shape justifies, we have a specific plan for every deeper technique, and we can say exactly what unlocks each one._


### Q13 — Can you just explain the whole thing simply?  `core`

**Say:** **Step 1 — we cut the state into tiny squares.** Eight million of them, each about the size of a football field _(a 100 m grid — every square has an ID, and everything in the system joins on it)_. Every square gets its own card with facts written on it: how steep it is, which way it faces, what kind of rock and soil it's made of, how close the nearest river and road are.

**Step 2 — the WHERE team.** A panel of experts looks at each square and answers one question: _"how shaky is this ground?"_ They don't all work the same way:

- One **reads the card of facts** _(gradient-boosted decision trees — LightGBM. This is the one running today)_

- One **looks at a picture of the hill taken from space**, judging shape and texture rather than numbers _(a convolutional neural network — CNN — reading terrain as an image)_

- One **traces where loose material would travel** if the slope let go _(a graph neural network — GNN — over the drainage network)_

Each gives the square a score out of ten. Then a **boss** — who has watched these experts for years and knows which one is usually right about high mountains and which about river valleys — blends their scores into one final WHERE score _(the meta-learner in a stacked ensemble)_. This map barely changes. A cliff is still a cliff next month.

**Step 3 — the WHEN team.** A different panel, the same square, a different question: _"is something pulling the trigger today?"_

- One knows the **old scientific rule** about how much rain breaks a hillside _(the rainfall intensity–duration threshold — the physics floor)_

- One holds **twenty-six years of rain diaries** for this exact square and checks whether today is weird _for here_ _(percentile-normalised rainfall against that cell's own climatology — the rule shipping today)_

- One **reads the card of rainfall numbers** _(gradient-boosted trees again, on rainfall features)_

- One **reads the last month of rain like a story** and spots the build-up _(a sequence model — LSTM or temporal convolutional network)_

- One has **seen hillsides all over the world** _(a pooled regional / global model, fine-tuned to Arunachal — also our benchmark)_

Scores out of ten again, and again a boss blends them. This score changes **every single day**.

**Step 4 — multiply the two together.** Shaky ground × today's trigger = today's danger. We multiply rather than add for one simple reason: if either number is zero, the answer _must_ be zero. Flat solid ground in a storm is still safe. A terrifying cliff in dry sunshine is still standing. Adding would let a huge storm make flat ground look dangerous, which is nonsense — multiplying can't do that, because anything times zero is zero. It's a loaded gun and a finger on the trigger. You need both.

**Step 5 — turn squares back into places.** The squares are too small to be useful to anyone, so we group them into real places that have a name and an officer in charge _(administrative circles)_. Then we add how many people and buildings are there — because a dangerous slope above an empty valley and one above a school are not the same emergency. That's what gets published, for today and the next seven days.

**Step 6 — tomorrow, we check.** We look at what actually happened and write it down. That does two jobs at once: it slowly builds the list of real events we're short of, _and_ it grades the experts _(continuous backtesting; candidates run in shadow before promotion)_. An expert who keeps getting it wrong gets less say from the boss, or gets dropped entirely.

> **The one thing people get wrong about the boss.** It doesn't pick one expert and ignore the rest. It decides _how loudly each one gets to speak_ — and that changes with the situation, so an expert trusted in high terrain might be turned down in a river valley.

> **Follow-up →** "How many of those experts exist right now?" Be straight: the WHERE side runs on one strong expert today with the panel being built around it, and the WHEN side has the rule-keeper and the diary-reader. The others join as we gather enough real events to grade them fairly. **The architecture is the answer; the panel fills in.**


### Q14 — And how does the flood side work, in the same simple terms?  `core`

**Say:** **Same shape, one big difference.** For a landslide, the rain that matters falls _on_ the slope that gives way. For a flood, the rain that matters can fall fifty kilometres away and walk down to you. So the flood side has to follow the water.

**Step 1 — the same eight million squares.** We don't build a new map. Flood reads the same cards the landslide side reads. That is the whole point of having one shared engine underneath.

**Step 2 — the WHERE team asks a different question:** _"how easily does water sit here?"_

- One stands in each square with a **measuring stick** and works out how high above the nearest stream it is — then adjusts for how _big_ that stream is, because two metres above a small creek and two metres above a great river are completely different amounts of safe _(HAND — Height Above Nearest Drainage — weighted by upstream catchment area. This is what ships today)_

- One **draws the bowl**: all the land uphill whose rain eventually passes this point _(catchment delineation and flow accumulation, over the HydroBASINS network)_

- One **looks at pictures from space of where water has actually stood** _(radar open-water detection — Sentinel-1 SAR — which sees through cloud)_

Scores out of ten, and a boss blends them into one flood-prone score _(the same meta-learner idea as the landslide side)_. Like the landslide map, it barely changes.

**Step 3 — the WHEN team follows the water.** The question is _"is water on its way?"_, and the experts look far beyond the square itself:

- One **adds up every drop of rain falling anywhere in the bowl upstream** and carries it downhill _(catchment-pooled rainfall percentile, routed basin-to-basin downstream. This is what ships today)_

- One **reads the real river gauges** — actual water-level sensors on real rivers here, with decades of readings and official danger marks _(CWC river-level records and NWDP discharge series)_

- One is a **world-traveller who models the great rivers of the planet**, useful as a cross-check on our biggest rivers _(a global hydrological model — GloFAS-style discharge reanalysis)_

- One **watches the dams**, because sometimes a flood isn't the sky, it's a person opening a gate _(reservoir level and release-schedule feeds)_

Scores out of ten, boss blends, changes every day.

**Step 4 — multiply, exactly the same rule.** Water-prone ground × water on its way = today's flood danger. If the ground sits high above every river, it doesn't matter how much rain fell upstream. If no water is coming, low ground is just low ground. Anything times zero is zero.

**Step 5 — group back up into real places**, add the people and the buildings, publish for today and the week ahead. Identical to the landslide side, because it _is_ the same delivery layer.

**Step 6 — and here floods are easier to grade than landslides.** Standing water is easy to see from space, even through monsoon cloud, using radar. A landslide scar is hard to spot; a flooded field is unmistakable. So we can check yesterday's flood forecast against what actually happened far more reliably — which means the experts get graded faster, and the flood side learns quicker.

> **The one honest gap, if they push.** The flood ground-map rests on solid, well-understood physics but is not yet checked against local evidence. The only official flood map we could get for this state turned out to be unusable — more than seventy percent of the pixels it marks as flooded sit on steep slopes, and water does not pond on a cliff. The real river-gauge records we've since found are exactly what turns that from a well-founded assumption into a measured fact — see the next question.

> **Follow-up →** "Why is flood harder here than in the plains?" Because nearly all of Arunachal's water is in small, steep mountain streams that nobody gauges — only a tiny fraction of the network is covered by big-river forecasting. A flood in Assam builds over days on a huge slow river; here a stream can come up in an hour. **That's why the catchment-rainfall route matters more to us than the big-river route.**


### Q15 — Hang on — are you training on past floods at all?  `sharp`

**Say:** **Not yet — and the reason is the single most interesting thing about this problem.**

**A landslide leaves a scar. A flood leaves nothing.** When a hillside collapses, the bare patch is still visible from space years later — which is why we have nearly forty thousand mapped landslides **in Arunachal itself** to learn from. But a flood drains away. By the time a satellite looks, the water's gone and the field looks like a field again. So there simply is no flood equivalent of that inventory.

**We tried the one that exists, and it was unusable.** The only official flood map obtainable for this state marks more than seventy percent of its "flooded" ground on slopes steeper than fifteen degrees. Water does not sit on a cliff. It's a smeared picture, not an observation, so it can't referee anything — and we say so on the product's own method page rather than quietly scoring against it.

**But floods have something landslides don't: rivers get measured.** Nobody has a sensor on every hillside, but there have been instruments in rivers for decades. We've confirmed two open government sources — one with **fifty-five years of real river-level readings** for this state's major rivers, still updating today, with official danger and warning marks for each station; another with **over seven hundred thousand flow readings across fourteen smaller rivers** spread across many districts.

**And that turns a logbook into a flood record.** When a river crosses its official danger mark on a given day, that is an objective, government-defined flood event with a date attached. So we don't have a map of past floods — we have something arguably better for training the timing half: decades of dated, measured river behaviour. Converting that into training labels is the next build on the flood side.

**The insight worth landing:** **Landslide and flood are mirror images in our data.** Landslide is rich in _where_ — forty thousand mapped scars — and starved of _when_, because nobody wrote the dates down. Flood is the exact opposite: almost nothing on where the water went, but decades of dated measurements of rivers rising. That's why each hazard is attacked from a different direction, and why one shared engine carrying two different data strategies is the right architecture rather than one model stretched over both.

> **Follow-up →** "So today's flood forecast is untrained?" Today's flood ground-map is **physics, not learning** — established hydrology about how high above a river you sit, which is well understood and standard practice. It's a well-founded hypothesis about Arunachal rather than a measured fact about it, and that distinction is printed in the product. The gauge records are what close it.


### Q16 — Is this AI? What kind, exactly?  `core`

**Say:** Yes, and across several layers. The scoring models that run today are gradient-boosted decision trees — classical machine learning, best-in-class for tabular data at our scale, and crucially they can explain any individual prediction. On top of that we have deep learning in specific roles: computer vision on satellite imagery, sequence models for rainfall dynamics, graph networks for how water moves through a river system, anomaly detection on sensor streams, and language models for extracting events from written records. Each one is matched to a data shape trees can't handle.

> **Follow-up →** "Which of those are running now?" The trees are the live forecast today. The deep-learning layers come online as the data that justifies each one accumulates — several are prototyped, and the sequencing is deliberate, not aspirational.


### Q17 — Why trees and not deep learning for the main model?  `core`

**Say:** Because of the shape of the data, not fashion. Our main model reads a table — about thirty-four numbers per location: steepness, which way the slope faces, clay content, rock type, distance to the nearest fault, and so on. For tabular data at this size, boosted trees consistently beat neural networks; that's a well-established result, not our opinion. They also train in minutes rather than days, need no scaling of inputs, handle missing values, and — the decisive one — they can tell you _why_ a place scored what it scored.

> The honest framing to use: **a neural network on this table would be a worse model that's harder to defend.** We're not avoiding deep learning — we're using it where its strengths apply, which is imagery, sequences, graphs and text.


### Q18 — Isn't "just trees" a bit old-fashioned for a deep-tech grant?

**Say:** Trees are the current state of the art for tabular problems — every major competition on structured data is still won by them. But it's also not the whole stack, it's the first layer. The right way to describe us is: classical ML where the data is a table, deep learning where the data is an image, a sequence, a graph or a document — and a clear, measured condition for when each one gets promoted.

> **Follow-up →** "What's the condition?" A new technique has to beat the simpler one on _held-out regions_, by a margin bigger than the noise. If it doesn't, we don't ship it. We've already killed one model that way — see Q33.


### Q19 — So where does deep learning actually fit? Give me the map.  `core`

**Say:** **1 · Computer vision on satellite images** — detecting and dating new landslide scars and flood extents. Images, so a segmentation network.

**2 · Self-supervised / foundation models** — learning general terrain representations from enormous amounts of _unlabelled_ satellite data, so our scarce labelled events go further.

**3 · Sequence models** — LSTM or temporal convolution, learning how a multi-day rainfall pattern builds toward failure, rather than us hand-engineering "rain over the last 3 days, 7 days, 15 days."

**4 · Graph neural networks** — because water doesn't move cell-by-cell, it moves along the drainage network. That's a graph, so model it as one.

**5 · Anomaly detection** — autoencoders over sensor telemetry, catching abnormal slope behaviour earlier than a fixed threshold would.

**6 · Language models** — pulling dated, located events out of decades of unstructured written records, and drafting plain-language bulletins from structured output.


### Q20 — Walk me through the overall modelling plan — where does it end up?  `core`

**Say:** **WHERE.** We have around forty thousand mapped local landslides, so an ensemble is justified on that half today. Several genuinely _different_ model families score the same cell — boosted trees on the feature table, a network reading the terrain as an image patch, others alongside — and a second-stage model learns how much to trust each one. Diversity is the whole point: five variations of the same tree model make the same mistakes and buy you nothing.

**WHEN.** Same architecture, switched on as the data accumulates. The layers are: the physics curve, which never leaves and stays a hard floor; our per-location rainfall rule; a tree model; a sequence model once dated events allow it; and a global model fine-tuned to Arunachal, which doubles as the benchmark we have to beat. Rather than picking a winner up front, they all run, they get weighted according to the conditions, and they're ranked continuously against what actually happens.

**Flood mirrors it**, with one deliberate difference — we build our own river models on Arunachal's own gauge records rather than depending on a global one, because that's what's provable to a client. Global discharge feeds are a cross-check on the big trunk rivers, not the engine.

**The honest part:** an ensemble needs more data than any single model. So this is sequenced, and the ranking machinery is exactly what tells us when each layer has earned its place.

> **One word to get right.** The technique is **stacking**, and the blender inside it is **the meta-learner** — that noun is correct, use it. What to avoid is calling the whole approach **meta-learning**, which is a different field (adapting fast to a brand-new task from a handful of examples) and a sharp listener will correct you. If someone does ask whether you use meta-learning: not for the ensemble — but it is genuinely on the radar for expanding into a new state, where we would start with very few local labels. And the blender **weights** models, it doesn't **switch** between them; saying "it chooses the right one" invites "so what happens when it chooses wrong?"

> **Follow-up →** "That's a lot of models to maintain." Honest answer: a new model _family_ is real work — a network reading image patches needs a different data loader than trees reading a table. What the shared spine standardises is not the input shape, it is the **key, the labels and the validation**: every model scores the same cells on the same frozen held-out regions, so comparing a new candidate against every existing one is one command rather than a project. And we run many more candidates than we ship — the ranking exists to retire models as much as to add them.


### Q21 — Explain stacking simply.

**Say:** Imagine five specialists each look at the same slope and give a risk number. Averaging them is the crude version. Stacking is smarter: you train a second model whose job is to learn _which specialist to believe under which conditions_ — maybe one is reliable in high-altitude terrain and another during heavy monsoon. That second model is the "meta-learner." It usually beats any individual model and beats a plain average.


### Q22 — If the models read different kinds of data, how do you combine them at all?  `deep`

**Say:** They're anchored to the same cell. Each model reads a different _view_ of the same grid — trees read the feature table, a vision model reads a raster window centred on that cell, a sequence model reads the rainfall series for that cell's weather pixel, the physics term reads two rainfall aggregates. Different shapes going in, but every one of them emits a score **for the same cell, measured on the same frozen held-out regions**. So the blender's input is just a row of scores per cell, plus a bit of context like region and season.

> **Why the alignment is the whole trick.** To blend model outputs you need every model's prediction on the same rows under the same train/test split — otherwise you're combining scores that were never measured on comparable ground, and the blender learns an artefact of the splits rather than which model is actually better. **That discipline is what the shared spine exists to enforce**, and it's why the folds were frozen before any model was trained.

> **Follow-up →** "So the spine doesn't save you the modelling work?" No, and I wouldn't claim it does. It saves the _evaluation_ and _delivery_ work, which is the part that otherwise multiplies with every model you add.


### Q23 — How do you rank models against each other when real events are so rare?  `deep`

**Say:** Slower than it sounds, and worth being straight about. You can't score a landslide model weekly the way you'd score a recommendation engine — the events are rare and under-reported, so a single season gives you very few clean scores. So three things. We rank on capture rate and alert frequency rather than a false-alarm rate we can't honestly measure. We hold out whole _regions_ and whole _years_, never random days, so one unusual monsoon can't flatter a model. And candidate models run in **shadow** — scoring alongside the live one without issuing anything — so a challenger builds a track record before it's ever promoted.

> **Follow-up →** "So how long before you know?" Seasons, not weeks — and that's exactly why we're building the ranking machinery now rather than when we need it. Every monsoon it isn't running is evidence we can't get back.


### Q24 — Doesn't an ensemble throw away the explainability you just told me mattered?  `sharp`

**Say:** That's the real tension in the design, and there are three answers to it. The base models stay individually explainable — the per-cell attribution still works on each one. The blender is deliberately kept small and inspectable, so for any given alert we can report how much each model contributed rather than just the total. And the physics floor sits _outside_ the ensemble entirely, as a hard rule no model is allowed to override.

**And the closing line:** So an ensemble costs you some explainability and you buy it back by design. If we ever reach a point where the extra accuracy doesn't justify the opacity for a government user, we ship the simpler model — that's a rule we've already followed once, on the trigger.


### Q25 — What's your explainability story? What's SHAP?  `core`

**Say:** SHAP is a method that breaks one specific prediction into contributions. So instead of "this cell scored 0.81," we can say "0.81 because steepness contributed this much, aspect this much, rock type this much." Every score the system produces can be decomposed that way. That is not a nice-to-have here — an officer ordering an evacuation has to justify it, and "the neural network said so" isn't a justification anyone can act on.

> There's a discipline point worth mentioning: **we don't trust importance rankings on their own.** A tree can use a feature heavily without needing it. We test by removing a feature and re-measuring — one of ours consumed twenty-three percent of the model's attention but cost almost nothing in accuracy when deleted. It was redundant with terrain. You only find that by ablating.


### Q26 — What exactly is the WHERE model?

**Say:** A classifier trained on nearly forty thousand mapped historical landslides **inside Arunachal**, plus carefully chosen examples of ground that has no recorded failure. It reads about thirty-four properties of each hundred-metre cell — steepness, curvature, which way it faces, soil texture and density at three depths, rock unit, distance to the nearest fault, river and road, land cover, elevation — and outputs a relative susceptibility score. Static; rebuilt roughly yearly, not daily.

> Interesting result to have ready: **the strongest single predictor turned out to be which direction the slope faces**, ahead of steepness. Physically sensible in the Himalaya — north-facing slopes hold moisture and snow differently, which drives how the rock weathers.


### Q27 — Is this a national model pointed at Arunachal, or trained on Arunachal itself?  `core`

**Say:** **Trained on Arunachal itself — every one of those forty thousand landslides is inside the state.** One of our sources is a national database, the Geological Survey's landslide inventory, but it was clipped to the state boundary before any of it was used. Our own verification layer actually caught the edge case: 246 polygons where their map tiles spilled across into Nagaland and Assam. Those were removed — they'd been quietly inflating both our inventory count and our district list.

> **Why this is worth saying out loud to a state government.** "A national model applied to your state" and "a model trained on your state's own landslides" are very different claims. Most hazard products in this space are the first. Ours is the second, and it's the reason our accuracy numbers mean something locally rather than being an average across terrain that looks nothing like this.

> **Follow-up →** "So you never use data from outside the state?" Only in one specific place, and it's deliberate. The _where_ half has abundant local data, so pooling would add nothing. The _when_ half is starved, so pooling dated events from across the Himalayan arc is a scoped route — and the test is designed honestly: train on the arc **excluding** Arunachal, then test on Arunachal's own events the model has never seen. If it doesn't beat what we already ship, we don't ship it.


### Q28 — What exactly is the WHEN model?

**Say:** Today it's a deliberately transparent rule rather than a fitted model, and that was a measured decision. It takes rainfall over the last three days and the last seven days, and converts each into a percentile against _that exact location's own_ twenty-six-year history. So the question isn't "did it rain 150 millimetres" — it's "how unusual is this for here." That matters enormously in a state where annual rainfall ranges from about eight hundred to over four thousand millimetres. A fixed millimetre threshold would alert the wet south permanently and the dry north never.

> **Follow-up →** "Why not a learned model?" Q34. We tested it and it lost.


### Q29 — Why multiply the two halves rather than add them?

**Say:** Because both are necessary and neither is sufficient. A cliff in dry weather doesn't fail. A downpour on flat stable ground does nothing. Multiplying preserves that — if either term is near zero, the hazard is near zero. Adding would let a torrential day raise the risk score of flat ground, which is physically wrong.


### Q30 — How much training data do you have?

**Say:** For the WHERE half: nearly forty thousand mapped landslide polygons **from within the state itself**, which land on about ninety-one thousand grid cells, giving a training table of over half a million rows. That's a genuinely large local inventory. For the WHEN half it collapses to the low dozens of precisely-dated events — which, again, is the core problem and the reason for the whole data-generation roadmap.


### Q31 — Where do your negative examples come from?  `deep`

**Say:** Good question, and it's subtler than it looks. We have tens of thousands of places where a landslide happened and _zero_ places where a surveyor certified "nothing here" — nobody maps the absence of a landslide. So negatives have to be constructed. We draw them only from terrain that could plausibly fail, and keep them at least five hundred metres from any mapped slide, because a cell a hundred metres from a known failure is on the same hillside in the same rock under the same rain — calling it "safe" teaches the model a distinction that doesn't physically exist.

> **Follow-up →** "Does that improve your score?" Honestly, no — we measured it and the accuracy barely moves. We keep it for two reasons the accuracy metric structurally cannot see: about one in six naive negatives sits right next to a known failure and is probably an unreported landslide, and some would be glaciers and lakes the model has no business scoring at all. **Being able to say "we tested our own justification and it didn't hold, here's the real reason" is a strong signal to a technical listener.**


### Q32 — What is "presence-only" data and why does it constrain you?  `deep`

**Say:** It means our records only ever say where something _did_ happen, never where it didn't. That has a hard consequence we're upfront about: our output is a **relative** risk index — valid for ranking places against each other — not a probability. A score of 0.5 does not mean fifty percent chance of failure, and we never present it as one, because the denominator that would make it a probability doesn't exist in the data.

> **Follow-up →** "So how do you communicate risk?" As classes — five bands — which is what a disaster authority actually uses, and how the scientific literature reports it.


### Q33 — Your trigger is a rule, not a model. Isn't that a weakness?  `be honest`

**Say:** It's a deliberate choice, and we can show the measurement. We fitted a proper model on our dated events and cross-validated it — it scored _worse_ than the simple unfitted rule. With that few examples, fitting adds variance without adding signal; the model memorises quirks of those specific events. So we ship the simpler thing, which is more accurate _and_ easier to defend to a government reviewer. That's a rare case where simple wins on both counts.

> **Follow-up →** "So when does it become a model?" We have an explicit threshold for that — Q34.


### Q34 — What's your rule for upgrading to a more complex model?  `core`

**Say:** A three-step ladder, keyed to how many dated events we hold. Below a few hundred: stay with the transparent rule, and pool in events from the wider Himalayan arc. In the low thousands: a proper tree-based trigger model, weighted toward local events. Above several thousand _and_ with sub-daily timing: that's when a sequence network — LSTM or temporal convolutional — becomes worth testing, because at that point the _shape_ of a rainfall burst over hours carries signal our hand-built features can't capture. And even then it has to beat trees on held-out regions or it doesn't ship.

> Say this line if you can: **"we know what would justify each next technique, and we're not going to pretend we're there before we are."** That is exactly the kind of discipline a technical judge is listening for.


### Q35 — Sequence models — LSTM, transformers — what would you use them for?

**Say:** Right now we hand-build features like "total rain over the last three days, seven days, fifteen days." That's us guessing which summaries matter. A sequence model reads the raw day-by-day series and learns the pattern itself — and rainfall-to-landslide is genuinely a sequence problem: two days with identical rain today behave completely differently depending on whether the previous fortnight was dry or soaked. Same technique class underpins modern rainfall-runoff modelling for floods.

> **Follow-up →** "Why not now?" Sequence networks are hungry — they need thousands of labelled sequences to beat well-chosen hand-built features. We have the rainfall history; what we lack is enough dated outcomes to attach to it. That's the same bottleneck as everything else.


### Q36 — Graph neural networks — why would you need those?  `deep`

**Say:** Because a river network is a graph, not a grid. Today we route rainfall downstream through catchments with explicit rules — this basin flows into that one. A graph network learns propagation over that same topology directly, which is a much better fit for flood: what matters isn't the cell next to you, it's the basin upstream of you, which might be fifty kilometres away. The same idea applies to debris-flow runout on the landslide side — where the material actually travels once it fails, which is a flow-path problem, not a cell problem.


### Q37 — Foundation models / self-supervised learning — what's that for?

**Say:** This one is genuinely elegant. We have very little _labelled_ data — dated events — but an effectively unlimited supply of _unlabelled_ satellite imagery of this terrain. Self-supervised pretraining lets a model learn general representations of what Himalayan terrain looks like from all that unlabelled imagery, by giving it tasks like "we've hidden part of this image, reconstruct it." Then you fine-tune that pretrained model on your handful of labelled events. It's the same principle as large language models: learn broadly from cheap data, specialise on expensive data.

> **Follow-up →** "Is that realistic for a small team?" Increasingly yes — there are open geospatial foundation models published specifically for Earth observation, so we'd fine-tune rather than pretrain from scratch. That's the practical route.


### Q38 — Computer vision — what does it do here?

**Say:** Two jobs. One, detecting and dating change: a landslide scar appears in satellite imagery at a specific moment, so if you can spot when it first appears, an undated landslide becomes a dated event. Two, mapping flood extent in real time — radar can see open water through cloud, which is exactly what you need during a monsoon. Both are image-segmentation problems, which is precisely where deep learning is unbeatable.

> **Follow-up →** "Is it working?" We've done the feasibility work rather than assume it. Ordinary optical imagery hits a hard physical wall — Q59 has that story, and it's a good one because it shows we test before we build.


### Q39 — Anomaly detection — where does that fit?

**Say:** On the sensor side. A tiltmeter on a slope produces a continuous stream that is boring ninety-nine percent of the time. A fixed threshold — "alarm if tilt exceeds X" — only fires once things are already bad. An autoencoder learns what _normal_ looks like for that specific slope, including its seasonal rhythms, and flags departures from normal, which is earlier and adapts per site. Every slope has its own personality; a threshold can't learn that and a trained model can.


### Q40 — You mentioned language models — for what?  `deep`

**Say:** The most valuable dated landslide records in this state probably aren't in any database — they're in written records. Road-closure logs kept by the roads department and border roads organisation for decades for operational reasons. Government field investigation reports. News archives. Every one of those is a dated, located event trapped in prose. Language models are very good at pulling structured records out of unstructured text — date, place, what happened, what triggered it. That's a direct attack on our core data problem.

> Second, smaller use: **drafting the plain-language bulletin** from structured model output, so a district officer gets readable text rather than a table. Generated from numbers the models produced, never inventing content.

> **Follow-up →** "Have you found anything?" We've located an openly downloadable archive of the geological survey's own field investigation reports for this state going back to the 1950s — dozens of them, several with exact event dates in the title. That's a genuinely new source, and it's the kind of thing automated extraction is made for.


### Q41 — Physics-informed machine learning — what does that mean?  `deep`

**Say:** It means the model isn't allowed to contradict established science. There's a well-known relationship in landslide science between how hard it rains, for how long, and whether slopes start failing. We use it two ways: as an input the model can read, and as a hard floor on the alert system — the forecast is never allowed to go quiet below the established curve, no matter what the model thinks. Further out, physics-informed neural networks put those constraints inside the network architecture itself, so the physics isn't a bolt-on.

> **Follow-up →** "Why is that better than just letting the model learn?" Because a model learns from the data it saw. If a rainfall event bigger than anything in the record shows up, a pure model has no idea what to do — physics does. It's insurance against exactly the events that matter most.


### Q42 — Are you using transfer learning?

**Say:** Yes, but selectively, and it's worth being precise. For the WHERE half we don't need it — we have forty thousand local labels, that's plenty. For the WHEN half it's exactly the right tool, because that's where we're scarce. The route we've scoped: pool dated rainfall-triggered landslides from the entire Himalayan arc — several hundred of them, roughly nine times our local sample — train on the arc, then **test on Arunachal's own events which the model has never seen.** If it beats our current rule, transfer is proven on held-out ground in the client's own state. If it doesn't, we've lost nothing and gained a measured answer.

> One technical point that makes pooling legitimate: because we normalise rainfall into **percentiles against each location's own history**, the model learns "unusually wet for here" rather than a millimetre number. That travels between the dry western Himalaya and the wet monsoon east; a raw threshold wouldn't.

> **Follow-up →** "Does transfer learning require a neural network?" No — and this is a good detail to have. The simple version is pooling the rows into one model with a region feature and weighting local examples higher. Same benefit, trains in seconds, and you can _measure_ the transfer by dropping the other regions and re-running.


### Q43 — How do you avoid overfitting?  `core`

**Say:** The main defence is how we split train and test, and it's the single most important methodological thing we do. The standard move — shuffle rows, keep eighty percent to train — is **wrong for geographic data** and gives you a beautiful fake result. Neighbouring cells are almost identical, so a random split puts a cell in training and the cell a hundred metres away in testing; the model effectively sees the answer. So we hold out entire regions instead. Our reported scores are lower because of it, and they're real.

> Additional discipline: **the held-out regions were chosen and frozen before any model was trained**, with a fixed random seed and a content hash written to disk. If you pick your test regions after seeing results, you will unconsciously prefer the ones that flatter you and you won't notice yourself doing it.


### Q44 — What is spatial cross-validation? Explain simply.

**Say:** Cut the state into blocks. Train the model on four-fifths of the blocks, then test it on the fifth it has never seen — and rotate through so every block gets its turn as the test set. It answers the question that matters: _would this work in a district we've never studied?_ Random row-splitting answers a much easier question and flatters the result. A lot of published work in this field reports higher numbers using random splits; those aren't comparable to ours, and we say so when benchmarking.


### Q45 — What's your compute setup? Do you need GPUs?

**Say:** Today, no — that's part of the point. The tree models train in minutes on ordinary hardware, and the live app runs on free-tier hosting with a small precomputed data bundle. That's a deliberate architecture: the heavy work is offline, and the thing users touch is light. GPUs come in when the vision and sequence models come in — imagery segmentation over years of satellite data is genuinely GPU work, but it's _offline_ work that produces training data, not something in the live forecast path.

> Good principle to state: **no neural network in the thing that makes predictions; neural networks in the thing that makes training data.** That keeps the live forecast explainable and fast while still getting deep learning's benefit where it counts.


### Q46 — How would you handle deployment at scale — MLOps?

**Say:** The disciplines are already partly in place. Raw data is immutable — never edited once fetched, every file recorded with its source, licence and a checksum. Every processed output has to be reproducible from raw. The next layer, which is on the roadmap, is stamping every published forecast with the exact input versions and code revision that produced it — so "reproduce the forecast you issued last Tuesday" is an answerable question. Then scheduled runs replacing manual ones, and scheduled retraining as the event archive grows.


### Q47 — What about model drift? The climate is changing.  `deep`

**Say:** Real risk, and we treat it as a design constraint rather than a caveat. Two mitigations. First, recalibration is scheduled, not one-time — the rainfall climatology that "unusual for here" is measured against gets refreshed, so the baseline moves with the climate. Second, we score rainfall as a percentile rather than an absolute, which absorbs a gradual shift in the mean automatically. What percentiles _don't_ absorb is a change in the shape of the extremes, and that's exactly why the physics floor stays in place.


### Q48 — What are the actual features the model reads?  `deep`

**Say:** Thirty-four per cell, in groups. **Terrain** — elevation, slope (we use the steepest patch within the cell, not the average, which measurably matters), which way it faces, curvature, a wetness index for how much upslope land drains into it. **Soil** — clay, sand and silt fractions, bulk density and organic carbon, each at three depths. **Geology** — rock unit, distance to the nearest fault line. **Land cover**, because tree roots physically bind soil. **Distances** to river and road — rivers erode the toe of a slope, road cuts slice into hillsides. Plus the dynamic rainfall features on top.


### Q49 — How do you know the model isn't just detecting roads or steep ground?  `deep`

**Say:** We tested for exactly that, because it's the obvious failure mode — landslides get mapped where surveyors can reach, and surveyors reach roads. We removed road distance and re-measured: costs about one percent of accuracy. We removed rock type: almost nothing. We stripped it back to terrain and drainage alone — ten physically interpretable features — and it still reached ninety-eight percent of full performance. And when we check predictions against actual landslides at different distances from roads, they track each other cleanly across every band. It's not a road detector.


### Q50 — What resolution do you model at, and why?

**Say:** Three different numbers and it's important not to confuse them. We _compute_ on a hundred-metre grid — eight point two million cells — because steepness genuinely varies over metres. But the rainfall data has a much coarser natural cell, around eleven kilometres, and that's a hard physical ceiling on how finely the _timing_ can vary. So we _publish_ at the administrative circle, roughly seventeen kilometres, which sits just above the physical skill limit and happens to be a real administrative unit with a name and an officer. Publishing finer would be fake precision.

> Worth saying out loud because people misread the map: **the map has hundred-metre terrain detail and eleven-kilometre weather detail.** Viewers see crisp terrain and assume the weather is that sharp. It isn't, and we label it.


### Q51 — How does the daily run actually work, step by step?

**Say:** Fetch yesterday's observed rainfall and the forecast for the next several days. Convert those into rolling totals — three-day, seven-day, and so on — and turn each into a percentile against that location's own history. Multiply the resulting trigger score by the static susceptibility score for each cell. Aggregate the cells up to reporting units. Join in population and buildings, so it becomes risk rather than just hazard. Publish, and archive the run — which matters because that archive is how you prove skill later.


### Q52 — Can you forecast how big the landslide will be?  `tested, no`

**Say:** No, and we tested both routes rather than assume. Does the rainfall predict the size of what it triggers? Not detectably at our sample size — the effect we saw appears in about three in ten random reshufflings of the same data, so it's noise. Does the terrain predict typical failure size? Also no, and the reason is interesting: **polygon size tracks which survey team drew it far more strongly than it tracks the hillside.** Different teams have different minimum mapping sizes and different habits about splitting or merging adjacent scars. Even a perfect model would be learning survey methodology.

> **Follow-up →** "So what could you offer instead?" Show the _observed_ size distribution of past failures near a searched location — clearly labelled as history, not forecast. It answers the instinct behind the question without inventing a prediction.


---

## 04 · The basics, in plain words

_Fifteen questions covering the words you'll use all evening. **If someone stops you mid-sentence and asks "sorry, what does that actually mean?", the answer is in here.** Read this section last thing before you go in — it's the one that stops you freezing on a simple question._


### Q53 — What actually _is_ a model?

**Say:** A rule-book the computer wrote for itself. We show it thousands of hillsides that collapsed and thousands that didn't, and it works out the pattern: "steep, facing north, this kind of rock, no trees — that combination keeps showing up in the ones that failed." Then when you hand it a new hillside it's never seen, it applies the rule-book and gives it a score. Nobody writes the rules by hand. The computer finds them in the examples.


### Q54 — How does the computer actually learn from past landslides?

**Say:** Think of it like a student doing practice papers. We give it a hillside and hide the answer. It guesses. We show it the real answer. It adjusts. Then it does that half a million times. Each round it gets slightly less wrong. _(That's the "boosting" in gradient-boosted trees — each new little rule-book is built specifically to fix the mistakes the previous ones made.)_

> **Follow-up →** "How do you know it learned instead of memorised?" We hold back entire regions it never sees during practice, then test on those. If it only memorised, it falls apart on unfamiliar ground. Ours doesn't — the score barely moves between regions, and that stability is the actual evidence.


### Q55 — What's the difference between hazard and risk?  `core`

**Say:** Big distinction, and people mix them up constantly. **Hazard** is the dangerous thing itself — this slope is likely to collapse. **Risk** is hazard plus what it lands on. A dangerous slope above an empty valley is high hazard and low risk. The same slope above a school is high hazard and very high risk. Our models produce hazard; we then join in population and buildings to turn it into risk — because an officer with limited resources needs the second one, not the first.


### Q56 — Why can't you just use ChatGPT for this?  `likely`

**Say:** Different tool for a different job. A chat model is brilliant with words — it has read enormous amounts of text. It has never looked at Arunachal's hillsides, it can't measure a slope, and it can't tell you whether last week's rain was unusual for a particular valley. Those are measurement problems, not language problems. Asking a chat model to forecast a landslide is like asking a very well-read person to predict tomorrow's weather from memory.

> **Where language models genuinely do help us:** reading. Decades of road-closure logs, government field reports and news archives all contain dated landslide events buried in prose. Pulling structured records out of written text is exactly what these models are good at — so we use them to _build the training data_, not to make the forecast.


### Q57 — You keep saying "unusual for here" — what does that mean?  `core`

**Say:** It's about comparing a place to its own history instead of to a fixed number. Some parts of this state get four times more rain than others. So 150 mm in three days is an ordinary Tuesday in the wet south and a once-in-a-decade event on the dry northern ridges. If we used one fixed rainfall number statewide, we'd be alarming the south permanently and never warning the north at all.

> **So instead we rank.** For every square we hold twenty-six years of daily rainfall, and we ask: out of all the days this place has ever seen, where does today sit? Top 10%? Top 1%? _(That ranking is called a percentile, computed against that cell's own climatology.)_ That single choice is the main methodological difference between us and a fixed-threshold rainfall alert.


### Q58 — What does "ground truth" mean?

**Say:** What actually happened, confirmed — as opposed to what a model guessed or a satellite estimated. A satellite estimates that 80 mm fell; a rain gauge on the ground _measures_ it. The gauge is ground truth. It matters because you can only grade a model against something you're confident is real, and most of our roadmap is different ways of getting more of it: sensors, drones, field reports, river gauges.


### Q59 — What happens when two of your models disagree?  `deep`

**Say:** Disagreement is information, not a problem. If every model says the same thing, you've learned nothing by having several. Two things happen. The blender has already learned, from past cases, which model tends to be right in that kind of situation, so it leans accordingly. And separately, **strong disagreement is itself worth flagging** — it means this is unusual ground the models read differently, and that's exactly where a human should look rather than trusting any single number.

> There's a version of this that becomes a real product feature: **reporting confidence, not just a score.** "High risk, and all our methods agree" and "high risk, but our methods disagree sharply" are different messages, and an officer deciding whether to close a road deserves to know which one they're holding.


### Q60 — How is the app fast if there are eight million squares?

**Say:** Because it doesn't do the hard work while you wait. All the heavy computation — the terrain, the eight million scores — happens beforehand, and the result is baked into a small file the page just reads. The only thing that happens live is fetching today's rain and doing a quick multiplication. It's the difference between cooking a meal to order and having it prepped: same food, served in seconds.

> **Follow-up →** "Doesn't that limit you?" It does today, and we know exactly how to remove it — move the calculation to a scheduled job that runs every few hours and writes the answer to a file. Then the detail we can afford stops being tied to how long a visitor will wait. That's the single highest-leverage fix on the delivery side.


### Q61 — What if the satellite data doesn't arrive one day?

**Say:** The system keeps working, because we never depend on a live call for anything historical. We hold our own copy of every input we've ever fetched. If today's feed is late, the forecast is less fresh — it isn't broken. And the rule is that raw data is never edited once it lands, so we can always rebuild everything downstream from scratch.


### Q62 — Why does which way a slope faces matter so much?  `good story`

**Say:** This genuinely surprised us — it turned out to be the model's **strongest single clue**, ahead of steepness, which nobody expects. But it makes physical sense in the Himalaya. A north-facing slope gets less sun, so it stays damp longer, holds snow differently, and the rock breaks down differently over decades. Two slopes with identical steepness and identical rock can be in genuinely different condition purely because one faces the sun and one doesn't. _(In the model it's "aspect," split into a north–south and an east–west component.)_

> Good to have ready as an example of **the model finding something we didn't tell it.** We gave it aspect as one column among thirty-four; it worked out on its own that it mattered most.


### Q63 — What's the difference between a forecast and a warning?

**Say:** A forecast is information — "conditions here are dangerous this week." A warning is an instruction — "leave." We produce the first. The second is a government decision, and deliberately so: it involves cost, disruption and public trust, and it belongs with the authority who carries that responsibility. What we owe them is the clearest possible picture and honesty about how sure we are.


### Q64 — What if a landslide happens somewhere you said was safe?  `hard`

**Say:** It will happen, and we've designed around admitting it rather than around avoiding it. Three things matter here. We never label anywhere "safe" — the lowest class is "very low," which is not the same word. Ground we haven't modelled shows as "not assessed," never as low risk. And every miss goes straight into the archive as a training example, so the system learns from exactly the cases that embarrassed it. A forecast that's never wrong isn't a forecast — it's a claim nobody should believe.


### Q65 — How will sensors and satellites work together?  `vision`

**Say:** They cover each other's weaknesses exactly. Satellites see **everywhere** but only roughly, and only from far away. A sensor sees **one slope**, but precisely, continuously, and from the inside. So the satellite layer scans the whole state and says "these forty slopes are the worst"; the sensors go on those forty and watch them properly. And the traffic runs both ways — a rain gauge on the ground tells us how far off the satellite's rainfall estimate is at that spot, so a handful of sensors quietly improves the free statewide layer too.


### Q66 — Why 100-metre squares? Why not smaller?

**Say:** A balance between detail and being able to work at all. At thirty metres you'd have ninety-one million squares and every experiment takes days, which means you try fewer ideas and the project gets worse. At two hundred and fifty metres you smooth away the steep face that actually fails — you'd average a cliff and a meadow into one gentle number. A hundred metres keeps the real slope visible and still fits in memory, so an experiment takes minutes.

> **Important not to confuse three different numbers.** We _compute_ at 100 m. The rainfall data is naturally about 11 km, which is a hard ceiling on how finely the _timing_ can vary. So we _publish_ at the administrative circle — above the physical skill limit, and a real place with a name. Publishing at 100 m would be fake precision.


### Q67 — How do you know the shape of the ground in places nobody's surveyed?

**Say:** Satellites measure it. There's a global elevation map built from radar flown in orbit, accurate to about thirty metres across the whole planet, including terrain no surveyor has ever walked _(a Digital Elevation Model — we use the Copernicus DEM)_. From that one height map you can calculate everything else by geometry: how steep each point is, which way it faces, how curved it is, and where water would flow. That's why a small team can model an entire state — the base measurement of the ground already exists, for free, everywhere.

> **Follow-up →** "Is thirty metres good enough?" For statewide screening, yes. For one specific slope you want much finer, which is what a drone survey gives you — and that's precisely the tier where drones enter the plan.


---

## 05 · Data, and manufacturing the ground truth we don't inherit

_Eighteen questions. The theme a technical listener should walk away with: **we are not just consumers of open data — we have a designed strategy for generating data nobody has.**_


### Q68 — Where does your data come from?

**Say:** Over twenty sources across roughly a dozen categories, all public today. NASA and European satellites for rainfall, elevation and imagery. The Geological Survey of India for rock type and the mapped landslide inventory. ISRO's Bhuvan platform and the state's own space applications centre for more recent landslide surveys. Global soil, land-cover and river-network datasets. Central Water Commission gauges for river levels. Population and building footprints for exposure. Nothing paid, nothing proprietary — deliberately, so the free tier genuinely runs on zero-cost inputs.


### Q69 — How much data are we talking about?

**Say:** Around eight gigabytes of raw source data across roughly ten thousand files, which becomes a processed grid table of about a gigabyte — eight point two million rows, one per hundred-metre cell of the state, thirty-four columns each. Plus a twenty-six-year daily rainfall archive with no gaps. The whole thing then compresses down to a few megabytes for the live app, because the app ships precomputed surfaces rather than doing the heavy work.


### Q70 — What's a "shared grid" and why does it matter so much?

**Say:** The data arrives in wildly incompatible shapes — elevation at thirty metres, soil at two hundred and fifty, rainfall at eleven kilometres, geology as polygons, rivers as lines. You can't feed that to any model. So we pick one grid and force everything onto it, so every row is one place and every column is one measurement about it. Every join in the system uses one key. It sounds mundane; it's the single most consequential engineering decision in the project, because everything downstream is a query against that table.

> Detail worth having: **the cell ID is deliberately readable** — it's row times a hundred thousand plus column, so you can decode any ID by arithmetic. Sequential IDs would hide a bad join silently; this makes one visible instantly.


### Q71 — How do you generate your own training data?  `core`

**Say:** This is the heart of the long-term plan, and it's a loop, not a download. A forecast goes out. What actually happened gets verified — through radar and drone imagery, our own sensor telemetry, crowdsourced field reports. The confirmed outcome becomes a new dated, located event in an archive. That archive retrains the models, which issue the next forecast. So every season the data asset grows on its own, and the models get better because of it rather than because we bought something.

> Feeding into the same archive from the side: **text mining** of road-closure logs, news archives and government investigation reports — decades of dated events sitting in prose that nobody has ever structured.

> **Follow-up →** "Is any of that running?" The forecast-logging piece is the very next thing to build, and it's first for a specific reason — Q72.


### Q72 — Why is forecast logging your top priority?

**Say:** Because it's the only thing on the list that's time-sensitive. An API can be built in any month. Yesterday's forecast is gone forever if nobody wrote it down. Every day without it destroys evidence permanently — and validation is exactly where we're thinnest. It's also the cheapest item on the roadmap: a daily snapshot and an append-only file.


### Q73 — Can you date old landslides from satellite imagery?  `good story`

**Say:** It was our highest-leverage idea and we tested it before building it — which is the part worth hearing. The plan: a scar appears in imagery at a moment in time, so find when each of our forty thousand scars first appeared and every one becomes a dated event. We tested against landslides whose dates we _already knew_ — the principle being, if you can't recover dates you already have, you can't discover dates you don't. Ordinary optical imagery failed hard: eighty-six percent of landslides here happen May to October, which is peak monsoon and peak cloud. **The imagery we need is exactly the imagery hardest to get.** Median date uncertainty came out around two months against the week we need.

> The test cost about twenty minutes and saved roughly two weeks of building something that would have failed only _after_ it was working.

> **Follow-up →** "So it's dead?" For optical. Radar is a different story — Q74.


### Q74 — What about radar instead of optical?  `deep`

**Say:** Radar ignores cloud entirely, so the thing that killed optical doesn't apply. We checked whether the satellite can actually see our slopes often enough — radar looks sideways, so steep terrain can fold over itself or sit in shadow, and we expected that to be fatal. It wasn't: four-to-five day revisit, and over ninety-nine percent of our mapped landslide cells are viewable from at least one orbit direction, because ascending and descending passes look at opposite sides. Detecting a scar _within_ radar is harder — it's a noisy signal and soil moisture mimics change — and that's the piece that needs the deep-learning work.

> **Follow-up →** "So what's blocking it?" A genuinely interesting catch-22: to validate a system that generates dates, you need landslides that are both precisely located _and_ already dated — which is exactly what we lack. The label shortage blocks its own fix. That's why sensors and text-mining matter: they break the loop from outside.


### Q75 — Tell me about the crowdsourcing plan.

**Say:** A field and citizen reporting app: someone photographs a slide or a flooded stretch, it captures location and time automatically, and it lands in a staging area — not straight into the model. Reports get cross-checked against satellite imagery and our own forecast for that day before they're trusted. The design rule is that partner and public data goes through quarantine with its own provenance before joining authoritative data, because one bad feed contaminating the layer everything is built on is very hard to undo.


### Q76 — Drones — what's the role?

**Say:** Repeat high-resolution surveys at the specific sites our model has already flagged. Satellite gives you the whole state at moderate detail; a drone gives you one hillside at centimetre detail, repeatedly, so you can measure change by comparing surveys. It's the middle rung between statewide satellite and a physical sensor bolted to one slope — and it's the practical way to get detailed terrain for a pilot valley without commissioning an expensive aerial survey.


### Q77 — Which government data would move the needle most?

**Say:** Road-closure logs from the state roads department and the border roads organisation. Every landslide that shut a road, with a date, kept for decades for purely operational reasons. Nobody thinks of it as a scientific dataset, which is exactly why it's untapped — it's plausibly hundreds to thousands of dated events for this state. After that: the state space centre's own field-verified landslide survey records, and ground rainfall stations from the meteorological department to correct known satellite bias at high altitude.


### Q78 — How good is your rainfall data, really?  `deep`

**Say:** Good enough, with a known and stated limit. Our historical archive is eleven-kilometre satellite rainfall, twenty-six years, zero gaps. The live forecast currently samples at about thirty-three kilometres, which is a hosting constraint rather than a science one — a public page can't make a visitor wait two minutes for API calls. We measured what that costs and it was inside the noise, which surprised us.

> The reason it survived is worth knowing: **we score percentiles, not millimetres.** Two rainfall sources can disagree on absolute totals and still rank wet days almost identically — and the storms that trigger widespread landsliding are large-scale systems that coarse sampling still sees. What coarse sampling _would_ miss is a single valley-scale cloudburst, and we say so.

> **Follow-up →** "How do you improve it?" Several free steps first — sample more points, and precompute on a schedule instead of on page load, which removes the constraint entirely. Beyond that, India's own national weather modelling centre resolves this terrain far better than any global model, and a state government is exactly the party able to obtain it.


### Q79 — How do you handle provenance and reproducibility?

**Say:** Raw data is append-only and never edited in place — every fetch records its source, licence, URL, fetch date and a checksum. Everything downstream must be reproducible from raw. The training sample itself is content-hashed, so if the hash changes, every number we've reported is void and has to be recomputed. That sounds severe; it's the only way to stop numbers quietly drifting away from the data that produced them.


### Q80 — What data do you hold that others don't?

**Say:** Individually, most inputs are public. The asset is the _assembly_: twenty-plus sources reconciled onto one grid with one key, a gap-free twenty-six-year rainfall history per location, and a set of derived layers — terrain, drainage, distance surfaces — that took real work to build correctly. Plus the negative results: a documented record of what we tested and what didn't work, which saves us from repeating it and would take someone else the same time to rediscover.


### Q81 — How did you validate the data itself?

**Say:** Independent cross-checks, each catching a different class of error. We computed drainage from our own elevation model and checked the lines coincide with the published river network — that one check proves the coordinate system, grid origin, orientation and flow routing are all correct simultaneously. We checked soil texture fractions sum to the right total. We checked our land-cover forest share against published figures. We checked slope against measured relief. Every one of those found or ruled out a real bug class.

> A nice concrete one: our own raw-data viewer surfaced soil bulk density as "107," which looked absurd until we realised the unit was centigrams per cubic centimetre. **Every column in our schema now carries its unit in the name**, so that class of bug is unmissable.


### Q82 — Is there anything wrong with your data you'd admit to?  `be honest`

**Say:** Yes, and it's the interesting kind. Our landslide inventory is survey data, and surveyors map what they can reach — so high-altitude terrain is under-represented. We measured the consequence: the band between two and four thousand metres holds about a fifth of known landslides but receives only about a tenth of our high-risk predictions. That's an operational under-warning exactly where roads are most fragile. It's a _label_ problem, so more model capacity won't fix it — the mitigation is treating thresholds as altitude-dependent and flagging high-altitude corridors for manual review regardless of what the model says.

> Saying this unprompted is a strength, not a weakness. It signals you actually measured your own model's failure modes rather than only its wins.


### Q83 — What's the flood data situation?

**Say:** The static half — which ground is flood-prone — is built from terrain: how high a place sits above the nearest drainage channel, weighted by how big that drainage is, because two metres above a major river and two metres above a hillside creek are not the same statement. The daily half pools rainfall across catchments and routes it downstream. And we recently found two open government sources of real measured river data for this state — decades of level readings on the major rivers with official danger thresholds, plus hundreds of thousands of discharge readings across fourteen smaller rivers. That's the ground truth this side was missing.


### Q84 — Where does the flood model stand honestly?  `be honest`

**Say:** Built and shipping, and the static layer is not yet locally validated — which the product says on its own methodology page. The reason is specific: the only observed flood record we could get for this state turned out to be unusable — over seventy percent of the pixels it marks as flooded sit on slopes steeper than fifteen degrees. Water doesn't pond on a cliff. So it's a rendering artefact, not an observation, and it can't referee anything. The layer rests on standard, well-understood physics and no local evidence yet. It's a well-founded hypothesis, not a measured fact — and the river gauge data we just found is exactly what turns it into one.

> There's a good methodology anecdote here if you want it: an early scoring bug made that unusable reference look like a _strong_ result — because ninety-three percent of cells score identically, and handling those ties wrongly turned pure chance into an apparently excellent number. We caught it and fixed the scoring. **Being the people who found their own too-good-to-be-true result is worth more than the result would have been.**


### Q85 — What's the biggest data risk to the business?

**Say:** Dependency on upstream systems we don't control — satellite feeds, government portals, global models. The mitigation is architectural: archive-first, cache everything, never depend on a live call for anything historical. We hold our own copy of every input, so an outage upstream degrades freshness, not function.


---

## 06 · Sensors, IoT, and the early-warning tier

_Fourteen questions. This is the most "deep tech" part of the vision and the most likely place a hardware-literate mentor probes. The one idea to land: **we don't scatter sensors — our own model earns the shortlist.**_


### Q86 — Are you going to build hardware?  `core`

**Say:** Sensors are a planned tier, yes — but deliberately downstream of the model, not parallel to it. The sequence matters: the satellite layer runs statewide and free, its own output ranks the worst slopes, and then instrumentation goes onto _those specific_ slopes. We never instrument blindly. That's the commercial story too — the free tier pays for itself by telling you where to spend the sensor budget.

> **Follow-up →** "Why not just start with sensors?" Because there are tens of thousands of slopes in this state and you can instrument dozens. Without a ranking layer, sensor placement is guesswork — and a sensor on the wrong slope tells you nothing.


### Q87 — How do sensors actually give early warning? What's the mechanism?  `core`

**Say:** Most slopes don't fail instantly — they **creep first**. Millimetres of movement, accelerating. If you're measuring that movement continuously, you see the acceleration curve, and you can extrapolate it forward to estimate when it reaches failure. That's called the inverse-velocity method and it's operational practice worldwide, not theory. That's how you get from "this area is at risk this week" to "this specific slope, in the next several hours."


### Q88 — Which sensors, specifically?

**Say:** For landslides: **tiltmeters** for ground rotation, **extensometers** measuring a crack widening across a known failure surface, **piezometers** for water pressure in the ground at depth — because saturation is what actually destroys a slope's grip. For floods: **river-stage sensors** for water level. Both hazards benefit from a **tipping-bucket rain gauge** at the site, which does double duty — it's ground truth that lets us correct satellite rainfall locally. And low-cost **seismic nodes** can pick up the vibration signature around a failure.


### Q89 — How do you decide where sensors go?  `core`

**Say:** Three signals stacked: high susceptibility from our model, repeatedly triggered in our own historical record, and people or a road below it — because a landslide in an empty valley is a hazard and one above a village is an emergency. And there's a shortcut that comes free: the government inventory flags several hundred slides as _reactivated_, meaning they've provably moved more than once. Those are repeat offenders by observation, not by model. That's where the first sensors go.


### Q90 — How does a sensor communicate from a valley with no mobile signal?  `deep`

**Say:** Low-power long-range radio — LoRaWAN or narrowband IoT — rather than assuming a cellular tower. The sensor talks to a local gateway over a link that works for kilometres at very low power, and the gateway handles the uplink. Critically, the gateway **buffers**: when connectivity drops, it stores readings and forwards them when the link returns, so a signal gap costs you latency, not data. Solar powered, because there's no mains supply on a hillside.


### Q91 — What runs on the device itself?  `deep`

**Say:** Edge pre-checking. You cannot stream continuous high-frequency readings from a remote hillside over a low-power radio — the bandwidth and the battery both say no. So the device does a first pass locally: is this reading normal for this site? If yes, send a summary. If it looks anomalous, escalate immediately at full resolution. That's the difference between a system that works in real terrain and one that works in a demo.


### Q92 — Sensors get stolen and break. How do you handle that?

**Say:** Realistically, and it's worth being blunt because it's the standard failure mode in this sector — field failure rates of around a quarter are documented in comparable Himalayan deployments, and Arunachal has harder access than most. So the design assumes loss: cheap nodes rather than expensive ones, redundancy at a site rather than a single point, and — crucially — **the satellite layer keeps working when a node dies.** The sensor tier is an enhancement on top of a system that degrades gracefully, not a dependency.


### Q93 — Is there a kind of landslide sensors can't help with?  `be honest`

**Say:** Yes, and we say it plainly rather than let it be discovered. Sensors work on slopes that creep before failing. **Debris flows** — where material liquefies and pours downhill — go from stable to gone in minutes with no measurable precursor. No instrument helps there; rainfall thresholds are all you have. The good news for the offer is that in our own inventory, movement classified as sliding is the large majority here and flows are a minority — so the sensor tier applies to most dangerous slopes in this state, not a fringe. But the caveat goes in writing in any proposal.


### Q94 — How do the sensors improve the satellite model?

**Say:** Three ways, and this is why they're strategic rather than just a product tier. One: a rain gauge on the ground measures what the satellite only estimates, so it **bias-corrects** the satellite locally — and satellite rainfall is known to under-read over high ridges. Two: a sensor that records a slope moving on a specific day produces exactly the thing we're starved of — a **dated event**. Three: continuous readings let us understand the physics between rain and failure at a resolution satellites never see. So sensors feed the free tier, not just the paid one.


### Q95 — What does a site cost?

**Say:** The low-cost approach in this sector puts a monitored site in the region of a lakh, against traditional imported slope instrumentation which runs into crores. That's the whole reason this is viable at state scale rather than for a handful of showcase sites. I'd want to give you a firm number only after we've specified our own build rather than quoting someone else's.

> **Follow-up →** Don't over-commit here. "That's the order of magnitude; our own costing comes with the pilot" is a perfectly good answer.


### Q96 — What's the full capability ladder?  `core`

**Say:** **Free, satellite only** — an area roughly the size of an administrative circle, one to three days ahead. That's live today.

**With government data** — ground rain gauges and river gauges tighten it to village-cluster scale and add short-range nowcasting.

**With instrumentation** — one specific slope, hours ahead, with an estimated time. That's the sensor tier.

Each rung is a real limit of the data at that tier, not a pricing decision — and each has a named thing that lifts it.


### Q97 — Flood sensors — same idea?

**Say:** Same logic, different instrument. River-stage sensors on the catchments our model ranks highest, reporting continuously with both a threshold and a rate-of-rise check — because how _fast_ a river is rising often matters more than its absolute level. And there's a head start: real government gauges already exist and report on some rivers here, including two live stations right in the pilot district we've scoped. So the network starts partly built.


### Q98 — Do you become a hardware company then?

**Say:** No — and that distinction is deliberate. The sensor network is an input to the platform, not the product. Hardware means manufacturing, field installation and maintenance crews, which is a different company shape. The realistic path for us is a small, focused network at ranked sites — possibly partnering for the hardware itself — while the platform stays the thing we own. What we're uniquely good at is knowing _where_ the sensor should go, and that's the part that's hard to copy.


### Q99 — What about GLOF — glacial lake outbursts?

**Say:** Genuinely relevant here and on our list, particularly for the northern high-altitude districts. There are real glacial lakes sitting upstream of populated valleys, and there's a mapped inventory of them available from the state's own agency. It's a distinct hazard from monsoon rain — it's driven by snowmelt and lake dynamics rather than rainfall — which makes it a good demonstration of the platform's core claim: a new hazard attaches to the same grid, the same validation discipline and the same delivery layer without rebuilding anything.


---

## 07 · Proof, honesty, and validation

_Twelve questions. The reason this section exists: **the credible answer is almost always the honest one.** A founder who reports their own misses reads as more trustworthy than one who only reports wins — and technical judges know it._


### Q100 — How accurate is it?  `core`

**Say:** The WHERE model scores about 0.86 on the standard scientific scorecard, measured the hard way — holding out entire regions the model has never seen. The WHEN half scores around 0.77 on the dated events we hold. And there's a practical number that matters more than either: **the top ten percent of terrain by our score contains about seventy percent of all known landslides**, and the top three percent contains about forty percent. That's what an authority actually uses — it means you can concentrate survey and mitigation on a tenth of the terrain and still cover seven in ten failures.

> **Follow-up →** "Is 0.86 good?" Yes — and worth noting that published work often reports above 0.90 using random splits, which leak neighbouring near-identical cells between training and testing. Ours is the honest protocol and the numbers aren't directly comparable. Say that; it lands well.


### Q101 — What does that score mean, in plain terms?

**Say:** Pick a place where a landslide happened and a place where one didn't, at random. The score is the probability the model ranks them the right way round. Fifty percent is a coin flip. Around eighty-six percent means it gets the ordering right roughly six times out of seven.


### Q102 — What's your false alarm rate?  `trap`

**Say:** We deliberately don't quote one, and the reason is honest rather than evasive. An alert day with no recorded landslide might mean we cried wolf — or it might mean a slope failed in an empty valley and nobody wrote it down. Landslides here are heavily under-reported. So any false-alarm number we published would be fiction. What we _can_ measure and do report is alert frequency — a real operational cost — and capture rate against known events.

> This is a strong answer, not a weak one. **"I could give you a number and it would be made up"** reads as rigour to anyone who knows the field.


### Q103 — How do you choose the alert threshold?

**Say:** We don't — the client does, and we put it in writing. Warn more freely and you catch more real events but cry wolf more often; warn conservatively and the reverse. There's no setting that maximises both. We present the trade-off table: at one setting you alert on about eight percent of days and catch around forty percent of known events; loosen it and you alert on nearly a quarter of days and catch over sixty percent. Where to sit is a judgement about the cost of a missed slide versus an ignored warning — that's a policy decision, not a technical parameter.

> The framing line: **the cost of a false alarm is a road crew on standby for a day; the cost of a miss is a bus in a debris flow.**


### Q104 — How far ahead does the warning come?  `core`

**Say:** We tested this specifically, because a scorecard number tells you the model can rank days — it doesn't tell you the signal exists _before_ the slope fails. Measured around our dated events: even five days out, conditions at the failure site are already well above an ordinary monsoon day, and the signal sharpens as the event approaches. The reason is physical — landslides here follow sustained wet spells rather than isolated flash storms, so the ground saturates progressively and the danger builds over days.

> **Follow-up →** Add the caveat unprompted: wet spells are self-correlated, so part of that early signal reflects persistence rather than pure predictive skill. What it genuinely establishes is that **risk is elevated across a multi-day window** — which is how the forecast should be used, not as a single-day pinpoint.


### Q105 — Have you caught a real event live?  `be honest`

**Say:** Not yet, and I won't claim otherwise. We've replayed history hard — running the system over past monsoons to see what it would have said — and it holds up. But a live season with a documented catch is our next milestone, not something we can point to today. That's exactly why forecast logging is the top priority: it's the machinery that turns the next monsoon into evidence.


### Q106 — What's your biggest weakness?

**Say:** Three, and they're all documented in our own methodology pages rather than hidden. One, the timing half rests on far fewer dated events than we'd like — that's the core constraint. Two, the flood static layer has no local validation yet. Three, the model under-warns at high altitude because of survey bias in the training labels. Each has a named, scoped fix in progress, and none of them is a surprise to us.


### Q107 — What experiments have failed?  `good story`

**Say:** Several, deliberately and cheaply. Using survey years as event dates — tested, the timing signal came out at or below chance. Fitting a machine-learning trigger on our small dated set — tested, it lost to the simple rule. Dating scars from optical imagery — killed by monsoon cloud in a twenty-minute test. Detecting scars in radar — the difference between a scar and the hillside around it was too small to work with. Forecasting event magnitude — both routes failed, and the size data turned out to measure the survey team more than the hillside.

> The number worth saying: **closing out all of those cost under five hours of testing and saved roughly a month of building things that would have failed later.** That pattern — cheap gates ahead of expensive builds, every claim tested against answers we already have — is how we work, and it's more valuable than any single result.


### Q108 — Why publish your failures at all?

**Say:** Because the buyer is a government disaster authority, and their entire risk is trusting a number that turns out to be inflated. A vendor who reports their own misses is far more credible than one who reports only successes. It's also self-protective: writing down what didn't work stops us re-running it, and stops an over-claim reaching a client deck. We caught one of our own too-good-to-be-true results that way.


### Q109 — How do you validate against other people's work?

**Say:** We compare against the national geological survey's own susceptibility mapping — but we never _train_ on it, because then we'd just be cloning their model and inheriting its mistakes. Disagreement isn't automatically failure, since theirs is coarser and older, but large disagreement means investigate. Separately we hold back an independent point inventory the model never saw and score against it.

> A detail worth having ready, because it shows discipline: we found that one of our own "independent" checks was actually **circular** — most of those points were centroids of the same landslides in our training data, so scoring them measured recall, not generalisation. We caught it, threw the flattering number away, and report the genuinely independent one instead, which is substantially weaker.


### Q110 — Does your system say "safe" anywhere?

**Say:** Not exactly, and there's a specific rule about it. About fourteen percent of the state is outside the model's domain — glaciers, permanent water, very flat ground. Those render as **"not assessed," never as "low risk,"** because they are completely different claims. A model that never saw a glacier has no business assigning one a number, and putting a reassuring colour on it invites a reviewer to distrust the whole map.


### Q111 — What if you're wrong and someone dies?  `hard`

**Say:** That's the reason for every constraint we've put on ourselves. The product carries an explicit statement that it's advisory and not a substitute for operational safety decisions. We never publish finer than the data supports. We never quote a probability the data can't produce. And the alert threshold is the authority's decision in writing, because it's their risk appetite, not our parameter. The honest position is that this improves on having nothing — the current alternative in most of this state is no forecast at all — while being explicit about what it can't do.


---

## 08 · Scale, roadmap and where it goes

_Twelve questions about the shape of the thing three to five years out._


### Q112 — Can this scale to other states?

**Say:** Structurally yes, and it was built that way on purpose — nothing in the engine hardcodes Arunachal. All the global inputs — satellite terrain, rainfall, soil, land cover — compute identically anywhere on Earth. What doesn't transfer automatically is the _calibration_: a new region needs its own labelled inventory and its own validation before we'd make any claim there. That's a discipline we'd hold to rather than quietly reuse a model trained elsewhere.


### Q113 — What other hazards could plug in?

**Say:** Anything that factors into "where is it possible" times "what's pulling the trigger." Forest fire — fuel and terrain times dryness and wind. Glacial lake outbursts. Earthquake-triggered slope failure, where the trigger is seismic rather than rainfall. Permafrost degradation at altitude. Each one is a new module against the same grid, the same validation discipline and the same delivery layer.


### Q114 — What's the API plan?

**Say:** Two distinct products, deliberately separated. The analysis-ready shelf — the cleaned, aligned, hazard-neutral data — and the model-output shelf, which is our forecasts. Different audiences, different update cadence, different terms. An external consumer wants one or the other, never both. Read-only first, with authentication, rate limits and a versioned contract from day one.

> **Follow-up →** "When?" Deliberately after automated scheduling, not before — an API serving data last refreshed by hand three weeks ago is worse than no API, because the staleness is invisible to whoever's consuming it.


### Q115 — Who would consume that feed?

**Say:** Roads and infrastructure planning, where knowing which corridor is fragile changes maintenance scheduling. Telecom and power operators with assets on unstable terrain. Insurance and risk modelling. Other researchers and agencies who need the aligned base layers rather than our forecasts. And ideally the state's own systems, so a warning surfaces where officers already work rather than in one more separate dashboard.


### Q116 — What's the pilot plan?

**Say:** Tawang district, starting from the Jang valley. Chosen for concrete reasons: small enough to fully instrument on a modest budget, unlike a statewide rollout; it already has more usable local data than most of the state, including two live government river gauges reporting nearby; it's on a border-roads corridor, so on-ground access for installing and maintaining equipment is plausibly better than in remote interior districts; and it carries that second hazard — glacial lake and snowmelt risk — that's worth demonstrating.


### Q117 — Where are you in one year? Three?

**Say:** One year: the loop closed — automated daily runs, every forecast logged and scored against what happened, one instrumented pilot valley producing real ground truth, and a first season of measured performance we can publish. Three years: the deeper model layers running on data that now justifies them, the data feed live with external consumers, multiple hazards on the same spine, and a track record across several monsoons rather than a backtest.


### Q118 — Would you open-source any of it?

**Say:** The methodology is already effectively open — we publish what we did, including what failed, because credibility with a government buyer depends on it. The models and the accumulated event archive are the asset. That's a fairly standard split in this kind of work: transparent method, proprietary data and operations.


### Q119 — What's the hardest thing for someone to copy?

**Say:** Time. Twenty-six years of rainfall history calibrated per location, an inventory reconciled from four different survey sources that genuinely disagree with each other, a documented record of what doesn't work, and — once it's running — an archive of verified local events that only accumulates by operating through monsoons. Someone with more resources could rebuild the pipeline. They can't compress the seasons.


### Q120 — What's the one thing that could kill this?  `hard`

**Say:** If the dated-event problem never gets solved, the timing half stays where it is — useful but capped. That's why we're attacking it from five directions at once rather than betting on any single route. The second risk is slower: a forecast nobody incorporates into their workflow is a website. Which is why the roadmap is heavy on delivery and integration, not just modelling.


### Q121 — Is there an international angle?

**Say:** The physics doesn't stop at a border, and neither does the data — everything we use is global. Nepal, Bhutan and the wider Himalayan belt have the same problem with less coverage than India. But we'd be honest that each region needs its own validation before we'd claim anything there. India first, and specifically the northeast, where the gap is largest.


### Q122 — What's the climate change angle?

**Say:** Directly relevant. Extreme rainfall events are getting more intense in this region, and slope failure responds to intensity rather than annual totals. That does two things: it increases the value of a forecasting layer, and it degrades any model calibrated once and left alone — which is why scheduled recalibration is in the architecture rather than being an afterthought. Longer term, the same platform is the natural place to run forward-looking risk assessment, not just next-week forecasting.


### Q123 — What's the technical milestone you're most focused on right now?

**Say:** Closing the loop — automated daily runs plus forecast logging, so that from this monsoon onward every forecast becomes a permanent piece of evidence. Everything else on the roadmap gets easier once that's running, because the fundamental constraint on this whole problem is dated local events, and that's the machine that manufactures them continuously.


---

## 09 · Sharp questions

_Eleven questions designed to test you rather than learn from you. In every case the answer is calm and specific — never defensive._


### Q124 — "Isn't this just a susceptibility map with weather bolted on?"

**Say:** That's the version most vendors sell and it's exactly what we designed against. The difference is that our rainfall isn't a static average baked into the map — it's a separate, daily, per-location signal measured against that location's own twenty-six-year history. A static map says four thousand slopes are dangerous, which was equally true last year. You can't evacuate anyone off that. Ours changes every morning and tells you which of them are primed _this week_.


### Q125 — "Google or ISRO could build this tomorrow."

**Say:** They could build the pipeline. They can't shortcut local calibration or local validation, and historically they haven't — global flood and landslide models exist and they're too coarse to act on for a district officer here, which is precisely the gap. The parts that are hard are the parts that are local: reconciling four disagreeing survey inventories, knowing that the government's own flood reference layer is unusable and why, knowing which state office holds the road-closure logs. That's not compute.


### Q126 — "Why would a government trust a startup with this?"

**Say:** They shouldn't, on trust. They should on evidence — which is why every number we publish is measured under a deliberately harsh protocol, why we publish our failures, and why the alert threshold is their decision in writing rather than our parameter. The realistic path is exactly the one other groups in this space took: a small pilot, a documented result, then a wider relationship. It's earned over seasons, not claimed in a pitch.


### Q127 — "You said you barely have dated data — so isn't your forecast guesswork?"  `hard`

**Say:** Fair challenge, and the distinction matters. The _where_ half rests on nearly forty thousand mapped local landslides — that's abundant, and it's the half that does the geographic work. The _when_ half rests on established rainfall physics, calibrated per location against decades of history, and validated against every dated event we have. It's not fitted on a small sample precisely _because_ the sample is small — we tested that and fitting made it worse. So it's not guesswork; it's a deliberately conservative construction that we can measure and explain, with a clear path to a learned model once the data justifies it.


### Q128 — "0.86 doesn't sound that impressive."

**Say:** It depends entirely on how it was measured, which is the real question. Published models in this field frequently report above 0.90 — using random splits that put a cell in training and the cell a hundred metres away in testing, which leaks the answer. Ours holds out entire regions the model has never seen. If we used the flattering protocol our number would be higher and would mean less. And the operationally meaningful figure is that a tenth of the terrain contains seven in ten known landslides.


### Q129 — "How is this different from what the meteorological department already issues?"

**Say:** They forecast _rain_. We forecast the _consequence_ — and the difference is the whole product. Two hundred millimetres on the Assam plains does nothing; the same rain on a West Kameng hillside is lethal. A rainfall warning tells everyone in a district the same thing; ours tells you which slopes in that district are actually loaded, because it multiplies the weather by the terrain. We consume weather forecasts as an input, we're not competing with them.


### Q130 — "Isn't this just a wrapper around free APIs?"

**Say:** The inputs are public — deliberately, so the base tier costs nothing to run. What's ours is everything between the input and the output: eight million cells of derived terrain and drainage that had to be computed and independently checked, a model trained on a reconciled inventory from four disagreeing sources, per-location rainfall climatology across twenty-six years, and a validation protocol that makes our own numbers look worse. Anyone can call the same APIs. The gap between calling them and producing a defensible daily forecast is the entire project.


### Q131 — "Small team — can you actually execute?"

**Say:** The evidence is what's already built: over twenty data sources ingested, a state-scale grid, two hazard models, and a live app — with the discipline to kill five of our own ideas cheaply rather than build them. The way we work is deliberately gate-first: test the risky assumption in hours before committing weeks. That's how a small team stays ahead of its own scope.


### Q132 — "What don't you know?"

**Say:** How the system performs in a live season — we've backtested, we haven't operated through a monsoon with the loop closed. Whether the flood static layer holds up against the river gauge records we've just found. And how much of our high-altitude under-warning is model versus label bias — we've measured it but not separated the causes. All three are answerable, and all three are answered by operating, not by more modelling.


### Q133 — "Give me the one number that convinces me."

**Say:** Ten percent of the state contains seventy percent of every landslide anyone has ever mapped there. That's what the model concentrates — and it means an authority can put its survey budget, its mitigation work and its sensors on a tenth of the terrain and still cover seven failures in ten.


### Q134 — "What's the most interesting thing you learned building this?"

**Say:** **The tie bug.** A validation score came back at 0.879 and looked excellent. It was chance. Ninety-three percent of cells scored identically, and mishandling those ties turned a coin flip into an apparently strong result. We found it ourselves.

**The negatives finding.** Standard practice says careful negative sampling should meaningfully improve your score. We tested it here and the score didn't move — because this terrain has almost no flat ground to contaminate the sample. We kept the practice anyway, for reasons the accuracy metric structurally cannot see.

**Simple beat complex.** We fitted a proper model for the timing half and it lost to a transparent rule. At small sample sizes, fitting adds variance without signal — so we shipped the simpler thing, which is both more accurate and easier to defend.


---

## 10 · If you open the live app

_You have something real to show. Use it — inside these lines._


**DO**

- Open the Forecast view, search any Arunachal town, show today plus the next seven days
- Switch the map layers — Hazard, Rain trigger, Susceptibility — if asked "what's driving this today"
- Show the Statewide view for the district-level picture; that's the operations view
- Open the Methodology / Validation page if someone technical pushes. **The honest numbers and the stated limits are already written there** — "it's all on the page" is a genuinely strong answer
- Point out that grey means "not assessed," not "safe" — it's a small detail that signals rigour

**DON'T**

- Don't search outside Arunachal — not built for it yet
- Don't imply it pinpoints one house or one hour
- Don't let the flood map imply the same proof level as landslide
- Don't read a score aloud as a percentage chance — it's a relative index
- Don't promise a feature you saw in this document as shipping today

---

## 11 · Land mines

_Short and specific, so you catch yourself mid-sentence._

- **Never invent an accuracy percentage.** No "99% accurate." Nobody has that for this problem and a technical person will ask what it means.
- **Never claim a real-time save.** "Tested hard against history" — not "we caught one."
- **Never quote a false alarm rate.** Explain why it can't be measured. That answer is stronger.
- **Never call a score a probability.** It's a relative index. "0.8" is not "80% chance."
- **Never claim house-level or hour-level precision at the free tier.** Area, over days. The sensor tier is what changes that.
- **Never say the flood model is validated.** The small-stream half isn't yet, and it's better coming from you.
- **Never say any data licence or partnership is "secured."** If it comes up: "in progress," and move on.
- **Never present a planned model layer as running today.** "That's where it's going" is honest and loses you nothing.

---

## 12 · Numbers worth remembering

_Round them when speaking. Nobody expects decimal places out loud — and vagueness on a number you half-remember sounds worse than rounding cleanly._

- **~40,000** — mapped historical landslides _inside Arunachal_ — the strength of the WHERE half
- **8.2 million** — grid cells at 100 m covering the state — _the shared spine_
- **34** — features measured per cell
- **26 years** — of daily rainfall history, zero gaps — _what "unusual for here" is measured against_
- **~0.86** — WHERE model score, held-out regions — _the headline accuracy_
- **~0.77** — WHEN model score on dated events
- **10% → 70%** — a tenth of the terrain holds seven in ten known landslides — _the operational claim_
- **3% → 40%** — the top class is 3% of area and holds 40% of slides
- **3–5 days** — signal is elevated before an event — _why a 7-day product is legitimate_
- **~11 km** — rainfall resolution — the real physical ceiling on timing precision
- **~29°** — median slope across the whole state — _why "just detect steepness" doesn't work here_
- **20+** — data sources ingested
- **<5 hours** — total cost of testing and killing five ideas that would have taken a month to build

---

## 13 · Words, translated

_If someone uses jargon at you, here's the plain swap — and the version to say back._

- **Susceptibility** — Which slopes are physically capable of failing — the "where." Barely changes year to year. A loaded gun.
- **Trigger** — What pulls the trigger — almost always rain. The "when." Changes daily.
- **AUC** — The report-card score. Pick a failed place and a safe place at random; AUC is the chance the model ranks them correctly. 0.5 is a coin flip.
- **Gradient boosting** — The main model. Builds many small if-then rulebooks, each fixing the last one's mistakes. Best-in-class on tables; explains itself.
- **SHAP** — Breaks one prediction into contributions — "0.81 because slope contributed this much, rock type this much."
- **Ensemble / stacking** — Several models scoring the same thing, with a second model learning which to trust when.
- **Spatial CV** — Testing on whole held-out _regions_, not random rows, so neighbouring cells can't leak the answer.
- **Presence-only** — Our records say where things happened, never where they didn't. Why we report ranks, not probabilities.
- **Antecedent rainfall** — How much already fell over previous days. Often a better predictor than today's rain.
- **Inverse velocity** — A slope creeps, the creep accelerates, you extrapolate the curve to estimate failure time. How sensors buy hours.
- **HAND** — Height above nearest drainage. How high you sit above the nearest river — the backbone of the flood layer.
- **SAR / radar** — Satellite radar. Sees through cloud, which optical can't — critical during a monsoon.
- **Backtest** — Replaying past years through the model to see what it would have said.
- **POD / FAR** — Share of real events caught / share of warnings that were wrong. You cannot maximise both.
- **Circle** — The administrative unit we publish at — roughly 17 km, a real place with an officer and a phone number.
- **Weak supervision** — Learning from imprecise labels — "sometime in 2017" rather than a date. We tested it here and it didn't work.

---

_Deliberately not covered: funding use beyond the technical roadmap, revenue model, market sizing, team structure. If those come up, answer naturally in the moment — this page won't have it pre-written. Competitor comparisons are also out of scope here; nobody from that world is expected in the room._
