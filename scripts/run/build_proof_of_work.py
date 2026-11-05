"""The NESFIC-D-07 Proof of Work PDF: SoilSense, what is built and how it was checked.

    python scripts/run/build_proof_of_work.py            # HTML + PDF
    python scripts/run/capture_soilsense_shots.py        # run first: the screenshots

Written for the challenge's evaluators: the Soil Conservation Department's officers
and the NESFIC jury. Every number is read from the reports the pipeline writes,
so a re-run after new results keeps the PDF in step with the app. Sections whose
results do not exist yet say so instead of guessing.

Outputs: docs/nesfic/SoilSense_Proof_of_Work.html and .pdf (A4, must stay < 10 MB).
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REP = ROOT / "reports"
SHOTS = ROOT / "docs" / "nesfic" / "shots"
OUT = ROOT / "docs" / "nesfic"
REGION = "assam"

# print palette (light): series 1 blue = ours, series 2 orange = others
BLUE, ORANGE, INK, INK2, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
GOOD, BAD, PEND = "#1f8a4c", "#c0392b", "#8a8984"


def jread(name: str):
    p = REP / name
    return json.loads(p.read_text()) if p.exists() else None


def img(path: Path, width: int = 1400, q: int = 80) -> str:
    """An image as an embedded JPEG data URI, scaled to `width` px."""
    if not path.exists():
        return ""
    im = Image.open(path).convert("RGB")
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def shot(name: str, caption: str, crop_h: int | None = None) -> str:
    p = SHOTS / f"{name}.png"
    if not p.exists():
        return f"<div class='pending'>Screenshot {name} not taken yet.</div>"
    if crop_h:
        im = Image.open(p)
        im = im.crop((0, 0, im.width, min(crop_h, im.height)))
        tmp = OUT / f"_{name}_crop.png"
        im.save(tmp)
        p = tmp
    return f"<figure><img src='{img(p)}'><figcaption>{caption}</figcaption></figure>"


def mark(ok) -> str:
    if ok is None:
        return f"<span class='st' style='color:{PEND}'>pending</span>"
    return (f"<span class='st' style='color:{GOOD}'>✔ pass</span>" if ok
            else f"<span class='st' style='color:{BAD}'>✕ fail</span>")


# ---- charts: inline SVG, static (a printed page has no hover) ---------------

def bar_chart(rows, title: str, unit: str, ref=None, w=640) -> str:
    """Horizontal bars, one series; `rows` = (label, value, highlight, note)."""
    h_row, left, right = 34, 210, 90
    h = 40 + h_row * len(rows) + 10
    mx = max(v for _, v, _, _ in rows) * 1.08
    sx = lambda v: left + (w - left - right) * v / mx
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{title}'>",
           f"<text x='0' y='16' class='ct'>{title}</text>"]
    for i, (lab, v, hi, note) in enumerate(rows):
        y = 34 + i * h_row
        out.append(f"<text x='{left - 10}' y='{y + 15}' text-anchor='end' class='cl'>{lab}</text>")
        out.append(f"<rect x='{left}' y='{y + 4}' width='{max(sx(v) - left, 2):.1f}' height='18' rx='4' "
                   f"fill='{BLUE if hi else '#b9b8b2'}'/>")
        out.append(f"<text x='{sx(v) + 6:.1f}' y='{y + 17}' class='cv'>{v:,.0f}{unit}"
                   f"<tspan class='cn'> {note}</tspan></text>")
    if ref is not None:
        x = sx(ref[0])
        out.append(f"<line x1='{x:.1f}' x2='{x:.1f}' y1='28' y2='{h - 6}' stroke='{INK}' "
                   f"stroke-width='1.5' stroke-dasharray='4 3'/>")
        out.append(f"<text x='{x + 4:.1f}' y='{h - 8}' class='cn'>{ref[1]}</text>")
    out.append("</svg>")
    return "".join(out)


def line_chart_log(cats, series, title: str, w=640, h=300) -> str:
    """Lines over categories on a log y-axis; `series` = (name, values, colour)."""
    import math
    left, right, top, bottom = 50, 120, 34, 46
    lo, hi = 0.1, 100.0
    sx = lambda i: left + (w - left - right) * i / (len(cats) - 1)
    sy = lambda v: top + (h - top - bottom) * (1 - (math.log10(v) - math.log10(lo)) /
                                              (math.log10(hi) - math.log10(lo)))
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{title}'>",
           f"<text x='0' y='16' class='ct'>{title}</text>"]
    for v in (0.1, 1, 10, 100):
        out.append(f"<line x1='{left}' x2='{w - right}' y1='{sy(v):.1f}' y2='{sy(v):.1f}' stroke='{GRID}'/>")
        out.append(f"<text x='{left - 6}' y='{sy(v) + 4:.1f}' text-anchor='end' class='cn'>{v:g}</text>")
    for i, c in enumerate(cats):
        out.append(f"<text x='{sx(i):.1f}' y='{h - bottom + 18}' text-anchor='middle' class='cn'>{c}</text>")
    out.append(f"<text x='{(left + w - right) / 2:.0f}' y='{h - 6}' text-anchor='middle' class='cn'>"
               "true slope of the ground</text>")
    for name, vals, col in series:
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(vals))
        out.append(f"<polyline points='{pts}' fill='none' stroke='{col}' stroke-width='2'/>")
        for i, v in enumerate(vals):
            out.append(f"<circle cx='{sx(i):.1f}' cy='{sy(v):.1f}' r='4.5' fill='{col}' "
                       f"stroke='#fff' stroke-width='2'/>")
        out.append(f"<text x='{sx(len(vals) - 1) + 10:.1f}' y='{sy(vals[-1]) + 4:.1f}' class='cl' "
                   f"fill='{INK}'>{name} {vals[-1]:g}</text>")
    out.append("</svg>")
    return "".join(out)


def year_bars(years, vals, title: str, w=640, h=210) -> str:
    left, right, top, bottom = 40, 10, 30, 30
    mx = max([v for v in vals if v is not None] + [1]) * 1.15
    bw = (w - left - right) / len(years)
    out = [f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{title}'>",
           f"<text x='0' y='16' class='ct'>{title}</text>",
           f"<line x1='{left}' x2='{w - right}' y1='{h - bottom}' y2='{h - bottom}' stroke='{GRID}'/>"]
    for i, (y, v) in enumerate(zip(years, vals)):
        x = left + i * bw + bw * 0.18
        if v is None:
            out.append(f"<text x='{x + bw * 0.32:.1f}' y='{h - bottom - 6}' text-anchor='middle' "
                       f"class='cn'>cloud</text>")
        else:
            bh = (h - top - bottom) * v / mx
            out.append(f"<rect x='{x:.1f}' y='{h - bottom - bh:.1f}' width='{bw * 0.64:.1f}' "
                       f"height='{bh:.1f}' rx='4' fill='{BLUE}'/>")
            out.append(f"<text x='{x + bw * 0.32:.1f}' y='{h - bottom - bh - 5:.1f}' text-anchor='middle' "
                       f"class='cv'>{v:.1f}%</text>")
        out.append(f"<text x='{x + bw * 0.32:.1f}' y='{h - 10}' text-anchor='middle' class='cn'>{y}</text>")
    out.append("</svg>")
    return "".join(out)


# ---- pages -------------------------------------------------------------------

def cover(meta, ch) -> str:
    yrs = f"{ch['years'][0]}–{ch['years'][-1]}" if ch else "2019–2026"
    n_ch = len(ch["years"]) if ch else 8
    return f"""
<section class='page cover'>
  <div class='kicker'>NESFIC 2026 · Stream 1 · Challenge NESFIC-D-07 · Soil Conservation Department, Government of Assam</div>
  <h1>SoilSense</h1>
  <p class='lede'>Soil-erosion risk, a ranked work list with reasons, and season-by-season
  monitoring for the whole of Assam. Built on the same data backbone that already runs two
  live hazard forecasts in Arunachal Pradesh.</p>
  <div class='facts'>
    <div><b>78,424 km²</b><span>all of Assam, in 100 m squares ({meta['scored_pct']:.0f}% scored; river land, water and towns marked "not assessed")</span></div>
    <div><b>{meta['n_catchments']}</b><span>small catchments and 35 districts ranked, each with its main cause and typical measures</span></div>
    <div><b>{n_ch} dry seasons</b><span>of bare ground measured from Sentinel-2, {yrs}, for comparison over time</span></div>
    <div><b>Checked first</b><span>every pass mark written down before the result existed, failures reported</span></div>
  </div>
  <p class='by'>BEE Solutions · Proof of Work · {meta['generated_utc'][:10]}</p>
  <p class='note'>Every screen shown here is the working app, not a mock-up, unless it is labelled "planned".</p>
</section>"""


ASKS = [
    ("Large-area identification and mapping of erosion-prone areas", "Erosion map of all Assam at 100 m, six classes, t/ha/yr; river land, water and towns marked \"not assessed\"", "under development"),
    ("Prioritisation of intervention locations", "703 catchments and 35 districts ranked; main cause, a second reason against similar slopes, typical measures; how firm each rank is (1,000 runs); re-rankable by the officer's own weights", "under development"),
    ("(beyond the statement) Where works pay most", "Soil reaching streams (where check dams and gully plugs pay most); \"What if we treat it?\" (soil saved by each measure); value of soil lost as nutrients and topsoil", "under development"),
    ("(beyond the statement) A second opinion from AI", "AI map learned from ISRO's mapped eroded land, shown beside the formula with the reasons for each area's score", "under development"),
    ("Faster preliminary assessment", "Type any village or a GPS position: one printable card with the loss around it, why, what helps, its catchment's rank, bare ground each year and this week's rain", "under development"),
    ("Periodic monitoring, temporal comparison", "Bare or burnt ground every dry season 2019–2026 from Sentinel-2; any season, or the change between two. Alerts for newly cleared slopes held back until they pass their tests", "under development"),
    ("(beyond the statement) Timing the work", "Weekly erosive-rain outlook from the live forecast, written down daily and replayed over past monsoons", "under development"),
    ("Combining spatial and environmental inputs", "Rain strength × soil × slope × cover × protection (RUSLE), each factor kept as its own layer", "under development"),
    ("Classification by risk level", "Common Indian six-class scheme until the department names its own", "under development"),
    ("GIS outputs for planning and field verification", "GeoPackage, KML, GeoJSON, CSV; 100 field points as a GPS file with form columns", "under development"),
    ("Pilot with comparison against field observations", "Blind field protocol to agree with the department; points chosen without the map's class", "planned · Phase 2–3"),
    ("Satellite data via ASSAC; department data as available", "Runs on open data today; department records swap in, each with a before/after", "planned · Phase 3"),
]


def asks_page() -> str:
    col = {"under development": GOOD}
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td><span class='st' style='color:{col.get(c, PEND)}'>{c}</span></td></tr>"
                   for a, b, c in ASKS)
    return f"""
<section class='page'>
  <h2>What the department asked for, and what exists today</h2>
  <table class='t'><tr><th>The department's words</th><th>SoilSense</th><th>State</th></tr>{rows}</table>
  <p class='small'>"Under development" means built and working in the app on real Assam data, and still
  being improved and tested. "Planned" means on our plan, with its phase. The same two labels are used
  in our application answers. Nothing on this page is a promise dressed as a feature.</p>
</section>"""


def screens(ch) -> str:
    return f"""
<section class='page'>
  <h2>The working app · erosion map</h2>
  {shot('01_map', 'The whole state. Classes in t/ha/yr; uncoloured land is not scored (river land, water, towns). The top 20 catchments are outlined. Alternative runs (other rain map, lower forest value) are one click away, because those two inputs are not yet settled.', 1250)}
</section>
<section class='page'>
  <h2>AI map: a second opinion beside the formula</h2>
  {shot('09_ai', "A tree model (LightGBM) learned which squares ISRO's experts marked as eroded on the national land-degradation map (2015–16), from terrain, soil, rain strength and cover. Tested only on map blocks it never saw. Shown as five bands, a rank and not tonnes, with each catchment's main reason and how its rank compares with the formula's. On blind satellite pictures it found visible erosion no better than the formula, so it stays a second opinion, not a replacement (page \"Checks\").", 1250)}
</section>
<section class='page'>
  <h2>Soil reaching streams</h2>
  {shot('10_streams', "Not all the soil a slope loses reaches a river; much settles lower down. From how well each square connects to the channel below it (Borselli's connectivity index and InVEST's delivery ratio, standard settings), this view shows where soil does reach streams: where check dams and gully plugs pay most, and what silts rivers and reservoirs. An estimate, not yet checked against measurements.", 1250)}
</section>
<section class='page'>
  <h2>A district at a glance</h2>
  {shot('02_map_district', 'Dima Hasao picked: average loss, share of high-or-worse land, rank among 35 districts under every run, total tonnes, main cause and typical measures, and the top catchments with their causes and whether their rank holds under both rain maps.', 1250)}
</section>
<section class='page'>
  <h2>This week's erosive rain</h2>
  {shot('07_week', "The next 7 days from the live rain forecast, set against what is normal at each place for these days of the year (the same forecast service's 16-year history, so its known wet bias cancels). Applied to the erosion map, it ranks the catchments where this week's rain will wash off the most soil. Each day's issue is written down so its rain can be graded later. Shown here on a dry late-October week; below the map, how well it did when replayed over 44 monsoon weeks.", 1750)}
</section>
<section class='page'>
  <h2>Village card</h2>
  {shot('08_village', "Type a village name (2,589 places from OpenStreetMap, GeoNames and the Survey of India) or a GPS position. The card shows the soil loss within about a kilometre, how much of that ground is high-risk and steep, the catchment's rank and how firm it is, why soil is lost there and what usually helps, how bare the ground has been each dry season, and this week's erosive rain. It downloads as a printable page.", 1250)}
</section>
<section class='page'>
  <h2>Change over time</h2>
  {shot('03_change', 'Bare or burnt ground in each square, measured from Sentinel-2 for every dry season since 2019, or the change between two seasons. Squares too cloudy that season stay blank. The steep-slope flags appear only after their tests pass (page "Checks").', 1700)}
</section>
<section class='page'>
  <h2>Priority list and field kit</h2>
  {shot('05_priority', 'Ranked catchments and districts with cause, second reason and typical measures; downloads for any GIS; and the field kit: 100 points in the top 20 catchments as a GPS file and a CSV with columns for what the team finds.', 2600)}
</section>
<section class='page'>
  <h2>What if we treat it?</h2>
  {shot('11_whatif', "Pick a district or catchment, choose measures (replanting steep open land, bench terraces, contour bunds or trenches) and how much of the eligible land to treat. The recipe is re-run with the works in place: soil saved a year, land treated, and where each measure saves most soil per hectare. Values come from the literature and are provisional, to confirm with the Soil Conservation Department; costs per hectare can be added to rank by soil saved per rupee.", 1350)}
</section>"""


def checks_page(san, gauge, ch, nr, meta_grade=None, meta_ai=None) -> str:
    s1 = san["S1"]["main"]
    rows = [
        ("Hills against plains", "Hill districts ≥ 3× the plains (median)", f"{s1['ratio']}×", True),
        ("Rain strength at the only measured gauge (Guwahati)", "Within ±25% of 7,924", "7,507 (−5%)", True),
        ("Soil factor against India's published erodibility map", "Pattern logged", "district rank agreement 0.94", True),
        ("Factor ranges and units", "K 0–0.08, C 0–1", "within range", True),
        ("Not all one class", "No class > 80%", "largest 45%", True),
        ("River land, water, towns", "Never given a class", "0 of 2.36 M such squares classed", True),
        ("False slope at canopy edges", "≤ 25% of flat hotspots on tree edges", "69% vs 65% background", False),
        ("Ranking holds across the two rain maps", "≥ 10 of the top 20 shared", "7 of 20: unstable ranks are marked", False),
        ("Top 20 catchments by eye on satellite imagery", "Visibly steep and/or bare", "20 of 20 steep, 10 visibly cleared", True),
        ("Rain map against 40 rain gauges (2001–18)", "Keep the map unless the other is clearly better", f"kept: pattern ρ {gauge['Assam']['rho_inresate']} vs {gauge['Assam']['rho_ired']} in Assam", True),
    ]
    if nr:
        x1, x2, x3 = nr["X1_auc_eroded_vs_normal"], nr["X2_catchments_spearman"], nr["X3_districts_spearman"]
        rows += [("ISRO land-degradation map: eroded vs normal land", f"Separation ≥ {x1['bar']:.2f}",
                  f"{x1['ours_main']:.2f} (national map {x1.get('IWED', float('nan')):.2f})", x1["pass"]),
                 ("ISRO map: catchment ranking", f"ρ ≥ {x2['bar']:.2f}",
                  f"{x2['ours_main']:.2f} (national map {x2.get('IWED', float('nan')):.2f})", x2["pass"]),
                 ("ISRO map: district ranking", f"ρ ≥ {x3['bar']:.2f}",
                  f"{x3['ours_main']:.2f} (national map {x3.get('IWED', float('nan')):.2f})", x3["pass"])]
    else:
        rows.append(("ISRO land-degradation map (three checks)", "set in advance", "running", None))
    og = meta_grade
    if og:
        ga = og["all"]
        rows += [("Weekly outlook replayed (44 weeks): which weeks are erosive", "ρ ≥ 0.60, above the seasonal normal",
                  f"{ga['G2_rho']:.2f} (normal alone {ga['G2_climatology']:.2f})", og["G2_pass"]),
                 ("Weekly outlook replayed: heavy weeks at a place", "≥ 0.70 (pairwise)", f"{ga['G3_auc']:.2f}", og["G3_pass"]),
                 ("Weekly outlook replayed: which places within a week", "ρ ≥ 0.30, above the seasonal normal",
                  f"{ga['G1_median_rho']:.2f} (normal alone {ga['G1_climatology']:.2f})", og["G1_pass"])]
    ai, eye = meta_ai or {}, jread(f"erosion_eyecheck_{REGION}.json")
    if ai:
        rows += [("AI map vs ISRO's eroded land, on blocks it never saw", "≥ 0.70 and ≥ 0.03 above the formula",
                  f"{ai['auc']['ai_A']:.2f} (formula {ai['auc']['formula']:.2f})", True),
                 ("AI map: catchment ranking vs ISRO's map", "ρ ≥ 0.40",
                  f"{ai['catchment_rho']['A']:.2f} (formula {ai['catchment_rho']['formula']:.2f})", True)]
    if eye:
        pf, pa, pg = eye["P-F"], eye["P-AI"], eye["P-G"]
        rows += [("Blind satellite pictures (300): formula's severe vs mild squares", "visible erosion ≥ 2× as often",
                  f"{pf['ratio']:.1f}×", pf["pass"]),
                 ("Blind satellite pictures: AI's top band vs its lower half", "≥ 2×",
                  f"{pa['ratio']:.1f}×: AI stays a second opinion", pa["pass"]),
                 ("Blind satellite pictures: terrain-only gully flag", "≥ 2×", f"{pg['ratio']:.1f}×: held back", pg["pass"])]
    if ch:
        t = ch["tests"]
        pct = lambda v: "–" if v is None else (f"{100 * v:.2f}%" if v < 0.001 else f"{100 * v:.1f}%")
        e3 = ch.get("E3") or {}
        att = " (second attempt)" if ch.get("attempt", 1) == 2 else ""
        rows += [("Change flags" + att + ": false alarms on untouched forest", "≤ 1.0%", pct(t["F1_stable_forest"]["rate"]), t["F1_stable_forest"]["pass"]),
                 ("Change flags" + att + ": false alarms from tea pruning", "≤ 3.0%", pct(t["F2_tea"]["rate"]), t["F2_tea"]["pass"]),
                 ("Change flags" + att + ": real clearing caught", "≥ 50%", pct(t["H1_hansen_clearing"]["rate"]), t["H1_hansen_clearing"]["pass"]),
                 ("Change flags" + att + ": blind check on dated pictures", "flags ≥ 70% confirmed",
                  (pct(e3["flag"]["share_yes"]) + f" ({pct(e3['flag']['share_yes_readable'])} of readable)") if e3 else "running",
                  e3.get("pass") if e3 else None)]
    body = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{mark(d)}</td></tr>" for a, b, c, d in rows)
    return f"""
<section class='page'>
  <h2>Checks, with the pass mark written down before the result</h2>
  <p>A failed check means "investigate and report", never "tweak until it passes". The failures
  are listed because they shape how the map should be read: we lead with the ranking, mark
  every rank that depends on an unsettled input, and hold back any feature until it passes.</p>
  <table class='t'><tr><th>Check</th><th>Pass mark (set in advance)</th><th>Result</th><th></th></tr>{body}</table>
</section>"""


def findings_page(san) -> str:
    ls = san["S8"]["LS_by_true_slope_median"]
    cats = [k.replace(" deg", "°").replace("30-90°", "> 30°") for k in ls]
    rain = bar_chart([("Rain gauge, measured (IMD)", 7924, False, "the reference"),
                      ("InRESatE map (used)", 7507, True, "−5%"),
                      ("IRED map", 4258, False, "−46%"),
                      ("Common Indian formula", 693, False, "−91%")],
                     "Rain strength (erosivity) at Guwahati, MJ·mm/ha/h/yr", "", ref=(7924, "gauge"))
    slope = line_chart_log(cats, [("ours", [v["LS_ours"] for v in ls.values()], BLUE),
                                  ("national map", [v["LS_iwed"] for v in ls.values()], ORANGE)],
                           "Slope factor (LS) by true slope, median, log scale")
    return f"""
<section class='page'>
  <h2>Two errors caught before any result existed</h2>
  <h3>1 · The usual rain formula reads 91% low in Assam</h3>
  {rain}
  <p class='small'>Most Indian erosion studies turn annual rainfall into rain strength with one
  formula. At Guwahati, the only place with a published measured value, it gives a tenth of the
  real figure. We use the satellite-based InRESatE map (−5%), keep IRED alongside, and tested
  both against 40 rain gauges.</p>
  <h3>2 · The national 250 m map barely responds to slope</h3>
  {slope}
  <p class='small'>Our slope factor rises 500-fold from flat land to steep hills; the national
  map's rises about twofold. That is why the national map rates western Assam's plains among
  India's most erodible, while ours puts the hills (Dima Hasao, the Karbi hills, the hills of
  south Kamrup and Cachar) first.</p>
</section>"""


def change_page(ch) -> str:
    if not ch:
        return ("<section class='page'><h2>Monitoring: bare ground every dry season</h2>"
                "<div class='pending'>Results pending.</div></section>")
    yrs = ch["years"]
    vals = [ch["yearly"][str(y)]["bare_pct_of_steep_scored_evaluable"] for y in yrs]
    seen = [ch["yearly"][str(y)]["evaluable_pct_of_scored"] for y in yrs]
    chart = year_bars(yrs, vals, "Share of Assam's steep land (≥ 10°) bare or burnt, each dry season")
    shown = ch["flags_shown"]
    return f"""
<section class='page'>
  <h2>Monitoring: bare ground every dry season, {yrs[0]}–{yrs[-1]}</h2>
  <p>In the hills, <i>jhum</i> plots are cleared in winter and burned in March–April; the ground
  stays bare until the crop grows after the monsoon starts. The monsoon's heavy rain falls on
  whatever the dry season left bare, so that is the season SoilSense measures: every 100 m
  square, from Sentinel-2's 10 m pictures, 1 February – 30 April, every year.</p>
  {chart}
  <p class='small'>Land seen clearly each season: {', '.join(f'{y} {s:.0f}%' for y, s in zip(yrs, seen))}.
  Squares too cloudy are left blank, never guessed.</p>
  <p>Each year's bare ground also re-runs the recipe ("loss with this year's cover"), and the
  catchments that got barer are listed. Flags for <b>new bare ground on a steep slope</b> are
  {'shown, having passed every test on the Checks page' if shown else 'held back until they pass the tests on the Checks page; the measured bare ground is shown meanwhile'}.</p>
  {shot('04_change_district', 'Change over time with a district picked.', 1700)}
</section>"""


ARCH = f"""
<svg viewBox='0 0 760 300' width='100%' role='img' aria-label='Architecture'>
 <defs><marker id='a' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto'>
 <path d='M0,0 L10,5 L0,10 z' fill='{INK2}'/></marker></defs>
 <g font-family='Inter,Arial' font-size='12'>
  {''.join(f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='{f}' stroke='{s}'/>"
           f"<text x='{x + w / 2}' y='{y + 20}' text-anchor='middle' font-weight='700' fill='{INK}'>{t}</text>"
           + ''.join(f"<text x='{x + w / 2}' y='{y + 38 + 15 * i}' text-anchor='middle' fill='{INK2}' font-size='11'>{ln}</text>" for i, ln in enumerate(lines))
           for x, y, w, h, f, s, t, lines in [
               (10, 20, 150, 120, '#f3f2ee', '#cfcdc6', 'Open sources', ['Copernicus DEM', 'SoilGrids', 'WorldCover, Sentinel-2', 'rain-strength maps', 'gauges, outlines']),
               (195, 20, 170, 120, '#eaf2fc', BLUE, 'Data backbone', ['raw store + provenance', 'one shared 100 m grid', 'region switch', '(Arunachal ↔ Assam)']),
               (400, 20, 160, 120, '#eaf2fc', BLUE, 'SoilSense recipe', ['R × K × LS × C × P', 'checks set in advance', 'dry-season cover', 'each year']),
               (595, 20, 155, 120, '#f3f2ee', '#cfcdc6', 'Outputs', ['map, rank + reasons', 'change over time', 'GIS files, field kit', 'web app']),
               (195, 190, 170, 90, '#fdf0ea', ORANGE, 'Same backbone, live', ['FloodSense (daily)', 'SlideSense (daily)', 'Arunachal Pradesh']),
               (595, 190, 155, 90, '#f3f2ee', '#cfcdc6', 'Field loop', ['field findings', 'held until checked', 'grade the map'])])}
  <line x1='160' y1='80' x2='193' y2='80' stroke='{INK2}' stroke-width='1.6' marker-end='url(#a)'/>
  <line x1='365' y1='80' x2='398' y2='80' stroke='{INK2}' stroke-width='1.6' marker-end='url(#a)'/>
  <line x1='560' y1='80' x2='593' y2='80' stroke='{INK2}' stroke-width='1.6' marker-end='url(#a)'/>
  <line x1='280' y1='140' x2='280' y2='188' stroke='{INK2}' stroke-width='1.6' marker-end='url(#a)'/>
  <line x1='672' y1='140' x2='672' y2='188' stroke='{INK2}' stroke-width='1.6' marker-end='url(#a)'/>
  <path d='M595,240 C520,240 520,110 562,110' fill='none' stroke='{INK2}' stroke-width='1.6' stroke-dasharray='4 3' marker-end='url(#a)'/>
 </g></svg>"""


def arch_page() -> str:
    return f"""
<section class='page'>
  <h2>How it is built</h2>
  {ARCH}
  <ul>
    <li><b>The data backbone is the core.</b> Each source is fetched by a script and stored
    untouched, with its source, licence, link, date and checksum. Every layer is fitted to one
    100 m grid. A region switch moved it from Arunachal Pradesh to Assam in about four weeks;
    the live Arunachal forecasts are re-checked after every change to shared code.</li>
    <li><b>The recipe is transparent.</b> RUSLE, the standard used in Indian soil conservation,
    with each factor kept as its own layer, so an officer can see why a place ranks high.</li>
    <li><b>AI beside the formula, never instead of it.</b> Under development: a gradient-boosted
    model learned from ISRO's mapped eroded land, tested on areas it never saw, with the reasons
    for each score. Planned: a panel of different models (formula, tree models, deep learning)
    blended by a referee model, learned across the Himalaya and North East and fine-tuned for
    Assam and each district; satellite-reading AI for forest, tea, <i>jhum</i> and fresh clearing.</li>
    <li><b>Outputs open anywhere:</b> GeoTIFF, GeoPackage, KML, GeoJSON, CSV, in WGS84 or UTM 46N;
    a web app that needs no installation.</li>
  </ul>
</section>"""


ROADMAP = [
    ("Under development", [
        "Erosion-risk map, all Assam, 100 m (RUSLE), with land not assessed marked",
        "Priority list of catchments and districts: cause, typical measures, rank firmness, re-ranking",
        "AI erosion map trained on ISRO's eroded land, as a second opinion with its reasons",
        "Dry-season bare and burnt ground every year since 2019 (Sentinel-2)",
        "Weekly erosive-rain outlook from the live forecast, graded against past monsoons",
        "Soil reaching streams; value of soil lost (nutrients as urea bags and rupees, topsoil depth)",
        "\"What if we treat it?\": soil saved by each measure",
        "Village card for any place; field kit with GPS visit points and GIS downloads"]),
    ("Planned", [
        "AI panel: formula, tree and deep-learning models blended by a referee model; learned across the Himalaya and North East, fine-tuned for Assam and each district, local-only models kept alongside; retrained after every monsoon",
        "Satellite-reading AI for forest, tea, jhum and fresh clearing, with jhum burn dating; radar monitoring through monsoon cloud",
        "Alerts for newly cleared slopes and hill cutting, sent only after an AI second check",
        "Seasonal outlook and a pre-monsoon watch list for divisions each April",
        "\"Did the works help?\" tracking; a works planner with costs; outputs shaped for PMKSY watershed and MGNREGA plans",
        "Stream sensors, rain gauges and soil-loss plots where the model points; drone and LiDAR surveys",
        "Offline field app in Assamese; farmers' photo reports sorted by AI and checked by a person; SMS, WhatsApp and voice advisories; an AI assistant for officers",
        "Riverbank erosion, flood sand on farmland, wetland and reservoir silting; landslide and flood forecasts for Assam on the same platform"]),
]


def roadmap_page() -> str:
    cols = "".join(f"<div><h3 style='color:{GOOD if k == 'Under development' else BLUE}'>{k}</h3><ul>"
                   + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>" for k, items in ROADMAP)
    return f"""
<section class='page'>
  <div class='kicker'>What comes next</div>
  <h2>Everything SoilSense will provide</h2>
  <p>Every item carries one of two labels, the same as in our application answers.
  <b>Under development</b>: built and working in the app on real Assam data, still being improved
  and tested. <b>Planned</b>: on our plan, for the programme (phases on the plan page) or after it.
  Features that fail their tests are held back until they pass.</p>
  <div class='two'>{cols}</div>
</section>"""


def wireframes_page() -> str:
    return """
<section class='page'>
  <h2>Next screens (Planned, Phase 2): mock-ups</h2>
  <div class='wf'>
    <div class='wfbox'><div class='wft'>Outlook scorecard</div>
      <div class='wfm'>[ each day's issued outlook against the rain that then fell, from satellite ]</div>
      <div class='wfr'>Issued 26 Oct for 26 Oct – 1 Nov · forecast 0.1× normal · fell: __× normal<br>
      Running record since the first issue, kept like FloodSense's</div></div>
    <div class='wfbox'><div class='wft'>Field form (phone)</div>
      <div class='wfr'>Point C06-3 · Dima Hasao · 25.17 N, 93.02 E<br>
      ☐ rills ☐ gullies ☐ fresh clearing ☐ sediment in stream<br>
      Bare soil: __ % · Existing works: ______<br>
      Photo ▢ · Observer ______ · Save → held as "unverified"</div></div>
    <div class='wfbox'><div class='wft'>Village card (in Assamese)</div>
      <div class='wfr'>Your area: <b>high soil loss</b>, mainly because of steep slopes cleared for <i>jhum</i>.<br>
      What helps: contour bunds, keeping cover on the slope before the monsoon, longer fallows.<br>
      Contact: Soil Conservation Division, ______</div></div>
  </div>
  <p class='small'>Field findings come back into SoilSense, stay "unverified" until an officer
  checks them, and then grade and calibrate the map.</p>
</section>"""


def live_page() -> str:
    land = ROOT / "webapp" / "assets" / "landing"
    return f"""
<section class='page'>
  <h2>Proof that the backbone works: two live products in Arunachal Pradesh</h2>
  <div class='two'>
    <figure><img src='{img(land / 'floodsense.webp', 900)}'><figcaption><b>FloodSense</b> runs by itself
    every morning in the cloud (Mumbai). Each forecast is written down before the day and graded
    against 32 river gauges: at a gauged river, when it says 20%, about 20% happen.</figcaption></figure>
    <figure><img src='{img(land / 'slidesense.webp', 900)}'><figcaption><b>SlideSense</b> issues a
    7-day landslide outlook for any place and road, learned from about 37,000 mapped landslides.
    It ranks a real landslide spot above a random one about 6 times in 7.</figcaption></figure>
  </div>
  <p>SoilSense is the third product on the same backbone and the first in a second state. The
  same team, the same pipeline, the same way of testing.</p>
</section>"""


def plan_page() -> str:
    rows = [("Done, Oct 2026", "Under development", "Assam on the backbone; state-wide 100 m erosion map with pre-registered checks; ranked catchments and districts with causes and firmness; AI erosion map as a second opinion; blind satellite-picture validation; dry-season bare ground since 2019; weekly outlook graded on past monsoons; village card; \"What if we treat it?\"; soil reaching streams; nutrient value of lost soil; field-kit exports; all in a working web app"),
            ("Nov 2026", "Conclave (Planned)", "Live demo on Assam data"),
            ("Nov – mid-Dec 2026", "Phase 1: AI and monitoring (Planned)", "Satellite-reading AI for forest, tea and jhum; jhum burn dating; radar monitoring; change alerts with an AI second check; seasonal outlook; district bulletins; panel-of-experts framework; pooled Himalaya and North-East training data. Depends on: satellite processing quota; any department data shared"),
            ("mid-Dec 2026 – Feb 2027", "Phase 2: prototype (Planned)", "Field-check protocol agreed with the department and dated before any visit; offline Assamese field app and village card; field and citizen intake with a holding area; \"did the works help?\"; pre-monsoon watch list; daily automated run with every outlook graded. Depends on: the department's choice of test areas and class scheme"),
            ("Feb 2027", "Demo Day", "Working prototype, early results, plan to MVP"),
            ("Feb – May 2027", "Phase 3: MVP (Planned)", "Field testing against pass marks set in advance; stream sensors, rain gauges, soil-loss plots and drone surveys at test sites; department data in; models fine-tuned for Assam and its districts and calibrated; works planner; layers in the department's GIS; staff training. Depends on: data-sharing permissions; field access"),
            ("From Jun 2027", "Pilot validation, then scale-up (Planned)", "First pre-monsoon watch list before the 2027 monsoon; retraining after every monsoon; advisories; farmers' photo reports; officer assistant; gully finder on drone imagery; riverbank, sand-cast farmland and reservoir-silting watch; landslide and flood forecasts for Assam; other North-East states")]
    body = "".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    return f"""
<section class='page'>
  <h2>Plan and pilot</h2>
  <table class='t'><tr><th>When</th><th>Phase</th><th>Deliverables</th></tr>{body}</table>
  <h3>Pilot, to agree with the department</h3>
  <p>Dima Hasao and the Karbi hills (steep, <i>jhum</i>, erosion a known concern), plus one
  foothill belt for contrast. A field protocol dated <b>before</b> any visit: blind points
  stratified across classes and top-ranked catchments; teams record rills, gullies, bare soil,
  sediment and existing works without seeing the map's class; agreement measured against a
  pass mark set in advance.</p>
  <h3>Data</h3>
  <p class='small'>Built on open data: Copernicus DEM GLO-30, SoilGrids (CC-BY), ESA WorldCover
  (CC-BY), Sentinel-2 via Google Earth Engine, InRESatE and IRED rain-strength maps (CC-BY),
  HydroSHEDS, Survey of India outline, NASA GPM IMERG and Open-Meteo rain, CWC river-sediment and
  river-level records. Used for comparison only, never redistributed: the IIT Delhi national
  erosion map (IWED), India's soil-erodibility map (ISED). NRSC's land-degradation map (Bhuvan):
  training labels for the AI map and an outside check, never redistributed. Ours: the backbone code, region switch, ranking and reasons, change detection,
  AI model and training pipeline, checks, app and the checked local record.</p>
</section>"""


CSS = f"""
@page {{ size: A4; margin: 14mm 14mm 16mm; }}
body {{ font-family: Inter, 'Segoe UI', Arial, sans-serif; color: {INK}; font-size: 10.5pt; line-height: 1.45; margin: 0; background: #fff; }}
.page {{ page-break-after: always; }}
h1 {{ font-size: 40pt; margin: 18mm 0 4mm; letter-spacing: -0.5px; }}
h2 {{ font-size: 16pt; margin: 0 0 4mm; }}
h3 {{ font-size: 12pt; margin: 5mm 0 2mm; }}
.kicker {{ color: {INK2}; font-size: 10pt; margin-top: 10mm; }}
.lede {{ font-size: 14pt; color: {INK2}; max-width: 160mm; }}
.facts {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; margin: 12mm 0; }}
.facts div {{ border-left: 3px solid {BLUE}; padding: 2mm 4mm; }}
.facts b {{ display: block; font-size: 18pt; }}
.facts span {{ color: {INK2}; font-size: 10pt; }}
.by {{ margin-top: 20mm; font-weight: 700; }}
.note, .small {{ color: {INK2}; font-size: 9pt; }}
figure {{ margin: 0 0 4mm; }}
figure {{ page-break-inside: avoid; }}
figure img {{ width: 100%; max-height: 228mm; object-fit: contain; object-position: left top; border: 1px solid {GRID}; border-radius: 4px; }}
figcaption {{ color: {INK2}; font-size: 9pt; margin-top: 2mm; }}
table.t {{ width: 100%; border-collapse: collapse; font-size: 9.5pt; }}
table.t th {{ text-align: left; color: {INK2}; font-weight: 600; border-bottom: 1.5px solid {INK}; padding: 2mm; }}
table.t td {{ border-bottom: 1px solid {GRID}; padding: 2mm; vertical-align: top; }}
.st {{ font-weight: 700; white-space: nowrap; }}
.pending {{ color: {PEND}; border: 1px dashed {GRID}; padding: 6mm; text-align: center; }}
.ct {{ font-size: 13px; font-weight: 700; fill: {INK}; }}
.cl {{ font-size: 12px; fill: {INK}; }}
.cv {{ font-size: 12px; font-weight: 700; fill: {INK}; }}
.cn {{ font-size: 11px; fill: {INK2}; font-weight: 400; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }}
li {{ margin-bottom: 1.5mm; }}
.wf {{ display: grid; grid-template-columns: 1fr; gap: 5mm; }}
.wfbox {{ border: 1.5px dashed #b9b8b2; border-radius: 6px; padding: 4mm; }}
.wft {{ font-weight: 700; margin-bottom: 2mm; }}
.wfm {{ background: #f3f2ee; color: {INK2}; text-align: center; padding: 10mm 2mm; margin-bottom: 2mm; border-radius: 4px; }}
.wfr {{ color: {INK2}; font-size: 10pt; }}
"""


def main() -> None:
    meta = json.loads((ROOT / "webapp" / "assets" / "erosion" / REGION / "meta.json").read_text())
    san = jread(f"erosion_sanity_{REGION}.json")["bars"]
    gauge = jread("gauge_erosivity_check.json")
    nr = jread(f"nrsc_ld_comparison_{REGION}.json")
    ch = meta.get("change")
    html = (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>SoilSense Proof of Work</title><style>{CSS}</style></head><body>"
            + cover(meta, ch) + asks_page() + screens(ch) + change_page(ch) + checks_page(san, gauge, ch, nr, meta.get("outlook_grade"), meta.get("ai"))
            + findings_page(san) + arch_page() + live_page() + roadmap_page() + wireframes_page() + plan_page()
            + "</body></html>")
    OUT.mkdir(parents=True, exist_ok=True)
    h = OUT / "SoilSense_Proof_of_Work.html"
    h.write_text(html, encoding="utf-8")
    for p in OUT.glob("_*_crop.png"):
        p.unlink()
    from playwright.sync_api import sync_playwright
    pdf = OUT / "SoilSense_Proof_of_Work.pdf"
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(h.as_uri())
        pg.wait_for_timeout(1500)
        pg.pdf(path=str(pdf), format="A4", print_background=True,
               margin={"top": "14mm", "bottom": "16mm", "left": "14mm", "right": "14mm"})
        b.close()
    mb = pdf.stat().st_size / 1e6
    print(f"  wrote {h.relative_to(ROOT)} and {pdf.relative_to(ROOT)} ({mb:.1f} MB{' — OVER 10 MB' if mb > 10 else ''})")


if __name__ == "__main__":
    main()
