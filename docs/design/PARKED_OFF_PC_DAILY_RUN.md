# Moving the daily forecast off this PC, and what waits on it

**Un-parked 2026-10-20 (user: move it to the Modal workspace).** Parked
2026-10-10 by the user's decision; §0 is the live state, §1–§5 the original
notes. Since parking: 13 and 15 October were also missed, and every run in
the week to 19 October started between 10:00 and 19:14, never 08:30.

## 0. Live state (2026-10-20)

**Decided**

| Question (§3) | Answer |
|---|---|
| Where it runs | **Modal**, workspace `pankajkarjay` (the user is an invited member; free Starter plan, $30/month credit, at most 5 scheduled jobs). Modal profile `pankajkarjay` on this PC; the default profile `yami0101` belongs to another project and is never switched. |
| How code and models get there | Uploaded **from this PC at each deploy** (`modal deploy`): code, the three model folders (16 MB) and the six data files the run reads (2.4 MB, found by tracing a real run). The private repo is not used: its models were last refreshed 2026-10-12. |
| Where the logs live | A Modal storage volume (`slopesense-daily`): `records/`, `reports/`, the run logs, the web snapshot. Seeded once from this PC. |
| Earth Engine from the host | **Yes**: robot account `slopesense-daily@earthengine-507510.iam.gserviceaccount.com` (roles Earth Engine Resource Viewer + Service Usage Consumer), key in the Modal secret `slopesense-ee`. Tested 2026-10-20: 11 days of soil water identical to the personal login. |
| How the app gets the day's forecast | **Not a push.** The job publishes the snapshot at one read-only link (`https://pankajkarjay--slopesense-flood-latest.us-east.modal.run`; the address without `.us-east` also answers); the app fetches it at most hourly and keeps its bundled copy if the link is down (`webapp/products/flood/feed.py`). No GitHub token, no daily app restart. |
| Cost | A run takes 2.5–3.5 min on this PC (traced 2026-10-20: 203 s and 155 s) and under a minute on Modal in Mumbai (53 s). With the India region's 1.75× price, well under $2 a month of the $30 credit. |

**Built** — `scripts/cloud/modal_daily.py` (run, schedule, link, check,
seed, pull). Code changes for the host, all inert on this PC:
- `fetch_39_era5land_soil.ee_init()`: signs in with `EE_SERVICE_ACCOUNT_KEY`
  when set, else the saved personal login as before.
- `flood_forecast_live.live_soil`: with `SOIL_REQUIRED=1` (set by the cloud
  job only) a missing soil input fails the run, so it is retried, never a
  quiet rain-only forecast.
- `forecast_log`: the flood gauge and area logs now carry `issued_at`, as
  the landslide log already did (rows before 2026-10-20 have none).
- The container runs in India time (`TZ=Asia/Kolkata`), so issue dates and
  "made at" times match the PC's.

**Found while building (2026-10-20) — both would have passed unnoticed**
- **The CWC gauge site does not answer from abroad.** From Modal's US
  (Boydton), Tokyo and Jakarta machines every CWC request hung until its
  60 s timeout; from Mumbai it answers in 0.1–2 s (NWDP and Open-Meteo answer
  from anywhere). The run does not fail without gauges — it carries on with
  rain only — so the job is **pinned to Modal's India region (`ap-south`,
  1.75× the base price)**, and a run where **no CWC gauge has a fresh
  reading is retried** (on the last try it is kept, and the status says so).
- **Machines with AVX-512 gave different numbers.** Modal hands out machines
  with and without it. The PC's Windows numpy has no AVX-512 routines; Linux
  numpy uses them where present, and they round the last digit and break
  ties differently. The same-numbers check failed on exactly the AVX-512
  machines (2 of 5): near-zero chances (0.00002 vs 0) and the order of tied
  places in "highest this week". Fixed by
  `NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SPR"` (the per-feature
  names such as `AVX512F` are silently ignored by numpy 2.4) and
  `OPENBLAS_CORETYPE=Haswell`: then 8 of 8 machines, 3 of them AVX-512,
  matched the PC exactly.

**Rule results**
- Rule 1 (same numbers): **PASS** 2026-10-20 — 8 of 8 cloud machines, every
  old number identical to this PC's on the recorded day.
- Rule 2 (soil used): **PASS** 2026-10-20 — first real cloud run (04:32,
  Mumbai, 1st try): soil wetness used (ERA5-Land to 2026-10-06), 17 of 18 CWC
  gauges fresh as on the PC, `issued_at` written in India time.
- Rules 3–4: the side-by-side week starts with the first scheduled run,
  **08:30 on 2026-10-20**. Rule 4 also needs the app's feed change
  (`webapp/app.py`, `products/flood/feed.py`) pushed to `v2` — pushed 2026-10-20 (ae9fa12).

**Deployed 2026-10-20 ~04:40** (`modal deploy`): app `slopesense-daily` in
workspace pankajkarjay — `daily` (08:30 Asia/Kolkata), `latest` (the link),
`run_now`, `golden_check`. Everything else stays as it was: the PC's own
08:30 task still runs and still writes this PC's logs.

**Daily checking during the week** — `modal run scripts/cloud/modal_daily.py::pull`
(profile pankajkarjay) copies the cloud's logs to `logs/cloud_copy/`;
`status.json` there says whether today's run worked and on which try. The
pull fetches file by file and takes ~10 min (reports/ is 21 MB).

**Redeploying after a code or model change** — the cloud runs the copy
uploaded at the last deploy, not this PC's live files. After changing the
forecast code or retraining a model: `record` on the PC, `seed --what golden`,
`::golden --times 4`, then `modal deploy`. The `modal` command lives in
`D:\CODE\Python\Projects\YTAuto\venv\Scripts\modal.exe` for now (not in this
project's venv).

**Pass/fail rules — written before the first cloud run**

1. **Same numbers.** `check_live_unchanged.py check`, run in the cloud on the
   day this PC recorded (`record`, 2026-10-20), reports no changed and no
   removed field. Added fields are allowed. Fail → not deployed.
2. **Soil used.** The cloud run's issue says soil wetness was used
   (`soil_wetness.used` is true in the snapshot). Fail → key or host problem;
   fix before deploying.
3. **On time, every day.** For 7 consecutive days the cloud log has an issue
   for the day, made before 09:30 India time (`issued_at`). One miss or late
   issue restarts the count.
4. **The app follows without a push.** On a day of the 7, the hosted app
   shows that day's issue with no push to `v2` since the feed change.
5. Only after 1–4: the cloud log becomes the main one (this PC pulls a copy
   with `::pull`) and the PC's scheduled task is switched off.

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
