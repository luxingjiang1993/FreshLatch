"""草稿 markdown 的 frontmatter 与块校验。"""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from freshlatch.eval.x1_checks import PUBLIC_LICENSES
from freshlatch.store.ingest import META_RE

from freshlatch.eval.x1_drafts.batch import _expected_rel_dir, _file_count, _is_pair
from freshlatch.eval.x1_drafts.constants import (
    BATCH_AS_OF,
    DOC_SOURCE_TYPES,
    FRONTMATTER_KEYS,
    LICENSE_SYNTHETIC,
    _BLOCK_ID_RE,
    _H2_LINE_RE,
    _NBS_MARKERS,
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


def _duplicate_frontmatter_key(content: str) -> str | None:
    """strip 之后撞名的键直接拒绝，避免后写的覆盖先写的。"""
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    matched = META_RE.match(text)
    if not matched:
        return None
    seen: set[str] = set()
    for line in matched.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, _value = line.partition(":")
        stripped = key.strip()
        if not stripped:
            continue
        if stripped in seen:
            return f"frontmatter 键重复: {stripped}"
        seen.add(stripped)
    return None


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
    expected = int(batch["chunks_per_doc"])
    if len(parsed) != expected:
        return f"期望 {expected} 段，实得 {len(parsed)} 段"
    if "max_chars_per_chunk" in batch:
        limit = int(batch["max_chars_per_chunk"])
        for ident, text in parsed:
            if len(text) > limit:
                return f"块 {ident} 超过 max_chars_per_chunk"
    return parsed


def _validate_markdown(content: str, batch: dict[str, Any], *, as_of: str) -> list[tuple[str, str]] | str:
    duplicate = _duplicate_frontmatter_key(content)
    if duplicate:
        return duplicate
    meta, body = _split_frontmatter(content)
    if "attribution" in meta or "data_source_url" in meta:
        return "合成文档不得包含 attribution 或 data_source_url"
    unknown = [key for key in meta if key not in FRONTMATTER_KEYS]
    if unknown:
        return "frontmatter 含未知键: " + ",".join(unknown)
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
        return "合成文档不得提及国家统计局、统计局或 stats.gov.cn"
    doc_id = meta["doc_id"]
    if not _doc_id_ok(doc_id, batch["batch_id"]):
        return f"doc_id 必须匹配 ^{batch['batch_id']}-[a-z0-9-]+$"
    return _validate_blocks(body, batch)


def _validate_batch_documents(
    documents: list[dict[str, str]],
    batch: dict[str, Any],
    seen: set[tuple[str, str]],
    out: Path,
    public_doc_ids: set[str] | None = None,
) -> str | None:
    expected_files = _file_count(batch)
    if len(documents) != expected_files:
        return f"文档数 {len(documents)} != n_docs {batch['n_docs']}" if not _is_pair(batch) else (
            f"文档数 {len(documents)} != 2*n_docs {expected_files}"
        )
    public = public_doc_ids or set()
    parsed: list[tuple[str, str, str, list[tuple[str, str]]]] = []
    local: set[tuple[str, str]] = set()
    rewritten_paths: list[str] = []
    for item in documents:
        rel = PurePosixPath(item["path"])
        meta, _body = _split_frontmatter(item["content"])
        doc_id_early = str(meta.get("doc_id", "")).strip()
        if doc_id_early and doc_id_early in public:
            return f"doc_id 已存在于公开语料: {doc_id_early}"
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
        # 模型常用 strategy_review_01.md 或裸 uuid。目录通过后，文件名改成 doc_id.md。
        new_path = f"{expected_dir}/{doc_id}.md"
        item["path"] = new_path
        if new_path in rewritten_paths:
            return "documents 路径重复"
        if (out / new_path).exists():
            return f"文档路径已存在: {new_path}"
        rewritten_paths.append(new_path)
        key = (doc_id, as_of)
        if key in seen or key in local:
            return f"doc_id 与 as_of 已存在: {doc_id} {as_of}"
        local.add(key)
        parsed.append((doc_id, as_of, new_path, checked))
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


def _prefix_question_ids(queries: list[Any], batch_id: str) -> None:
    """各批都回 q1 时，落盘前改成 {batch_id}-q1。已经带本批前缀的不再加。"""
    prefix = f"{batch_id}-"
    for item in queries:
        if not isinstance(item, dict):
            continue
        qid = item.get("id")
        if not isinstance(qid, str) or not qid.strip() or qid.startswith(prefix):
            continue
        item["id"] = prefix + qid


def _question_as_of_error(queries: list[Any]) -> str | None:
    for i, item in enumerate(queries):
        if not isinstance(item, dict):
            return f"题目不是对象: index {i}"
        if item.get("as_of") not in BATCH_AS_OF:
            return f"题目 as_of 必须是 T0 或 T1: index {i}"
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


def _is_public_corpus_meta(meta: dict[str, str]) -> bool:
    """公开法条才算「公开语料」。合成金标和公开文件放在同一目录，不能把合成 doc_id 当成公开占用。"""
    provenance = meta.get("provenance", "").strip()
    license_ = meta.get("license", "").strip()
    return provenance == "public" or license_ in PUBLIC_LICENSES


def _scan_doc_keys(
    roots: list[Path],
    *,
    public_only: bool = False,
) -> set[tuple[str, str]] | str:
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
            if public_only and not _is_public_corpus_meta(meta):
                continue
            doc_id = meta.get("doc_id", "").strip()
            as_of = meta.get("as_of", "").strip()
            if doc_id and as_of:
                found.add((doc_id, as_of))
    return found
