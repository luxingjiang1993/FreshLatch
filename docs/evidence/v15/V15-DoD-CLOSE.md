# Phase V1.5 DoD close · smoke-level

> **档：** 冒烟 / 对客 demo 层（零 LLM CI）。不报方差；不作统计升格；**不是** Hard-Gold；**不是** C vs T 显著。  
> **日期：** 2026-09-29  
> **Refs：** [#203](https://github.com/luxingjiang1993/FreshLatch/issues/203) CLOSED（`GROK-PROXY-APPROVED #203`） / parent [#196](https://github.com/luxingjiang1993/FreshLatch/issues/196) / blocked-by [#202](https://github.com/luxingjiang1993/FreshLatch/issues/202) closed via [PR #210](https://github.com/luxingjiang1993/FreshLatch/pull/210)  
> **规格 / 决议：** `docs/spec/12-PhaseV1.5-EvidenceBound.md` · ADR-0029 · 评估 `docs/research/V1.5-Evidence-bound补丁设计评估.md`  
> **硬 Exit 权威：** `docs/evidence/v15/ACCEPTANCE.md`（文首冒烟声明；硬条四勾；升「可发」仅加分）

本页是 V1.5 Exit 的可引用关门摘要。Exit 已由 Ronin 代批（`GROK-PROXY-APPROVED #203`）；实现 PR [#211](https://github.com/luxingjiang1993/FreshLatch/pull/211)。

## Demo path

顾问样例包 `v1-mck-soai` 装入主张集（mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale → 包结论 **勿发**）。对人审范围 discard mck-1 与 mck-4 后包结论变为 **需补丁**。对 mck-3 走独立 `propose_patch` / `confirm_patch`（有证 `t1_ids` ⊆ 本 Run 已入库 T1）覆盖正文并写 `patch_events` **arm=T**（含 before/after）；confirm 成功后触发单条再验（`reverify=true`）；导出 JSON + 短 MD。无证确认被拒且正文/正式账本零写。见 `docs/evidence/v15/ACCEPTANCE.md` 与 `tests/unit/test_evidence_bound_e2e.py`。

## DoD 四项（对齐硬 Exit）

- [x] **无证拒确认**（空 `t1_ids` → 拒；正文与正式账本零写）  
  `docs/evidence/v15/ACCEPTANCE.md` §4 硬条 1；`test_v15_prelock_main_seam_hard_bars` / library 等价（`error_code=PATCH_EMPTY_T1`）。实现 PR [#206](https://github.com/luxingjiang1993/FreshLatch/pull/206)（#198）。
- [x] **有证 confirm**（`t1_ids ⊆` 本 Run 已入库 T1 → 正文覆盖 + `arm=T` + before/after）  
  ACCEPTANCE §4 硬条 2；`patch_events` T 行。#197 [PR #205](https://github.com/luxingjiang1993/FreshLatch/pull/205) 扩展字段；#198 [PR #206](https://github.com/luxingjiang1993/FreshLatch/pull/206)。
- [x] **单条再验触发**（`reverify=true` / `reverify_triggered`；非整包唯一路径）  
  ACCEPTANCE §4 硬条 3；#199 [PR #208](https://github.com/luxingjiang1993/FreshLatch/pull/208)。
- [x] **导出存在**（JSON + 短 MD 关键字段；与 Client Memo 分轨）  
  ACCEPTANCE §4 硬条 4；#201 [PR #207](https://github.com/luxingjiang1993/FreshLatch/pull/207)。复验单条带 UI #200 [PR #209](https://github.com/luxingjiang1993/FreshLatch/pull/209)。主缝 e2e + ACCEPTANCE #202 [PR #210](https://github.com/luxingjiang1993/FreshLatch/pull/210)。

## 加分（非硬 Exit）

- [x] **升包结论「可发」** — ACCEPTANCE §5：**加分 pass**（夹具再验路径可演示）。**不是**硬 Exit。ADR-0029 / V15-Q21：Exit **不**硬绑「可发」。真模型再验为手测/里程碑加分。

## 证据引用

| 项 | 指针 |
|----|------|
| 硬 Exit / 冒烟声明 | `docs/evidence/v15/ACCEPTANCE.md` |
| 主缝测试 | `tests/unit/test_evidence_bound_e2e.py` |
| V1 发前回归 | `tests/unit/test_prepublish_e2e.py`（不红） |
| 实现 PR | [#205](https://github.com/luxingjiang1993/FreshLatch/pull/205) before/after · [#206](https://github.com/luxingjiang1993/FreshLatch/pull/206) propose/confirm · [#208](https://github.com/luxingjiang1993/FreshLatch/pull/208) 再验 · [#209](https://github.com/luxingjiang1993/FreshLatch/pull/209) UI · [#207](https://github.com/luxingjiang1993/FreshLatch/pull/207) 导出 · [#210](https://github.com/luxingjiang1993/FreshLatch/pull/210) e2e+ACCEPTANCE |
| 已关子票 | [#197](https://github.com/luxingjiang1993/FreshLatch/issues/197)–[#203](https://github.com/luxingjiang1993/FreshLatch/issues/203) closed（Ronin 代批；#203 = Exit） |
| 父规格 | [#196](https://github.com/luxingjiang1993/FreshLatch/issues/196) 由编排器在 Exit 代批后收口 |

## Out of Scope（确认未偷渡）

- [x] **薄对话**（实装或 stub）——未进主链；ADR-0029 / roadmap Phase V1.5 Out
- [x] **发前 UX 上 C|T 开关**——产品路径恒 `arm=T`；无 UI 切换（#200 / ACCEPTANCE §6）
- [x] **扩 HumanLatch `VALID_ACTIONS`**——仍仅 `discard|renew`（`src/freshlatch/gates/human_latch.py`；`test_v15_valid_actions_and_default_arm_unchanged`）
- [x] **产品路径无证 C**——无证拒确认；C 仅脚本/后台
- [x] **Exit 硬绑「可发」**——升可发仅加分（ACCEPTANCE §5）
- [x] **编辑器秀 / span 级 diff 台 / 独立补丁台**——仅复验单增量条带
- [x] **#8 Policy-as-code 并行**——未开
- [x] **改生产默认检索臂**——仍 `bm25`
- [x] **Hard-Gold / 论文 n≥30 / C vs T 显著**——本层不宣称、不升格

## 不宣称 Hard-Gold 或统计结论

本证据层只是冒烟 / 对客 demo。不把零 LLM 夹具、单次 e2e、或本关门摘要说成 Hard-Gold 通过、C vs T 显著、改默认臂授权，或 Evidence-bound 已成论文级统计结论。远程 issue CLOSED 不替代 `docs/evidence/v15/ACCEPTANCE.md`。

## 叙事对齐（README / 路线图）

- README：表单 Evidence-bound 闭环在仓；**薄对话本期 Out**；档=冒烟；指针本文件与 ACCEPTANCE。
- `docs/roadmap.md` Phase V1.5 Exit：**已齐（冒烟级）**；Out 含薄对话未实装/未 stub；升「可发」非硬条。
- `docs/contribution-boundary.md`：V1.5 冒烟落地句已补；不是 Hard-Gold。

## 本机关单命令

环境：Linux，Python 3.12+。命令按 #203 Acceptance 原样。本机 2026-09-29：

```text
$ python -m compileall -q src
exit:0

$ rg -n "Evidence-bound|薄对话|V1.5" README.md docs/roadmap.md docs/evidence/v15/ACCEPTANCE.md
# README.md:33 V1.5 = Evidence-bound … 薄对话本期 Out
# README.md:99–100 V1.5 (smoke) / 薄对话 remains Out
# docs/roadmap.md:… Phase V1.5 Exit 已齐；Out 含薄对话
# docs/evidence/v15/ACCEPTANCE.md:… 文首冒烟；硬条；薄对话 Out
exit:0
```

（pytest 权威在 ACCEPTANCE §2：`test_evidence_bound_e2e` + `test_prepublish_e2e`；本 DoD 票以 compileall + rg 叙事核对为 Acceptance 命令。）
