"""Render a flat front view of a built map's front wall (no theme) to PNG, for checking layouts.

Draws every brush facing the player, far to near, coloured by its material slot.
Usage: python preview_front.py "test_out/Flow Fix Egypt Test.sce" out.png [scale y0 y1 z0 z1]
"""
import json
import math
import sys

from PIL import Image, ImageDraw

import build

COLORS = {(0, "wall"): (217, 183, 138), (0, "ground"): (196, 161, 113), (0, "ceiling"): (234, 219, 182),
          (0, "ramp"): (154, 63, 34), (1, "wall"): (235, 228, 210), (1, "ground"): (43, 29, 18),
          (1, "ceiling"): (29, 77, 122), (1, "ramp"): (255, 231, 168)}
path, out = sys.argv[1], sys.argv[2]
SCALE = float(sys.argv[3]) if len(sys.argv) > 3 else 0.3        # pixels per map unit
Y0, Y1, Z0, Z1 = (float(v) for v in sys.argv[4:8]) if len(sys.argv) > 7 else (-2500, 2500, -1250, 1250)
parsed = build.parse(path)
m = json.loads(parsed["map"])
map_scale = float(next(l.split("=", 1)[1] for l in parsed["top"] if l.startswith("MapScale=")))


def tint(g, s):
    """The slot's own Tint from the map, so looks that repaint slots preview in their real colours."""
    try:
        v = next(q["value"] for q in m["materialSets"][g][s]["properties"] if q["name"] == "Tint")
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))
    except (KeyError, IndexError, StopIteration, TypeError):
        return COLORS.get((g, s), (255, 0, 255))


PALETTE = {(g, s): tint(g, s) for g in (0, 1) for s in ("wall", "ground", "ceiling", "ramp")}
img = Image.new("RGB", (int((Y1 - Y0) * SCALE), int((Z1 - Z0) * SCALE)), (40, 40, 40))
d = ImageDraw.Draw(img)
boxes = []
meshes = []
for o in m["objects"]:
    if o.get("type") != "brush" or not o.get("materialSets"):
        continue
    if "procedural" in o:                        # custom mesh: draw its player-facing triangles
        ox, oy, oz = (float(t) for t in o["location"].split(","))
        for sec, ms in zip(o["procedural"], o["materialSets"]):
            vs = [([float(t) * map_scale for t in v["location"].split(",")],
                   [float(t) for t in v["normal"].split(",")])
                  for v in sec["vertices"]]                   # the game multiplies vertices by MapScale again
            for k in range(0, len(sec["indices"]), 3):
                tri = [vs[i] for i in sec["indices"][k:k + 3]]
                if tri[0][1][0] < -0.5 and -3200 <= ox + tri[0][0][0] <= -2800:   # front wall only, as boxes
                    meshes.append((ox + tri[0][0][0], [(oy + p[1], oz + p[2]) for p, _ in tri],
                                   (ms["group"], ms["surface"])))
        continue
    x, y, z = (float(t) for t in o["location"].split(","))
    sx, sy, sz = (float(t) * 100 for t in o["scale"].split(","))
    if x < -3200 or x > -2800 or sx > 1000:        # only the front wall and what is carved on it
        continue
    ms = o["materialSets"][0]
    a = math.radians(float(o.get("rotation", "0, 0, 0").split(",")[0]))
    boxes.append((x, y, z, sy, sz, a, (ms["group"], ms["surface"])))
for x, y, z, sy, sz, a, slot in sorted(boxes, key=lambda b: -b[0]):   # far (large x) first
    c, s = math.cos(a), math.sin(a)                                 # clockwise within the wall
    pts = [(y + ly * c + lz * s, z - ly * s + lz * c) for ly, lz in ((0, 0), (sy, 0), (sy, sz), (0, sz))]
    d.polygon([((py - Y0) * SCALE, (Z1 - pz) * SCALE) for py, pz in pts], fill=PALETTE.get(slot, (255, 0, 255)))
for x, tri, slot in sorted(meshes, key=lambda t: -t[0]):
    d.polygon([((py - Y0) * SCALE, (Z1 - pz) * SCALE) for py, pz in tri], fill=PALETTE.get(slot, (255, 0, 255)))
for o in m["objects"]:                       # spawn volumes, outlined in red
    if o.get("name") == "SpawnVolume" and any(p["name"] == "TeamMask" and p["value"] == 2 for p in o["properties"]):
        _, y, z = (float(t) for t in o["location"].split(","))
        _, hy, hz = (float(t) * 100 for t in o["scale"].split(","))
        d.rectangle([(y - hy - Y0) * SCALE, (Z1 - z - hz) * SCALE, (y + hy - Y0) * SCALE, (Z1 - z + hz) * SCALE],
                    outline=(220, 40, 40))
img.save(out)
print(out, img.size)
