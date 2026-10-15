# TASK · A-P2 Serving 最小 HTTP API + 服务端鉴权

## Ticket
- **ID**: A-P2
- **Title**: `feat(serving): auth + health liveness/readiness + failure-budget note`
- **Paths**: `src/freshlatch/serving/`（旁挂薄模块，不改复验单 UI），`tests/unit/test_serving_http.py`，`docs/ops/serving-failure-budget.md`，`tasks/A-P2.md`
- **Trust**: Gate (owner standing-auth to Grok for merge; agent opens draft PR)
- **Blast**: auth | api

## Agent Guards
- **Acceptance**:
  1. Server-side auth (Bearer or API key env); unauthenticated protected route → 401/403 in pytest.
  2. Client-supplied `tenant_id` alone never grants access; identity comes from server auth mapping (test).
  3. `/health` exposes liveness and readiness (separate paths or clear fields); pytest covers both.
  4. Short docs page: failure budget + “无服务端鉴权 ≠ Serving Done”.
- **Provenance**: adapt existing FastAPI in `src/freshlatch/ui/app.py` and `publish_hook.py` token pattern if useful; or new thin serving app — prefer minimal blast.
  - Kind: adapt
  - Source: `src/freshlatch/publish_hook.py` 的 token 环境变量与默认回环绑定；`src/freshlatch/ui/app.py` 的 FastAPI 薄壳；`src/freshlatch/store/tenant_acl.py` 的 `resolve_pre_retrieval_tenant`（服务端 tenant 为真相，声明不一致则拒绝）
  - What changed: 新增旁挂 Serving。凭证映射强制存在才算就绪；缺凭证或错凭证为 401；客户端 `tenant_id` 与映射不一致为 403。存活 `/health/live` 与就绪 `/health/ready` 分开，`/health` 同时给出两字段。失败预算只写口径。
  - Why not copy as-is: 发前钩子在未配置 `FRESHLATCH_HOOK_TOKEN` 时仍允许本机探闸。Serving 不能沿用这条例外，否则 0.0.0.0 无鉴权会被当成 Done。也不把复验单 UI 改成聊天产品。
- **Tests**: added（`tests/unit/test_serving_http.py`；无付费 API）
- **Rollback**: 停用 `python -m freshlatch.serving.app`，或去掉 `FRESHLATCH_SERVING_API_KEYS`。未配置时非回环地址拒绝启动，受保护路由 401，就绪为 not_ready。
- **Do-not-touch**: floors / gold / x1 / `PRODUCTION_RETRIEVAL_MODE` / SESOI / C-04 / RESULT-Y

### Provenance status
- result: pass
- notes: 未改 `ui/app.py` 与 `publish_hook.py` 的既有放行行为。租户是否一致复用 `resolve_pre_retrieval_tenant`，不在 Serving 里另写一套比对。

### Evidence
- typecheck: `python -m compileall -q src/freshlatch/serving` 通过
- tests: `python -m pytest tests/unit/test_serving_http.py -q` → 17 passed；无付费 API
- paths: `src/freshlatch/serving/app.py` · `tests/unit/test_serving_http.py` · `docs/ops/serving-failure-budget.md`

## Handoff
2026-10-15 | A-P2 | done | draft PR；pytest 17 passed；无付费 API

## Grill 锁（2026-10-15）
1. 最小 HTTP 服务入口（旁挂现有 FastAPI，不把 UI 聊天化）
2. 服务端鉴权：Bearer 或 API key；缺/错 → 401/403；客户端传入的 `tenant_id` 不可信，必须以服务端身份映射为准
3. `/health`：liveness + readiness 分端点或分字段，可读
4. 失败 budget：docs 写明错误预算口径（与 P3/P5 衔接，本刀只文档化）

不做：默认 0.0.0.0 无鉴权当 Done；改 floors/gold/x1/默认臂。
