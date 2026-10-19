# Contribution Boundary — 可写贡献与禁用话术

> **更新（2026-10）：** 按 Hard-Gold 之后的默认臂变更改写。生产检索默认已是 `hybrid+rerank`。
> **现行口径：** [`docs/ops/口径一页纸.md`](ops/口径一页纸.md) + [`CONTEXT.md`](../CONTEXT.md) + [`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md)。
> **范围：** 对外可写的贡献边界。不是整条发前闭环的交付证明，也不是注册通过或产品就绪。
> **前版：** v0（I0）曾把生产默认写成钉死 bm25，并禁止说「dense / hybrid / rerank 已是生产默认」。该禁令在 2026-10-07 拍板之后不成立，已从黑名单删除。

---

## 1. 生产检索（现行）

- 默认臂：`hybrid+rerank`。精排是本地 `BAAI/bge-reranker-base`，只重排 hybrid 已经给出的 top-10。
- BM25 只作回退：`set_retrieval_switch("bm25")`。它不改常量 `PRODUCTION_RETRIEVAL_MODE`，也不是生产默认。
- 只切回词重叠精排：`set_retrieval_switch("hybrid+rerank_lexical")`。
- 缺向量记 `bm25_fallback`。reranker 失败记 `last_rerank_mode=lexical_fallback`。
- Hard-Gold / #259 的证据可以引用。那不是闭合统计意义上的产品通过，也不是「BM25 统计显著最优」。

决策链见 `docs/evidence/retrieval-decision.md`。I3 骨架规格已归档：`docs/_archive/2026-10/hard-gold.md`（第 6 节是 2026-10-07 变更记录）。现行默认以本页与口径一页纸为准。

---

## 2. 可以写的贡献（诚实）

| 可写 | 含义 |
|------|------|
| **可测 retrieve 子系统** | `claim→查询变换→retrieve→有序 evidence_id + retrieval_mode`；Agent 只当调用方，不可自选生产臂 |
| **评测臂与生产臂分离** | 评测可强制 bm25 / dense / hybrid / hybrid+rerank / bm25_fallback。生产默认是 `hybrid+rerank`。BM25 只经 `set_retrieval_switch("bm25")` 回退 |
| **降级诚实** | 向量失败 → BM25 并标记 `bm25_fallback`，不静默空结果 |

组合说法：检索子系统可独立测量、可降级。2026-10-07 起生产默认是本地 `BAAI/bge-reranker-base` 的 `hybrid+rerank`（只重排 hybrid top-10）。BM25 是回退，不是默认。

Phase A 冒烟复跑的历史入口在归档页 `docs/eval-retrieve.md`（原文 `docs/_archive/2026-10/eval-retrieve.md`）。那一页记录当时「为何仍 BM25」，不要把它的现在时当成现行默认臂。

---

## 3. 禁用话术（黑名单 · 口述与文档均禁）

1. 「我们做了 **agentic RAG**」（Phase A 明确 Out）
2. 「评测 **证明** BM25 **统计显著**最优」，或把冒烟持平说成换臂的统计证明
3. 「**首次**带证据改稿」或对外装形式化 **proof-carrying / PCC**
4. 「**Phase A = 整条发前闭环已交付**」（发前闭环属 V1+；Evidence-bound 属 V1.5）
5. **SaaS / PMF / L5 / 注册通过**（含 `counted_as_pass=true`、领域标杆、产品已就绪）
6. **开放聊天当作正式裁决**（开放 `web_search` 为主路径、聊天化主 UI 已交付、对话改正式裁决）

Related Work 祖先（RARR / PAVE / 事实检查等）可承认。边界话术用「发前新鲜度复验协议」。不要把 v0 冒烟写成已完成的整协议，也不要把现行默认臂说回 BM25。

已删除的旧禁令：「dense / hybrid / rerank 已是生产默认」不得说。2026-10 起生产默认就是 `hybrid+rerank`，这句可以按 §1 的范围说。

---

## 4. 阶段落地记录（冒烟档 · 落地当时的默认臂）

下表是各阶段追加的贡献面。冒烟档不报方差，不作统计显著。落地当时生产默认臂仍是 `bm25` 的句子，只描述那一天，不描述 2026-10-07 之后的现行默认（现行见 §1）。

| 阶段 | 将追加 / 已写入的贡献面 |
|------|------------------------|
| V1 | 单垂直发前路径；T1 落盘；包结论；`patch_events` 起记 |
| I1 | 失败三分法 + 可复盘误判样本（冒烟层口径：不报方差，不作统计显著） |
| V1.5 | Evidence-bound / attested patch（人确认 + 强制再验）；论文主投实验 |
| I2 | 安全三例可复现 demo：越权召回 · 间接注入 · 检索投毒（≠ idea #4；ADR-0030） |
| V2 | 发前钩子（Memo UI+CLI + 入站 check）+ 主张台账只读投影（冒烟·采用层；ADR-0031） |

- **V1 已落地（冒烟，2026-09-29）：** 发前闭环主缝在仓（顾问样例包 `v1-mck-soai`、白名单薄 URL、包结论、人审、`patch_events` 起记）。证据见 `docs/evidence/v1/V1-DoD-CLOSE.md`。档=冒烟。落地当时生产默认臂仍是 `bm25`。本条不是 Hard-Gold，也不是检索臂评测升格。
- **I1 已落地（冒烟，2026-09-29）：** 失败三分法 + 可复盘误判样本已在仓。短索引 `docs/evidence/i1/INDEX.md` 一眼：漏拦/误拦 ≥3，且 ≥1 条 `runnable=true`（金样 `i1-s005`）。证据见 `docs/evidence/i1/ACCEPTANCE.md`。档=冒烟；不报方差；生产 Gate / disposition / HumanLatch 枚举未扩；本条不是 Hard-Gold。
- **V1.5 已落地（冒烟，2026-09-29）：** 表单 Evidence-bound（独立 `propose_patch`/`confirm_patch`、有证覆盖、单条再验、导出）；薄对话本期 Out（未实装、未 stub）；HumanLatch `VALID_ACTIONS` 未扩；发前无 C\|T 开关；Exit 不硬绑「可发」。评估见 `docs/research/V1.5-Evidence-bound补丁设计评估.md`；ADR-0029；硬 Exit `docs/evidence/v15/ACCEPTANCE.md`；关门 `docs/evidence/v15/V15-DoD-CLOSE.md`。档=冒烟。落地当时不是 Hard-Gold，不是 C vs T 显著，不是改默认臂。
- **I2 已落地（冒烟，2026-09-29）：** 安全三例（ACL tenant 过滤 · 注入 Gate 拒绿 · poison 元数据剔除）可复现；注入 1× Lead→Auditor 冒烟 fail-closed；薄表 `docs/security.md`。评估见 `docs/research/I2-安全三例设计评估.md`；ADR-0030；硬 Exit `docs/evidence/i2/ACCEPTANCE.md`；关门 `docs/evidence/i2/I2-DoD-CLOSE.md`。档=冒烟；≠ #4；不是渗透认证，不是安全通过率，不是 Hard-Gold。落地当时不改生产默认臂。
- **V2 已落地（冒烟·采用层，2026-09-30）：** 发前钩子（Memo UI+CLI 同闸 + 入站 check allow/deny）+ 主张台账只读投影（discard∪renew）；零新写表；未做 Word/Notion/开放 webhook 平台；未图谱/CMS；未 Memo 商业裁决；未整包再验挂钩子；未解冻 Studio。评估见 `docs/research/V2-发前钩子与主张台账设计评估.md`；ADR-0031；硬 Exit `docs/evidence/v2/ACCEPTANCE.md`；关门 `docs/evidence/v2/V2-DoD-CLOSE.md`。档=冒烟·采用层；`curl` ≠ 平台已交付；不硬绑「可发」；不报采用率；不是 Hard-Gold。落地当时未改默认臂。

整协议口径（已入库 T1 才能裁定；`web→落盘→再验`；补丁 ⊆ T1；人确认；对话不改正式裁决）以 `docs/ops/口径一页纸.md` 与 `CONTEXT.md` 为准。历史阶段路线见归档的 `docs/roadmap.md`。

---

## 5. 指针

- 面试 / 对外：[`docs/ops/口径一页纸.md`](ops/口径一页纸.md)
- 词表：[`CONTEXT.md`](../CONTEXT.md)（含包结论四值）
- 检索决策链：[`docs/evidence/retrieval-decision.md`](evidence/retrieval-decision.md)
- Phase A 冒烟叙事（历史，页首已标明 2026-10-07 默认已改）：[`accounting-card.md`](./accounting-card.md)
- 规格：`docs/spec/10-PhaseA-RAG.md`（契约；不是本贡献清单的替代）
