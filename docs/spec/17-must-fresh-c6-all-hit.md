# §17 可选薄票：must_fresh c6 误 stale → 追 gold `all_hit`

> 来源：#241 post-fix 读数（`all_hit=False`，仅剩 `c6→stale`）+ `REPORT-20260930-REMAINING`「修到 all_hit 须另开票」  
> 实现票：[GitHub #243](https://github.com/luxingjiang1993/FreshLatch/issues/243)  
> 性质：**可选**工程修复薄票（非判据修订）；本规格**显式**把全量 `all_hit` 升为本票硬 Exit（与 #241「all_hit 非硬 Exit」分票）  
> 词表：`CONTEXT.md`  
> 证据锚：  
> - `reports/report-20260930-232556.md`（混淆矩阵 `c6→stale`；11/12；`all_hit=False`）  
> - 轨迹 `reports/trajectories/run-20260930-232438.jsonl`  
> - 金标 `data/eval/gold.json` → `causal_chain.c6`（`t0-competitor-news#p2`，why_fresh）  
> **测试主缝（预锁）：**  
> 1. **c6 不得误拦** — 同 decoding N=1：`c6=fresh`，且 J1 命中金标锚 `t0-competitor-news#p2@T1`（或等价登记锚）  
> 2. **全量 all_hit** — 同跑 12/12 / `all_hit=True`；且 **不回退** #239/#241：`c3`/`c7`=stale、`c9`=unknown、must_stale→fresh=0  

---

## Problem Statement

#241（CLOSED）已按 Acceptance 修好 must_unknown 护栏（c9 元陈述+主张数字回声）。同次活模 N=1（`report-20260930-232556`）读数：

| 期望档 | 命中 | 漏判 |
|--------|------|------|
| must_stale | 4/4 | 无 |
| must_fresh | 3/4 | **c6→stale** |
| must_unknown | 4/4 | 无 |
| 全量 | 11/12 | `all_hit=False` |

**只剩 c6**。若不追表现绿，可停；若还追 gold `all_hit`，必须**另开本票**，不得并进 #241、不得改 gold 凑绿。

### 根因（本跑轨迹，机制级）

主张 c6（must_fresh）：「竞品 SeaDesk 收缩东南亚免费版、聚焦付费商户,意味着市场窗口打开」。

金标支撑：`t0-competitor-news#p2@T1`（免费版收缩属实、付费续约 91%、亏损集中免费版）。

本跑 Lead 落 `mark_stale`，证据落到 **`#p3`**（非金标锚）：

> 3 月有分析认为免费版收缩意味着「市场付费意愿低、窗口不佳」；**9 月回看，SeaDesk 付费续约率与该判断不符**…

金标语义：这段是**否定当时「窗口不佳」误判**，因而**支撑**「窗口打开」。Lead/Auditor 把「与该判断不符」读成**推翻主张**，属于**支撑复盘读反当反证**（误拦），不是元陈述逃逸、不是闸消失。

报告乙-ii 已标「维度疑似混淆 / 锚未对齐」；J1 对 c6 金标锚未命中。历史 I1 `i1-s002` 为同主张另一形状（找错到 `competitor-notes`），本票以 **2026-09-30 本跑** 为主证据。

## Solution

交付一次**可选**工程修复：使 c6 在预锁 decoding 下回 `fresh`，同跑达到 `all_hit=True`，且不回退 #239/#241。

默认主路径（薄票，优先教义/受理语义，不新开闸族）：

1. **教义/rubric/persona（主缝）**：明确「复盘否定当时『窗口不佳』分析 ≠ 主张被推翻」；支撑段落不得当反证；must_fresh 干扰项「看似死其实活」须走 fresh / 同维核实，不得因旁近叙事误 stale。  
2. **确定性夹具（辅）**：注入本跑 c6 实录 reason（或最小「把『与该判断不符』当推翻」合成形）⇒ 工具层/教义断言可见纠正；不得 `claim_id` 特判。  
3. **活模验收（表现层，N=1）**：点名 `c6=fresh` + 全量 `all_hit=True`；回归 c3/c7/c9 与违例级 0。

**禁止**：改 `data/eval/gold.json` / 把 c6 改出 must_fresh；提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维；回滚 #239/#241；LLM judge；按 `claim_id` 硬编码放行。

> Anthropic 清单：本票 Exit 含表现层 `all_hit`（显式预锁，非事后升格）；N=1 只报命中不报方差；失败止损预先锁定；**工程修复 ≠ 改尺子**。

## Acceptance（预锁 · 先于实现）

**A. 确定性**

- [x] `python -m compileall -q src` exit 0  
- [x] `python -m pytest tests/ -q` 全绿；不删测凑绿  
- [x] 本跑 c6 实录（或最小合成）读反形有可断言纠正/打回路径；既有 #241 meta 测与 must_stale 合法锚测不红  

**B. 表现层（decoding 锁定；N=1 只报命中不报方差）**

- [x] `qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
- [x] 点名 gold run → **`c6=fresh`**；J1 命中 `t0-competitor-news#p2@T1`（或 gold 登记锚）  
- [x] 同跑 **`all_hit=True`（12/12）**  
- [x] 回归：`c3` 与 `c7` = `stale`；`c9` = `unknown`；must_stale→fresh = **0**  
- [x] 不声称 Hard-Gold / 统计显著；不改通过线文档把 N=1 冒充方差  

**C. 文档 / 未声称**

- [x] 报告/轨迹指针入档；规格或 evidence 追加 post-fix  
- [x] **未**改 `data/eval/gold.json`  

**止损（预锁）**

- B 未过 → **如实登记失败**，关闭或重开评估；**禁止改 gold**；**禁止第二次改本票 Acceptance / 止损线**凑绿。  
- 若教义收紧导致 must_stale（c3/c7）误伤或 c9 再逃逸 → 本票失败，回退变更并重签，不得用「平均 11/12」糊弄。  
- N≥3 方差 / Hard-Gold 声称 → **另开评测票**，不在本薄票范围。

## Out of scope

- 改金标期望档或 causal_chain 凑绿  
- 静默并进 #241 / 把本票失败算作 #241 未完成  
- 新闸算法大改（若实现中发现必须动闸 → **停**，另开决议/评估，不得本票内偷渡）  
- I1 `i1-s002` 历史轨迹重写（可互指，不作本票唯一 Exit）

## Paths（实现票可微调）

- `skills/reverify/SKILL.md` / `skills/freshness_audit/references/verdict-rubric.md` / Lead·Critic persona（主）  
- 必要时：`src/freshlatch/roles/lead.py` 工具层反馈文案（不改 gold）  
- `tests/unit/` 确定性夹具（新增或扩）  
- `docs/spec/17-must-fresh-c6-all-hit.md`（本规格；实现后回填）  
- 报告：`reports/report-*.md` / `reports/trajectories/`

## 参考

- #241（上游 must_unknown 护栏，CLOSED；all_hit 非其硬 Exit）  
- #239（换维/反默认，CLOSED）  
- `docs/evidence/full-repo/REPORT-20260930-REMAINING.md`（「修到 all_hit 须另开票」）  
- `docs/evidence/i1/i1-s002-c6-误拦-找错.md`（历史同主张另一形状）  
- `data/eval/gold.json` · `causal_chain.c6`

## Post-mortem（实现后回填 · #243）

- **解码锁定**：`qwen-flash` · `temperature=0.0` · `seed=None` · 报告 UTC `2026-09-30T16:48:38` 附近。
- **确定性**：`tests/unit/test_support_review_misread.py` / `test_support_review_tool_feedback.py` / `test_support_review_routing.py` 覆盖 c6 实录读反形、旁近 Lite 定价形、支撑事实反读形；#241 meta 测与 c3/c7 合法锚不红；`compileall` + 全量 pytest 绿。
- **实现主缝**：教义/rubric/persona 钉死「复盘否定窗口不佳 ≠ 主张被推翻」+「续约率/毛利核实 ⇒ 必须 fresh」；辅缝薄启发式 `gates/support_review.py`（工具层+rule_gate 打回 `SUPPORT_REVIEW_MISREAD`，非新闸族大改）。
- **表现层（N=1 冒烟，不报方差）**：
  - 报告：`reports/report-20261001-004837.md`
  - 原始：`reports/report-20261001-004837.json`
  - c6 轨迹：`reports/trajectories/run-20261001-004704.jsonl`
  - 点名：`c6=fresh`（J1 命中 `t0-competitor-news#p2@T1`）；`c3`/`c7`=`stale`；`c9`=`unknown`；must_stale→fresh=0；**`all_hit=True`（12/12）**
- **未声称**：不改 gold；不声称 Hard-Gold；N=1 只报命中。
- **规格状态**：implemented（2026-10-01）。
- **实现票**：[GitHub #243](https://github.com/luxingjiang1993/FreshLatch/issues/243)。
