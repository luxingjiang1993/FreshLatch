"""I1 #187: 从顾问垂直 v1-mck-soai 新跑并落可复跑轨迹(runnable=true 金样原料)。

层=答辩/冒烟。不改生产 Gate / disposition / HumanLatch / PRODUCTION_RETRIEVAL_MODE。
托管端点会漂移，跨会话复现只能近似。

用法(仓根):

  python3 scripts/i1_mck_runnable_gold.py \\
    --claim-id mck-1 \\
    --temperature 0.0 \\
    --out reports/i1-mck-runnable

  # 可选:仅灌 T0(演示「找不到」覆盖缺口;默认 T0+T1 全量)
  python3 scripts/i1_mck_runnable_gold.py \\
    --claim-id mck-1 --corpus-mode t0-only --out reports/i1-mck-runnable
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

from freshlatch.eval.matrix import EXPECTED_VERDICT  # noqa: E402
from freshlatch.llm import DecodingParams, LLMClient  # noqa: E402
from freshlatch.runner import Runner, load_docket  # noqa: E402
from freshlatch.store.ingest import ingest_into, load_corpus  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402

PACK_DIR = REPO / "data" / "packs" / "v1-mck-soai"
DEFAULT_GOLD = REPO / "docs" / "evidence" / "i1" / "mck-soai-gold.json"


def _expected(gold: dict, cid: str) -> str | None:
    for bucket, verdict in EXPECTED_VERDICT.items():
        if cid in gold.get(bucket, []):
            return verdict
    return None


def _ingest(store: SQLiteStore, corpus_root: Path, mode: str) -> int:
    """mode=full → t0+t1; mode=t0-only → 只灌 t0(覆盖缺口演示)。"""
    if mode == "full":
        return ingest_into(store, corpus_root)
    if mode != "t0-only":
        raise SystemExit(f"未知 corpus-mode: {mode}")
    # 只灌 T0:复用 load_corpus 后过滤,避免改 ingest 生产路径
    total = 0
    for doc, chunks in load_corpus(corpus_root):
        if doc.as_of != "T0":
            continue
        store.add_document(doc, chunks)
        total += len(chunks)
    return total


def main() -> None:
    ap = argparse.ArgumentParser(description="I1 McK SoAI runnable 金样跑数")
    ap.add_argument("--claim-id", default="mck-1")
    ap.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    ap.add_argument("--corpus-mode", choices=("full", "t0-only"), default="full")
    ap.add_argument("--model", default="qwen-flash")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=None,
                    help="temp=0 时 seed 无采样意义;默认 None")
    ap.add_argument("--out", type=Path, default=Path("reports/i1-mck-runnable"))
    args = ap.parse_args()

    gold = json.loads(args.gold.read_text(encoding="utf-8"))
    docket = load_docket(PACK_DIR / "docket.json")
    claims = [c for c in docket.claims if c.claim_id == args.claim_id]
    if not claims:
        raise SystemExit(f"卷宗无 claim_id={args.claim_id}")

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    db_path = out / "mck-run.sqlite"
    traj_dir = out / "trajectories"

    store = SQLiteStore(db_path)
    n_chunks = _ingest(store, PACK_DIR / "corpus", args.corpus_mode)

    run_date = datetime.now(timezone.utc).date().isoformat()
    decoding = DecodingParams(
        model=args.model,
        temperature=args.temperature,
        seed=args.seed,
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
    llm = LLMClient()
    runner = Runner(store, llm, mode="eval", decoding=decoding)
    result = runner.run(claims, trajectory_dir=traj_dir)

    claim = claims[0]
    expected = _expected(gold, claim.claim_id)
    machine = claim.status
    hit = expected is not None and machine == expected

    # 相对金标的漏拦/误拦(评测标签;非生产 status)
    err_kind = None
    if expected == "stale" and machine == "fresh":
        err_kind = "漏拦"
    elif expected == "fresh" and machine == "stale":
        err_kind = "误拦"
    elif expected == "stale" and machine not in ("stale",):
        # unknown/其它未收口为 stale → 该拦未拦
        err_kind = "漏拦"
    elif expected == "fresh" and machine not in ("fresh",):
        err_kind = "误拦" if machine == "stale" else None
    elif expected == "unknown" and machine == "fresh":
        err_kind = "漏拦"
    elif expected == "unknown" and machine == "stale":
        err_kind = "误拦"

    summary = {
        "kind": "i1_mck_runnable_gold",
        "layer": "答辩/冒烟",
        "pack_id": "v1-mck-soai",
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "corpus_mode": args.corpus_mode,
        "ingested_chunks": n_chunks,
        "gold_expected": expected,
        "machine_status": machine,
        "gold_hit": hit,
        "err_kind_vs_gold": err_kind,
        "reason": claim.reason,
        "t1_evidence_ids": list(claim.t1_evidence_ids),
        "decoding": {
            "model": decoding.model,
            "temperature": decoding.temperature,
            "seed": decoding.seed,
            "recorded_at": decoding.recorded_at,
            "date": run_date,
        },
        "trajectory_path": str(result.trajectory_path) if result.trajectory_path else None,
        "db_path": str(db_path),
        "repro_note": (
            "托管端点会漂移，跨会话复现只能近似。"
            "temp=0 时 seed 无采样意义。"
        ),
        "repro_command": (
            f"PYTHONPATH=src python3 scripts/i1_mck_runnable_gold.py "
            f"--claim-id {args.claim_id} --corpus-mode {args.corpus_mode} "
            f"--model {args.model} --temperature {args.temperature}"
            + (f" --seed {args.seed}" if args.seed is not None else "")
            + f" --out {out.as_posix()}"
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
