"""清单续跑、花费对账与已提交批次。"""

from __future__ import annotations

import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from freshlatch.eval.x1_drafts._lookup import _pkg_attr
from freshlatch.eval.x1_drafts.batch import _batch_fingerprint
from freshlatch.eval.x1_drafts.constants import (
    MARKER_NAME,
    PUBLIC_CORPUS,
    PUBLIC_TRAPS,
    RAW_GOLD_NOTE,
    _DOC_BUCKETS,
    _DOC_SNAPSHOTS,
)
from freshlatch.eval.x1_drafts.documents import _scan_doc_keys, _split_frontmatter
from freshlatch.eval.x1_drafts.io import _write_manifest
from freshlatch.eval.x1_drafts.paths import DraftShapeError
from freshlatch.eval.x1_drafts.shape import (
    _document_path_syntax_error,
    _strictly_inside,
    _token_usage_dict,
)

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




def _finite_money(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _held_charge_error(spent: float, held: float, *, held_field: str = "cost_cny") -> str | None:
    """已记花费非负，且 0 ≤ 预扣 ≤ 花费。中断之后提示或单价可能变了，预扣可以低于当前上界。"""
    if spent < 0:
        return "清单异常: spent_cny"
    if held < 0:
        return f"清单异常: {held_field}"
    if held > spent + 1e-9:
        return "清单异常: spent_cny"
    return None


def _recorded_cost_total(batches: dict[str, Any]) -> float | str:
    """各批已记 cost_cny 之和，含 sunk 与 inflight。非法金额返回字段名。"""
    total = 0.0
    for rec in batches.values():
        if not isinstance(rec, dict) or "cost_cny" not in rec:
            continue
        cost = _finite_money(rec.get("cost_cny"))
        if cost is None or cost < 0:
            return "cost_cny"
        total += cost
    return total


def _spend_below_recorded(spent: float, recorded: float) -> str | None:
    """已记花费必须盖住各笔已记成本。手改把 spent_cny 清零、成本还在时落在这里。"""
    if spent + 1e-9 < recorded:
        return "清单异常: spent_cny"
    return None


def _manifest_anomaly(batches: dict[str, Any], spent: float) -> str | None:
    if not math.isfinite(spent) or spent < 0:
        return "清单异常: spent_cny"
    inflight = [
        bid
        for bid, rec in batches.items()
        if isinstance(rec, dict) and rec.get("status") == "inflight"
    ]
    if len(inflight) > 1:
        return "清单异常: inflight"
    if inflight:
        rec = batches[inflight[0]]
        held = _finite_money(rec.get("cost_cny")) if isinstance(rec, dict) else None
        if held is None:
            return "清单异常: cost_cny"
        # 该批已经不在本次 spec 里也不拒绝，调用方把它标成 sunk，预扣留在 spent_cny。
        charge_err = _held_charge_error(spent, held)
        if charge_err:
            return charge_err
    recorded = _recorded_cost_total(batches)
    if isinstance(recorded, str):
        return f"清单异常: {recorded}"
    return _spend_below_recorded(spent, recorded)


def _resume_action(manifest: dict[str, Any], batch: dict[str, Any], fields: dict[str, Any], _fingerprint: str) -> str:
    records = manifest.get("batches")
    if not isinstance(records, dict):
        return "run"
    rec = records.get(batch["batch_id"])
    if not isinstance(rec, dict):
        return "run"
    if rec.get("status") == "committing":
        return "recover"
    if rec.get("status") != "ok":
        # failed 与 inflight 可以重跑。只有 ok 才核对解码参数和批次规格。
        return "run"
    # ok 批次固定在当初记下的提示摘要上：只改提示不会重跑。
    # 改 spec、温度、seed 或模型仍报「解码参数与清单不一致」并退出。
    for key in ("draft_model", "draft_temperature", "draft_seed"):
        if rec.get(key) != fields.get(key):
            return "mismatch"
    recorded_sha = rec.get("prompt_sha256")
    if not isinstance(recorded_sha, str):
        return "mismatch"
    stable_fields = dict(fields)
    stable_fields["prompt_sha256"] = recorded_sha
    if rec.get("fingerprint") != _batch_fingerprint(batch, stable_fields):
        return "mismatch"
    return "skip"


def _recorded_doc_rel_ok(rel: str) -> bool:
    """恢复时只删本批记下来的文档：corpus|traps / t0|t1 / 文件名.md。"""
    posix = PurePosixPath(rel)
    if posix.suffix.lower() != ".md" or len(posix.parts) != 3:
        return False
    bucket, snap, _name = posix.parts
    return bucket in _DOC_BUCKETS and snap in _DOC_SNAPSHOTS


def _discard_committing(out: Path, rec: dict[str, Any], seen: set[tuple[str, str]]) -> str | None:
    paths = rec.get("paths")
    if not isinstance(paths, list):
        return "committing 记录缺少 paths"
    out_resolved = out.resolve()
    for rel in paths:
        if not isinstance(rel, str) or _document_path_syntax_error(rel) or not _recorded_doc_rel_ok(rel):
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


def _drop_committing_question_ids(
    out: Path,
    batches: dict[str, Any],
    queries: list[dict[str, Any]],
) -> list[dict[str, Any]] | str:
    """committing 批次的题目 id 从 questions.json 里摘掉，避免续跑报题目冲突。"""
    drop: set[str] = set()
    for rec in batches.values():
        if not isinstance(rec, dict) or rec.get("status") != "committing":
            continue
        qids = rec.get("question_ids")
        if not isinstance(qids, list):
            continue
        for qid in qids:
            if isinstance(qid, str) and qid:
                drop.add(qid)
    if not drop:
        return queries
    kept = [item for item in queries if item.get("id") not in drop]
    qpath = out / "questions.json"
    if qpath.is_file() and len(kept) != len(queries):
        try:
            _pkg_attr("_atomic_write_text")(
                qpath,
                json.dumps({"queries": kept}, ensure_ascii=False, indent=2) + "\n",
            )
        except OSError as exc:
            return f"questions.json 无法回滚: {exc}"
    return kept


def _discard_open_commits(out: Path, batches: dict[str, Any]) -> str | None:
    seen: set[tuple[str, str]] = set()
    for rec in batches.values():
        if isinstance(rec, dict) and rec.get("status") == "committing":
            err = _discard_committing(out, rec, seen)
            if err:
                return err
    return None


def _public_doc_ids() -> set[str] | str:
    found = _scan_doc_keys([PUBLIC_CORPUS, PUBLIC_TRAPS], public_only=True)
    if isinstance(found, str):
        return found
    return {doc_id for doc_id, _as_of in found}


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
        _pkg_attr("_atomic_write_text")(dest, content)
    _pkg_attr("_atomic_write_text")(
        out / "questions.json",
        json.dumps({"queries": queries}, ensure_ascii=False, indent=2) + "\n",
    )
