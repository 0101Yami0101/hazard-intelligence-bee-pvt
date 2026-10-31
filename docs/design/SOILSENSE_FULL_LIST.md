# SoilSense — everything, by tier (FREE / ASK / PAID)

Written 2026-10-29. One list of everything SoilSense does, plans, or could do: built, tested,
planned in [ROADMAP_EROSION.md](ROADMAP_EROSION.md) (AD-xx), and new ideas not yet in any doc
(marked **new**).

**The tiers:**

- **FREE**: open data and our own work.
- **ASK**: needs a government body's data or permission.
- **PAID**: needs a budget (hardware, imagery, services, people).

**Status marks:** ✅ in the app · 🧪 built, tested and failed/parked · 🛠 built, not in the app
· 📅 planned · 💡 new idea.

## FREE: open data and our own work

### Maps and rankings

| | Item | What it gives |
|---|---|---|
| ✅ | Erosion map, 100 m, all Assam | Tonnes per hectare a year, six classes |
| ✅ | Priority list (703 catchments, 35 districts) | Reasons, firmness from 1,000 runs, custom weights |
| ✅ | AI erosion map (second opinion) | Learned from ISRO's map; no better than the formula on the ground |
| ✅ | Soil reaching streams | Where check dams pay most |
| ✅ | Value of soil lost | Nitrogen as urea bags and ₹, topsoil mm |
| ✅ | Bare ground every dry season, 2019–26 | Change over time |
| ✅ | Village card | One place, everything, printable |
| ✅ | "What if we treat it?" | Soil saved per measure |
| ✅ | Field kit | GPS points, KML, GPX, GeoPackage |
| 📅 | Satellite-reading AI: forest / tea / *jhum* / grove / fresh clearing (AD-08) | Settles the biggest uncertainty (after 1 Nov) |
| 📅 | AI second look at "newly cleared slope" alerts (AD-09) | Revives the held-back alerts |
| 📅 | Our own dated erosion labels from satellite pictures | Better examples for the WHERE AI |
| 📅 | *Jhum* cycle tracker: cleared, burnt, left fallow, by year | Shifting cultivation hotspots |
| 📅 | Post-monsoon season; official micro-watershed units (AD-15) | Matches the department's planning units |
| 📅 | Uncertainty shown per unit (a range, not one number) | Honest maps |
| 💡 | Burn scars (Feb–Apr) from Sentinel-2 | Dates each *jhum* burn, just before the rains |
| 💡 | Radar (Sentinel-1) through monsoon cloud | Sees fresh bare ground and slips when optical can't |
| 💡 | Hill-cutting watch, Guwahati and towns | Red-earth cuts that silt city drains and cause waterlogging |
| 💡 | Sand-mining and brick-kiln spotting | Disturbed river and flood land |
| 💡 | Road-cut erosion along hill roads (OSM roads × slope) | PWD / PMGSY maintenance hotspots |
| 💡 | Sand-cast farmland after floods (Brahmaputra) | Fields buried by flood sand: relief and compensation evidence |
| 💡 | Beel and wetland siltation (Deepor Beel etc.) | Which wetlands are filling up and from where |
| 💡 | Reservoir silting (Kopili, Karbi Langpi, Umiam inflow) | Years of storage lost; hydropower relevance |
| 🧪 | Gully-prone flag (terrain only) | No better than other sloping land |
| 🧪 | "Newly cleared slope" alerts | Too many false flags; held back |

### Forecasts

| | Item | What it gives |
|---|---|---|
| ✅ | Weekly erosive-rain outlook | Tested: good at *when*, weak at *where* |
| 🧪 | River-mud forecast (WHEN), four attempts | Failed: no flow data, one sample a day |
| 🧪 | River colour from satellite as a mud record | Too weak once the season is removed |
| 🧪 | Heavy-week warning text | Caught 1 in 3 heavy weeks |
| 📅 | Warning retry: cut set on 2024, judged on 2025 | Could pass on unseen weeks |
| 📅 | Sharper rain (IMERG 10 km, 2013–26) for the outlook | Download in bursts (NASA limits us) |
| 💡 | Seasonal outlook, 1–3 months (ECMWF seasonal, free via Copernicus) | "This monsoon looks wetter than usual": plan works before June |
| 💡 | Pre-monsoon watch list: barest steep catchments × the coming season's rain | One list for divisions each April |
| 📅 | Climate-future view, 2030s and 2050s (CMIP6) (AD-32) | Scenario, not forecast |

### Tools for officers

| | Item | What it gives |
|---|---|---|
| 📅 | District bulletins, an automatic PDF each season (AD-29 in the beyond list) | Hand-out for meetings |
| 📅 | Works planner: catchments + measures → quantities (AD-25 in the beyond list) | Draft plans; costs need the department's rates |
| 📅 | Scheme-ready outputs for PMKSY watershed and MGNREGA (AD-33) | Fits existing funding |
| 📅 | Map feeds: WMS / API to ASSAC and the state geoportal (AD-30 in the beyond list) | Their GIS reads ours |
| 📅 | Offline / low-data mode; Assamese wording | Field use |
| 📅 | Open method note and validation report; a paper (AD-36) | Credibility |
| 💡 | "Did the works help?" from **public** MGNREGA geotagged assets (Bhuvan) | Before/after bare ground and loss at treated sites, without waiting for records |
| 💡 | PMKSY-WDC watershed project boundaries (Bhuvan) overlaid | Which priority areas already have a project |
| 💡 | Soil Health Card district statistics as a check on our nitrogen map | Free validation |
| 💡 | Census 2011 village boundaries (open copies) | A proper village card |
| 💡 | Share-a-link / QR code on the village card | Officer to panchayat in one tap |

### Platform

| | Item | What it gives |
|---|---|---|
| 📅 | SlideSense and FloodSense for Assam (AD-22) | Three hazards, one state |
| 📅 | Other North-East *jhum* states (AD-35); Arunachal erosion (held back) | Same code, new region |
| 📅 | Riverbank erosion watch: Brahmaputra, Barak, Majuli (AD-21) | Bank-line change every year |

## ASK: needs a government body's data or permission

| | From | Item | What it unlocks |
|---|---|---|---|
| 📅 | Soil Conservation Dept | Treated-area records, their cover/practice values, schedule of rates | Treated vs untreated map; costs in the works planner; "did the works help?" |
| 📅 | Soil Conservation Dept | Soil survey; micro-watershed boundaries; field staff for checks | Better soil factor; their units; ground truth |
| 📅 | CWC | **River flow** at the sediment stations, and rating curves | Re-opens the river-mud forecast and tonnes-to-river checks |
| 📅 | ASSAC / NRSC | Land-degradation vectors, 1:10k land use, *jhum* maps, Cartosat imagery, CartoDEM | Better labels and cover; sharper terrain |
| 📅 | Survey of India / NHP | Bare-earth height model | Removes the treetop slope error |
| 💡 | IMD | Hourly automatic-weather-station rain | A true rain-intensity factor |
| 💡 | Agriculture Dept | Raw Soil Health Card samples | Calibrate nitrogen and carbon |
| 💡 | Forest Dept | Forest types / working plans; Tea Board garden boundaries | Splits the "tree" class without guessing |
| 💡 | Rural Development | MGNREGA works with dates and types | Full "did the works help?" |
| 💡 | Mining Dept | Sand-mining lease areas | Ties disturbance to permits |
| 💡 | ASDMA / Water Resources | Embankment and erosion-site lists, flood sand-cast reports | Riverbank and sand-cast checks |
| 💡 | GSI | Assam landslide inventory | SlideSense for Assam |
| 📅 | Department | WhatsApp / SMS channel, consent to message farmers | Advisories reach people |

## PAID: needs a budget

| | Item | What it unlocks |
|---|---|---|
| 📅 | Water-clarity + rain sensors at 2–3 small hill streams (AD-19) | **The** missing data for the river-mud forecast |
| 📅 | Soil-loss plots at pilot sites (AD-31) | Measured tonnes per hectare: calibrates the whole map |
| 📅 | Field validation visits, the pilot (AD-16) | Ground truth → an AI correction layer |
| 📅 | Farmers' photo reports, AI-sorted, person-checked (AD-17) | Continuous ground truth |
| 📅 | Gully finder, deep learning on sharp imagery (AD-18) | Gullies mapped, not guessed |
| 📅 | Offline Android field app in Assamese (AD-27 in the beyond list) | Field forms that work without signal |
| 📅 | WhatsApp / SMS / voice advisories (AD-28 in the beyond list) | Reach farmers; per-message costs |
| 📅 | Training workshops, user guide, handover (AD-34) | Adoption |
| 💡 | Commercial sharp imagery (Planet 3 m daily, or 30–50 cm tasking for pilots) | Monsoon monitoring; gully and hill-cut detail |
| 💡 | Drone surveys and LiDAR of pilot catchments | Bare-earth terrain, gully volumes, before/after works |
| 💡 | Lab soil tests (nutrients, how much richer eroded soil is) | Firm ₹ value of soil lost |
| 💡 | Soil-moisture sensors at pilot sites | When ground is saturated, so heavy rain does most harm |
| 💡 | "Ask SoilSense", an AI assistant for officers in English/Assamese, answering from our data | Plain answers, per district; API costs |
| 💡 | Earth Engine commercial plan (or own cloud processing) | Reliable statewide satellite runs |
| 💡 | Government-grade hosting (MeitY-empanelled cloud), uptime, security audit | Required for a department deployment |
| 💡 | Soil-carbon / watershed carbon-credit project design | Outside funding for treatment works |
| 💡 | Crop-insurance / relief evidence packs (sand-cast, slope failure) | Use by insurers and relief bodies |

## Where the AI sits, in one line each

- **Now:** the AI erosion map (a second opinion) and AI reasons.
- **Next (free, after 1 Nov):** the satellite-reading AI for cover and *jhum*, an AI check on
  alerts, and our own dated labels.
- **With the pilot (paid/ask):**
  - a field-corrected AI map;
  - a river-mud AI on sensor data;
  - a gully finder;
  - farmer-photo sorting;
  - the officer assistant.
