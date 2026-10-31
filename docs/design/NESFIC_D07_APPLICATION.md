# NESFIC 2026 application — NESFIC-D-07, Soil Erosion Risk Mapping & Monitoring

> **Draft answers for the portal form, written 2026-10-25.** Each answer is under the
> form's 500-word limit. Lines in **[square brackets]** are for us to confirm or fill, and
> must not be pasted. Facts and numbers come from [EROSION_PLAN.md](EROSION_PLAN.md)
> (results log) and [EROSION_MODULE.md](EROSION_MODULE.md). Re-check them there before
> submitting.
>
> **Superseded for pasting (2026-10-30):** the paste-ready answers, labelled [Under
> development] / [Planned] and carrying everything built since, are in
> [NESFIC_D07_FINAL_ANSWERS.md](NESFIC_D07_FINAL_ANSWERS.md). This file keeps the form
> facts, the department questions and the older draft.
>
> **Being reworked (plan of 2026-10-27):** the answers will carry the whole roadmap, each
> item labelled *built / being tested / in the programme (month) / beyond the programme*.
> See [NESFIC_D07_SUBMISSION_PLAN.md](NESFIC_D07_SUBMISSION_PLAN.md).

## What the official site says (checked 2026-10-25)

| Item | Official answer | Source |
|---|---|---|
| Website | `https://startup.assam.gov.in/nesfic26` (Assam Innovation & Startup Foundation, Govt of Assam) | home page |
| The 12 questions | **Official.** Word for word the "Uniform Solution Proposal Requirements", one page, the same for every challenge | `/nesfic26/docs/uspr.pdf` (Resources page) |
| D-07 closes | **10 November 2026** | `/nesfic26/problem-statements/nesfic-d-07` |
| Questions to the department | **Cut-off 25 October 2026 (today)**, through "Ask a question" on the D-07 page | same |
| Home-page timeline "25 Sep – 25 Oct" | Out of date; the challenge page says 10 Nov | home page vs D-07 page |
| Who can apply | Startups, companies, LLPs, registered entities, individuals, teams, researchers, students. Anywhere in India. DPIIT recognition **not** needed | home page FAQ |
| Team | Up to **5** including one **Lead Applicant**, who receives any grant | terms A3–A4 |
| Category | Registered Startup/Organisation · Innovator – Individual/Team · Educational Institution | terms A2 |
| Stream | **Stream 1** (answering a published problem statement) | terms A1 |
| Grants | Idea up to ₹10 L · **MVP & Prototype up to ₹20 L** · Deep Tech up to ₹40 L. Idea grants for at most 2 challenges, **only one MVP grant per applicant per edition** | home page |
| Fee | None | terms B8 |
| Uploads | Proof of Work PDF **mandatory**, ≤ 10 MB ("a proposal narrative alone is not sufficient"). Terms also say "upload the required pitch deck": put it inside the PDF or as the optional second PDF | form + terms A6 |
| Must disclose | Third-party data, software, models and IP used; what is our own work | terms A8, B6 |
| Assessment | Problem fit · innovation & merit · maturity · feasibility · impact · team & presentation. USPR adds: data, security & compliance; validation evidence; resource realism; pilot readiness | home page + USPR |
| Not promised | Selection is not a contract or purchase order | FAQ |
| IP | We keep our IP | terms B6 |
| Contact | `query.nesfic@assamstartup.org` | home page |
| Registration fields | Entity name (or Team/Individual), lead applicant name, phone with OTP, email, state, district, city, password, two consent boxes | `/register?role=startups` |

## The real form, read while logged in (2026-10-25)

Read on the COO's account at `/nesfic26/apply/stream-1?problem=nesfic-d-07`. Nothing was
typed or saved, and no draft was created: the dashboard says "You have not applied to a
challenge yet", and the Application ID reads "Generated when saved".

**01 Application details**

- **Filled in automatically:** Challenge ID NESFIC-D-07; owner Soil Conservation
  Department; title; Application ID (generated on save).
- **Participation type:** "Startup / Innovator".
- **Applicant type: "Team / Individual"**, not "Registered Entity". That was set at
  registration.
- **Lead applicant: Pankaj Kar** (COO), with his email and mobile already verified. Under
  the terms, the lead applicant receives any grant.
- **Team details, for each member:** Name\*, Email\*, Mobile\*, Role\*, Team / initiative
  name\* (filled in as "BEE Solutions"), Organisation name (optional), and Relevant skills /
  experience\*. Up to 4 more members, 5 in all.
- **Role choices:** Founder · Co-founder · Technical / Development · Product / Design ·
  Research / Domain · Business / Operations · Implementation / Field Support · Testing /
  Validation · Data / Analytics · Mentor / Advisor · Other.

**02 Proposal details**

- 12 required **plain-text boxes**, each with a 500-word counter.
- **Tables and bold do not survive pasting.** Convert them to short lines before pasting.

**03 Supporting material**

- Proof of Work PDF (required, ≤ 10 MB).
- Demo video URL (optional).
- Product / website URL (optional).
- Additional PDF (optional, ≤ 10 MB).

**04 Declarations**

- The work is original, the details are correct, and the committee's decision is final.
- One required "I agree" box; the lead's name is filled in automatically.

**Buttons:** Save as draft · Save & preview. Submission happens after the preview.

## Choices made in this draft (change if needed)

- **Stream 1, challenge D-07, applicant type "Team / Individual", team name BEE
  Solutions, lead applicant Pankaj Kar.** This is what the account is registered as. If the
  grant should go to the company instead, the company would need its own registration as a
  "Registered Entity". **[Decide before submitting.]**
- **Grant asked: MVP & Prototype (up to ₹20 L).** Two live modules and a working Assam
  first cut are past the idea stage.
- **D-18 (flood digital twin) not covered here.** We may apply to it too, but only one MVP
  grant can be won.

---

## 1. Problem understanding & user workflow

Assam loses topsoil from three very different kinds of land:

- steep hills under shifting cultivation (*jhum*) in Dima Hasao and Karbi Anglong;
- tea and village slopes along the foothills;
- cropland on gentle ground.

The loss is slow and hard to see until a slope is gullied, a stream silts up or a field's
yield falls. The Soil Conservation Department must decide where to send survey teams and
where to build bunds, check dams, contour trenches and vegetative barriers, with limited
staff and budget.

**Who the users are.**

- **Department planners and divisional officers**, who choose areas and works.
- **Field teams**, who survey and verify.
- **Farmers and communities** in erosion-prone areas, who live with the loss and carry out
  much of the conservation work.

**The current workflow, as the department describes it.** Erosion-prone areas are found
mostly through field observation, surveys and public information. That is slow and hard
to repeat consistently across 78,000 km². It is hardest exactly where access is worst: the
hill districts. Published erosion maps exist, but they are one-off studies at coarse
scale. They are not refreshed when land is cleared or when a monsoon is unusual. They do
not say which small catchment to visit first, or why.

**The gaps we address.**

1. **No consistent, state-wide picture at planning scale.** National maps are 250 m or
   coarser; ours is 100 m.
2. **No ranking.** A six-colour map does not tell a divisional officer which ten
   catchments to survey this season.
3. **No change over time.** Fresh *jhum* clearing or new bare slopes are not picked up
   between surveys.
4. **No reason attached.** Officers need to know *why* a place ranks high (steep slope,
   bare ground, heavy rain or weak soil), because the reason decides the treatment.
5. **No feedback.** Field findings do not flow back to improve the map.

**Intended outcome.** A state-wide erosion-risk layer for Assam, refreshed each season.
It feeds a ranked list of small catchments, each with its main driver named, and a field
kit that sends teams to the right places and brings their findings back. The result is
fewer wasted survey trips, conservation money spent where loss is highest, and a record
that shows whether treated areas improve.

---

## 2. Proposed solution & key features

**SoilSense** is the soil-erosion module of our hazard platform. It combines the five
factors the department names (rain strength, soil, slope, plant cover and land use) into
an erosion-risk layer for Assam. It then ranks, explains and monitors that layer.

**Main modules**

1. **Erosion-risk map (built).** The standard soil-loss recipe (RUSLE: rain × soil ×
   slope × cover × practice) on a 100 m grid over the whole state, in tonnes per hectare per
   year and the common Indian six classes. River land, water and built-up areas are shown as "not
   assessed", never "low", because RUSLE cannot model flood deposition or bank cutting.
2. **Priority list (built).** All 703 small catchments (HydroBASINS level 12) and 35
   districts, ranked by loss. Each row names its main cause, what sets it apart from
   catchments just as steep (for example "heavy rain, 2.5×"), typical measures, and how
   often it stays top 20 across 1,000 runs of the uncertain inputs. Officers can re-rank it
   by their own weights.
3. **Dry-season monitoring (built, first version).** Sentinel-2 measures how much of every
   square was bare or burnt each dry season since 2019: the ground the monsoon then hits.
   Any season, or the change between two, is on the map, and catchments getting barer are
   listed. Flags for "new bare ground on a steep slope" are held back until they pass their
   tests (section 9).
4. **Weekly outlook (built, first version).** Each day, the next seven days' forecast rain,
   set against each place's normal for the season, ranks the catchments where the coming
   rain will wash off the most soil. Replayed over 44 monsoon weeks, it calls the erosive
   weeks well.
5. **Field kit (export built; return form Phase 2).** Map and list download as GeoPackage,
   KML, GeoJSON and CSV. 100 visit points in the top 20 catchments come as a GPS file and a
   CSV with columns for findings. Findings stay apart until verified, then grade the map.
6. **Village card (built; Assamese wording Phase 2).** Search a place or type a GPS
   position: one printable card with the loss around it, why, what helps, how bare its
   slopes were each year, and this week's rain.

**What changes compared with today**

| Today | With SoilSense |
|---|---|
| Survey first, then decide | A ranked list first, so surveys go where loss is likely highest |
| One-off maps, 250 m or coarser | 100 m, refreshed each season |
| Colours only | A rank plus the reason |
| Field findings stay on paper | They come back and grade the map |
| No view of change | Bare ground every dry season since 2019, and the change between any two |
| No warning before a wet week | A weekly outlook from the live rain forecast |

**User interaction.** A web app, nothing to install: pick a district or village, see why
it ranks high, download the list for the field. The department's own data plugs in as it is
shared, each swap logged with a before-and-after comparison.

---

## 3. User journey, wireframes, prototype & proof of work

**Prototype maturity.** SoilSense runs today as a module in our web app, with real
state-wide Assam results, under the status "building". Five screens are built: the
**map**, **this week's outlook**, **change over time**, the **priority list** with its field
kit, and **how to read this** (the method and its limits). They pass our automated screen
check.
Screenshots are in the attached Proof of Work PDF (pages 3–9).

**Journey 1: a divisional officer planning the season**

1. Opens SoilSense and picks a district (for example Karbi Anglong).
2. The map opens on that district, with the six classes and the share of land in each.
3. The district card shows its mean loss and its rank among 35 districts.
4. The priority list shows the top catchments, each with its loss, its main driver and
   whether the rank holds under both rain maps.
5. Downloads the list and map layers (GeoPackage, KML, GeoJSON, CSV) and the field
   points (GPS file) for planning and fieldwork.

**Journey 2: a field team verifying**

1. Loads the field points (GPX or KML) on a phone or GPS unit.
2. Visits the top catchments and records what it sees (rills, gullies, fresh clearing,
   existing works), with a photo.
3. Findings are uploaded and held as "unverified" until checked. They then grade the map
   and feed its calibration **[Phase 2–3]**.

**Journey 3: a farmer or community member**

1. Receives a printed or shared village card (built in English; Assamese wording to be
   written by the team), for example: "Your area: high
   loss, mainly because of steep cleared slopes. Contour bunds and keeping cover on the
   slope help."
2. Can report a problem area through the field form, via the department or an NGO
   **[Phase 2]**.

**Wireframes in the PDF.** The built screens (map, list, method page), plus mock-ups of the
next screens: change view, weekly outlook, field form and village card.

**Proof of work beyond the prototype**

- **Two live products in Arunachal Pradesh run on the same backbone.** A flood forecast
  runs by itself every morning; it is written down before the day and graded against 32
  river gauges. A landslide forecast, learned from about 37,000 mapped landslides, is
  issued daily.
- **The Assam erosion map did not start from zero.** It came from that backbone, moved to
  a second state with a region switch.
- **Checks were written before the first result, then run on it:**
  - hills come out 8.3× the plains (bar: at least 3×);
  - the rain-strength map is within 5% of the measured Guwahati value;
  - on satellite imagery, all 20 of the top 20 catchments are visibly steep, 10 of them
    with visible clearing.

**[Demo video URL and product URL. The public app does not show SoilSense yet. Push it
before submitting, or leave the URL out and rely on the PDF.]**

---

## 4. Technology & solution architecture

**Architecture in one line.** Sources → raw store with a provenance record → one shared
100 m grid → factor layers → soil-loss estimate and classes → ranking and change → web app
and GIS exports → field findings come back.

**Data backbone (built, shared with our other products).**

- Python scripts fetch each source and store the original untouched.
- Each file keeps a record of its source, licence, link, fetch date and checksum.
- Every layer is fitted to one grid. For Assam: EPSG:32646 (UTM 46N), 100 m cells,
  6,500 × 4,500, on the same lattice as our Arunachal grid. The state mask is the Survey
  of India outline with 35 districts.
- A region switch selects the state. Our live Arunachal forecasts are checked after every
  change to shared code, to confirm they have not moved.

**Erosion recipe (RUSLE, A = R·K·LS·C·P)**

- **R, rain strength:** InRESatE (IIT Roorkee, from 30-minute satellite rain, 2001–2018).
  It reads 7,507 against 7,924 measured at Guwahati (−5%). IRED (IIT Delhi) runs alongside
  as a check. We rejected the common annual-rainfall formula, which reads 91% low there.
- **K, soil erodibility:** Williams' equation from SoilGrids sand, silt, clay and organic
  carbon. Its district pattern matches India's published erodibility map (ρ 0.94).
- **LS, slope length and steepness:** from the 30 m Copernicus DEM. The McCool slope form,
  suitable for steep hills; slope length from flow accumulation, capped at 300 m. A guard
  removes the false slope that tree canopies add on flat land.
- **C, cover:** ESA WorldCover class values for now; seasonal Sentinel-2 cover from Google
  Earth Engine from Phase 1.
- **P, practice:** 1 ("if untreated") until the department's treated-area records arrive.
- **Domain mask:** water, built-up land, channels, and river land less than 2 m above a
  large channel are marked "not assessed".

**Ranking.** Loss is summarised over HydroBASINS level-12 catchments and districts. The
main driver is the factor furthest above the state average. Each rank is recomputed under
both rain maps and both cover values for tree land, and every rank that does not hold is
marked.

**AI/ML.** Phases 0–2 use a transparent physical recipe that can be explained and audited.
Machine learning comes in for two jobs:

- classifying land cover from Sentinel-2, for example splitting forest, tea and fresh
  clearing;
- a correction layer trained on field findings. It is added only when enough labelled
  points exist, and is tested on spatial blocks held out from training.

**Stack.**

- Python geospatial tools (rasterio, GDAL, NumPy, GeoPandas).
- Google Earth Engine for Sentinel-2.
- A Streamlit web app with Leaflet maps.
- Daily jobs on Modal cloud in the Mumbai region, which already runs our flood forecast
  every morning.
- Outputs in GeoTIFF, GeoPackage, KML, CSV and GeoJSON, which open in QGIS and ArcGIS.

**Integration.** Plain open GIS formats, so the department can use the layers in its own
tools, with an API feed later if wanted.

---

## 5. Development methodology & intermediate steps

We work in short, checked steps. Each step has a written "done when", and every number is
logged.

1. **Discovery and requirements (done).** Every line of the D-07 statement was mapped to a
   feature and a phase. Every assumption was checked against published research and the
   data itself, which caught two big errors before any result existed: the usual
   rain-strength formula reads 91% low in Assam, and the usual slope formula overstates
   steep hills. Output: a design document and a register of every provisional choice.
2. **Backbone moved to Assam (done).** Region switch, Assam grid, official outline, and
   terrain, drainage, soil and land-cover layers. Output: Assam base layers, each with
   provenance.
3. **Recipe and pre-registered checks (done).** Pass bars were written before the first
   erosion number existed, so the map could not be tuned until it "looked right".
   - Passed: hills 8.3× plains, factor ranges, class spread, the "not assessed" mask, and
     live forecasts untouched.
   - Failed narrowly: false slope at canopy edges. A guard was added.
   - Failed outright: the two good rain maps share only 7 of the top 20 catchments. Rather
     than hide this, the list marks every rank that depends on the rain source.
4. **First priority list and app module (done).** 703 catchments ranked. The top 20 were
   checked by eye on imagery: 20 of 20 steep. Built into the app.
5. **Monitoring, outlook and outside check (done).** Bare ground every dry season since
   2019; the weekly outlook; field-kit exports; comparison with ISRO's land-degradation map.
   Change flags were tested before showing, failed two of four tests, and are held back.
6. **Phase 1: cover and validation (Nov–Dec 2026).** Split the "tree" class; change flags,
   second attempt; a blind imagery sample of about 300 points.
7. **Phase 2: prototype (Dec 2026–Feb 2027).** Outlook graded daily, field-form round trip
   and Assamese village card. The pilot protocol is agreed with
   the department and written down *before* any field visit. Output: the Demo Day build.
8. **Phase 3: MVP (Feb–May 2027).** Department data swapped in (soil survey, treated areas,
   field records), each with a before-and-after comparison. Field results grade and
   calibrate the map. Outputs go into the department's GIS.
9. **Refinement.** Each season, new field findings and new imagery re-run the map. Changes
   are logged and versioned.

The same method built our live flood and landslide forecasts.

---

## 6. Development timeline & milestones

Aligned with the NESFIC programme calendar.

| When | Phase | Milestones and deliverables | Depends on |
|---|---|---|---|
| Done (Oct 2026) | **0 · Application proof** | Assam on the backbone (grid, outline, 35 districts, base layers); first state-wide erosion map at 100 m; pre-registered checks; 703 catchments ranked with reasons; field-kit export; dry-season bare ground 2019–2026; weekly outlook; check against ISRO's map; app module | Open data only |
| Nov 2026 | Conclave | Live demo with Assam data | — |
| Nov–mid-Dec 2026 | **1 · Cover + validation** | Split the "tree" class; change flags, second attempt; rain factor from our own satellite rain archive; blind imagery check of about 300 points | Earth Engine; any department data shared |
| mid-Dec 2026–Feb 2027 | **2 · Prototype** | Outlook's rain graded daily; field form → import; Assamese village card; **pilot protocol agreed with the department** | The department's choice of pilot areas and class scheme |
| **Feb 2027** | **Demo Day** | Working prototype, early results, pilot plan | — |
| Feb–May 2027 | **3 · MVP** | Department data in (soil survey → K, treated areas → P, field records); field comparison in pilot areas against pre-written pass bars; calibration; outputs in the department's GIS; district reports | Data-sharing permissions; field access |
| **From Jun 2027** | **Validated pilot and scale-up** | MVP demonstration; extension to more districts and the full state on a seasonal cycle | Pilot results |

**Ready for validation.** The risk map and priority list can be field-checked now. The full
prototype, with monitoring, outlook and field kit, is ready for a structured pilot by
**February 2027**.

**Proposed pilot areas [to agree with the department].** Dima Hasao and Karbi Anglong
(steep hills, *jhum*, erosion a known concern), plus one foothill belt for contrast.

---

## 7. Data & information requirements

All of Phase 0 was built on **open data**, so the work does not depend on unconfirmed
access. Department data improves the map; it is not a precondition.

**In hand, open (licence checked, provenance recorded)**

| Data | Use | Source / format |
|---|---|---|
| Copernicus DEM GLO-30 | Slope, slope length, drainage | ESA, GeoTIFF |
| SoilGrids 250 m (sand, silt, clay, organic carbon) | Soil erodibility K | ISRIC, CC-BY 4.0 |
| ESA WorldCover 10 m | Land cover, cover factor C | CC-BY 4.0 |
| InRESatE and IRED rain-erosivity maps | Rain factor R | Zenodo, CC-BY 4.0 |
| HydroSHEDS / HydroBASINS | Channels, catchments for ranking | WWF, free licence |
| Survey of India state and district outline | State mask, districts | Survey of India |
| Sentinel-2 L2A + Cloud Score+ | Bare ground each dry season since 2019, change | Copernicus via Google Earth Engine |
| Hansen Global Forest Change | Testing the change detector (never an input) | UMD, CC-BY 4.0 |
| GPM IMERG and Open-Meteo forecast rain | Weekly outlook (Phase 2) | NASA; Open-Meteo |
| CWC / NWDP gauge records | Checking rain and sediment | Government open portals |

Used for comparison only, never redistributed: the IIT Delhi national erosion map (IWED,
no licence stated), India's soil-erodibility map (ISED, CC-BY) and NRSC's Land Degradation
map 1:50,000, 2015–16 (Bhuvan).

**Requested from the department or ASSAC (not yet confirmed; the plan works without them)**

| Data | Improves | Format we can take |
|---|---|---|
| Field observations of erosion, with location and date | Validation and calibration | CSV or Excel with coordinates, shapefile |
| Treated areas (bunds, check dams, plantations) | Practice factor P; treated vs untreated | Shapefile, KML |
| Soil survey or soil map | Soil factor K | Shapefile, scanned maps |
| The department's soil-loss class scheme and planning units (micro-watersheds) | Classes and ranking units | Any |
| Higher-resolution satellite imagery via ASSAC | Gully mapping in pilot areas | GeoTIFF |
| Rain-intensity gauge records (IMD, ASDMA) | Rain factor checks | CSV |

**Processing and annotation**

- **Sentinel-2:** cloud-masked seasonal composites, with the cloud share recorded for each
  season.
- **Land cover:** about 300 blind points labelled on dated imagery, for the tree-class
  split and for validation. Labels are made before results are seen.
- **Field records:** kept in a holding area until verified, and never mixed into the data
  unchecked.

**Assumptions stated plainly**

- **Rain:** only one rain-strength gauge check exists so far (Guwahati). The two good rain
  maps disagree on *where* rain is most erosive, so ranks are reported under both.
- **Tree cover:** the cover value for satellite "tree" land mixes forest, tea and *jhum*
  fallow. The planned Sentinel-2 split resolves this.
- **Department data:** none is assumed. If none arrives, the pilot runs on open data plus
  our own field checks.

---

## 8. Team, manpower & expertise

**[Names and roles below are taken from our company deck. Confirm them, add
qualifications, and add up to two more members (five in all).]**

| Member | Role | Expertise | Main work |
|---|---|---|---|
| **[Sonit Saikia], Co-founder & CTO** | Technical lead | Geospatial data pipelines, satellite and terrain processing, ML forecasting, web apps. Built the platform's backbone and its live flood and landslide forecasts | Recipe, monitoring, outlook, app, validation design |
| **[Nabam Changriang], Co-founder & CEO** | Partnerships and programme | Government and community engagement in the North East | Department liaison, pilot agreement, reporting |
| **Pankaj Kar, Co-founder & COO (Lead Applicant)** | Operations and field | Operations, logistics, field coordination | Pilot logistics, field teams, village outreach |
| **[Member 4: GIS / remote-sensing analyst]** | Analyst | Sentinel-2, QGIS, field survey | Seasonal cover, labelling, field kit |
| **[Member 5: soil conservation / agronomy adviser, or a mentor]** | Domain adviser | Soil conservation practice in Assam's hills | Treatment hints, class scheme, field protocol |

**Indicative manpower by phase, in person-months [to confirm]**

| Phase | Tech | Analyst | Field / outreach | Adviser |
|---|---|---|---|---|
| 1 · Nov–Dec 2026 | 1.5 | 1.5 | 0.25 | 0.25 |
| 2 · Dec 2026–Feb 2027 | 2.5 | 2 | 0.5 | 0.5 |
| 3 · Feb–May 2027 | 3 | 3 | 2 | 0.5 |

**Critical specialist skills**

- **Remote sensing and terrain analysis:** in the team.
- **Honest validation design** (pre-registered checks, held-out testing): in the team, and
  used on our live products.
- **Soil-conservation practice in Assam:** our adviser, and the department's own officers.
- **Assamese for community material:** in the team or a local partner.

**Track record.** The team built and runs a data backbone with 29 sources (about 300 GB)
and two live daily forecasts for Arunachal Pradesh. It moved that backbone to Assam and
produced a first state-wide erosion map in about four weeks.

---

## 9. Testing, validation & evidence

**How we test.** Every check is written down, with its pass mark, *before* the result
exists. A failed check means "investigate", never "tweak until it passes". Every result goes
into an append-only log, failures included.

**Results on Assam so far (pass mark → result)**

- Hills against plains: ≥ 3× → **8.3×**, pass.
- Rain strength at Guwahati, the only measured gauge: within ±25% → **−5%**, pass. The
  common Indian formula reads −91% there.
- Rain map against 40 rain gauges (2001–18): we kept the map whose pattern agrees better in
  Assam (0.36 against 0.20).
- Soil factor against India's erodibility map: district agreement **0.94**.
- Top 20 catchments by eye on satellite imagery: **20 of 20** steep, 10 visibly cleared.
- False slope at canopy edges: **failed narrowly**; a guard was added.
- Top 20 shared between the two rain maps: **failed (7 of 20)**; every rain-dependent rank
  is marked.
- **Against ISRO's Land Degradation map (NRSC, 1:50,000):** eroded vs normal land 0.66 (mark
  0.70), catchment ranks 0.36 (0.40), district ranks 0.13 (0.50): **all three failed.** The
  national 250 m map scores 0.42, −0.30 and −0.36: it points the wrong way. Most of our gap
  is on tree land, where one cover value stands for forest, tea and *jhum* fallow. Measured
  dry-season cover did not close it, so it stays the top open question.
- **Change flags** ("new bare ground on a steep slope"): false alarms on untouched forest
  and in tea gardens pass (0.05% and 1.8%; marks ≤ 1% and ≤ 3%); clearing caught (48%,
  mark ≥ 50%) and a blind check on dated pictures (58%, mark ≥ 70%) fail. A second attempt,
  also requiring a real loss of greenness and judged on new pictures, reached 63% (76% of
  the readable ones): still short, so the flags are held back and the measured bare ground
  is shown.

- **Weekly outlook, replayed** over 44 monsoon weeks (2024–25) with the forecasts issued then,
  against NASA satellite rain: which weeks are erosive ρ 0.63 (mark 0.60) and heavy weeks
  picked out 77% of the time (mark 70%) pass; which places within a week ρ 0.18 (mark 0.30)
  fails, so its list is read as regional.

We lead with the ranking; tonnes per hectare are indicative until calibrated.

**Next validation, each with its mark set in advance:** a blind imagery sample of about 300
points; measured river sediment where records allow; the outlook graded daily as it runs; the
pilot's blind field comparison, with the protocol agreed with the
department and dated before any visit.

**Performance measures:** ranking agreement with field findings; share of top catchments
confirmed in the field; false-alarm rate of change flags; skill of the outlook's rain.

**Prior product evidence.** The same team and backbone run a flood forecast graded daily
against 32 river gauges: when it says 20%, about 20% happen. Our landslide forecast,
learned from about 37,000 mapped landslides, ranks a real landslide spot above a random one
about 6 times in 7.

---

## 10. Security, privacy, safety & compliance

**Security**

- The web app is read-only. Viewing maps needs no account, and there are no passwords or
  payments.
- Department data is kept in access-controlled storage. It is used only for the challenge
  purpose, never published, and deleted or returned on request.
- Daily jobs run on cloud hosting in India (Mumbai region). Keys are kept out of the code.

**Privacy**

- The risk map holds no personal data. It describes land, not people or owners.
- A field-check record holds a location, date, observation and optional photo. The
  reporter's name is optional, collected with consent, and never shown publicly.
- Community material is at area level (village or catchment), never plot or owner level.

**Safety and human review**

- SoilSense is **decision support, not an automatic decision**. It ranks where to look
  first. The department verifies in the field before any works are planned.
- Every figure is labelled with the kind of number it is: measured, estimated, rank or
  provisional. Limits are written on the screen, not hidden, for example: "On tree-covered
  land a square's class is indicative."
- Field findings stay "unverified" until an officer checks them, so a wrong report cannot
  change the map on its own.

**Auditability**

- Every raw file keeps a record of its source, licence, link, fetch date and checksum.
- Every provisional choice is listed in a register, with what would change it.
- Every check and result goes into an append-only log. Outputs are versioned, so any past
  map can be rebuilt.

**Licences and IP compliance**

- Open data is used within its licence, and CC-BY sources are credited.
- Sources with no licence or a non-commercial licence are used only for comparison and
  never redistributed. That covers the IIT Delhi erosion map; FABDEM is not used at all.
- Google Earth Engine is used under its applicable terms.
- Third-party software is open source (Python geospatial stack, Streamlit, Leaflet).

**Interoperability**

- Open OGC formats: GeoTIFF, GeoPackage, KML, GeoJSON and CSV.
- Standard projections (WGS84, UTM 46N) and LGD district codes, so the layers open directly
  in QGIS, ArcGIS and Bhuvan-style viewers.

**Regulatory**

- Indian map rules are respected: the official Survey of India outline is used for the
  state and its districts.
- The few personal details in field forms follow the principles of India's DPDP Act 2023:
  consent, a limited purpose, the minimum data, and deletion on request.

---

## 11. Innovation & differentiation

**Existing alternatives (prior art), named plainly**

- The IIT Delhi national RUSLE map (Raj, Saharia & Chakma; IWED, 250 m).
- GloSEM, the global soil-erosion model (Borrelli et al.).
- The ISRO/SAC Desertification and Land Degradation Atlas (Assam: about 7.2 lakh ha
  degraded).
- One-off academic RUSLE studies of single basins.
- The department's own field surveys.

All are static: made once, at coarse scale, with no ranking, no reason and no feedback.
"A static map exists" is the department's own stated problem.

**What is new in SoilSense**

1. **A living layer, not a one-off map.** Bare ground is measured every dry season since
   2019, and a weekly outlook, refreshed from the live forecast, shows where the coming
   rain will wash off the most soil. Erosion risk changes when land is cleared or a wet
   week comes, and SoilSense changes with it.
2. **Factors checked against measurement before use.** We rejected the widely used Indian
   rain formula after finding it 91% low at the only measured gauge. We also showed that
   the national map's slope factor barely responds to slope. Against ISRO's own
   land-degradation map, ours points the right way and the national map the wrong way.
3. **A ranked work list with the reason.** Catchments are ranked, and each names its main
   driver, which points to the treatment. Ranks that depend on an uncertain input are
   marked, not hidden.
4. **Honest validation built in.** Pass bars are written before results, failures are
   reported, and field findings come back to grade the map.
5. **Built on a shared data backbone.** The same pipeline already runs live flood and
   landslide forecasts in Arunachal Pradesh. Moving it to Assam took a region switch, not
   a rebuild. That makes SoilSense cheap to keep running and cheap to extend, for example
   to riverbank erosion or floods in Assam.

**IP and dependencies**

- **Ours:** the backbone code, the region switch, the ranking and driver logic, the canopy
  slope guard, the validation framework, the app, and the checked local records it builds
  season by season.
- **Open-source software:** the Python geospatial stack (GDAL, rasterio, NumPy,
  GeoPandas), Streamlit and Leaflet.
- **Open data:** Copernicus DEM, SoilGrids, WorldCover, Sentinel-2, InRESatE and IRED,
  HydroSHEDS, and the Survey of India outline, all credited.
- **Proprietary service:** Google Earth Engine for Sentinel-2 processing. The same
  composites can be built directly from Copernicus if needed.
- **Method:** RUSLE (Wischmeier & Smith; Renard et al.) is a public standard. Our
  contribution is how it is fed, checked, ranked and kept current.

---

## 12. Resources, risks & pilot validation

**Indicative resources and cost drivers (MVP & Prototype grant, up to ₹20 L)
[split to confirm with the COO]**

| Driver | Share |
|---|---|
| Team time: tech build, analyst, field coordination | about 55% |
| Field work in pilot districts: travel, local guides, GPS and phones, community sessions in Assamese | about 20% |
| Cloud computing, storage, hosting, imagery processing | about 10% |
| Optional sensors at 2–3 pilot outlets (rain-intensity gauges, turbidity) | about 10% |
| Contingency | about 5% |

Most inputs are open data, so buying data is not a major cost.

**Key risks and mitigations**

| Risk | Mitigation |
|---|---|
| The two good rain-strength maps disagree on where rain is most erosive | Rank under both and mark unstable ranks; add gauge checks (IMD, ASDMA); build our own rain factor from satellite rain |
| The satellite "tree" class mixes forest, tea and *jhum* fallow, so cover is uncertain | Run both cover values; split the class with Sentinel-2 under a new, pre-registered blind test (a first attempt failed its test and was not adopted) |
| Canopy makes flat land look sloped in the elevation model | Guard in place; a bare-earth elevation model through ASSAC if available |
| Cloud blocks monsoon imagery | Pre- and post-monsoon composites; cloud share recorded; gaps marked, not filled silently |
| Department data arrives late or not at all | The whole plan runs on open data; department data is an upgrade |
| Field access in the hill districts (season, terrain) | Fieldwork in the dry season, with local guides and department staff |
| RUSLE cannot model gullies, landslides or riverbank cutting | Those areas are marked "not assessed"; gullies and riverbanks are noted as later extensions |
| Change flags give false alarms | Tested before showing: few false alarms on forest and tea, but they failed the blind picture check, so they are held back until a second attempt passes |

**How the solution will be pilot-validated**

- **Where:** Dima Hasao and Karbi Anglong, plus one foothill belt for contrast
  **[to agree with the department]**.
- **How:** a field protocol, agreed with the department and dated *before* any visit.
  Blind points are stratified across the risk classes and the top-ranked catchments. Field
  teams record the erosion signs they observe (rills, gullies, bare soil, sediment,
  existing works) without seeing the map's class. We then measure how well the ranking
  separates high-loss sites from low-loss sites, against a bar set in advance.
- **Plus:** where measured sediment records exist, the ranking is compared against them.
- **Outcome for the department:** a validated, ranked list for the pilot districts, layers
  in its own GIS, and a seasonal refresh cycle. That is the base for extending to the
  whole state.

---

## Proof of Work PDF (mandatory, ≤ 10 MB): built

`docs/nesfic/SoilSense_Proof_of_Work.pdf` (15 pages, about 2 MB), made by
`scripts/run/build_proof_of_work.py` from the app's own screenshots
(`scripts/run/capture_soilsense_shots.py`) and the reports. Re-run both after any change, so
the PDF and the app agree. Contents: cover; what the department asked for and what exists;
the five screens; dry-season monitoring; every check with its pass mark; the two errors caught
early (rain formula, national slope factor); architecture; planned screens; the two live
products; plan, pilot and data.

**Still to add or decide:** a short pitch deck (the terms ask for one), inside this PDF or
as the optional second PDF; team names and photos once confirmed.

## Questions for the department (cut-off 25 Oct, via "Ask a question" on the D-07 page)

1. Does the department use its own soil-loss class scheme? If so, which?
2. What planning unit do works use: micro-watersheds (SLUSI codes) or something else?
3. Which records could be shared with selected teams, and roughly when? (Field observations
   of erosion; treated areas; soil survey.)
4. Which GIS software does the department use, and which formats does it prefer?
5. Which areas does the department have in mind for the pilot?
6. Is riverbank erosion in scope, or does another department handle it?
