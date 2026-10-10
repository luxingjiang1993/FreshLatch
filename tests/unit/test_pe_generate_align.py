"""#471 L1：生成侧抬正确样 after↔evidence 对齐；不改核验闸实现。

#527 / ADR-0040 后 verify_edit 为主核验 NLI；本文件只锁「生成侧对齐、不 import 核验模块」。
"""

from __future__ import annotations

from freshlatch.eval.patch_events_generate import build_prompt

_ALIGN_T = "T 的 after_text 去掉首尾空白后须与 evidence_text 逐字相同。"
_ALIGN_B1 = "B1 的 after_text 去掉首尾空白后须与 evidence_text 逐字相同。"


def _req(arm: str, phase: str = "rewrite") -> dict:
    return {
        "arm": arm,
        "phase": phase,
        "before_text": "原文甲",
        "evidence_text": "证据乙",
        "claim_text": "不该进 rewrite",
    }


def test_t_and_b1_rewrite_prompt_require_after_align_evidence():
    """可执行证明：改的是生成提示对齐，不是核验闸。"""
    t_prompt = build_prompt(_req("T"))["prompt"]
    b1_prompt = build_prompt(_req("B1"))["prompt"]
    assert _ALIGN_T in t_prompt
    assert _ALIGN_B1 in b1_prompt
    # 对齐句落在 evidence 值之后，避免模型先改写 before 再忽略证据
    assert t_prompt.index("evidence_text：\n证据乙") < t_prompt.index(_ALIGN_T)
    assert b1_prompt.index("evidence_text：\n证据乙") < b1_prompt.index(_ALIGN_B1)


def test_c_rewrite_has_no_evidence_align_instruction():
    c_prompt = build_prompt(_req("C"))["prompt"]
    assert "evidence_text" not in c_prompt
    assert _ALIGN_T not in c_prompt
    assert _ALIGN_B1 not in c_prompt
    assert "逐字相同" not in c_prompt


def test_generate_module_does_not_import_or_bypass_verify():
    """生成侧不得 import 核验模块，也不得在生成里自行 strip 比对放宽。"""
    from pathlib import Path

    src = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "freshlatch"
        / "eval"
        / "patch_events_generate.py"
    ).read_text(encoding="utf-8")
    assert "patch_events_verify" not in src
    assert "after.strip" not in src
    assert "LLMClient(" not in src
