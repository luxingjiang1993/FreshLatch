# TASK / ticket — RET-01.6

## Ticket
- **ID**: RET-01.6
- **Title**: `spike(eval): x1 三臂复跑落盘与书面结论`
- **Paths**:
  - 运行期新建 `data/dense/x1-index.sqlite`（`data/dense/` 已 gitignore，不入库）
  - 运行期使用 `data/dense/x1-embed-cache.sqlite`（同样不入库）
  - 新建 `reports/x1/dense-rebuild-x1.md`
  - 新建 `reports/x1/retrieve-x1-arm-compare.md` 与 `.json`
  - 新建 `docs/evidence/retrieve-x1/RESULT-<YYYYMMDD>.md`（日期用跑分当天）
- **Executor**: 人触发或人批准的执行。需要 `DASHSCOPE_API_KEY`。花费不得超过 ¥10。不进任何 `/implement` 批队列。看到任一臂的分数之后，不得改指标定义、阈值、题集或语料。
- **先读**: `docs/evidence/retrieve-x1/PREREG.md` 与 `tasks/RET-01.md` 的报告列、预算、主人待定里的免费额度与端点计费

缺密钥时停，不要编造向量或分数。人尚未批准本票时，即使估算低于 10 元也不发请求。

## 步骤

1. 冻结门：`git show main:docs/evidence/retrieve-x1/PREREG.md` 成功，且该内容含一行 `owner_freeze: confirmed`。工作区里的 `docs/evidence/retrieve-x1/PREREG.md` 与 `main` 上该文件字节相同。任一不成立则退出非 0，不发 API。
2. `python scripts/run_retrieve_x1.py --check-only --corpus data/exp/x1/corpus --traps data/exp/x1/traps --questions data/eval/retrieve_x1.json --config data/exp/x1/config.json --prereg docs/evidence/retrieve-x1/PREREG.md` 退出 0。三行指纹不符则停，退回 RET-01.3 / RET-01.4，不要改题迁就。
3. 任何 `embed_texts` 之前先跑 `python scripts/run_retrieve_x1.py --estimate-only --cache data/dense/x1-embed-cache.sqlite --config data/exp/x1/config.json`（契约在 RET-01.5）。它打印 `uncached_chars`、`est_tokens = uncached_chars / 1.39`（标「估」）、`est_cny = est_tokens / 1000000 * 0.5`（`text-embedding-v4` 输入标价 ¥0.5 / 百万 tokens，父票所引，本票未重拉网页）。退出非 0 或人还没批准时，不继续建库。把同一组数字抄进 RESULT。
4. 建库（不传参的旧命令不要用）：

```bash
python scripts/build_dense_index.py --corpus data/exp/x1/corpus --traps data/exp/x1/traps --db data/dense/x1-index.sqlite --report reports/x1/dense-rebuild-x1.md --cache data/dense/x1-embed-cache.sqlite
```

5. `python scripts/run_retrieve_x1.py --dense-db data/dense/x1-index.sqlite --cache data/dense/x1-embed-cache.sqlite --config data/exp/x1/config.json --out reports/x1 --prereg docs/evidence/retrieve-x1/PREREG.md`
6. 按 PREREG 的 Δ 规则，在 RESULT 里对每个 qtype 写领先 / 持平 / 落后，并附逐题胜平负。文首写「实验轨，非改臂授权」。hybrid 不赢照样归档，进程在报告写完且未超预算时退出 0。主 R@10 / MRR 不含 `score_role: guardrail` 的跨快照旧版题。
6b. 同一份 RESULT 按 PREREG 另写，且不改主结论：护栏通过或失败（T1 查询对旧快照块的命中必须为 0）；conflict-pair ordering accuracy；三个子集（8-gram 比例 = 0、比例 ≤ 0.1、字符 LCS < 0.8）的 n 与领先 / 持平 / 落后，n≥15 才写稳健或不稳健，n<15 只报 n；草稿上 0.2 / 0.35 / 0.5 的去污染命中数（抄 PREREG / `SOURCES.md`，不重写正式 config）。关掉 `as_of` 的诊断若跑了，单独一节并写明不进主结论；没跑就写「未跑」。
7. 成本：预跑估算、embed 调用次数、缓存命中、标「估」的 token、聊天 token（本路径应为 0）、估算 CNY。跑完合计超过 `budget_cny_max`（10）则在 RESULT 记录超限，退出非 0。免费额度是否有效、`dashscope.aliyuncs.com` 与文档端点是否同价，都写「未核实」，不要把估算写成已抵扣后的账单。有控制台账单时把偏差补进 RESULT，不改 PREREG。

出分前的脚本崩溃可以修 `scripts/run_retrieve_x1.py` 或 `retrieve_typed.py` 的故障，修完整轮重跑，RESULT 记一笔。出分之后发现「想换个聚合方式」：停，另开票。那是在改预登记。

## Agent Guards
- **Blast**: none（新的 sqlite 路径；不改产品库，不改生产臂）
- **Trust**: Watch
- **Acceptance**:
  1. Given `git show main:docs/evidence/retrieve-x1/PREREG.md`，When 读取，Then 含 `owner_freeze: confirmed`，且与工作区该文件字节相同。否则不得出现任何 DashScope 请求。
  2. Given 步骤 2 的 `--check-only`，When 执行，Then 退出码 0，且打印的各 qtype n、trap 比例、chunk 数与三行指纹和 PREREG 一致。
  3. Given 尚未调用 API，When 读预跑估算，Then 有 `uncached_chars`、`est_tokens`、`est_cny`。`est_cny` > 10 时没有后续嵌入请求。
  4. Given 建库与复跑，When 读 `reports/x1/retrieve-x1-arm-compare.md`，Then 含「总体 / lexical / paraphrase / multi_hop / trap+adversarial」五行与 RET-01 规定的各列；dense / hybrid 的 `last_retrieval_mode` 诚实；`arm_pass_line` 标为参考。
  5. Given `docs/evidence/retrieve-x1/RESULT-<YYYYMMDD>.md`，When 阅读，Then 每个 qtype 有领先 / 持平 / 落后，有逐题胜平负，有「实验轨，非改臂授权」，含预跑估算，花费 ≤ 10 元或明确写了超限中止。免费额度与端点同价两项为「未核实」。主 R@10 不含护栏题。另有护栏通过/失败、conflict-pair ordering accuracy、三个子集（n<15 的不称稳健）、草稿三档命中数。`as_of` 关闭的诊断若出现，在单独一节，且不改主结论。
  6. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。开工前与收工后各跑 `python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"`，两行相同。`git status` 不得出现 `data/dense/x1-index.sqlite` 的待入库文件。
- **Tests**: waived（真分不进 CI。脚本单测已在 RET-01.5。本票证据是报告与 RESULT）
- **Rollback**: 删除 `reports/x1/` 与 `docs/evidence/retrieve-x1/RESULT-*.md`；本地删除 `data/dense/x1-*.sqlite`。不回滚 PREREG，除非宣布本轮无效
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`docs/evidence/retrieve-x1/PREREG.md`、`data/exp/x1/**`、`data/eval/retrieve_x1.json`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`

### Provenance status
- result: pass
- notes: 执行票不改生产代码路径。脚本契约以 RET-01.5 为准。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a（除非出分前修了脚本故障；修了则补 compileall）
- tests: waived
- paths:

## Handoff
`2026-10-06 | RET-01.6 | blocked | 等人把 owner_freeze 合入 main，且 RET-01.5 已合并。不进 /implement 队列。无 API key 或未批准则停`

## Blocked by
- RET-01.4
- RET-01.5
- 主人冻结确认：`docs/evidence/retrieve-x1/PREREG.md` 中的 `owner_freeze: confirmed` 已合入 `main`
