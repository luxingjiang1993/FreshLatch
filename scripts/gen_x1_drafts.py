"""生成 x1 文档/题目草稿，并用 qwen-plus 非思考抽检（RET-01.7）。

温度与 seed 只从配置读取；缺省或 JSON null 时拒绝，不落入 DecodingParams 的 temperature 0。
generate 按 spec 分批各调用一次模型，合并进 --out。单价只读 spec.pricing，抽检单价只读 spec.flag_pricing，脚本不内置价格。
P2 不由模型生成。花费按上界预检，用量缺失、截断或调用异常都记失败并停止。清单、题目和文档都经临时文件替换写入。
检查器退出码 2（阈值未写入）与 1（结构/许可）都打印，已通过校验的草稿仍写入 --out。
不把去污染阈值写进配置，也不把任何数字缺省传给检查器。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freshlatch.eval.x1_checks import check_x1
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.store.ingest import CLAUSE_RE, META_RE

FORBIDDEN_OUT_ROOTS = (
    ROOT / "data" / "corpus",
    ROOT / "data" / "traps",
    ROOT / "data" / "eval",
    ROOT / "docs" / "evidence" / "hard-gold-arm",
    ROOT / "reports",
)
RETRIEVE_X1 = ROOT / "data" / "eval" / "retrieve_x1.json"
MARKER_NAME = ".x1-drafts-manifest.json"
SIDECAR_MARKER = "x1_flag_sidecar"

DRAFT_MODEL = "qwen-flash"
FLAG_MODEL = "qwen-plus"
GOLD_PLACEHOLDER = "TODO-owner"
GOLD_QUESTION_KEYS = ("relevant", "answer_points", "distractors", "qtype")
NOTE_FIELDS = ("id", "suspicion", "reason", "severity")
RAW_GOLD_NOTE = "raw-response.txt 可能含模型自拟金标，不得当标签使用"
BATCH_GENRES = frozenset({f"S{i}" for i in range(1, 8)})
BATCH_DOMAINS = frozenset({"D0", "D1", "D2", "D3"})
BATCH_AS_OF = frozenset({"T0", "T1"})
DOC_SOURCE_TYPES = frozenset({"private", "public", "internal"})
LICENSE_SYNTHETIC = "synthetic"
P2_MODEL_REFUSAL = "P2 由人按国家统计局公告手写，不由模型生成"
DECODING_MISMATCH = "解码参数与清单不一致"
FRONTMATTER_KEYS = (
    "doc_id",
    "as_of",
    "source_type",
    "title",
    "provenance",
    "license",
    "domain",
    "genre",
)
# 估 token 的口径：不调用模型。输入按 prompt 码位的两倍作上界；输出按块、题、文档开销。
EST_OUTPUT_TOKENS_PER_CHUNK = 256
EST_OUTPUT_TOKENS_PER_DOC = 128
EST_OUTPUT_TOKENS_PER_QUESTION = 128
PUBLIC_CORPUS = ROOT / "data" / "exp" / "x1" / "corpus"
PUBLIC_TRAPS = ROOT / "data" / "exp" / "x1" / "traps"
_BATCH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
_BLOCK_ID_RE = re.compile(r"^p\d+$")
_H2_LINE_RE = re.compile(r"^##[^\n]*", re.MULTILINE)
_NBS_MARKERS = ("国家统计局", "stats.gov.cn")


class DraftShapeError(ValueError):
    """模型草稿 JSON 形状非法，应写 raw-response 后非 0 退出。"""


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_under(path: Path, root: Path) -> bool:
    target = _resolved(path)
    base = _resolved(root)
    if target == base:
        return True
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def _forbidden_resolved(resolved: Path) -> bool:
    """路径等于仓库根、禁写根、其后代，或禁写根的祖先，则禁止。"""
    if resolved == _resolved(ROOT) or resolved == _resolved(RETRIEVE_X1):
        return True
    for root in FORBIDDEN_OUT_ROOTS:
        r = _resolved(root)
        if _is_under(resolved, r) or _is_under(r, resolved):
            return True
    return False


def is_forbidden_out(path: Path) -> bool:
    """--out 不得等于仓库根、不得是禁写目录的祖先/自身/后代。"""
    return _forbidden_resolved(_resolved(path))


def is_forbidden_sidecar(path: Path) -> bool:
    """sidecar 沿用 --out 的禁写规则，并拒绝落在禁写祖先目录里的文件。"""
    resolved = _resolved(path)
    if _forbidden_resolved(resolved):
        return True
    return _forbidden_resolved(resolved.parent)


def _is_script_sidecar(path: Path) -> bool:
    """已有文件必须带本脚本写入的标记，才允许覆盖。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and data.get(SIDECAR_MARKER) is True


def _can_write_sidecar(path: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_sidecar(path):
        return (
            "错误: --sidecar 不得写成 data/eval/retrieve_x1.json，"
            "也不得落在禁写目录或其祖先下"
        )
    if path.suffix.lower() != ".json":
        return "错误: --sidecar 必须以 .json 结尾"
    if path.exists():
        if path.is_dir():
            return "错误: --sidecar 已存在且是目录"
        if not _is_script_sidecar(path):
            return "错误: --sidecar 已存在且不是本脚本写入的抽检文件，拒绝覆盖"
    return None


def _can_overwrite_out(out: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_out(out):
        return (
            "错误: --out 不得为仓库根，不得位于 data/corpus、data/traps、data/eval、"
            "docs/evidence/hard-gold-arm、reports 之下，也不得是这些目录的祖先"
        )
    if out.exists() and out.is_file():
        return "错误: --out 已存在且不是目录"
    if out.exists() and out.is_dir() and any(out.iterdir()):
        if not (out / MARKER_NAME).is_file():
            return "错误: --out 已存在且非空，缺少本脚本写入的清单，拒绝覆盖"
    return None


def _load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decoding_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_draft_decoding(cfg: dict[str, Any]) -> tuple[float, int] | str:
    """配置里 temperature / seed 任一为 null 或未传入则拒绝。"""
    if "draft_temperature" not in cfg or cfg.get("draft_temperature") is None:
        return "draft_temperature 为 null 或未传入，拒绝落到 DecodingParams 默认温度"
    if "draft_seed" not in cfg or cfg.get("draft_seed") is None:
        return "draft_seed 为 null 或未传入，拒绝落到 DecodingParams 默认"
    temp = cfg["draft_temperature"]
    seed = cfg["draft_seed"]
    if not _decoding_number(temp):
        return "draft_temperature 不是数字"
    if not isinstance(seed, int) or isinstance(seed, bool):
        return "draft_seed 不是整数"
    return float(temp), int(seed)


def _parse_json_content(text: str) -> Any:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        fence = raw.rfind("```")
        if fence != -1:
            raw = raw[:fence]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)


def _whitelist_notes(obj: Any) -> Any:
    """sidecar 只保留抽检备注字段，不落 gold。"""
    if isinstance(obj, list):
        return [_whitelist_notes(x) for x in obj]
    if isinstance(obj, dict):
        return {k: obj[k] for k in NOTE_FIELDS if k in obj}
    return obj


def _is_gold_key(key: str) -> bool:
    low = str(key).lower()
    if low.startswith("relevant"):
        return True
    return low in {"answer_points", "distractors", "qtype"}


def _strip_nested_gold(obj: Any) -> Any:
    """去掉任意深度的金标键，避免非标准嵌套泄漏。"""
    if isinstance(obj, dict):
        return {k: _strip_nested_gold(v) for k, v in obj.items() if not _is_gold_key(k)}
    if isinstance(obj, list):
        return [_strip_nested_gold(x) for x in obj]
    return obj


def _looks_like_question(obj: Any) -> bool:
    return isinstance(obj, dict) and ("id" in obj or "query" in obj)


def _as_question_list(value: Any) -> list[dict] | None:
    if isinstance(value, list):
        if all(isinstance(x, dict) for x in value):
            return value
        return None
    if _looks_like_question(value):
        return [value]
    return None


def _extract_questions(payload: Any) -> list[dict] | None:
    """把模型输出归一成题目对象列表；无法识别则返回 None。"""
    if isinstance(payload, list):
        return _as_question_list(payload)
    if not isinstance(payload, dict):
        return None
    if "queries" in payload:
        return _as_question_list(payload.get("queries"))
    q = payload.get("questions")
    if isinstance(q, dict) and "queries" in q:
        return _as_question_list(q.get("queries"))
    extracted = _as_question_list(q) if q is not None else None
    if extracted is not None:
        return extracted
    if _looks_like_question(payload) and "documents" not in payload:
        return [payload]
    if "documents" in payload and q is None:
        return []
    return None


def _normalize_question(item: dict[str, Any]) -> dict[str, Any]:
    cleaned = _strip_nested_gold(item)
    if not isinstance(cleaned, dict):
        cleaned = {}
    for key in GOLD_QUESTION_KEYS:
        cleaned[key] = GOLD_PLACEHOLDER
    return cleaned


def _document_path_syntax_error(raw_path: str) -> str | None:
    """拒绝盘符、UNC、反斜杠、.. 以及会落到暂存根的 '.'。Linux / Windows 同一套检查。"""
    if "\\" in raw_path:
        return f"路径非法: {raw_path}"
    for cls in (PurePosixPath, PureWindowsPath):
        parsed = cls(raw_path)
        if parsed.drive or parsed.anchor or parsed.root:
            return f"路径非法: {raw_path}"
        if ".." in parsed.parts:
            return f"路径非法: {raw_path}"
        if not parsed.parts:
            return f"路径非法: {raw_path}"
    rel = Path(raw_path)
    if rel.is_absolute() or ".." in rel.parts:
        return f"路径非法: {raw_path}"
    return None


def _document_paths_collide(rel_paths: list[str]) -> bool:
    """同一批草稿里，某文件路径是另一文件的父目录。"""
    parts_list = [PurePosixPath(p).parts for p in rel_paths]
    for i, a in enumerate(parts_list):
        for j, b in enumerate(parts_list):
            if i == j:
                continue
            if a and b and len(a) < len(b) and b[: len(a)] == a:
                return True
    return False


def _strictly_inside(path: Path, root: Path) -> bool:
    return path.is_relative_to(root) and path != root


def _normalize_documents(documents: Any) -> list[dict[str, str]]:
    if documents is None:
        return []
    if not isinstance(documents, list):
        raise DraftShapeError("documents 必须是列表")
    out: list[dict[str, str]] = []
    for i, item in enumerate(documents):
        if not isinstance(item, dict):
            raise DraftShapeError(f"documents[{i}] 必须是对象")
        if "path" not in item:
            raise DraftShapeError(f"documents[{i}] 缺少 path")
        raw_path = item["path"]
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise DraftShapeError(f"documents[{i}] path 必须是非空字符串")
        syntax = _document_path_syntax_error(raw_path)
        if syntax:
            raise DraftShapeError(f"documents[{i}] {syntax}")
        content = item.get("content", "")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise DraftShapeError(f"documents[{i}] content 必须是字符串")
        out.append({"path": raw_path, "content": content})
    if _document_paths_collide([item["path"] for item in out]):
        raise DraftShapeError("documents 路径文件与目录冲突")
    return out


def _normalize_generate_payload(payload: Any) -> dict[str, Any]:
    questions = _extract_questions(payload)
    if questions is None:
        raise DraftShapeError("无法从模型输出解析题目列表")
    if isinstance(payload, dict):
        documents = _normalize_documents(payload.get("documents"))
    else:
        documents = []
    normalized_qs = [_normalize_question(q) if isinstance(q, dict) else {} for q in questions]
    return {
        "documents": documents,
        "questions": {"queries": normalized_qs},
    }


def _materialize_drafts(payload: dict[str, Any], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    staging_resolved = dest.resolve()
    corpus = dest / "corpus"
    traps = dest / "traps"
    traps.mkdir(parents=True, exist_ok=True)
    try:
        planned: list[tuple[dict[str, str], Path]] = []
        for item in payload["documents"]:
            target = (dest / item["path"]).resolve()
            if not _strictly_inside(target, staging_resolved):
                raise DraftShapeError(f"路径非法: {item['path']}")
            planned.append((item, target))
        file_targets = [target for _item, target in planned]
        dir_targets: set[Path] = set()
        for target in file_targets:
            parent = target.parent
            while parent != staging_resolved:
                if not parent.is_relative_to(staging_resolved):
                    raise DraftShapeError("路径非法: 解析后逃出暂存目录")
                dir_targets.add(parent)
                nxt = parent.parent
                if nxt == parent:
                    break
                parent = nxt
        if set(file_targets) & dir_targets:
            raise DraftShapeError("documents 路径文件与目录冲突")
        for item, target in planned:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item["content"], encoding="utf-8")
        qpath = dest / "questions.json"
        qpath.write_text(
            json.dumps(payload["questions"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if not corpus.exists():
            corpus.mkdir(parents=True, exist_ok=True)
        return qpath
    except OSError as exc:
        raise DraftShapeError(f"写入草稿失败: {exc}") from exc


def _print_checker(result) -> None:
    print(result.format_report(), end="")
    print(f"checker_exit={result.exit_code}")


def _token_usage_dict(client: Any) -> dict[str, Any]:
    usage = getattr(client, "token_usage", None)
    to_dict = getattr(usage, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return {}


def _atomic_write_text(path: Path, text: str) -> None:
    """同目录临时文件写完后 os.replace，避免写到一半留下半截文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _write_manifest(dest: Path, fields: dict[str, Any]) -> None:
    _atomic_write_text(
        dest / MARKER_NAME,
        json.dumps(fields, ensure_ascii=False, indent=2) + "\n",
    )


def _replace_out(staging: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(staging, out)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _expected_rel_dir(genre: str, as_of: str) -> str:
    bucket = "traps" if genre == "S7" else "corpus"
    return f"{bucket}/{as_of.lower()}"


def _batch_canon(batch: dict[str, Any]) -> dict[str, Any]:
    keys = ["batch_id", "genre", "domain", "n_docs", "chunks_per_doc", "topic"]
    if batch.get("pair") is not True:
        keys.append("as_of")
    canon = {k: batch[k] for k in keys}
    for opt in ("must_include", "pair", "n_questions", "max_chars_per_chunk"):
        if opt in batch:
            canon[opt] = batch[opt]
    return canon


def _prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _decoding_fields(model: str, temperature: float, seed: int, prompt: str) -> dict[str, Any]:
    return {
        "draft_model": model,
        "draft_temperature": temperature,
        "draft_seed": seed,
        "prompt_sha256": _prompt_sha256(prompt),
    }


def _batch_fingerprint(batch: dict[str, Any], fields: dict[str, Any]) -> str:
    canon = _batch_canon(batch)
    canon.update(fields)
    blob = json.dumps(canon, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _optional_positive_int(batch: dict[str, Any], key: str, index: int) -> str | None:
    if key not in batch:
        return None
    if not _is_int(batch[key]) or batch[key] < 1:
        return f"batches[{index}] {key} 必须是正整数"
    return None


def _validate_batch(batch: Any, index: int) -> str | None:
    if not isinstance(batch, dict):
        return f"batches[{index}] 必须是对象"
    if batch.get("genre") == "P2":
        return P2_MODEL_REFUSAL
    required = ["batch_id", "genre", "domain", "n_docs", "chunks_per_doc", "topic"]
    pair = batch.get("pair")
    if pair is True:
        if "as_of" in batch:
            return f"batches[{index}] pair 为 true 时不得带 as_of"
    elif "pair" in batch:
        return f"batches[{index}] pair 只能为 true"
    else:
        required.append("as_of")
    missing = [k for k in required if k not in batch]
    if missing:
        return f"batches[{index}] 缺字段 {missing}"
    batch_id = batch["batch_id"]
    if not isinstance(batch_id, str) or not _BATCH_ID_RE.fullmatch(batch_id):
        return f"batches[{index}] batch_id 非法"
    if batch["genre"] not in BATCH_GENRES:
        return f"batches[{index}] genre 必须是 S1–S7"
    if batch["domain"] not in BATCH_DOMAINS:
        return f"batches[{index}] domain 必须是 D0–D3"
    if pair is not True and batch["as_of"] not in BATCH_AS_OF:
        return f"batches[{index}] as_of 必须是 T0 或 T1"
    if not _is_int(batch["n_docs"]) or batch["n_docs"] < 1:
        return f"batches[{index}] n_docs 必须是正整数"
    if not _is_int(batch["chunks_per_doc"]) or not 2 <= batch["chunks_per_doc"] <= 6:
        return f"batches[{index}] chunks_per_doc 必须是 2–6 的整数"
    topic = batch["topic"]
    if not isinstance(topic, str) or not topic.strip():
        return f"batches[{index}] topic 必须是非空字符串"
    for key in ("n_questions", "max_chars_per_chunk"):
        err = _optional_positive_int(batch, key, index)
        if err:
            return err
    if "must_include" in batch and not isinstance(batch["must_include"], list):
        return f"batches[{index}] must_include 必须是列表"
    if batch["genre"] == "S6":
        items = batch.get("must_include")
        if not isinstance(items, list) or not items:
            return f"batches[{index}] S6 的 must_include 必须是非空字符串列表"
        if not all(isinstance(item, str) and item.strip() for item in items):
            return f"batches[{index}] S6 的 must_include 必须是非空字符串列表"
    return None


def _load_spec(path: Path) -> dict[str, Any] | str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return f"无法读取 spec: {exc}"
    if not isinstance(data, dict):
        return "spec 必须是 JSON 对象"
    batches = data.get("batches")
    if not isinstance(batches, list) or not batches:
        return "spec.batches 必须是非空数组"
    seen: set[str] = set()
    for i, batch in enumerate(batches):
        err = _validate_batch(batch, i)
        if err:
            return err
        bid = batch["batch_id"]
        if bid in seen:
            return f"batch_id 重复: {bid}"
        seen.add(bid)
    return data


def _parse_pricing_block(pricing: Any, label: str) -> tuple[float, float, str] | str:
    if not isinstance(pricing, dict):
        return f"spec 缺少 {label}"
    source = pricing.get("source")
    if not isinstance(source, str) or not source.strip():
        return f"{label}.source 必须是非空字符串"
    in_price = pricing.get("input_cny_per_million")
    out_price = pricing.get("output_cny_per_million")
    if not _decoding_number(in_price) or in_price < 0:
        return f"{label}.input_cny_per_million 必须是非负数字"
    if not _decoding_number(out_price) or out_price < 0:
        return f"{label}.output_cny_per_million 必须是非负数字"
    return float(in_price), float(out_price), source


def _parse_pricing(spec: dict[str, Any]) -> tuple[float, float, str] | str:
    return _parse_pricing_block(spec.get("pricing"), "pricing")


def _parse_max_cny(value: Any) -> float | str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "--max-cny 必须是数字"
    if not math.isfinite(float(value)) or float(value) < 0:
        return "--max-cny 必须是有限的非负数"
    return float(value)


def _is_pair(batch: dict[str, Any]) -> bool:
    return batch.get("pair") is True


def _file_count(batch: dict[str, Any]) -> int:
    n = int(batch["n_docs"])
    if _is_pair(batch):
        return n * 2
    return n


def _question_allowance(batch: dict[str, Any]) -> int:
    if "n_questions" in batch:
        return int(batch["n_questions"])
    return _file_count(batch)


def _per_chunk_tokens(batch: dict[str, Any]) -> int:
    if "max_chars_per_chunk" in batch:
        return int(batch["max_chars_per_chunk"]) * 2
    return EST_OUTPUT_TOKENS_PER_CHUNK


def _output_token_upper(batch: dict[str, Any]) -> int:
    docs = _file_count(batch)
    return (
        docs * int(batch["chunks_per_doc"]) * _per_chunk_tokens(batch)
        + _question_allowance(batch) * EST_OUTPUT_TOKENS_PER_QUESTION
        + docs * EST_OUTPUT_TOKENS_PER_DOC
    )


def _input_token_upper(prompt: str) -> int:
    return len(prompt) * 2


def _build_batch_prompt(batch: dict[str, Any]) -> str:
    """拼一批的用户提示。合成正文自写，不给金标，只要 JSON。must_include 原样塞进提示。"""
    pair = _is_pair(batch)
    lines = [
        "生成 x1 实验的合成文档与题目草稿。",
        "合成正文必须自写，不得以版权原文为模板整段改写。",
        "不得给出金标。",
        "只返回 JSON。",
        "只返回 JSON 对象：documents 数组（元素含 path 与 content），以及带 queries 数组的 questions 对象（必须使用 queries 包装）。",
        "每道题只给 id、query、category、eval_intent、as_of。",
        f"本批 batch_id={batch['batch_id']}。",
        f"doc_id 必须匹配 ^{batch['batch_id']}-[a-z0-9-]+$。",
        f"genre={batch['genre']}，domain={batch['domain']}。",
        f"n_docs={batch['n_docs']}，每份文档 chunks_per_doc={batch['chunks_per_doc']} 个块。",
        f"topic：{batch['topic']}",
        "frontmatter 必须包含 doc_id、as_of（与目录一致）、source_type（只允许 private、public、internal）、title、provenance: synthetic、license: synthetic、domain、genre。",
        "license 只能是 synthetic。",
        "正文必须是 2 到 6 个独立的 ## pN 块，块 id 形如 p1，不得重复，块正文不得为空，块数等于 chunks_per_doc。",
    ]
    if pair:
        bucket = "traps" if batch["genre"] == "S7" else "corpus"
        lines.append(
            "本批 pair=true：每个 doc_id 同时给出 T0 与 T1 两份文档，doc_id 相同，pN 顺序相同，T1 改写已陈述事实。"
        )
        lines.append(f"路径分别位于 {bucket}/t0/ 与 {bucket}/t1/ 下，只一层文件名，扩展名 .md。")
        lines.append(f"documents 长度必须等于 {int(batch['n_docs']) * 2}。")
    else:
        dest = _expected_rel_dir(batch["genre"], batch["as_of"])
        lines.append(f"as_of={batch['as_of']}。")
        lines.append(f"每份文档路径必须位于 {dest}/ 下，只一层文件名，扩展名 .md。")
    if batch["genre"] == "S7":
        lines.append("本批是检索陷阱文档，路径必须在 traps 下，不要写入 corpus。")
    if batch["genre"] == "S6":
        lines.append("本批是 P1 缺口事实，只复述 must_include，不得自拟法律门槛或日期。")
    if "n_questions" in batch:
        lines.append(f"题目数量必须等于 {int(batch['n_questions'])}。")
    if "max_chars_per_chunk" in batch:
        lines.append(f"每个块正文不超过 {int(batch['max_chars_per_chunk'])} 个字符。")
    if "must_include" in batch:
        lines.append("must_include（原样遵守，不要改写这些事实）：")
        lines.append(json.dumps(batch["must_include"], ensure_ascii=False))
    return "\n".join(lines)


def _flag_skeleton() -> str:
    return "对下列题目草稿做非思考抽检，只标记疑点。只输出 id、suspicion、reason、severity。"


def _estimate_spec(spec: dict[str, Any]) -> dict[str, Any] | str:
    pricing = _parse_pricing(spec)
    if isinstance(pricing, str):
        return pricing
    flag_pricing = _parse_pricing_block(spec.get("flag_pricing"), "flag_pricing")
    if isinstance(flag_pricing, str):
        return flag_pricing
    in_price, out_price, source = pricing
    flag_in, flag_out, flag_source = flag_pricing
    input_tokens = 0
    output_tokens = 0
    question_slots = 0
    for batch in spec["batches"]:
        input_tokens += _input_token_upper(_build_batch_prompt(batch))
        output_tokens += _output_token_upper(batch)
        question_slots += _question_allowance(batch)
    cny = _cost_cny(input_tokens, output_tokens, in_price, out_price)
    flag_input = _input_token_upper(_flag_skeleton()) + question_slots * 64
    flag_output = max(EST_OUTPUT_TOKENS_PER_CHUNK, question_slots * EST_OUTPUT_TOKENS_PER_QUESTION)
    flag_cny = _cost_cny(flag_input, flag_output, flag_in, flag_out)
    return {
        "batches": len(spec["batches"]),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cny": cny,
        "pricing_source": source,
        "flag_input_tokens": flag_input,
        "flag_output_tokens": flag_output,
        "flag_cny": flag_cny,
        "flag_pricing_source": flag_source,
    }


def _format_estimate(est: dict[str, Any]) -> str:
    return (
        f"batches={est['batches']}\n"
        f"input_tokens={est['input_tokens']} 估\n"
        f"output_tokens={est['output_tokens']} 估\n"
        f"cny={est['cny']:.8f} 估\n"
        f"pricing_source={est['pricing_source']}\n"
        f"flag_input_tokens={est['flag_input_tokens']} 估\n"
        f"flag_output_tokens={est['flag_output_tokens']} 估\n"
        f"flag_cny={est['flag_cny']:.8f} 估\n"
        f"flag_pricing_source={est['flag_pricing_source']}\n"
    )


def _split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    matched = META_RE.match(text)
    if not matched:
        return {}, text
    meta: dict[str, str] = {}
    for line in matched.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, text[matched.end() :]


def _doc_id_ok(doc_id: str, batch_id: str) -> bool:
    return re.fullmatch(rf"^{re.escape(batch_id)}-[a-z0-9-]+$", doc_id) is not None


def _parse_blocks(body: str) -> list[tuple[str, str]] | str:
    headings = list(_H2_LINE_RE.finditer(body))
    if not headings:
        return "块数越界: 0"
    blocks: list[tuple[str, str]] = []
    for i, heading in enumerate(headings):
        matched = re.fullmatch(r"## (p\d+)\s*", heading.group(0))
        if not matched or _BLOCK_ID_RE.fullmatch(matched.group(1)) is None:
            return "块 id 必须是 pN"
        start = heading.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        blocks.append((matched.group(1), body[start:end].strip()))
    idents = [ident for ident, _text in blocks]
    if len(idents) != len(set(idents)):
        return "块 id 重复"
    if any(not text for _ident, text in blocks):
        return "块正文为空"
    return blocks


def _validate_blocks(body: str, batch: dict[str, Any]) -> list[tuple[str, str]] | str:
    parsed = _parse_blocks(body)
    if isinstance(parsed, str):
        return parsed
    if len(parsed) < 2 or len(parsed) > 6:
        return f"块数越界: {len(parsed)}"
    if len(parsed) != int(batch["chunks_per_doc"]):
        return f"块数 {len(parsed)} 与 chunks_per_doc 不一致"
    if "max_chars_per_chunk" in batch:
        limit = int(batch["max_chars_per_chunk"])
        for ident, text in parsed:
            if len(text) > limit:
                return f"块 {ident} 超过 max_chars_per_chunk"
    return parsed


def _validate_markdown(content: str, batch: dict[str, Any], *, as_of: str) -> list[tuple[str, str]] | str:
    meta, body = _split_frontmatter(content)
    missing = [key for key in FRONTMATTER_KEYS if not str(meta.get(key, "")).strip()]
    if missing:
        return "frontmatter 缺键: " + ",".join(missing)
    if meta["as_of"] != as_of:
        return "as_of 与目录或批次不一致"
    if meta["source_type"] not in DOC_SOURCE_TYPES:
        return "source_type 非法"
    if meta["provenance"] != "synthetic":
        return "provenance 必须为 synthetic"
    if meta.get("license") != LICENSE_SYNTHETIC:
        return "license 必须为 synthetic"
    if meta["domain"] != batch["domain"]:
        return "domain 与批次不一致"
    if meta["genre"] != batch["genre"]:
        return "genre 与批次不一致"
    lowered = content.lower()
    if any(marker.lower() in lowered for marker in _NBS_MARKERS):
        return "合成文档不得提及国家统计局或 stats.gov.cn"
    if "attribution" in meta or "data_source_url" in meta:
        return "合成文档不得包含 attribution 或 data_source_url"
    doc_id = meta["doc_id"]
    if not _doc_id_ok(doc_id, batch["batch_id"]):
        return f"doc_id 必须匹配 ^{batch['batch_id']}-[a-z0-9-]+$"
    return _validate_blocks(body, batch)


def _validate_batch_documents(
    documents: list[dict[str, str]],
    batch: dict[str, Any],
    seen: set[tuple[str, str]],
) -> str | None:
    expected_files = _file_count(batch)
    if len(documents) != expected_files:
        return f"文档数 {len(documents)} != n_docs {batch['n_docs']}" if not _is_pair(batch) else (
            f"文档数 {len(documents)} != 2*n_docs {expected_files}"
        )
    paths = [item["path"] for item in documents]
    if len(paths) != len(set(paths)):
        return "documents 路径重复"
    parsed: list[tuple[str, str, str, list[tuple[str, str]]]] = []
    local: set[tuple[str, str]] = set()
    for item in documents:
        rel = PurePosixPath(item["path"])
        meta, _body = _split_frontmatter(item["content"])
        as_of = str(meta.get("as_of", "")).strip()
        if _is_pair(batch):
            if as_of not in BATCH_AS_OF:
                return "as_of 与目录或批次不一致"
            expected_dir = _expected_rel_dir(batch["genre"], as_of)
        else:
            expected_dir = _expected_rel_dir(batch["genre"], batch["as_of"])
            as_of = batch["as_of"]
        if rel.suffix.lower() != ".md" or rel.parent.as_posix() != expected_dir or len(rel.parts) != 3:
            return f"路径不在 {expected_dir}/: {item['path']}"
        checked = _validate_markdown(item["content"], batch, as_of=as_of)
        if isinstance(checked, str):
            return checked
        doc_id = meta["doc_id"]
        key = (doc_id, as_of)
        if key in seen or key in local:
            return f"doc_id 与 as_of 已存在: {doc_id} {as_of}"
        local.add(key)
        parsed.append((doc_id, as_of, item["path"], checked))
    if _is_pair(batch):
        grouped: dict[str, dict[str, list[tuple[str, str]]]] = {}
        for doc_id, as_of, _path, blocks in parsed:
            grouped.setdefault(doc_id, {})[as_of] = blocks
        if len(grouped) != int(batch["n_docs"]):
            return f"pair 的 doc_id 数 {len(grouped)} != n_docs {batch['n_docs']}"
        for doc_id, versions in grouped.items():
            if set(versions) != {"T0", "T1"}:
                return f"pair 需要同一 doc_id 的 T0 与 T1: {doc_id}"
            ids0 = [ident for ident, _text in versions["T0"]]
            ids1 = [ident for ident, _text in versions["T1"]]
            if ids0 != ids1:
                return f"pair 的 pN 布局不一致: {doc_id}"
            texts0 = [text for _ident, text in versions["T0"]]
            texts1 = [text for _ident, text in versions["T1"]]
            if texts0 == texts1:
                return f"T1 必须改写已陈述事实: {doc_id}"
    return None


def _question_ids(queries: list[Any], seen: set[str]) -> list[str] | str:
    ids: list[str] = []
    for i, item in enumerate(queries):
        if not isinstance(item, dict):
            return f"题目不是对象: index {i}"
        qid = item.get("id")
        if not isinstance(qid, str) or not qid.strip():
            return f"题目缺少 id: index {i}"
        if qid in ids or qid in seen:
            return f"题目 id 冲突: {qid}"
        ids.append(qid)
    return ids


def _load_out_questions(out: Path) -> list[dict[str, Any]] | str:
    path = out / "questions.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return f"questions.json 无法解析: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("queries"), list):
        return "questions.json 无法解析"
    if not all(isinstance(item, dict) for item in data["queries"]):
        return "questions.json 无法解析"
    return list(data["queries"])


def _scan_doc_keys(roots: list[Path]) -> set[tuple[str, str]] | str:
    found: set[tuple[str, str]] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                return f"无法读取已有文档 {path}: {exc}"
            meta, _body = _split_frontmatter(text)
            doc_id = meta.get("doc_id", "").strip()
            as_of = meta.get("as_of", "").strip()
            if doc_id and as_of:
                found.add((doc_id, as_of))
    return found


def _load_manifest(out: Path) -> dict[str, Any]:
    path = out / MARKER_NAME
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _usage_pair(client: Any) -> tuple[int, int]:
    data = _token_usage_dict(client)
    return int(data.get("prompt_tokens") or 0), int(data.get("completion_tokens") or 0)


def _cost_cny(prompt_tokens: int, completion_tokens: int, in_price: float, out_price: float) -> float:
    return prompt_tokens / 1_000_000 * in_price + completion_tokens / 1_000_000 * out_price


def _resume_action(manifest: dict[str, Any], batch: dict[str, Any], fields: dict[str, Any], fingerprint: str) -> str:
    records = manifest.get("batches")
    if not isinstance(records, dict):
        return "run"
    rec = records.get(batch["batch_id"])
    if not isinstance(rec, dict):
        return "run"
    if rec.get("status") == "committing":
        return "recover"
    if rec.get("status") != "ok":
        return "run"
    for key, value in fields.items():
        if rec.get(key) != value:
            return "mismatch"
    if rec.get("fingerprint") != fingerprint:
        return "mismatch"
    return "skip"


def _discard_committing(out: Path, rec: dict[str, Any], seen: set[tuple[str, str]]) -> str | None:
    paths = rec.get("paths")
    if not isinstance(paths, list):
        return "committing 记录缺少 paths"
    out_resolved = out.resolve()
    for rel in paths:
        if not isinstance(rel, str) or _document_path_syntax_error(rel):
            return f"committing 路径非法: {rel}"
        target = (out / rel).resolve()
        if not _strictly_inside(target, out_resolved):
            return f"committing 路径非法: {rel}"
        if not target.exists():
            continue
        if not target.is_file():
            return f"committing 路径不是文件: {rel}"
        try:
            text = target.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            text = ""
        meta, _body = _split_frontmatter(text)
        doc_id = meta.get("doc_id", "").strip()
        as_of = meta.get("as_of", "").strip()
        if doc_id and as_of:
            seen.discard((doc_id, as_of))
        target.unlink()
    return None


def _manifest_body(state: dict[str, Any]) -> dict[str, Any]:
    failed = any(
        isinstance(rec, dict) and rec.get("status") == "failed"
        for rec in state["batches"].values()
    )
    body = {
        "model": state["model"],
        "temperature": state["temperature"],
        "seed": state["seed"],
        "recorded_at": state["recorded_at"],
        "token_usage": state["token_usage"],
        "checker_exit": state["checker_exit"],
        "checker_error": state["checker_error"],
        "batches": state["batches"],
        "spent_cny": state["spent_cny"],
        "max_cny": state["max_cny"],
        "pricing": state["pricing"],
        "stop_reason": state["stop_reason"],
    }
    note = state.get("raw_response_note")
    if failed or note:
        body["raw_response_note"] = note or RAW_GOLD_NOTE
    return body


def _flush_manifest(out: Path, state: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_manifest(out, _manifest_body(state))


def _commit_batch(out: Path, documents: list[dict[str, str]], queries: list[dict[str, Any]]) -> None:
    out_resolved = out.resolve()
    planned: list[tuple[Path, str]] = []
    for item in documents:
        dest = (out / item["path"]).resolve()
        if not _strictly_inside(dest, out_resolved):
            raise DraftShapeError(f"路径非法: {item['path']}")
        if dest.exists():
            raise DraftShapeError(f"文档路径已存在: {item['path']}")
        planned.append((dest, item["content"]))
    (out / "corpus").mkdir(parents=True, exist_ok=True)
    (out / "traps").mkdir(parents=True, exist_ok=True)
    for dest, content in planned:
        _atomic_write_text(dest, content)
    _atomic_write_text(
        out / "questions.json",
        json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gen_x1_drafts.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate", help="用 draft_model 按 spec 分批生成文档与题目草稿")
    gen.add_argument("--config", required=True)
    gen.add_argument("--out", required=True)
    gen.add_argument("--spec", required=True)
    gen.add_argument("--max-cny", required=True, type=float)
    gen.add_argument("--estimate-only", action="store_true")
    flag = sub.add_parser("flag", help="用 qwen-plus 非思考标记疑点")
    flag.add_argument("--config", required=True)
    flag.add_argument("--in", dest="inp", required=True)
    flag.add_argument("--sidecar", required=True)
    flag.add_argument("--spec", required=True)
    flag.add_argument("--max-cny", required=True, type=float)
    return parser


class _NoThinkingCreate:
    """不改 llm.py：在 chat.completions.create 上钉死 enable_thinking=False，并带上 max_tokens。"""

    def __init__(self, orig: Any, limits: dict[str, Any]) -> None:
        self._orig = orig
        self.limits = limits
        self.last_kwargs: dict[str, Any] | None = None
        self.last_finish_reason: str | None = None
        self.attempts = 0

    def __call__(self, **kwargs: Any) -> Any:
        self.attempts += 1
        extra = dict(kwargs.get("extra_body") or {})
        extra["enable_thinking"] = False
        kwargs["extra_body"] = extra
        max_tokens = self.limits.get("max_tokens")
        if max_tokens is not None:
            kwargs["max_tokens"] = int(max_tokens)
        self.last_kwargs = kwargs
        resp = self._orig(**kwargs)
        self.last_finish_reason = None
        choices = getattr(resp, "choices", None)
        if choices:
            self.last_finish_reason = getattr(choices[0], "finish_reason", None)
        return resp


def _pin_create(llm: Any, limits: dict[str, Any]) -> _NoThinkingCreate | None:
    """只碰已经注入的内部客户端，避免触发 LLMClient.client 去构造真实 SDK。"""
    inner = getattr(llm, "_client", None)
    if inner is None:
        return None
    inner.max_retries = 0
    completions = inner.chat.completions
    wrapper = _NoThinkingCreate(completions.create, limits)
    completions.create = wrapper
    return wrapper


def _pin_flag_thinking_off(llm: Any) -> None:
    _pin_create(llm, {"max_tokens": None})


def _write_failure_out(
    out: Path,
    raw_text: str,
    *,
    model: str,
    temperature: float,
    seed: int,
    recorded_at: str,
    token_usage: dict[str, Any],
    error: str,
    batch_id: str | None = None,
    state: dict[str, Any] | None = None,
) -> None:
    """失败路径也写清单，以便同一 --out 可以再次覆盖。不删除已完成批次。"""
    out.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(out / "raw-response.txt", raw_text)
    if batch_id:
        _atomic_write_text(out / "raw" / f"{batch_id}.txt", raw_text)
    if state is not None:
        state["checker_error"] = error
        state["raw_response_note"] = RAW_GOLD_NOTE
        _flush_manifest(out, state)
        return
    _write_manifest(
        out,
        {
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "recorded_at": recorded_at,
            "token_usage": token_usage,
            "checker_exit": None,
            "checker_error": error,
            "raw_response_note": RAW_GOLD_NOTE,
        },
    )


def _run_generate(args: argparse.Namespace, llm_client: Any) -> int:
    out = Path(args.out)
    deny = _can_overwrite_out(out)
    if deny:
        print(deny, file=sys.stderr)
        return 1
    cfg_path = Path(args.config)
    try:
        cfg = _load_config(cfg_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"错误: 无法读取配置: {exc}", file=sys.stderr)
        return 1
    max_cny = _parse_max_cny(args.max_cny)
    if isinstance(max_cny, str):
        print(f"错误: {max_cny}", file=sys.stderr)
        return 1
    spec = _load_spec(Path(args.spec))
    if isinstance(spec, str):
        print(f"错误: {spec}", file=sys.stderr)
        return 1
    if args.estimate_only:
        estimated = _estimate_spec(spec)
        if isinstance(estimated, str):
            print(f"错误: {estimated}", file=sys.stderr)
            return 1
        print(_format_estimate(estimated), end="")
        return 0
    decoded = _require_draft_decoding(cfg)
    if isinstance(decoded, str):
        print(f"错误: {decoded}", file=sys.stderr)
        return 1
    temperature, seed = decoded
    draft_model = cfg.get("draft_model")
    if draft_model != DRAFT_MODEL:
        print(f"错误: draft_model 必须为 {DRAFT_MODEL}", file=sys.stderr)
        return 1
    pricing = _parse_pricing(spec)
    if isinstance(pricing, str):
        print(f"错误: {pricing}", file=sys.stderr)
        return 1
    in_price, out_price, price_source = pricing
    prev = _load_manifest(out)
    prev_batches = prev.get("batches") if isinstance(prev.get("batches"), dict) else {}
    plans: list[tuple[dict[str, Any], str, dict[str, Any], str]] = []
    for batch in spec["batches"]:
        prompt = _build_batch_prompt(batch)
        fields = _decoding_fields(draft_model, temperature, seed, prompt)
        fingerprint = _batch_fingerprint(batch, fields)
        plans.append((batch, prompt, fields, fingerprint))
        if _resume_action(prev, batch, fields, fingerprint) == "mismatch":
            print(f"错误: {DECODING_MISMATCH}", file=sys.stderr)
            return 1
    loaded_questions = _load_out_questions(out)
    if isinstance(loaded_questions, str):
        print(f"错误: {loaded_questions}", file=sys.stderr)
        return 1
    queries = loaded_questions
    seen_ids: set[str] = set()
    for item in queries:
        qid = item.get("id")
        if isinstance(qid, str):
            seen_ids.add(qid)
    seen_docs = _scan_doc_keys([out, PUBLIC_CORPUS, PUBLIC_TRAPS])
    if isinstance(seen_docs, str):
        print(f"错误: {seen_docs}", file=sys.stderr)
        return 1
    prev_usage = prev.get("token_usage") if isinstance(prev.get("token_usage"), dict) else {}
    decoding = DecodingParams(model=draft_model, temperature=temperature, seed=seed)
    state: dict[str, Any] = {
        "model": draft_model,
        "temperature": temperature,
        "seed": seed,
        "recorded_at": prev.get("recorded_at") or decoding.recorded_at,
        "batches": {key: dict(val) for key, val in prev_batches.items() if isinstance(val, dict)},
        "spent_cny": float(prev.get("spent_cny") or 0.0),
        "max_cny": max_cny,
        "pricing": {
            "input_cny_per_million": in_price,
            "output_cny_per_million": out_price,
            "source": price_source,
        },
        "stop_reason": None,
        "checker_exit": None,
        "checker_error": None,
        "raw_response_note": None,
        "token_usage": {
            "prompt_tokens": int(prev_usage.get("prompt_tokens") or 0),
            "completion_tokens": int(prev_usage.get("completion_tokens") or 0),
            "total_tokens": int(prev_usage.get("prompt_tokens") or 0)
            + int(prev_usage.get("completion_tokens") or 0),
        },
    }
    # 第一份文档落盘前清单必须已经在，首批写到一半也能靠 committing 续跑。
    _flush_manifest(out, state)
    client_box: dict[str, Any] = {"client": llm_client}
    limits: dict[str, Any] = {"max_tokens": None}
    wrapper_box: dict[str, Any] = {"wrapper": None}

    def _client() -> Any:
        if client_box["client"] is None:
            client_box["client"] = LLMClient()
        return client_box["client"]

    def _arm(client: Any, max_tokens: int) -> None:
        limits["max_tokens"] = max_tokens
        if wrapper_box["wrapper"] is None:
            wrapper_box["wrapper"] = _pin_create(client, limits)

    def _finish_reason(message: Any) -> str | None:
        wrapper = wrapper_box["wrapper"]
        if wrapper is not None and wrapper.last_finish_reason:
            return wrapper.last_finish_reason
        value = getattr(message, "finish_reason", None)
        return value if isinstance(value, str) else None

    def _apply_usage(prompt_tokens: int, completion_tokens: int, cost: float) -> None:
        state["spent_cny"] += cost
        usage = state["token_usage"]
        usage["prompt_tokens"] += prompt_tokens
        usage["completion_tokens"] += completion_tokens
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    def _put_batch(batch_id: str, fields: dict[str, Any], fingerprint: str, **extra: Any) -> None:
        record = {
            "fingerprint": fingerprint,
            "draft_model": fields["draft_model"],
            "draft_temperature": fields["draft_temperature"],
            "draft_seed": fields["draft_seed"],
            "prompt_sha256": fields["prompt_sha256"],
        }
        record.update(extra)
        state["batches"][batch_id] = record

    def _fail_batch(batch_id: str, raw_text: str, error: str, fields: dict[str, Any], fingerprint: str) -> None:
        prev_rec = state["batches"].get(batch_id, {})
        if not isinstance(prev_rec, dict):
            prev_rec = {}
        _put_batch(
            batch_id,
            fields,
            fingerprint,
            status="failed",
            error=error,
            cost_cny=prev_rec.get("cost_cny", 0.0),
            prompt_tokens=prev_rec.get("prompt_tokens", 0),
            completion_tokens=prev_rec.get("completion_tokens", 0),
        )
        _write_failure_out(
            out,
            raw_text,
            model=draft_model,
            temperature=temperature,
            seed=seed,
            recorded_at=state["recorded_at"],
            token_usage=state["token_usage"],
            error=error,
            batch_id=batch_id,
            state=state,
        )
        print(f"错误: 批次 {batch_id}: {error}；{RAW_GOLD_NOTE}", file=sys.stderr)

    for batch, prompt, fields, fingerprint in plans:
        batch_id = batch["batch_id"]
        action = _resume_action({"batches": state["batches"]}, batch, fields, fingerprint)
        if action == "skip":
            continue
        upper_in = _input_token_upper(prompt)
        upper_out = _output_token_upper(batch)
        upper_cny = _cost_cny(upper_in, upper_out, in_price, out_price)
        if state["spent_cny"] + upper_cny > max_cny:
            state["stop_reason"] = "budget"
            print("错误: 累计花费已达 --max-cny，停止后续批次", file=sys.stderr)
            break
        if action == "recover":
            rec = state["batches"].get(batch_id, {})
            discard_err = _discard_committing(out, rec if isinstance(rec, dict) else {}, seen_docs)
            if discard_err:
                print(f"错误: 批次 {batch_id}: {discard_err}", file=sys.stderr)
                return 1
        client = _client()
        _arm(client, upper_out)
        before_prompt, before_completion = _usage_pair(client)
        try:
            message = client.chat(
                [{"role": "user", "content": prompt}],
                decoding=decoding,
            )
        except Exception as exc:
            _apply_usage(upper_in, upper_out, upper_cny)
            line = str(exc).strip().splitlines()
            detail = line[0] if line else type(exc).__name__
            _put_batch(
                batch_id,
                fields,
                fingerprint,
                status="failed",
                error=detail,
                cost_cny=upper_cny,
                prompt_tokens=upper_in,
                completion_tokens=upper_out,
            )
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: {detail}", file=sys.stderr)
            return 1
        after_prompt, after_completion = _usage_pair(client)
        delta_prompt = max(0, after_prompt - before_prompt)
        delta_completion = max(0, after_completion - before_completion)
        state["recorded_at"] = decoding.recorded_at
        raw_text = getattr(message, "content", "") or ""
        if delta_prompt == 0 and delta_completion == 0:
            _apply_usage(upper_in, upper_out, upper_cny)
            _put_batch(
                batch_id,
                fields,
                fingerprint,
                status="failed",
                error="用量缺失或为 0",
                cost_cny=upper_cny,
                prompt_tokens=upper_in,
                completion_tokens=upper_out,
            )
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: 用量缺失或为 0", file=sys.stderr)
            return 1
        cost = _cost_cny(delta_prompt, delta_completion, in_price, out_price)
        _apply_usage(delta_prompt, delta_completion, cost)
        _put_batch(
            batch_id,
            fields,
            fingerprint,
            status="failed",
            error=None,
            cost_cny=cost,
            prompt_tokens=delta_prompt,
            completion_tokens=delta_completion,
        )
        if _finish_reason(message) == "length":
            state["batches"][batch_id]["error"] = "finish_reason=length"
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: finish_reason=length", file=sys.stderr)
            return 1
        try:
            parsed = _parse_json_content(raw_text)
        except json.JSONDecodeError as exc:
            _fail_batch(batch_id, raw_text, f"模型输出不是 JSON: {exc}", fields, fingerprint)
            continue
        try:
            payload = _normalize_generate_payload(parsed)
        except DraftShapeError as exc:
            _fail_batch(batch_id, raw_text, str(exc), fields, fingerprint)
            continue
        doc_err = _validate_batch_documents(payload["documents"], batch, seen_docs)
        if doc_err:
            _fail_batch(batch_id, raw_text, doc_err, fields, fingerprint)
            continue
        id_result = _question_ids(payload["questions"]["queries"], seen_ids)
        if isinstance(id_result, str):
            _fail_batch(batch_id, raw_text, id_result, fields, fingerprint)
            if "冲突" in id_result:
                state["stop_reason"] = "id_conflict"
                break
            continue
        if "n_questions" in batch and len(id_result) != int(batch["n_questions"]):
            _fail_batch(
                batch_id,
                raw_text,
                f"题目数 {len(id_result)} 与 n_questions 不一致",
                fields,
                fingerprint,
            )
            continue
        rels = [PurePosixPath(item["path"]).as_posix() for item in payload["documents"]]
        _put_batch(
            batch_id,
            fields,
            fingerprint,
            status="committing",
            error=None,
            cost_cny=cost,
            prompt_tokens=delta_prompt,
            completion_tokens=delta_completion,
            paths=rels,
        )
        _flush_manifest(out, state)
        merged_queries = queries + payload["questions"]["queries"]
        try:
            _commit_batch(out, payload["documents"], merged_queries)
        except DraftShapeError as exc:
            print(f"错误: 批次 {batch_id}: {exc}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"错误: 批次 {batch_id}: 写入草稿失败: {exc}", file=sys.stderr)
            return 1
        queries = merged_queries
        seen_ids.update(id_result)
        for item in payload["documents"]:
            meta, _body = _split_frontmatter(item["content"])
            seen_docs.add((meta["doc_id"], meta["as_of"]))
        _put_batch(
            batch_id,
            fields,
            fingerprint,
            status="ok",
            error=None,
            cost_cny=cost,
            prompt_tokens=delta_prompt,
            completion_tokens=delta_completion,
            paths=rels,
        )
        state["checker_error"] = None
        _flush_manifest(out, state)

    qpath = out / "questions.json"
    if qpath.is_file():
        checker_exit: int | None = None
        checker_error: str | None = None
        try:
            result = check_x1(out / "corpus", out / "traps", qpath, cfg_path)
            _print_checker(result)
            checker_exit = result.exit_code
        except Exception as exc:
            checker_error = f"{type(exc).__name__}: {exc}"
            print(f"checker_error={checker_error}")
        state["checker_exit"] = checker_exit
        state["checker_error"] = checker_error
    if state["batches"] or state["stop_reason"]:
        _flush_manifest(out, state)
    current_ids = [batch["batch_id"] for batch in spec["batches"]]
    failed_current = any(
        isinstance(state["batches"].get(bid), dict) and state["batches"][bid].get("status") == "failed"
        for bid in current_ids
    )
    if state["stop_reason"] or failed_current:
        return 1
    return 0


def _load_flag_questions(inp: Path) -> list[dict[str, Any]]:
    if inp.is_dir():
        inp = inp / "questions.json"
    raw = json.loads(inp.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        qs = raw.get("queries", raw)
        if isinstance(qs, list):
            return list(qs)
        raise ValueError("抽检输入需要 queries 数组")
    if isinstance(raw, list):
        return list(raw)
    raise ValueError("抽检输入不是 JSON 数组或对象")


def _flag_prompt(slim: list[dict[str, Any]]) -> str:
    return _flag_skeleton() + json.dumps(slim, ensure_ascii=False)


def _flag_output_upper(n_questions: int) -> int:
    return max(EST_OUTPUT_TOKENS_PER_CHUNK, n_questions * EST_OUTPUT_TOKENS_PER_QUESTION)


def _read_flag_spent(sidecar: Path) -> float:
    if not sidecar.is_file() or not _is_script_sidecar(sidecar):
        return 0.0
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    return float(data.get("spent_cny") or 0.0)


def _write_flag_payload(sidecar: Path, payload: dict[str, Any]) -> None:
    _atomic_write_text(sidecar, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _run_flag(args: argparse.Namespace, llm_client: Any) -> int:
    sidecar = Path(args.sidecar)
    deny = _can_write_sidecar(sidecar)
    if deny:
        print(deny, file=sys.stderr)
        return 1
    cfg = _load_config(Path(args.config))
    if cfg.get("flag_model") != FLAG_MODEL:
        print(f"错误: flag_model 必须为 {FLAG_MODEL}", file=sys.stderr)
        return 1
    if cfg.get("flag_thinking") is not False:
        print("错误: flag_thinking 必须为 false", file=sys.stderr)
        return 1
    max_cny = _parse_max_cny(args.max_cny)
    if isinstance(max_cny, str):
        print(f"错误: {max_cny}", file=sys.stderr)
        return 1
    try:
        spec_obj = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"错误: 无法读取 spec: {exc}", file=sys.stderr)
        return 1
    flag_pricing = _parse_pricing_block(
        spec_obj.get("flag_pricing") if isinstance(spec_obj, dict) else None,
        "flag_pricing",
    )
    if isinstance(flag_pricing, str):
        print(f"错误: {flag_pricing}", file=sys.stderr)
        return 1
    in_price, out_price, price_source = flag_pricing
    questions = _load_flag_questions(Path(args.inp))
    slim = [{"id": q.get("id"), "query": q.get("query")} for q in questions]
    prompt = _flag_prompt(slim)
    upper_in = _input_token_upper(prompt)
    upper_out = _flag_output_upper(len(slim))
    upper_cny = _cost_cny(upper_in, upper_out, in_price, out_price)
    spent = _read_flag_spent(sidecar)
    if spent + upper_cny > max_cny:
        print("错误: 累计花费已达 --max-cny，停止后续批次", file=sys.stderr)
        return 1
    client = llm_client or LLMClient()
    limits: dict[str, Any] = {"max_tokens": upper_out}
    wrapper = _pin_create(client, limits)
    flag_temperature = 0.0
    decoding = DecodingParams(model=FLAG_MODEL, temperature=flag_temperature)
    before_prompt, before_completion = _usage_pair(client)
    try:
        message = client.chat(
            [{"role": "user", "content": prompt}],
            decoding=decoding,
        )
    except Exception as exc:
        line = str(exc).strip().splitlines()
        detail = line[0] if line else type(exc).__name__
        _write_flag_payload(
            sidecar,
            {
                SIDECAR_MARKER: True,
                "model": FLAG_MODEL,
                "flag_thinking": False,
                "temperature": flag_temperature,
                "status": "failed",
                "error": detail,
                "spent_cny": spent + upper_cny,
                "max_cny": max_cny,
                "pricing_source": price_source,
                "notes": [],
            },
        )
        print(f"错误: 抽检调用失败: {detail}", file=sys.stderr)
        return 1
    after_prompt, after_completion = _usage_pair(client)
    delta_prompt = max(0, after_prompt - before_prompt)
    delta_completion = max(0, after_completion - before_completion)
    if delta_prompt == 0 and delta_completion == 0:
        _write_flag_payload(
            sidecar,
            {
                SIDECAR_MARKER: True,
                "model": FLAG_MODEL,
                "flag_thinking": False,
                "temperature": flag_temperature,
                "status": "failed",
                "error": "用量缺失或为 0",
                "spent_cny": spent + upper_cny,
                "max_cny": max_cny,
                "pricing_source": price_source,
                "notes": [],
            },
        )
        print("错误: 抽检用量缺失或为 0", file=sys.stderr)
        return 1
    cost = _cost_cny(delta_prompt, delta_completion, in_price, out_price)
    finish = None
    if wrapper is not None and wrapper.last_finish_reason:
        finish = wrapper.last_finish_reason
    else:
        value = getattr(message, "finish_reason", None)
        if isinstance(value, str):
            finish = value
    if finish == "length":
        _write_flag_payload(
            sidecar,
            {
                SIDECAR_MARKER: True,
                "model": FLAG_MODEL,
                "flag_thinking": False,
                "temperature": flag_temperature,
                "status": "failed",
                "error": "finish_reason=length",
                "spent_cny": spent + cost,
                "max_cny": max_cny,
                "pricing_source": price_source,
                "notes": [],
            },
        )
        print("错误: 抽检 finish_reason=length", file=sys.stderr)
        return 1
    try:
        notes = _parse_json_content(getattr(message, "content", "") or "")
    except json.JSONDecodeError:
        notes = {"suspicion": getattr(message, "content", "") or ""}
    notes = _whitelist_notes(notes)
    payload = {
        SIDECAR_MARKER: True,
        "model": FLAG_MODEL,
        "flag_thinking": False,
        "temperature": decoding.temperature,
        "status": "ok",
        "spent_cny": spent + cost,
        "max_cny": max_cny,
        "pricing_source": price_source,
        "notes": notes,
    }
    _write_flag_payload(sidecar, payload)
    return 0


def main(argv: list[str] | None = None, llm_client: Any = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 1
        return int(code)
    if args.cmd == "generate":
        return _run_generate(args, llm_client)
    if args.cmd == "flag":
        return _run_flag(args, llm_client)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
