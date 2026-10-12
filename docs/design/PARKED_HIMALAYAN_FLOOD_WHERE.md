# ACTIVE PRIORITY — turning flood WHERE from a relative index into a real probability

**Status:** 🔴 **PRIORITIZED 2026-09-03 by explicit user decision — this is
now the single most important open task in the flood module.** No longer
parked. Read §0 first — it supersedes the old paused framing below, which
is kept only as background/history.

## §0. The priority plan, as decided 2026-09-03

**The goal restated in one line:** WHEN already gives a real calibrated
percentage. WHERE still only gives a checked ranking. Closing that gap —
so the system can finally state a real `P(flood, here, today)` instead of
a relative index — is the top priority.

**The plan, in order:**

1. **Pool every real event we can reach, for free**, from all three
   sources already found and verified — **DONE, 2026-09-04**:
   - Our own Sentinel-1 checks: Arunachal (74) + Himalaya proof (9).
   - The Google Earth Engine Global Flood Database pull: 155 real Himalaya
     events, 2000-2018 (see §5b).
   - The remaining 2019+ Sentinel-1-only candidates (GFD can't reach these
     — see §5b/§5d): **15 of 31 converted to real events** (48%, not the
     earlier "half-to-two-thirds" guess — see §5d for the honest correction).
   - **Actual combined total: 74 + 9 + 15 + 155 = 253 real Himalaya-wide
     events** (close to the ~270 estimate, slightly under because the
     no-coverage rate ran higher than planned).
2. **Convert every event to pixel-level training data**, not one row per
   event. Each event is a full raster — millions of real (terrain feature,
   flooded-or-not) pixel examples, not one data point. This is the same
   reframing that makes DL-scale training realistic at all off only ~270
   *events* — the real training set is closer to tens-to-hundreds of
   millions of *pixels*.
   - **Known, already-measured limit, not a guess**: pixels from the same
     event are correlated, not independent — going 34→74 events (both
     already millions of pixels each) did NOT fix the WHERE ranking's
     middle-class problem (see the earlier calibration section below).
     Pixel count buys real spatial-pattern learning; it does NOT buy more
     independent *event* diversity. Both still matter, separately.
   - **Mandatory evaluation discipline**: hold out whole EVENTS for
     testing, never a random pixel split — a random split leaks pixels
     from the same flood into both train and test and produces a fake,
     inflated score. Same rule already used everywhere else in this
     project (year-held-out CV for WHEN, region-held-out for the landslide
     Himalaya pooling).
3. **Train, then calibrate — two separate steps, not one.** A trained
   model's raw score is a ranking, not a percentage, until it goes through
   the same disciplined, held-out calibration step already built for WHEN
   (`calibrate_flood_when.py`'s isotonic + year-CV approach is the
   template). Training alone does not produce a real probability — this
   was a live point of confusion in chat 2026-09-03, resolved: rank first,
   calibrate second, same as WHEN.

**Decided: train FOUR independent players for WHERE, keep all four, don't
pick one in advance.** Directly follows the standing rule already recorded
in [[ensemble-strategy-decided]] ("keep pooled+local DL models side by
side") — the same principle already applied to WHEN (Variant A/B/C/D kept
separate, judged by measured held-out performance, not intuition).

| Player | Trained on | What it's best at |
|---|---|---|
| **Local-pixel DL** | Arunachal's own ~74-270-event pixels only | Most specific to Arunachal's actual terrain/rivers; still event-diversity-limited even with many pixels |
| **Himalaya-pooled DL** | Full Himalaya pixel pool, fine-tuned down to Arunachal | More diverse storm/terrain exposure; same "pool broad, then narrow" trick that already worked for WHEN's Variant B |
| **World-pooled DL** — added 2026-09-04 | Google's Global Flood Database, worldwide (913 events, not just the Himalaya-arc subset already pulled) → fine-tuned to Himalaya → fine-tuned again to Arunachal | Broadest possible exposure to general flood physics (low+flat+near-river floods everywhere); genuine risk it also picks up terrain patterns (deltas, coastal, desert) irrelevant to steep mountains — untested which way it nets out, that's exactly why it's kept separate and not assumed better or worse |
| **Tree-based (Random Forest/GBM) on the same pixels** — added 2026-09-04 | Same pooled+local pixel data, no architecture change needed | Needs far less data than DL to train reliably — same reason trees, not DL, were chosen for the landslide side ([[why-trees-not-deep-learning]]); a robust, harder-to-overfit member for a panel still this short on real events |

**Why four, not one:** none can be judged better in advance — that was
true for WHEN's variants too, and the untrained rule beat several of them.
Keep all four as separate panel members, let a real meta-learner (built
once they exist) decide the blend from measured held-out performance,
exactly the governance rule already in force everywhere else in this
project. Don't cherry-pick the better-looking one from small-sample
intuition — that mistake is explicitly what WHEN's Variant D avoided by
design. The World-pooled DL in particular is a real gamble, not an assumed
win — global terrain diversity might dilute the useful Himalaya-specific
signal instead of adding to it; only real held-out testing will say which.

**Full pipeline for every DL player, in order** (chat 2026-09-04): train
→ **meta-learner blends the players' rankings into one combined ranking**
→ **calibrate that blended ranking into a real percentage.** Same shape as
WHEN's Rule/A/B/C → Variant-D-blend → calibrator. Training alone never
produces a real probability; the meta-learner's job (weighing the players)
and calibration's job (turning the final blend into a real number) are
two separate, both-required steps, in that order.

**Why event-level (one row per whole event) was considered and rejected**
(chat 2026-09-04): it would throw away exactly what WHERE needs — a
single averaged row per event can say "this region flooded" but not
"this specific spot is the risky one." Pixel-level keeps that detail for
all three players above, including the tree-based one — it's not
event-level vs pixel-level, it's pixel-level for everything, DL and trees
alike.

**Fine-tuning data-size note** (chat 2026-09-04): ~270 pooled events is
too thin to train a DL model from scratch, but that was never the plan —
it's enough to *fine-tune* an already-pretrained model, which needs far
less data than training from zero. As more real Arunachal events get
confirmed over time, all three players get periodically re-fine-tuned/
retrained on a cadence — same standing rule as WHEN, not a one-time
ceiling.

---

## §0b. Definitive data state, cross-checked 2026-09-07 — read this for current numbers, not the narrative sections below

Every number below was re-derived directly from the saved report/interim
JSON files (not from memory or from earlier chat summaries) on 2026-09-07,
after two real accounting errors were caught and fixed (see "Corrections
found" at the end of this section). **This section is the canonical
current count — the §5-series sections tell the story of how each number
was reached, but if a narrative section and this section ever disagree,
this section is the one that was actually re-verified against source
files.**

### Arunachal Pradesh only

| # | Source | Candidates checked | Verified real | Status | Source file(s) |
|---|---|---:|---:|---|---|
| 1 | Our own Sentinel-1 (local download + full radar calibration), CWC/NWDP/Jang stations | 74 targeted | **74** (71 positive, 3 genuine dry zeros) | Precise, final | `flood_where_s1_statewide.json` (8) + `_statewide_expanded.json` (35) + `_s1_nwdp.json` (12) + `_s1_jang_multi_date.json` (12) + `_s1_loose_ends.json` (7) |
| 2 | Google Earth Engine GFD catalog, 2000-2018, Arunachal bbox | 94 | **70** | Precise, final — free/server-side MODIS | `flood_where_gee_gfd_arunachal.json` |
| 3 | Himalaya 9-town proof batch — the 1 Arunachal sanity check (Along/Aalo) | 1 | **1** | Precise, final — same local Sentinel-1 pipeline as #1 | `flood_where_himalaya_pool_test.json` |
| 4 | Himalaya-arc 2019+ batch (fetch_27) — events that land geographically inside the AP bbox | 6 of the batch's 29 | **6** | Precise, final — same local Sentinel-1 pipeline as #1 | `flood_where_himalaya_pool_full.json` (report_numbers 4772, 4822, 4919, 4920, 4963, 5091) |
| 5 | Groundsource pre-2019 → GFD check | 1,946 | **185** | Precise, final | `flood_where_groundsource_gfd_check.json` |
| 6 | Groundsource pre-2019 → gauge cross-check (of #5's leftovers) | 1,761 | **23** | Precise, final — real CWC gauge crossing | `flood_where_groundsource_gauge_crosscheck.json` |
| 7 | Groundsource pre-2019 (2014-18) → Sentinel-1-in-EE screen (of #5/#6's leftovers) | 1,056 | **603** | Provisional (Earth Engine fast path) | `flood_where_groundsource_pre2019_s1_ee_screen.json` |
| 8 | Groundsource 2019+ → Sentinel-1-in-EE screen | 3,530 | **2,227** | Provisional (Earth Engine fast path) | `flood_where_groundsource_s1_ee_screen.json` |
| 9 | Groundsource 2019+ → gauge cross-check (of #8's non-positives) | 1,303 | **49** (29 CWC + 20 NWDP) | Precise, final — real gauge crossing | `flood_where_groundsource_2019plus_gauge_crosscheck.json` |

**Totals:**
- Precise/final (#1+#2+#3+#4+#5+#6+#9): 74+70+1+6+185+23+49 = **408**
- Provisional, Earth-Engine fast path, not yet locally re-verified (#7+#8): 603+2,227 = **2,830**
- **AP grand total, verified: 408 + 2,830 = 3,238**
- Still unresolved (all inside the Groundsource pool, #5-9's denominator, see breakdown below): **2,389**
- AP grand total including unresolved: 3,238 + 2,389 = 5,627 (= 74+94+1+29 targeted/candidate items outside Groundsource, plus the 5,476-candidate Groundsource pool — see reconciliation below)

### Groundsource-AP-pool-only reconciliation (rows 5-9 above, denominator 5,476)

| | Pre-2019 (1,946) | 2019+ (3,530) |
|---|---:|---:|
| Confirmed via GFD | 185 | — |
| Confirmed via gauge | 23 | 49 |
| Confirmed via Sentinel-1-in-EE screen | 603 | 2,227 |
| **Verified subtotal** | **811** | **2,276** |
| Screened negative / no image, not near a gauge | 453 | 1,254 |
| Too old for any current method (pre-Oct-2014, no Sentinel-1 archive) | 682 | — |
| **Unresolved subtotal** | **1,135** | **1,254** |
| **Check: verified + unresolved = total** | 811+1,135=1,946 ✓ | 2,276+1,254=3,530 ✓ |

**Groundsource-AP total: 3,087 verified, 2,389 unresolved, 5,476 total** (all three numbers directly recomputed from the five source JSON files above, zero overlap found between any two confirmation stages — checked by set intersection, not assumed).

### Himalaya-region-wide total (AP + everywhere else), for cross-reference

The wider Himalaya-region running total (Bhutan/Nepal/Sikkim/Himachal/
Uttarakhand/J&K/Sub-Himalayan-WB **plus** AP) is **3,566** — this INCLUDES
the AP total above, not in addition to it:

| | Count |
|---|---:|
| AP-only verified (this section's total, above) | 3,238 |
| Non-AP verified (Himalaya proof batch minus Along: 8; arc-2019+ batch minus the 6 AP ones: 23; GFD catalog's non-AP portion: 155−70=85; CWC-gauge GFD cross-check, other states: 55; CWC-gauge Sentinel-1 batch, other states: 157) | 8+23+85+55+157 = **328** |
| **Himalaya-region-wide total** | 3,238 + 328 = **3,566** ✓ |

The "155" GFD figure was itself re-verified this session (a stale "not
yet done" note in §5b had raised doubt about it) — confirmed real via
`data/interim/flood_when/gfd_himalaya_arc_results.json`: 158 GFD events
intersect the wider Himalaya-arc bbox, 155 of those have a real detected
flood pixel (`flooded_px > 0`), and all 94/70 of the Arunachal-bbox
events are a clean subset of that 158/155 — no double-counting.

### Corrections found and fixed while cross-checking for this section (2026-09-07)

1. **Missed a whole bucket.** An earlier chat answer gave "1,936
   unresolved" for the two Sentinel-1-in-EE screen stages — it silently
   dropped the 453 pre-2019 (2014-18) candidates that fall inside
   Sentinel-1's window but screened negative and aren't near a gauge.
   Correct figure is **2,389** unresolved (1,135 + 1,254).
2. **7 real, already-confirmed Arunachal events were sitting uncounted
   in the "Himalaya-wide" bucket instead of the AP bucket** — 1 from the
   9-town proof batch (Along/Aalo) and 6 from the 29-event Himalaya-arc
   2019+ batch (report_numbers 4772, 4822, 4919, 4920, 4963, 5091 — all
   geographically inside the AP bbox, confirmed by lat/lon, `country:
   India`). These were real, satellite-confirmed events the whole time
   (two of them — 4919 and 4963 — are the same events already quoted in
   §5i's Earth-Engine-validation table), just never re-attributed to the
   AP-specific total until this cross-check. Fixed: AP total moves from
   3,231 to **3,238**.

## §0c. Options to resolve the 2,389 unresolved — brainstormed + web-checked 2026-09-07

Live web research done this session (not from memory) to find every real
avenue for the 1,135 pre-2019 + 1,254 2019+ unresolved candidates (§0b).
**Important caveat that rules out most "just buy a satellite" instincts**:
any *tasking*-based commercial service (ordering a new image) cannot
image a date that has already passed — it can only help *future*
events. For the existing 2,389-event backlog, only an *archive* (imagery
the provider already happened to collect over Arunachal on that date, or
an ongoing free/operational service that already covers those years)
can possibly help. Sources below are sorted by that distinction.

### FREE

| Source | What it is | Coverage | Real for our backlog? |
|---|---|---|---|
| **ESA ERS-1/2 + Envisat ASAR archive** | Pre-Sentinel-1 European SAR, same "new water vs baseline" method would apply | ERS-1 1991+, ERS-2 1995+, Envisat ASAR 2002-2012 | **Best lead for the 682 pre-Oct-2014 bucket** — free EO Sign-In registration, Level-1 data freely downloadable via ESA's (A)SAR Online Dissemination service ([earth.esa.int](https://earth.esa.int/eogateway/faq/how-do-i-access-the-ers-and-envisat-a-sar-data-services-)). Not yet tried — same calibration/threshold approach as our Sentinel-1 pipeline should transfer, coarser resolution (~30m WSM) but real SAR. |
| **ISRO RISAT-1 / EOS-04 (RISAT-1A) SAR, via Bhoonidhi** | India's own SAR satellites — RISAT-1 2012-2017, EOS-04 2022-present | Fills part of the 2014-2017 gap and the 2022+ residual | Free registration; data **coarser than 5m is explicitly "Open data for all users"** ([Bhoonidhi brochure](https://www.nrsc.gov.in/nrscnew/assets/pdf/brochures/Bhoonidhi_Brochure_2025.pdf)) — same flood-detection method as Sentinel-1 could run on this, and different orbit/revisit timing than Sentinel-1 means it could genuinely catch dates Sentinel-1 missed, not just duplicate it. |
| **NRSC/NDEM near-real-time + historical flood layers** | ISRO's own operational SAR-based flood mapping, explicitly produced for Arunachal Pradesh among 7 states | Current year + 2 years detailed, **10-year cumulative historical layer** | Confirmed real and AP-specific ([NDEM technical note](https://ndem.nrsc.gov.in/documents/downloads/nrt_technical_note.pdf)) — access mechanism (public web viewer vs. request) not yet confirmed, check `ndem.nrsc.gov.in` directly next. |
| **Landsat (5/7/8/9) via Earth Engine** | Free optical archive, already have Earth Engine access | 1999-present (L7), 1984+ (L5) | Reaches all the way to 2000; cloud-limited in monsoon Himalaya (known weakness) but zero new setup cost — worth a quick pass on the 682 pre-2014 bucket for the dry-season subset. |
| **JRC Global Surface Water (monthly)** | Free, already in Earth Engine, water-occurrence composites | 1984-present, monthly | Coarser time resolution (misses short flood pulses) but could catch longer-duration events among the unresolved. |
| **Copernicus EMS Rapid Mapping (EMSR activations)** | Free, real satellite-derived flood-extent vector maps, but only for officially activated major disasters | Per-activation | Searched — no confirmed Arunachal activation found yet (found Uttarakhand/Assam ones), worth checking the full activation list at [mapping.emergency.copernicus.eu/activations](https://mapping.emergency.copernicus.eu/activations/) against our specific unresolved dates directly. |
| **Retry Copernicus GFM via its actual public portal**, not just openEO/EODC | Same GFM product, different front door | 2015-present | New finding this session: `globalfloods.eu` redirects to `global-flood.emergency.copernicus.eu`, and GFM has WMS-T (map service) + an on-demand download portal (`gfm.portal.geoville.com`, didn't resolve from this machine — try again later or from a different network) — **this is a different backend than the EODC openEO connection that's currently down**, worth trying independently rather than only waiting on EODC. |
| **Crack NASA MCDWD properly** (already a known, paused blocker — §5i1) | Free, actively-maintained MODIS flood product | 2012-present | Unblocking this reaches most of the 2019+ residual at 250m resolution; needs the real API query format (tile-grid vs bbox), not yet solved. |
| **Reprocess our own already-fetched Sentinel-1-in-EE imagery with a smarter method** | No new data source at all — apply a pretrained flood-segmentation model (e.g. Sen1Floods11-style) instead of a flat -17dB threshold to the 1,707 in-window "screened negative" candidates | 2014-present | Free (compute only); a flat threshold is known to be crude — some "negatives" may be false negatives from an under-sensitive cutoff, not real absence of flooding. |
| **Widen the screen's date-pad/buffer** | Methodological tweak to fetch_32/33 | Same window | Free; could recover some of the 726+290=1,016 "no image found at all" candidates if the ±3-day pad was simply too narrow for that orbit's revisit gap. |

### ASK (free or low-cost, but needs an account/request/approval)

- **Bhoonidhi finer-than-5m RISAT products** — open for coarse res, priced for finer ("fair and transparent pricing to Non-Government Entities") — register and check exact terms.
- **Direct NDEM/NRSC request** for the raw historical flood GIS layers if the public portal turns out to be view-only — same precedent as the GSI report-archive ask already used for landslide data ([[gsi-report-archive-open]]).
- **NASA Earthdata account** (simple, free signup, separate from LAADS' own API) — the recommended next step to finally crack MCDWD (§5i1), still not done.
- **Arunachal SDMA / district disaster management situation reports** — same precedent as CWC/NWDP gauge requests; could independently corroborate specific dates even without pixel data, and might contain place names precise enough to fix a bad check-point coordinate.
- **Planet NICFI historical archive access** (2015-2024 monthly, 4.77m optical) — the NICFI program itself ended Jan 2025, but the already-collected historical archive may still be requestable for research use; not yet confirmed.

### PAID

- **ICEYE Flood Insights** — commercial SAR flood-monitoring service; has given free access to *some* declared disasters via Esri's Disaster Response Program, but that's for live emergency response, not backlog research — effectively paid for our use case, and only useful if their archive happens to cover the right historical date.
- **Maxar / Airbus tasked very-high-res optical** — commercial; their *Open Data* program (free) only covers officially activated major disasters, and tasking can't reach past dates at all — only their **existing archive** (if any) over Arunachal on the right date would help, which would need a paid archive search either way.
- **Capella Space / Umbra / Planet SkySat** — commercial SAR/optical constellations; same tasking-can't-time-travel caveat — only relevant via a paid archive search, not new tasking.
- **UP42 / Sentinel Hub commercial tiers** — mostly processing/quota convenience on data we already have free access to, not new historical coverage.

**Bottom line**: the two most promising *new* leads are the **ESA ERS/Envisat SAR archive** (directly answers the hardest 682 pre-2014 bucket, free, same method as our own pipeline) and **ISRO RISAT/Bhoonidhi + NDEM** (India-specific, free, could catch dates Sentinel-1's revisit schedule missed).

## §0d. The 2,389 unresolved are two different KINDS of gap — don't treat them as one problem

User's sharp catch, 2026-09-07: *"why only checking the 682 that was too old... what about the ones that screened negative because there's no satellite image for that timeframe?"* Correct — the 2,389 unresolved splits into two structurally different problems that need different fixes, not one:

| | Count | The actual problem | Right fix |
|---|---:|---|---|
| Genuinely pre-Sentinel-1 (before Oct 2014) | 682 | No SAR satellite of ours reaches that far back at all | A **different, older satellite archive** — ESA ERS/Envisat, ISRO RISAT-1 (§0c) |
| Inside Sentinel-1's era, but **no image found** in our own ±3-day search window | 987 (290 pre-2019 + 697 2019+) | Sentinel-1's real revisit cycle here is 6-12 days — our window may simply have been too narrow to catch the nearest real pass | **No new data source needed** — widen the date window and re-run the same free Earth Engine check (fetch_36, running now) |
| Inside Sentinel-1's era, image found, but **screened negative** (below the flat -17dB threshold) | 720 (163 pre-2019 + 557 2019+) | Real data was checked — either a genuinely dry check point, or a real flood a crude flat threshold missed | **Reprocess with a better method** (smarter threshold/segmentation), not a new satellite |

ESA/RISAT are the right tool ONLY for the first row (682) — using them on the other 1,707 would be reaching for a new satellite to solve a problem that isn't about satellite availability at all. Fixed the mistake by building
[fetch_36_groundsource_widewindow_recheck.py](../../scripts/fetch/fetch_36_groundsource_widewindow_recheck.py)
(same free Earth Engine method as fetch_32/33, `DATE_PAD_DAYS` raised 3→10, tagged `method: "earth_engine_native_widewindow"`) and running it on the 987 "no image" candidates — running now alongside the ESA precheck, results pending.

The 720 "screened negative" row is deliberately not touched yet — per the standing §5j reasoning (screening is cheap, but a crude flat threshold's false-negative rate is unmeasured, and re-processing 720 candidates with a better method is a real design task, not a quick script edit). Worth a real pass later, not blocking on it now.

**ESA ERS/Envisat precheck — DONE, 2026-09-07.** All 682 pre-Oct-2014
candidates checked via
[fetch_34_esa_asar_ers_precheck.py](../../scripts/fetch/fetch_34_esa_asar_ers_precheck.py)
against ESA's real public search backend (reverse-engineered from the
search page's own JS this session — no login needed to search, only to
later download; see the script for the exact `query.footprint.*` /
`query.beginAcquisition.*` field names, undocumented publicly).

- **153/682 fall inside either archive's real operating window**
  (Envisat ASA_WSM_1P: 2002-05 to 2012-04-08; ERS SAR_IMP_1P: 1991-07 to
  ~2011-07) — the other **529 fall in the 2012-2014 dead zone** (Envisat
  dead, Sentinel-1 not yet launched) where neither archive can ever help.
- **Of those 153, 41 have a real scene** (37 Envisat, 4 ERS — ERS's very
  low hit rate matches its known post-2001 tape-recorder/downlink
  limitations, it was mostly not actively imaging non-Europe ground
  stations by then) — a genuine **26.8% recovery rate** among the only
  candidates these archives could ever reach. All 41 are from 2007-2010.
- **These 41 are a real find, not yet verified** — this was only a
  precheck (confirms a scene exists, no download/flood computation yet).
  Downloading and processing them would need an ESA EO Sign-In account
  (free, email-verified — see §0c for the exact registration steps) and
  adapting the calibration pipeline to ASAR/ERS's different product
  format (not a drop-in reuse of the Sentinel-1 scripts).
- **The 529 dead-zone candidates are exactly where ISRO's RISAT-1
  (2012-2017) is the only remaining free lever** — still pending the
  user completing Bhoonidhi registration (§0c), and even then subject to
  the same real "was it actually tasked over this spot" tasking
  limitation that capped ESA's hit rate at 27%, not 100%.

**Wide-window recheck — DONE, 2026-09-08. Huge recovery.** All 987 of
[fetch_36](../../scripts/fetch/fetch_36_groundsource_widewindow_recheck.py)
(±3→±10 day window, same free Sentinel-1-in-EE method, no new data
source): **811/987 (82%) now screen positive** — the original ±3-day
window really was the problem for most of these, not a genuine absence
of data. Of the 811, the found scene sits a median of 7 days from the
reported flood date (min 4, max 10) — still a real, usable window, just
wider than the original. Remaining: 143 now have an image but still
screen negative, 33 still have no image at all even at ±10 days.
Tagged `method: "earth_engine_native_widewindow"`, same provisional
caveat as every other Earth-Engine-native number in this doc.

~~Updated AP running total: 3,238 + 811 = 4,049 verified, 2,389 − 811 =
1,578 unresolved.~~ **SUPERSEDED — see §0e, this number is unreliable.**

---

## §0e. Critical bug found 2026-09-08 — `.first()` is not deterministic, invalidates every EE-native screen number reported so far

User's own words, catching this: *"check those again my network got
disconnected. I am not sure if this step worked as intended."* Checked
properly instead of assuming the network was the issue — **it wasn't the
network. It's a real, previously-undetected bug in fetch_32, fetch_33,
and fetch_36 alike.**

**Root cause, confirmed directly**: every one of these scripts picks its
flood image and baseline image with `ee.Image(col.first())` on an
**unsorted** `ee.ImageCollection`. Earth Engine documents no stable
default order for `.first()` — when a candidate's date window contains
more than one matching Sentinel-1 image (common: a direct sample found
**47% of fetch_32/33's ±3-day-window candidates and 73% of fetch_36's
±10-day-window candidates have 2+ matching images**), repeated calls can
silently return a *different* image each time. Verified by literally
re-running the same candidates multiple times: the SAME uuid flipped
between `screen_positive: true` and `false`, with completely different
`pct_new_water_screen` values, zero code change — proof this was never
a stable measurement.

**This means every previously-reported Earth-Engine-native number this
session is unreliable, not just today's — 2,227 (fetch_32), 603
(fetch_33), and 811 (fetch_36) all inherit this bug.** The 720
"screened negative" bucket (§0d) is equally suspect. It also means the
gauge cross-check scripts, which took their "still unconfirmed" input
directly from these screens' `screen_positive` field, may have been run
against a slightly wrong candidate pool (their own 23/49 *confirmations*
are still valid — real gauge data, unaffected — but some candidates that
should have been offered to the gauge check may have been wrongly
excluded, having been mis-marked screen-positive by the bug).

**Fixed in all three scripts**: added `pick_image_near()` — instead of
`.first()`, explicitly fetch every matching image's id + timestamp,
and deterministically choose the one closest to a well-defined target
date (the candidate's reported date for the flood image; the baseline
window's midpoint for the baseline image), ties broken by `system:index`.
**Verified 100% reproducible** by re-running the previously-flaky
candidates 3x each post-fix — identical result every time.

**Old (unreliable) reports backed up, not deleted**:
`reports/_pre_determinism_fix_backup/` — kept for the record, not to be
cited as real numbers.

**All three re-runs DONE, 2026-09-08 — fully reconciled, real numbers.**

| | fetch_33 (pre-2019, 2014-18) | fetch_32 (2019+) | fetch_36 (wide-window) |
|---|---:|---:|---:|
| Total | 1,056 | 3,530 | 987 |
| Image found | 766 | 2,804 | 954 |
| Screen positive (fixed) | **616** (was 603) | **2,178** (was 2,227) | **752** (was 811) |

The direction wasn't consistent — fetch_33 went *up* 13, fetch_32 and
fetch_36 went *down* 49 and 59 — confirming this was genuine
non-determinism, not a one-directional bias.

**The 2019+ gauge cross-check was also re-run**, since its "unconfirmed"
input pool depends on fetch_32's screen output, which changed: **36
confirmed** (was 49, `reports/flood_where_groundsource_2019plus_gauge_crosscheck.json`).
The pre-2019 gauge check (23) did not need re-running — it's built from
GFD's output, never touched the buggy screen.

**Fully reconciled Groundsource totals** (every union checked against
the sum of its parts for overlap — all clean, zero double-counting):

| | Pre-2019 (1,946) | 2019+ (3,530) |
|---|---:|---:|
| GFD | 185 | — |
| Gauge | 23 | 36 |
| Screen (fetch_32/33) | 616 | 2,178 |
| Wide-window (fetch_36) | 215 | 537 |
| **Verified** | **1,039** | **2,751** |

**Groundsource: 3,790 verified / 1,686 unresolved (of 5,476).** Adding
the non-Groundsource AP-specific precise sources (74 own-Sentinel-1 + 70
GFD-catalog + 1 Along + 6 Himalaya-arc-batch-AP = 151, all unaffected by
this bug):

**Arunachal grand total, corrected: 3,941 verified, 1,686 unresolved.**
This is the number to cite going forward — 4,049 / 2,389 / 1,578 / 3,238
from earlier in this document are all superseded.

**Lesson for every future Earth-Engine-based script in this project**:
never call `.first()` (or rely on any unsorted collection's implicit
order) when more than one image can plausibly match a filter — always
sort explicitly or pick by an explicit criterion. This is the same
*category* of bug as the CDSE `search()` bug found 2026-09-05 (§5f) —
silently returning something plausible-looking instead of a real,
reproducible answer — just in a different subsystem.

## §0f. FUTURE SCOPE, PARKED 2026-09-08 — the remaining 1,686 unresolved AP candidates

**Status: deliberately deprioritized, not abandoned.** User's own words:
*"doc the remaining ones as future scope. Will come back to resolve
those which can be done if ever needed be."* Read this section first if
picking this specific thread back up — don't re-derive the plan below.

**Why parked, not pushed further right now**: the 3,882 AP candidates
already pixel-usable (§0e's table) already represent millions of real
training pixels — same "diminishing returns past a representative
sample" reasoning already established in §5j. The real bottleneck for
WHERE right now is turning those 3,882 into actual extracted pixel
masks (still not built — see §5n's Phase 1), not squeezing more events
out of the remaining 1,686. That extraction work should come before
resuming this thread.

**Exactly what's left, and the concrete next step for each piece**
(ranked by cost/yield, cheapest first — none of this has been started):

1. **Reprocess the "real image found, but scored below the flat -17dB
   threshold" subset — free, no new registration, no new download.**
   This is the single biggest remaining chunk. The scene is already
   identified for every one of these; the crude single-threshold
   comparison against one dry-season baseline image risks false
   negatives (a real flood just under the cutoff, or an unrepresentative
   baseline pass). Next step: recompute with either an adaptive/
   per-orbit-calibrated threshold, or a multi-baseline median instead of
   a single reference image.
2. **Download and verify the 41 already-identified ESA Envisat/ERS
   scenes (§0d) — free, bounded, fully scoped.** Needs the free ESA EO
   Sign-In account (no CAPTCHA, email-verified — registration steps in
   §0c) — then adapt the calibration pipeline to ASAR/ERS's older
   product format (not a drop-in reuse of the Sentinel-1 scripts).
3. **Complete the Bhoonidhi/RISAT-1/EOS-04 registration — needs the
   user, still pending from §0c.** The only free lever for the
   2012-2014 Envisat-to-Sentinel-1 dead zone, and for 2022+ alongside
   Sentinel-1. Registration is CAPTCHA-gated — cannot be automated;
   exact steps already given in §0c.
4. **Accept the small pre-2000s/pre-ERS remainder as permanently
   unresolved.** A handful of candidates predate every free SAR archive
   this project has found (ERS-1 starts 1991, but Arunachal tasking
   coverage that early is sparse-to-none per the direct check in §0d).
   Not worth continued effort baring a future paid archive search.

**Precise current breakdown of the 1,686** (from §0e, restated for a
future session's convenience):

| Bucket | Count | Blocker |
|---|---:|---|
| Pre-Oct-2014, no Sentinel-1 archive at all | 682 | 41 have a real ESA scene lead (item 2 above); the rest need RISAT (item 3) or are permanently out of reach (item 4) |
| Pre-2019 (2014-18), inside Sentinel-1's window | 225 | No image even at ±10 days, or below threshold (item 1) |
| 2019+, inside Sentinel-1's window | 779 | Same as above (item 1), and not near a gauge |

Nothing here is deleted or lost — every candidate stays in its dataset
file (`data/interim/flood_when/groundsource_aru_*`), every report JSON
stays on disk, and this section is the map back to exactly where each
piece stands.

## §0g. "Provisional" means two separate things — and the fix for each is different (2026-09-08)

User's question, worth pinning down precisely since it will come up
again: *"provisional compared to precision-grade — how do we upgrade
them, won't that take days?"* No — clarified and then actually started:

1. **We only had an aggregate number, not real pixel data.** The screen
   computed one summary percentage over a region (`reduceRegion`), not
   an actual flood/no-flood raster. This is the real gap for pixel
   training and has nothing to do with speed — fixed by asking Earth
   Engine for the actual small raster instead of the summary statistic
   (same free, no-download method, different output). **This is the
   fix now in progress — see below.**
2. **We haven't precisely confirmed Earth Engine's number matches our
   own local-pipeline convention** (the Jang-valley test, §0d: 10/12
   dates agreed within ~1pp, 2/12 off by ~6pp). This does NOT need all
   3,546 downloaded locally — a small representative sample (~30-50
   events) would be enough to measure the real gap and apply it as a
   correction/uncertainty band. **Not started — a Phase 2 task, correctly
   deferred, not urgent.**

**Fix for #1 — pixel-mask extraction, running now.**
[fetch_37_pixel_mask_extract.py](../../scripts/fetch/fetch_37_pixel_mask_extract.py):
for every one of the 3,546 screen-positive candidates (fetch_32 + 33 +
36 combined, confirmed disjoint by uuid), re-derives the exact same
flood/baseline image the screening step already picked (reusing the
now-fixed deterministic `pick_image_near`), then pulls a real
10km x 10km, 10m-resolution, 3-band (flood-day water / baseline water /
new-water) array via `ee.data.computePixels` — still free, still no raw
scene download, just asking for the raster instead of its average.

**Real technical limit hit and worked around**: `ee.data.computePixels`
caps a single request at 50MB — the original ~33km screening buffer at
10m/3-bands would be 66.5MB and fails outright; 10km/10m/3-bands (~3MB)
comfortably fits. `sampleRectangle` (the higher-level alternative) caps
at only 262,144 total pixels across all requested bands, even smaller —
ruled out for this box size.

**Real speed fix, not a guess**: first timing (0.5-4.5s/candidate in
isolated tests) jumped to ~27s/candidate in the real extraction function
— traced to an unnecessary `pt.transform('EPSG:3857',1).getInfo()`
network round-trip per candidate, done purely to convert a lat/lon to
Web Mercator meters, something with zero server-side dependency.
Replaced with a plain closed-form conversion computed locally —
confirmed by direct timing this dropped to **~4-8s/candidate**, putting
the full 3,546-candidate batch at roughly **6-7 hours, not days** — this
is the concrete number behind "don't need the slow pipeline, and this
part doesn't take days either."

Output: `data/interim/flood_where_pixels/<uuid>.npz` (compressed,
fw/bw/nw arrays + lat/lon/scale metadata) per event, progress tracked in
`reports/flood_where_pixel_mask_extract.json`. Running as of this note —
final count and a proper "how much is now truly pixel-trainable" report
to follow once it finishes.

---

> This is the flood-side twin of
> [PARKED_HIMALAYAN_POOLED_TRIGGER.md](PARKED_HIMALAYAN_POOLED_TRIGGER.md)
> (the landslide version of the same idea). Same shape: pool a wider region's
> real dated events, fine-tune on Arunachal's own real 74. Read that file for
> the general reasoning if this one is thin on it.

---

## 1. The idea in one line

WHERE's static risk map only has ~74 real satellite-checked Arunachal events
to be judged against — too few (§ see `FLOOD_WHEN_PILOT_PLAN.md`'s WHERE
sections). Instead of waiting for more Arunachal-only events, pool real
flood evidence from the wider Himalayan region (Bhutan, Nepal, Sikkim, wider
India/Pakistan/Bangladesh), train/fine-tune a WHERE player on that, same
"pool broad → shrink down to Arunachal" trick already used for WHEN's
Variant B.

## 2. What's been proven so far (done, don't redo)

1. **A real, free, dated Himalaya-wide flood-event source exists and was
   downloaded**: DFO's *Global Flood Records* (Zenodo
   `10.5281/zenodo.19288170`, CC0). Now saved locally at
   `data/raw/15_dfo_flood_records/Global_Flood_Records.gpkg` (and `.csv`) —
   **don't re-download**, just `geopandas.read_file(...)`.
   - 5,503 real dated global events, 1985-2023, each with a real footprint
     polygon.
   - **296 intersect the Himalayan arc** (72-97.5°E, 26-36°N).
   - **77 intersect Arunachal + immediate neighbors** (91-98°E, 26-30°N).
2. **Honest catch, checked not assumed**: every single Himalaya-arc record's
   `Source` is `News`/`FloodList` — zero satellite-traced. Polygons are
   often huge (some span 5-9° of lat/lon) — **not usable as direct
   pixel-level training labels**, same trap as
   [[bhuvan-flood-mask-is-unusable]]. Usable only as a real "when/roughly
   where" trigger to go check with our own Sentinel-1 pipeline — exactly
   how the 9-event proof batch below used it.
3. **9-event proof batch — 9/9 real positive signal.** Script:
   [fetch_26_himalaya_pool_test.py](../../scripts/fetch/fetch_26_himalaya_pool_test.py).
   Hand-picked 9 real, well-known river towns (3 Bhutan, 3 Nepal, 2 Sikkim,
   1 Arunachal sanity check) that a real DFO polygon actually contains, ran
   the same debugged calibration/warp Sentinel-1 pipeline used everywhere
   else in this project. Full table and result in
   `reports/flood_where_himalaya_pool_test.json` and
   `FLOOD_WHEN_PILOT_PLAN.md`'s "9-event Himalaya proof batch" section —
   **don't rerun, it's done and cached** (every downloaded scene is still on
   disk in `data/raw/11_satellite/`).
   - Range 0.02%-4.51% new water, all real, all positive.
   - Arunachal's own sanity check (Along, 1.00%) landed mid-distribution,
     not an outlier — the method transfers, not just works at home.

## 3. What this does NOT yet prove

9 real events is a real green light that the **pipeline** generalizes off
Arunachal. It is **not** enough to train anything — see the "will 9 be
enough" discussion in the chat/plan doc. Realistic estimate before running
it: after filtering out pre-2014 dates (before Sentinel-1 existed), dates
with no exact/near satellite match, and genuine no-coverage cases (2 of 37
in the last statewide expansion were exactly this), expect roughly
**half to two-thirds of whatever candidate count is attempted** to convert
into real usable satellite-checked events — not the raw 68 or 287.

## 4. The scope decision — SUPERSEDED 2026-09-03, resolved by §0/§5b

This table was the open question before the Earth Engine/GFD source was
found. It's resolved now, not by picking one row below, but by the
corrected math in §5b: GFD covers 155 of these events already (2000-2018,
mostly done), so the real remaining Sentinel-1-only task shrank from
"~287 more" to **~42 more (2019+ only)**. Kept for history, not as a live
choice:

| Option (superseded) | Total events | Remaining after the 9 | Extra download | Rough time |
|---|---:|---:|---:|---:|
| Arunachal + immediate neighbors only | 77 | 68 | ~90 GB | ~5-7 h |
| Whole Himalayan arc | 296 | 287 | ~370 GB | ~20-24+ h |

## 5. How to actually run it, once scoped

Unlike the hand-picked 9 towns, hundreds of events can't be hand-curated
one by one. The practical, honest method to extend this beyond the 9:

1. Load `data/raw/15_dfo_flood_records/Global_Flood_Records.gpkg`.
2. Filter to the chosen bbox (§4) **and `BeginDate >= 2015-01-01`**
   (Sentinel-1's operational start — anything older is automatically
   infeasible, filter it out before spending any download budget on it).
3. For each remaining polygon, use its own centroid (or
   `geometry.representative_point()`, which is guaranteed inside the
   polygon unlike a plain centroid) as the check point — **not** a
   hand-picked town, there are too many to research individually at this
   scale. Flag this plainly when reporting results: some fraction of
   checks will land on a genuinely dry/unaffected point inside a crude
   news-polygon and correctly score ~0%, and that is an expected
   consequence of the method, not a pipeline bug — don't let a bunch of
   real zeros look like a regression the way earlier honest zeros
   (Kanubari, Yinkiang's first try) were carefully distinguished from bugs.
4. Reuse `fetch_25_sentinel1_statewide_expand.py`'s `find_scene_for_date`
   and `ensure_baseline` (generic, already lat/lon-parameterized) —
   **remember the per-download token refresh fix** (both `fetch_25` and
   `fetch_26` needed it added separately; a new script would need it from
   the start, not bolted on after 401s appear).
5. Run as a background job, incrementally-written report (same pattern as
   `fetch_25`/`fetch_26`), so a multi-hour run surviving a session boundary
   loses nothing.
6. Once done: this becomes the real training set for a Himalaya-pooled
   WHERE player (Team WHERE's 2nd panel member), to be fine-tuned on
   Arunachal's own 74 events per [[ensemble-strategy-decided]]'s standing
   rule — kept in the panel even if it underperforms alone, judged by
   whether it helps the *ensemble*, not solo accuracy.

## 5b. New, real, higher-value source found — Google Earth Engine's Global Flood Database

Checked 2026-09-03, at the user's request, using their own Google account
(`sonit7dev@gmail.com`, Earth Engine project `earthengine-507510` — a real,
working, authenticated connection, now set up on this machine; see §5c for
how to reconnect a future session without repeating the OAuth dance).

`GLOBAL_FLOOD_DB/MODIS_EVENTS/V1` — 913 real events worldwide, 2000-2018,
each with **actual MODIS-observed flood-water pixels** (not a news-guessed
shape like raw DFO). Checked directly, not assumed:

- **94 of 913 events intersect the Arunachal bbox.**
- **70 of those 94 have a real observed flooded pixel inside the bbox**
  (some of the 94 only grazed a huge multi-country footprint's edge —
  checked properly, not just counted as a bbox hit).
- **43 of those 70 line up with a date we already independently confirmed
  via real CWC/NWDP river-gauge crossings** — an honest cross-check between
  two completely unrelated real data sources (government gauges vs.
  NASA/Yale satellite mapping), both agreeing. This is real triangulation,
  not a coincidence at that hit rate.
- Critically, **this reaches back to 2000** — 14+ years before Sentinel-1
  existed at all, a period this project currently has zero WHERE evidence
  for by any other means.

**Honest trade-offs, not a free upgrade over the Sentinel-1 work:**
- 250m resolution (MODIS) vs. our own ~10m (Sentinel-1) — coarse, village/
  road-level detail is not resolvable from this source.
- Stops at 2018 — nothing recent, so it complements the Sentinel-1 pipeline
  (which covers 2015-now) rather than replacing it.
- Still ultimately anchored to DFO's own news-triggered event windows for
  *when/roughly-where* to look (same `dfo_id` linkage) — the improvement
  over raw DFO is that the *extent itself* is real satellite pixels, not a
  news-report shape.

**Practically much faster than the Sentinel-1 route**: all 94 events were
queried server-side via Earth Engine in about two minutes total, with zero
scene downloads — versus ~5-8 minutes of actual bandwidth per event for
the Sentinel-1 pipeline. This is a genuinely strong candidate to check
first, or in parallel, before committing to the full 68-287 Sentinel-1
Himalaya rollout in §4.

Full data: `reports/flood_where_gee_gfd_arunachal.json`. Raw pulled
metadata: `data/interim/flood_when/gfd_meta.json`,
`data/interim/flood_when/gfd_arunachal_results.json`.

**Not yet done:** the same check for the wider Himalaya arc bbox (158 of
913 events intersect it, per the same query — not yet broken down by
real-pixel-or-not the way the Arunachal set was). Also not yet done:
actually pulling the per-event flood-extent rasters themselves (this pass
only counted pixels to check real coverage existed — the rasters
themselves, at `ee.Image(...).select('flooded')`, are what would actually
become training data).

## 5c. How to reconnect Earth Engine in a future session

1. `pip install earthengine-api` (already done in this project's venv).
2. The account is already authenticated on this machine — check first with
   `python -c "import ee; ee.Initialize(project='earthengine-507510'); print(ee.Number(1).getInfo())"`.
   If that works, nothing else is needed.
3. If the token has expired/been revoked, redo `ee.Authenticate()` —
   **`auth_mode='localhost'` worked cleanly** (opens a URL, user signs in
   in their own browser on this same machine, completes automatically —
   no manual code copy-paste needed, unlike `auth_mode='notebook'`, which
   hit a real snag: the printed code cannot be redeemed from a second
   process, since the PKCE verifier is per-process. Use `localhost` mode
   first, not `notebook`.
4. Project ID is `earthengine-507510` (the user's own, free "Unpaid usage"
   tier) — always pass it explicitly to `ee.Initialize()`, don't rely on
   project auto-detection (it resolved to an unrelated stale project ID on
   this machine and failed).

## 5d. Full Sentinel-1 rollout for 2019+ Himalaya-arc events — DONE, 2026-09-04

Script: [fetch_27_himalaya_pool_full.py](../../scripts/fetch/fetch_27_himalaya_pool_full.py).
Ran the 31 real DFO Himalaya-arc events from 2019 onward (the years GFD's
MODIS archive can't reach — see §5b) through the same debugged Sentinel-1
calibration/warp pipeline, using each event's own `representative_point()`
as the check point (not hand-picked towns — there were too many to
individually research at this scale).

**Result: 15/31 real, satellite-confirmed flood events. 16/31 confirmed
no Sentinel-1 pass exists at all in that event's reported window** (a real,
expected outcome of checking hundreds of arbitrary news-report windows
against actual satellite revisit gaps — not a pipeline bug). All 15 real
hits show genuine positive new-water signal, range **0.19%–15.86%**, median
4.89%, mean 4.43%.

**Honest correction to the earlier estimate**: §3 guessed "half-to-two-
thirds convert." Actual conversion rate was **15/31 = 48%** — lower than
guessed, because the no-coverage rate (52%) ran higher than expected. Worth
remembering for any future batch of this kind: don't assume two-thirds,
closer to half is the realistic planning number.

**Also worth noting for future runs**: the download side hit an unusually
high rate of transient network failures this run (repeated
`ConnectionError`/`ChunkedEncodingError` from `download.dataspace.copernicus.eu`)
— cleared on retry every time, no code issue, but took 3 resume passes
to fully clear. `fetch_27` distinguishes real "no coverage" (permanent,
skip) from a transient download failure (stays in the retry queue) —
worth porting that same distinction back into any earlier script that
doesn't have it, if reused again.

Full results: `reports/flood_where_himalaya_pool_full.json`.

## 5e. Fourth real source found — other Indian Himalayan states' own CWC gauges, 2026-09-04

User's question ("what about Himachal/Uttarakhand and other Indian
Himalayan states?") uncovered a real, previously-unused source: **CWC FFS
is a national system, not Arunachal-only** — we had only ever queried it
for Arunachal. Checked directly against the live API:

- **44 stations with a published real flood-danger threshold** across
  Himachal Pradesh (1), Uttarakhand (30), Jammu & Kashmir (3), and
  Sub-Himalayan West Bengal (10).
- Pulled each station's **full real water-level history** and counted
  real threshold-crossing events (grouped into distinct episodes, not raw
  days) from 2000 onward: **511 candidate flood events** — 338 in
  2000-2018 (checkable via Google's satellite data), 173 in 2019+
  (needs Sentinel-1, not yet run).

**Cross-checked the 338 candidates against Google's Global Flood
Database — no downloads, all server-side, ~2 minutes for the whole
batch.** Script: [fetch_28_gfd_gauge_crosscheck.py](../../scripts/fetch/fetch_28_gfd_gauge_crosscheck.py).

**Important bug caught and fixed before trusting the result**: the first
pass used `.filterDate()` naively, which only checks an image's own
`system:time_start` against the search window — not whether the window
*overlaps* the image's full `[time_start, time_end]` span. Since GFD
events can run weeks-to-months long, this silently missed almost every
real match (68/338 "found" instead of the real 172/338). Caught via a
known-flooded-pixel sanity check that came back with zero matches when it
should not have — fixed by filtering on real interval overlap
(`system:time_start <= window_end AND system:time_end >= window_start`)
instead.

**Second issue caught**: checking only the gauge's exact point (a single
~250m MODIS pixel) undercounted badly — a river gauge sits right in the
channel, which GFD correctly classifies as *permanent* water, not *new*
flood, so the single point rarely shows a real "new flood" signal even
during a genuine flood. Fixed by checking a 2km buffer around the gauge
(same reasoning as the Sentinel-1 windowed checks elsewhere in this
project) and reporting % of new-flood pixels in that area, not a single
point's yes/no.

**Final, corrected result: 55/338 real, independently satellite-confirmed
flood events** — a real CWC gauge crossing AND real NASA/Yale satellite
imagery agreeing, completely free, no download. Range 0.01%-44.23% new
water in the check area, median 5.4%. Concentrated in North Bengal
stations (38/55 from 3 Sub-Himalayan WB stations — plausible, a genuinely
flood-prone monsoon region).

**Updated real pooled total: 253 + 55 = 308 real Himalaya-wide events.**

**Not yet done at the time §5e was written**: the 173 candidates from
2019+ — see §5f, now in progress.

## 5f. Real bug found and fixed mid-run, 2026-09-05 — read this before trusting any "no coverage" count

Running the 2019+ batch (`fetch_29_cwc_gauge_himalaya_states.py`) hit a
real network outage partway through. **User asked the exact right
question — "can the disconnect be why some show no coverage, or were
they actually checked properly?"** Checked the code, not just assumed:
**yes, it was a real bug.**

`fetch_14_sentinel.py`'s `search()` collapsed two different outcomes into
the same empty list: (1) a request that failed all its retries (network
down) and (2) a request that succeeded and genuinely found zero results.
Both looked identical to the caller, so a mid-run network outage got
silently recorded as **confirmed permanent "no Sentinel-1 coverage"**
instead of a retryable failure — a real correctness bug, not just noise.

**Caught with direct proof, not just suspicion**: station `023-LBDJPG`
showed 20 straight "no-coverage" results, then the very next candidate
for that *same station* found a real scene immediately. A genuinely
uncovered location can't do that — this proved the streak was the outage,
not real.

**Fixed**: `search()` now raises when a request fails after all retries
instead of returning an empty list — a caller can no longer mistake
"couldn't check" for "checked, found nothing." All 35 no-coverage entries
recorded before the fix were cleared and re-run clean under the fixed
code (see `reports/flood_where_cwc_gauge_himalaya_states.json`). The 40
real confirmed events from the same run were **not** affected or
re-checked — those required an actual successful download, so they were
never at risk from this bug.

**Lesson for any future batch script in this project**: a "no coverage /
no data found" result must always come from a *provably successful*
empty search, never from a search that simply failed. `fetch_25` never
made a firm "confirmed no coverage" claim in the first place (it silently
left unfinished candidates for a rerun), so nothing to correct there.

**`fetch_27` WAS affected, and its previously-reported "final" numbers
were wrong — corrected here, 2026-09-05.** Re-checked (search only, no
downloads) all 16 of its old "no-coverage" entries under the same
now-fixed code: **14 of 16 immediately found a real scene** — only 2
(`#5269`, `#5449`) are genuinely uncovered. Ran all 14 for real (full
download + check): **10 converted to real events on the first pass, the
remaining 4 hit a separate, already-known geometry edge case (same as
`#5083` earlier — the matched scene's footprint doesn't quite cover the
point; resolved by retrying with a fresh baseline scene) and all 4
cleared on retry.**

**Corrected final total for §5d's batch: 29/31 real events (was wrongly
reported as 15/31), only 2/31 genuinely uncovered.** Range 0.0%-15.86%
new water, median 2.27%, mean 3.24%, 27/29 positive signal (2 genuine
zeros are expected — a real check point landing on a dry spot, not a
bug). **This changes the running combined total — see §5g.**

## 5g. Corrected combined running total, 2026-09-05

| Source | Count | Note |
|---|---:|---|
| Sentinel-1, Arunachal | 74 | unaffected by the bug |
| Himalaya proof batch | 9 | unaffected (hand-verified dates, no no-coverage claims) |
| Himalaya-arc 2019+ batch (§5d, corrected §5f) | **29** | was wrongly 15 before the bug fix |
| Google satellite data (2000-2018) | 155 | pure Earth Engine, never used the buggy code — unaffected |
| CWC-gauge cross-check via Google (§5e) | 55 | pure Earth Engine — unaffected |
| **Running total (before the CWC-gauge Sentinel-1 batch finishes)** | **322** | was wrongly 308 |

**CWC-gauge Sentinel-1 batch — DONE, 2026-09-06.** 174 candidates
(other Indian Himalayan states, 2019+, §5e/fetch_29), run under the
fixed code. **Result: 157/174 real events, 15/174 confirmed no
Sentinel-1 coverage, 2/174 unresolved** — blocked by a Copernicus
account-level 403 on the *login* endpoint itself (not a download
timeout), almost certainly a temporary rate-limit/lockout from the
sheer volume of token refreshes this one account made over many hours
today. Not retried further this session to avoid extending any lockout —
retry those 2 in a later session once enough time has passed. Range
0.01%-20.53% new water, median 3.26%, mean 4.25%, **157/157 positive
signal** — every single gauge-triggered candidate that had a real
satellite pass showed real flooding, reinforcing how strong a trigger a
measured gauge crossing is compared to a news report.

**Lesson for future large batches**: CDSE's login endpoint itself can
apparently rate-limit/lock out an account under heavy sustained use
(hundreds of token refreshes across many hours), separately from the
already-known per-request 401 (token just expired) and per-download
network flakiness. If a batch starts failing with `403 Forbidden` at
`identity.dataspace.copernicus.eu`'s token URL specifically (not the
OData/download URLs), that's this — back off and retry later, don't
hammer it.

**Final combined total after this batch: 322 + 157 = 479 real Himalaya-
wide pooled events.** This completes step 1 of the §0 priority plan
(pool every real event we can reach, for free) for every source found so
far except the still-not-yet-run Groundsource lead (§5h/§5i).

## 5l. Groundsource verification — running, 2026-09-06

Built two scripts per the §5i plan, both scoped to Arunachal first (same
staged approach as everything else). Candidates: 6,533 raw Groundsource
Arunachal rows → **5,476 after deduping** (date, area) near-duplicates
→ split **1,946 pre-2019** (GFD-checkable) / **3,530 2019+** (screen-only).

**[fetch_31_groundsource_gfd_check.py](../../scripts/fetch/fetch_31_groundsource_gfd_check.py)
— DONE.** Same proven method as fetch_28 (real interval-overlap date
filter, 2km buffer, no downloads). **Result: 185/1,946 real,
independently-confirmed events** (1,038/1,946 had a GFD image nearby at
all; of those, 185 showed a real new-flood pixel, not just a permanent-
water or dry hit). These 185 are final, real, usable events — same
standing as every other source in this project, no further download
step needed since GFD's own real satellite pixels are the ground truth
here.

**[fetch_32_groundsource_s1_ee_screen.py](../../scripts/fetch/fetch_32_groundsource_s1_ee_screen.py)
— running, not final yet.** Screens 2019+ candidates via Sentinel-1
imagery inside Earth Engine (no downloads) to flag which are worth a
real local download — **this produces a "worth downloading" flag, not a
counted event** (see §5i's precision caveat: this method's own percentage
doesn't match our calibrated pipeline closely enough to use directly).
Once finished, the plan is: download+run our own precise pipeline
(fetch_27/29-style) only on whichever candidates screened positive.

**Running total so far: 479 + 185 = 664 real pooled events**, with more
still to come once the 2019+ screen finishes and its positives get
properly downloaded and checked.

## 5m. Gauge cross-check recovers more real events from the satellite-unconfirmed pile

User's question: *"can we not confirm the same with gauge data since we
have them? out of the ones we don't have satellite data for, can we use
gauge or other something to make sure it did happen?"* — yes, and it's
free (no new API calls, we already have this gauge data downloaded).

Of the pre-2019 GFD check's **1,761 satellite-unconfirmed candidates**
(908 no image at all + 853 image-but-no-detected-water — see §5l for
why these are "unconfirmed," not "disproven"): **228 sit within 20km of
one of our 18 real CWC gauge stations.** Checked each against that
station's real water-level history (published danger level, or a 95th-
percentile proxy for the 5 stations without one) in a ±3 day window
around the reported date. **Result: 23 more real events confirmed** —
a genuine gauge crossing its flood level right around the report date,
peak levels all plausible (just above the threshold, not spurious
spikes).

**Running total: 664 + 23 = 687 real pooled events.**

**Now a proper, reusable script**: [gauge_crosscheck_groundsource.py](../../scripts/model/gauge_crosscheck_groundsource.py)
— user's instruction was "use any and all gauge data we have" — extended
to include NWDP's 14 small-stream stations too (18 CWC + 14 NWDP = 32
raw, 30 after excluding 2 NWDP stations with clearly wrong coordinates,
see below), then re-ran and **reproduced the same 23** — NWDP added
zero *for this specific pre-2019 batch*, for a real, checked reason:
almost every NWDP station's record only starts 2023-2025, too recent to
help confirm anything from 2000-2018. NWDP should matter once this same
script runs against the 2019+ batch instead, where its dates actually
fall inside NWDP's real coverage window.

**Real data-quality catch while building the combined registry**: two
NWDP station labels ("Changlang", "Ziro") carry coordinates that land
nowhere near Arunachal at all (Jammu & Kashmir and Uttarakhand
respectively) — almost certainly mislabeled in the source data.
Excluded rather than trusted; the correctly-named "Changlang_1" (real
Arunachal coordinates) was kept.

**Done, 2026-09-07 — 2019+ batch fully screened and gauge-cross-checked.**

Sentinel-1-in-EE screen ([fetch_32](../../scripts/fetch/fetch_32_groundsource_s1_ee_screen.py))
finished all 3,530 candidates: **2,804 had a Sentinel-1 image nearby at
all, 2,227 screened positive** (worth a real local download for the
precise number — not yet counted as events, per §5i's precision caveat).
Along the way, hit and fixed a real stall: the batch silently froze mid-
run for several minutes on one candidate — checked, Earth Engine itself
was healthy, so this was a genuine single-item hang, not a network
issue. Fixed with a hard 60-second per-candidate timeout (a thread pool
with `.result(timeout=60)`) — a stuck candidate now gets skipped and
retried on the next run instead of freezing the whole batch forever;
this caught exactly 3 more stalls before the batch finished clean.

Ran `gauge_crosscheck_groundsource.py` against the 1,303 screen-non-
positive candidates: **223 within 20km of a real gauge, 49 confirmed
real** — **29 via CWC, 20 via NWDP**. This is exactly where NWDP's real
coverage window (mostly 2023-2025) was expected to help, unlike the
pre-2019 batch where it added nothing — confirmed.

**Running total: 687 + 49 = 736 real, counted pooled events.**
Separately, **2,227 more candidates are now queued** for an actual local
Sentinel-1 download (fetch_27/29-style) to become precisely-counted
events — those are not yet in the 736, since the screen's own percentage
isn't precise enough to count directly (see §5i).

## 5n. The 2,227-download bottleneck is real — decided: Earth Engine now, local re-verification later (2026-09-07)

**The blocker, stated plainly**: at today's real observed download speed
(~1.2-1.7 MB/s, a scene 1.2-2.3 GB, 30+ minutes per event once queueing/
retries are counted — see §5j), running our own precise local pipeline on
all 2,227 screen-positive candidates would take **over 1,000 hours** and
a large amount of local storage. Not feasible on this machine today.

**Tested whether Earth Engine's own numbers can be trusted directly
instead of the local pipeline**, more rigorously than §5i's first 4-event
check: built
[sentinel1_ee_validate_jang.py](../../scripts/model/sentinel1_ee_validate_jang.py),
which re-runs the exact same 12 Jang-valley dates we already have
precise local numbers for (`reports/flood_where_s1_jang_multi_date.json`)
— same acquisitions, same per-orbit baseline scenes (matched by date, not
a generic search), same -17dB threshold, same 0.15° buffer — but computed
entirely inside Earth Engine (`COPERNICUS/S1_GRD`, `reduceRegion`, zero
download). Result in `reports/flood_where_s1_ee_vs_local_jang.json`:

| Date | EE new-water % | Local new-water % | Diff |
|---|---:|---:|---:|
| 2019-07-09 | 1.21 | 1.29 | -0.08 |
| 2019-07-14 | 1.66 | **8.10** | **-6.44** |
| 2019-08-02 | 1.43 | 1.42 | +0.01 |
| 2020-05-21 | 3.40 | 4.03 | -0.63 |
| 2020-05-23 | 3.59 | 4.11 | -0.52 |
| 2020-06-21 | 1.47 | 0.79 | +0.68 |
| 2020-06-26 | 1.58 | 2.03 | -0.45 |
| 2020-07-21 | 1.85 | 2.64 | -0.79 |
| 2020-07-22 | 1.85 | 2.64 | -0.79 |
| 2021-08-27 | 1.22 | 0.61 | +0.61 |
| 2023-08-24 | 1.90 | 2.04 | -0.14 |
| 2025-08-31 | 2.79 | **8.77** | **-5.98** |

10/12 dates agree within ~1 percentage point (mean abs diff 1.43pp,
median 0.63pp). 2/12 — both the largest local floods — are off by ~6pp.

**Root-caused, not left as a mystery**: confirmed both sides use the
identical underlying acquisitions (same scene timestamps/orbits, checked
directly by printing Earth Engine's own `system:index` against the local
pipeline's scene filenames — not an image-selection bug). Even the
*static baseline-day* water % (no flooding involved at all) disagrees
substantially between the two per orbit (e.g. orbit 150: local 4.7%
vs EE 8.4%; orbit 41: local 19.3% vs EE 14.0%; orbit 77: local 22.0% vs
EE 15.2%) — this is a genuine geometric processing difference, not a
threshold-edge artifact specific to big floods. Most likely cause: Earth
Engine's `COPERNICUS/S1_GRD` applies real DEM-based terrain correction
(orthorectification against SRTM), while our local pipeline
(`sentinel1_flood_evidence.py`) deliberately skips full terrain
correction and only does a GCP-based ellipsoid warp, by its own code
comments, to keep local processing fast. In Arunachal's steep terrain
this can shift how much of a valley/floodplain lands inside a fixed
lat/lon buffer — **this does not mean Earth Engine is less accurate; if
anything a real elevation model should be more correct here than the
local shortcut, not less.** Either way, the two are not numerically
interchangeable one-for-one.

**Decision (user, 2026-09-07)**: current hardware/bandwidth is a
temporary constraint, not a permanent one — a system upgrade is planned.
So: use Earth Engine as the fast, no-download method **now**, to unblock
the 2,227+ backlog, but do **not** treat it as the final, permanent
source of truth. Explicit two-phase plan, so it isn't lost:

- **Phase 1 (now)** — extend the existing screen
  ([fetch_32](../../scripts/fetch/fetch_32_groundsource_s1_ee_screen.py))
  from an aggregate percentage into an actual **per-pixel flood-mask
  pull** (small clipped raster/array per event, via Earth Engine's
  `computePixels`/`getDownloadURL` on a small buffered region — seconds
  and a few MB per event, not 30 minutes and 1-2 GB), and run it across
  all 2,227 screen-positive post-2019 candidates. Since Sentinel-1 in
  Earth Engine goes back to **October 2014**, not just 2019, the same
  fast method can also reach the pre-2019 candidates dated 2014-2018
  that neither GFD nor the gauge cross-check could confirm (§5l/§5m) —
  worth doing in the same pass. Every output row from this phase must be
  tagged `method: "earth_engine_native"` so it is never silently mixed
  with locally-calibrated numbers as if equally precise.
- **Phase 2 (later, once compute/storage/bandwidth is upgraded)** —
  re-run the full local download + calibration pipeline
  (`fetch_14_sentinel.py` + `sentinel1_flood_evidence.py`-style
  processing) on some or all of the same events. With many more paired
  measurements than today's 12 Jang dates, the EE-vs-local gap becomes
  something we can actually characterize (not just "roughly agrees"),
  and either correct the Phase-1 labels retroactively or feed the
  measured offset into the calibrator as an explicit uncertainty term.

**Not yet built**: the actual per-pixel extraction script for Phase 1
(today's work only built and ran the validation test above, which
reused the aggregate-`reduceRegion` approach already proven in
fetch_32 — real per-pixel arrays/rasters still need to be pulled, not
just the mean-over-region statistic).

**Phase 1 event-count update, same day — the pre-2019 gap also closes
partway.** Sentinel-1 in Earth Engine reaches back to **Oct 2014**, not
just 2019+, so the same free screen was pointed at the pre-2019
candidates GFD/gauges couldn't confirm. Of the 1,738 pre-2019 candidates
still unconfirmed after §5l/§5m: **1,056 fall inside Sentinel-1's window
(2014-2018) and 682 genuinely predate it** (no further free option for
those — GFD + gauge were already the best available). Ran
[fetch_33_groundsource_pre2019_s1_ee_screen.py](../../scripts/fetch/fetch_33_groundsource_pre2019_s1_ee_screen.py)
on the 1,056: **766/1,056 had a Sentinel-1 image nearby at all, 603/1,056
screened positive.**

**Provisional combined total, now counting both Earth-Engine-native
batches** (method tagged `earth_engine_native`, per the decision above —
fast path now, local re-verification later, not yet equivalent to the
precision-grade locally-calibrated numbers):

| Source | Count | Method |
|---|---:|---|
| Running total through §5m | 736 | mixed (Sentinel-1 local, GFD, gauge) |
| Groundsource 2019+ screen positives (fetch_32) | 2,227 | earth_engine_native |
| Groundsource pre-2019 (2014-18) screen positives (fetch_33) | 603 | earth_engine_native |
| **New provisional running total** | **3,566** | |

**Still genuinely unreachable for free**: 682 pre-2014 candidates (no
Sentinel-1 archive that far back, GFD/gauge already tried and exhausted)
— these stay trigger-only unless GFM or MCDWD come back online (§5i0/§5i1).

## 5h. Huge new candidate source found — Google's "Groundsource" dataset, 2026-09-05

User asked whether Google Flood Hub has anything usable — checked
properly rather than assumed. **Flood Hub's actual forecasts and its GRRR
reanalysis are both Google's own trained model output — correctly ruled
out, per the standing "build our own, don't just wrap their model" rule
([[flood-build-own-not-feed]]), and non-commercially licensed anyway.**
Two other things Google publishes on the same site turned out to be real,
raw, license-compatible data:

- **Caravan** (real gauge data) — checked, does **not** cover
  Nepal/Bhutan/Pakistan/the Himalaya at all (North America, South
  America, Australia, Europe only). Ruled out.
- **Groundsource** (`zenodo.org/records/18647054`, CC-BY-4.0, free,
  ~667MB Parquet, downloaded to
  `data/raw/16_groundsource/groundsource_2026.parquet`) — Google used
  Gemini to extract **2.6 million dated, localized flood events from news
  articles worldwide, 2000 to Feb 2026**, each with a real polygon
  footprint (`area_km2` + WKB geometry) — same *role* as DFO (a
  news-derived trigger, not itself satellite proof) but far bigger and
  more localized:
  - **155,279 events intersect the whole Himalaya arc bbox** (vs DFO's 296).
  - **6,533 events intersect the Arunachal area specifically** (vs DFO's 77).
  - Polygons are real localized areas (tens to low-thousands of km²), not
    DFO's country-spanning blobs — likely fewer "landed on a dry spot"
    misses than DFO gave us.
  - Reaches to present day — no 2018/2023 cutoff like GFD/DFO.

**Not yet done — this is a lead, not a counted event yet**: these are
still news-derived, need the same disciplined satellite/gauge
verification pipeline (Sentinel-1 or Google's GFD) before any of them
count as real, same distinction already enforced for every other source
in this project. Next step if pursued: filter to Sentinel-1-feasible
dates (2015+) and Arunachal/Himalaya scope, dedupe recurring same-spot
events, then run through the same `fetch_27`-style verification —
expect a real conversion rate well under 100%, same as every batch so far.

**Precise breakdown of the 6,533 Arunachal-area Groundsource candidates**
(checked directly against `data/raw/16_groundsource/groundsource_2026.parquet`,
2026-09-05):
- **814** dated 2000–2014 — checkable via Google's GFD only.
- **1,417** dated 2015–2018 — checkable via GFD **or** Sentinel-1.
- **4,302** dated 2019+ — Sentinel-1 only (GFD can't reach these years).
- **~520 duplicate (date, area) groups covering ~1,577 rows** look like
  the same real flood reported by multiple separate news articles — the
  realistic unique-event count is closer to **~5,000, not exactly 6,533**.
- Correction to an earlier framing in chat: **every single one of these
  has at least one available real check method** (Groundsource itself
  starts at 2000, same as GFD) — unlike DFO, which had a genuinely
  unreachable pre-2000 chunk. Nothing here is structurally unreachable.
- `area_km2` for post-2015 rows: median 2.9 km², 75th pct 27.4 km², a long
  tail up to ~4,950 km² — mostly real localized areas, occasionally still
  a big regional flood, but nothing like DFO's country-spanning blobs.

## 5i0. Copernicus Global Flood Monitoring (GFM) — checked, real, but currently unreachable (2026-09-07)

User asked whether GFD's 2018 cutoff has a real successor — yes, found
**Copernicus Global Flood Monitoring (GFM)**, an official EU service
(CEMS), same trust tier as GFD (peer-reviewed, already-validated, not a
DIY threshold), covering **2015-present, continuously updated** —
exactly the gap GFD leaves open. Would let us treat 2019+ checks as
final without a local download, the same way GFD already lets us do for
2000-2018.

**Access requires openEO + a separate EGI Check-in account** (not our
existing Google or CDSE login) — real friction getting through this:
several device-code logins expired before being clicked in time, one hit
a genuine "unexpected error" on EGI's Google integration specifically,
but **eventually succeeded** via a properly created EGI Check-in account
(not the Google-federated route). **This login is now cached as a
refresh token — future sessions should NOT need to repeat this whole
device-code dance**, just reconnect and call `authenticate_oidc()`.

**Blocked, but not by us — checked and confirmed twice independently**:
- Direct connection to EODC's own openEO backend (`openeo.eodc.eu`)
  timed out completely after 20 minutes.
- The federated `openeo.cloud` explicitly reports
  `"missing federation components: ['eodc']"` and lists **zero**
  collections even when properly authenticated.

**This is EODC's infrastructure being down/unreachable right now, not an
auth problem and not our code.** GFM specifically lives on EODC's
backend. Retry later — pip package `openeo` is installed
(`pip install openeo`), login is cached, so a future session just needs:
```python
import openeo
con = openeo.connect('openeo.cloud')
con.authenticate_oidc()  # should reuse cached refresh token, no browser needed
con.describe_collection('GFM')  # collection ID, confirmed correct from docs
```
If `list_collection_ids()` still reports `missing: ['eodc']`, EODC is
still down — wait and retry again later, don't re-diagnose from scratch.

## 5i1. NASA MCDWD — second GFD-successor candidate, real product confirmed, API access not yet cracked (2026-09-07)

Second alternative checked (after GFM turned out blocked by an external
outage, §5i0). **NASA's own MODIS flood product, `MCDWD_L3_NRT`**
(MODIS Collection 6.1, product confirmed real via
`ladsweb.modaps.eosdis.nasa.gov/api/v2/measurements/products` — it's a
genuine, currently-listed product, not a guess). Same idea as GFD (250m,
satellite-observed flood pixels) but **actively maintained since 2012**,
with a full reprocessed archive through 2025 released this year plus an
ongoing daily NRT feed — exactly the "GFD that never stopped" we wanted,
same trust tier (NASA's own operational product, not a DIY threshold).

**What's confirmed working:**
- The LAADS DAAC API itself is alive and responding
  (`ladsweb.modaps.eosdis.nasa.gov/api/v2/...`), unlike GFM's EODC
  backend which is currently down.
- Product `MCDWD_L3_NRT` genuinely exists, archive set `61`, collection
  `61` — confirmed by querying the real products catalog, not assumed.
- `disasters.nasa.gov`'s older ArcGIS ImageServer endpoints (found via
  web search) are **dead/moved** — don't waste time retrying those,
  they 404 no matter the path tried.

**What's NOT yet working — a real blocker, not a guess to repeat**:
every actual content query against `/api/v2/content/details` or
`/api/v2/content/archives` comes back with an empty file list, **even
with no location filter at all, just a broad date range**. This is not
"no data for our specific spot" — it's zero files for anything, which
means the query format itself is wrong somewhere (this product likely
organizes files by MODIS sinusoidal tile grid rather than plain lat/lon
bbox, or needs a different date syntax specific to this product) — not
that the product has no data.

**Exact commands already tried, don't repeat verbatim — vary the
approach instead:**
```
GET /api/v2/content/details?products=MCDWD_L3_NRT&collections=61&temporalRanges=2020-06-01..2020-06-08&regions=[BBOX]W94.6232 N27.5649 E94.9232 S27.2649
GET /api/v2/content/details?products=MCDWD_L3_NRT&collections=61&temporalRanges=2020-06-01..2020-06-03   (no region filter — still empty)
GET /api/v2/content/archives?collections=61&products=MCDWD_L3_NRT&temporalRanges=2020-06-01..2020-06-03  (HTML listing — also empty, just a "Next Page" link)
```
All returned `content: []` with a nonzero `n_pages`, an internally
inconsistent-looking response worth double-checking against the full
official API-v2 user guide (only partially fetchable this session) or
by testing with a real NASA Earthdata login (not yet created — a
separate, much simpler, well-established signup than EGI Check-in was).

**Next step when resumed**: read the full LAADS API-v2 user guide
end-to-end (not just search snippets) for a genuine worked example of
this exact product, or just create a NASA Earthdata account and try
their web search UI directly to confirm data really exists for a known
date/tile before debugging the API further.

## 5i. Faster verification route found and validated — Sentinel-1 lives inside Earth Engine too, no download needed

User's question, 2026-09-05: *"do we need to do the same local download
check for each of those events? can we not do some like we did for the
previous events using the earth engine images... it saved us a lot of
time didn't it?"* — checked, and yes, partially, with an important honest
nuance below. **This is the concrete next step, to run after the current
CWC-gauge Sentinel-1 batch (fetch_29) finishes.**

**Finding**: `COPERNICUS/S1_GRD` — the same real Sentinel-1 GRD scenes we
have been downloading one at a time from Copernicus Dataspace — is
*also* hosted directly inside Earth Engine, pre-calibrated to sigma0 dB.
This means the same "new water vs. dry-season baseline" comparison our
own pipeline does locally can be run **entirely server-side, with zero
downloads**, for any Sentinel-1-era date (2015-now) — not just the
2000-2018 window GFD covers.

**Validated directly, not assumed** — re-checked 4 events we'd already
confirmed real via our own downloaded-and-calibrated pipeline, using the
identical scenes via Earth Engine instead:

| Event | Our pipeline (downloaded, calibrated) | Earth Engine (`COPERNICUS/S1_GRD`, VV, -17dB threshold, no download) |
|---|---:|---:|
| #4919 (2020-06-04) | 15.86% | 14.45% |
| #5183 (2022-01-20) | 8.05% | 5.03% |
| #5101 (2021-07-31) | 7.6% | 3.0% |
| #4963 (2020-09-15) | 5.9% | 4.0% |

**Honest read of this result**: all 4 agree on the thing that matters
most for triage — real flood, real positive signal, right order of
magnitude. **But the exact percentage does not match precisely** —
Earth Engine's version of the same scene is processed slightly
differently (different terrain-correction/resampling choices than our
own `sentinel1_flood_evidence.py` pipeline) — so the two numbers are
**not interchangeable one-for-one**. Do not swap Earth Engine's % directly
into training/calibration data expecting it to mean the same thing as
our own pipeline's %.

**Decided plan (two-step, not a full replacement) — do this after
fetch_29 finishes**:
1. **Screen every 2019+ candidate through `COPERNICUS/S1_GRD` in Earth
   Engine first** — free, ~2 minutes per hundred candidates (same speed
   already proven for the GFD checks). This tells us which candidates
   show *any* real flood signal at all vs. genuinely nothing, at near-zero
   cost.
2. **Only download and run our own precise pipeline on the candidates
   that pass that screen** — the (likely large) chunk of candidates that
   show zero signal in the free screen never need to be downloaded at
   all. The exact number that goes into training/calibration still comes
   from our own pipeline, not Earth Engine's version, given the precision
   mismatch above.

This should cut the slow, flaky-network download work down to a fraction
of the full candidate count, while keeping our own calibrated numbers as
the ones that actually feed the model. Applies immediately to: the 4,302
2019+ Groundsource Arunachal candidates (§5h), and any future Sentinel-1
batch in this project going forward — worth porting into `fetch_27`/
`fetch_29`'s pattern as a standard pre-filter step, not a one-off.

**Not yet built**: the actual screening script. When picking this back
up, write `fetch_30`-style: reuse the `find_scene_in_window`-equivalent
logic but against `COPERNICUS/S1_GRD` (filter by `instrumentMode='IW'`,
`transmitterReceiverPolarisation` contains `'VV'`, bounds, date), a
per-orbit dry-season baseline image (same `relativeOrbitNumber_start`
matching), then `reduceRegion` over a matching buffer — code sketch
already proven working in the chat session that validated the 4 events
above, not yet saved as a standalone script.

## 5j. Why we deliberately will NOT locally verify every candidate — decided 2026-09-05

User's question, in good faith: *"if we get 100,000+ events and 5,000+ for
local AP, sounds like waste not to use them all."* Worth a precise,
permanent answer, since it will come up again.

**Two separate free/paid split, restated precisely:**
1. **Server-side screening (Earth Engine — GFD for 2000-2018, raw
   `COPERNICUS/S1_GRD` for 2019+) is cheap enough to run on ALL
   candidates**, Arunachal's 5,000ish or the whole arc's 150,000+ alike —
   roughly 2 minutes per hundred candidates, so even 150,000 is on the
   order of ~2 days of server-side querying, not weeks.
2. **Local download + our own precise pipeline is the expensive step**
   (today's real observed rate: ~1.2-1.7 MB/s, a scene is ~1.2-2.3 GB,
   and CDSE connection failures are common — multi-hour multi-pass runs
   even for a few hundred candidates, see §5f/§5g's real history this
   session). This step is deliberately NOT run on every candidate, only
   on whichever pass the free screen.

**Why not download-check literally everything the screen flags as real,
either — decided, not just cost-driven:**
- Directly measured earlier this session: doubling Arunachal's own event
  count 34→74 did **not** improve the WHERE ranking's middle-risk classes
  (see the calibration section elsewhere in this doc). More events from
  the *same* handful of rivers mostly repeat information already learned;
  they don't add new lessons.
- What actually matters for a *pixel-level* model is **event diversity**
  (different rivers, terrain, storm types), not raw event count — each
  single verified event already contributes millions of pixels on its
  own, so the marginal value of a 500th similar event is low while its
  download cost is exactly the same as the first.
- **Nothing is discarded permanently.** Every candidate stays in the
  pooled list forever. This is a staged rollout — check a diverse,
  representative slice first, hold the rest in reserve, and go back for
  more only if a real gap shows up later (e.g., calibration reveals we're
  weak on one flood type or region) — same standing "retrain on a
  cadence, keep adding real events over time" rule already in force
  everywhere else in this project ([[ensemble-strategy-decided]]).
- Analogy used in chat: measuring a country's average height needs a
  good sample of a few thousand people, not literally everyone — more
  data past that point barely moves the number while costing enormously
  more to collect.

## 5k. Why pixel-level was needed at all, restated precisely (not a data-scarcity workaround)

Also asked in chat, worth pinning down for good: **more events (even
100,000+) never made event-level training viable, because the limitation
was never about how much data existed — it's what one event-level *row*
can represent.**

- **An event-level row can only ever answer "did a flood happen somewhere
  in this general area?"** — that's what gets left in a table once a
  whole event is compressed into one row of aggregate features. No amount
  of additional rows changes what a single row can say.
- **WHERE's entire purpose is the finer question**: *which exact spot,
  not just which general area.* Only a per-location (pixel-level)
  representation can carry that distinction — this is a structural
  requirement of the *task*, not a symptom of too little data.
- **What more events DOES fix**: pixel-level training needs both (a)
  enough pixels (one event already gives millions) and (b) enough
  *distinct* real places/storms to generalize from — 100,000+ diverse
  events fixes (b), which the earlier 34→74 same-region test proved was
  the actual missing ingredient, not (a).
- **Conclusion, unchanged by scale**: event-level is trainable with
  enough rows, but always answers the wrong question for WHERE.
  Pixel-level was never a stopgap for having too few events — it is
  the only representation that matches what WHERE is actually for, and
  more real events make it *better*, not *unnecessary*.

## 0h. fetch_37 DONE, 2026-09-09 — real per-pixel flood masks extracted for all 3,546 screen-positive candidates

**Status: COMPLETE.** `scripts/fetch/fetch_37_pixel_mask_extract.py` finished
its full run: **3,546/3,546 masks extracted, 0 failures.**

- Output: `data/interim/flood_where_pixels/<uuid>.npz`, one file per event —
  3-band uint8 arrays (`fw`=flood-day water, `bw`=baseline water,
  `nw`=new water, the actual positive-class mask), 1000×1000px @ 10m
  (10km×10km crop per event), plus lat/lon/scale metadata.
- Verified against disk: 3,546 files present, byte-for-byte matches the
  report's "ok" count. Total size 0.19 GB compressed.
- Average `pct_new_water_10km_crop` across all masks: 4.65% (realistic
  class imbalance — not inflated). 494/3,546 masks show 0% new water in
  the 10km crop (edge cases where the flood signal sits outside the crop
  or below the -17dB threshold; still usable as hard negatives, not
  discarded).
- Source breakdown, confirmed disjoint by uuid: fetch_32 (2,178) +
  fetch_33 (616) + fetch_36 (752) = 3,546 exactly, no double-counting.
- **This closes the pixel-data bottleneck** that had been blocking real
  WHERE ensemble training since §0g's "provisional means two things"
  finding — the aggregate-percentage half of that problem is now fixed
  for every screen-positive candidate. (The second half, cross-validating
  against the local pipeline on a small sample, remains Phase 2, deferred.)
- Ran across ~8 session-boundary resumes; one concurrency incident caught
  and fixed mid-run (see below), otherwise 100% clean.

### Concurrency incident, caught and fixed 2026-09-09

Two (possibly more — background-task panel showed 2 running + 4 finished)
instances of fetch_37 ended up running at once across separate resumes.
Checked for damage before continuing: compared uuids with `status: "ok"`
in the report against `.npz` files actually on disk — **zero missing,
zero corrupted, 114 files on disk ahead of the last JSON checkpoint**
(expected — the script writes the `.npz` file before its periodic JSON
checkpoint, so disk always leads the report slightly). No overwrite or
race condition actually occurred, but running two at once was still
unsafe as a matter of design (both instances read the same "remaining"
list from the same stale checkpoint) — one instance was killed, the
survivor finished cleanly. The last 2 candidates separately hung past the
script's own 60s per-candidate timeout (~18 minutes with no checkpoint
movement, likely a network-level stall the thread-executor timeout
couldn't interrupt); killed and restarted, resume-safe design closed out
the final 2 in under a minute. **Lesson for any future long batch fetch
script: the per-candidate timeout does not guarantee the underlying
network call actually gets interrupted — a stuck candidate can still
block the whole batch indefinitely.**

## 0i. Tree vs deep learning — decided again for WHERE, same reasoning as landslides, restated 2026-09-09

Asked directly in chat: does 3.546 billion labeled pixels mean deep
learning is now viable? **No — restating why plainly, since the "billions
of pixels" framing is genuinely easy to misread as "billions of training
examples."**

- **3.546 billion is a pixel count, not an independent-example count.**
  It comes from only 3,546 distinct events, almost certainly clustered on
  a much smaller number of actual Arunachal river systems repeating
  across different years/storms.
- **Tree models train one pixel at a time** (elevation/slope/distance-to-
  river → flooded or not) with no notion of neighboring pixels, so 3.5B
  rows genuinely are 3.5B usable, mostly-independent training rows for a
  tree. This is why trees are the right choice for this dataset today —
  same underlying reasoning as [[why-trees-not-deep-learning]] on the
  landslide side.
- **Deep learning (CNN/U-Net-style, spatial-pattern models) needs
  diversity of independent *scenes*, not pixel volume** — neighboring
  pixels within one flood crop are almost the same information repeated,
  so more pixels from the same 3,546 scenes doesn't teach it more. It
  needs many genuinely different rivers/terrains/storms or it just
  memorizes our ~40-50 actual Arunachal rivers.
- **Rough estimate for when DL becomes viable**: ~500-1,000 genuinely
  distinct river/terrain locations, which — given AP's repeat rate — is
  roughly 15,000-30,000 accumulated events over time if confined to AP
  alone. This is a time/diversity problem, not a modeling problem;
  revisit as a yearly checkpoint, not a blocker.
- **The real unlock, if wanted sooner: Himalaya-arc-wide pooling.**
  Groundsource holds ~150,000 raw (unverified) candidate reports across
  the whole arc (Bhutan/Nepal/Sikkim/Himachal/Uttarakhand/J&K/sub-
  Himalayan-WB + AP) — see line ~1288 of this doc for the original cost
  estimate (~2 days of server-side Earth Engine screening for all
  150,000, same free method as fetch_32/33/36). If the AP screening yield
  rate (~65%, 3,546/5,476) held arc-wide, that's a plausible
  **90,000-100,000 real verified events spanning multiple countries and
  river systems** — which would supply the geographic diversity DL
  actually needs, not just AP's own repeats. **This has not been run
  yet.** It is the literal "Himalaya-pooled DL" option already sitting in
  the §0 table of four candidate model architectures (line ~63) — nothing
  new to decide, just the next scale-up step if/when prioritized.

## 0j. Train-then-calibrate — restated for WHERE, same recipe as WHEN, 2026-09-09

Asked directly in chat: does training the tree model on the 3,546 events
reach the original goal (a real probability, not a relative index)?
**Yes — but training alone is necessary, not sufficient. Calibration is
the second, separate step that actually gets there**, exactly as already
proven for WHEN (calibrated & event-verified across 29 stations, see
[[flood-when-pilot-plan]]).

- **A trained model's raw score is a ranking, not a percentage** — "0.78"
  only means "riskier than something scored lower," nothing more, until
  it's checked against reality. Showing a raw score as a percentage is
  the exact trap already flagged in [[percentile-max-is-not-a-probability]].
- **Calibration**: hold back real verified events the model never trained
  on, run the model on them, and check — of everything scored ~0.78, did
  roughly 78/100 of them actually flood? Adjust the score-to-probability
  mapping until real frequency matches the number shown.
- **3,546 events is enough to do both** — train on most of it, hold back
  a genuine untouched slice for calibration (calibration needs far fewer
  events than training).
- **Product framing, once done**: instead of a High/Medium/Low label
  shared across a whole zone, every point on the map gets its own real,
  checked percentage — e.g. a riverside field at 73%, a bridge approach
  at 41%, a nearby hillock at 8%, even though all three sit inside the
  same "flood-prone area." This is the actual definition of "done" for
  the ACTIVE PRIORITY stated at the top of this doc.

## 0k. TRAINED AND CALIBRATED, 2026-09-20 — the goal in §0 is met, with one honest limit

**Status: the ACTIVE PRIORITY at the top of this doc is DONE.** WHERE now
emits a calibrated probability per 100 m cell, not a percentile index.
Held-out calibration error **1.64% pooled, 1.35% inside Arunachal** —
i.e. ground the model promises 10% to really does flood about 10% of the
time. `webapp/assets/flood/floodprob.npz` ships it; `floodprone.npz` (the
old rule-based index) is left in place beside it for comparison.

### What runs

    scripts/build/build_unmasked_stack.py       feature stack, no state clip
    scripts/build/build_flood_where_samples.py  masks -> training table
    scripts/model/train_flood_where.py          train + cross-fitted calibration
    scripts/model/predict_flood_where.py        score the state
    scripts/model/check_flood_where_sanity.py   physical checks on the output

### Three things had to be fixed first, and each was a real defect

**1. The state clip was destroying the dataset.** Every terrain layer in
`data/interim/terrain/` is computed over the full grid and clipped to the
Arunachal polygon on write. Arunachal's floods are on the Brahmaputra
floodplain, and the state line runs along it. Measured: the clip kept
**361 of 2,508** events with flooded cells, and **4.3%** of the flooded
100 m cells. `build_unmasked_stack.py` rebuilds the same layers unclipped
— same derivation code, imported not copied — recovering **3,021 events
and 4,027,359 training rows**. Geology is dropped (APSSDI is
Arunachal-only and cannot follow the data across the line).

**2. The labels are real water, not radar shadow.** Checked before
training, because this is the exact failure that made the Bhuvan mask
unusable (70.5% of its flooded pixels on cliffs — see
[[bhuvan-flood-mask-is-unusable]]). Ours: **0.0% of flooded cells on
slopes above 15°**, median slope 1.0°, median HAND 0.7 m. Same-orbit
baselines are why — shadow is fixed by viewing geometry, so it cancels
in `new = flood-day water AND NOT baseline water`.

**3. Two models scored better on validation and were wrong on the map.**
This is the finding worth remembering. See below.

### The trap: validation cannot see out-of-distribution failure

**97% of the training rows sit below 500 m elevation.** They are cells in
10 km crops around flood reports, and the floods are in the lowland. Every
cross-validation fold is drawn from that same population, so no fold ever
asks the model about a mountain. Two variants passed validation and failed
physically:

| variant | AUC in Arunachal | what the map actually did |
|---|---|---|
| + ESA WorldCover | **0.936–0.950** | top cells were **glacial lakes**, median HAND 360 m |
| + elevation, aspect, soil | 0.822 | top cells were flat shelves at **1,709 m** |
| shipped: geometry only | 0.854 | top cells at **HAND 0 m, slope 1.0°, 147 m** |

Land cover fails because its classes are learnt on the floodplain and
change meaning with altitude: "permanent water" is river channel at 200 m
and **glacial lake** at 3,000 m; "bare/sparse" is sandbar then **scree**.
Absolute elevation and soil fail the same way for the same reason — none
of the three causes inundation, each is really a name for *which part of
the map this is*, and with a lowland-only training set the model used them
to memorise the Brahmaputra and then extrapolated.

**The shipped feature set is therefore geometry only** — height above the
nearest channel, channel size, distance to channel, slope, curvature,
relief, flow accumulation, TWI. Feature importance came out where
hydrology says it should: `hydro_hand_m` **31.4%**, `hydro_chan_km2`
17.7%, `hydro_chan_small_km2` 9.9%.

**A better validation number was the wrong thing to optimise.** The
land-cover model is still trained in `train_flood_where.py` as an
ablation, and its numbers are recorded, so the rejection stays auditable.

### Two scales of drainage, which is what small streams needed

HAND against a 100 km² channel threshold is right for the Siang and
useless in a Tawang side valley, where the creek that floods the village
drains ~15 km². Measured only against trunk channels, a hamlet 30 m above
its own creek reports several hundred metres of HAND and reads as
unfloodable. So `build_unmasked_stack.py` now builds **both**: trunk
(≥100 km²) and small (≥10 km²), each with HAND, channel size and distance.
Both matter to the model, and this is the first concrete progress on the
small-stream gap the flood docs keep flagging.

### The physical ceiling

Above **25 m** over the nearest drainage of either scale, probability is
set to **zero** rather than left to the model. This is not a tuning knob:
of our own 1,400,753 real flooded cells, **99.68% are within 10 m** and
**99.89% within 25 m**. It gates 89% of the state, which is correct — most
of Arunachal is hillside that cannot flood from a river.

### Honest limits — read before quoting any of this

- **Steep ground is the weak case. AUC 0.666, AP 0.017** at 0.15%
  prevalence. Pooled 0.802, Arunachal 0.854. The mountain number is the
  one that describes Jang, and it is mediocre.
- **High-altitude Arunachal is extrapolation, not evidence.** The training
  set is lowland; the ceiling is what keeps that extrapolation safe rather
  than a claim that the model was verified up there. At Jang (2,976 m)
  5.7% of cells are live, peaking at 14.8%. **This must be validated
  locally before it is quoted to a client at the pilot** — and it is a
  concrete, specific reason the Jang field visit and local gauges matter.
- **Conditional, not annual.** The number is the share of flood events
  reaching a catchment that put water on that cell. It is not an annual
  flood chance. The unconditional forecast is this × the WHEN model.
- **Calibration drifts at the top.** The highest bin promises 33.2% and
  delivers 23.3%. Below ~15% it tracks closely.
- **525 of 3,546 events are unused** — they fall outside the DEM window
  (mostly west of lon 91, Sikkim/Bhutan side). Recoverable only by
  extending the grid.

### Statewide result

2,351 km² above 5%, 1,565 km² above 10%, 137 km² above 20%. Physical
checks in `reports/flood_where_sanity.json`: top cells near a channel,
on flat ground, score falling with height, snow and tundra near zero —
**all four pass**.

## 0l. WHEN × WHERE JOINED into one daily forecast, and replayed on unseen years — 2026-09-21

**Status: built and replay-tested.** One number per 100 m patch per day:

    P(patch floods today) = P(flood in this ~10 km area today)   day model
                          x P(water reaches this patch | flood)  WHERE (§0k)
                          x valley factor                        see below

### What runs

    scripts/model/when_grid.py               WHEN score on all 1,953 rain cells, 2015-2026
    scripts/model/flood_forecast.py fit      day model + valley factors (production)
    scripts/model/flood_forecast.py <date>   the forecast: raster + JSON summary
    scripts/model/replay_flood_forecast.py   the 2023-26 replay
    scripts/model/train_flood_where.py --until 2022-12-31 --tag replay2022

### Three design decisions

- **WHEN runs everywhere, not just at 29 gauges.** Its inputs are local
  rain percentiles, defined for any rain cell. Verified: the grid version
  reproduces the original station scores to 4 decimals.
- **A new "day model" sits between them.** WHEN's own probability is for
  "gauge crosses danger level"; WHERE's event is "reported flood,
  satellite-confirmed". Multiplying probabilities of two different events
  is meaningless, so the WHEN score is re-mapped onto WHERE's event. Inputs:
  the WHEN score + the rain cell's floodable ground (sum of WHERE) — taken
  from terrain, deliberately NOT from past report counts, so a valley
  nobody writes news about isn't told it never floods.
- **The replay touches nothing from 2023+.** WHERE retrained on ≤2022
  floods (AUC 0.857 in Arunachal, same as the shipped 0.854), day-model tree
  on 2015-20, its calibration on 2021-22, "normal" levels from 2015-22.
  Scored against 1,028 floods of 2023–2026.

### Replay results (reports/flood_forecast_replay.json)

**Right day** — the timing skill is real but modest. The 0.949 ranking
score is inflated: most of it is floodplain cells flooding more often than
mountain cells, which is WHERE-type information. The honest timing number
is "times normal": on real flood days the chance was typically **2.5×
normal**. Warning at 2× normal catches **57%** of floods (64% counting the
day before) with ~10% of area-days under warning; at 5× it's 21–27% with
2.8%. Brier skill vs climatology only +0.8%.

**Right place** — holds on unseen years. Expected 497k flooded patches,
observed 473k. AUC 0.898 pooled, 0.938 Arunachal, **0.615 steep ground**.

**Together** — the raw join over-promised: 742k flooded patch-days expected
vs 407k observed, and **6.5× in Arunachal** (73k vs 11k). Cause is
structural: WHERE means "given a flood within ~5 km"; the join spreads it
over a ~10 km rain cell, and a mountain rain cell holds several separate
valleys that one flood doesn't all reach. Fixed with a **valley factor**
per terrain class of rain cell (fitted 2021-22, tested 2023-26):

| terrain | factor | test expected | observed |
|---|---|---|---|
| flat <5° | 0.554 | 390,671 | 403,309 |
| hilly 5–15° | 0.121 | 2,262 | 2,105 |
| steep ≥15° | 0.167 | 3,061 | 1,266 |

Region total now **396k vs 407k**. Inside Arunachal still **~3.4× high**
(38k vs 11k). A finer split (terrain × inside/outside the state) was tried
and **rejected**: its in-state factors swung an order of magnitude between
fit and test years and it only reached 2.6× — both variants are kept in
the replay output. Production factors (fitted 2021–26): flat 0.529, hilly
0.088, steep 0.088.

### Showcase days (production model — demonstrations, not tests)

- **30 Jun 2024**: 9.1× an ordinary day; the top areas (27.4–28.0°N,
  95.4–96.3°E, Lohit/Tezu/Namsai) are where that day's confirmed floods were.
- **15 Jan 2024**: 0.1× — quiet, correctly.
- **24 May 2024 — a miss**: 0.3×, on the biggest reported flood day. Local
  satellite rain in the days before was 0–10 mm, so whatever flooded those
  places came from upstream rain (or the report date is off). WHEN looks at
  rain on the spot only, so it is blind to water arriving from upstream.
  Across all floods, ~5% had <20 mm of local rain in the prior week and
  ~15% had <50 mm — a minority, but a real blind spot.

### Honest limits

- Absolute chances are a **floor** (unreported floods aren't in the truth)
  and inside Arunachal still run ~3× high. **Lead with "times normal" and
  the ranking**; don't quote the absolute patch percentage to a client yet.
- Timing skill is modest (2.5× normal on a typical flood day).
- Steep ground remains the weak case for WHERE.

### What would improve it most, in order

1. **Upstream catchment rain** as a WHEN input instead of point rain — the
   24 May class of miss, and likely part of the modest timing lift. Free,
   derivable from IMERG + the existing HydroSHEDS catchments.
   *(Done 2026-09-21 — modest real gain, and 24 May turned out to be a
   label-date problem, not upstream rain. See §0m.)*
2. Live rainfall feed (Open-Meteo, as the landslide side already uses) so
   this runs daily instead of as a hindcast.
3. Local validation at Jang — still the only fix for the mountain numbers.

## 0m. Upstream-catchment rain added to the day model — 2026-09-21

**Status: shipped in the production forecast.** `scripts/build/build_upstream_rain.py`
traces, for each ~10 km rain cell, the catchment of its biggest channel,
and turns daily rain into catchment-mean 3- and 7-day percentiles (the same
scaling WHEN uses locally). The day model now sees local WHEN score +
upstream 3-day + upstream 7-day + floodable ground.

**Tracer note.** pysheds' `catchment()` crashes the process (Windows access
violation, no Python error) on some pour points — border and interior
alike; it has no bounds checks. Replaced with a small numba tracer over a
reverse-drainage graph. Checked: traced catchment size equals flow
accumulation at the outlet for **all 1,832 outlets (0 mismatches)**, runs
in ~4 s. 486 rain cells drain >1,000 km²; median 252 km². Limit: catchments
stop at the grid window, so for the Siang most of the true (Tibetan)
catchment is unseen.

**Replay, same test as §0l, local-only vs local+upstream:**

| | local only | + upstream |
|---|---|---|
| fair timing AUC (each place vs its own normal) | 0.841 | **0.851** |
| typical flood day, × normal | 2.5 | 2.8 |
| warn at 2×: caught / time under warning | 56.6% / 9.8% | 63.8% / 11.4% |
| warn at 5× | 20.5% / 2.8% | 26.6% / 3.9% |
| warn at 10× | 0.8% / 1.9% | **6.7% / 1.1%** |
| 30 Jun 2024 floods | 8.1× | 9.4× |
| 24 May 2024 floods | 0.4× | 0.1× |

A modest, real gain. At 10× it catches more floods while warning less —
better on both axes at once. Region totals after the valley factor still
match (403k vs 407k); Arunachal still ~3.4× high.

### 24 May 2024 was not an upstream-rain miss — it's a label problem

Upstream rain did NOT fix it: catchment rain was ordinary for the season
(7-day percentiles 0.1–0.7). Looking closer:

- 8 of the 10 "24 May" floods were confirmed by Sentinel-1 scenes from
  **21 May**, when regional rain was ~1–6 mm/day.
- The heavy rain (Cyclone Remal's remnants, up to 150 mm/day) came
  **27–28 May** — after both dates.

So the satellite saw "new water" before any rain that could flood it. Two
likely causes, both about the truth data rather than the forecast:

1. **Report dates are loose.** Across all 3,546 floods, only 518 (15%) have
   their confirming satellite scene on the reported date; most are 1–6 days
   off either way (screens allowed ±3 to ±10 days). Timing is graded against
   those dates, so **measured timing skill is an underestimate.**
2. **Possible paddy false positives.** May–June in the Brahmaputra valley is
   rice-transplanting season; flooded paddy vs a dry-season baseline looks
   exactly like "new water". Not yet checked — an open question about label
   quality for both WHEN and WHERE.

### Next candidates

1. **Check the paddy question**: compare May–July "floods" in cropland vs
   other land cover against rain; if cropland events show no rain signal,
   filter them or use a same-season baseline. *(Done — ruled out; the real
   contamination is braided-channel shifts. See §0n.)*
2. **Date-tolerant verification**: score a flood as caught if warned within
   its satellite-scene window, with false alarms counted the same way.
3. Live rainfall feed (Open-Meteo) so this runs daily.
4. Jang local validation — still the only fix for the mountain numbers.

## 0n. Label audit: paddies ruled out, braided-channel shifts found — 2026-09-21

`scripts/model/check_paddy_labels.py` → `reports/flood_paddy_check.json`,
per-flood table in `data/interim/flood_forecast/event_label_audit.parquet`.

**The worry:** a flood label is "water Sentinel-1 saw that wasn't in a
same-orbit dry-season baseline". Rice paddies in the Brahmaputra valley are
deliberately flooded (Ahu Mar–Apr, Sali Jun–Aug, Boro Dec–Feb) and look
exactly like that.

**The test:** a real flood needs water from somewhere — unusual rain,
locally or upstream. A paddy is flooded on a calendar. For 2,353 floods
(mask + rain record + ≥5 flooded cells): the cropland share of the flooded
cells, and the rain signal in the week before the satellite **saw** the
water (scene date, not the loose report date) — the higher of the local and
upstream 7-day percentiles, each vs that place's own monsoon (ordinary
monsoon week ≈ 0.5; "dry" = below 0.5).

### Paddies: ruled out

Cropland-heavy floods come with **more** rain, not less, in every season
with data:

| season | cropland-heavy: n / rain pct / dry | other ground: n / rain pct / dry |
|---|---|---|
| pre-monsoon Mar–Apr | 16 / 0.43 / 56% | 36 / 0.27 / 78% |
| early monsoon May–Jul | 1,148 / 0.86 / 10% | 471 / 0.81 / 19% |
| late monsoon Aug–Oct | 313 / 0.74 / 15% | 328 / 0.66 / 34% |

And it rises steadily with cropland share (0–10% cropland: rain pct 0.68,
35% dry → 75–100%: 0.85, 12% dry) — the reverse of a paddy signature. The
strictest suspect list (≥50% cropland, dry week, rice-season month) is 126
floods, 2.6% of flooded cells, and even those are dry *less* often than
floods on other ground (12% vs 30%). Nothing to remove.

### What it found instead: braided-channel shifts

Rain-less "floods" lean onto river-corridor ground (WorldCover permanent
water 80 + bare/sandbar 60):

| group | floods | channel/sandbar share (median) | mostly channel |
|---|---|---|---|
| rain-backed | 1,913 | 0.10 | 23% |
| dry | 440 | 0.43 | 49% |
| dry season Nov–Feb (all 0 mm rain) | 41 | 0.70 | 73% |

That fits the Brahmaputra and its tributaries moving channels and sandbars
between the baseline image and the flood image, read as "new water" with no
rain behind it. **Channel-shift suspects** (dry + ≥50% channel/sandbar):
**215 floods (9%), 6.4% of flooded cells.** Their ids are in the report.

**Impact, bounded:** for WHERE they mostly teach "water appears right beside
the channel", which real floods also do, so the effect should be small. For
timing they are positives with no rain cause, so they pull the measured
timing skill down — alongside the loose report dates (§0m). Not yet
measured by re-running without them.

### The 24 May 2024 case — still unexplained

Neither paddy nor channel: its flooded cells are **92% tree cover**, 0%
cropland, 0% channel. Radar water detection under forest canopy is
unreliable (flooded forest usually brightens rather than darkens), so the
likeliest explanation is a radar artefact rather than a flood. A handful of
floods, not a pattern — recorded, not acted on.

### Next

- Re-run WHERE training and the forecast replay with the 215
  channel-shift suspects excluded, and see whether timing or place skill
  moves. If it does, exclude them for good (or re-screen them against a
  baseline image from the same season). *(Done — see §0o; excluded for good.)*
- A same-season baseline in the Earth Engine screen would remove channel
  shifts at the source for future pulls.

## 0o. Channel-shift suspects removed — replay decided it, now in production — 2026-09-21

Switches added: `train_flood_where.py --exclude-channel-shift` and
`replay_flood_forecast.py --train-clean / --test-clean`. Three replays
(all with upstream rain, all graded on 2023-26) separate two questions:

| | A: old model, old truth | B: old model, clean truth | C: clean model, clean truth |
|---|---|---|---|
| floods in the test truth | 1,028 | 947 | 947 |
| fair timing AUC | 0.851 | 0.862 | 0.834 |
| typical flood day, × normal | 2.8 | 3.0 | 3.5 |
| warn at 2×: caught / time under warning | 63.8% / 11.4% | 66.0% / 11.4% | 65.9% / **7.0%** |
| warn at 5× | 26.6% / 3.9% | 27.6% / 3.9% | 28.8% / **1.1%** |
| warn at 10× | 6.7% / 1.1% | 6.8% / 1.1% | 11.6% / **0.1%** |
| place AUC (all / Arunachal / steep) | 0.898 / 0.938 / 0.615 | 0.898 / 0.932 / 0.601 | 0.897 / 0.929 / 0.602 |
| Arunachal flooded patch-days, expected vs observed | 38k vs 11.2k | 38k vs 7.6k | 36.7k vs 7.6k |

**A→B (how much the suspects hid):** a little — fair timing 0.851→0.862,
2× catch 64→66%. They were rain-less "floods" nothing could forecast.

**B→C (does cleaning improve the model):** split verdict, decided for
cleaning.
- At every warning level anyone would actually use, the cleaned model
  catches **the same or more floods with far fewer alarms** — at 2×, same
  66% caught on 7% of area-days instead of 11%; at ~1% of area-days, 29%
  caught instead of 7%.
- The overall fair-timing AUC dropped (0.862→0.834). That loss sits at the
  extreme low-threshold end, where warnings would be issued most of the
  time — not a region anyone would operate in.
- WHERE is unchanged (place AUC 0.897 vs 0.898; ≤2022 CV Arunachal 0.861 vs
  0.857, steep 0.692 vs 0.720 — within fold noise at 0.19% prevalence).
- Cleaner labels are also simply more correct: water that appears because
  the river moved is not a flood.

**Side-effect worth knowing:** about a third of the flooded ground inside
Arunachal in 2023–26 (11.2k → 7.6k patch-days) was these suspects. So with
honest labels the Arunachal absolute over-prediction is **~5×, not ~3×**.
The ranking and "times normal" are unaffected; the "don't quote the absolute
percentage in Arunachal yet" rule stands more firmly.

### Now in production

- WHERE retrained without the 215 suspects: 2,806 floods, Arunachal AUC
  **0.865** (was 0.854), steep 0.656 (was 0.666), held-out calibration
  error 1.81% pooled / **1.43% Arunachal**, height-above-channel still the
  top feature (30%). Physical sanity checks: **all four pass**. Map and
  `floodprob.npz` regenerated.
- Day model refit on cleaned labels; valley factors flat 0.516, hilly
  0.090, steep 0.090.
- 30 Jun 2024 → 13.1× an ordinary day; 15 Jan 2024 → 0.1×.

## 0p. Why the joined forecast runs ~5× high inside Arunachal — diagnosed 2026-09-21

Scratch diagnostics, 2022-only clean models, 2023–26 truth. Two ideas were
tested and **ruled out** before the cause was found:

- **"Several separate valleys per rain cell"** — wrong. The count of
  separate stream pieces inside a rain cell has zero weight in a fitted
  reach model, and Arunachal cells hold *fewer* (median 3) than cells
  outside (4). A terrain-based per-cell reach model (Poisson on floodable
  area, slope, trunk share, largest river) only moved Arunachal from 4.8× to
  4.5× and was worse region-wide (432k vs 373k expected, 363k observed).
  Not shipped.
- **"Border cells whose Arunachal side is never looked at"** — wrong. Split
  by rain-cell type, the gap sits in cells **entirely inside** Arunachal
  (29.5k expected vs 6.6k observed, 4.5×), not border cells.

**The flood count is right** — floods centred in all-Arunachal cells,
2023–26: 115 expected, 119 reported. The gap is in how much ground each
flood covers, and it has two roughly equal parts:

> ⚠️ **Corrected 2026-09-27 (§0v):** this count match was an artefact — the
> replay counted Feb–Jul 2026, after the flood record ends, as flood-free,
> adding expected floods that could never be observed. On record days only
> it is **104 expected vs 150 recorded**: the count is ~⅓ low, with the same
> year-to-year drift §0v found. The two parts below still describe the
> patch-level gap.

1. **Where the floods land (~1.8×) — not separable from under-reporting.**
   The day model spreads expected floods across cells with lots of
   floodable ground (averaged over expected floods: 4.9 km² per cell);
   reported floods sit in cells with less (2.7 km²). Only **47 of 667**
   all-Arunachal rain cells had even one reported flood in 3½ years, and
   69% of the expected floods went to the other 620. Nothing in the data
   can tell "the model is too high there" from "floods there go
   unreported" — the flood record is news reports, and remote valleys are
   thin on news. **Deliberately not "fixed":** scaling to match reports
   would teach the forecast that unreported valleys are safe — the same
   trap the day model's design avoids (it uses terrain, not report counts).
2. **Given a flood, too much water (~1.8–2.9×) — real model error.** On
   ground a satellite actually looked at, inside Arunachal: 22.9k flooded
   patches expected vs 8.0k observed on the 2023–26 floods (2.9×), against
   ~1.2× outside. This one is fixable.

**Also found:** in 11 years only **41%** of Arunachal's floodable ground was
ever inside any satellite flood check. The other 59% has never been looked
at, so the "truth" there is always "no flood". That caps how well the
absolute number can be graded in Arunachal with this data — and is one more
concrete reason the Jang gauges and field checks matter.

### Fix for part 2: valley-confinement features — shipped

A flat patch on a narrow mountain valley floor and a flat patch on the open
Brahmaputra plain looked identical to every per-patch feature. Two
neighbourhood features now tell them apart (`build_unmasked_stack.py`
step 3b): **relief** and **mean slope** within a 2.1 km window. They
describe the shape of the ground around a patch, not "which part of the
map" — the trap that got absolute elevation removed.

2022-only clean models, graded on 2023–26 (same test as before):

| | before | with confinement |
|---|---|---|
| WHERE ranking, all / Arunachal / steep | 0.897 / 0.929 / 0.602 | **0.906 / 0.937** / 0.602 |
| given a flood, Arunachal: expected vs observed | 22.9k vs 8.0k (2.9×) | 20.4k vs 8.0k (**2.6×**) |
| given a flood, steep ground | 571 vs 482 (1.2×) | 424 vs 482 (0.9×) |
| joined, Arunachal patch-days | 36.7k vs 7.6k (4.8×) | 32.3k vs 7.6k (**4.2×**) |
| joined, whole region | 373k vs 363k | **369k** vs 363k |
| fair timing AUC | 0.834 | 0.838 |
| warn at 2× / 5× / 10×: caught (time under warning) | 65.9 (7.0) / 28.8 (1.1) / 11.6 (0.1) | 68.2 (7.5) / 22.3 (0.5) / 10.2 (0.1) |

A modest, consistent gain on place, with timing essentially unchanged. The
2022-only cross-validation agreed (steep 0.692 → 0.709, calibration error
1.42% → 0.90%).

**Production model** (all years, 2,806 cleaned floods, 15 features):
all 0.820 (was 0.804), Arunachal 0.863 (was 0.865), steep **0.673** (was
0.656); held-out calibration error **1.29% pooled / 1.13% Arunachal** (was
1.81% / 1.43%). Height above channel still the top feature (25.6%);
2 km mean slope 6th (7.3%). **Physical sanity checks: all four pass** (top
cells 0 m above channel, 0.4° slope, 136 m elevation; snow 0.01%, tundra
0.00%) — so the new features did not reopen the mountain-as-floodplain
failure. Day model refit: valley factors flat 0.485, hilly 0.114, steep
0.167. 30 Jun 2024 → 11.8× an ordinary day; 15 Jan 2024 → 0.1×.

Previous production models are backed up in the session scratchpad, not in
the repo.

### Where the Arunachal gap stands now

Joined forecast still ~4× high inside Arunachal on reported-flood truth.
About half of that is part 1 (can't be told from under-reporting — leave
it); the rest is WHERE still ~2.6× generous given a flood in the
mountains. **Rule unchanged: lead with "times normal" and the ranking; do
not quote the absolute percentage in Arunachal.** What would settle it is
local truth — the Jang gauges and field checks — not more modelling on
news-reported floods.

## 0q. The flood forecast runs on LIVE rain — today plus 7 days — 2026-09-21

    python scripts/model/flood_forecast_live.py build   # once (re-run after retraining)
    python scripts/model/flood_forecast_live.py         # daily
    -> reports/flood_forecast_live_<date>.json, data/processed/flood_forecast_live_<date>.tif

**Rain source:** Open-Meteo, the same service and the same 97 points the
landslide side already fetches (`webapp/core/rainfall.py`, reused, not
copied) — so both hazards share one download. Open-Meteo reads 1.68× wetter
than IMERG and agrees with it only loosely day to day, so live rain is never
compared with IMERG history. Every model input is re-scored against the
live service's OWN 2010–2026 archive (`data/interim/rainfall_om`): local
3/7-day rain at the nearest of the 97 points, and upstream-catchment rain
using the same catchment weights as §0m. "Times normal" divides by the live
path's own ordinary level.

### What the live feed costs — measured, not assumed

Three day models fitted identically (tree 2015–20, calibration 2021–22),
graded **inside Arunachal** on 2023–26 (1,306 days, 150 floods, unseen by
all three):

| | satellite rain | satellite-fitted, live rain | live-fitted, live rain |
|---|---|---|---|
| fair timing score | 0.725 | **0.725** | 0.670 |
| typical flood day, × normal | 1.7 | 1.5 | 1.2 |
| warn at 2×: caught / time under warning | 36% / 3.3% | 31% / 2.0% | 24% / 1.6% |
| warn at 5× | 9% / 0.7% | 6% / 0.3% | 7% / 0.3% |
| warn at 10× | 4% / 0.3% | 4% / 0.2% | 3% / 0.0% |

- **The live feed costs almost nothing in ranking**: the satellite-fitted
  model fed live-scaled rain scores the same 0.725 — it sits at a slightly
  more cautious point (fewer alarms, a few fewer catches) on the same curve.
- **Refitting on the live archive is worse** (0.670): that archive is
  weather-model rain, a weaker teacher than observed satellite rain. Not
  shipped. The daily run uses the production day model unchanged.
- A first, unfair version of this check (the shipped model, whose training
  years overlap 2023–26) showed 0.841 → 0.796 and suggested a big cost. That
  was the satellite run being graded partly in-sample. Recorded so it isn't
  re-quoted.

**Sobering and honest: timing inside Arunachal is weaker than region-wide.**
Out-of-sample, in-state: fair timing **0.725** (vs 0.838 across the whole
replay region); warning at 2× normal catches about **1 in 3** Arunachal
floods while under warning ~3% of the time.

### Sanity on known days (live pipeline, live-service archive)

- 28 Jun 2024 → 4.6×, 29 Jun → 9.3×, **30 Jun → 9.5×** an ordinary day
  (satellite path: ~12×) — rising a day or two ahead.
- 15 Jan 2024 → 0.1×. 24 May 2024 → 0.3× (the §0m label-date case).
- 28 May 2024 (Cyclone Remal's heaviest rain) → only 1.5×.

**First live issue, 21 Sep 2026:** 0.3–0.5× an ordinary day all week —
quiet, as expected for the tail of the monsoon.

### Limits

- The 97 points are ~33 km apart and all inside Arunachal: local rain is
  coarser than IMERG's 11 km, and catchment rain from Tibet/Bhutan is filled
  from the nearest in-state point. *(Since 2026-09-22: 219 points, ~22 km
  apart — §0u.)*
- Days 4–7 of the outlook ride on forecast rain, which is weak in mountains;
  treat them as indicative.
- *(Scheduled daily at 08:30 since 2026-09-22, and shown in the web app's
  FloodSense "Live forecast" screen from a daily snapshot; see
  FLOOD_WHEN_PILOT_PLAN.md §13b.)*

## 0r. River gauges in the live run, and a track record — 2026-09-21

The daily live run now also issues a calibrated chance per gauged river
(32 gauges, today + 6 days), fed each river's latest CWC/NWDP reading. It
logs every river forecast and area outlook, and grades the river forecasts
automatically against the gauges once each day has passed. The full numbers
are in [FLOOD_WHEN_PILOT_PLAN.md §13](FLOOD_WHEN_PILOT_PLAN.md).

The area outlook is logged but not yet graded: its truth is
satellite- or news-confirmed floods, which arrive late.

## 7. Why it was parked (original parking note, predates the 2026-09-09 work above)

User's own words: *"Hold it for now. Doc it as very important so that next
time we return to WHERE for flood we continue from here."* Not a technical
setback — the proof batch worked. Purely a scope/cost decision waiting on
the user, exactly like the landslide version of this same idea.

**Status as of 2026-09-09: no longer parked for lack of data** — the
pixel-mask bottleneck (§0h) is now closed. What remains is model work
(train + calibrate, §0j) and an open scale-up option (Himalaya-arc pooling
for DL, §0i), both ready to start whenever prioritized.

## 0s. River readings on the MAP — tested, did NOT help, not shipped — 2026-09-22

**Idea.** At a gauge, the river's own reading made the gauge's forecast far
better (§0r). The test here: does feeding it into the map's day model help
the valleys downstream too?

**Built:**
- `scripts/build/build_gauge_reach.py` follows each of the 32 gauged rivers
  downhill on the 100 m flow-accumulation grid.
  - It snaps each gauge to the biggest channel within 1.5 km, then steps to
    the neighbour with the most flow.
  - It records which rain cells each river passes through; 196 cells have a
    gauge upstream.
  - Traced catchments match the published ones where CWC gives them:
    Lemeking 11,321 vs 11,318 km², Kibithu 11,891 vs 12,949.
- It hands each of those cells yesterday's reading from the gauge upstream,
  on the same ordinary→threshold scale the gauge models use (`gauge_frac.npz`).
- `DayModel` now accepts inputs that may be missing (`optional`), which is
  backward-compatible with the shipped pickle.
- `replay_flood_forecast.py --gauge` switches the input on. Every replay now
  also scores the gauge-reached cells separately.

**Result** (same fair replay: tree 2015–20, calibration 2021–22, graded on
unseen 2023–26, clean labels, upstream rain in both):

| timing-only AUC | today's map | + gauge reading |
|---|---:|---:|
| whole region | 0.838 | 0.829 |
| cells with a gauge upstream (280 floods) | 0.839 | 0.824 |
| … inside Arunachal (75 floods) | 0.757 | 0.716 |

Warn at 2×: 68% caught before, 66% after. Worse everywhere, so it is not
shipped. The production day model is unchanged.

**Why (diagnosed, not guessed):** on its own, the gauge reading ranks the
map's flood records as well as rain does in 2015–22 (AUC 0.851 against
0.848). But it falls to 0.77–0.80 in 2023–26 while rain holds at 0.83–0.84.
- It is not the new NWDP gauges: CWC-only gives the same drop (0.851 →
  0.774).
- The map's truth is satellite/news-confirmed floods centred in a ~10 km
  cell, with loose dates. The gauge's truth is its own river crossing its
  threshold.
- Downstream of a gauge, the flood that gets reported is often a tributary
  or local flood the trunk gauge doesn't see. So the reading carries the
  same storm information as rain, overlaps with it, and is unstable across
  periods.

**Don't retry the same way.** Retest `--gauge` only when either:
- the map has its own graded track record (`records/flood_forecast/`) from a
  monsoon or two, or
- local truth arrives that ties floods to specific rivers (Jang).

At the gauges themselves, the reading stays the headline number (§0r).

## 0t. Auto-grading the MAP with Sentinel-1 — tested, NOT reliable enough, not wired in — 2026-09-22

**Idea.** River forecasts grade themselves against the gauge (§0r). The map's
area outlook has no such feed — its truth is news-reported floods, which
arrive late and patchily. Sentinel-1 (free, inside Google Earth Engine, no
download) sees the whole state every ~6-12 days. Could it grade the map
automatically, the same way a gauge grades a river forecast?

**Built:**
- `scripts/fetch/fetch_38_s1_cell_water.py` — per satellite pass, per rain
  cell: share of low ground (MERIT HAND < 10 m) under NEW water (VV <
  -17 dB, not wet in that orbit's March baseline). Runs entirely in Earth
  Engine. Extracted the full 2024 monsoon: 98 passes, 49,322 cell-passes,
  1,793 cells, ~80 min, one pass timed out (skippable, backfillable).
- `scripts/model/check_map_grader.py` — asks two honest questions before
  anything relies on this: (a) do already-known floods stand out from the
  grader's own noise floor, (b) does the map's forecast rank the grader's
  wettest cell-passes the way it ranks known floods.

**Result: (a) partially yes, (b) no — and (b) is the one that matters.**
- Known 2024 floods score AUC 0.74–0.76 against the grader's "excess new
  water" (in line with what a satellite check should show) — the satellite
  half of the idea works on its own.
- But the map's forecast has **no relationship** with the grader's general
  ranking: rank correlation ≈ 0.00, and AUC for the grader's own wettest 1–5%
  is only 0.58–0.66 — barely above chance, far below the 0.817 the same
  forecast gets when graded against the known floods on the same pass days.
- Two candidate fixes tried, neither closed the gap: comparing each pass
  only against its own relative orbit's history (same viewing geometry) —
  barely moved (a) and did nothing for (b); dropping cells that repeatedly
  top the "wettest" list across many unrelated dates (285 of 1,793 cells,
  a likely non-storm-cycle signature) — no improvement either, and only 13
  of those 285 overlap the already-known braided-channel-shift suspects
  (§0n), so it is not the same contamination.

**Reading:** the satellite half genuinely sees real floods. But most of what
it flags as "unusually wet" on an ordinary pass is something else the
forecast rightly does not chase — soil moisture, small watercourse
dynamics, or plain single-pass speckle that a 30 m median filter and a
single March baseline do not remove. With floods a rare 200 of 48,456
cell-passes, that noise swamps any ranking-based automatic grade.

**Not wired into the daily run.** Wiring an unreliable grader in would teach
the wrong lesson, silently, exactly the trap the whole calibration effort
has been careful to avoid. The extraction script and data are kept — this
is real, reusable groundwork, not a dead end:
- `s1_cell_water.parquet` is real evidence for any future spot-check.
- A next attempt would need a genuinely cleaner per-pixel water test (e.g.
  a multi-look/multi-date despeckle instead of one baseline scene, or
  restricting to a river-adjacent mask instead of all low ground) before
  trying this measurement again — a bigger job than this pass, parked here
  deliberately rather than half-fixed.
- The area outlook keeps relying on the existing evidence: replay against
  news-confirmed, satellite-verified floods (§0l–§0p), and whatever Jang
  ground truth eventually provides.

## 0u. More live rain points — done, but no measured timing gain — 2026-09-22

**Idea.** Live rain samples at only 97 points, ~33 km apart — coarser than
the 11 km IMERG grid the models were trained on, and the leading suspect
for why live-rain timing (0.71–0.72) trails the region-wide replay (0.847).
Open-Meteo can serve far more points for free; the limit found earlier
(`fetch_20_openmeteo_climatology.py`) was the LIVE app's per-refresh cost,
not the archive backfill.

**Done:** moved the shared rain spine from 0.3° (~33 km, 97 points) to 0.2°
(~22 km, 219 points) — roughly double density, not the previously-tried-
and-rejected 892-point (11 km) grid, which would need ~30 batches per
refresh. 219 needs ~8, still inside Open-Meteo's per-minute limit and still
hourly-cached (`core/rainfall.py`), so no visitor pays for it directly.

- Archive backfill: 21 min, 45 calls, a few rate-limit backoffs handled
  automatically, zero failures. `data/interim/rainfall_om/` regenerated.
- This is genuinely shared infrastructure, not flood-only: it also feeds
  SlideSense's live trigger (`webapp/assets/base/points.json`,
  `clim_quantiles.npz`, `nearest_point.npz`). Both products were re-tested
  after the change (below).
- Found and fixed 5 **pre-existing, unrelated** bugs in
  `scripts/run/export_webapp_bundle.py` while re-running it: `elevation.npz`,
  `clim_quantiles.npz`, `roads.geojson`, `rivers.geojson` and `towns.json`
  are written to `BASE` but the size the script PRINTS was read from `OUT`
  (the landslide folder) — cosmetic (a crash on the print line, not on the
  actual write), but it crashed the export outright since Python evaluates
  the f-string before printing. Also added a loud assert on the
  `nearest_point.npz` uint8 index (219 fits; 892 would silently wrap).

**Result: no measurable timing gain, honestly reported.** The number that
matters — the shipped model (satellite-fitted) fed live rain, inside
Arunachal, 2023–26 — moved **0.714 → 0.716**. Not an improvement worth
claiming; well inside noise on 150 floods. The "satellite" column (IMERG
only, untouched by this change) stayed exactly 0.736, confirming nothing
else shifted. The diagnostic live-fitted model moved 0.687 → 0.659 (never
shipped; a further sign that 150 floods is not enough to read small
differences at this scale).

**Why it likely didn't help:** either Open-Meteo's own reanalysis doesn't
carry real skill finer than what 97 points already captured — sampling it
more densely doesn't invent detail the source model doesn't have — or the
150-flood, 1,306-day Arunachal test is simply too small to detect a real
but modest gain. Both are plausible; this pass doesn't distinguish them.

**Kept anyway.** It halves the documented sampling gap (33 km → 22 km,
still stated honestly wherever the caveat appears), fixed a real class of
bug in the export script, and cost nothing ongoing (same hourly cache).
Going further (finer than 22 km) would need the live app itself to change
— a background refresh job instead of "first visitor after the hourly
cache expires pays for the fetch" — a separate, bigger piece of work, not
attempted here.

Both products retested after the change (Streamlit `AppTest`, all screens):
zero exceptions. SlideSense's own live trigger screen correctly reports
"of 219" points now.

## 0v. "Flood chance near here" — a uniform %, built and tested: Gate A FAILED — 2026-09-27

**The ask:** one real percentage for every place in Arunachal (not "× usual"),
honest about where it is weaker. Plan and pre-registered pass marks:
[FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md) (Phase 2, Gate A).

**What was built** (`scripts/model/near_here.py`, nothing else changed): on
top of the UNCHANGED day model, the chance of ≥1 flood record within 10 km of
a place (centre of its 0.1° rain cell), per day and over 7 days, plus
"anywhere in Arunachal". Raw = area-weighted union of the day model's cell
chances; isotonic curves fitted to how often it really happened; logical
limits enforced (week ≥ its likeliest day, ≤ the sum of days; near-here ≥ own
cell). Test: WHERE (floodable area) retrained to 2022, day model tree
2015–20 / calibration 2021–22, fed the live-archive rain, curves fitted
2021–22, graded 2023-01-01 → 2025-10-31 inside Arunachal.
Reports: `reports/flood_near_here_check.json` (10 km),
`..._check_20km.json` (the one pre-registered alternative),
`reports/flood_near_here_diagnosis.json`.

**Result — ranks well, level not stable:**

| inside Arunachal, 2023–25 | 10 km, day | 10 km, week | 20 km, week | state, week |
|---|---|---|---|---|
| A1 forecast ÷ recorded (pass 0.67–1.5) | **0.58** ✗ | **0.55** ✗ | 0.61 ✗ | 0.87 ✓ |
| A2 every range within 2× (≥10 floods) | ✗ | ✗ | ✗ | ✓ (2 ranges) |
| A3 Brier skill vs its own season | +0.003 ✓ | +0.016 ✓ | +0.025 ✓ | −0.19 ✗ |
| AUC (places × weeks) | 0.84 | 0.86 | 0.86 | 0.81 |
| logical limits (A4) | 0 violations | 0 | 0 | 0 |

By year (10 km, place-days): 2023 forecast 90 vs recorded 98; **2024 93 vs
194; 2025 74 vs 149**. Region-wide the same shortfall (×0.54), so it is not
an Arunachal quirk.

**Diagnosis (post-hoc, so diagnostics, not a pass):**
- **The drift is in the flood record, not the rain.** Same test with
  satellite rain instead of live-archive rain: recorded ÷ forecast by year
  2016–19 0.65–0.95, 2020–23 0.7–1.4, **2024 ≈ 2.0, 2025 1.6–2.0** — both
  rain sources alike (satellite: 0.74, 0.76, 0.81, 0.79, 1.30, 0.72, 1.43,
  0.96, 1.97, 1.62 for 2016→2025). Arunachal records per year: 27, 35, 21, 29, 58,
  24, 65, 33, 72, 55 (2016→2025). The rain-based forecast stays roughly
  flat; the record roughly doubled in 2024–25. More reporting (the record
  is news-based) or genuinely worse years — this data cannot separate them.
- **A production-like routine** (re-fit the curves every year on the latest
  two years, forecast the next) brings the totals within bounds (A1 0.76
  day, 0.69 week) but **still fails A2**: low-chance places flood 1.5–3×
  more often than said, higher ranges ~2× less often than said — the
  forecast is too sure of its own ranking from one year to the next.
- The record's own place-and-month frequencies beat the forecast slightly
  on Brier (−0.006 day, −0.034 week): where floods get *reported* persists
  year to year, which a physical rain + terrain model deliberately ignores
  (§0p).

**Decision point (open, 2026-09-27):** a single, stable "X% within 10 km
this week" that is right within 2× cannot be promised from news-based flood
records as they stand — their own rate moved 2× between recent years. The
ranking (AUC ~0.85) and the logical structure hold. Options put to the
user: show it as an *approximate* percentage fitted to the latest years
(2024–25) with the measured error stated, or hold it until a steadier truth
exists (Phase 8 evidence intake; gauges stay the checked forecast). Nothing
was wired into the daily run or the screen.

**Also found while setting this up:** the flood record ends Oct 2025 (17
records that month, 2 in Jan 2026, none after). The day model's production
calibration (2024–2026) and the earlier replays/source check (to
2026-07-29) counted Feb–Jul 2026 as flood-free. The new layers use truth
days only (to 2025-10-31); the day model itself is untouched — a refit is
proposed separately, not done.

### §0v continued — the decision, the retune, and what shipped (2026-09-27)

**User's decision:** show the near-here % as *approximate*, with its measured
error stated on screen; and retune the day model on record days only.

**Day model retuned** (`flood_forecast.py fit`, `TRUTH_END = 2025-10-31`):
calibration 2024-01-01 → 2025-10-31 (was 2024-01-01 → 2026-07-29): 1,227,440
rows / 619 flood cell-days (was 1,723,912 / 621 — the same floods, minus
~500k unrecorded days counted as dry). Valley factors re-fitted on record days:
flat 0.426, hilly 0.098, steep 0.139 (were 0.490 / 0.114 / 0.167). On the
golden live day (2026-09-27, same inputs): day-model chances ×1.41 median,
"× normal" ×1.04, expected flooded km² ×1.16; the 32 river forecasts
unchanged. Old files: session scratchpad `flood_forecast_models_pre_retune/`.

**Tests re-run on record days only:**
- Live source check (`flood_forecast_live.py build`): 1,035 days, 150 floods
  in Arunachal; fair timing satellite 0.736, **shipped path (satellite-fitted,
  live rain) 0.706** (was 0.716 with the unrecorded 2026 days), live-fitted
  0.648.
- Replay (`--upstream --train-clean --test-clean`, now to 2025-10-31): right
  day AUC 0.950 (Arunachal 0.883), timing-only 0.845; **expected 619 vs
  observed 945 floods (Arunachal 104 vs 150)** — see the §0p correction below;
  right place unchanged (Arunachal AUC 0.937; given a flood 20,393 vs 7,980
  patches); together after the valley factor 306k vs 363k patch-days,
  Arunachal 25.7k vs 7.6k (×3.4).

**⚠️ Correction to §0p's "the flood count is right — 115 expected, 119
reported":** that match came from the unrecorded Feb–Jul 2026 days, which
added expected floods with no chance of an observed one. On record days only
it is **104 expected vs 150 recorded** in Arunachal (and 619 vs 945 region-
wide) with the replay's 2021–22 calibration — the same year-to-year drift the
near-here test found. §0p's other findings (where floods land; WHERE ~2.6×
generous given a flood in the mountains) stand.

**Near-here, production** (`near_here.py fit`, on the retuned model, curves
2024-01-01 → 2025-10-31): wired into the daily run, the report
(`near_here` block), the web snapshot and the track record
(`records/flood_forecast/near_here/<issue>.npz` + `near_here_state.csv`,
from the next scheduled run). Golden check after wiring: 0 changed, 2 added.
Sanity: the week from 30 Jun 2024 → Arunachal-wide "over 95%", top place
56%; the week from 15 Jan 2024 → places ~0.01%. First live issue (week from
27 Sep 2026): Arunachal-wide 21%; highest places ~2.4% (Siang–Dibang, 21–23
flood days on record nearby).

**Measured error shown on screen** (production-like test — curves re-fitted
each year on the latest two years, as production is; post-hoc): per chance
range, recorded ÷ forecast between **0.42 and 3.06**; ranking AUC 0.86.

**Confidence (Gate C′, pre-registered before grading):** evidence = distinct
flood days on record within 10 km. Levels from records ≤2022, graded weekly
2023–25: High (≥3 days, 62 places) forecast ÷ recorded 0.34, AUC 0.738;
Medium (1–2, 107) 0.62, AUC 0.739; Low (0, 582) 1.25, AUC 0.752 — 64 floods
happened in "no record" places. High does not beat Medium → **merged**. The
premise "more records nearby = more accurate" did not hold: ranking is about
the same everywhere; what differs is the level — where floods are often
recorded, more get recorded than the physical model expects. Production-like,
two levels: **on record ×1.72 recorded ÷ forecast (AUC 0.78); none on record
×0.79 (AUC 0.82)** — shown on screen with each place's count.

## 0w. The rest of the screen plan, and a finding about the flood record itself — 2026-09-27

Plan: [FLOOD_SCREEN_PLAN.md](FLOOD_SCREEN_PLAN.md) Phases 3, 5, 7, 8, 9.

### ⚠️ The Sentinel-1 "confirmation" filters out almost nothing

`fetch_32`'s Earth Engine screen (new water within ~17 km, radar pass
within ±3 days, vs a dry-season image from the same orbit; positive above
0.3%) confirmed most of the flood records every model here trains on
(§0b rows 7–8: ~2,800 of ~3,100). It was validated only on 4 real floods
(§5i — sensitivity). It was never run on flood-free dates. Tested
2026-09-27 (`scripts/model/check_s1_screen_specificity.py` →
`reports/flood_s1_screen_specificity.json`): 40 screen-positive records,
each re-checked on its own date and on flood-free control dates at the same
place (no record within 20 km / 30 days):

| | n | median new water | 95th pct | "positive" at 0.3% |
|---|---|---|---|---|
| flood date | 40 | 5.6% | 12.0% | 100% |
| same season, a year apart | 19 | 3.1% | 11.0% | **100%** |
| mid-January (dry) | 33 | 2.7% | 5.1% | **97%** |

- **At 0.3% the screen passes nearly every flood-free date.** Flood dates do
  carry about twice the "new water" of controls, so there is real signal,
  but the ranges overlap: only 20% of the sampled records (30% of all
  screen-positive records) clear the controls' 95th percentile (9.2%).
- **A same-place test does not rescue it:** a flood date beat every
  same-place control 66% of the time, against a 33–50% chance level with 1–2
  controls; "at least 2× the place's usual" caught 49% of floods and 47% of
  flood-free controls.
- Also found: `fetch_32` caches ONE dry-season baseline per orbit for the
  whole batch, whichever place asked first — it need not cover later places.
  The new code clears it per place; the historical screen was not re-run.

**What this means, and what it does not:**
- The flood record is, in effect, **news-reported floods (Groundsource) that
  happened to have a radar pass near the date** — not "satellite-confirmed".
  Every model's truth, every test and every calibration here is about
  *reported* floods. That was always the event (§0l); the satellite step
  just added less than the wording claimed.
- WHERE's pixel labels (new water in the crops around each report) carry
  the same noise (~3% of ground reads as "new water" on a quiet day), yet
  WHERE's map passes every physical check and ranks held-out flooded ground
  at 0.86 in Arunachal — real flood water is concentrated where the noise is
  not. Its absolute level inherits the noise; not quantified.
- **Not rebuilt.** Re-deriving the truth with a real water test (speckle
  filtering, multiple references, HAND masking) and retraining is a
  project, not a fix — recorded as the next research step, not attempted.
- Wording corrected on every screen and in the model metadata: "reported
  floods", "radar images showed new water around them", never "confirmed by
  satellite".

### Phase 3 — the "if a flood comes" top ranges: Gate B FAILED, not applied

`scripts/model/check_where_topend.py` (pre-registered in the plan): a
second calibration step by terrain setting (open plain vs valley, 50 m of
relief within ~2 km), cross-fitted over WHERE's 5 spatial folds.
Report: `reports/flood_where_topend_check.json`.

| inside Arunachal | said | happened |
|---|---|---|
| before, 10–20% | 14.9% | 5.8% |
| after, 10–20% | 16.0% | 5.3% |
| before, 20%+ | 26.3% | 17.2% |
| after, 20%+ | 31.1% | 19.9% |

By fold and year block the top ranges swing from ×0.04 to ×1.04 (2019–21
matched; 2015–18 ×0.14; 2022–25 ×0.35); outside Arunachal the calibration
error got worse (0.015 → 0.039); physical checks passed. **Reason: how much
ground a flood covers varies too much from one flood to the next for any
fixed correction.** Per the plan's fallback: the model's number stays, shown
capped at "20%+", with the checked rate for its range beside it.

### Phase 5 — the gauge on a place's own river, and its graph

- `scripts/build/build_gauge_link.py` (+ `--selftest`, 7 toy cases): a
  gauge is "on this river" when the place's nearest channel (trunk if within
  25 m above it, else small) and the gauge share a flow path, the river is
  within ×0.5–×2 of the gauge's drainage area, and within 60 km along it.
  The toy test caught a real bug first: below a confluence the nearest
  upstream gauge was the tributary's, which the size rule then rejected,
  hiding the main river's gauge — fixed by checking size during the walk.
  Result: 29.9% of the state's floodable 100 m cells sit on a gauged river;
  30 of 32 gauges own some ground (Ziro's gauge is on a stream below the 10
  km² network; the NWDP Miao gauge's stream has no floodable ground).
  Spot checks: Pasighat → Passighat (1 km downstream), Seppa → Seppa,
  Bhalukpong, Daporijo, Aalo, Tuting, Doimukh, Yingkiong → their own gauges;
  Tezu → none (Kibithu is >60 km up the Lohit), Ziro, Tawang, Roing → none.
- `scripts/build/build_gauge_levels.py`: CWC's published warning, danger and
  highest-ever levels (13 gauges) + the model's own line and typical level.
- The daily run fetches 30 days of readings per gauge for the graph by a
  **separate display-only call** (`flood_gauge_live.history`), so the
  forecast's 8-day window is untouched. NWDP's feed genuinely skips days;
  the graph draws each run of reported days as its own segment.
- Screen: "River gauge on this river" or "none — the nearest one is on a
  different river"; the graph below the map (last 30 days, Now, lines,
  chance bars; no level forecast drawn).

### Phases 7–8 — new records and grading

- `scripts/model/flood_intake.py`: records from **river gauges crossing
  their lines** (one per episode, dated to its peak) and **people's
  reports** (the app's "Seen a flood? Report it" form, shown only where
  reports can actually be kept). Given the finding above, the radar is looked
  at (new water %, scene date) as **information only**, never as a
  confirmation. News feeds are not built: turning a story into a place
  precise enough needs village-level place reading. Test: `flood_intake.py
  test` (offline).
- `forecast_log.verify_area`: grades the logged near-here chances against
  the new records — **ranking only** (a week with no record is not proven
  dry). Tested on synthetic data.
- Both run in the daily job (log path only), wrapped so neither can stop
  the forecast. Today: 0 records, 0 graded — the monsoon is ending.

### Phase 9 — "How to read this forecast"

The ℹ️ popover's page, replacing the old rule-based "Method & limits".
Every figure is read from the daily snapshot's new `method` block (built by
`flood_forecast_live.method_facts()` from the test reports), `floodprob.json`
and the gauge assets — nothing typed.

## 0x. A radar water test that can say "no" — and the re-check of every record — 2026-09-28

**Why:** §0w — the screen that "confirmed" ~2,800 records passes 97–100% of
flood-free dates. The user's instruction: fix it.

**The new test** (`scripts/fetch/radar_water_test.py`), one place and date:
- the radar pass nearest the date, within ±3 days (Sentinel-1 VV, as before);
- a REFERENCE built from up to 15 dry-season passes (Dec–Mar) of the SAME
  track, within two years — the median, not one image;
- speckle smoothed (50 m median) on the flood image;
- only low, flat, normally-dry ground counts: MERIT height above the nearest
  drainage < 15 m, slope < 5°, JRC permanent-water occurrence < 50%;
- a 30 m pixel is NEW WATER only if it reads as water on the date (< −18 dB),
  was not water in the reference (≥ −18 dB), and dropped by more than 3 dB;
- measured: the share of that low ground within 10 km that became new water.

**Pre-registered, fixed before any result (validation):**
- 80 records drawn at random (fixed seed) from the screen-positive list, each
  also tested on flood-free control dates at the same place (same season a
  year apart; mid-January), no record within 20 km / 30 days.
- Places split at random into half A and half B. The threshold is set on
  half A only: the 97.5th percentile of A's control dates.
- **Pass, on half B:** at most 10% of control dates above the threshold
  (specificity ≥ 90%), AND flood dates above it at least 3× as often as
  control dates.
- If it passes: re-check every screened candidate with it and publish which
  records the radar supports. If it fails: say so; the records stay
  "reported, not radar-confirmed".

**Attempt 1 result (2026-09-28): FAILED, narrowly** (`reports/flood_radar_test_validation.json`).
Threshold from half A: 2.14% of low ground. Half B: specificity 0.897 (needed
0.90); flood dates above it 27.5% vs controls 10.3% (2.7×, needed 3×). But the
separation is far better than the old screen: median new-water share on flood
dates 0.83% vs 0.046% on dry-season controls (old screen: 5.6% vs 2.7%).
Same-season controls (monsoon dates a year apart, no record) sit at 0.15%,
p95 6.9% — the dry-season reference reads a normal wet monsoon day as new water.

**Attempt 2, pre-registered before running (2026-09-28):** one change — a
pixel counts as new water only if it is ALSO not water on an ordinary day of
the same season: a second reference, the median of up to 15 passes of the same
track within ±30 days of the same day of year in the three years either side
(the event's own year excluded); at least 3 needed. Everything else, the
controls and the pass marks unchanged. Validated on a FRESH sample: 80
records drawn with seed 7 from the ones attempt 1 did not use.

**Attempt 2 result (2026-09-28): PASSED** (`reports/flood_radar_test_validation.json`;
attempt 1 kept as `..._attempt1.json`). Fresh 80 records, 182 tests (161
measured; 20 had no radar pass within 3 days). Threshold from half A: **1.27%**
of the low, flat, normally-dry ground within 10 km. Half B: **specificity 0.978**
(1 of 45 flood-free dates above), flood dates above it **35%** — 16× the control
rate. Medians: flood dates 0.52%, dry controls 0.03%, same-season controls
0.065% (p95 0.85% — the monsoon false alarms are gone).

Reading: a record the test supports is now genuinely radar-confirmed. A record
it does not support is NOT disproved — the water may have drained before a pass
(every 6–12 days), the flood may have been small against 10 km of low ground,
or the report's place/date may be off. Next: re-check every candidate.

**Full re-check (2026-09-28)** — `reports/flood_radar_recheck.json`: all 4,586
screened candidates. Radar supports 1,198; does not show 2,367; no pass within
3 days 1,016; too few references 5. Of the old screen's positives: supported 996
(36%), not shown 1,794.

**The verified record** — `scripts/build/build_verified_floods.py` →
`data/interim/flood_events/verified_events.parquet`, `reports/flood_verified_record.json`:
2,185 events confirmed by at least one independent route (radar 1,153; Global
Flood Database 1,016; gauge cross-check 59; gauge-found floods with our own
radar 71; channel-shift suspects excluded; same place-day merged). Of the 3,331
reported records the models trained on, 1,302 (39%) are verified; 883 verified
events were not in that training list at all (the gauge-found floods among them).
Verified events per year are far steadier than reports (2022–25: 186, 163,
178, 104 vs 419, 435, 450, 340).

**Pre-registered before running (2026-09-28):** Gate A (FLOOD_SCREEN_PLAN.md
Phase 2), unchanged in every respect — same models' design, years, radius,
curves, pass marks — re-run with the VERIFIED record as the truth everywhere
(training the test day model, fitting the curves, grading). Report:
`reports/flood_near_here_check_verified.json`.

**Gate A re-run on the verified record** (`reports/flood_near_here_check_verified.json`):
still FAILS on level (week ×0.46; 2023 about right, 2024–25 2–3× more verified
floods than forecast — plausibly the second Sentinel-1 satellite from 2025
photographing more floods), but everything else improved: week ranking AUC
0.876 (reported truth 0.858), timing within each place 0.747 (0.624), and it
now BEATS the record's own place-and-month rate (Brier +0.095; reported −0.034).

**Train on which record?** (`reports/flood_near_here_train_on_which.json`,
both graded on verified floods, test day model tree 2015–20 / cal 2021–22):
trained on reported — Arunachal ranking 0.871, timing 0.726; region timing
0.715. Trained on verified — 0.876, **0.747**; region **0.758**. → switch.

**WHERE on verified events only** (`models/flood_where_verified`,
`reports/flood_where_verified_compare.json`, same folds, same verified rows):
Arunachal AUC 0.872 vs 0.868 (reported-trained), steep 0.654 vs 0.675,
calibration worse (top range says 29%, 11.7% happen). Not better — 1,081
events instead of 2,806 and the same old pixel masks. **WHERE stays trained on
the reported record** (its labels are water pixels, not the event dates).

**Switched to the verified record (2026-09-28)** — `flood_forecast.TRAIN_RECORD
= "verified"`, `training_events()`; `near_here.TRUTH = "verified"`:
- day model refit (tree 2015–23: 1,187 flood cell-days; calibration 2024–
  Oct 2025: 207); valley factors re-fit with the expected side scaled to the
  share of events that have water maps (flat 1.028, hilly 0.167, steep 0.025 —
  internal only; "× normal" and km² are not shown on screen).
- live source check, graded on verified floods (44 in Arunachal, 2023–25):
  **fair timing 0.845** for the shipped path (satellite-fitted, live rain) —
  was 0.706 against reported floods. Satellite rain 0.835; live-fitted 0.753.
- near-here production curves refit on verified (2024–Oct 2025). Production-like
  measured error: week ranking AUC 0.893, recorded ÷ forecast by range as the
  screen quotes it; evidence levels (Gate C′ again merged): on record ×1.62,
  none on record ×2.11 — both now under-forecast.
- golden check: river forecasts 0 changes; day-model chances ×0.36 median
  (fewer, real events); screen snapshot refreshed. Old models backed up in the
  session scratchpad (`flood_forecast_models_pre_verified/`).
- The historical replay (`replay_flood_forecast.py`) still grades the reported
  record — it is the record of that study, left as is.

## 0y. Soil wetness and 15/30-day rain in the day model — 2026-09-28

Full pre-registration and results: [SOIL_WETNESS_TEST.md](SOIL_WETNESS_TEST.md).

- **Soil wetness across all terrain: fails.** It helps on the plains and hurts on
  steep ground, where floods are flash floods.
- **Soil wetness on flat cells only (<5°): passes** on fresh years (2015–18),
  flat-cell timing +0.017. It also holds with a 16-day-old reading, which the
  live run can always get: flat +0.0095, Arunachal +0.019.
- **15/30-day rain: unstable** (helped 2023–25, hurt 2015–18), dropped.
- **Wired into production 2026-09-28** (user-approved): flat cells use the soil model (`FlatSoilDayModel`), the daily run fetches soil from Earth Engine, and near-here was re-measured. SOIL_WETNESS_TEST.md §10.

## 0z. Floods before 2015 — counted, and learned from — 2026-09-29

Full pre-registration, results and wiring: [OLDER_FLOODS_TEST.md](OLDER_FLOODS_TEST.md).

- **Why the forecast started in 2015:** the first flood list (news reports plus a
  radar screen) started 2015-06-03, when regular Sentinel-1 coverage began. The
  verified record (§0x) added 326 floods from 2003–2014 (39 in Arunachal), which
  the Global Flood Database confirmed. Neither the screen nor training used them.
- **Fix 1:** the "floods on record" count now starts in 2003. Its check passed;
  no forecast number changed.
- **Test 2** (pre-registered): tree from 2003 passed all four gates; from 2010
  failed the near-here gate. Timing +0.020 across the window, +0.028 in
  Arunachal, even though the old record is very incomplete (0% of the wettest
  1% of monsoon cell-days carry a verified flood in 2003–08).
- **Wired into production 2026-09-29** (user-approved) via
  `flood_forecast.TREE_FROM`:
  - live timing in Arunachal 0.851 → 0.879; near-here ranking 0.893 → 0.890;
  - river forecasts unchanged;
  - the screen's error wording now also reports the high ranges saying more
    than happened.
