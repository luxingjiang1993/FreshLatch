# 把 category-rule-v2 的 211 题、盲标合并后的新题、补批次，写成仓库题集。
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare_b as C  # noqa: E402
import gen_x1_drafts as drafts  # noqa: E402

DRAFT = ROOT / "data/exp/x1/ret013-draft"
X1 = ROOT / "data/exp/x1"
REPO_KEYS = (
    "id",
    "query",
    "as_of",
    "qtype",
    "category",
    "score_role",
    "relevant",
    "answer_points",
    "distractors",
    "eval_intent",
)

G2_QUERY = "新公司法（2023修订）的施行日期是什么？其第二百六十六条对出资期限有何要求？"
G2_DROP = "旧法（2018修正）的施行日期为二〇〇六年一月一日"
OVERRIDE_ID = "r4n-s4-d0-t1-91-qb"


def merge_points(a: list[str], b: list[str]) -> list[str]:
    """A ∪ B，互相包含时留较长的一条。"""
    uniq: list[str] = []
    for point in list(a) + list(b):
        if point not in uniq:
            uniq.append(point)
    uniq.sort(key=len, reverse=True)
    kept: list[str] = []
    for point in uniq:
        if any(point != other and point in other for other in kept):
            continue
        kept.append(point)
    return kept


def repo_item(item: dict) -> dict:
    out = {key: item[key] for key in REPO_KEYS}
    if item.get("conflict_pair"):
        out["conflict_pair"] = item["conflict_pair"]
    return out


def load_a() -> dict[str, dict]:
    items = []
    for name in ("round4/part1/questions.part1.json", "round4/part2/questions.part2.json"):
        raw = json.loads((DRAFT / name).read_text(encoding="utf-8"))
        items.extend(raw["queries"])
    return {q["id"]: q for q in items}


def batch_specs() -> list[dict]:
    """16 个 round4 批次加补上的 s6-d2-t1-91。S6 要带 must_include。"""
    rows = [
        ("s2-d0-t1-91", "S2", "D0", "T1", "越南经销商返点与客服响应：同快照冲突加元陈述，合成叙述"),
        ("s3-d1-t1-91", "S3", "D1", "T1", "竞品E年费与席位上限：同快照冲突加元陈述，合成叙述"),
        ("s4-d2-t1-91", "S4", "D2", "T1", "单票履约成本与退货率：同快照冲突加元陈述，合成叙述"),
        ("s6-d3-t1-91", "S6", "D3", "T1", "住户收入口径启用日与样本户数：同快照冲突加元陈述，合成叙述"),
        ("s1-d1-t1-91", "S1", "D1", "T1", "印尼支付牌照与退款到账：同快照冲突加元陈述，合成叙述"),
        ("s5-d2-t1-91", "S5", "D2", "T1", "平台活跃商户与留存率：同快照冲突加元陈述，合成叙述"),
        ("s2-d2-t0-91", "S2", "D2", "T0", "包装材料交期与抽检不良率：同快照冲突加元陈述，合成叙述"),
        ("s3-d0-t0-91", "S3", "D0", "T0", "竞品H坐席价格与试用天数：同快照冲突加元陈述，合成叙述"),
        ("s4-d0-t1-91", "S4", "D0", "T1", "工单自动分派准确率与处理时长：同快照冲突加元陈述，合成叙述"),
        ("s6-d1-t1-91", "S6", "D1", "T1", "v1接口下线日与v2成功率：同快照冲突加元陈述，合成叙述"),
        ("s1-d3-t0-91", "S1", "D3", "T0", "出口增速与港口吞吐：同快照冲突加元陈述，合成叙述"),
        ("s5-d1-t0-91", "S5", "D1", "T0", "网购渗透率与复购周期：同快照冲突加元陈述，合成叙述"),
        ("s2-d3-t1-91", "S2", "D3", "T1", "试点城市数量与补贴上限：同快照冲突加元陈述，合成叙述"),
        ("s3-d2-t1-91", "S3", "D2", "T1", "竞品G合规模块收费与服务可用性：同快照冲突加元陈述，合成叙述"),
        ("s4-d3-t0-91", "S4", "D3", "T0", "电力折标煤系数与产线利用率：同快照冲突加元陈述，合成叙述"),
        ("s6-d0-t1-91", "S6", "D0", "T1", "退款审批门槛与首次解决率：同快照冲突加元陈述，合成叙述"),
        ("s6-d2-t1-91", "S6", "D2", "T1", "仓库安检通过比例与工伤件数：同快照冲突加元陈述，合成叙述（补余量批次）"),
    ]
    must = {
        "s6-d3-t1-91": [
            "新的住户收入统计口径自5月1日起启用",
            "新口径的启用时间推迟到6月1日",
            "样本户数不再列入跟踪项",
            "本期样本户数为1.2万户",
        ],
        "s6-d1-t1-91": [
            "旧版v1接口将于9月30日下线",
            "v1接口的下线时间延期至11月30日",
            "接口调用成功率不再列入跟踪",
            "上周v2接口调用成功率为99.2%",
        ],
        "s6-d0-t1-91": [
            "金额在300美元以上的退款需要主管审批",
            "退款审批阈值改为500美元以上",
            "首次解决率本月未复测",
            "上月首次解决率为74%",
        ],
        "s6-d2-t1-91": [
            "仓库安检通过比例写成百分之九十六",
            "仓库安检通过比例写成百分之九十一",
            "工伤件数不再列入跟踪",
            "该月因工受伤为七件",
        ],
    }
    out = []
    for batch_id, genre, domain, as_of, topic in rows:
        batch = {
            "batch_id": batch_id,
            "genre": genre,
            "domain": domain,
            "n_docs": 2,
            "chunks_per_doc": 3,
            "n_questions": 3,
            "max_chars_per_chunk": 800,
            "topic": topic,
            "as_of": as_of,
        }
        if genre == "S6":
            batch["must_include"] = must[batch_id]
        out.append(batch)
    return out


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    for path in sorted(src.rglob("*.md")):
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != path.read_bytes():
                raise SystemExit(f"语料路径冲突: {target}")
            continue
        shutil.copy2(path, target)
        n += 1
    return n


def main() -> None:
    texts = C.load_chunks()
    # 补批次已经写进 staging corpus，重新读一次才能看见
    texts = C.load_chunks()
    b_raw = json.loads((DRAFT / "round4/blind-b/labels-b.json").read_text(encoding="utf-8"))
    sup = json.loads((DRAFT / "round4/blind-b/labels-supplement.json").read_text(encoding="utf-8"))
    queries_only = {
        row["id"]: row["query"]
        for row in json.loads(Path("/tmp/blind-queries.json").read_text(encoding="utf-8"))
    }
    a_by = load_a()
    base = json.loads(
        (DRAFT / "round4/category-rule-v2/questions.category-v2.json").read_text(encoding="utf-8")
    )

    merged_new = []
    rejected = []
    disagreements = []
    provenance_new = []
    for bq in b_raw["queries"]:
        qid = bq["id"]
        aq = a_by[qid]
        query = queries_only[qid]
        if set(bq["relevant"]) != set(aq["relevant"]) or bq["category"] != aq["category"]:
            disagreements.append(qid)
        if bq["decision"] != "accept":
            rejected.append(
                {
                    "id": qid,
                    "reason": bq["b_notes"],
                    "flags": bq["template_flags"],
                }
            )
            continue
        points = merge_points(aq["answer_points"], bq["answer_points"])
        distractors = []
        for eid in list(aq["distractors"]) + list(bq["distractors"]):
            if eid in bq["relevant"] or eid in distractors:
                continue
            if not eid.endswith("@" + bq["as_of"]):
                continue
            distractors.append(eid)
        missing = [p for p in points if not any(p in C.body_of(texts, eid) for eid in bq["relevant"])]
        if missing:
            raise SystemExit(f"{qid} 合并要点不是原文子串: {missing}")
        force = qid == OVERRIDE_ID
        qtype, why = C.qtype_kw(query, bq["relevant"], points, texts, force)
        item = {
            "id": qid,
            "query": query,
            "as_of": bq["as_of"],
            "qtype": qtype,
            "category": "trap",
            "score_role": "arm",
            "relevant": bq["relevant"],
            "answer_points": points,
            "distractors": distractors,
            "eval_intent": f"trap {bq['trap_kind']} {bq['b_notes']}",
        }
        merged_new.append(item)
        group = "part1-existing-corpus" if qid.startswith("r4m-") else "part2-templated"
        provenance_new.append(
            {
                "id": qid,
                "source": "consensus+qtype-override" if force else "consensus",
                "decision": "冗余证据，非多跳" if force else None,
                "note": bq["b_notes"],
                "template_flags": bq["template_flags"],
                "group": group,
                "annotators": ["model-A (round4 draft)", "model-B (Ronin 代理人 blind)"],
                "from_rule": ["qtype", "answer_points", "distractors", "category"],
                "qtype_reason": why,
                "trap_kind": bq["trap_kind"],
            }
        )

    for sq in sup["queries"]:
        missing = [p for p in sq["answer_points"] if not any(p in C.body_of(texts, eid) for eid in sq["relevant"])]
        if missing:
            raise SystemExit(f"{sq['id']} 补题要点不是原文子串: {missing}")
        qtype, why = C.qtype_kw(sq["query"], sq["relevant"], sq["answer_points"], texts, False)
        if qtype != sq["qtype"]:
            raise SystemExit(f"{sq['id']} 题型应为 {qtype}，稿上写了 {sq['qtype']}：{why}")
        item = repo_item(sq)
        item["qtype"] = qtype
        merged_new.append(item)
        provenance_new.append(
            {
                "id": sq["id"],
                "source": "single-model-supplement",
                "decision": None,
                "note": sq["b_notes"],
                "template_flags": sq["template_flags"],
                "group": "supplement-batch",
                "annotators": ["Ronin 代理人（模型，补批次，无独立 A 稿）"],
                "from_rule": ["qtype", "category"],
                "qtype_reason": why,
                "trap_kind": sq["trap_kind"],
            }
        )

    if disagreements:
        raise SystemExit(f"有 relevant/category 分歧未处理: {disagreements}")

    queries = []
    for old in base["queries"]:
        item = repo_item(old)
        if item["id"] == "s6-d2-g2-q1":
            item["query"] = G2_QUERY
            item["answer_points"] = [p for p in item["answer_points"] if G2_DROP not in p and "二〇〇六" not in p]
        queries.append(item)
    queries.extend(repo_item(q) for q in merged_new)

    ids = [q["id"] for q in queries]
    if len(ids) != len(set(ids)):
        raise SystemExit("题目 id 重复")

    n_copied = copy_tree(DRAFT / "corpus", X1 / "corpus")
    n_traps = copy_tree(DRAFT / "traps", X1 / "traps")

    questions = {
        "meta": {
            "status": "owner-delegated-model-reviewed",
            "category_rule": "category-rule-v2",
            "qtype_rule": "qtype-kw-v1",
            "human_row_review": False,
            "reviewer": "Ronin 代理人（模型），受 owner 委托",
        },
        "queries": queries,
    }
    gold = {
        "status": "owner-delegated-model-reviewed",
        "meta": questions["meta"],
        "queries": queries,
    }
    (X1 / "questions.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (X1 / "gold.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    spec = json.loads((ROOT / "scripts/x1_draft_spec.example.json").read_text(encoding="utf-8"))
    spec["note"] = (
        spec.get("note", "")
        + " 2026-10-07 登记 round4 陷阱补题批次 *-91（含补余量的 s6-d2-t1-91）。这些批次的正文已经入库，不再用本 spec 重新生成。"
    )
    spec["batches"].extend(batch_specs())
    text = json.dumps(spec, ensure_ascii=False, indent=2) + "\n"
    (X1 / "draft-spec.json").write_text(text, encoding="utf-8")
    loaded = drafts._load_spec(X1 / "draft-spec.json")
    if isinstance(loaded, str):
        raise SystemExit(loaded)

    prev = json.loads((DRAFT / "LABELING-PROVENANCE.json").read_text(encoding="utf-8"))
    prev["meta"]["category_rule_applied"] = "category-rule-v2"
    prev["meta"]["human_row_review"] = False
    prev["meta"]["round4"] = {
        "blind_b": "Ronin 代理人（模型，本会话）。先只看问句和语料，写入 round4/blind-b/labels-b.json，再对照 A。",
        "annotator_A": "round4 草稿（Ronin 代理人，模型）",
        "protocol": "relevant 与 category 一致则接受；answer_points 取并集留长子串；distractors 取并集去掉 relevant，只留同快照；qtype 按 qtype-kw-v1，冗余证据改判 paraphrase。",
        "accepted_of_54": len([p for p in provenance_new if p["group"] != "supplement-batch"]),
        "rejected": rejected,
        "owner_review_disagreements": [
            {
                "id": "r4m-s5-d3-t1-05-q6",
                "kind": "near-duplicate",
                "kept": True,
                "reason": "与已有 s5-d3-t1-05-q1 都围绕公交出行 43% 对 51%。q1 问变化、两侧都相关；本题问最近一次独立调查的比例，旧值做干扰。B 判它仍是真陷阱，先留在题集里。owner 若删，trap 余量再减 1。",
            }
        ],
        "qtype_override": {
            "id": OVERRIDE_ID,
            "to": "paraphrase",
            "reason": "复评块单独写出 86%、汇报中的 92% 和小样本，已经能答完全题。按 owner 决定 2 改判 paraphrase，不改 kw-v1 函数。",
        },
        "templated_part2": {
            "authored": 48,
            "accepted": len([p for p in provenance_new if p["group"] == "part2-templated"]),
            "rejected": 1,
            "score_separately": True,
        },
    }
    for row in prev["questions"]:
        if row["id"] == "s6-d2-g2-q1":
            row["note"] = (row.get("note") or "") + " owner 方案 A：删去旧法施行日子问及对应要点；备忘改为二〇一八年十月二十六日施行。"
    prev["questions"].extend(provenance_new)
    prev["meta"]["review_delegation"]["human_row_review"] = False
    prev["meta"]["review_delegation"]["round4_note"] = (
        "round4 的 54 题由模型 A 起草、Ronin 代理人盲标为 B，再按协议合并。"
        "owner 只定了规则、流程，并授权并入这批合成语料和补题；不是人工逐行审核。"
        "48 道 part2 题是模板化合成陷阱，分数要分开报。补批次 s6-d2-t1-91 只有一份模型标注。"
    )
    (X1 / "LABELING-PROVENANCE.json").write_text(
        json.dumps(prev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    from collections import Counter

    arm = [q for q in queries if q.get("score_role", "arm") == "arm"]
    report = {
        "n_questions": len(queries),
        "n_arm": len(arm),
        "n_guardrail": len(queries) - len(arm),
        "qtype_arm": dict(Counter(q["qtype"] for q in arm)),
        "trap_adv_arm": sum(q["category"] in ("trap", "adversarial") for q in arm),
        "copied_corpus_md": n_copied,
        "copied_trap_md": n_traps,
        "rejected": rejected,
        "spec_batches": len(spec["batches"]),
    }
    (DRAFT / "round4/blind-b/merge-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
