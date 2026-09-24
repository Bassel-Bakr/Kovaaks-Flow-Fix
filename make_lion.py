"""Sculpt the guardian lion statue and write lion_statue.json (user, 2026-09-24: "sculpt a smooth statue").

The lion is a signed distance field: ellipsoids and tapered capsules for the body, rump, haunches, chest, mane,
head, muzzle, ears, legs, paws and tail, joined with a smooth minimum so they blend like carved stone, with the eyes
and nostrils cut in. Naive surface nets turn the field into quads, and each vertex takes its normal from the field's
gradient, so the statue shades smoothly. Each face takes the colour of the nearer group of parts: the mane and the
tail tuft are the accent (ochre), the rest is the body (navy), as in the old profile art.

The pose follows that art (egypt_glyphs.json "lion", 58 x 28 pixels of 7 units): lying, forelegs stretched forward,
head raised, tail curled up over the rump. Lion coordinates, in map units: f from the front of the forepaws (0) back
to the rump (about 395), s across (the statue is symmetric apart from the tail, which leans to +s), z up from the
plinth top (0). egypt.py places it with its head toward the player (LION_TURNED).

The tools (primitives, smooth union, surface nets) are in sculpt.py.

Usage: python make_lion.py
"""
from pathlib import Path

from sculpt import cone, chain, ellipsoid, pair, smin, surface_nets, write

CELL = 9.0                          # surface-net cell size: about 2.5 screen pixels at 1080p from the spawn
BLEND = 16.0                        # smooth-minimum radius between body parts
MANE_BLEND = 8.0                    # between the mane and the body: less, so the mane stays a distinct mass


# ---- the parts ------------------------------------------------------------------------------------------------
BODY = [
    ellipsoid((255, 0, 58), (135, 56, 56)),                  # torso, lying low
    ellipsoid((150, 0, 66), (62, 52, 62)),                   # chest
    ellipsoid((342, 0, 56), (52, 48, 56)),                   # rump
    *pair(lambda s: ellipsoid((328, 30 * s, 52), (62, 34, 52))),                      # haunches
    *pair(lambda s: cone((330, 48 * s, 34), (272, 54 * s, 13), 20, 13)),              # hind legs, folded
    *pair(lambda s: ellipsoid((262, 54 * s, 12), (44, 16, 12))),                      # hind paws, beside the body
    *pair(lambda s: cone((152, 30 * s, 44), (38, 30 * s, 17), 24, 17)),               # forelegs, stretched forward
    *pair(lambda s: ellipsoid((24, 30 * s, 14), (26, 21, 14))),                       # forepaws
    ellipsoid((66, 0, 146), (42, 40, 41)),                   # head, well out in front of the mane
    ellipsoid((28, 0, 128), (30, 25, 22)),                   # muzzle
    ellipsoid((32, 0, 111), (24, 19, 11)),                   # chin
    *pair(lambda s: ellipsoid((74, 28 * s, 190), (10, 9, 13))),                       # ears, out of the mane
    *chain([(300, 10, 104), (306, 12, 148), (322, 14, 178), (348, 15, 188), (366, 15, 174), (372, 15, 154)],
           10, 8),                                                                      # tail, curled up
]
ACCENT = [
    ellipsoid((106, 0, 128), (48, 76, 78)),                  # mane: a ruff starting just behind the face
    ellipsoid((160, 0, 104), (42, 64, 62)),                  # the mane running back over the shoulders
    *pair(lambda s: ellipsoid((66, 36 * s, 132), (26, 24, 44))),                     # ruff round the cheeks
    ellipsoid((94, 0, 78), (34, 48, 42)),                    # the mane's bib on the chest
    ellipsoid((373, 15, 142), (14, 13, 18)),                 # tail tuft
]
CUTS = [
    *pair(lambda s: ellipsoid((38, 19 * s, 152), (8, 7, 5))),                          # eyes
    *pair(lambda s: ellipsoid((-1, 7 * s, 134), (6, 4, 4))),                           # nostrils
    cone((2, -13, 119), (2, 13, 119), 3.5, 3.5),                                       # mouth
]


def body(x, y, z):
    b = BODY[0](x, y, z)
    for f in BODY[1:]:
        b = smin(b, f(x, y, z), BLEND)
    return b


def field(x, y, z):
    d = smin(body(x, y, z), min(f(x, y, z) for f in ACCENT), MANE_BLEND)
    for f in CUTS:
        d = max(d, -f(x, y, z))
    return max(d, -z)                                         # flat underside on the plinth


def colour(x, y, z):
    """The nearer group of parts: the mane and the tail tuft are the accent, the rest the body."""
    return "accent" if min(f(x, y, z) for f in ACCENT) < body(x, y, z) else "body"


if __name__ == "__main__":
    verts, normals, tris = surface_nets(field, colour, (-10.0, -90.0, -8.0), (410.0, 90.0, 205.0), CELL,
                                        hidden=lambda *t: all(v[2] < 0.5 for v in t))   # the underside, on the plinth
    write(Path(__file__).with_name("lion_statue.json"),
          "Made by make_lion.py. Lion coordinates in map units: f back from the forepaws, s across, z up.",
          CELL, verts, normals, {k: tris[k] for k in ("body", "accent")})
