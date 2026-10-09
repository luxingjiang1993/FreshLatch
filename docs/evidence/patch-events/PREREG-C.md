# patch_events 路线 C · 预注册协议页（强制抄句 / copy-constrained）

**状态：协议已锁 · 冲甲正式主跑已激活**

锁死日期：2026-10-09。决议：[#483](https://github.com/luxingjiang1993/FreshLatch/issues/483)、ADR-0036。评估见 `docs/research/patch_events-路线C强制抄句冲甲设计评估.md`。规格见 `docs/spec/26-patch-events-路线C强制抄句冲甲.md`。父图 [#482](https://github.com/luxingjiang1993/FreshLatch/issues/482)。

本页是路线 C 的预注册载体。激活后：同一预注册只允许一次正式主跑；不得改判据与选取；结果只抄同一次主比较写入 `RESULT-C.md`。

**相对路线 B 的关系**：B（`PREREG-B` / `RESULT-B` / `formal-generations-b`，#480）为**冻结丙归档**。本页**不回写、不改** B 归档。B 负结果附录见文末固定引用句。C 失败时关 C 票、删 C 分支；A/B/ALT 归档全留。

本页不改生产。主张收窄为 fail-closed **attested / copy-constrained** edit：T 的 after 必须是对已给 `evidence_text` 的强制抄句，并绑定已入库 T1；核验不过 hard reject。测量的是「改不改」在抄句约束下的风险差，不宣称自由 rewrite SOTA，不宣称优于 RARR·KPR。

## 作废与冻结声明

以下**不得**作为路线 C 冲甲主证据（可作动机或结构缺陷附录）：

- 旧 `PREREG.md` + 现 n=30 `RESULT.md` 链  
- 路线 A 工单 #419–#430（整链废除，禁止复活）  
- 路线 B 主跑数字：不得抄进本页 `RESULT-C` 成立格；只作负结果附录（见文末）  
- ALT 夹具/探针：不得升格为甲；不得改主比较追甲  

禁止回写旧 PREREG / PREREG-B 凑甲。禁止同页二次主跑 B 或 C。

## 目标分层

1. **纪律目标（必须）**：可识别选取（继承 R）；本页功率/止损；门闩；一次正式主跑；结果只抄同一次主比较。  
2. **求验目标（不保证）**：结果甲 = T-C、T-B1、T-B2 均成立。  
3. **诚实收口**：乙或丙仍合法。禁止把「设计冲甲」写成「将得到甲」。

甲/乙/丙投稿映射继承 `docs/evidence/patch-events/DECISION-LOG.md`，**不放宽**。

## 继承包（默认基线 · 本页不重开决议）

除非本页「路线 C 增量」明文改写，下列与路线 B / ADR-0034 / ADR-0035 一致：

| 项 | 锁 |
|---|---|
| 固定 k 选取 | **R**（各臂自然放行集；k:=T 自然放行数；m≥k 则集内 `claim_id` 升序取前 k；m<k → 该臂固定 k 误放无定义） |
| k 下限 | **10**（未达不得激活冲甲正式主跑） |
| 成立定义 | 点估计>0 且 95% bootstrap 下界>0；bootstrap 10000、种子 `20261007`、流名 `bootstrap` |
| T/B1 时序 | **同 after 再分叉**：共用同一 `after_text` 后，T=绑定∧核验；B1=仅核验；两边不过均 hard reject |
| 禁止 | 空分 claim_id top-k 主选取；S/S+R（本期）；金标/评委/用户裁决进 score；放松 hard reject/绑定/逐字核验凑 k；无限加 n 不改本页 |

样本框、配额、构造算子（坏槽）、四臂角色（C/T/B1/B2）、指标定义、消融四项、评委有效登记与评分细则、用户抽检规则：**继承** `PREREG-B.md` 对应节（B 归档合入后的仓内路径；合入前以 #433/#472/#480 树尖为准）。本页正式 n 与门闩见下，不以旧 n=30 为主门槛。

### 配额（正式）

| 用途 | 数值 | 日期 | 条款替换 | 删除 | 合计 |
|---|---:|---:|---:|---:|---:|
| pilot（流程，不进主表） | 4（2/2） | 4（2/2） | 4（2/2） | 3（1/2） | 15 |
| n=100（路线 C 满样本门槛） | 25（12/13） | 25（12/13） | 25（12/13） | 25（12/13） | 100 |

名单以 `docs/evidence/patch-events/SPLIT-pe-v2.json` 为起点；实现票可锁 `SPLIT-pe-v2-route-c.json` 或显式复用并登记针。pilot id 不进正式 n。

## 路线 C 增量（相对 B）

### 强制抄句（生成器主 · 构造辅）

1. **T 生成器硬契约**：对每一候选，T（及与 T 共用的同 after 源）的 `after_text` **必须**等于请求内已有 `evidence_text` 去掉首尾空白后的文本（强制抄句）。这是契约/算子层约束，**不是** B 的软提示「请对齐」。  
2. **同 after**：B1 消费与 T 同一份抄句后的 `after_text`，再分叉决策闸（绑定缝仍为唯一可执行决策差）。  
3. **构造辅**：正确金标槽必须保证所绑 T1 chunk 的 `evidence_text` 可作为合法 after（可抄）；做不出则该槽作废，换下一条主张，**算子不改成更好做的**。坏槽仍按继承的扰动算子；禁止为凑差把坏样改成「抄对证据仍标坏」。  
4. **核验**：仍为去空白后 `after_text` 与 `evidence_text` 逐字相同；T 不过 → hard reject。禁止放宽核验或绑定来凑 k。  
5. **叙事**：对外写 attested / **copy-constrained** patch；禁止写成自由 rewrite 全面优于对照。

### 实验组（C 口径摘要）

| 组 | 做法 |
|---|---|
| C | 无证据改写。不绑定，不核验，不 hard reject。生成成功即自然放行。 |
| T | copy-constrained attested：after=强制抄句；须绑定已入库 T1；核验不过 hard reject。与 B1 同 after。 |
| B1 | 同 after 后仅核验；不过 hard reject；不跑绑定闸。禁止核验失败仍放行凑差。 |
| B2 | KPR 式 claim→diff；核验不过不自动 hard reject（继承 B）。 |

### ALT

B1′ / 同文四闸 / `compare_alt_*` **仅附录**，不进本页主表，不改主 `compare_primary` 追甲。

## 主比较与成立（不放宽）

比较顺序写死：T 对 C → T 对 B1 → T 对 B2。配对差 = 对照误放率 − T 误放率。成立定义见继承包。结果表三条 false-accept 与 k **只抄**同一次主比较输出。成立格不得手填。禁止把门闩/探针数字抄进成立格。

## 功率 / 止损 / 主跑次数

- **k 下限**：10。  
- **n**：100。  
- **止损**：正式主跑后若 T-B1 或 T-B2 点估计 ≤0 → 不得称甲；按乙或丙收口；禁止改选取或成立定义后重跑本预注册。  
- **同一预注册只允许一次正式主跑**。

## 仓外试分离门闩（已激活 · 见激活批注）

门闩报告不进主表，可扔。路径建议：`docs/evidence/patch-events/GATE-C-*.md`。规则必须与本页 R 一致。

过门（同时满足）后才允许写激活批注：

1. T 相对 B1 的固定 k 误放差方向为正；  
2. T 相对 B2 的固定 k 误放差方向为正；  
3. T 的 k ≥ 10。

**禁止**把 #479 `GATE-K-PROBE`（B 机制探针）升格为本页已过门。须对 **C 强制抄句机制** 重新出可扔报告。夹具层 `GATE-C-FIXTURE` 绿 ≠ 真数据正式过门；不得把夹具数字抄进 `RESULT-C` 成立格。

复测序：夹具 → 只读已保存生成冒烟 →（可选）人授小探针；均不进 `RESULT-C`。

## 日志与产物路径

- 正式入口：`python -m freshlatch.eval.patch_events_formal_c`（**默认不发**；须激活 + `--authorize-send`）  
- 名单针：`docs/evidence/patch-events/SPLIT-pe-v2.json` 的 `n100`（与 `load_formal_c_n100` / 路线 B 同针）  
- 正式生成：`docs/evidence/patch-events/formal-generations-c.jsonl`（或 `docs/evidence/patch-events-c/` 下实现票写死路径）  
- **禁止**写入 `formal-generations-b.jsonl`、旧 `formal-generations.jsonl`  
- 评委日志：`data/exp/patch-events-c/judge-logs/`（密钥不入库）  
- 结果：`docs/evidence/patch-events/RESULT-C.md`（实现票建壳；未激活前不得填成立格冒充已跑）

## 反 HARKing

见 B 丙后：同页二跑 B、降 CI、拿掉 B1、改成立定义、并 ALT 主表追甲 = 禁止。激活后改本页判据或选取 = 本预注册作废。补定 draft ≠ 本页原文。

## B 负结果附录（对外固定引用句）

> 路线 B（`PREREG-B` / `RESULT-B`，#480）在选取 R、T/B1 同 after、生成对齐提示齐备并过仓外门闩后，正式主跑一次：k=42；T−C / T−B1 / T−B2 点估计均 >0，但 95% CI 下界均 ≤0 → **结果丙**。说明「可识别 + 过门」≠ 甲；核心教训是**效应偏小**。B 全套冻结为丙归档；禁止同页二次主跑、禁止降 CI/拿掉 B1 翻盘。路线 C 另开本页，增量假设为强制抄句加大可辩护 T 相对差；不保证甲。

## Related Work 边界

继承 B：对照的是「改」的风险，不是「答」的风险。C 额外声明：主主张为 copy-constrained attested edit，不装自由改写方法首创。

## 激活批注

- **日期**：2026-10-09（UTC）
- **仓库针**：`821e8a1`（分支 `cursor/patch-events-route-c-copy-constrained-68b0`；#485 强制抄句 + #487 formal-c + #486 GATE-C 夹具 + #488 RESULT-C 壳；激活前 tip）
- **门闩依据**：`docs/evidence/patch-events/GATE-C-FIXTURE.md`（**层=fixture** · `gate_passed=true` · 可扔；**非**真数据正式过门）。**禁止**升格 #479 `GATE-K-PROBE`。
- **批准**：本会话 Ronin 代理人收到真人 Oriental Ronin 之人类代理明文「批准激活 PREREG-C 并正式主跑一次。」
- **约束**：同一预注册只此一次正式主跑；禁止 HARKing 改成立定义或选取 R；禁止把 GATE-C / 探针 / RESULT-B 数字抄进 RESULT-C 成立格；不保证甲。

## 修订记录

| 日期 | 工单 | 修订摘要 | 改了什么 | **未**改什么 |
|---|---|---|---|---|
| 2026-10-09 | #483 / ADR-0036 | 初锁：路线 C · 强制抄句 · 继承 R/同 after/门闩 · 未激活 | 新预注册页与抄句增量 | 甲定义；B 归档；ALT 主表 |
| 2026-10-09 | #490 | 人令激活 + 一次正式主跑授权 | 文首已激活；本激活批注 | 甲定义；B 归档；选取 R；成立定义 |
