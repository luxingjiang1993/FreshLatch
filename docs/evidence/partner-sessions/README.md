# partner-sessions

设计伙伴**按次**复验日志目录（E2）。

- 协议：[`docs/ops/设计伙伴按次日志.md`](../../ops/设计伙伴按次日志.md)
- 复制 [`TEMPLATE.md`](TEMPLATE.md) → `ps-YYYYMMDD-NN.md`
- 化名优先；禁止把合成 UX 分当真实按次
- 生产观测 / 伙伴日志 ≠ 乙尺；不回写 RESULT-Y

## Owner 自操首轮（步骤）

设计伙伴外联到位前，Owner 可自操一轮**真实**按次复验，产出同样落在本目录：

1. **复制模板**：[`TEMPLATE.md`](TEMPLATE.md) → `ps-YYYYMMDD-NN.md`（当天日期，NN 从 01 递增）。
2. **填信封**：`partner_alias` 填化名/代号（勿写真名）；`operator` 填 `Owner`；`vertical` 默认 `advisor`。
3. **如实记人审行**：每条 discard/renew 抄一行，含 `machine_status_before` 与派生 `override`；renew 被挡必填 `renew_blocked_reason`。
4. **outcome 四选一**：`voided` / `renewed` / `blocked` / `abandoned`，多主张取主目标并在备注写明另一侧计数；不得把 blocked 行藏掉。
5. **敏感附件留本机**：含敏感原文的截图/导出放本机目录，不进 git；会话文件只写化名与摘要。
6. **诚实署名**：Owner 自操是允许的第一次真实按次，但须如实署名——不得伪造成伙伴会话（冒用他人名义或假装已有外联）。

字段口径、outcome 定义与全部禁条以协议页 [`设计伙伴按次日志.md`](../../ops/设计伙伴按次日志.md) 为准。
