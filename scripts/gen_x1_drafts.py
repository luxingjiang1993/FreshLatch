"""生成 x1 文档/题目草稿，并用 qwen-plus 非思考抽检（RET-01.7）。

温度与 seed 只从配置读取；缺省或 JSON null 时拒绝，不落入 DecodingParams 的 temperature 0。
检查器退出码 2（阈值未写入）与 1（结构/许可）都打印，草稿仍写入 --out。
不把去污染阈值写进配置，也不把任何数字缺省传给检查器。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from freshlatch.eval.x1_checks import check_x1
from freshlatch.llm import DecodingParams, LLMClient

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
GOLD_PLACEHOLDER = "TODO-owner"
GOLD_QUESTION_KEYS = ("relevant", "answer_points", "distractors")
NOTE_FIELDS = ("id", "suspicion", "reason", "severity")


class DraftShapeError(ValueError):
    """模型草稿 JSON 形状非法，应写 raw-response 后非 0 退出。"""


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def _is_under(path: Path, root: Path) -> bool:
    target = _resolved(path)
    base = _resolved(root)
    if target == base:
        return True
    try:
        target.relative_to(base)
        return True
    except ValueError:
        return False


def _forbidden_resolved(resolved: Path) -> bool:
    """路径等于仓库根、禁写根、其后代，或禁写根的祖先，则禁止。"""
    if resolved == _resolved(ROOT) or resolved == _resolved(RETRIEVE_X1):
        return True
    for root in FORBIDDEN_OUT_ROOTS:
        r = _resolved(root)
        if _is_under(resolved, r) or _is_under(r, resolved):
            return True
    return False


def is_forbidden_out(path: Path) -> bool:
    """--out 不得等于仓库根、不得是禁写目录的祖先/自身/后代。"""
    return _forbidden_resolved(_resolved(path))


def is_forbidden_sidecar(path: Path) -> bool:
    """sidecar 沿用 --out 的禁写规则，并拒绝落在禁写祖先目录里的文件。"""
    resolved = _resolved(path)
    if _forbidden_resolved(resolved):
        return True
    return _forbidden_resolved(resolved.parent)


def _is_script_sidecar(path: Path) -> bool:
    """已有文件必须带本脚本写入的标记，才允许覆盖。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and data.get(SIDECAR_MARKER) is True


def _can_write_sidecar(path: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_sidecar(path):
        return (
            "错误: --sidecar 不得写成 data/eval/retrieve_x1.json，"
            "也不得落在禁写目录或其祖先下"
        )
    if path.suffix.lower() != ".json":
        return "错误: --sidecar 必须以 .json 结尾"
    if path.exists():
        if path.is_dir():
            return "错误: --sidecar 已存在且是目录"
        if not _is_script_sidecar(path):
            return "错误: --sidecar 已存在且不是本脚本写入的抽检文件，拒绝覆盖"
    return None


def _can_overwrite_out(out: Path) -> str | None:
    """返回拒绝原因；None 表示可以写入。"""
    if is_forbidden_out(out):
        return (
            "错误: --out 不得为仓库根，不得位于 data/corpus、data/traps、data/eval、"
            "docs/evidence/hard-gold-arm、reports 之下，也不得是这些目录的祖先"
        )
    if out.exists() and out.is_file():
        return "错误: --out 已存在且不是目录"
    if out.exists() and out.is_dir() and any(out.iterdir()):
        if not (out / MARKER_NAME).is_file():
            return "错误: --out 已存在且非空，缺少本脚本写入的清单，拒绝覆盖"
    return None


def _load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _decoding_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_draft_decoding(cfg: dict[str, Any]) -> tuple[float, int] | str:
    """配置里 temperature / seed 任一为 null 或未传入则拒绝。"""
    if "draft_temperature" not in cfg or cfg.get("draft_temperature") is None:
        return "draft_temperature 为 null 或未传入，拒绝落到 DecodingParams 默认温度"
    if "draft_seed" not in cfg or cfg.get("draft_seed") is None:
        return "draft_seed 为 null 或未传入，拒绝落到 DecodingParams 默认"
    temp = cfg["draft_temperature"]
    seed = cfg["draft_seed"]
    if not _decoding_number(temp):
        return "draft_temperature 不是数字"
    if not isinstance(seed, int) or isinstance(seed, bool):
        return "draft_seed 不是整数"
    return float(temp), int(seed)


def _parse_json_content(text: str) -> Any:
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        fence = raw.rfind("```")
        if fence != -1:
            raw = raw[:fence]
        raw = raw.strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)


def _whitelist_notes(obj: Any) -> Any:
    """sidecar 只保留抽检备注字段，不落 gold。"""
    if isinstance(obj, list):
        return [_whitelist_notes(x) for x in obj]
    if isinstance(obj, dict):
        return {k: obj[k] for k in NOTE_FIELDS if k in obj}
    return obj


def _is_gold_key(key: str) -> bool:
    low = str(key).lower()
    if low.startswith("relevant"):
        return True
    return low in {"answer_points", "distractors"}


def _strip_nested_gold(obj: Any) -> Any:
    """去掉任意深度的金标键，避免非标准嵌套泄漏。"""
    if isinstance(obj, dict):
        return {k: _strip_nested_gold(v) for k, v in obj.items() if not _is_gold_key(k)}
    if isinstance(obj, list):
        return [_strip_nested_gold(x) for x in obj]
    return obj


def _looks_like_question(obj: Any) -> bool:
    return isinstance(obj, dict) and ("id" in obj or "query" in obj)


def _as_question_list(value: Any) -> list[dict] | None:
    if isinstance(value, list):
        if all(isinstance(x, dict) for x in value):
            return value
        return None
    if _looks_like_question(value):
        return [value]
    return None


def _extract_questions(payload: Any) -> list[dict] | None:
    """把模型输出归一成题目对象列表；无法识别则返回 None。"""
    if isinstance(payload, list):
        return _as_question_list(payload)
    if not isinstance(payload, dict):
        return None
    if "queries" in payload:
        return _as_question_list(payload.get("queries"))
    q = payload.get("questions")
    if isinstance(q, dict) and "queries" in q:
        return _as_question_list(q.get("queries"))
    extracted = _as_question_list(q) if q is not None else None
    if extracted is not None:
        return extracted
    if _looks_like_question(payload) and "documents" not in payload:
        return [payload]
    if "documents" in payload and q is None:
        return []
    return None


def _normalize_question(item: dict[str, Any]) -> dict[str, Any]:
    cleaned = _strip_nested_gold(item)
    if not isinstance(cleaned, dict):
        cleaned = {}
    for key in GOLD_QUESTION_KEYS:
        cleaned[key] = GOLD_PLACEHOLDER
    return cleaned


def _normalize_documents(documents: Any) -> list[dict[str, str]]:
    if documents is None:
        return []
    if not isinstance(documents, list):
        raise DraftShapeError("documents 必须是列表")
    out: list[dict[str, str]] = []
    for i, item in enumerate(documents):
        if not isinstance(item, dict):
            raise DraftShapeError(f"documents[{i}] 必须是对象")
        if "path" not in item:
            raise DraftShapeError(f"documents[{i}] 缺少 path")
        raw_path = item["path"]
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise DraftShapeError(f"documents[{i}] path 必须是非空字符串")
        rel = Path(raw_path)
        if rel.is_absolute() or ".." in rel.parts:
            raise DraftShapeError(f"documents[{i}] 路径非法: {raw_path}")
        content = item.get("content", "")
        if content is None:
            content = ""
        if not isinstance(content, str):
            raise DraftShapeError(f"documents[{i}] content 必须是字符串")
        out.append({"path": raw_path, "content": content})
    return out


def _normalize_generate_payload(payload: Any) -> dict[str, Any]:
    questions = _extract_questions(payload)
    if questions is None:
        raise DraftShapeError("无法从模型输出解析题目列表")
    if isinstance(payload, dict):
        documents = _normalize_documents(payload.get("documents"))
    else:
        documents = []
    normalized_qs = [_normalize_question(q) if isinstance(q, dict) else {} for q in questions]
    return {
        "documents": documents,
        "questions": {"queries": normalized_qs},
    }


def _materialize_drafts(payload: dict[str, Any], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    corpus = dest / "corpus"
    traps = dest / "traps"
    traps.mkdir(parents=True, exist_ok=True)
    for item in payload["documents"]:
        rel = Path(item["path"])
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
    qpath = dest / "questions.json"
    qpath.write_text(
        json.dumps(payload["questions"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not corpus.exists():
        corpus.mkdir(parents=True, exist_ok=True)
    return qpath


def _print_checker(result) -> None:
    print(result.format_report(), end="")
    print(f"checker_exit={result.exit_code}")


def _token_usage_dict(client: Any) -> dict[str, Any]:
    usage = getattr(client, "token_usage", None)
    to_dict = getattr(usage, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    return {}


def _write_manifest(dest: Path, fields: dict[str, Any]) -> None:
    (dest / MARKER_NAME).write_text(
        json.dumps(fields, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _replace_out(staging: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(staging, out)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gen_x1_drafts.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate", help="用 draft_model 生成文档与题目草稿")
    gen.add_argument("--config", required=True)
    gen.add_argument("--out", required=True)
    flag = sub.add_parser("flag", help="用 qwen-plus 非思考标记疑点")
    flag.add_argument("--config", required=True)
    flag.add_argument("--in", dest="inp", required=True)
    flag.add_argument("--sidecar", required=True)
    return parser


class _NoThinkingCreate:
    """不改 llm.py：在 chat.completions.create 上钉死 enable_thinking=False。"""

    def __init__(self, orig: Any) -> None:
        self._orig = orig
        self.last_kwargs: dict[str, Any] | None = None

    def __call__(self, **kwargs: Any) -> Any:
        extra = dict(kwargs.get("extra_body") or {})
        extra["enable_thinking"] = False
        kwargs["extra_body"] = extra
        self.last_kwargs = kwargs
        return self._orig(**kwargs)


def _pin_flag_thinking_off(llm: Any) -> None:
    inner = getattr(llm, "client", None)
    if inner is None:
        return
    completions = inner.chat.completions
    completions.create = _NoThinkingCreate(completions.create)


def _write_failure_out(
    out: Path,
    raw_text: str,
    *,
    model: str,
    temperature: float,
    seed: int,
    recorded_at: str,
    token_usage: dict[str, Any],
    error: str,
) -> None:
    """失败路径也写清单，以便同一 --out 可以再次覆盖。"""
    if out.exists() and (out / MARKER_NAME).is_file():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw-response.txt").write_text(raw_text, encoding="utf-8")
    _write_manifest(
        out,
        {
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "recorded_at": recorded_at,
            "token_usage": token_usage,
            "checker_exit": None,
            "checker_error": error,
        },
    )


def _run_generate(args: argparse.Namespace, llm_client: Any) -> int:
    out = Path(args.out)
    deny = _can_overwrite_out(out)
    if deny:
        print(deny, file=sys.stderr)
        return 1
    cfg_path = Path(args.config)
    cfg = _load_config(cfg_path)
    decoded = _require_draft_decoding(cfg)
    if isinstance(decoded, str):
        print(f"错误: {decoded}", file=sys.stderr)
        return 1
    temperature, seed = decoded
    draft_model = cfg.get("draft_model")
    if draft_model != DRAFT_MODEL:
        print(f"错误: draft_model 必须为 {DRAFT_MODEL}", file=sys.stderr)
        return 1
    client = llm_client or LLMClient()
    decoding = DecodingParams(model=draft_model, temperature=temperature, seed=seed)
    message = client.chat(
        [
            {
                "role": "user",
                "content": (
                    "生成 x1 实验的文档与题目草稿 JSON。"
                    "只返回 JSON 对象：documents 数组，以及带 queries 数组的 questions 对象"
                    "（必须使用 queries 包装）。"
                    "每道题只给 id、query、category、eval_intent、as_of；金标由人终定。"
                ),
            }
        ],
        decoding=decoding,
    )
    raw_text = getattr(message, "content", "") or ""

    def _fail(error: str) -> int:
        _write_failure_out(
            out,
            raw_text,
            model=draft_model,
            temperature=temperature,
            seed=seed,
            recorded_at=decoding.recorded_at,
            token_usage=_token_usage_dict(client),
            error=error,
        )
        print(f"错误: {error}", file=sys.stderr)
        return 1

    try:
        payload = _parse_json_content(raw_text)
    except json.JSONDecodeError as exc:
        return _fail(f"模型输出不是 JSON: {exc}")
    try:
        payload = _normalize_generate_payload(payload)
    except DraftShapeError as exc:
        return _fail(str(exc))
    with tempfile.TemporaryDirectory(prefix="x1-drafts-") as tmp:
        staging = Path(tmp) / "bundle"
        qpath = _materialize_drafts(payload, staging)
        checker_exit: int | None = None
        checker_error: str | None = None
        try:
            result = check_x1(staging / "corpus", staging / "traps", qpath, cfg_path)
            _print_checker(result)
            checker_exit = result.exit_code
        except Exception as exc:
            checker_error = f"{type(exc).__name__}: {exc}"
            print(f"checker_error={checker_error}")
        _write_manifest(
            staging,
            {
                "model": draft_model,
                "temperature": temperature,
                "seed": seed,
                "recorded_at": decoding.recorded_at,
                "token_usage": _token_usage_dict(client),
                "checker_exit": checker_exit,
                "checker_error": checker_error,
            },
        )
        _replace_out(staging, out)
    return 0


def _load_flag_questions(inp: Path) -> list[dict[str, Any]]:
    if inp.is_dir():
        inp = inp / "questions.json"
    raw = json.loads(inp.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        qs = raw.get("queries", raw)
        if isinstance(qs, list):
            return list(qs)
        raise ValueError("抽检输入需要 queries 数组")
    if isinstance(raw, list):
        return list(raw)
    raise ValueError("抽检输入不是 JSON 数组或对象")


def _run_flag(args: argparse.Namespace, llm_client: Any) -> int:
    sidecar = Path(args.sidecar)
    deny = _can_write_sidecar(sidecar)
    if deny:
        print(deny, file=sys.stderr)
        return 1
    cfg = _load_config(Path(args.config))
    if cfg.get("flag_model") != FLAG_MODEL:
        print(f"错误: flag_model 必须为 {FLAG_MODEL}", file=sys.stderr)
        return 1
    if cfg.get("flag_thinking") is not False:
        print("错误: flag_thinking 必须为 false", file=sys.stderr)
        return 1
    questions = _load_flag_questions(Path(args.inp))
    slim = [{"id": q.get("id"), "query": q.get("query")} for q in questions]
    client = llm_client or LLMClient()
    _pin_flag_thinking_off(client)
    flag_temperature = 0.0
    decoding = DecodingParams(model=FLAG_MODEL, temperature=flag_temperature)
    message = client.chat(
        [
            {
                "role": "user",
                "content": (
                    "对下列题目草稿做非思考抽检，只标记疑点。"
                    "只输出 id、suspicion、reason、severity。"
                    + json.dumps(slim, ensure_ascii=False)
                ),
            }
        ],
        decoding=decoding,
    )
    try:
        notes = _parse_json_content(getattr(message, "content", "") or "")
    except json.JSONDecodeError:
        notes = {"suspicion": getattr(message, "content", "") or ""}
    notes = _whitelist_notes(notes)
    payload = {
        SIDECAR_MARKER: True,
        "model": FLAG_MODEL,
        "flag_thinking": False,
        "temperature": decoding.temperature,
        "notes": notes,
    }
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


def main(argv: list[str] | None = None, llm_client: Any = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 1
        return int(code)
    if args.cmd == "generate":
        return _run_generate(args, llm_client)
    if args.cmd == "flag":
        return _run_flag(args, llm_client)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
