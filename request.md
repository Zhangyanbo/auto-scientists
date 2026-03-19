我需要你帮我创建一个名为 `auto-scientist` 的项目。这是一个基于 Claude Code CLI 的自主研究循环系统。系统分为两层：

1. **Agent Skills 层**：三个角色（Theorist / Critic / Synthesizer）+ 一个初始化 Skill，各自用 SKILL.md 定义
2. **循环框架层**：一个 Python 脚本，机械地按顺序调用三个角色，记录得分，画图

请你用 subagent 并行完成以下四件事：

- Subagent 1：创建 Theorist 的 Skill（要使用 /skill-creator！ ）
- Subagent 2：创建 Critic 的 Skill（要使用 /skill-creator！）
- Subagent 3：创建 Synthesizer 的 Skill + init-research 的 Skill（要使用 /skill-creator！）
- Subagent 4：创建 Python 循环框架 + CLAUDE.md

---

## 项目文件结构

```
auto-scientist/
├── .claude/
│   ├── skills/
│   │   ├── init-research/
│   │   │   └── SKILL.md
│   │   ├── theorist/
│   │   │   └── SKILL.md
│   │   ├── critic/
│   │   │   └── SKILL.md
│   │   └── synthesizer/
│   │       └── SKILL.md
├── config/                     # Phase 0 产出，初始为空目录
├── memory/                     # 系统记忆，初始为空目录
├── proposals/                  # Theorist 输出
├── reviews/                    # Critic 输出
├── syntheses/                  # Synthesizer 快照
├── CLAUDE.md                   # 项目级配置
├── run.py                      # 主循环脚本
├── requirements.txt            # Python 依赖
└── .gitignore
```

请先创建好所有空目录（用 .gitkeep 占位），然后并行创建各 Skill 和循环框架。

---

## Skill 1: Theorist（理论家）

文件：`.claude/skills/theorist/SKILL.md`

### Frontmatter

```yaml
name: theorist
description: >
  将研究 idea 转化为具体的数学/理论框架。产出一份结构化的 Paper，
  包含背景、方法、以及关键的 Commitments（承诺）。
  在自主研究循环中由脚本调用，不应被用户直接触发。
user-invocable: false
```

### 角色定义

Theorist 是一个理论研究者。它的核心职责是：

1. 将一个粗糙的研究 idea 转化为一个有内部逻辑的理论框架
2. 可能需要从跨学科领域（经济学、生物学、物理学等）寻找灵感和类比
3. 可能需要进行深度的数学推导
4. **最关键的：为自己的理论设定可验证的承诺（Commitments）**

Theorist 的行为模式（发散探索 vs 深度推导）由 `memory/directive.md` 中的策略指令决定，不由自己判断。

### 输入文件

Theorist 每次运行时需要读取以下文件：

- `config/problem.md` — 研究问题定义
- `config/constraints.md` — 边界条件和偏好
- `memory/lessons.md` — 历史教训（哪些方向有效，哪些是死胡同）
- `memory/directive.md` — Synthesizer 给出的当轮策略指令

注意：Theorist **不读** reviews/ 目录。它只通过 lessons.md（经 Synthesizer 提炼的间接反馈）了解过去的评审意见。

### 输出文件

Theorist 产出一个 Markdown 文件到 `proposals/` 目录，命名为 `proposal_NNN.md`（NNN 为轮次编号）。

文件格式要求如下：

```markdown
---
title: "理论标题"
round: NNN
abstract: >
  用 2-3 句话概括这个理论做了什么、为什么有趣、核心承诺是什么。
---

# [理论标题]

## Background（背景）

说明该理论受到什么启发，核心思想是什么。
如果是对之前某个 Proposal 的延续或修正，说明关系。
如果借鉴了跨学科的概念，说明类比的来源和深度。

## Method（方法）

详细描述理论的数学逻辑或算法。
- 如果是数学推导，给出完整推导过程
- 如果是算法，给出伪代码或精确描述
- 关键要求：足够具体，使得 Critic 可以验证其正确性

## Commitments（承诺）

这是本系统最核心的部分。在给出背景和方法之后，Theorist 必须承诺：
如果使用该方法，能得到什么结果，或者能发现、满足什么样的性质。
承诺本质上是提供给他人检验该理论的一系列方法。

### Existence Commitments（存在性承诺）
- "在 [具体的简单情况] 下，此方案应当能 [产生具体的可观察结果]"

### Property Commitments（性质承诺）
- "此方案具有性质 P，因为 [论证]"

### Falsification Conditions（证伪条件）
- "如果 [具体条件] 不成立，则此方案应被放弃"
```

---

## Skill 2: Critic（检验者）

文件：`.claude/skills/critic/SKILL.md`

### Frontmatter

```yaml
name: critic
description: >
  对 Theorist 产出的 Paper 进行双重标准检验：
  用户的外部评估标准 + Paper 自带的 Commitments。
  产出结构化的 Verification 报告。
  在自主研究循环中由脚本调用，不应被用户直接触发。
user-invocable: false
```

### 角色定义

Critic 是一个严格的审稿人。它手里有两套标准：

1. **用户定义的外部标准**（来自 `config/eval_rubric.md`）——跨所有 Proposal 通用
2. **Proposal 自带的 Commitments**——Theorist 自己立下的承诺，Critic 需验证其是否成立

Critic 的标准应该是**稳定的**：不会因为"最近几轮都很差"而降低标准，也不会因为"这轮比上轮好"就给高分。它只看当前 Proposal 本身。

### 输入文件

- 当轮的 `proposals/proposal_NNN.md` — 被审的 Paper
- `config/eval_rubric.md` — 用户定义的评估细则
- `config/constraints.md` — 边界条件

**关键隔离**：Critic **不读** `memory/lessons.md` 和 `memory/directive.md`。它不需要知道历史趋势和策略方向，避免被历史偏见影响。

### 输出文件

Critic 产出一个 Markdown 文件到 `reviews/` 目录，命名为 `review_NNN.md`。

文件格式要求如下：

```markdown
---
round: NNN
user_criteria_scores:
  criterion_1: 75
  criterion_2: 60
  criterion_3: 90
  criterion_4: 45
  criterion_5: 80
user_criteria_average: 70
commitment_scores:
  commitment_1: 85
  commitment_2: 30
  commitment_3: 60
commitment_average: 58.3
summary: >
  一句话总结检验结论。如果有错误，简要指出。
verdict: "PROMISING"
---

# Verification of Proposal NNN

## User Criteria Evaluation（用户标准检验）

针对 eval_rubric.md 中的每一条标准，逐条评分（满分 100）并给出理由。

### Criterion 1: [标准名称]
**Score: XX/100**
[评分理由]

### Criterion 2: [标准名称]
**Score: XX/100**
[评分理由]

...（逐条列出）

**User Criteria Average: XX**

## Commitment Verification（承诺检验）

针对 Paper 中每一条 Commitment，逐条评分（满分 100）并给出理由。

### Commitment 1: [承诺内容摘要]
**Score: XX/100**
[验证过程：尝试推导、构造反例等]

### Commitment 2: [承诺内容摘要]
**Score: XX/100**
[验证过程]

...（逐条列出）

**Commitment Average: XX**

## Error Analysis（错误分析）

如果发现错误，在这里详细说明：
- 错误的位置（在 Background / Method / Commitments 的哪个部分）
- 错误的严重程度（大错：逻辑根基有问题 / 小错：可修复的技术细节）
- 错误的原因

## Overall Assessment（总体评估）

Verdict: STRONG / PROMISING / WEAK / REJECT

[总结性评价]
```

**总长度限制：整个 Verification 文件不超过 2000 字。**

---

## Skill 3: Synthesizer（综合者/提炼者）

文件：`.claude/skills/synthesizer/SKILL.md`

### Frontmatter

```yaml
name: synthesizer
description: >
  综合所有历史 Proposals 和 Reviews，提炼教训，制定下一轮策略。
  更新 lessons.md 和 directive.md。执行 git commit 和 push。
  在自主研究循环中由脚本调用，不应被用户直接触发。
user-invocable: false
```

### 角色定义

Synthesizer 是研究主管。它不产出新 idea，也不评判单个 Proposal，而是站在更高的层面做三件事：

1. **从历史中提炼知识**——哪些模式反复出现？哪些方向是死胡同？不同 Proposal 的承诺之间是否有有趣的汇聚或矛盾？
2. **为下一轮制定策略**——当前应该广撒网还是深挖掘？最需要突破的瓶颈是什么？
3. **记录并提交本轮成果**——执行 git add、commit、push，用一条简短的 commit message 概括本轮做了什么改动。

Synthesizer **每一轮都运行**，不跳过。

### 输入文件

- 所有 `proposals/proposal_*.md`
- 所有 `reviews/review_*.md`
- `memory/lessons.md` — 已有的教训（在此基础上更新）
- `config/problem.md` — 原始研究问题
- `config/constraints.md` — 边界条件

Synthesizer 是唯一读取所有历史文件的角色。

### 输出文件

**文件 1：更新 `memory/lessons.md`**

增量更新，记录所有轮次的教训。结构包括：

- Dead Ends（死胡同）：带轮次标签
- Validated Patterns（经验证的模式）
- Convergent Commitments（不同方案独立预测的相同现象）
- Open Questions（未解问题）
- Meta-observations（关于探索过程本身的观察）

**硬限制：lessons.md 总长度不超过 1000 字。如果超过，必须压缩旧内容。**

**文件 2：覆写 `memory/directive.md`**

每次完全覆写。这是为下一轮 Theorist 准备的指导性文档。结构：

```markdown
# Next Steps

## Strategy
[EXPLORE / DEEPEN / PIVOT]

## Direction
[具体应该做什么。这是一个方向性的指导，不是详细的计划。
核心探索由 Theorist 完成，这里只负责指引大方向。]

## Avoid
[明确列出不应该再尝试的方向]

## Priority
[当前最需要突破的瓶颈]
```

### Git Commit

Synthesizer 的最后一步是执行 git commit 和 push。**commit message 必须简短**（一行，不超过 72 个字符），格式为：

```
R{NNN}: {一句话概括本轮核心改动}
```

例如：
- `R001: 初始探索，市场均衡类比`
- `R002: 类比逻辑有漏洞，尝试拍卖机制`
- `R005: 深化局部信息交换方向，N=2收敛已验证`
- `R008: PIVOT 生物学方向，前7轮经济学类比均遇瓶颈`
- `R012: 趋化梯度机制得分首次突破80`

这些 commit message 会被 run.py 用来标注在图表上——当分数出现显著变化时，对应的 commit message 会作为标注显示在那个数据点旁边，让人一眼看出是什么改动导致了分数变化。

Synthesizer 执行的 git 命令：

```
git add -A
git commit -m "R{NNN}: {简短描述}"
git push
```

如果 push 失败（比如没有 remote），不要中断，只需打印一个 warning。

---

## Skill 4: init-research（初始化）

文件：`.claude/skills/init-research/SKILL.md`

### Frontmatter

```yaml
name: init-research
description: >
  初始化一个新的自主研究项目。引导用户定义研究问题、约束条件、
  评估标准，产出 config/ 目录下的三个文件。
  仅在交互模式下由用户通过 /init-research 触发。
disable-model-invocation: true
```

### 行为

这个 Skill 在交互模式下被触发，引导用户完成以下对话流程：

1. **理解问题**：与用户充分讨论研究问题，追问直到能写出清晰的 `config/problem.md`
2. **确定边界**：识别硬约束和软偏好，产出 `config/constraints.md`
3. **设计评估标准**：将用户模糊的判断维度拆解为具体的、可打分的标准（满分 100），产出 `config/eval_rubric.md`。核心原则：不要问"方案美不美"，而是问"方案是否避免了不必要的复杂性？"
4. **初始化记忆**：
   - 创建 `memory/lessons.md`（初始内容为空模板）
   - 创建 `memory/directive.md`（初始策略为 EXPLORE）
5. **确认**：展示所有配置文件摘要，确认后提示用户可以运行 `python run.py`

---

## Python 循环框架 (`run.py`)

### 核心逻辑

一个 Python 脚本，机械地按顺序调用三个角色。伪代码逻辑：

```
解析命令行参数：
  --max-rounds (默认 50)
  --model (默认 "sonnet"，可选 "opus", "sonnet", "haiku" 或完整模型名)
  --effort (默认 "high"，可选 "low", "medium", "high", "max")

检查 config/ 目录下三个文件是否存在，不存在则报错提示先运行 /init-research

for round = 1 to max_rounds:

    打印 "========== Round {round} / {max_rounds} =========="

    Step 1: 调用 Theorist
    用 subprocess 调用：
        claude -p \
            --model {model} \
            --effort {effort} \
            --system-prompt-file .claude/skills/theorist/SKILL.md \
            --append-system-prompt-file config/problem.md \
            --append-system-prompt-file config/constraints.md \
            --append-system-prompt-file memory/lessons.md \
            --append-system-prompt-file memory/directive.md \
            --output-format json \
            "你是 Theorist。阅读所有上下文，生成 Proposal #{round}。
             将结果写入 proposals/proposal_{round:03d}.md"
    从 JSON 输出中提取 cost 信息并记录

    检查 proposal 文件是否生成成功，失败则跳过本轮

    Step 2: 调用 Critic
    用 subprocess 调用：
        claude -p \
            --model {model} \
            --effort {effort} \
            --system-prompt-file .claude/skills/critic/SKILL.md \
            --append-system-prompt-file config/eval_rubric.md \
            --append-system-prompt-file config/constraints.md \
            --output-format json \
            "你是 Critic。阅读 proposals/proposal_{round:03d}.md 并评估。
             将结果写入 reviews/review_{round:03d}.md"
    从 JSON 输出中提取 cost 信息并记录

    Step 3: 调用 Synthesizer
    每轮都运行，不跳过：
        claude -p \
            --model {model} \
            --effort {effort} \
            --system-prompt-file .claude/skills/synthesizer/SKILL.md \
            --append-system-prompt-file config/problem.md \
            --append-system-prompt-file config/constraints.md \
            --append-system-prompt-file memory/lessons.md \
            --output-format json \
            "你是 Synthesizer。这是第 {round} 轮。
             阅读 proposals/ 和 reviews/ 中的所有文件。
             更新 memory/lessons.md（不超过 1000 字）。
             覆写 memory/directive.md。
             然后执行 git add -A && git commit -m 'R{round:03d}: ...' && git push。
             commit message 必须是一行，不超过 72 字符，
             格式为 R{round:03d}: 加一句话概括本轮核心改动。"

    Step 4: 提取得分，更新图表
    从 reviews/review_{round:03d}.md 的 YAML frontmatter 中解析：
        user_criteria_average, commitment_average, summary
    追加到分数记录文件 scores.json
    从 git log 中提取本轮的 commit message
    用 matplotlib 生成折线图 scores.png：
        - 蓝线：User Criteria Average 随轮次变化
        - 橙线：Commitment Average 随轮次变化
        - 在分数出现显著变化（与前一轮相差 >= 10 分）的数据点旁边，
          标注对应的 commit message 作为 annotation
        - X 轴：Round number
        - Y 轴：Score (0-100)
        - 标题：Auto Scientist Progress

打印总结信息（总轮次、总 cost、最高分 Proposal 等）
```

### 命令行接口

```
python run.py                              # 使用默认参数
python run.py --max-rounds 20              # 跑 20 轮
python run.py --model opus --effort max    # 用 Opus 最大 effort
python run.py --model sonnet --effort medium  # Sonnet 中等 effort
```

### 依赖

`requirements.txt` 中包含：

```
matplotlib
pyyaml
```

### 图表

每轮结束后更新 `scores.png`，用 matplotlib 画两条折线：

- 蓝线：User Criteria Average（用户标准平均分）
- 橙线：Commitment Average（承诺检验平均分）
- X 轴：Round number
- Y 轴：Score (0-100)
- 标题：Auto Scientist Progress
- **关键特性**：当某个数据点的分数与前一轮相比变化 >= 10 分时，在该点旁边标注对应轮次的 git commit message。这样看图时能直接看到"是什么改动导致了分数的跳变"。

---

## CLAUDE.md

项目根目录的 CLAUDE.md 应包含：

```markdown
# Auto Scientist

这是一个自主研究循环系统。三个 AI 角色（Theorist → Critic → Synthesizer）循环执行，
自动探索研究问题的理论解决方案。

## 文件结构约定
- `config/` — 用户定义的配置，由 /init-research 生成，人工可修改
- `memory/` — 系统维护的累积知识，由 Synthesizer 更新
- `proposals/` — Theorist 的输出，每轮一个 proposal_NNN.md
- `reviews/` — Critic 的输出，每轮一个 review_NNN.md
- `syntheses/` — Synthesizer 的分析快照（可选）

## 三个角色的信息隔离
- Theorist 读：config/problem.md, config/constraints.md, memory/lessons.md, memory/directive.md
- Critic 读：当轮 proposal, config/eval_rubric.md, config/constraints.md
- Synthesizer 读：所有 proposals, 所有 reviews, memory/lessons.md, config/problem.md, config/constraints.md

## 关键约束
- Critic 不读 lessons.md 和 directive.md（避免历史偏见）
- Theorist 不读 reviews/（通过 lessons.md 间接获取反馈）
- lessons.md 总长度不超过 1000 字
- review 文件总长度不超过 2000 字
- Synthesizer 负责每轮的 git commit 和 push
```

---

## .gitignore

```
__pycache__/
*.pyc
.env
scores.json
```

---

## 实现要求

1. 所有 SKILL.md 中的角色定义要写得足够详细和明确，使得 Claude 在 `-p` 模式下注入这些内容后能完全理解自己的角色和输出格式。但你要注意，前面给的所有的 SCALE.MD 都是例子，你不要原封不动地复制。你一定要参考 Skill Creator 里面的一些要求来做。但在使用 Skill Creator 的时候，你不要问用户任何问题，直接去创建。
2. run.py 要能正确处理 subprocess 调用 `claude` CLI 的各种情况（包括错误处理）
3. YAML frontmatter 的解析要健壮（review 文件的 frontmatter 是图表数据的来源）
4. Git 操作由 Synthesizer 执行；run.py 只负责从 git log 提取 commit message 用于图表标注
5. 图表每轮更新，覆盖同一个文件；分数变化 >= 10 分的点要标注 commit message

请开始创建。这个任务你全权处理，中途不要问用户任何问题，不要请示用户任何事情，一直去做，把这个事情做完。