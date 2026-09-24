"""Build "Flow Fix Frame Test": the arena with the brush frame replaced by a frame of Container props.

Why props: player themes repaint brushes by surface type, so under a flat theme the brush frame vanished.
Props keep their own look (confirmed in game). The user picked Container (teal shipping container) from
the prop sampler because it stays opaque and clearly visible even on a white theme.

The prop's native size and pivot are unknown (estimated from a screenshot: roughly 600 units per unit of
scale on each axis), so each side is a row of overlapping copies rather than one stretched piece:
overlap reads as a solid bar whatever the true size is, while a gap would show.

Usage: python frame_test.py   (writes test_out/Flow Fix Frame Test.sce)
"""
import copy
import json
from pathlib import Path

import build

PROP = "Container"
X = -2920.0                               # just in front of the wall face (-2900)
OFFSET = 120.0                            # distance from the panel edge to the bar's centre line
HORIZONTAL = "0.100000, 0.225000, 0.110000"  # top and bottom bars: long along y, short in z
VERTICAL = "0.100000, 0.110000, 0.225000"    # left and right bars: long along z, short in y
STEP_Y, STEP_Z = 110.0, 110.0             # smaller than the expected piece length, so copies overlap

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Frame Test"
spec["arena"] = True
spec["description"] = ("Frame test: a frame of Container props around the panel. Check it with and without "
                       "your themes, and that it never touches a target.")
Path("test_out").mkdir(exist_ok=True)
path, errors, warns = build.build(spec, "test_out")
assert not errors, errors

m = json.loads(build.parse(path)["map"])
panel = next(o for o in m["objects"] if o.get("type") == "brush" and o.get("materialSets")
             and o["materialSets"][0] == {"group": 1, "surface": "wall"})
_, y0, z0 = (float(t) for t in panel["location"].split(","))
_, sy, sz = (float(t) for t in panel["scale"].split(","))
y1, z1 = y0 + sy * 100, z0 + sz * 100

# drop the brush frame (group 1 "ceiling"); the props replace it
m["objects"] = [o for o in m["objects"]
                if not (o.get("type") == "brush" and o.get("materialSets")
                        and o["materialSets"][0] == {"group": 1, "surface": "ceiling"})]


def run(a, b, step):
    n = max(2, int((b - a) // step) + 2)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def prop(scale, y, z):
    return {"location": f"{X:.6f}, {y:.6f}, {z:.6f}", "name": PROP,
            "rotation": "0.000000, 0.000000, 0.000000", "scale": scale, "type": "prop"}


ya, yb = y0 - OFFSET, y1 + OFFSET  # horizontal bars span the corners too
props = [prop(HORIZONTAL, y, z1 + OFFSET) for y in run(ya, yb, STEP_Y)]
props += [prop(HORIZONTAL, y, z0 - OFFSET) for y in run(ya, yb, STEP_Y)]
props += [prop(VERTICAL, y0 - OFFSET, z) for z in run(z0, z1, STEP_Z)]
props += [prop(VERTICAL, y1 + OFFSET, z) for z in run(z0, z1, STEP_Z)]
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = props

text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {len(props)} {PROP} props; panel y {y0:.0f}..{y1:.0f}, z {z0:.0f}..{z1:.0f}")
