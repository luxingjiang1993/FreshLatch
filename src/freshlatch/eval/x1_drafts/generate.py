"""generate 子命令：按 spec 分批调用模型并写入 --out。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from freshlatch.eval.x1_drafts._lookup import _pkg_attr
from freshlatch.eval.x1_drafts.batch import (
    _batch_fingerprint,
    _cost_cny,
    _decoding_fields,
    _estimate_spec,
    _format_estimate,
    _input_token_upper,
    _load_spec,
    _output_token_upper,
    _parse_max_cny,
    _parse_pricing,
)
from freshlatch.eval.x1_drafts.constants import (
    CONSECUTIVE_VALIDATION_LIMIT,
    DECODING_MISMATCH,
    DRAFT_MODEL,
    PUBLIC_CORPUS,
    PUBLIC_TRAPS,
    RAW_GOLD_NOTE,
)
from freshlatch.eval.x1_drafts.documents import (
    _load_out_questions,
    _prefix_question_ids,
    _question_as_of_error,
    _question_ids,
    _scan_doc_keys,
    _split_frontmatter,
    _validate_batch_documents,
)
from freshlatch.eval.x1_drafts.io import _write_manifest
from freshlatch.eval.x1_drafts.ledger import (
    _commit_batch,
    _discard_committing,
    _discard_open_commits,
    _drop_committing_question_ids,
    _finite_money,
    _flush_manifest,
    _load_manifest,
    _manifest_anomaly,
    _public_doc_ids,
    _resume_action,
    _usage_pair,
)
from freshlatch.eval.x1_drafts.paths import DraftShapeError, _can_overwrite_out
from freshlatch.eval.x1_drafts.shape import (
    _load_config,
    _normalize_generate_payload,
    _parse_json_content,
    _print_checker,
    _require_draft_decoding,
)
from freshlatch.llm import DecodingParams, LLMClient

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
    """先经 LLMClient.client 拿到真实 SDK，再钉 max_tokens、关思考、max_retries=0。

    构造 OpenAI 客户端本身不发 HTTP。假客户端没有 client 属性时保持原样。
    """
    if isinstance(llm, LLMClient):
        inner = llm.client
    else:
        inner = getattr(llm, "_client", None)
    if inner is None:
        return None
    inner.max_retries = 0
    completions = inner.chat.completions
    current = completions.create
    if isinstance(current, _NoThinkingCreate):
        current.limits = limits
        return current
    wrapper = _NoThinkingCreate(current, limits)
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
    _pkg_attr("_atomic_write_text")(out / "raw-response.txt", raw_text)
    if batch_id:
        _pkg_attr("_atomic_write_text")(out / "raw" / f"{batch_id}.txt", raw_text)
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
        print(_format_estimate(estimated, max_cny), end="")
        if estimated["cny"] + estimated["flag_cny"] > max_cny:
            return 1
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
    if "spent_cny" in prev:
        spent_loaded = _finite_money(prev.get("spent_cny"))
        if spent_loaded is None or spent_loaded < 0:
            print("错误: 清单异常: spent_cny", file=sys.stderr)
            return 1
    else:
        spent_loaded = 0.0
    anomaly = _manifest_anomaly(prev_batches, spent_loaded)
    if anomaly:
        print(f"错误: {anomaly}", file=sys.stderr)
        return 1
    for rec in prev_batches.values():
        if isinstance(rec, dict) and rec.get("status") == "inflight":
            # 中断预扣留在 spent_cny 里，包括清单里已经没有的批次。清掉 inflight 后，这次调用按新的上界再扣。
            rec["status"] = "sunk"
    plans: list[tuple[dict[str, Any], str, dict[str, Any], str]] = []
    for batch in spec["batches"]:
        prompt = _pkg_attr("_build_batch_prompt")(batch)
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
    rolled = _drop_committing_question_ids(out, prev_batches, loaded_questions)
    if isinstance(rolled, str):
        print(f"错误: {rolled}", file=sys.stderr)
        return 1
    queries = rolled
    discard_err = _discard_open_commits(out, prev_batches)
    if discard_err:
        print(f"错误: {discard_err}", file=sys.stderr)
        return 1
    seen_ids: set[str] = set()
    for item in queries:
        qid = item.get("id")
        if isinstance(qid, str):
            seen_ids.add(qid)
    public_ids = _public_doc_ids()
    if isinstance(public_ids, str):
        print(f"错误: {public_ids}", file=sys.stderr)
        return 1
    seen_docs = _scan_doc_keys([out])
    if isinstance(seen_docs, str):
        print(f"错误: {seen_docs}", file=sys.stderr)
        return 1
    public_keys = _scan_doc_keys([PUBLIC_CORPUS, PUBLIC_TRAPS], public_only=True)
    if isinstance(public_keys, str):
        print(f"错误: {public_keys}", file=sys.stderr)
        return 1
    seen_docs |= public_keys
    prev_usage = prev.get("token_usage") if isinstance(prev.get("token_usage"), dict) else {}
    decoding = DecodingParams(model=draft_model, temperature=temperature, seed=seed)
    state: dict[str, Any] = {
        "model": draft_model,
        "temperature": temperature,
        "seed": seed,
        "recorded_at": prev.get("recorded_at") or decoding.recorded_at,
        "batches": {key: dict(val) for key, val in prev_batches.items() if isinstance(val, dict)},
        "spent_cny": spent_loaded,
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

    validation_streak = 0

    def _stop_if_validation_streak() -> bool:
        nonlocal validation_streak
        validation_streak += 1
        if validation_streak < CONSECUTIVE_VALIDATION_LIMIT:
            return False
        state["stop_reason"] = "consecutive_validation"
        _flush_manifest(out, state)
        print(f"错误: 连续 {CONSECUTIVE_VALIDATION_LIMIT} 批校验失败，停止", file=sys.stderr)
        return True

    for batch, prompt, fields, fingerprint in plans:
        batch_id = batch["batch_id"]
        action = _resume_action({"batches": state["batches"]}, batch, fields, fingerprint)
        if action == "skip":
            validation_streak = 0
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
        if state["spent_cny"] < 0:
            print("错误: 清单异常: spent_cny", file=sys.stderr)
            return 1
        held_in, held_out, held_cny = upper_in, upper_out, upper_cny
        _apply_usage(held_in, held_out, held_cny)
        _put_batch(
            batch_id,
            fields,
            fingerprint,
            status="inflight",
            error=None,
            cost_cny=held_cny,
            prompt_tokens=held_in,
            completion_tokens=held_out,
        )
        _flush_manifest(out, state)
        client = _client()
        _arm(client, upper_out)
        before_prompt, before_completion = _usage_pair(client)
        try:
            message = client.chat(
                [{"role": "user", "content": prompt}],
                decoding=decoding,
            )
        except KeyboardInterrupt:
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: 调用被中断", file=sys.stderr)
            return 130
        except Exception as exc:
            line = str(exc).strip().splitlines()
            detail = line[0] if line else type(exc).__name__
            _put_batch(
                batch_id,
                fields,
                fingerprint,
                status="failed",
                error=detail,
                cost_cny=held_cny,
                prompt_tokens=held_in,
                completion_tokens=held_out,
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
            _put_batch(
                batch_id,
                fields,
                fingerprint,
                status="failed",
                error="用量缺失或为 0",
                cost_cny=held_cny,
                prompt_tokens=held_in,
                completion_tokens=held_out,
            )
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: 用量缺失或为 0", file=sys.stderr)
            return 1
        cost = _cost_cny(delta_prompt, delta_completion, in_price, out_price)
        settled_spent = state["spent_cny"] + cost - held_cny
        if settled_spent < 0:
            print("错误: 清单异常: spent_cny", file=sys.stderr)
            return 1
        state["spent_cny"] = settled_spent
        usage = state["token_usage"]
        usage["prompt_tokens"] += delta_prompt - held_in
        usage["completion_tokens"] += delta_completion - held_out
        usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
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
        if delta_prompt > upper_in or delta_completion > upper_out:
            state["batches"][batch_id]["error"] = "usage_over_upper"
            state["stop_reason"] = "usage_over_upper"
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: usage_over_upper", file=sys.stderr)
            return 1
        if _finish_reason(message) == "length":
            state["batches"][batch_id]["error"] = "finish_reason=length"
            _flush_manifest(out, state)
            print(f"错误: 批次 {batch_id}: finish_reason=length", file=sys.stderr)
            return 1
        try:
            parsed = _parse_json_content(raw_text)
        except json.JSONDecodeError as exc:
            _fail_batch(batch_id, raw_text, f"模型输出不是 JSON: {exc}", fields, fingerprint)
            if _stop_if_validation_streak():
                break
            continue
        try:
            payload = _normalize_generate_payload(parsed)
        except DraftShapeError as exc:
            _fail_batch(batch_id, raw_text, str(exc), fields, fingerprint)
            if _stop_if_validation_streak():
                break
            continue
        doc_err = _validate_batch_documents(payload["documents"], batch, seen_docs, out, public_ids)
        if doc_err:
            _fail_batch(batch_id, raw_text, doc_err, fields, fingerprint)
            if _stop_if_validation_streak():
                break
            continue
        queries_now = payload["questions"]["queries"]
        as_of_err = _question_as_of_error(queries_now)
        if as_of_err:
            _fail_batch(batch_id, raw_text, as_of_err, fields, fingerprint)
            if _stop_if_validation_streak():
                break
            continue
        _prefix_question_ids(queries_now, batch_id)
        id_result = _question_ids(queries_now, seen_ids)
        if isinstance(id_result, str):
            _fail_batch(batch_id, raw_text, id_result, fields, fingerprint)
            if "冲突" in id_result:
                state["stop_reason"] = "id_conflict"
                break
            if _stop_if_validation_streak():
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
            if _stop_if_validation_streak():
                break
            continue
        validation_streak = 0
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
            question_ids=list(id_result),
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
            result = _pkg_attr("check_x1")(out / "corpus", out / "traps", qpath, cfg_path)
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
