"""Client Memo 导出契约(INV-2/INV-3;支撑 DEM-3 机检边界)。

seam: Client Memo 导出契约(扩既有 export/sheet 形态;不新开第四类 harness)。
读投影、不跑复验;与复验单/内部审计导出分离。DEM-3 完整 rubric 仍人工勾选,
本套件只锁字段在位与禁语,不升格为产品验证。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from freshlatch.export.__main__ import main as export_main
from freshlatch.models import Claim
from freshlatch.sheet import (
    export_client_memo_from_snapshot,
    export_sheet_from_snapshot,
    project_claim,
    render_client_memo_markdown,
)
from freshlatch.store.sqlite_store import SQLiteStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"

# INV-3 / DEM-3 禁止项(机检边界;人工 rubric 另挂勾选面)
FORBIDDEN_ROLE = re.compile(r"Lead|Critic")
FORBIDDEN_VERDICT = re.compile(r"建议进入|建议不进入")
# 字符级偏移 span 形态(本批禁止);允许 doc_id#anchor@as_of
CHAR_SPAN = re.compile(r"#\w+:\d+-\d+")


def _make_store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "freshlatch.db")


def _seed_memo_fixture(tmp_path) -> tuple[SQLiteStore, list[Claim], Path]:
    """夹具:仍成立 / 已作废 / 缺口各至少一条;缺口含无 T1 覆盖。"""
    store = _make_store(tmp_path)
    claims = [
        Claim(
            claim_id="c-fresh",
            statement="仍成立主张",
            t0_evidence_ids=["t0-doc#p1"],
            t1_evidence_ids=["t0-doc#p1@T1"],
            status="fresh",
            reason="T1 同口径仍成立",
        ),
        Claim(
            claim_id="c-void",
            statement="已作废主张",
            t0_evidence_ids=["t0-doc#p2"],
            t1_evidence_ids=["t0-doc#p2@T1"],
            status="stale",
            reason="T1 推翻原前提",
            voided=True,
            voided_at="20260922-100000",
        ),
        Claim(
            claim_id="c-gap",
            statement="缺口主张",
            t0_evidence_ids=["t0-doc#p3"],
            t1_evidence_ids=[],
            status="unknown",
            reason="",
        ),
    ]
    store.add_invalidation("c-void", "20260922-100000", reason="人审作废")
    store.log_latch("20260922-100000", "c-void", "discard", evidence_id=None)
    # 审计迹故意含角色字样——不得泄漏进 Client Memo
    store.log_rerun(
        "20260922-101000",
        "c-void",
        "reverify-c-void-1",
        "stale",
        1,
        note="Lead/Critic 轨迹仅审计",
    )

    snap_path = tmp_path / "memo_snapshot.json"
    snap = {
        "question": "合成课题:定价是否仍成立?",
        "store": str(store.path),
        "synthetic": True,
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
            }
            for c in claims
        ],
    }
    snap_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    return store, claims, snap_path


def test_client_memo_required_fields_inv2(tmp_path):
    """INV-2:ADR-0015 必填字段在位(课题/时间/免责/三分栏/claim+理由/evidence)。"""
    store, claims, _ = _seed_memo_fixture(tmp_path)
    projections = [project_claim(store, c) for c in claims]
    md = render_client_memo_markdown(
        projections,
        question="合成课题:定价是否仍成立?",
        generated_at="2026-09-22T12:00:00+08:00",
        synthetic=True,
    )

    assert "客户向复验备忘" in md
    assert "合成课题:定价是否仍成立?" in md
    assert "2026-09-22T12:00:00+08:00" in md
    assert "非法律意见" in md
    assert "非自动" in md  # 非自动决策 / 非自动商业决策
    assert "synthetic" in md.lower()

    assert "## 仍成立" in md
    assert "## 已作废" in md
    assert "## 缺口" in md

    assert "c-fresh" in md
    assert "T1 同口径仍成立" in md
    assert "c-void" in md
    assert "T1 推翻原前提" in md
    assert "c-gap" in md
    assert "无 T1 覆盖" in md

    assert "`t0-doc#p1@T1`" in md
    assert "](evidence:t0-doc#p1@T1)" in md
    assert CHAR_SPAN.search(md) is None


def test_client_memo_forbids_roles_and_commercial_verdict_inv3(tmp_path):
    """INV-3 + 禁止项:正文不得 Lead/Critic,不得「建议进入/不进入」。"""
    store, claims, _ = _seed_memo_fixture(tmp_path)
    projections = [project_claim(store, c) for c in claims]
    # 污染输入:理由里塞禁语——导出须洗掉,不得原样进正文
    projections[0]["reason"] = "Lead 认为可建议进入;Critic 反对建议不进入"
    md = render_client_memo_markdown(
        projections,
        question="课题问句",
        generated_at="2026-09-22T12:00:00+08:00",
    )
    body = md.split("## DEM-3")[0]  # 勾选面可出现禁语字样作检查项标题
    assert FORBIDDEN_ROLE.search(body) is None
    assert FORBIDDEN_VERDICT.search(body) is None
    # 审计轨迹/人审标签不得进客户向备忘
    assert "人审作废" not in md
    assert "重跑后仍红" not in md
    assert "Lead/Critic 轨迹仅审计" not in md


def test_client_memo_gap_column_explicit_no_t1_when_empty(tmp_path):
    """缺口栏无覆盖条目时显式写「无 T1 覆盖」。"""
    store = _make_store(tmp_path)
    only_fresh = Claim(
        claim_id="c-only",
        statement="仅仍成立",
        t1_evidence_ids=["t0-doc#p1@T1"],
        status="fresh",
        reason="仍成立",
    )
    md = render_client_memo_markdown(
        [project_claim(store, only_fresh)],
        question="仅一栏",
        generated_at="2026-09-22T12:00:00+08:00",
    )
    gap_block = md.split("## 缺口", 1)[1].split("## ", 1)[0]
    assert "无 T1 覆盖" in gap_block


def test_client_memo_separated_from_sheet_export(tmp_path):
    """与内部审计/复验单导出分离:标题与结构不同,sheet 仍含时间线。"""
    store, _, snap_path = _seed_memo_fixture(tmp_path)
    sheet_md = export_sheet_from_snapshot(snap_path, store)
    memo_md = export_client_memo_from_snapshot(
        snap_path,
        store,
        generated_at="2026-09-22T12:00:00+08:00",
    )
    assert sheet_md.startswith("# 复验单")
    assert "人审作废" in sheet_md or "人审续命" in sheet_md or "时间线" in sheet_md
    assert memo_md.startswith("# 客户向复验备忘")
    assert "## 仍成立" in memo_md
    assert memo_md != sheet_md
    assert "建议进入" not in memo_md.split("## DEM-3")[0]


def test_dem3_manual_rubric_checklist_surface(tmp_path):
    """DEM-3:五条「是」+禁止项「无」保留人工勾选面;不升格为产品断言。"""
    store, claims, _ = _seed_memo_fixture(tmp_path)
    md = render_client_memo_markdown(
        [project_claim(store, c) for c in claims],
        question="课题",
        generated_at="2026-09-22T12:00:00+08:00",
    )
    assert "## DEM-3" in md
    assert "人工" in md
    assert "不升格" in md or "产品验证" in md
    # 勾选面:未勾选 checkbox,供人填;测试不把勾选结果当通过线
    assert md.count("- [ ]") >= 6
    assert "课题问题句" in md
    assert "免责声明" in md
    assert "三分栏" in md
    assert "claim_id" in md
    assert "evidence_id" in md or "可点回" in md
    assert "建议进入" in md.split("## DEM-3", 1)[1]  # 禁止项检查条目可出现字面


def test_cli_client_memo_subcommand(tmp_path):
    store, _, snap_path = _seed_memo_fixture(tmp_path)
    out = tmp_path / "client_memo.md"
    export_main(
        [
            "client-memo",
            "--snapshot",
            str(snap_path),
            "--db",
            store.path,
            "--out",
            str(out),
            "--generated-at",
            "2026-09-22T12:00:00+08:00",
        ]
    )
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# 客户向复验备忘")
    assert "## 仍成立" in text
    assert FORBIDDEN_ROLE.search(text.split("## DEM-3")[0]) is None


def test_cli_module_client_memo_invocation(tmp_path):
    store, _, snap_path = _seed_memo_fixture(tmp_path)
    out = tmp_path / "via_module_memo.md"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.export",
            "client-memo",
            "--snapshot",
            str(snap_path),
            "--db",
            store.path,
            "--out",
            str(out),
            "--generated-at",
            "2026-09-22T12:00:00+08:00",
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
    assert "客户向复验备忘已写出" in (proc.stdout or "")
