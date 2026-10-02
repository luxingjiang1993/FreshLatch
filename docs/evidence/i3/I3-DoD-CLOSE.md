# Phase I3 DoD close · smoke / 面试加固

> **档：** 冒烟 / 面试加固（I3）。不报方差；不作统计显著；**不是**改生产默认臂授权；**不是**政策平台；**不是**真事故复盘。  
> **日期：** 2026-10-02  
> **Refs：** [#253](https://github.com/luxingjiang1993/FreshLatch/issues/253)（本票 · Exit 代收） / parent [#248](https://github.com/luxingjiang1993/FreshLatch/issues/248) / 子票 #249–#252  
> **规格 / 决议：** `docs/spec/20-PhaseI3-InterviewHardening.md` · ADR-0032 · 评估 `docs/research/I3-面试加固三轨设计评估.md`  
> **硬 Exit 权威：** `docs/evidence/i3/ACCEPTANCE.md`（文首层标签；三轨分节互不顶替）

本页是 I3 Exit 的可引用关门摘要。Exit 由 Ronin 代批（等 `GROK-PROXY-APPROVED #253`）；实现本摘要的 PR 合 main 后可关本票。

## Demo path

政策拒：声明式出处禁区命中 → `POLICY_SOURCE_BAN` 不得绿灯（旁路，不改 `rule_gate` 不变量正文）。B′：合成超时 → 结构化错误；人审重放不双写；轨迹 → 闸分布一页（合成夹具 · 非真事故）。Hard-Gold：分文件难金标 n≥20 · traps/对抗≥30% 可跑；默认臂仍 `bm25`（骨架 ≠ 换臂）。见 `docs/evidence/i3/ACCEPTANCE.md`。

## DoD 硬 Exit（三轨 · 引用 ACCEPTANCE）

- [x] **轨 A · #8 政策拒旁路**  
  ACCEPTANCE §2；`pytest tests/unit/test_i3_policy_gate.py -q`；[#249](https://github.com/luxingjiang1993/FreshLatch/issues/249) · [PR #254](https://github.com/luxingjiang1993/FreshLatch/pull/254)
- [x] **轨 B · B′ 合成夹具**  
  ACCEPTANCE §3；`pytest tests/unit/test_i3_agent_hardening.py -q`；[#250](https://github.com/luxingjiang1993/FreshLatch/issues/250) · [PR #255](https://github.com/luxingjiang1993/FreshLatch/pull/255)
- [x] **轨 C · Hard-Gold 骨架**  
  ACCEPTANCE §4；`pytest tests/unit/test_i3_hard_gold.py -q` · `python -m freshlatch.eval retrieve --hard`；[#251](https://github.com/luxingjiang1993/FreshLatch/issues/251) · [PR #256](https://github.com/luxingjiang1993/FreshLatch/pull/256)
- [x] **`docs/evidence/i3/ACCEPTANCE.md`**  
  文首层标签；三轨分节；[#252](https://github.com/luxingjiang1993/FreshLatch/issues/252) · main `b21845e`

## Out of Scope（确认未偷渡）

- [x] **改 `PRODUCTION_RETRIEVAL_MODE`**——仍 `bm25`
- [x] **宣称 Hard-Gold 已授权换臂**——未宣称；骨架 ≠ 换臂
- [x] **OPA/Cedar / 政策平台**——未开
- [x] **改写 `rule_gate` 不变量语义**——仅旁路组合
- [x] **Memory / 多 Agent / 跨 Provider 硬关门**——未做
- [x] **解冻 Studio**——未解冻
- [x] **C′ / 图谱 / CMS / High-Recall 改默认**——未开
- [x] **用 I3 替代 I1/I2**——未替代
- [x] **报方差 / 统计显著**——未报
- [x] **整包再验挂回发前钩子**——未挂（ADR-0031）

## 不宣称换臂或政策平台

本证据层只是冒烟 / 面试加固。骨架语料与合成夹具不得升格为「已改默认臂」「政策平台已交付」「已修真生产事故」。

## 叙事对齐（roadmap）

- `docs/roadmap.md` Phase I3 Exit：**已齐（冒烟/面试加固）**；Out 清单未偷渡；改臂另决议。
- 父规格 #248 收口评论指针本文件与 ACCEPTANCE。

## 本机关单命令

```text
$ python -m compileall -q src
exit:0

$ PYTHONPATH=src python -m pytest tests/unit/test_i3_policy_gate.py tests/unit/test_i3_agent_hardening.py tests/unit/test_i3_hard_gold.py tests/unit/test_i3_acceptance.py -q
25 passed
exit:0
```
