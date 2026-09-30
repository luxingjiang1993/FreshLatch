"""元陈述句法闸(#17,规则闸不变量 6 的判定引擎,评估见 docs/research/c9元陈述句法闸设计评估.md)。

「元陈述」= T1 中关于测量/跟踪行为本身的陈述(未复测/不再列入跟踪/无新数据/待发布/
未入账等),不承载关于主张对象的实质事实。纯元陈述是证据缺口,不是推翻——stale 理由
以它为唯一依据的,闸层打回 META_ONLY_DISPROOF,经「stale 打回落 unknown」路由 unknown。

算法(确定性句法启发式,先于任何测试写死,事后修改 = 评估作废重签):
  1. 按标点切子句;
  2. 含元陈述标记的子句剥掉;
  3. 若一个标记都没有 ⇒ 放行(无标记不株连);
  4. 存在含阿拉伯数字且非元子句的「实质子句」⇒ 放行(数值锚反证,如 c3/c7 实录);
     (#241 / 算法 A) 若传入 claim_statement:残留子句中的数字若全部出现在主张
     statement 中(主张数字回声),则该子句不算实质锚;
  5. 否则 ⇒ 纯元陈述,打回。

已知边界(预登记,评估文档 §拍板 B1-B3 + #241 补丁 B4):无数值的实体性反证与元陈述
共存时可能误伤,误伤方向单向(stale→unknown,不对称安全,绝不向绿灯开口);标记词表
封闭,增补走评审工单(#246 缺口 paraphrase 已入表);缺省不传 claim_statement 时行为不弱于 ADR-0008 当日打回。
"""

from __future__ import annotations

import re

# 封闭枚举(评估文档 §工程手段登记册 B2);新增 paraphrase 须走 #17 同款评审纪律
# #246 / §19:增补缺口声明 paraphrase(无新测量/无更新记录/数据缺口);不含单独「已过时」
_META_MARKERS: tuple[str, ...] = (
    "未复测",
    "不再列入跟踪", "不再跟踪", "不再列入",
    "无新数据", "暂无新数据", "没有新数据",
    "无新测量", "无任何更新", "无更新记录",
    "数据缺口声明", "数据缺口",
    "放弃追踪", "主动放弃追踪", "不再被追踪", "无新数据替代",
    "尚未发生",  # 未来例行调整未发生=缺口叙事,非现时推翻(#246 活模)
    "待发布", "尚未发布", "未入账", "未保留",
    "无法确认", "未能确认", "尚不能确认", "待核实",
    "本期未", "本轮未",
)

_CLAUSE_SPLIT = re.compile(r"[，。；、,.;:!?！？\n]+")
_DIGIT = re.compile(r"\d")
# 连续数字串;比对时用独立数位边界,避免「70」误命中「700」
_NUMBER = re.compile(r"\d+")
# 理由散文里常出现的主张编号(c9/c12…)与时点标签(T0/T1)不是数值锚,剥除后再抽数字
_CLAIM_ID_NOISE = re.compile(r"\bc\d+\b", re.IGNORECASE)
_AS_OF_NOISE = re.compile(r"\b[Tt][01]\b")
# 年月日历噪声:「2026 年」「11 月」「2 月」不是实质反证锚(#246 活模)
_YEAR_NOISE = re.compile(r"\b20\d{2}\b")
_MONTH_NOISE = re.compile(r"\d+\s*月")

# 闸层打回消息;Lead/Critic 工具层提前反馈复用同一句(单一真相,不复制措辞)
META_ONLY_MESSAGE = ("stale 反证不得为纯元陈述:未复测/不再列入跟踪/无新数据/无新测量/"
                     "无更新记录/数据缺口/待发布/未入账等是证据缺口,不是推翻"
                     "(过时未更新 ≠ 已被推翻)——请走 mark_gap + reverify_claim(unknown)")


def _strip_reason_noise(text: str) -> str:
    """剥除主张编号、T0/T1 与年月日历后再做数字判定(#246)。"""
    cleaned = _CLAIM_ID_NOISE.sub(" ", text)
    cleaned = _AS_OF_NOISE.sub(" ", cleaned)
    cleaned = _YEAR_NOISE.sub(" ", cleaned)
    return _MONTH_NOISE.sub(" ", cleaned)


def _numbers_in(text: str) -> list[str]:
    """抽取数字串;先剥除 cN / T0·T1 噪声。"""
    return _NUMBER.findall(_strip_reason_noise(text))


def _number_in_statement(num: str, statement: str) -> bool:
    """数字串是否作为独立数位序列出现在 statement(前后非数字)。"""
    return bool(re.search(rf"(?<!\d){re.escape(num)}(?!\d)", statement))


def _is_claim_echo_only(clause: str, claim_statement: str) -> bool:
    """残留子句数字是否全部为主张 statement 回声(算法 A)。

    无数字 ⇒ 不是「回声放行」问题(由外层无数字路径处理);
    有数字且全部见于 statement ⇒ 纯回声,不算实质锚;
    任一数字不见于 statement ⇒ 含独立数值锚。
    """
    nums = _numbers_in(clause)
    if not nums:
        return False
    return all(_number_in_statement(n, claim_statement) for n in nums)


def is_meta_only_disproof(reason: str, *, claim_statement: str | None = None) -> bool:
    """stale 理由是否以纯元陈述为唯一依据。空理由返回 False:理由存在性归工具层
    ≥20 字校验,闸不重复管(GateDecision.stale_reason 缺省向后兼容)。

    claim_statement:可选主张原文。传入时启用算法 A(主张数字回声不算实质锚);
    缺省 None 时行为不得弱于 ADR-0008 当日对历史形状的打回。
    """
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
        # 剥除 T0/T1、cN 后再判是否含实质数字(#246:「T1 原文…」不得当数值锚)
        clause_for_digit = _strip_reason_noise(clause)
        if not _DIGIT.search(clause_for_digit):
            continue
        # 含数字的非元子句:默认视为实质锚;算法 A 下纯回声不算
        if claim_statement is not None and _is_claim_echo_only(clause, claim_statement):
            continue
        return False  # 实质子句(独立数值锚):不是纯元陈述
    return has_meta
