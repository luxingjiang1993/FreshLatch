"""K5 token 入报告与单测:LLMClient 单桶累计 + run_gold raw 含用量块;禁网 mock。

拍板依据:#62 / docs/research/K4K5实装形态设计评估.md —
仅 K5-1(金标 run_gold);顶层 + per_run token_usage;K5-2 与 control 非本期必过。
不改闸 / gold.json / K6-4。
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from freshlatch.eval.report import render_report
from freshlatch.eval.runner import run_gold
from freshlatch.llm import LLMClient, TokenUsage
from freshlatch.store.base import InMemoryStore
from freshlatch.store.ingest import ingest_into

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CORPUS = REPO_ROOT / "data" / "corpus"
GOLD = REPO_ROOT / "data" / "eval" / "gold.json"
DOCKET = REPO_ROOT / "data" / "t0_docket.json"


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        d = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in self.tool_calls
            ]
        return d


_tc_counter = 0


def _tc(name, args):
    global _tc_counter
    _tc_counter += 1
    return SimpleNamespace(
        id=f"call_tu_{_tc_counter}", type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(args, ensure_ascii=False)),
    )


class _UsageFinishLLM:
    """立即 finish_reverify 收尾;每次 chat 向单桶写入固定 mock usage(禁网)。"""

    def __init__(self, prompt_per_call: int = 7, completion_per_call: int = 3):
        self._n = 0
        self._prompt = prompt_per_call
        self._completion = completion_per_call
        self.token_usage = TokenUsage()

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.token_usage.add(self._prompt, self._completion)
        self._n += 1
        if self._n % 2 == 1:
            return _Msg(tool_calls=[_tc("finish_reverify", {})])
        return _Msg(content="复验结束")


def test_token_usage_to_dict_and_reset():
    tu = TokenUsage()
    tu.add(10, 5)
    assert tu.to_dict() == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }
    tu.reset()
    assert tu.to_dict() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }


def test_llm_client_accumulates_usage_from_mock_response():
    """LLMClient.chat 从响应 usage 累加;不触网(替换 client)。"""
    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9")

    class FakeUsage:
        prompt_tokens = 11
        completion_tokens = 4

    class FakeResp:
        usage = FakeUsage()
        choices = [SimpleNamespace(message=_Msg(content="ok"))]

    calls = {"n": 0}

    def _create(**kwargs):
        calls["n"] += 1
        return FakeResp()

    llm.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=_create)),
    )
    llm.chat([{"role": "user", "content": "a"}])
    llm.chat([{"role": "user", "content": "b"}])
    assert calls["n"] == 2
    assert llm.token_usage.to_dict() == {
        "prompt_tokens": 22,
        "completion_tokens": 8,
        "total_tokens": 30,
    }


def test_llm_client_skips_when_usage_missing():
    """响应无 usage 字段时不炸,桶保持 0。"""
    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9")

    class FakeResp:
        usage = None
        choices = [SimpleNamespace(message=_Msg(content="ok"))]

    llm.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: FakeResp())),
    )
    llm.chat([{"role": "user", "content": "x"}])
    assert llm.token_usage.to_dict()["total_tokens"] == 0


def test_run_gold_raw_has_top_and_per_run_token_usage(tmp_path):
    """run_gold raw:顶层 token_usage + per_run[i].token_usage;遍间清零后合计。"""
    store = InMemoryStore()
    ingest_into(store, CORPUS)
    llm = _UsageFinishLLM(prompt_per_call=7, completion_per_call=3)
    raw = run_gold(
        store, llm,
        gold_path=GOLD, docket_path=DOCKET, runs=2,
        trajectory_dir=tmp_path / "traj",
    )
    assert "token_usage" in raw
    assert len(raw["per_run"]) == 2
    for r in raw["per_run"]:
        assert "token_usage" in r
        tu = r["token_usage"]
        assert tu["prompt_tokens"] > 0
        assert tu["completion_tokens"] > 0
        assert tu["total_tokens"] == tu["prompt_tokens"] + tu["completion_tokens"]

    # 顶层 = 各遍之和
    sum_p = sum(r["token_usage"]["prompt_tokens"] for r in raw["per_run"])
    sum_c = sum(r["token_usage"]["completion_tokens"] for r in raw["per_run"])
    assert raw["token_usage"] == {
        "prompt_tokens": sum_p,
        "completion_tokens": sum_c,
        "total_tokens": sum_p + sum_c,
    }
    # 两遍 chat 次数对称 → 用量应对齐(同脚本、同主张数)
    assert raw["per_run"][0]["token_usage"] == raw["per_run"][1]["token_usage"]

    md = render_report(raw)
    assert "Token 用量" in md
    assert f"prompt_tokens: `{sum_p}`" in md


def test_run_gold_without_token_bucket_still_emits_zero_block(tmp_path):
    """无 token_usage 属性的脚本假件:报告块仍在且为零(schema 稳定,不炸)。"""

    class _BareFinish:
        def __init__(self):
            self._n = 0

        def chat(self, messages, *, tools=None, decoding=None, response_format=None):
            self._n += 1
            if self._n % 2 == 1:
                return _Msg(tool_calls=[_tc("finish_reverify", {})])
            return _Msg(content="复验结束")

    store = InMemoryStore()
    ingest_into(store, CORPUS)
    raw = run_gold(
        store, _BareFinish(),
        gold_path=GOLD, docket_path=DOCKET, runs=1,
        trajectory_dir=tmp_path / "traj2",
    )
    assert raw["token_usage"] == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    assert raw["per_run"][0]["token_usage"]["total_tokens"] == 0
