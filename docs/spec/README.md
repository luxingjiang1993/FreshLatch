# FreshLatch 实施规格(W1–W4)

> 工单:[汇编全部决策 → W1–W4 实施规格 #13](https://github.com/luxingjiang1993/FreshLatch/issues/13)
> 性质:全部前置决议(工单 #2–#12,对应 ADR-0001–0007 与 11 份评估文档)的**汇编**,不含新决策;实施中如与本规格冲突,以工单决议评论 + ADR 为准,冲突须回填本规格。
> 语言:全中文,技术词保留英文原词;术语以 `CONTEXT.md` 词表为准。

## 目的地

W4 开工前决策完备的实施规格:复验主链(W1–W2)、Critic 与评测闸(W3–W4)、HumanLatch 最小闭环的全部技术决策已拍完,本规格可直接拆单实施。

## 规格分卷

| 卷 | 文件 | 内容 |
|---|---|---|
| 0 | [00-架构总览.md](00-架构总览.md) | 数据流图、分层、贯穿纪律 |
| 1 | [01-目录与模块.md](01-目录与模块.md) | 目录结构、模块职责、角色禁止事项落代码方式 |
| 2 | [02-数据schema与语料清单.md](02-数据schema与语料清单.md) | docket / 主张 / 语料 / chunk / gold.json schema 与 12 主张清单 |
| 3 | [03-工具表与白名单.md](03-工具表与白名单.md) | 工具签名、阶段白名单、focus 词表、fail-closed 校验 |
| 4 | [04-评测纪律.md](04-评测纪律.md) | 金标 runner、假绿对照、双 gate 测试、CI、复现两层 |
| 5 | [05-UI与交互.md](05-UI与交互.md) | 复验单形态、点回原文、作废/重跑、续命占位、四条红线 |
| 6 | [06-护栏预算与成本.md](06-护栏预算与成本.md) | Guardrails、步数/检索预算、模型与成本注记 |
| 7 | [07-验收-W1-W4.md](07-验收-W1-W4.md) | W1–W2 验收清单、W3 预检、W4 终审锁定判据与分级止损预案 |
| 8 | [08-拆单建议.md](08-拆单建议.md) | W1–W4 实施工单切分建议(供 to-tickets 或实施会话用) |
| 9 | [09-验收-W5-W8.md](09-验收-W5-W8.md) | W5–W8 验收判据 pre-registration 锁定版(K1–K7;统计层首次入判据) |
| 10 | [10-PhaseA-RAG.md](10-PhaseA-RAG.md) | Phase A RAG 子系统规格(retrieve 主缝;grilling→to-spec;Issue 见 tracker) |
| 11 | [11-PhaseV1-PrePublish.md](11-PhaseV1-PrePublish.md) | Phase V1 发前闭环(主缝=发前 Run 边界;ADR-0027;[#168](https://github.com/luxingjiang1993/FreshLatch/issues/168)) |
| 12 | [12-PhaseV1.5-EvidenceBound.md](12-PhaseV1.5-EvidenceBound.md) | Phase V1.5 Evidence-bound 补丁(主缝=确认边界;ADR-0029) |
| 13 | [13-PhaseI2-SecurityDemos.md](13-PhaseI2-SecurityDemos.md) | Phase I2 安全三例(主缝=召回信任边界+绿灯出口;ADR-0030;[#213](https://github.com/luxingjiang1993/FreshLatch/issues/213)) |
| 14 | [14-PhaseV2-PublishHook.md](14-PhaseV2-PublishHook.md) | Phase V2 发前钩子+主张台账(主缝=publish-hook 放行边界;ADR-0031;[#226](https://github.com/luxingjiang1993/FreshLatch/issues/226)) |
| 15 | [15-整仓分层验收.md](15-整仓分层验收.md) | 整仓编排验收(L0–L4;双绿灯;pre-registration;不含新功能决策) |
| 16 | [16-must-unknown-c9-护栏.md](16-must-unknown-c9-护栏.md) | #239 后 c9 误 stale：元陈述+主张数字回声逃逸；闸收紧+回归护栏；禁改 gold |
| 17 | [17-must-fresh-c6-all-hit.md](17-must-fresh-c6-all-hit.md) | 可选薄票：#241 后仅剩 c6 误 stale；追 gold `all_hit`；预锁止损；禁改 gold |

## 决议来源索引(本规格各节的权威出处)

| 决议 | 工单 | ADR / 评估文档 |
|---|---|---|
| 目录结构与模块划分 | #3 | ADR-0001 |
| 复验单 UI = FastAPI+HTML | #4 | ADR-0002 |
| 存储检索 = SQLite+BM25 多 stage 管线 | #5 | ADR-0003、《检索路线选型评估.md》 |
| Agent 循环 = 裸 tools 自写循环(ReAct) | #6 | ADR-0004、《Agent循环实现选型评估.md》 |
| LangGraph interrupt 人审模式研究 | #7 | 《langgraph-interrupt人审模式研究.md》 |
| 合成语料与金标(12 主张三档) | #8 | 《语料金标设计评估.md》 |
| 评测 harness 与假绿对照 | #9 | ADR-0005、《评测harness与假绿对照设计评估.md》 |
| Skills 文件内容设计 | #10 | 《Skills文件设计评估.md》 |
| HumanLatch 作废/续命最小闭环 | #11 | ADR-0006、《HumanLatch闭环设计评估.md》 |
| W4 验收标准操作化 | #12 | ADR-0007、《W4验收标准操作化评估.md》 |
| spawn_critic(focus) 词表 | #14 | 《spawn_critic-focus词表设计评估.md》 |
| 模型冒烟(qwen-flash go) | #2 | 《dashscope模型冒烟验证.md》 |
| 领域词表 | — | `CONTEXT.md` |
| 立项依据(冲突以切片为准) | — | `docs/product/FreshLatch-立项切片.md` |
| 双判一致;Auditor 在场 = 闸层不变量(废止 Lead `spawn_auditor`) | #20,#25,#48 | ADR-0009、ADR-0010;规格回填见 `03-工具表与白名单.md` §3.6 |
