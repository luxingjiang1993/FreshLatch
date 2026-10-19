# 正式产品质量闸 · 票索引（F0–F5）

本页只做指针。不改 `docs/evidence/quality-gate/PREREG.md`，不改 runner，不写金标 JSON。

ID 用 `docs/agents/agent-guards.md` 的 `^[A-Z]+-[0-9]+(\.[0-9]+)?$`。`QG-F0` 这种带字母的后缀不符合该正则（同 `RET-01.2a` 改成 `RET-01.7` 的先例）。切片代号 F0–F5 留在题目里，文件名用下一组空号 **QG-05 … QG-10**（QG-01…QG-04 已用于盘点、PREREG、入口、冒烟重跑）。

| 顺序 | 切片 | ID | 题目 | Trust | Blast | 依赖 | 谁做 |
|------|------|----|------|-------|-------|------|------|
| 1 | F0 | QG-05 | 正式闸范围 | Auto | none | 无 | 本文件即范围；不另开 `/implement` |
| 2 | F1 | QG-06 | schema 与路径登记 | Watch | api | QG-05 | 以后的 `/implement` |
| 3 | F2 | QG-07 | 草稿金标 | Watch | none | QG-06 | 以后的 `/implement`；LLM 只许草稿 |
| 4 | F3 | QG-08 | 人审定稿 | Gate | none | QG-07 | **人步骤。禁止 `/implement` 写定稿** |
| 5 | F4 | QG-09 | 判分接入 quality-gate | Watch | api | QG-06；G1/A1/T1 计分还依赖 QG-08 | 以后的 `/implement` |
| 6 | F5 | QG-10 | 把 R1 通过线写入 PREREG | Gate | none | QG-05 的锁定数字；建议在 QG-09 之后 | 起草 `/implement` 只写 TBD→地板，**不得**把确认写成 `confirmed` |
| — | F6 | 不建票 | 正式离线跑 | — | — | QG-10 主人手改确认之后 | 本 PR 不做 |

已锁（2026-10-13，主人；票内当决定，不当开放题）：

- R1：相对冻结 neural k10 **无回归**。地板 = 点估计 `Recall@10 ≥ 0.9732142857142857`，`MRR@10`（神经右臂）`≥ 0.8381855867346939`。p95 只描述，不挡门。
- x1 分母维持 `owner-delegated` / `human_row_review=false`。本切片不为分母再开人审票。
- G1/A1/T1 首版：金标落地并完成第一次冻结跑之后，用相对该次冻结的无回归。不发明绝对百分数。
- guardrail 0-hit、conflict_pair、multi_hop：报告-only / TBD，不是 P0。
- 不进产品 pass：smoke（`retrieve_gold` / `retrieve_traps` / `retrieve_hard_gold`）、PE-Y（丙）、SENS、nDCG、p95。
- LLM 只生成草稿。正式判分零 LLM。

下一跳 F6：`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md` 的正式一次跑。F6 不在本 PR。QG-04 那一次冒烟重跑不是 F6。

F6 没有打出 G1/A1/T1 的点估计：runner 仍印 `unregistered`。下面 Track A 才是计分。F0–F5 表不改。

## Track A（QG-11 … QG-13）

主人 2026-10-14 锁定。本段只做指针，不改 `docs/evidence/quality-gate/PREREG.md`，不改 runner，不写金标，不写绝对百分数。

Track B（`conflict_pair` / `multi_hop`，以及 guardrail 0-hit）保持报告-only / TBD。本索引不为它们升 P0 另开票。

| 顺序 | 切片 | ID | 题目 | Trust | Blast | 依赖 | 谁做 |
|------|------|----|------|-------|-------|------|------|
| 7 | Track A.1 | QG-11 | 离线计分 G1/A1/T1，仍不计通过 | Watch | api | QG-08、QG-09 | 以后的 `/implement` |
| 8 | Track A.2 | QG-12 | 第一次计分冻结跑 RESULT，只描述 | Watch | none | QG-11 已在 main | 以后的 `/implement`；数字必须来自那次跑 |
| 9 | Track A.3 | QG-13 | 相对无回归地板 + `segment_registered:` + 回归则非 0 | Gate | api | QG-12 的 RESULT | 以后的 `/implement`；不得改 `owner_freeze:`，不得写 `confirmed` |

已锁（2026-10-14，主人；票内当决定，不当开放题）：

- 计分零付费 LLM。低分在 QG-11 不改退出码。`segment_registered:` 不在 QG-11 加。
- 地板只来自 QG-12 真实 stdout 的点估计。F6 与 QG-04 都不是这组数字。实现者不得发明 SESOI，不写绝对百分数。
- RESULT 落在 `docs/evidence/quality-gate/QG-GAT-FREEZE-RESULT.md`，descriptive-only，本身不改通过线。
- QG-13 不得翻动 R1 确认，不得改行首 `owner_freeze:`。

## 本索引的可执行检查

```bash
python -c "from pathlib import Path; root=Path('tasks'); ids=['QG-05','QG-06','QG-07','QG-08','QG-09','QG-10']; need={'QG-05':['**Trust**: Auto','0.9732142857142857','0.8381855867346939','human_row_review=false','owner-delegated','PE-Y','nDCG','SENS','retrieve_gold.json','p95'], 'QG-06':['**Trust**: Watch','guard_should.json','cite_sentence.json','temporal_new_over_old.json','counted_as_pass','unregistered'], 'QG-07':['**Trust**: Watch','retrieve_traps.json','data/eval/gold.json','conflict_pair','human_row_review','draft'], 'QG-08':['**Trust**: Gate','keep','dispute'], 'QG-09':['**Trust**: Watch','counted_as_pass','0.9732142857142857','退出码'], 'QG-10':['**Trust**: Gate','owner_freeze','pending','unregistered','0.8381855867346939']};
idx=(root/'QG-FORMAL-INDEX.md').read_text(encoding='utf-8');
assert 'QG-05' in idx and 'QG-10' in idx and 'F6' in idx and '8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526' in idx;
[(_t:=(root/f'{i}.md').read_text(encoding='utf-8'), (_m:=[n for n in need[i] if n not in _t]) and (_ for _ in ()).throw(SystemExit(f'{i} missing {_m}'))) for i in ids]; print('qg-formal-tickets-ok', len(ids))"
```

F0–F5 的命令保持原样，仍打印 `qg-formal-tickets-ok 6`。Track A 另跑下面这一条。

```bash
python -c "from pathlib import Path; root=Path('tasks'); ids=['QG-11','QG-12','QG-13']; need={'QG-11':['**Trust**: Watch','**Blast**: api','counted_as_pass=false','citation recall','citation precision','new-over-old accuracy','G1-should-refuse-accuracy','src/freshlatch/eval/quality_gate.py','tests/unit/test_quality_gate.py','不写绝对百分数','segment_registered:','付费'], 'QG-12':['**Trust**: Watch','**Blast**: none','QG-GAT-FREEZE-RESULT.md','docs/evidence/quality-gate/','不写绝对百分数','owner_freeze','descriptive-only','模型拒绝率'], 'QG-13':['**Trust**: Gate','**Blast**: api','segment_registered: G1-should-refuse','segment_registered: A1','segment_registered: T1-new-over-old','r1_no_regression','owner_freeze','TBD','conflict_pair','multi_hop','不写绝对百分数','confirmed']};
idx=(root/'QG-FORMAL-INDEX.md').read_text(encoding='utf-8');
assert 'QG-11' in idx and 'QG-13' in idx and 'Track A' in idx and 'Track B' in idx and 'descriptive-only' in idx and 'F6' in idx;
[(_t:=(root/f'{i}.md').read_text(encoding='utf-8'), (_m:=[n for n in need[i] if n not in _t]) and (_ for _ in ()).throw(SystemExit(f'{i} missing {_m}'))) for i in ids]; print('qg-track-a-tickets-ok', len(ids))"
```
