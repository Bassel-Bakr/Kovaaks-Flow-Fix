# The Flow Fix look: the Egyptian window and the palace courtyard

Every Flow Fix scenario since 2026-09-24 shares one look. This page is the short overview. The full record for the
wiki (materials, themes, props, custom meshes, the art pipeline, the research and its sources, and the history of
every change) is in `.agents/skills/kovaaks-scenario-design/references/decoration.md`, and the confirmed map
mechanics are in `references/mechanics.md` next to it.

## What the player sees

- **The window.** The targets appear on a plain light grey wall inside a stone window: a jamb lining, a limestone
  frame with a red-ochre bead and a sill, two limestone pilasters and a stepped cornice. A navy band rings the opening
  and a navy line runs round the frame, so the window reads under themes that paint everything alike. The targets
  keep 60 units of clear space inside the frame.
- **The text.** The user's own hieroglyphs: the welcome line ("Welcome to my humble home") carved twice across the
  lintel from the centre outward, every sign facing the middle; the maker line ("This place was made by") down the
  left pilaster; the name "Bassel Bakr" in a cartouche on the right pilaster. Signs are navy with a dark outline.
- **The art.** A pharaoh's head (golden face, lapis nemes, no cobra) standing on the cornice, and a recumbent lion on
  a plinth beside each pilaster, facing the window. Both are stencils: thin plates whose gaps show the sky, so their
  features stay visible when a theme paints every surface one colour.
- **The courtyard.** A paved court with a navy pool, a dark grey palace wall with rounded battlements, a red
  palm-column portico with gold capitals on each side, two battered corner towers cut off by the screen edges (the
  nod to thundah's castle), grey palm silhouettes, and the Giza and Dahshur pyramids on the horizon.
- **Rules the user set.** No religious or cult symbols (no winged sun, uraeus, gods, ankh, djed, was, Eye of Horus,
  scarab or sphinx). Reproduce the user's hieroglyph text faithfully, never with filler signs. Nothing may cover a
  target.

## The palette (8 material slots)

| Slot | Surface type | Colour (default look) | Used by |
| --- | --- | --- | --- |
| group 0 `wall` | wall | palace grey 5d6066 | palace walls, roofs, towers, palms, sign outlines |
| group 0 `ground` | floor | lapis 1e4c9a | the pharaoh's headdress |
| group 0 `ceiling` | ceiling | limestone (ConcretePoured eadbb6) | window stone, kerbs, merlons, pyramids |
| group 0 `ramp` | ramp | red ochre 9a3f22 | bead, bands, lion manes, column shafts |
| group 1 `wall` | wall | light grey c8c8c8 | the wall behind the targets |
| group 1 `ground` | floor | navy 0f2a4d | signs, lion bodies, outline band, pool water |
| group 1 `ceiling` | ceiling | paving grey 77736b | the court floor |
| group 1 `ramp` | ramp | gold d4a02a | the pharaoh's face, capitals, bands, sill strip |

Maps allow only these two groups (plus "None"); more crashed the game. Themes repaint by surface type, which is why
the stone is on `ceiling`, the backdrop on `wall` and the carvings on `floor`: across the user's 149 themes that gives
the most contrast (the text reads in 117).

## Frame rate

The window with its art is about 84 objects; the courtyard adds 18 (10 blocks, 8 custom meshes, about 2,400
triangles). The Courtyard Test read 875 FPS without a theme override and 880 with one. The user's stats show a limit
of 1000 FPS and about 820 in play with the window look. Lessons: rotated blocks cost (the signs are merged into meshes);
plain blocks barely do; a theme can multiply the cost of our geometry.

## How it is built

- `build.py` uses the look for every scenario (`ARENA_DEFAULT = "window"`), through `egypt.add_window`, which applies
  `egypt.WINDOW_LOOK`: `MESH_SIGNS`, `DARK_TEXT`, `WINDOW_ONLY`, `WINDOW_HEAD = "top"`, `WINDOW_LIONS`,
  `LINTEL_MIRROR`, `STENCIL_ART` and `COURTYARD`.
- `egypt.py` builds the window, the text (`inscriptions.json`, from `make_inscriptions.py` and `strokes.py`) and the
  art (`egypt_glyphs.json`). The courtyard comes from `courtyard/final_geo.py` via `courtyard/court_export.py`.
- `check_scene.py out` must pass (nothing in front of a target), and `check_view.py` must show 0% off screen.
- Try any change to map structure as a single test scenario first (`egypt_test.py`, `courtyard_test.py`): a scenario
  that crashes the game makes it crash on every launch until the file is replaced.
