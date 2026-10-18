"""Auditor 判定臂离线评测 harness(I-08,决议 #691 / 票 #697)。

评测对象 = 生产判定路径的判定臂:生产 ``Auditor``(freshness_audit 教义注入,
qwen-flash temperature=0)+ 生产落档真值表(``arbitrate_stale_mark`` /
``arbitrate_fresh``)的闸后 status。**只测不调参**:本模块不改生产模型 /
temperature / SLO 门槛,不上产品 UI,禁 RESULT-Y / L4 话术。

实验设计(单一路径设计,全样本自包含于金标 JSON):
- gold=stale 样本走 ``mark_stale`` 路径:Lead 以 T1 锚段落提交反证包,
  期望 Auditor 判 stale(维度相符)或 dimension_match=false 被闸打回 unknown;
- gold=fresh 样本走 ``fresh_attempt`` 路径:Lead 以 T1 支持性证据提交 fresh 包,
  期望 Auditor 双判一致判 fresh;
- gold=unknown 样本走 ``fresh_attempt`` 路径但证据包无 T1 覆盖,
  期望 Auditor 按教义(无 T1 → 不猜)判 unknown;
- sensitivity 桶(#21 乙-i 维度混淆探针 c13/c14)单列附表,不进判分矩阵,不计通过线。

层级声明(Anthropic 纪律 #1):混淆矩阵报条数优先、率随行(小样本率遮丑,#8 口径);
n=12 的矩阵是**冒烟层读数**,不得冒充 ≥100 金标的统计结论——样本量协议节如实登记。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from freshlatch.eval.matrix import VERDICTS
from freshlatch.gates.rule_gate import arbitrate_fresh, arbitrate_stale_mark
from freshlatch.llm import DecodingParams
from freshlatch.models import Claim
from freshlatch.roles.auditor import EVIDENCE_PACKET_SCHEMA_VERSION, Auditor, AuditorVerdict
from freshlatch.store.ingest import parse_document

GOLD_SCHEMA_VERSION = "1"

PATH_MARK_STALE = "mark_stale"
PATH_FRESH_ATTEMPT = "fresh_attempt"
PATHS = (PATH_MARK_STALE, PATH_FRESH_ATTEMPT)

BUCKET_MATRIX = "matrix"
BUCKET_SENSITIVITY = "sensitivity"
BUCKETS = (BUCKET_MATRIX, BUCKET_SENSITIVITY)

# 决议 #691 样本量门槛:≥100(其中 ≥30 真人复审)。未达标时报告必须携带协议说明。
DEFAULT_THRESHOLDS = {"min_total": 100, "min_human": 30}
DEFAULT_PROTOCOL_NOTE = (
    "样本量协议(I-08,决议 #691):既有 must_* 人工金标池 = 12 条判分 + 2 条干扰项敏感度探针"
    "(W5–W8 / #21 人工因果链策展,human_curated=true)。扩至 ≥100(≥30 真人复审)需新一轮 "
    "Trust L1 人审排期:新样本需要新 T1 语料 + 人工因果链标注 + 抽检员复审,不是 Exit/harness "
    "票内能诚实在一夜之间造出的。本期先立 Auditor 判定臂测量尺,交付全人工策展样本的真实读数;"
    "扩池挂后续工单,绝不伪造/合成样本充数(防假绿)。"
)

# 冻结证据锚:拒绝写入(与 retrieve_eval / temporal_trained 等既有 sibling 同纪律)。
FROZEN_EVIDENCE_DIRS = (
    "docs/evidence/l4-ev-01-arm-table",
    "docs/evidence/temporal-trained-retrieval",
    "docs/evidence/patch-establishment",
)

REPRO_NOTE = (
    "判定臂层(Auditor 单轮判定)给定解码参数(temperature=0 同证据包同判定)逐位复现;"
    "托管端点在漂移,跨会话复现只能近似,此限制为留档声明。"
    "闸后落档经生产真值表(纯函数)逐位复现。"
)


@dataclass
class AuditorArmSample:
    """一条判定臂金标样本:主张 + Lead 证据包引用 + 期望档 + 人审来历。"""

    sample_id: str
    claim_id: str
    statement: str
    dimension: str | None
    t0_evidence_ids: list[str]
    bucket: str            # matrix | sensitivity
    path: str              # mark_stale | fresh_attempt
    gold: str              # fresh | stale | unknown
    human_curated: bool
    provenance: str
    lead_status: str       # fresh | stale(Lead 试图落的判定)
    lead_reason: str
    lead_evidence_ids: list[str]


@dataclass
class AuditorArmGold:
    samples: list[AuditorArmSample]
    thresholds: dict = field(default_factory=lambda: dict(DEFAULT_THRESHOLDS))
    protocol_note: str = DEFAULT_PROTOCOL_NOTE
    schema_version: str = GOLD_SCHEMA_VERSION


def _validate_sample(raw: dict) -> AuditorArmSample:
    missing = [k for k in ("sample_id", "claim_id", "statement", "bucket", "path", "gold",
                           "human_curated", "lead_status", "lead_reason",
                           "lead_evidence_ids") if k not in raw]
    if missing:
        raise ValueError(f"金标样本缺字段 {missing}: {raw.get('sample_id')!r}")
    gold = raw["gold"]
    if gold not in VERDICTS:
        raise ValueError(f"样本 {raw['sample_id']}: gold={gold!r} 非法(须为 {VERDICTS})")
    path = raw["path"]
    if path not in PATHS:
        raise ValueError(f"样本 {raw['sample_id']}: path={path!r} 非法(须为 {PATHS})")
    bucket = raw["bucket"]
    if bucket not in BUCKETS:
        raise ValueError(f"样本 {raw['sample_id']}: bucket={bucket!r} 非法(须为 {BUCKETS})")
    if raw["lead_status"] not in ("fresh", "stale"):
        raise ValueError(f"样本 {raw['sample_id']}: lead_status={raw['lead_status']!r} 非法")
    ids = raw["lead_evidence_ids"]
    if not isinstance(ids, list) or not all(isinstance(e, str) for e in ids):
        raise ValueError(f"样本 {raw['sample_id']}: lead_evidence_ids 须为字符串列表")
    # 路径 × 金标一致性(matrix 桶硬校验;sensitivity 桶是维度混淆探针,允许反例形态)
    if bucket == BUCKET_MATRIX:
        if path == PATH_MARK_STALE and gold != "stale":
            raise ValueError(f"样本 {raw['sample_id']}: mark_stale 路径(matrix 桶)只能配 gold='stale'")
        if path == PATH_FRESH_ATTEMPT and gold not in ("fresh", "unknown"):
            raise ValueError(f"样本 {raw['sample_id']}: fresh_attempt 路径只能配 gold='fresh'/'unknown'")
    if path == PATH_MARK_STALE and not ids:
        raise ValueError(f"样本 {raw['sample_id']}: mark_stale 路径必须给反证 evidence ids")
    if path == PATH_FRESH_ATTEMPT and bucket == BUCKET_MATRIX \
            and gold == "fresh" and not ids:
        raise ValueError(f"样本 {raw['sample_id']}: fresh_attempt + gold='fresh' 必须给支持性证据 ids")
    return AuditorArmSample(
        sample_id=raw["sample_id"], claim_id=raw["claim_id"],
        statement=str(raw["statement"]), dimension=raw.get("dimension"),
        t0_evidence_ids=list(raw.get("t0_evidence_ids") or []),
        bucket=bucket, path=path, gold=gold,
        human_curated=bool(raw["human_curated"]),
        provenance=str(raw.get("provenance", "")),
        lead_status=raw["lead_status"], lead_reason=str(raw["lead_reason"]),
        lead_evidence_ids=list(ids),
    )


def load_auditor_arm_gold(path: str | Path) -> AuditorArmGold:
    """加载判定臂金标池;schema/口径校验失败即拒绝(假绿防线,不静默吞)。"""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("kind") != "auditor_arm_gold":
        raise ValueError(f"{path}: kind 须为 'auditor_arm_gold'")
    if data.get("schema_version") != GOLD_SCHEMA_VERSION:
        raise ValueError(f"{path}: schema_version 须为 '{GOLD_SCHEMA_VERSION}'")
    raw_samples = data.get("samples")
    if not isinstance(raw_samples, list) or not raw_samples:
        raise ValueError(f"{path}: samples 须为非空列表")
    samples = [_validate_sample(s) for s in raw_samples]
    ids = [s.sample_id for s in samples]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: sample_id 重复: {sorted(ids)}")
    thresholds = data.get("thresholds") or dict(DEFAULT_THRESHOLDS)
    return AuditorArmGold(
        samples=samples,
        thresholds={"min_total": int(thresholds["min_total"]),
                    "min_human": int(thresholds["min_human"])},
        protocol_note=str(data.get("protocol_note") or DEFAULT_PROTOCOL_NOTE),
        schema_version=GOLD_SCHEMA_VERSION,
    )


def load_t1_texts(corpus_t1_dir: str | Path) -> dict[str, str]:
    """解析 T1 语料为 ``{doc_id}#{anchor}@T1 -> 块文本``。

    复用生产 ingest 单一真相(frontmatter + ## pN 切块),不自写解析器;
    块文本含 ``## pN`` 头,与生产检索返回给 Auditor 的块文本同构。
    """
    out: dict[str, str] = {}
    for md in sorted(Path(corpus_t1_dir).glob("*.md")):
        _, chunks = parse_document(md)
        for ch in chunks:
            out[f"{ch.doc_id}#{ch.clause_id}@{ch.as_of}"] = ch.text
    if not out:
        raise ValueError(f"{corpus_t1_dir}: 未解析到任何 T1 块")
    return out


def validate_samples_against_texts(samples: list[AuditorArmSample],
                                   t1_texts: dict[str, str]) -> None:
    """样本引用的证据 id 必须全部在 T1 语料可解析;缺一个即拒绝(不静默降级)。"""
    missing = [(s.sample_id, e) for s in samples for e in s.lead_evidence_ids
               if e not in t1_texts]
    if missing:
        raise ValueError(f"lead_evidence_ids 在 T1 语料不可解析: {missing}")


def post_gate(sample: AuditorArmSample, verdict: AuditorVerdict) -> tuple[str, bool]:
    """闸后落档状态 + 是否挂异议:按样本路径走生产真值表(不复制逻辑)。"""
    if sample.path == PATH_MARK_STALE:
        return arbitrate_stale_mark(verdict.status, verdict.dimension_match)
    return arbitrate_fresh(verdict.status), False


def run_auditor_arm(
    samples: list[AuditorArmSample],
    llm,
    *,
    doctrine: str | None,
    decoding: DecodingParams | None,
    t1_texts: dict[str, str],
    thresholds: dict | None = None,
    protocol_note: str = DEFAULT_PROTOCOL_NOTE,
    gold_path: str | None = None,
) -> dict:
    """逐样本跑生产 Auditor 判定 + 生产闸后落档,返回 raw dict(报告唯一原料)。

    doctrine=None 是教义加载失败的显式形态:判定仍按兜底人格执行,
    但每条记录落 ``skill_fallback`` 事件(不静默降级,与生产 Runner 同纪律)。
    """
    decoding = decoding or DecodingParams()
    auditor = Auditor(llm, doctrine=doctrine)
    records: list[dict] = []
    for s in samples:
        claim = Claim(claim_id=s.claim_id, statement=s.statement,
                      t0_evidence_ids=list(s.t0_evidence_ids), dimension=s.dimension)
        packet = auditor.build_packet(
            claim, lead_status=s.lead_status, lead_reason=s.lead_reason,
            lead_evidence_ids=list(s.lead_evidence_ids), evidence_texts=t1_texts,
        )
        verdict = auditor.judge(packet, decoding=decoding)
        gated_status, dissent = post_gate(s, verdict)
        records.append({
            "sample_id": s.sample_id,
            "claim_id": s.claim_id,
            "bucket": s.bucket,
            "path": s.path,
            "gold": s.gold,
            "human_curated": s.human_curated,
            "provenance": s.provenance,
            "lead_evidence_ids": list(s.lead_evidence_ids),
            "auditor_status": verdict.status,
            "auditor_reason": verdict.reason,
            "auditor_dimension_match": verdict.dimension_match,
            "gated_status": gated_status,
            "dissent": dissent,
            "skill_fallback": doctrine is None,
            "evidence_packet_schema": verdict.schema_version or EVIDENCE_PACKET_SCHEMA_VERSION,
        })
    th = dict(DEFAULT_THRESHOLDS if thresholds is None else thresholds)
    return {
        "kind": "auditor_arm_run",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "decoding": decoding.__dict__,
        "doctrine_loaded": doctrine is not None,
        "gold_path": gold_path,
        "thresholds": th,
        "protocol_note": protocol_note,
        "records": records,
        "evidence_packet_schema": EVIDENCE_PACKET_SCHEMA_VERSION,
        "repro_note": REPRO_NOTE,
    }


def arm_confusion(raw: dict) -> dict:
    """3×3 混淆矩阵(金标行 × 判定列)+ false-accept / false-reject + unknown 率。

    判分口径:仅 matrix 桶(12 条);sensitivity 桶单列附表,不进矩阵不计通过线(#21)。
    false-accept = 金标 stale → 闸后 fresh;false-reject = 金标 fresh → 闸后 stale;
    unknown 率 = 闸后 unknown 条数 / n。条数为主,率随行(n=12 是冒烟层读数,不冒充统计结论)。
    """
    matrix_records = [r for r in raw["records"] if r["bucket"] == BUCKET_MATRIX]
    n = len(matrix_records)
    human_records = [r for r in matrix_records if r["human_curated"]]
    gated_matrix: dict[str, dict[str, int]] = {g: {v: 0 for v in VERDICTS} for g in VERDICTS}
    human_matrix: dict[str, dict[str, int]] = {g: {v: 0 for v in VERDICTS} for g in VERDICTS}
    raw_matrix: dict[str, dict[str, int]] = {g: {v: 0 for v in VERDICTS} for g in VERDICTS}
    fa = fr = unk = 0
    for r in matrix_records:
        gated_matrix[r["gold"]][r["gated_status"]] += 1
        raw_matrix[r["gold"]][r["auditor_status"]] += 1
        if r["human_curated"]:
            human_matrix[r["gold"]][r["gated_status"]] += 1
        if r["gold"] == "stale" and r["gated_status"] == "fresh":
            fa += 1
        if r["gold"] == "fresh" and r["gated_status"] == "stale":
            fr += 1
        if r["gated_status"] == "unknown":
            unk += 1
    return {
        "n": n,
        "n_human": len(human_records),
        "gated_matrix": gated_matrix,
        "human_matrix": human_matrix,
        "raw_matrix": raw_matrix,
        "false_accept": {"count": fa, "rate": (fa / n) if n else 0.0},
        "false_reject": {"count": fr, "rate": (fr / n) if n else 0.0},
        "unknown_rate": {"count": unk, "rate": (unk / n) if n else 0.0},
        "sensitivity": {
            r["sample_id"]: r for r in raw["records"] if r["bucket"] == BUCKET_SENSITIVITY
        },
    }


_VERDICT_ZH = {"fresh": "fresh(活)", "stale": "stale(死)", "unknown": "unknown(未知)"}


def render_auditor_arm_report(raw: dict) -> str:
    m = arm_confusion(raw)
    th = raw["thresholds"]
    n_total = len(raw["records"])
    n_human = sum(1 for r in raw["records"] if r["human_curated"])
    size_ok = n_total >= th["min_total"] and n_human >= th["min_human"]
    d = raw["decoding"]
    lines: list[str] = [
        f"# Auditor 判定臂离线评测报告(I-08,{raw['recorded_at'][:10]})",
        "",
        "- 评测对象:生产判定臂——生产 `Auditor`(freshness_audit 教义注入,单轮 structured-output)"
        f" + 生产落档真值表闸后 status(模型 `{d['model']}`,非替身)",
        "- 只测不调参:生产模型 / temperature / SLO 门槛常量本期**未改**;不上产品 UI;"
        "禁 RESULT-Y / L4 话术。",
        f"- 复现条款:{raw['repro_note']}",
        "",
        "## 运行档案(decoding 逐运行入档,§4.7)",
        "",
        f"- 模型版本: `{d['model']}`",
        f"- temperature: `{d['temperature']}`",
        f"- seed: `{d['seed']}`",
        f"- 记录时间(UTC): {raw['recorded_at']}",
        f"- 教义注入: {'`skills/freshness_audit/SKILL.md`(加载成功)' if raw['doctrine_loaded'] else '**加载失败——兜底人格生效(不静默降级,逐样本落 skill_fallback)**'}",
        f"- Auditor 证据包 schema 版本: `{raw['evidence_packet_schema']}`",
        f"- 金标池: `{raw.get('gold_path')}`(schema `{GOLD_SCHEMA_VERSION}`)",
        "",
        "## 样本量与协议(决议 #691)",
        "",
        f"- 样本量: {n_total} 条(真人策展 {n_human} 条);门槛 ≥{th['min_total']}(其中 ≥{th['min_human']} 真人)。",
        f"- **达标: {'✅' if size_ok else '❌ 未达标'}**(协议已文档化,见下)",
        "",
        f"> {raw['protocol_note']}",
        "",
        "## 全量 vs 真人子集分栏(决议 #691;本期全量 ⊆ 真人策展,两栏重合)",
        "",
        f"- 全量 n={m['n']}(matrix 桶,判分口径);真人子集 n={m['n_human']}"
        "(human_curated=true,W5–W8/#21 人工因果链策展)。",
        "- 本期真人子集 = 全量;扩池引入非人审样本后,本表即成分栏判读(两栏分离)。",
        "",
        "| 金标 \\ 闸后 | 全量 fresh | 全量 stale | 全量 unknown | 真人 fresh | 真人 stale | 真人 unknown |",
        "|---|---|---|---|---|---|---|",
    ]
    for g in VERDICTS:
        full_row = m["gated_matrix"][g]
        hum_row = m["human_matrix"][g]
        lines.append(f"| {_VERDICT_ZH[g]} | {full_row['fresh']} | {full_row['stale']} "
                     f"| {full_row['unknown']} | {hum_row['fresh']} | {hum_row['stale']} "
                     f"| {hum_row['unknown']} |")
    lines += [
        "",
        "## 闸后 3×3 混淆矩阵(金标 × 落档 status;matrix 桶 12 条)",
        "",
        "| 金标 \\ 闸后 | fresh | stale | unknown |",
        "|---|---|---|---|",
    ]
    for g in VERDICTS:
        row = m["gated_matrix"][g]
        lines.append(f"| {_VERDICT_ZH[g]} | {row['fresh']} | {row['stale']} | {row['unknown']} |")
    lines += [
        "",
        f"- **false-accept**(金标 stale → 闸后 fresh): {m['false_accept']['count']} 条"
        f"({m['false_accept']['rate']:.1%})",
        f"- **false-reject**(金标 fresh → 闸后 stale): {m['false_reject']['count']} 条"
        f"({m['false_reject']['rate']:.1%})",
        f"- **unknown 率**(闸后 unknown / n): {m['unknown_rate']['count']}/{m['n']}"
        f"({m['unknown_rate']['rate']:.1%})",
        "",
        "> 与 #8 铁律的关系:报条数为判据、率仅随行参考(matrix.py「小样本不报百分比」"
        "口径不变);n=12 时率不具统计意义,阈值判读一律以条数为准。",
        "",
        "> 口径注:mark_stale 路径上 Auditor 判 fresh/unknown 不拦 stale(安全不对称,"
        "ADR-0010)——false-accept 在该路径结构性趋零是设计使然,不是测量豁免;"
        "判定臂自身的 fresh 误判见下方原始判定矩阵。",
        "",
        "## Auditor 原始判定 3×3(判定臂层读数;金标 × auditor verdict)",
        "",
        "| 金标 \\ 判定 | fresh | stale | unknown |",
        "|---|---|---|---|",
    ]
    for g in VERDICTS:
        row = m["raw_matrix"][g]
        lines.append(f"| {_VERDICT_ZH[g]} | {row['fresh']} | {row['stale']} | {row['unknown']} |")
    lines += [
        "",
        "> 层级声明(Anthropic 纪律 #1):n=12 为冒烟层读数,条数优先、率随行;"
        "不得冒充 ≥100 金标的统计结论。",
        "",
        "## 敏感度附表(乙-i 维度混淆探针:#21 c13 客单价≠毛利 / c14 覆盖率≠渗透率;"
        "不进判分矩阵,不计通过线)",
        "",
        "| sample_id | gold | auditor | dimension_match | 闸后落档 | 挂异议 |",
        "|---|---|---|---|---|---|",
    ]
    if not m["sensitivity"]:
        lines.append("| (无) |  |  |  |  |  |")
    for sid, r in sorted(m["sensitivity"].items()):
        dm = r["auditor_dimension_match"] if r["auditor_status"] == "stale" else None
        lines.append(f"| {sid} | {r['gold']} | {r['auditor_status']} | "
                     f"{'-' if dm is None else str(dm).lower()} | {r['gated_status']} "
                     f"| {'是' if r['dissent'] else '否'} |")
    lines += [
        "",
        "> 期望:Auditor 识破维度混淆——判 fresh,或 stale 但 dimension_match=false"
        "(经闸打回 unknown)。stale + dimension_match=true = 被干扰项骗过,归人工定性。",
        "",
        "## 每样本明细",
        "",
        "| sample_id | 桶 | 路径 | gold | auditor | dm | 闸后 | 异议 | fallback | 真人策展 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in raw["records"]:
        dm = r["auditor_dimension_match"] if r["auditor_status"] == "stale" else None
        lines.append(f"| {r['sample_id']} | {r['bucket']} | {r['path']} | {r['gold']} "
                     f"| {r['auditor_status']} | {'-' if dm is None else str(dm).lower()} "
                     f"| {r['gated_status']} | {'是' if r['dissent'] else '否'} "
                     f"| {'是' if r['skill_fallback'] else '否'} "
                     f"| {'是' if r['human_curated'] else '否'} |")
    lines += [
        "",
        "## 复现与漂移",
        "",
        f"- {raw['repro_note']}",
        "- 失败/异议条目归因人工定性;harness 只给机械矩阵,不判语义对错。",
        "",
    ]
    return "\n".join(lines)


def console_summary(raw: dict) -> str:
    m = arm_confusion(raw)
    return "\n".join([
        f"[auditor-arm] n={m['n']} model={raw['decoding']['model']} "
        f"temp={raw['decoding']['temperature']}",
        f"false-accept: {m['false_accept']['count']}; "
        f"false-reject: {m['false_reject']['count']}; "
        f"unknown 率: {m['unknown_rate']['count']}/{m['n']}",
        f"doctrine_loaded: {raw['doctrine_loaded']}",
    ])


def write_auditor_arm_outputs(raw: dict, out_dir: str | Path) -> tuple[Path, Path]:
    """报告 + raw JSON 双产出进 out_dir;冻结证据锚拒绝写入。"""
    out = Path(out_dir)
    posix = out.as_posix().replace("\\", "/").lstrip("./") \
        if not out.is_absolute() else out.as_posix().replace("\\", "/")
    for frozen in FROZEN_EVIDENCE_DIRS:
        if posix == frozen or posix.startswith(frozen + "/"):
            raise ValueError(f"冻结目录拒绝写入: {frozen}(报告落新 sibling,如 docs/evidence/auditor-arm-eval)")
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    md_path = out / f"auditor-arm-eval-{stamp}.md"
    json_path = out / f"auditor-arm-eval-{stamp}.json"
    if md_path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        md_path = out / f"auditor-arm-eval-{stamp}.md"
        json_path = out / f"auditor-arm-eval-{stamp}.json"
    md_path.write_text(render_auditor_arm_report(raw), encoding="utf-8")
    json_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    return md_path, json_path
