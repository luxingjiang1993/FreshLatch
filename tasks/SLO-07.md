# TASK / ticket — SLO-07

## Ticket
- **ID**: SLO-07
- **Title**: `feat(slo): 复验主业观测（D1 multi-run · D3=0 挂接 · D4 分布）`
- **Paths**: `docs/ops/生产补丁放行SLO.md`, `src/freshlatch/eval/`（multi-run 入口若需）, `src/freshlatch/disposition.py`, `reports/`, `data/eval/gold.json`（只读）

## What to build
(1) must_stale multi-run 跑法与「不得低于当前金标门」记录处（离线评测轨）；(2) D3 无 T1 绿灯=0 挂到 SLO-02 仪表；(3) 包结论三值分布周报。金标不得进生产 score / 在线放行。

## Blocked by
SLO-01, SLO-02

## Agent Guards
- **Blast**: api
- **Trust**: Watch
- **Acceptance**:
  - Given 离线 gold 评测入口, When 按文档跑 multi-run（n 与次数写死在命令/文档）, Then 产出 must_stale 命中汇总；文首标明离线评测层且 n 小时不报总体方差。
  - Given 生产放行/score 路径扫描说明, When 检查, Then 无读取 gold 标签作放行特征。
  - Given 一组 Run disposition, When 聚合 D4, Then 输出 可发/需补丁/勿发 计数或占比。
  - Given D3, When 对照 SLO-02 仪表, Then 无 T1 绿灯违例目标=0 可引用同一出口。
- **Provenance**:
  - Kind: adapt
  - Source: `src/freshlatch/eval/` · `data/eval/gold.json`（只读）· `src/freshlatch/disposition.py` · 立项切片北星句
  - What changed: multi-run/分布观测出口；不改金标
  - Why not copy as-is: 需对齐 D1/D4 与防火墙
- **Tests**: added
- **Do-not-touch**: 修改 gold 凑绿；金标进生产 score；RESULT-Y

### Provenance status
- result: pass
- notes: adapt eval/disposition；gold 只读

### Evidence *(after Matt /implement)*
- typecheck:
- tests:
- paths:

## Handoff
`2026-10-09 | SLO-07 | ready | blocked by SLO-01, SLO-02`
