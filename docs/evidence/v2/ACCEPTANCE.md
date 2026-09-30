# Phase V2 ACCEPTANCE

> **层身份：冒烟 / 采用层**（零 LLM CI 夹具可复跑）。不报采用率；不报方差；不作统计显著声明。本页不是 Hard-Gold，不是改生产默认臂授权，不是 webhook/插件平台已交付证明。  
> **判据：** ADR-0031 Exit 预锁；`docs/spec/14-PhaseV2-PublishHook.md`；评估 `docs/research/V2-发前钩子与主张台账设计评估.md` Q19。  
> **日期：** 2026-09-30  
> **对齐：** `origin/main` 合入 #227–#230 后 · Issue [#231](https://github.com/luxingjiang1993/FreshLatch/issues/231)

## 1. 冒烟声明（文首）

本页验收层 = **冒烟 · 采用层**。确定性预锁脚本证明「发前钩子被工作流点到」：Memo 闸正确、入站 check allow/deny 各 ≥1、台账可见本次 discard/renew。  
**禁止**把本页读成采用率报告、Hard-Gold、或生产插件/webhook 平台已交付。`curl`（或 TestClient）触发 check ≠ 开放 webhook 平台。Exit **不**硬绑包结论「可发」。

## 2. 交付物在仓

| 交付 | 路径 | 状态 |
|------|------|------|
| 规格 | `docs/spec/14-PhaseV2-PublishHook.md` | 在仓 |
| ADR-0031 | `docs/adr/0031-v2-发前钩子与主张台账.md` | 在仓 |
| 评估 | `docs/research/V2-发前钩子与主张台账设计评估.md` | 在仓 |
| 闸核心 | `src/freshlatch/publish_hook.py` | 在仓（#227） |
| 主张台账 | `src/freshlatch/claim_ledger.py` | 在仓（#228） |
| Memo 套闸 | `src/freshlatch/sheet.py` + CLI/UI | 在仓（#229） |
| 入站 check | `POST /api/publish-hook/check` | 在仓（#230） |
| 主缝 e2e | `tests/unit/test_v2_publish_hook_e2e.py` | 在仓（本票） |
| 顾问样例包 | `data/packs/v1-mck-soai/` | 复用，不另造垂直 |

## 3. 复跑命令（权威）

```bash
python -m compileall -q src
pytest tests/unit/test_v2_publish_hook_e2e.py \
  tests/unit/test_publish_hook.py \
  tests/unit/test_claim_ledger.py \
  tests/unit/test_publish_hook_memo.py \
  tests/unit/test_publish_hook_api.py -q
# 核对本文件 docs/evidence/v2/ACCEPTANCE.md
```

本机 2026-09-30 结果：**compile exit 0**；**52 passed**（e2e 2 + publish_hook/claim_ledger/memo/api 接线回归）。

### 3.1 curl 入站 check（手工等价；权威断言在 pytest TestClient）

ADR-0031 允许「curl **或**测试客户端」。CI/冒烟硬条由 `test_v2_prelock_main_seam_hard_bars` 用 TestClient 钉死 allow≥1 ∧ deny≥1。本机 UI 已起时可用：

```bash
# deny 例（勿发 Run；HTTP 403/409 + allow=false）
curl -sS -X POST http://127.0.0.1:8765/api/publish-hook/check \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"<DO_NOT_PUBLISH_RUN_ID>"}'

# allow 例（需补丁 Run + ack；HTTP 200 + allow=true；非硬绑可发）
curl -sS -X POST http://127.0.0.1:8765/api/publish-hook/check \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"<NEEDS_PATCH_RUN_ID>","ack_needs_patch":true}'
```

默认绑定本机 `127.0.0.1`；可选头 `X-FreshLatch-Hook-Token`（环境变量 `FRESHLATCH_HOOK_TOKEN`）。**不**宣称公网 webhook 平台。

## 4. 预锁脚本（禁 HARKing）

对照 ADR-0031 §5 / 评估 Q19。脚本步骤写死于 `tests/unit/test_v2_publish_hook_e2e.py` → `PRELOCK`；**禁止事后改「什么算点到」凑绿**。

| 步 | 动作 | 期望 |
|----|------|------|
| 0 | 样例包主张态：mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale | 包结论 **勿发**（可知） |
| 1 | 入站 check（无 ack）+ Memo 导出 | **deny**；Memo 零写 / 403 |
| 2 | 人审 **discard mck-1** + **renew mck-4**（锚 T1 `mck-soai-agents-2025-11#p3@T1`） | 台账可见两 claim_id；renew∉作废名单 |
| 3 | 包结论 | **需补丁**（剩 mck-3 unknown；**不**硬绑可发） |
| 4 | check + Memo 带 `ack_needs_patch=true` | **allow**；Memo 页眉含「需补丁」 |

HTTP 主缝：`test_v2_prelock_main_seam_hard_bars`。  
文首纪律：`test_v2_acceptance_doc_smoke_layer_and_hard_bars`。

## 5. 硬条勾（硬 Exit · 可核对）

| # | 硬条 | 判定 | 证据指针 |
|---|------|------|----------|
| 1 | **样例 Run 人审后 disposition 可知**（勿发 → 需补丁） | **pass** | `test_v2_prelock_main_seam_hard_bars` · `PRELOCK` |
| 2 | **Memo UI/CLI 闸动作正确**（勿发拒零写；需补丁+ack 放行并标「需补丁」） | **pass** | 同上；`/api/client-memo/export` + `export_client_memo_gated` |
| 3 | **入站 check deny ≥1**（TestClient ≡ curl） | **pass** | `POST /api/publish-hook/check` · `HOOK_DO_NOT_PUBLISH` |
| 4 | **入站 check allow ≥1**（需补丁+ack；disposition≠可发亦可） | **pass** | 同上 · `HOOK_OK` + `requires_needs_patch_banner` |
| 5 | **台账可见本次 discard/renew claim_id** | **pass** | `/api/claim-ledger` · mck-1 discard · mck-4 renew |
| 6 | **本 ACCEPTANCE 落盘且文首冒烟采用层** | **pass** | 本文件 |

**明确非硬条：** 包结论必须「可发」——本页硬勾路径停在「需补丁+ack」，**不**硬绑可发。

## 6. 加分勾（非硬 Exit）

| 项 | 判定 | 说明 |
|----|------|------|
| sheet / Evidence-bound 补丁包同闸 | **留位 / 另票** | ADR-0031：加分不挡 V2 Exit |
| 升包结论「可发」 | **非硬条** | 与 V1.5 纪律一致；本预锁不要求 |

## 7. 护栏（本票未破）

- [x] 零 LLM Exit 硬条（本页权威 pytest 无托管调用）
- [x] UI/CLI/HTTP 共用 `evaluate_publish_hook`（#227–#230 接线回归点名绿）
- [x] 主张台账零新写表；renew∉作废名单
- [x] 未宣称 webhook/插件平台已交付；curl ≠ 平台 Done
- [x] 未报采用率；未硬绑「可发」
- [x] 未改生产默认检索臂；未解冻 Studio

## 8. 可引用句（禁升格）

> V2（本地 ACCEPTANCE）：发前钩子冒烟可复跑；硬条（Memo 闸 · curl/TestClient allow+deny · 台账 discard/renew · 本文落盘）均 pass。档=冒烟·采用层。不硬绑「可发」。不是 Hard-Gold，不是采用率，不是 webhook/插件平台已交付。远程 issue CLOSED 不替代本文件。

## 9. 非本批 / 仍开

- Word/PPT/Notion 插件；开放公网 webhook 平台（→ Backlog C′）  
- 大图谱 / 全量采编 CMS  
- sheet/补丁包同闸（加分另票）  
- Exit 硬绑「可发」或报采用率  
- DoD 关门摘要：`docs/evidence/v2/V2-DoD-CLOSE.md`（[#232](https://github.com/luxingjiang1993/FreshLatch/issues/232)；本 ACCEPTANCE 不代关 DoD）  
- 本票 #231 等 Ronin `GROK-PROXY-APPROVED #231` 后再 close；父规格 #226 等 #232 代 Exit 后收口
