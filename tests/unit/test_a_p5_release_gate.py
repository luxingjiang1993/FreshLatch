"""A-P5：发车检查单的成本/延迟硬门。

注入超预算样本必须 fail，基线内必须 pass。不调用付费 API，不读夹具目录。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.sli import CHECKLIST_ITEM, RELEASE_GATE_ENV, check_release_gate
from freshlatch.sli.alert import make_window
from freshlatch.sli.release_gate import (
    CHECKLIST_GREEN,
    CHECKLIST_OFF,
    CHECKLIST_RED,
    COST_FACTOR_TEXT,
    REASON_COST,
    REASON_LATENCY,
    REASON_UNMEASURED,
    VERDICT_FAIL,
    VERDICT_PASS,
    format_release_gate,
)

REPO = Path(__file__).resolve().parents[2]
DOC = REPO / "docs" / "ops" / "发车检查单-成本延迟硬门.md"
MODULE = REPO / "src" / "freshlatch" / "sli" / "release_gate.py"


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
) -> list[dict]:
    events: list[dict] = [
        {"type": "run_meta", "mode": "online", "duration_ms": duration_ms},
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
        return events
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
    """十次生产请求。P95 下标 ceil(0.95*10)-1 = 9，时长 100 毫秒。"""
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


def _gate(**kwargs):
    defaults = {
        "baseline_cost": 10,
        "observed_cost": 10,
        "sla_e2e_p95_ms": 100,
        "e2e_p95_ms": 100,
    }
    defaults.update(kwargs)
    return check_release_gate(**defaults)


def test_cost_at_least_1_5x_baseline_fails_release() -> None:
    """成本达到基线的 1.5 倍即发车红。延迟仍在 SLA 内。"""
    decision = _gate(baseline_cost=1000, observed_cost=1500, e2e_p95_ms=100)
    assert decision.verdict == VERDICT_FAIL
    assert decision.checklist == CHECKLIST_RED
    assert decision.blocked is True
    assert decision.raw_fail is True
    assert decision.suppressed is False
    assert decision.reasons == (REASON_COST,)
    assert decision.cost_ratio == "1.5"
    assert decision.cost_factor == COST_FACTOR_TEXT
    assert decision.cost_is_quality is False
    assert decision.counted_as_pass is False
    assert decision.invents_sesoi is False
    assert decision.writes_result_y is False
    assert "成本不伪装质量" in decision.notes
    line = format_release_gate(decision)
    assert "checklist=发车红" in line
    assert "cost_is_quality=false" in line


def test_e2e_p95_over_sla_fails_release() -> None:
    """e2e P95 超过调用方 SLA 即发车红。成本仍低于 1.5 倍。"""
    decision = _gate(baseline_cost=10, observed_cost=14, sla_e2e_p95_ms=200, e2e_p95_ms=201)
    assert decision.verdict == VERDICT_FAIL
    assert decision.checklist == CHECKLIST_RED
    assert decision.blocked is True
    assert decision.reasons == (REASON_LATENCY,)
    assert decision.cost_ratio == "1.4"
    assert decision.e2e_p95_ms == 201
    assert decision.cost_is_quality is False


def test_within_baseline_and_sla_passes_release() -> None:
    """成本低于 1.5 倍且 P95 不超过 SLA 时放行。等于 SLA 仍算未超过。"""
    under = _gate(baseline_cost=1000, observed_cost=1499, sla_e2e_p95_ms=200, e2e_p95_ms=200)
    assert under.verdict == VERDICT_PASS
    assert under.checklist == CHECKLIST_GREEN
    assert under.blocked is False
    assert under.raw_fail is False
    assert under.reasons == ()
    assert under.cost_ratio == "1.499"
    assert under.counted_as_pass is False
    assert under.cost_is_quality is False
    assert "checklist=发车绿" in format_release_gate(under)

    exact_sla = _gate(e2e_p95_ms=80, sla_e2e_p95_ms=80, observed_cost=0)
    assert exact_sla.verdict == VERDICT_PASS
    assert exact_sla.checklist == CHECKLIST_GREEN
    assert exact_sla.reasons == ()


def test_both_breaches_keep_both_reasons() -> None:
    decision = _gate(baseline_cost=2, observed_cost=3, sla_e2e_p95_ms=10, e2e_p95_ms=11)
    assert decision.verdict == VERDICT_FAIL
    assert decision.reasons == (REASON_COST, REASON_LATENCY)
    assert decision.checklist == CHECKLIST_RED


def test_primary_sli_window_supplies_e2e_and_rates(tmp_path: Path) -> None:
    """合成窗走 measure_primary_sli。P95=100。两率只抄录，不改红绿。"""
    window = make_window(label="synthetic-window", trajectory_runs=_production_runs())
    held = check_release_gate(
        baseline_cost=10,
        observed_cost=10,
        sla_e2e_p95_ms=100,
        window=window,
    )
    assert held.latency_source == "window"
    assert held.e2e_p95_ms == 100
    assert held.abstain_rate == "2 / 10"
    assert held.retrieval_fallback_rate == "2 / 10"
    assert held.abstain_fallback_rate == "abstain=2 / 10; fallback=2 / 10"
    assert held.verdict == VERDICT_PASS
    assert held.checklist == CHECKLIST_GREEN
    assert held.reasons == ()

    late = check_release_gate(
        baseline_cost=10,
        observed_cost=10,
        sla_e2e_p95_ms=99,
        window=window,
    )
    assert late.verdict == VERDICT_FAIL
    assert late.reasons == (REASON_LATENCY,)
    assert late.e2e_p95_ms == 100

    costly = check_release_gate(
        baseline_cost=10,
        observed_cost=15,
        sla_e2e_p95_ms=100,
        window=window,
    )
    assert costly.verdict == VERDICT_FAIL
    assert costly.reasons == (REASON_COST,)
    assert costly.abstain_rate == "2 / 10"
    assert not any(tmp_path.iterdir())
    with pytest.raises(TypeError, match="夹具目录"):
        check_release_gate(
            baseline_cost=10,
            observed_cost=10,
            sla_e2e_p95_ms=100,
            window=tmp_path,  # type: ignore[arg-type]
        )


def test_sli_mapping_rates_do_not_invent_a_threshold() -> None:
    """主 SLI 字段直接读入。abstain 很高也不单独把检查单打红。"""
    decision = check_release_gate(
        baseline_cost=10,
        observed_cost=10,
        sla_e2e_p95_ms=50,
        sli={
            "e2e_p95_ms": 50,
            "abstain_rate": "9 / 10",
            "retrieval_fallback_rate": "8 / 10",
        },
    )
    assert decision.latency_source == "sli"
    assert decision.verdict == VERDICT_PASS
    assert decision.reasons == ()
    assert decision.abstain_rate == "9 / 10"
    assert decision.retrieval_fallback_rate == "8 / 10"
    assert decision.abstain_fallback_rate == "abstain=9 / 10; fallback=8 / 10"
    assert decision.invents_sesoi is False
    assert decision.counted_as_pass is False


def test_unmeasured_p95_fails_closed_and_is_not_zero() -> None:
    missing = check_release_gate(
        baseline_cost=10,
        observed_cost=10,
        sla_e2e_p95_ms=100,
        sli={
            "e2e_p95_ms": "样本不足",
            "abstain_rate": "样本不足",
            "retrieval_fallback_rate": "样本不足",
        },
    )
    assert missing.verdict == VERDICT_FAIL
    assert missing.checklist == CHECKLIST_RED
    assert missing.reasons == (REASON_UNMEASURED,)
    assert missing.e2e_p95_ms == "样本不足"
    assert missing.abstain_fallback_rate == "样本不足"
    assert missing.e2e_p95_ms not in {0, 0.0, "0", "0 ms"}
    rendered = format_release_gate(missing)
    assert "e2e_p95_ms=样本不足" in rendered
    assert "0 ms" not in rendered

    unmeasured = _gate(e2e_p95_ms="未计", observed_cost=20, baseline_cost=10)
    assert unmeasured.reasons == (REASON_COST, REASON_UNMEASURED)
    assert unmeasured.e2e_p95_ms == "未计"


def test_rollback_env_suppresses_block_without_clearing_the_breach() -> None:
    decision = _gate(observed_cost=15, environ={RELEASE_GATE_ENV: "off"})
    assert decision.verdict == VERDICT_FAIL
    assert decision.raw_fail is True
    assert decision.blocked is False
    assert decision.suppressed is True
    assert decision.checklist == CHECKLIST_OFF
    assert decision.cost_is_quality is False
    assert decision.checklist != CHECKLIST_GREEN

    held = _gate(environ={RELEASE_GATE_ENV: "off"})
    assert held.verdict == VERDICT_PASS
    assert held.blocked is False
    assert held.checklist == CHECKLIST_OFF

    explicit_on = _gate(observed_cost=15, environ={RELEASE_GATE_ENV: "on"})
    assert explicit_on.blocked is True
    assert explicit_on.checklist == CHECKLIST_RED

    blank = _gate(observed_cost=15, environ={RELEASE_GATE_ENV: "  "})
    assert blank.blocked is True


def test_rollback_env_reads_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RELEASE_GATE_ENV, "off")
    decision = _gate(observed_cost=15)
    assert decision.suppressed is True
    assert decision.blocked is False
    assert decision.verdict == VERDICT_FAIL


def test_caller_must_supply_baseline_and_sla() -> None:
    with pytest.raises(ValueError, match="baseline_cost"):
        _gate(baseline_cost=0)
    with pytest.raises(ValueError, match="baseline_cost"):
        _gate(baseline_cost=-1)
    with pytest.raises(ValueError, match="sla_e2e_p95_ms"):
        _gate(sla_e2e_p95_ms=0)
    with pytest.raises(ValueError, match="observed_cost"):
        _gate(observed_cost=-0.1)
    with pytest.raises(ValueError, match="之一"):
        check_release_gate(baseline_cost=10, observed_cost=10, sla_e2e_p95_ms=100)
    with pytest.raises(ValueError, match="之一"):
        _gate(sli={"e2e_p95_ms": 100})
    with pytest.raises(ValueError, match="e2e_p95_ms"):
        check_release_gate(
            baseline_cost=10,
            observed_cost=10,
            sla_e2e_p95_ms=100,
            sli={"abstain_rate": "1 / 10"},
        )
    with pytest.raises(ValueError, match="FRESHLATCH_RELEASE_GATE"):
        _gate(environ={RELEASE_GATE_ENV: "shadow"})
    with pytest.raises(ValueError, match="布尔|有限数"):
        _gate(baseline_cost=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="负"):
        _gate(e2e_p95_ms=-1)


def test_docs_checklist_item_and_rollback_env() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert CHECKLIST_ITEM in text
    assert "- [ ] " + CHECKLIST_ITEM in text
    assert "FRESHLATCH_RELEASE_GATE=off" in text
    assert "成本不伪装质量" in text
    assert "发车红" in text
    assert "1.5" in text
    assert "check_release_gate" in text
    module = MODULE.read_text(encoding="utf-8")
    assert "PRODUCTION_RETRIEVAL_MODE =" not in module
    assert "set_retrieval_switch" not in module
    assert "成本不伪装质量" in module
