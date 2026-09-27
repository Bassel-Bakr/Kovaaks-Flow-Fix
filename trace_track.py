"""Tracking along a drawn path: turn vector shapes into a KovaaK's scenario (2026-09-27).

The shapes are carved in chalk on a lecture hall's board, and a flying bot traces them: once round each closed shape
(repeating only the shorter stretch between where it joins and where it leaves), end to end along each open one,
flying a dashed route from one shape to the next. World Map is built with it (world_map.py). Any SVG works too:

    python trace_track.py drawing.svg "Scenario Name" [--speed 5] [--out out]

writes out/<Scenario Name>.sce and a picture of the board to test_out/<Scenario Name> board.png. Copy the scenario into
KovaaK's Scenarios folder by hand.

The numbers come from probes and play (.agents/skills/kovaaks-scenario-design/references/mechanics.md, "Flying bots,
waypoint paths", and scenario-types.md, "Case: tracking along a drawn path"): waypoints 0.125 s of travel apart,
acceleration 12 x speed, the Default aim profile, a turn rate of 100,000, waypoints lowered by 0.45 of the bot's
radius so its centre runs on the line, no turn tighter than TURN_R, no two parts of the path closer than CLEAR, and a
beam ticking every 0.01 s for 1 point (6,000 for 60 s on target).
"""
import argparse
import copy
import itertools
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import build
import egypt
import gen_specs as G
import strokes

CATA = G.SCEN + "/Cata IC Pizz Plz LighthawkFPS.sce"
VAI = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\824270\2816723509\VAI 1 Grandmaster TE.sce"
SCALE, EYE_X = 3.15, -6000.0
X_BOT = build.WALL_X - 100.0                         # the bot's plane
FACE_X = egypt.WALL                                  # the board's wall
D_BOT, D_WALL = X_BOT - EYE_X, FACE_X - EYE_X
STEP = 0.05                                          # deg between the points of every line
INF = float("inf")
NAME_FONT, NAME_PX = "segoeuib.ttf", 110             # labels: Segoe UI Bold, thinned to strokes


@dataclass
class Shape:
    """A line on the board in degrees (x across, y up). Labels are (text, anchor); anchor None puts the label as near
    the shape's centre of area as it fits, a point keeps it within ANCHOR_REACH of that point."""
    name: str
    points: list
    closed: bool = True
    labels: list = field(default_factory=list)


# --- geometry -------------------------------------------------------------------------------------------------------
def resample(pts, h=STEP, closed=True):
    src = pts + [pts[0]] if closed else list(pts)
    out, carry = [src[0]], 0.0
    for p0, p1 in zip(src, src[1:]):
        seg = math.dist(p0, p1)
        d = h - carry
        while d <= seg:
            out.append((p0[0] + (p1[0] - p0[0]) * d / seg, p0[1] + (p1[1] - p0[1]) * d / seg))
            d += h
        carry = seg - (d - h)
    if closed:
        return out[:-1] if math.dist(out[-1], out[0]) < h / 2 else out
    if math.dist(out[-1], src[-1]) > 1e-9:
        out.append(src[-1])
    return out


def average(pts, m, closed=True):
    n = len(pts)
    if closed:
        return [(sum(pts[(i + j) % n][0] for j in range(-m, m + 1)) / (2 * m + 1),
                 sum(pts[(i + j) % n][1] for j in range(-m, m + 1)) / (2 * m + 1)) for i in range(n)]
    out = []
    for i in range(n):
        win = pts[max(0, i - m):i + m + 1]
        out.append((sum(p[0] for p in win) / len(win), sum(p[1] for p in win) / len(win)))
    return out


def turn(a, b, c):
    return abs((math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0]) + math.pi)
               % (2 * math.pi) - math.pi)


def ease(pts, radius, gap=4, rounds=60, closed=True):
    """Smooth only the turns tighter than `radius` (and a few samples round them), a little each round."""
    n = len(pts)
    for _ in range(rounds):
        tight = set()
        for i in (range(n) if closed else range(gap, n - gap)):
            a, b, c = pts[i - gap], pts[i], pts[(i + gap) % n]
            t = turn(a, b, c)
            if t > 1e-9 and (math.dist(a, b) + math.dist(b, c)) / 2 / t < radius:
                tight.update((i + j) % n if closed else min(max(i + j, 1), n - 2) for j in range(-2 * gap, 2 * gap + 1))
        if not tight:
            break
        new = pts[:]
        for i in tight:
            new[i] = ((pts[i - 1][0] + 2 * pts[i][0] + pts[(i + 1) % n][0]) / 4,
                      (pts[i - 1][1] + 2 * pts[i][1] + pts[(i + 1) % n][1]) / 4)
        pts = new
    return resample(pts, STEP, closed)


def check(pts, clear, closed=True):
    """(tightest turn radius, closest approach of two parts of the line more than a few samples apart), in deg."""
    n = len(pts)
    tight = 1e9
    for i in (range(n) if closed else range(4, n - 4)):
        a, b, c = pts[i - 4], pts[i], pts[(i + 4) % n]
        t = turn(a, b, c)
        if t > 1e-9:
            tight = min(tight, (math.dist(a, b) + math.dist(b, c)) / 2 / t)
    grid, gap = {}, int(4 * clear / 0.1)
    for i, (y, z) in enumerate(pts):
        grid.setdefault((int(y // clear), int(z // clear)), []).append(i)
    close = 1e9
    for i in range(0, n, 3):
        y, z = pts[i]
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                for j in grid.get((int(y // clear) + a, int(z // clear) + b), []):
                    if (min(abs(i - j), n - abs(i - j)) if closed else abs(i - j)) > gap:
                        close = min(close, math.dist(pts[i], pts[j]))
    return tight, close


def bezier(p0, p1, p2, p3, step):
    n = max(8, int(3 * (math.dist(p0, p1) + math.dist(p1, p2) + math.dist(p2, p3)) / step))
    return [tuple((1 - s) ** 3 * p0[i] + 3 * (1 - s) ** 2 * s * p1[i] + 3 * (1 - s) * s ** 2 * p2[i] + s ** 3 * p3[i]
                  for i in range(2)) for s in (j / n for j in range(1, n))]


def area_centre(loop):
    a2 = cy = cz = 0.0
    for (y1, z1), (y2, z2) in zip(loop, loop[1:] + loop[:1]):
        cr = y1 * z2 - y2 * z1
        a2, cy, cz = a2 + cr, cy + (y1 + y2) * cr, cz + (z1 + z2) * cr
    return cy / (3 * a2), cz / (3 * a2)


def radius3(a, b, c):
    area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
    return math.dist(a, b) * math.dist(b, c) * math.dist(a, c) / (2 * area2) if area2 > 1e-12 else INF


def prepare(shape, turn_r):
    """A shape as the builder wants it: points STEP apart, no turn tighter than turn_r."""
    pts = resample(shape.points, STEP, shape.closed)
    return Shape(shape.name, ease(pts, turn_r, closed=shape.closed), shape.closed, shape.labels)


# --- the tour -------------------------------------------------------------------------------------------------------
def plan_tour(shapes, clear, max_hop=INF, log=print):
    """Order, entries and exits for a tour of all shapes. A closed shape traced in full between an entry and a
    different exit repeats the stretch between them, so the tour repeats the shorter stretch and the order, entries and
    exits are chosen together to make the hops plus the repeats shortest. An open shape is traced end to end. Every
    straight hop keeps `clear` from all lines (except near its ends). Exact over ports every 1 deg for up to 7 shapes
    (the best orders first); a nearest-neighbour order improved by 2-opt beyond that. Returns (order, ports), ports as
    (entry, exit) indices per position in the order."""
    n = len(shapes)
    pts = [s.points for s in shapes]
    CELL, END = 0.1, 0.5
    near_line = set()                                  # grid cells within `clear` of any line
    for line in pts:
        for py, pz in line:
            for i in range(round((py - clear) / CELL) - 1, round((py + clear) / CELL) + 2):
                for j in range(round((pz - clear) / CELL) - 1, round((pz + clear) / CELL) + 2):
                    if math.hypot(i * CELL - py, j * CELL - pz) <= clear:
                        near_line.add((i, j))

    def clear_hop(a, b):
        d = math.dist(a, b)
        steps = int(d / CELL) + 1
        for s in range(1, steps):
            f = s / steps
            if min(f, 1 - f) * d < END:
                continue
            if (round((a[0] + f * (b[0] - a[0])) / CELL), round((a[1] + f * (b[1] - a[1])) / CELL)) in near_line:
                return False
        return True

    memo = {}

    def hop(k, i, j, m):
        if (k, i, j, m) not in memo:
            a, b = pts[k][i], pts[j][m]
            d = math.dist(a, b)
            memo[k, i, j, m] = memo[j, m, k, i] = d if d < max_hop and clear_hop(a, b) else INF
        return memo[k, i, j, m]

    def arc(k, e, x):
        L = len(pts[k])
        if not shapes[k].closed:
            return 0.0 if {e, x} == {0, L - 1} and e != x else INF
        f = (x - e) % L
        return min(f, L - f) * STEP

    coarse = [list(range(0, len(p), 20)) if s.closed else [0, len(p) - 1] for s, p in zip(shapes, pts)]
    if n == 1:
        k = 0
        if shapes[0].closed:
            return [0], [(0, 0)]
        return [0], [(0, len(pts[0]) - 1)]

    def ring_ports(order):
        r = order.index(min(order, key=lambda k: len(coarse[k])))
        ring = order[r:] + order[:r]
        steps = list(range(1, n)) + [0]
        found = (INF, None)
        for x0 in coarse[ring[0]]:
            cost, back = {x0: 0.0}, []
            for s in steps:
                k, kp = ring[s], ring[s - 1]
                ent = {}
                for e in coarse[k]:
                    c, xp = min(((cp + hop(kp, xp, k, e), xp) for xp, cp in cost.items()), default=(INF, None))
                    if c < INF:
                        ent[e] = (c, xp)
                ext = {}
                for x in ([x0] if s == 0 else coarse[k]):
                    c, e = min(((ce + arc(k, e, x), e) for e, (ce, _) in ent.items()), default=(INF, None))
                    if c < INF:
                        ext[x] = (c, e)
                back.append((ent, ext))
                cost = {x: c for x, (c, _) in ext.items()}
            if cost.get(x0, INF) < found[0]:
                ports, x = {}, x0
                for s, (ent, ext) in zip(reversed(steps), reversed(back)):
                    e = ext[x][1]
                    ports[ring[s]] = (e, x)
                    x = ent[e][1]
                found = (cost[x0], ports)
        return (found[0], [found[1][k] for k in order]) if found[1] else (INF, None)

    def tour_cost(order, pe):
        return sum(arc(k, *pe[s]) + hop(k, pe[s][1], order[(s + 1) % n], pe[(s + 1) % n][0])
                   for s, k in enumerate(order))

    def refine(order, pe):
        for _ in range(6):
            before = pe[:]
            for s, k in enumerate(order):
                if not shapes[k].closed:
                    continue
                kp, kn, xp, en, m = order[s - 1], order[(s + 1) % n], pe[s - 1][1], pe[(s + 1) % n][0], len(pts[k])
                c, e, x = min((hop(kp, xp, k, e) + arc(k, e, x) + hop(k, x, kn, en), e, x)
                              for e in ((pe[s][0] + d) % m for d in range(-20, 21))
                              for x in ((pe[s][1] + d) % m for d in range(-20, 21)))
                if c < INF:
                    pe[s] = (e, x)
            if pe == before:
                break
        return pe

    gap_kj = {(k, j): min(math.dist(pts[k][a], pts[j][b]) for a in coarse_all(pts[k]) for b in coarse_all(pts[j]))
              for k in range(n) for j in range(n) if k != j}
    if n == 2:
        orders = [[0, 1]]
    elif n <= 7:
        orders = [[0, *rest] for rest in itertools.permutations(range(1, n)) if rest[0] < rest[-1]]
        orders.sort(key=lambda o: sum(gap_kj[o[s], o[(s + 1) % n]] for s in range(n)))
    else:
        orders = [two_opt(nearest_order(gap_kj, n), gap_kj)]
    best, feasible = (INF, None, None), 0
    for order in orders:                               # the most promising orders first, until ten work
        c, pe = ring_ports(order)
        log(f"  {' > '.join(shapes[k].name for k in order)}: {c:.1f} deg of hops and repeats")
        if c < INF:
            feasible += 1
            if c < best[0]:
                best = (c, order, pe)
            if feasible == 10:
                break
    if best[1] is None:
        return None
    _, order, pe = best
    pe = refine(order, pe)
    repeat = sum(arc(k, *pe[s]) for s, k in enumerate(order))
    log(f"tour {' > '.join(shapes[k].name for k in order)}: hops {tour_cost(order, pe) - repeat:.1f} deg, "
        f"repeated line {repeat:.1f} deg")
    return order, pe


def coarse_all(p):
    return range(0, len(p), 20)


def nearest_order(gap_kj, n):
    order, left = [0], set(range(1, n))
    while left:
        k = min(left, key=lambda j: gap_kj[order[-1], j])
        order.append(k)
        left.remove(k)
    return order


def two_opt(order, gap_kj):
    n = len(order)
    length = lambda o: sum(gap_kj[o[s], o[(s + 1) % n]] for s in range(n))
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                cand = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                if length(cand) < length(order) - 1e-9:
                    order, improved = cand, True
    return order


def tangent(pts, i, back=False):
    a, b = (pts[i - 6], pts[i]) if back else (pts[i], pts[(i + 6) % len(pts)])
    d = math.dist(a, b) or 1.0
    return (b[0] - a[0]) / d, (b[1] - a[1]) / d


def lay_path(shapes, order, pe, log=print):
    """The bot's whole path (deg, STEP apart, starting nearest the board's centre) and the routes between shapes."""
    n = len(shapes)
    pts = [s.points for s in shapes]
    for s, k in enumerate(order):                      # lap each closed shape the way that repeats the shorter stretch
        if not shapes[k].closed:
            continue
        e, x = pe[s]
        m = len(pts[k])
        if 2 * ((x - e) % m) > m:
            pts[k] = pts[k][::-1]
            pe[s] = (m - 1 - e, m - 1 - x)
            shapes[k] = Shape(shapes[k].name, pts[k], True, shapes[k].labels)

    def trav(k, e, x):
        line = pts[k]
        if shapes[k].closed:
            return line[e:] + line[:e] + [line[e]] + (line[e + 1:] + line[:e + 1])[:(x - e) % len(line)]
        return line if e == 0 else line[::-1]

    path, routes, legs = [], [], []
    for s, k in enumerate(order):
        if n == 1 and shapes[k].closed:
            path += pts[k]
            break
        kn = order[(s + 1) % n]
        (e, x), en, xn = pe[s], pe[(s + 1) % n][0], pe[(s + 1) % n][1]
        here, nxt = trav(k, e, x), trav(kn, en, xn)
        path += here
        a, b = here[-1], nxt[0]
        if shapes[k].closed:
            ta = tangent(pts[k], x, back=True)
        else:
            ta = tangent(here, len(here) - 1, back=True)
        tb = tangent(pts[kn], en) if shapes[kn].closed else tangent(nxt, 0)
        for tension in (1.0, 0.6, 0.35, 0.15, 0.0):    # straighter until the curve keeps off every line
            reach = (min(1.5, 0.4 * math.dist(a, b)) + 0.4) * tension
            route = bezier(a, (a[0] + reach * ta[0], a[1] + reach * ta[1]),
                           (b[0] - reach * tb[0], b[1] - reach * tb[1]), b, STEP)
            inner = [p for p in route if min(math.dist(p, a), math.dist(p, b)) > 0.6]
            if min((math.dist(p, q) for p in inner[::2] for line in pts for q in line[::2]), default=99) >= 0.15:
                break
        path += route
        routes.append([a] + route + [b])
        legs.append(f"{shapes[k].name} to {shapes[kn].name}")
    for leg, route in zip(legs, routes):               # the curved route, checked again
        inner = [p for p in route if min(math.dist(p, route[0]), math.dist(p, route[-1])) > 0.6]
        c = min((math.dist(p, q) for p in inner[::2] for line in pts for q in line[::2]), default=99)
        log(f"route {leg}: {sum(math.dist(p, q) for p, q in zip(route, route[1:])):.1f} deg, "
            f"{min(c, 99):.2f} deg from the nearest line" + ("  WARNING" if c < 0.15 else ""))
    path = resample(path, STEP)
    mid = min(range(len(path)), key=lambda i: math.hypot(*path[i]))
    path = path[mid:] + path[:mid]                     # the tour starts nearest the board's centre
    first = order.index(min(order, key=lambda k: min(math.dist(path[0], q) for q in pts[k])))
    tour_names = [shapes[k].name for k in order[first:] + order[:first]]
    return path, routes, tour_names


# --- labels ---------------------------------------------------------------------------------------------------------
def name_strokes(text):
    """The text as straight strokes ((x, y), (x, y)) in pixels (y down), and the text's width and height in pixels:
    drawn in NAME_FONT, thinned to a skeleton, traced, smoothed and simplified (strokes.py)."""
    font = ImageFont.truetype(NAME_FONT, NAME_PX)
    l, tp, r, b = font.getbbox(text)
    img = Image.new("L", (r - l + 12, b - tp + 12), 0)
    ImageDraw.Draw(img).text((6 - l, 6 - tp), text, font=font, fill=255)
    px = img.load()
    rows = [[1 if px[x, y] > 110 else 0 for x in range(img.size[0])] for y in range(img.size[1])]
    segs = []
    # dots (the i's): small blobs the tracer drops; each becomes a short round stroke at its centre
    seen = set()
    for y0, row in enumerate(rows):
        for x0, v in enumerate(row):
            if v and (x0, y0) not in seen:
                comp, stack = [], [(x0, y0)]
                seen.add((x0, y0))
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= ny < len(rows) and 0 <= nx < len(row) and rows[ny][nx] and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
                if len(comp) < (0.18 * NAME_PX) ** 2:
                    cx, cy = sum(p[0] for p in comp) / len(comp), sum(p[1] for p in comp) / len(comp)
                    segs.append(((cx - 1.5, cy), (cx + 1.5, cy)))
    for path in strokes.trace(strokes.thin(rows)):
        pts = strokes.rdp(strokes.smooth(path, 2), 1.5)
        segs += [((a[1], a[0]), (c[1], c[0])) for a, c in zip(pts, pts[1:])]
    return segs, img.size[0], img.size[1]


def layouts(text):
    """(strokes in pixels, width, height): the name on one line, and a two-word name on two centred lines."""
    out = [name_strokes(text)]
    if " " in text:
        parts = [name_strokes(w) for w in text.split(" ", 1)]
        gap = 0.2 * NAME_PX - 12                      # each image has 6 px of padding top and bottom
        w, y, segs = max(p[1] for p in parts), 0.0, []
        for strokes_, pw, ph in parts:
            segs += [((a[0] + (w - pw) / 2, a[1] + y), (c[0] + (w - pw) / 2, c[1] + y)) for a, c in strokes_]
            y += ph + gap
        out.append((segs, w, y - gap))
    return out


MARGINS, ANCHOR_REACH, CELL_N = (0.9, 0.75, 0.6, 0.45, 0.3), 3.0, 0.25


def room_for(x, z, w, h, pts, floor, margin=MARGINS[-1]):
    """The largest scale (deg per pixel) at which a w x h label centred on (x, z) keeps margin from every point;
    stops early once below floor."""
    best = INF
    for px, pz in pts:
        k = max(2 * (abs(px - x) - margin) / w, 2 * (abs(pz - z) - margin) / h)
        if k < best:
            best = k
            if best <= floor:
                return best
    return best


def place_labels(shapes, log=print):
    """Each label as close as it can to its shape's centre of area (or, within ANCHOR_REACH, to its anchor) while
    keeping the widest clearance of MARGINS from every line; lines 0.9 deg tall; where it fits nowhere, where the
    largest copy fits, drawn smaller. Returns the labels' strokes on the board (deg)."""
    labelled = [s for s in shapes if s.closed and s.labels]
    if not labelled:
        return []
    kp_cap = 0.9 / max(name_strokes(text)[2] for s in labelled for text, _ in s.labels)
    near_pts = [p for s in shapes for p in s.points[::2]]
    placed_all = []
    for shape in labelled:
        loop = shape.points
        ys, zs = [p[0] for p in loop], [p[1] for p in loop]
        y0, z0 = min(ys), min(zs)
        mask = Image.new("L", (int((max(ys) - y0) / 0.1) + 3, int((max(zs) - z0) / 0.1) + 3), 0)
        ImageDraw.Draw(mask).polygon([((p[0] - y0) / 0.1 + 1, (p[1] - z0) / 0.1 + 1) for p in loop], fill=255)

        def inside(y, z):
            i, j = int((y - y0) / 0.1 + 1), int((z - z0) / 0.1 + 1)
            return 0 <= i < mask.size[0] and 0 <= j < mask.size[1] and mask.getpixel((i, j)) > 0
        pts = [p for p in near_pts if y0 - 10 <= p[0] <= max(ys) + 10 and z0 - 10 <= p[1] <= max(zs) + 10]
        grid = [(y0 + i * CELL_N, z0 + j * CELL_N) for i in range(int((max(ys) - y0) / CELL_N) + 1)
                for j in range(int((max(zs) - z0) / CELL_N) + 1)]
        grid = [g for g in grid if inside(*g)]
        for text, anchor in shape.labels:
            goal = area_centre(loop) if anchor is None else anchor
            near_fit, roomiest = None, (0.0, None)
            cands = sorted((g for g in grid if anchor is None or math.dist(g, goal) <= ANCHOR_REACH),
                           key=lambda g: math.dist(g, goal))
            for margin in MARGINS:
                for lay in layouts(text):
                    _, w, h = lay
                    for y, z in cands:
                        if near_fit and math.dist((y, z), goal) >= near_fit[0]:
                            break
                        if room_for(y, z, w, h, pts, kp_cap, margin) > kp_cap:
                            near_fit = (math.dist((y, z), goal), lay, y, z)
                            break
                if near_fit:
                    break
            if near_fit:                               # refine towards the goal, 0.05 deg steps
                _, lay, y, z = near_fit
                _, w, h = lay
                fine = [(y + i * 0.05, z + j * 0.05) for i in range(-5, 6) for j in range(-5, 6)]
                y, z = min((g for g in fine if inside(*g) and room_for(*g, w, h, pts, kp_cap, margin) > kp_cap),
                           key=lambda g: math.dist(g, goal))
                k = room_for(y, z, w, h, pts, 0.0)
            else:
                for lay in layouts(text):
                    for y, z in grid:
                        kk = room_for(y, z, lay[1], lay[2], pts, roomiest[0])
                        if kk > roomiest[0]:
                            roomiest = (kk, (lay, y, z))
                if roomiest[1] is None:
                    log(f"{text}: no room inside {shape.name}; left out")
                    continue
                k, (lay, y, z) = roomiest
            segs, w, h = lay
            kp = min(k, kp_cap)
            log(f"{text}: {'two lines' if h > 1.5 * name_strokes(text)[2] else 'one line'} at "
                f"{y:.1f}, {z:.1f} deg ({math.dist((y, z), goal):.1f} from the goal), lines {0.9 * kp / kp_cap:.2f} "
                f"deg tall, " + (f"{margin} deg clear of the line" if near_fit else f"room for {k / kp_cap:.1f} x that"))
            top = (y - w * kp / 2, z + h * kp / 2)
            placed_all += [((top[0] + a[0] * kp, top[1] - a[1] * kp), (top[0] + c[0] * kp, top[1] - c[1] * kp))
                           for a, c in segs]
    return placed_all


# --- carving --------------------------------------------------------------------------------------------------------
CHALK_D = 2.0                                          # the chalk's lines stand this far proud of the board


def ribbon(scene, slot, pts, face_x, width, closed=False):
    """A flat line along pts ((y, z) wall points), width wide, facing the player: two vertices a point shared by the
    triangles on both sides (mitred joins, the mitre capped at twice the half-width), two triangles a segment. Open
    ends run on half a width."""
    pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
    if closed and len(pts) > 2 and math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    if len(pts) < 2:
        return
    hw, n = width / 2, len(pts)
    unit = lambda v: (v[0] / (math.hypot(*v) or 1.0), v[1] / (math.hypot(*v) or 1.0))
    dirs = [unit((pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1])) for i in range(n)]
    if not closed:
        dirs[-1] = dirs[-2]
        pts = ([(pts[0][0] - dirs[0][0] * hw, pts[0][1] - dirs[0][1] * hw)] + pts[1:-1]
               + [(pts[-1][0] + dirs[-1][0] * hw, pts[-1][1] + dirs[-1][1] * hw)])
    sec = scene.mesh.setdefault(slot, {"v": [], "i": []})
    base, x = len(sec["v"]), face_x - CHALK_D
    for i, (py, pz) in enumerate(pts):
        d1 = dirs[i]
        d0 = dirs[i - 1] if (closed or i > 0) else d1
        n0, n1 = (-d0[1], d0[0]), (-d1[1], d1[0])
        m = unit((n0[0] + n1[0], n0[1] + n1[1])) if math.hypot(n0[0] + n1[0], n0[1] + n1[1]) > 1e-6 else n1
        k = hw / max(m[0] * n1[0] + m[1] * n1[1], 0.5)
        for sgn in (1, -1):
            y, z = py + sgn * k * m[0], pz + sgn * k * m[1]
            sec["v"].append(((x, y, z), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (y / egypt.UV_UNIT, z / egypt.UV_UNIT)))
    for i in range(n if closed else n - 1):
        j = (i + 1) % n
        l0, r0, l1, r1 = base + 2 * i, base + 2 * i + 1, base + 2 * j, base + 2 * j + 1
        for tri in ((l0, r0, r1), (l0, r1, l1)):
            (_, ay, az), (_, by, bz), (_, cy, cz) = (sec["v"][v][0] for v in tri)
            if (by - ay) * (cz - az) - (bz - az) * (cy - ay) < 0:    # (B - A) x (C - A) must point +x, against
                tri = (tri[0], tri[2], tri[1])                       # the face normal (-x): the installed winding
            sec["i"] += list(tri)


def chains(segs):
    """Join segments that meet end to start into polylines."""
    out = []
    for a_, c_ in segs:
        if out and out[-1][-1] == a_:
            out[-1].append(c_)
        else:
            out.append([a_, c_])
    return out


# --- the scenario ---------------------------------------------------------------------------------------------------
TINTS = {(0, "wall"): "e6dcc4ff", (0, "ground"): "8a5a36ff", (0, "ceiling"): "f2f0eaff", (0, "ramp"): "a8773fff",
         (1, "wall"): "3d6f50ff", (1, "ground"): "ecece4ff", (1, "ceiling"): "5c3b22ff", (1, "ramp"): "3a3a3aff"}
WALLS, FLOOR, CEIL, WOOD = (0, "wall"), (0, "ground"), (0, "ceiling"), (0, "ramp")
BOARD, CHALK, FRAME, DARK = (1, "wall"), (1, "ground"), (1, "ceiling"), (1, "ramp")


def lecture_hall(s, bw, bh):
    """The room: walls, a board bw x bh (map units, half sizes) with its frame and ledge, the stepped floor with its
    desks, and the lecturer's desk. Tiers are slabs (the eye sees only their tops); the outermost desk column is left
    out (v11, user: "thin it a bit")."""
    rw, floor_z, ceil_z, back_x = bw + 900, -bh - 700, bh + 700, EYE_X - 2600
    t = 40.0
    s.box(FACE_X, FACE_X + t, -rw, rw, floor_z, ceil_z, WALLS)
    s.box(back_x - t, back_x, -rw, rw, floor_z, ceil_z + 1400, WALLS)
    s.box(back_x, FACE_X, -rw - t, -rw, floor_z, ceil_z + 1400, WALLS)
    s.box(back_x, FACE_X, rw, rw + t, floor_z, ceil_z + 1400, WALLS)
    s.box(back_x, FACE_X, -rw, rw, ceil_z + 1400, ceil_z + 1400 + t, CEIL)
    s.box(FACE_X - 6, FACE_X, -bw - 60, bw + 60, -bh - 60, bh + 60, BOARD)
    for y0, y1, z0, z1 in ((-bw - 90, bw + 90, bh + 60, bh + 95), (-bw - 90, bw + 90, -bh - 95, -bh - 60),
                           (-bw - 90, -bw - 60, -bh - 60, bh + 60), (bw + 60, bw + 90, -bh - 60, bh + 60)):
        s.box(FACE_X - 18, FACE_X, y0, y1, z0, z1, FRAME)
    s.box(FACE_X - 45, FACE_X - 6, -bw + 150, bw - 150, -bh - 120, -bh - 95, FRAME)
    x, z = FACE_X, floor_z
    tiers = []
    while x > back_x:                                  # tiers rising from the board to the back, a row of desks on each
        x0 = max(back_x, x - 520)
        s.box(x0, x, -rw, rw, z - t, z, FLOOR)
        tiers.append((x0, x, z))
        x, z = x0, z + 170
    for x0, x1, zt in tiers[2:]:
        for yc in [s_ * (350 + 700 * j) for j in range(int((rw - 750) // 700)) for s_ in (-1, 1)]:
            if abs(yc) < 400 and x0 < EYE_X < x1 + 200:
                continue                               # leave the player's own place clear
            top = zt + 230
            if top > -bh * (FACE_X - x1) / D_WALL * 1.0 - 60:     # never above the line to the board's bottom edge
                continue
            s.box(x0 + 120, x0 + 400, yc - 260, yc + 260, top - 25, top, WOOD)
            s.box(x0 + 140, x0 + 380, yc - 240, yc + 240, zt, top - 25, DARK)
    s.box(FACE_X - 900, FACE_X - 400, -700, 700, floor_z, floor_z + 280, WOOD)          # the lecturer's desk


def base_scenario(name, description, run_s, out, *, speed=5.0, r_bot=0.4, tags="Tracking, Smooth, Bassel, Bakr",
                  top=None, drop=()):
    """The scenario without its room, lines and path: every profile (the tracer bot, its dodge profile, the LG beam),
    the base map with the frame look's blocks removed and the materials tinted. Returns (path, head, map, the bot's
    spawn volumes, a template block, the bot's radius in world units, how far it rides above its waypoints)."""
    v = math.radians(speed) * D_BOT * SCALE
    acc = v * 12.0
    r_w = D_BOT * SCALE * math.tan(math.radians(r_bot))
    ride = 0.45 * r_w / SCALE                          # a flyer rides this far above its waypoints (map units)
    area = {"y": G.CY, "z": G.CZ, "size_y": G.EYE * math.tan(math.radians(26.6)) / 100,
            "size_z": G.EYE * math.tan(math.radians(18.6)) / 100}
    spec = dict(
        id="40", scenario_name=name, series="test", arena="frame", nodes=["sc-flick"],
        description=description,
        scenario_overrides=G.kv(Timelimit=f"{math.ceil(run_s) + 1:.1f}", ScorePerKill="0.0", ScorePerDamage="1.0",
                                ScoreLossPerMiss="0.0", **dict(G.COMMON2, SearchTags=tags, **(top or {}))),
        added_bots=["tracer"], bot_team=2,
        sections=[
            {"section_type": "Weapon Profile", "copy_from_file": CATA, "copy_section_name": "LG", "new_name": "LG",
             # the conventional tracking score: 6,000 for 60 s on target, 100 ticks a second worth 1
             "overrides": G.kv(DamagePerShot="1.0", TimeBetweenShots="0.01")},
            G.player(WeaponProfileNames="LG;;;;;;;"),
            G.char("tracer", r_w, MaxHealth="1000000.0", MaxSpeed=f"{v:.1f}", Acceleration=f"{acc:.1f}",
                   BrakingDeceleration="0.0", Friction="0.0", BrakingFrictionFactor="0.0", IsFlyer="true",
                   FlightObeysPitch="true", Gravity="0.0", AirControl="1.0", FlightVelocityUp=f"{v:.1f}",
                   FlightVelocityDown=f"{v:.1f}", FlightAccelUp=f"{acc:.1f}", FlightAccelDown=f"{acc:.1f}",
                   CanCrouch="false", BlockedSpawnRadius="0.0",
                   SpawnOffsetMin="X=0.000 Y=0.000 Z=0.000", SpawnOffsetMax="X=0.000 Y=0.000 Z=0.000"),
            {"section_type": "Bot Profile", "copy_from_file": G.BASE, "copy_section_name": "target",
             "new_name": "tracer",
             "overrides": G.kv(CharacterProfile="tracer", NoDodging="false", NoAiming="false",
                               DodgeProfileNames="follow", DodgeProfileWeights="1.0", DodgeProfileMinChangeTime="60.0",
                               DodgeProfileMaxChangeTime="60.0", RandomizeDodgeProfiles="false")},
            {"section_type": "Dodge Profile", "copy_from_file": VAI, "copy_section_name": "VAI 1 GM",
             "new_name": "follow",
             "overrides": G.kv(WaypointLogic="FollowAimAtWaypoint", WaypointTurnRate="100000.0",
                               ToggleLeftRight="false", ToggleForwardBack="false", JumpFrequency="0.0",
                               DamageReactionChangesDirection="false", BlockedMovementPercent="0.5",
                               BlockedMovementReactionMin="0.1", BlockedMovementReactionMax="0.1")},
        ],
        spawn_volumes=[dict(area, permitted_profile="tracer")], drop_sections=G.DROP_TARGET + list(drop))
    Path(out).mkdir(parents=True, exist_ok=True)
    path_out, errors, warns = build.build(copy.deepcopy(spec), out)
    if errors:
        sys.exit(f"{name}: {errors}")
    raw = Path(path_out).read_bytes().decode("utf-8")
    head, body = raw.split("[Map Data]", 1)
    m = json.loads(body)
    vols = [o for o in m["objects"] if o.get("name") == "SpawnVolume"
            and any(q["name"] == "TeamMask" and q["value"] == 2 for q in o["properties"])]
    template = copy.deepcopy(next(o for o in m["objects"] if o.get("type") == "brush" and "materialSets" in o
                                  and "procedural" not in o))
    m["objects"] = [o for o in m["objects"] if o not in vols and not (o.get("type") == "brush"
                    and -3400 <= float(o["location"].split(",")[0]) <= -2800)]    # the frame look's blocks go
    for (grp, slot), tint in TINTS.items():
        m["materialSets"][grp][slot]["properties"][0]["value"] = tint
    return path_out, head, m, vols, template, r_w, ride


def build_track(shapes, name, description="", out="out", *, speed=5.0, efficiency=0.91, r_bot=0.4, box=(41.0, 20.0),
                turn_r=0.25, clear=0.3, line_w=12.0, name_w=7.0, dash=0.5, tags="Tracking, Smooth, Bassel, Bakr",
                top=None, drop=(), prepared=False, max_hop=INF, preview="test_out", log=print):
    """Build the scenario; returns its path. shapes are Shape objects in board degrees (x across, y up, the board
    spanning +-box). prepared=True skips resampling and easing (the shapes already meet STEP and turn_r). max_hop caps
    a straight hop between shapes (deg); a smaller cap makes the tour search faster."""
    shapes = [s if prepared else prepare(s, turn_r) for s in shapes]
    for s in shapes:
        tight, close = check(s.points, clear, s.closed)
        if close < clear:
            log(f"WARNING {s.name}: two parts of the line only {close:.2f} deg apart (the bot may cut across)")
    for a in range(len(shapes)):
        for b in range(a + 1, len(shapes)):
            g = min(math.dist(p, q) for p in shapes[a].points[::4] for q in shapes[b].points[::4])
            if g < clear:
                log(f"WARNING {shapes[a].name} and {shapes[b].name} only {g:.2f} deg apart")
    for c in (clear, clear / 2, 0.0):                 # hops keep clear of the lines; relaxed only if nothing else works
        tour = plan_tour(shapes, c, max_hop, log)
        if tour:
            break
        log(f"WARNING no tour whose hops keep {c:.2f} deg clear of the lines; trying less")
    if not tour:
        sys.exit("no tour found")
    order, pe = tour
    path, routes, tour_names = lay_path(shapes, order, pe, log)
    total = sum(math.dist(a, b) for a, b in zip(path, path[1:] + path[:1]))
    run_s = total / (speed * efficiency)
    log(f"path {total:.0f} deg: {run_s:.1f} s at {speed} deg/s ({efficiency:.0%} of it)")
    r_min, i_min = min((radius3(path[i - 5], path[i], path[(i + 5) % len(path)]), i) for i in range(len(path)))
    log(f"tightest turn on the whole path: radius {r_min:.2f} deg at {path[i_min][0]:.1f}, {path[i_min][1]:.1f}")

    path_out, head, m, vols, template, r_w, ride = base_scenario(
        name, description.replace("{tour}", ", ".join(tour_names)), run_s, out, speed=speed, r_bot=r_bot, tags=tags,
        top=top, drop=drop)
    wall_pt = lambda p: (D_WALL * math.tan(math.radians(p[0])), D_WALL * math.tan(math.radians(p[1])))
    bw, bh = D_WALL * math.tan(math.radians(box[0])), D_WALL * math.tan(math.radians(box[1]))

    saved = egypt.ROUND_STROKES
    egypt.ROUND_STROKES = True
    s = egypt.Scene(template)
    s.body_slot, s.outline_slot = CHALK, CHALK
    s.section = "lecture hall"
    lecture_hall(s, bw, bh)
    s.section = "board"
    s.begin_mesh()
    for shape in shapes:
        wall = [wall_pt(p) for p in shape.points]
        if shape.closed:
            half = len(wall) // 2
            line = strokes.rdp(wall[:half + 1], 1.5)[:-1] + strokes.rdp(wall[half:] + wall[:1], 1.5)
        else:
            line = strokes.rdp(wall, 1.5)
        ribbon(s, CHALK, line, FACE_X - 6, line_w, closed=shape.closed)
    for route in routes:                               # dashes: one simplified ribbon per dash
        dense = [route[0]]
        for p, q in zip(route, route[1:]):
            steps = max(1, int(math.dist(p, q) / 0.05))
            dense += [(p[0] + (q[0] - p[0]) * i / steps, p[1] + (q[1] - p[1]) * i / steps) for i in range(1, steps + 1)]
        run, dash_pts = 0.0, []
        for p, q in zip(dense, dense[1:]):
            if int(run / dash) % 2 == 0:
                dash_pts.append(p)
            elif dash_pts:
                ribbon(s, CHALK, strokes.rdp([wall_pt(v) for v in dash_pts + [p]], 1.0), FACE_X - 6, line_w * 0.8)
                dash_pts = []
            run += math.dist(p, q)
        if dash_pts:
            ribbon(s, CHALK, strokes.rdp([wall_pt(v) for v in dash_pts], 1.0), FACE_X - 6, line_w * 0.8)
    name_segs = place_labels(shapes, log)
    for chain in chains(name_segs):
        ribbon(s, CHALK, [wall_pt(p) for p in chain], FACE_X - 6, name_w)
    s.finish()
    egypt.ROUND_STROKES = saved
    m["objects"] += s.boxes

    # the bot's waypoints: the path in the bot's plane, 0.125 s apart, lowered so its centre runs on the line
    plane = [(math.tan(math.radians(a)), math.tan(math.radians(b))) for a, b in path]
    step = math.radians(speed) * 0.125
    wps, carry = [plane[0]], 0.0
    for p0, p1 in zip(plane + plane[:1], plane[1:] + plane[:1]):
        seg = math.dist(p0, p1)
        dd = step - carry
        while dd <= seg:
            wps.append((p0[0] + (p1[0] - p0[0]) * dd / seg, p0[1] + (p1[1] - p0[1]) * dd / seg))
            dd += step
        carry = seg - (dd - step)
    if math.dist(wps[-1], wps[0]) < step / 2:
        wps.pop()
    names = [f"w{i}" for i in range(len(wps))]
    for nm, (u, w_) in zip(names, wps):
        m["objects"].append({"location": f"{X_BOT:.6f}, {D_BOT * u:.6f}, {D_BOT * w_ - ride:.6f}", "name": "Waypoint",
                             "properties": [{"name": "Name", "value": nm}, {"name": "BotPauseTimeMin", "value": 0.0},
                                            {"name": "BotPauseTimeMax", "value": 0.0}],
                             "rotation": "0.000000, 0.000000, 0.000000", "scale": "0.100000, 0.100000, 0.100000",
                             "type": "gameObject"})
    sp = copy.deepcopy(vols[0])
    sp["name"] = "SpawnPoint"
    u0, v0 = wps[0]
    sp["location"] = f"{X_BOT:.6f}, {D_BOT * u0:.6f}, {D_BOT * v0 - 2 * r_w / SCALE:.6f}"
    sp["scale"] = "0.100000, 0.100000, 0.100000"
    for q in sp["properties"]:
        q["value"] = {"Path": ",".join(names[1:] + names[:1]), "LoopingPath": True,
                      "PermittedCharacterProfiles": "tracer"}.get(q["name"], q["value"])
    m["objects"].append(sp)
    player = next(o for o in m["objects"] if o.get("name") == "SpawnPoint"
                  and any(q["name"] == "TeamMask" and q["value"] == 1 for q in o["properties"]))
    player["rotation"] = (f"0.000000, {math.degrees(math.atan(v0 / math.sqrt(1 + u0 * u0))):.6f}, "
                          f"{math.degrees(math.atan(u0)):.6f}")        # the view starts on the bot
    build.slim_meshes(m, float(next(l.split("=", 1)[1] for l in head.splitlines() if l.startswith("MapScale="))))
    nl = "\r\n" if "\r\n" in head else "\n"
    Path(path_out).write_bytes((head + "[Map Data]" + nl + build.dump_map(m).replace("\n", nl)).encode("utf-8"))
    log(f"{path_out}: {len(wps)} waypoints; {sum(1 for o in s.boxes if 'procedural' not in o)} hall blocks; "
        f"{len(m['objects'])} map objects; {Path(path_out).stat().st_size / 1e6:.2f} MB")

    if preview:                                        # a picture of the board: lines solid, routes thin, red = start
        f = 20.0
        img = Image.new("RGB", (int(2 * box[0] * f) + 40, int(2 * box[1] * f) + 60), (36, 64, 46))
        d = ImageDraw.Draw(img)
        P = lambda p: (20 + (p[0] + box[0]) * f, 40 + (box[1] - p[1]) * f)
        for shape in shapes:
            d.line([P(p) for p in shape.points + (shape.points[:1] if shape.closed else [])], fill=(236, 236, 228),
                   width=2)
        for route in routes:
            d.line([P(p) for p in route], fill=(180, 180, 170), width=1)
        for a, c in name_segs:
            d.line([P(a), P(c)], fill=(236, 236, 228), width=2)
        d.ellipse([P(path[0])[0] - 5, P(path[0])[1] - 5, P(path[0])[0] + 5, P(path[0])[1] + 5], fill=(220, 60, 40))
        d.text((20, 10), f"{name}: the board (lines solid, routes thin; red = start)", fill=(230, 230, 230))
        Path(preview).mkdir(parents=True, exist_ok=True)
        img.save(Path(preview) / f"{name} board.png")
    return Path(path_out)


# --- SVG ------------------------------------------------------------------------------------------------------------
def _matrix(transform):
    """An SVG transform attribute as a 2D affine matrix (a, b, c, d, e, f)."""
    mtx = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    for op, args in re.findall(r"(matrix|translate|scale|rotate|skewX|skewY)\s*\(([^)]*)\)", transform or ""):
        v = [float(t) for t in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", args)]
        if op == "matrix":
            n = tuple(v[:6])
        elif op == "translate":
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0.0)
        elif op == "scale":
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif op == "rotate":
            a = math.radians(v[0])
            cx, cy = (v[1], v[2]) if len(v) > 2 else (0.0, 0.0)
            c, s = math.cos(a), math.sin(a)
            n = (c, s, -s, c, cx - c * cx + s * cy, cy - s * cx - c * cy)
        elif op == "skewX":
            n = (1, 0, math.tan(math.radians(v[0])), 1, 0, 0)
        else:
            n = (1, math.tan(math.radians(v[0])), 0, 1, 0, 0)
        mtx = _mul(mtx, n)
    return mtx


def _mul(m, n):
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def _apply(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def _arc(p0, rx, ry, phi, large, sweep, p1, n):
    """Points along an SVG elliptical arc (endpoint parameterisation, SVG spec F.6)."""
    if rx == 0 or ry == 0:
        return [p1]
    phi = math.radians(phi)
    cp, sp = math.cos(phi), math.sin(phi)
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    rx, ry = abs(rx), abs(ry)
    lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    co = math.sqrt(max(num, 0.0) / (rx * rx * y1 * y1 + ry * ry * x1 * x1)) * (-1 if large == sweep else 1)
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx, cy = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2, sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2
    ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    out = []
    for i in range(1, n + 1):
        t = t1 + dt * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        out.append((cp * x - sp * y + cx, sp * x + cp * y + cy))
    return out


def _path(d, n=24):
    """An SVG path's subpaths as ([points], closed)."""
    toks = re.findall(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d)
    out, cur, start, pos = [], [], (0.0, 0.0), (0.0, 0.0)
    last_c, last_q, cmd, i = None, None, None, 0

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def flush(closed):
        nonlocal cur
        if len(cur) > 1:
            out.append((cur, closed))
        cur = []
    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                flush(True)
                pos = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = pos if rel else (0.0, 0.0)
        if c == "M":
            flush(False)
            pos = (ox + num(), oy + num())
            start, cur = pos, [pos]
            cmd = "l" if rel else "L"
        elif c in "LHV":
            if c == "L":
                pos = (ox + num(), oy + num())
            elif c == "H":
                pos = ((pos[0] if rel else 0.0) + num(), pos[1])
            else:
                pos = (pos[0], (pos[1] if rel else 0.0) + num())
            cur.append(pos)
        elif c in "CS":
            if c == "C":
                c1 = (ox + num(), oy + num())
            else:
                c1 = (2 * pos[0] - last_c[0], 2 * pos[1] - last_c[1]) if last_c else pos
            c2 = (ox + num(), oy + num())
            p3 = (ox + num(), oy + num())
            cur += [tuple((1 - t) ** 3 * pos[k] + 3 * (1 - t) ** 2 * t * c1[k] + 3 * (1 - t) * t * t * c2[k]
                          + t ** 3 * p3[k] for k in range(2)) for t in (j / n for j in range(1, n + 1))]
            pos, last_c = p3, c2
        elif c in "QT":
            if c == "Q":
                q1 = (ox + num(), oy + num())
            else:
                q1 = (2 * pos[0] - last_q[0], 2 * pos[1] - last_q[1]) if last_q else pos
            p2 = (ox + num(), oy + num())
            cur += [tuple((1 - t) ** 2 * pos[k] + 2 * (1 - t) * t * q1[k] + t * t * p2[k] for k in range(2))
                    for t in (j / n for j in range(1, n + 1))]
            pos, last_q = p2, q1
        elif c == "A":
            rx, ry, phi, large, sweep = num(), num(), num(), num(), num()
            p1 = (ox + num(), oy + num())
            cur += _arc(pos, rx, ry, phi, int(large), int(sweep), p1, n)
            pos = p1
        if c not in "CS":
            last_c = None
        if c not in "QT":
            last_q = None
    flush(False)
    return out


def svg_lines(file):
    """Every line of an SVG file as ([points], closed) in its own units (y down): paths (all commands), polylines,
    polygons, lines, rectangles, circles and ellipses, with their transforms."""
    root = ET.parse(file).getroot()
    out = []

    def walk(el, mtx):
        mtx = _mul(mtx, _matrix(el.get("transform")))
        tag = el.tag.split("}")[-1]
        f = lambda k, d=0.0: float(re.sub(r"[a-z%]+$", "", el.get(k, str(d))) or d)
        lines = []
        if tag == "path" and el.get("d"):
            lines = _path(el.get("d"))
        elif tag in ("polyline", "polygon"):
            v = [float(t) for t in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", el.get("points", ""))]
            lines = [(list(zip(v[::2], v[1::2])), tag == "polygon")]
        elif tag == "line":
            lines = [([(f("x1"), f("y1")), (f("x2"), f("y2"))], False)]
        elif tag == "rect":
            x, y, w, h = f("x"), f("y"), f("width"), f("height")
            lines = [([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], True)]
        elif tag in ("circle", "ellipse"):
            cx, cy = f("cx"), f("cy")
            rx, ry = (f("r"), f("r")) if tag == "circle" else (f("rx"), f("ry"))
            lines = [([(cx + rx * math.cos(2 * math.pi * i / 96), cy + ry * math.sin(2 * math.pi * i / 96))
                       for i in range(96)], True)]
        for pts, closed in lines:
            out.append(([_apply(mtx, p) for p in pts], closed))
        for child in el:
            if child.tag.split("}")[-1] not in ("defs", "clipPath", "mask", "symbol", "title", "desc"):
                walk(child, mtx)
    walk(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return out


def fit(lines, box, margin=1.5, min_len=1.0):
    """Lines in any units (y down) scaled to fit the board (deg, y up), centred; lines shorter than min_len deg after
    scaling are dropped (specks and dots the bot could not follow)."""
    xs = [p[0] for pts, _ in lines for p in pts]
    ys = [p[1] for pts, _ in lines for p in pts]
    w, h = max(xs) - min(xs) or 1.0, max(ys) - min(ys) or 1.0
    k = min((2 * box[0] - 2 * margin) / w, (2 * box[1] - 2 * margin) / h)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    shapes = []
    for i, (pts, closed) in enumerate(lines):
        q = [((x - cx) * k, (cy - y) * k) for x, y in pts]
        if closed and math.dist(q[0], q[-1]) < 1e-6:
            q = q[:-1]
        length = sum(math.dist(a, b) for a, b in zip(q, q[1:] + (q[:1] if closed else [])))
        if length >= min_len and len(q) >= 2:
            shapes.append(Shape(f"line {i + 1}", q, closed))
    return shapes


def main():
    ap = argparse.ArgumentParser(description="Build a tracking scenario from an SVG: the bot traces every line.")
    ap.add_argument("svg")
    ap.add_argument("name")
    ap.add_argument("--speed", type=float, default=5.0, help="deg/s (default 5)")
    ap.add_argument("--out", default="out")
    ap.add_argument("--description", default="Smooth tracking along a path you can see.[nl]The bot traces the "
                    "drawing on the chalkboard: {tour}. Hold fire: every second on the bot scores 100.")
    a = ap.parse_args()
    box = (41.0, 20.0)
    shapes = fit(svg_lines(a.svg), box)
    print(f"{len(shapes)} lines from {a.svg}")
    build_track(shapes, a.name, a.description, a.out, speed=a.speed, box=box)


if __name__ == "__main__":
    main()
