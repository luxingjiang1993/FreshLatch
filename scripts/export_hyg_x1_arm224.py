"""导出 HYG-02 / HYG-03 的 x1 作答臂 224 题预锁表。

用法（仓根，先 editable 安装）::

    python scripts/export_hyg_x1_arm224.py

默认写到 ``docs/evidence/hygiene/x1-arm-224.json``。
只读现行语料与已入库 ``per-query.json``，不重新 embedding，不调用付费 API。
作答臂不是 224 题时退出码 2，不覆盖目标文件。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from freshlatch.eval.retrieve_eval import mrr_at_k, ndcg_at_k, recall_at_k
from freshlatch.eval.x1_checks import check_x1

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data" / "exp" / "x1" / "questions.json"
CORPUS = ROOT / "data" / "exp" / "x1" / "corpus"
TRAPS = ROOT / "data" / "exp" / "x1" / "traps"
CONFIG = ROOT / "data" / "exp" / "x1" / "config.json"
PER_QUERY = ROOT / "docs" / "evidence" / "fastembed-081-recheck" / "per-query.json"
OUT = ROOT / "docs" / "evidence" / "hygiene" / "x1-arm-224.json"

ARMS = ("bm25", "hybrid", "hybrid+rerank_lexical", "hybrid+rerank")
K = 10
EXPECTED_N = 224

_RECORD = re.compile(
    r"^q (?P<id>\S+) r8=(?P<r8>\S+) lcs=(?P<lcs>\S+) "
    r"lcs_flag=(?P<lcs_flag>\d+) decontam=(?P<decontam>\d+) "
    r"score_role=(?P<score_role>\S+)$"
)


def _question_messages(messages: list[str], qid: str) -> list[str]:
    prefix = f"{qid} "
    return sorted(msg for msg in messages if msg.startswith(prefix))


def build_table() -> dict:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    queries = questions["queries"] if isinstance(questions, dict) else questions
    arm = [q for q in queries if (q.get("score_role") or "arm") == "arm"]
    if len(arm) != EXPECTED_N:
        raise SystemExit(f"作答臂 n={len(arm)}，不是 {EXPECTED_N}")

    checked = check_x1(CORPUS, TRAPS, QUESTIONS, CONFIG)
    by_record: dict[str, re.Match[str]] = {}
    for line in checked.records:
        match = _RECORD.match(line)
        if match is None:
            raise SystemExit(f"无法解析 check_x1 记录: {line}")
        by_record[match.group("id")] = match

    per_rows = json.loads(PER_QUERY.read_text(encoding="utf-8"))
    per_by_id = {row["id"]: row for row in per_rows}
    if set(per_by_id) != {q["id"] for q in arm}:
        raise SystemExit("per-query 题号与作答臂不一致")

    exported = []
    for item in arm:
        qid = item["id"]
        match = by_record.get(qid)
        if match is None or match.group("score_role") != "arm":
            raise SystemExit(f"check_x1 缺少作答臂记录 {qid}")
        row = per_by_id[qid]
        relevant = list(row["relevant"])
        metrics = {}
        for mode in ARMS:
            ranked = list(row["ranked"][mode])
            metrics[mode] = {
                "mrr_at_10": mrr_at_k(ranked, relevant, K),
                "ndcg_at_10": ndcg_at_k(ranked, relevant, K),
                "recall_at_10": recall_at_k(ranked, relevant, K),
            }
        exported.append(
            {
                "decontam": int(match.group("decontam")),
                "id": qid,
                "lcs": match.group("lcs"),
                "lcs_flag": int(match.group("lcs_flag")),
                "messages": _question_messages(checked.messages, qid),
                "metrics": metrics,
                "r8": match.group("r8"),
                "score_role": match.group("score_role"),
            }
        )

    return {
        "exit_code": checked.exit_code,
        "k": K,
        "messages": sorted(checked.messages),
        "n": EXPECTED_N,
        "questions": exported,
    }


def dumps(table: dict) -> str:
    return json.dumps(table, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    table = build_table()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(table), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} n={table['n']} exit_code={table['exit_code']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
