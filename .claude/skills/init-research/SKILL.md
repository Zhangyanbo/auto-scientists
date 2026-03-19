---
name: init-research
description: >
  初始化一个新的自主研究项目。引导用户定义研究问题、约束条件、
  评估标准，产出 config/ 目录下的三个文件。
  仅在交互模式下由用户通过 /init-research 触发。
disable-model-invocation: true
---

# Init Research

This skill initializes a new autonomous research project through an interactive dialog with the user. It produces five files across two directories (`config/` and `memory/`) that form the foundation for all subsequent research rounds.

This is an interactive skill — it asks the user questions, listens to their answers, and iterates until the outputs are right. Do not skip ahead or generate all files at once. Walk through each phase sequentially, confirming with the user before moving on.

# Dialog Flow

## Phase 1: 理解问题

Goal: Produce `config/problem.md`.

Start by asking the user to describe their research problem. Then ask follow-up questions to sharpen the problem statement. Good follow-ups include:

- "What would a successful answer look like? Can you give a concrete example?"
- "What's the scope — are we looking for a general theory, a specific mechanism, or a practical method?"
- "Is there existing work on this? What's unsatisfying about it?"
- "Who is the audience for this research?"

Keep asking until you can write a clear, specific problem statement. Then draft `config/problem.md` and show it to the user for confirmation. The file should contain:

```markdown
# Research Problem

## Problem Statement
[1-3 paragraphs describing the core question]

## Success Criteria
[What would a good answer look like? How will we know we've made progress?]

## Scope
[What's in scope and what's explicitly out of scope]

## Background
[Brief context — what's known, what's been tried, why it matters]
```

## Phase 2: 确定边界

Goal: Produce `config/constraints.md`.

Ask the user about constraints. Distinguish between hard constraints (absolute requirements) and soft preferences (nice-to-haves). Probe for:

- Methodological constraints (e.g., "must be analytically tractable", "no simulations")
- Resource constraints (e.g., time, compute, data availability)
- Stylistic preferences (e.g., "prefer elegance over generality")
- Domain boundaries (e.g., "stay within classical mechanics")

Draft and confirm with the user:

```markdown
# Constraints

## Hard Constraints
- [constraint 1]
- [constraint 2]

## Soft Preferences
- [preference 1]
- [preference 2]

## Out of Scope
- [explicitly excluded topics or approaches]
```

## Phase 3: 设计评估标准

Goal: Produce `config/eval_rubric.md`.

This is the most important phase. The evaluation rubric determines how proposals will be scored in every subsequent round. Work with the user to define concrete, scorable criteria.

The core principle: do not ask "is the proposal beautiful?" — instead ask "does the proposal avoid unnecessary complexity?" Turn vague aesthetic judgments into specific, assessable questions.

Guide the user through defining 4-6 evaluation dimensions. For each dimension, define:
- A clear name
- What it measures (1-2 sentences)
- Scoring guidelines (what earns a high vs. low score)
- Weight (points out of 100 total)

All weights must sum to 100.

```markdown
# Evaluation Rubric

Total: 100 points

## [Dimension 1 Name] (XX points)
**Measures**: [what this dimension assesses]
- **High (>80%)**: [what excellence looks like]
- **Medium (40-80%)**: [what adequacy looks like]
- **Low (<40%)**: [what failure looks like]

## [Dimension 2 Name] (XX points)
...
```

**Tips for good rubric design:**
- Prefer falsifiable criteria over subjective ones
- Each dimension should be independent — avoid double-counting
- Include at least one dimension for novelty/insight and one for rigor/correctness
- If the user struggles to articulate criteria, suggest common research dimensions: correctness, novelty, depth, clarity, generalizability, elegance

## Phase 4: 初始化记忆

Goal: Create `memory/lessons.md` and `memory/directive.md`.

This phase requires no user input. After completing Phases 1-3, create the memory directory and initialize both files automatically.

### `memory/lessons.md`

Initialize with an empty template:

```markdown
# Lessons Learned

## Dead Ends
(none yet)

## Validated Patterns
(none yet)

## Convergent Commitments
(none yet)

## Open Questions
(none yet)

## Meta-observations
(none yet)
```

### `memory/directive.md`

Initialize with the default exploration strategy:

```markdown
# Next Steps

## Strategy
EXPLORE

## Direction
自由探索。尚无历史数据，Theorist 应尝试多种不同的切入角度。

## Avoid
(no known dead ends yet)

## Priority
建立对问题的基本理解，产出至少 2-3 个有差异性的初始 Proposal。
```

# Completion

After creating all five files, present a summary to the user:

```
Research project initialized. Created:

  config/problem.md      — Research problem definition
  config/constraints.md  — Hard constraints and soft preferences
  config/eval_rubric.md  — Evaluation rubric (100 points total)
  memory/lessons.md      — Lessons learned (empty template)
  memory/directive.md    — Initial directive (EXPLORE)

You can now start the research loop.
```
