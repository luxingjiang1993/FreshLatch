# 本地 embedding 部署

生产检索默认仍是 BM25。`PRODUCTION_RETRIEVAL_MODE` 保持 `bm25`。本文只说明如何把本地 embedding 权重准备好，不授权切换到 hybrid。

模型是 `BAAI/bge-small-zh-v1.5`，库是 fastembed，维度 512。这不是阿里云 DashScope 的 `text-embedding-v4`，预热脚本不读付费 API key。

rerank 仍是 `rerank_lexical`（jieba token overlap），这里不下载神经 reranker。

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

成功时标准输出一行：`ok model=BAAI/bge-small-zh-v1.5 dim=512 cache_dir=...`。

把该目录带到离线机器，并在离线机器上设置同一个 `FASTEMBED_CACHE_PATH`。

## 离线

任一条件成立时，加载不会尝试下载：

- `HF_HUB_OFFLINE=1`
- `FRESHLATCH_EMBED_OFFLINE=1`

缓存里没有权重时，进程抛出 `LocalEmbedUnavailable`。信息里有 `model=`、`cache_dir=`、`exc_type=`，并指向 `python scripts/warmup_local_embed.py`。

离线状态下直接跑预热脚本会以退出码 2 结束，不会发起下载。

入库时如果 `chunk_embedder` 抛错，SQLite 写入仍会继续，但会打一条 warning：`doc_id`、`exc_type`、`missing_vecs`。正文变了的 chunk 不会留下旧 `vec`。库内缺向量的总数用 `SQLiteStore.count_missing_vecs()` 查询。

## 测试

pytest 在 `tests/conftest.py` 里把 `FRESHLATCH_LOCAL_EMBED=0`。单测不挂本地 embedder，不下载权重。
