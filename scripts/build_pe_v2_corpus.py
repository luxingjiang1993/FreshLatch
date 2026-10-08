"""从国家法律法规数据库快照抽取 pe_v2 语料。

读取已下载的 parquet（默认 /tmp/pe_v2_src），不改配额，不调用评委。
主张和证据块都是原文连续片段。跑完写出 docket、markdown 和 PROVENANCE.json。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

from freshlatch.eval.patch_events_construct import (
    ClaimView,
    ChunkRef,
    ConstructError,
    _clause,
    _date,
    _deletion,
    _find_dates,
    _find_numbers,
    _numeric,
    _sign,
    _slot_labels,
)

ROOT = Path(__file__).resolve().parents[1]
PARQUET_DIR = Path("/tmp/pe_v2_src")
CORPUS = ROOT / "data" / "corpus" / "pe_v2"
DOCKET = ROOT / "data" / "pe_v2_docket.json"
FETCH_TIME = "2026-10-08T05:18:00Z"
DATASET_URL = "https://huggingface.co/datasets/senry5433/china-effective-laws-regulations"
SOURCE_URL = "https://flk.npc.gov.cn/"
LICENSE = (
    "汇编 CC0-1.0（senry5433/china-effective-laws-regulations，快照 2026-08-26）。"
    "正文是国家机关立法、行政、司法性质文件，不适用《著作权法》第五条。"
    "国家法律法规数据库网站使用条款未逐页核验。"
)

_CYCLE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(个百分点|万元|元|%)")
_OB = re.compile(r"应当|不得")
_QUAL = re.compile(r"除[^，。；\n]{1,30}外|不少于\s*\d+|不超过\s*\d+|至少\s*\d+|至多\s*\d+")
_ABOL = ("废止", "不再存在", "不再要求", "不再")
_AFF = ("仍然", "仍", "继续")
_BUILDERS = {"数值": _numeric, "日期": _date, "条款替换": _clause, "删除": _deletion}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[。\n]", text) if part.strip()]


def _view(statement: str, t1_bodies: list[str], t0_bodies: list[str]) -> ClaimView:
    t1 = tuple(
        ChunkRef(f"p{i + 1}", f"doc#p{i + 1}@T1", body) for i, body in enumerate(t1_bodies)
    )
    t0 = tuple(
        ChunkRef(f"p{i + 1}", f"doc#p{i + 1}@T0", body) for i, body in enumerate(t0_bodies)
    )
    return ClaimView(
        claim_id="x",
        statement=statement,
        doc_id="doc",
        anchor="p1",
        t1=t1[0],
        t0=t0[0] if t0 else None,
        t1_chunks=t1,
        t0_chunks=t0,
    )


def _accepts(kind: str, statement: str, t1_bodies: list[str], t0_bodies: list[str]) -> bool:
    view = _view(statement, t1_bodies, t0_bodies)
    fn = _BUILDERS[kind]
    try:
        fn(view, "正确", None, None)
    except ConstructError:
        return False
    for op in range(4):
        for sign in ("plus", "minus"):
            try:
                fn(view, "坏", op, sign)
            except ConstructError:
                return False
    return True


def _structural_miss(kind: str, statement: str, t1_bodies: list[str], t0_bodies: list[str]) -> bool:
    view = _view(statement, t1_bodies, t0_bodies)
    try:
        _BUILDERS[kind](view, "正确", None, None)
    except ConstructError as exc:
        return exc.structural
    return False


def _isolated(kind: str, statement: str, t1_bodies: list[str], t0_bodies: list[str]) -> bool:
    earlier = ("数值", "日期", "条款替换", "删除")
    for name in earlier:
        if name == kind:
            break
        if not _structural_miss(name, statement, t1_bodies, t0_bodies):
            return False
    return True


def _load_docs() -> list[dict]:
    docs: list[dict] = []
    for path in sorted(PARQUET_DIR.glob("*.parquet")):
        table = pq.read_table(
            path,
            columns=[
                "id",
                "title",
                "status",
                "filename_date",
                "text",
                "sha256",
                "source_url",
                "source_filename",
                "category",
            ],
        )
        for i in range(table.num_rows):
            if table.column("status")[i].as_py() != "有效":
                continue
            text = table.column("text")[i].as_py() or ""
            if not text:
                continue
            docs.append(
                {
                    "id": table.column("id")[i].as_py(),
                    "title": table.column("title")[i].as_py(),
                    "filename_date": table.column("filename_date")[i].as_py() or "",
                    "text": text,
                    "sha256": table.column("sha256")[i].as_py() or "",
                    "source_url": table.column("source_url")[i].as_py() or SOURCE_URL,
                    "source_filename": table.column("source_filename")[i].as_py() or "",
                    "category": table.column("category")[i].as_py() or "",
                }
            )
    return docs


def _locate(text: str, snippet: str) -> int:
    return text.find(snippet)


def _meta(doc: dict, snippet: str) -> dict:
    return {
        "title": doc["title"],
        "filename_date": doc["filename_date"],
        "source_id": doc["id"],
        "source_sha256": doc["sha256"],
        "source_filename": doc["source_filename"],
        "source_url": doc["source_url"] or SOURCE_URL,
        "category": doc["category"],
        "offset": _locate(doc["text"], snippet),
    }


def _usable_number_sentence(sent: str) -> bool:
    if not (12 <= len(sent) <= 180):
        return False
    if _find_dates(sent) or _OB.search(sent) or _QUAL.search(sent):
        return False
    ints = []
    for match in _CYCLE.finditer(sent):
        raw = match.group(1)
        if "." in raw:
            continue
        value = int(raw)
        if abs(value) >= 6:
            ints.append(value)
    return len(ints) >= 1


def _pick_numeric(docs: list[dict], limit: int) -> list[dict]:
    picked: list[dict] = []
    seen: set[str] = set()
    grouped: dict[str, list[dict]] = {}
    for doc in docs:
        grouped.setdefault(doc["title"], []).append(doc)
    ordered = []
    for title, group in grouped.items():
        group.sort(key=lambda item: item["filename_date"])
        if len(group) >= 2:
            ordered.append(group)
    for group in ordered:
        if len(picked) >= limit:
            break
        older, newer = group[0], group[-1]
        if older["id"] == newer["id"]:
            continue
        for sent in _sentences(older["text"]):
            if sent in seen or not _usable_number_sentence(sent):
                continue
            window = _number_window(newer["text"], sent)
            if window is None:
                continue
            if not _accepts("数值", sent, [window], [sent]):
                continue
            if not _isolated("数值", sent, [window], [sent]):
                continue
            seen.add(sent)
            picked.append(
                {
                    "stratum": "数值",
                    "statement": sent,
                    "t0_bodies": [sent],
                    "t1_bodies": [window],
                    "t0_src": _meta(older, sent),
                    "t1_src": [_meta(newer, window)],
                }
            )
            break
    if len(picked) < limit:
        for doc in docs:
            if len(picked) >= limit:
                break
            sentences = _sentences(doc["text"])
            for index, sent in enumerate(sentences):
                if sent in seen or not _usable_number_sentence(sent):
                    continue
                window = _number_window_near(sentences, index)
                if window is None:
                    continue
                if not _accepts("数值", sent, [window], [sent]):
                    continue
                seen.add(sent)
                picked.append(
                    {
                        "stratum": "数值",
                        "statement": sent,
                        "t0_bodies": [sent],
                        "t1_bodies": [window],
                        "t0_src": _meta(doc, sent),
                        "t1_src": [_meta(doc, window)],
                    }
                )
                break
    return picked


def _number_window(text: str, statement: str) -> str | None:
    unit = _CYCLE.search(statement)
    if unit is None:
        return None
    wanted = unit.group(2)
    sentences = _sentences(text)
    for index, sent in enumerate(sentences):
        if _OB.search(sent) or _find_dates(sent):
            continue
        if wanted not in sent:
            continue
        window = _number_window_near(sentences, index)
        if window and wanted in window:
            return window
    return None


def _number_window_near(sentences: list[str], index: int) -> str | None:
    for width in range(0, 3):
        start = max(0, index - width)
        end = min(len(sentences), index + width + 1)
        chunk = sentences[start:end]
        if any(_OB.search(part) or _find_dates(part) for part in chunk):
            continue
        window = "。".join(chunk)
        nums = _find_numbers(window)
        values = {item.value for item in nums}
        if len(values) < 2:
            continue
        if not any(item.unit in {"%", "个百分点", "元", "万元"} and item.integer and abs(item.value) >= 6 for item in nums):
            continue
        return window
    return None


def _date_ok(sent: str) -> bool:
    if not (8 <= len(sent) <= 180):
        return False
    if _find_numbers(sent) or _OB.search(sent) or _QUAL.search(sent):
        return False
    dates = _find_dates(sent)
    if len(dates) != 1:
        return False
    day = dates[0].day
    return day is None or 1 <= day <= 28


def _pick_dates(docs: list[dict], limit: int) -> list[dict]:
    picked: list[dict] = []
    seen: set[str] = set()
    for doc in docs:
        if len(picked) >= limit:
            break
        sentences = [sent for sent in _sentences(doc["text"]) if _date_ok(sent)]
        if len(sentences) < 2:
            continue
        for left, right in zip(sentences, sentences[1:]):
            if left in seen:
                continue
            dates_left = _find_dates(left)
            dates_right = _find_dates(right)
            if not dates_left or not dates_right:
                continue
            if (dates_left[0].year, dates_left[0].month, dates_left[0].day) == (
                dates_right[0].year,
                dates_right[0].month,
                dates_right[0].day,
            ):
                continue
            if _OB.search(left) or _OB.search(right):
                continue
            if not _accepts("日期", right, [left, right], [right]):
                continue
            if not _isolated("日期", right, [left, right], [right]):
                continue
            seen.add(right)
            picked.append(
                {
                    "stratum": "日期",
                    "statement": right,
                    "t0_bodies": [right],
                    "t1_bodies": [left, right],
                    "t0_src": _meta(doc, right),
                    "t1_src": [_meta(doc, left), _meta(doc, right)],
                }
            )
            break
    return picked


def _clause_sentence(sent: str) -> bool:
    if not (8 <= len(sent) <= 160):
        return False
    if not _OB.search(sent):
        return False
    if _find_dates(sent) or _find_numbers(sent) or _QUAL.search(sent):
        return False
    return True


def _pick_clauses(docs: list[dict], limit: int) -> list[dict]:
    picked: list[dict] = []
    seen: set[str] = set()
    for doc in docs:
        if len(picked) >= limit:
            break
        sentences = [sent for sent in _sentences(doc["text"]) if _clause_sentence(sent)]
        if len(sentences) < 2:
            continue
        for left, right in zip(sentences, sentences[1:]):
            if left in seen or left == right or left in right or right in left:
                continue
            if not _accepts("条款替换", left, [left, right], [left]):
                continue
            if not _isolated("条款替换", left, [left, right], [left]):
                continue
            seen.add(left)
            picked.append(
                {
                    "stratum": "条款替换",
                    "statement": left,
                    "t0_bodies": [left],
                    "t1_bodies": [left, right],
                    "t0_src": _meta(doc, left),
                    "t1_src": [_meta(doc, left), _meta(doc, right)],
                }
            )
            break
    return picked


def _qual_spans(text: str) -> list[str]:
    found: list[str] = []
    for match in re.finditer(r"除[^，。；\n]{1,30}外", text):
        span = match.group(0).strip()
        if span and span not in found:
            found.append(span)
    for match in re.finditer(
        r"留存不少于\s*\d+\s*年|不少于\s*\d+\s*[^，。；\n]{0,12}|不超过\s*\d+\s*[^，。；\n]{0,12}|至少\s*\d+\s*[^，。；\n]{0,12}|至多\s*\d+\s*[^，。；\n]{0,12}",
        text,
    ):
        span = match.group(0).strip()
        if span and span not in found:
            found.append(span)
    return found


def _caps(statement: str, t1: str) -> set[object]:
    view = _view(statement, [t1], [statement])
    found: set[object] = set()
    try:
        _deletion(view, "正确", None, None)
    except ConstructError:
        return found
    found.add("C")
    for op in range(4):
        try:
            _deletion(view, "坏", op, "plus")
        except ConstructError:
            continue
        found.add(op)
    return found


def _pick_deletions(docs: list[dict]) -> list[dict]:
    abol: dict[str, tuple[str, dict]] = {}
    aff: dict[str, tuple[str, dict]] = {}
    for doc in docs:
        for sent in _sentences(doc["text"]):
            if _OB.search(sent):
                continue
            spans = _qual_spans(sent)
            if not spans:
                continue
            if any(marker in sent for marker in _ABOL):
                for span in spans:
                    if len(span) >= 8 and span not in abol:
                        abol[span] = (sent, doc)
            elif any(marker in sent for marker in _AFF):
                for span in spans:
                    if span not in aff:
                        aff[span] = (sent, doc)
    items: list[dict] = []
    seen: set[str] = set()
    for doc in docs:
        text = doc["text"]
        for sa, (abol_sent, abol_doc) in abol.items():
            ia = text.find(sa)
            if ia < 0:
                continue
            for sb, (aff_sent, aff_doc) in aff.items():
                if sa == sb:
                    continue
                ib = text.find(sb)
                if ib < 0 or abs(ia - ib) > 2500:
                    continue
                lo, hi = min(ia, ib), max(ia + len(sa), ib + len(sb))
                window = text[lo:hi]
                if window in seen or len(window) > 2500:
                    continue
                if _find_dates(window) or _find_numbers(window):
                    continue
                t1 = abol_sent + "。\n" + aff_sent + "。"
                if _OB.search(t1) or not _isolated("删除", window, [t1], [window]):
                    continue
                caps = _caps(window, t1)
                if "C" not in caps:
                    continue
                seen.add(window)
                items.append(
                    {
                        "stratum": "删除",
                        "statement": window,
                        "t0_bodies": [window],
                        "t1_bodies": [t1],
                        "t0_src": _meta(doc, window),
                        "t1_src": [_meta(abol_doc, abol_sent), _meta(aff_doc, aff_sent)],
                        "caps": caps,
                    }
                )
    plain = 0
    for doc in docs:
        op3_only = sum(1 for item in items if 3 in item["caps"] and 1 not in item["caps"])
        if plain >= 40 and op3_only >= 8:
            break
        for sent in _sentences(doc["text"]):
            if sent in seen or len(sent) > 240:
                continue
            if _find_dates(sent) or _find_numbers(sent) or _OB.search(sent):
                continue
            has_modifier = any(word in sent for word in ("大约", "约", "显著", "明显", "初步", "大致", "基本"))
            if plain >= 40 and not has_modifier:
                continue
            hits = [span for span in abol if span in sent]
            if not hits:
                continue
            span = max(hits, key=len)
            abol_sent, abol_doc = abol[span]
            t1 = abol_sent + "。"
            if _OB.search(t1) or not _isolated("删除", sent, [t1], [sent]):
                continue
            caps = _caps(sent, t1)
            if "C" not in caps:
                continue
            seen.add(sent)
            plain += 1
            items.append(
                {
                    "stratum": "删除",
                    "statement": sent,
                    "t0_bodies": [sent],
                    "t1_bodies": [t1],
                    "t0_src": _meta(doc, sent),
                    "t1_src": [_meta(abol_doc, abol_sent)],
                    "caps": caps,
                }
            )
    return _order_deletions(items)


def _slot_plan(edit_type: str) -> list[tuple[str, int | None, str | None]]:
    pilot, n30, rest = _slot_labels(edit_type)
    plan: list[tuple[str, int | None, str | None]] = []
    bad_index = 0
    for gold in list(pilot) + list(n30) + list(rest):
        if gold == "坏":
            plan.append((gold, bad_index % 4, _sign(bad_index)))
            bad_index += 1
        else:
            plan.append((gold, None, None))
    return plan


def _order_deletions(items: list[dict]) -> list[dict]:
    plan = _slot_plan("删除")
    extra = [("正确", None, None)] * 15
    reserved: dict[int, list[int]] = {0: [], 1: [], 3: []}
    taken: set[int] = set()

    def reserve(op: int, count: int) -> None:
        ranked = sorted(
            (index for index, item in enumerate(items) if op in item["caps"] and index not in taken),
            key=lambda index: sum(1 for other in (0, 1, 3) if other != op and other in items[index]["caps"]),
        )
        for index in ranked[:count]:
            reserved[op].append(index)
            taken.add(index)

    reserve(1, 4)
    reserve(0, 4)
    reserve(3, 3)
    used: set[int] = set()
    ordered: list[dict] = []
    for gold, operator, _sign in plan + extra:
        best: int | None = None
        if gold == "坏" and operator in reserved and reserved[operator]:
            best = reserved[operator].pop(0)
        else:
            for index, item in enumerate(items):
                if index in used or index in taken:
                    continue
                caps = item["caps"]
                if gold == "正确" and "C" in caps and not any(op in caps for op in (0, 1, 3)):
                    best = index
                    break
                if gold == "坏" and operator in caps and operator == 2:
                    best = index
                    break
            if best is None and gold == "正确":
                for index, item in enumerate(items):
                    if index in used or index in taken:
                        continue
                    if "C" in item["caps"]:
                        best = index
                        break
        if best is None:
            break
        used.add(best)
        taken.add(best)
        ordered.append(items[best])
    print(
        "deletion caps",
        {
            "op0": sum(1 for item in items if 0 in item["caps"]),
            "op1": sum(1 for item in items if 1 in item["caps"]),
            "op3": sum(1 for item in items if 3 in item["caps"]),
            "correct": sum(1 for item in items if "C" in item["caps"]),
            "ordered": len(ordered),
        },
    )
    return ordered


def _write_markdown(path: Path, doc_id: str, as_of: str, title: str, bodies: list[str]) -> str:
    chunks = []
    for index, body in enumerate(bodies, start=1):
        chunks.append(f"## p{index}\n{body.strip()}\n")
    text = (
        "---\n"
        f"doc_id: {doc_id}\n"
        f"as_of: {as_of}\n"
        "source_type: public\n"
        f"title: {title}\n"
        "checksum:\n"
        "---\n"
        + "\n".join(chunks)
    )
    data = text.encode("utf-8")
    path.write_bytes(data)
    return _sha256(data)


def _write(items: list[dict]) -> None:
    if CORPUS.exists():
        for path in CORPUS.rglob("*"):
            if path.is_file():
                path.unlink()
    (CORPUS / "t0").mkdir(parents=True, exist_ok=True)
    (CORPUS / "t1").mkdir(parents=True, exist_ok=True)
    claims = []
    provenance = []
    prefixes = {"数值": "a", "日期": "b", "条款替换": "c", "删除": "d"}
    counts = {name: 0 for name in prefixes}
    for item in items:
        counts[item["stratum"]] += 1
        claim_id = f"{prefixes[item['stratum']]}{counts[item['stratum']]:03d}"
        title = item["t0_src"]["title"]
        t0_hash = _write_markdown(
            CORPUS / "t0" / f"{claim_id}.md", claim_id, "T0", title, item["t0_bodies"]
        )
        t1_hash = _write_markdown(
            CORPUS / "t1" / f"{claim_id}.md", claim_id, "T1", title, item["t1_bodies"]
        )
        claims.append(
            {
                "claim_id": claim_id,
                "statement": item["statement"],
                "t0_evidence_ids": [f"{claim_id}#p1"],
                "dimension": item["stratum"],
            }
        )
        provenance.append(
            {
                "claim_id": claim_id,
                "stratum": item["stratum"],
                "fetch_time": FETCH_TIME,
                "license": LICENSE,
                "dataset_url": DATASET_URL,
                "t0_file": f"data/corpus/pe_v2/t0/{claim_id}.md",
                "t1_file": f"data/corpus/pe_v2/t1/{claim_id}.md",
                "t0_sha256": t0_hash,
                "t1_sha256": t1_hash,
                "t0_source": item["t0_src"],
                "t1_source": item["t1_src"],
            }
        )
    DOCKET.write_text(
        json.dumps(
            {
                "question": "公开法规的旧表述是否应按新文本更新",
                "claims": claims,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "fetch_time": FETCH_TIME,
        "dataset_url": DATASET_URL,
        "dataset_snapshot": "2026-08-26",
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claims": provenance,
    }
    (CORPUS / "PROVENANCE.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    docs = _load_docs()
    print(f"docs {len(docs)}")
    numeric = _pick_numeric(docs, 45)
    print(f"numeric {len(numeric)}")
    dates = _pick_dates(docs, 45)
    print(f"dates {len(dates)}")
    clauses = _pick_clauses(docs, 45)
    print(f"clauses {len(clauses)}")
    deletions = _pick_deletions(docs)
    print(f"deletions {len(deletions)}")
    _write(numeric + dates + clauses + deletions)
    print(f"wrote {DOCKET}")


if __name__ == "__main__":
    main()
