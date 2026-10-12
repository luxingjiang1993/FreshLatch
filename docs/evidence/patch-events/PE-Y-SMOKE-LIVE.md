# PE-Y-SMOKE-LIVE

日期：2026-10-12 15:15:24 +0800（探针）· 本页首版同日（Asia/Shanghai · UTC+8）
票：PE-Y-SMOKE-LIVE · GitHub #550
父图：#517
Depends-on：#549 合入 `2b7401ad2257f9c5d42311ca9d7635c5ef951909`
Trust：L1
Blast：none（本票只新建本页；未改生产码）

- run_kind: live
- 授权指针: `docs/evidence/patch-events/SENS-LIVE-2-ACTIVATION.md`
  · ACTIVATION 合入: `2b7401ad2257f9c5d42311ca9d7635c5ef951909`
- LIVE-2: `docs/evidence/patch-events/SENS-LIVE-2.md`
  · commit `c4b921aa7559b672f657c3ccdc44c0b7913c9224`
  · blob `9671b009ce1f3591fe4fc26da003e2fa8774301c`
- 冻结 S sha256: `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19`
- sensitivity_passed: 是（引用 LIVE-2；本页不重判）
- gate_passed: 否（冒烟不假装 gate 已过）
- smoke_passed: 否
- 层身份: outcome-neutral · ≠ gate_passed · ≠ 乙成立 · ≠ 开 PE-Y-05

本页是新建证据。历史页 `docs/evidence/patch-events/SMOKE-Y-N30.md` 不升格为本票过线。

## 判据锁（先于本 PR 的 CI 结果）

`smoke_passed=是` 当且仅当下面两条同时成立。本段写在观察本 PR Windows CI 之前。

- **(A)** 本 PR head 上 workflow `ci`（`.github/workflows/ci.yml`）的 `windows-latest` job：`ruff check` 与 `python -m pytest tests/ -q` 都成功。本地 Linux 预检不能代替这一条。
- **(B)** `PYTHONPATH=src python -m freshlatch.eval.patch_events_smoke_y`（`smoke_n=30`）exit 0，且可复核 `collapse=false`、`score_hygiene.ok=true`、`constitutes_gate_passed=False`。

当前观察：(B) 成立，(A) 尚未在本 PR 上终态。所以 `smoke_passed=否`。判据不随后续结果改写。若随后 (A) 成立，只回填本节之下的「(A) 回填」与页首 `smoke_passed`，并在那时给 #517 发 Decisions 一行。若 (A) 失败，页首保持否，走下面的回滚，不改 τ/ρ，不改生产码。

## 1. 前置核对（main @ `2b7401ad2257f9c5d42311ca9d7635c5ef951909`）

工作分支从 `origin/main` 的该提交切开。本地旧 `main`（`8885cce7f0889676de11a7d1685436baedf6d554`）不含激活页，不作为本票基线。

| 项 | 核对 |
|---|---|
| `activation_prerequisite_met=是` | `SENS-LIVE-2-ACTIVATION.md` 页首有此句 |
| 下一步允许 SMOKE-LIVE=是 | 同页：「下一步允许：SMOKE-LIVE = 是」 |
| 授权人 / 时间 | Oriental Ronin · 2026-10-12 14:46:42 +0800 |
| LIVE-2 commit | `c4b921aa7559b672f657c3ccdc44c0b7913c9224` 存在 |
| LIVE-2 blob | `git rev-parse c4b921aa7559b672f657c3ccdc44c0b7913c9224:docs/evidence/patch-events/SENS-LIVE-2.md` = `9671b009ce1f3591fe4fc26da003e2fa8774301c` |
| 激活提交对 LIVE-2 的增量 | `2b7401ad` 只追加「§9 人审节」，跑时句 `activation_prerequisite_met：否` 仍在 `c4b921aa` 正文里。本页仍认上述 commit / blob |
| 冻结 S | 26 条 `record_type=sample`。按 `SENS-S-FREEZE-PROTOCOL.md` §7（`ensure_ascii=false`、`sort_keys=true`、分隔符 `(',', ':')`，不含 header）现算 sha256 = `e1899872c8a6748de81d87b8c5b89c931d33d13fdd50109ad4694371258ced19` |
| sensitivity_passed | 是（LIVE-2 / ACTIVATION 引用；本页不重判） |
| gate_passed | 否 |
| 不认 | stub 激活、口头激活、旧 #507 |

冻结 jsonl 字节未改。τ、`ENTAILMENT_TAU`、ρ、ADR-0040 未改。

## 2. (A) CI / pytest

对齐 `.github/workflows/ci.yml`：

- runner：`windows-latest`
- Python：`3.11`
- Lint：`ruff check`
- Test：`python -m pytest tests/ -q`（`PYTHONIOENCODING=utf-8`）

**(A) 现状：未成立。** 本页首版提交时，本 PR 上还没有终态的 `windows-latest` 结果。因此不能写 `smoke_passed=是`。

### (A) 回填

（空。等本 PR head 的 `ci` 终态后，只在这里补 run URL、结论、head SHA。未回填前 (A) 保持未成立。）

### 本地预检（Linux · 不能充当 (A)）

环境：Linux · CPython 3.12.3。与 CI 的 `windows-latest` + Python 3.11 不是同一条 soak。

| 命令 | exit | 摘录 |
|---|---:|---|
| `ruff check` | 0 | `All checks passed!`（ruff 0.15.0） |
| `PYTHONPATH=src python -m pytest tests/unit/test_pe_smoke_y.py -q` | 0 | `10 passed in 7.99s` |

未改测试，未改生产码。全量 `pytest tests/ -q` 的 Windows 结果只认上面的 (A) 回填。

激活合入当时的历史 CI（`https://github.com/luxingjiang1993/FreshLatch/actions/runs/38215440566`，head `2b7401ad2257f9c5d42311ca9d7635c5ef951909`，conclusion `success`）只说明该提交当时的 `ci` 为绿。它不是本 PR 的 soak，不计入本页 (A)。

## 3. (B) live 探针

- 命令: `PYTHONPATH=src python -m freshlatch.eval.patch_events_smoke_y`
- 时刻: 2026-10-12 15:15:24 +0800（UTC `2026-10-12T07:15:24Z`）
- smoke_n: 30（合成三臂；非正式 n=400）
- exit: 0
- stdout:

```text
k=16 direction=positive collapse=False stop=False score_hygiene_ok=True gate_passed=False
wrote /workspace/docs/evidence/patch-events/SMOKE-Y-N30.md
```

- stderr: 空

入口 `src/freshlatch/eval/patch_events_smoke_y.py` 的摘要行把 `analysis["score_hygiene"]["ok"]` 印成 `score_hygiene_ok`，把 `analysis["constitutes_gate_passed"]` 印成 `gate_passed`。这行里的 `gate_passed=False` 是冒烟防火墙字段，等于 `constitutes_gate_passed=False`。它不把 LIVE-2 / 本页的 `gate_passed` 改成是。

同一分析对象的只读摘录（不写仓内文件；exit 0）：

```text
PYTHONPATH=src python -c 'from freshlatch.eval.patch_events_smoke_y import analyze_smoke, build_synthetic_smoke_rows, smoke_n; a=analyze_smoke(build_synthetic_smoke_rows(n=smoke_n(), collapse=False)); print("smoke_n="+str(a["n"])); print("collapse="+str(a["collapse"]).lower()); print("score_hygiene.ok="+str(a["score_hygiene"]["ok"]).lower()); print("constitutes_gate_passed="+str(a["constitutes_gate_passed"]))'
```

```text
smoke_n=30
collapse=false
score_hygiene.ok=true
constitutes_gate_passed=False
```

| 票面字段 | 本跑 |
|---|---|
| collapse | false |
| score_hygiene.ok | true |
| constitutes_gate_passed | False |
| smoke_n | 30 |

**(B) 成立。** 未跑 n=400，未跑 formal-y，未开 GATE-Y 真探针。

## 4. 历史 `SMOKE-Y-N30.md`（不升格）

上述 CLI 的默认路径会覆盖 `docs/evidence/patch-events/SMOKE-Y-N30.md`。覆盖内容相对跑前历史页有两处不同：代码针写成 `local`；T−C 点估计从 `0.375` 写成 `0.4375`。本票的过线 bar 不含该点估计。本票禁止用这次覆盖充当过线。

写盘后已还原。还原后 blob 与跑前相同：`49edaabf2eb238559d752c32af2deaf63f0994e0`。本页结论只认 §3 的 stdout 与只读摘录。

## 5. 失败回滚（smoke_passed=否）

原因：(A) 未在本 PR 的 `windows-latest` 上观察到 `ruff check` 与 `pytest tests/ -q` 全绿。(B) 已成立。这不是探针三项失败，也不是放宽 τ/ρ 的理由。

- 不改 τ，不改 `ENTAILMENT_TAU`，不改 ρ，不改 ADR-0040，不改冻结 S 字节，不改生产码。
- 回到激活态：`SENS-LIVE-2-ACTIVATION.md` 仍然有效（`activation_prerequisite_met=是`）。
- 不晋级 GATE。不开 GATE-Y 真探针，不开 PE-Y-05，不开 n=400。
- 不复活 #507。
- 不把本页写成 `gate_passed=是`，不写成乙成立。
- #517 Decisions 在 (A) 终态并回填之后发一行。终态若仍是失败，该行写 `smoke_passed=否` 与本原因。

## 6. 边界

- Trust L1。Blast none。
- 过烟（若日后回填为是）仍 ≠ 乙成立，≠ 自动 `gate_passed`，≠ 自动开 GATE / PE-Y-05。
- 本阶段不估 δ，不跑 discordant，不锁正式冲乙页。
- 下一步在 `smoke_passed=是` 之后才允许另票谈人授 GATE-Y。本页当前为否，该另票未开。
