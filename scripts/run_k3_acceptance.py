# -*- coding: utf-8 -*-
"""K3 统计层：seed 11/22/33 × 每 seed n=5，temp=0.7。逐 seed 落盘。"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "w5w8_acceptance" / "k3"
OUT.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env["PYTHONPATH"] = "src"
env["PYTHONIOENCODING"] = "utf-8"

seeds = [11, 22, 33]
summaries = []
for seed in seeds:
    seed_out = OUT / f"seed_{seed}"
    seed_out.mkdir(parents=True, exist_ok=True)
    traj = seed_out / "trajectories"
    console = OUT / f"seed_{seed}_console.txt"
    cmd = [
        sys.executable, "-m", "freshlatch.eval", "run",
        "--gold", "data/eval/gold.json",
        "--runs", "5",
        "--temperature", "0.7",
        "--seed", str(seed),
        "--out", str(seed_out),
        "--trajectory-dir", str(traj),
    ]
    print(f"=== K3 seed={seed} start ===", flush=True)
    with console.open("w", encoding="utf-8") as f:
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT, text=True)
    print(f"=== K3 seed={seed} exit={proc.returncode} ===", flush=True)
    # find newest report json in seed_out
    reports = sorted(seed_out.glob("report-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not reports:
        summaries.append({"seed": seed, "error": "no report", "exit": proc.returncode})
        continue
    raw = json.loads(reports[0].read_text(encoding="utf-8"))
    c2_stale = sum(1 for r in raw["per_run"] if r["decisions"].get("c2") == "stale")
    must_stale_fresh = 0
    for r in raw["per_run"]:
        for cid in ("c1", "c2", "c3", "c7"):
            if r["decisions"].get(cid) == "fresh":
                must_stale_fresh += 1
    summaries.append({
        "seed": seed,
        "report": str(reports[0]),
        "exit": proc.returncode,
        "c2_stale_of_5": c2_stale,
        "must_stale_fresh_count": must_stale_fresh,
        "pass_at_k": raw.get("pass_at_k"),
    })

# merge K3-2 metrics
c2_total = sum(s.get("c2_stale_of_5", 0) for s in summaries if "c2_stale_of_5" in s)
fresh_viol = sum(s.get("must_stale_fresh_count", 0) for s in summaries if "must_stale_fresh_count" in s)
merged = {
    "kind": "k3_aggregate",
    "spec": "temp=0.7, seed 11/22/33 × n=5",
    "c2_stale_of_15": c2_total,
    "c2_pass_line": ">=14/15",
    "c2_pass": c2_total >= 14,
    "must_stale_fresh_total": fresh_viol,
    "fresh_pass_line": "==0",
    "fresh_pass": fresh_viol == 0,
    "k3_2_pass": c2_total >= 14 and fresh_viol == 0,
    "per_seed": summaries,
    "cite_template_if_pass": (
        "K3（temp=0.7，seed 11/22/33，每 seed n=5）仅表明 c2 stale ≥14/15 "
        "且 must_stale 判 fresh 合计为 0，不是一期评测闭合，也不是 must_fresh 已愈，"
        "也不改写判定层冒烟未愈。"
    ),
}
(OUT / "k3_aggregate.json").write_text(
    json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(merged, ensure_ascii=False, indent=2), flush=True)
raise SystemExit(0 if merged["k3_2_pass"] else 2)
