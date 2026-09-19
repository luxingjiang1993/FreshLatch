# 评测 harness 与无工具假绿对照设计评估

> 工单:[评测 harness 与无工具假绿对照脚本](https://github.com/luxingjiang1993/FreshLatch/issues/9)
> 日期:2026-09-19 · 状态:已拍板(本文供实施参照与面试讲解)
> 配套:`docs/product/Anthropic级demo差距清单.md` 第 1、2、3 条、`docs/product/Anthropic面试准备清单.md` 第 7 条、`docs/research/语料金标设计评估.md`(gold.json schema)、ADR-0005

---

## 1. 问题:这张工单要拍什么

工单 #8 已把「测什么」(12 主张三档金标 + causal_chain + gold.meta seed/checksum 预留)钉死;本工单拍「怎么跑、怎么对账、怎么展示、怎么进 CI」。评测设施要同时养活四件事:

| 用途 | 出处 |
|---|---|
| 金标对账:导入 docket → 端到端复验 → 与 gold.json 对账,报 must_stale 命中率 | 工单 #9 正文;差距清单第 1 条(统计纪律接口) |
| 假绿对照:同模型无工具只读 T0 摘要,已死主张必须判绿(产品必须红) | CONTEXT.md「假绿对照」;立项切片 §8 |
| 规则闸单测:gold.json 驱动 pytest,stale/unknown 不得绿灯等不变量进 CI | 面试准备清单第 7 条;工单 #8 三道验收之三 |
| W3–W4 验收与面试演示:评测怎么跑、结果怎么展示 | 工单 #9 正文末问 |

**纪律前提**:评测是产品的一等功能(面试准备清单列为本期预留三件实装之一),不是外挂工具;「评测的是你真卖的东西」是本设计的排他性第一原则。

---

## 2. 七个决策与拍板

### 决策一:金标 runner 跑什么——端到端主链,不跑替身

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **(a) 端到端复验主链** ✅ | 真实 Lead 循环(#6 裸 tools 循环)+ Critic 派驻 + 规则闸,与复验单 UI 同一入口,无人审 | 测产品真身;假绿对照因果链(产品红是因为复验环节)闭合;面试叙事无可指摘 | 分钟级、有 LLM 成本、随机性大(决策七 multi-run 接口兜) |
| (b) 只跑 Auditor + 闸 | 跳过 Lead 检索,直接喂 T0/T1 文档给 Auditor 判三档 | 快、便宜、稳定;混淆矩阵干净 | 测替身:检索 miss 这个最大失败源被绕过;Auditor 过 ≠ 主链过,对照意义稀释 |
| (c) 两层都要 | 主指标 (a) + commit 级快速回归 (b) | 双档信号 | 两套对账代码工时翻倍;(b) 信号误导 |

**拍板 (a),且只实装 (a)**。multi-run 接口(决策七)就是治随机性的药;替身评测直接违背本工单的存在理由。

### 决策二:假绿对照的输出契约——JSON mode,三档同构

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **(a) JSON mode** ✅ | 要求 `{"verdict": "alive"\|"dead"\|"unknown"}` 结构化输出,按字段机械解析 | 解析确定;判 alive 即假绿,可机械对账;与主链三档判定同构 | 一次 prompt 工程;DashScope JSON mode 兼容性需冒烟补验(与 #2 已验的多轮工具调用是两条路) |
| (b) 自由文本 + 关键词匹配 | 问「是否仍成立」匹配关键词 | 零工程 | 解析脆弱(「似乎仍然基本成立」式句子把对账变成 NLP 题);对照结果不可信 = 对照失效 |

**拍板 (a)**。对照 prompt 红线:**不得透露 T1 存在、不得透露金标**——只给 T0 摘要 + 主张,问「现在是否仍成立」。这是「无工具基线必须判错」实验设计的本体,泄一句提示对照就废了。

### 决策三:代码落点与命令形态——`src/freshlatch/eval/` 包

| 选项 | 做法 | 优势 | 代价 |
|---|---|---|---|
| **(a) `src/freshlatch/eval/`** ✅ | `runner.py` 金标对账 / `control.py` 假绿对照 / `matrix.py` 混淆矩阵纯函数(可单测) / `report.py` 报告;`python -m freshlatch.eval run\|control\|report` | 符合 #3 模块划分;评测 import 主链路径自然 | — |
| (b) 仓库根 `eval/` 外挂目录 | 与产品物理隔离 | 隔离感 | 违背 ADR-0001;外挂 import 主链别扭;评测降级为二等公民 |

**拍板 (a)**。命令:`run --gold data/eval/gold.json [--runs N]`、`control`、`report`。

### 决策四:报告产出与混淆矩阵口径——双产出,报条数不报百分比

- **双产出**:console 摘要表(人当场看)+ `reports/report-<date>.md` 进 git(留存、可 diff、面试引用)。
- **混淆矩阵**:3×3(预测 fresh/stale/unknown × 期望三档),按 must_stale/must_fresh/must_unknown 各报**命中/漏判条数,不报百分比**——工单 #8 登记册已拍「12 条只看方向不看小数」,防小样本百分比遮丑。
- **失败归因**:本期只存原料——每条 run 的 trajectory jsonl 落盘(`docs/eval/` 或 `reports/trajectories/`),失败条目附轨迹指针 + 人工定性;机械归因 harness(检索 miss / 推理错 / 闸门绕过,差距清单第 2 条)是 W5–W8 项,**本期只留原料落点**。

### 决策五:CI 接入位——闸门单测进 CI,LLM 评测手动触发

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **(c) 两档** ✅ | CI 每次提交跑 pytest 规则闸单测(纯函数零成本);LLM 金标 runner 手动 + milestone 触发,报告落 `reports/` 进 git | 两个绿灯语义分离:CI 绿 = 代码不变量没破;评测报告绿 = 模型表现没破 | 评测报告靠人记得跑(milestone 纪律兜) |
| (a) CI 只跑单测 | 同上但无 milestone 约定 | 最省钱 | LLM 表现回归无信号 |
| (b) CI 全量跑 runner | 每次 push 真回归 | 自动化 | 烧额度、分钟级、DashScope 抖动 = 假红灯;prompt 迭代期恒红,违背「CI 红灯即回归」语义 |

**拍板 (c)**。pytest 目录借鉴多 agent 案例双 gate 结构:`tests/unit/`(gates 纯函数单测,CI 每次提交)+ `tests/eval/`(gold.json 驱动的闸单测,「stale/unknown 不得绿灯」「无 `t1_evidence_ids` 不得 fresh」「checksum 对不上不得 fresh/续命」,语义 = 多 agent 案例 compliance gate);`conftest.py` 只做 sys.path 注入,不堆 fixture。CI = GitHub Actions,job 只跑 `pytest tests/`,零 LLM 依赖。

### 决策六:评测运行方式——CLI + 报告,不做评测页 UI

| 选项 | 做法 | 优势 | 代价/风险 |
|---|---|---|---|
| **(a) CLI + markdown 报告** ✅ | 终端跑 + 报告进 git;验收展示 = 终端 runner + 复验单 UI 逐条点回 | 零新 UI 工时;复验单 UI(#4)已是判定展示面,两现成界面拼完整叙事 | 演示不如专用页面花哨 |
| (b) 评测页 UI | FastAPI 加 `/eval/` 页面 | 演示好看 | 第二界面工时翻倍;评测是开发纪律不是用户功能 |
| (c) runner 写库 + UI 读库 | 一个界面两个用途 | 界面复用 | runner↔UI 接缝在两者都未定型时是负担;W5–W8 消融表页届时再议 |

**拍板 (a) 本期**。

### 决策七:统计纪律接口——`--runs N` 本期实装,默认 1

- 接口:`run --runs N`,每条主张跑 N 遍,报 per-claim 命中次数/N + 全量通过率 + 波动区间;**报告格式按 N>1 设计**(per-claim pass@k 表),N=1 时该表退化为一列——接口不留遗憾。
- 成本账:12 主张 × N=10 × ≈¥0.001/主张 ≈ ¥0.12/轮全量,multi-run 便宜到不构成反对理由。
- 本期承诺:**接口实装 + N=1 报告**;N≥5 方差报告是 W5–W8 纪律(差距清单第 1 条归属 W5–W8,只借接口)。与 #8 登记册「多 seed 统计显著性【弃】」不冲突:multi-run 是 N 次独立运行,不是多 seed 统计表演。

---

## 3. 参考代码借鉴映射(盘点结论)

| 目标组件 | 借鉴模式 | 出处 |
|---|---|---|
| 金标 runner | 多 agent 案例:契约驱动 `machine_check.type` 分发(禁止按 assertion.id 写死分支)+「重置夹具→跑→validate→预算耗尽 blocked_for_human」循环;投顾案例:命中率 = found/expected 聚合 | `project 多agent/src/missions/runner.py`、`checks.py`、`artifacts/validation_contract.json`;`CASE-投顾AI助手(效果评估)/2-langsmith_testing_evaluation.py` |
| 混淆矩阵 3×3 | **三案例均无现成实现,新写**;挂载点仿 checks.py 正交断言设计(期望拒绝 × 实际拒绝 × 落库),扩成 TN/FP/FN/TP 表;`matrix.py` 写成纯函数进 `tests/unit/` | `project 多agent/src/missions/checks.py` |
| 假绿对照脚本 | 多 agent 案例刻意造假绿夹具(`AUDIT_BUGGY` 重写实现,造出 unit 绿/compliance 红)——「基线必须错、产品必须对」的现成模式 | `project 多agent/src/missions/runner.py`、`src/transfer_api/audit_fixtures.py` |
| pytest 双 gate | `tests/unit` vs `tests/compliance` 目录语义 + 5 行 conftest 注入 src;断言直接 new 服务对象查 error_code,不 mock 大山 | `project 多agent/tests/` |
| Auditor 打分器壳(后续) | openevals `create_llm_as_judge(feedback_key, continuous, judge=ChatTongyi)` 喂 inputs/outputs/reference/context 读 score | `CASE-openevals使用/5-rag_groundedness.py`、`8-hallucination.py` |
| 批量评估 + 阈值断言(后续) | deepeval `evaluate(test_cases, metrics)` + 阈值 metric + `assert_test`;LangSmith 数据集托管批量 run | `CASE-投顾AI助手(效果评估)/deepeval_wealth_advisor.py` |

**弃用判断**:LangSmith/deepeval/openevals 均不引入依赖——本期评测语义(金标对账 + 假绿对照 + 闸单测)三案例都只有零件没有整体,引入框架的代价(云端数据集、外部服务依赖)大于收益;`runner.py` 百余行自写即可,轨迹落盘自带可回放原料。openevals 打分器壳留作 Auditor 打分器需要 LLM-judge 时的写法参考,不进依赖。

## 4. 手段登记册(本期处置 vocabulary:【实装】/【预留】/【触发】/【弃】)

| 手段 | 一句话原理 | 优势 | 代价/风险 | 本期处置 |
|---|---|---|---|---|
| 端到端金标 runner | 跑真 Lead 循环对账 gold.json | 测真身,对照因果链闭合 | 慢、随机 | 【实装】 |
| multi-run `--runs N` | 每条金标跑 N 次报 pass@k/方差 | 治 Agent 随机性 | ≈¥0.12/轮,可忽略 | 【实装】接口,N=1 运行;N≥5 报告【触发】W5–W8 |
| 无工具假绿对照(JSON mode) | 同模型无工具读 T0,必须判错 | 证明复验环节真起作用 | 多一次冒烟(JSON mode 兼容性) | 【实装】 |
| 3×3 混淆矩阵 | 三档预测 × 三档期望 | 假阳性/假绿/unknown 漏判分开可见 | 12 条样本小 | 【实装】报条数不报百分比 |
| trajectory 原料落盘 | 每条 run 存 messages JSONL + 步数/预算遥测 | 失败可回放、归因有原料 | 磁盘 | 【实装】;机械归因 harness【触发】W5–W8 |
| 失败机械归因(检索 miss/推理错/闸门绕过) | 轨迹分类到失败类别 | 错误分析一页纸 | 要规则+LLM 混合判类 | 【预留】原料落点本期在场 |
| 闸门单测双 gate(unit/eval) | gold.json 驱动 gates 不变量 | 金标一份两用(#8 已拍) | 无 | 【实装】 |
| CI 金标回归 | 每次提交自动跑金标 | 真回归自动化 | 烧额度、假红灯、prompt 迭代期恒红 | 【弃】CI 只进 pytest;LLM runner 手动 + milestone【实装】 |
| 评测页 UI | 专用评测展示页 | 演示好看 | 第二界面工时 | 【弃】本期;W5–W8 消融页【触发】再议 |
| LLM-as-judge 打分器(openevals 式) | 模型打分 0–1 + feedback key | Auditor 需要 judge 时的壳 | 引入依赖 | 【弃】进依赖;写法留参考 |
| LangSmith/deepeval 托管评测 | 云端数据集 + 批量评估 | 团队级评测基建 | 外部服务依赖、本期语义用不上 | 【弃】 |
