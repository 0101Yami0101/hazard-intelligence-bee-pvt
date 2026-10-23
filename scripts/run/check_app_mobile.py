"""Phone and tablet check of every page: errors, sideways scrolling, things
sticking out past the screen, whether the menu can be opened, tiny text.

    python scripts/run/check_app_mobile.py TAG [--shots] [--only phone,tablet] [--pages a,b]
                                               [--py exe] [--app dir] [--port n]
                                               [--set ipad|tablets] [--browser webkit]

14 pages x 4 screens (phone 390, small phone 360, tablet 768, tablet on its
side 1024), about 25 minutes. Needs playwright. Screenshots and a JSON of
every measurement go beside this script's working folder, in mobile_TAG/.

`--set ipad`: the iPads on sale in 2026, upright and on their side, and two
Split View widths (14 screens). `--set tablets`: three Android tablets and a
Surface. `--browser webkit` runs them in WebKit, the engine of every browser
on an iPad (`python -m playwright install webkit` once). Added 2026-10-12.
First run 2026-10-10 (docs/design/FLOOD_SCREEN_PLAN.md): 4 of 56 with a
fault before the fixes, 0 after."""
import json, re, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

import tempfile
S = Path(tempfile.gettempdir()) / "hazard_app_checks"
S.mkdir(exist_ok=True)
tag = sys.argv[1]
arg = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
py, app, PORT = arg("--py", sys.executable), arg("--app", str(Path(__file__).resolve().parents[2])), int(arg("--port", "8799"))
SHOTS = S / f"mobile_{tag}"
SHOTS.mkdir(exist_ok=True)
SETS = {
    "default": [("phone", 390, 844, True), ("phone-small", 360, 740, True),
                ("tablet", 768, 1024, True), ("tablet-wide", 1024, 768, False)],
    # CSS sizes of the full screen; Safari's own bars take about 75 px of the
    # height, which is why each is tried a little shorter than the glass.
    "ipad": [("mini", 744, 1058, True), ("ipad10", 810, 1005, True), ("air11", 820, 1105, True),
             ("pro11", 834, 1135, True), ("air13", 1024, 1291, True), ("pro13", 1032, 1301, True),
             ("mini-side", 1133, 669, True), ("ipad10-side", 1080, 735, True),
             ("air11-side", 1180, 745, True), ("pro11-side", 1210, 759, True),
             ("air13-side", 1366, 949, True), ("pro13-side", 1376, 957, True),
             ("split-half-11", 590, 745, True), ("split-half-13", 683, 949, True)],
    "tablets": [("tab-8in", 600, 890, True), ("tab-11in", 800, 1210, True),
                ("tab-11in-side", 1280, 730, True), ("surface", 912, 1300, True)],
}
VIEWPORTS = SETS[arg("--set", "default")]
ENGINE = arg("--browser", "chromium")
PAGES = [("landing", "", None, None),
         ("slope-forecast", "landslide&geo=denied", None, None),
         ("slope-forecast-place", "landslide&geo=denied", None, "Tawang"),
         ("slope-roads", "landslide&geo=denied", "Roads", None),
         ("slope-susceptibility", "landslide&geo=denied", "Susceptibility", None),
         ("flood-forecast", "flood", None, None),
         ("flood-forecast-place", "flood", None, "Pasighat"),
         ("flood-prone", "flood", "Flood-prone ground", None),
         ("flood-prone-place", "flood", "Flood-prone ground", "Pasighat"),
         ("flood-catchments", "flood", "Catchments", None),
         ("flood-catchments-place", "flood", "Catchments", "Pasighat"),
         ("backbone-pipeline", "backbone", None, None),
         ("backbone-catalogue", "backbone", "Data catalogue", None),
         ("backbone-layers", "backbone", "Layer explorer", None),
         # SoilSense (Assam), added 2026-10-19
         ("erosion-map", "erosion", None, None),
         ("erosion-list", "erosion", "Priority list", None),
         ("erosion-how", "erosion", "How to read this", None)]

MEASURE = """() => {
  const vw = document.documentElement.clientWidth;
  const main = document.querySelector('[data-testid="stMain"]') || document.body;
  const out = [];
  for (const el of main.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    if (r.right > vw + 2 || r.left < -2) {
      // inside something that scrolls sideways on purpose (a table, a chart)? then it is fine
      let p = el.parentElement, scroller = false, clipped = false;
      while (p && p !== document.body) {
        const pc = getComputedStyle(p);
        if (/(auto|scroll)/.test(pc.overflowX) && p.scrollWidth > p.clientWidth + 1) { scroller = true; break; }
        if (/(hidden|clip)/.test(pc.overflowX)) { const pr = p.getBoundingClientRect(); if (pr.right <= vw + 2 && pr.left >= -2) { clipped = true; break; } }
        p = p.parentElement;
      }
      if (!scroller) out.push({tag: el.tagName.toLowerCase(), cls: (el.className && el.className.baseVal === undefined ? String(el.className) : '').slice(0, 60),
                               tid: el.getAttribute('data-testid') || '', right: Math.round(r.right), left: Math.round(r.left),
                               w: Math.round(r.width), clipped, text: (el.innerText || '').slice(0, 40).replace(/\\n/g, ' ')});
    }
  }
  let tiny = 0, texts = 0;
  const w = document.createTreeWalker(main, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) { const t = w.currentNode; if (!t.nodeValue.trim()) continue;
    const e = t.parentElement; const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none' || !e.getClientRects().length) continue;
    texts++; if (parseFloat(cs.fontSize) < 9.5) tiny++; }
  const iframes = [...main.querySelectorAll('iframe')].map(f => { const r = f.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }).filter(x => x[1] > 100);
  const tables = main.querySelectorAll('[data-testid="stDataFrame"]').length;
  return {vw, tables, docW: document.documentElement.scrollWidth, mainW: main.scrollWidth, mainCW: main.clientWidth,
          sticking: out.filter(o => !o.clipped).slice(0, 8), clippedCount: out.filter(o => o.clipped).length,
          tiny, texts, maps: iframes, height: Math.round(main.scrollHeight)};
}"""

def _running() -> bool:
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=2)
        return True
    except Exception:
        return False


class _Kept:
    """An app someone else started on this port: use it, leave it running."""
    def terminate(self): pass


# ⚠️ Every fresh copy of the app fetches live rain again. A night of runs, each
# starting its own, tripped the free weather service's limit and the landslide
# page came up "Live rainfall is unavailable" (2026-10-13). For a long session
# start the app once on --port and let every run use it.
srv = _Kept() if _running() else subprocess.Popen(
    [py, "-m", "streamlit", "run", "webapp/app.py", "--server.port", str(PORT),
     "--server.headless", "true", "--browser.gatherUsageStats", "false"],
    cwd=app, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
results, bad = [], 0


def settle(pg, least: int) -> None:
    """Wait `least` ms, then until the page has stopped working: no "running"
    mark, no grey placeholder, no spinner (60 s at most). A fixed wait was
    enough in Chromium and not in WebKit, which is slower here and was
    measured mid-load (2026-10-12)."""
    pg.wait_for_timeout(least)
    for _ in range(120):
        busy = pg.evaluate("""() => !!document.querySelector(
            '[data-testid="stStatusWidget"], [data-testid="stSkeleton"], [data-testid="stSpinner"]')""")
        if not busy:
            break
        pg.wait_for_timeout(500)
    pg.wait_for_timeout(1500)


def open_menu(pg) -> bool:
    """True if the sidebar is (or can be made) visible."""
    sb = pg.locator("[data-testid='stSidebar']")
    if sb.count() and sb.first.bounding_box() and sb.first.bounding_box()["x"] >= -5 and sb.first.bounding_box()["width"] > 100:
        return True
    for sel in ("[data-testid='stExpandSidebarButton']", "[data-testid='stSidebarCollapsedControl'] button",
                "[data-testid='stSidebarCollapsedControl']", "button[kind='headerNoPadding']"):
        b = pg.locator(sel)
        if b.count() and b.first.is_visible():
            b.first.click(); pg.wait_for_timeout(900)
            bb = sb.first.bounding_box() if sb.count() else None
            if bb and bb["x"] >= -5:
                return True
    return False


def close_menu(pg, mobile) -> None:
    if not mobile:
        return
    for sel in ("[data-testid='stSidebarCollapseButton'] button", "[data-testid='stSidebarCollapseButton']"):
        b = pg.locator(sel)
        if b.count() and b.first.is_visible():
            b.first.click(); pg.wait_for_timeout(700)
            return


try:
    for _ in range(90):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=2); break
        except Exception:
            time.sleep(1)
    with sync_playwright() as p:
        b = getattr(p, ENGINE).launch(headless=True)
        only, pages = arg("--only", ""), arg("--pages", "")
        for vname, vw, vh, mobile in [v for v in VIEWPORTS if not only or v[0] in only.split(",")]:
            ctx = b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=2 if mobile else 1,
                                is_mobile=mobile and (vw < 700 or ENGINE == "webkit"),
                                has_touch=mobile)
            for name, q, view, place in [x for x in PAGES if not pages or x[0] in pages.split(",")]:
                pg = ctx.new_page()
                pg.goto(f"http://localhost:{PORT}/" + (f"?m={q}" if q else ""), timeout=90000)
                settle(pg, 13000 if q else 7000)
                menu = None
                if q:
                    menu = open_menu(pg)
                    if view and menu:
                        pg.locator("[data-testid='stSidebar'] button").filter(has_text=view).first.click()
                        settle(pg, 11000)
                        menu = open_menu(pg) if mobile else True
                    close_menu(pg, mobile)
                if place:
                    inp = pg.locator("[data-testid='stSelectbox'] input").first
                    try:
                        inp.click(timeout=8000); pg.wait_for_timeout(400); inp.fill(place); pg.wait_for_timeout(1100)
                        pg.keyboard.press("Enter"); settle(pg, 11000)
                    except Exception as e:
                        print(f"   [{vname} {name}] search box not usable: {type(e).__name__}")
                m = pg.evaluate(MEASURE)
                m["texts_main"] = m["texts"]
                exc = pg.locator("[data-testid='stException']").count()
                side = m["docW"] > m["vw"] + 2 or m["mainW"] > m["mainCW"] + 2
                issues = []
                if exc: issues.append(f"{exc} exception(s)")
                if side: issues.append(f"page scrolls sideways ({max(m['docW'], m['mainW'])} px on {m['vw']})")
                if m["sticking"]: issues.append(f"{len(m['sticking'])}+ things past the edge")
                if q and menu is False: issues.append("menu cannot be opened")
                # A table (st.dataframe) draws its cells on a canvas, so its text is not
                # counted here; a page of tables is not empty (SoilSense list, 2026-10-19).
                if q and m["texts"] < 40 and not m.get("tables"): issues.append(f"page looks empty ({m['texts']} pieces of text)")
                if m["tiny"] > 0.15 * max(m["texts"], 1): issues.append(f"small text: {m['tiny']} of {m['texts']} pieces under 9.5 px")
                bad += bool(issues)
                results.append({"viewport": vname, "page": name, "issues": issues, **m})
                print(f"{vname:12s} {name:24s} {'OK ' if not issues else 'ISSUE'} maps {m['maps']} tiny {m['tiny']}/{m['texts']} "
                      f"len {m['height']}px  " + "; ".join(issues), flush=True)
                for o in m["sticking"][:4]:
                    print(f"        past edge: <{o['tag']}> {o['tid'] or o['cls']} right={o['right']} w={o['w']} '{o['text']}'")
                if side:
                    wide = pg.evaluate("""() => { const vw = document.documentElement.clientWidth; const o = [];
                      for (const el of document.querySelectorAll('[data-testid="stMain"] *')) { const r = el.getBoundingClientRect();
                        if (r.width > 2 && r.height > 2 && r.right > vw + 2) o.push([Math.round(r.right), el.tagName.toLowerCase(),
                          el.getAttribute('data-testid') || String(el.className.baseVal === undefined ? el.className : '').slice(0, 50), Math.round(r.width)]); }
                      o.sort((a, b) => b[0] - a[0]); const seen = new Set(), out = [];
                      for (const x of o) { const k = x[1] + x[2]; if (!seen.has(k)) { seen.add(k); out.push(x); } } return out.slice(0, 10); }""")
                    for x in wide:
                        print(f"        wide: right={x[0]} <{x[1]}> {x[2]} w={x[3]}")
                if "--shots" in sys.argv or issues:
                    # the page scrolls inside its own box, so make the window as tall as the page
                    pg.set_viewport_size({"width": vw, "height": int(min(m["height"] + 80, 9000))})
                    pg.wait_for_timeout(1800)
                    pg.screenshot(path=str(SHOTS / f"{vname}_{name}.png"))
                pg.close()
            ctx.close()
        b.close()
finally:
    srv.terminate()
(S / f"mobile_{tag}.json").write_text(json.dumps(results, indent=1))
print(f"\nRESULT {tag}: {len(results)} page-and-screen combinations, {bad} with issues")
