# Phase V1 — 发前闭环（Pre-publish loop）规格

> 来源：`/grill-with-docs`（V1）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：`0027`（垂直 / 包结论 / 薄 URL / patch_events）；上游 `0016`（T1 三卡）、`0002`（复验单 UI）、`0006`（HumanLatch）  
> 评估：`docs/research/V1-发前闭环垂直与包结论设计评估.md`  
> 路线图：`docs/roadmap.md` Phase V1  
> **测试主缝（已确认 2026-09-29）：发前 Run 边界** —  
> `主张集 + 合法 T1（三卡|薄 URL）→ 复验/规则闸 → 包结论(disposition) → 人审 → 发前列表/Run 详情投影 + patch_events 追加`  
> 子缝（仅当主缝测不到时）：① disposition 纯函数聚合；② 薄 URL 入库 fail-closed；③ patch_events 追加写。**优先只暴露主缝。**

---

## Problem Statement

顾问已签发的主张（定价、份额、采用率等）在对外发出前，需要证明「现在仍可复验」。仓库已有复验单、T1 三卡与 HumanLatch，但缺少：**单一顾问垂直的样例包**、**报告级包结论（可发/需补丁/勿发）**、**发前列表**、以及 **web→落盘→再验** 的薄 URL 入口与 **`patch_events` 记账**。没有这些，发前路径无法对外 demo，也无法为 V1.5 / 论文蓄对照数据。

## Solution

锁定唯一垂直为**顾问报告**，以 McKinsey State of AI 公开洞察为样例主包（T0≈2025-03 波 → T1≈2025-11 波）。在现有复验主链上增加：包结论新层、发前列表、薄 URL（仅 `www.mckinsey.com`）、JSONL `patch_events`（后台 C/T）。Run 详情复用复验单并加包结论条。不改生产检索默认臂；不做薄对话改裁决；不整本镜像咨报 PDF。

## User Stories

1. As a 独立顾问, I want 发前只服务「顾问报告」这一垂直, so that 叙事与样例不与研报/合规并行打架。
2. As a 独立顾问, I want 样例主张来自可指认的 McKinsey State of AI 出处, so that 面试与 demo 够「高大上」且可追溯。
3. As a 独立顾问, I want 仓内只存主张+摘录+URL/日期, so that 不把整本咨报当开源数据集再分发。
4. As a 独立顾问, I want 一条发前路径：选 T1 → 复验 → 看包结论 → 人审 → 列表可追踪, so that 我能演示「要发了」之前少翻车。
5. As a 独立顾问, I want 未选定合法 T1 不得开始定论, so that 无最新事实不假装绿灯。
6. As a 语料管理员, I want 继续使用上传 md / 粘贴确认 / 合成包三卡, so that 既有入口不回归。
7. As a 语料管理员, I want 薄 URL：粘贴一条 `www.mckinsey.com` 链接即可抓取落盘, so that 能演示 web→落盘→再验。
8. As a 语料管理员, I want 非白名单域名被拒绝且不入库, so that 不会做成开放爬虫。
9. As a 语料管理员, I want 超时/网络失败显式报错并可回落粘贴, so that 反爬不会卡死 demo。
10. As a 语料管理员, I want 非文本或空正文失败不入库, so that 脏页不会污染 T1。
11. As a 语料管理员, I want 落盘前校验失败零写, so that fail-closed。
12. As a 语料管理员, I want 落盘后有 checksum 可追, so that 轨迹能指认 T1 版本。
13. As a 语料管理员, I want PDF URL 自动解析本期不做（另票）, so that V1 不抢发前闭环带宽。
14. As a 复验操作者, I want 既有「开始复验」与规则闸行为保持, so that V1 不重写闸语义。
15. As a 复验操作者, I want 主张级仍用 fresh/stale/unknown/void, so that 词表不漂移。
16. As a 报告读者, I want 包级结论仅三值：可发 / 需补丁 / 勿发, so that 对人可讲、不发明第四套词。
17. As a 报告读者, I want 未收口 stale → 勿发, so that 红灯未处理不能装可发。
18. As a 报告读者, I want 无未收口 stale 但有 unknown/缺口 → 需补丁, so that 缺口可见。
19. As a 报告读者, I want 全 fresh（闸+双判过）且无人审 → 可发, so that V1 demo 不被强制人签拖垮。
20. As a 报告读者, I want 红灯均已 discard/renew 收口且无未处理 unknown → 可发, so that 人审收口后可放行。
21. As a 发前操作者, I want 发前列表显示标题/来源、包结论、更新时间、Run 状态, so that 一眼看到哪包能发。
22. As a 发前操作者, I want 从列表进入 Run 详情, so that 能下钻。
23. As a 发前操作者, I want Run 详情基于现有复验单并增加包结论条, so that 不造第三套详情 UI。
24. As a 发前操作者, I want 详情仍能作废/续命, so that 人审路径不断。
25. As a 发前操作者, I want 详情能看到 T1 checksum 列表与逐条闸结果, so that 可追责。
26. As a 发前操作者, I want 详情能链到轨迹, so that 排障可做。
27. As a 职人, I want 默认职人视图不被包结论工程词淹没, so that 成交面仍干净。
28. As an 审计者, I want 审计视图仍可看 Lead/Critic/轨迹, so that 面试可切深。
29. As a 论文/预实验记录者, I want 自 V1 起每次改稿相关事件写入 patch_events JSONL, so that C vs T 有账。
30. As a 论文/预实验记录者, I want 字段至少含 claim_id、before_disp、patch_span、t1_ids、human_confirm、reverify、minutes、arm、ts、actor, so that 与路线图预登记对齐。
31. As a 论文/预实验记录者, I want 人手补丁也走同一 schema, so that 不另起账本。
32. As a 产品负责人, I want C vs T 切换不出现在发前 UX, so that 产品不变成实验台。
33. As a 产品负责人, I want V1 不做薄对话, so that 不与 V1.5 Evidence-bound 抢范围。
34. As a 产品负责人, I want 对话不得改正式 disposition, so that 硬规则成立。
35. As a 架构守护者, I want 生产默认检索臂仍为 bm25, so that Hard-Gold 前不换臂。
36. As a 架构守护者, I want Agent 不可自选 production retrieval_mode, so that Phase A 纪律保留。
37. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按序实现。
38. As an 面试讲解者, I want 规格标明历史项目参考改编点与禁止照抄点, so that Provenance 可写。
39. As a 合规叙事者, I want README/文档写明单一垂直=顾问报告, so that DoD「垂直已写进文档」可勾。
40. As a 评测工程师, I want 至少抽 1 条映射用例核对包结论, so that 聚合不靠口述。
41. As a 安全意识用户, I want 抓取仅限白名单主机名精确匹配约定, so that 子域绕过需显式另决。
42. As a 回归守护者, I want thesis-1 / QuoteTTL 仍可作软 Port 烟测但不算第二垂直, so that 旧包不废。

## Implementation Decisions

### 主缝与模块

- **主缝**：发前 Run 边界（见文首）。对外可测行为：给定 Run 输入（主张集 + T1 选择含薄 URL）→ 产出包结论 + 可追责轨迹（含 T1 checksum）+ 可选 patch_events 行；列表/详情只是投影。
- **disposition**：纯函数聚合模块（输入主张态+人审收口标志 → 可发|需补丁|勿发）；UI/API 只消费结果，禁止平行发明状态词。
- **薄 URL**：T1 来源增量服务：校验 Host ∈ {`www.mckinsey.com`} → GET → 抽取正文 → 结构锚切块 → ingest；失败四态映射为明确错误码/短中文，零写。
- **发前列表**：薄 API + UI 壳；Run 详情路由到既有复验单并注入包结论条。
- **patch_events**：追加写 JSONL（目录 `data/patch_events/`）；后台/脚本写入；发前 UX 不暴露 arm 切换。
- **样例包**：新建顾问垂直数据包（主张清单 + T0/T1 摘录 md + 出处元数据）；不提交整本 McKinsey PDF 二进制为开源语料。

### API / 契约（逻辑，不钉文件路径）

- 扩展 T1 来源状态：增加 `url` 入口与失败四态枚举。
- 增加包结论查询（随 Run/复验结果返回）。
- 发前列表：列出 Run 摘要字段（标题/来源、disposition、更新时间、状态）。
- HumanLatch 既有 decide/rerun/status 保留；不因包结论绕过闸。

### 历史项目代码供参考 · 改编标注（强制）

> 索引：`docs/research/参考代码盘点.md`；物理树常见于课程仓 `历史项目代码供参考/`（及同级 CASE / project 目录）。凡工单触达下列改编，须在 Provenance 写 **kind=adapt** 并点名下方条目。

| V1 能力 | 参考（历史项目） | 处置 |
|---------|------------------|------|
| 发前列表 / 控制台列表壳 | **project 多agent** `mission_control/app.py`（FastAPI+HTML 人审控制台） | **改编**布局与列表态；业务字段换 Run/disposition，勿抄其编排角色名当 FreshLatch 词表 |
| 复验单详情增量 | 本仓既有 UI（ADR-0002）+ 同上 mission_control 审批条 | **以本仓为主**；mission_control 仅对照「列表→详情」信息架构 |
| 人审门闩 | 本仓 HumanLatch（ADR-0006）；设计祖先 **project 多agent** `runner.py` blocked_for_human | **不重写门闩**；禁止用 OpenManus `ask_human` 替换既有 interrupt 链 |
| HTTP 抓取薄 URL | 课程 **05_实战** feed/HTTP 拉取习惯；**CASE-MCP / Tavily** | **仅可借鉴**「请求+失败可见」；**禁止**照抄 Tavily/开放搜索当 c′ |
| 正文落盘与版本感 | **CASE-知识库处理** 版本/健康度脚本；**project 多agent** `rag.py` 元数据 | **改编** checksum/出处字段习惯；切块仍本仓 `## pN` |
| 报告式汇总条 | **RAG-cy** Streamlit 报告 UI | **不优先**；V1 坚持复验单 HTML 增量，避免第二 UI 栈 |
| 混合召回 / rerank | **CASE-高效召回** / **CASE-rerank** | **本期禁止改生产默认臂**；与 V1 Out 一致 |

**必须重写 / 不得当默认抄入**

- 开放 MultiQuery / 聊天 PDF QA / FAISS 换存储真相  
- 任意域名抓取、静默失败空入库  
- 用历史项目「approve_promotion」语义覆盖 FreshLatch discard/renew 词表  
- 把 C/T 实验开关做进发前主按钮

## Testing Decisions

- **好测试**：只断言主缝外部行为（合法/非法 URL → 是否入库；给定主张态向量 → disposition；列表字段；patch_events 追加一行可读），不锁 HTML 结构细节或抓取库品牌。
- **主测**：disposition 聚合表驱动；薄 URL 四失败态 + 白名单通过冒烟（可用 fixture HTTP，不打真网 CI）；发前列表 API 字段；patch_events 写后读；既有 `test_ui_t1_source` / latch 回归不红。
- **Prior art**：`tests/unit/test_ui_t1_source.py`、`test_ui_latch.py`、`test_rule_gate.py`、`test_override_latch.py`；gate1 零 LLM CI 纪律——真网抓取标手动/里程碑，白名单与失败态用夹具。
- **映射抽检**：至少 1 条金标/样例主张集核对 disposition（grill-prep 待勾项）。

## Out of Scope

- 多垂直并行；研报/合规主包（可另阶段）
- 薄对话 / Evidence-bound 补丁 UX（V1.5）
- 对话改正式 disposition；C/T 进发前 UX
- Hard-Gold、改生产 retrieval 默认臂、High-Recall SKU
- PDF URL 自动 `pdf_anchor` 入库（另票）
- 开放爬虫、多域名白名单扩张、自动盯梢
- Studio、Memory 大叙事、跨 Provider 对照作硬关门
- 整本 McKinsey PDF 开源再分发
- span 字符级点回加厚（非 V1 Exit 必需）

## Further Notes

- **Seams 确认**：主缝「发前 Run 边界」已于 2026-09-29 用户确认。下一跳 `/to-tickets`。
- **DoD 对照路线图**：未归档不得定论；disposition 可追责；人审走通；垂直写入 README；patch_events schema+开始记账。
- **下一跳**：`/to-tickets` → `/enrich-tickets`；涉及上表历史参考的票必须写 Provenance（path 指向 `历史项目代码供参考/...` 或盘点文档锚点）。
- **I0**：已 DONE；本规格不得宣称检索臂评测结论升格。
