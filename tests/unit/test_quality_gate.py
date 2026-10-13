"""QG-03 离线质量闸。夹具与假命中，不访问网络，不读付费密钥的值。"""

from __future__ import annotations

import ast
import inspect
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.eval import quality_gate as qg
from freshlatch.eval.quality_gate import (
    ContractError,
    PaidKeyRead,
    build_unregistered_rows,
    enforce_report,
    forbid_paid_env,
    parse_owner_freeze,
    parse_registered_segments,
    r1_no_regression,
    run_quality_gate,
    score_registered_segments,
)
from freshlatch.eval.retrieve_typed import compute_x1_fingerprints
from freshlatch.packs import repo_root

ROOT = repo_root()
PREREG = ROOT / "docs" / "evidence" / "quality-gate" / "PREREG.md"
SECRET = "sekret-should-not-leak"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["DASHSCOPE_API_KEY"] = SECRET + "-dash"
    env["DEEPSEEK_API_KEY"] = SECRET + "-deep"
    env["MOONSHOT_API_KEY"] = SECRET + "-moon"
    return subprocess.run(
        [sys.executable, "-m", "freshlatch.eval", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )


def _stdio(proc: subprocess.CompletedProcess[str]) -> tuple[str, str]:
    """Windows 上解码失败时 stdout/stderr 可能是 None。"""
    return proc.stdout or "", proc.stderr or ""


def test_parse_owner_freeze_one_line_only():
    text = "散文里 owner_freeze: pending 不算\nowner_freeze: confirmed\n"
    assert parse_owner_freeze(text) == "confirmed"
    assert parse_owner_freeze("owner_freeze: pending\nowner_freeze: confirmed\n") is None
    assert parse_owner_freeze("没有这一行\n") is None


def test_forbid_paid_env_blocks_read_without_returning_value(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", SECRET)
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET)
    monkeypatch.setenv("MOONSHOT_API_KEY", SECRET)
    with forbid_paid_env():
        with pytest.raises(PaidKeyRead) as got:
            os.getenv("DASHSCOPE_API_KEY")
        assert got.value.key == "DASHSCOPE_API_KEY"
        assert SECRET not in str(got.value)
        with pytest.raises(PaidKeyRead):
            os.environ["DEEPSEEK_API_KEY"]
        with pytest.raises(PaidKeyRead):
            "MOONSHOT_API_KEY" in os.environ
    assert os.environ["DASHSCOPE_API_KEY"] == SECRET


def test_cli_refuses_without_offline():
    proc = _run("quality-gate", "--prereg", str(PREREG))
    stdout, stderr = _stdio(proc)
    assert proc.returncode == 2
    assert "未设置 --offline" in stderr
    assert SECRET not in stdout + stderr
    assert "locked_gate=true" not in stdout


def test_cli_missing_prereg():
    proc = _run("quality-gate", "--offline", "--prereg", str(ROOT / "missing-prereg.md"))
    stdout, stderr = _stdio(proc)
    assert proc.returncode == 1
    assert "不存在" in stderr
    assert SECRET not in stdout + stderr


def test_owner_freeze_pending_is_not_locked(tmp_path, capsys):
    text = PREREG.read_text(encoding="utf-8")
    swapped = text.replace(
        "\nowner_freeze: confirmed\n",
        "\nowner_freeze: pending\n",
        1,
    )
    assert swapped != text
    path = tmp_path / "PREREG.md"
    path.write_text(swapped, encoding="utf-8")
    code = run_quality_gate(offline=True, prereg=str(path))
    err = capsys.readouterr().err
    assert code == 1
    assert "不是 confirmed" in err
    assert "锁定产品质量闸" in err


def test_fingerprint_mismatch(tmp_path, capsys):
    text = PREREG.read_text(encoding="utf-8")
    old = "config_sha256: 54736467729ccdc14aa1c9704908bf6f9dbc9292005488a92ae73edb23cfa2d6"
    flipped = old[:-1] + ("0" if old[-1] != "0" else "1")
    path = tmp_path / "PREREG.md"
    path.write_text(text.replace(old, flipped, 1), encoding="utf-8")
    code = run_quality_gate(offline=True, prereg=str(path))
    err = capsys.readouterr().err
    assert code == 1
    assert "指纹不一致" in err


def test_offline_command_marks_unregistered_and_compares_baseline(capsys, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", SECRET + "-dash")
    monkeypatch.setenv("DEEPSEEK_API_KEY", SECRET + "-deep")
    monkeypatch.setenv("MOONSHOT_API_KEY", SECRET + "-moon")
    import freshlatch.eval.control as control
    import freshlatch.eval.runner as runner
    import freshlatch.store.embeddings as embeddings
    import freshlatch.store.local_embed as local_embed
    import freshlatch.store.neural_rerank as neural_rerank

    def boom(*_args, **_kwargs):
        raise AssertionError("live 路径被调用")

    monkeypatch.setattr(runner, "run_gold", boom)
    monkeypatch.setattr(control, "run_control", boom)
    monkeypatch.setattr(control, "run_control_c", boom)
    monkeypatch.setattr(embeddings, "embed_texts", boom)
    monkeypatch.setattr(local_embed, "_load_model", boom)
    monkeypatch.setattr(neural_rerank, "_load_encoder", boom)

    code = run_quality_gate(offline=True, prereg=str(PREREG))
    captured = capsys.readouterr()
    assert code == 0, captured.err
    out = captured.out
    assert SECRET not in out + captured.err
    assert "arm=hybrid+rerank" in out
    assert "denominator=data/exp/x1/questions.json" in out
    assert "n_arm=224" in out
    assert "n_guardrail=43" in out
    assert "excluded_lexical_used=false" in out
    assert "paid_llm=false" in out
    assert "qg04=separate" in out
    assert "segment id=A1 status=unregistered" in out
    assert "segment id=G1-should-refuse status=unregistered" in out
    assert "segment id=T1-new-over-old status=unregistered" in out
    assert "status=pass" not in out
    assert "counted_as_pass=true" not in out
    assert "metric id=R1-recall@10 status=TBD value=0.9732142857142857" in out
    assert "metric id=R1-mrr@10 status=TBD value=0.8381855867346939" in out
    assert "0.7566609977324263" not in out
    for line in out.splitlines():
        if line.startswith("metric id=R1-recall@10") or line.startswith("metric id=R1-mrr@10"):
            assert "status=TBD" in line
            assert "r1_no_regression=true" in line
        elif line.startswith("metric id="):
            assert "status=TBD" in line
            assert "r1_no_regression" not in line
    assert "metric id=guardrail-0hit status=TBD value=unavailable" in out
    assert "metric id=conflict-pair-ordering status=TBD value=0.3333333333333333" in out
    assert "metric id=multi-hop-full-hit status=TBD value=0.7555555555555555" in out
    assert "trap_smoke id=trap-smoke status=not_counted" in out
    assert "in_denominator=false" in out
    assert "source=frozen-per-query-replay" in out


def test_module_entrypoint_matches_command_shape():
    """三条正式金标已在场时，离线闸仍退出码 0：三段 unregistered，file_present=true，未记通过。"""
    present = (
        "data/eval/guard_should.json",
        "data/eval/cite_sentence.json",
        "data/eval/temporal_new_over_old.json",
    )
    for rel in present:
        assert (ROOT / rel).is_file(), rel
    proc = _run(
        "quality-gate",
        "--offline",
        "--prereg",
        "docs/evidence/quality-gate/PREREG.md",
    )
    stdout, stderr = _stdio(proc)
    assert proc.returncode == 0, stderr
    assert (
        "segment id=G1-should-refuse status=unregistered "
        "file=data/eval/guard_should.json file_present=true counted_as_pass=false"
    ) in stdout
    assert (
        "segment id=A1 status=unregistered "
        "file=data/eval/cite_sentence.json file_present=true counted_as_pass=false"
    ) in stdout
    assert (
        "segment id=T1-new-over-old status=unregistered "
        "file=data/eval/temporal_new_over_old.json file_present=true counted_as_pass=false"
    ) in stdout
    assert "counted_as_pass=false" in stdout
    assert "counted_as_pass=true" not in stdout
    assert "status=pass" not in stdout
    assert SECRET not in stdout + stderr


def test_lf_fingerprint_matches_crlf_bytes(tmp_path):
    """同一正文的 CRLF 检出，按 lf 口径必须对上 LF 指纹。"""
    corpus = tmp_path / "corpus" / "t0"
    traps = tmp_path / "traps" / "t1"
    corpus.mkdir(parents=True)
    traps.mkdir(parents=True)
    files = [
        corpus / "a.md",
        traps / "b.md",
        tmp_path / "questions.json",
        tmp_path / "config.json",
    ]
    lf_payloads = [
        "甲行\n乙行\n".encode("utf-8"),
        "丙\n".encode("utf-8"),
        b'{"queries":[]}\n',
        b'{"top_k":10}\n',
    ]
    for path, payload in zip(files, lf_payloads):
        path.write_bytes(payload)
    lf = compute_x1_fingerprints(
        corpus=tmp_path / "corpus",
        traps=tmp_path / "traps",
        questions=tmp_path / "questions.json",
        config=tmp_path / "config.json",
        newline="lf",
    )
    for path, payload in zip(files, lf_payloads):
        path.write_bytes(payload.replace(b"\n", b"\r\n"))
    crlf = compute_x1_fingerprints(
        corpus=tmp_path / "corpus",
        traps=tmp_path / "traps",
        questions=tmp_path / "questions.json",
        config=tmp_path / "config.json",
        newline="lf",
    )
    raw = compute_x1_fingerprints(
        corpus=tmp_path / "corpus",
        traps=tmp_path / "traps",
        questions=tmp_path / "questions.json",
        config=tmp_path / "config.json",
    )
    assert crlf == lf
    assert raw["config_sha256"] != lf["config_sha256"]
    assert raw["corpus_aggregate_sha256"] != lf["corpus_aggregate_sha256"]


def test_live_invocation_refused(capsys):
    code = run_quality_gate(
        offline=True,
        prereg=str(PREREG),
        live_invocation="run",
    )
    err = capsys.readouterr().err
    assert code == 2
    assert "拒绝 live 路径: run" in err
    code_script = run_quality_gate(
        offline=True,
        prereg=str(PREREG),
        live_invocation="scripts/run_retrieve_x1.py",
    )
    err_script = capsys.readouterr().err
    assert code_script == 2
    assert "run_retrieve_x1.py" in err_script


def test_guardrail_fixture_stays_tbd_even_when_all_fail(capsys):
    hits = [[SimpleNamespace(as_of="T0")] for _ in range(qg.N_GUARDRAIL)]
    code = run_quality_gate(offline=True, prereg=str(PREREG), guardrail_hits=hits)
    out = capsys.readouterr().out
    assert code == 0
    assert "metric id=guardrail-0hit status=TBD value=0.0" in out
    assert "source=guardrail_pass" in out
    assert "counted_as_pass=false" in out
    assert "status=pass" not in out


def test_replay_mismatch_is_contract_break(capsys):
    code = run_quality_gate(
        offline=True,
        prereg=str(PREREG),
        replay_baseline=(0.0, 0.0),
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "确定性回放与冻结基线描述不一致" in captured.err
    assert "locked_gate=true" not in captured.out


def test_present_cite_file_still_unregistered(tmp_path):
    dest = tmp_path / "data" / "eval"
    dest.mkdir(parents=True)
    (dest / "cite_sentence.json").write_text("{}\n", encoding="utf-8")
    rows = build_unregistered_rows(tmp_path)
    a1 = next(row for row in rows if row.row_id == "A1")
    assert a1.status == "unregistered"
    assert a1.counted_as_pass is False
    assert "file_present=true" in a1.line
    with pytest.raises(ContractError):
        enforce_report(rows)


def test_missing_a1_cannot_exit_zero(tmp_path):
    rows = [row for row in build_unregistered_rows(tmp_path) if row.row_id != "A1"]
    with pytest.raises(ContractError):
        enforce_report(rows)


def test_unregistered_schema_field_tables():
    """字段表锁路径与列名。不发明 G1/A1/T1 的绝对百分数。"""
    by_id = {spec["id"]: spec for spec in qg.UNREGISTERED_SEGMENTS}
    assert tuple(by_id) == ("G1-should-refuse", "A1", "T1-new-over-old")
    assert by_id["G1-should-refuse"]["file"] == "data/eval/guard_should.json"
    assert by_id["A1"]["file"] == "data/eval/cite_sentence.json"
    assert by_id["T1-new-over-old"]["file"] == "data/eval/temporal_new_over_old.json"
    assert qg.GOLD_META_FIELDS == ("status", "human_row_review", "reviewer")
    assert qg.GOLD_META_STATUSES == frozenset({"draft", "final"})
    for spec in qg.UNREGISTERED_SEGMENTS:
        assert spec["meta_fields"] == qg.GOLD_META_FIELDS
    assert by_id["G1-should-refuse"]["item_fields"] == qg.GUARD_SHOULD_ITEM_FIELDS
    assert by_id["G1-should-refuse"]["item_fields"] == (
        "id",
        "policy_id",
        "label",
        "text",
        "source_refs",
    )
    assert by_id["G1-should-refuse"]["labels"] == frozenset({"should_refuse", "should_pass"})
    assert by_id["G1-should-refuse"]["metrics"] == ()
    assert by_id["A1"]["item_fields"] == (
        "id",
        "sentence",
        "cited_ids",
        "label",
        "source_refs",
    )
    assert by_id["A1"]["labels"] == frozenset({"supported", "false_cite", "miss_cite"})
    assert by_id["A1"]["metrics"] == ("citation recall", "citation precision")
    assert "Faithfulness" not in " ".join(by_id["A1"]["metrics"])
    assert by_id["T1-new-over-old"]["item_fields"] == (
        "id",
        "query",
        "as_of",
        "in_force",
        "superseded",
        "source_refs",
    )
    assert by_id["T1-new-over-old"]["labels"] == frozenset()
    assert by_id["T1-new-over-old"]["metrics"] == ("new-over-old accuracy",)
    joined = " ".join(
        field
        for spec in qg.UNREGISTERED_SEGMENTS
        for field in (*spec["item_fields"], *spec["metrics"])
    )
    assert "Recall@10" not in joined


def _rows_that_reach_pass_check() -> list[qg.ReportRow]:
    """金标段只有这三段。其余是既有 TBD / not_counted，好让检查走到 counted_as_pass。"""
    rows: list[qg.ReportRow] = []
    for spec in qg.UNREGISTERED_SEGMENTS:
        rows.append(qg.ReportRow(
            kind="segment",
            row_id=spec["id"],
            status="unregistered",
            counted_as_pass=False,
            line=(
                f"segment id={spec['id']} status=unregistered file={spec['file']} "
                "file_present=false counted_as_pass=false"
            ),
        ))
    for row_id in qg.REQUIRED_METRICS:
        rows.append(qg.ReportRow(
            kind="metric",
            row_id=row_id,
            status="TBD",
            counted_as_pass=False,
            line=(
                f"metric id={row_id} status=TBD value=unavailable "
                "baseline=none counted_as_pass=false"
            ),
        ))
    rows.append(qg.ReportRow(
        kind="trap",
        row_id=qg.TRAP_ROW_ID,
        status="not_counted",
        counted_as_pass=False,
        line=(
            f"trap_smoke id={qg.TRAP_ROW_ID} status=not_counted "
            "counted_as_pass=false"
        ),
    ))
    return rows


def test_three_segments_a1_counted_as_pass_raises(tmp_path):
    """只含这三段、且 A1 counted_as_pass=true 时，enforce_report 抛 ContractError。"""
    rows: list[qg.ReportRow] = []
    for row in build_unregistered_rows(tmp_path):
        if row.row_id == "A1":
            rows.append(qg.ReportRow(
                kind=row.kind,
                row_id=row.row_id,
                status=row.status,
                counted_as_pass=True,
                line=row.line.replace("counted_as_pass=false", "counted_as_pass=true"),
            ))
        else:
            rows.append(row)
    assert [row.row_id for row in rows] == [
        "G1-should-refuse",
        "A1",
        "T1-new-over-old",
    ]
    assert rows[1].counted_as_pass is True
    assert rows[1].status == "unregistered"
    with pytest.raises(ContractError):
        enforce_report(rows)


def test_unregistered_counted_as_pass_true_is_contract_error():
    """counted_as_pass=true 必须打在「被记成通过」上。缺指标行会先抛，盖不住这条。"""
    legal = _rows_that_reach_pass_check()
    enforce_report(legal)
    flipped: list[qg.ReportRow] = []
    for row in legal:
        if row.row_id != "A1":
            flipped.append(row)
            continue
        flipped.append(qg.ReportRow(
            kind=row.kind,
            row_id=row.row_id,
            status="unregistered",
            counted_as_pass=True,
            line=row.line.replace("counted_as_pass=false", "counted_as_pass=true"),
        ))
    with pytest.raises(ContractError, match="A1 被记成通过"):
        enforce_report(flipped)


def test_unregistered_printed_as_status_pass_is_contract_error():
    """把 unregistered 印成 status=pass 时抛 ContractError。status 字段仍是 unregistered。"""
    printed: list[qg.ReportRow] = []
    for row in _rows_that_reach_pass_check():
        if row.row_id != "A1":
            printed.append(row)
            continue
        printed.append(qg.ReportRow(
            kind=row.kind,
            row_id=row.row_id,
            status="unregistered",
            counted_as_pass=False,
            line=row.line.replace("status=unregistered", "status=pass"),
        ))
    with pytest.raises(ContractError, match="A1 打印成 pass"):
        enforce_report(printed)


def test_score_registered_a1_missing_cite_sentence_exits_nonzero(tmp_path, capsys):
    """A1 在临时目录被标成已登记，且 cite_sentence.json 缺失时，判分入口退出码非 0。"""
    mark = tmp_path / "registration.txt"
    mark.write_text("segment_registered: A1\n", encoding="utf-8")
    cite = tmp_path / "data" / "eval" / "cite_sentence.json"
    assert not cite.is_file()
    code = score_registered_segments(tmp_path, mark.read_text(encoding="utf-8"))
    err = capsys.readouterr().err
    assert code != 0
    assert "A1 已登记但文件缺失: data/eval/cite_sentence.json" in err


def test_unregistered_missing_cite_file_score_stays_zero(tmp_path, capsys):
    """现行 PREREG 不登记任何段。临时目录缺文件时，判分入口仍退出码 0。"""
    text = PREREG.read_text(encoding="utf-8")
    assert parse_registered_segments(text) == frozenset()
    code = score_registered_segments(tmp_path, text)
    err = capsys.readouterr().err
    assert code == 0, err


def _final_cite_text() -> str:
    payload = {
        "meta": {
            "status": "final",
            "human_row_review": True,
            "reviewer": "fixture-reviewer",
        },
        "items": [
            {
                "id": "cs-fixture-1",
                "sentence": "fixture sentence",
                "cited_ids": ["block@T1"],
                "label": "supported",
                "source_refs": ["fixture-src"],
                "disposition": "keep",
            }
        ],
    }
    return json.dumps(payload, ensure_ascii=False) + "\n"


def test_registered_final_cite_file_is_not_counted_as_pass(tmp_path, capsys):
    """已登记且文件是 final 时，结构检查通过，但行仍不是 pass。"""
    dest = tmp_path / "data" / "eval"
    dest.mkdir(parents=True)
    (dest / "cite_sentence.json").write_text(_final_cite_text(), encoding="utf-8")
    rows = build_unregistered_rows(tmp_path, registered=frozenset({"A1"}))
    a1 = next(row for row in rows if row.row_id == "A1")
    assert a1.status == "unregistered"
    assert a1.counted_as_pass is False
    assert "status=pass" not in a1.line
    assert "counted_as_pass=false" in a1.line
    code = score_registered_segments(tmp_path, "segment_registered: A1\n")
    err = capsys.readouterr().err
    assert code == 0, err


def test_registered_non_final_cite_file_exits_nonzero(tmp_path, capsys):
    """已登记但不是 QG-08 final 时，判分入口退出码非 0。"""
    dest = tmp_path / "data" / "eval"
    dest.mkdir(parents=True)
    draft = {
        "meta": {"status": "draft", "human_row_review": False, "reviewer": ""},
        "items": [],
    }
    (dest / "cite_sentence.json").write_text(
        json.dumps(draft, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    code = score_registered_segments(tmp_path, "segment_registered: A1\n")
    err = capsys.readouterr().err
    assert code != 0
    assert "不是 final" in err


def test_repo_qg08_final_files_pass_registered_structural_check(capsys):
    """仓库里的 QG-08 final 只做结构检查，不设绝对百分数，也不记成通过。"""
    lines = "".join(
        f"segment_registered: {spec['id']}\n" for spec in qg.UNREGISTERED_SEGMENTS
    )
    code = score_registered_segments(ROOT, lines)
    err = capsys.readouterr().err
    assert code == 0, err
    rows = build_unregistered_rows(
        ROOT,
        registered=frozenset(spec["id"] for spec in qg.UNREGISTERED_SEGMENTS),
    )
    assert [row.status for row in rows] == ["unregistered", "unregistered", "unregistered"]
    assert all(row.counted_as_pass is False for row in rows)


def test_r1_no_regression_two_floors_only():
    """两条地板取等为真；任一低于地板为假。没有第三条产品地板。"""
    recall = qg.R1_RECALL_AT_10_FLOOR
    mrr = qg.R1_MRR_AT_10_FLOOR
    assert recall == 0.9732142857142857
    assert mrr == 0.8381855867346939
    assert r1_no_regression(recall=recall, mrr=mrr) is True
    assert r1_no_regression(recall=math.nextafter(recall, 0.0), mrr=mrr) is False
    assert r1_no_regression(recall=recall, mrr=math.nextafter(mrr, 0.0)) is False
    assert list(inspect.signature(r1_no_regression).parameters) == ["recall", "mrr"]
    floor_names = [name for name in vars(qg) if name.endswith("_FLOOR")]
    assert floor_names == ["R1_RECALL_AT_10_FLOOR", "R1_MRR_AT_10_FLOOR"]


def test_quality_gate_source_has_no_live_imports():
    path = ROOT / "src" / "freshlatch" / "eval" / "quality_gate.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    banned = {
        "freshlatch.llm",
        "freshlatch.eval.runner",
        "freshlatch.eval.control",
        "freshlatch.ui",
        "freshlatch.ui.app",
        "freshlatch.store.embeddings",
    }
    assert banned.isdisjoint(imported)
    source = path.read_text(encoding="utf-8")
    assert "run_retrieve_x1" not in source
    assert "run_gold" not in source
    assert "LLMClient" not in source
