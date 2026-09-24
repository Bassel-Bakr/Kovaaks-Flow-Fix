---
name: kovaaks-scenario-design
description: Design or change a KovaaK's (FPSAimTrainer) scenario so it trains one specific aim weakness, using mechanics that are confirmed to work. Use this whenever the user wants a new drill, wants a scenario to target a flowchart problem, asks why a scenario isn't training what it should, wants targets worth different points, wants timed or pokeball or delayed-shot targets, or talks about spawn areas, target sizes, rotation, scoring, arenas, themes or map geometry, even if they don't say "design".
---

# KovaaK's scenario design

A scenario is a measuring instrument for one demand. Design it so the named weakness is the bottleneck,
nothing else is noisy, and the score pays for the right behaviour. Before building, write one sentence
saying what the scenario should be hard at.

## Steps

1. **Name the demand.** Map it to a node of the flowchart
   (`D:\Projects\aim\docs\articles\weakness-targeted-static-flowchart.md`). Respect the user's position:
   a too-loose arm drags into the flick; it does not overflick.
2. **Pick mechanics** from `references/mechanics.md`. Use only mechanics marked confirmed, or flag the
   unconfirmed ones to the user as a test item.
3. **Hunt the shortcut before the player finds it.**
   - **Nearest-target cherry-picking** with 3 or more targets turns wide flicks into short ones. Use fewer
     targets or spawn blocking.
   - **Skipping hard targets.** Use rotation slots, so a skipped target waits and blocks its slot.
   - **Letting timed targets expire** costs nothing unless the score gives them a premium.
   - **Spam-clicking.** Use a miss penalty, but not in recovery drills, where free misses are the point.
   - **Sweeping with held fire** in pokeball. The dwell requirement blocks it.
4. **Set the score model deliberately.** Whatever it pays for is what gets practised.
   - Use score per kill for equal targets.
   - Use HP-as-score (ScorePerDamage=1, EnableOverDamage=false) for value-weighted targets.
   - A target that waits when skipped needs points-per-second parity with the others. A target that
     expires when skipped needs a premium.
5. **Strip luck.** Use fixed, phase-shifted rotation cycles, not random ones, so every run gets the same mix.
   - **Lifetimes add noise when targets are abundant.** If the slots spawn targets much faster than the player
     kills them, expiry costs nothing and vanishing targets waste flicks (Recovery at 1.5 s).
   - **A deadline forces a habit.** One target whose lifetime is shorter than the bad habit's timing makes the
     habit fail every time (Hesitation: aim-then-click about 0.8 s, lifetime 0.7 s).
   - **Clusters make routes matter;** an even dense field plays like sixshot (Pathing).
   - **A time bank amplifies pace;** judge it by kills per second (Speed Build).
6. **Respect the view.** Keep the spawn area within about 46° × 26° (103 FOV, 16:9). The view is centred on
   the crosshair, so a wider area puts one target off screen while you aim at another. Verify with
   `check_view.py`.
7. **Calibrate against data, not intent.** Compare against the user's `cA sixshot` runs, never
   `cA sixshot dense`. A drill whose kill-time spread matches plain sixshot isn't testing anything new.
   See the kovaaks-run-analysis skill.

## User preferences

- **Naming.** `Flow Fix [problem]`. No numbers, no initials.
- **Looks.** Black targets by default. A type that must stand out gets a different shape as well as a
  colour, because players can force enemy colours. The user prefers a grey or dark grey theme.
- **Process.** Propose the change, show what it does, and wait for a yes before building.

## Map structure limits (a crash risk)

- **Material groups:** only 2 plus "None". More crash the renderer, and the game then crash-loops on
  launch.
- **Themes:** they replace materials by surface type (wall, floor, ceiling, ramp). Something that must stay
  visible, like a frame, needs a surface type different from its surroundings.
- **SpawnVolume half-extent** = scale × 100. A brush's location is its minimum corner, and brush scale
  1 = 100 units.
- **Player spawn** must be a SpawnPoint (one exact position), not a SpawnVolume (a random point in a box).
  A volume shifts the view on every reload and invalidates the angle checks. Check this in any base map
  you copy; cA sixshot's map has the volume.

Details and recipes are in `references/mechanics.md`. Every current scenario's design, evidence and verdict is in
`docs/scenarios.md` (with the design rules learned from calibration), and unapproved ideas are in `docs/future.md`. Decoration (materials, themes, props, custom meshes, the
art pipeline, the Egypt window look and its research sources) is in `references/decoration.md`; keep it current,
the user wants it for a wiki.
