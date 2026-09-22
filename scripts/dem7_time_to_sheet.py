"""DEM-7 Time-to-Sheet 固定观测脚本(#94 / C1-Batch0-1)。

走通:合成快照 → 复验单 sheet 导出 → 客户向复验备忘导出,记录墙钟分钟数。
层:α-demo / 仅观测。不设 <10min 硬阈值;不升格为 latch/产品验证。
不用 freshlatch.eval,不改 gold。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from freshlatch.models import Claim  # noqa: E402
from freshlatch.sheet import (  # noqa: E402
    export_client_memo_from_snapshot,
    export_sheet_from_snapshot,
)
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def _seed(work: Path) -> tuple[Path, Path]:
    """合成最小复验投影(读投影导出,不跑复验/LLM)。"""
    db_path = work / "dem7.db"
    store = SQLiteStore(db_path)
    claims = [
        Claim(
            claim_id="c-fresh",
            statement="仍成立主张",
            t1_evidence_ids=["t0-doc#p1@T1"],
            status="fresh",
            reason="T1 同口径仍成立",
        ),
        Claim(
            claim_id="c-void",
            statement="已作废主张",
            t1_evidence_ids=["t0-doc#p2@T1"],
            status="stale",
            reason="T1 推翻原前提",
            voided=True,
            voided_at="20260922-100000",
        ),
        Claim(
            claim_id="c-gap",
            statement="缺口主张",
            t1_evidence_ids=[],
            status="unknown",
            reason="",
        ),
    ]
    store.add_invalidation("c-void", "20260922-100000", reason="人审作废")
    store.log_latch("20260922-100000", "c-void", "discard", evidence_id=None)

    snap_path = work / "dem7_snapshot.json"
    snap = {
        "question": "DEM-7 观测课题:导出路径是否可走通?",
        "store": str(db_path),
        "synthetic": True,
        "claims": [
            {
                "claim_id": c.claim_id,
                "statement": c.statement,
                "t0_evidence_ids": c.t0_evidence_ids,
                "t1_evidence_ids": c.t1_evidence_ids,
                "status": c.status,
                "reason": c.reason,
                "voided": c.voided,
                "voided_at": c.voided_at,
            }
            for c in claims
        ],
    }
    snap_path.write_text(
        json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return snap_path, db_path


def run(out_dir: Path) -> dict:
    """固定脚本走通一遍并记录分钟数;hard_threshold 恒为 none(不设硬阈值)。"""
    import tempfile

    out_dir.mkdir(parents=True, exist_ok=True)

    t0 = time.perf_counter()
    # Windows 下 SQLite 连接可能短时占锁;ignore_cleanup_errors 避免观测脚本因清理失败退出
    with tempfile.TemporaryDirectory(prefix="dem7-", ignore_cleanup_errors=True) as tmp:
        work = Path(tmp)
        snap_path, db_path = _seed(work)
        store = SQLiteStore(db_path)

        sheet_path = out_dir / "sheet.md"
        memo_path = out_dir / "client_memo.md"
        export_sheet_from_snapshot(snap_path, store, out_path=sheet_path)
        export_client_memo_from_snapshot(
            snap_path,
            store,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            out_path=memo_path,
        )
        snap_out = out_dir / "dem7_snapshot.json"
        snap_out.write_text(snap_path.read_text(encoding="utf-8"), encoding="utf-8")
        del store
        elapsed_s = time.perf_counter() - t0
        elapsed_minutes = round(elapsed_s / 60.0, 4)

    def _rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        except ValueError:
            return str(p)

    payload = {
        "layer": "α-demo",
        "id": "DEM-7",
        "label": "Time-to-Sheet",
        "elapsed_seconds": round(elapsed_s, 4),
        "elapsed_minutes": elapsed_minutes,
        "hard_threshold": None,  # 不设硬阈值;仅观测
        "observation_only": True,
        "artifacts": {
            "sheet": _rel(sheet_path),
            "client_memo": _rel(memo_path),
            "snapshot": _rel(snap_out),
        },
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "仅观测记分钟数;无 <10min 硬阈值。"
            "不得把本读数说成产品已验证 / 一期测量闭合 / UX 证明了 latch。"
        ),
    }
    record_path = out_dir / "dem7-time-to-sheet.json"
    record_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(
        description="DEM-7 Time-to-Sheet 固定观测(不设硬阈值;α-demo 层)"
    )
    ap.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "reports" / "batch1_alpha" / "dem7"),
        help="写出 sheet/memo 与 dem7-time-to-sheet.json 的目录",
    )
    args = ap.parse_args(argv)
    payload = run(Path(args.out_dir))
    print(
        f"DEM-7 观测完成: elapsed_minutes={payload['elapsed_minutes']} "
        f"(硬阈值=无;层=α-demo;不升格)"
    )
    print(f"记录: {Path(args.out_dir) / 'dem7-time-to-sheet.json'}")


if __name__ == "__main__":
    main()
