# Anthropic 面试(AI Applied Engineer)准备清单

> 2026-09-19 与 wayfinder 建图会话讨论产出。问题:假设计划全部实现,面向 Anthropic 级公司的 AI Applied Engineer 面试,文档/交付物还缺哪些?技能维度还有哪些被遗漏?
>
> 归属:本期地图(W4 前规格)的 **Out of scope**,除标注「本期预留」的条目。W9–W12 口播期直接取用。

## 一、计划中已有的

| 已有 | 出处 |
|---|---|
| 8–10 分钟面试主叙事 + 90 秒记忆卫生模块pitch | 立项切片 §12、§11.6 |
| 主动揭短(不接 Mem0、合成数据、一类课题) | 切片 §11.6、§12 |
| demo 用户旅程脚本(导入→变红→作废→重跑) | 切片 §6 |
| 金标评测 + 无工具假绿对照 | 切片 §8、§10 |
| 决策记录/ADR——**wayfinder 地图 + domain-modeling 自动产出**,「如何与 AI agent 编排决策」本身就是 applied engineer 作品集,地图建议保留为公开工件 | 本仓 `.claude/rules/` + GitHub issues |

## 二、缺失的文档/交付物

1. **README(英文为主)**:问题、架构图、quickstart、demo 截图/GIF。外企面试第一入口;计划中没有。
2. **DESIGN.md 架构文档**:数据流、角色分权、不变量列表。可直接仿 `project 多agent/DESIGN_PHILOSOPHY.md` 的 I1–I8 写法(fail-closed、人类门闩、诚实自治级别——和 FreshLatch 叙事同构)。
3. **EVAL_REPORT.md 评测报告**:方法、结果表、混淆矩阵、消融、方差、成本。计划只有评测页,没有成文报告。
4. **LIMITATIONS / mini system card**:合成数据、单课题类、无 SSO、注入防护面、误用考虑、**为什么不微调**(把「何时该 fine-tune」的边界说清,本身就是信号)。切片只有口头揭短。
5. **技术文章 / blog post**:公开 writeup,书面表达的最常见证明方式。计划中没有。
6. **公开 demo 链接(可选)**:Streamlit Cloud / HF Spaces 不需要 Docker,与「不要 Docker」约束相容;数据全合成可公开。
7. **规则闸的 pytest 单测 + CI【本期预留】**:「stale 不得绿灯」是产品不变量,**闸门必须有测试**。计划完全未提测试!影响 W1–W4:仓库结构要留 `tests/`,评测 harness 工单要留 CI 回归位。
8. **可复现说明**:seed、依赖 pin、语料 checksum(见《Anthropic级demo差距清单》第 6 条)。
9. **Prompt/skill 迭代日志**:skill 文件每一版怎么改的、失败案例。ADR 里隐含,建议显式化。
10. **开源卫生**:LICENSE、requirements pin、.gitignore、英文 README。

## 三、技能维度对照(超出文档)

| 维度 | 现状 | 判定 |
|---|---|---|
| 多 Agent 编排 / 角色分权 | Lead/Critic/Auditor/Forensic + 激励分离 | ✅ 强项 |
| fail-closed 闸门 / 守卫设计 | stale 不得绿、checksum、无 T1 不得 fresh | ✅ 强项,补测试后更硬 |
| HITL 设计 | HumanLatch L0/L1 | ✅ 强项 |
| evals | 金标+对照 | ⚠️ 有骨架,缺统计纪律/消融/混淆矩阵(见差距清单 1–3) |
| RAG | 元数据过滤本地检索 | ✅ 覆盖 |
| 工具设计 / Function Calling / MCP | 工具表 + W5–W8 MCP | ✅ 覆盖 |
| 可观测性 | 轨迹可回放 | ⚠️ 缺 trace 树/错误归因(差距清单 2、6) |
| 成本/延迟工程 | 「开始记 token」 | ⚠️ 缺每复验成本、模型权衡曲线(差距清单 5) |
| 对抗鲁棒 | 无工具对照 | ⚠️ 缺语料注入最小检查(差距清单 4) |
| 测试/CI | **未提及** | ❌ 最大遗漏,本期预留 |
| 部署/公开链接 | 不要 Docker/K8s,本地跑 | ⚠️ 可选 Streamlit Cloud,不违约束 |
| fine-tuning | 无 | ✅ 有意不做,写成 ADR 即可 |
| Agent UX | 复验单非聊天界面 | ✅ 差异化亮点;可加轨迹流式回放 |
| 英文材料 | 叙事是英文,文档全中文 | ❌ README/评测报告/文章需英文版,W9–W12 |
| meta 叙事:用 agentic workflow 开发 AI 产品 | wayfinder 地图、AFK agent、triage 全在用 | ✅ 保留地图为公开工件即可 |

## 四、行动归属

- **本期(W1–W4 规格)只做两个预留**:① `tests/` + 闸门单测位(仓库结构工单);② 语料污染位 + seed 复现纪律(存储检索/语料工单)。
- **W5–W8**:评测报告骨架、消融表、成本遥测、CI 金标回归。
- **W9–W12**:英文 README、DESIGN.md、LIMITATIONS、技术文章、口播打磨、公开 demo 链接(可选)。
