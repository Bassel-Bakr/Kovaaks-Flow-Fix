# Flow Fix documentation

| Page | What it covers |
| --- | --- |
| [scenarios.md](scenarios.md) | Every scenario's design: the problem it trains, its setup and scoring, why each value is what it is, the calibration data and the verdict. Also the design rules learned. |
| [courtyard/](courtyard/) | The courtyard design record: the concept renders, the chosen design's player view and plan, and the design workflow's full result (`workflow_result.json`). |
| [look.md](look.md) | The shared look: the Egyptian window, its text and art, the palace courtyard, the palette, the frame-rate cost and how it is built. |
| [future.md](future.md) | Suggestions for future changes: calibration still to do, scenario and look ideas, code and tooling. |
| [`../.agents/skills/kovaaks-scenario-design/references/mechanics.md`](../.agents/skills/kovaaks-scenario-design/references/mechanics.md) | Confirmed KovaaK's mechanics: the .sce format, targets, scoring, geometry, rotation, custom meshes, performance, crash recovery. |
| [`../.agents/skills/kovaaks-scenario-design/references/decoration.md`](../.agents/skills/kovaaks-scenario-design/references/decoration.md) | The full decoration record for the wiki: materials, themes, props, brushes, custom meshes, the art pipeline, the Egypt look and courtyard in detail, the text, the history and the research sources. |
| [`../AGENTS.md`](../AGENTS.md) | The working guide: files, commands, the user's preferences, safety rules and open items. |
| [`../Flow Fix guide.md`](../Flow%20Fix%20guide.md) | The player-facing guide, installed next to the scenarios: which scenario to play for which symptom. |

## The loop

1. Change a scenario in `gen_specs.py` (with a comment on why and the evidence), or the look in `egypt.py`.
2. Build and check: `python gen_specs.py && python build.py specs.json out`, then `python check_view.py` and
   `python check_scene.py out`.
3. Try map-structure changes as a single test scenario first.
4. Back up the installed files into `retired/`, then `python install.py --dry-run` and `python install.py`.
5. Update `Flow Fix guide.md`, these pages and the memory.
6. After the user plays, read the stats (the `stats_*.py` scripts) and judge the scenario, not the player.
