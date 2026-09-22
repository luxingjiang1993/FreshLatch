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

from freshlatch.eval.matrix import BUCKETS
from freshlatch.eval.runner import (EVAL_MODE_SWITCHES, REPRO_NOTE,
                                    DEFAULT_DISTRACTOR_DOCKET, load_gold)
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.runner import load_docket
from freshlatch.store.base import RetrievalStore

VERDICT_PATTERN = re.compile(r"\{[^{}]*\"verdict\"[^{}]*\}")

# 预登记锁定件:docs/evidence/w4/false-green-control-prereg.md(决议 #46)
# 首次新运行前必须与预登记逐字一致:保留「现在是否仍然成立」,删禁外信息句。
CONTROL_PROMPT = """你是市场研判助手。以下是一条数周前签发的研判主张,以及签发时所依据的文档摘录:

主张: {statement}
签发时所依据的文档摘录: {t0_excerpt}

请判断:该主张现在是否仍然成立?
只输出 JSON,格式:{{"verdict": "alive"|"dead"|"unknown"}}。"""

# 仪器 C 锁定件:docs/evidence/w4/false-green-control-c-prereg.md(决议 #77)
# 旁增并行路径;旧 CONTROL_PROMPT 与旧预登记保持不动。
CONTROL_PROMPT_C = """你是市场研判助手。以下是一条数周前签发的研判主张,以及签发时所依据的文档摘录:

主张: {statement}
签发时所依据的文档摘录: {t0_excerpt}

若缺少签发之后的更新材料,不要因此默认 unknown。
请判断:该主张现在是否仍然成立?
只输出 JSON,格式:{{"verdict": "alive"|"dead"|"unknown"}}。"""

# C 私有多锚表(跑前写死;共享 t0_docket 只读,不从此表回写)
CONTROL_C_T0_EVIDENCE_IDS: dict[str, tuple[str, ...]] = {
    "c1": ("t0-competitor-notes#p1", "t0-competitor-notes#p2", "t0-competitor-notes#p3"),
    "c2": ("t0-regulatory-memo#p1", "t0-regulatory-memo#p2", "t0-regulatory-memo#p3"),
    "c3": ("t0-channel-interviews#p1", "t0-channel-interviews#p2", "t0-channel-interviews#p3"),
    "c4": ("t0-market-census#p1", "t0-market-census#p2", "t0-market-census#p3"),
    "c5": ("t0-cost-model#p1", "t0-cost-model#p2", "t0-cost-model#p3"),
    "c6": ("t0-competitor-news#p1", "t0-competitor-news#p2", "t0-competitor-news#p3"),
    "c7": ("t0-trade-press#p1", "t0-trade-press#p2", "t0-trade-press#p3"),
    "c8": ("t0-tech-ecosystem#p1", "t0-tech-ecosystem#p2", "t0-tech-ecosystem#p3"),
    "c9": ("t0-messaging-survey#p1", "t0-messaging-survey#p2", "t0-messaging-survey#p3"),
    "c10": ("t0-talent-salary#p1", "t0-talent-salary#p2", "t0-talent-salary#p3"),
    "c11": ("t0-payment-landscape#p1", "t0-payment-landscape#p2", "t0-payment-landscape#p3"),
    "c12": ("t0-infra-reliability#p1", "t0-infra-reliability#p2", "t0-infra-reliability#p3"),
    "c13": ("t0-competitor-economics#p1", "t0-competitor-economics#p2", "t0-competitor-economics#p3"),
    "c14": ("t0-channel-coverage#p1", "t0-channel-coverage#p2", "t0-channel-coverage#p3"),
}

CONTROL_REDLINE_NOTE = "prompt 红线:不提及 T1/快照/复验语料存在,不提及金标与期望判定(对照泄题即废)"


class ControlCMissingChunkError(RuntimeError):
    """已锁 evidence id 缺 chunk → 整刀作废,不得静默少拼(预登记作废线 §5)。"""


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
                docket_path: str | Path, decoding: DecodingParams | None = None,
                distractor_docket_path: str | Path | None = DEFAULT_DISTRACTOR_DOCKET) -> dict:
    decoding = decoding or DecodingParams()
    llm = llm or LLMClient()
    gold = load_gold(gold_path)
    docket = load_docket(docket_path)
    gold_ids = {cid for bucket in BUCKETS for cid in gold[bucket]}

    # 干扰项(#21 乙-i):must_fresh 方向,无工具基线读 T0 应判 alive(成立)——
    # 判 dead 说明干扰项在基线上即被识破,记录备查;不影响 control_pass 口径。
    distractor_ids = list(gold.get("must_fresh_distractor", []))
    claims = list(docket.claims)
    if distractor_ids and distractor_docket_path and Path(distractor_docket_path).exists():
        d_ids = set(distractor_ids)
        claims += [c for c in load_docket(distractor_docket_path).claims if c.claim_id in d_ids]

    results: dict[str, dict] = {}
    for claim in claims:
        if claim.claim_id not in gold_ids and claim.claim_id not in distractor_ids:
            continue  # 只跑金标 12 条(§4.2 对账口径)+ 干扰项桶;docket 外主张不进对照
        excerpt_parts = []
        for eid in claim.t0_evidence_ids:
            doc_id, _, anchor = eid.partition("#")
            chunk = store.get_chunk(doc_id, anchor, as_of="T0") if anchor else None
            if chunk is not None:
                excerpt_parts.append(chunk.text)
        t0_excerpt = "\n\n".join(excerpt_parts)
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
        "must_stale_total": len(gold["must_stale"]),
        "control_pass": len(false_green_dead) == len(gold["must_stale"]),
        # 干扰项基线读数(假绿对照记录,#21 乙-i):期望 alive;非 alive 列备查不计 pass
        "distractor_baseline": {cid: results[cid]["verdict"] for cid in distractor_ids
                                if cid in results},
        "distractor_baseline_note": ("must_fresh 干扰项:无工具基线只读 T0,应判 alive(成立);"
                                     "判 dead 说明干扰项在基线上即被识破,记录备查"),
    }


def _build_c_excerpt(store: RetrievalStore, claim_id: str) -> tuple[list[str], str]:
    """按 C 私有多锚表取 chunk;缺任一条 → 抛 ControlCMissingChunkError(作废,不静默少拼)。"""
    locked = CONTROL_C_T0_EVIDENCE_IDS.get(claim_id)
    if locked is None:
        raise ControlCMissingChunkError(
            f"仪器 C:claim_id={claim_id} 不在已锁多锚表 CONTROL_C_T0_EVIDENCE_IDS 中"
        )
    parts: list[str] = []
    for eid in locked:
        doc_id, _, anchor = eid.partition("#")
        chunk = store.get_chunk(doc_id, anchor, as_of="T0") if anchor else None
        if chunk is None:
            raise ControlCMissingChunkError(
                f"仪器 C:已锁 evidence id 缺 chunk → {claim_id}/{eid}(整刀作废,不得静默少拼)"
            )
        parts.append(chunk.text)
    return list(locked), "\n\n".join(parts)


def run_control_c(store: RetrievalStore, llm: LLMClient | None, *, gold_path: str | Path,
                  docket_path: str | Path, decoding: DecodingParams | None = None,
                  distractor_docket_path: str | Path | None = DEFAULT_DISTRACTOR_DOCKET) -> dict:
    """假绿仪器 C:并行 CONTROL_PROMPT_C + 私有多锚;共享 docket 只读。

    不改旧 run_control / CONTROL_PROMPT。缺 chunk 抛 ControlCMissingChunkError(作废线)。
    """
    decoding = decoding or DecodingParams()
    llm = llm or LLMClient()
    gold = load_gold(gold_path)
    docket = load_docket(docket_path)
    gold_ids = {cid for bucket in BUCKETS for cid in gold[bucket]}

    distractor_ids = list(gold.get("must_fresh_distractor", []))
    claims = list(docket.claims)
    if distractor_ids and distractor_docket_path and Path(distractor_docket_path).exists():
        d_ids = set(distractor_ids)
        claims += [c for c in load_docket(distractor_docket_path).claims if c.claim_id in d_ids]

    results: dict[str, dict] = {}
    for claim in claims:
        if claim.claim_id not in gold_ids and claim.claim_id not in distractor_ids:
            continue
        ids_sent, t0_excerpt = _build_c_excerpt(store, claim.claim_id)
        msg = llm.chat(
            [{"role": "user", "content": CONTROL_PROMPT_C.format(
                statement=claim.statement, t0_excerpt=t0_excerpt)}],
            decoding=decoding,
            response_format={"type": "json_object"},
        )
        content = (msg.content or "").strip()
        verdict = _parse_verdict(content)
        results[claim.claim_id] = {
            "verdict": verdict,
            "raw": content[:500],
            "t0_evidence_ids_sent": ids_sent,
            "t0_excerpt": t0_excerpt,
            "t0_excerpt_char_len": len(t0_excerpt),
        }

    false_green_dead = [cid for cid in gold["must_stale"] if results[cid]["verdict"] == "alive"]
    blind_green = [cid for cid in gold["must_unknown"] if results[cid]["verdict"] == "alive"]
    return {
        "kind": "control_run",
        "instrument": "false_green_control_c",
        "prompt_id": "CONTROL_PROMPT_C",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "decoding": decoding.__dict__,
        "redline_note": CONTROL_REDLINE_NOTE,
        "eval_mode_switches": list(EVAL_MODE_SWITCHES),
        "repro_note": REPRO_NOTE,
        "results": results,
        "false_green_must_stale": false_green_dead,
        "blind_green_must_unknown": blind_green,
        "must_stale_total": len(gold["must_stale"]),
        "control_pass": len(false_green_dead) == len(gold["must_stale"]),
        "distractor_baseline": {cid: results[cid]["verdict"] for cid in distractor_ids
                                if cid in results},
        "distractor_baseline_note": ("must_fresh 干扰项:无工具基线只读 T0,应判 alive(成立);"
                                     "判 dead 说明干扰项在基线上即被识破,记录备查"),
    }
