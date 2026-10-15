"""L4-C-04: 成立 patch 实验的事前判据与 manifest。未开跑,不打分,不改冻结地板。"""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from freshlatch.eval.__main__ import main
from freshlatch.eval.patch_events_construct import (
    STRATA,
    _alternate,
    _take_slot,
    construct_from_pins,
    load_claims,
)
from freshlatch.eval.patch_establishment import (
    FALSE_POSITIVE_IDS,
    FROZEN_CORPUS_REL,
    STOP_IDS,
    banned_needles,
    build_scaffold,
    experiment_corpus_sha256,
    manifest_field_line,
    require_prereg,
    validate_scaffold,
    write_scaffold,
)
from freshlatch.models import DEFAULT_MODEL, NLI_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.checksum import normalize_newlines, sha256_hex

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "evidence" / "patch-establishment"
PREREG = EVIDENCE / "PREREG.md"
RESULT = EVIDENCE / "RESULT.md"
MANIFEST = EVIDENCE / "manifest.json"
MEASUREMENT = EVIDENCE / "measurement.json"
LOCKED_FALSE_POSITIVE = (
    "FP-UNMEASURED",
    "FP-B04",
    "FP-REJUDGE",
    "FP-SECOND-Y",
    "FP-L5",
    "FP-SUPERIOR",
    "FP-FLOORS",
    "FP-SESOI",
    "FP-NULL-AS-ZERO",
)
LOCKED_STOP = (
    "STOP-UNRUN",
    "STOP-FAIL",
    "STOP-PASS",
    "STOP-SAME-YARDSTICK",
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
    "docs/evidence/patch-events/PREREG-Y.md":
        "0381aa4fd3f1247f5d242a16c9151571292f765bb90be182946248def59cc4c4",
    "data/eval/gold.json":
        "28b8b88c41fb2a89794efe063de2948605f513ca10701cfc081c4ad144a939c2",
    "data/eval/guard_should.json":
        "63144c205f02ebbde88b9dd95217dfc9a1d69f6813590d1dd4818481d50022de",
    "data/eval/cite_sentence.json":
        "7b299a0bce8589bc2fd810a706572be27b4409ab03bc8a6c6b4d8024ee65bc94",
    "data/eval/temporal_new_over_old.json":
        "3a1b959a6aa63b89d10fa883982c11b7b7234aacdb537d754a1587010e40c8a0",
    "data/exp/x1/questions.json":
        "2cd7c5fb1e14859049c148e4dafc95b4d3c0abb4fa1080965dcc57b0d57c73fe",
}
FROZEN_POINT_ESTIMATES = (
    "0.3333333333333333",
    "0.9732142857142857",
    "0.8381855867346939",
    "0.42857142857142855",
    "0.0927152317880795",
)
NEW_TEXT = (
    PREREG,
    RESULT,
    MANIFEST,
    MEASUREMENT,
    ROOT / "src" / "freshlatch" / "eval" / "patch_establishment.py",
    ROOT / "src" / "freshlatch" / "eval" / "__main__.py",
    ROOT / "tasks" / "L4-C-04.md",
    Path(__file__),
)


def _sha_lf(path: Path) -> str:
    return sha256_hex(normalize_newlines(path.read_bytes(), "lf"))


def _negated(line: str) -> bool:
    return any(token in line for token in ("不得", "禁止", "不是"))


def test_prereg_locks_criteria_manifest_and_unchanged_arm() -> None:
    text = PREREG.read_text(encoding="utf-8")
    require_prereg(text)
    assert manifest_field_line() in text
    assert LOCKED_FALSE_POSITIVE == FALSE_POSITIVE_IDS
    assert LOCKED_STOP == STOP_IDS
    for item in LOCKED_FALSE_POSITIVE + LOCKED_STOP:
        assert item in text
    assert "不改默认臂" in text
    assert "不改 floors" in text
    assert "PRODUCTION_RETRIEVAL_MODE" in text
    assert "hybrid+rerank" in text
    assert "本页不发明 SESOI" in text
    assert "numeric_line=unregistered" in text
    assert "Amendment-01" in text
    assert "registered:interval_gt0" in text
    assert "比较 A" in text
    assert "n=100" in text
    assert "sesoi=null" in text
    assert "不得把该线叫做 SESOI" in text
    assert "second_formal_y=false" in text
    assert "STOP-SAME-YARDSTICK" in text
    assert "不得称优于 RARR·KPR" in text
    assert "不得标产品 L5" in text
    assert "不得把历史结果丙改判为乙" in text
    assert "docs/evidence/patch-establishment/" in text
    assert "Phoenix-" not in text


def test_result_stub_stays_unmeasured() -> None:
    text = RESULT.read_text(encoding="utf-8")
    assert "run_status=unrun" in text
    assert "measurement_status=unmeasured" in text
    assert "counted_as_pass=false" in text
    assert "本页不发明 SESOI" in text
    assert "不得称优于 RARR·KPR" in text
    assert "不得标产品 L5" in text
    assert "不得把历史结果丙改判为乙" in text
    assert "不改默认臂" in text
    assert "不改 floors" in text
    assert "夹具绿不是结果乙" in text
    assert "docs/evidence/patch-establishment/" in text
    for needle in banned_needles():
        assert needle not in text


def test_docs_and_tests_omit_banned_needles() -> None:
    needles = banned_needles()
    roots = (ROOT / "docs", ROOT / "tests", ROOT / "src", ROOT / "tasks")
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix.lower() not in {".md", ".py"}:
                continue
            body = path.read_text(encoding="utf-8")
            for needle in needles:
                assert needle not in body, path


def test_new_pages_keep_superiority_and_l5_negated() -> None:
    pages = (PREREG, RESULT, ROOT / "tasks" / "L4-C-04.md")
    for path in pages:
        for line in path.read_text(encoding="utf-8").splitlines():
            if any(token in line for token in ("优于 RARR", "优于 KPR", "结果乙", "L5")):
                assert _negated(line), line


def test_committed_scaffold_is_unmeasured_and_frozen_bytes_hold(tmp_path: Path) -> None:
    before = {rel: _sha_lf(ROOT / rel) for rel in FROZEN_SHA256}
    manifest, measurement = build_scaffold(ROOT)
    write_scaffold(out_dir=tmp_path / "out", root=ROOT)
    after = {rel: _sha_lf(ROOT / rel) for rel in FROZEN_SHA256}
    assert before == after == FROZEN_SHA256
    committed_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    committed_measurement = json.loads(MEASUREMENT.read_text(encoding="utf-8"))
    fresh_manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
    fresh_measurement = json.loads((tmp_path / "out" / "measurement.json").read_text(encoding="utf-8"))
    assert committed_manifest == fresh_manifest == manifest
    assert committed_measurement == fresh_measurement == measurement
    assert measurement["run_status"] == "unrun"
    assert measurement["measurement_status"] == "unmeasured"
    assert measurement["establishment"]["status"] == "unmeasured"
    assert measurement["establishment"]["counted_as_pass"] is False
    assert measurement["establishment"]["sesoi"] is None
    assert measurement["establishment"]["numeric_line"] == "unregistered"
    assert measurement["establishment"]["n"] is None
    assert measurement["establishment"]["k"] is None
    assert measurement["establishment"]["ci95_low"] is None
    assert measurement["criteria"]["numeric_line"] == "registered:interval_gt0"
    assert measurement["criteria"]["sesoi"] is None
    assert manifest["criteria"]["numeric_line"] == "registered:interval_gt0"
    assert manifest["criteria"]["sesoi"] is None
    assert manifest["establishment"]["numeric_line"] == "unregistered"
    corpus = manifest["sources"]["experiment_corpus"]
    assert corpus["path"] == FROZEN_CORPUS_REL
    assert corpus["role"] == "frozen_corpus_unrun"
    assert corpus["measurement_status"] == "unmeasured"
    assert corpus["counts_as_establishment"] is False
    assert corpus["sha256"] == experiment_corpus_sha256(ROOT)
    assert measurement["establishment"]["false_accept_rate"] is None
    assert measurement["establishment"]["point_estimate"] is None
    assert measurement["firewall"]["product_l5"] is False
    assert measurement["firewall"]["second_formal_y"] is False
    assert measurement["firewall"]["b04_counts_as_establishment"] is False
    assert measurement["firewall"]["historical_result_y"] == "丙"
    assert measurement["firewall"]["historical_cells_rewritten"] is False
    assert measurement["firewall"]["claims_rarr_kpr_superiority"] is False
    assert measurement["production_retrieval_mode"] == "hybrid+rerank"
    assert measurement["replaces_frozen_baseline"] is False
    assert measurement["conclusion_dir"] == "docs/evidence/patch-establishment/"
    assert manifest["retrieval"]["mode"] == "hybrid+rerank"
    assert manifest["retrieval"]["weight_sha256"] is None
    assert manifest["model"]["generator_model"] == DEFAULT_MODEL == "qwen-flash"
    assert manifest["model"]["nli_model"] == NLI_MODEL == (
        "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    )
    assert manifest["model"]["generator_sha256"] is None
    assert manifest["model"]["nli_sha256"] is None
    assert manifest["model"]["temperature"] is None
    assert manifest["model"]["seed"] is None
    assert manifest["decoding"]["model"] is None
    assert manifest["establishment"]["n"] is None
    assert manifest["establishment"]["sesoi"] is None
    assert manifest["sources"]["b04_fixtures"]["counts_as_establishment"] is False
    assert manifest["sources"]["result_y"]["sha256"] == FROZEN_SHA256[
        "docs/evidence/patch-events/RESULT-Y.md"
    ]
    assert manifest["sources"]["quality_gate_prereg"]["sha256"] == FROZEN_SHA256[
        "docs/evidence/quality-gate/PREREG.md"
    ]
    body = MEASUREMENT.read_text(encoding="utf-8") + MANIFEST.read_text(encoding="utf-8")
    for token in FROZEN_POINT_ESTIMATES:
        assert token not in body
    for needle in banned_needles():
        assert needle not in body


def test_validate_rejects_invented_sesoi_scores_and_l5() -> None:
    manifest, measurement = build_scaffold(ROOT)
    cases = []
    scored = deepcopy(manifest)
    scored["establishment"]["sesoi"] = 0.05
    cases.append(scored)
    passed = deepcopy(manifest)
    passed["establishment"]["counted_as_pass"] = True
    cases.append(passed)
    filled = deepcopy(manifest)
    filled["establishment"]["point_estimate"] = 0.2
    cases.append(filled)
    marked = deepcopy(manifest)
    marked["establishment"]["status"] = "established"
    cases.append(marked)
    l5 = deepcopy(manifest)
    l5["firewall"]["product_l5"] = True
    cases.append(l5)
    rejudged = deepcopy(manifest)
    rejudged["firewall"]["historical_cells_rewritten"] = True
    cases.append(rejudged)
    second = deepcopy(manifest)
    second["firewall"]["second_formal_y"] = True
    cases.append(second)
    superior = deepcopy(manifest)
    superior["firewall"]["claims_rarr_kpr_superiority"] = True
    cases.append(superior)
    b04 = deepcopy(manifest)
    b04["firewall"]["b04_counts_as_establishment"] = True
    cases.append(b04)
    named = deepcopy(manifest)
    named["criteria"]["sesoi"] = 0.05
    cases.append(named)
    unregistered = deepcopy(manifest)
    unregistered["criteria"]["numeric_line"] = "unregistered"
    cases.append(unregistered)
    scored_line = deepcopy(manifest)
    scored_line["establishment"]["numeric_line"] = "registered:interval_gt0"
    cases.append(scored_line)
    cleared = deepcopy(manifest)
    cleared["sources"]["experiment_corpus"]["path"] = None
    cleared["sources"]["experiment_corpus"]["sha256"] = None
    cases.append(cleared)
    pointed = deepcopy(manifest)
    pointed["sources"]["experiment_corpus"]["path"] = "data/corpus/pe_v2"
    cases.append(pointed)
    x1 = deepcopy(manifest)
    x1["sources"]["experiment_corpus"]["path"] = "data/exp/x1"
    cases.append(x1)
    forged = deepcopy(manifest)
    forged["sources"]["experiment_corpus"]["sha256"] = "0" * 64
    cases.append(forged)
    for broken in cases:
        with pytest.raises(ValueError):
            validate_scaffold(broken, measurement, root=ROOT)
    ran = deepcopy(measurement)
    ran["run_status"] = "ran"
    with pytest.raises(ValueError, match="run_status"):
        validate_scaffold(manifest, ran, root=ROOT)


def test_writer_rejects_protected_dirs(tmp_path: Path) -> None:
    blocked = (
        "docs/evidence/patch-events",
        "docs/evidence/quality-gate",
        "docs/evidence/neural-rerank",
        "docs/evidence/temporal-trained-retrieval",
        "data/exp/x1",
        "data/eval",
    )
    for rel in blocked:
        with pytest.raises(ValueError):
            write_scaffold(out_dir=Path(rel), root=ROOT)
    weak = PREREG.read_text(encoding="utf-8").replace("不改默认臂", "默认臂另说")
    with pytest.raises(ValueError, match="锁句"):
        require_prereg(weak)


def test_production_arm_and_base_untouched() -> None:
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    base = (ROOT / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert "patch-establishment" not in base
    prereg = (ROOT / "docs" / "evidence" / "quality-gate" / "PREREG.md").read_text(encoding="utf-8")
    assert "owner_freeze: confirmed" in prereg or "owner_freeze: pending" in prereg
    assert _sha_lf(ROOT / "docs" / "evidence" / "quality-gate" / "PREREG.md") == FROZEN_SHA256[
        "docs/evidence/quality-gate/PREREG.md"
    ]


def test_cli_writes_unmeasured_scaffold(tmp_path: Path) -> None:
    out = tmp_path / "cli-out"
    code = main([
        "patch-establishment",
        "--out",
        str(out),
        "--root",
        str(ROOT),
    ])
    assert code is None
    body = json.loads((out / "measurement.json").read_text(encoding="utf-8"))
    assert body["run_status"] == "unrun"
    assert body["establishment"]["sesoi"] is None
    assert body["firewall"]["product_l5"] is False


def test_cli_rejects_patch_events(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main([
            "patch-establishment",
            "--out",
            "docs/evidence/patch-events",
            "--root",
            str(ROOT),
        ])
    assert exc.value.code == 1
    assert "patch-events" in capsys.readouterr().err


def test_subprocess_cli(tmp_path: Path) -> None:
    out = tmp_path / "sub"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "freshlatch.eval",
            "patch-establishment",
            "--out",
            str(out),
            "--root",
            str(ROOT),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "run_status=unrun" in proc.stdout
    assert "product_l5=false" in proc.stdout
    for needle in banned_needles():
        assert needle not in proc.stdout


def _leftover_pins() -> list[dict[str, str]]:
    """按层内 claim_id 字典序、余数槽和未改算子重放名单。"""
    route = json.loads(
        (ROOT / "docs/evidence/patch-events/SPLIT-pe-v2-route-y.json").read_text(encoding="utf-8")
    )
    excluded = {str(row["claim_id"]) for row in route["n400"]} | {
        str(row["claim_id"]) for row in route["pilot"]
    }
    docket = json.loads((ROOT / "data/pe_v2_docket.json").read_text(encoding="utf-8"))
    by_dim = {name: set() for name in STRATA}
    for row in docket["claims"]:
        cid = str(row["claim_id"])
        if cid in excluded:
            continue
        by_dim[str(row["dimension"])].add(cid)
    views = [
        view
        for view in load_claims(ROOT / "data/pe_v2_docket.json", ROOT / "data/corpus/pe_v2")
        if view.claim_id not in excluded
    ]
    slots = _alternate(13, 12)
    pins: list[dict[str, str]] = []
    for name in STRATA:
        pool = [view for view in views if view.claim_id in by_dim[name]]
        bad_index = 0
        structural_skip: set[str] = set()
        for gold in slots:
            edit, pool, bad_index, _skipped = _take_slot(
                pool, name, gold, bad_index, structural_skip
            )
            if edit is None:
                continue
            pins.append(
                {
                    "claim_id": edit.record["claim_id"],
                    "edit_type": name,
                    "construction_gold": edit.record["construction_gold"],
                }
            )
    return pins


def test_frozen_corpus_is_disjoint_unrun_and_rebuilt_offline() -> None:
    prereg = PREREG.read_text(encoding="utf-8")
    assert "- [x] 实验语料路径与 sha256 写入 manifest `sources.experiment_corpus`" in prereg
    assert "- [x] 主人写激活批注" in prereg
    assert "built_n=91" in prereg
    assert "gap_n=9" in prereg
    assert "目标 n=100 未满额建成" in prereg
    assert "- [x] 生成器 `generator_model` 与 NLI `nli_model` 写入 manifest" in prereg
    assert "- [ ] 生成器 `generator_sha256` 与 NLI `nli_sha256` 写入 manifest" in prereg
    assert "qwen-flash" in prereg
    assert "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7" in prereg
    assert "- [ ] 主人明文「跑」" in prereg
    base = ROOT / FROZEN_CORPUS_REL
    split = json.loads((base / "SPLIT.json").read_text(encoding="utf-8"))
    assert split["second_formal_y"] is False
    assert split["run_status"] == "unrun"
    assert split["measurement_status"] == "unmeasured"
    assert split["counts_as_establishment"] is False
    assert split["role"] == "frozen_corpus_unrun"
    assert split["target_n"] == 100
    assert split["remainder_rule"] == "correct=floor(layer/2); bad=ceil(layer/2)"
    formal = split["formal"]
    bare = [
        {
            "claim_id": row["claim_id"],
            "edit_type": row["edit_type"],
            "construction_gold": row["construction_gold"],
        }
        for row in formal
    ]
    assert bare == _leftover_pins()
    route = json.loads(
        (ROOT / "docs/evidence/patch-events/SPLIT-pe-v2-route-y.json").read_text(encoding="utf-8")
    )
    banned = {str(row["claim_id"]) for row in route["n400"]} | {
        str(row["claim_id"]) for row in route["pilot"]
    }
    ids = [row["claim_id"] for row in formal]
    assert set(ids).isdisjoint(banned)
    assert split["built_n"] == len(ids) == 91
    assert split["gap_n"] == 100 - len(ids) == 9
    assert split["gap_n"] > 0
    assert split["by_stratum"]["删除"]["bad_target"] == 13
    assert split["by_stratum"]["删除"]["bad"] < 13
    provenance = json.loads((base / "PROVENANCE.json").read_text(encoding="utf-8"))
    prov_by = {row["claim_id"]: row for row in provenance["claims"]}
    for cid in ids:
        row = prov_by[cid]
        for folder, key in (("t0", "source_t0_file"), ("t1", "source_t1_file")):
            copied = (base / "corpus" / folder / f"{cid}.md").read_bytes()
            source = (ROOT / row[key]).read_bytes()
            assert copied == source
    records = construct_from_pins(
        base / "docket.json",
        base / "corpus",
        bare,
    )
    lines = [
        json.loads(line)
        for line in (base / "CONSTRUCTED.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert lines == records
    blob = (base / "CONSTRUCTED.jsonl").read_text(encoding="utf-8")
    for token in ("compare_primary", "point_estimate", "false_accept_rate", "ci95_low", "sesoi"):
        assert token not in blob
    for row in records:
        assert "score" not in row
        assert "decision" not in row
