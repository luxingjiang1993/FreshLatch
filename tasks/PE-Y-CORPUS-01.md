# PE-Y-CORPUS-01 · 扩 pe_v2 公开语料至可满 n=400+共形预留

> GitHub Issue: [#500](https://github.com/luxingjiang1993/FreshLatch/issues/500)

## Parent

ADR-0038 · 缺额评估 `docs/research/patch_events-路线Y正式n与语料缺额设计评估.md` · 规格卷 27（Y7）· 语料先例 [#371](https://github.com/luxingjiang1993/FreshLatch/issues/371) · 名单针 PE-Y-03 / PR [#497](https://github.com/luxingjiang1993/FreshLatch/pull/497)

## Destination

在 `PREREG-Y` 样本框内续扩 `data/pe_v2_docket.json` 与 `data/corpus/pe_v2/`（公开法规同源 · #371 级 provenance），使库存足以支撑正式 n=400（四层各 100，层内 50/50）及共形每层 5 的 leftover 规划。**不**改 `PREREG-Y` 配额表；**不**激活；**不**开 PE-Y-05；**不**发正式模型；**不**重写 `SPLIT-pe-v2.json` 已冻结的 pilot/n30/n100 成员。

## 缺额事实（开票时只读）

- 现网 `pe_v2` claims=**178**（数值 45 / 日期 45 / 条款替换 45 / 删除 43）
- `SPLIT-pe-v2-route-y.json`：`status=不可激活`；各层 `gap_vs_ceiling` ≈ 59–60
- 粗目标（实现核实，Acceptance 以构造满额为准）：每层库存 **≥142**（约 `(pilot + 100 + 共形5) × 1.3`）；总池 **≥约 560**；跳过缓冲不够则如实记，**不得**为共形挖主配额

## Acceptance criteria

- [ ] Given 扩容后的 pe_v2 docket+corpus，When 跑 `construct_samples(data/pe_v2_docket.json, data/corpus/pe_v2)`（或本仓等价构造入口），Then 四层在「可供 route-y 正式 100/层」意义上**无语料不足**（各层可达 100 槽，层内正确/坏可按余数规则 50/50 配齐）；缺额不得靠改小 `PREREG-Y` 表解决
- [ ] 每层未使用主张在满 n=400 规划后仍力争 leftover ≥5（共形预留）；若不够 → 写「未做」，**不得**从 400 主配额挖条
- [ ] 每条主张可在对应 T0 全文逐字定位；`PROVENANCE.json` 含 URL、抓取时间、许可、sha256；文件 sha256 与 LF 内容一致
- [ ] `scripts/build_pe_v2_corpus.py`（或等价）目标从 45/层抬到足以满足上两条；删除层须显式目标条数（不得仍停留在「能捡多少算多少」而无验收数字）
- [ ] `docs/evidence/patch-events/DECISION-LOG.md` 增「跑数据前偏离 · pe_v2 再扩充（路线 Y / ADR-0038）」指针行（不改比较/成立尺/配额数字）
- [ ] 未设置三个评委密钥时：`pytest` 点名本票相关单测 + `python -m compileall -q src` 退出码 0
- [ ] **边界**：未改 `PREREG-Y` 配额表；文首仍未激活；未开/未派 PE-Y-05；未发正式模型；未碰第二领域 / KPR / 医疗 / thesis-1 合成主路径；未改写 `SPLIT-pe-v2.json` 的 pilot/n30/n100 成员列表

## Agent Guards

- **ID**: PE-Y-CORPUS-01
- **Title**: `feat(eval): 扩 pe_v2 公开语料至可满路线 Y n=400`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `data/pe_v2_docket.json`
  - `data/corpus/pe_v2/`（含 `t0/` · `t1/` · `PROVENANCE.json`）
  - `scripts/build_pe_v2_corpus.py`
  - `docs/evidence/patch-events/DECISION-LOG.md`（仅偏离指针）
  - `tests/unit/test_pe_v2_corpus.py`（扩或新建 route-y 库存断言）
- **Provenance**:
  - Kind: adapt
  - Source: [#371](https://github.com/luxingjiang1993/FreshLatch/issues/371) · `scripts/build_pe_v2_corpus.py` · 快照 `senry5433/china-effective-laws-regulations`
  - Pin: 数据集卡片快照日 `2026-08-26`；实现时记录所用 parquet/commit 针到 Evidence
  - What changed: 抬高每层抽取目标并续写 docket/corpus；同公开法规样本框
  - Why not copy as-is: 现 178 条不够 PREREG-Y n=400；#371 只按 B 档 n=100 填满
  - License note: 汇编 CC0-1.0；正文不适用著作权法第五条；网站条款未逐页核验（同 #371）
- **Tests**: updated
- **Do-not-touch**: `PREREG-Y.md` 配额表数字与激活状态；`PREREG-B`/`PREREG-C`/`RESULT-B`/`RESULT-C`；`SPLIT-pe-v2.json` 已发布 pilot/n30/n100 成员；构造算子语义；评委调用；`requirements.txt` / `pyproject.toml` / CI；PE-Y-05；正式发模型
- **Rollback**: 回退 docket/corpus/PROVENANCE 至扩容前 tip；DECISION-LOG 指针行可保留并注明回滚

### Provenance status

- result: pass
- notes: Kind=adapt。Blast=none。Trust=Watch。非 auth/db/pay。样本框锁定 pe_v2 公开法规。

### Evidence *(after Matt `/implement`)*

- typecheck:
- tests:
- paths:

## Blocked by

- None（可与 #494–#497 合入并行；但 route-y 重针见 PE-Y-CORPUS-02）

## Handoff

`enrich done | PE-Y-CORPUS-01 | ready | next: before-implement PE-Y-CORPUS-01`
