"""A-P4: 跨租户读 / 写 / 会话拒绝矩阵。身份只来自服务端映射。零付费 API。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.serving.acl import enforce_mapped_action
from freshlatch.serving.app import SERVING_KEYS_ENV, SERVING_TENANT_MISMATCH, SERVING_UNAUTHORIZED
from freshlatch.store.base import Chunk, Document, InMemoryStore
from freshlatch.store.tenant_acl import REASON_TENANT_ACL_DENIED

_REPO = Path(__file__).resolve().parents[2]
_SECURITY = _REPO / "docs" / "security.md"
_VICTIM = "aclmatrix-victim-b-only"
_OWNER = "aclmatrix-owner-a-clause"

# 每一行都是拒绝。client_tenant 单独出现,或与服务端映射不一致,都 fail-closed。
MATRIX = (
    {
        "case_id": "read-cross-tenant",
        "action": "read",
        "authorization": "Bearer key-a",
        "client_tenant": "tenant-b",
        "payload_tenant": None,
        "expect_code": SERVING_TENANT_MISMATCH,
        "expect_status": 403,
    },
    {
        "case_id": "write-cross-tenant",
        "action": "write",
        "authorization": "Bearer key-a",
        "client_tenant": "tenant-b",
        "payload_tenant": "tenant-b",
        "expect_code": SERVING_TENANT_MISMATCH,
        "expect_status": 403,
    },
    {
        "case_id": "write-payload-other-tenant",
        "action": "write",
        "authorization": "Bearer key-a",
        "client_tenant": "tenant-a",
        "payload_tenant": "tenant-b",
        "expect_code": REASON_TENANT_ACL_DENIED,
        "expect_status": None,
    },
    {
        "case_id": "session-cross-tenant",
        "action": "session",
        "authorization": "Bearer key-a",
        "client_tenant": "tenant-b",
        "payload_tenant": None,
        "expect_code": SERVING_TENANT_MISMATCH,
        "expect_status": 403,
    },
    {
        "case_id": "read-client-tenant-alone",
        "action": "read",
        "authorization": None,
        "client_tenant": "tenant-b",
        "payload_tenant": None,
        "expect_code": SERVING_UNAUTHORIZED,
        "expect_status": 401,
    },
    {
        "case_id": "write-client-tenant-alone",
        "action": "write",
        "authorization": None,
        "client_tenant": "tenant-b",
        "payload_tenant": "tenant-b",
        "expect_code": SERVING_UNAUTHORIZED,
        "expect_status": 401,
    },
    {
        "case_id": "session-client-tenant-alone",
        "action": "session",
        "authorization": None,
        "client_tenant": "tenant-b",
        "payload_tenant": None,
        "expect_code": SERVING_UNAUTHORIZED,
        "expect_status": 401,
    },
)


class _SpyStore(InMemoryStore):
    """ACL 拒绝时 retrieve 与 add_document 都必须保持 0。"""

    def __init__(self) -> None:
        super().__init__()
        self.retrieve_calls = 0
        self.write_calls = 0

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

    def add_document(self, doc, chunks) -> None:
        self.write_calls += 1
        super().add_document(doc, chunks)


def _pair(doc_id: str, tenant_id: str, text: str) -> tuple[Document, list[Chunk]]:
    doc = Document(
        doc_id=doc_id,
        as_of="T1",
        source_type="private",
        title=doc_id,
        doc_version="1.0",
        checksum="ap4",
        full_text=text,
        tenant_id=tenant_id,
    )
    chunk = Chunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}::chunk-p1@T1",
        clause_id="p1",
        title=doc_id,
        text=text,
        source_type="private",
        as_of="T1",
        doc_version="1.0",
        checksum="ap4",
        tokens=4,
        tenant_id=tenant_id,
    )
    return doc, [chunk]


def _seed(store: _SpyStore) -> None:
    for doc_id, tenant_id, text in (
        ("doc-tenant-a", "tenant-a", _OWNER),
        ("doc-tenant-b", "tenant-b", _VICTIM),
    ):
        doc, chunks = _pair(doc_id, tenant_id, text)
        InMemoryStore.add_document(store, doc, chunks)
    store.retrieve_calls = 0
    store.write_calls = 0


@pytest.fixture()
def store(monkeypatch):
    monkeypatch.setenv(SERVING_KEYS_ENV, "key-a=tenant-a,key-b=tenant-b")
    backed = _SpyStore()
    _seed(backed)
    return backed


def test_matrix_covers_read_write_session_and_client_tenant_alone():
    """矩阵至少覆盖读、写、会话;无凭证的客户端 tenant_id 三动作都在列。"""
    assert len(MATRIX) >= 3
    assert {row["action"] for row in MATRIX} >= {"read", "write", "session"}
    crossed = [
        row for row in MATRIX
        if row["authorization"] and row["client_tenant"] == "tenant-b"
    ]
    assert {row["action"] for row in crossed} >= {"read", "write", "session"}
    alone = [row for row in MATRIX if row["authorization"] is None]
    assert {row["action"] for row in alone} == {"read", "write", "session"}
    assert all(row["client_tenant"] == "tenant-b" for row in alone)


@pytest.mark.parametrize("case", MATRIX, ids=[row["case_id"] for row in MATRIX])
def test_cross_tenant_deny_matrix(case, store):
    """跨租户与仅客户端 tenant_id 都 fail-closed,且不读不写。"""
    document = None
    chunks = None
    if case["action"] == "write":
        document, chunks = _pair(
            "doc-write-attempt",
            case["payload_tenant"],
            _VICTIM,
        )
    before = [chunk.chunk_id for chunk in store._chunks]
    outcome = enforce_mapped_action(
        store,
        case["action"],
        authorization=case["authorization"],
        client_tenant=case["client_tenant"],
        query=_VICTIM,
        document=document,
        chunks=chunks,
    )
    assert outcome["ok"] is False
    assert outcome["fail_closed"] is True
    assert outcome["action"] == case["action"]
    assert outcome["code"] == case["expect_code"]
    assert "tenant_id" not in outcome
    if case["expect_status"] is not None:
        assert outcome["status_code"] == case["expect_status"]
    assert store.retrieve_calls == 0
    assert store.write_calls == 0
    assert [chunk.chunk_id for chunk in store._chunks] == before
    assert "doc-write-attempt" not in {chunk.doc_id for chunk in store._chunks}
    rendered = json.dumps(outcome, ensure_ascii=False)
    assert _VICTIM not in rendered
    assert _OWNER not in rendered


def test_acl_docs_scope_is_thin_not_full_saas():
    """范围句锁在安全文档。薄 ACL 不是完整 SaaS 多租户。"""
    text = _SECURITY.read_text(encoding="utf-8")
    assert "薄 ACL ≠ 完整 SaaS 多租户" in text
    assert "FRESHLATCH_SERVING_API_KEYS" in text
    assert "test_acl_cross_tenant_matrix.py" in text
