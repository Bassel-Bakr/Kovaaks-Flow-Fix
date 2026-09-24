"""Turn hieroglyph signs into straight strokes: one rotated block per stroke (see mechanics.md, brush rotation).

The font draws signs as line art. Each sign is rendered large, thinned to a 1-pixel skeleton (Zhang-Suen),
traced into polylines, and simplified (Ramer-Douglas-Peucker) into segments. Pure Python: no numpy here.

sign_strokes(char, em=EM) -> list of segments ((y0, z0), (y1, z1)) in em-pixel units, origin top-left,
z pointing down, plus the sign's (width, height).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = r"C:\Windows\Fonts\seguihis.ttf"
EM = 120         # render size in pixels (72 left fragments inside the vulture and a lumpy foot)
EPS = 3.0        # simplification tolerance in pixels (4.0 before the traces were smoothed; 1.5 left straight lines wavy)
SMOOTH = 2       # traces are averaged over 2 * SMOOTH + 1 pixels first, so curves stay curves without pixel steps
MIN_LEN = 6      # drop traces shorter than this many pixels
# Signs whose detail is too fine for the font's line art to survive thinning: drawn explicitly.
ZIGZAG = {"𓈖": 4}   # water ripple: number of teeth


def render(char, em=EM):
    font = ImageFont.truetype(FONT, em)
    l, t, r, b = font.getbbox(char)
    pad = 4
    img = Image.new("L", (r - l + 2 * pad, b - t + 2 * pad), 0)
    ImageDraw.Draw(img).text((pad - l, pad - t), char, font=font, fill=255)
    img = img.filter(ImageFilter.MaxFilter(3))
    w, h = img.size
    px = img.load()
    return [[1 if px[x, y] > 90 else 0 for x in range(w)] for y in range(h)]


def thin(g):
    """Zhang-Suen thinning, in place."""
    h, w = len(g), len(g[0])

    def nb(y, x):
        return [g[y - 1][x], g[y - 1][x + 1], g[y][x + 1], g[y + 1][x + 1],
                g[y + 1][x], g[y + 1][x - 1], g[y][x - 1], g[y - 1][x - 1]]
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            kill = []
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    if not g[y][x]:
                        continue
                    p = nb(y, x)
                    b = sum(p)
                    if not 2 <= b <= 6:
                        continue
                    a = sum(1 for i in range(8) if p[i] == 0 and p[(i + 1) % 8] == 1)
                    if a != 1:
                        continue
                    if step == 0 and p[0] * p[2] * p[4] == 0 and p[2] * p[4] * p[6] == 0:
                        kill.append((y, x))
                    if step == 1 and p[0] * p[2] * p[6] == 0 and p[0] * p[4] * p[6] == 0:
                        kill.append((y, x))
            for y, x in kill:
                g[y][x] = 0
            changed = changed or bool(kill)
    return g


N4 = [(-1, 0), (0, 1), (1, 0), (0, -1)]
N8 = N4 + [(-1, 1), (1, 1), (1, -1), (-1, -1)]


def trace(g):
    """Cover the skeleton with polylines: start at endpoints, walk to unvisited neighbours (4-neighbours
    first), and restart until every pixel is visited."""
    h, w = len(g), len(g[0])
    on = {(y, x) for y in range(h) for x in range(w) if g[y][x]}
    seen, paths = set(), []

    def free(p):
        return [(p[0] + dy, p[1] + dx) for dy, dx in N8 if (p[0] + dy, p[1] + dx) in on
                and (p[0] + dy, p[1] + dx) not in seen]
    while len(seen) < len(on):
        rest = [p for p in on if p not in seen]
        start = min(rest, key=lambda p: (len(free(p)), p))
        path, cur = [start], start
        seen.add(start)
        while True:
            nxt = [(cur[0] + dy, cur[1] + dx) for dy, dx in N4 if (cur[0] + dy, cur[1] + dx) in on
                   and (cur[0] + dy, cur[1] + dx) not in seen] or free(cur)
            if not nxt:
                break
            cur = nxt[0]
            seen.add(cur)
            path.append(cur)
        # join a path end to an already-drawn neighbour so strokes meet at junctions
        for end, idx in ((path[-1], len(path)), (path[0], 0)):
            touch = [(end[0] + dy, end[1] + dx) for dy, dx in N8 if (end[0] + dy, end[1] + dx) in on
                     and (end[0] + dy, end[1] + dx) not in path]
            if touch:
                path.insert(idx, touch[0])
        if len(path) >= MIN_LEN:
            paths.append(path)
    return paths


def smooth(path, k=None):
    """A traced path averaged over 2k + 1 neighbours (fewer near its ends, which stay fixed)."""
    k = SMOOTH if k is None else k
    if k <= 0 or len(path) < 3:
        return path
    out = [path[0]]
    for i in range(1, len(path) - 1):
        h = min(k, i, len(path) - 1 - i)
        win = path[i - h:i + h + 1]
        out.append((sum(p[0] for p in win) / len(win), sum(p[1] for p in win) / len(win)))
    return out + [path[-1]]


def rdp(pts, eps=EPS):
    if len(pts) < 3:
        return pts
    (y0, x0), (y1, x1) = pts[0], pts[-1]
    dy, dx = y1 - y0, x1 - x0
    norm = (dy * dy + dx * dx) ** 0.5 or 1.0
    far, idx = 0.0, 0
    for i, (y, x) in enumerate(pts[1:-1], 1):
        d = abs(dy * (x - x0) - dx * (y - y0)) / norm
        if d > far:
            far, idx = d, i
    if far <= eps:
        return [pts[0], pts[-1]]
    return rdp(pts[: idx + 1], eps)[:-1] + rdp(pts[idx:], eps)


def zigzag(char, teeth, em):
    g = render(char, em)
    rows = [y for y, r in enumerate(g) if any(r)]
    cols = [x for x in range(len(g[0])) if any(r[x] for r in g)]
    w, h = cols[-1] - cols[0], max(rows[-1] - rows[0], em * 0.08)
    pts = [(w * i / (2 * teeth), 0 if i % 2 else h) for i in range(2 * teeth + 1)]
    return [(a, b) for a, b in zip(pts, pts[1:])], (w, h)


def sign_strokes(char, em=EM):
    if char in ZIGZAG:
        return zigzag(char, ZIGZAG[char], em)
    g = thin(render(char, em))
    segs = []
    for path in trace(g):
        pts = rdp(smooth(path), EPS)   # read EPS and SMOOTH at call time, so callers can change them
        segs += [((a[1], a[0]), (b[1], b[0])) for a, b in zip(pts, pts[1:])]
    ys = [c for s in segs for c in (s[0][0], s[1][0])]
    zs = [c for s in segs for c in (s[0][1], s[1][1])]
    y0, z0 = min(ys), min(zs)
    segs = [((a[0] - y0, a[1] - z0), (b[0] - y0, b[1] - z0)) for a, b in segs]
    return segs, (max(ys) - y0, max(zs) - z0)


if __name__ == "__main__":
    import json
    text = json.load(open("inscriptions.json", encoding="utf-8"))["text"]
    for k in ("welcome", "madeby", "name"):
        for ch in text[k].replace(" ", ""):
            segs, size = sign_strokes(ch)
            print(k, ch, len(segs), "strokes", size)
