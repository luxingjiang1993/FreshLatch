"""正式 n=30 四臂入口。

默认不跑，退出 0，不发请求。
显式 ``--formal`` 时，用已合入的提示词正文向 ``DEFAULT_MODEL`` 发请求。
温度只读 ``default_llm.temperature``。补定，2026-10-08。不是预注册原文。
只发 C、T、B1 的 rewrite，以及 B2 的 claim。B2 的 diff 不发请求。
样本来自 ``SPLIT-pe-v2.json`` 的 n=30。不调用 ``load_formal_ids``，不读 pilot。
不跑消融，不调用自动核验。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import (
    HYBRID_COLUMN,
    ablation_interval_report,
    primary_comparison_rows,
    run_ablations,
)
from freshlatch.eval.patch_events_arms import ARMS, Decoding, run_arms
from freshlatch.eval.patch_events_construct import construct_samples
from freshlatch.eval.patch_events_metrics import (
    ABLATION_ORDER,
    N_BOOT,
    SEED,
    compare_primary,
    named_streams,
)
from freshlatch.evidence_id import parse_evidence_id
from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.eval.patch_events_send import dispatch_prompt, formal_requests, live_chat
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY

_PE_V2_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2.json")
_PE_V2_DOCKET = Path("data/pe_v2_docket.json")
_PE_V2_CORPUS = Path("data/corpus/pe_v2")
_FORMAL_N = 30

_GAP_TEMPERATURE = (
    "default_llm.temperature 不是 0。"
    "补定，2026-10-08。不是预注册原文。"
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")


def live_gaps() -> tuple[str, ...]:
    """温度或模型与登记不一致时，显式入口不得发请求。"""
    gaps = [] if callable(build_prompt) else ["正式生成器不可调用。"]
    entry = MODEL_REGISTRY["default_llm"]
    if entry.model != DEFAULT_MODEL or entry.temperature != 0:
        gaps.append(_GAP_TEMPERATURE)
    return tuple(gaps)


def load_pe_v2_formal_n30(root: Path | None = None) -> list[dict[str, Any]]:
    """只取 pe_v2 清单的正式 n=30，并按该清单的顺序带回构造记录。"""
    base = _repo_root() if root is None else Path(root)
    payload = json.loads((base / _PE_V2_SPLIT).read_text(encoding="utf-8"))
    ids = [str(row["claim_id"]) for row in payload["n30"]]
    if len(ids) != _FORMAL_N or len(set(ids)) != _FORMAL_N:
        raise RuntimeError("SPLIT-pe-v2.json 的 n=30 不是 30 条互异主张")
    pilot_ids = {str(row["claim_id"]) for row in payload["pilot"]}
    if set(ids) & pilot_ids:
        raise RuntimeError("正式 n=30 与 pilot 重叠")
    built = construct_samples(base / _PE_V2_DOCKET, base / _PE_V2_CORPUS)
    by_id = {str(row.record["claim_id"]): row.record for row in built.n30}
    missing = [claim_id for claim_id in ids if claim_id not in by_id]
    if missing:
        raise RuntimeError("正式 n=30 划分里的主张没有构造结果")
    return [dict(by_id[claim_id]) for claim_id in ids]


def ingested_t1(candidates: Sequence[Mapping[str, Any]]) -> set[str]:
    """候选证据里已经能解析成 T1 的 id。不另造入库规则。"""
    found: set[str] = set()
    for item in candidates:
        evidence_id = str(item["evidence_id"])
        parsed = parse_evidence_id(evidence_id)
        if parsed is None:
            continue
        _doc_id, _anchor, as_of = parsed
        if as_of == "T1":
            found.add(evidence_id)
    return found


def run_formal(
    candidates: Sequence[object],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1_ids: set[str] | None = None,
) -> dict[str, Any]:
    """先四臂并做三条主比较，再只对 T 做消融。hybrid+rerank 留在消融结果里，不进主比较。"""
    rows = list(candidates)
    ingested = ingested_t1(rows) if ingested_t1_ids is None else set(ingested_t1_ids)
    arms = run_arms(
        rows,
        generator=generator,
        verifier=verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )
    primary = compare_primary(
        primary_comparison_rows(arms),
        ingested_t1=ingested,
        streams=named_streams(),
    )
    ablations = run_ablations(
        rows,
        generator=generator,
        verifier=verifier,
        decoding=decoding,
        ingested_t1=ingested,
    )
    intervals = ablation_interval_report(
        arms["T"],
        ablations,
        ingested_t1=ingested,
        rng=random.Random(SEED),
    )
    return {
        "n": len(rows),
        "k": primary["k"],
        "n_boot": N_BOOT,
        "seed": SEED,
        "model": DEFAULT_MODEL,
        "arms": {arm: arms[arm] for arm in ARMS},
        "voids": arms["voids"],
        "ablations": {name: ablations[name] for name in (*ABLATION_ORDER, HYBRID_COLUMN)},
        "ablation_voids": ablations["voids"],
        "primary": primary,
        "ablation_intervals": intervals,
    }


def main(argv: list[str] | None = None) -> int:
    """默认关闭，退出 0，不发请求。显式 ``--formal`` 才发送已合入正文。"""
    _utf8_stdio()
    parser = argparse.ArgumentParser(prog="python -m freshlatch.eval.patch_events_formal")
    parser.add_argument("--formal", action="store_true")
    args = parser.parse_args(argv)
    if not args.formal:
        return 0
    gaps = live_gaps()
    if gaps:
        sys.stderr.write("\n".join(gaps) + "\n")
        return 2
    rows = load_pe_v2_formal_n30()
    for request in formal_requests(rows):
        dispatch_prompt(request, live_chat)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
