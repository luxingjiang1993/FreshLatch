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

DRAFT_MODEL = "qwen-flash"
FLAG_MODEL = "qwen-plus"
GOLD_PLACEHOLDER = "TODO-owner"
GOLD_KEYS = ("relevant", "answer_points", "distractors")
NOTE_FIELDS = ("id", "suspicion", "reason", "severity")


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


def _scrub_question_gold(questions: Any) -> Any:
    """金标由人终定：草稿里的 relevant / answer_points / distractors 一律改成占位。"""
    if isinstance(questions, dict):
        qs = questions.get("queries", questions)
        if isinstance(qs, list):
            for item in qs:
                if isinstance(item, dict):
                    for key in GOLD_KEYS:
                        item[key] = GOLD_PLACEHOLDER
            if "queries" in questions:
                questions["queries"] = qs
            return questions
        return questions
    if isinstance(questions, list):
        for item in questions:
            if isinstance(item, dict):
                for key in GOLD_KEYS:
                    item[key] = GOLD_PLACEHOLDER
        return {"queries": questions}
    return {"queries": []}


def _materialize_drafts(payload: dict[str, Any], dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    corpus = dest / "corpus"
    traps = dest / "traps"
    traps.mkdir(parents=True, exist_ok=True)
    for item in payload.get("documents") or []:
        rel = Path(item["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"非法草稿路径: {rel}")
        target = dest / rel
        if is_forbidden_out(target):
            raise ValueError(f"草稿路径落在禁写目录: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item["content"], encoding="utf-8")
    questions = _scrub_question_gold(payload.get("questions") or {"queries": []})
    qpath = dest / "questions.json"
    qpath.write_text(
        json.dumps(questions, ensure_ascii=False, indent=2) + "\n",
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


def _write_raw_response(out: Path, text: str) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw-response.txt").write_text(text, encoding="utf-8")


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
                    "只返回 documents 与 questions。"
                    "题目只给 id、query、category、eval_intent、as_of；金标由人终定。"
                ),
            }
        ],
        decoding=decoding,
    )
    raw_text = getattr(message, "content", "") or ""
    try:
        payload = _parse_json_content(raw_text)
    except json.JSONDecodeError as exc:
        _write_raw_response(out, raw_text)
        print(f"错误: 模型输出不是 JSON: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        _write_raw_response(out, raw_text)
        print("错误: 模型输出不是 JSON 对象", file=sys.stderr)
        return 1
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
    if is_forbidden_sidecar(sidecar):
        print(
            "错误: --sidecar 不得写成 data/eval/retrieve_x1.json，"
            "也不得落在禁写目录或其祖先下",
            file=sys.stderr,
        )
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
