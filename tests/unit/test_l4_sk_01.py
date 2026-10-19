"""L4-SK-01: Guards hook 样板含 failClosed 与退出码 2，默认不启用。

演练在本测试里跑样板脚本，不把 hooks.json 写进 .cursor/。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GUARDS_DOC = REPO / "docs/agents/agent-guards.md"
SAMPLE_HOOKS = REPO / "docs/agents/hooks/hooks.json"
SAMPLE_SCRIPT = REPO / "docs/agents/hooks/deny_exit_2.py"
LOOP_PATH = REPO / "src/freshlatch/roles/loop.py"
LOOP_REL = "src/freshlatch/roles/loop.py"
# 本票新增或改动的路径。验收「不改 loop.py」只对照这份清单与当前 checkout，不查历史 commit。
TICKET_PATHS = (
    "docs/agents/agent-guards.md",
    "docs/agents/hooks/hooks.json",
    "docs/agents/hooks/deny_exit_2.py",
    "tests/unit/test_l4_sk_01.py",
    # DOC-TREE-C(#729):根 tasks/** 考古已迁入 archive,票正文在归档副本。
    "docs/_archive/2026-10/tasks/L4-SK-01.md",
)


def cursor_command_hook_outcome(exit_code: int, *, fail_closed: bool) -> str:
    """按 Cursor 命令钩子约定把退出码映射成动作处置。

    退出码 2 等于 deny，动作被拒绝。
    退出码 0 采用 stdout JSON。
    其他退出码在 failClosed 为 true 时同样拒绝，否则放行。
    """
    if exit_code == 2:
        return "deny"
    if exit_code == 0:
        return "use_stdout"
    if fail_closed:
        return "deny"
    return "allow"


def test_sample_sets_fail_closed_and_points_at_exit_2_script():
    cfg = json.loads(SAMPLE_HOOKS.read_text(encoding="utf-8"))
    hook = cfg["hooks"]["beforeShellExecution"][0]
    assert cfg["version"] == 1
    assert hook["failClosed"] is True
    assert hook["command"] == "python docs/agents/hooks/deny_exit_2.py"
    script = SAMPLE_SCRIPT.read_text(encoding="utf-8")
    assert "退出码 2" in script
    assert "deny" in script
    assert "run_loop" in script


def test_enabled_sample_exit_2_denies_action():
    """显式启用后的演练：脚本返回退出码 2，动作记为 deny。

    这里直接执行样板脚本，等同文档里的拒绝演练。
    不创建 .cursor/hooks.json。
    """
    proc = subprocess.run(
        [sys.executable, str(SAMPLE_SCRIPT)],
        input=b'{"command":"echo l4-sk-01-drill","cwd":"."}\n',
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 2
    assert cursor_command_hook_outcome(proc.returncode, fail_closed=True) == "deny"
    payload = json.loads(proc.stdout.decode("utf-8"))
    assert payload["permission"] == "deny"
    assert "退出码 2" in payload["user_message"]


@pytest.mark.parametrize(
    ("exit_code", "fail_closed", "outcome"),
    [
        (2, True, "deny"),
        (2, False, "deny"),
        (1, True, "deny"),
        (0, True, "use_stdout"),
        (1, False, "allow"),
    ],
)
def test_fail_closed_contract(exit_code, fail_closed, outcome):
    assert cursor_command_hook_outcome(exit_code, fail_closed=fail_closed) == outcome


def test_sample_is_not_enabled_by_default():
    doc = GUARDS_DOC.read_text(encoding="utf-8")
    assert "Advanced/optional — not enabled in this repo by default." in doc
    assert "failClosed" in doc
    assert "退出码 2" in doc or "退出码 `2`" in doc
    assert "docs/agents/hooks/hooks.json" in doc
    assert ".cursor/hooks.json" in doc
    assert not (REPO / ".cursor" / "hooks.json").exists()
    tracked = subprocess.run(
        ["git", "ls-files", "--", ".cursor/hooks.json", ".cursor/hooks"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    assert tracked.stdout.strip() == ""


def test_ticket_does_not_change_run_loop():
    """不改 loop.py：内容里没有样板标记，当前 checkout 的差异也不含该路径。

    只用 HEAD 与工作区。浅克隆里没有旧 pin 时，这条仍然能跑。
    """
    loop = LOOP_PATH.read_text(encoding="utf-8")
    assert "failClosed" not in loop
    assert "deny_exit_2" not in loop
    assert LOOP_REL not in TICKET_PATHS
    names = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", LOOP_REL],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in names.stdout.splitlines() if line.strip()}
    assert LOOP_REL not in changed
    assert status.stdout.strip() == ""
