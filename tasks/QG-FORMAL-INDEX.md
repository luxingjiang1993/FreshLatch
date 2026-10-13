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

## 本索引的可执行检查

```bash
python -c "from pathlib import Path; root=Path('tasks'); ids=['QG-05','QG-06','QG-07','QG-08','QG-09','QG-10']; need={'QG-05':['**Trust**: Auto','0.9732142857142857','0.8381855867346939','human_row_review=false','owner-delegated','PE-Y','nDCG','SENS','retrieve_gold.json','p95'], 'QG-06':['**Trust**: Watch','guard_should.json','cite_sentence.json','temporal_new_over_old.json','counted_as_pass','unregistered'], 'QG-07':['**Trust**: Watch','retrieve_traps.json','data/eval/gold.json','conflict_pair','human_row_review','draft'], 'QG-08':['**Trust**: Gate','keep','dispute'], 'QG-09':['**Trust**: Watch','counted_as_pass','0.9732142857142857','退出码'], 'QG-10':['**Trust**: Gate','owner_freeze','pending','unregistered','0.8381855867346939']};
idx=(root/'QG-FORMAL-INDEX.md').read_text(encoding='utf-8');
assert 'QG-05' in idx and 'QG-10' in idx and 'F6' in idx and '8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526' in idx;
[(_t:=(root/f'{i}.md').read_text(encoding='utf-8'), (_m:=[n for n in need[i] if n not in _t]) and (_ for _ in ()).throw(SystemExit(f'{i} missing {_m}'))) for i in ids]; print('qg-formal-tickets-ok', len(ids))"
```
