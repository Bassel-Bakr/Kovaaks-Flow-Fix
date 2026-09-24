# The Flow Fix look: the Egyptian window and the palace courtyard

Every Flow Fix scenario since 2026-09-24 shares one look. The current version dates from 2026-09-25. This page is the
short overview. The full record for the wiki is in `.agents/skills/kovaaks-scenario-design/references/decoration.md`:
materials, themes, props, custom meshes, the art pipeline, the sculpts, the research and its sources, and the
history of every change. The confirmed map mechanics are in `references/mechanics.md` next to it.

## What the player sees

- **The window.** The targets appear on a plain light grey wall inside a stone window: a jamb lining, a limestone
  frame with a red-ochre bead and a sill, two limestone pilasters and a stepped cornice. A navy band rings the opening
  and a navy line runs round the frame, so the window reads under themes that paint everything alike. The targets
  keep 60 units of clear space inside the frame. The window is centred on the crosshair (2026-09-25).
- **The text.** The user's own hieroglyphs: the welcome line ("Welcome to my humble home") is carved twice across the
  lintel, from the centre outward, with every sign facing the middle. The maker line ("This place was made by") runs
  down the left pilaster, and the name "Bassel Bakr" is in a cartouche on the right pilaster. Signs are navy with a
  dark outline, drawn as smooth pen strokes with round ends (2026-09-25).
- **The pharaoh.** A sculpted bust, after Tutankhamun's mask, stands on the lintel in front of the cornice, between
  the two welcome lines. It has a golden face with painted lapis eyes, brows and mouth, a straight royal beard, a
  nemes in lapis and gold stripes, and a broad collar in lapis and gold rings. There is no cobra.
- **The lions.** Two sculpted recumbent lions lie on long plinths beside the pilasters, heads toward the player, like
  guardian lions flanking an approach. Each has a navy body, an ochre mane round the face, and a tail curled over the
  rump; the tails lean outward.
- **The courtyard.** A grey paved court with a navy pool, a sandstone palace wall with rounded battlements, a red
  palm-column portico with gold capitals on each side, two battered sandstone corner towers cut off by the screen
  edges (the nod to thundah's castle), grey palm silhouettes, and the Giza and Dahshur pyramids on the horizon.
- **Rules the user set.** No religious or cult symbols (no winged sun, uraeus, gods, ankh, djed, was, Eye of Horus,
  scarab or sphinx). Reproduce the user's hieroglyph text faithfully, never with filler signs. Nothing may cover a
  target. Every asset file carries the user's credits.

## The palette (8 material slots)

| Slot | Surface type | Colour (default look) | Used by |
| --- | --- | --- | --- |
| group 0 `wall` | wall | paving grey 77736b | the court floor, the palms, the sign outlines |
| group 0 `ground` | floor | lapis 1e4c9a | the bust's lapis: stripes, collar rings, beard, eyes |
| group 0 `ceiling` | ceiling | limestone (ConcretePoured eadbb6) | window stone, plinths, kerbs, merlons, pyramids |
| group 0 `ramp` | ramp | red ochre 9a3f22 | bead, bands, lion manes, column shafts |
| group 1 `wall` | wall | light grey c8c8c8 | the wall behind the targets |
| group 1 `ground` | floor | navy 0f2a4d | signs, lion bodies, outline band, pool water |
| group 1 `ceiling` | ceiling | sandstone c9a877 | palace walls, portico roofs, towers |
| group 1 `ramp` | ramp | gold d4a02a | the bust's gold: face, stripes, collar rings; capitals, bands, sill strip |

Maps allow only these two groups (plus "None"); more crashed the game. Themes repaint by surface type, which is why
the stone is on `ceiling`, the backdrop on `wall` and the carvings on `floor`: across the user's 149 themes that gives
the most contrast (the text reads in 117). Under a theme, the sandstone walls take the ceiling paint, like the window
stone, and the court floor takes the wall paint.

## Frame rate and file size

Each scenario is 104 map objects (2 from the base map), 51 of them custom meshes, about 30,500 mesh triangles, and
a file of about 5 MB. The user read 850 FPS with the sculpted lions and 910 FPS on low settings with the whole look
(2026-09-25).

Mesh data used to dominate the file. The game writes it one number per line, so the window look's files were 12 MB,
and the first build with the sculpts was 39 MB. The user saw a hitch on every restart. Three fixes are now in
`build.py` and `egypt.py`:
- **Compact mesh data:** one vertex per line.
- **Hidden faces left out.** The player never moves, so faces that point away from the eye are dropped.
- **Shared vertices** in the text strokes.

Lessons:
- Rotated blocks cost frame time; plain blocks barely do.
- Mesh triangles are cheap for the frame rate but not for the file.
- A theme can multiply the cost of our geometry.

## How it is built

- `build.py` uses the look for every scenario (`ARENA_DEFAULT = "window"`), through `egypt.add_window`. That applies
  `egypt.WINDOW_LOOK`:
  - `MESH_SIGNS`, `DARK_TEXT`, `WINDOW_ONLY`, `WINDOW_LIONS`, `LINTEL_MIRROR`, `STENCIL_ART`;
  - `WINDOW_HEAD = "front_lintel"`, `HEAD_SCULPT`, `LION_TURNED`, `ROUND_STROKES` and `COURTYARD`.

  `build.py` then writes the map with `COMPACT_MESHES` and `SLIM_MESHES`.
- `egypt.py` builds the window and the text (`inscriptions.json`, from `make_inscriptions.py` and `strokes.py`). It
  places the sculpts: `pharaoh_statue.json` from `make_pharaoh.py`, and `lion_statue.json` from `make_lion.py`. Both
  scripts use `sculpt.py`. The pixel art in `egypt_glyphs.json` is the fallback. The courtyard comes from
  `courtyard/final_geo.py` via `courtyard/court_export.py`.
- `check_scene.py out` must pass (nothing in front of a target), and `check_view.py` must show 0% off screen.
- `make_screenshots.py` renders each scenario's picture for the scenario list.
- Try any change to map structure as a single test scenario first (`egypt_test.py`, `courtyard_test.py`): a scenario
  that crashes the game makes it crash on every launch until the file is replaced.
