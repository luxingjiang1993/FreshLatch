"""c2 违例级修复回归(TDD 红灯先行):人格反模式口径 + fresh 前 Critic 强制 checkpoint + c2 轨迹原料守卫。

c2 事故形状(2026-09-20,基准+两次复现 3/3 确定性):Lead 逐字引用致死段落、自述「直接反证/已过时」,
然后以「合取主张只被推翻一支」为由判 fresh——检索正确、推理方向错。处置见 docs/evidence/w4/repro-check.md
背离二(§7.5 工程失败类,2 周修复窗口)。三层修复的结构断言:

1. 口径守卫:LEAD_PERSONA / skills/reverify/SKILL.md / verdict-rubric.md 三处落齐三条反模式
   (判定对象=签发原文,不得改验新版本;合取主张整体判定;引用反证后不得判 fresh);
2. 结构对冲:reverify_claim(fresh) 落判定前,本会话未派驻过 Critic ⇒ 强制自动派驻一次
   (§8.5 架构级对冲咬合;critic_spawn 事件带 auto 标记可与人工派驻区分);
3. 事故原料:c2 真实轨迹 fixture 可解析且事故形状(引反证后判 fresh)被钉住,防原料丢失。

结构断言 ≠ 模型行为证明;行为验收以 §7.5 窗口关闭的 n=3 活跑为准(冒烟框定,不报方差)。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.lead import LEAD_PERSONA, LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import InMemoryStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUBRIC = REPO_ROOT / "skills/freshness_audit/references/verdict-rubric.md"
SKILL = REPO_ROOT / "skills/reverify/SKILL.md"
# 复现2 的 c2 轨迹(三次违例运行之一,事故形状与基准/复现1 同构)
C2_FIXTURE = REPO_ROOT / "reports/trajectories/run-20260920-205643.jsonl"

# 三条反模式口径的关键词(实现落字后守卫,防日后改字漂移)
CLAUSE_ANTIPATTERN = "引用反证后不得判 fresh"
CLAUSE_CONJUNCTION = "合取主张"
CLAUSE_ORIGINAL = "签发原文"

MEMO_ID = "t0-regulatory-memo#p2@T1"
MEMO_TEXT = ("印尼通信部发布 PDP 法实施条例:面向印尼境内用户的在线客服对话日志须在印尼境内存储,"
             "2026 年 12 月 1 日起生效。泰国仅拟提出类似要求,尚未定稿。")
C2_STATEMENT = "印尼与泰国监管暂无客服数据本地化强制要求"
STALE_REASON = ("T1 原文明确印尼已发布 PDP 法实施条例,要求客服对话日志境内存储,"
                f"直接推翻『{C2_STATEMENT}』的印尼支前提,见 {MEMO_ID}")
FINDING_TEXT = f"找到反证:印尼 PDP 法实施条例推翻印尼支前提,见 {MEMO_ID}"

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
    """按 FIFO 脚本回吐消息;Lead/Critic/Auditor 共享同一脚本(FIFO 按调用顺序消费)。"""

    def __init__(self, script):
        self._script = list(script)

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        item = self._script.pop(0)
        return item(messages, tools) if callable(item) else item


def _aud(payload):
    """Auditor structured-output 响应(#22:fresh/mark_stale 钩子内自动触发,脚本须备位)。"""
    return _Msg(content=json.dumps(payload, ensure_ascii=False))


def _mk_chunk(doc_id: str, text: str, clause_id: str = "p2"):
    from freshlatch.store.base import Chunk
    return Chunk(doc_id=doc_id, chunk_id=f"{doc_id}-{clause_id}", clause_id=clause_id, title="t",
                 text=text, source_type="public", as_of="T1", doc_version="v2",
                 checksum="", tokens=20)


def _store() -> InMemoryStore:
    store = InMemoryStore()
    store.add_document(
        SimpleNamespace(doc_id="t0-regulatory-memo", as_of="T1", source_type="public",
                        title="监管备忘", doc_version="v2", checksum="", full_text=MEMO_TEXT),
        # 语料需 ≥3 篇:单篇池 BM25 idf 为负、score>0 过滤会把命中也滤掉(pipeline 已知行为)
        [_mk_chunk("t0-regulatory-memo", MEMO_TEXT),
         _mk_chunk("t0-regulatory-memo", "泰国监管动向:拟提出数据本地化咨询稿,尚未定稿。", "p3"),
         _mk_chunk("t0-side", "市场杂项:渠道集中度上升,与本主张无关。")],
    )
    return store


def _claim() -> Claim:
    return Claim(claim_id="c2", statement=C2_STATEMENT,
                 t0_evidence_ids=["t0-regulatory-memo#p2"])


def _ctx(store=None) -> RunContext:
    return RunContext(store=store or InMemoryStore(), guardrails=Guardrails())


def _lead_steps(ctx, tool):
    return [e for e in ctx.events if e.get("type") == "lead_step" and e.get("tool") == tool]


# -- 1. 口径守卫:三处文件落齐反模式 ---------------------------------------------------


@pytest.mark.parametrize("clause", [CLAUSE_ANTIPATTERN, CLAUSE_CONJUNCTION, CLAUSE_ORIGINAL])
def test_lead_persona_has_antipattern_clauses(clause):
    """内联人格(W1 最小版)必须携带三条反模式口径——c2 事故的直接补洞。"""
    assert clause in LEAD_PERSONA


@pytest.mark.parametrize("clause", [CLAUSE_ANTIPATTERN, CLAUSE_CONJUNCTION, CLAUSE_ORIGINAL])
def test_skill_md_syncs_antipattern_clauses(clause):
    """T6 落盘人格(SKILL.md,运行时替换内联版)与内联版同步;单一真相仍指 rubric,不复制定义。"""
    text = SKILL.read_text(encoding="utf-8")
    assert clause in text
    assert "verdict-rubric" in text  # 同步但不复制:完整定义唯一真相仍在 rubric


@pytest.mark.parametrize("clause", [CLAUSE_ANTIPATTERN, CLAUSE_CONJUNCTION, CLAUSE_ORIGINAL])
def test_verdict_rubric_has_direction_ironrules(clause):
    """三档判定单一真相(rubric)落方向铁律 + c2 反例,Lead/Critic 两侧引用防漂移。"""
    text = RUBRIC.read_text(encoding="utf-8")
    assert clause in text
    assert "c2" in text  # c2 类反例钉进干扰项正反例


# -- 2. 结构对冲:fresh 前 Critic 强制 checkpoint ---------------------------------------


def test_fresh_auto_spawns_critic_checkpoint_and_lead_can_revise():
    """§8.5 对冲咬合:本会话未派驻过 Critic 时,reverify_claim(fresh) 强制自动派驻一次。

    脚本复刻 c2 事故流程:Lead 检索致死段落 → 落 fresh(自动派驻同步跑 Critic,
    Critic 找到同一反证回吐)→ Lead 在工具观察里看到 checkpoint 后改判 mark_stale。
    """
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "印尼 数据本地化", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": "c2", "status": "fresh",
                                                 "evidence_ids": [MEMO_ID]})]),
        # —— 以下 4 条为自动派驻的 Critic 会话(FIFO 同步消费)——
        _Msg(tool_calls=[_tc("retrieve", {"query": "印尼 数据本地化", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"reason": STALE_REASON, "evidence_ids": [MEMO_ID],
                                             "dimension": "regulatory_stance"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": FINDING_TEXT})]),
        _Msg(content="报告完毕"),
        # —— Auditor 单轮判定(fresh 钩子内自动触发,#22/ADR-0009)——
        _aud({"status": "fresh", "reason": "证据包内未见推翻性表述"}),
        # —— Lead 看到 checkpoint 观察后改判 ——
        _Msg(tool_calls=[_tc("mark_stale", {"claim_id": "c2", "reason": STALE_REASON,
                                             "evidence_ids": [MEMO_ID], "dimension": "regulatory_stance"})]),
        # —— Auditor 单轮判定(mark_stale 钩子内自动触发,#22/ADR-0010)——
        _aud({"status": "stale", "reason": "反证成立,维度相符", "dimension_match": True}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm)
    decision = lead.run()

    # checkpoint 触发:一次且仅一次自动派驻,事件带 auto 标记、focus 不限方向
    spawns = [e for e in ctx.events if e.get("type") == "critic_spawn"]
    assert len(spawns) == 1
    assert spawns[0].get("auto") is True
    assert spawns[0]["focus"] is None

    # checkpoint 结论回吐进 fresh 的工具观察(Lead 下一轮可见,可改判)
    out = _lead_steps(ctx, "reverify_claim")[0]["result"]
    checkpoint = out.get("critic_checkpoint")
    assert checkpoint is not None, "fresh 落判定前必须附 Critic checkpoint 观察"
    assert checkpoint["counter_evidence_ids"] == [MEMO_ID]
    assert "印尼" in checkpoint["finding"]

    # Lead 改判生效:最终 stale 落档(模拟 c2 修复后的期望路径)
    assert decision.status == "stale"
    assert decision.evidence_ids == [MEMO_ID]


def test_no_auto_spawn_when_critic_already_spawned():
    """人工已派驻过 ⇒ fresh 不再重复自动派驻(不烧双倍预算)。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "印尼 数据本地化", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("spawn_critic", {"focus": "regulatory_stance"})]),
        _Msg(tool_calls=[_tc("report_finding", {"finding": "按监管口径方向未见推翻性 T1 证据"})]),
        _Msg(content="报告完毕"),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": "c2", "status": "fresh",
                                                 "evidence_ids": [MEMO_ID]})]),
        _aud({"status": "fresh", "reason": "证据包内未见推翻性表述"}),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    LeadReverifier(ctx, _claim(), llm).run()

    spawns = [e for e in ctx.events if e.get("type") == "critic_spawn"]
    assert len(spawns) == 1
    assert not spawns[0].get("auto"), "人工派驻不得带 auto 标记"
    out = _lead_steps(ctx, "reverify_claim")[0]["result"]
    assert "critic_checkpoint" not in out, "已派驻过则 fresh 不再附 checkpoint"


def test_no_auto_spawn_on_unknown_path():
    """非 fresh 落判定(unknown/stale)不触发 checkpoint——对冲只咬绿灯前。"""
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("mark_gap", {"description": "T1 未复测该指标,证据缺口"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": "c2", "status": "unknown"})]),
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    decision = LeadReverifier(ctx, _claim(), llm).run()
    assert decision.status == "unknown"
    assert not [e for e in ctx.events if e.get("type") == "critic_spawn"]


# -- 3. c2 事故原料守卫 -----------------------------------------------------------------


def test_c2_fixture_documents_bug_shape():
    """c2 真实轨迹(复现2)作回归原料:可解析、事故形状钉住(引反证后判 fresh)。

    fixture 缺失不硬失败(报告目录不入库),但本地存在时必须保持形状可断言。
    """
    if not C2_FIXTURE.exists():
        pytest.skip("c2 轨迹 fixture 不在本地(reports/ 不入库)")
    finals = [json.loads(ln) for ln in C2_FIXTURE.read_text(encoding="utf-8").splitlines()
              if json.loads(ln).get("type") == "claim_final"]
    assert len(finals) == 1
    final = finals[0]
    assert final["claim_id"] == "c2"
    assert final["status"] == "fresh", "fixture 记录的是修复前事故形状,不得改写历史"
    assert "反证" in final["reason"], "事故核心:自述反证后仍判 fresh"
    assert "印尼" in final["reason"] and "泰国" in final["reason"], "合取两支都在理由中"
