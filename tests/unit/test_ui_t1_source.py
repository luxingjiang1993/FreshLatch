"""DEM-2 / #89:T1 来源三卡 UI/API。挂复验单 UI 套件(TestClient + 源码红线)。

合法入口全集三卡;粘贴须确认入库;合成包标明 synthetic;未选定不得开复验;
联网插座默认关。不改 gold。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.tools import WEB_SEARCH_SOCKET_NOTE


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    # 粘贴/上传会落盘语料文件;必须指向临时树,禁止污染 data/corpus
    monkeypatch.setattr(appmod, "CORPUS", corpus)
    # 合成包仍用仓库真实语料(select_synthetic 需要 t1/)
    real_corpus = appmod.REPO_ROOT / "data" / "corpus"
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
    })
    appmod._reset_t1_source(store)
    # 合成卡单测单独换回真实路径
    client = TestClient(appmod.app)
    client.real_corpus = real_corpus  # type: ignore[attr-defined]
    client.tmp_corpus = corpus  # type: ignore[attr-defined]
    return client


# -- 源码/DOM 红线 ------------------------------------------------------------------


def test_t1_source_three_cards_surface_present():
    """DEM-2:复验前暴露且仅暴露 T1 来源三卡。"""
    html = appmod.HTML_PAGE
    assert "T1 来源三卡" in html
    assert 'id="t1-card-upload"' in html
    assert 'id="t1-card-paste"' in html
    assert 'id="t1-card-synthetic"' in html
    assert "确认入库" in html
    assert 'id="t1-paste-draft"' in html
    # 合成卡必须标明 synthetic
    assert "synthetic" in html.lower()
    # 联网默认关(插座文案在成交面可见)
    assert "联网" in html
    assert "默认关" in html or "默认关闭" in html


def test_network_socket_stays_off_whitelist():
    """联网插座若存在则默认关,不进角色白名单(本批主路径外)。"""
    assert "web_search" in WEB_SEARCH_SOCKET_NOTE
    from freshlatch import tools
    mounted = {t for wl in (tools.LEAD_TOOLS_W1, tools.LEAD_TOOLS_W3,
                            tools.CRITIC_TOOLS, tools.AUDITOR_TOOLS) for t in wl}
    assert "web_search" not in mounted
    assert "web_search" not in tools._TOOL_DEFS


# -- API 行为 ----------------------------------------------------------------------


def test_t1_source_starts_not_ready(client):
    """未选定合法来源 → ready=False。"""
    j = client.get("/api/t1-source").json()
    assert j["ready"] is False
    assert j["kind"] == "none"
    assert j["network_enabled"] is False
    ids = [c["id"] for c in j["cards"]]
    assert ids == ["upload", "paste", "synthetic"]


def test_reverify_blocked_without_t1_source(client):
    """未选定合法来源不得假装已有最新 T1(开始复验被拒)。"""
    client.post("/api/import")
    r = client.post("/api/reverify")
    assert r.status_code == 400
    assert "T1" in r.json()["error"]


def test_paste_draft_confirm_flow(client):
    """粘贴 → 草稿不可 retrieve;确认入库后 ready 且可 retrieve。"""
    store = appmod._store()
    # 垫两篇干扰块,避免 BM25 N≤2 IDF=0
    from freshlatch.store.base import Chunk, Document
    for i in (1, 2):
        text = f"## p1\n干扰{i}:监管口径旁证。"
        store.add_document(
            Document(doc_id=f"decoy-{i}", as_of="T1", source_type="private",
                     title=f"d{i}", doc_version="1.0", checksum="", full_text=text),
            [Chunk(doc_id=f"decoy-{i}", chunk_id=f"decoy-{i}::p1@T1", clause_id="p1",
                   title=f"d{i}", text=text, source_type="private", as_of="T1",
                   doc_version="1.0", checksum="", tokens=8)],
        )

    anchor = "UI三卡粘贴锚词SeaDesk降价"
    r = client.post("/api/t1-source/paste", json={"text": f"变更:{anchor}"})
    assert r.status_code == 200
    body = r.json()
    assert body["paste_status"] == "draft"
    assert body["ready"] is False
    assert store.get_chunk("paste-change", "p1", as_of="T1") is None

    r2 = client.post("/api/t1-source/confirm")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["paste_status"] == "confirmed"
    assert body2["ready"] is True
    assert store.get_chunk("paste-change", "p1", as_of="T1") is not None
    hits = store.retrieve("UI三卡粘贴锚词", as_of="T1")
    assert any(anchor in c.text for c in hits)


def test_synthetic_card_marks_synthetic_and_ready(client, monkeypatch):
    """选用内置合成评测包 → ready + synthetic 标明。"""
    # 合成包读真实 data/corpus;粘贴/上传仍用 fixture 临时树
    monkeypatch.setattr(appmod, "CORPUS", client.real_corpus)
    appmod._reset_t1_source(appmod._store())
    r = client.post("/api/t1-source/synthetic")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["kind"] == "synthetic"
    assert body["synthetic"] is True
    assert "synthetic" in body["message"].lower() or "合成" in body["message"]


def test_paste_confirm_writes_corpus_file(client):
    """确认粘贴后落盘 corpus/t1/{doc_id}.md,与 store checksum 同口径(档3b 牙齿)。"""
    from freshlatch.store.checksum import corpus_doc_path, sha256_hex

    r = client.post("/api/t1-source/paste", json={"text": "变更:落盘锚词"})
    assert r.status_code == 200
    assert client.post("/api/t1-source/confirm").status_code == 200
    path = corpus_doc_path(client.tmp_corpus, "paste-change", "T1")
    assert path.is_file()
    chunk = appmod._store().get_chunk("paste-change", "p1", as_of="T1")
    assert chunk is not None
    assert chunk.checksum == sha256_hex(path.read_bytes())


def test_upload_writes_corpus_file(client):
    """上传入库后落盘语料文件,供 make_checksum_fn 现算。"""
    from freshlatch.store.checksum import corpus_doc_path, sha256_hex

    md = (
        "---\n"
        "doc_id: upload-demo\n"
        "as_of: T1\n"
        "source_type: private\n"
        "title: 上传样例\n"
        "checksum:\n"
        "---\n"
        "## p1\n"
        "上传路径锚词:客户侧定价已变。\n"
    )
    r = client.post(
        "/api/t1-source/upload",
        files=[("files", ("upload-demo.md", md.encode("utf-8"), "text/markdown"))],
    )
    assert r.status_code == 200
    path = corpus_doc_path(client.tmp_corpus, "upload-demo", "T1")
    assert path.is_file()
    chunk = appmod._store().get_chunk("upload-demo", "p1", as_of="T1")
    assert chunk is not None
    assert chunk.checksum == sha256_hex(path.read_bytes())


def test_upload_rejects_non_t1_without_dirty_write(client):
    """上传含非 T1 文件时整批拒绝,不得留下已解析的脏 chunk。"""
    good = (
        "---\n"
        "doc_id: upload-good\n"
        "as_of: T1\n"
        "source_type: private\n"
        "title: 好文件\n"
        "checksum:\n"
        "---\n"
        "## p1\n"
        "好文件锚词。\n"
    )
    bad = (
        "---\n"
        "doc_id: upload-bad\n"
        "as_of: T0\n"
        "source_type: private\n"
        "title: 坏文件\n"
        "checksum:\n"
        "---\n"
        "## p1\n"
        "坏文件不应入库。\n"
    )
    r = client.post(
        "/api/t1-source/upload",
        files=[
            ("files", ("good.md", good.encode("utf-8"), "text/markdown")),
            ("files", ("bad.md", bad.encode("utf-8"), "text/markdown")),
        ],
    )
    assert r.status_code == 400
    assert "T1" in r.json()["error"]
    store = appmod._store()
    assert store.get_chunk("upload-good", "p1", as_of="T1") is None
    assert store.get_chunk("upload-bad", "p1", as_of="T0") is None
    assert client.get("/api/t1-source").json()["ready"] is False


def test_upload_rejects_non_utf8(client):
    """非 UTF-8 上传返回 400,不 500。"""
    r = client.post(
        "/api/t1-source/upload",
        files=[("files", ("bad.md", b"\xff\xfe\x00not-utf8", "text/markdown"))],
    )
    assert r.status_code == 400
    assert "UTF-8" in r.json()["error"]
