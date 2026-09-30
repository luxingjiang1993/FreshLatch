# §16 must_unknown 护栏回归（c9 误 stale）· 规格

> 来源：整仓 L3 表现层短板（`REPORT-20260930-REMAINING`）→ #239 关单后新形状 → 本规格（先于开实现票）  
> 词表：`CONTEXT.md`  
> 上游权威：ADR-0008（不变量 6 / 元陈述闸）、ADR-0011/0012（维度自标与受理预检）、`skills/freshness_audit/references/verdict-rubric.md`、#239（换维/反默认 `cost_model`，CLOSED）  
> 证据锚：`reports/report-20260930-214533.md`（混淆矩阵 `c9→stale`；11/12；`all_hit=False`）；轨迹 `reports/trajectories/run-20260930-214446.jsonl`  
> **测试主缝（预锁，开票前可再确认）：**  
> 1. **元陈述不得当推翻** — `is_meta_only_disproof` / `mark_stale` 工具层提前反馈 / `rule_gate` 不变量 6：含「未复测/不再列入跟踪/未保留…」且无独立实质反证时，不得落档 `stale`（须打回并路由 `unknown`）  
> 2. **#239 回归护栏** — 同 decoding 下 **c3、c7 仍为 stale**；违例级 `must_stale→fresh` 仍为 **0**  
> 子缝（仅主缝测不到时）：教义/persona「停追踪≠推翻」可断言片段；I1 金样与 #239 post-fix **不回退**。**优先只暴露两条主缝。**

---

## Problem Statement

#239 已按 Acceptance 修好 must_stale 漏拦（c3/c7 + I1 mck-1）：换维重试 + 反默认 `cost_model`。同次修后 N=1 gold 跑（`report-20260930-214533`）出现**新**漏判：

| 样本 | 期望 | 机判 | 说明 |
|------|------|------|------|
| gold `c9` | must_unknown | stale | T1 仅「本轮未复测…该指标不再列入跟踪项」；Lead 以元陈述当推翻并 `mark_stale(dimension=market_structure)` 一次受理 |
| 全量 | 12/12 | 11/12 | `all_hit=False`；must_stale 4/4、must_fresh 4/4、must_unknown 3/4 |

这**不在** #239 Acceptance 内，但是换维/反默认后的新风险：模型更敢 `mark_stale`，且 reason 形状进化为 **主张数字回声**，击穿 ADR-0008 既有启发式。

### 根因（机制级，已复现）

ADR-0008 / `meta_gate.py` 算法：含元标记的子句剥除后，若仍有「含阿拉伯数字且非元」的实质子句 ⇒ **放行**。

修后 c9 实录 reason 在剥除「未复测 / 未保留 / 不再列入跟踪」子句后，残留形如：

> 此句直接推翻了主张 c9 中关于『…渗透率不低于 **70%**』的前提…

`70%` 来自**主张原文回声**，不是 T1 上的独立数值反证。对修后轨迹 reason 直调 `is_meta_only_disproof` 得 `False`（会话内已复现）；历史 `C9_RUN2_REASON` 仍打回。故：**不是闸消失，是新逃逸形状**——与 W4 背离一同源问题（ADR-0008 背景），换皮再犯。

人格层（`LEAD_PERSONA` / reverify「未复测→mark_gap+unknown」）再次被端点漂移击穿；机械闸本应兜底，却被数字回声骗过。

## Solution

交付一次**工程修复（非判据修订）**：堵住「元陈述 + 主张数字回声」逃逸，使 c9 在预锁 decoding 下回 `unknown`，同时**不**回退 #239 的 c3/c7/mck-1。

默认主路径（实现顺序可拆票，但 Exit 绑死）：

1. **闸层（主缝 1）**：在 ADR-0008 包络内收紧 `is_meta_only_disproof`——对「仅复述主张内已有数字、无独立实质锚」的残留子句**不得**当作实质放行。算法变更须**先于实现**写入本规格 Testing Decisions +（若触 ADR-0008「事后改算法」条款）补一页评估补丁或新开决议票重签边界；**禁止**静默改启发式凑绿。  
2. **教义/persona（辅）**：重申 rubric 铁律——「未复测/停追踪/不再列入跟踪 = 证据缺口 → `mark_gap` + unknown」；禁止把「无法验证」写成「推翻前提」。  
3. **确定性单测**：注入修后 c9 实录 reason（及最小「主张数字回声」合成形）⇒ 必打回；c3/c7 合法数值锚形状仍放行。  
4. **活模验收（表现层，N=1）**：点名 c9=unknown；回归 c3/c7=stale。

**禁止**：改 `data/eval/gold.json`；把 c9 期望改成 stale；提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维；回滚 #239 换维教义来「换」c9。

## User Stories

1. As an 验收者, I want 修后 N=1 gold 下 c9 机判为 unknown, so that must_unknown 护栏从「主张数字回声」逃逸中恢复。  
2. As an 验收者, I want 同次跑 c3 与 c7 仍为 stale, so that #239 成果不回退。  
3. As an 验收者, I want 违例级 must_stale→fresh 仍为 0, so that 不对称安全不破。  
4. As an 验收者, I want N=1 只报命中不报方差, so that 不假装统计测量。  
5. As an 验收者, I want 止损预先锁定且禁止改 gold 凑绿, so that 不 HARKing。  
6. As a 闸守护者, I want 修后 c9 实录 reason 注入 `is_meta_only_disproof` 为 True, so that 逃逸形状机制级闭合。  
7. As a 闸守护者, I want 最小「元标记 + 主张数字回声」合成形同样打回, so that 不依赖整段长 reason。  
8. As a 闸守护者, I want 历史 C9_RUN2 / C9_REPRO2 形状仍打回, so that ADR-0008 既有回归不丢。  
9. As a 闸守护者, I want c3/c7 合法数值锚形状仍放行, so that 真反证不被误伤。  
10. As a 闸守护者, I want 「元陈述 + 独立实质数值锚」共存形仍放行, so that 既有 `test_meta_clause_with_substantive_numeric_clause_passes` 不红。  
11. As a Lead 调用方, I want `mark_stale` 对纯元/回声形在工具层提前打回并指向 mark_gap+unknown, so that 环内可恢复。  
12. As a Critic 调用方, I want 同判定函数打回（出口按白名单适配）, so that 单一真相。  
13. As a runner, I want 闸 `META_ONLY_DISPROOF` 仍经既有 stale→unknown 路由, so that 落档口径不变。  
14. As a 教义维护者, I want reverify/rubric/persona 明确「停追踪≠推翻」, so that 提示词与闸同向。  
15. As a 产品负责人, I want 不改 gold.json / must_unknown 期望档, so that 尺子不变。  
16. As a 产品负责人, I want 本票默认不提高 DIMENSION_RECOVERY_QUOTA, so that ADR-0012 后果条款不被偷渡。  
17. As a 产品负责人, I want 不把「全量 all_hit」静默升为本票硬 Exit, so that 范围不膨胀（可选加分须明示）。  
18. As a 回归守护者, I want I1 mck-1 post-fix 不被本票回退, so that #239 答辩金样仍成立。  
19. As an AFK agent, I want Paths 与 Acceptance 可执行, so that 可按序实现。  
20. As an 面试讲解者, I want 能讲清「#239 修漏拦 → 更敢 stale → 数字回声骗过旧启发式 → 闸收紧而非改金标」, so that 中级可过追问。  
21. As a 复现工程师, I want decoding 与报告路径入档, so that 跨会话只求近似。  
22. As a 架构守护者, I want 判定引擎仍单一真相在 `meta_gate.py`, so that Lead/Critic/rule_gate 不复制三份逻辑。  
23. As a 架构守护者, I want 若改算法则先锁边界再写测, so that 不违反 ADR-0008 预登记纪律。  
24. As a 文档维护者, I want evidence/报告追加 post-fix 段而非改历史失败叙事, so that 诚实。

## Implementation Decisions

### 主缝与模块

- **主缝 1（元陈述不得当推翻）**：行为真相在 `src/freshlatch/gates/meta_gate.py` 的 `is_meta_only_disproof`；`roles/lead.py` / `roles/critic.py` 工具层与 `gates/rule_gate.py` 不变量 6 **共用**该函数。修逃逸 = 收紧「什么叫实质数值锚」，不是新建第二套闸。  
- **主缝 2（#239 回归）**：活模点名断言 c3/c7；确定性侧保留既有合法 stale 形状测。  
- **教义辅路径**：`skills/reverify/SKILL.md`、`skills/freshness_audit/references/verdict-rubric.md`、Lead/Critic persona 中与「未复测」相关的纠正表——只加可断言片段，不改工具签名。  
- **非目标模块**：retrieve、HumanLatch、I2 安全闸、gold.json、DIMENSION_RECOVERY_QUOTA。

### 算法收紧方向（预锁意图；实现前可微调措辞，不可改 Exit）

在**不破坏**下列既有放行/打回契约的前提下，增加对「主张数字回声」的识别，候选（实现票二选一或组合，须在 PR 写明）：

| 候选 | 原理 | 风险 |
|------|------|------|
| A. 主张陈述数字集合作「回声黑名单」 | 残留子句中的数字若**全部**出现在该 claim `statement` 中，则不算实质锚 | 须把 `statement` 传入判定（或在工具层包装）；闸签名扩展要保持 rule_gate 可测 |
| B. 残留子句须含「非主张回声」的独立数值/实体变化谓词 | 更语义，但仍须确定性启发式 | 易误伤；边界要预登记 |
| C. 仅扩标记词表（「停止追踪」「无法验证」等） | 便宜 | **不够**：本逃逸已含旧标记，靠的是数字回声放行 |

**推荐默认：A（+ 必要的工具层传入 statement）**；C 可作辅，不可单独当 Exit。B 若采用须另开评估补丁写清误伤表。

> Anthropic 清单对齐：改闸算法 = 止损/验收相关机制变更，满足「事后改会毁实验意义」→ 须评估补丁或短 ADR 注记；**仍不改 gold**（工程修复，非判据修订，同 ADR-0008 §4）。

### API / 契约（逻辑）

- `is_meta_only_disproof(reason: str, *, claim_statement: str | None = None) -> bool`（或等价：保留单参并对新逃逸用可选第二参；**缺省 `None` 时行为不得弱于今日对历史形状的打回**）。  
- `mark_stale` / `rule_gate`：调用处传入主张 statement（已有 Claim 对象处直接取）。  
- 打回码仍为 `META_ONLY_DISPROOF`；消息可微更，但须指向 `mark_gap` + unknown。  
- **禁止**：LLM judge；闸读证据正文做语义比对（ADR-0008 已否）；为 c9 特判 claim_id。

### 历史形状对照

| 形状 | 今日闸 | 本规格目标 |
|------|--------|------------|
| `C9_RUN2_REASON` / `C9_REPRO2_REASON` | 打回 | 打回（回归） |
| 修后轨迹 reason（含「不低于 70%」回声） | **放行（逃逸）** | **打回** |
| `C3_LEGIT` / `C7_LEGIT` | 放行 | 放行（回归） |
| 元 + 独立「79 美元」实质锚 | 放行 | 放行 |

## Testing Decisions

- **好测试**：断言外部行为（打回/放行；落档 status），不锁模型品牌文案像素。  
- **确定性（硬门）**：  
  - 新测：修后 c9 实录 reason + 最小回声合成形 ⇒ `is_meta_only_disproof` True；经 runner/工具路径不得落 `stale`。  
  - 旧测全绿：`tests/unit/test_meta_gate.py`、`test_c9_meta_gate_routing.py`、相关 rule_gate。  
  - c3/c7 合法形仍 False（放行）。  
- **表现层（冒烟，N=1）**：  
  - decoding：`qwen-flash` · `temperature=0.0` · `seed=None` · 日期入档  
  - 点名：`python -m freshlatch.eval run --gold data/eval/gold.json --runs 1`（或仓内等价）→ **c9=unknown**；**c3 与 c7=stale**；must_stale→fresh=0  
  - 不报方差；不声称 Hard-Gold  
- **可选加分（非默认 Exit）**：同跑 12/12 / `all_hit=True`——若要声称须在实现票 Acceptance 显式勾选，否则只记读数。  
- **止损**：B 项 N=1 未过 → 如实登记，不改 gold，禁止第二次改判据；若收紧闸导致 c3/c7 误伤 → 本票失败，回退算法边界并重签，不得用「平均 11/12」糊弄。

## Out of Scope

- 修改 `data/eval/gold.json` / 将 c9 改出 must_unknown  
- 提高 `DIMENSION_RECOVERY_QUOTA`；披露登记维度值  
- 回滚 #239 换维/反默认教义作为「修 c9」手段  
- 把全量 `all_hit` 静默升为本规格硬 Exit  
- N≥3 方差评测票（另开）  
- Hard-Gold / 统计闭合 / 新 Phase 产品面  
- LLM-as-judge 元陈述分类；闸读 T1 正文语义比对  
- 为单个 claim_id 写死特判

## Further Notes

- **与 #239 边界**：#239 Exit = c3/c7/mck-1；本规格 = must_unknown 护栏回归（c9）+ #239 不回退。分票、分 Acceptance。  
- **与 ADR-0008**：同题再犯（提示词被击穿 + 需机械闸）；本次是**逃逸形状增量**，不是推翻「确定性句法启发式」选型。  
- **语料事实**：c9 主张「目标市场 WhatsApp Business 渗透率不低于 70%」；T1 `t0-messaging-survey#p2` 仅元陈述（停追踪），金标正确档 = must_unknown（§2.6 缺口演练）。  
- **下一跳**：`/enrich-tickets` → `/before-implement #241` → 新鲜会话 `/implement`。  
- **规格状态**：implemented（2026-09-30；算法 A 已实装；活模 N=1 见 post-fix）。  
- **实现票**：[GitHub #241](https://github.com/luxingjiang1993/FreshLatch/issues/241)。  
- **上游**：[GitHub #239](https://github.com/luxingjiang1993/FreshLatch/issues/239)（CLOSED；换维/反默认，本票不回退）。  
- **算法边界补丁**：`docs/research/c9元陈述句法闸-算法A主张数字回声补丁.md`（相对 ADR-0008 增量明示）。

## Post-fix（实现后回填）

- **解码锁定**：`qwen-flash` · `temperature=0.0` · `seed=None` · `recorded_at=2026-09-30T15:23:35+00:00`。  
- **确定性**：`tests/unit/test_meta_gate.py` / `test_c9_meta_gate_routing.py` / `test_c9_meta_gate_tool_feedback.py` 覆盖修后 c9 实录 reason + 最小回声合成形打回；历史形/合法锚回归绿；`compileall` + 全量 pytest 绿。  
- **表现层（N=1 冒烟，不报方差）**：  
  - 报告：`reports/report-20260930-232556.md`  
  - 原始：`reports/report-20260930-232556.json`  
  - 轨迹：c9=`reports/trajectories/run-20260930-232512.jsonl`；c3=`run-20260930-232355.jsonl`；c7=`run-20260930-232453.jsonl`  
  - 点名：`c9=unknown`、`c3=stale`、`c7=stale`；must_stale→fresh=0；must_unknown 4/4  
  - 读数：`all_hit=False`（must_fresh 漏 `c6→stale`，非本票硬 Exit）  
- **未声称**：不改 gold；不声称 Hard-Gold；全量 `all_hit` 非本票硬 Exit。
