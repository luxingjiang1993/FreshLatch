# TASK / ticket — ALT-05

## Ticket
- **ID**: ALT-05
- **Title**: `feat(eval): 授权后小 n 真数据旁路写入 patch-events-alt`
- **Paths**:
  - 扩展 `src/freshlatch/eval/patch_events_alt.py`（或薄 CLI `scripts/`）
  - 写入仅限 `docs/evidence/patch-events-alt/`（如 `probe-generations.jsonl`）
  - 单测：默认路径不发网络；授权旗标未开则拒绝发送
- **Executor**: `/implement`（**Gate**；默认零发送）
- **先读**: PROBE-LOCK；规格 ALT-05；云端默认不发模型纪律

未获 Oriental Ronin / Ronin 代理人**明文授权**前：本票可合入「默认不发」骨架，但不得实发模型、不得把读数当甲。

## 行为

1. 提供旁路写入入口：只写 `docs/evidence/patch-events-alt/`。
2. 默认（无 `--formal`/无授权环境变量/无明文旗标——实现选一并写死）：不调用付费 API。
3. 授权后小 n：层身份冒烟；不报方差充总体；不写主 RESULT。
4. 禁止打开旧 PREREG / 主 RESULT 作写。

## Agent Guards
- **Blast**: none（若实发模型则仍不改 production db/auth；但 Trust=Gate）
- **Trust**: Gate
- **Acceptance**:
  1. Given 默认旗标关闭，When 跑入口，Then 零网络/零密钥读取成功路径；单测可证明 generator 未被调用。
  2. Given 目标写路径，When 解析输出目录，Then 位于 `docs/evidence/patch-events-alt/` 下。
  3. Given 试图写入 `docs/evidence/patch-events/RESULT.md`，When 调用，Then 拒绝。
  4. Given 无明文授权记录，When PR/证据文首，Then 不得声称已完成真数据可分开。
- **Provenance**:
  - Kind: adapt
  - Source: `patch_events_formal.py` 默认不发模式（只读参考）
  - What changed: alt 目录写入与授权门闩
  - Why not copy as-is: 不得进主 formal 文件
- **Tests**: added
- **Do-not-touch**: 主 formal-generations.jsonl 既有行；主 RESULT；未授权实发

### Provenance status
- result: pass
- notes: Gate；人授前只许骨架。

### Evidence *(after Matt `/implement`)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-08 | ALT-05 | gate | 须明文授权才实发；/before-implement ALT-05 时核对 Gate`

## Blocked by
ALT-01；明文授权（实发部分）

## GitHub
- Issue: #454
