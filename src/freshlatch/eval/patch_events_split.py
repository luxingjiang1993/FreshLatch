"""patch_events 的划分清单。

把 construct_samples 在现有 docket 与语料上的结果写成可审计 JSON。
不改配额，不调用模型，不消费命名流。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from freshlatch.eval.patch_events_construct import QUOTAS, ConstructedEdit, Shortfall, construct_samples

_NOTE = Path("docs/evidence/patch-events/PILOT-NOTE.md")
_SPLIT = Path("docs/evidence/patch-events/SPLIT.json")
_ROUTE_B_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2-route-b.json")
_DOCKET = Path("data/t0_docket.json")
_CORPUS = Path("data/corpus")
_FORMAL_REFUSAL = "pilot 未结束，不得读取正式集"
_ROUTE_B_FORMAL_N = 100
_ROUTE_B_QUOTA_N100 = 100


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _tier_total(tier: str) -> int:
    return sum(correct + bad for correct, bad in QUOTAS[tier].values())


def _items(rows: tuple[ConstructedEdit, ...]) -> list[dict[str, str]]:
    return [
        {
            "claim_id": str(row.record["claim_id"]),
            "construction_gold": str(row.record["construction_gold"]),
            "edit_type": str(row.record["edit_type"]),
        }
        for row in rows
    ]


def _shortfalls(rows: tuple[Shortfall, ...]) -> list[dict[str, Any]]:
    return [
        {
            "claim_id": row.claim_id,
            "edit_type": row.edit_type,
            "operator": row.operator,
            "reason": row.reason,
        }
        for row in rows
    ]


def _body(root: Path) -> dict[str, Any]:
    result = construct_samples(root / _DOCKET, root / _CORPUS)
    pilot = _items(result.pilot)
    n30 = _items(result.n30)
    n100 = _items(result.n100)
    shortfalls = _shortfalls(result.shortfalls)
    return {
        "conformal_reserve": "未做",
        "counts": {
            "n100": len(n100),
            "n30": len(n30),
            "pilot": len(pilot),
            "shortfalls": len(shortfalls),
        },
        "gaps": {
            "n100": _tier_total("n100") - len(n100),
            "n30": _tier_total("n30") - len(n30),
            "pilot": _tier_total("pilot") - len(pilot),
        },
        "n100": n100,
        "n30": n30,
        "pilot": pilot,
        "quotas_target": {
            "n100": _tier_total("n100"),
            "n30": _tier_total("n30"),
            "pilot": _tier_total("pilot"),
        },
        "shortfalls": shortfalls,
        "source": {
            "corpus": _CORPUS.as_posix(),
            "docket": _DOCKET.as_posix(),
        },
    }


def render_manifest(root: Path | None = None) -> str:
    """渲染清单文本。不写文件。"""
    base = _repo_root() if root is None else Path(root)
    body = _body(base)
    digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    body["sha256"] = digest
    return _canonical(body)


def _read_split(root: Path) -> dict[str, Any]:
    return json.loads((root / _SPLIT).read_text(encoding="utf-8"))


def load_pilot_ids(root: Path, *, split: Path | None = None) -> list[str]:
    """只返回 pilot 的 claim_id。split 默认是论文清单。不打开正式集闸。"""
    base = Path(root)
    relative = _SPLIT if split is None else Path(split)
    path = relative if relative.is_absolute() else base / relative
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(row["claim_id"]) for row in payload["pilot"]]


def load_formal_ids(root: Path) -> dict[str, list[str]]:
    """笔记文件不存在时拒绝。拒绝发生在打开清单之前。"""
    base = Path(root)
    if not (base / _NOTE).is_file():
        raise RuntimeError(_FORMAL_REFUSAL)
    payload = _read_split(base)
    return {
        "n30": [str(row["claim_id"]) for row in payload["n30"]],
        "n100": [str(row["claim_id"]) for row in payload["n100"]],
    }


def route_b_split_path(root: Path | None = None) -> Path:
    """路线 B 正式 n=100 名单路径（写死）。不激活主跑，不发模型。"""
    base = _repo_root() if root is None else Path(root)
    return base / _ROUTE_B_SPLIT


def load_route_b_manifest(root: Path | None = None) -> dict[str, Any]:
    """读取路线 B 写死名单。不改配额，不构造样本，不发模型。"""
    path = route_b_split_path(root)
    return json.loads(path.read_text(encoding="utf-8"))


def load_route_b_formal_n100_ids(root: Path | None = None) -> list[str]:
    """正式 n=100 的 claim_id 列表。pilot id 不得出现。"""
    payload = load_route_b_manifest(root)
    target = int(payload["quotas_target"]["n100"])
    if target != _ROUTE_B_QUOTA_N100:
        raise RuntimeError("路线 B 不得改小 PREREG-B 的 n=100 配额")
    ids = [str(row["claim_id"]) for row in payload["n100"]]
    if len(ids) != len(set(ids)):
        raise RuntimeError("路线 B 正式 n=100 含重复主张")
    if len(ids) > _ROUTE_B_FORMAL_N:
        raise RuntimeError("路线 B 正式名单超过 n=100")
    pilot_ids = {str(row["claim_id"]) for row in payload["pilot"]}
    if set(ids) & pilot_ids:
        raise RuntimeError("路线 B 正式 n 与 pilot 重叠")
    gap = int(payload["gaps"]["n100"])
    if gap != target - len(ids):
        raise RuntimeError("路线 B gaps.n100 与配额/已建条数不一致")
    return ids


def route_b_result_fields(root: Path | None = None) -> dict[str, int]:
    """结果表可抄字段：语料缺额 = gaps.n100。不得为凑齐改小配额。"""
    payload = load_route_b_manifest(root)
    target = int(payload["quotas_target"]["n100"])
    if target != _ROUTE_B_QUOTA_N100:
        raise RuntimeError("路线 B 不得改小 PREREG-B 的 n=100 配额")
    built = len(payload["n100"])
    gap = int(payload["gaps"]["n100"])
    if gap != target - built:
        raise RuntimeError("语料缺额必须等于配额目标减已建条数")
    fields = payload.get("result_fields") or {}
    if int(fields.get("语料缺额", -1)) != gap:
        raise RuntimeError("result_fields.语料缺额 与 gaps.n100 不一致")
    return {"语料缺额": gap}
