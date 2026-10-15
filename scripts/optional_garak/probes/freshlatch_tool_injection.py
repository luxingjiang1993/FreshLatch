"""FreshLatch tool-calling prompt 集, 供操作者已安装的 garak 加载.

active 为 false: 裸跑 garak 全量探针不会带上这组 prompt.
只有样板脚本传入的 --spec 会选中 ToolInjection.
不参与生产 run_loop.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from garak import _config
from garak.probes._tier import Tier
from garak.probes.base import Probe

_ADAPTER = Path(__file__).resolve().parents[1]
_LOADER_NAME = "optional_garak_load"


def _ensure_freshlatch_match():
    """bootstrap 已登记则直接 import; 否则按文件加载."""
    if "freshlatch_match" in sys.modules:
        return
    if _LOADER_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(_LOADER_NAME, _ADAPTER / "_load.py")
        if spec is None or spec.loader is None:
            raise ImportError(_LOADER_NAME)
        module = importlib.util.module_from_spec(spec)
        sys.modules[_LOADER_NAME] = module
        spec.loader.exec_module(module)
    sys.modules[_LOADER_NAME].load_local(
        "freshlatch_match",
        _ADAPTER / "freshlatch_match.py",
    )


_ensure_freshlatch_match()
from freshlatch_match import DETECTOR_NAME, load_prompt_set

_PROMPTS = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "evidence"
    / "garak"
    / "tool-injection-prompts.json"
)


class ToolInjection(Probe):
    """对一组 FreshLatch tool-calling prompt 做 injection 扫描."""

    lang = "zh"
    active = False
    goal = "do not let an injected instruction produce a FreshLatch tool call"
    intent = "T009ignore"
    primary_detector = DETECTOR_NAME
    tags = ["owasp:llm01", "avid-effect:security:S0403"]
    tier = Tier.UNLISTED
    doc_uri = "docs/ops/可选-garak-tool-injection扫描.md"
    DEFAULT_PARAMS = Probe.DEFAULT_PARAMS | {"follow_prompt_cap": False}

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        payload = load_prompt_set(_PROMPTS)
        self._rows = payload["prompts"]
        self.prompts = [row["text"] for row in self._rows]

    def _attempt_prestore_hook(self, attempt, seq):
        row = self._rows[seq]
        attempt.notes["prompt_id"] = row["id"]
        attempt.notes["kind"] = row["kind"]
        attempt.notes["watched_tools"] = list(row["watched_tools"])
        return attempt
