"""Build "Flow Fix FPS Probe": Flow Fix Overflick plus one small carved block, nothing else (2026-09-24).

The Egypt room costs about 0.23 ms per frame whatever was removed or merged (decoration merged into meshes, big
pieces as blocks, even the walls, floor and ceiling deleted). The only change that moved it was turning 437
rotated sign blocks into meshes. The probe tests whether the cost is fixed, paid as soon as anything stands on
the wall: read it next to Flow Fix Overflick and Flow Fix Mesh Test in one session. The block uses the base
map's own material (no palette change) and sits in the top-left corner of the wall, clear of every target.

Usage: python fps_probe.py   (writes test_out/Flow Fix FPS Probe.sce)
"""
import copy
import json
from pathlib import Path

import build
import egypt


def add_probe(m, spawn_volumes, max_target_radius):
    wall = next(o for o in m["objects"] if o.get("type") == "brush" and o["location"].startswith("-2899.999512"))
    s = egypt.Scene(wall)
    s.section = "probe block"
    s.box(egypt.WALL - egypt.BODY_D, egypt.WALL, -2050, -2000, 950, 1000, egypt.SANDSTONE)   # 50 x 50, 14 deep
    i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
    m["objects"][i:i] = s.boxes
    return s.counts


specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix FPS Probe"
spec["arena"] = "egypt"                  # routed to add_probe below
spec["fixed_spawn"] = True
spec["description"] = ("FPS test: Flow Fix Overflick plus one small block on the wall. Compare FPS with Flow Fix "
                       "Overflick and Flow Fix Mesh Test in one session.")
real, egypt.add_egypt = egypt.add_egypt, add_probe
try:
    path, errors, warns = build.build(spec, "test_out")
finally:
    egypt.add_egypt = real
assert not errors, errors
m = json.loads(build.parse(path)["map"])
print(f"{path}: {sum(1 for o in m['objects'] if o.get('type') == 'brush')} brushes")
