# 跑数据前偏离草稿 · 扩充公开语料

状态：待用户确认。本页不是已生效决定。不改 `PREREG.md`，不改配额，不改构造算子。

日期：2026-10-08。拟定记录人：Ronin 代理人。此时尚无 pilot，也尚无正式评委数据。

## 预注册原文

`docs/evidence/patch-events/PREREG.md` 样本框：

- 只有第一课题 `thesis-1`：`data/t0_docket.json` 的主张，证据来自 `data/corpus/t1` 与对应的 `data/corpus/t0`。
- 合成语料。不用 KPR 的 benchmark，不用医疗指南，不做第二领域。
- 语料不够就把缺额写进结果，不在本页把配额改小，主比较不成立。

同页还写着：本页不改 `data/corpus`。

按这三句，在看见缺额之后另抓一批真实公开文本，并改用新的 docket，属于开跑前偏差。维持原合成语料、把缺额写进结果，则不是偏差。

## 若确认，拟记录的内容

1. 新语料放在 `data/corpus/pe_v2/`，主张放在 `data/pe_v2_docket.json`。不改 `data/corpus/t0`、`data/corpus/t1`、`data/t0_docket.json` 和金标。
2. 文本来自国家法律法规数据库现行有效法律、行政法规、地方性法规、司法解释的 2026-08-26 快照（`senry5433/china-effective-laws-regulations`，汇编许可 CC0-1.0）。官网入口是 https://flk.npc.gov.cn/ 。正文按《著作权法》第五条视为立法、行政、司法性质文件。网站使用条款未逐页核验。
3. 每条主张都能在来源全文里逐字定位。不用模型生成的句子充当语料。抓取时间、许可、来源 URL、来源 sha256 和本仓文件 sha256 记在 `data/corpus/pe_v2/PROVENANCE.json`。
4. 配额和算子不改。`construct_samples` 仍不产出共形预留。清单见 `docs/evidence/patch-events/SPLIT-pe-v2.json`。四层在 pilot 与 n=100 之后各留下不少于 5 条未使用主张。
5. 数值里有 8 条使用了同一标题的另一版本日期。日期和条款替换大多是同一现行文本中的两段原文。删除层的证据句有时来自另一部公开文本中含有同一限定语的句子。
