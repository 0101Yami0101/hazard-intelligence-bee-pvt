# FloodSense forecast screen — one checked number everywhere, confidence, river graphs

> **Status (2026-09-27):**
> - **Phase 0 DONE.** `scripts/model/check_live_unchanged.py` (golden live run
>   recorded 2026-09-27; replay reproduces every number exactly) and
>   `scripts/run/check_app_screens.py` (all 11 screen cases open cleanly).
> - **Phase 1 DONE.** See the Phase 1 results note below. Golden check after
>   it: 0 changed, only the intended "97 → 219 points" label.
> - **Phase 2 BUILT, Gate A FAILED** (10 km and the pre-registered 20 km).
>   Ranking is good (AUC ~0.85) but the level is not stable between years —
>   the flood record itself roughly doubled in 2024–25 relative to the rain.
>   Full numbers: [PARKED_HIMALAYAN_FLOOD_WHERE.md §0v](PARKED_HIMALAYAN_FLOOD_WHERE.md).
> - **User's decision (2026-09-27): show it as APPROXIMATE, with the measured
>   error stated; and retune the day model on record days only.** Both done:
>   - Day model retuned (calibration 2024-01-01 → 2025-10-31; its chances
>     ×1.41, "× normal" ×1.04, flooded km² ×1.16 on the golden day; **0
>     changes to the 32 river forecasts**). Replay and live source check
>     re-run on record days only (§0v).
>   - Near-here curves fitted on the retuned model (2024–25), wired into the
>     daily run, the report, the web snapshot and the track record
>     (`records/flood_forecast/near_here/`). Golden check: only additions.
>   - Phase 4 confidence: **Gate C′ merged High and Medium** (no better
>     ranking, level further off). Two levels shown: floods on record within
>     10 km, or none — each with its measured tendency (on record: ×1.7 more
>     recorded than forecast; none: ×0.8).
>   - Phase 6 core: the Live forecast screen now leads with the approximate
>     near-here %, its error line, the evidence line and a 7-day chart; map
>     and gauge dots on one % scale; "× usual" and the alert words gone.
> - **Phase 3 TESTED, Gate B FAILED — not applied.** The terrain correction
>   did not hold (top ranges swung ×0.04–×1.04 by fold and year); per the
>   fallback the "if a flood comes" number is shown capped at "20%+" with
>   the checked rate for its range beside it.
> - **Phase 5 DONE.** Gauge shown only when on the place's own river
>   (`build_gauge_link.py`, self-tested); Flood-Hub-style graph below the
>   map (`build_gauge_levels.py`, display-only 30-day history).
> - **Phases 7–8 DONE, with a finding that changed them.** The Sentinel-1
>   "confirmation" used for the training records passes 97–100% of
>   flood-free dates (PARKED §0w). So new records are gauge crossings and
>   people's reports, the radar number is information only, and the grader
>   scores ranking only. Wording "confirmed by satellite" corrected
>   everywhere. News-feed intake not built (needs village-level place reading).
> - **Phase 9 DONE.** "How to read this forecast" in the ℹ️ popover; every
>   figure read from files.
> - **2026-09-28 — the flood record fixed.** A new radar water test that can say
>   "no" (97.8% of flood-free dates correct, pre-registered, passed on fresh
>   records) re-checked all 4,586 reports; the VERIFIED record = 2,185 events
>   confirmed by radar, Google's Global Flood Database or a gauge. The day
>   model and near-here chances now train on it (timing inside Arunachal 0.706
>   → 0.845 on verified floods); WHERE stays (not better on verified-only).
>   PARKED §0x.
> - **2026-09-28 — soil wetness on flat ground, live.** Pre-registered test:
>   no for landslides and for 15/30-day rain; yes for floods on flat ground only,
>   confirmed on fresh years and with 16-day-old readings. Wired into the day
>   model, the daily run (Earth Engine fetch; rain-only fallback), near-here
>   (re-measured) and the method page. River forecasts and hill/steep areas
>   unchanged (golden check). [SOIL_WETNESS_TEST.md](SOIL_WETNESS_TEST.md) §10.
> - **2026-09-28 — gauge placement fixed; part-days shown.**
>   - **Placement:** `build_gauge_link.py` snapped each gauge to the BIGGEST
>     channel within 1.5 km, which on a river is always the downstream edge.
>     Every gauge moved 1.5-2 km downstream, and 5 landed on a bigger
>     neighbouring river (e.g. Pagoda: CWC catchment 176 km2, placed on
>     1,472 km2).
>   - **Now:** the nearest channel of the gauge's size (CWC published
>     catchment x0.5-2; NWDP big enough for its typical monsoon flow, from its
>     usable record).
>     - 30 of 32 gauges are placed; 27 within 0.3 km of the published spot,
>       and CWC catchments match to ~1-2%.
>     - Miao (NWDP) moves 1.7 km, onto the river its flow needs.
>     - Changlang and Ziro are not linked: NWDP's own coordinates are wrong,
>       and only their towns are known.
>   - **Map dots** are drawn at the placed point, so a click on a dot reads
>     "at this spot".
>   - **Part-days:** NWDP part-days (fewer than 48 of 96 readings) now show as
>     hollow dots on the gauge graph. They are display-only; no forecast uses them.
>   - **Checks:** golden check PASS (every forecast number identical); 14/14 screens.
>   - **Three linking faults found from a click on the Sagalee gauge ("no
>     gauge ... Sagalee, 0 km away, is on a different river"):**
>     1. Only ground with a >=2% flood chance was linked. A gauge in a
>        narrow valley (Sagalee's own spot: 1%) was not on its own river.
>        Now every spot beside a river is linked; flood-prone ground keeps
>        exactly its old link.
>     2. The steepest-rise walk steps past cells of a wide river. Ground
>        0.4 km below the Pasighat gauge read "a different river". Now a
>        channel cell beside a walked cell, with the same flow (within 2%),
>        is that river; a side stream never qualifies (self-tests cover both).
>     3. The "none" note claimed "a different river" without checking. It
>        now says which case applies: river here but no gauge on this stretch;
>        no river beside the spot; or a gauge whose exact spot is unknown.
>        "At this spot" is kept for clicks within 0.5 km of the gauge;
>        otherwise "on this stretch, N km away".
>     Floodable ground linked: 31.4% -> 32.2%. Passighat's recovers to
>     141.7 km2.
>   - **Open flag:** Changlang (2nd station) jumps ~10x between 2024 and 2025
>     (monsoon quarter median 8 -> 87 m3/s). It is not in
>     `gauge_records.RECORD_STARTS`; check it before its next retrain.
>     *Checked 2026-10-10: a real change of scale; its record now starts
>     February 2025 (FLOOD_WHEN_PILOT_PLAN.md §19a).*
> - **2026-09-28 — the forecast screen made over as a dashboard**, after the
>   user's mock-up (FLOOD_HUB_AND_MOCKUP_COMPARISON.md §2). The brief: keep the
>   mock-up's shape but miss nothing we have; minimum text, maximum visuals;
>   explanations behind ⓘ icons and badges; forecast, outlook and estimate
>   impossible to confuse. `webapp/products/flood/live.py`.
>   - **Six badges, one per kind of number**, each explained on hover:
>     Forecast ✔ (gauge, checked daily), Outlook ≈ (near here, approximate),
>     Estimate ◆ (if a flood comes), Measured ●, Input ☂ (rain, soil),
>     Record ◷. Every number on screen wears one. Level words on the chance
>     scale: Very low / Low / Moderate / Elevated / High (never "warning" or
>     "danger", which name the river's lines).
>   - **Layout:** header (issue time, search, run now) → key → statewide
>     tiles (outlook anywhere, areas at 10%+, rivers at 10%+, highest river,
>     above line now, gauges reporting) → place | map | 7-day outlook +
>     conditions (Rivers / Rain / Soil) → what changed · needs attention ·
>     track record → one gauge's graph beside a board of every gauge × every
>     day (click a row to open it) → table, report form and "how to read"
>     folded away.
>   - **Map:** rivers drawn by size; a gauge's own stretch glows in its
>     chance colour (the same link raster the "gauge on this river" lookup
>     reads); gauges as diamonds, red halo when above the line now; named
>     neighbouring places with their outlook (one per ~10 km area, never
>     overlapping); the area draining to the selected place as a soft wash.
>     Own Layers menu; the sidebar Rivers switch is hidden on this screen.
>   - **Place panel:** outlook headline with 7 day bars (scaled to at least
>     2%, so a quiet week looks flat), then tiles for if-a-flood-comes, the
>     own river's gauge, what that gauge reads now against its line, and
>     floods on record. With no place: Arunachal, plus the highest-outlook
>     areas as one-click buttons.
>   - **Two display-only additions to the daily snapshot** (golden check:
>     changed 0, removed 0, added 3): `previous` — the latest earlier issue's
>     statewide and river chances, and every place's week once that issue is
>     in the near-here log — for "what changed"; and `soil_wetness.pct_now` /
>     `flat` for the Soil panel. `flood_forecast_live.previous_issue`.
>   - **Needs attention** lists only what our numbers say (rivers above the
>     line, rivers at 5%+, areas at 10%+, gauges offline, soil missing). The
>     mock-up's bridge and evacuation advice needs district data we do not
>     have, and is not invented.
>   - **Narrow screens:** below ~1,200 px of content the outlook column drops
>     under the map instead of squeezing.
>   - **Checks:** 17/17 screens (new cases: the Rain and Soil tabs);
>     screenshots at 1920 and 1440 wide.
> - **2026-09-29 — Flood-prone ground and Catchments made over the same way**
>   (UI only: no data, model or snapshot change). The shared look moved to
>   `webapp/products/flood/ui.py` (stylesheet, badges, tiles, header, map
>   title with its Layers menu, river layer), so the three pages read as one.
>   All three share the place search and map click; switching page re-centres
>   the new page's map on the place.
>   - **Flood-prone ground** (Estimate ◆): tiles for ground a flood can reach
>     (10%+ / 20%+ / 2%+ km²), the Arunachal and steep-ground checks, and
>     floods learned from; "how the top colours held up" as said-vs-went-under
>     bars, and the most exposed places one click away. For a place: its
>     level word, the number on a 0–30% scale, height above the river, river
>     size, nearest low ground and the past-check rate for its range. Beside
>     the map: km² by level and the four things it is read from.
>   - **Catchments** (Input ☂): tiles for the share very wet or wetter,
>     exceptional catchments, average and wettest-upstream rain; 7 day
>     buttons; "catchments to watch" (named after the nearest settlement,
>     click to open). For a place: upstream rain that day, 18 days of bars
>     (past solid, forecast faded), its percentile for the time of year,
>     upstream area, last and next 3 days, and the area draining to it
>     outlined on the map.
>   - "If a flood comes" under 2% now reads "<2%", not "0%", on every page.
>   - **Checks:** 21/21 screens (new cases: both pages with a place, and a
>     later day); screenshots at 1920 and 1440 wide.
> - **2026-09-29 — floods back to 2003: counted on screen, and learned from.**
>   [OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md).
>   - "Floods on record" counts from 2003 (was "since 2015" — the design
>     text in Phase 4 below predates this). The start year is read from the
>     snapshot, never typed.
>   - The day model learns from 2003 (pre-registered test passed; wired in
>     with the user's go-ahead). Live timing in Arunachal 0.851 → 0.879;
>     near-here ranking 0.893 → 0.890.
>   - The measured error on screen now also says that at its highest
>     numbers (5% and up) it said more than happened, when measured so. The
>     "floor" and "often unreported" readings, and "about the same ranking
>     everywhere", now follow the measured numbers instead of being typed.
>   - The method page says what the model learns from ("every verified
>     flood of 2003–2023").
> - **Not done:** ⭐ Phase 10 — IMPORTANT, the next big feature (a level forecast line — needs its own model and
>   test), 2b (grading days 4–7 on archived forecast rain), and the research
>   step §0w points to: a real radar water test, then re-deriving the truth.
> - **2026-10-06 — the main row of all three pages evened up** (UI only: no
>   data, model or snapshot change; user: "this looks very uneven").
>   Measured before: the place panel, the map and the side panel ended
>   130–290 px apart on every page, and the side panel fell under the map
>   sooner than it needed to.
>   - **Three panels, one bottom line.** Each panel fills its column. What
>     takes up the spare height is content, never a blank: the list buttons,
>     the place tiles, the river rows (each up to a limit). Map height
>     560 → 480 px (`ui.MAP_H`) — the state is wide, not tall, and at 560 the
>     map was the tallest panel by far.
>   - **Side by side from 1,304 px of page** (the map's 620 px is what the
>     whole state needs at its starting zoom). Read off the row itself, so
>     closing the sidebar counts: a 1,552 px window shows three panels with
>     the sidebar closed and two rows with it open.
>   - **Under the map, the side panel uses the width**: the forecast page
>     puts its eight day buttons on one line and its rivers in two columns
>     of four; the other two pages put their list beside their other blocks.
>   - **Also:** the three cards under the map end on one line; the track
>     record's numbers are no longer cut off; tiles with and without an ⓘ
>     sit on one line; Catchments shows the state's last and next three days
>     of rain as tiles (the same two a place shows) and six catchments to
>     watch, not seven.
>   - All in `webapp/products/flood/ui.py` (the stylesheet's "main row"
>     block, `main_row`), with keyed blocks in `live.py` and `view.py`
>     (`fs_main`, `fs_r_a/b/c`, `fs_eq_*`). One trap recorded there: a
>     button with help text holds a hidden twin of itself, so the stylesheet
>     must never set `display` on what is inside it.
>   - **Checks:** 21/21 screens; panels measured level in 18 combinations
>     (window 1,366–1,920 px, sidebar open and closed, with and without a
>     place, all three pages); the same on the host's package versions
>     (Streamlit 1.65). Not on the public link until `v2` is pushed again.
> - **2026-10-07 — two fixes, UI only** (not on the public link until `v2`
>   is pushed again):
>   - **The landing page left behind inside a module.** Opening a module
>     from the landing page sometimes left the landing title above the
>     module until a reload (4 of 6 fresh visits in a test). The buttons
>     restarted the landing page mid-draw; they now switch on the click
>     itself (`webapp/app.py`, `_open`). Then 0 of 19 visits, both ways, all
>     three modules, and on the host's Streamlit 1.65.
>   - **Gauged rivers at the starting zoom.** Their bright bands and halos
>     piled into blobs, with a bead at every join. Each river size, and each
>     gauge's stretch, is now drawn as one line (5,692 map shapes → 1,318),
>     with a slimmer line and a softer halo (`ui._draw_rivers`). Colours,
>     the legend and what a stretch means are unchanged. Checked on the old
>     and new drawing side by side: hover label, gauge click, map click on
>     ground and on a river, the Rivers switch, the other two pages; the
>     same on the host's package versions; 21/21 screens.
>   - **The forecast box on the full-screen map** (user: "when the map is
>     full, we can't see any data"). Full screen shows only the map's own
>     box, so the page's panels cannot be seen there however they are
>     styled; the box therefore rides inside the map, hidden until the map
>     is full screen: the place, its headline chance and seven day bars, its
>     tiles (or, with no place, the areas with the highest outlook), and the
>     colour key, with a Hide / Show button. A click on the full-screen map
>     picks a place and the panel follows, staying full screen. Same numbers
>     from the same functions as the box beside the map (`live._full_panel`,
>     `_place_tiles`; `ui.fullscreen_panel`). Forecast page only — the other
>     two pages' maps go full screen without a panel. Not in it: the search
>     box and the day picker (page widgets cannot live inside the map).
>     Checked: the box beside the map is unchanged, byte for byte, in five
>     cases; 13/13 panel checks here and on the host's package versions;
>     the river checks again; 21/21 screens.
>   - **Data Backbone brought up to date** (it was last built 2026-08-17,
>     before any of the flood work). Its catalogue now holds the river
>     gauges, the radar scenes and the two flood-report sets (24 → 29
>     sources, 11 → 14 groups, 8 → 308 GB, 300 GB of it radar scenes); four
>     of those folders had no source record at all and got one after the
>     fact (`scripts/run/record_missing_sources.py`). The diagram draws
>     Live river gauges, the Daily run and — for flood forecasts — the
>     forecast-archive loop as built, and Hosted scheduling and the same
>     loop for landslides as still planned. New on the Pipeline page: "What
>     the platform holds today", one row per dataset (how much, what span,
>     last changed, how it is kept up to date) and the models with their
>     training dates — counts and dates only, measured by
>     `scripts/build/build_backbone_bundle.py` (`build_status`); the
>     forecast figures are read from the latest flood snapshot, since the
>     daily run does not rebuild this bundle. Checked: all 34 layer
>     summaries and previews identical to the old bundle; the 24 old sources
>     unchanged; pages clean here and on the host's package versions.
>     **Found on the way:** `records/flood_events/new_records.csv` holds one
>     entry and it is false — Murga Bridge, 2026-09-28, from the single
>     wrong reading (2,231.30 m against a line of 2,135.02 m) that the spike
>     filter was later built for; the gauge's cleaned high that day is
>     2,134.39 m. The forecast page's track record counts it as one new
>     flood record. Left in place, for the user to decide.
> - **2026-10-09 — the false Murga Bridge record withdraws itself** (the
>   user: remove it, after confirming it is false).
>   - **Confirmed:** CWC's server now holds 2,134.30 m for 11:00 on 28 Sep,
>     where it held 2,231.30 m; the track record's own re-read of that day
>     is 2,134.39 m against a line of 2,135.02 m.
>   - **Why it stayed:** the intake wrote the record on 29 Sep from the day's
>     reading as it then stood, and never looked at it again. The grading
>     re-reads the gauges every day; the intake did not.
>   - **Now** (`flood_intake.withdraw_corrected`, run inside `gather`): each
>     day, a gauge record whose day now reads below the line is withdrawn.
>     It stays in `candidates.csv`, marked, with the corrected reading, and
>     leaves `new_records.csv`. A day the readings no longer hold is left
>     alone; a crossing that comes back is a record again. Reports are not
>     touched.
>   - **Checked:** `flood_intake.py test` (a corrected reading, a day no
>     longer held, a crossing that returns) passes; on the real files the
>     record count went 1 → 0, and a second run changes nothing. The count
>     on screen follows at the next forecast run.
> - **2026-10-10 — three small screen fixes** (UI only; no number changed).
>   - **A gauge feed down at its source is named as that.** The government
>     small-river table (NWDP) has received no rows for any station since
>     29 Sep, 16:45; from 8 Oct all its gauges read "offline", with nothing
>     saying the feed itself was down. `live._feed_outages`: at least half a
>     network's gauges (and five or more) offline, last readings within
>     three days of each other and within the last 60 days. Needs attention
>     then shows "Small-river feed down · 29 Sep" (the detail and the gauge
>     names behind its ⓘ) apart from the single gauges long offline, and the
>     Gauges reporting tile says so. It clears by itself when readings
>     return.
>   - **SlopeSense "Next 7 days here" charts** listed days A–Z ("Fri 16"
>     before "Mon 12"; across a month end "01 Nov" before "29 Oct"). Both
>     charts now keep date order.
>   - **Data Backbone "Span" tile** read 27 yr by counting calendar years
>     touched; it is 26 whole years of rain (9,555 days) and now says 26.
>   - Checked on screen at 1,366 and 1,920 px (cards still end level, no
>     text cut off); screens pass.
>
> - **2026-10-10 — a river already above its line shows "unsure", not a small
>   percentage** (the user: "apply current fix until more data
>   accumulated"). Seven model designs failed to cure the fault
>   (FLOOD_WHEN_PILOT_PLAN.md §13h–§18); the rule, where it shows and how it
>   was checked are in §18d there. Screen only.
> - **2026-10-10 — the full-screen box on the other two pages.** Flood-prone
>   ground and Catchments now carry their place box on the map while it is
>   full screen, as the forecast page has since 2026-10-07.
>   - **What rides along:** the place (or "All of Arunachal"), then exactly
>     what the box beside the map shows — Flood-prone ground: how the top
>     colours held up and the most exposed places, or the place's estimate
>     and its four tiles; Catchments: the share very wet with its day bars
>     and the state's last and next three days, or the place's upstream rain,
>     its bars and four tiles — and the map's colour key. Hide / Show as on
>     the forecast page.
>   - **How:** `view._Panel` keeps each block's HTML as the page draws it
>     (`show`), so the panel can never say something the page does not.
>     What the page draws as widgets (the ✕ title, the list of place
>     buttons) is kept as plain rows. Not in it: the rain chart (a chart
>     cannot live inside the map), the search box and the day picker.
>   - **Checked:** 22 of 22 on the two pages (hidden at normal size, shown in
>     full screen, colour key present, nothing wider than the panel, Hide, a
>     click on the full-screen map picks a place and stays full screen, the
>     numbers equal the box beside the map, no errors); the forecast page's
>     own 13 checks still pass; screens pass.
>
> - **2026-10-10 — phones and tablets: every page checked, four faults
>   fixed** (UI only; no number changed). Until now the layout had been
>   measured at laptop and desktop widths only.
>   - **How it was checked:** every page of all three modules, with and
>     without a place — 14 pages — at four screens: phone 390 px, small
>     phone 360 px, tablet 768 px, tablet on its side 1,024 px. For each:
>     errors on screen, the page scrolling sideways, anything past the
>     screen's edge, whether the menu opens, text under 9.5 px. Then the
>     phone screenshots were read end to end, since counts do not show how
>     a page reads.
>   - **Before: 4 of 56 with a fault** — the forecast page scrolled sideways
>     on both phones, with and without a place. The screenshots showed
>     three more things the counts could not.
>   - **Fixed:**
>     1. *The gauge graph ran 34–52 px past a phone's screen* and took the
>        whole page sideways with it. It was one joined chart (level above,
>        chance bars below); a joined chart does not size itself to its
>        box. Now two charts sharing the time scale and one y-axis width
>        (`live.Y_AXIS`), so they line up as before and each fits
>        (`live._gauge_chart` returns a list; `.st-key-fs_gchart`).
>     2. *Day buttons stacked seven or eight rows deep* between the search
>        box and the map. Four to a row on a phone now: FloodSense
>        (`ui.py`, the 760 px block, `fs_r_a`) and SlopeSense
>        (`mapping.day_strip` is keyed `daystrip_*`; rule in `theme.py`).
>        ⚠️ **Correction, same day:** on the FloodSense pages this did not do
>        what is written here. The rule set the two ROWS of buttons side by
>        side, so a phone showed two columns that read downwards (Today, Sun,
>        Mon, Tue beside Wed, Thu, Fri) — it was reported as four to a row
>        without the screenshot being read closely enough. Found while
>        rebuilding SlopeSense, which uses the same rule, and fixed: each row
>        keeps the full width and its four buttons stay side by side
>        (`ui.py`, the 760 px block). Measured at 390 and 360 px on both
>        forecast pages: 4 in the first row, date order, none cut off,
>        narrowest button 77 px.
>     3. *Data Backbone's diagram cut a box's name off* ("Hosted
>        scheduling"): boxes had a fixed height. They grow on a phone, and
>        the return-path row may wrap (`theme.py`).
>     4. *The river list's "chance" heading ran past the panel's edge.* It
>        now ends at its column's edge (`ui.py`, `.fs-rhead`).
>   - **After: 56 of 56 with no fault.** Desktop unchanged: the three
>     panels end level in all 18 combinations measured before; the two
>     halves of the gauge graph start at the same x; screens pass.
>   - **Left as it is:** the page-head buttons (My location, Recentre, Run
>     now) are one per row on a phone; wide tables scroll sideways inside
>     their own box; a full-length phone page is long (the forecast page
>     about 5,700 px).
>   - **Not yet done:** the same survey on the host's newer package versions
>     (Streamlit 1.65) — to run before these changes are pushed.
>   - **To run it again:** `python scripts/run/check_app_mobile.py TAG`
>     (about 25 minutes; `--shots` keeps a screenshot of every page).
> - **2026-10-10 — the look is now shared with SlopeSense** (FloodSense
>   numbers and layout unchanged). SlopeSense's pages were rebuilt from the
>   same pieces: [SLOPESENSE_SCREEN.md](SLOPESENSE_SCREEN.md). What moved here:
>   - `ui.py` gained `SLOPE_TIERS` (SlopeSense's badges; `badge()` looks in
>     both), `Panel` (was `_Panel` in `view.py`; the two flood pages use it
>     from here), `page_head(..., warn=)` and `map_title(..., right=, ratio=)`.
>     The day-button rules also cover SlopeSense's `sl_d*` keys.
>   - **The header wraps when its own box is narrow** (`.st-key-fs_head`, a
>     container query at 640 px): on a 768 px tablet with the menu open the
>     page is 470 px wide and the search row ran off the right edge — on
>     FloodSense too. Title, then the search box, then its buttons two to a
>     row. This also puts the page-head buttons two to a row on a phone
>     (they were one per row, listed above as "left as it is").
>   - Checked: all 34 screen cases open; the full-screen panel check on
>     Flood-prone ground and Catchments still passes; phone and tablet
>     survey of the FloodSense and SlopeSense pages: 56 of 56 page-and-screen combinations with no fault.
>
> Until each phase ships, the rules in [FLOOD_MODULE.md](FLOOD_MODULE.md)
> ("What can honestly be quoted") still describe the live forecast screen.
> Background: [PARKED_HIMALAYAN_FLOOD_WHERE.md](PARKED_HIMALAYAN_FLOOD_WHERE.md)
> §0l–§0u (the joined forecast), [FLOOD_WHEN_PILOT_PLAN.md](FLOOD_WHEN_PILOT_PLAN.md)
> §13 (river gauges).

## 1. What changes, in plain words

The screen today shows three separate things for a clicked place: the
nearest river gauge's chance (which can be on another river), the spot's
chance of going under water if a flood comes, and a "× usual" figure. The
"× usual" figure reads like we are showing rain back to the user, and the
gauge number looks just as solid on a random hillside as on the gauge.

After this work, every place in Arunachal gets:

1. **One headline number, the same kind everywhere:** *"Flood chance near
   here, next 7 days: X%"* — the chance of a flood within about 10 km of
   the place in the coming week. A real, calibrated probability, checked on
   past years the model never saw.
2. **A day-by-day graph** of that chance for the 7 days.
3. **A confidence level** — High / Medium / Low — that says how much past
   flood evidence exists around that place, and therefore how well we have
   been able to check the number there.
4. **What it means for this exact spot:** "If a flood comes, chance this spot
   is under water" (or "high ground", with the nearest low ground).
5. **The river gauge only when it is on this place's own river**, labelled as
   a *checked forecast*, with a **Google-Flood-Hub-style graph**: the river's
   measured level for the last month, its warning / danger / highest-ever
   lines, and our chance of crossing the line for each coming day.

"× usual" disappears from the screen. The models underneath do not change.

## 2. Ground rules — every number on screen must pass all of these

1. **One exact event per number.** Its label says what, where, and when.
   ("Within about 10 km", "next 7 days", "danger level at this gauge".)
2. **Calibrated against exactly that event.** Not a neighbouring one. When
   it says 10%, about 10% of such cases must have happened.
3. **Checked on years the model never learned from**, inside Arunachal,
   on the live-rain path that actually ships — not only region-wide, and
   not only on satellite rain.
4. **No numbers multiplied together on screen** unless the product itself
   was checked. (The river chance is never folded into the spot number.)
5. **Logical consistency holds by construction**, and is asserted in code:
   a week is never less likely than any of its days, never more likely than
   the sum of its days, and "within 10 km" is never less likely than the
   place's own ~10 km rain cell.
6. **Every number is written down daily and graded when the truth arrives**
   (the track record in `records/flood_forecast/`).
7. **Limits are one click away, in plain words**, and never phrased as
   permanent when a named thing (data, a gauge, field checks) would lift them.

## 3. The numbers after the change

| # | On screen | Exact event | From | Checked how | Status |
|---|---|---|---|---|---|
| A | **Flood chance near here, next 7 days** (headline) | ≥1 flood record within 10 km of the centre of the place's ~10 km rain cell, in the 7 days starting today | production day model (unchanged) → new "near here" and "week" calibration layers | held-out years 2023–26, inside Arunachal, live-rain path; Gate A | **to build** |
| B | Day-by-day graph | same, for one day | same, daily layer only | same; Gate A | **to build** |
| C | If a flood comes, chance this spot is under water | 100 m spot shows new water, given a reported flood within ~5 km (WHERE's own training design: 10 km crops around reports) | WHERE (unchanged) | cross-fitted calibration; **over-promises at the top inside Arunachal** (see §5); Gate B | exists, **needs fix** |
| D | River gauge: chance of crossing its line, per day | the gauge's daily max ≥ its threshold (official CWC danger level, or the river's own wettest 2% of days) | gauge + rain models (unchanged) | out-of-fold 2015–26; graded daily against the gauge | exists |
| E | Chance of a flood somewhere in Arunachal this week | ≥1 flood record in Arunachal in the next 7 days | same layers as A, state-wide | held-out weeks 2023–26; Gate A | **to build** |
| F | Confidence: High / Medium / Low | not a probability — how much past flood evidence exists within 10 km | flood records + satellite-check coverage | levels must show measurably different checked performance; Gate C | **to build** |

**What "a flood record" means everywhere above:** a reported flood that a
Sentinel-1 radar pass then confirmed as new standing water (the same truth
every model here was trained and tested on; braided-channel-shift suspects
removed). Floods nobody reported, and short flash floods that drain before a
satellite passes, are not in it. The numbers are therefore a floor for
*every* flood, and flash floods in steep valleys are the most under-counted.
This is said on screen.

### Why the headline is "near here, this week", not "this 100 m spot, today"

- **Per spot per day the honest chance is tiny** — the highest ever was
  0.72%, and on an ordinary day a rain cell's chance is ~0.005% (median of
  the live path's "normal" level). A screen of "0.00%" is uniform but useless.
- **It cannot be checked per spot**: only 41% of Arunachal's floodable
  ground has ever been inside any satellite flood check, and only 47 of 667
  all-Arunachal rain cells had even one flood record in 2023–26.
- **The per-spot product runs ~4× high inside Arunachal** (§0p), half of which
  cannot be told apart from floods going unreported.
- **The area-level chance is the part already shown to add up**: floods
  centred in all-Arunachal cells, 2023–26, 115 forecast vs 119 recorded
  (§0p, satellite rain — to be re-checked on live rain in Gate A).
  *(Corrected 2026-09-27: that match relied on counting unrecorded 2026 days
  as dry; on record days it is 104 vs 150, and Gate A found the level drifts
  ~2× between years — see §0v. The area chance is still the better headline
  than the per-spot one; it ships as approximate.)*
- **It is how weather services handle rare hazards.** The US National Weather
  Service's flash-flood and tornado outlooks give "the chance of it happening
  within 25 miles (40 km) of a point", for the same reasons. Ours is 10 km,
  because the rain data are ~10 km cells and flood reports are located to
  roughly a village.
- **A 7-day window is forgiving of loose report dates** — the flood record's
  dates can be off by days (the 24 May 2024 case, §0m).

The spot is still answered — by number C, right under the headline.

**What people will see (rough, from the ordinary-day levels; firm numbers
come from Gate A):** most of Arunachal, most weeks, well under 1%; low
valleys and the plains edge in a wet spell, a few percent to tens of percent.
Small numbers for most places most weeks are the truth, not a fault.

## 4. What stays exactly the same

- The day model, WHERE, the valley factors, the gauge + rain models, their
  training and calibration files — **no retraining, no changed inputs.**
- `flood_gauge_live.forecast()` — same 8-day fetch window, same leads,
  same fallback, same bands. **The gauge-graph history is fetched by a
  separate display-only call** (see the trap in Phase 5).
- The daily 08:30 task, `--no-log`, and every existing log file and column.
  "× normal" and expected km² keep being computed and logged internally, so
  the existing track record continues unbroken. They just leave the screen.
- Internal band codes (`NORMAL … SEVERE`) in the logs. Only the words shown
  on screen change.

## 5. Problems found in the current screen (all fixed by this plan)

| Problem | Where | Fix (phase) |
|---|---|---|
| "Rain risk for this area … × its usual level" — it is the model's flood chance vs normal, not rain | `webapp/products/flood/live.py` `_place_panel` | replaced by A/B (6) |
| Nearest gauge shown for any spot, even on another river | `live.py` `_place_panel` | gauge link (5) |
| Chance words "Warning"/"Danger" collide with the river's official *warning level*/*danger level* lines the new graph will draw | `live.py` `ALERT`, metrics, table | numbers + colour ranges only on screen (6) |
| "If a flood comes" over-promises at the top inside Arunachal: says 11.9% → 5.9% happened; says 23.3% → 12.6% (cross-fitted check, `reports/flood_where_training.json`, `reliability_after_in_arunachal`); pooled top bin 32.1% → 20.7% | WHERE calibration, shown in `live.py` | Gate B (3) |
| "97 points" still printed; the live rain has used **219** points since 2026-09-22 | `scripts/model/flood_forecast_live.py` (`rain_source`, docstring), `webapp/products/flood/view.py` Method text, FLOOD_MODULE.md | read the count from `points.json` (1) |
| "Flood-prone ground" screen shows the OLD rule-based index (`floodprone.npz`), while the forecast uses the calibrated WHERE (`floodprob.npz`) — two "where" maps that can disagree; its caveat points to a Forecast page that no longer exists | `view.py` | show WHERE there (1) |
| Catchments screen's "Large enough to forecast / Watch only" metrics come from the removed rule-based model and contradict a forecast everywhere | `view.py` | remove; the confidence level replaces them (1) |
| Method page describes the removed rule-based method ("the two multiplied") | `view.py` Method branch (currently disabled) | rewrite as "How to read this forecast" (9) |
| `floodprob.json` says "given a flood event in its catchment"; WHERE was trained on 10 km crops around reports, i.e. "given a reported flood within ~5 km" | `scripts/model/predict_flood_where.py` (writer of `floodprob.json`) | one wording everywhere (1) |
| **Found in Phase 1:** the Catchments screen's catchment → rain-point table (`catchments.npz` `rain_pt`) still held positions in the OLD 97-point list; since 2026-09-22 the app fetches 219 points, so 1,664 of 1,680 catchments read rain from another place (median 119 km away, up to 466 km) | `webapp/assets/flood/catchments.npz`, built by `build_flood_layers.py` | re-mapped; export re-maps with the points; app refuses a mismatch (1) |
| **Found in Phase 1:** the forecast screen triggered a live-rain download (6 calls, ~20 s cold) it never used | `webapp/products/flood/view.py` | fetch moved into the Catchments screen (1) |
| **Found setting up Phase 2:** the flood record ends Oct 2025, but the day model's calibration (2024–2026) and the replays (to 2026-07-29) counted Feb–Jul 2026 as flood-free — the 2026 monsoon had simply not been recorded yet | `flood_forecast.py fit_production`, `replay_flood_forecast.py`, the live source check | **not changed** (a production model); new layers use real truth days only; refit proposed separately |

## 6. Phases

Sizes are relative (S/M/L). Each phase ends with its checks passing and its
notes written; nothing is committed unless asked.

### Phase 0 — Safety net first (S)

**Goal: prove afterwards that no existing logic changed.**

- `scripts/model/check_live_unchanged.py`: record one full daily run's
  *inputs* (the Open-Meteo rain arrays and each gauge's fetched series) and
  *outputs* (day-model P for all cells × days, expected km², × normal, every
  river row, the web snapshot) as a golden set in the scratchpad.
- After every later phase, re-run the new code on the **same frozen inputs**
  and assert every old output is identical (floats to 1e-9); new outputs
  may only be *added*.
- Streamlit AppTest over all FloodSense and SlopeSense screens: zero
  exceptions (as done on 2026-09-22).

### Phase 1 — Fix what is stale or contradictory (S)

No model work. The items marked (1) in §5: point count read from
`data/interim/rainfall_om/points.json`; "Flood-prone ground" screen switched
to the calibrated WHERE map with its own legend ("if a flood comes, chance
each spot is under water"); Catchments screen relabelled as an **input**
("rain upstream vs normal — an input to the forecast, not the forecast") and
its old forecastable/watch-only metrics removed; one wording for WHERE.

**Phase 1 results (2026-09-27):**
- Point count now read from `points.json` everywhere it was printed (live
  report, web snapshot, both products' method/data tables); stale comments
  fixed. RAINFALL_RESOLUTION_LIMITS.md carries a dated update.
- **Real bug found and fixed:** the Catchments screen's catchment → rain
  point table was still built for the old 97 points, so since 2026-09-22
  1,664 of 1,680 catchments showed rain from another place (median 119 km
  away, up to 466 km). Re-mapped (`build_flood_layers.py
  --rain-points-only`, nothing else in the file changed); the web export
  now re-maps whenever it writes the points; the app refuses a table whose
  recorded point count doesn't match.
- Flood-prone ground screen now shows the calibrated WHERE layer (the one
  the forecast uses): 1,048 km² at 10%+, 188 km² at 20%+, "86 in 100"
  ranking check, and the Arunachal top-range caution, all read from
  `floodprob.json` (written by `predict_flood_where.py`, `--meta-only`
  rewrites it without re-scoring).
- Catchments screen relabelled as an input; its stale "large enough to
  forecast / watch only" block removed; its day strip now shows the share
  of catchments with very wet upstream rain (it used to quote the removed
  rule-based forecast). The live-rain fetch now happens only on that screen.
- WHERE wording is one sentence everywhere: "if a flood is reported within
  about 5 km" (training crops are 10 km, centred on the reports).

### Phase 2 — Build and test the headline numbers A, B, E (L) — **Gate A**

> **Result (2026-09-27): FAILED at 10 km and at the pre-registered 20 km.**
> Built as specified (`scripts/model/near_here.py`); logical limits held
> with zero violations; ranking AUC 0.84–0.86; but forecast ÷ recorded was
> 0.55–0.61 over 2023–25 (2023 about right; 2024 and 2025 about half), and
> the ranges were not within 2×. Diagnosis: the flood record's own rate
> roughly doubled in 2024–25 relative to what the rain explains, with either
> rain source. See PARKED §0v. Per the plan, nothing ships until the user
> decides between an approximate % with its measured error, or holding it.

New `scripts/model/near_here.py` (`fit` / `check` / `apply`):

1. **Neighbourhood:** for each rain cell, the cells overlapping a 10 km
   circle around its centre. The event is any flood record within 10 km of
   that centre. (Any record inside the cell is within 10 km of its centre —
   the cell's half-diagonal is ~7.5 km — so "near here" contains the cell's
   own event.)
2. **Daily layer:** raw = 1 − Π(1 − p) over the neighbourhood, where p are
   the unchanged day-model chances; then an isotonic curve maps raw → the
   observed daily frequency of the event. The raw union assumes
   independence and over-states; the curve corrects it.
3. **Week layer:** raw = 1 − Π(1 − daily) over the 7 days, then its own
   isotonic curve against the observed weekly event. Floods cluster across
   days, so again the raw value over-states and the curve corrects it.
4. **Statewide (E):** same recipe, event = any record in Arunachal that week.
5. **Consistency, enforced and asserted:** week ≥ max(day), week ≤
   min(1, Σ day), near-here day ≥ own-cell day.

**How it is tested (the honest design, same as the live source check §0q):**
day model tree 2015–20, its calibration 2021–22 (satellite rain), fed the
**Open-Meteo archive** rain the live path uses; the near-here curves fitted
on 2021–22; everything graded on **2023–26 inside Arunachal**. Production
then refits the curves on the production day model's out-of-tree years
(2024–26) on live-archive rain — the same "tree years never fit the
calibration" rule the day model follows.

**Gate A — pre-registered, all inside Arunachal, 2023-01-01 → 2025-10-31:**

- A1 *adds up:* total forecast vs recorded, within a factor of 1.5 — for the
  daily number (place-days) and the weekly number (place-weeks).
- A2 *says what happens:* in every chance range holding ≥10 recorded floods,
  what happened is within a factor of 2 of what was said.
- A3 *beats knowing the season:* Brier skill > 0 against the forecast's own
  seasonal level — each place's average forecast for that calendar month,
  taken from years the day model never trained on (live-archive rain
  2010–14 and 2021–22). This asks whether the day-to-day forecast adds
  anything beyond "this place, this time of year". Reported alongside, not
  gated: skill against the flood record's own place-and-month frequencies
  (2015–22), which also carries where floods tend to get *reported*.
- A4 consistency rules hold on every cell-day.

*Pre-registration details, fixed before the first run (2026-09-27):*

- **Truth ends 2025-10-31.** The flood record has 17 records in Oct 2025,
  then 2 in Jan 2026 and none after; days after its end have no truth and are
  never fitted or graded. (Found while setting this up: the existing day
  model's calibration and the earlier replays counted Feb–Jul 2026 as
  flood-free. The new layers are calibrated on real truth days only, so they
  are not affected; the day model itself is left unchanged and the finding is
  recorded in §5.)
- **"Within 10 km"** = records within 10 km of the centre of the place's
  0.1° rain cell. The raw union weights each overlapping cell by the share of
  its area inside that circle (own cell = 1).
- **Weekly grading** uses non-overlapping weeks from 2023-01-01, so each
  flood counts once per place; A1 is also reported for all 7 week phases.
- **Test models:** WHERE for floodable area = the 2022-only clean model; day
  model tree 2015–20, calibration 2021–22 (satellite rain); both then fed the
  live-archive rain. Known, pre-existing limit shared with every earlier
  replay: the WHEN panel inside the local rain score was trained on gauge
  data from all years (gauge labels, not flood records).
- **Isotonic curves** fitted region-wide (all cells), graded inside
  Arunachal; region-wide results reported for context.

**If A fails:** try the one pre-registered alternative, 20 km. If that fails
too, show the daily layer only if it passes on its own; otherwise **don't
ship a number we can't stand behind** — keep the current screen minus
"× usual", and write down what failed.

**2b — Days 4–7 (M, inside Phase 2 if the data exist):** the test above uses
archive rain, i.e. the rain that actually fell. The live screen uses
*forecast* rain, which gets worse with lead time in mountains. Open-Meteo
keeps archived past forecasts (its historical-forecast / previous-runs
services — confirm coverage for our points). If available, grade by lead
day and, if days 4–7 over-promise, fit per-lead curves. If not available,
days 4–7 are drawn lighter on screen with "rain forecasts are less reliable
this far ahead", and the week number says it includes them.

*Done 2026-10-11 ([LEAD_DAY_TEST.md](LEAD_DAY_TEST.md)): the archive exists
from 2024-01-25. On two monsoons, days 4–7 rank 2.3 in 100 lower than days
1–3 (89.1 → 86.9), almost all of it at days 6–7, and do not over-promise.
The dashes stay; no per-lead curves were needed.*

### Phase 3 — Make "If a flood comes" honest inside Arunachal (M) — **Gate B**

The cross-fitted check shows WHERE about 2× high in its top two ranges
inside Arunachal (§5). This is the same "too much water given a flood in the
mountains" found in §0p, seen from WHERE's own side.

- Fit a second calibration step by **terrain setting** (open plain vs
  confined valley, from the 2 km relief/slope features that already exist)
  on the cross-fitted predictions — physical groups, not "inside the state"
  (a state-line split was tried for the valley factor and swung an order of
  magnitude between years, §0l).
- **Gate B:** the recalibrated top ranges inside Arunachal must hold within
  ±30% (relative) across folds *and* across years. Physical sanity checks
  (`check_flood_where_sanity.py`) must still pass.
- **If B fails:** keep the model's number but show the checked rate beside it
  ("in past checks inside Arunachal, spots given 20–40% flooded about 13% of
  the time"), and cap the display at "20%+".
- `FLOODABLE_MIN` (10%) stays as the display threshold for "low ground",
  re-stated in terms of the recalibrated number.

*Pre-registration details, fixed 2026-09-27 before the second stage was
fitted (only the terrain spread was looked at — outside Arunachal 90% of
training rows have under 18 m of relief within 2 km; inside, the median is
130 m):*

- **Groups:** *open* = relief within ~2 km (`terrain_relief_2km_m`) under
  50 m; *valley* = 50 m or more. Physical, not "inside the state".
- **Second stage:** per group, an isotonic curve from the first-stage
  (already cross-fitted) calibrated chance to the observed share, itself
  cross-fitted across the same 5 spatial folds (each fold mapped by a curve
  fitted on the other four), sample weights as in training.
- **B1:** inside Arunachal, pooled: every range at 5%+ holding ≥20 flooded
  rows within ±30% (said vs happened); every lower range within ×2.
- **B2:** the 5%+ ranges together, inside Arunachal, within ±30% in every
  fold and every year block (2015–18, 2019–21, 2022–25) that holds ≥20
  flooded rows there; smaller ones reported as too few to judge.
- **B3:** outside Arunachal, calibration error (ECE) not more than 10% worse.
- **B4:** the four physical sanity checks pass on the recalibrated map.
- **Where it applies if it passes:** only to the number *shown* ("if a flood
  comes") and the screen's low-ground mask. The model's own WHERE — the day
  model's floodable-area input and the joined product — stays first-stage,
  so no forecast number moves.

### Phase 4 — Confidence levels (M) — **Gate C**

Per rain cell (and so per place), from data only:

- **records:** flood records within 10 km, 2015–2026;
- **looked-at share:** the share of floodable ground within 10 km that was
  ever inside a satellite flood check.

Pre-registered levels: **High** = ≥3 records and ≥50% looked-at;
**Medium** = ≥1 record or ≥20% looked-at; **Low** = neither.

- **Gate C:** assign levels from ≤2022 data only, then grade 2023–26 by level.
  High must meet A1/A2 on its own. If High does not measurably beat Medium,
  merge them — never show a distinction the data can't back.
- **Gate C′ — restated 2026-09-27, before any level was graded.** Gate A
  failed and the user chose to show the % as *approximate*, so "High meets
  A1/A2" can no longer be the bar. Evidence is simplified to one count —
  **distinct days with a flood record within 10 km since 2015** (the
  "looked-at share" was dropped: satellite windows are centred on the
  records, so it mostly repeats the count). Levels: **High ≥3 days, Medium
  1–2, Low 0**. Graded on the Gate A test (weekly, non-overlapping,
  2023-01-01 → 2025-10-31), levels from records ≤2022: keep High separate
  from Medium only if High has **both** a higher ranking AUC **and** a
  forecast÷recorded ratio closer to 1 (|log ratio| smaller); otherwise merge
  them into one "floods on record here" level. A level with <10 floods in the
  test is "not measurable" — which is what Low means, and is said so on
  screen.
- **Known, unresolvable-with-this-data ambiguity (write it down, don't hide
  it):** the model deliberately uses terrain + rain, not where floods were
  reported before, so a remote valley isn't told it never floods. So in
  well-reported places it may say less than the record shows, and in
  unreported places more. We will measure the first; the second can't be
  measured without local truth. This is exactly what Low confidence means,
  and what Jang gauges, field checks and people's reports lift.
- Screen wording, true by construction: *High — "N floods on record within
  10 km since 2015; our forecasts are checked against them."* *Low — "Few or
  no floods on record near here, so we can't yet check this number here. It
  still uses the same rain and land-shape reasoning."*

### Phase 5 — River gauges: right river, Google-style graph (M)

**5a. Which gauge belongs to a place** — new `scripts/build/build_gauge_link.py`
→ `webapp/assets/flood/gauge_link.npz` (per display cell: gauge, upstream or
downstream, km along the river; or none, with why). Rule, physical and
explainable: a gauge is on this place's river when **the place's nearest
channel and the gauge are on one flow path** (following the 100 m
flow-accumulation walk already used in `build_gauge_reach.py`) **and the river
is about the same size at both** (drainage area within ×0.5–×2, so a small
tributary or a river doubled by a big confluence is "a different river"), and
the place is within WHERE's 25 m-above-channel ceiling of it. Checks: known
pairs (Pasighat town ↔ Passighat gauge on the Siang; a Tawang ridge ↔ none)
plus a small synthetic-grid test.

On screen: linked → "River gauge on this river: *Name*, N km upstream";
not linked → "No river gauge on this stream" (and the nearest gauge only as
"elsewhere, for reference", collapsed).

**5b. The graph** (Google Flood Hub style, Altair — already installed with
Streamlit, no new dependency):

Passighat's published lines, as an example (real values from its CWC record):

```
 River level (m)                          │ Now
 157.54 ─ ─ ─ ─ ─ highest ever (11 Jun 2000)│
 153.96 ─────────────── danger level ───────│──────────────
 152.96 ─────────────── warning level ──────│──────────────
       ▁▂▃▅▆▅▄▃▂▂▃▄▅▅▄▃  measured, last 30 days
                                            │ ██ ▇▇ ▅▅ ▃▃ ▂▂ ▂▂ ▁▁
                                            │ chance of crossing the
                                            │ danger level, each day
```

- Top: measured daily maximum for the last 30 days (solid; gaps left as gaps,
  never joined up), a "Now" line, and horizontal lines: **warning, danger,
  highest-ever** for CWC gauges that publish them (already on disk in
  `data/raw/11_gauges/cwc/*_static.json` → copied by a small build step to
  `webapp/assets/flood/gauge_levels.json`), and the **line our chance refers
  to** — the official danger level, or for the others "high-water mark: the
  river's own wettest 2% of days" plus its typical level.
- Bottom, same time axis: bars for the chance of crossing that line on each
  coming day, each marked with what it rests on ("rain + river reading, 1 day
  old" or "rain only — gauge offline since …").
- Units per network: CWC = water level (m); NWDP = flow (m³/s). NWDP
  publishes ~2 days late, so its measured line ends earlier — the graph says so.
- **No dotted water-level forecast line** (Google has one). We forecast the
  chance of crossing, not the level; a level line appears only after Phase 10.

**The trap this phase must not fall into:** widening the fetch window inside
`flood_gauge_live.forecast()` from 8 to 30 days would silently change live
logic — a gauge silent for 10–30 days would stop being flagged offline, and
"above threshold now" could come from a weeks-old reading. So history is
fetched by a **separate display-only function**; `forecast()` is untouched;
Phase 0's golden run proves it.

### Phase 6 — The screen (M)

Layout only — **the numbers in this sketch are made up**; real ones come from
the gates.

```
┌ Selected: Pasighat ─────────────────────────────────────────┐
│ FLOOD CHANCE NEAR HERE · next 7 days (27 Sep – 3 Oct)       │
│   6%                     ← colour of its range              │
│   chance of a flood within about 10 km of here              │
│   Confidence: High — 14 floods on record nearby since 2015  │
│   ▁ ▂ ▃ ▅ ▃ ░ ░   day by day (days 4–7 lighter)             │
│                                                             │
│ THIS SPOT                                                   │
│   If a flood comes, chance this spot is under water: 1%     │
│   High ground. Nearest low ground 0.8 km away: 18%          │
│                                                             │
│ RIVER GAUGE ON THIS RIVER · checked forecast                │
│   Passighat (Siang), 3 km upstream                          │
│   Tomorrow: 2% chance of reaching the danger level          │
│   [graph as in 5b]                                          │
└─────────────────────────────────────────────────────────────┘
```

- **Map:** low ground (WHERE ≥ the Phase 3 threshold) coloured by the
  near-here chance for the chosen period — "Next 7 days" (default) or one
  day. Legend in plain ranges, no adjectives: `<2% · 2–5% · 5–10% · 10–25% ·
  25%+` (the gauge models' existing band edges, so one scale everywhere).
  Legend note: "colour = chance of a flood near here; shown only on low ground
  a flood can reach". Gauge dots: that day's chance, or in "Next 7 days" mode
  **the highest single-day chance this week**, labelled as such (a week
  chance for gauges is not computed or checked, so it is not claimed).
- **Day strip:** "Next 7 days X%" + one button per day with its % —
  for the selected place, else the whole state (label says which).
- **Metrics:** chance of a flood somewhere in Arunachal this week (E) · rivers
  with 10%+ chance · highest river chance · rivers above danger level now.
- **Rivers table:** chance as a number and bar; the old "Level" words dropped.
- **Removed from screen:** every "× usual / × normal", "Rain risk", and the
  Watch/Alert/Warning/Danger chance words.
- **"How to read this"** box rewritten from §8.

### Phase 7 — Track record for the new numbers (S)

- Daily run logs, per issue, every cell's daily and weekly near-here chance,
  the statewide chance, and the confidence level →
  `records/flood_forecast/near_here/<issue>.npz` + `near_here_state.csv`
  (new files; existing logs untouched; ~15 KB a day).
- `forecast_log.py verify_area` grades them once flood records for those
  weeks exist (Phase 8), with the same reliability table the river scorecard
  uses. The on-screen track-record box gains an area line **only once**
  something has been graded.

### Phase 8 — Keep evidence coming in (M, then ongoing)

What "we are gathering data for these places" will truthfully mean — and the
screen says it only once each part is running:

1. **Gauge-triggered satellite checks (automatic, free):** when a gauge
   crosses its line, queue a Sentinel-1 check of the reach below it (the
   Earth Engine route already used in §5i/§5m). A confirmed result becomes a
   dated flood record.
2. **People's reports:** a "Report a flood" link on the screen (a simple form
   to start: place, date, photo optional) → each report gets the same
   Sentinel-1 check before it counts.
3. **Open news/disaster feeds** as candidate reports → same check.
4. **Partners, not blockers:** Jang pilot gauges and field checks; PWD
   road-block logs if they come. Nothing waits on them.

Each new confirmed record grades the logged forecasts (Phase 7) and updates
confidence levels at the next rebuild. The satellite-everywhere auto-grader
stays off — it was tested and failed (§0t).

### Phase 9 — Write it all down (S, at every phase)

- This file: status per phase + every gate's measured result.
- FLOOD_MODULE.md: replace "What can honestly be quoted" once shipped.
- PARKED_HIMALAYAN_FLOOD_WHERE.md: new §0v with the Gate A/B/C numbers.
- FLOOD_WHEN_PILOT_PLAN.md §13: gauge link + graph.
- Method page ("How to read this forecast") in the app, from §8.
- Memory: `flood-screen-plan`, plus `flood-forecast-joined`.

### Phase 10 — Later, only with its own test (L)

> ⭐ **IMPORTANT — the next big feature** (marked by the user, 2026-10-05):
> the river level forecast line below. **Live to 2 days ahead since
> 2026-10-06** (FLOOD_WHEN_PILOT_PLAN.md §14); the rest is still to build.
> Summary and why it matters: [FLOOD_MODULE.md](FLOOD_MODULE.md), top callout.

- **River level forecast line** (the dotted line on Google's graph): a
  model forecasting the daily level range (low / middle / high) at leads 1–7.
  Shown only if, on held-out years, the chance of crossing implied by its
  range agrees with the checked crossing chance — two forecasts on one graph
  must never contradict each other.
- A water-level graph for the whole reach (a virtual gauge), once 5a exists.

**Agreed 2026-10-06** (go-ahead from the user; full recap in
[RIVER_FORECAST_RECAP_2026-10-06.md](RIVER_FORECAST_RECAP_2026-10-06.md) §7):
- Feed the level model **a week of the gauge's hourly levels** and **the
  gauges upstream** where a chain exists, plus rain — what Google's own
  level model reads (FLOOD_HUB_AND_MOCKUP_COMPARISON.md §3). Today's gauge
  model sees one day's high and one day's change.
- Aim at **1–2 days ahead first**, where Google's level model stops; go
  further only if the tests carry it.
- Tests to write before building, besides the rule above: of the days a
  high river is given under 5%, fewer than 1 in 10 may flood (the open
  fault, FLOOD_WHEN_PILOT_PLAN.md §13j); not less accurate than the live
  models; any pattern used as an input must hold from one year to the next.
- **Second step:** Google's open-sourced river model beside ours as a
  second opinion and a yardstick — never the core, credited honestly.

## 7. Things we will NOT do, and why

- **Show "this 100 m spot, today: X%" as the headline** — tiny, uncheckable
  per spot, ~4× high in Arunachal (§3).
- **Calibrate each area to its own report count** — that teaches remote
  valleys they never flood (§0p). One calibration, confidence levels on top.
- **Fold the river chance into places** — tested on the map, made it worse (§0s).
- **Use satellite water everywhere as automatic truth** — tested, failed (§0t).
- **Draw a level forecast we don't make** (Phase 10 first).
- **Show a confidence difference the test can't back** (Gate C merges levels).

## 8. What we will be able to say (plain words; numbers filled in from the gates)

- **The big number:** "The chance of a flood within about 10 km of here in the
  next 7 days. It's worked out from the forecast rain here and upstream, and
  the shape of the land. We tested it on 2023–26 floods the model never saw:
  when it said about X%, about Y% happened." *(Gate A)*
- **Why so small most of the time:** "Floods at any one place in any one week
  are rare. A small number is the honest answer, not a broken one."
- **Confidence:** "High means many past floods near here to check against.
  Low means few or none on record — often because nobody reported them, not
  because none happened. The number still uses the same reasoning, we just
  can't check it there yet."
- **The spot:** "If a flood comes, how likely water reaches this exact spot,
  from its height above the river and the shape of the valley." *(Gate B)*
- **The river:** "At a river gauge we measure the river every day, so that
  forecast is checked daily against the real level."
- **What it doesn't count:** "Floods nobody reported, and flash floods that
  drain before a satellite passes. So in steep valleys the real chance can be
  higher than shown."

## 9. Open risks

- Gate A may pass region-wide and fail inside Arunachal (≈150 in-state
  floods in 2023–26 is a small test). The pre-registered 20 km fallback exists
  for this.
- Forecast-rain archives for days 4–7 may not reach back far enough for a
  meaningful per-lead test; then days 4–7 stay marked as less reliable.
- The reporting-propensity ambiguity (Phase 4) cannot be settled with news
  reports; only local truth settles it.
