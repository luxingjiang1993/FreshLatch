"""#487：路线 C 正式入口默认不发、n=100 针、禁写 b/旧路径、未激活拒发。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from freshlatch.eval.patch_events_formal import generations_path
from freshlatch.eval.patch_events_formal_c import (
    assert_generations_c_allowed,
    ensure_generations_c_shell,
    formal_c_requests,
    load_formal_c_n100,
    main,
    n100_claim_ids,
    prereg_c_activated,
    send_formal_c,
    status_pack,
)


def test_prereg_c_not_activated_on_current_tree():
    assert prereg_c_activated() is False


def test_n100_pin_matches_split_excludes_pilot():
    ids = n100_claim_ids()
    assert len(ids) == 100
    rows = load_formal_c_n100()
    assert [r["claim_id"] for r in rows] == ids
    payload = json.loads(
        Path("docs/evidence/patch-events/SPLIT-pe-v2.json").read_text(encoding="utf-8")
    )
    pilot = {str(r["claim_id"]) for r in payload["pilot"]}
    assert set(ids).isdisjoint(pilot)
    assert ids == [str(r["claim_id"]) for r in payload["n100"]]


def test_formal_c_requests_skip_b1_rewrite():
    rows = load_formal_c_n100()[:2]
    reqs = formal_c_requests(rows)
    assert ("B1", "rewrite") not in {(r["arm"], r["phase"]) for r in reqs}
    assert ("T", "rewrite") in {(r["arm"], r["phase"]) for r in reqs}
    assert ("C", "rewrite") in {(r["arm"], r["phase"]) for r in reqs}


def test_default_main_is_dry_no_send(capsys):
    code = main([])
    assert code == 0
    out = capsys.readouterr().out
    assert '"status": "dry"' in out
    assert '"activated": false' in out
    assert '"n": 100' in out
    assert "formal-generations-c.jsonl" in out
    assert "formal-generations-b.jsonl" in out
    assert "未激活" in out
    assert "默认不发" in out or "dry" in out


def test_authorize_send_refused_when_unactivated(capsys):
    code = main(["--authorize-send"])
    assert code == 2
    err = capsys.readouterr().err
    assert "未激活" in err


def test_recompute_refused_when_unactivated(capsys):
    code = main(["--recompute-only"])
    assert code == 2
    assert "未激活" in capsys.readouterr().err


def test_send_refuses_b_and_legacy_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_c.prereg_c_activated",
        lambda root=None: True,
    )
    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_c.generations_c_path",
        lambda root=None: generations_path(),
    )
    with pytest.raises(RuntimeError, match="formal-generations"):
        send_formal_c(chat=lambda *a, **k: "x")

    monkeypatch.setattr(
        "freshlatch.eval.patch_events_formal_c.generations_c_path",
        lambda root=None: Path("docs/evidence/patch-events/formal-generations-b.jsonl"),
    )
    with pytest.raises(RuntimeError, match="formal-generations-b"):
        send_formal_c(chat=lambda *a, **k: "x")


def test_assert_forbidden_filenames(tmp_path):
    with pytest.raises(RuntimeError):
        assert_generations_c_allowed(tmp_path / "formal-generations-b.jsonl", tmp_path)
    with pytest.raises(RuntimeError):
        assert_generations_c_allowed(tmp_path / "formal-generations.jsonl", tmp_path)


def test_ensure_shell_creates_empty_c_file(tmp_path):
    # 最小树：PREREG 不需要；只测壳路径在临时 root 下
    pe = tmp_path / "docs" / "evidence" / "patch-events"
    pe.mkdir(parents=True)
    path = ensure_generations_c_shell(tmp_path)
    assert path.name == "formal-generations-c.jsonl"
    assert path.is_file()
    assert path.read_text(encoding="utf-8") == ""


def test_status_pack_pins_split():
    pack = status_pack()
    assert pack["split"].endswith("SPLIT-pe-v2.json")
    assert pack["n"] == 100
    assert pack["activated"] is False
