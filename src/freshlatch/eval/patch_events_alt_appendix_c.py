"""路线 C · ALT 附录测量（Watch · 零 LLM · 不进主成立）。

复用先验 ``patch_events_alt``（同文四闸 / B1′ / ``compare_alt_*``）。
产物：``ALT-APPENDIX-C.md`` + RESULT-C 指针节。禁止改主比较成立格。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_alt import (
    compare_alt_fixed_k_appendix,
    compare_alt_natural,
    run_same_text_gates,
    upgrade_tier,
)
from freshlatch.eval.patch_events_formal import ingested_t1
from freshlatch.eval.patch_events_formal_c import load_formal_c_n100
from freshlatch.eval.patch_events_post_c import (
    extract_primary_fingerprint,
    load_generations_c,
)

_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_RESULT_B = Path("docs/evidence/patch-events/RESULT-B.md")
_APPENDIX = Path("docs/evidence/patch-events/ALT-APPENDIX-C.md")
_ALT_BEGIN = "<!-- PE-C-ALT:BEGIN -->"
_ALT_END = "<!-- PE-C-ALT:END -->"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def fixture_separable_candidates() -> list[dict[str, Any]]:
    """ALT-02 整集可分开夹具：坏 B2 / 坏 B1′（正文对齐但未绑定）+ 正确挡地板。"""
    good = {
        "claim_id": "good1",
        "construction_gold": "正确",
        "after_text": "证据原文",
        "evidence_id": "doc#p1@T1",
        "evidence_text": "证据原文",
    }
    bad_b2 = {
        "claim_id": "bad_b2",
        "construction_gold": "坏",
        "after_text": "被污染的改写",
        "evidence_id": "doc#p1@T1",
        "evidence_text": "证据原文",
    }
    bad_b1 = {
        "claim_id": "bad_b1",
        "construction_gold": "坏",
        # 正文=证据 → B1′ 放行；evidence_id 未入库 → T 绑定拒
        "after_text": "证据原文",
        "evidence_id": "doc#unbound@T1",
        "evidence_text": "证据原文",
    }
    return [bad_b2, bad_b1, good]


def candidates_from_formal_c_t_after(
    *,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """用正式 C 的 T rewrite after 做同文四闸附录测量（仍非主成立）。"""
    base = _repo_root() if root is None else Path(root)
    rows = load_formal_c_n100(base)
    generations = load_generations_c(base)
    after_by_id: dict[str, str] = {}
    for item in generations:
        if str(item.get("arm")) == "T" and str(item.get("phase")) == "rewrite":
            text = item.get("text")
            if isinstance(text, str):
                after_by_id[str(item["claim_id"])] = text
    out: list[dict[str, Any]] = []
    for row in rows:
        cid = str(row["claim_id"])
        after = after_by_id.get(cid)
        if after is None:
            continue
        out.append(
            {
                "claim_id": cid,
                "construction_gold": row["construction_gold"],
                "edit_type": row.get("edit_type"),
                "after_text": after,
                "evidence_id": row["evidence_id"],
                "evidence_text": row["evidence_text"],
            }
        )
    if len(out) != 100:
        raise RuntimeError(f"正式 C T after 不足 100：got {len(out)}")
    return out


def _fmt(value: object) -> str:
    if value is None:
        return "无定义"
    if isinstance(value, float):
        return format(value, ".16g")
    return str(value)


def _natural_table(report: Mapping[str, Any]) -> list[str]:
    lines = [
        "| 臂 | 自然放行数 | 自然放行率 | 自然误放率 |",
        "|---|---:|---:|---:|",
    ]
    arms = report.get("arms") or {}
    for arm in ("C", "T", "B1", "B2"):
        block = arms.get(arm) or {}
        lines.append(
            f"| {arm} | {_fmt(block.get('自然放行数'))} | "
            f"{_fmt(block.get('自然放行率'))} | {_fmt(block.get('自然误放率'))} |"
        )
    lines.append("")
    lines.append("| 比较 | 自然误放差（对照−T） |")
    lines.append("|---|---|")
    for item in report.get("contrasts") or []:
        lines.append(
            f"| {item.get('name')} | {_fmt(item.get('natural_false_accept_delta'))} |"
        )
    return lines


def _fixed_table(report: Mapping[str, Any]) -> list[str]:
    lines = [
        f"- k = `{report.get('k')!r}` · appendix_only=`{report.get('appendix_only')}` · "
        f"feeds_upgrade=`{report.get('feeds_upgrade')}`",
        "",
        "| 臂 | 固定k放行数 | 固定k误放率 |",
        "|---|---:|---:|",
    ]
    arms = report.get("arms") or {}
    for arm in ("C", "T", "B1", "B2"):
        block = arms.get(arm) or {}
        lines.append(
            f"| {arm} | {_fmt(block.get('固定k放行数'))} | {_fmt(block.get('固定k误放率'))} |"
        )
    lines.append("")
    lines.append("| 比较 | 固定k误放差（对照−T） |")
    lines.append("|---|---|")
    for item in report.get("contrasts") or []:
        lines.append(
            f"| {item.get('name')} | {_fmt(item.get('fixed_k_false_accept_delta'))} |"
        )
    return lines


def run_alt_appendix_c(*, root: Path | None = None) -> dict[str, Any]:
    """夹具可分开 + 正式 C after 同文四闸附录；零 LLM。"""
    base = _repo_root() if root is None else Path(root)
    # --- 夹具层 ---
    fix_cands = fixture_separable_candidates()
    fix_rows = run_same_text_gates(fix_cands, ingested_t1={"doc#p1@T1"})
    fix_natural = compare_alt_natural(fix_rows)
    fix_fixed = compare_alt_fixed_k_appendix(fix_rows)
    fix_tier = upgrade_tier(fix_natural)

    # --- 正式 C after 附录层 ---
    formal_cands = candidates_from_formal_c_t_after(root=base)
    ingested = ingested_t1(load_formal_c_n100(base))
    formal_rows = run_same_text_gates(formal_cands, ingested_t1=ingested)
    formal_natural = compare_alt_natural(formal_rows)
    formal_fixed = compare_alt_fixed_k_appendix(formal_rows)
    # 升级档只吃自然率；正式层仅附录记录，仍可算档但不升格 RESULT-C
    formal_tier = upgrade_tier(formal_natural)

    return {
        "sent_model": False,
        "feeds_main_establishment": False,
        "fixture": {
            "n": len(fix_cands),
            "natural": fix_natural,
            "fixed_k_appendix": fix_fixed,
            "upgrade_tier": fix_tier,
        },
        "formal_c_same_text": {
            "n": len(formal_cands),
            "natural": formal_natural,
            "fixed_k_appendix": formal_fixed,
            "upgrade_tier": formal_tier,
            "note": "用 formal-generations-c 的 T after 做同文四闸；B1=B1′；不进 RESULT-C 成立格",
        },
    }


def render_alt_appendix_c(pack: Mapping[str, Any]) -> str:
    """渲染 ALT-APPENDIX-C 全文。"""
    fix = pack.get("fixture") or {}
    formal = pack.get("formal_c_same_text") or {}
    lines: list[str] = [
        "# 路线 C · ALT 附录测量（ALT-APPENDIX-C）",
        "",
        "> **附录 only · 不进主成立 · 可分开 ≠ 甲 · 零 LLM**。",
        "> 平行轨先验：#435 / #450–#453 · `compare_alt_*` · B1′ / 同文四闸。",
        "> **禁止**把本页数字抄进 `RESULT-C` 主比较成立格；**禁止**改 `compare_primary` 追甲。",
        "> 升级暂缓（#455）；夹具绿 / 附录可分开 ≠ 冲甲成立。",
        "",
        "## 层身份",
        "",
        "| 层 | 用途 | 可否进 RESULT-C 成立格 |",
        "|---|---|---|",
        "| fixture | 设计探针 / 可分开冒烟 | **否** |",
        "| formal_c_same_text | 正式 C 的 T after 上跑同文四闸 | **否**（附录） |",
        "",
        "## A · 夹具可分开（ALT-02 口径）",
        "",
        f"- n = `{fix.get('n')!r}`",
        f"- upgrade_tier（只吃自然率）= `{fix.get('upgrade_tier')!r}`",
        "",
        "### 自然率",
        "",
        *_natural_table(fix.get("natural") or {}),
        "",
        "### 固定 k 附录（不得进升级闸）",
        "",
        *_fixed_table(fix.get("fixed_k_appendix") or {}),
        "",
        "## B · 正式 C · 同文四闸附录（T after 回放）",
        "",
        f"- n = `{formal.get('n')!r}`",
        f"- upgrade_tier（附录记录 · 不升格主表）= `{formal.get('upgrade_tier')!r}`",
        f"- 注：{formal.get('note')}",
        "",
        "### 自然率",
        "",
        *_natural_table(formal.get("natural") or {}),
        "",
        "### 固定 k 附录",
        "",
        *_fixed_table(formal.get("fixed_k_appendix") or {}),
        "",
        "## 边界",
        "",
        "- 不保证甲；不改甲定义；不复活 A；不改 B 归档。",
        "- ALT 并主表 = 禁止；本页失败也不回写 `PREREG-C` 判据。",
        "- 主比较成立只认 `RESULT-C` 主表（已抄一次 formal-c 主比较）。",
        "",
    ]
    return "\n".join(lines)


def write_alt_appendix_c(
    pack: Mapping[str, Any],
    *,
    root: Path | None = None,
    path: Path | None = None,
) -> Path:
    base = _repo_root() if root is None else Path(root)
    out = base / _APPENDIX if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    if out.name in {"RESULT-C.md", "RESULT-B.md", "PREREG-C.md", "PREREG-B.md"}:
        raise RuntimeError(f"禁止把 ALT 附录正文写入主缝页: {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_alt_appendix_c(pack), encoding="utf-8")
    return out


def render_result_c_alt_pointer(pack: Mapping[str, Any]) -> str:
    """RESULT-C 指针节：无主成立数字。"""
    fix = pack.get("fixture") or {}
    formal = pack.get("formal_c_same_text") or {}
    return "\n".join(
        [
            _ALT_BEGIN,
            "",
            "## ALT 附录指针（不进主成立）",
            "",
            "> 详见 `docs/evidence/patch-events/ALT-APPENDIX-C.md`。",
            "> B1′ / 同文四闸 / `compare_alt_*` **仅附录**；不得抄进上方主比较成立格。",
            "",
            f"- 夹具 upgrade_tier：`{fix.get('upgrade_tier')!r}`（可分开≠甲）",
            f"- 正式 C 同文附录 upgrade_tier：`{formal.get('upgrade_tier')!r}`（不升格主表）",
            "- 主比较成立格：仍以本页上方一次 formal-c 主比较为准（结果丙）。",
            "",
            _ALT_END,
            "",
        ]
    )


def merge_alt_pointer_into_result_c(text: str, pack: Mapping[str, Any]) -> str:
    """追加/替换 ALT 指针；主比较指纹必须不变。"""
    before = extract_primary_fingerprint(text)
    if not before:
        raise RuntimeError("RESULT-C 缺主比较成立格：拒绝 ALT 指针写入")
    section = render_result_c_alt_pointer(pack)
    if _ALT_BEGIN in text and _ALT_END in text:
        pattern = re.compile(
            re.escape(_ALT_BEGIN) + r".*?" + re.escape(_ALT_END) + r"\n?",
            flags=re.DOTALL,
        )
        merged = pattern.sub(section.rstrip() + "\n", text, count=1)
    else:
        # 插在 B 负结果附录之前（与 PE-C-POST 同区之后亦可）
        anchor = "## B 负结果附录"
        if anchor in text:
            merged = text.replace(anchor, section.rstrip() + "\n\n" + anchor, 1)
        else:
            merged = text.rstrip() + "\n\n" + section
    after = extract_primary_fingerprint(merged)
    if after != before:
        raise RuntimeError("ALT 指针写入改动了主比较成立格：拒绝落盘")
    # 指针节不得夹带主成立表数字行
    pointer = section
    if "| T 对 C | false-accept rate |" in pointer:
        raise RuntimeError("ALT 指针节禁止嵌入主比较表行")
    return merged


def write_result_c_alt_pointer(
    pack: Mapping[str, Any],
    *,
    root: Path | None = None,
    path: Path | None = None,
) -> Path:
    base = _repo_root() if root is None else Path(root)
    out = base / _RESULT_C if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    if out.resolve() == (base / _RESULT_B).resolve() or out.name == "RESULT-B.md":
        raise RuntimeError("禁止把 ALT 指针写入 RESULT-B")
    text = out.read_text(encoding="utf-8")
    merged = merge_alt_pointer_into_result_c(text, pack)
    out.write_text(merged, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m freshlatch.eval.patch_events_alt_appendix_c"
    )
    parser.add_argument("--dry-json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    try:
        pack = run_alt_appendix_c()
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    summary = {
        "sent_model": False,
        "feeds_main_establishment": False,
        "fixture_tier": (pack.get("fixture") or {}).get("upgrade_tier"),
        "formal_c_tier": (pack.get("formal_c_same_text") or {}).get("upgrade_tier"),
        "appendix": _APPENDIX.as_posix(),
    }
    if args.dry_json:
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        return 0
    if not args.no_write:
        ap = write_alt_appendix_c(pack)
        rc = write_result_c_alt_pointer(pack)
        sys.stdout.write(f"wrote {ap}\n")
        sys.stdout.write(f"wrote pointer -> {rc}\n")
    sys.stdout.write(json.dumps(summary, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
