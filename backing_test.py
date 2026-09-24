"""Build a backing test (2026-09-24): the Stencil Test with one prop behind the pharaoh's head and each lion.

Themes repaint every brush but not props, so a dark prop behind the stencil art stays dark in every theme and shows
through the art's holes. The prop's native size and pivot are unknown: the first try uses the scale and rotation an
installed map gives it, centred on each piece, and the user reports how it lands.

Usage: python backing_test.py [prop] [scale] [rotation]
       default: Sandstorm "0.032871, 0.0243, 0.001414" "0, 90, 0" (as in the installed map Geometry Dash Lvl 1)
Writes test_out/Flow Fix Backing Test.sce.
"""
import copy
import json
import sys
from pathlib import Path

import build
import egypt

PROP = sys.argv[1] if len(sys.argv) > 1 else "Sandstorm"
SCALE = sys.argv[2] if len(sys.argv) > 2 else "0.032871, 0.0243, 0.001414"
ROT = sys.argv[3] if len(sys.argv) > 3 else "0, 90, 0"
X = -3000.0                        # 40 units behind the stencil plates (their back is at x = -3040)

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Backing Test"
spec["arena"] = "egypt"
spec["description"] = f"Backing test: the Stencil Test with the prop {PROP} behind the pharaoh's head and each lion."
egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY = True, True, True
egypt.WINDOW_HEAD, egypt.WINDOW_LIONS, egypt.LINTEL_MIRROR, egypt.STENCIL_ART = "top", True, True, True
try:
    path, errors, warns = build.build(spec, "test_out")
finally:
    egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY = False, False, False
    egypt.WINDOW_HEAD, egypt.WINDOW_LIONS, egypt.LINTEL_MIRROR, egypt.STENCIL_ART = None, False, False, False
assert not errors, errors

m = json.loads(build.parse(path)["map"])
centres = []
for o in m["objects"]:           # the head and the lions: the stencil meshes standing clear of the wall
    if "procedural" not in o or not o.get("materialSets"):
        continue
    x, y, z = (float(t) for t in o["location"].split(","))
    vs = [[float(t) for t in v["location"].split(",")] for sec in o["procedural"] for v in sec["vertices"]]
    xs = [x + v[0] * egypt.arena.MAP_SCALE for v in vs]
    if max(xs) - min(xs) > egypt.STENCIL_T + 0.5:  # signs are 14 deep; the stencil plates are 6
        continue
    ys = [y + v[1] * egypt.arena.MAP_SCALE for v in vs]
    zs = [z + v[2] * egypt.arena.MAP_SCALE for v in vs]
    centres.append(((min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
assert len(centres) == 3, centres
props = [{"location": f"{X:.6f}, {cy:.6f}, {cz:.6f}", "name": PROP,
          "rotation": ", ".join(f"{float(v):.6f}" for v in ROT.split(",")),
          "scale": ", ".join(f"{float(v):.6f}" for v in SCALE.split(",")), "type": "prop"} for cy, cz in centres]
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = props
text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {PROP} x{len(props)} at", [(round(a), round(b)) for a, b in centres])
