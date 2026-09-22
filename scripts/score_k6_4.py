# -*- coding: utf-8 -*-
"""从 K6-4 报告 JSON 计算 c5/c6 fresh 恢复线。"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main(path: str) -> int:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    runs = raw["per_run"]
    c5 = sum(1 for r in runs if r["decisions"].get("c5") == "fresh")
    c6 = sum(1 for r in runs if r["decisions"].get("c6") == "fresh")
    n = len(runs)
    total = c5 + c6
    out = {
        "kind": "k6_4_score",
        "n": n,
        "temp": raw.get("decoding", {}).get("temperature"),
        "c5_fresh": c5,
        "c6_fresh": c6,
        "sum_fresh": total,
        "pass_line": "各>=2/3 且合计>=5/6",
        "c5_pass": c5 >= 2,
        "c6_pass": c6 >= 2,
        "sum_pass": total >= 5,
        "k6_4_pass": c5 >= 2 and c6 >= 2 and total >= 5,
        "per_run_c5_c6": [
            {"run": r["run"], "c5": r["decisions"].get("c5"), "c6": r["decisions"].get("c6")}
            for r in runs
        ],
        "must_stale_regression": {
            cid: sum(1 for r in runs if r["decisions"].get(cid) == "stale")
            for cid in ("c1", "c2", "c3", "c7")
        },
        "cite_template_if_pass": (
            "K6-4（n=3，temp=0）仅表明 c5/c6 两条在冒烟层达到各 ≥2/3 且合计 ≥5/6 fresh；"
            "三次均为 temp=0，不作为运行间噪声估计，不是统计测量，不是一期评测闭合，"
            "也不改写闸层可复现、K3 已锁未执行、或其他 must_fresh / must_unknown 未测部分。"
        ),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    Path(path).with_name("k6_4_score.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if out["k6_4_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
