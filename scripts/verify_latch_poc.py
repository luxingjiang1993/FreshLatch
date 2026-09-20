"""#11 §5.10 顺带验证(T9 开工第一项):SqliteSaver Windows 文件锁 + 进程重启恢复。

两段独立进程:
  phase1 —— 起图 → 跑到 interrupt 落盘 → 进程退出(连接关闭、文件锁释放);
  phase2 —— 全新进程 Command(resume) 恢复 → execute 落档 → 跨进程断言。
任一段断言失败 exit 1。驱动模式(无参数)依次跑两段并汇总。

用法:
  python scripts/verify_latch_poc.py                          # 驱动模式(临时目录)
  python scripts/verify_latch_poc.py phase1 <db_dir>          # 单跑(调试用)
  python scripts/verify_latch_poc.py phase2 <db_dir>
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

CLAIM = {"claim_id": "c1", "statement": "竞品客单价仍显著高于我们",
         "status": "stale", "reason": "T1 竞品降价(POC)"}
THREAD_ID = "reverify-round-20260920-000000"  # enter_round(ts="20260920-000000") 的轮次 thread


def _latch(db_dir: Path):
    from freshlatch.latch import HumanLatch
    from freshlatch.store.sqlite_store import SQLiteStore

    return HumanLatch(SQLiteStore(db_dir / "poc_freshlatch.db"), db_dir / "checkpoints.db")


def phase1(db_dir: Path) -> None:
    from freshlatch.models import Claim

    latch = _latch(db_dir)
    claim = Claim(claim_id=CLAIM["claim_id"], statement=CLAIM["statement"],
                  status=CLAIM["status"], reason=CLAIM["reason"])
    rnd = latch.enter_round([claim], ts="20260920-000000")
    assert rnd.waiting, "phase1:图未停在 interrupt"
    assert rnd.pending[0]["claim_id"] == "c1"
    print(json.dumps({"phase": 1, "thread_id": rnd.thread_id,
                      "pending": len(rnd.pending)}, ensure_ascii=False))
    # 进程在此退出:with 块已关 SqliteSaver 连接(Windows 文件锁释放 = phase2 能开同名库)


def phase2(db_dir: Path) -> None:
    from freshlatch.models import Claim

    latch = _latch(db_dir)
    state = latch.review_state(THREAD_ID)
    assert state is not None and state["next"], "phase2:重启后未找到中断态(checkpoint 未持久化)"
    results = latch.decide(THREAD_ID, [{"claim_id": "c1", "action": "discard"}],
                           claims=[Claim(claim_id=CLAIM["claim_id"], statement=CLAIM["statement"],
                                         status=CLAIM["status"], reason=CLAIM["reason"])])
    assert results[0]["ok"], f"phase2:落档失败 {results[0]}"
    store = latch.store
    assert store.list_invalidation() == ["c1"], "phase2:作废名单未跨进程持久化"
    with store._conn() as conn:
        rows = conn.execute("SELECT action, actor FROM latch_log WHERE claim_id='c1'").fetchall()
    assert [(r["action"], r["actor"]) for r in rows] == [("discard", "human")]
    print(json.dumps({"phase": 2, "resumed": True, "invalidation": store.list_invalidation()},
                     ensure_ascii=False))


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] in ("phase1", "phase2"):
        getattr(sys.modules[__name__], sys.argv[1])(Path(sys.argv[2]))
        return 0
    db_dir = Path(tempfile.mkdtemp(prefix="latch-poc-"))
    for phase in ("phase1", "phase2"):
        proc = subprocess.run([sys.executable, str(Path(__file__)), phase, str(db_dir)],
                              capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        if proc.returncode != 0:
            sys.stderr.write(proc.stderr)
            print("LATCH-POC FAIL", file=sys.stderr)
            return 1
    print("LATCH-POC PASS:interrupt 落盘 → 进程退出(锁释放)→ 新进程 resume 恢复 → 作废落档")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
