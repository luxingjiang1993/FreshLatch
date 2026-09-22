"""续命闭环(#23 / ADR-0006 §4)单测:零 LLM、零网络、零额度。

三层各守一段,违例一律打回附结构化原因:
- 闸层(rule_gate):renew 专用机械校验路径——证据时点 / checksum / 作废名单;
- 写路径(gates/human_latch):人审续命唯一出口——格式校验 → 点回校验 → 调闸 → 写回;
- 红线:Agent 工具链无任何续命入口(白名单不含 renew,由既有白名单用例守住)。
"""

from __future__ import annotations

from freshlatch.gates.human_latch import (
    RENEW_EVIDENCE_MALFORMED,
    RENEW_EVIDENCE_UNRESOLVED,
)
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.store.base import Chunk, Document
from freshlatch.store.sqlite_store import SQLiteStore

DOC = "t0-competitor-notes"
EID = f"{DOC}#p2@T1"
EID_T0 = f"{DOC}#p2@T0"


# -- 闸层:renew 专用机械校验路径 ------------------------------------------------------


def make_claim(claim_id: str = "c1") -> Claim:
    return Claim(claim_id=claim_id, statement="竞品客单价仍显著高于我们",
                 status="stale", reason="T1 竞品降价至我们 70%")


def make_ctx(**kw) -> GateContext:
    kw.setdefault("checksum_fn", lambda doc_id, as_of: None)
    return GateContext(**kw)


def test_gate_renew_without_evidence_blocked():
    """ADR-0006 §4:续命必须带 T1 原文证据——空 evidence 机械打回。"""
    r = rule_gate(make_claim(), GateDecision(status="renew"), make_ctx())
    assert not r.green and r.error_code == "RENEW_NO_EVIDENCE"


def test_gate_renew_evidence_must_anchor_t1():
    """锚 T0 的 id 不构成续命依据(T1 才是 ground truth,CONTEXT.md T0/T1 语料)。"""
    r = rule_gate(make_claim(), GateDecision(status="renew", t1_evidence_ids=[EID_T0]), make_ctx())
    assert not r.green and r.error_code == "RENEW_EVIDENCE_NOT_T1"


def test_gate_renew_invalidated_blocked():
    """§1.3:作废名单内不得 fresh/续命(与重跑打回同一张名单)。"""
    ctx = make_ctx(invalidation_list={"c1"})
    r = rule_gate(make_claim(), GateDecision(status="renew", t1_evidence_ids=[EID]), ctx)
    assert not r.green and r.error_code == "INVALIDATED"


def test_gate_renew_checksum_mismatch_blocked():
    """§1.3:checksum 对不上不得续命(有效性依据的机械一致性)。"""
    ctx = make_ctx(checksum_fn=lambda doc_id, as_of: "current-9f3")
    d = GateDecision(status="renew", t1_evidence_ids=[EID],
                     validity_basis={"doc_id": DOC, "checksum": "recorded-111"})
    r = rule_gate(make_claim(), d, ctx)
    assert not r.green and r.error_code == "CHECKSUM_MISMATCH"


def test_gate_renew_happy_path_green():
    """renew 是 L0 人审出口:过闸即绿,不受不变量 9 双判一致约束。"""
    d = GateDecision(status="renew", t1_evidence_ids=[EID],
                     validity_basis={"doc_id": DOC, "checksum": ""})
    assert rule_gate(make_claim(), d, make_ctx()).green


# -- 写路径:gates/human_latch 是人审续命唯一出口 ---------------------------------------


def make_store(tmp_path, *, checksum: str = "") -> SQLiteStore:
    store = SQLiteStore(tmp_path / "freshlatch.db")
    chunk = Chunk(doc_id=DOC, chunk_id=f"{DOC}-p2", clause_id="p2", title="竞品笔记",
                  text="T1:竞品客单价仍显著高于我们。", source_type="competitor",
                  as_of="T1", doc_version="v2", checksum=checksum, tokens=20)
    store.add_document(
        Document(doc_id=DOC, as_of="T1", source_type="competitor", title="竞品笔记",
                 doc_version="v2", checksum=checksum, full_text=chunk.text),
        [chunk],
    )
    return store


def make_latch(store, tmp_path, **kw) -> HumanLatch:
    return HumanLatch(store, tmp_path / "checkpoints.db", **kw)


def latch_actions(store, claim_id="c1") -> list[tuple]:
    with store._conn() as conn:
        rows = conn.execute(
            "SELECT action, evidence_id, actor FROM latch_log WHERE claim_id=?",
            (claim_id,)).fetchall()
    return [(r["action"], r["evidence_id"], r["actor"]) for r in rows]


def test_renew_turns_card_green_and_logs(tmp_path):
    """用户旅程正例:红灯主张 → 人带 T1 证据续命 → 闸过 → 卡片转绿 + 时间戳 + latch_log。"""
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    rnd = latch.enter_round(claims, ts="20260921-120000")

    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["ok"] is True, results[0]
    c = claims[0]
    assert c.status == "fresh"                      # 卡片转绿
    assert c.last_confirmed_at                      # 续命时间戳
    assert c.validity_basis and c.validity_basis["doc_id"] == DOC  # 新 validity_basis
    assert EID in c.t1_evidence_ids                 # 续命依据可点回
    assert latch_actions(store) == [("renew", EID, "human")]  # 审计迹落档
    assert store.list_invalidation() == []          # 续命不进作废名单


def test_atk_cs_04_renew_with_corpus_sha256_writes_basis(tmp_path):
    """ATK-CS-04:未篡改 + claimed=语料现算 → 过闸写 validity_basis + 审计迹。

    不得升格为「checksum 已证明 latch」——仅 invariant 牙齿正例。
    """
    from freshlatch.store.checksum import make_checksum_fn, sha256_hex
    from freshlatch.store.ingest import parse_document, ingest_into

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    (corpus / "t1" / f"{DOC}.md").write_bytes(raw)
    # t0 镜像可空目录;ingest 只扫有文件的
    (corpus / "t0").mkdir(parents=True)

    store = SQLiteStore(tmp_path / "atk.db")
    assert ingest_into(store, corpus) >= 1
    doc, _chunks = parse_document(corpus / "t1" / f"{DOC}.md")
    assert doc.checksum == sha256_hex(raw) and doc.checksum

    latch = make_latch(store, tmp_path, checksum_fn=make_checksum_fn(corpus))
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["ok"] is True, results[0]
    c = claims[0]
    assert c.status == "fresh"
    assert c.validity_basis == {"doc_id": DOC, "checksum": sha256_hex(raw)}
    assert latch_actions(store) == [("renew", EID, "human")]


def test_renew_without_evidence_writes_nothing(tmp_path):
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew"}])
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == "RENEW_NO_EVIDENCE"
    assert claims[0].status == "stale" and claims[0].last_confirmed_at is None
    assert latch_actions(store) == []


def test_renew_malformed_evidence_id_rejected(tmp_path):
    """格式校验:必须 doc#anchor@T1(复用 evidence_id 时点格式,CONTEXT.md 词表)。"""
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": "not-an-evidence-id"}])
    assert results[0]["error_code"] == RENEW_EVIDENCE_MALFORMED
    assert claims[0].status == "stale"


def test_renew_unresolvable_evidence_rejected(tmp_path):
    """点回校验:证据 id 必须点回真实 chunk(编造 id 不得续命)。"""
    store = make_store(tmp_path)
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": "t0-ghost#p9@T1"}])
    assert results[0]["error_code"] == RENEW_EVIDENCE_UNRESOLVED
    assert claims[0].status == "stale"


def test_renew_on_invalidated_claim_rejected(tmp_path):
    """已作废主张不得续命(作废是人的终局决定,规则闸查名单强制)。"""
    store = make_store(tmp_path)
    store.add_invalidation("c1", "2026-09-21T00:00:00", actor="human")
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    claims[0].voided = True
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["ok"] is False
    assert results[0]["error_code"] == "INVALIDATED"
    assert claims[0].status == "stale"


def test_renew_checksum_mismatch_rejected(tmp_path):
    """checksum 链:块上留档的 checksum 与当前实算不一致 → 闸打回,零写。"""
    store = make_store(tmp_path, checksum="recorded-111")
    latch = make_latch(store, tmp_path,
                       checksum_fn=lambda doc_id, as_of: "current-9f3")
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["error_code"] == "CHECKSUM_MISMATCH"
    assert claims[0].status == "stale" and latch_actions(store) == []


def test_renew_evidence_anchored_t0_rejected_by_gate(tmp_path):
    """分层兜底:格式与点回都过,但锚 T0 → 闸层 RENEW_EVIDENCE_NOT_T1 拦下。"""
    store = make_store(tmp_path)
    store.add_document(
        Document(doc_id=DOC, as_of="T0", source_type="competitor", title="竞品笔记",
                 doc_version="v1", checksum="", full_text="T0:竞品客单价高于我们。"),
        [Chunk(doc_id=DOC, chunk_id=f"{DOC}-p2-t0", clause_id="p2", title="竞品笔记",
               text="T0:竞品客单价高于我们。", source_type="competitor",
               as_of="T0", doc_version="v1", checksum="", tokens=20)],
    )
    latch = make_latch(store, tmp_path)
    claims = [make_claim()]
    rnd = latch.enter_round(claims)
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID_T0}])
    assert results[0]["error_code"] == "RENEW_EVIDENCE_NOT_T1"
    assert claims[0].status == "stale"


# -- 红线:Agent 侧工具链无续命入口 ----------------------------------------------------


def test_no_renew_tool_in_agent_whitelist():
    """ADR-0006 §4:续命是人审 L0 出口,Agent 工具链物理上不得可见(白名单 fail-closed)。

    两道断言:已挂载的角色白名单里没有 renew;工具表里也没有 renew 插座
    (没定义 = 任何阶段都挂不上,这是「阶段挂载」推论的反面用法)。
    """
    from freshlatch import tools

    mounted = {t for wl in (tools.LEAD_TOOLS_W1, tools.LEAD_TOOLS_W3,
                            tools.CRITIC_TOOLS, tools.AUDITOR_TOOLS) for t in wl}
    assert not [t for t in mounted if "renew" in t.lower()]
    assert not [n for n in tools._TOOL_DEFS if "renew" in n.lower()]
