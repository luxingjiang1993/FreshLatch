"""草稿输出路径红线。禁写根与仓库根不得被 --out / --sidecar 覆盖。"""

from __future__ import annotations

import json
from pathlib import Path

from freshlatch.eval.x1_drafts.constants import (
    FORBIDDEN_OUT_ROOTS,
    MARKER_NAME,
    RETRIEVE_X1,
    ROOT,
    SIDECAR_MARKER,
)

class DraftShapeError(ValueError):
    """模型草稿 JSON 形状非法，应写 raw-response 后非 0 退出。"""


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_under(path: Path, root: Path) -> bool:
    target = _resolved(path)
    base = _resolved(root)
    if target == base:
        return True
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def _forbidden_resolved(resolved: Path) -> bool:
    """路径等于仓库根、禁写根、其后代，或禁写根的祖先，则禁止。"""
    if resolved == _resolved(ROOT) or resolved == _resolved(RETRIEVE_X1):
        return True
    for root in FORBIDDEN_OUT_ROOTS:
        r = _resolved(root)
        if _is_under(resolved, r) or _is_under(r, resolved):
            return True
    return False


def is_forbidden_out(path: Path) -> bool:
    """--out 不得等于仓库根、不得是禁写目录的祖先/自身/后代。"""
    return _forbidden_resolved(_resolved(path))


def is_forbidden_sidecar(path: Path) -> bool:
    """sidecar 沿用 --out 的禁写规则，并拒绝落在禁写祖先目录里的文件。"""
    resolved = _resolved(path)
    if _forbidden_resolved(resolved):
        return True
    return _forbidden_resolved(resolved.parent)


def _is_script_sidecar(path: Path) -> bool:
    """已有文件必须带本脚本写入的标记，才允许覆盖。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and data.get(SIDECAR_MARKER) is True


def _can_write_sidecar(path: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_sidecar(path):
        return (
            "错误: --sidecar 不得写成 data/eval/retrieve_x1.json，"
            "也不得落在禁写目录或其祖先下"
        )
    if path.suffix.lower() != ".json":
        return "错误: --sidecar 必须以 .json 结尾"
    if path.exists():
        if path.is_dir():
            return "错误: --sidecar 已存在且是目录"
        if not _is_script_sidecar(path):
            return "错误: --sidecar 已存在且不是本脚本写入的抽检文件，拒绝覆盖"
    return None


def _can_overwrite_out(out: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_out(out):
        return (
            "错误: --out 不得为仓库根，不得位于 data/corpus、data/traps、data/eval、"
            "docs/evidence/hard-gold-arm、reports 之下，也不得是这些目录的祖先"
        )
    if out.exists() and out.is_file():
        return "错误: --out 已存在且不是目录"
    if out.exists() and out.is_dir() and any(out.iterdir()):
        if not (out / MARKER_NAME).is_file():
            return "错误: --out 已存在且非空，缺少本脚本写入的清单，拒绝覆盖"
    return None
