"""Copy an installed scenario under a new name with some settings changed (2026-09-25).

For fixing other authors' scenarios without touching them: the original stays as it is, and the copy gets its own
name (so its own score history) and a note in its description. Writes test_out/<new name>.sce; copy it into the
Scenarios folder by hand, and never over an existing file.

Usage:
  python patch_scenario.py "<installed name>" "<new name>" "<note>" "<section>|<profile name>|<key>=<value>" ...
  <section> is a section type such as "Dodge Profile", or "top" for the scenario's own settings (then leave the
  profile name empty: "top||Timelimit=60.0"). The key must already exist; the script refuses to add keys.
  "map|add|<object JSON>" appends an object to the map, for example an invisible Clip brush.
  "map|where:<property>=<value>|<object key>=<value>" changes one map object, found by a property, for example
  "map|where:PermittedCharacterProfiles=Seeker|location=0.000000, 0.000000, 0.000000".
"""
import json
import sys
from pathlib import Path

SCEN = Path("C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/Saved/SaveGames/Scenarios")


def patch(src_name, new_name, note, overrides):
    raw = (SCEN / f"{src_name}.sce").read_bytes()
    nl = "\r\n" if b"\r\n" in raw else "\n"
    lines = raw.decode("utf-8").split(nl)
    # the section each line belongs to: ("top", "") before the first header, then (type, Name=) per section
    where, cur, names = [], ("top", ""), {}
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = (s[1:-1], None)
            names[i] = cur
        where.append(cur)
    # a section's name is its first Name= line
    sec_name, key = {}, None
    for i, line in enumerate(lines):
        if i in names:
            key = i
        elif key is not None and key not in sec_name and line.startswith("Name="):
            sec_name[key] = line.split("=", 1)[1]
    label, key = [], None
    for i in range(len(lines)):
        if i in names:
            key = i
        label.append(("top", "") if key is None else (names[key][0], sec_name.get(key, "")))
    done, added, moved = set(), [], []
    for o in overrides:
        sec, prof, kv = o.split("|", 2)
        if sec == "map" and prof == "add":
            added.append(json.loads(kv))
            continue
        if sec == "map" and prof.startswith("where:"):    # "map|where:<property>=<value>|<object key>=<value>"
            moved.append((prof[len("where:"):].split("=", 1), kv.split("=", 1)))
            continue
        k, v = kv.split("=", 1)
        hits = [i for i, line in enumerate(lines) if label[i] == (sec, prof) and line.startswith(k + "=")]
        if len(hits) != 1:
            sys.exit(f"{o}: {len(hits)} matching lines; nothing written")
        lines[hits[0]] = f"{k}={v}"
        done.add(o)
    top = [i for i in range(len(lines)) if label[i] == ("top", "")]
    for i in top:
        if lines[i].startswith("Name="):
            lines[i] = f"Name={new_name}"
        elif lines[i].startswith("Description="):
            lines[i] = lines[i] + "[nl][nl]" + note
    if added or moved:                     # re-written the way the game writes maps: 4-space indents
        start = next(i for i, line in enumerate(lines) if line.strip() == "[Map Data]") + 1
        m = json.loads("\n".join(lines[start:]))
        for (prop, val), (key, new) in moved:
            hits = [o for o in m["objects"]
                    if any(p.get("name") == prop and str(p.get("value")) == val for p in o.get("properties", []))]
            if len(hits) != 1:
                sys.exit(f"map where {prop}={val}: {len(hits)} matching objects; nothing written")
            hits[0][key] = new
        m["objects"] += added
        lines = lines[:start] + json.dumps(m, indent=4).split("\n")
    out = Path("test_out") / f"{new_name}.sce"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(nl.join(lines).encode("utf-8"))
    return out


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    print(patch(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]))
