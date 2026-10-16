#!/usr/bin/env python3
"""C-04 LOCAL trial smoke (unofficial) — LMS OpenAI-compatible generator.

NOT formal 「跑」. Does NOT write docs/evidence/patch-establishment/RESULT.md.
Does NOT update formal manifest locks (generator stays qwen-flash in registry).
Trial artifacts only: labeled trial/unofficial, counts_as_establishment=false.

Formal C-04 locks generator=qwen-flash + nli=mDeBERTa; this trial uses local
LM Studio for the generator only (default model qwen3.5-9b).

Env:
  BASE_URL   OpenAI-compatible base (default http://127.0.0.1:1234/v1)
  MODEL      LMS model id (default qwen3.5-9b)
  API_KEY    optional (default lm-studio)
  C04_TRIAL_MAX_CLAIMS  max claims (default 3, hard cap 3)

Usage (on the machine that can reach LMS, typically 儒教武士):
  set BASE_URL=http://127.0.0.1:1234/v1
  set MODEL=qwen3.5-9b
  python scripts/smoke_c04_local_lms.py --out c04-local-trial
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Repo root = parents[1] of scripts/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from freshlatch.eval.patch_events_generate import build_prompt  # noqa: E402

_HARD_CAP = 3
_DEFAULT_BASE = "http://127.0.0.1:1234/v1"
_DEFAULT_MODEL = "qwen3.5-9b"
_FORMAL_GENERATOR = "qwen-flash"
_FORMAL_NLI = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
_ARMS = ("C", "T")


def _repo_root() -> Path:
    return _ROOT


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_claims(constructed: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in constructed.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        # Prefer T-arm construction rows (one per claim in frozen file)
        if row.get("arm") and row.get("arm") != "T":
            continue
        rows.append(row)
        if len(rows) >= limit:
            break
    if not rows:
        raise SystemExit(f"no claims in {constructed}")
    return rows


def _message_text(message: Any) -> str:
    """Prefer content; fall back to reasoning_content only if content empty."""
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    # openai SDK may expose reasoning_content on some LMS builds
    reason = getattr(message, "reasoning_content", None)
    if isinstance(reason, str) and reason.strip():
        return reason.strip()
    if isinstance(message, dict):
        c = message.get("content")
        if isinstance(c, str) and c.strip():
            return c.strip()
        r = message.get("reasoning_content")
        if isinstance(r, str) and r.strip():
            return r.strip()
    return ""


def _chat(
    *,
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=0)
    t0 = time.perf_counter()
    # Qwen3.5 in LMS: reasoning_effort=none puts answer in content (else all tokens are reasoning)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=512,
        extra_body={"reasoning_effort": "none"},
    )
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    choice = resp.choices[0]
    text = _message_text(choice.message)
    usage = resp.usage
    return {
        "text": text,
        "finish_reason": choice.finish_reason,
        "latency_ms": elapsed_ms,
        "model_reported": getattr(resp, "model", model),
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
            "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
            "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        },
    }


def _try_nli(after_text: str, evidence_text: str) -> dict[str, Any]:
    """Prefer formal mDeBERTa verify_edit; else trial exact-match stub."""
    try:
        from freshlatch.eval.patch_events_verify import (
            ENTAILMENT_TAU,
            XNLI_MODEL_ID,
            verify_edit,
        )

        out = verify_edit(
            {
                "after_text": after_text,
                "evidence_text": evidence_text,
                "claim_id": "trial",
                "arm": "T",
                "evidence_id": "trial",
            }
        )
        return {
            "nli_backend": "mDeBERTa-verify_edit",
            "nli_model": XNLI_MODEL_ID,
            "tau": ENTAILMENT_TAU,
            "ok": bool(out.get("ok")),
            "score": out.get("score"),
            "reason": out.get("reason"),
        }
    except Exception as exc:  # noqa: BLE001 — trial path must not die on missing torch
        exact = after_text.strip() == evidence_text.strip()
        return {
            "nli_backend": "trial_exact_match_fallback",
            "nli_model": None,
            "nli_unavailable_reason": f"{type(exc).__name__}: {exc}",
            "ok": exact,
            "score": 1.0 if exact else float("-inf"),
            "reason": "trial exact-match (mDeBERTa unavailable)" if exact else "trial mismatch",
            "note": "NOT formal NLI; do not treat as establishment score",
        }


def _score_arm(arm: str, after_text: str, evidence_text: str) -> dict[str, Any]:
    if arm == "C":
        # C: no evidence in prompt; formal path scores coverage without NLI release gate
        return {
            "decision": "release",
            "score": None,
            "nli": {
                "nli_backend": "skipped_for_arm_C",
                "note": "C arm has no evidence in prompt; trial records generation only",
            },
        }
    nli = _try_nli(after_text, evidence_text)
    decision = "release" if nli.get("ok") else "reject"
    return {"decision": decision, "score": nli.get("score"), "nli": nli}


def run_trial(
    *,
    root: Path,
    out_dir: Path,
    base_url: str,
    model: str,
    api_key: str,
    max_claims: int,
    temperature: float,
    timeout: float,
    dry_fixtures: bool,
) -> Path:
    max_claims = min(max(_HARD_CAP, 1), max(1, max_claims), _HARD_CAP)
    constructed = root / "data" / "patch-establishment" / "v1" / "CONSTRUCTED.jsonl"
    if not constructed.is_file():
        raise SystemExit(f"missing constructed file: {constructed}")

    claims = _load_claims(constructed, max_claims)
    results: list[dict[str, Any]] = []
    probe: dict[str, Any] = {"base_url": base_url, "model": model, "reachable": False}

    if dry_fixtures:
        probe["reachable"] = False
        probe["mode"] = "dry_fixtures"
        for row in claims:
            for arm in _ARMS:
                built = build_prompt(
                    {
                        "arm": arm,
                        "phase": "rewrite",
                        "before_text": row["before_text"],
                        "evidence_text": row["evidence_text"],
                    }
                )
                # dry: use construction after for T, before for C placeholder
                after = row["after_text"] if arm == "T" else f"[dry-C] {row['before_text']}"
                scored = _score_arm(arm, after, row["evidence_text"])
                results.append(
                    {
                        "claim_id": row["claim_id"],
                        "construction_gold": row.get("construction_gold"),
                        "edit_type": row.get("edit_type"),
                        "arm": arm,
                        "before_text": row["before_text"],
                        "evidence_text": row["evidence_text"],
                        "prompt_preview": str(built["prompt"])[:240],
                        "after_text": after,
                        "generation": {"dry": True, "text": after},
                        **scored,
                    }
                )
    else:
        # reachability probe
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url, timeout=min(timeout, 15), max_retries=0)
            models = client.models.list()
            probe["reachable"] = True
            probe["models"] = [m.id for m in models.data]
        except Exception as exc:  # noqa: BLE001
            probe["reachable"] = False
            probe["error"] = f"{type(exc).__name__}: {exc}"
            raise SystemExit(
                "LMS unreachable at "
                f"{base_url}: {probe['error']}\n"
                "Start server on the Windows host: lms server start --port 1234\n"
                "Then re-run this script there (not on the box)."
            ) from exc

        for row in claims:
            for arm in _ARMS:
                built = build_prompt(
                    {
                        "arm": arm,
                        "phase": "rewrite",
                        "before_text": row["before_text"],
                        "evidence_text": row["evidence_text"],
                    }
                )
                gen = _chat(
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    prompt=str(built["prompt"]),
                    temperature=temperature,
                    timeout=timeout,
                )
                after = gen["text"]
                scored = _score_arm(arm, after, row["evidence_text"])
                results.append(
                    {
                        "claim_id": row["claim_id"],
                        "construction_gold": row.get("construction_gold"),
                        "edit_type": row.get("edit_type"),
                        "arm": arm,
                        "before_text": row["before_text"],
                        "evidence_text": row["evidence_text"],
                        "prompt_chars": len(str(built["prompt"])),
                        "after_text": after,
                        "generation": gen,
                        **scored,
                    }
                )
                print(
                    f"[trial] {row['claim_id']} arm={arm} decision={scored['decision']} "
                    f"after_chars={len(after)} latency_ms={gen.get('latency_ms')}",
                    flush=True,
                )

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = {
        "schema": "c04-local-trial-v1",
        "label": "trial/unofficial",
        "counts_as_establishment": False,
        "formal_run": False,
        "formal_result_updated": False,
        "firewall": {
            "second_formal_y": False,
            "product_l5": False,
            "claims_rarr_kpr_superiority": False,
            "note": "STOP-UNRUN: this is not master「跑」; scores must not enter RESULT.md",
        },
        "formal_locks_reference": {
            "generator_model": _FORMAL_GENERATOR,
            "nli_model": _FORMAL_NLI,
            "trial_generator_override": model,
            "trial_base_url": base_url,
        },
        "created_at": _now_iso(),
        "probe": probe,
        "n_claims": len(claims),
        "arms": list(_ARMS),
        "claim_ids": [c["claim_id"] for c in claims],
        "rows": results,
    }
    out_path = out_dir / f"c04_local_trial_{stamp}.json"
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest = out_dir / "c04_local_trial_latest.json"
    latest.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
    readme = out_dir / "README_TRIAL.md"
    readme.write_text(
        "\n".join(
            [
                "# C-04 local trial artifacts (unofficial)",
                "",
                "- `counts_as_establishment=false`",
                "- Do **not** copy scores into `docs/evidence/patch-establishment/RESULT.md`",
                "- Formal generator lock remains `qwen-flash`; this trial used local LMS",
                "- Formal NLI lock remains mDeBERTa; if missing, rows use `trial_exact_match_fallback`",
                "",
                f"Latest: `{latest.name}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {out_path}", flush=True)
    print(f"latest {latest}", flush=True)
    return out_path


def main() -> None:
    env_limit = int(os.environ.get("C04_TRIAL_MAX_CLAIMS", "3"))
    parser = argparse.ArgumentParser(description="C-04 local LMS trial smoke (unofficial)")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(os.environ.get("C04_TRIAL_OUT", "c04-local-trial")),
        help="trial output directory (never formal RESULT path)",
    )
    parser.add_argument("--root", type=Path, default=_repo_root())
    parser.add_argument("--base-url", default=os.environ.get("BASE_URL", _DEFAULT_BASE))
    parser.add_argument("--model", default=os.environ.get("MODEL", _DEFAULT_MODEL))
    parser.add_argument("--api-key", default=os.environ.get("API_KEY", "lm-studio"))
    parser.add_argument("--max-claims", type=int, default=min(env_limit, _HARD_CAP))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument(
        "--dry-fixtures",
        action="store_true",
        help="no LMS calls; score constructed after_text only (still trial)",
    )
    args = parser.parse_args()
    if "patch-establishment" in args.out.as_posix() and args.out.name in {
        "RESULT.md",
        "manifest.json",
        "measurement.json",
    }:
        raise SystemExit("refusing to write formal patch-establishment result paths")
    # Guard: never write into formal evidence RESULT
    banned = _repo_root() / "docs" / "evidence" / "patch-establishment"
    try:
        out_resolved = args.out if args.out.is_absolute() else (_repo_root() / args.out)
        out_resolved = out_resolved.resolve()
        if out_resolved == banned.resolve() or banned.resolve() in out_resolved.parents:
            if out_resolved.name in {"RESULT.md", "manifest.json", "measurement.json", "PREREG.md"}:
                raise SystemExit("refusing formal evidence filenames")
            # allow a *sibling* trial folder under patch-establishment only if named trial
            if "local_trial" not in out_resolved.name and "trial" not in out_resolved.name:
                raise SystemExit(
                    "refusing to write into docs/evidence/patch-establishment/ "
                    "unless path name contains trial/local_trial"
                )
    except SystemExit:
        raise
    except OSError:
        pass

    run_trial(
        root=args.root.resolve(),
        out_dir=(args.out if args.out.is_absolute() else args.root / args.out).resolve(),
        base_url=args.base_url.rstrip("/"),
        model=args.model,
        api_key=args.api_key,
        max_claims=args.max_claims,
        temperature=args.temperature,
        timeout=args.timeout,
        dry_fixtures=args.dry_fixtures,
    )


if __name__ == "__main__":
    main()
