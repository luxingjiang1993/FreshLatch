---
name: earnings_figures
description: 财报数字主张的任务方法:把已签发的收入、毛利、客单价等数字对照 T1 原文复验。本包不进入 Runner 默认技能注入,也不进入 Lead 系统提示。references 不随正文注入,由 load_skill_reference 按 skills/{slug}/references/{name}.md 只读。
metadata: 主题=财报数字;形态=未挂载业务包;注入=不进 Runner、不进 Lead 系统提示;工具投影=Lead 默认白名单;口径=同科目数字须点回 T1 原文
---

# 财报数字主张

FreshLatch 的业务方法包,服务已签发主张里的财报数字:收入、毛利、客单价、席位价。本包停在磁盘,不进 Runner 默认注入,也不进 Lead 系统提示。判定仍走既有复验链;本文件只写这类主张怎么对照 T1 原文。

## 任务

把一条含财报数字的主张对照 T1 原文,得出三档之一:

- **fresh**:T1 原文对同一科目、同一口径写出与主张相同的数字;
- **stale**:T1 原文对同一科目、同一口径写出不同数字,并因此推翻主张里的该前提;
- **unknown**:T1 没有该科目,或只说未更新、无新数据、未入账。

数字以 T1 原文句子为准。本包不另设通过线,也不把检索分当成数字是否成立的依据。

## 工作流

1. 用 `retrieve` 在 T1 检索该科目所在段落。chunk 里看不到完整数字时,用 `read_source` 读原文。ground truth 是原文,不是 chunk。
2. 核对科目是否同一维:收入不是毛利,客单价不是成本,席位价不是续约率。维度不符的句子不能当该数字的支持或反证。
3. T1 同一科目写出相同数字 → `reverify_claim(claim_id, "fresh", [t1 evidence_id...])`。evidence_id 逐字来自本会话 `retrieve`,并以 `@T1` 结尾。
4. T1 同一科目写出不同数字,且该句推翻主张前提 → `mark_stale(claim_id, reason, [t1 evidence_id...], dimension)`。reason 写明 T1 哪一句、哪个科目、哪个数字推翻了主张里的哪个数字。
5. T1 没有该科目,或只声明缺口 → `mark_gap(description)` 后 `reverify_claim(claim_id, "unknown", [])`。
6. 需要专找「这个数字已经死了」的反证 → `spawn_critic(focus?)`。Critic 结论只作参考,判定仍由复验主链落下。
7. 完成或无路可走 → `finish_reverify()`。

## 教义:约束与纠正

约束的条目枚举唯一真相在代码(工具白名单 + 规则闸),本节只写约束的存在、理由与被拦后的正确动作;具体错误文案以工具层返回为准。

| 场景 | 原因 | 正确动作 |
|---|---|---|
| 主张写着收入,T1 只有毛利或成本句 | 科目不同维;毛利健康不能证明收入数字仍在 | 回到 T1 找同一科目;找不到则 `mark_gap` 后判 unknown |
| T1 写「未更新 / 无新数据 / 未入账」 | 缺口不是推翻;过时未公布不等于数字已被改写 | `mark_gap` 记录缺口,再 `reverify_claim` 为 unknown |
| 想凭记忆或上期财报把数字补进理由 | 签发时成立不构成现在仍成立;fresh 要有锚 T1 的证据 id | 先 `retrieve` 或 `read_source`;拿不到 T1 原文则不要判 fresh |
| `mark_stale` 的 reason 只写「与最新财报不符」 | 有效反证要有显式因果句:哪一句、哪个科目、哪个数字 | 回到 T1 原文指认句子与数字后再提交 |
| 检索里没有 `@T1` 的 evidence_id | 规则闸要求 fresh 引用锚在 T1 | 改 as_of 再 `retrieve`;仍没有则 `mark_gap` |

## 何时读 references

- `references/figure-line.md`:同一科目的核对清单。判定三档的口径不在本包复制,以 Auditor 侧 verdict-rubric 为单一真相。
