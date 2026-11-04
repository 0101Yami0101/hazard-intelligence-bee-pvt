"""Ocean-atmosphere indices that shift a monsoon: IOD (DMI) and the MJO (RMM).

    python scripts/fetch/fetch_58_ocean_indices.py

Stored for a later season outlook; no product reads them yet. We already keep
ENSO's ONI (fetch_06_weather.py). The Indian Ocean Dipole is the other big
year-to-year driver of Indian monsoon rain; the MJO moves wet and dry spells
within a season, 30-60 days apart.

Licence: public domain (NOAA PSL); Bureau of Meteorology RMM is free to use
with attribution.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from common import WEATHER, UA, record

SRC = {
    "dmi.had.long.data": ("https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data",
                          "NOAA PSL Dipole Mode Index (IOD), monthly, from HadISST"),
    "rmm.74toRealtime.txt": ("http://www.bom.gov.au/climate/mjo/graphics/rmm.74toRealtime.txt",
                             "Bureau of Meteorology RMM index (MJO), daily since 1974"),
}
OUT = WEATHER / "ocean_indices"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (url, source) in SRC.items():
        try:
            r = requests.get(url, headers={**UA, "Accept": "text/plain"}, timeout=120)
            r.raise_for_status()
        except Exception as e:  # noqa: BLE001
            print(f"  ! {name}: {e}")
            continue
        dest = OUT / name
        dest.write_bytes(r.content)
        print(f"  {name}  {len(r.content) / 1e3:.0f} kB")
        record(OUT, source=source, url=url, files=[dest],
               license_="Public domain (NOAA)" if "noaa" in url else "Free with attribution (BoM)",
               notes="Stored for a season outlook beside ENSO's ONI; no product reads it yet."
                     + (" This BoM file stopped updating on 2024-02-24." if "bom" in url else ""))


if __name__ == "__main__":
    main()
