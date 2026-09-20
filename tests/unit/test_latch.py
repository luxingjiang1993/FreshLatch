"""HumanLatch 管道单测(ADR-0006):零 LLM、零网络。

顺带覆盖 #11 §5.10 的调用级部分:SqliteSaver 每次 invoke 开关连接,tmp_path 库
跨 enter/decide 多次调用复用(Windows 文件锁不跨调用残留);
进程级「退出→重启→恢复」由 scripts/verify_latch_poc.py 驱动两段子进程验证。
"""

from __future__ import annotations

import sqlite3

import pytest

from freshlatch.gates.human_latch import INVALID_ACTION, RENEW_NOT_OPEN, UNKNOWN_CLAIM
from freshlatch.latch import HumanLatch, HumanLatchError
from freshlatch.models import Claim
from freshlatch.store.sqlite_store import SQLiteStore


def make_store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "freshlatch.db")


def make_latch(store, tmp_path, **kw) -> HumanLatch:
    return HumanLatch(store, tmp_path / "checkpoints.db", **kw)


def make_claims() -> list[Claim]:
    return [
        Claim(claim_id="c1", statement="竞品客单价仍显著高于我们",
              status="stale", reason="T1 竞品降价至我们 70%"),
        Claim(claim_id="c2", statement="普查仍支持规模假设", status="fresh", reason="T1 仍支持"),
        Claim(claim_id="c3", statement="T1 无原文覆盖", status="unknown"),
    ]


# -- 轮次级单 interrupt -------------------------------------------------------------


def test_round_interrupt_pending_only_red_yellow(tmp_path):
    latch = make_latch(make_store(tmp_path), tmp_path)
    claims = make_claims()
    rnd = latch.enter_round(claims, ts="20260920-120000")
    assert rnd.waiting
    assert rnd.thread_id == "reverify-round-20260920-120000"
    assert [p["claim_id"] for p in rnd.pending] == ["c1", "c3"]  # fresh(c2) 不进人审
    assert not claims[0].voided  # interrupt 未 resume,不落档
    assert (tmp_path / "checkpoints.db").exists()


def test_decide_discard_voids_and_logs(tmp_path):
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    claims = make_claims()
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "discard"}])
    assert results[0]["ok"] is True
    assert "c1" in store.list_invalidation()
    assert claims[0].voided and claims[0].voided_at
    assert claims[0].status == "stale"  # stale(机器)与 void(人)并存不互斥
    with store._conn() as conn:
        rows = conn.execute("SELECT action, actor FROM latch_log WHERE claim_id='c1'").fetchall()
    assert [(r["action"], r["actor"]) for r in rows] == [("discard", "human")]


def test_decide_renew_fail_closed_until_w5(tmp_path):
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    rnd = latch.enter_round(make_claims())
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": "t0-competitor-notes#p2@T1"}])
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == RENEW_NOT_OPEN
    assert store.list_invalidation() == []  # 未落任何写


def test_decide_unknown_claim_and_bad_action_rejected(tmp_path):
    latch = make_latch(make_store(tmp_path), tmp_path)
    rnd = latch.enter_round(make_claims())
    results = latch.decide(rnd.thread_id, [{"claim_id": "c9", "action": "discard"},
                                           {"claim_id": "c1", "action": "approve"}])
    assert results[0]["error_code"] == UNKNOWN_CLAIM
    assert results[1]["error_code"] == INVALID_ACTION


def test_no_pending_round_skips_interrupt(tmp_path):
    latch = make_latch(make_store(tmp_path), tmp_path)
    claims = [Claim(claim_id="c2", statement="仍成立", status="fresh")]
    rnd = latch.enter_round(claims)
    assert not rnd.waiting and rnd.thread_id is None
    assert not (tmp_path / "checkpoints.db").exists()  # 无红/黄灯不建 thread


def test_eval_mode_code_level_skip(tmp_path):
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path, mode="eval")
    rnd = latch.enter_round(make_claims())
    assert not rnd.waiting and rnd.pending == []
    assert not (tmp_path / "checkpoints.db").exists()  # eval 不碰 checkpoint
    with pytest.raises(HumanLatchError):
        latch.decide("reverify-round-x", [])
    with pytest.raises(HumanLatchError):
        latch.rerun(make_claims()[0])


# -- 重跑闭环 ------------------------------------------------------------------------


def test_rerun_requires_invalidated_claim(tmp_path):
    latch = make_latch(make_store(tmp_path), tmp_path)
    with pytest.raises(HumanLatchError):
        latch.rerun(make_claims()[0])


def test_rerun_timeline_gate_note_and_nth(tmp_path):
    store = make_store(tmp_path)
    fake = lambda claim: ("unknown", "Lead 判 fresh,规则闸按作废名单打回(INVALIDATED)")
    latch = make_latch(store, tmp_path, reverify_fn=fake)
    claims = make_claims()
    rnd = latch.enter_round(claims)
    latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "discard"}])

    e1 = latch.rerun(claims[0], ts="20260920-130000")
    assert e1["verdict"] == "unknown"
    assert e1["nth"] == 1
    assert e1["thread_id"] == "reverify-c1-20260920-130000"
    assert e1["label"] == "重跑后仍红(第 1 次)"
    assert "INVALIDATED" in e1["note"]

    e2 = latch.rerun(claims[0], ts="20260920-130100")
    assert e2["nth"] == 2 and e2["label"] == "重跑后仍红(第 2 次)"

    timeline = store.list_reruns("c1")
    assert [t["nth"] for t in timeline] == [1, 2]
    assert all(t["thread_id"].startswith("reverify-c1-") for t in timeline)
    with store._conn() as conn:
        actions = [r["action"] for r in conn.execute(
            "SELECT action FROM latch_log WHERE claim_id='c1'").fetchall()]
    assert actions == ["discard", "rerun", "rerun"]  # 审计迹:谁、何时、什么决定
    # 重跑 = 真实 LangGraph thread(一次复验 = 一个 thread),checkpoint 可回溯
    with sqlite3_conn(tmp_path / "checkpoints.db") as conn:
        rows = conn.execute(
            "SELECT thread_id FROM checkpoints WHERE thread_id LIKE 'reverify-c1-%'").fetchall()
    assert {r[0] for r in rows} == {e1["thread_id"], e2["thread_id"]}


def test_prune_rounds_keeps_recent_five(tmp_path):
    latch = make_latch(make_store(tmp_path), tmp_path)
    claims = make_claims()
    for i in range(7):  # 7 轮复验,每轮一个 thread
        latch.enter_round(claims, ts=f"20260920-00000{i}")
    removed = latch.prune_rounds()
    assert removed == 2
    with sqlite3_conn(tmp_path / "checkpoints.db") as conn:
        left = [r[0] for r in conn.execute(
            "SELECT thread_id FROM checkpoints WHERE thread_id LIKE 'reverify-round-%'").fetchall()]
    assert len(set(left)) == 5


# -- checkpoint 清理(ADR-0006 §9)-----------------------------------------------------


def sqlite3_conn(path):
    return sqlite3.connect(path)


def test_prune_keeps_recent_five_threads(tmp_path):
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    latch.enter_round(make_claims())  # 物化 checkpoints 表
    with sqlite3_conn(tmp_path / "checkpoints.db") as conn:
        for i in range(7):  # 造 7 个该主张的 thread checkpoint
            conn.execute("INSERT INTO checkpoints (thread_id, checkpoint_id) VALUES (?, ?)",
                         (f"reverify-c9-20260920-00000{i}", f"cp-{i}"))
    removed = latch.prune("c9")
    assert removed == 2
    with sqlite3_conn(tmp_path / "checkpoints.db") as conn:
        left = [r[0] for r in conn.execute(
            "SELECT thread_id FROM checkpoints WHERE thread_id LIKE 'reverify-c9-%'").fetchall()]
    assert len(left) == 5
    assert "reverify-c9-20260920-000006" in left  # 留最近(thread_id 字典序 = 时序)


def test_restart_recovery_two_subprocesses():
    """#11 §5.10 进程级验证:phase1 进程退出(锁释放)→ phase2 新进程 resume 恢复并落档。"""
    import os
    import subprocess
    import sys
    from pathlib import Path

    script = Path(__file__).resolve().parent.parent.parent / "scripts" / "verify_latch_poc.py"
    # 显式编码(Anthropic 纪律 #3):text=True 默认用 locale 编解码(Windows 中文版 = GBK),
    # 子进程输出 UTF-8 时父进程解码崩 → proc.stdout=None → 下游 TypeError(CI 700b27c 红因)。
    # 子进程 stdout 编码由 PYTHONIOENCODING 钉死,不依赖调用方环境。
    proc = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "LATCH-POC PASS" in proc.stdout
