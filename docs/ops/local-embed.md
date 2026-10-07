# 本地 embedding 部署

生产默认是 `hybrid+rerank`。精排是本地 `BAAI/bge-reranker-base`（fastembed `TextCrossEncoder`，CPU），只重排 hybrid 的 top-10。依据是 [PR #293](https://github.com/luxingjiang1993/FreshLatch/pull/293) 的 MRR@10 / nDCG@10，切换票是 [Issue #294](https://github.com/luxingjiang1993/FreshLatch/issues/294)。K=30 的 p95 超过 800 ms，生产不把 30 条送进 cross-encoder。

对外检索之前必须先预热两份权重：embedding 与 reranker。查询侧或 chunk 侧没有可用向量时，记录是 `bm25_fallback`。reranker 权重缺失或推理报错时打 warning，退回 `rerank_lexical`，并记 `last_rerank_mode=lexical_fallback`。

embedding 模型是 `BAAI/bge-small-zh-v1.5`，库是 fastembed `0.8.1`，维度 512。这不是阿里云 DashScope 的 `text-embedding-v4`，预热脚本不读付费 API key。`0.7.1` 没有 `TextCrossEncoder`，所以生产钉在 `0.8.1`。

reranker 权重约 1.1GB（inode 去重 1129561896 字节，其中 `onnx/model.onnx` 1112459588 字节）。首次加载约 8 秒（#293 记了 8.242696646000695 秒）。K=10 重排 p95 约 434 ms（#293 记了 434.1544819999399 ms）。这两项都不含 hybrid 检索。

## 切换后必须先预热

1. 安装 `requirements.txt`（含 `fastembed==0.8.1`）。
2. 把 `FASTEMBED_CACHE_PATH` 设成持久目录。未设置时，fastembed 用临时目录下的 `fastembed_cache`，重启后权重会丢。
3. 在能访问模型仓库的机器上跑 `python scripts/warmup_local_embed.py`。成功时标准输出一行：`ok model=BAAI/bge-small-zh-v1.5 dim=512 rerank=BAAI/bge-reranker-base cache_dir=...`。这一步同时下载 embedding 和 reranker。
4. 把该缓存目录带到要上线的机器，并设置同一个 `FASTEMBED_CACHE_PATH`。离线机器再设 `HF_HUB_OFFLINE=1` 或 `FRESHLATCH_EMBED_OFFLINE=1`。
5. 入库路径会挂本地 embedder（`FRESHLATCH_LOCAL_EMBED` 未设置时默认挂上）。已有库如果 `SQLiteStore.count_missing_vecs()` 不是 0，这些 chunk 不进 dense 打分；整池都没有可用向量时，这次检索记 `bm25_fallback`。

## 回退

不需要删权重。

- 一键回到 BM25：`set_retrieval_switch("bm25")`。之后的 `try_retrieve` 记 `retrieval_mode=bm25`，`rerank_mode=none`。
- 只把精排切回词重叠：`set_retrieval_switch("hybrid+rerank_lexical")`。记录是 `retrieval_mode=hybrid+rerank_lexical`，`rerank_mode=lexical`。
- 回到神经精排：`set_retrieval_switch("hybrid+rerank")`。成功时 `rerank_mode=bge-reranker-base`。

这三档都不改 `PRODUCTION_RETRIEVAL_MODE`。进程重启且没有再次设置开关时，沿用常量 `hybrid+rerank`，精排是 `BAAI/bge-reranker-base`。

缺向量时不要把结果标成 hybrid 或 hybrid+rerank。降级标记仍是 `bm25_fallback`。reranker 失败时检索臂仍记 `hybrid+rerank`，精排标记必须是 `lexical_fallback`，并打 warning。不得静默。

## 缓存目录

fastembed 的 `cache_dir` 来自环境变量 `FASTEMBED_CACHE_PATH`。

未设置时，fastembed 用自己的默认缓存（临时目录下的 `fastembed_cache`）。生产环境应设成持久目录，避免重启后权重丢失。

运行中的进程和预热脚本读同一个变量。

## 有网预热

在能访问模型仓库的机器上：

```bash
pip install -r requirements.txt
export FASTEMBED_CACHE_PATH=/var/cache/freshlatch-embed
python scripts/warmup_local_embed.py
```

成功时标准输出一行：`ok model=BAAI/bge-small-zh-v1.5 dim=512 rerank=BAAI/bge-reranker-base cache_dir=...`。

把该目录带到离线机器，并在离线机器上设置同一个 `FASTEMBED_CACHE_PATH`。

## 离线

任一条件成立时，加载不会尝试下载：

- `HF_HUB_OFFLINE=1`
- `FRESHLATCH_EMBED_OFFLINE=1`

缓存里没有 embedding 权重时，进程抛出 `LocalEmbedUnavailable`。信息里有 `model=`、`cache_dir=`、`exc_type=`，并指向 `python scripts/warmup_local_embed.py`。

缓存里没有 reranker 权重，或推理报错时，在线检索不抛出：打 warning，退回 `rerank_lexical`，`last_rerank_mode=lexical_fallback`。warning 里有 `model=BAAI/bge-reranker-base`、`cache_dir=`、`exc_type=`。预热脚本本身在这一步失败时退出码 1，标准错误同样带模型名和缓存目录。离线直接跑预热时，两条不可用信息都会打出来（embedding 与 reranker）。

离线状态下直接跑预热脚本会以退出码 2 结束，不会发起下载。

入库时如果 `chunk_embedder` 抛错，SQLite 写入仍会继续，但会打一条 warning：`doc_id`、`exc_type`、`missing_vecs`。正文变了的 chunk 不会留下旧 `vec`。库内缺向量的总数用 `SQLiteStore.count_missing_vecs()` 查询。

## 测试

pytest 在 `tests/conftest.py` 里把 `FRESHLATCH_LOCAL_EMBED=0` 和 `FRESHLATCH_NEURAL_RERANK=0`。单测不挂本地 embedder，不构造 `TextCrossEncoder`，不下载权重。精排行为用 mock 编码器断言。生产进程不要设置 `FRESHLATCH_NEURAL_RERANK=0`。
