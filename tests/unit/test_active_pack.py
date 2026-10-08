"""active_pack 主缝（Batch 4 #128–#130）。

验收层：迁移预锁。软 Port / FP 为 invariant；切包可见性为 demo；C4 为文档纪律。
禁止升格为「多垂类已 Port」「数据集已对外可用」「软 Port 过 = 产品已验证」。
草稿不等于已释放。推进 main ≠ 已释放。
本缝不含 LLM run_gold；若将来补跑须标 smoke，并记录模型、温度、日期、n，不进 Port 通过线。
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sqlite3
from dataclasses import fields
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.models import Claim
from freshlatch.packs import (
    ENV_ACTIVE_PACK,
    KNOWN_PACK_IDS,
    P1_PACK_ID,
    DEFAULT_PACK_ID,
    PackPaths,
    PackResolveError,
    active_pack_id,
    open_pack_store,
    repo_root,
    resolve_pack,
)
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.tools import FOCUS_DIMENSIONS

# 第一课题 gold / 卷宗 / 语料字节锁（FP4）。改这些文件凑 P1 即本缝失败。
THESIS_GOLD_SHA256 = "28b8b88c41fb2a89794efe063de2948605f513ca10701cfc081c4ad144a939c2"
THESIS_DOCKET_SHA256 = "b60325812bb9803f417093a5c82b9b4ddcfa2ddf7c1997f42be9ea2cebc5bcb4"
THESIS_CORPUS_SHA256 = "d40becb48e8b80e9765302a15e9fa7bf84051bd0cc8e48f264434f5feed42d51"
THESIS_MUST = {
    "must_stale": ["c1", "c2", "c3", "c7"],
    "must_fresh": ["c4", "c5", "c6", "c8"],
    "must_unknown": ["c9", "c10", "c11", "c12"],
    "must_quarantine": [],
}
FOCUS_SIX = (
    "competitor_pricing",
    "regulatory_stance",
    "interview_reversal",
    "cost_model",
    "market_structure",
    "tech_ecosystem",
)
CLAIM_FIELDS = {
    "claim_id",
    "statement",
    "t0_evidence_ids",
    "t1_evidence_ids",
    "dimension",
    "status",
    "reason",
    "last_confirmed_at",
    "validity_basis",
    "voided",
    "voided_at",
    "dissent",
}
SQLITE_COLUMNS = {
    "documents": {
        "doc_id", "as_of", "source_type", "title", "doc_version", "checksum", "full_text",
        "tenant_id", "poison", "untrusted",
    },
    "chunks": {
        "doc_id", "chunk_id", "clause_id", "title", "text", "source_type", "as_of",
        "doc_version", "checksum", "tokens", "parent_id", "hypo_questions", "vec",
        "tenant_id", "poison", "untrusted",
    },
    "invalidation_list": {"claim_id", "voided_at", "actor", "reason"},
    "latch_log": {"ts", "claim_id", "action", "evidence_id", "actor", "machine_status_before", "override", "run_id", "reviewer_note"},
    "rerun_log": {"ts", "claim_id", "thread_id", "verdict", "nth", "note"},
    "long_term_memory": {
        "memory_id", "content", "written_at", "last_confirmed_at", "source_ref",
        "checksum", "status",
    },
    "memory_flags": {
        "id", "memory_id", "flag_type", "reason", "flagged_at", "evidence_ids",
    },
    "quarantine_proposals": {
        "id", "memory_ids", "reason", "proposed_at", "confirmed_at", "confirmed_by",
    },
}
C4_PATH = "docs/research/C4-合成数据释放协议草稿.md"
FORBIDDEN_UPGRADE = (
    "多垂类已 Port",
    "数据集已对外可用",
    "软 Port 过 = 产品已验证",
)


def _normalize_bytes(data: bytes) -> bytes:
    """字节锁按 LF 语义,避免 Windows autocrlf 工作区 CRLF 假红。"""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(_normalize_bytes(path.read_bytes())).hexdigest()


def _corpus_sha256(root: Path) -> str:
    """论文语料锁只覆盖 t0 与 t1。pe_v2 与论文树并列，不进入本摘要。"""
    digest = hashlib.sha256()
    paths: list[Path] = []
    for name in ("t0", "t1"):
        directory = root / name
        if directory.is_dir():
            paths.extend(directory.rglob("*.md"))
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(_normalize_bytes(path.read_bytes()))
        digest.update(b"\0")
    return digest.hexdigest()


def _claim_ids(gold: dict, docket: dict) -> set[str]:
    ids: set[str] = set()
    for key in (
        "must_stale", "must_fresh", "must_unknown",
        "must_quarantine", "must_fresh_distractor",
    ):
        ids.update(gold.get(key) or [])
    ids.update(c["claim_id"] for c in docket["claims"])
    return ids


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _restore_thesis_pack():
    yield
    appmod.bind_active_pack(DEFAULT_PACK_ID)
    appmod._state.update({
        "claims": [],
        "question": "",
        "trajectory": None,
        "running": False,
        "latch": dict(appmod.EMPTY_LATCH),
    })


def test_default_pack_matches_thesis_paths(monkeypatch):
    monkeypatch.delenv(ENV_ACTIVE_PACK, raising=False)
    assert active_pack_id() == DEFAULT_PACK_ID
    pack = resolve_pack()
    root = repo_root()
    assert pack.pack_id == DEFAULT_PACK_ID
    assert pack.corpus == root / "data" / "corpus"
    assert pack.docket == root / "data" / "t0_docket.json"
    assert pack.gold == root / "data" / "eval" / "gold.json"
    assert pack.sqlite == root / "data" / "freshlatch.db"
    assert pack.checkpoints == root / "data" / "checkpoints.db"
    assert pack.distractor_docket == root / "data" / "eval" / "distractor_docket.json"
    assert "东南亚" in pack.question


def test_known_packs_are_only_thesis_and_p1():
    assert KNOWN_PACK_IDS == (DEFAULT_PACK_ID, P1_PACK_ID)


def test_unknown_and_empty_pack_rejected(monkeypatch):
    with pytest.raises(PackResolveError):
        resolve_pack("p3-commitwatch")
    with pytest.raises(PackResolveError):
        resolve_pack("  ")
    monkeypatch.setenv(ENV_ACTIVE_PACK, "  ")
    with pytest.raises(PackResolveError):
        active_pack_id()


def test_env_switches_to_p1(monkeypatch):
    monkeypatch.setenv(ENV_ACTIVE_PACK, P1_PACK_ID)
    pack = resolve_pack()
    root = repo_root() / "data" / "packs" / P1_PACK_ID
    assert pack.pack_id == P1_PACK_ID
    assert pack.corpus == root / "corpus"
    assert pack.docket == root / "docket.json"
    assert pack.gold == root / "gold.json"
    assert pack.sqlite == root / "freshlatch.db"
    assert pack.sqlite != resolve_pack(DEFAULT_PACK_ID).sqlite
    assert pack.synthetic is True
    assert "转报" in pack.question


def test_eval_and_ingest_defaults_follow_pack(monkeypatch):
    monkeypatch.delenv(ENV_ACTIVE_PACK, raising=False)
    from freshlatch.eval.__main__ import build_parser

    pack = resolve_pack(DEFAULT_PACK_ID)
    args = build_parser(pack).parse_args(["run"])
    assert Path(args.gold) == pack.gold
    assert Path(args.docket) == pack.docket
    assert Path(args.db) == pack.sqlite
    assert Path(args.distractor_docket) == pack.distractor_docket

    monkeypatch.setenv(ENV_ACTIVE_PACK, P1_PACK_ID)
    p1 = resolve_pack()
    p1_args = build_parser().parse_args(["run"])
    assert Path(p1_args.gold) == p1.gold
    assert Path(p1_args.db) == p1.sqlite

    path = repo_root() / "scripts" / "ingest_corpus.py"
    spec = importlib.util.spec_from_file_location("ingest_corpus_active_pack", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ing = mod.build_parser().parse_args([])
    assert Path(ing.corpus) == p1.corpus
    assert Path(ing.db) == p1.sqlite


def test_loader_does_not_import_or_rewrite_gates(tmp_path):
    src_path = repo_root() / "src" / "freshlatch" / "packs.py"
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    banned = ("freshlatch.gates", "freshlatch.roles", "freshlatch.latch", "freshlatch.ui")
    for mod in modules:
        for prefix in banned:
            assert not mod.startswith(prefix), mod

    import freshlatch.gates.human_latch as human_latch
    import freshlatch.gates.rule_gate as rule_gate

    before = (rule_gate.rule_gate, human_latch.apply_decisions)
    pack = resolve_pack(P1_PACK_ID)
    alt = PackPaths(
        pack_id=pack.pack_id,
        label=pack.label,
        synthetic=pack.synthetic,
        question=pack.question,
        corpus=pack.corpus,
        docket=pack.docket,
        gold=pack.gold,
        sqlite=tmp_path / "p1.db",
        checkpoints=tmp_path / "cp.db",
        distractor_docket=pack.distractor_docket,
    )
    store = open_pack_store(alt)
    conn = sqlite3.connect(store.path)
    try:
        cols = {
            row[0]
            for row in conn.execute("PRAGMA table_info(documents)")
        }
    finally:
        conn.close()
    assert "pack_id" not in cols
    assert before == (rule_gate.rule_gate, human_latch.apply_decisions)


def test_sqlite_schema_columns_frozen_without_pack_id(tmp_path):
    store = SQLiteStore(tmp_path / "schema.db")
    conn = sqlite3.connect(store.path)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert set(SQLITE_COLUMNS) <= tables
        for table, expected in SQLITE_COLUMNS.items():
            got = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            assert got == expected
            assert "pack_id" not in got
    finally:
        conn.close()


def test_focus_and_claim_fields_frozen():
    assert FOCUS_DIMENSIONS == FOCUS_SIX
    assert len(FOCUS_DIMENSIONS) == 6
    assert {f.name for f in fields(Claim)} == CLAIM_FIELDS


def test_p1_gold_isomorphic_and_isolated():
    thesis = resolve_pack(DEFAULT_PACK_ID)
    p1 = resolve_pack(P1_PACK_ID)
    thesis_gold = _load(thesis.gold)
    p1_gold = _load(p1.gold)
    thesis_docket = _load(thesis.docket)
    p1_docket = _load(p1.docket)

    assert set(p1_gold) == set(thesis_gold)
    for key, ids in THESIS_MUST.items():
        assert thesis_gold[key] == ids
    assert len(p1_gold["must_stale"]) >= 1
    assert len(p1_gold["must_fresh"]) >= 1
    assert len(p1_gold["must_unknown"]) >= 1
    assert p1_gold["must_quarantine"] == []

    thesis_ids = _claim_ids(thesis_gold, thesis_docket)
    p1_ids = _claim_ids(p1_gold, p1_docket)
    assert thesis_ids.isdisjoint(p1_ids)
    assert thesis_ids
    assert all(cid.startswith("c") for cid in thesis_ids)
    assert all(cid.startswith("q") for cid in p1_ids)

    dims = {c["dimension"] for c in p1_docket["claims"]}
    assert dims <= set(FOCUS_DIMENSIONS)
    assert p1_docket["question"] == p1_gold["question"]
    assert "转报" in p1_gold["question"]

    for cid in p1_gold["must_stale"]:
        chain = p1_gold["causal_chain"][cid]
        assert chain["t1_doc"]
        assert chain["anchor"]
        t1 = p1.corpus / "t1" / f"{chain['t1_doc']}.md"
        text = t1.read_text(encoding="utf-8")
        assert f"## {chain['anchor']}" in text

    readme = p1.corpus.parent / "README.md"
    assert "synthetic" in readme.read_text(encoding="utf-8").lower()
    header = (p1.corpus / "t0" / "q1-supplier-quote.md").read_text(encoding="utf-8")
    assert "synthetic:" in header.split("---", 2)[1]


def test_thesis_gold_and_corpus_bytes_unchanged():
    root = repo_root()
    assert _sha256(root / "data" / "eval" / "gold.json") == THESIS_GOLD_SHA256
    assert _sha256(root / "data" / "t0_docket.json") == THESIS_DOCKET_SHA256
    assert _corpus_sha256(root / "data" / "corpus") == THESIS_CORPUS_SHA256


def test_no_field_engine_or_new_main_cta():
    src = repo_root() / "src"
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "reverify_field" not in text
    assert appmod.MAIN_BUTTON_TEXT == "开始复验"
    for marker in ("比价", "字段引擎", "自动通知"):
        assert marker not in appmod.HTML_PAGE


def test_default_pack_import_still_thesis(tmp_path, monkeypatch):
    monkeypatch.delenv(ENV_ACTIVE_PACK, raising=False)
    appmod.bind_active_pack(DEFAULT_PACK_ID)
    store = SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    client = TestClient(appmod.app)
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["imported"] == 12
    body = client.get("/api/claims").json()
    assert body["pack"]["pack_id"] == DEFAULT_PACK_ID
    assert body["pack"]["synthetic"] is True
    assert "东南亚" in body["question"]
    assert {c["claim_id"] for c in body["claims"]} >= {"c1", "c12"}


def test_p1_switch_visible_and_same_journey(tmp_path, monkeypatch):
    """demo：切包后问题句、包名、synthetic 可观察；导入与合成三卡仍是原旅程。"""
    appmod.bind_active_pack(P1_PACK_ID)
    store = SQLiteStore(tmp_path / "t.db")
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    appmod._reset_t1_source(store)
    client = TestClient(appmod.app)
    imported = client.post("/api/import")
    assert imported.status_code == 200
    assert imported.json()["imported"] == 3
    synthetic = client.post("/api/t1-source/synthetic")
    assert synthetic.status_code == 200
    snap = synthetic.json()
    assert snap["kind"] == "synthetic"
    assert snap["synthetic"] is True
    assert snap["ready"] is True
    assert snap["ingested_chunks"] >= 1
    body = client.get("/api/claims").json()
    assert body["pack"]["pack_id"] == P1_PACK_ID
    assert body["pack"]["label"]
    assert body["pack"]["synthetic"] is True
    assert "转报" in body["question"]
    assert "转报" in body["pack"]["question"]
    assert {c["claim_id"] for c in body["claims"]} == {"q1", "q2", "q3"}
    assert 'id="pack-badge"' in appmod.HTML_PAGE


def test_c4_acceptance_citation_and_no_upgrade():
    root = repo_root()
    assert (root / C4_PATH).is_file()
    text = (root / "docs" / "evidence" / "batch4" / "ACCEPTANCE.md").read_text(encoding="utf-8")
    assert C4_PATH in text
    assert "默认未释放" in text
    assert "推进 main ≠ 已释放" in text
    assert "禁止升格" in text
    for phrase in FORBIDDEN_UPGRADE:
        assert phrase in text
    assert "run_gold" in text
    assert "smoke" in text
