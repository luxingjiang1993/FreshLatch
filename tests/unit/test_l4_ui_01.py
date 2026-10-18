"""L4-UI-01: 审计面展示 Query、Hits 分、Attribution、Unknown reason。

TestClient 读 HTML,不开浏览器,不调用付费 LLM。
夹具轨迹只放在本文件生成的 tmp 路径。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.evidence import CITE_OUTSIDE_REGISTRY
from freshlatch.numeric_gate import REASON_NUMERIC_MISMATCH
from freshlatch.roles.conflict_evidence import REASON_CONFLICTING_EVIDENCE
from freshlatch.roles.loop import ABSTENTION_REASONS
from freshlatch.roles.retrieve_grade import (
    REASON_GRADE_AMBIGUOUS,
    REASON_GRADE_INCORRECT_EXHAUSTED,
)
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.sheet import project_audit
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_ID = "fix-memo#p1@T1"
BM25_SCORE = 0.8125
RRF_SCORE = 0.25
_DO_NOT_TOUCH = (
    "docs/evidence/patch-events/RESULT-Y.md",
    "docs/evidence/patch-events/PREREG-Y.md",
    "docs/evidence/quality-gate/PREREG.md",
    "docs/evidence/neural-rerank/summary.json",
    "docs/evidence/neural-rerank/per-query.json",
    "data/eval/guard_should.json",
    "data/eval/cite_sentence.json",
    "data/eval/temporal_new_over_old.json",
    "data/eval/gold.json",
    # L4-B-05 扩展人审图的 disputed。冻结 gold / PREREG 仍在本列表。
)
_ROLE_NAMES = ("Lead", "Critic", "Auditor")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    saved = {
        "trajectory": appmod._state.get("trajectory"),
        "claims": list(appmod._state.get("claims") or []),
        "running": appmod._state.get("running"),
        "latch": dict(appmod._state.get("latch") or appmod.EMPTY_LATCH),
    }
    appmod._state["trajectory"] = None
    appmod._state["claims"] = []
    appmod._state["running"] = False
    appmod._state["latch"] = dict(appmod.EMPTY_LATCH)
    try:
        yield TestClient(appmod.app)
    finally:
        appmod._state["trajectory"] = saved["trajectory"]
        appmod._state["claims"] = saved["claims"]
        appmod._state["running"] = saved["running"]
        appmod._state["latch"] = saved["latch"]


def _write_jsonl(path: Path, events: list[dict]) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _scored_events() -> list[dict]:
    return [
        {
            "type": "retrieve",
            "query": "专业版定价",
            "claim_id": "c-ui",
            "as_of": "T1",
            "evidence_ids": [EVIDENCE_ID],
            "hits": 1,
        },
        {
            "type": "lead_step",
            "claim_id": "c-ui",
            "step": 1,
            "tool": "retrieve",
            "args": {"as_of": "T1"},
            "result": {
                "blocks": [{
                    "evidence_id": EVIDENCE_ID,
                    "scores": {
                        "bm25": BM25_SCORE,
                        "dense": None,
                        "rrf": RRF_SCORE,
                        "rerank": None,
                    },
                }],
                "reason_code": REASON_INSUFFICIENT_EVIDENCE,
            },
            "reason_code": REASON_INSUFFICIENT_EVIDENCE,
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-ui",
            "evidence_ids": [EVIDENCE_ID],
            "grade": None,
            "retry_count": 0,
            "abstained": True,
            "steps_used": 1,
            "finished": False,
            "failed": False,
            "failure_reason": None,
            "reason_code": REASON_INSUFFICIENT_EVIDENCE,
        },
    ]


def _section(html: str, element_id: str) -> str:
    marker = f'id="{element_id}"'
    assert marker in html
    return html.split(marker, 1)[1].split("</div>", 1)[0]


def test_ui_audit_shows_score_and_reason(client, tmp_path):
    """验收 1: 轨迹里的 hit 分与 reason code 出现在审计视图 HTML。"""
    path = tmp_path / "scored.jsonl"
    _write_jsonl(path, _scored_events())
    projected = project_audit(path)
    assert projected["parsed"] is True
    assert projected["query"] == ["专业版定价"]
    assert projected["attribution_ids"] == [EVIDENCE_ID]
    assert projected["unknown_reason"] == REASON_INSUFFICIENT_EVIDENCE
    assert projected["unknown_reason"] in ABSTENTION_REASONS
    assert projected["badges"] == [{"claim_id": "c-ui", "badge": "abstain"}]
    hit = projected["hits"][0]
    assert hit["evidence_id"] == EVIDENCE_ID
    assert hit["scores"]["bm25"] == BM25_SCORE
    assert hit["scores"]["rrf"] == RRF_SCORE
    assert hit["scores"]["dense"] is None
    assert hit["scores"]["rerank"] is None

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    assert 'id="audit-panel" class="visible"' in html
    assert "__AUDIT_BODY__" not in html
    hits = _section(html, "audit-hits")
    assert "0.8125" in hits
    assert "0.25" in hits
    assert "bm25" in hits
    assert "dense 无" in hits
    assert "rerank 无" in hits
    assert EVIDENCE_ID in _section(html, "audit-attribution")
    assert "专业版定价" in _section(html, "audit-query")
    assert REASON_INSUFFICIENT_EVIDENCE in _section(html, "audit-unknown")
    for role in _ROLE_NAMES:
        assert role not in html
    # 审计响应不把三徽章 class 画进页面;职人槽由 L4-UI-02 覆盖。
    assert 'class="badge verified"' not in html
    assert 'class="badge partial"' not in html
    assert 'class="badge abstain"' not in html
    buckets = _section(html, "audit-failure-buckets")
    assert "检索空" in buckets
    assert "grade 不够" in buckets
    assert "tool_tier_2 拒" in buckets
    assert "is-active" not in buckets
    assert ">失败<" not in buckets


def test_ui_worker_no_role_names(client):
    """验收 2: 职人视图 HTML 不含角色专名。人审动词仍是作废/续命。"""
    appmod._state["trajectory"] = None
    html = client.get("/").text
    assert "职人视图" in html
    assert 'id="view-craftsman" class="on"' in html
    assert 'id="audit-panel" class="visible"' not in html
    assert "__AUDIT_BODY__" not in html
    for role in _ROLE_NAMES:
        assert role not in html
    assert "作废" in html
    assert "续命" in html
    assert "action: 'discard'" in html or 'action: "discard"' in html
    assert "action:'renew'" in html or "action: 'renew'" in html or 'action:"renew"' in html
    assert "action:'disputed'" in html


def test_ui_audit_path_only_no_fake_score(client, tmp_path):
    """验收 3: 轨迹只有路径、没有解析字段时,不显示假的分数。"""
    path = tmp_path / "only-path.txt"
    path.write_text(str(path), encoding="utf-8")
    projected = project_audit(path)
    assert projected["parsed"] is False
    assert projected["query"] == []
    assert projected["hits"] == []
    assert projected["attribution_ids"] == []
    assert projected["unknown_reason"] is None
    assert projected["badges"] == []

    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    hits = _section(html, "audit-hits")
    assert "无" in hits
    assert not re.search(r"\d", hits)
    assert "bm25" not in hits
    assert "无" in _section(html, "audit-query")
    assert "无" in _section(html, "audit-attribution")
    assert "无" in _section(html, "audit-unknown")
    assert "0.8125" not in html
    assert REASON_INSUFFICIENT_EVIDENCE not in html


def test_ui_audit_ids_without_scores_stay_blank(client, tmp_path):
    """有 evidence id、没有分字段时展示 id,不把缺臂写成数字。"""
    path = tmp_path / "no-score.jsonl"
    _write_jsonl(path, [
        {
            "type": "retrieve",
            "query": "只有查询",
            "claim_id": "c-blank",
            "evidence_ids": ["doc#p9@T1"],
            "hits": 1,
        },
        {
            "type": "lead_loop_end",
            "claim_id": "c-blank",
            "evidence_ids": ["doc#p9@T1"],
            "grade": None,
            "retry_count": 0,
            "reason_code": REASON_GRADE_AMBIGUOUS,
        },
    ])
    projected = project_audit(path)
    assert projected["hits"] == [{"evidence_id": "doc#p9@T1", "scores": None}]
    assert projected["unknown_reason"] == REASON_GRADE_AMBIGUOUS
    appmod._state["trajectory"] = path
    html = client.get("/?view=audit").text
    hits = _section(html, "audit-hits")
    assert "doc#p9@T1" in hits
    assert "分 无" in hits
    assert "bm25" not in hits
    assert not re.search(r"\d+\.\d+", hits)
    assert REASON_GRADE_AMBIGUOUS in _section(html, "audit-unknown")


def test_ui_audit_ignores_free_text_reason(tmp_path):
    """自由文本不进 unknown_reason,页面也不把它当成原因码。"""
    path = tmp_path / "prose.jsonl"
    _write_jsonl(path, [
        {
            "type": "lead_loop_end",
            "claim_id": "c-prose",
            "evidence_ids": [],
            "grade": None,
            "retry_count": 0,
            "reason_code": "模型觉得不够",
        },
    ])
    projected = project_audit(path)
    assert projected["unknown_reason"] is None
    assert projected["parsed"] is False


# -- I-11(#710 / 决议 #704):职人首屏只留问题句/包结论/主 CTA/T1 白话状态 -----------------


def test_i11_checksum_hex_stays_in_collapsible_audit_area(client):
    """checksum hex 不压职人首屏:只在「高级/证据」折叠区内,默认不展开(无 open)。"""
    html = client.get("/").text
    assert '<details id="advanced-evidence">' in html  # 无 open 属性 = 默认折叠
    advanced = html.split('id="advanced-evidence"', 1)[1].split('id="craftsman-badges"', 1)[0]
    assert 'id="t1-checksums"' in advanced
    assert "checksum" in advanced


def test_i11_craftsman_first_screen_keeps_only_core_blocks(client):
    """职人首屏保留主 CTA/包结论/三类清单;噪音元素有职人隐藏规则,审计视图仍露出。"""
    html = client.get("/").text
    assert 'id="btn-run"' in html  # 主 CTA(一键样例)
    assert 'id="disposition-bar"' in html  # 包结论
    assert 'id="vernacular-lists"' in html  # 三类清单(决议 #704 明确不改)
    assert 'id="t1-status-short"' in html  # T1 白话状态(JS 渲染分支)
    for rule in (
        'html[data-view="craftsman"] #budget-progress{display:none}',
        'html[data-view="craftsman"] #pack-badge{display:none}',
        'html[data-view="craftsman"] #btn-import-draft{display:none}',
    ):
        assert rule in html
    audit = client.get("/?view=audit").text
    assert 'id="audit-panel" class="visible"' in audit
    assert "SYNTHETIC" in audit  # 审计视图保留原 SYNTHETIC 标签


def test_abstention_enum_unchanged():
    """Unknown reason 只读封闭枚举。旧码拼写不变;B-02 加入 conflicting_evidence。"""
    assert ABSTENTION_REASONS == frozenset({
        REASON_INSUFFICIENT_EVIDENCE,
        CITE_OUTSIDE_REGISTRY,
        REASON_GRADE_INCORRECT_EXHAUSTED,
        REASON_GRADE_AMBIGUOUS,
        REASON_NUMERIC_MISMATCH,
        REASON_CONFLICTING_EVIDENCE,
    })
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def _git_base_ref() -> str | None:
    """浅克隆没有 origin/main 时返回 None,不 fetch。"""
    candidates = ["origin/main"]
    extra = os.environ.get("GITHUB_BASE_REF", "").strip()
    if extra:
        candidates.append(f"origin/{extra}")
    seen: list[str] = []
    for ref in candidates:
        if ref in seen:
            continue
        seen.append(ref)
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return ref
    return None


def test_do_not_touch_paths_skip_when_base_missing():
    """有 base 时 Do-not-touch 路径不在 diff 里。缺 ref 则跳过,避免 CI exit 128。"""
    base = _git_base_ref()
    if base is None:
        pytest.skip("origin/main 缺失,跳过 Do-not-touch git 路径检查")
    diff = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if diff.returncode != 0:
        pytest.skip(
            "无法对 base 做 git diff,跳过 Do-not-touch git 路径检查: "
            + (diff.stderr or "").strip()
        )
    changed = [
        line.strip().replace("\\", "/")
        for line in diff.stdout.splitlines()
        if line.strip()
    ]
    for path in _DO_NOT_TOUCH:
        assert path not in changed
    assert not any(item.startswith("data/exp/x1/") for item in changed)
