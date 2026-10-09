"""ALT-04：平行轨防火墙（主缝零 diff / 禁写主表）。零 LLM，不读密钥。"""

from __future__ import annotations

import builtins
import hashlib
import http.client
import inspect
import os
import random
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_alt as alt
from freshlatch.eval import patch_events_metrics as metrics

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_README = _ROOT / "README.md"
_DIAGRAM = _ROOT / "docs" / "现状四闸-结构图.html"
_APP = _ROOT / "src" / "freshlatch" / "ui" / "app.py"
_ALT_TESTS = _ROOT / "tests" / "unit"
# 拼接构造，避免本文件字面量命中升格禁语扫描。
_UPGRADE_PHRASES = ("甲" + "成立", "结果" + "甲")
_INGESTED = {"doc#p1@T1"}
_FORBIDDEN_WRITE_RELATIVE = (
    "docs/evidence/patch-events/PREREG.md",
    "docs/evidence/patch-events/RESULT.md",
)
# 与 test_pe_freeze_surfaces 同一基线；本票不得改五处冻表面。
_LEDE_SHA256 = "1e9cb2bb7a4daa0460adfa106f3f7b57bc2d1fbb4ca10cef1dc1f150a9f85237"
_DIAGRAM_SHA256 = "8e44d3c94cb85c444202eef40ef65ca5925d02ec11bd666043aede90a6ce1a7f"
_ENTRY_SHA256 = "719da2f3c2389d0d54edad3fdf2bb78714fa1364831fef5853735df4e3108faf"


class AltWriteForbidden(PermissionError):
    """旁路写入入口守卫拒绝主缝证据页。"""


def _guard_alt_write_path(path: Path | str, *, repo_root: Path) -> Path:
    """可测路径守卫：模拟旁路写入入口；目标为旧 PREREG / 主 RESULT 则拒绝。"""
    root = repo_root.expanduser().resolve()
    target = Path(path).expanduser().resolve()
    forbidden = {(root / rel).resolve() for rel in _FORBIDDEN_WRITE_RELATIVE}
    if target in forbidden:
        raise AltWriteForbidden(f"旁路禁写主缝证据页: {target}")
    return target


def _alt_write_text(path: Path | str, text: str, *, repo_root: Path) -> Path:
    """旁路写入入口（测试夹具）：先守卫再写。"""
    target = _guard_alt_write_path(path, repo_root=repo_root)
    target.write_text(text, encoding="utf-8")
    return target


@pytest.fixture(autouse=True)
def _no_secrets_no_net(monkeypatch):
    seen: list[str] = []
    real = os.getenv

    def wrapped(key, default=None):
        name = str(key)
        seen.append(name)
        if name in _SECRET_ENV:
            raise AssertionError("不得读取密钥")
        return real(key, default)

    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(os, "getenv", wrapped)

    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)
    yield seen
    assert not any(name in _SECRET_ENV for name in seen)


def _sha_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lf(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _candidate(claim_id: str, *, gold: str, after: str, evidence: str, eid: str = "doc#p1@T1"):
    return {
        "claim_id": claim_id,
        "construction_gold": gold,
        "after_text": after,
        "evidence_id": eid,
        "evidence_text": evidence,
    }


def _primary_smoke_rows() -> list[dict]:
    rows: list[dict] = []
    for i, gold in enumerate(("正确", "正确", "坏", "坏")):
        cid = f"fw{i}"
        for arm in ("C", "T", "B1", "B2"):
            rows.append(
                {
                    "claim_id": cid,
                    "edit_type": "数值",
                    "arm": arm,
                    "ablation": "",
                    "construction_gold": gold,
                    "before_text": "修改前",
                    "after_text": "修改后",
                    "evidence_id": f"doc#{cid}@T1",
                    "evidence_text": "证据原文",
                    "decision": "reject",
                    "score": 0.2,
                    "latency_ms": 10,
                    "cost": 0,
                    "reverify_ok": False,
                }
            )
    return rows


def test_alt_compare_does_not_write_prereg_or_primary_result(monkeypatch):
    """旁路比较不得写旧 PREREG / 主 RESULT。"""
    before_prereg = _sha_bytes(_PREREG)
    before_result = _sha_bytes(_RESULT)
    writes: list[Path] = []
    real_open = builtins.open

    def tracked_open(file, mode="r", *args, **kwargs):
        path = Path(file).resolve() if not isinstance(file, int) else file
        mode_s = str(mode)
        if isinstance(path, Path) and any(flag in mode_s for flag in ("w", "a", "x", "+")):
            writes.append(path)
            if path in {_PREREG.resolve(), _RESULT.resolve()}:
                raise AssertionError(f"旁路不得写主缝: {path}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", tracked_open)

    rows = alt.run_same_text_gates(
        [_candidate("g", gold="正确", after="证据原文", evidence="证据原文")],
        ingested_t1=_INGESTED,
    )
    alt.compare_alt_natural(rows)

    assert _sha_bytes(_PREREG) == before_prereg
    assert _sha_bytes(_RESULT) == before_result
    forbidden = {_PREREG.resolve(), _RESULT.resolve()}
    assert not any(path in forbidden for path in writes)
    # 旁路模块仍无文件写入 API（与 ALT-01 一致）。
    src = inspect.getsource(alt)
    assert "write_text" not in src
    assert "write_bytes" not in src
    assert "open(" not in src
    assert "Path(" not in src


def test_write_entry_rejects_prereg_and_primary_result(tmp_path):
    """写入入口经路径守卫：目标为旧 PREREG / 主 RESULT → 拒绝。"""
    with pytest.raises(AltWriteForbidden):
        _alt_write_text(_PREREG, "不得写入", repo_root=_ROOT)
    with pytest.raises(AltWriteForbidden):
        _alt_write_text(_RESULT, "不得写入", repo_root=_ROOT)
    with pytest.raises(AltWriteForbidden):
        _alt_write_text(
            _ROOT / "docs" / "evidence" / "patch-events" / ".." / "patch-events" / "RESULT.md",
            "不得写入",
            repo_root=_ROOT,
        )
    before_prereg = _sha_bytes(_PREREG)
    before_result = _sha_bytes(_RESULT)
    allowed = tmp_path / "probe-note.md"
    _alt_write_text(allowed, "旁路可读", repo_root=_ROOT)
    assert allowed.read_text(encoding="utf-8") == "旁路可读"
    assert _sha_bytes(_PREREG) == before_prereg
    assert _sha_bytes(_RESULT) == before_result


def test_parallel_alt_tests_forbid_upgrade_phrases():
    """平行轨测试不含升格用语（甲+成立 / 结果+甲）。"""
    hits: list[str] = []
    for path in sorted(_ALT_TESTS.glob("test_pe_alt_*.py")):
        text = path.read_text(encoding="utf-8")
        for phrase in _UPGRADE_PHRASES:
            if phrase in text:
                hits.append(f"{path.name}:{phrase}")
    assert hits == []


def test_compare_primary_still_importable_and_callable():
    """主 compare_primary 仍可 import / 调用（冒烟，不改其行为）。"""
    assert callable(metrics.compare_primary)
    primary_src = inspect.getsource(metrics.compare_primary)
    before = random.getstate()
    report = metrics.compare_primary(
        _primary_smoke_rows(),
        streams=metrics.named_streams(),
    )
    assert report["k"] == 0
    assert [item["name"] for item in report["comparisons"]] == ["T-C", "T-B1", "T-B2"]
    assert all(item["established"] is False for item in report["comparisons"])
    assert inspect.getsource(metrics.compare_primary) == primary_src
    assert random.getstate() == before


def test_frozen_surfaces_untouched_by_alt_firewall_ticket():
    """本票不改五处冻表面（README 导语 / 架构图 / demo 入口；简历与 mastery 无独立文件）。"""
    readme = _lf(_README)
    lede = readme.split("## Snapshot", 1)[0]
    assert _sha_text(lede) == _LEDE_SHA256
    assert _sha_text(_lf(_DIAGRAM)) == _DIAGRAM_SHA256
    entry = _lf(_APP).split('if __name__ == "__main__":', 1)[1]
    assert _sha_text(entry) == _ENTRY_SHA256

    rows = alt.run_same_text_gates(
        [_candidate("g", gold="正确", after="证据原文", evidence="证据原文")],
        ingested_t1=_INGESTED,
    )
    alt.compare_alt_natural(rows)

    readme_after = _lf(_README)
    lede_after = readme_after.split("## Snapshot", 1)[0]
    assert _sha_text(lede_after) == _LEDE_SHA256
    assert _sha_text(_lf(_DIAGRAM)) == _DIAGRAM_SHA256
    entry_after = _lf(_APP).split('if __name__ == "__main__":', 1)[1]
    assert _sha_text(entry_after) == _ENTRY_SHA256
