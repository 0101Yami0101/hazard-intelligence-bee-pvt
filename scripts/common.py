"""Shared paths, AOI definition, and fetch helpers.

Every fetch script imports from here so the area of interest and the
naming convention are defined in exactly one place.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# Credentials — loaded from .env, never hard-coded
# --------------------------------------------------------------------------
def _load_env() -> dict[str, str]:
    """Minimal .env reader. Avoids a dependency; ignores blanks and comments."""
    env: dict[str, str] = {}
    f = ROOT / ".env"
    if not f.exists():
        return env
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ENV = _load_env()


def credential(name: str, required: bool = True) -> str:
    """Fetch a credential from .env, falling back to the process environment."""
    import os
    val = ENV.get(name) or os.environ.get(name, "")
    if required and not val:
        raise RuntimeError(
            f"Missing credential {name!r}.\n"
            f"  Copy .env.example to .env and fill it in.\n"
            f"  Nothing in .env is committed — see .gitignore."
        )
    return val


def have(*names: str) -> bool:
    """True if every named credential is present. For pre-flight checks."""
    return all(credential(n, required=False) for n in names)


def ecmwf_key(store: str = "cds") -> tuple[str, str]:
    """(url, key) for an ECMWF data store.

    One Personal Access Token covers CDS, EWDS and ADS, so EWDS_KEY is
    optional and falls back to CDSAPI_KEY. The URLs are not interchangeable:
    GloFAS lives only on EWDS, ERA5 only on CDS.
    """
    if store.lower() == "ewds":
        url = credential("EWDS_URL", required=False) or "https://ewds.climate.copernicus.eu/api"
        key = credential("EWDS_KEY", required=False) or credential("CDSAPI_KEY")
    else:
        url = credential("CDSAPI_URL", required=False) or "https://cds.climate.copernicus.eu/api"
        key = credential("CDSAPI_KEY")
    return url, key


# --------------------------------------------------------------------------
# Region — which state this run is for
# --------------------------------------------------------------------------
# Picked by the REGION environment variable, default "arunachal". An env var
# rather than a flag because every script reads these names at import time,
# before its own argument parsing runs:
#
#     $env:REGION = "assam"; python scripts/fetch/fetch_03_soil.py
#
# The "arunachal" entry is exactly the constants this file held before regions
# existed, and Arunachal keeps its old folders. The live 08:30 flood run does
# not set REGION, so it sees no change — proven by
# scripts/model/check_live_unchanged.py, not assumed. Other regions get
# region-scoped interim/processed folders; raw folders are shared, because
# every bbox-clipped raw file already carries AOI_NAME in its name.
# (docs/design/EROSION_MODULE.md §4.1; EROSION_PLAN.md decision D1 (a))
#
# bbox is (west, south, east, north) in EPSG:4326 and must cover the region's
# whole grid box (scripts/build/grid.py), not just the state, so terrain
# reaches the box edge. Tile ranges are the integer degrees that bbox touches.
DEFAULT_REGION = "arunachal"
REGIONS: dict[str, dict] = {
    "arunachal": {"state": "Arunachal Pradesh",
                  "bbox": (91.4, 26.5, 97.5, 29.6),
                  "lon_tiles": range(91, 98),     # 91E .. 97E
                  "lat_tiles": range(26, 30)},    # 26N .. 29N
    # Grid box spans 89.54-96.15E, 24.02-28.12N (measured 2026-10-17)
    "assam": {"state": "Assam",
              "bbox": (89.5, 24.0, 96.2, 28.2),
              "lon_tiles": range(89, 97),         # 89E .. 96E
              "lat_tiles": range(24, 29),         # 24N .. 28N
              # Survey of India, OVSF/1M/9 (2026-10-20): 35 current districts with LGD
              # codes, replacing GADM's 27 outdated ones (EROSION_PLAN.md V-12)
              "boundary": "soi"},
}


def _pick_region() -> str:
    import os
    name = os.environ.get("REGION", "").strip().lower() or DEFAULT_REGION
    if name not in REGIONS:
        raise SystemExit(f"Unknown REGION {name!r}; known: {', '.join(REGIONS)}")
    return name


REGION = _pick_region()

DATA = ROOT / "data"
RAW = DATA / "raw"
_SCOPE = () if REGION == DEFAULT_REGION else (REGION,)
INTERIM = DATA.joinpath("interim", *_SCOPE)
PROCESSED = DATA.joinpath("processed", *_SCOPE)
LOGS = ROOT / "logs"

BOUNDARIES = RAW / "01_boundaries"
TERRAIN = RAW / "02_terrain"
SOIL_GEOLOGY = RAW / "03_soil_geology"
LANDCOVER = RAW / "04_landcover"
HYDROLOGY = RAW / "05_hydrology"
WEATHER = RAW / "06_weather"
SEISMIC = RAW / "07_seismic"
LABELS = RAW / "08_labels"
EXPOSURE = RAW / "09_exposure"
CONTEXT = RAW / "10_context"


def outline(kind: str) -> Path:
    """The selected region's outline file: kind "state" or "district".

    Arunachal stays on GADM 4.1 (unchanged); Assam uses the Survey of India
    outline (scripts/fetch/fetch_01b_soi_boundaries.py). Both files carry the
    district name in NAME_2, so readers need not know which one they got.
    """
    src = REGIONS[REGION].get("boundary", "gadm")
    return BOUNDARIES / f"{src}_{kind}-boundary_vector_{AOI_NAME}.gpkg"
GAUGES = RAW / "11_gauges"

# --------------------------------------------------------------------------
# Area of interest — the selected region, with a small buffer
# --------------------------------------------------------------------------
AOI_NAME = REGION
AOI_STATE = REGIONS[REGION]["state"]       # the state's name as GADM spells it
# (west, south, east, north) in EPSG:4326
AOI_BBOX = REGIONS[REGION]["bbox"]

# Integer tile ranges covering the AOI, for tile-indexed datasets
AOI_LON_TILES = REGIONS[REGION]["lon_tiles"]
AOI_LAT_TILES = REGIONS[REGION]["lat_tiles"]


def bbox_str(sep: str = ",") -> str:
    return sep.join(str(v) for v in AOI_BBOX)


# --------------------------------------------------------------------------
# Fetch helpers
# --------------------------------------------------------------------------
UA = {"User-Agent": "LandSlideFlood-research/1.0 (data verification)"}


def http_get(url: str, params: dict | None = None, timeout: int = 120,
             retries: int = 3, **kwargs) -> requests.Response:
    """GET with retry and backoff. Raises on final failure."""
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout,
                             headers={**UA, **kwargs.pop("headers", {})}, **kwargs)
            r.raise_for_status()
            return r
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"GET failed after {retries} tries: {url}\n  {last}")


def download(url: str, dest: Path, timeout: int = 300,
             overwrite: bool = False, headers: dict | None = None) -> Path:
    """Stream a URL to disk. Skips if the file already exists."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not overwrite:
        print(f"  [skip] {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=timeout,
                      headers={**UA, **(headers or {})}) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    tmp.replace(dest)
    print(f"  [ok]   {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def head_size(url: str, timeout: int = 60) -> int | None:
    """Content-Length without downloading. None if the server won't say."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=UA)
        if r.ok and "Content-Length" in r.headers:
            return int(r.headers["Content-Length"])
    except Exception:  # noqa: BLE001
        pass
    return None


class EarthdataSession(requests.Session):
    """Session that survives the Earthdata URS redirect.

    Data hosts (GES DISC, NSIDC) bounce an unauthenticated request to
    urs.earthdata.nasa.gov and back. `requests` strips the Authorization
    header on any cross-host redirect, so basic auth alone yields 401. This
    keeps the header for the URS hop only, which is NASA's documented
    workaround, and lets the returned cookie carry the rest.
    """

    AUTH_HOST = "urs.earthdata.nasa.gov"

    def __init__(self, username: str | None = None, password: str | None = None):
        super().__init__()
        self.auth = (username or credential("EARTHDATA_USERNAME"),
                     password or credential("EARTHDATA_PASSWORD"))
        self.headers.update(UA)

    def rebuild_auth(self, prepared_request, response):  # noqa: D102
        headers = prepared_request.headers
        if "Authorization" not in headers:
            return
        orig = requests.utils.urlparse(response.request.url).hostname
        dest = requests.utils.urlparse(prepared_request.url).hostname
        if orig != dest and dest != self.AUTH_HOST and orig != self.AUTH_HOST:
            del headers["Authorization"]


def sha256(path: Path, limit: int = 1 << 24) -> str:
    """Hash of the first `limit` bytes — enough to detect a changed file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read(limit))
    return h.hexdigest()[:16]


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------
def record(folder: Path, source: str, url: str, files: list[Path],
           license_: str = "", notes: str = "") -> None:
    """Append a provenance entry to the folder's _SOURCES.json.

    One entry per (source, region). Raw folders are shared between regions,
    so without the region an Assam re-fetch of "SoilGrids" would silently
    replace Arunachal's entry. Entries with no "region" key are the default
    region's — every entry written before regions existed — and default-region
    entries are still written without the key, so their format is unchanged.
    """
    folder.mkdir(parents=True, exist_ok=True)
    manifest = folder / "_SOURCES.json"
    entries = json.loads(manifest.read_text()) if manifest.exists() else []
    entries = [e for e in entries
               if not (e.get("source") == source
                       and e.get("region", DEFAULT_REGION) == REGION)]
    entries.append({
        "source": source,
        **({} if REGION == DEFAULT_REGION else {"region": REGION}),
        "url": url,
        "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "license": license_,
        "notes": notes,
        "files": [
            {"name": f.name,
             "bytes": f.stat().st_size if f.exists() else 0,
             "sha256_head": sha256(f) if f.exists() else ""}
            for f in files
        ],
    })
    manifest.write_text(json.dumps(entries, indent=2))
    print(f"  [prov] recorded {source} -> {manifest.relative_to(ROOT)}")
