"""Build "Flow Fix Rotation Test": learn how KovaaK's rotates brushes, before building glyphs from strokes.

Flow Fix Overflick in the plain base room, plus four bars in a row above the target area:
  bar 1: rotation "0, 0, 0" (reference)
  bar 2: "30, 0, 0"    bar 3: "0, 30, 0"    bar 4: "0, 0, 30"
Each bar is 300 long (screen horizontal), 24 tall, 12 deep, anchored (location) at its lower-left-front
corner. Behind each rotated bar is an unrotated "ghost" copy (blue); an orange marker sits on the anchor;
1-4 black dots under each bar number it.

What the screenshot shows:
- The value that tilts its bar within the wall plane is the rotation glyph strokes need (about the axis
  pointing from the player to the wall). Its tilt direction gives the sign.
- A bar that gets shorter, or half-sinks into the wall, turns about the vertical axis.
- A bar that barely changes turns about the horizontal axis along its own length.
- Whether the rotated bar still touches its orange marker shows the pivot: corner (touches) or centre.

Usage: python rotation_test.py   (writes test_out/Flow Fix Rotation Test.sce)
"""
import copy
import json
from pathlib import Path

import build

WALL = -2900.0
Z = 850.0                   # anchor height: above the target area (spawn top ~540)
YS = (-1500.0, -700.0, 100.0, 900.0)
ROTS = ("0.000000, 0.000000, 0.000000", "30.000000, 0.000000, 0.000000",
        "0.000000, 30.000000, 0.000000", "0.000000, 0.000000, 30.000000")
L, H, D = 300.0, 24.0, 12.0


def mat(tint):
    return {"material": "MI_WA_PureColor", "pack": "Default",
            "properties": [{"name": "Tint", "value": tint}, {"name": "Scale", "value": 1.0},
                           {"name": "Roughness", "value": 0.9}, {"name": "Metallic", "value": 0.0},
                           {"name": "FullBright", "value": 0.6}]}


specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Rotation Test"
spec["arena"] = False
spec["fixed_spawn"] = True
spec["description"] = ("Rotation calibration. Bars 1-4 (count the dots): none, 30 in the 1st value, 30 in the 2nd, "
                       "30 in the 3rd. Blue = unrotated ghost, orange = anchor. Screenshot with no theme.")
Path("test_out").mkdir(exist_ok=True)
path, errors, warns = build.build(spec, "test_out")
assert not errors, errors

m = json.loads(build.parse(path)["map"])
# group 1 becomes the test palette: wall = black bars, ceiling = blue ghosts, ground = orange markers
m["materialSets"][1] = {"wall": mat("111111ff"), "ceiling": mat("3a7bd5ff"), "ground": mat("ff8c1aff"),
                        "ramp": mat("111111ff")}
wall = next(o for o in m["objects"] if o.get("type") == "brush" and o["location"].startswith("-2899.999512"))


def brush(x0, y0, z0, sx, sy, sz, surface, rotation="0.000000, 0.000000, 0.000000", group=90):
    b = copy.deepcopy(wall)
    b.pop("group", None)
    b.update({"name": "DefaultNoCollision", "location": f"{x0:.6f}, {y0:.6f}, {z0:.6f}",
              "scale": f"{sx / 100:.6f}, {sy / 100:.6f}, {sz / 100:.6f}", "rotation": rotation, "group": group,
              "materialSets": [{"group": 1, "surface": surface} for _ in range(6)]})
    return b


added = []
for n, (y, rot) in enumerate(zip(YS, ROTS), start=1):
    g = 90 + n
    if n > 1:
        added.append(brush(WALL - 4, y, Z, 4, L, H, "ceiling", group=g))            # ghost, unrotated
    added.append(brush(WALL - 4 - D, y, Z, D, L, H, "wall", rot, group=g))           # the test bar
    added.append(brush(WALL - 4 - D - 6, y - 10, Z - 10, 6, 20, 20, "ground", group=g))  # anchor marker
    for k in range(n):                                                                # number dots
        added.append(brush(WALL - 10, y + k * 45, Z - 90, 6, 25, 25, "wall", group=g))
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = added

text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])
print(f"{path}: {len(added)} calibration blocks")
