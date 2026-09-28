# V1 发前主缝贯通冒烟证据 (#174)

> 层身份:**冒烟/脚本验收**(零 LLM CI)。不报方差,不作统计升格。

## 命令

```text
python -m compileall -q src
pytest tests/unit/test_prepublish_e2e.py tests/unit/test_rule_gate.py -q
```

## 结果摘要

| 检查项 | 结果 |
|--------|------|
| 顾问样例包 `v1-mck-soai` + 夹具薄 URL → disposition | 预登记未收口 stale → **勿发** |
| 人审 discard 收口后列表/详情投影 | 一致 → **可发** |
| T1 checksum 可追 | 详情 `t1_checksums` 含入库 checksum |
| patch_events | 人审后 ≥1 行,字段齐全;`before_disp=勿发` |
| 映射抽检 vs ADR-0027 | `PREREG_MAPPING` 与边界一致 |
| thesis-1 / QuoteTTL 软 Port | 可解析;不算第二垂直(`v1-mck-soai ∉ KNOWN_PACK_IDS`) |
| 生产默认检索臂 | `PRODUCTION_RETRIEVAL_MODE == bm25` |

## 预登记映射(不可事后改期望凑绿)

`tests/unit/test_prepublish_e2e.py` → `PREREG_MAPPING`:

- mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale → 期望 **勿发**
