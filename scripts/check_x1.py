"""x1 许可 / 去污染 / 题集结构检查 CLI（RET-01.1）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freshlatch.eval.x1_checks import run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
