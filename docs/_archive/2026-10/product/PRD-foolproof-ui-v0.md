# PRD v0.1：FreshLatch 傻瓜式 UI（硅谷满配，暂不含真人）

**状态**：群评后修订 · 待主人锁  
**日期**：2026-10-17  
**范围**：UI / 上手路径；**不改** RESULT-Y、闸门判定、成立格数字  
**成功一句话**：没接触过项目的新人，不看文档，≤5 分钟完成「导入→看到结果→拍板至少一条」

**群评来源**：FreshLatch傻瓜UI·PRD评（GitHub 前沿 / AI编程评估 / Grok Bot / 硅谷AI编程教学大师）

---

## 1. 问题

当前界面像实验台：协议词（claim / latch / T0 / fail-closed）与控件密度高，新人不知道自己在干什么、下一步点哪。

## 2. 目标用户（模拟）

- Persona：第一次用「结论复验」工具的知识工作者 / 面试官旁观角色  
- 任务：拿一批旧结论，对照新材料，知道哪些还能信、哪些要自己定  
- **作品叙事下限**（面试旁观）：60 秒能说出「产品在拦什么」（无 T1 / 证据不够则挡续命），不把 UI 过线说成主实验成功

## 3. Activation（硬门槛）

用户在首次会话内看到三类结果清单，并**处理完至少一条「要你确认」**：

| 白话清单 | 映射现四态（勿另造） | 首次一行定义 |
|---|---|---|
| 仍可信 | fresh | 证据仍支撑这条结论 |
| 可能过期 | stale / unknown | 材料变了或证据不够 |
| 要你确认 | latch pending | 系统拦下，需你拍板 |

**「处理」= 明确动作**：底层仍仅 `discard` | `renew`（文案可写作废 / 续命）；处理后该条立刻从「要你确认」移走。  
**挡续命是成功路径**：无 T1 时 renew 被挡须说明「挡住=产品在干活」，不当报错清空。

**量化下限（步骤 3 可收紧，不可放松）**：
- 模拟完成率 ≥4/5
- 是否 ≤5 分钟（**含** Start reverify 墙钟 ≈2min / 实测 ~137s）
- 记下卡在第几步

## 4. 方案摘要

| 层 | 做什么 | 不做什么 |
|---|---|---|
| 主路径 | 三步壳：①**默认主 CTA=一键样例**（导入降为次按钮）→ ②自动复验（白话进度：「正在用新材料核对旧结论」；可取消/进度可见）→ ③只审待拍板 | 首屏铺协议字段；主 CTA 写成「生成答案」 |
| 披露 | 默认白话 + 一个主按钮；协议进「高级/证据」（两层上限） | 改 fail-closed 语义 |
| 空态/错误 | 会出现什么、点哪个、样例入口；拦了什么、能怎么改 | 堆 reject_reason 枚举当主文案 |
| Boot 防护 | 傻瓜壳**禁止** `boot()`/`import` 洗掉勿发 / 待拍板 sheet（WIPE_NOTE） | 刷新后假失败当成功 |
| 实现 | 文案层 + 壳 + 样例 CTA；三类清单与协议词解耦 | 改正式跑数 / RESULT-Y；吹成 L4 / 主实验成功 |

## 5. 工作流（硅谷满配 − 真人）

| 步 | 产出 | Skill（装源） |
|---|---|---|
| 1 模拟盲测 | 卡点与需求清单；**先吃 playtest 债**（Full UX Go hold、`copy_wrong_job`、CTA、勿发 sheet、Control Δ n/a） | 本机已装：playtest / human-experience / echo |
| 2 UI 审计 | 删/藏/放大；两层披露上限 | 本机已装：ux-product-auditor / impeccable；**待装**：[progressive-disclosure](https://github.com/oborchers/fractional-cto/tree/main/saas-design-principles/skills/progressive-disclosure) |
| 3 锁主路径 | Activation 文案 + 三步 IA + 空态/主按钮白话 | 待装：[marketingskills/onboarding](https://github.com/coreyhaines31/marketingskills/tree/main/skills/onboarding)（勿整仓）；[ux-writing-skill](https://github.com/content-designer/ux-writing-skill) 或 empty-state-writer；可选 linearprincipals 定默认露出 |
| 4 设计出稿 | 线框/高保真 | 本机/插件：frontend-design / better-layout / better-ui / refero-design / superdesign（**不堆更多设计 skill**） |
| 5 实现 | 可点三步壳；判定不动；ux-writing 约束空态/错误 | Matt implement + 开发时 impeccable/better-* + ux-writing |
| 6 复测+量化 | 完成率/步骤/时长过 §3 下限 | 再 playtest；记分表人工 |

不过第 6 步不算过。真人盲测后补。

## 6. 非目标

- 改乙/丙成立结论、另跑 formal  
- 全盘视觉品牌重做（可后置）  
- 把 Matt 工程链当 UX skill  
- 把傻瓜 UI 过线写成「产品已 L4 / 主实验成功」

## 7. 验收

- [ ] 步骤 1–2 文档落盘（含 playtest 债）  
- [ ] **样例 CTA 一键可走完** 三类清单路径  
- [ ] 走通后 **不经 boot/import 洗掉待拍板清单**  
- [ ] 三类清单文案与协议词解耦；协议词默认仅在高级可见  
- [ ] 步骤②有白话进度；≤5min 计量含复验墙钟  
- [ ] 模拟复测：完成率 ≥4/5 且 ≤5min（或步骤 3 收紧后的阈值）  
- [ ] 旁观 60 秒能说出「产品在拦什么」

## 8. 下一步（立即）

主人锁 v0.1 → 装 progressive-disclosure + onboarding + ux-writing → 开步骤 1（先吃 playtest 债的模拟盲测）。
