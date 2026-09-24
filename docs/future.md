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
- **In-play FPS with the 2026-09-25 look:** the user read 910 FPS on low settings in the Sand Test. Read `Avg FPS` in
  the stats of the next runs, with the user's usual theme, and check that the restart hitch is gone.

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

- **The sculpts under all-alike themes.** The bust and the lions are no longer stencils, so under the 30 themes that
  paint every surface type the same they read by their shape and shading alone, and not at all at full brightness.
  A screenshot under one of them would show whether they need anything, such as a prop, which themes do not repaint.
- **Courtyard under all-alike themes.** Under the same themes the courtyard reads only by its silhouette against the
  sky. A screenshot would show whether the portico or the towers need more contrast.
- **More detail in the sculpts.** `make_lion.py` and `make_pharaoh.py` can take more parts (mane locks, paw toes, the
  nemes' brow band) at little cost to the frame rate; each triangle costs file size, though. Coarser cells (lions 10,
  bust 8) would save about 20% more if the file ever needs it.
- **One outline per sign.** The text is overlapping round strokes. Merging each sign's strokes into one outline
  would cut the text's triangles further and remove the overlaps.
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
- **Slim the base map's objects.** `SLIM_MESHES` only touches custom meshes. The plain blocks (window stone, court
  blocks) could merge into meshes and be slimmed too, if the file size or the restart hitch ever matters again.
- **Version control.** The project became a git repository on 2026-09-24 (built outputs, test builds and `retired/`
  are ignored; see `.gitignore`). Commit each approved change with its docs.
- **The wiki.** `decoration.md`, `mechanics.md` and `docs/` are written to be moved into a wiki as they are.
