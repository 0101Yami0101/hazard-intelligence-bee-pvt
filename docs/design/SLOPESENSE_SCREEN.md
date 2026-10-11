# SlopeSense screens — the FloodSense look (2026-10-10)

SlopeSense was still the August design: a map card, a row of day buttons, a
scrolling inspector, plain metric cards. FloodSense had been rebuilt as
dashboards on 2026-09-28/29. This brings SlopeSense to the same look, built
from the same pieces, so the two modules read as one product.

**The maths did not change.** Susceptibility × rain trigger, the same cuts,
the same rain. What changed is how it is laid out — and three faults in the
old screen that turned up while every number was being compared (§4).

Code: `webapp/products/landslide/view.py` (pages), `webapp/products/flood/ui.py`
(the shared look), `webapp/core/grid.py` (`district_raster`).

---

## 1. The layout, the same on every page

1. **Header** — logo, title, one line, and the place search (the same session
   key as FloodSense, so a place picked in one module is still picked in the
   other). On Roads the right-hand slot is the route picker.
2. **Key** — the badges this page uses and one "what this is not" note.
3. **Tiles** — six numbers for the whole state.
4. **Main row** — place | map | side panel. The three end on one line while
   there is room (1,304 px of page); narrower, the side panel drops under the
   map; on a phone everything stacks.
5. **Below** — the place's week in full, tables, and "how to read" folded away.

Explanations sit behind an ⓘ or a badge's hover. Text on screen is kept short.

## 2. The kinds of number (badges)

Same glyphs, colours and borders as FloodSense's, with SlopeSense's own words
(`ui.SLOPE_TIERS`):

| Badge | What it marks |
|---|---|
| ≈ Outlook | the landslide level, and shares of land or road at a level. **A level is a rank, not a chance.** |
| ◆ Ground | slope susceptibility — static, no rain in it |
| ☂ Input | rain, and rain vs normal |
| ◷ Record | mapped landslides — history |

Nothing on SlopeSense is shown as a probability. Shares are shares of land or
kilometres of road.

## 3. The pages

### Forecast
- **Tiles:** land at High or above · Very High · most affected district · road
  at High or above (km) · unusually wet rain points · wettest point.
- **Left:** with no place, the state's share at High or above with a bar per
  day, and the rain behind it. With a **town or a point**, its level (word,
  "3 of 5", a bar per day in each day's colour), susceptibility, rain vs
  normal, rain that day and over 7 days. With a **district**, the share of its
  own land at High or above, Very High, the highest level in it, and rain
  averaged over the rain points inside it.
- **Map:** as before (click to pick a place; a district is clipped to its
  outline). The 3D switch stays parked and visibly disabled.
- **Right:** the 7 day buttons (4 to a row, coloured top edge, days 5–7
  dashed), **districts to watch** (the six with the largest share at High or
  above; a click opens the district), and a link to Roads with the day's km.
- **Below:** the place's week as a chart and a day-by-day table; all 18
  districts as a table with its CSV; how to read the levels.
- On the full-screen map the place box and colour key ride on the map, as on
  FloodSense.

Day buttons say what they show: "level at this place", "share of the district
at High+", or "share of the state at High+". Levels are shortened on the
buttons (V.Low, Low, Mod, High, V.High); the full word is the button's hint.

Shares under 10% are shown to one decimal ("1.7%"); a share above zero that
would round to 0.0% is shown as "<0.1%".

### Roads
- **Tiles:** road at High or above · Very High km · hotspot stretches · longest
  stretch · worst day this week · road assessed. With a route: length, km at
  High or above, Very High km, worst point, and the network figure.
- **Left:** the network's km at High or above with a bar per day and the five
  worst stretches; or the route's km at High or above and its km by level.
- **Right:** day buttons (network km at High or above), the network by level,
  a link to the forecast.
- **Below:** the worst-stretches table and CSV (network), or the elevation and
  outlook profiles and CSV (route).

### Susceptibility
Now takes a place (search or click), like FloodSense's Flood-prone ground.
- **Tiles:** checked on unseen ground (86 in 100) · landslides it learned from
  · top 10% of land holds 71% of mapped landslides · Very High ground 13.4× ·
  what it reads (34 inputs) · not scored (share of the state).
- **Left:** mapped landslides by level and the most susceptible districts; or
  the place's susceptibility on a 0–1 meter; or the district's shares.
- **Right:** land by level, what it is read from, a link to the forecast.

### Evidence, Model & validation
Reached from the ℹ️ menu as before. Same header and tiles; content unchanged.

### Changed 2026-10-11: real numbers in place of "3 of 5"
The place card's headline is now the level's measured figure ("3× the
usual"), with the ground and the rain each as a measured multiple, and the
day buttons and colour key carry the same figures. Why, the measurement and
its rules: [LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md).

## 4. Three faults found in the old screen, and fixed

All three were found by running the old and new pages side by side on the
same rain (§5).

1. **District figures were taken over the box around each district, not its
   outline.** A box holds large parts of the neighbours: Upper Siang's box has
   51,317 scored cells, its outline 25,928. On 10 Oct, 14 of 18 districts read
   differently (Lohit 2.4% in the box, 1.1% in its outline; Upper Siang 1.3% →
   0.5%). The page said so in a caption. Now `core.grid.district_raster` draws
   the 18 outlines once and every district figure and clip reads it. A cell on
   a shared border goes to the district listed first (39 cells).
2. **Every district picked after the first was shown through the first one's
   outline.** The clip came from a cached function whose cache key left the
   outline out, so the cache returned the first district's mask for all of
   them — for every visitor, until the app restarted. Shown in the test: the
   old page's colour key for Upper Siang, picked second, was Kurung Kumey's
   (59/26/13/2/0) and not its own (58/33/9/0/0). That function is removed.
3. **"Clear route" on Roads crashed** ("`st.session_state.rd_from` cannot be
   modified after the widget … is instantiated"). It now clears in a callback.

Also made consistent:
- **One answer for a town on flat ground.** The old inspector read the town's
  own cell and said "Not assessed"; the strip and the panel under the map read
  the nearest scored slope and gave a level. Every panel now reads the nearest
  scored slope and says how far away it is.
- **Week figures follow the rain.** They were cached under the date alone, so
  after the hourly rain refresh the day buttons could describe the earlier
  rain beside a map drawn from the new one. They are now keyed on the rain.

### The daily log follows
`scripts/model/landslide_forecast_log.py` logged the district table as the
page showed it — the box figures. It now reads the same `district_raster`, so
the log is still the screen. The one issue logged before the change
(2026-10-10) was rewritten from its own issue file with the new `rebuild`
command; `state.csv` came out byte-identical, `districts.csv` changed. The
table as first written is kept in
`records/landslide_forecast/_box_figures_until_2026-10-10/`. `check` and
`test` pass.

## 5. Checks

| Check | Result |
|---|---|
| Old page vs new page, same rain, one process (`check_numbers.py`, scratch): day figures, tiles, colour keys, the day-by-day table, the worst-stretches table, route figures, susceptibility — 43 comparisons | 43 of 43 |
| District table against the 18 outlines worked out independently | equal |
| Every screen opens without an exception (`scripts/run/check_app_screens.py`, 34 cases, 13 new for SlopeSense: town, district, flat-ground point, point outside the state, last day, a route, Evidence, Model) | pass |
| Browser, 1920 px: the three panels end level on 9 page states; later day, map click, full-screen panel, district to watch, Clear route, Evidence, Model; no console errors | pass |
| Browser, 1552 and 1366 px (side panel under the map) | pass, except one step at 1366 px: the test's map click landed outside the state, so the full-screen box correctly showed "outside the mapped area" and not a level. The same step passes at 1920 px. |
| Phone and tablet survey (`scripts/run/check_app_mobile.py`) | see §6 |
| Landslide log `check` and `test` | pass |

## 6. Phone and tablet

The first survey found one fault: on a 768 px tablet with the menu open the
page is 470 px wide, Streamlit still lays columns side by side there, and the
header's search row ran off the right edge. The header (shared with
FloodSense) now wraps when its own box is under 640 px: title, then the
search box, then its buttons two to a row.

The screenshots also showed the day buttons on a phone as two columns reading
downwards, not four to a row — on FloodSense as well, where the 2026-10-10
phone fix had been reported as "four to a row" (correction in
FLOOD_SCREEN_PLAN.md). Fixed in the shared rule; measured at 390 and 360 px on
both forecast pages: 4 in the first row, in date order, none cut off.

Result of the final survey, all 14 pages at 4 screens: 56 of 56 with no fault.

## 7. Left as it is

- **3D** stays parked (`WIP_3D`); the code paths are intact.
- **18 districts.** The district layer is the older 18-district set; newer
  districts are not in it.
- ~~The model's own caveat list still said rain is "~33 km sampled".~~ Fixed
  2026-10-11 at its source (`export_webapp_bundle.py`) and in the shipped
  `metrics.json`: "~22 km (219 points)".
- **The shared look still lives in `products/flood/ui.py`.** Moving it to
  `core/` is a tidy-up, not a behaviour change.
- **Not yet checked on the host's newer Streamlit** (1.65; this PC has 1.60),
  the same open item as the 2026-10-10 phone fixes.
