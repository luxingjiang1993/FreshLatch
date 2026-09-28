# patch_events

V1 起改稿对照与产品审计共用事件账。目录约定:本目录下 JSONL 追加写。

## 字段(预登记)

| 字段 | 含义 |
|------|------|
| `claim_id` | 主张 id |
| `before_disp` | 改稿前包结论(可发 / 需补丁 / 勿发) |
| `patch_span` | 补丁范围描述 |
| `t1_ids` | 引用的已入库 T1 id 列表 |
| `human_confirm` | 是否经人确认 |
| `reverify` | 是否立刻再验 |
| `minutes` | 人审/改稿工时(分钟) |
| `arm` | `C`(无证自由改写) 或 `T`(强制 ⊆ 已入库 T1) |
| `ts` | ISO-8601 时间戳 |
| `actor` | 写入主体(如 `human` / `script`) |

C vs T **只后台/脚本**记账,发前 UX 不提供臂切换。人手补丁走同一 schema。

## 示例一行

```json
{"claim_id":"c-mck-share-01","before_disp":"需补丁","patch_span":"定价段·份额主张改写","t1_ids":["mck-soai-2025-11#p3@T1"],"human_confirm":true,"reverify":true,"minutes":12.5,"arm":"T","ts":"2026-09-28T17:00:00+00:00","actor":"script"}
```

写入 API:`freshlatch.patch_events.append_event` / `append_human_patch`。
