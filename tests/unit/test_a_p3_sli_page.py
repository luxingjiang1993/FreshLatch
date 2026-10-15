"""A-P3：主 SLI 窗口 + multiwindow burn-rate page。

合成窗口即可。不读夹具目录，不联网，不发明 SESOI。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from freshlatch.sli.alert import (
    NOT_DONE,
    ONCALL_COVERAGE,
    ONCALL_HOURS,
    ONCALL_ROLE,
    PAGE_SINK_ENV,
    PROTOCOL_ONLY_NOT_DONE,
    PagePathError,
    RecordingSender,
    burn_windows_from_canary_events,
    canary_sample_bad,
    dispatch_page,
    evaluate_window,
    make_window,
    measure_primary_sli,
    multiwindow_breach,
    page_path_status,
)

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "ops" / "主SLI与burn-rate-page.md"
MODULE = REPO / "src" / "freshlatch" / "sli" / "alert.py"
NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def _span(claim_id: str) -> dict:
    return {
        "type": "claim_span",
        "claim_id": claim_id,
        "claim_text": "专业版定价 299 元/席/月。",
        "status": "fresh",
        "unsupported": False,
        "support": [
            {
                "role": "support",
                "evidence_id": "memo#p1@T1",
                "sentence_id": "s0",
                "text": "专业版定价 299 元/席/月。",
            }
        ],
        "oppose": [],
    }


def _run(
    *,
    claim_id: str,
    duration_ms: int,
    retrieval_mode: str,
    rerank_mode: str,
    abstain: bool,
    mode: str = "online",
) -> list[dict]:
    events: list[dict] = [
        {"type": "run_meta", "mode": mode, "duration_ms": duration_ms},
        {
            "type": "retrieve",
            "query": "q",
            "retrieval_mode": retrieval_mode,
            "rerank_mode": rerank_mode,
            "hits": 1,
            "used": 1,
        },
    ]
    if abstain:
        events.append(
            {
                "type": "claim_final",
                "claim_id": claim_id,
                "status": "unknown",
                "reason": "",
                "evidence_ids": [],
            }
        )
    else:
        events.append(
            {
                "type": "claim_final",
                "claim_id": claim_id,
                "status": "fresh",
                "reason": "",
                "evidence_ids": ["memo#p1@T1"],
            }
        )
        events.append(_span(claim_id))
    return events


def _production_runs() -> list[list[dict]]:
    """十次生产请求。P95 下标 ceil(0.95*10)-1 = 9，取 100。"""
    runs: list[list[dict]] = []
    for index in range(10):
        fallback = index < 2
        runs.append(
            _run(
                claim_id=f"c{index}",
                duration_ms=(index + 1) * 10,
                retrieval_mode="bm25_fallback" if fallback else "hybrid+rerank",
                rerank_mode="none" if fallback else "bge-reranker-base",
                abstain=fallback,
            )
        )
    return runs


def _canary(
    *,
    ts: datetime,
    failed: bool | None,
    value: float | None = None,
    halt_above: float | None = None,
    reason: str = "active_promote",
    trajectory_events: list[dict] | None = None,
) -> dict:
    event: dict = {
        "event": "canary_event",
        "ts": ts.isoformat(),
        "mode": "active",
        "canary_halted": bool(failed),
        "promoted": failed is False,
        "main_arm": "main",
        "canary_arm": "candidate",
        "serving_arm": "main",
        "reason": reason,
        "metric": "error",
        "value": value,
        "halt_above": halt_above,
        "failed": failed,
        "latched": False,
    }
    if trajectory_events is not None:
        event["trajectory_events"] = trajectory_events
    return event


def _assert_primary(row: dict) -> None:
    assert row["e2e_p95_ms"] == 100
    assert row["abstain_rate"] == "2 / 10"
    assert row["retrieval_fallback_rate"] == "2 / 10"
    assert row["abstain_fallback_rate"] == "abstain=2 / 10; fallback=2 / 10"
    assert row["N_request_ok"] == 10
    assert row["fallback_n"] == 2
    assert row["counted_as_pass"] is False
    assert row["invents_sesoi"] is False
    assert row["writes_result_y"] is False
    assert "不发明 SESOI" in row["notes"]
    assert "canary_event 来自 A-P1" in row["notes"]


def test_primary_sli_from_synthetic_window_not_a_directory(tmp_path: Path) -> None:
    """轨迹事件与 canary_event 都在内存窗里。目录不是入口。"""
    runs = _production_runs()
    runs.append(
        _run(
            claim_id="gold",
            duration_ms=99999,
            retrieval_mode="bm25_fallback",
            rerank_mode="lexical_fallback",
            abstain=True,
            mode="eval",
        )
    )
    recent = NOW - timedelta(minutes=1)
    window = make_window(
        label="synthetic-window",
        trajectory_runs=runs,
        canary_events=[
            _canary(ts=recent, failed=True, reason="breach_halt"),
            _canary(ts=recent, failed=False, value=0.1, halt_above=1.0),
            _canary(ts=recent, failed=None, reason="mode_off"),
        ],
    )
    row = measure_primary_sli(window)
    _assert_primary(row)
    assert row["window"] == "synthetic-window"
    assert row["sources"] == "trajectory+canary_event"
    assert row["canary_event_n"] == 3
    assert row["canary_sample_n"] == 2
    assert row["canary_bad_n"] == 1
    assert not any(tmp_path.iterdir())
    with pytest.raises(TypeError, match="夹具目录"):
        measure_primary_sli(tmp_path)  # type: ignore[arg-type]


def test_canary_event_window_lands_same_sli_without_trajectory_arg() -> None:
    """canary_event 可附带轨迹。不另给 trajectory_runs，也不读目录。"""
    events = []
    for index, run in enumerate(_production_runs()):
        events.append(
            _canary(
                ts=NOW - timedelta(seconds=index + 1),
                failed=index == 0,
                reason="breach_halt" if index == 0 else "shadow_observe",
                trajectory_events=run,
            )
        )
    window = make_window(label="canary-window", canary_events=events)
    row = measure_primary_sli(window)
    _assert_primary(row)
    assert row["sources"] == "trajectory+canary_event"
    assert row["canary_sample_n"] == 10
    assert row["canary_bad_n"] == 1


def test_injected_page_breach_records_webhook_sender() -> None:
    sink = RecordingSender()
    decision = multiwindow_breach(
        {"5m": (100, 100), "1h": (100, 100)},
        objective=0.01,
    )
    assert decision.page is True
    assert decision.ticket is False
    assert decision.page_rules == ("page:1h+5m>14.4",)
    actions = dispatch_page(
        {"5m": (100, 100), "1h": (100, 100)},
        objective=0.01,
        sink=sink,
        channel="webhook",
        environ={},
    )
    assert len(actions) == 1
    assert actions[0]["kind"] == "page"
    assert actions[0]["channel"] == "webhook"
    assert actions[0]["sent"] is True
    assert actions[0]["recorded"] is True
    assert actions[0]["oncall_role"] == ONCALL_ROLE
    assert actions[0]["objective_is_sesoi"] is False
    assert sink.payloads == [actions[0]]


def test_email_sender_is_mockable() -> None:
    seen: list[str] = []

    class EmailSink:
        def send(self, payload: dict) -> None:
            seen.append(payload["channel"])

    actions = dispatch_page(
        {"30m": (80, 100), "6h": (80, 100)},
        objective=0.1,
        sink=EmailSink(),
        channel="email",
        environ={},
    )
    assert actions[0]["kind"] == "page"
    assert actions[0]["rules"] == ["page:6h+30m>6"]
    assert seen == ["email"]


def test_ticket_breach_does_not_call_page_sender() -> None:
    sink = RecordingSender()
    windows = {
        "5m": (20, 100),
        "30m": (20, 100),
        "1h": (20, 100),
        "2h": (40, 100),
        "6h": (0, 100),
        "1d": (40, 100),
        "3d": (0, 100),
    }
    decision = multiwindow_breach(windows, objective=0.1)
    assert decision.page is False
    assert decision.ticket_rules == ("ticket:1d+2h>3",)
    actions = dispatch_page(windows, objective=0.1, sink=sink, environ={})
    assert len(actions) == 1
    assert actions[0]["kind"] == "ticket"
    assert actions[0]["respond_by"] == "next_business_day"
    assert actions[0]["sent"] is False
    assert sink.payloads == []


def test_slow_ticket_rule_and_recovered_short_window() -> None:
    slow = {name: (20, 100) for name in ("5m", "30m", "1h", "2h", "6h", "1d", "3d")}
    decision = multiwindow_breach(slow, objective=0.1)
    assert decision.page is False
    assert decision.ticket_rules == ("ticket:3d+6h>1",)
    sink = RecordingSender()
    actions = dispatch_page(
        {"1h": (100, 100), "5m": (0, 100)},
        objective=0.01,
        sink=sink,
        environ={},
    )
    assert actions == []
    assert sink.payloads == []
    assert multiwindow_breach({"1h": (100, 100)}, objective=0.01).page is False
    assert multiwindow_breach({"5m": (0, 0), "1h": (100, 100)}, objective=0.01).page is False


def test_canary_events_drive_page_and_next_day_ticket() -> None:
    sink = RecordingSender()
    recent = NOW - timedelta(minutes=1)
    events = [
        _canary(ts=recent, failed=True, reason="breach_halt")
        for _index in range(10)
    ]
    events.append(_canary(ts=recent, failed=None, reason="mode_off"))
    events.append(
        _canary(
            ts=NOW - timedelta(hours=2),
            failed=False,
            value=2.0,
            halt_above=1.0,
            reason="breach_halt",
        )
    )
    window = make_window(label="canary-burn", canary_events=events)
    result = evaluate_window(
        window,
        objective=0.01,
        sink=sink,
        now=NOW,
        channel="webhook",
        environ={},
    )
    assert result["sli"]["e2e_p95_ms"] == "样本不足"
    assert result["sli"]["abstain_fallback_rate"] == "样本不足"
    assert result["sli"]["sources"] == "canary_event"
    assert result["burn_windows"]["5m"] == (10, 10)
    assert result["burn_windows"]["1h"] == (10, 10)
    kinds = [item["kind"] for item in result["actions"]]
    assert kinds == ["page", "ticket"]
    assert result["actions"][1]["respond_by"] == "next_business_day"
    assert len(sink.payloads) == 1
    assert sink.payloads[0]["kind"] == "page"
    assert sink.payloads[0]["e2e_p95_ms"] == "样本不足"
    assert canary_sample_bad(events[-2]) is None
    assert canary_sample_bad(events[-1]) is True


def test_env_off_records_page_without_sending() -> None:
    sink = RecordingSender()
    actions = dispatch_page(
        {"5m": (100, 100), "1h": (100, 100)},
        objective=0.01,
        sink=sink,
        environ={PAGE_SINK_ENV: "off"},
    )
    assert actions[0]["kind"] == "page"
    assert actions[0]["sent"] is False
    assert actions[0]["suppressed"] is True
    assert actions[0]["recorded"] is True
    assert sink.payloads == []


def test_protocol_only_page_path_is_not_done() -> None:
    assert page_path_status(None) == NOT_DONE
    assert page_path_status(dispatch_page) == "callable"
    assert callable(dispatch_page)
    with pytest.raises(PagePathError, match=PROTOCOL_ONLY_NOT_DONE):
        dispatch_page(
            {"5m": (100, 100), "1h": (100, 100)},
            objective=0.01,
            sink=None,
            environ={},
        )
    with pytest.raises(TypeError):
        multiwindow_breach({"5m": (1, 1), "1h": (1, 1)})  # type: ignore[call-arg]
    text = MODULE.read_text(encoding="utf-8")
    assert "不发明 SESOI" in text
    assert "objective: float =" not in text
    assert "SESOI =" not in text


def test_docs_name_oncall_page_ticket_and_canary_event() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert ONCALL_ROLE in text
    assert ONCALL_COVERAGE in text
    assert ONCALL_HOURS in text
    assert "page" in text and "ticket" in text
    assert "次日" in text
    assert "canary_event" in text
    assert "sample_breached" in text
    assert "src/freshlatch/canary.py" in text
    assert PROTOCOL_ONLY_NOT_DONE in text
    assert f"没有可调用的 page 路径 = {NOT_DONE}" in text
    assert "page_path_status(None)" in text
    assert "dispatch_page" in text
    assert "夹具目录" in text
    assert "不发明 SESOI" in text
