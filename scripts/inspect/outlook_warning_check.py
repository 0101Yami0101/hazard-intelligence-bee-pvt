"""AD-28: would a simple heavy-erosive-week warning have worked? Judged on E2.2's replay.

    $env:REGION = "assam"; python scripts/inspect/outlook_warning_check.py

Rule and bars written before measuring (EROSION_PLAN.md, "AD-28 part 1"):
    warn      forecast x-normal >= 2.0 AND forecast share of a normal year >= 2%
    heavy     observed x-normal >= 2.0 AND observed share >= 2% (IMERG)
    W1        hit rate (warned heavy / heavy) >= 0.50
    W2        false alarms (warned not heavy / warned) <= 0.50
    W3        Peirce skill (hit rate - false-alarm rate) > 0.20
Per point-week (125 points x 44 Mondays, May-Sep 2024-25).

Input: data/interim/<region>/outlook_replay/replay_point_weeks.npz (outlook_replay.py)
Output: reports/outlook_warning_check_<region>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from common import AOI_NAME, INTERIM, ROOT

X_CUT, SHARE_CUT = 2.0, 0.02
BARS = {"W1_hit_rate": 0.50, "W2_false_alarms": 0.50, "W3_peirce": 0.20}


def main() -> None:
    z = np.load(INTERIM / "outlook_replay" / "replay_point_weeks.npz")
    m = np.isfinite(z["x_fc"]) & np.isfinite(z["x_ob"]) & np.isfinite(z["s_fc"]) & np.isfinite(z["s_ob"])
    warn = (z["x_fc"] >= X_CUT) & (z["s_fc"] >= SHARE_CUT)
    heavy = (z["x_ob"] >= X_CUT) & (z["s_ob"] >= SHARE_CUT)
    w, h = warn[m], heavy[m]
    hits, misses, fa, cn = int((w & h).sum()), int((~w & h).sum()), int((w & ~h).sum()), int((~w & ~h).sum())
    pod = hits / max(hits + misses, 1)
    far = fa / max(hits + fa, 1)
    pofd = fa / max(fa + cn, 1)
    weeks_any = int((warn & m).any(axis=1).sum())
    rep = {"region": AOI_NAME, "rule": {"x_normal": X_CUT, "share_of_year": SHARE_CUT}, "bars": BARS,
           "point_weeks": int(m.sum()), "heavy": hits + misses, "warned": hits + fa,
           "hits": hits, "misses": misses, "false_alarms": fa, "correct_quiet": cn,
           "W1_hit_rate": round(pod, 3), "W2_false_alarms": round(far, 3), "W3_peirce": round(pod - pofd, 3),
           "weeks_with_any_warning": weeks_any, "weeks": int(len(z["issue"]))}
    rep["pass"] = bool(rep["W1_hit_rate"] >= BARS["W1_hit_rate"] and rep["W2_false_alarms"] <= BARS["W2_false_alarms"]
                       and rep["W3_peirce"] > BARS["W3_peirce"])
    (ROOT / "reports" / f"outlook_warning_check_{AOI_NAME}.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
