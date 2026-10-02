"""I3 #250 · B′ 合成夹具：超时/假绿 → 结构化错误（非真事故复盘）。

合成夹具 · 非真事故复盘。不做 Memory/多 Agent；不把整包再验挂回 publish_hook。
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

# 稳定 error_code（短中文走 message）
ERR_AGENT_TIMEOUT = "AGENT_TIMEOUT"
ERR_SYNTHETIC_FALSE_GREEN = "SYNTHETIC_FALSE_GREEN"

FIXTURE_BANNER = "合成夹具 · 非真事故复盘"


@dataclass(frozen=True)
class StructuredAgentError:
    """受控路径可见失败：不得静默当成功绿。"""

    error_code: str
    message: str
    ok: bool = False
    green: bool = False  # 恒 False：结构化错误不得装绿灯成功态

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "green": self.green,
            "error_code": self.error_code,
            "message": self.message,
            "fixture": FIXTURE_BANNER,
        }


def run_with_timeout_structured(
    fn: Callable[[], T],
    timeout_s: float,
    *,
    force_timeout: bool = False,
) -> T | StructuredAgentError:
    """跑可调用体；超时或 force_timeout 夹具 → 结构化错误，不返回假绿成功。

    force_timeout：确定性合成超时（零等待），供单测/演示。
    """
    if force_timeout or timeout_s <= 0:
        return StructuredAgentError(
            error_code=ERR_AGENT_TIMEOUT,
            message=f"Agent 步骤超时（>{timeout_s}s）；{FIXTURE_BANNER}",
        )
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(fn)
        try:
            return fut.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError:
            return StructuredAgentError(
                error_code=ERR_AGENT_TIMEOUT,
                message=f"Agent 步骤超时（>{timeout_s}s）；{FIXTURE_BANNER}",
            )


def refuse_silent_green(*, attempted_green: bool, gate_allowed_green: bool) -> StructuredAgentError | None:
    """假绿夹具：试图绕过闸装绿时给出结构化错误，而非静默成功。

    attempted_green 且 gate 未放行 → 返回 SYNTHETIC_FALSE_GREEN。
    闸已放行则返回 None（由调用方走正常绿路径）。
    """
    if attempted_green and not gate_allowed_green:
        return StructuredAgentError(
            error_code=ERR_SYNTHETIC_FALSE_GREEN,
            message=f"拒绝静默假绿：闸未放行不得装成功态；{FIXTURE_BANNER}",
        )
    return None
