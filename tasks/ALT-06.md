# TASK / ticket — ALT-06

## Ticket
- **ID**: ALT-06
- **Title**: `docs(grilling): 平行轨升级/放弃决议（是否另开 PREREG-ALT）`
- **Paths**:
  - 决议后可能新增 `docs/evidence/patch-events-alt/PREREG-ALT.md`（仅可分开档）
  - 或技术报告落 `docs/evidence/patch-events-alt/` / `docs/research/`
  - 更新地图 #434 Decisions-so-far
- **Executor**: wayfinder grilling（**不**走业务 `/implement`）
- **先读**: PROBE-LOCK 升级闸；ALT-02/05 读数（若有）；ADR-0035

根据预锁三档拍板：可分开 → 允许另开主论文级新预注册文件（不自动激活、不取代冲甲页）；分不开 / 不值得升级 → 报告或放弃。禁止见结果后改闸。

## 行为

1. 汇总夹具（及授权小 n）读数相对升级闸。
2. 拍板一档并落四件套（若新开预注册则评估+ADR 条件再判）。
3. 不得改主 `compare_primary` / 冲甲页 / 旧 PREREG。

## Agent Guards
- **Blast**: none
- **Trust**: Gate（决议）
- **Acceptance**:
  1. Given 探针读数，When 对照 PROBE-LOCK 三档，Then 决议评论写明档位与处置。
  2. Given 可分开，When 开新预注册，Then 新文件路径不在旧 `PREREG.md`，且声明不取代冲甲页、不填主 RESULT。
  3. Given 分不开或不值得升级，When 关单，Then 有技术报告或放弃声明；未放宽升级闸。
- **Provenance**:
  - Kind: new
  - Source: ADR-0035；PROBE-LOCK
- **Tests**: waived（决议票）
- **Do-not-touch**: 主链预注册成立定义；见结果改闸

### Provenance status
- result: pass
- notes: 决议票；非代码 implement。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a
- tests: n/a
- paths:

## Handoff
`2026-10-08 | ALT-06 | ready-for-human | 待 ALT-02（及可选 ALT-05）读数后开 grilling`

## Blocked by
ALT-02；可选 ALT-05（若要用真数据档）

## GitHub
- Issue: #455
