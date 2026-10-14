"""L4-EV-01: 同 pin、同 gold 的 Recall@k / MRR 分臂表。

断言命令可跑且写出列。不断言新的均值门槛。
值域 [0, 1] 是 recall_at_k / mrr_at_k 的返回范围，不是通过线。
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.eval.__main__ import main
from freshlatch.eval.retrieve_eval import run_arm_metric_table
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "eval" / "fixtures" / "l4_ev_01_arm_gold.json"
EXAMPLE = ROOT / "docs" / "evidence" / "l4-ev-01-arm-table" / "arm-table.json"
PREREG = ROOT / "docs" / "evidence" / "quality-gate" / "PREREG.md"
SUMMARY = ROOT / "docs" / "evidence" / "neural-rerank" / "summary.json"
PER_QUERY = ROOT / "docs" / "evidence" / "neural-rerank" / "per-query.json"

ARMS = ("bm25", "dense", "hybrid", "hybrid+rerank")
HEADER = "| arm | Recall@k | MRR | observed_retrieval_mode | observed_rerank_mode |"
BANNED = ("通过", "失败", "counted_as_pass", "SESOI", "status=", "门槛")
# 神经冻结基线的点估计。小夹具表不得抄这些数字来冒充新表。
# 不收录 1/3、0.6、1.0：它们是小 n 上合法的 Recall / MRR，不是本表的门槛。
FROZEN_POINT_ESTIMATES = (
    "0.9732142857142857",
    "0.8381855867346939",
    "0.7566609977324263",
)
# quality-gate PREREG 只登记 summary.json。per-query.json 与其余 Do-not-touch 文件在此锁字节。
FROZEN_SHA256 = {
    "docs/evidence/neural-rerank/summary.json":
        "8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526",
    "docs/evidence/neural-rerank/per-query.json":
        "2c4df07089eeb33ab5887c588a1907bc3caa5447f9bcdde09280d6b8555f1b4c",
    "docs/evidence/patch-events/RESULT-Y.md":
        "b58d7023b7f7359ec4fae1c32673efaaa56f969d184754f69890b2ec2fc22705",
    "docs/evidence/patch-events/PREREG-Y.md":
        "0381aa4fd3f1247f5d242a16c9151571292f765bb90be182946248def59cc4c4",
    "docs/evidence/quality-gate/PREREG.md":
        "3d01f8a9481effab0506762853789d568451701d6e438b8615dc5a696af7f72c",
    "data/eval/guard_should.json":
        "63144c205f02ebbde88b9dd95217dfc9a1d69f6813590d1dd4818481d50022de",
    "data/eval/cite_sentence.json":
        "7b299a0bce8589bc2fd810a706572be27b4409ab03bc8a6c6b4d8024ee65bc94",
    "data/eval/temporal_new_over_old.json":
        "3a1b959a6aa63b89d10fa883982c11b7b7234aacdb537d754a1587010e40c8a0",
    "data/eval/gold.json":
        "28b8b88c41fb2a89794efe063de2948605f513ca10701cfc081c4ad144a939c2",
}
ROW_KEYS = {
    "arm",
    "mrr",
    "observed_rerank_mode",
    "observed_retrieval_mode",
    "recall_at_k",
}


def _env() -> dict[str, str]:
    env = os.environ.copy()
    env["FRESHLATCH_NEURAL_RERANK"] = "0"
    env["FRESHLATCH_LOCAL_EMBED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run_cli(out: Path, *, pin: str | None) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        "-m",
        "freshlatch.eval",
        "arm-table",
        "--gold",
        "tests/eval/fixtures/l4_ev_01_arm_gold.json",
        "--out",
        str(out),
    ]
    if pin is not None:
        cmd.extend(["--pin", pin])
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _load(out: Path) -> tuple[dict, str]:
    body = json.loads((out / "arm-table.json").read_text(encoding="utf-8"))
    markdown = (out / "arm-table.md").read_text(encoding="utf-8")
    return body, markdown


def test_arm_table_command_writes_columns(tmp_path: Path) -> None:
    out = tmp_path / "arm"
    proc = _run_cli(out, pin="l4-ev-01-test-pin")
    assert proc.returncode == 0, proc.stderr
    body, markdown = _load(out)
    assert body["level"] == "smoke"
    assert body["k"] == 10
    assert body["n"] == 2
    assert body["replaces_frozen_baseline"] is False
    assert body["production_retrieval_mode"] == "hybrid+rerank"
    assert body["code_pin"] == "l4-ev-01-test-pin"
    assert [row["arm"] for row in body["rows"]] == list(ARMS)
    assert HEADER in markdown
    assert "\ufffd" not in markdown
    for row in body["rows"]:
        assert set(row) == ROW_KEYS
        assert isinstance(row["recall_at_k"], float)
        assert isinstance(row["mrr"], float)
        assert 0.0 <= row["recall_at_k"] <= 1.0
        assert 0.0 <= row["mrr"] <= 1.0
        assert row["arm"] in markdown
    rerank = body["rows"][3]
    assert rerank["arm"] == "hybrid+rerank"
    assert rerank["observed_retrieval_mode"] == "hybrid+rerank"
    assert rerank["observed_rerank_mode"] == "lexical_fallback"
    # 四臂不是同一对数字抄四次。不断言哪一臂更高。
    metric_pairs = {(row["recall_at_k"], row["mrr"]) for row in body["rows"]}
    assert len(metric_pairs) > 1
    for row in body["rows"][:3]:
        assert row["observed_retrieval_mode"] == row["arm"]
        assert row["observed_rerank_mode"] == "none"


def test_arm_table_repeatable(tmp_path: Path) -> None:
    first = tmp_path / "a"
    second = tmp_path / "b"
    assert _run_cli(first, pin="same-pin").returncode == 0
    assert _run_cli(second, pin="same-pin").returncode == 0
    assert (first / "arm-table.json").read_bytes() == (second / "arm-table.json").read_bytes()
    assert (first / "arm-table.md").read_bytes() == (second / "arm-table.md").read_bytes()


def test_arm_table_has_no_pass_line(tmp_path: Path) -> None:
    out = tmp_path / "arm"
    assert _run_cli(out, pin="l4-ev-01-test-pin").returncode == 0
    body, markdown = _load(out)
    blob = markdown + "\n" + json.dumps(body, ensure_ascii=False)
    for token in BANNED:
        assert token not in blob
    for estimate in FROZEN_POINT_ESTIMATES:
        assert estimate not in blob
    assert "counted_as_pass" not in blob
    assert body["replaces_frozen_baseline"] is False


def test_arm_table_records_head_pin(tmp_path: Path) -> None:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    out = tmp_path / "arm"
    proc = _run_cli(out, pin=None)
    assert proc.returncode == 0, proc.stderr
    body, _markdown = _load(out)
    assert body["code_pin"] == head


def test_checked_in_example_schema(tmp_path: Path) -> None:
    """示例文件只锁列与臂名。不把示例里的均值当成门槛。"""
    example_text = EXAMPLE.read_text(encoding="utf-8")
    example = json.loads(example_text)
    markdown = (EXAMPLE.parent / "arm-table.md").read_text(encoding="utf-8")
    assert [row["arm"] for row in example["rows"]] == list(ARMS)
    assert example["level"] == "smoke"
    assert example["replaces_frozen_baseline"] is False
    assert example["neural_rerank_env"] == "0"
    assert HEADER in markdown
    blob = markdown + "\n" + example_text
    for token in BANNED:
        assert token not in blob
    for estimate in FROZEN_POINT_ESTIMATES:
        assert estimate not in blob
    out = tmp_path / "arm"
    assert _run_cli(out, pin="l4-ev-01-test-pin").returncode == 0
    fresh, _fresh_md = _load(out)
    assert [row["arm"] for row in fresh["rows"]] == [row["arm"] for row in example["rows"]]
    assert fresh["gold_sha256"] == example["gold_sha256"]
    assert fresh["k"] == example["k"]
    assert fresh["n"] == example["n"]


def test_refuses_frozen_output_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="neural-rerank"):
        run_arm_metric_table(
            gold_path=FIXTURE,
            out_dir=ROOT / "docs" / "evidence" / "neural-rerank",
            code_pin="x",
        )
    before = SUMMARY.read_bytes()
    with pytest.raises(SystemExit) as caught:
        main([
            "arm-table",
            "--gold",
            "tests/eval/fixtures/l4_ev_01_arm_gold.json",
            "--out",
            "docs/evidence/neural-rerank",
            "--pin",
            "x",
        ])
    assert caught.value.code == 1
    assert SUMMARY.read_bytes() == before
    assert not (tmp_path / "arm-table.json").exists()


def test_refuses_protected_gold(tmp_path: Path) -> None:
    gold = ROOT / "data" / "eval" / "gold.json"
    before = gold.read_bytes()
    with pytest.raises(ValueError, match="gold.json"):
        run_arm_metric_table(
            gold_path=gold,
            out_dir=tmp_path / "out",
            code_pin="x",
        )
    with pytest.raises(ValueError, match="x1"):
        run_arm_metric_table(
            gold_path=ROOT / "data" / "exp" / "x1" / "questions.json",
            out_dir=tmp_path / "out",
            code_pin="x",
        )
    assert gold.read_bytes() == before
    assert not (tmp_path / "out").exists()


def test_empty_pin_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="code_pin"):
        run_arm_metric_table(
            gold_path=FIXTURE,
            out_dir=tmp_path / "out",
            code_pin="  ",
        )


def test_frozen_baseline_sha_matches_prereg() -> None:
    prereg = PREREG.read_text(encoding="utf-8")
    listed = (
        "baseline_summary_sha256: "
        "8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526"
    )
    assert listed in prereg
    summary_sha = hashlib.sha256(SUMMARY.read_bytes()).hexdigest()
    assert summary_sha == FROZEN_SHA256["docs/evidence/neural-rerank/summary.json"]
    per_query_sha = hashlib.sha256(PER_QUERY.read_bytes()).hexdigest()
    assert per_query_sha == FROZEN_SHA256["docs/evidence/neural-rerank/per-query.json"]
    for rel, digest in FROZEN_SHA256.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest


def test_retrieval_constants_unchanged() -> None:
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert RRF_K == 60
    assert NEURAL_RERANK_K == 10
