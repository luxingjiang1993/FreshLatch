"""SLO-06：C1 作废率 / C2 override rate 只读周报聚合。

验收层=观测脚手架；不锁 Override Rate 通过线；不新增 HumanLatch 动词。
禁止升格：override⇒模型变好；C1/C2 数字⇒验收绿灯。
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.gates.human_latch import VALID_ACTIONS
from freshlatch.store.sqlite_store import SQLiteStore

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "slo_c1_c2_latch_rates.py"


def _load_agg():
    spec = importlib.util.spec_from_file_location("slo_c1_c2_latch_rates", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


agg = _load_agg()


@pytest.fixture()
def seeded_db(tmp_path: Path) -> Path:
    """含 discard/renew 与 override 0/1 的 latch_log 夹具。"""
    db = tmp_path / "slo06.db"
    store = SQLiteStore(db)
    # week A: 2026-09-22 .. 2026-09-28
    store.add_invalidation("c-void-fresh", "2026-09-22T10:00:00", reason="作废绿灯")
    store.log_latch(
        "2026-09-22T10:00:00",
        "c-void-fresh",
        "discard",
        machine_status_before="fresh",
        override=True,
        run_id="run-w1",
    )
    store.add_invalidation("c-void-stale", "2026-09-23T11:00:00", reason="作废已红")
    store.log_latch(
        "2026-09-23T11:00:00",
        "c-void-stale",
        "discard",
        machine_status_before="stale",
        override=False,
        run_id="run-w1",
    )
    store.log_latch(
        "2026-09-24T12:00:00",
        "c-renew-stale",
        "renew",
        evidence_id="doc#p1@T1",
        machine_status_before="stale",
        override=True,
        run_id="run-w1",
    )
    store.log_latch(
        "2026-09-25T13:00:00",
        "c-renew-fresh",
        "renew",
        evidence_id="doc#p2@T1",
        machine_status_before="fresh",
        override=False,
        run_id="run-w1",
    )
    # rerun 不得进 C1/C2 分母
    store.log_latch("2026-09-26T14:00:00", "c-void-fresh", "rerun", actor="human")
    # week B: 落在窗外
    store.log_latch(
        "2026-10-05T09:00:00",
        "c-later",
        "discard",
        machine_status_before="fresh",
        override=True,
        run_id="run-w2",
    )
    store.add_invalidation("c-later", "2026-10-05T09:00:00", reason="窗外")
    return db


def test_actions_closed_set_unchanged():
    """不新增 override action（Do-not-touch）。"""
    assert VALID_ACTIONS == ("discard", "renew")
    assert "override" not in VALID_ACTIONS


def test_c1_c2_rates_with_denominators(seeded_db: Path):
    """Given discard/renew+override 夹具, When 聚合, Then 作废率与 override rate 含分母。"""
    report = agg.build_report(seeded_db, week_start="2026-09-22")
    c1 = report.C1
    c2 = report.C2

    # 窗内人审 claim: void-fresh, void-stale, renew-stale, renew-fresh → 4
    # discard: 2
    assert c1["discard_claim_n"] == 2
    assert c1["denominator_n"] == 4
    assert c1["rate"] == pytest.approx(0.5)
    assert c1["discard_of_fresh_n"] == 1
    assert c1["invalidation_list_n"] == 3  # 含窗外 c-later

    # override 标签行: 4 条人审；true=2（void-fresh, renew-stale）
    assert c2["override_true_n"] == 2
    assert c2["denominator_n"] == 4
    assert c2["rate"] == pytest.approx(0.5)
    assert c2["not_model_improvement"] is True
    assert c2["not_acceptance_green"] is True


def test_disclaimer_in_text_and_json(seeded_db: Path):
    """Given 聚合输出头, When 阅读, Then 含 override 不作模型变好/不作验收绿灯。"""
    from dataclasses import asdict

    report = agg.build_report(seeded_db)
    text = agg.format_text(report)
    assert "override 不作模型变好" in text
    assert "不作验收绿灯" in text
    assert "ADR-0023" in report.disclaimer
    blob = json.dumps(asdict(report), ensure_ascii=False)
    assert "不作模型变好" in blob
    assert report.C2["not_acceptance_green"] is True


def test_ops_weekly_fields_fillable(seeded_db: Path):
    """Given 输出, When 对照 ops 周报, Then C1/C2 可填。"""
    report = agg.build_report(seeded_db, week_start="2026-09-22")
    fields = report.ops_fields
    assert "C1_作废率" in fields
    assert "C2_override_rate" in fields
    assert fields["C1_分子_discard_claim_n"] == 2
    assert fields["C1_分母_reviewed_claim_n"] == 4
    assert fields["C2_分子_override_true_n"] == 2
    assert fields["C2_分母_override_labeled_n"] == 4
    text = agg.format_text(report)
    assert "C1 作废率" in text
    assert "C2 override rate" in text
    assert "docs/ops/生产补丁放行SLO.md" in fields["可填周报"]


def test_cli_json_smoke(seeded_db: Path, tmp_path: Path):
    out = tmp_path / "c1c2.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--db",
            str(seeded_db),
            "--week-start",
            "2026-09-22",
            "--json",
            "-o",
            str(out),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["C1"]["denominator_n"] == 4
    assert data["C2"]["denominator_n"] == 4
    assert "不作模型变好" in data["disclaimer"]


def test_empty_denominator_is_null(tmp_path: Path):
    db = tmp_path / "empty.db"
    SQLiteStore(db)  # 建空表
    report = agg.build_report(db)
    assert report.C1["denominator_n"] == 0
    assert report.C1["rate"] is None
    assert report.C2["denominator_n"] == 0
    assert report.C2["rate"] is None
