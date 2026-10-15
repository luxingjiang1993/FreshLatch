# 模型适配分析（Model Fit Review）

日期：2026-10-15。Trust=Watch。切片 MUM-S5 / A-S5。

层身份：**桌面适配分析**。对照的是 main 上的 `MODEL_REGISTRY` 与 `resolve_model`（S2 profile、S3 运维文档已在 main），加上本机约束。本轮不是延迟采样，不是注册分，不开 C-04。延迟与吞吐全部是「未测」。没有付费 API，没有 LM Studio HTTP。未采样，不报方差。托管端点会漂移，跨会话复现只能是近似的；本轮没有新的云端跑次可以钉。

分析**不**改 locked slot，**不**改 manifest，**不**改 registry 里的生产默认模型 id，**不**写 RESULT。`prefer_local` 只表示日常草稿建议把 profile 设为 `local-lms`。换 `MODEL_REGISTRY["default_llm"].model` 另票。

评分维度与空白表在 [`model-fit-scorecard.template.md`](model-fit-scorecard.template.md)。日期锚点是 [`docs/evidence/model-fit/2026-10-15.md`](../evidence/model-fit/2026-10-15.md)。只读脚本是 `scripts/model_fit_review.py`（默认不发网络，没有 `--live`，CI 不需要 LM Studio）。

## 机型与候选

| 项 | 本轮采用的事实 |
| --- | --- |
| GPU | RTX 5070 Ti 12GB |
| 内存 | 32GB RAM |
| 草稿首选 | LM Studio `qwen3.5-9b`，推荐 n_ctx≈65536。与 `FRESHLATCH_LMS_MODEL` 缺省相同。地址缺省 `http://127.0.0.1:1234/v1`。 |
| 对照 | LM Studio `qwen3.8-27b` 混卸，n_ctx 约 8–12k。分析包含。草稿仍 prefer 9B，因为上下文预算够用，12GB 卡不必为草稿做混卸。 |
| 未做 | 不下载新 GGUF，不测 tok/s，不估月账单，不编 ¥/百万 token。 |

Chat 草稿候选：云端 `qwen-flash`（registry 现默认）vs LMS `qwen3.5-9b` vs LMS `qwen3.8-27b`（混卸）。27B 可能在短提示上更强，本轮没有质量对照，**不**用参数量宣布它赢。草稿 prefer 9B，理由是 n_ctx 与显存占用，不是质量榜。

## 结论总表

| 读点 | registry 模型 id（本轮不改） | `local-lms` 下 `resolve_model` | 结论 |
| --- | --- | --- | --- |
| `default_llm` | `qwen-flash`（temperature=0） | `qwen3.5-9b`，platform=`lmstudio` | `prefer_local` |
| `x1_draft` | `qwen-flash`（`DRAFT_MODEL`） | 能解析到同一台 LMS，**x1 调用点不读它** | `keep` |
| `x1_flag` | `qwen-plus` | registry 原对象（非 overlay） | `keep` |
| `embed` | `text-embedding-v4` | registry 原对象 | `keep` |
| `local_embed` | `BAAI/bge-small-zh-v1.5` | registry 原对象 | `keep` |
| `neural_rerank` | `BAAI/bge-reranker-base` | registry 原对象 | `keep` |
| `nli` | `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | registry 原对象（locked，transformers） | `keep` |
| `judge_qwen` | `qwen3-235b-a22b-instruct-2507` | registry 原对象（locked） | `must_cloud` |
| `judge_deepseek` | `deepseek-flash` | registry 原对象（locked） | `must_cloud` |
| `judge_kimi` | `kimi-k2.6` | registry 原对象（locked） | `must_cloud` |
| C-04 正式 generator | `DEFAULT_MODEL` = `qwen-flash` | 正式禁止 profile=`local-lms` | `must_cloud` |

```text
fit-verdict default_llm prefer_local
fit-verdict x1_draft keep
fit-verdict x1_flag keep
fit-verdict embed keep
fit-verdict local_embed keep
fit-verdict neural_rerank keep
fit-verdict nli keep
fit-verdict judge_qwen must_cloud
fit-verdict judge_deepseek must_cloud
fit-verdict judge_kimi must_cloud
fit-verdict c04_generator must_cloud
```

`keep` 6 个 registry 槽，`prefer_local` 1 个（仅日常 `default_llm`），`must_cloud` 3 个评委槽。C-04 读点另记 `must_cloud`，它不是第十一个 registry 槽。

## 日常草稿：`default_llm`

`LLMClient` 与未传 `model` 的 `DecodingParams` 调用 `resolve_model("default_llm")`。`FRESHLATCH_MODEL_PROFILE=local-lms` 时，这一条日常路径换成 LMS，业务调用点不用改。`DEFAULT_MODEL` 与 `MODEL_REGISTRY["default_llm"]` 仍是 `qwen-flash`。正式代码读这两处，不跟 profile 走。

| 维度 | `qwen-flash`（registry 默认，保留 id） | LMS `qwen3.5-9b` | LMS `qwen3.8-27b` 混卸 |
| --- | --- | --- | --- |
| 任务匹配 | 云端登记。正式生成也读这个 id | 日常草稿匹配。正式生成不走 profile | 只适合短上下文草稿 |
| 质量下限 | 现钉模型。本轮不重测，不把「便宜」写成质量结论 | 日常草稿可接受。桌面判断，无金标对照，无多 seed | 未测。不用 27B 这个名字代替测量 |
| 上下文 | 云端窗口。本轮不测 | n_ctx≈65536。草稿首选 | 约 8–12k。长草稿不够 |
| 延迟与吞吐 | 未测 | 未测 | 未测 |
| 成本 | 按次 API。无用量样本，不估月账单 | 无 token 账单。占这张 12GB 卡 | 混卸，运维摩擦更高。不报价 |
| 可复现 / 锁定 | temperature=0。`DEFAULT_MODEL` 给正式路径 | 可切 profile。不得写入 RESULT | 同左，且不推荐做草稿默认 |
| 运维摩擦 | 需要 `DASHSCOPE_API_KEY`。CI 单测不打这条网 | 本机 LMS。CI 不要求 LMS 在跑 | 12GB 放不下全量，要混卸。CI 同样不依赖 |

结论：`prefer_local`。日常草稿用 9B，不用 27B 做草稿首选。registry 生产默认模型 id 保持 `qwen-flash`。要改这个 id，另开票，本文件不授权。

## `x1_draft`

registry 模型是 `qwen-flash`，`max_output_tokens=32768`。`local-lms` 的 overlay 包含这个槽，`resolve_model("x1_draft")` 会指向同一台 LMS `qwen3.5-9b`。x1 生成入口读的是 `DRAFT_MODEL` 常量，不读 `resolve_model` 的返回值。把结论写成 `prefer_local` 会让人以为设了 profile 就换了 x1 草稿，实际不会。

结论：`keep`。日常草稿偏好记在 `default_llm`。本轮不改 x1 调用点，不改 `DRAFT_MODEL`。若另票把 x1 接到 `resolve_model`，草稿侧再考虑 9B；27B 混卸仍因 8–12k 上下文不适合当草稿首选。质量与延迟本轮未测。

## `x1_flag`

registry 模型是 `qwen-plus`，同样 `max_output_tokens=32768`。不在 overlay，也不是 locked。flag 用比草稿更高的云端档，是现登记，不是本轮新选的。9B 是草稿首选，不是 flag 的替换。12GB 上的 27B 混卸既未测质量，上下文也更紧。

结论：`keep`。不改 x1。不把 flag 标成 `must_cloud`：`PROFILE_LOCKED_SLOTS` 不含它，正式锁写在评委、`nli` 和 C-04 读点上。要换 flag 模型另票。延迟未测。

## `embed` / `local_embed` / `neural_rerank`

三条都不进 LM Studio。`embed` 仍是 DashScope `text-embedding-v4`。生产检索的本地向量是 `local_embed` 的 `BAAI/bge-small-zh-v1.5`（fastembed）。精排是 `BAAI/bge-reranker-base`。`PRODUCTION_RETRIEVAL_MODE` 本轮不改。

更重的 rerank 候选（如 `bge-reranker-v2-m3`、`bge-reranker-large`）会和草稿 9B 抢这张 12GB 卡。本轮不测它们，不换生产。云端 embed 与本地 `local_embed` 各干各的槽，不把 `embed` 指到 LMS。

结论：三槽都是 `keep`。任务匹配维持现状。质量下限未重跑。成本不重新报价。CI 继续不下载新权重。

## `nli`

模型 id 是 `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7`，platform=`transformers`，没有 `base_url`，没有 `env_key`。槽位在 locked 集合里，`local-lms` 不能换成 LMS。同族更小的多语 NLI 也许更快，本轮不测、不换，也不把 NLI 说成 LM Studio 模型。

结论：`keep`。这里的本地是 transformers 权重，不是 `prefer_local` 那个 LMS 草稿覆盖。正式跑建议继续锁这个 id。本轮不改 `VERIFY` 仪器，不改 model id 字符串。

## 评委 `judge_qwen` / `judge_deepseek` / `judge_kimi`

三家都在 locked 集合里，`local-lms` 返回 registry 原对象。

| slot | 模型 | temperature |
| --- | --- | --- |
| `judge_qwen` | `qwen3-235b-a22b-instruct-2507` | 0 |
| `judge_deepseek` | `deepseek-flash` | 0 |
| `judge_kimi` | `kimi-k2.6` | 0.6 |

评委要的是三家云端分歧，不是单机再跑一个 9B 或 27B。12GB 卡载不了这些云端档的同类体量。用本地草稿模型替代任一评委，任务就不匹配，质量下限也不成立。本轮不测延迟，不估三家 API 的月账单。

结论：三槽都是 `must_cloud`。不推荐本地。不映射到 LM Studio。

## C-04 正式 generator / RESULT

C-04 没有单独的 registry 槽。正式模块读 `DEFAULT_MODEL` 与 `MODEL_REGISTRY["default_llm"]`，调用时显式传入模型名。二者现在都是 `qwen-flash`。profile 不改写这两个常量，所以 `local-lms` 不会把正式生成器重映射到 LM Studio。即便如此，正式跑仍然禁止在 `local-lms` 下写 RESULT：日常 profile 与正式读点必须分开，避免误钉本地。

结论：`must_cloud`。正式 profile 不得是 `local-lms`。本轮不写 RESULT，不改 manifest 里的 `generator_model` / `nli_model`，不实现 S7 写入闸。S7 仍是后续切片。

## Cursor Agent

Cursor Agent 的工具循环不宜绑到本机 LM Studio。断网、上下文和工具协议都跟 FreshLatch 的草稿槽不是同一条路径。本计划不改 Cursor 配置。

## 复跑

空白维度表：[`model-fit-scorecard.template.md`](model-fit-scorecard.template.md)。

```powershell
$env:PYTHONPATH = "src"
python scripts/model_fit_review.py
```

```bash
PYTHONPATH=src python scripts/model_fit_review.py
```

已 `pip install -e ".[dev]"` 时可以不设 `PYTHONPATH`。脚本始终同时打印 `cloud` 与 `local-lms`，不读 `FRESHLATCH_MODEL_PROFILE`。`FRESHLATCH_LMS_MODEL` 若被设成别的名字，解析列跟着变，草稿结论仍 prefer 缺省的 `qwen3.5-9b`，并在 stdout 打一行 `warn`。没有 `--live`。传入未知参数时进程退出码 2。报告里的 `fit-verdict` 行与脚本结论不一致时退出码 1。

| 码 | 含义 |
| --- | --- |
| 0 | 表已打印。末行含 `http=none paid=none lms_required=no` |
| 1 | registry 与结论表对不齐，或报告缺少 `fit-verdict` 行，或 LMS 模型名/地址为空 |
| 2 | 未知命令行参数 |

## 本轮明确不做

- 不改 floors / gold / x1 调用点 / `PRODUCTION_RETRIEVAL_MODE`
- 不改 C-04 RESULT，不发明 SESOI
- 不改 registry 生产默认模型 id
- S6 连通性 HTTP、S7 RESULT 闸不在本文件
