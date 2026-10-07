"""PE-06 三家评委：假传输、固定细则、κ 不插补。

不读真实密钥，不发起网络请求。
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_judges as judges
from freshlatch.llm import DEFAULT_MODEL

_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_LOG_KEYS = (
    "时间",
    "请求的 model",
    "响应回显的 model",
    "请求的 temperature",
    "思考开关",
    "usage",
    "提示的 sha256",
    "原始输出",
    "解析结果",
)


def _prereg_rubric() -> str:
    text = Path("docs/evidence/patch-events/PREREG.md").read_text(encoding="utf-8")
    marker = "```text\n"
    start = text.index(marker + "你是修改核对员") + len(marker)
    end = text.index("\n```", start)
    return text[start:end]


def _item(**overrides):
    base = {
        "claim_id": "c1",
        "before_text": "修改前正文",
        "after_text": "修改后正文",
        "evidence_text": "证据正文",
        "evidence_id": "doc#a@T1",
        "arm": "ARM_SENTINEL_ZZ",
        "construction_gold": "GOLD_SENTINEL_ZZ",
        "other_judge": {"A": "OTHER_SENTINEL_ZZ"},
    }
    base.update(overrides)
    return base


def _ok(model: str, content: str | None = None, **overrides):
    body = {
        "model": model,
        "temperature": 0,
        "thinking": None,
        "content": content or '{"A":"是","B":"否"}',
        "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        "refused": None,
    }
    body.update(overrides)
    return body


class Scripted:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, request):
        self.calls.append(request)
        if not self.responses:
            raise AssertionError("假传输没有更多响应")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return nxt


@pytest.fixture(autouse=True)
def _unset_keys(monkeypatch):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)


def test_rubric_is_prereg_verbatim_and_models_are_locked():
    assert judges.RUBRIC == _prereg_rubric()
    assert judges.JUDGES["qwen"].model == "qwen2.5-72b-instruct"
    assert judges.JUDGES["deepseek"].model == "deepseek-ai/DeepSeek-V3"
    assert judges.JUDGES["kimi"].model == "kimi-k2.6"
    assert judges.JUDGES["kimi"].thinking == {"type": "disabled"}
    assert judges.JUDGES["deepseek"].thinking == {"type": "disabled"}
    assert judges.JUDGES["qwen"].thinking is None
    for spec in judges.JUDGES.values():
        assert spec.model != DEFAULT_MODEL
        assert spec.model not in spec.forbidden_models
    assert "qwen-flash" in judges.JUDGES["qwen"].forbidden_models
    assert "deepseek-chat" in judges.JUDGES["deepseek"].forbidden_models
    assert "deepseek-v4-pro" in judges.JUDGES["deepseek"].forbidden_models
    assert "kimi-latest" in judges.JUDGES["kimi"].forbidden_models
    assert "kimi-k3" in judges.JUDGES["kimi"].forbidden_models
    assert any("code" in item for item in judges.JUDGES["kimi"].forbidden_models)
    assert "DEFAULT_MODEL" not in Path(judges.__file__).read_text(encoding="utf-8")
    assert "真人盲审" not in Path(judges.__file__).read_text(encoding="utf-8")


def test_qwen_request_has_locked_model_and_only_four_user_fields(tmp_path):
    transport = Scripted([_ok("qwen2.5-72b-instruct")])
    judges.run_judges([_item()], transport=transport, logs_dir=tmp_path, judge_ids=("qwen",))
    call = transport.calls[0]
    assert call["model"] == "qwen2.5-72b-instruct"
    assert call["temperature"] == 0
    assert "thinking" not in call or call["thinking"] is None
    assert call["messages"][0] == {"role": "system", "content": judges.RUBRIC}
    user = call["messages"][1]["content"]
    assert user == (
        "修改前：\n修改前正文\n\n"
        "修改后：\n修改后正文\n\n"
        "证据原文：\n证据正文\n\n"
        "evidence id：\ndoc#a@T1"
    )
    for banned in (
        "ARM_SENTINEL_ZZ",
        "GOLD_SENTINEL_ZZ",
        "OTHER_SENTINEL_ZZ",
        "组别",
        "构造金标",
        "系统名",
        "qwen-flash",
        "CLAIM",
        "你是修改核对员",
    ):
        assert banned not in user
    assert [message["role"] for message in call["messages"]] == ["system", "user"]


def test_deepseek_and_kimi_send_temperature_zero_and_thinking_disabled(tmp_path):
    transport = Scripted(
        [
            _ok("deepseek-ai/DeepSeek-V3"),
            _ok("kimi-k2.6"),
        ]
    )
    judges.run_judges(
        [_item()],
        transport=transport,
        logs_dir=tmp_path,
        judge_ids=("deepseek", "kimi"),
    )
    assert transport.calls[0]["model"] == "deepseek-ai/DeepSeek-V3"
    assert transport.calls[1]["model"] == "kimi-k2.6"
    for call in transport.calls:
        assert call["temperature"] == 0
        assert call["thinking"] == {"type": "disabled"}
        assert call["messages"][0]["content"] == judges.RUBRIC


def test_bad_echo_voids_the_judge_and_does_not_change_temperature(tmp_path):
    cases = [
        _ok("qwen-plus"),
        _ok("qwen2.5-72b-instruct", temperature=0.6),
        _ok("qwen2.5-72b-instruct", refused="temperature", content=""),
        _ok("qwen2.5-72b-instruct", refused="thinking", content=""),
        RuntimeError("server rejected temperature=0"),
    ]
    for response in cases:
        transport = Scripted([response, _ok("qwen2.5-72b-instruct", temperature=1)])
        result = judges.run_judges(
            [_item(claim_id="c1"), _item(claim_id="c2")],
            transport=transport,
            logs_dir=tmp_path / type(response).__name__,
            judge_ids=("qwen",),
        )
        assert result["judges"]["qwen"]["void"] is True
        assert result["judges"]["qwen"]["labels"] == {}
        assert len(transport.calls) == 1
        assert transport.calls[0]["temperature"] == 0
        assert transport.calls[0]["model"] == "qwen2.5-72b-instruct"


def test_parse_failure_retries_once_then_records_missing(tmp_path):
    transport = Scripted(
        [
            _ok("qwen2.5-72b-instruct", content="不是 JSON"),
            _ok("qwen2.5-72b-instruct", content="还是不行"),
            _ok("deepseek-ai/DeepSeek-V3", content='{"A":"是","B":"否"}'),
            _ok("kimi-k2.6", content='{"A":"是","B":"否"}'),
        ]
    )
    result = judges.run_judges([_item()], transport=transport, logs_dir=tmp_path)
    assert len(transport.calls) == 4
    assert transport.calls[0]["messages"] == transport.calls[1]["messages"]
    assert transport.calls[0]["temperature"] == 0
    assert transport.calls[1]["temperature"] == 0
    assert transport.calls[0]["model"] == transport.calls[1]["model"] == "qwen2.5-72b-instruct"
    label = result["judges"]["qwen"]["labels"]["c1"]
    assert label == {"A": None, "B": None}
    assert label["A"] != "否"
    assert label["B"] != "否"
    kappa_a = result["kappa"]["A"]["cohen"]
    qwen_deepseek = next(item for item in kappa_a if item["pair"] == ["qwen", "deepseek"])
    assert qwen_deepseek["n"] == 0
    assert qwen_deepseek["kappa"] is None
    assert result["kappa"]["A"]["fleiss"]["n"] == 0


def test_second_parse_attempt_can_succeed(tmp_path):
    transport = Scripted(
        [
            _ok("qwen2.5-72b-instruct", content="废话"),
            _ok("qwen2.5-72b-instruct", content='{"A":"否","B":"是"}'),
        ]
    )
    result = judges.run_judges(
        [_item()],
        transport=transport,
        logs_dir=tmp_path,
        judge_ids=("qwen",),
    )
    assert result["judges"]["qwen"]["labels"]["c1"] == {"A": "否", "B": "是"}
    assert len(transport.calls) == 2


def test_kappa_excludes_missing_and_ignores_dual_annotation():
    rows = [
        {
            "claim_id": "c1",
            "qwen": {"A": "是", "B": "否"},
            "deepseek": {"A": "是", "B": "否"},
            "kimi": {"A": "否", "B": "是"},
            "dual": {"A": "否", "B": "否"},
        },
        {
            "claim_id": "c2",
            "qwen": {"A": None, "B": "否"},
            "deepseek": {"A": "否", "B": "否"},
            "kimi": {"A": "否", "B": "否"},
        },
        {
            "claim_id": "c3",
            "qwen": {"A": "是", "B": "是"},
            "deepseek": {"A": "否", "B": "否"},
            "kimi": {"A": "是", "B": "否"},
        },
        {
            "claim_id": "c4",
            "qwen": {"A": "否", "B": "是"},
            "deepseek": {"A": "否", "B": "否"},
            "kimi": {"A": "否", "B": None},
        },
    ]
    got = judges.agreement(rows)
    without_dual = judges.agreement(
        [{key: value for key, value in row.items() if key != "dual"} for row in rows]
    )
    assert got == without_dual

    # A：qwen 与 deepseek 都有标签的是 c1 是/是、c3 是/否、c4 否/否。c2 的 qwen 缺失。
    qwen_deepseek = next(item for item in got["A"]["cohen"] if item["pair"] == ["qwen", "deepseek"])
    assert qwen_deepseek["n"] == 3
    chance = Fraction(2, 3) * Fraction(1, 3) + Fraction(1, 3) * Fraction(2, 3)
    assert qwen_deepseek["kappa"] == float((Fraction(2, 3) - chance) / (1 - chance))
    # A 上只有 c2 缺一家，Fleiss 用 c1、c3、c4。B 上 c4 的 kimi 缺失。
    assert got["A"]["fleiss"]["n"] == 3
    assert got["B"]["fleiss"]["n"] == 3
    assert got["A"]["cohen"][0]["pair"] == ["qwen", "deepseek"]
    assert got["A"]["cohen"][1]["pair"] == ["qwen", "kimi"]
    assert got["A"]["cohen"][2]["pair"] == ["deepseek", "kimi"]


def test_fleiss_matches_hand_count_and_complete_agreement_is_one():
    rows = [
        {
            "claim_id": "c1",
            "qwen": {"A": "是"},
            "deepseek": {"A": "是"},
            "kimi": {"A": "是"},
        },
        {
            "claim_id": "c2",
            "qwen": {"A": "是"},
            "deepseek": {"A": "是"},
            "kimi": {"A": "否"},
        },
        {
            "claim_id": "c3",
            "qwen": {"A": "否"},
            "deepseek": {"A": "否"},
            "kimi": {"A": "否"},
        },
    ]
    fleiss = judges.agreement(rows)["A"]["fleiss"]
    assert fleiss["n"] == 3
    assert fleiss["kappa"] == float((Fraction(7, 9) - Fraction(41, 81)) / (1 - Fraction(41, 81)))

    unanimous = [
        {
            "claim_id": "c1",
            "qwen": {"A": "是"},
            "deepseek": {"A": "是"},
            "kimi": {"A": "是"},
        }
    ]
    assert judges.agreement(unanimous)["A"]["fleiss"] == {"kappa": 1.0, "n": 1}
    assert judges.agreement([])["A"]["fleiss"] == {"kappa": None, "n": 0}


def test_logs_have_required_fields_and_no_secrets(tmp_path, monkeypatch):
    sentinels = {
        "DASHSCOPE_API_KEY": "SENTINEL_DASHSCOPE",
        "DEEPSEEK_API_KEY": "SENTINEL_DEEPSEEK",
        "MOONSHOT_API_KEY": "SENTINEL_MOONSHOT",
    }
    for key, value in sentinels.items():
        monkeypatch.setenv(key, value)
    transport = Scripted(
        [
            _ok("qwen2.5-72b-instruct"),
            _ok("deepseek-ai/DeepSeek-V3"),
            _ok("kimi-k2.6"),
        ]
    )
    judges.run_judges([_item()], transport=transport, logs_dir=tmp_path)
    blob = "\n".join(path.read_text(encoding="utf-8") for path in tmp_path.glob("*.jsonl"))
    for value in sentinels.values():
        assert value not in blob
    for judge_id, model in (
        ("qwen", "qwen2.5-72b-instruct"),
        ("deepseek", "deepseek-ai/DeepSeek-V3"),
        ("kimi", "kimi-k2.6"),
    ):
        record = json.loads((tmp_path / f"{judge_id}.jsonl").read_text(encoding="utf-8"))
        for key in _LOG_KEYS:
            assert key in record
        assert record["请求的 model"] == model
        assert record["响应回显的 model"] == model
        assert record["请求的 temperature"] == 0
        assert record["解析结果"] == {"A": "是", "B": "否"}
        user = (
            "修改前：\n修改前正文\n\n"
            "修改后：\n修改后正文\n\n"
            "证据原文：\n证据正文\n\n"
            "evidence id：\ndoc#a@T1"
        )
        digest = hashlib.sha256(f"{judges.RUBRIC}\n{user}".encode("utf-8")).hexdigest()
        assert record["提示的 sha256"] == digest
    assert json.loads((tmp_path / "qwen.jsonl").read_text(encoding="utf-8"))["思考开关"] is None
    assert json.loads((tmp_path / "kimi.jsonl").read_text(encoding="utf-8"))["思考开关"] == {
        "type": "disabled"
    }
    assert judges.default_log_dir().parts[-4:] == ("data", "exp", "patch-events", "judge-logs")


def test_real_transport_uses_fake_sdk_and_keeps_the_key_out_of_logs(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "SENTINEL_DASHSCOPE")
    captured = {}

    class _Message:
        content = '{"A":"是","B":"否"}'

    class _Choice:
        message = _Message()

    class _Usage:
        prompt_tokens = 1
        completion_tokens = 1
        total_tokens = 2

    class _Response:
        def __init__(self, model):
            self.model = model
            self.choices = [_Choice()]
            self.usage = _Usage()

    class _Completions:
        def create(self, **kwargs):
            captured["kwargs"] = kwargs
            return _Response(kwargs["model"])

    class _Chat:
        completions = _Completions()

    class _Client:
        def __init__(self, *, api_key, base_url):
            captured["api_key"] = api_key
            captured["base_url"] = base_url

        chat = _Chat()

    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr("dotenv.find_dotenv", lambda *args, **kwargs: "")
    monkeypatch.setattr("openai.OpenAI", _Client)

    judges.run_judges(
        [_item()],
        transport=judges.real_transport,
        logs_dir=tmp_path,
        judge_ids=("qwen",),
    )
    assert captured["api_key"] == "SENTINEL_DASHSCOPE"
    assert captured["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert captured["kwargs"]["model"] == "qwen2.5-72b-instruct"
    assert captured["kwargs"]["temperature"] == 0
    assert "extra_body" not in captured["kwargs"]
    log = (tmp_path / "qwen.jsonl").read_text(encoding="utf-8")
    assert "SENTINEL_DASHSCOPE" not in log
    assert "qwen-flash" not in captured["kwargs"]["model"]

    monkeypatch.setenv("DEEPSEEK_API_KEY", "SENTINEL_DEEPSEEK")
    judges.run_judges(
        [_item()],
        transport=judges.real_transport,
        logs_dir=tmp_path,
        judge_ids=("deepseek",),
    )
    assert captured["kwargs"]["model"] == "deepseek-ai/DeepSeek-V3"
    assert captured["kwargs"]["temperature"] == 0
    assert captured["kwargs"]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert "SENTINEL_DEEPSEEK" not in (tmp_path / "deepseek.jsonl").read_text(encoding="utf-8")
