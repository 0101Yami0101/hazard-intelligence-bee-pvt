"""IMD gridded daily rain, 0.25 degree, India (Pai et al. 2014), one file a year.

    python scripts/fetch/fetch_59_imd_rain.py [first_year] [last_year]

India's official rain history, built from thousands of rain gauges. Stored as a
second, independent rain ruler: the forecast reads Open-Meteo end to end, and a
gauge-based grid is the obvious cross-check. No product reads it yet. Default
1981-2025 (about 1.1 GB); IMD publishes back to 1901.

Format (from IMD's page): little-endian float32, 366 (or 365) days x 129 rows x
135 columns; first value 6.5N 66.5E, last 38.5N 100.0E; -999 = no data. Files
are kept exactly as served.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from common import WEATHER, UA, record

URL = "https://www.imdpune.gov.in/cmpg/Griddata/rainfall.php"
OUT = WEATHER / "imd_rain_025"


def main() -> None:
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 1981
    b = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for y in range(a, b + 1):
        dest = OUT / f"ind{y}_rfp25.grd"
        if not dest.exists():
            r = requests.post(URL, data={"rain": str(y)}, headers=UA, timeout=600)
            r.raise_for_status()
            days = len(r.content) / (129 * 135 * 4)
            if days not in (365, 366):
                print(f"  ! {y}: {len(r.content)} bytes is not a year of grids, skipped")
                continue
            dest.write_bytes(r.content)
            time.sleep(2)
        print(f"  {dest.name}  {dest.stat().st_size / 1e6:.1f} MB")
        files.append(dest)
    record(OUT, source="IMD gridded daily rainfall 0.25 deg (Pai et al. 2014)", url=URL,
           files=sorted(OUT.glob("ind*_rfp25.grd")),
           license_="No licence on the download page; IMD's data policy applies. "
                    "Confirm before commercial use.",
           notes="Gauge-based official rain grid. Stored as a second rain ruler to "
                 "cross-check Open-Meteo; no product reads it yet.")


if __name__ == "__main__":
    main()
