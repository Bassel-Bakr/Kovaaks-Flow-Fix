# Flow Fix: which one to play when

Thirteen static clicking scenarios built on cA sixshot dense, with the same room, FOV and gun.
Targets are black. Each one targets one problem from the weakness targeted static flowchart, and
Flow Fix Check is an all-in-one check. The playlist "Flow Fix" runs them in the order below, with
Check last.

## Start from what you see, not from a score

Watch a replay, or pay attention during a few runs of cA sixshot. Find the line below that describes
your crosshair, and play that scenario.

| What your crosshair does | Play |
| --- | --- |
| Flies past the target and snaps back. Your arm feels tight. | Overflick, then Lingering |
| Lands on the target, then hangs there before moving on. | Lingering |
| Fine on short flicks, loses control on wide ones. | Wide Control |
| Starts slow and drags to the target. Your arm feels loose. | Slow Start, then Hesitation |
| Waits to be sure before clicking, so every kill takes a beat longer. | Hesitation |
| Starts fast, then crawls the last part of the way. | Early Braking |
| Clicks before it has stopped, and the miss lands right next to the target. | Early Click |
| Lands "close enough" and clicks without a final small correction. | Micro Adjust |
| Rhythm is good on close targets and falls apart after a wide flick. | Pacing Drop |
| Jumps around a cluster in no real order, or wastes a wide flick on a far target. | Pathing |
| One miss wrecks the next several shots. | Recovery |
| Clean, but you cannot get faster. | Speed Build |
| You are not sure, or you want a daily check. | Check |

**Tense or loose?** Both can look like a bad flick. A tense arm sails past the target, and your
hand tends to ache after a long session. A loose arm arrives late and drags. The first is Overflick
and Lingering. The second is Slow Start and Hesitation, not "tense up more".

**Delayed shots (Overflick and Hesitation).** In both, the shot fires a moment after you click,
wherever the crosshair is by then. In Overflick the delay is 50 ms: stop on the target, click, and
hold still. In Hesitation it is 300 ms, and each target lasts only 0.7 s: click first, then flick, and be on
the target when it fires. Aiming first and then clicking is too late.
Use the mouse button, as you would in a game. Clicking with a keyboard key leaves the aiming hand
free, so its scores are not comparable.

**Every target stays on screen.** No scenario spawns a target so far from another that you cannot
see it while aiming at the first, at 103 FOV on a 16:9 screen.

## Using Check

Check has three kinds of target:

- Black spheres in the middle.
- A small black sphere on the far left or right.
- A dark orange cube in the ring around the middle, which vanishes after 1.5 seconds. The shape
  shows it apart even if you force your own enemy colour.

Middle targets are worth 1 point. The small side target is worth 1.5, because a wide flick plus a
correction takes about 1.5 times as long, so both pay the same per second. The cube is worth up to
4: it drains from 4 to 0 over its 1.5 second life. Reaching it at 0.8 seconds pays about 1.9 and at
0.5 seconds about 2.7, so chasing cubes fast pays more than anything else. A miss costs half a point.

You cannot skip a kind of target: a small target you ignore stays up and waits for you. Notice which
kind costs you most:

- Middle targets: pacing. Go to Pacing Drop, Recovery or Speed Build.
- The small side target: wide control and micro adjustment. Go to Wide Control or Micro Adjust.
- The dark orange cube: slow starts. Go to Slow Start or Hesitation.

Do not edit Check. It is only useful as a check if it stays the same.

## A session

1. One run of Check, or of cA sixshot, to see what shows up today.
2. Three to five runs of the one scenario that matches.
3. One more run of Check at the end. Look at how the runs felt, not only at the score.

You do not need the whole playlist every day. Play through all of it now and then to spot
problems you had not noticed.

## When to move on

Stop drilling a problem once it stops showing up in Check and in cA sixshot. If you keep drilling a
fixed problem for another month, you are practising something you no longer need.

When a scenario gets easy, change one setting by a small step. Make a copy in the editor first and
change the copy, so the original and its scores stay as they are.

| Scenario | Change first |
| --- | --- |
| Overflick | Fire delay: DelayBeforeShot 0.05 to 0.07 (in the BB Gun steady weapon profile), or target radius 72 to 65 |
| Lingering | Dwell: MaxHealth 1.8 (80 ms) to 1.4 (60 ms) for speed, or 2.2 (100 ms) if landings are still sloppy |
| Wide Control | Target radius 40 to 35 |
| Slow Start | Lifetime: HealthRegenPerSec -2.0 (1 s) to -2.5 (0.8 s). Keep MaxHealth at 2, the most a target is worth. |
| Hesitation | Target lifetime: HealthRegenPerSec -1.4286 (0.7 s) to -1.667 (0.6 s). Or the fire delay: DelayBeforeShot 0.3 to 0.25 (in the BB Gun committed weapon profile). |
| Early Braking | Target radius 100 to 85. Target spacing is 400 (was 1000) so short flicks mix with wide ones. |
| Early Click | Target radius 95 to 80. Keep the miss penalty. |
| Micro Adjust | Target radius 32 to 28 |
| Pacing Drop | Small target radius 30 to 26 |
| Pathing | Target radius 40 to 35, or clusters further apart. The 30 targets sit in four clusters near the corners. |
| Recovery | Lifetime: HealthRegenPerSec -0.333 (3 s) to -0.5 (2 s) |
| Speed Build | TimeRefilledByKill 0.27 to 0.25. The rate at which the clock never runs out goes from 3.7 to 4 kills a second. |
| Check | Nothing. Leave it alone. |

Target radius lives in the target's Character Profile, as MainBBRadius, with MainBBHeight set to
twice the radius. HealthRegenPerSec and MaxHealth are in the same profile. TimeRefilledByKill is on
the main scenario page.

Speed Build is tuned to your cA sixshot history: a median of 145 over 607 runs, about 2.4 kills a
second. At that pace a run lasts about a minute. A run at your best pace, 161, lasts about 73 s.

## Check these in game

Some of the mechanics come from how other scenarios use them, not from documentation:

- **Zones in Check:** the cube should appear only in the ring around the middle, and the small
  target only on the far left or right.
- **Clock (Speed Build):** each kill should add 0.27 s.
- **Respawn delay (Pathing):** a killed spot should stay empty for a moment before a new target
  appears.

Already confirmed in game: delayed shots use the aim at the moment they fire (Overflick,
Hesitation), the pokeball dwell (Lingering), skipped small targets waiting in the rotation (Pacing
Drop, Check), timed targets scoring nothing when they expire, and spawn zones per target type.
