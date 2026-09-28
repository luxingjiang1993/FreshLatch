# Phase V1 DoD close · smoke-level

> **档：** 冒烟 / 零 LLM CI。不报方差，不作统计升格，不是 Hard-Gold。  
> **日期：** 2026-09-29  
> **Refs：** [#175](https://github.com/luxingjiang1993/FreshLatch/issues/175)（人终收，本文件不代关） / parent [#168](https://github.com/luxingjiang1993/FreshLatch/issues/168) / blocked-by [#174](https://github.com/luxingjiang1993/FreshLatch/issues/174) closed via [PR #181](https://github.com/luxingjiang1993/FreshLatch/pull/181)  
> **规格 / 决议：** `docs/spec/11-PhaseV1-PrePublish.md` · ADR-0027 · 评估 `docs/research/V1-发前闭环垂直与包结论设计评估.md`

本页是 V1 Exit 的可引用关门摘要。人终收仍在 #175；Cloud 只交包，不 close issue。

## Demo path

顾问样例包 `v1-mck-soai`（`data/packs/v1-mck-soai/`）装入主张集，经夹具薄 URL（白名单主机 `www.mckinsey.com`，CI 不打真网）落成合法 T1 并带 checksum；零 LLM 按预登记主张态走规则闸，聚合出报告级 disposition（未收口 stale → **勿发**）；HumanLatch 对人审 discard 收口后包结论变为 **可发**，发前列表与 Run 详情投影一致，详情可追到同一条 T1 checksum，并经 `record_human_review_events` 追加至少一行 `patch_events`（`before_disp=勿发`）。见 `docs/evidence/v1/prepublish-e2e.md` 与 `tests/unit/test_prepublish_e2e.py`。

## DoD 五项

- [x] **未归档不得定论**（无 T1 / `ready=false` → 不得开复验定论，规则闸不得绿灯）  
  `POST /api/reverify` 在 T1 未 ready 时 400（`src/freshlatch/ui/app.py`）；`tests/unit/test_ui_t1_source.py::test_reverify_blocked_without_t1_source`。无 `t1_evidence_ids` 不得 fresh：`tests/unit/test_rule_gate.py`。
- [x] **报告级 disposition 可追责**（可发 / 需补丁 / 勿发；`PREREG_MAPPING`；ADR-0027）  
  纯函数 `aggregate_disposition`（#170 / [PR #176](https://github.com/luxingjiang1993/FreshLatch/pull/176)）。预登记抽检：mck-1 stale · mck-2 fresh · mck-3 unknown · mck-4 stale → **勿发**；收口后 → **可发**。`tests/unit/test_prepublish_e2e.py`。
- [x] **人审路径走通**（HumanLatch discard → 可发；list/detail 同步）  
  主缝 `test_main_seam_sample_pack_thin_url_to_patch_events`：discard `mck-1` / `mck-3` / `mck-4` 后列表与详情同为 **可发**，Run 状态 **已落档**（#173 / #174，[PR #180](https://github.com/luxingjiang1993/FreshLatch/pull/180)、[PR #181](https://github.com/luxingjiang1993/FreshLatch/pull/181)）。
- [x] **单一垂直已写进文档 / README**（顾问报告）  
  README「单一垂直 = 顾问报告」；`docs/roadmap.md` Phase V1 In；样例包 #169 / [PR #178](https://github.com/luxingjiang1993/FreshLatch/pull/178)。thesis-1 与 QuoteTTL 可软 Port，`v1-mck-soai ∉ KNOWN_PACK_IDS`，不算第二垂直。
- [x] **`patch_events` schema 已落并开始记账**  
  `data/patch_events/`（#172 / [PR #177](https://github.com/luxingjiang1993/FreshLatch/pull/177)）。人审成功行经 `record_human_review_events` 追加；发前 UX 不提供 C/T 切换（`arm` 后台固定，现主链写入 `"C"`）。

## 证据引用

| 项 | 指针 |
|----|------|
| 冒烟摘要 | `docs/evidence/v1/prepublish-e2e.md` |
| 主缝测试 | `tests/unit/test_prepublish_e2e.py` |
| 实现 PR | [#176](https://github.com/luxingjiang1993/FreshLatch/pull/176) disposition · [#177](https://github.com/luxingjiang1993/FreshLatch/pull/177) patch_events · [#178](https://github.com/luxingjiang1993/FreshLatch/pull/178) 样例包 · [#179](https://github.com/luxingjiang1993/FreshLatch/pull/179) 薄 URL · [#180](https://github.com/luxingjiang1993/FreshLatch/pull/180) 两屏 · [#181](https://github.com/luxingjiang1993/FreshLatch/pull/181) 主缝 |
| 已关子票 | [#169](https://github.com/luxingjiang1993/FreshLatch/issues/169)–[#174](https://github.com/luxingjiang1993/FreshLatch/issues/174) closed |
| 仍开 | [#175](https://github.com/luxingjiang1993/FreshLatch/issues/175) 人终收 · [#168](https://github.com/luxingjiang1993/FreshLatch/issues/168) 父规格 |

## `patch_events` 样例行

仓内样例行：`data/patch_events/schema.example.jsonl`（`before_disp=需补丁`，`actor=script`，`arm=T`）。  
贯通测试不把该文件当运行账：e2e 在临时目录经 `record_human_review_events` 写入，断言字段齐全且 `before_disp=勿发`、`human_confirm=true`、`actor=human`。

## Out of Scope（确认未进主链）

- [x] 多垂直并行 / 研报合规主包（样例包不进 `KNOWN_PACK_IDS`）
- [x] 薄对话 / Evidence-bound UX（留 V1.5；ADR-0027 不授权）
- [x] C/T 进发前 UX（主链 `arm="C"` 写死；`tests/unit/test_patch_events.py` 禁 UX 开关）
- [x] Hard-Gold / 改生产默认 retrieval 臂（`PRODUCTION_RETRIEVAL_MODE == "bm25"`）
- [x] 开放爬虫 / 多域名白名单（仅 `www.mckinsey.com`；失败四态零写，#171 / [PR #179](https://github.com/luxingjiang1993/FreshLatch/pull/179)）
- [x] Studio / Memory 大叙事（路线图冻结 / 非主链）

## 不宣称检索臂评测升格

生产默认检索臂仍是 `bm25`。本证据层只是冒烟 / 零 LLM CI。不把 Phase A 对照表、dense/hybrid/rerank 评测臂，或本次发前夹具，说成 Hard-Gold 通过，也不授权改默认臂。

## 本机关单命令

环境：Linux，Python 3.12.3，pytest 9.1.1。`python -m compileall` 与 `rg` 按关单命令原样。pytest 两条都跑了：仓库 Quick start 是 `python -m pytest`（15 passed，exit 0），本关门包以这一条为绿；裸 `pytest` console script 在本 VM 上 exit 1，失败点是既有 `from tests.unit.test_meta_gate import ...`（console script 不把仓库根放进 `sys.path`），不是发前主缝断言失败。不把 exit 1 改写成绿。

```text
$ python -m compileall -q src
exit:0

$ pytest tests/unit/test_prepublish_e2e.py tests/unit/test_rule_gate.py -q
...........FF..                                                          [100%]
=================================== FAILURES ===================================
____________________ test_stale_meta_only_disproof_blocked _____________________

    def test_stale_meta_only_disproof_blocked():
        """不变量 6(#17):stale 反证不得为纯元陈述——打回 META_ONLY_DISPROOF,经 runner 落 unknown。"""
>       from tests.unit.test_meta_gate import C9_RUN2_REASON
E       ModuleNotFoundError: No module named 'tests'

tests/unit/test_rule_gate.py:79: ModuleNotFoundError
________________________ test_stale_legit_reason_passes ________________________

    def test_stale_legit_reason_passes():
        """不变量 6 正例:含数值锚的实质反证照常放行(不误伤合法 stale)。"""
>       from tests.unit.test_meta_gate import C7_LEGIT
E       ModuleNotFoundError: No module named 'tests'

tests/unit/test_rule_gate.py:88: ModuleNotFoundError
=========================== short test summary info ============================
FAILED tests/unit/test_rule_gate.py::test_stale_meta_only_disproof_blocked - ...
FAILED tests/unit/test_rule_gate.py::test_stale_legit_reason_passes - ModuleN...
2 failed, 13 passed in 1.18s
exit:1

$ python -m pytest tests/unit/test_prepublish_e2e.py tests/unit/test_rule_gate.py -q
...............                                                          [100%]
15 passed in 1.09s
exit:0

$ rg -n "顾问报告|patch_events|可发|需补丁|勿发" README.md docs/roadmap.md
docs/roadmap.md:71:| **In** | **单一垂直=顾问报告**（McK SoAI 03→11 样例包）；T1 落盘（checksum）；三卡+薄 URL（`www.mckinsey.com`）；Gate；包结论新层（**可发 / 需补丁 / 勿发**）；作废/续命；两屏（列表新建+复验单详情）；**`patch_events` JSONL 起记**（后台 C/T） |
docs/roadmap.md:80:- [x] `patch_events` schema 已落并开始记账  
docs/roadmap.md:229:- **自 V1 起**记账 `patch_events`（人手补丁也算）：`claim_id` / `before_disp` / `patch_span` / `t1_ids` / `human_confirm` / `reverify` / `minutes` / `arm=C|T`。
docs/roadmap.md:238:| W1–2 | I0 + `patch_events` schema |
docs/roadmap.md:297:| 2026-09-29 | **V1 grill DONE**：顾问报告+McK SoAI；包结论新层；薄 URL=`www.mckinsey.com`；评估见 `docs/research/V1-发前闭环垂直与包结论设计评估.md`；ADR-0027；下一跳 to-spec |
README.md:31:**单一垂直 = 顾问报告**（V1 / ADR-0027）。近端只做已签发顾问/战略主张的发前复验；样例主包为 McKinsey State of AI 公开洞察摘录（T0≈2025-03 → T1≈2025-11），见 `data/packs/v1-mck-soai/`。thesis-1 与 QuoteTTL 可留回归，**不算**第二垂直。仓内不提交整本咨报 PDF。
exit:0
```
