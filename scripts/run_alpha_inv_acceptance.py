"""α-inv 确定性验收编排(#94)。

测口:Latch/Gate 套件 + Client Memo 导出契约。
明确不用:freshlatch.eval 主跑、改 gold、假绿统计主口。
跑完更新 docs/evidence/batch1/alpha-acceptance.md 中的机器执行戳。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ACCEPTANCE = REPO_ROOT / "docs" / "evidence" / "batch1" / "alpha-acceptance.md"
DEM7 = REPO_ROOT / "scripts" / "dem7_time_to_sheet.py"
DEM7_OUT = REPO_ROOT / "reports" / "batch1_alpha" / "dem7"

# α-inv 确定性测口(既有 seams;不新开第四类 harness)
ALPHA_INV_TESTS = [
    "tests/unit/test_alpha_inv_acceptance.py",
    "tests/unit/test_rule_gate.py::test_invalidation_list_blocks_fresh",
    "tests/unit/test_renew.py::test_renew_on_invalidated_claim_rejected",
    "tests/unit/test_latch.py::test_decide_discard_voids_and_logs",
    "tests/unit/test_latch.py::test_rerun_timeline_gate_note_and_nth",
    "tests/unit/test_client_memo_export.py::test_client_memo_required_fields_inv2",
    "tests/unit/test_client_memo_export.py::test_client_memo_forbids_roles_and_commercial_verdict_inv3",
]


def _run_pytest(targets: list[str]) -> tuple[int, str]:
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", *targets]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def _run_dem7() -> dict | None:
    proc = subprocess.run(
        [sys.executable, str(DEM7), "--out-dir", str(DEM7_OUT)],
        cwd=str(REPO_ROOT),
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        return None
    record = DEM7_OUT / "dem7-time-to-sheet.json"
    if not record.exists():
        return None
    return json.loads(record.read_text(encoding="utf-8"))


def _stamp_acceptance(*, inv_ok: bool, dem7: dict | None, pytest_tail: str) -> None:
    """在验收记录末追加机器执行戳;不改预登记判据正文。"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    dem7_line = (
        f"- DEM-7 观测分钟数: **{dem7['elapsed_minutes']}** "
        f"(hard_threshold=none;仅观测)"
        if dem7
        else "- DEM-7:未跑或失败(对照项,不影响 α-inv 判定)"
    )
    block = (
        f"\n### 机器执行戳({ts})\n\n"
        f"- α-inv 套件结果: **{'PASS' if inv_ok else 'FAIL'}**\n"
        f"{dem7_line}\n"
        f"- 测口:Latch/Gate + Client Memo;未用 freshlatch.eval 主跑;未改 gold\n"
        f"- pytest 尾部:\n\n```\n{pytest_tail.strip()[-800:]}\n```\n"
    )
    text = ACCEPTANCE.read_text(encoding="utf-8")
    marker = "\n<!-- MACHINE_STAMP -->\n"
    if marker in text:
        head = text.split(marker)[0]
        text = head + marker + block
    else:
        text = text.rstrip() + "\n" + marker + block
    ACCEPTANCE.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="α-inv 确定性验收编排(#94)")
    ap.add_argument(
        "--skip-dem7",
        action="store_true",
        help="跳过 DEM-7 观测脚本(对照项)",
    )
    args = ap.parse_args(argv)

    print("[α-inv] 跑 Latch/Gate + Client Memo 确定性套件 …")
    code, out = _run_pytest(ALPHA_INV_TESTS)
    print(out)
    inv_ok = code == 0

    dem7 = None
    if not args.skip_dem7:
        print("[α-demo 对照] DEM-7 Time-to-Sheet 观测 …")
        dem7 = _run_dem7()
        if dem7:
            print(f"  elapsed_minutes={dem7['elapsed_minutes']} (无硬阈值)")

    if ACCEPTANCE.exists():
        _stamp_acceptance(inv_ok=inv_ok, dem7=dem7, pytest_tail=out)
        print(f"[记录] 已更新 {ACCEPTANCE}")

    print(
        "\n禁止升格句:不得把 α-demo 说成「产品已验证 / 一期测量闭合 / UX 证明了 latch」;"
        "latch 由 Void→Stay-Red / 闸证明。"
    )
    sys.exit(0 if inv_ok else 1)


if __name__ == "__main__":
    main()
