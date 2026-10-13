"""离线产品质量闸入口（QG-03）。

命令形状：
`python -m freshlatch.eval quality-gate --offline --prereg docs/evidence/quality-gate/PREREG.md`

只核对冻结身份，并用已有离线资产回放描述数字。通过线仍是 TBD 的列不判失败。
A1、should-refuse / should-pass、new-over-old 保持 unregistered，不得记成通过。
三段金标的字段表挂在 UNREGISTERED_SEGMENTS 上，本模块不创建 JSON，也不按表判分。
不调用付费 LLM，不读取 DASHSCOPE_API_KEY / DEEPSEEK_API_KEY / MOONSHOT_API_KEY。
QG-04 的 1 次新基线运行不在本模块。
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from importlib.metadata import version as dist_version
from pathlib import Path
from typing import Any, Iterator

from freshlatch.eval.retrieve_eval import mrr_at_k, recall_at_k
from freshlatch.eval.retrieve_typed import (
    PREREG_FP_KEYS,
    _full_hit,
    compute_x1_fingerprints,
    conflict_pair_correct,
    fingerprints_match,
    parse_prereg_fingerprints,
    guardrail_pass,
    require_as_of,
    score_role_of,
)
from freshlatch.models import LOCAL_EMBED_MODEL, NEURAL_RERANK_MODEL
from freshlatch.packs import repo_root
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.checksum import normalize_newlines, sha256_hex
from freshlatch.store.local_embed import LOCAL_EMBED_DIM
from freshlatch.store.neural_rerank import NEURAL_RERANK_K
from freshlatch.store.pipeline import RRF_K

# 第 9 节点名的付费密钥。本模块只在守卫里识别这些名字，不读取它们的值。
PAID_ENV_KEYS = frozenset({
    "DASHSCOPE_API_KEY",
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
})

QUESTIONS_REL = Path("data/exp/x1/questions.json")
CORPUS_REL = Path("data/exp/x1/corpus")
TRAPS_REL = Path("data/exp/x1/traps")
CONFIG_REL = Path("data/exp/x1/config.json")
BASELINE_SUMMARY_REL = Path("docs/evidence/neural-rerank/summary.json")
BASELINE_PER_QUERY_REL = Path("docs/evidence/neural-rerank/per-query.json")
EXCLUDED_SUMMARY_REL = Path("docs/evidence/x1-retrieval-modes/summary.json")
TRAP_SMOKE_REL = Path("data/eval/retrieve_traps.json")

QUESTIONS_SHA256 = "2cd7c5fb1e14859049c148e4dafc95b4d3c0abb4fa1080965dcc57b0d57c73fe"
BASELINE_SHA256 = "8fb4f1271b844c979b28bf351cf22ecbad354e3f5f35f7d2e1e7d760efb8e526"
EXCLUDED_SHA256 = "82a14ae9934e59d37f70bb0577e12d45718decd102cd7d51f584896a9f819143"

FROZEN_ARM = "hybrid+rerank"
FROZEN_EMBED_DIM = 512
FROZEN_RRF_K = 60
FROZEN_RERANK_K = 10
FROZEN_FASTEMBED = "0.8.1"
FROZEN_K = 10
N_QUESTIONS = 267
N_ARM = 224
N_GUARDRAIL = 43
N_MULTI_HOP = 45
N_CONFLICT = 3
QUESTION_STATUS = "owner-delegated-model-reviewed"

# G1 / A1 / T1 金标字段表。F2 草稿与 F3 定稿共用。
# final 时 human_row_review 必须为 true，且 reviewer 非空。那是定稿不变量，不是本闸的通过。
# 缺文件，或文件已在但通过线未写死，都仍是 unregistered，counted_as_pass 保持 false。
GOLD_META_FIELDS = (
    "status",
    "human_row_review",
    "reviewer",
)
GOLD_META_STATUSES = frozenset({"draft", "final"})

GUARD_SHOULD_ITEM_FIELDS = (
    "id",
    "policy_id",
    "label",
    "text",
    "source_refs",
)
GUARD_SHOULD_LABELS = frozenset({"should_refuse", "should_pass"})

CITE_SENTENCE_ITEM_FIELDS = (
    "id",
    "sentence",
    "cited_ids",
    "label",
    "source_refs",
)
CITE_SENTENCE_LABELS = frozenset({"supported", "false_cite", "miss_cite"})
# 首版同时报告这两项。Faithfulness 公式不进首版通过线。
CITE_SENTENCE_METRICS = (
    "citation recall",
    "citation precision",
)

TEMPORAL_NEW_OVER_OLD_ITEM_FIELDS = (
    "id",
    "query",
    "as_of",
    "in_force",
    "superseded",
    "source_refs",
)
# 与 R1 Recall@10 分列。不写绝对百分数。
TEMPORAL_NEW_OVER_OLD_METRIC = "new-over-old accuracy"

UNREGISTERED_SEGMENTS = (
    {
        "id": "G1-should-refuse",
        "file": "data/eval/guard_should.json",
        "meta_fields": GOLD_META_FIELDS,
        "item_fields": GUARD_SHOULD_ITEM_FIELDS,
        "labels": GUARD_SHOULD_LABELS,
        "metrics": (),
    },
    {
        "id": "A1",
        "file": "data/eval/cite_sentence.json",
        "meta_fields": GOLD_META_FIELDS,
        "item_fields": CITE_SENTENCE_ITEM_FIELDS,
        "labels": CITE_SENTENCE_LABELS,
        "metrics": CITE_SENTENCE_METRICS,
    },
    {
        "id": "T1-new-over-old",
        "file": "data/eval/temporal_new_over_old.json",
        "meta_fields": GOLD_META_FIELDS,
        "item_fields": TEMPORAL_NEW_OVER_OLD_ITEM_FIELDS,
        "labels": frozenset(),
        "metrics": (TEMPORAL_NEW_OVER_OLD_METRIC,),
    },
)
REQUIRED_METRICS = (
    "R1-recall@10",
    "R1-mrr@10",
    "guardrail-0hit",
    "conflict-pair-ordering",
    "multi-hop-full-hit",
)
TRAP_ROW_ID = "trap-smoke"
ALLOWED_STATUS = frozenset({"unregistered", "TBD", "not_counted"})


class ContractError(Exception):
    """冻结身份或离线契约被打破。不是 TBD 通过线。"""


class PaidKeyRead(Exception):
    """质量闸碰到付费密钥名。异常里只有键名，没有键值。"""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


@dataclass(frozen=True)
class ReportRow:
    """一行报告。counted_as_pass 必须为假，status 不得是 pass。"""

    kind: str
    row_id: str
    status: str
    counted_as_pass: bool
    line: str


@contextmanager
def forbid_paid_env() -> Iterator[None]:
    """挡下付费密钥的读取。命中则抛 PaidKeyRead，不把键值带出来。"""
    cls = type(os.environ)
    orig_get = os.environ.get
    orig_getenv = os.getenv
    orig_getitem = cls.__getitem__
    orig_contains = cls.__contains__

    def guarded_get(key: str, default: str | None = None) -> str | None:
        if key in PAID_ENV_KEYS:
            raise PaidKeyRead(key)
        return orig_get(key, default)

    def guarded_getenv(key: str, default: str | None = None) -> str | None:
        if key in PAID_ENV_KEYS:
            raise PaidKeyRead(key)
        return orig_getenv(key, default)

    def guarded_getitem(self: Any, key: str) -> str:
        if isinstance(key, str) and key in PAID_ENV_KEYS:
            raise PaidKeyRead(key)
        return orig_getitem(self, key)

    def guarded_contains(self: Any, key: object) -> bool:
        if isinstance(key, str) and key in PAID_ENV_KEYS:
            raise PaidKeyRead(key)
        return orig_contains(self, key)

    os.environ.get = guarded_get  # type: ignore[method-assign]
    os.getenv = guarded_getenv  # type: ignore[assignment]
    cls.__getitem__ = guarded_getitem  # type: ignore[method-assign]
    cls.__contains__ = guarded_contains  # type: ignore[method-assign]
    try:
        yield
    finally:
        os.environ.get = orig_get  # type: ignore[method-assign]
        os.getenv = orig_getenv  # type: ignore[assignment]
        cls.__getitem__ = orig_getitem  # type: ignore[method-assign]
        cls.__contains__ = orig_contains  # type: ignore[method-assign]


def parse_owner_freeze(text: str) -> str | None:
    """只认行首的 owner_freeze。全文必须恰好一行。解析器不把散文里的 pending 算进去。"""
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        prefix = "owner_freeze:"
        if stripped.startswith(prefix):
            found.append(stripped[len(prefix):].strip())
    if len(found) != 1:
        return None
    return found[0]


def _fp_line_counts(text: str) -> dict[str, int]:
    counts = {key: 0 for key in PREREG_FP_KEYS}
    for line in text.splitlines():
        stripped = line.strip()
        for key in PREREG_FP_KEYS:
            if stripped.startswith(key + ":"):
                counts[key] += 1
    return counts


def _fmt(value: float) -> str:
    return json.dumps(value)


def _sha256_file(path: Path) -> str:
    """冻结 sha 按 LF 字节。Windows 检出的 CRLF 先折回 LF。"""
    return sha256_hex(normalize_newlines(path.read_bytes(), "lf"))


def build_unregistered_rows(root: Path) -> list[ReportRow]:
    """三段永远 unregistered。文件在磁盘上也不改判成通过。

    字段表只登记在 UNREGISTERED_SEGMENTS。这里不读 JSON，也不看 meta.status。
    """
    rows: list[ReportRow] = []
    for spec in UNREGISTERED_SEGMENTS:
        rel = spec["file"]
        present = (root / rel).is_file()
        flag = "true" if present else "false"
        line = (
            f"segment id={spec['id']} status=unregistered file={rel} "
            f"file_present={flag} counted_as_pass=false"
        )
        rows.append(ReportRow(
            kind="segment",
            row_id=spec["id"],
            status="unregistered",
            counted_as_pass=False,
            line=line,
        ))
    return rows


def _metric_line(
    row_id: str,
    *,
    value: str,
    baseline: str,
    extra: str = "",
) -> ReportRow:
    tail = f" {extra}" if extra else ""
    line = (
        f"metric id={row_id} status=TBD value={value} baseline={baseline}"
        f"{tail} counted_as_pass=false"
    )
    return ReportRow(
        kind="metric",
        row_id=row_id,
        status="TBD",
        counted_as_pass=False,
        line=line,
    )


def enforce_report(rows: list[ReportRow]) -> None:
    """缺 A1、counted_as_pass=true，或把 unregistered / TBD 印成 pass 时，本次运行不能以 0 结束。"""
    if not rows:
        raise ContractError("报告没有行")
    by_id = {row.row_id: row for row in rows}
    if len(by_id) != len(rows):
        raise ContractError("报告行 id 重复")
    for spec in UNREGISTERED_SEGMENTS:
        row = by_id.get(spec["id"])
        if row is None or row.status != "unregistered":
            raise ContractError(f"{spec['id']} 缺失或不是 unregistered")
    for row_id in REQUIRED_METRICS:
        row = by_id.get(row_id)
        if row is None or row.status != "TBD":
            raise ContractError(f"{row_id} 缺失或不是 TBD")
    trap = by_id.get(TRAP_ROW_ID)
    if trap is None or trap.status != "not_counted":
        raise ContractError("陷阱冒烟缺失或被记入分母")
    for row in rows:
        if row.counted_as_pass:
            raise ContractError(f"{row.row_id} 被记成通过")
        if row.status not in ALLOWED_STATUS:
            raise ContractError(f"{row.row_id} 状态不可作为通过")
        if "counted_as_pass=false" not in row.line:
            raise ContractError(f"{row.row_id} 行未标明 counted_as_pass=false")
        if "status=pass" in row.line or "counted_as_pass=true" in row.line:
            raise ContractError(f"{row.row_id} 打印成 pass")
        if f"status={row.status}" not in row.line:
            raise ContractError(f"{row.row_id} 行与状态不一致")


def score_guardrail_hits(hits_by_question: list[list[Any]]) -> float:
    """护栏 0-hit。空列表不当成通过。query_as_of 由 guardrail_pass 丢弃，检查的是返回块。"""
    if not hits_by_question:
        raise ContractError("护栏命中列表为空")
    flags = [
        1.0 if guardrail_pass(hits, query_as_of="T1") else 0.0
        for hits in hits_by_question
    ]
    return sum(flags) / len(flags)


def _load_queries(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("题集不是 JSON") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("queries"), list):
        raise ContractError("题集缺少 queries")
    meta = raw.get("meta")
    if not isinstance(meta, dict):
        raise ContractError("题集缺少 meta")
    return raw, list(raw["queries"])


def _check_questions(root: Path, prereg_text: str) -> list[dict[str, Any]]:
    path = root / QUESTIONS_REL
    if not path.is_file():
        raise ContractError(f"题集不存在: {QUESTIONS_REL.as_posix()}")
    digest = _sha256_file(path)
    if digest != QUESTIONS_SHA256:
        raise ContractError("题集 sha256 不一致")
    if QUESTIONS_SHA256 not in prereg_text:
        raise ContractError("预注册未写明题集 sha256")
    document, queries = _load_queries(path)
    meta = document["meta"]
    if meta.get("human_row_review") is not False:
        raise ContractError("human_row_review 不是 false")
    if meta.get("status") != QUESTION_STATUS:
        raise ContractError("题集 status 与冻结标注不一致")
    n_arm = 0
    n_guard = 0
    n_hop = 0
    n_pair = 0
    for item in queries:
        try:
            require_as_of(item)
        except ValueError as exc:
            raise ContractError(str(exc)) from exc
        role = score_role_of(item)
        if role == "arm":
            n_arm += 1
            if item.get("qtype") == "multi_hop":
                n_hop += 1
        elif role == "guardrail":
            n_guard += 1
        else:
            raise ContractError(f"未知 score_role: {role}")
        pair = item.get("conflict_pair")
        if isinstance(pair, dict) and pair.get("in_force") and pair.get("superseded"):
            if role != "arm":
                raise ContractError("conflict_pair 不在 arm 内")
            n_pair += 1
    if len(queries) != N_QUESTIONS or n_arm != N_ARM or n_guard != N_GUARDRAIL:
        raise ContractError(
            f"分母计数不一致 n={len(queries)} arm={n_arm} guardrail={n_guard}"
        )
    if n_hop != N_MULTI_HOP or n_pair != N_CONFLICT:
        raise ContractError(f"切片计数不一致 multi_hop={n_hop} conflict_pair={n_pair}")
    return queries


def _check_pins(root: Path, prereg_text: str) -> str:
    """模型 id 只跟注册表和预注册正文对照，不在本文件再写一份字面量。"""
    mismatches: list[str] = []
    if PRODUCTION_RETRIEVAL_MODE != FROZEN_ARM:
        mismatches.append(f"arm={PRODUCTION_RETRIEVAL_MODE}")
    if LOCAL_EMBED_DIM != FROZEN_EMBED_DIM:
        mismatches.append(f"embed_dim={LOCAL_EMBED_DIM}")
    if LOCAL_EMBED_MODEL not in prereg_text or f"dim {LOCAL_EMBED_DIM}" not in prereg_text:
        mismatches.append("预注册未写明本地 embedding")
    if RRF_K != FROZEN_RRF_K:
        mismatches.append(f"rrf_k={RRF_K}")
    if NEURAL_RERANK_K != FROZEN_RERANK_K:
        mismatches.append(f"rerank_k={NEURAL_RERANK_K}")
    if NEURAL_RERANK_MODEL not in prereg_text:
        mismatches.append("预注册未写明精排模型")
    fastembed_ver = dist_version("fastembed")
    if fastembed_ver != FROZEN_FASTEMBED:
        mismatches.append(f"fastembed={fastembed_ver}")
    pin = f"fastembed=={FROZEN_FASTEMBED}"
    for rel in (Path("requirements.txt"), Path("pyproject.toml")):
        text = (root / rel).read_text(encoding="utf-8")
        if pin not in text:
            mismatches.append(f"{rel.as_posix()} 缺少 {pin}")
    if mismatches:
        raise ContractError("生产臂针不一致: " + ", ".join(mismatches))
    return fastembed_ver


def _check_summaries(root: Path, prereg_text: str) -> tuple[float, float]:
    baseline_path = root / BASELINE_SUMMARY_REL
    excluded_path = root / EXCLUDED_SUMMARY_REL
    if not baseline_path.is_file():
        raise ContractError("神经基线摘要不存在")
    if not excluded_path.is_file():
        raise ContractError("被排除的词面摘要不存在")
    baseline_sha = _sha256_file(baseline_path)
    excluded_sha = _sha256_file(excluded_path)
    if baseline_sha != BASELINE_SHA256:
        raise ContractError("基线摘要 sha256 不一致")
    if excluded_sha != EXCLUDED_SHA256:
        raise ContractError("被排除的词面摘要 sha256 不一致")
    if BASELINE_SHA256 not in prereg_text or EXCLUDED_SHA256 not in prereg_text:
        raise ContractError("预注册未写明基线或排除摘要 sha256")
    try:
        payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("基线摘要不是 JSON") from exc
    try:
        recall = float(payload["k10"]["recall"]["right_mean"])
        mrr = float(payload["k10"]["mrr"]["right_mean"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("基线摘要缺少 k10 右臂 Recall/MRR") from exc
    return recall, mrr


def _neural_rankings(root: Path) -> dict[str, list[str]] | None:
    """只读冻结 per-query 的 k10 神经名次。文件不在则没有本次回放。"""
    path = root / BASELINE_PER_QUERY_REL
    if not path.is_file():
        return None
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("per-query 不是 JSON") from exc
    if not isinstance(rows, list):
        raise ContractError("per-query 不是数组")
    ranked_by_id: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, dict) or "id" not in row:
            raise ContractError("per-query 行缺少 id")
        qid = str(row["id"])
        if qid in ranked_by_id:
            raise ContractError(f"per-query id 重复: {qid}")
        try:
            raw_ranked = row["k10"]["neural_ranked"]
        except (KeyError, TypeError) as exc:
            raise ContractError(f"{qid} 缺少 k10 神经名次") from exc
        if not isinstance(raw_ranked, list):
            raise ContractError(f"{qid} 神经名次不是列表")
        ranked_by_id[qid] = [str(item) for item in raw_ranked]
    return ranked_by_id


def _replay_arm(
    queries: list[dict[str, Any]],
    ranked_by_id: dict[str, list[str]],
) -> dict[str, float | int]:
    arm_ids = [str(item["id"]) for item in queries if score_role_of(item) == "arm"]
    if set(ranked_by_id) != set(arm_ids):
        raise ContractError("离线名次未恰好覆盖 arm 分母")
    recalls: list[float] = []
    mrrs: list[float] = []
    fulls: list[float] = []
    pair_ok = 0
    pair_n = 0
    for item in queries:
        if score_role_of(item) != "arm":
            continue
        qid = str(item["id"])
        ranked = ranked_by_id[qid]
        relevant = item.get("relevant")
        if not isinstance(relevant, list):
            raise ContractError(f"{qid} 缺少 relevant")
        relevant_ids = [str(eid) for eid in relevant]
        recalls.append(recall_at_k(ranked, relevant_ids, FROZEN_K))
        mrrs.append(mrr_at_k(ranked, relevant_ids, FROZEN_K))
        if item.get("qtype") == "multi_hop":
            fulls.append(_full_hit(ranked, relevant_ids, FROZEN_K))
        pair = item.get("conflict_pair")
        if isinstance(pair, dict) and pair.get("in_force") and pair.get("superseded"):
            pair_n += 1
            if conflict_pair_correct(ranked, pair):
                pair_ok += 1
    if len(recalls) != N_ARM or len(fulls) != N_MULTI_HOP or pair_n != N_CONFLICT:
        raise ContractError("回放分母与冻结切片不一致")
    return {
        "recall": sum(recalls) / len(recalls),
        "mrr": sum(mrrs) / len(mrrs),
        "full_hit": sum(fulls) / len(fulls),
        "pair_ok": pair_ok,
        "pair_n": pair_n,
    }


def _trap_row(root: Path) -> ReportRow:
    """冒烟三题不进分母，也不调用 BM25 检索。"""
    path = root / TRAP_SMOKE_REL
    rel = TRAP_SMOKE_REL.as_posix()
    if not path.is_file():
        line = (
            f"trap_smoke id={TRAP_ROW_ID} status=not_counted file={rel} "
            "present=false in_denominator=false counted_as_pass=false"
        )
        return ReportRow(
            kind="trap",
            row_id=TRAP_ROW_ID,
            status="not_counted",
            counted_as_pass=False,
            line=line,
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError("陷阱冒烟文件不是 JSON") from exc
    queries = payload.get("queries") if isinstance(payload, dict) else None
    n = len(queries) if isinstance(queries, list) else 0
    level = payload.get("level") if isinstance(payload, dict) else None
    level_text = level if isinstance(level, str) else "missing"
    line = (
        f"trap_smoke id={TRAP_ROW_ID} status=not_counted file={rel} "
        f"present=true level={level_text} n={n} in_denominator=false counted_as_pass=false"
    )
    return ReportRow(
        kind="trap",
        row_id=TRAP_ROW_ID,
        status="not_counted",
        counted_as_pass=False,
        line=line,
    )


def _run(
    *,
    offline: bool,
    prereg: str | None,
    live_invocation: str | None,
    guardrail_hits: list[list[Any]] | None,
    replay_baseline: tuple[float, float] | None,
) -> int:
    if not offline:
        print("拒绝：未设置 --offline，质量闸不得调用 live LLM。", file=sys.stderr)
        return 2
    if live_invocation and live_invocation.strip():
        print(f"拒绝 live 路径: {live_invocation.strip()}", file=sys.stderr)
        return 2
    if prereg is None or not str(prereg).strip():
        print("预注册文件缺失", file=sys.stderr)
        return 1
    prereg_path = Path(prereg)
    if not prereg_path.is_file():
        print(f"预注册文件不存在: {prereg_path}", file=sys.stderr)
        return 1

    root = repo_root()
    text = prereg_path.read_text(encoding="utf-8")
    owner = parse_owner_freeze(text)
    if owner != "confirmed":
        shown = owner if owner is not None else "缺失或重复"
        print(
            f"owner_freeze 不是 confirmed（读到 {shown}）。本次不能称为锁定产品质量闸。",
            file=sys.stderr,
        )
        return 1
    counts = _fp_line_counts(text)
    if any(counts[key] != 1 for key in PREREG_FP_KEYS):
        raise ContractError("预注册指纹行不是各一行")
    computed = compute_x1_fingerprints(
        corpus=root / CORPUS_REL,
        traps=root / TRAPS_REL,
        questions=root / QUESTIONS_REL,
        config=root / CONFIG_REL,
        newline="lf",
    )
    if not fingerprints_match(text, computed):
        parsed = parse_prereg_fingerprints(text)
        detail = ["指纹不一致"]
        for key in PREREG_FP_KEYS:
            detail.append(f"  {key} file={parsed.get(key)} computed={computed.get(key)}")
        print("\n".join(detail), file=sys.stderr)
        return 1

    fastembed_ver = _check_pins(root, text)
    queries = _check_questions(root, text)
    baseline_recall, baseline_mrr = _check_summaries(root, text)
    if replay_baseline is not None:
        baseline_recall, baseline_mrr = replay_baseline

    rankings = _neural_rankings(root)
    replay_source = "frozen-per-query-replay" if rankings is not None else "baseline-file-only"
    recall_value = "unavailable"
    mrr_value = "unavailable"
    full_value = "unavailable"
    pair_value = "unavailable"
    pair_extra = f"n={N_CONFLICT}"
    full_extra = f"n={N_MULTI_HOP}"
    recall_extra = f"source={replay_source}"
    mrr_extra = f"source={replay_source}"
    if rankings is not None:
        replay = _replay_arm(queries, rankings)
        got_recall = float(replay["recall"])
        got_mrr = float(replay["mrr"])
        if got_recall != baseline_recall or got_mrr != baseline_mrr:
            raise ContractError(
                "确定性回放与冻结基线描述不一致 "
                f"recall={_fmt(got_recall)}/{_fmt(baseline_recall)} "
                f"mrr={_fmt(got_mrr)}/{_fmt(baseline_mrr)}"
            )
        recall_value = _fmt(got_recall)
        mrr_value = _fmt(got_mrr)
        recall_extra += f" delta={_fmt(got_recall - baseline_recall)}"
        mrr_extra += f" delta={_fmt(got_mrr - baseline_mrr)}"
        full_value = _fmt(float(replay["full_hit"]))
        pair_ok = int(replay["pair_ok"])
        pair_n = int(replay["pair_n"])
        pair_value = _fmt(pair_ok / pair_n)
        pair_extra = f"correct={pair_ok} n={pair_n} source={replay_source}"
        full_extra = f"n={N_MULTI_HOP} source={replay_source}"

    if guardrail_hits is None:
        guard_value = "unavailable"
        guard_extra = f"n={N_GUARDRAIL} source=no-guardrail-hits"
    else:
        if len(guardrail_hits) != N_GUARDRAIL:
            raise ContractError(
                f"护栏命中条数 {len(guardrail_hits)} 与分母 {N_GUARDRAIL} 不一致"
            )
        guard_value = _fmt(score_guardrail_hits(guardrail_hits))
        guard_extra = f"n={N_GUARDRAIL} source=guardrail_pass"

    rows = [
        *build_unregistered_rows(root),
        _metric_line(
            "R1-recall@10",
            value=recall_value,
            baseline=_fmt(baseline_recall),
            extra=recall_extra,
        ),
        _metric_line(
            "R1-mrr@10",
            value=mrr_value,
            baseline=_fmt(baseline_mrr),
            extra=mrr_extra,
        ),
        _metric_line(
            "guardrail-0hit",
            value=guard_value,
            baseline="none",
            extra=guard_extra,
        ),
        _metric_line(
            "conflict-pair-ordering",
            value=pair_value,
            baseline="none",
            extra=pair_extra,
        ),
        _metric_line(
            "multi-hop-full-hit",
            value=full_value,
            baseline="none",
            extra=full_extra,
        ),
        _trap_row(root),
    ]
    enforce_report(rows)
    header = [
        "离线产品质量闸",
        "offline=true",
        "locked_gate=true",
        "owner_freeze=confirmed",
        "fingerprints=match",
        f"arm={PRODUCTION_RETRIEVAL_MODE}",
        f"embed_model={LOCAL_EMBED_MODEL}",
        f"embed_dim={LOCAL_EMBED_DIM}",
        f"rrf_k={RRF_K}",
        f"rerank_model={NEURAL_RERANK_MODEL}",
        f"rerank_k={NEURAL_RERANK_K}",
        f"fastembed={fastembed_ver}",
        f"denominator={QUESTIONS_REL.as_posix()}",
        f"n={N_QUESTIONS}",
        f"n_arm={N_ARM}",
        f"n_guardrail={N_GUARDRAIL}",
        f"questions_sha256={QUESTIONS_SHA256}",
        f"baseline={BASELINE_SUMMARY_REL.as_posix()}",
        f"baseline_sha256={BASELINE_SHA256}",
        "excluded_lexical_used=false",
        "paid_llm=false",
        "qg04=separate",
    ]
    print("\n".join(header + [row.line for row in rows]), flush=True)
    return 0


def run_quality_gate(
    *,
    offline: bool,
    prereg: str | None,
    live_invocation: str | None = None,
    guardrail_hits: list[list[Any]] | None = None,
    replay_baseline: tuple[float, float] | None = None,
) -> int:
    """离线闸。退出码 2 是 live 拒绝；1 是契约破坏；0 是不变量成立且未登记段已标明。"""
    try:
        with forbid_paid_env():
            return _run(
                offline=offline,
                prereg=prereg,
                live_invocation=live_invocation,
                guardrail_hits=guardrail_hits,
                replay_baseline=replay_baseline,
            )
    except PaidKeyRead as exc:
        print(f"拒绝读取付费密钥 {exc.key}", file=sys.stderr)
        return 2
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 1
