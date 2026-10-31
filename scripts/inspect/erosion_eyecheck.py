"""AD-05: the blind picture check — judges the formula, the AI and gully-prone ground on one sample.

    $env:REGION = "assam"; python scripts/inspect/erosion_eyecheck.py            # make the pictures
    $env:REGION = "assam"; python scripts/inspect/erosion_eyecheck.py --score labels.csv

Written down before any picture existed (EROSION_PLAN.md, "AD-05 and AD-30 part 1"):
    stratum F  40 scored squares per formula class (6 classes)
    stratum G  30 gully-prone squares + 30 open, >= 5 deg, not-flagged squares
    labels     gully / erosion / none / cant_tell ("yes" = gully or erosion)
    P-F        formula: yes share severe+very severe >= 2x slight+moderate
    P-AI       AI: yes share in its top 10% band >= 2x its lower half (stratum F)
    P-G        gully-prone yes share >= 2x control (stratum G)
    P-cmp      AUC formula vs AI on stratum F (reported; "AI better" only if >= 0.05 higher)

Pictures: Esri World Imagery (the app's base map), 500 m window, square outlined,
neutral ids; the key is a separate file opened only after labelling.

Output: data/interim/<region>/erosion/eyecheck_ad05/ (pictures, sheets, _key.csv),
        reports/erosion_eyecheck_<region>.json (after --score)
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

import grid as G
from common import AOI_NAME, INTERIM, ROOT

warnings.filterwarnings("ignore")

E = INTERIM / "erosion"
OUT = E / "eyecheck_ad05"
SEED, PER_CLASS, PER_G = 7, 40, 30
EDGES = [5, 10, 20, 40, 80]
HALF_M = 250
REPORT = ROOT / "reports" / f"erosion_eyecheck_{AOI_NAME}.json"


def rd(p):
    with rasterio.open(p) as s:
        return s.read(1)


def sample() -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    ok = rd(E / "erosion_assessed.tif").astype(bool)
    A = rd(E / "erosion_A_tpha.tif")
    ai = rd(E / "erosion_ai_score.tif")
    gp = rd(E / "erosion_gully_prone.tif")
    slope = rd(INTERIM / "terrain" / "terrain_slope_deg.tif")
    cls = np.digitize(A, EDGES) + 1
    ai_p90 = float(np.nanpercentile(ai[ok], 90))
    ai_p50 = float(np.nanpercentile(ai[ok], 50))
    rows = []
    for c in range(1, 7):
        cells = np.flatnonzero((ok & (cls == c) & np.isfinite(ai)).ravel())
        for i in rng.choice(cells, PER_CLASS, replace=False):
            rows.append(("F", int(i)))
    for flag, n in ((1, PER_G), (0, PER_G)):
        sel = (gp == flag) if flag == 1 else ((gp == 0) & (slope >= 5))
        cells = np.flatnonzero((sel & ok).ravel())
        for i in rng.choice(cells, n, replace=False):
            rows.append(("G1" if flag else "G0", int(i)))
    df = pd.DataFrame(rows, columns=["stratum", "cell"])
    df["A"] = A.ravel()[df.cell]
    df["formula_class"] = cls.ravel()[df.cell]
    df["ai"] = ai.ravel()[df.cell]
    df["ai_band"] = np.select([df.ai >= ai_p90, df.ai < ai_p50], ["top10", "lower_half"], "middle")
    df["gully_prone"] = gp.ravel()[df.cell]
    df["row"], df["col"] = np.unravel_index(df.cell.to_numpy(), G.SHAPE)
    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


def pictures() -> None:
    import requests
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from PIL import Image
    from erosion_priority import ESRI
    from common import UA
    OUT.mkdir(parents=True, exist_ok=True)
    df = sample()
    df.insert(0, "id", np.arange(1, len(df) + 1))
    df.to_csv(OUT / "_key.csv", index=False)
    to_ll = Transformer.from_crs(G.CRS, 4326, always_xy=True)
    for _, r in df.iterrows():
        f = OUT / f"pic_{int(r.id):03d}.jpg"
        if f.exists():
            continue
        x, y = G.centre_xy(r.row, r.col)
        (w, s_), (e, n) = to_ll.transform(x - HALF_M, y - HALF_M), to_ll.transform(x + HALF_M, y + HALF_M)
        img = requests.get(ESRI, params=dict(bbox=f"{w},{s_},{e},{n}", bboxSR=4326, imageSR=4326, size="400,400",
                                             format="jpg", f="image"), headers=UA, timeout=120)
        img.raise_for_status()
        f.write_bytes(img.content)
    # contact sheets of 12, with the 100 m square outlined (the window is 500 m: the square is the middle fifth)
    ids = df.id.tolist()
    for k in range(0, len(ids), 12):
        fig, axes = plt.subplots(3, 4, figsize=(16, 12.6))
        for ax, i in zip(axes.ravel(), ids[k:k + 12]):
            ax.imshow(Image.open(OUT / f"pic_{i:03d}.jpg"))
            ax.add_patch(Rectangle((160, 160), 80, 80, fill=False, ec="yellow", lw=1.6))
            ax.set_title(f"picture {i:03d}", fontsize=11)
            ax.set_xticks([]); ax.set_yticks([])
        for ax in axes.ravel()[len(ids[k:k + 12]):]:
            ax.axis("off")
        fig.tight_layout()
        fig.savefig(OUT / f"_sheet_{k // 12 + 1:02d}.png", dpi=70)
        plt.close(fig)
    pd.DataFrame({"id": ids, "label": ""}).to_csv(OUT / "labels_blank.csv", index=False)
    print(f"  {len(ids)} pictures, {(len(ids) + 11) // 12} sheets in {OUT}; key in _key.csv (do not open)")


def score(labels_csv: str) -> None:
    from scipy.stats import rankdata
    key = pd.read_csv(OUT / "_key.csv").merge(pd.read_csv(labels_csv), on="id")
    key["yes"] = key.label.isin(["gully", "erosion"])
    key["readable"] = key.label != "cant_tell"

    def share(sel):
        s = key[sel]
        rd_ = s[s.readable]
        return {"n": int(len(s)), "readable": int(len(rd_)), "yes": int(s.yes.sum()),
                "share_readable": round(float(rd_.yes.mean()), 3) if len(rd_) else None,
                "share_strict": round(float(s.yes.mean()), 3) if len(s) else None}

    F = key.stratum == "F"
    hi, lo = share(F & key.formula_class.isin([5, 6])), share(F & key.formula_class.isin([1, 2]))
    top, low = share(F & (key.ai_band == "top10")), share(F & (key.ai_band == "lower_half"))
    g1, g0 = share(key.stratum == "G1"), share(key.stratum == "G0")
    ratio = lambda a, b: (round(a["share_readable"] / b["share_readable"], 2)
                          if a["share_readable"] is not None and b["share_readable"] else None)

    def auc(score_, y):
        r = rankdata(score_)
        n1, n0 = int(y.sum()), int((~y).sum())
        return round(float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)), 3) if n1 and n0 else None
    R = key[F & key.readable]
    res = {"P-F": {"high": hi, "low": lo, "ratio": ratio(hi, lo)},
           "P-AI": {"top10": top, "lower_half": low, "ratio": ratio(top, low)},
           "P-G": {"gully_prone": g1, "control": g0, "ratio": ratio(g1, g0)},
           "P-cmp": {"auc_formula": auc(R.A.to_numpy(), R.yes.to_numpy()), "auc_ai": auc(R.ai.to_numpy(), R.yes.to_numpy()),
                     "readable": int(len(R))},
           "per_class_share": {int(c): share(F & (key.formula_class == c))["share_readable"] for c in range(1, 7)},
           "labels": key.label.value_counts().to_dict()}
    for k in ("P-F", "P-AI", "P-G"):
        res[k]["pass"] = bool(res[k]["ratio"] is not None and res[k]["ratio"] >= 2.0)
    c = res["P-cmp"]
    c["ai_better"] = bool(c["auc_formula"] is not None and c["auc_ai"] is not None and c["auc_ai"] - c["auc_formula"] >= 0.05)
    REPORT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    if "--score" in sys.argv:
        score(sys.argv[sys.argv.index("--score") + 1])
    else:
        pictures()
