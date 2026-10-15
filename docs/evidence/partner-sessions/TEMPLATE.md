# Partner session `ps-YYYYMMDD-NN`

> 按次复验日志 ≠ 客户成功 KPI ≠ 乙尺。  
> 协议：[`docs/ops/设计伙伴按次日志.md`](../../ops/设计伙伴按次日志.md)

## Envelope

| field | value |
|-------|-------|
| session_id | ps-YYYYMMDD-NN |
| partner_alias | |
| vertical | advisor |
| started_at | YYYY-MM-DD HH:MM Asia/Shanghai |
| ended_at | |
| operator | |
| product_entry | |
| claims_touched | |
| notes_session | |

## HumanLatch rows

| ts | claim_id | action | evidence_id | actor | machine_status_before | override | voided | renew_blocked_reason | reviewer_note | run_id |
|----|----------|--------|-------------|-------|----------------------|----------|--------|----------------------|---------------|--------|
| | | discard\|renew | | | fresh\|stale\|unknown | true\|false | true\|false | | | |

## Outcome

- [ ] `voided`
- [ ] `renewed`
- [ ] `blocked`
- [ ] `abandoned`

Primary outcome: `<one>`  
Secondary counts (if any): voided=__ renewed=__ blocked=__

## Firewall

- [ ] 未把本会话写成 RESULT-Y 乙 / 客户成功
- [ ] override 未解释为模型变好
- [ ] 未新增 HumanLatch 动词
