# Hard-Gold 规格（骨架 · 本波不改臂）

> **层身份：冒烟 / 面试加固（I3）。**  
> **本波 Hard-Gold = 骨架语料 + 增益门复跑；未授权改臂。**  
> **文首强制：** 骨架·不改臂。不报方差；不作统计显著；不是改生产默认臂授权。

## 1. 与冒烟分文件

| 集 | 路径 | 层 |
|----|------|-----|
| 冒烟 retrieve gold | `data/eval/retrieve_gold.json`（n=36） | smoke |
| **Hard-Gold** | `data/eval/retrieve_hard_gold.json` | hard · 骨架 |

禁止把 n=36 冒烟表称作 Hard-Gold 已过。

## 2. 预登记门槛（先于造数写死）

- **n ≥ 20**
- **traps / 对抗类 ≥ 30%**（`category ∈ {trap, adversarial}`）
- 增益门公式沿用 I0 / `docs/eval-retrieve.md` §3；**不事后改门凑换臂**
- Exit：**断言** `PRODUCTION_RETRIEVAL_MODE == "bm25"`

## 3. 复跑

```bash
PYTHONPATH=src python -m freshlatch.eval retrieve --hard
# 或
PYTHONPATH=src python -m freshlatch.eval retrieve --retrieve-gold data/eval/retrieve_hard_gold.json --hard
```

产出：`reports/retrieve-hard-gold-bm25.md`（及可选臂对比）。无 dense 索引时按 I0 纪律标需索引，**不得因此改臂**。

## 4. Out

- 本票不改 `PRODUCTION_RETRIEVAL_MODE`
- 不宣称 Hard-Gold 已授权换臂
- 不与主张金标混报

## 5. 改臂另决议（指针）

过线布尔与改臂**授权闸**见 **ADR-0033** · 评估 `docs/research/Hard-Gold过线与改臂决议设计评估.md` · 证据 `docs/evidence/hard-gold-arm/`（[#257](https://github.com/luxingjiang1993/FreshLatch/issues/257) · [#259](https://github.com/luxingjiang1993/FreshLatch/issues/259)）。  
hard 臂对比与 A0 **同库** = `corpus + traps`；dense 须覆盖同库。骨架 Exit ≠ 已换臂；过线后改配置仍须 **Gate** 实现票。
