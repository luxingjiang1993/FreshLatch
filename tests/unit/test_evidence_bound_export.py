"""#201 Evidence-bound 补丁导出包验收。

零 LLM:confirm 或显式导出 → JSON+短 MD 关键字段齐全;
与 Client Memo 分轨;不经 client_memo 字段集冒充。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch import patch_events as pe
from freshlatch.evidence_bound import PatchDraftStore, confirm_patch, propose_patch
from freshlatch.evidence_bound_export import (
    EXPORT_KIND,
    EXPORT_SCHEMA,
    REQUIRED_JSON_KEYS,
    PatchExportError,
    assert_required_json_keys,
    build_patch_export,
    export_from_confirm_result,
    export_from_patch_event,
    write_patch_export,
)
from freshlatch.models import Claim
from freshlatch.sheet import render_client_memo_markdown

ARCHIVED_EID = "mck-soai-2025-11#p3@T1"


def _noop_reverify(claim: Claim) -> tuple[str, str]:
    """#199 后 confirm 须注入再验钩子;导出测用确定性 no-op。"""
    return claim.status, "export-test-noop"


def _claim(
    claim_id: str,
    *,
    status: str = "unknown",
    statement: str = "旧主张正文",
    voided: bool = False,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        statement=statement,
        status=status,  # type: ignore[arg-type]
        voided=voided,
    )


def _pack() -> list[Claim]:
    return [
        _claim("mck-3", status="unknown", statement="缺口主张原文"),
        _claim("mck-2", status="fresh", statement="仍支持主张"),
    ]


# Client Memo 冒充检测:这些字面不应出现在补丁导出 MD
_CLIENT_MEMO_MARKERS = (
    "客户向复验备忘",
    "课题问题句",
    "免责声明",
    "DEM-3",
    "仍成立",
    "已作废",
    "缺口",
)


def test_confirm_returns_json_and_markdown_payload(tmp_path: Path):
    """Given 一次合法 confirm,When 取 result.export,Then JSON 与 MD 均含关键字段。"""
    claims = _pack()
    before_text = claims[0].statement
    events_dir = tmp_path / "patch_events"
    drafts = PatchDraftStore()
    propose_patch(
        claim_id="mck-3",
        after_text="经 T1 核后的主张句",
        claims=claims,
        drafts=drafts,
        run_id="run-export",
        t1_ids=[ARCHIVED_EID],
    )
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        minutes=9.0,
        drafts=drafts,
        run_id="run-export",
        events_dir=events_dir,
        claim_list=claims,
        actor="顾问甲",
        reverify_fn=_noop_reverify,
    )
    assert result.ok
    assert result.export is not None
    payload = result.export.json_payload
    md = result.export.markdown

    assert_required_json_keys(payload)
    assert payload["kind"] == EXPORT_KIND
    assert payload["schema"] == EXPORT_SCHEMA
    assert payload["before_text"] == before_text
    assert payload["after_text"] == "经 T1 核后的主张句"
    assert payload["t1_ids"] == [ARCHIVED_EID]
    assert payload["confirmer"] == "顾问甲"
    assert payload["disposition_before"]  # 再验前
    assert payload["disposition_after"]  # 再验后(=当前重算)
    assert payload["disposition_before"] == result.event["before_disp"]
    assert payload["disposition_after"] == result.disposition

    assert "before_text" in md or "before" in md.lower()
    assert "经 T1 核后的主张句" in md
    assert ARCHIVED_EID in md
    assert "顾问甲" in md
    assert payload["disposition_before"] in md
    assert payload["disposition_after"] in md
    assert "再验前" in md and "再验后" in md


def test_write_patch_export_writes_both_files(tmp_path: Path):
    """显式写出同次 JSON + 短 Markdown 两份文件。"""
    claims = _pack()
    events_dir = tmp_path / "pe"
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="改写后主张",
        t1_ids=[ARCHIVED_EID],
        minutes=4.0,
        events_dir=events_dir,
        claim_list=claims,
        actor="human",
        reverify_fn=_noop_reverify,
    )
    assert result.ok and result.export is not None
    out = tmp_path / "bundle"
    json_path, md_path = write_patch_export(result.export, out)
    assert json_path.is_file() and md_path.is_file()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert_required_json_keys(loaded)
    assert loaded["after_text"] == "改写后主张"
    text = md_path.read_text(encoding="utf-8")
    assert "Evidence-bound" in text
    assert "改写后主张" in text


def test_export_from_patch_event_explicit(tmp_path: Path):
    """显式导出:从正式确认行 + 再验后 disposition 组装,字段与账本一致。"""
    events_dir = tmp_path / "pe"
    event = pe.append_product_confirm(
        claim_id="mck-3",
        before_disp="需补丁",
        patch_span="mck-3·正文替换",
        t1_ids=[ARCHIVED_EID],
        minutes=6.0,
        before_text="旧句",
        after_text="新句",
        actor="确认者乙",
        events_dir=events_dir,
    )
    bundle = export_from_patch_event(event, disposition_after="可发")
    assert_required_json_keys(bundle.json_payload)
    assert bundle.json_payload["before_text"] == "旧句"
    assert bundle.json_payload["after_text"] == "新句"
    assert bundle.json_payload["t1_ids"] == [ARCHIVED_EID]
    assert bundle.json_payload["confirmer"] == "确认者乙"
    assert bundle.json_payload["disposition_before"] == "需补丁"
    assert bundle.json_payload["disposition_after"] == "可发"
    assert "需补丁" in bundle.markdown and "可发" in bundle.markdown


def test_export_from_confirm_result_allows_after_override(tmp_path: Path):
    """#199 再验后若包结论变化,可覆盖 disposition_after 再导出。"""
    claims = _pack()
    events_dir = tmp_path / "pe"
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="覆盖句",
        t1_ids=[ARCHIVED_EID],
        minutes=1.0,
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_noop_reverify,
    )
    refreshed = export_from_confirm_result(result, disposition_after="勿发")
    assert refreshed.json_payload["disposition_before"] == result.event["before_disp"]
    assert refreshed.json_payload["disposition_after"] == "勿发"


def test_export_rejects_failed_confirm():
    claims = [_claim("c1", status="fresh")]
    result = confirm_patch(
        claim_id="c1",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="不该",
        t1_ids=[ARCHIVED_EID],
        minutes=1.0,
    )
    assert not result.ok
    assert result.export is None
    with pytest.raises(PatchExportError):
        export_from_confirm_result(result)


def test_export_path_not_client_memo_field_set():
    """导出路径不经过 Client Memo 字段集冒充。"""
    bundle = build_patch_export(
        claim_id="mck-3",
        before_text="前",
        after_text="后",
        t1_ids=[ARCHIVED_EID],
        confirmer="顾问",
        disposition_before="需补丁",
        disposition_after="可发",
        t1_checksums={ARCHIVED_EID: "sha256:deadbeef"},
    )
    payload = bundle.json_payload
    # 补丁包专有 kind;不是客户备忘
    assert payload["kind"] == EXPORT_KIND
    assert "question" not in payload
    assert "disclaimer" not in payload
    assert "held" not in payload
    assert "voided" not in payload
    assert "gap" not in payload
    assert "synthetic" not in payload

    for marker in _CLIENT_MEMO_MARKERS:
        assert marker not in bundle.markdown

    # Client Memo 渲染确实含这些字面(对照,证明分轨)
    memo = render_client_memo_markdown(
        [
            {
                "claim_id": "mck-3",
                "status": "unknown",
                "voided": False,
                "reason": "缺口",
                "t1_evidence_ids": [ARCHIVED_EID],
            }
        ],
        question="课题?",
        generated_at="2026-09-29T00:00:00+00:00",
    )
    assert "客户向复验备忘" in memo
    assert "课题问题句" in memo


def test_required_json_keys_stable():
    """关键字段集合稳定,供 Exit/验收引用。"""
    assert set(REQUIRED_JSON_KEYS) == {
        "kind",
        "schema",
        "claim_id",
        "before_text",
        "after_text",
        "t1_ids",
        "confirmer",
        "disposition_before",
        "disposition_after",
    }


def test_export_from_event_without_texts_fails():
    """旧行缺 before/after → 显式导出 fail-closed。"""
    with pytest.raises(PatchExportError):
        export_from_patch_event(
            {
                "claim_id": "x",
                "before_disp": "需补丁",
                "t1_ids": [ARCHIVED_EID],
                "actor": "human",
            },
            disposition_after="可发",
        )
