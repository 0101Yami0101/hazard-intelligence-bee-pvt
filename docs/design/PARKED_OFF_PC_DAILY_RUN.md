# PARKED — moving the daily forecast off this PC, and what waits on it

**Parked on 2026-10-10 by the user's decision.** Not refuted, not blocked by
anything outside us: set aside so other work can go first. This file is the
whole of it, so nothing is lost when it is picked up again.

## 1. What is parked

| # on the list | Item | Size | Why it is here |
|---|---|---|---|
| **2** | **Move the daily forecast off this PC** | 1–2 days | the item itself |
| **19** | **Finer rain** (about 11 km in place of about 22 km) | about half a day, after item 2 | only worth doing once a scheduled job fetches the rain; see §4 |

Nothing else on the current list depends on the move.

## 2. Why it matters (so it is not forgotten for long)

The forecast is made by one Windows task on this PC at 08:30
(`scripts/run_daily_flood_forecast.ps1`, registered by
`scripts/register_daily_flood_forecast.ps1`). Found from the logs on
2026-10-09:

- **Two days were missed** (1 and 3 October): the PC was off or asleep.
- **Six days ran after 14:00**, not at 08:30.
- A missed day **cannot be had back**. A forecast that was not written down
  before the day cannot be graded. That is true of both logs now: floods
  (`records/flood_forecast/`) and, since 10 October, landslides
  (`records/landslide_forecast/`).
- **The public app only shows a fresh flood forecast when someone pushes
  the new snapshot.** Off the PC, that push can be part of the run.
- "Runs on one PC" is listed as an honest limit in the brief and the deck.
  This item is what removes it.

## 3. What the move has to carry

The daily run today, in one go:

1. Fetch live rain (Open-Meteo), river gauges (CWC, NWDP), soil wetness
   (Earth Engine, needs a key).
2. Run the flood models (`scripts/model/flood_forecast_live.py`): needs the
   model files in `models/` and scikit-learn, rasterio and the rest of the
   full Python environment — **not** the app's small package list.
3. Write the flood log and grade yesterday (`records/flood_forecast/`).
4. Write the landslide log (`scripts/model/landslide_forecast_log.py`, from
   the same rain fetch).
5. Write the web snapshot (`webapp/assets/flood/live_forecast.json` and
   the day's files).

**Rules it must keep**

- The public repos get **app files only** (`webapp`, `requirements.txt`,
  `runtime.txt`, `.streamlit`). Models, logs, training scripts and internal
  docs stay private. So the job runs from the **private** repo
  (`hazard-intelligence-bee-pvt`) and pushes only the snapshot to the
  public `v2` branch.
- Keys (Earth Engine and any other) live in the host's secret store, never
  in a file in the repo.
- The logs must keep growing in one place. If the job writes them, it must
  commit them back to the private repo; the PC's copy then follows it, not
  the other way round.
- The issue time is still not written into the flood log (found 2026-10-09).
  Fix it as part of this, so a late run is visible in the record.

**To decide when it is picked up** (not decided now)

- Where it runs: a scheduled GitHub Actions job on the private repo is the
  obvious first candidate (no new account, secrets store built in). Its
  timing can drift by some minutes and a free-tier job has a time limit, so
  the run's length there must be measured first. A small always-on server
  is the alternative.
- How the model files get there (in the private repo, or a release asset).
- Whether Earth Engine will accept a service-account key from that host.

**How to know it worked** (to be written as pass/fail rules before the run)

- For one recorded day, the hosted run gives the same numbers as this PC
  (`scripts/model/check_live_unchanged.py` is the tool: every old number
  identical).
- Both run side by side for a week; the PC's task is switched off only
  after seven days with no missed or late hosted run.
- The public app shows the day's issue without anyone pushing by hand.

## 4. Item 19, finer rain — why it waits

- Live rain is read at 219 points about 22 km apart. The rain history the
  timing was tested on is about 11 km (892 points). The gap is a
  free-service limit on how often rain can be asked for, not a science
  limit (RAINFALL_RESOLUTION_LIMITS.md).
- Today the landslide page fetches rain **when someone opens it**, so every
  extra point costs every visitor time and counts against the hourly cap.
- Once one scheduled job fetches the rain **once a day** and ships it with
  the snapshot, asking for 892 points costs a few more calls once, not on
  every visit. That is why it becomes cheap after item 2 and not before.
- **What it needs when done:** the climatology the rain is scored against,
  rebuilt for the 892 points; the catchment-to-rain-point table rebuilt
  (`build_flood_layers.py --rain-points-only` — a table built for another
  set of points silently shows each place another place's rain: that
  happened from 22 to 27 September); the landslide log's static checksums
  will change, which the log handles; then the golden check and the screen
  checks.
- **Measure, do not assume:** whether 11 km live rain scores better than
  22 km has not been measured. Write the pass/fail rule first.

## 5. Picking it up again

1. Read §3. Measure how long the full daily run takes on this PC and how
   big `models/` is.
2. Decide where it runs; put the keys in that host's secret store.
3. Write the pass/fail rules of §3 into this file, then build the job.
4. Run side by side for a week. Switch the PC task off only after that.
5. Then item 19, with its own rule written first.
6. Update: PLATFORM_ARCHITECTURE.md ("Scheduling"), the brief and deck
   ("It runs on one PC"), and the Data Backbone pipeline page, which shows
   "Hosted scheduling" as planned.
