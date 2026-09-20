# §2 数据 schema 与语料清单

> 出处:#8(语料金标)、ADR-0003(chunk schema、SQLite)、切片 §6/§8。红线:只用合成材料,界面标注 synthetic;课题锁定,开工后禁止改。

## 2.1 T0 卷宗导入件 `data/t0_docket.json`(EvidenceOS 形状,不是 EvidenceOS 产品)

```json
{
  "question": "是否应该在未来 12 个月进入东南亚中小企业 AI 客服市场?",
  "claims": [
    {
      "claim_id": "c1",
      "statement": "竞品在该市场的客单价仍显著高于我们",
      "t0_evidence_ids": ["t0-competitor-notes#p2"]
    }
  ]
}
```

- 导入是 Workflow:只读 `statement` 与 `t0_evidence_ids`(可选 `t0_evidence`),不做新调查。
- demo 用此文件冒充「两周前的卷宗」,不依赖蓝海项目4 代码。

## 2.2 主张 schema(复验后,内存 + UI 渲染对象)

| 字段 | 类型 | 说明 |
|---|---|---|
| `claim_id` | str | c1–c12 |
| `statement` | str | 主张正文(Auditor/Agent 不得修改) |
| `t0_evidence_ids` | list[str] | T0 证据,`doc_id#anchor` |
| `t1_evidence_ids` | list[str] | T1 证据,**无则不得 fresh(闸强制)** |
| `status` | enum | `fresh` / `stale` / `unknown` / `void` |
| `last_confirmed_at` | str\|null | 续命时更新(W5 起) |
| `validity_basis` | {doc_id, checksum} | 续命写新的 T1 证据基础(W5 起) |

## 2.3 语料文档(双镜像目录)

- 形态:`data/corpus/t0/` + `data/corpus/t1/`,同 doc_id 一一对应;**目录本身就是 as_of 维度**,与检索层 `WHERE as_of=` 换源天然对齐;点回 = 读文件 + 找锚点。
- 文首元数据头(每篇):

```markdown
---
doc_id: t0-competitor-notes
as_of: T0
source_type: private
title: 竞品访谈笔记
checksum:            # 本期留空,三处留位之一
---
## p2
<正文段落……>
```

- 正文锚点:`## p2` 等条款级锚点;`evidence_id = doc_id#anchor`(如 `t0-competitor-notes#p2`)。
- 规模红线:12 主张 / T0+T1 各 12 篇(20–30 篇区间的拍板值)/ 4–6 篇 T1 被故意改掉 / ≥3 条 must_stale / 双向干扰项在位。
- 结构感知分块:按标题层级(条款)切块,**不按固定长度切**;切块必须确定(金标复现优先)。

## 2.4 金标 `data/eval/gold.json`(完整版定稿)

```json
{
  "question": "是否应该在未来 12 个月进入东南亚中小企业 AI 客服市场?",
  "must_stale":   ["c1", "c2", "c3", "c7"],
  "must_fresh":   ["c4", "c5", "c6", "c8"],
  "must_unknown": ["c9", "c10", "c11", "c12"],
  "must_quarantine": [],
  "causal_chain": {
    "c1": { "t1_doc": "…", "anchor": "…", "change": "…", "why_stale": "…" }
  },
  "meta": { "seed": null, "temperature": 0, "checksums": {}, "note": "W5–W8 填 seed/checksum" }
}
```

- `causal_chain`:每条 must_stale 附「T1 改了什么 → 为什么 stale」——人审逐条核对 = 确定性因果链验收;W4 有效反证判据的「对齐」锚(§7)。
- `must_quarantine`:本期空数组占位(W9–W12 记忆卫生金标位,结构先在场)。
- **金标不记 focus**(评测测判定正确性,不测 Lead 的调度品味;#14)。
- 复现字段三处留位、本期为空:① 文档元数据头 `checksum:`;② SQLite documents 表 checksum 列;③ `gold.meta.checksums`。`seed`/`temperature` 只出现在 `gold.meta` 与运行配置;语料冻结后进 git,改动走评审。

## 2.5 SQLite 表(ADR-0003 + #11)

| 表 | 关键列 | 说明 |
|---|---|---|
| `chunks` | `doc_id, chunk_id, clause_id, title, text, source_type, as_of, doc_version, checksum, tokens, parent_id(留位), hypo_questions(留位), vec(留位)` | chunk schema 定稿 13 列,3 列本期空 |
| `documents` | `doc_id, as_of, source_type, doc_version, checksum(留位)` | 文档级元数据 + checksum 列(三处留位之二) |
| `invalidation_list` | `claim_id, voided_at, actor, reason?` | **作废名单 = 单一真相**,随课题持久;Lead 上下文与规则闸都查这张表;W9 记忆模块读它,不复制 |
| `latch_log` | `ts, claim_id, action, evidence_id?, actor="human"` | 人审审计迹 + 用户作废率(在线指标)取数口 |
| `rerun_log`(T9 追加) | `ts, claim_id, thread_id, verdict, nth, note` | 重跑时间线取数(§5.3「结果挂该主张卡片时间线」);latch_log 装不下 verdict/nth/thread,单列展示层取数表,人审写路径唯一出口不变 |

- checkpointer 单独文件 `data/checkpoints.db`(SqliteSaver,W3 起);同一主张只保留最近 5 个 thread 的 checkpoint,业务侧定期删行。

## 2.6 12 主张清单定稿(#8 §4)

| # | 主张(大意) | 维度 | 金标 | T1 改动 |
|---|---|---|---|---|
| c1 | 竞品客单价仍显著高于我们 | 竞品价格 | must_stale | 竞品降价至我们 70% |
| c2 | 监管暂无数据本地化强制要求 | 监管口径 | must_stale | 印尼/泰国新规 |
| c3 | 渠道伙伴接受 X% 分成 | 访谈改口 | must_stale | 伙伴改口 |
| c4 | 目标市场 ≥N 万家中小企业 | 市场结构 | must_fresh | 普查仍支持 |
| c5 | 单会话成本仍低于竞品 | 成本模型 | must_fresh | 仍支持 |
| c6 | 竞品发「市场亏损」新闻稿,窗口打开 | 干扰·看似死其实活 | must_fresh | 新闻属实但与客单价无因果 |
| c7 | T1 报道仍引用旧价格,优势仍在 | 干扰·看似活其实死 | must_stale | 报道滞后,官网新价已变 |
| c8 | 本地语言小模型生态不成熟,需全自研 | 技术生态 | must_fresh | 仍不成熟 |
| c9–c12 | T1 无原文覆盖的主张 ×4 | 缺口演练 | must_unknown | 无 T1 源 |

配比:4 must_stale(3 直球 + 1 看似活其实死)/ 4 must_fresh(含 1 看似死其实活)/ 4 must_unknown。六个维度与 focus 词表同构(§3.4)。

## 2.7 语料生产方式与三道验收(#8 决策五)

- **AFK 起草 + 人审**:agent 按 §2.6 清单起草;**出题人不得兼阅卷人**——起草是 agent,验收是人,基线模型是第三者。
- 验收三道(全收):
  1. **因果链人审**:每条 must_stale/must_fresh 按 `causal_chain` 表逐条点回 T1 原文,确认「改动真实存在、且确实导致 stale」;
  2. **假绿对照预演**:同模型无工具只读 T0 摘要,必须对 c1/c2/c3/c7 判「成立」——预演不过 = 干扰项埋得不够像,回炉;
  3. **金标驱动闸单测**:gold.json 直接喂 `gates/rule_gate.py` 单测(无 T1 不得 fresh、stale 不得绿灯),进 `tests/eval/`。
- **语料冻结纪律**:定稿后不再改,改动走评审。

## 2.8 上下文装配(Lead 短期记忆边界)

Lead 上下文只装:主张列表 + 最近检索块 + 作废名单 + 隔离名单。**不装全部语料**(切片 §8)。循环内 messages 单角色内只增不减(轨迹完整可回放);**不做上下文压缩**(证据完整性优先于 token,18 圈封顶用不上);本期循环不接记忆写入(跨主张长期记忆留位,W9–W12)。
