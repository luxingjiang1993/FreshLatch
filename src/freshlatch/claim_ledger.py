"""主张台账只读投影(ADR-0031 / #228)。

真源 = invalidation_list ∪ latch_log(discard/renew)。
零新 SQLite 写表;不改 human_latch 写路径;不与 patch_events 糊缝。
renew 永不进入作废名单查询结果(与既有闸语义一致)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from freshlatch.store.base import RetrievalStore

# 台账投影只收人审作废/续命;rerun 等其它 latch 动作不进台账
LEDGER_ACTIONS = frozenset({"discard", "renew"})

ACTION_LABELS = {"discard": "人审作废", "renew": "人审续命"}


def get_claim_ledger(
    store: RetrievalStore,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """只读合并投影:作废名单 ∪ latch_log(discard/renew)。

    run_id 给定时仅保留 latch_log.run_id 匹配的人审行;
    作废名单仍按既有 list_invalidation 全量返回(跨 Run 持久,与闸语义一致),
    但 entries 内 discard 行仍受 run_id 过滤。
    """
    invalidation_ids = list(store.list_invalidation())
    # renew 不得出现在作废名单——由写路径保证;此处只读断言友好字段
    if hasattr(store, "list_latch_rows"):
        latch_rows = store.list_latch_rows()
    else:
        latch_rows = []

    entries: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()
    for row in latch_rows:
        action = row.get("action")
        if action not in LEDGER_ACTIONS:
            continue
        row_run = row.get("run_id")
        if run_id is not None and row_run != run_id:
            continue
        key = (
            str(row.get("claim_id") or ""),
            str(action),
            str(row.get("ts") or ""),
            str(row.get("evidence_id") or ""),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        entries.append(
            {
                "claim_id": str(row.get("claim_id") or ""),
                "action": str(action),
                "ts": str(row.get("ts") or ""),
                "evidence_id": row.get("evidence_id"),
                "actor": row.get("actor") or "human",
                "run_id": row_run,
                "reviewer_note": row.get("reviewer_note"),
                "machine_status_before": row.get("machine_status_before"),
                "override": row.get("override"),
                "label": ACTION_LABELS.get(str(action), str(action)),
                "source": "latch_log",
            }
        )

    # 作废名单有、但 latch_log 无对应 discard 的孤儿(旧库/异常);补进投影,仍标 discard
    discard_from_latch = {e["claim_id"] for e in entries if e["action"] == "discard"}
    if run_id is None:
        for cid in invalidation_ids:
            if cid in discard_from_latch:
                continue
            entries.append(
                {
                    "claim_id": cid,
                    "action": "discard",
                    "ts": "",
                    "evidence_id": None,
                    "actor": "human",
                    "run_id": None,
                    "reviewer_note": None,
                    "machine_status_before": None,
                    "override": None,
                    "label": ACTION_LABELS["discard"],
                    "source": "invalidation_list",
                }
            )

    entries.sort(key=lambda e: (e.get("ts") or "", e.get("claim_id") or "", e.get("action") or ""))

    discard_ids = sorted({e["claim_id"] for e in entries if e["action"] == "discard"})
    renew_ids = sorted({e["claim_id"] for e in entries if e["action"] == "renew"})

    return {
        "run_id": run_id,
        "entries": entries,
        "discard_claim_ids": discard_ids,
        "renew_claim_ids": renew_ids,
        # 作废名单单一真相只读投影;renew 永不在此列表
        "invalidation_claim_ids": list(invalidation_ids),
    }


def export_claim_ledger_md(
    store: RetrievalStore,
    *,
    run_id: str | None = None,
    out_path: str | Path | None = None,
) -> str:
    """主张台账 Markdown 导出(只读;不写库表)。"""
    ledger = get_claim_ledger(store, run_id=run_id)
    md = render_claim_ledger_markdown(ledger)
    if out_path is not None:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
    return md


def render_claim_ledger_markdown(ledger: dict[str, Any]) -> str:
    """把 get_claim_ledger 产物渲成 Markdown。"""
    lines: list[str] = ["# 主张台账", ""]
    scope = ledger.get("run_id")
    if scope:
        lines.append(f"范围: Run `{scope}`")
    else:
        lines.append("范围: 全库(跨 Run 作废名单 + 人审 latch_log)")
    lines.append("")
    lines.append("写路径仍唯一经 HumanLatch;`invalidation_list` ∪ `latch_log`(discard/renew)只读投影。")
    lines.append("续命(renew)不进作废名单。与 `patch_events` 分缝。")
    lines.append("")

    discard_ids = ledger.get("discard_claim_ids") or []
    renew_ids = ledger.get("renew_claim_ids") or []
    void_ids = ledger.get("invalidation_claim_ids") or []
    lines.append("## 摘要")
    lines.append("")
    lines.append(f"- 作废(discard) claim_id: {', '.join(f'`{c}`' for c in discard_ids) or '(无)'}")
    lines.append(f"- 续命(renew) claim_id: {', '.join(f'`{c}`' for c in renew_ids) or '(无)'}")
    lines.append(
        f"- 作废名单(invalidation_list, renew∉此列): "
        f"{', '.join(f'`{c}`' for c in void_ids) or '(无)'}"
    )
    lines.append("")

    lines.append("## 条目")
    lines.append("")
    entries = ledger.get("entries") or []
    if not entries:
        lines.append("(尚无人审作废/续命记录)")
        lines.append("")
        return "\n".join(lines)

    for e in entries:
        label = e.get("label") or ACTION_LABELS.get(e.get("action", ""), e.get("action", ""))
        ts = e.get("ts") or "(无时间戳)"
        cid = e.get("claim_id") or ""
        line = f"- `{cid}` · {label} · {ts}"
        if e.get("evidence_id"):
            line += f" · evidence `{e['evidence_id']}`"
        if e.get("run_id"):
            line += f" · run `{e['run_id']}`"
        if e.get("source") == "invalidation_list":
            line += " · 源 invalidation_list"
        lines.append(line)
    lines.append("")
    return "\n".join(lines)
