# Who else is doing this, and why us

> Checked on the web on **2026-11-04**. Behind the "How are you different?" answers in
> `docs/lrn/phase-7-defend.html` §8 and its "Who else" grilling tab. Re-check before a
> big meeting: these programmes move every season.
>
> Related: COMPETITOR_IIOTS.md, COMPETITOR_ALERTIS.md, FLOOD_HUB_AND_MOCKUP_COMPARISON.md,
> BEYOND_PRESENTATION.md §2.3, §2.4, §8.8, §9.11, §9.12, §13.2, §13.3.

## The one-line answer

Each of them does one part, often better than we do: a district bulletin, a river
station, a watershed weather threat, one slope's sensors, a global model, a map after
the event. **None does all of these together for Arunachal: the whole state every day,
landslides and floods, seven days ahead, with the score shown, on one base that makes
the next hazard cheap.** The joining is the product. Never say "nobody else does this".

## Government

| Who | What it does (as published) | What it leaves open | How we fit |
|---|---|---|---|
| **GSI, National Landslide Forecasting Centre** (Bhusanket portal, Bhooskhalan app; opened 2024) | District bulletins for today and tomorrow, from IMD/NCMRWF rain forecasts + GSI susceptibility maps + rain thresholds. 2025: 21 districts in 8 states (4 operational, 17 experimental). Prototype came from the UK–India LANDSLIP project. | Its own rules: **≥10 years of dated landslides** to set a threshold, **≥3 monsoons** experimental (bulletins "not for public use") before going public. NE plan: 6 districts public by 2028, 18 by 2030, the rest from 2030. **Arunachal on the list: Itanagar only.** GSI's own slide: Arunachal has **26,451 landslides, 58 with dates**. | We work the rest of the state now, with a method that needs no fitted threshold (the per-place "how unusual is this rain" rule, 0.768 on 72 events). Every dated slide we find can go back to them. |
| **GSI, national susceptibility maps** (1:50k, ~4.34 lakh km², 181 districts) | A fixed **where** map. | The same in January and August: no **when**. | We use it as a cross-check, not an input (§2.4). Keep our side-by-side numbers back. |
| **CWC flood forecasts** | ~350 stations nationally (~200 level + ~150 inflow; counts differ by year and source), forecasts up to ~24 h, longer advisories, official danger levels. | Places away from a forecast station; small hill rivers. | We read the same public gauges, plus 14 NWDP small-river gauges: a chance for each of the next 7 days at all 32, an outlook away from gauges, a public score. |
| **IMD**: rain warnings + **South Asia Flash Flood Guidance System** | Flash-flood threat by watershed, hours to about a day; regional advisories up to 36 h since Sept 2020. | It forecasts the weather threat, not which slope or river reach is loaded. GSI's slide: 73 IMD weather stations in Arunachal's landslide-prone hills, **about 1 per 960 km²**. | Weather is our input. IMD ground rain is on our ask list. |
| **NESAC, FLEWS** (with ASDMA, since 2009) | Flood alerts for **Assam** by revenue circle; the first GIS hydro-met warning system in India. | Assam's plains, not Arunachal's hills. | Our hills are Assam's upstream. Our hill gauges and forecasts *could* be an input to them (idea, nothing agreed). |
| **NDMA** programmes | Landslide risk mitigation (NLRMP); **GLOF programme, ₹150 crore, 4 states including Arunachal**. | Funding and hardware programmes; someone still has to say where first. | The backbone can rank which slopes, rivers and lakes come first. **We have no lake-burst forecast.** |
| **APSDMA** | Tawang GLOF work (news, late Oct 2026): bathymetry training; preparing water-level recorders, satellite-linked sirens, high-altitude weather stations. | Sensors on chosen lakes. | Same as NDMA. Glacial-lake maps (NWIA) are on our APSAC ask. |
| **ISRO / NRSC / Bhuvan** | Satellite flood maps after events; landslide inventory. | After the event, not before. | We use the inventory. We tested the Bhuvan flood mask: 70.5% of its flooded pixels sit on slopes over 15°. **For our ears only**, never as an attack. |
| **ISRO / NRSC, NDEM** (National Database for Emergency Management) | A national geo-portal: a multi-scale geospatial database with decision-support tools, sharing space-based inputs and forecasting agencies' services for all disasters; mirrored at MHA. | A national shelf for emergency managers, not one state's daily landslide-and-flood forecast with a graded record. | "NDEM is the national shelf; we're one state's workshop." It could be one place our forecast is shown. Its Arunachal layers weren't checked in detail: don't claim what it lacks. |
| **NWIC, India-WRIS** | The national water-data portal: static and live rainfall, reservoir, river-point, soil-moisture and groundwater data. NWDP (our 14 small-river gauges) is in the same family. | Publishes readings; doesn't turn them into a per-river forecast with a score. | A source we thank. |

## Research and sensors

| Who | What it does | Difference | Careful |
|---|---|---|---|
| **IIT Mandi LEWS** (Prof. Dericks P. Shukla's group; launched **8 Jul 2026**) | Daily landslide forecast for the **whole Indian Himalayan Region**. ~26,000 GSI landslides → susceptibility map (ensemble ML). NASA Global Landslide Catalogue + 7 IMERG rain measures over 15 days → "P-RIL" trigger. Combined, shown in percentile classes. Earth Engine portal (today + the past 3 days), PDF bulletins, WhatsApp alerts. | **Closest to us in method**: same public inputs. Ours: **7 days ahead** on forecast rain (their portal shows today and the past 3 days); floods and erosion on the same base; test scores and the daily record on screen (tested on unseen 50 km blocks; "× the usual" measured on 84 slides). | We have not seen their test numbers or map resolution published. Say "we haven't seen", never "they don't". The portal did not load for an automated check on 2026-11-04, so **open it yourself before a meeting** and note what it shows for Arunachal. Not the same team as iIoTs. |
| **iIoTs / Intiot** (IIT Mandi spin-off) | Sensor boxes on ~60 chosen slopes. Kotropi 2018 save. | One slope minute by minute vs the whole state daily. | COMPETITOR_IIOTS.md. |
| **Alertis** (Dehradun) | Sensor pods, landslide + flood + fire; founded Oct 2025. | No proof shown yet. | COMPETITOR_ALERTIS.md. |
| **Amrita University, CBRI and others** | Sensor-based landslide warning on chosen sites (named in NDMA's NLRMP). | Same as the sensor rows. | Complementary. |

## Regional and UN (added 2026-11-05)

| Who | What it does | Difference | Careful |
|---|---|---|---|
| **ICIMOD, SERVIR-HKH** | Flood early warning for the Hindu Kush Himalaya: downscaled global flood discharge forecasts with routing models give water levels in flood-prone river stretches, 10–15 days ahead; community-based flood early warning (CBFEWS). | A regional programme through partner countries and pilot rivers; we work block by block on one state, from its own gauges, with landslides on the same base. | Where SERVIR runs operationally wasn't checked: never say it "doesn't cover" Arunachal. |
| **UN, Early Warnings for All** | The goal of early-warning coverage for everyone by 2027, on four pillars: risk knowledge; monitoring and forecasting; warning dissemination; preparedness and response. | A goal and framework, not a forecast. | We sit in the first two pillars; warning and response stay with the authorities. |

## Big companies

| Who | What it does | Difference |
|---|---|---|
| **Google Flood Hub** | River model 7 days ahead, worldwide; a level model at gauged big rivers in India (8–48 h). **Flash-flood model**: 20 km × 20 km squares, next 24 h, only in cities or places with a flood history, trained on "Groundsource" (news reports turned into flood records with Gemini). Not lake bursts or dam failures. Flood model open-sourced June 2026; the API is mostly non-commercial. | In Arunachal's hills, river points are model-only and "lower-confidence… for expert use". Pasighat showed only the past week when we checked (28 Sep). We read 32 real gauges each morning, including 14 small rivers. Their model is a planned second opinion beside ours. |
| **IBM–NASA Prithvi, NVIDIA Earth-2, Google DeepMind weather models** | Open "engines": foundation models for satellite images (flood, burn-scar, landslide mapping) and for weather. | Engines, not a district forecast. Each still needs local labels, local gauges and local tests, which is what the backbone holds. We don't use them today. Any of them can join the panel if it improves the whole panel (ENSEMBLE_STRATEGY.md). |
| **Insurance catastrophe models: Moody's RMS, Fathom** (checked 2026-11-05) | Moody's RMS sells an India Inland Flood Model (fluvial and pluvial; 125,000 events across 9,033 catchments) to insurers; Fathom (acquired by Swiss Re) sells global flood maps to insurance, finance, engineering and the public sector. | Built to price long-run risk over many simulated years, not to say what a district officer should watch this week. Their maps are validated on insured losses: never call them wrong, say they do a different job. |
| **Climate-risk analytics: e.g. Jupiter Intelligence** (checked 2026-11-05) | Risk scores for any address worldwide under emissions scenarios, built for banks' and companies' financial decisions. | Decades ahead for finance, not days ahead for an officer. |

## Indian companies

| Who | What it does | Difference |
|---|---|---|
| **Vassar Labs** and similar | AI flood forecasting and disaster platforms for state governments, basin by basin (e.g. Kerala's Periyar flood warning system). | Usually built to a tender, one basin or hazard at a time. Ours is already running in Arunachal on its own landslides and rivers. If a state picks an integrator, our feed can sit inside its platform. They have a delivery record we don't: say so. |
| **Satellite analytics startups** (e.g. Suhora) | Flood and damage maps from radar satellites, after the event. | After, not before. Their maps are exactly what we learn from: each mapped flood can become a verified record. |
| **Private weather companies** (e.g. Skymet) | Rain and weather forecasts sold to farmers, insurers and media. | They forecast the rain, not what it does to a slope or river: a possible supplier, not a rival. Not researched in detail. |

## Why should they let us do it?

1. **It's already running.** You judge a working thing, not a proposal.
2. **Nothing to buy to start.** It runs on free data. The asks are records, i.e. letters, not money. *No price or "free forever" until agreed with the CEO.*
3. **The warning stays theirs.** We give the forecast; the authority decides.
4. **Records stay on their terms.** Source and terms stay attached; use is agreed in writing (the holding area is designed, not built).
5. **A fair, pre-agreed test.** One district, one monsoon, yardsticks chosen before it starts (for example hit rate and false-alert rate, the measures GSI itself uses). Judge us on the score.
6. **It fills the gap their plans leave**, and hands back what it finds: dated slides, cleaned gauge records, the graded record.
7. **It doesn't lock them in.** The backbone can feed their own systems (Bhusanket, SACHET, a state dashboard). The open feed is planned, not built.

## Projects we don't know about

Never claim to know everything, least of all internal work. Ask back: "What's running? If
something already covers this, we'd rather feed it than copy it." Then three checks:
does it cover the whole state every day, does it look days ahead, does it show its
score? Where it does all three, we plug in. Where it doesn't, that's our place. Take the
name and follow up in writing.

## Weak spots against all of them (say them before they're found)

- No mandate: we're not an authority, and must never sound like one.
- No live monsoon yet: the record began 21 Sep 2026, as the rains ended.
- Landslide forecasts are written down but not yet graded live (dated slides come too slowly).
- Small team; years of trust are on their side.

## Sources (opened 2026-11-04)

- GSI, "Landslide and forecasting scenario in North Eastern Region" (DDG Dr. Saibal Ghosh), mines.gov.in/admin/storage/ckeditor/9_1751275999.pdf: status table, NE plan 2026–30, KPIs, dated-landslide and IMD weather-station tables.
- PIB PRID 2034433 (NLFC, Bhusanket, Bhooskhalan launch); GSI posts on 21 districts (4 operational, 17 experimental).
- IIT Mandi press release, 8 Jul 2026: iitmandi.ac.in/pdf/pressreleases/Press_Release_IIT_Mandi_Develops_Operational_Landslide_Early_Warning_System_for_the_Indian_Himalayan_Region.pdf; portal dexter-499110.projects.earthengine.app/view/lews.
- Google Flood Hub help, "How does the Flash Flood Model Work?" (support.google.com/flood-hub/answer/16811681).
- WMO, "South Asia Flash Flood Guidance System Launched".
- NESAC, Disaster Management Support page (FLEWS).
- PIB PRID 2117268 (NGRMP: ₹150 crore; Arunachal, Himachal, Sikkim, Uttarakhand).
- PIB PRID 1947578 and SANDRP (CWC station counts).
- Northeast Live / APSDMA posts, late Oct 2026 (Tawang GLOF preparedness).
- vassarlabs.com (Kerala Periyar flood warning system).
- NASA/IBM Prithvi pages; NVIDIA Earth-2 page.
- NDEM: https://ndem.nrsc.gov.in/ · https://www.isro.gov.in/DBEM.html (opened 2026-11-05)
- India-WRIS: https://indiawris.gov.in/wris/ · NWIC India-WRIS training PDF (opened 2026-11-05)
- ICIMOD SERVIR-HKH flood early warning: https://servir.icimod.org/science-applications/enhancing-flood-early-warning-systems/ (opened 2026-11-05)
- Moody's RMS flood models: https://www.moodys.com/web/en/us/capabilities/catastrophe-modeling/flood-models.html (opened 2026-11-05)
- Fathom: https://www.fathom.global/ · Jupiter Intelligence: https://www.jupiterintel.com/ (opened 2026-11-05)
