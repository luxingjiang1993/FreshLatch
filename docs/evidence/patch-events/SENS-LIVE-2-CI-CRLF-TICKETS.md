# TICKETS — SENS-LIVE-2 Windows CI CRLF（#546 / #542）

> **to-tickets** 来源：已锁 SPEC `docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md`（`fd548cac0e3870bd00e5e822778f64f86f4d7440`）+ RCA `docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-RCA.md`（`045481f637c3484cd36be08472ca8e42a5039938`）。Grill 2026-10-12「按推荐」（G1–G12）。Matt `/to-tickets` plain mode（本账号无 `custom_mode`）。
> **状态**：已发布。本页不是实施授权，不回改 SPEC。
> **父票**: GitHub `#542` · PR `#546` · 分支 `cursor/pe-y-sens-live-2-c869`
> **语言**: 中文。技术词保留 English 原词。
> **本文件不授权**写测、改生产代码、重跑 LIVE-2、合入 `#546`、关闭 `#542`、升格 `activation_prerequisite_met`。

## 拆票决定

一张实现票。SPEC 没有强制拆成多张：G3–G8 与 G10 是同一条垂直切片，落点都是 `tests/unit/test_pe_sensitivity.py`，分开后任何一张都不能单独把 Windows CI 打绿。没有 prefactor，没有 wide refactor，没有 blocker。

任务已经把粒度锁成「尽量少、倾向 1 张」。本步不再另开访谈。

| 票 | Title | Blocked by | 交付 |
|---|---|---|---|
| [#547](https://github.com/luxingjiang1993/FreshLatch/issues/547) | `fix(#542): 修正 CRLF 测的 LF 工作区假设（双语义）` | None | LF 与 CRLF 工作区上同一套 CRLF 断言都绿，仪器锁与正式冻结锁不削弱 |

- **Frontier**：`#547`（无 blocker）。下一跳是 `/enrich-tickets`，不是 `/implement`。
- **标签**：`ready-for-agent`（仓库已有）。没有 pe-y 类标签，不新造。
- **关系**：`#547` 是 `#542` 的 sub-issue。不关 `#542`，不合 `#546`。
- **链级 Destination**：Windows CI pytest 绿，且不削弱仪器锁 / 正式冻结完整性；然后才允许 L1 合入 `#546` 并关 `#542`。`activation_prerequisite_met` 仍为否。合入与关单不在 `#547` 的实施范围内。

## 根因（引用 RCA）

测试把「任何 checkout 的工作区字节 = git blob = LF 钉」写成不变量，而唯一的 CI checkout 给出的是 CRLF 工作区；生产 fold 在 `b9caf32` 已正确。

## Issue #547

以下正文与 GitHub issue 一致。

---

# fix(#542): 修正 CRLF 测的 LF 工作区假设（双语义）

**What to build:** 让 PR [#546](https://github.com/luxingjiang1993/FreshLatch/pull/546) 的 Windows CI 上，`pytest tests/unit/test_pe_sensitivity.py -q` 在工作区已是 CRLF 时通过，且同一套断言在工作区仍是 LF 时也通过。仪器锁与正式冻结锁不削弱。

**Blocked by:** None（可以立刻开始。下一跳是 `/enrich-tickets`，不是 `/implement`）。

**Status:** ready-for-agent

> **链序（G2，禁止跳）：** `/enrich-tickets` → `/before-implement` → `/implement`。本票不是实施授权。`/before-implement` 未过下方 SPEC §7 拒过条件，不得写测试、不得改生产码。

## Parent

- 父票 [#542](https://github.com/luxingjiang1993/FreshLatch/issues/542)（本票是其 sub-issue。本票不关闭 #542）
- PR [#546](https://github.com/luxingjiang1993/FreshLatch/pull/546) · 分支 `cursor/pe-y-sens-live-2-c869`
- SPEC（已锁，commit `fd548cac0e3870bd00e5e822778f64f86f4d7440`）：[`docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md`](https://github.com/luxingjiang1993/FreshLatch/blob/cursor/pe-y-sens-live-2-c869/docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md)
- RCA（commit `045481f637c3484cd36be08472ca8e42a5039938`）：[`docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-RCA.md`](https://github.com/luxingjiang1993/FreshLatch/blob/cursor/pe-y-sens-live-2-c869/docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-RCA.md)
- 票面镜像（本 to-tickets 提交）：`docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-TICKETS.md`

Grill 2026-10-12「按推荐」，G1–G12 全取推荐默认。SPEC 够修，本票不回改 SPEC。

## 根因（RCA 一句）

测试把「任何 checkout 的工作区字节 = git blob = LF 钉」写成不变量，而唯一的 CI checkout 给出的是 CRLF 工作区；生产 `_verify_py_sha256` 已在 `b9caf32` 先把 `\r\n` 折成 `\n` 再对 LF 钉，fold 正确。

Windows 观测 `cee71de30e0a2eca8b8c61ab514132d3412a996852bbcaaa673e0ade108abbef` 只是 CRLF 字节的 sha256，**不是**新钉，禁止写入常量。本轮 CI（run `38210170555`）停在前置断言，G7/G8 后半段尚未在 Windows 上执行；未执行不等于已证伪。

## What to build

Windows CI 作业与 Linux 本地跑同一条 pytest：三条 CRLF 测（或按 SPEC G9 合并后的等价测试）在两种换行下都绿。

- 内容未改时，折行后 `_verify_py_sha256() == VERIFY_PY_SHA256`（`58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`）。CRLF 副本与真实工作区都算「内容未改」。
- 未折行的 CRLF 字节 `sha256 != VERIFY_PY_SHA256`，折行这件事仍被看见。
- 临时副本里把 `ENTAILMENT_TAU = 0.5` 换成 `ENTAILMENT_TAU = 0.4`（一次，替换后字节必须不同）。折行后摘要离开钉。不改生产 τ。
- 仪器锁通过后，名单哈希不符：`run_sens_live2` 抛 `RuntimeError`，消息匹配 `正式冻结`，异常文本不含 `patch_events_verify.py`，`predict_xnli_probs` 调用次数为 0。仪器锁通过且 NLI 为 stub 时，`summary["n_bad"] == 20`，坏槽仍含 `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`。

不按 `os.name` 分叉。不用 `.gitattributes`、`core.autocrlf` 或强制 LF checkout 把 Windows 伪装成 LF。

**链级 Destination（G1 / G11，不是本票的实施动作）：** Windows CI pytest 绿，且不削弱仪器锁 / 正式冻结完整性；然后才允许 L1 合入 `#546` 并关 `#542`。`activation_prerequisite_met` 仍为否。合入、关单、重跑 LIVE-2、升格激活都不在本票。

## Ticket

- **ID**: [#547](https://github.com/luxingjiang1993/FreshLatch/issues/547)
- **Title**: `fix(#542): 修正 CRLF 测的 LF 工作区假设（双语义）`
- **Paths**: 见下。行为改动只允许 `tests/unit/test_pe_sensitivity.py`

## Paths

| 路径 | 本票 |
|---|---|
| `tests/unit/test_pe_sensitivity.py` | **允许改**。只动 CRLF 假设与其直接断言（现有 `_crlf_verify_copy`、`test_verify_py_crlf_matches_lf_pin_but_content_change_does_not`、`test_crlf_checkout_keeps_must_carry_gate`、`test_hash_mismatch_under_crlf_does_not_call_nli`；G9 可合并或改名） |
| `src/freshlatch/eval/patch_events_sensitivity.py` | **默认不动**。`b9caf32` 的 `_normalize_py_newlines` 已只做 `replace(b"\r\n", b"\n")`。优先零 diff |
| `src/freshlatch/eval/patch_events_verify.py` | **禁止**。τ 字面量只许出现在测试临时副本 |
| `docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl` | **禁止** |
| `docs/adr/` 下 ADR-0040 | **禁止** |
| `docs/evidence/patch-events/SENS-LIVE-2.md` 与 scores / run log | **禁止** |
| `docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md` | **禁止**。已锁 |
| `.gitattributes`、`.github/workflows/`、换行配置 | **禁止** |

## 已锁夹具顺序（SPEC Implementation Decisions §2）

CRLF 夹具一律先把 `\r\n` 规范成 `\n`，再把 `\n` 合成 `\r\n`：

`raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")`

禁止在仍含 `\r\n` 的原字节上直接 `replace(b"\n", b"\r\n")`（会得到 `\r\r\n`，生产 fold 只吃掉 `\r\n`，剩下的单独 `\r` 会让摘要离开钉）。工作区已经含 `\r` 时，可以直接把该字节交给仪器锁；合成路径仍然要在，否则 LF checkout 覆盖不到 CRLF。

## Acceptance criteria

实现会话用下面条目验收。每条都能用 diff、源码检索或 pytest 判定。权威文本是 SPEC §3（G3–G8、G10）。G9 允许合并或删除冗余 CRLF 测，合并后 G4–G8 的行为覆盖必须仍有活的测试。

- [ ] **G3 生产折行不动。** 相对 `b9caf32db4b7b0837808391c91274074e29ebe3a`，`VERIFY_PY_SHA256` 仍是 `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`，`FORMAL_FREEZE_SHA256` 仍是 `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`。`_normalize_py_newlines` 仍只把 `\r\n` 换成 `\n`，不删除单独的 `\r`。优先 `src/freshlatch/eval/patch_events_sensitivity.py` 零 diff。
- [ ] **G4 双语义都绿。** 下列行为在工作区 `patch_events_verify.py` 已是 CRLF、以及仍是 LF 时，同一 pytest 都通过。不按 `os.name` 分叉，不靠把 Windows 检出改成 LF 来躲：
  - `test_verify_py_crlf_matches_lf_pin_but_content_change_does_not`
  - `test_crlf_checkout_keeps_must_carry_gate`
  - `test_hash_mismatch_under_crlf_does_not_call_nli`
  - 若按 G9 改名或合并，合并后的测试必须仍覆盖这三条的断言，并在两种换行下都绿。
  - 命令：`pytest tests/unit/test_pe_sensitivity.py -q`
- [ ] **G5 禁止 LF 前提。** 测试源码不得再出现对工作区原字节的 `assert b"\r" not in raw`（或等价「原文件没有 CR 才继续」）。合成路径只走「先 `\r\n`→`\n`，再 `\n`→`\r\n`」。
- [ ] **G6 禁止原字节对钉。** 不得断言 `sha256(工作区原字节) == VERIFY_PY_SHA256`。必须断言：内容未改时折行后 `_verify_py_sha256() == VERIFY_PY_SHA256`；未折行的 CRLF 字节 `sha256 != VERIFY_PY_SHA256`。不得把 `cee71de30…` 写成新常量或新断言钉。
- [ ] **G7 正文一改就离开钉。** 在 CRLF 字节里把 `ENTAILMENT_TAU = 0.5` 换成 `ENTAILMENT_TAU = 0.4`（一次），且替换后字节必须不同于替换前。对该副本，折行后 `_verify_py_sha256() != VERIFY_PY_SHA256`。只改测试用的临时副本，不改生产常量 τ。
- [ ] **G8 仪器锁通过后冻结锁仍在。** CRLF 副本通过仪器锁之后：`run_sens_live2` 在名单哈希不符时抛 `RuntimeError`，消息匹配 `正式冻结`；异常文本不含 `patch_events_verify.py`；NLI `predict_xnli_probs` 调用次数为 0；仪器锁通过且 NLI 为 stub 时 `summary["n_bad"] == 20`，坏槽仍含 `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`。
- [ ] **G10 落点。** 行为 diff 只在 `tests/unit/test_pe_sensitivity.py`。不改写 SPEC 锁。不改 LIVE-2 证据、workflow、`.gitattributes`。

## before-implement 拒过条件（SPEC §7 / G12）

`/before-implement` 见到下列任一条，判拒过，不得进入 `/implement`：

1. 企图改 `VERIFY_PY_SHA256`、`FORMAL_FREEZE_SHA256`、冻结 jsonl、代码内 `SENSITIVITY_SET_S`。
2. 企图改 τ、ρ、ADR-0040 或 `ok` 公式（含把生产 `ENTAILMENT_TAU` 改成 0.4）。
3. 企图重跑 LIVE-2，或改 LIVE-2 报告 / 分表 / run log。
4. 企图把 `activation_prerequisite_met` 写成是，或升格 gate，或开 PE-Y-05。
5. 企图合入 `#543`，或启用过早哈希 `baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c`。
6. 企图改写 `#538` GATE-Y 失败句。
7. 测试计划里恢复 `assert b"\r" not in raw`，或恢复 `sha256(工作区原字节) == VERIFY_PY_SHA256`。
8. 企图去掉折行、改回比原始字节，或把单独 `\r` 一并折掉。
9. 企图用 `.gitattributes` / 强制 LF checkout 躲开 Windows CRLF。
10. 实现落点超出 Paths，或合并测试时丢掉 G7（正文改动离开钉）或 G8（正式冻结拒绝且不调 NLI）。

## Provenance

Paths 触及既有测试。Kind 是 adapt，不是新文件。

- **Kind**: adapt
- **Source**: `tests/unit/test_pe_sensitivity.py` 的 `_crlf_verify_copy` 与上列三条 CRLF 测。自 `b9caf32` 起该文件未改。
- **Pin**: 生产折行 `b9caf32db4b7b0837808391c91274074e29ebe3a`；SPEC `fd548cac0e3870bd00e5e822778f64f86f4d7440`；RCA `045481f637c3484cd36be08472ca8e42a5039938`
- **What changed**: 断言从「工作区原字节」改到「折行后的 `_verify_py_sha256()`」；夹具改为先规范化 LF 再合成 CRLF。
- **Why not copy as-is**: helper 仍假设「同一 LF 源文件写成 CRLF」。Windows 工作区已经是 CRLF，这个前提先失败，G7/G8 还没跑到。
- **License note**: 同仓，无外部代码。

## Agent Guards

薄字段在本票。**Trust / Blast 留给 `/enrich-tickets` 填写**，本 to-tickets 不代填、不宣称 enrich 已完成。

- **Trust**: （enrich）
- **Blast**: （enrich）
- **Tests**: 实现会话 updated（本 to-tickets 不改测试）
- **Do-not-touch**: `VERIFY_PY_SHA256`、`FORMAL_FREEZE_SHA256`、冻结 jsonl、代码内 `SENSITIVITY_SET_S`、τ、ρ、ADR-0040、`ok` 公式、LIVE-2 报告 / 分表 / run log、`#538` 失败句、`#543`、`.gitattributes`、workflow、SPEC 锁、单独 `\r` 的折行语义、`activation_prerequisite_met`
- **Rollback**: 还原 `tests/unit/test_pe_sensitivity.py` 即可；生产 fold 保持 `b9caf32`

## Blocked by

None（can start immediately）。无前置票。Frontier 就是本票。

## 下一跳

```text
/enrich-tickets → /before-implement → /implement
```

不要把本票直接交给 `/implement`。CI 绿、L1 合入 `#546`、关闭 `#542` 都在实现并验收之后，且 `activation_prerequisite_met` 保持否。
