"""RET-01.7：x1 草稿生成脚本与 qwen-plus 抽检。

单测注入假客户端，不发 HTTP，不读正式实验配置，不写正式语料目录。
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from freshlatch.llm import DecodingParams, LLMClient, TokenUsage

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_MOD_NAME = "gen_x1_drafts_ret01_7"
EVAL_X1 = ROOT / "data" / "eval" / "retrieve_x1.json"


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


def _file_fp(path: Path):
    if not path.is_file():
        return ("absent", None, None)
    st = path.stat()
    return ("present", hashlib.sha256(path.read_bytes()).hexdigest(), st.st_mtime)


class FakeLLM:
    """注入用假客户端：记录调用，不触网。"""

    def __init__(self, content: str = "") -> None:
        self.content = content
        self.calls: list[dict] = []
        self.decoding_log: list = []
        self.token_usage = TokenUsage()

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        self.calls.append(
            {
                "messages": messages,
                "decoding": decoding,
                "tools": tools,
                "response_format": response_format,
            }
        )
        self.decoding_log.append(decoding)
        return SimpleNamespace(content=self.content)


def _doc_body(**meta_over) -> str:
    meta = {
        "doc_id": "draft-doc",
        "as_of": "T1",
        "source_type": "private",
        "title": "草稿文档",
        "provenance": "synthetic",
        "license": "synthetic",
        "domain": "D0",
        "genre": "S1",
    }
    meta.update(meta_over)
    lines = ["---"]
    for k, v in meta.items():
        if v is None:
            continue
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("## p1")
    lines.append("顾问备忘里写了渠道改口后的报价口径，仅作草稿。")
    return "\n".join(lines) + "\n"


def _draft_payload(*, body: str | None = None, questions_over: dict | None = None) -> dict:
    questions = {
        "queries": [
            {
                "id": "draft-q1",
                "query": "渠道纪要里报价口径后来怎么改口",
                "qtype": "paraphrase",
                "category": "hard",
                "relevant": ["draft-doc#p1@T1"],
                "distractors": ["trap-doc#p1@T1"],
                "answer_points": ["改口后的报价口径"],
                "eval_intent": "草稿",
                "as_of": "T1",
            }
        ]
    }
    if questions_over:
        questions["queries"][0].update(questions_over)
    return {
        "documents": [
            {
                "path": "corpus/t1/draft-doc.md",
                "content": body if body is not None else _doc_body(),
            }
        ],
        "questions": questions,
    }


class _BoomOpenAI:
    def __init__(self, *args, **kwargs):
        raise AssertionError("测试进程不得构造真实 OpenAI 客户端")


class _RecordingInner:
    """记录 chat.completions.create 的 kwargs，不发网络。"""

    def __init__(self, content: str) -> None:
        self.kwargs_list: list[dict] = []
        self._content = content
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.kwargs_list.append(kwargs)
        msg = SimpleNamespace(content=self._content)
        return SimpleNamespace(usage=None, choices=[SimpleNamespace(message=msg)])


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


def test_flag_sidecar_whitelists_note_fields(tmp_path: Path):
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
                "reason": "证据对不上正文",
                "severity": "high",
                "relevant": ["should-not-be-written"],
                "distractors": ["also-gold"],
                "qtype": "paraphrase",
                "answer_points": ["不该出现"],
                "relevant_ids": ["x"],
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
    dumped = sidecar.read_text(encoding="utf-8")
    data = json.loads(dumped)
    assert data["model"] == "qwen-plus"
    assert data["flag_thinking"] is False
    assert data["temperature"] == 0.0
    assert data["x1_flag_sidecar"] is True
    notes = data["notes"]
    assert notes == {
        "id": "draft-q1",
        "suspicion": "锚可能不对",
        "reason": "证据对不上正文",
        "severity": "high",
    }
    for banned in ("relevant", "distractors", "qtype", "answer_points", "relevant_ids", "should-not-be-written"):
        assert banned not in dumped
    assert fake.calls
    assert fake.calls[0]["decoding"].model == "qwen-plus"


def test_null_decontam_prints_checker_and_still_writes(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload()
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg_obj = _cfg(decontam_8gram_max=None)
    cfg = _write_json(tmp_path / "config.json", cfg_obj)
    out = tmp_path / "drafts"
    captured: dict = {}
    real_check = mod.check_x1
    before_x1 = _file_fp(EVAL_X1)

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
    assert _file_fp(EVAL_X1) == before_x1


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


def test_out_repo_root_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    corpus = ROOT / "data" / "corpus"
    before = sorted(p.relative_to(ROOT) for p in corpus.rglob("*") if p.is_file())
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(ROOT)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    after = sorted(p.relative_to(ROOT) for p in corpus.rglob("*") if p.is_file())
    assert before == after


def test_out_data_dir_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    data = ROOT / "data"
    before = sorted(p.relative_to(data) for p in data.rglob("*") if p.is_file())
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(data)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    after = sorted(p.relative_to(data) for p in data.rglob("*") if p.is_file())
    assert before == after


def test_nonempty_out_without_marker_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "existing"
    out.mkdir()
    keep = out / "keep-me.txt"
    keep.write_text("preserve", encoding="utf-8")
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    assert keep.read_text(encoding="utf-8") == "preserve"


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
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "queries" in prompt
    assert "relevant" not in prompt
    assert "answer_points" not in prompt
    assert "distractors" not in prompt
    assert (out / ".x1-drafts-manifest.json").is_file()


def test_model_relevant_rewritten_to_todo_owner(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload()
    assert payload["questions"]["queries"][0]["relevant"] == ["draft-doc#p1@T1"]
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg(decontam_8gram_max=0.35))
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    printed = capsys.readouterr().out
    assert code == 0
    qtext = (out / "questions.json").read_text(encoding="utf-8")
    assert "TODO-owner" in qtext
    written = json.loads(qtext)
    item = written["queries"][0]
    assert item["relevant"] == "TODO-owner"
    assert item["distractors"] == "TODO-owner"
    assert item["answer_points"] == "TODO-owner"
    assert "draft-doc#p1@T1" not in qtext
    assert "checker_exit=1" in printed
    assert "relevant 必须是列表" in printed


def test_checker_exit_1_still_writes(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg(decontam_8gram_max=0.35))
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert "checker_exit=1" in printed
    assert (out / "questions.json").is_file()
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def test_as_of_mismatch_still_writes(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload(body=_doc_body(as_of="T0"))
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert "checker_error=AssertionError" in printed
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()
    body = (out / "corpus" / "t1" / "draft-doc.md").read_text(encoding="utf-8")
    assert "as_of: T0" in body


def test_missing_doc_id_still_writes(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload(body=_doc_body(doc_id=None))
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert "checker_error=KeyError" in printed
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def test_non_json_writes_raw_and_exits_nonzero(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM("这不是 JSON")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    captured = capsys.readouterr()
    assert code != 0
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert (out / "raw-response.txt").read_text(encoding="utf-8") == "这不是 JSON"
    assert (out / ".x1-drafts-manifest.json").is_file()


def test_flag_passes_enable_thinking_false_to_create(tmp_path: Path):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    sidecar = tmp_path / "flag-notes.json"
    inner = _RecordingInner(
        json.dumps({"id": "draft-q1", "suspicion": "抽检"}, ensure_ascii=False)
    )
    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9")
    llm.client = inner
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
        llm_client=llm,
    )
    assert code == 0
    assert inner.kwargs_list
    kw = inner.kwargs_list[0]
    assert kw["model"] == "qwen-plus"
    assert kw.get("extra_body") == {"enable_thinking": False}


def test_process_does_not_construct_openai(tmp_path: Path, monkeypatch):
    import freshlatch.llm as llm_mod

    monkeypatch.setattr(llm_mod, "OpenAI", _BoomOpenAI)

    def _boom_connect(self, *args, **kwargs):
        raise AssertionError("测试进程不得发 HTTP")

    monkeypatch.setattr(socket.socket, "connect", _boom_connect)
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    before_x1 = _file_fp(EVAL_X1)
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
    assert _file_fp(EVAL_X1) == before_x1


def test_sidecar_under_data_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps({"id": "q", "suspicion": "x"}, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    qpath = _write_json(tmp_path / "questions.json", _draft_payload()["questions"])
    sidecar = ROOT / "data" / "flag-notes.json"
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
    assert code != 0
    assert fake.calls == []
    assert not sidecar.exists()


def test_sidecar_llm_py_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps({"id": "q", "suspicion": "x"}, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    qpath = _write_json(tmp_path / "questions.json", _draft_payload()["questions"])
    target = ROOT / "src" / "freshlatch" / "llm.py"
    before = target.read_bytes()
    code = mod.main(
        [
            "flag",
            "--config",
            str(cfg),
            "--in",
            str(qpath),
            "--sidecar",
            str(target),
        ],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    assert target.read_bytes() == before


def test_sidecar_existing_plain_json_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps({"id": "q", "suspicion": "x"}, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    qpath = _write_json(tmp_path / "questions.json", _draft_payload()["questions"])
    sidecar = tmp_path / "notes.json"
    sidecar.write_text('{"foo": 1}\n', encoding="utf-8")
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
    assert code != 0
    assert fake.calls == []
    assert json.loads(sidecar.read_text(encoding="utf-8")) == {"foo": 1}


def _assert_todo_questions(out: Path) -> dict:
    qtext = (out / "questions.json").read_text(encoding="utf-8")
    written = json.loads(qtext)
    assert "queries" in written
    for item in written["queries"]:
        assert item["relevant"] == "TODO-owner"
        assert item["distractors"] == "TODO-owner"
        assert item["answer_points"] == "TODO-owner"
    return written


def test_questions_list_without_queries_wrapper(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    payload = {"documents": _draft_payload()["documents"], "questions": [q]}
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code == 0
    _assert_todo_questions(out)
    assert "draft-doc#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def test_top_level_question_list_normalized(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    fake = FakeLLM(json.dumps([q], ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code == 0
    written = _assert_todo_questions(out)
    assert written["queries"][0]["id"] == "draft-q1"
    assert "draft-doc#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")


def test_single_question_object_normalized(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    payload = {"documents": _draft_payload()["documents"], "questions": q}
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code == 0
    _assert_todo_questions(out)
    assert "draft-doc#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")


def test_nested_relevant_replaced_at_question_level(tmp_path: Path):
    mod = _load_script()
    q = {
        "id": "draft-q1",
        "query": "渠道纪要里报价口径后来怎么改口",
        "qtype": "paraphrase",
        "category": "hard",
        "eval_intent": "草稿",
        "as_of": "T1",
        "nested": {
            "relevant": ["secret-gold-id"],
            "relevant_ids": ["also-secret"],
        },
        "gold": {
            "answer_points": ["不该留下"],
            "distractors": ["也不该留下"],
        },
    }
    payload = {"documents": _draft_payload()["documents"], "questions": {"queries": [q]}}
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    assert code == 0
    qtext = (out / "questions.json").read_text(encoding="utf-8")
    written = _assert_todo_questions(out)
    item = written["queries"][0]
    assert "relevant" not in item.get("nested", {})
    assert "relevant_ids" not in item.get("nested", {})
    assert "answer_points" not in item.get("gold", {})
    assert "distractors" not in item.get("gold", {})
    assert "secret-gold-id" not in qtext
    assert "also-secret" not in qtext
    assert "不该留下" not in qtext


def test_document_missing_path_writes_raw(tmp_path: Path, capsys):
    mod = _load_script()
    payload = {
        "documents": [{"content": "无路径正文"}],
        "questions": _draft_payload()["questions"],
    }
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "缺少 path" in captured.err
    assert (out / "raw-response.txt").is_file()
    assert (out / ".x1-drafts-manifest.json").is_file()
    assert not (out / "questions.json").is_file()


def test_document_escape_path_writes_raw(tmp_path: Path, capsys):
    mod = _load_script()
    payload = {
        "documents": [{"path": "../freshlatch/llm.py", "content": "不该写出"}],
        "questions": _draft_payload()["questions"],
    }
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    llm_path = ROOT / "src" / "freshlatch" / "llm.py"
    before = llm_path.read_bytes()
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "路径非法" in captured.err
    assert llm_path.read_bytes() == before
    assert (out / "raw-response.txt").is_file()
    assert not (out / "questions.json").is_file()


def test_documents_non_list_writes_raw(tmp_path: Path, capsys):
    mod = _load_script()
    payload = {
        "documents": {"path": "corpus/t1/draft-doc.md", "content": "x"},
        "questions": _draft_payload()["questions"],
    }
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=fake,
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "documents 必须是列表" in captured.err
    assert (out / "raw-response.txt").is_file()
    assert not (out / "questions.json").is_file()


def test_non_json_then_rerun_same_out(tmp_path: Path):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    first = FakeLLM("这不是 JSON")
    code1 = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=first,
    )
    assert code1 != 0
    assert (out / ".x1-drafts-manifest.json").is_file()
    second = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    code2 = mod.main(
        ["generate", "--config", str(cfg), "--out", str(out)],
        llm_client=second,
    )
    assert code2 == 0
    assert (out / "questions.json").is_file()
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()
