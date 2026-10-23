# Pilot idea — Tawang district, starting from Jang

> ## ⭐ IMPORTANT — ground rain gauges are open: add them to the Jang pilot
> **(the user's instruction, 2026-10-20)**
>
> Marked by the user so it is not lost: *"make sure we go back to the other modules to
> add the newly found rain gauge data wherever applicable."* Tracked as item **#25** in
> [REMAINING_WORK.md](REMAINING_WORK.md).
> **Tested 2026-10-20 ([RAIN_GAUGES.md](RAIN_GAUGES.md) Part E):** Jang is where both rain sources are weakest: 3-day agreement 0.36 (IMERG) and 0.44 (Open-Meteo); totals 1.25× and 2.41× the gauge. Jang's rain is on NWDP only, 1–2 weeks late. The two Tawang river stations on the live CWC flood site carry no live rain (Rho Basti stopped in 2023; Murga Bridge has none). So Jang's gauge proves and grades; it cannot feed a live forecast.
>
> **What was found.** The Central Water Commission's own **rain gauges** are open on the
> National Water Data Portal (no login, no key), and nothing on the platform used them
> before. The forecasts run on satellite rain (IMERG, daily since 2000) and forecast rain.
> FloodSense's 32 "gauges" are river levels, not rain.
>
> - **Arunachal, daily:** Pasighat 1973→2026 (54 years), Tezu 48, Miao 47, Namsai 34,
>   Seppa 31, Bhalukpong 30, Kabu Basti 25, Yazali 23, Kibithu 20, Tuting 20, and
>   **Meteorological Station Jang, 2017→2026**. Updated to October 2026.
> - **Assam, daily:** from 1971, up to about 80 stations recently.
> - **Truly hourly:** only from 2019 (telemetry), about 9 Assam stations and 1 in Arunachal.
>   The file names say otherwise; they cannot be trusted for period or resolution.
> - **Get it:** `scripts/fetch/fetch_47_cwc_rainfall.py`. Real spans per station:
>   `scripts/inspect/cwc_rain_inventory.py` → `reports/cwc_rain_inventory.csv`.
> - **Limits:** points at river stations, mostly in valleys; read daily at 08:00; quality
>   not yet checked; little on the ridges.
>
> **Where it applies here:**
>
> - **Meteorological Station Jang has daily rain from 2017 to today.** That is the local
>   ground record the pilot asked for, before installing anything. Use it to check and
>   correct the satellite rain at Jang, for both forecasts.

> **Status: idea, not started.** Logged 2026-08-20 so it isn't lost. Nothing built yet.

> **2026-08-28:** the flood WHEN side of this pilot now has a concrete,
> step-by-step build plan — see [FLOOD_WHEN_PILOT_PLAN.md](FLOOD_WHEN_PILOT_PLAN.md).
> Read that before starting any implementation here.

## Why Tawang/Jang specifically

- Small enough to fully instrument on a modest budget — unlike a statewide rollout.
- Already has more real local data than most of the state (see below) — a head
  start no formal ask created.
- A genuine second hazard worth showcasing: **glacial lake outburst flood (GLOF)
  and snowmelt**, distinct from the rain-driven story everywhere else. Real
  glacial lakes sit upstream of the valley (see NWIA finding, `DATA_VERIFICATION.md`).
- Border-road corridor maintained by BRO — plausibly better on-ground access for
  installing/maintaining any paid sensors than remote interior districts.

## What's already free and usable today

- **Landslide susceptibility + daily trigger** — statewide build already covers
  this area, no extra work. Caveat: IMERG rainfall bias is known to be worse at
  this altitude than in the lowlands.
- **Flood static layer** — our own build already says **Tawang town itself is
  NOT flood-prone** (705 m above nearest drainage, class 0). **Jang, down in the
  valley on the actual river, is unconfirmed and worth checking specifically.**
- **Two real, live-updating CWC river-level gauges right in the area**:
  `Murga Bridge` (002Neid3) and `Rho Basti` (001NEID3), both reporting as
  recently as 2026-08-19. (A third station literally named "Jang" exists but
  is dead — stopped reporting in 2021, not useful.) No danger/warning
  threshold published for either yet — see Ask, below.
- **NESDR snow-cover layer** — relevant given Tawang's real seasonal snow.
- **NWIA wetland/glacial-lake maps** (APSAC, found 2026-08-20) — includes a
  glacial-lake category specifically; not yet confirmed downloadable, see
  `DATA_VERIFICATION.md`.

## Ask, specific to this one small district

1. ~~CWC: history + danger/warning thresholds for Murga Bridge and Rho Basti.~~
   → **Downgraded to nice-to-have, 2026-08-28.** History is archived and a
   flood-day threshold is now self-derived from it (no CWC input needed) —
   see [FLOOD_WHEN_PILOT_PLAN.md](FLOOD_WHEN_PILOT_PLAN.md) §1/§4. A real CWC
   threshold, if it ever arrives, becomes a cross-check, not a requirement.
2. BRO: road-block logs for this corridor — plausibly the best-kept landslide
   date records in the state, given military road maintenance.
3. Tawang DDMA: local incident records — a small office, more tractable than a
   state-wide request.
4. IMD: a ground rainfall station locally, to correct the high-altitude
   satellite bias.

## Paid, if this pilot gets funded

1. A few more water-level sensors along the river through Jang — a complete
   micro-network for one valley, not a token station.
2. Detailed terrain (LiDAR) for just the Jang valley — cheap at this scale,
   enough to turn a risk score into an actual "water reaches here" map.
   APSAC's own infrastructure page (`infrastructure.php`) says they already run
   in-house LiDAR point-cloud processing — worth asking whether a commissioned
   local survey is possible before sourcing this from an outside vendor.

Full source detail for everything referenced here: `DATA_VERIFICATION.md`.
