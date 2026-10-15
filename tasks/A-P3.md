# TASK · A-P3 主 SLI + burn-rate page

## Ticket
- **ID**: A-P3
- **Title**: `feat(ops): product SLI + burn-rate page rule + canary_event hook`
- **Paths**: `src/freshlatch/` (sli/alert module), `tests/`, `docs/ops/`
- **Trust**: Gate
- **Blast**: api | none

## Agent Guards
- **Acceptance**:
  1. Land e2e P95 and abstain/fallback rate from a real trajectory/canary window API (not fixture-dir alone); pytest with synthetic window ok.
  2. Burn-rate / multiwindow breach rule callable; pytest injects breach → page action recorded (webhook/email sender mockable).
  3. Docs: who is on-call (named role), page vs ticket, non-24x7; notes consume `canary_event` from A-P1.
  4. Protocol-only page without callable page path = NOT Done (test/docs assert).
- **Provenance**: adapt `product_sli.py` / `trajectory_sli.py` if useful; hook A-P1 canary events.
  - Kind: adapt
  - Source: `src/freshlatch/eval/trajectory_sli.py#aggregate_trajectory_runs`；`src/freshlatch/eval/product_sli.py#aggregate_product_runs`；`src/freshlatch/canary.py#sample_breached`
  - What changed: 目录聚合改为读完后调用内存入口。新模块 `src/freshlatch/sli/alert.py` 用 `SliWindow` 落 e2e P95 与 abstain/fallback，并用 multiwindow burn-rate 调用可注入的 page sender。消费 A-P1 `canary_event`。
  - Why not copy as-is: 原入口只读夹具目录。本票要求窗口 API，且 page 必须可调用，协议页 alone 不算 Done。
- **Do-not-touch**: floors / gold / x1 / PRODUCTION_RETRIEVAL_MODE / SESOI / C-04 / RESULT-Y
- **Tests**: added（`tests/unit/test_a_p3_sli_page.py`）
- **Rollback**: disable page sink / set env off（`FRESHLATCH_PAGE_SINK=off`）

### Provenance status
- result: pass
- notes: 未改 canary 停发闩，未改检索默认臂，未发明 SESOI。objective 由调用方传入。

### Evidence
- typecheck: `python -m compileall -q src/freshlatch/sli src/freshlatch/eval/trajectory_sli.py src/freshlatch/eval/product_sli.py` 通过
- tests: `python -m pytest tests/unit/test_a_p3_sli_page.py tests/unit/test_l4_ev_03_trajectory_sli.py tests/unit/test_l4_c_02_product_sli.py tests/unit/test_canary_halt.py -q` → 51 passed；无付费 API
- paths: `src/freshlatch/sli/alert.py` · `tests/unit/test_a_p3_sli_page.py` · `docs/ops/主SLI与burn-rate-page.md`

## Handoff
Draft PR A-P3. No paid「跑」. Leave draft=true.

## Grill 锁（2026-10-15）
1. 主 SLI：e2e P95 + abstain/fallback 率落盘（可接真轨迹窗或 canary_event；夹具目录 alone 不算）
2. multiwindow / 预算燃烧破线规则（文档+可测判定）
3. page=触达指定渠道（邮件或 webhook 接口可测；真实外发可 mock）；ticket=次日
4. 写明 on-call 是谁（非 24×7）；协议页 alone 不算 Done
5. 消费 A-P1 `canary_event` 作为事件源之一
