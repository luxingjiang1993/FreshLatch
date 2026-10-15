# 模型 profile（cloud / local-lms）

日常草稿用 env 在 `cloud` 与 `local-lms` 之间切换。解析入口是 `resolve_model(slot, profile=None)`（`src/freshlatch/model_profile.py`）。未传入 `profile` 时读 `FRESHLATCH_MODEL_PROFILE`。业务调用点不必为这次切换改代码。

`cloud` 返回 `MODEL_REGISTRY` 里的原对象。`local-lms` 只改下面写明的 overlay slot，把 model、platform、base_url 换成 LM Studio 的 OpenAI 兼容地址，并把 `env_key` 置为 `None`。锁定 slot 仍返回 registry 原对象。

未知 profile、未知 slot、把 LMS 模型名或地址设成空字符串，解析失败关闭，不会悄悄回到云端。

## 环境变量

| env | 缺省 | 作用 |
| --- | --- | --- |
| `FRESHLATCH_MODEL_PROFILE` | `cloud`（未设置时） | `cloud` 或 `local-lms` |
| `FRESHLATCH_LMS_MODEL` | `qwen3.5-9b` | local-lms overlay 使用的模型名 |
| `FRESHLATCH_LMS_BASE_URL` | `http://127.0.0.1:1234/v1` | LM Studio 的 OpenAI 兼容根地址 |

只允许这两个 profile 名字，大小写敏感。`LOCAL-LMS` 与空白字符串都会失败。

PowerShell：

```powershell
$env:FRESHLATCH_MODEL_PROFILE = "local-lms"
$env:FRESHLATCH_LMS_MODEL = "qwen3.5-9b"
$env:FRESHLATCH_LMS_BASE_URL = "http://127.0.0.1:1234/v1"
```

bash：

```bash
export FRESHLATCH_MODEL_PROFILE=local-lms
export FRESHLATCH_LMS_MODEL=qwen3.5-9b
export FRESHLATCH_LMS_BASE_URL=http://127.0.0.1:1234/v1
```

回到云端登记：把 `FRESHLATCH_MODEL_PROFILE` 设为 `cloud`，或从环境里去掉它。`FRESHLATCH_LMS_MODEL` 与 `FRESHLATCH_LMS_BASE_URL` 只在解析 overlay slot 时读取。

显式 `resolve_model(slot, profile="cloud")` 以参数为准，不读 `FRESHLATCH_MODEL_PROFILE`。

## Overlay slot

`local-lms` 只覆盖 `default_llm` 与 `x1_draft`。

| slot | local-lms 解析结果 |
| --- | --- |
| `default_llm` | model=`FRESHLATCH_LMS_MODEL`，platform=`lmstudio`，base_url=`FRESHLATCH_LMS_BASE_URL`，`env_key=None`。温度与输出上限仍复制云端行。 |
| `x1_draft` | 同一套 LM Studio 地址。`resolve_model("x1_draft")` 能解析到这台机器。 |

`default_llm` 的日常路径会跟 profile：`LLMClient` 与未传 `model` 的 `DecodingParams()` 调用 `resolve_model("default_llm")`。调用方显式传入的 `model=` 保持原字符串。

`x1` 生成入口仍读取 `DRAFT_MODEL`（registry 常量 `qwen-flash`），不读 `resolve_model` 的返回值。本页不改 x1 调用点。

`embed`、`local_embed`、`neural_rerank`、`x1_flag` 不在 overlay 里。`local-lms` 不把 embed 指到 LM Studio。

## Locked slot

下列 slot 在 `local-lms` 下保持 registry 原对象，覆盖不生效：

- `judge_qwen`
- `judge_deepseek`
- `judge_kimi`
- `nli`（platform=`transformers`，本地模型 id，不走 LM Studio，也没有 base_url）

C-04 正式生成器没有单独的 slot。正式模块继续读 `DEFAULT_MODEL` 与 `MODEL_REGISTRY["default_llm"]`，并在调用时显式传入模型名。profile 不改写这两个常量，所以 `local-lms` 不会把正式生成器重映射到 LM Studio。

## 正式跑前闸

切片 MUM-S7。写入 C-04 RESULT 与同一次注册分之前，`write_measured`（`src/freshlatch/eval/patch_establishment_formal.py`）调用 `assert_formal_run_allowed()`（`src/freshlatch/formal_run_gate.py`）。

| 条件 | 结果 |
| --- | --- |
| 未设置 `FRESHLATCH_MODEL_PROFILE`，或值为 `cloud` | 通过 |
| `local-lms` | `FormalRunGateError`，不写文件 |
| 未知 profile | `UnknownModelProfileError`，不写文件 |
| `FRESHLATCH_ALLOW_NON_RESULT_DEBUG=1` 且 profile 为 `local-lms` | 仍拒绝正式写入。该变量只表示非 RESULT 调试，唯一认的值是 `1` |

闸同时确认 locked slot（`judge_qwen`、`judge_deepseek`、`judge_kimi`、`nli`）在 `local-lms` 下仍是 `MODEL_REGISTRY` 原对象。被覆盖则失败关闭。

显式 `assert_formal_run_allowed(profile="cloud")` 以参数为准，不读 `FRESHLATCH_MODEL_PROFILE`。`write_measured` 不传 profile，因此进程里的 `local-lms` 会挡住写入。

本页与冒烟脚本都不写 RESULT。

### 未接线入口（follow-up）

本票只闸主路径 `write_measured`。它写 C-04 的 `docs/evidence/patch-establishment/RESULT.md`，以及同一次的 `measurement.json`、`manifest.json`、`primary-tc.json`。下列入口不写这份 C-04 RESULT，本票不改它们：

- `patch_events_formal_y.write_result_y`：历史 `RESULT-Y`
- `public_pack.write_result`：公开包 `RESULT.json`，拒绝写入 `docs/evidence/`
- `quality_gate.score_registered_segments`：离线质量闸判分，不落 RESULT 文件
- `patch_establishment.write_scaffold`：`run_status=unrun` 脚手架，不写分数
- `send_generations`：发送生成，不写 RESULT。本票不重开 C-04 正式跑
- `scripts/run_x1_offline_mode_compare.py`、`scripts/run_neural_rerank_compare.py`、`scripts/run_fastembed_081_recheck.py`、`scripts/run_issue_284_verify.py`：各自的实验 `RESULT.md`，不是 C-04 成立格

## 冒烟

`scripts/smoke_model_resolve.py` 对代表 slot 调用 `resolve_model`，把 `profile / slot / model / platform / base_url / kind` 打到 stdout。`kind` 是 slot 的类别，两个 profile 下相同：`overlay`（local-lms 允许换成本机）、`locked`（local-lms 仍返回 registry 原对象）、`registry`（既不覆盖也不锁定）。`cloud` 行上的 `overlay` 只表示这个 slot 可以被 local-lms 替换，该行的 model 仍是云端登记。`base_url` 为空时打印 `-`。

不发网络请求，不打 DashScope，不打 LM Studio HTTP，不构造聊天客户端。LM Studio 不必在跑。

```powershell
$env:PYTHONPATH = "src"
python scripts/smoke_model_resolve.py
python scripts/smoke_model_resolve.py --profile both
python scripts/smoke_model_resolve.py --profile local-lms
```

```bash
PYTHONPATH=src python scripts/smoke_model_resolve.py
PYTHONPATH=src python scripts/smoke_model_resolve.py --profile both
```

已 `pip install -e ".[dev]"` 时可以不设 `PYTHONPATH`。

| 调用 | 行为 |
| --- | --- |
| 不传 `--profile`，且未设置 `FRESHLATCH_MODEL_PROFILE` | 依次打印 `cloud` 与 `local-lms` |
| 不传 `--profile`，且设置了该 env | 只按该 env 解析。未知值退出码 1 |
| `--profile cloud` 或 `--profile local-lms` | 只打印这一个。显式参数不读 `FRESHLATCH_MODEL_PROFILE` |
| `--profile both` | 打印两个 profile。local-lms 行仍遵循 `FRESHLATCH_LMS_MODEL` 与 `FRESHLATCH_LMS_BASE_URL` |

退出码：

| 码 | 含义 |
| --- | --- |
| 0 | 表已打印。末行形如 `ok slots=10 profiles=cloud,local-lms http=none` |
| 1 | 未知 profile、未知 slot、LMS 模型名或地址为空，或 overlay / locked / `DEFAULT_MODEL` / `DRAFT_MODEL` 不变量不成立。原因在 stderr，前缀 `smoke_model_resolve failed:` |
| 2 | `--profile` 不是 `cloud`、`local-lms`、`both` |

单测 `tests/unit/test_model_profile.py` 覆盖解析本身。`tests/unit/test_smoke_model_resolve.py` 在进程内调用冒烟 `main`，不要求 LM Studio。

密钥是否在环境里、以及可选的 GET `/models`，见 [`model-connectivity.md`](model-connectivity.md)（S6）。解析冒烟本身仍然不发网络。

## 不要动

本切换不改 floors、gold、x1 调用点、`PRODUCTION_RETRIEVAL_MODE`，不写 C-04 RESULT，不发明 SESOI。适配分析见 [`model-fit-report.md`](model-fit-report.md)（S5）。连通性体检见 [`model-connectivity.md`](model-connectivity.md)（S6）。正式跑前的 cloud profile 闸是 S7，见上文「正式跑前闸」。
