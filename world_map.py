"""World Map (2026-09-27): the world's continents on a lecture hall's chalkboard, traced by the bot (trace_track.py).

    python world_map.py            writes out/World Map.sce and test_out/World Map board.png

Copy the scenario into KovaaK's Scenarios folder by hand. The coasts come from Natural Earth's 1:110m countries
(public domain, data/ne_110m_admin_0_countries.geojson, from github.com/nvkelso/natural-earth-vector): each continent's
countries filled on a grid, the largest island kept, lakes filled (channels cut first at the Bosporus, the Danish
straits and Hormuz keep those seas open), the lightest blur that keeps CLEAR between parts of the coast, the coast
traced as one loop, and only its sharp spots eased. Sinai is cut at Suez and Panama at the Darien, so no two continents
touch; Antarctica is a strip along the bottom, as on the user's reference map. The design history is in
.agents/skills/kovaaks-scenario-design/references/scenario-types.md ("Case: tracking along a drawn path").
"""
import json
import math

from PIL import Image, ImageDraw, ImageFilter

from trace_track import Shape, average, build_track, check, ease, resample

NE = "data/ne_110m_admin_0_countries.geojson"
ORDER = [  # name, countries (continent or country names), labels (text, lon, lat; None = the continent's centre)
    ("North America", {"North America"}, [("North America", None, None)]),
    ("South America", {"South America"}, [("South America", None, None)]),
    ("Africa", {"Africa"}, [("Africa", None, None)]),
    ("Antarctica", {"Antarctica"}, [("Antarctica", None, None)]),
    ("Australia", {"Australia"}, [("Australia", None, None)]),
    ("Eurasia", {"Europe", "Asia"}, [("Europe", 18.0, 52.0), ("Asia", 95.0, 50.0)]),
]
COUNTRY_CLIP = {"Egypt": ("max", 32.2),    # Sinai cut off at the Suez Canal: Africa and Asia apart
                "Panama": ("max", -78.4)}  # the Darien tip: North and South America apart
ANT_CUT, ANT_BAND = -77.5, -75.5           # Antarctica cut at ANT_CUT; the band up to ANT_BAND is land too, so the
                                           # Ross and Weddell Seas (which reach further south) do not break the strip
CHANNELS = [  # sea routes cut through the land (lon, lat), so enclosed seas stay part of the coast
    [(25.0, 39.6), (26.4, 40.2), (27.6, 40.7), (29.0, 41.1), (29.8, 41.9)],        # Dardanelles and Bosporus
    [(10.6, 57.9), (11.6, 57.0), (12.4, 56.2), (12.8, 55.5), (13.6, 54.9)],        # Kattegat and the Sound
    [(58.4, 24.5), (57.0, 25.8), (56.2, 26.6), (55.2, 26.5)],                      # Strait of Hormuz
]
CHANNEL_W = 0.45                    # deg on the board
MAP_W = 80.0                        # deg: the world's width on the board (lon -170..190)
LON0, LAT0 = 10.0, 12.0             # map centre
S = MAP_W / 360.0                   # deg on the board per degree of longitude or latitude
BOX = (41.0, 20.0)                  # deg: the board's half width and half height
TURN_R, CLEAR = 0.25, 0.3           # deg: sharp spots eased to this; no two parts of a coast closer
BLUR = 0.12                         # deg: the light blur that keeps the real shapes
RES = 0.05                          # deg per grid cell
countries = json.load(open(NE, encoding="utf-8"))["features"]


def clip(ring, side, cut):
    """The part of a ring on one side of a meridian (Sutherland-Hodgman)."""
    keep = (lambda p: p[0] <= cut) if side == "max" else (lambda p: p[0] >= cut)
    out = []
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if keep(b):
            if not keep(a):
                t = (cut - a[0]) / (b[0] - a[0])
                out.append((cut, a[1] + t * (b[1] - a[1])))
            out.append(b)
        elif keep(a):
            t = (cut - a[0]) / (b[0] - a[0])
            out.append((cut, a[1] + t * (b[1] - a[1])))
    return out


def rings(names):
    """The continent's country outlines (lon, lat); COUNTRY_CLIP cuts single countries (Sinai)."""
    out = []
    for f in countries:
        p = f["properties"]
        if p.get("CONTINENT") not in names and p.get("NAME") not in names:
            continue
        g = f["geometry"]
        for poly in (g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]):
            r = [(lon + 360.0 if lon < -150 and "Asia" in names else lon, lat) for lon, lat in poly[0]]
            if "North America" in names:
                r = [(lon - 360.0 if lon > 150 else lon, lat) for lon, lat in r]
            cut = COUNTRY_CLIP.get(p.get("NAME"))
            if cut and len(r) >= 3:
                r = clip(r, *cut)
            if len(r) >= 3:
                out.append(r)
    return out


def board_xy(lon, lat):
    return (lon - LON0) * S, (lat - LAT0) * S


def one_island(mask):
    """The largest island, its lakes filled; None if there is no land."""
    W, H = mask.size
    px = mask.load()
    seen, best = set(), set()
    for j in range(H):
        for i in range(W):
            if px[i, j] and (i, j) not in seen:
                comp, stack = set(), [(i, j)]
                seen.add((i, j))
                while stack:
                    a, b = stack.pop()
                    comp.add((a, b))
                    for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                        if 0 <= c < W and 0 <= d < H and px[c, d] and (c, d) not in seen:
                            seen.add((c, d))
                            stack.append((c, d))
                if len(comp) > len(best):
                    best = comp
    if not best:
        return None
    stack = [(i, j) for i in range(W) for j in (0, H - 1)] + [(i, j) for j in range(H) for i in (0, W - 1)]
    stack = [p for p in stack if p not in best]
    water = set(stack)
    while stack:
        a, b = stack.pop()
        for c, d in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
            if 0 <= c < W and 0 <= d < H and (c, d) not in best and (c, d) not in water:
                water.add((c, d))
                stack.append((c, d))
    out = Image.new("L", (W, H), 0)
    out.putdata([0 if (i, j) in water else 255 for j in range(H) for i in range(W)])
    return out


def coast(mask, x0, z1):
    """The island's edge as a closed loop (deg, y up), traced along the cell edges with land on the right; the grid's
    top-left corner is at (x0, z1)."""
    W, H = mask.size
    px = mask.load()
    land = lambda i, j: 0 <= i < W and 0 <= j < H and px[i, j] > 0
    start = next((i, j) for j in range(H) for i in range(W) if land(i, j))
    x, y, dx, dy = start[0], start[1], 1, 0
    pts, first = [], (x, y, dx, dy)
    for _ in range(4 * W * H):
        pts.append((x, y))
        x, y = x + dx, y + dy
        for ndx, ndy in ((dy, -dx), (dx, dy), (-dy, dx)):
            if ndx == 1:
                r, l = (x, y), (x, y - 1)
            elif ndx == -1:
                r, l = (x - 1, y - 1), (x - 1, y)
            elif ndy == 1:
                r, l = (x - 1, y), (x, y)
            else:
                r, l = (x, y - 1), (x - 1, y - 1)
            if land(*r) and not land(*l):
                dx, dy = ndx, ndy
                break
        if (x, y, dx, dy) == first:
            break
    return [(x0 + a * RES, z1 - b * RES) for a, b in pts]


def continent(name, names):
    """One continent's coast on the board (deg), smoothed into one loop that meets TURN_R and CLEAR."""
    rs = rings(names)
    if name == "Antarctica":                        # the same map, cut at ANT_CUT; west of 170 W wraps east
        pts = []
        for r in rs:
            for side, shift in (("min", 0.0), ("max", 360.0)):
                part = clip(r, side, -170.0)
                if len(part) < 3:
                    continue
                flip = [(lat, lon + shift) for lon, lat in part]          # clip by latitude: swap, clip, swap back
                flip = clip(flip, "min", ANT_CUT)
                if len(flip) >= 3:
                    pts.append([board_xy(lon, lat) for lat, lon in flip])
        pts.append([board_xy(lon, lat) for lon, lat in ((-170.0, ANT_BAND), (190.0, ANT_BAND), (190.0, ANT_CUT),
                                                       (-170.0, ANT_CUT))])
    else:
        pts = [[board_xy(lon, lat) for lon, lat in r] for r in rs]
    xs = [p[0] for r in pts for p in r]
    zs = [p[1] for r in pts for p in r]
    pad = 2.0
    x0, z1 = min(xs) - pad, max(zs) + pad
    w, h = int((max(xs) - min(xs) + 2 * pad) / RES), int((max(zs) - min(zs) + 2 * pad) / RES)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for r in pts:
        d.polygon([((x - x0) / RES, (z1 - z) / RES) for x, z in r], fill=255)
    if name != "Antarctica":
        for ch in CHANNELS:
            d.line([((bx - x0) / RES, (z1 - bz) / RES) for bx, bz in (board_xy(lon, lat) for lon, lat in ch)],
                   fill=0, width=max(1, int(CHANNEL_W / RES)))
    # the lightest blur whose coast keeps CLEAR between its parts, then only the sharp spots eased
    for blur in (BLUR, 0.15, 0.18, 0.22, 0.26, 0.3, 0.35):
        m2 = one_island(mask)
        for _ in range(2):
            m2 = m2.filter(ImageFilter.GaussianBlur(blur / RES)).point(lambda v: 255 if v > 127 else 0)
            m2 = one_island(m2)
        loop = ease(resample(average(resample(coast(m2, x0, z1), 0.05), 5), 0.05), TURN_R)
        tight, close = check(loop, CLEAR)
        if close >= CLEAR:
            break
    return loop, blur, tight, close


def main():
    shapes = []
    for name, names, labels in ORDER:
        loop, blur, tight, close = continent(name, names)
        length = sum(math.dist(a, b) for a, b in zip(loop, loop[1:] + loop[:1]))
        print(f"{name:14s} smoothing {blur} deg: coast {length:.0f} deg, tightest {tight:.2f}, closest "
              f"{min(close, 99):.2f}")
        shapes.append(Shape(name, loop, True, [(text, None if lon is None else board_xy(lon, lat))
                                               for text, lon, lat in labels]))
    build_track(
        shapes, "World Map",
        # the user's own description and tags, set in the game's editor (2026-09-27)
        ("Smooth tracking along a path you can see: the world map on a lecture hall's chalkboard.[nl]Trains staying "
         "on the bot without running ahead of it or overcorrecting.[nl]The bot goes once round each continent's coast "
         "in turn (Africa, Eurasia, North America, South America, Antarctica, Australia), flying the dashed route from "
         "one to the next."),
        tags="World, Map, Tracking, Smooth, Bassel, Bakr",
        top=dict(AimTypeTag="Tracking", AimSubTypeTag="Smoothness", DifficultyTag="4"),
        drop=["Weapon Profile|BB Gun", "Dodge Profile|Mimic"],   # unused; the game's editor dropped them
        box=BOX, turn_r=TURN_R, clear=CLEAR, prepared=True, max_hop=40.0)


if __name__ == "__main__":
    main()
