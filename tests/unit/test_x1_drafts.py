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
    """注入用假客户端：记录调用，不触网。默认记 1+1 token，避免被用量缺失判失败。"""

    def __init__(self, content: str = "", *, record_usage: bool = True) -> None:
        self.content = content
        self.calls: list[dict] = []
        self.decoding_log: list = []
        self.token_usage = TokenUsage()
        self.record_usage = record_usage
        self.finish_reason = "stop"

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
        if self.record_usage:
            self.token_usage.add(1, 1)
        return SimpleNamespace(content=self.content, finish_reason=self.finish_reason)


def _doc_body(*, n_chunks: int = 2, **meta_over) -> str:
    meta = {
        "doc_id": "b1-draft",
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


def _pricing_block(source: str) -> dict:
    return {
        "input_cny_per_million": 1,
        "output_cny_per_million": 2,
        "source": source,
    }


def _spec(batches=None, *, with_pricing: bool = True) -> dict:
    spec: dict = {"batches": [_batch()] if batches is None else batches}
    if with_pricing:
        spec["pricing"] = _pricing_block("单测占位，不是脚本内置标价")
        spec["flag_pricing"] = _pricing_block("单测抽检占位，不是脚本内置标价")
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


def _flag_extra(tmp_path: Path, name: str) -> list[str]:
    spec_path = _write_json(
        tmp_path / name,
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )
    return ["--spec", str(spec_path), "--max-cny", "100"]


def _draft_payload(*, body: str | None = None, questions_over: dict | None = None) -> dict:
    questions = {
        "queries": [
            {
                "id": "draft-q1",
                "query": "渠道纪要里报价口径后来怎么改口",
                "qtype": "paraphrase",
                "category": "hard",
                "relevant": ["b1-draft#p1@T1"],
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
                "path": "corpus/t1/b1-draft.md",
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
        self.max_retries = 2
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **kwargs):
        self.kwargs_list.append(kwargs)
        msg = SimpleNamespace(content=self._content)
        usage = SimpleNamespace(prompt_tokens=1, completion_tokens=1)
        choice = SimpleNamespace(message=msg, finish_reason="stop")
        return SimpleNamespace(usage=usage, choices=[choice])


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
            *_flag_extra(tmp_path, "flag-spec-notes.json"),
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
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()
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
    assert "不要另给 frontmatter 字段" in prompt
    assert "as_of: T1" in prompt
    assert "禁止写成日期" in prompt
    assert "qtype" not in prompt
    assert "^b1-[a-z0-9-]+$" in prompt
    assert '"path":"corpus/t1/b1-memo.md"' in prompt
    assert "题目 id 必须形如 b1-q1" in prompt
    assert "文件名必须是 <doc_id>.md" in prompt
    assert "目标文件已存在时，该批校验失败" not in prompt
    assert (out / ".x1-drafts-manifest.json").is_file()


def test_model_relevant_rewritten_to_todo_owner(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _draft_payload()
    assert payload["questions"]["queries"][0]["relevant"] == ["b1-draft#p1@T1"]
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
    assert item["qtype"] == "TODO-owner"
    assert "b1-draft#p1@T1" not in qtext
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
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()


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
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()
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
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()
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
            *_flag_extra(tmp_path, "flag-spec-thinking.json"),
        ],
        llm_client=llm,
    )
    assert code == 0
    assert inner.kwargs_list
    kw = inner.kwargs_list[0]
    assert kw["model"] == "qwen-plus"
    assert kw.get("extra_body") == {"enable_thinking": False}
    assert isinstance(kw.get("max_tokens"), int) and kw["max_tokens"] > 0
    assert inner.max_retries == 0


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
                *_flag_extra(tmp_path, "flag-spec-process.json"),
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
            *_flag_extra(tmp_path, "flag-spec-data.json"),
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
            *_flag_extra(tmp_path, "flag-spec-llm.json"),
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
            *_flag_extra(tmp_path, "flag-spec-plain.json"),
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
        assert item["qtype"] == "TODO-owner"
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
    assert "b1-draft#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()


def test_top_level_question_list_normalized(tmp_path: Path):
    mod = _load_script()
    q = _draft_payload()["questions"]["queries"][0]
    normalized = mod._normalize_generate_payload([q])
    assert normalized["questions"]["queries"][0]["relevant"] == "TODO-owner"
    assert normalized["questions"]["queries"][0]["id"] == "draft-q1"
    assert "b1-draft#p1@T1" not in json.dumps(normalized["questions"], ensure_ascii=False)
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
    assert "b1-draft#p1@T1" not in (out / "questions.json").read_text(encoding="utf-8")


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
        "documents": {"path": "corpus/t1/b1-draft.md", "content": "x"},
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
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()


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


def test_document_write_oserror_leaves_committing(tmp_path: Path, capsys, monkeypatch):
    mod = _load_script()
    real_write = mod._atomic_write_text

    def _boom(path, text):
        if Path(path).suffix == ".md":
            raise OSError("simulated write failure")
        return real_write(path, text)

    monkeypatch.setattr(mod, "_atomic_write_text", _boom)
    payload = _draft_payload()
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "drafts"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code == 1
    assert "Traceback" not in captured.err
    assert "Traceback" not in captured.out
    assert "写入草稿失败" in captured.err
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["b1"]["status"] == "committing"
    assert manifest["batches"]["b1"]["paths"] == ["corpus/t1/b1-draft.md"]
    assert not (out / "questions.json").is_file()
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()


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
            json.dumps(_batch_payload(first, doc_id="s1t1-memo-a", qid="q-a"), ensure_ascii=False),
            json.dumps(_batch_payload(second, doc_id="s2t0-memo-b", qid="q-b"), ensure_ascii=False),
        ]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "merged"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([first, second]))
    assert code == 0
    assert fake.index == 2
    assert (out / "corpus" / "t1" / "s1t1-memo-a.md").is_file()
    assert (out / "corpus" / "t0" / "s2t0-memo-b.md").is_file()
    written = _assert_todo_questions(out)
    assert [item["id"] for item in written["queries"]] == ["s1t1-q-a", "s2t0-q-b"]
    qtext = (out / "questions.json").read_text(encoding="utf-8")
    assert "s1t1-memo-a#p1@T1" not in qtext
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
    second = _batch_payload(batches[1], doc_id="b-d2", qid="q1")
    repeated = dict(second["questions"]["queries"][0])
    repeated["id"] = "q1"
    second["questions"]["queries"].append(repeated)
    payloads = [
        _batch_payload(batches[0], doc_id="a-d1", qid="same"),
        second,
        _batch_payload(batches[2], doc_id="c-d3", qid="other"),
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
    assert (out / "corpus" / "t1" / "a-d1.md").is_file()
    assert not (out / "corpus" / "t1" / "b-d2.md").exists()
    assert not (out / "corpus" / "t1" / "c-d3.md").exists()
    written = json.loads((out / "questions.json").read_text(encoding="utf-8"))
    assert [item["id"] for item in written["queries"]] == ["a-same"]


def test_bad_frontmatter_voids_whole_batch_and_continues(tmp_path: Path, capsys):
    mod = _load_script()
    bad = _batch(batch_id="bad", n_docs=2, topic="缺标题")
    good = _batch(batch_id="good", topic="下一批")
    ok_doc = {
        "path": "corpus/t1/bad-ok.md",
        "content": _doc_body(doc_id="bad-ok"),
    }
    broken = {
        "path": "corpus/t1/bad-doc.md",
        "content": _doc_body(doc_id="bad-doc", title=None),
    }
    question = _draft_payload()["questions"]["queries"][0]
    first_payload = {"documents": [ok_doc, broken], "questions": {"queries": [question]}}
    second_payload = _batch_payload(good, doc_id="good-later", qid="q-later")
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
    assert not (out / "corpus" / "t1" / "bad-ok.md").exists()
    assert not (out / "corpus" / "t1" / "bad-doc.md").exists()
    assert (out / "corpus" / "t1" / "good-later.md").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["bad"]["status"] == "failed"
    assert manifest["batches"]["good"]["status"] == "ok"
    assert (out / "raw" / "bad.txt").is_file()


@pytest.mark.parametrize("n_chunks", [1, 7])
def test_chunk_count_out_of_range_voids_whole_batch(tmp_path: Path, capsys, n_chunks: int):
    mod = _load_script()
    batch = _batch(batch_id="chunks", n_docs=2)
    documents = [
        {"path": "corpus/t1/chunks-ok.md", "content": _doc_body(doc_id="chunks-ok")},
        {
            "path": "corpus/t1/chunks-bad.md",
            "content": _doc_body(doc_id="chunks-bad", n_chunks=n_chunks),
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
    assert not (out / "corpus" / "t1" / "chunks-ok.md").exists()
    assert not (out / "corpus" / "t1" / "chunks-bad.md").exists()
    assert (out / "raw-response.txt").is_file()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["batches"]["chunks"]["status"] == "failed"


def test_s7_lands_in_traps(tmp_path: Path):
    mod = _load_script()
    batch = _batch(batch_id="s7", genre="S7", domain="D1", as_of="T0", topic="检索陷阱")
    fake = QueueLLM(
        [json.dumps(_batch_payload(batch, doc_id="s7-trap-a", qid="q-trap"), ensure_ascii=False)]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "traps-out"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
    assert code == 0
    assert fake.index == 1
    assert (out / "traps" / "t0" / "s7-trap-a.md").is_file()
    assert not (out / "corpus" / "t0" / "s7-trap-a.md").exists()
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
    assert estimated["input_tokens"] == 2 * sum(len(mod._build_batch_prompt(b)) for b in batches)
    assert estimated["output_tokens"] == (2 * 3 * 256 + 2 * 128 + 2 * 128) + (1 * 2 * 256 + 1 * 128 + 1 * 128)
    assert f"batches={estimated['batches']}" in printed
    assert f"input_tokens={estimated['input_tokens']} 估" in printed
    assert f"output_tokens={estimated['output_tokens']} 估" in printed
    assert f"cny={estimated['cny']:.8f} 估" in printed
    assert f"pricing_source={spec['pricing']['source']}" in printed
    assert f"flag_cny={estimated['flag_cny']:.8f} 估" in printed
    assert f"flag_pricing_source={spec['flag_pricing']['source']}" in printed
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
        _batch(batch_id="b1", topic="第一批"),
        _batch(batch_id="b2", topic="第二批"),
        _batch(batch_id="b3", topic="第三批"),
    ]
    payloads = [
        _batch_payload(batch, doc_id=f"{batch['batch_id']}-doc", qid=f"q-{batch['batch_id']}")
        for batch in batches
    ]
    spec = _spec(batches)
    spec["pricing"]["input_cny_per_million"] = 1
    spec["pricing"]["output_cny_per_million"] = 1
    upper_in = mod._input_token_upper(mod._build_batch_prompt(batches[0]))
    upper_out = mod._output_token_upper(batches[0])
    cap = mod._cost_cny(upper_in, upper_out, 1, 1)
    fake = QueueLLM(
        [json.dumps(item, ensure_ascii=False) for item in payloads],
        prompt_each=upper_in - 1,
        completion_each=upper_out - 1,
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "budget"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=spec, max_cny=repr(cap))
    captured = capsys.readouterr()
    assert code != 0
    assert "max-cny" in captured.err
    assert fake.index == 1
    assert (out / "corpus" / "t1" / "b1-doc.md").is_file()
    assert not (out / "corpus" / "t1" / "b2-doc.md").exists()
    assert not (out / "corpus" / "t1" / "b3-doc.md").exists()
    manifest = json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))
    assert manifest["stop_reason"] == "budget"
    assert manifest["spent_cny"] == pytest.approx(cap)
    assert manifest["batches"]["b1"]["status"] == "ok"
    assert "b2" not in manifest["batches"]


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
    assert [item["id"] for item in written["queries"]] == ["done-q-done", "todo-q-todo"]
    for item in written["queries"]:
        assert item["relevant"] == "TODO-owner"
        assert item["answer_points"] == "TODO-owner"
        assert item["distractors"] == "TODO-owner"


def test_must_include_passed_through_and_p2_rejected(tmp_path: Path, capsys):
    mod = _load_script()
    fact = "令 13 第四条清洗后不足 200 字不拆块"
    batch = _batch(
        batch_id="s6ok",
        genre="S6",
        domain="D3",
        topic="P1 缺口事实",
        must_include=[fact],
    )
    fake = QueueLLM(
        [json.dumps(_batch_payload(batch, doc_id="s6ok-gap", qid="q-gap"), ensure_ascii=False)]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "s6"
    assert _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch])) == 0
    prompt = fake.calls[0]["messages"][0]["content"]
    assert fact in prompt
    assert "国家统计局" not in prompt
    assert "stats.gov.cn" not in prompt

    p2 = _batch(batch_id="p2no", genre="P2", domain="D3", topic="不许模型写")
    p2_fake = FakeLLM("不应调用")
    p2_out = tmp_path / "p2"
    code = _generate(mod, tmp_path, p2_fake, cfg, p2_out, spec=_spec([p2]))
    captured = capsys.readouterr()
    assert code != 0
    assert "P2 由人按国家统计局公告手写，不由模型生成" in captured.err
    assert p2_fake.calls == []

    bad = _batch(batch_id="s1bad", topic="错误出处")
    bad_body = _doc_body(
        doc_id="s1bad-gdp",
        attribution="引自国家统计局网站 www.stats.gov.cn",
    )
    bad_fake = FakeLLM(
        json.dumps(_batch_payload(bad, doc_id="s1bad-gdp", qid="q-bad", body=bad_body), ensure_ascii=False)
    )
    bad_out = tmp_path / "nbs-bad"
    code_bad = _generate(mod, tmp_path, bad_fake, cfg, bad_out, spec=_spec([bad]))
    captured_bad = capsys.readouterr()
    assert code_bad != 0
    assert bad_fake.calls
    assert "attribution" in captured_bad.err or "国家统计局" in captured_bad.err
    assert not (bad_out / "corpus" / "t1" / "s1bad-gdp.md").exists()


def test_example_spec_targets_synthetic_chunks(tmp_path: Path):
    mod = _load_script()
    spec = json.loads((ROOT / "scripts" / "x1_draft_spec.example.json").read_text(encoding="utf-8"))
    loaded = mod._load_spec(ROOT / "scripts" / "x1_draft_spec.example.json")
    assert isinstance(loaded, dict)
    genres = {batch["genre"] for batch in spec["batches"]}
    assert genres == {f"S{i}" for i in range(1, 8)}
    raw_example = (ROOT / "scripts" / "x1_draft_spec.example.json").read_text(encoding="utf-8")
    assert "P2" not in raw_example
    assert "国家统计局" not in raw_example
    assert "stats.gov.cn" not in raw_example
    total = 0
    for batch in spec["batches"]:
        files = batch["n_docs"] * (2 if batch.get("pair") is True else 1)
        total += files * batch["chunks_per_doc"]
    assert total >= 520
    assert spec["pricing"]["input_cny_per_million"] is None
    assert spec["pricing"]["output_cny_per_million"] is None
    assert isinstance(spec["pricing"]["source"], str) and spec["pricing"]["source"].strip()
    assert spec["flag_pricing"]["input_cny_per_million"] is None
    assert spec["flag_pricing"]["output_cny_per_million"] is None
    assert isinstance(spec["flag_pricing"]["source"], str) and spec["flag_pricing"]["source"].strip()
    by_genre: dict[str, int] = {}
    gap_facts = [
        "数据出境安全评估结果有效期由令11的2年改为令16的3年；到期可在届满前60个工作日内申请延长3年，不再重新申报",
        "非关基运营者申报安全评估的个人信息门槛：令11为自上年1月1日起累计10万人；令16为自当年1月1日起累计100万人以上（不含敏感）或1万人以上敏感个人信息",
        "标准合同区间：令13为不满10万人；令16为10万人以上、不满100万人（不含敏感）或不满1万人敏感个人信息，并可走个人信息保护认证",
        "令16第五条新增豁免：当年累计不满10万人个人信息（不含敏感）免予申报、标准合同和认证；另有合同履行、跨境人力资源管理、紧急情况等场景",
        "2023公司法第四十七条：有限责任公司股东认缴出资须自成立之日起五年内缴足；2018法第二十六条无此期限",
        "2023公司法自2024年7月1日起施行，出资期限超过规定的存量公司应逐步调整（第二百六十六条）；2018法自2006年1月1日起施行",
        "未按期出资：2018法向已足额出资股东承担违约责任；2023法改为对公司损失承担赔偿责任，并新增董事会核查催缴、宽限期不少于六十日后失权、加速到期、未届期转让由受让人缴纳",
    ]
    seen_facts: list[str] = []
    gap_chunks = 0
    for batch in spec["batches"]:
        files = batch["n_docs"] * (2 if batch.get("pair") is True else 1)
        by_genre[batch["genre"]] = by_genre.get(batch["genre"], 0) + files * batch["chunks_per_doc"]
        assert mod._output_token_upper(batch) <= mod.MODEL_MAX_OUTPUT_TOKENS["qwen-flash"]
        assert 2 <= batch["chunks_per_doc"] <= 6
        if batch["genre"] in {"S1", "S2", "S3"}:
            assert batch.get("pair") is True
            assert "as_of" not in batch
        if batch["genre"] == "S6":
            assert batch["as_of"] == "T1"
            assert batch["must_include"]
            assert batch.get("pair") is not True
            blob = "\n".join(batch["must_include"])
            if batch["domain"] in {"D1", "D2"}:
                gap_chunks += files * batch["chunks_per_doc"]
                seen_facts.extend(batch["must_include"])
            else:
                assert batch["domain"] in {"D0", "D3"}
                assert "清洗" not in blob
                assert "不拆块" not in blob
                assert "200" not in blob
    assert by_genre["S1"] == 108
    assert by_genre["S2"] == 84
    assert by_genre["S3"] == 84
    assert 20 <= gap_chunks <= 24
    for fact in gap_facts:
        assert fact in seen_facts
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


def _manifest(out: Path) -> dict:
    return json.loads((out / ".x1-drafts-manifest.json").read_text(encoding="utf-8"))



def test_estimate_only_allows_null_decoding_and_prints_sources(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM("不应调用")
    cfg = _write_json(tmp_path / "config.json", _cfg(draft_temperature=None, draft_seed=None))
    code = _generate(
        mod,
        tmp_path,
        fake,
        cfg,
        tmp_path / "est-null-decoding",
        extra=["--estimate-only"],
    )
    printed = capsys.readouterr().out
    assert code == 0
    assert fake.calls == []
    assert "pricing_source=单测占位，不是脚本内置标价" in printed
    assert "flag_pricing_source=单测抽检占位，不是脚本内置标价" in printed
    assert "flag_cny=" in printed


def test_p2_and_s6_spec_rejected_before_model(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    fake = FakeLLM("不应调用")
    code = _generate(
        mod,
        tmp_path,
        fake,
        cfg,
        tmp_path / "no-p2",
        spec=_spec([_batch(genre="P2", topic="手写")]),
    )
    assert code != 0
    assert "P2 由人按国家统计局公告手写，不由模型生成" in capsys.readouterr().err
    assert fake.calls == []
    bare = _batch(genre="S6", topic="缺口")
    fake_s6 = FakeLLM("不应调用")
    code_s6 = _generate(mod, tmp_path, fake_s6, cfg, tmp_path / "no-s6", spec=_spec([bare]))
    assert code_s6 != 0
    assert fake_s6.calls == []


def test_decoding_mismatch_stops_before_model(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg(draft_temperature=0.7, draft_seed=7))
    out = tmp_path / "decode"
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    assert _generate(mod, tmp_path, fake, cfg, out) == 0
    assert len(fake.calls) == 1
    rec = _manifest(out)["batches"]["b1"]
    assert rec["draft_model"] == "qwen-flash"
    assert rec["draft_temperature"] == 0.7
    assert rec["draft_seed"] == 7
    assert len(rec["prompt_sha256"]) == 64
    blob = (out / ".x1-drafts-manifest.json").read_bytes()
    _write_json(cfg, _cfg(draft_temperature=0.2, draft_seed=99))
    again = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    code = _generate(mod, tmp_path, again, cfg, out)
    captured = capsys.readouterr()
    assert code == 1
    assert again.calls == []
    assert "解码参数与清单不一致" in captured.err
    assert "Traceback" not in captured.err
    assert (out / ".x1-drafts-manifest.json").read_bytes() == blob


def test_budget_precheck_refuses_before_call(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    code = _generate(mod, tmp_path, fake, cfg, tmp_path / "cap", max_cny="0")
    assert code != 0
    assert "max-cny" in capsys.readouterr().err
    assert fake.calls == []


def test_zero_usage_charges_upper_and_stops(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False), record_usage=False)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "zero-usage"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
    captured = capsys.readouterr()
    assert code == 1
    assert len(fake.calls) == 1
    assert "用量缺失或为 0" in captured.err
    assert "Traceback" not in captured.err
    prompt = mod._build_batch_prompt(batch)
    upper = mod._cost_cny(mod._input_token_upper(prompt), mod._output_token_upper(batch), 1, 2)
    manifest = _manifest(out)
    assert manifest["batches"]["b1"]["status"] == "failed"
    assert manifest["spent_cny"] == pytest.approx(upper)
    assert manifest["batches"]["b1"]["cost_cny"] == pytest.approx(upper)
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()


def test_length_finish_fails_batch(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    fake.finish_reason = "length"
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "length"
    code = _generate(mod, tmp_path, fake, cfg, out)
    captured = capsys.readouterr()
    assert code == 1
    assert "finish_reason=length" in captured.err
    assert "Traceback" not in captured.err
    manifest = _manifest(out)
    assert manifest["batches"]["b1"]["status"] == "failed"
    assert manifest["batches"]["b1"]["prompt_tokens"] == 1
    assert manifest["spent_cny"] < 0.01
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()


def test_model_exception_charges_estimate_without_traceback(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch()

    class _Boom(FakeLLM):
        def chat(self, *args, **kwargs):
            raise RuntimeError("模型调用失败")

    fake = _Boom("不会返回")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "boom"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.strip().splitlines() == ["错误: 批次 b1: 模型调用失败"]
    assert "Traceback" not in captured.out
    prompt = mod._build_batch_prompt(batch)
    upper = mod._cost_cny(mod._input_token_upper(prompt), mod._output_token_upper(batch), 1, 2)
    manifest = _manifest(out)
    assert manifest["batches"]["b1"]["status"] == "failed"
    assert manifest["spent_cny"] == pytest.approx(upper)


def test_spend_carries_across_resume(tmp_path: Path, capsys):
    mod = _load_script()
    first = _batch(batch_id="b1", topic="已花费")
    second = _batch(batch_id="b2", topic="续跑")
    spec = _spec([first])
    spec["pricing"]["input_cny_per_million"] = 1
    spec["pricing"]["output_cny_per_million"] = 1
    upper_in = mod._input_token_upper(mod._build_batch_prompt(first))
    upper_out = mod._output_token_upper(first)
    cap = mod._cost_cny(upper_in, upper_out, 1, 1)
    fake = QueueLLM(
        [json.dumps(_batch_payload(first, doc_id="b1-doc", qid="q1"), ensure_ascii=False)],
        prompt_each=upper_in - 1,
        completion_each=upper_out - 1,
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "carry"
    assert _generate(mod, tmp_path, fake, cfg, out, spec=spec, max_cny=repr(cap)) == 0
    spent = _manifest(out)["spent_cny"]
    assert spent == pytest.approx(cap)
    more = _spec([first, second])
    more["pricing"] = spec["pricing"]
    more["flag_pricing"] = spec["flag_pricing"]
    again = FakeLLM("不应调用")
    code = _generate(mod, tmp_path, again, cfg, out, spec=more, max_cny=repr(cap))
    assert code != 0
    assert again.calls == []
    assert "max-cny" in capsys.readouterr().err
    assert _manifest(out)["spent_cny"] == pytest.approx(spent)
    assert (out / "corpus" / "t1" / "b1-doc.md").is_file()


def test_corrupt_questions_exit_before_model(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "bad-questions"
    out.mkdir()
    marker = out / ".x1-drafts-manifest.json"
    marker.write_text("{}\n", encoding="utf-8")
    (out / "questions.json").write_text("{", encoding="utf-8")
    blob = marker.read_bytes()
    fake = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    code = _generate(mod, tmp_path, fake, cfg, out)
    assert code == 1
    assert "无法解析" in capsys.readouterr().err
    assert fake.calls == []
    assert marker.read_bytes() == blob

    shaped = tmp_path / "bad-shape"
    shaped.mkdir()
    (shaped / ".x1-drafts-manifest.json").write_text("{}\n", encoding="utf-8")
    (shaped / "questions.json").write_text("[]\n", encoding="utf-8")
    fake_shape = FakeLLM("不应调用")
    code_shape = _generate(mod, tmp_path, fake_shape, cfg, shaped)
    assert code_shape == 1
    assert fake_shape.calls == []


def test_crash_mid_commit_recovers_batch_one_and_two(tmp_path: Path, monkeypatch):
    mod = _load_script()
    real = mod._atomic_write_text
    gate = {"md": True}

    def _wrapped(path, text):
        if gate["md"] and Path(path).suffix == ".md":
            raise OSError("simulated crash")
        return real(path, text)

    monkeypatch.setattr(mod, "_atomic_write_text", _wrapped)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "crash1"
    payload = json.dumps(_draft_payload(), ensure_ascii=False)
    first = FakeLLM(payload)
    assert _generate(mod, tmp_path, first, cfg, out) == 1
    assert _manifest(out)["batches"]["b1"]["status"] == "committing"
    assert _manifest(out)["batches"]["b1"]["paths"] == ["corpus/t1/b1-draft.md"]
    assert (out / ".x1-drafts-manifest.json").is_file()
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()
    gate["md"] = False
    second = FakeLLM(payload)
    assert _generate(mod, tmp_path, second, cfg, out) == 0
    assert len(second.calls) == 1
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()
    assert _manifest(out)["batches"]["b1"]["status"] == "ok"

    batches = [_batch(batch_id="b1", topic="第一批"), _batch(batch_id="b2", topic="第二批")]
    payloads = [
        _batch_payload(batches[0], doc_id="b1-doc", qid="q1"),
        _batch_payload(batches[1], doc_id="b2-doc", qid="q2"),
    ]
    out2 = tmp_path / "crash2"

    def _wrapped_b2(path, text):
        name = Path(path).name
        if gate["md"] and name.startswith("b2-"):
            raise OSError("simulated crash")
        real(path, text)
        if name.startswith("b1-"):
            keep = out2 / "corpus" / "t1" / "keep.md"
            keep.parent.mkdir(parents=True, exist_ok=True)
            keep.write_text("keep", encoding="utf-8")

    monkeypatch.setattr(mod, "_atomic_write_text", _wrapped_b2)
    gate["md"] = True
    both = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    assert _generate(mod, tmp_path, both, cfg, out2, spec=_spec(batches)) == 1
    assert both.index == 2
    assert _manifest(out2)["batches"]["b1"]["status"] == "ok"
    assert _manifest(out2)["batches"]["b2"]["status"] == "committing"
    assert _manifest(out2)["batches"]["b2"]["paths"] == ["corpus/t1/b2-doc.md"]
    assert (out2 / "corpus" / "t1" / "keep.md").read_text(encoding="utf-8") == "keep"
    kept = (out2 / "corpus" / "t1" / "b1-doc.md").read_bytes()
    gate["md"] = False
    retry = QueueLLM([json.dumps(payloads[1], ensure_ascii=False)])
    assert _generate(mod, tmp_path, retry, cfg, out2, spec=_spec(batches)) == 0
    assert retry.index == 1
    assert (out2 / "corpus" / "t1" / "b1-doc.md").read_bytes() == kept
    assert (out2 / "corpus" / "t1" / "b2-doc.md").is_file()
    assert (out2 / "corpus" / "t1" / "keep.md").read_text(encoding="utf-8") == "keep"
    written_ids = [item["id"] for item in json.loads((out2 / "questions.json").read_text(encoding="utf-8"))["queries"]]
    assert written_ids == ["b1-q1", "b2-q2"]


def test_doc_id_blocks_license_and_collisions(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())

    def _run(payload, batch=None, out_name="case"):
        fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
        out = tmp_path / out_name
        spec = _spec() if batch is None else _spec([batch])
        code = _generate(mod, tmp_path, fake, cfg, out, spec=spec)
        err = capsys.readouterr().err
        return code, err, fake, out

    bad_id = _draft_payload(body=_doc_body(doc_id="draft-doc"))
    bad_id["documents"][0]["path"] = "corpus/t1/draft-doc.md"
    code, err, fake, out = _run(bad_id, out_name="bad-id")
    assert code != 0 and fake.calls and "b1-[a-z0-9-]+" in err
    assert not (out / "corpus" / "t1" / "draft-doc.md").exists()

    duplicated = _doc_body() + "## p1\n另一段合成正文。\n"
    code, err, fake, _out = _run(_draft_payload(body=duplicated), out_name="dup-block")
    assert code != 0 and "块 id 重复" in err and fake.calls

    non_pn = _doc_body().replace("## p1", "## note\n## p1", 1)
    code, err, fake, _out = _run(_draft_payload(body=non_pn), out_name="bad-heading")
    assert code != 0 and "块 id 必须是 pN" in err

    sub = _doc_body().replace("仅作草稿。", "仅作草稿。\n### 小节\n补充一句合成说明。", 1)
    code, err, fake, out = _run(_draft_payload(body=sub), out_name="subhead")
    assert code == 0, err
    assert "### 小节" in (out / "corpus" / "t1" / "b1-draft.md").read_text(encoding="utf-8")

    empty = _doc_body().replace("顾问备忘里写了渠道改口后的报价口径，仅作草稿。", "", 1)
    code, err, fake, _out = _run(_draft_payload(body=empty), out_name="empty-block")
    assert code != 0 and "块正文为空" in err

    code, err, fake, _out = _run(_draft_payload(body=_doc_body(license="cc-by")), out_name="license")
    assert code != 0 and "license 必须为 synthetic" in err

    nbs = _draft_payload(body=_doc_body().replace("仅作草稿。", "仅作草稿。详见 stats.gov.cn。", 1))
    code, err, fake, out = _run(nbs, out_name="nbs-body")
    assert code != 0 and fake.calls and "stats.gov.cn" in err
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()

    bureau = _draft_payload(body=_doc_body().replace("仅作草稿。", "仅作草稿。据统计局公告改过口径。", 1))
    code, err, fake, out = _run(bureau, out_name="bureau-only")
    assert code != 0 and fake.calls and "统计局" in err
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()

    limited = _batch(max_chars_per_chunk=5, n_questions=2)
    code, err, fake, _out = _run(_draft_payload(), limited, "limits")
    assert code != 0 and "max_chars_per_chunk" in err
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "5" in prompt
    assert "题目数量必须等于 2" in prompt


def test_doc_id_collision_in_run_out_and_public_corpus(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    first = _batch(batch_id="b", topic="第一份")
    second = _batch(batch_id="b-1", topic="同一 doc_id")
    first_payload = _batch_payload(first, doc_id="b-1-memo", qid="q1")
    second_body = _doc_body(doc_id="b-1-memo")
    question = dict(_draft_payload()["questions"]["queries"][0])
    question["id"] = "q2"
    second_payload = {
        "documents": [{"path": "corpus/t1/b-1-memo.md", "content": second_body}],
        "questions": {"queries": [question]},
    }
    fake = QueueLLM(
        [
            json.dumps(first_payload, ensure_ascii=False),
            json.dumps(second_payload, ensure_ascii=False),
        ]
    )
    out = tmp_path / "collide-run"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([first, second]))
    assert code != 0
    assert "已存在" in capsys.readouterr().err
    assert (out / "corpus" / "t1" / "b-1-memo.md").is_file()
    assert not (out / "corpus" / "t1" / "b-1-other.md").exists()
    assert fake.index == 2

    seeded = tmp_path / "collide-out"
    seeded_doc = seeded / "corpus" / "t1" / "b1-draft.md"
    seeded_doc.parent.mkdir(parents=True)
    seeded_doc.write_text(_doc_body(), encoding="utf-8")
    (seeded / ".x1-drafts-manifest.json").write_text("{}\n", encoding="utf-8")
    again = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    code_out = _generate(mod, tmp_path, again, cfg, seeded)
    assert code_out != 0
    assert "已存在" in capsys.readouterr().err
    assert len(again.calls) == 1

    reserved = _batch(batch_id="p1", as_of="T0", domain="D1", genre="S1", topic="保留前缀")
    reserved_fake = FakeLLM("不应调用")
    code_reserved = _generate(
        mod, tmp_path, reserved_fake, cfg, tmp_path / "reserved-p1", spec=_spec([reserved])
    )
    assert code_reserved != 0
    assert reserved_fake.calls == []
    assert "p1/p2" in capsys.readouterr().err
    assert mod._validate_batch(_batch(batch_id="p10"), 0) is None

    public = ROOT / "data" / "exp" / "x1" / "corpus" / "t1" / "p1-cac-o16.md"
    before = public.read_bytes()
    hit = _batch(batch_id="b1", as_of="T0", domain="D1", genre="S1", topic="另一快照撞公开 doc_id")
    body = _doc_body(doc_id="p1-cac-o16", as_of="T0", domain="D1", genre="S1")
    payload = _batch_payload(hit, doc_id="p1-cac-o16", qid="q-hit", body=body)
    payload["documents"][0]["path"] = "corpus/t0/p1-cac-o16.md"
    hit_fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    hit_out = tmp_path / "collide-public"
    code_hit = _generate(mod, tmp_path, hit_fake, cfg, hit_out, spec=_spec([hit]))
    assert code_hit != 0
    assert "已存在于公开语料" in capsys.readouterr().err
    assert len(hit_fake.calls) == 1
    assert public.read_bytes() == before
    assert not (hit_out / "corpus" / "t0" / "p1-cac-o16.md").exists()


def test_pair_writes_t0_and_t1(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch(batch_id="s1pair", n_docs=1, chunks_per_doc=2, topic="配对备忘")
    del batch["as_of"]
    batch["pair"] = True
    t0 = _doc_body(doc_id="s1pair-memo", as_of="T0")
    t1 = _doc_body(doc_id="s1pair-memo", as_of="T1").replace("仅作草稿。", "T1 已改写该事实。", 1)
    payload = {
        "documents": [
            {"path": "corpus/t0/s1pair-memo.md", "content": t0},
            {"path": "corpus/t1/s1pair-memo.md", "content": t1},
        ],
        "questions": _draft_payload()["questions"],
    }
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "pair"
    assert _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch])) == 0
    assert len(fake.calls) == 1
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "pair=true" in prompt
    assert (out / "corpus" / "t0" / "s1pair-memo.md").is_file()
    assert (out / "corpus" / "t1" / "s1pair-memo.md").is_file()
    same = {
        "documents": [
            {"path": "corpus/t0/s1pair-memo.md", "content": t0},
            {"path": "corpus/t1/s1pair-memo.md", "content": _doc_body(doc_id="s1pair-memo", as_of="T1")},
        ],
        "questions": _draft_payload()["questions"],
    }
    same_fake = FakeLLM(json.dumps(same, ensure_ascii=False))
    code = _generate(mod, tmp_path, same_fake, cfg, tmp_path / "pair-same", spec=_spec([batch]))
    assert code != 0
    assert "T1 必须改写已陈述事实" in capsys.readouterr().err


def test_generate_passes_max_tokens_and_thinking_off(tmp_path: Path):
    mod = _load_script()
    inner = _RecordingInner(json.dumps(_draft_payload(), ensure_ascii=False))
    llm = LLMClient(api_key="test-key", base_url="http://127.0.0.1:9")
    llm.client = inner
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "wrapped"
    assert _generate(mod, tmp_path, llm, cfg, out) == 0
    kw = inner.kwargs_list[0]
    assert kw.get("extra_body") == {"enable_thinking": False}
    assert kw["max_tokens"] == mod._output_token_upper(_batch())
    assert inner.max_retries == 0


def test_flag_fail_closed_budget_usage_and_exception(tmp_path: Path, capsys):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    spec_path = _write_json(
        tmp_path / "flag-pricing.json",
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )

    def _flag(fake, sidecar: Path, max_cny: str = "100"):
        return mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(sidecar),
                "--spec",
                str(spec_path),
                "--max-cny",
                max_cny,
            ],
            llm_client=fake,
        )

    refused = FakeLLM("不应调用")
    assert _flag(refused, tmp_path / "flag-cap.json", "0") != 0
    assert refused.calls == []
    assert "max-cny" in capsys.readouterr().err

    zero = FakeLLM(
        json.dumps({"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"}),
        record_usage=False,
    )
    zero_path = tmp_path / "flag-zero.json"
    assert _flag(zero, zero_path) == 1
    assert "用量缺失或为 0" in capsys.readouterr().err
    zero_side = json.loads(zero_path.read_text(encoding="utf-8"))
    assert zero_side["status"] == "failed"
    assert zero_side["spent_cny"] > 0

    class _Boom(FakeLLM):
        def chat(self, *args, **kwargs):
            raise RuntimeError("抽检失败")

    truncated = FakeLLM(
        json.dumps({"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"}),
    )
    truncated.finish_reason = "length"
    truncated_path = tmp_path / "flag-length.json"
    assert _flag(truncated, truncated_path) == 1
    assert "finish_reason=length" in capsys.readouterr().err
    truncated_side = json.loads(truncated_path.read_text(encoding="utf-8"))
    assert truncated_side["status"] == "failed"
    assert truncated_side["spent_cny"] < 0.01

    boom_path = tmp_path / "flag-boom.json"
    assert _flag(_Boom("x"), boom_path) == 1
    captured = capsys.readouterr()
    assert captured.err.strip().splitlines()[-1] == "错误: 抽检调用失败: 抽检失败"
    assert "Traceback" not in captured.err
    assert json.loads(boom_path.read_text(encoding="utf-8"))["status"] == "failed"


def test_output_upper_over_model_limit_refuses_spec(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch(n_docs=4, chunks_per_doc=3, max_chars_per_chunk=800, n_questions=8, pair=True)
    del batch["as_of"]
    fake = FakeLLM("不应调用")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    code = _generate(mod, tmp_path, fake, cfg, tmp_path / "too-wide", spec=_spec([batch]), extra=["--estimate-only"])
    assert code != 0
    assert "请拆分" in capsys.readouterr().err
    assert fake.calls == []


def test_estimate_only_reports_budget(tmp_path: Path, capsys):
    mod = _load_script()
    fake = FakeLLM("不应调用")
    cfg = _write_json(tmp_path / "config.json", _cfg(draft_temperature=None, draft_seed=None))
    code = _generate(
        mod,
        tmp_path,
        fake,
        cfg,
        tmp_path / "est-over",
        extra=["--estimate-only"],
        max_cny="0",
    )
    printed = capsys.readouterr().out
    assert code != 0
    assert fake.calls == []
    assert "budget=over" in printed
    assert "total_cny=" in printed
    assert "max_batch_output_tokens=" in printed


def test_usage_over_upper_stops(tmp_path: Path, capsys):
    mod = _load_script()

    class _Huge(FakeLLM):
        def chat(self, *args, **kwargs):
            super().chat(*args, **kwargs)
            self.token_usage.add(10_000_000, 10_000_000)

    fake = _Huge(json.dumps(_draft_payload(), ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "over-usage"
    code = _generate(mod, tmp_path, fake, cfg, out)
    assert code == 1
    assert "usage_over_upper" in capsys.readouterr().err
    manifest = _manifest(out)
    assert manifest["stop_reason"] == "usage_over_upper"
    assert manifest["batches"]["b1"]["status"] == "failed"
    assert manifest["batches"]["b1"]["error"] == "usage_over_upper"
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()


def test_crash_after_questions_json_recovers_ids(tmp_path: Path, monkeypatch):
    mod = _load_script()
    real = mod._atomic_write_text
    gate = {"boom": True}

    def _wrapped(path, text):
        real(path, text)
        if gate["boom"] and Path(path).name == "questions.json" and "b2-q1" in text:
            raise BaseException("questions written")

    monkeypatch.setattr(mod, "_atomic_write_text", _wrapped)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    batches = [_batch(batch_id="b1", topic="第一批"), _batch(batch_id="b2", topic="第二批")]
    payloads = [
        _batch_payload(batches[0], doc_id="b1-doc", qid="b1-q1"),
        _batch_payload(batches[1], doc_id="b2-doc", qid="b2-q1"),
    ]
    out = tmp_path / "crash-questions"
    both = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    with pytest.raises(BaseException, match="questions written"):
        _generate(mod, tmp_path, both, cfg, out, spec=_spec(batches))
    assert _manifest(out)["batches"]["b1"]["status"] == "ok"
    assert _manifest(out)["batches"]["b2"]["status"] == "committing"
    assert _manifest(out)["batches"]["b2"]["question_ids"] == ["b2-q1"]
    written = [item["id"] for item in json.loads((out / "questions.json").read_text(encoding="utf-8"))["queries"]]
    assert written.count("b1-q1") == 1
    assert written.count("b2-q1") == 1
    gate["boom"] = False
    retry = QueueLLM([json.dumps(payloads[1], ensure_ascii=False)])
    assert _generate(mod, tmp_path, retry, cfg, out, spec=_spec(batches)) == 0
    again = [item["id"] for item in json.loads((out / "questions.json").read_text(encoding="utf-8"))["queries"]]
    assert again.count("b1-q1") == 1
    assert again.count("b2-q1") == 1
    assert _manifest(out)["batches"]["b1"]["status"] == "ok"
    assert _manifest(out)["batches"]["b2"]["status"] == "ok"


def test_discard_refuses_non_doc_paths(tmp_path: Path):
    mod = _load_script()
    out = tmp_path / "out"
    raw = out / "raw" / "b1.txt"
    raw.parent.mkdir(parents=True)
    raw.write_text("keep", encoding="utf-8")
    questions = out / "questions.json"
    questions.write_text("{}\n", encoding="utf-8")
    manifest = out / ".x1-drafts-manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    assert mod._discard_committing(out, {"paths": ["raw/b1.txt"]}, set())
    assert raw.read_text(encoding="utf-8") == "keep"
    assert mod._discard_committing(out, {"paths": ["questions.json"]}, set())
    assert questions.is_file()
    assert mod._discard_committing(out, {"paths": [".x1-drafts-manifest.json"]}, set())
    assert manifest.is_file()


def test_flag_refuses_when_output_upper_exceeds_model_limit(tmp_path: Path, capsys):
    mod = _load_script()
    questions = {"queries": [{"id": f"q{i}", "query": "草稿"} for i in range(257)]}
    qpath = _write_json(tmp_path / "many-questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    fake = FakeLLM("不应调用")
    code = mod.main(
        [
            "flag",
            "--config",
            str(cfg),
            "--in",
            str(qpath),
            "--sidecar",
            str(tmp_path / "too-many.json"),
            *_flag_extra(tmp_path, "flag-too-many.json"),
        ],
        llm_client=fake,
    )
    assert code != 0
    assert fake.calls == []
    assert "请减少题目" in capsys.readouterr().err
    assert not (tmp_path / "too-many.json").exists()


def test_flag_spend_cumulative_per_input_dir(tmp_path: Path, capsys):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    spec_path = _write_json(
        tmp_path / "flag-ledger-spec.json",
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )
    note = json.dumps({"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"}, ensure_ascii=False)

    def _flag(fake, sidecar: Path, max_cny: str):
        return mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(sidecar),
                "--spec",
                str(spec_path),
                "--max-cny",
                max_cny,
            ],
            llm_client=fake,
        )

    first = FakeLLM(note)
    second = FakeLLM(note)
    assert _flag(first, tmp_path / "side-a.json", "100") == 0
    assert _flag(second, tmp_path / "side-b.json", "100") == 0
    side_a = json.loads((tmp_path / "side-a.json").read_text(encoding="utf-8"))
    side_b = json.loads((tmp_path / "side-b.json").read_text(encoding="utf-8"))
    assert side_b["spent_cny"] > side_a["spent_cny"]
    ledger = json.loads((tmp_path / ".x1-flag-spend.json").read_text(encoding="utf-8"))
    assert ledger["spent_cny"] == pytest.approx(side_b["spent_cny"])
    refused = FakeLLM("不应调用")
    code = _flag(refused, tmp_path / "side-c.json", str(ledger["spent_cny"]))
    assert code != 0
    assert refused.calls == []
    assert "max-cny" in capsys.readouterr().err


def _chat_completion(content: str, *, prompt_tokens: int = 4, completion_tokens: int = 6) -> dict:
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": "qwen-flash",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def test_real_client_pins_first_request_and_does_not_retry_500(tmp_path: Path, monkeypatch, capsys):
    import httpx
    import openai
    import freshlatch.llm as llm_mod

    mod = _load_script()
    bodies: list[dict] = []

    def ok_handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        bodies.append(body)
        if body.get("model") == "qwen-plus":
            content = json.dumps(
                {"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"},
                ensure_ascii=False,
            )
        else:
            content = json.dumps(_draft_payload(), ensure_ascii=False)
        return httpx.Response(200, json=_chat_completion(content))

    def factory(**kw):
        return openai.OpenAI(http_client=httpx.Client(transport=httpx.MockTransport(ok_handler)), **kw)

    monkeypatch.setattr(llm_mod, "OpenAI", factory)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "pinned"
    llm = LLMClient(api_key="test", base_url="http://127.0.0.1:9")
    assert not hasattr(llm, "_client") or llm._client is None
    assert _generate(mod, tmp_path, llm, cfg, out) == 0
    assert bodies
    first = bodies[0]
    assert first["max_tokens"] == mod._output_token_upper(_batch())
    assert first["enable_thinking"] is False
    qpath = out / "questions.json"
    flag_llm = LLMClient(api_key="test", base_url="http://127.0.0.1:9")
    code = mod.main(
        [
            "flag",
            "--config",
            str(cfg),
            "--in",
            str(qpath),
            "--sidecar",
            str(tmp_path / "pinned-flag.json"),
            *_flag_extra(tmp_path, "pinned-flag-spec.json"),
        ],
        llm_client=flag_llm,
    )
    assert code == 0
    flag_body = bodies[-1]
    assert flag_body["model"] == "qwen-plus"
    assert isinstance(flag_body["max_tokens"], int) and flag_body["max_tokens"] > 0
    assert flag_body["enable_thinking"] is False

    attempts = {"n": 0}

    def err_handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(500, json={"error": {"message": "boom", "type": "server_error"}})

    def err_factory(**kw):
        return openai.OpenAI(http_client=httpx.Client(transport=httpx.MockTransport(err_handler)), **kw)

    monkeypatch.setattr(llm_mod, "OpenAI", err_factory)
    boom = LLMClient(api_key="test", base_url="http://127.0.0.1:9")
    code_boom = _generate(mod, tmp_path, boom, cfg, tmp_path / "retry-once")
    captured = capsys.readouterr()
    assert code_boom == 1
    assert attempts["n"] == 1
    assert "Traceback" not in captured.err


def _s1_model_payload(*, snapshot_as_of: bool, gold: bool = False, yaml_and_object: bool = False) -> dict:
    """由真实 qwen-flash 回复裁出来的夹具。金标已去掉，as_of 只在 snapshot_as_of 时改成 T0/T1。"""
    bodies = {
        "a": (
            "## p1\n根据最新战略评估，本季度核心业务增长预期维持在年化12%。市场反馈显示，客户对现有产品线的满意度持续上升。\n\n"
            "## p2\n外部环境分析表明，主要竞争者近期未有重大技术突破。建议维持当前资源投入策略。\n\n"
            "## p3\n财务模型预测显示，若保持现有运营效率，下季度净利润率将稳定。风险控制机制运行良好。\n"
        ),
        "a1": (
            "## p1\n最新战略评估显示，核心业务增长预期已下调至年化7%。客户满意度调查揭示服务响应延迟问题加剧。\n\n"
            "## p2\n外部环境变化显著，主要竞争者已完成关键技术迭代。原判断窗口期已关闭。\n\n"
            "## p3\n财务模型更新后显示，因运营效率下降，下季度净利润率可能下降。内部审计发现流程违规事件。\n"
        ),
        "b": (
            "## p1\n本季度战略重点仍为巩固现有客户关系。客户留存率数据显示，高价值客户续约率保持在高位。\n\n"
            "## p2\n供应链稳定性评估认为，关键原材料供应充足，无短期中断风险。\n\n"
            "## p3\n人力资源规划显示，技术岗位空缺率高于行业平均。招聘渠道优化方案已在试点阶段。\n"
        ),
        "b1": (
            "## p1\n客户关系维护面临挑战，高价值客户续约率已下滑，部分大客户提出终止合作意向。\n\n"
            "## p2\n供应链出现严重波动，关键原材料采购周期延长，区域配送中心因物流中断暂停运营。\n\n"
            "## p3\n技术岗位空缺率远超行业水平。原有招聘渠道失效，人才短缺已影响项目交付进度。\n"
        ),
    }
    specs = [
        ("corpus/t0/s1-d0-01-memo-a.md", "s1-d0-01-memo-a", "T0", "已签发顾问备忘：两周后待复验的战略判断（T0）", "a"),
        ("corpus/t1/s1-d0-01-memo-a.md", "s1-d0-01-memo-a", "T1", "已签发顾问备忘：两周后待复验的战略判断（T1）", "a1"),
        ("corpus/t0/s1-d0-01-memo-b.md", "s1-d0-01-memo-b", "T0", "已签发顾问备忘：两周后待复验的战略判断（T0）-B", "b"),
        ("corpus/t1/s1-d0-01-memo-b.md", "s1-d0-01-memo-b", "T1", "已签发顾问备忘：两周后待复验的战略判断（T1）-B", "b1"),
    ]
    documents = []
    for path, doc_id, snap, title, key in specs:
        frontmatter = {
            "doc_id": doc_id,
            "as_of": snap if snapshot_as_of else "2024-06-15",
            "source_type": "private",
            "title": title,
            "provenance": "synthetic",
            "license": "synthetic",
            "domain": "D0",
            "genre": "S1",
        }
        if gold:
            frontmatter["relevant"] = ["secret-gold-anchor"]
            frontmatter["answer_points"] = ["secret-gold-point"]
            frontmatter["distractors"] = ["secret-gold-trap"]
            frontmatter["qtype"] = "secret-gold-type"
            frontmatter["relevant_ids"] = ["secret-gold-nested"]
        content = bodies[key]
        if yaml_and_object:
            content = "---\ndoc_id: s1-d0-01-memo-a\nas_of: T0\n---\n" + content
        documents.append({"path": path, "content": content, "frontmatter": frontmatter})
    questions = [
        {"id": "q1", "query": "T0 文档里核心业务增长预期后来有没有被改写？", "category": "fact_recall", "eval_intent": "verify_factual_consistency", "as_of": "T1"},
        {"id": "q2", "query": "T1 文档里研发进度相对 T0 有什么变化？", "category": "comparison", "eval_intent": "assess_revised_assessment", "as_of": "T1"},
        {"id": "q3", "query": "客户留存率在两份备忘里是否对不上？", "category": "contradiction_detection", "eval_intent": "detect_inconsistencies", "as_of": "T0"},
        {"id": "q4", "query": "供应链状况在两份备忘里是否一致？", "category": "alignment_check", "eval_intent": "evaluate_consistency_across_versions", "as_of": "T0"},
    ]
    return {"documents": documents, "questions": {"queries": questions}}


def _s1_pair_batch() -> dict:
    return {
        "batch_id": "s1-d0-01",
        "genre": "S1",
        "domain": "D0",
        "n_docs": 2,
        "chunks_per_doc": 3,
        "topic": "已签发顾问备忘：两周后待复验的战略判断",
        "pair": True,
    }


def test_frontmatter_object_with_snapshot_as_of_validates(tmp_path: Path):
    mod = _load_script()
    payload = _s1_model_payload(snapshot_as_of=True, gold=True)
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "folded"
    assert _generate(mod, tmp_path, fake, cfg, out, spec=_spec([_s1_pair_batch()])) == 0
    assert len(fake.calls) == 1
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "不要另给 frontmatter 字段" in prompt
    assert "as_of: T1" in prompt
    assert '"path":"corpus/t1/s1-d0-01-memo.md"' in prompt
    assert "题目 id 必须形如 s1-d0-01-q1" in prompt
    t0 = (out / "corpus" / "t0" / "s1-d0-01-memo-a.md").read_text(encoding="utf-8")
    t1 = (out / "corpus" / "t1" / "s1-d0-01-memo-a.md").read_text(encoding="utf-8")
    assert t0.startswith("---\n")
    assert "as_of: T0\n" in t0
    assert "as_of: T1\n" in t1
    blob = "\n".join(path.read_text(encoding="utf-8") for path in (out / "corpus").rglob("*.md"))
    for banned in ("secret-gold", "qtype:", "relevant:", "answer_points", "distractors"):
        assert banned not in blob
    questions = (out / "questions.json").read_text(encoding="utf-8")
    assert "secret-gold" not in questions


def test_dated_as_of_still_rejected(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _s1_model_payload(snapshot_as_of=False)
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "dated"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([_s1_pair_batch()]))
    err = capsys.readouterr().err
    assert code != 0
    assert len(fake.calls) == 1
    assert "as_of 与目录或批次不一致" in err
    assert "frontmatter 缺键" not in err
    assert not (out / "corpus" / "t0" / "s1-d0-01-memo-a.md").exists()
    assert _manifest(out)["batches"]["s1-d0-01"]["status"] == "failed"

    s2_batch = {
        "batch_id": "s2-d0-03",
        "genre": "S2",
        "domain": "D0",
        "n_docs": 2,
        "chunks_per_doc": 3,
        "topic": "访谈与渠道纪要",
        "pair": True,
    }
    s2_body = (
        "## p1\n公司A在2023年第三季度财报中披露，其核心业务收入同比增长。管理层表示这一趋势还将持续。\n\n"
        "## p2\n根据内部渠道纪要，公司A的海外分支机构在欧洲市场实现突破。\n\n"
        "## p3\n在近期的投资者访谈中，首席执行官明确指出公司正加速推进数字化转型。\n"
    )
    s2_docs = []
    for folder, doc_id in (
        ("t0", "s2-d0-03-0a1b2c3d4e5f"),
        ("t1", "s2-d0-03-0a1b2c3d4e5f"),
        ("t0", "s2-d0-03-1b2c3d4e5f6a"),
        ("t1", "s2-d0-03-1b2c3d4e5f6a"),
    ):
        s2_docs.append(
            {
                "path": f"corpus/{folder}/{doc_id.split('-', 3)[-1]}.md",
                "content": s2_body,
                "frontmatter": {
                    "doc_id": doc_id,
                    "as_of": "2024-04-01",
                    "source_type": "private",
                    "title": "公司A业绩与战略方向",
                    "provenance": "synthetic",
                    "license": "synthetic",
                    "domain": "D0",
                    "genre": "S2",
                },
            }
        )
    s2_payload = {
        "documents": s2_docs,
        "questions": {
            "queries": [
                {"id": "sq1", "query": "公司A核心业务收入后来怎么说？", "category": "factoid", "eval_intent": "direct", "as_of": "2024-04-01"}
            ]
        },
    }
    s2_fake = FakeLLM(json.dumps(s2_payload, ensure_ascii=False))
    s2_out = tmp_path / "dated-s2"
    code_s2 = _generate(mod, tmp_path, s2_fake, cfg, s2_out, spec=_spec([s2_batch]))
    assert code_s2 != 0
    assert "as_of 与目录或批次不一致" in capsys.readouterr().err
    assert s2_fake.calls
    assert not (s2_out / "corpus" / "t0").exists() or not any((s2_out / "corpus").rglob("*.md"))


def test_frontmatter_object_and_yaml_block_rejected(tmp_path: Path, capsys):
    mod = _load_script()
    payload = _s1_model_payload(snapshot_as_of=True, yaml_and_object=True)
    fake = FakeLLM(json.dumps(payload, ensure_ascii=False))
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "both"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([_s1_pair_batch()]))
    err = capsys.readouterr().err
    assert code != 0
    assert len(fake.calls) == 1
    assert "不能同时给出 frontmatter 对象和 content 里的 YAML 块" in err
    assert not (out / "corpus" / "t0" / "s1-d0-01-memo-a.md").exists()


def test_three_consecutive_validation_failures_stop(tmp_path: Path, capsys):
    mod = _load_script()
    batches = [_batch(batch_id=f"b{i}", topic=f"第{i}批") for i in range(1, 5)]
    payloads = []
    for batch in batches:
        payloads.append(
            {
                "documents": [
                    {
                        "path": f"corpus/t1/{batch['batch_id']}-draft.md",
                        "content": "## p1\n合成正文没有 YAML。\n## p2\n另一段。\n",
                        "frontmatter": {
                            "doc_id": f"{batch['batch_id']}-draft",
                            "as_of": "2024-06-15",
                            "source_type": "private",
                            "title": "日期快照",
                            "provenance": "synthetic",
                            "license": "synthetic",
                            "domain": "D0",
                            "genre": "S1",
                        },
                    }
                ],
                "questions": {"queries": [{"id": f"{batch['batch_id']}-q", "query": "问", "category": "c", "eval_intent": "e", "as_of": "T1"}]},
            }
        )
    fake = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "streak"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec(batches))
    err = capsys.readouterr().err
    assert code == 1
    assert fake.index == 3
    assert err.count("错误: 连续 3 批校验失败，停止") == 1
    assert "Traceback" not in err
    manifest = _manifest(out)
    assert manifest["stop_reason"] == "consecutive_validation"
    assert manifest["batches"]["b1"]["status"] == "failed"
    assert manifest["batches"]["b2"]["status"] == "failed"
    assert manifest["batches"]["b3"]["status"] == "failed"
    assert "b4" not in manifest["batches"]


def test_failed_batches_retry_when_prompt_changes(tmp_path: Path, monkeypatch, capsys):
    mod = _load_script()
    batch = _s1_pair_batch()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "scratch"
    bad = FakeLLM(json.dumps(_s1_model_payload(snapshot_as_of=False), ensure_ascii=False))
    assert _generate(mod, tmp_path, bad, cfg, out, spec=_spec([batch])) == 1
    failed = _manifest(out)["batches"]["s1-d0-01"]
    assert failed["status"] == "failed"
    old_sha = failed["prompt_sha256"]
    real = mod._build_batch_prompt

    def _changed(item):
        return real(item) + "\n提示已更新。"

    monkeypatch.setattr(mod, "_build_batch_prompt", _changed)
    good = FakeLLM(json.dumps(_s1_model_payload(snapshot_as_of=True), ensure_ascii=False))
    code = _generate(mod, tmp_path, good, cfg, out, spec=_spec([batch]))
    err = capsys.readouterr().err
    assert "解码参数与清单不一致" not in err
    assert code == 0
    assert len(good.calls) == 1
    rec = _manifest(out)["batches"]["s1-d0-01"]
    assert rec["status"] == "ok"
    assert rec["prompt_sha256"] != old_sha
    assert (out / "corpus" / "t0" / "s1-d0-01-memo-a.md").is_file()


def test_yaml_scalar_flattens_separators_and_rejects_duplicate_keys():
    mod = _load_script()
    sample = "甲\u2028乙\x85丙\v丁\f戊\x1c己\x1d庚\x1e辛"
    flattened = mod._yaml_scalar(sample)
    assert flattened == "甲 乙 丙 丁 戊 己 庚 辛"
    rendered = mod._render_yaml_frontmatter({"title": "甲\u2028poison: 注入"})
    assert "\npoison:" not in rendered
    assert "甲 poison: 注入" in rendered
    with pytest.raises(mod.DraftShapeError, match="键重复"):
        mod._render_yaml_frontmatter({"as_of": "T0", " as_of ": "T1"})
    duplicated = _doc_body().replace("as_of: T1\n", "as_of: T1\n as_of : T0\n", 1)
    err = mod._validate_markdown(duplicated, _batch(), as_of="T1")
    assert isinstance(err, str) and "键重复" in err and "as_of" in err


def test_unknown_frontmatter_key_and_dated_question_as_of_fail(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    poisoned = _draft_payload(body=_doc_body(poison="injected"))
    fake = FakeLLM(json.dumps(poisoned, ensure_ascii=False))
    out = tmp_path / "unknown-key"
    code = _generate(mod, tmp_path, fake, cfg, out)
    err = capsys.readouterr().err
    assert code == 1
    assert "未知键" in err and "poison" in err
    assert _manifest(out)["batches"]["b1"]["status"] == "failed"
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()

    dated = _draft_payload(questions_over={"as_of": "2024-05-20"})
    dated_fake = FakeLLM(json.dumps(dated, ensure_ascii=False))
    dated_out = tmp_path / "dated-question"
    code_dated = _generate(mod, tmp_path, dated_fake, cfg, dated_out)
    err_dated = capsys.readouterr().err
    assert code_dated == 1
    assert "题目 as_of 必须是 T0 或 T1" in err_dated
    assert _manifest(dated_out)["batches"]["b1"]["status"] == "failed"
    assert _manifest(dated_out)["batches"]["b1"]["status"] != "committing"
    assert not (dated_out / "corpus" / "t1" / "b1-draft.md").exists()


def test_interrupted_call_keeps_precharge_and_resume_replaces_it(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "inflight"

    class _Interrupt(FakeLLM):
        def chat(self, *args, **kwargs):
            raise KeyboardInterrupt

    code = _generate(mod, tmp_path, _Interrupt("不会返回"), cfg, out, spec=_spec([batch]))
    assert code == 130
    assert "调用被中断" in capsys.readouterr().err
    prompt = mod._build_batch_prompt(batch)
    upper = mod._cost_cny(mod._input_token_upper(prompt), mod._output_token_upper(batch), 1, 2)
    manifest = _manifest(out)
    assert manifest["batches"]["b1"]["status"] == "inflight"
    assert manifest["spent_cny"] == pytest.approx(upper)
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()

    again = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    assert _generate(mod, tmp_path, again, cfg, out, spec=_spec([batch])) == 0
    assert len(again.calls) == 1
    resumed = _manifest(out)
    assert resumed["batches"]["b1"]["status"] == "ok"
    assert resumed["spent_cny"] == pytest.approx(upper + mod._cost_cny(1, 1, 1, 2))
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()

    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "flag-questions.json", questions)
    spec_path = _write_json(
        tmp_path / "flag-inflight-spec.json",
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )

    def _flag(fake, sidecar: Path):
        return mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(sidecar),
                "--spec",
                str(spec_path),
                "--max-cny",
                "100",
            ],
            llm_client=fake,
        )

    flag_side = tmp_path / "flag-inflight.json"
    assert _flag(_Interrupt("不会返回"), flag_side) == 130
    ledger = json.loads((tmp_path / ".x1-flag-spend.json").read_text(encoding="utf-8"))
    side = json.loads(flag_side.read_text(encoding="utf-8"))
    assert side["status"] == "inflight"
    assert ledger["inflight"] is True
    slim = [{"id": questions["queries"][0]["id"], "query": questions["queries"][0]["query"]}]
    flag_prompt = mod._flag_prompt(slim)
    flag_upper = mod._cost_cny(
        mod._input_token_upper(flag_prompt),
        mod._flag_output_upper(1),
        1,
        2,
    )
    assert ledger["spent_cny"] == pytest.approx(flag_upper)
    note = json.dumps(
        {"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"},
        ensure_ascii=False,
    )
    assert _flag(FakeLLM(note), tmp_path / "flag-inflight-ok.json") == 0
    settled = json.loads((tmp_path / ".x1-flag-spend.json").read_text(encoding="utf-8"))
    assert "inflight" not in settled
    assert settled["spent_cny"] == pytest.approx(flag_upper + mod._cost_cny(1, 1, 1, 2))


def test_streak_stop_still_runs_checker(tmp_path: Path, capsys, monkeypatch):
    mod = _load_script()
    good = _batch(batch_id="ok1", topic="先成功一批")
    bad_batches = [_batch(batch_id=f"bad{i}", topic=f"失败{i}") for i in range(1, 5)]
    good_payload = _batch_payload(good, doc_id="ok1-memo", qid="q1")
    bad_payloads = []
    for batch in bad_batches:
        bad_payloads.append(
            {
                "documents": [
                    {
                        "path": f"corpus/t1/{batch['batch_id']}-draft.md",
                        "content": "## p1\n合成正文没有 YAML。\n## p2\n另一段。\n",
                        "frontmatter": {
                            "doc_id": f"{batch['batch_id']}-draft",
                            "as_of": "2024-06-15",
                            "source_type": "private",
                            "title": "日期快照",
                            "provenance": "synthetic",
                            "license": "synthetic",
                            "domain": "D0",
                            "genre": "S1",
                        },
                    }
                ],
                "questions": {
                    "queries": [
                        {
                            "id": "q1",
                            "query": "问",
                            "category": "c",
                            "eval_intent": "e",
                            "as_of": "T1",
                        }
                    ]
                },
            }
        )
    calls = {"n": 0}

    class _Result:
        exit_code = 2

        def format_report(self):
            return "report-only\n"

    def _fake_check(*_args, **_kwargs):
        calls["n"] += 1
        return _Result()

    monkeypatch.setattr(mod, "check_x1", _fake_check)
    fake = QueueLLM(
        [json.dumps(item, ensure_ascii=False) for item in [good_payload, *bad_payloads]]
    )
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "streak-check"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([good, *bad_batches]))
    err = capsys.readouterr().err
    assert code == 1
    assert fake.index == 4
    assert err.count("错误: 连续 3 批校验失败，停止") == 1
    assert calls["n"] == 1
    manifest = _manifest(out)
    assert manifest["stop_reason"] == "consecutive_validation"
    assert manifest["checker_exit"] == 2
    assert manifest["batches"]["ok1"]["status"] == "ok"
    assert "bad4" not in manifest["batches"]
    assert (out / "corpus" / "t1" / "ok1-memo.md").is_file()


def _folded_doc(path: str, doc_id: str, as_of: str, genre: str, domain: str, title: str, body: str) -> dict:
    return {
        "path": path,
        "content": body,
        "frontmatter": {
            "doc_id": doc_id,
            "as_of": as_of,
            "source_type": "private",
            "title": title,
            "provenance": "synthetic",
            "license": "synthetic",
            "domain": domain,
            "genre": genre,
        },
    }


def _plain_question(qid: str, as_of: str, text: str) -> dict:
    return {
        "id": qid,
        "query": text,
        "category": "fact_recall",
        "eval_intent": "verify_factual_consistency",
        "as_of": as_of,
    }


def test_replay_q1_and_colliding_filenames_commits_valid_batches(tmp_path: Path, capsys):
    """连续回放：q1 题号、strategy_review_01.md 和裸 uuid。脚本改写路径后，合法批次都落盘。"""
    mod = _load_script()
    kept = (
        "## p1\n根据最新战略评估，本季度核心业务增长预期维持在年化12%。客户对现有产品线的满意度持续上升。\n\n"
        "## p2\n外部环境分析表明，主要竞争者近期未有重大技术突破。建议维持当前资源投入策略。\n"
    )
    revised = (
        "## p1\n最新战略评估显示，核心业务增长预期已下调至年化7%。客户满意度调查揭示服务响应延迟问题加剧。\n\n"
        "## p2\n外部环境变化显著，主要竞争者已完成关键技术迭代。原判断窗口期已关闭。\n"
    )
    batches = [
        _batch(batch_id="s1-d0-04", as_of="T0", topic="战略复盘备忘"),
        _batch(batch_id="s1-d0-05", as_of="T0", topic="另一份战略复盘"),
        {
            "batch_id": "s2-d0-01",
            "genre": "S2",
            "domain": "D0",
            "n_docs": 1,
            "chunks_per_doc": 2,
            "topic": "访谈与渠道纪要",
            "pair": True,
        },
        _batch(batch_id="s1-d0", as_of="T0", topic="重复写已落盘的文件"),
    ]
    payloads = [
        {
            "documents": [
                _folded_doc(
                    "corpus/t0/strategy_review_01.md",
                    "s1-d0-04-memo",
                    "T0",
                    "S1",
                    "D0",
                    "战略复盘备忘",
                    kept,
                )
            ],
            "questions": {"queries": [_plain_question("q1", "T0", "核心业务增长预期后来有没有被改写？")]},
        },
        {
            "documents": [
                _folded_doc(
                    "corpus/t0/strategy_review_01.md",
                    "s1-d0-05-memo",
                    "T0",
                    "S1",
                    "D0",
                    "撞名的战略复盘",
                    kept,
                )
            ],
            "questions": {"queries": [_plain_question("q1", "T0", "客户满意度后来怎么写？")]},
        },
        {
            "documents": [
                _folded_doc(
                    "corpus/t0/c0ffee00abcd.md",
                    "s2-d0-01-memo",
                    "T0",
                    "S2",
                    "D0",
                    "访谈纪要 T0",
                    kept,
                ),
                _folded_doc(
                    "corpus/t1/c0ffee00abcd.md",
                    "s2-d0-01-memo",
                    "T1",
                    "S2",
                    "D0",
                    "访谈纪要 T1",
                    revised,
                ),
            ],
            "questions": {"queries": [_plain_question("q1", "T1", "增长预期在两份纪要里是否对不上？")]},
        },
        {
            "documents": [
                _folded_doc(
                    "corpus/t0/s1-d0-04-memo.md",
                    "s1-d0-04-memo",
                    "T0",
                    "S1",
                    "D0",
                    "再次写入同一路径",
                    kept,
                )
            ],
            "questions": {"queries": [_plain_question("q1", "T0", "同一路径再写一次会怎样？")]},
        },
    ]
    fake = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "replay"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec(batches))
    err = capsys.readouterr().err
    assert code == 1
    assert fake.index == 4
    assert "Traceback" not in err
    prompt = fake.calls[0]["messages"][0]["content"]
    assert "题目 id 必须形如 s1-d0-04-q1" in prompt
    assert "文件名必须是 <doc_id>.md" in prompt
    assert "目标文件已存在时，该批校验失败" not in prompt
    assert '"path":"corpus/t0/s1-d0-04-memo.md"' in prompt
    manifest = _manifest(out)
    assert manifest["batches"]["s1-d0-04"]["status"] == "ok"
    assert manifest["batches"]["s1-d0-05"]["status"] == "ok"
    assert manifest["batches"]["s2-d0-01"]["status"] == "ok"
    assert manifest["batches"]["s1-d0"]["status"] == "failed"
    assert "已存在" in manifest["batches"]["s1-d0"]["error"]
    assert all(rec["status"] != "committing" for rec in manifest["batches"].values())
    assert (out / "corpus" / "t0" / "s1-d0-04-memo.md").is_file()
    assert (out / "corpus" / "t0" / "s1-d0-05-memo.md").is_file()
    assert (out / "corpus" / "t0" / "s2-d0-01-memo.md").is_file()
    assert (out / "corpus" / "t1" / "s2-d0-01-memo.md").is_file()
    assert not (out / "corpus" / "t0" / "strategy_review_01.md").exists()
    assert not (out / "corpus" / "t0" / "c0ffee00abcd.md").exists()
    written = [item["id"] for item in json.loads((out / "questions.json").read_text(encoding="utf-8"))["queries"]]
    assert written == ["s1-d0-04-q1", "s1-d0-05-q1", "s2-d0-01-q1"]

    retry = QueueLLM([json.dumps(payloads[3], ensure_ascii=False)])
    assert _generate(mod, tmp_path, retry, cfg, out, spec=_spec(batches)) == 1
    assert retry.index == 1
    resumed = _manifest(out)
    assert resumed["batches"]["s1-d0-04"]["status"] == "ok"
    assert resumed["batches"]["s1-d0-05"]["status"] == "ok"
    assert resumed["batches"]["s2-d0-01"]["status"] == "ok"
    assert resumed["batches"]["s1-d0"]["status"] == "failed"
    assert all(rec["status"] != "committing" for rec in resumed["batches"].values())
    assert (out / "corpus" / "t0" / "s1-d0-04-memo.md").is_file()


def test_manifest_anomaly_exits_before_call(tmp_path: Path, capsys):
    mod = _load_script()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    batch = _batch()
    upper = mod._cost_cny(mod._input_token_upper(mod._build_batch_prompt(batch)), mod._output_token_upper(batch), 1, 2)
    cases = {
        "two-inflight": (
            {
                "spent_cny": upper * 2,
                "batches": {
                    "b1": {"status": "inflight", "cost_cny": upper},
                    "b2": {"status": "inflight", "cost_cny": upper},
                },
            },
            "inflight",
        ),
        "held-above-spent": (
            {
                "spent_cny": 1,
                "batches": {"b1": {"status": "inflight", "cost_cny": 10}},
            },
            "spent_cny",
        ),
        "negative-spent": ({"spent_cny": -1, "batches": {}}, "spent_cny"),
        "zeroed-spent": (
            {
                "spent_cny": 0,
                "batches": {"b1": {"status": "ok", "cost_cny": 1.5}},
            },
            "spent_cny",
        ),
    }
    for name, (body, field) in cases.items():
        out = tmp_path / name
        out.mkdir()
        marker = out / ".x1-drafts-manifest.json"
        marker.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        blob = marker.read_bytes()
        fake = FakeLLM("不应调用")
        code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec([batch]))
        err = capsys.readouterr().err
        assert code == 1
        assert fake.calls == []
        assert f"清单异常: {field}" in err
        assert marker.read_bytes() == blob


def test_flag_ledger_anomaly_exits_before_call(tmp_path: Path, capsys):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    qpath = _write_json(tmp_path / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    spec_path = _write_json(
        tmp_path / "flag-anomaly-spec.json",
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )
    ledger_path = tmp_path / ".x1-flag-spend.json"
    cases = [
        ({"spent_cny": -1}, "spent_cny"),
        ({"spent_cny": 1, "inflight": True, "held_cny": 5}, "spent_cny"),
        ({"spent_cny": 1, "inflight": "yes", "held_cny": 1}, "inflight"),
        ({"spent_cny": 0, "inflight": True, "held_cny": 1}, "spent_cny"),
    ]
    for body, field in cases:
        ledger_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        blob = ledger_path.read_bytes()
        fake = FakeLLM("不应调用")
        code = mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(tmp_path / "flag-anomaly.json"),
                "--spec",
                str(spec_path),
                "--max-cny",
                "100",
            ],
            llm_client=fake,
        )
        err = capsys.readouterr().err
        assert code == 1
        assert fake.calls == []
        assert f"清单异常: {field}" in err
        assert ledger_path.read_bytes() == blob


class _KeyboardInterruptLLM(FakeLLM):
    def chat(self, *args, **kwargs):
        raise KeyboardInterrupt


def _flag_upper_cny(mod, questions: dict) -> float:
    slim = [{"id": item.get("id"), "query": item.get("query")} for item in questions["queries"]]
    return mod._cost_cny(
        mod._input_token_upper(mod._flag_prompt(slim)),
        mod._flag_output_upper(len(slim)),
        1,
        2,
    )


def test_resume_after_prompt_grew_keeps_held_plus_real(tmp_path: Path, capsys, monkeypatch):
    mod = _load_script()
    batch = _batch()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "prompt-grew"
    assert _generate(mod, tmp_path, _KeyboardInterruptLLM("不会返回"), cfg, out, spec=_spec([batch])) == 130
    assert "调用被中断" in capsys.readouterr().err
    held = _manifest(out)["spent_cny"]
    real = mod._build_batch_prompt

    def _longer(item):
        return real(item) + "\n多一行提示。"

    monkeypatch.setattr(mod, "_build_batch_prompt", _longer)
    new_upper = mod._cost_cny(
        mod._input_token_upper(mod._build_batch_prompt(batch)),
        mod._output_token_upper(batch),
        1,
        2,
    )
    assert new_upper > held
    again = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    assert _generate(mod, tmp_path, again, cfg, out, spec=_spec([batch])) == 0
    assert len(again.calls) == 1
    resumed = _manifest(out)
    assert resumed["batches"]["b1"]["status"] == "ok"
    assert resumed["spent_cny"] == pytest.approx(held + mod._cost_cny(1, 1, 1, 2))
    assert (out / "corpus" / "t1" / "b1-draft.md").is_file()


def test_resume_after_output_price_change_keeps_held_plus_real(tmp_path: Path, capsys):
    mod = _load_script()
    batch = _batch()
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "price-changed"
    assert _generate(mod, tmp_path, _KeyboardInterruptLLM("不会返回"), cfg, out, spec=_spec([batch])) == 130
    capsys.readouterr()
    held = _manifest(out)["spent_cny"]
    resume_spec = _spec([batch])
    resume_spec["pricing"]["output_cny_per_million"] = 9
    new_upper = mod._cost_cny(
        mod._input_token_upper(mod._build_batch_prompt(batch)),
        mod._output_token_upper(batch),
        1,
        9,
    )
    assert new_upper > held
    again = FakeLLM(json.dumps(_draft_payload(), ensure_ascii=False))
    assert _generate(mod, tmp_path, again, cfg, out, spec=resume_spec) == 0
    assert len(again.calls) == 1
    resumed = _manifest(out)
    assert resumed["batches"]["b1"]["status"] == "ok"
    assert resumed["spent_cny"] == pytest.approx(held + mod._cost_cny(1, 1, 1, 9))


def test_resume_after_inflight_batch_leaves_spec_keeps_sunk_spend(tmp_path: Path, capsys):
    mod = _load_script()
    first = _batch()
    second = _batch(batch_id="b2", topic="另一批渠道纪要")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "batch-left"
    assert _generate(mod, tmp_path, _KeyboardInterruptLLM("不会返回"), cfg, out, spec=_spec([first])) == 130
    capsys.readouterr()
    held = _manifest(out)["batches"]["b1"]["cost_cny"]
    payload = _batch_payload(second, doc_id="b2-draft", qid="q1")
    again = FakeLLM(json.dumps(payload, ensure_ascii=False))
    assert _generate(mod, tmp_path, again, cfg, out, spec=_spec([second])) == 0
    assert len(again.calls) == 1
    resumed = _manifest(out)
    assert resumed["batches"]["b1"]["status"] == "sunk"
    assert resumed["batches"]["b1"]["cost_cny"] == pytest.approx(held)
    assert resumed["batches"]["b2"]["status"] == "ok"
    assert resumed["spent_cny"] == pytest.approx(held + mod._cost_cny(1, 1, 1, 2))
    assert not (out / "corpus" / "t1" / "b1-draft.md").exists()
    assert (out / "corpus" / "t1" / "b2-draft.md").is_file()


def test_flag_resume_after_question_added_keeps_held_plus_real(tmp_path: Path, capsys):
    mod = _load_script()
    questions = _draft_payload()["questions"]
    box = tmp_path / "flag-grew"
    qpath = _write_json(box / "questions.json", questions)
    cfg = _write_json(tmp_path / "config.json", _cfg())
    spec_path = _write_json(
        tmp_path / "flag-grew-spec.json",
        {"flag_pricing": _pricing_block("单测抽检占位，不是脚本内置标价")},
    )
    held_upper = _flag_upper_cny(mod, questions)

    def _flag(fake, sidecar: Path):
        return mod.main(
            [
                "flag",
                "--config",
                str(cfg),
                "--in",
                str(qpath),
                "--sidecar",
                str(sidecar),
                "--spec",
                str(spec_path),
                "--max-cny",
                "100",
            ],
            llm_client=fake,
        )

    assert _flag(_KeyboardInterruptLLM("不会返回"), box / "flag-inflight.json") == 130
    assert "调用被中断" in capsys.readouterr().err
    ledger_path = box / ".x1-flag-spend.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["inflight"] is True
    assert ledger["spent_cny"] == pytest.approx(held_upper)
    questions["queries"].append({"id": "draft-q2", "query": "多出来的一问"})
    qpath.write_text(json.dumps(questions, ensure_ascii=False), encoding="utf-8")
    assert _flag_upper_cny(mod, questions) > held_upper
    note = json.dumps(
        {"id": "draft-q1", "suspicion": "x", "reason": "y", "severity": "low"},
        ensure_ascii=False,
    )
    assert _flag(FakeLLM(note), box / "flag-ok.json") == 0
    settled = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert "inflight" not in settled
    assert settled["spent_cny"] == pytest.approx(held_upper + mod._cost_cny(1, 1, 1, 2))


def _example_section_count(prompt: str) -> int:
    example = prompt.split("单份文档示例：", 1)[1].split("\n", 1)[0]
    content = json.loads(example)["content"]
    return sum(1 for line in content.splitlines() if line.startswith("## p"))


def test_prompt_states_exact_chunk_count_including_pair_and_s6():
    mod = _load_script()
    two = _batch(chunks_per_doc=2)
    prompt = mod._build_batch_prompt(two)
    assert "每篇 content 正文恰好 2 段，标题依次为 `## p1` … `## p2`，不多不少。" in prompt
    assert _example_section_count(prompt) == 2

    four = _batch(batch_id="c4", chunks_per_doc=4, topic="四段备忘")
    prompt4 = mod._build_batch_prompt(four)
    assert "每篇 content 正文恰好 4 段，标题依次为 `## p1` … `## p4`，不多不少。" in prompt4
    assert _example_section_count(prompt4) == 4
    example4 = json.loads(prompt4.split("单份文档示例：", 1)[1].split("\n", 1)[0])["content"]
    assert "## p5" not in example4

    pair = {
        "batch_id": "pair5",
        "genre": "S2",
        "domain": "D0",
        "n_docs": 1,
        "chunks_per_doc": 5,
        "topic": "配对五段",
        "pair": True,
    }
    prompt_pair = mod._build_batch_prompt(pair)
    assert "每篇 content 正文恰好 5 段，标题依次为 `## p1` … `## p5`，不多不少。" in prompt_pair
    assert "T0 与 T1 各自的正文都恰好 5 段，标题依次为 `## p1` … `## p5`，不多不少。" in prompt_pair
    assert _example_section_count(prompt_pair) == 5

    fact = "令16第五条新增个人信息出境豁免场景"
    s6 = _batch(
        batch_id="s6-d1-c4",
        genre="S6",
        domain="D1",
        as_of="T1",
        chunks_per_doc=3,
        topic="监管豁免",
        must_include=[fact],
    )
    prompt_s6 = mod._build_batch_prompt(s6)
    sentence = "每篇 content 正文恰好 3 段，标题依次为 `## p1` … `## p3`，不多不少。"
    assert prompt_s6.count(sentence) == 1
    assert "只写 must_include 里的事实，不得自拟法律门槛或日期。" in prompt_s6
    assert "must_include（原样遵守，不要改写这些事实）：" in prompt_s6
    assert fact in prompt_s6
    assert "不得为了凑段数改写或删掉" in prompt_s6
    assert (
        "p1 完整写出 must_include 事实；其余段只写背景、适用范围或影响说明，不得新增门槛、日期、金额或其他数字，也不要拆开或改写 must_include 事实。"
        in prompt_s6
    )
    assert _example_section_count(prompt_s6) == 3
    multi = _batch(
        batch_id="s6-multi",
        genre="S6",
        domain="D3",
        as_of="T1",
        chunks_per_doc=3,
        topic="多条事实",
        must_include=[fact, "另一条已有事实"],
    )
    prompt_multi = mod._build_batch_prompt(multi)
    assert prompt_multi.count(sentence) == 1
    assert "不得新增门槛、日期、金额或其他数字，也不要拆开或改写 must_include 事实。" in prompt_multi
    assert "p1 完整写出 must_include 事实" not in prompt_multi
    assert "不要写法律门槛" in prompt_multi


def _s6_reply(batch_id: str, domain: str, title: str, paragraphs: list[str], question: str) -> dict:
    doc_id = f"{batch_id}-memo"
    body = [
        "---",
        f"doc_id: {doc_id}",
        "as_of: T1",
        "source_type: private",
        f"title: {title}",
        "provenance: synthetic",
        "license: synthetic",
        f"domain: {domain}",
        "genre: S6",
        "---",
    ]
    for index, paragraph in enumerate(paragraphs, start=1):
        body.append(f"## p{index}")
        body.append(paragraph)
    return {
        "documents": [
            {
                "path": f"corpus/t1/{doc_id}.md",
                "content": "\n".join(body) + "\n",
            }
        ],
        "questions": {
            "queries": [
                {
                    "id": f"{batch_id}-q1",
                    "query": question,
                    "category": "regulatory_change",
                    "eval_intent": "fact_recall",
                    "as_of": "T1",
                }
            ]
        },
    }


def test_s6_wrong_section_counts_fail_with_expected_and_actual(tmp_path: Path, capsys):
    """离线重放三批真实 qwen-flash 回复：6 段、6 段、2 段，期望都是 3 段。"""
    mod = _load_script()
    cases = [
        (
            "s6-d1-c4",
            "D1",
            6,
            [
                "根据令16第五条新增豁免规定，除关键信息基础设施运营者外，其他主体在满足特定条件时可免于开展个人信息出境安全评估申报、标准合同备案及认证程序。",
                "豁免适用的量化门槛为：当年累计出境的个人信息数量不足十万人，且不包含敏感个人信息。该标准适用于非关键信息基础设施运营者主体。",
                "此外，令16第五条明确列出若干具体豁免场景，包括但不限于合同履行所必需的跨境数据传输、跨境人力资源管理活动，以及应对突发紧急情况下的必要数据转移。",
                "上述豁免仅限于非关键信息基础设施运营者，且不得扩大解释或用于规避监管要求。所有数据处理行为仍须遵循最小必要原则与合法正当目的要求。",
                "特别提示：若涉及敏感个人信息，无论数量多少，均不适用本豁免条款，必须依法履行安全评估或标准合同等合规义务。",
                "本备忘内容基于现行有效法规，仅作合规指引参考，实际执行应以主管部门最终解释为准。",
            ],
            "令16第五条新增了哪些个人信息出境的豁免场景？",
        ),
        (
            "s6-d2-g1",
            "D2",
            6,
            [
                "根据2023公司法第四十七条，有限责任公司股东的认缴出资须自公司成立之日起五年内缴足。此规定为新设强制性期限要求。",
                "相较之下，2018年公司法第二十六条并未设定具体的出资缴足期限，允许股东自行约定出资时间。",
                "本次监管变更明确将认缴出资的最长期限限定为五年，强化了对公司资本真实性的监管要求。",
                "该调整旨在防范股东利用无限期认缴制度规避出资责任，提升企业信用透明度与市场稳定性。",
                "需注意，该条款仅适用于新设公司或未完成出资的存量公司，已履行出资义务的不溯及既往。",
                "所有相关主体应依据2023公司法第四十七条重新审视公司章程中的出资安排，确保合规。",
            ],
            "2023公司法第四十七条对有限责任公司股东认缴出资期限有何具体要求？",
        ),
        (
            "s6-d2-g2",
            "D2",
            2,
            [
                "新公司法（2023修订）于二〇二四年七月一日生效，第二百六十六条要求出资期限超出法定上限的存量公司逐步调整到位。",
                "旧法（2018修正）的施行日期为二〇〇六年一月一日。",
            ],
            "新公司法（2023修订）的施行日期是什么？",
        ),
    ]
    batches = []
    payloads = []
    for batch_id, domain, _count, paragraphs, question in cases:
        batches.append(
            _batch(
                batch_id=batch_id,
                genre="S6",
                domain=domain,
                as_of="T1",
                chunks_per_doc=3,
                topic=batch_id,
                must_include=[paragraphs[0]],
            )
        )
        payloads.append(
            _s6_reply(
                batch_id,
                domain,
                f"顾问备忘：{batch_id}",
                paragraphs,
                question,
            )
        )
    fake = QueueLLM([json.dumps(item, ensure_ascii=False) for item in payloads])
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "s6-sections"
    code = _generate(mod, tmp_path, fake, cfg, out, spec=_spec(batches))
    err = capsys.readouterr().err
    assert code == 1
    assert fake.index == 3
    assert "期望 3 段，实得 6 段" in err
    assert "期望 3 段，实得 2 段" in err
    manifest = _manifest(out)
    assert manifest["batches"]["s6-d1-c4"]["error"] == "期望 3 段，实得 6 段"
    assert manifest["batches"]["s6-d2-g1"]["error"] == "期望 3 段，实得 6 段"
    assert manifest["batches"]["s6-d2-g2"]["error"] == "期望 3 段，实得 2 段"
    assert all(rec["status"] == "failed" for rec in manifest["batches"].values())
    assert not (out / "corpus" / "t1" / "s6-d1-c4-memo.md").exists()
    assert manifest["stop_reason"] == "consecutive_validation"


def test_old_prompt_ok_batch_kept_when_prompt_changes(tmp_path: Path, monkeypatch, capsys):
    mod = _load_script()
    done = _batch(batch_id="done", topic="已完成")
    failed = _batch(batch_id="failed", topic="校验失败后重跑")
    todo = _batch(batch_id="todo", topic="尚未生成", domain="D2")
    cfg = _write_json(tmp_path / "config.json", _cfg())
    out = tmp_path / "prompt-resume"
    real = mod._build_batch_prompt

    def _old_prompt(item):
        return real(item).replace(mod._chunk_count_line(int(item["chunks_per_doc"])), "块数等于 chunks_per_doc。")

    monkeypatch.setattr(mod, "_build_batch_prompt", _old_prompt)
    done_payload = _batch_payload(done, doc_id="done-doc", qid="q-done")
    failed_body = _doc_body(
        n_chunks=6,
        doc_id="failed-doc",
        title="段数过多",
        domain="D0",
        genre="S1",
        as_of="T1",
    )
    failed_payload = {
        "documents": [{"path": "corpus/t1/failed-doc.md", "content": failed_body}],
        "questions": _batch_payload(failed, doc_id="failed-doc", qid="q-failed")["questions"],
    }
    first = QueueLLM(
        [json.dumps(done_payload, ensure_ascii=False), json.dumps(failed_payload, ensure_ascii=False)]
    )
    assert _generate(mod, tmp_path, first, cfg, out, spec=_spec([done, failed])) == 1
    assert first.index == 2
    before = _manifest(out)
    assert before["batches"]["done"]["status"] == "ok"
    assert before["batches"]["failed"]["status"] == "failed"
    assert "期望 2 段，实得 6 段" in before["batches"]["failed"]["error"]
    old_sha = before["batches"]["done"]["prompt_sha256"]
    spent_before = before["spent_cny"]
    real_cost = mod._cost_cny(1, 1, 1, 2)
    assert spent_before == pytest.approx(real_cost * 2)
    done_bytes = (out / "corpus" / "t1" / "done-doc.md").read_bytes()

    monkeypatch.setattr(mod, "_build_batch_prompt", real)
    retry_failed = _batch_payload(failed, doc_id="failed-doc", qid="q-failed")
    todo_payload = _batch_payload(todo, doc_id="todo-doc", qid="q-todo")
    second = QueueLLM(
        [json.dumps(retry_failed, ensure_ascii=False), json.dumps(todo_payload, ensure_ascii=False)]
    )
    code = _generate(mod, tmp_path, second, cfg, out, spec=_spec([done, failed, todo]))
    err = capsys.readouterr().err
    assert code == 0
    assert "解码参数与清单不一致" not in err
    assert second.index == 2
    assert [call["messages"][0]["content"].split("topic：", 1)[1].split("\n", 1)[0] for call in second.calls] == [
        "校验失败后重跑",
        "尚未生成",
    ]
    assert "每篇 content 正文恰好 2 段" in second.calls[0]["messages"][0]["content"]
    resumed = _manifest(out)
    assert resumed["batches"]["done"]["status"] == "ok"
    assert resumed["batches"]["done"]["prompt_sha256"] == old_sha
    assert resumed["batches"]["failed"]["status"] == "ok"
    assert resumed["batches"]["todo"]["status"] == "ok"
    assert resumed["spent_cny"] == pytest.approx(spent_before + real_cost * 2)
    assert (out / "corpus" / "t1" / "done-doc.md").read_bytes() == done_bytes
    assert (out / "corpus" / "t1" / "failed-doc.md").is_file()
    assert (out / "corpus" / "t1" / "todo-doc.md").is_file()
