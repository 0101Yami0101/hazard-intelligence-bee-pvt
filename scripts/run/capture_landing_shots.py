"""Retake the two module pictures shown on the home page.

    python scripts/run/capture_landing_shots.py

Writes  webapp/assets/landing/slidesense.webp  (SlideSense forecast, Itanagar)
        webapp/assets/landing/floodsense.webp  (FloodSense forecast, Pasighat)

Starts the app on a spare port, opens each forecast page with a place
picked, hides the side menu, and saves the top of the page 960 px wide.
Run it again whenever those two screens change their look. Needs playwright
and internet (live rain, map tiles). It never presses "Run now".
"""
from __future__ import annotations

import io
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "webapp" / "assets" / "landing"
PORT = 8793
SHOTS = [("landslide", "Itanagar", "slidesense"), ("flood", "Pasighat", "floodsense")]
W_OUT, RATIO = 960, 820 / 1280          # the same shape for both, so the cards line up


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "webapp/app.py",
                            "--server.port", str(PORT), "--server.headless", "true",
                            "--browser.gatherUsageStats", "false"],
                           cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(90):
            try:
                urllib.request.urlopen(f"http://localhost:{PORT}/_stcore/health", timeout=2)
                break
            except Exception:
                time.sleep(1)
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            for mod, place, name in SHOTS:
                pg = b.new_page(viewport={"width": 1360, "height": 1000}, device_scale_factor=1)
                pg.goto(f"http://localhost:{PORT}/?m={mod}", timeout=90000)
                pg.wait_for_selector(".st-key-fs_col_r", timeout=120000)
                pg.wait_for_timeout(8000)
                inp = pg.locator(".st-key-fs_head [data-testid='stSelectbox'] input").first
                inp.click()
                pg.wait_for_timeout(300)
                inp.fill(place)
                pg.wait_for_timeout(1000)
                pg.keyboard.press("Enter")
                pg.wait_for_timeout(11000)
                pg.add_style_tag(content="[data-testid='stSidebar']{display:none!important}")
                pg.wait_for_timeout(2500)
                pg.set_viewport_size({"width": 1360, "height": 1500})
                pg.wait_for_timeout(2500)
                box = pg.evaluate("""() => { const r = document.querySelector(
                    "[data-testid='stMainBlockContainer']").getBoundingClientRect();
                    return {x: r.left, y: r.top, w: r.width}; }""")
                img = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
                x0, w, y0 = box["x"] - 14, box["w"] + 28, max(box["y"] - 6, 0)
                c = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + w * RATIO)))
                c = c.resize((W_OUT, int(round(W_OUT * RATIO))), Image.LANCZOS)
                c.save(OUT / f"{name}.webp", "WEBP", quality=80, method=6)
                print(f"  {name}.webp  {c.size}  {(OUT / (name + '.webp')).stat().st_size // 1024} KB")
                pg.close()
            b.close()
    finally:
        srv.terminate()


if __name__ == "__main__":
    main()
