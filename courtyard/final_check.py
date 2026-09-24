"""Scratch (run from D:/Projects/flowfix with PYTHONPATH=.;test_out/courtyard): export the FINAL court into copies
of the 13 current builds (out/*.sce -> test_out/courtyard/final_check_sce, never installed) so check_scene.py can
test real custom meshes, and run finer screen-space checks: clearance to the target envelope, the head's sky,
nothing in front of the lions, object and triangle counts."""
import copy
import glob
import json
import math
import os

import authentic_geo as A
import final_geo as G

DST = r"D:\Projects\flowfix\test_out\courtyard\final_check_sce"


def proj(p):
    k = (-2900 - G.EYE_X) / (p[0] - G.EYE_X)
    return p[1] * k, p[2] * k


def export(o, template, ms):
    b = copy.deepcopy(template)
    for k in ("group", "materialSets", "procedural"):
        b.pop(k, None)
    b["name"] = "DefaultNoCollision"
    b["rotation"] = "0.000000, 0.000000, 0.000000"
    b["group"] = 90
    if o["kind"] == "box":
        x0, x1, y0, y1, z0, z1 = o["box"]
        b["location"] = f"{x0:.6f}, {y0:.6f}, {z0:.6f}"
        b["scale"] = f"{(x1 - x0) / 100:.6f}, {(y1 - y0) / 100:.6f}, {(z1 - z0) / 100:.6f}"
        b["materialSets"] = [{"group": o["slot"][0], "surface": o["slot"][1]} for _ in range(6)]
        return b, 12
    secs = {}
    for p in o["polys"]:
        secs.setdefault(p["slot"], []).append(p)
    allv = [v for p in o["polys"] for v in p["pts"]]
    origin = tuple(min(v[i] for v in allv) for i in range(3))
    b.update({"location": "%.6f, %.6f, %.6f" % origin, "mesh": "Cube", "scale": "1.000000, 1.000000, 1.000000",
              "type": "brush"})
    b["materialSets"] = [{"group": s[0], "surface": s[1]} for s in secs]
    b["procedural"] = []
    ntri = 0
    for slot, ps in secs.items():
        verts, idx = [], []
        for p in ps:
            n = p["n"]
            base = len(verts)
            e1 = A.norm(A.sub(p["pts"][1], p["pts"][0]))
            for v in p["pts"]:
                verts.append({"location": "%.6f, %.6f, %.6f" % tuple((v[i] - origin[i]) / ms for i in range(3)),
                              "normal": "%.6f, %.6f, %.6f" % n, "tangent": "%.6f, %.6f, %.6f, false" % e1,
                              "uv0": "%.6f, %.6f" % (A.dot(v, e1) / 100.0, A.dot(v, A.cross(n, e1)) / 100.0)})
            for k in range(1, len(p["pts"]) - 1):
                a, bb, c = p["pts"][0], p["pts"][k], p["pts"][k + 1]
                cr = A.cross(A.sub(bb, a), A.sub(c, a))
                tri = [base, base + k, base + k + 1]
                if A.dot(cr, n) > 0:                  # installed winding: (B-A)x(C-A) points against the normal
                    tri = [base, base + k + 1, base + k]
                idx += tri
                ntri += 1
        b["procedural"].append({"indices": idx, "vertices": verts})
    return b, ntri


def set_slot(m, group, surface, tint, fb):
    for q in m["materialSets"][group][surface]["properties"]:
        if q["name"] == "Tint":
            q["value"] = tint + "ff"
        if q["name"] == "FullBright":
            q["value"] = fb


os.makedirs(DST, exist_ok=True)
rows = []
for path in sorted(glob.glob(G.WINDOWS + r"\*.sce")):
    name = os.path.basename(path)[len("Flow Fix "):-4]
    L = G.load(name)
    objs = G.court(L)
    m = copy.deepcopy(L["map"])
    template = next(o for o in m["objects"] if o.get("name") == "DefaultNoCollision" and "procedural" not in o)
    ms_fields = m["materialSets"][0]["wall"]["properties"]
    set_slot(m, 0, "wall", G.PAL[G.PALACE][0], G.PAL[G.PALACE][1])
    set_slot(m, 1, "ceiling", G.PAL[G.PAVE][0], G.PAL[G.PAVE][1])
    tris, verts = {}, 0
    for o in objs:
        b, nt = export(o, template, L["ms"])
        m["objects"].append(b)
        tris[o["name"]] = nt
    text = open(path, encoding="utf-8").read()
    head = text[:text.index("[Map Data]") + len("[Map Data]")]
    with open(os.path.join(DST, f"Flow Fix {name}.sce"), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(head + "\n" + json.dumps(m) + "\n")
    # --- finer checks, per polygon
    ty0, ty1, tz0, tz1 = L["env"]
    worst, worst_name = 1e9, None
    for o in objs:
        for p in o["polys"]:
            if min(v[0] for v in p["pts"]) >= L["back"]:
                continue
            q = [proj(v) for v in p["pts"]]
            gy = max(ty0 - max(a for a, _ in q), min(a for a, _ in q) - ty1, 0.0)
            gz = max(tz0 - max(b for _, b in q), min(b for _, b in q) - tz1, 0.0)
            gap = math.hypot(gy, gz)
            if gap < worst:
                worst, worst_name = gap, o["name"]
    # the head's sky: nothing on screen within 150 (wall-plane units) of the head, above the cornice
    hx0, hx1, hy0, hy1, hz0, hz1 = L["head"]
    hq = [proj((hx0, y, z)) for y in (hy0, hy1) for z in (hz0, hz1)]
    Hy0, Hy1 = min(a for a, _ in hq) - 150, max(a for a, _ in hq) + 150
    Hz0 = min(b for _, b in hq)
    behind_head = sorted({o["name"] for o in objs for p in o["polys"]
                          if max(proj(v)[0] for v in p["pts"]) > Hy0 and min(proj(v)[0] for v in p["pts"]) < Hy1
                          and max(proj(v)[1] for v in p["pts"]) > Hz0})
    # lions: nothing wholly in front of the lion plane overlapping a lion on screen
    in_front = set()
    for lion in (L["lionL"], L["lionR"]):
        lq = [proj((lion[0], y, z)) for y in (lion[2], lion[3]) for z in (lion[4], lion[5])]
        ly0, ly1 = min(a for a, _ in lq), max(a for a, _ in lq)
        lz0, lz1 = min(b for _, b in lq), max(b for _, b in lq)
        for o in objs:
            for p in o["polys"]:
                if max(v[0] for v in p["pts"]) > lion[0] or o["name"] == "court floor":
                    continue
                q = [proj(v) for v in p["pts"]]
                if max(a for a, _ in q) > ly0 and min(a for a, _ in q) < ly1 and max(b for _, b in q) > lz0 and min(b for _, b in q) < lz1:
                    in_front.add(o["name"])
    nb = sum(o["kind"] == "box" for o in objs)
    rows.append((name, L, len(objs), nb, sum(tris.values()), worst, worst_name, behind_head, sorted(in_front)))
    print(f"{name:14} F={L['F']:7.0f} cols={len(L['info']['cols_left'])}/{len(L['info']['cols_right'])} "
          f"col_h={L['info']['col_h']:5.0f} palm_u={L['info']['palm_u'][1]:.3f} objects={len(objs)} ({nb} blocks) "
          f"tris={sum(tris.values()):5d} min gap={worst:5.0f} ({worst_name}) behind head={behind_head or '-'} "
          f"in front of lions={sorted(in_front) or '-'}")

name, L, *_ = rows[[r[0] for r in rows].index("Overflick")]
objs = G.court(L)
print("\nOverflick objects:")
for o in objs:
    print(f"  {o['name']:20} {o['kind']:4} stage {o['stage']}  tris {G.tri_count(o):4d}")
print({k: tuple(round(x) for x in v) for k, v in L["info"].items() if k in G.PYRAMIDS_L or k in G.PYRAMIDS_R})
