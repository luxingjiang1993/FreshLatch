"""QG-03 离线质量闸。夹具与假命中，不访问网络，不读付费密钥的值。"""

from __future__ import annotations

import ast
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
    run_quality_gate,
)
from freshlatch.packs import repo_root

ROOT = repo_root()
PREREG = ROOT / "docs" / "evidence" / "quality-gate" / "PREREG.md"
SECRET = "sekret-should-not-leak"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["DASHSCOPE_API_KEY"] = SECRET + "-dash"
    env["DEEPSEEK_API_KEY"] = SECRET + "-deep"
    env["MOONSHOT_API_KEY"] = SECRET + "-moon"
    return subprocess.run(
        [sys.executable, "-m", "freshlatch.eval", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


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
    assert proc.returncode == 2
    assert "未设置 --offline" in proc.stderr
    assert SECRET not in proc.stdout + proc.stderr
    assert "locked_gate=true" not in proc.stdout


def test_cli_missing_prereg():
    proc = _run("quality-gate", "--offline", "--prereg", str(ROOT / "missing-prereg.md"))
    assert proc.returncode == 1
    assert "不存在" in proc.stderr
    assert SECRET not in proc.stdout + proc.stderr


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
    assert "metric id=guardrail-0hit status=TBD value=unavailable" in out
    assert "metric id=conflict-pair-ordering status=TBD value=0.3333333333333333" in out
    assert "metric id=multi-hop-full-hit status=TBD value=0.7555555555555555" in out
    assert "trap_smoke id=trap-smoke status=not_counted" in out
    assert "in_denominator=false" in out
    assert "source=frozen-per-query-replay" in out


def test_module_entrypoint_matches_command_shape():
    proc = _run(
        "quality-gate",
        "--offline",
        "--prereg",
        "docs/evidence/quality-gate/PREREG.md",
    )
    assert proc.returncode == 0, proc.stderr
    assert "segment id=A1 status=unregistered" in proc.stdout
    assert "status=pass" not in proc.stdout
    assert SECRET not in proc.stdout + proc.stderr


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
