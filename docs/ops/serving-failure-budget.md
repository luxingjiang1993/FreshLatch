# Serving 失败预算与 Done 口径

> 层：运维口径。本页不测量可用性，不报失败预算消耗，不填目标百分数。
> Grill P2 锁定于 2026-10-15。数值窗口、预算燃烧与告警留给后续 P3/P5；本刀只锁定什么算失败、什么不算。
> 本页不改 floors、gold、x1、`PRODUCTION_RETRIEVAL_MODE`、SESOI、C-04、RESULT-Y。

## Serving Done

无服务端鉴权 ≠ Serving Done。

受保护路由只接受服务端凭证。环境变量 `FRESHLATCH_SERVING_API_KEYS` 的格式是 `token=tenant_id`，多项用逗号分隔。请求使用 `Authorization: Bearer <token>` 或头 `X-API-Key`。映射到的 `tenant_id` 是身份。客户端单独提交的 `tenant_id`（查询参数、请求体或其它头）不构成访问权。声明若与映射不一致，拒绝，不改用客户端的值。

监听 `0.0.0.0`（以及 `::` / `[::]` 或其它非回环地址）且映射未配置或格式不合法时，进程拒绝启动。`0.0.0.0` 无鉴权不是 Serving Done。只绑 `127.0.0.1` 但未配置映射，同样不是 Serving Done：受保护路由返回 401，就绪探针为未就绪。

正确的 401/403 是控制生效，不是对外服务成功。

## 失败预算口径

分母留给 P3/P5 挂数字时沿用。本页不写目标百分数，也不把单次请求当成可用性结论。

计入日后预算的失败：请求已经通过服务端鉴权，且客户端 `tenant_id` 声明缺失或与映射一致，响应却是 5xx。

不计入预算，也不能事后改记成预算内失败的硬违例：

- 无凭证或凭证错误，受保护路由却返回 2xx
- 仅凭客户端 `tenant_id` 返回 2xx
- 客户端 `tenant_id` 与服务端映射不一致，却返回 2xx

正确的 401 与 403 不消耗预算。未配置鉴权导致的就绪未完成，表示这一部署不是 Serving Done，不是可容忍错误。事后把上述硬违例改记成预算内失败，本页口径作废。

P3/P5 在此口径上登记时间窗、目标与预算燃烧告警。那些数字有随机层容差；本页的鉴权与租户映射是确定性层，测试须逐条一致。

## 探针

| 路径 | 含义 | 未配置鉴权 |
|------|------|------------|
| `GET /health/live` | 存活：进程能应答 | 200，`liveness=ok` |
| `GET /health/ready` | 就绪：凭证映射已配置且合法 | 503，`readiness=not_ready` |
| `GET /health` | 同一响应里同时给出两字段 | 200；存活为 ok，就绪为 not_ready |

探针不要求凭证，响应不带租户、不带密钥。存活失败表示进程该重启。就绪失败表示不要把流量送进来，不表示进程已死。`/health` 在进程能应答时保持 200，避免把未就绪误当成存活失败；流量判断以 `/health/ready` 的状态码为准。

## 启动

默认监听 `127.0.0.1`，端口 `8001`。`FRESHLATCH_SERVING_BIND_HOST` 与 `FRESHLATCH_SERVING_PORT` 可覆盖监听面。入口是 `python -m freshlatch.serving.app`。复验单 UI 仍在 `freshlatch.ui`，本面不增加聊天路由。复验单 UI 是本机 demo 面：进程内单会话态，无 cookie/session 分桶，无 Serving API Key 鉴权。UI 无会话分桶 / 多标签串态 = 产品边界（A），**不是**「Serving 未 Done」的证据——**UI 无分桶 ≠ Serving 未 Done**。Serving Done 仍只看本页：服务端凭证映射、401/403、就绪探针；默认口 `127.0.0.1:8001`。
