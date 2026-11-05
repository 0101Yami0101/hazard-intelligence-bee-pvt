"""The briefing's screen-guide pictures (docs/BRIEFING.md, Part B), taken from
the local app with a headless browser, then saved small as docs/briefing_shots/*.webp.

    python scripts/run/capture_briefing_shots.py
    python scripts/run/build_briefing.py

Take them after the 08:30 run, so the forecast on screen is today's.
"""
import subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

DEST = Path(__file__).resolve().parents[2] / "docs" / "briefing_shots"
out = Path(tempfile.mkdtemp())
PORT = 8811
ROOT = str(DEST.parents[1])
srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "webapp/app.py",
                        "--server.port", str(PORT), "--server.headless", "true",
                        "--browser.gatherUsageStats", "false"], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def shot(pg, sel, name, nth=0):
    el = pg.locator(sel).nth(nth)
    el.scroll_into_view_if_needed(); pg.wait_for_timeout(1200)
    pg.mouse.move(2, 2)
    el.screenshot(path=str(out / f"{name}.png"))
    print("ok", name, flush=True)


def pick(pg, place):
    inp = pg.locator(".st-key-fs_head [data-testid='stSelectbox'] input").first
    inp.click(); pg.wait_for_timeout(300); inp.fill(place); pg.wait_for_timeout(1200)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(16000)


try:
    for _ in range(90):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=2); break
        except Exception:
            time.sleep(1)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1536, "height": 900}, device_scale_factor=1)
        pg = ctx.new_page()
        # landing
        pg.goto(f"http://localhost:{PORT}/", timeout=90000)
        pg.wait_for_selector(".st-key-go_landslide button", timeout=180000); pg.wait_for_timeout(4000)
        shot(pg, ".st-key-land_wrap", "landing")
        # SlideSense forecast, Itanagar
        pg.goto(f"http://localhost:{PORT}/?m=landslide", timeout=90000)
        pg.wait_for_selector(".st-key-fs_col_r", timeout=240000); pg.wait_for_timeout(8000)
        pick(pg, "Itanagar")
        shot(pg, ".st-key-fs_main", "sl_main")
        shot(pg, ".fs-state", "sl_strip")
        # SlideSense Roads, a route
        pg.get_by_role("button", name="Roads").first.click(); pg.wait_for_timeout(12000)
        for key, val in (("rd_from", "Itanagar"), ("rd_to", "Ziro")):
            inp = pg.locator(f".st-key-{key} input, [data-testid='stSelectbox']:has(label:text-is('{'From' if key == 'rd_from' else 'To'}')) input").first
            inp.click(); pg.wait_for_timeout(300); inp.fill(val); pg.wait_for_timeout(1200)
            pg.keyboard.press("Enter"); pg.wait_for_timeout(9000)
        shot(pg, ".st-key-fs_main", "sl_roads_main")
        shot(pg, ".fs-state", "sl_roads_strip")
        # FloodSense, Pasighat
        pg.goto(f"http://localhost:{PORT}/?m=flood", timeout=90000)
        pg.wait_for_selector(".st-key-fs_col_r", timeout=240000); pg.wait_for_timeout(8000)
        pick(pg, "Pasighat")
        shot(pg, ".st-key-fs_main", "fl_main")
        shot(pg, ".fs-state", "fl_strip")
        # one gauge: Kibithu, 30 days then last 3 days
        g = pg.locator(".st-key-flv_gauge input").first
        g.scroll_into_view_if_needed(); g.click(); pg.wait_for_timeout(400); g.fill("Kibithu")
        pg.wait_for_timeout(900); pg.keyboard.press("Enter"); pg.wait_for_timeout(9000)
        col = "[data-testid='stColumn']:has(.st-key-flv_gspan)"
        shot(pg, col, "fl_gauge30", nth=0)
        pg.locator(".st-key-flv_gspan").get_by_text("Last 3 days").first.click(); pg.wait_for_timeout(9000)
        shot(pg, col, "fl_gauge3", nth=0)
        b.close()
finally:
    srv.terminate()

DEST.mkdir(parents=True, exist_ok=True)
for p in sorted(out.glob("*.png")):
    im = Image.open(p).convert("RGB")
    if im.width > 1400:
        im = im.resize((1400, round(im.height * 1400 / im.width)), Image.LANCZOS)
    im.save(DEST / f"{p.stem}.webp", "WEBP", quality=78, method=6)
print(f"saved to {DEST}")
