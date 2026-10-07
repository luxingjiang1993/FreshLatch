"""#347:三份 w12 脚本在 scripts/archive，文档不再指向旧路径。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NAMES = (
    "w12_comprehensive_acceptance_test.py",
    "w12_comprehensive_acceptance_test_v2.py",
    "w12_comprehensive_acceptance_test_final.py",
)
DOCS = (
    "docs/spec/15-整仓分层验收.md",
    "docs/evidence/full-repo/PLAN-20260930.md",
    "docs/evidence/full-repo/PLAN-20260930-REMAINING.md",
    "docs/evidence/full-repo/REPORT-20260930-REMAINING.md",
)


def test_w12_scripts_live_under_archive():
    for name in NAMES:
        assert (ROOT / "scripts" / "archive" / name).is_file()
        assert not (ROOT / "scripts" / name).exists()


def test_docs_cite_the_archive_path():
    blob = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in DOCS)
    assert "scripts/w12_comprehensive_" not in blob
    assert "scripts/archive/w12_comprehensive_" in blob
