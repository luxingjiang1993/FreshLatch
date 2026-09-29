"""Evidence-bound 补丁证据包导出(ADR-0029 / #201)。

同次合法 confirm(或显式导出)产出 JSON + 短 Markdown,至少含:
before/after、t1 指针、确认者、再验前后 disposition。

与 Client Memo(ADR-0015)分轨:不复用客户备忘字段集,不冒充审计包。
只读组装 patch_events / confirm 结果;禁止引入 Streamlit 第二栈;无 C|T UX。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

# 分轨标记:与 Client Memo / 复验单导出区分
EXPORT_KIND = "evidence_bound_patch"
EXPORT_SCHEMA = "freshlatch.evidence_bound_export.v1"

# JSON 关键字段(验收用)
REQUIRED_JSON_KEYS: tuple[str, ...] = (
    "kind",
    "schema",
    "claim_id",
    "before_text",
    "after_text",
    "t1_ids",
    "confirmer",
    "disposition_before",
    "disposition_after",
)


class PatchExportError(ValueError):
    """导出组装失败(缺关键字段等)。"""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class PatchExportBundle:
    """同次补丁证据包:机读 JSON 载荷 + 人读短 Markdown。"""

    json_payload: dict[str, Any]
    markdown: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "json_payload": dict(self.json_payload),
            "markdown": self.markdown,
        }


def _normalize_t1_ids(t1_ids: Sequence[str]) -> list[str]:
    return [str(x).strip() for x in t1_ids if str(x).strip()]


def _normalize_checksums(
    t1_ids: Sequence[str],
    t1_checksums: Mapping[str, str] | None,
) -> dict[str, str]:
    """仅保留落在 t1_ids 上的 checksum 指针;缺省为空 dict。"""
    if not t1_checksums:
        return {}
    allowed = set(t1_ids)
    return {
        str(k): str(v)
        for k, v in t1_checksums.items()
        if str(k) in allowed and str(v).strip()
    }


def build_patch_export(
    *,
    claim_id: str,
    before_text: str,
    after_text: str,
    t1_ids: Sequence[str],
    confirmer: str,
    disposition_before: str,
    disposition_after: str,
    t1_checksums: Mapping[str, str] | None = None,
    minutes: float | None = None,
    patch_span: str | None = None,
    arm: str | None = None,
    ts: str | None = None,
    reverify: bool | None = None,
    human_confirm: bool | None = None,
) -> PatchExportBundle:
    """组装同次补丁证据包(不经 Client Memo 字段集)。

    disposition_before / disposition_after 分别对应再验前/后再验包结论。
    """
    cid = (claim_id or "").strip()
    if not cid:
        raise PatchExportError("claim_id 不可为空")
    who = (confirmer or "").strip()
    if not who:
        raise PatchExportError("confirmer(确认者)不可为空")
    before_disp = (disposition_before or "").strip()
    after_disp = (disposition_after or "").strip()
    if not before_disp or not after_disp:
        raise PatchExportError("再验前后 disposition 均不可为空")

    ids = _normalize_t1_ids(t1_ids)
    checksums = _normalize_checksums(ids, t1_checksums)
    exported_at = ts or _utc_now()

    payload: dict[str, Any] = {
        "kind": EXPORT_KIND,
        "schema": EXPORT_SCHEMA,
        "claim_id": cid,
        "before_text": str(before_text),
        "after_text": str(after_text),
        "t1_ids": ids,
        "t1_checksums": checksums,
        "confirmer": who,
        "disposition_before": before_disp,
        "disposition_after": after_disp,
        "exported_at": exported_at,
    }
    if minutes is not None:
        payload["minutes"] = float(minutes)
    if patch_span is not None:
        payload["patch_span"] = patch_span
    if arm is not None:
        # 审计回放字段;非 UX 开关
        payload["arm"] = str(arm)
    if reverify is not None:
        payload["reverify"] = bool(reverify)
    if human_confirm is not None:
        payload["human_confirm"] = bool(human_confirm)

    md = render_patch_export_markdown(payload)
    return PatchExportBundle(json_payload=payload, markdown=md)


def render_patch_export_markdown(payload: Mapping[str, Any]) -> str:
    """短 Markdown:审计可读,刻意不含 Client Memo 三分栏/免责声明/DEM-3。"""
    t1_lines: list[str] = []
    checksums = payload.get("t1_checksums") or {}
    for eid in payload.get("t1_ids") or []:
        cs = checksums.get(eid) if isinstance(checksums, Mapping) else None
        if cs:
            t1_lines.append(f"- `{eid}` (checksum=`{cs}`)")
        else:
            t1_lines.append(f"- `{eid}`")
    if not t1_lines:
        t1_lines = ["- (无)"]

    parts = [
        "# Evidence-bound 补丁证据包",
        "",
        f"- **kind**: `{payload.get('kind')}`",
        f"- **schema**: `{payload.get('schema')}`",
        f"- **claim_id**: `{payload.get('claim_id')}`",
        f"- **确认者**: {payload.get('confirmer')}",
        f"- **exported_at**: {payload.get('exported_at')}",
    ]
    if "minutes" in payload:
        parts.append(f"- **minutes**: {payload['minutes']}")
    if "patch_span" in payload:
        parts.append(f"- **patch_span**: {payload['patch_span']}")
    parts.extend(
        [
            "",
            "## before / after",
            "",
            f"**before_text**: {payload.get('before_text')}",
            "",
            f"**after_text**: {payload.get('after_text')}",
            "",
            "## t1 指针",
            "",
            *t1_lines,
            "",
            "## 再验前后 disposition",
            "",
            f"- **再验前**: {payload.get('disposition_before')}",
            f"- **再验后**: {payload.get('disposition_after')}",
            "",
        ]
    )
    return "\n".join(parts).rstrip() + "\n"


def export_from_patch_event(
    event: Mapping[str, Any],
    *,
    disposition_after: str,
    confirmer: str | None = None,
    t1_checksums: Mapping[str, str] | None = None,
) -> PatchExportBundle:
    """显式导出:从正式 patch_events 行 + 再验后 disposition 组装。

    再验前 disposition 取事件 ``before_disp``;确认者默认事件 ``actor``。
    要求事件已含 before_text/after_text(正式确认行)。
    """
    if "before_text" not in event or "after_text" not in event:
        raise PatchExportError("正式确认行须含 before_text/after_text 方可导出")
    before_disp = str(event.get("before_disp") or "").strip()
    if not before_disp:
        raise PatchExportError("事件缺 before_disp(再验前 disposition)")
    who = (confirmer if confirmer is not None else str(event.get("actor") or "")).strip()
    t1_ids = event.get("t1_ids") or []
    if not isinstance(t1_ids, list):
        raise PatchExportError("事件 t1_ids 须为 list")
    return build_patch_export(
        claim_id=str(event.get("claim_id") or ""),
        before_text=str(event["before_text"]),
        after_text=str(event["after_text"]),
        t1_ids=t1_ids,
        confirmer=who,
        disposition_before=before_disp,
        disposition_after=disposition_after,
        t1_checksums=t1_checksums,
        minutes=float(event["minutes"]) if "minutes" in event else None,
        patch_span=event.get("patch_span"),
        arm=str(event["arm"]) if "arm" in event else None,
        ts=str(event["ts"]) if event.get("ts") else None,
        reverify=bool(event["reverify"]) if "reverify" in event else None,
        human_confirm=bool(event["human_confirm"]) if "human_confirm" in event else None,
    )


def export_from_confirm_result(
    result: Any,
    *,
    disposition_before: str | None = None,
    disposition_after: str | None = None,
    t1_checksums: Mapping[str, str] | None = None,
) -> PatchExportBundle:
    """从成功 ConfirmPatchResult 组装;失败 raise。

    默认:再验前=事件 before_disp;再验后=result.disposition。
    #199 真接线后再验若改包结论,可显式传入 disposition_after 覆盖。
    """
    if not getattr(result, "ok", False):
        raise PatchExportError("仅成功 confirm 可导出补丁证据包")
    event = getattr(result, "event", None) or {}
    if not isinstance(event, Mapping):
        event = {}

    before_disp = (disposition_before or "").strip() or str(event.get("before_disp") or "").strip()
    after_disp = (disposition_after or "").strip() or str(
        getattr(result, "disposition", None) or ""
    ).strip()
    if not before_disp:
        raise PatchExportError("无法解析再验前 disposition(需 disposition_before 或事件 before_disp)")
    if not after_disp:
        raise PatchExportError("无法解析再验后 disposition(需 disposition_after 或 result.disposition)")

    before_text = getattr(result, "before_text", None)
    after_text = getattr(result, "after_text", None)
    if before_text is None:
        before_text = event.get("before_text", "")
    if after_text is None:
        after_text = event.get("after_text", "")

    t1_ids = event.get("t1_ids") if isinstance(event.get("t1_ids"), list) else []
    confirmer = str(event.get("actor") or "human")

    return build_patch_export(
        claim_id=str(getattr(result, "claim_id", "") or event.get("claim_id") or ""),
        before_text=str(before_text),
        after_text=str(after_text),
        t1_ids=t1_ids,
        confirmer=confirmer,
        disposition_before=before_disp,
        disposition_after=after_disp,
        t1_checksums=t1_checksums,
        minutes=float(event["minutes"]) if "minutes" in event else None,
        patch_span=event.get("patch_span"),
        arm=str(event["arm"]) if "arm" in event else None,
        ts=str(event["ts"]) if event.get("ts") else None,
        reverify=bool(event["reverify"]) if "reverify" in event else None,
        human_confirm=bool(event["human_confirm"]) if "human_confirm" in event else None,
    )


def write_patch_export(
    bundle: PatchExportBundle,
    out_dir: Path | str,
    *,
    stem: str = "evidence_bound_patch",
) -> tuple[Path, Path]:
    """写入同次 JSON + Markdown 两份文件;返回 (json_path, md_path)。"""
    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / f"{stem}.json"
    md_path = root / f"{stem}.md"
    json_path.write_text(
        json.dumps(bundle.json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(bundle.markdown, encoding="utf-8")
    return json_path, md_path


def assert_required_json_keys(payload: Mapping[str, Any]) -> None:
    """验收辅助:缺关键键即 raise。"""
    missing = [k for k in REQUIRED_JSON_KEYS if k not in payload]
    if missing:
        raise PatchExportError(f"导出 JSON 缺关键字段: {', '.join(missing)}")
