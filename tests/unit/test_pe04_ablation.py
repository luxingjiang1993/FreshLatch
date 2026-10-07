"""PE-04：T 上的四项消融。假生成器、假核验器，不打真实 API。"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from freshlatch import patch_events as product_ledger
from freshlatch.eval import patch_events_arms as arms
from freshlatch.eval import patch_events_metrics as metrics
from freshlatch.eval.patch_events_ablation import (
    ABLATION_ORDER,
    HYBRID_COLUMN,
    ablation_interval_report,
    primary_comparison_rows,
    run_ablations,
)
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from tests.unit.test_pe03_arms import _Generator, _Verifier, _candidate


@pytest.fixture(autouse=True)
def _unset_keys(monkeypatch):
    for key in ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def _run(generator, verifier, **kwargs):
    decoding = kwargs.pop("decoding", arms.Decoding(temperature=0, seed=0))
    ingested = kwargs.pop("ingested_t1", {"doc#p1@T1"})
    candidates = kwargs.pop("candidates", [_candidate("c1"), _candidate("c2")])
    return run_ablations(
        candidates,
        generator=generator,
        verifier=verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )


def _arm_run(generator, verifier):
    return arms.run_arms(
        [_candidate("c1"), _candidate("c2")],
        generator=generator,
        verifier=verifier,
        decoding=arms.Decoding(temperature=0, seed=0),
        ingested_t1={"doc#p1@T1"},
    )


def test_four_switches_stay_on_t_and_do_not_touch_named_streams(monkeypatch):
    product_calls = []
    monkeypatch.setattr(
        "freshlatch.evidence_bound.confirm_patch",
        lambda **kwargs: product_calls.append("confirm"),
    )
    monkeypatch.setattr(
        "freshlatch.patch_events.append_product_confirm",
        lambda **kwargs: product_calls.append("append"),
    )
    streams = metrics.named_streams()
    before = {name: rng.getstate() for name, rng in streams.items()}
    global_before = random.getstate()
    result = _run(_Generator(), _Verifier())
    assert set(ABLATION_ORDER) == {
        "no_chunk_bind",
        "no_auto_verify",
        "soft_warning",
        "retrieval_bm25",
    }
    for tag in ABLATION_ORDER:
        rows = result[tag]
        assert [row["claim_id"] for row in rows] == ["c1", "c2"]
        assert [row["arm"] for row in rows] == ["T", "T"]
        assert [row["ablation"] for row in rows] == [tag, tag]
        assert tag not in {"C", "B1", "B2"}
    bind = result["no_chunk_bind"][0]
    verify = result["no_auto_verify"][0]
    assert bind["ablation"] != verify["ablation"]
    assert bind["arm"] == verify["arm"] == "T"
    assert product_calls == []
    assert product_ledger.VALID_ARMS == frozenset({"C", "T"})
    for name, rng in streams.items():
        assert rng.getstate() == before[name]
    assert random.getstate() == global_before


def test_soft_warning_does_not_hard_reject_when_verification_fails():
    result = _run(_Generator(), _Verifier(ok=False, score=0.1, reason="核验未通过"))
    row = result["soft_warning"][0]
    assert row["arm"] == "T"
    assert row["ablation"] == "soft_warning"
    assert row["decision"] == "release"
    assert row["decision"] != "reject"
    assert row["score"] == 0.1
    assert row["reverify_ok"] is False
    assert row["reject_reason"] == "核验未通过"
    assert result["retrieval_bm25"][0]["decision"] == "reject"
    assert result["no_auto_verify"][0]["decision"] == "release"
    assert result["no_auto_verify"][0]["score"] is None


def test_chunk_bind_and_auto_verify_switches_are_independent():
    verifier = _Verifier(ok=False, score=0.2, reason="核验未通过")
    result = _run(
        _Generator(evidence_id="doc#missing@T1"),
        verifier,
        ingested_t1={"doc#p1@T1"},
    )
    unbound = result["no_chunk_bind"][0]
    assert unbound["decision"] == "reject"
    assert unbound["reject_reason"] == "核验未通过"
    assert any(call["ablation"] == "no_chunk_bind" for call in verifier.calls)
    skipped = result["no_auto_verify"][0]
    assert skipped["decision"] == "reject"
    assert skipped["reject_reason"] == "证据未绑定已入库 T1"
    assert all(call["ablation"] != "no_auto_verify" for call in verifier.calls)


def test_retrieval_bm25_keeps_production_mode_and_books_hybrid_column():
    generator = _Generator()
    result = _run(generator, _Verifier())
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    base = Path("src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    bm25_calls = [
        call
        for call in generator.calls
        if call["ablation"] == "retrieval_bm25" and call["claim_id"] == "c1"
    ]
    assert bm25_calls
    assert {call["retrieval_mode"] for call in bm25_calls} == {"bm25"}
    assert all(call["arm"] == "T" for call in bm25_calls)
    hybrid = result[HYBRID_COLUMN]
    assert [row["claim_id"] for row in hybrid] == ["c1", "c2"]
    assert all(row["arm"] == "T" and row["ablation"] == "" for row in hybrid)
    hybrid_calls = [
        call
        for call in generator.calls
        if call["ledger"] == HYBRID_COLUMN and call["claim_id"] == "c1"
    ]
    assert hybrid_calls
    assert {call["retrieval_mode"] for call in hybrid_calls} == {PRODUCTION_RETRIEVAL_MODE}
    other = [
        call
        for call in generator.calls
        if call["ablation"] in {"no_chunk_bind", "no_auto_verify", "soft_warning"}
    ]
    assert other
    assert {call["retrieval_mode"] for call in other} == {PRODUCTION_RETRIEVAL_MODE}
    source = Path("src/freshlatch/eval/patch_events_ablation.py").read_text(encoding="utf-8")
    assert "PRODUCTION_RETRIEVAL_MODE =" not in source
    assert "set_retrieval_switch" not in source


def test_hybrid_column_matches_main_t_but_is_not_that_row():
    generator = _Generator()
    verifier = _Verifier()
    abl = _run(generator, verifier)
    fresh = _Generator()
    main = _arm_run(fresh, _Verifier())
    assert all(row["arm"] == "T" and row["ablation"] == "" for row in abl[HYBRID_COLUMN])
    assert all(row["ledger"] == HYBRID_COLUMN for row in abl[HYBRID_COLUMN])
    assert all("ledger" not in row for row in main["T"])
    stripped = [
        {key: value for key, value in row.items() if key != "ledger"} for row in abl[HYBRID_COLUMN]
    ]
    assert stripped == main["T"]
    assert abl[HYBRID_COLUMN] is not main["T"]
    assert all(left is not right for left, right in zip(abl[HYBRID_COLUMN], main["T"]))


def test_primary_comparison_rejects_hybrid_column_without_drawing_streams():
    arm = _arm_run(_Generator(), _Verifier())
    abl = _run(_Generator(), _Verifier())
    streams = metrics.named_streams()
    before = {name: rng.getstate() for name, rng in streams.items()}
    mixed = primary_comparison_rows(arm, abl) + abl[HYBRID_COLUMN]
    with pytest.raises(ValueError, match="hybrid\\+rerank"):
        metrics.compare_primary(mixed, streams=streams)
    for name, rng in streams.items():
        assert rng.getstate() == before[name]


def test_ablation_rows_stay_out_of_the_three_primary_comparisons():
    generator = _Generator()
    verifier = _Verifier(ok=True, score=0.4)
    arm = _arm_run(generator, verifier)
    abl = _run(_Generator(), _Verifier(ok=True, score=0.4))
    primary = primary_comparison_rows(arm, abl)
    assert [row["arm"] for row in primary] == ["C", "C", "T", "T", "B1", "B1", "B2", "B2"]
    assert all(row["ablation"] == "" for row in primary)
    banned = [row for tag in ABLATION_ORDER for row in abl[tag]]
    banned.extend(abl[HYBRID_COLUMN])
    primary_ids = {id(row) for row in primary}
    assert all(id(row) not in primary_ids for row in banned)
    tagged = [row for tag in ABLATION_ORDER for row in abl[tag]]
    left = metrics.compare_primary(primary, streams=metrics.named_streams())
    right = metrics.compare_primary(primary + tagged, streams=metrics.named_streams())
    assert [item["name"] for item in left["comparisons"]] == ["T-C", "T-B1", "T-B2"]
    assert left["comparisons"] == right["comparisons"]
    assert left["k"] == right["k"]


def test_interval_report_rejects_hybrid_column_before_any_draw():
    arm = _arm_run(_Generator(), _Verifier())
    abl = _run(_Generator(), _Verifier())
    rng = random.Random(metrics.SEED)
    before = rng.getstate()
    with pytest.raises(ValueError, match="hybrid\\+rerank") as caught:
        ablation_interval_report(abl[HYBRID_COLUMN], abl, rng=rng)
    message = str(caught.value)
    assert abl[HYBRID_COLUMN][0]["claim_id"] in message
    assert rng.getstate() == before

    mixed = list(arm["T"]) + list(abl[HYBRID_COLUMN])
    again = rng.getstate()
    with pytest.raises(ValueError, match="hybrid\\+rerank") as mixed_caught:
        ablation_interval_report(mixed, abl, rng=rng)
    mixed_message = str(mixed_caught.value)
    assert abl[HYBRID_COLUMN][0]["claim_id"] in mixed_message
    assert "claim_id 重复" not in mixed_message
    assert rng.getstate() == again


def test_intervals_consume_only_bootstrap_ablation():
    arm = _arm_run(_Generator(), _Verifier())
    abl = _run(_Generator(), _Verifier(ok=False))
    streams = metrics.named_streams()
    coverage = streams["coverage_c"].getstate()
    bootstrap = streams["bootstrap"].getstate()
    spot = streams["spotcheck"].getstate()
    report = ablation_interval_report(
        arm["T"],
        abl,
        rng=streams["bootstrap_ablation"],
        ingested_t1={"doc#p1@T1"},
    )
    assert [item["ablation"] for item in report] == list(ABLATION_ORDER)
    assert all(item["participates"] is False for item in report)
    assert streams["coverage_c"].getstate() == coverage
    assert streams["bootstrap"].getstate() == bootstrap
    assert streams["spotcheck"].getstate() == spot
    assert streams["bootstrap_ablation"].getstate() != bootstrap


def test_missing_temperature_voids_without_backfill():
    generator = _Generator()
    verifier = _Verifier()
    result = _run(generator, verifier, decoding=arms.Decoding(temperature=None, seed=0))
    assert generator.calls == []
    assert verifier.calls == []
    for tag in (*ABLATION_ORDER, HYBRID_COLUMN):
        assert result[tag] == []
    assert result["voids"]
    assert all(item["reason"] == "温度缺省" for item in result["voids"])


def test_module_does_not_read_secrets_or_draw_the_other_streams():
    source = Path("src/freshlatch/eval/patch_events_ablation.py").read_text(encoding="utf-8")
    for token in (
        "getenv",
        "environ",
        "DASHSCOPE",
        "DEEPSEEK",
        "MOONSHOT",
        "API_KEY",
        "named_streams",
        "compare_primary",
        "coverage_c",
        "spotcheck",
        "urllib",
        "httpx",
        "requests",
        "gold.json",
    ):
        assert token not in source
    run_source = Path("src/freshlatch/eval/patch_events_ablation.py").read_text(encoding="utf-8")
    assert "bootstrap_ablation" not in run_source.split("def ablation_interval_report", 1)[0]
