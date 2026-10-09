"""PX2 — GSI's statewiseLandslideReport archive as a 6th route to dated events.

Unlike PX0/PX0B/PX0C (all remote-sensing routes, all closed — see
docs/design/TEMPORAL_INVENTORY_ATTEMPTS.md), this is GSI's own written field
investigation reports: bhusanket.gsi.gov.in/statewiseLandslideReport.html.
The report bibliography is a plain static JSON, no auth; each report's PDF
downloads directly, no login (found 2026-08-20, re-checking a page believed
already investigated — see memory `gsi-report-archive-open`).

Three-stage pipeline, each stage resumable and safe to re-run:
  1. fetch_catalog()   -> data/interim/gsi_reports/national_catalog.json
       Pull the full national report bibliography (1,179 records, all states).
  2. scan(targets)     -> data/interim/gsi_reports/scan_results.json
       For Arunachal (every project type) + the rest of the Himalayan/NE arc
       (Post Disaster Studies only — the highest-yield category), download
       each PDF, extract text (PyMuPDF), and flag whether it names a real
       date (structured "Date of Initiation" field, a numeric dd.mm.yyyy,
       a spelled-out date like "15th June, 1989", or a "History of event"
       marker). This is NOT an exact event count — some reports bundle
       several events, most hold one; see the calibration note below.
  3. read the flagged reports by hand (or with a PDF-reading model) to turn
       "has a date signal" into an actual extracted, structured event.
       Not automated here — genuinely needs a human/LLM read per report.

Calibration point (2026-08-20, read directly, not inferred): the automated
"Date of Initiation" count exactly matched manual reading on one report
(`PDLS_2024_50185.pdf`, Arunachal — 4/4). Narrative pre-2016 reports need the
broader spelled-out-date regex to catch dates at all (structured field is a
post-~2016 convention); several were spot-verified against direct reading too
(Bomdila 1973, Jamiri/Munna Camp 1989, Minutang 1948, Bhalukpong 2016).

Results as of 2026-08-20 (243/255 reports successfully downloaded+scanned,
12 stuck behind a >60MB size cap or a 403):

    Arunachal Pradesh — event-relevant categories only (Post Disaster +
    Site Specific Studies, i.e. excluding pure susceptibility-mapping
    reports): 27 reports, 25 downloaded, 20 show a real date signal.
    Estimated new individual events: ~25-40 (some reports bundle 2-4).
    New Arunachal total: ~100-110 dated events (was 72, NASA GLC only).

    Himalayan/NE region, Post Disaster Studies only, 11 states: 215 reports,
    209 downloaded, 156 show a real date signal. Estimated new individual
    events, pooled region-wide: ~200-280.

Verdict: Arunachal alone is still short of what a trustworthy ML trigger
model needs (same conclusion as at 72 events — see
memory `only-90-dated-landslide-events-exist`). The pooled Himalayan number
is a different regime — enough to seriously attempt a properly
cross-validated tree-based model (not deep learning; see
memory `why-trees-not-deep-learning`), trained on the pool and fine-tuned to
Arunachal. This is what makes [[himalayan-pooling-is-the-live-ml-route]] a
live route again, now with day-precision reports instead of season-tagged
Bhuvan polygons.

Next step, not yet done: read the ~176 flagged reports (20 Arunachal + 156
regional) one at a time and extract each into a proper structured event
table. `data/interim/gsi_reports/scan_results.json` is the exact queue —
filter on `has_date_signal: true`.

Full writeup: docs/data_research/DATA_VERIFICATION.md §D,
docs/design/TEMPORAL_INVENTORY_ATTEMPTS.md.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # pymupdf

BASE = "https://bhusanket.gsi.gov.in"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "interim", "gsi_reports")
PDF_CACHE_DIR = os.path.join(DATA_DIR, "pdfs")  # not checked in; re-download on demand

HIMALAYAN_PDS_STATES = {
    "Sikkim", "Himachal Pradesh", " Himachal Pradesh", "Uttarakhand",
    "UT_Jammu & Kashmir", "UT: Jammu & Kashmir", " UT: Jammu & Kashmir",
    "UT_Ladakh", "Nagaland", "Manipur", "Mizoram", "Meghalaya", "Assam",
}

MONTHS = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
          r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")
SPELLED_DATE_RE = re.compile(
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?(?:\s*(?:and|,|to|-)\s*\d{{1,2}}(?:st|nd|rd|th)?)?\s+{MONTHS}[,]?\s+\d{{4}}\b",
    re.I,
)
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
DATE_INIT_RE = re.compile(r"Date of [Ii]nitiation[^\n]{0,60}", re.I)
SLIDE_NO_RE = re.compile(r"\bSlide No\.?\s*[:.]?\s*[A-Z0-9/]", re.I)
HISTORY_EVENT_RE = re.compile(r"(History of (the )?event|occurred on|triggered on|took place on)", re.I)


def fetch_catalog(save: bool = True) -> list[dict]:
    """Pull the full national report bibliography. The endpoint serves a JS
    array literal (`LandslideReport = [...]`), not pure JSON — strip the
    assignment before parsing. Node's `new Function` trick was used
    originally because it tolerates the odd inline comment; here we just
    need the assignment stripped, standard json.loads is fine."""
    url = f"{BASE}/json/LandslideReport/LandslideReport.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8", errors="replace")
    code = re.sub(r"^LandslideReport\s*=\s*", "", raw).rstrip().rstrip(";")
    catalog = json.loads(code)
    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "national_catalog.json"), "w", encoding="utf-8") as f:
            json.dump(catalog, f)
    return catalog


def select_targets(catalog: list[dict]) -> list[dict]:
    """Arunachal: every project type. Rest of the Himalayan/NE arc: Post
    Disaster Studies only (highest yield, keeps the scope tractable)."""
    out = []
    for rec in catalog:
        state = rec.get("State")
        if state == "Arunachal Pradesh":
            out.append(rec)
        elif state in HIMALAYAN_PDS_STATES and rec.get("Type of project") == "Post Disaster Studies":
            out.append(rec)
    return out


def _pdf_url(state: str, ptype: str, acc) -> str:
    return (f"{BASE}/Output/LandslideReport/{urllib.parse.quote(state)}/"
            f"{urllib.parse.quote(ptype)}/{urllib.parse.quote(str(acc))}.pdf")


def _safe_name(*parts) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", "_".join(str(p) for p in parts))[:120]


def _download(url: str, dest: str, timeout: int = 180, retries: int = 2) -> int:
    last_exc = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            with open(dest, "wb") as f:
                f.write(data)
            return len(data)
        except Exception as e:  # noqa: BLE001
            last_exc = e
            time.sleep(2)
    raise last_exc


def _analyze_pdf(path: str) -> dict:
    doc = fitz.open(path)
    text = "\n".join(p.get_text() for p in doc)
    flat = text.replace("\n", " ")
    n_date_init = len(DATE_INIT_RE.findall(text))
    n_slide_no = len(SLIDE_NO_RE.findall(text))
    n_numeric = len(set(NUMERIC_DATE_RE.findall(text)))
    n_spelled = len(SPELLED_DATE_RE.findall(flat))
    n_history = len(HISTORY_EVENT_RE.findall(text))
    return {
        "n_pages": len(doc), "text_chars": len(text),
        "n_date_of_initiation": n_date_init, "n_slide_no": n_slide_no,
        "n_numeric_dates": n_numeric, "n_spelled_dates": n_spelled,
        "n_history_event_markers": n_history,
        "has_date_signal": n_date_init > 0 or n_numeric > 0 or n_spelled > 0 or n_history > 0,
    }


def scan_one(rec: dict, max_bytes: int = 60_000_000) -> dict:
    state, ptype, acc = rec["State"], rec["Type of project"], rec["Acc. No."]
    row = {"state": state, "type": ptype, "acc": acc, "field_season": rec.get("Field Season"),
           "title": rec.get("Title of the project"), "downloaded": False}
    url = _pdf_url(state, ptype, acc)
    dest = os.path.join(PDF_CACHE_DIR, _safe_name(state, ptype, acc) + ".pdf")
    try:
        os.makedirs(PDF_CACHE_DIR, exist_ok=True)
        if not (os.path.exists(dest) and os.path.getsize(dest) > 1000):
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                status, size = r.status, int(r.headers.get("Content-Length") or 0)
            if status != 200:
                row["skip_reason"] = f"HEAD status {status}"
                return row
            if size > max_bytes:
                row["skip_reason"] = f"too large for this pass (>{max_bytes//1_000_000}MB)"
                return row
            _download(url, dest)
        row.update(_analyze_pdf(dest))
        row["downloaded"] = True
    except Exception as e:  # noqa: BLE001
        row["error"] = str(e)
    return row


def scan(targets: list[dict], workers: int = 8, save: bool = True) -> list[dict]:
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(scan_one, rec): rec for rec in targets}
        for i, fut in enumerate(as_completed(futures)):
            row = fut.result()
            results.append(row)
            print(f"[{i+1}/{len(targets)}] {row['state']}|{row['type']}|{row['acc']} -> "
                  f"{row.get('skip_reason') or row.get('error') or ('date_signal=' + str(row.get('has_date_signal')))}")
    if save:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "scan_results.json"), "w", encoding="utf-8") as f:
            json.dump(results, f, indent=1)
    return results


def summarize(results: list[dict]) -> dict:
    from collections import defaultdict
    by_state = defaultdict(lambda: {"n": 0, "downloaded": 0, "with_date_signal": 0})
    for r in results:
        s = by_state[r["state"]]
        s["n"] += 1
        if r.get("downloaded"):
            s["downloaded"] += 1
            if r.get("has_date_signal"):
                s["with_date_signal"] += 1
    return dict(by_state)


if __name__ == "__main__":
    cat = fetch_catalog()
    tgts = select_targets(cat)
    print(f"{len(tgts)} target reports (Arunachal, all types + rest of Himalayan arc, Post Disaster only)")
    res = scan(tgts)
    print(json.dumps(summarize(res), indent=1))
