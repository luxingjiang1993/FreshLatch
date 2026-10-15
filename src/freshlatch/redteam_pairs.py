"""红队成对夹具的单一路径。应拒与不应拒都从这里进入既有闸。

本模块不发明新的安全策略,也不调用外网扫描。
红队成对回归不等于完整对抗安全认证。
"""

from __future__ import annotations

from typing import Any, Callable

from freshlatch.gates.rule_gate import GateContext, GateDecision, rule_gate
from freshlatch.models import Claim
from freshlatch.roles.conflict_evidence import fresh_refusal_for_conflicting_evidence
from freshlatch.serving.acl import enforce_mapped_action
from freshlatch.tools import (
    REASON_ILLEGAL_TOOL_ARGS,
    dispatch_tiered_tool,
    tool_schema_error,
    tool_specs,
)

DISPOSITION_DENY = "deny"
DISPOSITION_ABSTAIN = "abstain"
DISPOSITION_ALLOW = "allow"

_KINDS = frozenset({"injection", "conflict", "tool_schema", "acl"})
_INJECTION_EVIDENCE_ID = "redteam-pair#p1@T1"


def run_redteam_fixture(kind: str, fixture: dict[str, Any]) -> dict[str, Any]:
    """按种类把一侧夹具送进既有入口,并给出 disposition。

    deny 与 abstain 都是应拒。allow 表示这一侧没有被拒。
    未知种类直接报错,不把未识别夹具当成放行。
    """
    if kind not in _KINDS:
        raise ValueError(f"未知红队夹具种类: {kind}")
    if kind == "injection":
        return _run_injection(fixture)
    if kind == "conflict":
        return _run_conflict(fixture)
    if kind == "tool_schema":
        return _run_tool_schema(fixture)
    return _run_acl(fixture)


def _outcome(
    disposition: str,
    *,
    fail_closed: bool,
    code: str | None,
    **extra: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "disposition": disposition,
        "fail_closed": fail_closed,
        "code": code,
    }
    body.update(extra)
    return body


def _run_injection(fixture: dict[str, Any]) -> dict[str, Any]:
    """间接注入与近邻措辞走同一条 rule_gate 绿灯请求。"""
    claim = Claim(
        claim_id="redteam-inj",
        statement="目标市场月活环比上升",
        t0_evidence_ids=["t0-channel#p1"],
    )
    decision = GateDecision(
        status="fresh",
        t1_evidence_ids=[_INJECTION_EVIDENCE_ID],
        auditor_verdict="fresh",
        t1_evidence_texts=[fixture["text"]],
    )
    result = rule_gate(
        claim,
        decision,
        GateContext(checksum_fn=lambda doc_id, as_of: None),
    )
    if result.green:
        disposition = DISPOSITION_ALLOW
    elif result.allowed:
        disposition = DISPOSITION_ABSTAIN
    else:
        disposition = DISPOSITION_DENY
    return _outcome(
        disposition,
        fail_closed=False,
        code=result.error_code,
        green=result.green,
        allowed=result.allowed,
    )


def _run_conflict(fixture: dict[str, Any]) -> dict[str, Any]:
    """互斥 @T1 与同值 @T1 都问 fresh 拒答函数。没有互斥对则不拒。"""
    refusal = fresh_refusal_for_conflicting_evidence(fixture["tool_trace"])
    if refusal is None:
        return _outcome(DISPOSITION_ALLOW, fail_closed=False, code=None)
    disposition = DISPOSITION_ABSTAIN if refusal.get("abstain") is True else DISPOSITION_DENY
    return _outcome(
        disposition,
        fail_closed=False,
        code=refusal.get("reason_code"),
    )


def _run_tool_schema(fixture: dict[str, Any]) -> dict[str, Any]:
    """先按已发给模型的 schema 再验,合法才进入权限档调度。"""
    name = fixture["name"]
    args = fixture["args"]
    handler: Callable[[dict], dict] = fixture["handler"]
    spec = tool_specs([name])[0]
    schema_error = tool_schema_error(spec, args)
    if schema_error:
        return _outcome(
            DISPOSITION_DENY,
            fail_closed=False,
            code=REASON_ILLEGAL_TOOL_ARGS,
            executed=False,
            error=schema_error,
        )
    trajectory: list[dict] = []
    called = {"n": 0}

    def wrapped(payload: dict) -> dict:
        called["n"] += 1
        return handler(payload)

    result = dispatch_tiered_tool(name, args, wrapped, trajectory=trajectory)
    if called["n"] == 0:
        observation = trajectory[-1]
        return _outcome(
            DISPOSITION_DENY,
            fail_closed=observation.get("fail_closed") is True,
            code=observation.get("reason_code"),
            executed=False,
        )
    return _outcome(
        DISPOSITION_ALLOW,
        fail_closed=False,
        code=None,
        executed=True,
        result=result,
    )


def _run_acl(fixture: dict[str, Any]) -> dict[str, Any]:
    """读、写、会话都先过 authorize_session。拒绝时不把语料放进观察。"""
    outcome = enforce_mapped_action(
        fixture["store"],
        fixture["action"],
        authorization=fixture.get("authorization"),
        api_key=fixture.get("api_key"),
        client_tenant=fixture.get("client_tenant"),
        query=fixture.get("query") or "",
        document=fixture.get("document"),
        chunks=fixture.get("chunks"),
    )
    if outcome.get("ok") is not True:
        denied = _outcome(
            DISPOSITION_DENY,
            fail_closed=outcome.get("fail_closed") is True,
            code=outcome.get("code"),
            action=outcome.get("action"),
        )
        if "status_code" in outcome:
            denied["status_code"] = outcome["status_code"]
        return denied
    doc_ids = [
        hit.doc_id
        for hit in outcome.get("hits") or []
        if isinstance(getattr(hit, "doc_id", None), str)
    ]
    allowed = _outcome(
        DISPOSITION_ALLOW,
        fail_closed=False,
        code=outcome.get("code"),
        action=outcome.get("action"),
        tenant_id=outcome.get("tenant_id"),
        doc_ids=doc_ids,
    )
    if "status_code" in outcome:
        allowed["status_code"] = outcome["status_code"]
    return allowed
