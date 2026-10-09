"""The NWDP small-river discharge station registry — the 14-station second
pass of the WHEN/WHERE rollout, after the 17 CWC stations (see
docs/design/FLOOD_WHEN_PILOT_PLAN.md §8, flood_stations.py for the CWC
sibling registry this deliberately mirrors).

Coordinates are the government's own per-row lat/lon
(fetch_24_nwdp_discharge.py), EXCEPT Changlang and Ziro — both stations'
raw coordinates are wrong in NWDP's own data (Changlang's sits in Kashmir,
Ziro's in Uttarakhand; flagged automatically by fetch_24's bounding-box
check, matching the caveat already logged in
docs/data_research/DATA_VERIFICATION.md Section C). Both corrected here by
geocoding the real town (Changlang town, Changlang district;
Ziro town, Lower Subansiri district).

No danger level exists for any of these 14 — NWDP publishes discharge
(m3/sec), not a level with a government-defined danger threshold. Every
station uses the self-derived percentile method
(backtest_flood_when.py's derive_flood_days()), same as CWC stations with
no published threshold — not a stopgap, the standing method for this tier.
"""
from __future__ import annotations

STATIONS = {
    "Aalo_1": {"name": "Aalo", "district": "West Siang", "lat": 28.131260, "lon": 94.793982},
    "Basar_1": {"name": "Basar", "district": "Lepa-Rada", "lat": 27.983, "lon": 94.672},
    "Changlang": {"name": "Changlang", "district": "Changlang", "lat": 27.12, "lon": 95.71},  # corrected, see docstring
    "Changlang_1": {"name": "Changlang (2nd station)", "district": "Changlang", "lat": 27.133, "lon": 95.734},
    "Darak(Kamba)": {"name": "Darak (Kamba)", "district": "West Siang", "lat": 28.259, "lon": 94.677},
    "Deomali_1": {"name": "Deomali", "district": "Tirap", "lat": 27.200, "lon": 95.458},
    "Kamlang_1": {"name": "Kamlang", "district": "Lohit", "lat": 27.757, "lon": 96.359},
    "Kanubari_1": {"name": "Kanubari", "district": "Longding", "lat": 26.896, "lon": 95.290},
    "Miao_2": {"name": "Miao (NWDP)", "district": "Changlang", "lat": 27.443, "lon": 95.941},
    "Sagalee_1": {"name": "Sagalee", "district": "Papum Pare", "lat": 27.214, "lon": 93.689},
    "Tenga_1": {"name": "Tenga", "district": "West Kameng", "lat": 27.203, "lon": 92.565},
    "Tengapani Bridge_1": {"name": "Tengapani Bridge", "district": "Lohit", "lat": 27.774, "lon": 95.975},
    "Tissa Camp_1": {"name": "Tissa Camp", "district": "Tirap", "lat": 26.913, "lon": 95.365},
    "Ziro": {"name": "Ziro", "district": "Lower Subansiri", "lat": 27.63, "lon": 93.83},  # corrected, see docstring
}
