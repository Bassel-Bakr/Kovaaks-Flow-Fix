"""Tools for sculpting smooth statues as custom meshes (2026-09-24): used by make_lion.py and make_pharaoh.py.

A statue is a signed distance field built from ellipsoids, tapered capsules and rounded boxes, joined with a smooth
minimum so the parts blend like carved stone. surface_nets() turns the field into quads (naive surface nets), gives
every vertex the field's gradient as its normal, so the statue shades smoothly, and sorts the triangles by colour:
colour(x, y, z) names the colour at a point, and triangles are cut along the colour boundaries. write() stores the result as JSON for egypt.py, whose
Scene.mesh_tris() places it in the map.

Pure Python (no numpy). A statue takes a few seconds, so the build reads the JSON instead of sculpting every time.
"""
import json
import math

from credits import CREDITS


def ellipsoid(c, r):
    cx, cy, cz = c
    rx, ry, rz = r

    def d(x, y, z):
        a, b, e = (x - cx) / rx, (y - cy) / ry, (z - cz) / rz
        k0 = math.sqrt(a * a + b * b + e * e)
        k1 = math.sqrt((a / rx) ** 2 + (b / ry) ** 2 + (e / rz) ** 2)
        return k0 * (k0 - 1.0) / k1 if k1 > 1e-9 else -min(r)
    return d


def cone(a, b, ra, rb):
    """A capsule from a to b whose radius runs from ra to rb."""
    ab = [b[i] - a[i] for i in range(3)]
    ll = sum(k * k for k in ab)

    def d(x, y, z):
        t = max(0.0, min(1.0, ((x - a[0]) * ab[0] + (y - a[1]) * ab[1] + (z - a[2]) * ab[2]) / ll))
        q = [a[i] + t * ab[i] for i in range(3)]
        return math.sqrt((x - q[0]) ** 2 + (y - q[1]) ** 2 + (z - q[2]) ** 2) - (ra + (rb - ra) * t)
    return d


def rbox(c, half, r):
    """A box centred on c with half-sizes half, its edges rounded by r."""
    def d(x, y, z):
        q = [abs(p - c[i]) - half[i] + r for i, p in enumerate((x, y, z))]
        out = math.sqrt(sum(max(k, 0.0) ** 2 for k in q))
        return out + min(max(q), 0.0) - r
    return d


def chain(points, r0, r1):
    """Tapered capsules along a polyline."""
    n = len(points) - 1
    return [cone(points[i], points[i + 1], r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n) for i in range(n)]


def pair(make):
    """A part and its mirror image: make(1) and make(-1)."""
    return [make(1), make(-1)]


def smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


def union(parts, k):
    """Smooth union of distance functions, as one distance function."""
    def d(x, y, z):
        v = parts[0](x, y, z)
        for f in parts[1:]:
            v = smin(v, f(x, y, z), k)
        return v
    return d


def surface_nets(field, colour, lo, hi, cell, hidden=None):
    """Mesh the surface field = 0 inside the box lo..hi. Returns vertices, unit normals and {colour: triangles},
    each triangle wound outward: (B - A) x (C - A) points along the normal. hidden(A, B, C) true leaves a triangle
    out (a flat back or underside nobody sees); vertices only such triangles used are dropped too."""
    n = [int(math.ceil((hi[i] - lo[i]) / cell)) + 1 for i in range(3)]
    P = lambda i, j, k: (lo[0] + i * cell, lo[1] + j * cell, lo[2] + k * cell)
    D = {}
    for i in range(n[0]):
        for j in range(n[1]):
            for k in range(n[2]):
                D[i, j, k] = field(*P(i, j, k))
    # one vertex per cell the surface crosses, at the mean of its edges' crossings
    edges = [((0, 0, 0), (1, 0, 0)), ((0, 1, 0), (1, 1, 0)), ((0, 0, 1), (1, 0, 1)), ((0, 1, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 1, 0)), ((1, 0, 0), (1, 1, 0)), ((0, 0, 1), (0, 1, 1)), ((1, 0, 1), (1, 1, 1)),
             ((0, 0, 0), (0, 0, 1)), ((1, 0, 0), (1, 0, 1)), ((0, 1, 0), (0, 1, 1)), ((1, 1, 0), (1, 1, 1))]
    vid, verts = {}, []
    for i in range(n[0] - 1):
        for j in range(n[1] - 1):
            for k in range(n[2] - 1):
                pts = []
                for a, b in edges:
                    pa, pb = (i + a[0], j + a[1], k + a[2]), (i + b[0], j + b[1], k + b[2])
                    da, db = D[pa], D[pb]
                    if (da < 0) != (db < 0):
                        t = da / (da - db)
                        A, B = P(*pa), P(*pb)
                        pts.append([A[m] + t * (B[m] - A[m]) for m in range(3)])
                if pts:
                    vid[i, j, k] = len(verts)
                    verts.append([sum(p[m] for p in pts) / len(pts) for m in range(3)])
    # one quad per grid edge the surface crosses, joining the four cells round it
    quads = []
    for i in range(n[0]):
        for j in range(n[1]):
            for k in range(n[2]):
                d0 = D[i, j, k]
                for axis in range(3):
                    q = [i, j, k]
                    q[axis] += 1
                    if q[axis] >= n[axis] or (d0 < 0) == (D[tuple(q)] < 0):
                        continue
                    u, v = [m for m in range(3) if m != axis]
                    cells = []
                    for du, dv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        c = [i, j, k]
                        c[u] -= du
                        c[v] -= dv
                        cells.append(tuple(c))
                    if all(c in vid for c in cells):
                        out = [0.0, 0.0, 0.0]                # outward: from the inside end of the edge
                        out[axis] = 1.0 if d0 < 0 else -1.0
                        quads.append(([vid[c] for c in cells], out))

    def grad(x, y, z, e=1.0):
        g = [field(x + e, y, z) - field(x - e, y, z), field(x, y + e, z) - field(x, y - e, z),
             field(x, y, z + e) - field(x, y, z - e)]
        ln = math.sqrt(sum(k * k for k in g)) or 1.0
        return [k / ln for k in g]
    normals = [grad(*p) for p in verts]
    # Colours are read at the vertices, and a triangle whose vertices differ is cut along the colour boundary
    # (found by bisection on its edges), so stripes and bands get straight, clean edges instead of steps of
    # whole quads. Each edge is cut once, so neighbouring triangles share the new vertex and no cracks open.
    vcol = [colour(*p) for p in verts]
    cut = {}

    def boundary(i, j):
        key = (min(i, j), max(i, j))
        if key not in cut:
            a, b = verts[key[0]], verts[key[1]]
            ca, lo, hi = vcol[key[0]], 0.0, 1.0
            for _ in range(12):
                mid = (lo + hi) / 2
                if colour(*[a[m] + mid * (b[m] - a[m]) for m in range(3)]) == ca:
                    lo = mid
                else:
                    hi = mid
            t = (lo + hi) / 2
            p = [a[m] + t * (b[m] - a[m]) for m in range(3)]
            verts.append(p)
            normals.append(grad(*p))
            vcol.append(None)
            cut[key] = len(verts) - 1
        return cut[key]
    tris = {}
    for q, out in quads:
        # wind the quad outward, judged by its diagonals against the grid edge it crosses (the smoothed normals
        # are not reliable where a quad folds over a sharp edge)
        d1 = [verts[q[2]][a] - verts[q[0]][a] for a in range(3)]
        d2 = [verts[q[3]][a] - verts[q[1]][a] for a in range(3)]
        cr = (d1[1] * d2[2] - d1[2] * d2[1], d1[2] * d2[0] - d1[0] * d2[2], d1[0] * d2[1] - d1[1] * d2[0])
        if sum(cr[a] * out[a] for a in range(3)) < 0:
            q = q[::-1]
        for t in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
            A, B, C = (verts[m] for m in t)
            if hidden and hidden(A, B, C):
                continue
            cs = [vcol[m] for m in t]
            if cs[0] == cs[1] == cs[2]:
                tris.setdefault(cs[0], []).append(list(t))
            elif len(set(cs)) == 3:                  # three colours meet: the colour at the middle takes it
                c = [sum(verts[m][a] for m in t) / 3 for a in range(3)]
                tris.setdefault(colour(*c), []).append(list(t))
            else:                                    # turn it so its odd vertex comes first, keeping the winding
                k = next(k for k in range(3) if cs[k] != cs[(k + 1) % 3] and cs[k] != cs[(k + 2) % 3])
                o, a, b = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
                pa, pb = boundary(o, a), boundary(o, b)
                tris.setdefault(vcol[o], []).append([o, pa, pb])
                tris.setdefault(vcol[a], []).extend([[pa, a, b], [pa, b, pb]])
    def area(t):
        A, B, C = (verts[m] for m in t)
        ab, ac = [B[a] - A[a] for a in range(3)], [C[a] - A[a] for a in range(3)]
        return math.sqrt((ab[1] * ac[2] - ab[2] * ac[1]) ** 2 + (ab[2] * ac[0] - ab[0] * ac[2]) ** 2
                         + (ab[0] * ac[1] - ab[1] * ac[0]) ** 2) / 2
    # the cuts leave a few slivers far below a pixel, some wound against their smoothed normals: drop them
    tris = {c: [t for t in ts if area(t) > 0.05] for c, ts in tris.items()}
    used = sorted({m for ts in tris.values() for t in ts for m in t})
    new = {m: k for k, m in enumerate(used)}
    return ([verts[m] for m in used], [normals[m] for m in used],
            {c: [[new[m] for m in t] for t in ts] for c, ts in tris.items() if ts})


def write(path, note, cell, verts, normals, tris):
    """Store a sculpt for egypt.py. "length" is its extent along x (toward the wall), from its front at x = 0."""
    out = {"credits": CREDITS, "note": note, "cell": cell, "length": round(max(v[0] for v in verts), 2),
           "vertices": [[round(c, 2) for c in v] for v in verts],
           "normals": [[round(c, 4) for c in nrm] for nrm in normals], "triangles": tris}
    path.write_text(json.dumps(out, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{path.name}: {len(verts)} vertices, "
          f"{sum(len(t) for t in tris.values())} triangles ({', '.join(f'{len(t)} {k}' for k, t in tris.items())}), "
          f"length {out['length']}")
