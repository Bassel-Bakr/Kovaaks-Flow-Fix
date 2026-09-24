@AGENTS.md
@.agents/skills/README.md

## Claude Code notes

- **Skills.** The project's skills live in `.agents/skills/` (the open Agent Skills format), not `.claude/skills/`, so
  Claude Code does not list them by itself. The skills index is imported above: when a task matches a skill's "use it
  when", read that skill's `SKILL.md` first and follow it.
- **Memory.** Anything you save to memory must also land in the repository (`docs/`, `AGENTS.md` or a skill), so
  other agents see it too.
- **Style.** The user writes docs in plain, simple English prose: short sentences, active voice, no arrows.
