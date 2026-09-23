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


def test_atk_cs_01_tamper_corpus_renew_checksum_mismatch_zero_write(tmp_path):
    """ATK-CS-01:篡改语料文件后经 HumanLatch renew → CHECKSUM_MISMATCH,续命字段零写。

    确定性负例钉死 ADR-0017 预锁激活句。不得升格为「checksum 已证明 latch」。
    """
    from freshlatch.store.checksum import make_checksum_fn, sha256_hex
    from freshlatch.store.ingest import ingest_into

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    (corpus / "t0").mkdir(parents=True)
    path = corpus / "t1" / f"{DOC}.md"
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    path.write_bytes(raw)

    store = SQLiteStore(tmp_path / "atk01.db")
    assert ingest_into(store, corpus) >= 1
    recorded = store.get_chunk(DOC, "p2", as_of="T1")
    assert recorded is not None
    assert recorded.checksum == sha256_hex(raw) and recorded.checksum

    claim = make_claim()
    before = (
        claim.status,
        claim.validity_basis,
        claim.last_confirmed_at,
        tuple(claim.t1_evidence_ids),
        claim.reason,
    )
    assert latch_actions(store) == []

    path.write_bytes(raw + b"\nTAMPER-ATK-CS-01\n")
    assert sha256_hex(path.read_bytes()) != recorded.checksum
    # 库内指纹保持入库时现算值;比对对象是篡改后的文件现算,不是刷新库列
    still = store.get_chunk(DOC, "p2", as_of="T1")
    assert still is not None and still.checksum == recorded.checksum

    latch = make_latch(store, tmp_path, checksum_fn=make_checksum_fn(corpus))
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["ok"] is False, results[0]
    assert results[0]["error_code"] == "CHECKSUM_MISMATCH"
    after = (
        claim.status,
        claim.validity_basis,
        claim.last_confirmed_at,
        tuple(claim.t1_evidence_ids),
        claim.reason,
    )
    assert after == before
    assert latch_actions(store) == []


def test_atk_cs_03_empty_claimed_nonzero_actual_blocks_write(tmp_path):
    """ATK-CS-03:checksum_fn 非空 + claimed 空字符串 → 拦截,不得绿灯写入。

    claimed 取自点回块的库内指纹(本夹具为空)。空 claimed 不是「未启用」。
    不得升格为「checksum 已证明 latch」。
    """
    store = make_store(tmp_path, checksum="")
    claim = make_claim()
    before = (
        claim.status,
        claim.validity_basis,
        claim.last_confirmed_at,
        tuple(claim.t1_evidence_ids),
        claim.reason,
    )
    assert latch_actions(store) == []
    latch = make_latch(store, tmp_path, checksum_fn=lambda doc_id, as_of: "corpus-sha256-nonempty")
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    assert results[0]["ok"] is False, results[0]
    assert results[0]["error_code"] == "CHECKSUM_MISMATCH"
    after = (
        claim.status,
        claim.validity_basis,
        claim.last_confirmed_at,
        tuple(claim.t1_evidence_ids),
        claim.reason,
    )
    assert after == before
    assert claim.status == "stale"
    assert latch_actions(store) == []


def test_atk_cs_02_store_column_fn_not_activation_success(tmp_path):
    """ATK-CS-02:注入读库列的 checksum_fn,不得因恒等过闸记为激活成功。

    错误接线只活在本夹具,不上线。语料先被篡改,使库列与文件现算分开,
    套套才会暴露;未篡改时二者相同,哨兵分不开。零 LLM。
    不得升格为「checksum 已证明 latch」。不进档 3a/3b。
    """
    from pathlib import Path

    from freshlatch.store.checksum import (
        counts_as_checksum_activation,
        make_checksum_fn,
        sha256_hex,
    )
    from freshlatch.store.ingest import ingest_into

    repo_root = Path(__file__).resolve().parents[2]

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    (corpus / "t0").mkdir(parents=True)
    path = corpus / "t1" / f"{DOC}.md"
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    path.write_bytes(raw)

    store = SQLiteStore(tmp_path / "atk02.db")
    assert ingest_into(store, corpus) >= 1
    recorded = store.get_chunk(DOC, "p2", as_of="T1")
    assert recorded is not None and recorded.checksum == sha256_hex(raw)

    prod = make_checksum_fn(corpus)
    # 哨兵不是恒 False:未篡改且闸绿时,语料现算可以记为激活(仍非 latch 证明)
    assert counts_as_checksum_activation(
        prod, corpus_root=corpus, doc_id=DOC, as_of="T1",
        store_column=recorded.checksum, gate_green=True,
    ) is True

    path.write_bytes(raw + b"\nTAMPER-ATK-CS-02\n")
    file_now = sha256_hex(path.read_bytes())
    assert file_now != recorded.checksum
    still = store.get_chunk(DOC, "p2", as_of="T1")
    assert still is not None and still.checksum == recorded.checksum

    def read_store_column(doc_id, as_of):
        chunk = store.get_chunk(doc_id, "p2", as_of=as_of)
        assert chunk is not None
        return chunk.checksum

    assert read_store_column(DOC, "T1") == recorded.checksum
    assert read_store_column(DOC, "T1") != file_now
    # 生产接线读文件,不读库列
    assert prod(DOC, "T1") == file_now
    assert prod(DOC, "T1") != recorded.checksum

    claim = make_claim()
    latch = make_latch(store, tmp_path, checksum_fn=read_store_column)
    rnd = latch.enter_round([claim])
    results = latch.decide(rnd.thread_id, [{"claim_id": "c1", "action": "renew",
                                            "evidence_id": EID}])
    # 恒等会骗过只比较返回值的闸;该绿不是激活登记
    assert results[0]["ok"] is True, results[0]
    assert counts_as_checksum_activation(
        read_store_column, corpus_root=corpus, doc_id=DOC, as_of="T1",
        store_column=recorded.checksum, gate_green=bool(results[0]["ok"]),
    ) is False

    # 契约:生产 checksum 模块与 UI renew 注入不得读库列
    checksum_src = (repo_root / "src/freshlatch/store/checksum.py").read_text(encoding="utf-8")
    assert "get_chunk" not in checksum_src
    assert "get_document" not in checksum_src
    assert "sqlite" not in checksum_src.lower()
    app_src = (repo_root / "src/freshlatch/ui/app.py").read_text(encoding="utf-8")
    assert "checksum_fn=make_checksum_fn(CORPUS)" in app_src


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


# -- #117 交界与边界:可观察回归(仍走 HumanLatch renew 主缝) ---------------------------

# 预锁句(#99 评估 §4.6)。改句 = 本批交界验收作废。不得升格为 latch 证明。
JUNCTION_LOCKED = (
    "Batch 2 renew 交界：格式→点回→闸（含 checksum）→仅绿后写 `validity_basis`/转绿；"
    "失败零写且 `error_code`+短中文透传；不启用跨轮重检；"
    "不得升格为 checksum 证明 latch / 商业裁决。"
)

# 失败 detail 禁止的商业裁决 / Agent 自绿话术(交界评估 §4.3)
_BANNED_DETAIL = (
    "建议作废",
    "主张已死",
    "该出局",
    "Agent",
    "机器改判",
    "已证明",
)

# fresh 半边允许出现 validity_basis 的模块:字段、续命写入、闸比对、导出投影、跨轮腐烂。
# runner / 角色 / 工具 / UI 不在此列 = 不构造 basis(结构性空转,档 3a OUT)。
_BASIS_ALLOWED = {
    "models.py",
    "sheet.py",
    "gates/human_latch.py",
    "gates/rule_gate.py",
    "gates/basis_rot.py",
}


def _has_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _assert_short_zh_detail(result: dict) -> None:
    """error_code + 短中文 detail 透传;不是商业裁决。"""
    code = result["error_code"]
    detail = result["detail"]
    assert code and code.replace("_", "").isalnum() and code == code.upper()
    assert detail and "\n" not in detail and len(detail) <= 400
    assert _has_cjk(detail)
    for bad in _BANNED_DETAIL:
        assert bad not in detail, detail


def _renew_fields(claim: Claim) -> tuple:
    return (
        claim.status,
        claim.validity_basis,
        claim.last_confirmed_at,
        tuple(claim.t1_evidence_ids),
        claim.reason,
    )


def _submit_renew(latch: HumanLatch, claim: Claim, evidence_id: str, ts: str) -> dict:
    rnd = latch.enter_round([claim], ts=ts)
    assert rnd.thread_id, ts
    results = latch.decide(rnd.thread_id, [{"claim_id": claim.claim_id, "action": "renew",
                                            "evidence_id": evidence_id}])
    assert len(results) == 1
    return results[0]


def test_batch2_junction_order_zero_write_then_green(tmp_path):
    """#117:格式→点回→闸→仅绿后写;失败零写且 error_code+短中文透传。

    checksum_fn 调用次数钉次序:格式/点回失败时闸不得先跑。
    不得升格为「checksum 已证明 latch」。不做档 3a/3b。零 LLM。
    """
    from freshlatch.store.checksum import make_checksum_fn, sha256_hex
    from freshlatch.store.ingest import ingest_into

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    (corpus / "t0").mkdir(parents=True)
    path = corpus / "t1" / f"{DOC}.md"
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    path.write_bytes(raw)

    store = SQLiteStore(tmp_path / "j117.db")
    assert ingest_into(store, corpus) >= 1
    recorded = sha256_hex(raw)
    chunk = store.get_chunk(DOC, "p2", as_of="T1")
    assert chunk is not None and chunk.checksum == recorded

    calls: list[tuple[str, str]] = []
    prod = make_checksum_fn(corpus)

    def counting(doc_id, as_of):
        calls.append((doc_id, as_of))
        return prod(doc_id, as_of)

    claim = make_claim()
    # 历史 basis 只是字段残留;失败不得改它,本批也不拿它做跨轮降级
    claim.validity_basis = {"doc_id": "hist-doc", "checksum": "old-round"}
    before = _renew_fields(claim)
    latch = make_latch(store, tmp_path, checksum_fn=counting)

    malformed = _submit_renew(latch, claim, "not-an-evidence-id", "20260923-117001")
    assert malformed["ok"] is False
    assert malformed["error_code"] == RENEW_EVIDENCE_MALFORMED
    _assert_short_zh_detail(malformed)
    assert calls == []
    assert _renew_fields(claim) == before
    assert latch_actions(store) == []

    unresolved = _submit_renew(latch, claim, "t0-ghost#p9@T1", "20260923-117002")
    assert unresolved["ok"] is False
    assert unresolved["error_code"] == RENEW_EVIDENCE_UNRESOLVED
    _assert_short_zh_detail(unresolved)
    assert calls == []  # 点回失败,闸(含 checksum)尚未执行
    assert _renew_fields(claim) == before
    assert latch_actions(store) == []

    path.write_bytes(raw + b"\nTAMPER-JUNCTION\n")
    mismatch = _submit_renew(latch, claim, EID, "20260923-117003")
    assert mismatch["ok"] is False
    assert mismatch["error_code"] == "CHECKSUM_MISMATCH"
    _assert_short_zh_detail(mismatch)
    assert "对不上" in mismatch["detail"]
    assert calls == [(DOC, "T1")]
    assert _renew_fields(claim) == before
    assert claim.status == "stale"
    assert latch_actions(store) == []

    path.write_bytes(raw)
    ok = _submit_renew(latch, claim, EID, "20260923-117004")
    assert ok["ok"] is True, ok
    assert ok["error_code"] is None
    assert _has_cjk(ok["detail"])
    for bad in _BANNED_DETAIL:
        assert bad not in ok["detail"]
    assert claim.status == "fresh"
    assert claim.validity_basis == {"doc_id": DOC, "checksum": recorded}
    assert claim.last_confirmed_at
    assert EID in claim.t1_evidence_ids
    assert latch_actions(store) == [("renew", EID, "human")]
    assert calls == [(DOC, "T1"), (DOC, "T1")]


def test_batch2_no_cross_round_recheck_after_green(tmp_path):
    """#117:不启用跨轮重检。续命转绿后篡改语料,再进轮不得自动降级。

    档 3b 留 #111,本测试只观察缺席。不得升格为 latch 证明。零 LLM。
    """
    from freshlatch.store.checksum import make_checksum_fn, sha256_hex
    from freshlatch.store.ingest import ingest_into

    corpus = tmp_path / "corpus"
    (corpus / "t1").mkdir(parents=True)
    (corpus / "t0").mkdir(parents=True)
    path = corpus / "t1" / f"{DOC}.md"
    raw = (
        f"---\ndoc_id: {DOC}\nas_of: T1\nsource_type: competitor\n"
        f"title: 竞品笔记\nchecksum:\n---\n\n## p2\n"
        f"T1:竞品客单价仍显著高于我们。\n"
    ).encode("utf-8")
    path.write_bytes(raw)
    store = SQLiteStore(tmp_path / "j117b.db")
    assert ingest_into(store, corpus) >= 1
    recorded = sha256_hex(raw)

    claim = make_claim()
    latch = make_latch(store, tmp_path, checksum_fn=make_checksum_fn(corpus))
    ok = _submit_renew(latch, claim, EID, "20260923-117010")
    assert ok["ok"] is True, ok
    basis = {"doc_id": DOC, "checksum": recorded}
    assert claim.validity_basis == basis
    assert claim.status == "fresh"

    path.write_bytes(raw + b"\nTAMPER-NO-CROSS-ROUND\n")
    again = latch.enter_round([claim], ts="20260923-117011")
    assert again.thread_id is None  # 已绿,不进待审,也不重读历史 basis
    assert claim.status == "fresh"
    assert claim.validity_basis == basis
    assert latch_actions(store) == [("renew", EID, "human")]

    public = [n for n in dir(HumanLatch) if not n.startswith("_")]
    assert not any("recheck" in n or "rot" in n or "downgrade" in n for n in public)


def test_batch2_boundary_note_fresh_idle_and_atk_refs():
    """#117:验收注记可核对;fresh 不构造 validity_basis;ATK-CS-01..04 在本模块可引用。

    不新开 runner 行为缝:fresh 空转用源码允许集钉死。档 3a/3b 未实现。
    """
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    note = (repo / "docs/evidence/batch2/junction-acceptance.md").read_text(encoding="utf-8")
    assert JUNCTION_LOCKED in note.replace("**", "")
    assert "结构性空转" in note
    assert "不构造" in note and "validity_basis" in note
    assert "不启用跨轮重检" in note
    assert "data/eval/gold.json" in note
    for atk in ("ATK-CS-01", "ATK-CS-02", "ATK-CS-03", "ATK-CS-04"):
        assert atk in note
    assert "3a" in note and "3b" in note
    # 注记可以写「不得升格」,不得把升格句当成结论标题
    assert "checksum 已证明 latch" not in note

    import tests.unit.test_renew as renew_mod

    for name in (
        "test_atk_cs_01_tamper_corpus_renew_checksum_mismatch_zero_write",
        "test_atk_cs_02_store_column_fn_not_activation_success",
        "test_atk_cs_03_empty_claimed_nonzero_actual_blocks_write",
        "test_atk_cs_04_renew_with_corpus_sha256_writes_basis",
    ):
        assert callable(getattr(renew_mod, name))

    src = repo / "src/freshlatch"
    hits = sorted(
        p.relative_to(src).as_posix()
        for p in src.rglob("*.py")
        if "validity_basis" in p.read_text(encoding="utf-8")
    )
    assert set(hits) <= _BASIS_ALLOWED
    assert "runner.py" not in hits
    assert "roles/lead.py" not in hits
    assert "tools.py" not in hits

    runner_src = (src / "runner.py").read_text(encoding="utf-8")
    start = runner_src.index("def _checksum_fn")
    body = runner_src[start:]
    nxt = body.find("\n    def ")
    body = body[:nxt] if nxt != -1 else body
    assert "return None" in body
    assert "sha256" not in body
    assert "get_chunk" not in body
    assert "validity_basis" not in body


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
