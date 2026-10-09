# patch_events 路线 B · T/B1 同 after 云端派工（#469–#471）

> 父规格：#468 · `docs/spec/25-patch-events-路线B-T与B1同after.md` · ADR-0035  
> 决议：#466 · 地图 #465 · 评估 `docs/research/patch_events-路线B-T与B1可执行差与抬k设计评估.md`  
> 基线分支：`cursor/tb1-exec-diff-raise-k-df02`（含 PREREG-B 激活前修订与规格 25）  
> enrich 已完成；主代理只编排，不写业务代码。  
> 链：每票独立 Cloud 会话 · `/before-implement <ID>` → 同会话可继续 `/implement`

## 票序

| 顺序 | Issue | Cloud 职责 | 依赖 |
|---|---|---|---|
| 前沿 | #469 | T/B1 同 after 再分叉 + 夹具 | 无 |
| 前沿∥ | #471 | 抬 k：降正确假阴性（生成侧） | 建议与 #469 并行；须守同 after，冲突时 rebase #469 |
| #469 后 | #470 | 仓外门闩复测报告（可扔） | **硬依赖** #469 |

#440 仍须复测三条件过 + 激活后才可正式生成；本波次**不得**开 #440。

## 每票固定提示词骨架

```text
仓库 FreshLatch（luxingjiang1993/FreshLatch）。只做 GitHub Issue #<ID>（读全文含 ## Agent Guards）。
派工权威：docs/agents/patch-events-tb1-cloud-dispatch.md
父规格 #468 · 规格 docs/spec/25-patch-events-路线B-T与B1同after.md · ADR-0035 · PREREG-B（未激活）。
中文交流；注释用中文 UTF-8；不要 emoji；不要写 fallback；不要 /writing-plans。
1) 确认本票无 open blocker；#470 须确认 #469 已合入或本分支已含同 after 缝，否则停并评论等待。
2) /before-implement #<ID>；门不过则 enrich/停，勿写业务代码。
3) 门过 → 同会话 /implement（TDD）；一票一会话。
4) 权威命令：python -m compileall -q src ；相关 pytest ；ruff check（若触）。
5) Evidence 三行评论到 Issue：typecheck · tests · paths。
6) 开 draft PR（base 指向派工基线或 main 链上约定分支）；分支名含票号。
7) 禁止：激活 PREREG-B；开 #440 正式生成进主表；复活路线 A；金标/评委进 score；
   B1 核验失败仍放行（D2）；放松 T hard reject/逐字核验凑 k；改选取 R/成立定义；
   回写旧 PREREG/RESULT 成立格；改五处冻表面；密钥入库。
8) 角色：你是 Cursor 代理实现票；人类代理称「Ronin 代理人」；真人作者 Oriental Ronin。
```
