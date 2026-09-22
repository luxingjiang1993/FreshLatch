"""α-inv 确定性验收套件(#94 / C1-Batch0-1 预登记卡)。

seam: Latch/Gate + Client Memo 导出契约;不开第四类 harness;不用 freshlatch.eval。
层:invariant。DEMO 项(DEM-1～7)仅对照,不升格为本套件通过线。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.sheet import (
    project_claim,
    render_client_memo_markdown,
)
from freshlatch.store.base import Chunk, Document
from freshlatch.store.sqlite_store import SQLiteStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"
ACCEPTANCE_RECORD = REPO_ROOT / "docs" / "evidence" / "batch1" / "alpha-acceptance.md"
DEM7_SCRIPT = REPO_ROOT / "scripts" / "dem7_time_to_sheet.py"
FORBIDDEN_ROLE = re.compile(r"Lead|Critic")
FORBIDDEN_VERDICT = re.compile(r"建议进入|建议不进入")
ANTI_ELEVATION = "不得把 α-demo 说成「产品已验证 / 一期测量闭合 / UX 证明了 latch」"

DOC = "t0-competitor-notes"
EID = f"{DOC}#p2@T1"


def _store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "freshlatch.db")


def _store_with_t1(tmp_path) -> SQLiteStore:
    store = _store(tmp_path)
    text = "T1:竞品客单价仍显著高于我们。"
    chunk = Chunk(
        doc_id=DOC,
        chunk_id=f"{DOC}-p2",
        clause_id="p2",
        title="竞品笔记",
        text=text,
        source_type="competitor",
        as_of="T1",
        doc_version="v2",
        checksum="",
        tokens=20,
    )
    store.add_document(
        Document(
            doc_id=DOC,
            as_of="T1",
            source_type="competitor",
            title="竞品笔记",
            doc_version="v2",
            checksum="",
            full_text=text,
        ),
        [chunk],
    )
    return store


def _stale_claim(cid: str = "c-void") -> Claim:
    return Claim(
        claim_id=cid,
        statement="竞品客单价仍显著高于我们",
        status="stale",
        reason="T1 竞品降价至我们 70%",
        t1_evidence_ids=[EID],
    )


# -- INV-1 Void→Stay-Red -------------------------------------------------------


def test_inv1_void_stay_red_100_percent(tmp_path):
    """INV-1:作废后 fresh/renew/rerun→Lead fresh 一律不得变绿可签发(Stay-Red=100%)。"""
    store = _store_with_t1(tmp_path)
    latch = HumanLatch(store, tmp_path / "checkpoints.db")
    claim = _stale_claim()
    claims = [claim]
    rnd = latch.enter_round(claims, ts="20260922-200000")
    discard = latch.decide(rnd.thread_id, [{"claim_id": claim.claim_id, "action": "discard"}])
    assert discard[0]["ok"] is True
    assert claim.claim_id in store.list_invalidation()
    assert claim.voided is True
    assert claim.status != "fresh"  # 机器态可仍 stale;不得变绿

    # 路径 A:规则闸对 Lead fresh 打回
    fresh_attempt = rule_gate(
        claim,
        GateDecision(
            status="fresh",
            t1_evidence_ids=[EID],
            auditor_verdict="fresh",
        ),
        GateContext(invalidation_list=set(store.list_invalidation())),
    )
    assert fresh_attempt.error_code == "INVALIDATED"
    assert not fresh_attempt.green and not fresh_attempt.allowed

    # 路径 B:人审续命写路径打回(另开一轮;作废名单仍生效)
    rnd2 = latch.enter_round(claims, ts="20260922-200100")
    renew = latch.decide(
        rnd2.thread_id,
        [{"claim_id": claim.claim_id, "action": "renew", "evidence_id": EID}],
    )
    assert renew[0]["ok"] is False
    assert renew[0]["error_code"] == "INVALIDATED"
    assert claim.status != "fresh"

    # 路径 C:重跑 — 模拟 Runner._finalize:Lead 欲 fresh → 同闸打回 → 落档非 fresh
    def gated_reverify(c: Claim) -> tuple[str, str]:
        gated = rule_gate(
            c,
            GateDecision(
                status="fresh",
                t1_evidence_ids=[EID],
                auditor_verdict="fresh",
            ),
            GateContext(invalidation_list=set(store.list_invalidation())),
        )
        if not gated.green:
            return (
                "unknown",
                f"Lead 判 fresh,规则闸按作废名单打回({gated.error_code})",
            )
        return ("fresh", "")

    latch_rerun = HumanLatch(
        store, tmp_path / "checkpoints-rerun.db", reverify_fn=gated_reverify
    )
    entry = latch_rerun.rerun(claim, ts="20260922-200200")
    assert "INVALIDATED" in entry["note"]
    assert entry["verdict"] != "fresh"
    assert claim.status != "fresh"
    assert "转绿" not in entry["label"]

    # Stay-Red = 100%:三路径全部不得变绿可签发
    # 注:latch.rerun 信任 reverify_fn;Stay-Red 以规则闸为准(上表 gate / renew / gated_reverify)
    stay_red = {
        "gate_fresh": not fresh_attempt.green,
        "renew": renew[0]["error_code"] == "INVALIDATED",
        "rerun": entry["verdict"] != "fresh" and "INVALIDATED" in entry["note"],
    }
    assert all(stay_red.values()) and len(stay_red) == 3



# -- INV-2 / INV-3(Client Memo 导出契约 seam)-----------------------------------


def _memo_fixture(tmp_path):
    store = _store(tmp_path)
    claims = [
        Claim(
            claim_id="c-fresh",
            statement="仍成立主张",
            t1_evidence_ids=["t0-doc#p1@T1"],
            status="fresh",
            reason="T1 同口径仍成立",
        ),
        Claim(
            claim_id="c-void",
            statement="已作废主张",
            t1_evidence_ids=["t0-doc#p2@T1"],
            status="stale",
            reason="T1 推翻原前提",
            voided=True,
            voided_at="20260922-100000",
        ),
        Claim(
            claim_id="c-gap",
            statement="缺口主张",
            t1_evidence_ids=[],
            status="unknown",
            reason="",
        ),
    ]
    store.add_invalidation("c-void", "20260922-100000", reason="人审作废")
    return store, claims


def test_inv2_client_memo_required_fields(tmp_path):
    """INV-2:ADR-0015 必填字段在位;不得含商业裁决句。"""
    store, claims = _memo_fixture(tmp_path)
    md = render_client_memo_markdown(
        [project_claim(store, c) for c in claims],
        question="合成课题:定价是否仍成立?",
        generated_at="2026-09-22T20:00:00+08:00",
        synthetic=True,
    )
    body = md.split("## DEM-3")[0]
    assert "客户向复验备忘" in md
    assert "合成课题:定价是否仍成立?" in md
    assert "2026-09-22T20:00:00+08:00" in md
    assert "非法律意见" in md
    assert "## 仍成立" in md and "## 已作废" in md and "## 缺口" in md
    assert "c-fresh" in md and "c-void" in md and "c-gap" in md
    assert "无 T1 覆盖" in md
    assert FORBIDDEN_VERDICT.search(body) is None


def test_inv3_client_memo_no_role_leakage(tmp_path):
    """INV-3:备忘正文不得出现 Lead/Critic 字样。"""
    store, claims = _memo_fixture(tmp_path)
    projections = [project_claim(store, c) for c in claims]
    projections[0]["reason"] = "Lead 认为可建议进入;Critic 反对建议不进入"
    md = render_client_memo_markdown(
        projections,
        question="课题问句",
        generated_at="2026-09-22T20:00:00+08:00",
    )
    body = md.split("## DEM-3")[0]
    assert FORBIDDEN_ROLE.search(body) is None
    assert FORBIDDEN_VERDICT.search(body) is None


# -- 验收记录分列 + 禁止升格句 -------------------------------------------------


def test_acceptance_record_splits_alpha_inv_and_demo():
    """验收记录必须分列 α-inv 与 α-demo,并印禁止升格句。"""
    assert ACCEPTANCE_RECORD.exists(), f"缺验收记录: {ACCEPTANCE_RECORD}"
    text = ACCEPTANCE_RECORD.read_text(encoding="utf-8")
    assert re.search(r"α-inv|alpha-inv", text, re.I)
    assert re.search(r"α-demo|alpha-demo", text, re.I)
    assert "INV-1" in text and "INV-2" in text and "INV-3" in text
    assert "DEM-7" in text
    assert ANTI_ELEVATION in text or (
        "产品已验证" in text and "一期测量闭合" in text and "UX 证明了 latch" in text
    )
    # demo 项若提及仅作对照、不升格
    assert "不升格" in text or "对照" in text


def test_acceptance_record_does_not_use_eval_as_main_mouth():
    """测口声明:Latch/Gate + Client Memo;不用 freshlatch.eval 主跑、不改 gold。"""
    text = ACCEPTANCE_RECORD.read_text(encoding="utf-8")
    assert ("Latch" in text or "闸" in text) and ("Gate" in text or "闸" in text)
    assert "Client Memo" in text or "客户向复验备忘" in text
    # 必须显式否定 eval 主跑与改 gold(禁止用模糊「不用」凑过)
    assert "freshlatch.eval" in text
    assert ("不用" in text and "eval" in text) or "未用 freshlatch.eval" in text
    assert "不改" in text and "gold" in text.lower()


# -- DEM-7 Time-to-Sheet(仅观测,无硬阈值)---------------------------------------


def test_dem7_script_exists_and_records_minutes(tmp_path):
    """DEM-7:固定脚本走通并记录分钟数;脚本本身不设 <10min 硬阈值。"""
    assert DEM7_SCRIPT.exists(), f"缺 DEM-7 脚本: {DEM7_SCRIPT}"
    src = DEM7_SCRIPT.read_text(encoding="utf-8")
    # 不设 <10min 硬阈值:脚本须声明观测口径,且无 assert 分钟上界
    assert "硬阈值" in src or "不设" in src or "观测" in src
    assert "assert" not in src.lower() or "elapsed_minutes" not in src.split("assert")[-1][:80]

    out_dir = tmp_path / "dem7"
    out_dir.mkdir()
    proc = subprocess.run(
        [
            sys.executable,
            str(DEM7_SCRIPT),
            "--out-dir",
            str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0, (proc.stderr or "") + (proc.stdout or "")
    record = out_dir / "dem7-time-to-sheet.json"
    assert record.exists()
    payload = json.loads(record.read_text(encoding="utf-8"))
    assert "elapsed_minutes" in payload
    assert isinstance(payload["elapsed_minutes"], (int, float))
    assert payload.get("hard_threshold") in (None, False, "none")
    # 脚本输出也可被验收记录引用,但不在本测断言分钟数上下界
