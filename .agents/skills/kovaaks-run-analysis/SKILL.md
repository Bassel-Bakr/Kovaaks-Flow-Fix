---
name: kovaaks-run-analysis
description: Read the user's KovaaK's run stats (CSV files in FPSAimTrainer/stats) and judge whether a scenario does its job — kill-time distributions, misses, per-target-type timing and value, expiries, comparison to the user's cA sixshot baseline. Use this whenever the user says they played a scenario ("played 08", "played Pathing 3 times", "check the stats"), asks how a scenario is working, or wants values tuned from real play, even if they don't mention stats or CSVs.
---

# KovaaK's run analysis

The user plays and then says "played X". Your job is to test the scenario, not to coach the player. Use
the data to answer three questions:
- Does the scenario force its demand?
- Does the score pay for the right behaviour?
- Is there luck or a shortcut?

Skip player advice ("your weakness is…, go play…") unless the user asks for it. They explicitly wanted
the scenarios improved first.

## Data

- **Location:** `C:\Program Files (x86)\Steam\steamapps\common\FPSAimTrainer\FPSAimTrainer\stats\`,
  more than 70k files. Always use a Python glob; `ls -la` there takes minutes.
- **File name:** `<Scenario Name> - Challenge - YYYY.MM.DD-HH.MM.SS Stats.csv`. The timestamp is when the
  run finished.
- **Per-kill rows:** `Kill #, Timestamp, Bot, Weapon, TTK, Shots, Hits, Accuracy, Damage Done, ...`. Misses
  before a kill = Shots − Hits. `Bot` is the Bot Profile name, which separates target types.
- **Summary rows:** `Key:,Value` lines such as `Kills:`, `Score:`, `Miss Count:`, `Challenge Start:`,
  `Damage Done:`. Also `Hash:` (changes whenever the scenario file changes, so it identifies the build),
  `Avg FPS:` and `Max FPS (config):` (the in-play frame rate and the user's limit, 1000 since 2026-09-24).
- **`TTK` is 0** for one-shot kills. Use the time between kills (from `Challenge Start:` for the first) instead.
- **No file without a score (2026-09-27).** Only challenge runs write a stats file, and only when they score: 16
  challenge runs of the FPS probes that scored 0 wrote none (the log still records "Challenge completed", and a
  small `performances/*.perf` file is written, but it holds no frame data). A probe that must be read from the stats
  needs a score, for example `ScorePerTime` or a target to hold fire on. Freeplay writes no stats file.
- **`OverShots` is the shots fired in the scenario's `OvershotProtectionTimer` (0.25 s in cA sixshot dense) after a kill** (the Overshots and Hitbox probes, 2026-09-27). With a beam
  ticking every 0.01 s it tops out at 25 however long the player keeps firing (bots that never respawned read 25 too),
  and a player who lets go 0.04 s after the kill gets 4. So it measures stopping fire after a kill, not overshooting
  the target; a weapon firing faster or with more pellets per shot reads higher (the survey saw up to 250).
  `Total Overshots` is its sum. `Fight Time` is the sum of the kill times.
- **Kill rows count since the previous kill.** A kill row's `Shots` and `Hits` include every shot since the previous
  kill, on any bot (the Hitbox probe).

## Tools in the project

```bash
python stats_basic.py "Early Braking" "cA sixshot"   # per-run score, misses, kill-time p10/median/p90, spread (CV)
python stats_varying_sizes.py                        # Pacing Drop: per-size time, the time after a small target
python stats_all_in_one.py                           # Check: per-type time, cube value and hit timing, expiries
python stats_recovery.py                             # Recovery: the kill after a miss, miss after miss, by build hash
python stats_slow_start.py                           # Slow Start: value per kill, age at kill, waiting vs fresh target
```

For other questions, write a short inline script with `parse` and `secs` from `stats_basic.py`. Group runs by
`Hash:` so an older build never mixes with the current one.

Scenarios are matched by name, and the scripts also read runs saved under the old numbered names.

## Method

1. **Keep runs from one build together.** Check the install time (the installed `.sce` file's modified
   time) and split the runs at it. Runs from an earlier build are a different scenario. Also ask which
   input method was used when a delayed shot is involved: keyboard and mouse clicks aren't comparable.

   **The spawn-size fix is one known split.** It happened on 2026-09-23 at about 02:30 local time
   (2026-09-22 23:32 UTC). Before it, `gen_specs.py` tiled spawn areas with scale = step / 100. That made
   each tile twice the intended size, so neighbouring tiles overlapped. Each tiled spawn area reached about
   half a tile past its designed edge on every side. The user saw targets spawn outside the spawn area, some
   of them on the arena frame. The fix (scale = step / 200) rebuilt all 13 scenarios. Each tiled spawn
   area shrank by about half a tile on each side. After the fix, the user confirmed that no more targets
   spawned on the frame. Runs played before the fix used larger spawn areas, so do not pool them with
   later runs. Speed Build uses the base grid of `cA sixshot dense`, not tiles, so the fix did not change
   its spawn area.
2. **Compare with the baseline.** Use the user's last ~30 `cA sixshot` runs. Their current baseline is
   about 146.5 score, 0.37 s median per kill, a kill-time spread (CV) of 0.33-0.34 and about 37% of kills under
   0.35 s.
3. **Read the right metric for the demand:**

   | Demand | Metric |
   | --- | --- |
   | Varying flick length | Kill-time spread (CV) and p10; if they match sixshot, the drill isn't varied |
   | Pacing disruption | The time for the kill right after a hard target, compared with after an easy one |
   | Stopping or landing (pokeball) | Hits per kill against the minimum (MaxHealth/0.2); the share of clean landings |
   | Fast start with a timed target | Hit time = L × (1 − value/H), readable in 0.1 s steps; expiries ≈ (slots × run length − total hit time) / L |
   | Target value balance | Points per second per type = value / median time per kill of that type |
   | Luck | The spread of the type mix per run; with fixed cycles it should match the design exactly |
   | Deadline with one target (Hesitation) | Targets caught against expired (an interval of n × lifetime + t means n expiries), time from appearing to kill, misses |
   | Route through clusters (Pathing) | Share of kills under 0.3 s (inside a cluster) and over 0.5 s (between clusters), spread above sixshot's 0.34 |
   | Time bank (Speed Build) | Run length against Timelimit + refill × kills, and kills per second; the score amplifies pace |
   | Recovery after a miss | The kill after a missed kill against after a clean one, and miss after miss against the base rate, next to sixshot's |
   | Draining value (HP as score) | Whether score varies more than kills; if score is just a fixed fraction of kills, the value adds nothing |
   | Frame rate in play | `Avg FPS` against `Max FPS (config)` |

4. **Say the verdict plainly:** validated, weak (plays like sixshot), broken, noisy, or needs more runs.
   One run is a hint, not a verdict.
5. **Propose a fix only when the data shows a problem.** Name the single change, what it should move in
   the stats, and wait for a yes. The kovaaks-scenario-design and flowfix-change skills cover how.

6. **Record the verdict** in `docs/scenarios.md` (the scenario's Evidence line and the table at the top) and in the
   notes your agent keeps, if any.

## Report

Lead with the verdict. Show a small table (runs and key metrics against the baseline), then say what the
numbers mean for the scenario, then give one proposal if there is one. Keep it short.
