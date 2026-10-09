"""WHERE trained on the reported record vs on the verified record — scored
fairly, on the same verified flood events, out of fold.

    python scripts/model/compare_where_verified.py

Both models use the same five spatial folds (the training table's `fold`
column), so each verified-event row is scored by a fold model that never saw
its block, and each model's own first-stage calibration is cross-fitted the
way training does it. Reported: ranking (AUC) pooled / inside Arunachal /
steep ground, and the calibration table inside Arunachal.
Writes  reports/flood_where_verified_compare.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import lightgbm as lgb
import numpy as np
import pandas as pd
import rasterio
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score

from check_where_topend import EDGES, ece, load_table, reliability
from common import INTERIM, PROCESSED, ROOT


def oof_cal(df, feats, model_dir: Path, train_mask: np.ndarray) -> np.ndarray:
    """Out-of-fold scores from the model's saved fold models, calibrated the
    way training does (each fold by a curve fitted on the other folds' rows
    THAT MODEL TRAINED ON)."""
    fold = df["fold"].to_numpy()
    y, w = df["label"].to_numpy(float), df["weight"].to_numpy(float)
    oof = np.full(len(df), np.nan)
    for f in sorted(np.unique(fold)):
        b = lgb.Booster(model_file=str(model_dir / f"fold{int(f)}.txt"))
        m = fold == f
        oof[m] = b.predict(df.loc[m, feats])
    cal = np.full(len(df), np.nan)
    for f in np.unique(fold):
        te = fold == f
        tr = (fold != f) & train_mask
        iso = IsotonicRegression(y_min=0, y_max=1, out_of_bounds="clip")
        cal[te] = iso.fit(oof[tr], y[tr], sample_weight=w[tr]).predict(oof[te])
    return cal


def main() -> None:
    df, feats = load_table()
    ver = set(pd.read_parquet(INTERIM / "flood_events" / "verified_events.parquet")["uuid"])
    ev = pd.read_parquet(PROCESSED / "flood_where_events.parquet")
    vev = set(ev.loc[ev["uuid"].isin(ver), "event"])
    is_v = df["event"].isin(vev).to_numpy()
    with rasterio.open(INTERIM / "state_mask.tif") as s:
        inst = s.read(1).astype(bool)
    ap = inst[df["row"].to_numpy(), df["col"].to_numpy()]
    steep = df["terrain_slope_deg"].to_numpy() >= 10.0
    y, w = df["label"].to_numpy(float), df["weight"].to_numpy(float)
    pos = y == 1
    out = {"what": "WHERE out-of-fold on the VERIFIED events' rows: trained on reported vs verified",
           "verified_events": int(len(vev)), "rows": int(is_v.sum())}
    for name, mdir, trained in (("trained on reported", ROOT / "models" / "flood_where",
                                 np.ones(len(df), bool)),
                                ("trained on verified", ROOT / "models" / "flood_where_verified", is_v)):
        cal = oof_cal(df, feats, mdir, trained)
        res = {}
        for area, m in (("pooled", is_v), ("Arunachal", is_v & ap), ("steep", is_v & steep)):
            res[area] = {"rows": int(m.sum()), "flooded": int(pos[m].sum()),
                         "auc": round(float(roc_auc_score(y[m], cal[m], sample_weight=w[m])), 4)}
        m = is_v & ap
        res["Arunachal_calibration"] = reliability(y[m], cal[m], w[m], pos[m])
        res["Arunachal_ece"] = round(ece(y[m], cal[m], w[m]), 5)
        out[name] = res
        print(f"  {name}: " + ", ".join(f"{a} AUC {res[a]['auc']}" for a in ("pooled", "Arunachal", "steep"))
              + f", Arunachal ECE {res['Arunachal_ece']}")
        for b in res["Arunachal_calibration"]:
            print(f"      {b['range']:>9} said {b['said_pct']:7.3f}% happened {b['happened_pct']:7.3f}%"
                  f"  flooded rows {b['flooded_rows']}")
    (ROOT / "reports" / "flood_where_verified_compare.json").write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
