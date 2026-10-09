"""#471 L1：生成侧抬正确样 after↔evidence 对齐；不放宽 verify_edit。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.eval.patch_events_verify import verify_edit

_ROOT = Path(__file__).resolve().parents[2]
_VERIFY = _ROOT / "src" / "freshlatch" / "eval" / "patch_events_verify.py"
_GENERATE = _ROOT / "src" / "freshlatch" / "eval" / "patch_events_generate.py"
# 锁 verify_edit 逐字语义表面：本票不得改该文件
_VERIFY_SHA256 = "738541f6c55d16ca041b1fd489fe7e2bf1e51d5b1f416bef4366e93c3a964614"
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


def test_verify_edit_surface_unchanged_and_still_exact_match():
    digest = hashlib.sha256(_VERIFY.read_bytes()).hexdigest()
    assert digest == _VERIFY_SHA256
    assert verify_edit(
        {
            "arm": "T",
            "claim_id": "c-fn",
            "after_text": "证据乙",
            "evidence_id": "e1",
            "evidence_text": "证据乙",
        }
    ) == {"ok": True, "score": None, "reason": "一致"}
    # 近义/子串仍不过：证明未放宽逐字语义
    assert verify_edit(
        {
            "arm": "T",
            "claim_id": "c-fn",
            "after_text": "证据乙。",
            "evidence_id": "e1",
            "evidence_text": "证据乙",
        }
    )["ok"] is False
    src = _GENERATE.read_text(encoding="utf-8")
    assert "patch_events_verify" not in src
    assert "after.strip" not in src
    assert "LLMClient(" not in src
