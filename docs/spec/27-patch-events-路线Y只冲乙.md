# 规格卷 27 — patch_events 路线 Y · 只冲乙（仅锁 T−C）

> **to-spec 来源**: grilling 拍板（四题「按推荐」）· 四件套 PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)  
> **ADR**: ADR-0037 · **缺额解锁** ADR-0038  
> **协议**: `docs/evidence/patch-events/PREREG-Y.md`（**未激活** · 缺额停泊）  
> **评估**: `docs/research/patch_events-路线Y只冲乙仅锁T-C设计评估.md` · `docs/research/patch_events-路线Y正式n与语料缺额设计评估.md`  
> **卷号**: 27（避撞 B=24 · ALT/同 after=25 · C=26；后三者可能仍在 Draft）  
> **语言**: 中文。技术词保留 English 原词。  
> 本页不是论文，不激活正式主跑，不发模型，不回写 B/C 冻结页，不填 RESULT-Y 成立格冒充已跑。
## 目的地

把路线 Y 决议落成可派工规格：继承 B 已验证机制包（R · 同 after · 软对齐），**不**走 C 强制抄句主路径；增量是预注册成立口径（仅 T−C + 点>0.05）、n=400、乙专用门闩与 formal-y 旁路。过门闩前不得正式主跑。本卷**不含**「保证乙」。

## 非目标

- 复活路线 A；改 B/C 成立格；同页二跑 B/C/Y  
- 放宽 hard reject；金标进 score；称甲 / soft-甲；保证乙  
- 以 C 强制抄句为 Y 主路径；ALT/夹具进主表  
- 新造 `compare_*`；改 `compare_primary` 数学追乙  
- 未过门激活 `PREREG-Y` / 开正式 n=400 进主表  
- 事后加 n 充数；升格 `#479` GATE-K-PROBE / GATE-C-FIXTURE  
- **静默改小** `PREREG-Y` 配额表凑库存；表写 400、实际喂 <400（ADR-0038）  
- 语料缺额未解除时派 PE-Y-05  

## 继承（承载）

| ID | 条款 | 出处 |
|---|---|---|
| H1 | 选取 R；k≥10；bootstrap 10000 / seed `20261007` | ADR-0034 · PREREG-B/Y |
| H2 | T/B1 同 after 再分叉；软对齐（非强制抄句） | ADR-0035 · PREREG-Y |
| H3 | 结果只抄同一次 `compare_primary`；一预注册一正式主跑 | #416 · PREREG-Y |
| H4 | 门闩可扔报告不进 RESULT；未过不得激活 | ADR-0037 · PREREG-Y |
| H5 | 不改生产检索常量；不改主张复验金标 | PREREG-Y |
| H6 | 解码串：`qwen-flash` / temp=0 / Decoding.seed=`20261007` / API seed=`None` | RESULT-B 跑针 · PREREG-Y |

## 增量（实装）

| ID | 条款 | Acceptance 种子 |
|---|---|---|
| Y1 | 旁路 `patch_events_formal_y`：默认不发；须激活 + `--authorize-send` | 未激活时 `--authorize-send` 拒绝；不写 b/c jsonl |
| Y2 | 正式名单 n=400（余数规则 50/50×4）；pilot 不进 | loader 返回 400 互异 id；与 pilot 无交；缺额 → **不可激活**（禁改小配额） |
| Y3 | `GATE-Y-PROBE`：过门 = k≥10 ∧ T−C 点估计>0；B1/B2 只报 | 报告含判定表与层身份「可扔」；夹具绿 ≠ 过门 |
| Y4 | RESULT-Y 成立口径：仅 T−C 且点>0.05∧下界>0；B1/B2 报告-only | 单测：三行均过经典「点>0∧下界>0」但 T−C 点≤0.05 → 分层丙；不得判甲 |
| Y5 | 产物路径 `formal-generations-y.jsonl` / `data/exp/patch-events-y/` | 禁止写 `*-b`/`*-c`/旧 formal jsonl |
| Y6 | B/C 负结果附录句保持在协议/结果壳 | 文面含 RESULT-B 丙锚点与 C 非主路径；禁同页翻 B/C |
| Y7 | 缺额解锁：扩 `pe_v2`（ADR-0038）；PE-Y-05 停泊至库存可满 400 | 扩容后 route-y SPLIT 可加载 400；**仍**未激活直至过门+人令 |

## 主缝

**主缝不在改比较器**，而在：

1. **formal-y 旁路**克隆 `patch_events_formal_b`（名单 n=400、激活守卫、解码针、抄表）；  
2. **GATE-Y** 克隆 `patch_events_gate_k_probe`（过门条件改对齐乙）；  
3. **RESULT-Y / outcome_tier_y**：在同一次 `compare_primary` 输出上套用 Y 成立尺（仅 T−C∧点>0.05∧下界>0；永不甲）。

`compare_primary` 保持唯一真相源；禁止新造 `compare_y`。

## 用户故事（派工用）

1. As a 评测工程师, I want formal-y 默认不发且未激活拒绝发送, so that 门闩不被绕过。  
2. As a 评测工程师, I want n=400 名单针可复现, so that 功效预登记可执行。  
3. As a 纪律官, I want GATE-Y 过门只看 k 与 T−C 方向, so that 门闩对齐冲乙而非冲甲。  
4. As a 纪律官, I want RESULT-Y 永不判甲且 B1/B2 不进成立, so that 放弃甲防火墙可测。  
5. As a 抄表守门人, I want 成立格只抄同一次 compare_primary, so that 不能手填/抄门闩。  
6. As an 面试讲解者, I want 固定引用 B 丙与 C 非主路径附录, so that 不装从零开始。  
7. As a 密钥守门人, I want 探针令与正式激活令分开, so that 探针不能冒充主跑授权。  
8. As a wayfinder, I want 票序硬门→门闩→名单/路径→抄表壳→（人授）正式主跑, so that 不倒置。  

## 票序建议

| 序 | 票 ID | 内容 | Trust |
|---|---|---|---|
| 1 | PE-Y-01 | formal-y 旁路骨架 + 激活守卫 + 默认不发（克隆 formal_b；点 Y 路径） | Watch |
| 2 | PE-Y-02 | GATE-Y-PROBE 报告格式 + 过门判定（k≥10∧T−C点>0）+ 夹具/复算；可扔 | Watch |
| 3 | PE-Y-03 | n=400 名单针（`SPLIT-pe-v2-route-y.json` 或显式超集登记） | Watch |
| 4 | PE-Y-04 | RESULT-Y 抄表口径（仅 T−C∧点>0.05；禁甲；B/C 附录） | Watch |
| 4b | PE-Y-CORPUS-01 [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500) | **（ADR-0038）** 扩 `pe_v2` 至可满 n=400+共形预留；禁改配额表 | Watch |
| 4c | PE-Y-CORPUS-02 [#501](https://github.com/luxingjiang1993/FreshLatch/issues/501) | **（ADR-0038）** 重针 `SPLIT-pe-v2-route-y.json` 离开不可激活；禁激活 | Watch |
| 5 | PE-Y-05 | **（库存可执行 + 过门 + 人授后）** 激活 + 一次正式主跑 + 抄成立格 | **Gate** |
| 6 | PE-Y-06 | （可选）消融/抽检导出；不改成立格 | Watch |

**缺额闸（PE-Y-05 前）**：`pe_v2≈178 < 400` 时 PE-Y-05 **不派**；解锁主路径见 ADR-0038（扩语料）。禁止为凑数改小配额。

**人令闸（PE-Y-05）** — 缺则停，禁止自批：

> 批准激活 PREREG-Y 并正式主跑一次。

探针令（「授权路线 Y 仓外探针发模型；不得激活。」）**不得**当作 PE-Y-05 授权。

## 基线依赖

工程实现宜叠在 B 机制已合入的针上（选取 R · 同 after · 软对齐核验）。若 B PR 尚未合 `main`，feat 票须写明 base 分支 / 依赖 PR（建议 tip `origin/cursor/prereg-b-formal-main-9809` 或已合入等价针），禁止假装从空分 top-k 重开，禁止引入 C 抄句契约作主路径。

## 云端派工

见 `docs/agents/patch-events-route-y-cloud-dispatch.md`。主代理边界：本 to-spec **可不含** `run_arms` 业务实现；由 enrich 后的 feat 票分窗 `/before-implement` → 新会话 `/implement`。

## 失败止损

- 门闩长期不过：保持未激活；改机制另决议，禁止改成立尺凑过门。  
- 正式主跑触发止损（点≤0.05 或下界≤0）→ **结果丙**；禁止加 n / 同页二跑。  
- 语料长期无法扩至 400：停泊保持；若人放弃功效，**另开**透明改 n 决议（不得静默改表）。  
- 不删 B/C/ALT 归档。
