# QG-04 冻结神经基线离线冒烟重跑

日期：2026-10-13。1 次离线冒烟核对，不报方差，不补 SESOI，不把描述数字写成产品通过线。

口径沿用 `docs/evidence/quality-gate/PREREG.md` 第 2 节与第 8 节。本页不改那一页的冻结字段，不改 `docs/evidence/neural-rerank/PREREG.md`，不改 `PRODUCTION_RETRIEVAL_MODE`。

## 结论

冒烟通过。排序层逐位一致。

同一臂、同一金标、同一 k=10 下，224 道 arm 题的 lexical 名次、neural 名次、hit 0/1 与冻结 `docs/evidence/neural-rerank/per-query.json` 逐题相同。Recall@10 右臂、MRR@10 右臂，以及左右臂差，与冻结 `summary.json` 的 k10 描述数字逐位相同。

这是单次确定性重跑，不是抽样，不估计运行间噪声。p95 有漂移，按预注册不挡「排序一致」。

## 对照（k10）

冻结文件：`docs/evidence/neural-rerank/summary.json`。

baseline_summary_sha256: `8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526`（重跑后字节未改，2451 字节）。

分母：`data/exp/x1/questions.json`，`score_role=arm`，n=224，k=10。右臂是 neural（`BAAI/bge-reranker-base`）。左臂是 lexical，只作对照。

| 字段 | 冻结 | 本次 | 差（本次 − 冻结） |
|---|---:|---:|---:|
| Recall@10 右臂 | 0.9732142857142857 | 0.9732142857142857 | 0 |
| Recall@10 左臂 | 0.9732142857142857 | 0.9732142857142857 | 0 |
| MRR@10 右臂 | 0.8381855867346939 | 0.8381855867346939 | 0 |
| MRR@10 左臂 | 0.7566609977324263 | 0.7566609977324263 | 0 |
| MRR@10 差（neural − lexical） | 0.08152458900226757 | 0.08152458900226757 | 0 |
| MRR@10 95% 区间 | 0.04773198341836735 ~ 0.1171530435090703 | 同左 | 0 |
| nDCG@10 右臂（描述，非本页通过指标） | 0.8249303827609481 | 0.8249303827609481 | 0 |
| nDCG@10 差 | 0.06231550367445169 | 0.06231550367445169 | 0 |
| McNemar 只 lexical / 只 neural / 都中 / 都未中 | 0 / 0 / 218 / 6 | 0 / 0 / 218 / 6 | 0 |

区间数字与冻结文件逐位相同，是因为题级配对完全相同，bootstrap 种子仍是脚本里的 `20261007`。本次不把这些区间解释成新的方差或 SESOI。

## 题级

`per-query.json`：冻结 224 题与本次 224 题 id 集合相同。

| 检查（k10） | 不一致题数 |
|---|---:|
| `relevant` | 0 |
| `lexical_ranked` 全序 | 0 |
| `neural_ranked` 全序 | 0 |
| lexical hit 0/1（`recall`） | 0 |
| neural hit 0/1（`recall`） | 0 |
| lexical / neural 的 MRR、nDCG | 0 |

k30 不是产品基线点（生产只把 hybrid 的 top-10 送进 cross-encoder）。本次脚本仍按原流程加报了 k30：名次与 hit 0/1 也逐题相同。k30 不进入上面的通过判断。

两份 `per-query.json` 的文件 sha256 不同。逐叶对照后，不同的字段只有 `k10`/`k30` 的 `lexical_s` 与 `neural_s`（每题重排墙钟，224 题 × 4 个字段）。名次与 hit 不在这些字段里。

## p95 与其它非排序字段

p95 只计重排本身，不含 hybrid 检索，不含加载。预注册写明 p95 可漂，不挡排序一致。

| 字段 | 冻结 | 本次 | 差（本次 − 冻结） |
|---|---:|---:|---:|
| k10 lexical p95 ms | 3.2369630007451633 | 2.886876000047778 | -0.3500870006973855 |
| k10 neural p95 ms | 434.1544819999399 | 433.7633459999779 | -0.391135999961989 |
| k30 lexical p95 ms | 7.125296000594972 | 6.808449999994082 | -0.31684600060088997 |
| k30 neural p95 ms | 1371.0923300004652 | 1347.4492790000454 | -23.643051000419746 |
| 首次加载 `load_s` | 8.242696646000695 | 5.4494102859999884 | -2.7932863600007067 |
| `weight_bytes` | 1129561896 | 1129559830 | -2066 |

`weight_bytes` 是缓存路径中含 `reranker` 的文件按 inode 去重后的字节和，不是排序指标。差 2066 字节不改变题级名次。

`recommendation` 字段仍是「建议另开切换票」。`recommendation_paragraph` 只把其中的 p95 换成了本次的 `433.7633459999779`。那四条实验取舍不是本页的产品通过线，本页不据此改生产臂。

## 运行命令

零付费 LLM。进程环境去掉 `DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY`、`MOONSHOT_API_KEY`，不读取它们的值。未调用 `run_retrieve_x1.py`，未调用 `freshlatch.eval` 的 `run` / `control` / `control-c`。

dump 用临时 venv 里的 fastembed 0.7.1。score 用已安装的产品针 fastembed 0.8.1。没有改 `requirements.txt` 或 `pyproject.toml`。

```bash
python3 -m venv /tmp/qg04-dump-venv
/tmp/qg04-dump-venv/bin/pip install 'fastembed==0.7.1' 'jieba==0.42.1' 'rank-bm25==0.2.2'

env -u DASHSCOPE_API_KEY -u DEEPSEEK_API_KEY -u MOONSHOT_API_KEY \
  PYTHONPATH=src \
  FASTEMBED_CACHE_PATH=/tmp/qg04-fastembed-cache \
  HF_HUB_DISABLE_TELEMETRY=1 \
  /tmp/qg04-dump-venv/bin/python scripts/run_neural_rerank_compare.py dump \
  --out /tmp/qg04-candidates.json

env -u DASHSCOPE_API_KEY -u DEEPSEEK_API_KEY -u MOONSHOT_API_KEY \
  FASTEMBED_CACHE_PATH=/tmp/qg04-fastembed-cache \
  HF_HUB_DISABLE_TELEMETRY=1 \
  python3 scripts/run_neural_rerank_compare.py score \
  --candidates /tmp/qg04-candidates.json \
  --out docs/evidence/quality-gate/qg04-rerun \
  --cache-dir /tmp/qg04-fastembed-cache
```

dump 日志：`wrote /tmp/qg04-candidates.json n_arm=224 chunks=794`，退出码 0。候选文件含 chunk 文本，留在 `/tmp`，不入库。

score 日志退出码 0。stdout 末行给出的 k10 p95 与 nDCG 与 `qg04-rerun/summary.json` 一致。

## 环境

| 项 | dump | score |
|---|---|---|
| 解释器 | `/tmp/qg04-dump-venv`（临时，未写入生产依赖） | 工作区已安装的 Python 3.12.3 |
| fastembed | 0.7.1 | 0.8.1 |
| onnxruntime | 1.31.0（0.7.1 解析出的临时依赖） | 1.30.0（产品钉） |
| numpy | 2.5.4 | 2.4.4 |
| 设备 | CPU。可用 provider 为 `AzureExecutionProvider`、`CPUExecutionProvider`，无 CUDA | 同左。`TextCrossEncoder(..., cuda=False)`，`cost.json` 的 `cuda` 为 false |
| embedding | `BAAI/bge-small-zh-v1.5`，dim 512 | 不重新嵌入；读 dump 候选 |
| 精排 | 不做 | `BAAI/bge-reranker-base`，fastembed `TextCrossEncoder` |
| 融合 / 模式 | hybrid 候选；脚本断言 `PRODUCTION_RETRIEVAL_MODE=hybrid+rerank` | 同左 |
| 缓存 | `/tmp/qg04-fastembed-cache` | 同一缓存目录 |

主机：Linux x86_64。两份日志里没有上述三个 API key 的名字。

`qg04-rerun/RESULT.md` 是脚本原样写出的。其中「生产 `requirements.txt` 仍是 fastembed==0.7.1」是脚本模板里的历史句子（与冻结 `docs/evidence/neural-rerank/RESULT.md` 相同）。现行生产钉是 `fastembed==0.8.1`。本次没有改脚本，所以没有改这句模板。

## 本次没有改的东西

- `scripts/run_neural_rerank_compare.py`
- `docs/evidence/quality-gate/PREREG.md`
- `docs/evidence/neural-rerank/` 下已冻结的 `PREREG.md`、`RESULT.md`、`summary.json`、`per-query.json`、`cost.json`
- `PRODUCTION_RETRIEVAL_MODE`、`requirements.txt`、`pyproject.toml`

证物副本在 `docs/evidence/quality-gate/qg04-rerun/`（`summary.json`、`per-query.json`、`cost.json`、脚本写出的 `RESULT.md`）。
