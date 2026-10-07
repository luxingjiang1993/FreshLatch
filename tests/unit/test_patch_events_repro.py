"""CHK-02：一条 dry-run 命令。不读密钥，不打真实 API。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = "freshlatch.eval.patch_events_repro"
SOURCE = ROOT / "src" / "freshlatch" / "eval" / "patch_events_repro.py"
BAD_IDS = ("clause-bad", "date-bad", "del-bad", "num-bad")
OK_IDS = ("clause-ok", "date-ok", "del-ok", "num-ok")
SENTINELS = {
    "DASHSCOPE_API_KEY": "sentinel-dash",
    "DEEPSEEK_API_KEY": "sentinel-deep",
    "MOONSHOT_API_KEY": "sentinel-kimi",
}


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    kept: dict[str, str] = {}
    for key in (
        "PATH",
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "HOME",
        "LANG",
        "LC_ALL",
        "SYSTEMROOT",
        "PATHEXT",
    ):
        value = os.environ.get(key)
        if value:
            kept[key] = value
    kept["PYTHONIOENCODING"] = "utf-8"
    kept["PYTHONUTF8"] = "1"
    if extra:
        kept.update(extra)
    return kept


def _run(*args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        cwd=ROOT,
        env=_env(extra_env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_two_dry_runs_match_and_label_the_table():
    first = _run()
    second = _run()
    assert first.returncode == 0
    assert second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr
    lines = first.stdout.splitlines()
    assert lines[0] == "dry-run 不是预注册正式表"
    assert "seed=20261007" in first.stdout
    assert "n=8" in first.stdout
    for name in ("T-C", "T-B1", "T-B2"):
        assert name in first.stdout
    for name in ("no_chunk_bind", "no_auto_verify", "soft_warning", "retrieval_bm25"):
        assert name in first.stdout
    assert "模型评委加单人抽检" in first.stdout
    assert "用户单人抽检" in first.stdout
    conflict = first.stdout.split("冲突清单", 1)[1]
    for claim_id in BAD_IDS:
        assert claim_id in conflict
    for claim_id in OK_IDS:
        assert claim_id not in conflict
    assert "三评委一致" in conflict
    assert "是" not in conflict
    assert "否" not in conflict


def test_sentinels_stay_out_of_stdio():
    result = _run(extra_env=SENTINELS)
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    for secret in SENTINELS.values():
        assert secret not in combined


def test_out_under_data_exits_before_creating_the_directory():
    target = ROOT / "data" / "patch-events-dry-run"
    assert not target.exists()
    result = _run("--out", "data/patch-events-dry-run")
    assert result.returncode == 2
    assert not target.exists()


def test_command_source_does_not_call_locked_entry_points():
    source = SOURCE.read_text(encoding="utf-8")
    for token in (
        "named_streams",
        "construct_samples",
        "load_dotenv",
        "getenv",
        "environ",
        "--live",
        "--seed",
        "DASHSCOPE",
        "DEEPSEEK",
        "MOONSHOT",
        "API_KEY",
        "gold.json",
    ):
        assert token not in source
    base = (ROOT / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert "PRODUCTION_RETRIEVAL_MODE =" not in source
