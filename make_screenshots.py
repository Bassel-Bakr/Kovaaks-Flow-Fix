"""Render a scenario screenshot for each Flow Fix scenario (2026-09-24).

KovaaK's shows a scenario's picture from SaveGames/Scenarios/Screenshots/<scenario name>.jpg (854 x 480); the game
also writes "<name>.auto.jpg" by itself. This script draws the player's view of each scenario's window and courtyard
with the courtyard workflow's renderer (courtyard/final_render.py: flat-shaded polygons, an assumed sun, no targets,
default colours, no theme) into test_out/screenshots/. It builds window-only copies of the 13 scenarios first,
because the renderer reads the window from a build and adds the court itself.

Usage: python make_screenshots.py   (installs nothing; install.py does not copy these either)
"""
import copy
import json
import sys
from pathlib import Path

import build
import egypt

sys.path.insert(0, str(Path(__file__).with_name("courtyard")))
import final_geo as G  # noqa: E402
import final_render as R  # noqa: E402

SRC = Path("test_out/shots_src")
OUT = Path("test_out/screenshots")
ZOOM = 1.36
# The game's own screenshot of Check (2026-09-24) showed the window about 1.5 degrees below the centre, as it
# was then; 15 pixels matched it. Since 2026-09-25 the window is centred on the crosshair, so no shift.
Y_SHIFT = 0
SRC.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

specs = json.loads(Path("specs.json").read_text(encoding="utf-8"))
look = egypt.WINDOW_LOOK
egypt.WINDOW_LOOK = dict(look, COURTYARD=False)   # the renderer adds the court to the window build itself
try:
    for s in specs:
        _, errors, _ = build.build(copy.deepcopy(s), SRC)
        assert not errors, (s["scenario_name"], errors)
finally:
    egypt.WINDOW_LOOK = look

G.WINDOWS = str(SRC.resolve())
for s in specs:
    name = s["scenario_name"][len("Flow Fix "):]
    L = G.load(name)
    # Zoomed like the game's own screenshot of Check (the window fills about 55% of the width): render the full
    # 103-degree view larger and keep its centre.
    big = R.render(L, G.court(L), W=round(854 * ZOOM), H=round(480 * ZOOM), SS=2, envelope=False)
    x0, y0 = (big.width - 854) // 2, (big.height - 480) // 2 - Y_SHIFT
    big.crop((x0, y0, x0 + 854, y0 + 480)).save(OUT / f"{s['scenario_name']}.jpg", quality=92)
    print(OUT / f"{s['scenario_name']}.jpg")
