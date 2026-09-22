"""T1 来源三卡状态机(ADR-0016 / DEM-2)。

三选一合法来源:
1. 上传 T1 语料包 → ingest 后可检索
2. 粘贴变更要点 → 先成草稿,人点「确认入库」后才 ingest;确认前对 retrieve / 续命不可见
3. 内置合成评测包 → 标明 synthetic

未选定不得假装已有最新 T1。联网插座默认关,不进本批主路径。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from freshlatch.store.base import Document, RetrievalStore
from freshlatch.store.ingest import ingest_into, parse_document_text, wrap_paste_as_t1_markdown

SourceKind = Literal["none", "upload", "paste", "synthetic"]
PasteStatus = Literal["none", "draft", "confirmed"]

DRAFT_DOC_ID = "paste-change"


@dataclass
class T1SourceState:
    """对外只读投影:UI/API 据此呈现三卡与就绪态。"""

    kind: SourceKind = "none"
    paste_status: PasteStatus = "none"
    paste_preview: str = ""  # 草稿可见文本摘要,不进 retrieve
    ready: bool = False
    synthetic: bool = False
    network_enabled: bool = False  # 插座默认关
    message: str = "未选定合法 T1 来源,不得假装已有最新事实"
    ingested_chunks: int = 0


@dataclass
class ActionResult:
    ok: bool
    error: str | None = None
    state: T1SourceState | None = None


@dataclass
class T1SourceSession:
    """会话级 T1 来源选择与粘贴草稿闸。

    草稿只住在本对象内存;确认前绝不 ``store.add_document``。
    """

    store: RetrievalStore
    corpus_root: Path | None = None
    draft_doc_id: str = DRAFT_DOC_ID
    _paste_text: str = field(default="", repr=False)
    _state: T1SourceState = field(default_factory=T1SourceState)

    @property
    def state(self) -> T1SourceState:
        return self._state

    def snapshot(self) -> dict:
        s = self._state
        return {
            "kind": s.kind,
            "paste_status": s.paste_status,
            "paste_preview": s.paste_preview,
            "ready": s.ready,
            "synthetic": s.synthetic,
            "network_enabled": s.network_enabled,
            "message": s.message,
            "ingested_chunks": s.ingested_chunks,
            "draft_doc_id": self.draft_doc_id,
            # DEM-2:合法入口全集仅此三卡
            "cards": [
                {"id": "upload", "label": "上传 T1 语料包", "synthetic": False},
                {"id": "paste", "label": "粘贴变更要点", "synthetic": False,
                 "requires_confirm": True},
                {"id": "synthetic", "label": "内置合成评测包", "synthetic": True},
            ],
        }

    def save_paste_draft(self, text: str) -> ActionResult:
        raw = (text or "").strip()
        if not raw:
            return ActionResult(ok=False, error="粘贴内容为空")
        self._paste_text = raw
        preview = raw if len(raw) <= 120 else raw[:117] + "..."
        self._state = T1SourceState(
            kind="paste",
            paste_status="draft",
            paste_preview=preview,
            ready=False,
            synthetic=False,
            network_enabled=False,
            message="粘贴草稿未确认入库:不可 retrieve、不可作续命证据",
            ingested_chunks=0,
        )
        return ActionResult(ok=True, state=self._state)

    def confirm_paste(self) -> ActionResult:
        if self._state.kind != "paste" or self._state.paste_status != "draft":
            return ActionResult(ok=False, error="无待确认的粘贴草稿")
        if not self._paste_text.strip():
            return ActionResult(ok=False, error="粘贴草稿为空")
        md = wrap_paste_as_t1_markdown(self._paste_text, doc_id=self.draft_doc_id)
        doc, chunks = parse_document_text(md)
        self.store.add_document(doc, chunks)
        self._state = T1SourceState(
            kind="paste",
            paste_status="confirmed",
            paste_preview=self._state.paste_preview,
            ready=True,
            synthetic=False,
            network_enabled=False,
            message="粘贴变更已确认入库,可作为 T1 检索与续命锚定",
            ingested_chunks=len(chunks),
        )
        return ActionResult(ok=True, state=self._state)

    def select_synthetic(self, corpus_root: Path | None = None) -> ActionResult:
        root = corpus_root or self.corpus_root
        if root is None:
            return ActionResult(ok=False, error="未配置合成评测包路径")
        if not (root / "t1").is_dir():
            return ActionResult(ok=False, error=f"合成评测包缺少 t1/: {root}")
        n = ingest_into(self.store, root)
        self._paste_text = ""
        self._state = T1SourceState(
            kind="synthetic",
            paste_status="none",
            paste_preview="",
            ready=True,
            synthetic=True,
            network_enabled=False,
            message="已选用内置合成评测包(synthetic)",
            ingested_chunks=n,
        )
        return ActionResult(ok=True, state=self._state)

    def ingest_upload_texts(self, files: list[tuple[str, str]]) -> ActionResult:
        """上传若干 markdown 文本:(filename, text) → 立即 ingest。

        仅接受 as_of=T1 的语料;无 frontmatter 时按粘贴包装为 T1 单篇。
        先全部解析/校验再一次性写入,避免中途失败留下脏 chunk。
        """
        if not files:
            return ActionResult(ok=False, error="未上传任何文件")
        parsed: list[tuple[Document, list]] = []
        for name, text in files:
            raw = (text or "").strip()
            if not raw:
                continue
            try:
                if raw.startswith("---"):
                    doc, chunks = parse_document_text(raw)
                else:
                    stem = Path(name).stem or "upload"
                    doc_id = f"upload-{stem}"
                    md = wrap_paste_as_t1_markdown(raw, doc_id=doc_id, title=stem)
                    doc, chunks = parse_document_text(md)
            except (KeyError, ValueError, AssertionError) as e:
                return ActionResult(ok=False, error=f"{name}:解析失败({e})")
            if doc.as_of != "T1":
                return ActionResult(
                    ok=False,
                    error=f"{name}:只接受 T1 语料包(as_of=T1),收到 as_of={doc.as_of}",
                )
            parsed.append((doc, chunks))
        if not parsed:
            return ActionResult(ok=False, error="上传文件无可入库内容")
        total = 0
        for doc, chunks in parsed:
            self.store.add_document(doc, chunks)
            total += len(chunks)
        self._paste_text = ""
        self._state = T1SourceState(
            kind="upload",
            paste_status="none",
            paste_preview="",
            ready=True,
            synthetic=False,
            network_enabled=False,
            message=f"已上传并入库 {total} 个 T1 chunk",
            ingested_chunks=total,
        )
        return ActionResult(ok=True, state=self._state)
