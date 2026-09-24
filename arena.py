"""Arena for Flow Fix scenarios (added 2026-09-23; grey rework after the first version crashed the game).

Encloses the base map's floating target wall in a dark grey room:
- floor, ceiling, side walls and a wall behind the player
- a dark panel on the target wall
- a matte light panel behind the targets, sized to the scenario's spawn area
- a thin dark frame around that panel

Only visuals change; nothing sits between the player and the targets.
Map units, before MapScale. A brush's location is its minimum corner, and scale 1 = 100 units.
"""
import copy

WALL_FRONT = -2900.0     # front face of the base map's target wall
ROOM_BACK = -7100.0      # behind the player (player at x = -6000)
HALF_Y, HALF_Z = 2500.0, 1250.0
SLAB = 100.0             # thickness of floor, ceiling and walls
PANEL_DEPTH = 4.0        # light panel sits this far in front of the wall
FRAME_DEPTH = 40.0       # how far the frame bars stand out from the wall; 6 looked like a sliver (2026-09-23)
FRAME_WIDTH = 90.0       # was 30, which the user measured in the editor and found too thin
MARGIN = 60.0            # clear space between the largest possible target and the frame, as seen on screen
MAP_SCALE = 3.15         # target radii and spawn offsets are world units; the map is scaled by this
VOLUME_HALF = 100.0      # a SpawnVolume's half-extent per unit of scale (scale 1 spans 200 units)
PLAYER_X = -5999.999512  # eye position (y = z = 0)
SPAWN_X = -2949.999756   # plane of the spawn volumes, in front of the wall
SPAWN_Z_OFFSET = 8.0     # target character SpawnOffset Z, world units
# Targets float in front of the wall, so from the eye they appear this much further out on the wall plane.
PARALLAX = (WALL_FRONT - PLAYER_X) / (SPAWN_X - PLAYER_X)


def _props(tint, roughness, metallic, fullbright, scale=1.0):
    return [{"name": "Tint", "value": tint}, {"name": "Scale", "value": scale},
            {"name": "Roughness", "value": roughness}, {"name": "Metallic", "value": metallic},
            {"name": "FullBright", "value": fullbright}]


def _mat(material, **kw):
    return {"material": material, "pack": "Default", "properties": _props(**kw)}


# Maps support only two material groups (plus a "None" group): no working map has more, and adding groups 3-5
# crashed the renderer (2026-09-23). So the arena redefines groups 0 and 1, which gives 8 surface slots.
# Dark grey theme at the user's request. Surfaces are self-lit (FullBright) because maps have no lights.
def _pure(tint, fullbright, roughness=0.85):
    return _mat("MI_WA_PureColor", tint=tint, roughness=roughness, metallic=0.0, fullbright=fullbright)


ROOM = {"ceiling": _pure("26282bff", 0.20),   # ceiling
        "ground": _pure("2e3033ff", 0.25),    # floor
        "wall": _pure("3a3d41ff", 0.25),      # side walls, the wall behind the player, and the target wall
        "ramp": _pure("32353aff", 0.20)}      # unused
PANEL_FRAME = {"wall": _pure("9a9ea3ff", 0.35),     # panel behind the targets: mid grey, so black targets stand out
               "ceiling": _pure("16181bff", 0.10),  # frame
               "ground": _pure("9a9ea3ff", 0.35),
               "ramp": _pure("16181bff", 0.10)}


def _brush(template, x0, x1, y0, y1, z0, z1, group, surface):
    b = copy.deepcopy(template)
    b.pop("group", None)
    b["location"] = f"{x0:.6f}, {y0:.6f}, {z0:.6f}"
    b["scale"] = f"{(x1 - x0) / 100:.6f}, {(y1 - y0) / 100:.6f}, {(z1 - z0) / 100:.6f}"
    b["rotation"] = "0.000000, 0.000000, 0.000000"
    b["materialSets"] = [{"group": group, "surface": surface} for _ in range(6)]  # every face the same
    return b


def target_envelope(spawn_volumes, max_target_radius):
    """Where targets can appear, projected from the eye onto the wall plane: (y0, y1, z0, z1)."""
    r = max_target_radius / MAP_SCALE
    dz = SPAWN_Z_OFFSET / MAP_SCALE
    return (PARALLAX * (min(v["y"] - v["size_y"] * VOLUME_HALF for v in spawn_volumes) - r),
            PARALLAX * (max(v["y"] + v["size_y"] * VOLUME_HALF for v in spawn_volumes) + r),
            PARALLAX * (min(v["z"] - v["size_z"] * VOLUME_HALF for v in spawn_volumes) + dz - r),
            PARALLAX * (max(v["z"] + v["size_z"] * VOLUME_HALF for v in spawn_volumes) + dz + r))


def window_bounds(spawn_volumes, max_target_radius, margin=MARGIN):
    """The target envelope plus the clear margin: the panel behind the targets."""
    y0, y1, z0, z1 = target_envelope(spawn_volumes, max_target_radius)
    return y0 - margin, y1 + margin, z0 - margin, z1 + margin


def add_arena(m, spawn_volumes, max_target_radius):
    """Add the room, panel and frame to map JSON m (modified in place)."""
    m["materialSets"][0] = ROOM
    m["materialSets"][1] = PANEL_FRAME
    g_room, g_panel, g_frame = 0, 1, 1

    wall = next(o for o in m["objects"] if o.get("type") == "brush" and o["location"].startswith("-2899.999512"))
    # Player themes replace materials by surface type (wall, floor, ceiling, ramp), not by group. So the target
    # wall uses the "wall" type like the panel, and the frame uses "ceiling": under a theme that gives walls
    # their own look, the frame stays a visible outline. On "ramp", the frame vanished into the same grid.
    wall["materialSets"] = [{"group": g_room, "surface": "wall"} for _ in range(6)]

    x0, x1 = ROOM_BACK, WALL_FRONT + 10
    room = [
        _brush(wall, x0, x1, -HALF_Y - SLAB, HALF_Y + SLAB, -HALF_Z - SLAB, -HALF_Z, g_room, "ground"),  # floor
        _brush(wall, x0, x1, -HALF_Y - SLAB, HALF_Y + SLAB, HALF_Z, HALF_Z + SLAB, g_room, "ceiling"),   # ceiling
        _brush(wall, x0, x1, -HALF_Y - SLAB, -HALF_Y, -HALF_Z, HALF_Z, g_room, "wall"),                  # left wall
        _brush(wall, x0, x1, HALF_Y, HALF_Y + SLAB, -HALF_Z, HALF_Z, g_room, "wall"),                    # right wall
        _brush(wall, x0, x0 + SLAB, -HALF_Y, HALF_Y, -HALF_Z, HALF_Z, g_room, "wall"),                   # behind player
    ]

    py0, py1, pz0, pz1 = window_bounds(spawn_volumes, max_target_radius)
    fx0, px0, w = WALL_FRONT - FRAME_DEPTH, WALL_FRONT - PANEL_DEPTH, FRAME_WIDTH
    panel = [
        _brush(wall, px0, WALL_FRONT, py0, py1, pz0, pz1, g_panel, "wall"),
        _brush(wall, fx0, WALL_FRONT, py0 - w, py1 + w, pz1, pz1 + w, g_frame, "ceiling"),  # top bar
        _brush(wall, fx0, WALL_FRONT, py0 - w, py1 + w, pz0 - w, pz0, g_frame, "ceiling"),  # bottom bar
        _brush(wall, fx0, WALL_FRONT, py0 - w, py0, pz0, pz1, g_frame, "ceiling"),          # left bar
        _brush(wall, fx0, WALL_FRONT, py1, py1 + w, pz0, pz1, g_frame, "ceiling"),          # right bar
    ]
    # brushes go before the gameObjects, like the base map
    i = next(k for k, o in enumerate(m["objects"]) if o.get("type") != "brush")
    m["objects"][i:i] = room + panel
    return (py0, py1, pz0, pz1)
