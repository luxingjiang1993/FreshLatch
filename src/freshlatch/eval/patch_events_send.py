"""显式正式入口的发送。只发送已经拼好的正文，不改提示词。"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_SEND: tuple[tuple[str, str], ...] = (
    ("C", "rewrite"),
    ("T", "rewrite"),
    ("B1", "rewrite"),
    ("B2", "claim"),
)


def formal_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """每条样本只排 C、T、B1 的 rewrite 和 B2 的 claim。不排 B2 的 diff。"""
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in _SEND:
            requests.append(
                {
                    "arm": arm,
                    "phase": phase,
                    "claim_id": row["claim_id"],
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
    return requests


def dispatch_prompt(
    request: Mapping[str, Any],
    chat: Callable[..., Any],
) -> dict[str, Any]:
    """空正文和 B2 的 diff 不调用 chat。其余请求的模型与温度只读登记。"""
    built = build_prompt(request)
    arm = str(built["arm"])
    phase = str(built["phase"])
    prompt = str(built["prompt"])
    result: dict[str, Any] = {
        "sent": False,
        "arm": arm,
        "phase": phase,
        "claim_id": request.get("claim_id"),
    }
    if (arm == "B2" and phase == "diff") or prompt == "":
        return result
    model = DEFAULT_MODEL
    temperature = MODEL_REGISTRY["default_llm"].temperature
    text = chat(prompt, model=model, temperature=temperature)
    field = str(built["output_field"])
    result["sent"] = True
    result["output_field"] = field
    result["model"] = model
    result["temperature"] = temperature
    result[field] = "" if text is None else str(text)
    return result


def generation_record(result: Mapping[str, Any]) -> dict[str, Any]:
    """只留下回文和实际使用的模型、温度。不带密钥，不带提示词里没有的请求字段。"""
    field = str(result["output_field"])
    return {
        "claim_id": result["claim_id"],
        "arm": result["arm"],
        "phase": result["phase"],
        "output_field": field,
        "text": result[field],
        "model": result["model"],
        "temperature": result["temperature"],
    }


def written_keys(path: Path) -> set[tuple[str, str, str]]:
    """文件里已经有的 claim_id、arm、phase。文件不存在则是空集。"""
    if not path.is_file():
        return set()
    keys: set[tuple[str, str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        keys.add((str(item["claim_id"]), str(item["arm"]), str(item["phase"])))
    return keys


def _saved_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def b2_claim_text(path: Path) -> dict[str, str]:
    """已经写下的 B2 claim。键是 claim_id，值是 claim 行的文本。"""
    found: dict[str, str] = {}
    for item in _saved_records(path):
        if item.get("arm") != "B2" or item.get("phase") != "claim":
            continue
        if item.get("output_field") != "claim_text":
            continue
        found[str(item["claim_id"])] = str(item.get("text") or "")
    return found


def b2_diff_written(path: Path) -> set[str]:
    """已经有 B2 diff 且输出字段是 after_text 的 claim_id。"""
    found: set[str] = set()
    for item in _saved_records(path):
        if item.get("arm") != "B2" or item.get("phase") != "diff":
            continue
        if item.get("output_field") != "after_text":
            continue
        found.add(str(item["claim_id"]))
    return found


def dispatch_b2_diff(
    request: Mapping[str, Any],
    chat: Callable[..., Any],
) -> dict[str, Any]:
    """B2 diff 正文为空则不调用 chat。回文写入 after_text，不抄 claim_text。"""
    built = build_prompt(request)
    result: dict[str, Any] = {
        "sent": False,
        "arm": str(built["arm"]),
        "phase": str(built["phase"]),
        "claim_id": request.get("claim_id"),
    }
    prompt = str(built.get("prompt") or "")
    if result["arm"] != "B2" or result["phase"] != "diff" or prompt == "":
        return result
    model = DEFAULT_MODEL
    temperature = MODEL_REGISTRY["default_llm"].temperature
    text = chat(prompt, model=model, temperature=temperature)
    result["sent"] = True
    result["output_field"] = "after_text"
    result["model"] = model
    result["temperature"] = temperature
    result["after_text"] = "" if text is None else str(text)
    return result


def append_b2_diffs(
    rows: Sequence[Mapping[str, Any]],
    path: Path,
    chat: Callable[..., Any],
) -> int:
    """只为已有 B2 claim 的 claim_id 补 diff。写完并 flush 之后才发下一条。"""
    claims = b2_claim_text(path)
    done = b2_diff_written(path)
    wrote = 0
    for row in rows:
        claim_id = str(row["claim_id"])
        if claim_id not in claims or claim_id in done:
            continue
        result = dispatch_b2_diff(
            {
                "arm": "B2",
                "phase": "diff",
                "claim_id": claim_id,
                "before_text": row["before_text"],
                "evidence_text": row["evidence_text"],
                "claim_text": claims[claim_id],
            },
            chat,
        )
        if append_sent(path, result):
            done.add(claim_id)
            wrote += 1
    return wrote


def append_sent(path: Path, result: Mapping[str, Any]) -> bool:
    """未发送的结果不写行。写完并落到磁盘后才返回。"""
    if not result.get("sent"):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(generation_record(result), ensure_ascii=False)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def live_chat(prompt: str, *, model: str, temperature: float) -> str:
    """用用户角色消息发送已拼好的正文。密钥只留在传输层，不在这里读取或打印。"""
    from freshlatch.llm import DecodingParams, LLMClient

    message = LLMClient().chat(
        [{"role": "user", "content": prompt}],
        decoding=DecodingParams(model=model, temperature=temperature),
    )
    content = getattr(message, "content", "")
    return "" if content is None else str(content)
