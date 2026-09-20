# ADR-0010: Stale 路径双人防线与维度异议闸不变量

- **状态**: Accepted(2026-09-21,工单 #24 拍板;判定人将重开方向决策权委托「按 Anthropic
  工程师标准拍板」,owner 指令闭环)
- **修订关系**: **修订 ADR-0009 子决策 2(stale 路径不在场条款)**;ADR-0009 其余条款
  (双判一致 3×3、fresh 路径在场机制、异议记录、MCP 显式不做)一律不动,继续有效。
- **相关**: 工单 #24 评估见 `docs/research/stale路径双人防线重开设计评估.md`;
  #21 行为验收 0/6(commit d4db693);#19 `docs/research/c5c6工程债处置设计评估.md`;
  #20 `docs/research/Auditor形态设计评估.md`;不变量先例 ADR-0008;在场机制先例 ADR-0009。

## 背景

#19 的人格/注入修复 bundle 经 #21 行为验收 0/6,按 pre-registered 锁死判别「人格层修复
判失效,重开方向」。失效形态:模型把 39 美元/月/店门售价等同为单会话服务成本的市场对标,
**并主动申明「该反证与主张的度量维度一致」**——自觉申明这一层整体被证不可托底。代码态
事实:`_t_mark_stale` 受理即落档,是主链上唯一零反对派的决策点(fresh 路径已有
critic checkpoint + 双判);注入 note 在落档后的回执才到场;ADR-0009 子决策 2「stale
路径不强制」的层数前提(#19 健在)已被 0/6 击穿,只剩 HumanLatch 一层,且收到的是无异议
自信红卡。c2 定性「自信地错恰是派驻最不会触发的时刻」对该路径逐字适用。

## 决议

### 1. stale 路径 Auditor 强制在场(自动触发)

`_t_mark_stale` 受理(三重硬校验通过、落档之前)自动触发 Auditor 单轮 structured-output
判定,输入 = 主张签发原文 + Lead 的 stale 包(reason + evidence_ids),输出 =
{verdict, dimension_match, 理由}。与 `_auto_critic_checkpoint` 同点同构:强制性住在
触发器,不住在错误信息。Auditor 形态/SOP/注入复用 #20 既定决议,本 ADR 零新造轮子。
Auditor 缺席不构成任何落档:hook 自动触发保证在场,闸前置校验 fail-closed 兜底。

### 2. 规则闸不变量 7:维度异议打回 stale

`dimension_match=False` 时规则闸打回 stale(error_code 登记),路由 **unknown + 异议
记录**挂复验单主张卡片,随黄卡进 HumanLatch。语义判断全部住在 Auditor(角色层),闸只
机械消费结构化 flag——与不变量 6(元陈述闸,判定引擎单一真相住 meta_gate)同构,
「闸管不变量,人格管语义质量」的分工不破。

### 3. mark_stale 路径真值表(与 ADR-0009 3×3 互补,不冲突;0009 的表管 fresh 请求)

| Lead mark_stale 反证包 | Auditor 判定 | 落档 |
|---|---|---|
| 反证成立、维度相符 | uphold | **stale**(照旧,零变化) |
| 反证维度不符 | dimension_mismatch | **unknown + 异议记录**(打回) |

**Auditor 无任何路径把任何状态改绿**(词表「不得拥有放行权」在此表现为:对假 stale 的
最大权力是降级 unknown;fresh 仍唯一经由 Lead 复验 + 双判一致)。Lead 被异议打回后须
回到 T1 做同维度复验再走 `reverify_claim(fresh)`,不得由 Auditor 代劳。

## 后果

- 词表:无新增术语;**规则闸** 词条不变量清单 touch-up 增第 7 条指针(评估文档 §4.7)。
- 机制实装并入 #22 窗口(auditor.py 与 fresh 路径触发的增量);#22 的 pre-registered
  判据一字不动;本决议行为验收独立触发(#25),不攒批。
- 验收 pre-registration 随本 ADR 锁定(评估文档 §4.6):通过线① c5/c6 ≥4/6 遍「非 stale
  落档」(定向线);② must_stale 4 条各 3/3 落 stale(回归守线);③ 无双判一致的 fresh
  落档(违例级一票否决);①未达成 → 停止同仪器第三次重试,重开 grilling 评估「独立标注源
  机器跨检」候选。本修复**不背负** c5/c6 ≥2/3 fresh 金标线(防 HARKing,理由见评估文档)。
- MARK_STALE_DIMENSION_NOTE 保留为教义表兜底,其在场时点(落档后回执)如实登记。
- **事后修改本 ADR 的不变量(撤销 stale 路径在场、放宽维度异议打回)等于在保留
  「双人在场已验」叙事的前提下拆 fake-stale 方向的第二判,W5–W8 及后续窗口的实验意义
  随之作废——修改必须走新评审工单并明示受影响窗口**(与 ADR-0009 后果条款同构)。
- 若「独立标注源机器跨检」(主张签发登记维度 + 反证强制维度字段 + 闸跨检)日后复活
  机器闸③的诚实形态,按 #19 pre-registered 条款须当场补 ADR。
