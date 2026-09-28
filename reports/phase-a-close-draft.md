# Phase A 关门草稿（#166，待真人终收）

本页是编排器起草的汇总，不是代批，也不是关单。n 为冒烟级，不声称统计显著，不报方差。交付分支：`cursor/freshlatch-phase-a-orchestration-9fd9`，见 PR #167。

## 各臂与基线

| 臂 | Recall@10 | 备注 |
| --- | --- | --- |
| A0 BM25 基线 | 1.0000 | MRR@10=0.7324；Recall@5=1.0000；n=36 |
| dense | 0.9722 | text-embedding-v4，本地余弦 |
| hybrid（RRF k=60） | 1.0000 | >= min(BM25, dense)，通过线 pass |
| hybrid+rerank | 1.0000 | 与 hybrid 持平，非严格更好 |

- BM25 相对 A0 容差 0：pass。
- must_stale 回放：pass。
- rerank：p95=11.4ms，未同时满足「Recall@10 严格更好且 p95≤800ms」，**生产默认关**。代码 `PRODUCTION_RETRIEVAL_MODE` 仍是 `bm25`。
- 陷阱三类与主金标分列，各 1 条，子集 Recall@10=1.0000，不计入主指标 n。元陈述只标干扰。
- 变换对比 n=10：裸 statement 与模板变换 Recall@10 均为 1.0000。默认不调用 LLM。

分列原文：

- `reports/retrieve-bm25-baseline.md`
- `reports/retrieve-arm-compare.md`
- `reports/retrieve-rerank-compare.md`
- `reports/retrieve-traps.md`
- `reports/retrieve-transform-compare.md`

## 语料 checksum

- corpus：`a1a35e9b55f48eaf4381a27855db987c3c5870fb6a43d4458829bcbacc5b0b04`
- retrieve 金标：`a62830b3c9e5b9fd10484ed06aa182d7a1ac25c0ca8cad739329230577f58255`
- 聚合：`00a43c88db4522a8d5bb2ebe821c0e22c81302a9ed1a117ed5b64932afc60bcb`
- 语料文件数 28，chunk 数 84。日期 2026-09-28。

## 索引重建

1. 在环境中配置 `DASHSCOPE_API_KEY`。不要把密钥写入仓库、报告或 Issue。
2. 运行 `PYTHONPATH=src python3 scripts/build_dense_index.py`。
3. 产物在 `data/dense/index.sqlite`（已 gitignore），存储是 SQLite `chunks.vec`，不是 FAISS。
4. 本次重建记录见 `reports/dense-rebuild.md`：模型 `text-embedding-v4`，状态 ok，chunks=84，dim=1024。
5. 复跑评测：`PYTHONPATH=src python3 -m freshlatch.eval retrieve`。

PDF 冒烟不进主指标：`data/smoke/phase-a-smoke.pdf`，重建命令 `PYTHONPATH=src python3 scripts/smoke_pdf_ingest.py`。见 `reports/phase-a-pdf-smoke.md`。

## 轨迹

`retrieve` 轨迹仍记录 query、filters、有序 `evidence_id`、`retrieval_mode`。对外主键是 `doc_id#anchor@as_of`。生产路径不能随意切臂。

## Out of Scope 未进主链

本阶段没有把下列项做成主链能力：Memory 挂载、日历生效/失效窗、开放知识点标签、主张台账、basis_rot 全链、对抗套件实跑、多 seed 消融、FAISS 换存储真相、字数窗主切块、开放联网问答。

## 本机命令

- `python3 -m compileall -q src` exit 0
- `python3 -m pytest -q tests/unit/test_store.py` exit 0（12 passed）

请真人审本草稿后自行终收 #166。编排器不代批、不关单。
