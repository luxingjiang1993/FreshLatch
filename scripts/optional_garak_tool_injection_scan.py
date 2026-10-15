#!/usr/bin/env python3
"""可选 NVIDIA garak tool-injection 扫描样板 (L4U-GARAK).

默认不进必合 CI. 未设置 FRESHLATCH_GARAK=1, 或当前解释器没有 garak 包时,
打印跳过原因并 exit 0. 不把 garak 写入 requirements.txt、pyproject.toml 或 CI.

开启且 garak 已由操作者安装时, 本脚本只包装文档化入口 `python -m garak`
(`--config` / `--spec` / `--target_type` / `--target_name` / `--report_prefix`
/ `--generations` / `--seed`). 探针是本仓薄适配, 不是 garak 源码副本.
不调用 run_loop, 不默认连接付费或外网端点.

说明: docs/ops/可选-garak-tool-injection扫描.md
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_ADAPTER = Path(__file__).resolve().parent / "optional_garak"


def load_local(name: str, path: Path):
    """按文件加载并登记进 sys.modules. 不改模块搜索路径."""
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_match = load_local("freshlatch_match", _ADAPTER / "freshlatch_match.py")
EXIT_BLOCK_SHIP = _match.EXIT_BLOCK_SHIP
EXIT_CONFIG = _match.EXIT_CONFIG
EXIT_INCONCLUSIVE = _match.EXIT_INCONCLUSIVE
EXIT_SKIP = _match.EXIT_SKIP
PROBE_SPEC = _match.PROBE_SPEC
REPORT_PREFIX = _match.REPORT_PREFIX
SCAN_GENERATIONS = _match.SCAN_GENERATIONS
SCAN_SEED = _match.SCAN_SEED
gate_decision = _match.gate_decision
load_prompt_set = _match.load_prompt_set
parse_report_jsonl = _match.parse_report_jsonl
summarize_block_ship = _match.summarize_block_ship

_REPO = Path(__file__).resolve().parents[1]
_PROMPTS = _REPO / "docs" / "evidence" / "garak" / "tool-injection-prompts.json"
_BOOTSTRAP = _ADAPTER / "bootstrap.py"
_RUNBOOK = "docs/ops/可选-garak-tool-injection扫描.md"


def _enabled() -> bool:
    return os.environ.get("FRESHLATCH_GARAK", "").strip().lower() in {"1", "true", "yes"}


def _garak_present() -> bool:
    return importlib.util.find_spec("garak") is not None


def _prepare_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _report_dir() -> Path:
    raw = os.environ.get("FRESHLATCH_GARAK_REPORT_DIR", "").strip()
    if raw:
        return Path(raw)
    return _REPO / "garak_runs"


def _write_config(path: Path, report_dir: Path, target_type: str, target_name: str) -> None:
    payload = {
        "run": {
            "generations": SCAN_GENERATIONS,
            "seed": SCAN_SEED,
            "spec": PROBE_SPEC,
        },
        "reporting": {
            "report_dir": str(report_dir),
            "report_prefix": REPORT_PREFIX,
        },
        "plugins": {
            "target_type": target_type,
            "target_name": target_name,
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _find_report(report_dir: Path) -> Path | None:
    direct = report_dir / f"{REPORT_PREFIX}.report.jsonl"
    if direct.is_file():
        return direct
    named = sorted(
        report_dir.glob(f"{REPORT_PREFIX}*.report.jsonl"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if named:
        return named[0]
    return None


def _skip(reason: str) -> int:
    print(
        f"L4U-GARAK: 跳过 ({reason}). 默认不进必合 CI. 说明: {_RUNBOOK}",
        flush=True,
    )
    return EXIT_SKIP


def main() -> int:
    _prepare_stdio()
    target_type = os.environ.get("FRESHLATCH_GARAK_TARGET_TYPE", "")
    target_name = os.environ.get("FRESHLATCH_GARAK_TARGET_NAME", "")
    reason, code = gate_decision(_enabled(), _garak_present(), target_type, target_name)
    if reason == "skip-disabled":
        return _skip("未设置 FRESHLATCH_GARAK=1")
    if reason == "skip-no-garak":
        return _skip("FRESHLATCH_GARAK=1 但当前解释器没有 garak 包")
    if code == EXIT_CONFIG:
        print(
            "L4U-GARAK: 缺少 FRESHLATCH_GARAK_TARGET_TYPE 或 "
            "FRESHLATCH_GARAK_TARGET_NAME. 不默认连接付费端点.",
            file=sys.stderr,
            flush=True,
        )
        return EXIT_CONFIG

    try:
        prompt_set = load_prompt_set(_PROMPTS)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"L4U-GARAK: prompt 集不可读: {exc}", file=sys.stderr, flush=True)
        return EXIT_CONFIG

    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    config_path = report_dir / f"{REPORT_PREFIX}.config.json"
    _write_config(config_path, report_dir, target_type.strip(), target_name.strip())
    expected = report_dir / f"{REPORT_PREFIX}.report.jsonl"
    summary_path = report_dir / f"{REPORT_PREFIX}.block-ship.json"
    command = [
        sys.executable,
        str(_BOOTSTRAP),
        "--config",
        str(config_path),
        "--spec",
        PROBE_SPEC,
        "--target_type",
        target_type.strip(),
        "--target_name",
        target_name.strip(),
        "--report_prefix",
        REPORT_PREFIX,
        "--generations",
        str(SCAN_GENERATIONS),
        "--seed",
        str(SCAN_SEED),
    ]
    print("L4U-GARAK: 包装 python -m garak", flush=True)
    print(f"prompt 集: {_PROMPTS}", flush=True)
    print(f"garak report: {expected}", flush=True)
    print(f"block-ship: {summary_path}", flush=True)
    completed = subprocess.run(command, check=False)
    report_path = _find_report(report_dir)
    attempts = []
    parsed = False
    if report_path is not None:
        attempts = parse_report_jsonl(report_path.read_text(encoding="utf-8"))
        parsed = True
    summary = summarize_block_ship(
        prompt_set,
        attempts,
        meta={
            "parsed": parsed,
            "garak_exit": completed.returncode,
            "target_type": target_type.strip(),
            "target_name": target_name.strip(),
            "prompt_set": str(_PROMPTS),
            "garak_report": str(report_path) if report_path is not None else str(expected),
            "config": str(config_path),
        },
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"block_ship={summary['block_ship']}", flush=True)
    print("本摘要不是安全认证, 不是 L5, 不是 C-04 重跑, 也不是合并门.", flush=True)
    if completed.returncode != 0:
        return completed.returncode
    if summary["block_ship"] is True:
        return EXIT_BLOCK_SHIP
    if summary["block_ship"] is None:
        return EXIT_INCONCLUSIVE
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
