---
name: event_timeline
description: 事件时点主张的任务方法:把已签发的发布、监管口径、访谈改口等事件对照 T1 快照复验。本包不进入 Runner 默认技能注入,也不进入 Lead 系统提示。references 不随正文注入,由 load_skill_reference 按 skills/{slug}/references/{name}.md 只读。
metadata: 主题=事件时点;形态=未挂载业务包;注入=不进 Runner、不进 Lead 系统提示;工具投影=Lead 默认白名单;口径=T0/T1 快照取代,不是日历失效
---

# 事件时点主张

FreshLatch 的业务方法包,服务已签发主张里的事件:产品发布、监管口径、访谈改口、跟踪名单上的一次变化。本包停在磁盘,不进 Runner 默认注入,也不进 Lead 系统提示。对照的是 T1 快照里这件事是否仍被写成成立。

## 任务

把一条事件主张对照 T1 原文,得出三档之一:

- **fresh**:T1 原文仍把该事件写成成立,且支持主张的每个前提;
- **stale**:T1 原文明确写下该事件被撤回、被替代,或同一口径已经改口,从而推翻主张前提;
- **unknown**:T1 没有覆盖该事件,或只说未复测、不再列入跟踪、无新测量。

时点用快照 `as_of` 的 T0 与 T1。日历上的一天过去了,本身不构成推翻。

## 工作流

1. 用 `retrieve` 在 T1 检索该事件的原文段落;必要时 `read_source` 读全文。ground truth 是 T1 原文,不是 chunk。
2. 先确认事件身份:发布是否同一次,口径是否同一条,访谈是否同一场。对象不同的叙述不能互相推翻。
3. T1 仍支持该事件的前提 → `reverify_claim(claim_id, "fresh", [t1 evidence_id...])`。证据 id 逐字来自本会话 `retrieve`,并以 `@T1` 结尾。
4. T1 明确写下撤回、替代或改口 → `mark_stale(claim_id, reason, [t1 evidence_id...], dimension)`。reason 指出 T1 哪一句推翻了主张里的哪一个事件前提。dimension 填本反证攻击的维度。
5. T1 无覆盖,或只有缺口声明 → `mark_gap(description)` 后 `reverify_claim(claim_id, "unknown", [])`。
6. 要沿某一方向专找反证 → `spawn_critic(focus?)`。结论只作参考。
7. 完成或无路可走 → `finish_reverify()`。

## 教义:约束与纠正

约束的条目枚举唯一真相在代码(工具白名单 + 规则闸),本节只写约束的存在、理由与被拦后的正确动作;具体错误文案以工具层返回为准。

| 场景 | 原因 | 正确动作 |
|---|---|---|
| 用「日期已过」判定事件死亡 | 本期的过期指快照取代:T0 仍成立、T1 已改写或删除;不是日历失效日 | 回到 T1 原文找改写或删除句;没有则不要判 stale |
| T1 只说「未复测 / 不再列入跟踪 / 无新测量」 | 停追踪不是推翻;缺口声明不能写成因果句 | `mark_gap` 记录缺口,判 unknown |
| 用另一场访谈推翻这一场的原话 | 事件对象不同,不能并成同一前提 | 只引用同一事件的 T1 句子;对不上则 `mark_gap` |
| 想把 T0 的发布稿继续当成现在仍成立 | 签发时的快照只证明曾经为真 | 用 `retrieve` 取 T1;没有锚 T1 的 id 则不要判 fresh |
| `mark_stale` 的 reason 没有指出哪一句改口 | 有效反证要有显式因果句 | 回到 `read_source` 的 T1 原文,写明改口句与被推翻的前提 |

## 何时读 references

- `references/event-anchors.md`:怎样确认是同一事件,以及快照取代与缺口声明的差别。
