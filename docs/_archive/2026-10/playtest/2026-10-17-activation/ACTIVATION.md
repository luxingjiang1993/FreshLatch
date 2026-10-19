# #666 傻瓜壳 Activation 冒烟

日期按 Asia/Shanghai 记为 2026-10-17。机器 UTC 记录落在 2026-10-16。  
范围只有 Activation / 傻瓜壳冒烟。

本笔记**不是** RESULT-Y 乙，**不是** L4，**不是**主实验成功，也**不是** Full UX Go。

## 怎么走的

云端 `POST /api/reverify` 本票没有再打。Start reverify 墙钟引用上一包实测 **137 秒**（`docs/playtest/2026-10-16/api-evidence/20-reverify-live.meta.json`，HTTP 200，12 条主张，latch pending 8，包结论勿发）。

短路径用进程内夹具顶上复验完成态，避免再烧一轮长 LLM：

1. 打开 `/`。主按钮是「一键样例」。`startSample()` 先 `POST /api/t1-source/synthetic`，再 `runReverify()`。本票只测量并调用了合成包这一跳。
2. 夹具写入三条主张并 `enter_round`（零 LLM，真实 HumanLatch interrupt）：`c-fresh` fresh、`c-stale` stale、`c-gap` unknown。待拍板是 `c-stale` 与 `c-gap`。未收口 stale → 包结论勿发。
3. `GET /api/boot` 两次，再 `POST /api/import`。待拍板与勿发仍在，`preserved: true`。
4. 对 `c-stale` 提交 `discard`。该条 `voided: true`，`status` 仍是 stale。轮次关闭后 latch pending 为空。这是人审提交收口，不是 boot 洗单。
5. 浏览器另走同一张活页：空页看主按钮 → 种入夹具 → 刷新两次 → 在「要你确认」点「作废」→「确认作废」→「提交人审决定」。没有点「一键样例」。

三类清单是页面上的展示映射，不新增后端状态。复验刚结束、红黄灯都还在待拍板时，「可能过期」可以是空态「这条里还没有」，定义行仍在。这和 2026-10-16 那次 8 条 pending 盖住全部 stale+unknown 是同一种形状。点作废并确认后，该条立刻离开「要你确认」，落到「可能过期」。

## 逐步结果

| 步 | 结果 | 证据 |
|---|---|---|
| 主 CTA = 一键样例；页内没有「生成答案」「开始复验」 | 通过 | 5/5 落地检查；`screenshots/01-landing-cta-empty-lists.jpg` |
| 三类标题与定义可见（仍可信 / 可能过期 / 要你确认） | 通过 | 同上；职人主路径可见文本无 claim / latch / T0 / fail-closed |
| 一键样例第一跳：选用合成包 | 通过 | `synthetic.ready=true`，`kind=synthetic`，入库 84 块。试次 1 耗时 0.441 秒 |
| 三类映射：仍可信 = fresh；要你确认 = 待拍板；可能过期此时为空 | 通过 | `display_buckets_before_decide`：fresh=`c-fresh`，confirm=`c-stale,c-gap`，maybe=[] |
| 至少一条 discard | 通过 | API `action=discard`，`ok=true`；浏览器点了「作废」并提交。`screenshots/03-after-discard-pick.jpg`、`04-after-submit.jpg` |
| 刷新或 `GET /api/boot` 不洗勿发与待拍板 | 通过 | 见下一节 |

卡点：已走的步骤里没有卡住的一步。云端复验没有重跑，所以不能把「没再打 LLM」写成产品卡点。

## 完成率与时长

同一夹具重复 5 次，5 次都过。这是冒烟计数，不是用户抽样，也不报方差。

| 试次 | 墙钟（秒） | 过 |
|---:|---:|---|
| 1 | 1.213 | 是 |
| 2 | 0.0915 | 是 |
| 3 | 0.0868 | 是 |
| 4 | 0.0874 | 是 |
| 5 | 0.0838 | 是 |

- 模拟完成率：**5/5**（下限 4/5）。
- 短路径单次最长 **1.213 秒**，低于 5 分钟。
- 引用的 Start reverify **137 秒** + 本票最长短路径 **1.213 秒** = **138.213 秒**，仍低于 300 秒。137 秒不是本票新测的。
- 5 次短路径合计 1.5625 秒。明细在 `api-evidence/summary.json` 与 `api-evidence/trials.json`。

## Boot 不洗待拍板

#669（commit `8385c71`）已经把页面 `boot()` 改成只 `GET /api/boot`，不再 `POST /api/import`。单测在 `tests/unit/test_ui_boot_preserve.py`。2026-10-16 的 `screenshots/WIPE_NOTE.md` 记的是改之前的洗单，本票没有复现。

本票本地复测（决定作废之前）：

- 5 次夹具：`disposition=勿发`，pending=`c-stale,c-gap`。第二次 `GET /api/boot` 相同。`POST /api/import` 返回 `preserved: true`，之后再 boot 仍是这两条、仍是勿发。见 `api-evidence/01-boot-before-decide.json`。
- 活页进程：`run-458af63da9`，thread `reverify-round-20261017-live`，`GET /api/boot` 同样是勿发 + 这两条 pending。见 `api-evidence/04-live-boot-before-ui.json` 与 `screenshots/02-boot-keeps-pending.jpg`。浏览器在这张单上刷新了两次，两条仍在「要你确认」。

作废并提交之后，同一 `run-458af63da9` 的 pending 为空，`c-stale.voided=true`，包结论变成**需补丁**。原因是唯一未收口 stale 已被作废，剩下未收口 unknown，按既有聚合就是需补丁。见 `api-evidence/05-live-boot-after-ui-decide.json`。这不是刷新把勿发洗掉。

## Playtest 债

| 债 | 本票 |
|---|---|
| `copy_wrong_job`（主按钮读成「生成答案」） | 已吃掉。服务出去的页和落地检查都没有「生成答案」。未改 `reverify.html`。 |
| CTA（冷启动主按钮曾是「开始复验」） | 已吃掉。唯一主按钮是「一键样例」。「开始复验」不在页内。未改 `reverify.html`。 |
| 勿发 sheet（boot/import 洗掉勿发与待拍板） | 已吃掉（#669）。本票复测见上节。`WIPE_NOTE.md` 留作改前记录。 |
| Control Δ（2026-10-16 记为 n/a） | 仍未测。本票没有重跑对照臂，不把这项写成已关闭。 |

## 明确不声称

- 不是 RESULT-Y 乙。
- 不是 L4。
- 不是主实验成功。
- 不是 Full UX Go。真人盲测仍后补。
- 137 秒是上一包墙钟引用，不是本票重新打出来的云端复验。

## 证据路径

- `api-evidence/summary.json`
- `api-evidence/trials.json`
- `api-evidence/01-boot-before-decide.json`
- `api-evidence/02-decide-discard.json`
- `api-evidence/03-boot-after-decide.json`
- `api-evidence/04-live-boot-before-ui.json`
- `api-evidence/05-live-boot-after-ui-decide.json`
- `screenshots/01-landing-cta-empty-lists.jpg`
- `screenshots/02-boot-keeps-pending.jpg`
- `screenshots/03-after-discard-pick.jpg`
- `screenshots/04-after-submit.jpg`

## 验收对照（enrich GWT）

1. 一键样例 → 三类白话清单 → 至少一条 discard：通过。样例第一跳实测；清单与作废用夹具加浏览器。云端复验用 137 秒引用，没有重跑。
2. 有 pending / 勿发时刷新或 `GET /api/boot` 仍在：通过。引用 #669，并有上面的本地复测。
3. 完成率与时长：5/5；短路径与「137 秒 + 短路径」都 ≤5 分钟；已走步骤无卡点。
4. 先吃 playtest 债再下结论：三项壳债已吃掉；Control Δ 仍是 n/a。没有从空白重编卡点，也没有为文案改 `reverify.html`。
5. 措辞只谈 Activation / 傻瓜壳冒烟。

## Evidence

`python -m compileall -q src` 退出码 0 · `pytest -q tests/unit/test_ui_boot_preserve.py tests/unit/test_ui_redlines.py tests/unit/test_ui_latch.py` 32 passed · 路径只增加 `docs/playtest/2026-10-17-activation/` 与 `docs/playtest/README.md` 一行索引，产品代码无漂移。
