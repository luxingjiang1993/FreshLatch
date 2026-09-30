"""#245/#246:媒体滞后误写成 mark_gap 的工具层打回。"""

from freshlatch.roles.lead import (
    MEDIA_LAG_AS_GAP_MESSAGE,
    _is_media_lag_misclassified_as_gap,
)


def test_media_lag_gap_description_blocked():
    desc = (
        "行业媒体《东南亚 SaaS 观察》2026 年 9 月刊未更新价格数据,"
        "其引用的 SeaDesk 标准版 99 美元/月报价存在已知滞后"
    )
    assert _is_media_lag_misclassified_as_gap(desc)
    assert "mark_stale" in MEDIA_LAG_AS_GAP_MESSAGE


def test_ordinary_gap_description_passes():
    assert not _is_media_lag_misclassified_as_gap("T1 无覆盖该薪酬指标,本期未测量")
