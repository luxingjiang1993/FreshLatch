"""#492：路线 C · ALT 附录测量；不进主成立；零 LLM。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.eval.patch_events_alt_appendix_c import (
    main,
    merge_alt_pointer_into_result_c,
    run_alt_appendix_c,
    write_alt_appendix_c,
    write_result_c_alt_pointer,
)
from freshlatch.eval.patch_events_post_c import extract_primary_fingerprint


@pytest.fixture(autouse=True)
def _ban_llm(monkeypatch):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("ALT 附录禁止发模型")),
    )


def test_run_alt_appendix_fixture_separable_and_formal_c():
    pack = run_alt_appendix_c()
    assert pack["sent_model"] is False
    assert pack["feeds_main_establishment"] is False
    assert pack["fixture"]["upgrade_tier"] == "可分开"
    assert pack["fixture"]["fixed_k_appendix"]["appendix_only"] is True
    assert pack["fixture"]["fixed_k_appendix"]["feeds_upgrade"] is False
    assert pack["formal_c_same_text"]["n"] == 100
    # 正式层可分开或分不开都合法；但不得喂主成立
    assert pack["formal_c_same_text"]["upgrade_tier"] in {"可分开", "分不开"}


def test_pointer_merge_keeps_primary_fingerprint():
    text = Path("docs/evidence/patch-events/RESULT-C.md").read_text(encoding="utf-8")
    before = extract_primary_fingerprint(text)
    pack = run_alt_appendix_c()
    merged = merge_alt_pointer_into_result_c(text, pack)
    assert extract_primary_fingerprint(merged) == before
    assert "<!-- PE-C-ALT:BEGIN -->" in merged
    assert "不进主成立" in merged
    assert "| T 对 C | false-accept rate |" not in merged.split("PE-C-ALT:BEGIN")[1].split(
        "PE-C-ALT:END"
    )[0]


def test_write_refuses_result_b(tmp_path):
    pack = {
        "fixture": {"upgrade_tier": "可分开"},
        "formal_c_same_text": {"upgrade_tier": "分不开"},
    }
    pe = tmp_path / "docs" / "evidence" / "patch-events"
    pe.mkdir(parents=True)
    (pe / "RESULT-C.md").write_text(
        "\n".join(
            [
                "# C",
                "| T 对 C | false-accept rate | 0.1 | 0 | 1 | 不成立 |",
                "| T 对 B1 | false-accept rate | 0.1 | 0 | 1 | 不成立 |",
                "| T 对 B2 | false-accept rate | 0.1 | 0 | 1 | 不成立 |",
                "- **固定放行数 k** = 1",
                "## B 负结果附录",
                "",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="RESULT-B"):
        write_result_c_alt_pointer(pack, root=tmp_path, path=pe / "RESULT-B.md")
    with pytest.raises(RuntimeError, match="主缝"):
        write_alt_appendix_c(pack, root=tmp_path, path=pe / "RESULT-C.md")


def test_main_dry_json(capsys, monkeypatch):
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_alt_appendix_c.write_alt_appendix_c",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("dry")),
    )
    code = main(["--dry-json"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"feeds_main_establishment": false' in out
    assert '"sent_model": false' in out
