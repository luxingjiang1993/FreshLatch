"""固定公开 eval 包的本地回放（A-P7）。

一条命令：``python -m freshlatch.eval public-pack``。
RESULT 的 ``content_hash`` 是去掉该字段后的规范 JSON 的 sha256。
abstain 只看 ``system_action``，不读 ``ragas_faithfulness``。
不调用付费 API，不写 RESULT-Y，不改 floors / gold / x1。
"""

from __future__ import annotations

import json
from pathlib import Path

from freshlatch.store.checksum import normalize_newlines, sha256_hex

PACK_ID = "a-p7-public-eval-v1"
PACK_REL = Path("tests/eval/fixtures/a_p7_public_eval_pack.json")
RESULT_NAME = "RESULT.json"
TICKET = "A-P7"

_LABELS = frozenset({"supported", "unsupported", "abstain"})
_ACTIONS = frozenset({"answer", "abstain"})
_BANNED_PACK_NAMES = frozenset({
    "gold.json",
    "retrieve_gold.json",
    "retrieve_hard_gold.json",
})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_pack_path() -> Path:
    """仓库内的固定夹具。不读 gold，不读 x1。"""
    return _repo_root() / PACK_REL


def canonical_result_bytes(result: dict) -> bytes:
    """规范 JSON：排序键、紧凑分隔、UTF-8、无末尾换行。不含 ``content_hash``。"""
    body = {key: value for key, value in result.items() if key != "content_hash"}
    text = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text.encode("utf-8")


def content_hash_of(result: dict) -> str:
    """对规范 JSON 字节做 sha256，小写 hex。"""
    return sha256_hex(canonical_result_bytes(result))


def verify_content_hash(result: dict) -> bool:
    """字段与规范 JSON 重算一致才为真。"""
    got = result.get("content_hash")
    if not isinstance(got, str):
        return False
    return got == content_hash_of(result)


def replay_public_pack(pack_path: Path | None = None) -> dict:
    """回放固定包，返回带 ``content_hash`` 的 RESULT。不写盘。"""
    path = default_pack_path() if pack_path is None else Path(pack_path)
    _reject_pack_path(path)
    if not path.is_file():
        raise ValueError(f"固定 eval 包不存在: {path.as_posix()}")
    raw = normalize_newlines(path.read_bytes(), "lf")
    try:
        pack = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("固定 eval 包不是 UTF-8 JSON") from exc
    if not isinstance(pack, dict):
        raise ValueError("固定 eval 包必须是 JSON 对象")
    return result_from_pack(pack, pack_sha256=sha256_hex(raw))


def result_from_pack(pack: dict, *, pack_sha256: str) -> dict:
    """由已解析的包构造 RESULT。``pack_sha256`` 由调用方按 LF 字节算好。"""
    if pack.get("pack_id") != PACK_ID:
        raise ValueError(f"pack_id 必须是 {PACK_ID}")
    if pack.get("level") != "smoke":
        raise ValueError("level 必须是 smoke")
    items = pack.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items 必须是非空数组")
    if not isinstance(pack_sha256, str) or len(pack_sha256) != 64:
        raise ValueError("pack_sha256 必须是 64 位小写 hex")
    rows = [_row(item) for item in items]
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("item id 重复")
    rows.sort(key=lambda row: row["id"])
    result = {
        "ticket": TICKET,
        "pack_id": PACK_ID,
        "pack_sha256": pack_sha256,
        "level": "smoke",
        "paid_api": False,
        "counted_as_pass": False,
        "invents_sesoi": False,
        "writes_result_y": False,
        "ragas_is_ground_truth": False,
        "ragas_used_as_label": False,
        "abstain_source": "system_action",
        "on_authoritative_leaderboard": False,
        "scope": "公开可复现 ≠ 登上权威榜",
        "n": len(rows),
        "n_abstain": sum(1 for row in rows if row["replay_label"] == "abstain"),
        "n_label_match": sum(1 for row in rows if row["label_match"]),
        "rows": rows,
    }
    result["content_hash"] = content_hash_of(result)
    return result


def write_result(result: dict, out_dir: Path, *, root: Path | None = None) -> Path:
    """把 RESULT 写成 ``RESULT.json``。拒绝证据目录与 data/。"""
    if not verify_content_hash(result):
        raise ValueError("content_hash 与规范 JSON 不一致")
    base = _repo_root() if root is None else Path(root)
    out = Path(out_dir)
    _reject_out(out, base)
    if out.exists() and not out.is_dir():
        raise ValueError("输出路径不是目录")
    out.mkdir(parents=True, exist_ok=True)
    dest = out / RESULT_NAME
    _reject_out(dest, base)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    dest.write_text(text, encoding="utf-8", newline="\n")
    return dest


def _row(item: object) -> dict:
    if not isinstance(item, dict):
        raise ValueError("item 必须是对象")
    item_id = _token(item.get("id"), "id")
    action = item.get("system_action")
    if action not in _ACTIONS:
        raise ValueError(f"{item_id} 的 system_action 必须是 answer 或 abstain")
    label = item.get("independent_label")
    if label not in _LABELS:
        raise ValueError(f"{item_id} 的 independent_label 不在封闭枚举")
    context_ids = _str_list(item.get("context_ids"), item_id, "context_ids")
    cited_ids = _str_list(item.get("cited_ids"), item_id, "cited_ids")
    span = item.get("context_span")
    answer = item.get("answer")
    if not isinstance(span, str) or not span:
        raise ValueError(f"{item_id} 的 context_span 必须是非空字符串")
    if not isinstance(answer, str) or not answer:
        raise ValueError(f"{item_id} 的 answer 必须是非空字符串")
    if "ragas_faithfulness" not in item:
        raise ValueError(f"{item_id} 缺少 ragas_faithfulness")
    ragas = _ragas_field(item.get("ragas_faithfulness"), item_id)
    replay = _replay_label(action, context_ids, cited_ids, span, answer)
    return {
        "id": item_id,
        "system_action": action,
        "independent_label": label,
        "replay_label": replay,
        "label_match": replay == label,
        "ragas_faithfulness": ragas,
        "ragas_used_as_label": False,
    }


def _replay_label(
    action: str,
    context_ids: list[str],
    cited_ids: list[str],
    span: str,
    answer: str,
) -> str:
    """abstain 优先。其余只看引用是否落在上下文、span 是否出现在答案里。"""
    if action == "abstain":
        return "abstain"
    cited_ok = bool(cited_ids) and all(cited in context_ids for cited in cited_ids)
    if cited_ok and span in answer:
        return "supported"
    return "unsupported"


def _ragas_field(value: object, item_id: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    raise ValueError(f"{item_id} 的 ragas_faithfulness 必须是字符串或 null")


def _str_list(value: object, item_id: str, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{item_id} 的 {field} 必须是数组")
    out: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry:
            raise ValueError(f"{item_id} 的 {field} 含空项")
        out.append(entry)
    return out


def _token(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
        raise ValueError(f"{field} 必须是不含空白的非空字符串")
    return value


def _reject_pack_path(path: Path) -> None:
    posix = path.as_posix()
    if path.name in _BANNED_PACK_NAMES:
        raise ValueError("公开包不得指向 gold")
    if "data/exp/x1" in posix:
        raise ValueError("公开包不得指向 x1")
    if "RESULT-Y" in path.name or "RESULT-Y" in posix:
        raise ValueError("公开包不得读取 RESULT-Y")


def _reject_out(path: Path, root: Path) -> None:
    resolved = path.resolve()
    if "RESULT-Y" in resolved.name:
        raise ValueError("公开包不得写入 RESULT-Y")
    try:
        rel = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return
    if rel == "data" or rel.startswith("data/"):
        raise ValueError("公开包 RESULT 不得写入 data/")
    if rel == "docs/evidence" or rel.startswith("docs/evidence/"):
        raise ValueError("公开包 RESULT 不得写入 docs/evidence/")
