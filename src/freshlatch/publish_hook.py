"""发前钩子闸(ADR-0031 / #227)。

确定性纯逻辑:给定 run_id、该 Run 包结论、T1 checksum 机械新鲜度、
可选 ack_needs_patch → allow/deny + code/message(+需补丁页眉约束)。

只读消费 disposition 词表(ADR-0027);不触发整包再验、零 LLM。
UI/CLI/HTTP 适配留给后续票;本模块禁止平行 if/else 出口。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from freshlatch.disposition import DISPOSITIONS, Disposition

# 错误/结果码(结构化;UI/CLI/HTTP 直接透传,禁止各出口另造近义词)
HOOK_MISSING_RUN_ID = "HOOK_MISSING_RUN_ID"
HOOK_UNBOUND_RUN = "HOOK_UNBOUND_RUN"
HOOK_CHECKSUM_DRIFT = "HOOK_CHECKSUM_DRIFT"
HOOK_DO_NOT_PUBLISH = "HOOK_DO_NOT_PUBLISH"
HOOK_NEEDS_PATCH_NO_ACK = "HOOK_NEEDS_PATCH_NO_ACK"
HOOK_OK = "HOOK_OK"

# 需补丁放行时强制页眉约束字面量(与包结论词表对齐)
NEEDS_PATCH_BANNER = "需补丁"


@dataclass(frozen=True)
class PublishHookResult:
    """发前钩子闸一次判定结果。

    allow: 是否放行导出/探闸
    disposition: 消费到的包结论;缺绑定时为 None
    code: 结构化码
    message: 短中文(与 code 同构,供三出口对照)
    requires_needs_patch_banner: 需补丁+ack 放行时强制页眉/载荷标明
    """

    allow: bool
    disposition: Disposition | None
    code: str
    message: str
    requires_needs_patch_banner: bool = False

    def to_dict(self) -> dict:
        return {
            "allow": self.allow,
            "disposition": self.disposition,
            "code": self.code,
            "message": self.message,
            "requires_needs_patch_banner": self.requires_needs_patch_banner,
        }


def checksums_fresh(
    recorded: Mapping[str, str] | None,
    current: Mapping[str, str] | None,
) -> bool:
    """机械比对 Run 绑定的 T1 checksum 与当前快照。

    两侧皆空 → 视为未漂(无校验键可漂,由调用方保证有键时才注入)。
    键集或任一值不一致 → 漂移。
    """
    rec = {str(k): str(v) for k, v in (recorded or {}).items()}
    cur = {str(k): str(v) for k, v in (current or {}).items()}
    if not rec and not cur:
        return True
    if set(rec.keys()) != set(cur.keys()):
        return False
    return all(rec[k] == cur[k] for k in rec)


def evaluate_publish_hook(
    *,
    run_id: str | None,
    disposition: str | None = None,
    ack_needs_patch: bool = False,
    checksum_fresh: bool = True,
) -> PublishHookResult:
    """发前钩子闸核心(表驱动语义)。

    优先级(fail-closed):
    1) 缺/空 run_id → deny
    2) 无法解析包结论(disposition 缺失或不在三值内) → deny
    3) 勿发 → deny(不暗示可落 Memo)
    4) checksum/run 机械新鲜度漂移 → deny
    5) 需补丁且未 ack → deny;ack 则放行并强制需补丁页眉
    6) 可发且未漂 → 放行
    """
    rid = (run_id or "").strip()
    if not rid:
        return PublishHookResult(
            allow=False,
            disposition=None,
            code=HOOK_MISSING_RUN_ID,
            message="缺绑定 Run,拒绝导出",
        )

    if disposition is None or disposition not in DISPOSITIONS:
        return PublishHookResult(
            allow=False,
            disposition=None,
            code=HOOK_UNBOUND_RUN,
            message="无法解析 Run 包结论,拒绝导出",
        )

    if disposition == "勿发":
        return PublishHookResult(
            allow=False,
            disposition="勿发",
            code=HOOK_DO_NOT_PUBLISH,
            message="包结论为勿发,拒绝导出",
        )

    if not checksum_fresh:
        return PublishHookResult(
            allow=False,
            disposition=disposition,
            code=HOOK_CHECKSUM_DRIFT,
            message="T1 checksum 或 Run 新鲜度已漂移,拒绝导出",
        )

    if disposition == "需补丁":
        if not ack_needs_patch:
            return PublishHookResult(
                allow=False,
                disposition="需补丁",
                code=HOOK_NEEDS_PATCH_NO_ACK,
                message="包结论为需补丁,未确认 ack 不得干净导出",
            )
        return PublishHookResult(
            allow=True,
            disposition="需补丁",
            code=HOOK_OK,
            message="需补丁已确认,放行并强制标明需补丁",
            requires_needs_patch_banner=True,
        )

    # 可发 + 未漂
    return PublishHookResult(
        allow=True,
        disposition="可发",
        code=HOOK_OK,
        message="包结论可发且新鲜度未漂,放行",
    )
