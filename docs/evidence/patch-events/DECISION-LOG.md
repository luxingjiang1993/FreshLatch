# patch_events 决策日志

日期：2026-10-07。仓库针：`main` `d42276d`。来源：#302 现稿、同日研讨评论，以及 Ronin 代理人对主比较、配额、构造、pilot、评委和投稿映射的拍板。

这一页记录投稿和范围。它不是预注册。改这一页不改变 `PREREG.md` 里的比较、指标、配额、算子、种子和评委。`PREREG.md` 跑数后不得修改；要改口径只能另写新文件，并声明旧页作废。

## 已锁进预注册的决定

下面各项的可执行定义在 `docs/evidence/patch-events/PREREG.md`。这里只留索引。

1. 主比较顺序：第一是 T 对 C 的误放率，第二是 T 对 B1（post-hoc verify），第三是 T 对 B2（KPR 式 claim→diff）。消融四项按 #302 写在主比较之后。
2. 主指标是固定放行率下的误放率。误拒率同时报。另报错改率、可复验率、延迟和成本。
3. n=30 的层配额是数值 8、日期 8、条款替换 8、删除 6。n=100 每类 25。
4. 每层正确修改与坏修改按预注册的余数规则拆开，构造算子在跑数前写死。
5. pilot 15 条只查流程，最多一份流程笔记，然后冻结。pilot 结果公开，不进主表。第二领域本轮不做。
6. 评委是三家 API 模型，见下一节。统计是配对 bootstrap 10000 次，种子 20261007。

## 评委拍板

#302 正文里的「至少 2 名真人盲审」不执行于本次跑数。研讨评论里「Kimi 单一外部评委，现有模型标注当第二标注方并报两者的 κ」已被同日更正替换。

现行决定：

- 三家评委是 Qwen2.5-72B、DeepSeek-V3、Kimi。三家都不是生成系统 `qwen-flash`。
- 走 API。model 字符串、temperature=0、思考关闭和评分细则以 `PREREG.md` 为准。全程留日志。
- 报三家两两之间的 Cohen's κ，以及三家的 Fleiss' κ。
- 三家意见不一致的样本由用户本人裁决。
- 用户本人另外盲审预注册里写死的那一部分，报评委与用户的一致率。
- 对外句子是「模型评委加单人抽检」。不得写成真人盲审。
- 仓内已有的模型双标只作辅助，不计入评委，不进入 κ。

冲 EMNLP 2027 Findings 之前，若走结果甲的那条投稿，再补 2 名真人盲审。那两名看不到组别。协议写在新的附加预注册里，不回改 `PREREG.md`。附加页完成之前，稿子仍只能写模型评委加单人抽检。

## 第二领域

研讨评论里的可选项是 API 文档或 changelog，30 到 50 条，只做泛化探针。本轮不做。不做 KPR benchmark，不做医疗指南。因此本次结果不写跨领域泛化。

## 场地

三条结果都不投 NAACL 2027。

「成立」用 `PREREG.md` 的定义：固定放行率下的误放率，配对差的点估计 > 0，且 95% bootstrap 区间下界 > 0。

### 结果甲

第一、第二、第三主比较都成立。

- 先挂 arXiv。
- 主投 ACL 2027 Industry / Demo。
- 冲 EMNLP 2027 Findings 之前补齐上一节的 2 名真人盲审。未补齐则不投 Findings。
- 贡献句可以同时写相对 C、B1、B2。仍然不写成新的 risk-coverage 方法，不写成笼统的可解释文档更新。

### 结果乙

只有第一主比较成立。第二或第三至少有一条不成立。

- 先挂 arXiv。
- 主投 ACL 2027 Industry / Demo。
- 不把 EMNLP 2027 Findings 当默认投稿。
- 贡献句只写相对无证据改写的 fail-closed。不写优于 RARR 或 KPR。

### 结果丙

第一主比较不成立，或无定义。

- 不投 ACL 2027 Industry / Demo。
- 不冲 EMNLP 2027 Findings。
- 可以写 arXiv 技术报告，或投 Workshop 保底。
- 不得把主实验写成成功。

消融、共形预留集和评委 κ 都不改变上面三条的分界。

## 跑数据前偏离 · Amendment 1

日期：2026-10-08。决定人：真人作者（Oriental Ronin，#325，2026-10-08 01:40 UTC+8）。此时尚无任何评委数据。同一条写在 `PREREG.md` 文末「修订记录 Amendment 1」。原锁定表保留，旁边加注「见 Amendment 1」。本页不改比较、指标、配额、算子和种子。

查阅日期：2026-10-08。

1. DeepSeek 评委 model：原值 `deepseek-ai/DeepSeek-V3`，新值 `deepseek-flash`。`thinking` 仍关闭。temperature 仍为 0。原因：DeepSeek 官网已无 V3 模型 id。文档：https://api-docs.deepseek.com/quick_start/pricing ，https://api-docs.deepseek.com/api/create-chat-completion 。非思考模式的 temperature 取值是 0 到 2；没有作用只针对思考模式（https://api-docs.deepseek.com/guides/thinking_mode），所以不改成别的温度。
2. 禁止名单：去掉 `deepseek-flash`。保留 `deepseek-reasoner`、`deepseek-v4-pro`、`deepseek-chat`。加入 `deepseek-ai/DeepSeek-V3`。
3. Kimi base_url：原值 `https://api.moonshot.ai/v1`，新值 `https://api.moonshot.cn/v1`。model 仍为 `kimi-k2.6`。thinking 仍关闭。temperature：原值 0，新值 0.6。原因：国内站非思考模式温度强制为 0.6（https://platform.moonshot.cn/docs/guide/kimi-k2-6-quickstart）。
4. Qwen 的 model 与 temperature=0 不变。回声校验改为对照这些新登记值。

## 跑数据前偏离 · Amendment 2

日期：2026-10-08。决定人：真人（Oriental Ronin，#329，2026-10-08 02:50 UTC+8）。此时尚无任何评委数据。同一条写在 `PREREG.md` 文末「修订记录 Amendment 2」。原文与 Amendment 1 保留。关联 #329、#304。

1. 比较对象：每条的最终标签对 `construction_gold`。三家在问题 A 和问题 B 上都一致时，最终标签是这个共同答案；否则是用户单人抽检的裁决。不用多数票，不拿单家评委单独比。缺评委标签或缺完整裁决的条目没有最终标签。缺评委标签的只进缺失清单。缺裁决的视为未完成。
2. 映射：A 为「是」且 B 为「是」→ `正确`；A 或 B 任一为「否」→ `坏`。映射结果与 `construction_gold` 不同即为冲突。
3. 范围：所有有最终标签的条目都参与比较，不限于抽检样本。
4. 清单显示 `claim_id`、修改前、修改后、证据、`construction_gold`、映射后的最终标签、来源（三评委一致 / 用户裁决）。不显示组别、消融、各家评委各自的选择。有未完成裁决时拒绝生成，不输出冲突结论。`construction_gold` 不被最终标签替换。清单只用于报告与复核。

理由：不用多数票，是遵循本页和 `PREREG.md` 里不用多数票填缺失的原禁令。不拿单家比，是为了不把各评委的选择露给用户。A 与 B 都为「是」才映成正确，贴合 fail-closed：任一为「否」就按坏修改对待。清单在需要的裁决写完之后才生成，抽检名单仍然先于不一致结果定下来，盲态保持。原因还有一条：原 `PREREG.md` 没有定义比较对象，也没有定义「是 / 否」到「正确 / 坏」的映射。

## 跑数据前偏离 · Amendment 3

日期：2026-10-08。决定人：用户（Oriental Ronin，2026-10-08 12:43 UTC+8）。转述人：Ronin 代理人。此时尚无 pilot，也尚无正式评委数据。同一条写在 `PREREG.md` 文末「修订记录 Amendment 3」。原锁定表与 Amendment 1、Amendment 2 原文保留。本条取代 Amendment 1 第 4 条中的 Qwen 模型名。本页不改比较、指标、配额、算子和种子。记录于 #366。

1. Qwen 评委 model：原值 `qwen2.5-72b-instruct`，新值 `qwen3-235b-a22b-instruct-2507`。temperature 仍为 0。不加 thinking 参数（纯 instruct）。endpoint 与密钥变量名 `DASHSCOPE_API_KEY` 不变。DeepSeek、Kimi 不动。
2. 原因：该登记模型已于 2026-05-13 在阿里云百炼下线（官方公告）。2026-10-08 12:39 冒烟返回 403 access_denied，GET /models 列表中无此模型。Amendment 1 写「Qwen 不变」时模型已下线。选择理由：开源权重、带日期固定快照、纯 instruct，接口将来下线仍可自部署复现。
3. 冒烟证据（2026-10-08 12:44，单次调用）：HTTP 成功，返回 model 与登记一致，temperature=0 无报错，无 reasoning_content，输出 JSON 可解析，延迟 1.44s，tokens 67/9。

已知局限（不改规则）：

- DeepSeek、Kimi、Qwen 的响应都不回传 temperature。现行 echo 规则对缺失字段不判不符，因此实际只核对了 model。请求侧发出的 temperature 记入 judge log 作为证据。论文如实说明。
- Kimi 关 thinking 后仍报 reasoning_tokens=1。仅备注。

## 跑数据前偏离 · 非拒绝类错误记缺失

日期：2026-10-08。决定人：用户（Oriental Ronin，#362 选 A）。转录人：Ronin 代理人。此时尚无 pilot，也尚无正式评委数据。不改 `PREREG.md`。记录于 #369。

1. 非拒绝类传输错误只作废该评委的该条，记缺失。同一评委的下一条继续。其他评委继续。不重试。
2. 该条的 `void_reason` 只含错误类型和整数状态码，不含错误正文、密钥、headers。没有状态码时只写错误类型。
3. 温度被拒、回显温度或 model 与登记不符、思考关不掉，仍使该评委整次运行作废，并丢掉该评委已有标签。
4. 结果按评委报告缺失率，分母是该评委本轮条数。整次作废的评委不把作废记成缺失率，该字段为空。

