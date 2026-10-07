"""一条 dry-run 命令：把 patch_events 各段串成结果表。

默认不访问网络。假评委只回显请求里的 model 与 temperature。
日志留在临时目录。标准输出的第一行标明这张表是演示。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import (
    ablation_interval_report,
    primary_comparison_rows,
    run_ablations,
)
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_judges import JUDGE_IDS, run_judges
from freshlatch.eval.patch_events_metrics import SEED, compare_primary, format_rate
from freshlatch.eval.patch_events_spotcheck import export_conflicts, export_spotcheck

_BANNER = "dry-run 不是预注册正式表"
_FIXTURE = Path("tests") / "fixtures" / "patch_events" / "repro.json"
_LABEL_LINE = '{"A":"是","B":"是"}'


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def _resolve_out(root: Path, raw: str) -> Path:
    target = Path(raw)
    if not target.is_absolute():
        target = root / target
    return target.resolve()


def _banned(root: Path, raw: str) -> bool:
    resolved = _resolve_out(root, raw)
    for parent in (root / "data", root / "docs" / "evidence"):
        base = parent.resolve()
        if resolved == base:
            return True
        try:
            resolved.relative_to(base)
        except ValueError:
            continue
        else:
            return True
    return False


def _load_candidates(root: Path) -> list[dict[str, Any]]:
    payload = json.loads((root / _FIXTURE).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("夹具必须是列表")
    return [dict(item) for item in payload]


def _ingested(candidates: Sequence[Mapping[str, Any]]) -> set[str]:
    found: set[str] = set()
    for item in candidates:
        evidence_id = str(item["evidence_id"])
        if evidence_id.endswith("@T1"):
            found.add(evidence_id)
    return found


def _fake_generator(request: Mapping[str, Any]) -> dict[str, Any]:
    claim_id = request["claim_id"]
    if request.get("phase") == "claim":
        return {"claim_text": f"主张-{claim_id}", "latency_ms": 0, "cost": 0}
    return {
        "after_text": f"生成-{request['arm']}-{claim_id}",
        "evidence_id": request["evidence_id"],
        "latency_ms": 0,
        "cost": 0,
    }


def _fake_verifier(_request: Mapping[str, Any]) -> dict[str, Any]:
    return {"ok": True, "score": 1, "reason": ""}


def _fake_transport(request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "model": request["model"],
        "temperature": request["temperature"],
        "thinking": request.get("thinking"),
        "content": _LABEL_LINE,
        "usage": None,
        "refused": None,
    }


def _label_rows(judged: Mapping[str, Any], records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    judges = judged["judges"]
    rows: list[dict[str, Any]] = []
    for record in records:
        claim_id = str(record["claim_id"])
        row: dict[str, Any] = {"claim_id": claim_id}
        for judge_id in JUDGE_IDS:
            row[judge_id] = judges[judge_id]["labels"].get(claim_id, {"A": None, "B": None})
        rows.append(row)
    return rows


def build_report(root: Path | None = None) -> str:
    """串起各段并返回整张表。调用方不传入随机流对象。"""
    repo = _repo_root() if root is None else root
    candidates = _load_candidates(repo)
    ingested = _ingested(candidates)
    decoding = Decoding(temperature=0, seed=SEED)
    arms_result = run_arms(
        candidates,
        generator=_fake_generator,
        verifier=_fake_verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )
    ablation_result = run_ablations(
        candidates,
        generator=_fake_generator,
        verifier=_fake_verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )
    primary = compare_primary(primary_comparison_rows(arms_result))
    intervals = ablation_interval_report(
        arms_result["T"],
        ablation_result,
        ingested_t1=ingested,
        rng=random.Random(SEED),
    )
    t_rows = arms_result["T"]
    with tempfile.TemporaryDirectory(prefix="patch-events-dry-run-") as directory:
        judged = run_judges(t_rows, transport=_fake_transport, logs_dir=Path(directory))
    labels = _label_rows(judged, t_rows)
    spot = export_spotcheck(t_rows, labels, n=30)
    conflicts = export_conflicts(t_rows, labels)
    lines = [
        _BANNER,
        f"seed={SEED}",
        f"n={len(candidates)}",
        "主比较",
    ]
    for item in primary["comparisons"]:
        lines.append(
            f"{item['name']} point={format_rate(item['point'])} "
            f"ci95_low={format_rate(item['ci95_low'])} "
            f"ci95_high={format_rate(item['ci95_high'])} "
            f"established={item['established']}"
        )
    lines.append("消融")
    for item in intervals:
        lines.append(str(item["ablation"]))
    lines.append("抽检")
    lines.append(spot["text"])
    lines.append(f"抽中={len(spot['spotcheck'])}")
    lines.append(conflicts["text"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    _utf8_stdio()
    parser = argparse.ArgumentParser(prog="python -m freshlatch.eval.patch_events_repro")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    root = _repo_root()
    if args.out is not None and _banned(root, args.out):
        return 2
    text = build_report(root)
    sys.stdout.write(text)
    if args.out is not None:
        target = _resolve_out(root, args.out)
        target.mkdir(parents=True, exist_ok=True)
        (target / "dry-run.txt").write_text(text, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
