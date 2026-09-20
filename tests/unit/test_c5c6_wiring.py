"""#21 实装结构断言(TDD 红灯先行):SKILL.md 接线(Runner 注入,补 T6 实装债)+ 人格最小 diff
+ mark_stale 维度核对指令确定性注入 + must_fresh 干扰项语料/敏感度附表/维度疑似混淆标注。

拍板依据:#19(grilling,已关)与 docs/research/c5c6工程债处置设计评估.md §4:
- 接线层为主(事实 1:教义表在盘不在场;事实 2:事故路径 Lead 自主 mark_stale 三重裸奔);
- 人格层最小 diff 一句指向已接线教义表(不复制铁律全文,防双拷贝漂移);
- mark_stale 观察确定性携带维度核对指令(指令在场 ≠ 机器判维度,闸③不重开);
- 乙-i:2 条 must_fresh 干扰项(客单价≠毛利、覆盖率≠渗透率),带完整 causal_chain 金标,
  不进 12 条判分矩阵,单列「干扰项敏感度」附表;各带假绿对照记录(control 基线应判 alive);
- 乙-ii:报告对「must_fresh 判 stale 且 anchor_aligned=False」自动标注「维度疑似混淆」
  (评测加严判据,归 #19 评估文档,不进 CONTEXT.md)。

结构断言 ≠ 模型行为证明(层间归因诚实框定,#19 §4.6):行为验收 n=3 temp=0 qwen-flash
由判定人本人触发(#21 验收段,额度纪律),bundle 绿不声称逐层行为生效。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.eval.report import render_report
from freshlatch.eval.runner import (
    dimension_confusion_flags,
    distractor_sensitivity,
    run_gold,
)
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LEAD_PERSONA, LeadReverifier
from freshlatch.runner import RunContext, Runner
from freshlatch.skills_loader import load_skill_body
from freshlatch.store.base import InMemoryStore
from freshlatch.store.ingest import ingest_into, load_corpus

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD = json.loads((REPO_ROOT / "data" / "eval" / "gold.json").read_text(encoding="utf-8"))
DISTRACTOR_DOCKET = json.loads(
    (REPO_ROOT / "data" / "eval" / "distractor_docket.json").read_text(encoding="utf-8"))
CORPUS = REPO_ROOT / "data" / "corpus"

DOCTRINE_MARKER = "约束与纠正"  # reverify/devil_advocate SKILL.md 共有的教义表节标记


# -- 本地最小假件(与 test_c5_dimension_anchor 同款结构,不跨测试文件 import) --------


_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_w_{_tc_counter}", type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
    )


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        d = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in self.tool_calls
            ]
        return d


class _ScriptLLM:
    """FIFO 脚本回吐;Lead/Critic/Auditor 共享同一脚本按调用顺序消费。"""

    def __init__(self, script):
        self._script = list(script)

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


class _FinishLLM:
    """任何会话首轮直接 finish_reverify 收尾(结构测试用,零语义)。"""

    def __init__(self):
        self._n = 0

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self._n += 1
        if self._n % 2 == 1:
            return _Msg(tool_calls=[_tc("finish_reverify", {})])
        return _Msg(content="复验结束")


def _chunk(doc_id: str, text: str):
    from freshlatch.store.base import Chunk
    return Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-p2", clause_id="p2", title="t",
                 text=text, source_type="internal", as_of="T1", doc_version="v2",
                 checksum="", tokens=20)


def _store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t0-cost-model", as_of="T1", source_type="internal",
                        title="成本模型", doc_version="v2", checksum="", full_text="x"),
        [_chunk("t0-cost-model", "T1 复测:我方单会话成本 0.009 美元,竞品折算约 0.019 美元。"),
         # 另两篇兜底:BM25 在 N≤2 池里对唯一命中文档给出负 IDF,score>0 过滤会吞掉命中
         # (rank_bm25 默认实现,IDF 符号翻转需 N>2n;c5 测试同款三篇结构)
         _chunk("t0-side", "市场杂项:渠道集中度上升,与本主张无关。"),
         _chunk("t0-notes", "行业杂项:客服 SaaS 融资事件汇总,与本主张无关。")],
    )
    return store


def _ctx(store=None) -> RunContext:
    return RunContext(store=store or InMemoryStore(), guardrails=Guardrails())


def _claim() -> Claim:
    return Claim(claim_id="c5", statement="我方单会话服务成本仍低于竞品",
                 t0_evidence_ids=["t0-cost-model#p2"])


# -- 1. 接线层:SKILL.md 从盘到场(补 T6 实装债) ---------------------------------


def test_loader_returns_body_without_frontmatter():
    body = load_skill_body("reverify")
    assert body and not body.lstrip().startswith("---")
    assert DOCTRINE_MARKER in body


def test_loader_missing_slug_returns_none():
    assert load_skill_body("no_such_skill") is None


def test_runner_wires_reverify_doctrine_into_lead():
    """Runner 加载 reverify 教义表并注入 Lead 系统提示(运行时在场,替换内联人格为主)。"""
    runner = Runner(InMemoryStore())
    assert runner._doctrine["reverify"] and DOCTRINE_MARKER in runner._doctrine["reverify"]
    lead = runner._spawn_lead(_claim())
    system = lead._build_system()
    assert DOCTRINE_MARKER in system, "教义表必须在运行时系统提示在场(#19 事实 1)"
    assert "作废名单" in system, "名单注入行不因接线而丢"
    assert system.startswith(  # 教义表为主,内联人格不再整份在场(防双拷贝漂移)
        runner._doctrine["reverify"][:40])


def test_runner_wires_devil_advocate_doctrine_for_critic():
    """Critic 侧同链接线核查(#19 子决策 1:一并核查,防同类缺口漏网)。"""
    runner = Runner(InMemoryStore())
    assert runner._doctrine["devil_advocate"] and DOCTRINE_MARKER in runner._doctrine["devil_advocate"]
    lead = runner._spawn_lead(_claim())
    assert lead._critic_doctrine and DOCTRINE_MARKER in lead._critic_doctrine


def test_lead_falls_back_to_inline_persona_when_doctrine_missing():
    """教义表加载失败 → 回退内联人格并落事件(不静默吞:在盘不在场是 c5/c6 事故根因)。"""
    ctx = _ctx()
    lead = LeadReverifier(ctx, _claim(), _ScriptLLM([]), doctrine=None)
    system = lead._build_system()
    assert system.startswith("你是 Lead Reverifier")
    assert any(e.get("type") == "skill_fallback" for e in ctx.events), \
        "回退必须落事件,静默降级 = 事故形态复发"


def test_critic_falls_back_to_inline_persona_when_doctrine_missing():
    ctx = _ctx()
    critic = Critic(ctx, _claim(), _ScriptLLM([]), doctrine=None)
    assert critic._build_system().startswith("你是 Critic")
    assert any(e.get("type") == "skill_fallback" for e in ctx.events)


def test_critic_doctrine_present_in_system_when_wired():
    critic = Critic(_ctx(), _claim(), _ScriptLLM([]),
                    doctrine=load_skill_body("devil_advocate"))
    assert DOCTRINE_MARKER in critic._build_system()


# -- 2. 人格层:最小 diff 一句指向(不复制铁律全文) --------------------------------


def test_persona_points_to_wired_doctrine_exactly_once():
    """内联 LEAD_PERSONA 只加一句指向已接线教义表(#19 子决策 2,防双拷贝漂移)。"""
    assert LEAD_PERSONA.count("skills/reverify/SKILL.md") == 1


# -- 3. 注入层:mark_stale 观察确定性携带维度核对指令 --------------------------------


def test_mark_stale_observation_carries_dimension_note():
    """事故路径(Lead 自主 mark_stale)受理回执必须带维度核对指令(结构在场,不依赖模型自觉)。

    #22/ADR-0010 后:回执同时携带 Auditor checkpoint(受理自动触发);MARK_STALE_DIMENSION_NOTE
    保留为教义表兜底(ADR-0010 子决策 4),断言不动。
    """
    ctx = _ctx(_store())
    llm = _ScriptLLM([
        _Msg(content=json.dumps({"status": "stale", "reason": "反证成立",
                                 "dimension_match": True}, ensure_ascii=False)),
    ])
    lead = LeadReverifier(ctx, _claim(), llm)
    lead._t_retrieve({"query": "单会话成本 复测", "as_of": "T1"})
    cost_id = "t0-cost-model#p2@T1"
    res = lead._t_mark_stale({
        "claim_id": "c5",
        "reason": "T1 成本模型原文显示我方单会话成本 0.009 美元低于竞品折算 0.019 美元,"
                  "推翻成本优势消失的前提",
        "evidence_ids": [cost_id],
    })
    assert res.get("recorded"), "受理回执结构不变"
    assert res.get("auditor_checkpoint", {}).get("verdict") == "stale", \
        "mark_stale 受理自动触发 Auditor(#22/ADR-0010)"
    note = res.get("note", "")
    assert "维度" in note, "受理回执必须携带维度核对指令"
    assert "客单价≠毛利" in note and "覆盖率≠渗透率" in note, \
        "指令必须枚举本期两类未见混淆类型(乙-i 同款词表)"


# -- 4. 乙-i:干扰项语料完整性(金标/docket/语料三方对齐) ---------------------------


def test_distractor_bucket_registered_and_partition_intact():
    """gold 新增 must_fresh_distractor 桶:c13/c14;12 条主矩阵分桶一字未动(判分口径不动)。"""
    assert GOLD["must_fresh_distractor"] == ["c13", "c14"]
    main = (GOLD["must_stale"] + GOLD["must_fresh"] + GOLD["must_unknown"])
    assert sorted(main, key=lambda c: int(c[1:])) == [f"c{i}" for i in range(1, 13)]
    for cid in ("c13", "c14"):
        entry = GOLD["causal_chain"][cid]
        for key in ("t1_doc", "anchor", "change", "why_fresh"):
            assert entry.get(key), f"{cid} 缺 causal_chain.{key}"
        assert "≠" in entry["why_fresh"], f"{cid} 的 why_fresh 必须写明维度混淆免疫理由"


def test_distractor_docket_matches_gold():
    ids = [c["claim_id"] for c in DISTRACTOR_DOCKET["claims"]]
    assert sorted(ids) == ["c13", "c14"]
    for c in DISTRACTOR_DOCKET["claims"]:
        assert c["statement"] and c["t0_evidence_ids"]


def test_distractor_corpus_anchors_resolve():
    """T1 金标锚 + T0 签发证据都必须在双镜像语料里可点回(ingestion 确定性复用)。"""
    chunks = {(c.doc_id, c.clause_id, c.as_of)
              for _, chs in load_corpus(CORPUS) for c in chs}
    for cid in GOLD["must_fresh_distractor"]:
        entry = GOLD["causal_chain"][cid]
        assert (entry["t1_doc"], entry["anchor"], "T1") in chunks, f"{cid} T1 锚不可点回"
    for c in DISTRACTOR_DOCKET["claims"]:
        for eid in c["t0_evidence_ids"]:
            doc_id, _, anchor = eid.partition("#")
            assert (doc_id, anchor, "T0") in chunks, f"{c['claim_id']} T0 证据不可点回"


def test_distractor_statements_have_no_control_leak_token():
    """对照红线延伸:干扰项主张 + T0 摘录不得含泄题词(与 test_control.py 同款词表)。"""
    leaks = ("T1", "快照", "金标", "gold", "must_stale", "复验")
    corpus_t0 = {p.stem: p.read_text(encoding="utf-8") for p in (CORPUS / "t0").glob("*.md")}
    for c in DISTRACTOR_DOCKET["claims"]:
        for tok in leaks:
            assert tok not in c["statement"], f"{c['claim_id']} 主张泄题: {tok}"
        doc_id = c["t0_evidence_ids"][0].split("#", 1)[0]
        for tok in leaks:
            assert tok not in corpus_t0[doc_id], f"{doc_id} T0 语料泄题: {tok}"


# -- 5. 乙-ii/附表:纯函数与报告标注 ----------------------------------------------


def _details(statuses: dict[str, list[str]]) -> list[dict]:
    """构造 per_run 序列:{cid: [status per run]} → [run -> {"decisions","detail"}]。"""
    runs = max(len(v) for v in statuses.values())
    out = []
    for i in range(runs):
        out.append({
            "decisions": {cid: ss[i] for cid, ss in statuses.items()},
            "detail": {cid: {"status": ss[i], "reason": "r", "evidence_ids": [],
                             "trajectory": "t.jsonl", "steps_used": 1}
                       for cid, ss in statuses.items()},
        })
    return out


def test_dimension_confusion_flags_pure():
    """乙-ii 判定:must_fresh 判 stale 且未落在金标锚 → 标注;fresh/stale 但锚对齐 → 不标注。"""
    gold = {"must_fresh": ["c4", "c5"],
            "causal_chain": {"c4": {"t1_doc": "t0-market-census", "anchor": "p2"},
                             "c5": {"t1_doc": "t0-cost-model", "anchor": "p2"}}}
    anchor4 = "t0-market-census#p2@T1"
    anchor5 = "t0-cost-model#p2@T1"
    per_run = _details({"c4": ["stale", "fresh"], "c5": ["stale", "stale"]})
    per_run[0]["detail"]["c4"]["evidence_ids"] = ["t0-other#p1@T1"]  # stale 且锚未对齐 → 标注
    per_run[0]["detail"]["c5"]["evidence_ids"] = [anchor5]           # stale 但锚对齐(真死?)→ 不标注
    per_run[1]["detail"]["c5"]["evidence_ids"] = [anchor5]
    flags = dimension_confusion_flags(gold, per_run)
    assert flags == {"c4": [True, False], "c5": [False, False]}


def test_distractor_sensitivity_pure():
    gold = {"must_fresh_distractor": ["c13"],
            "causal_chain": {"c13": {"t1_doc": "t0-competitor-economics", "anchor": "p2"}}}
    per_run = _details({"c13": ["fresh", "stale"]})
    per_run[0]["detail"]["c13"]["evidence_ids"] = ["t0-competitor-economics#p2@T1"]
    sens = distractor_sensitivity(gold, per_run)
    assert sens["c13"]["statuses"] == ["fresh", "stale"]
    assert sens["c13"]["fresh_hits"] == 1
    assert sens["c13"]["anchor_hits"] == 1
    assert sens["c13"]["expected_anchor"] == "t0-competitor-economics#p2@T1"


def _raw_gold_run(flags: dict[str, list[bool]], sensitivity: dict) -> dict:
    """最小 gold_run raw:矩阵全命中,其余判据表就位。"""
    buckets = {"must_stale": ["c1"], "must_fresh": ["c4"], "must_unknown": ["c9"]}
    decisions = {"c1": "stale", "c4": "fresh", "c9": "unknown"}
    matrix = {
        "counts": {"must_stale": {"fresh": [], "stale": ["c1"], "unknown": []},
                   "must_fresh": {"fresh": ["c4"], "stale": [], "unknown": []},
                   "must_unknown": {"fresh": [], "stale": [], "unknown": ["c9"]}},
        "hits": {"must_stale": 1, "must_fresh": 1, "must_unknown": 1},
        "misses": {"must_stale": [], "must_fresh": [], "must_unknown": []},
        "total": 3, "all_hit": True,
    }
    detail = {cid: {"status": s, "reason": "r", "evidence_ids": [],
                    "trajectory": "t.jsonl", "steps_used": 1}
              for cid, s in decisions.items()}
    return {
        "kind": "gold_run",
        "recorded_at": "2026-09-21T00:00:00+00:00",
        "runs": 1,
        "decoding": {"model": "qwen-flash", "temperature": 0.0, "seed": None,
                     "recorded_at": "2026-09-21T00:00:00+00:00"},
        "eval_mode_switches": [],
        "per_run": [{"run": 1, "decoding": {}, "decisions": decisions,
                     "detail": detail, "matrix": matrix}],
        "pass_at_k": {"c1": 1, "c4": 1, "c9": 1},
        "point_back_j1": {cid: {"expected_anchor": None, "hit": True,
                                "evidence_ids": [], "exempt": cid == "c9"}
                          for cid in decisions},
        "counterevidence_j2": {},
        "fresh_guardrail_j2": {"c4": [True]},
        "dimension_confusion_flags": flags,
        "distractor_sensitivity": sensitivity,
    }


def test_report_flags_dimension_confusion():
    raw = _raw_gold_run({"c4": [True]}, {})
    text = render_report(raw)
    assert "维度疑似混淆" in text and "c4" in text


def test_report_clean_run_has_no_confusion_flag():
    raw = _raw_gold_run({"c4": [False]}, {})
    text = render_report(raw)
    assert "维度疑似混淆" in text  # 节在位
    assert "⚠️" not in text


def test_report_renders_distractor_appendix():
    sens = {"c13": {"expected_anchor": "t0-competitor-economics#p2@T1",
                    "statuses": ["fresh"], "fresh_hits": 1, "anchor_hits": 1,
                    "trajectory": "t.jsonl"}}
    raw = _raw_gold_run({"c4": [False]}, sens)
    text = render_report(raw)
    assert "干扰项敏感度" in text and "c13" in text
    assert "不计通过线" in text, "附表必须声明不进判分矩阵、不计通过线(判分口径不动)"


def test_report_has_layered_attribution_header():
    raw = _raw_gold_run({"c4": [False]}, {})
    text = render_report(raw)
    assert "bundle 绿" in text, "报告抬头必须落层间归因诚实框定(#19 §4.6)"


# -- 6. run_gold 结构级闭环:干扰项走真主链入口(零 LLM,脚本即收尾) ----------------


def test_run_gold_includes_distractor_appendix_zero_llm(tmp_path):
    """真 gold/docket/corpus + 立即收尾脚本 LLM:12 条主矩阵口径不变,干扰项附表成列。"""
    store = InMemoryStore()
    ingest_into(store, CORPUS)
    raw = run_gold(store, _FinishLLM(), gold_path=REPO_ROOT / "data" / "eval" / "gold.json",
                   docket_path=REPO_ROOT / "data" / "t0_docket.json", runs=1,
                   trajectory_dir=tmp_path)
    assert set(raw["pass_at_k"]) == {f"c{i}" for i in range(1, 13)}, "主矩阵仍为 12 条"
    sens = raw["distractor_sensitivity"]
    assert sorted(sens) == ["c13", "c14"]
    for cid in ("c13", "c14"):
        assert sens[cid]["statuses"] == ["unknown"], "收尾脚本零语义,全部 unknown"
        assert sens[cid]["fresh_hits"] == 0
    assert raw["dimension_confusion_flags"] == {"c4": [False], "c5": [False],
                                                "c6": [False], "c8": [False]}
    # #22 双判 visit 留档:raw 带证据包 schema 版本(#20 §4.6 随报告登记)与 S1/S2 分歧率
    assert raw["evidence_packet_schema"] == "1"
    div = raw["divergence_s1_s2"]
    assert div["total"] == 12 and div["s2"] == 0, "收尾脚本零语义:无 Auditor fresh 异议"
    text = render_report(raw)
    assert "干扰项敏感度" in text
    assert "证据包 schema 版本" in text
