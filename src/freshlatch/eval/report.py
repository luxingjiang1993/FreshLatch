"""报告双产出(§4.3):console 摘要(当场看)+ `reports/report-<date>.md` + raw JSON(进 git)。

混淆矩阵报条数不报百分比;失败条目附轨迹指针,归因人工定性(机械归因 harness 归 W5–W8)。
decoding 参数 + 模型版本 + 日期逐运行入档(§4.7);托管端点漂移限制写入留档。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from freshlatch.eval.matrix import BUCKETS, EXPECTED_VERDICT

BUCKET_ZH = {"must_stale": "必须判死", "must_fresh": "必须判活", "must_unknown": "必须判未知"}


def _decoding_block(raw: dict) -> list[str]:
    d = raw["decoding"]
    return [
        "## 运行档案(decoding 逐运行入档,§4.7)",
        "",
        f"- 模型版本: `{d['model']}`",
        f"- temperature: `{d['temperature']}`",
        f"- seed: `{d['seed']}`",
        f"- 记录时间(UTC): {raw['recorded_at']}",
        "",
        "> 复现条款:闸层(must_* 零违例)给定解码参数下逐位复现;判定层按文档化容差;"
        "违例级背离触发人查。qwen-flash 是活托管端点,跨会话复现只能近似,此限制为留档声明。",
        "",
    ]


def render_report(raw: dict) -> str:
    if raw["kind"] == "gold_run":
        return _render_gold(raw)
    if raw["kind"] == "control_run":
        return _render_control(raw)
    raise ValueError(f"未知的 raw 结果类型: {raw['kind']}")


def _render_gold(raw: dict) -> str:
    lines: list[str] = [
        f"# 金标运行报告({raw['recorded_at'][:10]})",
        "",
        f"- 运行遍数 N = {raw['runs']}(per-claim 命中次数/N 见 pass@k 表;N=1 退化为单列)",
        "- 评测对象:端到端真主链(Lead 循环 + Critic 派驻 + 规则闸),非替身(ADR-0005 决策一)",
        f"- eval 模式开关:{' ; '.join(raw['eval_mode_switches'])}",
        "",
    ]
    lines += _decoding_block(raw)

    # 混淆矩阵:条数,不报百分比
    lines += ["## 混淆矩阵(条数;小样本不报百分比,§4.3)", "",
              "| 期望档 | fresh | stale | unknown | 命中 | 漏判 |", "|---|---|---|---|---|---|"]
    agg_pass = {cid: 0 for cid in raw["pass_at_k"]}
    for bucket in BUCKETS:
        hit_counts = [r["matrix"]["hits"][bucket] for r in raw["per_run"]]
        last = raw["per_run"][-1]["matrix"]
        counts = last["counts"][bucket]
        misses = last["misses"][bucket]
        miss_str = ", ".join(f"{m['claim_id']}→{m['predicted']}" for m in misses) or "无"
        hit_str = "/".join(str(h) for h in hit_counts) if raw["runs"] > 1 else str(hit_counts[0])
        lines.append(f"| {bucket}({BUCKET_ZH[bucket]}) | {len(counts['fresh'])} | {len(counts['stale'])} "
                     f"| {len(counts['unknown'])} | {hit_str} | {miss_str} |")
    lines.append("")

    # pass@k 表(按 N>1 设计;N=1 退化为单列)
    lines += ["## per-claim 命中次数/N(pass@k)", "", "| claim_id | 命中/N |", "|---|---|"]
    for cid, n in sorted(raw["pass_at_k"].items(), key=lambda kv: int(kv[0][1:])):
        lines.append(f"| {cid} | {n}/{raw['runs']} |")
    lines.append("")

    # J1 点回
    lines += ["## J1 点回判据(全量,不抽样;must_unknown 无 T1 原文天然豁免)", "",
              "| claim_id | 登记锚段落 | 判定证据命中 | 豁免 |", "|---|---|---|---|"]
    for cid, pb in sorted(raw["point_back_j1"].items(), key=lambda kv: int(kv[0][1:])):
        lines.append(f"| {cid} | {pb['expected_anchor']} | {'✅' if pb['hit'] else '❌'} "
                     f"| {'✅' if pb['exempt'] else ''} |")
    lines.append("")

    # J2 有效反证(机器层)+ 反向护栏
    lines += ["## J2 有效反证(机器可查三硬:①可点回 ③span 对齐;②语义判据为机器代理,硬判定归人工)",
              "", "| claim_id | 遍 | ①可点回 | ③锚对齐 | ②代理(reason 提及 t1_doc) | 机器层有效 |", "|---|---|---|---|---|---|"]
    for cid, checks in sorted(raw["counterevidence_j2"].items(), key=lambda kv: int(kv[0][1:])):
        for i, c in enumerate(checks, 1):
            lines.append(f"| {cid} | {i} | {'✅' if c['pointable'] else '❌'} "
                         f"| {'✅' if c['anchor_aligned'] else '❌'} "
                         f"| {'✅' if c['causal_sentence_proxy'] else '❌'} "
                         f"| {'✅' if c['valid_machine'] else '❌'} |")
    lines += ["", f"> {raw['counterevidence_j2'][next(iter(raw['counterevidence_j2']))][0]['causal_sentence_note']}",
              "", "## J2 反向护栏(must_fresh 不得出现机器层有效反证)", ""]
    for cid, guards in sorted(raw["fresh_guardrail_j2"].items(), key=lambda kv: int(kv[0][1:])):
        ok = "✅" if all(guards) else "❌"
        lines.append(f"- {cid}: {ok}({'/'.join('过' if g else '违' for g in guards)})")
    lines.append("")

    # 失败条目轨迹指针
    lines += ["## 失败条目轨迹指针(归因人工定性;机械归因 harness 归 W5–W8)", ""]
    last_detail = raw["per_run"][-1]["detail"]
    miss_ids = [m["claim_id"] for b in BUCKETS for m in raw["per_run"][-1]["matrix"]["misses"][b]]
    for cid in sorted(set(miss_ids), key=lambda c: int(c[1:])):
        d = last_detail.get(cid, {"trajectory": "(无 detail)"})
        lines.append(f"- {cid}: {d['trajectory']}")
    if not miss_ids:
        lines.append("- 无失败条目。")
    lines.append("")
    return "\n".join(lines)


def _render_control(raw: dict) -> str:
    lines: list[str] = [
        f"# 假绿对照报告({raw['recorded_at'][:10]})",
        "",
        "- 基线:同模型(qwen-flash)无工具,只读 T0 摘要;输出契约 JSON mode 三档(alive/dead/unknown)",
        f"- prompt 红线留档:{raw['redline_note']}",
        "- 对照成立判据:全部 must_stale 被判 alive(已死主张必须假绿,本产品必须红);"
        "must_unknown 判 alive = 没源的也敢判绿,同样记为对照信号",
        "",
    ]
    lines += _decoding_block(raw)
    lines += ["## 对照结果", "", "| claim_id | 基线判定 |", "|---|---|"]
    for cid, r in sorted(raw["results"].items(), key=lambda kv: int(kv[0][1:])):
        lines.append(f"| {cid} | {r['verdict']} |")
    lines += [
        "",
        f"- must_stale 假绿条数: {len(raw['false_green_must_stale'])}/4 ({', '.join(raw['false_green_must_stale']) or '无'})",
        f"- must_unknown 盲判绿条数: {len(raw['blind_green_must_unknown'])} ({', '.join(raw['blind_green_must_unknown']) or '无'})",
        f"- **对照成立: {'✅' if raw['control_pass'] else '❌'}**",
        "",
    ]
    return "\n".join(lines)


def console_summary(raw: dict) -> str:
    """当场看的摘要(N 行,不含明细)。"""
    if raw["kind"] == "gold_run":
        last = raw["per_run"][-1]["matrix"]
        parts = [f"[gold] N={raw['runs']} model={raw['decoding']['model']} "
                 f"temp={raw['decoding']['temperature']} seed={raw['decoding']['seed']}"]
        for bucket in BUCKETS:
            parts.append(f"{bucket}: 命中 {last['hits'][bucket]} "
                         f"漏判 {len(last['misses'][bucket])}")
        parts.append(f"all_hit: {last['all_hit']}")
        return "\n".join(parts)
    if raw["kind"] == "control_run":
        return (f"[control] model={raw['decoding']['model']} "
                f"must_stale 假绿 {len(raw['false_green_must_stale'])}/4; "
                f"对照成立: {raw['control_pass']}")
    raise ValueError(f"未知的 raw 结果类型: {raw['kind']}")


def write_outputs(raw: dict, out_dir: str | Path = "reports") -> tuple[Path, Path]:
    """双产出:report-<date>.md + raw JSON 同名进 git;已存在同名文件时追加时分秒。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    md_path = out / f"report-{stamp}.md"
    json_path = out / f"report-{stamp}.json"
    if md_path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        md_path = out / f"report-{stamp}.md"
        json_path = out / f"report-{stamp}.json"
    md_path.write_text(render_report(raw), encoding="utf-8")
    json_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    return md_path, json_path
