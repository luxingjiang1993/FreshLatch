"""清单与文本的原子写入。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from freshlatch.eval.x1_drafts._lookup import _pkg_attr
from freshlatch.eval.x1_drafts.constants import MARKER_NAME

def _atomic_write_text(path: Path, text: str) -> None:
    """同目录临时文件写完后 os.replace，避免写到一半留下半截文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _write_manifest(dest: Path, fields: dict[str, Any]) -> None:
    _pkg_attr("_atomic_write_text")(
        dest / MARKER_NAME,
        json.dumps(fields, ensure_ascii=False, indent=2) + "\n",
    )
