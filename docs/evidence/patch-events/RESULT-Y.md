# patch_events 路线 Y · 正式结果（RESULT-Y）

> 口径：`docs/evidence/patch-events/PREREG-Y.md`（**未激活** · 冲乙整合升格 · 本壳不得冒充已跑）。  
> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。  
> **成立格只认 T−C**：点估计 >0.05 且 95% 下界 >0；T−B1 / T−B2 为报告-only。  
> 禁止把 GATE-Y-PROBE / GATE-Y-SENSITIVITY / SMOKE-Y-N30 / 夹具 / RESULT-B / RESULT-C / ALT 抄进成立格。  
> 禁止称甲；放弃甲防火墙见 `PREREG-Y`。仪器/门闩 Amendment 见协议页（ADR-0040/0041）。

## 跑针

- **代码针**：未跑  
- **激活**：未激活  
- **n**：400（激活后填写名单针）  
- **生成路径**：`docs/evidence/patch-events/formal-generations-y.jsonl`（未写）  
- **解码（预锁）**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`20261007`；API seed=`None`

## 主比较（同一次 compare_primary · R）

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立（Y 口径） |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | false-accept rate | 未填 | 未填 | 未填 | 报告-only（不参与成立） |
| T 对 B2 | false-accept rate | 未填 | 未填 | 未填 | 报告-only（不参与成立） |

- **固定放行数 k** = 未填

## 甲 / 乙 / 丙判定

- **分层**：未跑  
- 判定规则预锁：仅当 T−C 点>0.05 且下界>0 → **结果乙**；否则（含止损触发）→ **结果丙**。本页**不得**判甲。

## B / C 负结果附录（动机 · 非本页成立格）

> 路线 B（#480）：k=42；T−C≈0.1190476；ci95_low≈−0.05556 → 丙。  
> 路线 C：k=93；T−C≈0.032258；下界=0 → 丙；非 Y 主路径。

## 边界

- 不保证乙；不称甲；不复活路线 A；不改 B/C 归档。  
- 乙成立也不许称优于 RARR·KPR。  
- 同一预注册禁止第二次正式主跑充数。
