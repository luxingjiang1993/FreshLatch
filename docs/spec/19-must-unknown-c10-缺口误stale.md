# §19 must_unknown 护栏：c10 数据缺口误 stale

> 来源：L3 金标 `run` N=1（`report-20261001-010433`）→ must_unknown 漏判 `c10→stale`；与 #241（c9 元陈述+数字回声，CLOSED）同族再犯、不同逃逸形  
> 词表：`CONTEXT.md`  
> 上游权威：ADR-0008（不变量 6 / 元陈述闸）、`gates/meta_gate.py`、Lead persona「无新数据 → mark_gap + unknown」、#241 算法 A（主张数字回声）  
> 证据锚：  
> - `reports/report-20261001-010433.md`（混淆矩阵 `c10→stale`；10/12；`all_hit=False`）  
> - 轨迹 `reports/trajectories/run-20261001-010402.jsonl`  
> - 金标 `data/eval/gold.json` → must_unknown 含 `c10`；语料 `t0-talent-salary#p2`（数据缺口声明）  
> **测试主缝（预锁）：**  
> 1. **缺口/无更新不得当推翻** — `is_meta_only_disproof` / `mark_stale` 工具层 / `rule_gate` 不变量 6：含「无新测量 / 无更新记录 / 数据缺口 / 调研已过时且无新测」等且无独立实质反证时，不得落档 `stale`（须打回并路由 `unknown`）  
> 2. **回归护栏** — 同 decoding 下 **c9=unknown**（#241 不回退）；**c3、c7 仍为 stale**；违例级 `must_stale→fresh` = **0**  
> 子缝：教义「无更新 ≠ 推翻」可断言片段；c5 反事实误拦归 §18，**不**绑本票 Exit。**优先只暴露两条主缝。**

---

## Problem Statement

#241 已堵住 c9「元陈述 + 主张数字回声」逃逸。同尺后续 N=1（`report-20261001-010433`）出现**新** must_unknown 漏判：

| 样本 | 期望 | 机判 | 说明 |
|------|------|------|------|
| gold `c10` | must_unknown | stale | T1 `t0-talent-salary#p2` 为**数据缺口声明**（本期无新测量；2 月 450 之后无更新）；Lead 写成「数据已过时 ⇒ 前提被推翻」并 `mark_stale` |
| 全量 | 12/12 | 10/12 | `all_hit=False`；另有 must_fresh `c5→stale`（**另票** §18，不并进本规格 Exit） |

这**不在** #241 Acceptance 内。机制同族（缺口当推翻），逃逸形不同：标记词表未覆盖「无新测量 / 无更新记录 / 已过时」，`has_meta` 未触发 ⇒ 整段 reason **放行**（即使含主张数字 450）。

### 根因（本跑轨迹，机制级）

主张 c10（must_unknown）：「雅加达双语客服专员综合用工成本约 450 美元/月」。

T1 原文（缺口演练）：

> 数据缺口声明:…本期**无新测量**；…2 月调研数据(雅加达约 450 美元/月…)之后**无任何更新记录**进入本档。

本跑 `mark_stale` reason 要旨：无新测量 + 无更新 ⇒「450 数据已过时」⇒「主张前提被 T1 原文明确推翻」。

对照 `meta_gate.py` 封闭标记（节选）：`未复测` / `无新数据` / `本期未` / …  
本跑用的是 **`无新测量` / `无任何更新记录` / `已过时`**——**不在**现行封闭词表子串命中集内 ⇒ `has_meta=False` ⇒ `is_meta_only_disproof` 返回 False（放行）。  
故：**不是闸消失，是标记词表/缺口 paraphrase 逃逸**——与 ADR-0008「标记封闭、增补走评审」同纪律；人格层「无新数据→unknown」再次被端点漂移击穿，机械闸未兜住新 paraphrase。

Auditor `dimension_match=true`；问题在元/缺口受理，不在维度跨检。

## Solution

交付一次**工程修复（非判据修订）**：堵住「数据缺口声明 / 无新测量 / 无更新」当推翻的逃逸，使 c10 在预锁 decoding 下回 `unknown`，同时**不**回退 #241/#239。

默认主路径（实现顺序可拆，Exit 绑死）：

1. **闸层（主缝 1）**：在 ADR-0008 包络内**评审增补** `_META_MARKERS`（及必要的缺口 paraphrase），使本跑 c10 实录 reason（及最小合成形）⇒ `is_meta_only_disproof` True；算法 A（主张数字回声）保持。增补清单须**先于实现**写入本规格 Testing Decisions / 短评估补丁；**禁止**静默扩词表凑绿。  
2. **教义/persona（辅）**：重申「无新测量 / 无更新 / 数据缺口声明 / 待复核 = 证据缺口 → `mark_gap` + unknown」；**过时未更新 ≠ 已被推翻**。  
3. **确定性单测**：注入本跑 c10 实录 reason + 最小缺口合成形 ⇒ 必打回；历史 c9 形与 c3/c7 合法锚回归。  
4. **活模验收（表现层，N=1）**：点名 `c10=unknown`；回归 `c9=unknown`、`c3`/`c7`=stale。

**禁止**：改 `data/eval/gold.json`；把 c10 期望改成 stale；提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维；回滚 #241 算法 A；LLM judge；按 `claim_id` 特判。

> Anthropic 清单：扩封闭标记 = 止损相关机制变更，须预登记误伤方向（单向 stale→unknown）；N=1 只报命中；全量 `all_hit` **默认非**硬 Exit。

## User Stories

1. As an 验收者, I want 修后 N=1 gold 下 c10 机判为 unknown, so that must_unknown 护栏覆盖缺口声明形。  
2. As an 验收者, I want 同次跑 c9 仍为 unknown, so that #241 不回退。  
3. As an 验收者, I want 同次跑 c3 与 c7 仍为 stale, so that must_stale 不回退。  
4. As an 验收者, I want 违例级 must_stale→fresh 仍为 0, so that 不对称安全不破。  
5. As an 验收者, I want N=1 只报命中不报方差, so that 不假装统计测量。  
6. As an 验收者, I want 止损预先锁定且禁止改 gold 凑绿, so that 不 HARKing。  
7. As a 闸守护者, I want 本跑 c10 实录 reason 注入 `is_meta_only_disproof` 为 True, so that 逃逸形状机制级闭合。  
8. As a 闸守护者, I want 最小「本期无新测量 / 无更新记录 / 已过时」合成形同样打回, so that 不依赖整段长 reason。  
9. As a 闸守护者, I want 历史 c9 回声形与 C9_RUN2 仍打回, so that #241/ADR-0008 回归不丢。  
10. As a 闸守护者, I want c3/c7 合法数值锚形状仍放行, so that 真反证不被误伤。  
11. As a Lead 调用方, I want `mark_stale` 对缺口形在工具层提前打回并指向 mark_gap+unknown, so that 环内可恢复。  
12. As a Critic 调用方, I want 同判定函数打回（出口按白名单适配）, so that 单一真相。  
13. As a runner, I want 闸 `META_ONLY_DISPROOF` 仍经既有 stale→unknown 路由, so that 落档口径不变。  
14. As a 教义维护者, I want rubric/persona 明确「无更新/缺口声明 ≠ 推翻」, so that 提示词与闸同向。  
15. As a 产品负责人, I want 不改 gold.json / must_unknown 期望档, so that 尺子不变。  
16. As a 产品负责人, I want 不把「全量 all_hit」静默升为本票硬 Exit, so that 范围不膨胀。  
17. As a 产品负责人, I want c5 反事实误 stale **不**绑进本票 Exit, so that 与 §18 分票。  
18. As an AFK agent, I want Paths 与 Acceptance 可执行, so that 可按序实现。  
19. As an 面试讲解者, I want 能讲清「无新测量 paraphrase 击穿封闭词表 → 评审增补而非改金标」, so that 中级可过追问。  
20. As a 复现工程师, I want decoding 与报告路径入档, so that 跨会话只求近似。  
21. As a 架构守护者, I want 判定引擎仍单一真相在 `meta_gate.py`, so that 不复制三份逻辑。  
22. As a 文档维护者, I want 标记增补写入评估补丁/本规格预登记表, so that 不违反 ADR-0008 封闭词表纪律。

## Implementation Decisions

### 主缝与模块

- **主缝 1（缺口不得当推翻）**：行为真相在 `src/freshlatch/gates/meta_gate.py` 的 `is_meta_only_disproof`；Lead/Critic 工具层与 `rule_gate` 不变量 6 **共用**。修逃逸 = **评审增补标记 / 缺口 paraphrase**，不是新建第二套闸。  
- **主缝 2（回归）**：活模点名 c9/c3/c7；确定性侧保留 #241 回声形与合法 stale 形。  
- **教义辅路径**：reverify / verdict-rubric / persona 中「无新数据」纠正表——扩写「无新测量 / 缺口声明 / 过时未更新」。  
- **非目标模块**：retrieve、HumanLatch、I2、gold.json、§18 c5 Exit、DIMENSION_RECOVERY_QUOTA。

### 标记增补方向（预锁意图；实现前可微调措辞，不可改 Exit）

候选增补（实现票可子集，须在 PR/补丁列出终表）：

| 标记/形 | 意图覆盖 |
|---------|----------|
| `无新测量` / `无任何更新` / `无更新记录` | 本跑 c10 实录 |
| `数据缺口` / `数据缺口声明` | 语料标题句 |
| `已过时`（仅当与缺口/无更新共现时计元？或整词入表） | reason「数据已过时」——若整词入表须预登记误伤（真「价格已过时且 T1 给新价」须仍放行，靠实质数值锚） |

**推荐默认**：先增补高置信缺口短语（`无新测量`、`无更新记录`、`数据缺口`）；`已过时` 慎独入表，优先「与缺口标记共现才剥」或依赖算法 A + 缺口标记组合。  
**禁止**：为过「已过时」三字误伤一切含该词的合法 stale 而不写误伤表。

> 相对 ADR-0008：同题再犯（提示词被击穿 + 需机械闸）；本次是**标记/paraphrase 增量**，不是推翻「确定性句法启发式」选型。须短评估补丁（类比 #241 算法 A 补丁）。

### API / 契约（逻辑）

- `is_meta_only_disproof(reason, *, claim_statement=...)` 签名保持；打回码仍为 `META_ONLY_DISPROOF`；消息可微更，须指向 `mark_gap` + unknown。  
- **禁止**：LLM judge；闸读 T1 正文语义比对；为 c10 特判 `claim_id`。

### 历史形状对照

| 形状 | 今日闸 | 本规格目标 |
|------|--------|------------|
| #241 c9 回声形 / C9_RUN2 | 打回 | 打回（回归） |
| 本跑 c10 缺口 reason | **放行（逃逸）** | **打回** |
| 最小「本期无新测量…推翻」合成 | 放行（预期） | **打回** |
| `C3_LEGIT` / `C7_LEGIT` | 放行 | 放行（回归） |
| 元/缺口 + 独立实质数值锚（非主张回声） | 放行 | 放行 |

## Testing Decisions

- **好测试**：断言外部行为（打回/放行；落档 status）。  
- **确定性（硬门）**：  
  - 新测：本跑 c10 实录 reason + 最小缺口合成形 ⇒ `is_meta_only_disproof` True；经工具/runner 路径不得落 `stale`。  
  - 旧测全绿：`tests/unit/test_meta_gate.py`、`test_c9_meta_gate_*`、相关 rule_gate。  
  - c3/c7 合法形仍 False（放行）。  
- **表现层（冒烟，N=1）**：  
  - decoding：`qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
  - `python -m freshlatch.eval run --gold data/eval/gold.json --runs 1` → **c10=unknown**；**c9=unknown**；**c3/c7=stale**；must_stale→fresh=0  
  - 不报方差；不声称 Hard-Gold  
- **可选加分（非默认 Exit）**：同跑 12/12 / `all_hit=True`——须实现票显式勾选。  
- **止损**：B 未过 → 如实登记，不改 gold，禁止二次改判据；若扩标记导致 c3/c7 误伤 → 本票失败，回退词表边界并重签。

## Acceptance（预锁 · 先于实现）

**A. 确定性**

- [ ] `python -m compileall -q src` exit 0  
- [ ] `python -m pytest tests/ -q` 全绿；不删测凑绿  
- [ ] 本跑 c10 实录 + 最小缺口合成形 ⇒ `is_meta_only_disproof` True；#241 形与 c3/c7 合法锚不红  
- [ ] 标记增补表写入本规格或 `docs/research/` 短补丁（预登记）  

**B. 表现层（decoding 锁定；N=1 只报命中不报方差）**

- [ ] `qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
- [ ] 点名 gold run → **`c10=unknown`**  
- [ ] 回归：`c9`=`unknown`；`c3`/`c7`=`stale`；must_stale→fresh=**0**  
- [ ] 不声称 Hard-Gold / 统计显著  

**C. 文档 / 未声称**

- [ ] 报告/轨迹指针入档；本规格追加 post-fix  
- [ ] **未**改 `data/eval/gold.json`  
- [ ] 全量 `all_hit` 非默认硬 Exit（除非实现票显式勾选）  

**止损（预锁）**

- B 未过 → 如实登记；**禁止改 gold**；**禁止第二次改本票 Acceptance/止损**凑绿。  
- 扩标记误伤 c3/c7 或回退 c9 → 本票失败，回退并重签。  
- N≥3 / Hard-Gold → **另开评测票**。

## Out of Scope

- 修改 `data/eval/gold.json` / 将 c10 改出 must_unknown  
- 把 §18（c5 反事实误 stale）并进本票 Exit  
- 静默把全量 `all_hit` 升为本规格硬 Exit  
- 提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维  
- 回滚 #241 算法 A；LLM judge；claim_id 特判；闸读 T1 正文  
- 旧 `control` 对照成立；干扰项 c13/c14 通过线

## Paths（实现票可微调）

- `src/freshlatch/gates/meta_gate.py`（主）  
- `src/freshlatch/roles/lead.py` / `critic.py` / `gates/rule_gate.py`（共用函数接线，通常无需新出口）  
- `skills/reverify/SKILL.md` / `skills/freshness_audit/references/verdict-rubric.md` / persona（辅）  
- `tests/unit/test_meta_gate.py` 等（扩夹具）  
- `docs/research/` 短补丁（标记增补预登记）  
- `docs/spec/19-must-unknown-c10-缺口误stale.md`（本规格；实现后回填）  
- 报告：`reports/report-*.md` / `reports/trajectories/`

## 参考

- #241 · `docs/spec/16-must-unknown-c9-护栏.md`（上游 must_unknown，CLOSED）  
- ADR-0008 · `docs/research/c9元陈述句法闸设计评估.md` · #241 算法 A 补丁  
- §18 · `docs/spec/18-must-fresh-c5-反事实敏感性.md`（同次跑另一漏点，分票）  
- `data/eval/gold.json` · docket `c10` · 语料 `t0-talent-salary`  
- 证据：`reports/report-20261001-010433.md` · `reports/trajectories/run-20261001-010402.jsonl`

## Further Notes

- **规格状态**：implemented（2026-10-01）。  
- **实现票**：[GitHub #246](https://github.com/luxingjiang1993/FreshLatch/issues/246)（与 #245 并行）。  
- **与 #241 边界**：#241 = 元标记已命中后的数字回声逃逸；本规格 = **标记未命中**的缺口 paraphrase + 年月噪声 + 放弃追踪假锚。分票、分 Acceptance。  
- **面试一句**：T1 自己写「数据缺口声明 / 无新测量」——把「没更新」说成「已推翻」，就是本票要堵的洞。

## Post-mortem（实现后回填 · #246）

- **解码锁定**：`qwen-flash` · `temperature=0.0` · `seed=None` · 报告 UTC `2026-09-30T17:51:05` 附近。
- **确定性**：`test_meta_gate.py` / `test_c9_meta_gate_routing.py` 覆盖 c10 实录、日期噪声形、放弃追踪 72% 假锚；标记增补见 `docs/research/c10缺口误stale-标记增补补丁.md`；全量 pytest **705 passed**。
- **实现主缝**：`meta_gate` 标记增补 + T0/T1/年月噪声剥除；教义「过时未更新≠推翻」。
- **表现层（N=1 冒烟，不报方差）**：
  - 报告：`reports/report-20261001-015105.md`
  - 点名：`c10=unknown`；`c9=unknown`；`c3`/`c7`=`stale`；must_stale→fresh=0；同跑 **`all_hit=True`**（加分读数）
- **未声称**：不改 gold；不声称 Hard-Gold。
