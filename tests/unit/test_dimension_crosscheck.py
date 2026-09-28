"""ADR-0011 独立标注源维度跨检单测(#29 实装;bundle 纪律:确定性层逐位可复现)。

覆盖三层(与 bundle 四项一一对应):
1. 签发校验:load_docket 对非法 dimension 硬拒绝(坏卷宗不进系统),缺失 = None 不拦;
2. 边界硬校验:mark_stale 双侧镜像(Lead/Critic)dimension 必填,非法值整 call 拒绝、
   回列词表,且校验先于 Auditor 触发(打回不落判定、零 Auditor 调用);
3. 闸字符串比对:不变量 8 位置(6 之后、7 之前)、错配打回 DIMENSION_CROSSCHECK_MISMATCH、
   两维任一缺失回落不变量 7、runner 端到端机械比对异议挂卡。

结构断言 ≠ 模型行为证明;行为验收在 #30(判据 pre-registered,判定人触发)。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext, load_docket
from freshlatch.store.base import InMemoryStore
from freshlatch.tools import FOCUS_DIMENSIONS

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DIMENSIONS = {  # 与 data/t0_docket.json 回填表(#29 决议评论提案)逐位一致
    "c1": "competitor_pricing", "c2": "regulatory_stance",
    "c3": "interview_reversal", "c4": "market_structure",
    "c5": "cost_model", "c6": "competitor_pricing",
    "c7": "competitor_pricing", "c8": "tech_ecosystem",
    "c9": "market_structure", "c10": "cost_model",
    "c11": "market_structure", "c12": "tech_ecosystem",
}

REASON = ("T1 原文明确推翻:测试反证,锚定主张前提的显式因果句,不少于二十字")


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


_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_dc_{_tc_counter}", type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
    )


class _ScriptLLM:
    def __init__(self, script):
        self._script = list(script)

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _aud(payload):
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def _ctx() -> RunContext:
    return RunContext(store=InMemoryStore(), guardrails=__import__(
        "freshlatch.guardrails", fromlist=["Guardrails"]).Guardrails())


def _store() -> InMemoryStore:
    """带 t0-x#p2@T1 块的内存 store(脚本 retrieve 后可引用)。

    另加两篇无关文档:单/双文档语料 BM25 idf ≤ 0、score 被召回层滤掉
    (rank_bm25 idf = ln((N-df+0.5)/(df+0.5)),N>2·df 才为正;既有测试同款多文档结构)。
    """
    from freshlatch.store.base import Chunk
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t0-x", as_of="T1", source_type="public", title="t",
                        doc_version="v2", checksum="",
                        full_text="T1 复测:竞品定价已变,推翻主张前提。"),
        [Chunk(doc_id="t0-x", chunk_id="t0-x-p2", clause_id="p2", title="t",
               text="T1 复测:竞品定价已变,推翻主张前提。", source_type="public",
               as_of="T1", doc_version="v2", checksum="", tokens=20)],
    )
    for doc_id, text in (("t0-side", "市场杂项,与本主张无关。"),
                         ("t0-side2", "渠道访谈纪要,与本主张无关。")):
        store.add_document(
            SimpleNamespace(doc_id=doc_id, as_of="T1", source_type="public", title="t",
                            doc_version="v2", checksum="", full_text=text),
            [Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-p1", clause_id="p1", title="t",
                   text=text, source_type="public", as_of="T1",
                   doc_version="v2", checksum="", tokens=20)],
        )
    return store


def _lead(claim=None, llm=None):
    return LeadReverifier(_ctx(), claim or Claim(claim_id="c5", statement="s",
                                                 t0_evidence_ids=[]),
                          llm or _ScriptLLM([]))


def _critic(claim=None):
    return Critic(_ctx(), claim or Claim(claim_id="c5", statement="s",
                                         t0_evidence_ids=[]),
                  _ScriptLLM([]))


def _gate_kwargs(**kw):
    kw.setdefault("status", "stale")
    kw.setdefault("t1_evidence_ids", ["t0-x#p2@T1"])
    kw.setdefault("auditor_verdict", "stale")
    kw.setdefault("auditor_dimension_match", True)
    return kw


def _gate(**kw) -> GateDecision:
    return GateDecision(**_gate_kwargs(**kw))


# -- 1. 签发校验 ---------------------------------------------------------------------------


def test_docket_backfill_matches_resolution_table():
    """存量回填(#29 bundle 2)逐位对账:12 条主张 dimension 与决议提案表一致。"""
    docket = load_docket(REPO_ROOT / "data" / "t0_docket.json")
    assert len(docket.claims) == 12
    for claim in docket.claims:
        assert claim.dimension == DIMENSIONS[claim.claim_id], claim.claim_id


def test_load_docket_rejects_illegal_dimension(tmp_path):
    """签发即校验:非法 dimension 硬拒绝,坏卷宗不进系统(ADR-0011 §1)。"""
    bad = tmp_path / "bad_docket.json"
    bad.write_text(json.dumps({
        "question": "q",
        "claims": [{"claim_id": "cX", "statement": "s",
                    "t0_evidence_ids": [], "dimension": "pricing"}],  # 非枚举值
    }, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="dimension 非法值"):
        load_docket(bad)


@pytest.mark.parametrize("dim", list(FOCUS_DIMENSIONS))
def test_load_docket_accepts_all_enum_values(tmp_path, dim):
    """枚举 6 值全部放行(封闭枚举与 FOCUS_DIMENSIONS 同源)。"""
    ok = tmp_path / "ok_docket.json"
    ok.write_text(json.dumps({
        "question": "q",
        "claims": [{"claim_id": "cX", "statement": "s",
                    "t0_evidence_ids": [], "dimension": dim}],
    }, ensure_ascii=False), encoding="utf-8")
    assert load_docket(ok).claims[0].dimension == dim


def test_load_docket_missing_dimension_is_none(tmp_path):
    """缺失 = 未登记主张:不拦导入(机械跨检无锚可比对,回落不变量 7)。"""
    legacy = tmp_path / "legacy_docket.json"
    legacy.write_text(json.dumps({
        "question": "q",
        "claims": [{"claim_id": "cX", "statement": "s", "t0_evidence_ids": []}],
    }, ensure_ascii=False), encoding="utf-8")
    assert load_docket(legacy).claims[0].dimension is None


# -- 2. 边界硬校验(双侧镜像,整段复刻 focus 形态)--------------------------------------------


def test_lead_mark_stale_illegal_dimension_rejected():
    """Lead 侧:非法 dimension 整 call 拒绝、回列词表;不落判定、不触发 Auditor。"""
    llm = _ScriptLLM([])  # 脚本空:任何 Auditor 调用都会 IndexError(断言零触发)
    lead = _lead(llm=llm)
    lead._seen_evidence.add("t0-x#p2@T1")
    r = lead._t_mark_stale({"claim_id": "c5", "reason": REASON,
                            "evidence_ids": ["t0-x#p2@T1"], "dimension": "pricing"})
    assert "error" in r
    for dim in FOCUS_DIMENSIONS:
        assert dim in r["error"], "错误信息必须回列全部合法值(focus 同款形态)"
    assert lead.decision.status == "unknown", "打回不落判定"
    assert lead.decision.stale_dimension is None
    assert lead.decision.auditor_verdict is None, "dimension 校验先于 Auditor 触发"


def test_lead_mark_stale_missing_dimension_rejected():
    """Lead 侧:缺 dimension(None)同样整 call 拒绝——必填不设默认占位枚举。"""
    lead = _lead()
    lead._seen_evidence.add("t0-x#p2@T1")
    r = lead._t_mark_stale({"claim_id": "c5", "reason": REASON,
                            "evidence_ids": ["t0-x#p2@T1"]})
    assert "error" in r and "dimension" in r["error"]
    assert lead.decision.status == "unknown"


def test_lead_mark_stale_legal_dimension_recorded():
    """Lead 侧:合法 dimension 受理并随判定包登记(进 ClaimDecision.stale_dimension)。"""
    llm = _ScriptLLM([_aud({"status": "stale", "reason": "反证成立",
                            "dimension_match": True})])
    lead = _lead(llm=llm)
    lead._seen_evidence.add("t0-x#p2@T1")
    r = lead._t_mark_stale({"claim_id": "c5", "reason": REASON,
                            "evidence_ids": ["t0-x#p2@T1"], "dimension": "cost_model"})
    assert "error" not in r
    assert lead.decision.status == "stale"
    assert lead.decision.stale_dimension == "cost_model"


def test_critic_mark_stale_illegal_dimension_rejected():
    """Critic 侧:非法 dimension 整 call 拒绝、回列词表;候选反证不记录。"""
    critic = _critic()
    critic._seen_evidence.add("t0-x#p2@T1")
    r = critic._t_mark_stale({"reason": REASON, "evidence_ids": ["t0-x#p2@T1"],
                              "dimension": "cost"})
    assert "error" in r
    for dim in FOCUS_DIMENSIONS:
        assert dim in r["error"]
    assert critic.result.stale_reason == "", "打回不记录候选反证"
    assert critic.result.stale_dimension is None


def test_critic_mark_stale_legal_dimension_recorded():
    """Critic 侧:合法 dimension 受理,随 CriticResult 回吐 Lead(派驻观察带 stale_dimension)。"""
    critic = _critic()
    critic._seen_evidence.add("t0-x#p2@T1")
    r = critic._t_mark_stale({"reason": REASON, "evidence_ids": ["t0-x#p2@T1"],
                              "dimension": "competitor_pricing"})
    assert "error" not in r
    assert r["recorded_counter_evidence"]["dimension"] == "competitor_pricing"
    assert critic.result.stale_dimension == "competitor_pricing"


def test_registered_dimension_not_in_model_context():
    """ADR-0011 差异③:登记维度不注入 Lead/Critic 上下文(闸层独享比对锚)。

    Critic 装配 + Lead 装配全文不得出现登记维度值——「照锚填字段」对策不成立的前提。
    """
    claim = Claim(claim_id="c5", statement="s", t0_evidence_ids=[],
                  dimension="cost_model")
    lead = _lead(claim=claim)
    task = lead._build_task()
    assert "cost_model" not in task, "Lead 任务上下文不得泄漏登记维度"
    critic = Critic(_ctx(), claim, _ScriptLLM([]), focus=None)
    assert "cost_model" not in critic._build_system(), "Critic 系统提示不得泄漏登记维度"


# -- 3. 闸字符串比对(不变量 8)-------------------------------------------------------------


def _ctx_gate(**kw) -> GateContext:
    kw.setdefault("checksum_fn", lambda doc_id, as_of: None)
    return GateContext(**kw)


def test_invariant8_mismatch_blocks_with_code():
    """登记维度 ≠ 反证自标维度:纯字符串比对打回,DIMENSION_CROSSCHECK_MISMATCH。"""
    r = rule_gate(Claim(claim_id="c5", statement="s"),
                  _gate(registered_dimension="cost_model",
                        stale_dimension="competitor_pricing"),
                  _ctx_gate())
    assert not r.allowed and not r.green
    assert r.error_code == "DIMENSION_CROSSCHECK_MISMATCH"
    assert "cost_model" in r.reason and "competitor_pricing" in r.reason


def test_invariant8_match_falls_through_to_invariant7():
    """两维一致:不变量 8 放行,照常进不变量 7(Auditor 语义核对)。"""
    r = rule_gate(Claim(claim_id="c5", statement="s"),
                  _gate(registered_dimension="cost_model", stale_dimension="cost_model"),
                  _ctx_gate())
    assert r.allowed and not r.green


def test_invariant8_skips_when_either_missing():
    """两维任一缺失 → 跳过不变量 8,回落不变量 7(fail-soft,不憋死真 stale)。"""
    claim = Claim(claim_id="c5", statement="s")
    # 未登记主张(登记维度缺失)
    r = rule_gate(claim, _gate(registered_dimension=None,
                               stale_dimension="competitor_pricing"), _ctx_gate())
    assert r.allowed, "登记维度缺失回落不变量 7,不机械打回"
    # 反证维度缺失(老调用点/平行路径)
    r = rule_gate(claim, _gate(registered_dimension="cost_model",
                               stale_dimension=None), _ctx_gate())
    assert r.allowed, "反证维度缺失同样跳过"


def test_invariant8_runs_before_invariant7():
    """位置断言:错配 + Auditor 缺席 → 报 DIMENSION_CROSSCHECK_MISMATCH 而非 AUDITOR_ABSENT
    (机械预检先于 Auditor 依赖项;若 7 在前,缺席兜底会先拦)。"""
    r = rule_gate(Claim(claim_id="c5", statement="s"),
                  _gate(registered_dimension="cost_model",
                        stale_dimension="competitor_pricing",
                        auditor_verdict=None, auditor_dimension_match=None),
                  _ctx_gate())
    assert r.error_code == "DIMENSION_CROSSCHECK_MISMATCH"


def test_invariant8_runs_after_invariant6():
    """位置断言:元陈述理由 + 维度错配 → 报 META_ONLY_DISPROOF(不变量 6 优先)。"""
    from tests.unit.test_meta_gate import C9_RUN2_REASON
    r = rule_gate(Claim(claim_id="c9", statement="s"),
                  _gate(stale_reason=C9_RUN2_REASON,
                        registered_dimension="market_structure",
                        stale_dimension="competitor_pricing"),
                  _ctx_gate())
    assert r.error_code == "META_ONLY_DISPROOF"


def test_invariant8_not_applicable_to_fresh():
    """fresh 请求不进 stale 分支:维度字段不参与 fresh 侧校验。"""
    r = rule_gate(Claim(claim_id="c5", statement="s"),
                  GateDecision(status="fresh", t1_evidence_ids=["t0-x#p2@T1"],
                               auditor_verdict="fresh",
                               registered_dimension="cost_model",
                               stale_dimension="competitor_pricing"),
                  _ctx_gate())
    assert r.green, "跨检只约束 stale 分支,fresh 双判一致即可绿"


# -- 4. runner 端到端:机械比对异议挂卡 -----------------------------------------------------


def test_runner_precheck_blocks_mismatch_end_to_end(tmp_path):
    """端到端(ADR-0012 后形态):mark_stale 错配维度 → 受理层预检打回,不再到闸。

    Lead 主链上不变量 8 的闸层拦截已被受理层预检前置(同一比对函数/同一
    error_code);模型被打回后若未显式收口(脚本直接收尾),落 unknown +
    mechanical_precheck 异议。本测试即「闸层不变量 8 对 Lead 路径转兜底」
    的登记锚:拦截点在受理层,归因看 dimension_precheck_block 事件。
    """
    from freshlatch.runner import Runner

    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "竞品 定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"claim_id": "c5", "reason": REASON,
                                             "evidence_ids": ["t0-x#p2@T1"],
                                             "dimension": "competitor_pricing"})]),
        _Msg(content="复验结束"),  # 打回后模型直接文本收尾(finish 被拒前的脚本形态)
    ])
    runner = Runner(_store(), llm)
    # 检索串来自主张查询变换,夹具主张须能召回后续引用的证据块。
    claim = Claim(claim_id="c5", statement="竞品定价已变", t0_evidence_ids=[],
                  dimension="cost_model")
    runner.run([claim], trajectory_dir=tmp_path)

    assert claim.status == "unknown"
    assert claim.dissent is not None, "预检打回且未显式收口 → 挂机械预检异议(黄卡不断供)"
    assert claim.dissent["kind"] == "mechanical_precheck"
    assert "ADR-0012" in claim.dissent["reason"]
    blocks = [e for e in runner.ctx.events if e["type"] == "dimension_precheck_block"]
    assert len(blocks) == 1 and blocks[0]["stale_dimension"] == "competitor_pricing"
    assert not any(e["type"] == "auditor_spawn" for e in runner.ctx.events), \
        "预检先于 Auditor:打回零 Auditor 调用"


def test_runner_gate_layer_crosscheck_dissent_backstop():
    """闸层不变量 8 兜底仍有效:绕过受理层的 stale 判定(判定包直注错配维度)到 _finalize
    → unknown + mechanical_crosscheck 异议(ADR-0011 形态不动;ADR-0012 登记为兜底)。"""
    from freshlatch.runner import ClaimDecision, Runner

    claim = Claim(claim_id="c5", statement="s", t0_evidence_ids=[],
                  dimension="cost_model")
    decision = ClaimDecision(claim_id="c5", status="stale", reason=REASON,
                             evidence_ids=["t0-x#p2@T1"],
                             auditor_verdict="stale", auditor_dimension_match=True,
                             stale_dimension="competitor_pricing")
    Runner(InMemoryStore(), mode="eval")._finalize(claim, decision)
    assert claim.status == "unknown"
    assert "DIMENSION_CROSSCHECK_MISMATCH" in claim.reason
    assert claim.dissent is not None
    assert claim.dissent["kind"] == "mechanical_crosscheck"
    assert claim.dissent["reason"].startswith("[机械跨检]")
    assert "cost_model" in claim.dissent["reason"]
    assert "competitor_pricing" in claim.dissent["reason"]
    assert claim.dissent["evidence_ids"] == ["t0-x#p2@T1"]


def test_runner_invariant8_skipped_when_unregistered(tmp_path):
    """端到端:未登记主张(dimension=None)mark_stale 不被机械跨检憋死,回落不变量 7。

    Auditor 维度相符 → stale 正常落档(与 ADR-0011 §4 回填窗口职责分账一致)。
    """
    from freshlatch.runner import Runner

    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "竞品 定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"claim_id": "c5", "reason": REASON,
                                             "evidence_ids": ["t0-x#p2@T1"],
                                             "dimension": "competitor_pricing"})]),
        _aud({"status": "stale", "reason": "反证成立", "dimension_match": True}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    runner = Runner(_store(), llm)
    # 检索串来自主张查询变换,夹具主张须能召回后续引用的证据块。
    claim = Claim(claim_id="c5", statement="竞品定价已变", t0_evidence_ids=[])  # dimension=None
    runner.run([claim], trajectory_dir=tmp_path)

    assert claim.status == "stale", "未登记主张回落不变量 7,真 stale 照常落档"
    assert claim.dissent is None
