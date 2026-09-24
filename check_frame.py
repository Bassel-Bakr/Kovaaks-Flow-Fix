"""Check that no target can overlap the arena frame on screen.

For every spawn volume corner, take the largest target of the profiles allowed there, project its
outermost edge from the eye onto the wall plane, and measure the gap to the inner edge of the frame.

Usage: python check_frame.py [folder]   (default: out)
"""
import glob
import json
import sys

import arena
import build

folder = sys.argv[1] if len(sys.argv) > 1 else "out"
bad = 0
for path in sorted(glob.glob(f"{folder}/*.sce")):
    p = build.parse(path)
    m = json.loads(p["map"])
    frame = [o for o in m["objects"] if o.get("type") == "brush" and o["materialSets"]
             and o["materialSets"][0] == {"group": 1, "surface": "ceiling"}]
    name = path.replace("\\", "/").split("/")[-1][:-4]
    if not frame:
        print(f"  {name:32} no arena")
        continue
    ys, zs = [], []
    for o in frame:
        x, y, z = (float(t) for t in o["location"].split(","))
        _, sy, sz = (float(t) for t in o["scale"].split(","))
        ys += [y, y + sy * 100]
        zs += [z, z + sz * 100]
    # inner edges of the frame = the panel bounds
    panel = next(o for o in m["objects"] if o.get("type") == "brush" and o["materialSets"]
                 and o["materialSets"][0] == {"group": 1, "surface": "wall"})
    x, y0, z0 = (float(t) for t in panel["location"].split(","))
    _, sy, sz = (float(t) for t in panel["scale"].split(","))
    y1, z1 = y0 + sy * 100, z0 + sz * 100
    radius = {s["name"]: float(build.get_key(s["lines"], "MainBBRadius")) for s in p["sections"]
              if s["type"] == "Character Profile" and s["name"] != "Player"}
    gap = 1e9
    for o in m["objects"]:
        if o.get("name") != "SpawnVolume":
            continue
        props = {q["name"]: q["value"] for q in o["properties"]}
        if props["TeamMask"] != 2:
            continue
        r = max(radius.values()) if not props["PermittedCharacterProfiles"] else radius[props["PermittedCharacterProfiles"]]
        r /= arena.MAP_SCALE
        _, vy, vz = (float(t) for t in o["location"].split(","))
        _, hy, hz = (float(t) * arena.VOLUME_HALF for t in o["scale"].split(","))
        dz = arena.SPAWN_Z_OFFSET / arena.MAP_SCALE
        k = arena.PARALLAX
        gap = min(gap, y1 - k * (vy + hy + r), k * (vy - hy - r) - y0,
                  z1 - k * (vz + hz + dz + r), k * (vz - hz + dz - r) - z0)
    ok = gap > 0
    bad += not ok
    print(f"  {name:32} smallest gap between a target edge and the frame: {gap:6.1f} map units  {'OK' if ok else 'OVERLAP'}")
sys.exit(1 if bad else 0)
