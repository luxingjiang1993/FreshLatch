# SPEC — SENS-LIVE-2 Windows CI CRLF（#546 / #542）

> **to-spec 来源**: wayfinder `freshlatch-yi-pr546-crlf-wayfinder` · grill **LOCKED 2026-10-12「按推荐」**（G1–G12 全取推荐默认）· Matt `/to-spec` plain mode（本账号无 `custom_mode`；按 [to-spec 模板](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md) 合成，**不再访谈**）
> **状态**: 本页已锁。缝已由 G10 预确认：沿用现有单测缝，不新开模块。
> **父票**: GitHub `#542` · PR `#546` · head 起点 `b9caf32db4b7b0837808391c91274074e29ebe3a`
> **语言**: 中文。技术词保留 English 原词。
> **本文件不授权**写测、改生产代码、重跑 LIVE-2、合入 `#546`、关闭 `#542`。

## 1. Destination（钉死）

### Problem Statement

PR `#546` 的 LIVE-2 证据已经在分支上，生产侧 `_verify_py_sha256` 也已经在哈希前把 `\r\n` 折成 `\n`。Windows CI 仍然红：3 个单测把「工作区是 LF」写死了。Windows checkout 下 `patch_events_verify.py` 已是 CRLF，这些断言先失败，仪器锁和正式冻结锁都还没被真正打到。

### Solution

只改 CRLF 相关测的假设，让同一套断言在「工作区已是 CRLF」和「工作区仍是 LF」两种语义下都成立。生产折行保持 `b9caf32` 的语义。仪器锁、正式冻结、τ、ρ、ADR-0040 不放宽。CI 绿之后才允许 L1 合入 `#546` 并关 `#542`，且 `activation_prerequisite_met` 仍为否。

**Destination 是**：Windows CI pytest 绿，且不削弱仪器锁 / 正式冻结完整性；然后合 `#546`、关 `#542`，`activation_prerequisite_met` 仍为否。

**Destination 不是**：重跑 LIVE-2、改 τ / ρ、改冻结 S、改 `VERIFY_PY_SHA256`、激活、合 `#543`、开 PE-Y-05、改写 `#538` 失败句。

## 2. Inputs / Provenance

### Grill 锁

| 项 | 已锁值 | 出处 |
|---|---|---|
| 锁日 | 2026-10-12「按推荐」；G1–G12 一律推荐默认 | grill |
| 正式冻结 S | sha256 `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` | grill 继承 / `FORMAL_FREEZE_SHA256` |
| 仪器钉 | `VERIFY_PY_SHA256` = `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`（LF 字节） | 代码常量；本 SPEC 禁止改 |
| 生产折行 | `_verify_py_sha256` 先 `replace(b"\r\n", b"\n")` 再哈希；单独 `\r` 不折 | commit `b9caf32` |
| LIVE-2 | S1–S4 过现行 ρ；S2=0.9000；`activation_prerequisite_met`=否；`gate_passed`=否 | 分支证据；不重跑 |
| #538 | GATE-Y 失败句保留 | grill / 硬约束 |
| #543 | 不合入；过早哈希 `baf33f5b9e0ea801c736d67385a94546fb6bd24af1ada0e4f27d1b9f5da1fa8c` 不是本冻结 | grill |

G1–G12 答案全部是「按推荐」。本 SPEC 不重开这些题。

### CI 失败锚（未在本步复跑）

| 项 | 值 |
|---|---|
| 运行 | GitHub Actions `ci` / `pytest` · run `38208715004`（pull_request） |
| head | `b9caf32db4b7b0837808391c91274074e29ebe3a` |
| 作业 | `Run tests (zero LLM)` · `pwsh` · Windows |
| 失败数 | 3 |

| 测 | 挂点（`b9caf32` 行号） | 观测 |
|---|---|---|
| `test_verify_py_crlf_matches_lf_pin_but_content_change_does_not` | `tests/unit/test_pe_sensitivity.py:245` | `sha256(工作区原字节)` = `cee71de30e0a2eca8b8c61ab514132d3412a996852bbcaaa673e0ade108abbef`，不等于 LF 钉 `58bdae90…739918` |
| `test_crlf_checkout_keeps_must_carry_gate` | `:232` `_crlf_verify_copy` | `assert b"\r" not in raw` 失败；工作区原字节已含 `\r\n` |
| `test_hash_mismatch_under_crlf_does_not_call_nli` | `:232` 同上 | 同上，未进入名单哈希 / NLI 断言 |

`cee71de30…` 只是这次 Windows checkout 的观测值，**不是**新钉，禁止写进常量。

### `b9caf32` 折行（生产已在，本 SPEC 保持）

`_normalize_py_newlines` 只做 `raw.replace(b"\r\n", b"\n")`。`_verify_py_sha256` 对折行后的字节取 sha256，再和 `VERIFY_PY_SHA256` 比。仪器锁失败文案含 `patch_events_verify.py`。名单不符走「正式冻结」`RuntimeError`，且不调用 NLI。本步不改这段生产逻辑。

## 3. Acceptance（可执行）

实现会话用下面条目验收。每条都能用 diff、源码检索或 pytest 判定。G9 允许把冗余 CRLF 测合并或删除，但合并后 G4–G8 的行为覆盖必须仍有活的测试。

1. **G3 生产折行不动。** 相对 `b9caf32`，`VERIFY_PY_SHA256` 与 `FORMAL_FREEZE_SHA256` 字符串不变。`_normalize_py_newlines` 仍只把 `\r\n` 换成 `\n`，不删除单独的 `\r`。优先生产文件零 diff；若有 diff，只能是折行旁的注释，折叠语义的字节行为不变。
2. **G4 双语义都绿。** 下列行为在工作区 `patch_events_verify.py` 已是 CRLF、以及仍是 LF 时，同一 pytest 都通过（不按 `os.name` 分叉，不靠把 Windows 检出改成 LF 来躲）：
   - `test_verify_py_crlf_matches_lf_pin_but_content_change_does_not`
   - `test_crlf_checkout_keeps_must_carry_gate`
   - `test_hash_mismatch_under_crlf_does_not_call_nli`
   - 若按 G9 改名或合并，合并后的测试必须仍覆盖这三条的断言，并在两种换行下都绿。
   - 命令形状：`pytest tests/unit/test_pe_sensitivity.py -q`（实现会话执行；本 to-spec 不跑）。
3. **G5 禁止 LF 前提。** 测试源码不得再出现对工作区原字节的 `assert b"\r" not in raw`（或等价「原文件没有 CR 才继续」）。已有 `\r` 时直接测仪器锁，或先规范成 LF 再合成 CRLF。本 SPEC 把后者定为唯一合成路径，避免 `\r\n` 上再 `replace(b"\n", b"\r\n")` 得到 `\r\r\n`。
4. **G6 禁止原字节对钉。** 不得断言 `sha256(工作区原字节) == VERIFY_PY_SHA256`。必须断言：
   - 内容未改时，折行后 `_verify_py_sha256() == VERIFY_PY_SHA256`（CRLF 副本与真实工作区都算「内容未改」）；
   - 未折行的 CRLF 字节（合成出的 CRLF）`sha256 != VERIFY_PY_SHA256`。
5. **G7 正文一改就离开钉。** 在 CRLF 字节里把 `ENTAILMENT_TAU = 0.5` 换成 `ENTAILMENT_TAU = 0.4`（一次），且替换后字节必须不同于替换前。对该副本，折行后 `_verify_py_sha256() != VERIFY_PY_SHA256`。这只改测试用的临时副本，不改生产常量 τ。
6. **G8 仪器锁通过后冻结锁仍在。** CRLF 副本通过仪器锁之后：
   - `run_sens_live2` 在名单哈希不符时抛 `RuntimeError`，消息匹配 `正式冻结`；
   - 异常文本不含 `patch_events_verify.py`（不得先被仪器锁文案挡住）；
   - NLI `predict_xnli_probs` 调用次数为 0；
   - 仪器锁通过且 NLI 为 stub 时，`summary["n_bad"] == 20`，坏槽仍含 `DIAG-CHEF-03-bad` 与 `DIAG-CHEF-04-bad`。
7. **G10 落点。** 实现 diff 的行为改动只在 `tests/unit/test_pe_sensitivity.py`。生产文件见第 1 条。本 SPEC 文件属于 to-spec 提交，实现会话不得改写本锁。

### User Stories

1. As a Windows CI 作业, I want 上述三条 CRLF 测在工作区已是 CRLF 时通过, so that `#546` 的 pytest 变绿。
2. As a Linux 本地跑测者, I want 同一条测在工作区仍是 LF 时通过, so that 修 Windows 不把本地打红。
3. As a 仪器锁守门人, I want 哈希前只折 `\r\n`→`\n`, so that CRLF 检出不假性打破 `VERIFY_PY_SHA256`。
4. As a 仪器锁守门人, I want 单独的 `\r` 不被折掉, so that 非换行 CR 仍会让摘要离开钉。
5. As a 仪器锁守门人, I want `VERIFY_PY_SHA256` 常量保持 LF 钉, so that 不为 Windows 另立一个 CRLF 钉。
6. As a 测作者, I want 断言打在折行后的 `_verify_py_sha256()`, so that 工作区原字节是 LF 还是 CRLF 都不会先炸。
7. As a 测作者, I want 未折行的 CRLF 字节明确不等于钉, so that 「折行」本身仍被看见，而不是静默改钉。
8. As a 测作者, I want 临时副本里的 τ 文本一改，折行摘要就离开钉, so that 仪器锁仍然能抓住正文改动。
9. As a 正式冻结守门人, I want CRLF 下仪器锁通过后仍执行 must-carry / `n_bad == 20`, so that 换行修复不绕过正式 S。
10. As a 正式冻结守门人, I want 名单哈希不符时拒绝开跑且不调用 NLI, so that 坏冻结不能进入打分。
11. As a 正式冻结守门人, I want 该错误走「正式冻结」文案而不是仪器锁文案, so that 失败层不会被误判成 `patch_events_verify.py`。
12. As a 测维护者, I want 可以合并冗余 CRLF 测, so that 文件变瘦，但 G4–G8 覆盖还在。
13. As a before-implement 守门, I want 改钉、改 τ/ρ、重跑 LIVE-2、升格激活、合 `#543` 被拒, so that 修 CI 不变成第二轮敏感性谈判。
14. As a 地图维护者, I want CI 绿之后才 L1 合 `#546` 并关 `#542`, so that 关单时 Windows pytest 已经是绿的。
15. As a 激活守门人, I want 关单后 `activation_prerequisite_met` 仍为否, so that LIVE-2 过 ρ 不被写成激活。
16. As a 抄表人, I want `#538` 的失败句保持原样, so that 本 SPEC 不改写历史 GATE-Y 句子。

### Implementation Decisions

行为决定如下。路径只出现在 §5。

1. 生产哈希契约维持：读字节 → 只把 `\r\n` 折成 `\n` → sha256 → 与既有 LF 钉比较。不新增第二枚钉。
2. CRLF 夹具一律「先把 `\r\n` 规范成 `\n`，再把 `\n` 合成 `\r\n`」。禁止在仍含 `\r\n` 的原字节上直接把 `\n` 换成 `\r\n`。
3. 工作区真实文件只用于「折行后摘要等于钉」这一条。它的原字节不得拿去和钉做相等断言。
4. τ 扰动沿用现有字面量替换：`ENTAILMENT_TAU = 0.5` → `ENTAILMENT_TAU = 0.4`，一次，作用在临时 CRLF 副本上。
5. 名单不符夹具沿用现有「改第一条 sample 的 `note`」做法；异常匹配 `正式冻结`；spy 证明 NLI 未被调用。
6. must-carry 仍看 `n_bad == 20` 与 `DIAG-CHEF-03-bad` / `DIAG-CHEF-04-bad`。不改冻结 jsonl，不改代码内 24 条 `SENSITIVITY_SET_S`。
7. 测试缝保持现有：monkeypatch `_verify_py_path`，调用 `_verify_py_sha256` 与 `run_sens_live2`。不新开测试模块，不新开生产入口。
8. 允许按 G9 瘦测。不允许为了变瘦删掉 G7 或 G8。

## 4. Test strategy

缝：现有 `tests/unit/test_pe_sensitivity.py` 里对 `_verify_py_sha256` / `run_sens_live2` 的外部行为。先验是同文件的 `test_hash_mismatch_does_not_call_nli` 与这三条 CRLF 测。好的测试只看折行摘要、拒绝层级、是否调用 NLI、must-carry 计数。不测 NLI 张量，不重跑真权重。

### 双语义

| 工作区 | 测必须成立的原因 |
|---|---|
| 已是 CRLF（Windows CI，run `38208715004` 那种 checkout） | 原字节含 `\r`；折行后才等于 LF 钉 |
| 仍是 LF（Linux 本地） | 原字节可以不含 `\r`；合成 CRLF 之后仍要走同一套断言 |

两种语义用同一条合成路径覆盖，不写 `if os.name == "nt"`。一次 pytest 在任一 checkout 上都应绿。Windows CI 绿是外部证明；LF checkout 绿是另一端证明。本 to-spec 两头都不跑。

### 禁止

- `assert b"\r" not in raw`（以及任何「工作区原文件不得含 CR」的前提）。
- `sha256(工作区原字节) == VERIFY_PY_SHA256`。
- 把观测到的 CRLF 摘要 `cee71de30…` 写成新常量或新断言钉。
- 用 `.gitattributes`、`core.autocrlf` 或强制 LF checkout 让 Windows 看起来像 LF，从而躲开 CRLF 语义。

### 允许

- 从规范化 LF 再合成 CRLF：`raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")` 这种顺序。
- 工作区已经含 `\r` 时，直接把该字节交给仪器锁（折行后等于钉）。合成路径仍然要在，否则 LF checkout 覆盖不到 CRLF。
- G9：删除或合并冗余 CRLF 测，只要 §3 的 G4–G8 覆盖还在。
- 可选、不强制：单独 `\r` 不被折掉的回归断言。若写，必须放在 §5 的测试文件里，并断言折行摘要离开钉。不得为此放宽生产折行。

## 5. Paths

| 路径 | 本链处置 |
|---|---|
| `tests/unit/test_pe_sensitivity.py` | **允许改**（实现会话）。只动 CRLF 假设与其直接断言。 |
| `src/freshlatch/eval/patch_events_sensitivity.py` | **默认不动**。`b9caf32` 折行已在。极小注释可以，禁止改常量、折行语义、τ、ρ、冻结比较。 |
| `docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md` | **本步写入**。实现会话不得改锁。 |
| `src/freshlatch/eval/patch_events_verify.py` | **禁止**。τ 字面量只许出现在测试临时副本里。 |
| `docs/evidence/patch-events/SENS-S-FREEZE-formal-S.jsonl` | **禁止**。 |
| `docs/adr/` 下 ADR-0040 | **禁止**。 |
| `docs/evidence/patch-events/SENS-LIVE-2.md` 与 scores / run log | **禁止**。不重跑、不改表。 |
| `.gitattributes` 及换行配置 | **禁止**。不得用检出策略代替测试修复。 |

## 6. Out of Scope / Non-goals

- 改 `VERIFY_PY_SHA256`、`FORMAL_FREEZE_SHA256`、冻结 jsonl、代码内 `SENSITIVITY_SET_S`。
- 改 τ、ρ、ADR-0040、`ok` 公式。
- 重跑 LIVE-2 真权重；改写 `#538` GATE-Y 失败句。
- `activation_prerequisite_met=是`、gate 升格、PE-Y-05、n=400。
- 合入 `#543`；把过早哈希当作正式冻结。
- 为 CRLF 另立一枚 sha256 钉。
- 把单独的 `\r` 也折掉。
- 本会话写测试、改生产逻辑、跑 pytest、跑 LIVE-2、合并 PR、关 issue。
- 在 issue tracker 新开票或打 `ready-for-agent`。派工是下一跳 `/to-tickets`，不是本步。

## 7. before-implement 拒过条件（G12）

`/before-implement` 见到下列任一条，判拒过，不得进入 `/implement`：

1. 企图改 `VERIFY_PY_SHA256`、`FORMAL_FREEZE_SHA256`、冻结 jsonl、代码内 `SENSITIVITY_SET_S`。
2. 企图改 τ、ρ、ADR-0040 或 `ok` 公式（含把生产 `ENTAILMENT_TAU` 改成 0.4）。
3. 企图重跑 LIVE-2，或改 LIVE-2 报告 / 分表 / run log。
4. 企图把 `activation_prerequisite_met` 写成是，或升格 gate，或开 PE-Y-05。
5. 企图合入 `#543`，或启用过早哈希。
6. 企图改写 `#538` GATE-Y 失败句。
7. 测试计划里恢复 `assert b"\r" not in raw`，或恢复 `sha256(工作区原字节) == VERIFY_PY_SHA256`。
8. 企图去掉折行、改回比原始字节，或把单独 `\r` 一并折掉。
9. 企图用 `.gitattributes` / 强制 LF checkout 躲开 Windows CRLF。
10. 实现落点超出 §5，或合并测试时丢掉 G7（正文改动离开钉）或 G8（正式冻结拒绝且不调 NLI）。

## 8. Next steps

```text
/to-tickets → enrich → before-implement → /implement
```

本文件是 `/to-spec` 的锁，不是实施授权。下一步才拆票。`/implement` 之前必须过 §7。CI 绿、L1 合入 `#546`、关闭 `#542` 都在实现并验收之后，且 `activation_prerequisite_met` 保持否。

### Further Notes

- plain mode：没有 custom skill 覆盖。缝不再拿回来问；G10 已经把缝钉在现有单测。
- 本步不发布新的 tracker issue，不加 `ready-for-agent`。G2 禁止跳过 to-tickets。
- 行号锚是 `b9caf32` 上的位置。实现改测试后行号会动；验收以测试名和 §3 行为为准。
