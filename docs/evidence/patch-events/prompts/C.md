# C

状态：可发送的提示词正文。补定，2026-10-08。不是预注册原文。这一份不与 T、B1、B2 共用。

## 已定

- 做法：无证据改写。
- 证据：提示词里不放 evidence。
- 输出：纯文本 after_text。
- 不要求模型输出 JSON 或 diff。
- 不设专门失败令牌。
- 不让模型打分。

## 指示正文

补定，2026-10-08。不是预注册原文。
before_text 写进 C、T、B1 和 B2 的 claim 提示词。
补定，2026-10-09。不是预注册原文。
根据下面给出的 before_text，改写一句纯文本。
C 的提示词里不放 evidence。
模型输出是纯文本。
生成模型只读 DEFAULT_MODEL。
温度只读 default_llm.temperature：0
