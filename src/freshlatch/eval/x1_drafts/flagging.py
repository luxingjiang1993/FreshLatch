"""flag 子命令：qwen-plus 非思考抽检。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from freshlatch.eval.x1_drafts._lookup import _pkg_attr
from freshlatch.eval.x1_drafts.batch import (
    _cost_cny,
    _flag_output_upper,
    _flag_skeleton,
    _input_token_upper,
    _parse_max_cny,
    _parse_pricing_block,
)
from freshlatch.eval.x1_drafts.constants import (
    FLAG_LEDGER_NAME,
    FLAG_MODEL,
    MODEL_MAX_OUTPUT_TOKENS,
    SIDECAR_MARKER,
)
from freshlatch.eval.x1_drafts.generate import _pin_create
from freshlatch.eval.x1_drafts.ledger import (
    _finite_money,
    _held_charge_error,
    _spend_below_recorded,
    _usage_pair,
)
from freshlatch.eval.x1_drafts.paths import _can_write_sidecar, is_forbidden_sidecar
from freshlatch.eval.x1_drafts.shape import _load_config, _parse_json_content, _whitelist_notes
from freshlatch.llm import DecodingParams, LLMClient

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




def _flag_input_dir(inp: Path) -> Path:
    return inp if inp.is_dir() else inp.parent


def _flag_ledger_path(inp: Path) -> Path:
    return _flag_input_dir(inp) / FLAG_LEDGER_NAME


def _read_flag_ledger(inp: Path) -> tuple[float, float, bool] | str:
    """返回 (spent_cny, held_cny, inflight)。inflight 时 held 已计入 spent。"""
    path = _flag_ledger_path(inp)
    if not path.exists():
        return 0.0, 0.0, False
    if not path.is_file():
        return "抽检花费账本不是文件"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return f"抽检花费账本无法解析: {exc}"
    if not isinstance(data, dict):
        return "抽检花费账本无法解析"
    if "inflight" in data and data.get("inflight") is not True and data.get("inflight") is not False:
        return "清单异常: inflight"
    spent = _finite_money(data.get("spent_cny", 0.0))
    if spent is None or spent < 0:
        return "清单异常: spent_cny"
    inflight = data.get("inflight") is True
    held = 0.0
    if inflight:
        held_value = _finite_money(data.get("held_cny"))
        if held_value is None:
            return "清单异常: held_cny"
        held = held_value
    return spent, held, inflight


def _write_flag_ledger(inp: Path, spent: float, *, held_cny: float | None = None) -> None:
    path = _flag_ledger_path(inp)
    if is_forbidden_sidecar(path):
        raise OSError("抽检花费账本落在禁写目录")
    body: dict[str, Any] = {"spent_cny": spent}
    if held_cny is not None:
        body["inflight"] = True
        body["held_cny"] = held_cny
    _pkg_attr("_atomic_write_text")(path, json.dumps(body, ensure_ascii=False, indent=2) + "\n")


def _write_flag_payload(sidecar: Path, payload: dict[str, Any]) -> None:
    _pkg_attr("_atomic_write_text")(sidecar, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


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
    inp = Path(args.inp)
    if is_forbidden_sidecar(_flag_ledger_path(inp)):
        print("错误: 抽检花费账本不得落在禁写目录", file=sys.stderr)
        return 1
    questions = _load_flag_questions(inp)
    slim = [{"id": q.get("id"), "query": q.get("query")} for q in questions]
    prompt = _flag_prompt(slim)
    upper_in = _input_token_upper(prompt)
    upper_out = _flag_output_upper(len(slim))
    flag_limit = MODEL_MAX_OUTPUT_TOKENS[FLAG_MODEL]
    if upper_out > flag_limit:
        print(
            f"错误: 抽检输出上界 {upper_out} 超过 {FLAG_MODEL} 上限 {flag_limit}，请减少题目后再抽检",
            file=sys.stderr,
        )
        return 1
    upper_cny = _cost_cny(upper_in, upper_out, in_price, out_price)
    loaded = _read_flag_ledger(inp)
    if isinstance(loaded, str):
        print(f"错误: {loaded}", file=sys.stderr)
        return 1
    spent, held, inflight = loaded
    if inflight:
        charge_err = _held_charge_error(spent, held, held_field="held_cny")
        if charge_err:
            print(f"错误: {charge_err}", file=sys.stderr)
            return 1
    # 抽检账本没有逐批记录。inflight 时已记成本就是 held_cny，花费不得低于它。
    cover_err = _spend_below_recorded(spent, held if inflight else 0.0)
    if cover_err:
        print(f"错误: {cover_err}", file=sys.stderr)
        return 1
    if inflight:
        # 旧的预扣留下，清掉 inflight 后再按这次调用重新预扣。
        _write_flag_ledger(inp, spent)
    if spent + upper_cny > max_cny:
        print("错误: 累计花费已达 --max-cny，停止后续批次", file=sys.stderr)
        return 1
    client = llm_client or LLMClient()
    limits: dict[str, Any] = {"max_tokens": upper_out}
    wrapper = _pin_create(client, limits)
    flag_temperature = 0.0
    decoding = DecodingParams(model=FLAG_MODEL, temperature=flag_temperature)

    def _record(
        status: str,
        error: str | None,
        spent_now: float,
        notes: Any,
        *,
        held_cny: float | None = None,
    ) -> None:
        _write_flag_ledger(inp, spent_now, held_cny=held_cny)
        payload: dict[str, Any] = {
            SIDECAR_MARKER: True,
            "model": FLAG_MODEL,
            "flag_thinking": False,
            "temperature": flag_temperature,
            "status": status,
            "spent_cny": spent_now,
            "max_cny": max_cny,
            "pricing_source": price_source,
            "notes": notes,
        }
        if error is not None:
            payload["error"] = error
        _write_flag_payload(sidecar, payload)

    held = upper_cny
    charged = spent + upper_cny
    if charged < 0:
        print("错误: 清单异常: spent_cny", file=sys.stderr)
        return 1
    _record("inflight", None, charged, [], held_cny=held)
    before_prompt, before_completion = _usage_pair(client)
    try:
        message = client.chat(
            [{"role": "user", "content": prompt}],
            decoding=decoding,
        )
    except KeyboardInterrupt:
        print("错误: 抽检调用被中断", file=sys.stderr)
        return 130
    except Exception as exc:
        line = str(exc).strip().splitlines()
        detail = line[0] if line else type(exc).__name__
        _record("failed", detail, charged, [])
        print(f"错误: 抽检调用失败: {detail}", file=sys.stderr)
        return 1
    after_prompt, after_completion = _usage_pair(client)
    delta_prompt = max(0, after_prompt - before_prompt)
    delta_completion = max(0, after_completion - before_completion)
    if delta_prompt == 0 and delta_completion == 0:
        _record("failed", "用量缺失或为 0", charged, [])
        print("错误: 抽检用量缺失或为 0", file=sys.stderr)
        return 1
    cost = _cost_cny(delta_prompt, delta_completion, in_price, out_price)
    settled = charged - held + cost
    if settled < 0:
        print("错误: 清单异常: spent_cny", file=sys.stderr)
        return 1
    if delta_prompt > upper_in or delta_completion > upper_out:
        _record("failed", "usage_over_upper", settled, [])
        print("错误: 抽检 usage_over_upper", file=sys.stderr)
        return 1
    finish = None
    if wrapper is not None and wrapper.last_finish_reason:
        finish = wrapper.last_finish_reason
    else:
        value = getattr(message, "finish_reason", None)
        if isinstance(value, str):
            finish = value
    if finish == "length":
        _record("failed", "finish_reason=length", settled, [])
        print("错误: 抽检 finish_reason=length", file=sys.stderr)
        return 1
    try:
        notes = _parse_json_content(getattr(message, "content", "") or "")
    except json.JSONDecodeError:
        notes = {"suspicion": getattr(message, "content", "") or ""}
    notes = _whitelist_notes(notes)
    _record("ok", None, settled, notes)
    return 0
