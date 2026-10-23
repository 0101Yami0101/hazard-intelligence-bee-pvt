"""Visual exit check for the erosion recipe — the five ingredients and the result.

    $env:REGION = "assam"; python scripts/build/check_erosion.py

Numbers can look fine while the picture is wrong. The hills (Karbi Anglong, Dima
Hasao, the Barak valley ridges in Assam) should stand out from the plains, and
"not assessed" (grey) should follow the rivers, not cover hillsides.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm

from common import AOI_STATE, INTERIM

S = INTERIM / "erosion"
STEP = 4


def rd(name):
    with rasterio.open(S / f"{name}.tif") as s:
        return s.read(1)[::STEP, ::STEP]


fig, axes = plt.subplots(3, 2, figsize=(16, 14))
panels = [("erosion_R", "R — rain erosivity (MJ mm/ha/h/yr)", "Blues", None),
          ("erosion_K", "K — soil erodibility (SI)", "YlOrBr", (0.012, 0.022)),
          ("erosion_LS", "LS — slope length x steepness (log)", "magma", "log"),
          ("erosion_C", "C — cover (land-cover lookup)", "Greens_r", (0, 0.45))]
for ax, (n, title, cmap, lim) in zip(axes.ravel()[:4], panels):
    a = rd(n)
    if lim == "log":
        im = ax.imshow(np.where(a > 0.01, a, np.nan), cmap=cmap, norm=LogNorm(0.05, 100))
    elif lim:
        im = ax.imshow(a, cmap=cmap, vmin=lim[0], vmax=lim[1])
    else:
        im = ax.imshow(a, cmap=cmap)
    ax.set_title(title); fig.colorbar(im, ax=ax, fraction=0.03)

ax = axes.ravel()[4]
cls = rd("erosion_class").astype(float)
inside = np.isfinite(rd("erosion_R"))
cls[(cls == 0) & ~inside] = np.nan
cmap = ListedColormap(["#bdbdbd", "#1a9850", "#a6d96a", "#fee08b", "#fdae61", "#f46d43", "#a50026"])
im = ax.imshow(cls, cmap=cmap, norm=BoundaryNorm(np.arange(-0.5, 7), 7), interpolation="nearest")
cb = fig.colorbar(im, ax=ax, fraction=0.03, ticks=range(7))
cb.ax.set_yticklabels(["not assessed", "slight <5", "moderate", "high", "very high", "severe", "very severe >80"])
ax.set_title("Class, main run (t/ha/yr)")

ax = axes.ravel()[5]
a = rd("erosion_A_tpha")
im = ax.imshow(np.where(a > 0, a, np.nan), cmap="inferno", norm=LogNorm(0.5, 300))
ax.set_title("A — soil loss, main run (t/ha/yr, log)"); fig.colorbar(im, ax=ax, fraction=0.03)

for ax in axes.ravel():
    ax.set_xticks([]); ax.set_yticks([])
fig.suptitle(f"Erosion recipe (RUSLE) — {AOI_STATE}, main run: InRESatE R, tree C 0.03, P = 1", fontsize=13)
fig.tight_layout()
out = S / "_check_erosion.png"
fig.savefig(out, dpi=90, bbox_inches="tight")
print(f"wrote {out}")
