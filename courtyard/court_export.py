"""Turn the courtyard pieces from final_geo.court() into map brushes (2026-09-24).

A piece is a plain block ({"kind": "box", "box": (x0, x1, y0, y1, z0, z1), "slot": (group, surface)}) or a custom
mesh made of polygons ({"kind": "mesh", "polys": [{"pts", "n", "slot"}]}). Meshes get one section per material slot,
vertices divided by MapScale, and the winding installed maps use (see mechanics.md, "Custom meshes").
"""
import copy

import authentic_geo as A


def export(o, template, map_scale, group):
    """One court piece as a brush: a plain block, or a custom mesh with one section per material slot."""
    b = copy.deepcopy(template)
    for k in ("group", "materialSets", "procedural"):
        b.pop(k, None)
    b.update({"name": "DefaultNoCollision", "rotation": "0.000000, 0.000000, 0.000000", "group": group})
    if o["kind"] == "box":
        x0, x1, y0, y1, z0, z1 = o["box"]
        b["location"] = f"{x0:.6f}, {y0:.6f}, {z0:.6f}"
        b["scale"] = f"{(x1 - x0) / 100:.6f}, {(y1 - y0) / 100:.6f}, {(z1 - z0) / 100:.6f}"
        b["materialSets"] = [{"group": o["slot"][0], "surface": o["slot"][1]} for _ in range(6)]
        return b
    secs = {}
    for p in o["polys"]:
        secs.setdefault(p["slot"], []).append(p)
    allv = [v for p in o["polys"] for v in p["pts"]]
    origin = tuple(min(v[i] for v in allv) for i in range(3))
    b.update({"location": "%.6f, %.6f, %.6f" % origin, "mesh": "Cube", "scale": "1.000000, 1.000000, 1.000000",
              "type": "brush"})
    b["materialSets"] = [{"group": s[0], "surface": s[1]} for s in secs]
    b["procedural"] = []
    for ps in secs.values():
        verts, idx = [], []
        for p in ps:
            n = p["n"]
            base = len(verts)
            e1 = A.norm(A.sub(p["pts"][1], p["pts"][0]))
            for v in p["pts"]:
                verts.append({"location": "%.6f, %.6f, %.6f" % tuple((v[i] - origin[i]) / map_scale for i in range(3)),
                              "normal": "%.6f, %.6f, %.6f" % n, "tangent": "%.6f, %.6f, %.6f, false" % e1,
                              "uv0": "%.6f, %.6f" % (A.dot(v, e1) / 100.0, A.dot(v, A.cross(n, e1)) / 100.0)})
            for k in range(1, len(p["pts"]) - 1):
                a, bb, c = p["pts"][0], p["pts"][k], p["pts"][k + 1]
                tri = [base, base + k, base + k + 1]
                if A.dot(A.cross(A.sub(bb, a), A.sub(c, a)), n) > 0:   # installed winding: against the normal
                    tri = [base, base + k + 1, base + k]
                idx += tri
        b["procedural"].append({"indices": idx, "vertices": verts})
    return b


def pure(tint, fullbright):
    """A flat-colour material entry (tint as RRGGBB)."""
    return {"material": "MI_WA_PureColor", "pack": "Default", "properties": [
        {"name": "Tint", "value": tint + "ff"}, {"name": "Scale", "value": 1.0}, {"name": "Roughness", "value": 0.9},
        {"name": "Metallic", "value": 0.0}, {"name": "FullBright", "value": fullbright}]}
