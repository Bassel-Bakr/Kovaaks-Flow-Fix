"""Ancient Egyptian window room for Flow Fix scenarios (test build, 2026-09-23).

The user asked for an ancient Egyptian window look (sandstone room, hieroglyph walls, a bright opening)
built by carving shapes from geometry. Everything is Cube brushes, whose placement is confirmed
(location = minimum corner, scale 1 = 100 units). Raised shapes still read as shading under textured
player themes, which repaint brushes by surface type.

Layout (map units, before MapScale). X points from the player (x = -6000) to the target wall (x = -2900);
+y is screen right, +z is up.
- A thick front wall (120 deep) with the window opening: the panel where targets appear, sized with
  parallax and a clear margin (arena.window_bounds).
- A limestone frame, a torus bead, a sill, and pilasters with stepped papyrus capitals.
- A stepped, fluted cavetto cornice with a winged sun disk on the lintel.
- Registers of carved hieroglyphs, a khekher frieze along the top, and a panelled dado.
- Glyph bands and stone benches on the side walls, a blue ceiling with gold stars and stone beams,
  and a sunlight patch on the floor.

Nothing is placed where it could cover a target: check_scene.py verifies every block against the
projected target envelope.

Only two material groups exist (more crashed the game), so 8 surface slots carry the palette:
group 0: wall = sandstone masonry, ground = floor slabs, ceiling = limestone trim, ramp = red ochre paint
group 1: wall = window view, ground = glyph outline, ceiling = Egyptian blue paint, ramp = gold

Themes (2026-09-23): player themes repaint by surface type. Across the user's 149 themes, "ceiling" differs
from "wall" most often, so carving is painted on the ceiling type, with a 1-pixel outline on the floor type
behind it: a glyph stays readable when either differs from the wall (130 of 149 themes, up from 114).
Relief is 14 deep so it shades even when a theme paints everything the same.

Inscriptions are the user's own text (inscriptions.json, rendered by make_inscriptions.py).
"""
import copy
import json
import math
import sys
from pathlib import Path

import arena

WALL = arena.WALL_FRONT            # -2900
DEPTH = 120.0                      # thickness of the front wall around the window
FRONT = WALL - DEPTH               # -3020, the carved face
HALF_Y, HALF_Z = arena.HALF_Y, arena.HALF_Z   # 2500, 1250
ROOM_BACK, SLAB = arena.ROOM_BACK, arena.SLAB

SANDSTONE, FLOOR, LIME, OCHRE = (0, "wall"), (0, "ground"), (0, "ceiling"), (0, "ramp")
VIEW, OUTLINE, BLUE, GOLD = (1, "wall"), (1, "ground"), (1, "ceiling"), (1, "ramp")
BODY_D, OUTLINE_D = 14.0, 8.0      # relief depth of glyph bodies and of their outline
# Outlines: the user wants them (2026-09-23). Cutting from ~600 to ~370 blocks did not change the user's
# FPS drop (still ~200), so blocks are probably not the cost; FLAT tests whether textured materials are.
OUTLINES = True
FLAT = False                       # True: every surface a flat colour, for the FPS material test
GROUP_BASE = 10                    # editor group ids start here (installed maps use 0-76; the base map 0-5)
STROKE_W, OUTLINE_W = 6.0, 2.5     # stroke width, and how far the dark backing stroke shows on each side
# Custom meshes ("procedural" brushes, 21 installed maps use them): each sign becomes one object with two
# sections (strokes, outline) instead of ~20-50 blocks. Block count is what costs FPS. Off until confirmed.
MESH_SIGNS = False
# Decoration meshes (2026-09-24): the user's profiling put most of the room's cost in object count (about 1 FPS
# per object at ~700 FPS), so each decoration element (frame, pilasters, winged sun, frieze...) becomes one
# custom-mesh object with one section per material. The room shell stays plain boxes. Off until confirmed.
# Result (2026-09-24): no measurable gain (0.25 -> 0.23 ms, within noise), and Mesh Test B showed big surfaces cost
# the same as mesh or block. Only the rotated sign strokes gain from meshes, so decoration stays plain blocks,
# which stay editable in the map editor.
MESH_DECOR = False
# Window only (user, 2026-09-24): just the window, standing on its own with sky around it. It keeps the opening,
# the frame, the sill, the pilasters and the cornice; the room (walls, floor, ceiling, benches, beams, stars), the
# dado, the frieze, the text columns and the winged sun (a religious symbol; the user wants none) are gone.
# - Tight: a narrower lining and frame band, and the pilasters 8 units from the frame. The targets keep the usual
#   60 units of clear space; at 20 they looked like they touched the frame.
# - Stone: limestone like the pilasters, filling only the window's outline: between the pilasters' outer edges,
#   from the pilaster bases just under the sill up to the cornice. The sandstone rendered dark brown in game.
# - Behind the targets: the base map's target wall, cut to the opening, plain light grey (no texture), so the
#   window shows a wall that differs from the limestone around it. The old light panel read as missing, plain
#   limestone matched the pilasters, the textured limestone was busy, and dark sandstone would hide black targets.
# - Text: the welcome line across the lintel, the user's full maker line ("this place was made by") on the left
#   pilaster and the name cartouche on the right, carved straight onto the stone. For themes (which repaint by
#   surface type) the stone is ceiling type, the wall behind the targets wall type, and the signs floor type with a
#   wall-type outline: readable in 117 of the user's 149 themes. 30 themes paint all four types alike; nothing
#   built from brushes shows there.
WINDOW_ONLY = False
# Mockup options for the window look (2026-09-24, the user asked to compare them side by side):
# WINDOW_HEAD: None (the welcome line fills the lintel), "lintel_split" (a pharaoh's head in the centre of a raised
# lintel, the welcome line split to either side), "top" (the head stands on the cornice, the lintel unchanged) or
# "lintel_alone" (the head alone on the raised lintel; the welcome line on the left pilaster, the maker line and the
# cartouche sharing the right one). WINDOW_LIONS: a recumbent lion on a plinth beside each pilaster base, the pair
# facing the window. The art (bitmaps "pharaoh" and "lion") comes from egypt_glyphs.json or EXTRA_ART.
WINDOW_HEAD = None
WINDOW_LIONS = False
# COURTYARD (the user's pick, 2026-09-24): the palace courtyard around the window, from the design workflow (the
# judge's merge of the lean and authentic concepts; code in courtyard/final_geo.py). Needs WINDOW_ONLY and the lions,
# since the portico starts past the lion plinths. It repaints group 0 wall to palace grey (the sign outlines turn dark
# grey too, as the user approved) and group 1 ceiling to the paving grey.
COURTYARD = False
COURT_GROUP = 100                  # editor groups of the court pieces, one per piece
# LINTEL_MIRROR: the welcome line carved twice from the centre of the lintel outward, the left copy mirrored, so
# every sign faces the middle, as on real Egyptian lintels (the research, 2026-09-24). The user picked it.
LINTEL_MIRROR = False
# STENCIL_ART (the user's pick, 2026-09-24; no prop backing): the free-standing head and lions become thin flat plates with no outline behind, so
# every gap inside them (eyes, mouth, headdress stripes, mane edge) is a hole that shows the sky. Themes paint every
# surface but set the sky separately, so the features stay visible even under a solid-colour theme. The plates are
# thin so the holes stay open at the angle the player sees them from (about 24 degrees up to the head).
STENCIL_ART = False
STENCIL_T = 6.0                    # plate thickness in map units
EXTRA_ART = {}
ART_PIXEL = 7.0                    # map units per art pixel (the head is about 300 units tall)
WIN_Y, WIN_Z = 4000.0, 2300.0      # the wall's half-size: the view at the carved face is about +-3750 x +-2110
UV_UNIT = 100.0                    # texture coordinates: 1 per 100 map units, like a scale-1 Cube brush
PROC_UNIT = arena.MAP_SCALE        # the game multiplies custom-mesh vertices by MapScale an extra time: in every
                                   # installed map, cube vertex size x MapScale = 100 (e.g. 50 at 2, 10 at 10).
                                   # Dividing by 2 (from a MapScale-2 example) still drew signs ~1.5x too big.
DARK_TEXT = False                  # dark blue text (user, 2026-09-23); the blue slot also paints the ceiling
BRUSH_NAME = "DefaultNoCollision"  # decoration needs no collision (148 such blocks in 40 installed maps)
PAINT = {"#": BLUE, "o": OCHRE}


def _mat(material, tint, fullbright, roughness=0.9, scale=1.0):
    return {"material": material, "pack": "Default",
            "properties": [{"name": "Tint", "value": tint}, {"name": "Scale", "value": scale},
                           {"name": "Roughness", "value": roughness}, {"name": "Metallic", "value": 0.0},
                           {"name": "FullBright", "value": fullbright}]}


GROUP0 = {"wall": _mat("MI_WA_StoneTilesFacade", "d9b78aff", 0.30),    # sandstone masonry
          "ground": _mat("MI_WA_BigConcreteTiles", "c4a171ff", 0.25),  # floor slabs
          "ceiling": _mat("MI_WA_ConcretePoured", "eadbb6ff", 0.35),   # limestone trim, beams
          "ramp": _mat("MI_WA_PureColor", "9a3f22ff", 0.30)}           # red ochre paint
GROUP1 = {"wall": _mat("MI_WA_PureColor", "ebe4d2ff", 0.55),           # window view: bright, black targets pop
          "ground": _mat("MI_WA_PureColor", "2b1d12ff", 0.20),         # glyph outline, dark umber
          "ceiling": _mat("MI_WA_PureColor", "1d4d7aff", 0.30),        # Egyptian blue: glyphs, ceiling
          "ramp": _mat("MI_WA_PureColor", "ffe7a8ff", 0.85)}           # gold: stars, sunlight

FALLBACK_GLYPHS = [  # used until egypt_glyphs.json exists
    {"name": "ankh", "rows": ["..###..", ".#...#.", ".#...#.", "..###..", "#######", "...#...", "...#...",
                              "...#...", "...#..."]},
    {"name": "sun", "rows": [".ooo.", "o...o", "o.o.o", "o...o", ".ooo."]},
]


class Scene:
    def __init__(self, template):
        self.template = template
        self.boxes = []
        self._section = "misc"
        self.counts = {}
        self.group = GROUP_BASE
        self.groups = {GROUP_BASE: "misc"}
        self.mesh = None                 # while set, rotated boxes are collected into one custom mesh
        self.body_slot, self.outline_slot = BLUE, OUTLINE   # material slots of carved signs
        self.accent_slot = OCHRE                            # the 'o' pixels of reliefs

    def begin_mesh(self):
        self.mesh = {}

    def end_mesh(self):
        """Emit everything collected since begin_mesh as one procedural brush, one section per material slot.
        Vertices are relative to the brush location, scale 1. Triangle winding follows installed maps:
        for a triangle (A, B, C), (B - A) x (C - A) points against the face normal."""
        mesh, self.mesh = self.mesh, None
        if not mesh:
            return
        allv = [v for sec in mesh.values() for v in sec["v"]]
        origin = tuple(min(v[0][i] for v in allv) for i in range(3))
        b = copy.deepcopy(self.template)
        for k in ("group", "materialSets"):
            b.pop(k, None)
        b.update({"location": "%.6f, %.6f, %.6f" % origin, "mesh": "Cube", "name": BRUSH_NAME,
                  "rotation": "0.000000, 0.000000, 0.000000", "scale": "1.000000, 1.000000, 1.000000",
                  "type": "brush", "group": self.group})
        b["materialSets"] = [{"group": slot[0], "surface": slot[1]} for slot in mesh]
        b["procedural"] = [{"indices": sec["i"],
                            "vertices": [{"location": "%.6f, %.6f, %.6f" % tuple((p[i] - origin[i]) / PROC_UNIT
                                                                                  for i in range(3)),
                                          "normal": "%.6f, %.6f, %.6f" % n,
                                          "tangent": "%.6f, %.6f, %.6f, false" % tg,
                                          "uv0": "%.6f, %.6f" % uv} for p, n, tg, uv in sec["v"]]}
                           for sec in mesh.values()]
        self.boxes.append(b)
        self.counts[self._section] = self.counts.get(self._section, 0) + 1

    def _mesh_box(self, x0, y0, z0, dx, dy, dz, a, slot):
        """Add a box (corner x0, y0, z0; turned a degrees clockwise within the wall) to the open mesh.
        A back face lying on the carved face or the wall is left out; the player never sees it.
        Each face gets planar texture coordinates (world-aligned, UV_UNIT per unit) and a tangent along
        its first edge, the vertex keys installed maps give textured custom meshes."""
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))

        def corner(lx, ly, lz):
            return (x0 + lx, y0 + ly * c + lz * s, z0 - ly * s + lz * c)
        u, v = (0.0, c, -s), (0.0, s, c)
        faces = [((-1.0, 0.0, 0.0), [(0, 0, 0), (0, dy, 0), (0, dy, dz), (0, 0, dz)]),
                 (tuple(-k for k in u), [(0, 0, 0), (dx, 0, 0), (dx, 0, dz), (0, 0, dz)]),
                 (u, [(0, dy, 0), (dx, dy, 0), (dx, dy, dz), (0, dy, dz)]),
                 (tuple(-k for k in v), [(0, 0, 0), (dx, 0, 0), (dx, dy, 0), (0, dy, 0)]),
                 (v, [(0, 0, dz), (dx, 0, dz), (dx, dy, dz), (0, dy, dz)])]
        if x0 + dx < FRONT - 1e-3:                            # free-standing (beams, stars): close the back
            faces.append(((1.0, 0.0, 0.0), [(dx, 0, 0), (dx, dy, 0), (dx, dy, dz), (dx, 0, dz)]))
        sec = self.mesh.setdefault(slot, {"v": [], "i": []})
        for n, quad in faces:
            q = [corner(*p) for p in quad]
            ab = [q[1][i] - q[0][i] for i in range(3)]
            ac = [q[2][i] - q[0][i] for i in range(3)]
            cr = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
            if sum(cr[i] * n[i] for i in range(3)) > 0:       # must point against the normal
                q = q[::-1]
            e1 = [q[1][i] - q[0][i] for i in range(3)]
            e2 = [q[3][i] - q[0][i] for i in range(3)]
            l1, l2 = math.sqrt(sum(k * k for k in e1)), math.sqrt(sum(k * k for k in e2))
            tu, tv = tuple(k / l1 for k in e1), tuple(k / l2 for k in e2)
            base = len(sec["v"])
            sec["v"] += [(p, n, tu, (sum(p[i] * tu[i] for i in range(3)) / UV_UNIT,
                                     sum(p[i] * tv[i] for i in range(3)) / UV_UNIT)) for p in q]
            sec["i"] += [base, base + 1, base + 2, base, base + 2, base + 3]

    def new_group(self, label):
        """Start a new editor group: blocks added from now on can be selected together in the map editor."""
        self.group += 1
        self.groups[self.group] = label

    @property
    def section(self):
        return self._section

    @section.setter
    def section(self, name):
        if self.mesh is not None:          # a decoration mesh ends where the next section starts
            self.end_mesh()
        self._section = name
        self.new_group(name)

    def decor(self, name):
        """Start a decoration section. With MESH_DECOR, all its blocks become one custom mesh, closed by the
        next section or finish()."""
        self.section = name
        if MESH_DECOR:
            self.begin_mesh()

    def finish(self):
        if self.mesh is not None:
            self.end_mesh()

    def box(self, x0, x1, y0, y1, z0, z1, slot):
        if x1 - x0 <= 0 or y1 - y0 <= 0 or z1 - z0 <= 0:
            return
        if self.mesh is not None:
            self._mesh_box(x0, y0, z0, x1 - x0, y1 - y0, z1 - z0, 0.0, slot)
            return
        b = copy.deepcopy(self.template)
        b.pop("group", None)
        b["name"] = BRUSH_NAME
        b["group"] = self.group
        b["location"] = f"{x0:.6f}, {y0:.6f}, {z0:.6f}"
        b["scale"] = f"{(x1 - x0) / 100:.6f}, {(y1 - y0) / 100:.6f}, {(z1 - z0) / 100:.6f}"
        b["rotation"] = "0.000000, 0.000000, 0.000000"
        b["materialSets"] = [{"group": slot[0], "surface": slot[1]} for _ in range(6)]
        self.boxes.append(b)
        self.counts[self._section] = self.counts.get(self._section, 0) + 1

    def box_rot(self, x0, y0, z0, dx, dy, dz, a, slot):
        """A box of size (dx, dy, dz) anchored at its corner (x0, y0, z0) and turned a degrees within the
        front wall, clockwise as the player sees it (calibrated in game, see mechanics.md)."""
        if dx <= 0 or dy <= 0 or dz <= 0:
            return
        if self.mesh is not None:
            self._mesh_box(x0, y0, z0, dx, dy, dz, a, slot)
            return
        self.box(x0, x0 + dx, y0, y0 + dy, z0, z0 + dz, slot)
        self.boxes[-1]["rotation"] = f"{a:.6f}, 0.000000, 0.000000"

    def stroke(self, p0, p1, face_x, width, depth, slot):
        """A straight stroke on the front wall from p0 to p1 ((y, z) points): one rotated block, centred on
        the line and extended by half its width at both ends so joints close."""
        (y0, z0), (y1, z1) = p0, p1
        length = math.hypot(y1 - y0, z1 - z0)
        uy, uz = ((y1 - y0) / length, (z1 - z0) / length) if length > 1e-6 else (1.0, 0.0)
        a = math.degrees(math.atan2(-uz, uy))
        sy, sz = y0 - uy * width / 2, z0 - uz * width / 2            # start, pulled back half a width
        ay, az = sy + uz * width / 2, sz - uy * width / 2            # minus half a width along local +z
        self.box_rot(face_x - depth, ay, az, depth, length + width, width, a, slot)

    def strokes(self, segs, face_x, width=STROKE_W, outline=OUTLINES):
        """Carve line art: blue strokes, and behind them wider, shallower dark strokes as an outline."""
        for p0, p1 in segs:
            self.stroke(p0, p1, face_x, width, BODY_D, self.body_slot)
        if outline:
            for p0, p1 in segs:
                self.stroke(p0, p1, face_x, width + 2 * OUTLINE_W, OUTLINE_D, self.outline_slot)

    def relief(self, rows, place, pixel, depth, outline=OUTLINES, flat=False):
        """Carve a bitmap ('#' blue, 'o' ochre) as raised rectangles, with a 1-pixel outline behind it.

        place(c0, c1, r0, r1, depth) returns box bounds for pixel columns c0..c1 and rows r0..r1 (row 0 = top).
        Rectangles come from cover(), which may overlap: blue boxes may run under ochre pixels because ochre
        is carved 2 units prouder and hides them. The outline is the shape grown by one pixel, carved
        shallower, so only its rim shows. (A thinner fixed-width rim was tried; it needed ~70 more blocks
        per scenario because the rims do not merge, so the rim is one pixel and the pixel was made smaller.)
        """
        # flat: one plane for both colours, so the blue must not run under the ochre (the faces would fight)
        for ch, allow, extra in ((("#", "#", 0.0), ("o", "o", 0.0)) if flat else (("#", "#o", 0.0), ("o", "o", 2.0))):
            for c0, c1, r0, r1 in cover(tuple(rows), ch, allow):
                self.box(*place(c0, c1, r0, r1, BODY_D + extra), self.body_slot if ch == "#" else self.accent_slot)
        if outline:
            for c0, c1, r0, r1 in cover(grow(rows), "#", "#"):
                self.box(*place(c0 - 1, c1 - 1, r0 - 1, r1 - 1, OUTLINE_D), self.outline_slot)


_COVER = {}


def grow(rows):
    """The bitmap's ink grown by one pixel in all 8 directions, padded by one pixel on every side."""
    h, w = len(rows), len(rows[0])
    ink = {(r, c) for r in range(h) for c in range(w) if rows[r][c] != "."}
    return tuple("".join("#" if any((r + dr - 1, c + dc - 1) in ink for dr in (-1, 0, 1) for dc in (-1, 0, 1))
                         else "." for c in range(w + 2)) for r in range(h + 2))



def cover(rows, ch, allow):
    """Greedy rectangle cover: rectangles made only of `allow` cells that together cover every `ch` cell.
    Each step takes the rectangle covering the most still-uncovered cells. Cached per bitmap."""
    key = (rows, ch, allow)
    if key in _COVER:
        return _COVER[key]
    h, w = len(rows), len(rows[0])
    ok = [[rows[r][c] in allow for c in range(w)] for r in range(h)]
    need = {(r, c) for r in range(h) for c in range(w) if rows[r][c] == ch}
    rects = []
    for r0 in range(h):
        for c0 in range(w):
            if not ok[r0][c0]:
                continue
            max_c = w
            for r1 in range(r0, h):
                c = c0
                while c < max_c and ok[r1][c]:
                    c += 1
                max_c = c
                if max_c == c0:
                    break
                for c1 in range(c0, max_c):
                    rects.append((c0, c1, r0, r1))
    chosen = []
    while need:
        best, gain = None, 0
        for c0, c1, r0, r1 in rects:
            g = sum(1 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1) if (r, c) in need)
            if g > gain:
                best, gain = (c0, c1, r0, r1), g
        chosen.append(best)
        c0, c1, r0, r1 = best
        need -= {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
    _COVER[key] = chosen
    return chosen


def front_relief(scene, rows, y_left, z_top, pixel, face_x, depth=BODY_D, outline=OUTLINES):
    """Relief on a wall facing the player (plane x = face_x), columns along +y, rows down from z_top."""
    def place(c0, c1, r0, r1, d):
        return (face_x - d, face_x, y_left + c0 * pixel, y_left + (c1 + 1) * pixel,
                z_top - (r1 + 1) * pixel, z_top - r0 * pixel)
    scene.relief(rows, place, pixel, depth, outline)


def side_relief(scene, rows, side, x_start, z_top, pixel, depth=BODY_D):
    """Relief on a side wall. side=+1: right wall (y = +HALF_Y), screen-right runs toward -x.
    side=-1: left wall (y = -HALF_Y), screen-right runs toward +x. x_start is the glyph's left edge."""
    face_y = side * HALF_Y

    def place(c0, c1, r0, r1, d):
        if side > 0:
            xa, xb = x_start - (c1 + 1) * pixel, x_start - c0 * pixel
            ya, yb = face_y - d, face_y
        else:
            xa, xb = x_start + c0 * pixel, x_start + (c1 + 1) * pixel
            ya, yb = face_y, face_y + d
        return (xa, xb, ya, yb, z_top - (r1 + 1) * pixel, z_top - r0 * pixel)
    scene.relief(rows, place, pixel, depth)


def load_inscriptions():
    return json.loads(Path(__file__).with_name("inscriptions.json").read_text(encoding="utf-8"))


def sign_segs(stroke, k):
    """A sign's strokes scaled by k (map units per render pixel): (segs, w, h), origin top-left, z down."""
    segs = [((s[0] * k, s[1] * k), (s[2] * k, s[3] * k)) for s in stroke["segs"]]
    return segs, stroke["size"][0] * k, stroke["size"][1] * k


def column_layout(text, strokes, k, gap, word_gap):
    """Signs top to bottom, each centred: (items, w, h), items = (segs, dy, dz, label) offsets in map units."""
    items, z = [], 0.0
    for wi, word in enumerate(text.split()):
        for ci, ch in enumerate(word):
            if items:
                z += gap if ci else word_gap
            segs, w, h = sign_segs(strokes[ch], k)
            items.append((segs, w, z, ch))
            z += h
    width = max(w for _, w, _, _ in items)
    return [(segs, (width - w) / 2, dz, lb) for segs, w, dz, lb in items], width, z


def row_layout(text, strokes, k, gap, word_gap):
    """Signs left to right, each centred on the line: (items, w, h), items = (segs, dy, dz, label) as above."""
    placed, y = [], 0.0
    for word in text.split():
        for ci, ch in enumerate(word):
            if placed:
                y += gap if ci else word_gap
            segs, w, h = sign_segs(strokes[ch], k)
            placed.append((segs, y, h, ch))
            y += w
    height = max(h for _, _, h, _ in placed)
    return [(segs, dy, (height - h) / 2, lb) for segs, dy, h, lb in placed], y, height


def cartouche_layout(name, strokes, k, gap, pad):
    """Name signs in a vertical cartouche: an 8-stroke ring with chamfered corners and a tie bar below."""
    inner, iw, ih = column_layout(name.replace(" ", ""), strokes, k, gap, gap)
    w, h, c = iw + 2 * pad, ih + 2 * pad, pad * 0.8
    pts = [(c, 0), (w - c, 0), (w, c), (w, h - c), (w - c, h), (c, h), (0, h - c), (0, c), (c, 0)]
    ring = [((a[0], a[1]), (b[0], b[1])) for a, b in zip(pts, pts[1:])]
    ring.append(((0, h + pad * 0.6), (w, h + pad * 0.6)))                    # tie bar
    items = [(ring, 0, 0, "cartouche")] + [(segs, dy + pad, dz + pad, lb) for segs, dy, dz, lb in inner]
    return items, w, h + pad * 0.6


def stack_layout(blocks, gap):
    """Stack laid-out blocks top to bottom, centred."""
    width = max(w for _, w, _ in blocks)
    out, z = [], 0.0
    for i, (items, w, h) in enumerate(blocks):
        if i:
            z += gap
        out += [(segs, dy + (width - w) / 2, dz + z, lb) for segs, dy, dz, lb in items]
        z += h
    return out, width, z


def standing_relief(scene, rows, y_left, z_bottom, pixel, back_x):
    """A free-standing cut-out (a statue seen face on): the bitmap as blocks whose back is at back_x, three times the
    carving depth thick, standing with its last row on z_bottom, and the dark outline as a thinner rim behind."""
    h = len(rows)

    def place(c0, c1, r0, r1, d):
        return (back_x - (STENCIL_T if STENCIL_ART else 3 * d), back_x, y_left + c0 * pixel,
                y_left + (c1 + 1) * pixel, z_bottom + (h - 1 - r1) * pixel, z_bottom + (h - r0) * pixel)
    scene.relief(rows, place, pixel, BODY_D, outline=not STENCIL_ART, flat=STENCIL_ART)


def load_glyphs():
    p = Path(__file__).with_name("egypt_glyphs.json")
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"glyphs": FALLBACK_GLYPHS, "winged_sun": None, "frieze_tile": None}


# The window look as the user approved it on 2026-09-24 (the Window Test): used by every Flow Fix scenario.
WINDOW_LOOK = dict(MESH_SIGNS=True, DARK_TEXT=True, WINDOW_ONLY=True, WINDOW_HEAD="top", WINDOW_LIONS=True,
                   LINTEL_MIRROR=True, STENCIL_ART=True, COURTYARD=True)


def add_window(m, spawn_volumes, max_target_radius):
    """add_egypt with the window look's settings, restoring the module's settings afterwards."""
    saved = {k: globals()[k] for k in WINDOW_LOOK}
    globals().update(WINDOW_LOOK)
    try:
        return add_egypt(m, spawn_volumes, max_target_radius)
    finally:
        globals().update(saved)


def add_egypt(m, spawn_volumes, max_target_radius):
    art = load_glyphs()
    if FLAT:   # same colours, but every surface MI_WA_PureColor (no textures)
        flat = lambda g: {k: _mat("MI_WA_PureColor", v["properties"][0]["value"], v["properties"][4]["value"])
                          for k, v in g.items()}
        m["materialSets"][0], m["materialSets"][1] = flat(GROUP0), flat(GROUP1)
    else:
        m["materialSets"][0] = copy.deepcopy(GROUP0)
        m["materialSets"][1] = copy.deepcopy(GROUP1)
    if DARK_TEXT:
        m["materialSets"][1]["ceiling"]["properties"][0]["value"] = "0f2a4dff"   # dark blue
    if WINDOW_ONLY:
        # The wall behind the targets: plain light grey, apart from the limestone around it (user, 2026-09-24).
        m["materialSets"][1]["wall"] = _mat("MI_WA_PureColor", "c8c8c8ff", 0.4)
        # Signs: body on the floor type, outline on the wall type (the sandstone slot, unused in this look), same
        # colours as before. Under the user's 149 themes the signs then differ from the ceiling-type stone in 117,
        # against 79 with the body on the ceiling type like the stone.
        m["materialSets"][1]["ground"] = copy.deepcopy(m["materialSets"][1]["ceiling"])
        m["materialSets"][0]["wall"] = copy.deepcopy(GROUP1["ground"])
        # The pharaoh's head: a golden face and a lapis-blue headdress (user, 2026-09-24). The blue takes the floor
        # slot of group 0 (unused in this look): floor type like the text and the lion bodies, so under a theme the
        # headdress changes colour with them and the face stays visible. On the ceiling type, like the stone, the
        # whole head turned into one grey shape. The gold takes the ramp slot of group 1 (the ledge strip too).
        m["materialSets"][0]["ground"] = _mat("MI_WA_PureColor", "1e4c9aff", 0.35)
        m["materialSets"][1]["ramp"] = _mat("MI_WA_PureColor", "d4a02aff", 0.5)
        if COURTYARD:                     # palace walls (and the sign outlines) grey; the free slot as paving
            m["materialSets"][0]["wall"] = _mat("MI_WA_PureColor", "5d6066ff", 0.25)
            m["materialSets"][1]["ceiling"] = _mat("MI_WA_PureColor", "77736bff", 0.3)

    wall = next(o for o in m["objects"] if o.get("type") == "brush" and o["location"].startswith("-2899.999512"))
    wall["materialSets"] = [{"group": 0, "surface": "wall"} for _ in range(6)]
    s = Scene(wall)
    if WINDOW_ONLY:
        s.body_slot, s.outline_slot = OUTLINE, SANDSTONE   # slots (1, ground) and (0, wall), repainted above

    wy, wz = (WIN_Y, WIN_Z) if WINDOW_ONLY else (HALF_Y, HALF_Z)   # the carved wall's half-size

    # --- room shell ---
    s.section = 'room shell'
    if not WINDOW_ONLY:
        s.box(ROOM_BACK, WALL + 10, -HALF_Y - SLAB, HALF_Y + SLAB, -HALF_Z - SLAB, -HALF_Z, FLOOR)
        s.box(ROOM_BACK, WALL + 10, -HALF_Y - SLAB, HALF_Y + SLAB, HALF_Z, HALF_Z + SLAB, BLUE)   # star ceiling
        s.box(ROOM_BACK, WALL + 10, -HALF_Y - SLAB, -HALF_Y, -HALF_Z, HALF_Z, SANDSTONE)
        s.box(ROOM_BACK, WALL + 10, HALF_Y, HALF_Y + SLAB, -HALF_Z, HALF_Z, SANDSTONE)
        s.box(ROOM_BACK, ROOM_BACK + SLAB, -HALF_Y, HALF_Y, -HALF_Z, HALF_Z, SANDSTONE)

    # --- window opening, jamb lining, thick front wall ---
    s.decor('window opening, jamb lin')
    oy0, oy1, oz0, oz1 = arena.window_bounds(spawn_volumes, max_target_radius)
    if WINDOW_ONLY:                       # the base map's wall, cut to the opening, is the wall seen through
        # the window: the view slot, repainted plain limestone colour above
        wall["location"] = f"{wall['location'].split(',')[0]}, {oy0:.6f}, {oz0:.6f}"
        wall["scale"] = f"{wall['scale'].split(',')[0]}, {(oy1 - oy0) / 100:.6f}, {(oz1 - oz0) / 100:.6f}"
        wall["materialSets"] = [{"group": VIEW[0], "surface": VIEW[1]} for _ in range(6)]
    else:
        s.box(WALL - 4, WALL, oy0, oy1, oz0, oz1, VIEW)
    J = 16.0 if WINDOW_ONLY else 24.0
    ry0, ry1, rz0, rz1 = oy0 - J, oy1 + J, oz0 - J, oz1 + J
    s.box(FRONT, WALL, ry0, ry1, oz1, rz1, LIME)          # lining top
    s.box(FRONT, WALL, ry0, ry1, rz0, oz0, GOLD)          # lining bottom: sunlight on the window ledge
    s.box(FRONT, WALL, ry0, oy0, oz0, oz1, LIME)          # lining left
    s.box(FRONT, WALL, oy1, ry1, oz0, oz1, LIME)          # lining right
    if not WINDOW_ONLY:                   # the window look builds its wall after the pilasters, to their outline
        s.box(FRONT, WALL, -wy, wy, rz1, wz, SANDSTONE)
        s.box(FRONT, WALL, -wy, wy, -wz, rz0, SANDSTONE)
        s.box(FRONT, WALL, -wy, ry0, rz0, rz1, SANDSTONE)
        s.box(FRONT, WALL, ry1, wy, rz0, rz1, SANDSTONE)

    # --- frame: limestone band, red ochre torus bead, sill ---
    s.decor('frame: limestone band, r')
    FW, FP, TW, TP = (60.0 if WINDOW_ONLY else 80.0), 24.0, 14.0, 34.0
    fy0, fy1, fz0, fz1 = ry0 - FW, ry1 + FW, rz0 - FW, rz1 + FW
    for (a0, a1, b0, b1) in [(fy0, fy1, rz1, fz1), (fy0, fy1, fz0, rz0), (fy0, ry0, rz0, rz1), (ry1, fy1, rz0, rz1)]:
        s.box(FRONT - FP, FRONT, a0, a1, b0, b1, LIME)
    ty0, ty1, tz0, tz1 = fy0 - TW, fy1 + TW, fz0 - TW, fz1 + TW
    for (a0, a1, b0, b1) in [(ty0, ty1, fz1, tz1), (ty0, ty1, tz0, fz0), (ty0, fy0, fz0, fz1), (fy1, ty1, fz0, fz1)]:
        s.box(FRONT - TP, FRONT, a0, a1, b0, b1, OCHRE)
    sill = 8.0 if WINDOW_ONLY else 40.0  # the tight pilasters stand 8 from the frame: the sill stops at them
    s.box(FRONT - 70, FRONT, ty0 - sill, ty1 + sill, tz0 - 36, tz0, LIME)   # sill ledge
    if WINDOW_ONLY:
        # Dark outlines (user, 2026-09-24): under themes that paint everything alike, the window, the frame and the
        # pilasters merged. A navy band on the lining's face rings the opening where the targets appear, and a
        # thinner line runs round the outside of the frame, between it and the pilasters and under the lintel.
        # Floor type, the type that differs from both the wall-type backdrop and the ceiling-type stone most often.
        s.section = "outlines"
        ring = [(ry0, ry1, oz1, rz1), (ry0, ry1, rz0, oz0), (ry0, oy0, oz0, oz1), (oy1, ry1, oz0, oz1)]
        for a0, a1, b0, b1 in ring:                       # the band round the opening, on the lining's front face
            s.box(FRONT - 3, FRONT, a0, a1, b0, b1, OUTLINE)
        line = 8.0                                         # outside the torus bead, in the gap to the pilasters
        for a0, a1, b0, b1 in [(ty0 - line, ty0, tz0, tz1 + line), (ty1, ty1 + line, tz0, tz1 + line),
                               (ty0, ty1, tz1, tz1 + line)]:
            s.box(FRONT - 3, FRONT, a0, a1, b0, b1, OUTLINE)

    # --- pilasters with papyrus capitals, cornice above ---
    s.decor('pilasters with papyrus c')
    PG, PW = (8.0, 190.0) if WINDOW_ONLY else (30.0, 150.0)   # tight and wider when they carry the inscriptions
    pz0 = tz0 - 36 - 70 if WINDOW_ONLY else -HALF_Z      # window look: the bases sit just under the sill
    art.update(EXTRA_ART)
    head = art.get("pharaoh") if WINDOW_ONLY and WINDOW_HEAD else None
    lintel_h = 150.0
    if head and WINDOW_HEAD != "top":    # a raised lintel carries the head: its height plus 20 above and below
        lintel_h = len(head) * ART_PIXEL + 40
    zc = tz1 + 20 + lintel_h             # cornice base
    cornice = [(0, 20, 30, OCHRE), (20, 60, 42, LIME), (60, 100, 62, LIME), (100, 140, 86, LIME), (140, 165, 96, LIME)]
    top = zc + cornice[-1][1]
    roof = 1900.0 if WINDOW_ONLY else HALF_Z - 40   # the window look has no ceiling, only the top of the view
    if top > roof:                       # tall windows: squeeze the lintel so the cornice fits under the ceiling
        zc -= top - roof
        top = roof
    pil = [(-1, ty0 - PG - PW, ty0 - PG), (1, ty1 + PG, ty1 + PG + PW)]
    for side, a, b in pil:
        s.box(FRONT - 55, FRONT, a - 15, b + 15, pz0, pz0 + 70, LIME)                  # base
        s.box(FRONT - 40, FRONT, a, b, pz0 + 70, zc - 120, LIME)                       # shaft
        for k, (dz, grow, prot) in enumerate([(0, 15, 52), (60, 40, 70)]):
            s.box(FRONT - prot, FRONT, a - grow, b + grow, zc - 120 + dz, zc - 60 + dz, LIME)   # capital
        for zb in (zc - 150,):                                                          # binding band
            s.box(FRONT - 44, FRONT, a, b, zb, zb + 10, OCHRE)
    c_y0, c_y1 = pil[0][1] - 60, pil[1][2] + 60
    for z0, z1, prot, slot in cornice:
        s.box(FRONT - prot, FRONT, c_y0, c_y1, zc + z0, zc + z1, slot)
    y = c_y0 + 20                                                                        # flutes on the cavetto
    k = 0
    while y + 14 < c_y1 - 20 and not WINDOW_ONLY:        # the user dropped the flutes in the window look
        s.box(FRONT - 90, FRONT - 86, y, y + 14, zc + 102, zc + 138, BLUE if k % 2 == 0 else OCHRE)
        y += 440
        k += 1

    if WINDOW_ONLY:                       # the stone wall, cut to the window's outline
        s.section = 'stone wall to the outline'
        # Limestone like the pilasters, not sandstone: the user wanted the wall material gone behind the lintel
        # text (it rendered dark brown in game), 2026-09-24.
        ya, yb = pil[0][1], pil[1][2]
        s.box(FRONT, WALL, ya, yb, rz1, zc, LIME)
        s.box(FRONT, WALL, ya, yb, pz0, rz0, LIME)
        s.box(FRONT, WALL, ya, ry0, rz0, rz1, LIME)
        s.box(FRONT, WALL, ry1, yb, rz0, rz1, LIME)

    if head:                              # the pharaoh's head: centred on the lintel, or standing on the cornice
        s.section = "pharaoh head"
        s.begin_mesh()                    # one object instead of about 100 relief blocks
        slots = s.body_slot, s.accent_slot
        s.body_slot, s.accent_slot = FLOOR, GOLD   # lapis headdress (floor type), golden skin
        hw, hh = len(head[0]) * ART_PIXEL, len(head) * ART_PIXEL
        cy = (oy0 + oy1) / 2
        if WINDOW_HEAD == "top":
            standing_relief(s, head, cy - hw / 2, top, ART_PIXEL, FRONT - 20)
        else:
            front_relief(s, head, cy - hw / 2, (tz1 + zc + hh) / 2, ART_PIXEL, FRONT)
        s.finish()
        s.body_slot, s.accent_slot = slots
    lion = art.get("lion") if WINDOW_ONLY and WINDOW_LIONS else None
    plinth_y = {}                         # the lion plinths' y extents, per side (the court starts past them)
    if lion:                              # a lion on a plinth beside each pilaster base, the pair facing the window
        lw = len(lion[0]) * ART_PIXEL
        for side, a, b in pil:
            s.section = "lion right" if side > 0 else "lion left"
            rows = lion if side < 0 else [r[::-1] for r in lion]   # drawn facing right, so the left one as is
            y_in = a - 15 if side < 0 else b + 15                 # the base's outer edge
            y0 = y_in - 40 - lw if side < 0 else y_in + 40
            plinth_y[side] = (min(y0 - 30, y_in), max(y0 + lw + 30, y_in))
            s.box(FRONT - 70, FRONT, *plinth_y[side], pz0, pz0 + 70, LIME)                              # plinth
            s.begin_mesh()                # the lion is one object
            standing_relief(s, rows, y0, pz0 + 70, ART_PIXEL, FRONT - 20)
            s.finish()

    # --- winged sun on the lintel (the window look carves the welcome line there instead) ---
    s.decor('winged sun on the lintel')
    if art.get("winged_sun") and zc - tz1 > 60 and not WINDOW_ONLY:
        ws = art["winged_sun"]
        span = min(c_y1 - c_y0 - 80, 1400.0)
        px = min(span / len(ws[0]), (zc - tz1 - 16) / len(ws))
        cy = (oy0 + oy1) / 2
        front_relief(s, ws, cy - px * len(ws[0]) / 2, tz1 + 8 + px * len(ws), px, FRONT)

    # --- dado: red ochre band, blue top edge ---
    s.decor('dado')
    if not WINDOW_ONLY:
        s.box(FRONT - 10, FRONT, -HALF_Y, HALF_Y, -HALF_Z, -950, OCHRE)
        s.box(FRONT - 14, FRONT, -HALF_Y, HALF_Y, -950, -935, BLUE)

    # --- frieze along the top: khekher knots (a knob on a shaft), blue border under it ---
    # Two blocks per knot and no outline, to keep the block count down (the user asked for fewer).
    s.decor('frieze')
    frieze_bottom = HALF_Z - 175
    if not WINDOW_ONLY:
        s.box(FRONT - 8, FRONT, -HALF_Y, HALF_Y, frieze_bottom - 16, frieze_bottom, BLUE)
    y = -HALF_Y + 60
    while y + 50 < HALF_Y - 40 and not WINDOW_ONLY:
        if not (top > frieze_bottom and c_y0 - 20 < y + 50 and y < c_y1 + 20):   # not behind the cornice
            s.box(FRONT - BODY_D, FRONT, y + 15, y + 35, frieze_bottom + 10, frieze_bottom + 90, BLUE)   # shaft
            s.box(FRONT - BODY_D, FRONT, y, y + 50, frieze_bottom + 90, frieze_bottom + 140, BLUE)      # knob
        y += 400

    # --- inscription columns beside the pilasters (the user's text) ---
    # One column per side. Left: "Welcome to my humble home". Right: iri.n ("made by") above Bassel Bakr in
    # a cartouche. Signs are line art: one rotated block per stroke, a dark backing stroke behind each
    # (user, 2026-09-23). Every sign, and the cartouche ring, is its own editor group.
    s.section = 'inscriptions'
    ins = load_inscriptions()
    st = ins["strokes"]
    BODY = 150.0                          # column width
    K = 1.05                              # map units per render pixel (signs about 130 units per em)
    z_hi, z_lo = frieze_bottom - 60, -935 + 60
    face = FRONT
    if WINDOW_ONLY:                       # carved on each pilaster shaft, below the binding band
        BODY = PW - 2 * 20                # 20 in from each edge
        z_hi, z_lo = zc - 150 - 50, pz0 + 70 + 40
        face = FRONT - 40                 # the shaft's face
    s.counts["_k"] = {}

    def carve(items, left, top, face_x):
        for segs, dy, dz, label in items:
            s.new_group(f"sign {label}")
            if MESH_SIGNS:
                s.begin_mesh()
            s.strokes([((left + dy + p[0], top - dz - p[1]), (left + dy + q[0], top - dz - q[1]))
                       for p, q in segs], face_x)
            if MESH_SIGNS:
                s.end_mesh()

    def lintel_line(text, ly0, ly1, lz0, lz1, label):
        k = K
        while True:
            items, w, h = row_layout(text, st, k, 30 * k, 70 * k)
            if (w <= ly1 - ly0 and h <= lz1 - lz0) or k < 0.4:
                break
            k *= 0.93
        s.counts["_k"][label] = round(k, 3)
        carve(items, (ly0 + ly1 - w) / 2, (lz0 + lz1 + h) / 2, FRONT)

    def mirrored_lintel(text, ly0, ly1, lz0, lz1, gap=60.0):
        """The line from the centre outward to the right, and its mirror image to the left."""
        c = (ly0 + ly1) / 2
        k = K
        while True:
            items, w, h = row_layout(text, st, k, 30 * k, 70 * k)
            if (w <= (ly1 - ly0) / 2 - gap / 2 and h <= lz1 - lz0) or k < 0.4:
                break
            k *= 0.93
        s.counts["_k"]["lintel mirrored"] = round(k, 3)
        top_z = (lz0 + lz1 + h) / 2
        carve(items, c + gap / 2, top_z, FRONT)
        flipped = [([((w - dy - a[0], a[1]), (w - dy - b[0], b[1])) for a, b in segs], 0.0, dz, label + " (mirror)")
                   for segs, dy, dz, label in items]
        carve(flipped, c - gap / 2 - w, top_z, FRONT)

    if WINDOW_ONLY and WINDOW_HEAD in (None, "top") and LINTEL_MIRROR:
        mirrored_lintel(ins["text"]["welcome"], pil[0][2] + 70, pil[1][1] - 70, tz1 + 15, zc - 15)
    elif WINDOW_ONLY and WINDOW_HEAD in (None, "top"):   # the welcome line across the lintel, between the capitals
        lintel_line(ins["text"]["welcome"], pil[0][2] + 70, pil[1][1] - 70, tz1 + 15, zc - 15, "lintel")
    elif WINDOW_ONLY and WINDOW_HEAD == "lintel_split":   # split at the word break nearest the middle
        words = ins["text"]["welcome"].split()
        widths = [sum(st[c]["size"][0] for c in w_) for w_ in words]
        cut = min(range(1, len(words)), key=lambda i: abs(sum(widths[:i]) - sum(widths[i:])))
        hw = len(head[0]) * ART_PIXEL
        cy = (oy0 + oy1) / 2
        mid = (tz1 + zc) / 2
        lintel_line(" ".join(words[:cut]), pil[0][2] + 70, cy - hw / 2 - 50, mid - 90, mid + 90, "lintel left")
        lintel_line(" ".join(words[cut:]), cy + hw / 2 + 50, pil[1][1] - 70, mid - 90, mid + 90, "lintel right")
    for side, a, b in pil:
        y0 = b + 70 if side > 0 else a - 70 - BODY
        if WINDOW_ONLY:
            y0 = a + 20
        k = K
        while True:
            if WINDOW_ONLY and WINDOW_HEAD == "lintel_alone" and side < 0:
                items, w, h = column_layout(ins["text"]["welcome"], st, k, 30 * k, 60 * k)
            elif WINDOW_ONLY and WINDOW_HEAD == "lintel_alone":
                items, w, h = stack_layout([column_layout(ins["text"]["maker"], st, k, 30 * k, 60 * k),
                                            cartouche_layout(ins["text"]["name"], st, k * 0.8, 30 * k, 20 * k)],
                                           50 * k)
            elif WINDOW_ONLY and side < 0:
                items, w, h = column_layout(ins["text"]["maker"], st, k, 30 * k, 60 * k)
            elif WINDOW_ONLY:
                items, w, h = cartouche_layout(ins["text"]["name"], st, k, 30 * k, 20 * k)
            elif side < 0:
                items, w, h = column_layout(ins["text"]["welcome"], st, k, 30 * k, 60 * k)
            else:
                items, w, h = stack_layout([column_layout(ins["text"]["madeby"], st, k, 30 * k, 60 * k),
                                            cartouche_layout(ins["text"]["name"], st, k * 0.72, 30 * k, 20 * k)],
                                           50 * k)
            if (w <= BODY and h <= z_hi - z_lo) or k < 0.4:
                break
            k *= 0.93
        s.counts["_k"][side] = round(k, 3)
        left = y0 + (BODY - w) / 2
        top = (z_hi + z_lo + h) / 2
        carve(items, left, top, face)
        if WINDOW_ONLY:
            continue
        s.new_group("column dividers")
        if MESH_DECOR:
            s.begin_mesh()
        for yd in (y0 - 20, y0 + BODY + 14):
            s.box(FRONT - 4, FRONT, yd, yd + 6, z_lo, z_hi, BLUE)
        s.finish()

    # --- side walls: stone benches (the "Left side" / "Right side" labels were dropped by the user) ---
    if WINDOW_ONLY:
        s.finish()
        if COURTYARD:                     # the palace courtyard, fitted to this window
            assert plinth_y, "the courtyard needs the lions (WINDOW_LIONS)"
            sys.path.insert(0, str(Path(__file__).with_name("courtyard")))
            import court_export
            import final_geo
            court = final_geo.court({"F": pz0, "yc": (oy0 + oy1) / 2, "stoneL": c_y0, "stoneR": c_y1,
                                     "plinthL": plinth_y[-1][0], "plinthR": plinth_y[1][1]})
            s.boxes += [court_export.export(o, wall, arena.MAP_SCALE, COURT_GROUP + k) for k, o in enumerate(court)]
            s.counts["courtyard"] = len(court)
        i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
        m["objects"][i:i] = s.boxes
        used = {bx["group"] for bx in s.boxes}
        s.counts["_groups"] = {g: lb for g, lb in s.groups.items() if g in used}
        return s.counts

    s.decor('side walls')
    for side in (1, -1):
        face = side * HALF_Y
        by0, by1 = (face - 170, face) if side > 0 else (face, face + 170)
        s.box(-3650, FRONT, by0, by1, -HALF_Z, -1090, LIME)                       # bench
        bt0, bt1 = (face - 185, face) if side > 0 else (face, face + 185)
        s.box(-3665, FRONT, bt0, bt1, -1090, -1070, SANDSTONE)                  # bench top

    # --- ceiling: stone beams, gold stars; floor: sunlight patch ---
    s.decor('ceiling: stone beams, go')
    for xb in (-3250, -3700, -4150):     # the ceiling is on screen only for x > -4215
        s.box(xb - 45, xb + 45, -HALF_Y, HALF_Y, HALF_Z - 80, HALF_Z, LIME)
    for i, xs in enumerate((-3470,)):
        for j in range(-3, 4):
            ys = j * 520 - 130
            s.box(xs - 20, xs + 20, ys - 20, ys + 20, HALF_Z - 4, HALF_Z, GOLD)     # one block per star
    s.box(-3700, FRONT, oy0 * 0.55, oy1 * 0.55, -HALF_Z, -HALF_Z + 2, GOLD)
    s.finish()

    i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
    m["objects"][i:i] = s.boxes
    used = {bx["group"] for bx in s.boxes}
    s.counts["_groups"] = {g: lb for g, lb in s.groups.items() if g in used}
    return s.counts
