# Blockland — the story world for the learning path

The game every phase page uses, so the dots join from Level 0 to Level 7. Chosen by the
user on 2026-11-04: a **video-game world**, simple English (a 12-year-old should follow
it), a 🎮 box beside every fact, a **Pixel asks** mini quiz per section, simple drawings,
and **word cards** for grown-up words.

## The rules for writing it

- **The fact stays.** Never replace a real fact with the story. Every 🎮 box ends with a
  **🔁 Real version** line, or sits right beside the fact it explains.
- **One meaning per game word.** Once a thing has a game name, it keeps it in every level
  (table below). Add new names here first, then use them.
- **Simple English.** Short sentences, everyday things (cricket, cakes, LEGO, school exams).
  No Hindi words.
- **Numbers stay real.** A game line may round a number but never change it. Check each
  number against the code or data before it goes on a page (see the memory rule
  "verify before writing learning content").
- **Honesty is part of the game.** Locked things are "locked", a beta is "beta", and the
  boss fight (a live monsoon) hasn't happened yet.

## The cast

| Game name | Real thing |
|---|---|
| 🧑‍🔧 **You, the Builder** | the CTO: keeps the world running and explains it to anyone |
| 🤖 **Pixel** | your helper bot: asks the question at the end of every section |
| 🌍 **Blockland** | the state on our map: Arunachal (world 1), Assam (world 2) |
| 🧱 **a block** | one 100 m × 100 m square (about a football field); Arunachal has 8.2 million |
| 🎒 **a block's inventory** | the 34 facts per square |
| 📔 **the rain diary** | 26 years of daily rain for every place |
| ⚙️ **the World Engine** | the Data Backbone |
| 🛡️ **the Guardians** | the modules: SlideSense (hills), FloodSense (water), SoilSense (soil, in Assam) |
| 🔒 **the empty slot** | "next hazard?" |
| 🎁 **loot chests** | data sources (46 opened, 20 more spotted = "ready") |
| 🏛️ **the Guilds** | the agencies that own chests: Rock Guild = GSI, River Guild = CWC, Sky Guild = IMD, Sky-Eye Guild = ISRO / APSAC / satellites |
| 🎁→🔐→🧲→📦→🛡️ | the pipeline: **loot run** (collect) → **the Vault** (keep) → **snap to grid** (line up) → **two chests** (shelves) → the **Guardians** use it (serve) |
| 📚 **the Sky-Eye Guild's map library** | APSSDI: the state's map-sharing portal (a library lends scrolls; the World Engine is a workshop that builds with them) |
| 🎨 **ten kinds of loot** | the ten standard data categories: topographic, geological, pedological, land cover, hydrological, meteorological, seismic, cryospheric, hazard events, exposure |
| 🏷️ **the tag / the fingerprint** | the record per file (source, terms, link, date) and its checksum |
| 📦 **Materials chest / Answers chest** | shelf 1 / shelf 2 |
| 📖 **the Prophecy Book** | the forecast log (written before the day) |
| 🏆 **the Scoreboard** | grading the forecasts after the day |
| ⭐ **XP** | what really happened, coming back as new examples |
| 🧨 **a TNT block** | WHERE: weak ground (susceptibility) |
| ⚡ **a spark** | WHEN: the trigger (rain, a rising river) |
| 📊 **the leaderboard** | a rank (landslide levels), not a percent |
| 🎲 **honest dice** | a calibrated chance ("20% means 20%") |
| 🌧️ **the Monsoon** | the season boss, June to September; the "boss fight" = a live monsoon test |
| 👾 **Glitches** | bad data (e.g. the flood map with water on cliffs, a broken gauge reading) |
| ☁️ **Cloud Curtain** | monsoon cloud that blinds optical satellites (Level 1, 4) |
| 🏋️ **the training gym / the surprise exam** | training a model / testing on unseen ground |
| ⏰ **the 8:30 alarm** | the daily cloud run (Modal, Mumbai) |
| 🚪 **the side door** | the open feed / API (locked) |
| 🔓 / 🔶 / 🔒 | built / partly built / planned |
| 🚫 **cheat codes** | phrases that lose an expert's trust |
| 🏃 **the speedrun** | the 3-minute story |
| 🩹 **patch notes** | old docs and what changed since |
| ⚔️ **the Council of Guilds** | the meeting room (Level 7): APSAC, GSI, CWC |
| 🧑‍🏫 **the seven teachers** (Level 1) | the seven fields: Rock (geology), Storm (rain trigger), Water (hydrology), River (river forecasting), Soil (erosion), Sky-Eye (remote sensing), Exam (model testing) |
| 🧒 **Super simple** line | the one-sentence kid version at the top of each section (from Level 1 on) |
| 🤼 **the tug of war** | factor of safety: grip ÷ pull |
| 💧 **the wet-floor slip** | pore pressure |
| 🔔 **the toast alarm** | the classic rainfall threshold line (rings on most monsoon days) |
| 📔 **checking the rain diary** | a percentile against the place's own rain history |
| 💦 **the sponge that never dries** | antecedent wetness (soil 89–95% full Apr–Sep). Don't use the 🧽 emoji: it shows as a box on Windows |
| ⚪ **the marble run / marble count** | flow direction (D8) / flow accumulation |
| ⬆️ **steps above the river** | HAND |
| 📏 **the height stick** + 🟥 red line | a river gauge + its danger level |
| 🛁 **bathtub vs cup** | lead time: big rivers vs hill streams |
| 🍰 **the five-ingredient recipe** | RUSLE (A = R·K·LS·C·P) |
| 📡 Echo-Eye · 📷 Camera-Eye · 🌧️ Rain-Counter · 🏔️ Height-Mapper | Sentinel-1 radar · Sentinel-2 optical · IMERG · Copernicus DEM |
| 🏋️ **the surprise exam** · 👀 **copying from your twin** | block cross-validation · leakage from a random split |
| 📏 **the tallest of 97** | the percentile-max trap |
| 🎯 **the usual** | base rate |
| 🎮 **other players** | other systems in the field (WHO_ELSE_LANDSCAPE.md): IIT Mandi, Google, GSI's own forecast centre… |

## The levels

| Level | Phase page | Title | The story beat |
|---|---|---|---|
| 0 | phase-0-big-picture | **Welcome to Blockland** | the world, the engine, the guardians, TNT × spark, what's locked |
| 1 | phase-1-science | **World physics** | why blocks fall (grip vs pull, water makes soil slippery), where water goes, the Cloud Curtain |
| 2 | phase-2-data-backbone | **The great loot run** | the 46 chests, the Guilds, the snap-to-grid tricks, one block's full inventory |
| 3 | phase-3-slidesense | **Guardian 1: SlideSense's training** | learning from ~37,000 old craters; the missing calendar pages (~90 dated slides); the surprise exam; the leaderboard |
| 4 | phase-4-floodsense | **Guardian 2: River watch** | height sticks, the gauge Glitch (spike filter), honest dice, the level line |
| 5 | phase-5-soilsense | **The second world: Assam** | soil washing off like a sandcastle in rain; the fix-it-first list of 703 valleys |
| 6 | phase-6-app-ops | **The server that wakes at 8:30** | the daily run, the Prophecy Book, packing the small backpack, what happens when it breaks |
| 7 | phase-7-defend | **The Council of Guilds** | hard questions, other players, cheat codes, why the Guilds should let you play |

## Word cards so far (Level 0)

Data Backbone · module · pipeline · grid square · layer · raw data · fingerprint
(checksum) · susceptibility · trigger · forecast · rank vs chance · calibrated · AUC ·
unseen ground (validation) · the loop (grading) · API / feed.

## Word cards (Level 1, done 5 Nov 2026)

Factor of safety · pore pressure · antecedent rain · rainfall threshold · percentile ·
flow accumulation · catchment · HAND · danger level · lead time · RUSLE · backscatter ·
base rate · leakage · out of distribution · pre-registration, plus six back from Level 0.

## Level 2 names and word cards (done 5 Nov 2026)

New names: 🎒 the backpack (the 34 facts) · chest colours 🟢/🟠/🔴 (licence: open / research-only / ask first) · a **dashed chest** = a "ready" source (spotted, not opened) · the six **gamerules** (DATA_CONTRACT's frozen choices) · a **cinema seat number** (cell ID) · the corner stone (the fixed origin) · three snapping tricks: **pouring** (raster), **"which country am I in?"** (polygon), **"how far to the nearest road?"** (distance) · **rain slabs** and the slab note (the IMERG index) · **open world / Guild quests / craft your own** (Free / Ask / Paid) · **painted-on locks** (portals that look closed) · the **Glitch scanner** (checks before trusting) · the small backpack (the ~16 MB app bundle).

Word cards: geospatial · source · held vs ready · provenance · licence · projection (UTM) · cell ID · raster vs vector · resample · point in polygon · distance to feature · feature table · rain index · SDI · bundle · REGION switch · Free/Ask/Paid, plus five back from Level 0.

## Level 3 names and word cards (done 5 Nov 2026)

New names: 🕳️ **the crater collection** (the merged landslide inventory) · 📅 **the missing calendar pages** (only ~90 day-dated slides) · **no all-clear stamps** (presence-only data) · **quiet blocks** and **the 500 m ring** (negatives and their buffer) · **cracked eggs** (unrecorded slides picked as negatives) · **lots of little 20-Questions games** (gradient-boosted trees) · **the five surprise exams** and **the app's Guardian** (fold models vs the full model) · **which clues mattered** (SHAP) · **the take-out test** (ablation) · **search a tenth, find seven in ten** (lift) · **the blind spot up high** (survey bias) · **not yesterday's exam** (independent validation) · **another player's map** (GSI's national map) · **spark strength** (rain bands) · **five boxes** (levels) · **replay mode** (backtest) · **the alarm knob** (alert threshold) · **silent valleys** (why no false-alarm rate) · **the locked doors** and **the circle** (dead ends) · **the honest label on the box** (limits card).

Two different "× the usual" figures, never mix them: the TNT map alone (High ground holds 4.4× its share of craters, Very High 13.4×) vs the forecast levels (TNT × spark, place-days: 0.2×, 1×, 2×, 3×, 10×).

Word cards: inventory · presence-only · negative sampling · buffer · domain mask · gradient-boosted trees · fold · full model · SHAP · ablation · lift · survey bias · independent validation · times the usual · backtest · alert threshold · capture rate · false alarm rate, plus five back from earlier levels.

## Level 4 names and word cards (done 5 Nov 2026)

New names: **three jars, three badges** (FloodSense's ✔ river chance / ≈ near-here outlook / ◆ if a flood comes) · **the witnessed flood diary** and its three witnesses (radar test, Global Flood Database, gauge crossing) · **a fair witness** (specificity on known dry dates) · **the honest-dice jars** (reliability table) · **two kinds of red line** (CWC danger vs own wettest 2%) · **the dotted footsteps**, **the shaded band** and **the lazy guess** (level line, 80% range, persistence) · **the 97 m Glitch** and **the three-pass Glitch scanner** (spike filter) · **the river sitting on the line** and **no more rerolls** (high-river fault, no eighth design) · **≈ the rough guess** (near-here, approximate) · **five level-ups** (the timing staircase) · **the boss fight hasn't started** (no crossing logged yet).

Near-here numbers to use (snapshot, 4 Nov): ranking ~0.90; recorded floods ~1.5× what it said where floods are on record, ~2.1× where none are; at 10%+ it said 18%, 10% happened. The older "1.3–6×, ~89 in 100" is out of date.

Word cards: gauge · danger level · own 2% line · reliability diagram · hit rate · success ratio · onset · verified record · specificity · conditional probability · level forecast · persistence baseline · prediction interval · spike filter · approximate, plus five back from earlier levels.

## Level 7 (done 5 Nov 2026; Levels 5 and 6 skipped at the user's request)

New names: **the Council of Guilds** with **the Mayor** (APSDMA) at the table · **six safe squares** (the six fallback lines) · **the three chests** (say freely / only if asked / keep) · **the recipe stays in the kitchen** · **every lock has a key** (Free / Ask / Paid; physics locks have none) · **🚫 cheat codes** (never-say phrases) · **the boss rush** (the grilling drill) · **the four checks** (whole state daily? days ahead? score shown? one base, many hazards?) · **the next update: the panel and the referee** (ensemble plan) · **house rules** (decide before the meeting) · **the final boss: the mock Council**. New other players: NDEM, India-WRIS, ICIMOD, Early Warnings for All, Moody's RMS, Fathom, Jupiter, private weather companies.

Emoji that show as boxes on Windows 10, so don't use them: 🫨 🧽 🪨 🪜 🪢 🧍. Each later level adds its own
and may show an old card again ("back from Level 0").
