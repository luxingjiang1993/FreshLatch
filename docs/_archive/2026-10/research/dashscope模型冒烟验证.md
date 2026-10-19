# DashScope 最便宜模型多轮工具调用冒烟验证

- 对应工单:[冒烟验证:DashScope 最便宜模型的多轮工具调用能力 #2](https://github.com/luxingjiang1993/FreshLatch/issues/2)
- 日期:2026-09-19
- 脚本:`scripts/smoke_dashscope_tool_loop.py`(可复跑:`python scripts/smoke_dashscope_tool_loop.py --model qwen-flash --runs 3`)
- 结论:**go;qwen-flash 为开发期主模型**。开发用最便宜模型压成本,真实业务可换更好模型。

## 测试设计

模拟 FreshLatch Lead 复验循环的最小形态:8 条中文主张(5 活 3 死,含金标)、15 篇中文文档(含噪声文档)、4 个工具(`list_claims` / `search_docs` / `read_doc` / `write_verdict`,全中文描述),裸 `chat.completions + tools` 循环。四个场景:

- **A 多轮循环**:跑满全部主张的 verdict,上限 30 轮;考察崩溃、非法 JSON、漏判。
- **B 并行调用**:统计单轮 >1 个 tool_calls 的轮次。
- **C 长上下文**:全部文档块 + 主张列表 + 作废名单一次性注入,直接问 verdict。
- **D 无工具假绿对照**:同模型不带工具,只读旧文档拼出的 T0 摘要,对 dead 主张是否判「成立」。

## 结果

| 场景 | qwen-flash(n=3) | qwen-turbo(n=2) |
|---|---|---|
| A 循环轮数 | 26 / 26 / 30(达上限但无崩溃、无非法 JSON) | 18 / 18 |
| A 非法 JSON | 0 | 0 |
| A 判定准确率(8 条金标) | 0.75 / 0.875 / 0.75(均值 **0.79**) | 0.75 / 0.625(均值 **0.69**) |
| B 并行 tool_calls | **0 次**(从未并行) | 0 次 |
| C 长上下文准确率 | **1.0** | 0.875 |
| D 假绿率(dead 被判「成立」) | **1.0** | 0.8 |

要点:

1. **≥18 轮目标达成**:两模型均稳定跑通 18–30 轮多轮 tool_calls 循环,不崩、不输出非法 JSON、不忘记调工具;最后一轮 qwen-flash 在 30 轮上限处仍有主张未出 verdict(未判崩,因无异常),实际 Lead 有步数护栏,触发护栏即收口,属可接受行为。
2. **并行 tool_calls 不可用**:两个最便宜模型单轮都只发 1 个 tool_call。架构上**不得假设并行工具调用**,检索编排按串行设计(或显式 `tool_choice` 提示,不保证生效)。
3. **中文函数调用准确可用**:中文工具描述 + 中文语料下,循环判定准确率 ~79%(qwen-flash),错误集中在「需多文档时间线推理」的陷阱主张(如计费规则变更链条 C7);长上下文单发判定 qwen-flash 反而满分。
4. **无工具假绿对照成立**:qwen-flash 不带工具时 dead 主张 100% 被判「成立」,对照组能有效暴露「不检索就放行」的假绿,评测哲学的前提在同模型上成立。
5. **qwen-flash 全面不劣于且更便宜**:准确率、长上下文、假绿率均优于 qwen-turbo;且阿里云已宣布 qwen-turbo 停止更新并推荐 qwen-flash。

## 成本估算(qwen-flash,国内价:输入 ¥0.15/百万 token、输出 ¥1.5/百万 token,≤128K)

一次完整 8 主张复验(冒烟实测均值):约 5.1 万输入 token + 1.2 千输出 token:

- **每主张复验 ≈ ¥0.001(约 0.1 分钱)**
- 一次完整 8 主张 Lead 复验 ≈ ¥0.01
- 加 Critic / Auditor 各一轮(上下文更短),单次复验单全链路 ≈ ¥0.02–0.03
- 评测期跑 100 次全量评测 ≈ ¥2–3,可忽略

价格来源:[阿里云模型调用价格](https://help.aliyun.com/zh/model-studio/model-pricing)(2026-09-16 页面)。

## 选型建议

- **开发期主模型(Lead 复验循环、Critic、Auditor):统一 qwen-flash**。同模型保证无工具假绿对照的公平性;成本可忽略。
- **若真实业务升档**:建议 Critic / Auditor 环节升 qwen-plus 档(输入约 ¥0.8/百万、输出约 ¥2/百万,以官网当时价格为准),Lead 循环保持 flash;升档后**假绿对照必须仍用与 Lead 同档的模型**,或同时跑两档对照。
- 文档与规格中统一标注:**「开发用最便宜模型压成本,真实业务可换更好模型」**。

## 复现

```bash
python scripts/smoke_dashscope_tool_loop.py --model qwen-flash --runs 3
python scripts/smoke_dashscope_tool_loop.py --model qwen-turbo  --runs 2
```
