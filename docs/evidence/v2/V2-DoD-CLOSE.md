# Phase V2 DoD close · smoke / adoption-level

> **档：** 冒烟 / 采用层（零 LLM CI 夹具可复跑）。不报采用率；不报方差；不作统计显著声明。**不是** Hard-Gold；**不是** webhook/插件平台已交付；**不是**改生产默认臂授权。  
> **日期：** 2026-09-30  
> **Refs：** [#232](https://github.com/luxingjiang1993/FreshLatch/issues/232)（本票 · Exit 代收） / parent [#226](https://github.com/luxingjiang1993/FreshLatch/issues/226) / blocked-by [#231](https://github.com/luxingjiang1993/FreshLatch/issues/231) CLOSED via [PR #237](https://github.com/luxingjiang1993/FreshLatch/pull/237) · `GROK-PROXY-APPROVED #231`  
> **规格 / 决议：** `docs/spec/14-PhaseV2-PublishHook.md` · ADR-0031 · 评估 `docs/research/V2-发前钩子与主张台账设计评估.md`  
> **硬 Exit 权威：** `docs/evidence/v2/ACCEPTANCE.md`（文首冒烟·采用层声明；硬条六勾；升「可发」非硬条；`curl`/TestClient ≠ 开放 webhook 平台）

本页是 V2 Exit 的可引用关门摘要。Exit 由 Ronin 代批（等 `GROK-PROXY-APPROVED #232`）；实现本摘要的 PR 合 main 后可关本票。**不**自行 close 父规格 #226（建议 Ronin 在本票代批后收口）。

## Demo path

顾问样例包 `v1-mck-soai`：主张态 mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale → 包结论 **勿发**。入站 `POST /api/publish-hook/check` 与 Client Memo 导出均 **deny**（零写）。人审 discard mck-1 + renew mck-4 后包结论变为 **需补丁**；台账可见两 claim_id（renew∉作废名单）。带 `ack_needs_patch=true` 时 check **allow**、Memo 放行并标「需补丁」。**不**硬绑包结论「可发」。见 `docs/evidence/v2/ACCEPTANCE.md` 与 `tests/unit/test_v2_publish_hook_e2e.py`。

## DoD 硬 Exit（对齐 ACCEPTANCE §5）

- [x] **样例 Run 人审后 disposition 可知**（勿发 → 需补丁）  
  `docs/evidence/v2/ACCEPTANCE.md` §5 硬条 1；`test_v2_prelock_main_seam_hard_bars` / `PRELOCK`。主缝 e2e #231 [PR #237](https://github.com/luxingjiang1993/FreshLatch/pull/237)。
- [x] **Memo UI/CLI 闸动作正确**（勿发拒零写；需补丁+ack 放行并标「需补丁」）  
  ACCEPTANCE §5 硬条 2；#229 [PR #236](https://github.com/luxingjiang1993/FreshLatch/pull/236)。
- [x] **入站 check deny ≥1**（TestClient ≡ curl）  
  ACCEPTANCE §5 硬条 3；#230 [PR #235](https://github.com/luxingjiang1993/FreshLatch/pull/235)。
- [x] **入站 check allow ≥1**（需补丁+ack；disposition≠可发亦可）  
  ACCEPTANCE §5 硬条 4；同上。
- [x] **台账可见本次 discard/renew claim_id**  
  ACCEPTANCE §5 硬条 5；#228 [PR #234](https://github.com/luxingjiang1993/FreshLatch/pull/234)。
- [x] **ACCEPTANCE 落盘且文首冒烟采用层**  
  ACCEPTANCE §5 硬条 6；#231 [PR #237](https://github.com/luxingjiang1993/FreshLatch/pull/237)。闸核心 #227 [PR #233](https://github.com/luxingjiang1993/FreshLatch/pull/233)。

## 加分（非硬 Exit）

- [ ] **sheet / Evidence-bound 补丁包同闸** — ACCEPTANCE §6：**留位 / 另票**。不挡 V2 Exit。
- [x] **升包结论「可发」非硬条** — ACCEPTANCE §6 / ADR-0031：本预锁停在「需补丁+ack」；**不**硬绑可发。

## 证据引用

| 项 | 指针 |
|----|------|
| 硬 Exit / 冒烟采用层声明 | `docs/evidence/v2/ACCEPTANCE.md` |
| 主缝测试 | `tests/unit/test_v2_publish_hook_e2e.py` |
| 接线回归 | `tests/unit/test_publish_hook.py` · `test_claim_ledger.py` · `test_publish_hook_memo.py` · `test_publish_hook_api.py` |
| 实现 PR | [#233](https://github.com/luxingjiang1993/FreshLatch/pull/233) 闸核心 · [#234](https://github.com/luxingjiang1993/FreshLatch/pull/234) 台账 · [#236](https://github.com/luxingjiang1993/FreshLatch/pull/236) Memo 套闸 · [#235](https://github.com/luxingjiang1993/FreshLatch/pull/235) 入站 check · [#237](https://github.com/luxingjiang1993/FreshLatch/pull/237) e2e+ACCEPTANCE |
| 已关子票 | [#227](https://github.com/luxingjiang1993/FreshLatch/issues/227)–[#231](https://github.com/luxingjiang1993/FreshLatch/issues/231) closed（Ronin 代批）；本票 #232 = Exit |
| 父规格 | [#226](https://github.com/luxingjiang1993/FreshLatch/issues/226)（V2 Exit 代批后由 Ronin/编排收口；本票**不**代关） |

## Out of Scope（确认未偷渡）

- [x] **Word / Notion / 开放 webhook 插件平台**——未做；仅本机入站 check + 可选 token；`curl`/TestClient ≠ 平台已交付（→ Backlog C′）
- [x] **大图谱 / 全量采编 CMS**——未开（→ Backlog）
- [x] **新表双写作废**——主张台账零新写表；只读投影 discard∪renew
- [x] **Memo 商业裁决**——Memo 只套闸；无商业裁决逻辑（ADR-0015 纪律）
- [x] **整包再验挂钩子**——钩子只读包结论 + 机械新鲜度；**不**整包再验
- [x] **扩 HumanLatch / renew 改正文**——未扩 `VALID_ACTIONS`；renew 不改正文
- [x] **改生产默认检索臂**——仍 `bm25`
- [x] **解冻 Studio**——仍冻结
- [x] **把检索 embed 称作本阶段交付**——未宣称
- [x] **Exit 硬绑「可发」/ 报采用率**——未硬绑；未报采用率
- [x] **Hard-Gold / 统计显著 / 采用率报告**——本层不宣称、不升格

## 冒烟采用层边界（禁升格）

- **curl / TestClient 触发 check ≠ 开放 webhook / 插件平台已交付。**
- 本页 + ACCEPTANCE = 冒烟·采用层；远程 issue CLOSED 不替代 `docs/evidence/v2/ACCEPTANCE.md`。
- 不把零 LLM 夹具、单次 e2e、或本关门摘要说成 Hard-Gold、采用率、平台 Done、或改默认臂授权。

## 叙事对齐（README / 路线图）

- README：V2 发前钩子+主张台账冒烟在仓；档=冒烟·采用层；指针本文件与 ACCEPTANCE；curl ≠ 平台已交付；不硬绑可发。
- `docs/roadmap.md` Phase V2 Exit：**已齐（冒烟·采用层）**；Out 清单未偷渡；C′/图谱·CMS 仍 Backlog。
- `docs/contribution-boundary.md`：V2 冒烟落地句已补；不是 Hard-Gold / 不是平台已交付。

## 本机关单命令

环境：Linux，Python 3.12+。命令按 #232 Acceptance（文档核对为主）与 ACCEPTANCE §3 权威 pytest。本机 2026-09-30：

```text
$ test -f docs/evidence/v2/V2-DoD-CLOSE.md && echo present
present

$ python3 -m compileall -q src
exit:0

$ PYTHONPATH=src python3 -m pytest tests/unit/test_v2_publish_hook_e2e.py tests/unit/test_publish_hook.py tests/unit/test_claim_ledger.py tests/unit/test_publish_hook_memo.py tests/unit/test_publish_hook_api.py -q
52 passed
exit:0
```

（硬 Exit 权威在 ACCEPTANCE §5；本 DoD 以文档指针 + 冒烟复跑为关门核对。）
