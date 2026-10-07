"""模型草稿 JSON 的形状整理与落盘前规范化。"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from freshlatch.eval.x1_drafts.constants import (
    GOLD_PLACEHOLDER,
    GOLD_QUESTION_KEYS,
    NOTE_FIELDS,
)
from freshlatch.eval.x1_drafts.paths import DraftShapeError

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


def _content_has_frontmatter_block(content: str) -> bool:
    return content.lstrip("\ufeff").lstrip().startswith("---")


def _yaml_scalar(value: Any) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        # splitlines 覆盖 \n \r 以外的分隔符，避免标量里再拆出新键。
        return " ".join(value.splitlines()).strip()
    return None


def _render_yaml_frontmatter(meta: dict[str, Any]) -> str:
    """把 frontmatter 对象渲染成 content 开头的 YAML 块。不改写 as_of。"""
    lines = ["---"]
    seen: set[str] = set()
    for key, value in meta.items():
        if not isinstance(key, str) or len(key.splitlines()) != 1:
            raise DraftShapeError(f"frontmatter 键非法: {key}")
        stripped = key.strip()
        if not stripped or ":" in stripped:
            raise DraftShapeError(f"frontmatter 键非法: {key}")
        if stripped in seen:
            raise DraftShapeError(f"frontmatter 键重复: {stripped}")
        seen.add(stripped)
        scalar = _yaml_scalar(value)
        if scalar is None:
            raise DraftShapeError(f"frontmatter 值必须是标量: {stripped}")
        lines.append(f"{stripped}: {scalar}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def _absorb_frontmatter_objects(documents: Any) -> Any:
    """content 没有 YAML 块时，把 frontmatter 对象折进去。两者都有则拒绝。"""
    if not isinstance(documents, list):
        return documents
    folded: list[Any] = []
    for i, item in enumerate(documents):
        if not isinstance(item, dict) or "frontmatter" not in item:
            folded.append(item)
            continue
        copied = dict(item)
        frontmatter = copied.pop("frontmatter")
        if not isinstance(frontmatter, dict):
            raise DraftShapeError(f"documents[{i}] frontmatter 必须是对象")
        content = copied.get("content", "")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise DraftShapeError(f"documents[{i}] content 必须是字符串")
        if _content_has_frontmatter_block(content):
            raise DraftShapeError(f"documents[{i}] 不能同时给出 frontmatter 对象和 content 里的 YAML 块")
        cleaned = _strip_nested_gold(frontmatter)
        if not isinstance(cleaned, dict):
            cleaned = {}
        copied["content"] = _render_yaml_frontmatter(cleaned) + content
        folded.append(copied)
    return folded


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
        documents = _normalize_documents(_absorb_frontmatter_objects(payload.get("documents")))
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
