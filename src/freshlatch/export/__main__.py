"""CLI:`python -m freshlatch.export sheet|client-memo --snapshot …`。

snapshot 须含 claims;可选 question。库路径优先 CLI --db,否则 snapshot 的 store/db 字段。
client-memo 与 sheet 分离:客户向字段契约,不含审计轨迹。
client-memo 走发前钩子闸(#229 / ADR-0031):deny 零写 Memo 文件。
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from freshlatch.sheet import (  # noqa: E402
    export_client_memo_from_snapshot_gated,
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
        help="从复验投影导出客户向复验备忘(ADR-0015;套发前钩子闸;不跑复验)",
    )
    p_memo.add_argument("--snapshot", required=True, help="复验单快照 JSON(claims + 可选 store)")
    p_memo.add_argument("--db", default=None, help="SQLite 库路径(覆盖快照内 store/db)")
    p_memo.add_argument("--out", default=None, help="写出 Markdown 路径;缺省打印到 stdout")
    p_memo.add_argument(
        "--generated-at",
        default=None,
        help="生成时间戳(缺省=UTC now);写入备忘必填字段",
    )
    # #229 发前钩子闸参数(与 UI 同语义)
    p_memo.add_argument(
        "--run-id",
        default=None,
        help="发前 Run 绑定键(必填语义;也可写在快照 run_id 字段)",
    )
    p_memo.add_argument(
        "--disposition",
        default=None,
        choices=["可发", "需补丁", "勿发"],
        help="包结论;缺省由快照主张聚合(disposition_for_claims)",
    )
    p_memo.add_argument(
        "--ack-needs-patch",
        action="store_true",
        help="显式确认需补丁仍导出(对齐 ack_needs_patch)",
    )
    p_memo.add_argument(
        "--checksum-fresh",
        dest="checksum_fresh",
        action="store_true",
        default=True,
        help="T1 checksum 机械新鲜度未漂(默认 True)",
    )
    p_memo.add_argument(
        "--checksum-stale",
        dest="checksum_fresh",
        action="store_false",
        help="声明 checksum 已漂移 → 闸拒",
    )

    args = ap.parse_args(argv)
    db_path = _resolve_db(args)
    store = SQLiteStore(db_path)

    if args.cmd == "sheet":
        md = export_sheet_from_snapshot(args.snapshot, store, out_path=args.out)
        label = "复验单"
        if args.out:
            print(f"{label}已写出: {args.out}")
        else:
            print(md, end="")
        return

    if args.cmd == "client-memo":
        generated_at = args.generated_at or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        # 套闸:deny 不得创建/覆盖 Memo 文件
        out_path = args.out
        if out_path is not None and Path(out_path).exists():
            # 已有文件时 deny 也不得改写;先记路径,闸后再决是否写
            pass
        hook, md = export_client_memo_from_snapshot_gated(
            args.snapshot,
            store,
            run_id=args.run_id,
            disposition=args.disposition,
            ack_needs_patch=bool(args.ack_needs_patch),
            checksum_fresh=bool(args.checksum_fresh),
            generated_at=generated_at,
            out_path=out_path,
        )
        if not hook.allow:
            # deny:保证零写——若此前不存在则仍不存在
            msg = f"发前钩子拒绝导出 Client Memo: {hook.code} · {hook.message}"
            print(msg, file=sys.stderr)
            raise SystemExit(1)
        if args.out:
            print(f"客户向复验备忘已写出: {args.out}")
        else:
            print(md, end="")
        return

    raise SystemExit(f"未知子命令: {args.cmd}")


if __name__ == "__main__":
    main()
