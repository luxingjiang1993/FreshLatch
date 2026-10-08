"""PE-03 四组：假生成器、假核验器，不打真实 API。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch import patch_events as product_ledger
from freshlatch.eval import patch_events_arms as arms
from freshlatch.llm import DEFAULT_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE


def _candidate(claim_id, **overrides):
    base = {
        "claim_id": claim_id,
        "edit_type": "数值",
        "arm": "T",
        "ablation": "no_chunk_bind",
        "construction_gold": "坏",
        "before_text": f"{claim_id}-修改前",
        "after_text": f"{claim_id}-构造后",
        "evidence_id": "doc#p1@T1",
        "evidence_text": "证据原文",
    }
    base.update(overrides)
    return base


class _Generator:
    def __init__(self, *, evidence_id="doc#p1@T1", fail=False):
        self.evidence_id = evidence_id
        self.fail = fail
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        if self.fail:
            return {"void": True}
        phase = request["phase"]
        claim_id = request["claim_id"]
        if phase == "claim":
            return {
                "claim_text": f"主张-{claim_id}",
                "latency_ms": 4,
                "cost": 0,
            }
        return {
            "after_text": f"生成-{request['arm']}-{claim_id}",
            "evidence_id": self.evidence_id,
            "latency_ms": 8 if phase == "diff" else 5,
            "cost": 0,
        }


class _Verifier:
    def __init__(self, *, ok=True, score=0.9, reason="核验未通过"):
        self.ok = ok
        self.score = score
        self.reason = reason
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        return {"ok": self.ok, "score": self.score, "reason": self.reason}


@pytest.fixture(autouse=True)
def _unset_keys(monkeypatch):
    for key in ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def _run(generator, verifier, **kwargs):
    decoding = kwargs.pop("decoding", arms.Decoding(temperature=0, seed=0))
    ingested = kwargs.pop("ingested_t1", {"doc#p1@T1"})
    candidates = kwargs.pop("candidates", [_candidate("c1"), _candidate("c2")])
    return arms.run_arms(
        candidates,
        generator=generator,
        verifier=verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )


def test_four_arms_share_claim_ids_and_t_reads_production_mode(monkeypatch):
    product_calls = []
    monkeypatch.setattr(
        "freshlatch.evidence_bound.confirm_patch",
        lambda **kwargs: product_calls.append("confirm"),
    )
    monkeypatch.setattr(
        "freshlatch.patch_events.append_product_confirm",
        lambda **kwargs: product_calls.append("append"),
    )
    generator = _Generator()
    verifier = _Verifier()
    result = _run(generator, verifier)
    for arm in ("C", "T", "B1", "B2"):
        records = result[arm]
        assert [row["claim_id"] for row in records] == ["c1", "c2"]
        assert [row["arm"] for row in records] == [arm, arm]
        assert all(row["ablation"] == "" for row in records)
        assert all(row["decision"] == "release" for row in records)
        # T/B1 同 after：共用一次 rewrite（请求 arm=T），故 B1 的 after 也带 T 前缀。
        expected_arm = "T" if arm in {"T", "B1"} else arm
        assert all(
            row["after_text"] == f"生成-{expected_arm}-{row['claim_id']}" for row in records
        )
    assert result["C"][0]["score"] is None
    assert result["C"][0]["evidence_id"] == ""
    assert result["T"][0]["score"] == 0.9
    assert result["T"][0]["evidence_id"] == "doc#p1@T1"
    t_calls = [call for call in generator.calls if call["arm"] == "T"]
    assert t_calls
    assert {call["retrieval_mode"] for call in t_calls} == {PRODUCTION_RETRIEVAL_MODE}
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    other = [call for call in generator.calls if call["arm"] != "T"]
    assert all(call["retrieval_mode"] is None for call in other)
    assert all(call["model"] == DEFAULT_MODEL for call in generator.calls)
    assert DEFAULT_MODEL == "qwen-flash"
    assert all(call["temperature"] == 0 and call["seed"] == 0 for call in generator.calls)
    assert all(call["arm"] != "C" for call in verifier.calls)
    assert product_calls == []
    source = Path("src/freshlatch/eval/patch_events_arms.py").read_text(encoding="utf-8")
    assert "PRODUCTION_RETRIEVAL_MODE =" not in source
    assert "DEFAULT_MODEL =" not in source
    base = Path("src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert product_ledger.VALID_ARMS == frozenset({"C", "T"})
    assert product_ledger.PRODUCT_ARM == "T"


def test_b2_generates_claim_before_diff():
    generator = _Generator()
    result = _run(generator, _Verifier())
    phases = [
        (call["phase"], call.get("claim_text"))
        for call in generator.calls
        if call["arm"] == "B2" and call["claim_id"] == "c1"
    ]
    assert phases[0][0] == "claim"
    assert phases[1] == ("diff", "主张-c1")
    assert result["B2"][0]["after_text"] == "生成-B2-c1"
    assert result["B2"][0]["latency_ms"] == 12


def test_verify_failure_rejects_b1_and_t_but_not_b2(monkeypatch):
    product_calls = []
    monkeypatch.setattr(
        "freshlatch.evidence_bound.confirm_patch",
        lambda **kwargs: product_calls.append(("confirm", kwargs.get("claim_id"))),
    )
    monkeypatch.setattr(
        "freshlatch.patch_events.append_product_confirm",
        lambda **kwargs: product_calls.append(("append", kwargs.get("claim_id"))),
    )
    result = _run(_Generator(), _Verifier(ok=False, score=0.1, reason="核验未通过"))
    b1 = result["B1"][0]
    b2 = result["B2"][0]
    tee = result["T"][0]
    assert b1["arm"] == "B1"
    assert b1["decision"] == "reject"
    assert b1["reject_reason"] == "核验未通过"
    assert b1["score"] == 0.1
    assert b2["arm"] == "B2"
    assert b2["decision"] == "release"
    assert b2["reverify_ok"] is False
    assert tee["arm"] == "T"
    assert tee["decision"] == "reject"
    assert tee["reject_reason"] == "核验未通过"
    assert result["C"][0]["decision"] == "release"
    assert result["C"][0]["score"] is None
    assert product_calls == []


def test_unbound_t_evidence_rejects_without_verifier_or_product_write(monkeypatch):
    product_calls = []
    monkeypatch.setattr(
        "freshlatch.evidence_bound.confirm_patch",
        lambda **kwargs: product_calls.append("confirm"),
    )
    monkeypatch.setattr(
        "freshlatch.patch_events.append_product_confirm",
        lambda **kwargs: product_calls.append("append"),
    )
    verifier = _Verifier(ok=True)
    result = _run(
        _Generator(evidence_id="doc#p9@T0"),
        verifier,
        candidates=[_candidate("c1")],
        ingested_t1={"doc#p1@T1"},
    )
    assert result["T"][0]["decision"] == "reject"
    assert result["T"][0]["reject_reason"] == "证据未绑定已入库 T1"
    assert result["T"][0]["arm"] == "T"
    assert all(call["arm"] != "T" for call in verifier.calls)
    assert product_calls == []


def test_missing_temperature_or_seed_voids_and_does_not_backfill():
    generator = _Generator()
    verifier = _Verifier()
    missing_temp = _run(
        generator,
        verifier,
        decoding=arms.Decoding(temperature=None, seed=7),
        candidates=[_candidate("c1")],
    )
    assert generator.calls == []
    assert verifier.calls == []
    assert missing_temp["C"] == []
    assert missing_temp["T"] == []
    assert {item["reason"] for item in missing_temp["voids"]} == {"温度缺省"}
    assert {item["arm"] for item in missing_temp["voids"]} == {"C", "T", "B1", "B2"}
    assert all(item["claim_id"] == "c1" for item in missing_temp["voids"])

    generator = _Generator()
    missing_seed = _run(
        generator,
        verifier,
        decoding=arms.Decoding(temperature=0, seed=None),
        candidates=[_candidate("c1")],
    )
    assert generator.calls == []
    assert missing_seed["B1"] == []
    assert {item["reason"] for item in missing_seed["voids"]} == {"种子缺省"}


def test_cost_is_zero_with_no_call_note_and_latency_is_only_generation():
    result = _run(_Generator(), _Verifier(), candidates=[_candidate("c1")])
    assert result["C"][0]["cost"] == 0
    assert result["C"][0]["latency_ms"] == 5
    assert result["cost_notes"] == {
        "C": "没有调用",
        "T": "没有调用",
        "B1": "没有调用",
        "B2": "没有调用",
    }
    assert "单价" not in Path("src/freshlatch/eval/patch_events_arms.py").read_text(encoding="utf-8")
