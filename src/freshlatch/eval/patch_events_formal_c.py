"""路线 C 正式入口（PREREG-C · n=100 · formal-generations-c）。

默认不发模型。须 ``PREREG-C`` 文首已激活且人授 ``--authorize-send`` 才发送。
产物只写 ``docs/evidence/patch-events/formal-generations-c.jsonl``；
禁止写入 ``formal-generations-b.jsonl`` / 旧 ``formal-generations.jsonl``。
回放走 ``run_arms_c``（强制抄句 + 同 after）。
未激活时拒绝正式主跑进主表。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import primary_comparison_rows
from freshlatch.eval.patch_events_arms import Decoding
from freshlatch.eval.patch_events_copy_constrained import run_arms_c
from freshlatch.eval.patch_events_formal import ingested_t1, live_gaps, _saved_generator
from freshlatch.eval.patch_events_formal_b import (
    decoding_pin,
    load_pe_v2_formal_n100,
    outcome_tier,
    verdict_sentence,
)
from freshlatch.eval.patch_events_metrics import SEED, compare_primary, named_streams
from freshlatch.eval.patch_events_send import (
    append_b2_diffs,
    append_sent,
    dispatch_prompt,
    live_chat,
    written_keys,
)
from freshlatch.eval.patch_events_verify import verify_edit

_PE_V2_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2.json")
_PREREG_C = Path("docs/evidence/patch-events/PREREG-C.md")
_GENERATIONS_C = Path("docs/evidence/patch-events/formal-generations-c.jsonl")
_GENERATIONS_B = Path("docs/evidence/patch-events/formal-generations-b.jsonl")
_FORMAL_LEGACY = Path("docs/evidence/patch-events/formal-generations.jsonl")
_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_FORMAL_N = 100
_SEND_C: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_ACTIVATED_LINE = "状态：协议已锁 · 冲甲正式主跑已激活"
_UNACTIVATED_MARK = "未激活"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def prereg_c_activated(root: Path | None = None) -> bool:
    """文首/状态行须为已激活，且不得残留未激活。"""
    base = _repo_root() if root is None else Path(root)
    text = (base / _PREREG_C).read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:8])
    if _UNACTIVATED_MARK in head:
        return False
    return _ACTIVATED_LINE in text or (
        "冲甲正式主跑已激活" in head and _UNACTIVATED_MARK not in head
    )


def generations_c_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / _GENERATIONS_C


def forbidden_generation_targets(root: Path | None = None) -> tuple[Path, Path]:
    """禁止写入的 B / 旧正式生成路径。"""
    base = _repo_root() if root is None else Path(root)
    return base / _GENERATIONS_B, base / _FORMAL_LEGACY


def assert_generations_c_allowed(path: Path, root: Path | None = None) -> None:
    """目标路径不得解析到 b 或旧 formal jsonl。"""
    base = _repo_root() if root is None else Path(root)
    resolved = path.resolve()
    banned_b, banned_legacy = forbidden_generation_targets(base)
    if resolved == banned_b.resolve():
        raise RuntimeError("禁止写入 formal-generations-b.jsonl")
    if resolved == banned_legacy.resolve():
        raise RuntimeError("禁止写入旧 formal-generations.jsonl")
    # 文件名硬闸（防 symlink 绕过名）
    name = resolved.name
    if name == "formal-generations-b.jsonl" or name == "formal-generations.jsonl":
        raise RuntimeError(f"禁止写入禁止文件名: {name}")


def n100_claim_ids(root: Path | None = None) -> list[str]:
    """锁定 SPLIT-pe-v2.json 的正式 n=100 名单针（排除 pilot）。"""
    base = _repo_root() if root is None else Path(root)
    payload = json.loads((base / _PE_V2_SPLIT).read_text(encoding="utf-8"))
    ids = [str(row["claim_id"]) for row in payload["n100"]]
    if len(ids) != _FORMAL_N or len(set(ids)) != _FORMAL_N:
        raise RuntimeError("SPLIT-pe-v2.json 的 n=100 不是 100 条互异主张")
    pilot_ids = {str(row["claim_id"]) for row in payload["pilot"]}
    if set(ids) & pilot_ids:
        raise RuntimeError("正式 n=100 与 pilot 重叠")
    return ids


def load_formal_c_n100(root: Path | None = None) -> list[dict[str, Any]]:
    """与路线 B 同针：``SPLIT-pe-v2.json`` n100 + construct；供 C 正式入口。"""
    return load_pe_v2_formal_n100(root)


def formal_c_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """发送队列：跳过 B1 rewrite（同 after；T 强制抄句由 run_arms_c 落实）。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _SEND_C:
            requests.append(
                {
                    "arm": arm,
                    "phase": phase,
                    "claim_id": row["claim_id"],
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
    return requests


def ensure_generations_c_shell(root: Path | None = None) -> Path:
    """保证 formal-generations-c.jsonl 壳存在（空文件即可）；不写 b/旧路径。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_c_path(base)
    assert_generations_c_allowed(path, base)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def status_pack(root: Path | None = None) -> dict[str, Any]:
    """默认入口只报状态：名单针、路径、是否激活；不发模型。"""
    base = _repo_root() if root is None else Path(root)
    ids = n100_claim_ids(base)
    path = ensure_generations_c_shell(base)
    return {
        "status": "dry",
        "activated": prereg_c_activated(base),
        "n": len(ids),
        "claim_ids_head": ids[:5],
        "claim_ids_tail": ids[-3:],
        "split": _PE_V2_SPLIT.as_posix(),
        "generations_c": path.as_posix(),
        "forbidden": [p.as_posix() for p in forbidden_generation_targets(base)],
        "prereg_c": (base / _PREREG_C).as_posix(),
        "result_c": (base / _RESULT_C).as_posix(),
        "decoding": decoding_pin(),
        "message": (
            "默认不发。未激活时禁止 --authorize-send。"
            "名单针=SPLIT-pe-v2.json n100。"
        ),
    }


def send_formal_c(
    *,
    root: Path | None = None,
    chat: Callable[..., Any] = live_chat,
) -> dict[str, Any]:
    """向 formal-generations-c 发送。调用方须已确认激活 + 授权。"""
    base = _repo_root() if root is None else Path(root)
    if not prereg_c_activated(base):
        raise RuntimeError("PREREG-C 未激活：禁止正式发送")
    path = generations_c_path(base)
    assert_generations_c_allowed(path, base)
    gaps = live_gaps()
    if gaps:
        return {"status": "live_gaps", "gaps": list(gaps), "sent": 0, "path": path}
    rows = load_formal_c_n100(base)
    done = written_keys(path)
    sent = 0
    for request in formal_c_requests(rows):
        key = (str(request["claim_id"]), str(request["arm"]), str(request["phase"]))
        if key in done:
            continue
        result = dispatch_prompt(request, chat)
        if append_sent(path, result):
            done.add(key)
            sent += 1
    b2_added = append_b2_diffs(rows, path, chat)
    return {
        "status": "sent",
        "sent": sent,
        "b2_diff_added": b2_added,
        "path": path,
        "n": len(rows),
        "decoding": decoding_pin(),
    }


def run_formal_c_primary(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """只读 formal-generations-c → run_arms_c → compare_primary（R）。零 LLM。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_c_path(base) if generations_file is None else Path(generations_file)
    if not path.is_absolute():
        path = base / path
    assert_generations_c_allowed(path, base)
    if not path.is_file() or path.stat().st_size == 0:
        return {
            "status": "no_generations",
            "primary": None,
            "arms": None,
            "generations_path": path,
            "generations_n": 0,
            "generations_sha256": (
                hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            ),
            "b2_count": 0,
            "n": 0,
            "tier": "丙",
            "verdict": "判定：结果丙。尚无 formal-generations-c 有效行；不得称甲。",
        }
    generations = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidates = load_formal_c_n100(base)
    ingested = ingested_t1(candidates)
    arms = run_arms_c(
        candidates,
        generator=_saved_generator(generations),
        verifier=verify_edit,
        decoding=Decoding(temperature=0, seed=SEED),
        ingested_t1=ingested,
    )
    b2_count = sum(
        1
        for record in arms["B2"]
        if isinstance(record.get("after_text"), str) and record.get("after_text") != ""
    )
    primary = None
    try:
        primary = compare_primary(
            primary_comparison_rows(arms),
            ingested_t1=ingested,
            streams=named_streams(),
        )
    except ValueError:
        primary = None
    tier = outcome_tier(primary)
    return {
        "status": "recomputed",
        "primary": primary,
        "arms": arms,
        "generations_path": path,
        "generations_n": len(generations),
        "generations_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "b2_count": b2_count,
        "n": len(candidates),
        "tier": tier,
        "verdict": verdict_sentence(tier, primary),
        "decoding": decoding_pin(),
        "claim_ids": [str(row["claim_id"]) for row in candidates],
    }


def main(argv: list[str] | None = None) -> int:
    """默认不发：打印状态并确保 c 壳存在。``--authorize-send`` 须已激活。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_formal_c"
    )
    parser.add_argument(
        "--authorize-send",
        action="store_true",
        help="人授后向 formal-generations-c 发送；默认关闭",
    )
    parser.add_argument(
        "--recompute-only",
        action="store_true",
        help="只复算已保存生成（零 LLM）；未激活时拒绝当作正式主跑收口",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="只打印状态（默认行为）",
    )
    args = parser.parse_args(argv)

    if args.authorize_send and args.recompute_only:
        sys.stderr.write("--authorize-send 与 --recompute-only 互斥\n")
        return 2

    if args.authorize_send:
        if not prereg_c_activated():
            sys.stderr.write("PREREG-C 未激活：拒绝正式主跑发送\n")
            return 2
        try:
            send_result = send_formal_c()
        except RuntimeError as exc:
            sys.stderr.write(f"{exc}\n")
            return 2
        if send_result.get("status") == "live_gaps":
            sys.stderr.write(f"live_gaps={send_result.get('gaps')!r}\n")
            return 2
        sys.stdout.write(
            f"sent={send_result.get('sent')!r} "
            f"b2_diff_added={send_result.get('b2_diff_added')!r}\n"
        )
        return 0

    if args.recompute_only:
        if not prereg_c_activated():
            sys.stderr.write("PREREG-C 未激活：拒绝把复算当作正式主跑收口\n")
            return 2
        pack = run_formal_c_primary()
        primary = pack.get("primary")
        k = None if primary is None else primary.get("k")
        sys.stdout.write(
            f"tier={pack.get('tier')} k={k!r} b2_count={pack.get('b2_count')!r} "
            f"status={pack.get('status')}\n"
        )
        sys.stdout.write(f"{pack.get('verdict')}\n")
        return 0

    # 默认：状态 + 壳；不发
    pack = status_pack()
    sys.stdout.write(json.dumps(pack, ensure_ascii=False, indent=2) + "\n")
    if pack.get("activated"):
        sys.stdout.write("已激活但仍默认不发；须显式 --authorize-send。\n")
    else:
        sys.stdout.write("未激活：禁止正式主跑进主表。\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
