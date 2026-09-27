# Scenario types: what the installed scenarios and the user's stats show

A study made on 2026-09-25 of every scenario type: static and dynamic clicking, tracking, target switching and the
untagged rest. It draws on the 388 scenarios installed in KovaaK's and the user's 71,755 stats files, as groundwork
for Flow Fix drills beyond static clicking. `survey_scenarios.py` reads every installed scenario into
`test_out/survey.json`; the numbers below come from that file and from the stats. Values are from other authors'
scenarios (mostly Voltaic, "VT"). What a setting does is inferred from its name and how it is used, unless it says
confirmed. Treat the "Unknowns" list as things to test in game before relying on them.

## The corpus

- **388 scenarios.** By the game's own tags (`AimTypeTag` / `AimSubTypeTag`):
  - Tracking: Smoothness 74, Reactivity 47, Both 46.
  - Target Switching: Static 15, Other 13, Fast 12, Slow 8.
  - Clicking: Static 69 (13 of them Flow Fix), Dynamic 30.
  - Other: 3. Untagged (older files): 67.

  Flow Fix is left out of the clicking numbers below. The top-level flags `AimTypeFlicking` (34 scenarios),
  `AimTypePlayerMovement` (5) and `AimTypeProjectile` (3) add detail to the tags. `DifficultyTag` holds a number.
- **Two map formats.** 201 scenarios hold a JSON map, like ours. 185 hold an older text format that starts with
  "reflex map version 8": the map format of the game Reflex Arena. It stores brushes as vertex lists, with Y up,
  and entities by type: PlayerSpawn, WorldSpawn, CameraPath, Target and Effect. A PlayerSpawn marks its team with
  `Bool8 teamA 0` or `Bool8 teamB 0`, meaning "not for team A" or "not for team B".
- **JSON map objects in use** (number of scenarios): SpawnPoint 198, Clip 122, DefaultNoCollision 53, Waypoint 37,
  SpawnVolume 24, Hurt 12, Teleporter 9, FullClip 9, WeaponClip 9, JumpPad 6, and a few props.

## Features in use across the 375 scenarios that are not Flow Fix

How many scenarios use each mechanic, as a guide to what is common and what is rare:

| Mechanic | Scenarios |
| --- | --- |
| Bots that jump (dodge `JumpFrequency` > 0) | 228 |
| Invincible player | 220 |
| Score per damage / per kill / per hit | 145 / 139 / 100 |
| Over-damage on (`EnableOverDamage`) | 141 |
| Health bars hidden | 134 |
| Bots that change direction when hit | 105 |
| Flying bots | 71 |
| The player can move | 70 |
| Magazines and reloads | 61 |
| Timescale other than 1 (slowed or sped-up games) | 64 |
| Bot rotation profiles (`.rot`) | 62 |
| Bots with movement or other abilities in use | 59 |
| Untargetable bots (helpers) | 56 |
| Plain accuracy multiplier / square-root accuracy multiplier | 55 / 50 |
| Healing bots (positive regen: pokeball-style dwell) | 33 |
| Timed bots (negative regen) | 33 |
| Bots with a head hitbox | 21 |
| Hitscan radius above 0 (a thicker shot) | 19 |
| Teleporters or jump pads / hurt volumes | 14 / 12 |
| Waypoint paths | 13 |
| End after N kills | 12 |
| Aim assist on the weapon / bots that aim and shoot at the player | 11 / 11 |
| Movement bonus score (MBS) / score per time / per distance | 11 / 9 / 9 |
| Loss per miss | 9 |
| Projectile weapons | 8 |
| Bots that stand still until hurt | 7 |
| Kill-efficiency / damage-efficiency multiplier | 6 / 3 |
| Recoil / headshot-only bots | 5 / 5 |
| Time refilled by kill | 1 (and Flow Fix Speed Build) |
| Fire delay (`DelayBeforeShot`) | 0 (only Flow Fix Overflick and Hesitation) |
| Adaptive difficulty (time dilation, target size) | 0 |

## How a static clicking scenario is built (56, not counting Flow Fix)

- **Weapon.** Mostly a semi-automatic hitscan with 0.1 s between shots (39). 9 use a fully automatic or 0.01 s
  weapon, and 4 a projectile. 19 have magazines and reloads.
- **Targets.** Usually one hit to kill. A median of 5 on screen at once (2 to 8). Their median width is 0.9° (0.6 to
  1.9°), at a median distance of 4,200 units. `BlockedSpawnRadius` (median 280) in 35 keeps a new target from
  appearing under the crosshair.
- **Spawn areas.** They span a median of 45° × 26° (25° to 74° wide), so many are wider than the 46° × 26° that
  Flow Fix keeps to.
- **Score.** Per kill in 54 of 56, usually with an accuracy multiplier: square-root accuracy in 31, plain accuracy
  in 23. A miss penalty appears in only 4; the accuracy multiplier does that job instead.
- **Timing tricks.** 7 use timed targets (negative regen), 4 use bot rotations, and 1 plays at a timescale of 1.8.
  23 carry the `AimTypeFlicking` flag.

## How a dynamic clicking scenario is built (30)

- **Weapon and score.** A semi-automatic hitscan (25), mostly with 0.1 s between shots, some 0.14 to 0.15 s. Score
  per kill, with an accuracy multiplier in 20 of 30.
- **Bots.** A median of 5 at once. 44 of 69 bot types move: median top speed 28°/s (15 to 45), 1.55 s strafes
  (0.55 to 5.5), 0.12 s to top speed, and 35 of them jump. Median width 1.3° at 2,400 units, so they are closer and
  bigger than static targets. Most die in one hit; some take up to 100.
- **Other.** 5 let the player move (`AimTypePlayerMovement`), and 3 score a movement bonus (MBS).

## How a tracking scenario is built

- **Weapon.** Almost all use a hitscan, fully automatic weapon that fires every 0.01 s: 100 shots per second, each
  one a "hit" or a "miss". Voltaic calls it "Track Master 100". A few fire every 0.025 to 0.05 s.
- **Score.**
  - The Voltaic benchmarks score hits: `ScorePerHit` 1, and each shot does next to no damage. So the score is the
    number of hundredths of a second on target: 60 s gives at most about 6,000.
  - Others score damage (`ScorePerDamage` 1), which comes to the same thing with a steady damage rate.
  - An accuracy multiplier is almost never used (4 of 167).
- **Bots.** Usually 1 bot, sometimes a rotation of bot types (`AddedBots` names a `.rot` whose `ProfileNames` take
  turns). Most bots cannot die in practice: health 1 with damage 0.001 per shot, or health in the thousands.
- **Movement is two parts.** The Character Profile sets the physics: `MaxSpeed`, `Acceleration`, `Friction`,
  `BrakingDeceleration`, `Gravity`, `IsFlyer`, `JumpVelocity` and `AirControl`. The Dodge Profile sets the
  decisions:
  - `MinLRTimeChange` / `MaxLRTimeChange`: how long a strafe lasts before the next direction change, drawn at random
    between the two. `ToggleLeftRight` true makes each change a reversal.
  - `MinFBTimeChange` / `MaxFBTimeChange` with `ToggleForwardBack`: the same for forward and back.
  - `MinTargetDistance` / `MaxTargetDistance`: keeps the bot within this distance band from the player, for example
    1300 to 1900.
  - `JumpFrequency`, `MinJumpTime` / `MaxJumpTime`: jumps.
  - `ToggleUpDownMinTime` / `ToggleUpDownMaxTime`: up and down changes for flyers.
  - `StrafeSwapMinPause` / `StrafeSwapMaxPause`: a pause at each reversal.
  - `DamageReactionChangesDirection`: the bot changes direction when hit.
- **Several dodge profiles per bot.** A bot profile lists `DodgeProfileNames` with `DodgeProfileWeights`, and swaps
  between them every `DodgeProfileMinChangeTime` to `DodgeProfileMaxChangeTime` seconds. Controlsphere swaps among
  3 strafe styles every 3 to 5 s, and Ground's bots among 2 to 7 styles.

### Typical numbers by subtype (medians, with the 10th to 90th percentile)

The distance is from the player's spawn to the bots' spawn, in world units (map units × MapScale). Angular values
use that distance, so they are rough.

| | Smoothness | Reactivity | Both |
| --- | --- | --- | --- |
| Strafe time | 1.55 s (0.12-5) | 0.55 s (0.36-1.05) | 0.65 s (0.44-1.0) |
| Time to top speed (MaxSpeed / Acceleration) | 0.17 s (0.07-1.0) | 0.14 s (0.03-0.28) | 0.30 s (0.09-0.36) |
| Top angular speed | 34°/s (8-64) | 33°/s (14-47) | 33°/s (18-72) |
| Sweep per strafe | 31° (8-93) | 18° (6-28) | 18° (11-35) |
| Target width | 0.9° (0.1-3.5) | 3.0° (1.5-4.8) | 1.4° (0-4.1) |
| Distance | 2,873 | 2,062 | 1,856 |
| Bot health | 1 (1-300) | 350 (100-1000) | 1 (1-600) |
| Direction change on hit | never | 41 of 77 dodge profiles | 7 of 125 |

So smoothness comes from long strafes and wide sweeps; reactivity from short strafes, quick acceleration and bots
that change direction when hit (typically a 50% chance to ignore, after 0.125 s, with a 0.25 s cooldown). The top
angular speed is about the same, around 33°/s, in all three.

## How a target switching scenario is built

- **Several bots at once**, typically 4 (3 to 6), each dying after a short time on target and respawning at once
  (`MinRespawnDelay` 0.001) somewhere else. `BlockedSpawnRadius` 200 to 300 stops a new bot spawning on top of the
  crosshair.
- **Time on target per kill.** The weapon fires every 0.01 to 0.012 s, and damage per shot is set against the bot's
  health:
  - VT ControlTS and DriftTS: 0.02 damage against 1 health, so 50 hits, about 0.5 to 0.6 s on target.
  - VT DotTS: 0.05 damage against 1 health, so 20 hits.
  - Median time to kill over all switching scenarios: 0.05 to 0.5 s.
- **Score** is usually per hit (0.2 to 0.5 per hit in the Voltaic set) or per damage, so time on target pays, and
  kills only matter because a dead bot moves.
- **Movement by subtype.**
  - Static: `NoDodging` true.
  - Slow: long strafes (median 2.5 s) and quick acceleration.
  - Other (DriftTS): 0.35 to 0.7 s strafes, jumps and forward-back drift.
  - Fast: 4 s strafes at long range (6,600 units), so fast in angle.

## Recipes of the Voltaic benchmarks the user plays most

Angles use the distance from the player's spawn to the bots' spawn, so they are rough. "Hit" scoring counts
hundredths of a second on target.

| Scenario | Type | Bots | Size, speed, strafe | Weapon | Score |
| --- | --- | --- | --- | --- | --- |
| VT 1w2ts Advanced S5 | static clicking | 2 still | 0.8°; 1 hit; blocked radius 250 | semi-auto, 0.1 s | 10 per kill × accuracy and √accuracy |
| VT 1w4ts Novice S5 | static clicking | 4 still | 1.2°; blocked radius 190 | semi-auto, 0.1 s | the same |
| VT Pasu Intermediate S5 | dynamic clicking | 4 moving, plus 8 tiny still "knocker" bots | 2.0°, 13°/s, 1.4 s strafes, jumps; blocked radius 800 | semi-auto, 0.1 s | the same |
| VT Popcorn Intermediate S5 | dynamic clicking | 4 types × 5 | 1.9°, 26 to 36°/s, 2.5 to 5.9 s strafes, jumps | semi-auto | 10 per kill × √accuracy |
| VT Frogtagon Intermediate S5 | dynamic clicking | 4 flyers | 2.3°, 23°/s, one direction until turned (60 s strafes) | semi-auto, 0.1 s | 10 per kill × √accuracy |
| VT Floating Heads Intermediate S5 | dynamic clicking | 5 | 1.3°, 15°/s, 2.75 s strafes, jumps; blocked radius 600 | semi-auto, 0.1 s | 10 per kill × accuracy and √accuracy |
| VT Snake Track Advanced S5 | tracking, smoothness | 1 | 0.9°, 61°/s, 1.7 s strafes | 0.01 s auto | per hit |
| VT Smoothbot Advanced | tracking, smoothness | 1 flyer | 1.1°, 60°/s, 2 s strafes, jumps | 0.01 s auto | per damage |
| VT Ground Intermediate S5 | tracking, reactivity | 3 types in rotation | 2.3 to 2.7°, 42 to 44°/s, 0.65 to 0.8 s strafes; each lives 19 s | 0.01 s auto | per hit |
| VT Controlsphere Advanced S5 | tracking, both | 1, plus 2 invisible "repel" flyers | 3.1°, 72°/s, 0.65 s strafes, jumps | 0.01 s auto | per hit |
| VT ControlTS Intermediate S5 | switching, slow | 4 | 1.9°, 19°/s, 1 s strafes, jumps; 50 hits to kill | 0.012 s auto | 0.2 per hit |
| VT DriftTS Advanced S5 | switching, other | 4 | 1.9°, 34°/s, 0.5 s strafes, jumps; 50 hits to kill | 0.01 s auto | 0.2 per hit |
| VT DotTS Advanced S5 | switching, static | 5 still dots | 20 hits to kill | 0.011 s auto | 0.5 per hit |

Helper bots (tiny, invisible, never shot: Pasu's "knockers", Controlsphere's "repels") are a Voltaic habit. They
seem to steer the real target by pushing it; that is still to be tested.

## Untagged and "Other" scenarios (70)

- **67 untagged** (older files without `AimTypeTag`). By weapon: 39 use a fully automatic hitscan and mostly score
  damage (tracking style), 25 a semi-automatic hitscan scoring kills (clicking style), 3 a projectile weapon. 73 of
  their 97 bot types move, and the median bot health is 100.
- **3 tagged "Other"**: kill-scored drills with 1 to 7 bots, one of them with a practically endless time limit.

## Paths and waypoints (scripted movement)

- A spawn object's `Path` property lists waypoint names separated by commas, for example
  `B1,B2,B3,...,C15,...`. `LoopingPath` repeats it.
- A Waypoint object carries `Name`, `BotPauseTimeMin` and `BotPauseTimeMax`.
- The dodge profile's `WaypointLogic` decides how the bot uses the path: `Ignore`, `FollowAimAtWaypoint`,
  `FollowAimAtTarget` or `FollowUntilCombat`. `WaypointTurnRate` is set with it.
- 13 installed scenarios use paths: ClockTrack, VAI, TSK 8/Inf/WHAT THE Tracking, ZigZag Tracking. They give
  deterministic, repeatable movement, which suits drills that must be the same every run.

## Other tools seen

- **Timed bot lives.** VT Ground gives its bots 1,900 health and `HealthRegenPerSec` -100, so each bot dies by
  itself after 19 s. It is the same trick as Flow Fix's timed targets. The stats then log one row per bot life.
- **Helper bots.** VT Pasu adds 8 tiny still "knocker" bots (radius 4, health 100). VT Controlsphere adds two invisible flyers ("Repel D", "Repel U": radius 0.01, speed 100000,
  a "Seeking" dodge profile) next to the real target, in a map called "Wall Repellent Circle". Their exact role is
  unknown; they seem to shape the sphere's movement.
- **Abilities.** Bots can use movement abilities. "Blink" is a dash of 15,000 units per second for 0.075 s, with up
  to 3 charges, used in combat when the player is more than 1,500 units away. Weapon, melee and sprint abilities
  exist too.
- **Recorded movement.** `PlaybackOnSpawn` and `PlaybackOptions.*` on a character play back recorded input. One
  installed scenario uses it.
- **Adaptive difficulty.** `IsTimeDilationActive` and `IsTargetSizeActive` with `PerformanceTarget` scale bot speed
  or size to the player's performance. No installed tracking or switching scenario uses them.

## What the stats record, by type

- **Every run** ends with totals: kills, hit and miss counts, damage done, score, the scenario hash, the game
  version, the start time, and the player's settings (sensitivity, FOV, resolution, crosshair, `Max FPS (config)`,
  `Avg FPS`).
- **Clicking** writes one row per kill: `Kill #`, `Timestamp`, `Bot`, `Weapon`, `TTK`, `Shots`, `Hits`, `Accuracy`,
  `Damage Done`, `Damage Possible`, `Efficiency`, `Cheated`, `OverShots`. The time between kills, the misses per
  kill (Shots minus Hits) and the bot type are what the Flow Fix static analyses use.
- **Totals only for bots that never die.** A tracking run without kills writes no per-event rows, only the totals:
  shots, hits, misses, damage, score, and settings such as FPS, resolution and sensitivity. VT Controlsphere, for
  example, shows 6,001 shots and 3,172 hits (52.9%). There is no time series, so the stats cannot show where in a
  run tracking broke down.
- **One row per kill otherwise.** When bots die, each kill is a row with its time, time to kill, shots, hits,
  accuracy and damage. Switching scenarios and timed-life bots (VT Ground) therefore give time-resolved data.
- **Design rule for Flow Fix.** To judge a tracking drill from the stats, give its bots a finite, timed life or
  health, so each segment is a row.

## The user's history by type (as data for baselines, not coaching)

- **Volume, on installed scenarios:**
  - tracking: 11,932 runs over 114 scenarios;
  - clicking: 8,258 over 77 (5,411 static, 2,832 dynamic);
  - switching: 5,051 over 39;
  - untagged: 3,449 over 57.

  Another 42,950 runs are on 1,997 scenarios that are no longer installed, so their type cannot be read.
- **Clicking, most played** (last 30 runs; time per kill is the median time between kills):

  | Scenario | Runs | Score | Accuracy | Time per kill |
  | --- | --- | --- | --- | --- |
  | VT 1w2ts Advanced S5 | 1,073 | 1,181 | 0.93 | 0.45 s |
  | VT 1w3ts Intermediate S5 | 618 | 1,348 | 0.94 | 0.39 s |
  | cA sixshot (the Flow Fix baseline) | 607 | 146 | 0.91 | 0.37 s |
  | VT 1w5ts Rasp Intermediate | 482 | 1,110 | 0.94 | 0.50 s |
  | VT 1w4ts Novice S5 | 455 | 1,470 | 0.94 | 0.37 s |
  | VT Pasu Intermediate S5 (dynamic) | 727 | 933 | 0.87 | 0.52 s |
  | VT Popcorn Intermediate S5 (dynamic) | 628 | 830 | 0.76 | 0.57 s |
  | VT Frogtagon Intermediate S5 (dynamic) | 288 | 1,215 | 0.82 | 0.39 s |

- **Tracking and switching, most played:**
  - VT Controlsphere Advanced S5: 1,483 runs.
  - VT Snake Track Advanced S5: 1,411.
  - VT Controlsphere Intermediate S5: 1,177.
  - VT ControlTS Intermediate S5: 1,034.
  - VT Controlsphere Novice S5: 792.
  - VT Raw Control Intermediate S5: 739.
- **Recent levels** (last 30 runs, as accuracy or hit share):

  | Scenario | Hit share |
  | --- | --- |
  | Controlsphere Advanced S5 | 0.52 |
  | Snake Track Advanced S5 | 0.56 |
  | Raw Control Intermediate S5 | 0.64 |
  | Ground Intermediate S5 | 0.59 |
  | Aether Intermediate S5 | 0.60 |
  | Smoothbot Advanced | 0.52 |

  Switching, with the time to kill:

  | Scenario | Hit share | Time to kill |
  | --- | --- | --- |
  | ControlTS Intermediate S5 | 0.50 | 1.11 s |
  | DriftTS Advanced S5 | 0.38 | 1.25 s |
  | DotTS Advanced S5 | 0.45 | 0.45 s |
  | Penta Bounce Intermediate S5 | 0.51 | 0.94 s |
  | EddieTS Intermediate S5 | 0.42 | 0.51 s |

  The first 30 runs of each were 0.10 to 0.23 lower. These make natural baselines, the way `cA sixshot` is for
  static.
- **The user's setup, from the stats:** 2560 × 1440, FOV 103 (Overwatch scale), 60 cm/360 at 3200 DPI, a dot
  crosshair. `Max FPS (config)` was 440 or 999 in recent runs. At 1440p, one 7-unit art pixel at 2,900 units is
  about 2.7 screen pixels, not 2 as earlier estimates assumed for 1080p.

## What this means for Flow Fix drills of every type

- **Bots need room and collision.** Moving bots walk on floors and are stopped by walls, and the Flow Fix window
  look has neither: every piece is `DefaultNoCollision`. Two ways fit the look:
  - Flying bots (`IsFlyer`, `Gravity` 0) inside an invisible `Clip` box that matches the window's target envelope.
  - A real floor and walls built as a court arena behind the window.
- **Keep the spawn area on screen.** The rule that spawn areas stay within about 46° × 26° still holds.
  `MinTargetDistance` / `MaxTargetDistance` and Clip walls are the tools for keeping a moving bot on screen.
- **Strip luck with paths.** Random strafe timing makes each run different. Waypoint paths give the same movement
  every run, as fixed rotation cycles do for the static drills.
- **Make the stats readable.** Give tracking bots timed lives, so every segment writes a row. Clicking and
  switching write rows by themselves.
- **Dynamic clicking and switching** need the same room and collision as tracking, since their bots move too. Their
  bots are closer and bigger than static targets (about 1.3 to 1.9° at about 2,000 units).
- **Static clicking** keeps working as Flow Fix does now. Installed scenarios rely on accuracy multipliers far more
  than on miss penalties, and none uses a fire delay; Flow Fix's delay drills are unusual.

## Case: the user's race scenario (1w1t Race WIP, 2026-09-25)

A "Seeker" bot on the player's team (team 1, `Untargetable`, weapon hidden) flies to the targets on the wall and
takes them with a short-range gun (`MaxHitscanRange` 100), racing the player. Fixes and findings, from test copies
made with `patch_scenario.py`:
- **The seeker drifted toward the player** whenever the player took its target first, for the 0.45 s until the next
  target respawned: with no target it kept flying "forward". An invisible `Clip` brush across the room just in
  front of the seeker's plane fixed it (confirmed). Clip blocks bots but not shots.
- **It moved very slowly.** `ForwardSpeedBias` 0.1 (with `StrafeSpeedMult` 0, so it only moves forward) and
  `TerminalVelocity` 100 held it far below its `MaxSpeed` of 1800. Setting them to 1.0 and 0 made it fast
  (confirmed).
- **Its paths curved.** The bot moves along its view, and its aim turned slowly toward each new target. The Aim
  Profile limited it: `MaxTurnAngleFromPadCenter` 75 (targets sit up to about 85° off the seeker's facing, since it
  flies just in front of the wall), `FlickFov` 30, aim errors of 15 to 40, and slow turn speeds. With 360, 360,
  errors 0 and speeds 20, plus finite acceleration (12000) and braking (24000, `BrakingFrictionFactor` 0), it
  still curved and overshot its targets: the bot carries momentum, so it drifts when it changes direction and does
  not stop in time. Now on trial: the original instant start and stop (100000) with the aim speeds at 1000, for
  straight constant-speed lines.
- **A "second crosshair" instead of a flying body** (`1w1t Race WIP Eye`):
  - **The setup.** The seeker stands still, hidden, at the player's exact spawn point, with the player's body size
    and spawn offset. Its laser is on (`ShowLaser`, `LaserAlpha` 1), its gun reaches the whole wall, and its
    tracers are off.
  - **Confirmed:** a laser that starts at the player's eye shows as a clean dot on the wall.
  - **The catch with aim assist.** With its gun's aim assist on (`AAMode` 2), the bot never turned: the laser stayed
    fixed at the centre, and targets died almost at once. Aim assist lands the bot's hits without it aiming.
  - **Aim assist off (`AAMode` 0): the bot does aim.** Its laser pointed at a target. But while the two bodies
    overlapped, nothing got through: the player's shots killed nothing, the seeker took no targets, and its laser
    started above and to the side of the player's eye (probably pushed out of the overlap at spawn). A laser that
    starts off the eye shows as a long line, not a dot.
  - **Dropped:** the user wants the seeker on the wall with the targets, flying to them, not beside the player.
- **Back to the flying seeker** (on trial): the original instant start and stop, the Clip wall, full speed, an aim
  that snaps to the next target with no reaction delay (`MinReactionTime`/`MaxReactionTime` 0.0001, turn speeds
  1000, no aim error). The seeker stops 90 units from its target (`MinTargetDistance` 90, inside the gun's 100),
  waits its 0.3 to 0.6 s shoot delay and moves on. The reaction delay had kept it flying for 0.3 to 0.4 s after
  each change of target at full speed, which is likely what overshot.
- **Measured from the user's replay** (120 fps, the seeker tracked by its colour):
  - **Movement:** mostly straight segments at a steady 40 to 50°/s on screen, after a start ramp of about 0.1 s.
  - **Arrival:** a small hook and 0.1 to 0.2 s of jitter between 0 and 30°/s. Near the target, the direction to it
    swings fast, and the 90-unit stop zone switches on and off.
  - **Stop:** no clean pause before moving on.
  - **A resampling trap:** resampling the 120 fps video to 60 fps made the speed look like it pulsed every 3 frames.
    At the native rate it is smooth.
- **Limit:** KovaaK's bots have no "move straight to a point and stop" command. They move along their view and brake
  only when they have no input, so an easing start and stop and a perfectly straight path pull against each other.

## Case: the Startled redesign of Lingering (2026-09-25, in test)

The user wants Lingering to fix lingering rather than practise it. Each target takes two hits and dashes away on
the first one. The user's wishes:
- two targets;
- a head that takes hits but no damage (`HeadshotMultiplier` 0 on the weapon), pointing where the dash will go;
- no movement before the first hit, and no change of direction during the dash;
- a short dash: 1350 units/s for 0.35 s, about 470 units;
- no knockback (weapon `KnockbackFactor` and `KnockbackFactorAir` 0).

Findings from the test copies:
- **Flying bots clamp to their flight speed.** A flyer (`IsFlyer`) bobbed up and down from spawn, because its dodge
  profile toggles up and down at the default `FlightVelocityUp`/`Down` of 800. With those set to 0, its dash
  vanished too: the dash is clamped to the flight speed.
- **`MainBBHeadOffset` moves the head along the body's up axis.** A negative offset (-144) hid the head completely.
- **A rolled spawn volume turns its bots (confirmed).** The volume's `rotation` is roll, pitch, yaw. A roll turns
  each bot it spawns about the player's line of sight, and the head turns with the body. So the head can point
  any way along the wall. `build.py` takes a `roll` per spawn volume.
- **A rolled volume turns its box too.** Wide volumes rolled by 90° or 45° spawned targets outside the window.
  Keep each rolled box inside the spawn area: swap the sides at 90°, and use diamonds (squares at 45°) inside
  small cells for the diagonals. `build.volume_extent`, the Clip box and `check_scene.py` take the roll into account.
- **Movement stays on the world axes.** The roll does not turn the dash:
  - A dodge strafe goes left or right, and a flyer's dodge goes up or down, whatever the roll.
  - The dash ability's `UpVelocity` pushes straight up the screen. A negative value pushes down.
- **The damage-triggered dash ability fires once ability use is allowed.** An earlier copy set the bot's
  `UseAbilityFrequency` to 0 and the dash never fired. With 1.0, as in DomiSphere, it fires on the first hit (with
  `NoAiming` true, top speed 0, gravity 0, not flying). `EndVelocityFactor` 0 stops it dead at the end.
- **One bot type per direction.** Since movement ignores the roll, each head direction needs its own type (8 types,
  45° apart). Each type has spawn volumes rolled to match and `PermittedCharacterProfiles` set to it. Its volumes
  cover the whole spawn area. Two slots draw types from a random Bot Rotation Profile. Each type builds its dash
  from the world axes: a dodge strafe for the sideways part and `UpVelocity` for the up or down part.
- **Open: the sideways part.** A dodge strafe on a floating non-flyer (gravity 0) did not move it. The next copy
  tried two fixes, one on each side: the same bot with `MaxAirSpeed` raised from 0, and a flyer with
  `IsFlyUpOnJumpAndCrouch` true, so its dodge could not fly it up or down. The user reported that it did not
  work. Next session: find which part failed.
- **Knockback is no help here:** a hit pushes the target along the shot's direction, which is into the wall. Only
  the flat vertical knockback could vary, and it is set on the weapon, so it is the same for every bot.

## Unknowns to test in game (probe scenarios)

- The units and feel of `MaxSpeed`, `Acceleration`, `Friction` and `BrakingDeceleration`, and how they combine at
  a reversal. Is there a coast, or an instant turn?
- What `ForwardTimeMult`, `BackTimeMult`, `LeftStrafeTimeMult` and `RightStrafeTimeMult` do. Tiny values such as
  0.00001 seem to switch a direction off.
- `TargetStrafeOverride` (`Mimic`, `Oppose`): whether it copies the player's strafes, which only matters if the
  player moves.
- The exact meaning of `WaypointLogic` values and `WaypointTurnRate`, and how `BotPauseTime` works on a path.
- The role of the Controlsphere helper bots and the "Wall Repellent" map.
- `LOSReact*` and `DamageReaction*` details.
- **`BlockedMovementPercent` and `BlockedMovementReactionMin/Max`** (confirmed 2026-09-25). Wall-bounce bots use strafes
  that never time out (`MinLRTimeChange` 1000) and turn back only when a wall blocks them.
  - **Tested in game: a higher value reacts sooner.** Pasu Track Extrasmooth TE uses 0.95 with a 0.01 to 0.02 s
    reaction, and the user saw its bot ride the side walls sometimes. A copy set to 0.1 (with a 0.15 to 0.2 s
    reaction) rode the walls even more.
  - **The reading that fits:** the bot counts as blocked when it moves slower than this share of its top speed;
    0.95 means below 95%. The speed seems to include vertical speed. That bot jumps at 1200 against a top speed of
    1000, so while it rises or falls fast along a wall it still moves faster than 95% and never counts as blocked.
  - **Confirmed by the fix:** `Pasu Track Extrasmooth TE Wall Fix` (made with `patch_scenario.py`) keeps 0.95 and
    the fast reaction. It jumps at 900 with gravity 0.197 instead of 1200 and 0.35: the same height, but it never
    moves faster than 95% of its top speed vertically. It also drops the author's random 0 to 0.25 s pause at each
    turn (`StrafeSwapMaxPause`). The user saw no more wall riding (2026-09-25).
  - **Rule for wall-bounce bots:** keep the jump speed below `BlockedMovementPercent` × `MaxSpeed`. Raise the jump
    height with lower gravity, not with a faster jump: the height is jump speed² / (2 × 980 × `Gravity`).
  - **Physical bounce.** The Character Profile's `BounceOffWalls` true makes the bot bounce off walls. ClockTrack
    and TSK DVD Tracking use it with the same movement as Pasu (top speed 1000, acceleration 15000, air control 1,
    strafes that never time out). ClockTrack keeps `BlockedMovementPercent` 0.95; DVD sets it to 0 and relies on
    the bounce alone. Pasu Track Extrasmooth TE has it off. `Pasu Track Extrasmooth TE Bounce Fix` turns it on and
    keeps the original jumps (1200, gravity 0.35), to test whether that stops the riding without slowing the
    jumps. The user saw it "float on the floor" instead: with gravity 0.35 it keeps landing, and the bounce seems
    to apply to the floor too. ClockTrack and DVD use gravity 0.1, so their bots rarely touch it. Retired.
  - **Why the original speeds conflict.** If the blocked test uses the bot's total speed, a bot that runs at 1000
    and jumps at 1200 cannot be caught at a wall mid-jump by any threshold. Catching 1200 at a wall would also
    catch 1000 in normal running, and the bot would turn all the time.
  - **Timer backup (confirmed 2026-09-25).** `Pasu Track Extrasmooth TE Timer Fix` keeps the original speeds and
    jumps and sets the strafe time to 3.05 s, about the time the bot takes to cross the room (2,973 units at 1000).
    A slide along a wall then ends within a moment by the timer. The user saw no riding and no mid-room turns, so
    the strafe timer restarts at every turn, wall turns included.
  - **Which fix for which map.** The slower jump (jump speed under 95% of top speed) works in any room with no
    tuning. The timer keeps the original jumps, but its time must match the room: the strafe time is (the inner
    width minus the bot's diameter) / top speed, plus about 0.07 s for the turn. It must be recomputed for every
    width or speed change, and anything that slows the bot's crossing (forward-back drift, other bots) makes it
    turn early.
  - **Installed default:** 0.5 with 0.125 to 0.2 s (248 dodge profiles).
- Whether `SpawnVolume` and `BlockedSpawnRadius` behave for moving bots as they do for static targets.

## Case: the Overflick ring (Blast Test, 2026-09-26)

The user wanted an Overflick drill where overflicking is impossible or not worth it. A normal click cannot show the
game an overflick that is corrected before the click, so the drill uses a held stream (the Poke-Drill) and penalty
bots round each target. The stream traces the crosshair's path; when it stays on a penalty bot, that bot blasts the
player and costs a point. Mechanics are in `mechanics.md` ("Blast penalty", "Overflick disc").
- **Scoring:** a target kill is worth 2 (`ScorePerKill`, 80 ms of contact), a blast costs 1
  (`ScoreLossPerDamageTaken` 0.1, 10 damage), misses are free, and a blast needs about 5 bullets in a row (the
  penalty bot's 100 HP, 5/s regen and `AIMaxSelfHealth` 99), so a fast pass on the way in is free and an overflick's
  turn is not. Each penalty bot blasts at most once per 0.5 s (user: one mistake, one point).
- **What failed on the way:**
  - blasts with nobody shooting (the normal-use switches on);
  - no blast at all (damage reaction only);
  - chain reactions (team 0);
  - flat and tall Cuboids (drawn wrong);
  - rings of small bots with gaps (bots need about 4 radii between centres);
  - `DisableCharacterCollision` (stopped the targets spawning);
  - a crosshair-blocked random spot (the spawn waits).
- **What worked:** one big sphere behind each target (a disc), placed by perspective and the full-height rule. The
  user then wanted a gap between target and penalty zone, and a target visible under forced colours. That gave a
  ring of 8 spheres, spread over 4 depths 130 units apart so no two are within 4 radii, with the target in front of
  them all. The build checks every pair.
- **Still open:** nothing makes holding the button necessary. A player can let go during the flick and press on
  arrival, so an overflick with the button up costs only time. No spin-up exists (`DelayBeforeShot` on a full-auto
  gun gives one shot per press). The last versions (2 targets at once, corners only) were not confirmed in game.

## Case: phases in one run (Phase Test, 2026-09-26)

The user asked for a 10 s scenario: 5 s clicking, then 5 s tracking, each with its own weapon.
- **Phases:** a Teleporter under the player's spawn (`Target` = a Waypoint's name, `TeleportDelay` 5) moves the
  player to a second room at 5 s. The player kept facing the same way. shimcluster uses the same object (15 s, 4
  rooms).
- **Second weapon:** nothing swaps the player's weapon by itself. Taking damage, ability triggers, running out of
  ammo and bot weapon randomising were all checked. What works: the tracking beam is a Weapon Ability
  (`AbilityProfileNames` `Track.abilwep;;;`), fired by holding the Ability 1 key, while mouse 1 stays the clicking
  gun.
- **Keeping each gun to its phase:** `BlockAbilityOnStartDuration`, a spawn without charges and the beam's
  `DelayAfterSpawn` all failed to lock the beam in room 1. Two things worked:
  - **Range:** the beam's `MaxHitscanRange` 6000 cannot reach room 1's targets (9,608 away); the tracking bot stands
    closer (3,780), scaled down in size and speed to look the same.
  - **Score:** the clicking gun does 0.001 damage, so it scores nothing on the tracking bot. Clicks score by kill,
    tracking by damage.
- **Tracking bot:** a flyer strafes only with `AirControl` above 0 (the base has 0).
- **First scores:** 5-10 points clicking and 2-6 tracking in the user's runs. The balance is not decided.

## The Workshop survey (2026-09-26)

`python survey_scenarios.py workshop` reads the Steam Workshop folder
(`steamapps\workshop\content\824270`, one folder per item) into `test_out/survey_workshop.json`: 1,422 scenarios, 1,245
of them not among the 388 installed ones. Each entry carries its `workshop_id`. What it adds:
- **Player abilities are used:** melee in 15 scenarios, movement in 3, weapon in 1, sprint in 1. mccoyfrozentrack gives
  the player all three kinds at once: a Rush dash (movement), a Stun Gren (weapon ability) and a Melee.
- **Teleporters in 15 scenarios.** TP Track the Floating apex moves the player between 3 rooms (LEFT, RIGHT, MID)
  with `TeleportDelay` 10: a rotation of positions every 10 s. Others use a delay of 0 as plain doors.
- **Very short runs:** 25 scenarios have `Timelimit` of 20 s or less, several of 5 s (Close Long Strafes 5s,
  shimPressure 5s).
- **Penalties through damage taken:** 34 use `ScoreLossPerDamageTaken`. The pressure family (fuglaaPressure,
  darkPressure, Pressure Aiming) gives its bots guns (`UseWeapons` true, aiming on) that shoot the player, 50 points
  per point of damage, so a target left alive costs score. shimPressure 5s sends bots rushing at the player (a
  movement ability of 10,000) with a melee hurtbox: "kill before they reach you".
- **Bot counts:** the most in one Workshop scenario is 36 (1wall9000sphere); most "9000 targets" scenarios use about
  30 that respawn.
- **No charge weapons,** and `DelayBeforeShot` appears mostly on the self-destruct bots' weapons (explode250ms to
  500ms).

### Mechanics new to this project (Workshop study, 2026-09-26)

Found by listing every setting whose value is rare (2-25 of 1,422 Workshop scenarios) against its usual value.
- **Adaptive difficulty ("Adapt" scenarios, 7).** `IsTargetSizeActive` (or `IsTimeDilationActive` for speed) with
  `PerformanceMetricType` (`Accuracy` or `KillsPerSecond`), `PerformanceTarget`, `AdjustmentInterval` (s) and
  `AdjustmentRate`, bounded by `Min/MaxTargetSizeMultiplier` (or speed). The game resizes the targets every interval
  to hold the player at the target: PeekShot Valorant Adapt aims at 2.1 kills per second every 5 s; Avasive Micro
  Reflex Adapt shrinks targets down to half size by accuracy. The stats record `Avg Target Scale`.
  Confirmed in Flow Fix 2 Adaptive Test (2026-09-26, 3 runs, accuracy target 0.9, 5% every 2 s, start 1x, floor
  0.4x): accuracy stayed at 86-92%, Avg Target Scale came out 0.54-0.57, and kill times rose through each run
  (0.43 s to 0.55 s) as the targets shrank. Starting at 1x spent half the run shrinking, so the average mixed that
  descent with the player's level; v2 starts at 0.55x with a 0.25x floor, so the average tracks the level.
- **Game speed.** `Timescale` runs the whole scenario slower or faster: 0.7 in the Pasu Raspberry family, 1.4 in
  Reflex Flick - Mini, 2.0 in 1w4t Pressure Revosect and 16 others. `TimeDilationBaseMultiplier` scales only the
  targets (0.66 to 1.4).
- **Finish lines.** `EndChallengeAfterKills` ends the run at N kills: VT Air Advanced after 5 bots; Apostrophe Flick
  Survival starts with 5 s, adds 0.3 s per kill and is won at 250 kills. `EndChallengeAfterDamage` does the same by
  damage.
- **Accuracy in the score.** `ScoreMultAccuracy` (with `MultSqrtAcc` for the square root) multiplies the score by
  accuracy, in 135 Workshop scenarios. `ScoreMultKillEfficiency` and `ScoreMultDamageEfficiency` exist too;
  `ScoreLossPerReload` charges per reload (25 in the REVENGE scenarios).
- **A second weapon on every shot.** A weapon's `AlsoShoot` names another weapon profile fired with each shot:
  Ascended Tracking fires an effect helper, the Revolving scenarios a "Gain Velocity For Stuck" helper that pushes
  stuck bots.
- **Lifetimes without HP.** A dodge profile's `LOSReactKillBot` true with `LOSReactKillBotTimerMin/Max` kills the bot
  that long after it sees the player (0.7 s in Avasive Micro Reflex Adapt), which leaves the HP free for values.
- **Phases by kill count.** 1 wall no bitches (5 phases of 45 to 65 kills) moves the player between rooms with
  Teleporters driven by a fixed rotation of helper bots (tp-helper-1, tp-to-room-2, tp-helper-2, tp-to-room-3).
  How a helper triggers the move is not worked out yet.
- **Also seen:** `SpawnGroup` numbers on bot profiles (LineClick: 4 groups); `Pierces` (bullets pass through
  targets); `DamageFalloffStart/StopDistance` (damage by distance); bot abilities with a negative `HealthRestore`
  (a dodge costs the bot health, Reactive Clicking Hard); player survival settings (`PlayerMaxLives` 1,
  `HealthRegainedonkill`, `LifeStealPercent`); `ScorePerTime`; movement scoring (`MBS*`, `DistanceScoreCondition`
  LooseMirror and LooseAntiMirror).

## Case: tracking along a drawn path (2026-09-27)

The user asked for tracking that really punishes overcorrection and prediction, "similar in philosophy" to Aether
Bot 2 and Silo "but better", then for the path to be carved on the wall behind the bot ("in-game hints").
- **React Track** (a dodge bot, beam scoring +1 a tick and -1.5 a miss): v1 was "easy and learnable" (mostly side
  to side); v2 changed direction too fast and never moved up and down. The user's aim: hard, but 100% possible when
  fully focused. A player reacts about 0.15 s late at best, so a bot that changes speed at `a` deg/s^2 pulls
  `a * 0.15^2 / 2` away: 80 deg/s^2 keeps that under 1 deg. Up and down needs jump and crouch (mechanics.md).
- **Split Track** (the user's idea): a big bot in front hides a small one on the same path; they part and meet
  again, and the small one scores 3 times as much (all head). Waypoint paths with both detours the same length kept
  them together exactly. The user found mirrored loops "tripy more than hard", and tracked the small bot only about
  1.3 s of the 11-13 s it was apart.
- **Drawn paths.** مستحيل ("impossible", Arabic Typesetting, kashida): a thinned letter line wobbles at pixel scale,
  the teeth force reversals, and smoothing them away cost legibility. One-line art (a fish, two Vecteezy world
  maps): the line touches itself, so the route doubles back. A generated island coast (a simple closed loop) worked
  "perfectly".
- **Continents from Natural Earth** (public domain, 1:110m countries,
  `github.com/nvkelso/natural-earth-vector`, file `geojson/ne_110m_admin_0_countries.geojson`): each continent's
  countries filled on a grid, the largest island kept, lakes filled (channels cut first at the Bosporus, the Danish
  straits and Hormuz keep those seas open), a light blur, the coast traced as one loop, and only its sharp spots
  eased. Sinai is cut at Suez and Panama at the Darien, so no two continents touch.
- **Phases:** one continent per panel, then per classroom, with teleport chains (mechanics.md). Too slow to switch
  and the next bot off the crosshair. **The Lecture Hall Track Test** (installed as `World Map`, the user's name, no prefix) puts the whole map on one wide
  chalkboard in one room: the bot laps each continent and flies a dashed route to the next. Antarctica is a strip
  along the bottom, as on the user's reference map. Script `_lecture_hall_test.py` (ignored by git).
- **Tracing each coast once.** v5 entered each continent at its point nearest the last one, went all the way round,
  then on round to its point nearest the next one, so it traced 160 of its 713 deg twice (the user: "we're tracing
  the same spots twice"). A coast traced in full from an entry to a different exit must repeat the stretch between
  them, so v6 laps each coast the way that repeats the shorter stretch and chooses the order, entries and exits
  together for the shortest hops plus repeats. It searches every order (the best by nearest gaps first), exactly over
  ports every 1 deg, then refines each port to 0.05 deg. Every straight hop keeps 0.3 deg from all coasts. The best
  tour is North America, South America, Antarctica, Australia, Africa, Eurasia: 82 deg of routes, 16 deg repeated,
  607 deg in all (133 s at 5 deg/s). One port per continent (no repeats at all) had no clear tour: a continent's two
  neighbours lie on opposite sides, so both routes would have to hug its coast.
- **Names inside the outlines (v7).** v6 put each name at the average of its coast points, so South America's ran over
  its coast. v7 puts each name as close as it can to its continent's centre of area (Europe and Asia within 3 deg of
  a set point, as they share one outline), at the widest clearance from every coast that fits there: 0.9 deg, else
  0.75, 0.6, 0.45 or 0.3. Lines stay 0.9 deg tall; a two-word name may take two lines. Result: every name 0.9 deg
  clear except Europe and Antarctica (0.6); South America on two lines.
