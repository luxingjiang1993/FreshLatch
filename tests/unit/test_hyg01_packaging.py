"""HYG-01 打包契约：editable 安装、钉、CI lint、不再用 src 插入导入。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

IN_SCOPE_DIRS = ("src", "scripts", "tests")

RUFF_SELECT = ("E9", "F821", "F822", "F823", "F601", "F602", "F811", "F706")


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_hyg01_packaging_contract():
    pyproject = _read("pyproject.toml")
    requirements = _read("requirements.txt")
    assert "fastembed==0.8.1" in pyproject
    assert "fastembed==0.8.1" in requirements
    assert "fastembed==0.7.1" not in pyproject
    assert "fastembed==0.7.1" not in requirements
    assert "BAAI/bge-reranker-base" in pyproject
    assert "BAAI/bge-reranker-base" in requirements
    assert "ruff==0.15.0" in pyproject
    for code in RUFF_SELECT:
        assert code in pyproject

    for line in requirements.splitlines():
        pin = line.strip()
        if not pin or pin.startswith("#"):
            continue
        assert pin in pyproject, pin

    assert "sys.path.insert" not in _read("tests/conftest.py")
    ci = _read(".github/workflows/ci.yml")
    assert 'pip install -e ".[dev]"' in ci
    assert "ruff check" in ci
    assert "python -m pytest tests/ -q" in ci
    assert "pythonpath = ." in _read("pytest.ini")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in _read(
        "src/freshlatch/store/base.py"
    )
    install = _read(".cursor/environment.json")
    assert "pip install -e" in install
    assert ".[dev]" in install

    quick = _read("README.md").split("## Quick start", 1)[1].split("## ", 1)[0]
    assert 'pip install -e ".[dev]"' in quick
    assert "PYTHONPATH" not in quick
    assert "ruff check" in _read("docs/agents/agent-guards.md")
    assert "ruff check" in _read("AGENTS.md")

    needle = "sys.path." + "insert"
    offenders: list[str] = []
    for folder in IN_SCOPE_DIRS:
        for path in (ROOT / folder).rglob("*.py"):
            if path.resolve() == Path(__file__).resolve():
                continue
            if needle in path.read_text(encoding="utf-8"):
                offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
