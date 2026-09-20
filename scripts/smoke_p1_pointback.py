"""P1 冒烟:随机 2 条主张 T1 点回,anchor 段落命中且高亮可见(§7.3 P1,通过线 2/2)。

三层核验(零 LLM):
1. 选样:seed=20260920 对金标 causal_chain 登记的主张(8 条非豁免)random.sample 2 条;
2. anchor 段落命中:检索库 get_chunk(doc, anchor, as_of="T1") 可解析(口径同 eval/checks.py);
3. 高亮可见:FastAPI TestClient 真起服务——/ 页含 .hit 高亮 CSS + scrollIntoView +
   t1_evidence_ids 渲染为 showSource 链接;/api/source/<doc>?as_of=T1 返回 200 且锚在段落清单内。

输出原样贴进 docs/evidence/w4/p1-p5-precheck.md 的 P1 行与「P1 点回记录」。
"""

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from freshlatch.eval.checks import parse_evidence_id  # noqa: E402
from freshlatch.store.sqlite_store import SQLiteStore  # noqa: E402
from freshlatch.ui import app as ui_app  # noqa: E402

SEED = 20260920
GOLD = json.loads((REPO_ROOT / "data" / "eval" / "gold.json").read_text(encoding="utf-8"))


def main() -> None:
    registered = sorted(GOLD["causal_chain"].keys(), key=lambda c: int(c[1:]))
    picks = random.Random(SEED).sample(registered, 2)
    store = SQLiteStore(REPO_ROOT / "data" / "freshlatch.db")
    client = TestClient(ui_app.app)

    page = client.get("/").text
    page_ok = all(s in page for s in (".hit{", "classList.add('hit')", "scrollIntoView"))
    client.post("/api/import")

    print(f"P1 选样:seed={SEED},抽中 {picks}(非豁免全集中 random.sample)")
    print(f"页面高亮机制在场(.hit CSS + add('hit') + scrollIntoView): {'✅' if page_ok else '❌'}")

    all_ok = page_ok
    for cid in picks:
        eid = GOLD["causal_chain"][cid]
        eid = f"{eid['t1_doc']}#{eid['anchor']}@T1"
        doc_id, anchor, as_of = parse_evidence_id(eid)
        hit = store.get_chunk(doc_id, anchor, as_of=as_of) is not None
        src = client.get(f"/api/source/{doc_id}", params={"as_of": as_of})
        anchors = [s["anchor"] for s in src.json().get("sections", [])]
        visible = src.status_code == 200 and anchor in anchors
        # t1 链接渲染路径:renderClaims 遍历 c.t1_evidence_ids 拼 showSource 链接(静态壳,
        # 链接运行时拼接;id 数据由复验 run 产出,冒烟不烧 LLM 重跑,只验渲染路径在场)。
        link_ok = ("for(const e of c.t1_evidence_ids||[])" in page
                   and "showSource(&quot;'+" in page)
        ok = hit and visible and link_ok
        all_ok = all_ok and ok
        print(f"[{cid}] {eid}")
        print(f"  anchor 段落命中(检索库解析): {'✅' if hit else '❌'}")
        print(f"  /api/source 200 且锚在段落清单: {'✅' if visible else '❌'}(T1 快照段落数 {len(anchors)})")
        print(f"  高亮链路渲染路径在场(t1 遍历 + showSource 模板): {'✅' if link_ok else '❌'}")

    print(f"\nP1 判定:{'2/2 通过 ✅' if all_ok else '未过 ❌'}"
          "(机器+服务端到端;headless 无浏览器像素级渲染,人看复核可在此之上叠加)")


if __name__ == "__main__":
    main()
