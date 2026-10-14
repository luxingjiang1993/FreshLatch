"""retrieve 边的 CRAG 三态。纯函数,零 I/O。

grade 在检索观察上算完。Agent 只读观察里的 grade 与 reason code,
不在循环里另写一套,也不做联网回退。
Ambiguous 表示这份观察不够支持继续写判定。
两条 T1 互相矛盾的 conflicting_evidence 不在本模块。
"""

from __future__ import annotations

from typing import Literal

Grade = Literal["correct", "incorrect", "ambiguous"]

REASON_GRADE_INCORRECT_EXHAUSTED = "grade_incorrect_exhausted"
REASON_GRADE_AMBIGUOUS = "grade_ambiguous"

# 夹具注入键。生产块没有该键时走下面的确定性规则。
INJECTION_KEY = "crag_grade"

_GRADES = frozenset({"correct", "incorrect", "ambiguous"})
# 同一观察里多块注入不一致时取最严。
_STRICTEST = ("incorrect", "ambiguous", "correct")

INCORRECT_EXHAUSTED_FRESH_REFUSAL = (
    "reverify_claim(fresh) 拒绝: retrieve 边 grade=incorrect,"
    "再检索一次后仍失败,reason_code=grade_incorrect_exhausted。不得写 fresh。"
)
AMBIGUOUS_FRESH_REFUSAL = (
    "reverify_claim(fresh) 拒绝: retrieve 边 grade=ambiguous,"
    "reason_code=grade_ambiguous。这份观察不够支持继续写判定,不得写 fresh。"
)


def read_injected_grade(blocks: list) -> str | None:
    """读夹具注入的三态。没有合法注入时返回 None。"""
    found: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        raw = block.get(INJECTION_KEY)
        if not isinstance(raw, str):
            continue
        grade = raw.strip().lower()
        if grade in _GRADES:
            found.append(grade)
    for grade in _STRICTEST:
        if grade in found:
            return grade
    return None


def _has_t1(blocks: list) -> bool:
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if str(block.get("evidence_id") or "").endswith("@T1"):
            return True
    return False


def grade_retrieve_observation(blocks: list) -> dict[str, str | None]:
    """给一次 retrieve 的块列表打 CRAG 三态。

    夹具可在块上注入 crag_grade。无注入时的确定性规则只看 id 后缀:
    至少一条 evidence_id 以 @T1 结尾为 correct,否则为 incorrect。
    Ambiguous 只来自注入,不读正文,不检测两条 T1 是否矛盾。
    reason_code 在 ambiguous 时为 grade_ambiguous。
    incorrect 的耗尽码要等再检索一次之后由 mark_incorrect_exhausted 写入。
    """
    injected = read_injected_grade(blocks)
    if injected is not None:
        grade = injected
        source = "injected"
    else:
        grade = "correct" if _has_t1(blocks) else "incorrect"
        source = "rule"
    reason = REASON_GRADE_AMBIGUOUS if grade == "ambiguous" else None
    return {"grade": grade, "reason_code": reason, "source": source}


def should_refine_incorrect(grade: dict) -> bool:
    """注入得到的 Incorrect 再检索一次。

    无 @T1 的规则型 incorrect 不加打检索,拒答仍走 sufficiency。
    """
    return grade.get("grade") == "incorrect" and grade.get("source") == "injected"


def mark_incorrect_exhausted(grade: dict) -> dict[str, str | None]:
    """再检索一次之后,注入的 Incorrect 仍在,则写上耗尽拒因。"""
    if grade.get("grade") != "incorrect" or grade.get("source") != "injected":
        return {
            "grade": grade.get("grade"),
            "reason_code": grade.get("reason_code"),
            "source": grade.get("source"),
        }
    return {
        "grade": "incorrect",
        "reason_code": REASON_GRADE_INCORRECT_EXHAUSTED,
        "source": "injected",
    }


def strip_grade_injection(blocks: list) -> list[dict]:
    """对外观察去掉注入键。Agent 只消费 grade 字段。"""
    public: list[dict] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        public.append(
            {key: value for key, value in block.items() if key != INJECTION_KEY}
        )
    return public


def fresh_refused_by_grade(observations: list[dict]) -> dict[str, str] | None:
    """Agent 消费观察上已经写好的 grade。不重算,不读块正文。

    无观察、grade 为 correct、或没有 grade:本票不强制拒答,返回 None。
    ambiguous:拒,reason_code=grade_ambiguous。
    incorrect 且 grade_reason_code 已是 grade_incorrect_exhausted:拒。
    规则型 incorrect 没有耗尽码,不在这里拒,无 @T1 仍由 sufficiency 负责。
    """
    if not observations:
        return None
    latest = observations[-1]
    grade = latest.get("grade")
    if grade == "ambiguous":
        return {"grade": "ambiguous", "reason_code": REASON_GRADE_AMBIGUOUS}
    if (
        grade == "incorrect"
        and latest.get("grade_reason_code") == REASON_GRADE_INCORRECT_EXHAUSTED
    ):
        return {
            "grade": "incorrect",
            "reason_code": REASON_GRADE_INCORRECT_EXHAUSTED,
        }
    return None


def grade_fresh_refusal_message(reason_code: str) -> str:
    """拒答文案。未知码直接报错,不改写成别的 reason。"""
    if reason_code == REASON_GRADE_INCORRECT_EXHAUSTED:
        return INCORRECT_EXHAUSTED_FRESH_REFUSAL
    if reason_code == REASON_GRADE_AMBIGUOUS:
        return AMBIGUOUS_FRESH_REFUSAL
    raise ValueError(f"未知 grade 拒因: {reason_code}")


def grade_token(grade: str) -> str:
    """轨迹里的紧凑记号,例如 grade=ambiguous。"""
    return f"grade={grade}"
