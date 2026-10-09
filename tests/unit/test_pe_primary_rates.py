"""三条 false-accept 只抄同一次 compare_primary。夹具不写入仓库结果表。"""

from __future__ import annotations

import hashlib
import http.client
import inspect
import json
import os
import socket
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_formal as formal
from freshlatch.eval import patch_events_metrics as metrics

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_GENERATIONS = _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl"
_README = _ROOT / "README.md"
_DIAGRAM = _ROOT / "docs" / "现状四闸-结构图.html"
_APP = _ROOT / "src" / "freshlatch" / "ui" / "app.py"
_GENERATIONS_SHA256 = "36b79124f2102e7d033a65aedf9b3f7ce54d6c9ade2291b15c60a72ac764093b"
_PREREG_SHA256 = "6e21466b028834a2eec5f8001ef74eac6cfca241b8a11cde5a0f1b0ac3e92095"
_LEDE_SHA256 = "1e9cb2bb7a4daa0460adfa106f3f7b57bc2d1fbb4ca10cef1dc1f150a9f85237"
_DIAGRAM_SHA256 = "8e44d3c94cb85c444202eef40ef65ca5925d02ec11bd666043aede90a6ce1a7f"
_ENTRY_SHA256 = "719da2f3c2389d0d54edad3fdf2bb78714fa1364831fef5853735df4e3108faf"
_BLANK = """\
| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立 |
|---|---|---|---|---|---|
| T 对 C | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 C | 误拒率 | 未填 | 未填 | 未填 | 未填 |
| T 对 B1 | false-accept rate | 未填 | 未填 | 未填 | 未填 |
| T 对 B2 | false-accept rate | 未填 | 未填 | 未填 | 未填 |

| 项目 | 值 |
|---|---|
| 固定放行数 k | 未填 |
"""
_SENTINEL = 0.101010101010101


def _lf(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _false_accept(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) >= 2 and cells[1] == "false-accept rate" and cells[0].startswith("T 对 "):
            found[cells[0]] = cells
    return found


def _report(**overrides) -> dict:
    base = {
        "k": 4,
        "comparisons": [
            {
                "name": "T-C",
                "point": _SENTINEL,
                "ci95_low": 0.0625,
                "ci95_high": 0.25,
                "established": True,
            },
            {
                "name": "T-B1",
                "point": 0.0,
                "ci95_low": -0.125,
                "ci95_high": 0.125,
                "established": False,
            },
            {
                "name": "T-B2",
                "point": 0.5,
                "ci95_low": 0.25,
                "ci95_high": 0.75,
                "established": True,
            },
        ],
    }
    base.update(overrides)
    return base


def _block_network(monkeypatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("测试不得连网")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(http.client.HTTPConnection, "request", blocked)
    monkeypatch.setattr(http.client.HTTPSConnection, "request", blocked)


def _spy_env(monkeypatch) -> list[str]:
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
    return seen


def test_writer_copies_the_function_return():
    report = _report()
    report["comparisons"][0]["established"] = True
    report["comparisons"][0]["ci95_low"] = -1.0
    written = metrics.write_primary_false_accept(_BLANK, report, b2_count=30)
    fresh = metrics.compare_primary  # 写入器不得改去调用它
    assert "compare_primary(" not in inspect.getsource(metrics.write_primary_false_accept)
    rows = _false_accept(written)
    assert list(rows) == ["T 对 C", "T 对 B1", "T 对 B2"]
    assert rows["T 对 C"][2:] == [
        metrics.format_rate(_SENTINEL),
        metrics.format_rate(-1.0),
        metrics.format_rate(0.25),
        "成立",
    ]
    assert rows["T 对 B1"][2:] == [
        metrics.format_rate(0.0),
        metrics.format_rate(-0.125),
        metrics.format_rate(0.125),
        "不成立",
    ]
    assert rows["T 对 B2"][2] == metrics.format_rate(0.5)
    assert rows["T 对 B2"][5] == "成立"
    assert "| T 对 C | 误拒率 | 未填 | 未填 | 未填 | 未填 |" in written
    k_line = next(line for line in written.splitlines() if line.startswith("| 固定放行数 k |"))
    assert _cells(k_line) == ["固定放行数 k", "4"]
    assert fresh is metrics.compare_primary
    assert metrics.format_rate(_SENTINEL) not in _lf(_RESULT)


def test_wrong_order_or_short_b2_does_not_write_numbers():
    swapped = _report()
    swapped["comparisons"] = list(reversed(swapped["comparisons"]))
    assert metrics.write_primary_false_accept(_BLANK, swapped, b2_count=30) == _BLANK
    assert metrics.write_primary_false_accept(_BLANK, _report(), b2_count=29) == _BLANK
    assert metrics.write_primary_false_accept(_BLANK, _report(), b2_count=31) == _BLANK
    assert metrics.format_rate(_SENTINEL) not in _lf(_RESULT)


def test_k_zero_leaves_the_rate_unfilled():
    report = _report(k=0)
    for item in report["comparisons"]:
        item["point"] = 0.0
        item["ci95_low"] = 0.0
        item["ci95_high"] = 0.0
        item["established"] = False
    written = metrics.write_primary_false_accept(_BLANK, report, b2_count=30)
    assert written == _BLANK
    for cells in _false_accept(written).values():
        assert cells[2] == "未填"
        assert cells[2] != "0"
    assert "| 固定放行数 k | 未填 |" in written
    assert "| 固定放行数 k | 0 |" not in written


def test_missing_b2_still_refuses_compare_primary():
    assert metrics.PRIMARY_CONTRASTS == ("C", "B1", "B2")
    assert "B2" in inspect.getsource(metrics._aligned)
    row = {
        "claim_id": "c0",
        "edit_type": "数值",
        "ablation": "",
        "construction_gold": "正确",
        "before_text": "前",
        "after_text": "后",
        "evidence_id": "doc#c0@T1",
        "evidence_text": "证据",
        "decision": "reject",
        "score": None,
    }
    rows = [{**row, "arm": arm} for arm in ("C", "T", "B1")]
    with pytest.raises(ValueError, match="B2"):
        metrics.compare_primary(rows)


def test_same_string_stays_on_its_own_field():
    same = "模型回了同一句"
    claim = formal._from_saved(
        {"output_field": "claim_text", "text": same},
        {"phase": "claim", "evidence_id": "doc#a@T1"},
    )
    diff = formal._from_saved(
        {"output_field": "after_text", "text": same},
        {"phase": "diff", "evidence_id": "doc#a@T1"},
    )
    assert claim == {"claim_text": same}
    assert "after_text" not in claim
    assert diff["after_text"] == same
    assert "claim_text" not in diff


def test_saved_result_matches_one_compare_primary(monkeypatch):
    before = {
        _RESULT: _RESULT.read_bytes(),
        _PREREG: _PREREG.read_bytes(),
        _GENERATIONS: _GENERATIONS.read_bytes(),
        _README: _README.read_bytes(),
        _DIAGRAM: _DIAGRAM.read_bytes(),
        _APP: _APP.read_bytes(),
    }
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    monkeypatch.setattr(formal, "live_chat", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")))
    generations = _lf(_GENERATIONS)
    assert _sha(generations) == _GENERATIONS_SHA256
    assert _sha(_lf(_PREREG)) == _PREREG_SHA256
    assert "saved_primary_report" not in inspect.getsource(formal.main)
    assert "write_primary_false_accept" not in inspect.getsource(formal.main)
    rows = [json.loads(line) for line in generations.splitlines() if line.strip()]
    claims = {
        item["claim_id"]: item["text"]
        for item in rows
        if item["arm"] == "B2" and item["phase"] == "claim"
    }
    diffs = [
        item
        for item in rows
        if item["arm"] == "B2" and item["phase"] == "diff" and item["output_field"] == "after_text"
    ]
    assert len(diffs) == 30
    assert all(item["text"] != "" for item in diffs)
    assert sum(item["text"] == claims[item["claim_id"]] for item in diffs) > 0
    pack = formal.saved_primary_report(formal.load_pe_v2_formal_n30(), rows)
    assert pack["b2_count"] == 30
    assert [item["name"] for item in pack["report"]["comparisons"]] == ["T-C", "T-B1", "T-B2"]
    repo = _lf(_RESULT)
    # 旧 RESULT 是空分同集附录；路线 B 的 R 选取不得回写其成立格。
    rendered = metrics.write_primary_false_accept(repo, pack["report"], b2_count=pack["b2_count"])
    assert rendered != repo or pack["report"]["comparisons"][2]["point"] != 0
    assert _RESULT.read_bytes() == before[_RESULT]
    assert metrics.format_rate(_SENTINEL) not in repo
    # R：B2 自然放行更宽时固定 k 集合可与 T 不同，旧「T-B2 差锁 0」不再由主路径产生
    t_ids = pack["report"]["arms"]["T"]["fixed"]["selected_claim_ids"]
    b2_ids = pack["report"]["arms"]["B2"]["fixed"]["selected_claim_ids"]
    assert t_ids is not None and b2_ids is not None
    assert pack["report"]["k"] == len(t_ids)
    readme = _lf(_README)
    assert _sha(readme.split("## Snapshot", 1)[0]) == _LEDE_SHA256
    assert _sha(_lf(_DIAGRAM)) == _DIAGRAM_SHA256
    entry = _lf(_APP).split('if __name__ == "__main__":', 1)[1]
    assert _sha(entry) == _ENTRY_SHA256
    for path, blob in before.items():
        assert path.read_bytes() == blob
    for key in _SECRET_ENV:
        assert key not in seen
