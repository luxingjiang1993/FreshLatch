# Hard-Gold 过线与改臂授权闸 · ACCEPTANCE

> **层身份：冒烟 / 决策闸。**  
> **状态（预锁文首）：流程已钉 · 复跑已跑 · 未过线 · 冻 bm25 · 未换臂。**  
> **不报方差；不作统计显著；不是渗透认证；主张金标 / control-c ≠ 本门。**  
> 权威：ADR-0033 · 评估见 `docs/research/Hard-Gold过线与改臂决议设计评估.md` · 决议 [#257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · 复跑 [#258](https://github.com/luxingjiang1993/FreshLatch/issues/258)

---

## 1. 与 I3 骨架分列

| 集 | 路径 | 本目录角色 |
|----|------|------------|
| I3 Hard-Gold 骨架 | `docs/evidence/i3/` · `docs/hard-gold.md` | 难金标可跑；断言仍 bm25；**≠** 换臂授权 |
| **本闸** | `docs/evidence/hard-gold-arm/` | 过线布尔 + 改臂授权流程 |

禁止把 I3 骨架 Exit 读成「已授权改 `PRODUCTION_RETRIEVAL_MODE`」。

---

## 2. 流程钉死（本决议 Exit）

| ID | 硬条 | 状态 |
|----|------|------|
| P1 | 评估文档落盘 | **pass** · `docs/research/Hard-Gold过线与改臂决议设计评估.md` |
| P2 | ADR-0033 Accepted | **pass** · `docs/adr/0033-hard-gold-过线与改臂授权闸.md` |
| P3 | CONTEXT 词条更新 | **pass** |
| P4 | roadmap「改臂另决议」指向本闸 | **pass** |
| P5 | dense+hard 复跑跟进票已开 | **pass** · [#258](https://github.com/luxingjiang1993/FreshLatch/issues/258) |

---

## 3. 过线复跑（#258 · 本文件勾选）

预锁布尔（ADR-0033）：dense 齐 ∧ hard 臂对比落盘 ∧ Hybrid 通过线在 hard 上成立。

| ID | 硬条 | 状态 |
|----|------|------|
| R1 | `data/dense/index.sqlite` 已建（gitignore；记录重建命令/日期） | **pass** · `reports/dense-rebuild.md` · `reports/dense-rebuild-258-note.md` · 2026-10-03 · text-embedding-v4 · chunks=84 |
| R2 | `python -m freshlatch.eval retrieve --hard`（或等价）产出臂对比报告 | **pass** · `reports/retrieve-hard-gold-bm25.md` · `reports/retrieve-hard-gold-arm-compare.md` |
| R3 | Hybrid 通过线在 hard 集上成立（公式见 `docs/eval-retrieve.md` §3） | **fail** · 臂对比通过线=fail（hybrid≥min 过，BM25 相对 A0 不过） |
| R4 | Rerank→生产门开/关单独入报告（不开不挡授权讨论 hybrid） | **pass（记关）** · `reports/retrieve-hard-gold-rerank-compare.md` · 判决=生产默认关 |
| R5 | 过线书面结论（过 / 不过 + 冻 bm25）写入本目录 | **pass** · [`RERUN-20261003.md`](./RERUN-20261003.md) · **不过线 · 冻 bm25** |

**当前总判：未过线 · 正式冻结 bm25。** 不得开改臂实现票。

---

## 4. 改臂实现（过线后 · Gate）

| ID | 硬条 | 状态 |
|----|------|------|
| A1 | 另开实现票；Trust=Gate；引用 R2/R3 报告路径 | **未开**（未过线） |
| A2 | 人终收后方可改 `PRODUCTION_RETRIEVAL_MODE` | **未做**（配置仍为 bm25） |

---

## 5. Out（偷渡否决）

- [ ] 本决议直接改生产默认臂  
- [ ] 无 dense 宣称过线  
- [ ] 用主张金标 / 假绿对照顶替 hard 增益门  
- [ ] 事后改增益门谓词  
- [ ] 报方差/通过率伪装 / 统计显著  
- [ ] 把 n=36 冒烟 retrieve 称作 Hard-Gold 已过  

（上列均须保持未勾 = 未偷渡；勾选表示违例。）

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-03 | 初版：#257 四件套；复跑节全未跑 |
| 2026-10-03 | #258 复跑：dense ok；Hybrid 门 fail；Rerank 关；不过线冻 bm25 |
