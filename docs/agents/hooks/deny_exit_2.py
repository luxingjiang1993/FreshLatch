"""L4-SK-01 Cursor Guards hook 样板。

退出码 2 表示 deny。Cursor 把命令钩子的退出码 2 当成 permission deny，
这次 beforeShellExecution 被拒绝。本脚本始终返回 2，用来演练这条约定。

failClosed 在同目录 hooks.json 里设为 true。默认不启用：
Cursor 只在仓库根存在 .cursor/hooks.json 时加载这份 project hook。
显式启用步骤写在 docs/agents/agent-guards.md。

本脚本不读取、不修改 run_loop 的工具白名单。
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    """读完 Cursor 写入的 stdin，再以退出码 2 拒绝动作。"""
    sys.stdin.buffer.read()
    payload = {
        "permission": "deny",
        "user_message": "L4-SK-01 样板拒绝该动作：退出码 2 表示 deny",
        "agent_message": "Guards hook sample returned exit 2. Cursor denies this action.",
    }
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
