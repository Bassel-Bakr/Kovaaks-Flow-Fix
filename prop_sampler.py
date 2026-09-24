"""Build "Flow Fix Prop Sampler": every candidate prop in two labelled rows (by order), so the user can
say which ones render opaque and would work as a frame. Some props render see-through (user report).

Rows sit above and below the panel, outside every spawn area. Scales come from installed maps, shrunk
where the installed scale was room-sized. JumpPad and Teleporter are left out (they may affect gameplay).

Usage: python prop_sampler.py   (writes test_out/Flow Fix Prop Sampler.sce)
"""
import copy
import json
from pathlib import Path

import build

TOP = [("Column", "0.1, 0.1, 0.5"), ("Crate", "0.2, 0.2, 0.2"), ("Barrel", "0.37, 0.37, 0.37"),
       ("Container", "0.225, 0.225, 0.225"), ("Ledge", "0.68, 0.68, 0.68"), ("Arch", "0.68, 0.68, 0.68"),
       ("Doorway", "0.235, 0.235, 0.235"), ("HellSingleDoorFrame", "0.3, 0.3, 0.3"),
       ("Fence", "0.335, 0.335, 0.335"), ("Window", "0.2375, 0.2375, 0.228"), ("Banner", "0.3, 0.3, 0.3")]
BOTTOM = [("BannerB", "0.5, 0.5, 0.5"), ("Signage", "0.66, 0.66, 0.66"), ("AnimeTilesStraight", "0.5, 0.5, 0.5"),
          ("AnimeWoodenPlank", "0.5, 0.5, 0.19"), ("CookieFloorSquaredTiles", "0.06, 0.06, 0.18"),
          ("CookieFloorGingerbread", "0.3, 0.3, 0.3"), ("TimmyContainer", "0.66, 0.66, 0.66"),
          ("TimmyConsole", "0.12, 0.12, 0.12"), ("TimmyButton", "0.3, 0.3, 0.3"), ("TimmyArrow", "0.5, 0.5, 0.5"),
          ("Tree", "0.44, 0.44, 0.44")]
X = -2920.0

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Prop Sampler"
spec["arena"] = True
spec["description"] = ("Prop sampler, left to right. Top: " + ", ".join(f"{i + 1} {n}" for i, (n, _) in enumerate(TOP))
                       + ". Bottom: " + ", ".join(f"{i + 12} {n}" for i, (n, _) in enumerate(BOTTOM))
                       + ". Which are opaque?")
Path("test_out").mkdir(exist_ok=True)
path, errors, warns = build.build(spec, "test_out")
assert not errors, errors

m = json.loads(build.parse(path)["map"])
panel = next(o for o in m["objects"] if o.get("type") == "brush" and o.get("materialSets")
             and o["materialSets"][0] == {"group": 1, "surface": "wall"})
_, y0, z0 = (float(t) for t in panel["location"].split(","))
_, sy, sz = (float(t) for t in panel["scale"].split(","))
y1, z1 = y0 + sy * 100, z0 + sz * 100


def row(items, z):
    n = len(items)
    ys = [y0 + (y1 - y0) * (i + 0.5) / n for i in range(n)]
    return [{"location": f"{X:.6f}, {y:.6f}, {z:.6f}", "name": name, "rotation": "0.000000, 0.000000, 0.000000",
             "scale": ", ".join(f"{float(v):.6f}" for v in scale.split(",")), "type": "prop"}
            for (name, scale), y in zip(items, ys)]


props = row(TOP, z1 + 250) + row(BOTTOM, z0 - 250)
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = props
text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {len(props)} props")
print(spec["description"])
