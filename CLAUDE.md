# Auto-Scientist

Autonomous research loop system, powered by Claude Code CLI.

## Project Structure

- `skills/` — Agent skill definitions (theorist.md, critic.md, synthesizer.md, init-auto-research/)
- `run.py` — Main loop script (reads skills directly, passes content in prompt)
- `install.sh` — Installer (sets up global CLI + Claude Code skill)

## User Project Structure (created by /init-auto-research)

- `config/` — Research configuration (problem.md, constraints.md, eval_rubric.md)
- `memory/` — System memory (lessons.md, directive.md)
- `proposals/` — Theorist output (theory proposals)
- `reviews/` — Critic output (verification reports)
- `syntheses/` — Synthesizer output (progress chart)

## Role Isolation Rules

- **Theorist** reads: config/problem.md, config/constraints.md, memory/lessons.md, memory/directive.md
  - Does NOT read reviews/ directory
- **Critic** reads: proposals/proposal_NNN.md, config/eval_rubric.md, config/constraints.md
  - Does NOT read memory/lessons.md, memory/directive.md
- **Synthesizer** reads: all proposals/, all reviews/, memory/lessons.md, config/problem.md, config/constraints.md

## File Limits

- `memory/lessons.md` must not exceed 1000 words
- `reviews/review_NNN.md` must not exceed 2000 words

## Git Commit Format

```
R{NNN}: {one-line summary}
```
