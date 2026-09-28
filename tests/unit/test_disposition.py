"""disposition 纯函数表驱动单测(ADR-0027 / #170)。

覆盖四条聚合边界;输出仅允许「可发 / 需补丁 / 勿发」,禁止第四套正式词。
零 LLM、零网络、零磁盘。
"""

from __future__ import annotations

import pytest

from freshlatch.disposition import (
    DISPOSITIONS,
    ClaimDispositionInput,
    aggregate_disposition,
)

C = ClaimDispositionInput


# ADR-0027 四条边界 × 合成主张态向量
# (cases, expected_disposition, note)
_BOUNDARY_CASES: list[tuple[list[ClaimDispositionInput], str, str]] = [
    # 1) 未收口 stale → 勿发
    ([C(status="stale")], "勿发", "单条未收口 stale"),
    ([C(status="fresh"), C(status="stale")], "勿发", "混有未收口 stale 优先勿发"),
    ([C(status="stale"), C(status="unknown")], "勿发", "stale+unknown 仍勿发(优先级)"),
    ([C(status="stale", human_action=None), C(status="fresh")], "勿发", "显式未收口"),
    # 2) 无未收口 stale 但有 unknown/缺口 → 需补丁
    ([C(status="unknown")], "需补丁", "单条 unknown"),
    ([C(status="fresh"), C(status="unknown")], "需补丁", "全无 stale 但有 unknown"),
    ([C(status="stale", human_action="discard"), C(status="unknown")], "需补丁",
     "红灯已 discard 但仍有未处理 unknown"),
    ([C(status="fresh"), C(status="fresh", has_gap=True)], "需补丁", "缺口同侧需补丁"),
    ([C(status="void"), C(status="unknown")], "需补丁", "void 已收口不算 stale,unknown 未处理"),
    # 3) 全 fresh(闸+双判过)且无人审 → 可发
    ([C(status="fresh")], "可发", "单条全 fresh"),
    ([C(status="fresh"), C(status="fresh")], "可发", "多条全 fresh 无人审"),
    ([], "可发", "空向量无未收口问题 → 可发"),
    # 4) 红灯均已 discard/renew 且无未处理 unknown → 可发
    ([C(status="stale", human_action="discard")], "可发", "单条 discard 收口"),
    ([C(status="stale", human_action="renew")], "可发", "单条 renew 收口"),
    ([C(status="stale", human_action="discard"), C(status="fresh")], "可发",
     "红灯 discard + 其余 fresh"),
    ([C(status="stale", human_action="renew"), C(status="fresh")], "可发",
     "红灯 renew + 其余 fresh"),
    ([C(status="stale", human_action="discard"),
      C(status="unknown", human_action="discard")], "可发",
     "stale 与 unknown 均已人审收口"),
    ([C(status="stale", human_action="renew"),
      C(status="unknown", human_action="renew")], "可发",
     "双红灯均 renew 收口"),
    ([C(status="void"), C(status="fresh")], "可发", "void 视为已收口"),
]


@pytest.mark.parametrize(
    "claims,expected,note",
    _BOUNDARY_CASES,
    ids=[c[2] for c in _BOUNDARY_CASES],
)
def test_adr0027_disposition_boundaries(claims, expected, note):
    """表驱动:ADR-0027 四条边界全覆盖。"""
    result = aggregate_disposition(claims)
    assert result == expected, note
    assert result in DISPOSITIONS


def test_output_only_three_formal_words():
    """契约出口仅三值;抽样确认不泄漏第四套近义词。"""
    samples = [
        [C(status="stale")],
        [C(status="unknown")],
        [C(status="fresh")],
        [C(status="stale", human_action="discard")],
    ]
    forbidden = {"通过", "待改", "拦截", "通过中", "待审", "阻塞", "ok", "block", "patch"}
    for claims in samples:
        out = aggregate_disposition(claims)
        assert out in DISPOSITIONS
        assert out not in forbidden
