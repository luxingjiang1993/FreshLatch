"""C-04 正式针：qwen-flash 生成 + mDeBERTa NLI + T−C 固定-k 误放差。

口径：``docs/evidence/patch-establishment/PREREG.md`` Amendment-01/02。
须主人已明文「跑」且 CLI ``--authorize-run``。只写 patch-establishment/。
禁止 LM Studio。禁止 exact-match 冒充正式 NLI。不改 floors/gold/x1/生产臂。
``second_formal_y=false``。不得标 L5。
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_arms import Decoding, _append_arm_record, _generate_edit
from freshlatch.eval.patch_events_formal import ingested_t1
from freshlatch.eval.patch_events_generate import build_prompt
from freshlatch.eval.patch_events_metrics import (
    N_BOOT,
    SEED,
    _Col,
    _arm_block,
    _bootstrap_fixed,
    _release_positions_r,
    format_rate,
    named_streams,
)
from freshlatch.eval.patch_events_rows import reject_duplicate_claim_ids
from freshlatch.eval.patch_events_send import append_sent, dispatch_prompt, live_chat, written_keys
from freshlatch.eval.patch_events_verify import ENTAILMENT_TAU, XNLI_MODEL_ID, verify_edit
from freshlatch.eval.patch_establishment import (
    CONCLUSION_DIR,
    CRITERIA_NUMERIC_LINE,
    FROZEN_CORPUS_REL,
    HISTORICAL_RESULT_Y,
    PREREG_REL,
    RESULT_REL,
    SCHEMA_VERSION,
    FALSE_POSITIVE_IDS,
    STOP_IDS,
    _dump,
    _reject_banned,
    _reject_out_dir,
    build_scaffold,
    file_sha256,
)
from freshlatch.models import DEFAULT_MODEL, MODEL_REGISTRY, NLI_MODEL
from freshlatch.store.base import PRODUCTION_RETRIEVAL_MODE

LEVEL_MEASURED = "formal_measured"
RUN_STATUS_RAN = "ran"
MEASUREMENT_STATUS_MEASURED = "measured"
K_MIN = 10
SEND_TC: tuple[tuple[str, str], ...] = (("C", "rewrite"), ("T", "rewrite"))
GENERATIONS_NAME = "formal-generations.jsonl"
PRIMARY_JSON_NAME = "primary-tc.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def prereg_run_authorized(root: Path | None = None) -> bool:
    """预注册页须勾上主人明文「跑」，并含 Amendment-02。"""
    base = _repo_root() if root is None else Path(root)
    text = (base / PREREG_REL).read_text(encoding="utf-8")
    checked = bool(
        re.search(r"- \[x\] 主人明文「跑」", text)
        or "主人 Oriental Ronin 明文「跑」" in text
    )
    return checked and "Amendment-02" in text


def decoding_pin() -> dict[str, Any]:
    entry = MODEL_REGISTRY["default_llm"]
    return {
        "model": DEFAULT_MODEL,
        "registry_model": entry.model,
        "temperature": float(entry.temperature),
        "decoding_seed": SEED,
        "api_seed": None,
        "n_boot": N_BOOT,
        "k_min": K_MIN,
        "nli_model": NLI_MODEL,
        "nli_tau": ENTAILMENT_TAU,
    }


def load_formal_candidates(root: Path | None = None) -> list[dict[str, Any]]:
    """读冻结 CONSTRUCTED.jsonl 的 T 行；n=built_n，不得补到 100。"""
    base = _repo_root() if root is None else Path(root)
    path = base / FROZEN_CORPUS_REL / "CONSTRUCTED.jsonl"
    if not path.is_file():
        raise RuntimeError(f"缺冻结构造文件: {path.as_posix()}")
    split = json.loads((base / FROZEN_CORPUS_REL / "SPLIT.json").read_text(encoding="utf-8"))
    if split.get("second_formal_y") is not False:
        raise RuntimeError("second_formal_y 必须为 false")
    if int(split.get("target_n") or 0) != 100:
        raise RuntimeError("target_n 必须保持 100")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("arm") and row.get("arm") != "T":
            continue
        rows.append(row)
    reject_duplicate_claim_ids(rows)
    built = int(split.get("built_n") or 0)
    if len(rows) != built:
        raise RuntimeError(f"CONSTRUCTED T 行数 {len(rows)} ≠ built_n {built}")
    formal_ids = {str(item["claim_id"]) for item in split.get("formal") or []}
    got_ids = {str(row["claim_id"]) for row in rows}
    if got_ids != formal_ids:
        raise RuntimeError("CONSTRUCTED 与 SPLIT.formal 主张不一致")
    return rows


def generations_path(root: Path | None = None) -> Path:
    base = _repo_root() if root is None else Path(root)
    return base / CONCLUSION_DIR / GENERATIONS_NAME


def formal_tc_requests(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for row in rows:
        for arm, phase in SEND_TC:
            requests.append(
                {
                    "arm": arm,
                    "phase": phase,
                    "claim_id": row["claim_id"],
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
    return requests


def send_generations(
    *,
    root: Path | None = None,
    chat: Callable[..., Any] | None = None,
    authorize_run: bool = False,
) -> dict[str, Any]:
    """向 DashScope 发 C/T rewrite。可续跑。须 authorize。"""
    if not authorize_run:
        raise RuntimeError("拒绝发送：缺 --authorize-run")
    base = _repo_root() if root is None else Path(root)
    if not prereg_run_authorized(base):
        raise RuntimeError("拒绝发送：PREREG 未勾主人明文「跑」或缺 Amendment-02")
    if DEFAULT_MODEL != "qwen-flash":
        raise RuntimeError(f"正式针生成器必须是 qwen-flash，得 {DEFAULT_MODEL!r}")
    rows = load_formal_candidates(base)
    path = generations_path(base)
    _reject_out_dir(path.parent)
    done = written_keys(path)
    chat_fn = live_chat if chat is None else chat
    sent = 0
    prompt_tokens = 0
    completion_tokens = 0
    for request in formal_tc_requests(rows):
        key = (str(request["claim_id"]), str(request["arm"]), str(request["phase"]))
        if key in done:
            continue
        result = dispatch_prompt(request, chat_fn)
        if append_sent(path, result):
            done.add(key)
            sent += 1
    # usage is not always on append_sent records; cost estimated later from API if present
    return {
        "path": path.as_posix(),
        "sent_new": sent,
        "total_keys": len(done),
        "n_claims": len(rows),
        "decoding": decoding_pin(),
    }


def _saved_generator(generations: Sequence[Mapping[str, Any]]):
    index = {
        (str(item["claim_id"]), str(item["arm"]), str(item["phase"])): item
        for item in generations
    }

    def generate(request: Mapping[str, Any]) -> dict[str, Any]:
        key = (str(request["claim_id"]), str(request["arm"]), str(request["phase"]))
        item = index.get(key)
        if item is None:
            return {"void": True}
        field = str(item.get("output_field") or "")
        text = "" if item.get("text") is None else str(item["text"])
        if request["phase"] == "rewrite" and field == "after_text":
            out = {
                "after_text": text,
                "evidence_id": request.get("evidence_id", ""),
            }
            if "latency_ms" in item:
                out["latency_ms"] = item["latency_ms"]
            if "cost" in item:
                out["cost"] = item["cost"]
            return out
        return {"void": True}

    return generate


def run_arms_tc(
    candidates: Sequence[Mapping[str, Any]],
    *,
    generator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    verifier: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    decoding: Decoding,
    ingested_t1_ids: set[str],
) -> dict[str, Any]:
    """只跑 C 与 T。B1/B2 本针不发送。"""
    rows = [dict(item) for item in candidates]
    reject_duplicate_claim_ids(rows)
    records: dict[str, list[dict[str, Any]]] = {"C": [], "T": []}
    voids: list[dict[str, str]] = []
    if decoding.temperature is None or decoding.seed is None:
        for candidate in rows:
            for arm in ("C", "T"):
                voids.append(
                    {
                        "claim_id": str(candidate["claim_id"]),
                        "arm": arm,
                        "reason": "解码缺温度或种子",
                    }
                )
        return {**records, "voids": voids}

    for candidate in rows:
        claim_id = str(candidate["claim_id"])
        produced_c, failed_c, latency_c, cost_c = _generate_edit(
            "C", candidate, generator, decoding
        )
        if produced_c is None:
            voids.append({"claim_id": claim_id, "arm": "C", "reason": failed_c or "生成失败"})
        else:
            _append_arm_record(
                records,
                "C",
                candidate,
                produced_c,
                verifier=verifier,
                ingested=ingested_t1_ids,
                latency_ms=latency_c,
                cost=cost_c,
            )
        produced_t, failed_t, latency_t, cost_t = _generate_edit(
            "T", candidate, generator, decoding
        )
        if produced_t is None:
            voids.append({"claim_id": claim_id, "arm": "T", "reason": failed_t or "生成失败"})
        else:
            _append_arm_record(
                records,
                "T",
                candidate,
                produced_t,
                verifier=verifier,
                ingested=ingested_t1_ids,
                latency_ms=latency_t,
                cost=cost_t,
            )
    return {**records, "voids": voids}


def compare_tc(
    rows: Sequence[Mapping[str, Any]],
    *,
    ingested_t1_ids: set[str] | None = None,
    streams: Mapping[str, random.Random] | None = None,
    k_min: int = K_MIN,
) -> dict[str, Any]:
    """主比较只认 T−C。成立：点>0 且 95% 下界>0 且有定义（L1，非 Y 的 0.05）。"""
    ingested = set(ingested_t1_ids or ())
    grouped: dict[str, list[Mapping[str, Any]]] = {"C": [], "T": []}
    for row in rows:
        if row.get("ablation", "") != "":
            continue
        arm = str(row["arm"])
        if arm not in grouped:
            raise ValueError(f"C-04 主比较只收 C/T，得 {arm!r}")
        grouped[arm].append(row)
    missing = [arm for arm, items in grouped.items() if not items]
    if missing:
        raise ValueError(f"主比较缺臂: {', '.join(missing)}")
    columns = {arm: _Col(items, ingested) for arm, items in grouped.items()}
    if columns["C"].claim_id != columns["T"].claim_id:
        raise ValueError("C 的候选 id 与 T 不一致")
    reference = columns["T"]
    n = len(reference)
    if n == 0:
        raise ValueError("候选数为 0")
    k = sum(reference.release)
    rngs = streams if streams is not None else named_streams()
    if k < k_min:
        return {
            "k": k,
            "k_min": k_min,
            "n": n,
            "defined": False,
            "point": None,
            "ci95_low": None,
            "ci95_high": None,
            "established": False,
            "reason": f"T 自然放行数 k={k} < k_min={k_min}",
            "arms": {
                "T": _arm_block(columns["T"], None, k),
                "C": _arm_block(columns["C"], None, k),
            },
        }
    drawn = list(range(n))
    selected = {
        arm: _release_positions_r(drawn, col.release, col.claim_id, k)
        for arm, col in columns.items()
    }
    arms = {arm: _arm_block(col, selected[arm], k) for arm, col in columns.items()}
    false_release = _bootstrap_fixed(
        "误放率",
        reference,
        columns["C"],
        rng=rngs["bootstrap"],
    )
    left_rate = arms["T"]["fixed"]["误放率"]
    right_rate = arms["C"]["fixed"]["误放率"]
    if left_rate is None or right_rate is None:
        point = None
    else:
        # T−C 误放率差：C 的固定-k 误放 − T 的固定-k 误放（与 compare_primary 的 right−left 且 contrast=C 一致）
        point = right_rate - left_rate
    low = false_release["low"]
    established = (
        point is not None
        and point > 0
        and false_release["defined"]
        and low is not None
        and low > 0
    )
    return {
        "k": k,
        "k_min": k_min,
        "n": n,
        "defined": bool(false_release["defined"] and point is not None),
        "point": point,
        "ci95_low": low,
        "ci95_high": false_release["high"],
        "established": established,
        "bootstrap": false_release,
        "arms": arms,
        "name": "T-C",
    }


def _require_real_nli() -> None:
    """拒绝 trial exact-match；必须能加载正式 XNLI。"""
    if XNLI_MODEL_ID != NLI_MODEL or NLI_MODEL != (
        "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    ):
        raise RuntimeError(f"NLI 型号未锁到正式针: {XNLI_MODEL_ID!r}")
    probe = verify_edit(
        {
            "arm": "T",
            "claim_id": "nli-probe",
            "after_text": "罚款五百元。",
            "evidence_id": "probe#p1@T1",
            "evidence_text": "罚款五百元。",
        }
    )
    if "score" not in probe:
        raise RuntimeError("正式 NLI 未返回 score")


def run_primary(
    *,
    root: Path | None = None,
    generations_file: Path | None = None,
) -> dict[str, Any]:
    """零新 LLM：读 generations → NLI 核验 → T−C。"""
    base = _repo_root() if root is None else Path(root)
    path = generations_path(base) if generations_file is None else Path(generations_file)
    if not path.is_absolute():
        path = base / path
    candidates = load_formal_candidates(base)
    if not path.is_file():
        return {
            "status": "no_generations",
            "primary": None,
            "n": len(candidates),
            "decoding": decoding_pin(),
        }
    generations = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    # refuse LMS / non-qwen-flash in saved generations
    for item in generations:
        model = str(item.get("model") or "")
        if model and model != "qwen-flash":
            raise RuntimeError(f"正式针拒绝非 qwen-flash 生成行: model={model!r}")
    have = {
        (str(item.get("claim_id")), str(item.get("arm")), str(item.get("phase")))
        for item in generations
    }
    missing = []
    for row in candidates:
        for arm, phase in SEND_TC:
            if (str(row["claim_id"]), arm, phase) not in have:
                missing.append((row["claim_id"], arm, phase))
    if missing:
        raise RuntimeError(f"生成未齐，缺 {len(missing)} 键；先 send")

    _require_real_nli()
    ingested = ingested_t1(candidates)
    arms = run_arms_tc(
        candidates,
        generator=_saved_generator(generations),
        verifier=verify_edit,
        decoding=Decoding(temperature=0.0, seed=SEED),
        ingested_t1_ids=ingested,
    )
    rows = list(arms["C"]) + list(arms["T"])
    primary = compare_tc(rows, ingested_t1_ids=ingested, streams=named_streams())
    return {
        "status": "recomputed",
        "primary": primary,
        "arms": arms,
        "generations_path": path.as_posix(),
        "generations_n": len(generations),
        "generations_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "n": len(candidates),
        "built_n": len(candidates),
        "target_n": 100,
        "gap_n": 100 - len(candidates),
        "voids": arms.get("voids") or [],
        "decoding": decoding_pin(),
        "claim_ids": [str(row["claim_id"]) for row in candidates],
    }


def _establishment_from_primary(primary: Mapping[str, Any] | None) -> dict[str, Any]:
    if not primary or not primary.get("defined"):
        return {
            "status": "measured_undefined" if primary else "unmeasured",
            "counted_as_pass": False,
            "sesoi": None,
            "numeric_line": "unregistered",
            "false_accept_rate": None,
            "point_estimate": None,
            "ci95_low": None,
            "ci95_high": None,
            "n": None if not primary else primary.get("n"),
            "k": None if not primary else primary.get("k"),
        }
    established = bool(primary.get("established"))
    return {
        "status": "established" if established else "not_established",
        "counted_as_pass": established,
        "sesoi": None,
        "numeric_line": "unregistered",
        "false_accept_rate": primary.get("point"),
        "point_estimate": primary.get("point"),
        "ci95_low": primary.get("ci95_low"),
        "ci95_high": primary.get("ci95_high"),
        "n": primary.get("n"),
        "k": primary.get("k"),
    }


def render_result_md(bundle: Mapping[str, Any], *, code_pin: str) -> str:
    primary = bundle.get("primary") or {}
    est = _establishment_from_primary(primary if isinstance(primary, Mapping) else None)
    established = bool(est.get("counted_as_pass"))
    lines = [
        "# 成立 patch 实验 · 正式结果（C-04）",
        "",
        "口径：`docs/evidence/patch-establishment/PREREG.md`（Amendment-01/02）。",
        "主比较只认 **T−C**（L1：点估计 > 0 且 95% CI 下界 > 0）。`sesoi=null`。本页不发明 SESOI。",
        "`second_formal_y=false`。不得标产品 L5。不得称优于 RARR·KPR。不得改判历史结果丙。",
        "",
        "## 跑针",
        "",
        f"- **代码针**：`{code_pin}`",
        "- **授权**：主人 Oriental Ronin 明文「跑」+ Amendment-02 + `--authorize-run`",
        f"- **built_n** = {bundle.get('built_n')}（target_n=100；gap_n={bundle.get('gap_n')}；不得把 91 假装成 100）",
        f"- **生成路径**：`{bundle.get('generations_path')}`（n_lines={bundle.get('generations_n')}；sha256=`{bundle.get('generations_sha256')}`）",
        f"- **解码**：model=`qwen-flash`；temperature=`0`；Decoding.seed=`{SEED}`；API seed=`None`；n_boot=`{N_BOOT}`；k_min=`{K_MIN}`",
        f"- **NLI**：`{NLI_MODEL}`；τ=`{ENTAILMENT_TAU}`（禁止 exact-match 回退）",
        f"- **run_status** = `{RUN_STATUS_RAN}`",
        f"- **measurement_status** = `{MEASUREMENT_STATUS_MEASURED}`",
        "",
        "## 主比较（T−C · L1）",
        "",
        "| 比较 | 指标 | 点估计 | 95% 区间下界 | 95% 区间上界 | 成立（C-04 L1） |",
        "|---|---|---|---|---|---|",
        (
            f"| T 对 C | false-accept rate | {format_rate(primary.get('point'))} | "
            f"{format_rate(primary.get('ci95_low'))} | {format_rate(primary.get('ci95_high'))} | "
            f"{'成立' if established else '不成立'} |"
        ),
        "",
        f"- **固定放行数 k** = {primary.get('k')}",
        f"- **k_min** = {K_MIN}",
        f"- **establishment.status** = `{est['status']}`",
        f"- **counted_as_pass** = `{str(est['counted_as_pass']).lower()}`",
        f"- **product_l5** = `false`",
        f"- **sesoi** = `null`",
        "",
        "## 丙防火墙",
        "",
        f"- 历史 `docs/evidence/patch-events/RESULT-Y.md` 分层仍是结果{HISTORICAL_RESULT_Y}。本页未改写。",
        "- B-04 夹具 `counts_as_establishment=false`。",
        "- 不改 floors。不改默认臂。`PRODUCTION_RETRIEVAL_MODE` 仍是 `hybrid+rerank`。",
        "",
        "## 边界",
        "",
        "- 本页不是路线 Y 的另一次正式主跑。",
        "- 即便成立格通过，本票仍不得单独把产品标成 L5。",
        "- 同一预注册禁止第二次正式主跑充数。",
        "",
    ]
    if primary.get("reason"):
        lines.insert(-1, f"- 备注：{primary.get('reason')}")
    document = "\n".join(lines) + "\n"
    _reject_banned(document)
    return document


def write_measured(
    *,
    root: Path,
    out_dir: Path,
    bundle: Mapping[str, Any],
    code_pin: str,
    authorize_run: bool,
) -> dict[str, Any]:
    """写入 measurement / RESULT / primary-tc。须 authorize。分数只在有 primary 后写。"""
    if not authorize_run:
        raise RuntimeError("拒绝写分：缺 --authorize-run")
    base = Path(root)
    if not prereg_run_authorized(base):
        raise RuntimeError("拒绝写分：PREREG 未授权「跑」")
    _reject_out_dir(out_dir)
    primary = bundle.get("primary")
    if not isinstance(primary, Mapping):
        raise RuntimeError("无 primary，拒绝写分")
    establishment = _establishment_from_primary(primary)
    # start from scaffold anchors, then overlay measured fields
    manifest, _measurement_scaffold = build_scaffold(base)
    manifest["level"] = LEVEL_MEASURED
    manifest["manifest_status"] = "schema_frozen_measured"
    manifest["model"]["measurement_status"] = MEASUREMENT_STATUS_MEASURED
    manifest["model"]["temperature"] = 0.0
    manifest["model"]["seed"] = SEED
    manifest["decoding"] = {
        "temperature": 0.0,
        "seed": SEED,
        "model": DEFAULT_MODEL,
        "note": "formal C-04; qwen-flash + mDeBERTa; Amendment-02",
    }
    manifest["establishment"] = establishment
    measurement = {
        "schema_version": SCHEMA_VERSION,
        "level": LEVEL_MEASURED,
        "run_status": RUN_STATUS_RAN,
        "measurement_status": MEASUREMENT_STATUS_MEASURED,
        "replaces_frozen_baseline": False,
        "production_retrieval_mode": PRODUCTION_RETRIEVAL_MODE,
        "conclusion_dir": CONCLUSION_DIR,
        "decoding": manifest["decoding"],
        "establishment": establishment,
        "firewall": manifest["firewall"],
        "criteria": {
            "false_positive": list(FALSE_POSITIVE_IDS),
            "stop": list(STOP_IDS),
            "sesoi": None,
            "numeric_line": CRITERIA_NUMERIC_LINE,
        },
        "primary": {
            "name": "T-C",
            "point": primary.get("point"),
            "ci95_low": primary.get("ci95_low"),
            "ci95_high": primary.get("ci95_high"),
            "k": primary.get("k"),
            "k_min": primary.get("k_min"),
            "n": primary.get("n"),
            "established": primary.get("established"),
            "defined": primary.get("defined"),
            "reason": primary.get("reason"),
        },
        "generations": {
            "path": bundle.get("generations_path"),
            "sha256": bundle.get("generations_sha256"),
            "n_lines": bundle.get("generations_n"),
        },
        "built_n": bundle.get("built_n"),
        "target_n": bundle.get("target_n"),
        "gap_n": bundle.get("gap_n"),
        "code_pin": code_pin,
    }
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(_dump(manifest), encoding="utf-8", newline="\n")
    (out / "measurement.json").write_text(_dump(measurement), encoding="utf-8", newline="\n")
    (out / PRIMARY_JSON_NAME).write_text(_dump(dict(primary)), encoding="utf-8", newline="\n")
    result_text = render_result_md(bundle, code_pin=code_pin)
    (base / RESULT_REL).write_text(result_text, encoding="utf-8", newline="\n")
    return {
        "run_status": RUN_STATUS_RAN,
        "measurement_status": MEASUREMENT_STATUS_MEASURED,
        "establishment": establishment["status"],
        "counted_as_pass": establishment["counted_as_pass"],
        "point": primary.get("point"),
        "ci95_low": primary.get("ci95_low"),
        "ci95_high": primary.get("ci95_high"),
        "k": primary.get("k"),
        "n": primary.get("n"),
        "result": (base / RESULT_REL).as_posix(),
    }


def estimate_cost_yuan(root: Path | None = None) -> dict[str, Any]:
    """开跑前成本上界（字符近似 token）。"""
    base = _repo_root() if root is None else Path(root)
    rows = load_formal_candidates(base)
    total_chars = 0
    for row in rows:
        for arm, phase in SEND_TC:
            built = build_prompt(
                {
                    "arm": arm,
                    "phase": phase,
                    "before_text": row["before_text"],
                    "evidence_text": row["evidence_text"],
                }
            )
            total_chars += len(str(built["prompt"]))
    calls = len(rows) * len(SEND_TC)
    # 保守：1 字 ≈ 1 token；输出按每调用 256 token 上界
    est_in = total_chars
    est_out = calls * 256
    # 国内价：输入 0.15 / 百万，输出 1.5 / 百万
    cost = est_in / 1e6 * 0.15 + est_out / 1e6 * 1.5
    return {
        "n_claims": len(rows),
        "n_calls": calls,
        "est_input_tokens_upper": est_in,
        "est_output_tokens_upper": est_out,
        "est_yuan_upper": round(cost, 4),
        "price": {"input_per_m": 0.15, "output_per_m": 1.5, "model": "qwen-flash"},
        "hard_cap_yuan": 10.0,
        "under_cap": cost <= 10.0,
    }
