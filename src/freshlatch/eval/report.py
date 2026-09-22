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
    lines = [
        "## 运行档案(decoding 逐运行入档,§4.7)",
        "",
        f"- 模型版本: `{d['model']}`",
        f"- temperature: `{d['temperature']}`",
        f"- seed: `{d['seed']}`",
        f"- 记录时间(UTC): {raw['recorded_at']}",
    ]
    if raw.get("runs", 1) > 1:
        lines.append(f"- 逐遍记录: `per_run[i].decoding`(每遍独立 DecodingParams,recorded_at 区分)")
    if raw.get("evidence_packet_schema"):
        lines.append(f"- Auditor 证据包 schema 版本: `{raw['evidence_packet_schema']}`"
                     "(#20 §4.6:版本随报告登记)")
    lines += [
        "",
        "> 复现条款:闸层(must_* 零违例)给定解码参数下逐位复现;判定层按文档化容差;"
        "违例级背离触发人查。qwen-flash 是活托管端点,跨会话复现只能近似,此限制为留档声明。",
        "",
    ]
    return lines


def _token_usage_block(raw: dict) -> list[str]:
    """K5-1:报告 MD 用量节(raw JSON 顶层 + per_run 已写;无块则跳过)。"""
    tu = raw.get("token_usage")
    if not tu:
        return []
    lines = [
        "## Token 用量(K5)",
        "",
        f"- prompt_tokens: `{tu['prompt_tokens']}`",
        f"- completion_tokens: `{tu['completion_tokens']}`",
        f"- total_tokens: `{tu['total_tokens']}`",
    ]
    if raw.get("runs", 1) > 1:
        lines.append("- 逐遍: `per_run[i].token_usage`")
    lines += ["", ""]
    return lines


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
        "- 层间归因诚实框定(#19 §4.6):本报告是 bundle 层行为读数;接线/注入/人格各层生效性"
        "由结构单测断言(tests/unit/test_c5c6_wiring.py),bundle 绿 ≠ 逐层行为生效。",
        "",
    ]
    lines += _decoding_block(raw)
    lines += _token_usage_block(raw)

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
              "", "| claim_id | 判定 | ①可点回 | ③锚对齐 | ②代理(reason 提及 t1_doc) | 机器层有效 |", "|---|---|---|---|---|---|"]
    for cid, checks in sorted(raw["counterevidence_j2"].items(), key=lambda kv: int(kv[0][1:])):
        for i, c in enumerate(checks, 1):
            lines.append(f"| {cid} | {c['status']} | {'✅' if c['pointable'] else '❌'} "
                         f"| {'✅' if c['anchor_aligned'] else '❌'} "
                         f"| {'✅' if c['causal_sentence_proxy'] else '❌'} "
                         f"| {'✅' if c['valid_machine'] else '❌'} |")
    if raw["counterevidence_j2"]:
        first_cid = next(iter(raw["counterevidence_j2"]))
        lines += ["", f"> {raw['counterevidence_j2'][first_cid][0]['causal_sentence_note']}"]
    # 决策七:全量通过率 + 波动区间(N>1 时有意义;N=1 退化为单遍读数)
    run_totals = [sum(r["matrix"]["hits"].values()) for r in raw["per_run"]]
    full_pass = sum(1 for r in raw["per_run"] if r["matrix"]["all_hit"])
    lines += [
        "",
        f"- 全量通过遍数: {full_pass}/{raw['runs']}(单遍 12 条全命中为全量通过)",
        f"- 单遍命中条数波动区间: [{min(run_totals)}, {max(run_totals)}] / 12",
        "",
        "## J2 反向护栏(must_fresh 不得出现机器层有效反证)", ""]
    for cid, guards in sorted(raw["fresh_guardrail_j2"].items(), key=lambda kv: int(kv[0][1:])):
        ok = "✅" if all(guards) else "❌"
        lines.append(f"- {cid}: {ok}({'/'.join('过' if g else '违' for g in guards)})")
    lines.append("")

    # 乙-ii:维度疑似混淆自动标注(must_fresh 判 stale 且锚未对齐;归 #19 评估文档,不进 CONTEXT.md)
    flags = raw.get("dimension_confusion_flags") or {}
    lines += ["## 维度疑似混淆标注(乙-ii:must_fresh 判 stale 且金标锚未对齐;机器疑似,定性归人查)",
              ""]
    flagged = False
    for cid, run_flags in sorted(flags.items(), key=lambda kv: int(kv[0][1:])):
        bad_runs = [str(i + 1) for i, f in enumerate(run_flags) if f]
        if bad_runs:
            flagged = True
            lines.append(f"- ⚠️ {cid}: 第 {'/'.join(bad_runs)} 遍 stale 且未落在金标锚"
                         f"——疑似以他维度证据推翻本维度主张(如定价≠成本、客单价≠毛利、覆盖率≠渗透率),人查定性")
    if not flagged:
        lines.append("- 无。")
    lines.append("")

    # 乙-i:干扰项敏感度附表(不进判分矩阵,不计通过线;#21)
    lines += ["## 干扰项敏感度附表(乙-i:must_fresh 方向未见混淆类型;不进判分矩阵,不计通过线)", ""]
    sens = raw.get("distractor_sensitivity") or {}
    if not sens:
        lines.append("- 本运行未含干扰项桶(gold.json 无 must_fresh_distractor 或未提供 distractor docket)。")
    else:
        lines += ["| claim_id | 期望 | 逐遍判定 | fresh 命中/N | 金标锚命中/N | 轨迹 |",
                  "|---|---|---|---|---|---|"]
        for cid, s in sorted(sens.items(), key=lambda kv: int(kv[0][1:])):
            lines.append(f"| {cid} | fresh | {'/'.join(s['statuses']) or '(未跑)'} "
                         f"| {s['fresh_hits']}/{raw['runs']} | {s['anchor_hits']}/{raw['runs']} "
                         f"| {s['trajectory']} |")
        lines += ["",
                  "> 口径:干扰项测修复对未见混淆类型(客单价≠毛利、覆盖率≠渗透率)的泛化,"
                  "判分矩阵仍为 12 条(W4↔W12 同尺),本表不计通过线;判定 stale 且锚未对齐时"
                  "按上一节「维度疑似混淆」标注人查。"]
    lines.append("")

    # S1/S2 分歧率(双判一致仲裁读数;只落档不报成败,#20 评估 §4.6)
    div = raw.get("divergence_s1_s2")
    lines += ["## S1/S2 分歧率(双判一致仲裁读数;只落档不报成败,#20 评估 §4.6)", ""]
    if div and div.get("total"):
        lines.append(f"- S1(其余主张×遍): {div['s1']};S2(Lead stale/unknown × Auditor fresh): {div['s2']}"
                     f";S2 占比: {div['s2_rate']:.1%}")
    else:
        lines.append("- 本运行无读数(raw 缺 divergence_s1_s2 或零主张×遍)。")
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
    instrument = raw.get("instrument") or "false_green_control"
    prompt_id = raw.get("prompt_id") or "CONTROL_PROMPT"
    title = "假绿仪器 C 报告" if instrument == "false_green_control_c" else "假绿对照报告"
    lines: list[str] = [
        f"# {title}({raw['recorded_at'][:10]})",
        "",
        f"- 仪器:`{instrument}`; prompt_id:`{prompt_id}`",
        "- 基线:同模型(qwen-flash)无工具,只读 T0 摘要;输出契约 JSON mode 三档(alive/dead/unknown)",
        f"- prompt 红线留档:{raw['redline_note']}",
        "- 对照成立判据:全部 must_stale 被判 alive(已死主张必须假绿,本产品必须红);"
        "must_unknown 判 alive = 没源的也敢判绿,同样记为对照信号",
        "",
    ]
    lines += _decoding_block(raw)
    has_excerpt = any("t0_excerpt_char_len" in r for r in raw["results"].values())
    if has_excerpt:
        lines += ["## 对照结果", "",
                  "| claim_id | 基线判定 | t0_excerpt 字数 | 送模 evidence ids |",
                  "|---|---|---|---|"]
        for cid, r in sorted(raw["results"].items(), key=lambda kv: int(kv[0][1:])):
            ids = ", ".join(r.get("t0_evidence_ids_sent") or [])
            lines.append(f"| {cid} | {r['verdict']} | {r.get('t0_excerpt_char_len', '')} | {ids} |")
    else:
        lines += ["## 对照结果", "", "| claim_id | 基线判定 |", "|---|---|"]
        for cid, r in sorted(raw["results"].items(), key=lambda kv: int(kv[0][1:])):
            lines.append(f"| {cid} | {r['verdict']} |")
    lines += [
        "",
        f"- must_stale 假绿条数: {len(raw['false_green_must_stale'])}/{raw['must_stale_total']} ({', '.join(raw['false_green_must_stale']) or '无'})",
        f"- must_unknown 盲判绿条数: {len(raw['blind_green_must_unknown'])} ({', '.join(raw['blind_green_must_unknown']) or '无'})",
        f"- **对照成立: {'✅' if raw['control_pass'] else '❌'}**",
        "",
    ]
    baseline = raw.get("distractor_baseline") or {}
    if baseline:
        lines += ["## 干扰项基线读数(#21 乙-i 假绿对照记录:期望 alive)", "",
                  "| claim_id | 基线判定 |", "|---|---|"]
        for cid, v in sorted(baseline.items(), key=lambda kv: int(kv[0][1:])):
            lines.append(f"| {cid} | {v} {'(期望 alive)' if v != 'alive' else '✅'} |")
        lines += ["", f"> {raw.get('distractor_baseline_note', '')}", ""]
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
        tag = "control-c" if raw.get("instrument") == "false_green_control_c" else "control"
        return (f"[{tag}] model={raw['decoding']['model']} "
                f"must_stale 假绿 {len(raw['false_green_must_stale'])}/{raw['must_stale_total']}; "
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
