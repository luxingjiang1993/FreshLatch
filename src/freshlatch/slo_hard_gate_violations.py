"""SLO-02 硬闸不变量违例计数/清单出口（B6/B7/C5/D3/C3）。

只读挂接既有闸语义（confirm_patch / HumanLatch renew / rule_gate /
Agent 工具白名单 / 未确认草案扫描）；不改闸谓词、不放宽 fail-closed。

词汇（ops 页对齐）:
- block: 闸正确拒拦（B6/C3 可观察拒拦；周报「违例」期望仍为 0）
- violation: 不变量被突破（期望 0）
- scan_pass: B7 等显式扫描通过（违例=0）

权威指标表: docs/ops/生产补丁放行SLO.md
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, MutableSequence, Sequence

from freshlatch.evidence_bound import (
    PATCH_EMPTY_T1,
    PATCH_T1_NOT_ARCHIVED,
    PatchDraftStore,
    confirm_patch,
    propose_patch,
)
from freshlatch.gates.human_latch import VALID_ACTIONS, apply_decisions
from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch import patch_events as pe
from freshlatch.publish_hook import evaluate_publish_hook
from freshlatch.tools import CRITIC_TOOLS, LEAD_TOOLS_W3, LEAD_TOOLS_W9

# ops 页硬闸 ID（本出口覆盖集）
HARD_GATE_IDS: tuple[str, ...] = ("B6", "B7", "C5", "D3", "C3")

# B6：无/非法 t1 被 confirm 拒拦的 error_code
B6_BLOCK_CODES: frozenset[str] = frozenset({PATCH_EMPTY_T1, PATCH_T1_NOT_ARCHIVED})

# C3：续命无新 T1 / 非法证据被拒
C3_BLOCK_CODES: frozenset[str] = frozenset(
    {
        "RENEW_NO_EVIDENCE",
        "RENEW_EVIDENCE_MALFORMED",
        "RENEW_EVIDENCE_UNRESOLVED",
        "RENEW_EVIDENCE_NOT_T1",
    }
)

# D3：无 T1 不得 fresh
D3_BLOCK_CODES: frozenset[str] = frozenset({"NO_T1_EVIDENCE"})

# Agent 侧不得出现的「自红转绿」动词（与 VALID_ACTIONS 人审出口切开）
_AGENT_FORBIDDEN_GREEN_ACTIONS: frozenset[str] = frozenset({"renew", "mark_fresh", "confirm_patch"})


@dataclass(frozen=True)
class HardGateRecord:
    """单条可观察事件：拒拦 / 违例 / 扫描通过。"""

    slo_id: str
    kind: str  # block | violation | scan_pass
    detail: str
    error_code: str | None = None
    claim_id: str | None = None
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HardGateReport:
    """硬闸违例计数/清单聚合结果。"""

    records: list[HardGateRecord] = field(default_factory=list)

    def add(self, record: HardGateRecord) -> None:
        if record.slo_id not in HARD_GATE_IDS:
            raise ValueError(f"未知硬闸 ID: {record.slo_id}")
        if record.kind not in ("block", "violation", "scan_pass"):
            raise ValueError(f"未知 kind: {record.kind}")
        self.records.append(record)

    def count(self, slo_id: str, kind: str) -> int:
        return sum(1 for r in self.records if r.slo_id == slo_id and r.kind == kind)

    def blocks(self, slo_id: str) -> int:
        return self.count(slo_id, "block")

    def violations(self, slo_id: str) -> int:
        return self.count(slo_id, "violation")

    def week_fields(self) -> dict[str, Any]:
        """对齐 ops §6 周报最小字段：硬闸违例计数（期望 0）+ 拒拦可观察量。"""
        out: dict[str, Any] = {
            "hard_gate_violation_counts": {
                sid: self.violations(sid) for sid in HARD_GATE_IDS
            },
            "hard_gate_block_counts": {
                sid: self.blocks(sid) for sid in HARD_GATE_IDS
            },
            "targets": {
                "B6_violations": 0,
                "B7_violations": 0,
                "C5_violations": 0,
                "D3_violations": 0,
                "C3_violations": 0,
                "B6_block_rate_approx": "≈100%（拒拦可观察）",
                "C3_renew_with_t1": "100%",
            },
            "records": [r.to_dict() for r in self.records],
        }
        return out

    def to_dict(self) -> dict[str, Any]:
        return self.week_fields()


def classify_confirm_reject(error_code: str | None) -> str | None:
    """confirm 拒拦码 → B6；其它码不归本出口。"""
    if error_code in B6_BLOCK_CODES:
        return "B6"
    return None


def classify_renew_reject(error_code: str | None) -> str | None:
    """renew 拒拦码 → C3。"""
    if error_code in C3_BLOCK_CODES:
        return "C3"
    return None


def classify_rule_gate_reject(error_code: str | None) -> str | None:
    """rule_gate 拒绿码 → D3（无 T1 fresh）。"""
    if error_code in D3_BLOCK_CODES:
        return "D3"
    return None


def record_confirm_outcome(
    report: HardGateReport,
    *,
    ok: bool,
    error_code: str | None,
    claim_id: str,
    detail: str = "",
    source: str = "confirm_patch",
) -> None:
    """只读挂接 confirm 结果：B6 拒拦记 block；若无证却 ok 则记 violation。"""
    if not ok:
        slo = classify_confirm_reject(error_code)
        if slo == "B6":
            report.add(
                HardGateRecord(
                    slo_id="B6",
                    kind="block",
                    detail=detail or f"confirm 拒拦: {error_code}",
                    error_code=error_code,
                    claim_id=claim_id,
                    source=source,
                )
            )
        return
    # 成功路径不应是无证——若调用方误报空证成功，记违例
    if error_code in B6_BLOCK_CODES:
        report.add(
            HardGateRecord(
                slo_id="B6",
                kind="violation",
                detail="无证/非法 t1 却 confirm 成功（不变量突破）",
                error_code=error_code,
                claim_id=claim_id,
                source=source,
            )
        )


def record_renew_outcome(
    report: HardGateReport,
    *,
    ok: bool,
    error_code: str | None,
    claim_id: str,
    validity_basis_before: dict | None,
    validity_basis_after: dict | None,
    detail: str = "",
    source: str = "human_latch.renew",
) -> None:
    """只读挂接 renew：无新 T1 拒拦 → C3 block；拒拦却写了 basis → violation。"""
    if not ok:
        slo = classify_renew_reject(error_code)
        if slo == "C3":
            report.add(
                HardGateRecord(
                    slo_id="C3",
                    kind="block",
                    detail=detail or f"renew 拒拦: {error_code}",
                    error_code=error_code,
                    claim_id=claim_id,
                    source=source,
                )
            )
            if validity_basis_after != validity_basis_before:
                report.add(
                    HardGateRecord(
                        slo_id="C3",
                        kind="violation",
                        detail="renew 拒绝后仍写入 validity_basis",
                        error_code=error_code,
                        claim_id=claim_id,
                        source=source,
                    )
                )
        return


def scan_b7_unconfirmed_drafts(
    report: HardGateReport,
    *,
    claims: Sequence[Claim] | Mapping[str, Claim],
    drafts: PatchDraftStore,
    run_id: str,
    events_dir: Path | None,
    statement_snapshots: Mapping[str, str],
    source: str = "b7_scan",
) -> None:
    """B7：未 confirm 草案不得改正文/正式 patch_events。

    通过 → scan_pass（违例计数 0）；发现泄漏 → violation。
    """
    if isinstance(claims, Mapping):
        by_id = dict(claims)
    else:
        by_id = {c.claim_id: c for c in claims}

    draft_map = drafts.list_for_run(run_id)
    events = pe.read_events(events_dir=events_dir) if events_dir is not None else []
    formal_claim_ids = {
        str(ev.get("claim_id"))
        for ev in events
        if ev.get("human_confirm") is True and ev.get("arm") == pe.PRODUCT_ARM
    }

    leaked = False
    for claim_id, draft in draft_map.items():
        claim = by_id.get(claim_id)
        snap = statement_snapshots.get(claim_id)
        if claim is not None and snap is not None and claim.statement != snap:
            if claim.statement == draft.after_text:
                leaked = True
                report.add(
                    HardGateRecord(
                        slo_id="B7",
                        kind="violation",
                        detail="未 confirm 草案已覆盖主张正文",
                        claim_id=claim_id,
                        source=source,
                    )
                )
        if claim_id in formal_claim_ids:
            # 仍有未丢弃草案却已有正式确认行：视为出门违例形状
            leaked = True
            report.add(
                HardGateRecord(
                    slo_id="B7",
                    kind="violation",
                    detail="未丢弃草案同时存在正式 patch_events 确认行",
                    claim_id=claim_id,
                    source=source,
                )
            )

    if not leaked:
        report.add(
            HardGateRecord(
                slo_id="B7",
                kind="scan_pass",
                detail="未确认草案扫描通过：正文未改、无对应正式确认行",
                source=source,
            )
        )


def probe_d3_no_t1_fresh(
    report: HardGateReport,
    *,
    claim: Claim | None = None,
    source: str = "rule_gate",
) -> None:
    """D3：无 T1 置 fresh 必须失败；违例目标语义=0（记 block，不记 violation）。"""
    c = claim or Claim(claim_id="slo-d3", statement="探针主张", status="stale")
    result = rule_gate(
        c,
        GateDecision(status="fresh", t1_evidence_ids=[], auditor_verdict="fresh"),
        GateContext(),
    )
    if not result.green and result.error_code in D3_BLOCK_CODES:
        report.add(
            HardGateRecord(
                slo_id="D3",
                kind="block",
                detail=result.reason or "无 T1 不得 fresh",
                error_code=result.error_code,
                claim_id=c.claim_id,
                source=source,
            )
        )
        return
    if result.green:
        report.add(
            HardGateRecord(
                slo_id="D3",
                kind="violation",
                detail="无 T1 却发出绿灯（D3 突破）",
                error_code=result.error_code,
                claim_id=c.claim_id,
                source=source,
            )
        )


def probe_c5_agent_cannot_self_green(
    report: HardGateReport,
    *,
    source: str = "agent_tools+rule_gate",
) -> None:
    """C5：Agent 不得自红转绿。

    机检：Agent 白名单不含 renew/mark_fresh；且红灯主张无 T1 不得经闸转绿。
    目标违例计数语义=0。
    """
    agent_tools = set(LEAD_TOOLS_W3) | set(LEAD_TOOLS_W9) | set(CRITIC_TOOLS)
    forbidden_present = sorted(agent_tools & _AGENT_FORBIDDEN_GREEN_ACTIONS)
    if forbidden_present:
        report.add(
            HardGateRecord(
                slo_id="C5",
                kind="violation",
                detail=f"Agent 白名单含自转绿动词: {forbidden_present}",
                source=source,
            )
        )
    else:
        report.add(
            HardGateRecord(
                slo_id="C5",
                kind="block",
                detail="Agent 白名单不含 renew/mark_fresh/confirm_patch",
                source=source,
            )
        )

    # 红灯主张试图无证 fresh：须失败（与 D3 同构；C5 语义=Agent 不得私转绿）
    red = Claim(claim_id="slo-c5", statement="红灯探针", status="stale", reason="机器判 stale")
    gate = rule_gate(
        red,
        GateDecision(status="fresh", t1_evidence_ids=[], auditor_verdict="fresh"),
        GateContext(),
    )
    if gate.green:
        report.add(
            HardGateRecord(
                slo_id="C5",
                kind="violation",
                detail="红灯主张无证经闸转绿（Agent 自红转绿形状）",
                error_code=gate.error_code,
                claim_id=red.claim_id,
                source=source,
            )
        )
    else:
        report.add(
            HardGateRecord(
                slo_id="C5",
                kind="block",
                detail="红灯无证 fresh 被闸打回（保持不得私转绿）",
                error_code=gate.error_code,
                claim_id=red.claim_id,
                source=source,
            )
        )

    # HumanLatch 人审出口封闭：confirm_patch 不得进 VALID_ACTIONS
    if "confirm_patch" in VALID_ACTIONS or "mark_fresh" in VALID_ACTIONS:
        report.add(
            HardGateRecord(
                slo_id="C5",
                kind="violation",
                detail="VALID_ACTIONS 非法扩容纳自转绿动词",
                source=source,
            )
        )


def probe_publish_hook_fail_closed(
    report: HardGateReport,
    *,
    source: str = "publish_hook",
) -> None:
    """只读挂接 publish_hook：缺绑定 fail-closed（佐证未确认/未绑不得出门，非独立 SLO ID）。"""
    denied = evaluate_publish_hook(run_id=None, disposition="可发")
    if denied.allow:
        report.add(
            HardGateRecord(
                slo_id="B7",
                kind="violation",
                detail="publish_hook 缺 run_id 却放行",
                error_code=denied.code,
                source=source,
            )
        )


def run_acceptance_probes(
    *,
    tmp_events_dir: Path,
    store: Any | None = None,
) -> HardGateReport:
    """跑齐 SLO-02 四条 Acceptance 探针，产出可填周报的计数/清单。

    零 LLM；复用既有 confirm / renew / rule_gate；不改闸谓词。
    store 若给出则用于 renew 点回（InMemory/SQLite 均可）；缺省用进程内假 store。
    """
    report = HardGateReport()
    archived = "slo-doc#p1@T1"

    # --- B6: 无合法 t1_ids confirm → 拒拦可观察 ---
    claims_b6: MutableSequence[Claim] = [
        Claim(claim_id="b6-c1", statement="旧正文", status="unknown"),
    ]
    before_stmt = claims_b6[0].statement
    r_empty = confirm_patch(
        claim_id="b6-c1",
        claims=claims_b6,
        archived_t1_ids={archived},
        after_text="试图无证改稿",
        t1_ids=[],
        minutes=1.0,
        events_dir=tmp_events_dir,
        reverify_fn=lambda c: (c.status, "noop"),
    )
    record_confirm_outcome(
        report,
        ok=r_empty.ok,
        error_code=r_empty.error_code,
        claim_id="b6-c1",
        detail=r_empty.detail,
    )
    if r_empty.ok or claims_b6[0].statement != before_stmt:
        report.add(
            HardGateRecord(
                slo_id="B6",
                kind="violation",
                detail="无证 confirm 未拒或已改正文",
                claim_id="b6-c1",
                source="confirm_patch",
            )
        )

    r_bad = confirm_patch(
        claim_id="b6-c1",
        claims=claims_b6,
        archived_t1_ids={archived},
        after_text="非法 id 改稿",
        t1_ids=["other#x@T1"],
        minutes=1.0,
        events_dir=tmp_events_dir,
        reverify_fn=lambda c: (c.status, "noop"),
    )
    record_confirm_outcome(
        report,
        ok=r_bad.ok,
        error_code=r_bad.error_code,
        claim_id="b6-c1",
        detail=r_bad.detail,
    )

    # --- B7: 未 confirm 草案不出门 ---
    claims_b7 = [Claim(claim_id="b7-c1", statement="草案前正文", status="stale")]
    snaps = {"b7-c1": claims_b7[0].statement}
    drafts = PatchDraftStore()
    propose_patch(
        claim_id="b7-c1",
        after_text="仅暂存草案句",
        claims=claims_b7,
        drafts=drafts,
        run_id="slo-b7",
        t1_ids=[archived],
    )
    scan_b7_unconfirmed_drafts(
        report,
        claims=claims_b7,
        drafts=drafts,
        run_id="slo-b7",
        events_dir=tmp_events_dir,
        statement_snapshots=snaps,
    )
    probe_publish_hook_fail_closed(report)

    # --- D3 / C5 ---
    probe_d3_no_t1_fresh(report)
    probe_c5_agent_cannot_self_green(report)

    # --- C3: renew 无新 T1 → 拒绝且不写 validity_basis ---
    claim_c3 = Claim(
        claim_id="c3-c1",
        statement="续命探针",
        status="stale",
        reason="机器判 stale",
        validity_basis=None,
    )
    basis_before = claim_c3.validity_basis
    effective_store = store if store is not None else _NullRenewStore()
    results = apply_decisions(
        effective_store,
        {"c3-c1": claim_c3},
        [{"claim_id": "c3-c1", "action": "renew"}],
    )
    row = results[0]
    record_renew_outcome(
        report,
        ok=bool(row.get("ok")),
        error_code=row.get("error_code"),
        claim_id="c3-c1",
        validity_basis_before=basis_before,
        validity_basis_after=claim_c3.validity_basis,
        detail=str(row.get("detail") or ""),
    )
    if claim_c3.validity_basis is not None:
        report.add(
            HardGateRecord(
                slo_id="C3",
                kind="violation",
                detail="renew 无 T1 后 validity_basis 非空",
                claim_id="c3-c1",
                source="human_latch.renew",
            )
        )
    if claim_c3.status == "fresh":
        report.add(
            HardGateRecord(
                slo_id="C3",
                kind="violation",
                detail="renew 无 T1 后 status 被置 fresh",
                claim_id="c3-c1",
                source="human_latch.renew",
            )
        )

    return report


class _NullRenewStore:
    """最小 store：无 chunk / 空作废名单，供 C3 无证 renew 探针。"""

    def list_invalidation(self) -> list[str]:
        return []

    def get_chunk(self, *args: Any, **kwargs: Any) -> None:
        return None

    def log_latch(self, *args: Any, **kwargs: Any) -> None:
        return None

    def add_invalidation(self, *args: Any, **kwargs: Any) -> None:
        return None

    def list_latch_events(self, claim_id: str | None = None) -> list[dict]:
        return []


def format_report_text(report: HardGateReport) -> str:
    """人读清单（中文，无 emoji）。"""
    fields = report.week_fields()
    lines = [
        "SLO-02 硬闸违例计数/清单（B6/B7/C5/D3/C3）",
        "",
        "违例计数（目标均为 0）:",
    ]
    for sid, n in fields["hard_gate_violation_counts"].items():
        lines.append(f"  {sid}: {n}")
    lines.append("")
    lines.append("拒拦/扫描可观察计数:")
    for sid, n in fields["hard_gate_block_counts"].items():
        lines.append(f"  {sid} blocks: {n}")
    b7_pass = report.count("B7", "scan_pass")
    lines.append(f"  B7 scan_pass: {b7_pass}")
    lines.append("")
    lines.append("清单:")
    if not report.records:
        lines.append("  （空）")
    else:
        for r in report.records:
            code = f" code={r.error_code}" if r.error_code else ""
            cid = f" claim={r.claim_id}" if r.claim_id else ""
            lines.append(f"  [{r.slo_id}/{r.kind}] {r.detail}{code}{cid}")
    return "\n".join(lines) + "\n"
