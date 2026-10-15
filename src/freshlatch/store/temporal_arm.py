"""评测专用时序臂。不改 PRODUCTION_RETRIEVAL_MODE,也不进入运维开关。

``store/base.py`` 保持原样。生产 SQLite 检索若被绑定到该臂,在排序前拒绝,
不把 BM25 / dense / hybrid / rerank 的名次记成这个名字。
"""

from __future__ import annotations

TEMPORAL_TRAINED_MODE = "temporal_trained"


class TemporalTrainedUnmeasured(RuntimeError):
    """该臂没有已核验权重。禁止把其它臂的名次记到这个名字上。"""


def reject_temporal_trained_ranking(requested: str | None) -> None:
    """绑定该臂时拒绝排序。不改走 BM25、dense 或 hybrid。"""
    if requested == TEMPORAL_TRAINED_MODE:
        raise TemporalTrainedUnmeasured(
            "temporal_trained 无已核验权重,拒绝改用其它臂的名次"
        )
