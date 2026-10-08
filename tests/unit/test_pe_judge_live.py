"""--live 默认关闭。单测替换 real_transport，不读密钥，不发请求。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval import patch_events_judges as judges

ROOT = Path(__file__).resolve().parents[2]
_SECRET_ENV = ("DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY")
_PE_V2_SPLIT = Path("docs/evidence/patch-events/SPLIT-pe-v2.json")


def _item() -> dict[str, str]:
    return {
        "claim_id": "c1",
        "before_text": "修改前正文",
        "after_text": "修改后正文",
        "evidence_text": "证据正文",
        "evidence_id": "doc#a@T1",
    }


def _echo(request: dict) -> dict:
    return {
        "model": request["model"],
        "temperature": request["temperature"],
        "thinking": request.get("thinking"),
        "content": '{"A":"是","B":"否"}',
        "usage": None,
        "refused": None,
    }


@pytest.fixture(autouse=True)
def _block_network(monkeypatch):
    for key in _SECRET_ENV:
        monkeypatch.delenv(key, raising=False)

    def blocked(_request):
        raise AssertionError("单测不得调用真实传输")

    monkeypatch.setattr(judges, "real_transport", blocked)


def test_default_command_does_not_read_keys_or_send(monkeypatch, capsys):
    seen: list[str] = []
    original = judges.os.getenv

    def wrapped(key, default=None):
        seen.append(str(key))
        return original(key, default)

    monkeypatch.setattr(judges.os, "getenv", wrapped)
    constructed: list[int] = []
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_construct.construct_samples",
        lambda *_args, **_kwargs: constructed.append(1),
    )
    assert judges.main([]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert constructed == []
    for key in _SECRET_ENV:
        assert key not in seen


def test_live_off_keeps_the_injected_transport(tmp_path):
    calls: list[str] = []

    def injected(request):
        calls.append(request["model"])
        return _echo(request)

    result = judges.run_judges(
        [_item()],
        transport=injected,
        logs_dir=tmp_path,
        judge_ids=("qwen",),
    )
    assert calls == [judges.JUDGES["qwen"].model]
    assert result["judges"]["qwen"]["labels"]["c1"] == {"A": "是", "B": "否"}
    assert result["judges"]["qwen"]["missing_rate"] == 0.0


def test_live_flag_uses_real_transport_not_the_injected_one(monkeypatch, tmp_path):
    calls: list[str] = []

    def echo(request):
        calls.append(request["model"])
        return _echo(request)

    def injected(_request):
        raise AssertionError("live 打开时不得使用传入的传输")

    monkeypatch.setattr(judges, "real_transport", echo)
    result = judges.run_judges(
        [_item()],
        transport=injected,
        logs_dir=tmp_path,
        judge_ids=("qwen",),
        live=True,
    )
    assert calls == [judges.JUDGES["qwen"].model]
    assert result["judges"]["qwen"]["missing_rate"] == 0.0
    line = json.loads((tmp_path / "qwen.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert line["解析结果"] == {"A": "是", "B": "否"}
    assert "env_key" not in line


def test_live_command_scores_only_pe_v2_pilot(monkeypatch, tmp_path, capsys):
    from freshlatch.eval.patch_events_split import load_formal_ids, load_pilot_ids

    calls: list[dict] = []

    def echo(request):
        calls.append(request)
        return _echo(request)

    formal_calls: list[int] = []

    def refuse_formal(*_args, **_kwargs):
        formal_calls.append(1)
        raise AssertionError("不得读取正式集")

    monkeypatch.setattr(judges, "real_transport", echo)
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_split.load_formal_ids",
        refuse_formal,
    )
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sentinel-dash")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sentinel-deep")
    monkeypatch.setenv("MOONSHOT_API_KEY", "sentinel-moon")

    assert judges.main(["--live", "--logs-dir", str(tmp_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    manifest = json.loads((ROOT / _PE_V2_SPLIT).read_text(encoding="utf-8"))
    pilot_ids = load_pilot_ids(ROOT, split=_PE_V2_SPLIT)
    formal_ids = {row["claim_id"] for row in manifest["n30"]} | {
        row["claim_id"] for row in manifest["n100"]
    }
    assert pilot_ids == [row["claim_id"] for row in manifest["pilot"]]
    assert set(pilot_ids).isdisjoint(formal_ids)
    assert formal_calls == []
    assert len(calls) == len(pilot_ids) * len(judges.JUDGE_IDS)
    rendered = json.dumps(report, ensure_ascii=False)
    for claim_id in formal_ids:
        assert claim_id not in rendered
    for judge_id in judges.JUDGE_IDS:
        block = report[judge_id]
        assert list(block["labels"]) == pilot_ids
        assert block["missing_rate"] == 0.0
        log_text = (tmp_path / f"{judge_id}.jsonl").read_text(encoding="utf-8")
        assert len(log_text.splitlines()) == len(pilot_ids)
        for secret in ("sentinel-dash", "sentinel-deep", "sentinel-moon"):
            assert secret not in log_text
            assert secret not in rendered
    assert not (ROOT / "docs" / "evidence" / "patch-events" / "PILOT-NOTE.md").is_file()
    with pytest.raises(RuntimeError, match="pilot 未结束，不得读取正式集"):
        load_formal_ids(ROOT)


def test_live_loader_source_does_not_name_the_formal_gate():
    text = Path(judges.__file__).read_text(encoding="utf-8")
    assert "load_formal_ids" not in text
    start = text.index("def load_pe_v2_pilot_items")
    end = text.index("\ndef ", start + 1)
    body = text[start:end]
    assert "n30" not in body
    assert "n100" not in body
