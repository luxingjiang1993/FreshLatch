---
name: patch_diff
description: patch diff 走查的任务方法:用 T1 原文核对已签发主张,并读 before_text 与 after_text 的行差。本包不进入 Runner 默认技能注入,也不进入 Lead 系统提示。references 不随正文注入,由 load_skill_reference 按 skills/{slug}/references/{name}.md 只读。scripts/line_delta.py 只计行差,不写事件账。
metadata: 主题=patch diff;形态=未挂载业务包;注入=不进 Runner、不进 Lead 系统提示;工具投影=Lead 默认白名单;账本=不写 patch_events
---

# patch diff 走查

FreshLatch 的业务方法包,服务已经放在人面前的正文差:before_text 是改前,after_text 是改后。本包停在磁盘,不进 Runner 默认注入,也不进 Lead 系统提示。走查回答的是「这处改字之后,主张还能否被 T1 原文复验」,不负责把草案写入事件账。

## 任务

给定一条主张,以及一对 before_text / after_text:

- 先看行差说明字面改了什么;
- 再把改后的前提交回 T1 原文,得出 fresh、stale、unknown 之一;
- 未确认的草案不进入正式事件账,也不能当成 T1 已经推翻原主张。

行差不是证据。证据仍是锚在 T1 的原文。

## 工作流

1. 读 before_text 与 after_text,分清哪些行只在改前、哪些行只在改后。磁盘上的 `scripts/line_delta.py` 只做这个计数,它不是白名单里的工具,也不写账。
2. 用 `retrieve` 在 T1 检索改后前提所在段落;chunk 不够时 `read_source` 读原文。
3. T1 原文支持改后仍要保持的每个前提 → `reverify_claim(claim_id, "fresh", [t1 evidence_id...])`。证据 id 逐字来自本会话 `retrieve`,并以 `@T1` 结尾。
4. T1 原文明确推翻其中某个前提 → `mark_stale(claim_id, reason, [t1 evidence_id...], dimension)`。reason 写的是 T1 的句子,不是 diff 本身。
5. T1 没有覆盖改后前提 → `mark_gap(description)` 后 `reverify_claim(claim_id, "unknown", [])`。
6. 需要专找反证 → `spawn_critic(focus?)`。结论只作参考。
7. 走查收口 → `finish_reverify()`。确认改稿、写入事件账不在本包的工具投影里。

## 教义:约束与纠正

约束的条目枚举唯一真相在代码(工具白名单 + 规则闸),本节只写约束的存在、理由与被拦后的正确动作;具体错误文案以工具层返回为准。

| 场景 | 原因 | 正确动作 |
|---|---|---|
| 把未确认草案的 after_text 当成已经推翻原主张 | 未确认草案不入账;字面改写不是 T1 原文 | 草案保持草案。推翻与否回到 `retrieve` / `read_source` 的 T1 句子 |
| 只凭行差就判 fresh | 行差说明改了哪些字,不提供锚 T1 的 evidence_id | 先取 T1 证据 id,再 `reverify_claim` |
| reason 只复述 after_text | 复验对象要能点回 T1;改后正文自己不能当自己的出处 | 引用 T1 的 evidence_id,写明哪一句支持或推翻哪个前提 |
| 想在走查里直接落账或放行 | 写事件账与放行不在本包投影的工具里;人确认才应用改稿 | 走完 `mark_gap` 或判定调用后 `finish_reverify`,把确认留给人 |
| diff 里出现了数字变化 | 数字变化仍要同科目对照 T1 原文,行差不算核对完成 | 按财报数字主张的同科目规则,用 T1 句子决定三档 |

## 何时读 references

- `references/diff-reading.md`:before_text / after_text 怎么读,以及行差与 T1 证据的分工。
