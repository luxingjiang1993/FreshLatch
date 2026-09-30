# focus 六个合法方向

封闭枚举,与语料金标维度同构。词表一致性由代码常量 `FOCUS_DIMENSIONS` + 单测钉死,本文件只是投影;以代码返回的错误信息为准。

| 枚举值 | 中文 | 找反证时看什么 |
|---|---|---|
| `competitor_pricing` | 竞品价格 | 竞品报价、版本、折扣的新表述,尤其低于主张口径的 |
| `regulatory_stance` | 监管口径 | 监管条文、实施条例、生效日期的新表述 |
| `interview_reversal` | 访谈改口 | 同一对象的复访口径与 T0 是否矛盾 |
| `cost_model` | 成本模型 | 单会话成本、折算口径的复测结果 |
| `market_structure` | 市场结构 | 市场规模普查、结构变化的同口径更新 |
| `tech_ecosystem` | 技术生态 | 技术路线、生态位的新事实 |

省略 focus = 不限方向,全语料找反证。填错值 → 整个调用被拒、回列本词表、重试计步。

## Prefer 规则(防默认落到更常见维)

判法仍是问『原主张凭什么为真?』——证据出处类型即维度。以下 Prefer 防默认 cost_model(FactReasoner 式封闭菜单 + Prefer-over;枚举反引号仅上表,本节明文以免词表投影漂移):

- Prefer interview_reversal over cost_model:证据出自访谈/纪要/口头口径时,即使内容谈分成、成本或定价,一律 interview_reversal
- Prefer market_structure over cost_model:证据是采用率、规模普查、份额/格局时走 market_structure
- Prefer competitor_pricing over cost_model:证据是客单价、报价、价目对标时走 competitor_pricing
- 禁止默认 cost_model:仅当主张前提建立在成本/费用结构测算上才填;有疑勿填 cost_model
