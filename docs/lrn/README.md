# Learning path — one visual page per phase

The plan is in [../LEARNING_ROADMAP.md](../LEARNING_ROADMAP.md). Open each page in a browser.
Ticks and quiz marks are saved in that browser. All pages share `lrn.css`.

| Phase | Page | State |
|---|---|---|
| 0 · The big picture | [phase-0-big-picture.html](phase-0-big-picture.html) | ready |
| 1 · The science underneath | [phase-1-science.html](phase-1-science.html) | ready |
| 2 · The data backbone | [phase-2-data-backbone.html](phase-2-data-backbone.html) | ready |
| 3 · SlideSense | [phase-3-slidesense.html](phase-3-slidesense.html) | ready |
| 4 · FloodSense | [phase-4-floodsense.html](phase-4-floodsense.html) | ready |
| 5 · SoilSense | [phase-5-soilsense.html](phase-5-soilsense.html) | ready |
| 6 · The app and operations | [phase-6-app-ops.html](phase-6-app-ops.html) | ready |
| 7 · Defending it in the room | [phase-7-defend.html](phase-7-defend.html) | ready |

`tools/one_square.py` prints every backbone layer for one point (the Phase 2 exercise):
`.venv\Scripts\python docs\lrn\tools\one_square.py <lat> <lon> "name"`. It needs the local `data/` folder.

`mobile/` holds the same pages as single files with the styles built in, for phones. Rebuild them after editing a page or `lrn.css`.

**Reference pages:** [apsac.html](apsac.html) — everything we use from APSAC and its family (APSSDI, Bhuvan, SAC, NESAC), and the full list of what to ask them for.

**Explainers:** [line-up.html](line-up.html) — what "lining up the data" means, drawn simply (the graph paper, the six tricks, one square with all its facts).
