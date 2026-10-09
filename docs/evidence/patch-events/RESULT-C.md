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

<!-- PE-C-POST:BEGIN -->

## 各臂（次要 · 不参与成立）

> 只抄同一次 `run_arms_c` + `compare_primary` 的臂块；不改主比较成立格。

| 臂 | 自然放行数 | 自然放行率 | 固定放行率 false-accept rate | 固定放行率误拒率 | 固定放行率错改率 | 固定放行率可复验率 | 延迟中位数 | 延迟 p95 | 成本 |
|---|---|---|---|---|---|---|---|---|---|
| C | 100 | 1 | 0.5161290322580645 | 0.0625 | 0.48 | 0 | 0 | 0 | 0 |
| T（copy-constrained） | 93 | 0.93 | 0.4838709677419355 | 0 | 0.45 | 1 | 0 | 0 | 0 |
| B1 | 100 | 1 | 0.5161290322580645 | 0.0625 | 0.48 | 0.9354838709677419 | 0 | 0 | 0 |
| B2 | 100 | 1 | 0.5161290322580645 | 0.0625 | 0.48 | 0.03225806451612903 | 0 | 0 | 0 |

- 固定放行数 k（只读，与主表一致）= `93`
- 放行数为 0 时误放率/可复验率写「无定义」，不得写成 0。

## 消融（只在 T · 不进主比较）

> 回放已保存 T rewrite；闸差由消融开关决定。随机流：`bootstrap_ablation` 同种子另起，不消耗主比较 `bootstrap` 前缀。

| 消融 | 预注册说法 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 |
|---|---|---|---|---|---|
| no_chunk_bind | 拿掉 chunk 绑定 | false-accept rate | -0.03149001536098311 | -0.1544958850901281 | 0.08888888888888891 |
| no_chunk_bind | 拿掉 chunk 绑定 | 误拒率 | 0.5208333333333334 | 0.3773584905660378 | 0.6595744680851063 |
| no_chunk_bind | 拿掉 chunk 绑定 | 错改率 | -0.26 | -0.36 | -0.16 |
| no_chunk_bind | 拿掉 chunk 绑定 | 可复验率 | -0.0714285714285714 | -0.1578947368421053 | 0 |
| no_auto_verify | 拿掉自动核验 | false-accept rate | 0 | 0 | 0 |
| no_auto_verify | 拿掉自动核验 | 误拒率 | 0 | 0 | 0 |
| no_auto_verify | 拿掉自动核验 | 错改率 | 0 | 0 | 0 |
| no_auto_verify | 拿掉自动核验 | 可复验率 | -1 | -1 | -1 |
| soft_warning | hard reject 换成 soft warning | false-accept rate | 0 | 0 | 0 |
| soft_warning | hard reject 换成 soft warning | 误拒率 | 0 | 0 | 0 |
| soft_warning | hard reject 换成 soft warning | 错改率 | 0 | 0 | 0 |
| soft_warning | hard reject 换成 soft warning | 可复验率 | -0.5806451612903225 | -0.6813186813186813 | -0.4831460674157303 |
| retrieval_bm25 | 检索臂换成 BM25 | false-accept rate | -0.07361455748552526 | -0.1937564372659176 | 0.05010622789235878 |
| retrieval_bm25 | 检索臂换成 BM25 | 误拒率 | 0.5208333333333334 | 0.3777777777777778 | 0.6666666666666666 |
| retrieval_bm25 | 检索臂换成 BM25 | 错改率 | -0.29 | -0.38 | -0.2 |
| retrieval_bm25 | 检索臂换成 BM25 | 可复验率 | 0 | 0 | 0 |
| hybrid+rerank | 另记一列，不进入主比较 | false-accept rate | 0.4102564102564102 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 误拒率 | 0.5208333333333334 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 错改率 | 0.16 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 可复验率 | 0 | 未填 | 未填 |

## 抽检（导出入口 · 非真人盲审）

> 身份：模型评委加单人抽检 · 角色：用户单人抽检。完成附加预注册前不得写真人盲审。
> 导出：`docs/evidence/patch-events/spotcheck-c-export.md` · `docs/evidence/patch-events/spotcheck-c-export.json`

- 抽检条数：20（n=100 配额：每层正确 2 / 坏 3）
- **抽检一致率**：未填（无用户标签）
- **用户对评委的 Cohen's κ**：未填（无用户标签）

<!-- PE-C-POST:END -->

## B 负结果附录（动机 · 非本页成立格）

> 路线 B（`PREREG-B` / `RESULT-B`，#480）在选取 R、T/B1 同 after、生成对齐提示齐备并过仓外门闩后，正式主跑一次：k=42；T−C / T−B1 / T−B2 点估计均 >0，但 95% CI 下界均 ≤0 → **结果丙**。说明「可识别 + 过门」≠ 甲；核心教训是**效应偏小**。B 全套冻结为丙归档；禁止同页二次主跑、禁止降 CI/拿掉 B1 翻盘。路线 C 另开 `PREREG-C`，增量假设为强制抄句加大可辩护 T 相对差；不保证甲。

## 边界

- 不保证甲；不改甲定义；不复活路线 A；不改 B 归档。
- 不称全面 SOTA；乙也不许称优于 RARR·KPR。
- 同一预注册禁止第二次正式主跑充数。
