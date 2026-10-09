"""路线 Y 正式主跑入口（PREREG-Y · n=400 · formal-generations-y）。

须已激活 ``PREREG-Y.md`` 文首，且人授 ``--authorize-send`` 才发模型。
产物只写 ``docs/evidence/patch-events/formal-generations-y.jsonl``，
禁止污染 ``formal-generations-b.jsonl`` / ``formal-generations-c.jsonl`` /
旧 ``formal-generations.jsonl``。
机制继承 B：T/B1 同 after + 软对齐；不以 C 强制抄句为主路径。
n=400 名单针：``SPLIT-pe-v2-route-y.json``（PE-Y-03）。缺额则明示不可激活，
禁止静默改小 ``PREREG-Y`` 配额。
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
from freshlatch.eval.patch_events_construct import (
    ConstructError,
    STRATA,
    construct_from_pins,
)
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
_PE_V2_ROUTE_Y = Path("docs/evidence/patch-events/SPLIT-pe-v2-route-y.json")
_PE_V2_DOCKET = Path("data/pe_v2_docket.json")
_PE_V2_CORPUS = Path("data/corpus/pe_v2")
_PREREG_Y = Path("docs/evidence/patch-events/PREREG-Y.md")
_GENERATIONS_Y = Path("docs/evidence/patch-events/formal-generations-y.jsonl")
_GENERATIONS_B = Path("docs/evidence/patch-events/formal-generations-b.jsonl")
_GENERATIONS_C = Path("docs/evidence/patch-events/formal-generations-c.jsonl")
_FORMAL_LEGACY = Path("docs/evidence/patch-events/formal-generations.jsonl")
_RESULT_Y = Path("docs/evidence/patch-events/RESULT-Y.md")
_EXP_DIR_Y = Path("data/exp/patch-events-y")
_FORMAL_N = 400
_LAYER_N = 100
# 同 after：不发 B1 rewrite；C/T rewrite + B2 claim，再补 B2 diff（继承 B）。
_SEND_Y: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B2", "claim"),
)
_ACTIVATED_MARK = "冲乙正式主跑已激活"
_SHORTFALL_MARK = "不可激活"

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


def route_y_split_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / _PE_V2_ROUTE_Y


def load_route_y_split(root: Path | None = None) -> dict[str, Any]:
    """读取路线 Y 名单针；缺文件即失败（不得回退静默改配额）。"""
    path = route_y_split_path(root)
    if not path.is_file():
        raise RuntimeError(
            f"缺 {_PE_V2_ROUTE_Y.as_posix()}：n=400 名单针未落盘；不可激活"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def n400_quota_targets() -> dict[str, tuple[int, int]]:
    """PREREG-Y 层配额：正确=floor(n/2)，坏=ceil(n/2)。不改预注册页。"""
    correct = _LAYER_N // 2
    bad = _LAYER_N - correct
    return {name: (correct, bad) for name in STRATA}


def route_y_n400_ready(root: Path | None = None) -> bool:
    """名单针是否已凑满 400 且 activation.ready（可加载）。缺额时 False。

    注意：ready ≠ PREREG-Y 已激活 ≠ 过门 ≠ 乙成立。
    """
    payload = load_route_y_split(root)
    if payload.get("status") == _SHORTFALL_MARK:
        return False
    if not (payload.get("activation") or {}).get("ready"):
        return False
    ids = [str(row["claim_id"]) for row in payload.get("n400") or []]
    gap = int((payload.get("gaps") or {}).get("n400") or 0)
    return len(ids) == _FORMAL_N and len(set(ids)) == _FORMAL_N and gap == 0


def _refuse_n400_shortfall(payload: Mapping[str, Any], *, built: int) -> None:
    gap = int((payload.get("gaps") or {}).get("n400") or (_FORMAL_N - built))
    raise RuntimeError(
        f"{_SHORTFALL_MARK}：语料缺额（n400 built={built} target={_FORMAL_N} "
        f"gap={gap}）；不得静默改小 PREREG-Y 配额；见 {_PE_V2_ROUTE_Y.as_posix()}"
    )


def load_pe_v2_formal_n400(root: Path | None = None) -> list[dict[str, Any]]:
    """正式 n=400 名单（PE-Y-03 / PE-Y-CORPUS-02）。

    接 ``SPLIT-pe-v2-route-y.json``。凑满则按针构造恰好 400 条互异记录且与 pilot 无交；
    缺额则显式 ``不可激活`` / 语料缺额失败，**禁止**返回不足 400 条冒充正式集。
    可加载 ≠ 已激活 ``PREREG-Y`` ≠ 过门 ≠ 乙成立。
    """
    base = _repo_root() if root is None else Path(root)
    payload = load_route_y_split(base)
    rows = list(payload.get("n400") or [])
    ids = [str(row["claim_id"]) for row in rows]
    gap = int((payload.get("gaps") or {}).get("n400") or 0)
    ready = bool((payload.get("activation") or {}).get("ready"))
    if (
        payload.get("status") == _SHORTFALL_MARK
        or not ready
        or gap != 0
        or len(ids) != _FORMAL_N
        or len(set(ids)) != _FORMAL_N
    ):
        _refuse_n400_shortfall(payload, built=len(set(ids)))

    pilot_ids = {str(row["claim_id"]) for row in payload.get("pilot") or []}
    if not pilot_ids:
        # 回退读 pe_v2 总清单 pilot，保证隔离不依赖 route-y 是否镜像 pilot。
        base_split = json.loads((base / _PE_V2_SPLIT).read_text(encoding="utf-8"))
        pilot_ids = {str(row["claim_id"]) for row in base_split.get("pilot") or []}
    if set(ids) & pilot_ids:
        raise RuntimeError("正式 n=400 与 pilot 重叠")

    quotas = n400_quota_targets()
    for name in STRATA:
        correct_t, bad_t = quotas[name]
        got_c = sum(
            1
            for row in rows
            if row.get("edit_type") == name and row.get("construction_gold") == "正确"
        )
        got_b = sum(
            1
            for row in rows
            if row.get("edit_type") == name and row.get("construction_gold") == "坏"
        )
        if got_c + got_b != _LAYER_N or (got_c, got_b) != (correct_t, bad_t):
            raise RuntimeError(
                f"n=400 层配额不符：{name} 得 ({got_c},{got_b}) "
                f"目标 ({correct_t},{bad_t})；不得静默改小 PREREG-Y 配额"
            )

    try:
        records = construct_from_pins(
            base / _PE_V2_DOCKET,
            base / _PE_V2_CORPUS,
            rows,
        )
    except ConstructError as exc:
        raise RuntimeError(
            f"{_SHORTFALL_MARK}：n=400 划分里有主张无构造结果 "
            f"（{exc.reason}）；不得静默改小配额"
        ) from exc
    if len(records) != _FORMAL_N:
        raise RuntimeError(
            f"{_SHORTFALL_MARK}：n=400 构造条数 {len(records)}≠{_FORMAL_N}；"
            "不得静默改小配额"
        )
    return records


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


# Y 成立地板：点估计须严格大于该值（与 compare_primary.established 的 point>0 不同）。
_Y_POINT_FLOOR = 0.05

_BC_APPENDIX = (
    "> 路线 B（#480）：k=42；T−C≈0.1190476；ci95_low≈−0.05556 → 丙。  \n"
    "> 路线 C：k=93；T−C≈0.032258；下界=0 → 丙；非 Y 主路径。"
)


def tc_established_y(item: Mapping[str, Any] | None) -> bool:
    """Y 成立尺：仅 T−C · 点>0.05 且 95% 下界>0。

    只读 ``point`` / ``ci95_low``；不读写、不改写 ``established`` 布尔。
    """
    if not item:
        return False
    point = item.get("point")
    low = item.get("ci95_low")
    return (
        isinstance(point, (int, float))
        and isinstance(low, (int, float))
        and point > _Y_POINT_FLOOR
        and low > 0
    )


def outcome_tier(primary: Mapping[str, Any] | None) -> str:
    """乙 / 丙：仅 T−C 按 Y 尺；B1/B2 不参与；永不甲。

    止损：点≤0.05 或下界≤0（含无定义）→ 丙。
    """
    if primary is None:
        return "丙"
    by_name = {item["name"]: item for item in primary.get("comparisons") or []}
    t_c = by_name.get("T-C") or {}
    if tc_established_y(t_c):
        return "乙"
    return "丙"


# 验收/对外别名（与 outcome_tier 同义）。
outcome_tier_y = outcome_tier


def verdict_sentence(tier: str, primary: Mapping[str, Any] | None) -> str:
    """据实判定句。Y 口径：永不判甲；B1/B2 报告-only。"""
    # 防火墙：任何误传「甲」均降为丙文案。
    if tier == "甲":
        tier = "丙"
    if primary is None:
        return "判定：结果丙。主比较无定义或未产出；不得判甲。"
    by_name = {item["name"]: item for item in primary.get("comparisons") or []}

    def _one(name: str) -> str:
        item = by_name.get(name) or {}
        if name == "T-C":
            est = "成立" if tc_established_y(item) else "不成立"
        else:
            est = "报告-only"
        return (
            f"{name} 点估计={format_rate(item.get('point'))} "
            f"95%下界={format_rate(item.get('ci95_low'))} → {est}"
        )

    detail = "；".join(_one(n) for n in ("T-C", "T-B1", "T-B2"))
    k = primary.get("k")
    if tier == "乙":
        return (
            f"判定：结果乙。k={k!r}。仅 T−C 按 Y 尺成立"
            f"（点>{_Y_POINT_FLOOR} 且下界>0）（{detail}）。"
            "不得判甲；T−B1/T−B2 报告-only。"
        )
    return (
        f"判定：结果丙。k={k!r}。T−C 未过 Y 尺或无定义"
        f"（点≤{_Y_POINT_FLOOR} 或下界≤0）（{detail}）。"
        "不得判甲；不得把主实验写成成功。"
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
            "verdict": "判定：结果丙。尚无 formal-generations-y；不得判甲。",
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


def _y_est_cell(name: str, item: Mapping[str, Any] | None, *, filled: bool) -> str:
    """成立（Y 口径）列：仅 T−C 可判；B1/B2 恒报告-only。"""
    if name in ("T-B1", "T-B2"):
        return "报告-only（不参与成立）"
    if not filled:
        return "未填"
    return "成立" if tc_established_y(item) else "不成立"


def render_result_y(
    pack: Mapping[str, Any],
    *,
    code_pin: str,
    activated_note: str,
) -> str:
    """渲染 RESULT-Y：三行主比较 + k + 乙/丙分层。只抄同一次 primary。

    B1/B2 报告-only；成立格只认 T−C（点>0.05∧下界>0）；永不判甲。
    """
    primary = pack.get("primary")
    comparisons = list((primary or {}).get("comparisons") or [])
    by_name = {item.get("name"): item for item in comparisons}
    labels = (("T-C", "T 对 C"), ("T-B1", "T 对 B1"), ("T-B2", "T 对 B2"))
    # 抄表门槛：名单 n=400 且同一次 primary 有定义即可。
    # 单条平台拒回（data_inspection_failed→void）可使 b2_count < 400，不得因此留空成立格。
    filled = primary is not None and pack.get("n") == _FORMAL_N
    lines: list[str] = [
        "# patch_events 路线 Y · 正式结果（RESULT-Y）",
        "",
        "> 口径：`docs/evidence/patch-events/PREREG-Y.md`。",
        "> 三行 false-accept 与 k **只抄**同一次 `compare_primary`（选取 R）。",
        "> **成立格只认 T−C**：点估计 >0.05 且 95% 下界 >0；T−B1 / T−B2 为报告-only。",
        "> 禁止把 GATE-Y-PROBE / 夹具 / RESULT-B / RESULT-C / ALT 抄进成立格。",
        "> 不得判甲；放弃甲防火墙见 `PREREG-Y`。",
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
        "| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立（Y 口径） |",
        "|---|---|---|---|---|---|",
    ]
    if not filled:
        for name, label in labels:
            est = _y_est_cell(name, None, filled=False)
            lines.append(
                f"| {label} | false-accept rate | 未填 | 未填 | 未填 | {est} |"
            )
        k_disp = "未填"
        tier_disp = pack.get("tier")
        if tier_disp in (None, "", "未跑"):
            tier_line = "- **分层**：未跑"
        else:
            tier_line = f"- **分层**：结果{tier_disp}"
        verdict_line = pack.get("verdict") or (
            f"- 判定规则预锁：仅当 T−C 点>{_Y_POINT_FLOOR} 且下界>0 → **结果乙**；"
            "否则（含止损触发）→ **结果丙**。本页**不得**判甲。"
        )
        if not str(verdict_line).startswith("-"):
            verdict_line = f"- {verdict_line}"
    else:
        for name, label in labels:
            item = by_name.get(name) or {}
            est = _y_est_cell(name, item, filled=True)
            lines.append(
                f"| {label} | false-accept rate | {format_rate(item.get('point'))} | "
                f"{format_rate(item.get('ci95_low'))} | "
                f"{format_rate(item.get('ci95_high'))} | {est} |"
            )
        k_disp = repr(primary.get("k"))
        tier_line = f"- **分层**：结果{pack.get('tier')}"
        verdict_line = f"- {pack.get('verdict')}"
    lines.extend(
        [
            "",
            f"- **固定放行数 k** = {k_disp}",
            "",
            "## 甲 / 乙 / 丙判定",
            "",
            tier_line,
            verdict_line,
            "",
            "## B / C 负结果附录（动机 · 非本页成立格）",
            "",
            _BC_APPENDIX,
            "",
            "## 边界",
            "",
            "- 不保证乙；不得判甲；不复活路线 A；不改 B/C 归档。",
            "- 乙成立也不许称优于 RARR·KPR。",
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

    # 与 formal_b 对齐：--authorize-send / --recompute-only 在非 --no-write 时抄 RESULT-Y。
    if not args.no_write:
        out = write_result_y(
            pack,
            code_pin=args.code_pin,
            activated_note=args.activated_note,
        )
        sys.stdout.write(f"wrote {out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
