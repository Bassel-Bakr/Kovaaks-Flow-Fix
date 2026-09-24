"""Build "Flow Fix Prop Test": the arena test plus sample props, to learn whether player themes repaint
props, and to see each prop's native size and pivot.

The props sit in a row above the panel, outside every spawn area, just in front of the target wall.
Their scales are ones that working maps already use.

Usage: python prop_test.py   (writes test_out/Flow Fix Prop Test.sce)
"""
import copy
import json
from pathlib import Path

import build

SAMPLES = [  # (prop name, y, scale "x, y, z") — scales copied from installed maps
    ("Column", -900.0, "0.062500, 0.062500, 0.514500"),
    ("Banner", -300.0, "0.062500, 2.175225, 0.027499"),
    ("Crate", 300.0, "0.201546, 0.201546, 0.201546"),
    ("Container", 900.0, "0.090500, 0.157849, 0.157849"),
]
X, Z = -2920.0, 950.0  # just in front of the wall (front face at x = -2900), well above the panel

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Prop Test"
spec["arena"] = True
spec["description"] = ("Prop test. Above the panel, left to right: Column, Banner, Crate, Container. "
                       "Check whether your theme repaints them.")
Path("test_out").mkdir(exist_ok=True)
path, errors, warns = build.build(spec, "test_out")
assert not errors, errors

p = build.parse(path)
m = json.loads(p["map"])
props = [{"location": f"{X:.6f}, {y:.6f}, {Z:.6f}", "name": name, "rotation": "0.000000, 0.000000, 0.000000",
          "scale": scale, "type": "prop"} for name, y, scale in SAMPLES]
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = props

text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {len(props)} props added")
