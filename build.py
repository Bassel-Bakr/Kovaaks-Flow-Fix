"""Build KovaaK's .sce files from workflow specs.

Usage: python build.py specs.json outdir
"""
import copy
import json
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
    map_text = json.dumps(m, indent=4)

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
