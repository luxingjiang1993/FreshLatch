"""x1 许可、8-gram 去污染与题集结构检查（RET-01.1）。

零 LLM、零网络。阈值缺键或 JSON null 时退出码 2，不得代入任何缺省数字。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from freshlatch.evidence_id import parse_evidence_id
from freshlatch.store.base import Chunk, chunk_evidence_id
from freshlatch.store.ingest import AS_OF_DIR, META_RE, load_corpus

# 地板常量（与 RET-01 配置键一致）。测试可覆盖应用值，不可改这些字面量。
MIN_CHUNKS = 600
MIN_PER_QTYPE = 30
MIN_TRAP_ADVERSARIAL_RATIO = 0.30
MIN_SYNTHETIC_RATIO = 0.60
MAX_PUBLIC_RATIO = 0.40

LOCKED_CONFIG = {
    "top_k": 10,
    "rrf_k": 60,
    "embed_model": "text-embedding-v4",
    "embed_dim": 1024,
    "draft_model": "qwen-flash",
    "flag_model": "qwen-plus",
    "flag_thinking": False,
    "lead_delta": 0.10,
    "budget_cny_max": 10,
}

LICENSE_WHITELIST = frozenset(
    {
        "synthetic",
        "PRC-Copyright-Art5",
        "US-Gov-17USC105",
        "CC0-1.0",
        "CC-BY-4.0",
    }
)
ZERO_COUNT_LICENSES = frozenset({"US-Gov-17USC105", "CC0-1.0", "CC-BY-4.0"})
PUBLIC_LICENSES = frozenset(
    {"PRC-Copyright-Art5", "US-Gov-17USC105", "CC0-1.0", "CC-BY-4.0"}
)
DOMAINS = frozenset({"D0", "D1", "D2", "D3"})
GENRES = frozenset({f"S{i}" for i in range(1, 8)} | {"P1", "P2"})
SOURCE_TYPES = frozenset({"private", "public", "internal"})
QTYPES = frozenset({"lexical", "paraphrase", "multi_hop"})
CATEGORIES = frozenset({"hard", "trap", "adversarial"})
SCORE_ROLES = frozenset({"arm", "guardrail"})

# 清洗后的法规名白名单，长名在前。
LAW_NAMES = (
    "中华人民共和国公司法",
    "个人信息出境标准合同办法",
    "促进和规范数据跨境流动规定",
    "数据出境安全评估办法",
    "个人信息出境认证办法",
    "公司法",
)

LCS_FLAG_MIN = 0.8
LEXICAL_MIN_LEN = 8
NGRAM = 8
# 块正文开头的条款标题，清洗前剥掉，避免 pN 粘到正文上。
_CLAUSE_HEADING = re.compile(r"^## p\d+[ \t]*(?:\n|$)")


@dataclass
class CheckResult:
    """一次 x1 检查的汇总。"""

    exit_code: int
    qtype_counts: dict[str, int]
    n_arm: int
    n_guardrail: int
    trap_adversarial_ratio: float
    n_chunks: int
    synthetic_ratio: float
    public_ratio: float
    decontam_hits: int
    license_violations: int
    lcs_flags: int
    records: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def format_report(self) -> str:
        lines = [
            f"qtype lexical={self.qtype_counts.get('lexical', 0)} "
            f"paraphrase={self.qtype_counts.get('paraphrase', 0)} "
            f"multi_hop={self.qtype_counts.get('multi_hop', 0)}",
            f"n_arm={self.n_arm} trap_adversarial_ratio={self.trap_adversarial_ratio:.4f}",
            f"chunks={self.n_chunks} synthetic_ratio={self.synthetic_ratio:.4f} "
            f"public_ratio={self.public_ratio:.4f}",
            f"decontam_hits={self.decontam_hits} license_violations={self.license_violations}",
            f"lcs_flags={self.lcs_flags} guardrail={self.n_guardrail}",
        ]
        lines.extend(self.records)
        for msg in self.messages:
            lines.append(f"msg {msg}")
        return "\n".join(lines) + "\n"


def strip_clause_heading(text: str) -> str:
    """去掉块开头的 ``## pN`` 标题行。"""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    m = _CLAUSE_HEADING.match(normalized)
    if m:
        return normalized[m.end() :]
    return normalized


def clean_text(text: str) -> str:
    """删掉 Unicode 类别 P（标点）、Z（分隔符）与 Cc（控制字符，含 \\n \\t \\r）。

    不做大小写折叠，不做繁简转换。
    """
    out: list[str] = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat[0] in {"P", "Z"} or cat == "Cc":
            continue
        out.append(ch)
    return "".join(out)


def clean_chunk_text(text: str) -> str:
    """块正文：先剥 ``## pN`` 标题行，再按 clean_text 清洗。"""
    return clean_text(strip_clause_heading(text))


def strip_law_names(cleaned_query: str) -> str:
    """只从已清洗 query 删除法规名；先删更长的名字。块正文不删。"""
    names = sorted(LAW_NAMES, key=len, reverse=True)
    out = cleaned_query
    for name in names:
        out = out.replace(name, "")
    return out


def char_8grams(text: str) -> set[str]:
    """清洗后字符串上连续 8 个 Unicode 码位的滑窗集合。"""
    if len(text) < NGRAM:
        return set()
    return {text[i : i + NGRAM] for i in range(len(text) - NGRAM + 1)}


def eight_gram_overlap(query_clean: str, chunk_texts_clean: list[str]) -> float | None:
    """query 的 8-gram 里出现在任一 relevant 块中的比例。集合为空则无法检查，返回 None。"""
    q_grams = char_8grams(query_clean)
    if not q_grams:
        return None
    body_grams: set[str] = set()
    for body in chunk_texts_clean:
        body_grams |= char_8grams(body)
    hit = sum(1 for g in q_grams if g in body_grams)
    return hit / len(q_grams)


def lcs_length(a: str, b: str) -> int:
    """字符最长公共子序列长度（不要求连续）。"""
    if not a or not b:
        return 0
    if len(a) > len(b):
        a, b = b, a
    prev = [0] * (len(a) + 1)
    for ch_b in b:
        curr = [0]
        for j, ch_a in enumerate(a):
            if ch_b == ch_a:
                curr.append(prev[j] + 1)
            else:
                curr.append(max(prev[j + 1], curr[-1]))
        prev = curr
    return prev[-1]


def lcs_ratio(query_clean: str, chunk_texts_clean: list[str]) -> float | None:
    """删白名单后的 query 与任一 relevant 块清洗正文的 LCS / query 长度，取最大。"""
    if not query_clean:
        return None
    best = 0
    for body in chunk_texts_clean:
        best = max(best, lcs_length(query_clean, body))
    return best / len(query_clean)


def _parse_frontmatter(text: str) -> dict[str, str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    m = META_RE.match(text)
    meta: dict[str, str] = {}
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta


def _load_extra_meta(root: Path) -> dict[tuple[str, str], dict[str, str]]:
    """按 (doc_id, as_of) 读取 ingest 会丢弃的许可字段。不改 ingest。"""
    out: dict[tuple[str, str], dict[str, str]] = {}
    if not root.is_dir():
        return out
    for as_of_dir, as_of in AS_OF_DIR.items():
        for path in sorted((root / as_of_dir).glob("*.md")):
            meta = _parse_frontmatter(path.read_text(encoding="utf-8"))
            doc_id = meta.get("doc_id", "")
            if doc_id:
                out[(doc_id, as_of)] = meta
    return out


def _load_all_chunks(corpus_dir: Path, traps_dir: Path) -> list[Chunk]:
    pairs = list(load_corpus(corpus_dir))
    if traps_dir.is_dir():
        pairs.extend(load_corpus(traps_dir))
    chunks: list[Chunk] = []
    for _doc, cs in pairs:
        chunks.extend(cs)
    return chunks


def _load_questions(source: Path | str | list | dict) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return list(source)
    if isinstance(source, dict):
        qs = source.get("queries", source)
        if isinstance(qs, list):
            return list(qs)
        raise ValueError("questions JSON 需要 queries 数组")
    path = Path(source)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return _load_questions(raw)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _fmt_opt_float(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.6f}"


def _record_line(
    qid: str,
    r8: float | None,
    lcs: float | None,
    lcs_flag: int,
    decontam: int,
    score_role: str,
) -> str:
    return (
        f"q {qid} r8={_fmt_opt_float(r8)} lcs={_fmt_opt_float(lcs)} "
        f"lcs_flag={lcs_flag} decontam={decontam} score_role={score_role}"
    )


def _load_config(config: dict | Path | str) -> dict[str, Any]:
    if isinstance(config, dict):
        return dict(config)
    return json.loads(Path(config).read_text(encoding="utf-8"))


@dataclass
class ConfigVerdict:
    """配置校验结果。floors 是应用后的规模下限。"""

    messages: list[str]
    has_violation: bool
    threshold_unlocked: bool
    decontam_max: float | None
    floors: dict[str, Any]


@dataclass
class CorpusVerdict:
    """语料与许可扫描结果。"""

    chunks: list[Chunk]
    by_eid: dict[str, Chunk]
    n_chunks: int
    license_violations: int
    synthetic_ratio: float
    public_ratio: float
    messages: list[str]
    has_violation: bool


@dataclass
class QuestionVerdict:
    """单题检查结果。"""

    messages: list[str]
    has_violation: bool
    record: str
    counted_arm: bool
    counted_guardrail: bool
    counted_qtype: str | None
    counted_trap: bool
    decontam_hit: bool
    lcs_flag: int


@dataclass
class SummaryVerdict:
    """题集汇总与退出码。"""

    messages: list[str]
    has_violation: bool
    exit_code: int
    trap_adversarial_ratio: float
    qtype_counts: dict[str, int]
    n_arm: int
    n_guardrail: int
    decontam_hits: int
    lcs_flags: int


def validate_x1_config(
    cfg: dict[str, Any],
    floor_overrides: dict[str, Any] | None,
) -> ConfigVerdict:
    """校验锁定配置与去污染阈值。缺键或 null 不代入任何数字。"""
    messages: list[str] = []
    threshold_unlocked = False
    has_violation = False

    if "decontam_8gram_max" not in cfg or cfg.get("decontam_8gram_max") is None:
        threshold_unlocked = True
        messages.append("decontam_8gram_max 缺键或为 null，不代入阈值")
        decontam_max: float | None = None
    elif not _is_number(cfg["decontam_8gram_max"]):
        has_violation = True
        messages.append("decontam_8gram_max 不是数字")
        decontam_max = None
    else:
        decontam_max = float(cfg["decontam_8gram_max"])
        if not math.isfinite(decontam_max):
            threshold_unlocked = True
            messages.append("decontam_8gram_max 为 NaN 或 Infinity，不代入阈值")
            decontam_max = None

    for key, expected in LOCKED_CONFIG.items():
        if key not in cfg:
            has_violation = True
            messages.append(f"配置缺键 {key}")
            continue
        got = cfg[key]
        if key == "flag_thinking":
            if got is not False:
                has_violation = True
                messages.append("flag_thinking 必须为 false")
            continue
        if _is_number(expected) and _is_number(got):
            if float(got) != float(expected):
                has_violation = True
                messages.append(f"{key} 必须为 {expected}，得到 {got}")
        elif got != expected:
            has_violation = True
            messages.append(f"{key} 必须为 {expected}，得到 {got}")

    ov = floor_overrides or {}
    apply_min_chunks = int(ov["min_chunks"]) if "min_chunks" in ov else MIN_CHUNKS
    apply_min_per = int(ov["min_per_qtype"]) if "min_per_qtype" in ov else MIN_PER_QTYPE
    apply_min_trap = (
        float(ov["min_trap_adversarial_ratio"])
        if "min_trap_adversarial_ratio" in ov
        else MIN_TRAP_ADVERSARIAL_RATIO
    )
    apply_min_syn = (
        float(ov["min_synthetic_ratio"])
        if "min_synthetic_ratio" in ov
        else MIN_SYNTHETIC_RATIO
    )
    apply_max_pub = (
        float(ov["max_public_ratio"]) if "max_public_ratio" in ov else MAX_PUBLIC_RATIO
    )

    if "min_chunks" in cfg:
        if not _is_number(cfg["min_chunks"]) or cfg["min_chunks"] < MIN_CHUNKS:
            has_violation = True
            messages.append("min_chunks 比锁定下限更松或非法")
        elif "min_chunks" not in ov:
            apply_min_chunks = int(cfg["min_chunks"])
    if "min_per_qtype" in cfg:
        if not _is_number(cfg["min_per_qtype"]) or cfg["min_per_qtype"] < MIN_PER_QTYPE:
            has_violation = True
            messages.append("min_per_qtype 比锁定下限更松或非法")
        elif "min_per_qtype" not in ov:
            apply_min_per = int(cfg["min_per_qtype"])
    if "min_trap_adversarial_ratio" in cfg:
        if (
            not _is_number(cfg["min_trap_adversarial_ratio"])
            or cfg["min_trap_adversarial_ratio"] < MIN_TRAP_ADVERSARIAL_RATIO
        ):
            has_violation = True
            messages.append("min_trap_adversarial_ratio 比锁定下限更松或非法")
        elif "min_trap_adversarial_ratio" not in ov:
            apply_min_trap = float(cfg["min_trap_adversarial_ratio"])
    if "min_synthetic_ratio" in cfg:
        if (
            not _is_number(cfg["min_synthetic_ratio"])
            or cfg["min_synthetic_ratio"] < MIN_SYNTHETIC_RATIO
        ):
            has_violation = True
            messages.append("min_synthetic_ratio 比锁定下限更松或非法")
        elif "min_synthetic_ratio" not in ov:
            apply_min_syn = float(cfg["min_synthetic_ratio"])
    if "max_public_ratio" in cfg:
        if (
            not _is_number(cfg["max_public_ratio"])
            or cfg["max_public_ratio"] > MAX_PUBLIC_RATIO
        ):
            has_violation = True
            messages.append("max_public_ratio 比锁定上限更松或非法")
        elif "max_public_ratio" not in ov:
            apply_max_pub = float(cfg["max_public_ratio"])

    return ConfigVerdict(
        messages=messages,
        has_violation=has_violation,
        threshold_unlocked=threshold_unlocked,
        decontam_max=decontam_max,
        floors={
            "min_chunks": apply_min_chunks,
            "min_per_qtype": apply_min_per,
            "min_trap_adversarial_ratio": apply_min_trap,
            "min_synthetic_ratio": apply_min_syn,
            "max_public_ratio": apply_max_pub,
        },
    )


def scan_x1_corpus(
    corpus_dir: Path | str,
    traps_dir: Path | str,
    floors: dict[str, Any],
) -> CorpusVerdict:
    """扫描语料许可、规模与合成/公开占比。"""
    corpus_dir = Path(corpus_dir)
    traps_dir = Path(traps_dir)
    messages: list[str] = []
    has_violation = False
    chunks = _load_all_chunks(corpus_dir, traps_dir)
    extra = _load_extra_meta(corpus_dir)
    extra.update(_load_extra_meta(traps_dir))
    by_eid = {chunk_evidence_id(c): c for c in chunks}
    n_chunks = len(chunks)

    license_bad_chunks = 0
    n_synthetic = 0
    n_public = 0
    for ch in chunks:
        meta = extra.get((ch.doc_id, ch.as_of), {})
        license_ = meta.get("license", "")
        provenance = meta.get("provenance", "")
        domain = meta.get("domain", "")
        genre = meta.get("genre", "")
        source_type = ch.source_type
        bad = False
        if license_ not in LICENSE_WHITELIST:
            bad = True
        if license_ in ZERO_COUNT_LICENSES:
            bad = True
        if license_ == "synthetic":
            if provenance != "synthetic":
                bad = True
        elif license_ in LICENSE_WHITELIST and provenance != "public":
            bad = True
        if domain not in DOMAINS:
            bad = True
        if genre not in GENRES:
            bad = True
        if source_type not in SOURCE_TYPES:
            bad = True
        if license_ in PUBLIC_LICENSES:
            if not (
                meta.get("source_url")
                and meta.get("publisher")
                and meta.get("retrieved_at")
            ):
                bad = True
        if license_ == "CC-BY-4.0" and not meta.get("attribution"):
            bad = True
        if genre == "P2":
            attr = meta.get("attribution", "")
            if (
                license_ != "synthetic"
                or not meta.get("data_source_url")
                or "www.stats.gov.cn" not in attr
            ):
                bad = True
        if provenance == "synthetic":
            n_synthetic += 1
        elif provenance == "public":
            n_public += 1
        if bad:
            license_bad_chunks += 1

    if license_bad_chunks:
        has_violation = True
        messages.append(f"许可违规 chunk={license_bad_chunks}")

    synthetic_ratio = (n_synthetic / n_chunks) if n_chunks else 0.0
    public_ratio = (n_public / n_chunks) if n_chunks else 0.0
    apply_min_chunks = floors["min_chunks"]
    apply_min_syn = floors["min_synthetic_ratio"]
    apply_max_pub = floors["max_public_ratio"]
    if n_chunks < apply_min_chunks:
        has_violation = True
        messages.append(f"chunk 数 {n_chunks} < {apply_min_chunks}")
    if synthetic_ratio < apply_min_syn:
        has_violation = True
        messages.append(f"合成占比 {synthetic_ratio:.4f} < {apply_min_syn}")
    if public_ratio > apply_max_pub:
        has_violation = True
        messages.append(f"公开占比 {public_ratio:.4f} > {apply_max_pub}")

    return CorpusVerdict(
        chunks=chunks,
        by_eid=by_eid,
        n_chunks=n_chunks,
        license_violations=license_bad_chunks,
        synthetic_ratio=synthetic_ratio,
        public_ratio=public_ratio,
        messages=messages,
        has_violation=has_violation,
    )


def check_x1_question(
    item: dict[str, Any],
    *,
    chunks: list[Chunk],
    by_eid: dict[str, Chunk],
    decontam_max: float | None,
) -> QuestionVerdict:
    """检查一道题。消息字符串与拆分前的单题段相同。"""
    messages: list[str] = []
    has_violation = False
    qid = str(item.get("id", ""))
    qtype = item.get("qtype")
    category = item.get("category")
    score_role = item.get("score_role", "arm")
    if score_role is None:
        score_role = "arm"
    relevant = item.get("relevant")
    distractors = item.get("distractors")
    required_q = ("id", "qtype", "category", "relevant", "distractors", "eval_intent", "as_of")
    missing = [k for k in required_q if k not in item]
    if missing:
        has_violation = True
        messages.append(f"{qid or '?'} 缺字段 {missing}")
    if qtype not in QTYPES:
        has_violation = True
        messages.append(f"{qid} qtype 非法")
    if category not in CATEGORIES:
        has_violation = True
        messages.append(f"{qid} category 非法")
    if score_role not in SCORE_ROLES:
        has_violation = True
        messages.append(f"{qid} score_role 非法")
        score_role = "arm"
    if not isinstance(relevant, list):
        has_violation = True
        messages.append(f"{qid} relevant 必须是列表")
        relevant = []
    if not isinstance(distractors, list):
        has_violation = True
        messages.append(f"{qid} distractors 必须是列表")

    counted_arm = False
    counted_guardrail = False
    counted_qtype: str | None = None
    counted_trap = False
    is_guardrail = score_role == "guardrail"
    if is_guardrail:
        counted_guardrail = True
        if qtype == "multi_hop":
            has_violation = True
            messages.append(f"{qid} 护栏题不得为 multi_hop")
    else:
        counted_arm = True
        if isinstance(qtype, str) and qtype in {"lexical", "paraphrase", "multi_hop"}:
            counted_qtype = qtype
        if category in {"trap", "adversarial"}:
            counted_trap = True
        if len(relevant) == 0:
            has_violation = True
            messages.append(f"{qid} arm 题 relevant 不得为空")

    query_ok = False
    cleaned_q = ""
    if "query" not in item:
        has_violation = True
        messages.append(f"{qid} 缺 query")
    elif not isinstance(item.get("query"), str):
        has_violation = True
        messages.append(f"{qid} query 不是字符串")
    else:
        cleaned_q = strip_law_names(clean_text(item["query"]))
        if not cleaned_q:
            has_violation = True
            messages.append(f"{qid} query 去白名单后为空")
        else:
            query_ok = True

    r8: float | None = None
    lcs: float | None = None
    lcs_flag = 0
    decontam = 0

    skip_decontam = is_guardrail and len(relevant) == 0
    rel_chunks: list[Chunk] = []
    for eid in relevant:
        ch = by_eid.get(str(eid))
        if ch is None:
            has_violation = True
            messages.append(f"{qid} relevant 找不到 {eid}")
        else:
            rel_chunks.append(ch)
    rel_clean = [clean_chunk_text(c.text) for c in rel_chunks]

    if qtype == "multi_hop" and not is_guardrail:
        doc_ids = []
        for eid in relevant:
            parsed = parse_evidence_id(str(eid))
            if parsed is None:
                continue
            doc_id = parsed[0]
            if doc_id:
                doc_ids.append(doc_id)
        if len(relevant) < 2 or len(set(doc_ids)) < 2:
            has_violation = True
            messages.append(f"{qid} multi_hop 须跨至少两个 doc_id")
        points = item.get("answer_points")
        if not isinstance(points, list) or len(points) < 2:
            has_violation = True
            messages.append(f"{qid} 须有至少 2 条 answer_points")
        elif not all(isinstance(p, str) for p in points):
            has_violation = True
            messages.append(f"{qid} answer_points 必须是字符串列表")
        else:
            cleaned_pts = [clean_text(p) for p in points]
            if any(not p for p in cleaned_pts):
                has_violation = True
                messages.append(f"{qid} answer_points 清洗后有空串")
            else:
                for ch in chunks:
                    body = clean_chunk_text(ch.text)
                    if all(p in body for p in cleaned_pts):
                        has_violation = True
                        messages.append(f"{qid} answer_points 集中在同一 chunk")
                        break

    if not skip_decontam and query_ok:
        if qtype == "lexical":
            r8 = None
            lcs = None
            if len(cleaned_q) >= LEXICAL_MIN_LEN and any(
                cleaned_q in body for body in rel_clean
            ):
                decontam = 1
        elif qtype in {"paraphrase", "multi_hop"}:
            r8 = eight_gram_overlap(cleaned_q, rel_clean)
            lcs = lcs_ratio(cleaned_q, rel_clean)
            if (
                decontam_max is not None
                and r8 is not None
                and r8 > decontam_max
            ):
                decontam = 1
            if lcs is not None and lcs >= LCS_FLAG_MIN:
                lcs_flag = 1

    return QuestionVerdict(
        messages=messages,
        has_violation=has_violation,
        record=_record_line(qid, r8, lcs, lcs_flag, decontam, str(score_role)),
        counted_arm=counted_arm,
        counted_guardrail=counted_guardrail,
        counted_qtype=counted_qtype,
        counted_trap=counted_trap,
        decontam_hit=bool(decontam),
        lcs_flag=lcs_flag,
    )


def summarize_x1(
    questions: list[QuestionVerdict],
    *,
    floors: dict[str, Any],
    threshold_unlocked: bool,
    prior_violation: bool,
) -> SummaryVerdict:
    """汇总题型地板与退出码。阈值未锁定时退出码为 2，优先于违规的 1。"""
    messages: list[str] = []
    has_violation = prior_violation
    qtype_counts = {"lexical": 0, "paraphrase": 0, "multi_hop": 0}
    n_arm = 0
    n_guardrail = 0
    n_trap_adv = 0
    decontam_hits = 0
    lcs_flags = 0
    for question in questions:
        if question.has_violation:
            has_violation = True
        if question.counted_guardrail:
            n_guardrail += 1
        if question.counted_arm:
            n_arm += 1
        if question.counted_qtype:
            qtype_counts[question.counted_qtype] += 1
        if question.counted_trap:
            n_trap_adv += 1
        if question.decontam_hit:
            decontam_hits += 1
        if question.lcs_flag:
            lcs_flags += 1

    if decontam_hits:
        has_violation = True
        messages.append(f"去污染命中 {decontam_hits}")

    apply_min_per = floors["min_per_qtype"]
    apply_min_trap = floors["min_trap_adversarial_ratio"]
    for qt, n in qtype_counts.items():
        if n < apply_min_per:
            has_violation = True
            messages.append(f"{qt} n={n} < {apply_min_per}")
    trap_ratio = (n_trap_adv / n_arm) if n_arm else 0.0
    if n_arm < 3 * apply_min_per:
        # n≥90 与每型 ≥30 同一套地板：3 * min_per_qtype
        has_violation = True
        messages.append(f"n_arm={n_arm} < {3 * apply_min_per}")
    if trap_ratio < apply_min_trap:
        has_violation = True
        messages.append(f"trap+adversarial 比例 {trap_ratio:.4f} < {apply_min_trap}")

    if threshold_unlocked:
        exit_code = 2
    elif has_violation:
        exit_code = 1
    else:
        exit_code = 0
    return SummaryVerdict(
        messages=messages,
        has_violation=has_violation,
        exit_code=exit_code,
        trap_adversarial_ratio=trap_ratio,
        qtype_counts=qtype_counts,
        n_arm=n_arm,
        n_guardrail=n_guardrail,
        decontam_hits=decontam_hits,
        lcs_flags=lcs_flags,
    )


def check_x1(
    corpus_dir: Path | str,
    traps_dir: Path | str,
    questions: Path | str | list | dict,
    config: dict | Path | str,
    *,
    floor_overrides: dict[str, Any] | None = None,
) -> CheckResult:
    """执行 x1 检查。floor_overrides 仅供单测覆盖规模，不改变锁定常量。"""
    cfg = _load_config(config)
    config_v = validate_x1_config(cfg, floor_overrides)
    corpus_v = scan_x1_corpus(corpus_dir, traps_dir, config_v.floors)
    question_vs = [
        check_x1_question(
            item,
            chunks=corpus_v.chunks,
            by_eid=corpus_v.by_eid,
            decontam_max=config_v.decontam_max,
        )
        for item in _load_questions(questions)
    ]
    summary = summarize_x1(
        question_vs,
        floors=config_v.floors,
        threshold_unlocked=config_v.threshold_unlocked,
        prior_violation=config_v.has_violation or corpus_v.has_violation,
    )
    messages = list(config_v.messages)
    messages.extend(corpus_v.messages)
    for question in question_vs:
        messages.extend(question.messages)
    messages.extend(summary.messages)
    return CheckResult(
        exit_code=summary.exit_code,
        qtype_counts=summary.qtype_counts,
        n_arm=summary.n_arm,
        n_guardrail=summary.n_guardrail,
        trap_adversarial_ratio=summary.trap_adversarial_ratio,
        n_chunks=corpus_v.n_chunks,
        synthetic_ratio=corpus_v.synthetic_ratio,
        public_ratio=corpus_v.public_ratio,
        decontam_hits=summary.decontam_hits,
        license_violations=corpus_v.license_violations,
        lcs_flags=summary.lcs_flags,
        records=[question.record for question in question_vs],
        messages=messages,
    )


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="x1 许可 / 去污染 / 题集结构检查")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--traps", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    result = check_x1(args.corpus, args.traps, args.questions, args.config)
    print(result.format_report(), end="")
    return result.exit_code


def main() -> int:
    return run_cli()
