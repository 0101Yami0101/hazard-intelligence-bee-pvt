# The Data Backbone — the script

## Slide 1 · Title

Thank you for having us. We are BEE Solutions.

What I want to show you today is not one more app. It is the backbone we are building underneath the apps.

Let me tell you how we got here. We set out to build one thing: a landslide map for Arunachal Pradesh. And while building it, we ran into two things that changed our plan.

1. The data that modern AI needs for a problem like this already exists for Arunachal. But it is scattered. It comes in different shapes, sizes and formats. So every project starts from zero.
2. Every hazard is, underneath, the same question. Where can it happen, and when? And both can be answered from much the same set of data.

Put those two together, and you stop building an app. You start building what goes under all of them. Give us about twelve minutes, and you will see it running.

## Slide 2 · The problem

Take the first of those two. It may surprise you, but everything you need to see a landslide or a flood coming already exists. The height of the ground. The soil. The rock. The rain. The rivers, and the gauges on them. All of it has been measured.

So why is it so hard to use? Look at the shapes it comes in. One source gives a reading every 30 metres. Another, every 11 kilometres. One is outlines, one is lines, one is single dots on a map. It sits with a dozen agencies, each in its own format. It is a jigsaw where every piece was cut by a different hand.

So every team runs into the same four walls.

1. The data is in pieces.
2. Every project starts from zero. Months go into lining things up, one map is published, and the work is thrown away.
3. That map goes stale. The ground stays where it is, but rain and rivers change every single day.
4. The one that bothers us most: nobody keeps score. A forecast is made, and no one writes it down and checks it afterwards.

That is why this field is full of static maps, one-off studies, and pilots that never grow.

## Slide 3 · The idea

That is what led us to the idea, and it fits in one line. Do the hard part once.

- **Collect** every useful source.
- **Check** each one, before we trust it.
- **Line up** all of it on one shared map.
- **Keep current** day after day.

Here is a picture to hold on to. Imagine the whole state cut into squares, each about the size of a football field. There are 8.2 million of them. Every source we bring in becomes one more layer, laid over those same squares. So pick any square of ground, anywhere in the state, and you can read straight down through the layers and know everything about it: how steep it is, what the soil is, how much rain has fallen.

And once that exists, anything can be built on top.

## Slide 4 · How it works

How does it work? Follow it from left to right. It is five steps.

1. **Collect:** We fetch every source, and the weather every single day.
2. **Keep:** The original file is stored untouched, with a note of where it came from, so nothing is ever lost.
3. **Line up:** Each one is fitted to the shared map.
4. **Shelve:** There are two shelves: one for ready-to-use data, one for the forecasts.
5. **Serve:** Products simply read from those shelves.

Now look at the line underneath, because it matters most. Every forecast is written down before the day, and checked after it. What really happened flows back in as new data. The system keeps its own scorecard.

Today that means:

- **29** sources lined up.
- **8.2 million** squares on the shared map.
- **26 years** of daily rain, for every place in the state.

## Slide 5 · Rules we keep in mind

Why should anyone trust what comes out? Because of the rules we keep in mind while we build it. These are the main ones.

- **One map for everything:** So two products can never disagree about where a place is.
- **Keep the original:** So any number on any screen can be traced back to where it came from.
- **Check before trusting:** Even official data can be wrong, and we have caught it.
- **No hazard built in:** Nothing in the backbone is tied to one hazard; each product brings its own question.
- **Two shelves:** Someone planning a road wants the base layers. An officer on duty wants a forecast.
- **Close the loop:** Every forecast is graded.
- **Test on ground it has never seen:** A forecast is judged only on places it was not shown while it was being built.
- **Label every number:** Each number on screen says what it is: a forecast, a measurement or a record.
- **Say so when unsure:** Where the data cannot support an answer, it says so instead of guessing.

## Slide 6 · A product is a question

So if the backbone is the foundation, what is a product? A product is simply a question asked of the backbone.

Remember the second thing we learned? Every hazard asks a question of the same shape.

- **Where** can it happen? That is the ground, and the ground barely changes.
- **When** is something setting it off? That is rain and rivers, and they change every day.

Where, times when.

- **Landslides:** Weak ground, times rain that is unusual for that place.
- **Floods:** Ground that water can reach, times rain upstream and the level of the river.

The backbone already holds both halves. The product only has to bring the question.

## Slide 7 · Same layers, reused

And this is where it pays off. Down the left are the backbone's layers. A filled dot means a product uses that layer today.

- **Landslides, first:** It needed nearly all of the layers. That was the long, hard build.
- **Floods, second:** It reused those same layers and added just two files of its own. Two. One rain fetch now feeds both.
- **Soil erosion, next:** The hollow dots are planned, and you can already see that most of what it needs is sitting there, waiting.

That is what we mean by doing the hard part once.

## Slide 8 · Running today

Everything I have said so far could be a plan on paper. It is not. It is running today, and it has a name: SlopeSense, our hazard intelligence platform.

WITH THE APP: Let me show you.

WITHOUT THE APP: These next screens come straight from the app, taken on 10 October. First the backbone itself: every source it draws from, on record, and every layer on one map. Then the two products built on it.

## Slide 9 · SlideSense

The first product on the backbone is SlideSense, our landslide forecast.

- **What it asks:** Where is the ground weak, and is the rain unusual for that place?
- **What it gives:** Pick any town, any stretch of road, and it gives you a seven-day outlook, on a map in five levels from very low to very high.
- **How to read it:** "High" means something very simple: look here first.

Now look at the box at the bottom. Ground shape, soil, rock types, land cover, rain. Every single thing it reads was already in the backbone.

## Slide 10 · FloodSense

The second product is FloodSense, our flood forecast. Same backbone. Only the question is new.

- **What it asks:** Can water reach this ground, and are the rain and the river rising?
- **What it gives:** A seven-day flood outlook for any place, and it follows the river gauges along its own rivers.
- **How it runs:** Nobody has to press a button: it runs by itself, every morning.
- **Its record:** Look at the small panel: every forecast written down, then checked against what the real river did.

Remember the line under the pipeline? This is that loop, working.

And once again, the box at the bottom. Nearly everything it reads was already there.

## Slide 11 · What else

So what else can stand on it? We see three directions.

- **More hazards:** Anything that has a where and a when. Soil erosion is next; after that, forest fire, riverbank erosion, drought.
- **More places:** The satellite inputs cover the whole world, so the same steps can run anywhere. Each new state brings its own local records and its own checking.
- **More users:** Of the data itself: road planners, power and telecom companies, insurers, researchers, the state's own systems.

Let me be straight about the dashed ones. That last group is planned, through an open feed. It is not there yet.

## Slide 12 · Stronger with time

There is one more thing, and it may be the most important. This gets stronger with time, in two ways.

1. **The loop:** Every forecast, once it has been graded, becomes a dated, located example that did not exist anywhere before. Code can be copied in a week. Seasons of checked local history cannot be copied at all.
2. **The data can climb:** In three steps.
   - **Free, today:** It runs on free, open data, and it tells you about an area, days ahead.
   - **Ask, next:** This step costs letters, not money: records that offices already hold would make it finer and faster.
   - **Paid, on chosen spots:** Our own sensors and surveys: one slope, one stretch of river, hours ahead.

And every step up sharpens every product at once, because they all read from the same backbone.

## Slide 13 · Close

So if you keep one picture from today, keep this one. An app is a vehicle. The backbone is the road. We are building the road, and we are running the first two vehicles on it to show that it carries weight.

What comes next for us:

1. More hazards and more places, on the same backbone.
2. Every forecast checked, and the whole pipeline running by itself.
3. An open feed, for others to build on.

And this is where you come in.

- **A hazard** that worries you.
- **A place** you are responsible for.
- **Records** sitting in a cabinet.

That is exactly where we would like to begin. Thank you. We would be glad to take your questions.
