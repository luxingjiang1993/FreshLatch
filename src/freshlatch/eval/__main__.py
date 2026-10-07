"""CLI:`python -m freshlatch.eval run|control|control-c|report`(§4.1)。

run --gold data/eval/gold.json [--runs N]   金标对账(LLM,手动/milestone 触发,不进 CI)
control                                      无工具假绿对照(旧仪器;判 alive = 假绿,对照成立)
control-c                                    假绿仪器 C(并行 CONTROL_PROMPT_C + 私有多锚)
report <raw.json>                            从 raw JSON 重渲染 markdown(不改判据,只重排版)

decoding 参数显式逐运行入档(§4.7);temp=0 时 seed 无采样意义,采样场景请显式非零温度。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from freshlatch.eval.control import run_control, run_control_c  # noqa: E402
from freshlatch.eval.report import console_summary, render_report, write_outputs  # noqa: E402
from freshlatch.eval.retrieve_eval import (  # noqa: E402
    run_arm_compare,
    run_hard_gold_retrieve,
    run_rerank_compare,
    run_retrieve_baseline,
    run_transform_compare,
    run_trap_eval,
)
from freshlatch.eval.runner import run_gold  # noqa: E402
from freshlatch.llm import DecodingParams  # noqa: E402
from freshlatch.packs import PackPaths, resolve_pack  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402


def _decoding(args: argparse.Namespace) -> DecodingParams:
    return DecodingParams(temperature=args.temperature,
                          seed=args.seed if args.seed is not None else None)


def build_parser(pack: PackPaths | None = None) -> argparse.ArgumentParser:
    """默认 gold/docket/db 走 active_pack,避免入口再硬编码第二套路径。"""
    pack = resolve_pack() if pack is None else pack
    ap = argparse.ArgumentParser(prog="freshlatch.eval", description="评测 harness(§4)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--gold", default=str(pack.gold))
        p.add_argument("--docket", default=str(pack.docket))
        p.add_argument("--db", default=str(pack.sqlite))
        p.add_argument("--temperature", type=float, default=0.0)
        p.add_argument("--seed", type=int, default=None)
        p.add_argument("--out", default="reports")

    p_run = sub.add_parser("run", help="金标对账(端到端真主链)")
    common(p_run)
    p_run.add_argument("--runs", type=int, default=1, help="每条主张跑 N 遍(§4.4,默认 1)")
    p_run.add_argument("--trajectory-dir", default="reports/trajectories")
    p_run.add_argument("--distractor-docket", default=str(pack.distractor_docket))

    p_ctrl = sub.add_parser("control", help="无工具假绿对照(旧仪器)")
    common(p_ctrl)
    p_ctrl.add_argument("--distractor-docket", default=str(pack.distractor_docket))

    p_ctrl_c = sub.add_parser("control-c", help="假绿仪器 C(并行 CONTROL_PROMPT_C)")
    common(p_ctrl_c)
    p_ctrl_c.add_argument("--distractor-docket", default=str(pack.distractor_docket))

    p_rep = sub.add_parser("report", help="从 raw JSON 重渲染 markdown")
    p_rep.add_argument("raw_json")
    p_rep.add_argument("--out", default="reports")

    p_ret = sub.add_parser("retrieve", help="BM25 retrieve 冒烟基线(无 LLM)")
    p_ret.add_argument("--corpus", default="data/corpus")
    p_ret.add_argument("--gold", default="data/eval/gold.json")
    p_ret.add_argument("--docket", default="data/t0_docket.json")
    p_ret.add_argument("--distractor-docket", default="data/eval/distractor_docket.json")
    p_ret.add_argument("--retrieve-gold", default="data/eval/retrieve_gold.json")
    p_ret.add_argument(
        "--hard",
        action="store_true",
        help="Hard-Gold 骨架集（data/eval/retrieve_hard_gold.json；不改臂）",
    )
    p_ret.add_argument("--out", default="reports")

    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.cmd == "report":
        raw = json.loads(Path(args.raw_json).read_text(encoding="utf-8"))
        print(render_report(raw))
        return

    if args.cmd == "retrieve":
        if getattr(args, "hard", False):
            hard_path = Path(args.retrieve_gold)
            if hard_path.name == "retrieve_gold.json" or not hard_path.is_file():
                hard_path = Path("data/eval/retrieve_hard_gold.json")
            hard = run_hard_gold_retrieve(
                corpus=Path(args.corpus),
                hard_gold_path=hard_path,
                out_dir=Path(args.out),
            )
            print(
                f"[Hard-Gold 骨架] n={hard['stats']['n']} "
                f"traps/对抗={hard['stats']['trap_adversarial_count']} "
                f"Recall@10={hard['metrics']['recall']['10']:.4f} "
                f"臂={hard['production_retrieval_mode']}"
            )
            print(f"报告: {hard['report_path']}")
            return
        try:
            payload = run_retrieve_baseline(
                corpus=Path(args.corpus),
                gold_path=Path(args.gold),
                docket_path=Path(args.docket),
                distractor_path=Path(args.distractor_docket),
                retrieve_gold_path=Path(args.retrieve_gold),
                out_dir=Path(args.out),
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            raise SystemExit(1) from exc
        if not payload["replay_pass"]:
            print("must_stale 回放 fail", file=sys.stderr)
            raise SystemExit(1)
        print(
            f"n={payload['metrics']['n']} Recall@10={payload['metrics']['recall']['10']:.4f} "
            f"MRR@10={payload['metrics']['mrr@10']:.4f} replay=pass"
        )
        print(f"报告: {payload['report_path']}")
        trap_gold = Path(args.retrieve_gold).parent / "retrieve_traps.json"
        trap_root = Path("data/traps")
        if trap_gold.is_file() and trap_root.is_dir():
            traps = run_trap_eval(
                trap_root=trap_root, trap_gold_path=trap_gold, out_dir=Path(args.out),
            )
            print(f"陷阱: {traps['report_path']}")
        compare = run_transform_compare(
            corpus=Path(args.corpus),
            docket_path=Path(args.docket),
            distractor_path=Path(args.distractor_docket),
            gold_path=Path(args.gold),
            out_dir=Path(args.out),
        )
        print(f"变换对比: {compare['report_path']}")
        dense_db = Path("data/dense/index.sqlite")
        if dense_db.is_file():
            arms = run_arm_compare(
                corpus=Path(args.corpus),
                retrieve_gold_path=Path(args.retrieve_gold),
                dense_db=dense_db,
                a0_baseline_path=Path(args.out) / "retrieve-bm25-baseline.json",
                out_dir=Path(args.out),
            )
            print(
                f"三列: {arms['report_path']} RRF k={arms['rrf_k']} "
                f"通过线={arms['verdict']}"
            )
            if not arms["pass"]:
                raise SystemExit(1)
            rerank = run_rerank_compare(
                corpus=Path(args.corpus),
                retrieve_gold_path=Path(args.retrieve_gold),
                dense_db=dense_db,
                out_dir=Path(args.out),
            )
            print(f"rerank: {rerank['report_path']} {rerank['sentence']}")
        return

    store = SQLiteStore(args.db)
    if args.cmd == "run":
        raw = run_gold(store, None, gold_path=args.gold, docket_path=args.docket,
                       runs=args.runs, decoding=_decoding(args),
                       trajectory_dir=args.trajectory_dir,
                       distractor_docket_path=args.distractor_docket)
    elif args.cmd == "control-c":
        raw = run_control_c(store, None, gold_path=args.gold, docket_path=args.docket,
                            decoding=_decoding(args),
                            distractor_docket_path=args.distractor_docket)
    else:  # control(旧仪器)
        raw = run_control(store, None, gold_path=args.gold, docket_path=args.docket,
                          decoding=_decoding(args),
                          distractor_docket_path=args.distractor_docket)
    print(console_summary(raw))
    md_path, json_path = write_outputs(raw, args.out)
    print(f"报告: {md_path}\n原始 JSON: {json_path}")


if __name__ == "__main__":
    main()
