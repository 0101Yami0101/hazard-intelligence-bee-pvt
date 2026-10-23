"""Rainfall erosivity (the R factor) for India — two open, measured-intensity maps.

The soil-erosion module's rain factor (docs/design/EROSION_PLAN.md, R2/R3). The
annual-rainfall formula in common Indian use, R = 79 + 0.363 x rain (Singh et al.
1981), reads 91% low against the only gauge-derived value we have (Guwahati, 7,924
MJ mm/ha/h/yr), so R comes from maps built from rain *intensity*:

  InRESatE  Das, Jain & Gupta 2022 (IIT Roorkee), Catena 212:106067.
            30-min IMERG, 2001-2018, 0.1 deg. Zenodo 11064154.  -> the Phase 0 R
  IRED      Raj et al. 2022 (IIT Delhi). Hourly IMDAA, 1979-2018, 0.12 deg.
            Zenodo 6469693.                                   -> sensitivity case

Both are national, so one fetch serves every region; run it without REGION.
Both are CC-BY 4.0. Archives are kept as downloaded and unpacked beside them.
"""
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import WEATHER, download, record

OUT = WEATHER / "erosivity"

SETS = {
    "inresate": {
        "source": "InRESatE R-factor (Das, Jain & Gupta 2022)",
        "page": "https://doi.org/10.5281/zenodo.11064154",
        "files": {
            "R-factor.zip": "https://zenodo.org/records/11064154/files/R-factor.zip?download=1",
            "read_me.docx": "https://zenodo.org/records/11064154/files/read%20me.docx?download=1",
            # added 2026-10-20: the daily rain -> erosivity model behind the map, to
            # turn decades of DAILY gauge rain into R at the gauges (register V-01)
            "daily_model_parameters.zip": ("https://zenodo.org/records/11064154/files/"
                                           "Daily%20Rainfall%20Erosivity%20Model%20Parameters.zip?download=1"),
        },
        "notes": ("Annual R, MJ mm ha-1 h-1 yr-1, from 30-min IMERG Final 2001-2018, 0.1 deg. "
                  "MATLAB files R.mat / lat.mat / lon.mat. Guwahati: 7,507 vs gauge 7,924 (-5%). "
                  "Paper: Catena 212 (2022) 106067, doi:10.1016/j.catena.2022.106067."),
    },
    "ired": {
        "source": "IRED Indian Rainfall Erosivity Dataset (Raj et al. 2022)",
        "page": "https://doi.org/10.5281/zenodo.6469693",
        "files": {
            "IRED.zip": ("https://zenodo.org/api/records/6505510/files/"
                         "Indian%20Rainfall%20Erosivity%20Dataset%20(IRED).zip/content"),
        },
        "notes": ("Annual R, MJ mm ha-1 h-1 yr-1, from hourly IMDAA 1979-2018, 0.12 deg, "
                  "GeoTIFF + NetCDF, plus FI and MFI. Guwahati: 4,258 vs gauge 7,924 (-46%). "
                  "Concept DOI 6469693 resolves to record 6505510."),
    },
}


def main() -> None:
    print("Rainfall erosivity (R factor) — InRESatE and IRED")
    for key, s in SETS.items():
        folder = OUT / key
        written = []
        for name, url in s["files"].items():
            dest = download(url, folder / name, timeout=600)
            written.append(dest)
            if dest.suffix == ".zip":
                # A Zenodo "page not found" arrives as HTML with a 200, so check
                # the archive is one before trusting it (bit us 2026-10-17).
                if not zipfile.is_zipfile(dest):
                    raise SystemExit(f"  {dest.name} is not a zip archive — check the URL: {url}")
                with zipfile.ZipFile(dest) as z:
                    z.extractall(folder)
                print(f"  [unzip] {dest.name} -> {folder.relative_to(OUT.parent)}")
        record(OUT, source=s["source"], url=s["page"], files=written,
               license_="CC-BY 4.0", notes=s["notes"])


if __name__ == "__main__":
    main()
