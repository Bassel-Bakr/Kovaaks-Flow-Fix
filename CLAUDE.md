@AGENTS.md

## Claude Code notes

- **Skills.** Claude Code discovers skills in `.claude/skills/`. Those are thin adapters: each points to the shared,
  agent-neutral skill in `skills/<name>/SKILL.md`. Read and edit the shared file; keep an adapter's `name` and
  `description` in sync with its shared skill.
- **Memory.** Anything you save to memory must also land in the repository (`docs/`, `AGENTS.md` or a skill), so
  other agents see it too.
- **Style.** The user writes docs in plain, simple English prose: short sentences, active voice, no arrows.
