"""元陈述句法闸(#17,规则闸不变量 6 的判定引擎,评估见 docs/research/c9元陈述句法闸设计评估.md)。

「元陈述」= T1 中关于测量/跟踪行为本身的陈述(未复测/不再列入跟踪/无新数据/待发布/
未入账等),不承载关于主张对象的实质事实。纯元陈述是证据缺口,不是推翻——stale 理由
以它为唯一依据的,闸层打回 META_ONLY_DISPROOF,经「stale 打回落 unknown」路由 unknown。

算法(确定性句法启发式,先于任何测试写死,事后修改 = 评估作废重签):
  1. 按标点切子句;
  2. 含元陈述标记的子句剥掉;
  3. 若一个标记都没有 ⇒ 放行(无标记不株连);
  4. 存在含阿拉伯数字且非元子句的「实质子句」⇒ 放行(数值锚反证,如 c3/c7 实录);
  5. 否则 ⇒ 纯元陈述,打回。

已知边界(预登记,评估文档 §拍板 B1-B3):无数值的实体性反证与元陈述共存时可能误伤,
误伤方向单向(stale→unknown,不对称安全,绝不向绿灯开口);标记词表封闭,增补走评审工单。
"""

from __future__ import annotations

import re

# 封闭枚举(评估文档 §工程手段登记册 B2);新增 paraphrase 须走 #17 同款评审纪律
_META_MARKERS: tuple[str, ...] = (
    "未复测",
    "不再列入跟踪", "不再跟踪", "不再列入",
    "无新数据", "暂无新数据", "没有新数据",
    "待发布", "尚未发布", "未入账", "未保留",
    "无法确认", "未能确认", "尚不能确认", "待核实",
    "本期未", "本轮未",
)

_CLAUSE_SPLIT = re.compile(r"[，。；、,.;:!?！？\n]+")
_DIGIT = re.compile(r"\d")

# 闸层打回消息;Lead/Critic 工具层提前反馈复用同一句(单一真相,不复制措辞)
META_ONLY_MESSAGE = ("stale 反证不得为纯元陈述:未复测/不再列入跟踪/无新数据/待发布/未入账等"
                     "是证据缺口,不是推翻——请走 mark_gap + reverify_claim(unknown)")


def is_meta_only_disproof(reason: str) -> bool:
    """stale 理由是否以纯元陈述为唯一依据。空理由返回 False:理由存在性归工具层
    ≥20 字校验,闸不重复管(GateDecision.stale_reason 缺省向后兼容)。"""
    if not reason:
        return False
    has_meta = False
    for clause in _CLAUSE_SPLIT.split(reason):
        clause = clause.strip()
        if not clause:
            continue
        if any(m in clause for m in _META_MARKERS):
            has_meta = True
            continue  # 元子句:剥掉
        if _DIGIT.search(clause):
            return False  # 实质子句(数值锚且非元子句):不是纯元陈述
    return has_meta
