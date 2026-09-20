"""Critic:真 Agent,只找「主张已死」的反证,由 Lead 的 spawn_critic 同步派驻(§6.3)。

激励隔离:新会话(消息历史不共享)、换人格系统提示词、换白名单、换预算;
只收「主张原文 + focus + 相关 evidence_id 列表」,Lead 的思路与全过程 transcript 一律不过境。
白名单 CRITIC_TOOLS:无 spawn(深度恒 1)、无 reverify_claim(只许判死,物理上无法放行)。
与 Lead 共享 RunContext 的 Run 级检索预算:Lead 查多了 Critic 就剩得少(§6.1)。
人格为内联最小版;skills/devil_advocate/SKILL.md(T6)落盘后由 Runner 注入替换。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from freshlatch.evidence import check_evidence_ids, valid_as_of
from freshlatch.models import Claim
from freshlatch.roles.loop import run_loop
from freshlatch.tools import CRITIC_TOOLS, FOCUS_DIMENSIONS, tool_specs

FOCUS_ZH: dict[str, str] = dict(zip(
    FOCUS_DIMENSIONS,
    ("竞品价格", "监管口径", "访谈改口", "成本模型", "市场结构", "技术生态"),
))

CRITIC_PERSONA = """你是 Critic,FreshLatch 的反对派复验员,唯一任务是找出「这条主张已经死了」的反证。

工作方式(裸 ReAct,逐轮决策,无全程计划):
1. 用 retrieve 在 T1(复验时刻快照)按给定 focus 方向检索;必要时 read_source 读原文全文兜底。ground truth 永远是 T1 原文,不是 chunk。
2. 找到推翻性证据 → mark_stale(reason, [t1 evidence_id...]):reason 必须含显式因果句,指出 T1 原文哪一句推翻了主张的哪个前提,不得只写「与最新文档不符」;evidence_id 逐字引用本会话 retrieve 返回、以 @T1 结尾的 id,不得编造。
3. T1 只说「未复测/无新数据/待发布/未入账」是证据缺口,不是推翻,不得 mark_stale。
4. 结论只从 report_finding(finding) 回吐一次:找到反证时 finding 含因果句与证据 id;没找到时 finding 如实说明按 focus 方向检索后未见推翻性 T1 证据。

纪律:
- 只许判死,不许判活:你没有 reverify_claim,物理上无法放行。
- 反证必须锚在主张的同一前提/度量维度:主张讲成本,竞品定价/月费不构成成本的反证
  (定价≠成本,与「无因果关系并列」同类干扰);维度不符不得 mark_stale,
  应在 report_finding 如实说明该方向未见同维度推翻证据。
- 你没有任何 spawn 工具,不得派驻(深度恒 1)。
- report_finding 之后不再调用任何工具。"""

FINDING_NOT_REPORTED = "Critic 步数预算耗尽,未交出 report_finding 结论。"  # 固定标记,不冒充结论(§3.3 唯一出口)


@dataclass
class CriticResult:
    finding: str = ""
    counter_evidence_ids: list[str] = field(default_factory=list)
    stale_reason: str = ""
    steps_used: int = 0
    finished: bool = False  # 模型自发收尾(报告后停手);预算耗尽软收尾为 False


class Critic:
    """一次派驻实例:全新循环(新会话/人格/白名单/预算),同步跑完回吐结论。"""

    def __init__(self, ctx, claim: Claim, llm, *, focus: str | None = None,
                 evidence_ids: list[str] | None = None) -> None:
        self.ctx = ctx
        self.claim = claim
        self.llm = llm
        self.focus = focus  # 封闭枚举 6 值之一,或 None=不限方向(Lead 侧已硬校验)
        self.evidence_ids = list(evidence_ids or [])
        self._seen_evidence: set[str] = set()  # 本会话 retrieve 白名单(#16 同款)
        self.result = CriticResult()

    def run(self) -> CriticResult:
        loop = run_loop(
            system=self._build_system(),
            task=self._build_task(),
            tools=tool_specs(list(CRITIC_TOOLS)),
            execute=self._execute,
            chat=lambda msgs, tools=None: self.llm.chat(msgs, tools=tools, decoding=self.ctx.decoding),
            max_steps=self.ctx.guardrails.critic_max_steps,
            soft_close=self.ctx.guardrails.exhausted_soft_close(),
            on_event=lambda ev: self.ctx.emit({"type": "critic_step", "claim_id": self.claim.claim_id, **ev}),
        )
        self.result.steps_used = loop.steps_used
        self.result.finished = loop.finished
        if not self.result.finding:
            # 软收尾兜底:未走 report_finding 的出口一律给固定标记——
            # 软收尾的 assistant 自由文本不是 Critic 结论,不得回吐冒充(§3.3 唯一出口、§6.1 护栏管天花板不管结论)。
            self.result.finding = FINDING_NOT_REPORTED
        return self.result

    # -- 上下文装配(只装主张原文 + focus + 相关 evidence_id 列表,§6.3)----------

    def _build_system(self) -> str:
        if self.focus:
            focus_line = f"本次派驻方向(focus): {self.focus}({FOCUS_ZH.get(self.focus, self.focus)})"
        else:
            focus_line = "本次派驻方向: 不限(未指定 focus),全语料找反证"
        return f"{CRITIC_PERSONA}\n\n{focus_line}"

    def _build_task(self) -> str:
        ids = ", ".join(self.evidence_ids) or "(无)"
        return (
            f"待找反证的主张 {self.claim.claim_id}: {self.claim.statement}\n"
            f"Lead 已检索到的相关 evidence_id(仅供点回核对;你的反证必须逐字来自本会话 retrieve 返回): {ids}\n"
            "请按工作方式逐轮找反证,结论只从 report_finding 回吐一次。"
        )

    # -- 工具执行(fail-closed;结论回吐后一切工具调用拒绝)------------------------

    def _execute(self, name: str, args: dict) -> dict:
        if self.result.finding:
            return {"error": "结论已从 report_finding 回吐,派驻已结束,不得再调用工具"}
        handler = {
            "retrieve": self._t_retrieve,
            "read_source": self._t_read_source,
            "mark_stale": self._t_mark_stale,
            "report_finding": self._t_report_finding,
        }.get(name)
        if handler is None:  # fail-closed,理论上 tool_specs 已拦截
            raise RuntimeError(f"未允许的工具: {name}")
        return handler(args)

    def _t_retrieve(self, args: dict) -> dict:
        try:
            as_of = valid_as_of(args.get("as_of"))
        except ValueError as e:
            return {"error": str(e)}
        hits = self.ctx.try_retrieve(
            args["query"],
            source_type=args.get("source_type") or None,
            as_of=as_of or None,
            top_k=10,
        )
        if isinstance(hits, dict):  # 预算已尽,fail-soft(与 Lead 共享 Run 级预算)
            return hits
        blocks = [
            {"evidence_id": f"{c.doc_id}#{c.clause_id}@{c.as_of}", "as_of": c.as_of,
             "source_type": c.source_type, "text": c.text}
            for c in hits
        ]
        self._seen_evidence.update(b["evidence_id"] for b in blocks)
        return {"blocks": blocks, "retrieval_used": self.ctx.retrieval_used}

    def _t_read_source(self, args: dict) -> dict:
        try:
            as_of = valid_as_of(args.get("as_of")) or "T1"
        except ValueError as e:
            return {"error": str(e)}
        text = self.ctx.store.read_source(args["doc_id"], as_of=as_of)
        if text is None:
            return {"error": f"未找到文档 {args['doc_id']} 的 {as_of} 快照"}
        return {"doc_id": args["doc_id"], "as_of": as_of, "full_text": text}

    def _t_mark_stale(self, args: dict) -> dict:
        """只许判死:候选反证落 result(连同 stale_reason 回吐 Lead),放行权永远在规则闸,不在 Critic。"""
        reason = args.get("reason", "").strip()
        if len(reason) < 20:
            return {"error": "reason 必须含显式因果句(指出 T1 原文哪一句推翻了哪个前提),不能少于 20 字"}
        ids, err = check_evidence_ids(args.get("evidence_ids"), self._seen_evidence, require_t1=True)
        if err:
            return {"error": f"mark_stale 必须给出可点回的 T1 反证 id(有效反证=可点回): {err}"}
        self.result.stale_reason = reason
        self.result.counter_evidence_ids = ids or []
        return {"recorded_counter_evidence": {"reason": reason, "evidence_ids": ids},
                "note": "反证已记录;最终是否采纳由 Lead 基于其本会话证据判定"}

    def _t_report_finding(self, args: dict) -> dict:
        finding = str(args.get("finding", "")).strip()
        if not finding:
            return {"error": "finding 不能为空"}
        self.result.finding = finding
        return {"reported": True, "note": "派驻结束,请勿再调用任何工具"}
