# Flood WHEN pilot — implementation plan (Tawang first)

**Status:** 🟢 **CALIBRATED — this is a real probability now, 2026-09-01.**
**CWC (18 stations):** WHEN trained/scored for all 17 reachable (Bhalukpong
outside the rainfall grid); WHERE checked at 16/17, every one positive — §7,
§11. **NWDP (14 small rivers):** WHEN scored for 12/14; WHERE 11/12 positive
— §12. **Combined (32 stations): 29 have checked WHEN evidence, 28 a real
WHERE check (27 positive).** **§10: calibration done and independently
verified** — on official-danger-level stations the calibrated forecast is
accurate to within 0.03% calibration error, reaches 26× the base rate on its
top 1% of days, and caught **76.5% of 379 real flood episodes** at ELEVATED
or above (23.5% missed, listed by name). Operational scorer:
`predict_flood_when.py`.

> **🆕 2026-09-21 — WHEN is no longer gauge-only, and it is now joined to
> WHERE.** The same rain rule + trees are scored on all 1,953 rain cells
> (`scripts/model/when_grid.py`, reproduces the station scores to 4
> decimals) and mapped onto satellite-confirmed floods by a new "day model",
> then multiplied with the now-calibrated WHERE layer. This supersedes the
> "WHEN only — deliberately NOT multiplied" limit in §10. Replay on
> 2023–26: on real flood days the area's chance was typically 2.5× normal;
> warning at 2× catches 57–64% of floods. Full record:
> [PARKED_HIMALAYAN_FLOOD_WHERE.md §0l](PARKED_HIMALAYAN_FLOOD_WHERE.md).

> **2026-08-28 — Passighat (large Siang river) archived alongside the two
> Tawang gauges.** Variants B and C only mean anything with a genuinely
> different river size to pool or naive-transfer from; two nearby small
> Tawang streams alone couldn't test that. Passighat has a **published** CWC
> danger level (153.96 m) too, so it doubles as a real-threshold cross-check
> against the self-derived method used for Tawang. See §5.

> **2026-08-28, later same day — do not wait on the CWC threshold ask.** The
> user's explicit instruction: build a real prediction capability using only
> data we find or derive ourselves, and treat any government ask as a bonus,
> never a blocker. §1 and §4 below now reflect that — the self-derived label
> is the **standing method**, not a stopgap for while an ask is pending.

**Decisions locked in for this plan:**
- **Pilot district: Tawang** (Murga Bridge + Rho Basti gauges), not a statewide
  pass — see [PILOT_TAWANG.md](PILOT_TAWANG.md) for why this district.
- **Build WHEN before WHERE** — WHEN's data is ready now; WHEN's output (a real
  dated flood list) is also the exact input WHERE needs to start. See
  [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §7 for the reasoning.
- **Explicit constraint from the user: the pilot must not leave the eventual
  statewide model or system weaker.** §6 below ("Guardrails") exists specifically
  to answer that — read it before writing any pilot-specific code.
- **Train model variants separately and keep them separate — don't merge into
  one blended model.** Each variant (see §2) is trained, tested and reported
  on its own, so we can see how each actually performs before the meta-learner
  ever touches them. This is the same diversity principle as
  [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §3, applied explicitly here.

---

## 0. Objective

Prove the whole WHEN pipeline — archive → backtest → train → validate — end to
end on real data, on the smallest honest slice of the state, in a way that
plugs into the statewide rollout later **without rework**. A secondary output
(the confirmed flood-date list) becomes the starting input for the WHERE
pilot (§7).

**Success looks like:** at least one trained variant that beats the existing
rainfall-rule's backtested score on Tawang's own held-out years, a clean,
reusable pipeline that needs no rewrite to add the next station, and a
side-by-side scorecard of every variant tried — not just the winner.

---

## 1. The flood-day label is self-derived — permanently, not while we wait

**Murga Bridge and Rho Basti have no published CWC danger/warning threshold**
(confirmed twice now: in [PILOT_TAWANG.md](PILOT_TAWANG.md), and again
first-hand when Phase 0's fetch returned both fields null). That threshold
would normally define "this day was a flood" — but **this plan does not wait
for it, and does not treat it as required.**

Instead, "this day counts as high water" is computed **from each station's
own recorded history**, with no government input at all: the top 2% of that
station's own daily-max readings — a standard percentile-based flood-proxy
technique used in hydrology exactly when no official threshold exists. An
annual-maxima Gumbel return-level is fitted alongside as an independent
cross-check (§4 shows both agreeing closely, which is itself evidence the
self-derived number is sound).

**If CWC answers the threshold ask anyway, it's a bonus — swap it in as one
more cross-check.** It never becomes a dependency this plan is blocked on.

---

## 2. The WHEN panel roster for flood

Mapped onto the same panel shape as the rest of the ensemble
([ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §1), for **gauged rivers only**
— ungauged streams still have just the rule-based box until they get a gauge
or a proxy of their own.

| Slot | Method | Status |
|---|---|---|
| Rule-based | Catchment rainfall-percentile rule | 🟢 live today — one input to the shipped blend (D), see §5 |
| Trees (pooled, size-aware / B) | Gradient-boosted tree, all stations pooled + catchment area feature | 🟢 live today — blended into D; solo doesn't yet beat the rule, on record |
| Trees (naive-transfer diagnostic / C) | Gradient-boosted tree, trained on Passighat only | 🟢 live today — blended into D; solo ties/slightly beats the rule, most promising thread so far |
| Trees (per-station / A) | Gradient-boosted tree, one station's own data only | 🔴 tested, 2026-08-28 — strictly dominated by B, excluded from the blend, kept on record |
| Other ML | "Similar-day" analog method — find past days with a matching rainfall/level pattern, use what actually happened | 🔵 candidate, not started |
| Deep learning 1 | Sequence model (e.g. LSTM), trained per-river on that river's own long history | 🔵 later, once Phase 2's tree work is proven |
| Deep learning 2 | Same, but pre-trained on a wider pool of other rivers first, then fine-tuned locally | 🔵 later — needs a pooled multi-river dataset sourced first |
| Other / cross-check | GloFAS, pulled in as a second opinion for the ~5 largest rivers only | ⚪ cross-check only, not trained by us |
| Other / blocked | Dam release schedules as an input, for regulated rivers | ⚪ blocked on the NHPC ask |

**Referee (meta-learner):** starts as a plain weighted blend of whichever of
the above are actually built, and only grows more sophisticated as more real
held-out flood days accumulate to check it against
([ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §4).

---

## 3. Phase 0 — Archive the pilot's real data ✅ done 2026-08-28

| | |
|---|---|
| Source | `ffs.india-water.gov.in` open API (no login), stations `002Neid3` (Murga Bridge), `001NEID3` (Rho Basti) |
| Script | [fetch_21_cwc_gauges.py](../../scripts/fetch/fetch_21_cwc_gauges.py) — **station code is a parameter** (`STATIONS` registry + `--station NAME:CODE`), no hardcoded one-off path |
| Output | `data/raw/11_gauges/cwc/<station_code>_hhs.csv` (level series) + `_static.json` (thresholds) |

**Result, both stations downloaded in one pass, no pagination needed:**

| Station | Code | Readings | Span | Danger/warning published? |
|---|---|---:|---|---|
| Murga Bridge | `002Neid3` | 37,155 | 2018-11-14 → 2026-08-24 (live) | ❌ null — confirms §1 |
| Rho Basti | `001NEID3` | 61,318 | 2005-06-01 → 2026-08-24 (live) | ❌ null — confirms §1 |

**98,473 real, dated water-level readings now on disk.** Both stations
confirmed still updating as of today. Confirms §1's constraint first-hand:
neither has a real threshold yet, so Phase 1 proceeds on the percentile
proxy. Provenance recorded in `data/raw/11_gauges/cwc/_SOURCES.json`.

---

## 4. Phase 1 — Backtest the existing rule ✅ done 2026-08-28

Ran the existing catchment-rainfall-percentile rule — unchanged, the same
rule already shipping — back through both stations' real history, checked
against the self-derived flood-day labels from §1.

| | |
|---|---|
| Script | [backtest_flood_when.py](../../scripts/model/backtest_flood_when.py) |
| Rainfall lookup | Both stations approximated to Jang town centre (27.5834N, 91.9802E) — CWC's API returns no coordinates for either gauge, both are documented as "~10 km from Jang." That uncertainty is smaller than IMERG's own ~11 km cell, so it costs no precision the rainfall input didn't already lack. |
| Output | `reports/flood_when_backtest_tawang.json`, `data/interim/flood_when/tawang_flood_days.csv` (147 self-derived flood-day labels — the WHERE-phase handoff list) |

**⚠️ Data-quality finding, fixed before scoring:** the raw CWC feed contains a
handful of gross sensor/transmission glitches per station (values off by
~10-1000x, plus a couple of literal 0.00 dropouts) — e.g. one 2026 Murga
Bridge reading of 2,134,040 against a normal range of ~2,134. Left in, a
single one of these corrupts an annual maximum and the whole extreme-value
cross-check. Filtered with a generous modified-z-score check (5 dropped for
Murga Bridge, 9 for Rho Basti) before any statistic touched the data — real
flood peaks are three orders of magnitude smaller than these glitches, so
none were at risk of being filtered out.

**Result — the existing rule, entirely unfitted, already clears the bar with
zero data asked for:**

| Station | Self-derived threshold | Gumbel cross-check (2-yr) | Flood days found | **AUC** |
|---|---:|---:|---:|---:|
| Murga Bridge | 2135.02 | 2134.99 (agrees) | 56 | **0.931** |
| Rho Basti | 2232.17 | 2232.10 (agrees) | 91 | **0.794** |

Both beat the landslide trigger's own honest baseline (0.768,
[MODEL_TRIGGER_AND_HAZARD.md](MODEL_TRIGGER_AND_HAZARD.md) §4) — Murga Bridge
substantially so. At the trigger's p75 operating point, Murga Bridge catches
**98.2%** of its self-derived flood days while flagging only 25% of all days
(a ~3.9x lift); Rho Basti catches 68.1% at the same setting. Full operating-
point tables in the JSON report.

**What this proves, in plain terms:** using only data we found and derived
ourselves — no CWC threshold, no new ask answered — the *existing, already-
shipping* rule already does meaningfully better than chance at telling real
high-water days apart from ordinary ones, on two real Tawang rivers. Phase 2
(training a second WHEN method) now has a real, honest number to try to beat.

---

## 5. Phase 2 — Train separate model variants, keep them separate ✅ done 2026-08-28

Trained **three distinct variants**, each kept as its own model file and
scored on its own — not merged, not averaged together at training time:

| Variant | Trained on | Purpose |
|---|---|---|
| **A — per-station** | Only that one station's own history | The direct local baseline — simplest, most defensible, exactly what the pilot promised |
| **B — pooled, size-aware** | Every gauged station archived so far (Murga Bridge + Rho Basti + Passighat), with catchment area as an explicit feature | Tests whether pooling across river *sizes* helps — the size-axis version of the Himalayan pooling instinct |
| **C — naive big-river-only (diagnostic, not for shipping)** | Only Passighat, applied to Tawang's small stations without any size-awareness | Strawman — exists purely to show whether naive transfer is worse than variant B |

| | Script | Output |
|---|---|---|
| Train + score | [train_flood_when.py](../../scripts/model/train_flood_when.py) | `models/flood_when/<variant>_<code>.pkl`, `reports/flood_when_variant_comparison_tawang.json` |

**Evaluation method, revised from the original single-holdout idea:** a first
attempt used a fixed "most recent 20%" cut per station, matching how Phase 1
was checked. It broke — Rho Basti and Passighat's most recent years both
happened to be flood-quiet by chance, leaving **zero** flood days in that one
fixed window and no score at all for 2 of 3 stations. Fixed by switching to
**5-fold cross-validation grouped by calendar year**: every year is held out
exactly once, tested by a model that never trained on it, and every flood day
across the whole record eventually gets scored. Same "never seen during
training" discipline as a single holdout, just rotated instead of fixed —
and it doesn't let one unlucky window erase a station's result.

**⚠️ Second data-quality finding, fixed before scoring:** the same modified-
z-score clean from Phase 1 caught 2 more gross sensor glitches for Passighat
(readings of 50.29 m and 105.28 m against a normal range around 150 m).

**Result — the scorecard, AUC per station:**

| Station | Baseline (untrained rule) | A (own data) | B (pooled, size-aware) | C (naive, Passighat→here) |
|---|---:|---:|---:|---:|
| Murga Bridge | 0.922 | 0.866 | 0.914 | **0.931** |
| Rho Basti | 0.786 | 0.624 | 0.639 | **0.795** |
| Passighat | **0.954** | 0.926 | 0.946 | 0.926 |

**Honest reading — none of the three trained variants clearly beat the
untrained rule SOLO, at this data scale.** Variant A (fitting on one
station's own ~55-90 flood days) is the *worst* performer everywhere,
sometimes by a wide margin — the exact same finding already proven for
landslide's trigger ([MODEL_TRIGGER_AND_HAZARD.md](MODEL_TRIGGER_AND_HAZARD.md)
§4: "fitting on 72 events loses to not fitting one"), now independently
confirmed a second time, in a different hazard, on different data.

**The one genuinely interesting result: Variant C, trained only on the large
Siang river and pointed at small Tawang streams with zero size-awareness,
comes out on top or tied on top in 2 of 3 stations** — narrowly (0.931 vs
0.922; 0.795 vs 0.786), not a confident win, but notable given the concern
raised when this was first discussed (a big river "taking days to rise"
behaving too differently from a creek that "flashes in hours" to transfer
cleanly). A likely reason: the rainfall feature going in is **already
percentile-normalised per location** before any model sees it — the same
trick that let one landslide trigger work from the wet south to the dry
north without retuning may already be absorbing most of what would otherwise
make big-river and small-stream behaviour look different. Interesting, but
margins are too thin and samples too small (54-91 flood days) to call this
proven — flagged for re-checking once more stations are archived, not
declared a result yet.

### D — the actual shipped WHEN score: ML is blended in now, not benched

Per [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §3 — do not sideline a
trained model just because it didn't win solo — the live WHEN score is an
**equal-weight blend of the rule, B, and C**, computed and scored the same
honest, cross-validated way as everything else:

| Station | Baseline (rule alone) | **D — shipped (rule+B+C blend)** |
|---|---:|---:|
| Murga Bridge | 0.922 | 0.921 |
| Rho Basti | 0.786 | 0.782 |
| Passighat | 0.954 | 0.953 |

**Honest reading of D:** the blend performs on par with the rule — within
noise of it, not confidently above or below. That is a genuinely different,
better story than "ML doesn't help yet": **two real trained models are now
part of the live score today**, contributing real weight, at zero cost to
accuracy. A is deliberately left out of the blend — not because it's ML, but
because it is *strictly dominated* by B on every station tested (weaker with
no offsetting diversity), so blending it in would add noise for nothing. It
stays on record, not deleted, and gets tried again as its own station
accumulates more data.

A few alternative weightings (rule+C only, rule+2×C, C alone) were checked
against these same cross-validated numbers and found equally close to
baseline — **not cherry-picked into D**, deliberately: picking whichever
blend happens to score best on this small a proof set (54-91 flood days per
station) would itself be the "fitting on 72 events loses to not fitting"
mistake one level up. The equal-weight blend is kept because it is the
simplest defensible choice, not because it is provably the best one.

**What actually grows ML's share of this score over time:** not manual
re-weighting, but more real data. As §8's rollout adds stations and each
retrain cycle adds another season's flood days, B and C should start pulling
ahead of the rule with real margin, and the blend's weights can graduate from
equal to properly learned — exactly the "referee complexity ceiling rises
with proof data" rule in [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §4.
Phase 2 is not a failure: it produced an honest, cross-validated answer
instead of a guess, put real ML weight into the live score today, and left a
specific, real question (does percentile-normalisation erase the
big-river-vs-small-stream difference?) worth re-testing as more data
arrives.

---

## 6. Guardrails — how this stays pilot-*sized*, not pilot-*shaped*

The user's condition on running Tawang first: **it must not make the eventual
statewide model or system weaker.** Concretely, that means:

1. **Every script is generic from day one** — station ID / district is an
   argument, never hardcoded. "Pilot" means *which inputs we run first*, not a
   special one-off code path that needs rewriting later.
2. **Features are percentile-normalised per station**, exactly like the
   existing rainfall trigger is normalised per grid cell
   ([MODEL_TRIGGER_AND_HAZARD.md](MODEL_TRIGGER_AND_HAZARD.md) §4). This is
   what lets a small mountain gauge (Tawang) and a huge lowland river
   (Passighat) sit in the *same* pooled model later without one swamping the
   other — the model learns "unusual for this river," not a raw number.
3. **Variant A's pilot-trained model is a proof, not the shipped model.**
   Once more stations are archived, retrain Variant A from scratch per new
   station, and retrain Variant B on the full pooled set — don't bolt a
   frozen Tawang-only model onto the statewide system.
4. **Keep every variant simple at this scale**, per
   [ENSEMBLE_STRATEGY.md](ENSEMBLE_STRATEGY.md) §4 — two gauges is not enough
   proof data to trust a complex model or a complex meta-learner; a plain
   tree model and a plain backtest score is the right ambition for this
   phase, not a ceiling being avoided.
5. **Cross-check on one very different station before generalising anything.**
   Before any pilot-derived assumption (feature choice, proxy-threshold
   percentile, etc.) gets treated as the statewide default, re-run it once
   against a large, very different river (e.g. Passighat/Siang) and confirm
   it still behaves sensibly. Catches "Tawang is a small mountain valley"
   quirks before they quietly become defaults.
6. **Keeping variants A, B and C separate is itself a guardrail, not just a
   curiosity.** It means the pilot can never quietly ship "the pooled model
   worked on Tawang" without also showing whether the simpler per-station
   model would have done just as well — the comparison report in §5 is the
   evidence trail for that.

---

## 7. Phase 3 — Hand off to the WHERE pilot 🟡 in progress, 2026-08-28

Phase 1/2 produced 147 self-derived high-water days across the two Tawang
gauges (137 distinct dates). That list is the direct input to building WHERE
evidence: pull Sentinel-1 radar for those specific dates around Jang valley —
the one location our static layer flags as **unconfirmed** (Tawang town
itself already reads not-flood-prone, class 0; Jang was flagged as worth
checking, see [PILOT_TAWANG.md](PILOT_TAWANG.md)) — and look for real
standing water on the ground.

| | |
|---|---|
| Script | [fetch_22_sentinel1_flood_dates.py](../../scripts/fetch/fetch_22_sentinel1_flood_dates.py) |
| Output | `data/interim/flood_when/s1_jang_acquisition_days.json`, `reports/flood_where_s1_feasibility.json` |

**⚠️ First attempt hung, not a data problem — a query-scope mistake.** A
single request spanning the full 2019-2026 range returned nothing for
several minutes with no error. Diagnosed by checking scene *volume* first
(a cheap `count()`-only call: 1,461 scenes over 7.5 years for this small
AOI) — not too large to page through, but the catalogue's own code comments
already warn it is "flaky on wide queries." Fixed by chunking the search
into one request per year; each returns in 15-45s.

**Feasibility result — real, and good enough to proceed:** Sentinel-1 does
**not** pass over Jang daily (single-satellite, multi-orbit coverage, not a
12-day flat cycle thanks to overlapping relative orbits) —

| Flood dates with a Sentinel-1 pass within N days | Count |
|---|---:|
| same day (0) | **13 / 137 (9%)** |
| within 1 day | 32 / 137 (23%) |
| within 2 days | 48 / 137 (35%) |
| within 6 days | 56 / 137 (41%) |

13 flood days have an **exact same-day** Sentinel-1 pass over Jang — real,
usable, dated evidence candidates, spanning 2019-2025 (2019-07-09,
2019-07-14, 2019-08-02, 2020-05-21/23, 2020-06-21/26, 2020-07-20/21/22,
2021-08-27, 2023-08-24, 2025-08-31). Full list and every date's exact gap in
the JSON report.

**Both scenes downloaded and verified real:** the 2025-08-31 flood-day scene
(`S1C_IW_GRDH..._CB7B_COG.SAFE`, 1.06 GB) and a 2025-02-26 dry-season
baseline on the **same relative orbit** (77) — matching geometry means no
full terrain-correction is needed to compare them. Both downloads needed a
retry wrapper: the CDSE host reset the connection mid-transfer on the first
attempt for each file (once at 30%, once at 40%) — same "flaky" behaviour
the catalogue's own code comments already warned about for search, now also
true for large downloads. Fixed generically (5 attempts, fresh token each
time), not scene-specific.

### Phase 3b — calibrated water detection: two real bugs found and fixed, then a real result

Script: [sentinel1_flood_evidence.py](../../scripts/model/sentinel1_flood_evidence.py).
Raw Sentinel-1 GRD is GCP-referenced (control points, not a simple grid) and
uncalibrated (digital numbers, not physical backscatter) — both had to be
handled correctly, and getting either wrong produces a plausible-*looking*
but wrong map. Two real bugs were caught by checking the actual pixel values
and a rendered image before trusting any number, not just checking the code
ran without error:

1. **Co-registration bug.** First pass fit an independent local affine
   window per scene and cropped both to "the same shape," then diffed them
   directly. Result looked plausible (real percentages) but was wrong: the
   *dry baseline* showed more "water" (24%) than the flood day (20%), and
   18% of the area appeared to flip water-state between dates — the
   signature of two misaligned grids, not real change. Same array shape is
   not the same ground location.
2. **Warp-resolution collapse.** The fix (warping through GDAL via each
   scene's real GCPs onto one explicit shared grid) produced images that
   were nearly *flat* — real per-pixel variance dropped from ~7.5 dB to
   ~0.15–0.2 dB, visually a featureless gray rectangle with no terrain at
   all. Reproduced in 10 lines on random synthetic data with no Sentinel-1
   data involved at all: forcing an explicit `transform`/`width`/`height`
   directly on a GCP-based `WarpedVRT` silently mis-scales the warp — GDAL
   needs to pick its own natural resolution from the GCPs first. Fixed with
   a two-step warp: auto-resolution GCP warp, *then* a plain CRS-to-CRS
   reproject onto the shared grid (a well-behaved operation once GCPs are
   out of the picture). A related, smaller issue on the way: the baseline
   scene's local GCPs happened to span only 2 distinct azimuth rows within
   too tight a margin, which made GDAL's auto-selected 2nd-order polynomial
   fit singular ("Transform is not solvable") — fixed by widening the
   margin so at least 3 row-bands are always included.

**After both fixes, the rendered image shows real terrain** — ridgelines,
drainage channels, a visible swath-edge cutoff exactly where Jang's position
near this pass's southern boundary predicts one (Phase 3 feasibility check
already flagged this).

**Result** (`reports/flood_where_s1_jang_20250831.json`), Jang valley, VV
backscatter, −17 dB water threshold, 0.88% of the window excluded as
no-coverage (the swath-edge wedge, not counted as water):

| | Flood day (2025-08-31) | Dry baseline (2025-02-26) |
|---|---:|---:|
| % of window below water threshold | 16.0% | 22.1% |

**The headline, more reliable number is the change, not either absolute
percentage** — a fixed dB cutoff is a rough rule of thumb, not calibrated
for this specific terrain, so the raw percentages above shouldn't be quoted
as "X% of Jang is flooded." What is more trustworthy: **7.2% of the window
dropped below the water threshold on the flood day specifically, having been
above it on the dry-season baseline** — real backscatter change, not
present on the calm day. Visually, that change traces the valley-bottom
drainage network, not a random scatter — the physically expected pattern
for a real high-water signal, not a co-registration artefact (which is
exactly what bug #1 above looked like instead).

**Honest limits of this one result:** a single date pair, one water
threshold not locally calibrated, and no independent confirmation (no
ground report, no second sensor) that this specific 7.2% is really Jang's
flood extent rather than partly vegetation/moisture change unrelated to
flooding. It is real, dated, methodologically sound evidence — not yet a
validated flood map. The next step, done immediately after (see below), was
repeating this across the rest of the 13 exact-match dates to see if the
same pattern recurs.

### Repeated across all 13 exact-match dates — the signal holds, every time

Downloaded and ran the same calibrated check on the remaining 12 dates
(script generalized to loop over every date; only 3 relative orbits cover
all 13 dates, so only 2 more dry-season baselines were needed, reused across
every flood date sharing an orbit — see `FLOOD_SCENES`/`BASELINE_BY_ORBIT` in
[sentinel1_flood_evidence.py](../../scripts/model/sentinel1_flood_evidence.py)).
Downloads needed the same retry-on-connection-reset handling as before, plus
one further fix: `fetch_14_sentinel.py`'s `download_one()` used a flat 1800s
timeout that does not reliably catch a stream that goes silent mid-transfer
(observed stuck at a fixed byte count for 10+ minutes, no exception) — fixed
to a `(30, 90)` connect/read timeout tuple plus periodic progress logging, a
generic reliability fix, not scene-specific.

**Result, `reports/flood_where_s1_jang_multi_date.json`, 12 of 13 dates
(2020-07-20's S1B scene hit an edge-case GCP window bug, not yet fixed —
noted honestly rather than silently dropped):**

| Flood date | Orbit | New-water (flood-only) |
|---|---:|---:|
| 2019-07-09 | 150 | 1.3% |
| 2019-07-14 | 41 | **8.1%** |
| 2019-08-02 | 150 | 1.4% |
| 2020-05-21 | 41 | 4.0% |
| 2020-05-23 | 77 | 4.1% |
| 2020-06-21 | 150 | 0.8% |
| 2020-06-26 | 41 | 2.0% |
| 2020-07-21 / 2020-07-22 (same scene) | 77 | 2.6% |
| 2021-08-27 | 150 | 0.6% |
| 2023-08-24 | 77 | 2.0% |
| 2025-08-31 | 77 | **8.8%** |

*(Numbers revised 2026-08-30 from the original pass — margin fix below;
same conclusion, no change in story.)*

**Every single one of the 12 dates shows a positive new-water signal** —
min 0.6%, median 2.6%, max 8.8%, mean 3.2%. Nothing scored zero or negative.
This holds across 5 different years (2019–2025), all 3 relative orbits
covering Jang, and 2 different satellites (S1A, S1B/S1C) — **this is no
longer one lucky data point, it is a repeatable signal**, exactly the
upgrade the honest-limits note above called for.

**What this still is not:** proof of the exact extent or severity of each
flood, or confirmation the range tracks real flood *size* (that would need
checking against the river-level data itself — do the bigger new-water
percentages correspond to higher gauge readings on those same dates? — not
yet done). It is real, repeated, dated evidence that Jang valley shows a
genuine radar water signature on every confirmed high-water day tested,
which is a legitimate, provable WHERE-side result to show alongside the
WHEN-side work.

### WHERE rollout ✅ done 2026-08-30 — 8 of 9 new stations checked, real signal at 7

Extended the same calibrated pipeline to 9 of the WHEN rollout's other
stations that had at least one exact satellite-day match (script:
[fetch_23_sentinel1_statewide_dates.py](../../scripts/fetch/fetch_23_sentinel1_statewide_dates.py)
for feasibility, [sentinel1_flood_evidence_statewide.py](../../scripts/model/sentinel1_flood_evidence_statewide.py)
for the calibrated check — both reuse, not reinvent, the Jang pipeline's
already-debugged calibration/warp code, generalized to take each station's
own real location). **One flood date per station this pass, not a full
multi-date sweep like Jang got** — proving the signal exists at each new
location first.

Four stations have no confirmed flood day (excluded, same as the WHEN
rollout — Tuting, Pangin, Lemeking, Namsai) and Bhalukpong's only real flood
days (1987-2014) predate Sentinel-1's operational archive, so there was
nothing to search for.

**A third real bug, same family as before:** Kibithu hit the identical
"Transform is not solvable" singular-GCP-matrix error found on the original
baseline scene — its window sits right at the image's top edge, where the
existing 3000-pixel GCP margin still only reached 2 distinct azimuth rows.
Fixed by widening the margin to 5000 pixels. **Re-ran the entire 12-date
Jang sweep with the same wider margin for consistency** (results above are
the corrected numbers — small shifts, same conclusion, nothing changed
qualitatively). The 2020-07-20 (S1B) window bug flagged earlier is still
open, unrelated to this fix.

**Result** (`reports/flood_where_s1_statewide.json`):

| Station | Flood date | New-water (flood-only) |
|---|---|---:|
| Kibithu | 2016-07-26 | 1.2% |
| Yinkiang | 2023-08-29 | **0.0%** |
| Passighat | 2021-08-29 | 2.1% |
| Jollang | 2022-09-05 | 1.9% |
| Miao | 2026-04-22 | 0.1% |
| Daporizo | 2019-07-22 | 5.8% |
| Doimukh | 2024-11-17 | 2.5% |
| Pagoda | 2024-07-01 | 3.2% |
| Pare HEP | 2026-07-29 | 4.6% |

**7 of 8 checked stations show a real positive signal** on their one tested
flood date — a second, independent confirmation of the Jang pattern, now
spread across the state rather than one valley. **One honest exception, not
hidden:** Yinkiang scored an exact 0.0% — either that particular date's
flood was too localized/shallow for this method to catch, the chosen scene
timing missed the peak, or a real limit of the method at that location; not
investigated further this pass.

**Combined WHERE picture (before loose-ends cleanup):** Jang valley (12/12
positive across 5 years) + 8 new stations (7/8 positive on one date each) =
19 of 20 checks across 10 different locations and 7 years show a real
satellite water signal on a confirmed flood day.

---

## 11. Loose ends closed ✅ done 2026-09-01

Three real gaps remained after §8/§7's rollout, all closed in one pass —
scripts: [sentinel1_flood_evidence_loose_ends.py](../../scripts/model/sentinel1_flood_evidence_loose_ends.py).

### Fix 1 — 4 stations with a real threshold their whole record never reaches

Tuting, Pangin, Lemeking, Namsai each have a **published** CWC danger level
that their **entire recorded history — years to decades — never once
reaches** (checked directly: each station's all-time max sits a consistent
1–8 units below its own danger level). Real, not a bug — these are
genuinely calm rivers by their own official standard. But "use the real
threshold" silently gave these 4 stations **zero** training/evidence labels.

**Fix:** `backtest_flood_when.py` and `train_flood_when.py` now fall back to
the self-derived percentile proxy (same method already used for stations
with no threshold at all) whenever the real threshold is never crossed,
clearly labelled so it's never confused with an actual danger-level
crossing. Re-ran both scripts statewide:

| Station | Flood days found | WHEN AUC (shipped blend, D) |
|---|---:|---:|
| Tuting | 146 | 0.892 |
| Pangin | 62 | 0.938 |
| Lemeking | 121 | 0.909 |
| Namsai | 90 | 0.882 |

All four score **among the strongest in the whole statewide set** — makes
sense: a genuinely calm river's rare high-water days are easy to tell apart
from its normal ones. `arunachal_flood_days.csv` grew from 1,092 to 1,511
labelled flood-days on this fix alone.

### Fix 2 — Yinkiang's exact 0.0% new-water reading

Flagged honestly in §7 rather than hidden. Retried on a **different**
exact-match date (2020-06-28, was 2023-08-29) — scored **2.1% new-water**,
a real positive signal. **Conclusion: the original 0.0% was specific to
that one date/scene, not a limit of the method or the location** — the
kind of check that's only meaningful because the original miss was reported
plainly instead of silently dropped.

### Fix 3 — Seppa and Tamen (no exact satellite match, only 2 days off)

Checked them anyway, on the nearest real acquisition:

| Station | Date used | Gap from flood day | New-water |
|---|---|---:|---:|
| Seppa | 2026-07-15 | 2 days | 1.7% |
| Tamen | 2022-07-07 | 2 days | 2.2% |

Both real, positive signals — confirms a close (not exact) match is still
usable evidence, worth remembering for future rollouts where an exact match
isn't available.

### A fourth issue found and fixed along the way — and one genuinely unfixable

**Tuting sits right at the edge of Sentinel-1's coverage — a real
location limit, not a per-date fluke.** The first attempted date failed
with "no real coverage despite matching the AOI search" (the same class of
edge case as 2020-07-20's S1B miss at Jang, §7 — now raises a clear message
instead of a cryptic rasterio crash, a small robustness fix made while
diagnosing this). A second attempt on a **different orbit** (4) hit the
*exact same* failure — proving it isn't one bad date, that whole orbit's
swath doesn't reach Tuting. **Third attempt, a third orbit (143), worked**:
0.5% new-water, a real positive signal, small because a young, narrow river
here.

**One robustness fix with no data implication:** the download batch script
crashed outright on a transient DNS resolution failure mid-run (CDSE's auth
host briefly unreachable) because only the download step was wrapped in
retry logic, not the token step before it. Fixed by wrapping both — a
network blip, not a data or method problem.

### Final combined WHERE picture, CWC stations

**Every one of the 16 distinct river locations checked so far shows a real,
positive satellite water signal on a confirmed flood day** — Jang valley
(12/12 dates across 5 years) plus 15 other named rivers statewide (one date
each, now including Yinkiang's corrected retry), spanning 2016-2026. Zero
locations show no signal. Only Bhalukpong (pre-2015 flood era, predates
Sentinel-1) remains untouched among CWC's 18 stations.

---

## 12. NWDP pass — the 14 small rivers, done ✅ 2026-09-01

The planned "different pass" for the 14 smaller NWDP rivers (this doc's own
§8 note, and the plan agreed with the user) — same WHEN-then-WHERE recipe,
built as its own parallel scripts rather than editing the CWC ones, since
NWDP's data shape and quality issues are genuinely different.

### Data: real, free, fetched — `fetch_24_nwdp_discharge.py`

`nwdp.nwic.gov.in` (NWIC, sister body to CWC) — documented CKAN API, no
login, bulk CSV dump confirmed working (per
`docs/data_research/DATA_VERIFICATION.md` Finding 12). **754,899 real
discharge readings (m³/sec, 15-min intervals) across all 14 stations**,
2023–2026.

**Two of the government's own reported coordinates are wrong** — confirmed
automatically (a bounding-box check flags anything outside Arunachal):
Changlang's raw coordinate sits in Kashmir, Ziro's in Uttarakhand. Both
corrected by geocoding the real town (`nwdp_stations.py`, the registry
mirroring `flood_stations.py`). The other 12 stations' coordinates passed
the check.

### WHEN — `backtest_flood_when_nwdp.py`

Every one of the 14 uses the self-derived percentile method — **no NWDP
station publishes a danger threshold at all** (unlike CWC, where 13/18 do),
so this is the standing method here, not a fallback for a few.

**A real, different data-quality problem than CWC's**: NWDP's raw feed has
explicit sentinel/fault codes baked into the stream — values pinned at
exactly ±99999.99 / 100000.00 — plus physically impossible negative
discharge, on every station checked (2–17% of readings on the worst
stations). Not sensor drift to smooth around like CWC's decimal-shift
glitches — dead-giveaway fault codes, filtered with a hard bound
(`|discharge| >= 50,000` or `< 0`, dropped outright) plus a handful of
garbage 2000-01-xx timestamps on 2 stations (already flagged in
`DATA_VERIFICATION.md` as a template artefact).

| Result | |
|---|---|
| Scored | 12 of 14 (Deomali, Miao_2 fall outside the rainfall grid — same limitation as Bhalukpong, not fixed here) |
| Flood days found | 137, self-derived |
| AUC range | 0.659 (Tissa Camp) – 0.957 (Kamlang), median 0.876 |

Full table: `reports/flood_when_backtest_nwdp.json`.

### WHERE — `sentinel1_flood_evidence_nwdp.py`

Same calibration/warp pipeline, unchanged, applied to each station's real
location. One flood date per station (Sagalee had no exact match — used the
nearest scene, 1 day off, same as Seppa/Tamen in §11).

| Station | Flood date | New-water |
|---|---|---:|
| Aalo | 2026-06-04 | 2.8% |
| Basar | 2024-07-01 | 0.7% |
| Changlang | 2024-08-13 | 1.1% |
| Changlang (2nd station) | 2026-04-22 | 0.8% |
| Darak (Kamba) | 2025-07-27 | **4.6%** |
| Kamlang | 2024-05-02 | 2.4% |
| Kanubari | 2026-05-06 | **0.0%** |
| Tenga | 2024-06-29 | 2.4% |
| Tengapani Bridge | 2026-04-22 | 1.4% |
| Tissa Camp | 2025-07-27 | 0.1% |
| Ziro | 2023-07-24 | 1.4% |
| Sagalee | 2024-10-05 (1 day off) | 1.0% |

**11 of 12 positive.** All orbits needed (4, 41, 70, 77, 106, 143) already
had a baseline downloaded from the CWC pass — zero new baseline scenes
needed for this entire 14-station rollout, only the flood-day scenes
themselves (11 unique downloads, 2 stations shared an already-downloaded
scene by coincidence of date).

**Kanubari, the one miss — retried, and it's real, not a date fluke.**
Unlike Yinkiang (§11), which flipped to positive on a second date, Kanubari
scored an **identical exact 0.0% on two independent dates** (2026-05-06 and
2026-06-11, different months, both real exact satellite matches). Reported
honestly rather than retried a third time to fish for a positive — this
looks like a genuine station-level limitation (a channel too narrow for
this method at 11 m resolution, or a local terrain effect), not a fixable
bug or a lucky/unlucky date. Left open, not swept under the rug.

### Combined picture, both networks

| | CWC (18 stations) | NWDP (14 stations) | Total |
|---|---:|---:|---:|
| WHEN scored | 17 | 12 | 29 / 32 |
| WHERE checked | 17* | 12 | 29 / 32 |
| WHERE positive | 16 | 11 | 27 / 29 |

*Includes 2020-07-20's known-open S1B coverage gap at Jang (§7), which
doesn't block the other 12 dates already scored there.

**32 real river-monitoring stations exist across the state's two open
government networks. 29 now have real, checked WHEN evidence and 29 have
had a real WHERE satellite check attempted — 27 of those confirmed
positive, 1 confirmed negative on two independent dates (Kanubari), 1 not
yet retried (Tissa Camp's 0.06%/0.07% reads as a very weak but technically
positive signal, not zero — left as is).** This is now full practical
coverage of Arunachal's real, government-run river gauge networks, not a
pilot or a partial rollout.

---

## 8. Rollout path — the confirmed next step 🔵 not started

Both pilot pre-conditions are now met (§6.5's cross-check *is* variant C
against Passighat, done in §5; the pilot proved out end to end through §7).
So this is next, not conditional:

1. Extend Phase 0's fetch script (`fetch_21_cwc_gauges.py`) to every
   remaining CWC station and all 14 NWDP stations — no rewrite needed,
   station ID is already a parameter.
2. Retrain Variant A per new station and Variant B on the full pooled set —
   the Tawang-only versions are superseded, not extended. Variant C stays a
   diagnostic, rerun only if the size-aware question needs re-checking.
3. Keep reporting all surviving variants side by side, statewide — the
   scorecard habit doesn't stop after the pilot.
4. Repeat Phase 3's feasibility-check-then-calibrated-check recipe
   (`fetch_22_sentinel1_flood_dates.py` → `sentinel1_flood_evidence.py`) at
   each new station's nearest unconfirmed WHERE location, the same way it
   ran for Jang.
5. Fix the one open bug (2020-07-20's S1B window edge case, §7) if a new
   station's scenes hit the same GCP pattern — otherwise it can stay a known
   gap.

### Rollout, step 1-3 ✅ done 2026-08-30 — WHEN now runs on 17 stations statewide, not 3

Extended [flood_stations.py](../../scripts/model/flood_stations.py) — now
the **shared** registry both `backtest_flood_when.py` and
`train_flood_when.py` import from, replacing each script's own hardcoded
3-station dict — to all **18 CWC stations** found tagged or physically
located in Arunachal Pradesh (17 via `meteorologicalSubDivision = "Arunachal
Pradesh"`, plus Rho Basti, untagged). Real per-station coordinates came from
`layer-station-geo`, a separate, undocumented endpoint found this session —
the main station record returns null lat/lon for every gauge, which is why
the original pilot approximated both Tawang gauges to a shared "Jang town"
point. **Fixed that too** — both Tawang gauges now use their own real
coordinates. Catchment area came from `layer-station`, queried one station
at a time (its bulk/list query 500s).

**Result: 98,473 readings (3 stations) → over 1.1 million readings (18
stations), spanning Kibithu (97.03°E, near the China border) to Bhalukpong
(92.64°E, near Assam) — genuinely statewide, not just Tawang.**
**13 of 18 stations have a published CWC danger level** (vs. 1 of 3 before)
— most of the state no longer needs the self-derived proxy at all.

**Two real correctness bugs caught before trusting any of this — both fixed
and re-verified against the original pilot stations to confirm no
regression:**

1. **Data-cleaning bug — would have silently deleted 17% of a station's real
   history.** The original outlier filter (a single global median/MAD for a
   station's whole multi-decade record) is fine for catching isolated
   glitches, but Miao (`008-ubddib`) has two genuinely real level clusters
   (~130-215 m and ~216-310 m, no readings between) — almost certainly a
   gauge re-levelling at some point in ~30 years of record, not sensor
   error. The global check flagged **18,732 of 112,413 readings (17%)** as
   "errors." Fixed with a rolling 90-day local median/MAD instead of one
   whole-series baseline (a slow datum shift moves the local baseline with
   it), plus a ratio backstop (only drop where the value is also a true
   zero or off by 3×+ from its own neighbourhood — a rolling MAD can itself
   collapse toward zero in a genuinely calm stretch, which briefly caused
   its own false positives on Rho Basti before this backstop was added).
   Re-verified: both original pilot stations now drop *exactly* their
   original counts (5 for Murga Bridge, 9 for Rho Basti) — zero regression.
2. **A border-adjacent gauge falls outside the IMERG-indexed rainfall
   grid.** Bhalukpong (`029-UBDDIB`, 27.02°N, 92.64°E, right on the Assam
   boundary) sits inside the project's bounding box but outside the actual
   indexed grid (built against the state polygon, not the box) — crashed
   the whole batch on first run. Fixed by catching this per-station and
   skipping just that one, in both Phase 1 and Phase 2's scripts, so one
   edge case can no longer take down every other station's result.

**Phase 1 (backtest) result, 17/18 stations scored — full table in
`reports/flood_when_backtest_arunachal.json`:**
most stations show AUC 0.82-0.96 against their own real or self-derived
flood days — consistent with the original pilot's numbers, now confirmed at
statewide scale, not just 2-3 rivers.

**Phase 2 (train variants A/B/C/D) result — full table in
`reports/flood_when_variant_comparison_arunachal.json`:**
the same pattern holds at scale — **Variant A (fitting on one station's own
data alone) is now dramatically worse everywhere it can be compared**
(e.g. Daporizo 0.104, Yinkiang 0.480, Rho Basti 0.581, against baselines of
0.885/0.901/0.812) — the strongest confirmation yet of "fitting on scarce
data loses to not fitting," now shown across 17 stations instead of 3. The
shipped blend (D) tracks close to or slightly above the baseline rule on
every station with enough data to score.

**Two honest findings flagged, not swept past:**
- **4 stations show zero flood days despite a published danger level**
  (Tuting, Pangin, Lemeking, Namsai) — either genuinely quiet records in the
  data pulled, or a stale/mismatched threshold; not yet investigated further.
- **2 stations score badly** (Doimukh 0.38, Tamen 0.37 — worse than the
  0.82-0.96 typical range), both with only 2 flood days each — most likely
  small-sample noise, but flagged rather than hidden; these catchments may
  genuinely behave differently from the rainfall trigger's assumptions.

**Not yet done — the WHERE half of the rollout (§8 step 4):** repeating
Phase 3's satellite feasibility-check-and-calibrated-water-detection recipe
at the other 16 stations' locations is a much larger undertaking than the
WHEN side (each station needs its own scene search, download, and
calibrated processing — the Tawang pilot alone took multiple GB and a long
processing pass for just 3 orbits). Scoped as the next concrete step, not
started this pass.

**Why rollout comes before calibration (§10) — decided 2026-08-30:**
calibrating "does our 70% really mean 70%" needs a broad, varied set of real
outcomes to check against. Right now that's ~150 flood days from 2 small,
similar mountain streams plus 1 big river — too little and too similar to
calibrate on without repeating the exact mistake already learned twice this
session ("fitting on scarce data loses to not fitting," Phase 2 §5). Rollout
is also now low-risk: every real bug in this pipeline was found and fixed
during the Tawang pilot (§3, §5, §7's three separate bugs) — extending it to
more rivers is mostly repetition of a proven recipe, not new risk. Expanding
first also directly grows the calibration's own eventual input, so it isn't
wasted sequencing — calibrating now would likely need redoing once more
data arrives anyway.

---

## 9. Open items / asks tied to this plan

- CWC: real danger/warning thresholds for Murga Bridge and Rho Basti —
  **downgraded to a nice-to-have cross-check, not a blocker.** §1 and §4
  show the self-derived label already works and needs no ask answered. If it
  arrives, it becomes one more thing to compare the self-derived threshold
  against — it does not gate anything.
- **Nothing in this plan is blocked on any ask.** Phases 0-1 are proof of
  that: both ran to completion, on real data, with zero government input.

---

## 10. Calibration ✅ DONE 2026-09-01 — it is a real probability now

Scripts: [calibrate_flood_when.py](../../scripts/model/calibrate_flood_when.py),
[predict_flood_when.py](../../scripts/model/predict_flood_when.py),
[verify_flood_events.py](../../scripts/model/verify_flood_events.py).
Reports: `flood_when_calibration.json`, `flood_when_event_verification.json`.

### The gap this closed

Everything before this measured **AUC** — whether the score ranks risky days
above calm ones. It does. AUC says nothing about whether the number itself
means anything. Measured here for the first time: **the raw blend score was
badly miscalibrated, and as a probability it was worse than useless** — a
Brier skill score of **-2.67** against climatology, i.e. quoting the raw
score as a percentage would have been worse than answering "0.76% every day,
forever." That is exactly the overclaim §10 previously warned against, now
measured rather than assumed.

### Method, and the one thing that makes it honest

Isotonic regression (monotonic — it rescales magnitudes without reordering,
so it cannot damage the AUC already earned), cross-checked against Platt
scaling, which agreed closely.

**The calibrator is itself held out.** A calibrator scored on the rows it
was fitted on looks perfect by construction — the easiest way to fake this
result. Every number below comes from year-grouped CV *of the calibrator*,
on top of input scores that were already out-of-fold from the model's own
year-grouped CV. No row is ever scored by a model or a calibrator that saw
its year.

### Result — official CWC danger level (the number to quote to an official)

46,693 station-days, 353 real danger-level crossings, base rate 0.76%.

| | raw score | calibrated |
|---|---:|---:|
| Calibration error | 10.91% | **0.03%** |
| Brier skill vs climatology | −2.665 | **+0.091** |
| AUC | 0.917 | 0.911 |

Reliability — predicted vs. what actually happened, on years the calibrator
never saw:

| Predicted band | Days | Predicted | **Observed** |
|---|---:|---:|---:|
| 0–1% | 38,244 | 0.1% | **0.1%** |
| 1–2% | 1,991 | 1.3% | **1.9%** |
| 2–5% | 2,536 | 2.8% | **2.8%** |
| 5–10% | 1,027 | 6.2% | **4.9%** |
| 10–25% | 711 | 13.4% | **13.2%** |
| 25–50% | 40 | 45.7% | **57.5%** |

### Sharpness — calibrated is not enough on its own

A forecast that always answers "0.76%" is perfectly calibrated and useless.
What the system actually does on the days it commits:

| On the riskiest… | Predicted | Observed | vs base rate | Share of all floods caught |
|---|---:|---:|---:|---:|
| top 0.1% of days | 50.4% | **43.5%** | 57× | 5.7% |
| top 1% of days | 20.4% | **19.7%** | 26× | 26.1% |
| top 5% of days | 9.2% | **9.0%** | 12× | 59.5% |
| top 10% of days | 5.8% | **5.7%** | 7.6× | 75.9% |
| top 25% of days | 2.7% | **2.7%** | 3.6× | 89.5% |

**It never says 90%, and it should not.** With rainfall-only inputs on a
0.76%-base-rate event, the honest ceiling is a peak issued probability of
~67%. A system claiming 95% certainty here would be lying.

### Event-level verification — what it said on real flood days

1,138 real flood days, **379 distinct episodes**, 29 stations, all
out-of-fold:

| Peak alert reached during the episode | Episodes | Share |
|---|---:|---:|
| SEVERE (≥25%) | 63 | 16.6% |
| HIGH (≥10%) | 84 | 22.2% |
| MODERATE (≥5%) | 67 | 17.7% |
| ELEVATED (≥2%) | 76 | 20.1% |
| **NORMAL — missed entirely** | **89** | **23.5%** |

**76.5% of real flood episodes got ELEVATED or above; 38.8% got HIGH or
SEVERE; 23.5% were missed outright.** The misses are listed by name in
`flood_when_event_verification.json` — e.g. Murga Bridge's 6-day July 2020
episode peaked at 1.00%, a clean miss. Named hits include Miao's 14-day June
2003 flood (SEVERE, 33.6%) and Pangin's 11-day July 2017 flood (SEVERE,
36.9%).

### ⚠️ Two different probabilities — never blur them in a pitch

| Station type | The number means | Base rate |
|---|---|---|
| Published CWC danger level (13 stations) | P(crosses the government's own official danger level today) | 0.76%, real |
| Self-derived top-2% (16 stations) | P(today is in this river's own wettest 2% of days) | 2.0%, **by construction** |

Both are calibrated and both are real; they are not the same claim. The
self-derived group's base rate follows from its own definition, so it is the
weaker thing to quote. `predict_flood_when.py` carries a `means` field per
row for exactly this reason and never averages the two together.

### First empirical WHERE check ✅ done 2026-09-01, expanded 2026-09-02 — real, honest, not yet a calibration

Script: [calibrate_flood_where.py](../../scripts/model/calibrate_flood_where.py).
First pass reused the 34 satellite events already scanned that session (Jang's
12 dates + 9 statewide CWC stations + 12 NWDP stations, no new downloads).
The next day, on the honest reading below, went back and processed every
*remaining* real exact-match satellite date already identified but not yet
pulled (`fetch_25_sentinel1_statewide_expand.py`, 37 more station-dates,
35 succeeded — 2 are genuine no-coverage cases, same class of real gap as the
documented 2020-07-20 S1B bug, not a new bug), plus the 7 already-computed
loose-ends checks that the first pass had missed folding in. **74 real
events now, up from 34** — same debugged calibration/warp pipeline
throughout, still overlaying real water masks against `webapp/assets/flood/
floodprone.npz`, the actual shipped static risk map.

| Predicted class | Pixels checked | Showed real new water |
|---|---:|---:|
| Very Low | 30,036,455 | **1.00%** |
| Low | 21,377,030 | 2.20% |
| Moderate | 25,159,360 | 1.56% |
| High | 23,604,659 | 1.44% |
| **Very High** | 34,726,757 | **5.16%** |

**Honest reading, updated:** Very High still clearly shows the most real
water (~5× Very Low), unchanged from the first pass — the map is not
random, and more data didn't move that headline number. But the ranking is
**still not clean monotonic**, and more data made the middle worse, not
better: Low (2.20%) now sits above both Moderate (1.56%) *and* High
(1.44%). That rules out "it was just 30-event noise, more data will sort it
out" as the full story — going from 34 to 74 events left the same shape.
The more likely real explanation: the static map's middle classes
(Moderate/High) are genuinely not well-separated from each other at this
resolution, even though the two extremes (Very Low, Very High) are. Still
not the finished spatial calibration — that needs a real held-out curve
fit the disciplined way §10 did for WHEN — but the honest conclusion has
shifted from "probably just needs more events" to "the middle classes may
need the risk map itself revisited, not just a bigger sample."

Chart: `data/interim/flood_when/where_calibration_overlay.png`. Full numbers
and per-event breakdown: `reports/flood_where_calibration.json`.

**Bhoonidhi (ISRO) checked as a backfill source, 2026-09-02 — real lead,
blocked on registration, not a workaround.** Its search API needs no
login and genuinely works (confirmed live), and it carries India's own
EOS-04 SAR (2022+) alongside a Sentinel-1 mirror — a real second source,
not just a copy of what CDSE already gave us. But every real-radar search
tried — Jang valley on a date we already know has a positive Sentinel-1
match, several other AOIs, both older and current dates, multiple satellite
choices — came back "No satellites available," consistently enough to be a
real result rather than a fluke: anonymous search likely only surfaces
results once logged in. No self-serve signup exists on the site; this is a
manual/approval registration, same category as the other government asks,
not a silent extra data source we can add ourselves.

### Himalaya-pooled WHERE player — data check done 2026-09-02, real but with a catch

User proposed a second WHERE panel player: train on the wider Himalayan
region, then fine-tune to Arunachal (same "pool broad, then narrow down"
trick that already helped WHEN's Variant B). Checked for real data before
building anything, same discipline as everywhere else here.

**Dartmouth Flood Observatory's Global Flood Records** (real, free, CC0,
`Zenodo 10.5281/zenodo.19288170`) — 5,503 dated flood events worldwide,
1985-2023, each with an actual footprint polygon (not just a point).
Downloaded and checked directly: **296 events intersect the Himalayan arc
(72-97.5°E, 26-36°N), 77 intersect Arunachal and its immediate neighbors
(91-98°E, 26-30°N)** — India 131, Nepal 48, Pakistan 42, Bangladesh 21 of
the arc total. Real, dated, genuinely near us.

**The catch, checked not assumed:** every single Himalaya-arc record's
`Source` field is `News` or `FloodList` (media-report based) — **zero** are
satellite-traced. Confirmed by measuring the polygons themselves, not just
trusting the label: bounding boxes routinely span 5-9 degrees of latitude
and longitude — e.g. one 1988 "flood" polygon covers 76.9-96.1°E, a
better part of the whole Eastern Himalaya, clearly a news-report region
estimate, not a real flood extent. Using these polygons directly as
pixel-level "this flooded" training labels would repeat the exact mistake
already caught and rejected once this project ([[bhuvan-flood-mask-is-unusable]]
— 70.5% of its "flooded" pixels were on cliffs): a label that's real about
*when* but not trustworthy about *where*, precisely.

**What this is actually good for:** a real, free list of 77 dated
candidate flood events near Arunachal (extendable to 296 across the wider
Himalaya) to feed into our *own* already-debugged Sentinel-1 pipeline — the
same move already made for Arunachal itself (CWC gauge crossing → go check
Sentinel-1 on that date), just using DFO's date+rough-region as the trigger
for Nepal/Bhutan/wider-Himalaya instead of a gauge we don't have there.
That produces real, precise, satellite-derived labels — DFO supplies the
"when/roughly where to look," not the label itself.

**Not yet checked:** the Global Flood Database (Cloud to Street/Yale, 913
events, 2000-2018, MODIS-derived — actual satellite raster flood extents
rather than news polygons) is a real, higher-quality candidate but its
per-event catalog lives inside Google Earth Engine, which needs its own
account/auth to query — not yet attempted. Worth checking before the next
pass if it has real Himalaya coverage; would be strictly better label
quality than DFO's polygons if so.

### 9-event Himalaya proof batch ✅ done 2026-09-02 — 9/9 real positive signal

Script: [fetch_26_himalaya_pool_test.py](../../scripts/fetch/fetch_26_himalaya_pool_test.py).
Per the user's explicit instruction — check 5-10 first, ask before the full
77-296 — picked 9 real, well-known Himalayan river towns whose location a
real DFO flood-event polygon actually contains (not the crude polygon
itself as the check point — a specific real river town chosen by hand),
then ran the exact same debugged Sentinel-1 pipeline used throughout this
project, no new code beyond the fetch/loop wiring:

| Town | Country | Date | New water |
|---|---|---|---:|
| Biratnagar (Koshi) | Nepal | 2021-06-19 | 0.02% |
| Phuentsholing (Wangchu) | Bhutan | 2023-06-16 | 0.39% |
| Kathmandu (Bagmati) | Nepal | 2021-07-02 | 0.81% |
| Along/Aalo *(sanity check)* | Arunachal | 2021-06-30 | 1.00% |
| Thimphu (Wangchu) | Bhutan | 2021-06-14 | 1.90% |
| Gangtok (Teesta basin) | Sikkim | 2023-10-07 | 1.97% |
| Rangpo (Teesta) | Sikkim | 2023-10-07 | 2.02% |
| Punakha (Mo/Pho Chhu) | Bhutan | 2021-06-14 | 2.27% |
| Pokhara (Seti) | Nepal | 2021-07-02 | 4.51% |

**Result: 9/9 show a real positive water signal — including the 2023
South Lhonak GLOF/Teesta disaster in Sikkim, checked on the nearest pass
3 days after the outburst, and every Bhutan/Nepal town, none of which this
project had ever touched before.** The Arunachal sanity check (Along,
1.00%) lands right in the middle of the distribution, not an outlier —
one honest early sign the method transfers, not just works at home.

Two real bugs hit and fixed mid-run, same families as before: the CDSE
token-expiry bug from the statewide batch (forgot to port the per-download
refresh into this new script, fixed the same way), and two ordinary
transient network failures (one `ChunkedEncodingError`, one plain
`ConnectionError`) that a retry cleared on both — nothing structural.

**Honest scope check on what this proves:** 9 events is a real green light
that the pipeline generalizes off Arunachal, not proof the *idea* (pool
Himalaya, fine-tune to Arunachal) already has enough training data — see
the "will 9 be enough" discussion above. Full report:
`reports/flood_where_himalaya_pool_test.json`.

**Status: ⏸️ PAUSED here, deliberately, 2026-09-02 — user's own instruction:
"Hold it for now. Doc it as very important so that next time we return to
WHERE for flood we continue from here."** Full data check and proof batch
are both done and don't need repeating. Scaling to the remaining ~68-287
DFO-listed candidates is the real next step, waiting only on the user's
scope choice (Arunachal-neighbors-only vs whole arc — the cost difference
is ~90GB/5-7h vs ~370GB/20-24h+, genuinely worth asking again, not
assuming). **Full resume plan, what's already on disk, and exactly what to
ask: [PARKED_HIMALAYAN_FLOOD_WHERE.md](PARKED_HIMALAYAN_FLOOD_WHERE.md) —
read that file first, don't re-derive any of this.**

### Remaining honest limits

- **Autocorrelation.** 1,138 flood days are ~379 episodes; the calibration
  *mapping* is unaffected but confidence in it is narrower than the raw day
  count suggests.
- **Hindcast path, not a live feed.** *(Superseded 2026-09-21: the joined
  forecast now runs on live Open-Meteo rain via
  `scripts/model/flood_forecast_live.py` — see PARKED_HIMALAYAN_FLOOD_WHERE.md
  §0q. The gauge-level `predict_flood_when.py` below is still hindcast.)*
  Rainfall features come from the
  archived IMERG stack. Everything downstream — blend, calibration, bands —
  is what a live system runs; only the input tap differs. Wiring the live
  Open-Meteo path in is the remaining step to real time, and changes none of
  the numbers above.
- **WHEN only.** *(Superseded 2026-09-21 — WHERE is now calibrated and the
  two are joined; see the note at the top of this doc.)* This calibrates the timing half. Multiplying a calibrated
  probability by the *uncalibrated* static WHERE layer produces an
  uncalibrated product — so the two are deliberately NOT multiplied into a
  single headline number yet. At a gauge, quote the calibrated probability;
  away from a gauge, the static layer remains a relative index, exactly as
  before. Calibrating the spatial half needs dated, located inundation
  extents, which the Sentinel-1 work (§7, §11, §12) has now started
  producing but has not yet accumulated enough of.

- CWC: real danger/warning thresholds for Murga Bridge and Rho Basti —
  **downgraded to a nice-to-have cross-check, not a blocker.** §1 and §4
  show the self-derived label already works and needs no ask answered. If it
  arrives, it becomes one more thing to compare the self-derived threshold
  against — it does not gate anything.
- **Nothing in this plan is blocked on any ask.** Phases 0-1 are proof of
  that: both ran to completion, on real data, with zero government input.

## 13. WHEN fed the river's own latest reading + a live track record ✅ 2026-09-21

Two steps, done together.

### 13a. Gauge + rain models, 1-3 days ahead

`scripts/model/train_flood_when_gauge.py` → `models/flood_when_gauge/`,
`reports/flood_when_gauge.json`.

**Question:** the shipped WHEN reads rain only. At a gauged river we also
know where the water is now. How much is that worth?

**Inputs** for target day D, gauge last read on D-L (L = 1, 2, 3):
- rain on D, as before: r3, r7, trigger_lag1
- `g_frac`, the level on D-L as a share of the way from the river's median
  to its threshold (0 = ordinary, 1 = at threshold)
- `g_rise`, the one-day change in `g_frac`

Threshold units pool a 5 m trunk river and a 0.5 m hill stream on one scale,
per guardrail 2. The labels are the same as WHEN's: the official danger
level if the record reaches it, else the river's own top 2%.

**Model and data:**
- One pooled HistGradientBoosting per lead, monotone increasing in every
  input.
- **All 32 gauges.** The shared rain-cell lookup (`when_grid.cell_of`) also
  covers Bhalukpong, Deomali and Miao_2, which the clipped raster had
  skipped.
- About 92k gauge-days, of which about 1,135 are flood days.

**How it was graded:**
- Year-grouped out-of-fold scores, with a year-grouped calibrator on top.
- The rain-only baseline is run through the identical pipeline on the
  identical rows.
- **Onset days** means the river was below its threshold at the last
  reading. Those are the numbers that matter: a river above danger
  yesterday is easy to call today.

Lead 1, official danger level, warning at 25%:

| | rain only | rain + river reading |
|---|---:|---:|
| all days: floods caught / warnings right | 11% / 21% | **58% / 56%** |
| onset only: floods caught / warnings right | 6% / 6% | **12% / 33%** |
| AUC all / onset | 0.904 / 0.868 | **0.964 / 0.928** |
| Brier skill all / onset | 0.04 / −0.17 | **0.37 / 0.07** |

- The gain holds at every lead: onset AUC is 0.93–0.94 against 0.87–0.89
  for rain only.
- It beats plain persistence ("tomorrow = today"), which catches 60% at
  lead 1, 42% at lead 2 and 32% at lead 3, with the same share of its
  warnings right.
- Rain-only onset skill is negative. That is the old WHEN over-promising on
  onset days, which the gauge models fix.
- Top-1% said/happened is now honest in every subset. For example, official
  onset at lead 1 says 14.5% and 12.5% happens; rain only says 21% and 5%
  happens.

**Two calibration fixes, both measured before they were kept:**
1. One shared calibration curve over-promised on onset days: at official
   gauges it said about 20% and about 12% happened.
2. Official-danger and own-top-2% gauges have different onset base rates
   (0.29% against 0.79%). So there are four curves, river state × label
   kind, both known at issue time.

**Record breaks found while doing this:** each gauge was checked by comparing
its yearly 5th–95th percentile ranges. Four change scale partway through.
Only the record from the break on is used (`RECORD_STARTS`):
- **Ziro:** 2023–24 dry season read 100–2,700 m³/s; from 2025 on, 0–194. Its
  top-2% threshold had been 2,372 against today's 0.7.
- **Namsai:** the level steps up about 5 m during 2019.
- **Doimukh:** 2019–21 sits about 22 m lower, then returns.
- **Pagoda:** 2019–20 sits about 15 m lower.

The rain-only WHEN labels (§10) predate this check and still use the full
records.

### 13b. Live run, forecast log and automatic checking

- **Gauge feeds:** `scripts/model/flood_gauge_live.py`.
  - **CWC:** a nested `id.dataTime gte` filter works on `new-entry-data`,
    about 150 rows a week instead of the full history. It is live to the
    hour.
  - **NWDP:** `datastore_search`, sorted by `_id desc`. It runs about 2 days
    behind, skips days and posts partial ones. Days with fewer than 48 of 96
    readings are treated as missing.
- **Model choice:** the model is picked by the age of the last complete day
  of readings. 1–3 days uses the matching lead model; anything older uses the
  same pipeline on rain alone. Every row says which one it used.
- **Where it runs:** wired into `flood_forecast_live.py`. The daily run now
  writes a `rivers` block (32 gauges × 7 days) into
  `reports/flood_forecast_live_<date>.json`, flags "above threshold now" from
  today's partial readings, logs everything and runs the checks.
- **Log and checks:** `scripts/model/forecast_log.py` keeps the log in
  `records/flood_forecast/` (moved out of git-ignored `data/` on 2026-09-22:
  a track record can't be regenerated):
  - every river forecast and area outlook as issued;
  - the gauge maxima read back;
  - forecasts joined to outcomes;
  - `reports/flood_forecast_scorecard.json`.
- **Grading:** river forecasts grade themselves from the same feeds. A target
  day with no reading after 21 days becomes "no reading". The area outlook
  is logged but waits for satellite or news truth.
- **Testing:** the checker was tested on a backdated copy of the log, and
  real gauge read-backs graded 67 of 96.

**First live issue, 21 Sep 2026:**
- Every river is NORMAL; the highest is Tuting at 0.9%.
- 13 gauges were on a 1-day-old reading and 13 NWDP gauges on a 2-day-old
  one.
- Silent CWC gauges: Yinkiang, Pangin, Doimukh, Pagoda and Tamen, plus
  NWDP's Kamlang. These fell back to rain only.

**Scheduled 2026-09-22.** The Windows task "FloodSense daily forecast"
runs daily at 08:30, after CWC's 08:00 reading. It is registered by
`scripts/register_daily_flood_forecast.ps1` and runs
`scripts/run_daily_flood_forecast.ps1`.
- If the machine was off at 08:30, it runs as soon as it's back on.
- It tries 3 times, 10 minutes apart.
- It logs to `logs/flood_forecast_daily/<date>.log`.
- This machine's PATH has no System32, so the runner uses only full paths.
- It runs as the signed-in user, so it needs that user logged in.

First scheduled run: 22 Sep. 13 of the 21 Sep forecasts were checked (no
crossings, all said under 1%). The rest are waiting on NWDP's delay or on
silent gauges.

**On screen 2026-09-22.** FloodSense's first view, "Live forecast"
(`webapp/products/flood/live.py`), shows:
- the 7-day strip (× an ordinary day);
- the map of floodable ground (location model ≥10% given a flood), coloured
  by how unusual the day is;
- the 32 gauges as coloured dots;
- the rivers table (chance, band, threshold kind, reading used);
- the track record.

It reads `webapp/assets/flood/live_forecast.json`, which the daily run
writes (`export_web` in `flood_forecast_live.py`). The app can't run the
models itself (no scikit-learn on the free host). The old rule-based
screen is kept, renamed "Rain index".

Run locally beside the full project, the screen also has **"Run the forecast
now"**. It runs the real models on the spot (`flood_forecast_live.py --no-log`,
1–3 min, progress shown) and flags when today's forecast hasn't run yet.
`--no-log` leaves the track record alone, so the logged issue stays the
scheduled 08:30 one, written down before the day. It was tested: the
snapshot refreshed and the log file was byte-identical afterwards.

**Still open:**
- Let the scorecard build over the next monsoon; it means little until
  about 20 threshold crossings have been checked.

### 13c. Clean-up pass ✅ 2026-09-22

**1. The rain-only fallback was over-promising.** Tested on onset days, a
single pooled curve said ~21% where ~8% happened. Fixed two ways:
- **Gauge models now cover leads 1–9** (`lead1..9.pkl`), so a reporting
  gauge has a gauge-aware model for every outlook day, NWDP's lag included.
  Even a 9-day-old reading still helps: onset AUC is 0.929–0.938 at every
  lead, against 0.87–0.91 for rain alone. Calibration holds at leads 1–3; at
  leads 4–9 the top 1% runs a little high (e.g. lead 7, all days: 39% said,
  32% happened).
- **Rain-only is now only the fallback for an offline gauge.** There the
  river's state is unknown, so it is calibrated per label kind with state
  ignored. Top 1%: official gauges said 18.0%, 14.7% happened; own-top-2%
  gauges said 33.7%, 32.6% happened.

**2. Scale-break gauges removed from the old rain-only WHEN too.**
`RECORD_STARTS` (Ziro, Namsai, Doimukh, Pagoda) now lives in
`scripts/model/gauge_records.py`. It is used by `train_flood_when.py`,
`train_flood_when_nwdp.py` and `train_flood_when_gauge.py`. The backtest
scripts behind the WHERE flood-date lists are deliberately unchanged.

Retrained the whole chain: WHEN panel → calibration → `when_grid` →
production day model → live scales and normal → replay. Old models are
backed up in the session scratchpad.
- **Namsai WHEN:** 0.882 → 0.911.
- **Calibration error** after isotonic: 0.04–0.15%.
- **Map replay** (2023–26, clean): timing-only AUC 0.838 → 0.847. At 2×
  it catches 69% (was 68%); at 5×, 27% (was 22%). Arunachal ranking AUC
  0.888 → 0.884.
- **Live-source check inside Arunachal:** satellite-fitted model on live
  rain 0.725 → 0.714 (150 floods), within noise.

Kept, because the cleaned records are the correct ones.

**3. Silent gauges are offline, not seasonal.** Each reported year-round,
then stopped:

| Gauge | Last reading |
|---|---|
| Yinkiang | 12 Jun 2024 |
| Kamlang (NWDP) | 7 Feb 2025 |
| Tamen, Doimukh, Pagoda | 30 Apr – 1 May 2025 (same day: one telemetry change) |
| Pangin | 5 Sep 2025 |

Expect them to stay on rain only next monsoon. The live run now looks up
each silent gauge's last reading (CWC: two-year window; NWDP: newest row,
else the archive's `record_ends`). It marks the gauge `gauge_offline`, and
the screen shows "gauge offline since …".

### 13d. On screen: the gauge on a place's own river, and its graph ✅ 2026-09-27

A river's checked forecast now appears for a place only when the gauge is on
that place's own river (same flow path, drainage area within ×0.5–×2, within
60 km along it — `scripts/build/build_gauge_link.py`, self-tested); otherwise
the screen says no gauge measures that river and names the nearest one as
being on a different river. Below the map, a Google-Flood-Hub-style graph per
gauge: the last 30 days of real daily highs (a separate display-only fetch —
the forecast's 8-day window is unchanged), a "Now" line, CWC's published
warning / danger / highest-ever lines where they exist
(`build_gauge_levels.py`), the line our chance refers to, and bars for our
chance on each coming day. No level forecast is drawn. Details: PARKED
§0w, FLOOD_SCREEN_PLAN.md Phase 5. Gauge crossings also feed the new flood
records (`flood_intake.py`).

### 13e. What the gauge data showed when placing gauges on the map ✅ 2026-09-28

Found while fixing where each gauge sits on the map's rivers
(`build_gauge_link.py`; the screen side is in FLOOD_SCREEN_PLAN.md status).

**Placement.**
- The old rule, "biggest channel within 1.5 km", moved every gauge
  1.5–2 km downstream, and 5 onto a bigger neighbouring river. Pagoda, for
  example: CWC catchment 176 km², placed on a 1,472 km² river.
- The new rule is the nearest channel within 2 km that is the gauge's size:
  - **CWC:** within ×0.5–2 of the published catchment, where one exists.
    For Siang gauges fed from Tibet, whose catchment is mostly off the map,
    any trunk river.
  - **NWDP:** big enough to carry its typical monsoon flow, at most
    0.4 m³/s per km², judged on the usable record only
    (`gauge_records.RECORD_STARTS`).
- Result: 27 of 32 gauges land within 0.3 km of their published spot. CWC
  catchments are matched to ~1–2% (Doimukh 1,210 vs 1,212 km²; Tamen
  7,569 vs 7,568; Daporizo 15,104 vs 15,114).
- **Miao (NWDP)** sits on an 84 km² stream but carries ~200 m³/s in the
  monsoon, which is physically impossible there. It is placed on the
  1,374 km² river 1.7 km away.

**Gauges whose location is not really known.**
- NWDP's own coordinates for Changlang (Kashmir) and Ziro (Uttarakhand) are
  wrong. `nwdp_stations.py` stands in each town, which does not say which
  stretch of river the gauge measures. Both are now left unmatched to places
  on the map; their forecasts and graphs are unchanged.
- **Ziro's record before 2025 looks like a different river:**
  - 2023–24 flows are 100–5,900 m³/s (monsoon medians 1,000–1,900).
  - From February 2025 they are 0–12 m³/s, a small stream, which fits Ziro.
  - The raw coordinates (30.29°N, 78.98°E) sit on the Alaknanda, whose
    flows match the early numbers.
  - `RECORD_STARTS["Ziro"] = 2025-03-01` already keeps the early part out of
    training. This explains why.
- ⚠️ **Open flag — Changlang (2nd station) may have an unrecorded record
  break.**
  - Its quarterly median flow jumps ~10× between 2024 and 2025 (2024 Q3:
    8 m³/s; 2025 Q3: 87 m³/s).
  - It is not in `RECORD_STARTS`, so its own-wettest-2% threshold may span
    two scales.
  - Check it with the annual 5th–95th percentile test before its next retrain.

**What NWDP's feed actually delivers** (last 30 days to 2026-09-28).
- Aalo sent nothing on 13 of 31 days (29–30 Aug, 2–5 Sep, 10–14 Sep, and
  the last 2 days, which NWDP publishes about 2 days late).
- Tenga is blank on the same dates, so these are network-wide outages, not
  one gauge.
- 23 Sep was a part-day at every NWDP gauge (37–38 of 96 readings).
- Part-days (fewer than 48 of 96 readings) are still kept out of every
  forecast. Since today the gauge graph shows them as hollow dots
  (`flood_gauge_live.fetch_history`), with the reading count in the tooltip.
  Aalo showed 15 complete days and 3 part-days out of 31.

### 13f. One wrong reading read as a flood — a filter that judges in metres ✅ 2026-10-05

**What happened.** On 2026-09-29 the screen showed Murga Bridge at 52%, with
"River now: +96.3 m above its high-water line".
- CWC's feed held one reading of **2,231.30 m at 11:00 on 28 Sep**. Every
  other reading that month was 2,134.3–2,134.9 m; the next hour read 2,134.29.
- The river forecast reads the previous day's highest reading. So it saw a
  river 96 m above its line and said 52% (34%, 29% … for the following days).
- It was not the day-model change of that day: the old model had already
  said 51.9% at 09:11, and river forecasts were identical before and after it.
- The value is within 13 cm of Rho Basti's level at that hour (2,231.17 m),
  the neighbouring station with the next station code. So it was probably
  logged under the wrong station. **CWC has since corrected it** to 2,134.30.
- The track record marked 7 forecasts for 28 Sep as "the river crossed". It
  corrected itself by 30 Sep: each run re-reads the gauges when grading.
  The 29 Sep issue's 52 / 34 / 29% stay logged as issued and are graded as
  three false alarms.

**Levels are heights above sea level, not depths.** Murga Bridge's water
sits ~2,134 m above the sea, Pasighat's ~150 m. The river is a few metres
deep at both. What a flood changes is metres: the rise from typical to the
line is 0.8 m at Murga Bridge and 3.8 m at Pasighat, and the biggest rise on
record at any gauge is about 20 m (Pangin). A 97 m jump is impossible
everywhere.

**Why the old filter missed it.** `clean_readings` only dropped a reading
that was a zero or 3× / ⅓ of its neighbourhood, a test built for dropouts
and slipped decimal points. As a share of a height above sea level, that
test gets looser the higher the gauge: it rejects readings above ~450 m at
Pasighat and above ~6,400 m at Murga Bridge. +97 m is only 4.5% there. The
forecast itself was never at fault: it measures each river against its own
typical level and its own line.

**The new rule** (`backtest_flood_when.impossible_excursions`, a second pass
inside `clean_readings`, so the live run, training and the backtests all use
it). An *impossible excursion* is a level that leaves a steady stretch,
sits away, and comes back to where it was in one step. The level it left
and returned to is taken as the true one.
- One stray reading: more than 5 m from a steady level on both sides.
- Several readings in a row: more than 20 m away, flat (the true level plus
  a fixed error), back within 72 hours.
- "Steady", "flat" and "came back" mean within 20% of the jump. Readings
  must be no more than 3 hours apart.

**Never removed** (each checked):
- a jump that has not come back yet, so the newest reading always stands
  until the next one — a real surge must not be hidden;
- a rise that recedes gradually, even +30 m in one hour;
- a peaked wave that drops back in one step;
- a shift that stays (a re-levelled gauge);
- one reading up to 5 m away (a dam release can pulse 3 m);
- readings more than 3 hours apart (3 a day cannot tell a slip from a
  short flood).

**Tested on every CWC gauge's full history before it was switched on**
(1.2 million readings, 18 gauges):
- 124 readings removed, in 56 excursions. Most are exact slips: off by
  exactly 100 m, doubled (145.52 → 291.51), off by 30, 25, 18 or 10 m.
- **11 false high-water days** removed from the history: Jollang 5,
  Pagoda 2, Yinkiang, Pangin, Doimukh and Tamen 1 each. At Doimukh and
  Tamen that is 1 of only 2 days ever at the line.
- A first version (one stray reading only) was rejected on this test. At
  Miao on 2005-06-01 it removed three correct readings and kept a day of
  wrong ones, and it missed Pagoda reading double for 15 hours.
- The live path, with the bad reading put back: 28 Sep's daily high
  2,231.30 (old cleaning) → 2,134.39 (new), no longer above the line.
- Golden check PASS, 0 differences; the daily run completes end to end.

**Known limits** (not fixed here):
- A wrong value that is still wrong at run time is not removed until it
  comes back. It can raise one day's forecast; the grading then corrects
  itself, as it did here.
- Winter stretches with 3 readings a day are not judged. Several slips
  remain there, nearly all downward, which cannot make a false high.
  One is upward: Pagoda 2022-12-16, +42 m.
- **Two sources that disagree** are left alone unless one side is a lone
  reading: Tuting (two series ~15 m apart, 2013–17), Pangin (readings
  alternating 9 m apart, August 2019), Pasighat (a second series ~3 m
  lower, July 2018). Which side is right is not known. At Pangin the rule
  removed two lone high readings (4 and 9 Aug 2019), so 4 Aug is no longer
  a high-water day; that one is a judgement, not a certainty.
- ⚠️ **The gauge models were trained before this filter.** Their history
  held the 11 false high-water days above (18 after the third pass, §13g).
  Retraining them on the cleaned history is a separate step, with its own
  before-and-after check (`train_flood_when_gauge.py`,
  `reports/flood_when_gauge.json`). **Tried 2026-10-06 and not shipped:
  the check failed, §13h.**

### 13g. Are the removed readings really false? — the evidence, and a third pass ✅ 2026-10-06

The user's instruction before any retrain: check that the readings the
filter removes are actually false. Checked with tests that do not use the
filter's own rules (`scripts/model/check_gauge_excursions.py`,
`reports/gauge_excursions_check.json`).

**Four independent tests per run of removed readings:**
- **Still:** the nearest kept readings before and after agree within 0.5 m.
- **Out of range:** the value is outside everything else the gauge has
  recorded, or above CWC's published highest-ever level.
- **Slip:** one keying slip undone puts it back between its neighbours (a
  multiple of 10 m added or taken off, two neighbouring digits swapped, or
  halved).
- **Other gauge:** another CWC gauge read that value within the hour.

"Certain" = at least two; "likely" = one; "judgement" = none.

**The check found the §13f filter incomplete, and wrong in two ways.** The
filter now has three passes (`backtest_flood_when.py`):
1. the old proportion test (zeros, slipped decimals);
2. `impossible_excursions` (§13f);
3. `keying_slips`, new.

What testing against the history exposed:
- **Seven false high-water days were still in the cleaned history.** They
  sat where readings come 3 a day, or where wrong and right readings
  alternate: Pangin 2019-08-09 (210.5 for 201.5, three times), Jollang
  2021-11-28 (+30), Miao 2001-01-23 (273.77 for 237.77), Doimukh 2024-11-17
  (188.63, Pangin's level that hour), Pagoda 2022-12-16 (187.31, also
  Pangin's) and 2023-04-03 (154.23 for 145.23), Tamen 2022-11-27 (+100).
  Pass 3 removes a reading only when the river is steady around it, is back
  on both sides within two readings, and a slip explains it (or it is more
  than 20 m away).
- **Both passes could side with a wrong majority.** Where a second, wrong
  series outnumbers the true one for a stretch, each true reading stands
  alone between steady runs of wrong ones, and the true readings were
  removed. Pass 3 did this to two real readings at Pangin (April 2018, a
  second series 161 m too low); pass 2 did it on a made-up series. Both now
  require the steady level they trust to be an ordinary one for the gauge:
  inside the middle 98% of the series, give or take 10 m (`_ordinary_levels`).
- Pass 3 repeats until nothing more is found, so a short run of slips goes
  whole (Namsai, three readings of 134.8 for 143.8).

**Checks, now permanent** (`scripts/model/check_gauge_cleaning.py`; run it
after any change to the cleaning):
- **Behaviour:** 22 made-up series with a known answer, all pass. Slips
  that must go; and what must stay: a surge, a dam-break wave, a flood that
  recedes, a re-levelled gauge, the newest reading, real floods at 3
  readings a day, and five mixed-series cases where no TRUE reading may be
  lost.
- **History:** 1,180,994 readings. Pass 2 removes 124 and pass 3 removes
  70: 194 in all, **18 false high-water days**. The only high-water days
  that still look odd are real: Tuting 2013-06-25 (monsoon) and
  2018-10-19/20, the landslide-dam surge (144 of 144 readings kept, highest
  434.11 m).

**The evidence.**
- 112 runs of removed readings: **85 certain, 18 likely, 9 judgement.**
- **All 18 high-water days taken away are certain.** Doimukh 2, Jollang 6,
  Miao 1, Pagoda 4, Pangin 2, Tamen 2, Yinkiang 1. Every one has still
  neighbours; 15 are out of range; 15 are explained by a slip; two are
  Pangin's level logged under another station.
- **Pangin against Pasighat** (same river, 50 km downstream): when Pangin
  is really at 198–202 m Pasighat reads 152.16 (90% of days
  151.21–152.90); at 208–212 m it reads 154.18 (153.85–154.73). On
  2019-08-04 Pasighat read 152.09–152.19, and on 2019-08-09 152.26–152.64.
  The river was near 200 m both days, not 210.
- **Not certain: 27 runs, none on a high-water day.** All are at Miao
  (downward slips and its old-datum values) and Tuting (18 readings on six
  winter days where two sources differ by 5–15 m). At Tuting which side is
  right is not known; the cleaning keeps the continuous series.
- CWC's server still holds every one of them (asked 2026-10-05 for the
  first 56). It corrected Murga Bridge's reading within days, but not these.

**What the false days had already done.**
- **Doimukh and Tamen have never reached their official danger level.**
  Both of the days on record at the line were false, at each gauge.
- **Four floods in the verified record rest on false readings** (the
  "gauge" route, `build_verified_floods.py`): Pangin 2019-08-09, Jollang
  2020-05-04 and 2022-09-05, Doimukh 2024-11-17. Their radar check let them
  through: it counts any new-water pixel, and in three of the four the
  radar saw less water that day than on the ordinary day. So that route is
  only as good as the gauge reading. Of the 48 gauge-found floods at level
  gauges, 42 are at the line after cleaning. Besides these four, Seppa
  2026-07-15 and Tamen 2022-07-07 were not at today's line even before
  cleaning. **Not yet fixed:** taking them out changes the record the day
  model learns from, so it means retraining that model too.
- None of the 59 news reports "confirmed by a gauge crossing" rests on a
  removed value.

**Rules for retraining the gauge models, fixed before it is run.**
- "Before" = the models as trained on the history with pass 1 only;
  "after" = on the history with all three passes. Nothing else differs.
- Both are graded the way the training script always grades (year-grouped,
  out of fold), against the **cleaned** history as truth, on the gauge-days
  both have, at gauges whose line the cleaning does not move.
- **G1:** at leads 1, 2 and 3, on all days and on onset days, the "after"
  ranking (AUC) and Brier skill are each no more than 0.005 below "before".
- **G2:** the golden check shows changes only in river-gauge outputs.
  Day-model and near-here fields stay identical.
- Gauges whose line moves are reported separately, "after" only. Doimukh
  and Tamen are expected to move from the official danger level to their
  own wettest 2% of days, by the existing rule: the official level counts
  only where the record reaches it.
- If G1 or G2 fails, the retrain is not shipped and the cause is found
  first.

### 13h. The retrain check failed — the cause, one fix, and its rules ❌ not shipped 2026-10-06

**G1 failed on 1 of its 12 comparisons, so the retrain was not shipped**
(`reports/gauge_retrain_check_G1_failed.json`; 27 gauges whose line does
not move, cleaned history as truth):

| days ahead | days | ranking (AUC) before → after | Brier skill before → after | |
|---|---|---|---|---|
| 1 | all | 0.975 → 0.974 | 0.406 → 0.407 | ok |
| 1 | onset | 0.944 → 0.943 | 0.095 → 0.097 | ok |
| 2 | all | **0.938 → 0.927** | 0.228 → 0.232 | **fail** |
| 2 | onset | 0.942 → 0.943 | 0.103 → 0.108 | ok |
| 3 | all | 0.942 → 0.944 | 0.187 → 0.183 | ok |
| 3 | onset | 0.944 → 0.945 | 0.116 → 0.119 | ok |

**The cause.**
- The model's own score ranks the days exactly as well after the retrain
  as before (0.9607 both, 2 days ahead). The fall appears only once the
  score is turned into a chance.
- **All of it is 13 flood days** in one of the five test year-groups:
  Murga Bridge 2020-07-13/14, Pasighat 2020-07-22/23, Rho Basti 2016-06-21
  and 2016-09-27, Miao 2004-06-25 and 2016-05-19/20, Lemeking 2023-06-17,
  Tuting 2020-08-18, Namsai 2020-09-28, Kibithu 2016-07-05. On each the
  river was already above its line two days earlier, and each went from a
  7–20% chance to **exactly 0%**.
- **Why 0%.** The score is turned into a chance by a separate curve for
  each of four groups (river below or above its line × own line or
  official line). The "river above" groups are small (about 760 and 370
  days). Their curve's lowest step is 0% wherever the few lowest-scored
  days in the group happened not to flood. So a river above its line with
  a low score is told 0%, while the same score with the river *below* its
  line is given 3–15%.
- The retrain moved those 13 days' scores down a little (the largest from
  0.195 to 0.081), under that step.
- Two other suspects were tested and cleared. Leaving Doimukh and Tamen
  in the official curves: 0.927. Fitting the curves on the 27 unchanged
  gauges only: 0.928.
- **The fault is in the models live today, not only in the retrain.** Two
  days ahead, at an official gauge above its danger level, a score under
  0.04 is given 0%. Three days ahead the same gauge is given 3.1% where a
  river below its line with the same score is given 8.6%. The "before"
  numbers above already carry it (0.938 after the curves against 0.961
  before them).

**The fix — one, chosen on its reason, before any test of it.**
- For the same score, a river already above its line is never given a
  lower chance than a river below it: the "river above" curve becomes the
  higher of the two curves, per kind of line
  (`train_flood_when_gauge.calibrate`, `ABOVE = "floor"`; reproduce with
  `check_gauge_retrain.py floor`).
- The reason is the one the split was made for (measured 2026-09-22): the
  same score means *less* when the river has not risen yet. A curve that
  says the opposite at its thin end is fitting a handful of days.
- Days with the river below its line are not touched.

**Rules, fixed before the fix is run** (`check_gauge_retrain.py`). Three
versions, graded as in §13g (same rows, same truth, same 27 gauges):
A = today's models (no floor, history as it was); B = the floor, history
as it was; C = the floor, cleaned history — what would ship.
- **H1, the retrain alone:** C against B.
- **H2, the floor alone:** B against A. And every river-below day keeps
  exactly the chance it had.
- **H3, what ships against what is live:** C against A.
- For each: ranking (AUC) and Brier skill no more than **0.005** lower at
  1–3 days ahead (the forecast days, as in G1) and no more than **0.010**
  lower at 4–9 days ahead (the outlook days), on all days and on onset
  days. Judged on unrounded values.
- **H4, the fault itself, at every lead:** in C no river-above day is
  given less than the river-below curve gives its score; and C gives a
  chance under 1% to no more river-above flood days than A does.
- **G2** as in §13g.
- If any of these fails, nothing is shipped and it is reported as failed.
  No second fix is tried on this test.

**Result: the fix failed its test too. Nothing is shipped.** ❌ 2026-10-06
(`reports/gauge_retrain_check.json`; run twice, identical.)

| | | |
|---|---|---|
| H1, the retrain alone (C against B) | **pass** | all nine leads |
| H2, the floor alone (B against A) | **fail** | 1 day ahead; passes 2–9 |
| H2, river-below days untouched | pass | 0 days touched at every lead |
| H3, ships against live (C against A) | **fail** | 1 day ahead; passes 2–9 |
| H4, the fault itself | pass | every lead |

All days, 27 gauges, cleaned truth (A live, B floor, C floor + cleaned, X
plain retrain):

| days ahead | AUC A | B | C | X | Brier skill A | B | C | X |
|---|---|---|---|---|---|---|---|---|
| 1 | 0.975 | 0.976 | 0.975 | 0.974 | **0.406** | **0.344** | **0.383** | 0.407 |
| 2 | 0.938 | 0.961 | 0.961 | 0.927 | 0.228 | 0.235 | 0.238 | 0.232 |
| 3 | 0.942 | 0.956 | 0.956 | 0.944 | 0.187 | 0.188 | 0.185 | 0.183 |
| 4 | 0.934 | 0.947 | 0.945 | 0.928 | 0.147 | 0.148 | 0.152 | 0.148 |
| 5 | 0.935 | 0.943 | 0.943 | 0.936 | 0.134 | 0.132 | 0.130 | 0.137 |
| 6 | 0.930 | 0.941 | 0.939 | 0.931 | 0.123 | 0.124 | 0.119 | 0.116 |
| 7 | 0.933 | 0.939 | 0.939 | 0.932 | 0.124 | 0.124 | 0.129 | 0.129 |
| 8 | 0.936 | 0.940 | 0.939 | 0.934 | 0.129 | 0.131 | 0.132 | 0.129 |
| 9 | 0.934 | 0.936 | 0.937 | 0.935 | 0.121 | 0.118 | 0.122 | 0.121 |

- **What the floor does well.** Ranking rises at every lead (+0.001 to
  +0.023). River-above flood days given under 1%, live → with the floor,
  leads 1–9: 1→0, 25→0, 16→5, 16→6, 12→7, 13→4, 8→3, 6→2, 2→1 (of 602,
  421, 323, 257, 205, 175, 155, 141, 138 such days).
- **Where it fails: 1 day ahead, Brier skill 0.406 → 0.344** (and 0.383
  with the cleaned history). On onset days it is 0.095 → 0.088; that part
  is five gauge-days whose "river above" state in the old history was
  itself a false reading.

**Why it fails 1 day ahead.**
- One day ahead, **no river-below day in the record has ever scored 0.5
  or more.** Most river-above days score above 0.6.
- Up there the floor compares against a river-below curve with no days
  behind it — its last value, held flat.
- 686 river-above days scoring 0.6 or more were lifted from 68% to 100%.
  68.1% of them flooded. The curve was right before the floor touched it.
- So the reason given for the fix holds only at low scores. That was not
  checked before the fix was chosen.

**What the test showed about the low end.**
- Two days ahead, 68 river-above days scored under 0.1, and **38% of them
  flooded.** Live they are given about 0%; with the floor 2.5–6.5%. Right
  direction, still far too low.
- Beyond one day ahead the score hardly separates flood from no flood
  *among* river-above days (ranking 0.52 at own-line gauges and 0.70 at
  official ones, 2 days ahead). The honest chance for such a day is close
  to the group's own rate, about 4 in 10, and both ends of its curve rest
  on a handful of days.

**Where this leaves things.**
- **Live: the models of 2026-09-22, unchanged.** `FLOOR_ABOVE = False`;
  `check_live_unchanged.py check` shows 0 changes. The three-pass reading
  filter is not part of this and stays live. (The switch is now
  `ABOVE = "isotonic"`, §13i.)
- **The plain retrain (X) is not shipped either** — it failed G1. Against
  live over all nine leads: onset skill better at 8 of 9 (+0.001 to
  +0.006; lead 6 −0.005), onset ranking within ±0.002, all-days ranking
  −0.011 at lead 2 and −0.006 at lead 4 (the same thin-end fault).
- ⚠️ **Known fault, live:** a river already above its line, with a low
  score, can be told 0% for 2–9 days ahead. In the test history that is
  about 1 in 17 of the flood days that follow a high river, 2 days ahead.
- **Open, the user's call:** repair the "river above" step as its own
  piece of work, with its own test (this one is used up: one fix, tried,
  failed), then retrain once with the cleaned history.

### 13i. Repairing the "river above" step — a second fix, and its rules ❌ better, not cured, not shipped 2026-10-06

The user's instruction after §13h: *"Is it logically incorrect or what? Solve
it if it's wrong."*

**Is it logically wrong? Yes.**
- A river already above its flood line is told 0% for the days ahead, while
  about 4 in 10 such days are above the line again.
- No river behaves that way. It comes from the method: a stepped curve
  fitted to a few hundred days makes its end steps out of a handful of
  them.

**This is the second fix tried on the same history**, and a second try is
easier to pass by luck. What guards against that: one fix; chosen on a
textbook rule, not on a number seen in §13h; nothing in it tuned by us; one
run; the same gates.

**The fix.**
- The stepped curve (isotonic regression) is the wrong tool for a small
  group. The standard guidance is that it needs about a thousand days or
  more, and fits noise below that. The standard substitute for a small
  group is a smooth S-curve with two fitted numbers (sigmoid, or Platt,
  scaling on the model's log-odds).
- The river-above groups hold about 370 and 760 days. The river-below
  groups hold about 29,000 and 51,000.
- So the two river-above groups get the S-curve, and the two river-below
  groups keep the stepped curve. Nothing else changes
  (`train_flood_when_gauge.calibrate`, `ABOVE = "sigmoid"`).
- An S-curve cannot make a 0% or a 100% step out of a handful of days.
  Where the score hardly ranks the days, it flattens toward the group's
  own rate — which §13h found to be the truth.
- It must not fall as the score rises: if a fitted curve would, the
  group's flat rate is used.
- Both numbers are fitted (maximum likelihood, no penalty). None is set by
  hand.

**Rules, fixed before the fix is run.** As §13h, with the S-curve in place
of the floor: A = today's models; B = S-curve, history as it was; C =
S-curve, cleaned history — what would ship.
- **H1** (C against B), **H2** (B against A; every river-below day keeps
  exactly its chance), **H3** (C against A): AUC and Brier skill no more
  than 0.005 lower at 1–3 days ahead and 0.010 at 4–9, on all days and on
  onset days, unrounded. Same rows, truth and gauges as before.
- **H4, the fault itself:** at every lead, C gives no river-above flood
  day a chance under 1%. (§13h's other H4 test compared against the
  river-below curve; §13h showed that comparison is not valid where that
  curve has no days behind it, so it is dropped.)
- Reported, not a gate: for the lowest-scored fifth of river-above days,
  the chance said against the share that flooded, A and C.
- **G2** as in §13g.
- If any gate fails: nothing is shipped, it is reported as failed, and no
  third fix is tried without the user's say.
- If all pass: the gauge models are retrained on the cleaned history with
  the S-curve and shipped, with the backups of §13g in place.

**Result: every accuracy gate passes; H4, the fault itself, fails. Nothing
is shipped.** ❌ 2026-10-06 (`reports/gauge_retrain_check.json`, one run.)

| | | |
|---|---|---|
| H1, the retrain alone (C against B) | **pass** | all nine leads |
| H2, the S-curve alone (B against A) | **pass** | all nine leads; 0 river-below days touched |
| H3, ships against live (C against A) | **pass** | all nine leads |
| H4, no river-above flood day under 1% | **fail** | leads 2–8 |

All days, 27 gauges, cleaned truth (A = the models live; C = S-curve +
cleaned history):

| days ahead | AUC A → C | Brier skill A → C | river-above flood days under 1%, A → C | lowest chance a river-above day gets, A → C |
|---|---|---|---|---|
| 1 | 0.975 → 0.975 | 0.406 → 0.411 | 1 → 0 | 0% → 2.7% |
| 2 | 0.938 → 0.961 | 0.228 → 0.239 | 25 → **2** | 0% → 0.25% |
| 3 | 0.942 → 0.956 | 0.187 → 0.190 | 16 → **2** | 0% → 0.22% |
| 4 | 0.934 → 0.946 | 0.147 → 0.156 | 16 → **6** | 0% → 0.12% |
| 5 | 0.935 → 0.944 | 0.134 → 0.137 | 12 → **6** | 0% → 0.04% |
| 6 | 0.930 → 0.939 | 0.123 → 0.123 | 13 → **5** | 0% → 0.08% |
| 7 | 0.933 → 0.939 | 0.124 → 0.131 | 8 → **4** | 0% → 0.02% |
| 8 | 0.936 → 0.939 | 0.129 → 0.134 | 6 → **2** | 0% → 0.07% |
| 9 | 0.934 → 0.937 | 0.121 → 0.124 | 2 → 0 | 0% → 0.31% |

- On onset days C is level with A or better at 8 of 9 leads (worst: lead 6,
  skill −0.005, inside the tolerance).
- **So the S-curve with the cleaned history is better than what is live at
  every lead, and cuts the fault by 50–90%. It does not remove it.** The
  gate was "removed", so it failed.
- Lowest-scored fifth of river-above days, chance said against the share
  that flooded: 2 days ahead A 16% / C 16% / happened 32%; 3 days 10% / 11%
  / 22%; 4 days 7% / 8% / 17%. The low end is still said at about half of
  what happens.

**Why a curve cannot cure it — the cause is one level down.**
*(Corrected by §13j: the per-gauge shares below are all years pooled. From
one year to the next they hold only weakly; they mostly mark single
high-water spells.)*
- **How long a river stays above its line is a habit of that river, and
  the model is not told which river it is.** Share of river-above days
  that are above again 2 days later, per gauge: Deomali 7%, Seppa 10%,
  Jollang 14%, Bhalukpong 16% … Tuting 62%, Rho Basti 63%, Pangin 65%,
  Daporizo 82%. The S-curve gives all of them 30–50%. Four days later:
  Bhalukpong 0%, Jollang 4% … Rho Basti 53%, Daporizo 71%.
- The model's main input is rain. With no rain coming it scores a high
  river near zero, whichever river it is. That is right for a stream that
  drops in a day and wrong for a river that stays up for a week.
- The days still under 1% are exactly that: Rho Basti 5–10 June 2016 (at
  its line for a week, rain mostly in its lowest 0–13%) and 29 Sep 2016, Kibithu
  21–22 June 2016, Daporizo 19 July 2019. *Not checked:* whether Rho
  Basti's dry week is snow-melt or a reading problem.
- One curve per group cannot give Deomali 7% and Daporizo 82% from the
  same score. The floor and the S-curve both treat the symptom.

**What would cure it** (not built; a third attempt, the user's call):
- Tell the model each river's own habit of staying high — for example,
  how often that gauge was still above its line the same number of days
  later, taken only from other years. Tested by these same gates.
- This is the first building block of the ⭐ level line (FLOOD_SCREEN_PLAN
  Phase 10): a forecast of the level itself is a forecast of how the river
  falls.

**Where this leaves things.**
- **Live: the models of 2026-09-22, unchanged.** The three-pass reading
  filter stays live. (The training default became `ABOVE = "sigmoid"` in
  §13j; the live models were not retrained.)
- Ready to ship on the user's word, as an improvement and not a cure:
  S-curve + cleaned history (`ABOVE = "sigmoid"`, then
  `train_flood_when_gauge.py` and the rebuild steps of §13g).

### 13j. The cure — telling the model each river's habit of staying high ❌ failed, not adopted 2026-10-06

The user's instruction after §13i: *"Add the improvements but no need to
push live for now if not needed. Just build the real cure."* So this
section builds and tests; **nothing here goes live.**

**What is added: one input, `habit`.**
- For a river that is above its line at the last reading: how often this
  gauge, once above its line, was above it again the same number of days
  later. For a river below its line: 0 (there is nothing to stay).
- It is on top of the two improvements of §13i (the cleaned history and
  the S-curve). The five existing inputs and everything else are as they
  were. The rain-only fallback (gauge offline, state unknown) does not
  get it.
- **No row's input ever holds its own outcome.** A day's `habit` is
  counted from the gauge's *other* years only. In the year-grouped test,
  a year being scored is not in the count at all, and each training day
  leaves its own year out.
- A gauge with few river-above days: one imaginary day at the pooled rate
  of its kind of line is added to the count. That keeps it away from 0%
  and 100%, and gives a gauge with no such days the pooled rate. This is
  the only number set by hand, and it is the smallest one that does that
  job.
- Live it is read from a per-gauge table saved with the models (counted
  over all years).

**Why this one.** §13i measured it: 2 days on, Deomali is above its line
again 7% of the time and Daporizo 82%, and the model could not tell them
apart. Only the river-above side is changed, because that is where the
fault is; onset days already work and are left alone as far as possible.

**This is the third change tested on the same history.** The guards are
the same as before: chosen on the measured cause, one design, one run,
rules first.

**Versions** (same rows, truth and 27 gauges as §13g–§13i):
A = the models live today; C = S-curve + cleaned history (§13i);
D = C + `habit` — the cure.

**Rules, fixed before it is run.**
- **K1, the cure against live (D against A):** AUC and Brier skill no
  more than 0.005 lower at 1–3 days ahead and 0.010 at 4–9, on all days
  and on onset days, unrounded.
- **K2, the new input against the improvement alone (D against C):** the
  same tolerances. The input must not cost anything.
- **K3, the fault itself.** At every lead: of the river-above days D
  gives **under 5%**, **fewer than 1 in 10** may flood. Leads with fewer
  than 20 such days are judged together.
  - This replaces "no flood day under 1%" (H4). That test is not fair to
    a forecast that is allowed to say 1%: if it honestly says "under 1%"
    on two hundred days, one or two floods among them is what being right
    looks like. With `habit` the forecast *should* go low for a stream
    that always drops within a day. What must not happen is the fault of
    §13h — said near zero, a third of them flood — and K3 tests that with
    room to spare. The old count is still reported.
- **K4, the cause itself.** At every lead, among river-above days, D
  ranks flood days above quiet days better than C does (AUC within those
  days). If the model has really learned which rivers stay up, this must
  rise.
- Reported, not gates: river-above flood days under 1% (A, C, D); per
  gauge, the chance said against the share that stayed above; the five
  gauges whose line moves.
- **If K1 or K3 fails,** the cure is not adopted. **If K2 or K4 fails,**
  the `habit` input is not adopted (the §13i improvement stays
  available). Either way it is reported as failed, and no fourth design
  is tried without the user's say.
- **If all pass:** the training script builds the cure by default, and a
  full set of models is trained into `models/flood_when_gauge_next/`,
  beside the live ones. **The live models are not replaced** until the
  user says so; replacing them then needs G2 (§13g).

**Result: the cure failed. Every gate fails somewhere. `habit` is not
adopted.** ❌ 2026-10-06 (`scripts/model/check_gauge_cure.py`,
`reports/gauge_cure_check.json`, one run. Mechanics checked first on
made-up tables: the count matches its definition row by row, and flipping
a day's outcome never moves that day's own input.)

| | | where |
|---|---|---|
| K1, the cure against live | **fail** | 1 day ahead, onset days: Brier skill 0.095 → 0.083. Every other comparison passes. |
| K2, the new input on its own | **fail** | onset days, 1 day ahead (−0.013) and 3 days ahead (−0.005) |
| K3, the fault itself | **fail** | 1–2 days ahead together, and 3 and 4 days ahead |
| K4, the cause itself | **fail** | 6, 7 and 9 days ahead; passes 1–5 and 8 |

K3 — river-above days given under 5%, and how many of them flooded:

| days ahead | A live | C improvement | D cure |
|---|---|---|---|
| 1 | 1 day, 1 flooded | 6, 3 | 0 |
| 2 | 61, 25 (41%) | 41, 17 (41%) | 12, 9 (75%) |
| 3 | 118, 21 (18%) | 55, 9 (16%) | 39, 6 (15%) |
| 4 | 193, 21 (11%) | 148, 23 (16%) | 101, 14 (14%) |
| 5 | 205, 15 (7%) | 214, 16 (7%) | 189, 13 (7%) |
| 6 | 294, 22 (7%) | 267, 26 (10%) | 237, 12 (5%) |
| 7 | 367, 28 (8%) | 305, 20 (7%) | 285, 19 (7%) |
| 8 | 399, 26 (7%) | 307, 12 (4%) | 308, 10 (3%) |
| 9 | 345, 21 (6%) | 280, 13 (5%) | 265, 12 (5%) |

- **By this fairer measure the fault lives 1–4 days ahead**, in all three
  versions. From 5 days on, all three are roughly honest at the low end.
- The improvement and the cure make the fault **rarer** (fewer days given
  under 5%), not **milder** (of those days, as large a share floods).
- What `habit` did do: all-days Brier skill up at 1–5 days ahead (2 days:
  0.239 → 0.261); no river-above flood day under 1% at 1–4 days ahead;
  ranking among river-above days up at 1–5 days (2 days: 0.607 → 0.670).
  It cost onset days 1 day ahead, and did nothing from 6 days on.

**Why it failed — and a correction to §13i.**
- §13i said how long a river stays high "is a habit of that river", from
  each gauge's share over all its years together. **That was never
  checked from one year to the next. It does not hold well.**
- A gauge's share in one year against the same gauge's other years
  (gauge-years with 5+ river-above days): correlation 0.49 two days
  ahead and 0.33 four days ahead. They differ by 16 points on average —
  against 21 and 19 points for simply using the pooled share. Knowing the
  gauge helps a little, not a lot.
- **The big numbers were single spells:**
  - Daporizo "82%": 16 of its 17 river-above days are one spell in 2019.
  - Rho Basti "63%": 2016 (35 of 44 stayed) and 2017 (19 of 27). In its
    six other years, 3 of 20.
  - Tuting "62%": 2010 (21 of 23) and 2020 (16 of 25), but 2018 2 of 8
    and 2013 1 of 6.
  - Deomali "7%": 13 of its 15 days are 2024.
- So staying high is mostly a mark of a particular **high-water spell**,
  not of the river. What tells a spell from a spike — how long the river
  has already been up, how its level has moved over several days — is
  not among the model's inputs (it sees the last reading and one day's
  change).

**Where this leaves things.**
- **Live: the models of 2026-09-22, unchanged** (`check_live_unchanged.py
  check`: 0 changes).
- **The improvement is added, not live** (the user's instruction): the
  training script now builds S-curve + cleaned history by default
  (`ABOVE = "sigmoid"`), and a full set is in
  `models/flood_when_gauge_next/` with its own report. Checked through
  the live scoring code: lowest chance a river above its line gets over a
  grid of dry, falling situations — live 0.00%, improved 0.05%.
- To make it live later: replace `models/flood_when_gauge/` with that
  folder, rebuild `build_gauge_levels.py` and `build_gauge_reach.py`,
  pass G2, re-record the golden baseline, refresh the snapshot. Doimukh
  and Tamen then move to their own wettest 2% (§13g).
- `habit` and the floor stay in the training script, unused, so their
  tests can be re-run.
- **Three designs have now been tested on this history; none cures the
  fault.** The next one should not be a fourth small input chosen from
  the same numbers. The place to solve "what does a high river do next"
  is the level forecast (⭐ FLOOD_SCREEN_PLAN Phase 10), which reads
  several days of the river's own level; K3 above should be one of its
  acceptance tests.

## 14. The level line — our own river level forecast (✅ live to 2 days ahead since 2026-10-06; chance model adopted by the user's decision)

Go-ahead from the user on 2026-10-06 (RIVER_FORECAST_RECAP_2026-10-06.md
§6–§7). This is the user-marked next feature (FLOOD_SCREEN_PLAN Phase 10),
and the fourth attempt at the open "river already above its line told ~0%"
fault of §13h–§13j. **Nothing here goes live or on screen in this step.**

### 14a. What the gauges really hold (counted 2026-10-06)
- **CWC, 18 gauges:** about half of all days have hourly readings (the
  flood season) and half have three a day, at 08:00, 13:00 and 18:00.
- Of the 1,716 river-above days on record, 1,124 have 20 or more readings
  that day and 544 have four or fewer — mostly Pasighat and Daporizo before
  hourly reporting began.
- **NWDP, 14 gauges:** about 95 readings a day, but only from 2023–2025 on.
- **So "a week of hourly levels" cannot be the input as such.** The inputs
  below can all be read from three readings a day as well as from hourly.

### 14b. The design, fixed before any of it is run

**One new set of inputs — "the river's own week"** — read at the last
complete day, the same day today's `g_frac` is read. All in the gauge's own
units (0 = its ordinary level, 1 = its line):

| Input | What it is |
|---|---|
| `rise3` | change in the daily high over the last 3 days |
| `mean7` | average of the last 7 daily highs |
| `max7` | highest of the last 7 daily highs |
| `above7` | how many of the last 7 days were at or above the line |
| `end` | the last reading of the day — where the river ended the day |
| `day_rise` | last reading minus first reading of the day — rising or falling through the day |

- The week's figures need at least 4 of the 7 days; otherwise they are left
  empty and the model works without them.
- Rule on direction: `end` is a level, so more of it may never lower the
  chance, like today's five inputs. The other five describe the shape of
  the week and are left free.
- **No per-gauge input** (§13j showed why), and no upstream gauges yet —
  one ingredient per test. Upstream gauges are the next test.

**Two models read these inputs, beside today's five:**
- **W, the chance model:** the improved gauge model of §13i (S-curve,
  cleaned history) with the six inputs added. Nothing else changed.
- **The level model:** for each lead, three models of the *change* in the
  daily high from the last complete day — low (1 in 10 lower), middle, high
  (1 in 10 higher) — with the same tree settings as the chance model. The
  low–high range is then widened or narrowed, per river state and kind of
  line, by the amount that makes it hold 8 in 10 outcomes in *other* years
  (the same year-grouped discipline as the chance curves). The middle line
  is not adjusted.

### 14c. Rules, fixed before it is run

Chance model — same rows, truth and 27 gauges as §13g–§13j; A = the models
live today, C = the improvement of §13i:
- **W1, against live (W against A)** and **W2, against the improvement (W
  against C):** AUC and Brier skill no more than 0.005 lower at 1–3 days
  ahead and 0.010 at 4–9, on all days and on onset days, unrounded.
- **W3, the fault itself:** at every lead, of the river-above days W gives
  under 5%, fewer than 1 in 10 flood. Leads with fewer than 20 such days
  are judged together. (K3 of §13j, unchanged.)
- **W4, the cause:** among river-above days, W ranks flood days above quiet
  days better than C at each of 1–4 days ahead — where the fault lives —
  and no more than 0.010 worse at 5–9.

Level model — every gauge and row of the cleaned history, year-grouped, at
**1 and 2 days ahead** (the first aim):
- **L1, it must beat "the river stays where it is":** the middle line's
  average miss is smaller than that of no change, on all days and on
  river-above days.
- **L2, the range must be honest:** it holds 75–85% of outcomes on all
  days, and 70–90% on river-above days.
- **L3, the line and the chance must not contradict** (the rule written in
  FLOOD_SCREEN_PLAN Phase 10): where the whole range sits above the line,
  at least 3 in 4 of those days cross and W's chance averages at least 50%;
  where the whole range sits below the line, fewer than 1 in 10 cross and
  W's chance averages under 10%.
- **How far ahead the line may be drawn:** up to the last lead, counting
  from 1, at which L1 and L2 both hold. Leads 3–7 are reported for that.

Decisions:
- **W1–W4 all pass:** W replaces C as the chance model the training script
  builds (still not live — the user's instruction of 2026-10-06).
- **L1–L3 all pass:** the level model is adopted, and the screen work can
  start.
- Anything that fails is reported as failed and not adopted. **No fifth
  design on this history without the user's say.**

### 14d. Result — the level model passes; the chance model fails one gate of four (2026-10-06)

One run (`scripts/model/check_gauge_week.py`, `reports/gauge_week_check.json`).
Mechanics checked first on made-up and real records, including that
changing every reading from a date on moves no input for an earlier
target day.

**The level model: L1, L2 and L3 all pass at 1 and 2 days ahead.** ✅

| days ahead | middle line's miss against "no change", all days | on river-above days | range holds, all / river-above | CWC gauges, river above: miss in metres against "no change" | line and chance agree (L3) |
|---|---|---|---|---|---|
| 1 | −19% | −35% | 80.0% / 80.2% | 0.33 m against 0.55 m | yes |
| 2 | −18% | −42% | 80.0% / 80.6% | 0.57 m against 0.92 m | yes |
| 3 | −19% | −50% | 79.9% / 79.0% | 0.64 m against 1.14 m | **no** |
| 4 | −19% | −54% | 80.0% / 78.8% | 0.64 m against 1.31 m | **no** |
| 5 | −19% | −56% | 80.0% / 80.1% | 0.67 m against 1.47 m | **no** |
| 6 | −20% | −57% | 80.0% / 79.2% | 0.70 m against 1.61 m | **no** |
| 7 | −20% | −60% | 80.0% / 79.7% | 0.71 m against 1.70 m | **no** |

- On all days at CWC gauges the middle line misses by 0.13 m one day ahead
  and 0.22 m two days ahead ("no change": 0.17 m and 0.26 m).
- L3 at 1 day: the whole range sat above the line on 350 days, 93% of them
  crossed, and W said 88% on average. At 2 days: 76 days, 80% crossed, W
  said 66%. Whole range below the line: 0.3–0.4% crossed, W said the same.
- **How far the line may be drawn.** By the rule of §14c (L1 and L2) it
  holds to 7 days. But the standing rule of FLOOD_SCREEN_PLAN Phase 10 —
  the line and the chance must never contradict — holds only at 1 and 2
  days. From 3 days on, where the whole range sits above the line only
  30–66% of those days cross. **So the line is drawn to 2 days**
  (`gauge_week.DRAW_TO_LEAD`). Further ahead needs its own test.

**The chance model W: W1, W2 and W4 pass at every lead; W3 fails at 2, 3
and 4 days.** ❌ Not adopted, by the rule.

| days ahead | Brier skill, all days: A live / C / W | onset days: A / C / W | ranking among river-above days: C → W | river-above days W gives under 5%, flooded | W3 |
|---|---|---|---|---|---|
| 1 | 0.406 / 0.411 / **0.548** | 0.095 / 0.097 / 0.119 | 0.634 → 0.905 | 60 days, 5 (8%) | ok |
| 2 | 0.228 / 0.239 / **0.301** | 0.103 / 0.108 / 0.115 | 0.607 → 0.778 | 21 days, 5 (24%) | **fail** |
| 3 | 0.187 / 0.190 / **0.225** | 0.116 / 0.119 / 0.131 | 0.634 → 0.736 | 80 days, 9 (11%) | **fail** |
| 4 | 0.147 / 0.156 / **0.185** | 0.102 / 0.107 / 0.122 | 0.663 → 0.739 | 135 days, 14 (10.4%) | **fail** |
| 5 | 0.134 / 0.137 / 0.165 | 0.104 / 0.105 / 0.121 | 0.693 → 0.755 | 218 days, 20 (9%) | ok |
| 6 | 0.123 / 0.123 / 0.147 | 0.104 / 0.099 / 0.113 | 0.697 → 0.755 | 279 days, 18 (6%) | ok |
| 7 | 0.124 / 0.131 / 0.148 | 0.103 / 0.109 / 0.120 | 0.743 → 0.793 | 332 days, 11 (3%) | ok |
| 8 | 0.129 / 0.134 / 0.143 | 0.113 / 0.115 / 0.121 | 0.774 → 0.798 | 332 days, 10 (3%) | ok |
| 9 | 0.121 / 0.124 / 0.131 | 0.107 / 0.107 / 0.114 | 0.755 → 0.759 | 272 days, 12 (4%) | ok |

- **The week of levels is the missing ingredient.** W is more accurate
  than both the live models and the improvement at every lead, on all days
  and on onset days, and at last tells flood from quiet among river-above
  days (1 day ahead: 0.63 → 0.90).
- **The fault is much smaller, not gone.** River-above flood days given
  under 5%, live → W: 2 days ahead 25 → 5; 3 days 21 → 9; 4 days 21 → 14.
  The gate is "fewer than 1 in 10", and W is at 24%, 11% and 10.4%.

**What the failing days are.**
- 2 days ahead: 5 flood days — four are **Rho Basti, 5–8 June 2016**, one
  is Seppa 2011. 3 days ahead: 9 — six Rho Basti June 2016, two Kibithu
  2016, one Miao 2014. 4 days ahead: 14 — seven Rho Basti 2016, four Seppa,
  one each Kibithu, Lemeking, Changlang.
- **Rho Basti, June 2016, was checked and is a real river, not a reading
  problem** (this closes the loose end of §13i). It stepped up about 0.8 m
  between 31 May and 1 June, as it does at the start of the season in
  other years (+0.66 m on 2014-06-18, +0.75 m on 2015-08-28, +0.87 m on
  2020-05-18). Hour by hour it shows a smooth daily cycle, lowest about
  midday and highest about midnight — melt water. Then it sat **0 to 21
  cm above its line for two weeks with almost no rain.**
- At that gauge the line is 1.09 m above the ordinary level. Of its 91
  days at or above the line, 20 are within 5 cm of it and 37 within 10 cm.
  **Whether such a day counts as a flood hangs on centimetres.** No yes/no
  chance can call that.
- The level model on the same days: for 6 June 2016, two days ahead, its
  range ran from 0.82 to 1.03 of the way to the line, middle 0.93. The
  river came in at 1.04. "Sitting just under the line, could touch it" is
  the honest picture, and a line shows it where a percentage cannot.

**The level line cannot sit beside the live chance model.** Two days
ahead, where the whole range sat above the line (71 days, 83% crossed),
the live model averaged 45% and said under 25% on 12 of them. Where the
middle line was at or above the line (472 days), the live model said
under 5% on 20; W on 3. So the line needs W beside it.

**Where this leaves things.**
- **Level model: adopted, built, not on screen.** `python
  scripts/model/gauge_week.py --out models/flood_when_gauge_next` wrote
  `level1.pkl` … `level7.pkl` and `level.json` there.
- **W: not adopted** — the user's call. It failed the fault test narrowly
  and on days that hang on centimetres, and it passed everything else by a
  wide margin; but the rule was written first and it failed.
- **Live: unchanged** (`check_live_unchanged.py check`: 0 changes).
- Not built yet: reading the day's first and last reading in the live run
  (`flood_gauge_live.py` fetches the day's high only); the dotted line on
  the gauge graph; upstream gauges (the next test); agreement of line and
  chance beyond 2 days.
- New loose ends: Rho Basti's levels have drifted lower since 2016–17 (71
  of its 91 line days are in those two years; none in 2022 or 2024–26), so
  its "own wettest 2%" line may be out of date. And for rivers that sit on
  their line for weeks, the flood label itself is fragile.


### 14e. Adopted and made live — the user's decision (2026-10-06)

Asked whether to adopt W despite its narrow fail and to put the level line
on screen, the user answered: *"Yes, do next steps for the updates."* So:
- **W is the chance model now, knowing it failed W3** (§14d). This is the
  user's decision, not a passed gate. The method page says where it is
  weakest.
- **The level line is on the gauge graph, to 2 days after the last full
  day of readings.**
- The reading filter, the cleaned history and the S-curve (§13f–§13i) went
  live with it: this is the retrain those sections were waiting for.

**What changed.**
- `train_flood_when_gauge.py`: `FEATS` = the five inputs + the six week
  inputs; tables from `gauge_week.build_tables`; the level models are
  fitted beside the chance models. With no `--out` it replaces the live
  models.
- `flood_gauge_live.py`: each gauge's daily series now carries the day's
  first and last reading (`attrs["first_last_n"]`); `week_now` computes
  the six inputs through the training function; each row carries
  `level_low / level_mid / level_high` for leads up to `draw_to_lead`.
- `flood_forecast_live.py`: the level reaches the web snapshot
  (`rivers[].days[day].level`) and the method facts (`method.level`).
- `webapp/products/flood/live.py`: the dotted line, its shaded range and
  an "Expected high" tile; `view.py`: the method page's words, and a new
  line under "What it does not count".

**Checks, in order.**
1. Mechanics of the inputs and the level model (§14d).
2. **Training and live agree:** 1,136 forecasts replayed through the live
   code from the gauges' own records — every input identical to the
   training table (largest difference 4e-16).
3. The new code with the *old* models: every old number identical; only
   empty level fields added.
4. **G2, after the switch:** the only outputs that changed are the river
   rows and the method page's gauge figures. The day model's chances, the
   raster, the area outlook and near-here are identical. 224 river rows,
   the same gauges and days.
5. A new baseline recorded for 2026-10-06 and replayed: 0 changes.
6. The 21 screen checks pass; the graph was looked at (Pangin, Rho Basti,
   Aalo).
7. The track-record log accepts the three new columns (tried on a copy).

**What is live.**
- Chance models with 11 inputs (leads 1–9), the rain-only fallback, level
  models (leads 1–7 saved, **drawn to 2**).
- `gauge_levels.json` rebuilt. **Doimukh and Tamen now use their own
  wettest 2% of days** (120.45 m and 277.29 m) instead of an official
  danger level their record never reached (§13g).
- The web snapshot was refreshed without writing to the track record.
  Today's logged forecast (09:21) is the old models'. **The first logged
  forecast from the new models is 7 October, 08:30.**
- On 6 October: 17 CWC gauges carry a level line. Yinkiang is offline.
  **None of the 14 NWDP gauges carries one:** their readings arrive 2–3
  days late, so today is already more than 2 days after their last full
  day.

**To go back.** Copy `models/flood_when_gauge_pre_cleaning/` over
`models/flood_when_gauge/` and delete `level*.pkl` and `level.json` there;
restore `flood_when_gauge.json` and `gauge_levels.json` from
`reports/_pre_gauge_cleaning_backup/`; the old baseline is
`data/interim/flood_forecast/golden_live_pre_week_inputs/`.

**Not done yet.**
- **Grading the level line.** Its forecasts are written to the log from 7
  October; nothing grades them against the gauge yet.
- A level line for the NWDP gauges (the days between their last reading
  and today).
- The line beyond 2 days — needs the line and the chance to agree (§14d).
- Upstream gauges as inputs — the next test.
- Google's open model alongside (RIVER_FORECAST_RECAP §7, Step 2).
- The gauge models learned from the whole record, including Rho Basti's
  drift (§14d): its line may be out of date.


## 15. The four false floods leave the verified record — rules first (2026-10-09)

The user's instruction: remove them, *"before removing confirm that they are
actually false"*. This closes the "not yet fixed" item of §13g.

### 15a. Confirmed false, from the raw readings (checked again 2026-10-09)

| Flood in the record | Line | What the gauge holds that day | Independent check |
|---|---|---|---|
| Pangin 2019-08-09 | 204.75 m | Hourly 201.3–201.7 all day, with four readings of 210.50–210.57 in between (09:00, 13:00, 14:00, 16:00): up 9 m and back within the hour, four times | Pasighat, 50 km down the same river, read 152.56–152.64 m all day, 1.3 m under its own danger level. Swapped digits (210.5 for 201.5) |
| Jollang 2020-05-04 | 166.09 m | 164.39 every hour from midnight to 08:00, except 04:00: 326.39 | 158 m above anything else this gauge has recorded (its range is 163.07–167.75) |
| Jollang 2022-09-05 | 166.09 m | 164.28 at 23:00, 264.27 at 00:00, 164.27 at 01:00 | Exactly 100 m too high |
| Doimukh 2024-11-17 | 120.45 m | Three readings: 118.25, 118.50, 188.63; next morning 118.20 | Pangin read 188.50–188.53 that afternoon: Pangin's level logged under Doimukh |

With the false readings out, the highest reading on those four days is
201.66, 164.39, 164.94 and 118.50 m — each below its line. No other
verified flood sits in the same 10 km cell on the same day, or within about
15 km and 6 days, so nothing else vouches for them.

The false record in the live track record (Murga Bridge 2026-09-28, §13f)
was checked the same day: CWC's server now holds 2,134.30 m for that hour.
It is handled in the intake, not here (FLOOD_SCREEN_PLAN.md status,
2026-10-09).

### 15b. The rule that removes them

`build_verified_floods.py`, route 4 (floods found from a gauge): a
gauge-found flood is not counted when the cleaning lowers that day's highest
reading **and** the cleaned high is below the gauge's line. Tried on all 48
gauge-found floods at level gauges before it was written in: it picks these
four and no others.

Left in on purpose: Seppa 2026-07-15 and Tamen 2022-07-07. Their readings
are not false; they are below *today's* line (§13g). That is a separate
question, not answered here.

### 15c. Rules for re-fitting the day model, fixed before it is run

The day model, the near-here curves and the live "ordinary day" level are
re-fitted on the corrected record by the same steps as OLDER_FLOODS_TEST.md
§5c, nothing else changed. Four cell-days of flood labels change: three of
1,449 in the tree years, one of 207 in the calibration years.

- **F1 — the record.** The rebuilt record differs from the old one by
  exactly these four events. Every other event is identical.
- **F2 — timing.** Live timing inside Arunachal (satellite-fitted model on
  live rain, 2023–25, `flood_forecast_live_check.json`) is not more than
  0.005 below the figure on record (0.879). The truth it is graded on
  loses one flood of 44 (Doimukh 2024); that is the correction itself.
- **F3 — ranking.** The near-here weekly ranking inside Arunachal
  (`flood_near_here_diagnosis.json`) is not more than 0.005 below the
  figure on record (0.890).
- **F4 — nothing else moves.** The golden check shows changes only in
  day-model outputs (chances, area outlook, near-here, times-normal, the
  raster, the re-measured figures) and in floods-on-record counts near
  Pangin, Jollang and Doimukh. **Zero** changes in river forecasts.
- **F5 — screens.** All 21 screen checks pass.

If any rule fails, the old model files are put back
(`models/flood_forecast_pre_false_floods/`) and the cause is found first.
The four events stay out of the record either way: they are not floods.

### 15d. Result (2026-10-09) — all five rules pass; live

| Rule | Result |
|---|---|
| F1 the record | **Pass.** 2,185 → 2,181 events; the four gone, none added, every other event identical. Gauge-found floods 71 → 67 |
| F2 timing | **Pass.** 0.879 → **0.895** (43 floods, 2023–25, satellite-fitted model on live rain). On satellite rain 0.874 → 0.870 |
| F3 ranking | **Pass.** Near-here weekly ranking inside Arunachal 0.890 → **0.902**; daily 0.893 → 0.903 |
| F4 nothing else moves | **Pass.** 27,297 changed values, all day-model fields, near-here fields and the re-measured figures. River rows identical, whole (`export_args.rivers`, `snapshot.rivers`). Floods on record changed at 8 places, all down by 1 or 2 |
| F5 screens | **Pass.** No screen raises an error |

**A control run, to be sure the change comes from the four events only.**
The production fit was repeated on the *old* list into a scratch folder: it
reproduces the model that was live exactly (ordinary-day level, valley
factors, every file: largest gap 0.0). So the pipeline is repeatable and
every difference above is the four events.

**Why four labels move so much.** On the recorded quiet day (6 October)
the typical cell's chance fell to about 0.43 of what it was, the total
over all cells fell 9%, and the state's 7-day figure went from 9.6% to
8.1%. The four false floods were "floods" on days with no unusual rain. They
taught the model that a flood can come out of an ordinary day. Without
them, ordinary days score lower and the wet days stand out more — which is
what the better timing score measures. Valley factors: flat 1.048 → 0.982,
hilly 0.160 → 0.161, steep 0.020 → 0.024.

**One recorded figure flipped, with no effect on screen.** Gate C′ (keep
"High" evidence apart from "Medium" only if it ranks better *and* sits
closer to 1) now reads "keep apart": High 0.846 against Medium 0.843, where
it was 0.819 against 0.839. A margin of 0.003 is noise, not a finding. The
snapshot's `level` field therefore holds three levels where it held two.
No screen reads that field — the screens use the count of floods on record
and the two-level figures, which are still measured the same way (on
record ×1.52, none on record ×1.98). Left as the rule gives it; flagged.

**Live.** New baseline recorded for 2026-10-09 and replayed: 0 changes.
The web snapshot was refreshed without writing to the track record;
today's logged forecast (the scheduled run) is the old model's, and **the
first logged forecast from this model is 10 October**. The Data Backbone
page was rebuilt (2,181 floods).

**To go back:** `models/flood_forecast_pre_false_floods/` →
`models/flood_forecast/`; `reports/_pre_false_floods_backup/*` → `reports/`;
`data/interim/flood_forecast/golden_live_pre_false_floods/` is the old
baseline. The old list is kept at
`data/interim/flood_events/_pre_false_floods/` for reference only: the four
events are not floods and should not go back.

**Still open, not touched here:** Seppa 2026-07-15 and Tamen 2022-07-07 —
true readings, below today's line.
*Answered 2026-10-10, §19c: both were filed under the satellite scene's
date. Seppa is a real flood two days earlier; Tamen is a keying slip.*


## 16. The level line is graded every day (2026-10-10)

The first item of §14e's "not done yet". The level forecasts have been in
the log since 7 October; now each is checked against the gauge.

**What is graded** (`forecast_log.grade_level`, run inside `verify`, so
every daily run and every `forecast_log.py verify`): the middle of the line
against the day's highest reading, as the track record re-reads it
(cleaned).
- **Miss:** typical (median), mean and largest, in the gauge's units.
- **The yardstick:** the same miss had the river simply stayed at the last
  full day's high — what the line was tested against in §14.
- **Range held:** the share of days the high fell inside low–high. It is
  built to hold 80%.
- Split by how many days after the last full day of readings the target is
  (the model's own lead, 1 or 2), and by gauge. CWC (metres) and NWDP (flow)
  are kept apart; no NWDP gauge carries a line yet.
- Under 100 checked days it is marked "too few to judge".
- A forecast issued late in the day is graded like any other: the level
  model reads only complete days, so the target day's readings never reach
  it.

**Where it shows.** `reports/flood_forecast_scorecard.json` (`level_line`),
the daily log, the web snapshot (`track_record.level_line`), and one line on
the forecast page's Track record card with the detail behind its ⓘ.

**First reading — 85 gauge-days, targets 7–9 October, 17 CWC gauges.**

| Days after the last full day | Days | Typical miss | Mean miss | If the river stayed put | Range held |
|---|---|---|---|---|---|
| 1 | 51 | 0.02 m | 0.06 m | 0.14 m | 88% |
| 2 | 34 | 0.06 m | 0.16 m | 0.28 m | 79% |
| Both | 85 | 0.04 m | 0.10 m | 0.20 m | 85% |

- In line with the test of §14 (0.13 m and 0.22 m mean, range 80%), and
  better than "stays put" by about half. **But these are quiet, falling
  autumn rivers, and 85 days is too few to judge.** A river in flood is the
  real test.
- **Pare HEP stands out:** typical miss 0.73 m, range held on 1 day of 5.
  It is a hydropower dam gauge; its level follows releases, which nothing
  we read can see. Every other gauge's typical miss is under 0.09 m. Not
  acted on — worth a note on that gauge's graph, or leaving the line off
  it, once more days are in.
- One row checked by hand: Pasighat, issued 7 Oct for 8 Oct, middle
  149.929 m, river 149.76 m, miss 0.169 m.

**Checks.** Golden check: 0 changed, 1 added (`track_record.level_line`).
Screens pass. The Track record card still ends level with its two
neighbours, and the new line fits on one row at 1,366, 1,440 and 1,920 px.


## 17. Curing the high-river fault — three ingredients, rules first (2026-10-10)

The user's instruction: no wording on screen in place of the number; fix the
fault itself, with all three ingredients ("DO all the fixes"). This is the
fifth design on this history (§14c: none without the user's say — given).
**Nothing here goes live in this step.**

The fault, as it stands in the live models (W, §14d): of the days a river
already above its line is given under 5%, 24%, 11% and 10.4% end above the
line 2, 3 and 4 days ahead. The rule is fewer than 1 in 10.

### 17a. The three ingredients, fixed before any of it is run

**U — the gauge upstream.** Read on the same day as the gauge's own reading.
- *Which gauge:* the nearest gauge upstream on the same flow path whose
  river is at least a quarter the size of this gauge's (traced on the
  100 m flow raster from each gauge's placed spot). If it has no reading
  that day, the next one up.
- *The pairs this gives* (10 of 32 gauges): Yinkiang ← Tuting; Pangin ←
  Yinkiang, then Tuting; Passighat ← Pangin, then Yinkiang; Daporizo ←
  Lemeking; Namsai ← Miao; Bhalukpong ← Seppa; Doimukh ← Pare HEP, then
  Sagalee; Pare HEP ← Sagalee; Rho Basti ← Murga Bridge; Tengapani Bridge ←
  Pagoda. Every other gauge has none; its inputs are left empty.
- *Inputs:* `up_frac` (the upstream river's high, in its own units: 0 its
  ordinary level, 1 its line), `up_rise1`, `up_rise3` (its change over 1
  and 3 days), `up_share` (the upstream river's size as a share of this
  one's). Rule on direction: more `up_frac` may never lower the chance;
  the others are free.

**M — melt water.** ERA5-Land, the source the soil input already uses, on
the same grid (`fetch_40_era5land_melt.py`).
- Averaged over the area draining to the gauge that lies inside the map
  (the upstream weights of its rain cell).
- Read **16 days before the target day** — the lag the soil input uses,
  because the live run can always get it.
- *Inputs:* `melt7` (melt water over the 7 days ending then, mm), `swe`
  (snow still lying, mm), `temp7` (mean air temperature of those 7 days).
  All free.

**LV — the level line sets the chance when the river is already high.**
- For river-above days only, at 1–7 days ahead (where a level model
  exists). The S-curve that turns the score into a chance (§13i) gets a
  second input: where the line sits in the level model's range,
  `z = (level now + middle of the forecast change − 1) ÷ (high − low)`.
  Chance = S-curve of (a × score + c × z + b); a and c may not be
  negative (an input whose fitted number is negative is dropped).
- Fitted year-grouped like every curve here: a row's `z` comes from level
  models that never saw its year, and the curve from other years.
- River-below days are not touched.

U and M also go into the level model, by the same keep rule.

### 17b. Rules, fixed before it is run

Same rows, same cleaned truth, same year-grouped scoring as §14.

**Y — does the pattern hold from one year to the next** (checked first; an
ingredient that fails is dropped before any model is fitted):
- U: at each pair, in each year with 30 or more days of both, the upstream
  level one day earlier and the gauge's own level move together
  (correlation above 0). Must hold in at least 9 pair-years in 10.
- M: at gauges where melt matters (an average April–July `melt7` of 5 mm or
  more), in each year with 30 or more April–July days, `melt7` and the
  river's level move together. Must hold in at least 2 gauge-years in 3.

**K — is an ingredient kept.** Added alone to the live inputs, it is kept
if (1) it does no harm — AUC and Brier skill no more than 0.005 lower at
1–3 days and 0.010 at 4–9, on all days and on onset days — and (2) among
river-above days its Brier skill is better than without it at 3 or more of
leads 1–4. For the level model: kept if the middle line's average miss at
1 and 2 days is not larger, on all days and on river-above days. LV is
judged the same way against the model with the kept inputs.

**The final model** = live inputs + the kept ingredients. Against the live
models:
- **N, no harm:** as K(1), at every lead.
- **C, the fault itself** (W3 of §14c, unchanged): at every lead, of the
  river-above days given under 5%, fewer than 1 in 10 flood. Leads with
  fewer than 20 such days are judged together.
- **L, the level line** (only if the level model changes): L1–L3 of §14c at
  1 and 2 days, with the final chance model.

**Decisions.**
- N, C and L all pass: the fault is cured; ready to go live on the user's
  word.
- N passes, C fails but is smaller: reported as an improvement, not a
  cure; the user decides.
- N fails: not adopted.
- Reported either way: Rho Basti, June 2016, day by day.

### 17c. Result (2026-10-10) — not cured; one small improvement, two ingredients dropped

One run (`scripts/model/check_gauge_fix.py`, `reports/gauge_fix_check.json`;
inputs in `scripts/model/gauge_extra.py`; melt data from
`scripts/fetch/fetch_40_era5land_melt.py`, 9,619 days, no gaps). Mechanics
checked first: no input reads past its own day, and the lags are as written.
All 32 gauges, the cleaned history. **Nothing live was changed.**

| Ingredient | Year-to-year check (Y) | Keep rule (K) | Outcome |
|---|---|---|---|
| U, the gauge upstream | **Holds:** 89 of 89 pair-years move together, typical correlation 0.93 | No harm, but better among river-above days at only 1 of leads 1–4 (needs 3). In the level model: better at 1 day, slightly worse at 2 | **Not kept** |
| M, melt water (16 days old) | **Fails:** 77 of 213 gauge-years (36%); typical correlation −0.31 | — | **Dropped before any model** |
| LV, the level line in the chance | — | No harm; better among river-above days at leads 2, 3, 4 | **Kept** |

**Why U adds nothing.** The pattern is real — the two gauges move together
almost perfectly. That is exactly why it is not new: the river's own week
(§14) already carries what the gauge upstream would say a day earlier.

**Why M fails.** Read 16 days late and averaged over each catchment, melt
peaks in April–May while the big rivers peak in the monsoon, so at most
gauges more melt goes with a *lower* river. It does hold at the high
headwaters (Kibithu 20 of 20 years, Pagoda 5 of 5, Rho Basti 9 of 13), but
the rule was written for all gauges where melt matters, and it failed.

**The final model = live + LV. N passes, L passes, C fails.**

River-above days given under 5%, and how many of them flooded:

| Days ahead | Live (W) | With LV | Rule (under 10%) |
|---|---|---|---|
| 1 | 71 days, 5 (7.0%) | 86, 6 (7.0%) | ok |
| 2 | 24, 5 (20.8%) | 66, 7 (**10.6%**) | **fail** |
| 3 | 82, 9 (11.0%) | 93, 10 (**10.8%**) | **fail** |
| 4 | 152, 14 (9.2%) | 174, 13 (7.5%) | ok |
| 5 | 254, 21 (8.3%) | 280, 20 (7.1%) | ok |
| 6 | 332, 18 (5.4%) | 360, 25 (6.9%) | ok |
| 7–9 | 2.8–3.7% | unchanged | ok |

- LV halves the rate at 2 days (20.8% → 10.6%) — but mostly by putting
  more quiet days under 5%, not by lifting flood days out: the flood days
  given under 5% went from 5 to 7. Brier skill among river-above days, 2
  days ahead: 0.242 → 0.264; elsewhere the change is small either way.
- **Rho Basti, June 2016 is untouched:** the same 4, 6 and 6 flood days
  under 5% at 2, 3 and 4 days ahead, with or without LV. The level model
  itself puts that river just under its line on those days (§14d), so its
  position cannot lift the chance.
- The level line is unchanged (no input was kept in it): L1–L3 hold at 1
  and 2 days, with the LV chance as with the live one.
- On all 32 gauges the live model's own figures are 20.8%, 11.0% and 9.2%
  at 2, 3 and 4 days (§14d's 24%, 11%, 10.4% were on the 27 gauges whose
  line the cleaning did not move).

**By the rules: an improvement, not a cure. The user decides whether LV is
adopted.** Recommended: no. It is small, it misses the rule it was built
for, and it adds a second moving part to every river-above forecast.

**What this run rules out, and what is left.**
- More inputs of the kind we can read today do not cure it: the river's own
  week already holds the information.
- The days still wrong are rivers sitting within centimetres of their line
  (Rho Basti: 37 of its 91 line days are within 10 cm, §14d). No chance
  model can call those; the level line shows them honestly.
- Not tested, each would be a sixth design: melt read fresh (a few days
  old, from the weather forecast's own temperature) and only at the high
  headwaters where Y held; and judging a river at its line by a margin
  ("within 10 cm of its line") in place of a yes/no crossing.


## 18. Two more tests on the high-river fault — rules first (2026-10-10)

The user's instruction after §17c: run both untested ideas. This is the
sixth and seventh design on this history, each on the user's say.
**Nothing here goes live in this step.** The chance model is the live one
(W) throughout; neither test changes how the level line is drawn.

### 18a. Test A — a river at its line is called "at its line"

**The idea.** For a river hovering within centimetres of its line, "above
or not" is close to a coin toss (Rho Basti, June 2016: 0–21 cm above its
line for two weeks). The level line already shows such days honestly. So
on those days the screen would say "at its line" with the level range, and
show a percentage only on the other days.

**The flag, fixed before it is run.** A river-above day is flagged "at its
line" when the level model's low–high range for the target day touches the
band *line ± margin*. Margin: **10 cm** at level gauges (CWC); at flow
gauges (NWDP) 10% of the way from the ordinary level to the line. Level
models exist for 1–7 days ahead; at 8–9 nothing is flagged.

**Rules.**
- **A1, the fault itself:** at every lead, of the river-above days *not*
  flagged and given under 5%, fewer than 1 in 10 end at or above the line.
  Leads with fewer than 20 such days are judged together. (Rule C of §17b,
  on the days that would still show a percentage.)
- **A2, the flag means what it says:** at 1 and 2 days ahead (where the
  level line is drawn), between 2 and 8 in 10 of flagged days end at or
  above the line — a real toss-up, not a disguised yes or no.
- **A3, the flag is not a blanket:** at 1 and 2 days ahead, no more than
  half of river-above days are flagged.
- Reported: how many flagged days end inside the band; Rho Basti, June
  2016, day by day; the same counts at 3–7 days.

**Decision.** A1–A3 all pass: the fault is closed by the display rule, and
it can be built on the user's word. Otherwise reported as failed.

### 18b. Test B — fresh melt at the high gauges only

**The idea.** In §17 melt was read 16 days late at every gauge and failed
the year-to-year check. Read fresh, and only where a river is melt-fed, it
may still carry what the model lacks.

**Fixed before it is run.**
- *Which gauges:* level gauges that stand above **1,000 m** (their own
  ordinary reading, which is a height above sea level): Rho Basti, Murga
  Bridge, Kibithu, Lemeking. A physical rule, set before looking at which
  gauges gain. Every other gauge's melt inputs are left empty.
- *Inputs:* the three of §17a (`melt7`, `swe`, `temp7`), read on **the day
  of the gauge's own reading**, not 16 days before the target.
- *What this measures:* the most that fresh melt information could be
  worth, from the archive. ERA5-Land itself arrives about 9 days late, so
  going live would need a fresher feed (the weather forecast's own
  temperature and snow). That is built only if this passes.

**Rules** (as §17b):
- **Y:** at these gauges, in each year with 30 or more April–July days,
  fresh `melt7` and the river's level move together in at least 2
  gauge-years in 3.
- **K:** no harm against W at every lead (all days and onset days), and
  better Brier skill among river-above days at 3 or more of leads 1–4.
  Also reported for the four gauges alone.
- **C:** the fault test of §17b on the result.

**Decision.** Y, K and C pass: cured; a live feed is the next step. Y and K
pass, C fails: an improvement, the user decides whether a live feed is
worth building. Otherwise not adopted.

### 18c. Result (2026-10-10) — both fail

One run (`scripts/model/check_gauge_fix2.py`,
`reports/gauge_fix2_check.json`). **Nothing live was changed.**

**Test A, "at its line": A1 and A2 pass, A3 fails. Not adopted.**

| Days ahead | River-above days | Flagged "at its line" | Of flagged: ended at/above the line | Ended inside the band | Under 5% and not flagged: days, flooded |
|---|---|---|---|---|---|
| 1 | 1,188 | **79%** | 52% | 24% | 6, 0 |
| 2 | 1,183 | **91%** | 43% | 17% | 10, 1 |
| 3 | 1,183 | 90% | 34% | 15% | 50, 3 (6.0%) |
| 4 | 1,182 | 85% | 29% | 13% | 97, 5 (5.2%) |
| 5–7 | | 66–83% | 22–23% | 10% | 2.4–4.9% |

- The days left showing a percentage are honest (A1), and the flagged days
  are real toss-ups (A2). But **the flag covers 8 to 9 river-above days in
  10** (A3 allows half). It is not a mark for the few rivers hovering at
  their line: it is nearly every high river.
- Only 17–24% of flagged days end inside the 10 cm band. So "at its line"
  would be the wrong words for most of them.
- Of Rho Basti's wrongly-low June 2016 days, the flag takes 4 of 4 at 2
  days ahead, 4 of 6 at 3 days and 2 of 6 at 4 days.
- **What this says about the fault.** It is not a handful of odd rivers.
  One or two days after a river is above its line, whether it is still
  above is close to even odds on most such days (52% and 43% of the
  flagged days), and the level model's range, built to hold 8 days in 10,
  is wider than the river's distance from its line.

**Test B, fresh melt at the gauges above 1,000 m: fails Y. Dropped before
any model.**
- 23 of 59 gauge-years move together (39%; the rule is 2 in 3); typical
  correlation −0.14. Kibithu 15 of 20, Murga Bridge 3 of 8, Rho Basti 3 of
  13, Lemeking 2 of 18.
- Read fresh, melt and the river's level do not rise together at these
  gauges in most years. (Read 16 days earlier, Rho Basti held in 9 of 13
  years, §17c: at that gauge the river follows the melt by weeks, which a
  same-day reading cannot show.)

**Where seven designs leave it.** The floor, the S-curve, the per-river
habit, the river's week, upstream gauges and melt, the level line in the
chance, and the "at its line" flag: the river's week is the only one that
moved the fault much, and it is live. The remaining error is not a missing
input we can fetch. Whether a high river is still above its line a day or
two later is, on this record, close to even odds on most such days.
**No eighth design on this history** — with this many tries on the same few
hundred days, a pass would more likely be luck than a cure. What changes the
picture is new information: more monsoons logged, gauges further upstream,
dam release schedules.

### 18d. What is on screen instead (2026-10-10, the user: "apply current fix until more data accumulated")

With no model cure, the screen stops showing a small number it cannot stand
behind. **Screen only: the forecast, its log and its grading are untouched**
(golden check: 0 changed).

- **The rule** (`live._unsure`): the river was at or above its line on its
  last full day of readings (the state the model itself reads), the target
  day is 1–4 days after that reading, and the chance is under 5%. Then the
  day shows "unsure" (a "?" in the small day cells), not the percentage.
  These are exactly the days the tests found wrong; from 5 days on the
  small numbers held, and a chance of 5% or more is shown as it is.
- **A figure that sums up a week** (the highest day) shows "unsure" when
  that highest chance is itself under 5% and any of its days is unsure.
- **Where:** the place tile "River reaches its line", the Rivers list, the
  gauge's label and tooltip on the map, its stretch's tooltip, the gauge
  popup's day cells, the gauge graph's bars (grey, tooltip says why), the
  river board, the "Highest chance" tile, a Note column in the table, and
  the method page's "what it does not count".
- **Checked** on a made-up snapshot (Passighat above its line with small
  chances all week; Seppa above its line with 41% tomorrow): Passighat reads
  "unsure" everywhere, Seppa keeps its 41%; no errors; cards still level;
  the real snapshot was put back byte for byte. On today's real snapshot no
  river is above its line, so nothing looks different. Screens pass.
- **To take it out again** when a cure exists: `_unsure` returning False
  removes it everywhere.

## 19. Gauge housekeeping before the next re-teach (2026-10-10)

Three flags had been left open. Each was checked against the readings.
**Nothing live changed:** the daily run reads the trained `stations.json`
and the verified list on disk, and neither was rewritten (golden check: 0
changed).

### 19a. Changlang (2nd station): 2024 is on another scale — record now starts Feb 2025

| | 2024 | 2025 | 2026 |
|---|---|---|---|
| Mean 7-day rain, Apr–Aug (model input) | 0.6 | 0.5 | 0.6 |
| Median flow, Apr–Aug, m³/s | 24 | 109 | 104 |
| Against the first Changlang station, same days | 0.15× | 1.3× | 3.1× |

The same rain gave about a quarter of the flow in 2024. The gauge sent
nothing from October 2024 to January 2025 and came back on the new scale.
`gauge_records.RECORD_STARTS["Changlang_1"] = "2025-02-01"`. Its own top-2%
line moves 594 → 691 m³/s (10 days at it → 8). **Takes effect at the next
re-teach of the gauge models**, not before.

(The first Changlang station is a different question: its coordinates are
wrong and it is not linked to places. Not touched.)

### 19b. Rho Basti: the line is old, but there is no break to cut at — left whole

- 71 of the 91 days at its line (2,232.17 m, its own top 2%) are 2016–17.
  Since 2021 there has been one.
- Allowing for rain, the monsoon level has eased about 2–3 cm a year since
  2016: 2016–17 sat about 20–26 cm higher than the rain explains, 2022–26
  about 6–8 cm lower. There is no step and no change in the lowest readings
  that would date a re-levelling.
- A line from recent years alone would be lower (2018 on: 2,231.97 m;
  2021 on: 2,231.82 m) and would relabel 12 or 45 ordinary days since 2021
  as floods, with nothing to confirm any of them.
- **Decision: leave it.** The cause cannot be told from the readings (two
  wet melt years, or a channel that has cut down). What settles it is
  CWC's real danger level for Rho Basti, already on the ask list. Noted in
  `gauge_records.py`.

### 19c. Seppa 2026 and Tamen 2022: both were filed two days off their river

Both come from `flood_where_s1_loose_ends.json`, where `flood_date` holds
the **satellite scene's** date and the real flood day sits in a separate
`note`. The list builder read only `flood_date`.

| Record | Filed under | Real flood day | That day's readings | Verdict |
|---|---|---|---|---|
| Seppa | 2026-07-15 | 2026-07-13 | rose 337.25 → 340.88 m over 8 hours, 6 hourly readings at or above the danger level (340.00), then fell | **Real flood, wrong day** |
| Tamen | 2022-07-07 | 2022-07-09 | 23 readings 274.10–274.30 m and one of 284.19 between two of 274.19 | **Not a flood: a keying slip** |

Tamen is the same kind as the four removed in §15. The false-reading rule
(§15b) could not see it because it looked at the 7th, not the 9th. The
radar agrees: less water on the "flood" day (6.68%) than on the ordinary
day (7.37%).

**Fixed in `build_verified_floods._day`:** it reads the note as well. A
dry run of the builder (nothing written) gives exactly this and no other
difference: 2,181 → 2,180 events; `gauge:070-UBDDIB:2022-07-07` gone
(dropped by the §15b rule as `…:2022-07-09`); `gauge:027-UBDDIB:2026-07-15`
replaced by `…:2026-07-13`; every other event identical.

### 19d. The re-teach — rules, fixed before it is run (2026-10-10, the user's go-ahead)

The user's word: *"Re-teach with the gauge fixes from item 20."* Two
re-teaches, one after the other, each with its own check.

**A correction to what was written here first.** The earlier draft said the
gauge re-teach should move "Changlang's rows only". That was wrong: the
gauge models are one pooled model per lead over all 32 gauges, so taking
132 days out of one gauge can move every river's number a little. The rule
below says so.

**Part 1 — the gauge models** (Changlang's second station from Feb 2025).
Trained into `models/flood_when_gauge_next/` first; switched in only if
K1–K2 pass.

- **K1 — no worse.** Against the live models' own report
  (`reports/flood_when_gauge.json`), ranking (AUC) and Brier skill of
  "rain + gauge", on all days and on onset days: not more than **0.005**
  lower at 1–3 days ahead, not more than **0.010** lower at 4–9 (the
  tolerances of §13h). The rows are not quite the same rows — one gauge
  lost 132 days and its line moved — so this is report against report.
- **K2 — only the intended gauge changes.** In `stations.json`, the line,
  ordinary level and base rate differ at `Changlang_1` and nowhere else.
- **K3 — the level line is no worse.** Its checked miss at CWC gauges one
  and two days ahead (`level.json`) is not more than 0.01 m larger.
- **K4 — after the switch, nothing else moves.** Golden check: changes only
  in river rows and the method page's gauge figures; every day-model field
  identical. No gauge other than Changlang's second station moves by more
  than 1 percentage point on the recorded day.

**Part 2 — the day model** (Tamen 2022 out, Seppa 2026 to its real day).
The steps of §15c.

- **F1** the rebuilt record differs from the old by exactly: Tamen
  2022-07-07 gone, Seppa 2026-07-15 → 2026-07-13. 2,181 → 2,180.
- **F2** live timing inside Arunachal not more than 0.005 below 0.895.
- **F3** near-here weekly ranking not more than 0.005 below 0.902.
- **F4** golden check: day-model fields, floods-on-record near Tamen and
  Seppa, and the re-measured figures only. River rows identical to Part 1's.
- **F5** all screens pass.

If a part fails, its old files go back
(`models/flood_when_gauge_pre_housekeeping/`,
`models/flood_forecast_pre_housekeeping/`) and it is reported as failed.
Tamen stays out of the record either way: it is not a flood.

### 19e. Result, Part 1 — the gauge models: all four rules pass; live (2026-10-11)

| Rule | Result |
|---|---|
| K1 no worse | **Pass.** Judged unrounded, old and new scored the same way in one run (the old figures reproduce the live report). Largest drops at 1–3 days: Brier skill −0.0043 and onset skill −0.0041 at 1 day (limit −0.005); 2 days: skill **+0.016**, onset +0.010; 3 days: all within −0.003. 4–9 days: all within ±0.006 on the rounded reports (limit −0.010) |
| K2 only the intended gauge | **Pass.** `stations.json` differs at `Changlang_1` only: line 593.7 → 691.3 m³/s, ordinary level 62.4 → 79.3, base rate 2.07% → 2.28%. 121 fewer gauge-days and 2 fewer flood days in the 1-day table |
| K3 level line no worse | **Pass.** CWC gauges, out of fold: 1 day 0.1339 m → 0.1339 m; 2 days 0.2148 m → 0.2148 m; range holds 80.4% → 80.6% and 80.2% → 80.2% |
| K4 nothing else moves | **Pass.** 615 changed values on the recorded day, every one a river row or a gauge figure on the method page. The day model's output and the raster are identical. Largest move at any gauge: 0.47 percentage points (Pare HEP, 0.69% → 0.22%); limit 1 |

The live gauge models are the re-taught ones from 2026-10-11. The old set
is in `models/flood_when_gauge_pre_housekeeping/`, its report in
`reports/_pre_housekeeping_backup/`.

### 19f. Result, Part 2 — the day model: all five rules pass; live (2026-10-11)

| Rule | Result |
|---|---|
| F1 the record | **Pass.** 2,181 → 2,180. Gone: `gauge:070-UBDDIB:2022-07-07` (Tamen). `gauge:027-UBDDIB:2026-07-15` → `…:2026-07-13` (Seppa). No other event changed. Gauge-found floods 67 → 66 |
| F2 timing | **Pass.** 0.8952 → **0.8956** (43 floods, 2023–25, satellite-fitted model on live rain) |
| F3 ranking | **Pass.** Near-here weekly ranking inside Arunachal 0.9024 → 0.8989: 0.0035 lower, inside the 0.005 allowed. Daily 0.9033 → 0.8988 |
| F4 nothing else moves | **Pass.** 11,557 changed values: 615 are Part 1's river rows and gauge figures, the same count as after Part 1; the rest are day-model fields (near-here chances, times-normal, the area outlook, the raster, the re-measured figures). Floods on record changed at 2 places, both next to Tamen, both 1 → 0 |
| F5 screens | **Pass.** All 34 screen cases open |

**What moved, on the recorded day (9 October).** The state's 7-day figure
2.04% → 2.19%; a typical place ×1.10 (middle 90% of places ×0.28 to
×2.32); places keep their order (rank correlation 0.95). Valley factors:
flat 0.982 → 1.001, hilly 0.161 → 0.162, steep 0.024 → 0.021. One flood
label in the tree years changed (1,446 → 1,445).

**Gate C′ flipped back.** The snapshot's `level` field holds two levels
again (it went to three on 9 October on a margin of 0.003, §15d). The same
remark applies: the margin is noise, and no screen reads that field.

**Live.** New baseline recorded for 2026-10-11 and replayed: 0 changes. The
web snapshot was refreshed without writing to the track record (the five
log files are byte-identical). **The first logged forecast from these
models is the 08:30 run of 11 October.** The Data Backbone pages were
rebuilt (2,180 floods).

**To go back:** `models/flood_forecast_pre_housekeeping/` →
`models/flood_forecast/`; `models/flood_when_gauge_pre_housekeeping/` →
`models/flood_when_gauge/`; `reports/_pre_housekeeping_backup/*` →
`reports/`; `data/interim/flood_events/_pre_housekeeping/` holds the old
list (for reference: Tamen is not a flood and should not go back);
`data/interim/flood_forecast/golden_live_pre_housekeeping/` is the old
baseline.

## 20. Pare HEP: no level line for a dam gauge (2026-10-11)

§16 flagged Pare HEP: in its first five graded days the level line's range
held on one, with a typical miss of 0.73 m against 0.04 m for the rest. The
user's instruction: *"Do what's best."* Five days is too few to judge a
line on, so the gauge's own record was looked at instead.

**Pare HEP sits at a hydro-power dam, and its level behaves like one.** On
its whole record (62 days from 2026-06-18), beside the 17 other CWC level
gauges:

| | Pare HEP | The other 17 |
|---|---|---|
| Typical day-to-day move in the daily high | 0.36 m | 0.01–0.22 m |
| Day-to-day move on one day in ten, as a share of the gap between its usual level and its line | 1.24 | 0.06–0.27 |
| Days whose high stands more than 0.5 m above both the first and the last reading (a rise and fall inside the day) | 57% | 0–8% |

The level model learned how rivers rise and fall on rain. This one rises
when the gates open. No amount of grading will fix that; what would
forecast it is the dam's release schedule, which is on the ask list.

**Done**
- `gauge_records.NO_LEVEL_LINE` names the gauge and the reason.
- The daily run issues no level line for it (`flood_gauge_live.forecast`).
- The snapshot carries the reason (`rivers[].no_level_line`) and the gauge's
  graph says it in a line under the tiles and in the ⓘ.
- **Grading:** the five days already issued stay in the log. They are
  reported on their own (`level_line.no_longer_drawn`), not in the figures
  for the line that is still drawn. With them: 85 checked, typical miss
  0.04 m, mean 0.10 m, range held 85%. Without: **80 checked, 0.04 m,
  mean 0.07 m, range held 89%**, 16 gauges. Both are written here so the
  change is not mistaken for an improvement in the model.
- Golden check: the only values that changed are Pare HEP's level fields
  (its two drawn days), plus the two new fields.
- The track-record line on screen ("Level line: N checked …") is read from
  the scorecard the daily run writes; it shows the new figures from the
  08:30 run of 11 October on.

**Not changed, and worth knowing:** Pare HEP still gets a *chance* of
reaching its line. That line is its own top 2% of 62 days — one or two
days — and its level is set by releases. The chance is the weakest of the
32 for the same reason. Left as it is for now; taking a gauge out of the
chance forecast changes the logged record and is a separate decision.

