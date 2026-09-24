@AGENTS.md

## Claude Code notes

- **Skills.** The project's skills live in `.agents/skills/` (the open Agent Skills format), not `.claude/skills/`.
  Before a task that matches one, read `.agents/skills/README.md` and the skill's `SKILL.md`, and follow it.
- **Memory.** Anything you save to memory must also land in the repository (`docs/`, `AGENTS.md` or a skill), so
  other agents see it too.
- **Style.** The user writes docs in plain, simple English prose: short sentences, active voice, no arrows.
