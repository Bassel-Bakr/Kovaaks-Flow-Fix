"""Scratch (run from D:/Projects/flowfix with PYTHONPATH=.;test_out/courtyard): the FINAL courtyard design,
merged from the three concepts (lean, atmos, authentic). Geometry only; final_render.py draws it, final_check.py
exports it into copies of the 13 window builds for check_scene.py.

Coordinates: map units. x from the player to the target wall, +y screen right, +z up. Eye at (-6000, 0, 0).
Per layout: F = the window's lowest point (court floor), yc = window axis, stone and plinth edges from the build.
The skyline heights (palace top, crowns, tower, pyramids) are ABSOLUTE, so the skyline sits at the same screen
height in all 13 scenarios; the floor, stylobates and column bases follow F.
"""
import json
import math
import os

import authentic_geo as A
from authentic_geo import poly, box_polys, frustum, add, mul, sub

EYE_X = -6000.0
TANH, TANV = A.TANH, A.TANV
HERE = os.path.dirname(os.path.abspath(__file__))
WINDOWS = r"D:\Projects\flowfix\out"      # the current builds (test_out/egypt_window_all holds a stale Pathing)

# ---- palette (8 slots) ---------------------------------------------------------------------------------
PALACE, LAPIS, LIME, OCHRE = (0, "wall"), (0, "ground"), (0, "ceiling"), (0, "ramp")
BACK, NAVY, PAVE, GOLD = (1, "wall"), (1, "ground"), (1, "ceiling"), (1, "ramp")
PAL = {PALACE: ("5d6066", 0.25),   # RETINT: was dark umber 2b1d12 / 0.2 (sign outlines); now palace grey + outlines
       LAPIS: ("1e4c9a", 0.35),    # unchanged: headdress
       LIME: ("eadbb6", 0.35),     # unchanged: limestone (ConcretePoured)
       OCHRE: ("9a3f22", 0.30),    # unchanged: red ochre
       BACK: ("c8c8c8", 0.40),     # unchanged: target backdrop, nothing new uses it
       NAVY: ("0f2a4d", 0.30),     # unchanged: signs, lions, outlines; + pool water
       PAVE: ("77736b", 0.30),     # FREE slot repainted: court paving only
       GOLD: ("d4a02a", 0.50)}     # unchanged: face, sill strip; + column bands and capitals

# ---- fixed numbers ---------------------------------------------------------------------------------------
Z_TOP = 185.0            # palace wall top and portico roof top (absolute)
ROOF_H = 150.0           # portico roof / architrave depth
XW0, XW1 = -2820.0, -2720.0   # palace front wall: face 80 behind the backdrop plane (-2900)
XP = -3160.0             # portico front (architrave face)
XC = -3085.0             # column axis
XS = -3220.0             # stylobate front
Y_TW = 3050.0            # tower inner face at its base, from the axis
BATTER = 70.0            # tower batter, in x (front) and y (inner face)
XT = -3230.0             # tower front at its base
XTB = -2900.0            # tower back (a shallow tower stays a narrow sliver at the screen edge)
T_TOP = 780.0            # tower wall top (absolute)
Y_FAR = 5400.0           # off-screen extent of walls and floor
COL_PITCH = 330.0
X_PALM = -1500.0         # palm stencil plane (4500 from the eye), in the garden behind the palace
Z_PYR = -1200.0          # pyramid bases (hidden behind the palace wall)


def load(name):
    """Layout of one built scenario (window polys, F, yc, envelope) plus the extents in layouts.json."""
    L = A.layout(os.path.join(WINDOWS, f"Flow Fix {name}.sce"))
    ex = json.load(open(os.path.join(HERE, "layouts.json")))[name]
    L.update(name=name, stoneL=ex["stone_y"][0], stoneR=ex["stone_y"][1], plinthL=ex["plinthL"][2],
             plinthR=ex["plinthR"][3], cornice=ex["cornice_top"], head=ex["head"], lionL=ex["lionL"],
             lionR=ex["lionR"])
    return L


def visible_y(x, y, margin=1.06):
    """Is world y inside the screen at depth x (with a small margin)?"""
    return abs(y) < TANH * (x - EYE_X) * margin


# ---- merlons and crowns ----------------------------------------------------------------------------------
def merlon(a0, zb, t0, t1, s, slot, along="y", mirror=False):
    """Round-topped 'Egyptian merlon': a (130 s) wide profile, 55 s straight + a 65 s half-round, extruded
    between t0 and t1 on the other horizontal axis. along='y': the profile runs along y from a0 (a0 is the edge
    nearest the axis; mirror=True runs toward -y), thickness along x; along='x': profile along x, thickness in y."""
    w, h, r = 130 * s, 55 * s, 65 * s
    sg = -1 if mirror else 1
    prof = [(a0, zb), (a0 + sg * w, zb), (a0 + sg * w, zb + h)]
    prof += [(a0 + sg * (r + r * math.cos(math.pi * j / 6)), zb + h + r * math.sin(math.pi * j / 6)) for j in range(1, 6)]
    prof += [(a0, zb + h)]
    if along == "y":
        P = lambda a, z, t: (t, a, z)
    else:
        P = lambda a, z, t: (a, t, z)
    cen = P(a0 + sg * r, zb + h, (t0 + t1) / 2)
    out = [poly([P(a, z, t0) for a, z in prof], slot, ref=cen), poly([P(a, z, t1) for a, z in prof], slot, ref=cen)]
    for i in range(1, len(prof)):                      # skip the bottom edge (it sits on the cavetto)
        j = (i + 1) % len(prof)
        out.append(poly([P(*prof[i], t0), P(*prof[j], t0), P(*prof[j], t1), P(*prof[i], t1)], slot, ref=cen))
    return out


def crown(face_x, back_x, y_in, y_out, z0, s, ret=False, merlons=True, vis=None):
    """Palace crown on a wall whose front face (facing the player) is at face_x and top at z0, running from
    y_in (the end nearest the axis) to y_out: red band just under the top, a two-step limestone cavetto over the
    whole top, then a row of merlons along the front (and along the inner end if ret)."""
    sg = 1 if y_out > y_in else -1
    out = []

    def span(ext):
        a, b = y_in - sg * (ext if ret else 0), y_out
        return min(a, b), max(a, b)
    out += box_polys(face_x - 12 * s, back_x, *span(12 * s), z0 - 30 * s, z0, OCHRE)
    out += box_polys(face_x - 30 * s, back_x, *span(30 * s), z0, z0 + 35 * s, LIME)
    out += box_polys(face_x - 52 * s, back_x, *span(52 * s), z0 + 35 * s, z0 + 75 * s, LIME)
    if not merlons:
        return out
    zb = z0 + 75 * s
    pitch = 210 * s
    a = y_in + sg * 25 * s
    while sg * (y_out - (a + sg * 130 * s)) >= 0:
        if vis is None or vis(face_x, a):
            out += merlon(a, zb, face_x - 40 * s, face_x, s, LIME, "y", mirror=sg < 0)
        a += sg * pitch
    if ret:                                           # return row along the inner end, front to back
        a = face_x + 25 * s
        while a + 130 * s <= back_x - 10:
            out += merlon(a, zb, y_in - sg * 40 * s, y_in, s, LIME, "x")
            a += pitch
    return out


# ---- palms (flat stencils facing the player) -------------------------------------------------------------
def flat(pts, slot):
    return poly([(X_PALM, y, z) for y, z in pts], slot, out=(-1, 0, 0), flat=True)


def strip(path, halfw, slot):
    """A flat band of varying half-width along a 2D (y, z) path, as quads."""
    out = []
    for i in range(len(path) - 1):
        (y0, z0), (y1, z1) = path[i], path[i + 1]
        dy, dz = y1 - y0, z1 - z0
        l = math.hypot(dy, dz) or 1
        ny, nz = -dz / l, dy / l
        w0, w1 = halfw[i], halfw[i + 1]
        out.append(flat([(y0 - ny * w0, z0 - nz * w0), (y1 - ny * w1, z1 - nz * w1),
                         (y1 + ny * w1, z1 + nz * w1), (y0 + ny * w0, z0 + nz * w0)], slot))
    return out


def frond(c, a0, length, droop, wmax, slot, n=8):
    """Feather (pinnate) frond: a thin rachis with forward-angled leaflet teeth on both sides."""
    bend = -1 if math.cos(math.radians(a0)) >= 0 else 1
    pts, th = [c], math.radians(a0)
    step = length / n
    for i in range(n):
        th += bend * math.radians(droop) / n
        y, z = pts[-1]
        pts.append((y + step * math.cos(th), z + step * math.sin(th)))
    out = []
    for i in range(n):
        (y0, z0), (y1, z1) = pts[i], pts[i + 1]
        dy, dz = (y1 - y0) / step, (z1 - z0) / step
        ny, nz = -dz, dy
        s = (i + 0.5) / n
        core0, core1 = 9 * (1 - 0.6 * i / n), 9 * (1 - 0.6 * (i + 1) / n)
        leaf = wmax * math.sin(math.pi * min(1.0, 0.12 + s))       # leaflets longest mid-frond
        out.append(flat([(y0 - ny * core0, z0 - nz * core0), (y1 - ny * core1, z1 - nz * core1),
                         (y1 + ny * core1, z1 + nz * core1), (y0 + ny * core0, z0 + nz * core0)], slot))
        for sd in (-1, 1):
            tip = (y1 + sd * ny * leaf + dy * leaf * 0.55, z1 + sd * nz * leaf + dz * leaf * 0.55 - 0.25 * leaf)
            out.append(flat([(y0 + sd * ny * core0, z0 + sd * nz * core0), (y1 + sd * ny * core1, z1 + sd * nz * core1),
                             tip], slot))
    return out


def date_palm(yb, zb, crown_c, slot):
    """Date palm: slightly curved trunk to crown_c (y, z), 15 arching feather fronds."""
    cy, cz = crown_c
    path = [(yb + (cy - yb) * (t / 8) ** 1.6, zb + (cz - zb) * t / 8) for t in range(9)]
    out = strip(path, [34 - 12 * t / 8 for t in range(9)], slot)
    out += strip([(cy, cz - 60), (cy, cz + 40)], [40, 30], slot)            # crown knob
    spec = [(96, 520, 8, 44), (72, 600, 30, 52), (118, 580, 28, 50), (48, 650, 55, 56), (140, 640, 55, 56),
            (26, 700, 75, 58), (160, 690, 75, 58), (6, 680, 95, 56), (178, 660, 95, 56), (-14, 600, 100, 50),
            (196, 610, 100, 50), (-34, 520, 90, 44), (214, 500, 90, 44), (60, 470, 12, 40), (126, 450, 12, 40)]
    for a0, ln, dr, w in spec:
        out += frond((cy, cz), a0, ln, dr, w, slot)
    return out


def fan(c, a_mid, r, slot, spread=70.0, teeth=5):
    """Doum fan leaf: a sector with a ragged (split) outer edge, fanned from its stalk end c."""
    pts = [c]
    k = 2 * teeth
    for j in range(k + 1):
        a = math.radians(a_mid - spread / 2 + spread * j / k)
        rr = r * (1.0 if j % 2 == 0 else 0.84)
        pts.append((c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)))
    return [flat([pts[0], pts[j], pts[j + 1]], slot) for j in range(1, len(pts) - 1)]


def doum_palm(yb, zb, fork, crowns, slot):
    """Doum palm: trunk forks once; each branch ends in a round crown of 9 stiff fan leaves."""
    fy, fz = fork
    out = strip([(yb, zb), ((yb + fy) / 2 + 10, (zb + fz) / 2), (fy, fz)], [38, 34, 30], slot)
    for (cy, cz), sd in zip(crowns, (-1, 1)):
        mid = ((fy + cy) / 2 + sd * 30, (fz + cz) / 2 - 30)
        out += strip([(fy, fz), mid, (cy, cz)], [28, 24, 20], slot)
        for k, a in enumerate([-20, 5, 30, 58, 90, 122, 150, 175, 200]):
            r = 280 * (0.85 if k % 2 else 1.0)
            st = (cy + 55 * math.cos(math.radians(a)), cz + 55 * math.sin(math.radians(a)))
            out += strip([(cy, cz), st], [14, 10], slot)
            out += fan(st, a, r, slot)
    return out


# ---- pyramids ---------------------------------------------------------------------------------------------
def pyramid(u, v, d, slope):
    """Plain square pyramid, cardinal (axis-aligned), apex at screen (u, v) and distance d; base hidden."""
    xc, yc_ = EYE_X + d, u * d
    h = v * d - Z_PYR
    b = h / math.tan(math.radians(slope))
    apex = (xc, yc_, Z_PYR + h)
    cs = [(xc - b, yc_ - b), (xc - b, yc_ + b), (xc + b, yc_ + b), (xc + b, yc_ - b)]
    out = []
    for i in range(4):
        p, q = cs[i], cs[(i + 1) % 4]
        out.append(poly([(p[0], p[1], Z_PYR), (q[0], q[1], Z_PYR), apex], LIME, ref=(xc, yc_, Z_PYR + h / 3)))
    return out, (xc, yc_, b, h)


PYRAMIDS_L = {"Khafre-like": (-0.775, 0.222, 30000, 53.1), "Khufu-like": (-0.88, 0.212, 34000, 51.8),
              "Menkaure-like": (-0.955, 0.176, 28000, 51.3)}
PYRAMIDS_R = {"Red-like": (0.80, 0.205, 30000, 43.4), "second": (0.935, 0.19, 34000, 52.0)}


# ---- the court --------------------------------------------------------------------------------------------
def court(L):
    """Objects: {'name', 'kind': 'box'|'mesh', 'box'?, 'slot'?, 'polys', 'stage'}. Also sets L['shadows']
    (render-only roof shadows for the assumed sun) and L['info']."""
    F, yc = L["F"], L["yc"]
    objs, shadows, info = [], [], {}

    def box(name, stage, x0, x1, y0, y1, z0, z1, slot, **flags):
        objs.append({"name": name, "kind": "box", "stage": stage, "box": (x0, x1, y0, y1, z0, z1), "slot": slot,
                     "polys": box_polys(x0, x1, y0, y1, z0, z1, slot, **flags)})

    def mesh(name, stage, polys):
        objs.append({"name": name, "kind": "mesh", "stage": stage, "polys": polys})

    # 1. Paving and the axial pool (navy water, limestone kerb as 4 editable blocks)
    box("court floor", "A", -4900, XW1, yc - Y_FAR, yc + Y_FAR, F - 60, F, PAVE, ground=0)
    px0, px1, pw, kw, kh = -4450.0, -3450.0, 330.0, 45.0, 30.0
    box("pool water", "A", px0, px1, yc - pw, yc + pw, F, F + 5, NAVY, ground=1)
    box("pool kerb near", "A", px0 - kw, px0, yc - pw - kw, yc + pw + kw, F, F + kh, LIME)
    box("pool kerb far", "A", px1, px1 + kw, yc - pw - kw, yc + pw + kw, F, F + kh, LIME)
    box("pool kerb left", "A", px0, px1, yc - pw - kw, yc - pw, F, F + kh, LIME)
    box("pool kerb right", "A", px0, px1, yc + pw, yc + pw + kw, F, F + kh, LIME)

    u_stone = max(-L["stoneL"], L["stoneR"]) / (-3020 - EYE_X)
    info["u_stone"] = u_stone
    sides = (("left", -1, L["stoneL"], L["plinthL"]), ("right", 1, L["stoneR"], L["plinthR"]))
    for side, sg, stone, plinth in sides:
        Y = lambda yp: yc + sg * yp                     # distance from the axis -> world y
        y_wall0 = stone - sg * 60                       # palace wall starts hidden behind the pilaster
        py0 = plinth + sg * 170                         # portico starts 170 past the lion plinth
        py1 = Y(Y_TW)                                   # and ends at the tower
        info[f"py0_{side}"], info[f"py1_{side}"] = py0, py1

        # 2. Palace front wall (behind the backdrop plane: can never cover a target)
        box(f"palace wall {side}", "A", XW0, XW1, *sorted((y_wall0, Y(Y_FAR))), F, Z_TOP, PALACE)
        # 3. Portico roof / architrave (a plain block, palace grey)
        box(f"portico roof {side}", "A", XP, XW0, *sorted((py0, py1)), Z_TOP - ROOF_H, Z_TOP, PALACE)
        # render-only: the roof's shadow on the back wall for the assumed sun (-0.55, -0.35, 0.75)
        dz, dy = 340 * 0.75 / 0.55, 340 * 0.35 / 0.55
        # left: the tower blocks the low sun at the outer end, so the whole span is shaded; right: the sun
        # enters at the open inner end and lights a strip 'dy' wide there. Clipped to the portico span.
        ya, yb = sorted((py0, py1)) if sg < 0 else (py0 + dy, py1)
        shadows.append(poly([(XW0 - 0.5, ya, Z_TOP - ROOF_H - dz), (XW0 - 0.5, yb, Z_TOP - ROOF_H - dz),
                             (XW0 - 0.5, yb, Z_TOP - ROOF_H), (XW0 - 0.5, ya, Z_TOP - ROOF_H)], PALACE,
                            out=(-1, 0, 0), shadow=True))

        # 4. Skyline mesh: crown on the palace wall (between window and portico), crown on the portico front
        #    (with its inner-end return), and the battered corner tower with a 1.25x crown.
        vis = lambda fx, a: visible_y(fx, a) and abs(a) / (fx - EYE_X) > u_stone - 0.01
        sky = []
        sky += crown(XW0, XW1, y_wall0, py0 - sg * 20, Z_TOP, 1.0, vis=vis)
        sky += crown(XP, XW0, py0, py1, Z_TOP, 1.0, ret=True, vis=vis)
        yi0, yi1 = Y(Y_TW), Y(Y_TW + BATTER)
        xt1 = XT + BATTER
        yf = Y(Y_FAR)
        tw = [poly([(XT, yi0, F), (XT, yf, F), (xt1, yf, T_TOP), (xt1, yi1, T_TOP)], PALACE, out=(-1, 0, 0)),
              poly([(XT, yi0, F), (XTB, yi0, F), (XTB, yi1, T_TOP), (xt1, yi1, T_TOP)], PALACE, out=(0, -sg, 0)),
              poly([(xt1, yi1, T_TOP), (XTB, yi1, T_TOP), (XTB, yf, T_TOP), (xt1, yf, T_TOP)], PALACE, out=(0, 0, 1)),
              poly([(XTB, yi0, F), (XTB, yf, F), (XTB, yf, T_TOP), (XTB, yi1, T_TOP)], PALACE, out=(1, 0, 0)),
              poly([(XT, yf, F), (XTB, yf, F), (XTB, yf, T_TOP), (xt1, yf, T_TOP)], PALACE, out=(0, sg, 0))]
        sky += tw
        sky += crown(xt1, XTB, yi1, yf, T_TOP, 1.25, ret=True, vis=vis)
        mesh(f"skyline {side}", "A", sky)

        # 5. Colonnade mesh: stylobate + N palm columns centred in the portico span
        span = abs(py1 - py0)
        n = max(2, min(4, int((span - 236 - 80) // COL_PITCH) + 1))
        mid = (py0 + py1) / 2
        ys = [mid + (k - (n - 1) / 2) * COL_PITCH for k in range(n)]
        info[f"cols_{side}"] = ys
        col = box_polys(XS, XW0, *sorted((py0 - sg * 40, py1)), F, F + 40, LIME, ground=2)
        zb, zt = F + 40, Z_TOP - ROOF_H
        H = zt - zb
        info["col_h"] = H
        for ci, cy in enumerate(ys):
            first = len(col)
            z1 = zb + 0.031 * H
            col += frustum(XC, cy, zb, z1, 118, 112, 10, LIME, caps=(False, True))            # base disk
            z2 = zb + 0.72 * H
            col += frustum(XC, cy, z1, z2, 62, 57, 10, OCHRE, caps=(False, False))           # shaft
            z3 = z2 + 0.026 * H
            col += frustum(XC, cy, z2, z3, 65, 65, 10, GOLD, caps=(False, False))            # binding band
            z4 = zb + 0.953 * H
            col += frustum(XC, cy, z3, z4, 57, 108, 0, GOLD, star=(8, 0.86, 0.80), caps=(False, False))  # palm capital
            col += box_polys(XC - 85, XC + 85, cy - 85, cy + 85, z4, zt, LIME)                # abacus
            for k, q in enumerate(col[first:]):
                q["grp"], q["ord"] = (side, ci), k
        mesh(f"colonnade {side}", "B", col)

    # 6. Pyramids (absolute apexes: the same screen position in every layout)
    for side, table in (("left", PYRAMIDS_L), ("right", PYRAMIDS_R)):
        pp = []
        for nm, args in table.items():
            q, inf = pyramid(*args)
            pp += q
            info[nm] = inf
        mesh(f"pyramids {side}", "C", pp)

    # 7. Palms: flat stencils in the garden behind the palace, placed clear of the cornice by screen position
    d = X_PALM - EYE_X
    uL = -max(0.60, -L["stoneL"] / (-3020 - EYE_X) + 0.10)
    uR = max(0.60, L["stoneR"] / (-3020 - EYE_X) + 0.10)
    info["palm_u"] = (uL, uR)
    mesh("date palm left", "C", date_palm(uL * d + 25, F, (uL * d - 20, 0.27 * d), PALACE))
    mesh("doum palm right", "C", doum_palm(uR * d, F, (uR * d + 30, 0.165 * d),
                                            [((uR - 0.040) * d, 0.262 * d), ((uR + 0.052) * d, 0.286 * d)], PALACE))
    L["shadows"], L["info"] = shadows, info
    return objs


def tri_count(o):
    if o["kind"] == "box":
        return 12
    return sum(len(p["pts"]) - 2 for p in o["polys"])


if __name__ == "__main__":
    L = load("Overflick")
    objs = court(L)
    for o in objs:
        print(f"{o['name']:22} {o['kind']:4} stage {o['stage']} tris {tri_count(o):5d}")
    print("objects", len(objs), "tris", sum(tri_count(o) for o in objs))
    print({k: (tuple(round(x) for x in v) if isinstance(v, tuple) else v) for k, v in L["info"].items()})
