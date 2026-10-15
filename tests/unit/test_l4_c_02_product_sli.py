"""L4-C-02：product SLI 与离线质量闸 stdout 分列。

观测行不是 RESULT-Y，不是 PREREG floors。不把在线率写进注册通过线。
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from freshlatch.eval.product_sli import (
    MIN_JUDGED_FOR_RATE,
    OBSERVATION_MARK,
    PRODUCT_SLI_MANIFEST,
    aggregate_product_sli,
    classify_claim_events,
    format_product_sli_rows,
)
from freshlatch.eval.quality_gate import run_quality_gate

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "src" / "freshlatch" / "eval" / "product_sli.py"
PROTOCOL = REPO / "docs" / "ops" / "抽检-主张忠实.md"
INDEX = REPO / "docs" / "ops" / "生产观测phase2-索引.md"
PREREG = REPO / "docs" / "evidence" / "quality-gate" / "PREREG.md"
LOOP = REPO / "src" / "freshlatch" / "roles" / "loop.py"
GATE_SOURCE = REPO / "src" / "freshlatch" / "eval" / "quality_gate.py"

GATE_METRIC_IDS = (
    "G1-should-refuse-accuracy",
    "A1-citation-recall",
    "A1-citation-precision",
    "T1-new-over-old-accuracy",
    "R1-recall@10",
    "R1-mrr@10",
)
_GATE_VALUE = re.compile(
    r"metric id=(?P<row>\S+) status=\S+ value=(?P<value>\S+)"
)
_PHOENIX_NAME = re.compile(r"Phoenix-[A-Za-z]")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _jsonl(directory: Path, name: str, events: list[dict]) -> None:
    body = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
    (directory / name).write_text(body + "\n", encoding="utf-8")


def _support_span(claim_id: str, status: str = "fresh") -> dict:
    return {
        "type": "claim_span",
        "claim_id": claim_id,
        "claim_text": "专业版定价 299 元/席/月。",
        "status": status,
        "sentence_scheme": "sentence_id",
        "unsupported": False,
        "support": [
            {
                "role": "support",
                "evidence_id": "memo#p1@T1",
                "sentence_id": "s0",
                "anchor": "memo#p1@T1#s0",
                "text": "专业版定价 299 元/席/月。",
            }
        ],
        "oppose": [],
    }


def _final(claim_id: str, status: str, evidence_ids: list[str] | None = None) -> dict:
    return {
        "type": "claim_final",
        "claim_id": claim_id,
        "statement": "主张",
        "status": status,
        "reason": "",
        "evidence_ids": list(evidence_ids or []),
        "auditor_verdict": None,
    }


def _judgment(claim_id: str, status: str, evidence_ids: list[str]) -> dict:
    return {
        "type": "cite_registry_judgment",
        "claim_id": claim_id,
        "status": status,
        "evidence_ids": evidence_ids,
    }


def _refusal(claim_id: str) -> dict:
    return {
        "type": "cite_registry_refusal",
        "claim_id": claim_id,
        "tool": "reverify_claim",
        "reason_code": "cite_outside_registry",
    }


def _abstain_step(claim_id: str) -> dict:
    return {
        "type": "lead_step",
        "claim_id": claim_id,
        "step": 2,
        "tool": "__verify_abstain__",
        "args": {},
        "result": {"abstain": True, "evidence_ids": []},
        "evidence_ids": [],
    }


def _window(tmp_path: Path, claims: list[tuple[str, list[dict]]], *, mode: str = "online") -> None:
    events: list[dict] = [{"type": "run_meta", "mode": mode}]
    for _claim_id, claim_events in claims:
        events.extend(claim_events)
    _jsonl(tmp_path, "run-online.jsonl", events)


def _row(rows: list[dict], metric: str, kind: str = "weekly") -> dict:
    matched = [row for row in rows if row["metric"] == metric and row["kind"] == kind]
    assert len(matched) == 1
    return matched[0]


def test_fixture_window_emits_product_sli_rows(tmp_path: Path) -> None:
    """夹具窗含 claim / citation。周报行标成 product SLI，并带 observation 句。"""
    claims: list[tuple[str, list[dict]]] = []
    for index in range(8):
        claim_id = f"c{index:02d}"
        claims.append((claim_id, [_final(claim_id, "fresh"), _support_span(claim_id)]))
    for index in range(8, 10):
        claim_id = f"c{index:02d}"
        claims.append((claim_id, [_final(claim_id, "stale"), _refusal(claim_id)]))
    for index in range(10, 13):
        claim_id = f"c{index:02d}"
        claims.append((claim_id, [_final(claim_id, "unknown", ["memo#p1@T1"])]))
    claims.append(("c13", [_final("c13", "fresh")]))
    _window(tmp_path, claims)

    rows = aggregate_product_sli(tmp_path, window="2026-10-08/2026-10-14 Asia/Shanghai")
    grounded = _row(rows, "groundedness")
    abstain = _row(rows, "abstain")
    missing = _row(rows, "missing_score", kind="alert")

    assert grounded["layer"] == "product SLI"
    assert abstain["layer"] == "product SLI"
    assert missing["layer"] == "product SLI"
    assert grounded["value"] == "8 / 10"
    assert grounded["numerator"] == 8
    assert grounded["denominator"] == 10
    assert abstain["value"] == "3 / 14"
    assert abstain["numerator"] == 3
    assert abstain["denominator"] == 14
    assert missing["value"] == "缺分"
    assert missing["numerator"] == 1
    assert grounded["sample_rate"] == "14 / 14"
    assert grounded["counted_as_pass"] is False
    assert grounded["writes_prereg"] is False
    assert OBSERVATION_MARK in grounded["notes"]
    assert "RESULT-Y" in grounded["notes"] and "PREREG floors" in grounded["notes"]

    text = format_product_sli_rows(rows)
    assert "layer=product SLI" in text
    assert "counted_as_pass=false" in text
    assert "writes_prereg=false" in text
    assert "counted_as_pass=true" not in text
    assert "status=pass" not in text
    assert "0 / 0" not in text
    for row in rows:
        assert row["value"] not in {"0", "0.0", "0%", "0 / 0"}


def test_small_window_is_insufficient_not_zero(tmp_path: Path) -> None:
    claims = [
        ("a", [_final("a", "fresh"), _support_span("a")]),
        ("b", [_final("b", "fresh"), _support_span("b")]),
        ("c", [_final("c", "unknown")]),
    ]
    _window(tmp_path, claims)
    rows = aggregate_product_sli(tmp_path, window="w")
    grounded = _row(rows, "groundedness")
    abstain = _row(rows, "abstain")
    assert grounded["value"] == "样本不足"
    assert grounded["numerator"] == 2
    assert grounded["denominator"] == 2
    assert grounded["denominator"] < MIN_JUDGED_FOR_RATE
    assert abstain["value"] == "样本不足"
    assert abstain["numerator"] == 1
    assert grounded["value"] not in {"0", "0.0", "0%", "0 / 0"}
    assert all(row["layer"] == "product SLI" for row in rows)
    assert not any(row["metric"] == "missing_score" for row in rows)


def test_docs_state_observation_is_not_result_y_or_floors() -> None:
    protocol = PROTOCOL.read_text(encoding="utf-8")
    index = INDEX.read_text(encoding="utf-8")
    for text in (protocol, index):
        assert "product SLI" in text
        assert "observation ≠ RESULT-Y ≠ PREREG floors" in text
        assert "不回写 PREREG" in text or "不回写 `PREREG`" in text or "不回写 PREREG" in text
    assert "src/freshlatch/eval/product_sli.py" in protocol
    assert "src/freshlatch/eval/product_sli.py" in index
    assert not _PHOENIX_NAME.search(protocol)
    assert not _PHOENIX_NAME.search(index)
    module = MODULE.read_text(encoding="utf-8")
    assert "Phoenix-" not in module
    assert "observation ≠ RESULT-Y ≠ PREREG floors" in module


def test_output_shares_no_gate_pass_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """product SLI 文本不得含质量闸 G1/A1/T1/R1 的 value= 通过线数字。"""
    claims = [
        (f"g{index:02d}", [_final(f"g{index:02d}", "fresh"), _support_span(f"g{index:02d}")])
        for index in range(10)
    ]
    claims.append(("miss", [_final("miss", "stale")]))
    _window(tmp_path, claims)
    before = _sha256(PREREG)
    rows = aggregate_product_sli(
        tmp_path,
        window="obs-window",
        prior_groundedness="8 / 10",
    )
    after = _sha256(PREREG)
    assert before == after
    rendered = format_product_sli_rows(rows)
    assert _row(rows, "drift_watch", kind="alert")["value"] == "10 / 10"
    assert "8 / 10" in _row(rows, "drift_watch", kind="alert")["notes"]

    code = run_quality_gate(offline=True, prereg=str(PREREG))
    captured = capsys.readouterr()
    assert code == 0, captured.err
    gate_values: dict[str, str] = {}
    for line in captured.out.splitlines():
        matched = _GATE_VALUE.search(line)
        if matched and matched.group("row") in GATE_METRIC_IDS:
            gate_values[matched.group("row")] = matched.group("value")
    assert set(gate_values) == set(GATE_METRIC_IDS)
    for row_id, token in gate_values.items():
        assert token not in rendered, row_id
        assert f"value={token}" not in rendered
        assert row_id not in rendered
    assert "counted_as_pass=true" not in captured.out
    assert "counted_as_pass=false" in rendered
    assert PRODUCT_SLI_MANIFEST["writes_prereg"] is False
    assert PRODUCT_SLI_MANIFEST["counted_as_pass"] is False


def test_same_prior_and_non_rate_prior_do_not_alert(tmp_path: Path) -> None:
    claims = [
        (f"g{index:02d}", [_final(f"g{index:02d}", "fresh"), _judgment(f"g{index:02d}", "fresh", ["memo#p1@T1"])])
        for index in range(10)
    ]
    _window(tmp_path, claims)
    same = aggregate_product_sli(tmp_path, prior_groundedness="10 / 10")
    assert not any(row["metric"] == "drift_watch" for row in same)
    foreign = aggregate_product_sli(tmp_path, prior_groundedness="0.9732142857142857")
    rendered = format_product_sli_rows(foreign)
    assert "0.9732142857142857" not in rendered
    assert not any(row["metric"] == "drift_watch" for row in foreign)
    withheld = aggregate_product_sli(tmp_path, prior_groundedness="样本不足")
    assert not any(row["metric"] == "drift_watch" for row in withheld)


def test_abstain_beats_supportive_citation() -> None:
    events = [
        _final("c", "fresh", ["memo#p1@T1"]),
        _support_span("c"),
        {
            "type": "lead_loop_end",
            "claim_id": "c",
            "abstained": True,
            "finished": True,
        },
    ]
    assert classify_claim_events(events) == "abstain"


def test_claim_final_beats_earlier_unknown_result() -> None:
    events = [
        {"type": "claim_result", "claim_id": "c", "status": "unknown"},
        _final("c", "fresh", ["memo#p1@T1"]),
        _support_span("c"),
    ]
    assert classify_claim_events(events) == "grounded"


def test_span_unsupported_is_ungrounded_even_with_ids() -> None:
    events = [
        _final("c", "stale"),
        _judgment("c", "stale", ["memo#p1@T1"]),
        {
            "type": "claim_span",
            "claim_id": "c",
            "status": "stale",
            "unsupported": True,
            "support": [],
            "oppose": [],
        },
    ]
    assert classify_claim_events(events) == "ungrounded"


def test_refusal_only_is_ungrounded() -> None:
    assert classify_claim_events([_final("c", "stale"), _refusal("c")]) == "ungrounded"


def test_unknown_citation_without_terminal_is_abstain() -> None:
    assert classify_claim_events([_judgment("c", "unknown", ["memo#p1@T1"])]) == "abstain"


def test_verify_abstain_tool_and_hardening_are_abstain() -> None:
    assert classify_claim_events([_abstain_step("c")]) == "abstain"
    assert classify_claim_events(
        [{"type": "agent_hardening_error", "claim_id": "c", "status": "unknown"}]
    ) == "abstain"


def test_eval_mode_and_sample_every(tmp_path: Path) -> None:
    _window(
        tmp_path,
        [(f"e{index}", [_final(f"e{index}", "fresh"), _support_span(f"e{index}")]) for index in range(6)],
        mode="eval",
    )
    prod = [
        (f"p{index}", [_final(f"p{index}", "fresh"), _support_span(f"p{index}")])
        for index in range(4)
    ]
    events: list[dict] = [{"type": "run_meta", "mode": "online"}]
    for _claim_id, claim_events in prod:
        events.extend(claim_events)
    _jsonl(tmp_path, "prod.jsonl", events)
    rows = aggregate_product_sli(tmp_path, sample_every=2, window="stride")
    grounded = _row(rows, "groundedness")
    assert grounded["sample_rate"] == "2 / 4"
    assert grounded["numerator"] == 2
    assert grounded["denominator"] == 2
    assert grounded["value"] == "样本不足"


def test_idempotent_and_does_not_write(tmp_path: Path) -> None:
    _window(tmp_path, [("c", [_final("c", "fresh"), _support_span("c")])])
    before = sorted(path.name for path in tmp_path.iterdir())
    first = aggregate_product_sli(tmp_path, window="w")
    second = aggregate_product_sli(tmp_path, window="w")
    assert first == second
    assert sorted(path.name for path in tmp_path.iterdir()) == before


def test_bad_inputs(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        aggregate_product_sli(tmp_path / "missing")
    (tmp_path / "bad.jsonl").write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        aggregate_product_sli(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    rows = aggregate_product_sli(empty, window="empty")
    assert _row(rows, "groundedness")["value"] == "样本不足"
    assert _row(rows, "groundedness")["sample_rate"] == "样本不足"
    assert _row(rows, "abstain")["denominator"] == 0
    with pytest.raises(ValueError):
        aggregate_product_sli(empty, sample_every=0)
    with pytest.raises(ValueError):
        aggregate_product_sli(empty, sample_every=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        aggregate_product_sli(empty, sample_every=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        classify_claim_events([])
    with pytest.raises(ValueError):
        classify_claim_events([{"type": "retrieve", "claim_id": "c"}])


def test_json_events_wrapper(tmp_path: Path) -> None:
    payload = {
        "events": [
            {"type": "run_meta", "mode": "online"},
            _final("c", "fresh"),
            _judgment("c", "fresh", ["memo#p9@T1"]),
        ]
    }
    (tmp_path / "only.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    rows = aggregate_product_sli(tmp_path, window="json")
    assert _row(rows, "groundedness")["numerator"] == 1
    assert _row(rows, "abstain")["numerator"] == 0


def test_module_stays_out_of_registration_and_run_loop() -> None:
    module = MODULE.read_text(encoding="utf-8")
    assert "counted_as_pass=true" not in module
    assert "status=pass" not in module
    assert "langgraph" not in module
    assert "0.9732142857142857" not in module
    assert "0.8381855867346939" not in module
    assert "quality_gate" not in module
    gate = GATE_SOURCE.read_text(encoding="utf-8")
    assert "product_sli" not in gate
    loop = LOOP.read_text(encoding="utf-8")
    assert "本模块不 import langgraph" in loop
    for line in loop.splitlines():
        stripped = line.strip()
        assert not stripped.startswith("import langgraph")
        assert not stripped.startswith("from langgraph")
    assert PRODUCT_SLI_MANIFEST["counted_in_registered_g1_a1_t1_r1"] is False
    assert PRODUCT_SLI_MANIFEST["writes_result_y"] is False
    assert PRODUCT_SLI_MANIFEST["invents_sesoi"] is False
