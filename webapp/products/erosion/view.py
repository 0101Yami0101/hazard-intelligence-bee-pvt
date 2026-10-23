"""SoilSense pages: the erosion map, the priority list, and how to read them.

First version (Phase 0). What it must never do, by design
(docs/design/EROSION_MODULE.md §6, EROSION_PLAN.md register V-16 / V-17):
  - show a class or a rank as a chance;
  - hide that two inputs are unsettled — the rain-strength map and the cover
    value for "tree" land — so both alternative runs are one click away, and
    every top catchment says whether it stays on top under the other rain map;
  - call un-scored land "low": river land, water and towns stay uncoloured.
"""
from __future__ import annotations

import html

import folium
import pandas as pd
import streamlit as st
from folium.plugins import Fullscreen
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium

import core.theme as T
from core.mapping import rgba_overlay
from products.erosion import data as D
from products.flood import ui as U          # the shared dashboard look

VIEWS = [("🗺️", "Erosion map"), ("📋", "Priority list"), ("📖", "How to read this")]
HOME = "Erosion map"
RUNS = {"main": "Main run", "ired": "Other rain map", "treeC_alt": "Lower forest value"}
RUN_HELP = {
    "main": "Rain strength from InRESatE (closest to the only gauge-measured value, at "
            "Guwahati); cover value 0.03 for land the satellite map calls 'tree'.",
    "ired": "The same, with the other national rain-strength map (IRED). The two maps "
            "agree on the broad picture but not on every catchment.",
    "treeC_alt": "The same, with cover value 0.003 for 'tree' land: right for closed forest, "
                 "too low for tea gardens and jhum fallow, which that class also contains.",
}
ALL = "All of the state"
# Once the tree split is adopted (Phase 1 E1.1, EROSION_PLAN.md) the main run
# measures cover per square, and the third option shows what the split changed.
RUNS_SPLIT = {"main": "Main run", "ired": "Other rain map", "treeC_avg": "Before the tree split"}
RUN_HELP_SPLIT = {
    "main": "Rain strength from InRESatE (closest to the only gauge-measured value, at "
            "Guwahati). Ground cover measured per square: land the satellite map calls 'tree' "
            "is split into forest, tea or bush, regrowing and freshly cleared ground.",
    "ired": RUN_HELP["ired"],
    "treeC_avg": "The same, with one cover value (0.03) for all 'tree' land, as before the "
                 "split: shows what measuring the cover changed.",
}


def _runs(meta: dict) -> tuple[dict, dict, str]:
    """(labels, help, comparison key) — the split's set once it is adopted."""
    if meta.get("tree_split", {}).get("adopted"):
        return RUNS_SPLIT, RUN_HELP_SPLIT, "treeC_avg"
    return RUNS, RUN_HELP, "treeC_alt"


def _esc(s) -> str:
    return html.escape(str(s))


def _nav() -> str:
    if st.session_state.get("er_view") not in [v for _, v in VIEWS]:
        st.session_state.er_view = HOME
    with st.sidebar:
        for icon, label in VIEWS:
            active = st.session_state.er_view == label
            if st.button(f"{icon}  {label}", key=f"ernav_{label}", width="stretch",
                         type="primary" if active else "secondary"):
                if not active:
                    st.session_state.er_view = label
                    st.rerun()
    return st.session_state.er_view


def _region() -> str | None:
    regs = D.regions()
    with st.sidebar:
        st.divider()
        st.markdown("<div class='side-label'>State</div>", unsafe_allow_html=True)
        if not regs:
            return None
        names = {r: r.title() for r in regs}
        r = st.selectbox("State", regs, format_func=names.get, key="er_region",
                         label_visibility="collapsed")
        st.caption("Arunachal Pradesh: computed with the same code as a test run, "
                   "not yet reviewed for showing (the forest cover question).")
    return r


def _settings():
    with st.sidebar:
        st.divider()
        st.markdown("<div class='side-label'>Map settings</div>", unsafe_allow_html=True)
        basemap = st.radio("Basemap", list(T.BASEMAPS), horizontal=True,
                           index=list(T.BASEMAPS).index(T.BASEMAP_DEFAULT),
                           label_visibility="collapsed", key="set_basemap")
        opacity = st.slider("Overlay opacity", 0.0, 1.0, 0.75, 0.05, key="set_opacity")
        c1, c2 = st.columns(2)
        with c1:
            top = st.toggle("Top 20", value=True, key="er_top",
                            help="Outline the 20 highest-ranked small catchments.")
            dists = st.toggle("Districts", value=False, key="er_dists")
        with c2:
            labels = st.toggle("Names", value=True, key="set_labels")
    return dict(basemap=basemap, opacity=opacity, top=top, districts=dists, labels=labels)


def _district_pick(B) -> str:
    names = sorted(f["properties"]["district"] for f in B["districts"]["features"])
    return st.selectbox("District", [ALL] + names, key="er_district",
                        label_visibility="collapsed",
                        help="Pick a district to zoom to it and see its figures.")


def _feature(B, name):
    return next((f for f in B["districts"]["features"]
                 if f["properties"]["district"] == name), None)


def _bounds(geom) -> list:
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for x in c:
                walk(x)
    walk(geom["coordinates"])
    return [[min(ys), min(xs)], [max(ys), max(xs)]]


def _map(B, run: str, s: dict, focus: str) -> None:
    meta = B["meta"]
    m = folium.Map(location=meta["center"], zoom_start=7, tiles=None, control_scale=True)
    m.options.update(minZoom=6, maxBounds=[[meta["bounds"][0][0] - 2, meta["bounds"][0][1] - 2],
                                           [meta["bounds"][1][0] + 2, meta["bounds"][1][1] + 2]])
    url, attr = T.BASEMAPS[s["basemap"]]
    folium.TileLayer(url, attr=attr, name="Base", control=False, no_wrap=True).add_to(m)
    folium.map.CustomPane("labels", z_index=650).add_to(m)
    if s["labels"]:
        folium.TileLayer(T.LABEL_TILES[s["basemap"]],
                         attr=attr if "Esri" in attr else T.ESRI_CANVAS,
                         pane="labels", control=False, no_wrap=True).add_to(m)
    Fullscreen(position="topleft").add_to(m)
    if s["opacity"] > 0:
        ImageOverlay(rgba_overlay(B["classes"][run], D.CLASS_COLORS, alpha=255),
                     bounds=B["bounds"], opacity=s["opacity"], interactive=False,
                     zindex=2).add_to(m)
    ink = T.BOUNDARY_INK.get(s["basemap"], T.ACCENT)
    folium.GeoJson(B["outline"], style_function=lambda _: {"color": ink, "weight": 2,
                                                           "fill": False}).add_to(m)
    if s["districts"]:
        folium.GeoJson(B["districts"], style_function=lambda _: {
            "color": "#e5e7eb", "weight": 0.8, "fill": False, "opacity": 0.7}).add_to(m)
    if s["top"]:
        top = {"type": "FeatureCollection",
               "features": [f for f in B["catchments"]["features"]
                            if f["properties"][f"rank_{run}"] <= 20]}
        folium.GeoJson(
            top, style_function=lambda _: {"color": "#ffffff", "weight": 1.6,
                                           "fill": True, "fillOpacity": 0.0},
            highlight_function=lambda _: {"weight": 3, "color": "#ffd166"},
            tooltip=folium.GeoJsonTooltip(
                fields=[f"rank_{run}", "district", f"meanA_{run}", "main_driver", "mark"],
                aliases=["Rank", "District", "Average loss (t/ha/yr)", "Main cause", ""],
                sticky=True)).add_to(m)
    if focus != ALL:
        f = _feature(B, focus)
        if f is not None:
            folium.GeoJson(f, style_function=lambda _: {"color": "#ffd166", "weight": 3,
                                                        "fill": False}).add_to(m)
            m.fit_bounds(_bounds(f["geometry"]))
    st_folium(m, height=U.MAP_H, use_container_width=True, pixelated=True,
              returned_objects=[], key=f"ermap_{run}_{focus}")


def _legend(shares: dict) -> None:
    names = [f"{n} <span>{r}</span>" for n, r in zip(D.CLASS_NAMES, D.CLASS_RANGES)]
    vals = [shares.get(k, 0) / 100 for k in
            ("slight", "moderate", "high", "very high", "severe", "very severe")]
    st.markdown(U.legend(names, D.CLASS_COLORS, vals,
                         tip="Share of scored land in each class, t/ha/yr. Uncoloured land "
                             "is not scored by this method: rivers and land within 2 m of a "
                             "large river, water, towns."), unsafe_allow_html=True)


def _district_card(B, name: str) -> None:
    f = _feature(B, name)
    if f is None:
        return
    p = f["properties"]
    n = len(B["districts"]["features"])
    tiles = [
        U._tile("Average loss", f"{p['meanA_main']:.0f}", "t/ha/yr, scored land", "er_estimate"),
        U._tile("High or worse", f"{p['high_or_worse_pct']:.0f}%", "≥ 10 t/ha/yr", "er_class"),
        U._tile("Rank", f"{p['rank_main']} of {n}", f"other rain map: {p['rank_ired']} · "
                f"{_runs(B['meta'])[0][_runs(B['meta'])[2]].lower()}: "
                f"{p.get('rank_' + _runs(B['meta'])[2], '–')}", "er_rank"),
        U._tile("Total", f"{p['total_t_per_yr'] / 1e6:.1f} Mt",
                f"a year, over {p['scored_km2']:,.0f} km² scored"),
    ]
    st.markdown(U._sec(_esc(name)) + U._tiles(tiles, 2), unsafe_allow_html=True)
    cause = p["main_driver"] + (f", then {p['also']}" if p.get("also") else "")
    # st.caption, not a .fs-note: that style is one line and ran past the panel
    st.caption(f"Main cause against the state average: **{cause}**. "
               f"{p['not_scored_pct']:.0f}% of the district is not scored "
               f"(river land, water, towns).")


def _top_list(B, run: str, n: int = 10) -> None:
    feats = sorted((f["properties"] for f in B["catchments"]["features"]),
                   key=lambda p: p[f"rank_{run}"])[:n]
    rows = []
    for p in feats:
        firm = p["mark"] == "top under both rain maps"
        right = (f"{p[f'meanA_{run}']:.0f} t/ha/yr"
                 + (" · <span style='color:#4cc37a'>firm</span>" if firm
                    else " · <span style='color:#f5b14c'>rain-dependent</span>"
                    if run == "main" else ""))
        rows.append(U._row(f"#{p[f'rank_{run}']}", "#e0a458",
                           f"{_esc(p['district'])} · {p['scored_km2']:.0f} km²"
                           f"<br><small>{_esc(p['main_driver'])}</small>", right))
    st.markdown(U._sec("Top catchments", U.badge("er_rank", mini=True),
                       note=_runs(B["meta"])[0][run]) + "".join(rows), unsafe_allow_html=True)


def _map_page(B, s) -> None:
    meta = B["meta"]
    focus = U.page_head("SoilSense · soil erosion",
                        f"{meta['state']} · first version, built {meta['generated_utc'][:10]}",
                        icon="◬", search_row=lambda: _district_pick(B), warn=False)
    U.key_row("er_estimate", "er_class", "er_rank",
              note="Rain-washed soil only: not riverbanks or landslides.")
    sh = meta["shares"]["main"]
    high = sum(sh[k] for k in ("high", "very high", "severe", "very severe"))
    dfeat = sorted((f["properties"] for f in B["districts"]["features"]),
                   key=lambda p: p["rank_main"])
    tiles = [
        U._tile("Land scored", f"{meta['scored_pct']:.0f}%", "the rest is river land, water, towns"),
        U._tile("High or worse", f"{high:.0f}%", "of scored land, ≥ 10 t/ha/yr", "er_class"),
        U._tile("Typical loss", f"{meta['median_A']:.0f}", "t/ha/yr, median of scored land",
                "er_estimate"),
        U._tile("Worst district", _esc(dfeat[0]["district"]),
                f"{dfeat[0]['meanA_main']:.0f} t/ha/yr on average", "er_rank"),
        U._tile("Catchments ranked", f"{meta['n_catchments']}", "small catchments, ≥ 5 km² scored"),
        U._tile("Firm in the top 20", f"{meta['n_top_both']} of 20",
                "stay top 20 under both rain maps", "er_rank"),
    ]
    st.markdown(U._tiles(tiles, 6), unsafe_allow_html=True)

    runs, helps, _ = _runs(meta)
    if st.session_state.get("er_run") not in runs:
        st.session_state.pop("er_run", None)        # an option from before the split
    run = st.segmented_control("Run", list(runs), format_func=runs.get, default="main",
                               key="er_run", label_visibility="collapsed") or "main"
    st.caption(helps[run])
    c_map, c_side = st.columns([2.5, 1.25], gap="medium")
    with c_map:
        _map(B, run, s, focus or ALL)
        _legend(meta["shares"][run])
        st.caption("On tree-covered land a square's class is indicative: one cover value "
                   "stands for forest, tea gardens and jhum fallow alike. Rank catchments, "
                   "not single squares.")
    with c_side:
        if focus and focus != ALL:
            _district_card(B, focus)
        _top_list(B, run)


def _table(feats, cols: dict) -> pd.DataFrame:
    df = pd.DataFrame([f["properties"] for f in feats])
    return df[list(cols)].rename(columns=cols)


def _list_page(B) -> None:
    meta = B["meta"]
    U.page_head("Priority list", f"{meta['state']} · where to survey and treat first",
                icon="◬", warn=False)
    U.key_row("er_rank", "er_estimate",
              note="Ranked by average estimated loss over the scored land of each unit.")
    dname = st.selectbox("Show catchments in", [ALL] + sorted(
        f["properties"]["district"] for f in B["districts"]["features"]), key="er_list_d")
    feats = sorted(B["catchments"]["features"], key=lambda f: f["properties"]["rank_main"])
    if dname != ALL:
        feats = [f for f in feats if f["properties"]["district"] == dname]
    cat = _table(feats, {"rank_main": "Rank", "district": "District", "scored_km2": "km² scored",
                         "meanA_main": "Avg loss t/ha/yr", "high_or_worse_pct": "High or worse %",
                         "main_driver": "Main cause", "mark": "Firmness",
                         "rank_ired": "Rank, other rain map",
                         f"rank_{_runs(meta)[2]}": f"Rank, {_runs(meta)[0][_runs(meta)[2]].lower()}",
                         "HYBAS_ID": "Catchment id"})
    st.markdown(U._sec("Small catchments", U.badge("er_rank", mini=True),
                       note=f"{len(cat)} shown · 'Firmness' is given for the top 20"),
                unsafe_allow_html=True)
    st.dataframe(cat, hide_index=True, width="stretch", height=380,
                 column_config={"Avg loss t/ha/yr": st.column_config.NumberColumn(format="%.0f"),
                                "High or worse %": st.column_config.NumberColumn(format="%.0f"),
                                "km² scored": st.column_config.NumberColumn(format="%.0f"),
                                "Catchment id": st.column_config.NumberColumn(format="%d")})
    dis = _table(sorted(B["districts"]["features"], key=lambda f: f["properties"]["rank_main"]),
                 {"rank_main": "Rank", "district": "District", "meanA_main": "Avg loss t/ha/yr",
                  "high_or_worse_pct": "High or worse %", "total_t_per_yr": "Total t/yr",
                  "main_driver": "Main cause", "rank_ired": "Rank, other rain map",
                  f"rank_{_runs(meta)[2]}": f"Rank, {_runs(meta)[0][_runs(meta)[2]].lower()}",
                  "not_scored_pct": "Not scored %"})
    dis["Total t/yr"] = (dis["Total t/yr"] / 1000).round().astype(int) * 1000
    st.markdown(U._sec("Districts", U.badge("er_rank", mini=True),
                       note="totals rounded to the nearest 1,000 t"), unsafe_allow_html=True)
    st.dataframe(dis, hide_index=True, width="stretch", height=420,
                 column_config={"Avg loss t/ha/yr": st.column_config.NumberColumn(format="%.0f"),
                                "High or worse %": st.column_config.NumberColumn(format="%.0f"),
                                "Total t/yr": st.column_config.NumberColumn(format="localized"),
                                "Not scored %": st.column_config.NumberColumn(format="%.0f")})
    d1, d2, d3 = st.columns(3)
    allc = _table(sorted(B["catchments"]["features"], key=lambda f: f["properties"]["rank_main"]),
                  {k: k for k in B["catchments"]["features"][0]["properties"]})
    d1.download_button("Catchments (CSV)", allc.to_csv(index=False).encode(),
                       f"soilsense_catchments_{meta['region']}.csv", "text/csv", width="stretch")
    d2.download_button("Districts (CSV)", dis.to_csv(index=False).encode(),
                       f"soilsense_districts_{meta['region']}.csv", "text/csv", width="stretch")
    import json
    d3.download_button("Catchments for GIS (GeoJSON)", json.dumps(B["catchments"]).encode(),
                       f"soilsense_catchments_{meta['region']}.geojson", "application/geo+json",
                       width="stretch")


def _how_page(B) -> None:
    meta = B["meta"]
    ck = meta["checks"]
    U.page_head("How to read SoilSense", f"{meta['state']} · method, checks and limits",
                icon="◬", warn=False)
    s1 = ck.get("S1", {}).get("main", {})
    ts = meta.get("tree_split", {})
    if ts.get("adopted"):
        sh = ts.get("share_of_tree_pct", {})
        pick = lambda pre: next((v for k, v in sh.items() if k.startswith(pre)), 0)
        cover_para = (
            "2. **Cover on \"tree\" land, now measured.** The satellite land-cover map calls forest, "
            "tea gardens and *jhum* land all \"tree\". Since Phase 1 each such square is split by "
            "canopy height (1 m) and recent clearing (forest-loss maps to 2025): "
            f"**forest {pick('T4'):.0f}%**, **tea or bush {pick('T3'):.0f}%**, "
            f"**regrowing {pick('T2'):.0f}%**, **freshly cleared {pick('T1'):.0f}%** "
            f"(no height data: {pick('T0'):.0f}%). The tea-versus-forest rule was set on "
            f"{ts.get('outlines', {}).get('tea', '?')} OpenStreetMap tea-garden outlines and "
            f"{ts.get('outlines', {}).get('forest', '?')} forest outlines, and scored "
            f"{ts.get('P1', 0):.2f} on a half it never saw; a blind check on satellite pictures "
            "passed too. *Before the tree split* shows the old single value, for comparison.")
    else:
        cover_para = (
            "2. **Cover on \"tree\" land.** The satellite land-cover map calls forest, tea gardens "
            "and young *jhum* fallow all \"tree\". The value used (0.03) is a fair average for "
            "that mix but too high for closed forest. *Lower forest value* shows the opposite "
            "case. The fix, splitting the class with satellite pictures, is the next phase.")
    st.markdown(f"""
**What it estimates.** How much soil rain washes off the land each year, in tonnes per hectare,
from the standard recipe used in Indian soil-conservation work (RUSLE). It multiplies five things:
**how hard the rain hits** (rain strength), **how easily the soil washes** (soil), **how steep and
long the slope is**, **how bare the ground is** (cover) and **protection** such as bunds and
terraces. Protection is unknown to us, so the map shows land **as if untreated**.

**Kinds of number.**
- *Estimate* (t/ha/yr): indicative, and can be off by a factor of several.
- *Class*: the estimate cut at 5, 10, 20, 40 and 80 t/ha/yr. It is as uncertain as the
  estimate.
- *Rank*: where to act first. It is the firmest number here, and it is marked when it
  depends on the rain map.

None of these is a chance.

**What is not scored** (left uncoloured): rivers and land within 2 m of a large river, water and
towns. On that land floods and bank cutting move the soil, and this recipe sees neither. That is
**{100 - meta['scored_pct']:.0f}%** of {meta['state']}.

**Two inputs are not settled yet, so both alternatives are shown.**
1. **Rain strength.** Two national maps exist. The one used checks within 5% of the only
   gauge-measured value we have (Guwahati); the other is 46% low there, and they disagree
   on the exact catchment order. *Other rain map* shows the difference. Catchments that stay
   in the top 20 under both are marked *firm*.
{cover_para}

**Checks it passed before being shown.**
- Hills come out about **{s1.get('ratio', 0):.0f}×** worse than plains.
- The rain map lands within 0.3% of the Guwahati gauge.
- No class takes most of the land.
- Un-scored land is never given a class.
- The top 20 catchments were each checked by eye on satellite pictures: all are steep, and
  half show cleared or bare slopes.
- Compared with the national 250 m erosion map, the order differs because that map's slope
  factor barely changes between flat and steep ground. Ours follows the slope, so our list
  starts in the hills.

**Limits.**
- Sheet and rill erosion only. Not gullies, riverbanks or landslides.
- Satellite rain misses short bursts.
- Soil comes from a 250 m global model.
- The terrain model includes treetops; flat land beside trees is corrected for this.
- District outlines are the Survey of India's official set (35 districts).

**What lifts these limits:**
- the department's treated-area records (protection);
- soil surveys;
- rain-intensity gauges;
- field checks of the ranked catchments.
""")


def render(shell) -> None:
    st.markdown(U.FS_CSS, unsafe_allow_html=True)
    view = _nav()
    region = _region()
    if region is None:
        st.error("**The SoilSense bundle is missing.** Run "
                 "`scripts/run/export_erosion_bundle.py` with REGION set.")
        return
    B = D.load(region)
    if view == "Erosion map":
        s = _settings()
        _map_page(B, s)
    elif view == "Priority list":
        _list_page(B)
    else:
        _how_page(B)
