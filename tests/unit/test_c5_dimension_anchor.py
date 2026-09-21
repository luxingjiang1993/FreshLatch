"""c5 二修回归(TDD 红灯先行):度量维度锚定(① Critic 生产侧) + 采纳前独立核对(② Lead 消费侧)。

c5 事故形状(2026-09-20,修复后冒烟 run-223219):checkpoint 自动派驻的 Critic 把竞品门售价
(39 美元/月/店,定价维度)当作「我方单会话成本仍低于竞品」主张(成本维度)的反证 mark_stale
——维度混淆;Lead 未独立核对即镜像 Critic 框架改判,must_fresh 翻转。处置与拍板见
docs/evidence/w4/repro-check.md 背离三、docs/research/c5二修方向设计评估.md。

三层修复结构断言(与 c2 同款):
1. 口径守卫:Critic 人格 / Lead 人格 / verdict-rubric / SKILL.md 四处落齐「度量维度锚定」;
2. 结构注入:checkpoint/spawn 回吐 Lead 的观察强制带「采纳前独立核对维度对应」指令;
3. 事故原料:c5 真实轨迹 fixture 可解析且事故形状(定价当成本反证)被钉住,防原料丢失。

结构断言 ≠ 模型行为证明;行为验收以 §7.5 窗口关闭的 n=3 活跑为准(冒烟框定,不报方差)。
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.guardrails import Guardrails
from freshlatch.models import Claim
from freshlatch.roles.critic import CRITIC_PERSONA
from freshlatch.roles.lead import LEAD_PERSONA, LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import InMemoryStore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUBRIC = REPO_ROOT / "skills/freshness_audit/references/verdict-rubric.md"
SKILL = REPO_ROOT / "skills/reverify/SKILL.md"
GLOSSARY = REPO_ROOT / "CONTEXT.md"
# c5 事故轨迹(修复后冒烟,checkpoint 介导的维度混淆翻转;轨迹目录不入库,缺失则跳过)
C5_FIXTURE = REPO_ROOT / "reports/trajectories/run-20260920-223219.jsonl"

# 维度锚定口径的关键词(实现落字后守卫,防日后改字漂移)
CLAUSE_DIMENSION = "度量维度"
CLAUSE_COST_PRICE = "定价≠成本"
CLAUSE_INDEPENDENT_CHECK = "独立核对"

COST_DOC = "t0-cost-model"
COST_ID = f"{COST_DOC}#p2@T1"
COST_TEXT = ("T1 复测:我方单会话成本 0.009 美元,竞品折算约 0.019 美元,"
             "我方约为竞品的 47%,成本优势仍成立。")
COMPETITOR_ID = "t0-competitor-notes#p2@T1"
COMPETITOR_TEXT = "竞品 2026 年 7 月发布 Lite 版门店套餐,门售价 39 美元/月/店。"
C5_STATEMENT = "我方单会话成本仍低于竞品"
# Critic 的维度混淆反证(定价当成本)——事故形状复刻
CONFUSED_REASON = ("T1 原文显示竞品 Lite 版门售价 39 美元/月/店,价格高于我方套餐,"
                   f"直接推翻『{C5_STATEMENT}』前提,见 {COMPETITOR_ID}")

_tc_counter = 0


def _tc(name, args):
    """构造一个 OpenAI tool_call 形状的消息段(幂等 id 递增)。"""""
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_c5_{_tc_counter}", type="function",
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
        SimpleNamespace(doc_id=COST_DOC, as_of="T1", source_type="public",
                        title="成本模型", doc_version="v2", checksum="", full_text=COST_TEXT),
        [_mk_chunk(COST_DOC, COST_TEXT),
         _mk_chunk("t0-competitor-notes", COMPETITOR_TEXT),
         _mk_chunk("t0-side", "市场杂项:渠道集中度上升,与本主张无关。")],
    )
    return store


def _claim() -> Claim:
    return Claim(claim_id="c5", statement=C5_STATEMENT,
                 t0_evidence_ids=[f"{COST_DOC}#p2"])


def _ctx(store=None) -> RunContext:
    return RunContext(store=store or InMemoryStore(), guardrails=Guardrails())


# -- 1. 口径守卫:四处落齐维度锚定 --------------------------------------------------------


@pytest.mark.parametrize("clause", [CLAUSE_DIMENSION, CLAUSE_COST_PRICE, CLAUSE_INDEPENDENT_CHECK])
def test_lead_persona_has_dimension_clauses(clause):
    """Lead 人格(消费侧):采纳 Critic 反证前强制独立核对维度对应,不得镜像。"""


    assert clause in LEAD_PERSONA


@pytest.mark.parametrize("clause", [CLAUSE_DIMENSION, CLAUSE_COST_PRICE])
def test_critic_persona_has_dimension_clauses(clause):
    """Critic 人格(生产侧):反证必须锚同一前提/度量维度,维度不符不得 mark_stale。"""
    assert clause in CRITIC_PERSONA


@pytest.mark.parametrize("clause", ["c5", CLAUSE_DIMENSION, CLAUSE_COST_PRICE])
def test_verdict_rubric_has_c5_dimension_example(clause):
    """单一真相(rubric)落 c5 类反向干扰项示例:定价≠成本,维度不符不构成 stale。"""
    text = RUBRIC.read_text(encoding="utf-8")
    assert clause in text


def test_verdict_rubric_stale_definition_anchors_dimension():
    """stale 定义本体补维度锚定:互斥必须锚同一前提/度量维度。"""
    text = RUBRIC.read_text(encoding="utf-8")
    stale_line = next(ln for ln in text.splitlines() if ln.startswith("- **stale**"))
    assert CLAUSE_DIMENSION in stale_line


def test_skill_md_syncs_dimension_clauses():
    """T6 落盘人格(SKILL.md)与内联版同步:教义表落「维度不符不采纳」处置行。"""
    text = SKILL.read_text(encoding="utf-8")
    assert CLAUSE_DIMENSION in text
    assert CLAUSE_INDEPENDENT_CHECK in text


def test_context_glossary_anchors_valid_counterevidence():
    """词表:有效反证定义补「因果句锚同一度量维度」,与 rubric 单一真相不漂移。"""
    text = GLOSSARY.read_text(encoding="utf-8")
    para = next(block for block in text.split("\n\n")
                if "**有效反证 (valid counter-evidence)**" in block)
    assert CLAUSE_DIMENSION in para
    assert CLAUSE_COST_PRICE in para


# -- 2. 结构注入:checkpoint 观察强制带维度核对指令 ------------------------------------------


def test_checkpoint_note_injects_dimension_check():
    """§8.5 对冲咬合的 c5 补洞:checkpoint 回吐 Lead 的观察必须带「采纳前独立核对维度」指令。

    脚本复刻 c5 事故流程:Lead 检索成本模型 → 落 fresh(自动派驻 Critic,
    Critic  retrieve 到竞品定价 notes 并以维度混淆理由 mark_stale)→ Lead 看到
    checkpoint 观察(含维度核对指令)后决定不采纳,维持 fresh。
    """
    llm = _ScriptLLM([
        _Msg(tool_calls=[_tc("retrieve", {"query": "单会话成本 复测", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("reverify_claim", {"claim_id": "c5", "status": "fresh",
                                                 "evidence_ids": [COST_ID]})]),
        # —— 以下 4 条为自动派驻的 Critic 会话(FIFO 同步消费)——
        _Msg(tool_calls=[_tc("retrieve", {"query": "竞品 定价", "as_of": "T1"})]),
        _Msg(tool_calls=[_tc("mark_stale", {"reason": CONFUSED_REASON,
                                             "evidence_ids": [COMPETITOR_ID],
                                             "dimension": "competitor_pricing"})]),
        _Msg(tool_calls=[_tc("report_finding",
                             {"finding": f"找到反证:竞品定价高于我方,见 {COMPETITOR_ID}"})]),
        _Msg(content="报告完毕"),
        # —— Auditor 单轮判定(fresh 钩子内自动触发,#22/ADR-0009)——
        _aud({"status": "fresh", "reason": "T1 成本复测支持主张"}),
        # —— Lead 看到 checkpoint 观察(含维度核对指令)后不采纳,维持 fresh ——
        _Msg(tool_calls=[_tc("finish_reverify", {})]),
        _Msg(content="复验结束"),
    ])
    ctx = _ctx(_store())
    lead = LeadReverifier(ctx, _claim(), llm)
    decision = lead.run()

    spawns = [e for e in ctx.events if e.get("type") == "critic_spawn"]
    assert len(spawns) == 1 and spawns[0].get("auto") is True

    # checkpoint 观察必须带维度核对指令(结构注入,不依赖模型自觉)
    out = [e for e in ctx.events if e.get("type") == "lead_step"
           and e.get("tool") == "reverify_claim"][0]["result"]
    checkpoint = out.get("critic_checkpoint")
    assert checkpoint is not None
    note = checkpoint.get("note", "")
    assert CLAUSE_DIMENSION in note, "checkpoint note 必须要求采纳前核对度量维度"
    assert CLAUSE_INDEPENDENT_CHECK in note

    # Lead 不采纳维度混淆反证 → 维持 fresh(修复後期望路径)
    assert decision.status == "fresh"
    assert decision.evidence_ids == [COST_ID]


# -- 3. c5 事故原料守卫 --------------------------------------------------------------------


def test_c5_fixture_documents_bug_shape():
    """c5 真实轨迹(冒烟 run-223219)作回归原料:可解析、事故形状钉住(定价当成本反证)。

    fixture 缺失不硬失败(报告目录不入库),但本地存在时必须保持形状可断言。
    """
    if not C5_FIXTURE.exists():
        pytest.skip("c5 轨迹 fixture 不在本地(reports/ 不入库)")
    events = [json.loads(ln) for ln in C5_FIXTURE.read_text(encoding="utf-8").splitlines()]
    finals = [e for e in events if e.get("type") == "claim_final"]
    assert len(finals) == 1
    final = finals[0]
    assert final["claim_id"] == "c5"
    assert final["status"] == "stale", "fixture 记录的是二修前事故形状,不得改写历史"
    assert "39" in final["reason"], "事故核心:竞品定价(39 美元/月/店)被当作成本反证"
    assert "定价" in final["reason"], "事故核心:理由用定价维度语汇推翻成本维度主张"
    # checkpoint 介导:auto=True 的自动派驻产出了维度混淆反证
    spawns = [e for e in events if e.get("type") == "critic_spawn"]
    assert any(s.get("auto") is True for s in spawns), "事故由 checkpoint 自动派驻介导"
