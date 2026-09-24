"""Check which scenarios can put a target off screen while the crosshair is on another target.

The view is centred on the crosshair, so a spawn area wider than the field of view lets two targets be
too far apart to see at once. For random pairs of spawn points (uniform inside the spawn volumes),
aim at the first and test whether the second projects inside the screen.

Usage: python check_view.py [folder]   (default: out)
"""
import glob
import json
import math
import random
import sys

import build

HFOV = 103.0                       # locked horizontal FOV in every flowfix scenario
ASPECT = 16 / 9                    # the user's screen
MARGIN = 0.9                       # count a target as off screen once it is past 90% of the half-screen
PLAYER = (-5999.999512, 0.0, 0.0)  # map units; MapScale cancels out of every angle
TAN_H = math.tan(math.radians(HFOV / 2))
TAN_V = TAN_H / ASPECT


def spawn_boxes(path):
    m = json.loads(build.parse(path)["map"])
    boxes = []
    for o in m["objects"]:
        if o.get("name") != "SpawnVolume":
            continue
        if not any(p["name"] == "TeamMask" and p["value"] == 2 for p in o["properties"]):
            continue
        x, y, z = (float(t) for t in o["location"].split(","))
        _, sy, sz = (float(t) for t in o["scale"].split(","))
        boxes.append((x, y, z, sy * 100, sz * 100))  # SpawnVolume half-extent = scale * 100 (confirmed in game)
    return boxes


def sample(boxes, rng):
    x, y, z, hy, hz = rng.choice(boxes)
    return (x, y + rng.uniform(-hy, hy), z + rng.uniform(-hz, hz))


def on_screen(aim, point):
    """Project point into a camera at PLAYER looking at aim (no roll, Z up)."""
    f = [a - p for a, p in zip(aim, PLAYER)]
    n = math.sqrt(sum(c * c for c in f))
    f = [c / n for c in f]
    r = [f[1], -f[0], 0.0]                      # right = forward x up
    rn = math.sqrt(r[0] ** 2 + r[1] ** 2)
    r = [c / rn for c in r]
    u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]]
    d = [a - p for a, p in zip(point, PLAYER)]
    zc = sum(a * b for a, b in zip(d, f))
    if zc <= 0:
        return False
    xs = sum(a * b for a, b in zip(d, r)) / zc
    ys = sum(a * b for a, b in zip(d, u)) / zc
    return abs(xs) <= MARGIN * TAN_H and abs(ys) <= MARGIN * TAN_V


def angles(p):
    dx, dy, dz = (a - b for a, b in zip(p, PLAYER))
    return math.degrees(math.atan2(dy, dx)), math.degrees(math.atan2(dz, math.hypot(dx, dy)))


rng = random.Random(1)
folder = sys.argv[1] if len(sys.argv) > 1 else "out"
print(f"screen: +-{HFOV / 2:.1f} deg horizontal, +-{math.degrees(math.atan(TAN_V)):.1f} deg vertical "
      f"(off screen = past {MARGIN:.0%} of that)")
for path in sorted(glob.glob(f"{folder}/*.sce")):
    boxes = spawn_boxes(path)
    corners = [(x, y + sy * hy, z + sz * hz) for x, y, z, hy, hz in boxes for sy in (-1, 1) for sz in (-1, 1)]
    yaw = [angles(c)[0] for c in corners]
    pitch = [angles(c)[1] for c in corners]
    off = sum(not on_screen(sample(boxes, rng), sample(boxes, rng)) for _ in range(20000)) / 20000
    name = path.replace("\\", "/").split("/")[-1][:-4]
    print(f"  {name:34} spawn area {max(yaw) - min(yaw):5.1f} x {max(pitch) - min(pitch):4.1f} deg   "
          f"pairs with one target off screen: {off:6.1%}")
