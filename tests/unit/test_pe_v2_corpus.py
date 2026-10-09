"""pe_v2 公开语料能填满预注册配额。不调用评委，不读密钥。"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from freshlatch.eval.patch_events_construct import (
    QUOTAS,
    STRATA,
    ConstructError,
    _build,
    _sign,
    construct_samples,
    load_claims,
)

_ROOT = Path(__file__).resolve().parents[2]
_DOCKET = _ROOT / "data" / "pe_v2_docket.json"
_CORPUS = _ROOT / "data" / "corpus" / "pe_v2"
_MANIFEST = _ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2.json"

# 路线 Y / ADR-0038 续扩下限（Acceptance：可满 n=400 + 共形预留规划）
_MIN_PER_STRATUM = {"数值": 150, "日期": 150, "条款替换": 150, "删除": 220}
_MIN_TOTAL = sum(_MIN_PER_STRATUM.values())


def _lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_pe_v2_decision_is_confirmed_after_amendment_3():
    log = _lf(_ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG.md").decode("utf-8")
    draft = _ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG-pe-v2-DRAFT.md"
    assert not draft.exists()
    amendment = log.index("## 跑数据前偏离 · Amendment 3")
    missing = log.index("## 跑数据前偏离 · 非拒绝类错误记缺失")
    confirmed = log.index("## 跑数据前偏离 · 扩充公开语料")
    assert amendment < missing < confirmed
    section = log[confirmed:]
    assert "决定人：用户（Oriental Ronin，2026-10-08 13:32 UTC+8）" in section
    assert "转录人：Ronin 代理人" in section
    assert "此时尚无 pilot，也尚无正式评委数据" in section
    assert "不改 `PREREG.md`" in section
    assert "日期与条款替换大多取自同一现行文本的两段，而不是新旧版本。" in section
    assert "删除层存在算子伪影：修饰词表含「约」，会从「约定」里删字。" in section


def test_pe_v2_route_y_expand_decision_log_pointer():
    log = _lf(_ROOT / "docs" / "evidence" / "patch-events" / "DECISION-LOG.md").decode("utf-8")
    marker = "## 跑数据前偏离 · pe_v2 再扩充（路线 Y / ADR-0038）"
    assert marker in log
    section = log[log.index(marker) :]
    assert "不改" in section and "PREREG-Y" in section
    assert "n=400" in section
    assert "不改写" in section and "SPLIT-pe-v2.json" in section
    assert "PE-Y-CORPUS-02" in section or "#501" in section
    assert "不改比较、成立尺" in section or "不改**比较、成立尺" in section
    prereg = _lf(_ROOT / "docs" / "evidence" / "patch-events" / "PREREG-Y.md").decode("utf-8")
    # PE-Y-05 激活后文首为已激活；配额表仍不得静默改小。
    assert "冲乙正式主跑已激活" in prereg
    assert "| n=400（路线 Y 满样本门槛） | 100（50/50） | 100（50/50） | 100（50/50） | 100（50/50） | 400 |" in prereg


def test_pe_v2_fills_quotas_and_keeps_margin():
    result = construct_samples(_DOCKET, _CORPUS)
    manifest = json.loads(_lf(_MANIFEST).decode("utf-8"))
    assert len(result.pilot) == 15
    assert len(result.n30) == 30
    assert len(result.n100) == 100
    assert not any(item.claim_id == "" for item in result.shortfalls)
    for tier, rows in (
        ("pilot", result.pilot),
        ("n30", result.n30),
        ("n100", result.n100),
    ):
        for name in STRATA:
            correct, bad = QUOTAS[tier][name]
            got_c = sum(
                1
                for row in rows
                if row.record["edit_type"] == name and row.record["construction_gold"] == "正确"
            )
            got_b = sum(
                1
                for row in rows
                if row.record["edit_type"] == name and row.record["construction_gold"] == "坏"
            )
            assert (got_c, got_b) == (correct, bad)
            assert manifest["by_stratum"][tier][name]["gap"] == 0
    assert [row.record["claim_id"] for row in result.pilot] == [
        item["claim_id"] for item in manifest["pilot"]
    ]
    assert [row.record["claim_id"] for row in result.n100] == [
        item["claim_id"] for item in manifest["n100"]
    ]


def test_pe_v2_claims_are_verbatim_and_hashed():
    docket = json.loads(_lf(_DOCKET).decode("utf-8"))
    provenance = json.loads(_lf(_CORPUS / "PROVENANCE.json").decode("utf-8"))
    by_id = {row["claim_id"]: row for row in provenance["claims"]}
    counts = Counter(claim["dimension"] for claim in docket["claims"])
    assert len(docket["claims"]) == len(by_id) >= _MIN_TOTAL
    for name, minimum in _MIN_PER_STRATUM.items():
        assert counts[name] >= minimum, (name, counts[name], minimum)
    assert provenance.get("dataset_snapshot") == "2026-08-26"
    assert provenance.get("dataset_revision")
    assert provenance.get("target_per_stratum") == 150
    for claim in docket["claims"]:
        claim_id = claim["claim_id"]
        statement = claim["statement"]
        t0 = _lf(_CORPUS / "t0" / f"{claim_id}.md").decode("utf-8")
        assert statement in t0
        row = by_id[claim_id]
        assert row["fetch_time"]
        assert row["license"]
        assert row["t0_source"]["source_url"]
        assert hashlib.sha256(_lf(_CORPUS / "t0" / f"{claim_id}.md")).hexdigest() == row["t0_sha256"]
        assert hashlib.sha256(_lf(_CORPUS / "t1" / f"{claim_id}.md")).hexdigest() == row["t1_sha256"]
        assert row["t0_source"]["offset"] >= 0
    inventory = json.loads(_lf(_MANIFEST).decode("utf-8"))["inventory"]
    for name, block in inventory.items():
        assert block["leftover"] >= 5
        assert block["claims"] * 10 >= block["with_conformal"] * 13


def _caps_of(view, stratum: str) -> set[object]:
    caps: set[object] = set()
    try:
        _build(view, stratum, "正确", None, None)
        caps.add("C")
    except ConstructError:
        return caps
    for op in range(4):
        for sign in ("plus", "minus"):
            try:
                _build(view, stratum, "坏", op, sign)
                caps.add(op)
                break
            except ConstructError:
                continue
    return caps


def _smart_fill(
    stratum: str,
    n_correct: int,
    n_bad: int,
    pool: list,
) -> tuple[bool, list[str], int]:
    """按余数规则 50/50 配槽；稀缺坏算子先预留（删除层）。不改构造算子语义。"""
    annotated = [(view, _caps_of(view, stratum)) for view in pool]
    annotated = [(view, caps) for view, caps in annotated if "C" in caps]
    labels: list[tuple[str, int | None]] = []
    bad = correct = 0
    while bad < n_bad or correct < n_correct:
        if bad < n_bad and (bad == correct or correct >= n_correct):
            labels.append(("坏", bad % 4))
            bad += 1
        else:
            labels.append(("正确", None))
            correct += 1
    need_ops = Counter(op for gold, op in labels if gold == "坏" and op in (0, 1, 3))
    avail = {
        op: sum(1 for _, caps in annotated if op in caps) for op in need_ops
    }
    order = sorted(need_ops, key=lambda op: avail[op] - need_ops[op])
    taken: set[int] = set()
    reserved: dict[int, list[int]] = {0: [], 1: [], 3: []}
    for op in order:
        need = need_ops[op]
        ranked = sorted(
            (
                index
                for index, (_, caps) in enumerate(annotated)
                if op in caps and index not in taken
            ),
            key=lambda index: sum(
                1 for other in (0, 1, 3) if other != op and other in annotated[index][1]
            ),
        )
        for index in ranked[:need]:
            reserved[op].append(index)
            taken.add(index)
    remaining = set(range(len(annotated))) - taken
    used: list[str] = []
    for gold, operator in labels:
        best: int | None = None
        if gold == "坏" and operator in reserved and reserved[operator]:
            best = reserved[operator].pop(0)
        elif gold == "正确":
            for index in list(remaining):
                caps = annotated[index][1]
                if "C" in caps and not any(op in caps for op in (0, 1, 3)):
                    best = index
                    break
            if best is None:
                for index in list(remaining):
                    if "C" in annotated[index][1]:
                        best = index
                        break
        else:
            for index in list(remaining):
                if operator in annotated[index][1]:
                    best = index
                    break
        if best is None:
            return False, used, len(remaining)
        used.append(annotated[best][0].claim_id)
        remaining.discard(best)
    return True, used, len(remaining)


def test_pe_v2_route_y_inventory_supports_n400_with_conformal_margin():
    """四层可供 route-y 正式 100/层且 50/50；满规划后 leftover≥5。不重针 route-y。"""
    docket = json.loads(_lf(_DOCKET).decode("utf-8"))
    manifest = json.loads(_lf(_MANIFEST).decode("utf-8"))
    pilot_ids = {item["claim_id"] for item in manifest["pilot"]}
    dim_of = {claim["claim_id"]: claim["dimension"] for claim in docket["claims"]}
    views = load_claims(_DOCKET, _CORPUS)
    by_dim: dict[str, list] = defaultdict(list)
    for view in views:
        by_dim[dim_of[view.claim_id]].append(view)

    for name in STRATA:
        pool = [view for view in by_dim[name] if view.claim_id not in pilot_ids]
        ok, used, leftover = _smart_fill(name, 50, 50, pool)
        assert ok, f"{name} 无法配齐 route-y 50/50"
        assert len(used) == 100
        assert leftover >= 5, f"{name} leftover={leftover}"

    for name in STRATA:
        pilot_c, pilot_b = QUOTAS["pilot"][name]
        ok_pilot, pilot_used, _ = _smart_fill(name, pilot_c, pilot_b, by_dim[name])
        assert ok_pilot
        rem = [view for view in by_dim[name] if view.claim_id not in set(pilot_used)]
        ok_formal, formal_used, leftover = _smart_fill(name, 50, 50, rem)
        assert ok_formal, f"{name} pilot 后无法配齐 100"
        assert len(formal_used) == 100
        assert leftover >= 5
