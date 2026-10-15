"""在线 product SLI：轨迹采样 → claim 抽检 → 周报/报警（L4-C-02）。

纯函数。只读轨迹目录，不写盘，不改调用方文件。
不进入注册 G1/A1/T1/R1，不写 RESULT-Y，不写 PREREG floors，
不发明 SESOI，不改地板，不改生产检索臂，不把夹具读数当成注册分变好。
``counted_as_pass`` 恒为 false。采样步长不回写 PREREG。

层身份句（行内 notes 与协议页同一句）：
``observation ≠ RESULT-Y ≠ PREREG floors``。

字段习惯（注释对照，不新建产品主名，不绑定 SaaS）：
- RAGAS faithfulness：主张是否被给定上下文支撑。落点是 groundedness 行。
- Langfuse：对 trace 采样后在 observation 上挂 score。落点是本模块只读 JSONL。
- RAGFlow：chunk citation 是否在场。落点是 evidence_ids / claim_span。
- Arize / LangSmith：span 级 faithful/unfaithful 与在线采样。只说明字段习惯。

夹具 schema 与 ``trajectory_sli`` 相同：目录顶层 ``*.jsonl`` / ``*.json``，不递归。
``run_meta.mode == eval`` 的文件整份排除（金标 / canary 不进 product SLI 分母）。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal, TypedDict

LAYER_PRODUCT_SLI = "product SLI"
OBSERVATION_MARK = "observation ≠ RESULT-Y ≠ PREREG floors"
PLACEHOLDER_INSUFFICIENT = "样本不足"
MISSING_SCORE_VALUE = "缺分"
# 与 docs/ops/抽检-主张忠实.md §4.1 同一起步量。不足则比率写「样本不足」，禁止 0%。
# 这是观测诚实句，不是注册通过线。
MIN_JUDGED_FOR_RATE = 10

ABSTAIN_TOOL = "__verify_abstain__"
_RATE_RE = re.compile(r"^\d+ / \d+$")

ClaimLabel = Literal["abstain", "grounded", "ungrounded", "missing_score"]

PRODUCT_SLI_MANIFEST: dict[str, object] = {
    "ticket": "L4-C-02",
    "layer": LAYER_PRODUCT_SLI,
    "observation_mark": OBSERVATION_MARK,
    "counted_as_pass": False,
    "writes_prereg": False,
    "writes_result_y": False,
    "counted_in_registered_g1_a1_t1_r1": False,
    "invents_sesoi": False,
}


class ProductSliRow(TypedDict):
    """一行 product SLI。比率与占位都是字符串，避免把未计写成 0。"""

    layer: str
    kind: str
    window: str
    metric: str
    value: str
    numerator: int
    denominator: int
    sample_rate: str
    counted_as_pass: bool
    writes_prereg: bool
    notes: str


def aggregate_product_sli(
    trajectory_dir: str | Path,
    *,
    window: str | None = None,
    sample_every: int = 1,
    prior_groundedness: str | None = None,
) -> list[ProductSliRow]:
    """读轨迹目录，返回 product SLI 行。不写盘。

    ``window`` 缺省时用目录路径，表示这一目录就是观测窗口。
    ``sample_every`` 是采样步长：排序后保留下标能被它整除的主张。
    ``1`` 表示全取。步长只出现在本行的 ``sample_rate`` 计数里，不回写 PREREG。
    ``prior_groundedness`` 只能是上一窗本函数写出的 ``N / D`` 字符串。
    与本窗 groundedness 不同才出 drift_watch。没有数字通过线。
    """
    every = _require_sample_every(sample_every)
    root = Path(trajectory_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"轨迹目录不存在: {root}")
    label = root.as_posix() if window is None else window

    units = _claim_units(root)
    seen = len(units)
    kept = [unit for index, unit in enumerate(units) if index % every == 0]
    labels = [classify_claim_events(events) for _claim_id, events in kept]

    n_abstain = labels.count("abstain")
    n_grounded = labels.count("grounded")
    n_ungrounded = labels.count("ungrounded")
    n_missing = labels.count("missing_score")
    n_kept = len(labels)
    grounded_den = n_grounded + n_ungrounded

    sample_rate = _sample_rate(n_kept, seen)
    grounded_value = _rate_value(n_grounded, grounded_den)
    abstain_value = _rate_value(n_abstain, n_kept)

    rows: list[ProductSliRow] = [
        _row(
            kind="weekly",
            window=label,
            metric="groundedness",
            value=grounded_value,
            numerator=n_grounded,
            denominator=grounded_den,
            sample_rate=sample_rate,
            extra="groundedness 分母不含 abstain 与缺分",
        ),
        _row(
            kind="weekly",
            window=label,
            metric="abstain",
            value=abstain_value,
            numerator=n_abstain,
            denominator=n_kept,
            sample_rate=sample_rate,
            extra="abstain 含终态 unknown 与 __verify_abstain__，不进 groundedness 分母",
        ),
    ]
    if n_missing:
        rows.append(
            _row(
                kind="alert",
                window=label,
                metric="missing_score",
                value=MISSING_SCORE_VALUE,
                numerator=n_missing,
                denominator=n_kept,
                sample_rate=sample_rate,
                extra="缺分：非 abstain 终态没有 citation，不记成 0%",
            )
        )
    if _drift(prior_groundedness, grounded_value):
        rows.append(
            _row(
                kind="alert",
                window=label,
                metric="drift_watch",
                value=grounded_value,
                numerator=n_grounded,
                denominator=grounded_den,
                sample_rate=sample_rate,
                extra=(
                    f"相对上一窗 groundedness {prior_groundedness} 不同；"
                    "这是 alert，不是通过线，不回写 PREREG"
                ),
            )
        )
    return rows


def classify_claim_events(events: list[dict]) -> ClaimLabel:
    """一条主张的抽检标签。只读事件，不调用模型。

    abstain 优先于 citation：拒答或终态 unknown 不进 groundedness 分母。
    有 claim_span 时以 span 的支撑为准；否则看 cite_registry_judgment 的 evidence_ids。
    非 abstain 但没有 citation 事件 → missing_score。
    """
    if not events:
        raise ValueError("主张事件为空")
    if not _is_claim_unit(events):
        raise ValueError("没有 claim 或 citation 事件")
    if _is_abstain(events):
        return "abstain"
    citation = _citation_label(events)
    if citation:
        return citation
    return "missing_score"


def format_product_sli_row(row: ProductSliRow) -> str:
    """一行文本。``counted_as_pass=false`` 与 ``writes_prereg=false`` 写死。"""
    return (
        f"product_sli layer={row['layer']} kind={row['kind']} "
        f"window={row['window']} metric={row['metric']} value={row['value']} "
        f"numerator={row['numerator']} denominator={row['denominator']} "
        f"sample_rate={row['sample_rate']} "
        f"counted_as_pass=false writes_prereg=false "
        f"notes={row['notes']}"
    )


def format_product_sli_rows(rows: list[ProductSliRow]) -> str:
    """多行文本，供与质量闸 stdout 对照。末尾带换行。"""
    body = "\n".join(format_product_sli_row(row) for row in rows)
    return body + ("\n" if body else "")


def _require_sample_every(sample_every: int) -> int:
    if isinstance(sample_every, bool) or not isinstance(sample_every, int):
        raise ValueError("sample_every 必须是大于等于 1 的整数")
    if sample_every < 1:
        raise ValueError("sample_every 必须是大于等于 1 的整数")
    return sample_every


def _claim_units(root: Path) -> list[tuple[str, list[dict]]]:
    """生产轨迹里的主张，按文件名与 claim_id 排序。eval 整文件排除。"""
    units: list[tuple[str, str, list[dict]]] = []
    for path in _trajectory_files(root):
        events = _load_events(path)
        if _is_eval_run(events):
            continue
        grouped: dict[str, list[dict]] = {}
        for event in events:
            if not isinstance(event, dict):
                continue
            claim_id = event.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id:
                continue
            grouped.setdefault(claim_id, []).append(event)
        for claim_id in sorted(grouped):
            claim_events = grouped[claim_id]
            if _is_claim_unit(claim_events):
                units.append((path.name, claim_id, claim_events))
    units.sort(key=lambda item: (item[0], item[1]))
    return [(claim_id, events) for _name, claim_id, events in units]


def _trajectory_files(root: Path) -> list[Path]:
    files = [
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl"}
    ]
    return sorted(files, key=lambda path: path.name)


def _load_events(path: Path) -> list[dict]:
    """按后缀读事件。坏 JSON 直接抛出，不把半截文件当成空样本。"""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".jsonl":
        events: list[dict] = []
        for line in text.splitlines():
            body = line.strip()
            if not body:
                continue
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                events.append(parsed)
        return events
    parsed = json.loads(text)
    if isinstance(parsed, list):
        return [item for item in parsed if isinstance(item, dict)]
    if isinstance(parsed, dict):
        inner = parsed.get("events")
        if isinstance(inner, list):
            return [item for item in inner if isinstance(item, dict)]
        if "type" in parsed:
            return [parsed]
    return []


def _is_eval_run(events: list[dict]) -> bool:
    for event in events:
        if event.get("type") == "run_meta" and event.get("mode") == "eval":
            return True
    return False


def _is_claim_unit(events: list[dict]) -> bool:
    for event in events:
        kind = event.get("type")
        if kind in {
            "claim_final",
            "claim_result",
            "cite_registry_judgment",
            "cite_registry_refusal",
            "claim_span",
            "agent_hardening_error",
        }:
            return True
        if kind == "lead_loop_end" and event.get("abstained") is True:
            return True
        if _lead_step_abstain(event):
            return True
    return False


def _is_abstain(events: list[dict]) -> bool:
    if _terminal_status(events) == "unknown":
        return True
    for event in events:
        if event.get("type") == "lead_loop_end" and event.get("abstained") is True:
            return True
        if event.get("type") == "agent_hardening_error":
            return True
        if _lead_step_abstain(event):
            return True
    if _terminal_status(events) is not None:
        return False
    statuses = [
        event.get("status")
        for event in events
        if event.get("type") in {"cite_registry_judgment", "claim_span"}
        and isinstance(event.get("status"), str)
    ]
    return bool(statuses) and all(status == "unknown" for status in statuses)


def _lead_step_abstain(event: dict) -> bool:
    if event.get("type") != "lead_step":
        return False
    if event.get("tool") == ABSTAIN_TOOL:
        return True
    result = event.get("result")
    return isinstance(result, dict) and result.get("abstain") is True


def _terminal_status(events: list[dict]) -> str | None:
    """claim_final 优先于 claim_result。生产终态在 claim_final。"""
    for kind in ("claim_final", "claim_result"):
        matched = [event for event in events if event.get("type") == kind]
        if not matched:
            continue
        status = matched[-1].get("status")
        if isinstance(status, str):
            return status
    return None


def _citation_label(events: list[dict]) -> ClaimLabel | Literal[""]:
    spans = [event for event in events if event.get("type") == "claim_span"]
    if spans:
        if all(_span_supported(event) for event in spans):
            return "grounded"
        return "ungrounded"
    judgments = [
        event for event in events if event.get("type") == "cite_registry_judgment"
    ]
    refusals = [
        event for event in events if event.get("type") == "cite_registry_refusal"
    ]
    if any(_has_evidence_ids(event) for event in judgments):
        return "grounded"
    if judgments or refusals:
        return "ungrounded"
    return ""


def _span_supported(event: dict) -> bool:
    if event.get("unsupported") is True:
        return False
    support = event.get("support")
    return isinstance(support, list) and len(support) > 0


def _has_evidence_ids(event: dict) -> bool:
    evidence_ids = event.get("evidence_ids")
    if not isinstance(evidence_ids, list):
        return False
    return any(isinstance(item, str) and item.strip() for item in evidence_ids)


def _rate_value(numerator: int, denominator: int) -> str:
    """不足起步量或分母为 0 时写「样本不足」，不写 0 / 0 或 0%。"""
    if denominator < MIN_JUDGED_FOR_RATE:
        return PLACEHOLDER_INSUFFICIENT
    return f"{numerator} / {denominator}"


def _sample_rate(kept: int, seen: int) -> str:
    if seen <= 0:
        return PLACEHOLDER_INSUFFICIENT
    return f"{kept} / {seen}"


def _drift(prior: str | None, current: str) -> bool:
    if prior is None:
        return False
    previous = prior.strip()
    if not _RATE_RE.fullmatch(previous) or not _RATE_RE.fullmatch(current):
        return False
    return previous != current


def _row(
    *,
    kind: str,
    window: str,
    metric: str,
    value: str,
    numerator: int,
    denominator: int,
    sample_rate: str,
    extra: str,
) -> ProductSliRow:
    return ProductSliRow(
        layer=LAYER_PRODUCT_SLI,
        kind=kind,
        window=window,
        metric=metric,
        value=value,
        numerator=numerator,
        denominator=denominator,
        sample_rate=sample_rate,
        counted_as_pass=False,
        writes_prereg=False,
        notes=f"{OBSERVATION_MARK}；{extra}",
    )
