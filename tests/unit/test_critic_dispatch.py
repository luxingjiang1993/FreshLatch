"""Critic 动态派驻单测(§6.3 / §3.4 / §7.3 P5):白名单、focus 硬校验、激励隔离、预算、结论回吐。

全部走脚本化假 LLM 与 InMemoryStore——零网络、零真模型(CI gate 1 语义,ADR-0005)。
"""

import json
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import BUDGET_EXHAUSTED_MESSAGE, Guardrails
from freshlatch.models import Claim
from freshlatch.roles.critic import FINDING_NOT_REPORTED, Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.roles.loop import run_loop
from freshlatch.runner import RunContext
from freshlatch.store.base import Chunk, InMemoryStore
from freshlatch.tools import CRITIC_TOOLS, FOCUS_DIMENSIONS, tool_specs

EVIDENCE_ID = "t1-pricing#p2@T1"
FINDING_TEXT = "找到反证:T1 定价条款写明价格调整,推翻了主张的签发时定价前提,见 t1-pricing#p2@T1"
STALE_REASON = "T1 原文明确写明专业版定价已调整,直接推翻了主张签发时的定价数字前提。"

_tc_counter = 0


def _tc(name, args):
    """构造一个 OpenAI tool_call 形状的消息段(幂等 id 递增)。"""
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_{_tc_counter}", type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
    )


class _Msg:
    """假 assistant 消息:chat() 返回值,带 model_dump(循环要落 messages)。"""

    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        d = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in self.tool_calls
            ]
        return d


class _ScriptLLM:
    """按 FIFO 脚本回吐消息;脚本项可为消息或可调用 (messages, tools) -> 消息。

    每次调用记录 (messages, tools) 到 calls——激励隔离断言靠它抓 Critic 会话内容。
    """

    def __init__(self, script):
        self._script = list(script)
        self.calls = []

    def chat(self, messages, *, tools=None, decoding=None):
        self.calls.append((list(messages), tools))  # 存副本:循环会原地 append,引用会失真
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _mk_chunk(doc_id: str, text: str, clause_id: str = "p2") -> Chunk:
    return Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-c1", clause_id=clause_id, title="t",
                 text=text, source_type="public", as_of="T1", doc_version="v2",
                 checksum="", tokens=20)


def _store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t1-pricing", as_of="T1", source_type="public",
                        title="T1 定价页", doc_version="v2", checksum="", full_text="定价调整全文"),
        # 语料需 ≥3 篇:单篇池 BM25 idf 为负、score>0 过滤会把命中也滤掉(pipeline 已知行为)
        [_mk_chunk("t1-pricing", "专业版定价已调整,自 T1 起按新价格执行,旧定价不再适用。"),
         _mk_chunk("t1-interview", "访谈纪要:客户反馈交付周期延长,服务响应变慢。"),
         _mk_chunk("t1-market", "市场结构观察:渠道集中度上升,长尾玩家出清。")],
    )
    return store


def _claim() -> Claim:
    return Claim(claim_id="c1", statement="专业版定价 299 元/席/月",
                 t0_evidence_ids=["t0-pricing#p1@T0"])


def _ctx(store=None, guardrails=None) -> RunContext:
    return RunContext(store=store or InMemoryStore(),
                      guardrails=guardrails or Guardrails())


def _critic_calls(llm: _ScriptLLM):
    """从假 LLM 记录里抓 Critic 会话(系统消息含反对派人格)的全部调用。"""
    return [(m, t) for (m, t) in llm.calls
            if m and "反对派复验员" in str(m[0].get("content", ""))]


# -- 合法派驻全流程 ----------------------------------------------------------------

def test_spawn_valid_focus_finding_reported_back():
    """P5 冒烟主路径:Lead retrieve → spawn_critic(合法 focus)→ Critic 找反证 → 结论回吐 Lead。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "competitor_pricing"})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"reason": STALE_REASON, "evidence_ids": [EVIDENCE_ID]})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": FINDING_TEXT})]),
        _Msg(content="报告完毕"),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm)
    lead.run()

    spawn_events = [e for e in ctx.events if e.get("type") == "critic_spawn"]
    result_events = [e for e in ctx.events if e.get("type") == "critic_result"]
    assert len(spawn_events) == 1 and spawn_events[0]["focus"] == "competitor_pricing"
    assert result_events[0]["counter_evidence_ids"] == [EVIDENCE_ID]

    # 结论回吐 Lead:spawn_critic 的工具观察里带 finding
    spawn_steps = [e for e in ctx.events
                   if e.get("type") == "lead_step" and e.get("tool") == "spawn_critic"]
    out = spawn_steps[0]["result"]
    assert out["reported_by"] == "critic"
    assert out["finding"] == FINDING_TEXT
    assert out["counter_evidence_ids"] == [EVIDENCE_ID]
    assert out["stale_reason"] == STALE_REASON  # Critic 的「判死」语义随结论一并回吐

    # Critic 步数走自己的预算(critic_max_steps=8 内),遥测事件落 ctx.events(进轨迹 JSONL)
    critic_steps = [e for e in ctx.events if e.get("type") == "critic_step"]
    assert critic_steps and all(e["claim_id"] == "c1" for e in critic_steps)


def test_spawn_incentive_isolation():
    """激励隔离:新会话(消息历史不共享),只传「主张原文 + focus + 相关 evidence_id 列表」。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "regulatory_stance"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "按监管口径方向未见推翻性 T1 证据"})]),
        _Msg(content="报告完毕"),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    LeadReverifier(ctx, _claim(), llm).run()

    critic_msgs = [m for (m, _t) in _critic_calls(llm)]
    assert critic_msgs, "Critic 应至少有派驻后的首轮调用"
    first = critic_msgs[0]
    assert len(first) == 2  # 全新会话:只有 system + user,不挂 Lead 的 messages 历史
    system, task = first[0]["content"], first[1]["content"]
    assert "作废名单" not in system  # Lead 侧上下文(作废/隔离名单)不过境
    assert "签发时(T0)证据" not in task  # Lead 的任务文本不过境
    assert "专业版定价 299 元/席/月" in task  # 主张原文过境
    assert "regulatory_stance" in system  # focus 过境(在人格行)
    assert EVIDENCE_ID in task  # 相关 evidence_id 列表过境


def test_spawn_focus_omitted_means_unbounded():
    """focus 省略 = 不限方向(§3.4:不设占位枚举值),是合法调用。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("spawn_critic", {})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "全语料未见推翻性 T1 证据"})]),
        _Msg(content="报告完毕"),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    LeadReverifier(ctx, _claim(), llm).run()
    spawn_events = [e for e in ctx.events if e.get("type") == "critic_spawn"]
    assert len(spawn_events) == 1 and spawn_events[0]["focus"] is None


# -- focus 硬校验 + 重试计步(#14)----------------------------------------------------

def test_spawn_invalid_focus_rejected_with_vocab():
    """非法 focus:整个调用被拒,错误回列全部 6 个合法值(§3.4 决策三)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "价格战"})]),
        _Msg(content="放弃派驻"),
    ])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm)
    lead.run()

    spawn_steps = [e for e in ctx.events
                   if e.get("type") == "lead_step" and e.get("tool") == "spawn_critic"]
    err = spawn_steps[0]["result"]["error"]
    for slug in FOCUS_DIMENSIONS:
        assert slug in err
    assert "不限方向" in err
    assert not [e for e in ctx.events if e.get("type") == "critic_spawn"], "非法值不得触发派驻"


def test_retry_consumes_lead_step_budget():
    """重试计步:每次重试消耗 Lead 步数预算;预算耗尽注入软收尾,不硬断(#14)。"""
    script = [
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "价格战"})]),
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "品牌舆情"})]),
        _Msg(content="预算耗尽,基于现有证据下结论"),
    ]
    llm = _ScriptLLM(script)
    lead = LeadReverifier(_ctx(_store(), Guardrails(lead_max_steps=2)), _claim(), llm)
    lead.run()
    assert lead.steps_used == 2  # 两次(非法)调用各占一步——穷举撞词表等于烧预算
    loop_ends = [e for e in lead.ctx.events if e.get("type") == "lead_loop_end"]
    assert loop_ends[0]["finished"] is False  # 未自发收尾,靠软收尾兜底
    # 软收尾 = 预算归零后最后一次无工具调用(tools=None)
    assert llm.calls[-1][1] is None


def test_loop_soft_close_injected_at_budget_zero():
    """循环层:步数预算归零注入软收尾系统消息,最后再做一次无工具调用(护栏管天花板,不管结论)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价"})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价"})]),
        _Msg(content="软收尾后的最终结论"),
    ])

    def execute(name, args):
        return {"blocks": []}

    result = run_loop(system="s", task="t", tools=tool_specs(["retrieve"]),
                      execute=execute, chat=llm.chat, max_steps=2,
                      soft_close=BUDGET_EXHAUSTED_MESSAGE)
    assert result.steps_used == 2 and result.finished is False
    system_msgs = [m for m in result.messages if m.get("role") == "system"]
    assert BUDGET_EXHAUSTED_MESSAGE in [m.get("content") for m in system_msgs]
    assert result.tool_trace[-1]["tool"] == "__soft_close__"


# -- 深度恒 1 与只许判死 ------------------------------------------------------------

def test_depth_one_no_spawn_tool():
    """深度恒 1(硬约束):Critic 白名单无 spawn 工具;物理调用直接 fail-closed。"""
    names = [t["function"]["name"] for t in tool_specs(list(CRITIC_TOOLS))]
    assert "spawn_critic" not in names
    critic = Critic(_ctx(), _claim(), _ScriptLLM([]))
    with pytest.raises(RuntimeError):
        critic._execute("spawn_critic", {})


def test_critic_cannot_release_or_fresh():
    """Critic 只许判死:无 reverify_claim(fail-closed),mark_stale 也只是记录候选反证。"""
    assert "reverify_claim" not in CRITIC_TOOLS
    critic = Critic(_ctx(), _claim(), _ScriptLLM([]))
    with pytest.raises(RuntimeError):
        critic._execute("reverify_claim", {"claim_id": "c1", "status": "fresh"})
    out = critic._execute("mark_stale", {"reason": STALE_REASON, "evidence_ids": []})
    assert "error" in out  # 空证据 id 拒收:反证必须可点回


def test_critic_report_finding_single_exit():
    """report_finding 是唯一出口:回吐后一切工具调用被拒。"""
    critic = Critic(_ctx(), _claim(), _ScriptLLM([]))
    out = critic._execute("report_finding", {"finding": FINDING_TEXT})
    assert out["reported"] is True
    after = critic._execute("retrieve", {"query": "定价"})
    assert "error" in after and "派驻已结束" in after["error"]


# -- Critic 侧校验 -----------------------------------------------------------------

def test_critic_counter_evidence_whitelist():
    """Critic 反证证据同样逐字白名单 + 必须锚 T1(#16 同款约束)。"""
    critic = Critic(_ctx(), _claim(), _ScriptLLM([]))
    unseen = critic._execute("mark_stale", {"reason": STALE_REASON, "evidence_ids": ["d#p9@T1"]})
    assert "未检索到" in unseen["error"]
    critic._seen_evidence.add("d#p1@T0")
    not_t1 = critic._execute("mark_stale", {"reason": STALE_REASON, "evidence_ids": ["d#p1@T0"]})
    assert "@T1" in not_t1["error"]
    short = critic._execute("mark_stale", {"reason": "定价变了", "evidence_ids": ["d#p1@T1"]})
    assert "20 字" in short["error"]
    critic._seen_evidence.add("d#p1@T1")
    ok = critic._execute("mark_stale", {"reason": STALE_REASON, "evidence_ids": ["d#p1@T1"]})
    assert "recorded_counter_evidence" in ok


def test_critic_budget_independent_guardrail():
    """Critic 走 critic_max_steps(默认 8),与 Lead 预算互相独立;耗尽软收尾。

    未走 report_finding 的出口时,结论位只给固定「未交结论」标记——
    软收尾的 assistant 自由文本不得冒充 Critic 结论(§3.3 唯一出口)。
    """
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "价格", "as_of": "T1"})]),
        _Msg(content="预算耗尽,基于现有证据未发现推翻性内容"),
    ])
    ctx = _ctx(_store(), Guardrails(lead_max_steps=18, critic_max_steps=2))
    critic = Critic(ctx, _claim(), llm)
    result = critic.run()
    assert result.steps_used == 2 and result.finished is False
    assert result.finding == FINDING_NOT_REPORTED


def test_retrieval_budget_shared_run_level():
    """Run 级共享检索预算:Lead 查多了 Critic 就剩得少;超限 fail-soft 不抛异常(§6.1)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("spawn_critic", {})]),
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "检索预算已尽,改用 read_source 后未见推翻性证据"})]),
        _Msg(content="报告完毕"),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store(), Guardrails(retrieval_budget=1))
    LeadReverifier(ctx, _claim(), llm).run()
    critic_retrieve = [e for e in ctx.events
                       if e.get("type") == "critic_step" and e.get("tool") == "retrieve"]
    assert critic_retrieve[0]["result"]["budget_exhausted"] is True
    assert ctx.retrieval_used == 1  # 计数不越界


# -- §6.4 结构化轨迹断言 ------------------------------------------------------------

def test_trajectory_lead_step_n_calls_retrieve():
    """「Lead 第 N 圈应调 retrieve」式断言:tool_trace 逐步落盘,步数与工具可对账。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="完成"),
    ])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm)
    lead.run()
    steps = [e for e in ctx.events if e.get("type") == "lead_step"]
    assert steps[0]["step"] == 1 and steps[0]["tool"] == "retrieve"
    assert steps[1]["tool"] == "finish_reverify"
    assert steps[0]["result"]["blocks"][0]["evidence_id"] == EVIDENCE_ID
