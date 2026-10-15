# 主 SLI 与 burn-rate page（A-P3）

层：观测。本页落地 e2e P95 与 abstain/fallback 率，以及可调用的 multiwindow burn-rate page。

本页不改 floors、gold、x1、`PRODUCTION_RETRIEVAL_MODE`、SESOI、C-04、RESULT-Y。不发明 SESOI。不把观测读数写成注册通过线。`counted_as_pass` 恒为 false。

代码在 `src/freshlatch/sli/alert.py`。计数复用 `src/freshlatch/eval/trajectory_sli.py` 与 `src/freshlatch/eval/product_sli.py` 的内存入口，不另写一套 P95 / abstain / fallback。

## 主 SLI

同一窗三格：

| 格 | 含义 | 分母 |
|----|------|------|
| `e2e_p95_ms` | 成功完成请求的端到端 P95（毫秒） | `N_request_ok` |
| `abstain_rate` | 主张抽检里的 abstain 占比 | 采样后的主张数 |
| `retrieval_fallback_rate` | `bm25_fallback` 或 `lexical_fallback` 的占比 | 检索调用次数 |

`abstain_fallback_rate` 把后两格写在同一句：`abstain=<率>; fallback=<率>`。两格都是「样本不足」时，这一句也是「样本不足」。禁止把未测写成 0、0% 或 0 ms。

入口是 `measure_primary_sli(SliWindow)`。`SliWindow` 由内存中的轨迹事件和/或 `canary_event` 组成。传入夹具目录会拒绝。只扫夹具目录不算本票 Done。

`run_meta.mode=eval` 的轨迹整份排除，与既有 SLI 相同。金标不进这些格。

## 消费 A-P1 canary_event

事件源之一是 A-P1 的 `canary_event`（`src/freshlatch/canary.py`，协议 [`生产路径canary停发.md`](生产路径canary停发.md)）。本页不发停发闩，停发仍由 `CanaryController` 做。

一条事件算对照样本，当 `failed` 是布尔，或同时有 `value` 与 `halt_above`。是否算坏，调用 `sample_breached`：`failed=true`，或 `value > halt_above`。`failed` 为空且没有停发线的事件（例如 `mode=off`）不进 burn 分母。

`burn_windows_from_canary_events` 按 `ts` 放入 `5m`、`30m`、`1h`、`2h`、`6h`、`1d`、`3d`。窗是 `[now - 窗长, now]`。`ts` 必须带时区。

可选字段 `trajectory_events` 是这次对照所附的轨迹事件，用来落上面三格。没有该字段时，三格只来自同一窗口里的 `trajectory_runs`。

这不是 [`冻结金标canary跑法.md`](冻结金标canary跑法.md)。那边是冻结金标 SLI 6。本页不读金标，不写注册分。

## burn-rate

允许坏率 `objective` 由调用方传入，范围是 `(0, 1)`。本模块没有默认数。这个数不是 SESOI，不是 PREREG floor，不是 RESULT-Y。测试里出现的数字只属于那一次注入。

某一窗的燃烧倍数是 `(bad / total) / objective`。`total=0` 的窗是未测，使用它的规则不破线。不把未测写成 0 倍。

规则是 SRE Workbook《Alerting on SLOs》的 multiwindow multi-burn-rate。倍数按 30 天预算折算，是告警策略，不是产品效应量。短窗和长窗必须同时超过倍数：

| 严重度 | 长窗 | 短窗 | 倍数 | 长窗对应的预算消耗 |
|--------|------|------|------|--------------------|
| page | 1h | 5m | 14.4 | 2% |
| page | 6h | 30m | 6 | 5% |
| ticket | 1d | 2h | 3 | 10% |
| ticket | 3d | 6h | 1 | 10% |

判定函数是 `multiwindow_breach`。缺一窗则这一对不破。

A-P2 的鉴权后 5xx 口径仍在 [`serving-failure-budget.md`](serving-failure-budget.md)。本页不填写目标可用性百分数，也不把单次请求当成可用性结论。burn 的 `(bad, total)` 由调用方注入，或由 `canary_event` 样本折出。

## 谁值班

值班角色是 **生产路径值班**。这是具名角色，不是某一位私人姓名。与 A-P1 的「当班生产路径负责人」是同一席位：谁当班，谁就是这个角色。

覆盖是 **非 24×7**。时段是 Asia/Shanghai 工作日 09:00–18:00。夜间和周末没有值班应答。破线时 page 仍会调用渠道并留下记录；窗口外不保证有人接。ticket 在次日处理，次日指下一工作日，不在夜间叫醒。

## page 与 ticket

| | page | ticket |
|----|------|--------|
| 触发 | 上表前两行，长短窗同时超过 | 上表后两行，长短窗同时超过 |
| 触达 | `webhook` 或 `email`，调用注入的 sender | 不调用 page sender |
| 记录 | `kind=page`，`sent=true`（未抑制时） | `kind=ticket`，`respond_by=next_business_day` |
| 人 | 值班时段内看渠道 | 次日 |

可调用路径是 `freshlatch.sli.alert.dispatch_page`。`evaluate_window` 先落主 SLI，再把 SLI 放进 page / ticket 记录。sender 由调用方注入。`RecordingSender` 只记 payload，不联网。真实 webhook 或 email 传输不在本模块里，测试替换 sender 即可。

回滚：`FRESHLATCH_PAGE_SINK=off`。破线仍记下 page，`suppressed=true`，`sent=false`，不调用 sender。该变量也可设为 `webhook` 或 `email`，用来指定渠道。

## Done 口径

没有可调用的 page 路径 = NOT Done。`page_path_status(None)` 返回 NOT Done。协议页 alone 不算 Done。

只改本页、不调用 `dispatch_page`、或破线时没有可调用的 sender，都不是 Done。`PagePathError` 的文案含「协议页 alone 不算 Done」。
