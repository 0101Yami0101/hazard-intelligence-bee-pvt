# Ensemble strategy — the panel-of-experts plan, and how we govern it

**Status:** planning decision, 2026-08-28. Nothing here is built yet — this is the
agreed target architecture and the rules for growing into it. Applies to **both**
SlideSense and FloodSense; hazard-agnostic by design, same as the rest of the core.

---

## 1. The architecture (confirmed)

```
        WHERE box                          WHEN box
  ┌─────────────────────┐           ┌─────────────────────┐
  │ rule-based           │           │ rule-based           │
  │ trees (different)    │           │ trees (different)    │
  │ other ML methods     │──[meta]   │ other ML methods     │──[meta]
  │ deep learning 1       │  learner │ deep learning 1       │  learner
  │ deep learning 2       │           │ deep learning 2       │
  │ ...more as found      │           │ ...more as found      │
  └─────────────────────┘           └─────────────────────┘
          WHERE score        x          WHEN score        =  HAZARD
```

**Both boxes get their own meta-learner** — one referee blends the WHERE panel,
a separate referee blends the WHEN panel. They are not shared. Only after each
side has produced its own single score do the two get multiplied together.

This is the same shape for landslide and flood. Neither module runs the full
picture yet — see §2.

---

## 2. Current fill status (2026-08-28)

| | WHERE box | WHEN box |
|---|---|---|
| **Landslide** | 1 method live (terrain rule) + tree model built and validated on real local labels (37,788 polygons, AUC 0.860) — closest to ready for a real panel | 1 method live (unfitted rainfall-percentile rule, AUC 0.768 — see [MODEL_TRIGGER_AND_HAZARD.md](MODEL_TRIGGER_AND_HAZARD.md) §4 for why it is deliberately *not* fitted yet) |
| **Flood** | 1 method live (HAND × catchment-area physics rule) | 1 method live (catchment rainfall-percentile rule) |

**No box on either hazard has a real panel + meta-learner running today.** Every
cell above is a single method standing in for the eventual panel. Landslide-WHERE
is furthest along because it already has real local ground truth to grade
candidate methods against; the other three cells lack that and are the priority
for the data work described in [FLOOD_MODULE.md](FLOOD_MODULE.md) and
[TEMPORAL_INVENTORY_ATTEMPTS.md](TEMPORAL_INVENTORY_ATTEMPTS.md).

---

## 3. Model inclusion policy — gate the ensemble, not the individual model

**Do not discard a model just because it underperforms the current rule on its
own.** A meta-learner does not pick a single winner — it learns *how much to
trust* each panel member, and a model that is weaker on average can still help
if it is wrong in a **different way** than the others (classic ensemble
diversity). Vetoing a model before it ever reaches the referee throws that
value away.

**The real check:** does adding model X to the ensemble improve the *whole
ensemble's* accuracy on real held-out data — not "does model X alone beat the
baseline." If yes, keep it in, however small its own standalone score. If the
ensemble is measurably worse with it than without, drop or down-weight it —
that decision is made at the ensemble level, after the referee has had a
chance to use it, not before.

---

## 4. Meta-learner complexity ceiling — matched to how much proof data exists

The referee itself is a model and needs its own held-out evidence to be
trusted. With only a few hundred real events to check against (today's
reality for both hazards' WHEN side), a complex, finely-tuned referee risks
**learning noise in a tiny test set**, not real patterns.

- **Now (hundreds of events):** keep the referee simple — a fixed or lightly
  weighted blend, not a fully learned trust model.
- **Later (real held-out events climb into the low thousands and beyond):**
  the referee can grow into a properly learned model of "trust this expert
  more in these conditions."

This ceiling is not permanent — it rises automatically as more real events
are confirmed, the same shape as `state-limits-with-their-tier` in memory:
name what lifts the limit, don't phrase it as fixed.

---

## 5. The regional-pool → fine-tune → local-only-in-parallel plan (DL strategy)

Confirmed valid, 2026-08-28. Generalizes and extends the parked Himalayan
pooling plan ([PARKED_HIMALAYAN_POOLED_TRIGGER.md](PARKED_HIMALAYAN_POOLED_TRIGGER.md))
past landslide-only and past "one pooled model":

1. **Local data too thin to train on alone** → pool data from the wider
   Himalayan region (or other similarly-terrained regions) and train a DL
   model on the pooled set.
2. **Fine-tune** that pooled model on whatever local (Arunachal) data exists,
   making it locally aware.
3. **Add it to the panel** as one more expert opinion, graded by the §3 rule.
4. **Later, once enough local-only data has accumulated** — train a
   **separate, second** DL model using *only* local data.
5. **Keep both** the fine-tuned regional model and the new local-only model
   in the panel at the same time. This is deliberate, not redundant: they
   tend to fail on different cases (one carries broader regional patterns,
   one carries Arunachal-specific quirks), and that difference is exactly
   what a meta-learner can exploit.

**Flood-specific nuance:** for *gauged* rivers, this may not need the
"borrow first" step at all — 55 years of daily CWC readings on one river is
already tens of thousands of data points, plausibly enough to train a
local-only sequence model directly. Regional pooling earns its keep mainly
on **ungauged** rivers and small streams, where there is no local time series
to train on at all yet.

---

## 6. Retraining cadence — continual improvement, not a one-time train

Both the model's own skill *and* our ability to safely trust it (the §4
ceiling) improve together as more real data comes in. So:

- **Retrain regularly** — after every monsoon season, or whenever a
  meaningful batch of newly confirmed events lands (new GSI reports read,
  new river danger-level crossings recorded, etc.), not once and left alone.
- **An underperforming model is not a dead end, it is early.** Keep it in the
  panel and re-evaluate it at every retrain cycle rather than deleting it.
- This is the operational form of §4 and §5 combined: the referee gets
  smarter and every panel member gets another chance to prove itself, on a
  recurring schedule, without a redesign each time.

---

## 7. Applying this to flood right now (2026-08-28 planning)

### Flood WHERE — buildable today vs blocked

| Buildable now, no new data needed | Blocked — needs data/access we don't have |
|---|---|
| Live: HAND × catchment-area rule | Real flood **depth** (feet of water) — needs river cross-section/bathymetry (asked, CWC — [GOV_DATA_REQUEST_LIST.md](GOV_DATA_REQUEST_LIST.md) §2) |
| Flow-accumulation / drainage-network model straight from terrain data — engineering only | Water behaviour after a river leaves its banks — needs embankment/levee locations (asked, State Water Resources) |
| Historical open-water footprint from free Sentinel-1 SAR imagery — real ground evidence of where water has actually sat | City-block urban flood detail — needs drainage-pipe maps (asked) and LiDAR (paid item) |
| NESDR wet-season vs dry-season Waterbody comparison — free, found, untested lead (see [FLOOD_MODULE.md](FLOOD_MODULE.md) "Next" item 4) | Glacial-lake burst floods (GLOF) — needs NWIA bulk access, still pending confirmation |

### Flood WHEN — buildable today vs blocked

| Buildable now | Blocked |
|---|---|
| Live: catchment rainfall-percentile rule | Ungauged rivers/streams — no ground truth to check any guess against yet |
| Real second method: CWC's 55-year gauge history + published danger thresholds (major rivers) and NWDP's discharge series (14 smaller rivers) — real data to check and to train on, see recipe below | Dam-regulated rivers — releases look like noise without NHPC's release schedules (asked) |
| GloFAS as a cross-check on the ~5 largest rivers | Fast, flash-flood-prone small catchments — daily satellite rainfall is too coarse/slow; needs short-fuse radar (asked, IMD — may not exist yet for this region) |

### The 55-year CWC/NWDP gauge data — the two-step recipe

1. **Backtest the current rule first (no training).** Run the existing
   rainfall-percentile rule back through the real gauge history and score it:
   on days the river actually crossed danger level, did the rule flag high
   risk? This is a calibration check, not a trained model — it gives an
   honest, provable score for what already ships.
2. **Train and validate a real second WHEN model.** Split each gauge's
   history into a visible training period (most of it) and a hidden test
   period never shown during training (a held-out chunk of recent years).
   Train a tree-based model on the visible years using rainfall + past level
   patterns; test it against the hidden years. If it beats the step-1 score
   on hidden data, it earns a real seat as a second WHEN-panel method — see
   §3. If not, nothing is lost — the rule keeps shipping, now with a proven
   score attached.

**Why this works here specifically:** one gauge's 55 years of daily readings
is tens of thousands of data points — a real train/test split is possible
per-river today, unlike landslide's event-count scarcity
([TEMPORAL_INVENTORY_ATTEMPTS.md](TEMPORAL_INVENTORY_ATTEMPTS.md)).

> **2026-08-28 — build order decided: WHEN before WHERE, pilot first.** WHEN
> is built first because its data is ready now, and its output (a real dated
> flood list) is the exact input WHERE needs to pull satellite evidence for.
> Full step-by-step plan, starting with a Tawang pilot and the guardrails that
> keep a small pilot from weakening the eventual statewide model:
> [FLOOD_WHEN_PILOT_PLAN.md](FLOOD_WHEN_PILOT_PLAN.md).
