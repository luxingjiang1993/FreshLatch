"""#336:运行时依赖与 pyproject 对齐,setuptools 用精确钉。"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SETUPTOOLS_PIN = "setuptools==68.1.2"


def _requirement_lines(text: str) -> list[str]:
    pins: list[str] = []
    for line in text.splitlines():
        raw = line.split("#", 1)[0].strip()
        if raw:
            pins.append(raw)
    return pins


def test_runtime_pins_match_project_dependencies():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime = _requirement_lines(requirements)
    declared = list(project["project"]["dependencies"])
    assert runtime == declared
    assert all("==" in pin for pin in runtime)
    assert all(">=" not in pin and "<=" not in pin for pin in runtime)
    for name in ("pytest", "httpx", "ruff"):
        assert not any(pin.startswith(f"{name}==") for pin in runtime)
    dev = project["project"]["optional-dependencies"]["dev"]
    assert "pytest==9.1.1" in dev
    assert "httpx==0.28.1" in dev
    assert "ruff==0.15.0" in dev
    assert project["build-system"]["requires"] == [SETUPTOOLS_PIN]
    assert "fastembed==0.8.1" in runtime
    assert "fastembed==0.8.1" in declared
    assert "fastembed==0.7.1" not in requirements
    assert "fastembed==0.7.1" not in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    base = (ROOT / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    assert 'PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"' in base
