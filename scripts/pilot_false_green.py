"""假绿对照预演(T1 验收②,§2.7):同模型(qwen-flash)不带工具,只读 T0 摘要。

已死主张 c1/c2/c3/c7 必须被判「成立」——预演不过 = 干扰项埋得不够像,语料回炉。
prompt 红线(§4.2):不得透露 T1 存在、不得透露金标。正式 control.py 归 T10 实装。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from freshlatch.llm import LLMClient  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402

Docket = json.loads(Path("data/t0_docket.json").read_text(encoding="utf-8"))
DEAD = ["c1", "c2", "c3", "c7"]

PROMPT = """你是市场研判助手。以下是一条数周前签发的研判主张及其签发时所依据的文档摘录(均为当时口径):

主张: {statement}
签发时依据: {t0}

请判断:基于上述材料,该主张在当时是否成立、看起来是否合理?只依据给定材料回答。
回答格式:成立 / 不成立,并给一句理由。"""


def main() -> None:
    store = SQLiteStore("data/freshlatch.db")
    llm = LLMClient()
    results = {}
    for c in Docket["claims"]:
        if c["claim_id"] not in DEAD:
            continue
        doc_id, anchor = c["t0_evidence_ids"][0].split("#")
        chunk = store.get_chunk(doc_id, anchor, as_of="T0")
        msg = llm.chat(
            [{"role": "user", "content": PROMPT.format(statement=c["statement"], t0=chunk.text)}]
        )
        text = (msg.content or "").strip()
        verdict = "成立" if text.startswith("成立") else "不成立"
        results[c["claim_id"]] = verdict
        print(f"{c['claim_id']} -> {verdict} | {text[:80]}")
    passed = all(v == "成立" for v in results.values())
    print(f"\n假绿预演: {'通过' if passed else '未过(干扰项不够像,语料需回炉)'}")


if __name__ == "__main__":
    main()
