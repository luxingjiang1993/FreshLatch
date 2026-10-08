"""PE-06：三家外部评委的请求、作废、日志和 κ。

传输沿用 OpenAI 兼容 chat.completions。评委不使用生成默认模型。
temperature 按评委登记。服务端拒绝该参数、回显温度与登记值不一致、回显 model 与锁定字符串不一致，
或拒绝关闭思考，则该评委整次运行作废，不改温度、不换模型。
密钥只在真实传输里从环境变量读取，不写入日志。
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from freshlatch.models import MODEL_REGISTRY

RUBRIC = (
    "你是修改核对员。你只回答两个问题，不给修改建议，不评价文风。\n"
    "问题A：修改后的陈述与所附证据是否一致？只回答是或否。\n"
    "问题B：所附证据能否支撑这次修改？只回答是或否。\n"
    "证据缺失时，两题都答否。\n"
    "输出一行 JSON，形如 {\"A\":\"是\",\"B\":\"否\"}。A 和 B 只能是「是」或「否」。\n"
    "不要输出其他文字。"
)

_LABELS = ("是", "否")
_QUESTIONS = ("A", "B")
JUDGE_IDS = ("qwen", "deepseek", "kimi")
_PAIRS = (("qwen", "deepseek"), ("qwen", "kimi"), ("deepseek", "kimi"))


@dataclass(frozen=True)
class JudgeSpec:
    judge_id: str
    name: str
    model: str
    env_key: str
    base_url: str
    temperature: float
    thinking: dict[str, str] | None
    forbidden_models: frozenset[str]


def _judge_binding(purpose: str) -> tuple[str, str, str, frozenset[str], float]:
    entry = MODEL_REGISTRY[purpose]
    if not entry.base_url or not entry.env_key or entry.temperature is None:
        raise RuntimeError(f"{purpose} 缺少 base_url、env_key 或 temperature")
    return (
        entry.model,
        entry.env_key,
        entry.base_url,
        entry.forbidden_models,
        entry.temperature,
    )


_QWEN_MODEL, _QWEN_ENV, _QWEN_URL, _QWEN_FORBIDDEN, _QWEN_TEMPERATURE = _judge_binding(
    "judge_qwen"
)
(
    _DEEPSEEK_MODEL,
    _DEEPSEEK_ENV,
    _DEEPSEEK_URL,
    _DEEPSEEK_FORBIDDEN,
    _DEEPSEEK_TEMPERATURE,
) = _judge_binding("judge_deepseek")
_KIMI_MODEL, _KIMI_ENV, _KIMI_URL, _KIMI_FORBIDDEN, _KIMI_TEMPERATURE = _judge_binding(
    "judge_kimi"
)

JUDGES: dict[str, JudgeSpec] = {
    "qwen": JudgeSpec(
        judge_id="qwen",
        name="Qwen2.5-72B",
        model=_QWEN_MODEL,
        env_key=_QWEN_ENV,
        base_url=_QWEN_URL,
        temperature=_QWEN_TEMPERATURE,
        thinking=None,
        forbidden_models=_QWEN_FORBIDDEN,
    ),
    "deepseek": JudgeSpec(
        judge_id="deepseek",
        name="DeepSeek-V3",
        model=_DEEPSEEK_MODEL,
        env_key=_DEEPSEEK_ENV,
        base_url=_DEEPSEEK_URL,
        temperature=_DEEPSEEK_TEMPERATURE,
        thinking={"type": "disabled"},
        forbidden_models=_DEEPSEEK_FORBIDDEN,
    ),
    "kimi": JudgeSpec(
        judge_id="kimi",
        name="Kimi",
        model=_KIMI_MODEL,
        env_key=_KIMI_ENV,
        base_url=_KIMI_URL,
        temperature=_KIMI_TEMPERATURE,
        thinking={"type": "disabled"},
        forbidden_models=_KIMI_FORBIDDEN,
    ),
}


class MissingAPIKey(RuntimeError):
    """真实传输缺少对应环境变量。"""


def default_log_dir() -> Path:
    """正式日志目录。调用前不创建。"""
    return Path(__file__).resolve().parents[3] / "data" / "exp" / "patch-events" / "judge-logs"


def build_user_message(before: str, after: str, evidence_text: str, evidence_id: str) -> str:
    """用户消息只含修改前、修改后、证据原文、evidence id。"""
    return (
        "修改前：\n"
        f"{before}\n"
        "\n"
        "修改后：\n"
        f"{after}\n"
        "\n"
        "证据原文：\n"
        f"{evidence_text}\n"
        "\n"
        "evidence id：\n"
        f"{evidence_id}"
    )


def parse_labels(raw: str) -> dict[str, str] | None:
    """一行 JSON，A 和 B 只能是「是」或「否」。失败返回 None，不记成否。"""
    text = raw.strip()
    if not text or "\n" in text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or set(data) != {"A", "B"}:
        return None
    if data["A"] not in _LABELS or data["B"] not in _LABELS:
        return None
    return {"A": data["A"], "B": data["B"]}


def _prompt_sha256(user: str) -> str:
    return hashlib.sha256(f"{RUBRIC}\n{user}".encode("utf-8")).hexdigest()


def _temperature_echo_mismatch(expected: float, actual: object) -> bool:
    """没回显温度不算不符。回显了但不是登记值，则作废。"""
    if actual is None:
        return False
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        return True
    return float(actual) != float(expected)


def _refusal_reason(exc: BaseException) -> str | None:
    text = str(exc)
    lowered = text.lower()
    if "temperature" in lowered:
        return "temperature"
    if "thinking" in lowered or "思考" in text:
        return "thinking"
    return None


def _void_reason(spec: JudgeSpec, result: Mapping[str, Any]) -> str | None:
    refused = result.get("refused")
    if refused in ("temperature", "thinking"):
        return str(refused)
    if result.get("model") != spec.model:
        return "response_model"
    if _temperature_echo_mismatch(spec.temperature, result.get("temperature")):
        return "temperature"
    if spec.thinking is not None:
        echoed = result.get("thinking")
        if echoed is not None and echoed != spec.thinking:
            return "thinking"
    return None


def _invoke(transport: Callable[[Mapping[str, Any]], Mapping[str, Any]], request: Mapping[str, Any]) -> dict[str, Any]:
    try:
        result = transport(request)
    except Exception as exc:
        reason = _refusal_reason(exc)
        if reason is None:
            raise
        return {
            "model": None,
            "temperature": None,
            "thinking": None,
            "content": "",
            "usage": None,
            "refused": reason,
        }
    return dict(result)


def real_transport(request: Mapping[str, Any]) -> dict[str, Any]:
    """OpenAI 兼容传输。测试注入替身，不在单测里打到真实端点。"""
    from dotenv import find_dotenv, load_dotenv
    from openai import OpenAI

    load_dotenv(find_dotenv(usecwd=True))
    key = os.getenv(str(request["env_key"]), "")
    if not key:
        raise MissingAPIKey(str(request["env_key"]))
    client = OpenAI(api_key=key, base_url=str(request["base_url"]), max_retries=0)
    kwargs: dict[str, Any] = {
        "model": request["model"],
        "messages": request["messages"],
        "temperature": request["temperature"],
    }
    thinking = request.get("thinking")
    try:
        if thinking is not None:
            response = client.chat.completions.create(**kwargs, extra_body={"thinking": thinking})
        else:
            response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        reason = _refusal_reason(exc)
        if reason is None:
            raise
        return {
            "model": None,
            "temperature": None,
            "thinking": None,
            "content": "",
            "usage": None,
            "refused": reason,
        }
    usage = getattr(response, "usage", None)
    usage_dict = None
    if usage is not None:
        usage_dict = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
    message = response.choices[0].message
    return {
        "model": getattr(response, "model", None),
        "temperature": getattr(response, "temperature", None),
        "thinking": getattr(response, "thinking", None),
        "content": getattr(message, "content", None) or "",
        "usage": usage_dict,
        "refused": None,
    }


def _status_code(exc: BaseException) -> int | None:
    """只留整数状态码。不读异常正文，也不读 headers。"""
    code = getattr(exc, "status_code", None)
    if type(code) is int:
        return code
    return None


def _call_record(
    spec: JudgeSpec,
    digest: str,
    elapsed: float,
    *,
    response_model: object,
    usage: object,
    content: str,
    parsed: dict[str, str] | None,
    error_type: str | None = None,
    status_code: int | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "时间": datetime.now(timezone.utc).isoformat(),
        "请求的 model": spec.model,
        "响应回显的 model": response_model,
        "请求的 temperature": spec.temperature,
        "思考开关": spec.thinking,
        "usage": usage,
        "提示的 sha256": digest,
        "原始输出": content,
        "解析结果": parsed,
        "延迟": elapsed,
    }
    if error_type is not None:
        record["错误类型"] = error_type
        record["状态码"] = status_code
    return record


def _append_log(logs_dir: Path, judge_id: str, record: Mapping[str, Any]) -> None:
    path = logs_dir / f"{judge_id}.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _request(spec: JudgeSpec, user: str) -> dict[str, Any]:
    return {
        "judge_id": spec.judge_id,
        "model": spec.model,
        "temperature": spec.temperature,
        "thinking": spec.thinking,
        "messages": [
            {"role": "system", "content": RUBRIC},
            {"role": "user", "content": user},
        ],
        "base_url": spec.base_url,
        "env_key": spec.env_key,
    }


def _label(row: Mapping[str, Any], judge_id: str, question: str) -> str | None:
    block = row.get(judge_id)
    if not isinstance(block, dict):
        return None
    value = block.get(question)
    if value in _LABELS:
        return str(value)
    return None


def _as_float(value: Fraction) -> float:
    """分数算完再转浮点，避免 3.11 与 3.12 的中间除法末位不同。"""
    return float(value)


def _cohen(pairs: list[tuple[str, str]]) -> dict[str, Any]:
    n = len(pairs)
    if n == 0:
        return {"kappa": None, "n": 0}
    agreed = sum(left == right for left, right in pairs)
    observed = Fraction(agreed, n)
    expected = Fraction(0)
    for label in _LABELS:
        left_rate = Fraction(sum(left == label for left, _right in pairs), n)
        right_rate = Fraction(sum(right == label for _left, right in pairs), n)
        expected += left_rate * right_rate
    if expected == 1:
        kappa = 1.0 if observed == 1 else None
    else:
        kappa = _as_float((observed - expected) / (1 - expected))
    return {"kappa": kappa, "n": n}


def _fleiss(rows: list[list[str]]) -> dict[str, Any]:
    n_items = len(rows)
    if n_items == 0:
        return {"kappa": None, "n": 0}
    n_raters = len(rows[0])
    item_agreement: list[Fraction] = []
    counts = {label: 0 for label in _LABELS}
    for row in rows:
        tally = {label: 0 for label in _LABELS}
        for label in row:
            tally[label] += 1
            counts[label] += 1
        sum_sq = sum(value * value for value in tally.values())
        item_agreement.append(Fraction(sum_sq - n_raters, n_raters * (n_raters - 1)))
    observed = sum(item_agreement, Fraction(0)) / n_items
    total = n_items * n_raters
    expected = sum((Fraction(counts[label], total) ** 2 for label in _LABELS), Fraction(0))
    if expected == 1:
        kappa = 1.0 if observed == 1 else None
    else:
        kappa = _as_float((observed - expected) / (1 - expected))
    return {"kappa": kappa, "n": n_items}


def agreement(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """按题分开的 Cohen 三对和 Fleiss。只读 qwen、deepseek、kimi。缺失不插补。"""
    report: dict[str, Any] = {}
    for question in _QUESTIONS:
        cohen = []
        for left, right in _PAIRS:
            pairs = []
            for row in rows:
                left_label = _label(row, left, question)
                right_label = _label(row, right, question)
                if left_label is not None and right_label is not None:
                    pairs.append((left_label, right_label))
            scored = _cohen(pairs)
            cohen.append({"pair": [left, right], **scored})
        complete = []
        for row in rows:
            labels = [_label(row, judge_id, question) for judge_id in JUDGE_IDS]
            if all(label is not None for label in labels):
                complete.append([label for label in labels if label is not None])
        report[question] = {"cohen": cohen, "fleiss": _fleiss(complete)}
    return report


def run_judges(
    items: Sequence[Mapping[str, Any]],
    *,
    transport: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    logs_dir: Path,
    judge_ids: Sequence[str] = JUDGE_IDS,
) -> dict[str, Any]:
    """逐评委、逐条调用。解析失败只再请求一次。作废则丢掉该评委已有标签。"""
    directory = Path(logs_dir)
    directory.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    ordered: list[Mapping[str, Any]] = []
    for item in items:
        claim_id = str(item["claim_id"])
        if claim_id in seen:
            raise ValueError(f"claim_id 重复: {claim_id}")
        seen.add(claim_id)
        ordered.append(item)

    judges_out: dict[str, dict[str, Any]] = {}
    for judge_id in judge_ids:
        spec = JUDGES[judge_id]
        labels: dict[str, dict[str, str | None]] = {}
        void = False
        void_reason = ""
        for item in ordered:
            user = build_user_message(
                str(item["before_text"]),
                str(item["after_text"]),
                str(item["evidence_text"]),
                str(item["evidence_id"]),
            )
            request = _request(spec, user)
            digest = _prompt_sha256(user)
            parsed: dict[str, str] | None = None
            for _attempt in range(2):
                started = time.perf_counter()
                try:
                    result = _invoke(transport, request)
                except Exception as exc:
                    _append_log(
                        directory,
                        judge_id,
                        _call_record(
                            spec,
                            digest,
                            time.perf_counter() - started,
                            response_model=None,
                            usage=None,
                            content="",
                            parsed=None,
                            error_type=type(exc).__name__,
                            status_code=_status_code(exc),
                        ),
                    )
                    raise
                elapsed = time.perf_counter() - started
                reason = _void_reason(spec, result)
                parsed = None if reason else parse_labels(str(result.get("content") or ""))
                _append_log(
                    directory,
                    judge_id,
                    _call_record(
                        spec,
                        digest,
                        elapsed,
                        response_model=result.get("model"),
                        usage=result.get("usage"),
                        content=str(result.get("content") or ""),
                        parsed=parsed,
                    ),
                )
                if reason:
                    void = True
                    void_reason = reason
                    labels = {}
                    break
                if parsed is not None:
                    break
            if void:
                break
            claim_id = str(item["claim_id"])
            if parsed is None:
                labels[claim_id] = {"A": None, "B": None}
            else:
                labels[claim_id] = parsed
        judges_out[judge_id] = {
            "model": spec.model,
            "void": void,
            "void_reason": void_reason,
            "labels": labels,
        }

    rows = []
    for item in ordered:
        claim_id = str(item["claim_id"])
        row: dict[str, Any] = {"claim_id": claim_id}
        for judge_id in JUDGE_IDS:
            block = judges_out.get(judge_id)
            if block is None or block["void"]:
                row[judge_id] = {"A": None, "B": None}
            else:
                row[judge_id] = block["labels"].get(claim_id, {"A": None, "B": None})
        rows.append(row)
    return {"judges": judges_out, "kappa": agreement(rows)}
