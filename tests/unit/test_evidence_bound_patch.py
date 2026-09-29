"""#198+#199 Evidence-bound propose/confirm + 单条再验验收。

零 LLM、零网络;资格闸、T1 硬闸、暂存零写、有证覆盖+T 行、单条再验触发、
disposition 再验后重算、VALID_ACTIONS 未扩、非整包默认路径。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch import patch_events as pe
from freshlatch.disposition import aggregate_disposition, ClaimDispositionInput
from freshlatch.evidence_bound import (
    PATCH_EMPTY_T1,
    PATCH_INELIGIBLE,
    PATCH_REVERIFY_UNAVAILABLE,
    PATCH_T1_NOT_ARCHIVED,
    PatchDraftStore,
    confirm_patch,
    discard_patch_draft,
    is_patch_eligible,
    propose_patch,
)
from freshlatch.gates.human_latch import VALID_ACTIONS
from freshlatch.models import Claim
from freshlatch.prepublish import (
    disposition_for_claims,
    list_archived_t1_evidence_ids,
)
from freshlatch.store.base import Chunk, Document, InMemoryStore, chunk_evidence_id

ARCHIVED_EID = "mck-soai-2025-11#p3@T1"
OTHER_EID = "other-doc#p1@T1"


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


def _pack_unknown_stale() -> list[Claim]:
    """未收口 unknown + fresh → 包结论需补丁(无未收口 stale)。"""
    return [
        _claim("mck-3", status="unknown", statement="缺口主张原文"),
        _claim("mck-2", status="fresh", statement="仍支持主张"),
    ]


def _noop_reverify(claim: Claim) -> tuple[str, str]:
    """夹具:不改主张态,只证明再验回调被调用。"""
    return claim.status, "fixture-noop"


def _fresh_reverify(claim: Claim) -> tuple[str, str]:
    """夹具:确定性把目标主张打成 fresh(零 LLM)。"""
    claim.status = "fresh"
    claim.reason = "fixture single-claim reverify"
    return "fresh", "fixture-to-fresh"


# ---------------------------------------------------------------------------
# 资格闸 / propose 暂存零写
# ---------------------------------------------------------------------------


def test_propose_unknown_ok_does_not_mutate_statement_or_ledger(tmp_path: Path):
    """Given 未 discard 的 unknown,When propose_patch,Then 草案可取且正文与正式账本不变。"""
    claims = _pack_unknown_stale()
    before_stmt = claims[0].statement
    events_dir = tmp_path / "patch_events"
    drafts = PatchDraftStore()

    result = propose_patch(
        claim_id="mck-3",
        after_text="经 T1 核后的主张句",
        claims=claims,
        drafts=drafts,
        run_id="run-a",
        t1_ids=[ARCHIVED_EID],
    )
    assert result.ok
    assert result.draft is not None
    assert result.draft.after_text == "经 T1 核后的主张句"
    assert claims[0].statement == before_stmt
    assert pe.read_events(events_dir=events_dir) == []
    assert drafts.get("run-a", "mck-3") is not None


def test_propose_rejects_fresh_and_discarded():
    """Given fresh 或已 discard 主张,When propose_patch,Then 拒绝。"""
    drafts = PatchDraftStore()
    fresh = [_claim("c-fresh", status="fresh")]
    r1 = propose_patch(
        claim_id="c-fresh",
        after_text="改",
        claims=fresh,
        drafts=drafts,
    )
    assert not r1.ok
    assert r1.error_code == PATCH_INELIGIBLE
    assert drafts.get("session", "c-fresh") is None

    discarded = [_claim("c-void", status="unknown", voided=True)]
    r2 = propose_patch(
        claim_id="c-void",
        after_text="改",
        claims=discarded,
        drafts=drafts,
    )
    assert not r2.ok
    assert r2.error_code == PATCH_INELIGIBLE


def test_discard_draft_clears_without_touching_claim_or_ledger(tmp_path: Path):
    """propose 后可丢弃草案;正文与正式账本仍不变。"""
    claims = _pack_unknown_stale()
    before = claims[0].statement
    events_dir = tmp_path / "patch_events"
    drafts = PatchDraftStore()
    propose_patch(
        claim_id="mck-3",
        after_text="草案句",
        claims=claims,
        drafts=drafts,
        run_id="run-b",
    )
    assert discard_patch_draft(claim_id="mck-3", drafts=drafts, run_id="run-b")
    assert drafts.get("run-b", "mck-3") is None
    assert claims[0].statement == before
    assert pe.read_events(events_dir=events_dir) == []


# ---------------------------------------------------------------------------
# confirm 硬闸:空/非法 t1 → 零写
# ---------------------------------------------------------------------------


def test_confirm_empty_t1_rejects_zero_mutation(tmp_path: Path):
    """Given 空 t1_ids,When confirm_patch,Then 拒绝;statement 与正式账本行数不变。"""
    claims = _pack_unknown_stale()
    before = claims[0].statement
    events_dir = tmp_path / "patch_events"
    # 先写一行旧账,确认拒绝后行数仍为 1
    pe.append_event(
        {
            "claim_id": "seed",
            "before_disp": "需补丁",
            "patch_span": "seed",
            "t1_ids": [ARCHIVED_EID],
            "human_confirm": True,
            "reverify": False,
            "minutes": 0.0,
            "arm": "C",
            "ts": "2026-09-29T00:00:00+00:00",
            "actor": "script",
        },
        events_dir=events_dir,
    )
    before_n = len(pe.read_events(events_dir=events_dir))

    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="试图无证改稿",
        t1_ids=[],
        minutes=5.0,
        events_dir=events_dir,
        reverify_fn=_noop_reverify,
    )
    assert not result.ok
    assert result.error_code == PATCH_EMPTY_T1
    assert claims[0].statement == before
    assert len(pe.read_events(events_dir=events_dir)) == before_n
    assert result.reverify_requested is False
    assert result.reverify_triggered is False


def test_confirm_non_archived_t1_rejects_zero_mutation(tmp_path: Path):
    """Given 非本 Run 归档 id,When confirm_patch,Then 拒绝且零改正文零写正式账本。"""
    claims = _pack_unknown_stale()
    before = claims[0].statement
    events_dir = tmp_path / "patch_events"

    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="非法证据改稿",
        t1_ids=[OTHER_EID],
        minutes=3.0,
        events_dir=events_dir,
        reverify_fn=_noop_reverify,
    )
    assert not result.ok
    assert result.error_code == PATCH_T1_NOT_ARCHIVED
    assert claims[0].statement == before
    assert pe.read_events(events_dir=events_dir) == []


def test_confirm_without_reverify_dependency_rejects_zero_mutation(tmp_path: Path):
    """Given 合法 t1 但无 reverify_fn/store,When confirm,Then 拒确认且零改正文。"""
    claims = _pack_unknown_stale()
    before = claims[0].statement
    events_dir = tmp_path / "patch_events"
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="有证但缺再验依赖",
        t1_ids=[ARCHIVED_EID],
        minutes=1.0,
        events_dir=events_dir,
    )
    assert not result.ok
    assert result.error_code == PATCH_REVERIFY_UNAVAILABLE
    assert claims[0].statement == before
    assert pe.read_events(events_dir=events_dir) == []
    assert result.reverify_triggered is False


# ---------------------------------------------------------------------------
# confirm 有证 → 覆盖 + 单条再验 + T 行 + disposition
# ---------------------------------------------------------------------------


def test_confirm_with_valid_t1_overwrites_and_writes_T_row(tmp_path: Path):
    """Given 未 discard 的 unknown 与合法 t1_ids,When confirm_patch,
    Then statement=after_text,单条再验触发,patch_events 追加 arm=T 含 before/after。
    """
    claims = _pack_unknown_stale()
    before_text = claims[0].statement
    events_dir = tmp_path / "patch_events"
    drafts = PatchDraftStore()
    propose_patch(
        claim_id="mck-3",
        after_text="经 T1 核后的主张句",
        claims=claims,
        drafts=drafts,
        run_id="run-c",
        t1_ids=[ARCHIVED_EID],
    )
    # propose 后正文仍旧
    assert claims[0].statement == before_text

    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        minutes=12.5,
        drafts=drafts,
        run_id="run-c",
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_noop_reverify,
    )
    assert result.ok
    assert claims[0].statement == "经 T1 核后的主张句"
    assert result.before_text == before_text
    assert result.after_text == "经 T1 核后的主张句"
    assert result.disposition in ("可发", "需补丁", "勿发")
    assert result.disposition == disposition_for_claims(claims)
    assert result.reverify_requested is True
    assert result.reverify_triggered is True
    assert result.reverify_verdict == "unknown"  # noop 未改态
    assert drafts.get("run-c", "mck-3") is None  # 确认后清草案

    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    row = rows[0]
    assert row["arm"] == pe.PRODUCT_ARM == "T"
    assert row["before_text"] == before_text
    assert row["after_text"] == "经 T1 核后的主张句"
    assert row["t1_ids"] == [ARCHIVED_EID]
    assert row["human_confirm"] is True
    assert row["reverify"] is True
    assert row["claim_id"] == "mck-3"
    assert row["minutes"] == 12.5


def test_confirm_triggers_single_claim_reverify_only(tmp_path: Path):
    """Given 合法 confirm,When 观察再验钩子,Then 仅目标 claim 被再验且事件 reverify=true。"""
    claims = _pack_unknown_stale()
    seen: list[str] = []

    def spy(claim: Claim) -> tuple[str, str]:
        seen.append(claim.claim_id)
        claim.status = "fresh"
        claim.reason = "spy-reverify"
        return "fresh", "spy"

    events_dir = tmp_path / "patch_events"
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="经核主张",
        t1_ids=[ARCHIVED_EID],
        minutes=4.0,
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=spy,
    )
    assert result.ok
    assert result.reverify_triggered is True
    assert seen == ["mck-3"]  # 非整包:mck-2 未被再验
    assert claims[0].status == "fresh"
    assert claims[1].status == "fresh"  # 原本就是 fresh,未被回调
    assert pe.read_events(events_dir=events_dir)[0]["reverify"] is True


def test_confirm_disposition_matches_aggregate_after_reverify(tmp_path: Path):
    """Given 确认后主张态向量,When 聚合 disposition,Then 与发前投影一致。"""
    claims = [
        _claim("mck-3", status="unknown", statement="缺口"),
        _claim("mck-2", status="fresh", statement="绿"),
    ]
    # 确认前:未收口 unknown → 需补丁
    assert disposition_for_claims(claims) == "需补丁"

    events_dir = tmp_path / "patch_events"
    result = confirm_patch(
        claim_id="mck-3",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="改写后缺口主张",
        t1_ids=[ARCHIVED_EID],
        minutes=6.0,
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_fresh_reverify,
    )
    assert result.ok
    assert claims[0].status == "fresh"
    expected = aggregate_disposition(
        ClaimDispositionInput(status=c.status, human_action=None) for c in claims
    )
    assert result.disposition == expected == disposition_for_claims(claims) == "可发"
    assert result.reverify_verdict == "fresh"


def test_confirm_stale_eligible_with_explicit_args(tmp_path: Path):
    """未 discard 的 stale 可直接 confirm(无需先 propose)。"""
    claims = [
        _claim("mck-1", status="stale", statement="过期主张"),
        _claim("mck-2", status="fresh", statement="绿灯"),
    ]
    events_dir = tmp_path / "patch_events"
    result = confirm_patch(
        claim_id="mck-1",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="改写后的过期主张",
        t1_ids=[ARCHIVED_EID],
        minutes=8.0,
        events_dir=events_dir,
        claim_list=claims,
        reverify_fn=_noop_reverify,
    )
    assert result.ok
    assert claims[0].statement == "改写后的过期主张"
    assert result.reverify_triggered is True
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    assert rows[0]["arm"] == "T"
    assert rows[0]["before_text"] == "过期主张"
    assert rows[0]["reverify"] is True


def test_confirm_rejects_fresh_without_writing(tmp_path: Path):
    claims = [_claim("c1", status="fresh", statement="可发主张")]
    events_dir = tmp_path / "patch_events"
    result = confirm_patch(
        claim_id="c1",
        claims=claims,
        archived_t1_ids={ARCHIVED_EID},
        after_text="不该写入",
        t1_ids=[ARCHIVED_EID],
        minutes=1.0,
        events_dir=events_dir,
        reverify_fn=_noop_reverify,
    )
    assert not result.ok
    assert result.error_code == PATCH_INELIGIBLE
    assert claims[0].statement == "可发主张"
    assert pe.read_events(events_dir=events_dir) == []


# ---------------------------------------------------------------------------
# HumanLatch 未扩 / 辅助
# ---------------------------------------------------------------------------


def test_valid_actions_still_discard_renew_only():
    """HumanLatch VALID_ACTIONS 仍仅为 discard|renew。"""
    assert VALID_ACTIONS == ("discard", "renew")
    assert "apply_patch" not in VALID_ACTIONS
    assert "propose_patch" not in VALID_ACTIONS
    assert "confirm_patch" not in VALID_ACTIONS


def test_is_patch_eligible_matrix():
    assert is_patch_eligible(_claim("a", status="unknown"))
    assert is_patch_eligible(_claim("b", status="stale"))
    assert not is_patch_eligible(_claim("c", status="fresh"))
    assert not is_patch_eligible(_claim("d", status="void"))
    assert not is_patch_eligible(_claim("e", status="unknown", voided=True))


def test_list_archived_t1_evidence_ids_from_memory_store():
    store = InMemoryStore()
    chunk = Chunk(
        doc_id="mck-soai-2025-11",
        chunk_id="mck-soai-2025-11-p3",
        clause_id="p3",
        title="摘录",
        text="份额句",
        source_type="public",
        as_of="T1",
        doc_version="1.0",
        checksum="abc",
        tokens=3,
    )
    store.add_document(
        Document(
            doc_id="mck-soai-2025-11",
            as_of="T1",
            source_type="public",
            title="摘录",
            doc_version="1.0",
            checksum="abc",
            full_text="份额句",
        ),
        [chunk],
    )
    ids = list_archived_t1_evidence_ids(store)
    assert chunk_evidence_id(chunk) in ids
    assert ARCHIVED_EID in ids


def test_disposition_recomputed_after_confirm_still_uses_aggregate():
    """返回的 disposition 须来自既有纯函数,不发明第四套词。"""
    claims = [
        _claim("mck-3", status="unknown", statement="缺口"),
        _claim("mck-2", status="fresh", statement="绿"),
    ]
    expected = aggregate_disposition(
        ClaimDispositionInput(status=c.status, human_action=None) for c in claims
    )
    assert disposition_for_claims(claims) == expected
