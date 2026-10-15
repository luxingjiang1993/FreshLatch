"""L4-C-03: 检索前 ACL。tenant_id 由服务端注入,越权 fail-closed。零 LLM。"""

import ast
from pathlib import Path

import pytest

from freshlatch.models import Claim
from freshlatch.roles.critic import Critic
from freshlatch.roles.lead import LeadReverifier
from freshlatch.runner import RunContext
from freshlatch.store.base import (
    PRODUCTION_RETRIEVAL_MODE,
    Chunk,
    Document,
    InMemoryStore,
)
from freshlatch.store.tenant_acl import (
    REASON_TENANT_ACL_DENIED,
    TenantAclError,
    retrieve_for_session,
)
from freshlatch.store.sqlite_store import SQLiteStore
from freshlatch.tools import LEAD_TOOLS_W3, LEAD_TOOLS_W9

ROOT = Path(__file__).resolve().parents[2]


def _chunk(doc_id: str, tenant_id: str, text: str) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}::chunk-p1@T1",
        clause_id="p1",
        title=doc_id,
        text=text,
        source_type="private",
        as_of="T1",
        doc_version="1.0",
        checksum="c03",
        tokens=8,
        tenant_id=tenant_id,
    )


def _populate(store) -> None:
    specs = [
        ("tenant-a", "A", "aclmarker 租户A专属条款"),
        ("tenant-a-noise-1", "A", "noisea1 租户A其他条款"),
        ("tenant-a-noise-2", "A", "noisea2 租户A旁支条款"),
        ("tenant-b", "B", "aclmarker 租户B专属条款"),
        ("tenant-b-noise-1", "B", "noiseb1 租户B其他条款"),
        ("tenant-b-noise-2", "B", "noiseb2 租户B旁支条款"),
        ("filler-0", "default", "zzzfill0 无关条款 filleronly0"),
        ("filler-1", "default", "zzzfill1 无关条款 filleronly1"),
    ]
    for doc_id, tenant_id, text in specs:
        chunk = _chunk(doc_id, tenant_id, text)
        store.add_document(
            Document(
                doc_id=doc_id,
                as_of="T1",
                source_type="private",
                title=doc_id,
                doc_version="1.0",
                checksum="c03",
                full_text=text,
                tenant_id=tenant_id,
            ),
            [chunk],
        )


class _SpyStore(InMemoryStore):
    """记下 retrieve 是否被调用。ACL 拒绝时必须保持 0。"""

    def __init__(self) -> None:
        super().__init__()
        self.retrieve_calls = 0

    def retrieve(self, query, *, as_of=None, source_type=None, top_k=10,
                 tenant_id=None, patch_id=None, valid_at=None):
        self.retrieve_calls += 1
        return super().retrieve(
            query,
            as_of=as_of,
            source_type=source_type,
            top_k=top_k,
            tenant_id=tenant_id,
            patch_id=patch_id,
            valid_at=valid_at,
        )


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "memory":
        backed = InMemoryStore()
    else:
        backed = SQLiteStore(tmp_path / "c03.db")
    _populate(backed)
    return backed


def _lead(ctx: RunContext) -> LeadReverifier:
    claim = Claim(claim_id="c-acl", statement="aclmarker 共享预算")
    return LeadReverifier(ctx, claim, llm=None)


def test_tool_tenant_mismatch_rejects_and_hides_other_tenant(store):
    """会话 A 时,工具声明 B 被拒绝,B 的块不出现。"""
    ctx = RunContext(store=store, mode="online", server_tenant_id="A")
    denied = _lead(ctx)._t_retrieve({
        "query": "ignored",
        "as_of": "T1",
        "tenant_id": "B",
    })
    assert denied["fail_closed"] is True
    assert denied["reason_code"] == REASON_TENANT_ACL_DENIED
    assert "blocks" not in denied
    assert "租户B" not in denied["error"]
    assert ctx.retrieval_used == 0
    assert not any(event.get("type") == "retrieve" for event in ctx.events)
    assert ctx.events[-1]["type"] == "tenant_acl"
    assert ctx.events[-1]["server_tenant"] == "A"
    assert ctx.events[-1]["tool_tenant"] == "B"


def test_omitted_tool_tenant_uses_server_tenant_only(store):
    """工具不传 tenant 时注入会话 A,B 的块不在 hits。"""
    ctx = RunContext(store=store, mode="online", server_tenant_id="A")
    led = _lead(ctx)._t_retrieve({"query": "ignored", "as_of": "T1"})
    ids = {block["evidence_id"].split("#")[0] for block in led["blocks"]}
    assert "tenant-a" in ids
    assert "tenant-b" not in ids
    assert ctx.events[-1]["filters"]["tenant_id"] == "A"

    critic = Critic(ctx, Claim(claim_id="c-acl", statement="aclmarker 共享预算"), llm=None)
    crit = critic._t_retrieve({"query": "ignored", "as_of": "T1", "tenant_id": "  A  "})
    crit_ids = {block["evidence_id"].split("#")[0] for block in crit["blocks"]}
    assert crit_ids == ids
    assert "tenant-b" not in crit_ids


def test_missing_server_tenant_fail_closed_without_reading_corpus():
    """无服务端 tenant 时生产入口明确报错,且不读库。"""
    store = _SpyStore()
    _populate(store)
    store.retrieve_calls = 0
    ctx = RunContext(store=store, mode="online", server_tenant_id=None)
    denied = ctx.try_retrieve("aclmarker", as_of="T1", top_k=10, tenant_id="B")
    assert denied["fail_closed"] is True
    assert denied["reason_code"] == REASON_TENANT_ACL_DENIED
    assert "缺少服务端 tenant_id" in denied["error"]
    assert store.retrieve_calls == 0
    assert ctx.retrieval_used == 0

    blank = RunContext(store=store, mode="online", server_tenant_id="   ")
    blank_denied = _lead(blank)._t_retrieve({"query": "ignored", "as_of": "T1"})
    assert blank_denied["fail_closed"] is True
    assert store.retrieve_calls == 0

    with pytest.raises(TenantAclError) as raised:
        retrieve_for_session(store, "aclmarker", server_tenant_id=None, tool_tenant="A")
    assert raised.value.payload["fail_closed"] is True
    assert store.retrieve_calls == 0


def test_sqlite_where_scopes_tenant_before_python_filter(monkeypatch, tmp_path):
    """SQLite WHERE 按服务端 tenant 收窄。关掉 Python 过滤后异租户仍进不来。"""
    store = SQLiteStore(tmp_path / "where.db")
    _populate(store)

    def _keep_all(chunks, *, tenant_id):
        return list(chunks)

    monkeypatch.setattr("freshlatch.store.sqlite_store.filter_retrieve_pool", _keep_all)
    hits = store.retrieve("aclmarker", tenant_id="A", top_k=10)
    ids = {chunk.doc_id for chunk in hits}
    assert ids == {"tenant-a"}
    assert "tenant-b" not in ids


def test_no_vector_db_swap_and_default_tools_unchanged():
    """不换向量库,不把 web_search / LEAD_TOOLS_W9 变成默认。"""
    from freshlatch.tools import _TOOL_DEFS

    sqlite_src = (ROOT / "src/freshlatch/store/sqlite_store.py").read_text(encoding="utf-8")
    base_src = (ROOT / "src/freshlatch/store/base.py").read_text(encoding="utf-8")
    loop_src = (ROOT / "src/freshlatch/roles/loop.py").read_text(encoding="utf-8")
    folded = "\n".join([sqlite_src, base_src]).lower()
    assert "qdrant" not in folded
    assert "chroma" not in folded
    assert "faiss" not in folded
    assert "web_search" not in _TOOL_DEFS
    assert "web_search" not in LEAD_TOOLS_W3
    assert "web_search" not in LEAD_TOOLS_W9
    assert "list_memories" not in LEAD_TOOLS_W3
    assert "spawn_forensic" not in LEAD_TOOLS_W3
    assert LEAD_TOOLS_W9 != LEAD_TOOLS_W3
    imported: list[str] = []
    for node in ast.walk(ast.parse(loop_src)):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any("langgraph" in name for name in imported)
    mode_lines = [
        line.strip()
        for line in base_src.splitlines()
        if line.startswith("PRODUCTION_RETRIEVAL_MODE")
    ]
    assert mode_lines == ['PRODUCTION_RETRIEVAL_MODE = "hybrid+rerank"']
    assert PRODUCTION_RETRIEVAL_MODE == "hybrid+rerank"
