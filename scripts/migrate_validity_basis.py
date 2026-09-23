"""显式批迁 CLI:快照 JSON 内 validity_basis dict → 一元 list(#150)。

用法:
  python -m scripts.migrate_validity_basis PATH [PATH ...]
  python -m scripts.migrate_validity_basis --dry-run PATH
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接 python scripts/migrate_validity_basis.py
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from freshlatch.basis_migrate import migrate_snapshot_file  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="存量 validity_basis 单对象 → 一元 list")
    parser.add_argument("paths", nargs="+", type=Path, help="复验单快照 JSON 路径")
    parser.add_argument("--dry-run", action="store_true", help="只统计不写回")
    args = parser.parse_args(argv)
    total = 0
    for path in args.paths:
        n = migrate_snapshot_file(path, write=not args.dry_run)
        total += n
        action = "将迁" if args.dry_run else "已迁"
        print(f"{path}: {action} {n} 条")
    print(f"合计 {total} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
