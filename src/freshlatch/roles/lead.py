"""Lead Reverifier:真 Agent,裸 ReAct 循环,逐轮自主决定下一步。

上下文只装:主张 + 最近检索块 + 作废名单(§2.8);不装全部语料,不做上下文压缩。
W1 人格为内联最小版;skills/reverify/SKILL.md(T6)落盘后由 Runner 注入替换。
"""

from __future__ import annotations

from freshlatch.models import Claim
from freshlatch.roles.loop import LoopResult, run_loop
from freshlatch.runner import ClaimDecision, RunContext
from freshlatch.tools import LEAD_TOOLS_W1, tool_specs

LEAD_PERSONA_W1 = """你是 Lead Reverifier,FreshLatch 的复验主官。你的任务是把一条已签发主张从「曾经为真」改成「现在仍可复验」。

工作方式(裸 ReAct,逐轮决策,无全程计划):
1. 先用 retrieve 在 T1(复验时刻快照)检索与主张相关的证据块;必要时 read_source 读原文全文兜底。
2. 如需对照签发时口径,可再查 T0,但判定 ground truth 永远是 T1 原文。
3. T1 的复测/核实内容直接支持主张的每个前提 → reverify_claim(claim_id, "fresh", [t1 evidence_id...])。
   注意:判 fresh 必须给出 T1 证据 id,否则会被规则闸打回。
4. T1 原文明确推翻主张 → mark_stale(claim_id, reason),reason 必须含显式因果句:指出 T1 原文哪一句推翻了主张的哪个前提,不得只写「与最新文档不符」。
   注意:只有 T1 出现明确的推翻性内容时才判 stale;T1 只说「未复测/无新数据/待发布/未入账」是证据缺口,不是推翻——走 mark_gap + unknown,不得判 stale。
5. T1 无原文覆盖或证据不足 → mark_gap(description) 后 reverify_claim(claim_id, "unknown", [])。
6. 完成或无路可走 → finish_reverify()。

纪律:
- 作废名单里的主张已被人工作废,不要试图把它改回 fresh,闸会打回。
- 你没有联网工具,不要臆造 T1 之外的信息。
- 每条主张只下一次判定。"""

MAX_EVIDENCE_IN_CONTEXT = 3  # 最近检索块只装最近 3 条,不装全部语料


class LeadReverifier:
    def __init__(self, ctx: RunContext, claim: Claim, llm) -> None:
        self.ctx = ctx
        self.claim = claim
        self.llm = llm
        self.steps_used = 0
        self.decision = ClaimDecision(claim_id=claim.claim_id)
        self._recent_blocks: list[str] = []
        self._finished = False

    def run(self) -> ClaimDecision:
        self.ctx.gaps = []  # 缺口按主张隔离,禁止跨主张渗漏
        system = self._build_system()
        task = self._build_task()
        tools = tool_specs(list(LEAD_TOOLS_W1))
        loop: LoopResult = run_loop(
            system=system, task=task, tools=tools,
            execute=self._execute,
            chat=lambda msgs, tools=None: self.llm.chat(msgs, tools=tools, decoding=self.ctx.decoding),
            max_steps=self.ctx.guardrails.lead_max_steps,
            soft_close=self.ctx.guardrails.exhausted_soft_close(),
            on_event=lambda ev: self.ctx.emit({"type": "lead_step", "claim_id": self.claim.claim_id, **ev}),
        )
        self.steps_used = loop.steps_used
        self.ctx.emit({"type": "lead_loop_end", "claim_id": self.claim.claim_id,
                       "steps_used": loop.steps_used, "finished": loop.finished})
        if not self.decision.reason and self.decision.status == "unknown":
            self.decision.reason = "证据不足,未下结论(unknown)"
        if not self.decision.reason:
            # fresh 判定模型通常把理由写在工具调用前的 assistant 文本里,抓回作落档理由
            for m in reversed(loop.messages):
                if m.get("role") == "assistant" and m.get("content"):
                    self.decision.reason = str(m["content"])[:500]
                    break
        return self.decision

    # -- 上下文装配 -----------------------------------------------------------

    def _build_system(self) -> str:
        voided = sorted(self.ctx.invalidation_list)
        void_line = f"作废名单(人工已作废,不得改回 fresh): {', '.join(voided) if voided else '(空)'}"
        return f"{LEAD_PERSONA_W1}\n\n{void_line}"

    def _build_task(self) -> str:
        ev = ", ".join(self.claim.t0_evidence_ids) or "(无)"
        return (
            f"待复验主张 {self.claim.claim_id}: {self.claim.statement}\n"
            f"签发时(T0)证据: {ev}\n"
            "请按工作方式逐轮复验,最终以工具落判定。"
        )

    # -- 工具执行(fail-closed:只挂白名单内的可调用)----------------------------

    def _execute(self, name: str, args: dict) -> dict:
        handler = {
            "retrieve": self._t_retrieve,
            "read_source": self._t_read_source,
            "reverify_claim": self._t_reverify_claim,
            "mark_stale": self._t_mark_stale,
            "mark_gap": self._t_mark_gap,
            "finish_reverify": self._t_finish,
        }.get(name)
        if handler is None:  # fail-closed,理论上 tool_specs 已拦截
            raise RuntimeError(f"未允许的工具: {name}")
        return handler(args)

    def _t_retrieve(self, args: dict) -> dict:
        as_of = args.get("as_of") or None
        if as_of not in (None, "T0", "T1"):
            return {"error": f"as_of 只能是 T0|T1,收到: {as_of}"}
        hits = self.ctx.try_retrieve(
            args["query"],
            source_type=args.get("source_type") or None,
            as_of=as_of,  # 已在上方校验 ∈ {None,"T0","T1"}
            top_k=10,  # §8.5:top_k 放宽到 10 缓释同义改写漏召回
        )
        if isinstance(hits, dict):  # 预算已尽,fail-soft
            return hits
        blocks = [
            {"evidence_id": f"{c.doc_id}#{c.clause_id}", "as_of": c.as_of,
             "source_type": c.source_type, "text": c.text}
            for c in hits
        ]
        self._recent_blocks = [b["evidence_id"] for b in blocks[-MAX_EVIDENCE_IN_CONTEXT:]]
        return {"blocks": blocks, "retrieval_used": self.ctx.retrieval_used}

    def _t_read_source(self, args: dict) -> dict:
        as_of = args.get("as_of", "T1")
        if as_of not in ("T0", "T1"):
            return {"error": f"as_of 只能是 T0|T1,收到: {as_of}"}
        text = self.ctx.store.read_source(args["doc_id"], as_of=as_of)
        if text is None:
            return {"error": f"未找到文档 {args['doc_id']} 的 {as_of} 快照"}
        return {"doc_id": args["doc_id"], "as_of": as_of, "full_text": text}

    def _t_reverify_claim(self, args: dict) -> dict:
        status = args.get("status")
        if status not in ("fresh", "stale", "unknown"):
            return {"error": f"status 只能是 fresh|stale|unknown,收到: {status}"}
        if args.get("claim_id") != self.claim.claim_id:
            return {"error": f"claim_id 只能是 {self.claim.claim_id}"}
        evidence_ids = [str(e) for e in args.get("evidence_ids") or []]
        if status == "fresh" and not evidence_ids:
            return {"error": "判 fresh 必须给出 t1 evidence_ids(规则闸强制)"}
        if status == "stale":
            return {"error": "stale 请用 mark_stale(必须含显式因果句)"}
        self.decision.status = status
        self.decision.evidence_ids = evidence_ids
        if status == "unknown" and self.ctx.gaps:
            self.decision.reason = "缺口: " + "; ".join(self.ctx.gaps)
        return {"recorded": {"claim_id": self.claim.claim_id, "status": status,
                             "evidence_ids": evidence_ids},
                "note": "fresh 需经规则闸,闸打回将落 unknown"}

    def _t_mark_stale(self, args: dict) -> dict:
        if args.get("claim_id") != self.claim.claim_id:
            return {"error": f"claim_id 只能是 {self.claim.claim_id}"}
        reason = args.get("reason", "").strip()
        if len(reason) < 20:
            return {"error": "reason 必须含显式因果句(指出 T1 原文哪一句推翻了哪个前提),不能少于 20 字"}
        self.decision.status = "stale"
        self.decision.reason = reason
        return {"recorded": {"claim_id": self.claim.claim_id, "status": "stale", "reason": reason}}

    def _t_mark_gap(self, args: dict) -> dict:
        desc = args.get("description", "").strip()
        if not desc:
            return {"error": "description 不能为空"}
        self.ctx.gaps.append(desc)
        return {"recorded_gap": desc}

    def _t_finish(self, args: dict) -> dict:
        self._finished = True
        return {"finished": True}
