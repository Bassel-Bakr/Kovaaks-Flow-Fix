"""Build "Flow Fix Courtyard Test" (2026-09-24): Flow Fix Overflick in the window look, inside the palace courtyard
the user picked from the design workflow (the judge's merge: the lean "Court of Appearances" with the authentic
concept's skyline heights and pool).

The court geometry comes from courtyard/final_geo.py (the workflow's code, kept as it was checked): a paved court
with a navy pool, a dark grey crenellated palace wall, a red palm-column portico on each side, two battered corner
towers cut by the screen edge, grey palm stencils and distant pyramids. 18 objects: 10 blocks and 8 custom meshes.
It repaints two slots, as the user approved: group 0 wall from dark umber to palace grey 5d6066 (the sign outlines
turn dark grey too), and the free group 1 ceiling to the paving grey 77736b.

The user also asked for the workflow's "authentic" concept to compare (python courtyard_test.py authentic): a long
palace front with an eight-column palm portico and doorways, a crenellated enclosure wall and the pyramid field. It
keeps every existing slot and only repaints the free group 1 ceiling as mud-brick paving (5a534b).

Usage: python courtyard_test.py [authentic]
       (writes test_out/Flow Fix Courtyard Test.sce, or Flow Fix Courtyard Authentic.sce; installs nothing)
"""
import copy
import json
import sys
from pathlib import Path

import build

sys.path.insert(0, str(Path(__file__).with_name("courtyard")))
import authentic_geo as A  # noqa: E402
import final_geo as G  # noqa: E402

GROUP_BASE = 100                   # editor groups for the court pieces, one per piece


from court_export import export, pure  # noqa: E402


def set_slot(m, group, surface, tint, fullbright):
    m["materialSets"][group][surface] = pure(tint, fullbright)


AUTHENTIC = len(sys.argv) > 1 and sys.argv[1] == "authentic"
specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = copy.deepcopy(next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick"))
spec["scenario_name"] = "Flow Fix Courtyard Authentic" if AUTHENTIC else "Flow Fix Courtyard Test"
spec["description"] = ("Look test: Flow Fix Overflick in the window look, inside an Egyptian palace courtyard "
                       "(portico, towers, pool, palms, pyramids). Compare FPS with Flow Fix Overflick.")
import egypt  # noqa: E402

if AUTHENTIC:                      # the window look without the judge's court, which is now part of the look
    look = egypt.WINDOW_LOOK
    egypt.WINDOW_LOOK = dict(look, COURTYARD=False)
try:
    path, errors, warns = build.build(spec, "test_out")      # the window look is the default
finally:
    if AUTHENTIC:
        egypt.WINDOW_LOOK = look
assert not errors, errors
if not AUTHENTIC:                  # the judge's court comes with the window look now
    print(f"{path}: window look with the courtyard")
    sys.exit(0)
m = json.loads(build.parse(path)["map"])

template = next(o for o in m["objects"] if o.get("name") == "DefaultNoCollision" and "procedural" not in o)
if AUTHENTIC:                      # fitted to the built Overflick window (same geometry as this test)
    L = A.layout(str(path))       # the window-only build written just above
    objs = A.court(L)
    set_slot(m, *A.MUD, *A.SLOTS[A.MUD])
else:
    L = G.load("Overflick")
    objs = G.court(L)
    set_slot(m, *G.PALACE, *G.PAL[G.PALACE])
    set_slot(m, *G.PAVE, *G.PAL[G.PAVE])
court = [export(o, template, L["ms"], GROUP_BASE + i) for i, o in enumerate(objs)]
i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
m["objects"][i:i] = court
text = path.read_bytes().decode("ascii")
head = text[: text.index("[Map Data]") + len("[Map Data]")]
path.write_bytes((head + "\r\n" + "\r\n".join(json.dumps(m, indent=4).splitlines()) + "\r\n").encode("ascii"))
json.loads(build.parse(path)["map"])  # round-trip check
print(f"{path}: {len(court)} court objects ({sum(o['kind'] == 'box' for o in objs)} blocks, "
      f"{sum(o['kind'] == 'mesh' for o in objs)} meshes), "
      f"{sum(len(s['indices']) // 3 for b in court for s in b.get('procedural', []))} mesh triangles")
