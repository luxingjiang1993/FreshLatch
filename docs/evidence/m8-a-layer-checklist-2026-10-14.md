# M8 A 层预核验清单（2026-10-14）

- 日期：2026-10-14
- HEAD：`9cc116d975e06246c6c9d61db8a173364d16a73b`（`feat(skills): L4-SK-02 中文业务 skill 包 (#620)`）
- 对照基线：`b2caaeffdc6ba56885087fcd5beddd560fb563b2`（QG-13，`#600`）
- 主人：Oriental Ronin 于 2026-10-14 点头
- Trust：Watch。本页只记录核验，不改产品代码、PREREG、金标、x1、neural-rerank、`PRODUCTION_RETRIEVAL_MODE`
- 结论：**PASS**

可回归的拒答产品 / A 层工程完成；Skill 标 L3；不标 L5；不把注册 G1/A1/T1/R1 的 value= 说成产品率

optional EV-03 / §11 new PREREG not required for M8

夹具绿不等于注册分数。本页不把 `counted_as_pass` 改成 true，不把 `status` 改成 pass，不发明 SESOI。

## 1. 离线质量闸

命令（本 checkout，工作目录为仓库根）：

```text
python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md
```

退出码：0。stdout 全文另存于核验机 `/opt/cursor/artifacts/m8-quality-gate.txt`。下面 token 从该次 stdout 逐字抄出。

| 冻结项 | 期望 value | 本次 stdout |
|---|---|---|
| G1 | `1.0` | `metric id=G1-should-refuse-accuracy status=TBD value=1.0 ... g1_no_regression=true counted_as_pass=false` |
| A1 recall | `0.42857142857142855` | `metric id=A1-citation-recall status=TBD value=0.42857142857142855 ... a1_no_regression=true counted_as_pass=false` |
| A1 precision | `0.6` | `metric id=A1-citation-precision status=TBD value=0.6 ... a1_no_regression=true counted_as_pass=false` |
| T1 | `0.3333333333333333` | `metric id=T1-new-over-old-accuracy status=TBD value=0.3333333333333333 ... t1_no_regression=true counted_as_pass=false` |
| R1 Recall@10 | `0.9732142857142857` | `metric id=R1-recall@10 status=TBD value=0.9732142857142857 baseline=0.9732142857142857 ... delta=0.0 r1_no_regression=true counted_as_pass=false` |
| R1 MRR@10 | `0.8381855867346939` | `metric id=R1-mrr@10 status=TBD value=0.8381855867346939 baseline=0.8381855867346939 ... delta=0.0 r1_no_regression=true counted_as_pass=false` |

闸头同时印出：`locked_gate=true`，`owner_freeze=confirmed`，`fingerprints=match`，`arm=hybrid+rerank`，`embed_model=BAAI/bge-small-zh-v1.5`，`rrf_k=60`，`rerank_model=BAAI/bge-reranker-base`，`rerank_k=10`，`fastembed=0.8.1`。

计分行：12 行（3 条 `segment` + 9 条 `metric`）全部是 `status=TBD` 且 `counted_as_pass=false`。stdout 中没有 `status=pass`，也没有 `counted_as_pass=true`。

`trap_smoke` 一行是 `status=not_counted`、`in_denominator=false`、`counted_as_pass=false`。这是冒烟，不是计分行；契约要求它保持 `not_counted`，本页不把它改成 TBD 或 pass。

## 2. Do-not-touch

方法：`git rev-parse <baseline>:<path>` 与 `HEAD:<path>` 比 blob；`git log --oneline b2caaef..HEAD -- <paths>` 看基线之后谁碰过这些路径。`data/exp/x1/` 下 532 个文件逐个比 blob。

| 路径 | 基线 blob = HEAD blob | 基线之后的提交 |
|---|---|---|
| `docs/evidence/patch-events/RESULT-Y.md` | `ce768b99cf463332ab90bd45de264de442b83de2` | 无 |
| `docs/evidence/patch-events/PREREG-Y.md` | `5721fa4b80a8c3f9e8b9d460c5a7bef498153315` | 无 |
| `docs/evidence/quality-gate/PREREG.md` | `cdef003fcb8ea685d0f762b26c849189d7029114` | 无 |
| `docs/evidence/neural-rerank/summary.json` | `2de91d9a7a800b9ee0a7c312b015e46a03af6ff4` | 无 |
| `docs/evidence/neural-rerank/per-query.json` | `2232bb9bfb2540e9929d339b11b539d5b8dc6a05` | 无 |
| `data/eval/guard_should.json` | `9cfef9d44bcc0b48268e5305e81348b2c205e44d` | 无 |
| `data/eval/cite_sentence.json` | `ea0d769659ef4b0f9bef800791ba39f144db21f4` | 无 |
| `data/eval/temporal_new_over_old.json` | `c2f42e0e569f0f042d87e5b293a2eef1040d8202` | 无 |
| `data/eval/gold.json` | `c7a14683de82bb795fd67bbb505bd6f7128b7c2a` | 无 |
| `data/exp/x1/`（含 `questions.json` 与语料，532 文件） | 全部相同 | 无 |
| `src/freshlatch/models.py` | `de701b998679f24b1d38fc76df06ba6461d91838` | 无 |
| `pyproject.toml` | `d8fdc53b86ef28f3265d540592cfd3a8b75be16c` | 无 |
| `requirements.txt` | `7640b2f1a53eedeced621afe1ded6d5e153b2d25` | 无 |

整文件相同，所以下列锁没有被改写：

- `RESULT-Y.md` / `PREREG-Y.md` 成立格（成立只认 T−C：点估计 >0.05 且 95% 下界 >0；本次主表 T−C 仍为不成立）
- `PREREG.md` 的 floor 行、`segment_registered:` 三行、`owner_freeze: confirmed`、§7 三行指纹、`R1 通过线主人确认: confirmed`
- neural-rerank 的 `summary.json` 与 `per-query.json`
- 金标四件套与 x1 语料 / `questions.json`

`src/freshlatch/store/base.py`、`pipeline.py`、`neural_rerank.py` 的 blob 在基线之后变过。碰它们的提交只有：

- `42df3c7371d0d4add7ce7594c3df9adb5edda8a1` L4-RAG-04（`#605`）hit 可测分与 rerank 开关记录
- `1ac137d15d5c1fe52c596276f1e549fc75d793f4` L4-RAG-03（`#606`）patch 与有效期过滤先于 RRF

这两笔是检索边上的工程改动。常量赋值在基线与 HEAD 上仍是：

- `PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"`（`base.py` 第 15 行，两边相同）
- `RRF_K = 60`（`pipeline.py`，基线第 86 行，HEAD 第 216 行，值未变）
- `NEURAL_RERANK_K = 10`（`neural_rerank.py` 第 18 行，两边相同）
- `fastembed==0.8.1`（`pyproject.toml` 与 `requirements.txt` blob 未变）
- 本地模型名随 `models.py` blob 未变：embedding `BAAI/bge-small-zh-v1.5`，rerank `BAAI/bge-reranker-base`（与本次闸头一致）

判决：生产默认臂仍是 hybrid+rerank。基线之后没有提交改写 floors、gold、x1、neural-rerank 冻结文件或生产臂常量。

## 3. Skill 旁路三票

三枚合并提交都是 HEAD 的祖先（`git merge-base --is-ancestor` 为真；`#620` 就是 HEAD）：

| 票 | PR | squash |
|---|---|---|
| L4-SK-03 references 真能读到 | `#618` | `bb6f3e20e6346b24514c69f9b72498fa7ee7e163` |
| L4-SK-01 Guards hook 样板 failClosed | `#619` | `27acda75cefa11e6a4327aeb22febbd17ddcb4b9` |
| L4-SK-02 中文业务 skill 包 | `#620` | `9cc116d975e06246c6c9d61db8a173364d16a73b` |

`skills/` 下包在盘。reverify 的 references 与加载器一致：frontmatter 写 `load_skill_reference` 按 `skills/{slug}/references/{name}.md` 只读；正文里没有「references 由循环内 read_source 按需读取」；`load_skill_reference("reverify", "rerun-rules")` 读到含「名单的存储真相是 SQLite」的正文，而 `load_skill_body("reverify")` 不包含该句，也不包含 `load_skill_reference`。`skills/reverify/references/verdict-basis.md` 与 `rerun-rules.md` 都在。

hook 样板在 `docs/agents/hooks/hooks.json` 与 `docs/agents/hooks/deny_exit_2.py`。`failClosed` 为 true，退出码 2。仓库根没有 `.cursor/hooks.json`，`git ls-files` 也不跟踪它。`docs/agents/agent-guards.md` 写明样板默认不启用。

四个中文包在盘且未挂进 Runner：`skills/earnings_figures`、`skills/event_timeline`、`skills/patch_diff`、`skills/strategy_walkthrough`。各包 frontmatter 写明不进入 Runner、不进入 Lead 系统提示。`src/freshlatch/runner.py` 默认仍是三次 `load_skill_body`：`reverify`、`devil_advocate`、`freshness_audit`。该文件没有 `load_skill_reference`，也没有上述四个 slug。

旁证：`pytest tests/unit/test_skills.py tests/unit/test_l4_sk_01.py -q` 为 49 passed。

## 4. M1–M7 指针

工程完成的指针，不是新指标。下列 squash 都在 HEAD 历史上。票号取自各提交正文。

| 里程碑 | 票 | PR | squash |
|---|---|---|---|
| M1 拒答边 | L4-RAG-01 | `#602` | `e7b44f469ab32ac89926af66c557c82cb246f7bb` |
| M1 | L4-RAG-02 | `#604` | `aa7f2a5537f0a5236bde8337dc73fd16d55c4c0f` |
| M1 | L4-RAG-04 | `#605` | `42df3c7371d0d4add7ce7594c3df9adb5edda8a1` |
| M2 版本过滤 | L4-RAG-03 | `#606` | `1ac137d15d5c1fe52c596276f1e549fc75d793f4` |
| M2 | L4-EV-T1-CASE | `#603` | `7547e9f15d57ddbec018f69d56cd01940e0f5c17` |
| M3 线上引用检查 | L4-FC-CITE | `#607` | `b0c66bf68f9c9a668ee12ac932e422e10c8a163c` |
| M3 | L4-EV-02 | `#608` | `b131d562e76b8ea38e8437dc643a088055258d35` |
| M4 调用与权限 | L4-FC-01 | `#609` | `5ab6ca3e077e61ecee6181e41c31ea33e430c1ec` |
| M4 | L4-FC-02 | `#610` | `005a7e2b9aa21e4364ef412a64f39bcb1daa71de` |
| M4 | L4-FC-03 | `#611` | `17d9ddb89e09d13dff6069ab42c149866039c35b` |
| M5 短环 | L4-AG-01 | `#612` | `99b285e50df7194c510ce09433ec0b0eeba8ea18` |
| M5 | L4-AG-02 | `#613` | `9da579a37dd24daec49eaf5aa43f4780ac465119` |
| M5 | L4-AG-03 | `#614` | `9b55ff7ac84a2820243b88207432f8a91a49472e` |
| M6 审计面 | L4-UI-01 | `#615` | `dc551f01c94a6a1b20977fe7a09d8b4467b30868` |
| M6 | L4-UI-02 | `#616` | `3c3ac7a6fdb89288a5ad868ad733cfe13669cb46` |
| M7 臂表 | L4-EV-01 | `#617` | `2aba5500069ac813ba8ab3254258e5093e1d48c7` |

里程碑定义见 `docs/evidence/l4-full-build-plan-2026-10-14.md` §3。

## 5. 声称边界

本页允许的对外句只有：

可回归的拒答产品 / A 层工程完成；Skill 标 L3；不标 L5；不把注册 G1/A1/T1/R1 的 value= 说成产品率

`G1 value=1.0`、`A1 recall value=0.42857142857142855`、`A1 precision value=0.6`、`T1 value=0.3333333333333333`、`R1 Recall@10 value=0.9732142857142857`、`R1 MRR@10 value=0.8381855867346939` 是注册无回归锁上的冻结点估计，`status` 仍是 TBD。它们不是产品拒绝率、产品引用率或产品时序准确率。

optional EV-03 / §11 new PREREG not required for M8。构建计划 §11 的新预注册页（拒答行为率、线上 citation、活检索时序）留在 M8 之后，本清单不要求它。
