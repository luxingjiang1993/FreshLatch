"""#172/#197 patch_events JSONL:写后读、before/after、产品写 T、发前 UX 无 C/T 开关。

零 LLM、零网络;只测 data/patch_events 账本缝与发前表面约束。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from freshlatch import patch_events as pe

REQUIRED = (
    "claim_id",
    "before_disp",
    "patch_span",
    "t1_ids",
    "human_confirm",
    "reverify",
    "minutes",
    "arm",
    "ts",
    "actor",
)


def _sample_event(**overrides):
    base = {
        "claim_id": "c-mck-share-01",
        "before_disp": "需补丁",
        "patch_span": "定价段·份额主张改写",
        "t1_ids": ["mck-soai-2025-11#p3@T1"],
        "human_confirm": True,
        "reverify": True,
        "minutes": 12.5,
        "arm": "T",
        "ts": "2026-09-28T17:00:00+00:00",
        "actor": "script",
    }
    base.update(overrides)
    return base


def test_append_then_read_roundtrip_fields_complete(tmp_path: Path):
    """Given 一次合法 append,When 读 JSONL,Then 字段齐全且值一致。"""
    events_dir = tmp_path / "patch_events"
    written = pe.append_event(_sample_event(), events_dir=events_dir)
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    row = rows[0]
    for key in REQUIRED:
        assert key in row
        assert row[key] == written[key]
    assert row["arm"] == "T"
    assert row["t1_ids"] == ["mck-soai-2025-11#p3@T1"]


def test_append_with_before_after_text_roundtrip(tmp_path: Path):
    """Given 含 before_text/after_text 的合法 append,When 读账本,Then 两字段与写入一致且 arm 可为 T。"""
    events_dir = tmp_path / "patch_events"
    written = pe.append_event(
        _sample_event(
            before_text="旧份额主张句",
            after_text="经 T1 核后的份额主张句",
            arm="T",
        ),
        events_dir=events_dir,
    )
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    row = rows[0]
    assert row["before_text"] == "旧份额主张句"
    assert row["after_text"] == "经 T1 核后的份额主张句"
    assert row["before_text"] == written["before_text"]
    assert row["after_text"] == written["after_text"]
    assert row["arm"] == "T"


def test_read_legacy_row_without_before_after_ok(tmp_path: Path):
    """Given 仅含 V1 旧字段的历史行,When 读账本,Then 不抛错。"""
    events_dir = tmp_path / "patch_events"
    events_dir.mkdir(parents=True)
    legacy = {
        "claim_id": "mck-1",
        "before_disp": "勿发",
        "patch_span": "人审discard",
        "t1_ids": [],
        "human_confirm": True,
        "reverify": False,
        "minutes": 0.0,
        "arm": "C",
        "ts": "2026-09-28T16:00:00+00:00",
        "actor": "human",
    }
    path = events_dir / pe.DEFAULT_FILENAME
    path.write_text(json.dumps(legacy, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    assert rows[0]["claim_id"] == "mck-1"
    assert "before_text" not in rows[0]
    assert "after_text" not in rows[0]


def test_append_rejects_partial_before_after(tmp_path: Path):
    """before_text 与 after_text 须成对出现。"""
    with pytest.raises(pe.PatchEventError, match="成对"):
        pe.append_event(_sample_event(before_text="仅有 before"), events_dir=tmp_path)


def test_append_product_confirm_forces_arm_t(tmp_path: Path):
    """产品确认路径恒写 arm=T,且正式行含 before/after。"""
    events_dir = tmp_path / "patch_events"
    assert pe.PRODUCT_ARM == "T"
    written = pe.append_product_confirm(
        claim_id="c-mck-3",
        before_disp="需补丁",
        patch_span="mck-3 主张改写",
        t1_ids=["mck-soai-2025-11#p3@T1"],
        minutes=5.0,
        before_text="旧正文",
        after_text="新正文",
        ts="2026-09-29T08:00:00+00:00",
        events_dir=events_dir,
    )
    assert written["arm"] == "T"
    assert written["before_text"] == "旧正文"
    assert written["after_text"] == "新正文"
    assert written["human_confirm"] is True
    assert written["reverify"] is True
    rows = pe.read_events(events_dir=events_dir)
    assert rows[0]["arm"] == pe.PRODUCT_ARM
    assert rows[0]["before_text"] == "旧正文"
    assert rows[0]["after_text"] == "新正文"


def test_human_patch_uses_same_schema(tmp_path: Path):
    """人手补丁经同一 schema 写入(arm 由后台/脚本显式传入,非 UX 开关)。"""
    events_dir = tmp_path / "patch_events"
    pe.append_human_patch(
        claim_id="c-human-01",
        before_disp="勿发",
        patch_span="人手工改写结论句",
        t1_ids=[],
        human_confirm=True,
        reverify=False,
        minutes=8,
        arm="C",
        actor="human",
        ts="2026-09-28T18:00:00+00:00",
        events_dir=events_dir,
    )
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    for key in REQUIRED:
        assert key in rows[0]
    assert rows[0]["arm"] == "C"
    assert rows[0]["actor"] == "human"
    assert rows[0]["t1_ids"] == []
    assert "before_text" not in rows[0]


def test_append_rejects_invalid_arm(tmp_path: Path):
    with pytest.raises(pe.PatchEventError):
        pe.append_event(_sample_event(arm="X"), events_dir=tmp_path)


def test_append_rejects_missing_required(tmp_path: Path):
    bad = _sample_event()
    del bad["claim_id"]
    with pytest.raises(pe.PatchEventError):
        pe.append_event(bad, events_dir=tmp_path)


def test_default_repo_dir_is_data_patch_events():
    """约定目录落在仓内 data/patch_events/(相对模块解析)。"""
    assert pe.default_events_dir().name == "patch_events"
    assert pe.default_events_dir().parent.name == "data"


def test_record_human_review_events_writes_ok_only(tmp_path: Path):
    """人审结果批量记账:仅 ok 行落盘,before_disp 保留人审前快照。"""
    events_dir = tmp_path / "patch_events"
    written = pe.record_human_review_events(
        [
            {"claim_id": "mck-1", "ok": True, "action": "discard"},
            {"claim_id": "mck-x", "ok": False, "action": "discard"},
            {"claim_id": "", "ok": True, "action": "discard"},
        ],
        before_disp="勿发",
        t1_ids=["doc-a#abc@T1"],
        arm="C",
        events_dir=events_dir,
    )
    assert len(written) == 1
    rows = pe.read_events(events_dir=events_dir)
    assert len(rows) == 1
    assert rows[0]["claim_id"] == "mck-1"
    assert rows[0]["before_disp"] == "勿发"
    assert rows[0]["patch_span"] == "人审discard"
    assert rows[0]["t1_ids"] == ["doc-a#abc@T1"]
    assert rows[0]["human_confirm"] is True
    assert rows[0]["arm"] == "C"
    assert "before_text" not in rows[0]


def test_prepublish_surface_has_no_ct_arm_switch():
    """发前相关 UI/API 不得出现 arm=C|T 实验开关控件或路由。"""
    repo = Path(__file__).resolve().parents[2]
    ui_app = (repo / "src" / "freshlatch" / "ui" / "app.py").read_text(encoding="utf-8")
    pe_mod = (repo / "src" / "freshlatch" / "patch_events.py").read_text(encoding="utf-8")

    # 禁止发前表面出现 C/T 切换控件文案/路由
    banned_ui = [
        r"arm\s*=\s*[\"']C[\"']\s*\|\s*[\"']T[\"']",
        r"C\s*vs\s*T",
        r"实验臂",
        r"arm-switch",
        r"arm_switch",
        r"/api/.*arm",
        r"select[^>]*(C|T).*臂",
    ]
    for pat in banned_ui:
        assert re.search(pat, ui_app, flags=re.I) is None, f"发前 UI 命中禁面: {pat}"

    # 模块允许 arm 枚举常量,但不得暴露「给 UX 切换」的 API 名
    assert "ux_arm_switch" not in pe_mod
    assert "set_arm_from_ui" not in pe_mod
