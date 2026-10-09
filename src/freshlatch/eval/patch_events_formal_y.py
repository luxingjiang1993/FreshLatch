"""路线 Y 正式主跑入口（PREREG-Y · n=400 · formal-generations-y）。

须已激活 ``PREREG-Y.md`` 文首，且人授 ``--authorize-send`` 才发模型。
产物只写 ``docs/evidence/patch-events/formal-generations-y.jsonl``，
禁止污染 ``formal-generations-b.jsonl`` / ``formal-generations-c.jsonl`` /
旧 ``formal-generations.jsonl``。
机制继承 B：T/B1 同 after + 软对齐；不以 C 强制抄句为主路径。
n=400 名单由 PE-Y-03 实装；本模块仅留桩接口。
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

_PREREG_Y = Path("docs/evidence/patch-events/PREREG-Y.md")
_GENERATIONS_Y = Path("docs/evidence/patch-events/formal-generations-y.jsonl")
_GENERATIONS_B = Path("docs/evidence/patch-events/formal-generations-b.jsonl")
_GENERATIONS_C = Path("docs/evidence/patch-events/formal-generations-c.jsonl")
_FORMAL_LEGACY = Path("docs/evidence/patch-events/formal-generations.jsonl")
_RESULT_Y = Path("docs/evidence/patch-events/RESULT-Y.md")
_EXP_DIR_Y = Path("data/exp/patch-events-y")
_FORMAL_N = 400
# 同 after：不发 B1 rewrite；C/T rewrite + B2 claim，再补 B2 diff（继承 B）。
_SEND_Y: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_ACTIVATED_MARK = "冲乙正式主跑已激活"

# 成功写盘路径不得触及的产物（单测断言）。
FORBIDDEN_GENERATION_PATHS: tuple[Path, ...] = (
    _GENERATIONS_B,
    _GENERATIONS_C,
    _FORMAL_LEGACY,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def prereg_y_activated(root: Path | None = None) -> bool:
    """文首须含已激活标记。"""
    base = _repo_root() if root is None else Path(root)
    text = (base / _PREREG_Y).read_text(encoding="utf-8")
    return _ACTIVATED_MARK in text.splitlines()[0] or (
        _ACTIVATED_MARK in text and "状态：协议已锁 · 冲乙正式主跑已激活" in text
    )


def generations_y_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / _GENERATIONS_Y


def exp_dir_y(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / _EXP_DIR_Y


def load_pe_v2_formal_n400(root: Path | None = None) -> list[dict[str, Any]]:
    """正式 n=400 名单（PE-Y-03）。本票仅留桩，不得假装已有 400 名单。"""
    del root
    raise NotImplementedError(
        "PE-Y-03：n=400 名单针尚未实装（SPLIT-pe-v2-route-y 或显式超集）"
    )


def formal_y_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """路线 Y 发送队列：跳过 B1 rewrite（同 after · 继承 B）。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _SEND_Y:
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
    """占位分层（PE-Y-04 将改为仅 T−C∧点>0.05；永不甲）。

    本票骨架沿用 B 的甲/乙/丙启发式，供 recompute 空跑；正式成立尺见 PE-Y-04。
    """
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
    """据实判定句占位。正式 Y 口径（永不甲）由 PE-Y-04 替换。"""
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
            f"判定：结果甲（骨架占位，PE-Y-04 将禁止甲）。k={k!r}。"
            f"（{detail}）。"
        )
    if tier == "乙":
        return (
            f"判定：结果乙。k={k!r}。仅第一主比较（T-C）成立"
            f"（{detail}）。不得称甲。"
        )
    return (
        f"判定：结果丙。k={k!r}。第一主比较（T-C）不成立或无定义"
        f"（{detail}）。不得称甲；不得把主实验写成成功。"
    )


def run_formal_y_primary(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """只读 formal-generations-y → run_arms → compare_primary（R）。零 LLM。

    无生成文件时安全空跑（不调名单 loader）。有生成文件时须 PE-Y-03 名单就绪。
    """
    base = _repo_root() if root is None else Path(root)
    path = generations_y_path(base) if generations_file is None else Path(generations_file)
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
            "verdict": "判定：结果丙。尚无 formal-generations-y；不得称甲。",
            "decoding": decoding_pin(),
        }
    generations = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    candidates = load_pe_v2_formal_n400(base)
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


def send_formal_y(
    *,
    root: Path | None = None,
    chat: Callable[..., Any] = live_chat,
) -> dict[str, Any]:
    """向 formal-generations-y 发送。调用方须已确认激活 + 授权。"""
    base = _repo_root() if root is None else Path(root)
    if not prereg_y_activated(base):
        raise RuntimeError("PREREG-Y 未激活：禁止正式发送")
    path = generations_y_path(base)
    for forbidden in FORBIDDEN_GENERATION_PATHS:
        if path.resolve() == (base / forbidden).resolve():
            raise RuntimeError(f"禁止写入 {forbidden.as_posix()}")
    gaps = live_gaps()
    if gaps:
        return {"status": "live_gaps", "gaps": list(gaps), "sent": 0, "path": path}
    rows = load_pe_v2_formal_n400(base)
    done = written_keys(path)
    sent = 0
    for request in formal_y_requests(rows):
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


def render_result_y(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    activated_note: str,
) -> str:
    """渲染 RESULT-Y 壳（成立尺细节归 PE-Y-04）。只抄同一次 primary。"""
    primary = pack.get("primary")
    comparisons = list((primary or {}).get("comparisons") or [])
    by_name = {item.get("name"): item for item in comparisons}
    labels = (("T-C", "T 对 C"), ("T-B1", "T 对 B1"), ("T-B2", "T 对 B2"))
    lines: list[str] = [
        "# patch_events 路线 Y · 正式结果（RESULT-Y）",
        "",
        "> 口径：`docs/evidence/patch-events/PREREG-Y.md`。",
        "> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。",
        "> 禁止把 GATE-Y-PROBE / B/C 数字抄进成立格。",
        "> 成立尺（仅 T−C∧点>0.05；永不甲）见 PE-Y-04。",
        "",
        "## 跑针",
        "",
        f"- **代码针**：{code_pin}",
        f"- **激活**：{activated_note}",
        f"- **n** = {pack.get('n')!r}（目标 400；名单见 PE-Y-03）",
        f"- **生成路径**：`{_GENERATIONS_Y.as_posix()}`"
        f"（n_lines={pack.get('generations_n')!r}；"
        f"sha256=`{pack.get('generations_sha256')}`）",
        f"- **日志目录**：`{_EXP_DIR_Y.as_posix()}`",
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
            "## 分层判定（壳）",
            "",
            f"- **分层**：结果{pack.get('tier')}",
            f"- {pack.get('verdict')}",
            "",
            "## 边界",
            "",
            "- 不保证乙；不称甲；不以 C 抄句为主路径。",
            "- 不回写 RESULT-B / RESULT-C / 旧 RESULT。",
            "- 同一预注册禁止第二次正式主跑充数。",
            "",
        ]
    )
    return "\n".join(lines)


def write_result_y(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    activated_note: str,
    root: Path | None = None,
    path: Path | None = None,
) -> Path:
    base = _repo_root() if root is None else Path(root)
    out = base / _RESULT_Y if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    text = render_result_y(pack, code_pin=code_pin, activated_note=activated_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """默认不发。``--authorize-send`` 须 PREREG-Y 已激活。``--recompute-only`` 零 LLM。"""
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_formal_y"
    )
    parser.add_argument(
        "--authorize-send",
        action="store_true",
        help="人授后向 formal-generations-y 发送；默认关闭",
    )
    parser.add_argument(
        "--recompute-only",
        action="store_true",
        help="只复算已保存生成并写 RESULT-Y；不发送",
    )
    parser.add_argument("--code-pin", default="local")
    parser.add_argument(
        "--activated-note",
        default="PREREG-Y 激活态见文首；门闩=GATE-Y-PROBE",
    )
    parser.add_argument("--no-write", action="store_true", help="只打印，不写 RESULT-Y")
    args = parser.parse_args(argv)

    if args.authorize_send and args.recompute_only:
        sys.stderr.write("--authorize-send 与 --recompute-only 互斥\n")
        return 2
    if args.authorize_send and args.no_write:
        sys.stderr.write("--no-write 下拒绝 --authorize-send\n")
        return 2

    if args.authorize_send:
        if not prereg_y_activated():
            sys.stderr.write("PREREG-Y 未激活：拒绝 --authorize-send\n")
            return 2
        send_result = send_formal_y()
        if send_result.get("status") == "live_gaps":
            sys.stderr.write(f"live_gaps={send_result.get('gaps')!r}\n")
            return 2
        sys.stdout.write(
            f"sent={send_result.get('sent')!r} "
            f"b2_diff_added={send_result.get('b2_diff_added')!r}\n"
        )

    if not args.authorize_send and not args.recompute_only:
        # 默认入口：不发模型、不写 generations-y。
        sys.stdout.write(
            "formal-y default: no send "
            f"(activated={prereg_y_activated()}; "
            "require activation + --authorize-send to send)\n"
        )
        pin = decoding_pin()
        sys.stdout.write(
            f"decoding model={pin['model']!r} temperature={pin['temperature']!r} "
            f"decoding_seed={pin['decoding_seed']!r} api_seed={pin['api_seed']!r}\n"
        )
        return 0

    pack = run_formal_y_primary()
    primary = pack.get("primary")
    k = None if primary is None else primary.get("k")
    sys.stdout.write(
        f"tier={pack.get('tier')} k={k!r} b2_count={pack.get('b2_count')!r} "
        f"status={pack.get('status')}\n"
    )
    sys.stdout.write(f"{pack.get('verdict')}\n")

    if not args.no_write and args.recompute_only:
        out = write_result_y(
            pack,
            code_pin=args.code_pin,
            activated_note=args.activated_note,
        )
        sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
