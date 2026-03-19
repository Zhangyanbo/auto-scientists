# Auto-Scientist

Autonomous research loop powered by Claude Code CLI. Iteratively develops, critiques, and refines theoretical frameworks for open-ended research problems — problems where there is no single loss function to optimize.

## Design Philosophy

The core idea: **a theory that cannot specify how to verify or falsify itself is not a real theory.**

The Theorist agent doesn't just propose ideas — every output is a *commitment*. It must state: "if this theory is correct, you will observe X under condition Y; if Z does not hold, abandon it." This transforms vague speculation into something checkable. The Critic then has a clear job: verify whether those commitments actually hold, alongside the user's own evaluation criteria. The Synthesizer reads all history, distills lessons, and sets direction for the next round.

```
Theorist  ──▶  Critic  ──▶  Synthesizer  ──╮
   ▲                                        │
   ╰────────────────────────────────────────╯
```

- **Theorist** — Proposes a structured theory with three types of commitments: existence claims (it works in this concrete case), property claims (it guarantees this structural property), and falsification conditions (abandon it if this fails).
- **Critic** — Checks each commitment against the proposal's own logic, and scores the proposal against the user's predefined rubric. Two independent failure modes are caught: unfalsifiable theories (weak commitments) and off-target theories (fail the rubric).
- **Synthesizer** — The research director. Sets strategy (EXPLORE / DEEPEN / PIVOT) so that exploration vs. exploitation emerges from the loop dynamics.

The agents are informationally isolated to prevent bias: the Theorist never reads reviews, the Critic never reads historical lessons, and only the Synthesizer has full context.

## Quick Start

Prerequisites: Python >= 3.11, [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code), [uv](https://docs.astral.sh/uv/) (or pip).

First, fork this repo on GitHub — the loop automatically commits and pushes results, so you need your own repo to write to.

```bash
git clone https://github.com/<your-username>/auto-scientists.git
cd auto-scientists
uv sync          # or: pip install -r requirements.txt
```

### 1. Initialize a Research Project

```bash
claude
# Then type: /init-research
```

An interactive dialog walks you through defining your research problem (`config/problem.md`), constraints (`config/constraints.md`), and multi-dimensional evaluation rubric (`config/eval_rubric.md`).

### 2. Run the Loop

```bash
python run.py --rounds 10
```

Each round runs Theorist → Critic → Synthesizer, producing a proposal, a scored review, and updated strategy. A progress chart is saved to `syntheses/progress.png`.

Options: `--start N` (resume from round N), `--model NAME` (default: sonnet), `--debug` (stream output).

## Project Structure

```
config/          Research problem, constraints, evaluation rubric
memory/          Accumulated lessons + strategy directive
proposals/       Theorist output (one per round)
reviews/         Critic output (one per round)
syntheses/       Progress chart
run.py           Main loop script
.claude/skills/  Agent definitions (theorist, critic, synthesizer, init-research)
```
