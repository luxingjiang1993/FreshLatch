# 15 分钟复现卡（面试/交接 · IR-PACK #738）

> 层身份：**代码不变量复现卡**。跑的是零 LLM 双路测试（CI gate 1 同命令），
> **不是**重跑正式实验——路线 Y 主跑 n=400 的正式结果不重放，只指
> [`docs/evidence/patch-events/RESULT-Y.md`](../evidence/patch-events/RESULT-Y.md)。
> Ticket [#738](https://github.com/luxingjiang1993/FreshLatch/issues/738) · Parent [#734](https://github.com/luxingjiang1993/FreshLatch/issues/734) · Brief `org-os/runbooks/briefs/IR-PACK.md` §D。
> 本页是合入硬闸（R-06）：无此卡不合入。

---

## 0. 克隆 + 安装（≈5 min）

```bash
git clone https://github.com/luxingjiang1993/FreshLatch.git
cd FreshLatch
python -m venv .venv && .venv\Scripts\activate        # Windows；POSIX 用 source .venv/bin/activate
pip install -e ".[dev]"
```

零 LLM 依赖（ADR-0005）：不需要任何模型密钥、不下载权重、不打网。
`tests/conftest.py` 已把 `FRESHLATCH_LOCAL_EMBED=0` / `FRESHLATCH_NEURAL_RERANK=0`（见 [local-embed.md](local-embed.md)）。

## 1. 双路 pytest（≈5–10 min）

### 路 1 · CI 等价路（外机验收，预期全绿）

```bash
ruff check
set PYTHONIOENCODING=utf-8          # POSIX: export PYTHONIOENCODING=utf-8
python -m pytest tests/ -q
```

与 `.github/workflows/ci.yml` 同命令（Windows · Python 3.11 · 零 LLM）。
CI 用 `fetch-depth=1` 检出，**没有** `origin/main`，冻结面守卫用例自动 skip——
所以 CI 绿 = 代码不变量没破（gate 1）。

### 路 2 · 本机冻结面守卫路（改冻结文件前的哨兵）

```bash
git fetch origin main               # 需要本地有 origin/main 引用
python -m pytest tests/eval/test_g2_should_abstain.py -q
```

`test_do_not_touch_and_ci_still_collects_eval` 把工作区对 `origin/main` 的 diff
对 do-not-touch 名单（`RESULT-Y.md` / `PREREG*.md` / `data/eval/` / `ci.yml` / 依赖钉 /
`src/` 全体等）做硬断言：

- 在 **main 或干净工作区**：绿。
- 在 **动了 `src/` 的功能分支**：按设计报红——那是守卫在工作，**不要**去"修"它；
  先在分支上确认 `git diff origin/main...HEAD -- docs/evidence/hard-gold-arm/ docs/evidence/patch-events/RESULT-Y.md data/exp/x1/ src/freshlatch/disposition.py` 为空，再判断红是不是预期。
- 路 2 语义 = 冻结面哨兵；路 1 语义 = 全量回归。两路都绿（路 2 在合入后的 main 上绿）才算整包可指认。

## 2. 正式结果指针（不重跑）

| 要什么 | 去哪 | 一句话状态 |
|--------|------|------------|
| 路线 Y 正式主跑（n=400） | [`RESULT-Y.md`](../evidence/patch-events/RESULT-Y.md) | **结果丙**；T−C 不成立（点估计 0.093，95% 下界 −0.006）；k=151；判丙不判甲 |
| Y 口径预注册 | [`PREREG-Y.md`](../evidence/patch-events/PREREG-Y.md) | 冻结；同一预注册禁止第二次正式主跑充数 |
| 金标闸（改臂授权） | [`docs/evidence/hard-gold-arm/ACCEPTANCE.md`](../evidence/hard-gold-arm/ACCEPTANCE.md) | 冒烟/决策闸：已过线 · 未换臂 · `PRODUCTION_RETRIEVAL_MODE` 未授权改动 |
| 拒答行为夹具（G2 表） | [`GOLD-TABLE-v0.md`](GOLD-TABLE-v0.md) + [拒答行为夹具.md](拒答行为夹具.md) | 合成离线夹具；夹具绿 ≠ 注册 G1/A1 过线 ≠ RESULT-Y 乙 |
| 指标地图 | [metrics-map.md](metrics-map.md) | North Star = B2 人审有效动作率；pytest 计数是 guardrail 不是 North Star |

硬边界（复述 RESULT-Y 防火墙）：演示可过 ≠ 测量可信；烟测/夹具/本机 demo **不是**
正式 RESULT；不得把路线 Y 写成成功；不改冻结面让数字变好看。

### 若顺手开 UI demo（非主线）

本页主线仍是零 LLM 双路 pytest + RESULT-Y 指针；UI 只是可选顺手。P2 会话态 = A（单进程 `_state`，不分桶）：**一浏览器、一窗口、一 `freshlatch.ui` 进程**。勿开第二标签「对照」——会覆盖进程内 `_state`。要干净态：走高级重置 `POST /api/session/reset`（与现 UI 行为一致），不要靠新标签。本机 UI demo ≠ 正式 RESULT / 测量可信。

## 3. 出人 15 min 走查清单

- [ ] 路 1：`ruff check` 绿 + `pytest tests/ -q` 绿（fresh clone，无密钥）。
- [ ] 路 2：`test_g2_should_abstain.py` 在 main 上绿；在功能分支上理解"按设计报红"。
- [ ] 打开 `RESULT-Y.md` 能读到：判丙、k=151、T−C 不成立、不得判甲。
- [ ] 打开 `hard-gold-arm/ACCEPTANCE.md` 能读到：已过线 · 未换臂 · 改臂须走授权闸。
