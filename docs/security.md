# FreshLatch 安全演示（I2）

> **层：冒烟。** 本页不是渗透认证，不报安全通过率，不报方差。硬 Exit 只有下面硬表三行。
> 权威：ADR-0030 · 父规格 #213。夹具正文由 #214 / #215 落地，本页只做薄表互链。不改 `docs/research/adversarial/INDEX.md`，不把目录升版写成 I2 Done。

## 硬表

| threat | demo_id | layer | repro_cmd | expected | smoke_note |
|--------|---------|-------|-----------|----------|------------|
| 越权召回 | `acl-t001` | `RetrievalStore.retrieve` 显式 `tenant_id` | `pytest tests/unit/test_i2_retrieve_trust.py -q -k acl_t001` | `tenant_id=B` 的结果不含租户 A | 冒烟 · 确定性 · 不绑 LLM |
| 间接注入 | `inj-t001` | `rule_gate` + `Runner._finalize` | `pytest tests/unit/test_rule_gate.py tests/unit/test_i2_injection_gate.py -q` | 污染 T1 不得给出 `fresh` 绿灯 | 冒烟 · 零 LLM · 不挂 `meta_gate` · **双标记子串**（「忽略指令」类 ∧「标为 fresh」类同时命中才拒）；未带 `t1_evidence_texts` 的旧调用点不启用 |
| 检索投毒 | `poison-t001` | `retrieve` 按 `poison`/`untrusted` 元数据剔除 | `pytest tests/unit/test_i2_retrieve_trust.py -q -k poison_t001` | 高分毒块不进入结果集 | 冒烟 · 确定性 · 不靠无标签启发式 |

短索引：`docs/evidence/i2/INDEX.md`。验收硬勾：`docs/evidence/i2/ACCEPTANCE.md`。

## 对照参考仓划界（口述 · 不升格 Exit）

面试追问「为什么不做参考仓那套」时用下面三句；**不是**新硬门、不报 ASR/通过率。

| 参考 | 他们证明什么 | 我们刻意不做什么 |
|------|--------------|------------------|
| PoisonedRAG | 无标签语料腐蚀：对抗段落打高分进召回 | 投毒硬门只认显式 `poison`/`untrusted`；不假装能检测无标签腐蚀 |
| TRIM / rag-evidence-inject · rag-redteam | 证据在场注入基准、指令掩码、canary ASR、CI 红队探针矩阵 | 注入落在既有 Gate fail-closed + 1× 真链路冒烟；不是 TRIM 中间件或红队产品 |
| ogx-evals | 企业多租户 ABAC、CTLR/AVR 评测矩阵 | 薄 `tenant_id` 真 `retrieve` 过滤即可；无租户管理面 / 完整 RBAC |
| SafeRAG | RAG 安全基准全景（Noise/Conflict/Toxicity/DoS 等） | I2 = 面试安全轮三例冒烟；≠ 安全平台或渗透认证 |

本机索引：`历史项目代码供参考/FreshLatch-roadmap-refs/`（清单见 `docs/FreshLatch-完整版参考清单.md`）。

## 可选（不计入 I2 Exit）

idea #4 过期伪装 `adv-fresh-t001` 可同波作面试弹药，证据页 `docs/evidence/i2/adv-fresh-t001.md`。**不计入 I2 Exit，不是硬表第四行。** I2 ≠ #4。
