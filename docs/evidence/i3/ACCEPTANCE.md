# Phase I3 ACCEPTANCE

> **层身份：冒烟 / 面试加固（I3）。不报方差；不作统计显著；**  
> **不是改生产默认臂授权；不是政策平台已交付；不是已修真生产事故。**  
> **判据：** ADR-0032；`docs/spec/20-PhaseI3-InterviewHardening.md`；父规格 #248。  
> **日期：** 2026-10-02  
> **对齐：** `origin/main`（#249/#250/#251 实现经 PR #254/#255/#256）  
> **三轨互不顶替：** 任一轨失败不得标 I3 Exit 绿。

## 1. 冒烟声明（文首）

本页验收层 = **冒烟 / 面试加固（I3）**。  
确定性硬门覆盖 #8 政策拒、B′ 结构化错误/重入/闸分布、Hard-Gold 默认臂断言与 hard 集可跑。  
**禁止**把本页读成：改臂授权、政策平台已交付、真生产事故复盘、方差/统计显著、或用 I3 顶替 I1/I2。

## 2. 轨 A · #8 Policy-as-code（出处禁区旁路）

| # | 硬条 | 判定 | 证据指针 |
|---|------|------|----------|
| A1 | 声明式出处禁区可加载；命中 → `POLICY_SOURCE_BAN` 不得绿灯 | **pass** | `pytest tests/unit/test_i3_policy_gate.py -q` · 规则 `data/policy/source_ban.json` · 夹具 [`policy-source-ban.md`](./policy-source-ban.md) · 模块 `src/freshlatch/gates/policy_gate.py` |
| A2 | 未命中不误伤既有 fresh 回归；**未改** `rule_gate` 不变量正文 | **pass** | 同上；`pytest tests/unit/test_rule_gate.py -q` |
| A3 | 文档标明「政策拒 ≠ 新鲜度拒」；无 OPA/Cedar | **pass** | [`policy-source-ban.md`](./policy-source-ban.md) · ADR-0032 |

实现：[#249](https://github.com/luxingjiang1993/FreshLatch/issues/249) · [PR #254](https://github.com/luxingjiang1993/FreshLatch/pull/254)

## 3. 轨 B · B′ 合成夹具

| # | 硬条 | 判定 | 证据指针 |
|---|------|------|----------|
| B1 | 超时/假绿 → 结构化错误（`AGENT_TIMEOUT` / `SYNTHETIC_FALSE_GREEN`），不静默绿 | **pass** | `pytest tests/unit/test_i3_agent_hardening.py -q` · `src/freshlatch/i3_hardening.py` |
| B2 | 人审 discard/renew 重放不双写 `latch_log` 坏账 | **pass** | 同上（幂等用例） |
| B3 | 轨迹 → 闸分布一页（CLI/MD）含可读计数 | **pass** | `python -m freshlatch.i3_gate_dist` · [`bprime-synthetic.md`](./bprime-synthetic.md) |

**合成夹具 · 非真事故复盘。** 不做 Memory/多 Agent；未挂整包再验到 `publish_hook`。

实现：[#250](https://github.com/luxingjiang1993/FreshLatch/issues/250) · [PR #255](https://github.com/luxingjiang1993/FreshLatch/pull/255)

## 4. 轨 C · Hard-Gold 骨架

> **本波 Hard-Gold = 骨架语料 + 增益门复跑；未授权改臂。**

| # | 硬条 | 判定 | 证据指针 |
|---|------|------|----------|
| C1 | 与冒烟分文件；n≥20；traps/对抗≥30% | **pass** | `data/eval/retrieve_hard_gold.json`（n=20 · traps/对抗=8 · 40%）· `docs/hard-gold.md` |
| C2 | hard 集可跑 BM25 报告；增益门沿用 I0；**断言** `PRODUCTION_RETRIEVAL_MODE=="bm25"` | **pass** | `pytest tests/unit/test_i3_hard_gold.py -q` · `python -m freshlatch.eval retrieve --hard` · [`reports/retrieve-hard-gold-bm25.md`](../../reports/retrieve-hard-gold-bm25.md) |
| C3 | 规格文首骨架·不改臂；禁止把 n=36 冒烟称作 Hard-Gold 已过 | **pass** | `docs/hard-gold.md` |

实现：[#251](https://github.com/luxingjiang1993/FreshLatch/issues/251) · [PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256)

## 5. 联合 Out（偷渡一票否决 · 本页确认未犯）

- [x] 未改 `PRODUCTION_RETRIEVAL_MODE`（仍 bm25）
- [x] 未宣称 Hard-Gold 已授权换臂
- [x] 无 OPA/Cedar / 政策平台
- [x] 未改写 `rule_gate` 不变量语义
- [x] 无 Memory/多 Agent 硬关门
- [x] 未解冻 Studio；未开 C′/图谱/CMS
- [x] 未用 I3 替代 I1/I2
- [x] 未报方差/统计显著
- [x] 未把整包再验挂回发前钩子

## 6. 复跑命令（权威 · 预锁）

```bash
python -m compileall -q src
PYTHONPATH=src pytest tests/unit/test_i3_policy_gate.py tests/unit/test_i3_agent_hardening.py tests/unit/test_i3_hard_gold.py -q
PYTHONPATH=src python -m freshlatch.eval retrieve --hard
```

本机记录（2026-10-02）：三测合跑 **24 passed**；Hard-Gold `n=20` · traps/对抗=`8` · 臂=`bm25`。

## 7. 可引用句（禁升格）

> I3（本地 ACCEPTANCE）：政策拒旁路 / B′ 合成夹具 / Hard-Gold 骨架三轨硬条分节 pass。档=冒烟/面试加固。不是改臂授权，不是政策平台，不是真事故复盘，不报方差。

## 8. 非本票 / 指针

- DoD 关门摘要：`docs/evidence/i3/I3-DoD-CLOSE.md`（#253；本 ACCEPTANCE 不代关 DoD）
- 父规格 [#248](https://github.com/luxingjiang1993/FreshLatch/issues/248)
