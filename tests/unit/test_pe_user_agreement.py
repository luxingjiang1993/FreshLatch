"""用户抽检对评委。夹具标签，不发请求，不改预注册和已填的三家 κ。"""

from __future__ import annotations

import hashlib
import http.client
import inspect
import os
import socket
from pathlib import Path

from freshlatch.eval import patch_events_judges as judges
from freshlatch.eval.patch_events_spotcheck import IDENTITY

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_ROOT = Path(__file__).resolve().parents[2]
_PREREG = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_GENERATIONS = _ROOT / "docs" / "evidence" / "patch-events" / "formal-generations.jsonl"
_PREREG_SHA256 = "6e21466b028834a2eec5f8001ef74eac6cfca241b8a11cde5a0f1b0ac3e92095"
_COHEN_LINES = (
    "| A | qwen-deepseek | 0.926829268292683 | 30 |",
    "| A | qwen-kimi | 0.7715736040609137 | 30 |",
    "| A | deepseek-kimi | 0.8421052631578947 | 30 |",
    "| B | qwen-deepseek | 0.926829268292683 | 30 |",
    "| B | qwen-kimi | 0.7804878048780488 | 30 |",
    "| B | deepseek-kimi | 0.85 | 30 |",
)
_FLEISS_LINES = (
    "| A | 0.8473713962690785 | 30 |",
    "| B | 0.8523783488244943 | 30 |",
)
_UNFILLED = (
    "| 抽检一致率 | 未填 |",
    "| 用户对评委的 Cohen's κ | 未填 |",
)
_ROWS = (
    {
        "claim_id": "c1",
        "qwen": {"A": "是", "B": "否"},
        "deepseek": {"A": "是", "B": "是"},
        "kimi": {"A": "否", "B": "否"},
    },
    {
        "claim_id": "c2",
        "qwen": {"A": "否", "B": "是"},
        "deepseek": {"A": None, "B": "否"},
        "kimi": {"A": "否", "B": "是"},
    },
    {
        "claim_id": "c3",
        "qwen": {"A": "是", "B": "是"},
        "deepseek": {"A": "否", "B": "否"},
        "kimi": {"A": "是", "B": None},
    },
    {
        "claim_id": "c4",
        "qwen": {"A": "否", "B": "否"},
        "deepseek": {"A": "否", "B": "否"},
        "kimi": {"A": "否", "B": "否"},
    },
)
_USER = {
    "c1": {"A": "是", "B": "否"},
    "c2": {"A": "是", "B": None},
    "c3": {},
}


def _lf(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


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


def _guard(monkeypatch):
    before = {path: path.read_bytes() for path in (_PREREG, _RESULT, _GENERATIONS)}
    seen = _spy_env(monkeypatch)
    _block_network(monkeypatch)
    monkeypatch.setattr(judges, "real_transport", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")))
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不得发请求")),
    )
    return before, seen


def _finish(before: dict[Path, bytes], seen: list[str]) -> None:
    for path, blob in before.items():
        assert path.read_bytes() == blob
    for key in _SECRET_ENV:
        assert key not in seen


def _both(judge_id: str, question: str) -> tuple[int, list[tuple[str, str]]]:
    matched = 0
    pairs: list[tuple[str, str]] = []
    for row in _ROWS:
        user = _USER.get(row["claim_id"], {}).get(question)
        judge = row[judge_id].get(question)
        if user not in {"是", "否"} or judge not in {"是", "否"}:
            continue
        pairs.append((str(user), str(judge)))
        if user == judge:
            matched += 1
    return matched, pairs


def _by_judge(report: dict, question: str) -> dict[str, dict]:
    return {item["judge_id"]: item for item in report["questions"][question]}


def test_agreement_is_matches_over_both_labeled(monkeypatch):
    before, seen = _guard(monkeypatch)
    report = judges.user_judge_agreement(_ROWS, _USER)
    assert report["identity"] == IDENTITY == "模型评委加单人抽检"
    assert set(report["questions"]) == {"A", "B"}
    for question in ("A", "B"):
        found = _by_judge(report, question)
        assert list(found) == ["qwen", "deepseek", "kimi"]
        for judge_id, item in found.items():
            matched, pairs = _both(judge_id, question)
            assert item["n"] == len(pairs)
            assert item["matched"] == matched
            assert item["n"] != len(_ROWS)
            assert item["agreement"] == matched / item["n"]
            assert item["kappa"] == judges._cohen(pairs)["kappa"]
            assert item["n"] == judges._cohen(pairs)["n"]
    qwen_a = _by_judge(report, "A")["qwen"]
    qwen_b = _by_judge(report, "B")["qwen"]
    assert qwen_a["n"] == 2
    assert qwen_b["n"] == 1
    assert qwen_a["n"] + qwen_b["n"] != qwen_a["n"]
    _finish(before, seen)


def test_missing_labels_are_not_imputed_and_user_stays_out_of_fleiss(monkeypatch):
    before, seen = _guard(monkeypatch)
    report = judges.user_judge_agreement(_ROWS, _USER)
    assert "fleiss" not in report
    source = inspect.getsource(judges.user_judge_agreement)
    assert "_cohen(" in source
    assert "_fleiss" not in source
    stuffed = [{**row, "user": {"A": "是", "B": "否"}} for row in _ROWS]
    assert judges.agreement(list(_ROWS)) == judges.agreement(stuffed)
    empty = judges.user_judge_agreement(_ROWS, None)
    assert empty["questions"].keys() == report["questions"].keys()
    for question in ("A", "B"):
        for item in empty["questions"][question]:
            assert item["n"] == 0
            assert item["matched"] == 0
            assert item["agreement"] is None
            assert item["kappa"] is None
            assert item["agreement"] != 0
    text = _lf(_RESULT)
    for line in (*_COHEN_LINES, *_FLEISS_LINES, *_UNFILLED):
        assert line in text
    prereg = _lf(_PREREG)
    assert hashlib.sha256(prereg.encode("utf-8")).hexdigest() == _PREREG_SHA256
    assert "一致率 = 两边标签相同的条数 / 两边都有标签的条数。" in prereg
    assert "用户不进入三家的 Fleiss' κ。" in prereg
    assert "模型评委加单人抽检" in prereg
    module = Path(judges.__file__).read_text(encoding="utf-8")
    assert "真人盲审" not in module
    assert "user_judge_agreement" not in inspect.getsource(judges.main)
    _finish(before, seen)
