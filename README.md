# FreshLatch（复验闩）

> Reverify latch for signed claims — from "once true" to "still verifiable now."

两周前那份判断，客户今天追问：**还成立吗？**

FreshLatch 不做新摘要，也不替你做商业裁决。它对照签发时原文（T0）与复验时点原文（T1），给你一份能点回证据的**复验单**：哪些仍可复验、哪些已失效、缺口在哪；过期、冲突、无 T1 原文支持的主张**不得保持绿灯**——人决定作废或续命。

仓库：[luxingjiang1993/FreshLatch](https://github.com/luxingjiang1993/FreshLatch)

---

## 它解决什么问题

顾问、研究员、战略岗常常已经出过一版判断，附件看起来可辩护。两周后世界变了：竞品改价、监管口径更新、访谈对象改口。人仍可能把**旧绿灯**发给客户——做错一次是职业风险。

你真正需要的不是「再写一篇」，而是：

> 给我一份能指回 T0 与 T1 原文的复验单：哪些仍成立、哪些必须作废、缺口是什么。

频率大约每 2–6 周一次「还成立吗」。FreshLatch 卖的就是这一次对照与收门。

---

## 你得到什么

主界面是**复验单**（不是聊天框）。每条已签发主张会落到四种状态之一：

| 状态 | 含义（人话） |
|------|----------------|
| **fresh** | 仍可复验——须有可点回的 T1 证据 |
| **stale** | 已失效——须能指回推翻它的 T1 原文 |
| **unknown** | 证据不足，或闸打回——不得假装还绿 |
| **void** | 人已作废——机器红灯之外的人决定 |

成交物还包括：

- **点回原文**：判定要能指到证据，而不是模型「记得」
- **HumanLatch（人闩）**：人对红/黄灯主张点「作废」或「续命」（续命必须带 T1 证据）；Agent **不得**自己把红灯改回绿灯
- **客户向复验备忘（可选导出）**：可转发的三分栏（仍成立 / 已作废 / 缺口），不含「建议进入/不进入市场」类裁决

一句话边界：**卖作废与缺口，不卖更快摘要，不卖自动决策。**

---

## 给谁用 / 不给谁用

**适合：**

- 独立顾问、产业研究员、战略岗——已经出过一版判断，要对自己上周附件负责
- 需要「研究 / 提案诚信」预算的个人或小团队（设计意图上的现金楔子）

**明确不适合：**

- 只要更快摘要的增长团队
- 要企业 SSO / 全家桶采购一次到位
- 要系统自动给出商业裁决的买方
- 把本仓当成通用记忆平台 / Agent 中台的采购

当前公开仓库以**合成课题与本地 demo**为主；真实客户机密不进作品集。

---

## 它怎么工作（短版）

一次复验大致是这条路径：

1. **导入**已签发主张（T0 卷宗形状：主张 + 当时证据引用）
2. **选定 T1 来源**（上传语料包、粘贴变更要点后确认入库、或使用内置合成评测包——界面会标明 synthetic）
3. **对照**：系统按 T1 原文检索与阅读，找「仍成立」与「已死」的依据
4. **判定落档**：`fresh` / `stale` / `unknown`；规则闸强制——无 T1 证据不得绿，`stale`/`unknown` 不得保持绿灯
5. **人闩**：人作废或续命；作废名单进下一轮，该主张不得再绿

技术上有 Lead / Critic / Auditor 等角色与规则闸，但对访客只需记住：**原文是真相，闸管放行，人管作废与续命。**

默认 demo 课题（合成）：「两周前那份『是否进入东南亚中小企业 AI 客服市场』的判断，现在还成立吗？」

---

## Demo / 当前状态（诚实）

- **可跑**：本地复验单 UI、主链复验、人审作废/续命、合成语料与闸层单测
- **标明 synthetic**：demo 与评测材料是合成的，不是真实客户卷宗
- **不是**：已上线 SaaS、已有付费客户、或「W12 已通过 / 一期测量已闭合」——请勿这样引用本仓
- **已知半成品**（细节见路线图与证据目录）：检索仍以 BM25 为主；记忆卫生等模块有代码但未全部挂进默认主链；联网自动采编未做

想看工程验收边界，请读 `docs/evidence/` 与根目录 `CONTEXT.md`，不要把 README 当成验收证书。

---

## 快速开始

**环境：** Python 3.11+；跑 LLM 主链时在仓库根配置 `.env`（至少 `DASHSCOPE_API_KEY`，OpenAI 兼容）。确定性单测可不依赖真实 Key。

```powershell
# Windows PowerShell：控制台 UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()

cd <repo-root>
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PYTHONPATH = "src"
python -m pytest -q          # 单测
python -m freshlatch.ui.app  # 复验单 UI → http://127.0.0.1:8000
```

Unix 等价：`source .venv/bin/activate`，`export PYTHONPATH=src`。主按钮文案是「开始复验」，不是「生成答案」。

语料入库示例：`PYTHONPATH=src python scripts/ingest_corpus.py`

---

## 更深的文档

| 想了解 | 去读 |
|--------|------|
| 产品立项与边界 | [`docs/product/FreshLatch-立项切片.md`](docs/product/FreshLatch-立项切片.md) |
| 术语表（主张 / T0·T1 / 闸 / HumanLatch） | [`CONTEXT.md`](CONTEXT.md) |
| 架构与规格 | [`docs/spec/00-架构总览.md`](docs/spec/00-架构总览.md)、[`docs/spec/README.md`](docs/spec/README.md) |
| 整合路线图 | [`docs/roadmap.md`](docs/roadmap.md) |
| 验收与证据 | [`docs/evidence/`](docs/evidence/) |
| Agent / 贡献约定 | [`AGENTS.md`](AGENTS.md) |

---

## 路线图（一瞥）

下一程大致是：**先把检索（RAG）做成可独立测量的子系统**，再补证据点回与契约口径，然后加固 Agent 评测与半激活模块的「接上或切除」。联网只允许「采编落盘成 T1 → 再复验」，不做开放问答主产品。完整条目见 [`docs/roadmap.md`](docs/roadmap.md)。

---

## 许可与免责

本仓库暂无独立 `LICENSE` 文件；使用前请自行确认合规需求。

**免责：** FreshLatch 输出的是复验对照与人闩记录，**不是法律意见，不是自动商业决策**。合成 demo 仅用于说明产品形态；真实客户机密请勿写入公开作品集。