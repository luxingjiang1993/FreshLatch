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
- **Executor**: 执行票。PREREG 已在 main 上之后，用 RET-01.5 的脚本跑真分并写结论。看到任一臂的分数之后，不得改指标定义、阈值、题集或语料。
- **先读**: `docs/evidence/retrieve-x1/PREREG.md` 与 `tasks/RET-01.md` 的报告列、预算、主人待定第 3 项

缺 `DASHSCOPE_API_KEY` 时停，不要编造向量或分数。

## 步骤

1. `python scripts/run_retrieve_x1.py --check-only --corpus data/exp/x1/corpus --traps data/exp/x1/traps --questions data/eval/retrieve_x1.json --config data/exp/x1/config.json --prereg docs/evidence/retrieve-x1/PREREG.md` 退出 0。指纹不符则停，退回 RET-01.3 / RET-01.4，不要改题迁就。
2. 建库（不传参的旧命令不要用）：

```bash
python scripts/build_dense_index.py --corpus data/exp/x1/corpus --traps data/exp/x1/traps --db data/dense/x1-index.sqlite --report reports/x1/dense-rebuild-x1.md --cache data/dense/x1-embed-cache.sqlite
```

3. `python scripts/run_retrieve_x1.py --dense-db data/dense/x1-index.sqlite --cache data/dense/x1-embed-cache.sqlite --config data/exp/x1/config.json --out reports/x1 --prereg docs/evidence/retrieve-x1/PREREG.md`
4. 按 PREREG 的 Δ 规则，在 RESULT 里对每个 qtype 写领先 / 持平 / 落后，并附逐题胜平负。文首写「实验轨，非改臂授权」。hybrid 不赢照样归档，进程在报告写完且未超预算时退出 0。
5. 成本：embed 调用次数、缓存命中、标「估」的 token、聊天 token（本路径应为 0）、估算 CNY。合计超过 `budget_cny_max`（10）则中止，并在 RESULT 记录超限，退出非 0。免费额度是否有效、`dashscope.aliyuncs.com` 与文档端点是否同价，都写「未核实」，不要把估算写成已抵扣后的账单。有控制台账单时把偏差补进 RESULT，不改 PREREG。

出分前的脚本崩溃可以修 `scripts/run_retrieve_x1.py` 或 `retrieve_typed.py` 的故障，修完整轮重跑，RESULT 记一笔。出分之后发现「想换个聚合方式」：停，另开票。那是在改预登记。

## Agent Guards
- **Blast**: none（新的 sqlite 路径；不改产品库，不改生产臂）
- **Trust**: Watch
- **Acceptance**:
  1. Given 步骤 1 的 `--check-only`，When 执行，Then 退出码 0，且打印的各 qtype n、trap 比例、chunk 数、指纹与 PREREG 一致。
  2. Given 步骤 2 与 3，When 读 `reports/x1/retrieve-x1-arm-compare.md`，Then 含「总体 / lexical / paraphrase / multi_hop / trap+adversarial」五行与 RET-01 规定的各列；dense / hybrid 的 `last_retrieval_mode` 诚实；`arm_pass_line` 标为参考。
  3. Given `docs/evidence/retrieve-x1/RESULT-<YYYYMMDD>.md`，When 阅读，Then 每个 qtype 有领先 / 持平 / 落后，有逐题胜平负，有「实验轨，非改臂授权」，估算成本 ≤ 10 元或明确写了超限中止。免费额度与端点同价两项为「未核实」。
  4. Given 本票 diff，When `git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/eval/__main__.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps data/dense/index.sqlite reports/dense-rebuild.md "reports/retrieve-hard-gold-*"`，Then 输出为空。`git status` 不得出现 `data/dense/index.sqlite` 或 `data/dense/x1-index.sqlite` 的待入库文件。
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
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`docs/evidence/retrieve-x1/PREREG.md`、`data/exp/x1/**`、`data/eval/retrieve_x1.json`

### Provenance status
- result: pass
- notes: 执行票不改生产代码路径。脚本契约以 RET-01.5 为准。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a（除非出分前修了脚本故障；修了则补 compileall）
- tests: waived
- paths:

## Handoff
`2026-10-06 | RET-01.6 | blocked | 等 PREREG 冻结且 RET-01.5 已合并。无 API key 则停`

## Blocked by
- RET-01.4
- RET-01.5
