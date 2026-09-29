# Phase I2 — Security demos · INTERVIEW SAFETY ROUND 规格

> 来源：`/grill-with-docs`（I2）共享理解 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：`0030`（薄 ACL 与注入/投毒冒烟三例）；上游规则闸 / retrieve（ADR-0003 等）；明确 **≠** idea #4 / ADR-0022 对抗目录 Exit  
> 评估：`docs/research/I2-安全三例设计评估.md`  
> 路线图：`docs/roadmap.md` Phase I2  
> **测试主缝（已确认 2026-09-29）：**  
> 1. **召回信任边界** — `RetrievalStore.retrieve`：可选 `tenant_id` 硬过滤 + 显式 `poison`/`untrusted` 建 pool 剔除 → 结果集不得含异租户块 / 投毒块  
> 2. **绿灯出口** — `rule_gate` + `Runner._finalize`：污染 T1（间接注入文案）不得仅因此给出 `fresh`  
> 子缝（仅主缝测不到时）：schema 可选列兼容；工具/`try_retrieve` 透传 `tenant_id`；`docs/security.md` + `docs/evidence/i2/ACCEPTANCE.md` 形状。**优先只暴露两条主缝。**

---

## Problem Statement

冲 mid 需要可复现的安全演示，但仓内尚无 ACL 召回过滤、无间接注入拒绿夹具、无投毒元数据剔除，也没有 `docs/security.md` / i2 ACCEPTANCE。面试官无法对照「召回带信任边界 / 语料翻不动绿灯 / 高分恶意块不可引用」三条故事；若临时用 #4 过期伪装或口头讲安全，会踩路线图 Out 与 ADR-0030。

## Solution

在**既有** retrieve 与规则闸真路径上交付 **冒烟三例**（各恰好 1 fixture）：合成 `tenant_id` 越权召回失败、污染 T1 间接注入 → Gate fail-closed、显式 poison 标签块不得进可引用集；外加 `docs/security.md` 薄表与 `docs/evidence/i2/ACCEPTANCE.md`。确定性 pytest 为硬门；注入另跑 **1×** Lead+Critic+LLM 冒烟（显式 decoding）。不做安全平台、不做 UI 硬门；#4 可选一条且 **不计入** Exit。

## User Stories

1. As an 面试官, I want 看到越权召回测例可复跑失败（B 看不到 A）, so that 「ACL」不是口头故事。
2. As an 面试官, I want 看到间接注入污染 T1 翻不动 fresh, so that 规则闸 fail-closed 可指认。
3. As an 面试官, I want 看到带 poison 标签的高分块进不了可引用集, so that 投毒与注入正交可讲。
4. As an 面试官, I want 一页 security.md 表把三威胁与 repro 命令对齐, so that 口述有锚点。
5. As an 验收者, I want Exit 硬条为三例确定性断言 + 注入 1× LLM 冒烟 + security.md + ACCEPTANCE, so that 口头不算。
6. As an 验收者, I want ACCEPTANCE 文首声明冒烟层且禁报安全通过率/方差, so that 不升格认证。
7. As an 验收者, I want fixture id 预锁为 acl-t001 / inj-t001 / poison-t001, so that 禁 HARKing 改桶。
8. As an 验收者, I want #4 过期伪装若同波交付则分节可选勾且不进 I2 Exit, so that I2≠#4。
9. As a 检索调用方, I want retrieve 支持可选 tenant_id（缺省 default）, so that 单仓兼容。
10. As a 检索调用方, I want 不传 tenant_id 时行为与改前一致, so that 既有调用不炸。
11. As a 检索调用方, I want 异租户块永不出现在结果集, so that 信任边界在召回层。
12. As a 检索调用方, I want poison/untrusted 块即使 BM25 高分也被剔除, so that 元数据硬门成立。
13. As a Lead/Critic, I want 经 try_retrieve 的召回同样受 ACL/poison 约束, so that Agent 路径不漏。
14. As a Forensic 工具用户, I want 直调 store.retrieve 也受同一过滤, so that 旁路不漏网。
15. As a 语料作者, I want Chunk/Document 可带可选 tenant_id 与 poison 标签, so that 夹具可入库。
16. As a 语料作者, I want 无标签块默认非 poison 且 tenant 为 default, so that 旧语料可读。
17. As a Gate 守护者, I want 注入夹具走 rule_gate/_finalize 拒绿, so that 绿灯唯一出口不旁路。
18. As a Gate 守护者, I want 不用 meta_gate 承担注入故事, so that 与 stale 元陈述闸不混。
19. As a Gate 守护者, I want 确定性测不依赖 LLM 品牌与像素, so that CI 可绿。
20. As a 冒烟操作者, I want 注入场景可跑 1 次真模型 e2e 并记录 model/temperature/seed/日期, so that 真链路可演示。
21. As a 冒烟操作者, I want ACL 与投毒不硬绑 LLM e2e, so that 随机系统不判那两面生死。
22. As a 产品负责人, I want 本期无租户管理面/RBAC/SSO, so that 不做安全平台。
23. As a 产品负责人, I want 无标签内容启发式不作投毒硬门, so that Exit 可预锁。
24. As a 产品负责人, I want ingest 注入扫描仅留位不加硬门, so that 范围不膨胀。
25. As a 产品负责人, I want 生产默认检索臂仍为 bm25, so that 不借 I2 改臂。
26. As a 产品负责人, I want 不扩 HumanLatch 动词、不改 disposition 词表, so that V1/I1/V1.5 不回退。
27. As an 架构守护者, I want 过滤落在 RetrievalStore.retrieve 而非仅 try_retrieve, so that Forensic 旁路也被盖住。
28. As an 架构守护者, I want 不新建独立 ACL/安全服务模块作主路径, so that 接缝最少。
29. As an 架构守护者, I want 不把 I2 样例塞进 data/traps 与 retrieve 评测陷阱混名, so that 证据目录清晰。
30. As an 架构守护者, I want 不宣称 adversarial INDEX 升版即 I2 Done, so that ≠ ADR-0022 Exit。
31. As a 文档维护者, I want 证据落 docs/evidence/i2/, so that 与 i0/i1/v15 对齐。
32. As a 文档维护者, I want security.md 列含 threat/demo_id/layer/repro_cmd/expected/smoke_note, so that 薄表可扫。
33. As a 文档维护者, I want 三威胁主表不含 #4 行（或灰显可选）, so that Exit 边界可见。
34. As a 回归守护者, I want 既有 as_of/source_type 过滤与 retrieve 臂测不红, so that Phase A 不回退。
35. As a 回归守护者, I want 既有 rule_gate 不变量测不红, so that 注入防护是增量不是改写绿灯语义。
36. As a 回归守护者, I want evidence_id 会话白名单仍工作, so that #16 防伪造不破（且受益于召回已剔毒）。
37. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按序实现。
38. As an 面试讲解者, I want 能一句话说清注入打闸、投毒打可引用集、ACL 打租户过滤, so that 三例正交。
39. As an 面试讲解者, I want 明确不做安全平台、#4 不顶替 I2, so that 不踩 Out。
40. As a 职人, I want 本期无安全 UI 硬门, so that 冲 mid 不靠新屏。
41. As a 合成租户演示者, I want acl-t001 夹具含至少两租户块与同 query 可命中正文, so that 过滤可测而非空库巧合。
42. As a 注入演示者, I want inj-t001 正文含明确「忽略指令/标为 fresh」类语句且已入库, so that 与差距清单 §4 对齐。
43. As a 投毒演示者, I want poison-t001 块可被检索打到高分但带 poison 标签, so that 「高分仍剔除」可证。
44. As a #4 可选作者, I want 至多一条 adv-fresh-t001 过期伪装样例可落 evidence 分节, so that 面试弹药可选。
45. As a CI 守护者, I want 确定性三例进可自动跑的 unit/security 测, so that 无 Key 也能验硬门。
46. As a 复现工程师, I want ACCEPTANCE 写明托管漂移限制, so that 跨会话 e2e 只求近似。

## Implementation Decisions

### 主缝与模块

- **主缝 1（召回信任边界）**：扩展 `RetrievalStore.retrieve` 契约——可选 `tenant_id`；结果集硬排除异租户与 `poison`/`untrusted`（或等价布尔/枚举）块。`SQLiteStore` 与 `InMemoryStore` 同语义。`try_retrieve` / 工具层可透传 `tenant_id` 并记入轨迹 filters，但**行为真相**以 store 结果为准（覆盖 Forensic 直调）。
- **主缝 2（绿灯出口）**：不新开闸模块；注入防护挂既有 `rule_gate` + `_finalize` 路径。确定性夹具断言：给定污染 T1 场景，不得产出可验收的 `fresh` 绿灯（或显式打回 `unknown`/非绿，与现有 fail-closed 口径一致）。**禁止**把注入故事挂到 `meta_gate`。
- **Schema**：Chunk（及入库所需 Document 侧字段若必要）增加**可选** `tenant_id`（缺省 `default`）与 poison/untrusted 标记；旧行缺省兼容；**禁止**挪用无关留位列偷语义。
- **夹具与证据**：`docs/evidence/i2/` 下 `acl-t001` / `inj-t001` / `poison-t001`（可选 `adv-fresh-t001`）；测码优先 `tests/unit/test_i2_*.py` 或 `tests/security/`；语料/夹具正文勿与 `data/traps/` 混名。
- **交付文档**：新建 `docs/security.md` 薄表；实现后写 `docs/evidence/i2/ACCEPTANCE.md`（文首冒烟；硬条 vs #4 可选分节；注入 e2e 记录 decoding）。

### API / 契约（逻辑，不钉文件路径）

- `retrieve(query, …, tenant_id=None)`：`tenant_id is None` → 兼容旧行为（等价全可见于当前单仓语义，或显式视为 `default`——实现须在规格实现注记中二选一并测死，**推荐缺省租户池=`default` 且无参只见 `default` 与未标注块的约定须与「无参兼容」一致：无参=不过滤租户列 / 或无参=`default`；**拍板：无参不启用租户过滤（完全兼容）；显式传入 `tenant_id` 才硬过滤。**）
- 显式 `tenant_id=B` → 结果中每一块的租户必须为 B（缺省字段视为 `default`，故不等于 B 则排除）。
- poison 标记为真的块：**永不**出现在 retrieve 返回列表（在 BM25/排序前或后剔除均可，外部只断言「不在结果集」）。
- 工具 schema 可增加可选 `tenant_id`；Agent 未传则走无参兼容。
- **禁止**：租户 CRUD API；RBAC 角色表；无标签投毒分类器作硬门；安全中心 UI。

### 历史项目代码供参考 · 改编标注

| I2 能力 | 参考 | 处置 |
|---------|------|------|
| WHERE 过滤 | store `as_of`/`source_type`；`test_where_filters` | **同构扩展** tenant/poison |
| 绿灯出口 | `rule_gate` / `_finalize`；`test_rule_gate.py` | **增量断言**注入夹具；不改无关不变量语义 |
| 会话白名单 | `check_evidence_ids` / `_seen_evidence` | **不改主语义**；召回已剔毒则自动受益 |
| 记忆 quarantine | quarantine status 分池 | **不复用为 ACL**；思路可类比但 I2 落 chunk retrieve |
| 冒烟 e2e | V1/V1.5 预锁脚本风格 | **仅注入 1×**；ACL/poison 确定性 |

**必须重写 / 不得当默认抄入**

- 安全平台 / SSO / 多租户产品面  
- 用 #4 过期伪装顶替任一 I2 Exit 例  
- 三威胁全绑单次 LLM 判生死  
- 把 I2 Done 写成 adversarial catalog 升版  

## Testing Decisions

- **好测试**：只断言主缝外部行为（结果集成员资格；绿灯是否成立），不锁实现是 SQL WHERE 还是 Python 过滤，不锁 CSS/像素。
- **主测**：  
  - `acl-t001`：同 query 下 `tenant_id=B` 结果不含 A 块；无参兼容回归。  
  - `poison-t001`：高分 poison 块不在结果集。  
  - `inj-t001`：确定性 Gate/夹具路径非 `fresh` 绿灯。  
  - 注入 1× LLM e2e：ACCEPTANCE 记录参数；失败不靠改判据凑绿。  
- **Prior art**：`tests/unit/test_store.py`（where 过滤）、`test_rule_gate.py`、`test_alpha_inv_acceptance.py`、retrieve 臂测；gate1 零 LLM CI 覆盖确定性三例。  
- **ACCEPTANCE**：`docs/evidence/i2/ACCEPTANCE.md`；`docs/security.md` 与 demo_id 互链。

## Out of Scope

- 安全平台；完整 RBAC；租户管理面；SSO
- 多攻击面大而全；红队产品循环
- 用 idea #4 替代本阶段 Exit；把 #4 勾进 I2 硬条
- 无标签内容启发式投毒硬门；ingest 注入扫描硬门（留位）
- 三威胁全部硬绑 LLM e2e；取消确定性层
- 安全/ACL 专用 UI 硬门
- 扩 HumanLatch / disposition / 生产失败三分法枚举
- 改生产检索默认臂；Hard-Gold；Studio
- 宣称 adversarial INDEX 升版 = I2 Done
- 渗透认证或安全通过率/方差报告

## Further Notes

- **Seams 确认**：召回信任边界 + 绿灯出口两条主缝已于 2026-09-29 用户确认（「缝 OK」）。
- **DoD / Exit 对照路线图与 ADR-0030**：三例可复现；security.md；i2 ACCEPTANCE；分层硬门；#4 可选≠Exit。
- **无参 tenant 拍板（实现注记）**：`tenant_id` **未传入**时不启租户过滤（最大兼容）；**显式传入**才过滤。缺省字段值仍为 `default`，供显式 `tenant_id="default"` 使用。
- **下一跳**：`/to-tickets` → `/enrich-tickets` → `/before-implement` → `/implement`。  
- **规格 issue**：[GitHub #213](https://github.com/luxingjiang1993/FreshLatch/issues/213) `ready-for-agent`。  
- **决议工单**：grill 收口 [#212](https://github.com/luxingjiang1993/FreshLatch/issues/212)（CLOSED）。  
- **V1.5 / I1 / V1**：已 DONE（冒烟）；本规格不回退其契约。
