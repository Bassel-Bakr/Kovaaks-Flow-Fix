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
- **Two map formats.** 200 scenarios hold a JSON map, like ours. 186 hold an older text format that starts with
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

## Unknowns to test in game (probe scenarios)

- The units and feel of `MaxSpeed`, `Acceleration`, `Friction` and `BrakingDeceleration`, and how they combine at
  a reversal. Is there a coast, or an instant turn?
- What `ForwardTimeMult`, `BackTimeMult`, `LeftStrafeTimeMult` and `RightStrafeTimeMult` do. Tiny values such as
  0.00001 seem to switch a direction off.
- `TargetStrafeOverride` (`Mimic`, `Oppose`): whether it copies the player's strafes, which only matters if the
  player moves.
- The exact meaning of `WaypointLogic` values and `WaypointTurnRate`, and how `BotPauseTime` works on a path.
- The role of the Controlsphere helper bots and the "Wall Repellent" map.
- `LOSReact*`, `BlockedMovement*` and `DamageReaction*` details.
- Whether `SpawnVolume` and `BlockedSpawnRadius` behave for moving bots as they do for static targets.
