"""The lines drawn on each river gauge's graph.

    python scripts/build/build_gauge_levels.py

Reads   models/flood_when_gauge/stations.json         (the model's threshold and
                                                        ordinary level per gauge)
        data/raw/11_gauges/cwc/<code>_static.json     (CWC's published warning,
                                                        danger and highest levels)
Writes  webapp/assets/flood/gauge_levels.json

Every line is either published by the Central Water Commission or is the
exact line our chance refers to — nothing is drawn that neither source
states. For the official-danger gauges the two are the same line. For the
others the chance is for the river's own wettest 2% of days; CWC's lines
are still drawn where CWC publishes them (for several of these the
official danger level has never been reached in the record, which is why
the model uses the river's own high-water mark instead). NWDP gauges
publish flow, not level, and have no official lines.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import ROOT

CWC_RAW = ROOT / "data" / "raw" / "11_gauges" / "cwc"


def main() -> None:
    st = json.loads((ROOT / "models" / "flood_when_gauge" / "stations.json").read_text())
    out = {}
    for code, s in st.items():
        cwc = s["network"] == "CWC"
        g = {"name": s["name"], "network": s["network"],
             "unit": "m" if cwc else "m³/s",
             "quantity": "river level" if cwc else "river flow",
             "model_line": s["threshold"], "model_line_is_official_danger": bool(s["official"]),
             "model_line_means": s["means"], "typical": s["base"],
             "warning": None, "danger": None, "highest": None, "highest_date": None}
        f = CWC_RAW / f"{code}_static.json"
        if cwc and f.exists():
            d = json.loads(f.read_text())
            g.update(warning=d.get("warningLevel"), danger=d.get("dangerLevel"),
                     highest=d.get("highestFlowLevel"), highest_date=d.get("highestFlowLevelDate"))
        out[code] = g
    dst = ROOT / "webapp" / "assets" / "flood" / "gauge_levels.json"
    dst.write_text(json.dumps(out, indent=2))
    n_off = sum(1 for g in out.values() if g["danger"] is not None)
    print(f"  {len(out)} gauges; {n_off} with CWC's published lines -> {dst}")


if __name__ == "__main__":
    main()
