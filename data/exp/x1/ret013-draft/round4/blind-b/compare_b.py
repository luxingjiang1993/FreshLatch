# 对照盲标 B 与草稿 A，并按 qtype-kw-v1 重算题型。只打印分歧，不改题。
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "src"))

from freshlatch.eval.x1_checks import (  # noqa: E402
    clean_chunk_text,
    clean_text,
    eight_gram_overlap,
    lcs_ratio,
    strip_law_names,
)
from freshlatch.store.ingest import load_corpus  # noqa: E402
from freshlatch.store.base import chunk_evidence_id  # noqa: E402
from freshlatch.store.pipeline import tokenize  # noqa: E402

DRAFT = ROOT / "data/exp/x1/ret013-draft"
CORPUS = DRAFT / "corpus"

KW_STOP = frozenset(
    """什么 哪些 哪个 哪份 哪一 哪家 哪项 哪类 哪里 哪几种 如何 为何 为什么 是否 有何 怎样 怎么 怎么样 多少 几年 几个 几天 请问 请 有没有 能否
    分别 以及 其中 这一 这个 那个 那份 那家 这些 那些 相比 之间 关于 对于 根据 按照 还是 或者 并且 而且 如果 现在 目前 当前 最新 原先 以前 此前 之前 之后 后来 一下 某些
    时点 阶段 文档 文件 材料 版本 内容 一份 两份 三份 多份
    规定 提到 提及 指出 说明 描述 表述 表示 认为 显示 说法 给出
    原因 理由 目的 用途 状态 方式 方法 作用 意义 特点 优势 差异 区别 不同 变化 变了 变动 调整 处理 情况 问题 方面 发生
    可以 需要 应当 可能 能够 具有 存在 出现 发现 获得 处于 通过 使用 提供 仍然 引发 导致 进行 采取 属于 相关 一致 实际 真实
    """.split()
)
LAW_NAMES = (
    "中华人民共和国公司法",
    "个人信息出境标准合同办法",
    "促进和规范数据跨境流动规定",
    "数据出境安全评估办法",
    "个人信息出境认证办法",
    "公司法",
)
CITE_RE = re.compile(r"令\d+号|第[一二三四五六七八九十百千0-9]+[条款项章]|附件\d+")
QUOTE_RE = re.compile(r"[“\"「『]([^”\"」』]{2,})[”\"」』]|[‘']([^’']{2,})[’']")
LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.]{0,}")
# 带单位的汉字数量，以及阿拉伯数字。跟在哪/每/各/某/任/这/那 后面的数字不算。
NUM_RE = re.compile(
    r"(?<![哪每各某任这那])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?%?"
    r"|(?<![哪每各某任这那])[一二三四五六七八九十百千万两0-9]+(?:个|年|天|日|月|周|小时|分钟|元|美元|万元|个百分点)"
)
HAN_RE = re.compile(r"^[\u4e00-\u9fff]+$")


def load_chunks() -> dict[str, str]:
    texts: dict[str, str] = {}
    for _doc, chunks in load_corpus(CORPUS):
        for ch in chunks:
            texts[chunk_evidence_id(ch)] = ch.text
    return texts


def body_of(texts: dict[str, str], eid: str) -> str:
    raw = texts.get(eid, "")
    # chunk.text 含 ## pN 标题行
    lines = raw.split("\n", 1)
    if lines and lines[0].startswith("## "):
        return lines[1] if len(lines) > 1 else ""
    return raw


def keywords(query: str) -> list[str]:
    text = query
    for name in sorted(LAW_NAMES, key=len, reverse=True):
        text = text.replace(name, " ")
    text = text.replace("T0", " ").replace("T1", " ")
    text = CITE_RE.sub(" ", text)
    found: list[str] = []
    used = [False] * len(text)

    def take(span_text: str, start: int, end: int) -> None:
        if any(used[start:end]):
            return
        piece = span_text.strip()
        if len(piece) < 1:
            return
        found.append(piece)
        for i in range(start, end):
            used[i] = True

    for m in QUOTE_RE.finditer(text):
        inner = m.group(1) or m.group(2) or ""
        if len(inner) >= 2:
            # 只占引号内文字，避免把引号本身再切进去
            a = m.start(1) if m.group(1) is not None else m.start(2)
            b = m.end(1) if m.group(1) is not None else m.end(2)
            take(inner, a, b)
    for m in LATIN_RE.finditer(text):
        if any(used[m.start() : m.end()]):
            continue
        token = m.group(0)
        if any(ch.isalpha() for ch in token):
            take(token, m.start(), m.end())
    for m in NUM_RE.finditer(text):
        if any(used[m.start() : m.end()]):
            continue
        take(m.group(0), m.start(), m.end())
    residual = "".join(ch if not used[i] else " " for i, ch in enumerate(text))
    # jieba 在残串上切。位置用顺序对齐：tokenize 不回位置，覆盖率只看词面。
    for tok in tokenize(residual):
        if not HAN_RE.fullmatch(tok):
            continue
        if len(tok) < 2:
            continue
        if tok[0] in "哪几":
            continue
        if tok in KW_STOP:
            continue
        found.append(tok)
    # 去重保序
    out: list[str] = []
    seen = set()
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def coverage(query: str, rel_bodies: list[str]) -> float:
    keys = keywords(query)
    if not keys:
        return 0.0
    blob = clean_text("".join(rel_bodies))
    hit = 0
    for key in keys:
        if clean_text(key) and clean_text(key) in blob:
            hit += 1
    return hit / len(keys)


def metrics(query: str, rel_ids: list[str], texts: dict[str, str]) -> dict:
    bodies = [body_of(texts, eid) for eid in rel_ids]
    cleaned_bodies = [clean_chunk_text(texts[eid]) for eid in rel_ids if eid in texts]
    q_clean = strip_law_names(clean_text(query))
    r8 = eight_gram_overlap(q_clean, cleaned_bodies) if cleaned_bodies else None
    lcs = lcs_ratio(q_clean, cleaned_bodies) if cleaned_bodies else None
    cov = coverage(query, bodies)
    return {"r8": r8, "lcs": lcs, "coverage": cov, "keywords": keywords(query)}


def qtype_kw(query: str, rel_ids: list[str], points: list[str], texts: dict[str, str], force_para: bool) -> tuple[str, str]:
    m = metrics(query, rel_ids, texts)
    r8 = m["r8"] if m["r8"] is not None else 0.0
    if r8 > 0.2:
        return "lexical", f"r8={r8:.3f}>0.2"
    if m["coverage"] >= 0.8:
        return "lexical", f"coverage={m['coverage']:.3f}>=0.8 kw={m['keywords']}"
    doc_ids = []
    for eid in rel_ids:
        doc_ids.append(eid.split("#", 1)[0])
    same_chunk = False
    cleaned_pts = [clean_text(p) for p in points]
    for eid in rel_ids:
        blob = clean_chunk_text(texts.get(eid, ""))
        if cleaned_pts and all(p and p in blob for p in cleaned_pts):
            same_chunk = True
            break
    by_doc: dict[str, list[str]] = {}
    for eid in rel_ids:
        by_doc.setdefault(eid.split("#", 1)[0], []).append(eid)
    all_in_one_doc = False
    if cleaned_pts:
        for doc, eids in by_doc.items():
            blob = "".join(clean_chunk_text(texts.get(e, "")) for e in eids)
            if all(p and p in blob for p in cleaned_pts):
                all_in_one_doc = True
                break
    structure = (
        len(rel_ids) >= 2
        and len(set(doc_ids)) >= 2
        and len(points) >= 2
        and not same_chunk
        and not all_in_one_doc
    )
    if structure and not force_para:
        return "multi_hop", f"structure r8={r8:.3f} cov={m['coverage']:.3f}"
    if force_para:
        return "paraphrase", f"冗余证据，非多跳 r8={r8:.3f} cov={m['coverage']:.3f}"
    return "paraphrase", f"else r8={r8:.3f} cov={m['coverage']:.3f} kw={m['keywords']}"


def main() -> None:
    texts = load_chunks()
    b = json.loads((DRAFT / "round4/blind-b/labels-b.json").read_text(encoding="utf-8"))
    a_items = []
    for name in ("round4/part1/questions.part1.json", "round4/part2/questions.part2.json"):
        raw = json.loads((DRAFT / name).read_text(encoding="utf-8"))
        a_items.extend(raw["queries"])
    a_by = {q["id"]: q for q in a_items}
    # 问句以 B 文件为准；若缺 query，从 A 只补 query/as_of（盲标文件未重复问句也可）
    queries_only = {}
    # labels-b 没存 query。从盲标提取文件读。
    blind_q = json.loads(Path("/tmp/blind-queries.json").read_text(encoding="utf-8"))
    for row in blind_q:
        queries_only[row["id"]] = row["query"]

    rows = []
    for bq in b["queries"]:
        qid = bq["id"]
        aq = a_by[qid]
        query = queries_only[qid]
        # 要点必须是 relevant 正文子串
        missing = []
        for p in bq["answer_points"]:
            ok = any(p in body_of(texts, eid) for eid in bq["relevant"])
            if not ok:
                missing.append(p)
        force = "冗余证据" in bq["b_notes"]
        qt, why = qtype_kw(query, bq["relevant"], bq["answer_points"], texts, force)
        m = metrics(query, bq["relevant"], texts)
        rel_eq = set(bq["relevant"]) == set(aq["relevant"])
        cat_eq = bq["category"] == aq["category"]
        rows.append(
            {
                "id": qid,
                "decision": bq["decision"],
                "flags": bq["template_flags"],
                "rel_eq": rel_eq,
                "b_rel": bq["relevant"],
                "a_rel": aq["relevant"],
                "cat_b": bq["category"],
                "cat_a": aq["category"],
                "qtype_b": bq["qtype"],
                "qtype_rule": qt,
                "qtype_a": aq["qtype"],
                "qtype_why": why,
                "r8": m["r8"],
                "lcs": m["lcs"],
                "cov": m["coverage"],
                "ap_missing": missing,
                "ap_b": bq["answer_points"],
                "ap_a": aq["answer_points"],
                "dis_b": bq["distractors"],
                "dis_a": aq["distractors"],
                "kind_a": aq.get("trap_kind"),
                "kind_b": bq["trap_kind"],
                "notes": bq["b_notes"],
            }
        )
    out = DRAFT / "round4/blind-b/compare-b.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(rows)
    rel_bad = [r for r in rows if not r["rel_eq"]]
    cat_bad = [r for r in rows if r["cat_b"] != r["cat_a"]]
    kind_bad = [r for r in rows if r["kind_b"] != r["kind_a"]]
    qt_rule_ne_a = [r for r in rows if r["qtype_rule"] != r["qtype_a"]]
    missing = [r for r in rows if r["ap_missing"]]
    print(f"n={n} rel_diff={len(rel_bad)} cat_diff={len(cat_bad)} kind_diff={len(kind_bad)} qtype_rule_ne_A={len(qt_rule_ne_a)} ap_missing={len(missing)}")
    print("--- relevant diff ---")
    for r in rel_bad:
        print(r["id"])
        print("  B", r["b_rel"])
        print("  A", r["a_rel"])
    print("--- category/kind diff ---")
    for r in cat_bad + [x for x in kind_bad if x not in cat_bad]:
        print(r["id"], "cat", r["cat_b"], r["cat_a"], "kind", r["kind_b"], r["kind_a"])
    print("--- qtype rule != A ---")
    for r in qt_rule_ne_a:
        print(r["id"], "rule", r["qtype_rule"], "A", r["qtype_a"], "B", r["qtype_b"], r["qtype_why"], "r8", r["r8"], "lcs", r["lcs"])
    print("--- answer point not in B relevant ---")
    for r in missing:
        print(r["id"], r["ap_missing"])
    print("--- decisions ---")
    from collections import Counter
    print(Counter(r["decision"] for r in rows))
    print("--- high lcs or r8 among non-lexical rule ---")
    for r in rows:
        if r["qtype_rule"] != "lexical" and ((r["r8"] or 0) > 0.2 or (r["lcs"] or 0) >= 0.8):
            print(r["id"], r["qtype_rule"], "r8", r["r8"], "lcs", r["lcs"])


if __name__ == "__main__":
    main()
