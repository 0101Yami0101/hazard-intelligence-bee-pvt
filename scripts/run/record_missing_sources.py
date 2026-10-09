"""Write the missing provenance records for raw data fetched without one.

    python scripts/run/record_missing_sources.py

Every raw folder is meant to carry a `_SOURCES.json` — source, URL, licence,
fetch date, and a checksum per file (`common.record`). Four folders fetched
during the flood work in Aug–Sep 2026 never got one, because their fetch
scripts did not call `record()`:

    11_gauges/nwdp         NWDP small-river discharge (fetch_24)
    11_satellite           Sentinel-1 radar scenes (fetch_14 and 22–27)
    15_dfo_flood_records   DFO Global Flood Records (downloaded by hand)
    16_groundsource        Groundsource flood reports (downloaded by hand)

This writes them after the fact, from what is on disk and what the project's
own notes recorded at the time (docs/design/PARKED_HIMALAYAN_FLOOD_WHERE.md,
docs/data_research/DATA_VERIFICATION.md, the fetch scripts' docstrings). Two
things differ from a record written at fetch time, and each entry says so in
its notes:

  * `fetched_utc` is the newest file's modification time — when the last
    file landed on disk — not the time this script ran;
  * the checksum is taken now, so it proves the file has not changed SINCE
    today, not since it was downloaded.

Safe to run again: it replaces its own entries and leaves any other entry in
the same manifest alone.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import RAW, ROOT, sha256

TODAY = datetime.now(timezone.utc).date().isoformat()
AFTER = (f"Record written after the fact on {TODAY}: fetch date is the newest file's "
         "modification time; checksums taken then.")

# folder (under data/raw), file pattern, source, url, licence, notes
MISSING = [
    ("11_gauges/nwdp", "*.csv",
     "NWDP river discharge telemetry (NWIC / CWC)",
     "https://nwdp.nwic.gov.in/datastore/dump/<resource_id>",
     "other-open (NWDP: hydrological analysis, flood forecasting, water resource management)",
     "Two resources of the dataset river-discharge-telemetry-hourly-central-water-"
     "commission-cwc: 9c755c40 (2023 to Sept 2025) and 9a7feb81 (Jan 2026 on). "
     "14 Arunachal stations. scripts/fetch/fetch_24_nwdp_discharge.py."),
    ("11_satellite", "*.zip",
     "Sentinel-1 GRD radar scenes (Copernicus Data Space)",
     "https://catalogue.dataspace.copernicus.eu/odata/v1/Products",
     "Copernicus Sentinel data — free, full and open access",
     "IW GRDH scenes on and around flood dates, read by the radar water test behind "
     "the verified flood record. scripts/fetch/fetch_14_sentinel.py, fetch_22 to 27."),
    ("15_dfo_flood_records", "*",
     "DFO Global Flood Records",
     "https://doi.org/10.5281/zenodo.19288170",
     "CC0",
     "5,503 dated large flood events worldwide. Downloaded by hand from Zenodo "
     "(the Dartmouth Flood Observatory's own archive returns HTTP 410)."),
    ("16_groundsource", "*.parquet",
     "Groundsource flood reports (Google)",
     "https://zenodo.org/records/18647054",
     "CC-BY-4.0",
     "News-derived, dated, located flood reports. Downloaded by hand from Zenodo."),
]


def main() -> None:
    for folder, pat, source, url, lic, notes in MISSING:
        d = RAW / folder
        files = sorted(f for f in d.glob(pat) if f.is_file() and f.name != "_SOURCES.json")
        if not files:
            print(f"  [skip] {folder}: nothing on disk")
            continue
        newest = max(f.stat().st_mtime for f in files)
        manifest = d / "_SOURCES.json"
        entries = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
        entries = [e for e in entries if e.get("source") != source]
        entries.append({
            "source": source, "url": url,
            "fetched_utc": datetime.fromtimestamp(newest, timezone.utc).isoformat(
                timespec="seconds"),
            "license": lic, "notes": f"{notes} {AFTER}",
            "files": [{"name": f.name, "bytes": f.stat().st_size, "sha256_head": sha256(f)}
                      for f in files],
        })
        manifest.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        print(f"  [prov] {source}: {len(files)} files, "
              f"{sum(f.stat().st_size for f in files)/1e9:.2f} GB -> "
              f"{manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
