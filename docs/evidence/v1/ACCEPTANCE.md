# Phase V1 ACCEPTANCE

> **档：** 演示/冒烟层（零 LLM CI）；不报方差；不作统计显著声明。  
> **判据：** roadmap Phase V1 Exit / DoD；`docs/spec/11-PhaseV1-PrePublish.md`；ADR-0027；**I1-Q7(c) / ADR-0028**（本地本文件为准；远程 issue CLOSED ≠ 自动 Exit）。  
> **日期：** 2026-09-29  
> **本机：** Windows 10 · Python 3.x · 对齐 `origin/main` @ `0850c2e` 后复跑  
> **关门摘要（Cloud 交包）：** `docs/evidence/v1/V1-DoD-CLOSE.md`（本 ACCEPTANCE 是 I1 硬挡要求的本地证明文件）

## 1. 交付物在仓

| 交付 | 路径 | 状态 |
|------|------|------|
| 规格 | `docs/spec/11-PhaseV1-PrePublish.md` | 在仓 |
| ADR-0027 | `docs/adr/0027-v1-顾问报告垂直包结论与薄URL.md` | 在仓 |
| 评估 | `docs/research/V1-发前闭环垂直与包结论设计评估.md` | 在仓 |
| 顾问样例包 | `data/packs/v1-mck-soai/` | 在仓 |
| disposition | `src/freshlatch/disposition.py` | 在仓 |
| 薄 URL / 两屏 / 主缝 | `t1_source.py` · `prepublish.py` · `ui/app.py` | 在仓 |
| patch_events | `src/freshlatch/patch_events.py` · `data/patch_events/` | 在仓 |
| 冒烟证据 | `docs/evidence/v1/prepublish-e2e.md` | 在仓 |
| DoD 关门摘要 | `docs/evidence/v1/V1-DoD-CLOSE.md` | 在仓 |
| README 垂直钉死 | 根 `README.md`「单一垂直 = 顾问报告」 | 在仓 |

## 2. I1-Q7 四项核对（本地复跑）

命令（PowerShell；权威入口 `python -m pytest`；亦可用裸 `pytest`，① 卫生后 collection 一致）：

```powershell
$env:PYTHONPATH = ""
python -m compileall -q src
python -m pytest tests/unit/test_prepublish_e2e.py tests/unit/test_disposition.py tests/unit/test_patch_events.py tests/unit/test_rule_gate.py tests/unit/test_hybrid_rrf.py -q
```

本机 2026-09-29 结果：**compile exit 0**；**46 passed**。

| # | 项 | 判定 | 证据指针 |
|---|----|------|----------|
| 1 | **disposition 映射抽检** | **pass** | `test_prereg_mapping_disposition_matches_adr0027`：`PREREG_MAPPING` = mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale → **勿发**；边界见 `test_adr0027_disposition_boundaries` |
| 2 | **patch_events 一行** | **pass** | 仓内样例：`data/patch_events/schema.example.jsonl`（1 行，字段齐全）；主缝人审写入：`test_main_seam_sample_pack_thin_url_to_patch_events` 断言 `before_disp=勿发`、`human_confirm=true`、`actor=human` |
| 3 | **默认臂仍 bm25** | **pass** | `PRODUCTION_RETRIEVAL_MODE == "bm25"`（`src/freshlatch/store/base.py`）；`test_production_retrieval_default_remains_bm25` + `test_hybrid_rrf` 断言 |
| 4 | **人审走通（发前主缝）** | **pass** | `test_main_seam_sample_pack_thin_url_to_patch_events`：夹具薄 URL → 勿发 → HumanLatch discard 收口 → 列表/详情 **可发** + patch_events；门闩回归另见 `tests/unit/test_latch.py` / `test_ui_latch.py` |

> 样例 JSONL 一行原文（schema 锚，非运行账）：  
> `{"claim_id":"c-mck-share-01","before_disp":"需补丁",...,"arm":"T","actor":"script"}`  
> 贯通测试在临时目录经 `record_human_review_events` 另写运行行（见 e2e）。

## 3. roadmap DoD 五项（冒烟级）

对照 `docs/evidence/v1/V1-DoD-CLOSE.md`；本机复跑未推翻：

- [x] 未归档不得定论（无 T1 / `ready=false` 不得复验定论）  
- [x] 报告级 disposition 可追责（可发 / 需补丁 / 勿发 + 预登记映射）  
- [x] 人审路径走通（discard → 可发；list/detail 同步）  
- [x] 单一垂直已写进文档/README（顾问报告 + `v1-mck-soai`）  
- [x] `patch_events` schema 已落并开始记账（样例行 + 人审追加路径）

## 4. 可引用句（禁升格）

> V1（本地 ACCEPTANCE）：发前主缝冒烟可复跑；disposition 映射抽检、patch_events 一行、默认臂 bm25、人审主缝走通均 pass。档=冒烟。不是 Hard-Gold，不是改默认臂授权，不是统计显著，不是 V1.5 Evidence-bound 已交付。远程 CLOSED 不替代本文件。

## 5. 非本批 / 仍开

- 改 `PRODUCTION_RETRIEVAL_MODE` / Hard-Gold  
- 薄对话 / Evidence-bound UX（V1.5）  
- 开放爬虫 / 多域名白名单  
- GitHub [#175](https://github.com/luxingjiang1993/FreshLatch/issues/175) **人终收**（若仍开：本文件不代关 issue；本地 Exit 证明以本 ACCEPTANCE 为准解锁 I1 落样本）
