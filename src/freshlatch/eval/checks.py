"""J1/J2 机器可查判据(§7.4):点回、有效反证三硬判据的机器层。

层级声明(Anthropic 纪律 #1):本模块只实现 demo 层机械判据——
① 可点回(id 解析合法 + chunk 在库可解析)、③ span 与金标 causal_chain 对齐;
② 「理由含显式因果句」是语义判据,机器只做代理检查(reason 提及 t1_doc),
   语义复核归人工,报告里必须如实标注,不得冒充硬判据。
"""

from __future__ import annotations

from freshlatch.store.base import RetrievalStore

EXPECTED_ID_TEMPLATE = "{t1_doc}#{anchor}@T1"


def parse_evidence_id(eid: str) -> tuple[str, str, str] | None:
    """`doc_id#anchor@as_of` → (doc_id, anchor, as_of);格式不合法返回 None。"""
    try:
        body, as_of = eid.rsplit("@", 1)
        doc_id, anchor = body.rsplit("#", 1)
    except ValueError:
        return None
    if not doc_id or not anchor or as_of not in ("T0", "T1"):
        return None
    return doc_id, anchor, as_of


def expected_evidence_id(gold: dict, claim_id: str) -> str | None:
    """金标 causal_chain 登记的锚段落 id;无登记(must_unknown)返回 None,天然豁免 J1。"""
    entry = gold.get("causal_chain", {}).get(claim_id)
    if not entry:
        return None
    return EXPECTED_ID_TEMPLATE.format(t1_doc=entry["t1_doc"], anchor=entry["anchor"])


def check_point_back(store: RetrievalStore, evidence_ids: list[str]) -> dict[str, bool]:
    """每个 id:格式合法且 chunk 在库内按登记时点可解析 = 可点回。"""
    resolvable: dict[str, bool] = {}
    for eid in evidence_ids:
        parsed = parse_evidence_id(eid)
        resolvable[eid] = (
            parsed is not None
            and store.get_chunk(parsed[0], parsed[1], as_of=parsed[2]) is not None
        )
    return resolvable


def check_counterevidence(store: RetrievalStore, gold: dict, claim_id: str,
                          status: str, reason: str, evidence_ids: list[str]) -> dict:
    """有效反证三硬判据的机器层(§7.4 J2)。

    前置条件(J4 人查查出的实现缺陷,2026-09-20 修复):判定方向必须是 stale——
    fresh 判定引用的永远是支持性证据,不构成反证;不过此条件,
    must_fresh 的正确 fresh 判定必然命中金标锚,反向护栏恒假;
    must_stale 判 fresh 却引用致死段落(如 c2)会被误计为「有效反证」。
    """
    expected = expected_evidence_id(gold, claim_id)
    resolvable = check_point_back(store, evidence_ids)
    aligned = expected is not None and expected in evidence_ids
    t1_doc = (gold.get("causal_chain", {}).get(claim_id) or {}).get("t1_doc", "")
    stale_direction = status == "stale"
    return {
        "claim_id": claim_id,
        "status": status,
        "expected_anchor": expected,
        "evidence_ids": evidence_ids,
        "stale_direction": stale_direction,
        "pointable": all(resolvable.values()) if resolvable else False,
        "resolvable_detail": resolvable,
        "anchor_aligned": aligned,
        # 代理判据:reason 提及致死段落所在文档。语义复核(是否真为显式因果句)归人工。
        "causal_sentence_proxy": bool(t1_doc) and t1_doc in reason,
        "causal_sentence_note": "② 显式因果句为语义判据,机器仅查 reason 提及 t1_doc(代理),硬判定归人工复核",
        "valid_machine": stale_direction and bool(evidence_ids)
        and all(resolvable.values()) and aligned,
    }
