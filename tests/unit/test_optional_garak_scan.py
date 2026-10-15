"""L4U-GARAK: 可选 garak 样板默认不进必合 CI.

未设置 FRESHLATCH_GARAK 时, 下面的操作者用例 skip.
始终执行的用例只检查跳过路径和预锁判据, 不导入 garak, 不联网.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO / "scripts" / "optional_garak_tool_injection_scan.py"
_BOOTSTRAP = _REPO / "scripts" / "optional_garak" / "bootstrap.py"
_MATCH = _REPO / "scripts" / "optional_garak" / "freshlatch_match.py"
_PROMPTS = _REPO / "docs" / "evidence" / "garak" / "tool-injection-prompts.json"
_RUNBOOK = _REPO / "docs" / "ops" / "可选-garak-tool-injection扫描.md"
_SECURITY = _REPO / "docs" / "security.md"
_README = _REPO / "docs" / "evidence" / "garak" / "README.md"


def _load_match():
    spec = importlib.util.spec_from_file_location("freshlatch_match", _MATCH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MATCH_MOD = _load_match()


def _garak_enabled() -> bool:
    return os.environ.get("FRESHLATCH_GARAK", "").strip().lower() in {"1", "true", "yes"}


def _run_script(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=_REPO,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("FRESHLATCH_GARAK", None)
    env.pop("FRESHLATCH_GARAK_TARGET_TYPE", None)
    env.pop("FRESHLATCH_GARAK_TARGET_NAME", None)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _imports_garak_at_module_level(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names if alias.name.split(".")[0] == "garak")
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "garak":
            found.append(node.module)
    return found


def test_default_script_exits_zero_without_env():
    proc = _run_script(_base_env())
    assert proc.returncode == 0
    assert "FRESHLATCH_GARAK" in proc.stdout
    assert "默认不进必合 CI" in proc.stdout
    assert "garak_runs" not in proc.stdout


def test_enabled_without_garak_package_exits_zero():
    env = _base_env()
    env["FRESHLATCH_GARAK"] = "1"
    proc = _run_script(env)
    garak_spec = importlib.util.find_spec("garak")
    if garak_spec is not None:
        pytest.skip("当前解释器已安装 garak; 缺包跳过路径不在此环境")
    assert proc.returncode == 0
    assert "没有 garak 包" in proc.stdout
    assert proc.stderr == ""


def test_wrapper_modules_do_not_import_garak_at_import_time():
    assert _imports_garak_at_module_level(_SCRIPT) == []
    assert _imports_garak_at_module_level(_BOOTSTRAP) == []
    assert _imports_garak_at_module_level(_MATCH) == []


def test_gate_does_not_run_without_flag_package_or_target():
    decide = _MATCH_MOD.gate_decision
    assert decide(False, False, "", "") == ("skip-disabled", 0)
    assert decide(True, False, "", "") == ("skip-no-garak", 0)
    assert decide(True, True, "", "repeat") == ("need-target", 2)
    assert decide(True, True, "test.Repeat", "") == ("need-target", 2)
    assert decide(True, True, "test.Repeat", "repeat") == ("run", None)


def test_shipped_prompt_set_and_runbook_pointer():
    payload = _MATCH_MOD.load_prompt_set(_PROMPTS)
    ids = [row["id"] for row in payload["prompts"]]
    assert "fl-inj-001" in ids
    assert "fl-benign-001" in ids
    runbook = _RUNBOOK.read_text(encoding="utf-8")
    assert "默认不进必合 CI" in runbook
    assert "freshlatch-tool-injection.report.jsonl" in runbook
    assert "freshlatch-tool-injection.block-ship.json" in runbook
    assert "probes.freshlatch_tool_injection.ToolInjection" in runbook
    assert "FRESHLATCH_GARAK" in runbook
    assert "不是安全认证" in runbook
    assert "不是 L5" in runbook
    security = _SECURITY.read_text(encoding="utf-8")
    assert "docs/ops/可选-garak-tool-injection扫描.md" in security
    assert "本仓 CI 不调用 garak" in security
    readme = _README.read_text(encoding="utf-8")
    assert "block_ship" in readme
    assert "默认不进必合 CI" in readme


def test_injection_call_shape_blocks_ship_and_benign_does_not():
    payload = _MATCH_MOD.load_prompt_set(_PROMPTS)
    clean = {
        row["id"]: ["不调用工具, 只说明证据不足。"]
        for row in payload["prompts"]
    }
    miss = _MATCH_MOD.summarize_block_ship(
        payload,
        [{"prompt_id": key, "outputs": value} for key, value in clean.items()],
        meta={},
    )
    assert miss["block_ship"] is False

    hit_outputs = dict(clean)
    hit_outputs["fl-inj-001"] = ['{"function": {"name": "reverify_claim", "arguments": "{}"}}']
    hit = _MATCH_MOD.summarize_block_ship(
        payload,
        [{"prompt_id": key, "outputs": value} for key, value in hit_outputs.items()],
        meta={},
    )
    assert hit["block_ship"] is True
    inj = next(row for row in hit["prompts"] if row["id"] == "fl-inj-001")
    assert inj["outcome"] == "hit"
    assert inj["reached_tools"] == ["reverify_claim"]

    prose = dict(clean)
    prose["fl-inj-002"] = ["不要调用 mark_stale, 这是语料正文。"]
    prose_summary = _MATCH_MOD.summarize_block_ship(
        payload,
        [{"prompt_id": key, "outputs": value} for key, value in prose.items()],
        meta={},
    )
    assert prose_summary["block_ship"] is False

    benign_call = dict(clean)
    benign_call["fl-benign-001"] = ['{"name": "retrieve"}']
    benign = _MATCH_MOD.summarize_block_ship(
        payload,
        [{"prompt_id": key, "outputs": value} for key, value in benign_call.items()],
        meta={},
    )
    assert benign["block_ship"] is False
    assert benign["claims"]["security_certification"] is False
    assert benign["claims"]["l5"] is False
    assert benign["claims"]["merge_gate"] is False


def test_missing_attempt_is_inconclusive():
    payload = _MATCH_MOD.load_prompt_set(_PROMPTS)
    summary = _MATCH_MOD.summarize_block_ship(payload, [], meta={})
    assert summary["block_ship"] is None


def test_report_jsonl_joins_prompt_id_and_tool_calls():
    line = json.dumps(
        {
            "entry_type": "attempt",
            "prompt": {"turns": [{"role": "user", "content": {"text": "FLGARAK fl-inj-003"}}]},
            "outputs": [
                {
                    "text": "好的",
                    "tool_calls": [{"function": {"name": "retrieve", "arguments": "{}"}}],
                }
            ],
            "notes": {"prompt_id": "fl-inj-003", "watched_tools": ["retrieve"]},
        },
        ensure_ascii=False,
    )
    attempts = _MATCH_MOD.parse_report_jsonl(line + "\n" + json.dumps({"entry_type": "eval"}))
    assert len(attempts) == 1
    assert attempts[0]["prompt_id"] == "fl-inj-003"
    assert _MATCH_MOD.reached_tools(attempts[0]["outputs"][0], ["retrieve"]) == ["retrieve"]
    assert _MATCH_MOD.reached_tools('<tool_call name="mark_stale">', ["mark_stale"]) == ["mark_stale"]


@pytest.mark.skipif(
    not _garak_enabled(),
    reason="FRESHLATCH_GARAK 未设置; 默认 CI 不跑 garak",
)
def test_operator_env_does_not_scan_without_target():
    """操作者打开开关但没给 target 时, 脚本不得启动扫描."""
    env = _base_env()
    env["FRESHLATCH_GARAK"] = "1"
    proc = _run_script(env)
    assert proc.returncode in {0, 2}
    assert "block_ship=true" not in proc.stdout
