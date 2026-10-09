"""#491：路线 C 消融/次要填格 + 抽检导出；零 LLM；不改主比较成立格。"""

from __future__ import annotations

from pathlib import Path

import pytest

from freshlatch.eval.patch_events_post_c import (
    extract_primary_fingerprint,
    main,
    merge_post_into_result_c,
    render_post_sections,
    run_post_c,
    write_result_c_post,
)


@pytest.fixture(autouse=True)
def _ban_llm(monkeypatch):
    monkeypatch.setattr(
        "freshlatch.llm.LLMClient",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("后置票禁止发模型")),
    )


def test_run_post_c_zero_llm_and_ablation_on_t_only():
    pack = run_post_c()
    assert pack["sent_model"] is False
    assert pack["n"] == 100
    assert pack["k"] == 93
    assert set(pack["ablations"]) >= {
        "no_chunk_bind",
        "no_auto_verify",
        "soft_warning",
        "retrieval_bm25",
        "hybrid+rerank",
    }
    for tag, rows in pack["ablations"].items():
        if tag == "voids":
            continue
        for row in rows:
            assert row["arm"] == "T"
    spot = pack["spotcheck"]["spotcheck"]
    assert len(spot) == 20  # n=100 配额：4 层 × (2+3)


def test_merge_does_not_touch_primary_false_accept_rows():
    text = Path("docs/evidence/patch-events/RESULT-C.md").read_text(encoding="utf-8")
    before = extract_primary_fingerprint(text)
    assert "T 对 C" in before and "k** = 93" in before
    pack = run_post_c()
    merged = merge_post_into_result_c(text, pack)
    assert extract_primary_fingerprint(merged) == before
    assert "<!-- PE-C-POST:BEGIN -->" in merged
    assert "## 消融（只在 T · 不进主比较）" in merged
    assert "抽检一致率**：未填" in merged or "抽检一致率**：未填" in merged
    assert "真人盲审" in merged and "不得" in merged


def test_write_refuses_result_b(tmp_path):
    pack = {
        "k": 1,
        "primary": {"arms": {}, "k": 1},
        "ablation_intervals": [],
        "ablations": {},
        "spotcheck": {"spotcheck": []},
    }
    # 最小 RESULT-C 主表
    pe = tmp_path / "docs" / "evidence" / "patch-events"
    pe.mkdir(parents=True)
    result_c = pe / "RESULT-C.md"
    result_c.write_text(
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
        write_result_c_post(pack, root=tmp_path, path=pe / "RESULT-B.md")


def test_render_zero_release_is_undefined_not_zero():
    # 构造放行数为 0 的臂块：误放/可复验应为「无定义」
    pack = {
        "k": 0,
        "primary": {
            "arms": {
                "C": {
                    "natural": {"放行数": 0, "放行率": 0.0, "误放率": None, "可复验率": None, "误拒率": 1.0, "错改率": 0.0},
                    "fixed": {"误放率": None, "误拒率": None, "错改率": None, "可复验率": None},
                    "latency_median": None,
                    "latency_p95": None,
                    "cost": 0,
                },
                "T": {
                    "natural": {"放行数": 0, "放行率": 0.0, "误放率": None, "可复验率": None, "误拒率": None, "错改率": None},
                    "fixed": {"误放率": None, "误拒率": None, "错改率": None, "可复验率": None},
                    "latency_median": None,
                    "latency_p95": None,
                    "cost": 0,
                },
                "B1": {
                    "natural": {"放行数": 0, "放行率": 0.0, "误放率": None, "可复验率": None, "误拒率": None, "错改率": None},
                    "fixed": {"误放率": None, "误拒率": None, "错改率": None, "可复验率": None},
                    "latency_median": None,
                    "latency_p95": None,
                    "cost": 0,
                },
                "B2": {
                    "natural": {"放行数": 0, "放行率": 0.0, "误放率": None, "可复验率": None, "误拒率": None, "错改率": None},
                    "fixed": {"误放率": None, "误拒率": None, "错改率": None, "可复验率": None},
                    "latency_median": None,
                    "latency_p95": None,
                    "cost": 0,
                },
            }
        },
        "ablation_intervals": [],
        "ablations": {},
        "spotcheck": {"spotcheck": []},
    }
    md = render_post_sections(pack)
    # C 行自然误放在放行 0 时应为无定义，不得出现「| 0 |」冒充误放率格子——至少正文含「无定义」
    assert "无定义" in md
    assert "| C | 0 | 0 | 无定义 |" in md or "无定义" in md.split("各臂")[1]


def test_main_dry_json_no_write(capsys, monkeypatch):
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_post_c.write_result_c_post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("dry 不得写")),
    )
    code = main(["--dry-json"])
    assert code == 0
    out = capsys.readouterr().out
    assert '"sent_model": false' in out
    assert '"spotcheck_n": 20' in out
