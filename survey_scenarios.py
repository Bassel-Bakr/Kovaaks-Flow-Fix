"""Read-only survey of the scenarios installed in KovaaK's (2026-09-25): every scenario's settings as data.

Parses each .sce into its top-level keys and its profile sections (bots, dodge, weapons, characters, rotations,
abilities), without the map, plus a few facts from the map (spawn objects, paths, brush count). Writes
test_out/survey.json for the study of every scenario type (see
.agents/skills/kovaaks-scenario-design/references/scenario-types.md). Installs and changes nothing.

Usage: python survey_scenarios.py
"""
import glob
import json
import os
import re
from pathlib import Path

SCEN = r"C:\Program Files (x86)\Steam\steamapps\common\FPSAimTrainer\FPSAimTrainer\Saved\SaveGames\Scenarios"
HEADER = re.compile(r"^\[(.+)\]$")


def parse(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    top, sections, cur, map_text = {}, [], None, None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = HEADER.match(line.strip())
        if m and m.group(1) == "Map Data":
            map_text = "\n".join(lines[i + 1:])
            break
        if m:
            cur = {"type": m.group(1), "keys": {}}
            sections.append(cur)
        elif "=" in line:
            k, v = line.split("=", 1)
            (cur["keys"] if cur else top)[k.strip()] = v.strip()
    facts = {}
    if map_text:
        try:
            m = json.loads(map_text)
            objs = m.get("objects", [])
            facts = {
                "brushes": sum(1 for o in objs if o.get("type") == "brush"),
                "meshes": sum(1 for o in objs if o.get("procedural")),
                "spawn_points": sum(1 for o in objs if o.get("name") == "SpawnPoint"),
                "spawn_volumes": sum(1 for o in objs if o.get("name") == "SpawnVolume"),
                "paths": sorted({p["value"] for o in objs for p in o.get("properties", [])
                                 if p.get("name") == "Path" and p.get("value")}),
                "object_names": sorted({o.get("name", "") for o in objs}),
            }
        except (ValueError, TypeError):
            if map_text.lstrip().startswith("reflex map version"):
                # the older map format, taken from the game Reflex Arena: brushes as vertex lists, entities by type
                ents = re.findall(r"^\t+type (\w+)", map_text, re.M)
                facts = {"format": map_text.lstrip().split("\n", 1)[0],
                         "brushes": len(re.findall(r"^\tbrush\b", map_text, re.M)),
                         "entities": {e: ents.count(e) for e in sorted(set(ents))}}
            else:
                facts = {"map_error": True}
    return {"file": os.path.basename(path)[:-4], "top": top, "sections": sections, "map": facts}


if __name__ == "__main__":
    out = [parse(f) for f in sorted(glob.glob(os.path.join(SCEN, "*.sce")))]
    Path("test_out").mkdir(exist_ok=True)
    Path("test_out/survey.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(out)} scenarios -> test_out/survey.json")
