# Phase V2 — 发前钩子 + 主张台账 · ADOPTION 规格

> 来源：`/grill-with-docs`（V2）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：`0031`（发前钩子闸与主张台账只读投影）；上游 `0015`（Client Memo）、`0006`（HumanLatch / 作废名单）、`0027`（包结论）、`0029`（补丁导出分轨）  
> 评估：`docs/research/V2-发前钩子与主张台账设计评估.md`  
> 路线图：`docs/roadmap.md` Phase V2  
> **测试主缝（已确认 2026-09-30）：发前钩子放行边界（publish-hook gate）** —  
> `run_id + 该 Run 包结论(可发|需补丁|勿发) + T1 checksum/run 机械新鲜度 + 可选 ack_needs_patch → 同一闸函数 allow/deny → UI Memo 导出、CLI client-memo、入站 POST check 三者行为一致（勿发拒且不落文件；需补丁无 ack 拒；需补丁+ack 放行并强制标明；可发且未漂放行；漂移拒）`  
> 子缝（仅当主缝测不到时）：① 主张台账只读投影形状；② 入站 check 绑定面（本机/token/缺 run_id）；③ `docs/evidence/v2/ACCEPTANCE.md` 冒烟脚本。**优先只暴露主缝。**

---

## Problem Statement

发前路径已能给出包结论、作废/续命与 Evidence-bound 补丁，但顾问在「要发给客户」时仍缺少一步**采用闸**：Client Memo 导出当前不跑复验、UI 无导出按钮、外部打包前无法探同一闸；作废/续命历史虽写在库表，却没有可读的**主张台账**投影。没有发前钩子与台账，Adoption 叙事无法 demo，也容易把检索 embed 或采编平台误当成下一跳。

## Solution

交付 **发前钩子（publish hook）** 与 **主张台账（claim ledger）**：以只读包结论 + T1 checksum/`run_id` 机械新鲜度为确定性闸（不整包再验）；Client Memo 的 UI「导出客户备忘」与 CLI 共用该闸；另提供本机默认的入站 HTTP check（可选 token）供 `curl`/外部工具探闸；`需补丁` 默认拒干净导出，显式 `ack_needs_patch` 才放行并强制页眉标明。主张台账为作废名单 ∪ 续命日志的只读投影（详情旁路 + 可导出 MD），零新写表。Exit 为冒烟采用层，不硬绑「可发」，不宣称插件平台已交付。

## User Stories

1. As a 独立顾问, I want 在发前 UI 一点「导出客户备忘」就受包结论闸约束, so that 勿发包带不走干净附件。
2. As a 独立顾问, I want CLI 导出 Client Memo 与 UI 同一闸语义, so that 脚本工作流不绕过。
3. As a 独立顾问, I want 勿发时导出被拒绝且不生成 Memo 文件, so that 假附件不落盘。
4. As a 独立顾问, I want 需补丁默认不能「干净导出」, so that 缺口不会装成可发。
5. As a 独立顾问, I want 显式确认 ack_needs_patch 后仍可带走缺口备忘且页眉标明需补丁, so that 诚实采用成立。
6. As a 独立顾问, I want 可发且 T1 checksum 未漂移时可导出, so that 正常发前路径通。
7. As a 独立顾问, I want checksum 或 run 机械新鲜度漂移时被拒绝, so that 过期快照不能装新鲜。
8. As a 独立顾问, I want 导出前不强制整包再跑 Lead, so that 采用闸便宜可测。
9. As an 外部工具集成者, I want POST 入站 publish-hook check 并收到 allow/deny JSON, so that 打包前能探同一闸。
10. As an 外部工具集成者, I want 请求必填 run_id, so that 闸绑在发前 Run 而非含糊 claim 列表。
11. As an 外部工具集成者, I want 缺 run_id 时 fail-closed, so that 无绑定不放行。
12. As an 外部工具集成者, I want 可传 ack_needs_patch 与 UI/CLI 同语义, so that 三出口一致。
13. As a 安全意识用户, I want 入站钩子默认只听本机, so that 冒烟不暴露公网攻击面。
14. As a 安全意识用户, I want 可选共享密钥头校验, so that 需要时可加薄鉴权。
15. As a 安全意识用户, I want 文档声明公网暴露须另票, so that 不把 curl 冒烟称作 webhook 平台。
16. As a 复验操作者, I want Run 详情旁路看到作废与续命的 claim_id 列表, so that 主张历史可查。
17. As a 复验操作者, I want 台账默认可折叠, so that 职人视图不被审计淹没。
18. As a 复验操作者, I want 可导出台账 Markdown, so that 面试/自用可带走。
19. As a 复验操作者, I want 台账只读不新写库表, so that 作废名单单一真相不被双写破坏。
20. As a 复验操作者, I want 续命出现在台账但不进作废名单, so that 与既有闸语义一致。
21. As a 报告读者, I want Memo 仍遵守 Client Memo 字段集且无商业裁决句, so that ADR-0015 不破。
22. As a 报告读者, I want Memo 仍无 Lead/Critic 轨迹, so that 对客附件干净。
23. As a 报告读者, I want 需补丁放行时页眉/载荷显式「需补丁」, so that 读者不被绿章误导。
24. As a 发前操作者, I want 发前列表或详情有导出客户备忘入口, so that 「要发了」可点到。
25. As a 发前操作者, I want 闸失败时看到与钩子 code/message 同构的短中文, so that UI/CLI/HTTP 可对照。
26. As a 产品负责人, I want 产品词叫发前钩子与主张台账而非 Embed, so that 不与检索向量撞车。
27. As a 产品负责人, I want 本期不做 Word/Notion/开放 webhook 平台, so that 不偷渡旧 Phase C。
28. As a 产品负责人, I want sheet/补丁包同闸可另票加分, so that 不挡冒烟 Exit。
29. As a 产品负责人, I want 不扩 HumanLatch 动词、不用 renew 改正文, so that 闩与补丁分缝保留。
30. As a 产品负责人, I want 不改生产默认检索臂、不解冻 Studio, so that Hard-Gold/冻结纪律成立。
31. As an 验收者, I want Exit 硬条含 Memo 闸正确 + curl allow/deny 各≥1 + 台账可见本次 discard/renew + v2 ACCEPTANCE, so that 采用可勾。
32. As an 验收者, I want ACCEPTANCE 文首声明冒烟采用层且不报采用率, so that 不升格统计。
33. As an 验收者, I want Exit 不硬绑包结论可发, so that 与 V1.5 纪律一致。
34. As an 验收者, I want 预锁脚本禁事后改「什么算点到」, so that 防 HARKing。
35. As an 架构守护者, I want UI/CLI/HTTP 共用同一闸函数, so that 三套语义不漂移。
36. As an 架构守护者, I want 闸只读 disposition 与 checksum 新鲜度, so that 确定性可测、零 LLM Exit。
37. As an 架构守护者, I want 台账投影自 invalidation_list 与 latch_log, so that 写路径仍唯一经 human_latch。
38. As an 架构守护者, I want 台账与 patch_events 分缝, so that 人审历史≠改稿对照账。
39. As an 面试讲解者, I want 能讲清钩子≠embedding、台账≠新表、curl≠插件平台, so that mid 不被打穿。
40. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按序实现。
41. As a 回归守护者, I want 既有 disposition/latch/Memo 字段/prepublish 回归不红, so that V1/V1.5 不回退。
42. As a 文档维护者, I want README/路线图写明 V2 In/Out/Exit 与 C′ Backlog, so that 叙事一致。

## Implementation Decisions

### 主缝与模块

- **主缝**：发前钩子放行边界（见文首）。对外可测：给定 Run 态与 ack 标志 → allow/deny 与是否落 Memo 文件；UI、CLI、入站 HTTP **同结果**。
- **共享闸用例**：新建逻辑服务（名称在实现中自洽即可）输入至少含 `run_id`、当前 disposition、checksum/新鲜度快照、`ack_needs_patch`；输出 `allow`、`disposition`、`code`、`message`（及可选页眉约束）。**禁止**三出口平行 if/else。
- **Client Memo**：在既有导出契约上**套闸**；通过才调用既有 Memo 渲染/写文件；失败零写。UI 增加「导出客户备忘」入口（发前列表或 Run 详情增量，不新造第三套主导航）。
- **CLI**：`client-memo` 子命令走同一闸；支持等价 ack 标志（标志名实现自洽，语义对齐 `ack_needs_patch`）。
- **入站 check**：HTTP POST；必填 `run_id`；可选 `ack_needs_patch`；deny 返回 403 或 409 + JSON 体；默认绑定本机回环；可选环境变量 token 头校验。
- **新鲜度**：相对该 Run 已记录的 T1 checksum（或约定 run 绑定键）比对；漂移 → deny。不在此路径触发整包 Agent 再验。
- **主张台账**：只读合并 `invalidation_list` 与 `latch_log` 中 discard/renew；投影 API 或视图挂 Run 详情旁路；另支持 Markdown 导出。零 DDL 新写表（只读查询既有表）。
- **样例/Exit**：沿用顾问垂直 / `v1-mck-soai` 路径可复现；ACCEPTANCE 预锁见 ADR-0031。

### API / 契约（逻辑，不钉文件路径）

- `evaluate_publish_hook(run_id, ack_needs_patch?, …) → {allow, disposition, code, message, …}`
- `export_client_memo_gated(…)`：先 evaluate，allow 才写 Memo；需补丁+ack 时强制页眉/字段标明。
- `POST …/publish-hook/check`：体含 `run_id`、可选 `ack_needs_patch`；响应同构。
- `get_claim_ledger(run_id|scope)` / `export_claim_ledger_md(…)`：只读投影。
- **禁止**：出站通知 webhook 顶替 check；公网默认监听；Memo 写商业裁决；新建双写作废写路径；扩 latch 动词。

### 历史项目代码供参考 · 改编标注

| V2 能力 | 参考 | 处置 |
|---------|------|------|
| 包结论读取 | 本仓 `disposition_for_claims` / 发前 Registry | **复用**；闸只读 |
| Client Memo 渲染 | 本仓 export client-memo / ADR-0015 | **套闸**；字段集不扩商业裁决 |
| 作废/续命真相 | `invalidation_list` + `latch_log` / ADR-0006 | **只读投影**；不改写路径 |
| 发前 Run 键 | PrepublishRegistry / active_run_id | **绑定**钩子 run_id |
| 补丁导出 | evidence_bound_export | **分轨**；同闸仅加分另票 |

**必须重写 / 不得当默认抄入**

- 检索 embed / 向量化冒充本阶段  
- Word/Notion/开放 webhook 平台、目录 drop 作唯一外部形态  
- 导出路径强制整包 Lead 再验  
- 新 claim_ledger 写表双写作废名单  
- 把 patch_events 当作人审台账  

## Testing Decisions

- **好测试**：只断言主缝外部行为（三出口同 allow/deny；勿发/无 ack 需补丁零写文件；ack 后页眉含需补丁；漂移拒；缺 run_id 拒），不锁 CSS/像素与 LLM。
- **主测**：闸表驱动（disposition × ack × 新鲜度）；UI/CLI/HTTP 适配层各至少一条委托同闸；台账投影含 discard 与 renew 且 renew ∉ 作废名单；回归 disposition/latch/Memo 字段/prepublish。
- **Prior art**：`test_disposition.py`、`test_client_memo_export` / alpha INV-2、`test_prepublish_*`、`test_ui_latch.py`、`test_renew.py`（作废名单语义）；gate1 零 LLM CI——V2 Exit **硬条零 LLM**。
- **ACCEPTANCE**：实现后写 `docs/evidence/v2/ACCEPTANCE.md`（冒烟文首；硬条含 curl allow/deny；加分：sheet/补丁同闸、页眉带 checksum 等与硬条分离）。

## Out of Scope

- Word/PPT/Notion 插件；开放公网 webhook 平台；目录 drop 监视器（→ Backlog C′）
- 大图谱；全量采编 CMS
- 内部 sheet / Evidence-bound 补丁包同闸（加分另票，非硬 Exit）
- 导出路径强制整包再验；出站「通知 webhook」顶替 check
- Memo 商业裁决；扩 HumanLatch；renew 改正文；新表双写作废
- 改生产默认检索臂；解冻 Studio；Hard-Gold；#8 并行
- 把 curl 冒烟升格为 webhook 平台已交付；报采用率/方差
- Exit 硬绑包结论「可发」

## Further Notes

- **Seams 确认**：主缝「发前钩子放行边界」已于 2026-09-30 用户确认。
- **DoD / Exit 对照路线图与 ADR-0031**：Memo 闸正确；curl 入站 allow/deny 各 ≥1；台账可见本次 discard/renew；`docs/evidence/v2/ACCEPTANCE.md`；不硬绑可发。
- **下一跳**：`/to-tickets` → `/enrich-tickets` → `/before-implement` → `/implement`。
- **规格 issue**：[GitHub #226](https://github.com/luxingjiang1993/FreshLatch/issues/226) `ready-for-agent`。
- **决议**：grill 四件套已落（评估 + ADR-0031 + CONTEXT + roadmap）；本规格为实现权威用户故事面。
- **I2 / V1.5**：已 DONE（冒烟）；本规格不改 ACL/poison/注入契约，不扩补丁 API。
