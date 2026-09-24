"""Sculpt the pharaoh's bust and write pharaoh_statue.json (user, 2026-09-25: make the head smooth like the lions).

The bust follows the old pixel art (egypt_glyphs.json "pharaoh", 44 x 40 pixels of 7 units, about 300 x 280) and
Tutankhamun's mask: a golden face with painted lapis eyes, brows and mouth, ears, a straight royal beard with gold
braid bands, a nemes headcloth in lapis and gold stripes (the dome, the side flaps flaring down behind the ears and
the two lappets hanging in front of the shoulders) and a broad collar in concentric lapis and gold bands. No cobra
or vulture on the brow: the user's rule against religious symbols.

The back is cut flat: egypt.py stands the bust just in front of the cornice, on the lintel (WINDOW_HEAD
"front_lintel" with HEAD_SCULPT). Bust coordinates, in map units: x from the front (the tip of the nose, 0) back to
the flat back (about 150), y across, z up from the bottom of the collar (0).

Usage: python make_pharaoh.py   (the tools are in sculpt.py)
"""
import math
from pathlib import Path

from sculpt import cone, ellipsoid, pair, rbox, smin, surface_nets, union, write

CELL = 7.0                          # the stripes are 14 units: two cells each; their edges are cut exactly
DEPTH = 150.0                       # from the flat back to the front plane the parts are measured from
STRIPE = 14.0                       # nemes stripe height


def at(fwd, y, z):
    """A point given as its distance in front of the flat back."""
    return (DEPTH - fwd, y, z)


FACE = [
    ellipsoid(at(86, 0, 160), (42, 48, 64)),                     # face and forehead, in front of the nemes
    ellipsoid(at(86, 0, 128), (38, 36, 30)),                     # jaw and cheeks
    cone(at(124, 0, 178), at(136, 0, 150), 6, 10),               # nose
    *pair(lambda s: ellipsoid(at(72, 48 * s, 165), (12, 8, 18))),      # ears
    ellipsoid(at(60, 0, 105), (38, 36, 45)),                     # neck
]
NEMES = [
    ellipsoid(at(42, 0, 205), (62, 80, 76)),                     # the headcloth over the crown, behind the face
    *pair(lambda s: ellipsoid(at(48, 80 * s, 175), (40, 28, 46))),     # side flaps, flaring out ...
    *pair(lambda s: ellipsoid(at(40, 108 * s, 110), (34, 26, 50))),    # ... and down behind the ears
    *pair(lambda s: rbox(at(70, 70 * s, 105), (12, 17, 62), 6)),       # lappets in front of the shoulders
]
BEARD = [cone(at(106, 0, 108), at(104, 0, 50), 11, 12)]
COLLAR = [ellipsoid(at(24, 0, 88), (28, 150, 88))]
GROUPS = {"face": union(FACE, 10), "nemes": union(NEMES, 14), "beard": union(BEARD, 1), "collar": union(COLLAR, 1)}


def field(x, y, z):
    d = min(GROUPS["face"](x, y, z), GROUPS["beard"](x, y, z))
    d = smin(d, GROUPS["nemes"](x, y, z), 5.0)
    d = smin(d, GROUPS["collar"](x, y, z), 5.0)
    return max(d, x - DEPTH, -z)                                 # flat back, flat bottom


def colour(x, y, z):
    part = min(GROUPS, key=lambda k: GROUPS[k](x, y, z))
    fwd = DEPTH - x
    if part == "face":
        eye = ((abs(y) - 19) / 11) ** 2 + ((z - 172) / 4.5) ** 2 <= 1 and fwd > 100
        brow = 181 <= z - 0.004 * (abs(y) - 19) ** 2 <= 188 and 7 <= abs(y) <= 31 and fwd > 100
        mouth = 136 <= z <= 140 and abs(y) <= 13 and fwd > 100
        return "lapis" if eye or brow or mouth else "gold"
    if part == "nemes":
        return "lapis" if int(z // STRIPE) % 2 == 0 else "gold"
    if part == "beard":
        return "gold" if int(z // 12) % 3 == 0 else "lapis"
    return "lapis" if int(math.hypot(y, z - 120) // 15) % 2 == 0 else "gold"      # collar bands


if __name__ == "__main__":
    verts, normals, tris = surface_nets(field, colour, (-8.0, -160.0, -5.0), (DEPTH + 5, 160.0, 290.0), CELL,
                                        hidden=lambda *t: all(v[0] > DEPTH - 0.5 for v in t))   # the flat back
    write(Path(__file__).with_name("pharaoh_statue.json"),
          "Made by make_pharaoh.py. Bust coordinates in map units: x back from the nose, y across, z up.",
          CELL, verts, normals, tris)
