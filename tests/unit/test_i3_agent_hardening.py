"""I3 #250：B′ 合成夹具（超时结构化错误 · 重放不双写 · 闸分布一页）。

零 LLM。合成夹具 · 非真事故复盘。
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from freshlatch.gates.human_latch import apply_decisions
from freshlatch.i3_gate_dist import render_gate_distribution
from freshlatch.i3_hardening import (
    ERR_AGENT_TIMEOUT,
    ERR_SYNTHETIC_FALSE_GREEN,
    FIXTURE_BANNER,
    StructuredAgentError,
    refuse_silent_green,
    run_with_timeout_structured,
)
from freshlatch.models import Claim
from freshlatch.runner import Runner
from freshlatch.store.base import Chunk, Document, InMemoryStore
from freshlatch.store.sqlite_store import SQLiteStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DOC = ROOT / "docs" / "evidence" / "i3" / "bprime-synthetic.md"
DOC = "t0-competitor-notes"
EID = f"{DOC}#p2@T1"


def _now_factory():
    step = {"n": 0}

    def now() -> datetime:
        step["n"] += 1
        return datetime(2026, 10, 2, 12, 0, step["n"])

    return now


def test_fixture_doc_marks_synthetic_not_real_incident():
    body = FIXTURE_DOC.read_text(encoding="utf-8")
    assert "合成夹具" in body
    assert "非真事故" in body
    assert FIXTURE_BANNER.split("·")[0].strip() in body or "合成夹具" in body


def test_force_timeout_returns_structured_error_not_green():
    """合成超时夹具 → 稳定 error_code + 短中文；不落假绿成功态。"""
    out = run_with_timeout_structured(lambda: "ok", 1.0, force_timeout=True)
    assert isinstance(out, StructuredAgentError)
    assert out.error_code == ERR_AGENT_TIMEOUT
    assert out.ok is False and out.green is False
    assert "超时" in out.message
    assert "合成夹具" in out.message


def test_real_timeout_structured(monkeypatch):
    """真超时路径同样结构化（短睡超短超时）。"""
    def slow():
        time.sleep(0.5)
        return "done"

    out = run_with_timeout_structured(slow, 0.05)
    assert isinstance(out, StructuredAgentError)
    assert out.error_code == ERR_AGENT_TIMEOUT
    assert out.green is False


def test_refuse_silent_false_green():
    err = refuse_silent_green(attempted_green=True, gate_allowed_green=False)
    assert err is not None
    assert err.error_code == ERR_SYNTHETIC_FALSE_GREEN
    assert err.green is False
    assert refuse_silent_green(attempted_green=True, gate_allowed_green=True) is None


def test_runner_guarded_agent_call_emits_timeout_event():
    store = InMemoryStore()
    runner = Runner(store, mode="eval")
    out = runner.guarded_agent_call(
        lambda: "should-not-run",
        force_timeout=True,
        claim_id="c-timeout",
        timeout_s=1.0,
    )
    assert isinstance(out, StructuredAgentError)
    assert out.error_code == ERR_AGENT_TIMEOUT
    hardening = [e for e in runner.ctx.events if e.get("type") == "agent_hardening_error"]
    assert hardening
    assert hardening[0]["error_code"] == ERR_AGENT_TIMEOUT
    assert hardening[0]["status"] != "fresh"


def test_discard_replay_no_double_write(tmp_path):
    store = SQLiteStore(tmp_path / "latch.db")
    claim = Claim(claim_id="c1", statement="x", status="fresh", reason="m")
    now = _now_factory()
    first = apply_decisions(store, {"c1": claim},
                            [{"claim_id": "c1", "action": "discard"}], now=now)
    second = apply_decisions(store, {"c1": claim},
                             [{"claim_id": "c1", "action": "discard"}], now=now)
    assert first[0]["ok"] and second[0]["ok"]
    assert "幂等" in second[0]["detail"]
    assert len(store.list_latch_rows(claim_id="c1")) == 1


def test_renew_replay_no_double_write(tmp_path):
    """人审 renew 同证据重放：不新增 latch_log 坏账行。"""
    store = SQLiteStore(tmp_path / "renew.db")
    chunk = Chunk(
        doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="竞品",
        text="T1 仍成立", source_type="competitor", as_of="T1",
        doc_version="v2", checksum="abc", tokens=10,
    )
    store.add_document(
        Document(doc_id=DOC, as_of="T1", source_type="competitor", title="竞品",
                 doc_version="v2", checksum="abc", full_text=chunk.text),
        [chunk],
    )
    claim = Claim(claim_id="c-r", statement="客单价高", status="stale", reason="旧")
    now = _now_factory()
    decision = {"claim_id": "c-r", "action": "renew", "evidence_id": EID}
    first = apply_decisions(store, {"c-r": claim}, [decision], now=now)
    assert first[0]["ok"] is True
    n1 = len(store.list_latch_rows(claim_id="c-r"))
    second = apply_decisions(store, {"c-r": claim}, [decision], now=now)
    assert second[0]["ok"] is True
    assert "幂等" in second[0]["detail"]
    assert len(store.list_latch_rows(claim_id="c-r")) == n1 == 1


def test_gate_distribution_page_from_trajectory(tmp_path):
    """轨迹 → 闸分布 MD/stdout 含可读计数。"""
    traj = tmp_path / "run-demo.jsonl"
    rows = [
        {"type": "run_meta", "mode": "eval"},
        {"type": "claim_result", "claim_id": "a", "status": "unknown",
         "reason": "[闸打回:NO_T1_EVIDENCE] 无证据"},
        {"type": "claim_result", "claim_id": "b", "status": "unknown",
         "reason": "[闸打回:POLICY_SOURCE_BAN] 政策拒"},
        {"type": "claim_final", "claim_id": "c", "status": "fresh", "reason": "过闸"},
        {"type": "agent_hardening_error", "claim_id": "d", "status": "unknown",
         "error_code": "AGENT_TIMEOUT", "reason": "[闸打回:AGENT_TIMEOUT] 超时"},
    ]
    traj.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                    encoding="utf-8")
    out_md = tmp_path / "gate-dist.md"
    md = render_gate_distribution(traj, out_md=out_md)
    assert out_md.is_file()
    assert "闸分布" in md
    assert "合成夹具" in md
    assert "非真事故" in md
    assert "NO_T1_EVIDENCE" in md
    assert "POLICY_SOURCE_BAN" in md or "AGENT_TIMEOUT" in md
    assert "`fresh`" in md or "fresh" in md
    assert "计数" in md
