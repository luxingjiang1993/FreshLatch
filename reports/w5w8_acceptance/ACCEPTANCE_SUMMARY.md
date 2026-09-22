# W5–W8 验收运行汇总（2026-09-22）

> **层级声明（2a）**：本文件是验收执行记录，不是「一期测量已闭合」证书。  
> 通过的统计/冒烟项只用已锁「仅表明」句引用；未过项如实登记。  
> **canonical 摘引入口**：下文「可引用索引」专节（决议:[决议:诚实状态落档形态与关图判据](https://github.com/luxingjiang1993/FreshLatch/issues/57)；评估见 `docs/research/诚实状态落档形态与关图判据设计评估.md`）。  
> 收口图:[地图:W5-W8 诚实可引用状态](https://github.com/luxingjiang1993/FreshLatch/issues/51)；父图:[地图:一期评测可引用边界](https://github.com/luxingjiang1993/FreshLatch/issues/41) 已关。

## 可引用索引

> 本专节是 W5–W8 本次跑数的**唯一摘引入口**。禁止把本文件当作「验收证书 / 一期闭合 / 全量通过」。禁单摘总表表头「过 / 倾向过 / 部分过」当结论。

### 已过项（仅表明 · 逐字 · #54）

1. **K3（统计层·已过）**
   > K3（temp=0.7，seed 11/22/33，每 seed n=5）仅表明 c2 stale ≥14/15 且 must_stale 判 fresh 合计为 0，不是一期评测闭合，也不是 must_fresh 已愈，也不改写判定层冒烟未愈。

2. **K1（demo·否定式达标）**
   > K1（demo）仅表明 `src/` 无 MCP server/listener 且 inspector 未连，不是 MCP 安全证书，也不是一期评测闭合。

3. **K6-2（机制层冒烟·倾向过，本批 n=3，temp=0）**
   > K6-2（n=3，temp=0）仅表明本批机制层冒烟：c5/c6 非 stale 5/6 且 must_stale 各 3/3 stale；三次均为 temp=0，不作为运行间噪声估计，不是统计测量，不是判定层已愈，也不改写 K6-4 未愈。

4. **K2（demo·部分过 + K2-1 备案）**
   > K2（demo）仅表明 Auditor 自动在场与单轮判定在金标跑中可见；`spawn_auditor` 不在 `LEAD_TOOLS_W3`，与 K2-1 字面冲突已按 ADR-0009/0010 与 spec 03 §3.6 备案，不是 K2-1 字面全过，也不是一期评测闭合。

5. **总判（必挂）**
   > 产品可运行（单测绿、UI 起、金标链跑通）。闸层可复现。不符合 W5–W8 全量验收通过。不得写成一期评测闭合。

### 未过 / 对照不成立（登记句 · 分条）

6. **K6-4（行为冒烟·未过 · #53 §7.5）**
   > K6-4 行为冒烟未愈；已按 §7.5 触发一次性 2 周修复窗口；机制层本批 intact；不是 must_fresh 已放弃，也不是判定层已愈 / 一期评测闭合。

7. **K4 / K5（demo·未实装 · #55）**
   > K4/K5：demo 层未实装，本图只登记；不启 §7.5 2 周钟；实装另开施工图。K7：子项可各自过/倾向过，收口包因 K4/K5（及他票未过）未闭合——索引陈述，非 K7-1…4 字面连坐。与 K6-4 分条，不合成一条「W5–W8 未过」。

8. **新假绿对照（仪器冒烟·对照不成立 · #56）**
   > 新假绿对照（qwen-flash，temp=0.0，seed=None，n=1，预登记仪器）仅表明 must_stale 假绿 0/4（c1/c2/c3/c7 全 unknown）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合。

### 明确禁止

- 「W5–W8 全量验收通过」「一期(评测/测量)闭合」「一期测量已闭合」
- 单摘表头「过 / 倾向过 / 部分过」；单独摘 K7「部分过」当通过
- 对未过项使用任何通过句模板；把「对照不成立」写成「假绿对照通过」或「仪器作废」
- 重开 K2-1 字面；改通过线 / `gold.json` / 已锁判据凑绿
- 旧文 09-21 改口条幅仍写「K3 未执行」者视为**历史快照**，更新读数只认本专节

### 关图检查表指针

关收口图前检查表见评估 `docs/research/诚实状态落档形态与关图判据设计评估.md` §拍板。K6-4 修窗另图；2 周钟（2026-09-22 起算）不因关收口图停。

## 执行环境

| 项 | 值 |
|---|---|
| 模型 | qwen-flash |
| git | `0e81824`（运行时 HEAD；另有未提交：`CONTROL_PROMPT` 预登记对齐 + 本目录产物） |
| 代码改动 | 仅 `CONTROL_PROMPT` 按 `docs/evidence/w4/false-green-control-prereg.md` 逐字更新（删禁外信息句） |
| 单测 | `pytest tests/` → **264 passed** |
| UI 冒烟 | `127.0.0.1:8765` 返回 SYNTHETIC +「开始复验」；无「开始调查」「生成答案」 |

## 总表

| 项 | 层级 | 结果 | 可引用句 / 说明 |
|---|---|---|---|
| K1 MCP 暴露面为零 | demo | **过** | `src/` 无 MCP server/listener；inspector 未连（否定式达标） |
| K2 Auditor 实装 | demo | **部分过** | 自动在场 + 单轮判定在金标跑中可见；`spawn_auditor` **不在** `LEAD_TOOLS_W3`（与 K2-1 字面冲突，以 ADR-0009/0010 自动触发为准，见 spec 03 §3.6 备案） |
| K3 统计层 | 统计 | **过** | 见下「仅表明」句 |
| K4 导出 Markdown | demo | **未过** | 仓库无命令/UI 导出入口与对账单测 |
| K5 token 记账 | demo | **未过** | `LLMClient` 未累计 prompt/completion token，报告无用量块 |
| K6-2 机制层 | 冒烟 | **倾向过**（本批 n=3） | c5/c6 非 stale 5/6；must_stale 各 3/3 stale；详见 k6_4 报告 |
| K6-4 fresh 恢复 | 冒烟 | **未过** | c5 fresh 0/3，c6 fresh 0/3，合计 0/6（线：各≥2/3 且合计≥5/6） |
| K7 收口 | demo | **部分过** | 单测绿 + UI 可起；导出/token 缺则整包未收口 |
| 新假绿对照 | 仪器冒烟 | **对照不成立** | must_stale 假绿 0/4（全 unknown）；不作废（无 unparseable / 无矛盾句回潮） |

**总判**：产品**可运行**（单测绿、UI 起、金标链跑通、闸层 must_stale 稳）。**不符合** W5–W8 全量验收通过（K4/K5 缺实装；K6-4 未愈；假绿仪器未成立）。**不得**写成一期评测闭合。

## K3（统计层）

- 设计：temp=0.7，seed 11/22/33，每 seed n=5（合计 15）
- 读数：c2 stale **15/15**；must_stale 判 fresh **0**
- 原料：`reports/w5w8_acceptance/k3/` + `k3_aggregate.json`

**唯一允许摘引（通过后模板）**：

> K3（temp=0.7，seed 11/22/33，每 seed n=5）仅表明 c2 stale ≥14/15 且 must_stale 判 fresh 合计为 0，不是一期评测闭合，也不是 must_fresh 已愈，也不改写判定层冒烟未愈。

c5/c6/c9 在 15 遍中的背离（K3-2③必记）：c5 = fresh 3 / unknown 12；c6 = fresh 2 / unknown 12 / stale 1；c9 = stale 3 / unknown 12。不升级、不进 K3 通过线。n=15 框定为单端点统计层读数，非显著性检验。

## K6-4（行为冒烟）

- 设计：n=3，temp=0
- 读数：c5/c6 均为 non-fresh（unknown/stale）；**未达**通过线
- 原料：`reports/w5w8_acceptance/k6_4/` + `k6_4_score.json`
- 处置：按 §7.5 一次性 2 周修复窗（2026-09-22 起算）；**不得**改 `gold.json` / 通过线 / 人格提示词凑绿。修窗另图，见可引用索引句 6。

可引用：见上文「可引用索引」句 6。不得使用通过句模板。

## 新假绿对照（仪器冒烟）

- prompt 已按预登记改码后首跑
- must_stale：c1/c2/c3/c7 全 `unknown` → **对照不成立**（不作废）
- 原料：`reports/w5w8_acceptance/report-20260922.json`（kind=control_run）
- 本阶段不追「成立」；不放宽 4/4；不新开预登记软化。决议:[决议:假绿对照不成立后的可引用边界](https://github.com/luxingjiang1993/FreshLatch/issues/56)；评估见 `docs/research/假绿对照不成立后可引用边界设计评估.md`

**唯一允许摘引**：

> 新假绿对照（qwen-flash，temp=0.0，seed=None，n=1，预登记仪器）仅表明 must_stale 假绿 0/4（c1/c2/c3/c7 全 unknown）→ 对照不成立且不作废；不是仪器已证明产品无假绿，也不是可放宽 4/4 alive，也不是一期评测闭合。

## 金标 N=1 冒烟（非判据）

- must_stale 4/4；must_fresh 0/4；must_unknown 3/4
- `reports/w5w8_acceptance/gold_n1/`

## 缺口（要过全量验收还需）

1. 实装 K4 复验单 Markdown 导出 + 对账单测  
2. 实装 K5 token 遥测写入报告  
3. K6-4 行为修复后按**同一通过线**复验（一次性窗口纪律，不改线）  
4. 假绿仪器：对照不成立时只记录；若要成立须保持预登记通过线，不得放宽  

## 产物索引

| 路径 | 内容 |
|---|---|
| `reports/w5w8_acceptance/gold_n1/` | N=1 冒烟 |
| `reports/w5w8_acceptance/k6_4/` | K6-4 n=3 |
| `reports/w5w8_acceptance/k3/` | K3 三 seed |
| `scripts/run_k3_acceptance.py` | K3 批跑 |
| `scripts/score_k6_4.py` | K6-4 计分 |
| `src/freshlatch/eval/control.py` | CONTROL_PROMPT 已对齐预登记 |
