"""Run 编排:预算/名单注入、轨迹 JSONL 落盘、模式开关(在线|eval)。

eval 模式(W3–W4 评测 harness 用):代码级跳过 HumanLatch、代码级禁用联网;
W1–W2 零 HumanLatch,本模块不 import langgraph。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from freshlatch.guardrails import BUDGET_EXHAUSTED_MESSAGE, Guardrails
from freshlatch.llm import DecodingParams, LLMClient
from freshlatch.models import AsOf, Claim
from freshlatch.store.base import RetrievalStore

RETRIEVAL_EXHAUSTED = {"budget_exhausted": True,
                       "message": "检索预算已尽(24/Run)。请改用 read_source 直读原文,或基于现有证据下结论。"}


@dataclass
class RunContext:
    """一次 Run 的共享状态:store、护栏、作废名单、检索预算计数、轨迹事件。"""

    store: RetrievalStore
    guardrails: Guardrails = field(default_factory=Guardrails)
    invalidation_list: set[str] = field(default_factory=set)
    retrieval_used: int = 0
    events: list[dict] = field(default_factory=list)
    decoding: DecodingParams = field(default_factory=DecodingParams)
    mode: str = "online"  # online | eval
    gaps: list[str] = field(default_factory=list)
    quarantine_list: set[str] = field(default_factory=set)  # 隔离名单(W9 记忆卫生;槽位本期为空)

    def try_retrieve(self, query: str, *, source_type: str | None = None,
                     as_of: AsOf | None = None, top_k: int = 10) -> list | dict:
        """retrieve 的预算闸门:Run 级共享计数,超限 fail-soft 返回结构化结果,不抛异常。"""
        if self.retrieval_used >= self.guardrails.retrieval_budget:
            self.events.append({"type": "budget", "kind": "retrieval_exhausted",
                                "used": self.retrieval_used})
            return RETRIEVAL_EXHAUSTED
        self.retrieval_used += 1
        hits = self.store.retrieve(query, as_of=as_of, source_type=source_type, top_k=top_k)
        self.events.append({"type": "retrieve", "query": query, "as_of": as_of,
                            "used": self.retrieval_used, "hits": len(hits)})
        return hits

    def emit(self, event: dict) -> None:
        self.events.append(event)


@dataclass
class ClaimDecision:
    claim_id: str
    status: str = "unknown"
    reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    claims: list[Claim]
    decisions: dict[str, ClaimDecision]
    trajectory_path: Path | None
    steps_by_claim: dict[str, int]
    retrieval_used: int
    decoding: DecodingParams


@dataclass
class Docket:
    """T0 卷宗导入件(EvidenceOS 形状,§2.1):question + 主张列表,单一真相在 data/。"""

    question: str
    claims: list[Claim]


def load_docket(path: str | Path) -> Docket:
    """导入是 Workflow:只读 statement 与 t0_evidence_ids,不做新调查(§2.1)。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Docket(
        question=data["question"],
        claims=[
            Claim(claim_id=c["claim_id"], statement=c["statement"],
                  t0_evidence_ids=list(c.get("t0_evidence_ids", [])))
            for c in data["claims"]
        ],
    )


class Runner:
    def __init__(self, store: RetrievalStore, llm: LLMClient | None = None,
                 guardrails: Guardrails | None = None, *, mode: str = "online",
                 decoding: DecodingParams | None = None) -> None:
        self.ctx = RunContext(
            store=store,
            guardrails=guardrails or Guardrails(),
            invalidation_list=set(store.list_invalidation()),
            decoding=decoding or DecodingParams(),
            mode=mode,
        )
        self.llm = llm or LLMClient()
        self._trajectory_path: Path | None = None

    def run(self, claims: list[Claim], *, trajectory_dir: str | Path = "reports/trajectories") -> RunResult:
        from freshlatch.roles.lead import LeadReverifier  # 延迟导入避免环

        decisions: dict[str, ClaimDecision] = {}
        steps_by_claim: dict[str, int] = {}
        for claim in claims:
            lead = LeadReverifier(self.ctx, claim, self.llm)
            decision = lead.run()
            decisions[claim.claim_id] = decision
            steps_by_claim[claim.claim_id] = lead.steps_used
            self._finalize(claim, decision)

        tdir = Path(trajectory_dir)
        tdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._trajectory_path = tdir / f"run-{ts}.jsonl"
        self._dump_trajectory(claims, decisions)
        return RunResult(claims=claims, decisions=decisions,
                         trajectory_path=self._trajectory_path,
                         steps_by_claim=steps_by_claim,
                         retrieval_used=self.ctx.retrieval_used,
                         decoding=self.ctx.decoding)

    def _finalize(self, claim: Claim, decision: ClaimDecision) -> None:
        """判定落档:Agent 不得拥有放行权——fresh/stale 必须过规则闸,闸打回落 unknown。"""
        from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
        claim.reason = decision.reason
        claim.t1_evidence_ids = decision.evidence_ids
        gate_ctx = GateContext(invalidation_list=self.ctx.invalidation_list,
                               checksum_fn=self._checksum_fn, eval_mode=(self.ctx.mode == "eval"))
        if decision.status == "fresh":
            gate = rule_gate(claim, GateDecision(status="fresh", t1_evidence_ids=decision.evidence_ids), gate_ctx)
            if gate.green:
                claim.status = "fresh"
            else:
                claim.status = "unknown"
                claim.reason = f"[闸打回:{gate.error_code}] {gate.reason}; 原理由: {decision.reason}"
        elif decision.status == "stale":
            gate = rule_gate(claim, GateDecision(status="stale", t1_evidence_ids=decision.evidence_ids,
                                                 stale_reason=decision.reason), gate_ctx)
            if gate.allowed:
                claim.status = "stale"
            else:
                claim.status = "unknown"
                claim.reason = f"[闸打回:{gate.error_code}] {gate.reason}; 原理由: {decision.reason}"
        else:
            claim.status = "unknown"
        self.ctx.emit({"type": "claim_result", "claim_id": claim.claim_id,
                       "status": claim.status, "reason": claim.reason})

    def _checksum_fn(self, doc_id: str, as_of: AsOf) -> str | None:
        """checksum 三处留位本期为空:documents 表 checksum 列默认 '',视为未启用。"""
        return None

    def _dump_trajectory(self, claims: list[Claim], decisions: dict[str, ClaimDecision]) -> None:
        assert self._trajectory_path is not None
        with self._trajectory_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "run_meta", "mode": self.ctx.mode,
                                "decoding": self.ctx.decoding.__dict__,
                                "guardrails": self.ctx.guardrails.__dict__,
                                "invalidation_list": sorted(self.ctx.invalidation_list),
                                "soft_close_message": BUDGET_EXHAUSTED_MESSAGE},
                               ensure_ascii=False) + "\n")
            for ev in self.ctx.events:
                f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
            for c in claims:
                d = decisions[c.claim_id]
                f.write(json.dumps({"type": "claim_final", "claim_id": c.claim_id,
                                    "statement": c.statement, "status": c.status,
                                    "reason": d.reason, "evidence_ids": d.evidence_ids},
                                   ensure_ascii=False) + "\n")
