"""National erosion reference maps (IIT Delhi) — for COMPARISON only.

The soil-erosion module's sanity checks (docs/design/EROSION_PLAN.md, E0.7):
  ISED  Indian Soil Erodibility Dataset (Raj et al. 2023), K factor. CC-BY 4.0.
        Zenodo 6505314, ~2.0 GB.                       -> S3: our K vs theirs
  IWED  Indian Water Erosion Dataset (Raj, Saharia & Chakma), national RUSLE at
        250 m. Zenodo 7823909, ~2.3 GB. NO LICENCE STATED -> compare only, never
        redistribute, never show as a layer (EROSION_PLAN.md R4).   -> S8

National files, so run without REGION. Archives are kept as downloaded and
unpacked beside them. Large and on a sometimes flaky line, so downloads resume
from the partial file (see resumable()). Zenodo redirects ISED's record 6505314
to its newest version, 8011445 (same 1.97 GB file).
"""
import sys
import time
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import SOIL_GEOLOGY, UA, WEATHER, http_get, record

SETS = {
    "ised": {"record": "6505314", "folder": SOIL_GEOLOGY / "ised",
             "source": "ISED Indian Soil Erodibility Dataset (Raj et al. 2023)",
             "license": "CC-BY 4.0",
             "notes": "National K factor. Used only to compare our Williams (1995) K (E0.7, S3)."},
    "iwed": {"record": "7823909", "folder": WEATHER / "erosivity" / "iwed",
             "source": "IWED Indian Water Erosion Dataset (Raj, Saharia & Chakma)",
             "license": "NONE STATED on Zenodo — compare only, do not redistribute or display",
             "notes": "National RUSLE potential soil loss, 250 m, on IRED rain and NRSC land use, "
                      "P < 1 on cropland. Used only for check S8 (EROSION_PLAN.md R4)."},
}


def resumable(url: str, dest: Path, size: int, tries: int = 150) -> Path:
    """Download with resume. Large files on this line stall mid-stream (ISED sat
    at 245 MB for 30 min on 2026-10-17, waiting on a dead connection), and
    common.download() restarts from zero. This keeps the .part file, asks the
    server for the rest with an HTTP Range header (Zenodo answers 206), and gives
    up on a silent connection after 60 s so the next try can pick up."""
    if dest.exists() and dest.stat().st_size == size:
        print(f"  [skip] {dest.name} ({size / 1e9:.2f} GB)")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, tries + 1):
        have = part.stat().st_size if part.exists() else 0
        if have >= size:
            break
        try:
            with requests.get(url, stream=True, timeout=(30, 60), allow_redirects=True,
                              headers={**UA, "Range": f"bytes={have}-"}) as r:
                if r.status_code == 200 and have:      # server ignored the Range: start over
                    have = 0
                    part.unlink()
                r.raise_for_status()
                with open(part, "ab") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
        except Exception as exc:  # noqa: BLE001
            now = part.stat().st_size if part.exists() else 0
            print(f"  [retry {attempt}] at {now / 1e6:,.0f} / {size / 1e6:,.0f} MB: {type(exc).__name__}",
                  flush=True)
            time.sleep(min(60, 5 * attempt))
    if not part.exists() or part.stat().st_size != size:
        raise SystemExit(f"  gave up on {dest.name}")
    part.replace(dest)
    print(f"  [ok]   {dest.name} ({size / 1e9:.2f} GB)")
    return dest


def main(which: list[str]) -> None:
    for key in which:
        s = SETS[key]
        meta = http_get(f"https://zenodo.org/api/records/{s['record']}", timeout=60).json()
        print(f"  {key}: Zenodo record {s['record']} -> version {meta.get('id')}")
        written = []
        for f in meta["files"]:
            url = f["links"].get("content") or f["links"]["self"]
            dest = s["folder"] / f["key"].replace(" ", "_")
            print(f"  {key}: {f['key']} ({f['size'] / 1e9:.2f} GB)")
            got = resumable(url, dest, f["size"])
            written.append(got)
            if got.suffix == ".zip":
                if not zipfile.is_zipfile(got):
                    raise SystemExit(f"  {got.name} is not a zip archive")
                with zipfile.ZipFile(got) as z:
                    z.extractall(s["folder"])
                print(f"  [unzip] {got.name}")
        record(s["folder"], source=s["source"], url=f"https://doi.org/10.5281/zenodo.{s['record']}",
               files=written, license_=s["license"], notes=s["notes"])


if __name__ == "__main__":
    main(sys.argv[1:] or list(SETS))
