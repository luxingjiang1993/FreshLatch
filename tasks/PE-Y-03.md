# PE-Y-03 · n=400 正式名单针

## Parent

规格卷 27 · ADR-0037 · PR [#493](https://github.com/luxingjiang1993/FreshLatch/pull/493)

## Destination

落实 `PREREG-Y` 配额：四层各 100（50/50），合计 400；pilot id 不进正式。写死 `SPLIT-pe-v2-route-y.json` 或显式复用 `SPLIT-pe-v2` 超集并登记针。

## Acceptance criteria

- [ ] Given 名单针已落盘，When 调用 formal-y 的 n=400 loader，Then 返回恰好 400 条互异 `claim_id`
- [ ] loader 结果与 pilot 名单无交集（单测）
- [ ] 层配额：数值/日期/条款替换/删除各 100，且层内正确/坏 = 50/50（余数规则）
- [ ] 若语料不够：记缺额并失败或显式「不可激活」，**不得**静默改小 `PREREG-Y` 配额表
- [ ] `python -m compileall -q src` 退出 0；相关 pytest 绿（可挂在 `test_pe_formal_y.py` 或 `test_pe_split_y.py`）

## Agent Guards

- **ID**: PE-Y-03
- **Title**: `feat(eval): pe_v2 路线 Y n=400 名单针`
- **Trust**: Watch
- **Blast**: none
- **Paths**:
  - `docs/evidence/patch-events/SPLIT-pe-v2-route-y.json`（new 或显式指针文件）
  - `src/freshlatch/eval/patch_events_formal_y.py`（loader 接线 · adapt）
  - `docs/evidence/patch-events/SPLIT-pe-v2.json`（只读来源）
  - `tests/unit/test_pe_split_y.py` 或扩 `test_pe_formal_y.py`（new）
- **Provenance**:
  - Kind: adapt
  - Source: `docs/evidence/patch-events/SPLIT-pe-v2.json`（仓内；n100 超集扩展）
  - Pin: 当前分支文件；实现时记录 blob sha256 到票 Evidence
  - What changed: 新增 n400（或等价键）划分；pilot 仍隔离；配额对齐 PREREG-Y
  - Why not copy as-is: 现 SPLIT 仅有 pilot/n30/n100，不够 Y 正式针
  - License note: 同仓数据
- **Tests**: added
- **Do-not-touch**: 旧 SPLIT 已发布键的既有语义（可追加不可改写 n100 成员若已冻结引用）；B/C 名单针；构造算子；`PREREG-Y` 配额表数字
- **Rollback**: 删除 route-y SPLIT；formal-y loader 回退到明确 NotImplemented

### Provenance status

- result: pass
- notes: adapt 仓内 SPLIT；无外链；实现时补 sha256 pin

### Evidence *(after Matt `/implement`)*

- typecheck:
- tests:
- paths:

## Blocked by

语料池须支撑 400+ 共形预留；不够则本票以「缺额不可激活」收口，不改预注册。建议在 PE-Y-01 loader 接口可读之后接线。

## Handoff

`enrich done | PE-Y-03 | ready | next: before-implement PE-Y-03`
