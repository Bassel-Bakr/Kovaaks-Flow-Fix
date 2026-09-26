# Flow Fix scenarios: design specs and calibration

Each scenario attacks one problem from the Chinese weakness-targeted static flowchart: a Chinese original credited to
violat3, circulated by jizu, and translated into English by M0NARK in March 2025. The user's own write-up with every
node animated is `D:\Projects\aim\docs\articles\weakness-targeted-static-flowchart.md`. All of them start from `cA sixshot dense`:
the same room, FOV 103, the BB Gun and the same target colour (black). `gen_specs.py` is the source of truth; this page
explains the numbers in it. Status and data are as of 2026-09-24.

Every scenario uses the Egyptian window look with the palace courtyard (see `look.md`). The look does not change
the drill: targets spawn in the same places, and nothing covers them.

**Centred on the crosshair (2026-09-25).** The base map's target grid is centred 0.6° left of and 1.5° below the
crosshair, and every Flow Fix spawn area used to inherit that offset. At the user's request, every spawn area is now
centred on the crosshair (`CY, CZ = 0, 0` in `gen_specs.py`): each layout moved 30 units right and 80 up, and the
window moved with it. Target sizes, spacing and scoring are unchanged, and no angle moves by more than 1.5°, so runs
before and after compare, although the scenario hash changed.

**In game.** Every description starts with the flowchart problem it targets ("Chinese weakness-targeted static
flowchart: ..."), then says what it trains, how it works and how it scores (2026-09-24). The search tags are
"Flow Fix, flowfix, Static, Clicking, Bassel, Bakr, Egypt"; the aim type is Clicking, subtype Static.

## At a glance

| Scenario | Problem it trains | Setup in one line | Score | Status |
| --- | --- | --- | --- | --- |
| Overflick | Overflicking, too much force | 6 targets, shot fires 50 ms after the click | kills, miss −0.5 | Delay confirmed; no runs since the rename |
| Lingering | Crosshair lingers after the flick | 4 targets, hold fire for 80 ms of contact | kills, misses free | Validated |
| Wide Control | Too little control on wide flicks | 4 small targets spread wide | kills, miss −0.25 | 1 old run; needs runs |
| Slow Start | Dragging initial flick | 2 big targets worth 2 points, draining to 0 in 1 s | remaining HP, miss −0.1 | Works (6 runs) |
| Hesitation | Waiting to be sure before clicking | 1 target that lives 0.7 s, shot fires 300 ms after the click | kills, miss −0.5 | Forces its demand (3 runs) |
| Early Braking | Decelerating too early | 2 big targets, flicks of mixed length | kills, miss −0.25 | Works |
| Early Click | Clicking too fast | 3 large targets, long flicks | kills, miss −1 | No runs since the rename |
| Micro Adjust | No micro adjustments | 1 small target on an outer ring | kills, miss −0.5 | No runs since the rename |
| Pacing Drop | Wider flicks ruin pacing | 4 slots cycling big/mid/small targets | kills, miss −0.25 | Validated; 1 new run unread |
| Pathing | Cluster approach, target priorities | 30 small targets in 4 corner clusters | kills, miss −0.25 | Validated |
| Recovery | Pacing falls apart after a miss | 5 targets that live 3 s, misses free | kills | Clean, but weak on its own metric |
| Speed Build | Controlled bursts, building speed | Sixshot dense on a 20 s clock, +0.27 s per kill | kills, miss −0.1 | Works |
| Check | All of the above | 3 target types with values 1, 1.5 and up to 4 | remaining HP, miss −0.5 | Validated (the reference) |

Units: sizes are `MainBBRadius` in world units (map units × 3.15). Spawn areas are the angle they cover from the
player (check_view.py prints them); the cap is about 46° × 26°, so no target can be off screen while you aim at
another. The baseline for every comparison is the user's last ~30 runs of plain `cA sixshot` (not dense): about
146.5 score, 0.37 s median per kill, kill-time spread (CV) 0.33-0.34, about 37% of kills under 0.35 s.

## The scenarios

### 01 Overflick
- **Demand.** Stop on the target before clicking. Flowchart: overflick, too much force, decelerating too late.
- **Setup.** 6 targets, radius 72, at least 900 apart, spawn area 32.9° × 22.2°. Weapon "BB Gun steady": the shot
  fires 50 ms after the click, where the crosshair is then. A miss costs half a kill.
- **Why.** Without the delay it played like plain sixshot, and a miss penalty cannot tell an overshoot from an
  undershoot. With the delay, a shot only lands if the crosshair has stopped.
- **Evidence.** The 50 ms delay was confirmed working on 2026-09-23 (mouse vs keyboard clicks differ; the guide
  says to use the mouse button). No runs under the current name yet.

### 02 Lingering
- **Demand.** A fast flick, a short stop, straight on. Flowchart: crosshair lingers, fluid transitions.
- **Setup.** 4 targets, radius 60, at least 900 apart, never spawning within 10° of the crosshair, spawn area
  36.3° × 22.2°. Weapon "Poke-Drill": hold fire; it deals 0.2 damage every 0.01 s. Targets have 1.8 HP and heal
  100 HP per second, so a kill needs 80 ms of unbroken contact and any gap heals it. Misses are free.
- **Evidence.** Validated: every kill took at least the 9 hits the dwell requires.

### 03 Wide Control
- **Demand.** Land a wide flick with control and correct before confirming. Flowchart: too little control on wide
  flicks, tense arm.
- **Setup.** 4 small targets, radius 40, at least 1500 apart, never within 6° of the crosshair, spawn area
  46.2° × 25.8° (the full cap). A miss costs a quarter kill.
- **Evidence.** One old run, which suggested it may be too lenient. Needs 3 runs.

### 04 Slow Start
- **Demand.** Start each flick fast; don't drag. Flowchart: dragging initial flick, arm too relaxed.
- **Setup.** 2 big targets, radius 100, at least 1500 apart, never within 10° of the crosshair, spawn area 46.2° ×
  25.8°. Each target has 2 HP and drains 2 HP per second, so it is worth 2 points when it appears and 0 after 1 s.
  Score is the target's remaining HP at the kill (HP as score). A miss costs 0.1.
- **Evidence (6 runs).** Kills 108-134, value per kill 0.44-0.52, about 20-24 targets expire per run. The score
  varies about twice as much as the kill count, so the draining value pays for speed beyond kills. About 80% of
  kills go to the target that was already waiting; each flick then starts right off the previous kill, which is the
  demand. Verdict: works.

### 05 Hesitation
- **Demand.** Click as you start the flick, and be on target when the shot fires. Flowchart: dragging initial flick,
  pre-emptive hit confirmation.
- **Setup.** 1 target at a time, radius 72, never within 6° of the crosshair, spawn area 32.9° × 22.2°. It has 1 HP
  and drains in 0.7 s. Weapon "BB Gun committed": the shot fires 300 ms after the click. A miss costs half a kill.
- **Why.** The 300 ms delay was discovered by the user while testing Overflick. With 3 targets and no lifetime, the
  user's 6 mouse runs aimed first and then waited out the delay (click-first kills stayed at 7-15%). Now aiming
  first and then clicking takes about 0.8 s and outlasts the target, while clicking first takes about 0.55 s.
- **Evidence (3 runs).** About 74% of targets caught, a median of 0.6 s from appearing to kill (so the click comes
  about 0.3 s in, early in the flick). Misses rose to 22-29, because a late shot at a vanished target counts as a
  miss. Verdict: forces its demand. Keyboard-key runs are not comparable with mouse runs.

### 06 Early Braking
- **Demand.** Keep the speed late in the flick, then stop. Flowchart: decelerating too early.
- **Setup.** 2 big targets, radius 100, at least 400 apart, never within 4° of the crosshair, spawn area 44.6° ×
  27.6°. A miss costs a quarter kill.
- **Why.** With 3 targets there was always a near one. With 2 targets at least 1000 apart, every flick was medium to
  long (10% of kills under 0.35 s). Spacing 400 lets short flicks mix in with the wide ones.
- **Evidence (4 runs at spacing 400).** Scores 138-141, 18-26% of kills under 0.35 s. The spread of kill times did
  not rise (0.22-0.32), because big targets make short and long flicks take similar times. Verdict: works.

### 07 Early Click
- **Demand.** Click only once you have landed, with the same rhythm every time. Flowchart: clicking too fast,
  inconsistent hit confirmation.
- **Setup.** 3 large targets, radius 95, at least 2500 apart (long flicks), never within 10° of the crosshair, spawn
  area 44.6° × 27.6°. A miss costs a whole kill, double taps included (overshot protection off).
- **Evidence.** No runs under the current name. Needs 3 runs.

### 08 Micro Adjust
- **Demand.** Flick, then make the small correction before clicking. Flowchart: no micro adjustments.
- **Setup.** 1 small target, radius 32, on an outer ring (the middle 25.8° × 11.2° is empty), never within 12.5° of the
  crosshair, spawn area 46.2° × 25.8°. A miss costs half a kill.
- **Evidence.** No runs under the current name. Needs 3 runs.

### 09 Pacing Drop
- **Demand.** Keep the pace through size changes: fast on easy targets, patient on small ones. Flowchart: wider
  flicks ruin pacing, pacing keeps dropping.
- **Setup.** 4 slots, each cycling through a fixed order of big (radius 100), mid (60) and small (30) targets,
  phase-shifted so every run gets exactly 25% big, 50% mid and 25% small. A skipped small target waits in its slot.
  At least 1200 apart, spawn area 46.2° × 25.8°. A miss costs a quarter kill.
- **Why.** Random rotation put luck in the size mix; fixed cycles removed it. The small size went from 35 to 30,
  because at 35 small kills were only 5% slower than mid ones.
- **Evidence.** Validated with the fixed cycles. One run on the current build (2026-09-24 01:03) is not read yet.

### 10 Pathing
- **Demand.** Clear a cluster, then make one wide flick to the next; choose the route. Flowchart: cluster approach on
  wide flicks, target priorities.
- **Setup.** 30 targets, radius 40, at least 250 apart, in four clusters of 400 × 300 map units near the corners of a
  39.7° × 21.7° area. A killed spot refills after 0.25-0.4 s (respawn delay, not yet confirmed in game). A miss
  costs a quarter kill.
- **Why.** At 14 targets, and again as an even field of 30, it played like plain sixshot: the next target was always
  near. Clusters make the route matter.
- **Evidence (3 runs).** Scores 146-148, 21-36% of kills under 0.3 s inside clusters, spread 0.42-0.47 (sixshot 0.34).
  The user's test run staying on one half scored about 18 lower, so camping loses. Verdict: validated.

### 11 Recovery
- **Demand.** After a miss, get the rhythm back instead of slowing down. Flowchart: disrupted pacing, hard pressure.
- **Setup.** 5 targets, radius 60, at least 900 apart, spawn area 43.0° × 22.2°. Each lives 3 s. Misses are free.
- **Why.** At a 1.5 s lifetime, 5 slots spawned 3.3 targets per second against 1.5 kills per second: about 60%
  expired, and targets vanished mid-flick, which made misses and slow kills noise from the mechanic.
- **Evidence (3 runs at 3 s).** Kills 110-127, misses 17-24, few expiries. The kill after a miss is 0.92× the normal
  time, the same as sixshot (0.91×): the user does not show the problem, so the drill has nothing to expose for them.
  Verdict: clean, but weak on its own metric. See `future.md` for redesign ideas.

### 12 Speed Build
- **Demand.** Build and sustain speed in controlled bursts. Flowchart: controlled bursts, cluster farming.
- **Setup.** Sixshot dense (6 targets, radius 65, its own spawn grid, 25.2° × 22.8°) on a 20 s clock. Every kill adds
  0.27 s. At the user's usual pace a run lasts about a minute; above 3.7 kills per second it never ends. A miss costs
  a tenth of a kill.
- **Evidence (4 runs).** Run length matches 20 + 0.27 s per kill. 2.45-2.68 kills per second, a steady pace from
  start to end. The score grows faster than the pace (+9% pace gave +33% score), so judge progress by kills per
  second, not score. Verdict: works.

### 13 Check (the reference; always last in the playlist)
- **Demand.** Everything at once: pacing, wide flicks with a micro adjustment, and fast starts.
- **Setup.** 3 slots with fixed, phase-shifted cycles of 5 targets (3 middle, 1 small side, 1 cube). Score is the
  target's remaining HP (HP as score); a miss costs half a point.
  - Middle targets: radius 60, worth 1, in a central area.
  - Small side targets: radius 35, worth 1.5, far left and right. A skipped one waits, so its value only needs
    points-per-second parity with the middle targets.
  - Cube: a dark orange cuboid (half-width 53, a different shape so it stands out even when enemy colours are
    forced), worth 4 draining to 0 over 1.5 s, in a ring around the middle. A skipped cube expires, so it pays a
    premium.
- **Evidence (3 runs).** Points per second: middle 2.48, small side 2.68 (parity within 8%), cube 3.64 (a 47%
  premium). About 6 of 25 cubes expire; the median cube is hit 0.9 s after it appears, worth 1.6. Verdict: validated.
  Do not change Check casually: it is the reference.

## Design rules learned here

- **One demand per scenario,** and find the shortcut before the player does: nearest-target cherry-picking, camping,
  spam-clicking, sweeping, skipping hard targets. Fix it with fewer targets, rotation, spawn blocking or scoring.
- **Keep every target on screen:** spawn areas within about 46° × 26°.
- **Strip luck from the score:** fixed rotation cycles, not random ones.
- **Target values:** a target that waits when skipped needs points-per-second parity; one that expires needs a premium.
- **Lifetimes create noise when targets are abundant:** if slots spawn targets much faster than the player kills them,
  expiry costs nothing and vanishing targets waste flicks (Recovery at 1.5 s).
- **A deadline forces a habit:** one target with a lifetime shorter than the bad habit's timing (Hesitation).
- **Clusters make routes matter:** an even dense field plays like sixshot (Pathing).
- **A time bank amplifies pace:** read it by kills per second (Speed Build).
- **Big targets compress kill times:** a change in flick lengths may not show in the time spread (Early Braking).
- **Judge with data,** from at least 3 runs of one build. Runs are grouped by the scenario hash in each stats file;
  keyboard-key and mouse-button runs of delayed-shot scenarios are not comparable.

## Flow Fix 2 (2026-09-26)

A second batch of 8 scenarios, installed next to Flow Fix with its own playlist, "Flow Fix 2". It follows the review
of 2026-09-25: the tester's feedback and runs, the user's worry that some drills build bad habits, and two research
reports. Flow Fix itself is unchanged.

**Rules.**
- **A normal click only:** an instant shot on a single click. After practice with a delay, performance drops once
  the delay is removed ([Cunningham et al. 2001](https://doi.org/10.1111/1467-9280.d01-17)), and the aftereffect does
  not fade on its own ([Kennedy et al. 2009](https://pubmed.ncbi.nlm.nih.gov/18609410/)). The tester scored 0 kills
  from 84 shots in Hesitation, and both players held fire through the flick in Lingering (2-6% clean landings).
- **Misses cost time, not points.** The gun holds one round: a kill refills it, and a miss forces a 0.35 s reload.
  People set their aim and speed by the payoff ([Trommershäuser et al. 2003](https://pubmed.ncbi.nlm.nih.gov/12868646/),
  [Dean et al. 2007](https://pubmed.ncbi.nlm.nih.gov/18217850/)), and cheap misses cost accuracy here: the tester's
  Slow Start 77% against 90.5% in cA sixshot, the user's Recovery 85% against 91%. Voltaic uses reloads on its speed
  scenarios.
- **Gentle deadlines only:** imposed timing costs accuracy ([Zhang et al. 2010](https://pubmed.ncbi.nlm.nih.gov/20884550/)).
- **Several distances where one would do:** one exact condition becomes a skill of its own
  ([Keetch et al. 2005](https://pubmed.ncbi.nlm.nih.gov/16262492/)).
- **Judge by transfer:** a cA sixshot run before and after a session, not the drill's own score
  ([Soderstrom & Bjork 2015](https://bjorklab.psych.ucla.edu/wp-content/uploads/sites/13/2016/11/soderstorm_ra_learningvsperformance.pdf)).
- **The frame look:** the window frame and its text alone, without the courtyard, the bust or the lions
  (`egypt.FRAME_LOOK`, arena "frame"). Return is 143 map objects, 40 of them meshes, about 11,700 triangles and
  2.5 MB, against 193 objects, 30,400 triangles and 5.1 MB for Check.

| Scenario | Replaces | Setup | Score |
| --- | --- | --- | --- |
| Overflick | Overflick's 50 ms fire delay | 6 targets, radius 72, as Overflick | kills |
| Return | Lingering's hold-fire pokeball | One slot: a sphere (radius 60, worth 1) 8, 10 or 12 deg out, then a cube (half-width 53) at the centre, worth 2 and draining to 0 in 0.7 s | remaining HP |
| Slow Start | Slow Start's 0.1 miss cost | As Slow Start | remaining HP |
| Cold Start | Hesitation's 300 ms fire delay | 1 target, radius 72, never within 6 deg of the crosshair, worth 2 and draining to 0 over 1.5 s | remaining HP |
| Ladder | Early Braking | One slot in a fixed cycle: cube, near, cube, mid, cube, far. Spheres of radius 60 at 5, 10 and 18 deg (18 only within 35 deg of the horizontal). Each leg is its own bot type | kills |
| Early Click | Early Click's whole-kill miss cost | As Early Click; double taps count as misses | kills |
| Anchor | Micro Adjust | One slot, 12 pairs in a fixed, scrambled order: a big cube (half-width 80) at one of 6 spots, then a small sphere (radius 32) 2.5-3.5 deg from it, on a random side | kills |
| Recovery | Recovery's free misses | As Recovery | kills |

**How to read the stats.** Each kill row names its bot type.
- Return: the gap before each `home` kill is the transition plus a known return.
- Ladder: the `home` rows after `near`, `mid` and `far` are planned flicks of 5, 10 and 18 deg. If the far legs cost
  more than their distance explains (time against log2(2D/W)), the braking is early.
- Anchor: the `s1`-`s6` rows time the correction apart from the flick to the cube.
- Cold Start: the value at the kill gives the hit time, 1.5 x (1 - value/2), in 0.1 s steps.
- All: accuracy against cA sixshot, and a cA sixshot run after the session.

**Status.** Installed 2026-09-26, no runs yet. Untested in game: the one-round reload (its keys come from 1w2ts
reload smallflicks) and a fixed rotation with repeated entries (Anchor).

**First runs (user, 2026-09-26, 3-4 runs each; no cA sixshot runs around them yet).**
- Overflick: 142-150 kills at 92.8% accuracy, the same as plain cA sixshot. Nothing forces the stop: an overflick
  corrected before the click costs only a little time. Redesign pending.
- Slow Start: 91.0% accuracy (Flow Fix Slow Start 88.3%) with more kills (133-141 against 124-133). Recovery: 90.9%
  (was 84.7%) with 119-132 kills. The one-round gun brought accuracy back to cA sixshot's level without costing kills.
- Return: the return to the cube takes 0.48 s at the median, worth 0.86 of 2; 3 cubes expired in 3 runs.
- Ladder: planned returns take 0.479, 0.511 and 0.534 s after 5, 10 and 18 deg flicks, a straight line against
  log2(2D/W) (about 30 ms per bit). The far flicks cost no more than their distance explains, so the user shows no
  early braking here.
- Anchor: the fixed order works (a1, s1, a4, s4, ...). Correction legs take 0.62 s at the median, 0.09 misses per kill.
- Cold Start: 90-93 kills, value 1.2 of 2 at the median (hit 0.6 s after the target appears), 97.6% accuracy.
- Early Click: 132-143 kills at 95.4%. Frame look: 933-972 FPS against the user's 1000 limit.
- Changed the same day: Ladder's and Return's cube now sits centred on the crosshair, with a square marking the centre.

**Height fix (2026-09-26, all 21 scenarios, user: "fix layout").** A target stands on its spawn point, so every layout
sat 0.4-0.6 deg above where the spec put it (half the target's height plus 8 world units). `build.py` now lowers each
volume by that, and targets are centred where the spec says. Sizes, spacing and scoring are unchanged, but every
scenario's hash changed, so compare runs across the date. Pacing Drop's volumes take every size, so they use the
mean of the three (the residue is about 0.2 deg). The builds before the fix are in
`retired/layout before the height fix (installed until 2026-09-26)/`.
