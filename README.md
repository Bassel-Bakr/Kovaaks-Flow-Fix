# Flow Fix

KovaaK's static clicking scenarios built from the weakness targeted static flowchart
(`D:\Projects\aim\docs\articles\weakness-targeted-static-flowchart.md`): one scenario per problem plus an all-in-one
check, all based on cA sixshot dense, in a shared ancient Egyptian look (a stone window in a palace courtyard).

Start with [`docs/`](docs/README.md):
- [`docs/scenarios.md`](docs/scenarios.md): every scenario's design, why each value is what it is, and its calibration.
- [`docs/look.md`](docs/look.md): the window, its text and art, the courtyard, the palette and how it is built.
- [`docs/future.md`](docs/future.md): suggestions for future changes.

The player-facing guide is [`Flow Fix guide.md`](Flow%20Fix%20guide.md), installed next to the scenarios.
[`AGENTS.md`](AGENTS.md) is the working guide for AI agents: every file, the commands, the user's preferences and
the safety rules.

## Main files

| File | What it is |
| --- | --- |
| `gen_specs.py` | Every scenario's design. Edit this to change a scenario. Writes `specs.json`. |
| `build.py` | Turns `specs.json` into `.sce` files in `out/`, with the window look (`egypt.py`) and the courtyard (`courtyard/`). |
| `check_view.py`, `check_scene.py` | Checks: no target off screen, nothing covering a target. |
| `playlist.py`, `install.py` | The `Flow Fix` playlist, and the installer (copies changed files; `--dry-run` previews). |
| `stats_*.py` | Read-only analysis of the user's runs. |
| `retired/` | Old installed files and superseded test scenarios. Nothing is deleted. |

## Rebuild and install

```bash
python gen_specs.py && python build.py specs.json out
python check_view.py && python check_scene.py out
python install.py --dry-run && python install.py
```

Restart KovaaK's afterwards; it reads scenarios only at startup.
