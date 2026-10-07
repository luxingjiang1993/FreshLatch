"""批次校验、提示词、预算上界与花费估算。"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from freshlatch.eval.x1_drafts._lookup import _pkg_attr
from freshlatch.eval.x1_drafts.constants import (
    BATCH_AS_OF,
    BATCH_DOMAINS,
    BATCH_GENRES,
    DRAFT_MODEL,
    EST_OUTPUT_TOKENS_PER_CHUNK,
    EST_OUTPUT_TOKENS_PER_DOC,
    EST_OUTPUT_TOKENS_PER_QUESTION,
    FLAG_MODEL,
    MODEL_MAX_OUTPUT_TOKENS,
    P2_MODEL_REFUSAL,
    _BATCH_ID_RE,
    _RESERVED_BATCH_RE,
)
from freshlatch.eval.x1_drafts.shape import _decoding_number

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
    if _RESERVED_BATCH_RE.match(batch_id):
        return f"batches[{index}] batch_id 前缀 p1/p2 保留给手写公开文档"
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
    upper = _output_token_upper(batch)
    limit = MODEL_MAX_OUTPUT_TOKENS[DRAFT_MODEL]
    if upper > limit:
        return (
            f"batches[{index}] {batch['batch_id']} 输出上界 {upper} 超过 {DRAFT_MODEL} 上限 {limit}，请拆分该批"
        )
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
    slots = sum(_question_allowance(batch) for batch in batches)
    flag_limit = MODEL_MAX_OUTPUT_TOKENS[FLAG_MODEL]
    flag_upper = _flag_output_upper(slots)
    if flag_upper > flag_limit:
        return f"抽检输出上界 {flag_upper} 超过 {FLAG_MODEL} 上限 {flag_limit}，请减少题目后再抽检"
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


def _chunk_count_line(n: int) -> str:
    return f"每篇 content 正文恰好 {n} 段，标题依次为 `## p1` … `## p{n}`，不多不少。"


def _example_sections(n: int) -> str:
    """示例正文段数与该批 chunks_per_doc 一致。"""
    lines: list[str] = []
    for index in range(1, n + 1):
        lines.append(f"## p{index}")
        lines.append("合成正文。" if index == 1 else "另一段。")
    return "\n".join(lines) + "\n"


def _prompt_document_example(batch: dict[str, Any]) -> str:
    """示例用本批的目录、genre、as_of 和 batch_id，文件名等于 doc_id.md，段数等于 chunks_per_doc。"""
    as_of = "T1" if _is_pair(batch) else batch["as_of"]
    doc_id = f"{batch['batch_id']}-memo"
    path = f"{_expected_rel_dir(batch['genre'], as_of)}/{doc_id}.md"
    n = int(batch["chunks_per_doc"])
    content = (
        f"---\n"
        f"doc_id: {doc_id}\n"
        f"as_of: {as_of}\n"
        f"source_type: private\n"
        f"title: 示例\n"
        f"provenance: synthetic\n"
        f"license: synthetic\n"
        f"domain: {batch['domain']}\n"
        f"genre: {batch['genre']}\n"
        f"---\n"
        f"{_example_sections(n)}"
    )
    return json.dumps({"path": path, "content": content}, ensure_ascii=False, separators=(",", ":"))


def _build_batch_prompt(batch: dict[str, Any]) -> str:
    """拼一批的用户提示。合成正文自写，不给金标，只要 JSON。must_include 原样塞进提示。"""
    pair = _is_pair(batch)
    n_chunks = int(batch["chunks_per_doc"])
    lines = [
        "生成 x1 实验的合成文档与题目草稿。",
        "合成正文必须自写，不得以版权原文为模板整段改写。",
        "不得给出金标。",
        "只返回 JSON。",
        "只返回 JSON 对象：documents 数组（元素只含 path 与 content），以及带 queries 数组的 questions 对象（必须使用 queries 包装）。",
        "每道题只给 id、query、category、eval_intent、as_of。题目的 as_of 只能是 T0 或 T1，不要写日期。",
        f"题目 id 必须形如 {batch['batch_id']}-q1。",
        f"本批 batch_id={batch['batch_id']}。",
        f"doc_id 必须匹配 ^{batch['batch_id']}-[a-z0-9-]+$。",
        f"genre={batch['genre']}，domain={batch['domain']}。",
        f"n_docs={batch['n_docs']}，每份文档 chunks_per_doc={batch['chunks_per_doc']} 个块。",
        f"topic：{batch['topic']}",
        "每份文档的 content 必须以 YAML frontmatter 开头：第一行 ---，接着每行一个「键: 值」，再一行 ---。不要另给 frontmatter 字段。",
        "frontmatter 必须包含 doc_id、as_of、source_type（只允许 private、public、internal）、title、provenance: synthetic、license: synthetic、domain、genre。",
        "t0/ 目录下 as_of 必须是 T0，t1/ 目录下 as_of 必须是 T1，禁止写成日期。",
        "license 只能是 synthetic。",
        _chunk_count_line(n_chunks),
        "块 id 形如 p1，不得重复，块正文不得为空。",
        "文件名必须是 <doc_id>.md。目录必须与 as_of 和 genre 一致。",
        "单份文档示例：" + _prompt_document_example(batch),
    ]
    if pair:
        bucket = "traps" if batch["genre"] == "S7" else "corpus"
        lines.append(
            "本批 pair=true：每个 doc_id 同时给出 T0 与 T1 两份文档，doc_id 相同，pN 顺序相同，T1 改写已陈述事实。"
        )
        lines.append(f"路径分别位于 {bucket}/t0/ 与 {bucket}/t1/ 下，只一层文件名，扩展名 .md。")
        lines.append(f"documents 长度必须等于 {int(batch['n_docs']) * 2}。")
        lines.append("同一 doc_id 的两份文档：t0/ 里 as_of 写 T0，t1/ 里 as_of 写 T1，不要写日期。")
        lines.append(f"T0 与 T1 各自的正文都恰好 {n_chunks} 段，标题依次为 `## p1` … `## p{n_chunks}`，不多不少。")
    else:
        dest = _expected_rel_dir(batch["genre"], batch["as_of"])
        lines.append(f"as_of={batch['as_of']}，不要写成日期。")
        lines.append(f"每份文档路径必须位于 {dest}/ 下，只一层文件名，扩展名 .md。")
    if batch["genre"] == "S7":
        lines.append("本批是检索陷阱文档，路径必须在 traps 下，不要写入 corpus。")
    if batch["genre"] == "S6":
        if batch["domain"] in {"D1", "D2"}:
            lines.append("本批复述监管变更要点，只写 must_include 里的事实，不得自拟法律门槛或日期。")
        else:
            lines.append("本批是变更要点与补丁记录，只写 must_include 里的合成事实，不要写法律门槛。")
        lines.append("段数要求不改 must_include：这些事实仍须原样写入，不得为了凑段数改写或删掉。")
        facts = batch.get("must_include")
        if isinstance(facts, list) and len(facts) == 1:
            lines.append(
                "p1 完整写出 must_include 事实；其余段只写背景、适用范围或影响说明，不得新增门槛、日期、金额或其他数字，也不要拆开或改写 must_include 事实。"
            )
        else:
            lines.append("不得新增门槛、日期、金额或其他数字，也不要拆开或改写 must_include 事实。")
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
    max_batch_output = 0
    for batch in spec["batches"]:
        input_tokens += _input_token_upper(_pkg_attr("_build_batch_prompt")(batch))
        batch_out = _output_token_upper(batch)
        output_tokens += batch_out
        max_batch_output = max(max_batch_output, batch_out)
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
        "max_batch_output_tokens": max_batch_output,
    }


def _format_estimate(est: dict[str, Any], max_cny: float) -> str:
    total = float(est["cny"]) + float(est["flag_cny"])
    budget = "ok" if total <= max_cny else "over"
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
        f"total_cny={total:.8f} 估\n"
        f"max_batch_output_tokens={est['max_batch_output_tokens']}\n"
        f"max_cny={max_cny:.8f}\n"
        f"budget={budget}\n"
    )

def _cost_cny(prompt_tokens: int, completion_tokens: int, in_price: float, out_price: float) -> float:
    return prompt_tokens / 1_000_000 * in_price + completion_tokens / 1_000_000 * out_price

def _flag_output_upper(n_questions: int) -> int:
    return max(EST_OUTPUT_TOKENS_PER_CHUNK, n_questions * EST_OUTPUT_TOKENS_PER_QUESTION)
