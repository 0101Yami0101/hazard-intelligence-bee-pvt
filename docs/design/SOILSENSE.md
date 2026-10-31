# SoilSense — start here

> The front door to the soil-erosion module. It says what SoilSense is, what each page
> shows, where its files are, how to rebuild it, and which document holds the detail.
> Written 2026-10-31. When this page and a detailed document disagree, the detailed one
> wins; fix this page.

## What it is

SoilSense is the platform's third module. It shows **where rain washes soil off the land in
Assam, which small catchments and districts to survey and treat first, and how that changes
over time.** It answers the Assam Soil Conservation Department's problem statement
NESFIC-D-07.

It is built on the same data backbone as SlideSense and FloodSense, moved to a second state
with a region switch (`REGION=assam`). That move is the point: it shows the backbone is not
tied to Arunachal or to one hazard.

The core is the standard soil-loss recipe used in Indian soil-conservation work (RUSLE):
rain strength × how easily the soil washes × slope × ground cover × protection. Four of the
five come from open data already in the backbone. Protection (bunds, terraces) is unknown
until the department shares its treated-area records, so every number is "if untreated".

**State on 2026-10-31:** first version built and in the app with the status "building".
Deployed to the public `v2` app on 2026-10-31.

## The pages

| Page | What it shows | Kind of number |
|---|---|---|
| **Erosion map** | Yearly soil loss in six classes, 100 m squares, all Assam. Switch between the main run, the other rain map and the lower forest value. Extra views: the AI second opinion and soil reaching streams. District outlines; the top 20 catchments | Estimate (t/ha/yr), class |
| **This week** | The next 7 days' erosive rain against each place's normal for the time of year, and the catchments where it does most harm | Multiples of normal |
| **Village card** | Search a place (2,589 villages and towns) or a 'lat, lon'. One printable card: loss around it, the main reason, what helps, rank, bare-ground trend, this week's rain | Estimate, rank |
| **Change over time** | Bare ground in each dry season 2019–2026 from Sentinel-2, or the change between two years; catchments getting barer | Measured share |
| **Priority list** | 703 catchments and 35 districts ranked, each with its main cause, a second reason against similar slopes, typical measures, how firm the rank is, and what the lost soil is worth. Sliders re-rank by the officer's own weights. Field kit download | Rank |
| **What if we treat it?** | Soil saved per measure (replanting, terraces, contour bunds), per hectare and per catchment | Estimate (provisional values) |
| **How to read this** | The method in plain words, and every check with its result | — |

Rules the pages keep (from the design):

- A class or rank is never shown as a chance.
- The two unsettled inputs (which rain-strength map is right, and the cover value for land
  the satellite map calls "tree") are never hidden. Both alternatives are one click away,
  and each top catchment says whether it stays on top under the other rain map.
- Land the recipe does not apply to (rivers, water, towns) stays uncoloured, never "low".

## What is held back, and why

| Piece | State | Why |
|---|---|---|
| "New bare ground on a steep slope" flags | Held back | Two attempts; two of four tests fail (blind picture check 62.5%, bar 70%) |
| River-mud forecast (WHEN) | Parked | Four tests failed; mud at CWC stations follows the river, not hill rain. Needs small-stream sensors, plots or CWC flow |
| Splitting "tree" into forest, tea and jhum | Not adopted | The blind picture check failed; a second attempt needs a new sample |
| Gully-prone ground flag | Not adopted | No better than other open sloping land |
| Weekly outlook in the 08:30 cloud run | Local only | Logged on this PC; adding it to Modal needs a redeploy |
| Assamese wording on the village card | Not written | Needs a native speaker |
| Return path of the field form | Not built | Exports work; nothing comes back in yet |

## Where things are

| What | Where |
|---|---|
| App module | `webapp/products/erosion/` (`view.py` pages, `data.py` loading, `outlook.py` this week's rain) |
| App data | `webapp/assets/erosion/assam/` (10.5 MB): class maps, bare ground per year, outlook inputs, catchments, districts, villages, field kit |
| Recipe and builds | `scripts/build/erosion_*.py`, `scripts/build/cover_change.py` |
| Ranking, AI map, outlook log | `scripts/model/erosion_priority.py`, `erosion_rank_stability.py`, `train_erosion_ai.py`, `erosion_ai_explain.py`, `erosion_outlook_log.py` |
| Checks | `scripts/build/check_erosion.py`, `scripts/inspect/check_erosion_bars.py`, `scripts/inspect/erosion_eyecheck.py` |
| Bundle export | `scripts/run/export_erosion_bundle.py` |
| Results | `reports/erosion_*` |
| Outlook log | `records/erosion_outlook/assam/` |
| Proof of Work PDF and screenshots | `docs/nesfic/` (`scripts/run/build_proof_of_work.py`, `capture_soilsense_shots.py`) |

## Rebuilding it

Every script takes `REGION=assam`; with no REGION set they run for Arunachal as before.

```powershell
$env:REGION = "assam"
.venv\Scripts\python scripts\build\erosion_factors.py        # the recipe and the classes
.venv\Scripts\python scripts\model\erosion_priority.py       # the ranked list
.venv\Scripts\python scripts\run\export_erosion_bundle.py    # the app's files
Remove-Item Env:REGION
```

The full 12-step order, with times, is in
[EROSION_PLAN.md, How to run anything for Assam](EROSION_PLAN.md#how-to-run-anything-for-assam).
After any change to shared code (`common.py`, `grid.py`), run
`scripts/model/check_live_unchanged.py check` so the live flood forecast is not disturbed.

## The documents

| Document | Read it for |
|---|---|
| [EROSION_MODULE.md](EROSION_MODULE.md) | The design: what the department asked, the method, validation, tiers, limits |
| [EROSION_PLAN.md](EROSION_PLAN.md) | The working plan: status at a glance, the revisit register (V-01…), the build log, every test written before it ran and its result |
| [ROADMAP_EROSION.md](ROADMAP_EROSION.md) | What to add next, AI and otherwise, in priority order (AD-01…AD-36) |
| [SOILSENSE_FULL_LIST.md](SOILSENSE_FULL_LIST.md) | Everything SoilSense can offer, by tier (FREE / ASK / PAID) |
| [NESFIC_D07_FINAL_ANSWERS.md](NESFIC_D07_FINAL_ANSWERS.md) | The paste-ready application answers |
| [NESFIC_D07_APPLICATION.md](NESFIC_D07_APPLICATION.md) | The full application draft, official-site facts and Proof of Work contents |
| [NESFIC_D07_SUBMISSION_PLAN.md](NESFIC_D07_SUBMISSION_PLAN.md) | How the application, PDFs and app carry the whole offer |
| [NESFIC_USPR.md](NESFIC_USPR.md) | The official form's 12 questions |
| [DATA_CONTRACT.md](DATA_CONTRACT.md) | The Assam grid, frozen 2026-10-17 |

**Key dates:** applications close 10 Nov 2026; our target is to submit by 7 Nov.
