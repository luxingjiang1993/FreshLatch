# §18 must_fresh 护栏：c5 反事实/敏感性误 stale

> 来源：L3 金标 `run` N=1（`report-20261001-010433`）→ must_fresh 漏判 `c5→stale`；与 #243（c6 支撑复盘读反，CLOSED）分机制  
> 词表：`CONTEXT.md`  
> 上游权威：`skills/freshness_audit/references/verdict-rubric.md`、Lead persona「只有 T1 明确推翻才 stale」、#243 / `gates/support_review.py`（邻族误拦，本票不回退）  
> 证据锚：  
> - `reports/report-20261001-010433.md`（混淆矩阵 `c5→stale`；10/12；`all_hit=False`；乙-ii 已标 c5）  
> - 轨迹 `reports/trajectories/run-20261001-010246.jsonl`  
> - 金标 `data/eval/gold.json` → `causal_chain.c5`（`t0-cost-model#p2`，why_fresh）  
> **测试主缝（预锁）：**  
> 1. **敏感性/反事实不得当现时推翻** — 教义/rubric/persona +（必要时）薄启发式：含「若…则需重新评估 / 进一步降价至…档」等**未实现情景**的 reason，不得单独支撑 `mark_stale`；现时结论以同维现时段落为准  
> 2. **回归护栏** — 同 decoding 下 **c3、c7 仍为 stale**；**c6=fresh**（#243 不回退）；**c9=unknown**（#241 不回退）；违例级 `must_stale→fresh` = **0**  
> 子缝：确定性夹具注入本跑 c5 实录 reason（及最小「若…需重评」合成形）⇒ 可断言打回/纠正。**优先只暴露两条主缝。**

---

## Problem Statement

#243 已按 Acceptance 修好 must_fresh c6（支撑复盘读反 → fresh，曾一度 `all_hit=True`）。同尺后续 N=1（`report-20261001-010433`）出现**新** must_fresh 漏判：

| 样本 | 期望 | 机判 | 说明 |
|------|------|------|------|
| gold `c5` | must_fresh | stale | Lead/Auditor 以 `t0-cost-model#p3` 敏感性句「若竞品进一步降价至 49 美元档…需重新评估」为反证；忽略同文档 `p2`「结论维持 / 约为竞品 47%」 |
| 全量 | 12/12 | 10/12 | `all_hit=False`；另有 must_unknown `c10→stale`（**另票** §19，不并进本规格 Exit） |

这**不在** #243 Acceptance 内。机制与 c6 不同：不是把支撑复盘读反，而是把**假设情景/敏感性分析**当成**当前事实已推翻**。

### 根因（本跑轨迹，机制级）

主张 c5（must_fresh）：「我方单会话服务成本仍低于竞品」。

金标支撑：`t0-cost-model#p2@T1`（复测 0.009 vs 竞品约 0.019，结论维持）。

本跑 Lead 落 `mark_stale`，证据落到 **`#p3`**：

> 敏感性更新:…若竞品进一步降价至 49 美元档,我方成本优势将收窄至约 20%,**需重新评估**。

金标语义：`p3` 是**未实现情景的敏感性**；现时结论在 `p2` 仍成立。Lead/Auditor reason 把「若…需重新评估」写成「在当前竞品报价下…『仍低于』不成立」——属**反事实升格为现时推翻**（误拦），不是元陈述逃逸、不是维度跨检失败（本跑 `dimension_match=true`）。

报告乙-ii 已标「维度疑似混淆 / 锚未对齐」；J1 对 c5 金标锚未命中。

## Solution

交付一次**可选**工程修复（非判据修订）：使 c5 在预锁 decoding 下回 `fresh`，且不回退 #239/#241/#243。

默认主路径（薄票，优先教义/受理语义；闸大改须另开决议）：

1. **教义/rubric/persona（主缝）**：明确「敏感性 / 反事实 /『若…则』情景 ≠ 现时推翻」；现时 must_fresh 须落在同维**现时**支持段落；「需重新评估」 alone 不是 stale 锚。  
2. **确定性夹具（辅）**：注入本跑 c5 实录 reason（或最小「若竞品进一步降价…需重新评估 ⇒ 当前仍低于不成立」合成形）⇒ 工具层/教义路径可断言纠正；**禁止** `claim_id` 特判。  
3. **薄启发式（可选辅缝）**：若教义 alone 不够稳，可扩 `support_review` 邻族或平行薄模块（句法标记：`若`+`需重新评估` / `进一步降价至`+推翻结论），误伤方向单向（stale 打回 → 引导 fresh）；**禁止**本票内偷渡新闸族大改——若必须动 ADR 级算法 → **停**，另开评估。  
4. **活模验收（表现层，N=1）**：点名 `c5=fresh` + J1 命中 `t0-cost-model#p2@T1`；回归 c3/c7/c6/c9 与违例级 0。

**禁止**：改 `data/eval/gold.json` / 把 c5 改出 must_fresh；提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维；回滚 #239/#241/#243；LLM judge；按 `claim_id` 硬编码放行。

> Anthropic 清单：N=1 只报命中不报方差；止损预先锁定；**工程修复 ≠ 改尺子**；全量 `all_hit` **默认非**本票硬 Exit（可选加分须明示）。

## User Stories

1. As an 验收者, I want 修后 N=1 gold 下 c5 机判为 fresh, so that must_fresh 不再被敏感性句误拦。  
2. As an 验收者, I want J1 命中 `t0-cost-model#p2@T1`, so that 现时锚回金标。  
3. As an 验收者, I want 同次跑 c3 与 c7 仍为 stale, so that must_stale 不回退。  
4. As an 验收者, I want 同次跑 c6=fresh、c9=unknown, so that #243/#241 不回退。  
5. As an 验收者, I want 违例级 must_stale→fresh 仍为 0, so that 不对称安全不破。  
6. As an 验收者, I want N=1 只报命中不报方差, so that 不假装统计测量。  
7. As an 验收者, I want 止损预先锁定且禁止改 gold 凑绿, so that 不 HARKing。  
8. As a 教义维护者, I want rubric/persona 明确「若…则 / 敏感性 ≠ 现时推翻」, so that 提示词与夹具同向。  
9. As a 闸守护者, I want 本跑 c5 实录 reason 有可断言打回/纠正路径, so that 机制级闭合。  
10. As a 闸守护者, I want 最小「若…需重新评估 + 推翻『仍低于』」合成形同样打回, so that 不依赖整段长 reason。  
11. As a 闸守护者, I want c3/c7 合法数值锚形状仍放行, so that 真反证不被误伤。  
12. As a Lead 调用方, I want `mark_stale` 对反事实升格形在工具层提前打回并指向同维现时 fresh, so that 环内可恢复。  
13. As a 产品负责人, I want 不改 gold.json / must_fresh 期望档, so that 尺子不变。  
14. As a 产品负责人, I want 不把「全量 all_hit」静默升为本票硬 Exit, so that 范围不膨胀（可选加分须明示）。  
15. As a 产品负责人, I want c10 缺口误 stale **不**绑进本票 Exit, so that 与 §19 分票。  
16. As an AFK agent, I want Paths 与 Acceptance 可执行, so that 可按序实现。  
17. As an 面试讲解者, I want 能讲清「p3 敏感性被升格为现时推翻、忽略 p2 结论维持」, so that 中级可过追问。  
18. As a 复现工程师, I want decoding 与报告路径入档, so that 跨会话只求近似。  
19. As a 架构守护者, I want 优先教义+薄启发式、禁止 claim_id 特判, so that 不偷渡新闸大改。  
20. As a 文档维护者, I want evidence/报告追加 post-fix 段而非改历史失败叙事, so that 诚实。

## Implementation Decisions

### 主缝与模块

- **主缝 1（反事实不得当现时推翻）**：`skills/reverify/SKILL.md`、`skills/freshness_audit/references/verdict-rubric.md`、Lead/Critic persona；必要时 `roles/lead.py` `mark_stale` 受理反馈文案；可选扩 `gates/support_review.py` 邻族形 D（或平行薄模块），经工具层 + `rule_gate` 打回。  
- **主缝 2（回归）**：活模点名 c3/c7/c6/c9；确定性侧保留既有合法 stale / #241 meta / #243 support_review 测。  
- **非目标模块**：retrieve、HumanLatch、I2、gold.json、DIMENSION_RECOVERY_QUOTA、§19 c10 Exit。

### 启发式方向（预锁意图；实现前可微调措辞，不可改 Exit）

| 候选 | 原理 | 风险 |
|------|------|------|
| A. 教义 alone | 「若/敏感性/需重新评估 ≠ 现时推翻」写进 rubric/persona + 工具反馈 | 端点漂移可再击穿 |
| B. 薄句法形 D | reason 合取（情景标记 ∧ 推翻结论）⇒ 打回；引导回同维现时 fresh | 须预登记误伤表；不得误伤真「已降价至 X」现时句 |
| C. 读 T1 正文比对 p2 vs p3 | 语义强 | **否**（与 ADR-0008/闸纪律同向：禁闸读正文语义比对） |

**推荐默认：A + B（薄）**；C 弃。B 的「现时已发生降价」合法 stale 须放行（预登记对照形）。

### API / 契约（逻辑）

- 若新增判定函数：签名风格对齐 `is_support_review_misread(reason) -> bool`；打回码新建封闭枚举值（如 `COUNTERFACTUAL_AS_OVERTURN`）或并入 support_review 族——实现票二选一，PR 写明。  
- **禁止**：LLM judge；闸读证据正文；为 c5 特判 `claim_id`。

## Testing Decisions

- **好测试**：断言外部行为（打回/放行；落档 status），不锁模型品牌文案像素。  
- **确定性（硬门）**：  
  - 新测：本跑 c5 实录 reason + 最小反事实合成形 ⇒ 打回/纠正路径 True。  
  - 旧测全绿：`test_support_review_*`、`test_meta_gate*`、c3/c7 合法锚。  
  - 合法「现时已降价推翻成本优势」形仍放行（预登记合成）。  
- **表现层（冒烟，N=1）**：  
  - decoding：`qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
  - `python -m freshlatch.eval run --gold data/eval/gold.json --runs 1` → **c5=fresh**；J1=`t0-cost-model#p2@T1`；**c3/c7=stale**；**c6=fresh**；**c9=unknown**；must_stale→fresh=0  
  - 不报方差；不声称 Hard-Gold  
- **可选加分（非默认 Exit）**：同跑 12/12 / `all_hit=True`——须在实现票 Acceptance 显式勾选；默认只记读数。  
- **止损**：B 未过 → 如实登记，**不改 gold**，禁止第二次改本票 Acceptance/止损凑绿；若收紧导致 c3/c7 误伤或 c6/c9 回退 → 本票失败，回退并重签。

## Acceptance（预锁 · 先于实现）

**A. 确定性**

- [ ] `python -m compileall -q src` exit 0  
- [ ] `python -m pytest tests/ -q` 全绿；不删测凑绿  
- [ ] 本跑 c5 实录（或最小合成）反事实升格形有可断言纠正/打回；#241/#243 相关测与 must_stale 合法锚测不红  

**B. 表现层（decoding 锁定；N=1 只报命中不报方差）**

- [ ] `qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
- [ ] 点名 gold run → **`c5=fresh`**；J1 命中 `t0-cost-model#p2@T1`（或 gold 登记锚）  
- [ ] 回归：`c3`/`c7`=`stale`；`c6`=`fresh`；`c9`=`unknown`；must_stale→fresh=**0**  
- [ ] 不声称 Hard-Gold / 统计显著；不把 N=1 冒充方差  

**C. 文档 / 未声称**

- [ ] 报告/轨迹指针入档；本规格追加 post-fix  
- [ ] **未**改 `data/eval/gold.json`  
- [ ] 全量 `all_hit` 非默认硬 Exit（除非实现票显式勾选加分）  

**止损（预锁）**

- B 未过 → 如实登记失败；**禁止改 gold**；**禁止第二次改本票 Acceptance/止损**凑绿。  
- 若收紧误伤 c3/c7 或回退 c6/c9 → 本票失败，回退变更并重签。  
- N≥3 / Hard-Gold → **另开评测票**。

## Out of Scope

- 改金标期望档或 causal_chain 凑绿  
- 把 §19（c10 缺口误 stale）并进本票 Exit  
- 静默把全量 `all_hit` 升为本规格硬 Exit  
- 新闸算法大改 / 读 T1 正文语义比对 / LLM judge / claim_id 特判  
- 旧 `control` 对照成立（仪器问题，非本票）  
- 干扰项 c13/c14 通过线（附表，不计本票 Exit）

## Paths（实现票可微调）

- `skills/reverify/SKILL.md` / `skills/freshness_audit/references/verdict-rubric.md` / Lead·Critic persona（主）  
- 必要时：`src/freshlatch/roles/lead.py` 工具层反馈；`src/freshlatch/gates/support_review.py`（或平行薄模块）+ `rule_gate` 接线  
- `tests/unit/` 确定性夹具（新增或扩）  
- `docs/spec/18-must-fresh-c5-反事实敏感性.md`（本规格；实现后回填）  
- 报告：`reports/report-*.md` / `reports/trajectories/`

## 参考

- #243 · `docs/spec/17-must-fresh-c6-all-hit.md`（邻族 must_fresh 误拦，CLOSED）  
- #241 · `docs/spec/16-must-unknown-c9-护栏.md`（must_unknown 元陈述，CLOSED）  
- §19 · `docs/spec/19-must-unknown-c10-缺口误stale.md`（同次跑另一漏点，分票）  
- `data/eval/gold.json` · `causal_chain.c5`  
- 证据：`reports/report-20261001-010433.md` · `reports/trajectories/run-20261001-010246.jsonl`

## Further Notes

- **规格状态**：implemented（2026-10-01）。  
- **实现票**：[GitHub #245](https://github.com/luxingjiang1993/FreshLatch/issues/245)（与 #246 并行）。  
- **与 #243 边界**：#243 = 支撑复盘/旁近定价读反；本规格 = 反事实/敏感性升格 + 成本当窗口。分票、分 Acceptance。  
- **面试一句**：p2 说「结论维持」，p3 说「若再降价才需重评」——把「若」当成「已」，就是本票要堵的洞。

## Post-mortem（实现后回填 · #245）

- **解码锁定**：`qwen-flash` · `temperature=0.0` · `seed=None` · 报告 UTC `2026-09-30T17:51:05` 附近。
- **确定性**：`test_support_review_*` / `test_media_lag_gap.py` 覆盖 c5 反事实形、c6 成本当窗口形、媒体滞后误 gap；`compileall` + 全量 pytest **705 passed**。
- **实现主缝**：教义/rubric/persona + `support_review` 形 D/E；辅缝 `mark_gap` 拒媒体滞后当缺口。
- **表现层（N=1 冒烟，不报方差）**：
  - 报告：`reports/report-20261001-015105.md`
  - 原始：`reports/report-20261001-015105.json`
  - 点名：`c5=fresh`（J1=`t0-cost-model#p2@T1`）；`c3`/`c7`=`stale`；`c6`=`fresh`；`c9`=`unknown`；must_stale→fresh=0；同跑 **`all_hit=True`（12/12）**（加分读数，不声称 Hard-Gold）
- **未声称**：不改 gold；不声称 Hard-Gold / 统计显著。
