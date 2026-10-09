"""SLO-07 复验主业观测出口（D1 multi-run · D3=0 挂接 · D4 分布）。

层身份:
- D1/D5: **离线评测层**（金标 / Hard-Gold multi-run）。结果进 reports，**不进生产 score / 在线放行**。
- D3: **硬闸**，违例目标=0；**只引用 SLO-02 同一出口**，不另造冲突语义。
- D4: **观测 / Watch**，包结论三值周报（可发 / 需补丁 / 勿发）。

权威指标表: docs/ops/生产补丁放行SLO.md
金标门: must_stale 每遍全命中（hits == |must_stale|）；不得低于该门。
"""

from __future__ import annotations

import ast
import json
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from freshlatch.disposition import DISPOSITIONS, Disposition, aggregate_disposition
from freshlatch.disposition import ClaimDispositionInput
from freshlatch.eval.matrix import EXPECTED_VERDICT
from freshlatch.slo_hard_gate_violations import (
    HardGateReport,
    run_acceptance_probes,
)

# ---------------------------------------------------------------------------
# 层身份 / 预注册常量（写死；事后改门槛凑绿 = 作废）
# ---------------------------------------------------------------------------

LAYER_OFFLINE_EVAL = "离线评测层"
LAYER_HARD_GATE = "硬闸"
LAYER_WATCH = "观测"

# multi-run 默认遍数（命令与文档同锁；冒烟 n）
DEFAULT_MULTI_RUN_N = 3

# n 小于此阈值时只称冒烟，**不报总体方差**（Anthropic 清单：n 小诚实框定）
VARIANCE_REPORT_MIN_N = 30

# 当前金标门（D1）：must_stale 每遍全命中
GOLD_FLOOR_ID = "must_stale_full_hit_per_run"
GOLD_FLOOR_STATEMENT = (
    "不得低于当前金标门：must_stale 每遍全命中"
    "（hits == |must_stale|；期望判定 stale）"
)

DEFAULT_GOLD_PATH = Path("data/eval/gold.json")

# 生产放行 / score 路径（扫描金标不得作放行特征）
PRODUCTION_RELEASE_SCAN_PATHS: tuple[str, ...] = (
    "src/freshlatch/publish_hook.py",
    "src/freshlatch/prepublish.py",
    "src/freshlatch/evidence_bound.py",
    "src/freshlatch/disposition.py",
    "src/freshlatch/sheet.py",
    "src/freshlatch/claim_ledger.py",
    "src/freshlatch/export",
    "src/freshlatch/ui/app.py",
)

# 禁止出现在生产放行路径中的金标放行特征子串
_FORBIDDEN_GOLD_RELEASE_MARKERS: tuple[str, ...] = (
    "gold.json",
    "load_gold",
    "must_stale",
    "must_fresh",
    "must_unknown",
    "must_quarantine",
    "must_fresh_distractor",
)


# ---------------------------------------------------------------------------
# Gold 只读
# ---------------------------------------------------------------------------


def load_gold_readonly(path: str | Path = DEFAULT_GOLD_PATH) -> dict[str, Any]:
    """只读加载金标；本模块不写回、不改文件。"""
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "must_stale" not in data:
        raise ValueError(f"金标缺少 must_stale 桶: {p}")
    return data


# ---------------------------------------------------------------------------
# D1 — must_stale multi-run（离线评测）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MustStaleRunHit:
    """单遍 must_stale 命中摘要。"""

    run: int
    hits: int
    total: int
    misses: tuple[str, ...]  # claim_id 未命中（非 stale）
    meets_floor: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class D1MultiRunSummary:
    """D1 must_stale multi-run 汇总（离线评测层）。"""

    layer: str = LAYER_OFFLINE_EVAL
    n_runs: int = 0
    must_stale_ids: list[str] = field(default_factory=list)
    gold_floor_id: str = GOLD_FLOOR_ID
    gold_floor_statement: str = GOLD_FLOOR_STATEMENT
    per_run: list[MustStaleRunHit] = field(default_factory=list)
    pass_at_k: dict[str, int] = field(default_factory=dict)
    runs_meeting_floor: int = 0
    meets_floor_all_runs: bool = False
    report_population_variance: bool = False
    variance_note: str = ""
    source: str = ""  # smoke_fixture | gold_run_report | decisions

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "n_runs": self.n_runs,
            "must_stale_ids": list(self.must_stale_ids),
            "gold_floor_id": self.gold_floor_id,
            "gold_floor_statement": self.gold_floor_statement,
            "per_run": [r.to_dict() for r in self.per_run],
            "pass_at_k": dict(self.pass_at_k),
            "runs_meeting_floor": self.runs_meeting_floor,
            "meets_floor_all_runs": self.meets_floor_all_runs,
            "report_population_variance": self.report_population_variance,
            "variance_note": self.variance_note,
            "source": self.source,
        }


def _variance_policy(n_runs: int) -> tuple[bool, str]:
    """n 小时不报总体方差；达阈值才允许方差字段（本出口仍默认不报）。"""
    if n_runs < VARIANCE_REPORT_MIN_N:
        return (
            False,
            (
                f"n={n_runs} < {VARIANCE_REPORT_MIN_N}：框定为冒烟检查，"
                "不报总体方差（非统计测量）。"
            ),
        )
    return (
        False,
        (
            f"n={n_runs} 已达记录阈值，本出口仍只报 pass@k 与门比对，"
            "不报总体方差（防假信心）。"
        ),
    )


def summarize_must_stale_multirun(
    gold: Mapping[str, Any],
    per_run_decisions: Sequence[Mapping[str, str]],
    *,
    source: str = "decisions",
) -> D1MultiRunSummary:
    """从多遍 {claim_id: status} 汇总 must_stale 命中与金标门。

    期望判定固定为 stale（与 eval.matrix.EXPECTED_VERDICT 对齐）。
    """
    must_stale = list(gold["must_stale"])
    expected = EXPECTED_VERDICT["must_stale"]
    n_runs = len(per_run_decisions)
    report_var, var_note = _variance_policy(n_runs)

    per_run: list[MustStaleRunHit] = []
    pass_at_k: dict[str, int] = {cid: 0 for cid in must_stale}

    for idx, decisions in enumerate(per_run_decisions, start=1):
        hits = 0
        misses: list[str] = []
        for cid in must_stale:
            predicted = decisions.get(cid, "missing")
            if predicted == expected:
                hits += 1
                pass_at_k[cid] += 1
            else:
                misses.append(cid)
        meets = hits == len(must_stale)
        per_run.append(
            MustStaleRunHit(
                run=idx,
                hits=hits,
                total=len(must_stale),
                misses=tuple(misses),
                meets_floor=meets,
            )
        )

    runs_ok = sum(1 for r in per_run if r.meets_floor)
    return D1MultiRunSummary(
        layer=LAYER_OFFLINE_EVAL,
        n_runs=n_runs,
        must_stale_ids=must_stale,
        per_run=per_run,
        pass_at_k=pass_at_k,
        runs_meeting_floor=runs_ok,
        meets_floor_all_runs=runs_ok == n_runs and n_runs > 0,
        report_population_variance=report_var,
        variance_note=var_note,
        source=source,
    )


def smoke_multirun_decisions(
    gold: Mapping[str, Any],
    *,
    n_runs: int = DEFAULT_MULTI_RUN_N,
    inject_miss_run: int | None = None,
    inject_miss_claim: str | None = None,
) -> list[dict[str, str]]:
    """构造离线冒烟用 multi-run 判定（不调 LLM；默认全命中金标门）。

    inject_miss_* 仅供单测制造掉门样本。
    """
    if n_runs < 1:
        raise ValueError("n_runs 须 >= 1")
    expected = EXPECTED_VERDICT["must_stale"]
    out: list[dict[str, str]] = []
    for i in range(1, n_runs + 1):
        row = {cid: expected for cid in gold["must_stale"]}
        if inject_miss_run == i and inject_miss_claim:
            row[inject_miss_claim] = "fresh"
        out.append(row)
    return out


def summarize_from_gold_run_report(raw: Mapping[str, Any], gold: Mapping[str, Any]) -> D1MultiRunSummary:
    """从既有 gold_run 报告 JSON（eval.runner 产出）提取 D1 汇总。"""
    if raw.get("kind") != "gold_run":
        raise ValueError(f"期望 kind=gold_run，得到 {raw.get('kind')!r}")
    per_run = raw.get("per_run") or []
    decisions = [r.get("decisions") or {} for r in per_run]
    return summarize_must_stale_multirun(gold, decisions, source="gold_run_report")


def format_d1_report(summary: D1MultiRunSummary) -> str:
    """人读 D1 报告；文首标明离线评测层；n 小时不报总体方差。"""
    lines = [
        f"【{summary.layer}】SLO-07 D1 must_stale multi-run",
        "",
        f"- 层身份: {summary.layer}（金标不得进生产 score / 在线放行）",
        f"- 运行遍数 n = {summary.n_runs}（写死于命令/文档；默认 {DEFAULT_MULTI_RUN_N}）",
        f"- 金标门: {summary.gold_floor_statement}",
        f"- 金标门 id: {summary.gold_floor_id}",
        f"- 来源: {summary.source}",
        f"- 方差纪律: {summary.variance_note}",
        f"- report_population_variance: {summary.report_population_variance}",
        "",
        "## must_stale 命中汇总（条数；不报百分比）",
        "",
        "| run | hits/total | 是否过门 | 漏判 |",
        "|---|---|---|---|",
    ]
    for r in summary.per_run:
        miss = ", ".join(r.misses) if r.misses else "无"
        floor = "是" if r.meets_floor else "否"
        lines.append(f"| {r.run} | {r.hits}/{r.total} | {floor} | {miss} |")
    lines += [
        "",
        "## per-claim 命中次数/n（pass@k；冒烟不报总体方差）",
        "",
        "| claim_id | 命中/n |",
        "|---|---|",
    ]
    for cid in summary.must_stale_ids:
        lines.append(f"| {cid} | {summary.pass_at_k.get(cid, 0)}/{summary.n_runs} |")
    lines += [
        "",
        f"- 过门遍数: {summary.runs_meeting_floor}/{summary.n_runs}",
        f"- 全部过门: {'是' if summary.meets_floor_all_runs else '否'}",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# D3 — 挂接 SLO-02 同一出口
# ---------------------------------------------------------------------------


def d3_from_hard_gate_report(report: HardGateReport) -> dict[str, Any]:
    """从 SLO-02 HardGateReport 抽出 D3 字段（同一 week_fields 出口）。"""
    fields = report.week_fields()
    return {
        "layer": LAYER_HARD_GATE,
        "slo_id": "D3",
        "source_module": "freshlatch.slo_hard_gate_violations",
        "same_exit_as": "SLO-02",
        "target_violations": 0,
        "violations": fields["hard_gate_violation_counts"].get("D3", 0),
        "blocks": fields["hard_gate_block_counts"].get("D3", 0),
        "hard_gate_violation_counts": fields["hard_gate_violation_counts"],
        "note": "无 T1 绿灯违例目标=0；计数语义与 SLO-02 仪表同一出口，勿另造冲突语义。",
    }


def run_d3_via_slo02(*, tmp_events_dir: Path | None = None) -> dict[str, Any]:
    """跑 SLO-02 Acceptance 探针并返回 D3 挂接视图。"""
    if tmp_events_dir is None:
        with tempfile.TemporaryDirectory(prefix="slo07-d3-") as tmp:
            report = run_acceptance_probes(tmp_events_dir=Path(tmp))
            return d3_from_hard_gate_report(report)
    report = run_acceptance_probes(tmp_events_dir=tmp_events_dir)
    return d3_from_hard_gate_report(report)


# ---------------------------------------------------------------------------
# D4 — 包结论三值分布（观测）
# ---------------------------------------------------------------------------


@dataclass
class D4Distribution:
    """D4 包结论分布周报字段。"""

    layer: str = LAYER_WATCH
    total_runs: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    ratios: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "total_runs": self.total_runs,
            "counts": dict(self.counts),
            "ratios": dict(self.ratios),
            "labels": sorted(DISPOSITIONS),
        }


def distribute_dispositions(dispositions: Iterable[Disposition | str]) -> D4Distribution:
    """聚合一组 Run 级 disposition → 可发/需补丁/勿发 计数与占比。"""
    counts = Counter({d: 0 for d in sorted(DISPOSITIONS)})
    total = 0
    for d in dispositions:
        if d not in DISPOSITIONS:
            raise ValueError(f"非法 disposition: {d!r}（仅三值）")
        counts[d] += 1
        total += 1
    ratios = {
        k: (counts[k] / total if total else 0.0) for k in sorted(DISPOSITIONS)
    }
    return D4Distribution(
        layer=LAYER_WATCH,
        total_runs=total,
        counts=dict(counts),
        ratios=ratios,
    )


def distribute_from_claim_batches(
    batches: Sequence[Sequence[ClaimDispositionInput]],
) -> D4Distribution:
    """只读调用 disposition.aggregate_disposition，再聚合 D4 分布。"""
    dispositions = [aggregate_disposition(batch) for batch in batches]
    return distribute_dispositions(dispositions)


def format_d4_report(dist: D4Distribution) -> str:
    lines = [
        f"【{dist.layer}】SLO-07 D4 包结论三值分布",
        "",
        f"- 层身份: {dist.layer}（周报；本波不作 Gate 生死）",
        f"- Run 总数: {dist.total_runs}",
        "",
        "| 包结论 | 计数 | 占比 |",
        "|---|---|---|",
    ]
    for label in sorted(DISPOSITIONS):
        c = dist.counts.get(label, 0)
        r = dist.ratios.get(label, 0.0)
        lines.append(f"| {label} | {c} | {r:.2%} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 防火墙：生产路径不得读金标作放行特征
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoldFirewallHit:
    path: str
    marker: str
    line: int
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldFirewallScan:
    """生产放行/score 路径金标隔离扫描结果。"""

    ok: bool = True
    scanned_files: list[str] = field(default_factory=list)
    hits: list[GoldFirewallHit] = field(default_factory=list)
    note: str = (
        "金标（gold.json / must_* 桶标签）不得作为生产 score 或在线放行特征；"
        "离线评测仅允许在 eval/ 与本观测出口。"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "scanned_files": list(self.scanned_files),
            "hits": [h.to_dict() for h in self.hits],
            "note": self.note,
        }


def _iter_py_files(root: Path, rel: str) -> list[Path]:
    target = root / rel
    if target.is_file() and target.suffix == ".py":
        return [target]
    if target.is_dir():
        return sorted(p for p in target.rglob("*.py") if p.is_file())
    return []


def _line_is_comment_or_doc_noise(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def scan_production_paths_no_gold_release(
    repo_root: str | Path = ".",
) -> GoldFirewallScan:
    """扫描生产放行/score 相关路径：不得出现金标放行特征。

    用源码文本扫描（含 AST 字符串常量）；命中即失败。
    """
    root = Path(repo_root).resolve()
    scan = GoldFirewallScan()
    for rel in PRODUCTION_RELEASE_SCAN_PATHS:
        for path in _iter_py_files(root, rel):
            rel_s = str(path.relative_to(root)).replace("\\", "/")
            scan.scanned_files.append(rel_s)
            text = path.read_text(encoding="utf-8")
            # 字符串常量（含 docstring）也会被扫到——生产模块不应嵌入金标路径/桶名
            for i, line in enumerate(text.splitlines(), start=1):
                if _line_is_comment_or_doc_noise(line):
                    # 注释里提及纪律词可接受；但 gold.json / load_gold 即便在注释也危险，仍拦
                    comment_only_soft = ("must_stale", "must_fresh", "must_unknown")
                    for marker in _FORBIDDEN_GOLD_RELEASE_MARKERS:
                        if marker not in line:
                            continue
                        if line.lstrip().startswith("#") and marker in comment_only_soft:
                            continue
                        if marker in line:
                            scan.hits.append(
                                GoldFirewallHit(
                                    path=rel_s,
                                    marker=marker,
                                    line=i,
                                    snippet=line.strip()[:160],
                                )
                            )
                    continue
                for marker in _FORBIDDEN_GOLD_RELEASE_MARKERS:
                    if marker in line:
                        scan.hits.append(
                            GoldFirewallHit(
                                path=rel_s,
                                marker=marker,
                                line=i,
                                snippet=line.strip()[:160],
                            )
                        )
            # AST 再扫字符串字面量（防拆行拼接漏网时至少抓住常量）
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    for marker in _FORBIDDEN_GOLD_RELEASE_MARKERS:
                        if marker in node.value:
                            scan.hits.append(
                                GoldFirewallHit(
                                    path=rel_s,
                                    marker=marker,
                                    line=getattr(node, "lineno", 0) or 0,
                                    snippet=node.value[:160],
                                )
                            )
    # 去重
    seen: set[tuple[str, str, int]] = set()
    uniq: list[GoldFirewallHit] = []
    for h in scan.hits:
        key = (h.path, h.marker, h.line)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    scan.hits = uniq
    scan.ok = len(scan.hits) == 0
    return scan


# ---------------------------------------------------------------------------
# 组合周报 / Acceptance
# ---------------------------------------------------------------------------


def build_week_observability(
    *,
    gold_path: str | Path = DEFAULT_GOLD_PATH,
    n_runs: int = DEFAULT_MULTI_RUN_N,
    gold_run_report: Mapping[str, Any] | None = None,
    disposition_batches: Sequence[Sequence[ClaimDispositionInput]] | None = None,
    dispositions: Sequence[Disposition | str] | None = None,
    repo_root: str | Path = ".",
    tmp_events_dir: Path | None = None,
) -> dict[str, Any]:
    """组装 D1+D3+D4+防火墙一周最小可勾选包。"""
    gold = load_gold_readonly(gold_path)
    if gold_run_report is not None:
        d1 = summarize_from_gold_run_report(gold_run_report, gold)
    else:
        decisions = smoke_multirun_decisions(gold, n_runs=n_runs)
        d1 = summarize_must_stale_multirun(gold, decisions, source="smoke_fixture")

    d3 = run_d3_via_slo02(tmp_events_dir=tmp_events_dir)

    if disposition_batches is not None:
        d4 = distribute_from_claim_batches(disposition_batches)
    elif dispositions is not None:
        d4 = distribute_dispositions(dispositions)
    else:
        # 冒烟默认：三类各一，证明分布出口
        d4 = distribute_dispositions(["可发", "需补丁", "勿发"])

    firewall = scan_production_paths_no_gold_release(repo_root)

    return {
        "kind": "slo07_week_observability",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "layer_banner": (
            f"D1={LAYER_OFFLINE_EVAL}; D3={LAYER_HARD_GATE}(SLO-02 同出口); "
            f"D4={LAYER_WATCH}"
        ),
        "d1": d1.to_dict(),
        "d3": d3,
        "d4": d4.to_dict(),
        "gold_firewall": firewall.to_dict(),
        "commands": {
            "offline_multirun_doc": (
                f"python scripts/slo_d1_d4_observability.py --runs {DEFAULT_MULTI_RUN_N}"
            ),
            "full_llm_gold_eval": (
                f"python -m freshlatch.eval run --gold data/eval/gold.json "
                f"--runs {DEFAULT_MULTI_RUN_N}"
            ),
            "slo02_hard_gate": "python scripts/slo_hard_gate_violations.py",
        },
    }


def format_week_report(payload: Mapping[str, Any]) -> str:
    """人读组合周报。"""
    d1 = D1MultiRunSummary(
        layer=payload["d1"]["layer"],
        n_runs=payload["d1"]["n_runs"],
        must_stale_ids=list(payload["d1"]["must_stale_ids"]),
        gold_floor_id=payload["d1"]["gold_floor_id"],
        gold_floor_statement=payload["d1"]["gold_floor_statement"],
        per_run=[MustStaleRunHit(**r) for r in payload["d1"]["per_run"]],
        pass_at_k=dict(payload["d1"]["pass_at_k"]),
        runs_meeting_floor=payload["d1"]["runs_meeting_floor"],
        meets_floor_all_runs=payload["d1"]["meets_floor_all_runs"],
        report_population_variance=payload["d1"]["report_population_variance"],
        variance_note=payload["d1"]["variance_note"],
        source=payload["d1"]["source"],
    )
    d4 = D4Distribution(
        layer=payload["d4"]["layer"],
        total_runs=payload["d4"]["total_runs"],
        counts=dict(payload["d4"]["counts"]),
        ratios=dict(payload["d4"]["ratios"]),
    )
    d3 = payload["d3"]
    fw = payload["gold_firewall"]
    lines = [
        "SLO-07 复验主业观测周报（D1 · D3 · D4）",
        "",
        f"- 层身份条幅: {payload['layer_banner']}",
        f"- recorded_at: {payload.get('recorded_at', '')}",
        "",
        format_d1_report(d1).rstrip(),
        "",
        "【硬闸】D3 无 T1 绿灯=0（SLO-02 同一出口）",
        "",
        f"- source: {d3.get('source_module')} / {d3.get('same_exit_as')}",
        f"- D3 violations: {d3.get('violations')}（目标 {d3.get('target_violations')}）",
        f"- D3 blocks: {d3.get('blocks')}",
        f"- note: {d3.get('note')}",
        "",
        format_d4_report(d4).rstrip(),
        "",
        "【防火墙】生产放行/score 路径金标隔离",
        "",
        f"- ok: {fw.get('ok')}",
        f"- scanned_files: {len(fw.get('scanned_files') or [])}",
        f"- hits: {len(fw.get('hits') or [])}",
        f"- note: {fw.get('note')}",
        "",
    ]
    return "\n".join(lines) + "\n"


def acceptance_ok(payload: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Acceptance 机检：D1 冒烟过门 · D3=0 · D4 三值齐全可观察 · 防火墙绿。"""
    errors: list[str] = []
    d1 = payload.get("d1") or {}
    if d1.get("layer") != LAYER_OFFLINE_EVAL:
        errors.append("D1 层身份非离线评测层")
    if d1.get("report_population_variance") is True and d1.get("n_runs", 0) < VARIANCE_REPORT_MIN_N:
        errors.append("n 小时不得报总体方差")
    if not d1.get("meets_floor_all_runs"):
        errors.append("D1 未全部过金标门（冒烟 fixture 应过门）")
    d3 = payload.get("d3") or {}
    if d3.get("same_exit_as") != "SLO-02":
        errors.append("D3 未挂接 SLO-02 同一出口")
    if d3.get("violations", 1) != 0:
        errors.append(f"D3 violations != 0: {d3.get('violations')}")
    d4 = payload.get("d4") or {}
    labels = set((d4.get("counts") or {}).keys())
    if labels != set(DISPOSITIONS):
        errors.append(f"D4 标签不完整: {labels}")
    if (d4.get("total_runs") or 0) < 1:
        errors.append("D4 无样本")
    fw = payload.get("gold_firewall") or {}
    if not fw.get("ok"):
        errors.append(f"金标防火墙命中: {fw.get('hits')}")
    return (len(errors) == 0, errors)
