"""PE-01 实验记录：字段往返、非法值拒绝、产品账本仍只接受 C/T。

零 LLM、零网络、不读密钥。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch import patch_events as pe
from freshlatch.eval import patch_events_exp as exp


def _sample(**overrides):
    base = {
        "claim_id": "c-001",
        "edit_type": "数值",
        "arm": "T",
        "ablation": "",
        "construction_gold": "正确",
        "before_text": "修改前",
        "after_text": "修改后",
        "evidence_id": "doc#c1@T1",
        "evidence_text": "证据原文",
    }
    base.update(overrides)
    return base


def test_roundtrip_edit_types_arms_and_ablations(tmp_path: Path):
    """四类修改、四组、四项消融写入后读回，字段与写入一致。"""
    events_dir = tmp_path / "exp"
    written = []
    for edit_type in ("数值", "日期", "条款替换", "删除"):
        written.append(
            exp.append_experiment_record(
                _sample(claim_id=f"edit-{edit_type}", edit_type=edit_type),
                events_dir=events_dir,
            )
        )
    for arm in ("C", "T", "B1", "B2"):
        written.append(
            exp.append_experiment_record(
                _sample(
                    claim_id=f"arm-{arm}",
                    arm=arm,
                    ablation="",
                    construction_gold="坏",
                ),
                events_dir=events_dir,
            )
        )
    for ablation in (
        "no_chunk_bind",
        "no_auto_verify",
        "soft_warning",
        "retrieval_bm25",
    ):
        written.append(
            exp.append_experiment_record(
                _sample(
                    claim_id=f"ab-{ablation}",
                    arm="T",
                    ablation=ablation,
                    construction_gold="坏",
                    evidence_id="",
                ),
                events_dir=events_dir,
            )
        )
    filled = exp.append_experiment_record(
        _sample(
            claim_id="ran",
            decision="release",
            reject_reason="",
            score=0.5,
            latency_ms=12,
            cost=0,
            reverify_ok=True,
        ),
        events_dir=events_dir,
    )
    written.append(filled)
    rows = exp.read_experiment_records(events_dir=events_dir)
    assert rows == written
    assert {row["edit_type"] for row in rows} >= {"数值", "日期", "条款替换", "删除"}
    assert {row["arm"] for row in rows} >= {"C", "T", "B1", "B2"}
    assert {row["ablation"] for row in rows} >= {
        "no_chunk_bind",
        "no_auto_verify",
        "soft_warning",
        "retrieval_bm25",
    }
    empty_score = next(row for row in rows if row["claim_id"] == "edit-数值")
    assert "score" not in empty_score
    assert "decision" not in empty_score
    assert rows[-1]["score"] == 0.5
    assert rows[-1]["decision"] == "release"
    assert rows[-1]["cost"] == 0
    assert rows[-1]["reverify_ok"] is True
    blank_evidence = next(row for row in rows if row["claim_id"] == "ab-no_chunk_bind")
    assert blank_evidence["evidence_id"] == ""


def test_empty_score_roundtrip(tmp_path: Path):
    written = exp.append_experiment_record(
        _sample(score=None),
        events_dir=tmp_path,
    )
    rows = exp.read_experiment_records(events_dir=tmp_path)
    assert rows == [written]
    assert rows[0]["score"] is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"edit_type": "金额"},
        {"arm": "X"},
        {"arm": "b1"},
        {"construction_gold": "对"},
        {"ablation": "bm25"},
        {"decision": "hold"},
        {"score": True},
        {"score": "高"},
        {"latency_ms": True},
        {"reverify_ok": "yes"},
    ],
)
def test_rejects_illegal_fields(tmp_path: Path, overrides):
    with pytest.raises(exp.ExperimentRecordError):
        exp.append_experiment_record(_sample(**overrides), events_dir=tmp_path)


@pytest.mark.parametrize("arm", ["C", "B1", "B2"])
def test_ablation_requires_arm_t(tmp_path: Path, arm: str):
    with pytest.raises(exp.ExperimentRecordError):
        exp.append_experiment_record(
            _sample(arm=arm, ablation="no_chunk_bind"),
            events_dir=tmp_path,
        )


def test_product_confirm_stays_arm_t_and_rejects_b1_b2(tmp_path: Path):
    assert pe.VALID_ARMS == frozenset({"C", "T"})
    assert pe.PRODUCT_ARM == "T"
    events_dir = tmp_path / "product"
    written = pe.append_product_confirm(
        claim_id="c-product",
        before_disp="需补丁",
        patch_span="主张改写",
        t1_ids=["doc#c1@T1"],
        minutes=1.0,
        before_text="旧",
        after_text="新",
        ts="2026-10-07T00:00:00+00:00",
        events_dir=events_dir,
    )
    assert written["arm"] == "T"
    assert pe.read_events(events_dir=events_dir)[0]["arm"] == "T"
    for arm in ("B1", "B2"):
        with pytest.raises(pe.PatchEventError):
            pe.append_event(
                {
                    "claim_id": "c-product",
                    "before_disp": "需补丁",
                    "patch_span": "主张改写",
                    "t1_ids": ["doc#c1@T1"],
                    "human_confirm": True,
                    "reverify": True,
                    "minutes": 1.0,
                    "arm": arm,
                    "ts": "2026-10-07T00:00:00+00:00",
                    "actor": "script",
                },
                events_dir=events_dir,
            )


def test_product_legacy_row_without_experiment_fields_still_reads(tmp_path: Path):
    events_dir = tmp_path / "product"
    events_dir.mkdir()
    legacy = {
        "claim_id": "old-1",
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
    (events_dir / pe.DEFAULT_FILENAME).write_text(
        json.dumps(legacy, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    rows = pe.read_events(events_dir=events_dir)
    assert rows == [legacy]
    assert "construction_gold" not in rows[0]
    assert "ablation" not in rows[0]


def test_experiment_ledger_is_not_the_product_ledger():
    assert exp.DEFAULT_FILENAME != pe.DEFAULT_FILENAME
    assert exp.default_experiment_dir().name != pe.default_events_dir().name


def test_module_does_not_read_or_store_secrets():
    text = Path(exp.__file__).read_text(encoding="utf-8")
    for token in (
        "DASHSCOPE_API_KEY",
        "DEEPSEEK_API_KEY",
        "MOONSHOT_API_KEY",
        "getenv",
        "environ",
        "真人盲审",
    ):
        assert token not in text


def test_locked_assignments_unchanged():
    repo = Path(__file__).resolve().parents[2]
    base = (repo / "src" / "freshlatch" / "store" / "base.py").read_text(encoding="utf-8")
    llm = (repo / "src" / "freshlatch" / "llm.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
    assert 'DEFAULT_MODEL = "qwen-flash"' in llm
