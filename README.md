# Auto-Scientist

Autonomous research loop powered by Claude Code CLI. Iteratively develops, critiques, and refines theoretical frameworks for open-ended research problems — problems where there is no single loss function to optimize.

## Design Philosophy

The core idea: **a theory that cannot specify how to verify or falsify itself is not a real theory.**

The Theorist agent doesn't just propose ideas — every output is a *commitment*. It must state: "if this theory is correct, you will observe X under condition Y; if Z does not hold, abandon it." This transforms vague speculation into something checkable. The Critic then has a clear job: verify whether those commitments actually hold, alongside the user's own evaluation criteria. The Synthesizer reads all history, distills lessons, and sets direction for the next round.

```
Theorist  -->  Critic  -->  Synthesizer  --+
   ^                                       |
   +---------------------------------------+
```

- **Theorist** — Proposes a structured theory with three types of commitments: existence claims (it works in this concrete case), property claims (it guarantees this structural property), and falsification conditions (abandon it if this fails).
- **Critic** — Checks each commitment against the proposal's own logic, and scores the proposal against the user's predefined rubric. Two independent failure modes are caught: unfalsifiable theories (weak commitments) and off-target theories (fail the rubric).
- **Synthesizer** — The research director. Sets strategy (EXPLORE / DEEPEN / PIVOT) so that exploration vs. exploitation emerges from the loop dynamics.

The agents are informationally isolated to prevent bias: the Theorist never reads reviews, the Critic never reads historical lessons, and only the Synthesizer has full context.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Zhangyanbo/auto-scientists/main/install.sh | bash
```

The installer will ask whether you use `uv` or `python`, then set up:
- `auto-research` command (global CLI)
- `/init-auto-research` skill in Claude Code

## Usage

### 1. Initialize a Research Project

```bash
mkdir my-research && cd my-research
git init
claude
# Then type: /init-auto-research
```

An interactive dialog walks you through defining your research problem, constraints, and multi-dimensional evaluation rubric.

### 2. Run the Loop

```bash
auto-research --rounds 10
```

Each round runs Theorist -> Critic -> Synthesizer, producing a proposal, a scored review, and updated strategy. A progress chart is saved to `syntheses/progress.png`.

Options: `--start N` (resume from round N), `--model NAME` (default: sonnet), `--debug` (stream output).
