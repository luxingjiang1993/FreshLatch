"""PE-07 用户抽检与分歧裁决。夹具标签，零 API，不读密钥。"""

from __future__ import annotations

import copy
import inspect
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_construct import STRATA
from freshlatch.eval.patch_events_spotcheck import (
    ALREADY,
    IDENTITY,
    SPOTCHECK_ROLE,
    SpotcheckError,
    export_spotcheck,
    select_spotcheck,
)

_GOLD = ("正确", "坏")
_JUDGES = ("qwen", "deepseek", "kimi")


def _records(per_gold: int) -> list[dict]:
    rows = []
    for edit_type in STRATA:
        for gold in _GOLD:
            code = "c" if gold == "正确" else "b"
            for index in range(per_gold):
                claim_id = f"{edit_type}-{code}-{index:02d}"
                rows.append(
                    {
                        "claim_id": claim_id,
                        "edit_type": edit_type,
                        "arm": "ARM_SENTINEL",
                        "ablation": "ABL_SENTINEL",
                        "construction_gold": gold,
                        "before_text": f"前-{claim_id}",
                        "after_text": f"后-{claim_id}",
                        "evidence_id": f"doc-{claim_id}#p1@T1",
                        "evidence_text": f"证据-{claim_id}",
                        "qwen": "LEAK_QWEN",
                        "deepseek": "LEAK_DEEPSEEK",
                        "kimi": "LEAK_KIMI",
                    }
                )
    return rows


def _label_row(
    claim_id: str,
    *,
    overrides: dict | None = None,
    absent: dict | None = None,
) -> dict:
    overrides = overrides or {}
    absent = absent or {}
    row: dict = {"claim_id": claim_id}
    for judge in _JUDGES:
        cell = {"A": "是", "B": "否"}
        cell.update(overrides.get(judge, {}))
        for question in absent.get(judge, ()):
            cell[question] = None
        row[judge] = cell
    return row


def _labels(records, **kwargs) -> list[dict]:
    return [_label_row(row["claim_id"], **kwargs) for row in records]


def _counts(rows: list[dict]) -> dict[tuple[str, str], int]:
    tally: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["edit_type"], row["construction_gold"])
        tally[key] = tally.get(key, 0) + 1
    return tally


def test_select_signature_rejects_judge_labels():
    names = set(inspect.signature(select_spotcheck).parameters)
    assert names == {"records", "n", "rng"}
    with pytest.raises(TypeError):
        select_spotcheck(_records(1), n=30, labels=[])


def test_n30_and_n100_quotas_follow_stratum_order():
    records = _records(4)
    small = select_spotcheck(records, n=30)
    assert len(small) == 8
    tally = _counts(small)
    cursor = 0
    for stratum in STRATA:
        assert tally[(stratum, "正确")] == 1
        assert tally[(stratum, "坏")] == 1
        assert small[cursor]["edit_type"] == stratum
        assert small[cursor]["construction_gold"] == "正确"
        assert small[cursor + 1]["edit_type"] == stratum
        assert small[cursor + 1]["construction_gold"] == "坏"
        cursor += 2

    large = select_spotcheck(records, n=100)
    assert len(large) == 20
    cursor = 0
    for stratum in STRATA:
        assert _counts(large)[(stratum, "正确")] == 2
        assert _counts(large)[(stratum, "坏")] == 3
        block = large[cursor : cursor + 5]
        assert [row["construction_gold"] for row in block] == ["正确", "正确", "坏", "坏", "坏"]
        assert {row["edit_type"] for row in block} == {stratum}
        cursor += 5


def test_two_exports_and_reversed_input_keep_claim_order():
    records = _records(4)
    first = [row["claim_id"] for row in select_spotcheck(records, n=30)]
    second = [row["claim_id"] for row in select_spotcheck(records, n=30)]
    reversed_ids = [row["claim_id"] for row in select_spotcheck(list(reversed(records)), n=30)]
    assert first == second == reversed_ids
    left = export_spotcheck(records, None, n=100)
    right = export_spotcheck(list(reversed(records)), None, n=100)
    assert [row["claim_id"] for row in left["spotcheck"]] == [
        row["claim_id"] for row in right["spotcheck"]
    ]


def test_spotcheck_ignores_judge_labels():
    records = _records(4)
    bare = [row["claim_id"] for row in export_spotcheck(records, None, n=30)["spotcheck"]]
    labeled = export_spotcheck(records, _labels(records), n=30)
    flipped = []
    for row in _labels(records):
        row = copy.deepcopy(row)
        row["kimi"] = {"A": "否", "B": "是"}
        flipped.append(row)
    changed = export_spotcheck(records, flipped, n=30)
    assert bare == [row["claim_id"] for row in labeled["spotcheck"]]
    assert bare == [row["claim_id"] for row in changed["spotcheck"]]


def test_user_tables_hide_arm_gold_and_judge_choices():
    records = _records(4)
    target = records[0]["claim_id"]
    missing_id = records[1]["claim_id"]
    labels = []
    for row in records:
        if row["claim_id"] == target:
            labels.append(_label_row(target, overrides={"kimi": {"A": "否"}}))
        elif row["claim_id"] == missing_id:
            labels.append(_label_row(missing_id, absent={"kimi": ("A", "B")}))
        else:
            labels.append(_label_row(row["claim_id"]))
    out = export_spotcheck(records, labels, n=30)
    for row in out["spotcheck"]:
        assert set(row) == {
            "claim_id",
            "before_text",
            "after_text",
            "evidence_text",
            "evidence_id",
        }
    adjudication_ids = {row["claim_id"] for row in out["adjudication"]}
    missing_ids = {row["claim_id"] for row in out["missing"]}
    assert target in adjudication_ids
    assert target not in missing_ids
    assert missing_id in missing_ids
    assert missing_id not in adjudication_ids
    assert adjudication_ids.isdisjoint(missing_ids)
    for row in out["adjudication"]:
        assert set(row) == {
            "claim_id",
            "before_text",
            "after_text",
            "evidence_text",
            "evidence_id",
            "裁决",
            "备注",
        }
        assert row["裁决"] == ""
        assert row["备注"] == ""
    missing_row = next(row for row in out["missing"] if row["claim_id"] == missing_id)
    assert set(missing_row) == {"claim_id", "缺失"}
    assert missing_row["缺失"] == ["kimi:A", "kimi:B"]
    leaked = ("ARM_SENTINEL", "ABL_SENTINEL", "LEAK_QWEN", "LEAK_DEEPSEEK", "LEAK_KIMI", "真人盲审")
    for token in leaked:
        assert token not in out["text"]
    adjudication_text = out["text"].split("不一致裁决表", 1)[1].split("缺失清单", 1)[0]
    for token in ("qwen", "deepseek", "kimi", "是", "否", "ARM_SENTINEL"):
        assert token not in adjudication_text
    assert IDENTITY in out["text"]
    assert SPOTCHECK_ROLE in out["text"]
    assert "抽检表" in out["text"]
    assert "缺失清单" in out["text"]


def test_partial_gap_is_missing_even_if_the_other_question_would_disagree():
    records = _records(4)
    claim_id = records[0]["claim_id"]
    labels = [
        _label_row(claim_id, overrides={"deepseek": {"A": "否"}}, absent={"kimi": ("A",)})
        if row["claim_id"] == claim_id
        else _label_row(row["claim_id"])
        for row in records
    ]
    out = export_spotcheck(records, labels, n=30)
    assert claim_id not in {row["claim_id"] for row in out["adjudication"]}
    missing_row = next(row for row in out["missing"] if row["claim_id"] == claim_id)
    assert missing_row["缺失"] == ["kimi:A"]
    assert "是" not in "".join(missing_row["缺失"])
    assert "否" not in "".join(missing_row["缺失"])


def test_written_spotcheck_answer_becomes_the_adjudication():
    records = _records(1)
    selected = select_spotcheck(records, n=30)
    assert len(selected) == 8
    target = selected[0]["claim_id"]
    labels = [
        _label_row(target, overrides={"qwen": {"B": "是"}})
        if row["claim_id"] == target
        else _label_row(row["claim_id"])
        for row in records
    ]
    answer = {"A": "是", "B": "否"}
    out = export_spotcheck(records, labels, n=30, answers={target: answer})
    row = next(item for item in out["adjudication"] if item["claim_id"] == target)
    assert row["裁决"] == answer
    assert row["备注"] == ALREADY
    assert ALREADY in out["text"]
    assert row["裁决"] is not answer


def test_answer_outside_spotcheck_does_not_skip_a_second_look():
    records = _records(4)
    selected = {row["claim_id"] for row in select_spotcheck(records, n=30)}
    outside = next(row["claim_id"] for row in records if row["claim_id"] not in selected)
    labels = [
        _label_row(outside, overrides={"deepseek": {"A": "否"}})
        if row["claim_id"] == outside
        else _label_row(row["claim_id"])
        for row in records
    ]
    out = export_spotcheck(
        records,
        labels,
        n=30,
        answers={outside: {"A": "是", "B": "否"}},
    )
    row = next(item for item in out["adjudication"] if item["claim_id"] == outside)
    assert row["裁决"] == ""
    assert row["备注"] == ""
    assert ALREADY not in out["text"]


def test_export_does_not_replace_construction_gold_or_drop_rows():
    records = _records(4)
    original = copy.deepcopy(records)
    labels = _labels(records)
    out = export_spotcheck(records, labels, n=30, answers={"数值-c-00": {"A": "否", "B": "否"}})
    assert records == original
    assert len(out["spotcheck"]) == 8
    assert all(row["construction_gold"] in _GOLD for row in records)


def test_short_pool_and_duplicate_claim_id_raise():
    with pytest.raises(SpotcheckError):
        select_spotcheck(_records(1), n=100)
    rows = _records(1)
    rows.append(dict(rows[0]))
    with pytest.raises(SpotcheckError):
        select_spotcheck(rows, n=30)


def test_module_has_no_blind_review_wording_or_secret_reads():
    source = Path(select_spotcheck.__code__.co_filename).read_text(encoding="utf-8")
    for token in (
        "真人盲审",
        "getenv",
        "environ",
        "DASHSCOPE",
        "DEEPSEEK",
        "MOONSHOT",
        "API_KEY",
        "named_streams",
        ".shuffle(",
        ".sample(",
        ".randrange(",
        ".choices(",
        "urllib",
        "httpx",
        "requests",
    ):
        assert token not in source
    assert IDENTITY == "模型评委加单人抽检"
    assert SPOTCHECK_ROLE == "用户单人抽检"
    assert ALREADY == "已有抽检答案，不再第二次看"
