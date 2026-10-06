"""发前钩子闸表驱动单测(ADR-0031 / #227)。

覆盖 disposition × ack × 新鲜度五类语义 + 缺 run_id fail-closed。
零 LLM、零网络、不触发整包再验。
"""

from __future__ import annotations

import pytest

from freshlatch.disposition import DISPOSITIONS
from freshlatch.publish_hook import (
    HOOK_CHECKSUM_DRIFT,
    HOOK_DO_NOT_PUBLISH,
    HOOK_MISSING_RUN_ID,
    HOOK_NEEDS_PATCH_NO_ACK,
    HOOK_OK,
    HOOK_UNBOUND_RUN,
    NEEDS_PATCH_BANNER,
    PublishHookResult,
    checksums_fresh,
    evaluate_publish_hook,
)

# (run_id, disposition, ack, checksum_fresh, expect_allow, expect_code, expect_banner, note)
_GATE_CASES: list[tuple] = [
    # —— 缺绑定 / 无法解析 ——
    (None, "可发", False, True, False, HOOK_MISSING_RUN_ID, False, "run_id=None fail-closed"),
    ("", "可发", False, True, False, HOOK_MISSING_RUN_ID, False, "run_id 空串 fail-closed"),
    ("   ", "可发", False, True, False, HOOK_MISSING_RUN_ID, False, "run_id 空白 fail-closed"),
    ("run-1", None, False, True, False, HOOK_UNBOUND_RUN, False, "缺 disposition fail-closed"),
    ("run-1", "通过", False, True, False, HOOK_UNBOUND_RUN, False, "非法第四套词 fail-closed"),
    # —— 勿发拒(不暗示可落 Memo) ——
    ("run-1", "勿发", False, True, False, HOOK_DO_NOT_PUBLISH, False, "勿发+无ack拒"),
    ("run-1", "勿发", True, True, False, HOOK_DO_NOT_PUBLISH, False, "勿发+ack仍拒"),
    ("run-1", "勿发", False, False, False, HOOK_DO_NOT_PUBLISH, False, "勿发优先于漂移码"),
    # —— 需补丁 × ack ——
    ("run-1", "需补丁", False, True, False, HOOK_NEEDS_PATCH_NO_ACK, False, "需补丁无ack拒"),
    ("run-1", "需补丁", True, True, True, HOOK_OK, True, "需补丁+ack放行带页眉"),
    ("run-1", "需补丁", True, False, False, HOOK_CHECKSUM_DRIFT, False, "需补丁+ack但漂移仍拒"),
    # —— 可发 × 新鲜度 ——
    ("run-1", "可发", False, True, True, HOOK_OK, False, "可发未漂放行"),
    ("run-1", "可发", True, True, True, HOOK_OK, False, "可发+多余ack仍放行无页眉"),
    ("run-1", "可发", False, False, False, HOOK_CHECKSUM_DRIFT, False, "可发但checksum漂移拒"),
]


@pytest.mark.parametrize(
    "run_id,disposition,ack,fresh,allow,code,banner,note",
    _GATE_CASES,
    ids=[c[-1] for c in _GATE_CASES],
)
def test_evaluate_publish_hook_table(
    run_id, disposition, ack, fresh, allow, code, banner, note,
):
    """表驱动:disposition × ack × 新鲜度 → 五类语义 + fail-closed。"""
    result = evaluate_publish_hook(
        run_id=run_id,
        disposition=disposition,
        ack_needs_patch=ack,
        checksum_fresh=fresh,
    )
    assert isinstance(result, PublishHookResult), note
    assert result.allow is allow, note
    assert result.code == code, note
    assert result.requires_needs_patch_banner is banner, note
    assert result.message, note
    if allow and disposition == "需补丁":
        assert result.requires_needs_patch_banner is True, note
        assert NEEDS_PATCH_BANNER == "需补丁"
    if result.disposition is not None:
        assert result.disposition in DISPOSITIONS, note
    if not allow:
        # deny 不得暗示可落 Memo(无放行页眉)
        assert result.requires_needs_patch_banner is False or not allow


def test_to_dict_shape():
    """契约出口字段同构,供后续 UI/CLI/HTTP 透传。"""
    r = evaluate_publish_hook(
        run_id="r1", disposition="需补丁", ack_needs_patch=True, checksum_fresh=True,
    )
    d = r.to_dict()
    assert d["allow"] is True
    assert d["disposition"] == "需补丁"
    assert d["code"] == HOOK_OK
    assert d["requires_needs_patch_banner"] is True
    assert "message" in d


@pytest.mark.parametrize(
    "recorded,current,expected,note",
    [
        ({}, {}, True, "双侧空视为未漂"),
        (None, None, True, "None/None 未漂"),
        ({"d1": "aaa"}, {"d1": "aaa"}, True, "同键同值未漂"),
        ({"d1": "aaa"}, {"d1": "bbb"}, False, "同键值变=漂移"),
        ({"d1": "aaa"}, {"d1": "aaa", "d2": "x"}, False, "键集扩大=漂移"),
        ({"d1": "aaa", "d2": "x"}, {"d1": "aaa"}, False, "键集缩小=漂移"),
        ({"d1": "aaa"}, {}, False, "当前空而有记录=漂移"),
    ],
)
def test_checksums_fresh_helper(recorded, current, expected, note):
    """机械新鲜度助手:键集或值不一致即漂。"""
    assert checksums_fresh(recorded, current) is expected, note


def test_gate_is_pure_no_llm_import_side_effect():
    """闸模块不得 import LLM / runner(零 LLM 硬条)。"""
    import ast

    import freshlatch.publish_hook as mod

    with open(mod.__file__, encoding="utf-8") as f:
        tree = ast.parse(f.read())
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_prefixes = ("freshlatch.llm", "openai", "anthropic", "freshlatch.runner",
                          "freshlatch.roles")
    for name in imported:
        for prefix in forbidden_prefixes:
            assert not (name == prefix or name.startswith(prefix + ".")), (
                f"publish_hook 不得引入 {name}"
            )
    # 仅允许 disposition 词表(本仓 adapt)
    assert "freshlatch.disposition" in imported
