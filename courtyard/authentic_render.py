"""Reference copy (run from D:/Projects/flowfix with PYTHONPATH=.;test_out/courtyard). Throwaway: player's-view render of the court concept (painter's algorithm, flat-shaded polygons)."""
import math
import sys

from PIL import Image, ImageDraw, ImageFont

import authentic_geo as G

SUN = G.norm((-0.55, -0.35, 0.75))     # toward the sun: behind the player's left shoulder, high


def rgb(slot, n, shadow=False, override=None):
    tint, fb = override.get(slot, G.SLOTS[slot]) if override else G.SLOTS[slot]
    c = [int(tint[i:i + 2], 16) for i in (0, 2, 4)]
    lit = 0.0 if shadow else max(0.0, G.dot(n, SUN))
    k = fb + (1 - fb) * (0.38 + 0.62 * lit)
    return tuple(min(255, int(v * k)) for v in c)


def tiles(p, T):
    pts = p["pts"]
    if len(pts) != 4:
        return [p]
    e1 = math.dist(pts[0], pts[1])
    e2 = math.dist(pts[1], pts[2])
    n1, n2 = max(1, math.ceil(e1 / T)), max(1, math.ceil(e2 / T))
    if n1 * n2 == 1:
        return [p]

    def bil(s, t):
        a = G.add(G.mul(pts[0], (1 - s) * (1 - t)), G.mul(pts[1], s * (1 - t)))
        b = G.add(G.mul(pts[2], s * t), G.mul(pts[3], (1 - s) * t))
        return G.add(a, b)
    out = []
    for i in range(n1):
        for j in range(n2):
            q = dict(p)
            q["pts"] = [bil(i / n1, j / n2), bil((i + 1) / n1, j / n2), bil((i + 1) / n1, (j + 1) / n2), bil(i / n1, (j + 1) / n2)]
            out.append(q)
    return out


def render(L, objs, path, W=1920, H=1080, SS=2, override=None, sky=((226, 218, 196), (118, 160, 206)),
           caption=None, envelope=True):
    Wp, Hp = W * SS, H * SS
    f = (Wp / 2) / G.TANH
    img = Image.new("RGB", (Wp, Hp))
    d = ImageDraw.Draw(img)
    for row in range(Hp):                                   # sky gradient (the theme sets the real sky)
        v = (Hp / 2 - row) / f
        t = max(0.0, min(1.0, v / G.TANV)) ** 0.8
        c = tuple(int(sky[0][i] + (sky[1][i] - sky[0][i]) * t) for i in range(3))
        d.line([(0, row), (Wp, row)], fill=c)

    def proj(p):
        dd = p[0] - G.EYE_X
        return (Wp / 2 + f * p[1] / dd, Hp / 2 - f * p[2] / dd)
    eye = (G.EYE_X, 0.0, 0.0)
    ground, rest = [], []
    for p in L["window"]:
        rest.append(p)
    for o in objs:
        for p in o["polys"]:
            if "ground" in p and p["n"][2] < 0.9:
                continue            # pavement / pool sides: buried in the floor or behind the kerb in game
            (ground if "ground" in p else rest).append(p)
    for p in sorted(ground, key=lambda q: q["ground"]):
        if G.dot(p["n"], G.sub(eye, G.centroid(p["pts"]))) > 0:
            d.polygon([proj(v) for v in p["pts"]], fill=rgb(p["slot"], p["n"], p.get("shadow"), override))
    items, grp_d = [], {}
    for p in rest:
        c = G.centroid(p["pts"])
        if G.dot(p["n"], G.sub(eye, c)) <= 0:
            continue
        if "grp" in p:
            grp_d.setdefault(p["grp"], []).append(c[0] - G.EYE_X)
            items.append((p["grp"], p.get("ord", 0), p))
            continue
        T = 90 if c[0] < 0 else 100000
        for q in tiles(p, T):
            cq = G.centroid(q["pts"])
            items.append((cq[0] - G.EYE_X, 0, q))
    gd = {k: sum(v) / len(v) for k, v in grp_d.items()}
    items = [(gd[a] if isinstance(a, tuple) else a, b, q) for a, b, q in items]
    items.sort(key=lambda t: (-t[0], t[1]))
    for _, _, q in items:
        d.polygon([proj(v) for v in q["pts"]], fill=rgb(q["slot"], q["n"], q.get("shadow"), override))
    if envelope:
        y0, y1, z0, z1 = L["env"]
        k = arena_k = 1.0 / (-2900 - G.EYE_X)
        box = [proj((-2900, y0, z1)), proj((-2900, y1, z0))]
        d.rectangle([box[0][0], box[0][1], box[1][0], box[1][1]], outline=(220, 30, 30), width=2 * SS)
    img = img.resize((W, H), Image.LANCZOS)
    if caption:
        dr = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 18)
        dr.rectangle([0, H - 30, W, H], fill=(20, 20, 20))
        dr.text((10, H - 26), caption, fill=(235, 235, 235), font=font)
    img.save(path)
    return img


if __name__ == "__main__":
    lay = sys.argv[1] if len(sys.argv) > 1 else "Overflick"
    out = sys.argv[2] if len(sys.argv) > 2 else r"D:\Projects\flowfix\test_out\courtyard\authentic_view.png"
    L = G.layout(rf"D:\Projects\flowfix\test_out\egypt_window_all\Flow Fix {lay}.sce")
    objs = G.court(L)
    print("F", L["F"], "yc", L["yc"], "D", round(L["D"], 1), "cols", [round(c) for c in L["cols"]], "objects", len(objs))
    render(L, objs, out, caption=f"Flow Fix {lay}: authentic palace court concept, player's view (eye (-6000,0,0), 103 FOV, 16:9), "
                                 "default colours, no theme; red = target envelope; sky is set by the theme")
    print("saved", out)
