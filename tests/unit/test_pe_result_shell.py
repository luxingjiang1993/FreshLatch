"""结果表：评委一致性已填，其余数字格保持「未填」。"""

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
    assert [(row[2], row[3]) for row in cohen[0][1:]] == [
        ("0.926829268292683", "30"),
        ("0.7715736040609137", "30"),
        ("0.8421052631578947", "30"),
        ("0.926829268292683", "30"),
        ("0.7804878048780488", "30"),
        ("0.85", "30"),
    ]
    assert [(row[1], row[2]) for row in fleiss[0][1:]] == [
        ("0.8473713962690785", "30"),
        ("0.8523783488244943", "30"),
    ]

    projects = [table for table in tables if table[0] == ["项目", "值"]]
    assert len(projects) == 2
    assert projects[0][1][0] == "固定放行数 k"
    assert projects[0][2:] == [
        ["共形预留 false-accept rate 上界", "未做"],
        ["语料缺额", "0"],
    ]
    assert projects[1][1:] == [
        ["抽检一致率", EMPTY],
        ["用户对评委的 Cohen's κ", EMPTY],
    ]

    for table in (arms, comparisons, ablations):
        header = table[0]
        indexes = [i for i, name in enumerate(header) if name not in LABEL_HEADERS]
        assert indexes
        for row in table[1:]:
            assert len(row) == len(header)
            if table is comparisons and row[1] == "false-accept rate":
                continue
            for index in indexes:
                assert row[index] == EMPTY
                assert re.search(r"\d", row[index]) is None

    assert "n=30 的 Cohen's κ 与 Fleiss' κ 按仓库 `agreement` 写入。" in text
    assert re.search(r"[abcd]\d{3}", text) is None
    yes, no = "是", "否"
    for left in (yes, no):
        for right in (yes, no):
            assert f"{left}/{right}" not in text
