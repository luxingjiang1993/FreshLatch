"""复验单共享投影与 Markdown 导出(K4)+ 客户向复验备忘(ADR-0015)。

真源:内存 Claim ⊕ 审计表(latch_log / rerun_log)合并投影——与复验单 UI 卡片同构。
导出写 voided,不伪造 status=void。CLI 读快照 JSON,不现场跑复验。
客户向备忘复用同一投影,但不含轨迹/人审时间线,并过禁语与字段契约。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from freshlatch.evidence_bound import is_patch_eligible
from freshlatch.evidence_id import display_evidence_id
from freshlatch.latch import HumanLatch
from freshlatch.models import Claim
from freshlatch.prepublish import disposition_for_claims
from freshlatch.roles.retrieve_grade import (
    REASON_GRADE_AMBIGUOUS,
    REASON_GRADE_INCORRECT_EXHAUSTED,
)
from freshlatch.roles.retrieve_sufficiency import REASON_INSUFFICIENT_EVIDENCE
from freshlatch.tools import REASON_TOOL_TIER_DENIED, TOOL_TIER_2
from freshlatch.publish_hook import (
    NEEDS_PATCH_BANNER,
    PublishHookResult,
    evaluate_publish_hook,
)
from freshlatch.reading_source import BYPASS_TEXT, MEMO_NOTE
from freshlatch.store.base import RetrievalStore

# 人审动作时间线文案(后端唯一生成;重跑文案走 HumanLatch.timeline_label)
LATCH_EVENT_LABELS = {
    "discard": "人审作废",
    "renew": "人审续命",
    "disputed": "人审改账",
}

# 产品失败三桶。与 ops ADR-0028 评测桶(找不到/找错/没用上)不是同一套词。
PRODUCT_BUCKET_RETRIEVAL_EMPTY = "retrieval_empty"
PRODUCT_BUCKET_GRADE_INSUFFICIENT = "grade_insufficient"
PRODUCT_BUCKET_TOOL_TIER_2_DENIED = "tool_tier_2_denied"
PRODUCT_FAILURE_BUCKETS: tuple[tuple[str, str], ...] = (
    (PRODUCT_BUCKET_RETRIEVAL_EMPTY, "检索空"),
    (PRODUCT_BUCKET_GRADE_INSUFFICIENT, "grade 不够"),
    (PRODUCT_BUCKET_TOOL_TIER_2_DENIED, "tool_tier_2 拒"),
)
_PRODUCT_BUCKET_LABELS = dict(PRODUCT_FAILURE_BUCKETS)


def project_claim(store: RetrievalStore, claim: Claim) -> dict[str, Any]:
    """Claim ⊕ 审计表 → UI/导出/对账单测同吃的字典投影。"""
    # 时间线 = 重跑(rerun_log)+ 人审动作(latch_log 的作废/续命)两条审计迹按 ts 合并;
    # rerun 同时写两表,只从 rerun_log 计一次,不重复。单一真相在库表。
    events = [
        {
            **t,
            "kind": "rerun",
            "evidence_id": None,
            "label": HumanLatch.timeline_label(t["verdict"], t["nth"]),
            "override": None,
            "machine_status_before": None,
        }
        for t in store.list_reruns(claim.claim_id)
    ]
    events += [
        {
            "kind": e["action"],
            "ts": e["ts"],
            "thread_id": None,
            "evidence_id": e["evidence_id"],
            "label": LATCH_EVENT_LABELS.get(e["action"], e["action"]),
            # override 是派生标签,可在时间线上观察;不表示模型变好
            "override": e.get("override"),
            "machine_status_before": e.get("machine_status_before"),
            "run_id": e.get("run_id"),
            # disputed 的结论进时间线,再打开时与台账同一句话
            "reviewer_note": e.get("reviewer_note") if e.get("action") == "disputed" else None,
            "note": (e.get("reviewer_note") or "") if e.get("action") == "disputed" else "",
        }
        for e in store.list_latch_events(claim.claim_id)
        if e["action"] != "rerun"
    ]
    events.sort(key=lambda e: e["ts"])
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "t0_evidence_ids": list(claim.t0_evidence_ids),
        "t1_evidence_ids": list(claim.t1_evidence_ids),
        "status": claim.status,
        "reason": claim.reason,
        "voided": claim.voided,
        "voided_at": claim.voided_at,
        "last_confirmed_at": claim.last_confirmed_at,  # 续命时间戳(§5.4)
        "validity_basis": claim.validity_basis,  # 续命写的新有效性依据(§5.4)
        "timeline": events,
        # #200:补丁条带入口闸(与 evidence_bound.is_patch_eligible 同口径)
        "patch_eligible": is_patch_eligible(claim),
    }


# 职人视图只读徽章。不是 Claim.status,也不写入主张。
UI_BADGE_VERIFIED = "verified"
UI_BADGE_PARTIAL = "partial"
UI_BADGE_ABSTAIN = "abstain"
# stale / void 已有机器结论,不套 partial。
_UI_BADGE_SKIP_PARTIAL = frozenset({"stale", "void"})


def project_audit(trajectory: str | Path | None) -> dict[str, Any]:
    """只读轨迹投影成审计面。不改闸,不改 Claim.status。

    字段:query、hits(含 scores)、attribution_ids、unknown_reason、badges、
    claim_spans(句 id 锚,支撑句与反对句分列)、failure_buckets(产品三桶,分列)。
    scores 只抄 RAG-04 已有的 bm25 / dense / rrf / rerank;缺臂留空。
    命中行若事件里已有 as_of / patch_id / valid_from / valid_to,原样抄上。
    没有这些键时不补空键,避免改旧轨迹的命中字典。
    unknown_reason 只经由 parse_failure_replay,不另写 reason 拼写。
    文件不是轨迹 JSONL,或没有这些字段时,对应项为空,不编造分数。
    badges 是 UiBadge 只读列表,语义见 project_ui_badges;缺字段时为 []。
    claim_spans 只读 claim_span 事件;不把命中块涂成支撑句。
    failure_buckets 三枚标签始终分列,高亮至多对应本轨迹命中的桶,不收成一个失败。
    """
    path_text = None if trajectory is None else str(trajectory)
    out: dict[str, Any] = _empty_audit(path_text)
    if trajectory is None:
        return out
    path = Path(trajectory)
    if not path.is_file():
        return out
    events = _load_audit_events(path)
    if events is None:
        return out

    queries: list[str] = []
    hit_scores: dict[str, dict[str, float | None] | None] = {}
    hit_meta: dict[str, dict[str, str]] = {}
    hit_order: list[str] = []

    def add_query(value: object) -> None:
        if isinstance(value, str) and value.strip() and value not in queries:
            queries.append(value)

    def add_hit(
        evidence_id: object,
        scores_raw: object,
        meta_raw: object = None,
    ) -> None:
        if not isinstance(evidence_id, str) or not evidence_id:
            return
        copied = _copy_hit_scores(scores_raw)
        incoming = _copy_visible_patch(meta_raw)
        if evidence_id not in hit_scores:
            hit_order.append(evidence_id)
            hit_scores[evidence_id] = copied
            hit_meta[evidence_id] = incoming
            return
        if hit_scores[evidence_id] is None and copied is not None:
            hit_scores[evidence_id] = copied
        stored = hit_meta.setdefault(evidence_id, {})
        for key, value in incoming.items():
            stored.setdefault(key, value)

    for event in events:
        if event.get("type") == "retrieve":
            add_query(event.get("query"))
            score_map = event.get("scores")
            if not isinstance(score_map, dict):
                score_map = {}
            raw_hits = event.get("hits")
            if isinstance(raw_hits, list):
                for row in raw_hits:
                    if isinstance(row, dict):
                        add_hit(row.get("evidence_id"), row.get("scores"), row)
            ids = event.get("evidence_ids")
            if isinstance(ids, list):
                for evidence_id in ids:
                    row_scores = score_map.get(evidence_id) if isinstance(evidence_id, str) else None
                    add_hit(evidence_id, row_scores)
        if event.get("type") == "lead_step" and event.get("tool") == "retrieve":
            result = event.get("result")
            if isinstance(result, dict):
                blocks = result.get("blocks")
                if isinstance(blocks, list):
                    for block in blocks:
                        if isinstance(block, dict):
                            add_hit(block.get("evidence_id"), block.get("scores"), block)
            args = event.get("args")
            if isinstance(args, dict):
                add_query(args.get("query"))

    attribution: list[str] = []
    reason: str | None = None
    # 复用 AG-03。调用卫生码与自由文本不会出现在 reason_code 上。
    from freshlatch.runner import parse_failure_replay

    replay = parse_failure_replay(path)
    for claim in replay.get("claims") or []:
        for evidence_id in claim.get("evidence_ids") or []:
            if isinstance(evidence_id, str) and evidence_id and evidence_id not in attribution:
                attribution.append(evidence_id)
        code = claim.get("reason_code")
        if reason is None and isinstance(code, str) and code:
            reason = code

    from freshlatch.claim_span import project_claim_spans

    claim_spans = project_claim_spans(events)
    bucket_view = project_failure_buckets(replay)
    parsed = bool(
        queries or hit_order or attribution or reason or claim_spans
        or bucket_view["failure_bucket_claims"]
    )
    out["parsed"] = parsed
    out["query"] = queries
    hits: list[dict[str, Any]] = []
    for evidence_id in hit_order:
        row: dict[str, Any] = {
            "evidence_id": evidence_id,
            "scores": hit_scores[evidence_id],
        }
        extra = hit_meta.get(evidence_id) or {}
        if extra:
            row.update(extra)
        hits.append(row)
    out["hits"] = hits
    out["attribution_ids"] = attribution
    out["unknown_reason"] = reason
    out["claim_spans"] = claim_spans
    out["failure_bucket"] = bucket_view["failure_bucket"]
    out["failure_buckets"] = bucket_view["failure_buckets"]
    out["failure_bucket_claims"] = bucket_view["failure_bucket_claims"]
    # 与审计字段分开算:只读徽章,不回写 status。
    out["badges"] = project_ui_badges(path)
    return out


def _empty_audit(path_text: str | None) -> dict[str, Any]:
    """没有可解析轨迹时的审计壳。三桶在场但无一高亮。"""
    return {
        "parsed": False,
        "path": path_text,
        "query": [],
        "hits": [],
        "attribution_ids": [],
        "unknown_reason": None,
        "badges": [],
        "claim_spans": [],
        "failure_bucket": None,
        "failure_buckets": _inactive_failure_buckets(),
        "failure_bucket_claims": [],
    }


def _inactive_failure_buckets() -> list[dict[str, Any]]:
    return [
        {"id": bucket_id, "label": label, "active": False}
        for bucket_id, label in PRODUCT_FAILURE_BUCKETS
    ]


def classify_product_failure_bucket(row: dict) -> str | None:
    """一条复放主张 → 至多一个产品桶。没有信号时返回 None,不发明「失败」。

    优先 tool_tier_2 拒,其次 grade 不够,再次检索空。
    grade=incorrect 且 reason 为 insufficient_evidence、命中为空时归检索空。
    """
    denials = row.get("tool_tier_2_denials") or []
    if isinstance(denials, list):
        for item in denials:
            if not isinstance(item, dict):
                continue
            if item.get("reason_code") != REASON_TOOL_TIER_DENIED:
                continue
            if item.get("tool_tier") == TOOL_TIER_2:
                return PRODUCT_BUCKET_TOOL_TIER_2_DENIED
    reason = row.get("reason_code")
    if reason in (REASON_GRADE_INCORRECT_EXHAUSTED, REASON_GRADE_AMBIGUOUS):
        return PRODUCT_BUCKET_GRADE_INSUFFICIENT
    evidence_ids = row.get("evidence_ids") or []
    has_ids = isinstance(evidence_ids, list) and any(
        isinstance(item, str) and item for item in evidence_ids
    )
    if row.get("hits_empty") is True and not has_ids:
        if reason in (None, REASON_INSUFFICIENT_EVIDENCE):
            return PRODUCT_BUCKET_RETRIEVAL_EMPTY
    return None


def project_failure_buckets(replay: dict) -> dict[str, Any]:
    """复放结果 → 三桶投影。多主张命中不同桶时各桶独立高亮,不合并成一个标签。"""
    active: list[str] = []
    claims: list[dict[str, str]] = []
    for row in replay.get("claims") or []:
        if not isinstance(row, dict):
            continue
        bucket_id = classify_product_failure_bucket(row)
        if bucket_id is None:
            continue
        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            continue
        claims.append({
            "claim_id": claim_id,
            "bucket": bucket_id,
            "label": _PRODUCT_BUCKET_LABELS[bucket_id],
        })
        if bucket_id not in active:
            active.append(bucket_id)
    buckets = [
        {"id": bucket_id, "label": label, "active": bucket_id in active}
        for bucket_id, label in PRODUCT_FAILURE_BUCKETS
    ]
    failure_bucket = active[0] if len(active) == 1 else None
    return {
        "failure_bucket": failure_bucket,
        "failure_buckets": buckets,
        "failure_bucket_claims": claims,
    }


def render_failure_buckets_html(buckets: object) -> str:
    """三桶 HTML。标签分列;active 才加 is-active。不输出单独的「失败」标签。"""
    import html as html_lib

    rows = buckets if isinstance(buckets, list) else None
    if not rows:
        rows = _inactive_failure_buckets()
    parts: list[str] = []
    active_ids: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        bucket_id = str(row.get("id") or "")
        label = str(row.get("label") or "")
        if not bucket_id or not label:
            continue
        active = bool(row.get("active"))
        if active:
            active_ids.append(bucket_id)
        class_name = "failure-bucket is-active" if active else "failure-bucket"
        parts.append(
            f'<span class="{class_name}" data-bucket="{html_lib.escape(bucket_id)}">'
            f"{html_lib.escape(label)}</span>"
        )
    data_active = html_lib.escape(",".join(active_ids))
    return (
        f'<div id="audit-failure-buckets" data-active="{data_active}">'
        "<b>失败三桶</b> · "
        + "".join(parts)
        + "</div>"
    )


# 审计命中行展示的四列。过滤仍走 filter_patch_metadata,这里只读。
PATCH_VISIBILITY_FIELDS = ("as_of", "patch_id", "valid_from", "valid_to")


def _copy_visible_patch(raw: object) -> dict[str, str]:
    """事件里已经写出的非空补丁列。缺键或空白不补空字符串。"""
    if not isinstance(raw, dict):
        return {}
    copied: dict[str, str] = {}
    for key in PATCH_VISIBILITY_FIELDS:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            copied[key] = value.strip()
    return copied


def _chunk_patch_fields(store: RetrievalStore, evidence_id: object) -> dict[str, str | None]:
    """按 evidence_id 读库内块。不调用 retrieve,不收窄候选池。"""
    from freshlatch.evidence_id import parse_evidence_id
    from freshlatch.store.pipeline import meta_text

    empty: dict[str, str | None] = {key: None for key in PATCH_VISIBILITY_FIELDS}
    parsed = parse_evidence_id(evidence_id)
    if parsed is None:
        return empty
    doc_id, anchor, as_of = parsed
    empty["as_of"] = as_of
    chunk = store.get_chunk(doc_id, anchor, as_of=as_of)
    if chunk is None:
        return empty
    return {
        "as_of": meta_text(chunk.as_of) or as_of,
        "patch_id": meta_text(chunk.patch_id),
        "valid_from": meta_text(chunk.valid_from),
        "valid_to": meta_text(chunk.valid_to),
    }


def annotate_audit_patch_visibility(audit: dict[str, Any], store: RetrievalStore) -> dict[str, Any]:
    """给审计命中补上 as_of / patch_id / valid_from / valid_to。

    轨迹里已有的非空值保留。缺的列从库内块读。库里也没有时,
    as_of 用证据主键的快照后缀,其余三列为 None,界面显示「无」。
    不改检索,不改 Claim.status。
    """
    hits = audit.get("hits")
    if not isinstance(hits, list):
        return audit
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        looked = _chunk_patch_fields(store, hit.get("evidence_id"))
        for key in PATCH_VISIBILITY_FIELDS:
            current = hit.get(key)
            if isinstance(current, str) and current.strip():
                hit[key] = current.strip()
                continue
            hit[key] = looked.get(key)
    return audit


def project_ui_badges(
    trajectory: str | Path | None,
    claims: list[Claim] | None = None,
) -> list[dict[str, str]]:
    """本轮轨迹(加可选主张状态)→ UiBadge 列表。不写 Claim.status。

    verified: 本轮记录为 fresh,且 rule_gate 对同一 evidence id 与
    auditor_verdict 放行绿灯(足以续验且未拒答)。
    partial: 有本轮 evidence id,但够不上 verified,且不是拒答。
    abstain: parse_failure_replay 的 reason_code 属于拒答族。拒答优先。
    旧轨迹缺这些字段时不产生条目;调用方对缺主张保持 null,不编造。
    """
    if trajectory is None:
        return []
    path = Path(trajectory)
    events = _load_audit_events(path)
    if events is None:
        return []
    return _ui_badges_from_events(path, events, claims)


def _ui_badges_from_events(
    path: Path,
    events: list[dict],
    claims: list[Claim] | None,
) -> list[dict[str, str]]:
    from freshlatch.runner import parse_failure_replay

    replay = parse_failure_replay(path)
    reasons: dict[str, str] = {}
    for row in replay.get("claims") or []:
        claim_id = row.get("claim_id")
        code = row.get("reason_code")
        if isinstance(claim_id, str) and claim_id and isinstance(code, str) and code:
            reasons[claim_id] = code

    order: list[str] = []
    evidence: dict[str, list[str]] = {}
    recorded_status: dict[str, str] = {}
    auditor: dict[str, str] = {}

    def touch(claim_id: object) -> str | None:
        if not isinstance(claim_id, str) or not claim_id:
            return None
        if claim_id not in evidence:
            order.append(claim_id)
            evidence[claim_id] = []
        return claim_id

    def add_id(claim_id: str, value: object) -> None:
        if isinstance(value, str) and value and value not in evidence[claim_id]:
            evidence[claim_id].append(value)

    def add_ids(claim_id: str, values: object) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            add_id(claim_id, value)

    for event in events:
        claim_id = touch(event.get("claim_id"))
        if claim_id is None:
            continue
        kind = event.get("type")
        if kind == "retrieve":
            add_ids(claim_id, event.get("evidence_ids"))
            raw_hits = event.get("hits")
            if isinstance(raw_hits, list):
                for hit in raw_hits:
                    if isinstance(hit, dict):
                        add_id(claim_id, hit.get("evidence_id"))
        elif kind == "lead_step":
            add_ids(claim_id, event.get("evidence_ids"))
            if event.get("tool") == "retrieve":
                result = event.get("result")
                if isinstance(result, dict):
                    blocks = result.get("blocks")
                    if isinstance(blocks, list):
                        for block in blocks:
                            if isinstance(block, dict):
                                add_id(claim_id, block.get("evidence_id"))
        elif kind == "lead_loop_end":
            add_ids(claim_id, event.get("evidence_ids"))
        elif kind in ("claim_final", "claim_result"):
            add_ids(claim_id, event.get("evidence_ids"))
            recorded = event.get("status")
            if isinstance(recorded, str) and recorded:
                recorded_status[claim_id] = recorded
            verdict = event.get("auditor_verdict")
            if isinstance(verdict, str) and verdict:
                auditor[claim_id] = verdict

    memory = {claim.claim_id: claim for claim in (claims or [])}
    badges: list[dict[str, str]] = []
    for claim_id in order:
        # 拒答族优先:即便主张状态仍是 fresh,也不得投影成 verified。
        if reasons.get(claim_id):
            badges.append({"claim_id": claim_id, "badge": UI_BADGE_ABSTAIN})
            continue
        ids = evidence.get(claim_id) or []
        recorded = recorded_status.get(claim_id)
        if recorded is None and claim_id in memory:
            recorded = memory[claim_id].status
        verdict = auditor.get(claim_id)
        if recorded == "fresh" and _fresh_gate_allows(claim_id, ids, verdict):
            badges.append({"claim_id": claim_id, "badge": UI_BADGE_VERIFIED})
            continue
        if ids and recorded not in _UI_BADGE_SKIP_PARTIAL:
            badges.append({"claim_id": claim_id, "badge": UI_BADGE_PARTIAL})
    return badges


def _fresh_gate_allows(
    claim_id: str,
    evidence_ids: list[str],
    auditor_verdict: str | None,
) -> bool:
    """只读调用 rule_gate。临时 Claim 不写回调用方的主张。"""
    from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate

    probe = Claim(
        claim_id=claim_id,
        statement="",
        status="unknown",
        t1_evidence_ids=list(evidence_ids),
    )
    decision = GateDecision(
        status="fresh",
        t1_evidence_ids=list(evidence_ids),
        auditor_verdict=auditor_verdict,
    )
    result = rule_gate(probe, decision, GateContext())
    return bool(result.allowed and result.green)


def _load_audit_events(path: Path) -> list[dict] | None:
    """整文件都是 JSON 对象才当作轨迹。只有路径文本时返回 None。"""
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    events: list[dict] = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            continue
        try:
            event = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(event, dict):
            events.append(event)
    if not events:
        return None
    return events


def _copy_hit_scores(raw: object) -> dict[str, float | None] | None:
    """只保留已写出的有限数字。四个臂都缺则返回 None,调用方显示「无」。"""
    if not isinstance(raw, dict):
        return None
    import math

    from freshlatch.store.pipeline import HIT_SCORE_FIELDS

    copied: dict[str, float | None] = {}
    any_number = False
    for name in HIT_SCORE_FIELDS:
        value = raw.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            copied[name] = None
            continue
        number = float(value)
        if not math.isfinite(number):
            copied[name] = None
            continue
        copied[name] = number
        any_number = True
    if not any_number:
        return None
    return copied


def project_run_disposition(claims: list[Claim] | tuple[Claim, ...]) -> str:
    """报告级包结论投影(#173):与发前列表/复验单包结论条同吃 disposition 纯函数。"""
    from freshlatch.prepublish import disposition_for_claims

    return disposition_for_claims(claims)


def claim_from_dict(raw: dict[str, Any]) -> Claim:
    """快照 JSON 单条主张 → Claim(忽略未知键)。"""
    return Claim(
        claim_id=raw["claim_id"],
        statement=raw["statement"],
        t0_evidence_ids=list(raw.get("t0_evidence_ids") or []),
        t1_evidence_ids=list(raw.get("t1_evidence_ids") or []),
        dimension=raw.get("dimension"),
        status=raw.get("status") or "unknown",
        reason=raw.get("reason") or "",
        last_confirmed_at=raw.get("last_confirmed_at"),
        validity_basis=raw.get("validity_basis"),
        voided=bool(raw.get("voided", False)),
        voided_at=raw.get("voided_at"),
        dissent=raw.get("dissent"),
    )


def load_snapshot(path: str | Path) -> dict[str, Any]:
    """读复验单快照 JSON。须含 claims;可选 question / store(或 db)。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "claims" not in data:
        raise ValueError("快照须为含 claims 数组的 JSON 对象")
    if not isinstance(data["claims"], list):
        raise ValueError("快照 claims 须为数组")
    return data


def _fmt_evidence_ids(proj: dict[str, Any]) -> str:
    ids = list(proj.get("t0_evidence_ids") or []) + list(proj.get("t1_evidence_ids") or [])
    return ", ".join(f"`{eid}`" for eid in ids) if ids else "(无)"


def projections_with_override(projections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """审计过滤:时间线含 override=true 的主张。

    过滤只便于抽查人机对抗。结果不是模型变好,也不作 Override Rate 通过线。
    """
    kept: list[dict[str, Any]] = []
    for proj in projections:
        if any(ev.get("override") is True for ev in (proj.get("timeline") or [])):
            kept.append(proj)
    return kept


def _fmt_timeline(proj: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for ev in proj.get("timeline") or []:
        label = ev.get("label") or ev.get("kind") or ""
        ts = ev.get("ts") or ""
        eid = ev.get("evidence_id")
        note = ev.get("note") or ""
        line = f"- {ts} · {label}".rstrip(" ·")
        if ev.get("override") is True:
            line += " · override"
        parts = [line]
        if eid:
            parts.append(f"  evidence_id: `{eid}`")
        if note:
            parts.append(f"  note: {note}")
        lines.append("\n".join(parts) if len(parts) > 1 else parts[0])
    return lines


def render_claim_markdown(proj: dict[str, Any]) -> str:
    """单主张 Markdown 块(对齐 UI 卡片字段;写 voided 不伪造 status=void)。"""
    void_mark = "【已作废·灰显】" if proj.get("voided") else ""
    title = f"## {proj['claim_id']} {void_mark}".rstrip()
    lines = [
        title,
        "",
        proj.get("statement") or "",
        "",
        f"- **判定**: `{proj.get('status')}`",
        f"- **作废(voided)**: {'是' if proj.get('voided') else '否'}"
        + (f" · `{proj['voided_at']}`" if proj.get("voided_at") else ""),
        f"- **理由**: {proj.get('reason') or '(空)'}",
        f"- **原文点回(evidence_id)**: {_fmt_evidence_ids(proj)}",
        f"- **续命 last_confirmed_at**: "
        f"{'`' + proj['last_confirmed_at'] + '`' if proj.get('last_confirmed_at') else '(无)'}",
        f"- **续命 validity_basis**: "
        f"{json.dumps(proj['validity_basis'], ensure_ascii=False) if proj.get('validity_basis') else '(无)'}",
        "- **人审/重跑时间线**:",
    ]
    tl = _fmt_timeline(proj)
    if tl:
        lines.extend(tl)
    else:
        lines.append("- (空)")
    return "\n".join(lines)


def render_sheet_markdown(
    projections: list[dict[str, Any]],
    *,
    question: str = "",
) -> str:
    """全量复验单 Markdown。"""
    parts = [
        "# 复验单",
        "",
        BYPASS_TEXT,
        "",
        f"**问题**: {question or '(未提供)'}",
        "",
        f"**主张数**: {len(projections)}",
        "",
    ]
    for proj in projections:
        parts.append(render_claim_markdown(proj))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def export_sheet_from_snapshot(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    out_path: str | Path | None = None,
) -> str:
    """读快照 → 投影 → Markdown;可选落盘。返回 Markdown 文本。"""
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    md = render_sheet_markdown(projections, question=str(snap.get("question") or ""))
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return md


# ---- 客户向复验备忘 (Client Memo;ADR-0015 / INV-2·INV-3) ----
# 与复验单导出分离:读同一投影,不写轨迹/人审时间线,过禁语与字段契约。

# 禁止项字面:「建议进入/不进入」→ 建议进入 | 建议不进入(不含裸「不进入」,避免误伤)。
# I-03(#674/#677)初值表:ADR-/GATE/DEM-/闸/异议/路由/DIMENSION_MISMATCH + 报告 H 节样例;
# 机器 token 用 \b 边界,避免误伤 NAVIGATE 之类英文词;导出单测对样例 Memo 零命中。
_CLIENT_MEMO_FORBIDDEN = re.compile(
    r"Lead|Critic|建议进入|建议不进入"
    r"|\bADR-\d+\b|\bGATE\b|\bDEM-\d+\b|\bDIMENSION_MISMATCH\b"
    r"|闸|异议|路由"
)
_CLIENT_MEMO_DISCLAIMER = (
    "免责声明:本备忘非法律意见、非自动商业决策;"
    "仅反映既定 T1 事实下的复验投影,不构成投资或交易建议。"
)


def _sanitize_client_memo_text(text: str) -> str:
    """洗掉角色名与商业裁决禁语,避免投影理由泄漏进客户向正文。"""
    cleaned = _CLIENT_MEMO_FORBIDDEN.sub("", text or "")
    return re.sub(r"\s+", " ", cleaned).strip()


def _client_memo_bucket(proj: dict[str, Any]) -> str:
    """三分栏归属:已作废优先;仍成立=fresh 且未作废;其余进缺口。"""
    if proj.get("voided"):
        return "voided"
    if (proj.get("status") or "") == "fresh":
        return "held"
    return "gap"


# 客户向结论模板(I-03 #674 拍板:模板/规则层,不上 LLM):
# 一句客户向结论,按三分栏取值;机器理由(internal_reason 侧)不进默认面。
_CLIENT_MEMO_CONCLUSIONS = {
    "held": "现有证据支持该主张仍然成立。",
    "voided": "该主张已被后续证据推翻,不再成立。",
    "gap": "现有证据不足以确认该主张。",
}


def _external_reason(proj: dict[str, Any]) -> str:
    """模板 external_reason:纯规则,无 LLM;不含闸码/ADR/角色名。"""
    return _CLIENT_MEMO_CONCLUSIONS[_client_memo_bucket(proj)]


def _client_memo_pointback_ids(proj: dict[str, Any]) -> list[str]:
    """可点回 evidence_id:仅 T1;`doc_id#anchor@as_of`,不做字符级偏移。"""
    return [str(e) for e in (proj.get("t1_evidence_ids") or []) if e]


def _render_client_memo_entry(proj: dict[str, Any], *, gap_no_t1: bool = False) -> str:
    """单条:claim_id + 客户向结论句(external_reason 模板)+ 证据列表(纯文本)。

    「无 T1 覆盖」仅挂在缺口栏(gap_no_t1);仍成立/已作废不强制该文案。
    internal_reason / 机器 reason 不进客户向默认面(I-03);证据以纯文本呈现,
    不用 evidence: scheme(附录/点回由调用方按原文 id 自行映射,#677 story 24)。
    """
    cid = proj.get("claim_id") or ""
    conclusion = _external_reason(proj)
    eids = _client_memo_pointback_ids(proj)
    lines = [f"- **{cid}**: {conclusion}"]
    if eids:
        for eid in eids:
            # I-04(#695 决议 #689):主文可读句;括号保留完整原 id(纯文本无 scheme)
            lines.append(f"  - 证据: {display_evidence_id(eid)}（原文 `{eid}`）")
    elif gap_no_t1:
        lines.append("  - 证据: 无 T1 覆盖")
    return "\n".join(lines)


def _render_client_memo_section(
    title: str,
    entries: list[dict[str, Any]],
    *,
    empty_gap_explicit: bool = False,
) -> str:
    parts = [f"## {title}", ""]
    if not entries:
        if empty_gap_explicit:
            parts.append("- 无 T1 覆盖")
        else:
            parts.append("- (无)")
        parts.append("")
        return "\n".join(parts)
    for proj in entries:
        gap_no_t1 = empty_gap_explicit and not _client_memo_pointback_ids(proj)
        parts.append(_render_client_memo_entry(proj, gap_no_t1=gap_no_t1))
        parts.append("")
    return "\n".join(parts)


def _render_dem3_rubric_checklist() -> str:
    """DEM-3 人工勾选面:五条「是」+禁止项「无」;不升格为产品验证。"""
    return "\n".join(
        [
            "## DEM-3 人工 rubric(勾选面;不升格为产品验证)",
            "",
            "以下由人勾选;机器套件只锁字段/禁语边界,勾选结果不作通过线。",
            "",
            "- [ ] 有课题问题句与生成时间戳",
            "- [ ] 有免责声明(非法律意见/非自动决策;可标明 synthetic)",
            "- [ ] 三分栏齐全:仍成立/已作废/缺口",
            "- [ ] 每条有 claim_id + 一句话理由",
            "- [ ] 至少一条带可点回 evidence_id,或缺口栏显式写「无 T1 覆盖」",
            "- [ ] 禁止项全无:无「建议进入/不进入」;默认备忘正文无 Lead/Critic 字样",
            "",
        ]
    )


def render_client_memo_markdown(
    projections: list[dict[str, Any]],
    *,
    question: str = "",
    generated_at: str,
    synthetic: bool = False,
    needs_patch_banner: bool = False,
    include_dem3_rubric: bool = False,
) -> str:
    """客户向复验备忘 Markdown(ADR-0015 必填字段;禁轨迹与商业裁决句)。

    needs_patch_banner:发前钩子需补丁+ack 放行时强制页眉标明「需补丁」(ADR-0031);
    不扩商业裁决、不写轨迹。
    include_dem3_rubric:DEM-3 人工勾选面仅显式开启才挂(#674 拍板:默认剔除);
    机器套件只锁字段/禁语边界,勾选结果不作通过线。
    """
    held: list[dict[str, Any]] = []
    voided: list[dict[str, Any]] = []
    gap: list[dict[str, Any]] = []
    for proj in projections:
        bucket = _client_memo_bucket(proj)
        if bucket == "held":
            held.append(proj)
        elif bucket == "voided":
            voided.append(proj)
        else:
            gap.append(proj)

    disclaimer = _CLIENT_MEMO_DISCLAIMER
    if synthetic:
        disclaimer += "本导出所依据语料标明为 synthetic(合成评测包)。"

    parts = [
        "# 客户向复验备忘",
        "",
    ]
    # 需补丁页眉紧贴标题后,强制可见;字面量与闸约束对齐
    if needs_patch_banner:
        parts.extend([f"**{NEEDS_PATCH_BANNER}**", ""])
    parts.extend(
        [
            f"**课题问题句**: {_sanitize_client_memo_text(question) or '(未提供)'}",
            "",
            f"**生成时间**: {generated_at}",
            "",
            f"**{disclaimer}**",
            "",
            MEMO_NOTE,
            "",
            _render_client_memo_section("仍成立", held),
            _render_client_memo_section("已作废", voided),
            _render_client_memo_section("缺口", gap, empty_gap_explicit=True),
        ]
    )
    # DEM-3 人工 rubric 默认剔除(#674 拍板);仅显式开启时挂勾选面
    if include_dem3_rubric:
        parts.append(_render_dem3_rubric_checklist())
    return "\n".join(parts).rstrip() + "\n"


def export_client_memo_gated(
    *,
    run_id: str | None,
    disposition: str | None,
    projections: list[dict[str, Any]],
    generated_at: str,
    ack_needs_patch: bool = False,
    checksum_fresh: bool = True,
    question: str = "",
    synthetic: bool = False,
    out_path: str | Path | None = None,
) -> tuple[PublishHookResult, str | None]:
    """Client Memo 套发前钩子闸(#229 / ADR-0031)。

    先 evaluate_publish_hook;deny → 零写 out_path、markdown=None;
    allow → 渲染 ADR-0015 字段集;需补丁+ack 时强制页眉「需补丁」。
    UI/CLI 必须走本函数,禁止平行 if/else 出口。
    """
    hook = evaluate_publish_hook(
        run_id=run_id,
        disposition=disposition,
        ack_needs_patch=ack_needs_patch,
        checksum_fresh=checksum_fresh,
    )
    if not hook.allow:
        return hook, None

    md = render_client_memo_markdown(
        projections,
        question=question,
        generated_at=generated_at,
        synthetic=synthetic,
        needs_patch_banner=hook.requires_needs_patch_banner,
    )
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return hook, md


def export_client_memo_from_snapshot(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    generated_at: str,
    out_path: str | Path | None = None,
) -> str:
    """读复验投影 → 客户向备忘 Markdown;不跑复验。可选落盘。

    无闸渲染(字段契约/单测用)。发前导出请走 export_client_memo_from_snapshot_gated。
    """
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    md = render_client_memo_markdown(
        projections,
        question=str(snap.get("question") or ""),
        generated_at=generated_at,
        synthetic=bool(snap.get("synthetic")),
    )
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return md


def export_client_memo_from_snapshot_gated(
    snapshot_path: str | Path,
    store: RetrievalStore,
    *,
    run_id: str | None,
    generated_at: str,
    disposition: str | None = None,
    ack_needs_patch: bool = False,
    checksum_fresh: bool = True,
    out_path: str | Path | None = None,
) -> tuple[PublishHookResult, str | None]:
    """快照 → 套闸 Client Memo;deny 零写。disposition 缺省时由主张聚合。"""
    snap = load_snapshot(snapshot_path)
    claims = [claim_from_dict(c) for c in snap["claims"]]
    projections = [project_claim(store, c) for c in claims]
    disp = disposition if disposition is not None else disposition_for_claims(claims)
    # 快照可覆写 run_id(便于夹具自带绑定键)
    rid = run_id if run_id is not None else snap.get("run_id")
    return export_client_memo_gated(
        run_id=str(rid) if rid is not None else None,
        disposition=disp,
        projections=projections,
        generated_at=generated_at,
        ack_needs_patch=ack_needs_patch,
        checksum_fresh=checksum_fresh,
        question=str(snap.get("question") or ""),
        synthetic=bool(snap.get("synthetic")),
        out_path=out_path,
    )
