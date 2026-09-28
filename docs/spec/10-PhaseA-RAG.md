# Phase A — RAG 子系统规格

> 来源：`/grill-with-docs`（Phase A）决议摘要 → `/to-spec`  
> 词表：`CONTEXT.md`  
> 权威 ADR：0003（须随本规格开修订票：评测可跑 dense/rerank vs 生产默认须增益）  
> 路线图：`docs/roadmap.md` Phase A（A7/A8 措辞以本规格为准）  
> 测试主缝（已确认）：**`retrieve` 子系统边界**（含入口主张查询变换）

---

## Problem Statement

复验主链已经能跑，但检索仍是「BM25 + 空透传 vector/rerank」，无法独立证明召回是否变好。Agent、闸门与假绿仪器会把「检索 miss」和「判定错误」缠在一起。产品要把已签发主张从「曾经为真」变成「现在仍可复验」，却还没有一份可复现的 retrieve 评测表、稳定的对外契约，以及失败时诚实降级——因此无法在不改 Agent 品味的前提下迭代 hybrid/rerank。

## Solution

把 `claim → 主张查询变换 → retrieve(query, filters) → 有序 evidence_id` 做成可独立测量、可替换的子系统。Agent（Lead/Critic）只当调用方，不得自由改写检索串。评测双轨：子系统 Recall@10/MRR 为关门硬条件；既有 must_stale 金标命中回放为保险丝。Dense 用 ingestion 预计算向量 + 运行时本地余弦；hybrid 用 RRF；rerank 仅当相对 hybrid 有增益且延迟达标才可设生产默认；向量失败硬降级 BM25 并标记 `retrieval_mode`。PDF 软关门；日历时间窗、Memory、开放标签、聊天向量化裁定一律不做。

## User Stories

1. As a 检索工程师, I want 一份冻结的 retrieve 调用契约, so that Agent 与评测共用同一入口且算法可替换。
2. As a 检索工程师, I want 对外命中主键始终是 `evidence_id`, so that 白名单点回与金标锚不因内部 `chunk_id` 漂移。
3. As a 检索工程师, I want 按 `as_of` / `source_type` 做快照过滤, so that T0/T1 换源对照仍然是 WHERE 级干净过滤。
4. As a 检索工程师, I want 轨迹记录 query、filters、有序 `evidence_id[]`、`retrieval_mode`, so that 失败可归因到检索臂而非只看 hits 计数。
5. As a 评测工程师, I want ≥30–50 条 retrieve 金标 query, so that 子系统指标可复现跑表。
6. As a 评测工程师, I want 主指标 Recall@10、辅指标 MRR、并报告 K∈{5,10}, so that 与现状 top_k=10 对齐且可对照。
7. As a 评测工程师, I want hybrid 不低于 BM25 与 dense 中较差者, so that 融合不会系统性变差。
8. As a 评测工程师, I want BM25 相对 A0 基线不得越容差回退, so that 「大家一起变差」不能假装过关。
9. As a 评测工程师, I want 报告标明 n 为冒烟级、非统计显著, so that 演示可过不等于测量可信。
10. As a 评测工程师, I want 主张金标派生相关 evidence_id, so that retrieve 金标与既有因果锚同源。
11. As a 评测工程师, I want 快照取代/冲突/元陈述陷阱人工标注, so that 闸语义不会偷偷塞进召回金标。
12. As a 评测工程师, I want must_stale 命中回放在变换后 query × as_of=T1 × top_k=10 下全绿, so that 主链保险丝仍在。
13. As a 评测工程师, I want `eval retrieve`（或等价 CLI）一键复跑, so that AFK 可对照基线。
14. As a 语料管理员, I want corpus 与 retrieve 金标的目录聚合 checksum 入档, so that 评测语料可指认版本。
15. As a 语料管理员, I want 一页 BM25 基线报告, so that A0 有可引用起点。
16. As a 语料管理员, I want 索引可重建步骤写清, so that 换机可复现。
17. As a 语料管理员, I want 继续 `## pN` 结构锚切块, so that 既有 evidence_id 不被字数窗打碎。
18. As a 语料管理员, I want ≥1 份真实文档冒烟入库可检索, so that ingest 通路被真文件验证且不污染主指标 n。
19. As a 语料管理员, I want PDF 纯文本先规范成同构锚再 ingest, so that 软关门不破坏切块契约。
20. As a 系统集成者, I want 主张查询变换默认是模板/规则, so that 检索增益不与 LLM 漂移缠死。
21. As a 系统集成者, I want LLM 改写仅作对比臂, so that 可测量变换前后 Recall 而不改默认路径。
22. As a Lead 调用方, I want 只提交主张（及可选登记维度）, so that 查询串由变换器产出而非我自由发挥。
23. As a Critic 调用方, I want focus 经封闭枚举映射进同一变换器, so that 角色品味不能穿透检索归因。
24. As a 检索工程师, I want dense 填实 vector 融合 stage, so that 语义同义漏召回可被测量。
25. As a 检索工程师, I want DashScope `text-embedding-v4` 在 ingestion 预计算向量, so that 运行时评测可本地余弦、不出网打分。
26. As a 检索工程师, I want 向量/模型失败时硬降级 BM25 并标记 `bm25_fallback`, so that 演示环境不静默空结果。
27. As a 检索工程师, I want hybrid 使用 RRF, so that 跨量纲分数无需调 α。
28. As a 检索工程师, I want BM25/dense/hybrid 三列对比表, so that 选型有据。
29. As a 检索工程师, I want rerank 对比臂可跑, so that 能判断是否默认开启。
30. As a 产品负责人, I want rerank 仅当 Recall@10 严格优于 hybrid 且 p95≤800ms 才可生产默认, so that 无增益不开默认。
31. As a 评测工程师, I want 评测夹具可强制 `retrieval_mode`, so that 分臂对比不依赖生产开关。
32. As a 合规叙事者, I want 明确不做日历生效/失效窗, so that 「过期」不会与 basis_rot 抢词。
33. As a 合规叙事者, I want 陷阱包使用快照取代/冲突/元陈述三类名称, so that 路线图旧称「过期」有操作定义。
34. As an AFK agent, I want 本规格可拆成带 Acceptance 的工单, so that 可按 A0→A1→… 实施。
35. As a 架构守护者, I want ADR-0003 修订为「评测可跑 / 默认须增益」, so that 与 Phase A 主动建对比臂不矛盾。
36. As a 架构守护者, I want Memory/开放标签/聊天向量化/主张台账不进本规格, so that Phase A 不膨胀。
37. As a 面试讲解者, I want 登记「参考代码改编点」与「必须重写点」, so that 不重复造轮子也不误抄冲突方案。

## Implementation Decisions

### 契约与主缝
- **唯一行为验收缝**：`主张查询变换 → retrieve → 有序 evidence_id + retrieval_mode`。CLI、工具、回放、分臂评测必须走同一缝。
- **生产签名**：`retrieve(query, *, as_of=None, source_type=None, top_k=10)`。`doc_version` 继续存于 chunk；过滤进生产签名不作为 A0 硬阻塞（可另票）。
- **评测夹具**：可强制 `retrieval_mode ∈ {bm25, dense, hybrid, hybrid+rerank, bm25_fallback}`；生产默认不得让 Agent 随意切臂。
- **对外主键**：`evidence_id = doc_id#anchor@as_of`。`chunk_id` 仅存储内部。
- **轨迹最低字段**：query、filters、有序 evidence_id 列表、retrieval_mode（结束「只记 hits 计数」）。

### 变换与角色
- **主张查询变换 v0**：确定性模板（主张 statement ± 登记维度/`focus` 中文名）；恒等变换若无增益可保留接口。
- **LLM 改写**：仅对比臂；模型名/温度/种子写入运行记录；失败回落 statement。
- **Lead/Critic**：禁止自由改写检索串；Critic 的 focus 只经变换器。

### 切块与 ingest
- **结构锚切块**：维持 `## pN`；主契约不用字数窗。
- **PDF**：软关门——抽纯文本 → 打同构锚 → 入库；表格/HTML/OCR 后置。
- **真文档**：≥1 份冒烟；不进主指标样本 n。

### 打分管线
- **BM25**：继续 jieba + BM25Okapi（已有主链）。
- **Dense**：填实 vector 融合；DashScope `text-embedding-v4` ingestion 预计算；运行时本地余弦；失败 → BM25 + `bm25_fallback`。
- **Hybrid**：RRF（参数 k 写入报告）；弃用参考库中的 α 加权分数融合作为默认。
- **Rerank**：可跑对比；默认开启门槛 = Recall@10 严格优于 hybrid **且** 单次 retrieve（含 rerank）p95≤800ms（本地评测机）。未过线则默认关。
- **相对 ADR-0003**：Phase A **允许评测主动**跑 dense/hybrid/rerank；**无增益不得设生产默认**。须另开 ADR 修订「金标回放不过才点菜」句，改为区分评测可跑 vs 生产默认。

### 评测与入档
- **双轨**：子系统 Recall@10/MRR；must_stale 回放保险丝。禁止互相顶替。
- **Hybrid 通过线**：≥ min(BM25, dense)；且 BM25 相对 A0 基线不越预登记容差回退。
- **Retrieve 金标**：主张金标派生 + 陷阱三类人工。
- **A0 入档**：corpus + retrieve 金标目录聚合 checksum；一页基线报告（日期、文件数、chunk 数、BM25 Recall@10/MRR、回放 pass/fail）。
- **诚实框定**：n≈30–50 为冒烟级，不报统计显著/方差声称。

### 参考代码改编（避免重复造轮子）
在 `历史项目代码供参考/`（gitignore）内 **改编** 下列能力；**禁止**整文件搬进主链当开放问答 RAG：

| 能力 | 改编自（目录级） | 处置 |
|------|------------------|------|
| `##` 切块与 citation 形状 | project 多agent `rag.py` / citation schema | 已基本在主链；补齐轨迹 evidence_id 纪律 |
| jieba + BM25Okapi 打分形态 | CASE-高效召回 HybridSearch；CASE-知识库处理 BM25 | 主链已有；评测表形态可借鉴知识库 hit@k |
| embedding 调用形态（v4） | CASE-知识库处理版本管理脚本 | 改编入库写 `vec`；**不**以 FAISS 为真相存储 |
| DashScope embedding 批调用/重试 | RAG-cy embedding 脚本 | 改编；模型钉 v4 |
| 金标命中/准确率评估骨架 | CASE-知识库处理 `evaluate_retrieval_methods` | 改编为 evidence_id 级 Recall@K/MRR + 回放 |

**必须重写 / 不得当默认抄入**：
- CASE-高效召回的 **α 加权混合**、**FAISS 主存**、**MultiQuery + 聊天 PDF QA**
- CASE-rerank / bge 重权重作为 A 默认（仅对比臂候选）
- RAG-cy Docling/字数窗/parent-page 主路径、Jina/LLM rerank 默认
- 全库 **无现成 RRF**——RRF 本规格新写

Provenance 要求：触达现有 store/pipeline/ingest/eval 的工单须标注 kind=adapt，并指向上表参考路径或本仓既有实现。

## Testing Decisions

- **好测试**：只断言主缝外部行为（给定 query/filters/mode → evidence_id 序列与 mode 标记；指标表可复现），不锁内部向量库实现细节。
- **主测模块**：retrieve 管线（含变换入口）、降级模式、快照过滤、索引重建后一致性、评测 CLI 报告字段。
- **Prior art**：`tests/unit/test_store.py` 金标命中回放；`freshlatch.eval` 报告落盘模式；gate1 零 LLM CI 纪律——retrieve 子系统单测进 CI；需 DashScope 的 embedding 构建可标手动/里程碑，但「已有 vec 时的本地打分」应可离线测。
- **分列冒烟**：强制 dense 可用 vs 允许 bm25_fallback 分列，禁止混报。

## Out of Scope

- Memory 挂载/切除、用户聊天/人审自由文本向量化裁定
- 开放知识点标签、主张资产库台账（C3）
- 日历 effective/expiry 过滤、basis_rot 全链（B5）
- 对抗套件实跑、多 seed Agent 消融、并发、跨 Provider
- 开放联网问答、通用对话写绿灯
- GraphRAG、微调 reranker、字数窗主切块、FAISS/Chroma 换存储真相
- span 字符级点回（属中间层 M）、Agent 编排大改

## Further Notes

- **路线图措辞回填**：A7「时间窗」→ 快照过滤 + 版本字段；A8「过期」→ 快照取代。建议与 ADR-0003 修订同批文档 PR。
- **关门条件**：可复现评测表；契约稳定且轨迹含 evidence_id；快照过滤与索引重建可读；dense 失败降级可测；本节 Out of Scope 未偷渡进主链。
- **下一跳**：`/to-tickets` → `/enrich-tickets`；每票含可执行 Acceptance 与 Paths；涉及参考库改编的票写 Provenance。
- **grilling 决议编号 R1–R19** 见本会话摘要；词表已更新：快照过滤、主张查询变换、结构锚切块、快照取代、检索陷阱三类。
