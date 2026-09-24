# Suggestions for future changes

Ideas collected on 2026-09-24. None of them is approved: each needs the user's yes before it is built, and scenario
changes should wait for data (3 runs of the current build) rather than intent.

## Calibration still to do

- **Play the scenarios without data on their current build:** Overflick, Wide Control, Early Click and Micro Adjust
  (no runs under their current names), Lingering and Pacing Drop (validated earlier; one new Pacing Drop run is
  unread). 3 runs each, then "played X".
- **Hesitation:** track the share of targets caught and the misses. If it stays frustrating, ease the lifetime to
  0.8 s (`HealthRegenPerSec` -1.25); once more than about 85% are caught, tighten it to 0.6 s (-1.667).
- **Pathing:** the respawn delay (0.25-0.4 s) is still unconfirmed in game. A run where killed spots refill instantly
  would look the same in the stats, so it needs a visual check.
- **In-play FPS with the courtyard:** read `Avg FPS` in the stats of the next runs, with the user's usual theme.

## Scenario ideas

- **Recovery redesign.** The user does not slow down after a miss, so the drill has nothing to expose. Two options if
  the problem ever shows up: combine it with Speed Build's time bank (misses stay free, but every slow kill drains
  the clock, so a post-miss slowdown costs time), or use HP-as-score targets whose value drains from the moment they
  appear, so hesitation after a miss costs points.
- **Slow Start, cold starts.** A variant with one target at a time, whose value drains from its appearance, would
  test reacting to a new target as well as accelerating. Keep the current drill; this would be a separate scenario.
- **Check, exact parity.** The small side target at 1.5 pays 8% more per second than the middle targets; 1.4 would be
  exact. The gap is within run-to-run noise, so change it only if more runs confirm it.
- **Early Braking, stop precision.** If the user wants the stop to matter more, smaller targets (radius 100 to 85)
  make a late stop harder; the guide lists this as the next step.
- **Speed Build.** Report kills per second next to the score in its analysis, since the score amplifies pace.
- **A consistency drill.** Flicks of one fixed distance in random directions would isolate rhythm from flick length,
  as a baseline for the other drills.

## Look ideas

- **Always-dark backing for the stencils.** Themes do not repaint props, so a dark plain prop behind the head and the
  lions would stay dark in every theme. The prop names in the editor's anime pack are unknown here; if the user lists
  them, a new sampler can test them (see `backing_sampler.py`, `backing_test.py`).
- **Courtyard under all-alike themes.** 30 of the user's 149 themes paint every surface type the same; there the
  courtyard reads only by its silhouette against the sky. A screenshot under one of them would show whether the
  portico or the towers need a stencil treatment too.
- **Variety between scenarios.** The court fits each window already; small per-scenario touches (the pool, the palm
  types) could help tell scenarios apart at a glance, if the user wants that.

## Code and tooling

- **Retire the legacy looks.** `egypt.py` still carries the full room, the pixel signs, `MESH_DECOR`, the side labels
  and other switches used only by old tests. Removing them would make the window look much easier to change.
  `arena.py` and the prop scripts are retired too.
- **One stats report.** A single script that groups every scenario's runs by scenario hash and reports the standard
  metrics plus `Avg FPS` would replace the per-scenario scripts for routine checks.
- **A perspective preview.** The courtyard workflow's `courtyard/final_render.py` (used by `make_screenshots.py`) draws the player's view in
  perspective. Promoted to a project tool, it would preview any look change without the game.
- **Crash guards in the build.** Fail the build if a map has more than 3 material groups, or a mesh with an index out
  of range, before anything can reach the game.
- **Version control.** The project became a git repository on 2026-09-24 (built outputs, test builds and `retired/`
  are ignored; see `.gitignore`). Commit each approved change with its docs.
- **The wiki.** `decoration.md`, `mechanics.md` and `docs/` are written to be moved into a wiki as they are.
