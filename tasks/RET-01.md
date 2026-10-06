# TASK / ticket — RET-01

父票 / 规格索引。本文件不授权改应用代码。实现按下方子票各开一次 `/implement`（人步骤除外）。

## Ticket
- **ID**: RET-01
- **Title**: `spike(eval): 扩语料 + 分型难题集 + 三臂复跑（bm25 / dense / hybrid）实验轨`
- **Paths**:
  - `tasks/RET-01.md`（本文件）
  - `tasks/RET-01.1.md` … `tasks/RET-01.7.md`（子票；无 `RET-01.2a`，正则不允许）
  - `tasks/CI-01.md` 不在本父票的子票计数里（main 上既有的 CI 失败，另票）
- **Pin**: 核对时 `main` = `18b5172`（`18b5172ebff535652c6166dc6cd927d4bdc3c769`）

实现路径（语料、脚本、证据）由子票拥有。本票的 diff 只应出现在 `tasks/`。

## 子票（依赖顺序）

| 顺序 | ID | 交付 | 依赖 | 谁做 |
|------|----|------|------|------|
| 1 | RET-01.1 | 许可 / 去污染 / 题集结构检查 | 无 | `/implement` |
| 2 | RET-01.2 | embedding 内容哈希缓存；`build_dense_index.py` 可选路径 | 无 | `/implement` |
| 3 | RET-01.7 | `scripts/gen_x1_drafts.py`（含抽检子命令） | RET-01.1 | `/implement` |
| 4 | RET-01.3 | 混合语料、`SOURCES.md`、`config.json`、人定金标 | RET-01.1、RET-01.2、RET-01.7。去污染阈值与 P1 摘录清单已批准。仍开放：陷阱操作化定义；冻结前 flk.npc.gov.cn 核对 | **整张是人步骤，禁止 `/implement`** |
| 5 | RET-01.4 | `PREREG.md` 正文与三行指纹 | RET-01.3 | `/implement` 只写文档 |
| 5b | RET-01.4 冻结确认 | 主人写入 `owner_freeze: confirmed` 并合入 `main` | RET-01.4 的文档已写好 | **人步骤** |
| 6 | RET-01.5 | 分型打分与 `scripts/run_retrieve_x1.py`（假向量；不跑真分） | RET-01.1、RET-01.2。不依赖 RET-01.7。可与 3、4 并行 | `/implement` |
| 7 | RET-01.6 | 同库三臂复跑、分型报告、`RESULT-<YYYYMMDD>.md` | 冻结定义成立，且 RET-01.5 已落地 | **人触发或人批准的执行**；不进任何 `/implement` 队列 |

人步骤只有两处：RET-01.3 整张，以及 RET-01.4 的冻结确认行。`RET-01.2a` / `RET-01.2b` 不符合 `docs/agents/agent-guards.md` 的 `^[A-Z]+-[0-9]+(\.[0-9]+)?$`，所以缓存留在 RET-01.2，草稿生成用 RET-01.7。

冻结定义：`docs/evidence/retrieve-x1/PREREG.md` 已在 `main` 上，且含主人写下的一行 `owner_freeze: confirmed`。起草者只能写 `owner_freeze: pending`。RET-01.6 跑分前检查这一行。

`main` 上自 `833af15` 起，`tests/unit/test_i3_hard_gold.py::test_hard_arm_compare_same_corpus_as_a0` 在无 `DASHSCOPE_API_KEY` 的 CI 里失败。那不是本实验的子票，见 `tasks/CI-01.md`。RET-01.5 的验收命令不跑这个测试。

## Agent Guards
- **Blast**: none（本票只新增 `tasks/*.md`）
- **Trust**: Watch（仓库默认；不涉 auth / db / pay）
- **Acceptance**:
  1. Given 本目录七张子票，When 执行下面的命令，Then 退出码 0，并打印 `ret-01-children-ok 7`。

```bash
python -c "from pathlib import Path; root=Path('tasks'); ids=['RET-01.1','RET-01.2','RET-01.3','RET-01.4','RET-01.5','RET-01.6','RET-01.7']; needles=['PRODUCTION_RETRIEVAL_MODE','retrieve_hard_gold.json','data/dense/index.sqlite','reports/retrieve-hard-gold-','ADR-0033','#260','ACCEPTANCE.md','RERUN-','**Blast**: none','**Trust**: Watch','hard-c4-paraphrase','hard-c6-paraphrase'];
[(_t:=(root/f'{i}.md').read_text(encoding='utf-8'), (_m:=[n for n in needles if n not in _t]) and (_ for _ in ()).throw(SystemExit(f'{i} missing {_m}'))) for i in ids]; print('ret-01-children-ok', len(ids))"
```

  2. Given 上表，When 按依赖阅读，Then 人步骤是 RET-01.3 整张，加上 RET-01.4 的 `owner_freeze: confirmed`。RET-01.6 依赖该冻结，且不进 `/implement` 队列。
  3. Given 本票 diff，When 列出路径，Then 全部位于 `tasks/`。
- **Tests**: waived（纯工单；不新增 pytest）
- **Rollback**: 删除 `tasks/RET-01.md`、`tasks/RET-01.1.md` … `tasks/RET-01.7.md`。`tasks/CI-01.md` 单独回滚
- **Do-not-touch**:
  - `PRODUCTION_RETRIEVAL_MODE` 与生产默认臂（保持 `bm25`，`src/freshlatch/store/base.py`）
  - `docs/evidence/hard-gold-arm/ACCEPTANCE.md` 的冻结结论，以及同目录 RERUN 证据（`RERUN-20261003.md`、`RERUN-20261003-259.md`）
  - GitHub issue #260（OPEN，`ready-for-human`；改臂实现，与本实验互不阻塞）
  - `data/eval/retrieve_hard_gold.json`（`hard-c4-paraphrase`、`hard-c6-paraphrase` 只作背景，不改该文件）
  - `data/dense/index.sqlite`
  - `reports/retrieve-hard-gold-*`
  - ADR-0033 正文（`docs/adr/0033-hard-gold-过线与改臂授权闸.md`）
  - 同时不改：`data/corpus/**`、`data/traps/**`、`reports/dense-rebuild.md`、`src/freshlatch/eval/__main__.py`、`src/freshlatch/eval/retrieve_eval.py`、`src/freshlatch/store/embeddings.py`、`src/freshlatch/store/ingest.py`、`src/freshlatch/llm.py`、`src/freshlatch/store/base.py`

子票验收里的 `git diff` 使用同一条路径清单（不含 `data/dense/index.sqlite`，该文件被 `.gitignore`，`git diff` 永远是空的）：

```bash
git diff --stat main -- src/freshlatch/store/base.py src/freshlatch/eval/__main__.py src/freshlatch/eval/retrieve_eval.py src/freshlatch/store/embeddings.py src/freshlatch/store/ingest.py src/freshlatch/llm.py docs/evidence/hard-gold-arm data/eval/retrieve_hard_gold.json data/corpus data/traps reports/dense-rebuild.md "reports/retrieve-hard-gold-*"
```

`data/dense/index.sqlite` 用开工前与收工后各跑一次下面的命令，两行输出必须相同：

```bash
python -c "import hashlib; from pathlib import Path; p=Path('data/dense/index.sqlite'); print('absent' if not p.is_file() else hashlib.sha256(p.read_bytes()).hexdigest(), 'absent' if not p.is_file() else p.stat().st_mtime)"
```

### Provenance status
- result: pass
- notes: 父票不改既有代码。adapt 记在 RET-01.2、RET-01.5、RET-01.7。子票 ID 使用正则里的 `RET-01.N`。`CI-01` 不是子票。

### Evidence *(after Matt `/implement`)*
- typecheck: n/a（本票无 src）
- tests: waived
- paths: `tasks/RET-01.md` · `tasks/RET-01.1.md` … `tasks/RET-01.7.md` · `tasks/CI-01.md`（范围外）

## 已锁决策（主人已定，子票不得改口）

- 语料混合 = 合成 + 部分公开宽松许可文本，配比以下表为目标。硬门槛：corpus + traps 合计 **≥600 chunk**；合成正文（`provenance: synthetic`）≥60%；公开原文（`provenance: public`）≤40%。表内约 79% / 21% 是目标，不是第二套门槛。旧的 24% 公开目标不再凑满：P1 按 RET-01.3 的 A+B 清单实装约 138 chunk（按 660 计约 20.9%），缺口约 20 chunk 用合成 S6 变更要点补。
- 题集 `qtype ∈ {lexical, paraphrase, multi_hop}`，**每个 qtype ≥30，合计 n≥90**，目标 n=90–120。`category ∈ {trap, adversarial}` 的题 ≥30%（沿用 `docs/hard-gold.md` 的预登记口径，分母是臂对比题的题数，不含 `score_role: guardrail`）。
- `multi_hop` 的 `relevant` ≥2 个锚，且来自 ≥2 个不同 `doc_id`（`@T0` / `@T1` 不算第二个文档）。现 hard 集里 `hard-trap-conflict-1` 的两个锚同属 `trap-conflict`，不能当作 multi_hop 的形状样例。另加硬检查：`answer_points`（≥2 条）不得同时出现在同一个 chunk；出现则该题不能作为 multi_hop 通过（单跳捷径）。细则在 RET-01.1。
- hybrid 领先阈值 **Δ≥0.10**：该型 R@10（hybrid − bm25）≥ 0.10 为领先，≤ −0.10 为落后，其余持平。`arm_pass_line` 只作参考列，不作改臂授权。hybrid 不赢是合格结果。主 R@10 / MRR 不含跨快照旧版陷阱。
- 去污染分两套，算法在 RET-01.1。计算重合之前，先从 query 去掉法规名白名单（点名法规是合法的）。`lexical`：清洗后的**整段 query** 长度 ≥8 且作为子串出现在任一 relevant 块的清洗正文里，才算污染。`paraphrase` / `multi_hop`：只走字符 8-gram 重合率，**严格大于** `decontam_8gram_max` 才算污染，等于阈值不判。主人已批准 `decontam_8gram_max` = **0.2**。`data/exp/x1/config.json` 在 main 上还不存在，本决议不创建它；RET-01.3 创建时写入 `0.2`。检查器在缺键或 JSON `null` 时仍退出码 2，不得把 0.2 或 0.5 当缺省代入。0.5 只留在预登记的临时敏感度对照里，不进正式配置。字符 LCS / 问句长度 ≥ 0.8 是复核旗标，不是门。
- 检索按 `as_of` 过滤。本实验不改这道过滤，不改生产臂。跨快照旧版陷阱（现有 `trap-supersede-1` 这一类：T1 问句的干扰在另一快照）不进三臂 recall / MRR，改到单独的通过/失败护栏：T1 查询对旧快照块的命中必须为 0。同快照冲突条文作 hard negative，并计 **conflict-pair ordering accuracy**（现行条文排在被取代条文之前的配对占比）。关掉 `as_of` 的诊断消融单独报告，不进主结论。指标归属由 RET-01.4 预锁。不改 `data/corpus/**`、`data/traps/**` 与 `data/eval/retrieve_traps.json`。
- 法规标题与条号只放 frontmatter，正文从条文本身起。把标题前置进 chunk（contextual retrieval）不在本期：三臂同样不做，留给以后的消融。
- 公司法按主题拆成约 4–5 类 doc，每个快照文件 2–6 个 chunk，`doc_id` 稳定。主题与 C1–C10 / G1–G14 在 RET-01.3。
- 预算帽 **¥10**，写入 `config.json` 的 `budget_cny_max`。超限停跑。
- Embedding：`text-embedding-v4`，维度 **1024**，与 `reports/dense-rebuild.md` 已记录的 dim=1024 对齐。不换模型、不传 `text_type` / `instruct` / sparse。内容哈希缓存键含 model 与 dim。
- 草稿生成：`qwen-flash`（`src/freshlatch/llm.py` 的 `DEFAULT_MODEL`）。`qwen-plus` **非思考**只标记可疑标注，不写 gold。这是主人批准的、对 `docs/spec/06-护栏预算与成本.md` §6.5「开发期统一 qwen-flash」的例外，只用于离线抽检，不进入 Lead 循环。gold（`relevant` / `distractors` / `qtype`）由人终定；另一人复核 ≥20%，记入 PREREG。
- 层身份 = 实验 / 冒烟。不报方差，不作统计显著。
- 生产臂保持 bm25。与 #260 互不阻塞。

### 语料来源表（chunk 占比目标）

场景：已签发顾问 / 战略判断，两周后复验。定位依据：`README.md`、`docs/product/FreshLatch.md`、`docs/product/FreshLatch-立项切片.md`、`CONTEXT.md`、ADR-0027、ADR-0028。主张维度以 `data/t0_docket.json` 已出现的取值为准：`competitor_pricing` / `regulatory_stance` / `interview_reversal` / `market_structure` / `cost_model` / `tech_ecosystem`。

| 体裁 | 来源 | 许可 | 目标占比 | 主要练的题型 |
|------|------|------|----------|----------------|
| S1 已签发顾问备忘（T0 签发 + T1 待复验） | 合成，D0–D3 | `synthetic` | 14% | multi_hop、paraphrase |
| S2 访谈 / 渠道纪要（含改口） | 合成 | `synthetic` | 10% | paraphrase、同快照改口。跨快照旧版只进护栏 |
| S3 竞品价目 / 报价快照 | 合成 | `synthetic` | 10% | lexical、同快照旧价。跨快照旧版只进护栏 |
| S4 内部测算 / 成本模型版本 | 合成 | `synthetic` | 8% | lexical、维度错配 |
| S5 二手转述 / 汇编（引用旧数） | 合成 | `synthetic` | 8% | 词面撞车、语义近邻旧事实 |
| S6 变更要点 / 补丁记录 | 合成 | `synthetic` | 9% | multi_hop、元陈述陷阱。含补 P1 缺口的约 20 chunk |
| S7 检索陷阱专用文档 | 合成 | `synthetic` | 10% | trap / adversarial 的语料载体。题数 ≥30% 是另一分母，见下 |
| P1 法规版本对正文 | 公开，D1 / D2 | `PRC-Copyright-Art5` | 21% | lexical、paraphrase、multi_hop、同快照冲突。跨快照旧版只进护栏 |
| P2 官方统计初值→终值，叙述自写 | 数据来自国家统计局公告，D3 | `synthetic`（注明出处） | 10% | lexical、multi_hop。跨快照旧版只进护栏 |

合计目标：合成正文约 79%（S1–S7 69% + P2 10%），公开原文约 21%。D0 约占合成部分一半，以便和现有东南亚 SMB 客服主题连续。S7 的 10% 是 **chunk** 占比；`trap`+`adversarial` ≥30% 是 **题数** 占比（分母不含护栏题）。

P1 摘录已批准，逐条表在 RET-01.3（清单 A+B，不收把令 11 / 13 / 16 收成全文的清单 C）。来源是令 11、令 13、令 16，另加令 20《个人信息出境认证办法》（2026-01-01 施行）。公司法按 RET-01.3 的主题 doc 拆，不整部入库。条号以官网正文为准。冻结前到 https://flk.npc.gov.cn/ 核对有无后续修正；这项核对仍是开放的人步骤。未列入 `SOURCES.md` 的条文不得入库。

P2 候选（本票默认，除非主人在 RET-01.3 开工前改口）：全国 GDP 初步核算 → 修订 / 最终核实。草稿所引数字（2023 年修订后 1294272 亿元、比初步核算增 33690 亿元；2024 年最终核实 1348066 亿元、比初步核算减 1018 亿元）**仓内无副本**。RET-01.3 写入前对照统计局公告，不符则以官网为准并记入 `SOURCES.md`。

许可白名单（`license` 取值即枚举）：

- `synthetic`：本仓生成。不得以版权原文为模板整段改写。
- `PRC-Copyright-Art5`：只取发文机关官网正文（全国人大网 npc.gov.cn、网信办 cac.gov.cn）。不取政策解读、负责人答记者问、新闻稿、图解。只截与主张相关的条文，不整部搬运。
- `US-Gov-17USC105`、`CC0-1.0`、`CC-BY-4.0`：规则保留在白名单里，**本票 chunk 占比必须为 0**。
- 排除：CC BY-SA（含维基百科）、NC / ND、无明确许可的网页、新闻稿、客户 / 保密数据、`excerpt_only` 摘录（`data/packs/v1-mck-soai/` 的 frontmatter 已是这种摘录，不得当扩库模板）。

`source_type` 只使用仓内已有取值 `private` / `public` / `internal`（`src/freshlatch/tools.py` 的描述；`data/corpus/t0/t0-cost-model.md` 已用 `internal`）。不新增第四种。

frontmatter 在现有 `doc_id` / `as_of` / `source_type` / `title` 之外增加：`provenance`、`license`、`domain`（`D0|D1|D2|D3`）、`genre`（`S1`–`S7` / `P1` / `P2`）。public 另加 `source_url`、`publisher`、`retrieved_at`。`CC-BY-4.0` 另加 `attribution`。P2 另加 `data_source_url` 与 `attribution: 引自国家统计局网站 www.stats.gov.cn`。`parse_document_text` 会把未知键读进 meta 再丢弃，不改解析器（`src/freshlatch/store/ingest.py`）。

切块沿用 `## pN`。目录是 `t0/` 与 `t1/`。x1 入库走 `load_corpus`（断言 `as_of` 与目录一致）。不要为了 x1 去改 `load_trap_corpus`（该函数不断言 `as_of`）。

干扰不偏袒任何一臂：词面撞车、语义近邻但事实不同、同快照冲突、元陈述（CONTEXT「检索陷阱三类」：快照取代、同快照冲突陈述、元陈述）、维度错配、近重复版本。T0→T1 跨快照旧版可以出题，但不进臂的 recall / MRR，只进护栏。字段风格沿用 `data/eval/retrieve_traps.json` 的 `distractors` 与 `eval_intent`。不改该文件，也不改 `data/traps/**`。

固定参数：`top_k=10`；RRF k=60（`freshlatch.store.pipeline.RRF_K`）。随机步骤的 temperature / seed / model 必须出现在配置里；托管端点不保证逐字复现，复现以入库产物 + checksum 为准。

## 主人待定（不得代锁）

下列事项仍未签核，或核对尚未发生。子票不得把它们写成已生效。

1. **免费额度与端点计费**。中国站「每模型 100 万 tokens、开通后 90 天」对本账号是否仍有效：未核实。是否开通 Batch：未核实。仓内端点是 `https://dashscope.aliyuncs.com/compatible-mode/v1`（`DASHSCOPE_BASE_URL`、`embeddings._ENDPOINT`）。它和文档里的 `{WorkspaceId}.cn-beijing.maas.aliyuncs.com` 是否同一标价：未核实。RET-01.6 按北京地域标价估算并执行 ¥10 帽，报告里这两项写「未核实」，不得写成已用免费额度抵扣。
2. **陷阱类型的操作化定义**。建议稿里的三类（同快照冲突、取代、未重测）主人尚未签核。已批准的只有计分规则：跨快照旧版进护栏、同快照冲突作 hard negative、conflict-pair ordering accuracy、`as_of` 关闭的诊断不进主结论。不得把未签的三类定义抄进 PREREG 当成已批准。
3. **flk 后续修正核对**。https://flk.npc.gov.cn/ 上，令 11 / 13 / 16 / 20 与公司法 2023 在入库冻结前有没有再修订：尚未核对。RET-01.3 的人在冻结前做，结果写入 `SOURCES.md`。不得预写「无修正」。

已批准、不再待定：`decontam_8gram_max` = 0.2；P1 用 A+B（含令 20），不把公开占比凑到 24%。检查器在阈值缺键或 `null` 时仍退出码 2。

草稿里其余未决项，本票也不代锁：

- 第五条适用范围与网站声明的关系是本实验的工作判断，不是法律意见。
- P2 是否改用分行业 / 分地区修订数。未改口前只用全国 GDP 两份公告的数据点，叙述自写。
- 首次建库后用控制台账单校正「估」token，校正结果写入 RESULT，不回头改 PREREG 的判据。

temperature 与 seed 没有被主人指定成某个数。生成脚本在二者缺省时必须拒绝运行。人在 RET-01.3 把选定值写入 `config.json`。`DecodingParams` 的代码默认 `temperature=0.0` 不得被脚本悄悄沿用：仓内 `__main__.py` 已写明 temp=0 时 seed 没有采样意义。

## 背景（按 `18b5172` 核对）

- 生产默认臂 `PRODUCTION_RETRIEVAL_MODE = "bm25"`（`src/freshlatch/store/base.py`）。
- #258 整门不过线。`28dc437` 的 `reports/retrieve-hard-gold-arm-compare.md`：BM25 R@10 = 0.3500，dense = 0.4500，hybrid = 0.5000，通过线 fail。同一份报告里 `hybrid >= min(BM25, dense)` 是 **pass**，fail 来自 BM25 相对 A0（A0 = 0.6000）。当时 dense 重建记录是 chunks=84（`docs/evidence/hard-gold-arm/RERUN-20261003.md`），不是后来的 94。
- #259 同库（corpus+traps）后：**过线 · 未换臂**。BM25 = A0 = 0.6000，dense = 0.6500，hybrid = 0.7500。chunks = 94 = 84 + 10。见 `docs/evidence/hard-gold-arm/ACCEPTANCE.md`、`RERUN-20261003-259.md`、现行 `reports/retrieve-hard-gold-arm-compare.md`、`reports/dense-rebuild.md`。
- 语料文件 28（`data/corpus`），chunk 84；陷阱文件 4，chunk 10。hard 集 n=20（`trap` 5 + `adversarial` 3 + `hard` 12）。
- 已知错标（只作背景）：`hard-c4-paraphrase` 问「支付景观相关 T1 证据」，锚在 `t0-market-census#p2@T1`，该块写的是市场规模（约 830 万家）。`hard-c6-paraphrase` 问「人才薪酬」，锚在 `t0-competitor-news#p2@T1`，该块写的是 SeaDesk 免费版与续约率。
- 仓库根目录没有 `LICENSE` / `LICENSE.md`。`README.md` 写明尚无独立 LICENSE 文件。
- `data/dense/` 已在 `.gitignore`。
- `python -m freshlatch.eval` 的子命令是 `run`、`control`、`control-c`、`report`、`retrieve`。x1 不扩展这个 CLI。不带 `--hard` 的 `retrieve` 在 `data/dense/index.sqlite` 存在时会把臂对比写进 `reports/`，通过线 fail 时进程退出 1。

## 相对草稿的核对修正

草稿作为规格保留；下列条目改成仓内事实，或标成未在仓内证实。

1. 工单 ID 以 `docs/agents/agent-guards.md` 为准：`^[A-Z]+-[0-9]+(\.[0-9]+)?$`，另有日期形与 issue 号。草稿文首写成 `^[A-Z]+-[0-9]+$`。子票用 `RET-01.1`–`RET-01.7`。评审里的 `RET-01.2a` / `RET-01.2b` 不符合该正则。
2. 陷阱是 4 个文件、10 个 chunk。草稿「traps 10 chunk」对；这里补上文件数。
3. #258 的整门 fail 是 BM25 相对 A0；hybrid 对 min(BM25, dense) 在那份报告里是 pass。当时索引 chunks=84。
4. `docs/spec/06-护栏预算与成本.md` §6.5 是「开发期统一 qwen-flash」；升 qwen-plus 的建议限于 Critic / Auditor，Lead 保持 flash。本实验的模型分工以已锁决策为准，不把 §6.5 读成正式链路全部改 plus。
5. 代码批大小是 8（`BATCH = 8`，以及 `_cached_query_embedder` 的 `batch = 8`）。「API 上限 10 条/批」在仓内没有出处，不写入验收。
6. `embed_texts` 的请求体只有 `model` 与 `input`，没有维度常量。dim=1024 的仓内证据是 `reports/dense-rebuild.md`。
7. 草稿成本假设里的 64.7 token/chunk、1.39 字/token、hard 集 query 均值 12.1，在 `18b5172` 没有留档。仓内 `Chunk.tokens` 用 `pipeline.tokenize`（jieba）。成本表保留为草稿估算。
8. x1 使用 `load_corpus`，以便 `as_of` 与目录一致。`load_trap_corpus` 没有这道断言。
9. S7 的 10% 与题集 trap/adversarial ≥30% 分母不同。草稿表格末列「保证 ≥30% 占比」容易读成 S7 的 chunk 份额，此处拆开。
10. 草稿中的单一新模块拆成 `x1_checks.py`（RET-01.1）、`embed_cache.py`（RET-01.2）、`retrieve_typed.py`（RET-01.5）、`scripts/gen_x1_drafts.py`（RET-01.7）。
11. `scripts/build_dense_index.py` 当前没有命令行参数。路径是模块级常量 `CORPUS`、`TRAPS`、`DB`、`REPORT`。
12. 去污染的批准值是 0.2，但不得变成代码缺省：键缺失或 `null` 时检查器退出码 2，不得代入 0.2 或 0.5。`lexical` 用整段 query 子串规则；8-gram 重合率只用于 `paraphrase` / `multi_hop`。正式 `config.json` 由 RET-01.3 写入 0.2。0.5 不是缺省，只作临时敏感度对照。
13. 查询向量不复用 `retrieve_eval._cached_query_embedder`。x1 的查询嵌入建在 RET-01.2 的 `embed_cache` 上。语料与 traps 都用 `load_corpus`，不用 `load_trap_corpus`。

## 配置键（名字锁死，值的空位见主人待定）

`data/exp/x1/config.json` 由 RET-01.3 创建。main 上还没有这个文件，本决议不新建它。检查逻辑见 RET-01.1：低于已锁下限的配置视为失败；`decontam_8gram_max` 缺键或为 `null` 时退出码 2，不得代入已批准的 0.2。

- `top_k`: 10
- `rrf_k`: 60
- `embed_model`: `text-embedding-v4`
- `embed_dim`: 1024
- `draft_model`: `qwen-flash`
- `draft_temperature`: 人填写前为 `null`
- `draft_seed`: 人填写前为 `null`
- `flag_model`: `qwen-plus`
- `flag_thinking`: false
- `decontam_8gram_max`: 主人已批准 **0.2**。文件创建前没有这个键。检查器不得在缺键或 `null` 时自行填 0.2
- `lead_delta`: 0.10
- `budget_cny_max`: 10
- `min_chunks`: 600
- `min_per_qtype`: 30
- `min_trap_adversarial_ratio`: 0.30
- `min_synthetic_ratio`: 0.60
- `max_public_ratio`: 0.40

代码里的下限常量与上表一致。配置可以把下限改得更严，不能改得更松。

## 报告列（RET-01.5 实现，RET-01.6 填真数）

按行：总体、lexical、paraphrase、multi_hop、trap+adversarial。按列：R@10、MRR@10、multi_hop 全命中 R@10（非该型写 n/a）、干扰命中@10、hybrid 相对 bm25 的逐题胜/平/负、p50/p95 查询延迟（`time.perf_counter`，百分位算法沿用 `retrieve_eval._p95_ms`）、embed 调用次数、缓存命中、embed token（`embed_texts` 不回传 usage，按字符估算并标「估」）、LLM token（复跑路径应为 0）、估算成本（CNY）。dense / hybrid 列须满足 `last_retrieval_mode` 与请求臂一致，口径同 `run_arm_compare`。

本实验不把 `hybrid+rerank` 列为第四臂。

主表的 R@10、MRR@10 不含跨快照旧版陷阱。另列，不并进主 R@10：护栏（T1 查询命中旧快照块数，通过 = 0）、conflict-pair ordering accuracy、三个预登记子集（8-gram 比例 = 0、比例 ≤ 0.1、字符 LCS < 0.8；n ≥ 15 才讨论稳健）、RET-01.7 草稿上 0.2 / 0.35 / 0.5 的去污染命中数。关掉 `as_of` 的诊断若跑了，单独一节，不进主结论。

## 模型与成本（草稿估算，仓内未复核单价）

现配置（已在代码中核对）：

- Chat：`qwen-flash`，OpenAI SDK，`DASHSCOPE_BASE_URL` 默认华北2（北京）兼容端点。`TokenUsage` 经 `LLMClient.token_usage` 累计。
- Embedding：`text-embedding-v4`，环境变量 `DASHSCOPE_API_KEY`。查询向量在 `run_arm_compare` 与 `run_rerank_compare` 里各建一次进程内缓存。
- 词法重排是本地 `rerank_lexical`。BM25 用 jieba。x1 三臂复跑不调用重排。

草稿估算合计约 ¥0.4–1.5（低：600 chunk / 90 题；高：1000 chunk / 120 题），低于 ¥10 帽。单价来自草稿所引的仓外页面，**本工单落盘时未重新打开**：

- https://help.aliyun.com/zh/model-studio/model-pricing
- https://help.aliyun.com/zh/model-studio/text-embedding-synchronous-api
- https://www.alibabacloud.com/help/en/model-studio/model-pricing
- https://www.alibabacloud.com/help/en/model-studio/text-embedding-v4

token 假设（64.7、1.39、query 12.1 等）无仓内留档。RET-01.6 用账单校正，不把这张表当成已测量的成本。

许可与公告 URL 同样来自草稿，摘录时由 RET-01.3 对照活页核对，不在本票复述为已打开核实：全国人大网公司法 2018 修正与 2023 修订、网信办令第 11 / 13 / 16 号、国家统计局 GDP 公告与服务条款、中国政府网网站声明、著作权法第五条（WIPO Lex）、17 U.S.C. §105、CC0、CC BY 4.0、Wikimedia 使用条款。

## Out

- 改 `PRODUCTION_RETRIEVAL_MODE` 或任何生产默认臂；对 #260 做任何动作
- 改 `docs/evidence/hard-gold-arm/**`、`data/eval/retrieve_hard_gold.json`、`reports/retrieve-hard-gold-*`、`data/corpus/**`、`data/traps/**`
- 覆盖 `data/dense/index.sqlite` 或 `reports/dense-rebuild.md`
- 看了分数之后改题、改阈值、改门
- 白名单外文本；把 `excerpt_only` 摘录当模板
- 把本轮结论写成「已证明 hybrid 最优」或改臂授权
- 换 embedding 模型或维度
- 把法规标题前置到 chunk 正文（contextual retrieval）。三臂都做或都不做；本期都不做
- 为了让跨快照旧版陷阱进入召回而改掉 `as_of` 过滤。诊断消融只能另节报告

## Handoff
`2026-10-06 | RET-01 | draft | 去污染 0.2 与 P1 A+B 清单已折入子票。RET-01.1 与 RET-01.2 可 /implement。RET-01.3 仍是人步骤；陷阱操作化定义未签，flk 核对未做`

## Blocked by
None（本索引票）。与 #260 互不阻塞。
