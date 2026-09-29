# Phase V1.5 ACCEPTANCE

> **层身份：冒烟 / 对客 demo 层**（零 LLM CI 夹具可复跑）。不报方差；不作统计显著声明；**禁止**单次运行报 C vs T 显著。本页不是 Hard-Gold，不是改生产默认臂授权，不是论文 n≥30 结论。  
> **判据：** roadmap Phase V1.5 Exit；`docs/spec/12-PhaseV1.5-EvidenceBound.md`；ADR-0029；grill V15-Q14 / V15-Q21 预锁。  
> **日期：** 2026-09-29  
> **对齐：** `origin/main` 合入 #199/#200/#201 后 · Issue [#202](https://github.com/luxingjiang1993/FreshLatch/issues/202)

## 1. 交付物在仓

| 交付 | 路径 | 状态 |
|------|------|------|
| 规格 | `docs/spec/12-PhaseV1.5-EvidenceBound.md` | 在仓 |
| ADR-0029 | `docs/adr/0029-v1.5-evidence-bound补丁与独立确认API.md` | 在仓 |
| 评估 | `docs/research/V1.5-Evidence-bound补丁设计评估.md` | 在仓 |
| propose/confirm | `src/freshlatch/evidence_bound.py` | 在仓（#198/#199） |
| 导出 | `src/freshlatch/evidence_bound_export.py` | 在仓（#201） |
| 复验单条带 UI | `src/freshlatch/ui/app.py` | 在仓（#200） |
| 主缝 e2e | `tests/unit/test_evidence_bound_e2e.py` | 在仓（本票） |
| V1 发前回归 | `tests/unit/test_prepublish_e2e.py` | 回归不红 |
| 顾问样例包 | `data/packs/v1-mck-soai/` | 复用，不另造垂直 |

## 2. 复跑命令（权威）

```bash
python -m compileall -q src
pytest tests/unit/test_evidence_bound_e2e.py tests/unit/test_prepublish_e2e.py -q
# 核对本文件 docs/evidence/v15/ACCEPTANCE.md
```

本机 2026-09-29 结果：**compile exit 0**；**8 passed**（e2e 4 + prepublish 4）。

## 3. 预锁脚本（禁 HARKing）

对照 ADR-0029 §8 / V15-Q14。脚本步骤写死于 `tests/unit/test_evidence_bound_e2e.py` → `PRELOCK`；**禁止事后改期望凑绿**。

| 步 | 动作 | 期望 |
|----|------|------|
| 0 | 样例包主张态：mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale | 包结论 **勿发** |
| 1 | 对人审范围 **discard mck-1 与 mck-4**（不 discard mck-3） | 包结论 **需补丁** |
| 2 | 对 **mck-3** 表单/API Evidence-bound 补丁 → confirm（有证） | 正文覆盖；T 臂账本行 |
| 3 | 单条再验触发 | `reverify=true` / `reverify_triggered` |
| 4 | 导出包 | JSON + 短 MD 关键字段存在 |

HTTP 主缝：`test_v15_prelock_main_seam_hard_bars`（夹具薄 URL + latch decide + `/api/patch/*`）。  
夹具等价：`test_v15_prelock_library_fixture_equivalent`（`voided` 等价 discard + 库级 propose/confirm）。

## 4. 硬条四勾（硬 Exit · 可核对）

| # | 硬条 | 判定 | 证据指针 |
|---|------|------|----------|
| 1 | **无证拒确认**（空 `t1_ids` → 拒；正文与正式账本零写） | **pass** | `test_v15_prelock_main_seam_hard_bars` / library 等价：`error_code=PATCH_EMPTY_T1` |
| 2 | **有证 confirm**（`t1_ids ⊆` 本 Run 已入库 T1 → 正文覆盖 + `arm=T`） | **pass** | 同上；`patch_events` T 行含 before/after |
| 3 | **reverify=true / 单条再验触发** | **pass** | `reverify_requested` ∧ `reverify_triggered`；事件 `reverify=true` |
| 4 | **导出存在**（JSON + 短 MD 关键字段） | **pass** | `result.export` / HTTP `export`；`REQUIRED_JSON_KEYS` |

## 5. 加分勾（非硬 Exit）

| 项 | 判定 | 说明 |
|----|------|------|
| 升包结论「可发」 | **加分 pass**（夹具再验 → fresh） | **不是**硬 Exit。ADR-0029 / V15-Q21：Exit **不**硬绑「可发」。真模型再验为手测/里程碑加分，本页零 LLM 夹具仅证明「可升格路径可演示」。 |

## 6. 护栏（本票未破）

- [x] HumanLatch `VALID_ACTIONS` 仍仅 `discard|renew`（`test_v15_valid_actions_and_default_arm_unchanged`）
- [x] 生产默认检索臂仍 `bm25`
- [x] 无薄对话 / stub；发前 UX 无 C|T 开关（既有 #200 UI 测）
- [x] 既有 V1 发前主缝 `test_prepublish_e2e` 不红

## 7. 可引用句（禁升格）

> V1.5（本地 ACCEPTANCE）：Evidence-bound 主缝冒烟可复跑；硬条四勾（拒无证 / 有证 confirm / 单条再验 / 导出）均 pass。档=冒烟·对客 demo。升「可发」=加分非硬条。不是 Hard-Gold，不是 C vs T 显著，不是改默认臂，不是吹首次/PCC。远程 issue CLOSED 不替代本文件。

## 8. 非本批 / 仍开

- 薄对话（实装或 stub）  
- 扩 HumanLatch 第三动词 / renew 改正文  
- Exit 硬绑「可发」或改生产默认臂  
- #8 Policy-as-code 并行；论文 n≥30  
- DoD 关门摘要：`docs/evidence/v15/V15-DoD-CLOSE.md`（[#203](https://github.com/luxingjiang1993/FreshLatch/issues/203)；本 ACCEPTANCE 不代关 DoD）  
- 本票 #202 已 CLOSED（`GROK-PROXY-APPROVED #202`）；父规格 #196 等 #203 代 Exit 后由编排器收口
