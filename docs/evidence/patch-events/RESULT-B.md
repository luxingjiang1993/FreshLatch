# patch_events 路线 B · 正式结果（RESULT-B）

> 口径：`docs/evidence/patch-events/PREREG-B.md`（已激活）。
> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。
> 禁止把 GATE-K-PROBE / gate-k-probe-generations / GATE-SEPARATION* 抄进成立格。
> 旧 `RESULT.md` / `PREREG.md` / n=30 链不得当冲甲主证据。

## 跑针

- **代码针**：3a50302
- **激活**：PREREG-B 已激活（2026-10-08）；门闩=docs/evidence/patch-events/GATE-K-PROBE.md；批准=本会话明文
- **n** = 100（`load_pe_v2_formal_n100()` / `SPLIT-pe-v2.json` n100）
- **生成路径**：`docs/evidence/patch-events/formal-generations-b.jsonl`（n_lines=400；sha256=`80e6fc85323b32b385c2af2cc964310cab9a895a3b97dee548d33a98d61b52d9`）
- **B2 after 条数**：100
- **解码**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`20261007`；API seed=`None`

## 主比较（同一次 compare_primary · R）

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立 |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 0.1190476190476191 | -0.05555555555555558 | 0.2894736842105263 | 不成立 |
| T 对 B1 | false-accept rate | 0.04761904761904762 | 0 | 0.1428571428571428 | 不成立 |
| T 对 B2 | false-accept rate | 0.1190476190476191 | -0.05718487394957981 | 0.2926829268292683 | 不成立 |

- **固定放行数 k** = 42

## 甲 / 乙 / 丙判定

- **分层**：结果丙
- 判定：结果丙。k=42。第一主比较（T-C）不成立或无定义（T-C 点估计=0.1190476190476191 95%下界=-0.05555555555555558 → 不成立；T-B1 点估计=0.04761904761904762 95%下界=0 → 不成立；T-B2 点估计=0.1190476190476191 95%下界=-0.05718487394957981 → 不成立）。不得称甲；不得把主实验写成成功。

## 边界

- 不保证甲；不改甲定义；不复活路线 A。
- 不称全面 SOTA；乙也不许称优于 RARR·KPR。
- 同一预注册禁止第二次正式主跑充数。
