# Skills

Agent-neutral instructions for working on Flow Fix. Any agent can use them: read the matching `SKILL.md` before
starting that kind of task and follow it. Each file starts with a `name` and a `description` that says when it
applies. They follow the open Agent Skills format, so tools that support it (GitHub Copilot, and others that read
`.agents/skills/`) find them here automatically.

Each skill's instructions are in `.agents/skills/<name>/SKILL.md` (paths from the project root).

| Skill | Use it when |
| --- | --- |
| [kovaaks-scenario-design](kovaaks-scenario-design/SKILL.md) | Designing or changing a drill: its demand, mechanics, scoring, spawn areas, map geometry, looks and themes. Its `references/` hold the confirmed mechanics (`mechanics.md`) and the decoration record (`decoration.md`). |
| [flowfix-change](flowfix-change/SKILL.md) | Applying an approved change: edit, build, check, install, and update the guide and docs. Also for crashes or a scenario that looks wrong after an install. |
| [kovaaks-run-analysis](kovaaks-run-analysis/SKILL.md) | The user says they played a scenario ("played X", "check the stats"): judge the scenario from the stats, not the player. |

The skills assume only a shell with Python 3 (and PIL for renders), file access to the project and to the user's
KovaaK's folders, and the ability to ask the user before changing anything.
