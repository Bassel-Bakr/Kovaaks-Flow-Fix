# Flow Fix: agent guide

KovaaK's (FPSAimTrainer) static clicking scenarios, one per problem in the weakness targeted static
flowchart (`D:\Projects\aim\docs\articles\weakness-targeted-static-flowchart.md`), plus an all-in-one
check. Every scenario is generated from `cA sixshot dense` (same room, FOV 103, BB Gun) by scripts in
this folder.

## Files

| File | Role |
| --- | --- |
| `gen_specs.py` | The design of every scenario. Edit this, never the installed `.sce` files. Writes `specs.json`. |
| `build.py` | Builds `out/*.sce` from `specs.json`: copies sections from installed scenarios, applies overrides, rebuilds the map, and checks every reference. |
| `arena.py` | Retired grey room (`"arena": True`). Every scenario now uses the Egyptian window look (`ARENA_DEFAULT = "window"` in `build.py`, `egypt.add_window`). |
| `playlist.py` | Writes the `Flow Fix` playlist (UTF-16 LE JSON with BOM). |
| `install.py` | Copies changed files into KovaaK's. Retires to `retired/` only scenarios it installed itself (`installed.json`) that are no longer built, never overwriting a retired copy. Supports `--dry-run`; `FLOWFIX_GAME` points it at a test folder. |
| `check_view.py` | Fails a layout that can put a target off screen (103 FOV, 16:9). |
| `check_frame.py` | Fails an arena whose frame can overlap a target on screen. |
| `egypt.py` | Ancient Egyptian window room built from carved Cube brushes and custom meshes (the user's requested look). Used when a spec has `"arena": "egypt"`. `WINDOW_ONLY` builds the window look. The pixel art for the pharaoh's head and the lions comes from `egypt_glyphs.json`. That file also holds older art: 16 hand-drawn signs, the winged sun and a frieze tile. |
| `strokes.py` | Turns font signs into straight strokes: renders the line art, thins it (Zhang-Suen), traces it, smooths the trace (`SMOOTH`) and simplifies it (RDP, `EPS` 3). With `MESH_SIGNS` on, the strokes of each sign merge into one custom mesh, and with `ROUND_STROKES` each stroke has round ends. The water sign is drawn as an explicit zigzag. |
| `sculpt.py` | Tools for the smooth statues: distance-field parts (ellipsoids, tapered capsules, rounded boxes), smooth union, surface nets with smooth normals, colour boundaries cut exactly into the mesh, and `write()` for the JSON. |
| `make_lion.py`, `make_pharaoh.py` | Sculpt the guardian lion (`lion_statue.json`) and the pharaoh's bust (`pharaoh_statue.json`). Rerun one after changing its parts; the build only reads the JSON. |
| `credits.py` | The credits (the user, Bassel Bakr) that head every asset JSON: `lion_statue.json`, `pharaoh_statue.json`, `inscriptions.json`, `egypt_glyphs.json`. |
| `rotation_test.py` | The calibration scenario that established how brush rotation works (retired; results are in mechanics.md). |
| `make_inscriptions.py` | Renders the user's hieroglyph text into `inscriptions.json`. `egypt.py` reads only its `"strokes"` and `"text"` keys. Every stroke sign comes from the Segoe UI Historic font. Only the water sign is drawn by hand, as a zigzag. The pixel keys (`"signs"`, `"cartouche"`, `"lines"`) still mix in hand-drawn signs from `egypt_glyphs.json`: ankh, djed, was sceptre, vulture, owl, reed, water, mouth and bread. These were made for the old pixel build, and the room does not use them. Needs PIL and the font; the build itself doesn't. |
| `preview_front.py` | Renders a flat front view of a built map to PNG, for checking a layout without the game. |
| `courtyard/` | The palace courtyard from the design workflow: `final_geo.py` (the chosen design, `court()`), `authentic_geo.py` (helpers and the authentic concept), `court_export.py` (pieces to brushes and meshes), `final_check.py` and `layouts.json` (the workflow's checks, kept for reference). |
| `courtyard_test.py` | `python courtyard_test.py authentic` builds the authentic concept as `Flow Fix Courtyard Authentic` for comparison. The chosen court is part of the window look now. |
| `fps_probe.py` | Builds `Flow Fix FPS Probe`: Overflick plus one small block. It tested whether the room's cost per frame is fixed, paid as soon as anything stands on the wall. It is not: the cost is spread across the pieces. Retired. |
| `check_scene.py` | Fails any map where a brush or prop in front of the targets overlaps the projected target envelope. It works for any decoration; run it on every look. |
| `egypt_test.py` | Builds four look tests into `test_out/`. `Flow Fix Egypt Test` is the full room. `Mesh Test` makes each sign one custom mesh. `Window Test` is the 2026-09-24 look: the window with the stencil head and lions, the mirrored welcome line and the courtyard. `Egypt Test FLAT` uses flat colours, for an FPS comparison. It also builds all 13 layouts in each look into `test_out/egypt_all`, `egypt_mesh_all` and `egypt_window_all`, so `check_scene.py` can check them. |
| `window_mockups.py` | Builds the head placement options and renders them side by side into `test_out/window mockups.png`. Installs nothing. |
| `backing_sampler.py`, `backing_test.py` | Backing experiments (retired): a numbered row of candidate props, and one prop (Sandstorm by default) behind the head and lions, as an always-dark backing that themes cannot repaint. The user stopped at the stencil without a backing, and the sculpts replaced the stencils on 2026-09-25. |
| `.agents/skills/` | The agent-neutral skills, indexed in `.agents/skills/README.md` (`SKILL.md` plus references). |
| `make_screenshots.py` | Renders each scenario's picture for KovaaK's scenario list into `test_out/screenshots/` (854 x 480 JPG, the player's view of the window and courtyard, no targets). Copy them to `SaveGames/Scenarios/Screenshots/<scenario name>.jpg`. Move a screenshot the user took in game to `retired/` rather than overwrite it; on 2026-09-25 the user asked for all 13 to be rendered, and their Check screenshot of the old look went to `retired/screenshots (installed until 2026-09-25)/`. |
| `.gitignore` | Keeps generated files (`out/`, `specs.json`, `test_out/`), local state (`installed.json`) and the `retired/` archive out of git. |
| `docs/` | Human-facing docs: `scenarios.md` (every scenario's design, evidence and verdict), `look.md` (the shared look), `future.md` (suggestions), `README.md` (index and the loop). Keep them current with every change. |
| `prop_test.py`, `prop_sampler.py`, `frame_test.py` | Retired prop tests for a frame that themes cannot repaint. Prop Test checks whether themes repaint props. Prop Sampler shows every candidate prop so the user can pick the opaque ones. Frame Test builds the arena frame from Container props. |
| `survey_scenarios.py` | Read-only survey of every scenario installed in KovaaK's into `test_out/survey.json`: top-level keys, profile sections and map facts (both map formats). The basis of `references/scenario-types.md`. |
| `stats_basic.py`, `stats_varying_sizes.py`, `stats_all_in_one.py`, `stats_recovery.py`, `stats_slow_start.py` | Read-only analysis of the user's runs. |
| `Flow Fix guide.md` | Player-facing guide, installed next to the scenarios. Keep it in sync with every change. |
| `retired/`, `test_out/` | `retired/` holds old installed files, and `retired/tests/` holds superseded test scenarios. `test_out/` holds the current test builds and the folders with all 13 scenarios in each look (`egypt_all`, `egypt_mesh_all`, `egypt_window_all`). |

## Commands

```bash
python gen_specs.py && python build.py specs.json out
python playlist.py specs.json "out/Flow Fix.json" "Flow Fix" "$(date +%s)"
python check_view.py && python check_frame.py
python install.py
```

KovaaK's paths:
- Scenarios: `C:\Program Files (x86)\Steam\steamapps\common\FPSAimTrainer\FPSAimTrainer\Saved\SaveGames\Scenarios`
- Stats: `...\FPSAimTrainer\stats`, more than 70k CSVs. Use a Python glob; `ls -la` there is very slow.
- Logs and crash reports: `C:\Users\basse\AppData\Local\FPSAimTrainer\Saved\Logs` and `\Crashes`

## Docs

`docs/scenarios.md` holds each scenario's design and calibration verdict, `docs/look.md` the look, `docs/future.md`
ideas that are not approved yet, and `docs/courtyard/` the courtyard design record. Update them in the same change as `gen_specs.py` or `egypt.py`.

## Skills (`.agents/skills/`)

The skills follow the open Agent Skills format and live in `.agents/skills/<name>/SKILL.md` (with references).
GitHub Copilot and other agents that support the format discover them there; any other agent should read
`.agents/skills/README.md` and the matching `SKILL.md` before that kind of task.

- **kovaaks-scenario-design:** designing or changing a drill. Confirmed mechanics are in
  `references/mechanics.md`; decoration (materials, themes, props, meshes, rotations, the Egypt look, art
  research) in `references/decoration.md`; every scenario type (how installed scenarios build static and dynamic
  clicking, tracking and switching, typical numbers, what the stats record) in `references/scenario-types.md`. The user wants all of it kept for a wiki: record
  every finding there.
- **flowfix-change:** the edit, build, check, install and document loop, plus the arena test path.
- **kovaaks-run-analysis:** "played X, check the stats". Judges the scenario from the user's runs.

## Working with this user

- **Commits.** Use Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, with an optional scope such
  as `docs(skills):`). Commit only when the user asks, on a branch rather than `main`.

- **Ask before changing.** Say what you will change and wait for a yes. Answer questions and audits
  directly.
- **Test the scenario, not the player.** When the user says "played X, check the stats", report what the data
  says about the scenario: does it force its demand, does the score pay for the right thing, is there
  luck or a shortcut. No coaching unless asked.
- **Baseline.** Compare against `cA sixshot`, never `cA sixshot dense`.
- **Naming.** `Flow Fix [problem]`, with no numbers and no initials. Tags: Flow Fix, flowfix, Static, Clicking,
  Bassel, Bakr, Egypt. Descriptions open with "Chinese weakness-targeted static flowchart: [problem]", then what it
  trains, how it works and how it scores. The playlist order comes from the
  `id` in `gen_specs.py`, and Check is always last.
- **Test scenarios.** Keep only one installed at a time. With several, the user opened the wrong one;
  superseded tests go to `retired/tests/`.
- **Credits in assets.** Every asset JSON the project makes (`lion_statue.json`, `pharaoh_statue.json`,
  `inscriptions.json`, `egypt_glyphs.json`) starts with a `"credits"` entry naming the user, Bassel Bakr. The
  entry comes from `credits.py`; a new asset file gets it too (user, 2026-09-25).
- **Inscriptions.** The user reads and writes hieroglyphs and supplied the room's text. Reproduce it
  faithfully and never fill space with meaningless signs. Keep at least 3 pixels between outlined signs,
  or their outlines fuse.
- **Frame rate: rotated blocks cost, plain blocks barely do.** Merging the signs' 458 stroke blocks into 21
  meshes cut the map from 587 objects to 150. That saved about 0.21 ms per frame (Egypt Test 580 FPS, Mesh
  Test 660). Merging 122 axis-aligned decoration blocks into meshes saved nothing measurable, and big
  surfaces cost the same as mesh or block (Mesh Test B, 2026-09-24). So signs are meshes (`MESH_SIGNS`) and decoration stays blocks, which stay
  editable. Since 2026-09-25 each scenario is 104 map objects (2 from the base map), 51 of them custom meshes:
  the signs, the sculpted bust, the two sculpted lions and the court's meshes. That is about 30,500 mesh
  triangles and about 5 MB. Mesh triangles are cheap for the frame rate but not for the file: the game writes
  mesh data one number per line, and a 39 MB build gave the user a hitch on every restart. So `build.py` writes
  meshes compactly and leaves out faces the fixed eye can never see (`COMPACT_MESHES`, `SLIM_MESHES`).
  Compare frame time (1000/FPS) against Overflick read in the same session. Report the object count, triangle
  count and file size with every look change, and ask for an FPS check. The user's limit was 400 FPS on
  2026-09-23 and is 1000 since 2026-09-24 (`Max FPS (config)` in the stats). In play they averaged about 820
  with the window look; the 2026-09-25 look read 910 on low settings.
- **The user saves their own copies** into the Scenarios folder (e.g. `Flow Fix Mesh Test d.sce`, an editor
  copy used for profiling). `install.py` only retires names listed in `installed.json`, so those stay put.
  Test scenarios are installed by hand and never enter that list.
- **Room look.** The user wants an ancient Egyptian window aesthetic, carved from geometry, in stone
  materials. No religious or cult symbols (user, 2026-09-24): no winged sun, uraeus, gods, ankh, djed, was,
  Eye of Horus, scarab or sphinx. Royal and natural motifs are fine (pharaoh's face with nemes, lions,
  cartouches, papyrus capitals, mouldings). Props keep their look under themes. A theme repaints each brush
  by its surface type (wall, floor, ceiling or ramp). Raised relief shades only when the theme is below
  full-bright 1. About 30 of the user's 149 themes paint all four surface types the same. Under those themes
  the window, frame, pilasters and text merge into one surface. The user's white marble theme is one of them.
- **"Prop" can mean any piece.** The user sometimes says "prop" for any piece of the map, brushes included.
  On 2026-09-23 "reduce the number of used props overall" meant fewer blocks. When the user asks about props,
  check the screenshot or ask which pieces they mean.
- **Looks.** Targets are black by default. A target type that must stand out gets a different
  shape as well as a colour, for players who force enemy colours. The user's usual theme, Bassel 3, forces
  enemy colours and turns every target black. The user prefers a grey or dark grey theme.
- **Settings the user found or chose.** HP-as-score for value-weighted targets. The fire-delay trick
  in Hesitation. Keeping the frame off every target.
- **The user's view on arm tension.** A too-loose arm drags into the flick; it does not overflick.
  Do not prescribe "tense up".

## Design rules learned here

- **One demand per scenario.** Find the shortcut before the player does: nearest-target cherry-picking,
  camping, spam-clicking, sweeping, skipping hard targets. Fix it with fewer targets, rotation, spawn
  blocking or scoring.
- **Keep every target on screen.** Spawn areas are capped at about 46 by 26 degrees, because the view is centred on
  the crosshair.
- **Strip luck from the score.** Use fixed rotation cycles, not random ones.
- **Target values.** A target that waits when skipped needs points-per-second parity. A target that
  expires when skipped needs a premium, or nobody chases it.
- **Judge with data.** Whether a scenario does its job comes from the user's stats. The design intent
  alone doesn't settle it.

## Safety

- **Crash loop.** KovaaK's reopens the last played scenario at startup. A crashing scenario therefore makes
  the game crash on launch until that installed file is replaced. Try any change to map structure
  (brushes, materials) in a separate test scenario first.
- **Material groups.** Installed maps have two or three material groups, never more, and their brushes use
  only groups 0 and 1. A build with six groups, which put new brushes on groups 3 to 5 after "None", crashed
  the renderer. The same room loaded once it used groups 0 and 1. Keep three groups at most, and put brushes
  only on groups 0 and 1.
- **Player spawn.** Always a SpawnPoint. A player SpawnVolume (as in the cA sixshot base map) spawns at
  a random point in its box, so the view shifts on every reload; `build.py` swaps it (`FIXED_SPAWN_DEFAULT`).
- **Geometry.** A SpawnVolume's half-extent is scale times 100, so tile with scale = step / 200. A brush's
  location is its minimum corner, and brush scale 1 spans 100 units. Player themes replace materials by
  surface type (wall, floor, ceiling, ramp).
- **Nothing gets deleted.** Old installed files move to `retired/`, and the user's own scenarios are never
  overwritten.

## Environment pitfalls

- **Shell.** Git Bash on Windows. Python cannot open `/tmp/...` paths, so write temp files inside the
  project. In inline Python, Windows paths need raw strings, because `\f` and `\U` break them.
- **The `rtk` hook** rewrites `grep`, and some flag combinations (`-h -a`) fail. Use the Grep tool or Python
  instead.
- **`.sce` files** are ASCII with CRLF line endings. `build.py` handles this; do not hand-edit.

## State and open items

The scenario history and verdicts are in `docs/scenarios.md`; the look's history is in `.agents/skills/kovaaks-scenario-design/references/decoration.md`.

The grey arena is closed. The Arena Test loads without a crash, and after the spawn-volume size fix no
target spawns on its frame. Themes that paint every surface type the same hide its frame and panel, and no
map setting can prevent this. The Egyptian window look replaced it. The Arena, Prop and Frame tests are in `retired/tests/`.

Still open:
- The window look is in all 13 scenarios since 2026-09-24, at the user's request (`ARENA_DEFAULT = "window"`,
  `egypt.WINDOW_LOOK`), with the palace courtyard since later that day (`egypt.COURTYARD`, the user's pick from
  the design workflow). On 2026-09-25, after the Sand Test, the look changed in all 13:
  - sandstone palace walls on a grey court;
  - the sculpted pharaoh's bust on the lintel;
  - sculpted lions facing the player;
  - smooth round-stroked text;
  - the window centred on the crosshair;
  - compact, slimmed files;
  - new screenshots for all 13.

  Earlier builds are in `retired/`, one folder per look: `plain look (installed until 2026-09-24)`,
  `window look without courtyard (installed until 2026-09-24)` and `window look with stencil art (installed until
  2026-09-25)`. The Sand Test and its earlier versions are in `retired/tests/`. No test scenario is installed.
  Ask for an in-play FPS reading and whether the restart hitch is gone.
- Calibration on 2026-09-24 (details in `docs/scenarios.md`): Check validated (the small target at
  1.5 keeps points-per-second parity on the new layout), Pathing validated after the four-cluster change,
  Early Braking works after the spacing change, Speed Build works, Recovery is clean at 3 s but weak on its own
  metric, Slow Start works (6 runs). Hesitation was changed to one target with a 0.7 s lifetime
  (click-first stayed at 7-15% in 6 mouse runs); it needs new runs.
