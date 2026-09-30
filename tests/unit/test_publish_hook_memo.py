"""Client Memo 套发前钩子闸(#229 / ADR-0031)。

主缝:UI/CLI 同闸;勿发零写;需补丁+ack 页眉「需补丁」;ADR-0015 禁商业裁决/轨迹。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from freshlatch.models import Claim
from freshlatch.prepublish import disposition_for_claims
from freshlatch.publish_hook import (
    HOOK_DO_NOT_PUBLISH,
    HOOK_NEEDS_PATCH_NO_ACK,
    HOOK_OK,
    NEEDS_PATCH_BANNER,
    evaluate_publish_hook,
)
from freshlatch.sheet import (
    export_client_memo_from_snapshot_gated,
    export_client_memo_gated,
    project_claim,
    render_client_memo_markdown,
)
from freshlatch.store.sqlite_store import SQLiteStore
import freshlatch.ui.app as appmod

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = REPO_ROOT / "src"

FORBIDDEN_ROLE = re.compile(r"Lead|Critic")
FORBIDDEN_VERDICT = re.compile(r"建议进入|建议不进入")


def _store(tmp_path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "memo_gate.db")


def _claims_do_not_publish() -> list[Claim]:
    """未收口 stale → 勿发。"""
    return [
        Claim(
            claim_id="c-stale",
            statement="未收口红灯",
            t0_evidence_ids=["t0#a"],
            t1_evidence_ids=["t0#a@T1"],
            status="stale",
            reason="T1 推翻",
        )
    ]


def _claims_needs_patch() -> list[Claim]:
    """无未收口 stale + 未处理 unknown → 需补丁。"""
    return [
        Claim(
            claim_id="c-fresh",
            statement="仍成立",
            t1_evidence_ids=["t0#a@T1"],
            status="fresh",
            reason="仍成立",
        ),
        Claim(
            claim_id="c-gap",
            statement="缺口",
            t0_evidence_ids=["t0#b"],
            t1_evidence_ids=[],
            status="unknown",
            reason="",
        ),
    ]


def _claims_publishable() -> list[Claim]:
    return [
        Claim(
            claim_id="c-ok",
            statement="全绿",
            t1_evidence_ids=["t0#a@T1"],
            status="fresh",
            reason="仍成立",
        )
    ]


def _snap(tmp_path, store: SQLiteStore, claims: list[Claim], *, run_id: str) -> Path:
    path = tmp_path / f"{run_id}.json"
    path.write_text(
        json.dumps(
            {
                "question": "闸测课题",
                "store": str(store.path),
                "run_id": run_id,
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
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def test_do_not_publish_deny_zero_write(tmp_path):
    """Given 勿发 Run,When 导出,Then deny 且目标路径无新 Memo 文件。"""
    store = _store(tmp_path)
    claims = _claims_do_not_publish()
    assert disposition_for_claims(claims) == "勿发"
    out = tmp_path / "should_not_exist.md"
    assert not out.exists()
    hook, md = export_client_memo_gated(
        run_id="run-deny",
        disposition="勿发",
        projections=[project_claim(store, c) for c in claims],
        generated_at="2026-09-30T00:00:00Z",
        out_path=out,
    )
    assert hook.allow is False
    assert hook.code == HOOK_DO_NOT_PUBLISH
    assert md is None
    assert not out.exists()


def test_needs_patch_without_ack_zero_write(tmp_path):
    store = _store(tmp_path)
    claims = _claims_needs_patch()
    out = tmp_path / "no_ack.md"
    hook, md = export_client_memo_gated(
        run_id="run-np",
        disposition="需补丁",
        projections=[project_claim(store, c) for c in claims],
        generated_at="2026-09-30T00:00:00Z",
        ack_needs_patch=False,
        out_path=out,
    )
    assert hook.allow is False
    assert hook.code == HOOK_NEEDS_PATCH_NO_ACK
    assert md is None
    assert not out.exists()


def test_needs_patch_ack_banner_no_commercial_no_trace(tmp_path):
    """需补丁+ack → 产物含「需补丁」;无商业裁决/无轨迹。"""
    store = _store(tmp_path)
    claims = _claims_needs_patch()
    # 污染理由:禁语须洗掉(ADR-0015);审计迹另从 store 注入验证不泄漏
    claims[0].reason = "Lead 建议进入;Critic 建议不进入"
    store.log_rerun(
        "20260930-100000",
        "c-fresh",
        "reverify-c-fresh-1",
        "fresh",
        1,
        note="Lead/Critic 轨迹仅审计",
    )
    store.add_invalidation("c-gap", "20260930-100000", reason="人审作废")
    out = tmp_path / "with_banner.md"
    hook, md = export_client_memo_gated(
        run_id="run-ack",
        disposition="需补丁",
        projections=[project_claim(store, c) for c in claims],
        generated_at="2026-09-30T00:00:00Z",
        ack_needs_patch=True,
        out_path=out,
    )
    assert hook.allow is True
    assert hook.code == HOOK_OK
    assert hook.requires_needs_patch_banner is True
    assert md is not None
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text == md
    assert NEEDS_PATCH_BANNER in text
    assert f"**{NEEDS_PATCH_BANNER}**" in text
    body = text.split("## DEM-3")[0]
    assert FORBIDDEN_ROLE.search(body) is None
    assert FORBIDDEN_VERDICT.search(body) is None
    assert "人审作废" not in text
    assert "Lead/Critic 轨迹仅审计" not in text


def test_cli_and_core_same_gate_isomorphic(tmp_path):
    """同一 Run + 同一 ack → CLI 与核心闸 allow/deny 同构。"""
    store = _store(tmp_path)
    claims = _claims_do_not_publish()
    snap = _snap(tmp_path, store, claims, run_id="run-iso")
    out_cli = tmp_path / "cli_deny.md"

    core = evaluate_publish_hook(
        run_id="run-iso", disposition="勿发", ack_needs_patch=False, checksum_fresh=True,
    )
    hook, md = export_client_memo_from_snapshot_gated(
        snap,
        store,
        run_id="run-iso",
        disposition="勿发",
        ack_needs_patch=False,
        generated_at="2026-09-30T00:00:00Z",
        out_path=out_cli,
    )
    assert hook.allow is core.allow is False
    assert hook.code == core.code == HOOK_DO_NOT_PUBLISH
    assert md is None
    assert not out_cli.exists()

    # CLI 进程同样 deny + 零写
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.export",
            "client-memo",
            "--snapshot",
            str(snap),
            "--db",
            store.path,
            "--run-id",
            "run-iso",
            "--disposition",
            "勿发",
            "--out",
            str(out_cli),
            "--generated-at",
            "2026-09-30T00:00:00Z",
        ],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(SRC), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode != 0
    assert not out_cli.exists()
    assert "HOOK_DO_NOT_PUBLISH" in (proc.stderr or "") or "勿发" in (proc.stderr or "")


def test_cli_allow_needs_patch_with_ack(tmp_path):
    store = _store(tmp_path)
    claims = _claims_needs_patch()
    snap = _snap(tmp_path, store, claims, run_id="run-cli-ack")
    out = tmp_path / "cli_ack.md"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.export",
            "client-memo",
            "--snapshot",
            str(snap),
            "--db",
            store.path,
            "--run-id",
            "run-cli-ack",
            "--ack-needs-patch",
            "--out",
            str(out),
            "--generated-at",
            "2026-09-30T00:00:00Z",
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
    text = out.read_text(encoding="utf-8")
    assert NEEDS_PATCH_BANNER in text
    assert text.startswith("# 客户向复验备忘")


@pytest.fixture()
def ui_client(tmp_path, monkeypatch):
    store = SQLiteStore(tmp_path / "ui.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "_PATCH_EVENTS_DIR", tmp_path / "patch_events")
    appmod._state.update(
        {
            "claims": [],
            "question": "UI 闸测",
            "trajectory": None,
            "running": False,
            "latch": dict(appmod.EMPTY_LATCH),
            "active_run_id": None,
            "bound_t1_checksums": {},
        }
    )
    appmod._prepublish.clear()
    return TestClient(appmod.app), store


def test_ui_and_cli_same_gate_allow_deny(ui_client, tmp_path):
    """同一 Run/ack:UI API 与核心闸 allow/deny 一致。"""
    client, store = ui_client

    # —— 勿发 ——
    appmod._state["claims"] = _claims_do_not_publish()
    appmod._state["active_run_id"] = "run-ui-deny"
    appmod._state["bound_t1_checksums"] = {}
    r = client.post("/api/client-memo/export?ack_needs_patch=false")
    assert r.status_code == 403
    body = r.json()
    assert body["allow"] is False
    assert body["code"] == HOOK_DO_NOT_PUBLISH
    core = evaluate_publish_hook(
        run_id="run-ui-deny", disposition="勿发", ack_needs_patch=False, checksum_fresh=True,
    )
    assert body["code"] == core.code
    assert body["allow"] == core.allow

    # —— 需补丁无 ack ——
    appmod._state["claims"] = _claims_needs_patch()
    appmod._state["active_run_id"] = "run-ui-np"
    r2 = client.post("/api/client-memo/export?ack_needs_patch=false")
    assert r2.status_code == 403
    assert r2.json()["code"] == HOOK_NEEDS_PATCH_NO_ACK

    # —— 需补丁+ack ——
    r3 = client.post("/api/client-memo/export?ack_needs_patch=true")
    assert r3.status_code == 200
    text = r3.text
    assert NEEDS_PATCH_BANNER in text
    assert "客户向复验备忘" in text
    assert r3.headers.get("X-FreshLatch-Needs-Patch-Banner") == "1"
    body_part = text.split("## DEM-3")[0]
    assert FORBIDDEN_VERDICT.search(body_part) is None


def test_ui_has_export_client_memo_entry():
    """UI 有「导出客户备忘」入口;非第二 UI 栈。"""
    assert "导出客户备忘" in appmod.HTML_PAGE
    assert "exportClientMemo" in appmod.HTML_PAGE
    assert "/api/client-memo/export" in appmod.HTML_PAGE
    assert "ack-needs-patch" in appmod.HTML_PAGE
    # 禁止引入第二 UI 框架脚本/挂载
    assert "app_streamlit" not in appmod.HTML_PAGE
    assert "from streamlit" not in appmod.HTML_PAGE


def test_render_banner_only_when_flagged(tmp_path):
    """页眉「需补丁」仅在 needs_patch_banner 时出现。"""
    store = _store(tmp_path)
    proj = [project_claim(store, c) for c in _claims_publishable()]
    plain = render_client_memo_markdown(
        proj, question="q", generated_at="t", needs_patch_banner=False,
    )
    flagged = render_client_memo_markdown(
        proj, question="q", generated_at="t", needs_patch_banner=True,
    )
    assert f"**{NEEDS_PATCH_BANNER}**" not in plain
    assert f"**{NEEDS_PATCH_BANNER}**" in flagged
