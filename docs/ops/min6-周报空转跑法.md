# min-6 周报空转跑法

> **生产观测 ≠ 乙尺。** 空转完成 ≠ 周报绿 ≠ 实验成立。  
> 本页服务近端 E1：固定窗口把 [`docs/evidence/slo-min6/周报骨架.md`](../evidence/slo-min6/周报骨架.md) 六格填完；样本不足时写「样本不足」/「未计」/「未跑」，禁止 0% / 0 ms 假绿。  
> 成员定义以 [`生产观测最小6-索引.md`](生产观测最小6-索引.md) 为准。  
> **不改** `src/`、floors/gold/x1、`PRODUCTION_RETRIEVAL_MODE`、RESULT-Y/PREREG-Y。  
> 日期：2026-10-16（Asia/Shanghai）。

---

## 1. 何时算空转完成

| 勾 | 条件 |
|----|------|
| 窗口 | 文首写明起止与时区 Asia/Shanghai（建议半开 `[start, end)`） |
| 针 | `code_pin` = 当周 tip sha；`canary_pin` 指针 `docs/evidence/slo-min6/canary-pin.md` |
| 六格 | SLI 1–6 按骨架全部有值（允许「样本不足」「未计」「未跑」） |
| 防火墙 | 文首保留 ≠乙尺 / ≠模型变好 / Canary≠乙尺；自检勾选 |
| 禁 | 禁止用假 0% 填不足；禁止回写 RESULT-Y；禁止称乙 |

有真实流量时仍用同一跑法；只是格子从「样本不足」换成真实分子分母。

---

## 2. 步骤

1. 复制骨架为 `docs/evidence/slo-min6/周报-YYYY-MM-DD至YYYY-MM-DD.md`（结束日用半开终点日前一天的日历标签亦可，但文内 interval 必须自洽）。  
2. 填 `window` / `code_pin` / `canary_pin`。  
3. 按协议页逐格填（只读协议，不改协议）：

| SLI | 协议页 | 无账本时写 |
|-----|--------|------------|
| 1·2 | [`抽检-放行误放误拒.md`](抽检-放行误放误拒.md) | 样本不足（成对） |
| 3 | [`判定-unknown三分协议.md`](判定-unknown三分协议.md) | 样本不足 |
| 4 | [`人审-override周报.md`](人审-override周报.md) | 样本不足；保留 ADR-0023 声明 |
| 5 | [`延迟与检索回退周报.md`](延迟与检索回退周报.md) | 两列都「样本不足」或 P95「未计」；同一行 |
| 6 | [`冻结金标canary跑法.md`](冻结金标canary跑法.md) | **未跑**（空转默认不付费跑 canary） |

4. 勾防火墙自检。  
5. 人读结论段写明：空转完成与否、是否构成放行成功（否）、是否触及 RESULT-Y（否）。  
6. 按指标地图周节奏（[`metrics-map.md`](metrics-map.md) §2 Cadence）导出时，另抄人审 B 组三行：模板 [`人审-B2B3-周表模板.md`](人审-B2B3-周表模板.md)。B1 无伙伴会话写「样本不足」，禁本地空跑顶 B1；B2/B3 分母为 0 写「样本不足」，禁 0%。PL 盯周节奏，Eng 导出。

---

## 3. 样本不足句式（可粘贴）

```text
本周样本不足：窗口内无可核对生产终态 / latch_log 可计行 / 检索事件；对应格写「样本不足」或「未计」或「未跑」。禁止写成 0%、0 ms。生产观测 ≠ 乙尺。未回写 RESULT-Y。
```

SLI 6 专用：

```text
canary 本周未跑：pass rate 写「未跑」。Canary ≠ 乙尺。掉线处置=未跑。不回写 Y。
```

---

## 4. 非目标

- 空转不要求付费「跑」canary 或云模型  
- 不把空转绿写成 RESULT-Y 乙或注册通过  
- 不升 phase-2（cost / faithfulness 等）为主格  
- 不改检索臂与金标

## 5. 首周副本

[`docs/evidence/slo-min6/周报-2026-10-09至2026-10-15.md`](../evidence/slo-min6/周报-2026-10-09至2026-10-15.md)
