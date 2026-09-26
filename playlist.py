"""Write a KovaaK's playlist (UTF-16 LE JSON with BOM, same shape as the installed ones).

Usage: python playlist.py specs.json out.json "Playlist name" unix_time
"""
import json
import sys
from pathlib import Path

specs = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
name, updated = sys.argv[3], int(sys.argv[4])
# Individual drills 01-11 first; the all-in-one is id 12 so it sorts last.
# One playlist per series (2026-09-26): "Flow Fix" and "Flow Fix 2" (the spec's "series", "Flow Fix" by default).
names = [s["scenario_name"] for s in sorted(specs, key=lambda s: s["id"]) if s.get("series", "Flow Fix") == name]
playlist = {
    "playlistName": name,
    "playlistId": 0,
    "authorSteamId": "",
    "authorName": "",
    "scenarioList": [{"scenario_name": n, "play_Count": 1} for n in names],
    "description": "Static clicking drills built from the weakness targeted static flowchart. "
                   "Each scenario targets one flowchart issue; Flow Fix Check, the all-in-one, comes last.",
    "hasOfflineScenarios": True,
    "hasEdited": True,
    "shareCode": "",
    "version": 1,
    "updated": updated,
    "isPrivate": True,
}
text = json.dumps(playlist, indent="\t", ensure_ascii=False).replace("\n", "\r\n")
Path(sys.argv[2]).write_bytes(b"\xff\xfe" + text.encode("utf-16-le"))
print(f"{len(names)} scenarios -> {sys.argv[2]}")
