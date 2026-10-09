"""Which river gauge, if any, is on each place's own river.

    python scripts/build/build_gauge_link.py            # build the web asset
    python scripts/build/build_gauge_link.py --selftest # the rule on a toy river

Writes  webapp/assets/flood/gauge_link.npz    per display cell: gauge, relation, km,
                                              river (1 = beside a river a flood can come from)
        webapp/assets/flood/gauge_link.json   gauge order, the rule, per-gauge counts

════════════════════════════════════════════════════════════════════════════
WHY
════════════════════════════════════════════════════════════════════════════
The forecast screen used to show the NEAREST gauge for any clicked spot —
often on a different river, yet presented just as solidly as a gauge on the
spot's own river. A gauge's checked forecast is about ITS river, so it now
appears as "the gauge on this river" only when it is (FLOOD_SCREEN_PLAN.md,
Phase 5a).

════════════════════════════════════════════════════════════════════════════
THE RULE (fixed before building)
════════════════════════════════════════════════════════════════════════════
A place's river is its nearest channel, at the scale WHERE uses for it: the
trunk network (>= 100 km2 upstream) if the place is within 25 m above it,
else the small network (>= 10 km2) if within 25 m of that, else it has no
river a flood can come from. A gauge is on that river when BOTH:

    same flow path    following the steepest rise in flow accumulation (the
                      walk build_gauge_reach.py uses), the river passes the
                      gauge (gauge downstream) or the gauge's river passes the
                      place (gauge upstream)
    same river        drainage area within x0.5 - x2 of the gauge's, so a
                      small side stream, or a river doubled by a big
                      confluence, counts as a different river
    and near          within 60 km along the river

If both an upstream and a downstream gauge qualify, the nearer one along
the river is used. Every place beside a river is linked — whatever its flood
chance: which river a place is on does not depend on how likely it is to go
under water (until 2026-09-28 only ground with a >=2% chance was linked, so a
gauge in a narrow valley — Sagalee, its own spot at 1% — was "not on this
place's river" at its own dot). Places above every river are linked through
their nearest low ground — the screen does that lookup.

════════════════════════════════════════════════════════════════════════════
WHERE EACH GAUGE SITS ON THE MAP'S RIVERS (fixed 2026-09-28)
════════════════════════════════════════════════════════════════════════════
A gauge is placed on the NEAREST channel within 2 km of its published
location that is the right size for it:

    CWC, catchment published   upstream area within x0.5-x2 of it (when the
                               catchment lies mostly outside the map — the
                               Siang, fed from Tibet — any trunk river)
    NWDP                       big enough to carry the gauge's typical
                               monsoon flow (median June-September flow at
                               most MAX_RUNOFF per km2)
    otherwise                  any channel of the small network

A gauge with no such channel is not linked to any place. Neither is a gauge
whose published coordinates are wrong in NWDP's own data (TOWN_ONLY: we only
know its town, not which stretch of river it measures). Flows are taken from
the gauge's usable record only (gauge_records.RECORD_STARTS).

The old rule took the BIGGEST channel within 1.5 km. On a river that is
always the downstream edge of the search box, so every gauge was placed
1.5-2 km downstream of its real spot. Where a bigger river was within
1.5 km, it jumped onto the wrong river entirely (Pagoda: published 176 km2,
placed on a 1,472 km2 river). The nearest-channel rule lands within 0.3 km
for 27 of 32 gauges, matching CWC's published catchments to ~1-2%.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))

import numpy as np

TRUNK_CELLS = 10_000          # 100 km2 of 100 m cells — WHERE's trunk network
SMALL_CELLS = 1_000           # 10 km2 — WHERE's small network
HAND_CEILING_M = 25.0         # WHERE's physical ceiling
AREA_RATIO = 2.0
MAX_KM = 60.0
FLOODABLE_MIN = 0.02          # 100 m cells considered: some chance a flood reaches them
SNAP_PX = 20                  # a gauge goes to the nearest channel of its size within 2 km
MAX_RUNOFF = 0.4              # m3/s per km2 — above any Arunachal river's typical monsoon flow
SAME_FLOW = 0.02              # a channel cell beside a walked cell, within 2% of its flow, is that river
# NWDP's own coordinates for these are wrong (Kashmir, Uttarakhand); the
# registry stands in the town (nwdp_stations.py), which does not say which
# stretch of river the gauge is on
TOWN_ONLY = {"Changlang": "Changlang town", "Ziro": "Ziro town"}
NB =[(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


# ── the river network ─────────────────────────────────────────────────────
def downstream_pointers(acc: np.ndarray, cells: np.ndarray) -> np.ndarray:
    """For each flat cell index in `cells`, the flat index of its neighbour
    with the largest flow accumulation greater than its own (-1 if none) —
    the same step build_gauge_reach.walk() takes."""
    H, W = acc.shape
    r, c = np.divmod(cells, W)
    best = acc.ravel()[cells].astype(np.float64)
    nxt = np.full(len(cells), -1, np.int64)
    for dr, dc in NB:
        r2, c2 = r + dr, c + dc
        ok = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
        v = np.full(len(cells), -np.inf)
        v[ok] = acc[r2[ok], c2[ok]]
        better = v > best
        best = np.where(better, v, best)
        nxt = np.where(better, r2 * W + c2, nxt)
    return nxt


def link_network(acc: np.ndarray, gauge_cells: list[int], cell_km: float = 0.1):
    """Walk the network once. Returns, for every channel cell (acc >=
    SMALL_CELLS, plus the gauge cells):
        idx        flat indices, sorted
        down_g     first gauge met going downstream (-1 none), down_km
        up_g       nearest gauge upstream whose river passes here (-1), up_km"""
    flat = acc.ravel()
    idx = np.union1d(np.flatnonzero(flat >= SMALL_CELLS), np.asarray(gauge_cells, np.int64))
    nxt = downstream_pointers(acc, idx)
    W = acc.shape[1]
    pos = {int(v): i for i, v in enumerate(idx)}
    step = np.where(nxt >= 0, cell_km * np.where(
        (np.abs(nxt // W - idx // W) + np.abs(nxt % W - idx % W)) == 2, np.sqrt(2), 1.0), 0.0)
    gauge_at = np.full(len(idx), -1, np.int32)
    for g, cell in enumerate(gauge_cells):
        gauge_at[pos[int(cell)]] = g
    # downstream: process from the most accumulated cell down, so each cell's
    # next cell (always more accumulated) is already resolved
    order = np.argsort(-flat[idx], kind="stable")
    down_g = np.full(len(idx), -1, np.int32)
    down_km = np.full(len(idx), np.inf)
    for i in order:
        if gauge_at[i] >= 0:
            down_g[i], down_km[i] = gauge_at[i], 0.0
            continue
        j = pos.get(int(nxt[i]), -1) if nxt[i] >= 0 else -1
        if j >= 0 and down_g[j] >= 0:
            down_g[i], down_km[i] = down_g[j], down_km[j] + step[i]
    # upstream gauges: walk each gauge's river down and keep, per cell, the
    # nearest gauge that is still THIS river's size. Checking the size here,
    # not afterwards, matters: below a confluence the nearest upstream gauge
    # can be the tributary's, which the size rule rejects — and keeping only
    # it would hide the main river's gauge (the toy test caught exactly
    # that). A river only grows downstream, so once a gauge's river is more
    # than AREA_RATIO times the gauge's size, it stays so and the walk stops.
    up_g = np.full(len(idx), -1, np.int32)
    up_km = np.full(len(idx), np.inf)
    for g, cell in enumerate(gauge_cells):
        i, km = pos[int(cell)], 0.0
        limit = AREA_RATIO * float(flat[int(cell)])
        while i >= 0 and km <= MAX_KM and flat[idx[i]] <= limit:
            if km < up_km[i]:
                up_g[i], up_km[i] = g, km
            if nxt[i] < 0:
                break
            km += step[i]
            i = pos.get(int(nxt[i]), -1)
    # The steepest-rise walk can step PAST a cell of the same river: it jumps
    # to the most-accumulated neighbour, which on a diagonal is often two cells
    # on. A channel cell beside a walked cell that carries the same flow
    # (within SAME_FLOW) is that river. Without this, ground 0.4 km below the
    # Pasighat gauge on the Siang read "a different river" (2026-09-28). A side
    # stream beside a river carries far less flow, so it never qualifies. One
    # pass, from the walked links only, so nothing chains.
    H = acc.shape[0]
    r, c = np.divmod(idx, W)
    a = flat[idx].astype(np.float64)
    for arr_g, arr_km in ((down_g, down_km), (up_g, up_km)):
        g0, k0 = arr_g.copy(), arr_km.copy()
        for dr, dc in NB:
            r2, c2 = r + dr, c + dc
            inb = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
            nb = np.where(inb, r2 * W + c2, -1)
            j = np.clip(np.searchsorted(idx, nb), 0, len(idx) - 1)
            hit = inb & (idx[j] == nb) & (g0[j] >= 0) & (g0 < 0)
            hit &= np.abs(a[j] - a) <= SAME_FLOW * a
            km_new = k0[j] + cell_km * (np.sqrt(2) if dr and dc else 1.0)
            better = hit & (km_new < arr_km)
            arr_g[better], arr_km[better] = g0[j][better], km_new[better]
    return idx, down_g, down_km, up_g, up_km


def link_cells(river_cells: np.ndarray, acc_flat: np.ndarray, gauge_area: np.ndarray, net) -> tuple:
    """Apply the rule to each place's river cell (flat index; -1 = no river).
    Returns (gauge, relation 1=gauge upstream / 2=gauge downstream, km)."""
    idx, down_g, down_km, up_g, up_km = net
    where = np.searchsorted(idx, river_cells)
    where = np.clip(where, 0, len(idx) - 1)
    found = (river_cells >= 0) & (idx[where] == river_cells)
    a = np.where(river_cells >= 0, acc_flat[np.clip(river_cells, 0, None)], 0).astype(np.float64)
    g_out = np.full(len(river_cells), -1, np.int32)
    rel = np.zeros(len(river_cells), np.int8)
    km = np.full(len(river_cells), np.nan)
    dg, dk = down_g[where], down_km[where]
    ug, uk = up_g[where], up_km[where]
    ok_d = found & (dg >= 0) & (dk <= MAX_KM) & (gauge_area[np.clip(dg, 0, None)] <= AREA_RATIO * a)
    ok_u = found & (ug >= 0) & (uk <= MAX_KM) & (a <= AREA_RATIO * gauge_area[np.clip(ug, 0, None)])
    use_u = ok_u & (~ok_d | (uk <= dk))
    use_d = ok_d & ~use_u
    g_out[use_u], rel[use_u], km[use_u] = ug[use_u], 1, uk[use_u]
    g_out[use_d], rel[use_d], km[use_d] = dg[use_d], 2, dk[use_d]
    return g_out, rel, km


def snap(acc: np.ndarray, r0: int, c0: int, lo: float = SMALL_CELLS,
         hi: float = np.inf) -> int:
    """Flat index of the nearest channel cell within SNAP_PX of (r0, c0)
    whose upstream area is lo..hi cells; -1 when there is none."""
    ra, ca = max(r0 - SNAP_PX, 0), max(c0 - SNAP_PX, 0)
    win = acc[ra:r0 + SNAP_PX + 1, ca:c0 + SNAP_PX + 1]
    rr, cc = np.nonzero((win >= max(lo, SMALL_CELLS)) & (win <= hi))
    d = np.hypot(rr + ra - r0, cc + ca - c0)
    ok = d <= SNAP_PX
    if not ok.any():
        return -1
    j = np.flatnonzero(ok)[np.argmin(d[ok])]
    return int((rr[j] + ra) * acc.shape[1] + cc[j] + ca)


def size_bounds(code: str, network: str, acc_max: float, flows: dict) -> tuple:
    """(lo, hi, basis): the upstream area, in 100 m cells, a gauge's river
    must have — see the module docstring."""
    if network == "CWC":
        from flood_stations import STATIONS
        a = STATIONS.get(code, {}).get("catchment_km2")
        if not a:
            return SMALL_CELLS, np.inf, "no published catchment"
        if a * 100 / AREA_RATIO > acc_max:
            return TRUNK_CELLS, np.inf, f"catchment {a:,.0f} km2, mostly outside the map"
        return a * 100 / AREA_RATIO, a * 100 * AREA_RATIO, f"CWC catchment {a:,.0f} km2"
    q = flows.get(code)
    if q is None:
        return SMALL_CELLS, np.inf, "no flow record"
    return q / MAX_RUNOFF * 100, np.inf, f"typical monsoon flow {q:.0f} m3/s"


def nwdp_typical_flow() -> dict:
    """Median June-September discharge per NWDP station, from the archive
    (fetch_24_nwdp_discharge.py), over each gauge's usable record only;
    gross sensor errors dropped."""
    import pandas as pd
    from common import INTERIM
    from gauge_records import RECORD_STARTS
    f = INTERIM / "flood_when" / "nwdp_combined.parquet"
    if not f.exists():
        return {}
    d = pd.read_parquet(f, columns=["Station", "Data Acquisition Time", "discharge"])
    q = pd.to_numeric(d["discharge"], errors="coerce")
    t = pd.to_datetime(d["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce")
    start = pd.to_datetime(d["Station"].map(RECORD_STARTS))
    ok = (q >= 0) & (q < 20_000) & t.dt.month.between(6, 9) & ~(t < start)
    return q[ok].groupby(d.loc[ok, "Station"]).median().to_dict()


# ── the build ─────────────────────────────────────────────────────────────
def build() -> None:
    import rasterio
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    import grid as G
    from common import INTERIM, PROCESSED, ROOT

    print("Gauge link — which gauge is on each place's own river")
    stack = INTERIM / "terrain_unmasked"
    with rasterio.open(stack / "hydro_flowacc_cells.tif") as s:
        acc = np.nan_to_num(s.read(1), nan=-1.0).astype(np.float32)
        tf = s.transform
    st = json.loads((ROOT / "models" / "flood_when_gauge" / "stations.json").read_text())
    codes = list(st)
    to_utm = Transformer.from_crs("EPSG:4326", G.CRS, always_xy=True)
    to_ll = Transformer.from_crs(G.CRS, "EPSG:4326", always_xy=True)
    flows = nwdp_typical_flow()
    acc_max = float(acc.max())
    gauge_cells, placement = [], {}
    print(f"  {'gauge':<24}{'moved':>7}{'river km2':>11}  basis")
    for code in codes:
        x, y = to_utm.transform(st[code]["lon"], st[code]["lat"])
        c0, r0 = ~tf * (x, y)
        lo, hi, basis = size_bounds(code, st[code]["network"], acc_max, flows)
        cell = -1 if code in TOWN_ONLY else snap(acc, int(r0), int(c0), lo, hi)
        gauge_cells.append(cell)
        p = {"listed": [st[code]["lat"], st[code]["lon"]], "basis": basis}
        if cell >= 0:
            r, c = divmod(cell, acc.shape[1])
            lon, lat = to_ll.transform(*(tf * (c + 0.5, r + 0.5)))
            p.update(placed=[round(lat, 5), round(lon, 5)],
                     moved_km=round(0.1 * float(np.hypot(r - int(r0), c - int(c0))), 2),
                     river_km2=round(float(acc[r, c]) * 0.01))
            print(f"  {st[code]['name'][:23]:<24}{p['moved_km']:>6.1f}k{p['river_km2']:>11,}  {basis}")
        else:
            p["placed"] = None
            p["not_linked"] = (f"its published coordinates are wrong; only {TOWN_ONLY[code]} is "
                               "known, not which stretch of river it measures"
                               if code in TOWN_ONLY else
                               "no river of its size within 2 km of its listed location")
            print(f"  {st[code]['name'][:23]:<24}{'-':>7}{'-':>11}  {basis} -> NOT LINKED")
        placement[code] = p
    # only placed gauges enter the network; `placed` maps back to `codes`
    placed = np.asarray([i for i, c in enumerate(gauge_cells) if c >= 0], np.int64)
    pcells = [gauge_cells[i] for i in placed]
    gauge_area = acc.ravel()[pcells].astype(np.float64)
    net = link_network(acc, pcells)
    print(f"  {len(net[0]):,} channel cells walked, {len(pcells)} of {len(codes)} gauges placed")

    with rasterio.open(PROCESSED / "flood_where_prob_100m.tif") as s:
        where = s.read(1)
    hand = {}
    for n in ("hydro_hand_m", "hydro_hand_small_m"):
        with rasterio.open(stack / f"{n}.tif") as s:
            hand[n] = s.read(1)
    # every cell beside a river (within WHERE's height ceiling of a channel),
    # whatever its flood chance
    beside = np.isfinite(where) & ((hand["hydro_hand_m"] <= HAND_CEILING_M)
                                   | (hand["hydro_hand_small_m"] <= HAND_CEILING_M))
    rr, cc = np.nonzero(beside)
    floodable = where[rr, cc] >= FLOODABLE_MIN
    print(f"  {len(rr):,} 100 m cells beside a river, {int(floodable.sum()):,} of them floodable")

    W = acc.shape[1]
    river = np.full(len(rr), -1, np.int64)
    for thr, hname in ((TRUNK_CELLS, "hydro_hand_m"), (SMALL_CELLS, "hydro_hand_small_m")):
        ch = np.flatnonzero(acc.ravel() >= thr)
        tree = cKDTree(np.column_stack(np.divmod(ch, W)))
        need = (river < 0) & (hand[hname][rr, cc] <= HAND_CEILING_M)
        _, j = tree.query(np.column_stack([rr[need], cc[need]]))
        river[need] = ch[j]
    g, rel, km = link_cells(river, acc.ravel(), gauge_area, net)
    g = np.where(g >= 0, placed[np.clip(g, 0, None)], -1)           # -> index into codes
    print(f"  linked to a gauge on their own river: {100*(g >= 0).mean():.1f}% of riverside cells, "
          f"{100*(g[floodable] >= 0).mean():.1f}% of floodable ones")

    # onto the display grid: each display cell takes the link of its most
    # floodable 100 m cell (the display layer shows that cell's chance too)
    base = ROOT / "webapp" / "assets" / "base"
    gj = json.loads((base / "grid.json").read_text())
    to_ll = Transformer.from_crs(G.CRS, "EPSG:4326", always_xy=True)
    xs, ys = rasterio.transform.xy(G.TRANSFORM, rr, cc)
    lon, lat = to_ll.transform(np.asarray(xs), np.asarray(ys))
    dr = ((gj["north"] - lat) / (gj["north"] - gj["south"]) * gj["height"]).astype(int)
    dc = ((lon - gj["west"]) / (gj["east"] - gj["west"]) * gj["width"]).astype(int)
    inb = (dr >= 0) & (dr < gj["height"]) & (dc >= 0) & (dc < gj["width"])
    key = dr * gj["width"] + dc
    wv = where[rr, cc]
    order = np.lexsort((-wv, key))                 # by display cell, most floodable first
    first = np.r_[True, key[order][1:] != key[order][:-1]]
    pick = order[first & inb[order]]
    out_g = np.full(gj["height"] * gj["width"], -1, np.int8)
    out_rel = np.zeros(gj["height"] * gj["width"], np.int8)
    out_km = np.zeros(gj["height"] * gj["width"], np.uint16)
    out_g[key[pick]] = g[pick]
    out_rel[key[pick]] = rel[pick]
    out_km[key[pick]] = np.where(np.isfinite(km[pick]), np.round(km[pick] * 10), 0).astype(np.uint16)
    out_river = np.zeros(gj["height"] * gj["width"], np.uint8)
    out_river[key[pick]] = (river[pick] >= 0).astype(np.uint8)
    shape = (gj["height"], gj["width"])
    web = ROOT / "webapp" / "assets" / "flood"
    np.savez_compressed(web / "gauge_link.npz", gauge=out_g.reshape(shape),
                        relation=out_rel.reshape(shape), km10=out_km.reshape(shape),
                        river=out_river.reshape(shape))
    per = {codes[i]: {"name": st[codes[i]]["name"],
                      "display_cells": int((out_g == i).sum()),
                      "floodable_km2": round(float(((g[floodable] == i) * 0.01).sum()), 1),
                      **placement[codes[i]]}
           for i in range(len(codes))}
    (web / "gauge_link.json").write_text(json.dumps({
        "codes": codes,
        "relation": {"1": "gauge upstream — this river flows from the gauge to here",
                     "2": "gauge downstream — this river flows past the gauge"},
        "km": "along the river, km x 10 (km10)",
        "rule": {"river": f"nearest trunk channel (>= {TRUNK_CELLS//100} km2) within "
                          f"{HAND_CEILING_M:.0f} m above, else nearest small channel "
                          f"(>= {SMALL_CELLS//100} km2) within {HAND_CEILING_M:.0f} m",
                 "same_path": "steepest-rise flow walk, as build_gauge_reach.py",
                 "same_river": f"drainage area within x{1/AREA_RATIO:g}-x{AREA_RATIO:g}",
                 "near": f"within {MAX_KM:.0f} km along the river",
                 "gauge_placement": (f"nearest channel within {SNAP_PX / 10:g} km of the listed "
                                     "location that is the gauge's size (CWC published "
                                     f"catchment x{1/AREA_RATIO:g}-x{AREA_RATIO:g}; NWDP big "
                                     "enough for its typical monsoon flow at "
                                     f"{MAX_RUNOFF} m3/s per km2); none -> not linked")},
        "per_gauge": per,
    }, indent=2))
    print(f"  display cells linked: {int((out_g >= 0).sum()):,}")
    for code in codes:
        p = per[code]
        print(f"    {p['name'][:20]:<21}{p['display_cells']:>7,} display cells  "
              f"{p['floodable_km2']:>8.1f} km2 floodable")
    print(f"  wrote {web / 'gauge_link.npz'}")


# ── the rule on a toy river ───────────────────────────────────────────────
def selftest() -> None:
    """The rule on a toy network, not the data: a trunk river flowing east
    along row 5 (gauge at column 10); a tributary flowing south into it at
    column 20 (gauge at row 2); a small stream flowing north into the trunk
    at column 5, ABOVE the trunk gauge."""
    H, W = 12, 60
    acc = np.zeros((H, W), np.float32)
    acc[5, :] = 20_000 + np.arange(W) * 100              # trunk, growing east
    acc[0:5, 20] = 1_500 + np.arange(5) * 50              # tributary, flowing south
    acc[5, 21:] += 1_700                                  # trunk after the confluence
    acc[6:12, 5] = 1_150 - np.arange(6) * 10              # small stream, flowing north
    g_trunk, g_trib = 5 * W + 10, 2 * W + 20
    ga = acc.ravel()[[g_trunk, g_trib]].astype(np.float64)

    def one(cell, km_per_cell=1.0):
        net = link_network(acc, [g_trunk, g_trib], cell_km=km_per_cell)
        g, rel, km = link_cells(np.array([cell]), acc.ravel(), ga, net)
        return int(g[0]), int(rel[0]), (None if np.isnan(km[0]) else round(float(km[0]), 3))

    checks = {
        "trunk above its gauge -> gauge 6 km downstream": (one(5 * W + 4), (0, 2, 6.0)),
        "trunk below its gauge -> gauge 20 km upstream": (one(5 * W + 30), (0, 1, 20.0)),
        "tributary above its gauge -> its own gauge": (one(1 * W + 20), (1, 2, 1.0)),
        "tributary below its gauge -> its own gauge": (one(3 * W + 20), (1, 1, 1.0)),
        "trunk 98 km below the gauge -> too far": (one(5 * W + 59, km_per_cell=2.0), (-1, 0, None)),
        "small stream flowing into the trunk -> not the trunk's gauge (area)":
            (one(9 * W + 5), (-1, 0, None)),
        "no river": (one(-1), (-1, 0, None)),
    }
    # gauge placement: listed 3 cells north of the trunk at column 16, where
    # the tributary (column 20) is 4 cells away and the trunk grows east.
    # The old biggest-channel rule would have taken the trunk's east end.
    big = np.zeros((60, 60), np.float32)
    big[30, :] = 20_000 + np.arange(60) * 100            # trunk, growing east
    big[0:30, 34] = 1_500 + np.arange(30) * 50           # tributary at column 34
    at = lambda r, c: (int(r), int(c))
    rc = lambda k: at(*divmod(k, 60)) if k >= 0 else None
    checks.update({
        "gauge placed on the nearest channel, not the biggest": (rc(snap(big, 27, 16)), (30, 16)),
        "a gauge too big for the tributary skips it for the trunk":
            (rc(snap(big, 25, 31, lo=10_000)), (30, 31)),
        "a gauge the tributary's size takes the tributary": (rc(snap(big, 25, 31, hi=5_000)), (25, 34)),
        "nothing of its size within 2 km -> not placed": (rc(snap(big, 5, 5, lo=10**7)), None),
    })
    # a cell of the trunk the walk steps past: row 6, beside the trunk, same
    # flow — the gauge (row 5, col 10) is upstream of it; a side stream
    # beside the trunk, with far less flow, stays unlinked
    wide = acc.copy()
    wide[6, 12] = wide[5, 12] - 20                       # same river, 0.1% less flow
    wide[4, 14] = 1_600                                  # side stream beside the trunk
    def one_w(cell):
        net = link_network(wide, [g_trunk, g_trib], cell_km=1.0)
        ga_w = wide.ravel()[[g_trunk, g_trib]].astype(np.float64)
        g, rel, km = link_cells(np.array([cell]), wide.ravel(), ga_w, net)
        return int(g[0]), int(rel[0]), (None if np.isnan(km[0]) else round(float(km[0]), 3))
    checks.update({
        "a trunk cell the walk steps past -> the trunk's gauge": (one_w(6 * W + 12), (0, 1, 2.414)),
        "a side stream beside the trunk -> not the trunk's gauge": (one_w(4 * W + 14), (-1, 0, None)),
    })
    bad = {k: v for k, v in checks.items() if v[0] != v[1]}
    for k, (got, want) in checks.items():
        print(f"  {'ok  ' if got == want else 'FAIL'} {k}: {got}")
    if bad:
        raise SystemExit(f"selftest FAILED: {bad}")
    print("selftest: PASS — same path, same-size river and distance rules behave")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else build()
