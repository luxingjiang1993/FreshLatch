# 故障演练 runbook（A-P8）

层：演练。本页是注入失败之后的回滚剧本，并指向一份已经走过的 dry-run 记录。

**演练级 ≠ 真 DAU/真事故史。**

本页不改 floors、gold、x1、`PRODUCTION_RETRIEVAL_MODE`、SESOI、C-04、RESULT-Y。不发明 SESOI。不把演练读数写成注册通过线，也不写成线上事故档案。无付费 API。本页不发起评测「跑」。

注入与回滚只调用已有入口：

- A-P1：`src/freshlatch/canary.py` 的 `CanaryController` 与 `canary_event`。协议是 [`生产路径canary停发.md`](生产路径canary停发.md)。
- A-P3：`src/freshlatch/sli/alert.py` 的 `make_window`、`evaluate_window`、`dispatch_page`。协议是 [`主SLI与burn-rate-page.md`](主SLI与burn-rate-page.md)。

## 谁演练

值班角色是 **生产路径值班**。这是 A-P1 的当班生产路径负责人，也是 A-P3 的同一席位。覆盖是 **非 24×7**，时段是 Asia/Shanghai 工作日 09:00–18:00。演练不把这一席写成 24×7 事故指挥。

## 口径

对照 OTel GenAI：一次操作的 span status 取 `ERROR` 或 `OK`，属性挂在同一次操作上。本剧本把注入、观测、回滚写成同一条本地步骤序列，每步带 `span_status`，并复用 `canary_event` 与主 SLI 字段。不导出 OTel，不接 collector。

对照 Phoenix 的演练轨迹：一次场景、一组步骤、挂上当次字段。本记录是那一口径的本地 dry-run。不绑定 Phoenix，不新建 Phoenix-* 主名。

`halt_above` 与 burn 的 `objective` 只属于这一次注入。它们由调用方传入。它们是演练参数，不是 SESOI，不是注册分，不是 DAU。

## 注入失败

前置：本机 `CANARY_MODE=active`。默认 `off` 时主路径不晋升，失败样本也不会闩住停发，所以注入要先离开 `off`。`shadow` 也会在破线时停发，并且从不晋升；本记录走 `active`，以便看见破线前可以晋升、破线后拒绝晋升。

1. 准备对照臂。臂名不得与主路径 `main` 相同。本记录用 `candidate`。
2. 注入失败样本：`CanarySample(failed=True, metric="error_count", value=3, halt_above=1)`。`failed=true` 即破线。`value > halt_above` 是另一条破线；本记录用失败注入。`halt_above=1` 只是这一次样本上的停发线。
3. 调用 `CanaryController.evaluate("candidate", sample)`。
4. 预期 `canary_event`：`event=canary_event`，`canary_halted=true`，`promoted=false`，`serving_arm=main`，`reason=breach_halt`，`failed=true`。主路径拒绝晋升。
5. 停发已闩。再送健康样本 `CanarySample(failed=False, metric="error_count", value=0, halt_above=1)`。预期仍是 `canary_halted=true`，`promoted=false`，`serving_arm=main`，`latched=true`。健康样本不能自己解开闩。

## 挂上 SLI

只把破线那条 `canary_event` 放进 `make_window(label="failure-drill-dry-run-001", canary_events=[...])`。不传夹具目录。回滚产生的 `mode=off` 事件不放进这个窗。

调用 `evaluate_window`。`sink` 用 `RecordingSender`（只记 payload，不联网）。`channel=webhook`。`environ={}`，这样 page 不会被 sink 关掉。`now` 取破线事件 `ts` 之后、仍落在 `5m` 窗内的带时区时刻。

本次 dry-run 的 `objective=0.01`。这个数只属于这一次演练注入。`alert.py` 没有默认 `objective`。

预期：

- 窗里没有轨迹。`e2e_p95_ms`、`abstain_rate`、`retrieval_fallback_rate`、`abstain_fallback_rate` 都是「样本不足」。禁止写成 0、0% 或 0 ms。同一份主 SLI 里，`N_request_ok`、`N_retrieve`、`abstain_numerator`、`abstain_denominator`、`fallback_n` 会是 0；这些 0 是没有轨迹时的计数字段，比率格仍以「样本不足」为准。
- `sources` 为 `canary_event`。`canary_event_n=1`，`canary_sample_n=1`，`canary_bad_n=1`。这 1 条是演练样本，不是 DAU。
- `counted_as_pass=false`。`invents_sesoi=false`。`writes_result_y=false`。
- 各 burn 窗 `(bad, total)=(1, 1)`。燃烧倍数是 `1 / 0.01 = 100`。长短窗同时超过倍数，所以 page 规则 `page:1h+5m>14.4`、`page:6h+30m>6` 与 ticket 规则 `ticket:1d+2h>3`、`ticket:3d+6h>1` 一起破。
- page 动作 `kind=page`。`RecordingSender` 收下 payload 时 `sent=true`。这表示演练记录器记下了 payload，不是发出了真实 webhook 或 email。ticket 动作 `kind=ticket`，`respond_by=next_business_day`，不调用 page sender。

## 回滚

两步都做。先解开 canary 停发闩，再关掉 page sink。

1. Canary：`CANARY_MODE=off`，进程内对应 `set_mode("off")`。再 `evaluate`。预期 `mode=off`，`canary_halted=false`，`promoted=false`，`serving_arm=main`，`reason=mode_off`。主路径继续原臂。若这一步仍带上健康样本，事件里的 `failed=false`；`mode=off` 本身不晋升。进程重启不代替这一步：模式若仍是 `active` 或 `shadow`，破线会再次停发。
2. Page：`FRESHLATCH_PAGE_SINK=off`。用同一组 burn 窗再调 `dispatch_page`。page 仍记录，`suppressed=true`，`sent=false`，不调用 sender。ticket 仍只记录，`respond_by=next_business_day`。

回滚不改 floors、gold、x1、`PRODUCTION_RETRIEVAL_MODE`。不回写 RESULT-Y。不重跑 C-04。

## 演练记录模板

每次演练落一份记录。已走过的一次是 [`故障演练-dry-run-001.json`](故障演练-dry-run-001.json)。

| 字段 | 填什么 |
|------|--------|
| `drill_id` | 本次编号 |
| `layer` | 固定 `演练级` |
| `scope` | 固定 `演练级 ≠ 真 DAU/真事故史` |
| `walked` | 走过为 true |
| `paid_api` | 固定 false。不发起评测「跑」 |
| `oncall_role` | `生产路径值班` |
| `otel_export` | 固定 false |
| `phoenix_binding` | 固定 false。不新建 Phoenix-* 主名 |
| `inject` | 失败样本、破线 `canary_event`、闩住后的下一条 `canary_event` |
| `sli` | 主 SLI、burn 窗、page / ticket。写明 `objective` 只属于这次注入，以及 sender 是否联网 |
| `rollback` | `CANARY_MODE=off` 之后的 `canary_event`，以及 `FRESHLATCH_PAGE_SINK=off` 的 page / ticket |
| `steps` | 顺序：inject → observe_latch → hang_sli → rollback_canary → rollback_page。`span_status` 取 `ERROR` 或 `OK`，只写在记录里 |

## 范围

演练级 ≠ 真 DAU/真事故史。

单机 canary ≠ 多区渐进发布; ≠ 注册分; ≠ L5.

这里没有线上事故时间线，没有 DAU，没有把 dry-run 的 1 条 `canary_event` 写成流量。`objective` 与 `halt_above` 不是 SESOI。`counted_as_pass` 恒为 false。`RecordingSender` 的 `sent=true` 不是真实外发。
