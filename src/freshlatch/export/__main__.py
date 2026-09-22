"""CLI:`python -m freshlatch.export sheet|client-memo --snapshot …`。

snapshot 须含 claims;可选 question。库路径优先 CLI --db,否则 snapshot 的 store/db 字段。
client-memo 与 sheet 分离:客户向字段契约,不含审计轨迹。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from freshlatch.sheet import (  # noqa: E402
    export_client_memo_from_snapshot,
    export_sheet_from_snapshot,
    load_snapshot,
)
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
        description="复验导出(sheet=内部复验单;client-memo=客户向备忘;与 eval 报告分离)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_sheet = sub.add_parser("sheet", help="从快照 JSON + SQLite 审计表导出复验单 Markdown")
    p_sheet.add_argument("--snapshot", required=True, help="复验单快照 JSON(claims + 可选 store)")
    p_sheet.add_argument("--db", default=None, help="SQLite 库路径(覆盖快照内 store/db)")
    p_sheet.add_argument("--out", default=None, help="写出 Markdown 路径;缺省打印到 stdout")

    p_memo = sub.add_parser(
        "client-memo",
        help="从复验投影导出客户向复验备忘(ADR-0015;不跑复验)",
    )
    p_memo.add_argument("--snapshot", required=True, help="复验单快照 JSON(claims + 可选 store)")
    p_memo.add_argument("--db", default=None, help="SQLite 库路径(覆盖快照内 store/db)")
    p_memo.add_argument("--out", default=None, help="写出 Markdown 路径;缺省打印到 stdout")
    p_memo.add_argument(
        "--generated-at",
        default=None,
        help="生成时间戳(缺省=UTC now);写入备忘必填字段",
    )

    args = ap.parse_args(argv)
    db_path = _resolve_db(args)
    store = SQLiteStore(db_path)

    if args.cmd == "sheet":
        md = export_sheet_from_snapshot(args.snapshot, store, out_path=args.out)
        label = "复验单"
    elif args.cmd == "client-memo":
        generated_at = args.generated_at or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        md = export_client_memo_from_snapshot(
            args.snapshot,
            store,
            generated_at=generated_at,
            out_path=args.out,
        )
        label = "客户向复验备忘"
    else:
        raise SystemExit(f"未知子命令: {args.cmd}")

    if args.out:
        print(f"{label}已写出: {args.out}")
    else:
        print(md, end="")


if __name__ == "__main__":
    main()
