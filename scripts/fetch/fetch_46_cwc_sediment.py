"""CWC daily suspended-sediment measurements for the North East (NWDP).

    python scripts/fetch/fetch_46_cwc_sediment.py

The soil-erosion module's only truly MEASURED check (EROSION_MODULE.md §7, V3):
how much mud the rivers carry. Published by the Central Water Commission on the
National Water Data Portal (CKAN, open API, no key), dataset
"Suspended Sediments (Manual - Daily), Central Water Commission (CWC)", one CSV
per state and period. Field: "Manual Daily Suspended Sediments (g/L)" =
concentration, with station, river, basin, district and coordinates.

Found 2026-10-20: CWC's daily DISCHARGE for Assam is not on the portal (only
Meghalaya among the North-East states), so concentration cannot be turned into
loads (t/yr) from this source alone. National river-flow data for the
transboundary Brahmaputra and Barak basins is withheld in India.

National files (one per state), fetched without REGION. Licence on the portal:
"Other (Open)".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import GAUGES, download, record

OUT = GAUGES / "cwc_sediment"
DUMP = "https://nwdp.nwic.gov.in/datastore/dump/{rid}"
DATASET = ("https://nwdp.nwic.gov.in/dataset/"
           "suspended-sediments-manual-daily-andhra-pradesh-department-central-water-commission-cwc")
RESOURCES = {
    "08cf3a3a-c6e5-4c7a-871d-28861a3f8b88": "Assam 1961-2025",
    "b809cd25-a40b-495c-91b3-67137963e542": "Assam 2026-2030",
    "a1dddacf-d5c8-4c6d-b1eb-cd403f1e4609": "Arunachal Pradesh 1961-2025",
    "a2415cb4-a63f-4894-81a6-7f07662b2ebc": "Arunachal Pradesh 2026-2030",
    "3c97f3c8-112a-4a36-8647-54a8748dd035": "Meghalaya 1961-2025",
    "c5e182c1-590c-4ac0-92ab-e743068932f7": "Meghalaya 2026-2030",
}


def main() -> None:
    print("CWC suspended sediment (NWDP) — North East")
    written = [download(DUMP.format(rid=rid), OUT / f"{rid}.csv", timeout=900)
               for rid in RESOURCES]
    record(OUT, source="CWC Suspended Sediments, Manual Daily (NWDP)", url=DATASET, files=written,
           license_="Other (Open), as listed on nwdp.nwic.gov.in",
           notes="Daily suspended-sediment concentration, g/L. Files: "
                 + "; ".join(f"{rid}.csv = {name}" for rid, name in RESOURCES.items())
                 + ". No CWC discharge for Assam on the portal.")


if __name__ == "__main__":
    main()
