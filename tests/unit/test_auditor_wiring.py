"""#22 实装结构断言(TDD 红灯先行):Auditor 单轮 SOP 本体 + fresh/stale 双路径结构性在场
+ 规则闸不变量(auditor 在场 fail-closed + 不变量 7 维度异议)+ 落档仲裁真值表
+ 异议记录结构化落档 + S1/S2 分歧率落档。

拍板依据:#20/ADR-0009(双判一致 3×3、fresh 钩子内自动触发、闸 auditor_verdict 前置兜底)、
#25/ADR-0010(stale 路径双人防线:mark_stale 受理自动触发 Auditor、dimension_match 输出、
不变量 7 打回 unknown + 异议记录;MARK_STALE_DIMENSION_NOTE 保留为教义表兜底)。

结构断言 ≠ 模型行为证明(层间归因诚实框定,#19 §4.6 继承):行为验收 n=3 temp=0 qwen-flash
由判定人独立触发(#26,blocked by #22),不并入本工单攒批(归因纪律)。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.eval.report import render_report
from freshlatch.eval.runner import divergence_counts
from freshlatch.gates.rule_gate import (
    GateContext,
    GateDecision,
    arbitrate_fresh,
    arbitrate_stale_mark,
    rule_gate,
)
from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.auditor import (
    AUDITOR_PERSONA,
    EVIDENCE_PACKET_SCHEMA_VERSION,
    Auditor,
    AuditorVerdict,
    parse_verdict,
)
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import ClaimDecision, RunContext, Runner
from freshlatch.store.base import InMemoryStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_AUDIT = REPO_ROOT / "skills" / "freshness_audit" / "SKILL.md"

DOCTRINE_MARKER = "约束与纠正"  # freshness_audit SKILL.md 教义表节标记

CLAIM_ID = "cx"
STMT = "我方单会话服务成本仍低于竞品"
EID = "t0-cost-model#p2@T1"
REASON = ("T1 成本模型原文显示我方单会话成本 0.009 美元低于竞品折算 0.019 美元,"
          "推翻成本优势消失的前提")
DISSENT_REASON = "反证锚定的是定价维度,非主张的成本维度(定价≠成本),不构成 stale"

_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_a_{_tc_counter}", type="function",
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


def _aud(payload: dict) -> _Msg:
    """Auditor structured-output 响应(模型侧 JSON mode 的 content)。"""
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


class _ScriptLLM:
    """FIFO 脚本回吐;Lead/Critic/Auditor 共享同一脚本按调用顺序消费。"""

    def __init__(self, script):
        self._script = list(script)
        self.seen_calls: list[dict] = []  # (tools, response_format) 留档

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.seen_calls.append({"tools": tools, "response_format": response_format})
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _mk_chunk(doc_id: str, text: str):
    from freshlatch.store.base import Chunk
    return Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-p2", clause_id="p2", title="t",
                 text=text, source_type="internal", as_of="T1", doc_version="v2",
                 checksum="", tokens=20)


def _store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t0-cost-model", as_of="T1", source_type="internal",
                        title="成本模型", doc_version="v2", checksum="", full_text="x"),
        [_mk_chunk("t0-cost-model", "T1 复测:我方单会话成本 0.009 美元,竞品折算约 0.019 美元。"),
         _mk_chunk("t0-side", "市场杂项:渠道集中度上升,与本主张无关。"),
         _mk_chunk("t0-notes", "行业杂项:客服 SaaS 融资事件汇总,与本主张无关。")],
    )
    return store


def _claim() -> Claim:
    return Claim(claim_id=CLAIM_ID, statement=STMT, t0_evidence_ids=["t0-cost-model#p2"])


def _ctx(store=None) -> RunContext:
    return RunContext(store=store or InMemoryStore(), guardrails=Guardrails())


def _lead(llm, ctx=None, *, auditor_doctrine="DOCTRINE"):
    return LeadReverifier(ctx or _ctx(_store()), _claim(), llm,
                          auditor_doctrine=auditor_doctrine)


def _retrieve_first(lead):
    lead._t_retrieve({"query": "单会话成本 复测", "as_of": "T1"})


def _finalize(status: str, *, auditor_verdict=None, auditor_reason="",
              auditor_dimension_match=None, evidence=None) -> Claim:
    """Runner._finalize 直调:构造 Lead 判定 → 落档仲裁(零 LLM)。"""
    runner = Runner(_store())
    claim = _claim()
    decision = ClaimDecision(claim_id=CLAIM_ID, status=status, reason=REASON,
                             evidence_ids=evidence if evidence is not None else [EID],
                             auditor_verdict=auditor_verdict,
                             auditor_reason=auditor_reason,
                             auditor_dimension_match=auditor_dimension_match)
    runner._finalize(claim, decision)
    return claim


# -- 1. Auditor 本体:单轮 structured-output + 证据包 schema 版本化 -----------------------


def test_packet_schema_versioned_and_whitelist_texts():
    """证据包 schema 版本化(#20 子决策 1,进验收判据):版本字段在册,块文本只装白名单内 id。"""
    auditor = Auditor(_ScriptLLM([]))
    packet = auditor.build_packet(
        _claim(), lead_status="stale", lead_reason=REASON, lead_evidence_ids=[EID, "ghost#p9@T1"],
        evidence_texts={EID: "T1 复测:我方单会话成本 0.009 美元。"},
    )
    assert packet.schema_version == EVIDENCE_PACKET_SCHEMA_VERSION
    d = packet.as_dict()
    for key in ("schema_version", "claim_id", "statement", "lead_status", "lead_reason",
                "lead_evidence_ids", "evidence_texts"):
        assert key in d, f"证据包缺字段: {key}"
    assert d["lead_status"] == "stale"
    assert EID in d["evidence_texts"]
    assert "ghost#p9@T1" not in d["evidence_texts"], "未检索到的 id 不得编造块文本"


def test_parse_verdict_valid_with_dimension_match():
    v = parse_verdict(json.dumps({"status": "stale", "reason": "r", "dimension_match": False}))
    assert v.status == "stale" and v.dimension_match is False and v.reason == "r"
    assert v.schema_version == EVIDENCE_PACKET_SCHEMA_VERSION


@pytest.mark.parametrize("content", ["not json", "", None, json.dumps(["list"])])
def test_parse_verdict_non_json_fail_closed(content):
    """结构化输出解析失败 fail-closed:机器绝不把解析失败当 fresh(ADR-0009 在场不变量)。"""
    v = parse_verdict(content)
    assert v.status == "unknown"


def test_parse_verdict_invalid_status_fail_closed():
    v = parse_verdict(json.dumps({"status": "green", "reason": "r"}))
    assert v.status == "unknown"
    v2 = parse_verdict(json.dumps({"reason": "r"}))
    assert v2.status == "unknown"


def test_parse_verdict_dimension_match_non_bool_ignored():
    v = parse_verdict(json.dumps({"status": "stale", "reason": "r", "dimension_match": "否"}))
    assert v.dimension_match is None, "非 bool 的 dimension_match 不得机械消费"


def test_judge_single_round_structured_output():
    """单轮判定(无工具无循环):一次 chat、json_object response_format、教义表为主份 system。"""
    llm = _ScriptLLM([_aud({"status": "fresh", "reason": "T1 复测支持"})])
    auditor = Auditor(llm, doctrine="DOCTRINE_BODY")
    packet = auditor.build_packet(_claim(), lead_status="fresh", lead_reason="",
                                  lead_evidence_ids=[EID], evidence_texts={EID: "t"})
    v = auditor.judge(packet)
    assert v.status == "fresh"
    assert len(llm.seen_calls) == 1, "单轮 SOP:恰好一次调用"
    assert llm.seen_calls[0]["response_format"] == {"type": "json_object"}
    assert llm.seen_calls[0]["tools"] is None, "Auditor 无工具"


def test_judge_injects_doctrine_as_system():
    """SKILL.md 注入走 #19 skills 接线:教义表正文在 system prompt 在场(在盘不在场=事故根因)。"""
    llm = _ScriptLLM([_aud({"status": "unknown", "reason": "缺口"})])
    auditor = Auditor(llm, doctrine="DOCTRINE_BODY")
    packet = auditor.build_packet(_claim(), lead_status="fresh", lead_reason="",
                                  lead_evidence_ids=[], evidence_texts={})
    auditor.judge(packet)
    assert auditor.using_fallback is False


def test_judge_falls_back_to_inline_persona():
    """教义表缺失 → 内联 AUDITOR_PERSONA 兜底(不静默:调用方落 skill_fallback 事件)。"""
    llm = _ScriptLLM([_aud({"status": "unknown", "reason": "缺口"})])
    auditor = Auditor(llm, doctrine=None)
    assert auditor.using_fallback is True
    packet = auditor.build_packet(_claim(), lead_status="fresh", lead_reason="",
                                  lead_evidence_ids=[], evidence_texts={})
    auditor.judge(packet)
    assert AUDITOR_PERSONA


def test_runner_wires_freshness_audit_doctrine():
    """Runner 加载 freshness_audit 教义表并注入 Lead(沿派驻链给 Auditor)。"""
    runner = Runner(InMemoryStore())
    body = runner._doctrine["freshness_audit"]
    assert body and DOCTRINE_MARKER in body
    lead = runner._spawn_lead(_claim())
    assert lead._auditor_doctrine == body


def test_auditor_fallback_emits_skill_fallback_event():
    """Auditor 教义表缺失时触发路径落 skill_fallback(freshness_audit)——静默降级=事故复发。"""
    llm = _ScriptLLM([_aud({"status": "stale", "reason": "反证成立", "dimension_match": True})])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm, auditor_doctrine=None)
    lead._t_retrieve({"query": "单会话成本 复测", "as_of": "T1"})
    lead._t_mark_stale({"claim_id": CLAIM_ID, "reason": REASON, "evidence_ids": [EID]})
    assert any(e.get("type") == "skill_fallback" and e.get("skill") == "freshness_audit"
               for e in ctx.events)


# -- 2. fresh 路径:_t_reverify_claim(fresh) 钩子内自动触发(ADR-0009) ---------------------


def test_fresh_auto_triggers_auditor_checkpoint():
    """fresh 落判定前自动触发 Auditor(与 _auto_critic_checkpoint 同点同构),结论回吐观察。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": CLAIM_ID, "status": "fresh",
                                                 "evidence_ids": [EID]})]),
        # —— 自动派驻的 Critic 会话(critic checkpoint 先跑,顺序不变)——
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "未见推翻性证据"})]),
        _Msg(content="报告完毕"),
        # —— Auditor 单轮判定(fresh 钩子内)——
        _aud({"status": "fresh", "reason": "T1 复测支持主张每个前提"}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    lead = _lead(llm, ctx)
    decision = lead.run()

    spawns = [e for e in ctx.events if e.get("type") == "auditor_spawn"]
    assert len(spawns) == 1
    assert spawns[0].get("auto") is True and spawns[0].get("path") == "fresh"
    assert decision.auditor_verdict == "fresh"
    assert decision.status == "fresh", "钩子只做在场+记录,落档仲裁在 finalize(闸层)"

    out = [e for e in ctx.events if e.get("type") == "lead_step"
           and e.get("tool") == "reverify_claim"][0]["result"]
    assert out.get("auditor_checkpoint", {}).get("verdict") == "fresh", \
        "Auditor 结论必须回吐进 fresh 的工具观察(Lead 可见可改判)"


def test_fresh_path_critic_checkpoint_preserved():
    """ADR-0009 增量不动 §8.5:critic checkpoint 仍在,且先于 Auditor 触发(观察顺序)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": CLAIM_ID, "status": "fresh",
                                                 "evidence_ids": [EID]})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "未见推翻性证据"})]),
        _Msg(content="报告完毕"),
        _aud({"status": "fresh", "reason": "支持"}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    _lead(llm, ctx).run()
    order = [e for e in ctx.events
             if e.get("type") in ("critic_spawn", "auditor_spawn")]
    assert [e["type"] for e in order] == ["critic_spawn", "auditor_spawn"]


def test_arbitrate_fresh_table():
    """ADR-0009 3×3 的 fresh 请求行:auditor fresh→fresh;stale→stale;unknown/缺席→unknown。"""
    assert arbitrate_fresh("fresh") == "fresh"
    assert arbitrate_fresh("stale") == "stale"
    assert arbitrate_fresh("unknown") == "unknown"
    assert arbitrate_fresh(None) == "unknown", "Auditor 缺席不构成任何绿格"


def test_fresh_x_auditor_stale_finalizes_stale():
    """Lead fresh × Auditor stale → stale 落档(含 stale 落 stale;Auditor 理由作落档理由)。"""
    claim = _finalize("fresh", auditor_verdict="stale", auditor_reason="T1 原文推翻前提")
    assert claim.status == "stale"
    assert "Auditor 双判推翻" in claim.reason


def test_fresh_x_auditor_stale_dimension_mismatch_fail_closed():
    """fresh × auditor stale 但 dimension_match=False:不变量 7 优先,打回 unknown——
    不造「维度不符的红卡」(与 ADR-0010 异议落点一致;arbitrate_fresh docstring 已注明)。"""
    claim = _finalize("fresh", auditor_verdict="stale", auditor_reason="包内证据维度不符",
                      auditor_dimension_match=False)
    assert claim.status == "unknown"
    assert "DIMENSION_MISMATCH" in claim.reason


def test_fresh_x_auditor_unknown_finalizes_unknown():
    claim = _finalize("fresh", auditor_verdict="unknown", auditor_reason="证据不足")
    assert claim.status == "unknown"
    assert "双判未一致" in claim.reason


def test_fresh_auditor_absent_fail_closed_unknown():
    """Auditor 缺席(钩子未触发)时 fresh 不得绿:fail-closed 落 unknown。"""
    claim = _finalize("fresh", auditor_verdict=None)
    assert claim.status == "unknown"


# -- 3. stale 路径:_t_mark_stale 受理自动触发(ADR-0010,落档之前) --------------------------


def test_mark_stale_auto_triggers_auditor_before_recording():
    """mark_stale 受理(三重硬校验通过、落档之前)自动触发 Auditor——时点断言:触发时未落档。"""
    trigger_state: dict = {}

    def _auditor_fn(messages, tools=None):
        trigger_state["status_at_trigger"] = lead.decision.status
        return _aud({"status": "stale", "reason": "反证成立", "dimension_match": True})

    llm = _ScriptLLM([_auditor_fn])
    ctx = _ctx(_store())
    lead = _lead(llm, ctx)
    lead._t_retrieve({"query": "单会话成本 复测", "as_of": "T1"})
    res = lead._t_mark_stale({"claim_id": CLAIM_ID, "reason": REASON, "evidence_ids": [EID]})

    assert trigger_state["status_at_trigger"] == "unknown", \
        "Auditor 触发必须在落档之前(ADR-0010 子决策 1)"
    assert res.get("auditor_checkpoint", {}).get("verdict") == "stale"
    assert lead.decision.status == "stale"
    assert lead.decision.auditor_verdict == "stale"
    assert lead.decision.auditor_dimension_match is True
    assert [e for e in ctx.events if e.get("type") == "auditor_spawn"
            and e.get("path") == "stale" and e.get("auto") is True]


def test_mark_stale_meta_reason_still_rejected_before_auditor():
    """不变量 6 的环内打回先于 Auditor 触发(顺序不漂):元陈述理由零 Auditor 调用。"""
    from tests.unit.test_meta_gate import C9_RUN2_REASON
    llm = _ScriptLLM([])  # 脚本空:任何 LLM 调用都会 IndexError
    lead = _lead(llm)
    lead._seen_evidence.add("t0-messaging-survey#p3@T1")
    r = lead._t_mark_stale({"claim_id": CLAIM_ID, "reason": C9_RUN2_REASON,
                            "evidence_ids": ["t0-messaging-survey#p3@T1"]})
    assert "error" in r
    assert lead.decision.auditor_verdict is None


def test_arbitrate_stale_mark_table():
    """ADR-0010 mark_stale 路径真值表(修订 ADR-0009 stale 行);返回 (落档, 是否异议)。"""
    assert arbitrate_stale_mark("stale", True) == ("stale", False)    # uphold:真反证照落
    assert arbitrate_stale_mark("stale", None) == ("stale", False)    # 未给维度字段:不机械消费
    assert arbitrate_stale_mark("stale", False) == ("unknown", True)  # 维度异议:打回+异议
    assert arbitrate_stale_mark("fresh", None) == ("stale", True)     # ADR-0009:含 stale 落 stale+异议
    assert arbitrate_stale_mark("unknown", None) == ("stale", False)  # ADR-0009:含 stale 落 stale
    assert arbitrate_stale_mark(None, None) == ("unknown", False)     # 缺席 fail-closed


def test_mark_stale_uphold_finalizes_stale():
    """真反证(维度相符)stale 照旧落档,零变化(ADR-0010 子决策 3)。"""
    claim = _finalize("stale", auditor_verdict="stale", auditor_reason="反证成立",
                      auditor_dimension_match=True)
    assert claim.status == "stale"
    assert claim.dissent is None, "uphold 路径无异议记录"


def test_mark_stale_dimension_mismatch_routed_unknown_with_dissent():
    """不变量 7:dimension_match=False 打回 stale → unknown + 异议记录挂主张卡片。"""
    claim = _finalize("stale", auditor_verdict="stale", auditor_reason=DISSENT_REASON,
                      auditor_dimension_match=False)
    assert claim.status == "unknown"
    assert "DIMENSION_MISMATCH" in claim.reason
    assert claim.dissent == {"auditor_verdict": "stale", "reason": DISSENT_REASON,
                             "evidence_ids": [EID]}, "异议记录必须结构化(Auditor 判定+理由+证据 id)"


def test_mark_stale_auditor_fresh_keeps_stale_with_dissent():
    """ADR-0009:Lead stale × Auditor fresh → stale 照落 + 异议记录(随红卡进 HumanLatch)。"""
    claim = _finalize("stale", auditor_verdict="fresh", auditor_reason="T1 复测支持主张")
    assert claim.status == "stale"
    assert claim.dissent and claim.dissent["auditor_verdict"] == "fresh"


def test_mark_stale_auditor_absent_fail_closed():
    """Auditor 缺席不构成任何落档(ADR-0010):闸 fail-closed 打回 unknown。"""
    claim = _finalize("stale", auditor_verdict=None)
    assert claim.status == "unknown"
    assert "AUDITOR_ABSENT" in claim.reason


# -- 4. 规则闸:auditor_verdict 前置不变量 + 不变量 7 --------------------------------------


def _gate(status, *, auditor_verdict=None, auditor_dimension_match=None,
          t1=None, stale_reason="", invalidation=None):
    claim = Claim(claim_id=CLAIM_ID, statement=STMT, t0_evidence_ids=[])
    ctx = GateContext(invalidation_list=invalidation or set(),
                      checksum_fn=lambda doc_id, as_of: None)
    d = GateDecision(status=status,
                     t1_evidence_ids=t1 if t1 is not None else [EID],
                     stale_reason=stale_reason,
                     auditor_verdict=auditor_verdict,
                     auditor_dimension_match=auditor_dimension_match)
    return rule_gate(claim, d, ctx)


def test_gate_fresh_requires_auditor_verdict():
    """ADR-0009 闸前置不变量:fresh 需 auditor_verdict 在场且 == fresh(fail-closed 兜底)。"""
    r = _gate("fresh", auditor_verdict=None)
    assert not r.allowed and r.error_code == "AUDITOR_ABSENT"
    r = _gate("fresh", auditor_verdict="stale")
    assert not r.allowed and r.error_code == "ARBITRATION_MISMATCH"
    r = _gate("fresh", auditor_verdict="fresh")
    assert r.green


def test_gate_stale_requires_auditor_presence():
    """ADR-0010:Auditor 缺席不构成任何落档——stale 请求无 verdict 打回。"""
    r = _gate("stale", auditor_verdict=None)
    assert not r.allowed and r.error_code == "AUDITOR_ABSENT"


def test_gate_invariant_7_dimension_mismatch():
    """不变量 7:dimension_match=False 打回 stale(语义判断住 Auditor,闸只机械消费结构化 flag)。"""
    r = _gate("stale", auditor_verdict="stale", auditor_dimension_match=False)
    assert not r.allowed and r.error_code == "DIMENSION_MISMATCH"
    r = _gate("stale", auditor_verdict="stale", auditor_dimension_match=True)
    assert r.allowed and not r.green, "uphold:stale 落档放行但恒不绿灯"
    r = _gate("stale", auditor_verdict="stale", auditor_dimension_match=None)
    assert r.allowed, "dimension_match 缺席(None)不得误伤合法 stale"


def test_gate_stale_auditor_fresh_or_unknown_still_allowed():
    """ADR-0009 stale 行:Auditor fresh/unknown 不拦 stale 落档(异议记录由 finalize 挂)。"""
    assert _gate("stale", auditor_verdict="fresh").allowed
    assert _gate("stale", auditor_verdict="unknown").allowed


def test_gate_renew_not_auditor_gated():
    """续命(renew)是 L0 人审出口,auditor_verdict 不变量只咬 fresh(双判一致不约束人)。"""
    claim = Claim(claim_id=CLAIM_ID, statement=STMT, t0_evidence_ids=[])
    ctx = GateContext(checksum_fn=lambda doc_id, as_of: None)
    r = rule_gate(claim, GateDecision(status="renew", t1_evidence_ids=[EID]), ctx)
    assert r.green


# -- 5. 异议记录 + 轨迹留档(集成:run → 轨迹 claim_final) ---------------------------------


def test_run_dumps_auditor_and_dissent_to_trajectory(tmp_path):
    """端到端:mark_stale × 维度异议 → unknown + 异议记录;轨迹 claim_final 带 auditor/dissent 留档。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"claim_id": CLAIM_ID, "reason": REASON,
                                             "evidence_ids": [EID]})]),
        _aud({"status": "stale", "reason": DISSENT_REASON, "dimension_match": False}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    runner = Runner(_store(), llm)
    claim = _claim()
    result = runner.run([claim], trajectory_dir=tmp_path)
    assert claim.status == "unknown"
    assert claim.dissent and claim.dissent["reason"] == DISSENT_REASON

    finals = [json.loads(ln) for ln in result.trajectory_path.read_text(encoding="utf-8").splitlines()
              if json.loads(ln).get("type") == "claim_final"]
    assert len(finals) == 1
    assert finals[0]["auditor_verdict"] == "stale"
    assert finals[0]["dissent"]["reason"] == DISSENT_REASON
    assert finals[0]["schema_version"] == EVIDENCE_PACKET_SCHEMA_VERSION


def test_run_fresh_uphold_dumps_green(tmp_path):
    """fresh × Auditor fresh → 绿灯;轨迹带 auditor_verdict 留档(#20 验收结构断言④原料)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": CLAIM_ID, "status": "fresh",
                                                 "evidence_ids": [EID]})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "未见推翻性证据"})]),
        _Msg(content="报告完毕"),
        _aud({"status": "fresh", "reason": "T1 复测支持"}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    runner = Runner(_store(), llm)
    claim = _claim()
    result = runner.run([claim], trajectory_dir=tmp_path)
    assert claim.status == "fresh"
    finals = [json.loads(ln) for ln in result.trajectory_path.read_text(encoding="utf-8").splitlines()
              if json.loads(ln).get("type") == "claim_final"]
    assert finals[0]["auditor_verdict"] == "fresh"
    assert finals[0]["dissent"] is None


# -- 6. S1/S2 分歧率落档(#20 评估 §4.6:只落档不报成败) + SOP 守卫 -------------------------


def test_divergence_counts_pure():
    """操作化定义:每主张每跑 Lead stale/unknown × Auditor fresh 计 S2,反之为 S1。"""
    per_run = [{"detail": {
        "c1": {"lead_status": "stale", "auditor_verdict": "stale"},
        "c2": {"lead_status": "unknown", "auditor_verdict": "fresh"},   # S2
        "c3": {"lead_status": "fresh", "auditor_verdict": "fresh"},     # S1
        "c4": {"lead_status": "stale", "auditor_verdict": None},        # S1(缺席 fail-closed)
    }}]
    div = divergence_counts(per_run)
    assert div["s1"] == 3 and div["s2"] == 1
    assert div["total"] == 4
    assert abs(div["s2_rate"] - 0.25) < 1e-9


def test_divergence_counts_empty_runs():
    assert divergence_counts([]) == {"s1": 0, "s2": 0, "total": 0, "s2_rate": 0.0}


def test_report_renders_divergence_section():
    matrix = {"counts": {"must_stale": {"fresh": [], "stale": [], "unknown": []},
                         "must_fresh": {"fresh": [], "stale": [], "unknown": []},
                         "must_unknown": {"fresh": [], "stale": [], "unknown": []}},
              "hits": {"must_stale": 0, "must_fresh": 0, "must_unknown": 0},
              "misses": {"must_stale": [], "must_fresh": [], "must_unknown": []},
              "total": 0, "all_hit": True}
    raw = {
        "kind": "gold_run", "recorded_at": "2026-09-21T00:00:00+00:00", "runs": 1,
        "decoding": {"model": "qwen-flash", "temperature": 0.0, "seed": None},
        "eval_mode_switches": [],
        "per_run": [{"run": 1, "decoding": {}, "decisions": {}, "detail": {}, "matrix": matrix}],
        "pass_at_k": {}, "point_back_j1": {}, "counterevidence_j2": {},
        "fresh_guardrail_j2": {}, "dimension_confusion_flags": {},
        "distractor_sensitivity": {},
        "divergence_s1_s2": {"s1": 3, "s2": 1, "total": 4, "s2_rate": 0.25},
        "evidence_packet_schema": EVIDENCE_PACKET_SCHEMA_VERSION,
    }
    text = render_report(raw)
    assert "S1/S2" in text and "分歧率" in text
    assert "只落档不报成败" in text
    assert "证据包 schema 版本" in text, "schema 版本随报告登记(#20 §4.6)"


def test_freshness_audit_sop_carries_dimension_match():
    """SOP 增项(#22 范围 2):dimension_match 输出字段 + 反证维度核对项在场。"""
    text = SKILL_AUDIT.read_text(encoding="utf-8")
    assert "dimension_match" in text
    assert "维度" in text
    assert "mark_stale" in text, "SOP 必须写明 mark_stale 反证包输入形态(ADR-0010)"
