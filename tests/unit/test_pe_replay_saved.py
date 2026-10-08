"""回放已保存的生成记录。不发请求，不改 jsonl 已有的行。"""

from __future__ import annotations

import hashlib
import http.client
import inspect
import json
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_formal as formal
from freshlatch.eval.patch_events_ablation import HYBRID_COLUMN, _retrieval_mode
from freshlatch.eval.patch_events_metrics import ABLATION_ORDER, SEED
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_GENERATIONS = _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_GENERATIONS_SHA256 = "3cede5e84fa7bd0d8fdabd954263d1239bda54b6e8dfcf62f5806c70f8cb330e"
_PRIMARY_NAMES = ("T-C", "T-B1", "T-B2")
_ARM_LABELS = ("C", "T（fail-closed）", "B1", "B2")


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


def _refuse_client(*_args, **_kwargs):
    raise AssertionError("不得构造会发请求的客户端")


@pytest.fixture(autouse=True)
def _guard(monkeypatch):
    before = {
        _GENERATIONS: _bytes(_GENERATIONS),
        _RESULT: _bytes(_RESULT),
        _PREREG: _bytes(_PREREG),
    }
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr("freshlatch.llm.LLMClient", _refuse_client)
    monkeypatch.setattr(formal, "live_chat", _refuse_client)
    monkeypatch.setattr(formal, "main", _refuse_client)
    monkeypatch.setattr(formal, "append_sent", _refuse_client)
    yield seen
    for path, blob in before.items():
        assert _bytes(path) == blob
    for key in _SECRET_ENV:
        assert key not in seen


def _saved_rows() -> list[dict]:
    raw = _GENERATIONS.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _GENERATIONS_SHA256
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    assert len(rows) == 120
    return rows


def _text_index(rows: list[dict], arm: str, phase: str, field: str) -> dict[str, str]:
    found = {
        str(item["claim_id"]): str(item["text"])
        for item in rows
        if item["arm"] == arm and item["phase"] == phase and item["output_field"] == field
    }
    assert len(found) == 30
    return found


def _assert_unrecorded(value: object) -> None:
    if isinstance(value, dict):
        assert "latency_ms" not in value
        assert "cost" not in value
        for item in value.values():
            if isinstance(item, str):
                assert "没有调用" not in item
            else:
                _assert_unrecorded(item)
    elif isinstance(value, list):
        for item in value:
            _assert_unrecorded(item)


def _result_cells() -> None:
    text = _RESULT.read_text(encoding="utf-8")
    assert "没有调用" not in text
    arm_rows = []
    false_accept = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("|") or not cells:
            continue
        if cells[0] in _ARM_LABELS:
            arm_rows.append(cells)
        if len(cells) >= 2 and cells[1] == "false-accept rate" and cells[0].startswith("T 对 "):
            false_accept.append(cells)
    assert [row[0] for row in arm_rows] == list(_ARM_LABELS)
    for row in arm_rows:
        assert row[-3:] == ["未填", "未填", "未填"]
        assert "0" not in row[-3:]
    assert [row[0] for row in false_accept] == ["T 对 C", "T 对 B1", "T 对 B2"]
    for row in false_accept:
        assert row[2:] == ["未填", "未填", "未填", "未填"]


def test_saved_file_hash_rejects_any_edited_line():
    raw = _GENERATIONS.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _GENERATIONS_SHA256
    assert raw.count(b"\n") == 120


def test_field_routing_keeps_claim_text_out_of_after_text():
    claim = formal._from_saved(
        {"output_field": "claim_text", "text": "只属于主张"},
        {"phase": "claim", "evidence_id": "doc#a@T1"},
    )
    rewrite = formal._from_saved(
        {"output_field": "after_text", "text": "只属于改写"},
        {"phase": "rewrite", "evidence_id": "doc#a@T1"},
    )
    diff = formal._from_saved(
        {"output_field": "after_text", "text": "只属于差异"},
        {"phase": "diff", "evidence_id": "doc#a@T1"},
    )
    misplaced = formal._from_saved(
        {"output_field": "claim_text", "text": "只属于主张"},
        {"phase": "diff", "evidence_id": "doc#a@T1"},
    )
    assert claim == {"claim_text": "只属于主张"}
    assert "after_text" not in claim
    assert rewrite["after_text"] == "只属于改写"
    assert "claim_text" not in rewrite
    assert diff["after_text"] == "只属于差异"
    assert "claim_text" not in diff
    assert misplaced == {"void": True}
    assert "after_text" not in misplaced


def test_replay_current_rows_refuses_without_b2_after_text(monkeypatch):
    rows = _saved_rows()
    assert all("latency_ms" not in item and "cost" not in item and "seed" not in item for item in rows)
    counts = {(item["arm"], item["phase"], item["output_field"]) for item in rows}
    assert counts == {
        ("C", "rewrite", "after_text"),
        ("T", "rewrite", "after_text"),
        ("B1", "rewrite", "after_text"),
        ("B2", "claim", "claim_text"),
    }
    saved = {
        "C": _text_index(rows, "C", "rewrite", "after_text"),
        "T": _text_index(rows, "T", "rewrite", "after_text"),
        "B1": _text_index(rows, "B1", "rewrite", "after_text"),
    }
    calls: list[str] = []
    real_compare = formal.compare_primary
    real_ablate = formal.run_ablations

    def compare_wrapped(*args, **kwargs):
        calls.append("compare_primary")
        return real_compare(*args, **kwargs)

    def ablate_wrapped(*args, **kwargs):
        calls.append("run_ablations")
        return real_ablate(*args, **kwargs)

    monkeypatch.setattr(formal, "compare_primary", compare_wrapped)
    monkeypatch.setattr(formal, "run_ablations", ablate_wrapped)
    monkeypatch.setattr(formal, "ablation_interval_report", _refuse_client)

    report = formal.replay_saved_generations(formal.load_pe_v2_formal_n30(), rows)

    assert calls == ["compare_primary", "run_ablations"]
    assert report["comparisons"] is None
    assert report["primary_error"] is not None
    assert "B2" in report["primary_error"]
    assert report["arms"]["B2"] == []
    b2_voids = [item for item in report["voids"] if item["arm"] == "B2"]
    assert len(b2_voids) == 30
    assert {item["reason"] for item in b2_voids} == {"生成失败"}
    assert [item for item in report["voids"] if item["reason"] in {"种子缺省", "温度缺省"}] == []
    for arm in ("C", "T", "B1"):
        played = report["arms"][arm]
        assert len(played) == 30
        assert [item["after_text"] for item in played] == [saved[arm][item["claim_id"]] for item in played]
    _assert_unrecorded(report)
    _result_cells()


def test_ablations_reuse_saved_t_text_and_leave_production_retrieval(monkeypatch):
    rows = _saved_rows()
    saved_t = _text_index(rows, "T", "rewrite", "after_text")
    monkeypatch.setattr(formal, "ablation_interval_report", _refuse_client)
    report = formal.replay_saved_generations(
        formal.load_pe_v2_formal_n30(),
        rows,
    )
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert PRODUCTION_RETRIEVAL_MODE != "bm25"
    assert _retrieval_mode("retrieval_bm25") == "bm25"
    assert _retrieval_mode(HYBRID_COLUMN) == PRODUCTION_RETRIEVAL_MODE
    names = [] if report["comparisons"] is None else [item["name"] for item in report["comparisons"]]
    assert names == [] or names == list(_PRIMARY_NAMES)
    assert all(HYBRID_COLUMN not in name for name in (*names, *_PRIMARY_NAMES))
    assert "B2" in report["primary_error"]
    for column in (*ABLATION_ORDER, HYBRID_COLUMN):
        played = report["ablations"][column]
        assert len(played) == 30
        assert [item["after_text"] for item in played] == [saved_t[item["claim_id"]] for item in played]
        assert {item["arm"] for item in played} == {"T"}
    assert "retrieval_bm25" in report["ablations"]
    assert HYBRID_COLUMN in report["ablations"]
    _assert_unrecorded(report)
    _result_cells()


def test_replay_comment_does_not_say_the_saved_request_carried_a_seed():
    source = inspect.getsource(formal.replay_saved_generations)
    assert "没有发出种子" in source
    for banned in ("带了种子", "发出了种子", "sent with a seed", "included a seed"):
        assert banned not in source
    assert SEED == 20261007
    replay_file = Path(formal.__file__).read_text(encoding="utf-8")
    main_src = replay_file.split("def main(", 1)[1].split("\nif __name__", 1)[0]
    assert "replay_saved_generations" not in main_src
    assert "带了种子" not in replay_file
    assert "发出了种子" not in replay_file
    assert "RESULT.md" not in replay_file
