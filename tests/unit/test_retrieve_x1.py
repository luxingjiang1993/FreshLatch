"""RET-01.5：x1 分型三臂打分脚本（假向量，不打网）。"""

from __future__ import annotations

import json
import math
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.eval.retrieve_eval import _p95_ms, recall_at_k
from freshlatch.eval.retrieve_typed import (
    QUERY_EMBED_BATCH,
    compute_x1_fingerprints,
    conflict_pair_correct,
    count_uncached,
    estimate_cost_from_uncached,
    fingerprints_match,
    guardrail_pass,
    is_production_dense_db,
    load_score_config,
    make_cached_query_embedder,
    parse_prereg_fingerprints,
    reject_protected_sqlite_paths,
    require_as_of,
    run_cli,
    run_typed_compare,
    score_role_of,
    unique_embed_texts,
)
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE
from freshlatch.store.ingest import load_corpus
from freshlatch.store.pipeline import pack_vec
from freshlatch.store.sqlite_store import SQLiteStore

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "run_retrieve_x1.py"
DIM = 8


def _cfg(**over):
    cfg = {
        "top_k": 10,
        "rrf_k": 60,
        "embed_model": "text-embedding-v4",
        "embed_dim": DIM,
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


def _locked_cfg(**over):
    """check-only 用，embed_dim 必须 1024。"""
    return _cfg(embed_dim=1024, **over)


def _write_doc(root: Path, as_of_dir: str, as_of: str, doc_id: str, clauses: list[str], **meta):
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
    for i, body in enumerate(clauses, start=1):
        lines.append(f"## p{i}")
        lines.append(body)
        lines.append("")
    (folder / f"{doc_id}.md").write_text("\n".join(lines), encoding="utf-8")


def _q(qid, query, *, qtype="paraphrase", category="hard", relevant=None, distractors=None, **extra):
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


def _write_dummy_dense(db_path: Path, corpus: Path, traps: Path, dim: int = DIM) -> int:
    """与 test_i3_hard_gold._write_dummy_dense 相同手法：pack_vec，非全零。"""
    pairs = list(load_corpus(corpus))
    if traps.is_dir():
        pairs.extend(load_corpus(traps))
    n = 0
    store = SQLiteStore(db_path)
    for doc, chunks in pairs:
        for i, chunk in enumerate(chunks):
            vec = [0.0] * dim
            vec[i % dim] = 1.0
            chunk.vec = pack_vec(vec)
        store.add_document(doc, chunks)
        n += len(chunks)
    return n


def _fake_embed_match_first(texts: list[str]) -> list[list[float]]:
    """查询向量对齐 dummy dense 的第 0 槽。"""
    return [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in texts]


def _boom_embed(*_a, **_k):
    raise AssertionError("不得调用真实 embed_texts")


def test_production_retrieval_mode_is_hybrid_rerank():
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"


def test_is_production_dense_db_string_only():
    assert is_production_dense_db("data/dense/index.sqlite") is True
    assert is_production_dense_db(Path("data/dense/index.sqlite")) is True
    assert is_production_dense_db("/tmp/data/dense/index.sqlite") is True
    assert is_production_dense_db("data/dense/./index.sqlite") is True
    assert is_production_dense_db("data//dense/index.sqlite") is True
    assert is_production_dense_db("data/dense/../dense/index.sqlite") is True
    assert is_production_dense_db("DATA/DENSE/INDEX.SQLITE") is True
    assert is_production_dense_db(r"data\dense\index.sqlite") is True
    assert is_production_dense_db("data/dense/x1-index.sqlite") is False
    assert is_production_dense_db("/tmp/x1-index.sqlite") is False


def test_cli_rejects_production_dense_db_without_touching_file(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_cfg()), encoding="utf-8")
    code = run_cli([
        "--config", str(cfg),
        "--dense-db", "data/dense/index.sqlite",
        "--cache", str(tmp_path / "c.sqlite"),
        "--out", str(tmp_path / "out"),
        "--prereg", str(tmp_path / "PREREG.md"),
    ])
    assert code != 0


def test_p50_uses_same_ceil_as_p95_and_does_not_double_ms():
    samples = [0.01, 0.02, 0.03, 0.04]
    p95 = _p95_ms(samples)
    ordered = sorted(samples)
    p50 = ordered[max(0, math.ceil(0.50 * len(ordered)) - 1)] * 1000.0
    assert p95 == ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] * 1000.0
    assert p50 == 20.0


def _score_fixture(tmp_path: Path):
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    _write_doc(
        corpus, "t1", "T1", "doc-now",
        [
            "现行条文 保留期限两年 现行独有词ALPHA",
            "被取代条文 旧期限三年 被取代独有词BETA",
            "干扰块 无关叙述 GAMMA",
        ],
    )
    _write_doc(
        corpus, "t0", "T0", "doc-old",
        [
            "旧快照独有词OMEGA 过期标价",
        ],
    )
    _write_doc(
        traps, "t1", "T1", "trap-now",
        [
            "陷阱现行 同快照 陷阱词DELTA",
        ],
    )
    _write_doc(
        traps, "t0", "T0", "trap-old",
        [
            "陷阱旧版 独有词THETA",
        ],
    )
    questions = [
        _q(
            "arm-lex",
            "现行独有词ALPHA 保留期限两年",
            qtype="lexical",
            category="hard",
            relevant=["doc-now#p1@T1"],
            distractors=["doc-now#p2@T1"],
        ),
        _q(
            "arm-para",
            "现行独有词ALPHA",
            qtype="paraphrase",
            category="hard",
            relevant=["doc-now#p1@T1"],
            distractors=["doc-now#p3@T1"],
        ),
        _q(
            "arm-hop",
            "现行独有词ALPHA 陷阱词DELTA",
            qtype="multi_hop",
            category="trap",
            relevant=["doc-now#p1@T1", "trap-now#p1@T1"],
            distractors=["doc-now#p2@T1"],
            answer_points=["现行独有词ALPHA", "陷阱词DELTA"],
        ),
        _q(
            "arm-conflict",
            "现行独有词ALPHA 被取代独有词BETA 保留期限",
            qtype="paraphrase",
            category="adversarial",
            relevant=["doc-now#p1@T1"],
            distractors=["doc-now#p2@T1"],
            conflict_pair={
                "in_force": "doc-now#p1@T1",
                "superseded": "doc-now#p2@T1",
            },
        ),
        _q(
            "guard-t1",
            "旧快照独有词OMEGA 现行独有词ALPHA",
            qtype="lexical",
            category="trap",
            relevant=[],
            distractors=["doc-old#p1@T0"],
            score_role="guardrail",
            as_of="T1",
        ),
    ]
    qpath = tmp_path / "questions.json"
    qpath.write_text(
        json.dumps({"queries": questions}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_cfg()), encoding="utf-8")
    dense = tmp_path / "dense.sqlite"
    n = _write_dummy_dense(dense, corpus, traps)
    assert n >= 4
    cache = tmp_path / "cache.sqlite"
    return corpus, traps, qpath, cfg, dense, cache


def test_typed_scoring_excludes_guardrail_and_splits_conflict(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    out = tmp_path / "out"
    payload = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=out,
        embed_fn=_fake_embed_match_first,
        disable_as_of=False,
    )
    main = payload["main"]
    assert main["n_arm"] == 4
    assert main["n_guardrail"] == 1
    assert payload["diagnostic_ran"] is False
    assert payload["as_of_off_diagnostic"] is None
    assert payload["production_retrieval_mode"] == "hybrid+rerank"
    assert main["buckets"]["总体"]["bm25"]["n"] == 4
    assert main["buckets"]["lexical"]["bm25"]["n"] == 1
    arm_ids = [row["id"] for row in main["per_query"] if row["score_role"] == "arm"]
    assert "guard-t1" not in arm_ids
    assert set(arm_ids) == {"arm-lex", "arm-para", "arm-hop", "arm-conflict"}
    g = main["guardrail"][0]
    assert g["id"] == "guard-t1"
    assert g["pass"] is True
    assert g["t0_hits"] == 0
    assert main["conflict_pair_n"] == 1
    acc = main["conflict_pair_ordering_accuracy"]
    assert acc["bm25"] == 0.0
    assert acc["hybrid"] == 1.0
    bm25 = main["buckets"]["总体"]["bm25"]
    assert bm25["R@10"] == 1.0
    assert bm25["MRR@10"] == 0.875
    assert bm25["distractor_hit@10"] == 0.75
    assert bm25["distractor_n"] == 4
    r10 = main["buckets"]["总体"]["hybrid"]["R@10"]
    assert r10 == 1.0
    assert main["buckets"]["总体"]["hybrid"]["MRR@10"] == 1.0
    md = Path(payload["report_path"]).read_text(encoding="utf-8")
    for label in ("总体", "lexical", "paraphrase", "multi_hop", "trap+adversarial"):
        assert label in md
    assert "conflict-pair ordering accuracy" in md
    assert "- bm25: 0.0000" in md
    assert "- hybrid: 1.0000" in md
    assert "未跑" in md
    assert "参考" in md
    raw = json.loads(Path(payload["json_path"]).read_text(encoding="utf-8"))
    for row in raw["main"]["per_query"]:
        assert "qtype" in row
        assert "score_role" in row
        assert "ranked" in row
    assert raw["main"]["buckets"]["总体"]["hybrid"]["R@10"] == r10
    assert main["dense_honest"] is True
    assert main["hybrid_honest"] is True
    assert main["buckets"]["总体"]["dense"]["modes_seen"] == ["dense"]
    assert main["buckets"]["总体"]["hybrid"]["modes_seen"] == ["hybrid"]
    assert not (out / "retrieve-x1-as-of-off.md").is_file()


def test_guardrail_fails_when_t0_leaks():
    hits_ok = [SimpleNamespace(as_of="T1")]
    hits_bad = [SimpleNamespace(as_of="T1"), SimpleNamespace(as_of="T0")]
    assert guardrail_pass(hits_ok) is True
    assert guardrail_pass(hits_bad) is False


def test_conflict_pair_rules():
    inf = "a#p1@T1"
    sup = "a#p2@T1"
    pair = {"in_force": inf, "superseded": sup}
    assert conflict_pair_correct([inf, sup], pair) is True
    assert conflict_pair_correct([sup, inf], pair) is False
    assert conflict_pair_correct([inf], pair) is True
    assert conflict_pair_correct([sup], pair) is False
    assert conflict_pair_correct([], pair) is False


def test_disable_as_of_is_separate_and_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    base = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "out-off",
        embed_fn=_fake_embed_match_first,
        disable_as_of=False,
    )
    on = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "out-on",
        embed_fn=_fake_embed_match_first,
        disable_as_of=True,
    )
    assert base["diagnostic_ran"] is False
    assert on["diagnostic_ran"] is True
    main_r = base["main"]["buckets"]["总体"]["bm25"]["R@10"]
    assert on["main"]["buckets"]["总体"]["bm25"]["R@10"] == main_r
    assert on["as_of_off_diagnostic"] is not None
    md = Path(on["report_path"]).read_text(encoding="utf-8")
    assert "不覆盖主表" in md or "不进主结论" in md
    assert Path(on["diagnostic_path"]).is_file()
    g_main = on["main"]["guardrail"][0]
    g_diag = on["as_of_off_diagnostic"]["guardrail"][0]
    assert g_main["pass"] is True
    assert g_diag["pass"] is False
    assert g_diag["t0_hits"] >= 1


def test_multi_hop_full_hit_and_distractor(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    payload = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "out",
        embed_fn=_fake_embed_match_first,
    )
    hop = payload["main"]["buckets"]["multi_hop"]["bm25"]
    assert hop["n"] == 1
    assert hop["multi_hop_full_hit@10"] is not None
    lex = payload["main"]["buckets"]["lexical"]["bm25"]
    assert lex["multi_hop_full_hit@10"] is None
    trap = payload["main"]["buckets"]["trap+adversarial"]["hybrid"]
    assert trap["n"] == 2
    dist = payload["main"]["buckets"]["总体"]["bm25"]["distractor_hit@10"]
    assert dist == 0.75
    assert payload["main"]["buckets"]["总体"]["bm25"]["distractor_n"] == 4


def test_estimate_only_no_embed(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, _dense, cache = _score_fixture(tmp_path)
    texts = unique_embed_texts(corpus, traps, qpath)
    uncached, miss, hit = count_uncached(
        texts, cache_path=cache, model="text-embedding-v4", dim=DIM
    )
    assert uncached > 0
    assert miss > 0
    assert hit == 0
    tokens, cny = estimate_cost_from_uncached(uncached)
    assert abs(tokens - uncached / 1.39) < 1e-9
    assert abs(cny - tokens / 1_000_000 * 0.5) < 1e-12
    env = os.environ.copy()
    env.pop("DASHSCOPE_API_KEY", None)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--estimate-only",
            "--corpus", str(corpus),
            "--traps", str(traps),
            "--questions", str(qpath),
            "--config", str(cfg),
            "--cache", str(cache),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "uncached_chars=" in proc.stdout
    assert "est_tokens=" in proc.stdout
    assert "est_cny=" in proc.stdout


def test_estimate_over_budget_nonzero(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    corpus, traps, qpath, cfg_path, _d, cache = _score_fixture(tmp_path)
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["budget_cny_max"] = 0.0
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    env = os.environ.copy()
    env.pop("DASHSCOPE_API_KEY", None)
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--estimate-only",
            "--corpus", str(corpus),
            "--traps", str(traps),
            "--questions", str(qpath),
            "--config", str(cfg_path),
            "--cache", str(cache),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode != 0


def _write_check_fixture(tmp_path: Path):
    """满足 RET-01.1 地板的 tmp 语料，供 --check-only 验收。"""
    corpus = tmp_path / "corpus"
    traps = tmp_path / "traps"
    t1_clauses = []
    t0_clauses = []
    trap_t1 = []
    trap_t0 = []
    for i in range(1, 151):
        t1_clauses.append(f"语料块t1编号{i:04d}的独立叙述。甲点{i:04d}")
        t0_clauses.append(f"语料块t0编号{i:04d}的独立叙述。乙点{i:04d}")
        trap_t1.append(f"陷阱块t1编号{i:04d}的独立叙述。")
        trap_t0.append(f"陷阱块t0编号{i:04d}的独立叙述。")
    _write_doc(corpus, "t1", "T1", "doc-t1", t1_clauses)
    _write_doc(corpus, "t0", "T0", "doc-t0", t0_clauses)
    _write_doc(traps, "t1", "T1", "trap-t1", trap_t1)
    _write_doc(traps, "t0", "T0", "trap-t0", trap_t0)
    queries = []
    for i in range(1, 31):
        queries.append(_q(
            f"lex-{i:02d}",
            f"词面问句编号{i:04d}不出现在块里abcdefgh",
            qtype="lexical",
            category="hard",
            relevant=[f"doc-t1#p{i}@T1"],
            distractors=[f"doc-t0#p{i}@T0"],
        ))
        queries.append(_q(
            f"para-{i:02d}",
            f"改写问法编号{i:04d}请说明独立事项",
            qtype="paraphrase",
            category="hard" if i > 15 else "trap",
            relevant=[f"doc-t1#p{i + 30}@T1"],
            distractors=[f"trap-t1#p{i}@T1"],
        ))
        queries.append(_q(
            f"hop-{i:02d}",
            f"跨文档问法编号{i:04d}请对照两端",
            qtype="multi_hop",
            category="adversarial" if i <= 15 else "hard",
            relevant=[f"doc-t1#p{i}@T1", f"doc-t0#p{i}@T0"],
            distractors=[f"trap-t1#p{i}@T1"],
            answer_points=[f"甲点{i:04d}", f"乙点{i:04d}"],
        ))
    queries.append(_q(
        "guard-1",
        "护栏问句编号0001只用于检查",
        qtype="lexical",
        category="trap",
        relevant=[],
        distractors=["doc-t0#p1@T0"],
        score_role="guardrail",
        as_of="T1",
    ))
    qpath = tmp_path / "questions.json"
    qpath.write_text(json.dumps({"queries": queries}, ensure_ascii=False), encoding="utf-8")
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_locked_cfg()), encoding="utf-8")
    computed = compute_x1_fingerprints(
        corpus=corpus, traps=traps, questions=qpath, config=cfg
    )
    prereg = tmp_path / "PREREG.md"
    prereg.write_text(
        "\n".join([
            "# PREREG 临时",
            "other_hex: " + ("deadbeef" * 8),
            f"corpus_aggregate_sha256: {computed['corpus_aggregate_sha256']}",
            f"questions_aggregate_sha256: {computed['questions_aggregate_sha256']}",
            f"config_sha256: {computed['config_sha256']}",
            "owner_freeze: pending",
            "",
        ]),
        encoding="utf-8",
    )
    return corpus, traps, qpath, cfg, prereg, computed


def test_check_only_prereg_ok_and_mismatch(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    corpus, traps, qpath, cfg, prereg, computed = _write_check_fixture(tmp_path)
    env = os.environ.copy()
    env.pop("DASHSCOPE_API_KEY", None)
    cmd = [
        sys.executable,
        str(SCRIPT),
        "--check-only",
        "--corpus", str(corpus),
        "--traps", str(traps),
        "--questions", str(qpath),
        "--config", str(cfg),
        "--prereg", str(prereg),
    ]
    ok = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, check=False)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "prereg fingerprints ok" in ok.stdout
    text = prereg.read_text(encoding="utf-8")
    old = computed["config_sha256"]
    flipped = ("0" if old[0] != "0" else "1") + old[1:]
    prereg.write_text(text.replace(old, flipped, 1), encoding="utf-8")
    bad = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, check=False)
    assert bad.returncode != 0
    prereg.write_text(
        "\n".join([
            "# PREREG 临时",
            "other_hex: " + ("cafebabe" * 8),
            f"corpus_aggregate_sha256: {computed['corpus_aggregate_sha256']}",
            f"questions_aggregate_sha256: {computed['questions_aggregate_sha256']}",
            f"config_sha256: {computed['config_sha256']}",
            "owner_freeze: confirmed",
            "",
        ]),
        encoding="utf-8",
    )
    still = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env, check=False)
    assert still.returncode == 0, still.stdout + still.stderr


def test_parse_prereg_ignores_other_hex_and_owner_freeze():
    text = (
        "abc 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef\n"
        "corpus_aggregate_sha256: " + ("a" * 64) + "\n"
        "questions_aggregate_sha256: " + ("b" * 64) + "\n"
        "config_sha256: " + ("c" * 64) + "\n"
        "owner_freeze: confirmed\n"
    )
    parsed = parse_prereg_fingerprints(text)
    assert parsed["corpus_aggregate_sha256"] == "a" * 64
    assert "owner_freeze" not in parsed
    assert fingerprints_match(text, parsed) is True


def test_do_not_touch_git_diff_empty():
    """x1 票仍锁住评测入口、付费 embedding、hard gold 与语料。

    2026-10-07 真人拍板改了 ``PRODUCTION_RETRIEVAL_MODE`` 和 Hard-Gold
    退出检查，所以 ``base.py`` 与 ``retrieve_eval.py`` 不再列入这份空 diff。
    """
    probe = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "main^{commit}"],
        cwd=ROOT,
        check=False,
    )
    if probe.returncode != 0:
        pytest.skip("无本地 main，AC4 是人工证据步骤")
    proc = subprocess.run(
        [
            "git", "diff", "--stat", "main", "--",
            "src/freshlatch/eval/__main__.py",
            "src/freshlatch/store/embeddings.py",
            "src/freshlatch/store/ingest.py",
            "src/freshlatch/llm.py",
            "docs/evidence/hard-gold-arm",
            "data/eval/retrieve_hard_gold.json",
            "data/corpus",
            "data/traps",
            "reports/dense-rebuild.md",
            "reports/retrieve-hard-gold-*",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_score_role_default_arm():
    assert score_role_of({}) == "arm"
    assert score_role_of({"score_role": None}) == "arm"
    assert score_role_of({"score_role": "guardrail"}) == "guardrail"


def test_recall_import_not_rewritten():
    assert recall_at_k(["a"], ["a"], 10) == 1.0


def test_cli_rejects_cache_equal_production_or_dense_db(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(_cfg()), encoding="utf-8")
    other = tmp_path / "other.sqlite"
    other.write_bytes(b"")
    code_prod = run_cli([
        "--estimate-only",
        "--config", str(cfg),
        "--corpus", str(tmp_path / "corpus"),
        "--traps", str(tmp_path / "traps"),
        "--questions", str(tmp_path / "q.json"),
        "--cache", "data/dense/index.sqlite",
    ])
    assert code_prod == 1
    code_same = run_cli([
        "--config", str(cfg),
        "--dense-db", str(other),
        "--cache", str(other),
        "--out", str(tmp_path / "out"),
        "--prereg", str(tmp_path / "PREREG.md"),
    ])
    assert code_same == 1
    with pytest.raises(ValueError):
        reject_protected_sqlite_paths(
            cache_path="data/dense/./index.sqlite", dense_db=tmp_path / "x.sqlite"
        )
    with pytest.raises(ValueError):
        reject_protected_sqlite_paths(cache_path=other, dense_db=other)


def test_count_uncached_is_read_only_and_missing_is_all_miss(tmp_path):
    dummy = tmp_path / "not-cache.sqlite"
    conn = sqlite3.connect(dummy)
    conn.execute("CREATE TABLE other (k TEXT)")
    conn.execute("INSERT INTO other VALUES ('x')")
    conn.commit()
    conn.close()
    before = dummy.read_bytes()
    uncached, miss, hit = count_uncached(
        ["abc", "abc", "de"], cache_path=dummy, model="text-embedding-v4", dim=8
    )
    after = dummy.read_bytes()
    assert before == after
    conn = sqlite3.connect(dummy)
    try:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        conn.close()
    assert tables == [("other",)]
    assert hit == 0
    assert miss == 2
    assert uncached == len("abc") + len("de")
    missing = tmp_path / "absent.sqlite"
    u2, m2, h2 = count_uncached(
        ["zz"], cache_path=missing, model="text-embedding-v4", dim=8
    )
    assert not missing.exists()
    assert (u2, m2, h2) == (2, 1, 0)


def test_query_embed_batches_at_most_eight(tmp_path):
    seen_sizes: list[int] = []

    def fake(texts: list[str]) -> list[list[float]]:
        seen_sizes.append(len(texts))
        return [[1.0] + [0.0] * 7 for _ in texts]

    queries = [f"问句{i:02d}独立文本" for i in range(12)]
    cache = tmp_path / "cache.sqlite"
    embedder, counter = make_cached_query_embedder(
        queries,
        cache_path=cache,
        model="text-embedding-v4",
        dim=DIM,
        embed_fn=fake,
    )
    assert QUERY_EMBED_BATCH == 8
    assert all(n <= 8 for n in seen_sizes)
    assert counter.max_batch <= 8
    assert len(seen_sizes) >= 2
    assert embedder(queries[0])[0] == 1.0


def test_conflict_pair_per_arm_bm25_zero_hybrid_one(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    payload = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "out",
        embed_fn=_fake_embed_match_first,
    )
    acc = payload["main"]["conflict_pair_ordering_accuracy"]
    assert acc["bm25"] == 0.0
    assert acc["hybrid"] == 1.0
    row = next(r for r in payload["main"]["per_query"] if r["id"] == "arm-conflict")
    assert row["conflict_pair_correct"]["bm25"] is False
    assert row["conflict_pair_correct"]["hybrid"] is True
    assert row["ranked"]["bm25"][0] == "doc-now#p2@T1"
    assert row["ranked"]["hybrid"][0] == "doc-now#p1@T1"
    md = Path(payload["report_path"]).read_text(encoding="utf-8")
    assert "- bm25: 0.0000" in md
    assert "- hybrid: 1.0000" in md


def test_mode_fallback_raises_before_write(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)

    def boom_query(q):
        raise RuntimeError("断 embed")

    import freshlatch.eval.retrieve_typed as mod

    orig = mod.make_cached_query_embedder

    def wrap(*args, **kwargs):
        _embedder, counter = orig(*args, **kwargs)
        return boom_query, counter

    monkeypatch.setattr(mod, "make_cached_query_embedder", wrap)
    out = tmp_path / "out-fallback"
    with pytest.raises(ValueError, match="模式不诚实"):
        mod.run_typed_compare(
            corpus=corpus,
            traps=traps,
            questions=qpath,
            config=cfg,
            dense_db=dense,
            cache_path=cache,
            out_dir=out,
            embed_fn=_fake_embed_match_first,
        )
    assert not (out / "retrieve-x1-arm-compare.md").is_file()


def test_missing_config_keys_and_wrong_top_k_fail(tmp_path):
    with pytest.raises(ValueError, match="缺键"):
        load_score_config({})
    cfg = _cfg()
    cfg["top_k"] = 3
    with pytest.raises(ValueError, match="top_k"):
        load_score_config(cfg)
    cfg2 = _cfg()
    cfg2["rrf_k"] = 1
    with pytest.raises(ValueError, match="rrf_k"):
        load_score_config(cfg2)
    empty = tmp_path / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    (tmp_path / "corpus" / "t0").mkdir(parents=True)
    (tmp_path / "corpus" / "t1").mkdir(parents=True)
    (tmp_path / "traps" / "t0").mkdir(parents=True)
    (tmp_path / "traps" / "t1").mkdir(parents=True)
    q = tmp_path / "q.json"
    q.write_text(json.dumps({"queries": []}), encoding="utf-8")
    code = run_cli([
        "--estimate-only",
        "--config", str(empty),
        "--corpus", str(tmp_path / "corpus"),
        "--traps", str(tmp_path / "traps"),
        "--questions", str(q),
    ])
    assert code != 0


def test_as_of_required_and_guardrail_must_be_t1():
    with pytest.raises(ValueError, match="as_of"):
        require_as_of({"id": "q1", "query": "x"})
    with pytest.raises(ValueError, match="护栏"):
        require_as_of({"id": "g", "as_of": "T0", "score_role": "guardrail"})
    assert require_as_of({"id": "ok", "as_of": "T1"}) == "T1"


def test_r10_unchanged_if_conflict_pair_field_stripped(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    with_pair = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "a",
        embed_fn=_fake_embed_match_first,
    )
    raw = json.loads(qpath.read_text(encoding="utf-8"))
    for item in raw["queries"]:
        item.pop("conflict_pair", None)
    q2 = tmp_path / "questions-nopair.json"
    q2.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    without = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=q2,
        config=cfg,
        dense_db=dense,
        cache_path=tmp_path / "cache2.sqlite",
        out_dir=tmp_path / "b",
        embed_fn=_fake_embed_match_first,
    )
    for mode in ("bm25", "dense", "hybrid"):
        assert (
            with_pair["main"]["buckets"]["总体"][mode]["R@10"]
            == without["main"]["buckets"]["总体"][mode]["R@10"]
        )
    assert with_pair["main"]["conflict_pair_n"] == 1
    assert without["main"]["conflict_pair_n"] == 0


def test_distractor_mean_skips_empty(tmp_path, monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.setattr("freshlatch.store.embeddings.embed_texts", _boom_embed)
    corpus, traps, qpath, cfg, dense, cache = _score_fixture(tmp_path)
    raw = json.loads(qpath.read_text(encoding="utf-8"))
    for item in raw["queries"]:
        if item["id"] == "arm-para":
            item["distractors"] = []
    qpath.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    payload = run_typed_compare(
        corpus=corpus,
        traps=traps,
        questions=qpath,
        config=cfg,
        dense_db=dense,
        cache_path=cache,
        out_dir=tmp_path / "out",
        embed_fn=_fake_embed_match_first,
    )
    bm25 = payload["main"]["buckets"]["总体"]["bm25"]
    assert bm25["distractor_n"] == 3
    assert bm25["distractor_hit@10"] == 1.0
