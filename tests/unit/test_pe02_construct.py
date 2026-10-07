"""PE-02 构造算子与配额。夹具语料，零 API，不改金标和 PREREG。"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_construct as pc
from freshlatch.eval.patch_events_construct import (
    ChunkRef,
    ClaimView,
    ConstructError,
    QUOTAS,
    round_half_away_from_zero,
    shift_month,
)

_ROOT = Path(__file__).resolve().parents[2]


def _write_doc(directory: Path, doc_id: str, as_of: str, chunks: list[tuple[str, str]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    body = [
        "---",
        f"doc_id: {doc_id}",
        f"as_of: {as_of}",
        "source_type: private",
        "title: fixture",
        "checksum:",
        "---",
    ]
    for anchor, text in chunks:
        body.append(f"## {anchor}")
        body.append(text)
    (directory / f"{doc_id}.md").write_text("\n".join(body) + "\n", encoding="utf-8")


def _add_claim(
    tmp: Path,
    claims: list[dict[str, str]],
    claim_id: str,
    statement: str,
    t1_chunks: list[tuple[str, str]],
    t0_chunks: list[tuple[str, str]] | None = None,
) -> None:
    _write_doc(tmp / "corpus" / "t1", claim_id, "T1", t1_chunks)
    _write_doc(tmp / "corpus" / "t0", claim_id, "T0", t0_chunks or [("p1", "旧口径")])
    claims.append(
        {
            "claim_id": claim_id,
            "statement": statement,
            "t0_evidence_ids": [f"{claim_id}#p1"],
        }
    )


def _full_fixture(tmp: Path, extra_numeric: int = 0) -> Path:
    claims: list[dict[str, str]] = []
    for index in range(29 + extra_numeric):
        _add_claim(
            tmp,
            claims,
            f"a-num-{index:03d}",
            "价格为 100 元",
            [("p1", "价格为 80 元，手续费 3 元。")],
        )
    for index in range(29):
        _add_claim(
            tmp,
            claims,
            f"b-date-{index:03d}",
            "生效日为 2024 年 3 月 15 日",
            [("p1", "生效日为 2026 年 6 月 15 日。备案日为 2020 年 1 月 2 日。")],
        )
    for index in range(29):
        _add_claim(
            tmp,
            claims,
            f"c-clause-{index:03d}",
            "服务商应当删除日志",
            [
                ("p1", "服务商应当留存日志"),
                ("p2", "渠道商不得导出日志"),
            ],
        )
    for index in range(28):
        _add_claim(
            tmp,
            claims,
            f"d-del-{index:03d}",
            "除金融机构外，一般行业可存储在境外，留存不少于 5 年，大约符合旧口径",
            [("p1", "留存不少于 5 年这一限定已废止。除金融机构外这一例外仍然有效。")],
        )
    docket = tmp / "docket.json"
    docket.write_text(json.dumps({"claims": claims}, ensure_ascii=False), encoding="utf-8")
    return docket


def _bad(result: pc.ConstructResult, edit_type: str) -> list[pc.ConstructedEdit]:
    rows = [
        edit
        for edit in result.pilot
        if edit.record["edit_type"] == edit_type and edit.record["construction_gold"] == "坏"
    ]
    rows.extend(
        edit
        for edit in result.n100
        if edit.record["edit_type"] == edit_type and edit.record["construction_gold"] == "坏"
    )
    return rows


def test_repeat_quotas_and_operators(tmp_path: Path):
    docket = _full_fixture(tmp_path)
    corpus = tmp_path / "corpus"
    quotas_before = json.dumps(QUOTAS, ensure_ascii=False)
    first = pc.construct_samples(docket, corpus)
    second = pc.construct_samples(docket, corpus)

    def signature(result: pc.ConstructResult) -> list[tuple[str, str, str, int | None]]:
        rows = list(result.pilot) + list(result.n100)
        return [
            (
                edit.record["claim_id"],
                edit.record["edit_type"],
                edit.record["construction_gold"],
                edit.operator,
            )
            for edit in rows
        ]

    assert signature(first) == signature(second)
    assert first.shortfalls == ()
    assert json.dumps(QUOTAS, ensure_ascii=False) == quotas_before

    pilot_ids = [edit.record["claim_id"] for edit in first.pilot]
    n30_ids = [edit.record["claim_id"] for edit in first.n30]
    n100_ids = [edit.record["claim_id"] for edit in first.n100]
    assert len(pilot_ids) == 15
    assert len(n30_ids) == 30
    assert len(n100_ids) == 100
    assert len(set(pilot_ids)) == 15
    assert len(set(n30_ids)) == 30
    assert set(n30_ids) <= set(n100_ids)
    assert n100_ids[:30] == n30_ids
    assert set(pilot_ids).isdisjoint(n30_ids)
    assert set(pilot_ids).isdisjoint(n100_ids)

    deletion = [edit for edit in first.pilot if edit.record["edit_type"] == "删除"]
    assert len(deletion) == 3
    assert sum(edit.record["construction_gold"] == "正确" for edit in deletion) == 1
    assert sum(edit.record["construction_gold"] == "坏" for edit in deletion) == 2

    for edit_type, (correct, bad) in QUOTAS["n100"].items():
        rows = [edit for edit in first.n100 if edit.record["edit_type"] == edit_type]
        assert len(rows) == 25
        assert sum(edit.record["construction_gold"] == "正确" for edit in rows) == correct
        assert sum(edit.record["construction_gold"] == "坏" for edit in rows) == bad
        assert bad == correct + 1

    for edit in list(first.pilot) + list(first.n100):
        assert "decision" not in edit.record
        assert edit.record["ablation"] == ""
        if edit.record["construction_gold"] == "正确":
            assert edit.operator is None
        else:
            assert edit.operator is not None

    numeric_bad = _bad(first, "数值")
    assert [edit.operator for edit in numeric_bad] == [index % 4 for index in range(len(numeric_bad))]
    assert [edit.sign for edit in numeric_bad] == [
        "plus" if (index // 4) % 2 == 0 else "minus" for index in range(len(numeric_bad))
    ]
    assert "88 元" in numeric_bad[0].record["after_text"]
    assert numeric_bad[0].operator == 0 and numeric_bad[0].sign == "plus"
    assert "72 元" in numeric_bad[4].record["after_text"]
    assert "800 元" in numeric_bad[1].record["after_text"]
    assert "8 元" in numeric_bad[5].record["after_text"]
    assert "3 元" in numeric_bad[2].record["after_text"]
    assert "80 万元" in numeric_bad[3].record["after_text"]
    assert "80 个百分点" in numeric_bad[7].record["after_text"]

    date_bad = _bad(first, "日期")
    assert "2027 年 6 月 15 日" in date_bad[0].record["after_text"]
    assert "2025 年 6 月 15 日" in date_bad[4].record["after_text"]
    assert "2026 年 7 月 15 日" in date_bad[1].record["after_text"]
    assert "2026 年 5 月 15 日" in date_bad[5].record["after_text"]
    assert "2020 年 1 月 2 日" in date_bad[2].record["after_text"]
    assert date_bad[3].record["evidence_id"].endswith("@T0")
    assert "2026 年 6 月 15 日" in date_bad[3].record["after_text"]

    clause_bad = _bad(first, "条款替换")
    assert clause_bad[0].record["after_text"] == "服务商不得留存日志"
    assert clause_bad[1].record["after_text"] == "渠道商应当留存日志"
    assert clause_bad[2].record["after_text"] == "渠道商不得导出日志"
    assert clause_bad[3].record["evidence_id"].endswith("#p2@T1")
    assert clause_bad[3].record["after_text"] == "服务商应当留存日志"

    deletion_bad = _bad(first, "删除")
    correct = next(
        edit.record["after_text"]
        for edit in first.pilot
        if edit.record["edit_type"] == "删除" and edit.record["construction_gold"] == "正确"
    )
    assert correct == "除金融机构外，一般行业可存储在境外，大约符合旧口径"
    assert deletion_bad[0].record["after_text"] == "一般行业可存储在境外，留存不少于 5 年，大约符合旧口径"
    assert deletion_bad[2].record["evidence_id"] == ""
    assert deletion_bad[2].record["after_text"] == correct
    assert deletion_bad[3].edit_note == "按新证据必须更新"
    assert "大约" not in deletion_bad[3].record["after_text"]
    assert "留存不少于 5 年" in deletion_bad[3].record["after_text"]


def test_ineligible_slot_keeps_operator_and_reports_shortfall(tmp_path: Path):
    claims: list[dict[str, str]] = []
    _add_claim(
        tmp_path,
        claims,
        "a-same",
        "价格为 9 元",
        [("p1", "价格为 4 元，另有 9 元。")],
    )
    _add_claim(
        tmp_path,
        claims,
        "b-ok",
        "价格为 100 元",
        [("p1", "价格为 80 元，手续费 3 元。")],
    )
    docket = tmp_path / "docket.json"
    docket.write_text(json.dumps({"claims": claims}, ensure_ascii=False), encoding="utf-8")
    quotas_before = json.dumps(QUOTAS, ensure_ascii=False)
    result = pc.construct_samples(docket, tmp_path / "corpus")
    assert json.dumps(QUOTAS, ensure_ascii=False) == quotas_before
    assert result.pilot[0].record["claim_id"] == "b-ok"
    assert result.pilot[0].operator == 0
    assert result.pilot[0].sign == "plus"
    assert "88 元" in result.pilot[0].record["after_text"]
    voided = result.shortfalls[0]
    assert voided.claim_id == "a-same"
    assert voided.edit_type == "数值"
    assert voided.operator == 0
    assert voided.reason == "扰动结果与正确值相同"
    assert any(item.reason == "语料不足" and item.operator == 0 for item in result.shortfalls[1:])


def test_extra_claims_are_not_taken_from_conformal_reserve(tmp_path: Path):
    docket = _full_fixture(tmp_path, extra_numeric=5)
    result = pc.construct_samples(docket, tmp_path / "corpus")
    numeric_ids = [
        edit.record["claim_id"]
        for edit in list(result.pilot) + list(result.n100)
        if edit.record["edit_type"] == "数值"
    ]
    assert len(numeric_ids) == 29
    assert not any(claim_id.startswith("a-num-03") or claim_id >= "a-num-029" for claim_id in numeric_ids)
    assert all(item.edit_type != "数值" or item.reason != "语料不足" for item in result.shortfalls)


def test_rounding_and_month_carry():
    assert round_half_away_from_zero(Decimal("16.5"), 0) == Decimal("17")
    assert round_half_away_from_zero(Decimal("13.5"), 0) == Decimal("14")
    assert round_half_away_from_zero(Decimal("1.375"), 2) == Decimal("1.38")
    assert round_half_away_from_zero(Decimal("1.125"), 2) == Decimal("1.13")
    assert round_half_away_from_zero(Decimal("-1.5"), 0) == Decimal("-2")
    assert shift_month(2026, 1, 15, -1) == (2025, 12, 15)
    assert shift_month(2026, 12, 15, 1) == (2027, 1, 15)
    with pytest.raises(ConstructError, match="日期无效"):
        shift_month(2026, 1, 31, 1)


def test_decimal_percent_and_invalid_day_via_builder():
    fraction = ClaimView(
        claim_id="frac",
        statement="费率为 2%",
        doc_id="frac",
        anchor="p1",
        t1=ChunkRef("p1", "frac#p1@T1", "费率为 1.25%，另计 0.50%。"),
        t0=ChunkRef("p1", "frac#p1@T0", "旧"),
        t1_chunks=(ChunkRef("p1", "frac#p1@T1", "费率为 1.25%，另计 0.50%。"),),
        t0_chunks=(ChunkRef("p1", "frac#p1@T0", "旧"),),
    )
    built = pc._build(fraction, "数值", "坏", 0, "plus")
    assert "1.38%" in built.record["after_text"]

    january = ClaimView(
        claim_id="jan",
        statement="生效日为 2024 年 1 月 1 日",
        doc_id="jan",
        anchor="p1",
        t1=ChunkRef("p1", "jan#p1@T1", "生效日为 2026 年 1 月 31 日。"),
        t0=ChunkRef("p1", "jan#p1@T0", "旧"),
        t1_chunks=(ChunkRef("p1", "jan#p1@T1", "生效日为 2026 年 1 月 31 日。"),),
        t0_chunks=(ChunkRef("p1", "jan#p1@T0", "旧"),),
    )
    with pytest.raises(ConstructError, match="日期无效"):
        pc._build(january, "日期", "坏", 1, "plus")


def test_module_does_not_read_secrets_or_touch_locked_files():
    text = Path(pc.__file__).read_text(encoding="utf-8")
    for token in ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "getenv", "environ", "random"):
        assert token not in text
    prereg = _ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
    gold = _ROOT / "data" / "eval" / "gold.json"
    sample = _ROOT / "data" / "corpus" / "t1" / "t0-competitor-notes.md"
    before = {path: path.read_bytes() for path in (prereg, gold, sample)}
    pc.construct_samples(_ROOT / "data" / "t0_docket.json", _ROOT / "data" / "corpus")
    after = {path: path.read_bytes() for path in (prereg, gold, sample)}
    assert before == after
