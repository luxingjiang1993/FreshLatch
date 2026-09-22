"""CLI:`python -m freshlatch.export sheet --snapshot … [--db …] [--out …]`。

snapshot 须含 claims;可选 question。库路径优先 CLI --db,否则 snapshot 的 store/db 字段。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from freshlatch.sheet import export_sheet_from_snapshot, load_snapshot  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def _resolve_db(args: argparse.Namespace) -> Path:
    if args.db:
        return Path(args.db)
    snap = load_snapshot(args.snapshot)
    for key in ("store", "db", "store_path", "db_path"):
        if snap.get(key):
            return Path(str(snap[key]))
    raise SystemExit("须提供 --db,或在快照 JSON 中写 store/db 字段")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        prog="freshlatch.export",
        description="复验单 Markdown 导出(K4;与 eval 报告分离)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_sheet = sub.add_parser("sheet", help="从快照 JSON + SQLite 审计表导出复验单 Markdown")
    p_sheet.add_argument("--snapshot", required=True, help="复验单快照 JSON(claims + 可选 store)")
    p_sheet.add_argument("--db", default=None, help="SQLite 库路径(覆盖快照内 store/db)")
    p_sheet.add_argument("--out", default=None, help="写出 Markdown 路径;缺省打印到 stdout")

    args = ap.parse_args(argv)
    if args.cmd != "sheet":
        raise SystemExit(f"未知子命令: {args.cmd}")

    db_path = _resolve_db(args)
    store = SQLiteStore(db_path)
    md = export_sheet_from_snapshot(args.snapshot, store, out_path=args.out)
    if args.out:
        print(f"复验单已写出: {args.out}")
    else:
        print(md, end="")


if __name__ == "__main__":
    main()
