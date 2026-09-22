"""K4 复验单 Markdown 导出与对账单测:零 LLM、零网络。

对账真源 = sheet.project_claim(与 UI _claim_to_dict 同函数);断言作废灰显标记与
人审/重跑时间线条目不缺,且 MD 与投影字段一致。不改闸/gold/K6-4。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from freshlatch.export.__main__ import main as export_main
from freshlatch.models import Claim
from freshlatch.sheet import (
    claim_from_dict,
    export_sheet_from_snapshot,
    load_snapshot,
    project_claim,
    render_sheet_markdown,
)
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.ui import app as appmod

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"


def _make_store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "freshlatch.db")


def _seed_fixture(tmp_path) -> tuple[SQLiteStore, list[Claim], Path]:
    """夹具:12 主张快照 + 库内 discard/renew/rerun 审计迹(禁网)。"""
    store = _make_store(tmp_path)
    claims: list[Claim] = []
    for i in range(1, 13):
        cid = f"c{i}"
        claims.append(
            Claim(
                claim_id=cid,
                statement=f"主张 {cid} 陈述",
                t0_evidence_ids=[f"t0-doc-{cid}#p2"],
                t1_evidence_ids=[f"t0-doc-{cid}#p2@T1"] if i <= 8 else [],
                status="stale" if i == 1 else ("fresh" if i == 2 else "unknown"),
                reason=f"理由-{cid}",
                voided=(i == 1),
                voided_at="20260922-100000" if i == 1 else None,
                last_confirmed_at="20260922-110000" if i == 2 else None,
                validity_basis={"doc_id": "t0-doc-c2", "checksum": "abc"} if i == 2 else None,
            )
        )

    # c1:作废 + 重跑时间线(rerun 同时写两表;投影只从 rerun_log 计一次)
    store.add_invalidation("c1", "20260922-100000", reason="人审作废")
    store.log_latch("20260922-100000", "c1", "discard", evidence_id=None)
    store.log_rerun("20260922-101000", "c1", "reverify-c1-1", "stale", 1, note="仍红")
    store.log_latch("20260922-101000", "c1", "rerun", evidence_id=None)

    # c2:续命时间线(带 evidence_id)
    store.log_latch(
        "20260922-110000",
        "c2",
        "renew",
        evidence_id="t0-doc-c2#p2@T1",
    )

    snap_path = tmp_path / "sheet_snapshot.json"
    snap = {
        "question": "夹具问题",
        "store": str(store.path),
        "claims": [
            {
                "claim_id": c.claim_id,
                "statement": c.statement,
                "t0_evidence_ids": c.t0_evidence_ids,
                "t1_evidence_ids": c.t1_evidence_ids,
                "status": c.status,
                "reason": c.reason,
                "voided": c.voided,
                "voided_at": c.voided_at,
                "last_confirmed_at": c.last_confirmed_at,
                "validity_basis": c.validity_basis,
            }
            for c in claims
        ],
    }
    snap_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return store, claims, snap_path


def test_project_claim_matches_ui_delegate(tmp_path):
    """UI _claim_to_dict 与 sheet.project_claim 同构(委托同一真源)。"""
    store, claims, _ = _seed_fixture(tmp_path)
    for c in claims:
        assert appmod._claim_to_dict(store, c) == project_claim(store, c)


def test_voided_and_timeline_in_projection(tmp_path):
    """K4-2:作废灰显字段 + 续命/重跑时间线条目机器可查。"""
    store, claims, _ = _seed_fixture(tmp_path)
    p1 = project_claim(store, claims[0])
    assert p1["voided"] is True
    assert p1["voided_at"] == "20260922-100000"
    assert p1["status"] == "stale"  # 不伪造 status=void
    kinds = [e["kind"] for e in p1["timeline"]]
    labels = [e["label"] for e in p1["timeline"]]
    assert kinds == ["discard", "rerun"]  # latch 的 rerun 行不重复计入
    assert "人审作废" in labels
    assert "重跑后仍红(第 1 次)" in labels

    p2 = project_claim(store, claims[1])
    assert p2["voided"] is False
    assert p2["last_confirmed_at"] == "20260922-110000"
    assert p2["validity_basis"] == {"doc_id": "t0-doc-c2", "checksum": "abc"}
    assert len(p2["timeline"]) == 1
    assert p2["timeline"][0]["kind"] == "renew"
    assert p2["timeline"][0]["label"] == "人审续命"
    assert p2["timeline"][0]["evidence_id"] == "t0-doc-c2#p2@T1"


def test_markdown_reconciles_with_projection(tmp_path):
    """导出 MD 与投影字段对账:evidence / 判定 / 理由 / 人审动作 / 灰显标记。"""
    import re

    store, claims, snap_path = _seed_fixture(tmp_path)
    projections = [project_claim(store, c) for c in claims]
    md = render_sheet_markdown(projections, question="夹具问题")

    assert "**主张数**: 12" in md
    assert "夹具问题" in md

    # 全量 12 主张标题在场(用词边界,避免 c1 误匹配 c10)
    for i in range(1, 13):
        assert re.search(rf"^## c{i}(?:\s|$)", md, re.M)

    # c1:灰显 + 判定 + 理由 + evidence + 时间线
    assert "【已作废·灰显】" in md
    assert "- **作废(voided)**: 是" in md
    assert "`stale`" in md
    assert "理由-c1" in md
    assert "`t0-doc-c1#p2`" in md
    assert "人审作废" in md
    assert "重跑后仍红(第 1 次)" in md

    # c2:续命时间线 + evidence_id
    assert "人审续命" in md
    assert "`t0-doc-c2#p2@T1`" in md
    assert "20260922-110000" in md

    # 按主张切块后逐条对账(机器可查,不抽样)
    blocks = re.split(r"(?=^## )", md, flags=re.M)
    by_id = {}
    for block in blocks:
        m = re.match(r"^## (c\d+)\b", block)
        if m:
            by_id[m.group(1)] = block
    assert set(by_id) == {p["claim_id"] for p in projections}

    for proj in projections:
        block = by_id[proj["claim_id"]]
        assert f"`{proj['status']}`" in block
        if proj["reason"]:
            assert proj["reason"] in block
        for eid in proj["t0_evidence_ids"] + proj["t1_evidence_ids"]:
            assert f"`{eid}`" in block
        if proj["voided"]:
            assert "【已作废·灰显】" in block
            assert "**作废(voided)**: 是" in block
        else:
            assert "【已作废·灰显】" not in block
        for ev in proj["timeline"]:
            assert ev["label"] in block
            if ev.get("evidence_id"):
                assert f"`{ev['evidence_id']}`" in block

    # 经快照路径导出一致
    md2 = export_sheet_from_snapshot(snap_path, store)
    assert md2 == md


def test_snapshot_roundtrip_claim_fields(tmp_path):
    _, claims, snap_path = _seed_fixture(tmp_path)
    snap = load_snapshot(snap_path)
    restored = [claim_from_dict(c) for c in snap["claims"]]
    assert len(restored) == 12
    assert restored[0].voided is True
    assert restored[0].status == "stale"
    assert restored[1].validity_basis == claims[1].validity_basis


def test_cli_sheet_writes_markdown(tmp_path):
    store, _, snap_path = _seed_fixture(tmp_path)
    out = tmp_path / "sheet.md"
    export_main(
        [
            "sheet",
            "--snapshot",
            str(snap_path),
            "--db",
            store.path,
            "--out",
            str(out),
        ]
    )
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# 复验单")
    assert "**主张数**: 12" in text
    assert "【已作废·灰显】" in text
    assert "人审续命" in text


def test_cli_module_invocation(tmp_path):
    """python -m freshlatch.export sheet 入口可跑(禁网夹具)。"""
    store, _, snap_path = _seed_fixture(tmp_path)
    out = tmp_path / "via_module.md"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.export",
            "sheet",
            "--snapshot",
            str(snap_path),
            "--db",
            store.path,
            "--out",
            str(out),
        ],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    assert "复验单已写出" in (proc.stdout or "")
