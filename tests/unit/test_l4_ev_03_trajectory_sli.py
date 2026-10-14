"""L4-EV-03：轨迹目录聚合成周报同一行。不计注册 G1/A1/T1/R1。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.trajectory_sli import SLI_MANIFEST, aggregate_trajectory_sli

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "src" / "freshlatch" / "eval" / "trajectory_sli.py"


def _jsonl(directory: Path, name: str, events: list[dict]) -> None:
    body = "\n".join(json.dumps(event, ensure_ascii=False) for event in events)
    (directory / name).write_text(body + "\n", encoding="utf-8")


def _run(
    *,
    mode: str = "online",
    duration_ms: int | float | None = None,
    retrieves: list[dict] | None = None,
    terminal: dict | None = None,
    extra: list[dict] | None = None,
) -> list[dict]:
    """一个文件 = 一次 run。retrieve 字段对齐 runner.try_retrieve。"""
    meta: dict = {"type": "run_meta", "mode": mode}
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    events: list[dict] = [meta]
    events.extend(retrieves or [])
    events.extend(extra or [])
    if terminal is not None:
        events.append(terminal)
    return events


def _retrieve(retrieval_mode: str, rerank_mode: str, **extra: object) -> dict:
    event = {
        "type": "retrieve",
        "query": "q",
        "retrieval_mode": retrieval_mode,
        "rerank_mode": rerank_mode,
        "hits": 1,
        "used": 1,
    }
    event.update(extra)
    return event


def _claim(**extra: object) -> dict:
    event = {
        "type": "claim_final",
        "claim_id": "c1",
        "status": "unknown",
        "reason": "",
        "evidence_ids": [],
    }
    event.update(extra)
    return event


def test_happy_path_ops_columns_and_p95_index(tmp_path: Path) -> None:
    """五次成功请求。P95 下标 ceil(0.95*5)-1 = 4，取升序后的 100。"""
    rows = [
        (10, "hybrid+rerank", "bge-reranker-base"),
        (40, "bm25", "none"),
        (100, "hybrid+rerank", "lexical_fallback"),
        (20, "hybrid", "none"),
        (30, "bm25_fallback", "none"),
    ]
    for index, (duration, retrieval_mode, rerank_mode) in enumerate(rows):
        _jsonl(
            tmp_path,
            f"run-{index}.jsonl",
            _run(
                duration_ms=duration,
                retrieves=[_retrieve(retrieval_mode, rerank_mode)],
                terminal=_claim(),
            ),
        )
    row = aggregate_trajectory_sli(tmp_path, window="2026-10-08/2026-10-14 Asia/Shanghai")
    assert row["e2e_p95_ms"] == 100
    assert row["retrieval_fallback_rate"] == "2 / 5"
    assert row["N_request_ok"] == 5
    assert row["N_retrieve"] == 5
    assert row["fallback_n"] == 2
    assert row["window"] == "2026-10-08/2026-10-14 Asia/Shanghai"
    assert "cost → phase-2" in row["notes"]
    assert "不计注册 G1/A1/T1/R1" in row["notes"]
    names_before = sorted(path.name for path in tmp_path.iterdir())
    again = aggregate_trajectory_sli(tmp_path, window=row["window"])
    assert again == row
    assert sorted(path.name for path in tmp_path.iterdir()) == names_before


def test_explicit_bm25_switch_is_not_fallback(tmp_path: Path) -> None:
    """运维开关 retrieval_mode=bm25 不进 fallback 分子。"""
    _jsonl(
        tmp_path,
        "switch.jsonl",
        _run(
            duration_ms=15,
            retrieves=[
                _retrieve("bm25", "none"),
                _retrieve("bm25", "none"),
                _retrieve("hybrid+rerank_lexical", "lexical"),
                _retrieve("dense", "none"),
            ],
            terminal=_claim(status="stale"),
        ),
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["fallback_n"] == 0
    assert row["N_retrieve"] == 4
    assert row["retrieval_fallback_rate"] == "0 / 4"
    assert row["retrieval_fallback_rate"] not in {"0", "0.0", "0%", "0.0%"}
    assert "bm25_fallback" not in row["retrieval_fallback_rate"]
    assert "这是回退计数" in row["notes"]


def test_one_retrieve_counts_once_when_both_fallback_flags(tmp_path: Path) -> None:
    _jsonl(
        tmp_path,
        "both.jsonl",
        _run(
            duration_ms=8,
            retrieves=[_retrieve("bm25_fallback", "lexical_fallback")],
            terminal=_claim(),
        ),
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_retrieve"] == 1
    assert row["fallback_n"] == 1
    assert row["retrieval_fallback_rate"] == "1 / 1"
    assert "全在 fallback" in row["notes"]


def test_budget_and_modeless_retrieve_are_outside_denominator(tmp_path: Path) -> None:
    _jsonl(
        tmp_path,
        "mixed.jsonl",
        _run(
            duration_ms=50,
            retrieves=[_retrieve("hybrid+rerank", "bge-reranker-base")],
            extra=[
                {"type": "budget", "kind": "retrieval_exhausted", "used": 24},
                {"type": "retrieve", "query": "old", "hits": 3, "used": 1},
                {
                    "type": "budget",
                    "kind": "retrieval_exhausted",
                    "retrieval_mode": "bm25_fallback",
                    "rerank_mode": "lexical_fallback",
                },
            ],
            terminal=_claim(),
        ),
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_retrieve"] == 1
    assert row["fallback_n"] == 0
    assert row["retrieval_fallback_rate"] == "0 / 1"


def test_empty_dir_placeholders_not_zero_rates(tmp_path: Path) -> None:
    row = aggregate_trajectory_sli(tmp_path)
    assert row["e2e_p95_ms"] == "样本不足"
    assert row["retrieval_fallback_rate"] == "样本不足"
    assert row["N_request_ok"] == 0
    assert row["N_retrieve"] == 0
    assert row["e2e_p95_ms"] not in {0, 0.0, "0", "0 ms", "0.0"}
    assert row["retrieval_fallback_rate"] not in {"0", "0.0", "0%", "0 / 0"}
    assert "0 ms" not in str(row["e2e_p95_ms"])
    assert "不把 P95 写成 0 ms" in row["notes"]


def test_terminal_without_duration_is_unmeasured(tmp_path: Path) -> None:
    """有终态、没有墙钟：P95 写未计。检索比率仍按事件计，不编成 0。"""
    _jsonl(
        tmp_path,
        "no-clock.jsonl",
        _run(retrieves=[_retrieve("bm25_fallback", "none")], terminal=_claim()),
    )
    _jsonl(tmp_path, "also.jsonl", _run(terminal=_claim()))
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_request_ok"] == 2
    assert row["e2e_p95_ms"] == "未计"
    assert row["e2e_p95_ms"] not in {0, 0.0, "0", "0 ms"}
    assert row["retrieval_fallback_rate"] == "1 / 1"
    assert "P95 写未计" in row["notes"]


def test_retrieve_without_terminal_is_not_request_ok(tmp_path: Path) -> None:
    """半截请求不进 N_request_ok。完成的 retrieve 仍进检索分母。"""
    _jsonl(
        tmp_path,
        "half.jsonl",
        _run(
            retrieves=[_retrieve("bm25", "none")],
            extra=[{"type": "lead_loop_end", "claim_id": "c1", "finished": True}],
        ),
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_request_ok"] == 0
    assert row["e2e_p95_ms"] == "样本不足"
    assert row["N_retrieve"] == 1
    assert row["fallback_n"] == 0
    assert row["retrieval_fallback_rate"] == "0 / 1"


def test_n1_p95_is_that_sample_and_notes_say_smoke(tmp_path: Path) -> None:
    payload = {
        "events": _run(
            duration_ms=17,
            retrieves=[_retrieve("dense", "none")],
            terminal=_claim(),
        )
    }
    (tmp_path / "only.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_request_ok"] == 1
    assert row["e2e_p95_ms"] == 17
    assert "n=1" in row["notes"]
    assert "不报总体方差" in row["notes"]


def test_publish_exit_deny_counts_as_terminal(tmp_path: Path) -> None:
    _jsonl(
        tmp_path,
        "deny.jsonl",
        [
            {"type": "run_meta", "mode": "online"},
            _retrieve("hybrid", "none"),
            {"type": "publish_exit", "allow": False, "duration_ms": 80},
        ],
    )
    _jsonl(
        tmp_path,
        "allow.jsonl",
        [
            _retrieve("bm25", "none"),
            {"type": "publish_exit", "allow": True, "duration_ms": 10},
        ],
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_request_ok"] == 2
    # n=2，ceil(1.9)-1 = 1，升序 [10, 80] 取 80。
    assert row["e2e_p95_ms"] == 80
    assert row["retrieval_fallback_rate"] == "0 / 2"


def test_eval_mode_excluded_from_both_denominators(tmp_path: Path) -> None:
    _jsonl(
        tmp_path,
        "gold.jsonl",
        _run(
            mode="eval",
            duration_ms=1,
            retrieves=[_retrieve("bm25", "none")] * 9,
            terminal=_claim(status="fresh"),
        ),
    )
    _jsonl(
        tmp_path,
        "prod.jsonl",
        _run(
            duration_ms=40,
            retrieves=[_retrieve("bm25_fallback", "none")],
            terminal=_claim(),
        ),
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["N_request_ok"] == 1
    assert row["N_retrieve"] == 1
    assert row["fallback_n"] == 1
    assert row["e2e_p95_ms"] == 40
    assert row["retrieval_fallback_rate"] == "1 / 1"


def test_duration_on_claim_final_when_run_meta_has_none(tmp_path: Path) -> None:
    events = [
        {"type": "retrieve", "retrieval_mode": "bm25", "rerank_mode": "none"},
        {"type": "claim_final", "claim_id": "c1", "status": "unknown", "duration_ms": 12.5},
    ]
    (tmp_path / "one.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n",
        encoding="utf-8",
    )
    row = aggregate_trajectory_sli(tmp_path)
    assert row["e2e_p95_ms"] == 12.5
    assert row["retrieval_fallback_rate"] == "0 / 1"


def test_manifest_and_docstring_exclude_registered_scores() -> None:
    assert SLI_MANIFEST["counted_in_registered_g1_a1_t1_r1"] is False
    assert SLI_MANIFEST["writes_result_y"] is False
    assert SLI_MANIFEST["invents_sesoi"] is False
    text = MODULE.read_text(encoding="utf-8")
    assert "不计" in text and "G1/A1/T1/R1" in text
    assert "不写" in text and "RESULT-Y" in text
    assert "counted_as_pass=true" not in text
    assert "status=pass" not in text
    assert "样本不足" in text


def test_missing_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        aggregate_trajectory_sli(tmp_path / "missing")


def test_bad_json_line_raises(tmp_path: Path) -> None:
    (tmp_path / "bad.jsonl").write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        aggregate_trajectory_sli(tmp_path)
