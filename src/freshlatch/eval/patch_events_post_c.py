"""路线 C 后置：消融 / 次要指标填格 + 抽检导出（Watch · 零 LLM）。

只回放 ``formal-generations-c.jsonl`` + ``run_arms_c``；消融复用已保存 T rewrite。
禁止改主比较三行 false-accept / k；禁止写 B 归档；禁止发模型。
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_ablation import (
    ABLATION_ORDER,
    HYBRID_COLUMN,
    ablation_interval_report,
    primary_comparison_rows,
    run_ablations,
)
from freshlatch.eval.patch_events_arms import Decoding
from freshlatch.eval.patch_events_copy_constrained import run_arms_c
from freshlatch.eval.patch_events_formal import _saved_generator, ingested_t1
from freshlatch.eval.patch_events_formal_c import (
    assert_generations_c_allowed,
    generations_c_path,
    load_formal_c_n100,
    prereg_c_activated,
)
from freshlatch.eval.patch_events_metrics import (
    METRIC_ORDER,
    SEED,
    compare_primary,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_spotcheck import IDENTITY, SPOTCHECK_ROLE, export_spotcheck
from freshlatch.eval.patch_events_verify import verify_edit

_RESULT_C = Path("docs/evidence/patch-events/RESULT-C.md")
_RESULT_B = Path("docs/evidence/patch-events/RESULT-B.md")
_SPOTCHECK_EXPORT = Path("docs/evidence/patch-events/spotcheck-c-export.md")
_SPOTCHECK_JSON = Path("docs/evidence/patch-events/spotcheck-c-export.json")
_ARMS = ("C", "T", "B1", "B2")
_ARM_LABEL = {
    "C": "C",
    "T": "T（copy-constrained）",
    "B1": "B1",
    "B2": "B2",
}
_ABLATION_SAYING = {
    "no_chunk_bind": "拿掉 chunk 绑定",
    "no_auto_verify": "拿掉自动核验",
    "soft_warning": "hard reject 换成 soft warning",
    "retrieval_bm25": "检索臂换成 BM25",
    HYBRID_COLUMN: "另记一列，不进入主比较",
}
_METRIC_DISPLAY = {
    "误放率": "false-accept rate",
    "误拒率": "误拒率",
    "错改率": "错改率",
    "可复验率": "可复验率",
}
_POST_BEGIN = "<!-- PE-C-POST:BEGIN -->"
_POST_END = "<!-- PE-C-POST:END -->"
_PRIMARY_MARKERS = (
    "## 主比较（同一次主比较 · R · run_arms_c）",
    "| T 对 C | false-accept rate |",
    "| T 对 B1 | false-accept rate |",
    "| T 对 B2 | false-accept rate |",
    "**固定放行数 k**",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_generations_c(root: Path | None = None) -> list[dict[str, Any]]:
    """读取 formal-generations-c；禁止落到 b/旧路径。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_c_path(base)
    assert_generations_c_allowed(path, base)
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError("formal-generations-c.jsonl 为空：禁止后置填格")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_post_c(*, root: Path | None = None) -> dict[str, Any]:
    """零 LLM：回放 → 主比较（只读）→ 消融 → 抽检导出包。"""
    base = _repo_root() if root is None else Path(root)
    if not prereg_c_activated(base):
        raise RuntimeError("PREREG-C 未激活：拒绝后置填格冒充正式")
    candidates = load_formal_c_n100(base)
    generations = load_generations_c(base)
    ingested = ingested_t1(candidates)
    generator = _saved_generator(generations)
    decoding = Decoding(temperature=0, seed=SEED)
    arms = run_arms_c(
        candidates,
        generator=generator,
        verifier=verify_edit,
        decoding=decoding,
        ingested_t1=ingested,
    )
    # 主比较只读：抄表用；不得在此改写 RESULT-C 成立格
    streams = named_streams()
    primary = compare_primary(
        primary_comparison_rows(arms),
        ingested_t1=ingested,
        streams=streams,
    )
    ablations = run_ablations(
        candidates,
        generator=generator,
        verifier=verify_edit,
        decoding=decoding,
        ingested_t1=ingested,
    )
    ablation_stream = random.Random(SEED)
    intervals = ablation_interval_report(
        arms["T"],
        ablations,
        ingested_t1=ingested,
        rng=ablation_stream,
    )
    # 抽检：以 T 臂记录为池（含金标/编辑类型）
    spot = export_spotcheck(arms["T"], n=100)
    return {
        "n": len(candidates),
        "k": primary.get("k"),
        "primary": primary,
        "arms": {arm: arms[arm] for arm in _ARMS},
        "ablations": {name: ablations[name] for name in (*ABLATION_ORDER, HYBRID_COLUMN)},
        "ablation_intervals": intervals,
        "spotcheck": spot,
        "bootstrap_consumed": "bootstrap（主比较只读）",
        "ablation_stream": "bootstrap_ablation 同种子另起 Random(SEED)",
        "sent_model": False,
    }


def _cell(value: object) -> str:
    if value is None:
        return "无定义"
    if isinstance(value, str):
        return value
    return format_rate(float(value)) if isinstance(value, (int, float)) and not isinstance(
        value, bool
    ) else str(value)


def render_post_sections(pack: Mapping[str, Any]) -> str:
    """次要 / 消融 / 抽检节正文（不含主比较）。"""
    primary = pack.get("primary") or {}
    arm_blocks = (primary.get("arms") or {}) if isinstance(primary, Mapping) else {}
    lines: list[str] = [
        _POST_BEGIN,
        "",
        "## 各臂（次要 · 不参与成立）",
        "",
        "> 只抄同一次 `run_arms_c` + `compare_primary` 的臂块；不改主比较成立格。",
        "",
        "| 臂 | 自然放行数 | 自然放行率 | 固定放行率 false-accept rate | 固定放行率误拒率 | 固定放行率错改率 | 固定放行率可复验率 | 延迟中位数 | 延迟 p95 | 成本 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for arm in _ARMS:
        block = arm_blocks.get(arm) or {}
        natural = block.get("natural") or {}
        fixed = block.get("fixed") or {}
        lines.append(
            "| {label} | {nr} | {nrate} | {fa} | {mr} | {wr} | {rv} | {med} | {p95} | {cost} |".format(
                label=_ARM_LABEL[arm],
                nr=_cell(natural.get("放行数")),
                nrate=_cell(natural.get("放行率")),
                fa=_cell(fixed.get("误放率")),
                mr=_cell(fixed.get("误拒率")),
                wr=_cell(fixed.get("错改率")),
                rv=_cell(fixed.get("可复验率")),
                med=_cell(block.get("latency_median")),
                p95=_cell(block.get("latency_p95")),
                cost=_cell(block.get("cost")),
            )
        )
    lines.extend(
        [
            "",
            f"- 固定放行数 k（只读，与主表一致）= `{pack.get('k')!r}`",
            "- 放行数为 0 时误放率/可复验率写「无定义」，不得写成 0。",
            "",
            "## 消融（只在 T · 不进主比较）",
            "",
            "> 回放已保存 T rewrite；闸差由消融开关决定。随机流：`bootstrap_ablation` 同种子另起，不消耗主比较 `bootstrap` 前缀。",
            "",
            "| 消融 | 预注册说法 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 |",
            "|---|---|---|---|---|---|",
        ]
    )
    by_tag = {item.get("ablation"): item for item in (pack.get("ablation_intervals") or [])}
    for tag in ABLATION_ORDER:
        item = by_tag.get(tag)
        saying = _ABLATION_SAYING.get(tag, tag)
        if item is None:
            for metric in METRIC_ORDER:
                lines.append(
                    f"| {tag} | {saying} | {_METRIC_DISPLAY[metric]} | 未填 | 未填 | 未填 |"
                )
            continue
        points = item.get("point") or {}
        intervals = item.get("intervals") or {}
        for metric in METRIC_ORDER:
            iv = intervals.get(metric) or {}
            lines.append(
                "| {tag} | {saying} | {disp} | {pt} | {lo} | {hi} |".format(
                    tag=tag,
                    saying=saying,
                    disp=_METRIC_DISPLAY[metric],
                    pt=_cell(points.get(metric)),
                    lo=_cell(iv.get("low")),
                    hi=_cell(iv.get("high")),
                )
            )
    # hybrid+rerank 另记：有记录则报自然误放点，无 bootstrap 区间
    hybrid_rows = (pack.get("ablations") or {}).get(HYBRID_COLUMN) or []
    if hybrid_rows:
        from freshlatch.eval.patch_events_metrics import natural_rates

        rates = natural_rates(hybrid_rows)
        for metric in METRIC_ORDER:
            lines.append(
                f"| {HYBRID_COLUMN} | {_ABLATION_SAYING[HYBRID_COLUMN]} | "
                f"{_METRIC_DISPLAY[metric]} | {_cell(rates.get(metric))} | 未填 | 未填 |"
            )
    else:
        for metric in METRIC_ORDER:
            lines.append(
                f"| {HYBRID_COLUMN} | {_ABLATION_SAYING[HYBRID_COLUMN]} | "
                f"{_METRIC_DISPLAY[metric]} | 未填 | 未填 | 未填 |"
            )

    spot = pack.get("spotcheck") or {}
    selected = list(spot.get("spotcheck") or [])
    lines.extend(
        [
            "",
            "## 抽检（导出入口 · 非真人盲审）",
            "",
            f"> 身份：{IDENTITY} · 角色：{SPOTCHECK_ROLE}。完成附加预注册前不得写真人盲审。",
            f"> 导出：`{_SPOTCHECK_EXPORT.as_posix()}` · `{_SPOTCHECK_JSON.as_posix()}`",
            "",
            f"- 抽检条数：{len(selected)}（n=100 配额：每层正确 2 / 坏 3）",
            "- **抽检一致率**：未填（无用户标签）",
            "- **用户对评委的 Cohen's κ**：未填（无用户标签）",
            "",
            _POST_END,
            "",
        ]
    )
    return "\n".join(lines)


def extract_primary_fingerprint(text: str) -> str:
    """主比较成立格指纹：三行 false-accept + k。用于断言后置写入不改主表。"""
    lines = text.splitlines()
    keep: list[str] = []
    for line in lines:
        if "| T 对 C | false-accept rate |" in line:
            keep.append(line)
        elif "| T 对 B1 | false-accept rate |" in line:
            keep.append(line)
        elif "| T 对 B2 | false-accept rate |" in line:
            keep.append(line)
        elif "**固定放行数 k**" in line:
            keep.append(line)
    return "\n".join(keep)


def merge_post_into_result_c(text: str, pack: Mapping[str, Any]) -> str:
    """把后置节写入 RESULT-C：替换旧 PE-C-POST 块，否则插在 B 附录前。不碰主比较行。"""
    before = extract_primary_fingerprint(text)
    if not before:
        raise RuntimeError("RESULT-C 缺主比较成立格：拒绝后置写入")
    section = render_post_sections(pack)
    if _POST_BEGIN in text and _POST_END in text:
        pattern = re.compile(
            re.escape(_POST_BEGIN) + r".*?" + re.escape(_POST_END) + r"\n?",
            flags=re.DOTALL,
        )
        merged = pattern.sub(section.rstrip() + "\n", text, count=1)
    else:
        anchor = "## B 负结果附录"
        if anchor in text:
            merged = text.replace(anchor, section.rstrip() + "\n\n" + anchor, 1)
        else:
            merged = text.rstrip() + "\n\n" + section
    after = extract_primary_fingerprint(merged)
    if after != before:
        raise RuntimeError("后置写入改动了主比较成立格：拒绝落盘")
    # 禁止误写 RESULT-B 内容进 C
    if "路线 B · 正式结果（RESULT-B）" in merged and "路线 C" not in merged.splitlines()[0]:
        raise RuntimeError("拒绝把 RESULT-B 标题写入 RESULT-C")
    return merged


def write_spotcheck_exports(pack: Mapping[str, Any], *, root: Path | None = None) -> tuple[Path, Path]:
    """落抽检 md + json；一致率未填。"""
    base = _repo_root() if root is None else Path(root)
    spot = pack.get("spotcheck") or {}
    md_path = base / _SPOTCHECK_EXPORT
    json_path = base / _SPOTCHECK_JSON
    selected = list(spot.get("spotcheck") or [])
    lines = [
        "# 路线 C 抽检导出（spotcheck-c）",
        "",
        f"> {IDENTITY} · {SPOTCHECK_ROLE} · **非真人盲审** · 不进主成立格。",
        "> 无用户标签：一致率 / κ 保持未填。",
        "",
        f"- n 配额：100 → 抽出 {len(selected)} 条",
        "- 种子流：`spotcheck` · `Random(20261007)`",
        "- 抽检一致率：未填",
        "- 用户对评委的 Cohen's κ：未填",
        "",
        "## 配对表（用户可见字段）",
        "",
    ]
    for row in selected:
        lines.extend(
            [
                f"### {row.get('claim_id')}",
                "",
                f"- before: {row.get('before_text')}",
                f"- after: {row.get('after_text')}",
                f"- evidence_id: {row.get('evidence_id')}",
                f"- evidence: {row.get('evidence_text')}",
                "",
            ]
        )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines), encoding="utf-8")
    payload = {
        "identity": IDENTITY,
        "spotcheck_role": SPOTCHECK_ROLE,
        "agreement_rate": None,
        "user_judge_kappa": None,
        "n_selected": len(selected),
        "spotcheck": selected,
        "note": "无用户标签；一致率未填；非真人盲审",
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path, json_path


def write_result_c_post(
    pack: Mapping[str, Any],
    *,
    root: Path | None = None,
    path: Path | None = None,
) -> Path:
    """合并后置节进 RESULT-C；禁止写 RESULT-B。"""
    base = _repo_root() if root is None else Path(root)
    out = base / _RESULT_C if path is None else Path(path)
    if not out.is_absolute():
        out = base / out
    if out.resolve() == (base / _RESULT_B).resolve() or out.name == "RESULT-B.md":
        raise RuntimeError("禁止把后置节写入 RESULT-B")
    text = out.read_text(encoding="utf-8")
    merged = merge_post_into_result_c(text, pack)
    out.write_text(merged, encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    """默认：回放填格 + 抽检导出。``--dry-json`` 只打印不写。"""
    parser = argparse.ArgumentParser(prog="python -m freshlatch.eval.patch_events_post_c")
    parser.add_argument("--dry-json", action="store_true", help="只打印摘要 JSON，不写盘")
    parser.add_argument("--no-write", action="store_true", help="算完不写 RESULT-C / 导出")
    args = parser.parse_args(argv)

    try:
        pack = run_post_c()
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        return 2

    summary = {
        "sent_model": False,
        "n": pack.get("n"),
        "k": pack.get("k"),
        "ablation_tags": list(ABLATION_ORDER),
        "spotcheck_n": len((pack.get("spotcheck") or {}).get("spotcheck") or []),
        "primary_k_readonly": pack.get("k"),
    }
    if args.dry_json:
        sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        return 0

    if not args.no_write:
        out = write_result_c_post(pack)
        md_path, json_path = write_spotcheck_exports(pack)
        sys.stdout.write(f"wrote {out}\n")
        sys.stdout.write(f"wrote {md_path}\n")
        sys.stdout.write(f"wrote {json_path}\n")
    sys.stdout.write(json.dumps(summary, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
