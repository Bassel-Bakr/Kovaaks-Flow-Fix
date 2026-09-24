"""Scratch (run from D:/Projects/flowfix with PYTHONPATH=.;test_out/courtyard): renders of the FINAL courtyard.
Player's view (painter's algorithm, flat-shaded polygons, assumed sun), a Bassel 3 approximation, a 4-layout
sheet, the plan, and per-element screen coverage from an object-id buffer."""
import math
import sys

from PIL import Image, ImageDraw, ImageFont

import authentic_geo as A
import final_geo as G
from authentic_render import tiles

SUN = A.norm((-0.55, -0.35, 0.75))     # toward the sun: behind the player's left shoulder, high (assumed)
OUT = r"D:\Projects\flowfix\test_out\courtyard"
FONT = lambda s: ImageFont.truetype("arial.ttf", s)
FONTB = lambda s: ImageFont.truetype("arialbd.ttf", s)

# Bassel 3 (from its file): MARBLE POLISHED white on all four types; wall full-bright 0.76, the rest 1.0 (flat).
MARBLE = "d9d9db"
B3 = {s: (MARBLE, 0.76 if s[1] == "wall" else 1.0) for s in G.PAL}
B3_SKY = ((179, 180, 182), (179, 180, 182))
DEFAULT_SKY = ((226, 218, 196), (118, 160, 206))


def rgb(slot, n, shadow, pal):
    tint, fb = pal[slot]
    c = [int(tint[i:i + 2], 16) for i in (0, 2, 4)]
    lit = 0.0 if shadow else max(0.0, A.dot(n, SUN))
    k = fb + (1 - fb) * (0.38 + 0.62 * lit)
    return tuple(min(255, int(v * k)) for v in c)


def draw_list(L, objs, with_shadows=True):
    """Painter's list: (poly, object id). Ground first (by order), then far to near; columns as groups."""
    eye = (G.EYE_X, 0.0, 0.0)
    ground, rest = [], []
    for p in L["window"]:
        rest.append((p, 1))
    for oi, o in enumerate(objs):
        for p in o["polys"]:
            if "ground" in p and p["n"][2] < 0.9:
                continue                        # floor / pool / stylobate sides: buried or hidden in game
            (ground if "ground" in p else rest).append((p, oi + 2))
    if with_shadows:
        for p in L.get("shadows", []):
            rest.append((p, 99))
    out = []
    for p, oid in sorted(ground, key=lambda t: t[0]["ground"]):
        if A.dot(p["n"], A.sub(eye, A.centroid(p["pts"]))) > 0:
            out.append((p, oid))
    items, grp_d = [], {}
    for p, oid in rest:
        c = A.centroid(p["pts"])
        if A.dot(p["n"], A.sub(eye, c)) <= 0:
            continue
        if "grp" in p:
            grp_d.setdefault(p["grp"], []).append(c[0] - G.EYE_X)
            items.append((p["grp"], p.get("ord", 0), p, oid))
            continue
        T = 90 if c[0] < -1000 else 100000
        for q in tiles(p, T):
            cq = A.centroid(q["pts"])
            items.append((cq[0] - G.EYE_X + (-0.2 if q.get("shadow") else 0), 0, q, oid))
    gd = {k: sum(v) / len(v) for k, v in grp_d.items()}
    items = [(gd[a] if isinstance(a, tuple) else a, b, q, oid) for a, b, q, oid in items]
    items.sort(key=lambda t: (-t[0], t[1]))
    return out + [(q, oid) for _, _, q, oid in items]


def render(L, objs, path=None, pal=None, sky=DEFAULT_SKY, caption=None, envelope=True, W=1920, H=1080, SS=2,
           ids=False):
    pal = pal or G.PAL
    win_pal = dict(pal)
    Wp, Hp = W * SS, H * SS
    f = (Wp / 2) / G.TANH
    img = Image.new("RGB", (Wp, Hp))
    d = ImageDraw.Draw(img)
    for row in range(Hp):
        v = (Hp / 2 - row) / f
        t = max(0.0, min(1.0, v / G.TANV)) ** 0.8
        d.line([(0, row), (Wp, row)], fill=tuple(int(sky[0][i] + (sky[1][i] - sky[0][i]) * t) for i in range(3)))
    idimg = Image.new("L", (Wp, Hp), 0) if ids else None
    di = ImageDraw.Draw(idimg) if ids else None

    def proj(p):
        dd = p[0] - G.EYE_X
        return (Wp / 2 + f * p[1] / dd, Hp / 2 - f * p[2] / dd)
    for q, oid in draw_list(L, objs):
        pts = [proj(v) for v in q["pts"]]
        d.polygon(pts, fill=rgb(q["slot"], q["n"], q.get("shadow"), win_pal))
        if ids and oid != 99:
            di.polygon(pts, fill=oid)
    if envelope:
        y0, y1, z0, z1 = L["env"]
        a, b = proj((-2900, y0, z1)), proj((-2900, y1, z0))
        d.rectangle([a[0], a[1], b[0], b[1]], outline=(220, 30, 30), width=2 * SS)
    img = img.resize((W, H), Image.LANCZOS)
    if caption:
        dr = ImageDraw.Draw(img)
        dr.rectangle([0, H - 30, W, H], fill=(20, 20, 20))
        dr.text((10, H - 26), caption, fill=(235, 235, 235), font=FONT(18))
    if path:
        img.save(path)
    if ids:
        hist = idimg.histogram()
        tot = Wp * Hp
        return img, {i: hist[i] / tot for i in range(256) if hist[i]}
    return img


def coverage(L, objs):
    _, cov = render(L, objs, envelope=False, SS=1, ids=True)
    named = {"sky": cov.get(0, 0.0), "window": cov.get(1, 0.0)}
    for oi, o in enumerate(objs):
        named[o["name"]] = cov.get(oi + 2, 0.0)
    return named


def layouts_sheet(names, path):
    W, H = 960, 540
    sheet = Image.new("RGB", (2 * W, 2 * H))
    for i, nm in enumerate(names):
        L = G.load(nm)
        objs = G.court(L)
        im = render(L, objs, W=W, H=H, SS=2)
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, H - 26, W, H], fill=(20, 20, 20))
        dr.text((8, H - 23), f"{nm}  (floor z {L['F']:.0f}, {len(objs)} objects)", fill=(235, 235, 235), font=FONT(17))
        sheet.paste(im, ((i % 2) * W, (i // 2) * H))
    sheet.save(path)


def plan(path):
    L = G.load("Overflick")
    objs = G.court(L)
    info = L["info"]
    yc = L["yc"]
    img = Image.new("RGB", (2200, 1520), (247, 245, 240))
    d = ImageDraw.Draw(img)
    # ---- panel A: the court, x -6300..-1100 across, y -5600..5600 up
    S, ox, oy = 0.125, 60, 100
    P = lambda x, y: (ox + (x + 6300) * S, oy + (5600 - y) * S)

    def rect(x0, x1, y0, y1, fill, outline=None, width=1):
        a, b = P(x0, max(y0, y1)), P(x1, min(y0, y1))
        d.rectangle([a[0], a[1], b[0], b[1]], fill=fill, outline=outline, width=width)
    d.text((ox, 30), "A. The court (Overflick, floor z = -968). x across toward the targets, +y up = screen right",
           fill=(20, 20, 20), font=FONTB(20))
    d.rectangle([P(-6300, 5600), P(-1100, -5600)], outline=(170, 170, 170))
    rect(-4900, G.XW1, yc - 5400, yc + 5400, (150, 146, 138))                       # 1 floor
    rect(-4495, -3405, yc - 375, yc + 375, (222, 208, 172))                         # 2 kerb
    rect(-4450, -3450, yc - 330, yc + 330, (22, 48, 88))                            # 2 water
    for side, sg in (("left", -1), ("right", 1)):
        py0, py1 = info[f"py0_{side}"], info[f"py1_{side}"]
        stone = L["stoneL"] if sg < 0 else L["stoneR"]
        rect(G.XW0, G.XW1, stone - sg * 60, yc + sg * 5400, (93, 96, 102))          # 3 palace wall
        rect(G.XS, G.XW0, py0 - sg * 40, py1, (222, 208, 172))                      # 5 stylobate
        rect(G.XP, G.XW0, py0, py1, None, outline=(93, 96, 102), width=3)           # 4 roof outline
        for cy in info[f"cols_{side}"]:
            c = P(G.XC, cy)
            d.ellipse([c[0] - 118 * S, c[1] - 118 * S, c[0] + 118 * S, c[1] + 118 * S], fill=(154, 63, 34),
                      outline=(212, 160, 42), width=2)
        yi0 = yc + sg * G.Y_TW
        d.polygon([P(G.XT, yi0), P(G.XTB, yi0), P(G.XTB, yc + sg * 5400), P(G.XT, yc + sg * 5400)], fill=(70, 72, 77))
        pl = L["plinthL"] if sg < 0 else L["plinthR"]
        rect(-3090, -3020, pl, pl - sg * 476, (222, 208, 172))                      # plinth
        lion = L["lionL"] if sg < 0 else L["lionR"]
        rect(-3060, -3030, lion[2], lion[3], (15, 42, 77))                           # lion (drawn thicker than it is)
    rect(-3020, -2900, L["stoneL"], L["stoneR"], (234, 219, 182), outline=(160, 150, 120))  # window stone
    rect(-2900, -2890, L["env"][0] - 60, L["env"][1] + 60, (200, 200, 200))
    d.line([P(-2950, L["env"][0]), P(-2950, L["env"][1])], fill=(220, 30, 30), width=5)
    dp = G.X_PALM - G.EYE_X
    uL, uR = info["palm_u"]
    for u, rr in ((uL, 600), (uR, 560)):                                             # palms: crown width
        c = P(G.X_PALM, u * dp)
        d.line([P(G.X_PALM, u * dp - rr), P(G.X_PALM, u * dp + rr)], fill=(80, 82, 88), width=5)
        d.ellipse([c[0] - 6, c[1] - 6, c[0] + 6, c[1] + 6], fill=(80, 82, 88))
    eye = P(-6000, 0)
    d.ellipse([eye[0] - 7, eye[1] - 7, eye[0] + 7, eye[1] + 7], fill=(200, 30, 30))
    for sg in (-1, 1):
        d.line([eye, P(-6000 + 5600 / G.TANH, sg * 5600)], fill=(60, 90, 200), width=2)
        d.line([eye, P(-2900, L["env"][0 if sg < 0 else 1])], fill=(220, 90, 90), width=1)
    labels = [(1, -4300, 3900), (2, -3950, 0), (3, -2770, 4600), (4, -2990, 2550), (5, -3400, -2450), (6, -3060, -4300),
              (7, -1500, -3200), (8, -1500, 3200), (9, -2960, 1500), (10, -3055, -1580)]
    for n, x, y in labels:
        c = P(x, y)
        d.ellipse([c[0] - 13, c[1] - 13, c[0] + 13, c[1] + 13], fill=(255, 255, 255), outline=(20, 20, 20), width=2)
        d.text((c[0] - (5 if n < 10 else 10), c[1] - 10), str(n), fill=(20, 20, 20), font=FONTB(17))
    d.line([P(-6100, -5450), P(-5100, -5450)], fill=(20, 20, 20), width=3)
    d.text(P(-6100, -5250), "1000 units", fill=(20, 20, 20), font=FONT(15))
    tx, ty = 760, 100
    notes = [
        "1  Court floor: block x -4900..-2720, y +-5400, z F-60..F. Paving (g1 ceiling).",
        "2  Pool: navy water 1000 x 660 (z F..F+5) in a limestone kerb, 4 blocks 45 wide, 30 high.",
        "3  Palace front wall: block x -2820..-2720, from behind the pilaster to y +-5400,",
        "   z F..185. Face 80 behind the backdrop plane: it cannot cover a target.",
        "4  Portico roof: block x -3160..-2820, z 35..185, from 170 past the lion plinth",
        "   to the tower. Crown on its front: red band, cavetto, round merlons (to z 380).",
        "5  Colonnade: limestone stylobate x -3220..-2820 (40 high) and N palm columns",
        "   at x -3085, 330 apart (N = 3 here, 2-4 by layout): red shaft, gold band",
        "   and capital, limestone base and abacus.",
        "6  Corner tower (migdol): battered block x -3230..-2900, |y| 3050..5400,",
        "   z F..780, crown x1.25 with merlons to z 1024. Cut off by the screen edge.",
        "7  Date palm, 8  doum palm: flat grey stencils at x -1500, trunks hidden by",
        "   the palace wall; crowns at u +-0.60 (moved out for wider windows).",
        "9  The existing window (unchanged); red bar = target envelope at x -2950.",
        "10 Lions on plinths (unchanged); the palace wall now shows through them.",
        "",
        "Blue: 103-degree view cone. Pink: sight lines to the target envelope.",
        "Only the floor, pool, kerb, colonnade and portico lie in front of the",
        "targets, all outside the pink lines on screen.",
        "Skyline heights are absolute (z 185 / 380 / 1024), so the skyline",
        "sits at the same screen height in all 13 scenarios; the floor,",
        "stylobates and column bases follow each window's base F.",
        "",
        "Objects: 18 (10 blocks, 8 meshes), about 2,600 triangles.",
        "Stage A: floor, pool, kerb, walls, roofs, skylines (12 objects).",
        "Stage B: + colonnades (2).  Stage C: + pyramids and palms (4).",
    ]
    for i, t in enumerate(notes):
        d.text((tx, ty + i * 25), t, fill=(30, 30, 30), font=FONT(16))
    py = ty + len(notes) * 25 + 20
    d.text((tx, py), "Palette (8 slots; 2 groups + None, as now)", fill=(20, 20, 20), font=FONTB(17))
    uses = {G.PALACE: "RETINT (was 2b1d12): palace, roofs, towers, palms, outlines",
            G.LAPIS: "unchanged: headdress",
            G.LIME: "unchanged: window stone + kerb, crowns, bases, pyramids",
            G.OCHRE: "unchanged: bead, manes + crown bands, column shafts",
            G.BACK: "unchanged: target backdrop only",
            G.NAVY: "unchanged: signs, lion bodies, outlines + pool water",
            G.PAVE: "FREE slot, repainted: court paving only",
            G.GOLD: "unchanged: face, sill strip + column bands, capitals"}
    for i, (s, (tint, fb)) in enumerate(G.PAL.items()):
        yy = py + 30 + i * 27
        d.rectangle([tx, yy, tx + 34, yy + 20], fill=tuple(int(tint[k:k + 2], 16) for k in (0, 2, 4)), outline=(60, 60, 60))
        d.text((tx + 44, yy + 1), f"g{s[0]} {s[1]:7} {tint} fb {fb:.2f}  {uses[s]}", fill=(30, 30, 30), font=FONT(15))
    py += 30 + 8 * 27 + 16
    d.text((tx, py), "Checks: check_scene.py passes on all 13 builds with the court added;", fill=(30, 30, 30), font=FONT(16))
    d.text((tx, py + 25), "closest approach to a target envelope 194 units (the floor), nothing", fill=(30, 30, 30), font=FONT(16))
    d.text((tx, py + 50), "behind the head, nothing in front of the lions.", fill=(30, 30, 30), font=FONT(16))
    # ---- panel B: the far field
    S2, ox2, oy2 = 0.0165, 1420, 100
    P2 = lambda x, y: (ox2 + (x + 7000) * S2, oy2 + (40000 - y) * S2)
    d.text((ox2, 30), "B. Far field (same axes, 1/7.6 the scale)", fill=(20, 20, 20), font=FONTB(20))
    d.rectangle([P2(-7000, 40000), P2(39000, -40000)], outline=(170, 170, 170))
    pyr = {k: v for k, v in info.items() if k in G.PYRAMIDS_L or k in G.PYRAMIDS_R}
    for nm, (xc, ycc, b, h) in pyr.items():
        d.rectangle([P2(xc - b, ycc + b), P2(xc + b, ycc - b)], fill=(232, 220, 186), outline=(150, 130, 90), width=2)
    e2 = P2(-6000, 0)
    for nm, (xc, ycc, b, h) in pyr.items():
        c = P2(xc, ycc)
        d.line([e2, c], fill=(190, 160, 110), width=1)
        d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=(120, 100, 60))
        d.text((c[0] + 8, c[1] - 8), f"{nm}, apex z {h + G.Z_PYR:.0f}", fill=(20, 20, 20), font=FONT(14))
    for sg in (-1, 1):
        d.line([e2, P2(-6000 + 40000 / G.TANH, sg * 40000)], fill=(60, 90, 200), width=2)
    d.rectangle([P2(-6300, 5600), P2(-1100, -5600)], outline=(200, 30, 30), width=2)
    d.text((ox2 + 10, oy2 + 1330), "Red box: panel A. Plain square pyramids, cardinal (axis-aligned), one mesh a side.",
           fill=(20, 20, 20), font=FONT(14))
    d.text((ox2 + 10, oy2 + 1350), "Bases at z -1200, hidden by the palace wall; only the tops show above the merlons.",
           fill=(20, 20, 20), font=FONT(14))
    img.save(path)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "view"
    if what == "view":
        L = G.load("Overflick")
        objs = G.court(L)
        render(L, objs, OUT + r"\final_view.png",
               caption="FINAL court, Overflick: player's view (eye (-6000,0,0), 103 FOV, 16:9), no theme, assumed sun "
                       "front-left; red = target envelope; the theme sets the real sky")
        render(L, objs, OUT + r"\final_view_bassel3.png", pal=B3, sky=B3_SKY,
               caption="FINAL court under an approximation of Bassel 3 (marble; wall type full-bright 0.76, floor/ceiling/"
                       "ramp flat 1.0; solid sky b3b4b6)")
        cov = coverage(L, objs)
        for k, v in sorted(cov.items(), key=lambda t: -t[1]):
            print(f"  {k:22} {100 * v:5.1f}%")
    elif what == "sheet":
        layouts_sheet(["Pacing Drop", "Early Braking", "Speed Build", "Pathing"], OUT + r"\final_layouts.png")
    elif what == "plan":
        plan(OUT + r"\final_plan.png")
