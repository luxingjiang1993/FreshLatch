# 生产路径 canary 停发（A-P1）

单机 canary ≠ 多区渐进发布; ≠ 注册分; ≠ L5.

本页是本机生产路径的发车开关：`CANARY_MODE=off|shadow|active`，默认 `off`。代码在 `src/freshlatch/canary.py`。`CanaryController.evaluate` 决定主路径服役哪条臂。

本页不是 [`冻结金标canary跑法.md`](冻结金标canary跑法.md)。那一页是冻结金标 SLI 6 的离线 pass rate。本页不读金标，不写注册分，不改 `PRODUCTION_RETRIEVAL_MODE`，不发明 SESOI，不重跑 C-04，不改 RESULT-Y。

## 谁看

值班 owner 是当班生产路径负责人。看 `canary_event` 里的 `canary_halted`。`true` 表示这台机器已经停发，canary 臂没有升上主路径。

## 何时停

`shadow` 或 `active` 下，样本 `failed=true`，或 `value` 大于本次调用带入的 `halt_above`，即破线。破线即停：`canary_halted=true`，`promoted=false`，`serving_arm` 保持主路径。停发会闩住，后面的健康样本也不能晋升。

`halt_above` 只是这一次样本上的停发线，不是注册分，也不是 SESOI。

## 如何回滚

把 `CANARY_MODE=off`（进程内对应 `set_mode("off")`）。默认也是 `off`。切回 `off` 解开停发闩，主路径继续原臂，不晋升 canary 臂。

停发闩在本进程内。进程重启不会代替回滚：模式若仍是 `active` 或 `shadow`，要重新对照，破线会再次停发。

## 三种模式

| 模式 | 主路径 |
|------|--------|
| `off` | 不晋升。不写 canary 指标。 |
| `shadow` | 写对照指标，不晋升。破线同样停发。 |
| `active` | 未破线时，本机可以把 canary 臂升上主路径。破线则拒绝晋升。 |

## P3

每次咨询发出 `canary_event`：挂在判定结果上，也可落到调用方指定的 JSONL，或交给 `on_event` hook。P3 消费这些事件做分页。本页不发页、不接告警通道。

## 范围

单机 canary ≠ 多区渐进发布; ≠ 注册分; ≠ L5.

这里没有多区流量阶梯，没有区域摘流，也没有把一次停发写成成熟度等级。发前钩子闸与检索默认臂保持原样。

## Skill 单包（A-P9）

单包 demo / 非 marketplace。

业务 skill 不进 Runner 默认注入。开关是 `FRESHLATCH_SKILL_ALLOWLIST`，环境变量与同名 config 键都认；config 里有该键时优先于环境。未设置、空白、或字面量 `off` 都是 off，不挂任何包。设成恰好一个业务包 slug（`earnings_figures`、`event_timeline`、`patch_diff`、`strategy_walkthrough` 之一）才挂载该包。逗号多项、空格多项、未知 slug、角色包都 fail-closed，不改为挂全部包。

skill→tool 先过 Serving ACL（身份来自 `FRESHLATCH_SERVING_API_KEYS`，客户端单独提交的 `tenant_id` 不构成访问权；工具参数里的 `tenant_id` 还必须与服务端租户一致），再过 `tool_tier`（`dispatch_tiered_tool`）。越权、跨租户、`tool_tier_2`、未过人审的 `tool_tier_1` 都不调用工具。

每次调用写一条轨迹。`latency` 单位是秒。字段只有：

| 字段 | 含义 |
|------|------|
| `package` | 挂上的业务包 slug；未挂载时为空字符串 |
| `id` | 本次调用 id |
| `ok` | 工具是否执行成功 |
| `latency` | 秒 |
| `reason` | 放行时为 `ok`；拒绝时为原因码（`skill_allowlist_off`、`skill_allowlist_invalid`、`skill_not_triggered`、`skill_tool_not_allowed`、`tool_tier_denied`、`tenant_acl_denied`、`SERVING_UNAUTHORIZED`、`SERVING_TENANT_MISMATCH`） |

该触发 / 不该触发用包上的确定性触发词，不调用模型。pytest：`tests/unit/test_skill_allowlist.py`。

发车勾选（可选。不改变本页 canary 的默认 `off`）：

- [ ] 若本机要做单包 demo，`FRESHLATCH_SKILL_ALLOWLIST` 只填一个业务包；未勾选则保持 off
