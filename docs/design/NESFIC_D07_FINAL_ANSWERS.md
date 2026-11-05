# NESFIC-D-07: final answers (paste-ready)

> Rewritten 2026-10-30. Plain text for the portal's 12 boxes (500-word limit each; the form
> drops tables and bold). Labels: [Under development] = built or being built and tested now;
> [Planned] = on our plan, for the programme or after it. Numbers are kept only where the
> form needs them (dates, phases, grant category, defining specifications). Plans carried
> over from our landslide (SlideSense) and flood (FloodSense) modules are included where
> they apply to erosion. Text in {curly braces} is for us to fill and must not be pasted.
> Word counts are at the end.

---

## 1. Problem understanding & user workflow

Assam loses topsoil from three very different kinds of land: steep hills under shifting cultivation (jhum) in the hill districts; tea and village slopes along the foothills; and cropland on gentler ground. The loss is slow and hard to see until a slope is gullied, a stream or wetland silts up, or a field's yield falls. Each tonne of soil lost also carries away nutrients farmers then replace with fertiliser.

Who the users are:
- Department planners and divisional officers, who decide where to survey and where to build bunds, check dams, contour trenches and vegetative barriers, with limited staff and budget.
- Field teams, who survey, verify and supervise works.
- Farmers and communities in erosion-prone areas, who live with the loss and carry out much of the conservation work.
- Partner agencies who feel the downstream effects: disaster management, water resources, agriculture, forests and rural development.

The current workflow, as the department describes it: erosion-prone areas are found mostly through field observation, surveys and public information. That is slow and hard to repeat consistently across the state, and hardest where access is worst, in the hill districts. Published erosion maps exist, but they are one-off studies at coarse scale, not refreshed when land is cleared or a monsoon is unusual, and they do not say which small catchment to visit first, or why.

The gaps we address:
1. No consistent, state-wide picture at planning scale.
2. No ranking. A coloured map does not tell an officer which catchments to survey this season.
3. No reason attached. The reason (steep slope, bare ground, heavy rain or weak soil) decides the treatment.
4. No view of change. Fresh jhum clearing, hill cutting and new bare slopes are missed between surveys.
5. No warning. Nobody is told before an unusually erosive week or season.
6. No feedback. Field findings and completed works do not flow back to show what worked and to improve the map.

Intended outcome: one living erosion layer for Assam, refreshed every season and improved every year, feeding a ranked list of small catchments with the cause named and measures suggested; weekly and seasonal outlooks; a village card anyone can read; and a field loop that sends teams to the right places and brings their findings back. The result is fewer wasted survey trips, conservation money spent where loss is highest, and evidence of whether treated areas improve.

---

## 2. Proposed solution & key features

SoilSense is the soil-erosion module of SlopeSense, our multi-hazard platform. All its modules stand on one shared data backbone, which already runs live landslide and flood forecasts in Arunachal Pradesh. SoilSense combines the five factors the department names (rain, soil, slope, plant cover and land use) into an erosion layer for Assam, then ranks, explains, monitors and forecasts it.

Working prototype, state-wide:
- [Under development] Erosion-risk map at 100 m for the whole state, using the standard soil-loss method (RUSLE); river land, water and towns marked "not assessed", never "low".
- [Under development] Priority list of small catchments and districts, each with its main cause, typical measures and how firm its rank is; officers can re-rank by their own priorities.
- [Under development] AI erosion map trained on ISRO's mapped eroded land, shown beside the formula as a second opinion, with the reasons behind each area's score.
- [Under development] Dry-season bare and burnt ground every year since 2019, from Sentinel-2 satellites.
- [Under development] Weekly erosive-rain outlook from the live rain forecast, graded against past monsoons.
- [Under development] Soil reaching streams, showing where check dams pay most.
- [Under development] Value of soil lost: nutrients as bags of urea and rupees, and topsoil depth.
- [Under development] "What if we treat it?": soil saved by each measure.
- [Under development] Village card for any place; field kit with GPS visit points and GIS downloads.

Next:
- [Planned] An AI panel: several different models (the formula, tree models, deep learning) blended by a referee model, learned first across the wider Himalaya and North East, then fine-tuned for Assam and for each district.
- [Planned] Satellite-reading AI that tells forest, tea, jhum and fresh clearing apart and dates each jhum burn; radar monitoring through monsoon cloud.
- [Planned] Alerts for newly cleared slopes and hill cutting, sent only after an AI second check.
- [Planned] Seasonal outlook and a pre-monsoon watch list for divisions each April.
- [Planned] "Did the works help?" tracking; a works planner with costs; outputs shaped for PMKSY watershed and MGNREGA plans.
- [Planned] Stream sensors, rain gauges and soil-loss plots placed where the model points; drone and LiDAR surveys of chosen catchments.
- [Planned] Offline field app in Assamese; farmers' photo reports sorted by AI and checked by a person; SMS, WhatsApp and voice advisories; an AI assistant for officers.
- [Planned] Wider watch: riverbank erosion, flood sand on farmland, wetland and reservoir silting; landslide and flood forecasts for Assam on the same platform.

What changes: a ranked list with reasons before the survey, refreshed every season, change seen every year, warnings before erosive spells, and findings flowing back so the models improve every monsoon. Users need only a browser; department data plugs in as it is shared.

---

## 3. User journey, wireframes, prototype & proof of work

Prototype maturity: SoilSense already runs as a module of our web app with real state-wide Assam results [Under development]. Its screens cover the erosion map (with the AI view and the soil-reaching-streams view), this week's outlook, the village card, change over time, the priority list with the field kit, "What if we treat it?", and a page explaining the method and its limits. All pass our automated screen checks. Screenshots and wireframes of next screens are in the attached Proof of Work PDF.

Journey 1, a divisional officer planning the season:
1. Opens SoilSense and picks a district.
2. Sees the map, the district's rank, its main cause, the soil reaching its streams and the nutrients it loses.
3. Opens the priority list, sets what matters to the division, and compares measures in "What if we treat it?".
4. Downloads the list, map layers and GPS visit points for the field.
5. [Planned] Receives an April watch list, a seasonal outlook and a district bulletin each season, and can ask an AI assistant questions about the district.

Journey 2, a field team verifying:
1. Loads the GPS points on a phone.
2. Visits the top catchments and records what it sees: rills, gullies, fresh clearing, existing works, with a photo.
3. [Planned] Findings come back through an offline field app, wait in a holding area until an officer checks them, then grade the map and teach the AI.
4. [Planned] Drone surveys of chosen catchments and works, repeated over time to measure change.

Journey 3, a farmer or community member:
1. Is shown or sent a village card: loss around the village, why, what helps, and how bare its slopes were each year.
2. [Planned] Receives it in Assamese, with advisories before heavy-rain spells by SMS, WhatsApp or voice.
3. [Planned] Reports a problem area with a phone photo; AI sorts reports and an officer confirms them.

Proof of work beyond the prototype:
- Two live products on the same backbone in Arunachal Pradesh: a flood forecast that runs every morning in the cloud and grades itself against river gauges, and a landslide forecast learned from tens of thousands of mapped landslides.
- The Assam erosion layer was produced by moving that backbone to a second state, not by starting again.
- Every check was written down before its result existed, then run. Hills come out far above the plains, as they should. The rain factor matches the measured value at Guwahati closely, where the commonly used Indian formula reads far too low. The top-ranked catchments are visibly steep on satellite images. And in a blind check of satellite pictures, labelled before the answer key was opened, squares the map calls severe showed visible erosion clearly more often than squares it calls mild, passing the bar set in advance.

{Demo video URL and product URL, if SoilSense is published before submission.}

---

## 4. Technology & solution architecture

Architecture: sources, a provenance-recorded raw store, one shared 100 m grid, physical and AI models, ranking, change and forecasts, then the web app, GIS feeds and field app, with verified outcomes flowing back to retrain the models.

Backbone: [Under development] every source kept untouched with its licence, link, date and checksum; one grid on Survey of India outlines; a region switch for new states; a daily cloud run with every forecast logged and graded (live for our flood module). [Planned] Outputs stamped with input and code versions; a holding area for field, partner and citizen reports; a sensor path with quality filters.

Models:
- [Under development] RUSLE soil-loss model with a canopy-slope guard; sediment-connectivity model; weekly erosive-rain outlook; gradient-boosted AI trained on ISRO's eroded land, tested on unseen areas, with per-area explanations.
- [Planned] A panel of experts for WHERE and WHEN (rule-based, tree and deep-learning models) blended by a meta-learner; models trained across the Himalaya and North East, fine-tuned for Assam and each district, with local-only models alongside; calibration to real chances and tonnes; retraining after every monsoon; gauge-corrected rain, seasonal outlooks and climate scenarios.
- [Planned] Deep learning that reads satellite, radar and drone images (land cover, jhum, burn scars, hill cutting, gullies); sequence models on sensor streams; AI that turns news and reports into dated events, sorts farmers' photos and answers officers' questions.

Technology stack:
- Language and data: [In use] Python, NumPy, Pandas, SciPy, Numba, Dask, Parquet and Arrow. [Planned] PostgreSQL with PostGIS for field, farmer and sensor records.
- Geospatial and remote sensing: [In use] GDAL, Rasterio, GeoPandas, Shapely, PyProj, Xarray, NetCDF and HDF5; PySheds and scikit-image for terrain and drainage; Google Earth Engine, Copernicus Data Space (openEO) and STAC catalogues for Sentinel-2. [Planned] Sentinel-1 radar processing; Indian archives through Bhoonidhi; QGIS for analysts.
- Machine learning: [In use] scikit-learn, LightGBM, SHAP explanations, spatial block cross-validation. [Planned] PyTorch with convolutional segmentation networks (U-Net type) and pretrained Earth-observation foundation models fine-tuned for Assam; LSTM and temporal models; stacked meta-learners; experiment tracking and a model registry (MLflow); GPU cloud training.
- Weather and climate: [In use] NASA GPM IMERG, Open-Meteo forecasts, Copernicus Climate Data Store (ERA5). [Planned] ECMWF seasonal forecasts and CMIP6 projections.
- Field, drones and sensors [Planned]: IoT rain, water-clarity and soil-moisture sensors over GSM or LoRaWAN with MQTT ingest; drone photogrammetry (OpenDroneMap) and LiDAR point clouds (PDAL); an offline Android data-collection app.
- Apps and delivery: [In use] Streamlit web app with Leaflet (Folium) maps, PDF reports, Playwright screen tests. [Planned] FastAPI REST API; OGC map services (GeoServer WMS and WMTS) for ASSAC and the state geoportal; SMS, WhatsApp and voice gateways; an LLM-based officer assistant.
- Infrastructure: [In use] serverless cloud jobs in India (Modal), scheduled daily runs, Git version control. [Planned] Docker containers, government-empanelled hosting, monitoring and alerting.
- Outputs: GeoTIFF and Cloud-Optimised GeoTIFF, GeoPackage, KML, GeoJSON, CSV and PDF, opening directly in QGIS and ArcGIS.

---

## 5. Development methodology & intermediate steps

We work in short, checked steps. Every step has a written "done when", every test has its pass mark written down before the result exists, and every result, failures included, goes into a permanent log. Features that do not pass are held back, not shown.

1. Discovery and requirements [Under development]. Every line of the problem statement mapped to a feature; every assumption checked against research and the data. This caught errors in widely used inputs before any result existed.
2. Backbone moved to Assam [Under development]. Region switch, grid, official outlines, terrain, drainage, soil and land-cover layers, each with provenance.
3. Physical model and pre-registered checks [Under development]. Rain, soil and slope factors checked against measured and published values; where a check failed, we fixed or marked the result, never tuned it.
4. Ranking, app and decision tools [Under development]. Ranked catchments with causes and firmness, village card, "What if we treat it?", soil reaching streams, nutrient value, field kit.
5. First AI and outside checks [Under development]. AI map trained on ISRO's eroded land and tested on unseen areas; a blind satellite-picture check judging both the formula and the AI; the outlook replayed over past monsoons. Some early features (clearing alerts, river-sediment forecasts, heavy-week warnings) are held back until they pass: field data and sensors unlock them.
6. Phase 1, Nov–Dec 2026 [Planned]. Satellite-reading AI; radar monitoring; alerts with an AI second check; seasonal outlook; the panel-of-experts framework with the formula, tree and first deep-learning members; Himalaya and North-East pooled training data assembled.
7. Phase 2, Dec 2026–Feb 2027 [Planned]. field-check protocol agreed with the department; offline Assamese field app; "did the works help?"; pre-monsoon watch list; daily automated run with every outlook logged and graded; Demo Day build.
8. Phase 3, Feb–May 2027 [Planned]. Field testing at chosen sites: sensors, plots and drone surveys; department data swapped in, each with a before-and-after comparison; models fine-tuned for Assam and its districts and calibrated on field and plot data; works planner; layers into the department's GIS; training.
9. Continuous improvement [Planned]. After every monsoon: new field findings, sensor records and imagery come in; every panel member is retrained and re-graded; the referee is re-fitted as proof data grows; weaker members are kept and re-tested rather than dropped. Then scale-up: statewide seasonal cycle, advisories, other hazards and other North-East states.

---

## 6. Development timeline & milestones

Aligned with the NESFIC programme calendar.

Done, October 2026 [Under development]: Assam on the backbone; state-wide 100 m erosion map with pre-registered checks; ranked catchments and districts with causes and firmness; AI erosion map as a second opinion; blind satellite-picture validation; dry-season bare ground since 2019; weekly outlook graded on past monsoons; village card; "What if we treat it?"; soil reaching streams; nutrient value of lost soil; field-kit exports; all in a working web app.

November 2026, Conclave [Planned]: live demo on Assam data.

November to mid-December 2026, Phase 1, AI and monitoring [Planned]:
- Satellite-reading AI for forest, tea and jhum; jhum burn dating; radar monitoring.
- Change alerts with an AI second check; seasonal outlook; district bulletins.
- Panel-of-experts framework; pooled Himalaya and North-East training data.
Depends on: satellite processing quota; any department data shared.

Mid-December 2026 to February 2027, Phase 2, prototype [Planned]:
- Field-check protocol agreed with the department and dated before any visit.
- Offline Assamese field app and village card; citizen and field intake with a holding area.
- "Did the works help?"; pre-monsoon watch list; daily automated run with every outlook graded.
Depends on: the department's choice of test areas and class scheme.

February 2027, Demo Day: working prototype, early results, plan to MVP.

February to May 2027, Phase 3, MVP [Planned]:
- Field testing against pass marks set in advance.
- Stream sensors, rain gauges, soil-loss plots and drone surveys at chosen test sites.
- Department data in; models fine-tuned for Assam and its districts and calibrated.
- Works planner; layers in the department's GIS; staff training.
Depends on: data-sharing permissions; field access.

From June 2027, pilot validation (section 12), then scale-up [Planned]:
- First pre-monsoon watch list issued before the 2027 monsoon, then every year.
- Retraining after every monsoon; statewide seasonal refresh.
- SMS, WhatsApp and voice advisories; farmers' photo reports; AI assistant for officers.
- AI gully finder on drone imagery; sensor-based river-sediment outlook.
- Riverbank, sand-cast farmland and reservoir-silting watch; landslide and flood forecasts for Assam; other North-East states.

Ready for validation: the prototype by February 2027 and the MVP by May 2027.

---

## 7. Data & information requirements

The working prototype was built entirely on open data, so nothing depends on unconfirmed access. Department data improves SoilSense; it is not a precondition.

In use, open, licence checked and provenance recorded [Under development]:
- Copernicus elevation model; SoilGrids soil properties; ESA WorldCover land cover.
- Satellite rain-erosivity maps (IIT Roorkee, IIT Delhi); HydroSHEDS channels and catchments.
- Survey of India state and district outlines.
- Sentinel-2 imagery for bare ground each dry season.
- NASA satellite rain and forecast rain for the outlook and its grading.
- CWC river-sediment and river-level records.
- NRSC Land Degradation map: training labels for the AI and an outside check, never redistributed.

Planned open and public sources [Planned]: Sentinel-1 radar; seasonal forecasts and climate projections; geotagged MGNREGA and PMKSY watershed works on Bhuvan; Soil Health Card statistics; erosion, landslide and land-degradation records from across the Himalaya and North East for pooled AI training; dated events read from news and public reports.

Requested from the department, ASSAC and line agencies (not yet confirmed; the plan works without them) [Planned]:
- Field observations of erosion with location and date.
- Treated areas and works; schedule of rates.
- Soil survey, soil-loss classes and planning units (micro-watersheds).
- High-resolution imagery, elevation data or LiDAR via ASSAC; Indian satellite archives through Bhoonidhi.
- Rain-intensity records (IMD, ASDMA) and river-flow records (CWC).
- Forest, tea-garden and sand-mining boundaries; road-damage and silt-clearance logs (PWD).
- Formats accepted: shapefile, GeoPackage, KML, CSV or Excel with coordinates, scanned maps.

Data we will generate ourselves [Planned]: sensor readings (rain, water clarity, soil moisture), soil-loss plot measurements, drone and LiDAR surveys, lab soil tests, verified field and farmer reports, and our own graded record of every forecast issued.

Processing and annotation:
- Satellite composites cloud-masked, with cloud cover recorded.
- AI labels made blind and checked on held-out areas and districts; pooled regional data kept separate from local data so each model's source is known.
- Sensor streams filtered for spikes, drift and dropouts before use.
- Field, farmer and partner records stay in a holding area until verified.

Assumptions stated plainly:
- National rain-erosivity maps disagree on where rain is most erosive, so ranks are tested under more than one.
- The satellite "tree" class mixes forest, tea and jhum fallow until the satellite-reading AI splits it.
- Tonnes are estimates until calibrated by soil-loss plots; rankings are the lead output.

---

## 8. Team, manpower & expertise

{Confirm names, roles and qualifications before pasting; up to five members.}

Team:
- {Nabam Changriang}, Co-founder and CEO, partnerships and programme. Government and community engagement in the North East. Department liaison, field-test and data-sharing agreements, reporting.
- Pankaj Kar, Co-founder and COO, Lead Applicant, operations and field. Field logistics and teams, sensor and plot installation, drone survey coordination, village outreach.
- {Sonit Saikia}, Co-founder and CTO, technical lead. Geospatial data pipelines, satellite and terrain processing, machine learning and forecasting, web apps. Built the platform's data backbone and its live flood and landslide forecasts. Leads the erosion model, AI panel, monitoring, outlooks, app and validation design.
- {Member 4}, GIS and remote-sensing analyst. Optical and radar satellite processing, AI training labels, field kit, GIS support for the department.
- {Member 5}, soil-conservation or agronomy adviser. Treatment choices, class scheme, field protocol, soil-plot design.

Indicative manpower by development phase, in person-months {to confirm}:
- Phase 1, Nov–Dec 2026 (AI and monitoring): technical 1.5, analyst 1.5, field 0.25, adviser 0.25.
- Phase 2, Dec 2026–Feb 2027 (prototype): technical 2.5, analyst 2, field 0.5, adviser 0.5.
- Phase 3, Feb–May 2027 (MVP and field testing): technical 3, analyst 3, field 2, adviser 0.5.
- After May 2027 (pilot validation): to be planned with the department.

Critical skills and where they come from:
- Remote sensing, terrain analysis, machine learning and deep learning: in the team.
- Honest validation design (tests written before results, held-out checks, graded forecasts): in the team, used daily on our live products.
- Soil-conservation practice in Assam's hills: our adviser and the department's officers.
- Sensors, drones, LiDAR and soil-loss plots [Planned]: field partners or hired specialists for installation and flying; data handling in the team.
- Assamese for the field app, village cards and advisories [Planned]: in the team or a local partner.

Track record:
- The team built and runs a data backbone of many open sources and two live daily forecasts for Arunachal Pradesh, one of which grades itself every day.
- It moved that backbone to Assam and produced a state-wide erosion layer, an AI model, a blind validation and a working app within weeks.
- Every test, passed or failed, is logged and reported.

---

## 9. Testing, validation & evidence

How we test: every check is written down, with its pass mark, before the result exists. A failed check means "investigate", never "tweak until it passes". Every result goes into a permanent log, failures included, and features that fail are held back from users.

Evidence on Assam so far [Under development]:
- Physical sense: hills come out far above the plains, as required by the bar set in advance.
- Rain factor: matches the measured value at Guwahati closely; the commonly used Indian formula, rejected, reads far too low there.
- Soil factor: agrees closely with India's published soil-erodibility map.
- Top-ranked catchments: visibly steep on satellite images.
- Blind picture check: satellite pictures labelled before the answer key was opened; squares the map calls severe showed visible erosion clearly more often than squares it calls mild, passing the pre-set bar.
- AI map: tested only on map areas it never saw; it matches ISRO's eroded land far better than the formula, but on the blind pictures it did no better, so it is shown as a second opinion, not a replacement.
- Weekly outlook: replayed over past monsoons against satellite rain; it picks the erosive weeks and the heavy weeks well, and is weaker on exactly where within a week, so it is read regionally.
- Rank firmness: every rank recomputed many times across the uncertain inputs; firmness is shown beside each rank.
- Held back until they pass: early clearing alerts, heavy-week warning text, a terrain-only gully flag, and river-sediment forecasts from open data, which need sensors and river flow.

Validation plan [Planned]:
- AI panel: every model tested on held-out areas, held-out years and held-out districts; a model stays only if it improves the whole panel; the referee kept simple until proof data grows.
- Fine-tuned models (Himalaya to Assam to district) checked against local-only models on the same held-out data.
- Calibration: scores turned into chances and tonnes only on data the models never trained on.
- Satellite-reading AI tested on blind, dated pictures before adoption.
- Every outlook and alert written down before the week and graded after it, automatically.
- Field checks during development: protocol agreed with the department and dated before any visit; blind points across risk classes; teams record erosion signs without seeing the map; pass marks set in advance.
- Soil-loss plots and stream sensors: the first direct measure of soil leaving the slopes, used to calibrate the map.
- "Did the works help?": treated sites compared with similar untreated ones each season.
- Retesting after every monsoon, with results published in the log.

Performance measures: field confirmation of top catchments; alert catch and false-alarm rates; outlook skill; measured against estimated loss at plots; each model generation against the last.

Prior evidence: the same backbone runs a flood forecast that grades itself daily against river gauges, and a landslide forecast whose high-risk ground matches mapped landslides well.

---

## 10. Security, privacy, safety & compliance

Security:
- [Under development] The web app is read-only; viewing maps needs no account, and there are no passwords or payments.
- [Under development] Automated jobs run on cloud servers in India; keys are kept out of the code.
- [Planned] Department data in access-controlled storage, used only for this purpose, never published, deleted or returned on request.
- [Planned] Role-based logins for department users, the field app and private layers; encrypted transfer; an API with authentication, rate limits and a versioned contract.
- [Planned] A security audit and government-empanelled hosting before department-wide use.

Privacy:
- The erosion layer holds no personal data. It describes land, not people or owners.
- [Planned] Field and farmer reports hold a location, date, observation and optional photo; names and phone numbers are optional, collected with consent, never shown publicly, and deleted on request.
- [Planned] Advisories by SMS, WhatsApp or voice only to people who opt in, through the department's channels.
- Community material stays at village or catchment level, never plot or owner level.

Safety and human review:
- SoilSense is decision support, not an automatic decision. It ranks where to look first; the department verifies in the field before any works are planned.
- Every figure is labelled with the kind of number it is (measured, estimate, rank, AI view, outlook), and limits are written on the screen.
- AI outputs are always shown beside the transparent formula, with their reasons, and adopted only after passing tests written in advance.
- [Planned] Field, farmer, partner and AI-sorted reports wait in a holding area until an officer checks them, so no single report can change the map.
- [Planned] Sensor readings pass quality filters for spikes, drift and dropouts before any model uses them.
- [Planned] Alerts go out only for features that passed their tests, and only after an AI second check.
- [Planned] Sensors, plots and drone flights only with landowner and community consent, away from homes and paths.

Auditability:
- Every raw file keeps its source, licence, link, date and checksum.
- Every provisional choice is listed with what would change it.
- Every check and result is logged; [Planned] every output stamped with its inputs and code version, so any past map or forecast can be rebuilt.

Licences and IP:
- Open data used within its licence and credited; sources with no licence or a non-commercial licence used only for comparison and never redistributed.
- NRSC polygons used to train and check our model, never redistributed.
- Google Earth Engine and Copernicus Data Space used under their terms; software is open source.

Interoperability: open formats, standard projections and LGD district codes; [Planned] map feeds and an API for ASSAC and the state geoportal.

Regulatory: Survey of India outlines; personal data handled under the DPDP Act 2023; [Planned] drone flights under India's drone rules with required permissions.

---

## 11. Innovation & differentiation

Existing alternatives: national and global soil-erosion maps, ISRO's land-degradation atlas, one-off academic studies of single basins, and the department's own field surveys. All are static: made once, at coarse scale, with no ranking, no reason, no forecast and no feedback.

What is new in SoilSense:
1. One data backbone, many hazards. The same pipeline already runs live flood and landslide forecasts in Arunachal Pradesh; moving it to Assam took a region switch, not a rebuild. Every new data source, sensor or field record improves every module at once. [Planned] Landslides and floods for Assam, riverbank erosion, and other North-East states on the same base.
2. A living layer, not a one-off map. [Under development] Bare ground measured every year and a weekly erosive-rain outlook from the live forecast. [Planned] Radar monitoring through monsoon cloud, AI-checked change alerts, seasonal outlooks and an April watch list.
3. AI that is layered, plural and honest. [Under development] An AI model beside the transparent formula, with its reasons, judged by a blind satellite-picture test before any claim. [Planned] A panel of different models blended by a referee; models learned across the Himalaya and North East and fine-tuned for Assam and each district, with local-only models kept alongside; calibration to real chances and tonnes; retraining after every monsoon.
4. A ranked work list with the reason and the payoff. [Under development] Each catchment's cause, rank firmness, soil reaching its streams, nutrients lost and soil saved by each measure. [Planned] Works planner with costs, scheme-ready outputs for PMKSY and MGNREGA, and "did the works help?" tracking.
5. A loop that makes its own ground truth. [Under development] Forecasts written down and graded, the method already running daily for our flood module. [Planned] Field, farmer and partner reports through a holding area; every verified record becomes training and test data no one else has.
6. Measured truth at the source. [Planned] Sensors and soil-loss plots placed where the model points, plus drone and LiDAR surveys, giving the first direct measurements of soil leaving Assam's hill slopes.
7. Reaching people. [Under development] A village card for any place. [Planned] An offline Assamese field app, SMS, WhatsApp and voice advisories, and an AI assistant for officers.
8. Wider value [Planned]: flood sand on farmland as relief evidence, wetland and reservoir silting, and soil-carbon projects that could bring outside funding for treatment works.

IP and dependencies:
- Ours: the backbone and region switch, ranking and cause logic, AI models and training pipeline, the validation framework, the app, and the checked local records built each season. Code can be copied; seasons of checked local history cannot.
- Third party: open-source software (Python geospatial stack, LightGBM, Streamlit, Leaflet); open data (Copernicus, SoilGrids, WorldCover, Sentinel, NASA rain, national erosivity maps, HydroSHEDS, Survey of India), all credited; Earth Engine and Copernicus Data Space as services.
- Method: RUSLE is a public standard; our contribution is how it is fed, checked, ranked, explained, forecast and kept current.

---

## 12. Resources, risks & pilot validation

Indicative cost heads for the MVP & Prototype grant {amounts to confirm with the COO}:
- Team time: technical build, AI development, remote-sensing analysis, field coordination.
- Field testing and pilot work: travel, local guides, phones and GPS, community sessions in Assamese.
- Field instruments at test sites [Planned]: rain gauges, water-clarity and soil-moisture sensors, simple soil-loss plots.
- Drone surveys of chosen catchments and lab soil tests [Planned].
- Cloud computing, storage, satellite processing and hosting.
- Contingency.
Larger items (high-resolution commercial imagery, LiDAR, statewide messaging, government-grade hosting) are planned for the scale-up phase with department or partner funding.

Key risks and mitigations:
- National rain-erosivity maps disagree: ranks tested under more than one and firmness shown; [Planned] ground gauges and test-site rain sensors correct satellite rain.
- The satellite "tree" class mixes forest, tea and jhum: [Planned] satellite-reading AI split, adopted only after a blind test; forest and tea-garden boundaries if shared.
- Tonnes are uncalibrated: rankings lead; [Planned] plots and sensors calibrate.
- Too few local examples for AI: [Planned] pooled Himalaya and North-East training, fine-tuned locally; simple referee until proof data grows; field and farmer reports add examples every season.
- AI learns the wrong thing: AI always shown beside the formula, tested on unseen areas and blind pictures, adopted only after passing.
- Monsoon cloud: [Planned] radar satellites; cloud recorded, gaps marked.
- Canopy distorts slope: guard in place; [Planned] bare-earth elevation via ASSAC, drones or LiDAR.
- Features failing their tests: held back until field data and sensors let them pass.
- Department data arrives late: the plan runs on open data.
- Field access in hill districts: dry-season fieldwork with local guides and department staff.
- Sensor damage or faulty readings: community consent, robust instruments, automatic quality filters.
- RUSLE cannot model gullies, landslides or riverbank cutting: those areas are marked; [Planned] gully finder, riverbank watch and our landslide module.

How the solution will be pilot-validated [Planned]:
- Where: Dima Hasao and Karbi Anglong, plus one foothill belt {to agree with the department}.
- How: a field protocol agreed with the department and dated before any visit; blind points across risk classes and top catchments; teams record erosion signs without seeing the map; pass marks set in advance.
- Measured: plots and sensors give real soil-loss and sediment numbers; drones map gullies and treated works.
- Learned: verified findings fine-tune and calibrate the models, tested on held-out areas and districts.
- Outcome for the department: a validated, ranked list for the pilot districts, layers in its own GIS, a seasonal refresh and April watch list, and a tested path to the whole state.

---

## Word counts (excluding {curly} notes)

- 1. Problem understanding & user workflow: 400 words
- 2. Proposed solution & key features: 463 words
- 3. User journey, wireframes, prototype & proof of work: 469 words
- 4. Technology & solution architecture: 484 words
- 5. Development methodology & intermediate steps: 390 words
- 6. Development timeline & milestones: 355 words
- 7. Data & information requirements: 399 words
- 8. Team, manpower & expertise: 353 words
- 9. Testing, validation & evidence: 486 words
- 10. Security, privacy, safety & compliance: 478 words
- 11. Innovation & differentiation: 492 words
- 12. Resources, risks & pilot validation: 431 words
