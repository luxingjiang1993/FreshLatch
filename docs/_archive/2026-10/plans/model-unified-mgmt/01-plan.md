# FreshLatch 模型统一管理计划

状态：APPROVED（主人 Oriental Ronin，2026-10-15）— 含适配分析 + 连通性体检 + 正式跑前闸；实现走 Grok→Cloud Agent→Matt；S1/S2 拆 PR；S4 不做

本文件是批准稿的仓库副本。切片进度以 [00-status.md](00-status.md) 为准。本 PR 只做 S0 + S1。

范围：统一 model 选择/解析 + 对各槽位做「是否仍是当前最优」分析（含本地 LM Studio）；**不含** C-04「跑」与 RESULT；**不**改 floors/gold/x1/production arm 行为语义

## 仓库落点说明（入库时补，不改批准结论）

- **ADR**：不新开 `docs/adr/`。本仓 ADR 用于难反转、反直觉、且有真实取舍的拍板。现有 ADR 没有 model registry / 槽位选择的同类短记。S1 只把已有 model id 收进 `MODEL_REGISTRY`，调用方改读 registry，不改运行默认。profile 与 locked slot 的取舍在 S2，三条件届时再判。
- **词表**：S1 不改 `CONTEXT.md`。`nli` 是 registry 的 purpose，不是新的产品词。profile / locked 等到 S2 再判是否进词表。
- **本 PR 不做**成功标准第 2、3、5 条里的 profile、locked、fit report。fixtures 绿不等于注册分。本计划不发明 SESOI。

---

## 1. 问题

- 已有 `MODEL_REGISTRY`（`src/freshlatch/models.py`），但 NLI、部分 `scripts/`、C-04 generator/nli 仍在 registry 外。
- 换模型常要改多处；密钥/base_url 在 `llm.py` 有写死；无 profile，本地 LM Studio 无法一键切。
- 正式评测（注册分 / C-04）若与日常本地混用，有「误钉本地」风险。
- **新增**：registry 里各槽位「当初选的云端默认」未必仍是最优；主人已有 LM Studio（9B 全卡 / 27B 混卸），需要**可复跑的适配分析**，而不是口头感觉。

成功标准：

1. `src/` + 相关 `scripts/` 的 model 字面量只出现在 registry（或测试白名单）。
2. 日常用 env/profile 切换 cloud ↔ local-lms，**不改业务调用点**。
3. 正式跑（C-04 / 注册分相关）可 `locked`，拒绝被 local profile 覆盖。
4. 现有单测绿；新增 registry/profile 单测。
5. **交付一份按槽位的适配分析报告**（保留/可换本地/必须云端 + 理由），并有可复跑的评分表模板；换模建议须主人另批，分析本身不自动改正式钉死项。

---

## 2. 方案（务实，非 gateway）

```
调用方 → resolve(slot, profile?) → ModelEntry(...)
                ↑
         MODEL_REGISTRY + profiles
                ↑
         适配分析（只读评测表 / 报告，不自动改正式锁）
```

- **Registry**：唯一真相（扩 NLI、补齐 env_key 使用）。
- **Profile**：`cloud`（默认）/ `local-lms`；`FRESHLATCH_MODEL_PROFILE` 选择；只覆盖允许的 slot。
- **Locked slots**：generator/nli/judges（正式）等默认不可被 local 覆盖。
- **适配分析模块**：对每个 slot 用固定维度对比「当前默认 vs 候选（含 LMS）」；输出 `docs/ops/model-fit-report.md`（或 evidence 下带日期的报告），**建议变更走另票**，分析 PR 默认只加报告+模板。
- **不建**独立 model gateway 服务。

---

## 3. Profile 草案

| slot | cloud（现状） | local-lms（建议） | locked? |
|------|---------------|-------------------|---------|
| `default_llm` | qwen-flash @ DashScope | qwen3.5-9b @ `http://127.0.0.1:1234/v1` | 否（草稿可本地） |
| `embed` | text-embedding-v4 | 继续 `local_embed` 路径为主（LMS 一般不做 embed） | 否 |
| `local_embed` / `neural_rerank` | 已本地 fastembed | 不变（分析是否换更强小模型） | 否 |
| `nli` | mDeBERTa…（现硬编码） | 仍 transformers 本地；收入 registry | 正式跑建议锁 |
| `judge_*` | 三云端评委 | 默认不映射本地 | **是** |
| C-04 `generator_model` | manifest 钉死（现 null） | 正式跑禁止 local profile | **是** |

说明：Cursor IDE BYOK **不在本计划运行时范围内**；可在适配分析里**顺带一句**「Agent 不宜本地」，但不改 Cursor 配置。

---

## 4. 补充模块：模型适配分析（Model Fit Review）

### 4.1 目的

回答：「registry 里每个用途，在**当前机器（RTX 5070 Ti 12GB + 32GB RAM + LM Studio）+ 成本 + 正式性**约束下，是否仍是最好选项？」

### 4.2 每个 slot 的固定维度（打分表）

| 维度 | 说明 |
|------|------|
| 任务匹配 | 草稿 / 正式生成 / 评委 / embed / rerank / NLI |
| 质量下限 | 能否接受（面试/产品 demo vs 注册分） |
| 上下文 | 典型 prompt 长度 vs 本机可载 n_ctx（9B≤65k；27B 混卸约 8–12k） |
| 延迟与吞吐 | 本机实测 vs 云端 API |
| 成本 | ¥/百万 token 或本机电费近似；月度粗算 |
| 可复现 / 锁定 | 能否 hash、是否允许进 RESULT |
| 运维摩擦 | 密钥、断网、VRAM、与现有 CI |

结论三选一：`keep`（维持） / `prefer_local`（日常改本地） / `must_cloud`（必须云端）。

### 4.3 候选集（首轮）

- Chat 草稿：`qwen-flash`（云） vs LMS `qwen3.5-9b` vs LMS `qwen3.8-27b`（混卸）
- Judges：维持三云端；本地仅标记「不推荐」并简述原因
- Embed：云 `text-embedding-v4` vs 已有 `bge-small-zh-v1.5`
- Rerank：已有 `bge-reranker-base`；可选列更强候选但**默认不换生产**
- NLI：现 mDeBERTa；列是否有同级更小/更快替代（分析级，不自动换）

### 4.4 方法（轻量，可复跑）

- **不**开正式 C-04；用小固定 fixture（≤20 条或现有 smoke）+ 同一 prompt 模板。
- 输出：表格 + 每槽 3–5 行建议；记录机型、LMS 上下文、日期。
- 自动化：`scripts/model_fit_review.py`（或 notebook）读 registry，打印槽位与 profile 解析，可选跑 smoke；人审结论写入报告。

### 4.5 与统一管理的关系

- 分析**依赖** registry（S1 后字面量已收口，分析才完整）。
- 分析**不**自动改 locked / manifest；若建议换正式模型 → 另开 Gate 票。

---

## 5. 切片（开写顺序）

### S0 — 文档入库

- `docs/plans/model-unified-mgmt/`（本目录的 `00-status.md` 与 `01-plan.md`）。ADR 短记见文首：本切片跳过。

### S1 — 收口字面量（行为不变）

- NLI → registry；scripts → registry；`llm.py` 读 `env_key`/`base_url`；强化扫描测试。

### S2 — Profile 解析

- `resolve_model`；`FRESHLATCH_MODEL_PROFILE` / LMS base + model env；locked 不可覆盖；单测。

### S3 — 运维文档与冒烟

- `docs/ops/model-profiles.md`；`scripts/smoke_model_resolve.py`。

### S5 — 模型适配分析（新增，建议在 S3 后）

- 评分表模板 + 首轮报告 `docs/ops/model-fit-report.md`（或 `docs/evidence/model-fit/YYYY-MM-DD.md`）。
- 可选脚本读 registry 列出槽位与 keep/prefer_local/must_cloud 草稿，主人改结论。
- **默认不改生产默认模型**；若报告建议换 `default_llm` 日常默认 → 另票。

### S6 — 密钥/连通性体检

- `scripts/smoke_model_connectivity.py`（或并入 smoke）：检查各 slot 的 env 是否存在、DashScope/LMS `/v1/models` 或最小 chat 是否可达；失败给清晰退出码，不跑正式评测。

### S7 — 正式跑前闸

- 写 RESULT / 注册分入口前：断言 `profile≠local-lms`（除非显式解锁且仍禁止写入正式 RESULT）、locked 槽未被覆盖；失败即停。

### S4 —（可选）C-04 manifest 对齐

- **默认不做**。

PR 建议：S1 一 PR；S2 一 PR；S3+S5 可同 PR 或拆开（报告可先人写、脚本后补）。

---

## 6. 非目标 / Do-not-touch

- 不改 retrieval 生产默认（hybrid+rerank）除非另票。
- 不改 floors / gold / x1 / production arm。
- 不开 C-04「跑」、不写 RESULT。
- 不强制下载新 GGUF。
- 不把 Cursor Agent 工具循环「修进」本计划（仅在 fit 报告里标注不适合）。

---

## 7. 风险

| 风险 | 缓解 |
|------|------|
| local profile 误入正式分 | locked + 报告明确 must_cloud |
| 适配分析变成无数据空谈 | 固定维度 + 小 fixture 实测延迟/能否载入 |
| 报告驱动乱改生产 | 分析与变更拆票；生产默认变更需主人另批 |

---

## 8. 执行策略（已定）

- Grok Bot 拆票 / 审合；Cloud Agent 开写（`before-implement` + Matt）；主人本机 Cursor 非必须。
- 会消耗 Cursor spending：票拆小、少 follow-up。
- S1、S2 两个 PR；S3+S5+S6+S7 可跟 S2 后或单独文档/脚本 PR；S4 不做。
- 本 PR = S0 + S1。S2 起另 PR。

## 9. 请主人终批（历史；策略已确认）

2026-10-15 主人已批。下列四条按批准稿保留，不再重开：

1. 原统一管理 + **S5 适配分析** 一起批准。
2. S1 / S2 拆两个 PR。
3. S4 不做。
4. 首轮分析包含 27B 混卸对比，但标 prefer 9B 做草稿（上下文更够用）。
