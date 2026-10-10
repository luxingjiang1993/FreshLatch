"""正式比较缝。只喂夹具，不新写放行函数，不发请求。"""

from __future__ import annotations

import http.client
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_metrics import SEED, compare_primary
from freshlatch.eval import patch_events_verify as verify_mod
from freshlatch.eval.patch_events_verify import verify_edit

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_GENERATIONS = _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_N = 30


def _bytes(path: Path) -> bytes | None:
    if not path.exists():
        return None
    return path.read_bytes()


def _block_network(monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)


def _spy_env(monkeypatch) -> list[str]:
    seen: list[str] = []
    real = os.getenv

    def wrapped(key, default=None):
        name = str(key)
        seen.append(name)
        if name in _SECRET_ENV:
            raise AssertionError("不得读取密钥")
        return real(key, default)

    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(os, "getenv", wrapped)
    return seen


@pytest.fixture(autouse=True)
def _guard(monkeypatch):
    before = {
        "generations": _bytes(_GENERATIONS),
        "result": _bytes(_RESULT),
        "prereg": _bytes(_PREREG),
    }
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    # #527：夹具缝不测真实 NLI；stub 避免下模型
    def _fake_nli(premise: str, hypothesis: str) -> dict[str, float]:
        if premise == hypothesis:
            return {"entailment": 0.91, "neutral": 0.05, "contradiction": 0.04}
        return {"entailment": 0.05, "neutral": 0.10, "contradiction": 0.85}

    monkeypatch.setattr(verify_mod, "predict_xnli_probs", _fake_nli)
    yield seen
    assert _bytes(_GENERATIONS) == before["generations"]
    assert _bytes(_RESULT) == before["result"]
    assert _bytes(_PREREG) == before["prereg"]
    for key in _SECRET_ENV:
        assert key not in seen


def _candidates() -> list[dict[str, str]]:
    return [
        {
            "claim_id": f"c{index:02d}",
            "before_text": f"before-{index}",
            "evidence_id": f"doc#a{index}@T1",
            "evidence_text": f"evidence-{index}",
            "edit_type": "数值",
            "construction_gold": "坏" if index % 2 else "正确",
        }
        for index in range(_N)
    ]


def _arms(generator):
    return run_arms(
        _candidates(),
        generator=generator,
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=SEED),
    )


def test_claim_text_only_makes_compare_primary_refuse(_guard):
    def generator(request):
        claim_id = str(request["claim_id"])
        if request["arm"] == "B2" and request["phase"] == "claim":
            return {"claim_text": f"claim-only-{claim_id}", "evidence_id": request["evidence_id"]}
        if request["arm"] == "B2" and request["phase"] == "diff":
            return {"claim_text": request["claim_text"]}
        return {
            "after_text": f"rewrite-{request['arm']}-{claim_id}",
            "evidence_id": request["evidence_id"],
        }

    arms = _arms(generator)
    assert arms["B2"] == []
    rows = primary_comparison_rows(arms)
    assert [row for row in rows if row["arm"] == "B2"] == []
    with pytest.raises(ValueError, match="B2") as caught:
        compare_primary(rows)
    assert "B2" in str(caught.value)


def test_distinct_after_text_yields_three_comparisons(_guard):
    claims: dict[str, str] = {}

    def generator(request):
        claim_id = str(request["claim_id"])
        if request["arm"] == "B2" and request["phase"] == "claim":
            text = f"claim-only-{claim_id}"
            claims[claim_id] = text
            return {"claim_text": text, "evidence_id": request["evidence_id"]}
        if request["arm"] == "B2" and request["phase"] == "diff":
            return {
                "after_text": f"diff-after-{claim_id}",
                "evidence_id": request["evidence_id"],
            }
        return {
            "after_text": f"rewrite-{request['arm']}-{claim_id}",
            "evidence_id": request["evidence_id"],
        }

    arms = _arms(generator)
    rows = primary_comparison_rows(arms)
    b2_rows = [row for row in rows if row["arm"] == "B2"]
    assert len(b2_rows) == _N
    assert len(claims) == _N
    for row in b2_rows:
        assert row["after_text"] != claims[row["claim_id"]]
    report = compare_primary(rows)
    assert [item["name"] for item in report["comparisons"]] == ["T-C", "T-B1", "T-B2"]
