"""主指标三行未填时，五处对外表面相对 101c81e 无 diff。"""

from __future__ import annotations

import hashlib
from pathlib import Path

from freshlatch.eval.patch_events_metrics import _metric_on, format_rate, natural_rates

_ROOT = Path(__file__).resolve().parents[2]
_README = _ROOT / "README.md"
_DIAGRAM = _ROOT / "docs" / "现状四闸-结构图.html"
_APP = _ROOT / "src" / "freshlatch" / "ui" / "app.py"
_RESULT = _ROOT / "docs" / "evidence" / "patch-events" / "RESULT.md"
_BASELINE = "101c81e0b631d53ecf4d1db913a2ab6ae86e43e5"
_LEDE_SHA256 = "1e9cb2bb7a4daa0460adfa106f3f7b57bc2d1fbb4ca10cef1dc1f150a9f85237"
_DIAGRAM_SHA256 = "8e44d3c94cb85c444202eef40ef65ca5925d02ec11bd666043aede90a6ce1a7f"
_ENTRY_SHA256 = "719da2f3c2389d0d54edad3fdf2bb78714fa1364831fef5853735df4e3108faf"
_THESIS = (
    "Default demo thesis (synthetic): "
    '*"Does the judgment on entering the Southeast Asia SMB AI customer-support '
    'market in the next 12 months still hold?"*'
)
_ENTRY = "python -m freshlatch.ui.app    # Reverify Sheet → http://127.0.0.1:8000"
_COMPARISONS = ("T 对 C", "T 对 B1", "T 对 B2")
_SURFACE_MARKERS = ("简历一行", "mastery pack", "mastery-pack", "mastery_pack")
# 101c81e 没有独立的简历一行文件，也没有 mastery pack 文件。
_BASELINE_SURFACE_FILES: dict[str, str] = {}


def _lf(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _text_or_none(path: Path) -> str | None:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _primary_false_accept(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[1] != "false-accept rate":
            continue
        if cells[0] in _COMPARISONS:
            found[cells[0]] = cells[2]
    return found


def _rates_unfilled(text: str) -> bool:
    cells = _primary_false_accept(text)
    return cells == {name: "未填" for name in _COMPARISONS}


def _cites_three_rates(text: str) -> bool:
    lowered = text.lower()
    if "false-accept" not in lowered:
        return False
    dash = all(token in text for token in ("T-C", "T-B1", "T-B2"))
    labeled = all(token in text for token in _COMPARISONS)
    return dash or labeled


def _surface_paths() -> list[Path]:
    found: list[Path] = []
    for path in _ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        stem = path.stem.lower().replace("_", "-")
        if stem in {"resume-line", "mastery-pack", "简历一行"} or "简历" in path.name:
            found.append(path)
    return found


def _citing_surfaces() -> list[str]:
    hits: list[str] = []
    for path in _surface_paths():
        relative = path.relative_to(_ROOT).as_posix()
        text = _text_or_none(path)
        if text is None:
            continue
        if relative not in _BASELINE_SURFACE_FILES:
            if _cites_three_rates(text):
                hits.append(relative)
            continue
        if _sha(text) != _BASELINE_SURFACE_FILES[relative]:
            hits.append(relative)
    spec = _ROOT / "docs" / "spec"
    self_path = Path(__file__).resolve()
    for path in _ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == self_path:
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if spec in path.parents:
            continue
        if path.suffix.lower() not in {".md", ".html", ".txt", ".py"}:
            continue
        text = _text_or_none(path)
        if text is None:
            continue
        for line in text.splitlines():
            if any(marker in line.lower() for marker in _SURFACE_MARKERS) and _cites_three_rates(line):
                hits.append(f"{path.relative_to(_ROOT).as_posix()}: {line.strip()}")
    return hits


def _assert_frozen_surfaces() -> None:
    readme = _lf(_README)
    lede = readme.split("## Snapshot", 1)[0]
    assert _sha(lede) == _LEDE_SHA256
    assert _sha(_lf(_DIAGRAM)) == _DIAGRAM_SHA256
    assert [line for line in readme.splitlines() if line.startswith("Default demo thesis")] == [_THESIS]
    assert [line for line in readme.splitlines() if "python -m freshlatch.ui.app" in line] == [_ENTRY]
    entry = _lf(_APP).split('if __name__ == "__main__":', 1)[1]
    assert _sha(entry) == _ENTRY_SHA256
    assert "(synthetic)" in _THESIS
    assert _citing_surfaces() == []


def test_unfilled_primary_rates_freeze_five_surfaces():
    result = _lf(_RESULT)
    cells = _primary_false_accept(result)
    assert _BASELINE == "101c81e0b631d53ecf4d1db913a2ab6ae86e43e5"
    if _rates_unfilled(result):
        assert all(value != "0" for value in cells.values())
    # 抽检一致率、评委 κ、延迟、成本都不改这五处。
    assert "Cohen's κ" in result
    assert "qwen-deepseek" in result
    assert "抽检一致率" in result
    _assert_frozen_surfaces()


def test_k_zero_false_accept_is_undefined_and_surfaces_stay_frozen():
    value = _metric_on("误放率", [0, 1], [], [True, False], [False, True], [False, False])
    assert value is None
    rendered = format_rate(value)
    assert rendered == "无定义"
    assert rendered != "0"
    assert "0" not in rendered
    rates = natural_rates(
        [
            {
                "construction_gold": "坏",
                "decision": "reject",
                "evidence_id": "",
                "reverify_ok": False,
            }
        ],
        ingested_t1=set(),
    )
    assert rates["放行数"] == 0
    assert rates["误放率"] is None
    assert format_rate(rates["误放率"]) != "0"
    result = _lf(_RESULT)
    if _rates_unfilled(result):
        _assert_frozen_surfaces()
        for value_cell in _primary_false_accept(result).values():
            assert value_cell != "0"
