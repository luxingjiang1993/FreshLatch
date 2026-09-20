"""无工具假绿对照(§4.2):同模型不带工具,只读 T0 摘要 + 主张,问「现在是否仍成立」。

输出契约:JSON mode `{"verdict": "alive"|"dead"|"unknown"}`,机械解析对账(决策二)。
prompt 红线:**不得透露 T1 存在、不得透露金标**——泄一句对照即废。
假绿来源完整性(§4.2):must_stale 判 alive = 该红的判绿;must_unknown 判 alive = 没源的也敢判绿;
对照成立 = 全部 must_stale 被判 alive(已死主张必须假绿,本产品必须红)。
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from freshlatch.eval.runner import EVAL_MODE_SWITCHES, REPRO_NOTE, load_gold
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.runner import load_docket
from freshlatch.store.base import RetrievalStore

VERDICT_PATTERN = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}")

CONTROL_PROMPT = """你是市场研判助手。以下是一条数周前签发的研判主张,以及签发时所依据的文档摘录:

主张: {statement}
签发时所依据的文档摘录: {t0_excerpt}

请判断:该主张现在是否仍然成立?只依据给定材料回答,不要引入材料之外的信息。
只输出 JSON,格式:{{"verdict": "alive"|"dead"|"unknown"}}。"""

CONTROL_REDLINE_NOTE = "prompt 红线:不提及 T1/快照/复验语料存在,不提及金标与期望判定(对照泄题即废)"


def _parse_verdict(content: str) -> str:
    """机械解析 JSON mode 输出;解析不出 → unparseable(显式可见,不猜)。"""
    if not content:
        return "unparseable"
    match = VERDICT_PATTERN.search(content)
    if not match:
        return "unparseable"
    try:
        verdict = json.loads(match.group(0))["verdict"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return "unparseable"
    return verdict if verdict in ("alive", "dead", "unknown") else "unparseable"


def run_control(store: RetrievalStore, llm: LLMClient | None, *, gold_path: str | Path,
                docket_path: str | Path, decoding: DecodingParams | None = None) -> dict:
    decoding = decoding or DecodingParams()
    llm = llm or LLMClient()
    gold = load_gold(gold_path)
    docket = load_docket(docket_path)

    results: dict[str, dict] = {}
    for claim in docket.claims:
        t0_excerpt = ""
        if claim.t0_evidence_ids:
            doc_id, _, anchor = claim.t0_evidence_ids[0].partition("#")
            chunk = store.get_chunk(doc_id, anchor, as_of="T0") if anchor else None
            if chunk is not None:
                t0_excerpt = chunk.text
        msg = llm.chat(
            [{"role": "user", "content": CONTROL_PROMPT.format(
                statement=claim.statement, t0_excerpt=t0_excerpt)}],
            decoding=decoding,
            response_format={"type": "json_object"},
        )
        content = (msg.content or "").strip()
        verdict = _parse_verdict(content)
        results[claim.claim_id] = {"verdict": verdict, "raw": content[:500]}

    false_green_dead = [cid for cid in gold["must_stale"] if results[cid]["verdict"] == "alive"]
    blind_green = [cid for cid in gold["must_unknown"] if results[cid]["verdict"] == "alive"]
    return {
        "kind": "control_run",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "decoding": decoding.__dict__,
        "redline_note": CONTROL_REDLINE_NOTE,
        "eval_mode_switches": list(EVAL_MODE_SWITCHES),
        "repro_note": REPRO_NOTE,
        "results": results,
        "false_green_must_stale": false_green_dead,
        "blind_green_must_unknown": blind_green,
        "control_pass": len(false_green_dead) == len(gold["must_stale"]),
    }
