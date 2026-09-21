"""Lead Reverifier:真 Agent,裸 ReAct 循环,逐轮自主决定下一步。

上下文只装:主张 + 最近检索块 + 作废名单(§2.8);不装全部语料,不做上下文压缩。
人格双轨(#21 接线后):系统提示主份 = skills/reverify/SKILL.md 教义表(Runner 注入,
规格 T6 实装债补齐);内联 LEAD_PERSONA 为加载失败兜底 + 一句指向教义表(不复制铁律
全文,防双拷贝漂移)。教义表缺失时的回退落 skill_fallback 事件,不静默降级——
「在盘不在场」正是 c5/c6 事故根因(#19 评估文档事实 1)。
W3 起白名单含 spawn_critic:动态派驻 Critic 专找反证(§6.3),Critic 结论只作参考,判定仍由 Lead 下。
"""

from __future__ import annotations

from freshlatch.evidence import check_evidence_ids, valid_as_of
from freshlatch.gates.meta_gate import META_ONLY_MESSAGE, is_meta_only_disproof
from freshlatch.models import Claim
from freshlatch.roles.auditor import Auditor
from freshlatch.roles.critic import Critic
from freshlatch.roles.loop import LoopResult, run_loop
from freshlatch.runner import ClaimDecision, RunContext
from freshlatch.tools import FOCUS_DIMENSIONS, LEAD_TOOLS_W3, tool_specs

LEAD_PERSONA = """你是 Lead Reverifier,FreshLatch 的复验主官。你的任务是把一条已签发主张从「曾经为真」改成「现在仍可复验」。

工作方式(裸 ReAct,逐轮决策,无全程计划):
1. 先用 retrieve 在 T1(复验时刻快照)检索与主张相关的证据块;必要时 read_source 读原文全文兜底。
2. 如需对照签发时口径,可再查 T0,但判定 ground truth 永远是 T1 原文。
3. T1 的复测/核实内容直接支持主张的每个前提 → reverify_claim(claim_id, "fresh", [t1 evidence_id...])。
   注意:判 fresh 必须给出 T1 证据 id(形如 doc#p2@T1),从 retrieve 结果里逐字引用,否则会被规则闸打回。
4. T1 原文明确推翻主张 → mark_stale(claim_id, reason, [t1 evidence_id...], dimension),reason 必须含显式因果句:指出 T1 原文哪一句推翻了主张的哪个前提,不得只写「与最新文档不符」;反证 id 必须逐字引用 retrieve 返回的 T1 证据 id,不得编造;dimension 必填,填本反证自身攻击的维度(6 枚举之一,非法值整 call 拒绝并回列词表)。
   注意:只有 T1 出现明确的推翻性内容时才判 stale;T1 只说「未复测/无新数据/待发布/未入账」是证据缺口,不是推翻——走 mark_gap + unknown,不得判 stale。
5. T1 无原文覆盖或证据不足 → mark_gap(description) 后 reverify_claim(claim_id, "unknown", [])。
6. 想对主张加压、专找「已死」反证 → spawn_critic(focus?):focus 可省略(=不限方向),只能填 6 个枚举值
   (competitor_pricing/regulatory_stance/interview_reversal/cost_model/market_structure/tech_ecosystem),
   填错整个调用被拒并回列词表,重试消耗你的步数预算。Critic 结论只是参考输入,判定与证据引用仍由你负责。
7. 完成或无路可走 → finish_reverify()。

纪律:
- 作废名单里的主张已被人工作废,不要试图把它改回 fresh,闸会打回。
- 你没有联网工具,不要臆造 T1 之外的信息。
- 每条主张只下一次判定。
- 引用反证后不得判 fresh:你在 reason 里把某段 T1 称为「反证/推翻/已过时/被取代」后,fresh 即被排除——那段就是 stale 的反证,走 mark_stale。
- 合取主张(「A 与 B」式)按签发原文整体判定:T1 明确推翻任一前提 ⇒ 整体 stale;其余前提未推翻或未复测,不构成判 fresh 的理由。
- fresh 的唯一含义是签发原文此刻仍成立;不得改验「主张的新版本」——被新事实取代或改写的主张是 stale,不是 fresh。
- 采纳 Critic 反证前必须独立核对其锚定的前提/度量维度与主张签发原文是否一致:主张讲成本,竞品定价/月费不是成本的反证(定价≠成本,属「无因果关系并列」式干扰);维度不符不得据此改判 stale,更不得未核对即镜像 Critic 框架下判定。
- 完整教义(「约束与纠正」对照表)单一真相在 skills/reverify/SKILL.md,正常由 Runner 整份注入本提示;若你未见该对照表,说明注入失败,仍须按本内联纪律执行。"""

# mark_stale 受理回执确定性携带的维度核对指令(#19 子决策 3):
# 事故路径(Lead 自主 mark_stale)三重硬校验无一与维度有关,本指令保证「核对在场」——
# 指令在场 ≠ 机器判维度(闸③不重开);词表随乙-i 干扰项同步扩充(客单价≠毛利、覆盖率≠渗透率)。
MARK_STALE_DIMENSION_NOTE = (
    "mark_stale 受理自查(每条必显,不依赖自觉):该反证锚定的前提/度量维度与主张签发原文是否一致?"
    "定价≠成本、客单价≠毛利、覆盖率≠渗透率等「无因果关系并列」不构成推翻;"
    "维度不符不得据此判 stale,应放弃本次判定并回到 T1 原文找同维度证据,或走 mark_gap + unknown。"
)


class LeadReverifier:
    def __init__(self, ctx: RunContext, claim: Claim, llm, *,
                 doctrine: str | None = None, critic_doctrine: str | None = None,
                 auditor_doctrine: str | None = None) -> None:
        self.ctx = ctx
        self.claim = claim
        self.llm = llm
        self._doctrine = doctrine  # reverify SKILL.md 正文(Runner 接线,#21);None=回退内联人格
        self._critic_doctrine = critic_doctrine  # 沿派驻链给 Critic(devil_advocate)
        self._auditor_doctrine = auditor_doctrine  # 沿自动触发链给 Auditor(freshness_audit,#22)
        self.steps_used = 0
        self.decision = ClaimDecision(claim_id=claim.claim_id)
        self._finished = False
        self._seen_evidence: set[str] = set()  # 本会话 retrieve 返回过的 evidence_id(#16 白名单)
        self._seen_blocks: dict[str, str] = {}  # evidence_id → 块文本(Auditor 证据包原料,#22)
        self._critic_spawned = False  # 本会话是否已派驻过 Critic(§8.5 checkpoint 去重)

    def run(self) -> ClaimDecision:
        self.ctx.gaps = []  # 缺口按主张隔离,禁止跨主张渗漏
        system = self._build_system()
        task = self._build_task()
        tools = tool_specs(list(LEAD_TOOLS_W3))
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
        quarantined = sorted(self.ctx.quarantine_list)
        void_line = f"作废名单(人工已作废,不得改回 fresh): {', '.join(voided) if voided else '(空)'}"
        quarantine_line = f"隔离名单: {', '.join(quarantined) if quarantined else '(空)'}"
        if self._doctrine:
            base = self._doctrine  # 教义表在场为主份(单一真相在 skills/reverify/SKILL.md)
        else:
            # 兜底:教义表加载失败仍须能跑,但绝不静默——事件落轨迹,内联人格有指向句
            self.ctx.emit({"type": "skill_fallback", "skill": "reverify",
                           "claim_id": self.claim.claim_id})
            base = LEAD_PERSONA
        return f"{base}\n\n{void_line}\n{quarantine_line}"

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
            "spawn_critic": self._t_spawn_critic,
            "finish_reverify": self._t_finish,
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
            as_of=as_of,
            top_k=10,  # §8.5:top_k 放宽到 10 缓释同义改写漏召回
        )
        if isinstance(hits, dict):  # 预算已尽,fail-soft
            return hits
        blocks = [
            {"evidence_id": f"{c.doc_id}#{c.clause_id}@{c.as_of}", "as_of": c.as_of,
             "source_type": c.source_type, "text": c.text}
            for c in hits
        ]
        self._seen_evidence.update(b["evidence_id"] for b in blocks)
        self._seen_blocks.update({b["evidence_id"]: b["text"] for b in blocks})
        # 「最近检索块」= messages 里最近的 tool 结果(§2.8:messages 单角色内只增不减),
        # 模型每轮基于最新观察决策,无需额外注入。
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

    def _check_evidence_ids(self, raw: object, *, require_t1: bool) -> tuple[list[str] | None, str | None]:
        """白名单校验(#16):id 必须逐字来自本会话 retrieve 返回;fresh/stale 引用的必须是锚 T1 的证据。"""
        return check_evidence_ids(raw, self._seen_evidence, require_t1=require_t1)

    def _t_reverify_claim(self, args: dict) -> dict:
        status = args.get("status")
        if status not in ("fresh", "stale", "unknown"):
            return {"error": f"status 只能是 fresh|stale|unknown,收到: {status}"}
        if args.get("claim_id") != self.claim.claim_id:
            return {"error": f"claim_id 只能是 {self.claim.claim_id}"}
        evidence_ids: list[str] = []
        checkpoint: dict | None = None
        audit: dict | None = None
        if status == "fresh":
            ids, err = self._check_evidence_ids(args.get("evidence_ids"), require_t1=True)
            if err:
                return {"error": f"判 fresh 必须给出锚 T1 的检索证据 id: {err}"}
            evidence_ids = ids or []
            checkpoint = self._auto_critic_checkpoint()  # §8.5:绿灯前反对派必须有一次发言机会
            audit = self._auto_auditor_checkpoint(path="fresh", reason="",
                                                  evidence_ids=evidence_ids)  # ADR-0009 双判
        else:
            evidence_ids = [str(e) for e in args.get("evidence_ids") or []]
        if status == "stale":
            return {"error": "stale 请用 mark_stale(必须含显式因果句)"}
        self.decision.status = status
        self.decision.evidence_ids = evidence_ids
        if status == "unknown" and self.ctx.gaps:
            self.decision.reason = "缺口: " + "; ".join(self.ctx.gaps)
        result = {"recorded": {"claim_id": self.claim.claim_id, "status": status,
                               "evidence_ids": evidence_ids},
                  "note": "fresh 需经规则闸(双判一致),闸打回将落 unknown"}
        if checkpoint:
            result["critic_checkpoint"] = checkpoint
        if audit:
            result["auditor_checkpoint"] = audit
        return result

    def _t_mark_stale(self, args: dict) -> dict:
        if args.get("claim_id") != self.claim.claim_id:
            return {"error": f"claim_id 只能是 {self.claim.claim_id}"}
        reason = args.get("reason", "").strip()
        if len(reason) < 20:
            return {"error": "reason 必须含显式因果句(指出 T1 原文哪一句推翻了哪个前提),不能少于 20 字"}
        if is_meta_only_disproof(reason):
            return {"error": f"mark_stale 打回: {META_ONLY_MESSAGE}"}
        ids, err = self._check_evidence_ids(args.get("evidence_ids"), require_t1=True)
        if err:
            return {"error": f"stale 必须给出可点回的 T1 反证 id(有效反证=可点回): {err}"}
        # ADR-0011:反证必填维度字段(问法=反证自身攻击的维度)。硬校验整段复刻 focus 形态:
        # 非法值整 call 拒绝、回列词表;每次重试消耗 Lead 步数预算(循环每轮计一步)。
        dimension = args.get("dimension")
        if dimension not in FOCUS_DIMENSIONS:
            return {"error": "dimension 只能是 %s 之一;收到: %r"
                              % ("/".join(FOCUS_DIMENSIONS), dimension)}
        # ADR-0010:受理(三重硬校验通过、落档之前)自动触发 Auditor 单轮判定——
        # 强制性住在触发器(c2 同构:自信地错恰是自愿派驻最不会触发的时刻)。
        audit = self._auto_auditor_checkpoint(path="stale", reason=reason,
                                              evidence_ids=ids or [])
        self.decision.status = "stale"
        self.decision.reason = reason
        self.decision.evidence_ids = ids or []
        self.decision.stale_dimension = dimension
        result = {"recorded": {"claim_id": self.claim.claim_id, "status": "stale",
                               "reason": reason, "evidence_ids": ids},
                  "note": MARK_STALE_DIMENSION_NOTE}
        if audit:
            result["auditor_checkpoint"] = audit
        return result

    def _t_mark_gap(self, args: dict) -> dict:
        desc = args.get("description", "").strip()
        if not desc:
            return {"error": "description 不能为空"}
        self.ctx.gaps.append(desc)
        return {"recorded_gap": desc}

    def _auto_critic_checkpoint(self) -> dict | None:
        """fresh 落判定前的强制反对派 checkpoint(§8.5 架构级对冲咬合)。

        事故背景:c2 三次运行 Lead 都逐字引用致死段落后自信地判 fresh,全程零 Critic 派驻——
        派驻由 LLM 自主决定时,「自信地错」恰是派驻最不会触发的时刻。故改为结构性触发:
        本会话未派驻过(人工或自动)则强制自动派驻一次;focus 不限方向——
        主张→维度映射表会漏掉干扰项,全语料找反证最稳。
        Critic 结论只作参考,判定仍由 Lead 下;此 checkpoint 保证反对派至少发言一次。
        """
        if self._critic_spawned:
            return None
        return self._spawn_critic(focus=None, auto=True)

    def _auto_auditor_checkpoint(self, *, path: str, reason: str,
                                 evidence_ids: list[str]) -> dict | None:
        """Auditor 结构性在场:fresh 路径(ADR-0009)与 mark_stale 路径(ADR-0010,#25)落档前
        自动触发单轮判定,与 _auto_critic_checkpoint 同点同构。

        触发器保证运行,规则闸保证不变量(fail-closed 兜底):Auditor 不可用/调用失败时
        不阻断本工具,verdict 缺席由规则闸 AUDITOR_ABSENT 打回——Auditor 缺席不构成
        任何绿格,也不构成任何 stale 落档。结论回吐工具观察,Lead 可见可改判。
        """
        if self.llm is None:
            return None
        self.ctx.emit({"type": "auditor_spawn", "claim_id": self.claim.claim_id,
                       "path": path, "auto": True})
        auditor = Auditor(self.llm, doctrine=self._auditor_doctrine)
        if auditor.using_fallback:  # 在盘不在场 = c5/c6 事故根因,不静默降级
            self.ctx.emit({"type": "skill_fallback", "skill": "freshness_audit",
                           "claim_id": self.claim.claim_id, "path": path})
        packet = auditor.build_packet(self.claim, lead_status=path, lead_reason=reason,
                                      lead_evidence_ids=evidence_ids,
                                      evidence_texts=self._seen_blocks)
        try:
            verdict = auditor.judge(packet, decoding=self.ctx.decoding)
        except Exception as e:  # 端点故障不炸主循环;缺席由闸 fail-closed
            self.ctx.emit({"type": "auditor_error", "claim_id": self.claim.claim_id,
                           "path": path, "error": f"{type(e).__name__}: {e}"})
            return None
        self.decision.auditor_verdict = verdict.status
        self.decision.auditor_reason = verdict.reason
        self.decision.auditor_dimension_match = verdict.dimension_match
        self.ctx.emit({"type": "auditor_verdict", "claim_id": self.claim.claim_id,
                       "path": path, "verdict": verdict.status,
                       "dimension_match": verdict.dimension_match})
        return {"verdict": verdict.status, "reason": verdict.reason,
                "dimension_match": verdict.dimension_match,
                "schema_version": verdict.schema_version}

    def _t_spawn_critic(self, args: dict) -> dict:
        """动态派驻(§6.3):同进程同步起全新循环实例;focus 调用边界硬校验,非法值回列词表。

        只传「主张原文 + focus + 相关 evidence_id 列表」——激励隔离 + 省 token + 评测可复现;
        每次重试消耗 Lead 步数预算(循环每轮计一步,#14)。Critic 结论回吐为工具观察,由 Lead 自行决定是否采纳。
        """
        focus = args.get("focus")
        if focus in (None, ""):
            focus = None  # 省略 = 不限方向(§3.4:不设占位枚举值)
        elif focus not in FOCUS_DIMENSIONS:
            return {"error": "focus 只能是 %s 之一,或省略(=不限方向);收到: %r"
                              % ("/".join(FOCUS_DIMENSIONS), focus)}
        return self._spawn_critic(focus, auto=False)

    def _spawn_critic(self, focus: str | None, *, auto: bool) -> dict:
        """派驻执行体:人工(_t_spawn_critic)与自动 checkpoint 共用;事件带 auto 标记可区分来源。"""
        self._critic_spawned = True
        self.ctx.emit({"type": "critic_spawn", "claim_id": self.claim.claim_id,
                       "focus": focus, "auto": auto})
        critic = Critic(self.ctx, self.claim, self.llm, focus=focus,
                        evidence_ids=sorted(self._seen_evidence),
                        doctrine=self._critic_doctrine)
        result = critic.run()
        self.ctx.emit({"type": "critic_result", "claim_id": self.claim.claim_id,
                       "focus": focus, "steps_used": result.steps_used,
                       "counter_evidence_ids": result.counter_evidence_ids})
        return {"reported_by": "critic", "focus": focus, "auto": auto,
                "finding": result.finding,
                "counter_evidence_ids": result.counter_evidence_ids,
                "stale_reason": result.stale_reason,
                "stale_dimension": result.stale_dimension,
                "note": "Critic 只找反证、不得放行;是否采纳由你基于本会话证据自行判定。"
                        "采纳其 mark_stale 前,先独立核对该反证是否锚在主张的同一前提/度量维度"
                        "(主张讲成本、反证给竞品定价=维度不符,属干扰项,不得据此改判 stale);"
                        "核对通过也要用你自己的 reason 与证据 id 落 mark_stale,不得镜像 Critic 框架"}

    def _t_finish(self, args: dict) -> dict:
        self._finished = True
        return {"finished": True}
