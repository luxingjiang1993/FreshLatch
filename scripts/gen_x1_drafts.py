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

DRAFT_MODEL = "qwen-flash"
FLAG_MODEL = "qwen-plus"

last_flag_requests: list[dict[str, Any]] = []


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


def is_forbidden_out(path: Path) -> bool:
    """--out 不得落在正式语料、题集、hard-gold 证据或 reports 下。"""
    if _resolved(path) == _resolved(RETRIEVE_X1):
        return True
    return any(_is_under(path, root) for root in FORBIDDEN_OUT_ROOTS)


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


def _drop_relevant(obj: Any) -> Any:
    """sidecar 不得带上 relevant，即使模型回了也不落盘。"""
    if isinstance(obj, dict):
        return {k: _drop_relevant(v) for k, v in obj.items() if k != "relevant"}
    if isinstance(obj, list):
        return [_drop_relevant(x) for x in obj]
    return obj


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
    questions = payload.get("questions") or {"queries": []}
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


def _run_generate(args: argparse.Namespace, llm_client: Any) -> int:
    out = Path(args.out)
    if is_forbidden_out(out):
        print("错误: --out 不得位于 data/corpus、data/traps、data/eval、docs/evidence/hard-gold-arm、reports 之下", file=sys.stderr)
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
                    "只返回 documents 与 questions，不要把题目写成正式 gold 文件。"
                ),
            }
        ],
        decoding=decoding,
    )
    payload = _parse_json_content(getattr(message, "content", "") or "")
    if not isinstance(payload, dict):
        print("错误: 模型输出不是 JSON 对象", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="x1-drafts-") as tmp:
        staging = Path(tmp) / "bundle"
        qpath = _materialize_drafts(payload, staging)
        result = check_x1(staging / "corpus", staging / "traps", qpath, cfg_path)
        _print_checker(result)
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(staging, out)
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
    global last_flag_requests
    last_flag_requests = []
    sidecar = Path(args.sidecar)
    if _resolved(sidecar) == _resolved(RETRIEVE_X1):
        print("错误: 抽检 sidecar 不得写成 data/eval/retrieve_x1.json", file=sys.stderr)
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
    decoding = DecodingParams(model=FLAG_MODEL)
    # 抽检不打开思考；DecodingParams 无该字段，只在请求记录里钉死关闭。
    last_flag_requests.append({"model": FLAG_MODEL, "thinking": False})
    message = client.chat(
        [
            {
                "role": "user",
                "content": (
                    "对下列题目草稿做非思考抽检，只标记疑点，不要改写 relevant，不要输出 gold。"
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
    notes = _drop_relevant(notes)
    payload = {
        "model": FLAG_MODEL,
        "flag_thinking": False,
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
