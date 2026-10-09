# patch_events 路线 C · 正式结果（RESULT-C）

> 口径：`docs/evidence/patch-events/PREREG-C.md`（已激活）。
> 三行 false-accept 与 k **只抄**同一次主比较（选取 R · `run_arms_c`）。
> 禁止把 GATE-C / 探针 / B 的 RESULT-B 数字抄进成立格。
> 旧 `RESULT.md` / `RESULT-B.md` 不得当冲甲主证据。

## 跑针

- **代码针**：9f28be6
- **激活**：PREREG-C 已激活（2026-10-09）；门闩依据=GATE-C-FIXTURE.md（fixture）；批准=本会话明文「批准激活 PREREG-C 并正式主跑一次。」
- **n** = 100（`load_formal_c_n100()` / `SPLIT-pe-v2.json` n100）
- **生成路径**：`docs/evidence/patch-events/formal-generations-c.jsonl`（n_lines=400；sha256=`9865adbb44b66fafcac97b0dcd121a6d45a955a0e2f976d075900bdf98bf8007`）
- **B2 after 条数**：100
- **解码**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`20261007`；API seed=`None`

## 主比较（同一次主比较 · R · run_arms_c）

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立 |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 0.032258064516129 | 0 | 0.07777777777777772 | 不成立 |
| T 对 B1 | false-accept rate | 0.032258064516129 | 0 | 0.07692307692307698 | 不成立 |
| T 对 B2 | false-accept rate | 0.032258064516129 | 0 | 0.07777777777777778 | 不成立 |

- **固定放行数 k** = 93

## 甲 / 乙 / 丙判定

- **分层**：结果丙
- 判定：结果丙。k=93。第一主比较（T-C）不成立或无定义（T-C 点估计=0.032258064516129 95%下界=0 → 不成立；T-B1 点估计=0.032258064516129 95%下界=0 → 不成立；T-B2 点估计=0.032258064516129 95%下界=0 → 不成立）。不得称甲；不得把主实验写成成功。

## B 负结果附录（动机 · 非本页成立格）

> 路线 B（`PREREG-B` / `RESULT-B`，#480）在选取 R、T/B1 同 after、生成对齐提示齐备并过仓外门闩后，正式主跑一次：k=42；T−C / T−B1 / T−B2 点估计均 >0，但 95% CI 下界均 ≤0 → **结果丙**。说明「可识别 + 过门」≠ 甲；核心教训是**效应偏小**。B 全套冻结为丙归档；禁止同页二次主跑、禁止降 CI/拿掉 B1 翻盘。路线 C 另开 `PREREG-C`，增量假设为强制抄句加大可辩护 T 相对差；不保证甲。

## 边界

- 不保证甲；不改甲定义；不复活路线 A；不改 B 归档。
- 不称全面 SOTA；乙也不许称优于 RARR·KPR。
- 同一预注册禁止第二次正式主跑充数。
