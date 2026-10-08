"""结果表壳子：格子按预注册排齐，数字格保持「未填」。"""

from __future__ import annotations

import re
from pathlib import Path

from freshlatch.eval.patch_events_ablation import HYBRID_COLUMN
from freshlatch.eval.patch_events_metrics import ABLATION_ORDER, METRIC_ORDER, PRIMARY_CONTRASTS
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
PREREG = ROOT / "docs" / "evidence" / "patch-events" / "PREREG.md"
EMPTY = "未填"
METRICS = ("false-accept rate",) + METRIC_ORDER[1:]
ABLATION_GLOSS = {
    "no_chunk_bind": "拿掉 chunk 绑定",
    "no_auto_verify": "拿掉自动核验",
    "soft_warning": "hard reject 换成 soft warning",
    "retrieval_bm25": "检索臂换成 BM25",
    HYBRID_COLUMN: "另记一列，不进入主比较",
}
LABEL_HEADERS = {"臂", "比较", "指标", "消融", "预注册说法", "题", "配对", "项目"}


def _tables(text: str) -> list[list[list[str]]]:
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            if current:
                tables.append(current)
                current = []
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and all(set(cell) <= set("-:") and cell for cell in cells):
            continue
        current.append(cells)
    if current:
        tables.append(current)
    return tables


def _by_header(tables: list[list[list[str]]], first: str) -> list[list[str]]:
    matches = [table for table in tables if table[0][0] == first]
    assert len(matches) == 1
    return matches[0]


def test_shell_follows_locked_comparisons_and_leaves_numbers_blank():
    text = RESULT.read_text(encoding="utf-8")
    prereg = PREREG.read_text(encoding="utf-8")
    assert "第一主比较：T 对 C 的误放率。" in prereg
    assert "第二：T 对 B1 的误放率。" in prereg
    assert "第三：T 对 B2 的误放率。" in prereg
    assert METRIC_ORDER[0] == "误放率"
    assert PRIMARY_CONTRASTS == ("C", "B1", "B2")
    assert ABLATION_ORDER == (
        "no_chunk_bind",
        "no_auto_verify",
        "soft_warning",
        "retrieval_bm25",
    )
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
    assert "false-accept" in text
    assert "BM25" in text
    assert "hybrid+rerank" in text
    assert "rerank" in text

    tables = _tables(text)
    arms = _by_header(tables, "臂")
    assert [row[0] for row in arms[1:]] == ["C", "T（fail-closed）", "B1", "B2"]
    assert "false-accept rate" in arms[0][3]

    comparisons = _by_header(tables, "比较")
    expected_comparisons = [
        (f"T 对 {contrast}", metric)
        for contrast in PRIMARY_CONTRASTS
        for metric in METRICS
    ]
    assert [(row[0], row[1]) for row in comparisons[1:]] == expected_comparisons
    assert HYBRID_COLUMN not in {row[0] for row in comparisons[1:]}

    ablations = _by_header(tables, "消融")
    expected_ablations = [
        (tag, ABLATION_GLOSS[tag], metric)
        for tag in (*ABLATION_ORDER, HYBRID_COLUMN)
        for metric in METRICS
    ]
    assert [(row[0], row[1], row[2]) for row in ablations[1:]] == expected_ablations

    cohen = [
        table for table in tables if table[0][0] == "题" and table[0][1] == "配对"
    ]
    assert len(cohen) == 1
    assert [(row[0], row[1]) for row in cohen[0][1:]] == [
        ("A", "qwen-deepseek"),
        ("A", "qwen-kimi"),
        ("A", "deepseek-kimi"),
        ("B", "qwen-deepseek"),
        ("B", "qwen-kimi"),
        ("B", "deepseek-kimi"),
    ]
    fleiss = [table for table in tables if table[0][0] == "题" and "Fleiss" in table[0][1]]
    assert len(fleiss) == 1
    assert [row[0] for row in fleiss[0][1:]] == ["A", "B"]

    value_cells: list[str] = []
    for table in tables:
        header, *rows = table
        assert rows
        indexes = [i for i, name in enumerate(header) if name not in LABEL_HEADERS]
        assert indexes
        for row in rows:
            assert len(row) == len(header)
            for index in indexes:
                value_cells.append(row[index])
    assert value_cells
    assert set(value_cells) == {EMPTY}
    for cell in value_cells:
        assert re.search(r"\d", cell) is None

    # 数字只出现在臂名 B1/B2、术语 BM25、以及表头 p95 / 95% 区间。
    assert set(re.findall(r"\d+", text)) <= {"1", "2", "25", "95"}
    for banned in ("a001", "a002", "b004", "d002", "否/否", "是/是", "是/否", "否/是"):
        assert banned not in text
