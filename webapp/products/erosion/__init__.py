"""SoilSense — the soil-erosion module (Assam first; NESFIC-D-07).

The same backbone moved to a second state and a third hazard: rain strength,
soil, slope and ground cover, combined with the standard soil-loss recipe
(RUSLE), then ranked into a work list of small catchments and districts.

⚠️ Status is "building". This is the first version (Phase 0): the map and the
list are real and checked, but two inputs cannot yet be pinned down with open
data — which rain-strength map is right, and the cover value for land the
satellite map calls "tree" (forest, tea gardens and jhum fallow together). The
pages show both, and mark every ranking that depends on them. Every
provisional choice is listed, with what would change it, in
docs/design/EROSION_PLAN.md ("Revisit register").

Data: webapp/assets/erosion/<region>/, written by
scripts/run/export_erosion_bundle.py. Nothing here reads the shared Arunachal
grid; the module carries its own state's geography.
"""
