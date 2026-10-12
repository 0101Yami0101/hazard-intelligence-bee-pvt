"""Open every screen of the web app headlessly and report any exception.

    python scripts/run/check_app_screens.py

Uses Streamlit's own AppTest runner, so it exercises the real page code
(maps, panels, tables) without a browser. Each module and each of its
screens is opened once; the flood forecast screen is also opened with a
place selected, which is the path that draws the side panel. Any exception
is a failure. It does not judge how a screen looks — that still needs a
browser — only that every screen runs.
"""
from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
APP = str(ROOT / "webapp" / "app.py")

CASES = [
    ("landslide", "view", ["Forecast", "Roads", "Susceptibility"], None, {}),
    # SlideSense with a town, a district, a valley-floor point that snaps to
    # the nearest slope, a point outside the state, and a later day
    ("landslide", "view", ["Forecast", "Susceptibility"], "Tawang", {}),
    ("landslide", "view", ["Forecast", "Susceptibility"], "Upper Siang district", {}),
    ("landslide", "view", ["Forecast", "Susceptibility"], "28.0660, 95.3260", {}),
    ("landslide", "view", ["Forecast", "Susceptibility"], "26.2000, 91.7000", {}),
    ("landslide", "view", ["Forecast", "Roads"], None, {"day_i": "last"}),
    ("landslide", "view", ["Roads"], None, {"rd_from": "Itanagar", "rd_to": "Ziro"}),
    ("landslide", "view", ["Evidence", "Model & Validation"], None, {}),
    ("flood", "fl_view", ["Live forecast", "Flood-prone ground", "Catchments"], None, {}),
    ("flood", "fl_view", ["Live forecast"], "Pasighat", {}),
    ("flood", "fl_view", ["Live forecast"], "28.0660, 95.3260", {}),
    # one forecast day chosen instead of the whole week (flv_day -1 = week)
    ("flood", "fl_view", ["Live forecast"], "Pasighat", {"flv_day": 2}),
    ("flood", "fl_view", ["Live forecast"], None, {"flv_day": 5}),
    # the conditions panel's other tabs (Rain fetches live rain)
    ("flood", "fl_view", ["Live forecast"], "Pasighat", {"flv_cond": "Soil"}),
    ("flood", "fl_view", ["Live forecast"], "Aalo", {"flv_cond": "Rain"}),
    ("flood", "fl_view", ["Live forecast"], None, {"flv_cond": "Soil"}),
    # the other two pages with a place, and a later day on Catchments
    ("flood", "fl_view", ["Flood-prone ground", "Catchments"], "Pasighat", {}),
    ("flood", "fl_view", ["Flood-prone ground"], "Tawang", {}),
    ("flood", "fl_view", ["Catchments"], None, {"flc_day": 4}),
    ("flood", "fl_view", ["How to read this forecast"], None, {}),
    ("backbone", "bb_view", ["Pipeline", "Data catalogue", "Layer explorer"], None, {}),
]


def main() -> int:
    failures = 0
    # the home page: the module tiles and the story under them (core/landing.py)
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    story = sum("lp-sec" in str(m.value) or "lp-close" in str(m.value) for m in at.markdown)
    if at.exception or story < 5:
        failures += 1
        print(f"  FAIL  home page ({story} story blocks)")
        for e in at.exception:
            print("        " + str(e.message)[:300])
    else:
        print(f"  ok    home page ({story} story blocks)")
    for module, key, views, place, extra in CASES:
        for v in views:
            at = AppTest.from_file(APP, default_timeout=300)
            at.session_state["module"] = module
            at.session_state[key] = v
            if place:
                at.session_state["search"] = place
            for k, val in extra.items():
                if val != "last":
                    at.session_state[k] = val
            at.run()
            if "last" in extra.values():
                # the last forecast day: its index depends on today's rain
                # window, so it is read from the day buttons and clicked
                btn = [x for x in at.button if str(x.key).startswith(("sl_d", "flc_d"))]
                if btn:
                    btn[-1].click().run()
            where = (f"{module} / {v}" + (f" / {place}" if place else "")
                     + (f" / {extra}" if extra else ""))
            if at.exception:
                failures += 1
                print(f"  FAIL  {where}")
                for e in at.exception:
                    print("        " + str(e.message)[:300])
            else:
                print(f"  ok    {where}")
    print(f"\n{'PASS' if not failures else 'FAIL'} — {failures} screen(s) raised an exception")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
