"""A-P7：固定公开 eval 包本地回放，RESULT 带稳定 content_hash。

零付费 API。不改 floors / gold / x1 / RESULT-Y。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from freshlatch.eval.public_pack import (
    PACK_ID,
    replay_public_pack,
    result_from_pack,
    verify_content_hash,
    write_result,
)

REPO = Path(__file__).resolve().parents[2]
PACK = REPO / "tests" / "eval" / "fixtures" / "a_p7_public_eval_pack.json"
DOC = REPO / "docs" / "eval-public-pack.md"
MODULE = REPO / "src" / "freshlatch" / "eval" / "public_pack.py"
GOLD = REPO / "data" / "eval" / "gold.json"
RESULT_Y = REPO / "docs" / "evidence" / "patch-events" / "RESULT-Y.md"


def _independent_hash(result: dict) -> str:
    body = {key: value for key, value in result.items() if key != "content_hash"}
    blob = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def test_replay_hash_stable_and_canonical() -> None:
    first = replay_public_pack()
    second = replay_public_pack(PACK)
    assert first["content_hash"] == second["content_hash"]
    assert first["pack_id"] == PACK_ID
    assert verify_content_hash(first)
    assert _independent_hash(first) == first["content_hash"]
    assert len(first["content_hash"]) == 64
    assert first["paid_api"] is False
    assert first["counted_as_pass"] is False
    assert first["invents_sesoi"] is False
    assert first["writes_result_y"] is False
    assert first["ragas_is_ground_truth"] is False
    assert first["ragas_used_as_label"] is False
    assert first["on_authoritative_leaderboard"] is False
    assert first["scope"] == "公开可复现 ≠ 登上权威榜"
    assert first["n"] == 4
    assert first["n_abstain"] == 1
    assert first["n_label_match"] == 4
    assert first["content_hash"] in DOC.read_text(encoding="utf-8")


def test_abstain_ignores_ragas_overlap() -> None:
    result = replay_public_pack()
    rows = {row["id"]: row for row in result["rows"]}
    abstain = rows["pub-abstain-overlap"]
    assert abstain["system_action"] == "abstain"
    assert abstain["replay_label"] == "abstain"
    assert abstain["independent_label"] == "abstain"
    assert abstain["ragas_faithfulness"] == "1.0"
    assert abstain["ragas_used_as_label"] is False
    assert abstain["label_match"] is True
    low = rows["pub-supported-low-ragas"]
    assert low["ragas_faithfulness"] == "0.0"
    assert low["replay_label"] == "supported"
    assert rows["pub-unsupported"]["replay_label"] == "unsupported"
    assert rows["pub-supported"]["replay_label"] == "supported"


def test_crlf_pack_keeps_hash(tmp_path: Path) -> None:
    """检出可能已是 CRLF。先折成 LF，再分别写成 LF 与 CRLF 副本。"""
    raw = PACK.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    lf = tmp_path / "pack-lf.json"
    crlf = tmp_path / "pack-crlf.json"
    lf.write_bytes(raw)
    crlf.write_bytes(raw.replace(b"\n", b"\r\n"))
    left = replay_public_pack(lf)
    right = replay_public_pack(crlf)
    assert left["pack_sha256"] == right["pack_sha256"]
    assert left["content_hash"] == right["content_hash"]


def test_cli_verify_and_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from freshlatch.eval.__main__ import main

    main(["public-pack", "--verify", "--out", str(tmp_path)])
    captured = capsys.readouterr()
    assert "verify=ok" in captured.out
    written = json.loads((tmp_path / "RESULT.json").read_text(encoding="utf-8"))
    assert verify_content_hash(written)
    assert f"content_hash={written['content_hash']}" in captured.out


def test_rejects_gold_x1_and_evidence_write() -> None:
    before_gold = GOLD.read_bytes()
    before_y = RESULT_Y.read_bytes()
    with pytest.raises(ValueError, match="gold"):
        replay_public_pack(GOLD)
    with pytest.raises(ValueError, match="x1"):
        replay_public_pack(REPO / "data" / "exp" / "x1" / "questions.json")
    sample = replay_public_pack()
    with pytest.raises(ValueError, match="docs/evidence"):
        write_result(sample, REPO / "docs" / "evidence" / "patch-events")
    with pytest.raises(ValueError, match="RESULT-Y"):
        write_result(sample, REPO / "docs" / "evidence" / "patch-events" / "RESULT-Y.md")
    assert GOLD.read_bytes() == before_gold
    assert RESULT_Y.read_bytes() == before_y


def test_docs_and_module_contract() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "公开可复现 ≠ 登上权威榜" in text
    assert "RAGAS alone ≠ ground truth" in text
    assert "content_hash" in text
    assert "python -m freshlatch.eval public-pack" in text
    assert "abstain" in text
    assert "ARES" in text
    assert "pytest" in text
    assert "付费 API" in text
    source = MODULE.read_text(encoding="utf-8")
    assert "os.environ" not in source
    assert "DASHSCOPE" not in source
    assert "import openai" not in source
    assert "requests" not in source


def test_counted_as_pass_stays_false_on_mismatch() -> None:
    pack = {
        "pack_id": PACK_ID,
        "level": "smoke",
        "items": [
            {
                "id": "pub-mismatch",
                "system_action": "answer",
                "context_ids": ["memo#p1@T1"],
                "cited_ids": ["memo#p1@T1"],
                "context_span": "期限为三十日",
                "answer": "期限为三十日",
                "independent_label": "abstain",
                "ragas_faithfulness": "1.0",
            }
        ],
    }
    result = result_from_pack(pack, pack_sha256="ab" * 32)
    assert result["rows"][0]["replay_label"] == "supported"
    assert result["rows"][0]["label_match"] is False
    assert result["counted_as_pass"] is False
    assert result["n_label_match"] == 0
