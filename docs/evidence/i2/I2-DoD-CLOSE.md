# Phase I2 DoD close · smoke-level

> **档：** 冒烟 / 面试安全轮（确定性硬门 + 注入 1× LLM 冒烟）。不报方差；不作渗透认证；**不是** Hard-Gold；**不是**安全通过率。  
> **日期：** 2026-09-29  
> **Refs：** [#219](https://github.com/luxingjiang1993/FreshLatch/issues/219)（本票 · Exit 代收） / parent [#213](https://github.com/luxingjiang1993/FreshLatch/issues/213) / blocked-by [#218](https://github.com/luxingjiang1993/FreshLatch/issues/218) CLOSED via [PR #224](https://github.com/luxingjiang1993/FreshLatch/pull/224) · `GROK-PROXY-APPROVED #218`  
> **规格 / 决议：** `docs/spec/13-PhaseI2-SecurityDemos.md` · ADR-0030 · 评估 `docs/research/I2-安全三例设计评估.md`  
> **硬 Exit 权威：** `docs/evidence/i2/ACCEPTANCE.md`（文首冒烟声明；硬勾三例确定性 + 注入 1× e2e）· 薄表 `docs/security.md`

本页是 I2 Exit 的可引用关门摘要。Exit 由 Ronin 代批（等 `GROK-PROXY-APPROVED #219`）；实现本摘要的 PR 合 main 后可关本票。

## Demo path

越权召回：`retrieve(tenant_id=B)` 不得返回租户 A 块（`acl-t001`）。间接注入：污染 T1 经 `rule_gate` / `_finalize` 不得给出 `fresh`（`inj-t001` 确定性零 LLM；另 1× Lead→Auditor 真模型冒烟终态 `stale` / fail-closed）。检索投毒：显式 `poison`/`untrusted` 高分块入结果前剔除（`poison-t001`）。薄表一行一威胁见 `docs/security.md`。见 `docs/evidence/i2/ACCEPTANCE.md`。

## DoD 硬 Exit 三例 + 互链

- [x] **越权召回 `acl-t001`**（确定性 · 不绑 LLM）  
  `docs/evidence/i2/ACCEPTANCE.md` §2 行 1；`pytest tests/unit/test_i2_retrieve_trust.py -q -k acl_t001`；夹具 `acl-t001.json`；薄表 `docs/security.md`。实现 PR [#220](https://github.com/luxingjiang1993/FreshLatch/pull/220)（#214）。
- [x] **间接注入 `inj-t001`**（确定性 · 零 LLM）  
  ACCEPTANCE §2 行 3；`pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q`；夹具 `inj-t001.md`；薄表同上。实现 PR [#221](https://github.com/luxingjiang1993/FreshLatch/pull/221)（#215）。
- [x] **检索投毒 `poison-t001`**（确定性 · 不绑 LLM）  
  ACCEPTANCE §2 行 2；`pytest tests/unit/test_i2_retrieve_trust.py -q -k poison_t001`；夹具 `poison-t001.json`；薄表同上。实现 PR [#220](https://github.com/luxingjiang1993/FreshLatch/pull/220)（#214）。
- [x] **`docs/security.md` 硬表三行**  
  #217 [PR #223](https://github.com/luxingjiang1993/FreshLatch/pull/223)；与 ACCEPTANCE 互链。
- [x] **`docs/evidence/i2/ACCEPTANCE.md`**  
  文首冒烟；硬三例 + 注入 1× e2e decoding（model=`qwen-flash` · temperature=`0.0` · seed=`218` · 日期=`2026-09-29` · 终态 `stale`）；#218 [PR #224](https://github.com/luxingjiang1993/FreshLatch/pull/224)。

## 可选（不挡硬关）

- [x] **#216 idea #4 `adv-fresh-t001`** — 可选票已 CLOSED；**不计入** I2 硬 Exit（ADR-0030 / I2≠#4）。ACCEPTANCE §4 仅可选分节。本关门不因 #4 缺省主仓证据页而挡硬关。

## 证据引用

| 项 | 指针 |
|----|------|
| 硬 Exit / 冒烟声明 | `docs/evidence/i2/ACCEPTANCE.md` |
| 薄表 | `docs/security.md` |
| 短索引 | `docs/evidence/i2/INDEX.md` |
| 注入 1× e2e | `inj-t001-e2e-summary.json` · `trajectories/inj-t001-e2e-20260929.jsonl` · `tests/unit/test_i2_injection_e2e.py` |
| 实现 PR | [#220](https://github.com/luxingjiang1993/FreshLatch/pull/220) ACL+poison · [#221](https://github.com/luxingjiang1993/FreshLatch/pull/221) 注入 Gate · [#223](https://github.com/luxingjiang1993/FreshLatch/pull/223) 文档 · [#224](https://github.com/luxingjiang1993/FreshLatch/pull/224) e2e+ACCEPTANCE |
| 已关子票 | [#214](https://github.com/luxingjiang1993/FreshLatch/issues/214)–[#218](https://github.com/luxingjiang1993/FreshLatch/issues/218) closed（Ronin 代批；#216 可选）；本票 #219 = Exit |
| 父规格 | [#213](https://github.com/luxingjiang1993/FreshLatch/issues/213)（I2 Exit 代批后收口） |

## Out of Scope（确认未偷渡）

- [x] **安全平台 / 多攻击面大而全**——未开；仅三例冒烟硬门
- [x] **完整 RBAC / 租户管理面**——仅 `retrieve` 显式 `tenant_id` 薄过滤；无管理面
- [x] **无标签投毒启发式作硬门**——poison 仅显式 `poison`/`untrusted` 元数据
- [x] **三威胁全绑 LLM 判生死**——ACL/poison 确定性；注入硬门零 LLM；1× e2e 仅注入冒烟加层
- [x] **用 #4 顶替 I2 Exit**——#4 仅可选；硬勾表不含 `adv-fresh`
- [x] **UI 硬门**——未把安全三例绑成 UI 闸
- [x] **扩 HumanLatch `VALID_ACTIONS`**——未扩
- [x] **改生产默认检索臂**——仍 `bm25`
- [x] **adversarial INDEX 升版 = Done**——未改 `docs/research/adversarial/INDEX.md` 叙事冒充 I2 Done
- [x] **Hard-Gold / 渗透认证 / 安全通过率/方差**——本层不宣称、不升格

## 不宣称渗透认证或 Hard-Gold

本证据层只是冒烟 / 面试安全轮。不把确定性夹具、单次 e2e、或本关门摘要说成渗透认证通过、安全通过率、Hard-Gold、或改默认臂授权。远程 issue CLOSED 不替代 `docs/evidence/i2/ACCEPTANCE.md`。

## 叙事对齐（README / 路线图）

- README：I2 安全三例（ACL·注入·投毒）冒烟在仓；档=冒烟；指针本文件与 ACCEPTANCE；≠ #4；非渗透认证。
- `docs/roadmap.md` Phase I2 Exit：**已齐（冒烟级）**；Out 清单未偷渡；#4 仍可选≠Exit。
- `docs/contribution-boundary.md`：I2 冒烟落地句已补；不是 Hard-Gold / 不是渗透认证。

## 本机关单命令

环境：Linux，Python 3.12+。命令按 #219 Acceptance（文档核对为主；compileall 可选冒烟）。本机 2026-09-29：

```text
$ python3 -m compileall -q src
exit:0

$ PYTHONPATH=src python3 -m pytest tests/unit/test_i2_retrieve_trust.py tests/unit/test_i2_injection_gate.py tests/unit/test_rule_gate.py tests/unit/test_i2_security_index.py tests/unit/test_i2_injection_e2e.py -q
37 passed, 1 skipped
exit:0
```

（真模型注入冒烟权威在 ACCEPTANCE §3；本 DoD 以文档指针 + 确定性复跑为关门核对。）
