# RCA — SENS-LIVE-2 Windows CI CRLF（#546 / #542）

> **性质**: 只读根因分析。本页不授权改测试、改生产代码、改钉、重跑 LIVE-2、合入或关单。
> **对照锁**: `docs/evidence/patch-events/SENS-LIVE-2-CI-CRLF-SPEC.md`（`fd548ca`，已锁）
> **Grill**: 2026-10-12「按推荐」G1–G12
> **分析 head**: `fd548cac0e3870bd00e5e822778f64f86f4d7440`
> **语言**: 中文。技术词保留 English 原词。

## 0. 结论

三条失败是**同一根因**。

Windows CI 的工作区把 git blob 里的 LF `patch_events_verify.py` 写成了 CRLF。三条测仍把「工作区原字节是 LF、且 `sha256(原字节) == VERIFY_PY_SHA256`」写成前置条件，于是在生产折行之前失败。

生产 `_verify_py_sha256` 已在 `b9caf32` 先做 `\r\n`→`\n` 再对 LF 钉。钉 `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918` 与当前 blob 的 LF sha256 一致。Windows 观测 `cee71de30e0a2eca8b8c61ab514132d3412a996852bbcaaa673e0ade108abbef` 等于同一字节把每个 `\n` 换成 `\r\n` 之后的 sha256，**不是**新钉，也不是内容漂移。

`SENS-LIVE-2-CI-CRLF-SPEC.md` 的验收已经覆盖修复方向。本 RCA 补上的是字节级同一性、触发条件的配置层、以及「本轮 CI 没有跑到 G7/G8 后半段」。这些不是行为缺口，**不必为了拆票回改已锁 SPEC**。下一跳是 Matt `/to-tickets`，不是 `/implement`。

## 1. 现象

| 项 | 值 |
|---|---|
| Workflow | `.github/workflows/ci.yml` · `ci` / job `pytest` |
| Runner | `windows-latest`（该 workflow 只有这一个 pytest job） |
| Run | `38210170555` · https://github.com/luxingjiang1993/FreshLatch/actions/runs/38210170555 |
| Job | `114682341989` · `Run tests (zero LLM)` · `python -m pytest tests/ -q` |
| head | `fd548cac0e3870bd00e5e822778f64f86f4d7440`（`pull_request`） |
| 计数 | 3 failed, 1194 passed, 4 skipped（181.12s） |
| 相对 `b9caf32` | 仅新增 SPEC 文档。`src/`、`tests/`、workflow 零 diff |

失败只在 `tests/unit/test_pe_sensitivity.py`：

| 测 | CI 挂点 | 断言 |
|---|---|---|
| `test_verify_py_crlf_matches_lf_pin_but_content_change_does_not` | `:245` | `sha256(raw) == VERIFY_PY_SHA256`。实际 `cee71de30…`，期望 `58bdae90…` |
| `test_crlf_checkout_keeps_must_carry_gate` | `:265` → `_crlf_verify_copy` `:232` | `assert b"\r" not in raw`。repr 末尾已是 `\r\n` |
| `test_hash_mismatch_under_crlf_does_not_call_nli` | `:309` → 同上 `:232` | 同上。未进入名单哈希 / NLI |

摘录来源：该 job 的 FAILURES 段（`uploads/windows-pytest-failures-full.txt`）。行号与当前 head 源码一致（`b9caf32` 之后测试文件未改）。

## 2. 复现

### 2.1 仓库侧（LF 工作区，本分析机）

`git ls-files --eol`：

```text
i/lf    w/lf    attr/    src/freshlatch/eval/patch_events_verify.py
i/lf    w/lf    attr/    tests/unit/test_pe_sensitivity.py
```

仓库根目录没有 `.gitattributes`。`git check-attr -a` 对上述文件无输出。本机 git config 没有 `core.autocrlf` / `core.eol`。

对 `src/freshlatch/eval/patch_events_verify.py` 的工作区字节（4121 bytes）：

| 量 | 值 |
|---|---|
| `\r` | 0 |
| `\n` | 106 |
| `\r\n` | 0 |
| 单独 `\r` | 0 |
| BOM / 前 8000 字节 NUL | 无 |
| `sha256(raw)` | `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918` |
| 与 `VERIFY_PY_SHA256` | 相等 |
| `sha256(raw.replace(b"\n", b"\r\n"))` | `cee71de30e0a2eca8b8c61ab514132d3412a996852bbcaaa673e0ade108abbef` |
| 与 Windows 观测 | 相等（106 处 `\n` 一对一变成 `\r\n`，4227 bytes） |
| 再 `replace(b"\r\n", b"\n")` | 回到原 LF 字节，sha256 回到钉 |
| `ENTAILMENT_TAU = 0.5` 出现次数 | 1（`patch_events_verify.py:22`） |

LF 工作区跑这三条，外加两条会走到真实 `_verify_py_path()` 的旁证测（stub NLI，不是 LIVE-2 真权重）：

```text
pytest tests/unit/test_pe_sensitivity.py::test_verify_py_crlf_matches_lf_pin_but_content_change_does_not \
  ::test_crlf_checkout_keeps_must_carry_gate \
  ::test_hash_mismatch_under_crlf_does_not_call_nli \
  ::test_hash_mismatch_does_not_call_nli \
  ::test_formal_freeze_keeps_must_carry_and_s2_denominator -q
```

结果：`5 passed in 0.25s`。

### 2.2 CI 侧（CRLF 工作区）

workflow 步骤是 `actions/checkout@v4`，没有 `git config`，没有 autocrlf 开关（`.github/workflows/ci.yml`）。

本 job 日志没有打印 `git config core.autocrlf`。能从日志直接读到的是失败 repr：工作区 `patch_events_verify.py` 含 `\r\n`。GitHub 对 `windows-latest` 的公开说明是：镜像沿用 Git for Windows 的全局 `core.autocrlf=true`；没有 `.gitattributes` 时，git 判为 text、且 blob 为 LF 的文件，checkout 写成 CRLF（[actions/checkout#135](https://github.com/actions/checkout/issues/135)，[actions/runner-images#32](https://github.com/actions/runner-images/issues/32)）。`actions/checkout@v4` 默认不把该值改成 `false`。

这条配置说明与观测闭合：blob 是 LF，CI 工作区含 `\r\n`，且 sha256 **精确等于**「LF 字节把 `\n` 换成 `\r\n`」。中间没有 BOM、没有多出来的字节、没有第二套内容。

## 3. 因果链

```text
git blob（LF，sha256 = 58bdae… = VERIFY_PY_SHA256）
    │
    │  windows-latest：无 .gitattributes，text 文件按 core.autocrlf=true 检出
    ▼
工作区 patch_events_verify.py（CRLF，sha256 = cee71de30…）
    │
    ├─ 生产 _verify_py_sha256
    │     read_bytes → replace(b"\r\n", b"\n") → sha256 → 与钉比较
    │     层：折行后的字节
    │
    └─ 三条测（b9caf32 与 fold 同一次提交写上）
          层：工作区原字节
          │
          ├─ :245  sha256(原字节) == 钉          → 第 1 条在这里失败
          │         随后才 replace(\n → \r\n)、才调用 _verify_py_sha256
          │
          └─ _crlf_verify_copy :232
                assert b"\r" not in 原字节       → 第 2、3 条在这里失败
                随后才 replace(\n → \r\n)，才 monkeypatch，才 run_sens_live2
```

四层不要并成一句：

| 层 | 是什么 |
|---|---|
| 触发条件 | `windows-latest` checkout 把 LF blob 写成 CRLF 工作区。本仓没有 `.gitattributes` 把 `patch_events_verify.py` 钉成 `eol=lf`。workflow 也没有关掉 autocrlf |
| 直接原因 | 断言打在工作区原字节上：`:245` 对钉，`:232` 要求没有 `\r` |
| 根因 | 测试契约假设「任何 checkout 的工作区字节 = git blob = LF 钉」。生产契约是「先只折 `\r\n`，再和 LF 钉比」。两套契约不在同一层。fold 已经按生产契约落地，测试仍按旧的工作区契约写 |
| 为何一边绿一边红 | 绿的是 LF 工作区（索引 `i/lf`、工作区 `w/lf`；本机 5 passed）。红的是 CRLF 工作区（本 CI）。workflow **没有** Linux job。同一条断言，两种工作区字节 |

`b9caf32` 的提交说明已经写了「Windows checkout 把该文件写成 CRLF，原始字节 sha256 偏离 LF 摘要」，并加上了 `_normalize_py_newlines`。同一次 diff 把三条测加进 `tests/unit/test_pe_sensitivity.py`，helper 文档字符串仍是「模拟 Windows checkout：同一 **LF 源文件**写成 CRLF」。生产修的是哈希层，测试修的是「从 LF 再模拟一份 CRLF」。CI 上源文件已经是 CRLF，模拟的前提不成立，所以生产 fold 救不了这三条。

## 4. 根因（确认）

**确认。** 根因是测试把 LF 工作区写成了不变量，而唯一的 CI checkout 给出的是 CRLF 工作区。

三条是同一根因的三个出口：

1. `test_verify_py_crlf_matches_lf_pin_but_content_change_does_not` 自己读工作区并在 `:245` 对钉。它不经过 `_crlf_verify_copy`，但前提与 helper 相同：原字节必须已经是 LF。
2. `test_crlf_checkout_keeps_must_carry_gate` 死在 helper 的「原文件没有 CR」。
3. `test_hash_mismatch_under_crlf_does_not_call_nli` 与第 2 条共用 helper，死在同一行。

第 2、3 条的 must-carry、`正式冻结`、`predict_xnli_probs` 调用次数，在本 run 里都还没执行。失败摘要不能被读成「CRLF 下 must-carry 坏了」或「CRLF 下 NLI 被调用了」。

## 5. 排除项

下列项都用本 head 的字节或本 run 的通过列表核对过。

| 假设 | 核对结果 |
|---|---|
| `VERIFY_PY_SHA256` 过时，跟当前 `patch_events_verify.py` 对不上 | LF sha256 等于钉 `58bdae…`。`fd548ca` 未改该文件 |
| Windows 观测 `cee71de30…` 表示内容被改、多了 BOM、或混有单独 `\r` | 该值等于 106 个 `\n` 一对一换成 `\r\n`。折回去等于原 LF |
| 生产 fold 在本轮 Windows 工作区上对不齐钉 | `_normalize_py_newlines` 只做 `raw.replace(b"\r\n", b"\n")`（`patch_events_sensitivity.py`）。同文件的 `test_formal_freeze_keeps_must_carry_and_s2_denominator` 与 `test_hash_mismatch_does_not_call_nli` 调用 `run_sens_live2`，且不替换 `_verify_py_path`。仪器锁在 `assert_formal_freeze_structure` 里：折行摘要不等于钉就抛出含 `patch_events_verify.py` 的 `RuntimeError`（约 `:765`）。这两条不在 FAILED 列表里，源码也没有 skip。本轮 CRLF 工作区上，折行后的摘要等于钉 |
| 仪器锁和名单锁的先后被测反了 | `run_sens_live2` 先 `assert_formal_freeze_structure`（其中含仪器锁），再 `formal_freeze_sha256`，不符才抛「冻结 sha256 与正式冻结不一致」（约 `:867`）。第 3 条测要的就是「仪器锁先过，再在名单层拒绝且不调 NLI」。它死在 helper，还没进入这条顺序 |
| 冻结 jsonl 在 Windows 上被 `write_text` 写成 CRLF，导致第 3 条失败 | 第 3 条在写 jsonl 之前就失败。名单哈希是解析后的 canonical JSON，不是文件原字节。走同一写法的 `test_hash_mismatch_does_not_call_nli` 已在本 run 通过 |
| 测试文件自身的 CRLF 让 `b"\r"` 字面量变了 | Python 解析源码时把 `\r\n` 收成 `\n`。失败 repr 显示 `b'\r'` 仍是 CR，比较的是 `patch_events_verify.py` 的字节 |
| 另有第四个哈希断言在本 run 失败 | FAILED 只有这三行。1194 passed |
| 本 head 又改了测或钉，所以和 SPEC 锚的 run 不是同一失败 | `git diff b9caf32 HEAD -- src tests .github` 为空。SPEC 写的 run `38208715004` / head `b9caf32` 与本 run 的挂点、两个 sha256、行号相同 |

## 6. 与 SPEC 对照

SPEC 状态：已锁。实现会话不得改那份锁。本页不改它。

### 6.1 SPEC 已覆盖（够按它拆票）

| SPEC | 本 RCA 的对应 |
|---|---|
| §1 问题：三条测把「工作区是 LF」写死 | 确认，并且给出字节证明 |
| §3.1 / G3 生产折行不动，钉字符串不动 | 确认应当不动。fold 与本轮 Windows 通过的旁证测一致 |
| §3.2 / G4 同一测在 CRLF 与 LF 工作区都绿，不按 `os.name` 分叉 | 修复方向已写清。LF 端本机已绿；CRLF 端仍是本 CI |
| §3.3 / G5 禁止 `assert b"\r" not in raw`；合成顺序是先 `\r\n`→`\n` 再 `\n`→`\r\n` | 这就是第 2、3 条的直接原因。顺序是为了避开下面的误修 |
| §3.4 / G6 禁止 `sha256(工作区原字节) == 钉`；改断言折行后的 `_verify_py_sha256()`；未折的 CRLF 字节不得等于钉 | 这就是第 1 条的直接原因 |
| §3.5–3.6 / G7、G8 τ 文本离开钉；仪器锁通过后仍走「正式冻结」、不调 NLI、`n_bad == 20` | 方向已写清。本 CI **没有执行到**这些断言 |
| §3.7 / G10 行为 diff 只在 `tests/unit/test_pe_sensitivity.py` | 与根因落点一致 |
| §4 禁止把 `cee71de30…` 写成新钉；禁止 `.gitattributes` / autocrlf / 强制 LF checkout | 与误修风险一致 |
| §7 拒过：改钉、改 τ/ρ、重跑 LIVE-2、升格激活、合 `#543`、恢复那两条断言、放宽 fold、用检出策略躲开 | 本 RCA 不放宽任何一条 |
| §8 下一跳 `/to-tickets` | 维持 |

### 6.2 SPEC 没写、本 RCA 补上的部分

这些是溯源和引理。**不构成 to-tickets 之前必须回改 SPEC 的行为缺口。** 票面引用本文件即可。已锁 SPEC 保持不动。

| 缺口 | 为什么不阻塞拆票 |
|---|---|
| SPEC 的 CI 锚是 run `38208715004` / head `b9caf32`。当前红的是 run `38210170555` / job `114682341989` / head `fd548ca` | 两 run 的失败字节与行号相同。`fd548ca` 只加了 SPEC。验收按测试名和 §3 行为，SPEC §8 已这样写 |
| SPEC 把 `cee71de30…` 标成「观测值，不是新钉」，没有证明它等于 `sha256(LF 字节的 \n→\r\n)` | §3 的修复不依赖这个十六进制。证明放在本页 §2，用来排除内容漂移和钉过时 |
| SPEC 写「Windows checkout」，没有点名 `core.autocrlf=true`、无 `.gitattributes`、`actions/checkout@v4` 未覆盖 | 修的是测试契约，不是检出配置。§5 / §7.9 已经禁止用检出策略代替测试修复 |
| 本轮失败停在前置断言，G7/G8 的后半段没有在 Windows 上跑到 | §3 已要求修完之后这些断言仍在，且两种换行都绿。票的验收不要把「未执行」写成「已证伪」 |
| CI 没有 Linux job。「LF 也绿」不是另一条 workflow | §4 已要求实现会话在 LF checkout 上跑同一 pytest。本页 §2.1 是分析时的 LF 证据，不是实现验收 |

## 7. 误修风险

优先顺序是「SPEC 已锁的改法」在前。下面每一条都是候选方向，**本页不实施**。

1. **按 SPEC 改测试（唯一建议实施的方向）。** 只动 `tests/unit/test_pe_sensitivity.py`。去掉工作区原字节对钉、去掉 `assert b"\r" not in raw`。CRLF 夹具走 `raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")`。内容未改时断言折行后 `_verify_py_sha256() == VERIFY_PY_SHA256`；合成出的 CRLF 原字节 sha256 不等于钉；τ 字面量 `ENTAILMENT_TAU = 0.5` → `0.4` 一次后，折行摘要离开钉；仪器锁通过后名单不符仍是「正式冻结」、不调用 NLI、must-carry 仍是 `n_bad == 20`。LF 与 CRLF 工作区走同一条路径。
2. **不要改 `VERIFY_PY_SHA256`。** 把它换成 `cee71de30…` 会把某一次 CRLF checkout 的观测焊进常量。LF 工作区会立刻红。钉的对象会从「仪器文件内容」变成「检出策略」。
3. **不要只删 `:232` 的 assert、留下 `replace(b"\n", b"\r\n")`。** 工作区已经是 CRLF 时，每个 `\r\n` 会变成 `\r\r\n`（本文件 4333 bytes，多出 106 个 CR）。生产 fold 只吃掉 `\r\n`，剩下的单独 `\r` 还在，折行结果仍是 CRLF 字节，sha256 仍是 `cee71de30…`，不等于钉。仪器锁继续失败。这会看起来像「fold 不够」，从而引诱把单独 `\r` 也折掉。
4. **不要放宽生产 fold。** 不要改回「哈希原字节」。不要把单独 `\r` 一并删掉。G3 要求只折 `\r\n`。本文件当前没有单独 `\r`；放宽 fold 会让非换行 CR 也被当成换行。
5. **不要用 `.gitattributes`、`core.autocrlf=false`、或 checkout 前改 git config 把 Windows 工作区改成 LF。** CI 可以因此变绿，但绿的原因是工作区又变回测试所假设的 LF，生产 fold 在真实 CRLF checkout 上不再被这三条打到。SPEC §7.9 把这条定为拒过。
6. **不要动 τ、ρ、`FORMAL_FREEZE_SHA256`、冻结 jsonl、代码内 `SENSITIVITY_SET_S`、LIVE-2 报告 / 分表 / run log、`activation_prerequisite_met`、`#538` 失败句、`#543`。** 本失败与这些字节无关。

## 8. 建议下一跳

```text
Matt /to-tickets → enrich → before-implement → /implement
```

不要跳过这条链直接改测试。`/before-implement` 仍用 SPEC §7 的拒过条件；本 RCA 是票的输入，不是实施授权。

拆票时建议写上的验收锚（都不新开行为）：

- 改动文件限于 `tests/unit/test_pe_sensitivity.py`（生产文件保持 `b9caf32` 的 fold 语义）。
- 三条测试名仍覆盖 G4–G8；允许 G9 合并，不允许丢掉「正文改动离开钉」和「正式冻结拒绝且不调 NLI」。
- 验收命令形状沿用 SPEC：`pytest tests/unit/test_pe_sensitivity.py -q`，在 LF 工作区与 Windows CI 的 CRLF 工作区都绿。
- `VERIFY_PY_SHA256` 仍是 `58bdae90199bfcb901cc22622e7ebeedfbe800bd208b60858febeab069739918`。`cee71de30…` 不进常量。
- 不重跑 LIVE-2。`activation_prerequisite_met` 保持否。
