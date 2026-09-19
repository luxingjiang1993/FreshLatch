# 存储与检索:SQLite + BM25,多 stage 管线留位,弃 Chroma / FAISS 混合

语料存储与检索层采用 **SQLite + BM25(路线 B)**:chunk 存 SQLite,`as_of=T0|T1` / `source_type` 过滤是 WHERE 子句;打分层设计为多 stage 管线(`recall → [vector] → [rerank]`),本期只实装 BM25(`rank_bm25` + `jieba`),vector / rerank stage 为骨架空实现,`vec` 列已入 schema。

**为什么**:第一判据是元数据过滤干净(as_of 换源是产品核心动作)与金标可复现(评测期运行时纯本地),不是召回上限。规模经济学:20–30 篇(立项切片红线,数百 chunk)到几百篇,暴力打分都是毫秒级,FAISS 要到十万级向量才有存在价值;其结构性短板(元数据过滤脏、faiss-cpu/torch 重依赖、reranker 权重数百 MB)不随规模变好。Chroma 的唯一增量优势 SQLite 零成本同得。RAG 工程手段(假设性问题、parent-document、HyDE、MultiQuery、rerank 等 24 项)登记于 `docs/research/检索路线选型评估.md` 第 7 册,按处置分级:【实装】【留位】【承载】【触发】【弃】;一切 LLM 参与的检索增强由熔断条件触发——金标命中回放(must_stale 证据块须在 top_k)不过,才在对应工单打点菜。

**后果**:Chunk schema 定稿 `doc_id, chunk_id, clause_id, title, text, source_type, as_of, doc_version, checksum, tokens, parent_id(留位), hypo_questions(留位), vec(留位)`;引用模型沿用 `rag.py` 的 Chunk/RagCitation 扩展;语料 checksum 与污染文档位按数据+测试双留位落位(本期不启用);embedding 路启用形态已定(DashScope `text-embedding-v4` ingestion 期预计算、运行时本地余弦,不出网)。对应工单 [#5](https://github.com/luxingjiang1993/FreshLatch/issues/5)。
