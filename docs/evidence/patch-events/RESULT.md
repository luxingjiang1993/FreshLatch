# patch_events 结果

这是结果表。口径在 `PREREG.md`。本页不回写预注册。n=30 的 Cohen's κ 与 Fleiss' κ 按仓库 `agreement` 写入。共形预留 false-accept rate 上界是「未做」。语料缺额是 0。其余该填数字的格子仍是「未填」。这里没有四臂估计，没有 pilot 数字，没有逐条评委标签，没有抽检答案。

主指标是固定放行率下的 false-accept rate。预注册里的名字是误放率。误拒率同时留格。错改率、可复验率、延迟、成本留格，不参与「成立」。

四条臂是 C、T（fail-closed）、B1、B2。主比较顺序是 T 对 C、T 对 B1、T 对 B2。配对差 = 对照的 false-accept rate − T 的 false-accept rate。这些格子不填。

消融只在 T 上，放在三条主比较之后，不改主比较的判决。检索消融把脚本里的检索臂换成 BM25，并另记一列 hybrid+rerank。生产检索仍是 hybrid+rerank。本页不改这一赋值。

## 各臂

| 臂 | 自然放行数 | 自然放行率 | 固定放行率 false-accept rate | 固定放行率误拒率 | 固定放行率错改率 | 固定放行率可复验率 | 延迟中位数 | 延迟 p95 | 成本 |
|---|---|---|---|---|---|---|---|---|---|
| C | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 |
| T（fail-closed） | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 |
| B1 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 |
| B2 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 | 未填 |

| 项目 | 值 |
|---|---|
| 固定放行数 k | 未填 |
| 共形预留 false-accept rate 上界 | 未做 |
| 语料缺额 | 0 |

## 主比较

| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立 |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 C | 误拒率 | 未填 | 未填 | 未填 | 未填 |
| T 对 C | 错改率 | 未填 | 未填 | 未填 | 未填 |
| T 对 C | 可复验率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | 误拒率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | 错改率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | 可复验率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B2 | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 B2 | 误拒率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B2 | 错改率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B2 | 可复验率 | 未填 | 未填 | 未填 | 未填 |

## 消融

| 消融 | 预注册说法 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 |
|---|---|---|---|---|---|
| no_chunk_bind | 拿掉 chunk 绑定 | false-accept rate | 未填 | 未填 | 未填 |
| no_chunk_bind | 拿掉 chunk 绑定 | 误拒率 | 未填 | 未填 | 未填 |
| no_chunk_bind | 拿掉 chunk 绑定 | 错改率 | 未填 | 未填 | 未填 |
| no_chunk_bind | 拿掉 chunk 绑定 | 可复验率 | 未填 | 未填 | 未填 |
| no_auto_verify | 拿掉自动核验 | false-accept rate | 未填 | 未填 | 未填 |
| no_auto_verify | 拿掉自动核验 | 误拒率 | 未填 | 未填 | 未填 |
| no_auto_verify | 拿掉自动核验 | 错改率 | 未填 | 未填 | 未填 |
| no_auto_verify | 拿掉自动核验 | 可复验率 | 未填 | 未填 | 未填 |
| soft_warning | hard reject 换成 soft warning | false-accept rate | 未填 | 未填 | 未填 |
| soft_warning | hard reject 换成 soft warning | 误拒率 | 未填 | 未填 | 未填 |
| soft_warning | hard reject 换成 soft warning | 错改率 | 未填 | 未填 | 未填 |
| soft_warning | hard reject 换成 soft warning | 可复验率 | 未填 | 未填 | 未填 |
| retrieval_bm25 | 检索臂换成 BM25 | false-accept rate | 未填 | 未填 | 未填 |
| retrieval_bm25 | 检索臂换成 BM25 | 误拒率 | 未填 | 未填 | 未填 |
| retrieval_bm25 | 检索臂换成 BM25 | 错改率 | 未填 | 未填 | 未填 |
| retrieval_bm25 | 检索臂换成 BM25 | 可复验率 | 未填 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | false-accept rate | 未填 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 误拒率 | 未填 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 错改率 | 未填 | 未填 | 未填 |
| hybrid+rerank | 另记一列，不进入主比较 | 可复验率 | 未填 | 未填 | 未填 |

## 评委与抽检

| 题 | 配对 | Cohen's κ | 条数 |
|---|---|---|---|
| A | qwen-deepseek | 0.926829268292683 | 30 |
| A | qwen-kimi | 0.7715736040609137 | 30 |
| A | deepseek-kimi | 0.8421052631578947 | 30 |
| B | qwen-deepseek | 0.926829268292683 | 30 |
| B | qwen-kimi | 0.7804878048780488 | 30 |
| B | deepseek-kimi | 0.85 | 30 |

| 题 | Fleiss' κ | 条数 |
|---|---|---|
| A | 0.8473713962690785 | 30 |
| B | 0.8523783488244943 | 30 |

| 项目 | 值 |
|---|---|
| 抽检一致率 | 未填 |
| 用户对评委的 Cohen's κ | 未填 |
