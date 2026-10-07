"""gen_x1_drafts 入口。"""

from __future__ import annotations

from typing import Any

from freshlatch.eval.x1_drafts.flagging import _run_flag
from freshlatch.eval.x1_drafts.generate import _build_parser, _run_generate

def main(argv: list[str] | None = None, llm_client: Any = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 1
        return int(code)
    if args.cmd == "generate":
        return _run_generate(args, llm_client)
    if args.cmd == "flag":
        return _run_flag(args, llm_client)
    return 1
