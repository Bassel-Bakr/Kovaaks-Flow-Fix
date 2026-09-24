"""Build "Flow Fix Egypt Test" (Overflick's drill inside the Egyptian room) into test_out/, and build all 13
scenarios with the Egypt look into test_out/egypt_all/ so check_scene.py can confirm the layout is
safe for every spawn area.

Usage: python egypt_test.py
"""
import copy
import json
import shutil
from pathlib import Path

import build
import egypt

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
Path("test_out").mkdir(exist_ok=True)
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Egypt Test"
spec["arena"] = "egypt"
spec["fixed_spawn"] = True
spec["description"] = "Look test: Flow Fix Overflick inside the Egyptian window room."
path, errors, warns = build.build(spec, "test_out")
assert not errors, errors
m = json.loads(build.parse(path)["map"])
print(f"{path}: {sum(1 for o in m['objects'] if o.get('type') == 'brush')} brushes, "
      f"{len(m['materialSets'])} material groups")

# Mesh test: each sign one custom-mesh object (strokes + outline sections), dark blue text; decoration stays plain
# blocks (merging it into meshes gained nothing, 2026-09-24). All 13 scenarios are also built this way into
# test_out/egypt_mesh_all/ so check_scene.py can check them against every spawn area.
egypt.MESH_SIGNS, egypt.DARK_TEXT = True, True
mesh = copy.deepcopy(spec)
mesh["scenario_name"] = "Flow Fix Mesh Test"
mesh["description"] = ("Test: every sign is one custom-mesh object (dark blue, outlined); the decoration is plain "
                       "blocks. Compare FPS with Flow Fix Overflick.")
path, errors, warns = build.build(mesh, "test_out")
assert not errors, errors
mm = json.loads(build.parse(path)["map"])
print(f"{path}: {sum(1 for o in mm['objects'] if o.get('type') == 'brush')} brushes, "
      f"{sum(1 for o in mm['objects'] if 'procedural' in o)} custom meshes")
meshout = Path("test_out/egypt_mesh_all")
shutil.rmtree(meshout, ignore_errors=True)
meshout.mkdir()
for s in specs:
    s = copy.deepcopy(s)
    s["arena"] = "egypt"
    _, errors, _ = build.build(s, meshout)
    assert not errors, (s["scenario_name"], errors)

# Window test (user, 2026-09-24): only the window in a plain sandstone wall, inscriptions on the pilasters.
# All 13 are built the same way into test_out/egypt_window_all/ for check_scene.py.
egypt.WINDOW_ONLY = True
egypt.WINDOW_HEAD, egypt.WINDOW_LIONS = "top", True   # the user's pick from the mockups (option B with lions)
egypt.LINTEL_MIRROR = True                            # the user's pick: the welcome line mirrored from the centre
egypt.STENCIL_ART = True           # the user's pick (2026-09-24): stencil head and lions, no prop backing behind them
egypt.COURTYARD = True             # the user's pick (2026-09-24): the palace courtyard around the window
win = copy.deepcopy(spec)
win["scenario_name"] = "Flow Fix Window Test"
win["description"] = ("Look test: the Egyptian window, a pharaoh's head on the cornice and two lions, the inscriptions "
                      "carved on the lintel and pilasters. Compare FPS with Flow Fix Overflick in one session.")
path, errors, warns = build.build(win, "test_out")
assert not errors, errors
mw = json.loads(build.parse(path)["map"])
print(f"{path}: {sum(1 for o in mw['objects'] if o.get('type') == 'brush')} brushes, "
      f"{sum(1 for o in mw['objects'] if 'procedural' in o)} custom meshes")
winout = Path("test_out/egypt_window_all")
shutil.rmtree(winout, ignore_errors=True)
winout.mkdir()
for s in specs:
    s = copy.deepcopy(s)
    s["arena"] = "egypt"
    _, errors, _ = build.build(s, winout)
    assert not errors, (s["scenario_name"], errors)
egypt.WINDOW_ONLY = False
egypt.WINDOW_HEAD, egypt.WINDOW_LIONS, egypt.LINTEL_MIRROR = None, False, False
egypt.STENCIL_ART = False
egypt.COURTYARD = False
egypt.MESH_SIGNS, egypt.DARK_TEXT = False, False
print(f"all {len(specs)} scenarios built with the mesh look in {meshout} and the window look in {winout}")

# FPS material test: the same room with flat colours instead of textures
import egypt
egypt.FLAT = True
flat = copy.deepcopy(spec)
flat["scenario_name"] = "Flow Fix Egypt Test FLAT"
flat["description"] = "FPS test: Flow Fix Egypt Test with flat colours instead of textured stone."
path, errors, warns = build.build(flat, "test_out")
assert not errors, errors
egypt.FLAT = False
print(f"{path}: flat-colour copy")

allout = Path("test_out/egypt_all")
shutil.rmtree(allout, ignore_errors=True)
allout.mkdir()
for s in specs:
    s = copy.deepcopy(s)
    s["arena"] = "egypt"
    _, errors, _ = build.build(s, allout)
    assert not errors, (s["scenario_name"], errors)
print(f"all {len(specs)} scenarios built with the Egypt look in {allout}")
