# V1 顾问报告样例包 · McKinsey State of AI

本目录是 **V1 近端唯一垂直「顾问报告」** 的样例主包：基于 McKinsey *State of AI* 公开洞察页的**主张清单 + T0/T1 摘录块 + 出处 URL/日期元数据**。

## 边界（必读）

- **单一垂直 = 顾问报告**。本包服务发前复验 demo / 面试叙事，不是研报主包，也不是合规主包。
- **仓内只存摘录**：禁止把整本 McKinsey PDF 当开源语料再分发（ADR-0027 / #169）。
- **thesis-1 / QuoteTTL（p1-quotettl）** 仍可回归，**不算**第二产品垂直。
- 摘录来自公开洞察页短段，供可指认出处；非全文字面镜像。

## 波次

| 波 | 材料 | 约日期 | 洞察页 |
|----|------|--------|--------|
| T0 | *How organizations are rewiring to capture value* | 2025-03-12 | https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-how-organizations-are-rewiring-to-capture-value |
| T1 | *The state of AI in 2025: Agents, innovation, and transformation* | 2025-11-05 | https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai |

## 文件

| 路径 | 用途 |
|------|------|
| `docket.json` | 已签发主张清单（可导入） |
| `provenance.json` | 主张 → 出处 URL/日期 |
| `corpus/t0/*.md` | T0 摘录（`## pN` 结构锚） |
| `corpus/t1/*.md` | T1 摘录（`## pN` 结构锚） |

装载提示：本包**不**注册进 `FRESHLATCH_ACTIVE_PACK` 已知表（避免冒充第二 active_pack 垂直）。主张可通过 docket / 主张导入稿引用；语料可按路径指向本目录 `corpus/`。
