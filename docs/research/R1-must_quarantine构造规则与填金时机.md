# R1：`must_quarantine` 构造规则与填金时机

- **状态**: 事实汇总（RESEARCH 层；非产品验收绿）
- **票面**: GitHub #109（侧轨 R1，Part of #96）
- **分支**: `research/r1-must-quarantine`
- **决议日期口径**: 一手来源以 2026-09-21 ADR-0014 / MemoryForensics 评估为准；本文件只汇总、不改 ADR / CONTEXT / gold
- **验收层声明**: 本文件属 RESEARCH。可引用「规则已预注册、金标仍空、UI/W9 默认不挂」；**不得**升格为「记忆卫生已通过 / 一期测量闭合 / 产品绿」

---

## 0. 决策可依赖的事实清单（摘要）

| # | 事实 | 一手来源 | 决策含义 |
|---|---|---|---|
| F1 | `must_quarantine` 构造规则的单一真相在评估文档 §7；ADR-0014 钉死「填金晚于规则落档」 | ADR-0014 决策 2；`MemoryForensics操作定义对齐与论文路径设计评估.md` §7 | 后续填 `gold.json` 不得按 demo 输出回填；改 §7 须声明评测作废 |
| F2 | 分桶规模来自立项切片 §11.3：8–12 条合成记忆；金标须含 2 dead + 1 对互斥两侧 + 2 unverified；其余可召回 | `FreshLatch-立项切片.md` §11.3；评估 §7.1 | 填金时 id 集合须满足该配比；`must_keep` 对照桶在评估加码、不进 CONTEXT |
| F3 | 今日 `data/eval/gold.json` 的 `must_quarantine` 仍为 `[]`；`test_gold_gate` 断言空数组 | `gold.json` L6；`tests/eval/test_gold_gate.py` L56 | **今日语料金标缺口**：结构在场、条目未填；记忆 runner 尚未存在 |
| F4 | Lead 默认白名单仍为 `LEAD_TOOLS_W3`；`LEAD_TOOLS_W9` / `_t_spawn_forensic` 代码在盘但对模型不可见 | `src/freshlatch/tools.py`；`lead.py`；ADR-0014 决策 3 | **默认 UI / W9 不挂**；不进 Batch 5 成交面；本票不 block ε |
| F5 | 记忆卫生 UI 侧栏在切片 §11.4 / 评估登记册为「中期·承载」，现状「未做」 | 切片 §11.4；评估 §5 #12、§9.2、登记册「记忆卫生 UI 侧栏」 | 填金与冒烟 runner **先于**产品 UI；UI 不得挡规则锁与另提交填数 |
| F6 | demo 脚本合成夹具按 §11.3 配比跑通，但是 **demo 层 n=1**，明确禁止写进 gold / 准确率 / 论文主表 | `scripts/w9_w12_memory_forensics_demo.py`；评估 §5.1 | 夹具可作另提交填金的**参考形状**，不可当金标本身 |
| F7 | CONTEXT 只定义产品语义；覆盖正则 / ATTRIBUTE / 通过线细节不进词表 | CONTEXT `must_quarantine`；评估 §8 #4 | 实现与评测加严归评估/ADR，不扩 CONTEXT |
| F8 | 三曲线设计把 R1 标为 RESEARCH 侧轨；「金标前 W9/真 Forensic」列为 REJECT/HOLD | `docs/plans/2026-09-22-freshlatch-three-curves-design.md` | 本票关闭 = 事实清单就位，不触发 implement |

---

## 1. 构造规则（摘录 + 缺口）

### 1.1 规则草案来源链（优先级）

1. **操作化锁死**：`docs/research/MemoryForensics操作定义对齐与论文路径设计评估.md` **§7**（预注册；改规则 = 评测作废）
2. **ADR 闸**：`docs/adr/0014-memory-forensics-eval-preregistration.md`（接受规则单一真相在 §7；本 ADR 接受日不得把 demo 写入 gold）
3. **产品规模原文**：`docs/product/FreshLatch-立项切片.md` **§11.3**（8–12 条与分桶数字的出处）
4. **词表边界**：根目录 `CONTEXT.md` → `must_quarantine`（只说「必须被提议移出下一轮记忆侧召回的 memory_id」；构造规则与通过线在评估文档）
5. **schema 占位**：`docs/spec/02-数据schema与语料清单.md` §2.4；`docs/research/语料金标设计评估.md`（空数组占位、结构先在场）

### 1.2 §7 已锁内容（决策可直接引用）

**规模与分桶（§7.1 / 切片 §11.3）**

- 合成记忆 **8–12** 条，写入记忆夹具（路径另提交指定；不进主张 `causal_chain`）。
- **`must_quarantine` 必须包含**：
  - 2 条 **dead** id
  - 互斥对中「不得同时召回」的 **两侧** id（= 1 对 contradictory，计 2 条）
  - 2 条 **unverified** id
- **`must_keep`（评估加的对照桶，不进 CONTEXT）**：至少 3 条仍受 T1 支持、有合法 `source_ref`、且不与 must_quarantine 条目共享「具体对象 ∩ 同一 ATTRIBUTE 词」——防全隔离假绿。
- 互斥对 **不得**用「T0 旧价 vs T1 新价」冒充；那种配对应落 **dead**（只隔离旧侧）。互斥对必须是 T1 **不能单独裁决** 的同维度相对表述。

**通过线（§7.2；记忆 runner 尚未存在）**

- 建议态即可计「离开下一轮召回」。
- must_quarantine 每条 id 必须被 flag，且 `propose_quarantine` 名单包含该 id。
- must_keep 不得出现在提议隔离名单。
- 每条 dead ≥1 个可点回的 `doc_id#anchor@T1`；evidence 须能在 T1 语料取回；空列表 = 本条失败。
- 每条 unverified 理由须指出「缺 source_ref」或「文档 id 不存在」。
- 人未确认前，磁盘 `status` 仍为 active。

**层声明与违例（§7.3–§7.4）**

- 第一版记忆 runner = **冒烟**（确定性闩 n=1；若 LLM Forensic 则另锁采样，不得把小 n 报方差）。
- 违例级：漏标 must_quarantine；误隔 must_keep；dead 无真实 T1 证据；未确认即 `status=quarantined`；评测路径联网；事后改 §7 还不声明作废。

**检测器操作定义（评估 §5 子决策；ADR-0014 决策 1）**

- 顺序：unverified → dead(T1) → 其余互斥。
- dead：与 `source_ref` 对应 T1 冲突（含「从 X 降至 Y」覆盖）；**无 T1 不得标 dead**；时效词单独标 dead **废弃**。
- 互斥：同属性词 +（数字冲突或反义）+ **具体对象门闩**；对象不相交 → 不互斥。
- unverified：无 `source_ref`，或 doc 在 T0/T1 皆不存在；不可核 ≠ 假。
- checksum-dead：**留位**（CONTEXT 已钉未启用）。

### 1.3 已知缺口（事实，非待办工单）

| 缺口 | 证据 | 说明 |
|---|---|---|
| `gold.json` 无具体 memory_id | `must_quarantine: []` | 规则已锁、数未填 |
| 记忆夹具路径未在 gold / 仓内主张夹具并列钉死 | 评估 §7.1「路径另提交指定」；§10.1 #2 | 填金提交须同时交付夹具 |
| 记忆冒烟 runner 不存在 | 评估 §7.2「尚未存在」；§10.1 #3 | 通过线无法自动跑 |
| `must_keep` 未进 gold schema | 仅评估文档；CONTEXT 明确不收 | 对照桶住评估/runner，不扩词表 |
| UI 侧栏未做 | 评估 §9.2；completion 勘误文 | 与填金解耦 |
| Lead 未挂 W9 | `LEAD_TOOLS_W3` 实装；ADR-0014 决策 3 | 主张 `must_stale` 矩阵与记忆评测隔离 |
| demo 夹具 id ≠ 金标 | demo 用 `mem_dead_price` 等合成 id | 另提交填金须用真实语料 doc_id 对齐的夹具；**禁止**把 demo 输出当 gold |

---

## 2. 填金时机（事实依据上的建议）

> 本节「建议」= 把已拍板纪律翻译成可执行顺序；**不新开决议**。

### 2.1 已拍板的先后纪律

| 顺序 | 内容 | 来源 |
|---|---|---|
| ① 已完成 | 锁构造规则（§7）+ 立 ADR-0014 | 评估拍板维度二 b；ADR-0014 |
| ② **下一次可填金提交** | 记忆夹具（8–12，真实 doc_id）+ 按 §7 写入 `must_quarantine` id + 对照桶 must_keep（评估侧）+ 改 `test_gold_gate` 空断言 | 评估 §10.1 #2；ADR-0014 后果条 |
| ③ 可并行/紧随 | 记忆冒烟 runner：确定性 `inspect`，断言 §7.2；**不并进** 12 条主张矩阵 | 评估 §10.1 #3；ADR-0014 决策 3 |
| ④ 更晚 | UI 侧栏；确认后同步 `quarantine_list`；记忆假绿对照 | 评估 §10.1 #4–6 |
| ⑤ 触发条件后 | W9 白名单挂载：仅记忆 runner / 手动演示；默认复验仍 W3 | 评估 §10.1 #7；登记册「触发」 |

**禁止的填金时机**（已被否）：

- 按本次 / 任意 demo 结果回填 gold → HARKing（评估 §4.2 a；ADR 替代方案第 1 条）。
- 规则未声明作废就改 §7 凑绿（§7 开篇；ADR-0014 决策 2）。

### 2.2 相对产品 UI 的纪律（票面「默认 UI 不挂」）

1. **填金与 UI 解耦**：切片把侧栏放在 §11.4，评估把 UI 标「中期·承载」；北极星是金标 memory_id 与冒烟通过线，不是侧栏像素。
2. **三曲线 R1 = RESEARCH**：不进 Batch 5 成交面；「金标前 W9/真 Forensic」为 REJECT/HOLD（`2026-09-22-freshlatch-three-curves-design.md`）。
3. **本票不 block ε**：ε 信任内嵌 / 对抗套件目录可与 R1 事实清单并行；无主链 blocker。
4. **人确认前不删盘**：CONTEXT 隔离定义 + 切片 §11.2 / §11.5；与「不接 Mem0」同属勿重开边界（#109 票面）。

---

## 3. 今日语料金标缺口（可核对）

```text
文件: data/eval/gold.json
字段: "must_quarantine": []
单测: tests/eval/test_gold_gate.py → assert GOLD["must_quarantine"] == []
词表: CONTEXT.md 已有 must_quarantine 产品定义（不含构造细则）
```

- **有**：字段结构、空数组占位、闸测锁空、词条、§7 规则、ADR-0014。
- **无**：任何 `memory_id` 条目；记忆夹具入库路径与 gold 的绑定；记忆 runner；与主张 `causal_chain` 同级的记忆因果登记（设计上也不进 causal_chain）。

因此：**今日缺口 =「规则已预注册、数与 runner 未交付」**，不是「规则未定义」。

---

## 4. 与 ADR-0014 / MemoryForensics 预登记的对齐核对

| ADR-0014 决策 | 本票事实核对 | 冲突？ |
|---|---|---|
| 1. 操作定义执行体优先；时效词 dead 废弃 | 评估 §5 #2–4；demo 已按 T1 对照改口 | 无冲突；本文件不改代码 |
| 2. 填金晚于 §7；接受日不得写 demo 进 gold | `gold.json` 仍 `[]` | 无冲突；符合预登记 |
| 3. 主张评测与记忆评测隔离；Lead 默认 W3 | `lead.py` 用 `LEAD_TOOLS_W3`；W9 tuple 在 `tools.py` 未挂 | 无冲突；支持「默认不挂」 |
| 4. 论文身份 = T1 锚定 fail-closed 闩，非词表算法 | 评估 §4.4 / §10 | 本票不谈发表 KPI |

**未发现需改 ADR / CONTEXT 的冲突。** 若未来填金时把 `must_keep` 塞进 CONTEXT，将违反 Anthropic 清单 4 / 评估 §8 #4——应留在评估与 runner。

---

## 5. 可引用句边界（RESEARCH ≠ 产品绿）

**本文件允许引用的句子（示例）：**

- 「`must_quarantine` 构造规则已在 MemoryForensics 评估 §7 预注册，并由 ADR-0014 锁死填金先后。」
- 「截至本调研，`gold.json` 的 `must_quarantine` 仍为空数组；单测锁空；记忆冒烟 runner 未实装。」
- 「Lead 默认不挂 W9；记忆卫生 UI 侧栏未做；R1 为 RESEARCH 侧轨，不 block ε。」

**禁止升格句：**

- 「W12 / 记忆卫生已通过验收」
- 「must_quarantine 评测已绿 / 有准确率」
- 「侧栏已有 / 与 Lead 无缝集成」（见 `docs/task-completion/w9-w12-memory-forensics-completion.md` 与 `W12_FINAL_COMPLIANCE_CERTIFICATION.md` 改口边界）
- 把 `scripts/w9_w12_memory_forensics_demo.py` 的一次运行写成金标或论文结果

**层标签**：本文件 = **RESEARCH**。下一步若开 implement 票填金，须另标 **smoke/invariant**，且失败只改实现不改 §7。

---

## 6. 一手来源索引

| 路径 | 用途 |
|---|---|
| `docs/adr/0014-memory-forensics-eval-preregistration.md` | 预注册 ADR |
| `docs/research/MemoryForensics操作定义对齐与论文路径设计评估.md` §5–§10 | 构造规则单一真相、填金顺序、UI/W9 处置 |
| `docs/product/FreshLatch-立项切片.md` §11.1–§11.5 | 三类发现、规模、UI、验收原文 |
| `docs/adr/0013-memoryforensics模块设计与实现.md` | 角色/工具/隔离；指向 ADR-0014 |
| `CONTEXT.md`（must_quarantine） | 产品金标词义边界 |
| `data/eval/gold.json` | 今日空数组事实 |
| `tests/eval/test_gold_gate.py` | 空数组断言 |
| `src/freshlatch/tools.py`（LEAD_TOOLS_W3/W9） | 默认不挂证据 |
| `src/freshlatch/roles/lead.py` | spawn_forensic 预留 |
| `scripts/w9_w12_memory_forensics_demo.py` | demo 层夹具形状（非金标） |
| `docs/plans/2026-09-22-freshlatch-three-curves-design.md` | R1 侧轨与 Batch 边界 |
| `docs/spec/02-数据schema与语料清单.md` §2.4 | 空数组占位规格 |

---

## 7. 对本票验收的勾选

- [x] 构造规则：从 ADR/评估/切片摘录 + 缺口表
- [x] 填金时机：先规则、另提交填数、runner、再 UI/W9
- [x] 默认 UI 不挂 / 不 block ε
- [x] 今日金标无 must_quarantine 条目 + 缺口说明
- [x] 可引用边界：RESEARCH ≠ 产品绿
- [x] 不改 CONTEXT / ADR / 产品代码（本提交仅本文件）
