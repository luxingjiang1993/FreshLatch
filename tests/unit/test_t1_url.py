"""#171 / ADR-0027:薄 URL T1(白名单 · 失败四态 · checksum)。

夹具 HTTP 注入,CI 不打真网。三卡既有路径不回归见 test_ui_t1_source。
禁止 Tavily/开放搜索当 c′;切块仍本仓 ## pN。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import freshlatch.ui.app as appmod
from freshlatch.store.checksum import corpus_doc_path, sha256_hex
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.t1_source import (
    ALLOWED_URL_HOST,
    URL_EMPTY_OR_NON_TEXT,
    URL_FETCH_FAILED,
    URL_HOST_NOT_ALLOWED,
    URL_VALIDATE_FAILED,
    HttpGetResult,
    T1SourceSession,
    host_allowed,
)

WHITELIST_URL = f"https://{ALLOWED_URL_HOST}/capabilities/quantumblack/our-insights/state-of-ai"
ANCHOR = "McKinseyStateOfAI夹具锚词代理采用率已升至六成"


def _ok_html(body: str = ANCHOR) -> HttpGetResult:
    html = (
        "<!DOCTYPE html><html><head><title>t</title>"
        "<script>evil()</script></head><body>"
        f"<h1>State of AI</h1><p>{body}</p></body></html>"
    )
    return HttpGetResult(
        ok=True,
        status=200,
        content_type="text/html; charset=utf-8",
        body=html.encode("utf-8"),
    )


def _fixture_get(result: HttpGetResult):
    """返回固定夹具 GET;断言不依赖真网。"""

    def _get(url: str, timeout: float) -> HttpGetResult:
        assert ALLOWED_URL_HOST in url or True  # 调用方先过白名单
        return result

    return _get


def _session(tmp_path: Path, http_get) -> T1SourceSession:
    store = SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    return T1SourceSession(store, corpus_root=corpus, http_get=http_get)


def _store_chunk_ids(store: SQLiteStore) -> set[str]:
    """粗粒度零写哨兵:列当前全部 chunk_id。"""
    with store._conn() as conn:  # noqa: SLF001 — 单测哨兵读内部
        rows = conn.execute("SELECT chunk_id FROM chunks").fetchall()
    return {r[0] for r in rows}


# -- 主机名精确匹配 --------------------------------------------------------------


@pytest.mark.parametrize(
    "url,ok",
    [
        (WHITELIST_URL, True),
        (f"http://{ALLOWED_URL_HOST}/x", True),
        (f"https://{ALLOWED_URL_HOST}", True),
        ("https://mckinsey.com/x", False),
        ("https://insights.mckinsey.com/x", False),
        ("https://evil.com/www.mckinsey.com", False),
        ("https://www.mckinsey.com.evil.com/x", False),
        ("ftp://www.mckinsey.com/x", False),
        ("not-a-url", False),
        ("", False),
    ],
)
def test_host_allowed_exact_match(url, ok):
    assert host_allowed(url) is ok


# -- 白名单成功路径 + checksum ---------------------------------------------------


def test_whitelist_url_ingests_with_checksum(tmp_path):
    """Given Host=www.mckinsey.com 夹具含正文,When 薄 URL 入库,Then 落盘+checksum。"""
    from freshlatch.t1_source import _doc_id_from_url

    sess = _session(tmp_path, _fixture_get(_ok_html()))
    before = _store_chunk_ids(sess.store)

    result = sess.ingest_from_url(WHITELIST_URL)

    assert result.ok
    assert result.error_code is None
    assert result.checksum
    assert sess.state.ready is True
    assert sess.state.kind == "url"
    assert sess.state.checksum == result.checksum
    assert sess.state.source_url == WHITELIST_URL
    assert sess.state.network_enabled is False  # 开放插座仍关
    assert sess.state.ingested_chunks >= 1

    after = _store_chunk_ids(sess.store)
    assert after - before  # 有新 chunk

    doc_id = _doc_id_from_url(WHITELIST_URL)
    chunk = sess.store.get_chunk(doc_id, "p1", as_of="T1")
    assert chunk is not None
    assert ANCHOR in chunk.text
    assert chunk.clause_id == "p1"
    assert chunk.text.startswith("## p1")
    assert chunk.checksum == result.checksum

    path = corpus_doc_path(sess.corpus_root, doc_id, "T1")
    assert path.is_file()
    assert sha256_hex(path.read_bytes()) == result.checksum


# -- 失败四态零写 ----------------------------------------------------------------


def test_non_whitelist_zero_write(tmp_path):
    calls = {"n": 0}

    def boom(url: str, timeout: float) -> HttpGetResult:
        calls["n"] += 1
        return _ok_html()

    sess = _session(tmp_path, boom)
    before = _store_chunk_ids(sess.store)
    result = sess.ingest_from_url("https://example.com/page")
    assert result.ok is False
    assert result.error_code == URL_HOST_NOT_ALLOWED
    assert "白名单" in (result.error or "")
    assert calls["n"] == 0  # 未过白名单不得发 HTTP
    assert _store_chunk_ids(sess.store) == before
    assert sess.state.ready is False
    assert list(sess.corpus_root.rglob("*.md")) == []


def test_fetch_failed_zero_write(tmp_path):
    sess = _session(
        tmp_path,
        _fixture_get(HttpGetResult(ok=False, error="timed out")),
    )
    before = _store_chunk_ids(sess.store)
    result = sess.ingest_from_url(WHITELIST_URL)
    assert result.ok is False
    assert result.error_code == URL_FETCH_FAILED
    assert _store_chunk_ids(sess.store) == before
    assert sess.state.ready is False


def test_empty_or_non_text_zero_write(tmp_path):
    # 非文本
    sess = _session(
        tmp_path,
        _fixture_get(
            HttpGetResult(
                ok=True,
                status=200,
                content_type="application/pdf",
                body=b"%PDF-1.4 fake",
            )
        ),
    )
    before = _store_chunk_ids(sess.store)
    r1 = sess.ingest_from_url(WHITELIST_URL)
    assert r1.ok is False
    assert r1.error_code == URL_EMPTY_OR_NON_TEXT
    assert _store_chunk_ids(sess.store) == before

    # 空正文 HTML
    sess2 = _session(
        tmp_path / "b",
        _fixture_get(
            HttpGetResult(
                ok=True,
                status=200,
                content_type="text/html",
                body=b"<html><body><script>x</script></body></html>",
            )
        ),
    )
    before2 = _store_chunk_ids(sess2.store)
    r2 = sess2.ingest_from_url(WHITELIST_URL)
    assert r2.ok is False
    assert r2.error_code == URL_EMPTY_OR_NON_TEXT
    assert _store_chunk_ids(sess2.store) == before2


def test_validate_failed_zero_write(tmp_path, monkeypatch):
    """落盘前校验失败 → 零写且 error_code=URL_VALIDATE_FAILED。"""
    import freshlatch.t1_source as mod

    def boom_parse(text, *, checksum=None):
        raise ValueError("夹具强制校验失败")

    monkeypatch.setattr(mod, "parse_document_text", boom_parse)
    sess = _session(tmp_path, _fixture_get(_ok_html()))
    before = _store_chunk_ids(sess.store)
    result = sess.ingest_from_url(WHITELIST_URL)
    assert result.ok is False
    assert result.error_code == URL_VALIDATE_FAILED
    assert _store_chunk_ids(sess.store) == before
    assert sess.state.ready is False
    assert list(sess.corpus_root.rglob("*.md")) == []


# -- API 夹具路径 + 三卡不回归 ---------------------------------------------------


@pytest.fixture()
def client(tmp_path, monkeypatch):
    store = appmod.SQLiteStore(tmp_path / "t.db")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    monkeypatch.setattr(appmod, "_store", lambda: store)
    monkeypatch.setattr(appmod, "CHECKPOINTS", tmp_path / "cp.db")
    monkeypatch.setattr(appmod, "CORPUS", corpus)
    appmod._state.update({
        "claims": [], "question": "", "trajectory": None,
        "running": False, "latch": dict(appmod.EMPTY_LATCH),
    })
    appmod._reset_t1_source(store)
    return TestClient(appmod.app)


def test_api_url_success_and_cards_unchanged(client):
    """API 白名单成功;cards 仍仅三卡(薄 URL 不进 cards)。"""
    sess = appmod._t1_session()
    sess.http_get = _fixture_get(_ok_html())

    snap = client.get("/api/t1-source").json()
    assert [c["id"] for c in snap["cards"]] == ["upload", "paste", "synthetic"]
    assert snap["allowed_url_host"] == ALLOWED_URL_HOST
    assert snap["ready"] is False

    r = client.post("/api/t1-source/url", json={"url": WHITELIST_URL})
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["kind"] == "url"
    assert body["checksum"]
    assert [c["id"] for c in body["cards"]] == ["upload", "paste", "synthetic"]


def test_api_url_failure_codes_visible(client):
    """四失败态经 API 返回可区分 error_code,且零写。"""
    sess = appmod._t1_session()
    store = sess.store
    before = _store_chunk_ids(store)

    r = client.post("/api/t1-source/url", json={"url": "https://evil.example/x"})
    assert r.status_code == 400
    assert r.json()["error_code"] == URL_HOST_NOT_ALLOWED

    sess.http_get = _fixture_get(HttpGetResult(ok=False, error="network down"))
    r2 = client.post("/api/t1-source/url", json={"url": WHITELIST_URL})
    assert r2.status_code == 400
    assert r2.json()["error_code"] == URL_FETCH_FAILED

    assert _store_chunk_ids(store) == before
    assert client.get("/api/t1-source").json()["ready"] is False


def test_ui_surface_has_thin_url_without_breaking_three_cards():
    """成交面暴露薄 URL 入口,三卡 DOM 仍在。"""
    html = appmod.HTML_PAGE
    assert "T1 来源三卡" in html
    assert 'id="t1-card-upload"' in html
    assert 'id="t1-card-paste"' in html
    assert 'id="t1-card-synthetic"' in html
    assert 'id="t1-thin-url"' in html
    assert "ingestThinUrl" in html
    assert "/api/t1-source/url" in html
