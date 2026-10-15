# patch-establishment v1 冻结语料（unrun）

本目录是 Comparison A（T attested / fail-closed 对 C 无证据改写）的实验语料冻结件。`run_status=unrun`。`measurement_status=unmeasured`。`counts_as_establishment=false`。`role=frozen_corpus_unrun`。

这不是激活，不是「跑」，不是成立。不填分数，不发明 SESOI。`second_formal_y=false`。本目录不是 `data/corpus/pe_v2` 的正式 Y 名单，也不是第二次正式 Y。STOP-SAME-YARDSTICK。

## 选取

来源是 `data/corpus/pe_v2` 中、不在 `docs/evidence/patch-events/SPLIT-pe-v2-route-y.json` 的 n400 与 pilot 里的 leftover 主张。`corpus/t0` 与 `corpus/t1` 的正文从 pe_v2 逐字节复制。许可沿用源 `PROVENANCE.json`。

目标配额是 4 层 × 25。层内 `correct=floor(25/2)=12`，`bad=ceil(25/2)=13`。余数规则借 PREREG-B / PREREG-Y / `patch_events_construct`。层内 leftover 按 `claim_id` 字典序取用。某个槽位 `ConstructError` 就换下一条主张，算子不改成更好做的那一个，跳过记入 `SPLIT.json` 的 `shortfalls`。

配额目标不改小。本次建成 formal 91，缺额 9。数值、日期、条款替换各 25（正确 12 / 坏 13）。删除建成 16（正确 12 / 坏 4），坏槽目标仍是 13。leftover 里能做删除算子 0 的主张只有两条，字典序取用时后一条被更早的坏槽用掉；算子不改，后续坏槽记「语料不足」，不补合成主张，不把未建成的槽算进 `formal`。`CONSTRUCTED.jsonl` 是离线 `construct_from_pins` 的记录，没有 generation，没有 score，没有 `compare_primary`。`arm=T` 只是构造器 schema 的占位，不代表已经跑过 T。

## 文件

- `corpus/t0/*.md`、`corpus/t1/*.md`：源正文副本
- `docket.json`：建成主张的 docket 子集
- `PROVENANCE.json`：来源、许可、与 Y 名单的隔离
- `SPLIT.json`：formal 针、shortfalls、gaps
- `CONSTRUCTED.jsonl`：离线构造记录

B-04 夹具仍是 `counts_as_establishment=false`。夹具绿不是成立。
