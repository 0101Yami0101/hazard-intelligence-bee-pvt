"""Loading SoilSense's bundle: one folder per state under assets/erosion/."""
from __future__ import annotations

import json

import numpy as np
import streamlit as st

from core.bundle import product_dir

ROOT = product_dir("erosion")

# 0 = not scored (left transparent), then slight .. very severe
CLASS_NAMES = ["Slight", "Moderate", "High", "Very high", "Severe", "Very severe"]
CLASS_RANGES = ["< 5", "5–10", "10–20", "20–40", "40–80", "> 80"]
CLASS_COLORS = ["#1a9850", "#a6d96a", "#fee08b", "#fdae61", "#f46d43", "#a50026"]


def regions() -> list[str]:
    """States with an exported bundle, in a fixed order."""
    if not ROOT.exists():
        return []
    return sorted(p.name for p in ROOT.iterdir() if (p / "meta.json").exists())


@st.cache_data(show_spinner=False)
def load(region: str) -> dict:
    d = ROOT / region
    z = np.load(d / "classes.npz")
    read = lambda n: json.loads((d / n).read_text(encoding="utf-8"))
    return {"meta": read("meta.json"),
            "classes": {k: z[k] for k in z.files if k != "bounds"},
            "bounds": z["bounds"].tolist(),
            "catchments": read("catchments.geojson"),
            "districts": read("districts.geojson"),
            "outline": read("outline.geojson")}
