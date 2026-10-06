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


@pytest.fixture(autouse=True)
def _block_socket_connect(monkeypatch):
    """测试进程不得对 DashScope 或任何地址发起真实连接。"""

    def _boom(self, *args, **kwargs):
        raise AssertionError("测试进程不得发 HTTP")

    monkeypatch.setattr(socket.socket, "connect", _boom)


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


def _doc_body(*, n_chunks: int = 2, **meta_over) -> str:
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
    chunk_text = (
        "顾问备忘里写了渠道改口后的报价口径，仅作草稿。",
        "复验只核对本快照口径，旧报价不当作现行结论。",
    )
    for i in range(1, n_chunks + 1):
        lines.append(f"## p{i}")
        lines.append(chunk_text[i - 1] if i <= len(chunk_text) else f"合成草稿补充块 {i}。")
    return "\n".join(lines) + "\n"


def _batch(**over) -> dict:
    batch = {
        "batch_id": "b1",
        "genre": "S1",
        "domain": "D0",
        "as_of": "T1",
        "n_docs": 1,
        "chunks_per_doc": 2,
        "topic": "渠道纪要里的报价口径",
    }
    batch.update(over)
    return batch


def _spec(batches=None, *, with_pricing: bool = True) -> dict:
    spec: dict = {"batches": [_batch()] if batches is None else batches}
    if with_pricing:
        spec["pricing"] = {
            "input_cny_per_million": 1,
            "output_cny_per_million": 2,
            "source": "单测占位，不是脚本内置标价",
        }
    return spec


def _generate(mod, tmp_path: Path, fake, cfg: Path, out: Path, *, spec=None, max_cny: str = "100", extra=None):
    spec_path = _write_json(tmp_path / f"spec-{out.name}.json", _spec() if spec is None else spec)
    argv = [
        "generate",
        "--config",
        str(cfg),
        "--out",
        str(out),
        "--spec",
        str(spec_path),
        "--max-cny",
        str(max_cny),
    ]
    if extra:
        argv.extend(extra)
    return mod.main(argv, llm_client=fake)


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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, forbidden)
    assert code != 0
    assert fake.calls == []
    assert not forbidden.exists()


def test_out_repo_root_rejected(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    corpus = ROOT / "data" / "corpus"
    before = sorted(p.relative_to(ROOT) for p in corpus.rglob("*") if p.is_file())
    code = _generate(mod, tmp_path, fake, cfg, ROOT)
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
    code = _generate(mod, tmp_path, fake, cfg, data)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
    assert code != 0
    assert fake.calls == []
    assert keep.read_text(encoding="utf-8") == "preserve"


def test_generate_uses_flash_decoding_params(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    assert "不得以版权原文为模板整段改写" in prompt
    assert "不得给出金标" in prompt
    assert "只返回 JSON" in prompt
    assert (out / ".x1-drafts-manifest.json").is_file()


def test_model_relevant_rewritten_to_todo_owner(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload()
    assert payload["questions"]["queries"][0]["relevant"] == ["draft-doc#p1@T1"]
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg(decontam_8gram_max=0.35))
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
    printed = capsys.readouterr().out
    assert code == 0
    assert "checker_exit=1" in printed
    assert (out / "questions.json").is_file()
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def test_as_of_mismatch_voids_batch(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload(body=_doc_body(as_of="T0"))
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code != 0
    assert "Traceback" not in captured.err
    assert "as_of" in captured.err
    assert not (out / "corpus" / "t1" / "draft-doc.md").exists()
    assert (out / "raw-response.txt").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["b1"]["status"] == "failed"


def test_missing_doc_id_voids_batch(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload(body=_doc_body(doc_id=None))
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code != 0
    assert "Traceback" not in captured.err
    assert "缺键" in captured.err
    assert not (out / "corpus" / "t1" / "draft-doc.md").exists()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["b1"]["status"] == "failed"


def test_non_json_writes_raw_and_exits_nonzero(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM("这不是 JSON")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code != 0
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert (out / "raw-response.txt").read_text(encoding="utf-8") == "这不是 JSON"
    assert (out / ".x1-drafts-manifest.json").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert "不得当标签使用" in captured.err
    assert "不得当标签使用" in manifest["raw_response_note"]


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
    assert _generate(mod, tmp_path, fake, cfg, out) == 0
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
    code = _generate(mod, tmp_path, fake, cfg, out)
    assert code == 0
    _assert_todo_questions(out)
    assert "draft-doc#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def test_top_level_question_list_normalized(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    normalized = mod._normalize_generate_payload([q])
    assert normalized["questions"]["queries"][0]["relevant"] == "TODO-owner"
    assert normalized["questions"]["queries"][0]["id"] == "draft-q1"
    assert "draft-doc#p1@T1" not in json.dumps(normalized["questions"], ensure_ascii=False)
    fake = FakeLLM(json.dumps([q], ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    assert code != 0
    assert not (out / "questions.json").is_file()


def test_single_question_object_normalized(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    payload = {"documents": _draft_payload()["documents"], "questions": q}
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code = _generate(mod, tmp_path, fake, cfg, out)
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
    code1 = _generate(mod, tmp_path, first, cfg, out)
    assert code1 != 0
    assert (out / ".x1-drafts-manifest.json").is_file()
    second = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    code2 = _generate(mod, tmp_path, second, cfg, out)
    assert code2 == 0
    assert (out / "questions.json").is_file()
    assert (out / "corpus" / "t1" / "draft-doc.md").is_file()


def _assert_document_path_failure(tmp_path: Path, capsys, documents, *, err_substr: str) -> None:
    """非法文档路径必须走 raw-response 失败路径，不得 traceback。"""
    mod = _load_script()
    payload = {
        "documents": documents,
        "questions": _draft_payload()["questions"],
    }
    raw = json.dumps(payload, ensure_ascii=False)
    fake = FakeLLM(raw)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    llm_path = ROOT / "src" / "freshlatch" / "llm.py"
    before_llm = llm_path.read_bytes()
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert err_substr in captured.err
    assert "不得当标签使用" in captured.err
    assert (out / "raw-response.txt").read_text(encoding="utf-8") == raw
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert "不得当标签使用" in manifest["raw_response_note"]
    assert not (out / "questions.json").is_file()
    assert llm_path.read_bytes() == before_llm


@pytest.mark.parametrize(
    "raw_path",
    [
        "C:x",
        "C:data/corpus/t1/x.md",
        "C:\\abs\\x.md",
        "\\\\server\\share\\x.md",
        "corpus\\..\\..\\x.md",
        ".",
    ],
)
def test_document_windows_and_root_paths_write_raw(tmp_path: Path, capsys, raw_path: str):
    """Linux / Windows CI 同一套用例：盘符、UNC、反斜杠穿越、暂存根均拒绝。"""
    _assert_document_path_failure(
        tmp_path,
        capsys,
        [{"path": raw_path, "content": "不该写出"}],
        err_substr="路径非法",
    )


def test_document_corpus_file_dir_collision_writes_raw(tmp_path: Path, capsys):
    _assert_document_path_failure(
        tmp_path,
        capsys,
        [
            {"path": "corpus", "content": "文件伪装成 corpus 目录"},
            {"path": "corpus/t1/d.md", "content": _doc_body()},
        ],
        err_substr="文件与目录冲突",
    )


def test_document_write_oserror_writes_raw(tmp_path: Path, capsys, monkeypatch):
    mod = _load_script()
    real_write = Path.write_text

    def _boom(self, *args, **kwargs):
        if self.suffix == ".md":
            raise OSError("simulated write failure")
        return real_write(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _boom)
    payload = _draft_payload()
    raw = json.dumps(payload, ensure_ascii=False)
    fake = FakeLLM(raw)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert "写入草稿失败" in captured.err
    assert "不得当标签使用" in captured.err
    assert (out / "raw-response.txt").read_text(encoding="utf-8") == raw
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert "不得当标签使用" in manifest["raw_response_note"]
    assert not (out / "questions.json").is_file()


def test_document_path_syntax_rejects_drive_unc_backslash_and_dot():
    """不依赖本机 Path 语义：Linux CI 也能拦住 Windows 盘符/UNC。"""
    mod = _load_script()
    samples = [
        "C:x",
        "C:data/corpus/t1/x.md",
        "C:\\abs\\x.md",
        "\\\\server\\share\\x.md",
        "corpus\\..\\..\\x.md",
        ".",
        "../x.md",
        "/abs/x.md",
    ]
    for raw in samples:
        err = mod._document_path_syntax_error(raw)
        assert err, f"应拒绝路径 {raw!r}"
        assert "路径非法" in err
    assert mod._document_path_syntax_error("corpus/t1/d.md") is None
    assert mod._document_paths_collide(["corpus", "corpus/t1/d.md"])
    assert not mod._document_paths_collide(["corpus/t1/d.md", "corpus/t1/e.md"])


class QueueLLM(FakeLLM):
    """按顺序返回预设回复，并可在每次调用后累加 token。"""

    def __init__(self, contents: list[str], *, prompt_each: int = 0, completion_each: int = 0) -> None:
        super().__init__(contents[0] if contents else "")
        self.contents = list(contents)
        self.prompt_each = prompt_each
        self.completion_each = completion_each
        self.index = 0

    def chat(self, messages, *, tools=None, decoding=None, response_format=None):
        if self.index >= len(self.contents):
            raise AssertionError("模型调用次数超过准备的回复")
        self.content = self.contents[self.index]
        self.index += 1
        message = super().chat(
            messages,
            tools=tools,
            decoding=decoding,
            response_format=response_format,
        )
        if self.prompt_each or self.completion_each:
            self.token_usage.add(self.prompt_each, self.completion_each)
        return message


def _batch_payload(batch: dict, *, doc_id: str, qid: str, body: str | None = None, documents=None) -> dict:
    as_of = batch["as_of"]
    folder = "traps" if batch["genre"] == "S7" else "corpus"
    meta = {
        "doc_id": doc_id,
        "as_of": as_of,
        "source_type": "internal",
        "title": f"{doc_id} 标题",
        "provenance": "synthetic",
        "license": "synthetic",
        "domain": batch["domain"],
        "genre": batch["genre"],
    }
    if batch["genre"] == "P2":
        meta["data_source_url"] = "https://www.stats.gov.cn/sj/zxfb/"
        meta["attribution"] = "引自国家统计局网站 www.stats.gov.cn"
    content = body if body is not None else _doc_body(n_chunks=batch["chunks_per_doc"], **meta)
    docs = documents if documents is not None else [{"path": f"{folder}/{as_of.lower()}/{doc_id}.md", "content": content}]
    question = {
        "id": qid,
        "query": f"{doc_id} 的复验问题",
        "qtype": "paraphrase",
        "category": "hard",
        "relevant": [f"{doc_id}#p1@{as_of}"],
        "distractors": ["old#p1@T0"],
        "answer_points": ["不该留下的金标"],
        "eval_intent": "草稿",
        "as_of": as_of,
        "nested": {"relevant_ids": ["secret-gold"]},
    }
    return {"documents": docs, "questions": {"queries": [question]}}


def test_multi_batch_merge_strips_gold(tmp_path: Path):
    mod = _load_script()
    first = _batch(batch_id="s1t1", as_of="T1")
    second = _batch(batch_id="s2t0", genre="S2", domain="D1", as_of="T0", topic="访谈改口")
    fake = QueueLLM(
        [
            json.dumps(_batch_payload(first, doc_id="memo-a", qid="q-a"), ensure_ascii=False),
            json.dumps(_batch_payload(second, doc_id="memo-b", qid="q-b"), ensure_ascii=False),
        ]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "merged"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([first, second]))
    assert code == 0
    assert fake.index == 2
    assert (out / "corpus" / "t1" / "memo-a.md").is_file()
    assert (out / "corpus" / "t0" / "memo-b.md").is_file()
    written = _assert_todo_questions(out)
    assert [item["id"] for item in written["queries"]] == ["q-a", "q-b"]
    qtext = (out / "questions.json").read_text(encoding="utf-8")
    assert "memo-a#p1@T1" not in qtext
    assert "不该留下的金标" not in qtext
    assert "old#p1@T0" not in qtext
    assert "secret-gold" not in qtext
    assert "relevant_ids" not in qtext


def test_question_id_conflict_stops_later_batches(tmp_path: Path, capsys):
    mod = _load_script()
    batches = [
        _batch(batch_id="a", topic="第一批"),
        _batch(batch_id="b", topic="第二批"),
        _batch(batch_id="c", topic="第三批"),
    ]
    payloads = [
        _batch_payload(batches[0], doc_id="d1", qid="same"),
        _batch_payload(batches[1], doc_id="d2", qid="same"),
        _batch_payload(batches[2], doc_id="d3", qid="other"),
    ]
    fake = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "conflict"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec(batches))
    captured = capsys.readouterr()
    assert code != 0
    assert "冲突" in captured.err
    assert "Traceback" not in captured.err
    assert fake.index == 2
    assert (out / "corpus" / "t1" / "d1.md").is_file()
    assert not (out / "corpus" / "t1" / "d2.md").exists()
    assert not (out / "corpus" / "t1" / "d3.md").exists()
    written = json.loads((out / "questions.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in written["queries"]] == ["same"]


def test_bad_frontmatter_voids_whole_batch_and_continues(tmp_path: Path, capsys):
    mod = _load_script()
    bad = _batch(batch_id="bad", n_docs=2, topic="缺标题")
    good = _batch(batch_id="good", topic="下一批")
    ok_doc = {
        "path": "corpus/t1/ok-doc.md",
        "content": _doc_body(doc_id="ok-doc"),
    }
    broken = {
        "path": "corpus/t1/bad-doc.md",
        "content": _doc_body(doc_id="bad-doc", title=None),
    }
    question = _draft_payload()["questions"]["queries"][0]
    first_payload = {"documents": [ok_doc, broken], "questions": {"queries": [question]}}
    second_payload = _batch_payload(good, doc_id="later-doc", qid="q-later")
    fake = QueueLLM(
        [
            json.dumps(first_payload, ensure_ascii=False),
            json.dumps(second_payload, ensure_ascii=False),
        ]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "void-batch"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([bad, good]))
    captured = capsys.readouterr()
    assert code != 0
    assert "缺键" in captured.err
    assert fake.index == 2
    assert not (out / "corpus" / "t1" / "ok-doc.md").exists()
    assert not (out / "corpus" / "t1" / "bad-doc.md").exists()
    assert (out / "corpus" / "t1" / "later-doc.md").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["bad"]["status"] == "failed"
    assert manifest["batches"]["good"]["status"] == "ok"
    assert (out / "raw" / "bad.txt").is_file()


@pytest.mark.parametrize("n_chunks", [1, 7])
def test_chunk_count_out_of_range_voids_whole_batch(tmp_path: Path, capsys, n_chunks: int):
    mod = _load_script()
    batch = _batch(batch_id="chunks", n_docs=2)
    documents = [
        {"path": "corpus/t1/ok-chunks.md", "content": _doc_body(doc_id="ok-chunks")},
        {
            "path": "corpus/t1/bad-chunks.md",
            "content": _doc_body(doc_id="bad-chunks", n_chunks=n_chunks),
        },
    ]
    payload = {
        "documents": documents,
        "questions": _draft_payload()["questions"],
    }
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / f"chunks-{n_chunks}"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
    captured = capsys.readouterr()
    assert code != 0
    assert "块数越界" in captured.err
    assert "Traceback" not in captured.err
    assert not (out / "corpus" / "t1" / "ok-chunks.md").exists()
    assert not (out / "corpus" / "t1" / "bad-chunks.md").exists()
    assert (out / "raw-response.txt").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["chunks"]["status"] == "failed"


def test_s7_lands_in_traps(tmp_path: Path):
    mod = _load_script()
    batch = _batch(batch_id="s7", genre="S7", domain="D1", as_of="T0", topic="检索陷阱")
    fake = QueueLLM(
        [json.dumps(_batch_payload(batch, doc_id="trap-a", qid="q-trap"), ensure_ascii=False)]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "traps-out"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
    assert code == 0
    assert fake.index == 1
    assert (out / "traps" / "t0" / "trap-a.md").is_file()
    assert not (out / "corpus" / "t0" / "trap-a.md").exists()
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "traps/t0" in prompt
    assert "不得以版权原文为模板整段改写" in prompt


def test_estimate_only_skips_model_and_requires_pricing(tmp_path: Path, capsys):
    mod = _load_script()
    batches = [
        _batch(batch_id="e1", n_docs=2, chunks_per_doc=3, topic="估价甲"),
        _batch(batch_id="e2", as_of="T0", topic="估价乙"),
    ]
    spec = _spec(batches)
    fake = FakeLLM("不应调用")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "est"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=spec, extra=["--estimate-only"])
    printed = capsys.readouterr().out
    assert code == 0
    assert fake.calls == []
    assert not out.exists()
    estimated = mod._estimate_spec(spec)
    assert estimated["batches"] == 2
    assert estimated["input_tokens"] == sum(len(mod._build_batch_prompt(b)) for b in batches)
    assert estimated["output_tokens"] == (2 * 3 * 256 + 2 * 128) + (1 * 2 * 256 + 1 * 128)
    assert f"batches={estimated['batches']}" in printed
    assert f"input_tokens={estimated['input_tokens']} 估" in printed
    assert f"output_tokens={estimated['output_tokens']} 估" in printed
    assert f"cny={estimated['cny']:.8f} 估" in printed
    assert "估" in printed

    missing = _spec(batches, with_pricing=False)
    fake_missing = FakeLLM("不应调用")
    code_missing = _generate(
        mod,
        tmp_path,
        fake_missing,
        cfg,
        tmp_path / "est-missing",
        spec=missing,
        extra=["--estimate-only"],
    )
    assert code_missing != 0
    assert fake_missing.calls == []

    null_price = _spec([batches[0]])
    null_price["pricing"]["input_cny_per_million"] = None
    fake_null = FakeLLM("不应调用")
    code_null = _generate(
        mod,
        tmp_path,
        fake_null,
        cfg,
        tmp_path / "est-null",
        spec=null_price,
        extra=["--estimate-only"],
    )
    assert code_null != 0
    assert fake_null.calls == []

    fake_run = FakeLLM("不应调用")
    code_run = _generate(mod, tmp_path, fake_run, cfg, tmp_path / "run-missing", spec=missing)
    assert code_run != 0
    assert fake_run.calls == []


def test_budget_stops_before_next_batch(tmp_path: Path, capsys):
    mod = _load_script()
    batches = [
        _batch(batch_id="p1", topic="第一批"),
        _batch(batch_id="p2", topic="第二批"),
        _batch(batch_id="p3", topic="第三批"),
    ]
    payloads = [
        _batch_payload(batch, doc_id=f"doc-{batch['batch_id']}", qid=f"q-{batch['batch_id']}")
        for batch in batches
    ]
    spec = _spec(batches)
    spec["pricing"]["input_cny_per_million"] = 1
    spec["pricing"]["output_cny_per_million"] = 1
    fake = QueueLLM(
        [json.dumps(item, ensure_ascii=False) for item in payloads],
        prompt_each=1_000_000,
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "budget"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=spec, max_cny="1")
    captured = capsys.readouterr()
    assert code != 0
    assert "max-cny" in captured.err
    assert fake.index == 1
    assert (out / "corpus" / "t1" / "doc-p1.md").is_file()
    assert not (out / "corpus" / "t1" / "doc-p2.md").exists()
    assert not (out / "corpus" / "t1" / "doc-p3.md").exists()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["stop_reason"] == "budget"
    assert manifest["spent_cny"] >= 1
    assert manifest["batches"]["p1"]["status"] == "ok"
    assert "p2" not in manifest["batches"]


def test_resume_skips_completed_batches(tmp_path: Path):
    mod = _load_script()
    done = _batch(batch_id="done", topic="已完成")
    todo = _batch(batch_id="todo", topic="待生成", domain="D2")
    done_payload = _batch_payload(done, doc_id="done-doc", qid="q-done")
    todo_payload = _batch_payload(todo, doc_id="todo-doc", qid="q-todo")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "resume"
    first = QueueLLM([json.dumps(done_payload, ensure_ascii=False)])
    assert _generate(mod, tmp_path, first, cfg, out, spec=_spec([done])) == 0
    assert first.index == 1

    class _BoomLLM(FakeLLM):
        def chat(self, *args, **kwargs):
            raise AssertionError("已完成批次不应再次调用模型")

    assert _generate(mod, tmp_path, _BoomLLM("不应调用"), cfg, out, spec=_spec([done])) == 0
    second = QueueLLM([json.dumps(todo_payload, ensure_ascii=False)])
    assert _generate(mod, tmp_path, second, cfg, out, spec=_spec([done, todo])) == 0
    assert second.index == 1
    assert "todo" in second.calls[0]["messages"][0]["content"]
    assert (out / "corpus" / "t1" / "done-doc.md").is_file()
    assert (out / "corpus" / "t1" / "todo-doc.md").is_file()
    written = json.loads((out / "questions.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in written["queries"]] == ["q-done", "q-todo"]
    for item in written["queries"]:
        assert item["relevant"] == "TODO-owner"
        assert item["answer_points"] == "TODO-owner"
        assert item["distractors"] == "TODO-owner"


def test_must_include_passed_through_and_p2_attribution(tmp_path: Path, capsys):
    mod = _load_script()
    fact = "2023 年修订后 1294272 亿元、比初步核算增 33690 亿元"
    batch = _batch(
        batch_id="p2ok",
        genre="P2",
        domain="D3",
        topic="全国 GDP 叙述自写",
        must_include=[fact],
    )
    fake = QueueLLM(
        [json.dumps(_batch_payload(batch, doc_id="gdp", qid="q-gdp"), ensure_ascii=False)]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "p2"
    assert _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch])) == 0
    prompt = fake.calls[0]["messages"][0]["content"]
    assert fact in prompt
    body = (out / "corpus" / "t1" / "gdp.md").read_text(encoding="utf-8")
    assert "attribution: 引自国家统计局网站 www.stats.gov.cn" in body
    assert "data_source_url:" in body

    bad = _batch(batch_id="p2bad", genre="P2", domain="D3", topic="错误出处")
    bad_body = _doc_body(
        doc_id="gdp-bad",
        genre="P2",
        domain="D3",
        data_source_url="https://www.stats.gov.cn/sj/zxfb/",
        attribution="引自别处",
    )
    bad_fake = FakeLLM(
        json.dumps(_batch_payload(bad, doc_id="gdp-bad", qid="q-bad", body=bad_body), ensure_ascii=False)
    )
    bad_out = tmp_path / "p2-bad"
    code = _generate(mod, tmp_path, bad_fake, cfg, bad_out, spec=_spec([bad]))
    captured = capsys.readouterr()
    assert code != 0
    assert "attribution" in captured.err
    assert not (bad_out / "corpus" / "t1" / "gdp-bad.md").exists()


def test_example_spec_targets_synthetic_chunks(tmp_path: Path):
    mod = _load_script()
    spec = json.loads((ROOT / "scripts" / "x1_draft_spec.example.json").read_text(encoding="utf-8"))
    loaded = mod._load_spec(ROOT / "scripts" / "x1_draft_spec.example.json")
    assert isinstance(loaded, dict)
    genres = {batch["genre"] for batch in spec["batches"]}
    assert genres == {f"S{i}" for i in range(1, 8)} | {"P2"}
    total = sum(batch["n_docs"] * batch["chunks_per_doc"] for batch in spec["batches"])
    assert total == 474
    assert spec["pricing"]["input_cny_per_million"] is None
    assert spec["pricing"]["output_cny_per_million"] is None
    assert isinstance(spec["pricing"]["source"], str) and spec["pricing"]["source"].strip()
    for batch in spec["batches"]:
        assert 2 <= batch["chunks_per_doc"] <= 6
        if batch["genre"] == "P2":
            assert batch["must_include"]
    fake = FakeLLM("不应调用")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    code = _generate(
        mod,
        tmp_path,
        fake,
        cfg,
        tmp_path / "example-est",
        spec=spec,
        extra=["--estimate-only"],
    )
    assert code != 0
    assert fake.calls == []


def test_spec_chunks_per_doc_out_of_range_skips_model(tmp_path: Path):
    mod = _load_script()
    fake = FakeLLM("{}")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    code = _generate(
        mod,
        tmp_path,
        fake,
        cfg,
        tmp_path / "bad-spec",
        spec=_spec([_batch(chunks_per_doc=7)]),
    )
    assert code != 0
    assert fake.calls == []
