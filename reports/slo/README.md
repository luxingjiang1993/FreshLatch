# reports/slo — 生产补丁/放行 SLO 周报输出

本目录存放**观测层**周报机读/人读片段。层身份：运营纪律，**不是**实验乙成立格，**禁止**回写 `RESULT-Y`。

## A6 再验失败率

| 项 | 约定 |
|----|------|
| 脚本 | `scripts/slo_a6_reverify_fail_rate.py` |
| 逻辑 | `src/freshlatch/slo_a6.py`（只读聚合） |
| 输入 | `data/patch_events/*.jsonl`（`human_confirm`∧`reverify`）+ 可选 outcomes（`reverify_verdict`） |
| 输出 | `a6-<YYYYMMDD>-<YYYYMMDD>.json` 与同名 `.md` |
| 周报字段 | JSON/`md` 中的 `weekly_fill_line`，对照 `docs/ops/生产补丁放行SLO.md` §6「A6 再验失败率」 |
| 空态 | 窗内 0 条 confirm → `A6 再验失败率: 本周无 confirm`（**禁止**填 0%） |

### 生成示例

```bash
python scripts/slo_a6_reverify_fail_rate.py \
  --events-dir data/patch_events \
  --outcomes path/to/outcomes.jsonl \
  --window-start 2026-10-02T00:00:00+00:00 \
  --window-end 2026-10-09T00:00:00+00:00 \
  --out-dir reports/slo
```

`outcomes` 行最小字段：`claim_id`、`ts`、`reverify_verdict`（与 confirm 行对齐）。若 events 行已内嵌 `reverify_verdict`，可省略 `--outcomes`。
