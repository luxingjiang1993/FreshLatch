"""RET-01.1：x1 许可、去污染与题集结构检查。

不读模型密钥环境变量，不打开 dense 索引文件。
测试一律用 tmp fixture，不创建正式实验配置文件。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from freshlatch.eval.x1_checks import (
    LAW_NAMES,
    MAX_PUBLIC_RATIO,
    MIN_CHUNKS,
    MIN_PER_QTYPE,
    MIN_SYNTHETIC_RATIO,
    MIN_TRAP_ADVERSARIAL_RATIO,
    check_x1,
    clean_text,
    eight_gram_overlap,
    strip_law_names,
)

ROOT = Path(__file__).resolve().parents[2]
SMALL_FLOORS = {
    "min_chunks": 0,
    "min_per_qtype": 0,
    "min_trap_adversarial_ratio": 0.0,
    "min_synthetic_ratio": 0.0,
    "max_public_ratio": 1.0,
}

LAW = "数据出境安全评估办法"


def _cfg(**over):
    cfg = {
        "top_k": 10,
        "rrf_k": 60,
        "embed_model": "text-embedding-v4",
        "embed_dim": 1024,
        "draft_model": "qwen-flash",
        "draft_temperature": None,
        "draft_seed": None,
        "flag_model": "qwen-plus",
        "flag_thinking": False,
        "decontam_8gram_max": 0.2,
        "lead_delta": 0.10,
        "budget_cny_max": 10,
    }
    cfg.update(over)
    return cfg


def _write_doc(root: Path, as_of_dir: str, as_of: str, doc_id: str, body: str, **meta):
    folder = root / as_of_dir
    folder.mkdir(parents=True, exist_ok=True)
    fm = {
        "doc_id": doc_id,
        "as_of": as_of,
        "source_type": meta.pop("source_type", "private"),
        "title": meta.pop("title", doc_id),
        "provenance": meta.pop("provenance", "synthetic"),
        "license": meta.pop("license", "synthetic"),
        "domain": meta.pop("domain", "D0"),
        "genre": meta.pop("genre", "S1"),
    }
    fm.update(meta)
    lines = ["---"]
    for k, v in fm.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append(body.rstrip() + "\n")
    (folder / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def _ok_body(extra: str = "占位叙述用于凑块。") -> str:
    return f"## p1\n{extra}\n"


def _q(
    qid: str,
    query: str,
    *,
    qtype: str = "paraphrase",
    category: str = "hard",
    relevant: list[str] | None = None,
    distractors: list[str] | None = None,
    **extra,
):
    item = {
        "id": qid,
        "query": query,
        "qtype": qtype,
        "category": category,
        "relevant": relevant or [],
        "distractors": distractors or [],
        "eval_intent": extra.pop("eval_intent", "单测"),
        "as_of": extra.pop("as_of", "T1"),
    }
    item.update(extra)
    return item


def _run(corpus, traps, questions, config):
    return check_x1(
        corpus, traps, questions, config, floor_overrides=SMALL_FLOORS
    )


def test_floor_constants_locked():
    assert MIN_PER_QTYPE == 30
    assert MIN_TRAP_ADVERSARIAL_RATIO == 0.30
    assert MIN_CHUNKS == 600
    assert MIN_SYNTHETIC_RATIO == 0.60
    assert MAX_PUBLIC_RATIO == 0.40


def test_missing_or_null_threshold_does_not_substitute_0_2(tmp_path: Path):
    """配置缺键或 null 时退出码 2，且不拿 0.2 / 0.5 判 paraphrase 污染。"""
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    # 块正文含大量与问句相同的 8-gram，比例会高于 0.2 和 0.5
    shared = "甲乙丙丁戊己庚辛壬癸子丑寅卯"
    _write_doc(corpus, "t1", "T1", "doc-a", _ok_body(shared))
    questions = [
        _q("p1", shared, qtype="paraphrase", relevant=["doc-a#p1@T1"]),
    ]
    r_null = _run(corpus, traps, questions, _cfg(decontam_8gram_max=None))
    assert r_null.exit_code == 2
    assert r_null.decontam_hits == 0
    rec = r_null.records[0]
    assert "decontam=0" in rec
    assert "r8=na" not in rec
    r_missing = _run(corpus, traps, questions, {k: v for k, v in _cfg().items() if k != "decontam_8gram_max"})
    assert r_missing.exit_code == 2
    assert r_missing.decontam_hits == 0
    r_locked = _run(corpus, traps, questions, _cfg(decontam_8gram_max=0.2))
    assert r_locked.exit_code == 1
    assert r_locked.decontam_hits == 1


def test_acceptance_lexical_title_not_enough(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(
        corpus,
        "t1",
        "T1",
        "law-doc",
        f"## p1\n{LAW}适用于重要数据出境活动。\n",
    )
    q_ok = "客户追问数据出境安全评估办法是否仍要走评估"
    questions = [
        _q("lex-title", q_ok, qtype="lexical", relevant=["law-doc#p1@T1"]),
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.decontam_hits == 0
    assert "decontam=0" in r.records[0]
    assert "r8=na" in r.records[0]


def test_acceptance_lexical_full_query_copy(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    copied = "适用于重要数据出境活动"
    _write_doc(
        corpus,
        "t1",
        "T1",
        "law-doc",
        f"## p1\n{LAW}{copied}。\n",
    )
    questions = [
        _q("lex-copy", copied, qtype="lexical", relevant=["law-doc#p1@T1"]),
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 1
    assert r.decontam_hits == 1
    assert "decontam=1" in r.records[0]


def test_whitelist_stripped_from_query_not_chunk(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    extra = "后续安排如何处理完毕"
    _write_doc(corpus, "t1", "T1", "law-doc", f"## p1\n{LAW}只出现在块里。\n")
    query = LAW + extra
    cleaned_q = strip_law_names(clean_text(query))
    assert LAW not in cleaned_q
    assert extra == cleaned_q or extra.replace("。", "") in cleaned_q
    body = clean_text(f"## p1\n{LAW}只出现在块里。")
    assert LAW in body
    before = eight_gram_overlap(clean_text(query), [body])
    after = eight_gram_overlap(cleaned_q, [body])
    assert before is not None and before > 0.2
    assert after is None or after <= 0.2
    questions = [
        _q("para-wl", query, qtype="paraphrase", relevant=["law-doc#p1@T1"]),
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 0
    assert r.decontam_hits == 0
    # 先删更长的名字，避免「公司法」截断「中华人民共和国公司法」
    assert strip_law_names("中华人民共和国公司法条文") == "条文"
    assert strip_law_names("公司法修订") == "修订"


def test_multi_hop_single_doc_id(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t1", "T1", "same-doc", "## p1\n要点甲独有。\n\n## p2\n要点乙独有。\n")
    questions = [
        _q(
            "mh-one",
            "跨段提问但不跨文档",
            qtype="multi_hop",
            relevant=["same-doc#p1@T1", "same-doc#p2@T1"],
            answer_points=["要点甲独有", "要点乙独有"],
        )
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 1
    assert any("doc_id" in m for m in r.messages)


def test_multi_hop_same_doc_t0_t1_not_two(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t0", "T0", "snap", "## p1\n旧快照甲点。\n")
    _write_doc(corpus, "t1", "T1", "snap", "## p1\n新快照乙点。\n")
    questions = [
        _q(
            "mh-snap",
            "同一文档两个快照",
            qtype="multi_hop",
            relevant=["snap#p1@T0", "snap#p1@T1"],
            answer_points=["旧快照甲点", "新快照乙点"],
        )
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 1
    assert any("doc_id" in m for m in r.messages)


def test_multi_hop_answer_points_same_chunk(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t1", "T1", "doc-a", "## p1\n甲点与乙点写在一起。\n")
    _write_doc(corpus, "t1", "T1", "doc-b", "## p1\n无关旁述。\n")
    questions = [
        _q(
            "mh-shortcut",
            "看起来像两跳",
            qtype="multi_hop",
            relevant=["doc-a#p1@T1", "doc-b#p1@T1"],
            answer_points=["甲点", "乙点"],
        )
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 1
    assert any("answer_points" in m for m in r.messages)


def test_multi_hop_points_split_across_docs(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t1", "T1", "doc-a", "## p1\n只有甲点在这里。\n")
    _write_doc(corpus, "t1", "T1", "doc-b", "## p1\n只有乙点在这里。\n")
    questions = [
        _q(
            "mh-ok",
            "两跳分属两文档",
            qtype="multi_hop",
            relevant=["doc-a#p1@T1", "doc-b#p1@T1"],
            answer_points=["只有甲点在这里", "只有乙点在这里"],
        )
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 0


def test_lcs_flag_is_not_decontam_gate(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    # 问句连续 8-gram 不在块里，但作为子序列 LCS 很长
    q = "甲乙丙丁戊己庚辛壬癸"
    body = "甲壹乙贰丙叁丁肆戊伍己陆庚柒辛捌壬玖癸"
    _write_doc(corpus, "t1", "T1", "doc-a", f"## p1\n{body}\n")
    questions = [_q("para-lcs", q, qtype="paraphrase", relevant=["doc-a#p1@T1"])]
    r = _run(corpus, traps, questions, _cfg(decontam_8gram_max=0.2))
    assert r.exit_code == 0
    assert r.lcs_flags >= 1
    assert r.decontam_hits == 0
    rec = r.records[0]
    assert "lcs_flag=1" in rec
    assert "decontam=0" in rec


def test_ratio_equal_threshold_not_contaminated(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    query = "abcdefghijkl"  # 5 个 8-gram
    body = "abcdefgh" + "zzzzzzzzzzzz"
    _write_doc(corpus, "t1", "T1", "doc-a", f"## p1\n{body}\n")
    questions = [_q("eq", query, qtype="paraphrase", relevant=["doc-a#p1@T1"])]
    r = _run(corpus, traps, questions, _cfg(decontam_8gram_max=0.2))
    rec = r.records[0]
    assert "r8=0.200000" in rec
    assert r.decontam_hits == 0
    assert r.exit_code == 0


def test_bad_license_exit_1(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(
        corpus,
        "t1",
        "T1",
        "doc-a",
        _ok_body("无污染叙述十二字以上。"),
        license="not-a-license",
        provenance="public",
    )
    questions = [
        _q("p1", "无污染问句十二字以上", qtype="paraphrase", relevant=["doc-a#p1@T1"]),
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.exit_code == 1
    assert r.license_violations >= 1


def test_cli_exit_codes(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    traps.mkdir()
    shared = "甲乙丙丁戊己庚辛壬癸子丑寅卯"
    _write_doc(corpus, "t1", "T1", "doc-a", _ok_body(shared), license="not-a-license", provenance="public")
    _write_doc(corpus, "t1", "T1", "same", "## p1\n甲独。\n\n## p2\n乙独。\n")
    questions = [
        _q("p-hi", shared, qtype="paraphrase", relevant=["doc-a#p1@T1"]),
        _q(
            "mh-one",
            "单文档两锚",
            qtype="multi_hop",
            relevant=["same#p1@T1", "same#p2@T1"],
            answer_points=["甲独", "乙独"],
        ),
    ]
    qpath = tmp_path / "q.json"
    qpath.write_text(json.dumps({"queries": questions}, ensure_ascii=False), encoding="utf-8")
    cfg1 = tmp_path / "c1.json"
    cfg1.write_text(json.dumps(_cfg(), ensure_ascii=False), encoding="utf-8")
    cfg2 = tmp_path / "c2.json"
    cfg2.write_text(json.dumps(_cfg(decontam_8gram_max=None), ensure_ascii=False), encoding="utf-8")
    script = ROOT / "scripts" / "check_x1.py"
    p1 = subprocess.run(
        [
            sys.executable,
            str(script),
            "--corpus",
            str(corpus),
            "--traps",
            str(traps),
            "--questions",
            str(qpath),
            "--config",
            str(cfg1),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert p1.returncode == 1, p1.stdout + p1.stderr
    p2 = subprocess.run(
        [
            sys.executable,
            str(script),
            "--corpus",
            str(corpus),
            "--traps",
            str(traps),
            "--questions",
            str(qpath),
            "--config",
            str(cfg2),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert p2.returncode == 2, p2.stdout + p2.stderr
    assert "decontam_hits=" in p2.stdout
    # null 配置不得用 0.2/0.5 给 paraphrase 打去污染分
    r_fn = _run(corpus, traps, questions, _cfg(decontam_8gram_max=None))
    para = [x for x in r_fn.records if x.startswith("q p-hi ")][0]
    assert "decontam=0" in para


def test_guardrail_excluded_from_denominators(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t1", "T1", "doc-a", _ok_body("护栏旁述十二字以上。"))
    questions = [
        _q(
            "g1",
            "旧快照护栏",
            qtype="lexical",
            category="trap",
            score_role="guardrail",
            relevant=[],
        ),
        _q(
            "a1",
            "臂对比题十二字以上",
            qtype="paraphrase",
            category="hard",
            relevant=["doc-a#p1@T1"],
        ),
    ]
    r = _run(corpus, traps, questions, _cfg())
    assert r.n_guardrail == 1
    assert r.n_arm == 1
    assert r.qtype_counts["lexical"] == 0
    assert r.qtype_counts["paraphrase"] == 1
    assert r.trap_adversarial_ratio == 0.0
    g = [x for x in r.records if x.startswith("q g1 ")][0]
    assert "score_role=guardrail" in g
    assert "r8=na" in g


def test_looser_config_floor_fails(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(corpus, "t1", "T1", "doc-a", _ok_body("叙述十二字以上即可。"))
    questions = [_q("a1", "问句十二字以上即可", relevant=["doc-a#p1@T1"])]
    r = _run(corpus, traps, questions, _cfg(min_per_qtype=20))
    assert r.exit_code == 1
    assert any("更松" in m for m in r.messages)


def test_p2_requires_stats_attribution(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(
        corpus,
        "t1",
        "T1",
        "gdp",
        _ok_body("叙述自写的统计口径。"),
        genre="P2",
        license="synthetic",
        provenance="synthetic",
        data_source_url="https://www.stats.gov.cn/example",
        attribution="引自国家统计局网站 www.stats.gov.cn",
    )
    questions = [_q("a1", "问句十二字以上即可", relevant=["gdp#p1@T1"])]
    r = _run(corpus, traps, questions, _cfg())
    assert r.license_violations == 0
    _write_doc(
        corpus,
        "t1",
        "T1",
        "gdp-bad",
        _ok_body("叙述自写的统计口径二。"),
        genre="P2",
        license="synthetic",
        provenance="synthetic",
        data_source_url="https://www.stats.gov.cn/example",
        attribution="未注明官网",
    )
    r2 = _run(corpus, traps, questions, _cfg())
    assert r2.license_violations >= 1


def test_tests_do_not_touch_secrets_or_dense_index():
    impl = (ROOT / "src" / "freshlatch" / "eval" / "x1_checks.py").read_text(
        encoding="utf-8"
    )
    assert "DASHSCOPE" not in impl
    assert "index.sqlite" not in impl
    assert "environ" not in impl
    assert "decontam_8gram_max" in impl
    assert "0.2" not in impl
    assert "0.5" not in impl
