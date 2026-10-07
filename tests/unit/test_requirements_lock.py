"""#349:传递依赖锁与 requirements.txt 的直接钉一致。不改安装方式。"""

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = (
    "uv pip compile requirements.txt --python-version 3.11 "
    "--python-platform x86_64-unknown-linux-gnu -o requirements.lock",
    "uv pip compile requirements.txt --python-version 3.11 "
    "--python-platform x86_64-pc-windows-msvc -o requirements.lock",
)
UNCHANGED = {
    "requirements.txt": "4bce621ca55c039e3f4476172f4bfc3de224223552e3e1eb5b829f59a57f50b9",
    "pyproject.toml": "777d422c93cfd1c205425f4a1edec97c8485d1554842a40f457772181bec38ae",
    ".github/workflows/ci.yml": "46ff1e9b407bb2a0ab62fa979d94784fbaf6a0626e6f3a3afaea381f69d3936f",
}


def _normalize(name: str) -> str:
    return name.lower().replace("_", "-")


def _direct_pins(text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in text.splitlines():
        raw = line.split("#", 1)[0].strip()
        if not raw or raw.startswith("-"):
            continue
        name, version = raw.split("==", 1)
        pins[_normalize(name)] = version
    return pins


def _lock_direct_versions(text: str) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line or line.startswith("#") or line.startswith((" ", "\t")):
            index += 1
            continue
        spec = line.split(";", 1)[0].split("#", 1)[0].strip()
        comments: list[str] = []
        nxt = index + 1
        while nxt < len(lines) and (
            not lines[nxt] or lines[nxt].startswith((" ", "\t", "#"))
        ):
            comments.append(lines[nxt])
            nxt += 1
        if "-r requirements.txt" in "\n".join(comments) and "==" in spec:
            name, version = spec.split("==", 1)
            found.setdefault(_normalize(name), set()).add(version.strip())
        index = nxt
    return found


def test_lock_direct_pins_match_requirements_txt():
    for path, digest in UNCHANGED.items():
        # Windows 检出可能把换行写成 CRLF。比对前归一成 LF，锁的是仓库内容。
        data = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == digest
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")
    assert all(command in lock for command in COMMANDS)
    assert "pillow==11.3.0" in lock
    assert "Python>=3.14" in lock or "Python >=3.14" in lock or "3.14" in lock
    required = _direct_pins((ROOT / "requirements.txt").read_text(encoding="utf-8"))
    locked = _lock_direct_versions(lock)
    assert set(required) == set(locked)
    for name, version in required.items():
        assert locked[name] == {version}
    assert required["fastembed"] == "0.8.1"
