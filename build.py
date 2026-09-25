"""Build KovaaK's .sce files from workflow specs.

Usage: python build.py specs.json outdir
"""
import copy
import json
import math
import re
import sys
from pathlib import Path

import arena
import egypt

ARENA_DEFAULT = "window"   # the Egyptian window look, rolled out to every scenario on 2026-09-24 (user)
# The base map spawns the player at a random point in a SpawnVolume (half-extent 32 map units), so the view
# shifts slightly on every reload (user report, 2026-09-23). fixed_spawn swaps it for a SpawnPoint at the
# same place. Confirmed in game by the user on 2026-09-23 (the view no longer moves), so it is on for all.
FIXED_SPAWN_DEFAULT = True

SCEN = Path("C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/Saved/SaveGames/Scenarios")
BASE = SCEN / "cA sixshot dense.sce"
SECTION_ORDER = ["Aim Profile", "Ability Profile", "Bot Profile", "Bot Rotation Profile", "Character Profile", "Dodge Profile", "Weapon Profile"]
WALL_X = -2949.999756
HEADER = re.compile(r"^\[(.+)\]$")


# COMPACT_MESHES (2026-09-25): custom-mesh data written one vertex per line and many indices per line, instead of
# one number per line as the game itself writes it. The window look's meshes made the scenario file 12 MB, and the
# sculpted statues 39 MB, mostly indentation; the user saw a hitch on every restart. The game reads it the same
# (the Sand Test loaded, 2026-09-25), so it is on for all.
COMPACT_MESHES = True


def dump_map(m):
    """The map as JSON text: indented like the game writes it, with compact mesh data under COMPACT_MESHES."""
    if not COMPACT_MESHES:
        return json.dumps(m, indent=4)
    meshes = {}
    for o in m["objects"]:
        if o.get("procedural"):
            key = f"@@mesh{len(meshes)}@@"
            meshes[key], o["procedural"] = o["procedural"], key
    try:
        text = json.dumps(m, indent=4)
    finally:
        for o in m["objects"]:
            if isinstance(o.get("procedural"), str):
                o["procedural"] = meshes[o["procedural"]]
    c = lambda v: json.dumps(v, separators=(",", ":"))
    NL = "\n"
    for key, secs in meshes.items():
        parts = []
        for sec in secs:
            idx = sec["indices"]
            rows = [",".join(str(i) for i in idx[k:k + 60]) for k in range(0, len(idx), 60)]
            parts.append('{"indices":[' + NL + (',' + NL).join(rows) + NL + '],"vertices":[' + NL
                         + (',' + NL).join(c(v) for v in sec["vertices"]) + NL + ']}')
        text = text.replace(f'"{key}"', '[' + NL + (',' + NL).join(parts) + NL + ']', 1)
    return text


# SLIM_MESHES (2026-09-25, tested in the Sand Test, on for all): the player never moves (speed 0, no jump, no gravity), so a
# custom-mesh face that points away from the eye can never be seen. slim_meshes() leaves those faces out, drops the
# vertices only they used, and writes mesh numbers with MESH_DECIMALS decimals instead of 6 (0.0001 x MapScale is
# still 0.0003 units). Measured on the Sand Test: 44% fewer triangles, 33% fewer vertices, half the mesh text.
SLIM_MESHES = True
MESH_DECIMALS = 4
EYE_MARGIN = 20.0          # keep a face seen from anywhere within this distance of the eye (map units)


def slim_meshes(m, map_scale):
    """Leave out the custom-mesh faces the fixed eye can never see, and shorten the mesh numbers (see SLIM_MESHES).
    Faces follow the installed winding: (B - A) x (C - A) points into the mesh."""
    sp = next(o for o in m["objects"] if o.get("name") == "SpawnPoint")
    eye = [float(t) for t in sp["location"].split(",")]

    def nums(s):
        parts = [t.strip() for t in s.split(",")]
        return ", ".join(t if t in ("true", "false") else f"{float(t):.{MESH_DECIMALS}f}" for t in parts)
    keep_objects = []
    for o in m["objects"]:
        if not o.get("procedural"):
            keep_objects.append(o)
            continue
        loc = [float(t) for t in o["location"].split(",")]
        plain = (o.get("rotation", "0, 0, 0").replace(" ", "") in ("0,0,0", "0.000000,0.000000,0.000000")
                 and o.get("scale", "1, 1, 1").replace(" ", "") in ("1,1,1", "1.000000,1.000000,1.000000"))
        secs, mats = [], []
        for sec, mat in zip(o["procedural"], o["materialSets"]):
            P = [[loc[i] + float(t) * map_scale for i, t in enumerate(v["location"].split(","))]
                 for v in sec["vertices"]]
            idx = sec["indices"]
            kept = []
            for k in range(0, len(idx), 3):
                a, b, c = (P[i] for i in idx[k:k + 3])
                ab, ac = [b[j] - a[j] for j in range(3)], [c[j] - a[j] for j in range(3)]
                n = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
                ln = math.sqrt(sum(t * t for t in n))
                if plain and ln > 0:
                    cen = [(a[j] + b[j] + c[j]) / 3 for j in range(3)]
                    # the eye's signed distance in front of the face (its outward normal is -n)
                    if sum((eye[j] - cen[j]) * -n[j] for j in range(3)) / ln < -EYE_MARGIN:
                        continue
                kept += idx[k:k + 3]
            if not kept:
                continue
            used = sorted(set(kept))
            new = {i: k for k, i in enumerate(used)}
            secs.append({"indices": [new[i] for i in kept],
                         "vertices": [{key: nums(val) for key, val in sec["vertices"][i].items()} for i in used]})
            mats.append(mat)
        if secs:
            o["procedural"], o["materialSets"] = secs, mats
            keep_objects.append(o)
    m["objects"] = keep_objects


def volume_extent(v):
    """A spawn volume's half-extents across and up the wall, in map units. A rolled volume turns its box too, so
    it spawns over its turned box (2026-09-25: a wide volume rolled 90 deg spawned targets outside the window)."""
    hy, hz = v["size_y"] * 100, v["size_z"] * 100
    c, s = abs(math.cos(math.radians(v.get("roll", 0.0)))), abs(math.sin(math.radians(v.get("roll", 0.0))))
    return c * hy + s * hz, s * hy + c * hz


def clip_box(volumes, radius, thickness=20.0):
    """Six invisible Clip slabs round the spawn volumes (plus a target's radius, in map units), so moving targets
    stay where they can spawn: on screen and on the wall plane. Clip blocks bots but not shots (2026-09-25: the
    Pasu Track copy and the race seeker). A spec sets "clip_box": true to get it."""
    x0, x1 = WALL_X - 16 - radius, WALL_X + 16 + radius      # the volumes are 32 deep round WALL_X
    ext = [(v, *volume_extent(v)) for v in volumes]
    y0 = min(v["y"] - hy for v, hy, hz in ext) - radius
    y1 = max(v["y"] + hy for v, hy, hz in ext) + radius
    z0 = min(v["z"] - hz for v, hy, hz in ext) - radius
    z1 = max(v["z"] + hz for v, hy, hz in ext) + radius
    t = thickness
    slabs = [(x0 - t, x0, y0 - t, y1 + t, z0 - t, z1 + t), (x1, x1 + t, y0 - t, y1 + t, z0 - t, z1 + t),
             (x0, x1, y0 - t, y0, z0 - t, z1 + t), (x0, x1, y1, y1 + t, z0 - t, z1 + t),
             (x0, x1, y0, y1, z0 - t, z0), (x0, x1, y0, y1, z1, z1 + t)]
    return [{"location": f"{a:.6f}, {c:.6f}, {e:.6f}", "mesh": "Cube", "name": "Clip",
             "rotation": "0.000000, 0.000000, 0.000000",
             "scale": f"{(b - a) / 100:.6f}, {(d - c) / 100:.6f}, {(f - e) / 100:.6f}", "type": "brush"}
            for a, b, c, d, e, f in slabs]


def parse(path):
    text = Path(path).read_text(encoding="utf-8", errors="strict")
    lines = text.splitlines()
    top, sections, map_data = [], [], None
    cur = None
    for i, line in enumerate(lines):
        m = HEADER.match(line.strip())
        if m and m.group(1) == "Map Data":
            map_data = "\n".join(lines[i + 1:])
            break
        if m:
            cur = {"type": m.group(1), "lines": []}
            sections.append(cur)
        elif cur is None:
            top.append(line)
        else:
            cur["lines"].append(line)
    for s in sections:
        s["name"] = next((l.split("=", 1)[1] for l in s["lines"] if l.startswith("Name=")), None)
    return {"top": top, "sections": sections, "map": map_data}


_cache = {}


def load(path):
    p = str(Path(path))
    if p not in _cache:
        _cache[p] = parse(p)
    return _cache[p]


def get_key(lines, key):
    for l in lines:
        if l.startswith(key + "="):
            return l.split("=", 1)[1]
    return None


def set_key(lines, key, value, warn, where):
    for i, l in enumerate(lines):
        if l.startswith(key + "="):
            lines[i] = f"{key}={value}"
            return
    warn.append(f"{where}: key '{key}' not present in copied section, appended")
    lines.append(f"{key}={value}")


def find_section(parsed, stype, name):
    for s in parsed["sections"]:
        if s["type"] == stype and s["name"] == name:
            return s
    return None


def build(spec, outdir):
    errors, warns = [], []
    base = load(BASE)
    top = list(base["top"])
    sections = [copy.deepcopy(s) for s in base["sections"]]

    for d in spec.get("drop_sections", []):
        stype, name = d.split("|", 1)
        before = len(sections)
        sections = [s for s in sections if not (s["type"] == stype and s["name"] == name)]
        if len(sections) == before:
            warns.append(f"drop_sections: {d} not found in base")

    for sec in spec["sections"]:
        src = load(sec["copy_from_file"]) if Path(sec["copy_from_file"]).exists() else None
        if src is None:
            errors.append(f"copy_from_file missing: {sec['copy_from_file']}")
            continue
        s = find_section(src, sec["section_type"], sec["copy_section_name"])
        if s is None:
            errors.append(f"no [{sec['section_type']}] Name={sec['copy_section_name']} in {sec['copy_from_file']}")
            continue
        s = copy.deepcopy(s)
        where = f"[{sec['section_type']}] {sec['new_name']}"
        set_key(s["lines"], "Name", sec["new_name"], warns, where)
        s["name"] = sec["new_name"]
        for kv in sec["overrides"]:
            set_key(s["lines"], kv["key"], kv["value"], warns, where)
        idx = next((i for i, t in enumerate(sections) if t["type"] == s["type"] and t["name"] == s["name"]), None)
        if idx is None:
            sections.append(s)
        else:
            sections[idx] = s

    # names
    by_type = {}
    for s in sections:
        by_type.setdefault(s["type"], []).append(s["name"])
        if by_type[s["type"]].count(s["name"]) > 1:
            errors.append(f"duplicate [{s['type']}] {s['name']}")

    # AddedBots entries: "name" or "name.bot" -> [Bot Profile], "name.rot" -> [Bot Rotation Profile]
    bots = [b if b.endswith((".bot", ".rot")) else b + ".bot" for b in spec["added_bots"]]
    distinct_files = list(dict.fromkeys(bots))
    distinct = []
    for b in distinct_files:
        name, ext = b[:-4], b[-4:]
        if ext == ".bot":
            if name not in by_type.get("Bot Profile", []):
                errors.append(f"added bot '{b}' has no [Bot Profile]")
            distinct.append(name)
        else:
            rot = find_section({"sections": sections}, "Bot Rotation Profile", name)
            if rot is None:
                errors.append(f"added rotation '{b}' has no [Bot Rotation Profile]")
                continue
            names = (get_key(rot["lines"], "ProfileNames") or "").split(";")
            weights = (get_key(rot["lines"], "ProfileWeights") or "").split(";")
            if len(names) != len(weights):
                errors.append(f"rotation '{name}': {len(names)} ProfileNames vs {len(weights)} ProfileWeights")
            for n in names:
                if n not in by_type.get("Bot Profile", []):
                    errors.append(f"rotation '{name}' entry '{n}' has no [Bot Profile]")
                elif n not in distinct:
                    distinct.append(n)
    used_chars = set()
    for s in sections:
        if s["type"] == "Bot Profile" and s["name"] in distinct:
            cp = get_key(s["lines"], "CharacterProfile")
            used_chars.add(cp)
            if cp not in by_type.get("Character Profile", []):
                errors.append(f"bot '{s['name']}' CharacterProfile '{cp}' missing")
            for w in (get_key(s["lines"], "WeaponsProfileNames") or "").split(";"):
                if w and w not in by_type.get("Weapon Profile", []):
                    errors.append(f"bot '{s['name']}' weapon '{w}' missing")
            for d in (get_key(s["lines"], "DodgeProfileNames") or "").split(";"):
                if d and d not in by_type.get("Dodge Profile", []):
                    errors.append(f"bot '{s['name']}' dodge '{d}' missing")
            if get_key(s["lines"], "UseWeapons") == "true" and not any((get_key(s["lines"], "WeaponsProfileNames") or "").split(";")):
                warns.append(f"bot '{s['name']}' UseWeapons=true but no weapon")
    player = find_section({"sections": sections}, "Character Profile", "Player")
    pw = (get_key(player["lines"], "WeaponProfileNames") or "").split(";")[0]
    if pw not in by_type.get("Weapon Profile", []):
        errors.append(f"player weapon '{pw}' missing")

    # top-level
    slug = re.sub(r"[^A-Za-z0-9]+", "_", spec["scenario_name"]).strip("_")
    fixed = {
        "Name": spec["scenario_name"],
        "Description": spec["description"],
        "AddedBots": ";".join(bots),
        # ClickTrack 3t pattern: every .bot used (directly or via a rotation), then the .rot files.
        "BotCharacters": ";".join([f"{n}.bot" for n in distinct] + [b for b in distinct_files if b.endswith(".rot")]),
        "BotMaxLives": ";".join("0" for _ in bots),
        "BotTeams": ";".join("0" for _ in bots),
        "MapName": spec.get("map_name") or f"{slug}.json",
    }
    for kv in spec["scenario_overrides"]:
        if kv["key"] in fixed:
            warns.append(f"scenario_overrides tried to set builder-owned key {kv['key']}, ignored")
            continue
        set_key(top, kv["key"], kv["value"], warns, "top-level")
    for k, v in fixed.items():
        set_key(top, k, v, warns, "top-level")

    # map
    m = json.loads(base["map"])
    tmpl = next(o for o in m["objects"] if o.get("name") == "SpawnVolume"
                and any(p["name"] == "TeamMask" and p["value"] == 2 for p in o["properties"]))
    kept = [o for o in m["objects"] if not (o.get("name") == "SpawnVolume"
            and any(p["name"] == "TeamMask" and p["value"] == 2 for p in o["properties"]))]
    vols = []
    for v in spec["spawn_volumes"]:
        if not (-2400 <= v["y"] <= 2400 and -1200 <= v["z"] <= 1200):
            errors.append(f"volume out of wall area: {v}")
        if v["permitted_profile"] and v["permitted_profile"] not in used_chars:
            errors.append(f"volume profile '{v['permitted_profile']}' not used by any added bot")
        o = copy.deepcopy(tmpl)
        o.pop("group", None)
        o["location"] = f"{WALL_X:.6f}, {v['y']:.6f}, {v['z']:.6f}"
        o["scale"] = f"0.160000, {v['size_y']:.6f}, {v['size_z']:.6f}"
        if "roll" in v:        # turn the volume, its box and the bots it spawns, as the player sees it
            r = o.get("rotation", "0, 0, 0").split(",")
            o["rotation"] = ", ".join([f"{v['roll']:.6f}"] + [t.strip() for t in r[1:]])
        for p in o["properties"]:
            if p["name"] == "PermittedCharacterProfiles":
                p["value"] = v["permitted_profile"]
        vols.append(o)
    for cp in used_chars:
        if not any(v["permitted_profile"] in (cp, "") for v in spec["spawn_volumes"]):
            errors.append(f"character '{cp}' has no spawn volume")
    # insert target volumes before the player spawn (last object)
    m["objects"] = kept[:-1] + vols + kept[-1:] if kept and kept[-1].get("name") == "SpawnVolume" else kept + vols
    # Arena disabled 2026-09-23: it crashed KovaaK's renderer on load (access violation after LoadMap).
    if spec.get("fixed_spawn", FIXED_SPAWN_DEFAULT):
        for o in m["objects"]:
            if o.get("name") == "SpawnVolume" and any(p["name"] == "TeamMask" and p["value"] == 1
                                                      for p in o["properties"]):
                o["name"] = "SpawnPoint"
                o["scale"] = "0.250000, 0.250000, 0.250000"
    look = spec.get("arena", ARENA_DEFAULT)   # False, True (grey arena), "egypt" (module settings) or "window"
    if look:
        radii = [float(get_key(s["lines"], "MainBBRadius")) for s in sections
                 if s["type"] == "Character Profile" and s["name"] in used_chars]
        if look == "window":
            egypt.add_window(m, spec["spawn_volumes"], max(radii))
        elif look == "egypt":
            egypt.add_egypt(m, spec["spawn_volumes"], max(radii))
        else:
            arena.add_arena(m, spec["spawn_volumes"], max(radii))
    if spec.get("clip_box"):
        map_scale = float(next(l.split("=", 1)[1] for l in top if l.startswith("MapScale=")))
        radius = max(float(get_key(s["lines"], "MainBBRadius")) for s in sections
                     if s["type"] == "Character Profile" and s["name"] in used_chars)
        m["objects"] += clip_box(spec["spawn_volumes"], radius / map_scale)
    if SLIM_MESHES:
        slim_meshes(m, float(next(l.split("=", 1)[1] for l in top if l.startswith("MapScale="))))
    map_text = dump_map(m)

    ordered = sorted(sections, key=lambda s: SECTION_ORDER.index(s["type"]) if s["type"] in SECTION_ORDER else 99)
    out = list(top)
    for s in ordered:
        out.append(f"[{s['type']}]")
        out.extend(s["lines"])
    out.append("[Map Data]")
    out.extend(map_text.splitlines())
    path = Path(outdir) / f"{spec['scenario_name']}.sce"
    path.write_bytes(("\r\n".join(out) + "\r\n").encode("ascii"))

    # round-trip check
    rt = parse(path)
    json.loads(rt["map"])
    return path, errors, warns


def main():
    specs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    bad = 0
    for spec in specs:
        path, errors, warns = build(spec, outdir)
        print(f"== {path.name}: {len(errors)} errors, {len(warns)} warnings")
        for e in errors:
            print("   ERROR", e)
        for w in warns:
            print("   warn ", w)
        bad += bool(errors)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
