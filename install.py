"""Install built Flow Fix files into KovaaK's, copying only what changed.

- out/*.sce            -> SaveGames/Scenarios/
- Flow Fix guide.md    -> SaveGames/Scenarios/
- out/Flow Fix.json    -> SaveGames/Playlists/
- Scenarios this script installed before (listed in installed.json) that are no longer built (renamed or
  removed) move to retired/. Nothing else is ever retired: the user's own saves (e.g. an editor copy such as
  "Flow Fix Mesh Test d.sce") and test scenarios installed by hand are never in the list. Nothing is deleted,
  and a file already in retired/ is never overwritten; the new one gets a " (2)", " (3)"... suffix.

Usage: python install.py [--dry-run]
Restart KovaaK's afterwards; it only reads scenarios at startup.
Set FLOWFIX_GAME to another SaveGames folder to try it without touching the game.
"""
import filecmp
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GAME = Path(os.environ.get("FLOWFIX_GAME",
                           "C:/Program Files (x86)/Steam/steamapps/common/FPSAimTrainer/FPSAimTrainer/Saved/SaveGames"))
MANIFEST = ROOT / "installed.json"     # names of the scenarios this script has installed
RETIRED = ROOT / "retired"
dry = "--dry-run" in sys.argv


def copy(src, dst):
    if dst.exists() and filecmp.cmp(src, dst, shallow=False):
        return False
    print(f"{'would copy' if dry else 'copy'}: {src.name} -> {dst}")
    if not dry:
        shutil.copy2(src, dst)
        assert filecmp.cmp(src, dst, shallow=False), f"copy mismatch: {dst}"
    return True


def free_name(folder, name):
    """name, or name with " (2)", " (3)"... before the extension if name is taken in folder."""
    p = folder / name
    k = 2
    while p.exists():
        p = folder / f"{Path(name).stem} ({k}){Path(name).suffix}"
        k += 1
    return p


built = sorted(p.name for p in (ROOT / "out").glob("*.sce"))
# First run with a manifest: only the scenarios built now count as installed by this script.
installed_before = set(json.loads(MANIFEST.read_text(encoding="utf-8"))) if MANIFEST.exists() else set(built)

changed = sum(copy(ROOT / "out" / n, GAME / "Scenarios" / n) for n in built)
changed += copy(ROOT / "Flow Fix guide.md", GAME / "Scenarios" / "Flow Fix guide.md")
if (ROOT / "out" / "Flow Fix.json").exists():
    changed += copy(ROOT / "out" / "Flow Fix.json", GAME / "Playlists" / "Flow Fix.json")

RETIRED.mkdir(exist_ok=True)
for name in sorted(installed_before - set(built)):
    src = GAME / "Scenarios" / name
    if not src.exists():
        continue
    dst = free_name(RETIRED, name)
    print(f"{'would retire' if dry else 'retire'}: {name} -> {dst}")
    if not dry:
        shutil.move(str(src), dst)

if not dry:
    MANIFEST.write_text(json.dumps(built, indent=1) + "\n", encoding="utf-8")
print(f"{changed} file(s) {'would change' if dry else 'changed'}. Restart KovaaK's to load them.")
