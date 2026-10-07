"""草稿生成用的路径、模型名与预锁常量。"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]

FORBIDDEN_OUT_ROOTS = (
    ROOT / "data" / "corpus",
    ROOT / "data" / "traps",
    ROOT / "data" / "eval",
    ROOT / "docs" / "evidence" / "hard-gold-arm",
    ROOT / "reports",
)
RETRIEVE_X1 = ROOT / "data" / "eval" / "retrieve_x1.json"
MARKER_NAME = ".x1-drafts-manifest.json"
SIDECAR_MARKER = "x1_flag_sidecar"

DRAFT_MODEL = "qwen-flash"
FLAG_MODEL = "qwen-plus"
# qwen-flash / qwen-plus 最大输出 token。来源：help.aliyun.com/zh/model-studio/qwen-flash 与 qwen-plus，2026-10-06。
MODEL_MAX_OUTPUT_TOKENS = {
    "qwen-flash": 32768,
    "qwen-plus": 32768,
}
FLAG_LEDGER_NAME = ".x1-flag-spend.json"
CONSECUTIVE_VALIDATION_LIMIT = 3
GOLD_PLACEHOLDER = "TODO-owner"
GOLD_QUESTION_KEYS = ("relevant", "answer_points", "distractors", "qtype")
NOTE_FIELDS = ("id", "suspicion", "reason", "severity")
RAW_GOLD_NOTE = "raw-response.txt 可能含模型自拟金标，不得当标签使用"
BATCH_GENRES = frozenset({f"S{i}" for i in range(1, 8)})
BATCH_DOMAINS = frozenset({"D0", "D1", "D2", "D3"})
BATCH_AS_OF = frozenset({"T0", "T1"})
DOC_SOURCE_TYPES = frozenset({"private", "public", "internal"})
LICENSE_SYNTHETIC = "synthetic"
P2_MODEL_REFUSAL = "P2 由人按国家统计局公告手写，不由模型生成"
DECODING_MISMATCH = "解码参数与清单不一致"
FRONTMATTER_KEYS = (
    "doc_id",
    "as_of",
    "source_type",
    "title",
    "provenance",
    "license",
    "domain",
    "genre",
)
# 估 token 的口径：不调用模型。输入按 prompt 码位的两倍作上界；输出按块、题、文档开销。
EST_OUTPUT_TOKENS_PER_CHUNK = 256
EST_OUTPUT_TOKENS_PER_DOC = 128
EST_OUTPUT_TOKENS_PER_QUESTION = 128
PUBLIC_CORPUS = ROOT / "data" / "exp" / "x1" / "corpus"
PUBLIC_TRAPS = ROOT / "data" / "exp" / "x1" / "traps"
_BATCH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")
# p1 / p2 以及紧跟分隔符的前缀留给手写公开文档；p10、p21 不在此列。
_RESERVED_BATCH_RE = re.compile(r"(?i)^p[12](?:[-._]|$)")
_BLOCK_ID_RE = re.compile(r"^p\d+$")
# 只有「## 」一级标题是块边界；### 小节留在块正文里。
_H2_LINE_RE = re.compile(r"^##(?!#)[^\n]*", re.MULTILINE)
_NBS_MARKERS = ("统计局", "stats.gov.cn")
_DOC_BUCKETS = frozenset({"corpus", "traps"})
_DOC_SNAPSHOTS = frozenset({"t0", "t1"})
