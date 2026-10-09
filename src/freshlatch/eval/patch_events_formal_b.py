"""路线 B 正式主跑入口（PREREG-B · n=100 · formal-generations-b）。

须已激活 ``PREREG-B.md`` 文首，且人授 ``--authorize-send`` 才发模型。
产物只写 ``docs/evidence/patch-events/formal-generations-b.jsonl``，
禁止污染旧 ``formal-generations.jsonl``。
T/B1 同 after：发送队列跳过 B1 rewrite；回放走 ``run_arms`` 同 after 分叉。
主比较只抄同一次 ``compare_primary``（选取 R）写入 ``RESULT-B.md``。
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
from freshlatch.eval.patch_events_arms import Decoding, run_arms
from freshlatch.eval.patch_events_construct import construct_samples
from freshlatch.eval.patch_events_formal import (
    ingested_t1,
    live_gaps,
    _saved_generator,
)
from freshlatch.eval.patch_events_metrics import (
    SEED,
    compare_primary,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_send import (
    append_b2_diffs,
    append_sent,
    dispatch_prompt,
    live_chat,
    written_keys,
)
from freshlatch.eval.patch_events_verify import verify_edit
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_PE_V2_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2.json")
_PE_V2_DOCKET = Path("data/pe_v2_docket.json")
_PE_V2_CORPUS = Path("data/corpus/pe_v2")
_PREREG_B = Path("docs/evidence/patch-events/PREREG-B.md")
_GENERATIONS_B = Path("docs/evidence/patch-events/formal-generations-b.jsonl")
_FORMAL_LEGACY = Path("docs/evidence/patch-events/formal-generations.jsonl")
_RESULT_B = Path("docs/evidence/patch-events/RESULT-B.md")
_FORMAL_N = 100
# 同 after：不发 B1 rewrite；C/T rewrite + B2 claim，再补 B2 diff。
_SEND_B: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_ACTIVATED_MARK = "冲甲正式主跑已激活"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def prereg_b_activated(root: Path | None = None) -> bool:
    """文首须含已激活标记。"""
    base = _repo_root() if root is None else Path(root)
    text = (base / _PREREG_B).read_text(encoding="utf-8")
    return _ACTIVATED_MARK in text.splitlines()[0] or (
        _ACTIVATED_MARK in text and "状态：协议已锁 · 冲甲正式主跑已激活" in text
    )


def generations_b_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / _GENERATIONS_B


def load_pe_v2_formal_n100(root: Path | None = None) -> list[dict[str, Any]]:
    """只取 pe_v2 清单正式 n=100；pilot 不得进入。"""
    base = _repo_root() if root is None else Path(root)
    payload = json.loads((base / _PE_V2_SPLIT).read_text(encoding="utf-8"))
    ids = [str(row["claim_id"]) for row in payload["n100"]]
    if len(ids) != _FORMAL_N or len(set(ids)) != _FORMAL_N:
        raise RuntimeError("SPLIT-pe-v2.json 的 n=100 不是 100 条互异主张")
    pilot_ids = {str(row["claim_id"]) for row in payload["pilot"]}
    if set(ids) & pilot_ids:
        raise RuntimeError("正式 n=100 与 pilot 重叠")
    built = construct_samples(base / _PE_V2_DOCKET, base / _PE_V2_CORPUS)
    by_id = {str(row.record["claim_id"]): row.record for row in built.n100}
    missing = [claim_id for claim_id in ids if claim_id not in by_id]
    if missing:
        raise RuntimeError("正式 n=100 划分里的主张没有构造结果")
    return [dict(by_id[claim_id]) for claim_id in ids]


def formal_b_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """路线 B 发送队列：跳过 B1 rewrite（同 after）。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _SEND_B:
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


def decoding_pin() -> dict[str, Any]:
    entry = MODEL_REGISTRY["default_llm"]
    return {
        "model": DEFAULT_MODEL,
        "registry_model": entry.model,
        "temperature": entry.temperature,
        "decoding_seed": SEED,
        "api_seed": None,
    }


def outcome_tier(primary: Mapping[str, Any] | None) -> str:
    """甲 / 乙 / 丙：同 DECISION-LOG；甲 = 三行均成立。"""
    if primary is None:
        return "丙"
    by_name = {item["name"]: item for item in primary.get("comparisons") or []}
    t_c = by_name.get("T-C") or {}
    t_b1 = by_name.get("T-B1") or {}
    t_b2 = by_name.get("T-B2") or {}
    c_ok = t_c.get("established") is True
    b1_ok = t_b1.get("established") is True
    b2_ok = t_b2.get("established") is True
    if c_ok and b1_ok and b2_ok:
        return "甲"
    if c_ok:
        return "乙"
    return "丙"


def verdict_sentence(tier: str, primary: Mapping[str, Any] | None) -> str:
    """据实判定句。不保证甲；不称全面 SOTA。"""
    if primary is None:
        return "判定：结果丙。主比较无定义或未产出；不得称甲。"
    by_name = {item["name"]: item for item in primary.get("comparisons") or []}

    def _one(name: str) -> str:
        item = by_name.get(name) or {}
        est = "成立" if item.get("established") is True else "不成立"
        return (
            f"{name} 点估计={format_rate(item.get('point'))} "
            f"95%下界={format_rate(item.get('ci95_low'))} → {est}"
        )

    detail = "；".join(_one(n) for n in ("T-C", "T-B1", "T-B2"))
    k = primary.get("k")
    if tier == "甲":
        return (
            f"判定：结果甲。k={k!r}。同一次 compare_primary（R）下 "
            f"T-C、T-B1、T-B2 均成立（{detail}）。"
        )
    if tier == "乙":
        return (
            f"判定：结果乙。k={k!r}。仅第一主比较（T-C）成立，"
            f"T-B1 或 T-B2 至少一条不成立（{detail}）。"
            "不得称优于 RARR·KPR；不得称甲。"
        )
    return (
        f"判定：结果丙。k={k!r}。第一主比较（T-C）不成立或无定义"
        f"（{detail}）。不得称甲；不得把主实验写成成功。"
    )


def run_formal_b_primary(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """只读 formal-generations-b → run_arms（同 after）→ compare_primary（R）。零 LLM。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_b_path(base) if generations_file is None else Path(generations_file)
    if not path.is_absolute():
        path = base / path
    if not path.is_file():
        return {
            "status": "no_generations",
            "primary": None,
            "arms": None,
            "generations_path": path,
            "generations_n": 0,
            "generations_sha256": None,
            "b2_count": 0,
            "n": 0,
            "tier": "丙",
            "verdict": "判定：结果丙。尚无 formal-generations-b；不得称甲。",
        }
    generations = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidates = load_pe_v2_formal_n100(base)
    ingested = ingested_t1(candidates)
    arms = run_arms(
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


def send_formal_b(
    *,
    root: Path | None = None,
    chat: Callable[..., Any] = live_chat,
) -> dict[str, Any]:
    """向 formal-generations-b 发送。调用方须已确认激活 + 授权。"""
    base = _repo_root() if root is None else Path(root)
    if not prereg_b_activated(base):
        raise RuntimeError("PREREG-B 未激活：禁止正式发送")
    path = generations_b_path(base)
    legacy = base / _FORMAL_LEGACY
    if path.resolve() == legacy.resolve():
        raise RuntimeError("禁止写入旧 formal-generations.jsonl")
    gaps = live_gaps()
    if gaps:
        return {"status": "live_gaps", "gaps": list(gaps), "sent": 0, "path": path}
    rows = load_pe_v2_formal_n100(base)
    done = written_keys(path)
    sent = 0
    for request in formal_b_requests(rows):
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


def render_result_b(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    activated_note: str,
) -> str:
    """渲染 RESULT-B：三行主比较 + k + 甲/乙/丙判定。只抄同一次 primary。"""
    primary = pack.get("primary")
    comparisons = list((primary or {}).get("comparisons") or [])
    by_name = {item.get("name"): item for item in comparisons}
    labels = (("T-C", "T 对 C"), ("T-B1", "T 对 B1"), ("T-B2", "T 对 B2"))
    lines: list[str] = [
        "# patch_events 路线 B · 正式结果（RESULT-B）",
        "",
        "> 口径：`docs/evidence/patch-events/PREREG-B.md`（已激活）。",
        "> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。",
        "> 禁止把 GATE-K-PROBE / gate-k-probe-generations / GATE-SEPARATION* 抄进成立格。",
        "> 旧 `RESULT.md` / `PREREG.md` / n=30 链不得当冲甲主证据。",
        "",
        "## 跑针",
        "",
        f"- **代码针**：{code_pin}",
        f"- **激活**：{activated_note}",
        f"- **n** = {pack.get('n')!r}（`load_pe_v2_formal_n100()` / `SPLIT-pe-v2.json` n100）",
        f"- **生成路径**：`{_GENERATIONS_B.as_posix()}`"
        f"（n_lines={pack.get('generations_n')!r}；"
        f"sha256=`{pack.get('generations_sha256')}`）",
        f"- **B2 after 条数**：{pack.get('b2_count')!r}",
        f"- **解码**：model=`{(pack.get('decoding') or {}).get('model')}`；"
        f"temperature=`{(pack.get('decoding') or {}).get('temperature')}`；"
        f"Decoding.seed=`{(pack.get('decoding') or {}).get('decoding_seed')}`；"
        f"API seed=`{(pack.get('decoding') or {}).get('api_seed')}`",
        "",
        "## 主比较（同一次 compare_primary · R）",
        "",
        "| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立 |",
        "|---|---|---|---|---|---|",
    ]
    if primary is None or pack.get("b2_count") != _FORMAL_N:
        for _name, label in labels:
            lines.append(
                f"| {label} | false-accept rate | 未填 | 未填 | 未填 | 未填 |"
            )
        k_disp = "未填"
    else:
        for name, label in labels:
            item = by_name.get(name) or {}
            est = "成立" if item.get("established") is True else "不成立"
            lines.append(
                f"| {label} | false-accept rate | {format_rate(item.get('point'))} | "
                f"{format_rate(item.get('ci95_low'))} | "
                f"{format_rate(item.get('ci95_high'))} | {est} |"
            )
        k_disp = repr(primary.get("k"))
    lines.extend(
        [
            "",
            f"- **固定放行数 k** = {k_disp}",
            "",
            "## 甲 / 乙 / 丙判定",
            "",
            f"- **分层**：结果{pack.get('tier')}",
            f"- {pack.get('verdict')}",
            "",
            "## 边界",
            "",
            "- 不保证甲；不改甲定义；不复活路线 A。",
            "- 不称全面 SOTA；乙也不许称优于 RARR·KPR。",
            "- 同一预注册禁止第二次正式主跑充数。",
            "",
        ]
    )
    return "\n".join(lines)


def write_result_b(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    activated_note: str,
    root: Path | None = None,
    path: Path | None = None,
) -> Path:
    base = _repo_root() if root is None else Path(root)
    out = base / _RESULT_B if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    # 守卫：B2 条数须达 n=100 才许抄成立格；否则仍写页但主表为未填
    text = render_result_b(pack, code_pin=code_pin, activated_note=activated_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """默认不发。``--authorize-send`` 须 PREREG-B 已激活。``--recompute-only`` 零 LLM 抄表。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_formal_b"
    )
    parser.add_argument(
        "--authorize-send",
        action="store_true",
        help="人授后向 formal-generations-b 发送；默认关闭",
    )
    parser.add_argument(
        "--recompute-only",
        action="store_true",
        help="只复算已保存生成并写 RESULT-B；不发送",
    )
    parser.add_argument("--code-pin", default="local")
    parser.add_argument(
        "--activated-note",
        default="PREREG-B 已激活；门闩=GATE-K-PROBE.md",
    )
    parser.add_argument("--no-write", action="store_true", help="只打印，不写 RESULT-B")
    args = parser.parse_args(argv)

    if args.authorize_send and args.recompute_only:
        sys.stderr.write("--authorize-send 与 --recompute-only 互斥\n")
        return 2
    if args.authorize_send and args.no_write:
        sys.stderr.write("--no-write 下拒绝 --authorize-send\n")
        return 2

    if not prereg_b_activated():
        sys.stderr.write("PREREG-B 未激活：拒绝正式主跑\n")
        return 2

    send_result: dict[str, Any] | None = None
    if args.authorize_send:
        send_result = send_formal_b()
        if send_result.get("status") == "live_gaps":
            sys.stderr.write(f"live_gaps={send_result.get('gaps')!r}\n")
            return 2
        sys.stdout.write(
            f"sent={send_result.get('sent')!r} "
            f"b2_diff_added={send_result.get('b2_diff_added')!r}\n"
        )

    pack = run_formal_b_primary()
    primary = pack.get("primary")
    k = None if primary is None else primary.get("k")
    sys.stdout.write(
        f"tier={pack.get('tier')} k={k!r} b2_count={pack.get('b2_count')!r} "
        f"status={pack.get('status')}\n"
    )
    sys.stdout.write(f"{pack.get('verdict')}\n")

    if not args.no_write:
        out = write_result_b(
            pack,
            code_pin=args.code_pin,
            activated_note=args.activated_note,
        )
        sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
