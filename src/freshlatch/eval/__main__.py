"""CLI:`python -m freshlatch.eval run|control|report`(§4.1)。

run --gold data/eval/gold.json [--runs N]   金标对账(LLM,手动/milestone 触发,不进 CI)
control                                      无工具假绿对照(判 alive = 假绿,对照成立)
report <raw.json>                            从 raw JSON 重渲染 markdown(不改判据,只重排版)

decoding 参数显式逐运行入档(§4.7);temp=0 时 seed 无采样意义,采样场景请显式非零温度。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from freshlatch.eval.control import run_control  # noqa: E402
from freshlatch.eval.report import console_summary, render_report, write_outputs  # noqa: E402
from freshlatch.eval.runner import run_gold  # noqa: E402
from freshlatch.llm import DecodingParams  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def _decoding(args: argparse.Namespace) -> DecodingParams:
    return DecodingParams(temperature=args.temperature,
                          seed=args.seed if args.seed is not None else None)


def main() -> None:
    ap = argparse.ArgumentParser(prog="freshlatch.eval", description="评测 harness(§4)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--gold", default="data/eval/gold.json")
        p.add_argument("--docket", default="data/t0_docket.json")
        p.add_argument("--db", default="data/freshlatch.db")
        p.add_argument("--temperature", type=float, default=0.0)
        p.add_argument("--seed", type=int, default=None)
        p.add_argument("--out", default="reports")

    p_run = sub.add_parser("run", help="金标对账(端到端真主链)")
    common(p_run)
    p_run.add_argument("--runs", type=int, default=1, help="每条主张跑 N 遍(§4.4,默认 1)")
    p_run.add_argument("--trajectory-dir", default="reports/trajectories")

    p_ctrl = sub.add_parser("control", help="无工具假绿对照")
    common(p_ctrl)

    p_rep = sub.add_parser("report", help="从 raw JSON 重渲染 markdown")
    p_rep.add_argument("raw_json")
    p_rep.add_argument("--out", default="reports")

    args = ap.parse_args()

    if args.cmd == "report":
        raw = json.loads(Path(args.raw_json).read_text(encoding="utf-8"))
        print(render_report(raw))
        return

    store = SQLiteStore(args.db)
    if args.cmd == "run":
        raw = run_gold(store, None, gold_path=args.gold, docket_path=args.docket,
                       runs=args.runs, decoding=_decoding(args),
                       trajectory_dir=args.trajectory_dir)
    else:  # control
        raw = run_control(store, None, gold_path=args.gold, docket_path=args.docket,
                          decoding=_decoding(args))
    print(console_summary(raw))
    md_path, json_path = write_outputs(raw, args.out)
    print(f"报告: {md_path}\n原始 JSON: {json_path}")


if __name__ == "__main__":
    main()
