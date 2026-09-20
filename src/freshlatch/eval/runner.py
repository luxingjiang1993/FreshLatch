"""金标 runner(§4.1):端到端真主链对账 gold.json。

每主张 × 每遍独立 Runner 实例(独立 RunContext:检索预算 24 不跨遍共享),轨迹 JSONL 逐遍落盘。
统计纪律(决策七):--runs N 每条主张跑 N 遍,报 per-claim 命中次数/N;N=1 退化为单列。
W4 的 3 遍 × 3 seed 验收冒烟按 §4.4 不走本 runner(独立拍板,显式非零温度 + 换 seed 重跑)。
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from freshlatch.eval.checks import check_counterevidence, expected_evidence_id
from freshlatch.eval.matrix import BUCKETS, EXPECTED_VERDICT, confusion_matrix
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.runner import Runner, load_docket
from freshlatch.store.base import RetrievalStore

EVAL_MODE_SWITCHES = (
    "跳过 HumanLatch:W1–W4 未挂载,runner 不 import langgraph,人审不进评测路径",
    "禁用联网:web_search 不在任何角色白名单,模型物理上不可见(§4.6)",
)
REPRO_NOTE = ("闸层(must_* 零违例)给定解码参数下逐位复现;判定层(矩阵条数)按文档化容差;"
              "违例级背离(must_stale 被判 fresh)触发人查。qwen-flash 为活托管端点,跨会话复现只能近似。")


def load_gold(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gold_claims(gold: dict, docket_path: str | Path) -> list:
    """docket 中取金标 12 主张(statement 与 t0_evidence_ids 单一真相在 data/)。"""
    docket = load_docket(docket_path)
    ids = {cid for bucket in BUCKETS for cid in gold[bucket]}
    return [c for c in docket.claims if c.claim_id in ids]


def run_gold(store: RetrievalStore, llm: LLMClient | None, *, gold_path: str | Path,
             docket_path: str | Path, runs: int = 1,
             decoding: DecodingParams | None = None,
             trajectory_dir: str | Path = "reports/trajectories") -> dict:
    """跑 N 遍全量金标,返回原始结果 dict(报告与 raw JSON 的唯一原料)。"""
    decoding = decoding or DecodingParams()
    llm = llm or LLMClient()
    gold = load_gold(gold_path)
    claims = gold_claims(gold, docket_path)

    per_run: list[dict] = []
    for run_idx in range(1, runs + 1):
        # 逐运行 decoding 留档(§4.7):每遍独立 DecodingParams,recorded_at 区分运行
        run_decoding = replace(decoding, recorded_at=datetime.now(timezone.utc).isoformat())
        decisions: dict[str, str] = {}
        detail: dict[str, dict] = {}
        for claim in claims:
            runner = Runner(store, llm, mode="eval", decoding=run_decoding)
            result = runner.run([claim], trajectory_dir=trajectory_dir)
            final = claim.status
            decisions[claim.claim_id] = final
            detail[claim.claim_id] = {
                "status": final,
                "reason": claim.reason,
                "evidence_ids": list(claim.t1_evidence_ids),
                "trajectory": str(result.trajectory_path),
                "steps_used": result.steps_by_claim.get(claim.claim_id, 0),
            }
        matrix = confusion_matrix(gold, decisions)
        per_run.append({"run": run_idx, "decoding": run_decoding.__dict__,
                        "decisions": decisions,
                        "detail": detail, "matrix": matrix.to_dict()})

    # per-claim 命中次数/N(报告按 N>1 设计的 pass@k 表)
    pass_at_k = {
        cid: sum(1 for r in per_run if r["decisions"].get(cid) == _expected(gold, cid))
        for cid in (c.claim_id for c in claims)
    }

    # J1 点回 + J2 有效反证机器判据:取每主张 N 遍中最近一遍的 detail(条数容差层)
    point_back: dict[str, dict] = {}
    counterevidence: dict[str, list[dict]] = {}
    for claim in claims:
        cid = claim.claim_id
        last = per_run[-1]["detail"][cid]
        expected = expected_evidence_id(gold, cid)
        point_back[cid] = {
            "expected_anchor": expected,
            "hit": expected is not None and expected in last["evidence_ids"],
            "evidence_ids": last["evidence_ids"],
            "exempt": expected is None,  # must_unknown 无 T1 原文天然豁免
        }
        if cid in gold["must_stale"]:
            counterevidence[cid] = [
                check_counterevidence(store, gold, cid,
                                      per_run[i]["detail"][cid]["reason"],
                                      per_run[i]["detail"][cid]["evidence_ids"])
                for i in range(runs)
            ]
    # 反向护栏:must_fresh 不得出现有效反证(机器层)
    fresh_guardrail = {
        cid: [not check_counterevidence(store, gold, cid,
                                        per_run[i]["detail"][cid]["reason"],
                                        per_run[i]["detail"][cid]["evidence_ids"])["valid_machine"]
              for i in range(runs)]
        for cid in gold["must_fresh"]
    }

    return {
        "kind": "gold_run",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "runs": runs,
        "decoding": decoding.__dict__,
        "eval_mode_switches": list(EVAL_MODE_SWITCHES),
        "repro_note": REPRO_NOTE,
        "per_run": per_run,
        "pass_at_k": pass_at_k,
        "point_back_j1": point_back,
        "counterevidence_j2": counterevidence,
        "fresh_guardrail_j2": fresh_guardrail,
        "trajectory_dir": str(trajectory_dir),
    }


def _expected(gold: dict, cid: str) -> str | None:
    for bucket in BUCKETS:
        if cid in gold[bucket]:
            return EXPECTED_VERDICT[bucket]
    return None
