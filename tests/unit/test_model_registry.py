"""模型注册表：用途一行，字面量只留在 models.py。"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"

_LOG_ATTRS = frozenset(
    {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
)


def _offset_chars(source: str, lineno: int, col: int) -> int:
    """tokenize 的列是行内字符下标。"""
    lines = source.splitlines(keepends=True)
    return len("".join(lines[: lineno - 1])) + col


def _offset_utf8(source: str, lineno: int, byte_col: int) -> int:
    """ast 的列是行内 UTF-8 字节下标。"""
    lines = source.splitlines(keepends=True)
    prefix = "".join(lines[: lineno - 1])
    line = lines[lineno - 1]
    head = line.encode("utf-8")[:byte_col].decode("utf-8")
    return len(prefix) + len(head)


def _ast_span(source: str, node: ast.AST) -> tuple[int, int]:
    return (
        _offset_utf8(source, node.lineno, node.col_offset),
        _offset_utf8(source, node.end_lineno, node.end_col_offset),
    )


def _docstring_nodes(tree: ast.AST) -> list[ast.AST]:
    found: list[ast.AST] = []

    def consider(body: list[ast.stmt]) -> None:
        if not body or not isinstance(body[0], ast.Expr):
            return
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            found.append(value)
        elif isinstance(value, ast.JoinedStr):
            found.append(value)

    if isinstance(tree, ast.Module):
        consider(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            consider(node.body)
    return found


def _is_log_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name) and func.id == "print":
        return True
    return isinstance(func, ast.Attribute) and func.attr in _LOG_ATTRS


def _whitelist_spans(source: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    tree = ast.parse(source)
    for node in _docstring_nodes(tree):
        spans.append(_ast_span(source, node))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_log_call(node):
            continue
        args = list(node.args) + [kw.value for kw in node.keywords]
        for arg in args:
            for child in ast.walk(arg):
                if isinstance(child, ast.JoinedStr) or (
                    isinstance(child, ast.Constant) and isinstance(child.value, str)
                ):
                    spans.append(_ast_span(source, child))
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type != tokenize.COMMENT:
            continue
        start_line, start_col = tok.start
        end_line, end_col = tok.end
        spans.append(
            (_offset_chars(source, start_line, start_col), _offset_chars(source, end_line, end_col))
        )
    return spans


def mask_whitelisted(source: str) -> str:
    """抹掉注释、docstring、日志文案，其余源码保留。"""
    chars = list(source)
    for start, end in _whitelist_spans(source):
        for index in range(start, end):
            if chars[index] != "\n":
                chars[index] = " "
    return "".join(chars)


def model_name_hits(source: str, names: set[str]) -> list[str]:
    masked = mask_whitelisted(source)
    hits: list[str] = []
    for name in sorted(names, key=len, reverse=True):
        start = 0
        while True:
            index = masked.find(name, start)
            if index < 0:
                break
            line_no = masked.count("\n", 0, index) + 1
            hits.append(f"{line_no}: {name}")
            start = index + len(name)
    return hits


def registered_model_names() -> set[str]:
    from freshlatch.models import MODEL_REGISTRY

    names: set[str] = set()
    for entry in MODEL_REGISTRY.values():
        names.add(entry.model)
        names.update(entry.forbidden_models)
    return names


def test_scanner_keeps_code_literals_and_skips_whitelist():
    sample = (
        '"""中文 qwen-flash in docstring"""\n'
        "# 注释 qwen-flash\n"
        'logger.info("日志 qwen-flash")\n'
        'print("日志 qwen-plus")\n'
        'locked = "qwen-flash"\n'
    )
    hits = model_name_hits(sample, {"qwen-flash", "qwen-plus"})
    assert hits == ["5: qwen-flash"]


def test_registry_rows_and_aliases_keep_current_values():
    from freshlatch.eval.patch_events_judges import JUDGES
    from freshlatch.eval.x1_checks import LOCKED_CONFIG
    from freshlatch.eval.x1_drafts.constants import (
        DRAFT_MODEL,
        FLAG_MODEL,
        MODEL_MAX_OUTPUT_TOKENS,
    )
    from freshlatch.llm import DASHSCOPE_BASE_URL, DEFAULT_MODEL
    from freshlatch.models import MODEL_REGISTRY
    from freshlatch.store.embeddings import EMBED_MODEL, _ENDPOINT
    from freshlatch.store.local_embed import LOCAL_EMBED_MODEL
    from freshlatch.store.neural_rerank import NEURAL_RERANK_MODEL

    expected = {
        "default_llm": ("qwen-flash", "dashscope", DASHSCOPE_BASE_URL, "DASHSCOPE_API_KEY"),
        "embed": (
            "text-embedding-v4",
            "dashscope",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "DASHSCOPE_API_KEY",
        ),
        "local_embed": ("BAAI/bge-small-zh-v1.5", "fastembed", None, None),
        "neural_rerank": ("BAAI/bge-reranker-base", "fastembed", None, None),
        "x1_draft": (
            "qwen-flash",
            "dashscope",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "DASHSCOPE_API_KEY",
        ),
        "x1_flag": (
            "qwen-plus",
            "dashscope",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "DASHSCOPE_API_KEY",
        ),
        "judge_qwen": (
            "qwen3-235b-a22b-instruct-2507",
            "dashscope",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "DASHSCOPE_API_KEY",
        ),
        "judge_deepseek": (
            "deepseek-flash",
            "deepseek",
            "https://api.deepseek.com",
            "DEEPSEEK_API_KEY",
        ),
        "judge_kimi": (
            "kimi-k2.6",
            "moonshot",
            "https://api.moonshot.cn/v1",
            "MOONSHOT_API_KEY",
        ),
    }
    assert set(MODEL_REGISTRY) == set(expected)
    for purpose, (model, platform, base_url, env_key) in expected.items():
        entry = MODEL_REGISTRY[purpose]
        assert entry.purpose == purpose
        assert entry.model == model
        assert entry.platform == platform
        assert entry.base_url == base_url
        assert entry.env_key == env_key

    draft = MODEL_REGISTRY["x1_draft"]
    flag = MODEL_REGISTRY["x1_flag"]
    assert draft.max_output_tokens == 32768
    assert flag.max_output_tokens == 32768
    assert MODEL_MAX_OUTPUT_TOKENS == {"qwen-flash": 32768, "qwen-plus": 32768}
    assert DRAFT_MODEL == "qwen-flash"
    assert FLAG_MODEL == "qwen-plus"
    assert DEFAULT_MODEL == "qwen-flash"
    assert DASHSCOPE_BASE_URL == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert EMBED_MODEL == "text-embedding-v4"
    assert _ENDPOINT == "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
    assert LOCAL_EMBED_MODEL == "BAAI/bge-small-zh-v1.5"
    assert NEURAL_RERANK_MODEL == "BAAI/bge-reranker-base"
    assert LOCKED_CONFIG["embed_model"] == "text-embedding-v4"
    assert LOCKED_CONFIG["draft_model"] == "qwen-flash"
    assert LOCKED_CONFIG["flag_model"] == "qwen-plus"
    assert LOCKED_CONFIG["top_k"] == 10
    assert LOCKED_CONFIG["rrf_k"] == 60
    assert LOCKED_CONFIG["embed_dim"] == 1024
    assert LOCKED_CONFIG["flag_thinking"] is False
    assert LOCKED_CONFIG["lead_delta"] == 0.10
    assert LOCKED_CONFIG["budget_cny_max"] == 10

    qwen = JUDGES["qwen"]
    deepseek = JUDGES["deepseek"]
    kimi = JUDGES["kimi"]
    assert qwen.model == "qwen3-235b-a22b-instruct-2507"
    assert qwen.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert qwen.env_key == "DASHSCOPE_API_KEY"
    assert qwen.thinking is None
    assert qwen.forbidden_models == frozenset({"qwen-flash", "qwen-plus", "qwen-max"})
    assert deepseek.model == "deepseek-flash"
    assert deepseek.base_url == "https://api.deepseek.com"
    assert deepseek.env_key == "DEEPSEEK_API_KEY"
    assert deepseek.temperature == 0
    assert deepseek.thinking == {"type": "disabled"}
    assert deepseek.forbidden_models == frozenset(
        {
            "deepseek-ai/DeepSeek-V3",
            "deepseek-chat",
            "deepseek-reasoner",
            "deepseek-v4-pro",
        }
    )
    assert "deepseek-flash" not in deepseek.forbidden_models
    assert kimi.model == "kimi-k2.6"
    assert kimi.base_url == "https://api.moonshot.cn/v1"
    assert kimi.env_key == "MOONSHOT_API_KEY"
    assert kimi.temperature == 0.6
    assert kimi.thinking == {"type": "disabled"}
    assert kimi.forbidden_models == frozenset({"kimi-latest", "kimi-k3", "kimi-k2.7-code"})
    assert qwen.temperature == 0
    assert MODEL_REGISTRY["default_llm"].temperature is None
    assert MODEL_REGISTRY["judge_qwen"].forbidden_models == qwen.forbidden_models
    assert MODEL_REGISTRY["judge_deepseek"].forbidden_models == deepseek.forbidden_models
    assert MODEL_REGISTRY["judge_kimi"].forbidden_models == kimi.forbidden_models


def test_src_model_name_literals_only_in_registry():
    names = registered_model_names()
    assert "qwen-flash" in names
    assert "deepseek-flash" in names
    assert "deepseek-ai/DeepSeek-V3" in names
    offenders: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name == "models.py":
            continue
        hits = model_name_hits(path.read_text(encoding="utf-8"), names)
        offenders.extend(f"{path.relative_to(SRC.parent)}:{hit}" for hit in hits)
    assert offenders == []


def test_report_text_still_names_the_same_models():
    from freshlatch.eval.report import _decoding_block, _render_control
    from freshlatch.eval.runner import REPRO_NOTE

    block = _decoding_block(
        {
            "decoding": {"model": "qwen-flash", "temperature": 0.0, "seed": 1},
            "recorded_at": "2026-10-07T00:00:00+00:00",
        }
    )
    assert any("qwen-flash 是活托管端点" in line for line in block)
    control = _render_control(
        {
            "recorded_at": "2026-10-07T00:00:00+00:00",
            "redline_note": "n",
            "decoding": {"model": "qwen-flash", "temperature": 0.0, "seed": None},
            "results": {},
            "false_green_must_stale": [],
            "must_stale_total": 0,
            "blind_green_must_unknown": [],
            "control_pass": False,
        }
    )
    assert "同模型(qwen-flash)无工具" in control
    assert "qwen-flash 为活托管端点" in REPRO_NOTE
