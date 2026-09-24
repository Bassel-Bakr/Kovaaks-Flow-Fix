"""Build the window-look mockups the user asked to compare side by side (2026-09-24) and render them as one image.

Variants (see WINDOW_HEAD in egypt.py): the pharaoh's head on a raised lintel with the welcome line split beside it,
standing on the cornice, or alone on the lintel with the text on the pilasters; each with a lion beside each
pilaster. Art comes from the design drafts in test_out/art/ until the final designs are stored in egypt_glyphs.json.
Nothing is installed.

Usage: python window_mockups.py [pharaoh.txt lion.txt]   (writes test_out/mockups/*.sce and "window mockups.png")
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build
import egypt


def bitmap(path):
    return [r.rstrip("\n") for r in open(path, encoding="utf-8") if r.strip()]


head_file = sys.argv[1] if len(sys.argv) > 2 else "test_out/art/pA_v3_full.txt"
lion_file = sys.argv[2] if len(sys.argv) > 2 else "test_out/art/lionA_v9.txt"
egypt.EXTRA_ART = {"pharaoh": bitmap(head_file), "lion": bitmap(lion_file)}

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
spec = next(s for s in specs if s["scenario_name"] == "Flow Fix Overflick")
out = Path("test_out/mockups")
out.mkdir(parents=True, exist_ok=True)
variants = [("lintel_split", "A: head on the lintel, text beside it"),
            ("top", "B: head standing on the cornice"),
            ("lintel_alone", "C: head alone, text on the pilasters")]
egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY, egypt.WINDOW_LIONS = True, True, True, True
images = []
try:
    for key, label in variants:
        egypt.WINDOW_HEAD = key
        s = copy.deepcopy(spec)
        s["arena"] = "egypt"
        s["scenario_name"] = f"Flow Fix Mockup {key}"
        path, errors, _ = build.build(s, out)
        assert not errors, errors
        png = out / f"{key}.png"
        subprocess.run([sys.executable, "preview_front.py", str(path), str(png), "0.3",
                        "-2250", "2250", "-1150", "1500"], check=True, capture_output=True)
        m = json.loads(build.parse(path)["map"])
        n = sum(1 for o in m["objects"] if o.get("type") == "brush") - 2
        images.append((f"{label}  ({n} objects)", Image.open(png).convert("RGB")))
finally:
    egypt.MESH_SIGNS, egypt.DARK_TEXT, egypt.WINDOW_ONLY, egypt.WINDOW_LIONS = False, False, False, False
    egypt.WINDOW_HEAD, egypt.EXTRA_ART = None, {}
W = sum(im.width for _, im in images) + 20 * (len(images) + 1)
H = max(im.height for _, im in images) + 50
sheet = Image.new("RGB", (W, H), (30, 30, 30))
d = ImageDraw.Draw(sheet)
x = 20
for label, im in images:
    sheet.paste(im, (x, 40))
    d.text((x, 15), label, fill=(240, 240, 240))
    x += im.width + 20
sheet.save("test_out/window mockups.png")
print("test_out/window mockups.png", sheet.size)
