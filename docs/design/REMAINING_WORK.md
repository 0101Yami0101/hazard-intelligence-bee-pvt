# What is left to do — as of 2026-10-11

The working list made on 2026-10-09 ("push the application as far as it
will go now"), with everything done since crossed off. One place to look so
nothing is lost. The soil-erosion module for Assam is **not** on this list
by the user's instruction (it has its own plan: EROSION_PLAN.md).

## 1. Open, not started

| # | Item | Size (estimate) | Notes |
|---|---|---|---|
| **15** | **Landslide timing learned from the whole Himalaya** | 3-hour download + about a day | The biggest gain left for the landslide forecast: its "when" half rests on 84 dated landslides in the state; the Himalayan arc has about 800 more. The download was stopped at 10% and resumes. Steps: [PARKED_HIMALAYAN_POOLED_TRIGGER.md](PARKED_HIMALAYAN_POOLED_TRIGGER.md). It would also firm up the roughest number on the place card ("High = 3×", from 8 landslides) and settle whether a weak slope should read High on a below-normal rain day ([LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) §4). |
| **16b** | **The level line beyond 2 days** | 1–2 days | May fail: beyond 2 days the line and the chance disagreed too often when it was last looked at. Rules first. FLOOD_WHEN_PILOT_PLAN.md §14. |
| **21** | **News-feed intake for flood reports** | 2–3 days | So the flood chance *near a place* can be graded as records arrive. Today new records come only from gauge crossings and the report form. |
| **17** | **Google's open river model beside ours** | 3–5 days | As a second opinion, not a feed. A new model to install, feed and compare. |

## 2. Outside the code

| # | Item | Notes |
|---|---|---|
| **23** | **Data request letters** | [GOV_DATA_REQUEST_LIST.md](GOV_DATA_REQUEST_LIST.md). Added by this round of work: **dam release schedules** (Pare HEP's level follows the gates, FLOOD_WHEN_PILOT_PLAN.md §20) and **CWC's danger level for Rho Basti** (§19b). Road-block logs with chainage remain the best ask for landslides. |
| **24** | **Bhoonidhi sign-up and the Inner Line Permit** | |

## 3. Parked on purpose

| # | Item | Where |
|---|---|---|
| **2** | Move the daily forecast off this PC | [PARKED_OFF_PC_DAILY_RUN.md](PARKED_OFF_PC_DAILY_RUN.md) |
| **19** | Finer rain (11 km in place of 22 km), after item 2 | the same file, §4 |

Un-park when days are missed or late again: two days were missed and six
ran late in the first three weeks.

## 4. Decisions waiting on the user

1. **Pare HEP's flood chance.** Its level line is off (a dam gauge). It
   still gets a *chance* of reaching a line that rests on 62 days of
   record. Keep, mark as unsure, or remove? Removing changes the logged
   record. FLOOD_WHEN_PILOT_PLAN.md §20.
2. **Dash only days 6 and 7?** Measured on two monsoons, days 4 and 5 rank
   as well as days 1–3; the drop is at 6 and 7. Left as it is (4–7 dashed)
   until a rule is written and next monsoon's data is in.
   [LEAD_DAY_TEST.md](LEAD_DAY_TEST.md) §3.
3. **"High" on a below-normal rain day.** Looked at, left alone, with the
   reasons. [LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) §4.
4. **Tighter screenshots** in the brief and deck (the new ones have a wider
   empty margin than the old).
5. **Local `main`** still sits on the old public history, so the editor
   lists about 240 files as changed. Pointing it at the private backup
   would clear that; it changes nothing that is deployed.

## 5. Small things noticed, not fixed

- **The first Changlang station** has wrong coordinates and is not linked
  to places (§19a deals only with the second).
- **18 districts.** The district layer is the older 18-district set.
- **The shared look lives in `webapp/products/flood/ui.py`.** Moving it to
  `core/` is a tidy-up.
- **3D view** stays parked (`WIP_3D`).
- **The flood log does not record the time of issue**, so a late run is not
  visible in it (to fix with item 2).
- **Evidence page figures** ("9,555 days", "8.2 M cells") are typed in, not
  read from files.
- **The landslide log** is written on this PC only; the hosted app does not
  log.

## 6. Done since 2026-10-09 (for the record)

| # | Item | Where it is written up |
|---|---|---|
| 1 | Private backup of the whole project | memory; this file §7 |
| 3, 10 | Withdrawn flood record; small display fixes | FLOOD_SCREEN_PLAN.md |
| 4, 5 | Four false floods removed; day model re-fitted | FLOOD_WHEN_PILOT_PLAN.md §15 |
| 6 | SlideSense forecasts written down daily | ROADMAP_LANDSLIDE.md |
| 7 | Level line graded daily | FLOOD_WHEN_PILOT_PLAN.md §16 |
| 8 | River above its line shows "unsure" (a stopgap; seven cures tested) | §17–§18 |
| 9 | Full-screen box on all three flood pages | FLOOD_SCREEN_PLAN.md |
| 11 | Phone and tablet check, with fixes | FLOOD_SCREEN_PLAN.md |
| 12 | SlideSense in the FloodSense look; district figures on real outlines | [SLIDESENSE_SCREEN.md](SLIDESENSE_SCREEN.md) |
| 13 | One-page forecast report | [FORECAST_REPORT.md](FORECAST_REPORT.md) |
| 14 | Brief, deck and script refreshed | FORECAST_REPORT.md, end |
| 16 | Upstream gauges for the high-river fault: tested, no gain | §17 |
| 18 | Forecast graded by lead day | [LEAD_DAY_TEST.md](LEAD_DAY_TEST.md) |
| 20 | Gauge housekeeping, then both models re-taught | §19 |
| 22 | Compared with GSI's 50 m map; GSI's map re-fetched correctly | [GSI_MAP_COMPARISON.md](GSI_MAP_COMPARISON.md) |
| – | Pare HEP: no level line for a dam gauge | §20 |
| – | Real numbers ("3× the usual") in place of "4 of 5" | [LANDSLIDE_TIMES_USUAL.md](LANDSLIDE_TIMES_USUAL.md) |
| – | Renamed: platform = SlopeSense, landslide module = SlideSense | §8 below |
| – | Presenter's script: fuller spoken words, a new opening (how the idea formed, the two things learned), then cut down by the user's instruction to the words alone, slide by slide | docs/PRESENTATION_SCRIPT.md |
| – | Home page tells the idea in five parts, matching the script | [LANDING_PAGE.md](LANDING_PAGE.md) |

## 7. What is deployed, and what is backed up

**Public app** — `hazard-intelligence-bee`, branch `v2`, commit `dc66b2a`
(2026-10-12, the fourth push of the day after `24f7834`, `df981ac` and
`9a03e0d`). App files only (`webapp`, `requirements.txt`, `runtime.txt`,
`.streamlit`). This push changed 11 files, all described in sections 10 to
12: the satellite map as the default, the map opening one step in on
Itanagar's side, the outside shading reaching the edges, a selected district
outlined and lit alone in both modules, and a "My location" button that
works. Before it the branch already carried the new names (the platform is
SlopeSense, the landslide module SlideSense), the home page that tells the
idea in five parts, the forecast listed last in both side menus, and the
flood forecast issued 12 October. Models, logs, training scripts and
internal docs are not on it. The old app (`SlopeSense2`, `main`) was not
touched.

**The hosted flood forecast is frozen at the 12 October issue** until
someone pushes a newer snapshot: the daily 08:30 run on this PC does not
push (item 2).

**Checked before this push, on the host's package versions** (Streamlit
1.65, pandas 3.0): all 35 screens open; the map as it opens on all six
tabs, 13 of 13; a district on every map tab of both modules, 21 of 21;
"My location" allowed inside, allowed outside and refused, 28 of 28; the
home page's jump bar and Open buttons 37 of 37; phone and tablet survey of
every page 56 of 56 with no fault.

**To try once on the live app**, because no test here can stand in for it:
press "My location". The host shows the app inside its own frame, and
whether that frame lets a browser share a position can only be seen there.

**Private backup** — `hazard-intelligence-bee-pvt`, `main`: the whole
working tree as it stood after this deploy (code, app, docs, models,
records, reports), everything `.gitignore` excludes left out (`data/`,
`logs/`, `misc/`, `docs/investor`, `docs/temp`, `.env`). Its `v2` is the
same commit as the public one. It does not update itself.

## 8. The rename of 2026-10-11

By the user's decision: the **platform** is **SlopeSense**, shown on the home
page as SLOPESENSE with "Hazard Intelligence Platform" under it (the initials
make "SHIP"). The **landslide module** is **SlideSense**. FloodSense and Data
Backbone keep their names.

| Changed | Not changed, on purpose |
|---|---|
| Home page title, browser tab title | The module's web address (`?m=landslide`), so old links work |
| Module name on its tile, side menu, page footer | Folder names (`products/landslide`), session keys, CSS keys (`sl_*`) |
| One-page report: section line and footer | Models, forecast logs, records: no number moved |
| Download name `slidesense_DATE.csv` (was `slopesense_`) | Repo names and links (`SlopeSense`, `SlopeSense2`, `hazard-intelligence-bee`) |
| Brief, deck, script, README, design notes (217 places in 50 files) | The first app, still called SlopeSense; "SlopeSense v1" / "the earlier SlopeSense" in code comments mean it |
| `SLOPESENSE_SCREEN.md` → `SLIDESENSE_SCREEN.md` | `PROJECTED.md`, `WEBAPP_PLAN.md` §5: comparisons with the first app |
| Labels inside `reports/gsi_susceptibility_comparison.json` and its script (`slidesense_*`), by text, not re-run | `docs/investor/`, `docs/temp/`, `EVENT_CRASH_COURSE.md` (stale) |
| Pictures: the brief's landing and pipeline shots; all 13 slide thumbnails on the script page | |

Checked after the change: 34 screens open with no exception; the flood
golden check reports every number identical; phone and tablet survey of the
home page and the SlideSense forecast, 12 of 12 with no fault; the report
downloads 5 of 5 and carries the new names; a final search finds the old
name only where it means the platform or the first app.

## 9. Side-menu order, 2026-10-12

By the user's instruction the forecast is the LAST item in both modules'
side menus: SlideSense reads Roads, Susceptibility, Forecast; FloodSense
reads Flood-prone ground, Catchments, Live forecast. Each module still
OPENS on its forecast (`HOME` in each `view.py`; the code no longer treats
"first in the list" as "the forecast"), so links, the demo steps and the
"Open the forecast" buttons behave as before. Checked: the order, the
opening page and every menu click in a browser (11 of 11), all 35 screens.
Deployed 2026-10-12.

## 10. The map as it opens, 2026-10-12

Three changes the user asked for, all in the shared map code, so they hold
on every tab of SlideSense and FloodSense:

- **Satellite is the map a visitor gets.** `BASEMAP_DEFAULT` in
  `core/theme.py`; the picker in the side menu still lists Dark, Light,
  Terrain, Satellite in that order and remembers a visitor's own choice.
- **It opens one step in, on Itanagar's side of the state** (zoom 8, centred
  a little north of the town: `MAP_OPEN_AT`, `MAP_OPEN_ZOOM`). Nothing is
  selected by this: no pin, and every panel still reads "All of Arunachal".
  One step out shows the whole state as before. Picking a place flies to it
  as it always did.
- **The shading outside the state now reaches the edges however far out the
  map is zoomed.** The shape that shades the outside stopped 4 degrees past
  the border; zoomed right out on a wide or full-screen map that left bright
  strips down both sides. It now runs from 30 to 160 E and 15 S to 70 N
  (`webapp/assets/base/outside_mask.geojson`, and the same box in
  `scripts/run/export_webapp_bundle.py` so the next export keeps it).

One thing found on the way and fixed: with the satellite picture the map's
credit line named two different sources, wrapped onto a second line and
covered the foot of the map. The place names now carry the same credit as
the picture under them, so it prints once.

Left as they were, on purpose: the flood map's labels are still spaced for
the whole-state view (zoom 7), so they do not pile up when a visitor steps
out. The pictures of the two modules on the home page, in the deck and in
the brief were taken on the dark map and still show it.

Checked in a browser on this PC's versions and on the host's (Streamlit
1.65): all six tabs open on satellite at the new view with no pin, 13 of 13;
zoomed right out and full screen at 2,400 px wide the shading reaches both
edges; all 35 screens open; phone and tablet survey of the ten map pages
20 of 20 with no fault. Deployed 2026-10-12 (`dc66b2a`).

## 11. A selected district is lit alone, 2026-10-12

**Why FloodSense showed no district border.** It treated a district as one
point, its centre: a pin, the map at town zoom, no outline. Only SlideSense
drew the outline, in its own page code.

**Now, in both modules** (the shared map code, `core/mapping.py`):

- Pick a district and its outline is drawn, and **everything outside it goes
  dark**: the rest of Arunachal as well as the land beyond the state, with
  the overlays, rivers, roads, gauges and labels on it. Place names and hover
  tips stay readable. It is one shape, the whole view with the district cut
  out, drawn in its own layer above the markers (`overlay_group(focus=)`,
  `_spotlight`). It cannot be clicked, so a click on the dark part still
  selects the spot under it.
- **The map frames the district to fill the view** (`focus_view`): the
  closest whole zoom at which it fits a map 480 px wide, centred on the
  middle of its outline. The old rule put every district at zoom 6 to 8, so
  Papum Pare was 90 px wide on a 630 px map; they now open at 8 to 10. On a
  phone the widest districts run a little past the sides.
- A town or a clicked spot is unchanged: a pin, no spotlight. Clearing the
  selection lights the whole state again.

**FloodSense keeps the pin at the district's centre**, because its panel's
numbers are still read at that one spot (the flood chance within about 10 km
of it), not over the whole district as SlideSense's are. District-wide flood
figures would be a separate piece of work.

Two small faults met on the way, both older than this change. Fixed: in
SlideSense, picking on a new tab the place last picked on the old tab left
the new map where it opened (FloodSense already handled this). Not changed:
**a chosen place is dropped when the tab or the module changes**, in both
modules; the comments in the code expect it to carry over. Left alone until
the user says which they want.

Checked in a browser on this PC's versions and the host's: two districts on
every map tab of both modules, a click on the dark part, clearing, a town, a
phone, 21 of 21; all 35 screens open; the opening-view check 13 of 13; phone
and tablet survey of seven map pages 14 of 14. Deployed 2026-10-12 (`dc66b2a`).

## 12. "My location" works, 2026-10-12

**Why it did nothing.** The button ran a small script that asked the browser
for the position and then wrote the answer into the page's address. Streamlit
runs such a script in a sandboxed frame, and a sandboxed frame may not change
the address of the page around it. The browser refused that last step every
time, in every browser, on this PC and on the host, so the answer never
arrived. On top of that only one page said anything about a refusal or a
position outside the state, far down the page.

**Now** (`core/location.py`, `core/geo_component/index.html`):

- The asking is done by a tiny component of our own, which hands the answer
  back as its value. No extra package, no page reload: the tab, the map
  settings and the session survive a press.
- Inside Arunachal: "My location, near <town>" is selected and pinned, on
  every map page of both modules. A second press asks again.
- Every other outcome is said under the search row, on every page that has
  one: outside the state (with the coordinates), refused (and how to allow
  it), could not be found, browser cannot do it. While the browser is being
  asked it says so. The message goes as soon as a place is picked.
- A position in the address (`?geo=ok&lat=..&lon=..`) is still taken, and
  `?geo=denied` still opens the whole state; the phone survey uses the latter.

**Limits that are the browser's, not ours.** It only asks on a secure
address: the live app (https) and `localhost` are fine, the app opened by an
IP address on the office network is not. A desktop PC with no Wi-Fi often
places itself by its internet provider, which can be a city outside
Arunachal; the app then says so and selects nothing. Not yet tried on the
live app itself, where the page sits inside the host's own frame.

Checked in a browser with the position set by the test, on this PC's
versions and the host's: allowed inside, allowed outside and refused, on
every map page of both modules, a second press, a search afterwards, the
address forms and a phone, 28 of 28; all 35 screens; phone and tablet survey
of six pages 12 of 12. Deployed 2026-10-12 (`dc66b2a`).
