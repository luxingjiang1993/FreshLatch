"""L4-C-01: 训练/时序检索新预注册。锁 schema,不打分,不改冻结地板。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.eval.__main__ import main
from freshlatch.eval.temporal_trained import (
    ARM_MRAG_UNTRAINED,
    ARM_TEMPORAL_TRAINED,
    CORPUS_REL,
    K,
    METRICS,
    PREREG_REL,
    banned_claim,
    corpus_sha256,
    write_measurement,
)
from freshlatch.runner import RETRIEVAL_SWITCH_MODES, RunContext
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    InMemoryStore,
)
from freshlatch.store.temporal_arm import (
    TEMPORAL_TRAINED_MODE,
    TemporalTrainedUnmeasured,
)
from freshlatch.store.checksum import normalize_newlines, sha256_hex
from freshlatch.store.sqlite_store import SQLiteStore

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / PREREG_REL
CORPUS = ROOT / CORPUS_REL
MEASUREMENT = ROOT / "docs" / "evidence" / "temporal-trained-retrieval" / "measurement.json"
NEEDLE = banned_claim()
NEW_TEXT_PATHS = (
    PREREG,
    CORPUS,
    MEASUREMENT,
    ROOT / "src" / "freshlatch" / "eval" / "temporal_trained.py",
    ROOT / "src" / "freshlatch" / "eval" / "__main__.py",
    ROOT / "src" / "freshlatch" / "runner.py",
    ROOT / "src" / "freshlatch" / "store" / "base.py",
    ROOT / "src" / "freshlatch" / "store" / "temporal_arm.py",
    ROOT / "src" / "freshlatch" / "store" / "sqlite_store.py",
    # DOC-TREE-C(#729):票正文 L4-C-01.md 随根 tasks/** 考古迁入 archive。
    ROOT / "docs" / "_archive" / "2026-10" / "tasks" / "L4-C-01.md",
    Path(__file__),
)
FROZEN_SHA256 = {
    "docs/evidence/neural-rerank/per-query.json":
        "2c4df07089eeb33ab5887c588a1907bc3caa5447f9bcdde09280d6b8555f1b4c",
    "docs/evidence/neural-rerank/summary.json":
        "8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526",
    "docs/evidence/quality-gate/PREREG.md":
        "3d01f8a9481effab0506762853789d568451701d6e438b8615dc5a696af7f72c",
    "docs/evidence/patch-events/RESULT-Y.md":
        "b58d7023b7f7359ec4fae1c32673efaaa56f969d184754f69890b2ec2fc22705",
    "data/eval/gold.json":
        "28b8b88c41fb2a89794efe063de2948605f513ca10701cfc081c4ad144a939c2",
    "data/eval/guard_should.json":
        "63144c205f02ebbde88b9dd95217dfc9a1d69f6813590d1dd4818481d50022de",
    "data/eval/cite_sentence.json":
        "7b299a0bce8589bc2fd810a706572be27b4409ab03bc8a6c6b4d8024ee65bc94",
    "data/eval/temporal_new_over_old.json":
        "3a1b959a6aa63b89d10fa883982c11b7b7234aacdb537d754a1587010e40c8a0",
}
FROZEN_POINT_ESTIMATES = (
    "0.3333333333333333",
    "0.9732142857142857",
    "0.8381855867346939",
)


def _sha_lf(path: Path) -> str:
    return sha256_hex(normalize_newlines(path.read_bytes(), "lf"))


def _chunk() -> Chunk:
    return Chunk(
        doc_id="demo-art-1",
        chunk_id="demo-art-1::v2024@2024-01-01",
        clause_id="v2024",
        title="演示",
        text="alpha-rate-token 2024",
        source_type="public",
        as_of="T1",
        doc_version="v2024",
        checksum="c01",
        tokens=8,
    )


def test_prereg_declares_metrics_arms_and_frozen_relation() -> None:
    text = PREREG.read_text(encoding="utf-8")
    assert "事前指标" in text
    for metric in METRICS:
        assert metric in text
    assert "temporal_trained" in text
    assert "mrag_untrained" in text
    assert "replaces_frozen_baseline=false" in text
    assert "T1-new-over-old-accuracy" in text
    assert "R1-recall@10" in text
    assert "R1-mrr@10" in text
    assert "per-query.json" in text
    assert "不改写注册 T1 的 `value=`" in text
    assert "不改写注册 R1 的 `value=`" in text
    assert "counted_as_pass=false" in text
    assert "data/temporal-trained/v1/corpus.json" in text
    assert "data/exp/x1/" in text
    digest = corpus_sha256(CORPUS.read_bytes())
    assert f"corpus_sha256: {digest}" in text
    assert NEEDLE not in text


def test_new_files_omit_unverified_claim() -> None:
    for path in NEW_TEXT_PATHS:
        assert path.is_file(), path
        assert NEEDLE not in path.read_text(encoding="utf-8"), path


def test_measurement_does_not_score_or_touch_frozen_files(tmp_path: Path) -> None:
    before = {rel: _sha_lf(ROOT / rel) for rel in FROZEN_SHA256}
    out = tmp_path / "out"
    payload = write_measurement(out_dir=out, corpus_path=CORPUS)
    after = {rel: _sha_lf(ROOT / rel) for rel in FROZEN_SHA256}
    assert before == after
    assert before == FROZEN_SHA256
    assert payload["replaces_frozen_baseline"] is False
    assert payload["counted_as_pass"] is False
    assert payload["production_retrieval_mode"] == "hybrid+rerank"
    assert payload["k"] == K
    assert payload["n"] == 2
    assert payload["level"] == "schema"
    assert [row["arm"] for row in payload["arms"]] == [
        ARM_TEMPORAL_TRAINED,
        ARM_MRAG_UNTRAINED,
    ]
    for row in payload["arms"]:
        for metric in METRICS:
            assert row[metric] is None
        assert row["measurement_status"] == "unmeasured"
        assert row["production_default"] is False
    body = (out / "measurement.json").read_text(encoding="utf-8")
    for token in FROZEN_POINT_ESTIMATES:
        assert token not in body
    assert "per-query.json" not in (out / "measurement.json").name
    committed = json.loads(MEASUREMENT.read_text(encoding="utf-8"))
    fresh = json.loads((out / "measurement.json").read_text(encoding="utf-8"))
    assert committed == fresh


def test_weights_file_still_unmeasured(tmp_path: Path) -> None:
    weights = tmp_path / "weights.bin"
    weights.write_bytes(b"not-a-model")
    payload = write_measurement(
        out_dir=tmp_path / "out",
        corpus_path=CORPUS,
        weights_path=weights,
    )
    trained = payload["arms"][0]
    assert trained["arm"] == ARM_TEMPORAL_TRAINED
    assert trained["reason"] == "scorer_not_landed"
    assert trained["Recall@k"] is None
    assert payload["weights_present"] is True


def test_corpus_and_output_reject_protected_paths(tmp_path: Path) -> None:
    blocked_corpus = Path("data/exp/x1/questions.json")
    with pytest.raises(ValueError, match="x1"):
        write_measurement(out_dir=tmp_path / "out", corpus_path=blocked_corpus)
    with pytest.raises(ValueError, match="neural-rerank"):
        write_measurement(
            out_dir=Path("docs/evidence/neural-rerank"),
            corpus_path=CORPUS,
        )
    with pytest.raises(ValueError, match="quality-gate"):
        write_measurement(
            out_dir=Path("docs/evidence/quality-gate"),
            corpus_path=CORPUS,
        )


def test_production_arm_unchanged_and_switch_rejects_temporal() -> None:
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert TEMPORAL_TRAINED_MODE not in RETRIEVAL_SWITCH_MODES
    base = (ROOT / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    ctx = RunContext(store=InMemoryStore(), mode="online")
    with pytest.raises(ValueError, match="检索开关"):
        ctx.set_retrieval_switch(TEMPORAL_TRAINED_MODE)
    with pytest.raises(RuntimeError, match="生产路径"):
        ctx.arm_eval_retrieval_mode(TEMPORAL_TRAINED_MODE)


def test_eval_hook_returns_unmeasured_without_store_retrieve() -> None:
    class BoomStore(InMemoryStore):
        def retrieve(self, *args, **kwargs):
            raise AssertionError("temporal_trained 不得调用 store.retrieve")

    store = BoomStore()
    ctx = RunContext(store=store, mode="eval")
    ctx.arm_eval_retrieval_mode(TEMPORAL_TRAINED_MODE)
    result = ctx.try_retrieve("2021-06-01 适用的演示税率", top_k=10)
    assert isinstance(result, dict)
    assert result["temporal_trained_unmeasured"] is True
    assert result["measurement_status"] == "unmeasured"
    assert result["replaces_frozen_baseline"] is False
    assert result["evidence_ids"] == []
    assert ctx.events[-1]["retrieval_mode"] == TEMPORAL_TRAINED_MODE
    assert ctx.events[-1]["hits"] == 0


def test_default_retrieve_stays_on_production_path() -> None:
    store = InMemoryStore()
    store._chunks.append(_chunk())
    hits = store.retrieve("alpha-rate-token", top_k=5)
    assert isinstance(hits, list)
    assert store.last_retrieval_mode == "bm25"
    ctx = RunContext(store=store, mode="online")
    again = ctx.try_retrieve("alpha-rate-token", top_k=5)
    assert isinstance(again, list)
    assert ctx.events[-1]["retrieval_mode"] != TEMPORAL_TRAINED_MODE
    assert ctx.last_retrieval_manifest is None or "temporal_trained" not in str(
        ctx.last_retrieval_manifest
    )


def test_sqlite_bound_temporal_mode_refuses(tmp_path: Path) -> None:
    base = (ROOT / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    assert "temporal_trained" not in base
    sqlite = SQLiteStore(tmp_path / "c01.sqlite")
    sqlite.bind_eval_retrieval_mode(TEMPORAL_TRAINED_MODE)
    with pytest.raises(TemporalTrainedUnmeasured):
        sqlite.retrieve("税率", top_k=5)
    sqlite.bind_eval_retrieval_mode(None)
    assert sqlite.retrieve("税率", top_k=5) == []


def test_unknown_contrast_arm_is_not_executable() -> None:
    ctx = RunContext(store=InMemoryStore(), mode="eval")
    with pytest.raises(ValueError, match="未知 retrieval_mode"):
        ctx.arm_eval_retrieval_mode(ARM_MRAG_UNTRAINED)


def test_cli_writes_schema(tmp_path: Path) -> None:
    out = tmp_path / "cli-out"
    code = main([
        "temporal-prereg",
        "--corpus",
        "data/temporal-trained/v1/corpus.json",
        "--out",
        str(out),
    ])
    assert code is None
    body = json.loads((out / "measurement.json").read_text(encoding="utf-8"))
    assert body["replaces_frozen_baseline"] is False
    assert body["metrics"] == list(METRICS)


def test_cli_rejects_x1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([
            "temporal-prereg",
            "--corpus",
            "data/exp/x1/questions.json",
            "--out",
            str(tmp_path / "nope"),
        ])
    assert exc.value.code == 1
    assert "x1" in capsys.readouterr().err


def test_subprocess_cli(tmp_path: Path) -> None:
    out = tmp_path / "sub"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.eval",
            "temporal-prereg",
            "--corpus",
            "data/temporal-trained/v1/corpus.json",
            "--out",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "replaces_frozen_baseline=false" in proc.stdout
    assert NEEDLE not in proc.stdout
