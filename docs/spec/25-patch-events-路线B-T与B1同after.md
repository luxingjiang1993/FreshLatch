# patch_events 路线 B · T/B1 同 after 再分叉与抬 k（to-spec 增量）

> 来源：决议 [#466](https://github.com/luxingjiang1993/FreshLatch/issues/466) · 地图 [#465](https://github.com/luxingjiang1993/FreshLatch/issues/465) · ADR-0035 · `/to-spec`  
> 父规格：[`24-patch-events-路线B冲甲.md`](./24-patch-events-路线B冲甲.md) · 父票 [#436](https://github.com/luxingjiang1993/FreshLatch/issues/436)  
> 评估：`docs/research/patch_events-路线B-T与B1可执行差与抬k设计评估.md`  
> 协议页：`docs/evidence/patch-events/PREREG-B.md`（**激活前修订已记** · **正式主跑未激活**）  
> 上游已落：选取 R（#437）· 门闩冒烟未过（#438）  
> **测试主缝（本增量）**：`run_arms`（或等价）上 T/B1 **同 after 再分叉**  
> 语言：中文。技术词保留 English 原词。  
> 本页不激活正式主跑，不发模型（除非人授小探针票），不回写旧 `PREREG.md`，不填 `RESULT-B` 成立格。

## Problem Statement

选取 R 已打开可识别性，但 #438 仓外门闩未过：

1. T−B1 固定 k 误放差 = 0：T/B1 在独立生成 + 同核验 hard reject 下高度同构，绑定缝被生成噪声盖住；  
2. T 的 k = 3 < 10：正确样假阴性全是核验不过，绑定未杀正确样；  
3. 未过门不得激活 `PREREG-B`、不得开 #440 正式生成进主表。

#466 已拍板：D1 同 after 再分叉 · L1 降正确假阴性 · 复测序与激活前修订。本规格把拍板收成可测工程缝与票序，**不保证**得到甲。

## Solution

1. **行为差缝**：同一 `claim_id` 上 T/B1 共用一份 rewrite `after_text`，再分叉决策（T：绑定∧核验；B1：仅核验；两边不过均 hard reject）。  
2. **复测夹具 + 报告格式**：夹具证明分叉；报告字段与 `PREREG-B` R / 门闩三条件一致；机制后重跑可扔 `GATE-SEPARATION`（或等价新针路径）。  
3. **抬 k（第二张）**：生成侧降正确假阴性；禁止松闸凑 k。  

求验目标（甲）不保证。禁止把「设计冲甲」写成「将得到甲」。

## User Stories

1. As a 统计读者, I want T 与 B1 在同一 after 上只因绑定闸而分叉, so that T−B1 对照不是生成噪声。
2. As a 统计读者, I want B1 核验不过仍拒绝, so that 对照不被削弱凑差。
3. As a 复现者, I want 夹具上「坏·未绑定 T1 且 after==evidence」时 T reject / B1 release, so that 绑定缝可测。
4. As a 复现者, I want 同 after 且两边核验失败时均 reject, so that D2 不被偷偷实装。
5. As a 预注册守门人, I want 门闩复测报告字段与 PREREG-B R 一致, so that 激活条件不被另定。
6. As a 预注册守门人, I want 复测报告文首标明可扔/不进主表/非甲, so that 冒烟不升格。
7. As a 预注册守门人, I want 未过三条件时报告不得建议激活, so that #440 不被绕过。
8. As an 工程代理人, I want 第一张票只做 D1 + 复测夹具/格式, so that 不夹带正式生成。
9. As an 工程代理人, I want 抬 k 票单独验收「正确样过 T 变多」, so that 不用松闸冒充 L1。
10. As a 密钥守门人, I want 默认不发模型, so that 未授权不烧配额。
11. As a 平行轨守门人, I want 本缝不改 `compare_primary` 成立定义, so that #434 防火墙仍在。
12. As an 面试讲解者, I want 规格写明见门闩失败改的是可执行定义不是成立定义, so that 反 HARKing 可讲。

## Implementation Decisions

### 主缝 A（硬门 · 票序 1b）

**缝**：`src/freshlatch/eval/patch_events_arms.py` 的 `run_arms` / `_generate_edit` / `_decide`（或由其唯一调用的共享 after 辅助函数）。

- 对每一候选：先产生**一份**供 T 与 B1 共用的 rewrite `after_text`（及同一候选 `evidence_id`），再分别调用决策。  
- **T**：`_bound_t1` 失败 → reject（理由保持「证据未绑定已入库 T1」）；通过后再 `verify_edit`；不过 → hard reject。  
- **B1**：跳过绑定闸；只跑同一 `verify_edit`；不过 → reject（臂记 B1，不得记成 T）。  
- **C / B2**：行为相对本增量不变（C 仍生成即放行；B2 仍不因核验 hard reject）。  
- 禁止实装：B1 核验失败仍 release / soft warning；B1 专用弱核验；为凑差把金标写入 score。  
- 共享 after 的生成请求臂标记：实现可选「以 T 请求生成一次」或「显式 shared rewrite 阶段」；须在代码注释（中文）与测试中写清，且 T/B1 记录中的 `after_text` **逐字相同**。

### 主缝 B（复测 · 票序 2'）

**缝**：可扔报告 `docs/evidence/patch-events/GATE-SEPARATION.md`（或实现票写死的 `GATE-SEPARATION-remeasure.md` 等价路径）+ 只读回放/夹具入口。

- 规则针 = `PREREG-B` 固定 k 选取 R（与 #437 同一 `compare_primary`）。  
- 数据序：夹具冒烟 → 只读旧 n=30 生成 →（可选，人授）小探针。  
- 最低字段：各臂自然放行/自然误放；固定 k 集合与误放率；T−B1/T−B2 差与方向；k；三条件判定；激活建议；代码针；是否发模型。  
- 未过三条件 → **不得**建议激活；**不得**改 `PREREG-B` 文首；**不得**填 `RESULT-B` 成立格。

### 主缝 C（抬 k · 票序 1c）

**缝**：生成提示 / 正式生成路径中与「正确样 after 对齐 evidence」相关的最小改动（`patch_events_generate.py` 及测试），**不**改 `verify_edit` 逐字语义，**不**改 T hard reject。

- 验收叙事：正确样在 T 上核验假阴性下降的可测路径（夹具或只读回放对比），不是放宽闸。  
- 不得为抬 k 修改绑定闸或成立定义。

### 缺口与关掉方式

| 缺口 | 决定 | 验收时要看见 |
|---|---|---|
| T/B1 独立生成盖住绑定缝 | 同 after 再分叉 | 夹具：同 after 上 T reject（未绑定）且 B1 release（核验 ok） |
| B1 被削弱凑差 | 保持核验不过则拒 | 夹具：同 after 核验失败 → 两臂均 reject |
| #438 报告过期 | 机制后必重跑 | 新报告写明针与三条件；未过不得建议激活 |
| k 被假阴性压死 | L1 生成侧 | 正确样过 T 的路径可测；verify/绑定语义不变 |
| 未过门进主表 | 生成票仍挡 | #440 依赖复测过门 + 激活批注 |

### 票序（本增量）

父索引：[\#468](https://github.com/luxingjiang1993/FreshLatch/issues/468)

| 序 | 票 | 挡否 |
|---|---|---|
| 1b | [\#469](https://github.com/luxingjiang1993/FreshLatch/issues/469) T/B1 同 after 再分叉 + 复测夹具 | 挡复测报告与后续抬差叙事 |
| 2' | [\#470](https://github.com/luxingjiang1993/FreshLatch/issues/470) 仓外门闩复测报告（可扔） | 挡激活 / #440 |
| 1c | [\#471](https://github.com/luxingjiang1993/FreshLatch/issues/471) 抬 k：降正确假阴性（生成侧） | 挡「k≥10」求验路径；可与 2' 并行准备，但松闸禁止 |
| （既有） | #439 名单 · #440 生成 · … | #440 仍须门闩过 + 激活 |

### 与平行轨 / 选取缝防火墙

- 不改 `compare_primary` 的 R 成立定义。  
- 不改旧 `PREREG.md` / 旧 `RESULT.md` 成立格。  
- 平行轨 `#434` 只许 `compare_alt_*`，不得用本缝数字填 `RESULT-B`。

## Testing Decisions

### 缝 A（`run_arms`）

只看缝外面：注入 generator/verifier/ingested，断言 decision。

必须覆盖：

1. **绑定缝**：`after == evidence`，`evidence_id` 非已入库 T1 → T=`reject`（未绑定），B1=`release`；且两臂 `after_text` 相同。  
2. **同核验失败**：`after != evidence` → T 与 B1 均 `reject`（非 release）。  
3. **双过**：已绑定 T1 且 after==evidence → 两臂均 `release`，after 相同。  
4. **不读密钥、不发网络**。

### 缝 B（报告）

- 字段齐全；可扔声明；三条件表；未过 ⇒ 不得建议激活。  
- 默认不发模型。

### 缝 C（抬 k）

- 证明改的是生成对齐，不是 `verify_edit` / 绑定语义。  
- 至少一条夹具或契约测试锁住「核验仍是逐字相同」。

本规格会话不落地业务代码；留给实现票（TDD）。

## Out of Scope

- 激活 `PREREG-B`；开 #440 正式生成进主表  
- 复活路线 A；回写旧 PREREG/RESULT 成立格  
- D2/D3（削弱 B1）；放松 T hard reject / 逐字核验凑 k  
- 金标/评委进 score；夹具填甲  
- 改选取 R 或成立定义  
- `/writing-plans`、`/executing-plans`；本会话 `/implement`  
- 平行轨升级决议（#455）

## Further Notes

- **可以**在 enrich 后对新工程票跑 `/before-implement` → 新会话 `/implement`。  
- 复测即使方向为正，也只授权写激活批注；甲仍不保证。  
- 旧 #438 报告保持「未过」历史身份；新复测须换针或明确批注「机制后重跑」，不得把旧页改写成已过门而不重算。
