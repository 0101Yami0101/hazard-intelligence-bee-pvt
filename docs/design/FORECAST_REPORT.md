# One-page forecast report (2026-10-10)

A single printable page with **both forecasts** for one selection: a town or
point, a district, or the whole state. It was in the mock-up
([FLOOD_HUB_AND_MOCKUP_COMPARISON.md](FLOOD_HUB_AND_MOCKUP_COMPARISON.md),
"generate report") and had not been built.

Code: `webapp/products/report.py`. Button: under the main row on SlopeSense's
Forecast page and FloodSense's Live forecast page ("📄 One-page forecast
report · <place>").

## What it is

- A self-contained **HTML page** (about 9 KB, no images, no outside files),
  laid out for A4 in a light theme. It opens in any browser; printing it and
  choosing "Save as PDF" gives a PDF. A line above the page says so (it does
  not print).
- **Not a PDF made by the app.** That needs a PDF library on the host; the
  app is deliberately kept to pure-Python packages.
- Built **when the button is pressed**, not on every redraw of the page: the
  button is handed a function (`download_button(data=callable)`). This needs
  Streamlit 1.60 or newer; both `requirements.txt` files now say so (the host
  runs 1.65).

## What is on it

| | Town or point | District | State |
|---|---|---|---|
| **Landslide outlook** | level today ("Level 3 of 5 · Moderate"), the level on each of 7 days, susceptibility, rain vs normal, rain today and over 7 days; the nearest-slope note when the point is flat ground | share of its land at High or above today and each day, Very High, highest level, rain averaged over its rain points | share of the state at High or above, wet points, wettest point, the 4 districts to watch |
| **Flood outlook** | chance of a flood within ~10 km over 7 days and each day, floods on record, "if a flood comes" for the spot, the gauge on its own river with its chance and what it reads now | the highest of its ~10 km areas, the 5 areas with the highest outlook, the gauges inside the district | chance of a flood anywhere, rivers above their line, gauges reporting, top 4 areas and top 4 gauges |

Then six short "how to read" notes and a footer.

## Rules it keeps

- Every number comes from the functions the screens use (the landslide maths,
  `core.grid.district_raster`, the flood snapshot and `live.py`'s helpers).
  Nothing is worked out a second way.
- A landslide level is a rank, not a chance. The flood chance near a place is
  marked approximate, the gauge chance checked. "If a flood comes" is capped
  at 20%+. Numbers are never multiplied together.
- A river above its line reads "unsure", as on screen.
- It says when each half was issued: the landslide outlook is worked out from
  rain read at the moment the report is made; the flood forecast is the daily
  run's, with its date and time, and "N days old" if it is not today's.
- Later days (weaker rain forecasts) have dashed boxes: days 5–7 for
  landslides, days 4–7 for floods, as on each screen.

## Checks (`check_report.py`, scratch)

| Check | Result |
|---|---|
| Builds for 8 selections: state, two towns, a flat-ground town, two districts (one with no rain point or gauge inside it), a point, a point outside the state | 8 of 8 |
| Same numbers as the screens, on the same rain and snapshot: land at High or above, wet points, a town's level / susceptibility / rain, a district's share, flood chance for the state and a town, "if a flood comes", the river gauge and its chance, floods on record | 11 of 11 |
| Printed to A4: one page, nothing overflowing | 8 of 8 |
| The button in a browser, both pages, state / town / district: a file downloads with the right place in it | 5 of 5 |
| All 34 screen cases still open; desktop layout; phone and tablet on the four forecast pages | 34 of 34 screens open; desktop 18 of 18; phone and tablet 16 of 16 with no fault |

## Left out

- **No map** on the page. A map image needs either a tile fetch at report
  time or a drawing library on the host.
- **Today only for the headline.** The 7-day strip is there; the report is
  not re-cut for a chosen later day.
- **No watchlist or scheduled sending.** The mock-up's "watchlist" and
  "officer login" need proper hosting.

## Also on 2026-10-10: the brief, deck and script were refreshed

- **Figures:** 29 sources and about 308 GB (was "24 sources, about 8 GB");
  4,032 flood forecasts written down and 1,938 graded (was 3,136 and 1,564);
  landslide forecasts are now "written down daily, not graded" (was "not
  logged"); the level line graded, 85 so far, typically 4 cm off.
- **Stale notes removed:** the Data Backbone pages "last rebuilt on 17
  August", the "27 yr" tile, the SlopeSense chart "out of order", the
  "33 km" label. Added: the one-page report button, SlopeSense's new look.
- **Screens re-captured:** six in BRIEFING.html (pipeline, catalogue, rain
  archive, SlopeSense, FloodSense, track record) and four in
  PRESENTATION.html, with the numbered pins moved to the new layout.
- **Files:** docs/BRIEFING.md, BRIEFING.html, PRESENTATION.html,
  PRESENTATION_SCRIPT.md, PRESENTATION_SCRIPT.html. All open with no console
  errors; the deck still has 13 slides.
- **Not re-made:** the small slide thumbnails inside PRESENTATION_SCRIPT.html,
  and the landing-page and layer-explorer pictures (those screens did not
  change).
