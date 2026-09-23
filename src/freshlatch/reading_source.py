"""读法源单一真相(变体 C / ε 如何读复验评估 §4)。

旁路、Client Memo 附注、ACCEPTANCE 只投影本模块字面,不各写各的。
文案在场仅表明误读边界可被核对。
禁止:demo 可读 ⇒ 付费或验证成功;文案在场 ⇒ 对抗仪器已过;
Time-to-Sheet/rubric ⇒ 付费或一期闭合。
"""

from __future__ import annotations

# 复验单旁路缩写:身份 / 机器 / 人 / 边界。主叙事仍卖作废。
BYPASS_TEXT = (
    "如何读本复验单:"
    "【身份】卖作废。"
    "【机器】fresh/stale/unknown 是机器判定。"
    "【人】void 是人的决定,void≠stale。"
    "【边界】非法律意见、非自动决策。"
)

# Client Memo 附注:边界 + 人/机一句。不投影人审事件流,不写商业裁决。
MEMO_NOTE = (
    "附注:非法律意见、非自动决策。"
    "void 是人的决定,fresh/stale/unknown 是机器判定,void≠stale。"
)

# ACCEPTANCE 预锁整句。改字 = 本批文案验收作废并须重登。
ACCEPTANCE_SENTENCE = (
    "「如何读复验」读法源已投影至复验单旁路与 Client Memo 附注；"
    "ACCEPTANCE 仅表明误读边界（非法律/非自动、void≠stale、demo≠验证）可被核对在场，"
    "不表明产品验证成功、付费意愿或对抗仪器已过。"
)
