"""#337:两处无引用函数删除后,定义和调用都不再出现。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _python_under(*folders: str) -> str:
    parts: list[str] = []
    for folder in folders:
        for path in (ROOT / folder).rglob("*.py"):
            parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_unused_functions_have_no_def_or_call():
    blob = _python_under("src", "scripts")
    assert "def build_text_pdf" not in blob
    assert "build_text_pdf(" not in blob
    assert "def build_list_row_from_session" not in blob
    assert "build_list_row_from_session(" not in blob
    anchor = (ROOT / "src/freshlatch/store/pdf_anchor.py").read_text(encoding="utf-8")
    assert "def pdf_to_document" in anchor
