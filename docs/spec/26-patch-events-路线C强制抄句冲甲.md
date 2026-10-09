# 规格卷 26 — patch_events 路线 C · 强制抄句冲甲

> **to-spec 来源**: [#483](https://github.com/luxingjiang1993/FreshLatch/issues/483) · 父图 [#482](https://github.com/luxingjiang1993/FreshLatch/issues/482)  
> **ADR**: ADR-0036  
> **协议**: `docs/evidence/patch-events/PREREG-C.md`（**未激活**）  
> **评估**: `docs/research/patch_events-路线C强制抄句冲甲设计评估.md`  
> **卷号**: 26（避撞 B 的 24/25 与 ALT 旁路卷号）

## 目的地

把路线 C 冲甲决议落成可派工规格：继承 B 已验证机制包，增量实装强制抄句，过门闩前不得正式主跑。本卷**不含**业务实现代码义务以外的「保证甲」。

## 非目标

- 复活路线 A；改 B 成立格；B/C 同页二跑  
- 放宽 hard reject；金标进 score；保证甲  
- ALT B1′/同文四闸进主表  
- 称全面 SOTA / 优于 RARR·KPR  
- 未过门激活 `PREREG-C` / 开正式 n=100 进主表  

## 继承（承载）

| ID | 条款 | 出处 |
|---|---|---|
| H1 | 选取 R；k≥10；成立定义不放宽 | ADR-0034 · PREREG-B/C |
| H2 | T/B1 同 after 再分叉 | ADR-0035 |
| H3 | 结果只抄同一次主比较；一预注册一正式主跑 | #416 纪律 · PREREG-C |
| H4 | 门闩三条件；可扔报告不进 RESULT | ADR-0034 · PREREG-C |
| H5 | 不改生产检索常量；不改主张复验金标 | PREREG-C |

## 增量（实装）

| ID | 条款 | Acceptance 种子 |
|---|---|---|
| C1 | T after 强制抄句硬契约（= evidence_text 去空白） | 单测：契约路径产出逐字相同；非仅提示词含子串 |
| C2 | 正确槽构造可抄；不可抄作废换条 | 单测/夹具：不可抄正确槽不进正式名单或记缺额 |
| C3 | 同 after 上绑定缝仍可分开 T/B1 | 夹具：坏绑定样 T reject / B1 release |
| C4 | 新可扔门闩报告 GATE-C（对 C 机制） | 报告含三条件表；标明可扔；禁升格 RESULT-C |
| C5 | 产物路径 formal-generations-c / RESULT-C | 禁止写 b/旧 jsonl；未激活不填成立格 |
| C6 | B 负结果附录句入协议/结果壳 | 文面含 #480 丙与效应偏小；禁同页翻 B |

## 用户故事（派工用）

1. As a 评测工程师, I want T 臂 after 由强制抄句契约产出, so that C 相对 B 有可辩护增量且叙事为 copy-constrained。  
2. As a 评测工程师, I want 正确构造槽保证可抄, so that 门闩 k 不被结构性假阴性压死。  
3. As a 评测工程师, I want 同 after 再分叉仍在, so that T−B1 对照仍是绑定缝而非生成噪声。  
4. As a 纪律官, I want 新 GATE-C 可扔报告且未过不得激活, so that 不把门闩倒置。  
5. As a 纪律官, I want 不改 B 归档、不并 ALT 主表, so that 防火墙成立。  
6. As a 作者, I want RESULT-C 只抄一次主比较, so that 成立格不可手填。  
7. As an 面试讲解者, I want 固定引用 B 丙附录句, so that 不装从零开始。  
8. As a wayfinder, I want C 失败可关票删分支而留 A/B/ALT, so that 止损可执行。  

## 票序建议

1. **硬门**：强制抄句生成缝 + 同 after 继承夹具（C1–C3）  
2. **门闩**：GATE-C 报告格式与复测夹具（C4）— 可扔  
3. **名单/路径**：n=100 针与 formal-generations-c 壳（C5）— 默认不发  
4. **抄表壳**：RESULT-C 壳 + B 附录句（C6）— 未激活不填成立  
5. **（过门+人授激活后）** 正式生成 / 回放抄表 — Gate  

人轨（盲审附加、检索另轨、不能假绿）继续并行，不塞入 false-accept 主表。

## 云端派工

见 `docs/agents/patch-events-route-c-cloud-dispatch.md`（若本 PR 已落）。主代理边界：本 to-spec **可不含** `run_arms` 业务实现；由 enrich 后的 feat 票分窗 `/before-implement` → 新会话 `/implement`。
