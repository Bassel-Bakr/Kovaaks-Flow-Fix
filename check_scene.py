"""Check that no map geometry can cover a target, whatever the decoration.

For every brush and prop in front of the targets' back plane, project its corners from the eye onto the
wall plane and fail if that rectangle overlaps the target envelope (where targets can appear, projected
the same way). Objects entirely behind the targets cannot cover them; objects extending behind the eye
(room shell) are skipped. Props have unknown size, so each counts as a 300-unit cube around its pivot.

Usage: python check_scene.py [folder]   (default: out); exits 1 on any overlap.
"""
import glob
import json
import math
import sys

import arena
import build

EYE_X = arena.PLAYER_X
PROP_HALF = 150.0


def spec_volumes(m):
    vols = []
    for o in m["objects"]:
        if o.get("name") != "SpawnVolume":
            continue
        props = {q["name"]: q["value"] for q in o["properties"]}
        if props["TeamMask"] != 2:
            continue
        _, y, z = (float(t) for t in o["location"].split(","))
        _, sy, sz = (float(t) for t in o["scale"].split(","))
        vols.append({"y": y, "z": z, "size_y": sy, "size_z": sz})
    return vols


def project(x, y, z):
    k = (arena.WALL_FRONT - EYE_X) / (x - EYE_X)
    return y * k, z * k


folder = sys.argv[1] if len(sys.argv) > 1 else "out"
bad = 0
for path in sorted(glob.glob(f"{folder}/*.sce")):
    p = build.parse(path)
    m = json.loads(p["map"])
    map_scale = float(next(l.split("=", 1)[1] for l in p["top"] if l.startswith("MapScale=")))
    radius = max(float(build.get_key(s["lines"], "MainBBRadius")) for s in p["sections"]
                 if s["type"] == "Character Profile" and s["name"] != "Player")
    ty0, ty1, tz0, tz1 = arena.target_envelope(spec_volumes(m), radius)
    back = arena.SPAWN_X + radius / arena.MAP_SCALE      # the targets' far side
    hits, checked = [], 0
    extents = []                                   # (object, x range, y range, z range) to test
    for o in m["objects"]:
        if o.get("type") == "brush" and "procedural" in o:
            # Custom mesh: test each triangle's bounds, not the whole mesh's. A merged decoration mesh
            # (e.g. the carved wall around the window) has a hole where the targets are, so its overall
            # bounds would always overlap the envelope.
            x, y, z = (float(t) for t in o["location"].split(","))
            sx, sy, sz = (float(t) * map_scale for t in o["scale"].split(","))  # vertices get MapScale again
            for sec in o["procedural"]:
                vs = [[float(t) for t in v["location"].split(",")] for v in sec["vertices"]]
                for k in range(0, len(sec["indices"]), 3):
                    tri = [vs[i] for i in sec["indices"][k:k + 3]]
                    extents.append((o, (x + min(v[0] for v in tri) * sx, x + max(v[0] for v in tri) * sx),
                                    (y + min(v[1] for v in tri) * sy, y + max(v[1] for v in tri) * sy),
                                    (z + min(v[2] for v in tri) * sz, z + max(v[2] for v in tri) * sz)))
            continue
        elif o.get("type") == "brush":
            x, y, z = (float(t) for t in o["location"].split(","))
            sx, sy, sz = (float(t) * 100 for t in o["scale"].split(","))
            ra, rb, rc = (float(t) for t in o.get("rotation", "0, 0, 0").split(","))
            if rb or rc:                           # not calibrated: use a sphere around the box
                rad = (sx * sx + sy * sy + sz * sz) ** 0.5
                xs, ys, zs = (x - rad, x + rad), (y - rad, y + rad), (z - rad, z + rad)
            else:                                  # a: clockwise within the wall, pivot at the corner
                c, s_ = math.cos(math.radians(ra)), math.sin(math.radians(ra))
                pts = [(ly * c + lz * s_, -ly * s_ + lz * c) for ly in (0, sy) for lz in (0, sz)]
                xs = (x, x + sx)
                ys = (y + min(p[0] for p in pts), y + max(p[0] for p in pts))
                zs = (z + min(p[1] for p in pts), z + max(p[1] for p in pts))
        elif o.get("type") == "prop":
            x, y, z = (float(t) for t in o["location"].split(","))
            xs, ys, zs = (x - PROP_HALF, x + PROP_HALF), (y - PROP_HALF, y + PROP_HALF), (z - PROP_HALF, z + PROP_HALF)
        else:
            continue
        extents.append((o, xs, ys, zs))
    hit_ids, checked_ids = set(), set()
    for o, xs, ys, zs in extents:
        if min(xs) >= back or min(xs) <= EYE_X + 1:
            continue
        near_x = max(min(xs), EYE_X + 1)
        pts = [project(xx, yy, zz) for xx in (near_x, max(xs)) for yy in ys for zz in zs]
        py0, py1 = min(q[0] for q in pts), max(q[0] for q in pts)
        pz0, pz1 = min(q[1] for q in pts), max(q[1] for q in pts)
        checked_ids.add(id(o))
        if py0 < ty1 and py1 > ty0 and pz0 < tz1 and pz1 > tz0 and id(o) not in hit_ids:
            hit_ids.add(id(o))
            hits.append((o.get("name"), o["location"], o["scale"], o.get("group")))
    checked = len(checked_ids)
    name = path.replace("\\", "/").split("/")[-1][:-4]
    status = "OK" if not hits else f"{len(hits)} OVERLAP(S)"
    print(f"  {name:32} {checked:4} objects in front of the targets checked: {status}")
    for h in hits[:5]:
        print("     ", h)
    bad += bool(hits)
sys.exit(1 if bad else 0)
