"""CWC rain-gauge records for Assam and Arunachal Pradesh (NWDP), hourly and daily.

    python scripts/fetch/fetch_47_cwc_rainfall.py

Why: rain erosivity (R) is computed from rain INTENSITY, and our R comes from a
satellite map checked against one gauge-derived value (Guwahati). Ground gauges
at many stations could anchor it (EROSION_PLAN.md, register V-01).

Source: the Central Water Commission's rain gauges at its river stations, on the
National Water Data Portal (CKAN, open API, no key). ⚠️ The period in each file's
NAME is a generic template, not the data's real span (an NWDP file named
"1970-2025" held 2023-2025; see the nwdp memory note). The real years per
station are measured by scripts/inspect/cwc_rain_inventory.py.

National files, fetched without REGION. Licence on the portal: "Other (Open)".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import WEATHER, download, record

OUT = WEATHER / "cwc_rain"
DUMP = "https://nwdp.nwic.gov.in/datastore/dump/{rid}"
RESOURCES = {
    # manual hourly
    "912056fd-f866-4b7e-83a1-8870dc8bc184": "Assam, manual hourly, named 1961-1990",
    "bc45bf00-a4a6-4718-bc40-74b8e37c8316": "Assam, manual hourly, named 1991-2020",
    "a7694c60-412c-434d-8a65-65a68ad08bb9": "Arunachal Pradesh, manual hourly, named 1991-2020",
    # telemetry hourly
    "5cb88369-8b55-45a2-beb5-eaae184bb0ca": "Assam, telemetry hourly, named 1991-2020",
    "1f77001d-77b2-4d2d-a5af-b20168b9d517": "Assam, telemetry hourly, named 2021-2025",
    "f9dab5a8-4be1-4fa7-ba46-d08555a6653f": "Assam, telemetry hourly, named 2026-2030",
    "6c1277e3-9137-46c9-bc50-bd7735181e6f": "Arunachal Pradesh, telemetry hourly, named 1991-2020",
    "d887faf6-a866-4946-9f2d-5ff5ba9227c3": "Arunachal Pradesh, telemetry hourly, named 2021-2025",
    "6db6b360-9dab-4b3a-824e-62aa2655e880": "Arunachal Pradesh, telemetry hourly, named 2026-2030",
    # manual daily
    "f6a140c8-4ad7-4f7e-86a9-d6686dcbbe80": "Assam, manual daily, named 1961-1990",
    "b8ab233c-1a33-49f4-81a3-4ff6009b63cb": "Assam, manual daily, named 1991-2020",
    "51acd4ce-fb56-43f5-9a0b-ea621a1b9683": "Assam, manual daily, named 2021-2025",
    "29ba370f-3ead-4ffc-b92a-83527ca41d45": "Assam, manual daily, named 2026-2030",
    "5cde4079-431f-4d9c-b9cb-c6a1223f5afa": "Arunachal Pradesh, manual daily, named 1961-1990",
    "1476ba3e-4e35-438c-88e1-9e31fcaa2cbb": "Arunachal Pradesh, manual daily, named 1991-2020",
    "72bc22ad-ab98-4f24-992d-9e111b2cad3e": "Arunachal Pradesh, manual daily, named 2021-2025",
    "ef65bc64-cab5-4da0-953a-10244adfa646": "Arunachal Pradesh, manual daily, named 2026-2030",
}


def main() -> None:
    print("CWC rain gauges (NWDP) — Assam and Arunachal Pradesh")
    written = [download(DUMP.format(rid=rid), OUT / f"{rid}.csv", timeout=900) for rid in RESOURCES]
    record(OUT, source="CWC rainfall, manual and telemetry, hourly and daily (NWDP)",
           url="https://nwdp.nwic.gov.in/dataset/rainfall-cwc-manual-hourly", files=written,
           license_="Other (Open), as listed on nwdp.nwic.gov.in",
           notes="Files: " + "; ".join(f"{rid}.csv = {name}" for rid, name in RESOURCES.items())
                 + ". Periods in names are templates; real spans are measured per station.")


if __name__ == "__main__":
    main()
