"""#467：T/B1 同 after 再分叉 + 门闩复测夹具（默认零 LLM）。"""

from __future__ import annotations

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_gate_retest import (
    arm_natural_stats,
    gate_conditions,
    natural_release_claim_ids,
    render_gate_separation_markdown,
)
from freshlatch.eval.patch_events_metrics import compare_primary, named_streams
from freshlatch.eval.patch_events_verify import verify_edit


def _candidate(claim_id: str, *, gold: str, evidence_id: str, evidence_text: str) -> dict:
    return {
        "claim_id": claim_id,
        "edit_type": "数值",
        "arm": "T",
        "ablation": "",
        "construction_gold": gold,
        "before_text": f"{claim_id}-前",
        "after_text": "",
        "evidence_id": evidence_id,
        "evidence_text": evidence_text,
    }


def _shared_copy_generator(request):
    """夹具：rewrite/diff 一律抄 evidence_text，保证同 after 上核验可过。"""
    if request["phase"] == "claim":
        return {"claim_text": f"主张-{request['claim_id']}", "latency_ms": 1, "cost": 0}
    return {
        "after_text": request["evidence_text"],
        "evidence_id": request["evidence_id"],
        "latency_ms": 2,
        "cost": 0,
    }


def test_shared_after_fork_natural_release_sets_can_differ():
    """同 after 上：绑定缝只挡 T → T/B1 自然放行集可以不同。"""
    candidates = [
        _candidate(
            "a-bound",
            gold="正确",
            evidence_id="doc#a@T1",
            evidence_text="证据甲",
        ),
        _candidate(
            "b-unbound",
            gold="正确",
            evidence_id="doc#b@T0",
            evidence_text="证据乙",
        ),
        _candidate(
            "c-bound-bad",
            gold="坏",
            evidence_id="doc#c@T1",
            evidence_text="证据丙",
        ),
    ]
    calls: list[tuple[str, str]] = []

    def counting_generator(request):
        calls.append((str(request["arm"]), str(request["phase"])))
        return _shared_copy_generator(request)

    result = run_arms(
        candidates,
        generator=counting_generator,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=0),
        ingested_t1={"doc#a@T1", "doc#c@T1"},
    )

    # 同 after：B1 不再单独 rewrite；T 与 B1 after 逐字相同。
    rewrite_arms = [arm for arm, phase in calls if phase == "rewrite"]
    assert rewrite_arms.count("T") == 3
    assert "B1" not in rewrite_arms
    for left, right in zip(result["T"], result["B1"], strict=True):
        assert left["after_text"] == right["after_text"]
        assert left["claim_id"] == right["claim_id"]

    t_ids = set(natural_release_claim_ids(result["T"]))
    b1_ids = set(natural_release_claim_ids(result["B1"]))
    assert t_ids == {"a-bound", "c-bound-bad"}
    assert b1_ids == {"a-bound", "b-unbound", "c-bound-bad"}
    assert t_ids != b1_ids

    by_t = {row["claim_id"]: row for row in result["T"]}
    by_b1 = {row["claim_id"]: row for row in result["B1"]}
    assert by_t["b-unbound"]["decision"] == "reject"
    assert by_t["b-unbound"]["reject_reason"] == "证据未绑定已入库 T1"
    assert by_b1["b-unbound"]["decision"] == "release"
    assert by_b1["b-unbound"]["reverify_ok"] is True


def test_b1_verify_failure_still_hard_rejects_on_shared_after():
    candidates = [
        _candidate(
            "mismatch",
            gold="正确",
            evidence_id="doc#m@T1",
            evidence_text="应对齐",
        )
    ]

    def paraphrase(request):
        if request["phase"] == "claim":
            return {"claim_text": "主张", "latency_ms": 0, "cost": 0}
        return {
            "after_text": "并不对齐",
            "evidence_id": request["evidence_id"],
            "latency_ms": 0,
            "cost": 0,
        }

    result = run_arms(
        candidates,
        generator=paraphrase,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=1),
        ingested_t1={"doc#m@T1"},
    )
    assert result["T"][0]["after_text"] == result["B1"][0]["after_text"] == "并不对齐"
    assert result["T"][0]["decision"] == "reject"
    assert result["B1"][0]["decision"] == "reject"
    assert result["B1"][0]["reject_reason"] == "核验不过"
    assert result["T"][0]["reject_reason"] == "核验不过"


def test_gate_retest_report_is_disposable_and_zero_llm_by_default():
    candidates = [
        _candidate("x1", gold="正确", evidence_id="doc#x@T1", evidence_text="X"),
        _candidate("x2", gold="坏", evidence_id="doc#y@T0", evidence_text="Y"),
    ]
    result = run_arms(
        candidates,
        generator=_shared_copy_generator,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=2),
        ingested_t1={"doc#x@T1"},
    )
    primary = compare_primary(
        primary_comparison_rows(result),
        ingested_t1={"doc#x@T1"},
        streams=named_streams(),
    )
    markdown = render_gate_separation_markdown(
        arm_rows=result,
        primary_report=primary,
        source_note="夹具 · 零 LLM",
    )
    assert "不进主表" in markdown
    assert "可扔" in markdown
    assert "非甲" in markdown
    assert "零 LLM" in markdown
    assert "自然放行" in markdown
    assert "固定 k 误放差" in markdown
    gate = gate_conditions(primary)
    assert gate["passed"] is False
    assert "不得建议激活" in markdown
    assert "PREREG-B" in markdown
    # 夹具上 T/B1 放行集可不同（同 after）
    assert arm_natural_stats(result["T"])["自然放行 claim_id"] != arm_natural_stats(
        result["B1"]
    )["自然放行 claim_id"]
