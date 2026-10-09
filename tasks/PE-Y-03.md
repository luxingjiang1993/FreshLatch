# PE-Y-03 · n=400 正式名单针

## Parent

规格卷 27 · ADR-0037 · PR #493

## Destination

落实 `PREREG-Y` 配额：四层各 100（50/50），合计 400；pilot id 不进正式。写死 `SPLIT-pe-v2-route-y.json` 或显式复用 `SPLIT-pe-v2` 超集并登记针。

## Acceptance criteria

- [ ] loader 返回恰好 400 条互异 `claim_id`
- [ ] 与 pilot 名单无交集
- [ ] 层配额符合余数规则；缺额可记账、不在本票改小配额
- [ ] formal-y 名单入口调用本针；pytest 绿

## Agent Guards

- **ID**: PE-Y-03 · **Trust**: Watch · **Blast**: none  
- **Paths**: `docs/evidence/patch-events/SPLIT-pe-v2-route-y.json`（或登记复用路径）；`patch_events_formal_y` loader  
- **Do-not-touch**: 旧 SPLIT 已冻结行语义；B/C 名单针；构造算子  

## Blocked by

语料池须够 400+预留；不够则记缺额并停激活，不改预注册配额。
