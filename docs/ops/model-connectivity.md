# 模型连通性体检

切片 MUM-S6 / A-S6。脚本 `scripts/smoke_model_connectivity.py`。

默认检查当前 profile 下每个 slot 的 `resolve_model` 结果，以及该行 `env_key` 在**进程环境**里是否为非空字符串。stdout 只打印变量名和 `present` / `missing` / `n/a`，不打印密钥值。不构造聊天客户端，不发 chat completions，不读 `.env` 文件。不写 C-04 RESULT。

`--probe-lms` 与 `--probe-http` 才发 HTTP，而且只做 GET `{base_url}/models`。这不是付费 chat 的成功标准。

## 本机怎么跑

已 `pip install -e ".[dev]"` 时可以不设 `PYTHONPATH`。否则先把 `src` 放进 `PYTHONPATH`。变量要在 shell 里导出；本脚本不加载 `.env`。

```powershell
$env:PYTHONPATH = "src"
python scripts/smoke_model_connectivity.py
python scripts/smoke_model_connectivity.py --profile local-lms
python scripts/smoke_model_connectivity.py --profile local-lms --probe-lms
python scripts/smoke_model_connectivity.py --probe-http --timeout 5
```

```bash
PYTHONPATH=src python scripts/smoke_model_connectivity.py
PYTHONPATH=src python scripts/smoke_model_connectivity.py --profile local-lms
PYTHONPATH=src python scripts/smoke_model_connectivity.py --profile local-lms --probe-lms
PYTHONPATH=src python scripts/smoke_model_connectivity.py --probe-http --timeout 5
```

| 调用 | 行为 |
| --- | --- |
| 不传探针 | 只解析并检查 env。末行 `probe=none chat=none`。LM Studio 不必在跑。 |
| `--profile cloud` 或 `--profile local-lms` | 显式 profile，不读 `FRESHLATCH_MODEL_PROFILE`。 |
| 不传 `--profile` | 读 `FRESHLATCH_MODEL_PROFILE`。未设置时按 `cloud`。 |
| `--probe-lms` | 只 GET LM Studio。地址来自 `resolve_model("default_llm", profile="local-lms")`，即 `FRESHLATCH_LMS_BASE_URL` 或缺省 `http://127.0.0.1:1234/v1`，再拼 `/models`。profile 仍是 `cloud` 时也不会改去打云端 chat。 |
| `--probe-http` | 对**当前 profile** 解析结果里每个 http(s) `base_url` GET `/models`。同一 URL 只打一次。`profile=cloud` 时不包含 LM Studio。`profile=local-lms` 时 overlay slot 的地址就是 LM Studio，会包含在内；locked 的 `judge_*` 仍是云端 `base_url`。 |
| 两个探针同时 | 同一 URL 只打一次。 |

LMS 的 HTTP 只在这两种情况出现：当前 profile 是 `local-lms` 且开了 `--probe-http`（打的是解析出来的 overlay `base_url`），或显式 `--probe-lms`。`base_url` 必须是带主机名的 `http` / `https`。连不上、超时、HTTP 非 2xx，退出码 2。不另做第二条 TCP 预检，也不改试别的路径。

有 `env_key` 的 GET 把密钥放在 `Authorization: Bearer` 请求头里。缺密钥时先退出码 1，不发这个请求。`local-lms` 的 overlay slot（`default_llm`、`x1_draft`）`env_key` 为空，探针不带云端密钥；`judge_*` 与 `embed` 等仍按 registry 要求各自的 env。

`nli`、`local_embed`、`neural_rerank` 没有 `base_url`，不参与 HTTP。

## CI 为什么不探针

GitHub Actions 只跑 `pytest`（零 LLM）。流水线**不**传 `--probe-http`，**不**传 `--probe-lms`，不启动本机 LM Studio，也不需要云端密钥。

单测 `tests/unit/test_smoke_model_connectivity.py` 在进程内调用 `main`，用假 env，并挡住 `urlopen`。默认路径的测试不发 HTTP。探针路径的测试替换 `http_get`。CI 因此不依赖可达的 DashScope、DeepSeek、Moonshot 或 LM Studio。

不要把本脚本加进 CI 的实网步骤。缺密钥时默认路径退出码是 1，那是给本机体检用的，不是 pytest 的门槛。

## 退出码

| 码 | 含义 |
| --- | --- |
| 0 | 解析成功，声明了 `env_key` 的 slot 都有非空值。若带了探针，全部 GET 为 HTTP 2xx。末行形如 `ok profile=cloud slots=10 env_missing=0 probe=none chat=none`。 |
| 1 | 配置。未知 profile、未知 slot、LMS 模型名或地址为空、`base_url` 不是带主机名的 http(s)、`--timeout` 不是正数、缺 env、或 overlay / locked / `DEFAULT_MODEL` / `DRAFT_MODEL` 不变量不成立。stderr 前缀 `smoke_model_connectivity failed:`。缺 env 时 stdout 仍有表，`env` 列为 `missing`。 |
| 2 | 探针不可达：超时、连接失败，或 HTTP 非 2xx（含 401 / 403 / 5xx）。未知命令行参数也是 2（argparse，没有上述前缀）。 |

密钥已经导出但服务拒绝，是退出码 2。变量本身缺失，是退出码 1，请求不会发出。

## 正式跑仍须 cloud profile

退出码 0 只说明当前进程的 env 与 registry 解析（以及你显式打开的 GET `/models`）通过。它**不是**正式评测许可。

正式 C-04 / RESULT 仍须 profile 为 `cloud`。写入前要断言 profile 不是 `local-lms`、locked slot 未被覆盖。那道闸是 **S7**，见 [`docs/plans/model-unified-mgmt/01-plan.md`](../plans/model-unified-mgmt/01-plan.md) 的 S7。本脚本不实现闸，不写 RESULT，也不在 `local-lms` 下放行正式跑。

解析规则与 overlay / locked 名单见 [`model-profiles.md`](model-profiles.md)。适配结论见 [`model-fit-report.md`](model-fit-report.md)（S5）。

## 不要动

本脚本不改 floors、gold、x1 调用点、`PRODUCTION_RETRIEVAL_MODE`，不写 C-04 RESULT，不发明 SESOI。成功标准不是一次付费 chat。
