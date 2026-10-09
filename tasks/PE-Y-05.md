# PE-Y-05 · 激活 PREREG-Y + 一次正式主跑 + RESULT-Y 抄表（Gate）

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493) · 前置 PE-Y-01…04

## Destination

人令齐备且 `GATE-Y-PROBE` 过门后：写激活批注 → 一次 `--authorize-send` → 同一次主比较抄入 RESULT-Y。不保证乙。禁止称甲。禁止改 B/C 归档。

## 人令闸（缺则停 · 禁止自批）

本票 **Blocked**，直至会话出现真人令原文（逐字）：

> 批准激活 PREREG-Y 并正式主跑一次。

探针令（「授权路线 Y 仓外探针发模型；不得激活。」）**不得**当作本票授权。

## Acceptance criteria

- [ ] Given 会话**无**正式人令，When 试图激活或 `--authorize-send`，Then 拒绝；`PREREG-Y` 保持未激活；成立格未填
- [ ] Given 正式人令 + `GATE-Y-PROBE` 真数据 `gate_passed=true`，When 执行本票，Then：文首已激活；激活批注含日期/仓库针/GATE-Y 路径；恰好一次写入 `formal-generations-y.jsonl`
- [ ] RESULT-Y 三行 false-accept 与 k 只抄同一次 `compare_primary`；分层按 PE-Y-04 口径；文面不得称甲
- [ ] 产物禁止写入 `formal-generations-b.jsonl` / `formal-generations-c.jsonl` / 旧 `formal-generations.jsonl`
- [ ] Evidence 三行齐：`python -m compileall -q src` · 相关 pytest · paths ok
- [ ] 未改 `PREREG-B`/`RESULT-B`/`formal-generations-b` 与 C 对应冻结页

## Agent Guards

- **ID**: PE-Y-05
- **Title**: `feat(eval): 激活 PREREG-Y 并正式主跑一次（Gate）`
- **Trust**: Gate
- **Blast**: eval（证据账 / 生成 jsonl）；非 auth/db/pay，但人令+正式发模型 → **Gate**
- **Paths**:
  - `docs/evidence/patch-events/PREREG-Y.md`（激活批注）
  - `docs/evidence/patch-events/RESULT-Y.md`（成立格）
  - `docs/evidence/patch-events/formal-generations-y.jsonl`（new）
  - `docs/evidence/patch-events/GATE-Y-PROBE.md`（只读过门依据）
  - `src/freshlatch/eval/patch_events_formal_y.py`
- **Provenance**:
  - Kind: adapt
  - Source: `patch_events_formal_b.py` 主跑/抄表流程 @ B tip；人令闸对标 `tasks/PE-C-04.md` 形态
  - Pin: `4ec045b96aa23a19acd2822accdac52658366958`
  - URL: https://github.com/luxingjiang1993/FreshLatch/blob/4ec045b96aa23a19acd2822accdac52658366958/src/freshlatch/eval/patch_events_formal_b.py
  - What changed: 激活对象/产物改 Y；分层走乙口径；门闩依据改 GATE-Y
  - Why not copy as-is: 求验乙非甲；n=400；禁升格 B 门闩
  - License note: 同仓
- **Tests**: updated（守卫+抄表回归；正式发模型不进 CI）
- **Do-not-touch**: B/C 归档成立格；甲定义；hard reject/绑定放宽；金标进 score；同页二跑；加 n；用探针令冒充本票
- **Rollback**: 若误激活且未主跑：撤激活批注回未激活；若已主跑：冻结为一次结果，禁止二跑「修正」

### Provenance status

- result: pass
- notes: adapt B 正式主跑流程；Gate 因人令+发模型；前置票未齐前不得开工

### Evidence *(after Matt `/implement`)*

- typecheck:
- tests:
- paths:

## Blocked by

- PE-Y-01…04 Acceptance 绿
- **PE-Y-CORPUS-01/#500 + PE-Y-CORPUS-02/#501** Acceptance 绿（正式 n=400 可加载；ADR-0038）
- `GATE-Y-PROBE` 真数据 `gate_passed=true`
- 会话出现正式人令原文

## Handoff

`enrich done | PE-Y-05 | blocked (Gate·人令·过门) | next: 勿 before-implement 直至闸齐`
