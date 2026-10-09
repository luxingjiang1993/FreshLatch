# patch_events 路线 Y · 正式结果（RESULT-Y）

> 口径：`docs/evidence/patch-events/PREREG-Y.md`。
> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。
> **成立格只认 T−C**：点估计 >0.05 且 95% 下界 >0；T−B1 / T−B2 为报告-only。
> 禁止把 GATE-Y-PROBE / 夹具 / RESULT-B / RESULT-C / ALT 抄进成立格。
> 不得判甲；放弃甲防火墙见 `PREREG-Y`。

## 跑针

- **代码针**：86f38cd
- **激活**：PREREG-Y 已激活；门闩=GATE-Y-PROBE.md；人令=批准激活 PREREG-Y 并正式主跑一次。；d030 平台安检拒回记作废针
- **n** = 400（目标 400；名单见 PE-Y-03）
- **生成路径**：`docs/evidence/patch-events/formal-generations-y.jsonl`（n_lines=1599；sha256=`d09283d9a0e24a441b4fc7ac2b46cb9d92adcd5495c5fc324ca6be7b4fddca64`）
- **日志目录**：`data/exp/patch-events-y`
- **B2 after 条数**：399
- **解码**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`20261007`；API seed=`None`

## 主比较（同一次 compare_primary · R）

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立（Y 口径） |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 0.06310679611650488 | -0.009756097560975618 | 0.14 | 不成立 |
| T 对 B1 | false-accept rate | 0 | 0 | 0.02666844919786094 | 报告-only（不参与成立） |
| T 对 B2 | false-accept rate | 0.06310679611650488 | -0.009011056511056473 | 0.1377595003518648 | 报告-only（不参与成立） |

- **固定放行数 k** = 206

## 甲 / 乙 / 丙判定

- **分层**：结果丙
- 判定：结果丙。k=206。T−C 未过 Y 尺或无定义（点≤0.05 或下界≤0）（T-C 点估计=0.06310679611650488 95%下界=-0.009756097560975618 → 不成立；T-B1 点估计=0 95%下界=0 → 报告-only；T-B2 点估计=0.06310679611650488 95%下界=-0.009011056511056473 → 报告-only）。不得判甲；不得把主实验写成成功。

## B / C 负结果附录（动机 · 非本页成立格）

> 路线 B（#480）：k=42；T−C≈0.1190476；ci95_low≈−0.05556 → 丙。  
> 路线 C：k=93；T−C≈0.032258；下界=0 → 丙；非 Y 主路径。

## 边界

- 不保证乙；不得判甲；不复活路线 A；不改 B/C 归档。
- 乙成立也不许称优于 RARR·KPR。
- 同一预注册禁止第二次正式主跑充数。
