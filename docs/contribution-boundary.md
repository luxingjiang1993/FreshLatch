# Contribution Boundary v0 — Phase A / retrieve 子系统

> **版本：** v0（I0）  
> **范围：** 可测 retrieve 子系统与默认臂纪律；**不是**整条发前闭环已交付证明。  
> **后续：** V1 / I1 / V1.5 将追加协议层贡献声明（见 §3 占位）。  
> **评估：** `docs/research/I0-冒烟层与数字真相源设计评估.md`

---

## 1. 本阶段可写的贡献（诚实）

| 可写 | 含义 |
|------|------|
| **可测 retrieve 子系统** | `claim→查询变换→retrieve→有序 evidence_id + retrieval_mode`；Agent 只当调用方，不可自选生产臂 |
| **评测臂与生产臂分离** | 评测可强制 bm25 / dense / hybrid / hybrid+rerank / bm25_fallback；生产默认钉死 bm25，直至增益门 + Hard-Gold |
| **降级诚实** | 向量失败 → BM25 并标记 `bm25_fallback`，不静默空结果 |
| **冒烟对照可复跑** | 报告在 `reports/`；入口见 [`eval-retrieve.md`](./eval-retrieve.md) |

组合说法（与 roadmap 贡献口径对齐、本阶段只声明检索切片）：  
「我们把复验链路上的检索做成可独立测量、可降级的子系统，并用预登记增益门挡住无增益换默认。」

---

## 2. 禁用话术（黑名单 · 口述与文档均禁）

1. 「我们做了 **agentic RAG**」（Phase A 明确 Out）  
2. 「**dense / hybrid / rerank 已是生产默认**」  
3. 「评测 **证明** BM25 **统计显著**最优」  
4. 「**首次**带证据改稿」或对外装形式化 **proof-carrying / PCC**  
5. 「**Phase A = 整条发前闭环已交付**」（发前闭环属 V1+；Evidence-bound 属 V1.5）

Related Work 祖先（RARR / PAVE / 事实检查等）可承认；边界话术用「发前新鲜度复验协议」留给后续阶段，**勿**在 v0 假装已完成。

---

## 3. 后续阶段将声明（占位 · 非本 v0 交付）

| 阶段 | 将追加的贡献面（占位） |
|------|------------------------|
| V1 | 单垂直发前路径；T1 落盘；包结论；`patch_events` 起记 |
| I1 | 失败三分法 + 可复盘误判样本（冒烟层口径：不报方差，不作统计显著） |
| V1.5 | Evidence-bound / attested patch（人确认 + 强制再验）；论文主投实验 |
| I2 | 安全三例可复现 demo：越权召回 · 间接注入 · 检索投毒（≠ idea #4；ADR-0030） |
| V2 | 发前钩子（Memo UI+CLI + 入站 check）+ 主张台账只读投影（冒烟·采用层；ADR-0031） |

- **V1 已落地（冒烟，2026-09-29）：** 发前闭环主缝在仓（顾问样例包 `v1-mck-soai`、白名单薄 URL、包结论、人审、`patch_events` 起记）。证据见 `docs/evidence/v1/V1-DoD-CLOSE.md`。档=冒烟；生产默认臂仍 `bm25`；本条不是 Hard-Gold，也不是检索臂评测升格。
- **I1 已落地（冒烟，2026-09-29）：** 失败三分法 + 可复盘误判样本已在仓。短索引 `docs/evidence/i1/INDEX.md` 一眼：漏拦/误拦 ≥3，且 ≥1 条 `runnable=true`（金样 `i1-s005`）。证据见 `docs/evidence/i1/ACCEPTANCE.md`。档=冒烟；不报方差；生产 Gate / disposition / HumanLatch 枚举未扩；本条不是 Hard-Gold。
- **V1.5 已落地（冒烟，2026-09-29）：** 表单 Evidence-bound（独立 `propose_patch`/`confirm_patch`、有证覆盖、单条再验、导出）；薄对话本期 Out（未实装、未 stub）；HumanLatch `VALID_ACTIONS` 未扩；发前无 C\|T 开关；Exit 不硬绑「可发」。评估见 `docs/research/V1.5-Evidence-bound补丁设计评估.md`；ADR-0029；硬 Exit `docs/evidence/v15/ACCEPTANCE.md`；关门 `docs/evidence/v15/V15-DoD-CLOSE.md`。档=冒烟；不是 Hard-Gold，不是 C vs T 显著，不是改默认臂。
- **I2 已落地（冒烟，2026-09-29）：** 安全三例（ACL tenant 过滤 · 注入 Gate 拒绿 · poison 元数据剔除）可复现；注入 1× Lead→Auditor 冒烟 fail-closed；薄表 `docs/security.md`。评估见 `docs/research/I2-安全三例设计评估.md`；ADR-0030；硬 Exit `docs/evidence/i2/ACCEPTANCE.md`；关门 `docs/evidence/i2/I2-DoD-CLOSE.md`。档=冒烟；≠ #4；不是渗透认证，不是安全通过率，不是 Hard-Gold，不改生产默认臂。
- **V2 已落地（冒烟·采用层，2026-09-30）：** 发前钩子（Memo UI+CLI 同闸 + 入站 check allow/deny）+ 主张台账只读投影（discard∪renew）；零新写表；未做 Word/Notion/开放 webhook 平台；未图谱/CMS；未 Memo 商业裁决；未整包再验挂钩子；未改默认臂；未解冻 Studio。评估见 `docs/research/V2-发前钩子与主张台账设计评估.md`；ADR-0031；硬 Exit `docs/evidence/v2/ACCEPTANCE.md`；关门 `docs/evidence/v2/V2-DoD-CLOSE.md`。档=冒烟·采用层；`curl` ≠ 平台已交付；不硬绑「可发」；不报采用率；不是 Hard-Gold。

整协议口径（已入库 T1 才能裁定；`web→落盘→再验`；补丁 ⊆ T1；人确认；对话不改正式裁决）以 roadmap「贡献口径」为准，**随阶段追加进本文件**，不在 v0 写成已交付。

---

## 4. 指针

- 数字与口述：[`accounting-card.md`](./accounting-card.md)  
- 复跑：[`eval-retrieve.md`](./eval-retrieve.md)  
- 规格：`docs/spec/10-PhaseA-RAG.md`（契约；**不是**本贡献清单的替代）
