"""T1 来源三卡状态机(ADR-0016 / DEM-2)+ 薄 URL 增量(ADR-0027 / #171)。

三选一合法来源:
1. 上传 T1 语料包 → ingest 后可检索
2. 粘贴变更要点 → 先成草稿,人点「确认入库」后才 ingest;确认前对 retrieve / 续命不可见
3. 内置合成评测包 → 标明 synthetic

V1 增量「薄 URL」(c′):仅白名单主机名精确匹配 ``www.mckinsey.com`` 的单条 URL
→ GET → 抽取正文 → 本仓 ``## pN`` 切块 → ingest;落盘后有 checksum。
失败四态零写,可回落粘贴确认。禁止开放爬虫/Tavily 当 c′。

未选定不得假装已有最新 T1。联网插座默认关;薄 URL 是白名单单域缝,不是开放联网插座。
"""

from __future__ import annotations

import html as html_lib
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Literal

from freshlatch.store.base import Document, RetrievalStore
from freshlatch.store.checksum import write_corpus_doc
from freshlatch.store.ingest import ingest_into, parse_document_text, wrap_paste_as_t1_markdown

SourceKind = Literal["none", "upload", "paste", "synthetic", "url"]
PasteStatus = Literal["none", "draft", "confirmed"]

DRAFT_DOC_ID = "paste-change"

# 薄 URL 白名单:主机名精确匹配(ADR-0027);子域/裸域均拒绝
ALLOWED_URL_HOST = "www.mckinsey.com"
URL_FETCH_TIMEOUT_SEC = 15.0

# 失败四态 error_code(可区分;短中文走 ActionResult.error)
URL_HOST_NOT_ALLOWED = "URL_HOST_NOT_ALLOWED"
URL_FETCH_FAILED = "URL_FETCH_FAILED"
URL_EMPTY_OR_NON_TEXT = "URL_EMPTY_OR_NON_TEXT"
URL_VALIDATE_FAILED = "URL_VALIDATE_FAILED"

# text/* 与常见 HTML 视为可抽正文;其余 Content-Type 归「非文本」
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
    checksum: str = ""  # 薄 URL/落盘成功后可见;失败保持空
    source_url: str = ""  # 最近一次成功薄 URL;失败零写时清空


@dataclass
class ActionResult:
    ok: bool
    error: str | None = None
    error_code: str | None = None
    state: T1SourceState | None = None
    checksum: str | None = None


# 可注入的 HTTP GET:CI/单测用夹具,禁止默认打真网
HttpGetFn = Callable[[str, float], "HttpGetResult"]


@dataclass(frozen=True)
class HttpGetResult:
    """HTTP 抓取结果;网络层失败用 ok=False + error,不抛到业务层。"""

    ok: bool
    status: int = 0
    content_type: str = ""
    body: bytes = b""
    error: str | None = None


def default_http_get(url: str, timeout: float = URL_FETCH_TIMEOUT_SEC) -> HttpGetResult:
    """真网 GET(仅白名单校验通过后调用)。借鉴失败可见,禁止静默空入库。"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FreshLatch-ThinURL/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ctype = resp.headers.get_content_type() if hasattr(resp.headers, "get_content_type") else (
                (resp.headers.get("Content-Type") or "").split(";")[0].strip()
            )
            return HttpGetResult(
                ok=True,
                status=getattr(resp, "status", 200) or 200,
                content_type=ctype or "",
                body=raw,
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read() or b""
        except Exception:  # noqa: BLE001 — 读 body 失败仍归网络错
            body = b""
        ctype = ""
        if exc.headers is not None:
            ctype = (exc.headers.get("Content-Type") or "").split(";")[0].strip()
        # 4xx/5xx 仍视为抓取失败(非文本/空正文另判成功响应)
        return HttpGetResult(
            ok=False,
            status=int(exc.code),
            content_type=ctype,
            body=body,
            error=f"HTTP {exc.code}",
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HttpGetResult(ok=False, error=str(exc) or type(exc).__name__)


class _HtmlTextExtractor(HTMLParser):
    """极简 HTML→纯文本;去掉 script/style,保留可见文字。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in ("script", "style", "noscript"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip_depth:
            self._skip_depth -= 1
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "tr"):
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", " ".join(self._chunks)).strip()


def extract_plain_text(body: bytes, content_type: str) -> str | None:
    """从响应字节抽正文;非文本或解码失败返回 None(归空/非文本态)。"""
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype and not (
        ctype.startswith("text/")
        or ctype in ("application/xhtml+xml", "application/xml", "application/json")
        or "html" in ctype
    ):
        return None
    try:
        raw = body.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw = body.decode("latin-1")
        except UnicodeDecodeError:
            return None
    raw = raw.strip()
    if not raw:
        return None
    if "html" in ctype or raw.lstrip().lower().startswith("<!doctype") or "<html" in raw[:200].lower():
        parser = _HtmlTextExtractor()
        try:
            parser.feed(raw)
            parser.close()
        except Exception:  # noqa: BLE001 — 解析失败当非文本
            return None
        text = html_lib.unescape(parser.text()).strip()
        return text or None
    return raw


def host_allowed(url: str) -> bool:
    """主机名精确匹配白名单;拒绝子域/裸域/凭据伪装。"""
    try:
        parsed = urllib.parse.urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = (parsed.hostname or "").lower()
    return host == ALLOWED_URL_HOST


def _doc_id_from_url(url: str) -> str:
    """由 URL 路径派生稳定 doc_id;非法字符压成短横。"""
    parsed = urllib.parse.urlparse(url.strip())
    path = (parsed.path or "/").strip("/") or "index"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", path).strip("-").lower()
    if not slug:
        slug = "index"
    if len(slug) > 80:
        slug = slug[:80].rstrip("-")
    return f"url-mck-{slug}"


@dataclass
class T1SourceSession:
    """会话级 T1 来源选择与粘贴草稿闸。

    草稿只住在本对象内存;确认前绝不 ``store.add_document``。
    薄 URL 可通过 ``http_get`` 注入夹具,CI 不打真网。
    """

    store: RetrievalStore
    corpus_root: Path | None = None
    draft_doc_id: str = DRAFT_DOC_ID
    http_get: HttpGetFn = field(default=default_http_get)
    fetch_timeout: float = URL_FETCH_TIMEOUT_SEC
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
            "checksum": s.checksum,
            "source_url": s.source_url,
            "allowed_url_host": ALLOWED_URL_HOST,
            "draft_doc_id": self.draft_doc_id,
            # DEM-2:合法入口全集仍仅此三卡;薄 URL 是增量入口,不进 cards
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
        # 落盘语料文件:与 doc.checksum 同口径,供 make_checksum_fn / 档3b 跨轮腐烂现算
        if self.corpus_root is not None:
            write_corpus_doc(self.corpus_root, doc.doc_id, doc.as_of, doc.full_text)
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
            # 与粘贴同口径:上传也必须落盘,否则 checksum_fn 恒 None、腐烂假牙
            if self.corpus_root is not None:
                write_corpus_doc(self.corpus_root, doc.doc_id, doc.as_of, doc.full_text)
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

    def ingest_from_url(self, url: str) -> ActionResult:
        """薄 URL 入库(ADR-0027):白名单 Host → GET → 抽正文 → ## pN 切块 → 落盘。

        失败四态均零写(不 touch store / corpus_root),错误码可区分,可回落粘贴确认。
        ``http_get`` 可注入夹具:CI 不打真网。禁止 Tavily/开放搜索当 c′。
        """
        raw_url = (url or "").strip()
        if not raw_url or not host_allowed(raw_url):
            return ActionResult(
                ok=False,
                error_code=URL_HOST_NOT_ALLOWED,
                error=f"非白名单主机:仅允许精确匹配 {ALLOWED_URL_HOST}",
            )

        fetched = self.http_get(raw_url, self.fetch_timeout)
        if not fetched.ok or (fetched.status and fetched.status >= 400):
            return ActionResult(
                ok=False,
                error_code=URL_FETCH_FAILED,
                error=f"抓取失败:超时或网络错({fetched.error or fetched.status or 'unknown'})",
            )

        plain = extract_plain_text(fetched.body, fetched.content_type)
        if plain is None or not plain.strip():
            return ActionResult(
                ok=False,
                error_code=URL_EMPTY_OR_NON_TEXT,
                error="非文本或空正文:无法抽取可入库正文",
            )

        doc_id = _doc_id_from_url(raw_url)
        title = f"薄URL {ALLOWED_URL_HOST}"
        md = wrap_paste_as_t1_markdown(plain, doc_id=doc_id, title=title)
        try:
            doc, chunks = parse_document_text(md)
            if doc.as_of != "T1":
                raise ValueError(f"as_of 须为 T1,收到 {doc.as_of}")
            if not chunks:
                raise ValueError("切块结果为空")
            if not doc.checksum:
                raise ValueError("checksum 为空")
        except (KeyError, ValueError, AssertionError) as e:
            return ActionResult(
                ok=False,
                error_code=URL_VALIDATE_FAILED,
                error=f"落盘前校验失败:{e}",
            )

        # 校验通过后才写入:失败四态保证此前零写
        self.store.add_document(doc, chunks)
        if self.corpus_root is not None:
            write_corpus_doc(self.corpus_root, doc.doc_id, doc.as_of, doc.full_text)

        self._paste_text = ""
        self._state = T1SourceState(
            kind="url",
            paste_status="none",
            paste_preview="",
            ready=True,
            synthetic=False,
            network_enabled=False,  # 开放联网插座仍关;薄 URL ≠ 开放插座
            message=f"薄 URL 已入库({len(chunks)} chunk),checksum={doc.checksum[:12]}…",
            ingested_chunks=len(chunks),
            checksum=doc.checksum,
            source_url=raw_url,
        )
        return ActionResult(
            ok=True,
            state=self._state,
            checksum=doc.checksum,
        )
