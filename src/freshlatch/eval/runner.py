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
from freshlatch.llm import DecodingParams, LLMClient, TokenUsage
from freshlatch.roles.auditor import EVIDENCE_PACKET_SCHEMA_VERSION
from freshlatch.runner import Runner, load_docket
from freshlatch.store.base import RetrievalStore

# 乙-i 干扰项桶(#21):must_fresh 方向的未见混淆类型探针(客单价≠毛利、覆盖率≠渗透率)。
# 不进 BUCKETS 判分矩阵(12 条口径一字未动,W4↔W12 同尺),单列敏感度附表,不计通过线。
DISTRACTOR_BUCKET = "must_fresh_distractor"
DEFAULT_DISTRACTOR_DOCKET = "data/eval/distractor_docket.json"

EVAL_MODE_SWITCHES = (
    "跳过 HumanLatch:W1–W4 未挂载,runner 不 import langgraph,人审不进评测路径",
    "禁用联网:web_search 不在任何角色白名单,模型物理上不可见(§4.6)",
)
REPRO_NOTE = ("闸层(must_* 零违例)给定解码参数下逐位复现;判定层(矩阵条数)按文档化容差;"
              "违例级背离(must_stale 被判 fresh)触发人查。qwen-flash 为活托管端点,跨会话复现只能近似。")

_ZERO_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def _reset_token_usage(llm: object) -> None:
    """单桶清零;非 LLMClient 的脚本假件无 token_usage 时静默跳过。"""
    tu = getattr(llm, "token_usage", None)
    if isinstance(tu, TokenUsage):
        tu.reset()


def _snapshot_token_usage(llm: object) -> dict:
    """读取当前桶快照;假件无桶时回零(报告块字段仍在,schema 稳定)。"""
    tu = getattr(llm, "token_usage", None)
    if isinstance(tu, TokenUsage):
        return tu.to_dict()
    return dict(_ZERO_USAGE)


def load_gold(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gold_claims(gold: dict, docket_path: str | Path) -> list:
    """docket 中取金标 12 主张(statement 与 t0_evidence_ids 单一真相在 data/)。"""
    docket = load_docket(docket_path)
    ids = {cid for bucket in BUCKETS for cid in gold[bucket]}
    return [c for c in docket.claims if c.claim_id in ids]


def _detail(result, claim) -> dict:
    """单主张运行明细(主矩阵与干扰项附表共用;#22 起带双判留档字段)。"""
    dec = result.decisions[claim.claim_id]
    return {
        "status": claim.status,
        "reason": claim.reason,
        "evidence_ids": list(claim.t1_evidence_ids),
        "trajectory": str(result.trajectory_path),
        "steps_used": result.steps_by_claim.get(claim.claim_id, 0),
        # 双判留档(#20/ADR-0009):Lead 原始判定 + Auditor 判定,S1/S2 分歧率原料
        "lead_status": dec.status,
        "auditor_verdict": dec.auditor_verdict,
        "dissent": claim.dissent,
    }


def run_gold(store: RetrievalStore, llm: LLMClient | None, *, gold_path: str | Path,
             docket_path: str | Path, runs: int = 1,
             decoding: DecodingParams | None = None,
             trajectory_dir: str | Path = "reports/trajectories",
             distractor_docket_path: str | Path = DEFAULT_DISTRACTOR_DOCKET) -> dict:
    """跑 N 遍全量金标,返回原始结果 dict(报告与 raw JSON 的唯一原料)。

    主矩阵恒为 BUCKETS 三桶 12 条(判分口径不动);must_fresh_distractor 桶走同一真主链,
    单列敏感度附表原料(乙-i),不计通过线。
    """
    decoding = decoding or DecodingParams()
    llm = llm or LLMClient()
    gold = load_gold(gold_path)
    claims = gold_claims(gold, docket_path)
    # 干扰项主张:独立 docket(不动生产卷宗),缺桶或缺文件则本段留空(向后兼容)
    distractor_path = Path(distractor_docket_path)
    distractor_claims: list = []
    if gold.get(DISTRACTOR_BUCKET) and distractor_path.exists():
        d_ids = set(gold[DISTRACTOR_BUCKET])
        distractor_claims = [c for c in load_docket(distractor_path).claims
                             if c.claim_id in d_ids]

    per_run: list[dict] = []
    per_run_distractor: list[dict] = []
    # K5-1:顶层合计 = 各遍 token_usage 之和;每遍开跑前清零单桶
    total_usage = TokenUsage()
    for run_idx in range(1, runs + 1):
        _reset_token_usage(llm)
        # 逐运行 decoding 留档(§4.7):每遍独立 DecodingParams,recorded_at 区分运行
        run_decoding = replace(decoding, recorded_at=datetime.now(timezone.utc).isoformat())
        decisions: dict[str, str] = {}
        detail: dict[str, dict] = {}
        for claim in claims:
            runner = Runner(store, llm, mode="eval", decoding=run_decoding)
            result = runner.run([claim], trajectory_dir=trajectory_dir)
            final = claim.status
            decisions[claim.claim_id] = final
            detail[claim.claim_id] = _detail(result, claim)
        matrix = confusion_matrix(gold, decisions)
        # 干扰项同链跑(同一 decoding、同一 Runner 入口),不进 matrix;用量计入本遍桶
        if distractor_claims:
            d_decisions: dict[str, str] = {}
            d_detail: dict[str, dict] = {}
            for claim in distractor_claims:
                runner = Runner(store, llm, mode="eval", decoding=run_decoding)
                result = runner.run([claim], trajectory_dir=trajectory_dir)
                d_decisions[claim.claim_id] = claim.status
                d_detail[claim.claim_id] = _detail(result, claim)
            per_run_distractor.append({"run": run_idx, "decisions": d_decisions,
                                       "detail": d_detail})
        run_usage = _snapshot_token_usage(llm)
        total_usage.add(run_usage["prompt_tokens"], run_usage["completion_tokens"])
        per_run.append({"run": run_idx, "decoding": run_decoding.__dict__,
                        "decisions": decisions,
                        "detail": detail, "matrix": matrix.to_dict(),
                        "token_usage": run_usage})

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
                                      per_run[i]["detail"][cid]["status"],
                                      per_run[i]["detail"][cid]["reason"],
                                      per_run[i]["detail"][cid]["evidence_ids"])
                for i in range(runs)
            ]
    # 反向护栏:must_fresh 不得出现有效反证(机器层;fresh 方向不构成反证,见 checks 前置条件)
    fresh_guardrail = {
        cid: [not check_counterevidence(store, gold, cid,
                                        per_run[i]["detail"][cid]["status"],
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
        "token_usage": total_usage.to_dict(),  # K5-1:顶层合计(与 per_run[i].token_usage 同字段)
        "per_run": per_run,
        "pass_at_k": pass_at_k,
        "point_back_j1": point_back,
        "counterevidence_j2": counterevidence,
        "fresh_guardrail_j2": fresh_guardrail,
        "dimension_confusion_flags": dimension_confusion_flags(gold, per_run),
        "distractor_sensitivity": distractor_sensitivity(gold, per_run_distractor),
        "divergence_s1_s2": divergence_counts(per_run),
        "evidence_packet_schema": EVIDENCE_PACKET_SCHEMA_VERSION,  # #20 §4.6:版本随报告登记
        "trajectory_dir": str(trajectory_dir),
    }


def _expected(gold: dict, cid: str) -> str | None:
    for bucket in BUCKETS:
        if cid in gold[bucket]:
            return EXPECTED_VERDICT[bucket]
    return None


# -- 乙-ii / 乙-i 汇总纯函数(可单测,层间归因靠它们不靠 bundle) -------------------


def divergence_counts(per_run: list[dict]) -> dict:
    """S1/S2 分歧率落档(#20 评估 §4.6):每主张每跑 Lead stale/unknown × Auditor fresh 计 S2,
    反之为 S1。只落档不报成败(W9–W12 调优信号);原始判定对取 per_run[i].detail 的
    lead_status/auditor_verdict 字段(#22 双判留档)。"""
    s1 = s2 = 0
    for r in per_run:
        for d in (r.get("detail") or {}).values():
            if d.get("lead_status") in ("stale", "unknown") and d.get("auditor_verdict") == "fresh":
                s2 += 1
            else:
                s1 += 1
    total = s1 + s2
    return {"s1": s1, "s2": s2, "total": total,
            "s2_rate": (s2 / total) if total else 0.0}


def dimension_confusion_flags(gold: dict, per_run: list[dict]) -> dict[str, list[bool]]:
    """乙-ii 标注原料:must_fresh 判 stale 且未落在金标锚 → 该遍记「维度疑似混淆」。

    评测模式加严判据,归 #19 评估文档(纪律 #4,不进 CONTEXT.md);机器只给疑似标注,定性归人查。
    """
    flags: dict[str, list[bool]] = {}
    for cid in gold["must_fresh"]:
        expected = expected_evidence_id(gold, cid)
        flags[cid] = [
            per_run[i]["detail"][cid]["status"] == "stale"
            and expected not in per_run[i]["detail"][cid]["evidence_ids"]
            for i in range(len(per_run))
        ]
    return flags


def distractor_sensitivity(gold: dict, per_run: list[dict]) -> dict[str, dict]:
    """乙-i 附表原料:干扰项逐遍判定 + fresh 命中 + 金标锚命中(不进判分矩阵)。"""
    sens: dict[str, dict] = {}
    for cid in gold.get(DISTRACTOR_BUCKET, []):
        expected = expected_evidence_id(gold, cid)
        if not per_run:  # 桶在册但未配置 docket:留空位,不炸
            sens[cid] = {"expected_anchor": expected, "statuses": [],
                         "fresh_hits": 0, "anchor_hits": 0, "trajectory": None}
            continue
        statuses = [per_run[i]["decisions"][cid] for i in range(len(per_run))]
        sens[cid] = {
            "expected_anchor": expected,
            "statuses": statuses,
            "fresh_hits": sum(1 for s in statuses if s == "fresh"),
            "anchor_hits": sum(
                1 for i in range(len(per_run))
                if expected in per_run[i]["detail"][cid]["evidence_ids"]
            ),
            "trajectory": per_run[-1]["detail"][cid]["trajectory"],
        }
    return sens
