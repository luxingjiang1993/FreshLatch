"""RET-01.7：x1 草稿生成脚本与 qwen-plus 抽检。

单测注入假客户端，不发 HTTP，不读正式实验配置，不写正式语料目录。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.llm import DecodingParams, TokenUsage

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_MOD_NAME = "gen_x1_drafts_ret01_7"


def _load_script():
    path = ROOT / "scripts" / "gen_x1_drafts.py"
    spec = importlib.util.spec_from_file_location(_SCRIPT_MOD_NAME, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _unload_script():
    yield
    sys.modules.pop(_SCRIPT_MOD_NAME, None)


def _cfg(**over):
    cfg = {
        "top_k": 10,
        "rrf_k": 60,
        "embed_model": "text-embedding-v4",
        "embed_dim": 1024,
        "draft_model": "qwen-flash",
        "draft_temperature": 0.7,
        "draft_seed": 11,
        "flag_model": "qwen-plus",
        "flag_thinking": False,
        "decontam_8gram_max": None,
        "lead_delta": 0.10,
        "budget_cny_max": 10,
    }
    cfg.update(over)
    return cfg


def _write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class FakeLLM:
    """注入用假客户端：记录调用，不触网。"""

    def __init__(self, content: str = "") -> None:
        self.content = content
        self.calls: list[dict] = []
        self.decoding_log: list = []
        self.token_usage = TokenUsage()

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        thinking = False
        self.calls.append(
            {
                "messages": messages,
                "decoding": decoding,
                "tools": tools,
                "thinking": thinking,
                "response_format": response_format,
            }
        )
        self.decoding_log.append(decoding)
        return SimpleNamespace(content=self.content)


def _draft_payload() -> dict:
    body = (
        "---\n"
        "doc_id: draft-doc\n"
        "as_of: T1\n"
        "source_type: private\n"
        "title: 草稿文档\n"
        "provenance: synthetic\n"
        "license: synthetic\n"
        "domain: D0\n"
        "genre: S1\n"
        "---\n"
        "## p1\n"
        "顾问备忘里写了渠道改口后的报价口径，仅作草稿。\n"
    )
    questions = {
        "queries": [
            {
                "id": "draft-q1",
                "query": "渠道纪要里报价口径后来怎么改口",
                "qtype": "paraphrase",
                "category": "hard",
                "relevant": ["draft-doc#p1@T1"],
                "distractors": [],
                "eval_intent": "草稿",
                "as_of": "T1",
            }
        ]
    }
    return {
        "documents": [{"path": "corpus/t1/draft-doc.md", "content": body}],
        "questions": questions,
    }


class _BoomOpenAI:
    def __init__(self, *args, **kwargs):
        raise AssertionError("测试进程不得构造真实 OpenAI 客户端")


def test_missing_out_exits_nonzero_without_llm(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    code = mod.main(["generate", "--config", str(cfg)], llm_client=fake)
    assert code != 0
    assert fake.calls == []


def test_null_temperature_exits_nonzero_without_llm(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg(draft_temperature=None))
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    assert not (out / "questions.json").is_file()


def test_missing_seed_exits_nonzero_without_llm(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    raw = _cfg()
    del raw["draft_seed"]
    cfg = _write_json(tmp_path / "config.json", raw)
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []


def test_flag_sidecar_has_no_gold_relevant(tmp_path: Path):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    sidecar = tmp_path / "flag-notes.json"
    fake = FakeLLM(
        json.dumps(
            {
                "id": "draft-q1",
                "suspicion": "锚可能不对",
                "relevant": ["should-not-be-written"],
            },
            ensure_ascii=False,
        )
    )
    code = mod.main(
        [
            "flag",
            "--config",
            str(cfg),
            "--in",
            str(qpath),
            "--sidecar",
            str(sidecar),
        ],
        llm_client=fake,
    )
    assert code == 0
    assert sidecar.is_file()
    dumped = sidecar.read_text(encoding="utf-8")
    data = json.loads(dumped)
    assert "relevant" not in dumped
    assert "should-not-be-written" not in dumped
    assert "gold" not in json.dumps(data, ensure_ascii=False).lower()
    assert fake.calls, "抽检必须调用假客户端"
    for call in fake.calls:
        d = call["decoding"]
        assert isinstance(d, DecodingParams)
        assert d.model == "qwen-plus"
        assert call["thinking"] is False
    assert mod.last_flag_requests
    for rec in mod.last_flag_requests:
        assert rec["model"] == "qwen-plus"
        assert rec["thinking"] is False


def test_null_decontam_prints_checker_and_still_writes(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload()
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg_obj = _cfg(decontam_8gram_max=None)
    cfg = _write_json(tmp_path / "config.json", cfg_obj)
    out = tmp_path / "drafts"
    captured: dict = {}
    real_check = mod.check_x1

    def _wrap(corpus_dir, traps_dir, questions, config, **kwargs):
        captured["config"] = config
        captured["kwargs"] = kwargs
        return real_check(corpus_dir, traps_dir, questions, config, **kwargs)

    mod.check_x1 = _wrap
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert "decontam_8gram_max 缺键或为 null" in printed
    assert (out / "questions.json").is_file()
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()
    on_disk = json.loads(cfg.read_text(encoding="utf-8"))
    assert on_disk["decontam_8gram_max"] is None
    assert 0.2 not in on_disk.values()
    passed = captured["config"]
    if isinstance(passed, dict):
        assert passed.get("decontam_8gram_max") is None
        assert 0.2 not in passed.values()
    else:
        loaded = json.loads(Path(passed).read_text(encoding="utf-8"))
        assert loaded.get("decontam_8gram_max") is None
        assert 0.2 not in loaded.values()
    assert "floor_overrides" not in captured["kwargs"]
    assert "decontam_8gram_max" not in captured["kwargs"]
    src = (ROOT / "scripts" / "gen_x1_drafts.py").read_text(encoding="utf-8")
    assert "0.2" not in src
    eval_gold = ROOT / "data" / "eval" / "retrieve_x1.json"
    assert not eval_gold.is_file()


def test_forbidden_out_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    forbidden = ROOT / "data" / "eval" / "nested-drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(forbidden)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    assert not forbidden.exists()


def test_generate_uses_flash_decoding_params(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code == 0
    assert fake.calls
    d = fake.calls[0]["decoding"]
    assert d.model == "qwen-flash"
    assert d.temperature == 0.7
    assert d.seed == 11


def test_process_does_not_construct_openai(tmp_path: Path, monkeypatch):
    import openai

    monkeypatch.setattr(openai, "OpenAI", _BoomOpenAI)
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    assert (
        mod.main(
            ["generate", "--config", str(cfg), "--out", str(out)],
            llm_client=fake,
        )
        == 0
    )
    qpath = out / "questions.json"
    sidecar = tmp_path / "flags.json"
    assert (
        mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(sidecar),
            ],
            llm_client=fake,
        )
        == 0
    )
