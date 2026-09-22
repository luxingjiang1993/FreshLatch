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
from freshlatch.roles.auditor import EVIDENCE_PACKET_SCHEMA_VERSION
from freshlatch.skills_loader import load_skill_body
from freshlatch.store.base import RetrievalStore
from freshlatch.tools import FOCUS_DIMENSIONS

RETRIEVAL_EXHAUSTED = {"budget_exhausted": True,
                       "message": "检索预算已尽(24/Run)。请改用 read_source 直读原文,或基于现有证据下结论。"}


def list_retrieve_zero_hits(events: list[dict]) -> list[dict]:
    """从轨迹事件抽出 retrieve 空命中(DEM-5 真源)。

    只计 type=retrieve 且 hits==0;预算耗尽(budget)与有命中不计入。
    返回浅拷贝列表,供 UI 强提示;调用方不得据此改写主张判定。
    """
    out: list[dict] = []
    for ev in events:
        if ev.get("type") != "retrieve":
            continue
        if int(ev.get("hits", -1)) != 0:
            continue
        out.append({
            "query": ev.get("query", ""),
            "as_of": ev.get("as_of"),
            "used": ev.get("used"),
            "hits": 0,
        })
    return out


@dataclass
class RunContext:
    """一次 Run 的共享状态:store、护栏、作废名单、检索预算计数、轨迹事件。"""

    store: RetrievalStore
    guardrails: Guardrails = field(default_factory=Guardrails)
    invalidation_list: set[str] = field(default_factory=set)
    retrieval_used: int = 0
    lead_steps_used: int = 0  # 当前 Lead 会话步数(UI DEM-4 进度;与 lead_max_steps 对齐)
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
    status: str = "unknown"  # Lead 的判定(fresh/stale/unknown);落档仲裁后最终态在 claim.status
    reason: str = ""
    evidence_ids: list[str] = field(default_factory=list)
    auditor_verdict: str | None = None  # Auditor 单轮判定在场(ADR-0009/0010;None = 未触发/缺席)
    auditor_reason: str = ""
    auditor_dimension_match: bool | None = None  # ADR-0010:False = 维度异议
    stale_dimension: str | None = None  # ADR-0011:反证自标维度(mark_stale 必填 dimension 字段)
    dimension_objection: dict | None = None  # ADR-0012:受理层维度预检打回记录
    # {error_code, stale_dimension, evidence_ids};Lead 未显式收口(reverify_claim/mark_stale
    # 受理即清)时由 _finalize 落机械比对异议(黄卡不断供)


@dataclass
class RunResult:
    claims: list[Claim]
    decisions: dict[str, ClaimDecision]
    trajectory_path: Path | None
    steps_by_claim: dict[str, int]
    retrieval_used: int
    decoding: DecodingParams
    # DEM-5:本轮 retrieve 空命中清单(UI 强提示真源);空列表 = 无零命中,不触发横幅
    retrieve_zero_hits: list[dict] = field(default_factory=list)


@dataclass
class Docket:
    """T0 卷宗导入件(EvidenceOS 形状,§2.1):question + 主张列表,单一真相在 data/。"""

    question: str
    claims: list[Claim]


def load_docket(path: str | Path) -> Docket:
    """导入是 Workflow:只读 statement 与 t0_evidence_ids,不做新调查(§2.1)。

    dimension 签发即校验(ADR-0011):非法值硬拒绝,坏卷宗不进系统;缺失 = None,
    stale 路径维度防线回落不变量 7(机械跨检无锚可比对,不拦未登记主张)。
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    claims = []
    for c in data["claims"]:
        dim = c.get("dimension")
        if dim is not None and dim not in FOCUS_DIMENSIONS:
            raise ValueError(
                f"签发卷宗 {path} 主张 {c.get('claim_id')}:dimension 非法值 {dim!r}"
                f"(封闭枚举:{'/'.join(FOCUS_DIMENSIONS)};ADR-0011 签发即校验,坏卷宗不进系统)")
        claims.append(Claim(claim_id=c["claim_id"], statement=c["statement"],
                            t0_evidence_ids=list(c.get("t0_evidence_ids", [])),
                            dimension=dim))
    return Docket(question=data["question"], claims=claims)


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
        # 教义表接线(规格 T6 实装债,#21):skills/*.md 从盘到场,启动时加载一次,
        # 逐会话注入角色系统提示;加载失败为 None,角色侧回退内联人格并落 skill_fallback 事件。
        self._doctrine: dict[str, str | None] = {
            "reverify": load_skill_body("reverify"),
            "devil_advocate": load_skill_body("devil_advocate"),
            "freshness_audit": load_skill_body("freshness_audit"),  # Auditor(#20/ADR-0009,#22 接线)
        }

    def _spawn_lead(self, claim: Claim):
        """构造 Lead 会话:教义表(reverify 为本会话主提示,devil_advocate 沿派驻链给 Critic,
        freshness_audit 沿自动触发链给 Auditor)。"""
        from freshlatch.roles.lead import LeadReverifier  # 延迟导入避免环

        return LeadReverifier(self.ctx, claim, self.llm,
                              doctrine=self._doctrine.get("reverify"),
                              critic_doctrine=self._doctrine.get("devil_advocate"),
                              auditor_doctrine=self._doctrine.get("freshness_audit"))

    def run(self, claims: list[Claim], *, trajectory_dir: str | Path = "reports/trajectories") -> RunResult:
        decisions: dict[str, ClaimDecision] = {}
        steps_by_claim: dict[str, int] = {}
        for claim in claims:
            lead = self._spawn_lead(claim)
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
                         decoding=self.ctx.decoding,
                         retrieve_zero_hits=list_retrieve_zero_hits(self.ctx.events))

    def _finalize(self, claim: Claim, decision: ClaimDecision) -> None:
        """判定落档:Agent 不得拥有放行权——fresh/stale 必须过规则闸,闸打回落 unknown。

        双判一致仲裁(ADR-0009 fresh 请求行 / ADR-0010 mark_stale 路径表,单一真相在
        gates/rule_gate.py 的 arbitrate_* 纯函数):fresh × Auditor stale → stale 落档;
        fresh × unknown/缺席 → unknown;mark_stale × 维度异议 → unknown + 异议记录;
        mark_stale × Auditor fresh → stale + 异议记录。Auditor 无任何路径把状态改绿。
        """
        from freshlatch.gates.rule_gate import (
            ERR_DIMENSION_CROSSCHECK_MISMATCH,
            GateContext,
            GateDecision,
            arbitrate_fresh,
            arbitrate_stale_mark,
            rule_gate,
        )
        claim.reason = decision.reason
        claim.t1_evidence_ids = decision.evidence_ids
        gate_ctx = GateContext(invalidation_list=self.ctx.invalidation_list,
                               checksum_fn=self._checksum_fn, eval_mode=(self.ctx.mode == "eval"))

        def _gate_decision(status: str, *, stale_reason: str = "") -> GateDecision:
            # auditor 三字段随判定包一次搬运(双判一致的闸输入,ADR-0009/0010);
            # 维度两字段(ADR-0011):登记维度来自签发卷宗,反证维度来自 mark_stale 必填字段
            return GateDecision(status=status, t1_evidence_ids=decision.evidence_ids,
                                stale_reason=stale_reason,
                                auditor_verdict=decision.auditor_verdict,
                                auditor_dimension_match=decision.auditor_dimension_match,
                                registered_dimension=claim.dimension,
                                stale_dimension=decision.stale_dimension)

        def _gate_back(reason_text: str) -> None:
            claim.status = "unknown"
            claim.reason = (f"[闸打回:{gate.error_code}] {gate.reason}; "
                            f"原理由: {reason_text}")

        if decision.status == "fresh":
            routed = arbitrate_fresh(decision.auditor_verdict)
            if routed == "fresh":
                gate = rule_gate(claim, _gate_decision("fresh"), gate_ctx)
                if gate.green:
                    claim.status = "fresh"
                else:
                    _gate_back(decision.reason)
            elif routed == "stale":
                # Auditor 推翻 Lead 的 fresh:按 stale 落档链过闸(Auditor 理由作 stale_reason);
                # 不变量 7 优先:dimension_match=False 时 DIMENSION_MISMATCH 打回 unknown
                gate = rule_gate(claim, _gate_decision("stale", stale_reason=decision.auditor_reason),
                                 gate_ctx)
                if gate.allowed:
                    claim.status = "stale"
                    claim.reason = f"[Auditor 双判推翻 Lead fresh] {decision.auditor_reason}"
                else:
                    _gate_back(decision.reason)
            else:
                claim.status = "unknown"
                basis = (f"Auditor 判 {decision.auditor_verdict}" if decision.auditor_verdict
                         else "Auditor 缺席(fail-closed)")
                claim.reason = (f"[双判未一致] Lead fresh × {basis}: "
                                f"{decision.auditor_reason or decision.reason}")
        elif decision.status == "stale":
            gate = rule_gate(claim, _gate_decision("stale", stale_reason=decision.reason), gate_ctx)
            if gate.allowed:
                claim.status = "stale"
            else:
                _gate_back(decision.reason)
            # 异议记录(ADR-0009 §3 / ADR-0010):Auditor 反对 Lead 的 stale 时结构化挂卡。
            # 闸因无关原因(如元陈述)打回时异议照挂:status 已落 unknown,异议是给人审的
            # 合法输入(「机器拒了这条 stale,且 Auditor 认为主张仍成立」),两 ADR 均未禁止。
            _, dissent = arbitrate_stale_mark(decision.auditor_verdict,
                                              decision.auditor_dimension_match)
            if dissent:
                claim.dissent = {"kind": "auditor_semantic",
                                 "auditor_verdict": decision.auditor_verdict,
                                 "reason": decision.auditor_reason,
                                 "evidence_ids": list(decision.evidence_ids)}
            elif gate.error_code == ERR_DIMENSION_CROSSCHECK_MISMATCH:
                # ADR-0011 不变量 8:机械跨检打回,异议 = 纯结构比对事实(零模型意见),
                # 复用 arbitrate_stale_mark 异议形态(随黄卡进 HumanLatch)
                claim.dissent = {"kind": "mechanical_crosscheck",
                                 "auditor_verdict": decision.auditor_verdict,
                                 "reason": (f"[机械跨检] 登记维度 {claim.dimension} ≠ "
                                            f"反证自标维度 {decision.stale_dimension}"
                                            "(纯字符串比对,零模型意见;ADR-0011 不变量 8)"),
                                 "evidence_ids": list(decision.evidence_ids)}
        else:
            claim.status = "unknown"
            if decision.dimension_objection and not claim.dissent:
                # ADR-0012:受理层维度预检打回后 Lead 未显式收口(soft_close 兜底
                # 或未过双判),机械比对异议照挂——异议记录是黄卡进 HumanLatch 的
                # 合法输入,不因拦截点上移而断供(登记维度值仍不披露)。
                obj = decision.dimension_objection
                claim.dissent = {"kind": "mechanical_precheck",
                                 "auditor_verdict": decision.auditor_verdict,
                                 "reason": (f"[机械跨检预检 ADR-0012] 反证自标维度 "
                                            f"{obj['stale_dimension']} ≠ 签发登记维度"
                                            "(值不披露),mark_stale 未受理、零 Auditor 调用;"
                                            "Lead 未显式收口,路由 unknown"),
                                 "evidence_ids": list(obj.get("evidence_ids", []))}
        self.ctx.emit({"type": "claim_result", "claim_id": claim.claim_id,
                       "status": claim.status, "reason": claim.reason,
                       "auditor_verdict": decision.auditor_verdict})

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
                                    "reason": d.reason, "evidence_ids": d.evidence_ids,
                                    "auditor_verdict": d.auditor_verdict,
                                    "dissent": c.dissent,
                                    "schema_version": EVIDENCE_PACKET_SCHEMA_VERSION},
                                   ensure_ascii=False) + "\n")
