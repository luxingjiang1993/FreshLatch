# β+ 档 3b：演示录屏口播 + 面试讲法取材

> **Status as of 2026-09-23**（PR #145 合入 `main`）  
> **验收层**：demo / 口播 = 确定性 invariant 演示，**不是**统计结论，**不是**「checksum 已证明 latch」。  
> **正本**：预锁句与禁升格以 [`ACCEPTANCE.md`](./ACCEPTANCE.md) 为准；面试问答以评估文档 §6 为准。本文只做**取材汇编与录屏步骤**，不另造更强主张。

## 0. 录屏前必读（禁升格）

口播与字幕**禁止**出现以下升格（ACCEPTANCE §3 逐字纪律）：

- 本批 ACCEPTANCE **不得**升格为：checksum 已证明 latch；跨轮重检上线 = 统计结论；demo 掉灯 = 产品验证成功；Override Rate / 对抗通过率。
- `checksum_fn` 必须语料现算；禁读与 basis 同源库列。
- 人审动词仍仅 discard|renew；机械行 `basis_rot` 的 override 不得为 true。
- 不改 gold；不自动 void；无 basis 的 Agent fresh 不检（半激活诚实；不偷开档 3a）。

可说的唯一产品层结论（与预锁句同义复述，勿加码）：

> 只证明：带 `validity_basis` 的 `fresh` 绿灯，在对应语料被篡改后，会经同一 `check_basis`/`apply_rot` 机械掉成 `unknown`，并写 `latch_log action=basis_rot`；复验入口本轮不进 Lead。

## 1. 预锁 invariant（口播可逐字念；改字 = 本批验收作废）

出处：`ACCEPTANCE.md` §1（与评估 §4 预锁整句一致）。

> 档 3b：对 `status==fresh` 且 `validity_basis` 非空的主张，复验入口与 UI 拉单/渲染均须经同一 `check_basis`（语料现算 sha256，禁读库列）；不符则 `apply_rot` → `unknown` + 机械码（如 `BASIS_CHECKSUM_MISMATCH`），写 `latch_log`，保留 basis 与 `last_confirmed_at`，且复验入口不进 Lead。无 basis 的 fresh 不检。本句不得升格为统计结论或「checksum 已证明 latch」。

## 2. 演示录屏脚本（约 2–3 分钟；PR #145 人工项）

目标画面（双触发各至少一镜）：

| 镜号 | 路径 | 画面必须出现 |
|---|---|---|
| A | 复验入口 | 续命后 `fresh` → 篡改语料 → 点复验 → `unknown` + 理由含 `BASIS_CHECKSUM_MISMATCH`；本轮不进 Lead |
| B | UI 拉单 | 同一腐烂主张：刷新/打开复验单（`GET /api/claims`）后仍为 `unknown`；库内有 `basis_rot` 行 |
| C（可选对照） | 无 basis | 无 `validity_basis` 的 Agent `fresh`：点复验/拉单**不**因 3b 掉灯（半激活诚实） |

### 2.1 准备

1. 工作区切到含 #145 的 `main`（或等价 commit `977ba3b`）。  
2. 启动复验单 UI（本仓惯例启动 `freshlatch.ui.app`；语料根默认 `data/corpus`，active pack 时跟 pack）。  
3. 选一条已人审 **renew**、且 `validity_basis` 非空的 `fresh` 主张（Batch 2 半激活写侧）。记下 `doc_id` 与语料文件路径：`{{CORPUS}}/t1/{{doc_id}}.md`。

### 2.2 镜 A — 复验入口

口播（可念）：

> 这是档 3b：只检「已写 basis」的 fresh。我先确认它是绿灯，然后在盘上改语料——checksum 现算，不读库列。点复验时，闸在进 Lead 之前机械掉 unknown。

操作：

1. UI 上确认该主张 `status=fresh`，理由为人审续命类。  
2. 用编辑器在对应 `t1/{{doc_id}}.md` 追加一行无关文本并保存（模拟跨轮腐烂）。  
3. 对该主张点**复验**。  
4. 停镜核对：`unknown`；理由含 `BASIS_CHECKSUM_MISMATCH`；`validity_basis` 与 `last_confirmed_at` **仍在**；本轮轨迹未进 Lead。  
5. （可选）查 latch：`action=basis_rot`，`override` 不为 true。

### 2.3 镜 B — UI 拉单（真写库，非只改展示）

口播：

> 双触发的另一半：打开或刷新复验单走同一套 `check_basis`/`apply_rot`。掉灯必须落在持久化观察点，不能只改响应体。

操作：

1. 保持语料仍为篡改态（或另起一条同样续命+篡改）。  
2. 刷新复验单 / 重新打开列表（触发 `GET /api/claims`）。  
3. 停镜：列表中该主张为 `unknown`；再次刷新仍为 `unknown`（幂等，不抖动）。  
4. 口头点明：这与镜 A **共用** `src/freshlatch/gates/basis_rot.py`，不是第二套逻辑。

### 2.4 镜 C — 负对照（推荐 15 秒）

口播：

> 没有 basis 的 Agent fresh 不检——半激活边界；等档 3a 写侧，不能把意图当成今天的牙。

操作：找一条无 `validity_basis` 的 `fresh`，点复验或拉单，确认**不**因 3b 降为 `unknown`。

### 2.5 录屏留档纪律

- mp4 **不进 git**（与 W4 留档惯例一致）；本目录可另记本地路径。  
- 本文件与 `ACCEPTANCE.md` 进 git；勾选负例已在 ACCEPTANCE §2 由单测勾 `[x]`，人录屏是**演示层**复核，不改写预锁句。

## 3. 面试讲法（逐字取材于评估 §6）

### 3.1 档 3b（主弹药）

出处：`docs/research/β+-档3b-跨轮腐烂重检设计评估.md` §6。

> **Q:为什么不先做 3a 再做 3b？**
> A:3b 读的是**已写** basis。今日 renew 已写；跨轮腐烂正是产品承诺所在。等 3a 等于让有牙的半边继续空转。

> **Q:为什么掉 unknown 不掉 stale？**
> A:stale 要求可点回的 T1 反证叙事。checksum 腐烂是机械事实，硬塞 evidence 是假反证。unknown + 机械码更诚实。

> **Q:为什么 UI 也要写库？**
> A:选了双触发。只提示不写 = 打开复验单仍显示 fresh，牙齿在展示层假活。

> **Q:这证明 latch 了吗？**
> A:没有。预锁句禁止升格。只证明「带 basis 的绿灯在语料变了之后会机械掉 unknown」。

> ---

### 3.2 档 3a 方向锁（追问「为什么 fresh 还没牙」时用）

出处：`docs/research/β+-档3a-fresh-validity_basis设计评估.md` §6。本批**不实装** 3a；只锁 list 方向（ADR-0024）。

> **Q:档 2 都做了，为什么 fresh 还不补 validity_basis？**
> A:补的时候必须先答单 doc 还是 list。单 doc 在多 evidence 下是假牙——只校主证却像全链有 checksum。我们宁可半边诚实空转，也不把假牙写成「已激活」。方向上锁的是 list，本批不实装。

> **Q:那你们是不是永远不做 3a？**
> A:不是。本票锁的是「若做则 list 同构 + 全员受检 + renew 一元 list + 存量迁一元 list」。实装必须另开票并预登记负例，不能从本票关单自动派生。

> **Q:为什么不直接实装 list？**
> A:动 schema、闸循环、投影/导出、存量迁移——这是实现批，不是方向批。方向先锁死，避免实装单里再吵单 doc「先顶上」。

> **Q:3b 能不能开？**
> A:能。但必须写清：今天写侧只有 renew 的单对象 basis；将来若做 3a，意图是 list。不能把意图当成当前事实，也不能假装没有意图。

> **Q:这算不算 checksum 已证明 latch？**
> A:不算。本票连 fresh 半边都没启用。预锁句在 ADR-0017；本票只加方向，不改激活宣称。

> ---

## 4. 30 秒电梯稿（合成；主张强度不超过 §1 预锁句）

> Batch 2 之后 renew 会写 `validity_basis`。档 3b 把跨轮腐烂做成产品行为：复验入口和 UI 拉单共用 `check_basis`/`apply_rot`，语料现算 sha256，不符就掉 `unknown` 并记 `basis_rot`。我们故意不掉 `stale`——那是机械事实不是可点回反证。Agent fresh 半边仍无 basis，方向已锁成 list，实装另开票。这不证明 latch 统计成立，只证明带 basis 的绿灯在语料变了之后会机械掉灯。

## 5. 机器复核（录屏前后可跑）

```text
pytest tests/unit/test_basis_rot.py tests/unit/test_ui_basis_rot.py tests/unit/test_beta_plus_3b_acceptance.py -q
```

挂载关系见 `ACCEPTANCE.md` §4。

## 6. 链接索引

| 角色 | 路径 / 票 |
|---|---|
| 预锁 + 禁升格正本 | `docs/evidence/beta-plus-3b/ACCEPTANCE.md` |
| 3b 评估 §6 | `docs/research/β+-档3b-跨轮腐烂重检设计评估.md` |
| 3a 评估 §6 | `docs/research/β+-档3a-fresh-validity_basis设计评估.md` |
| ADR | ADR-0025（3b）、ADR-0024（3a 方向） |
| 实装 | #143 复验入口、#144 拉单 + ACCEPTANCE、PR #145 |
