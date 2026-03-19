# Auto-Scientist

自主研究循环系统，基于 Claude Code CLI。

## 项目结构

- `config/` — 研究配置（problem.md, constraints.md, eval_rubric.md）
- `memory/` — 系统记忆（lessons.md, directive.md）
- `proposals/` — Theorist 产出的理论提案
- `reviews/` — Critic 产出的审查报告
- `syntheses/` — Synthesizer 产出的综合快照
- `run.py` — 主循环脚本

## 角色隔离规则

- **Theorist** 读取: config/problem.md, config/constraints.md, memory/lessons.md, memory/directive.md
  - 不读 reviews/ 目录
- **Critic** 读取: proposals/proposal_NNN.md, config/eval_rubric.md, config/constraints.md
  - 不读 memory/lessons.md, memory/directive.md
- **Synthesizer** 读取: 所有 proposals/, 所有 reviews/, memory/lessons.md, config/problem.md, config/constraints.md

## 文件限制

- `memory/lessons.md` 不超过 1000 字
- `reviews/review_NNN.md` 不超过 2000 字

## Git Commit 格式

```
R{NNN}: {一句话概括}
```

## 运行

```bash
uv pip install -r requirements.txt
python run.py --rounds 10
```
