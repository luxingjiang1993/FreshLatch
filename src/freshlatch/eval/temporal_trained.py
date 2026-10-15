"""训练 / 时序检索的新预注册脚手架。

口径锁在 ``docs/evidence/temporal-trained-retrieval/PREREG.md``。
本期没有训练权重,也不把其它臂的名次记成 ``temporal_trained``。
不改 ``PRODUCTION_RETRIEVAL_MODE``。不写冻结 ``neural-rerank`` / 质量闸地板。
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.temporal_arm import TEMPORAL_TRAINED_MODE
from freshlatch.store.checksum import normalize_newlines, sha256_hex

SCHEMA_VERSION = "l4-c-01-v1"
K = 10
METRICS = ("Recall@k", "MRR", "nDCG")
ARM_TEMPORAL_TRAINED = TEMPORAL_TRAINED_MODE
ARM_MRAG_UNTRAINED = "mrag_untrained"
ARMS = (ARM_TEMPORAL_TRAINED, ARM_MRAG_UNTRAINED)
REPLACES_FROZEN_BASELINE = False
MEASUREMENT_STATUS = "unmeasured"
LEVEL = "schema"
MEASUREMENT_NAME = "measurement.json"
CORPUS_REL = Path("data/temporal-trained/v1/corpus.json")
PREREG_REL = Path("docs/evidence/temporal-trained-retrieval/PREREG.md")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DOC_KEYS = ("doc_id", "version_id", "as_of", "valid_from", "text")
_QUERY_KEYS = ("query_id", "query", "query_date", "relevant")
_BLOCKED_CORPUS = (
    ("data", "exp", "x1"),
    ("data", "eval", "gold.json"),
    ("data", "eval", "guard_should.json"),
    ("data", "eval", "cite_sentence.json"),
    ("data", "eval", "temporal_new_over_old.json"),
    ("docs", "evidence", "neural-rerank"),
)
_BLOCKED_OUT = (
    ("docs", "evidence", "neural-rerank"),
    ("docs", "evidence", "quality-gate"),
    ("docs", "evidence", "patch-events"),
    ("data", "exp", "x1"),
    ("data", "eval"),
)


def banned_claim() -> str:
    """官方训练代码未核实公开。返回值只用于拒绝,不写入文档。"""
    return "已复现" + " TempRetriever"


def _reject_banned_claim(text: str) -> None:
    if banned_claim() in text:
        raise ValueError("文本含未核实的训练臂宣称")


def corpus_sha256(data: bytes) -> str:
    """CRLF 折成 LF 再哈希。与质量闸冻结指纹同一换行口径。"""
    return sha256_hex(normalize_newlines(data, "lf"))


def version_key(doc: dict) -> str:
    """版本身份。形状对齐 evidence_id: ``doc_id#version_id@as_of``。"""
    return f"{doc['doc_id']}#{doc['version_id']}@{doc['as_of']}"


def _path_parts(path: Path | str) -> tuple[str, ...]:
    text = str(path).replace("\\", "/").strip()
    stack: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if stack:
                stack.pop()
            continue
        stack.append(part)
    return tuple(stack)


def _path_contains(path: Path | str, needle: tuple[str, ...]) -> bool:
    parts = _path_parts(path)
    width = len(needle)
    if width == 0 or len(parts) < width:
        return False
    return any(parts[index:index + width] == needle for index in range(len(parts) - width + 1))


def _reject_path(path: Path | str, needles: tuple[tuple[str, ...], ...], *, kind: str) -> None:
    for needle in needles:
        if _path_contains(path, needle):
            joined = "/".join(needle)
            raise ValueError(f"拒绝{kind} {joined}")


def _require_date(value: object, label: str) -> str:
    if not isinstance(value, str) or _DATE.fullmatch(value) is None:
        raise ValueError(f"{label} 必须是 YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} 不是合法日期") from exc
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 必须是非空字符串")
    return value


def validate_corpus(corpus: object) -> dict:
    """锁版本语料形状。不打分。"""
    if not isinstance(corpus, dict):
        raise ValueError("语料必须是对象")
    if corpus.get("level") != LEVEL:
        raise ValueError(f"语料 level 必须是 {LEVEL}")
    _require_text(corpus.get("corpus_id"), "corpus_id")
    _require_text(corpus.get("corpus_version"), "corpus_version")
    documents = corpus.get("documents")
    queries = corpus.get("queries")
    if not isinstance(documents, list) or not documents:
        raise ValueError("documents 必须是非空数组")
    if not isinstance(queries, list) or not queries:
        raise ValueError("queries 必须是非空数组")
    keys: set[str] = set()
    versions_by_doc: dict[str, int] = {}
    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            raise ValueError(f"documents[{index}] 必须是对象")
        for key in _DOC_KEYS:
            if key not in doc:
                raise ValueError(f"documents[{index}] 缺少 {key}")
        _require_text(doc["doc_id"], f"documents[{index}].doc_id")
        _require_text(doc["version_id"], f"documents[{index}].version_id")
        _require_text(doc["text"], f"documents[{index}].text")
        _require_date(doc["as_of"], f"documents[{index}].as_of")
        _require_date(doc["valid_from"], f"documents[{index}].valid_from")
        valid_to = doc.get("valid_to")
        if valid_to is not None:
            _require_date(valid_to, f"documents[{index}].valid_to")
        key = version_key(doc)
        if key in keys:
            raise ValueError(f"版本身份重复: {key}")
        keys.add(key)
        versions_by_doc[doc["doc_id"]] = versions_by_doc.get(doc["doc_id"], 0) + 1
    if not any(count >= 2 for count in versions_by_doc.values()):
        raise ValueError("版本语料至少要有同一 doc_id 的两个版本")
    seen_query: set[str] = set()
    for index, row in enumerate(queries):
        if not isinstance(row, dict):
            raise ValueError(f"queries[{index}] 必须是对象")
        for key in _QUERY_KEYS:
            if key not in row:
                raise ValueError(f"queries[{index}] 缺少 {key}")
        query_id = _require_text(row["query_id"], f"queries[{index}].query_id")
        if query_id in seen_query:
            raise ValueError(f"query_id 重复: {query_id}")
        seen_query.add(query_id)
        _require_text(row["query"], f"queries[{index}].query")
        _require_date(row["query_date"], f"queries[{index}].query_date")
        relevant = row["relevant"]
        if not isinstance(relevant, list) or not relevant:
            raise ValueError(f"queries[{index}].relevant 必须是非空数组")
        for item in relevant:
            if not isinstance(item, str) or item not in keys:
                raise ValueError(f"queries[{index}] 的 relevant 不在版本表里: {item}")
    return corpus


def _arm_row(arm: str, *, weights_present: bool) -> dict:
    if arm == ARM_TEMPORAL_TRAINED:
        reason = "scorer_not_landed" if weights_present else "weights_absent"
        kind = "trained_or_published_equivalent"
    elif arm == ARM_MRAG_UNTRAINED:
        reason = "contrast_not_scored"
        kind = "untrained_contrast"
    else:
        raise ValueError(f"未知臂 {arm}")
    return {
        "arm": arm,
        "kind": kind,
        "production_default": False,
        "Recall@k": None,
        "MRR": None,
        "nDCG": None,
        "measurement_status": MEASUREMENT_STATUS,
        "reason": reason,
    }


def build_measurement(
    corpus: dict,
    *,
    corpus_sha256: str,
    weights_present: bool = False,
) -> dict:
    """事前指标的空测量。数字位保持 null,不从冻结 T1/R1 抄值。"""
    validate_corpus(corpus)
    if not re.fullmatch(r"[0-9a-f]{64}", corpus_sha256):
        raise ValueError("corpus_sha256 必须是 64 位小写 hex")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "level": LEVEL,
        "k": K,
        "n": len(corpus["queries"]),
        "metrics": list(METRICS),
        "replaces_frozen_baseline": REPLACES_FROZEN_BASELINE,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "corpus_id": corpus["corpus_id"],
        "corpus_version": corpus["corpus_version"],
        "corpus_sha256": corpus_sha256,
        "frozen_relation": {
            "T1": "does_not_replace",
            "R1": "does_not_replace",
            "frozen_per_query": "docs/evidence/neural-rerank/per-query.json",
            "quality_gate_prereg": "docs/evidence/quality-gate/PREREG.md",
            "registered_value_rewritten": False,
        },
        "counted_as_pass": False,
        "decoding": {
            "temperature": None,
            "seed": None,
            "model": None,
            "note": "schema scaffold, no LLM, no trained weights",
        },
        "weights_present": weights_present,
        "arms": [_arm_row(arm, weights_present=weights_present) for arm in ARMS],
    }
    _reject_scored_metrics(payload)
    return payload


def _reject_scored_metrics(payload: dict) -> None:
    """本期没有打分器。出现数字就拒绝落盘。"""
    for row in payload["arms"]:
        for metric in METRICS:
            if row[metric] is not None:
                raise ValueError(f"{row['arm']} 的 {metric} 本期必须是 null")
        if row["measurement_status"] != MEASUREMENT_STATUS:
            raise ValueError("measurement_status 本期必须是 unmeasured")
    if payload["replaces_frozen_baseline"] is not False:
        raise ValueError("replaces_frozen_baseline 必须是 false")
    if payload["counted_as_pass"] is not False:
        raise ValueError("counted_as_pass 必须是 false")
    if payload["production_retrieval_mode"] != PRODUCTION_RETRIEVAL_MODE:
        raise ValueError("测量不得改写 production_retrieval_mode")


def load_corpus(path: Path) -> tuple[dict, str]:
    _reject_path(path, _BLOCKED_CORPUS, kind="读取受保护路径")
    raw = Path(path).read_bytes()
    digest = corpus_sha256(raw)
    text = normalize_newlines(raw, "lf").decode("utf-8")
    _reject_banned_claim(text)
    corpus = validate_corpus(json.loads(text))
    return corpus, digest


def write_measurement(
    *,
    out_dir: Path,
    corpus_path: Path,
    weights_path: Path | None = None,
) -> dict:
    """写出 measurement.json。不改 PREREG,不写冻结目录。"""
    _reject_path(out_dir, _BLOCKED_OUT, kind="把测量写进")
    corpus, digest = load_corpus(corpus_path)
    weights_present = bool(weights_path is not None and Path(weights_path).is_file())
    payload = build_measurement(
        corpus,
        corpus_sha256=digest,
        weights_present=weights_present,
    )
    document = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _reject_banned_claim(document)
    out = Path(out_dir)
    if out.exists() and not out.is_dir():
        raise ValueError(f"输出路径不是目录: {out.as_posix()}")
    out.mkdir(parents=True, exist_ok=True)
    destination = out / MEASUREMENT_NAME
    if destination.name == "per-query.json":
        raise ValueError("拒绝写入 per-query.json")
    destination.write_text(document, encoding="utf-8", newline="\n")
    payload["json_path"] = destination.as_posix()
    return payload
