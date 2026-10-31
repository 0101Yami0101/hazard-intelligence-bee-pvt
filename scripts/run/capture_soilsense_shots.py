"""Screenshots of every SoilSense page, for the NESFIC Proof of Work PDF.

    python scripts/run/capture_soilsense_shots.py

Starts the app on a spare port, opens SoilSense, visits each page (and the map
with one district picked), and saves full-width PNGs to docs/nesfic/shots/.
Needs playwright and internet (map tiles). Read-only: it presses page buttons
and pickers only.
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "nesfic" / "shots"
PORT = 8794
# (file name, sidebar button, district to pick or None, page height to keep)
SHOTS = [("01_map", "Erosion map", None, 1250),
         ("02_map_district", "Erosion map", "Dima Hasao", 1250),
         ("07_week", "This week", None, 1750),
         ("08_village", "Village card", "q:Haflong", 1250),
         ("03_change", "Change over time", None, 1700),
         ("04_change_district", "Change over time", "Dima Hasao", 1700),
         ("05_priority", "Priority list", None, 2600),
         ("06_method", "How to read this", None, 2400)]


def pick_district(pg, name: str) -> None:
    inp = pg.locator("[data-testid='stMain'] [data-testid='stSelectbox'] input").first
    inp.click()
    pg.wait_for_timeout(300)
    inp.fill(name)
    pg.wait_for_timeout(800)
    pg.keyboard.press("Enter")


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
            for name, button, district, height in SHOTS:
                pg = b.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
                pg.goto(f"http://localhost:{PORT}/?m=erosion", timeout=90000)
                nav = pg.locator("[data-testid='stSidebar'] button", has_text=button).first
                nav.wait_for(state="visible", timeout=120000)
                pg.wait_for_timeout(3000)
                nav.click()
                pg.wait_for_timeout(6000)
                if district and district.startswith("q:"):          # the village card's search box
                    box = pg.locator("[data-testid='stMain'] [data-testid='stTextInput'] input").first
                    box.fill(district[2:])
                    box.press("Enter")
                    pg.wait_for_timeout(9000)
                elif district:
                    pick_district(pg, district)
                    pg.wait_for_timeout(7000)
                pg.set_viewport_size({"width": 1440, "height": height})
                pg.wait_for_timeout(6000)              # map tiles
                pg.screenshot(path=str(OUT / f"{name}.png"), full_page=False)
                print(f"  {name}.png", flush=True)
                pg.close()
            b.close()
    finally:
        srv.terminate()


if __name__ == "__main__":
    main()
