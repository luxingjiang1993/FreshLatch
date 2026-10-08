"""正式 n=30 入口默认不跑。单测只注入假生成器和假核验器。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_ablation import HYBRID_COLUMN
from freshlatch.eval.patch_events_arms import ARMS, Decoding
from freshlatch.eval.patch_events_metrics import ABLATION_ORDER, N_BOOT, SEED
from freshlatch.eval import patch_events_formal as formal
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

ROOT = Path(__file__).resolve().parents[2]
_SPLIT = ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2.json"
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")


def _manifest() -> dict:
    return json.loads(_SPLIT.read_text(encoding="utf-8"))


def _generator(request):
    if request.get("phase") == "claim":
        return {"claim_text": "stub-claim", "latency_ms": 0, "cost": 0}
    return {
        "after_text": "stub-after",
        "evidence_id": request["evidence_id"],
        "latency_ms": 0,
        "cost": 0,
    }


def _verifier(_request):
    return {"ok": True, "score": 1, "reason": ""}


@pytest.fixture(autouse=True)
def _drop_keys(monkeypatch):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)


def test_default_command_does_not_construct_or_read_keys(monkeypatch, capsys):
    seen: list[str] = []

    def wrapped(key, default=None):
        seen.append(str(key))
        return None

    monkeypatch.setattr("os.getenv", wrapped)

    def blocked(*_args, **_kwargs):
        raise AssertionError("默认入口不得构造样本")

    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "run_formal", blocked)
    assert formal.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for key in _SECRET_ENV:
        assert key not in seen


def test_formal_flag_stops_on_missing_callables(monkeypatch, capsys):
    def blocked(*_args, **_kwargs):
        raise AssertionError("缺实现时不得构造样本或跑臂")

    def must_not_verify(_request):
        raise AssertionError("温度未锁定时正式入口不得调用自动核验")

    monkeypatch.setattr("freshlatch.eval.patch_events_verify.verify_edit", must_not_verify)
    monkeypatch.setattr(formal, "construct_samples", blocked)
    monkeypatch.setattr(formal, "run_arms", blocked)
    monkeypatch.setattr(formal, "run_ablations", blocked)
    monkeypatch.setattr(formal, "compare_primary", blocked)
    assert formal.main(["--formal"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    text = captured.err
    assert "没有可调用的正式生成器" in text
    assert "没有可调用的自动核验器" not in text
    assert "不把温度补成 0" in text
    assert "_generate_edit" in text
    source = Path(formal.__file__).read_text(encoding="utf-8")
    assert "LLMClient(" not in source
    assert "chat.completions" not in source
    assert DEFAULT_MODEL == "qwen-flash"
    assert MODEL_REGISTRY["default_llm"].model == "qwen-flash"
    assert MODEL_REGISTRY["default_llm"].temperature is None


def test_loader_and_run_use_formal_n30_not_pilot(monkeypatch):
    calls = {"formal": 0}

    def refuse(*_args, **_kwargs):
        calls["formal"] += 1
        raise AssertionError("不得读取旧正式集闸")

    monkeypatch.setattr("freshlatch.eval.patch_events_split.load_formal_ids", refuse)
    items = formal.load_pe_v2_formal_n30(ROOT)
    manifest = _manifest()
    n30_ids = [row["claim_id"] for row in manifest["n30"]]
    pilot_ids = {row["claim_id"] for row in manifest["pilot"]}
    n100_ids = [row["claim_id"] for row in manifest["n100"]]
    assert calls["formal"] == 0
    assert [item["claim_id"] for item in items] == n30_ids
    assert len(n30_ids) == 30
    assert set(n30_ids).isdisjoint(pilot_ids)
    assert n30_ids != n100_ids

    seen: list[dict] = []

    def generator(request):
        seen.append(dict(request))
        return _generator(request)

    report = formal.run_formal(
        items,
        generator=generator,
        verifier=_verifier,
        decoding=Decoding(temperature=0, seed=SEED),
    )
    assert report["n"] == 30
    assert report["seed"] == 20261007
    assert report["n_boot"] == 10000
    assert report["n_boot"] == N_BOOT
    assert report["model"] == "qwen-flash"
    assert report["k"] == sum(row["decision"] == "release" for row in report["arms"]["T"])
    assert [item["name"] for item in report["primary"]["comparisons"]] == ["T-C", "T-B1", "T-B2"]
    assert report["primary"]["k"] == report["k"]
    first = report["primary"]["comparisons"][0]["intervals"]["误放率"]
    assert first["kept"] + first["dropped"] == N_BOOT
    assert [row["ablation"] for row in report["ablation_intervals"]] == list(ABLATION_ORDER)
    assert all(row["participates"] is False for row in report["ablation_intervals"])
    assert HYBRID_COLUMN in report["ablations"]
    assert HYBRID_COLUMN not in {item["name"] for item in report["primary"]["comparisons"]}
    for arm in ARMS:
        assert [row["claim_id"] for row in report["arms"][arm]] == n30_ids
        assert all(row["ablation"] == "" for row in report["arms"][arm])
    modes = {call["retrieval_mode"] for call in seen if call.get("ablation") == "retrieval_bm25"}
    assert modes == {"bm25"}
    hybrid_modes = {
        call["retrieval_mode"] for call in seen if call.get("ledger") == HYBRID_COLUMN
    }
    assert hybrid_modes == {"hybrid+rerank"}
    assert {call["model"] for call in seen} == {"qwen-flash"}
    assert {call["temperature"] for call in seen} == {0}
    assert {call["seed"] for call in seen} == {SEED}
    assert all(call["arm"] != "C" or call["phase"] == "rewrite" for call in seen)
    source = Path(formal.__file__).read_text(encoding="utf-8")
    assert "load_formal_ids(" not in source
    assert "LLMClient(" not in source
    assert "chat.completions" not in source
    assert "load_dotenv" not in source
    assert "getenv" not in source
    assert "RESULT.md" not in source
