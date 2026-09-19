# ADR-0006: HumanLatch 中断机制与作废/续命闭环设计

- **状态**: Accepted(2026-09-20,工单 #11 拍板)
- **相关**: ADR-0002(复验单 UI 形态)、ADR-0004(Agent 循环裸 tools 路线)、研究 `docs/research/langgraph-interrupt人审模式研究.md`(工单 #7)

## 背景

HumanLatch(人审工作流)是六段流程之后的第 7 段:人对每条红/黄灯主张点「作废」或「续命」(续命必须带 T1 evidence_id)。硬约束:

- Agent 不得自己把红灯改回绿灯;Auditor 不得拥有放行权(角色诚实表);
- 作废 id 进作废名单后,该主张重跑不得再绿(代码强制);
- 「图不是 Agent」:LangGraph 只承担 checkpoint/interrupt,Lead 循环跑图外(ADR-0004)。

## 决议

### 1. 中断机制:LangGraph interrupt + SqliteSaver,拍板

`interrupt()` + `Command(resume)` + `SqliteSaver`(`data/checkpoints.db`),锁版本 `langgraph>=1.0,<2.0`,LangGraph 用法隔离到独立模块。自研门闩(参考代码 `project 多agent` 的 `blocked_for_human` 模式)作为被记录的真实取舍弃用:需自写状态序列化/flag 管理/恢复入口,且放弃 checkpoint 历史回溯与多 interrupt 串联的原生能力。

### 2. 中断粒度:轮次级单 interrupt

一轮 Lead 复验跑完、Scribe 排版后,图在收尾节点 `interrupt()` 一次;**一轮复验 = 一个 thread_id**。resume 值传整个决定列表 `[{claim_id, action, evidence_id?}, ...]`。不为每条主张开 interrupt(12 主张 = 12 thread,checkpoint 膨胀且徽章状态复杂)。

### 3. 作废闭环(W3–W4 实装)

- 人点「作废」→ 双重确认弹窗(「作废后重跑不得再绿」)→ `status=void` 灰显 + 作废记录;`stale`(机器判定)与 `void`(人的决定)并存不互斥。
- **重跑**:人点「重跑作废主张」按钮触发(不自动),**只重跑该主张**,新开 thread(`reverify-{claim_id}-{ts}`)跑迷你复验;结果挂该主张卡片时间线(如「重跑后仍红(第 N 次)」)。即使 Lead 仍判 fresh,规则闸查作废名单打回。
- W1–W2 **零 HumanLatch**(切片权威:W1–W2 生死闸是「无 T1 不得绿灯」),W3 起接作废。

### 4. 续命闭环(W5–W8 实装,W3–W4 设计定稿)

- evidence_id 从**本轮已检索 T1 块下拉选择**(非自由文本),选择器天然满足「续命必须带 T1 evidence_id」;
- 生效条件:checksum 校验通过 → 写**新的 validity_basis(T1 doc+checksum)** + 更新 `last_confirmed_at` → `status=fresh`;
- 「Agent 不得把红灯改回绿灯」禁令口径:**只约束 Agent 侧工具链**,人审是 L0 合法出口,规则闸注释写明;
- W3–W4 复验单上续命按钮**渲染但 disabled**,tooltip「W5 开放:续命必须带 T1 原文证据」。

### 5. 作废名单:单一真相

SQLite `invalidation_list(claim_id, voided_at, actor, reason?)` 表,**随课题持久**;与长期记忆的「已废 id」是同一份真相(W9 记忆模块读它,不复制)。Lead 上下文与规则闸校验都查这张表。

### 6. 双保险

- **代码层**:写路径唯一 = `gates/human_latch.py`(由它调规则闸);Agent 工具白名单 fail-closed,不含写 `void`/改判定的工具;`gates/` 是绿灯唯一出口(ADR-0001)。
- **交互层**:按钮 disabled 逻辑(无 evidence_id 续命不可用)+ 作废双重确认弹窗。
- **人审日志必做**:SQLite `latch_log(ts, claim_id, action, evidence_id?, actor="human")`,既是审计迹也是用户作废率(在线指标)的取数口。

### 7. 评测纪律

评测模式**代码级跳过 HumanLatch 节点**(与「评测期联网代码级禁用」同一纪律):eval 模式图直通,interrupt 不触发,人审动作不进评测路径;must_stale 由规则闸强制,不依赖人审。

### 8. FastAPI 集成:同步端点绕开 async 阻塞

HumanLatch 端点(`/api/latch/decide`、重跑触发)写**同步 `def` 端点**,FastAPI 自动线程池执行,同步 SqliteSaver 不阻塞事件循环。LangGraph 异步 API(`ainvoke`/AsyncSqliteSaver)本期不碰。

### 9. checkpoint 清理

同一主张只保留最近 5 个 thread 的 checkpoint,业务侧定期删行;不依赖 LangGraph 内置清理 API(研究报告遗留问题 3)。

## 后果

- W3 实装前置:LangGraph 极简 POC(研究报告 §5 建议的进程重启恢复验证)可在 W3 开工时顺带做,不单独立票。
- 词表新增 `void`、`重跑` 术语(CONTEXT.md 已落)。
- 重跑不依赖 `graph.update_state()` 回退 API,LangGraph 使用面保持最小,版本升级风险低。
