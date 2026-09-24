"""Build "Flow Fix Backing Sampler" (2026-09-24): the Stencil Test plus a numbered row of props above the gateway.

The user wants an always-dark backing behind the pharaoh's head and the lions. Themes repaint every brush, but props
keep their own look, so one of these props squashed into a plate would stay dark in every theme. The user picks the
plainest dark one under a solid-colour theme. Scales come from installed maps (the props' native sizes are unknown).

Usage: python backing_sampler.py   (writes test_out/Flow Fix Backing Sampler.sce)
"""
import copy
import json
from pathlib import Path

import build
import egypt

CANDIDATES = [("TimmyContainer", "0.4, 0.4, 0.4"), ("TimmyConsole", "0.12, 0.12, 0.12"),
              ("TimmyButton", "0.3, 0.3, 0.3"), ("HellSingleDoorFrame", "0.3, 0.3, 0.3"),
              ("Column", "0.1, 0.1, 0.3"), ("Doorway", "0.235, 0.235, 0.235"), ("Ledge", "0.5, 0.5, 0.5"),
              ("Signage", "0.5, 0.5, 0.5"), ("McCoy", "0.312, 0.312, 0.312"), ("Barrel", "0.3, 0.3, 0.3")]
X, Z = -3100.0, 1600.0             # in front of the gateway plane, above the head (which ends at about z 1320)

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Backing Sampler"
spec["arena"] = "egypt"
spec["description"] = ("Backing sampler, left to right above the gateway: "
                       + ", ".join(f"{i + 1} {n}" for i, (n, _) in enumerate(CANDIDATES))
                       + ". Which is the plainest dark one under a solid-colour theme?")
egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY = True, True, True
egypt.WINDOW_HEAD, egypt.WINDOW_LIONS, egypt.LINTEL_MIRROR, egypt.STENCIL_ART = "top", True, True, True
try:
    path, errors, warns = build.build(spec, "test_out")
finally:
    egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY = False, False, False
    egypt.WINDOW_HEAD, egypt.WINDOW_LIONS, egypt.LINTEL_MIRROR, egypt.STENCIL_ART = None, False, False, False
assert not errors, errors

m = json.loads(build.parse(path)["map"])
n = len(CANDIDATES)
props = [{"location": f"{X:.6f}, {-2250 + 4500 * i / (n - 1):.6f}, {Z:.6f}", "name": name,
          "rotation": "0.000000, 0.000000, 0.000000",
          "scale": ", ".join(f"{float(v):.6f}" for v in scale.split(",")), "type": "prop"}
         for i, (name, scale) in enumerate(CANDIDATES)]
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = props
text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {len(props)} props")
print(spec["description"])
