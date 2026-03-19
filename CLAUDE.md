# Auto-Scientist

Autonomous research loop system, powered by Claude Code CLI.

## Project Structure

- `config/` — Research configuration (problem.md, constraints.md, eval_rubric.md)
- `memory/` — System memory (lessons.md, directive.md)
- `proposals/` — Theorist output (theory proposals)
- `reviews/` — Critic output (verification reports)
- `syntheses/` — Synthesizer output (progress snapshots)
- `run.py` — Main loop script

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

## Running

```bash
uv pip install -r requirements.txt
python run.py --rounds 10
```
