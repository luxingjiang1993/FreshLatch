"""生成 x1 文档/题目草稿，并用 qwen-plus 非思考抽检（RET-01.7）。

温度与 seed 只从配置读取；缺省或 JSON null 时拒绝，不落入 DecodingParams 的 temperature 0。
generate 按 spec 分批各调用一次模型，合并进 --out。单价只读 spec.pricing，脚本不内置价格。
检查器退出码 2（阈值未写入）与 1（结构/许可）都打印，已通过校验的草稿仍写入 --out。
不把去污染阈值写进配置，也不把任何数字缺省传给检查器。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
GOLD_QUESTION_KEYS = ("relevant", "answer_points", "distractors")
NOTE_FIELDS = ("id", "suspicion", "reason", "severity")
RAW_GOLD_NOTE = "raw-response.txt 可能含模型自拟金标，不得当标签使用"
BATCH_GENRES = frozenset({f"S{i}" for i in range(1, 8)} | {"P2"})
BATCH_DOMAINS = frozenset({"D0", "D1", "D2", "D3"})
BATCH_AS_OF = frozenset({"T0", "T1"})
DOC_SOURCE_TYPES = frozenset({"private", "public", "internal"})
P2_ATTRIBUTION = "引自国家统计局网站 www.stats.gov.cn"
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
# 估 token 的口径：不调用模型。输入按 prompt 的 Unicode 码位数；输出按块与文档开销。
EST_OUTPUT_TOKENS_PER_CHUNK = 256
EST_OUTPUT_TOKENS_PER_DOC = 128
_BATCH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


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
    return low in {"answer_points", "distractors"}


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


def _write_manifest(dest: Path, fields: dict[str, Any]) -> None:
    (dest / MARKER_NAME).write_text(
        json.dumps(fields, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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
    keys = ("batch_id", "genre", "domain", "as_of", "n_docs", "chunks_per_doc", "topic")
    canon = {k: batch[k] for k in keys}
    if "must_include" in batch:
        canon["must_include"] = batch["must_include"]
    return canon


def _batch_fingerprint(batch: dict[str, Any]) -> str:
    blob = json.dumps(_batch_canon(batch), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _validate_batch(batch: Any, index: int) -> str | None:
    if not isinstance(batch, dict):
        return f"batches[{index}] 必须是对象"
    missing = [k for k in ("batch_id", "genre", "domain", "as_of", "n_docs", "chunks_per_doc", "topic") if k not in batch]
    if missing:
        return f"batches[{index}] 缺字段 {missing}"
    batch_id = batch["batch_id"]
    if not isinstance(batch_id, str) or not _BATCH_ID_RE.fullmatch(batch_id):
        return f"batches[{index}] batch_id 非法"
    if batch["genre"] not in BATCH_GENRES:
        return f"batches[{index}] genre 必须是 S1–S7 或 P2"
    if batch["domain"] not in BATCH_DOMAINS:
        return f"batches[{index}] domain 必须是 D0–D3"
    if batch["as_of"] not in BATCH_AS_OF:
        return f"batches[{index}] as_of 必须是 T0 或 T1"
    if not _is_int(batch["n_docs"]) or batch["n_docs"] < 1:
        return f"batches[{index}] n_docs 必须是正整数"
    if not _is_int(batch["chunks_per_doc"]) or not 2 <= batch["chunks_per_doc"] <= 6:
        return f"batches[{index}] chunks_per_doc 必须是 2–6 的整数"
    topic = batch["topic"]
    if not isinstance(topic, str) or not topic.strip():
        return f"batches[{index}] topic 必须是非空字符串"
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


def _parse_pricing(spec: dict[str, Any]) -> tuple[float, float, str] | str:
    pricing = spec.get("pricing")
    if not isinstance(pricing, dict):
        return "spec 缺少 pricing"
    source = pricing.get("source")
    if not isinstance(source, str) or not source.strip():
        return "pricing.source 必须是非空字符串"
    in_price = pricing.get("input_cny_per_million")
    out_price = pricing.get("output_cny_per_million")
    if not _decoding_number(in_price) or in_price < 0:
        return "pricing.input_cny_per_million 必须是非负数字"
    if not _decoding_number(out_price) or out_price < 0:
        return "pricing.output_cny_per_million 必须是非负数字"
    return float(in_price), float(out_price), source


def _parse_max_cny(value: Any) -> float | str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "--max-cny 必须是数字"
    if not math.isfinite(float(value)) or float(value) < 0:
        return "--max-cny 必须是有限的非负数"
    return float(value)


def _build_batch_prompt(batch: dict[str, Any]) -> str:
    """拼一批的用户提示。合成正文自写，不给金标，只要 JSON。must_include 原样塞进提示。"""
    dest = _expected_rel_dir(batch["genre"], batch["as_of"])
    lines = [
        "生成 x1 实验的合成文档与题目草稿。",
        "合成正文必须自写，不得以版权原文为模板整段改写。",
        "不得给出金标。",
        "只返回 JSON。",
        "只返回 JSON 对象：documents 数组（元素含 path 与 content），以及带 queries 数组的 questions 对象（必须使用 queries 包装）。",
        "每道题只给 id、query、category、eval_intent、as_of。",
        f"本批 batch_id={batch['batch_id']}。",
        f"genre={batch['genre']}，domain={batch['domain']}，as_of={batch['as_of']}。",
        f"n_docs={batch['n_docs']}，每份文档 chunks_per_doc={batch['chunks_per_doc']} 个块。",
        f"topic：{batch['topic']}",
        f"每份文档路径必须位于 {dest}/ 下，只一层文件名，扩展名 .md。",
        "frontmatter 必须包含 doc_id、as_of（与目录一致）、source_type（只允许 private、public、internal）、title、provenance: synthetic、license、domain、genre。",
        "正文必须是 2 到 6 个独立的 ## pN 块，块数等于 chunks_per_doc。",
    ]
    if batch["genre"] == "S7":
        lines.append("本批是检索陷阱文档，路径必须在 traps 下，不要写入 corpus。")
    if batch["genre"] == "P2":
        lines.append(
            "P2 文档另需 data_source_url，且 attribution 必须为：引自国家统计局网站 www.stats.gov.cn。"
            "叙述自写，只把 must_include 中的事实原样写入正文。"
        )
    if "must_include" in batch:
        lines.append("must_include（原样遵守，不要改写这些事实）：")
        lines.append(json.dumps(batch["must_include"], ensure_ascii=False))
    return "\n".join(lines)


def _estimate_spec(spec: dict[str, Any]) -> dict[str, Any] | str:
    pricing = _parse_pricing(spec)
    if isinstance(pricing, str):
        return pricing
    in_price, out_price, _source = pricing
    input_tokens = 0
    output_tokens = 0
    for batch in spec["batches"]:
        input_tokens += len(_build_batch_prompt(batch))
        output_tokens += (
            int(batch["n_docs"]) * int(batch["chunks_per_doc"]) * EST_OUTPUT_TOKENS_PER_CHUNK
            + int(batch["n_docs"]) * EST_OUTPUT_TOKENS_PER_DOC
        )
    cny = input_tokens / 1_000_000 * in_price + output_tokens / 1_000_000 * out_price
    return {
        "batches": len(spec["batches"]),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cny": cny,
    }


def _format_estimate(est: dict[str, Any]) -> str:
    return (
        f"batches={est['batches']}\n"
        f"input_tokens={est['input_tokens']} 估\n"
        f"output_tokens={est['output_tokens']} 估\n"
        f"cny={est['cny']:.8f} 估\n"
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


def _validate_batch_documents(documents: list[dict[str, str]], batch: dict[str, Any]) -> str | None:
    if len(documents) != int(batch["n_docs"]):
        return f"文档数 {len(documents)} != n_docs {batch['n_docs']}"
    expected_dir = _expected_rel_dir(batch["genre"], batch["as_of"])
    paths = [item["path"] for item in documents]
    if len(paths) != len(set(paths)):
        return "documents 路径重复"
    for item in documents:
        rel = PurePosixPath(item["path"])
        if rel.suffix.lower() != ".md" or rel.parent.as_posix() != expected_dir or len(rel.parts) != 3:
            return f"路径不在 {expected_dir}/: {item['path']}"
        err = _validate_markdown(item["content"], batch)
        if err:
            return err
    return None


def _validate_markdown(content: str, batch: dict[str, Any]) -> str | None:
    meta, body = _split_frontmatter(content)
    missing = [key for key in FRONTMATTER_KEYS if not str(meta.get(key, "")).strip()]
    if missing:
        return "frontmatter 缺键: " + ",".join(missing)
    if meta["as_of"] != batch["as_of"]:
        return "as_of 与目录或批次不一致"
    if meta["source_type"] not in DOC_SOURCE_TYPES:
        return "source_type 非法"
    if meta["provenance"] != "synthetic":
        return "provenance 必须为 synthetic"
    if meta["domain"] != batch["domain"]:
        return "domain 与批次不一致"
    if meta["genre"] != batch["genre"]:
        return "genre 与批次不一致"
    if batch["genre"] == "P2":
        if not meta.get("data_source_url", "").strip():
            return "P2 缺少 data_source_url"
        if meta.get("attribution", "") != P2_ATTRIBUTION:
            return "P2 attribution 必须为引自国家统计局网站 www.stats.gov.cn"
    chunk_ids = CLAUSE_RE.findall(body)
    if len(chunk_ids) < 2 or len(chunk_ids) > 6:
        return f"块数越界: {len(chunk_ids)}"
    if len(chunk_ids) != int(batch["chunks_per_doc"]):
        return f"块数 {len(chunk_ids)} 与 chunks_per_doc 不一致"
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


def _load_out_questions(out: Path) -> list[dict[str, Any]]:
    path = out / "questions.json"
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return []
    if isinstance(data, dict) and isinstance(data.get("queries"), list):
        return [item for item in data["queries"] if isinstance(item, dict)]
    return []


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


def _resume_action(manifest: dict[str, Any], batch: dict[str, Any]) -> str:
    records = manifest.get("batches")
    if not isinstance(records, dict):
        return "run"
    rec = records.get(batch["batch_id"])
    if not isinstance(rec, dict) or rec.get("status") != "ok":
        return "run"
    if rec.get("fingerprint") == _batch_fingerprint(batch):
        return "skip"
    return "mismatch"


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


def _commit_batch(staging: Path, out: Path, documents: list[dict[str, str]], queries: list[dict[str, Any]]) -> None:
    planned: list[tuple[Path, Path]] = []
    for item in documents:
        src = staging / item["path"]
        dest = out / item["path"]
        if dest.exists():
            raise DraftShapeError(f"文档路径已存在: {item['path']}")
        planned.append((src, dest))
    for src, dest in planned:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    (out / "corpus").mkdir(parents=True, exist_ok=True)
    (out / "traps").mkdir(parents=True, exist_ok=True)
    qpath = out / "questions.json"
    qpath.write_text(
        json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
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
    return parser


class _NoThinkingCreate:
    """不改 llm.py：在 chat.completions.create 上钉死 enable_thinking=False。"""

    def __init__(self, orig: Any) -> None:
        self._orig = orig
        self.last_kwargs: dict[str, Any] | None = None

    def __call__(self, **kwargs: Any) -> Any:
        extra = dict(kwargs.get("extra_body") or {})
        extra["enable_thinking"] = False
        kwargs["extra_body"] = extra
        self.last_kwargs = kwargs
        return self._orig(**kwargs)


def _pin_flag_thinking_off(llm: Any) -> None:
    inner = getattr(llm, "client", None)
    if inner is None:
        return
    completions = inner.chat.completions
    completions.create = _NoThinkingCreate(completions.create)


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
    (out / "raw-response.txt").write_text(raw_text, encoding="utf-8")
    if batch_id:
        raw_dir = out / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / f"{batch_id}.txt").write_text(raw_text, encoding="utf-8")
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
    decoded = _require_draft_decoding(cfg)
    if isinstance(decoded, str):
        print(f"错误: {decoded}", file=sys.stderr)
        return 1
    temperature, seed = decoded
    draft_model = cfg.get("draft_model")
    if draft_model != DRAFT_MODEL:
        print(f"错误: draft_model 必须为 {DRAFT_MODEL}", file=sys.stderr)
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
    pricing = _parse_pricing(spec)
    if isinstance(pricing, str):
        print(f"错误: {pricing}", file=sys.stderr)
        return 1
    in_price, out_price, price_source = pricing
    prev = _load_manifest(out)
    prev_batches = prev.get("batches") if isinstance(prev.get("batches"), dict) else {}
    for batch in spec["batches"]:
        if _resume_action(prev, batch) == "mismatch":
            print(
                f"错误: batch_id 已成功但 spec 与清单不一致: {batch['batch_id']}",
                file=sys.stderr,
            )
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
    queries = _load_out_questions(out)
    seen_ids: set[str] = set()
    for item in queries:
        qid = item.get("id")
        if isinstance(qid, str):
            seen_ids.add(qid)
    client_box: dict[str, Any] = {"client": llm_client}

    def _client() -> Any:
        if client_box["client"] is None:
            client_box["client"] = LLMClient()
        return client_box["client"]

    def _fail_batch(batch_id: str, raw_text: str, error: str) -> None:
        state["batches"][batch_id] = {
            "status": "failed",
            "fingerprint": state["batches"].get(batch_id, {}).get("fingerprint"),
            "error": error,
            "cost_cny": state["batches"].get(batch_id, {}).get("cost_cny", 0.0),
            "prompt_tokens": state["batches"].get(batch_id, {}).get("prompt_tokens", 0),
            "completion_tokens": state["batches"].get(batch_id, {}).get("completion_tokens", 0),
        }
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

    for batch in spec["batches"]:
        batch_id = batch["batch_id"]
        if _resume_action({"batches": state["batches"]}, batch) == "skip":
            continue
        if state["spent_cny"] >= max_cny:
            state["stop_reason"] = "budget"
            print("错误: 累计花费已达 --max-cny，停止后续批次", file=sys.stderr)
            break
        client = _client()
        before_prompt, before_completion = _usage_pair(client)
        message = client.chat(
            [{"role": "user", "content": _build_batch_prompt(batch)}],
            decoding=decoding,
        )
        after_prompt, after_completion = _usage_pair(client)
        delta_prompt = max(0, after_prompt - before_prompt)
        delta_completion = max(0, after_completion - before_completion)
        cost = _cost_cny(delta_prompt, delta_completion, in_price, out_price)
        state["spent_cny"] += cost
        state["recorded_at"] = decoding.recorded_at
        usage = state["token_usage"]
        usage["prompt_tokens"] += delta_prompt
        usage["completion_tokens"] += delta_completion
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
        state["batches"][batch_id] = {
            "status": "failed",
            "fingerprint": _batch_fingerprint(batch),
            "error": None,
            "cost_cny": cost,
            "prompt_tokens": delta_prompt,
            "completion_tokens": delta_completion,
        }
        raw_text = getattr(message, "content", "") or ""
        try:
            parsed = _parse_json_content(raw_text)
        except json.JSONDecodeError as exc:
            _fail_batch(batch_id, raw_text, f"模型输出不是 JSON: {exc}")
            continue
        try:
            payload = _normalize_generate_payload(parsed)
        except DraftShapeError as exc:
            _fail_batch(batch_id, raw_text, str(exc))
            continue
        doc_err = _validate_batch_documents(payload["documents"], batch)
        if doc_err:
            _fail_batch(batch_id, raw_text, doc_err)
            continue
        id_result = _question_ids(payload["questions"]["queries"], seen_ids)
        if isinstance(id_result, str):
            _fail_batch(batch_id, raw_text, id_result)
            if "冲突" in id_result:
                state["stop_reason"] = "id_conflict"
                break
            continue
        with tempfile.TemporaryDirectory(prefix="x1-drafts-") as tmp:
            staging = Path(tmp) / "bundle"
            try:
                _materialize_drafts(payload, staging)
            except DraftShapeError as exc:
                _fail_batch(batch_id, raw_text, str(exc))
                continue
            except OSError as exc:
                _fail_batch(batch_id, raw_text, f"写入草稿失败: {exc}")
                continue
            try:
                _commit_batch(staging, out, payload["documents"], queries + payload["questions"]["queries"])
            except DraftShapeError as exc:
                _fail_batch(batch_id, raw_text, str(exc))
                continue
            except OSError as exc:
                _fail_batch(batch_id, raw_text, f"写入草稿失败: {exc}")
                continue
        queries = queries + payload["questions"]["queries"]
        seen_ids.update(id_result)
        state["batches"][batch_id] = {
            "status": "ok",
            "fingerprint": _batch_fingerprint(batch),
            "error": None,
            "cost_cny": cost,
            "prompt_tokens": delta_prompt,
            "completion_tokens": delta_completion,
        }
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
    questions = _load_flag_questions(Path(args.inp))
    slim = [{"id": q.get("id"), "query": q.get("query")} for q in questions]
    client = llm_client or LLMClient()
    _pin_flag_thinking_off(client)
    flag_temperature = 0.0
    decoding = DecodingParams(model=FLAG_MODEL, temperature=flag_temperature)
    message = client.chat(
        [
            {
                "role": "user",
                "content": (
                    "对下列题目草稿做非思考抽检，只标记疑点。"
                    "只输出 id、suspicion、reason、severity。"
                    + json.dumps(slim, ensure_ascii=False)
                ),
            }
        ],
        decoding=decoding,
    )
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
        "notes": notes,
    }
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
