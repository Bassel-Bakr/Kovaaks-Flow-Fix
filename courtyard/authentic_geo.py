"""Reference copy (run from D:/Projects/flowfix with PYTHONPATH=.;test_out/courtyard). Throwaway: the 'authentic palace court' concept around the Egyptian window (geometry only).

Coordinates: map units, x from the player to the target wall (x = west), +y screen right (north), +z up.
The court is generated per layout from the built window: F = the window's lowest point (court floor),
yc = the window axis, plinth extents -> where the first column may stand.
"""
import json
import math

import arena
import build

EYE_X = -6000.0
TANH = math.tan(math.radians(51.5))
TANV = TANH * 9 / 16

UMBER, LAPIS, LIME, OCHRE = (0, "wall"), (0, "ground"), (0, "ceiling"), (0, "ramp")
BACK, NAVY, MUD, GOLD = (1, "wall"), (1, "ground"), (1, "ceiling"), (1, "ramp")
SLOTS = {UMBER: ("2b1d12", 0.20), LAPIS: ("1e4c9a", 0.35), LIME: ("eadbb6", 0.35), OCHRE: ("9a3f22", 0.30),
         BACK: ("c8c8c8", 0.40), NAVY: ("0f2a4d", 0.30), MUD: ("5a534b", 0.30), GOLD: ("d4a02a", 0.50)}

# ---- the concept's fixed numbers -------------------------------------------------------------------
Z_ROOF = 240.0          # portico cornice top (absolute, so the skyline is the same in all 13 layouts)
X_COL = -2750.0         # column axis line (behind the backdrop plane -2900)
STYLO_H = 50.0          # limestone stylobate under the portico
X_BACKWALL = -2150.0    # palace facade behind the portico
Y_IN = 1300.0           # portico starts here (hidden behind the window's pilasters)
Y_OUT = 5300.0          # and runs off screen
ENC_X, ENC_T = 500.0, 300.0      # crenellated enclosure wall (Medinet Habu type), front face and thickness
ENC_TOP = 0.105 * (ENC_X - EYE_X)    # its wall top sits at v = 0.105 on screen
MERLON_W, MERLON_GAP, MERLON_RECT = 170.0, 90.0, 45.0
PYR_BASE_Z = -1150.0


# ---- small vector helpers ----------------------------------------------------------------------------
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)
def centroid(pts): return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))


def newell(pts):
    n = [0.0, 0.0, 0.0]
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        n[0] += (p[1] - q[1]) * (p[2] + q[2])
        n[1] += (p[2] - q[2]) * (p[0] + q[0])
        n[2] += (p[0] - q[0]) * (p[1] + q[1])
    return norm(tuple(n))


def poly(pts, slot, ref=None, out=None, **flags):
    """A planar polygon; oriented so its normal points away from ref (or along out)."""
    pts = [tuple(p) for p in pts]
    n = newell(pts)
    want = out if out is not None else sub(centroid(pts), ref)
    if dot(n, want) < 0:
        pts, n = pts[::-1], mul(n, -1)
    d = {"pts": pts, "n": n, "slot": slot}
    d.update(flags)
    return d


def box_polys(x0, x1, y0, y1, z0, z1, slot, **flags):
    c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    faces = [[(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
             [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
             [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    return [poly(f, slot, ref=c, **flags) for f in faces]


def ring(cx, cy, z, radii, angles):
    return [(cx + r * math.cos(a), cy + r * math.sin(a), z) for r, a in zip(radii, angles)]


def frustum(cx, cy, z0, z1, r0, r1, n, slot, star=None, caps=(True, True), phase=0.0):
    """Vertical prism/frustum; r0, r1 scalars, or star=(k, rin_ratio) for a lobed (palm frond) profile."""
    if star:
        k, ratio0, ratio1 = star
        n = 2 * k
        angles = [phase + math.pi * i / k for i in range(n)]
        rad0 = [r0 * (1 if i % 2 == 0 else ratio0) for i in range(n)]
        rad1 = [r1 * (1 if i % 2 == 0 else ratio1) for i in range(n)]
    else:
        angles = [phase + 2 * math.pi * i / n for i in range(n)]
        rad0, rad1 = [r0] * n, [r1] * n
    b, t = ring(cx, cy, z0, rad0, angles), ring(cx, cy, z1, rad1, angles)
    ref = (cx, cy, (z0 + z1) / 2)
    out = []
    for i in range(n):
        j = (i + 1) % n
        q = [b[i], b[j], t[j], t[i]]
        mid = centroid(q)
        out.append(poly(q, slot, out=(mid[0] - cx, mid[1] - cy, 0.0)))
    if caps[0]:
        out += fan_cap(b, (cx, cy, z0), slot, (0, 0, -1))
    if caps[1]:
        out += fan_cap(t, (cx, cy, z1), slot, (0, 0, 1))
    return out


def fan_cap(ringpts, centre, slot, outdir):
    """Cap a (possibly star-shaped) ring with triangles around its centre."""
    return [poly([centre, ringpts[i], ringpts[(i + 1) % len(ringpts)]], slot, out=outdir) for i in range(len(ringpts))]


def sweep(path, hw, ht, n, slot, cap_start=True, cap_end=True, side=None):
    """Tube along path; cross-section an ellipse (semi-axes hw across, ht up) sampled at n points."""
    secs = []
    for i, p in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
        T = norm(sub(b, a))
        S = cross(T, (0, 0, 1))
        if math.sqrt(dot(S, S)) < 1e-4:
            S = side or (0, 1, 0)
        S = norm(S)
        U = norm(cross(S, T))
        w, h = hw[i], ht[i]
        secs.append([add(p, add(mul(S, w * math.cos(2 * math.pi * k / n)), mul(U, h * math.sin(2 * math.pi * k / n))))
                     for k in range(n)])
    out = []
    for i in range(len(path) - 1):
        c = mul(add(path[i], path[i + 1]), 0.5)
        for k in range(n):
            q = [secs[i][k], secs[i][(k + 1) % n], secs[i + 1][(k + 1) % n], secs[i + 1][k]]
            out.append(poly(q, slot, ref=c))
    if cap_start:
        out.append(poly(secs[0], slot, out=sub(path[0], path[1])))
    if cap_end:
        out.append(poly(secs[-1], slot, out=sub(path[-1], path[-2])))
    return out


# ---- layout -------------------------------------------------------------------------------------------
def spawn_volumes(m):
    vols = []
    for o in m["objects"]:
        if o.get("name") != "SpawnVolume":
            continue
        pr = {q["name"]: q["value"] for q in o["properties"]}
        if pr["TeamMask"] != 2:
            continue
        _, y, z = (float(t) for t in o["location"].split(","))
        _, sy, sz = (float(t) for t in o["scale"].split(","))
        vols.append({"y": y, "z": z, "size_y": sy, "size_z": sz})
    return vols


def window_polys(o, ms):
    """The window's own brushes as render polygons (boxes: slot of face 0; meshes: per section)."""
    x, y, z = (float(t) for t in o["location"].split(","))
    if "procedural" in o:
        sx, sy, sz = (float(t) * ms for t in o["scale"].split(","))
        out = []
        for sec, mset in zip(o["procedural"], o["materialSets"]):
            vs = [((x + a * sx, y + b * sy, z + c * sz), tuple(float(t) for t in v["normal"].split(",")))
                  for v in sec["vertices"] for a, b, c in [tuple(float(t) for t in v["location"].split(","))]]
            idx = sec["indices"]
            for k in range(0, len(idx), 3):
                tri = [vs[i] for i in idx[k:k + 3]]
                out.append({"pts": [t[0] for t in tri], "n": tri[0][1], "slot": (mset["group"], mset["surface"]),
                            "window": True})
        return out
    sx, sy, sz = (float(t) * 100 for t in o["scale"].split(","))
    ms0 = o["materialSets"][0]
    return box_polys(x, x + sx, y, y + sy, z, z + sz, (ms0["group"], ms0["surface"]), window=True)


def layout(path):
    p = build.parse(path)
    m = json.loads(p["map"])
    ms = float(next(l.split("=", 1)[1] for l in p["top"] if l.startswith("MapScale=")))
    rad = max(float(build.get_key(s["lines"], "MainBBRadius")) for s in p["sections"]
              if s["type"] == "Character Profile" and s["name"] != "Player")
    env = arena.target_envelope(spawn_volumes(m), rad)
    X, Y, Z, polys = [], [], [], []
    yc = 0.0
    for o in m["objects"]:
        if o.get("type") != "brush":
            continue
        x, y, z = (float(t) for t in o["location"].split(","))
        if not -3600 < x < -2800:          # the window, and the turned lions and their plinths (to -3500)
            continue
        pp = window_polys(o, ms)
        polys += pp
        for q in pp:
            for v in q["pts"]:
                X.append(v[0]); Y.append(v[1]); Z.append(v[2])
        if o["location"].startswith("-2899.99") and o["materialSets"][0]["group"] == 1:
            sy = float(o["scale"].split(",")[1]) * 100
            yc = y + sy / 2
    # the window stone's half-width above the plinths (pilasters, cornice): the portico starts inside it
    stone = [abs(v[1] - yc) for q in polys if q["slot"] == (0, "ceiling") for v in q["pts"] if v[2] > min(Z) + 150]
    return {"path": path, "map": m, "parsed": p, "ms": ms, "rad": rad, "env": env, "F": min(Z), "y_stone": max(stone),
            "ymin": min(Y), "ymax": max(Y), "ztop": max(Z), "yc": yc, "window": polys,
            "back": arena.SPAWN_X + rad / arena.MAP_SCALE}


# ---- the court ----------------------------------------------------------------------------------------
def court(L):
    """Return the list of objects: {'name', 'kind': 'box'|'mesh', 'box'?, 'slot'?, 'polys'}."""
    F, yc = L["F"], L["yc"]
    objs = []

    def box(name, x0, x1, y0, y1, z0, z1, slot, **flags):
        objs.append({"name": name, "kind": "box", "box": (x0, x1, y0, y1, z0, z1), "slot": slot,
                     "polys": box_polys(x0, x1, y0, y1, z0, z1, slot, **flags)})

    def mesh(name, polys):
        objs.append({"name": name, "kind": "mesh", "polys": polys})

    # 1. Court pavement (mud plaster), split at the targets' back plane so the rear half is never checked.
    xs = -2915.0                                   # behind every layout's target back plane (-2918 at most)
    box("pavement front", -5000, xs, yc - 5300, yc + 5300, F - 100, F, MUD, ground=0)
    box("pavement rear", xs, -2040, yc - 5300, yc + 5300, F - 100, F, MUD, ground=0)

    # 2. Axial pool (Malqata / Amarna painted-pool floor as a shallow basin) with a limestone kerb.
    px0, px1, pw, kw, kh = -4450.0, -3450.0, 330.0, 45.0, 40.0
    box("pool water", px0, px1, yc - pw, yc + pw, F, F + 6, NAVY, ground=1)
    box("pool kerb near", px0 - kw, px0, yc - pw - kw, yc + pw + kw, F, F + kh, LIME)
    box("pool kerb far", px1, px1 + kw, yc - pw - kw, yc + pw + kw, F, F + kh, LIME)
    box("pool kerb left", px0, px1, yc - pw - kw, yc - pw, F, F + kh, LIME)
    box("pool kerb right", px0, px1, yc + pw, yc + pw + kw, F, F + kh, LIME)

    # 3. Portico wings: 4 palm columns per side (8 in all; the window stands between the 4th and 5th,
    #    as at Medinet Habu), architrave, torus bead, 3-step cavetto cornice, roof, palace facade, a door.
    S = F + STYLO_H
    D = (Z_ROOF - S) / 9.8                         # base .33 + column 7.5 + architrave 1 + bead .13 + cornice .84
    L["D"] = D
    X_COL = -2895.0 + 1.30 * D                     # so the cornice's front (1.30 D ahead of the axis) stays behind x = -2895
    L["x_col"] = X_COL
    base_h, col_h = 0.33 * D, 7.5 * D
    cap_h, abacus_h, band_zone = 0.26 * col_h, 0.30 * D, 0.49 * D
    shaft_h = col_h - cap_h - abacus_h - band_zone
    arch0 = S + base_h + col_h
    arch1 = arch0 + 1.0 * D
    bead1 = arch1 + 0.13 * D
    step = 0.28 * D
    xa0, xa1 = X_COL - 0.55 * D, X_COL + 0.55 * D
    # first column clear of the lion plinth on screen: base disk's far inner point 0.02 (15 px) outside it
    rb = 1.1 * D
    u_pl = max(-L["ymin"], L["ymax"]) / (-3090 - EYE_X)
    need = []
    for sgn in (-1, 1):
        # |y| = y' + sgn*yc ... solve (|y| - rb) / (d_col + rb) >= u_side + 0.02
        u_side = (-L["ymin"] if sgn < 0 else L["ymax"]) / (-3090 - EYE_X)
        absy = (u_side + 0.02) * (X_COL - EYE_X + rb) + rb
        need.append(absy - sgn * yc)          # world |y| = y' + sgn*yc
    y4 = max(need)
    spacing = 4.1 * D
    L["cols"] = [y4 + k * spacing for k in range(4)]
    L["u_plinth"] = u_pl
    for side, sgn in (("left", -1), ("right", 1)):
        def Y(yp):                                   # y' (distance from the axis) -> world y
            return yc + sgn * yp
        ylo, yhi = sorted((Y(L["y_stone"] - 40), Y(Y_OUT)))
        struct = []
        stylo = box_polys(-2895, X_BACKWALL + 100, ylo, yhi, F, S, LIME)                  # stylobate
        for q in stylo:
            if q["n"][2] > 0.9:
                q["ground"] = 2
        struct += stylo
        struct += box_polys(xa0, xa1, ylo, yhi, arch0, arch1, LIME)                        # architrave
        struct += box_polys(xa0 - 0.12 * D, xa1, ylo, yhi, arch1, bead1, OCHRE)            # torus bead
        for k in range(3):                                                                 # cavetto steps
            struct += box_polys(xa0 - (k + 1) * 0.25 * D, xa1, ylo, yhi, bead1 + k * step, bead1 + (k + 1) * step, LIME)
        struct += box_polys(xa1, X_BACKWALL + 100, ylo, yhi, arch1 - 0.6 * D, arch1, MUD)  # roof slab
        struct += box_polys(X_BACKWALL, X_BACKWALL + 100, ylo, yhi, S, arch1 - 0.6 * D, LIME, shadow=True)  # facade
        mesh(f"portico {side} structure", struct)
        cols = []
        for ci, yp in enumerate(L["cols"]):
            cx, cy = X_COL, Y(yp)
            first = len(cols)
            cols += frustum(cx, cy, S, S + base_h, 1.1 * D, 1.05 * D, 10, LIME, caps=(False, True))
            z = S + base_h
            cols += frustum(cx, cy, z, z + shaft_h, 0.5 * D, 0.45 * D, 8, OCHRE, caps=(False, False))
            z += shaft_h
            bh, gh = 0.07 * D, 0.035 * D
            for b in range(5):                                        # five binding bands
                cols += frustum(cx, cy, z, z + bh, 0.48 * D, 0.48 * D, 8, GOLD, caps=(False, False))
                z += bh
                if b < 4:
                    cols += frustum(cx, cy, z, z + gh, 0.45 * D, 0.45 * D, 8, OCHRE, caps=(False, False))
                    z += gh
            # palm capital: nine fronds bound round the top of the shaft, flaring outward at the tips
            z1 = z + 0.7 * cap_h
            cols += frustum(cx, cy, z, z1, 0.47 * D, 0.64 * D, 0, GOLD, star=(9, 0.88, 0.80), caps=(False, False))
            cols += frustum(cx, cy, z1, z + cap_h, 0.64 * D, 0.82 * D, 0, GOLD, star=(9, 0.80, 0.74), caps=(False, True))
            z += cap_h
            cols += box_polys(cx - 0.5 * D, cx + 0.5 * D, cy - 0.5 * D, cy + 0.5 * D, z, z + abacus_h, LIME)  # abacus
            for k, q in enumerate(cols[first:]):
                q["grp"], q["ord"] = (side, ci), k
        mesh(f"portico {side} columns", cols)
        # a limestone door in the facade, between the 3rd and 4th column from the window
        ydc = Y(L["cols"][0] + 1.5 * spacing)
        dw, dh, jw, lh = 2.2 * D, 4.7 * D, 0.4 * D, 0.7 * D
        xf = X_BACKWALL
        door = []
        door += box_polys(xf - 2, xf, ydc - dw / 2, ydc + dw / 2, S, S + dh, UMBER, shadow=True)
        door += box_polys(xf - 0.15 * D, xf, ydc - dw / 2 - jw, ydc - dw / 2, S, S + dh, OCHRE, shadow=True)
        door += box_polys(xf - 0.15 * D, xf, ydc + dw / 2, ydc + dw / 2 + jw, S, S + dh, OCHRE, shadow=True)
        door += box_polys(xf - 0.2 * D, xf, ydc - dw / 2 - jw - 0.1 * D, ydc + dw / 2 + jw + 0.1 * D, S + dh, S + dh + lh, LIME, shadow=True)
        mesh(f"door {side}", door)

    # 4. Garden palms behind the palace wings (dark umber silhouettes), crowns placed by screen position.
    def at(u, dd):
        return EYE_X + dd, u * dd

    def date_palm(u, dd, v_crown, lean, fr_len=900.0, seed=0.0):
        x0, y0 = at(u, dd)
        top = (x0 + 0.25 * lean * 60, y0 + lean * 60, v_crown * dd)
        n = 7
        path, r = [], []
        for i in range(n + 1):
            t = i / n
            path.append((x0 + (top[0] - x0) * t, y0 + (top[1] - y0) * t * t, F + (top[2] - F) * t))
            r.append(55 - 20 * t)
        out = sweep(path, r, r, 7, UMBER, side=(1, 0, 0))
        K = 12
        for k in range(K):
            ph = 2 * math.pi * k / K + seed
            e0 = math.radians([50, 24, 0][k % 3])
            ln = fr_len * [0.85, 1.0, 0.9][k % 3]
            h = (math.cos(ph), math.sin(ph), 0.0)
            g = ln * [0.55, 0.75, 0.6][k % 3]
            pts = []
            for i in range(6):
                s = i / 5
                pts.append(add(top, add(mul(h, ln * s * math.cos(e0)), (0, 0, ln * s * math.sin(e0) - g * s * s))))
            hw = [10, 40, 50, 44, 28, 6]
            out += sweep(pts, hw, [6, 12, 12, 9, 6, 2], 4, UMBER, cap_start=False)
        return out

    def doum_palm(u, dd, v_fork, v_crowns, spread=520.0):
        x0, y0 = at(u, dd)
        fork = (x0, y0 + 40, v_fork * dd)
        out = sweep([(x0, y0, F), (x0, y0 + 20, (F + fork[2]) / 2), fork], [60, 52, 46], [60, 52, 46], 7, UMBER, side=(1, 0, 0))
        for sgn, vc in zip((-1, 1), v_crowns):
            tip = (x0 + 80 * sgn, y0 + sgn * spread, vc * dd)
            mid = ((fork[0] + tip[0]) / 2, (fork[1] + tip[1]) / 2 - sgn * 60, (fork[2] + tip[2]) / 2 + 60)
            out += sweep([fork, mid, tip], [44, 38, 32], [44, 38, 32], 7, UMBER, side=(1, 0, 0))
            for k in range(12):                       # fan-leaf crown: stiff upright fans on short stalks
                ph = 2 * math.pi * k / 12 + 0.3
                el = math.radians([55, 25, -5][k % 3])
                dvec = (math.cos(ph) * math.cos(el), math.sin(ph) * math.cos(el), math.sin(el))
                c = add(tip, mul(dvec, 120))
                h1 = norm(cross(dvec, (0, 0, 1))) if abs(dvec[2]) < 0.95 else (1, 0, 0)
                a1 = norm(cross(h1, dvec))           # the fan's plane holds dvec and the near-vertical a1
                a2 = h1
                fan = [c] + [add(c, add(mul(dvec, 240 * math.cos(t)), mul(a1, 240 * math.sin(t))))
                             for t in [math.radians(-75 + 18.75 * j) for j in range(9)]]
                out.append(poly(fan, UMBER, out=a2))
                out.append(poly([add(p, mul(a2, -3)) for p in fan], UMBER, out=mul(a2, -1)))
            out += sweep([tip, add(tip, (0, 0, 60))], [50, 20], [50, 20], 6, UMBER)
        return out

    right = date_palm(1.10, 4500, 0.43, 4, seed=0.2) + date_palm(1.31, 5100, 0.35, 6, fr_len=850, seed=1.1)
    left = date_palm(-1.06, 4700, 0.45, -3, seed=0.7) + doum_palm(-1.31, 4300, 0.09, (0.25, 0.30), spread=430)
    mesh("palms left", left)
    mesh("palms right", right)

    # 5. The crenellated enclosure (Medinet Habu's girdle wall, rounded 'Egyptian merlons'), far behind.
    for side, sgn in (("left", -1), ("right", 1)):
        ya, yb = sorted((yc + sgn * 2000, yc + sgn * 8600))
        enc = box_polys(ENC_X, ENC_X + ENC_T, ya, yb, PYR_BASE_Z, ENC_TOP, MUD)
        y = ya + 40
        while y + MERLON_W < yb:
            r = MERLON_W / 2
            prof = [(y, ENC_TOP), (y + MERLON_W, ENC_TOP), (y + MERLON_W, ENC_TOP + MERLON_RECT)]
            prof += [(y + r + r * math.cos(t), ENC_TOP + MERLON_RECT + r * math.sin(t))
                     for t in [math.pi * j / 6 for j in range(1, 6)]]
            prof += [(y, ENC_TOP + MERLON_RECT)]
            xf, xb = ENC_X + 60, ENC_X + 60 + 180
            front = [(xf, a, b) for a, b in prof]
            back = [(xb, a, b) for a, b in prof]
            cc = (xf + 90, y + r, ENC_TOP + MERLON_RECT)
            enc.append(poly(front, MUD, out=(-1, 0, 0)))
            for i in range(len(prof)):
                j = (i + 1) % len(prof)
                if i == 0:
                    continue                      # the bottom edge sits on the wall
                enc.append(poly([front[i], front[j], back[j], back[i]], MUD, ref=cc))
            y += MERLON_W + MERLON_GAP
        mesh(f"enclosure {side}", enc)

    # 6. The Memphite pyramid field on the western horizon (limestone casing; cardinal, so axis-aligned).
    def pyramid(u, dd, v_apex, slope_deg, name_sq=1.0):
        xc, yc_ = at(u, dd)
        h = v_apex * dd - PYR_BASE_Z
        b = h / math.tan(math.radians(slope_deg))
        apex = (xc, yc_, PYR_BASE_Z + h)
        cs = [(xc - b, yc_ - b * name_sq), (xc + b, yc_ - b * name_sq), (xc + b, yc_ + b * name_sq), (xc - b, yc_ + b * name_sq)]
        out = []
        for i in range(4):
            a, c = cs[i], cs[(i + 1) % 4]
            out.append(poly([(a[0], a[1], PYR_BASE_Z), (c[0], c[1], PYR_BASE_Z), apex], LIME, ref=(xc, yc_, PYR_BASE_Z + h / 3)))
        return out, (xc, yc_, b, h)

    def bent(u, dd, v_apex):
        xc, yc_ = at(u, dd)
        h = v_apex * dd - PYR_BASE_Z
        hb = 0.466 * h
        b1 = (h - hb) / math.tan(math.radians(43.3))
        b0 = b1 + hb / math.tan(math.radians(54.5))
        apex = (xc, yc_, PYR_BASE_Z + h)
        ref = (xc, yc_, PYR_BASE_Z + h / 4)
        out = []
        sq0 = [(xc - b0, yc_ - b0), (xc + b0, yc_ - b0), (xc + b0, yc_ + b0), (xc - b0, yc_ + b0)]
        sq1 = [(xc - b1, yc_ - b1), (xc + b1, yc_ - b1), (xc + b1, yc_ + b1), (xc - b1, yc_ + b1)]
        z1 = PYR_BASE_Z + hb
        for i in range(4):
            j = (i + 1) % 4
            out.append(poly([(sq0[i][0], sq0[i][1], PYR_BASE_Z), (sq0[j][0], sq0[j][1], PYR_BASE_Z),
                             (sq1[j][0], sq1[j][1], z1), (sq1[i][0], sq1[i][1], z1)], LIME, ref=ref))
            out.append(poly([(sq1[i][0], sq1[i][1], z1), (sq1[j][0], sq1[j][1], z1), apex], LIME, ref=ref))
        return out, (xc, yc_, b0, h)

    def step_pyr(u, dd, v_apex):
        xc, yc_ = at(u, dd)
        h = v_apex * dd - PYR_BASE_Z
        bx, by = h * 60.5 / 62.5, h * 54.5 / 62.5        # Djoser: 121 x 109 m base, 62.5 m tall
        out = []
        th = h / 6
        bat = th / math.tan(math.radians(74))          # each tier's faces lean in at about 74 degrees
        ref = (xc, yc_, PYR_BASE_Z + h / 3)
        for k in range(6):
            s0 = 1 - 0.13 * k
            z0, z1 = PYR_BASE_Z + k * th, PYR_BASE_Z + (k + 1) * th
            lo = [(xc - bx * s0, yc_ - by * s0), (xc + bx * s0, yc_ - by * s0), (xc + bx * s0, yc_ + by * s0), (xc - bx * s0, yc_ + by * s0)]
            hi = [(xc - bx * s0 + bat, yc_ - by * s0 + bat), (xc + bx * s0 - bat, yc_ - by * s0 + bat),
                  (xc + bx * s0 - bat, yc_ + by * s0 - bat), (xc - bx * s0 + bat, yc_ + by * s0 - bat)]
            for i in range(4):
                j = (i + 1) % 4
                out.append(poly([(lo[i][0], lo[i][1], z0), (lo[j][0], lo[j][1], z0), (hi[j][0], hi[j][1], z1), (hi[i][0], hi[i][1], z1)], LIME, ref=ref))
            out.append(poly([(p[0], p[1], z1) for p in hi], LIME, out=(0, 0, 1)))
        return out, (xc, yc_, bx, h)

    L["pyramids"] = {}
    lp, rp = [], []
    for nm, (pp, info) in {"Red (Dahshur)": pyramid(-0.72, 23000, 0.215, 43.2),
                           "Bent (Dahshur)": bent(-0.905, 27000, 0.195)}.items():
        lp += pp; L["pyramids"][nm] = info
    for nm, (pp, info) in {"Menkaure (Giza)": pyramid(0.72, 29500, 0.168, 51.3),
                           "Khafre (Giza)": pyramid(0.835, 30500, 0.215, 53.1),
                           "Khufu (Giza)": pyramid(0.95, 31500, 0.205, 51.8)}.items():
        rp += pp; L["pyramids"][nm] = info
    mesh("pyramids left (Dahshur)", lp)
    mesh("pyramids right (Giza)", rp)
    return objs
