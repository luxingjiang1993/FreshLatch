# 检索陷阱三类（与主金标分列）

本页只报告陷阱子集,不顶替主张 must_* ,也不计入主指标 n。语料在 data/traps,不改论文语料 data/corpus。冒烟级,不声称统计显著。

## 快照取代 · trap-supersede-1

- query: 席位标价
- as_of: T1
- 相关 evidence_id: trap-supersede#p1@T1
- 干扰 evidence_id: trap-supersede#p1@T0
- 评测意图: 相关块是 T1 已改写的标价;T0 旧标价是干扰,不是当前快照。
- Recall@10（陷阱子集）: 1.0000
- 命中序: trap-supersede#p1@T1, trap-supersede#p2@T1, trap-meta#p2@T1, trap-conflict#p1@T1, trap-conflict#p2@T1, trap-conflict#p3@T1, trap-meta#p1@T1

## 同快照冲突 · trap-conflict-1

- query: 席位上限
- as_of: T1
- 相关 evidence_id: trap-conflict#p1@T1, trap-conflict#p2@T1
- 干扰 evidence_id: trap-conflict#p3@T1
- 评测意图: 同一 T1 快照内两条上限互相冲突,两条都标为相关;无关旁注是干扰。
- Recall@10（陷阱子集）: 1.0000
- 命中序: trap-conflict#p1@T1, trap-conflict#p2@T1, trap-conflict#p3@T1, trap-meta#p2@T1, trap-supersede#p1@T1, trap-meta#p1@T1

## 元陈述 · trap-meta-1

- query: 席位月费实测
- as_of: T1
- 相关 evidence_id: trap-meta#p2@T1
- 干扰 evidence_id: trap-meta#p1@T1
- 评测意图: 元陈述块只作干扰,不标成必须当反证命中。
- Recall@10（陷阱子集）: 1.0000
- 命中序: trap-meta#p2@T1, trap-meta#p1@T1, trap-conflict#p1@T1, trap-conflict#p2@T1, trap-conflict#p3@T1, trap-supersede#p1@T1
