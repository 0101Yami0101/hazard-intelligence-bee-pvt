# CEO briefing — next steps for the Jang/Tawang pilot

**Purpose of this doc:** a plain-language reference for answering CEO
questions about what comes next, for both products, starting at the pilot
site. Not a technical spec — see `PILOT_TAWANG.md`, `FLOOD_WHEN_PILOT_PLAN.md`,
`PARKED_HIMALAYAN_FLOOD_WHERE.md` and `DATA_VERIFICATION.md` for the full
detail behind every claim here.

**One-paragraph version, if there's only two minutes:** We've already found
and used essentially every free data source available for both hazards,
statewide. What's left needs either a relationship (a letter or call to a
government office) or a budget line (sensors, a terrain survey, better
imagery) — and we already know exactly which ask unlocks what. Jang/Tawang
is the right place to spend that next round of effort: it's small enough to
fully fund, already has more local data than most of the state, and lets us
prove a second hazard type (glacial lake floods) the rest of the state
doesn't have.

---

## Where we are today

Both products already work and already produce real output, statewide,
for free:

- **SlideSense** (landslides): live, gives a susceptibility score for any
  point in Arunachal Pradesh, with a daily rain-driven trigger on top.
- **FloodSense** (floods): both halves are built and joined into one daily
  forecast. One half answers "when will a river likely flood"; the other
  answers "which ground goes underwater if it does". *(Updated 22 Sept 2026.)*
  - It runs by itself every morning on live rain.
  - At the state's 32 river gauges it also reads the river's own latest
    water level. That gives a real, checked chance that each river reaches
    danger level over the next few days.
  - Every forecast is written down on the day and graded against what the
    river actually did.

The honest milestone to report isn't "we found some more data" — it's that
we've now systematically exhausted the free tier. Every remaining gap
needs either a government relationship or money.

---

## Why Jang and Tawang, specifically

- **Small enough to fully instrument on a real budget** — not a
  statewide-scale ask.
- **Already ahead of the rest of the state on local data**, with zero
  formal request needed to get there: two real, live government river
  gauges sit right in this valley, and we've already directly checked our
  satellite method against 12 real historical flood dates specific to
  this exact valley.
- **A second, genuinely different hazard to showcase**: glacial lake
  outburst floods and snowmelt, upstream of the valley — a distinct story
  from the monsoon-rain flooding everywhere else in the state.
- **A real, dated local landslide event already on record**: GSI's own
  written investigation into the April 2016 Tawang Town landslide — a
  concrete, official, citable local proof point for SlideSense.
- **Easier logistics**: the valley sits on a Border Roads Organisation
  corridor, which plausibly means better physical access for installing
  or maintaining any sensors than a remote interior district would.

---

## FloodSense at Jang

### What we already have

- **Flood timing (WHEN) is done and proven** for this valley — trained
  and calibrated against two real local river gauges (Murga Bridge, Rho
  Basti), both still reporting live. On official-threshold stations
  elsewhere in the state this same method caught over three-quarters of
  real flood episodes, and its confidence numbers have been checked
  against real outcomes, not just theory.
- **Since Sept 2026 it also reads both Jang gauges live every morning.**
  Adding the river's own level to the rain was tested on past years. At the
  rivers with an official danger level, the warnings caught about five
  times as many floods (58% vs 11%) and were right more than half the
  time.
- **A real satellite check specific to this valley**: 12 actual historical
  flood dates in Jang were directly verified using satellite water-extent
  data, not just modeled — genuine ground truth for this exact place.
- **A relevant snow-cover layer already in hand**, useful given this
  valley's real seasonal snow and glacial-lake exposure.
- **A general flood-prone map already covers this area** — though the
  specific stretch of river through Jang itself hasn't been individually
  double-checked yet, which is a known, worth-closing gap, not a hidden one.

### What we don't have yet (the free ceiling)

- **No official government danger/warning water-level number** for either
  local gauge. We've worked around this by calculating our own threshold
  directly from each gauge's own recorded history — a standard, accepted
  technique — so this isn't blocking, but an official number would be a
  nice independent confirmation.
- **No confirmed, downloadable map of the actual glacial lakes** upstream
  yet — a relevant dataset has been found, just not yet confirmed
  accessible.
- **No fine-grained terrain map of the valley floor** — meaning we can say
  "this river will likely flood soon" with real confidence, but not yet
  "and here is the exact field or building that goes underwater."

### Next moves — ASK (free or low-cost, needs a relationship, not code)

- **CWC**: request the official danger/warning threshold for the two
  local gauges — nice-to-have confirmation, not a blocker.
- **BRO**: request road-block maintenance logs for this corridor — a
  military-maintained road plausibly has some of the best-kept blockage
  records in the state, useful for both hazards.
- **Tawang district disaster office (DDMA)**: request local incident
  records — a small office, a much more tractable ask than a statewide one.
- **IMD**: request a real ground rainfall station for Tawang, to correct
  a known bias — our satellite rainfall estimate is measurably less
  accurate at this altitude than in the lowlands.
- **ISRO Bhoonidhi registration** (already in progress, pending a CAPTCHA-
  gated sign-up step): once through, opens India's own radar satellite
  archive, which can potentially fill in older flood dates our current
  free tools can't reach.
- **APSAC**: ask whether their own in-house terrain-survey (LiDAR)
  capability, already listed on their own infrastructure page, could
  cover the Jang valley before we look at an outside vendor.

### Next moves — PAID (only if this pilot gets a budget)

- **A small network of extra water-level sensors** along the river
  through Jang — turning one or two government gauge points into a full
  picture of the whole valley.
- **A commissioned detailed terrain survey (LiDAR) of just the Jang
  valley** — the single upgrade that turns a general risk score into an
  actual "water reaches exactly here" map. Cheap at this small a scale.
- **Optional: commercial satellite tasking** (e.g. Planet, Maxar) for
  ongoing monitoring going forward. This can't recover past floods —
  tasked satellites can only image the future — but it means every new
  flood in Jang from here on could be captured at much sharper detail,
  continuously proving and improving the model in near-real time.

---

## SlideSense at Jang / Tawang

### What we already have

- **The statewide susceptibility build already covers this area** — no
  extra work needed to have a live score here today.
- **A real, dated, official proof point**: GSI's own written report on
  the exact April 2016 Tawang Town landslide.
- **A large pool of dated landslide events across the wider Himalayan
  region** (roughly 800+, spanning the whole mountain arc, not just
  Arunachal) already gathered and ready — not yet folded into the active
  model, but sitting there as a known next lever.

### What we don't have yet

- **The daily rain-based trigger is known to be less accurate at this
  altitude** than in the lowlands — a real, acknowledged limitation, not
  a hidden one.
- **No size/magnitude forecast** — we can currently say "a landslide is
  likely here," not "and it will be this big." This has been tested and
  isn't achievable with data available today — worth being upfront about
  if asked directly.

### Next moves — ASK

- **GSI licence**: this is the natural moment to formally request full
  permission to publish and commercially use GSI's own national
  landslide inventory — currently restricted to internal reference only.
  This single dataset underlies roughly 70% of our strongest existing
  landslide evidence; getting cleared to use it commercially, plus access
  to their fuller dated-events table (currently only a tiny fraction is
  publicly visible), is the single biggest available upgrade to
  SlideSense's data foundation.
- **BRO**: the same road-block logs requested for FloodSense double as
  landslide date records.
- **PWD**: road-maintenance and blockage logs — a genuinely better source
  of dated landslide events than GSI's own limited public table.
- **Tawang DDMA**: same local incident-record request as FloodSense.

### Next moves — PAID

- **The same Jang-valley terrain survey (LiDAR) requested for FloodSense
  serves SlideSense too** — one cost, sharper answers for both hazards at
  once (exact water reach, and exact slope stability).
- **A couple of physical ground-movement or rainfall sensors placed on
  the known-unstable 2016 Tawang slope**, or another known-risk slope
  nearby — a highly visible, concrete proof point that the forecast
  tracks a real, monitorable hillside, not just a model on paper.

---

## What the pilot team does on the ground

Everything above is about *data and permissions*. This section is about
*people physically going to Jang* — what they survey, install, collect,
and log while they're there, and what to plan around before they go.

### Surveying and mapping

- **River cross-section / bathymetry survey of the Jang river.** This is
  the single missing piece that turns "the water level is high" into an
  actual depth-and-extent map. Gauge readings alone can never do this —
  someone has to physically survey the riverbed shape. This is the
  top-ranked flood data gap statewide, and Jang is small enough to survey
  in full.
- **Drone survey of the valley**, repeated over time. A satellite gives
  the whole state at moderate detail; a drone gives one hillside or
  riverbank at centimetre detail, repeatably, so change can be measured
  survey-to-survey. This is the practical, mid-cost way to get detailed
  terrain for one pilot valley without commissioning a full aerial LiDAR
  contract — and doubles as the terrain upgrade both products need.
- **Toposheet-grade contour and drainage mapping**, if the standard
  30-metre elevation data proves too coarse once the team is looking at
  Jang up close — a lower priority than the river survey, but worth a
  field check.

### Installing and placing sensors

- **Don't scatter sensors — let the model choose the site.** The
  defensible version of "add hardware" is: our own statewide model
  already tells you *which* slope or river stretch is worth watching;
  physical sensors only make sense once that answer exists. For Jang,
  the known-unstable April 2016 Tawang Town slope is the obvious first
  candidate, not a guess.
- **River sensors**: additional water-level sensors physically placed
  along the Jang river, turning the two existing gauge points into full
  coverage of the valley.
- **Slope sensors**: for the one or two highest-risk slopes only —
  piezometers, tiltmeters, extensometers, or crackmeters (the standard
  instrument set for slope early-warning) measure real ground movement
  hours to days before failure — something no satellite can see, at any
  resolution. This only works on slopes that creep before they fail.
  Sudden debris flows and rockfalls give no such warning. In GSI's own
  survey they are a small minority of Arunachal's mapped landslides
  (about 3%, probably under-counted), so most dangerous slopes here can
  be instrumented — but sites should be picked knowing that limit going
  in. *(Corrected 2026-10-06: this line used to say "roughly six in ten";
  the survey figures are in DESIGN.md, Part 1.)*
- **A real local rain gauge in Tawang/Jang itself** — installed, not
  just requested from IMD — would correct a known, measurable satellite
  rainfall bias at this altitude, arguably the single biggest accuracy
  lever available for both hazards here.

### The verification loop — logging what actually happens

- **Start daily forecast logging immediately, before anything else.**
  This is the cheapest and most time-sensitive task on this entire list:
  a forecast issued today and not written down is gone forever the
  moment tomorrow arrives — there is no way to retroactively prove or
  disprove it later. It costs almost nothing (a daily snapshot file) and
  it's the one thing on this whole list that money can't buy back later.
  **Done for floods (21–22 Sept 2026):**
  - Every day's flood forecast is saved automatically.
  - The river forecasts are graded against the gauges without anyone
    doing anything.
  - The area forecasts are saved and wait for satellite or field
    confirmation.
- **Every real flood or landslide that happens during the pilot gets
  verified and logged** — via satellite/drone re-imaging, sensor
  telemetry, or a field visit — as a new dated, located event. That
  confirmed archive is what retrains and improves the model each season;
  the pilot doesn't just consume data, it's designed to manufacture its
  own.

### Local data the team can collect just by asking around

- **Photograph BRO, PWD, and DDMA road-block/incident logbooks
  directly**, rather than waiting on a formal data-sharing agreement —
  these are handwritten operational registers kept for decades, and a
  field visit can often extract far more, far faster, than a written
  request working through channels.
- **Talk to residents and village elders** near the river and near the
  2016 landslide site — local memory of past high-water marks and slope
  history is low-cost corroboration that costs nothing but time on-site.
- **A lightweight manual building/structure inventory** near the river
  and the known slope — official building-inventory data barely exists
  for this state, and a field team is well-placed to informally note
  what's actually exposed while they're already there.
- **Photograph, geotag, and time-stamp anything relevant on sight** — the
  same discipline planned for a future public reporting app applies
  equally to the team's own field notes: capture location and time
  automatically, keep it staged and cross-checked before it's trusted as
  a confirmed event.

### Plan around this before the team goes

- **Tawang sits in an Inner Line Permit zone, on an active international
  border.** Any field visit, sensor install, or maintenance trip needs
  ILP clearance arranged ahead of time — budget real lead time for this,
  not a same-week trip.
- **Access is still real work, even on the BRO corridor.** The
  Border Roads-maintained road plausibly gives better physical access
  than a remote interior district, but "better" is relative — this is
  still high-altitude, monsoon-affected terrain, and travel/maintenance
  windows should be planned around the season, not assumed available
  year-round.

### The alternative that needs no site visit at all

Worth knowing before committing field-team time: a processed-satellite
option exists that answers a version of the same slope-monitoring
question with **zero physical access needed**. A commercial InSAR
processing service (vendors like TRE Altamira or Gamma) run against the
free Sentinel-1 archive can produce a live list of **which slopes are
already moving, right now** — not just "susceptible," but actually
detected in motion — statewide, without installing a single sensor. It
doesn't replace ground instruments (no hours-ahead failure warning, no
sub-millimetre precision), but it's worth running in parallel, since it
needs no team on the ground, no ILP, and no maintenance visits at all.

---

## Suggested order of operations

1. **Start daily forecast logging today, before anything else moves.**
   Zero cost, zero dependencies, and the only item on this list that
   becomes permanently unrecoverable if delayed.
2. **Send every zero-cost ask together, this week** — CWC threshold,
   BRO logs, Tawang DDMA records, IMD ground station, and the GSI licence
   letter. They're all just letters or calls; no reason to trickle them
   out one at a time.
3. **In parallel, finish the ISRO Bhoonidhi registration** and see what
   it opens up for this valley specifically.
4. **Arrange Inner Line Permit clearance for a field visit now**, given
   the real lead time it needs — don't let it become the bottleneck once
   everything else is ready.
5. **Decide the terrain-survey path**: ask APSAC first (possibly free or
   low-cost), get an outside-vendor drone/LiDAR quote as a fallback
   either way. This one paid item is the highest-leverage single spend —
   it improves both products at once. Bundle the river cross-section
   survey into the same field trip.
6. **On that same field visit**: photograph BRO/PWD/DDMA logbooks,
   talk to residents near the river and the 2016 slide site, and do a
   lightweight building-inventory walk — all near-zero marginal cost
   once a team is already on-site.
7. **Once terrain data is in hand**, convert the flood risk score into an
   actual water-reach map, and sharpen the landslide model's precision
   the same way.
8. **Budget-permitting, add the extra river and slope sensors** —
   guided by the model's own top-risk picks, not placed by guess — plus
   consider commissioning InSAR processing in parallel, since it needs no
   site visit at all.
9. **Independent of any of the above**: the flood-location model
   training and calibration work can start immediately — it only needs
   data already collected, not the pilot's outcome. **Done (Sept 2026):**
   the "where does the water go" half now gives a real, checked chance for
   every 100 m patch, and it has been joined with the "is a flood coming"
   half into one daily forecast, then tested on 2023–26 floods it had never
   seen. It finds the right places well; its timing is useful but modest;
   and in steep mountain ground — Jang's kind of terrain — it is still
   reasoning more than it is proven. That last point is the concrete reason
   the Jang field visit and local gauges matter.

---

## Likely questions, and how to answer them

**"Haven't we already used all the free data out there?"**
Yes — essentially everything free and automatic has already been found
and used, statewide, for both hazards. What's left needs either a
relationship (a call or letter to a government office) or a budget line
(sensors, a terrain survey, sharper imagery). We already know exactly
which ask unlocks what.

**"Why not just wait for more free data to show up?"**
Two of the remaining gaps genuinely won't close on their own: a
resolution-limited terrain map, and a legally restricted landslide
database. Both need either money or a formal request regardless of how
long we wait.

**"Can we give someone a real probability number today?"**
For floods, yes, in three honest forms *(updated Sept 2026)*:
- **At a gauged river:** "X% chance this river reaches danger level
  today". This is the strongest number, and it has been checked: when it
  says 20%, about 20% happen.
- **For an area:** "flood risk here is 9× normal today".
- **For a spot:** "if this area floods, this spot has a 30–40% chance of
  going under".

We do **not** say "this exact spot has a 30% chance of flooding today". A
single spot's daily chance is naturally tiny, well under 1% even on the
worst day on record. In the mountains our flood record is too thin to
vouch for that number yet, which is exactly what the Jang ground truth is
for.

For landslides, we're still one training/calibration step away, using data
already collected. None of that is blocked on the pilot; it can start now.

**"What does the pilot actually buy us that the statewide product
doesn't already have?"**
A small enough area to fully fund and instrument, a chance to prove a
second hazard type (glacial lake floods) the rest of the state doesn't
have, a path to precise water-reach mapping, and a visible, tightly
monitored success story to point to before scaling statewide.

**"What's the one thing that helps both products at once?"**
A detailed terrain survey (LiDAR) of the Jang valley. It sharpens exactly
where floodwater goes and exactly which slope is unstable — for one cost.

**"Do we need the GSI licence for this pilot to work?"**
No — SlideSense already runs without it, at this pilot and statewide.
But it's the single biggest available upgrade to landslide data quality,
and since we're already writing government letters for the pilot, this
is a natural moment to send that one too.

---

**Bottom line:** the free-data phase is genuinely finished, not abandoned
early — that's real progress, not a stall. Jang/Tawang is the right next
step precisely because it's small enough to fund fully, already has a
head start, and every ask on this list has a known, specific payoff
already identified. Nothing here is speculative; it's a shopping list
built from what we've already proven works.
