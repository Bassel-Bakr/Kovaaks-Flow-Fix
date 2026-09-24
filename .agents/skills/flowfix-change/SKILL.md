---
name: flowfix-change
description: Apply an approved change to the Flow Fix scenario set and install it into KovaaK's safely — edit gen_specs.py, rebuild, run the view and frame checks, update the guide/playlist/memory, install only changed files. Use this whenever a Flow Fix scenario, its layout, scoring, naming, arena or playlist is changed, added, renamed or reinstalled, or when the user reports that KovaaK's crashes or a scenario looks wrong after an install.
---

# Changing and installing Flow Fix

The project lives in `D:\Projects\flowfix`. Its source of truth is `gen_specs.py`. Installed `.sce` files
are build outputs; never edit them by hand, because the next build overwrites them.

## Before building

- **Get a yes first.** The user wants to hear what will change and approve it. Say which scenarios change,
  what changes, and whether scores reset.
- **Pick the path.** A change to map structure (brushes, `materialSets`, arena) goes through a separate
  test scenario first, because a crashing scenario makes the game crash on launch. Scenario-setting
  changes can go straight in.

## Steps

1. **Edit `gen_specs.py`.** Leave a short comment on why each value is what it is, with the date and the
   evidence (for example "at 14 targets the user's runs matched plain cA sixshot"). These comments are
   how future sessions know which values are measured and which are guesses.
2. **Build:**
   ```bash
   python gen_specs.py && python build.py specs.json out
   ```
   It must print 0 errors. Treat warnings about appended keys as bugs: they mean a key name doesn't
   exist in the copied section.
3. **Check:**
   ```bash
   python check_view.py            # 0.0% off screen for every scenario
   python check_frame.py test_out  # only when the arena is involved
   python check_scene.py test_out  # on every room look
   ```
4. **Playlist, when names or order change:**
   ```bash
   python playlist.py specs.json "out/Flow Fix.json" "Flow Fix" "$(date +%s)"
   ```
5. **Update `Flow Fix guide.md`** wherever the change shows: the symptom table, the "change first" table,
   descriptions, and the in-game checks list. Update `docs/scenarios.md` (setup, why, evidence, the table at the
   top) or `docs/look.md` for a look change, and move an idea out of `docs/future.md` once it is built.
6. **Install:** back up the installed files you are about to replace into `retired/` (a dated folder), then
   `python install.py --dry-run`, then `python install.py`. It copies only changed files,
   verifies each copy, and moves to `retired/` only scenarios it installed before (listed in
   `installed.json`) that are no longer built. It never touches the user's own saves or hand-installed test
   scenarios, and it never overwrites a file in `retired/`. Tell the user to restart KovaaK's.
7. **Record it.** Put the new values and why in `docs/scenarios.md` (or `docs/look.md`); if your agent keeps its
   own notes or memory, update them too. Also update AGENTS.md if a
   rule or preference changed.

## Renaming

KovaaK's keys score history and stats CSV filenames by scenario name, so a rename starts a fresh history.
Say so before renaming. Afterwards, make sure the stats scripts read both the old and new names.

## The arena test path

Try every room look (the grey arena, the Egyptian window) as one test scenario in `test_out/` first.
- **Grey arena:** build `Flow Fix Arena Test`, a copy of one spec with `"arena": True`. Then run
  `python check_frame.py test_out`.
- **Egyptian window:** `python egypt_test.py` builds the test scenarios. It also builds all 13 scenarios in
  three versions of the look, into `test_out/egypt_all/`, `test_out/egypt_mesh_all/` and
  `test_out/egypt_window_all/`.
- **Every look:** run `python check_scene.py` on the folder you test, for example
  `python check_scene.py test_out/egypt_all`. It fails if a brush or prop in front of the targets can
  cover a target.

Install only that one test file, by hand. `install.py` copies scenarios only from `out/`, so it never
installs a test. Keep one test installed at a time, and move a superseded test to `retired/tests/`. Have
the user open it:
- If it crashes, read the log, then replace the installed test file with a safe build so the game can
  start.
- If it loads, that is not enough. The grey arena loaded without a crash, but it never went into the set.
  The user saw that some themes do not show its frame. They asked for solid props instead, and then chose
  the Egyptian window look.
- A new look goes into the 13 scenarios only after the user checks it in game and says yes. The window look
  did so on 2026-09-24: `ARENA_DEFAULT = "window"` in `build.py`. To change the look of every scenario, edit
  `egypt.WINDOW_LOOK` or `egypt.py`, test it as a single test scenario first, then rebuild and install. Back up
  the installed scenarios into `retired/` before overwriting them, since `install.py` overwrites changed files.

## Report back

Say what changed, what was verified (errors, off-screen checks, byte-identical installs), what still
needs an in-game check, and whether scores reset.
