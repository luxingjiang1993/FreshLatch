"""课题包解析（active_pack）。

只解析包 id、拼路径、打开对应 SQLite。不改闸、不放行、不写续命。
配置约定：环境变量 FRESHLATCH_ACTIVE_PACK；未设置时为默认包 thesis-1
（第一课题现有 corpus / docket / gold / SQLite）。已知包仅 thesis-1 与
p1-quotettl。未知或空 id 直接拒绝。

本模块不是「多垂类已 Port」，也不是数据集已释放。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from freshlatch.store.sqlite_store import SQLiteStore

ENV_ACTIVE_PACK = "FRESHLATCH_ACTIVE_PACK"
DEFAULT_PACK_ID = "thesis-1"
P1_PACK_ID = "p1-quotettl"
KNOWN_PACK_IDS = (DEFAULT_PACK_ID, P1_PACK_ID)


class PackResolveError(ValueError):
    """active_pack 无法解析。不回落到另一包。"""


@dataclass(frozen=True)
class PackPaths:
    """一次解析的路径结果。sqlite 文件允许尚不存在，打开时由既有 SCHEMA 创建。"""

    pack_id: str
    label: str
    synthetic: bool
    question: str
    corpus: Path
    docket: Path
    gold: Path
    sqlite: Path
    checkpoints: Path
    distractor_docket: Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def active_pack_id() -> str:
    """未设置环境变量 → 默认包。已设置但为空 → 拒绝。"""
    if ENV_ACTIVE_PACK not in os.environ:
        return DEFAULT_PACK_ID
    raw = os.environ[ENV_ACTIVE_PACK].strip()
    if not raw:
        raise PackResolveError(f"{ENV_ACTIVE_PACK} 已设置但为空")
    return raw


def _read_question(docket: Path) -> str:
    data = json.loads(docket.read_text(encoding="utf-8"))
    question = data["question"]
    if not isinstance(question, str) or not question.strip():
        raise PackResolveError(f"课题包 docket 缺少 question: {docket}")
    return question


def _pack(
    *,
    pack_id: str,
    label: str,
    corpus: Path,
    docket: Path,
    gold: Path,
    sqlite: Path,
    checkpoints: Path,
    distractor_docket: Path,
) -> PackPaths:
    required = (corpus, docket, gold)
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise PackResolveError("课题包路径缺失: " + "; ".join(missing))
    if not (corpus / "t0").is_dir() or not (corpus / "t1").is_dir():
        raise PackResolveError(f"课题包 corpus 缺少 t0/ 或 t1/: {corpus}")
    return PackPaths(
        pack_id=pack_id,
        label=label,
        synthetic=True,
        question=_read_question(docket),
        corpus=corpus,
        docket=docket,
        gold=gold,
        sqlite=sqlite,
        checkpoints=checkpoints,
        distractor_docket=distractor_docket,
    )


def _thesis1(root: Path) -> PackPaths:
    return _pack(
        pack_id=DEFAULT_PACK_ID,
        label="第一课题",
        corpus=root / "data" / "corpus",
        docket=root / "data" / "t0_docket.json",
        gold=root / "data" / "eval" / "gold.json",
        sqlite=root / "data" / "freshlatch.db",
        checkpoints=root / "data" / "checkpoints.db",
        distractor_docket=root / "data" / "eval" / "distractor_docket.json",
    )


def _p1(root: Path) -> PackPaths:
    base = root / "data" / "packs" / P1_PACK_ID
    return _pack(
        pack_id=P1_PACK_ID,
        label="P1 QuoteTTL 薄",
        corpus=base / "corpus",
        docket=base / "docket.json",
        gold=base / "gold.json",
        sqlite=base / "freshlatch.db",
        checkpoints=base / "checkpoints.db",
        distractor_docket=base / "distractor_docket.json",
    )


_BUILDERS = {
    DEFAULT_PACK_ID: _thesis1,
    P1_PACK_ID: _p1,
}


def resolve_pack(pack_id: str | None = None) -> PackPaths:
    """解析 active_pack。pack_id 为 None 时读环境变量（未设置则默认包）。"""
    pid = active_pack_id() if pack_id is None else str(pack_id).strip()
    if not pid:
        raise PackResolveError("pack_id 为空")
    builder = _BUILDERS.get(pid)
    if builder is None:
        known = ", ".join(KNOWN_PACK_IDS)
        raise PackResolveError(f"未知 active_pack {pid!r}（已知: {known}）")
    return builder(repo_root())


def open_pack_store(pack: PackPaths) -> SQLiteStore:
    """打开该包自己的 SQLite 文件。表结构用既有 SCHEMA，不加列。

    入库前可补本地向量。``FRESHLATCH_LOCAL_EMBED=0`` 时不挂 embedder。
    """
    from freshlatch.store.local_embed import attach_local_embedder

    store = SQLiteStore(pack.sqlite)
    attach_local_embedder(store)
    return store
