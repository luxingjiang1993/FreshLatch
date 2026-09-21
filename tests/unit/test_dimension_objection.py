"""ADR-0012 受理层维度预检与异议后同维度复验路径单测(#27 实装)。

覆盖(#27/Q1–Q5 拍板逐项,Anthropic 评审修订版):
1. 受理层预检:登记维度 ≠ 反证自标维度 → 整 call 打回(DIMENSION_CROSSCHECK_MISMATCH,
   与闸不变量 8 同一 error_code/同一纯函数),先于 Auditor 触发(零调用)、不落判定;
2. 红线:登记维度值不进错误文案、不进任务注入(异议摘要只注结构化 kind 通用文案);
3. 恢复额度=1:第二次维度不符硬拒;探测通道封死(至多试 2 值,枚举空间 6);
4. 异议状态机:打回置位 / reverify_claim·mark_stale 受理即清 / finish 置位期间机械拒绝;
5. 闸侧落卡:异议未清且落 unknown → _finalize 挂 mechanical_precheck 异议(黄卡不断供);
6. 跨轮注入:dissent 非空 → task 注入异议摘要;eval 路径(dissent=None)零行为变化。

结构断言 ≠ 模型行为证明;c5/c6 ≥2/3 fresh 行为验收判据 pre-registered(#27 工单体),
判定人触发,本文件不碰。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.gates.rule_gate import ERR_DIMENSION_CROSSCHECK_MISMATCH
from freshlatch.models import Claim
from freshlatch.roles.lead import (FINISH_OBJECTION_REFUSAL,
                                   MARK_STALE_DIMENSION_PRECHECK,
                                   MARK_STALE_OBJECTION_QUOTA_REFUSAL,
                                   LeadReverifier)
from freshlatch.runner import ClaimDecision, RunContext, Runner
from freshlatch.store.base import InMemoryStore
from freshlatch.guardrails import Guardrails

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

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


class _ScriptLLM:
    def __init__(self, script):
        self._script = list(script)

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _aud(payload):
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def _ctx() -> RunContext:
    return RunContext(store=InMemoryStore(), guardrails=Guardrails())


def _lead(claim=None, llm=None):
    return LeadReverifier(_ctx(), claim or Claim(claim_id="c5", statement="s",
                                                 t0_evidence_ids=[]),
                          llm or _ScriptLLM([]))


def _registered_claim() -> Claim:
    return Claim(claim_id="c5", statement="s", t0_evidence_ids=[],
                 dimension="cost_model")  # 与回填表一致


def _stale_args(dimension="competitor_pricing") -> dict:
    return {"claim_id": "c5", "reason": REASON,
            "evidence_ids": ["t0-x#p2@T1"], "dimension": dimension}


# -- 1. 受理层预检(先于 Auditor、同一 error_code、不落判定) ---------------------------------


def test_precheck_blocks_mismatch_before_auditor():
    """登记维度(cost_model)≠ 自标维度(competitor_pricing):整 call 打回。

    零 Auditor 调用(脚本空,任何调用即 IndexError)、不落判定、异议置位。
    """
    llm = _ScriptLLM([])  # 预检先于 Auditor:非空脚本即证明 Auditor 被误触
    lead = _lead(claim=_registered_claim(), llm=llm)
    lead._seen_evidence.add("t0-x#p2@T1")
    r = lead._t_mark_stale(_stale_args())
    assert "error" in r
    assert ERR_DIMENSION_CROSSCHECK_MISMATCH in r["error"]
    assert "competitor_pricing" in r["error"], "回执须带 Lead 自标的 Y(其已知)"
    assert "cost_model" not in r["error"], "ADR-0011 红线:登记维度 X 值不披露"
    assert lead.decision.status == "unknown", "打回不落判定"
    assert lead.decision.stale_dimension is None
    assert lead.decision.auditor_verdict is None
    assert lead._objection is not None
    assert lead._objection["stale_dimension"] == "competitor_pricing"


def test_precheck_skips_when_unregistered():
    """未登记主张(claim.dimension=None):预检无锚可比对 → 跳过,回落 Auditor(不变量 7)。"""
    llm = _ScriptLLM([_aud({"status": "stale", "reason": "反证成立",
                            "dimension_match": True})])
    lead = _lead(Claim(claim_id="cX", statement="s", t0_evidence_ids=[]), llm=llm)
    lead._seen_evidence.add("t0-x#p2@T1")
    r = lead._t_mark_stale({"claim_id": "cX", "reason": REASON,
                            "evidence_ids": ["t0-x#p2@T1"],
                            "dimension": "competitor_pricing"})
    assert "error" not in r, "未登记主张不得被机械预检憋死(ADR-0011 fail-soft)"
    assert lead.decision.status == "stale"


def test_precheck_match_proceeds_and_clears_objection():
    """打回后同维度 mark_stale(cost_model):受理、Auditor 在场、旧异议清除。"""
    lead = _lead(claim=_registered_claim(), llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    assert "error" in lead._t_mark_stale(_stale_args()), "前置:首次维度不符打回"
    llm2 = _ScriptLLM([_aud({"status": "stale", "reason": "反证成立",
                             "dimension_match": True})])
    lead.llm = llm2
    r = lead._t_mark_stale(_stale_args(dimension="cost_model"))
    assert "error" not in r, "同维度反证过跨检,不得被额度误伤"
    assert lead.decision.status == "stale"
    assert lead._objection is None, "新判定受理即清旧异议(finish 闸放行)"


# -- 2. 恢复额度与探测通道 ------------------------------------------------------------------


def test_second_mismatch_quota_refusal():
    """恢复额度=1:第二次维度不符 → 硬拒(区别于首次打回文案),仍零 Auditor 调用。"""
    lead = _lead(claim=_registered_claim(), llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    r1 = lead._t_mark_stale(_stale_args())
    assert MARK_STALE_DIMENSION_PRECHECK.split(":", 1)[0].split("打回")[0] in r1["error"]
    r2 = lead._t_mark_stale(_stale_args(dimension="market_structure"))
    assert "error" in r2
    assert MARK_STALE_OBJECTION_QUOTA_REFUSAL in r2["error"], "第二次 = 额度硬拒文案"
    assert r2["error"] != r1["error"]
    assert lead.decision.status == "unknown", "硬拒同样不落判定"
    assert lead._objection["stale_dimension"] == "competitor_pricing", "额度不重置异议"


# -- 3. 异议状态机与 finish 机械闸 -----------------------------------------------------------


def test_finish_refused_while_objection_pending():
    """异议未清 → finish_reverify 机械拒绝(0/6 教训:强制性不住提示词,住闸)。"""
    lead = _lead(claim=_registered_claim(), llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    lead._t_mark_stale(_stale_args())
    r = lead._t_finish({})
    assert "error" in r and FINISH_OBJECTION_REFUSAL in r["error"]
    assert not lead._finished


def test_reverify_unknown_clears_objection_and_allows_finish():
    """reverify_claim(unknown) 受理 → 异议清除 → finish 放行。"""
    lead = _lead(claim=_registered_claim(), llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    lead._t_mark_stale(_stale_args())
    r = lead._t_reverify_claim({"claim_id": "c5", "status": "unknown",
                                "evidence_ids": []})
    assert "error" not in r
    assert lead.decision.status == "unknown"
    assert lead._objection is None
    assert "error" not in lead._t_finish({}), "显式收口后 finish 放行"
    assert lead._finished


def test_recovery_fresh_keeps_double_judgment():
    """异议后 reverify_claim(fresh):双判链完整(Critic checkpoint 去重后 Auditor 在场)。"""
    llm = _ScriptLLM([_aud({"status": "fresh", "reason": "双判一致",
                            "dimension_match": True})])
    lead = _lead(claim=_registered_claim(), llm=llm)
    lead._critic_spawned = True  # checkpoint 去重已另有覆盖,本测聚焦双判
    lead._seen_evidence.add("t0-x#p2@T1")
    lead._t_mark_stale(_stale_args())
    r = lead._t_reverify_claim({"claim_id": "c5", "status": "fresh",
                                "evidence_ids": ["t0-x#p2@T1"]})
    assert "error" not in r
    assert lead.decision.status == "fresh"
    assert lead.decision.auditor_verdict == "fresh", "fresh 仍唯一经双判一致"
    assert lead._objection is None


# -- 4. 闸侧落卡(异议未清 + unknown → dissent 不断供) ----------------------------------------


def test_finalize_hangs_precheck_dissent_when_unresolved():
    """异议未清且未落 fresh/stale → _finalize 挂 mechanical_precheck 异议(ADR-0012)。"""
    claim = _registered_claim()
    decision = ClaimDecision(claim_id="c5", status="unknown", reason="证据不足",
                             dimension_objection={
                                 "error_code": ERR_DIMENSION_CROSSCHECK_MISMATCH,
                                 "stale_dimension": "competitor_pricing",
                                 "evidence_ids": ["t0-x#p2@T1"]})
    Runner(InMemoryStore(), mode="eval")._finalize(claim, decision)
    assert claim.status == "unknown"
    assert claim.dissent is not None
    assert claim.dissent["kind"] == "mechanical_precheck"
    assert claim.dissent["evidence_ids"] == ["t0-x#p2@T1"]
    assert "cost_model" not in claim.dissent["reason"], "挂卡理由同样不披露登记值"
    assert "ADR-0012" in claim.dissent["reason"]


def test_finalize_no_dissent_without_objection():
    """无异议的普通 unknown(如证据不足)→ 不挂异议(不造虚假异议记录)。"""
    claim = _registered_claim()
    decision = ClaimDecision(claim_id="c5", status="unknown", reason="证据不足")
    Runner(InMemoryStore(), mode="eval")._finalize(claim, decision)
    assert claim.status == "unknown"
    assert claim.dissent is None


def test_finalize_no_dissent_when_recovered_fresh():
    """异议后经显式收口落 fresh(双判一致)→ 不挂异议(异议已被解决,黄卡无需此输入)。"""
    claim = _registered_claim()
    decision = ClaimDecision(claim_id="c5", status="fresh", reason="同维度证据支持",
                             evidence_ids=["t0-x#p2@T1"],
                             auditor_verdict="fresh",
                             dimension_objection=None)
    runner = Runner(InMemoryStore(), mode="eval")
    runner._finalize(claim, decision)
    assert claim.status == "fresh"
    assert claim.dissent is None


# -- 5. 跨轮注入(dissent → task;红线与 eval 零变化) -----------------------------------------


def test_task_injects_objection_summary_without_reason_or_dimension():
    """dissent 非空 → task 注入 kind 通用文案;原始 reason(含登记值)与维度值零泄漏。"""
    claim = _registered_claim()
    claim.dissent = {"kind": "mechanical_crosscheck",
                     "auditor_verdict": None,
                     "reason": "[机械跨检] 登记维度 cost_model ≠ 反证自标维度 competitor_pricing",
                     "evidence_ids": []}
    lead = _lead(claim=claim)
    task = lead._build_task()
    assert "上轮未决异议" in task
    assert "机械跨检" in task
    assert "cost_model" not in task, "闸层异议原文含登记值,注入必须过滤(红线)"
    assert "[机械跨检] 登记维度" not in task, "不得原样带 reason"


def test_task_injects_auditor_semantic_kind():
    """kind=auditor_semantic → 对应文案注入。"""
    claim = _registered_claim()
    claim.dissent = {"kind": "auditor_semantic", "auditor_verdict": "stale",
                     "reason": "Auditor 认为反证不成立", "evidence_ids": []}
    task = _lead(claim=claim)._build_task()
    assert "Auditor 语义异议" in task


def test_task_unchanged_without_dissent():
    """dissent=None(eval 每遍现载的同形状)→ task 无注入段,评测路径零行为变化。"""
    lead = _lead(claim=_registered_claim())
    task = lead._build_task()
    assert "上轮未决异议" not in task
    assert "cost_model" not in task, "红线常设:登记维度任何形态不进 Lead 上下文"


def test_precheck_block_event_records_dimension_values():
    """轨迹逐 call 留档自标维度值(探测拟合形态可归因,#27/Q4 Anthropic 修订)。"""
    lead = _lead(claim=_registered_claim(), llm=_ScriptLLM([]))
    lead._seen_evidence.add("t0-x#p2@T1")
    lead._t_mark_stale(_stale_args())
    events = [e for e in lead.ctx.events if e["type"] == "dimension_precheck_block"]
    assert len(events) == 1
    assert events[0]["stale_dimension"] == "competitor_pricing"
    assert events[0]["quota"] == 1
