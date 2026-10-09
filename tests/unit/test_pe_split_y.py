"""路线 Y n=400 名单针：满额配额、与 pilot 隔离、禁静默改小、缺额 fail-closed。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_construct import STRATA
from freshlatch.eval.patch_events_formal_y import (
    _FORMAL_N,
    _LAYER_N,
    load_pe_v2_formal_n400,
    load_route_y_split,
    n400_quota_targets,
    route_y_n400_ready,
    route_y_split_path,
)

_ROOT = Path(__file__).resolve().parents[2]
_ROUTE_Y = _ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2-route-y.json"
_SPLIT = _ROOT / "docs" / "evidence" / "patch-events" / "SPLIT-pe-v2.json"
_PREREG_Y = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG-Y.md"
_DOCKET = _ROOT / "data" / "pe_v2_docket.json"


def test_route_y_pin_file_exists_and_targets_prereg_y_quotas():
    """Acceptance: 名单针落盘；四层各 100 且 50/50；合计目标 400。"""
    assert route_y_split_path() == _ROUTE_Y
    assert _ROUTE_Y.is_file()
    payload = load_route_y_split()
    assert payload["quotas_target"]["total"] == _FORMAL_N
    quotas = n400_quota_targets()
    for name in STRATA:
        block = payload["quotas_target"]["n400"][name]
        correct, bad = quotas[name]
        assert block["total"] == _LAYER_N
        assert (block["correct"], block["bad"]) == (correct, bad) == (50, 50)
        stratum = payload["by_stratum"]["n400"][name]
        assert stratum["target"] == _LAYER_N
        assert stratum["correct_target"] == 50
        assert stratum["bad_target"] == 50


def test_route_y_full_n400_ready_not_shortfall():
    """Acceptance: CORPUS-02 满额后离开不可激活；gaps=0；层内 50/50。"""
    payload = load_route_y_split()
    assert payload["status"] != "不可激活"
    assert payload["activation"]["ready"] is True
    assert payload["counts"]["n400"] == _FORMAL_N
    assert payload["counts"]["target_n400"] == _FORMAL_N
    assert payload["gaps"]["n400"] == 0
    assert len(payload["n400"]) == _FORMAL_N
    assert len({row["claim_id"] for row in payload["n400"]}) == _FORMAL_N
    assert route_y_n400_ready() is True
    # 目标配额仍钉在 400，禁止静默改小
    assert payload["quotas_target"]["total"] == 400
    for name in STRATA:
        gap_block = payload["gaps"]["by_stratum"][name]
        assert gap_block["gap"] == 0
        assert gap_block["target"] == _LAYER_N
        stratum = payload["by_stratum"]["n400"][name]
        assert stratum["gap"] == 0
        assert stratum["built"] == _LAYER_N
        assert (stratum["correct"], stratum["bad"]) == (50, 50)


def test_route_y_conformal_leftover_or_unmade():
    """共形：leftover≥5/层或 conformal_reserve 标明未做；不得挖主配额。"""
    payload = load_route_y_split()
    assert payload["quotas_target"]["total"] == 400
    leftover = payload.get("leftover_non_pilot") or {}
    reserve = str(payload.get("conformal_reserve") or "")
    if leftover:
        for name in STRATA:
            assert int(leftover[name]) >= 5
    else:
        assert "未做" in reserve


def test_n400_loader_returns_exactly_400():
    """Acceptance: loader 成功返回恰好 400 条互异记录。"""
    rows = load_pe_v2_formal_n400()
    assert len(rows) == _FORMAL_N
    assert len({row["claim_id"] for row in rows}) == _FORMAL_N
    for name in STRATA:
        got_c = sum(
            1
            for row in rows
            if row["edit_type"] == name and row["construction_gold"] == "正确"
        )
        got_b = sum(
            1
            for row in rows
            if row["edit_type"] == name and row["construction_gold"] == "坏"
        )
        assert (got_c, got_b) == (50, 50)


def test_n400_ids_disjoint_from_pilot():
    """Acceptance: formal 与 pilot 无交（针内 n400 ∪ 镜像 pilot）。"""
    payload = load_route_y_split()
    base = json.loads(_SPLIT.read_text(encoding="utf-8"))
    pilot_ids = {str(row["claim_id"]) for row in base["pilot"]}
    assert {str(row["claim_id"]) for row in payload["pilot"]} == pilot_ids
    n400_ids = {str(row["claim_id"]) for row in payload["n400"]}
    assert n400_ids.isdisjoint(pilot_ids)
    rows = load_pe_v2_formal_n400()
    assert {str(row["claim_id"]) for row in rows}.isdisjoint(pilot_ids)


def test_prereg_y_quota_table_numbers_unchanged():
    """Do-not-touch: 不改 PREREG-Y 配额表数字；文首仍未激活。"""
    text = _PREREG_Y.read_text(encoding="utf-8")
    assert (
        "| n=400（路线 Y 满样本门槛） | 100（50/50） | 100（50/50） "
        "| 100（50/50） | 100（50/50） | 400 |"
    ) in text
    assert "冲乙正式主跑已激活" not in text.splitlines()[0]


def test_source_pin_matches_split_pe_v2_and_docket_blob():
    """Provenance: route-y 登记 SPLIT-pe-v2 与扩容后 docket sha256。"""
    payload = load_route_y_split()
    digest = hashlib.sha256(_SPLIT.read_bytes()).hexdigest()
    assert payload["source"]["split_pe_v2_sha256"] == digest
    assert payload["source"]["split_pe_v2"] == "docs/evidence/patch-events/SPLIT-pe-v2.json"
    docket_digest = hashlib.sha256(_DOCKET.read_bytes()).hexdigest()
    assert payload["source"]["docket_sha256"] == docket_digest
    assert payload["source"]["docket_claims"] == 670


def test_loader_refuses_artificial_shortfall_pin(tmp_path, monkeypatch):
    """缺额 fail-closed：人为缺额针仍 RuntimeError(不可激活…)，不得返回不足 400。"""
    shortfall = {
        "status": "不可激活",
        "activation": {"ready": False},
        "gaps": {"n400": 400},
        "counts": {"n400": 0, "target_n400": 400},
        "n400": [],
        "pilot": [],
        "quotas_target": {"total": 400, "n400": {}},
    }
    path = tmp_path / "SPLIT-pe-v2-route-y.json"
    path.write_text(json.dumps(shortfall, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_y.route_y_split_path",
        lambda root=None: path,
    )
    assert route_y_n400_ready(tmp_path) is False
    with pytest.raises(RuntimeError, match="不可激活.*语料缺额") as exc:
        load_pe_v2_formal_n400(tmp_path)
    msg = str(exc.value)
    assert "不得静默改小" in msg
    assert "400" in msg


def test_loader_never_returns_undersized_list(tmp_path, monkeypatch):
    """禁止静默改小：即便针里塞了不足 400 条，loader 也不得返回它们。"""
    partial = {
        "status": "ok",
        "activation": {"ready": True},
        "gaps": {"n400": 0},
        "n400": [
            {"claim_id": f"x{i:03d}", "construction_gold": "坏", "edit_type": "数值"}
            for i in range(10)
        ],
        "pilot": [],
        "quotas_target": {"total": 400, "n400": {}},
    }
    path = tmp_path / "SPLIT-pe-v2-route-y.json"
    path.write_text(json.dumps(partial, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_y.route_y_split_path",
        lambda root=None: path,
    )
    with pytest.raises(RuntimeError, match="不可激活|语料缺额"):
        load_pe_v2_formal_n400(tmp_path)
