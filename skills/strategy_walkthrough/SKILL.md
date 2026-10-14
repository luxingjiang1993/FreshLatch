---
name: strategy_walkthrough
description: 策略 walkthrough 的任务方法:按发前顺序走查已签发的顾问或战略主张是否仍被 T1 原文支持。本包不进入 Runner 默认技能注入,也不进入 Lead 系统提示。references 不随正文注入,由 load_skill_reference 按 skills/{slug}/references/{name}.md 只读。
metadata: 主题=策略走查;形态=未挂载业务包;注入=不进 Runner、不进 Lead 系统提示;垂直=顾问报告;输出=三档判定,不另写商业裁决
---

# 策略 walkthrough

FreshLatch 的业务方法包,服务顾问报告与战略类已签发主张的发前走查。近端垂直是顾问报告:样例语料是公开洞察的主张与摘录,不是另开一套研报产品。本包停在磁盘,不进 Runner 默认注入,也不进 Lead 系统提示。

## 任务

按固定顺序走查一条战略主张,并把结论落在既有三档:

- **fresh**:T1 原文仍支持主张的每个前提;
- **stale**:T1 原文明确推翻某个前提;
- **unknown**:T1 无覆盖,或证据不足以支撑任一档。

走查不产出「建议进入 / 不进入」。包级可发、需补丁、勿发由产品聚合,不在本包另起状态名。

## 工作流

1. 读已签发主张原文,拆出前提。市场窗口、成本、竞品定价、监管口径分开,不并成一句。
2. 用 `retrieve` 在 T1 检索同维段落。命中上的 bm25、dense、rrf、rerank 分只是检索观察,不决定三档。chunk 不足时 `read_source` 读原文。
3. 每个前提都能在 T1 原文找到对应表述 → `reverify_claim(claim_id, "fresh", [t1 evidence_id...])`。证据 id 逐字来自本会话 `retrieve`,并以 `@T1` 结尾。
4. 某一前提被 T1 同维句子明确推翻 → `mark_stale(claim_id, reason, [t1 evidence_id...], dimension)`。reason 写明哪一句推翻哪个前提。
5. 有前提在 T1 悬空 → `mark_gap(description)` 后 `reverify_claim(claim_id, "unknown", [])`。
6. 要对「窗口已死」加压 → `spawn_critic(focus?)`。旁近句子(定价写成窗口、成本写成格局)只作干扰项核对,不直接镜像成判定。
7. 走查结束 → `finish_reverify()`。

## 教义:约束与纠正

约束的条目枚举唯一真相在代码(工具白名单 + 规则闸),本节只写约束的存在、理由与被拦后的正确动作;具体错误文案以工具层返回为准。

| 场景 | 原因 | 正确动作 |
|---|---|---|
| 走查末尾想写「建议进入」或「建议不进入」 | 客户向备忘不含商业裁决;本包只复验已签发前提 | 停在 fresh / stale / unknown 与证据 id,不追加进入与否 |
| 用竞品降价推翻「市场窗口已打开」 | 定价动作与窗口前提不同维 | 回到 T1 找窗口同维句子;没有则 `mark_gap`,不要 `mark_stale` |
| 检索分很高就想判 fresh | bm25、dense、rrf、rerank 不是判定阈值 | 只看 T1 原文是否支持每个前提,再调用 `reverify_claim` |
| 一个前提有 T1 句子、另一个没有 | 一个前提悬空就不够格 fresh | 对悬空前提 `mark_gap`,整条判 unknown |
| 想改主张正文来让走查变绿 | 走查对象是已签发原文;改稿由人确认 | `finish_reverify`,不在本包里改写主张 |

## 何时读 references

- `references/walk-order.md`:发前走查的顺序,以及走查结果与包结论的分界。
